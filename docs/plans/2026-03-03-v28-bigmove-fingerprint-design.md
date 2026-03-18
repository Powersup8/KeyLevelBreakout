# v2.8 Design — Big-Move Fingerprint Integration

**Date:** 2026-03-03
**Version:** v2.7 → v2.8
**Evidence:** Multi-symbol big-move fingerprint (2,069 moves, 13 symbols, 2x 5m-ATR) + TSLA deep-dive (6,761 moves)

---

## Summary

Seven changes in one release, from trivial constant fixes to a new signal type:

1. **Runner Score time window** — 10-11 → 9:30-10
2. **D-tier symbols** — add TSM
3. **closeLoc threshold** — 0.4 → 0.3
4. **Body ≥ 80% fakeout warning** — `⚠` on labels
5. **Pre-move volume ramp computation** — classify every signal bar
6. **QBS/MC standalone signals** — new signal type with labels, CONF, alerts
7. **2x ATR big-move flag** — `⚡` on any signal hitting 2x ATR
8. **Moderate ramp dimming** — dim 1-2x ramp signals (trap bucket)

---

## Item 1: Runner Score Time Window

**Evidence:** 9:30-10 = 70% runner rate, MFE 2.36 vs 10-11 = 69%, MFE 1.75. Validated across 11/13 symbols.

**Change:** Line 427:
```pine
// OLD
bool isScoreWindow = etHour == 10
// NEW
int etMin = minute(time, TZ)
bool isScoreWindow = etHour == 9 and etMin >= 30
```

**Impact:** Runner Score +1 shifts from 10:00-10:59 to 9:30-9:59. Affects label display only.

---

## Item 2: D-Tier Symbols

**Evidence:** TSM = 38% runner rate at 2x ATR level (next worst: SLV 57%). Massive outlier across all analyses.

**Change:** Line 428:
```pine
// OLD
bool isDTier = syminfo.ticker == "AMD" or syminfo.ticker == "MSFT" or syminfo.ticker == "GLD"
// NEW
bool isDTier = syminfo.ticker == "AMD" or syminfo.ticker == "MSFT" or syminfo.ticker == "GLD" or syminfo.ticker == "TSM"
```

**Impact:** TSM signals get -1 Runner Score. No signals suppressed.

---

## Item 3: closeLoc Threshold

**Evidence:** Signal data shows 50.06 (good) vs 51.04 (bad) close location = zero differentiation. Current 0.4 threshold blocks valid signals without benefit.

**Change:** Lines 390-391:
```pine
// OLD
fCandle_bull = bodyRatio > 0.3 and closeLoc_bull > 0.4
fCandle_bear = bodyRatio > 0.3 and closeLoc_bear > 0.4
// NEW
fCandle_bull = bodyRatio > 0.3 and closeLoc_bull > 0.3
fCandle_bear = bodyRatio > 0.3 and closeLoc_bear > 0.3
```

**Impact:** Fewer false suppressions. Minimal risk — the data says this filter has no edge.

---

## Item 4: Body ≥ 80% Fakeout Warning

**Evidence:** Across all 13 symbols at 2x ATR level: body ≥ 80% = 55% fakeouts vs 36% runners. INVERSE of naive expectation. Gap: -7.6%.

**Change:** After line 391, add:
```pine
bool bodyWarn = bodyRatio >= 0.8
```

When `bodyWarn` is true, append `⚠` to any signal label text. No suppression — visual warning only.

**Affected code:** Label-building sections for BRK, REV, RCL, RT, VWAP signals (~5 insertion points). Each gets:
```pine
string bwSuffix = bodyWarn ? " ⚠" : ""
// append bwSuffix to label text
```

**Impact:** Trader sees `⚠` on high-body signals and can factor it into decision-making.

---

## Item 5: Pre-Move Volume Ramp Computation

**Evidence:** U-shaped relationship across 2,069 big moves:
- Drying (<0.5x): 68% runner, 3% fakeout — "quiet before storm"
- Steady (0.5-1x): 67%, 6%
- Moderate (1-2x): 56%, 7% — WORST (the trap)
- Surging (2-5x): 53%, 4%
- Explosive (>5x): 64%, 3%, MFE 2.66 — "momentum cascade"

### Data Requirements

Need 6 bars of historical signal-TF volume. Currently we fetch `sigVol` (current) and `sigVolPrev` (prior bar). Need 4 more.

**Change to request.security tuple** (line 340): Add `volume[2]`, `volume[3]`, `volume[4]`, `volume[5]` to the existing tuple.

Tuple element count: current ~25 + 4 = ~29 (limit: 127). Safe.

### Computation

```pine
// Pre-move volume ramp: last 3 bars avg / prior 3 bars avg
float recentVol3 = (nz(sigVol) + nz(sigVolPrev) + nz(sigVol2)) / 3.0
float priorVol3  = (nz(sigVol3) + nz(sigVol4) + nz(sigVol5)) / 3.0
float preVolRamp = priorVol3 > 0 ? recentVol3 / priorVol3 : 1.0

// Classify
bool isVolDrying    = preVolRamp < 0.5    // quiet before storm
bool isVolExplosive = preVolRamp > 5.0    // momentum cascade
bool isVolModerate  = preVolRamp >= 1.0 and preVolRamp < 2.0  // trap bucket
```

### Visual on existing signals

Append to any signal label:
- `🔇` when `isVolDrying` (quiet setup)
- `🔊` when `isVolExplosive` (momentum cascade)
- No glyph for moderate/steady (default)

---

## Item 6: QBS/MC Standalone Signals

