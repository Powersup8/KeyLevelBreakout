# v2.7 Data-Driven Upgrades Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement three data-driven improvements: lower body filter threshold, fix Runner Score volume factor, add VWAP zone signals, and add 5-minute checkpoint after CONF.

**Architecture:** All changes to `KeyLevelBreakout.pine`. Phase 1 edits thresholds. Phase 2 adds VWAP as a 9th level type using existing reversal/filter/CONF infrastructure. Phase 3 adds bar-counting checkpoint logic after CONF pass.

**Tech Stack:** Pine Script v6, TradingView

**Design doc:** `docs/plans/2026-03-03-v27-data-driven-upgrades-design.md`

---

## Task 1: Version Bump

**Files:**
- Modify: `KeyLevelBreakout.pine:2`

**Step 1: Update version string**

```pine
// OLD (line 2)
// Detects bullish/bearish 5m candle closes through key levels (v2.6e)

// NEW
// Detects bullish/bearish 5m candle closes through key levels (v2.7)
```

**Step 2: Update Runner Score tooltip** (line 38)

```pine
// OLD
i_runnerScore  = input.bool(true, "Show Runner Score (①-⑤)",  tooltip="Score based on VWAP, vol 2-5x, time 10-11, level quality, symbol tier", group="Signals")

// NEW
i_runnerScore  = input.bool(true, "Show Runner Score (①-⑤)",  tooltip="Score based on VWAP, vol ≥5x, time 10-11, level quality, symbol tier", group="Signals")
```

**Step 3: Update body filter tooltip** (line 50)

```pine
// OLD
i_fCandle = input.bool(true, "Candle Body Quality Filter",  tooltip="Suppress wick-heavy breakout candles (body < 50% or close in wrong zone)", group="Filters")

// NEW
i_fCandle = input.bool(true, "Candle Body Quality Filter",  tooltip="Suppress wick-heavy breakout candles (body < 30% or close in wrong zone)", group="Filters")
```

**Step 4: Commit**

```
feat(v2.7): version bump + tooltip updates
```

---

## Task 2: Phase 1a — Body Filter Threshold 50% → 30%

**Files:**
- Modify: `KeyLevelBreakout.pine:369-370`

**Step 1: Change body and close-location thresholds**

```pine
// OLD (lines 369-370)
fCandle_bull = bodyRatio > 0.5 and closeLoc_bull > 0.6
fCandle_bear = bodyRatio > 0.5 and closeLoc_bear > 0.6

// NEW
fCandle_bull = bodyRatio > 0.3 and closeLoc_bull > 0.4
fCandle_bear = bodyRatio > 0.3 and closeLoc_bear > 0.4
```

**Step 2: Verify in TradingView**

Load on TSLA 5m chart, compare signal count with old vs new thresholds. Expect: more signals pass the body filter (fewer suppressed/dimmed).

**Step 3: Commit**

```
fix(v2.7): lower body filter 50%→30%, closeLoc 60%→40% — data shows body% is not a differentiator
```

---

## Task 3: Phase 1b — Runner Score Volume Factor ≥5x

**Files:**
- Modify: `KeyLevelBreakout.pine:409, 411`

**Step 1: Change volume condition from 2-5x range to ≥5x**

```pine
// OLD (line 409)
int scoreBull = (sigC > vwapVal ? 1 : 0) + (not na(volRatioBull) and volRatioBull >= 2.0 and volRatioBull <= 5.0 ? 1 : 0) + (isScoreWindow ? 1 : 0) + (not isDTier ? 1 : 0)

// NEW
int scoreBull = (sigC > vwapVal ? 1 : 0) + (not na(volRatioBull) and volRatioBull >= 5.0 ? 1 : 0) + (isScoreWindow ? 1 : 0) + (not isDTier ? 1 : 0)
```

```pine
// OLD (line 411)
int scoreBear = (sigC < vwapVal ? 1 : 0) + (not na(volRatioBear) and volRatioBear >= 2.0 and volRatioBear <= 5.0 ? 1 : 0) + (isScoreWindow ? 1 : 0) + (not isDTier ? 1 : 0)

// NEW
int scoreBear = (sigC < vwapVal ? 1 : 0) + (not na(volRatioBear) and volRatioBear >= 5.0 ? 1 : 0) + (isScoreWindow ? 1 : 0) + (not isDTier ? 1 : 0)
```

**Step 2: Verify in TradingView**

Check that a signal with 3.5x volume no longer gets +1 for volume. Check that 6x volume does get +1. Check that 10x+ still gets +1.

**Step 3: Commit**

```
fix(v2.7): Runner Score vol factor 2-5x→≥5x — data shows 10x+ is best, 2-5x has no edge
```

---

## Task 4: Phase 2 — VWAP Zone Signal — Input + Zone Computation

