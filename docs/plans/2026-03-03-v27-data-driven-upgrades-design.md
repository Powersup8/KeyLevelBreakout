# v2.7 Design — Data-Driven Upgrades

**Date:** 2026-03-03
**Version:** v2.6e → v2.7
**Evidence:** Multi-symbol fingerprint (1,841 signals, 13 symbols) + Big move fingerprint (9,596 bars, 13 symbols)

---

## Summary

Three phases in one release:

1. **Phase 1 — Quick fixes:** Body filter 50%→30%, Runner Score vol 2-5x→≥5x
2. **Phase 2 — VWAP zone signal:** 9th level type with full filter pipeline
3. **Phase 3 — 5-minute checkpoint:** Label update + alert after CONF, 1 signal bar later

---

## Phase 1: Quick Data-Driven Fixes

### 1a. Body Filter Threshold: 0.5 → 0.3

**Evidence:** Body% has zero differentiation between good and bad signals (49% vs 48%). Body ≥80% is actually a fakeout indicator (55% fakeouts vs 36% runners). Current 50% threshold actively suppresses valid signals.

**Change:** Edit two conditions (~line 367):

```pine
// OLD
fCandle_bull = bodyRatio > 0.5 and closeLoc_bull > 0.6
fCandle_bear = bodyRatio > 0.5 and closeLoc_bear > 0.6

// NEW
fCandle_bull = bodyRatio > 0.3 and closeLoc_bull > 0.4
fCandle_bear = bodyRatio > 0.3 and closeLoc_bear > 0.4
```

**Rationale for closeLoc 0.6→0.4:** Keeps the close-location check proportional to the body requirement. A candle with 30% body closing at 40% of its range is the new reasonable minimum.

### 1b. Runner Score Volume Factor: 2-5x → ≥5x

**Evidence:** 10x+ volume = 32% CONF + 0.50 MFE (best). 2-5x = 20% CONF (no edge over baseline). The relationship is monotonic: more volume = better. Current 2-5x range rewards the wrong bucket.

**Change:** Edit two conditions (~line 409):

```pine
// OLD (bull and bear)
+ (not na(volRatioBull) and volRatioBull >= 2.0 and volRatioBull <= 5.0 ? 1 : 0)

// NEW
+ (not na(volRatioBull) and volRatioBull >= 5.0 ? 1 : 0)
```

Same change for `scoreBear` with `volRatioBear`.

**Impact:** 4 line edits. Zero structural risk. Purely threshold corrections backed by data.

---

## Phase 2: VWAP Zone Signal (9th Level Type)

### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Signal type | Rejection only (not breakout) | Data shows VWAP ±0.1 ATR zone has best follow-through (89% runner, 1.98 MFE) |
| Architecture | 9th level type in existing pipeline | Reuses filter stack, CONF, Runner Score, SL lines, labels — no duplication |
| Zone width | ±0.1 ATR | Matches the data bucket with best MFE |
| Filter stack | Reversal stack (ADX + Body) | VWAP rejection is counter-trend by nature, same as level reversals |
| Once-per guard | Per direction per session | Prevents spam since VWAP moves continuously |

### New Input

```pine
i_vwapSignal = input.bool(true, "VWAP Zone Signals",
    tooltip="Fire reversal signals when price rejects off VWAP ±0.1 ATR zone",
    group="Signals")
```

### Zone Computation

Near existing `vwapVal = ta.vwap` (~line 343):

```pine
float vwapZoneWidth = dailyATR * 0.10
float vwapZoneHi    = not na(vwapVal) ? vwapVal + vwapZoneWidth : na
float vwapZoneLo    = not na(vwapVal) ? vwapVal - vwapZoneWidth : na
```

### Signal Detection

After existing reversal detection (~line 600):

```pine
// Bull VWAP rejection: wick dips into zone from above, close rejects above zone top
bool rBullVWAP = i_vwapSignal and not na(vwapZoneHi) and isRegular and newSigBar
     and sigC > sigO and sigL <= vwapZoneHi and sigC > vwapZoneHi
     and (not i_vwapFilter or sigC > vwapVal)

// Bear VWAP rejection: wick pushes into zone from below, close rejects below zone bottom
bool rBearVWAP = i_vwapSignal and not na(vwapZoneLo) and isRegular and newSigBar
     and sigC < sigO and sigH >= vwapZoneLo and sigC < vwapZoneLo
     and (not i_vwapFilter or sigC < vwapVal)
```

### Filter Gate

```pine
sigBullVWAP = rBullVWAP and fGateBull_rev   // reversal stack: ADX + Body
sigBearVWAP = rBearVWAP and fGateBear_rev
```

### Once-Per Guard

```pine
var bool xVWAPBull = false
var bool xVWAPBear = false

// Reset at session open
if session.isfirstbar
    xVWAPBull := false
    xVWAPBear := false

// Gate signals
sigBullVWAP := sigBullVWAP and not xVWAPBull
sigBearVWAP := sigBearVWAP and not xVWAPBear

// Set flags on fire
if sigBullVWAP
    xVWAPBull := true
if sigBearVWAP
    xVWAPBear := true
```

**Note:** Using once-per-session initially. Can relax to once-per-N-bars if we want multiple VWAP signals per day (VWAP moves, so the same level can be tested multiple times from different prices). Start strict, loosen later based on data.

### Label Creation

Same pattern as existing reversal labels. Label text format:

```
~ VWAP ▲  1.5x ^65 ②        (bull VWAP rejection)
~ VWAP ▼  2.1x v78 ③        (bear VWAP rejection)
```