New signal type: fires when the vol ramp fingerprint is present even WITHOUT a key-level breakout.

### Trigger Conditions

**QBS (Quiet Before Storm):**
- `isVolDrying` (preVolRamp < 0.5)
- Current signal bar range ≥ 1.5x signal-TF ATR (the explosion itself)
- Regular trading hours
- Once per direction per session (like VWAP zone signals)

**MC (Momentum Cascade):**
- `isVolExplosive` (preVolRamp > 5.0)
- Current signal bar range ≥ 1.5x signal-TF ATR
- Regular trading hours
- Once per direction per session

### Evidence Stack

QBS/MC use a **reduced** evidence stack:
- ✅ ADX > 20 (validated for big moves: blocks worst bucket)
- ✅ Body quality (body > 0.3, closeLoc > 0.3)
- ❌ Skip EMA alignment (noise at big-move level: -4% gap)
- ❌ Skip RS vs SPY (not tested for big moves)
- ❌ Skip VWAP directional (noise at big-move level: -4% gap)

```pine
evStackQBS_bull = (not i_fADX or fADX) and (not i_fCandle or fCandle_bull)
evStackQBS_bear = (not i_fADX or fADX) and (not i_fCandle or fCandle_bear)
```

Same as reversal evidence stack (ADX + Body only).

### Labels

```
🔇 QBS           🔊 MC
Bear 0.4x ③      Bull 7.2x ④
```

Line 1: glyph + type
Line 2: direction + vol ramp ratio + Runner Score

Colors:
- QBS: cyan/teal (distinctive from green/red BRK signals)
- MC: orange (high energy, distinctive from gold ✓★)

Label size: `size.normal` (same as other signals)

### CONF Tracking

QBS/MC signals enter the same CONF pipeline as other signals:
- Track if price continues in signal direction within confirmation window
- Display ✓/✗ on label
- Feed into 5-minute checkpoint (already implemented)
- ✓★ for high-conviction (≥5x vol + ≥80% close position)

### Alerts

Two new alert conditions:
```pine
alertcondition(qbsFired, "QBS — Quiet Before Storm", "🔇 Quiet Before Storm: vol drying → explosion")
alertcondition(mcFired,  "MC — Momentum Cascade",    "🔊 Momentum Cascade: vol surging → continuation")
```

### Session Tracking (once per direction per session)

```pine
var bool qbsBullFired = false
var bool qbsBearFired = false
var bool mcBullFired  = false
var bool mcBearFired  = false
if newRegular
    qbsBullFired := false
    qbsBearFired := false
    mcBullFired  := false
    mcBearFired  := false
```

### Input Toggle

```pine
i_qbsSignal = input.bool(true, "QBS/MC Signals (Vol Ramp Patterns)",
    tooltip="Fire signals when pre-move volume pattern matches high-probability fingerprint",
    group="Signals")
```

---

## Item 7: 2x ATR Big-Move Flag

**Evidence:** At 2x signal-TF ATR, runner rate is 65% across all symbols. These are the bars that matter.

### Data Requirement

Need signal-TF ATR(14). Add to request.security tuple:
```pine
ta.atr(14)  // signal-TF ATR
```

One more tuple element (total ~30/127).

### Computation

```pine
float sigATR = sigATR14  // from request.security
float sigRangeATR = sigATR > 0 ? (sigH - sigL) / sigATR : 0
bool isBigMove = sigRangeATR >= 2.0
```

### Visual

When `isBigMove` is true on ANY signal (BRK, REV, RCL, RT, VWAP, QBS, MC):
- Append `⚡` to label text
- Upgrade label size to `size.large` (same as multi-level confluence)

This stacks with other glyphs: a signal could show `BRK ⚡🔇 ⚠` (breakout + big move + quiet setup + high body warning).

---

## Item 8: Moderate Ramp Dimming

**Evidence:** 1-2x vol ramp = 56% runner (worst bucket), 7% fakeout (worst). This is the trap.

When `isVolModerate` is true and `i_fMode == "Dim"`:
- Signal still shows but label color becomes gray
- Append `?` suffix (same behavior as other dimmed signals)

When `i_fMode == "Suppress"`:
- Moderate ramp alone does NOT suppress (too aggressive — 56% is still >50%)
- Only dims as visual warning

This uses the existing dim infrastructure (gray color + `?` suffix).

---

## Resource Budget

| Resource | Before (v2.7) | After (v2.8) | Limit |
|----------|--------------|-------------|-------|
| Lines of code | ~1,411 | ~1,510 (+~100) | No hard limit (token budget) |
| request.security calls | 11 | 11 (reuse existing) | 40 |
| Tuple elements | ~25 | ~30 (+5: 4 vol + 1 ATR) | 127 |
| max_labels_count | 500 | 500 (no change) | 500 |
| New inputs | 0 | 1 (i_qbsSignal toggle) | — |
| New alert conditions | 0 | 2 (QBS, MC) | — |

**Safe on all dimensions.**

---

## What We Explicitly DON'T Change

- **EMA filter** — works for signals (+13% gap), leave ON
- **VWAP filter** — works for reversals, leave ON
- **ADX threshold** — 20 is validated, don't raise
- **RS vs SPY** — weak but harmless, leave ON
- **Volume floor (1.5x)** — fine as-is
- **Gap detection** — TSLA-specific, not universal, skip

---

## Version Bump

v2.7 → v2.8: "Big-Move Fingerprint Integration"

Indicator title line:
```pine
// Detects bullish/bearish 5m candle closes through key levels (v2.8)
```