**Files:**
- Modify: `KeyLevelBreakout.pine:38` (new input), `KeyLevelBreakout.pine:343-345` (zone computation)

**Step 1: Add input** after line 38 (i_runnerScore):

```pine
i_vwapSignal   = input.bool(true, "VWAP Zone Signals",  tooltip="Fire reversal signals when price rejects off VWAP ±0.1 ATR zone", group="Signals")
```

**Step 2: Add zone computation** after line 345 (rearmBuf):

```pine
// VWAP zone: ±0.1 ATR around VWAP (data: best follow-through at this distance)
float vwapZoneWidth = not na(dailyATR) ? dailyATR * 0.10 : 0.0
float vwapZoneHi    = not na(vwapVal) ? vwapVal + vwapZoneWidth : na
float vwapZoneLo    = not na(vwapVal) ? vwapVal - vwapZoneWidth : na
```

**Step 3: Commit**

```
feat(v2.7): add VWAP zone signal input + zone computation (±0.1 ATR)
```

---

## Task 5: Phase 2 — VWAP Signal Detection + Filter Gate

**Files:**
- Modify: `KeyLevelBreakout.pine` — after reversal flags section (~line 147-155 for var declarations, ~line 264-272 for reset, ~line 648 for detection, ~line 663 for filter gate)

**Step 1: Add once-per state variables** after the existing `var bool xOL` (line 154):

```pine
var bool xVWAPBull = false
var bool xVWAPBear = false
```

**Step 2: Add session reset** in the `if newRegular` block, after `xOL := false` (line 263):

```pine
    xVWAPBull := false
    xVWAPBear := false
```

**Step 3: Add VWAP reversal detection** after the ORB reversal lines (~line 647, after rRevBearOH):

```pine
// ─── VWAP Zone Reversals ────────────────────────────────
// Bull: wick dips into VWAP zone from above, close rejects above zone top
rRevBullVWAP = i_vwapSignal and not na(vwapZoneHi) and isRegular and newSigBar
     and sigC > sigO and sigL <= vwapZoneHi and sigC > vwapZoneHi
     and (not i_vwapFilter or not na(vwapVal) and sigC > vwapVal)

// Bear: wick pushes into VWAP zone from below, close rejects below zone bottom
rRevBearVWAP = i_vwapSignal and not na(vwapZoneLo) and isRegular and newSigBar
     and sigC < sigO and sigH >= vwapZoneLo and sigC < vwapZoneLo
     and (not i_vwapFilter or not na(vwapVal) and sigC < vwapVal)
```

**Step 4: Add filtered signals with once-per gate** after the existing reversal filter gate section (~line 662, after sigRevBearOH):

```pine
// VWAP filtered signals (reversal stack: ADX + Body)
sigRevBullVWAP = rRevBullVWAP and not xVWAPBull and fGateBull_rev
sigRevBearVWAP = rRevBearVWAP and not xVWAPBear and fGateBear_rev
```

**Step 5: Set once-per flags** after the existing reversal flag updates (~line 680, after rOH := true):

```pine
if sigRevBullVWAP
    xVWAPBull := true
if sigRevBearVWAP
    xVWAPBear := true
```

**Step 6: Wire into combined signals** — update anyRevBull/anyRevBear (~line 687-688):

```pine
// OLD
anyRevBull  = sigRevBullPML or sigRevBullYL or sigRevBullWL or sigRevBullOL
anyRevBear  = sigRevBearPMH or sigRevBearYH or sigRevBearWH or sigRevBearOH

// NEW
anyRevBull  = sigRevBullPML or sigRevBullYL or sigRevBullWL or sigRevBullOL or sigRevBullVWAP
anyRevBear  = sigRevBearPMH or sigRevBearYH or sigRevBearWH or sigRevBearOH or sigRevBearVWAP
```

**Step 7: Commit**

```
feat(v2.7): VWAP zone signal detection + filter gate + once-per-session guard
```

---

## Task 6: Phase 2 — VWAP Label Text + Count Integration

**Files:**
- Modify: `KeyLevelBreakout.pine` — reversal label text section (~line 736-780), reversal count (~line 782-783)

**Step 1: Add VWAP reversal text** — insert after the sigRevBullOL block (~line 757) and sigRevBearOH block (~line 780):

After the bull reversal text block (after line 757):
```pine
if sigRevBullVWAP
    revBullText := revBullText + (revBullText != "" ? "\n" : "") + "~ VWAP"
```

After the bear reversal text block (after line 780):
```pine
if sigRevBearVWAP
    revBearText := revBearText + (revBearText != "" ? "\n" : "") + "~ VWAP"
```

**Note:** Using `"\n"` separator (not `" + "`) for VWAP since it's a different level type than the key levels. This puts it on its own line in the label for clarity.