Wire into existing label creation block. VWAP label uses:
- `~` prefix (reversal)
- `VWAP` as level name
- Same volume ratio, close position, Runner Score display
- Same color scheme (blue for bull reversal, orange for bear reversal)
- Dim mode `?` suffix when evidence stack fails (same as other reversals)

### CONF Tracking

Wire VWAP signals into existing CONF state machine:
- On signal fire: store entry, start tracking for auto-promote
- Same `bRTLbl`, `bRTDir`, `bRTEntry` pattern as level reversals
- CONF ✓ / ✓★ upgrade applies
- SL lines at 0.10/0.15 ATR on CONF pass
- VWAP exit alert activates on CONF pass

### Log Output

```
[KLB] 11:35 ▼ ~ VWAP vol=2.1x pos=78% vwap=below ema=aligned adx=27 body=83% rs=-0.2%
```

### What Does NOT Change

- Existing 8 level types — untouched
- Existing breakout/reversal/reclaim/retest logic — untouched
- Filter stack structure — untouched (VWAP signals plug in)
- Runner Score computation — untouched (VWAP signals get scored same way)

---

## Phase 3: 5-Minute Checkpoint

### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Trigger | After CONF ✓/✓★ passes | Only evaluate confirmed signals (already filtered) |
| Timing | 1 signal bar after CONF (= 5 min on 5m TF) | Data validated 5-minute checkpoint specifically |
| Threshold | +0.05 ATR in trade direction | 93% runner, 0% fakeout when combined with EMA + VWAP |
| UX | Update existing label + fire alert | Minimal visual clutter, visible in replay |
| Overlap | Latest signal wins (overwrite) | Simple, no queue. New CONF replaces pending checkpoint |

### State Variables

```pine
var float checkpointEntry = na     // entry price at CONF time
var int   checkpointBar   = na     // bar_index when CONF fired
var label checkpointLbl   = na     // the label to update
var int   checkpointDir   = 0      // +1 bull, -1 bear
```

### On CONF Pass

Inside existing auto-promote blocks (~line 900 for bull, ~line 1043 for bear), add:

```pine
// Bull CONF pass — start checkpoint
checkpointEntry := sigC
checkpointBar   := bar_index
checkpointLbl   := bRTLbl
checkpointDir   := 1    // or -1 for bear block
```

### Checkpoint Evaluation

New block after CONF logic, runs every bar:

```pine
if not na(checkpointBar) and bar_index == checkpointBar + 1 and newSigBar
    float pnl = checkpointDir == 1
         ? (sigC - checkpointEntry) / dailyATR
         : (checkpointEntry - sigC) / dailyATR

    bool hold = pnl > 0.05

    // Update existing label
    string curText = label.get_text(checkpointLbl)
    label.set_text(checkpointLbl, curText + (hold ? "\n5m✓" : "\n5m✗"))

    // Alert
    if hold
        alert("5m HOLD: +" + str.tostring(math.round(pnl * 100, 1)) + "% ATR", alert.freq_once_per_bar)
    else
        alert("5m BAIL: " + str.tostring(math.round(pnl * 100, 1)) + "% ATR", alert.freq_once_per_bar)

    // Log
    if i_debugLog and barstate.isconfirmed
        log.info("[KLB] 5m CHECK {0} {1} pnl={2} → {3}",
            fmtTime(time), checkpointDir == 1 ? "▲" : "▼",
            str.tostring(math.round(pnl, 3)), hold ? "HOLD" : "BAIL")

    // Reset
    checkpointBar := na
```

### Label Appearance After Checkpoint

```
▼ BRK Yest L ✓  3.2x v85 ④
5m✓                                ← positive after 5 minutes

▲ BRK PM H ✓★  8.1x ^92 ⑤
5m✗                                ← went negative, bail signal
```

---

## Version & Changelog

```
v2.7: Body filter 50%→30%, Runner Score vol ≥5x, VWAP zone signals, 5-min checkpoint
```

## Estimated Line Count

| Component | Lines |
|-----------|-------|
| Phase 1: Body filter edits | 2 |
| Phase 1: Runner Score vol edits | 2 |
| Phase 2: Input | 2 |
| Phase 2: Zone computation | 3 |
| Phase 2: Signal detection | 6 |
| Phase 2: Filter gate | 2 |
| Phase 2: Once-per guard | 10 |
| Phase 2: Label creation + CONF wiring | ~15 |
| Phase 2: Log output | 2 |
| Phase 3: State variables | 4 |
| Phase 3: CONF pass additions | 8 (4 per direction) |
| Phase 3: Checkpoint evaluation | 15 |
| **Total** | **~70 lines added/changed** |

## Testing Checklist

- [ ] Phase 1: Body filter at 30% — fewer signals suppressed than at 50%
- [ ] Phase 1: Runner Score — vol 4x gets 0 points, vol 6x gets +1
- [ ] Phase 2: VWAP rejection fires when wick enters zone and close rejects
- [ ] Phase 2: VWAP signal goes through evidence stack (dimmed/suppressed when filters fail)
- [ ] Phase 2: VWAP signal gets CONF tracking, SL lines, Runner Score
- [ ] Phase 2: Only one VWAP signal per direction per session
- [ ] Phase 2: VWAP signal label shows `~ VWAP ▲/▼` with volume/position/score
- [ ] Phase 3: 5m✓ appears on label 1 signal bar after CONF when P&L > +0.05 ATR
- [ ] Phase 3: 5m✗ appears when P&L ≤ +0.05 ATR
- [ ] Phase 3: Alert fires at checkpoint time
- [ ] Phase 3: New CONF overwrites pending checkpoint (no stale evaluations)
- [ ] All existing signals unchanged (regression check on 13 symbols)