**Step 2: Update reversal counts** (~line 782-783):

```pine
// OLD
revBullCount = (sigRevBullPML ? 1 : 0) + (sigRevBullYL ? 1 : 0) + (sigRevBullWL ? 1 : 0) + (sigRevBullOL ? 1 : 0)
revBearCount = (sigRevBearPMH ? 1 : 0) + (sigRevBearYH ? 1 : 0) + (sigRevBearWH ? 1 : 0) + (sigRevBearOH ? 1 : 0)

// NEW
revBullCount = (sigRevBullPML ? 1 : 0) + (sigRevBullYL ? 1 : 0) + (sigRevBullWL ? 1 : 0) + (sigRevBullOL ? 1 : 0) + (sigRevBullVWAP ? 1 : 0)
revBearCount = (sigRevBearPMH ? 1 : 0) + (sigRevBearYH ? 1 : 0) + (sigRevBearWH ? 1 : 0) + (sigRevBearOH ? 1 : 0) + (sigRevBearVWAP ? 1 : 0)
```

**Step 3: Commit**

```
feat(v2.7): VWAP zone label text + reversal count integration
```

---

## Task 7: Phase 2 — VWAP Log Output + Alert

**Files:**
- Modify: `KeyLevelBreakout.pine` — log section (~line 460-490), alert section

**Step 1: Add VWAP signal to log output**

Find the `dbAppend()` call or the signal log block. Add VWAP to the level name logic. In the label text building for the debug system, VWAP signals should appear as "~ VWAP" in the levels column.

The existing code stores level names via `dbLevels` array. The VWAP reversal text is already built into `revBullText`/`revBearText` (Task 6), which flows into `combinedBullText`/`combinedBearText`, which is the label text. The log uses `dbAppend()` which reads the signal data separately.

Find where `dbAppend` is called for reversals and add a VWAP case. The existing pattern is per-level-type. Add:

```pine
// In the bull reversal dbAppend section
if sigRevBullVWAP and not isOld
    dbAppend(time, "▲", "~", "VWAP", volRatioBull, bullClosePos)

// In the bear reversal dbAppend section
if sigRevBearVWAP and not isOld
    dbAppend(time, "▼", "~", "VWAP", volRatioBear, bearClosePos)
```

**Step 2: Add VWAP alert conditions**

Find existing reversal alert conditions and add VWAP:

```pine
alertcondition(sigRevBullVWAP, title="Bull VWAP Reversal", message="▲ ~ VWAP rejection (bull)")
alertcondition(sigRevBearVWAP, title="Bear VWAP Reversal", message="▼ ~ VWAP rejection (bear)")
```

**Step 3: Commit**

```
feat(v2.7): VWAP zone signal log output + alert conditions
```

---

## Task 8: Phase 3 — 5-Minute Checkpoint State Variables

**Files:**
- Modify: `KeyLevelBreakout.pine` — after VWAP exit state (~line 232)

**Step 1: Add checkpoint state variables** after the VWAP exit state section:

```pine
// ─── 5-Minute Checkpoint State ─────────────────────────
var float checkpointEntry = na     // entry price at CONF time
var int   checkpointBar   = na     // bar_index when CONF fired
var label checkpointLbl   = na     // the label to update
var int   checkpointDir   = 0      // +1 bull, -1 bear
```

**Step 2: Reset at session open** — add in the `if newRegular` block (~line 232):

```pine
    checkpointEntry := na
    checkpointBar   := na
    checkpointLbl   := na
    checkpointDir   := 0
```

**Step 3: Commit**

```
feat(v2.7): add 5-minute checkpoint state variables
```

---

## Task 9: Phase 3 — Wire Checkpoint into CONF Pass

**Files:**
- Modify: `KeyLevelBreakout.pine:902-913` (bull CONF), `KeyLevelBreakout.pine:1042-1053` (bear CONF)

**Step 1: Add checkpoint activation in bull CONF auto-promote** — after `confFailStreak := 0` (line 903):

```pine
            // Start 5-minute checkpoint
            checkpointEntry := sigC
            checkpointBar   := bar_index
            checkpointLbl   := bRTLbl
            checkpointDir   := 1
```

**Step 2: Add checkpoint activation in bear CONF auto-promote** — after `confFailStreak := 0` (line 1043):

```pine
            // Start 5-minute checkpoint
            checkpointEntry := sigC
            checkpointBar   := bar_index
            checkpointLbl   := sRTLbl
            checkpointDir   := -1
```

**Step 3: Commit**

```
feat(v2.7): wire checkpoint activation into CONF pass (bull + bear)
```

---

## Task 10: Phase 3 — Checkpoint Evaluation Logic

**Files:**
- Modify: `KeyLevelBreakout.pine` — new block after the bear CONF section (~after line 1060)

**Step 1: Add checkpoint evaluation block**

```pine
// ─── 5-Minute Checkpoint ────────────────────────────────
// Evaluate 1 signal bar after CONF pass: is price still positive?
if not na(checkpointBar) and newSigBar and bar_index > checkpointBar
    float pnl = checkpointDir == 1
         ? (sigC - checkpointEntry) / dailyATR
         : (checkpointEntry - sigC) / dailyATR

    bool hold = pnl > 0.05

    // Update existing CONF label
    if not na(checkpointLbl)
        string curText = label.get_text(checkpointLbl)
        label.set_text(checkpointLbl, curText + (hold ? "\n5m✓" : "\n5m✗"))

    // Alert
    string dir = checkpointDir == 1 ? "▲" : "▼"
    string pnlStr = str.tostring(math.round(pnl, 2))
    if hold
        alert("5m HOLD " + dir + " +" + pnlStr + " ATR", alert.freq_once_per_bar)
    else
        alert("5m BAIL " + dir + " " + pnlStr + " ATR", alert.freq_once_per_bar)

    // Log
    if i_debugLog and barstate.isconfirmed
        log.info("[KLB] 5m CHECK {0} {1} pnl={2} → {3}",
            fmtTime(time), dir, pnlStr, hold ? "HOLD" : "BAIL")

    // Reset
    checkpointEntry := na
    checkpointBar   := na
    checkpointLbl   := na
    checkpointDir   := 0
```

**Note:** Uses `bar_index > checkpointBar` (not `== checkpointBar + 1`) combined with `newSigBar` — this fires on the next signal bar after CONF, which is exactly 1 signal period (5 min on 5m TF). The `>` handles edge cases where bar_index might skip.

**Step 2: Verify in TradingView**

- Find a signal that got CONF ✓ — it should now show `5m✓` or `5m✗` on the label 1 bar later
- Check that the alert fires at the right time
- Check that new CONF overwrites pending checkpoint (no stale evaluations)

**Step 3: Commit**

```
feat(v2.7): 5-minute checkpoint evaluation — label update + alert after CONF
```

---

## Task 11: Update Documentation

**Files:**
- Modify: `KeyLevelBreakout.md` — changelog section
- Modify: `KeyLevelBreakout_Improvements.md` — update status of recommendations R1-R3

**Step 1: Add v2.7 changelog entry** to KeyLevelBreakout.md:

```markdown
### v2.7 — Data-Driven Upgrades (2026-03-03)
- **Body filter lowered** — 50% → 30% threshold (data: body% has zero quality differentiation)
- **Runner Score vol factor** — 2-5x → ≥5x (data: 10x+ has 32% CONF + 0.50 MFE, 2-5x = 20%)
- **VWAP zone signals** — New signal type: reversal off VWAP ±0.1 ATR zone. Full filter pipeline, CONF tracking, Runner Score. Solves "level desert" problem.
- **5-minute checkpoint** — After CONF ✓/✓★, evaluates P&L 1 signal bar later. Shows 5m✓ (hold) or 5m✗ (bail) on label + alert. Data: >+0.05 ATR at 5min = 93% runner, 0% fakeout.
```

**Step 2: Update improvement recommendations** in KeyLevelBreakout_Improvements.md — mark R1 (body filter), R2 (Runner Score vol), R3 (5-min gate) as ✅ IMPLEMENTED v2.7. Mark VWAP zone signal as ✅ IMPLEMENTED v2.7.

**Step 3: Commit**

```
docs(v2.7): changelog + improvement status updates
```

---

## Task 12: Final Regression Check

**No code changes — verification only.**

**Step 1: Load v2.7 in TradingView on TSLA 5m chart**

Check:
- [ ] Existing breakout signals unchanged (same labels, same positions)
- [ ] Existing reversal signals unchanged
- [ ] Body filter less aggressive (more signals pass)
- [ ] Runner Score: 3.5x vol = no vol point, 6x = +1 point
- [ ] VWAP zone signals appear as `~ VWAP ▲/▼` when price rejects off VWAP
- [ ] VWAP signals get CONF tracking (✓/✓★)
- [ ] VWAP signals respect evidence stack (dimmed/suppressed when filters fail)
- [ ] 5m✓/5m✗ appears on labels after CONF pass
- [ ] Only one VWAP signal per direction per session
- [ ] Pine Logs show VWAP signals and 5m checkpoint entries
- [ ] No compilation errors

**Step 2: Spot-check on SPY, GOOGL, QQQ**

Quick visual check that signals look reasonable across symbols.

**Step 3: Check TSLA 2/26 specifically**

The "level desert" day — does the VWAP signal catch the 11:34 breakdown? VWAP was at 409.93, price pushed up to 410.17 and rejected. This should fire a `~ VWAP ▼` signal.
