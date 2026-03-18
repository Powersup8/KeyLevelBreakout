# v2.8 Big-Move Fingerprint Integration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate validated big-move fingerprint findings into KeyLevelBreakout.pine (v2.7 → v2.8), adding volume ramp detection, QBS/MC standalone signals, and visual warnings.

**Architecture:** 8 changes to a single file (`KeyLevelBreakout.pine`). No new files. No new `request.security` calls — all new data fetched by expanding the existing signal-TF tuple (lines 340-341). Changes are ordered from trivial constants → medium computations → complex new signal type.

**Tech Stack:** Pine Script v6, TradingView indicator

**Design doc:** `docs/plans/2026-03-03-v28-bigmove-fingerprint-design.md`

---

### Task 1: Trivial Constant Changes (Items 1-3)

Three 1-line edits that are independent of everything else.

**Files:**
- Modify: `KeyLevelBreakout.pine:427` (Runner Score time window)
- Modify: `KeyLevelBreakout.pine:428` (D-tier symbols)
- Modify: `KeyLevelBreakout.pine:390-391` (closeLoc threshold)

**Step 1: Change Runner Score time window from 10-11 to 9:30-10**

Line 427 currently reads:
```pine
bool isScoreWindow = etHour == 10
```

Replace with:
```pine
int etMin = minute(time, TZ)
bool isScoreWindow = etHour == 9 and etMin >= 30
```

Note: `etHour` already exists on line 426. `etMin` is a new variable inserted between lines 426-427.

**Step 2: Add TSM to D-tier symbols**

Line 428 currently reads:
```pine
bool isDTier = syminfo.ticker == "AMD" or syminfo.ticker == "MSFT" or syminfo.ticker == "GLD"
```

Replace with:
```pine
bool isDTier = syminfo.ticker == "AMD" or syminfo.ticker == "MSFT" or syminfo.ticker == "GLD" or syminfo.ticker == "TSM"
```

**Step 3: Lower closeLoc threshold from 0.4 to 0.3**

Lines 390-391 currently read:
```pine
fCandle_bull = bodyRatio > 0.3 and closeLoc_bull > 0.4
fCandle_bear = bodyRatio > 0.3 and closeLoc_bear > 0.4
```

Replace with:
```pine
fCandle_bull = bodyRatio > 0.3 and closeLoc_bull > 0.3
fCandle_bear = bodyRatio > 0.3 and closeLoc_bear > 0.3
```

**Step 4: Verify in TradingView**

Add indicator to chart, verify it compiles. Spot-check Runner Score shows ① or higher during 9:30-9:59 bars, not during 10:xx bars. TSM chart should show -1 score impact.

**Step 5: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "v2.8: trivial constant fixes (time window, D-tier, closeLoc)"
```

---

### Task 2: Body Warning ⚠ (Item 4)

Add `bodyWarn` flag and append `⚠` to all signal labels when body ≥ 80%.

**Files:**
- Modify: `KeyLevelBreakout.pine:391` (add bodyWarn after closeLoc)
- Modify: `KeyLevelBreakout.pine:864-865` (combined bull label text building)
- Modify: `KeyLevelBreakout.pine:1009-1010` (combined bear label text building)

**Step 1: Add bodyWarn flag**

After line 391 (the `fCandle_bear` line), insert:
```pine
bool bodyWarn = bodyRatio >= 0.8
```

**Step 2: Append ⚠ to bull label quality line**

Line 865 currently reads:
```pine
    combinedBullText += bullQualLine != "" ? "\n" + bullQualLine : ""
```

Replace with:
```pine
    string bwSuffix = bodyWarn ? " ⚠" : ""
    combinedBullText += bullQualLine != "" ? "\n" + bullQualLine + bwSuffix : (bwSuffix != "" ? "\n" + bwSuffix : "")
```

**Step 3: Append ⚠ to bear label quality line**

Line 1010 currently reads:
```pine
    combinedBearText += bearQualLine != "" ? "\n" + bearQualLine : ""
```

Replace with:
```pine
    string bwSuffix = bodyWarn ? " ⚠" : ""
    combinedBearText += bearQualLine != "" ? "\n" + bearQualLine + bwSuffix : (bwSuffix != "" ? "\n" + bwSuffix : "")
```

**Step 4: Verify in TradingView**

Compile. Look for signals with strong body bars (e.g. marubozu candles with ≥80% body). They should show `⚠` suffix. Signals with normal body should not.

**Step 5: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "v2.8: body ≥80% fakeout warning (⚠ on labels)"
```

---

### Task 3: Expand Signal-TF Tuple + Volume Ramp Computation (Item 5)

Add 4 historical volume bars to the `request.security` tuple, compute pre-move volume ramp, classify into buckets, and add glyphs to existing labels.

**Files:**
- Modify: `KeyLevelBreakout.pine:340-341` (request.security tuple)
- Insert after: `KeyLevelBreakout.pine:~422` (volume ramp computation, before Runner Score)
- Modify: `KeyLevelBreakout.pine:~865` (bull label glyphs)
- Modify: `KeyLevelBreakout.pine:~1010` (bear label glyphs)

**Step 1: Expand the request.security tuple**

Lines 340-341 currently read:
```pine
[sigC, sigO, sigH, sigL, sigPC, sigPC2, sigVol, sigVolPrev, sigVolSma] = request.security(syminfo.tickerid, i_signalTF,
     [close[1], open[1], high[1], low[1], close[2], close[3], volume[1], volume[2], ta.sma(volume, i_volLen)[1]], lookahead = barmerge.lookahead_on)
```

Replace with (add 4 vol bars + ATR):
```pine
[sigC, sigO, sigH, sigL, sigPC, sigPC2, sigVol, sigVolPrev, sigVolSma, sigVol2, sigVol3, sigVol4, sigVol5, sigATR14] = request.security(syminfo.tickerid, i_signalTF,
     [close[1], open[1], high[1], low[1], close[2], close[3], volume[1], volume[2], ta.sma(volume, i_volLen)[1], volume[3], volume[4], volume[5], volume[6], ta.atr(14)[1]], lookahead = barmerge.lookahead_on)
```

Note: `volume[3..6]` gives us signal bars [t-3] through [t-6]. Combined with existing `volume[1]` (sigVol) and `volume[2]` (sigVolPrev), we have 6 bars of volume history. `ta.atr(14)[1]` is signal-TF ATR for Item 7 (big-move flag).

**Step 2: Add volume ramp computation**

Insert after the `bearVolAlpha` line (~line 422), before Runner Score section:

```pine
// ─── Pre-Move Volume Ramp (v2.8) ───────────────────────
// Recent 3 bars avg vs prior 3 bars avg
float recentVol3 = (nz(sigVol) + nz(sigVolPrev) + nz(sigVol2)) / 3.0
float priorVol3  = (nz(sigVol3) + nz(sigVol4) + nz(sigVol5)) / 3.0
float preVolRamp = priorVol3 > 0 ? recentVol3 / priorVol3 : 1.0

// Classify: U-shaped edge (drying + explosive = good, moderate = trap)
bool isVolDrying    = preVolRamp < 0.5
bool isVolExplosive = preVolRamp > 5.0
bool isVolModerate  = preVolRamp >= 1.0 and preVolRamp < 2.0

// Signal-TF ATR for big-move detection
float sigRangeATR = not na(sigATR14) and sigATR14 > 0 ? (sigH - sigL) / sigATR14 : 0
bool isBigMove = sigRangeATR >= 2.0

// Volume ramp glyph for labels
string volRampGlyph = isVolDrying ? "🔇" : isVolExplosive ? "🔊" : ""
string bigMoveGlyph = isBigMove ? "⚡" : ""
```

**Step 3: Add glyphs to bull label text**

In the bull label section (after `bwSuffix` from Task 2), modify the quality line building to include ramp + big-move glyphs. The line that builds `combinedBullText` quality section needs the glyphs prepended to the quality line:

Replace the `combinedBullText` quality line code (from Task 2) with:
```pine
    string bwSuffix = bodyWarn ? " ⚠" : ""
    string sigGlyphs = bigMoveGlyph + volRampGlyph
    string glyphLine = sigGlyphs != "" ? sigGlyphs + " " : ""
    combinedBullText += bullQualLine != "" ? "\n" + glyphLine + bullQualLine + bwSuffix : (sigGlyphs != "" or bwSuffix != "" ? "\n" + sigGlyphs + bwSuffix : "")
```

Also upgrade label size when `isBigMove`:
Where `finalSize` is computed (~line 878):
```pine
    string finalSize = isDimBull ? size.tiny : isCooled ? size.tiny : isAftn ? size.tiny : (isBigMove or totalCount >= 2 ? size.large : (totalCount == 1 ? size.small : size.small))
```

**Step 4: Add glyphs to bear label text**

Same pattern in the bear label section (~line 1010):
```pine
    string bwSuffix = bodyWarn ? " ⚠" : ""
    string sigGlyphs = bigMoveGlyph + volRampGlyph
    string glyphLine = sigGlyphs != "" ? sigGlyphs + " " : ""
    combinedBearText += bearQualLine != "" ? "\n" + glyphLine + bearQualLine + bwSuffix : (sigGlyphs != "" or bwSuffix != "" ? "\n" + sigGlyphs + bwSuffix : "")
```

And upgrade `finalSize` for bear (~line 1023):
```pine
    string finalSize = isDimBear ? size.tiny : isCooled ? size.tiny : isAftn ? size.tiny : (isBigMove or totalCount >= 2 ? size.large : (totalCount == 1 ? size.small : size.small))
```

**Step 5: Verify in TradingView**

Compile. Check:
- Tuple still has ≤127 elements (now ~14 named vars → ~14 elements, well under limit)
- Labels show `🔇` on quiet signals, `🔊` on explosive volume ramp signals
- Labels show `⚡` on bars with range ≥ 2x signal-TF ATR (these should be large and rare)
- Normal signals have no extra glyphs

**Step 6: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "v2.8: volume ramp computation + big-move flag (🔇🔊⚡ glyphs)"
```

---

### Task 4: QBS/MC Standalone Signals (Item 6)

New signal type: fires when volume ramp fingerprint (Quiet Before Storm / Momentum Cascade) matches, even WITHOUT a key-level breakout. This is the core feature of v2.8.

**Files:**
- Modify: `KeyLevelBreakout.pine:39` (add input toggle after i_vwapSignal)
- Modify: `KeyLevelBreakout.pine:240-246` (session reset block, add QBS/MC vars)
- Insert after: `KeyLevelBreakout.pine:~698` (QBS/MC signal detection, after VWAP filtered signals)
- Insert after: `KeyLevelBreakout.pine:~729` (add to combined signal booleans)
- Insert before: `KeyLevelBreakout.pine:~843` (QBS/MC labels, before combined bull label)
- Modify: `KeyLevelBreakout.pine:~1400-1411` (alerts section)

**Step 1: Add input toggle**

After line 39 (`i_vwapSignal`), insert:
```pine
i_qbsSignal   = input.bool(true, "QBS/MC Signals (Vol Ramp Patterns)",  tooltip="Fire signals when pre-move volume pattern matches high-probability fingerprint (Quiet Before Storm / Momentum Cascade)", group="Signals")
```

**Step 2: Add session tracking variables**

In the session state area (after the VWAP zone session vars around line 232), find the `if newRegular` block that resets `vwapExitBull`. Before that block (~line 231), insert:

```pine
// ─── QBS/MC Session State ─────────────────────────
var bool qbsBullFired = false
var bool qbsBearFired = false
var bool mcBullFired  = false
var bool mcBearFired  = false
```

And in the `if newRegular` block at line 240, add resets:
```pine
    qbsBullFired := false
    qbsBearFired := false
    mcBullFired  := false
    mcBearFired  := false
```

**Step 3: Add CONF tracking variables for QBS/MC**

In the CONF tracking area (near line 234), add:
```pine
// ─── QBS/MC CONF Tracking ─────────────────────────
var int   qmcRTState    = 0       // 0=inactive, 1=monitoring, -1=failed
var label qmcRTLbl      = na
var string qmcRTBase    = ""
var float qmcRTEntry    = na
var int   qmcRTDir      = 0       // +1 bull, -1 bear
var int   qmcRTStart    = 0
var float qmcRTVolRatio = na
var int   qmcRTClosePos = na
```

And reset in `if newRegular`:
```pine
    qmcRTState := 0
    qmcRTLbl   := na
    qmcRTBase  := ""
    qmcRTEntry := na
    qmcRTDir   := 0
    qmcRTStart := 0
```

**Step 4: Add QBS/MC signal detection**

Insert after the VWAP signal detection and filtering section (~after line 720, before "Combined Signals" at line 722). These signals use the same pattern as VWAP signals (once per direction per session, reversal evidence stack):

```pine
// ─── QBS/MC Volume Ramp Signals (v2.8) ──────────────────
// QBS: Quiet Before Storm — volume drying before big bar
bool rQBS_bull = i_qbsSignal and isVolDrying and sigRangeATR >= 1.5
     and sigC > sigO and isRegular and newSigBar
bool rQBS_bear = i_qbsSignal and isVolDrying and sigRangeATR >= 1.5
     and sigC < sigO and isRegular and newSigBar

// MC: Momentum Cascade — explosive volume with big bar
bool rMC_bull = i_qbsSignal and isVolExplosive and sigRangeATR >= 1.5
     and sigC > sigO and isRegular and newSigBar
bool rMC_bear = i_qbsSignal and isVolExplosive and sigRangeATR >= 1.5
     and sigC < sigO and isRegular and newSigBar

// Filtered (evidence stack: ADX + Body, same as reversals)
bool sigQBS_bull = rQBS_bull and not qbsBullFired and fGateBull_rev
bool sigQBS_bear = rQBS_bear and not qbsBearFired and fGateBear_rev
bool sigMC_bull  = rMC_bull  and not mcBullFired  and fGateBull_rev
bool sigMC_bear  = rMC_bear  and not mcBearFired  and fGateBear_rev

// Any QBS/MC fired
bool qbsFired = sigQBS_bull or sigQBS_bear
bool mcFired  = sigMC_bull  or sigMC_bear

// Update session flags
if sigQBS_bull
    qbsBullFired := true
if sigQBS_bear
    qbsBearFired := true
if sigMC_bull
    mcBullFired := true
if sigMC_bear
    mcBearFired := true
```

**Step 5: Add to combined signal booleans**

After `anyReversal` (line 729), add:
```pine
anyQBSMC = qbsFired or mcFired
```

**Step 6: Add QBS/MC labels**

Insert before the "Combined Bull Label" section (~line 843). QBS/MC get their own standalone labels:

```pine
// ─── QBS/MC Labels (v2.8) ────────────────────────────────
if sigQBS_bull or sigMC_bull
    bool isQBS = sigQBS_bull
    string qmType = isQBS ? "🔇 QBS" : "🔊 MC"
    float rampVal = preVolRamp
    string rampStr = str.tostring(rampVal, "#.#") + "x"
    int score = finalScoreBull
    string scoreStr = score >= 1 ? " " + array.get(SCORE_GLYPHS, math.min(score, 5)) : ""
    string qmText = qmType + "\nBull " + rampStr + scoreStr
    // Dim check (reversal evidence stack)
    bool isDimQM = i_fMode == "Dim" and not evStackBull_rev
    if isDimQM
        qmText += "\n?"
    // Moderate ramp dimming (trap bucket)
    bool isModDim = isVolModerate
    color qmColor = isDimQM or isModDim ? color.new(color.gray, 70) : isQBS ? color.new(color.teal, 0) : color.new(color.orange, 0)
    color qmTextColor = isDimQM or isModDim ? color.new(color.gray, 50) : color.black
    if isModDim and not isDimQM
        qmText += "\n?"
    string qmSize = isBigMove ? size.large : size.normal
    label qmLbl = label.new(bar_index + shapeOff, na, qmText,
         yloc=yloc.belowbar, style=label.style_label_up,
         color=qmColor, textcolor=qmTextColor, size=qmSize)
    // CONF setup
    if i_confirm and not isOld
        qmcRTState    := 1
        qmcRTLbl      := qmLbl
        qmcRTBase     := qmText
        qmcRTEntry    := sigC
        qmcRTDir      := 1
        qmcRTStart    := sigBarIdx
        qmcRTVolRatio := volRatioBull
        qmcRTClosePos := bullClosePos

if sigQBS_bear or sigMC_bear
    bool isQBS = sigQBS_bear
    string qmType = isQBS ? "🔇 QBS" : "🔊 MC"
    float rampVal = preVolRamp
    string rampStr = str.tostring(rampVal, "#.#") + "x"
    int score = finalScoreBear
    string scoreStr = score >= 1 ? " " + array.get(SCORE_GLYPHS, math.min(score, 5)) : ""
    string qmText = qmType + "\nBear " + rampStr + scoreStr
    // Dim check (reversal evidence stack)
    bool isDimQM = i_fMode == "Dim" and not evStackBear_rev
    if isDimQM
        qmText += "\n?"
    // Moderate ramp dimming (trap bucket)
    bool isModDim = isVolModerate
    color qmColor = isDimQM or isModDim ? color.new(color.gray, 70) : isQBS ? color.new(color.teal, 0) : color.new(color.orange, 0)
    color qmTextColor = isDimQM or isModDim ? color.new(color.gray, 50) : color.black
    if isModDim and not isDimQM
        qmText += "\n?"
    string qmSize = isBigMove ? size.large : size.normal
    label qmLbl = label.new(bar_index + shapeOff, na, qmText,
         yloc=yloc.abovebar, style=label.style_label_down,
         color=qmColor, textcolor=qmTextColor, size=qmSize)
    // CONF setup
    if i_confirm and not isOld
        qmcRTState    := 1
        qmcRTLbl      := qmLbl
        qmcRTBase     := qmText
        qmcRTEntry    := sigC
        qmcRTDir      := -1
        qmcRTStart    := sigBarIdx
        qmcRTVolRatio := volRatioBear
        qmcRTClosePos := bearClosePos
```

**Step 7: Add QBS/MC CONF monitoring**

Insert after the 5-Minute Checkpoint section (~line 1165), before Per-Level Retest Monitoring:

```pine
// ─── QBS/MC Confirmation (v2.8) ────────────────────────
// Simple direction monitoring: did price continue in signal direction?
if qmcRTState == 1 and newSigBar and isRegular
    int elapsed = sigBarIdx - qmcRTStart
    if elapsed > 0
        bool continues = qmcRTDir == 1 ? sigC > qmcRTEntry : sigC < qmcRTEntry
        if continues
            // Auto-promote to CONF pass
            bool highConv = not na(qmcRTVolRatio) and qmcRTVolRatio >= 5.0 and not na(qmcRTClosePos) and qmcRTClosePos >= 80
            if not na(qmcRTLbl)
                if highConv
                    label.set_text(qmcRTLbl, qmcRTBase + "\n✓★")
                    label.set_color(qmcRTLbl, color.new(#FFD700, 0))
                    label.set_textcolor(qmcRTLbl, color.black)
                else
                    label.set_text(qmcRTLbl, qmcRTBase + "\n✓")
                    label.set_color(qmcRTLbl, qmcRTDir == 1 ? color.new(color.green, 0) : color.new(color.red, 0))
                    label.set_textcolor(qmcRTLbl, color.white)
            confPassCount  += 1
            confFailStreak := 0
            // VWAP exit tracking
            if qmcRTDir == 1
                vwapExitBull := true
                vwapExitBear := false
            else
                vwapExitBear := true
                vwapExitBull := false
            // 5-minute checkpoint
            checkpointEntry := sigC
            checkpointBar   := bar_index
            checkpointLbl   := qmcRTLbl
            checkpointDir   := qmcRTDir
            qmcRTState := 0
        else
            // Failed — price went against signal
            qmcRTState := -1
            confFailStreak += 1
            if not na(qmcRTLbl)
                label.set_text(qmcRTLbl, qmcRTBase + "\n✗")
                label.set_color(qmcRTLbl, color.new(color.gray, 60))
                label.set_textcolor(qmcRTLbl, color.new(color.gray, 40))
```

**Step 8: Add QBS/MC alerts**

In the programmatic alerts section (~line 1390), add after the reversal alerts:
```pine
if sigQBS_bull
    alert("🔇 QBS Bull: vol drying → explosion " + str.tostring(preVolRamp, "#.#") + "x", alert.freq_once_per_bar)
if sigQBS_bear
    alert("🔇 QBS Bear: vol drying → explosion " + str.tostring(preVolRamp, "#.#") + "x", alert.freq_once_per_bar)
if sigMC_bull
    alert("🔊 MC Bull: vol surging → continuation " + str.tostring(preVolRamp, "#.#") + "x", alert.freq_once_per_bar)
if sigMC_bear
    alert("🔊 MC Bear: vol surging → continuation " + str.tostring(preVolRamp, "#.#") + "x", alert.freq_once_per_bar)
```

In the alertcondition section (~line 1411), add:
```pine
alertcondition(qbsFired, "QBS — Quiet Before Storm", "🔇 Quiet Before Storm: vol drying → explosion")
alertcondition(mcFired,  "MC — Momentum Cascade",    "🔊 Momentum Cascade: vol surging → continuation")
alertcondition(anyBreakout or anyReversal or anyQBSMC, "Any Setup", "Breakout, reversal, or QBS/MC detected")
```

Note: This replaces the existing `alertcondition` on the last line that only covers breakout+reversal.

**Step 9: Verify in TradingView**

Compile. Check:
- QBS/MC labels appear as standalone cyan/orange labels
- They fire independently of breakouts (no key level required)
- Once per direction per session (test by counting on a busy day)
- CONF ✓/✗ appears after 1 signal bar
- Alerts fire in the alert log

**Step 10: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "v2.8: QBS/MC standalone signals (vol ramp fingerprint)"
```

---

### Task 5: Moderate Ramp Dimming (Item 8)

When `isVolModerate` (1-2x ramp) is true on ANY signal, dim to gray with `?`.

**Files:**
- Modify: `KeyLevelBreakout.pine:~867-878` (bull label dim logic)
- Modify: `KeyLevelBreakout.pine:~1012-1023` (bear label dim logic)

**Step 1: Add moderate ramp dimming to bull labels**

After the existing `isDimBull` logic (~line 867), add moderate ramp awareness. Modify the `isDimBull` line:

```pine
    bool isDimBull = (i_fMode == "Dim" and not (bullText != "" ? evStackBull : evStackBull_rev)) or isVolModerate
```

This means: dim if evidence stack fails OR if volume ramp is in the moderate (trap) bucket. The existing dim infrastructure (gray color + `?` suffix) handles the rest automatically.

**Step 2: Add moderate ramp dimming to bear labels**

Same pattern (~line 1012):

```pine
    bool isDimBear = (i_fMode == "Dim" and not (bearText != "" ? evStackBear : evStackBear_rev)) or isVolModerate
```

**Step 3: Verify in TradingView**

Compile. Signals during 1-2x volume ramp periods should appear dimmed (gray with `?`). Signals with drying or explosive volume should not be dimmed by this logic.

**Step 4: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "v2.8: moderate ramp dimming (1-2x vol = trap bucket)"
```

---

### Task 6: Version Bump + Final Verification

**Files:**
- Modify: `KeyLevelBreakout.pine:2` (version comment)
- Modify: `KeyLevelBreakout.pine:425` (Runner Score comment)

**Step 1: Update version comment**

Line 2 currently reads:
```pine
// Detects bullish/bearish 5m candle closes through key levels (v2.7)
```

Replace with:
```pine
// Detects bullish/bearish 5m candle closes through key levels (v2.8)
```

**Step 2: Update Runner Score comment**

Line 425 currently reads:
```pine
// 5 factors: VWAP aligned, vol 2-5x, time 10-11, level quality (bear=LOW), not D-tier symbol
```

Replace with:
```pine
// 5 factors: VWAP aligned, vol ≥5x, time 9:30-10, level quality (bear=LOW), not D-tier symbol
```

**Step 3: Full verification in TradingView**

Add to multiple symbols (TSLA, AAPL, SPY, QQQ, TSM). Verify:
1. ✅ Compiles without errors
2. ✅ Runner Score fires 9:30-9:59 (not 10:00-10:59)
3. ✅ TSM signals show -1 Runner Score
4. ✅ closeLoc no longer blocks at 0.3-0.4 range
5. ✅ Body ≥80% signals show `⚠`
6. ✅ Volume ramp glyphs appear (`🔇` / `🔊`) on existing signals
7. ✅ Big move bars (2x ATR) show `⚡` and `size.large`
8. ✅ QBS/MC standalone labels appear in cyan/orange
9. ✅ QBS/MC get CONF ✓/✗ tracking
10. ✅ Moderate ramp (1-2x) dims existing signals
11. ✅ Alerts fire correctly

**Step 4: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "v2.8: Big-Move Fingerprint Integration (version bump + verified)"
```

---

## Implementation Order Summary

| Task | Item(s) | Lines changed | Risk |
|------|---------|--------------|------|
| 1 | Constants (1,2,3) | ~4 | Zero — trivial value changes |
| 2 | Body warning (4) | ~5 | Zero — visual only |
| 3 | Vol ramp + ATR (5,7) | ~20 | Low — tuple expansion, new vars |
| 4 | QBS/MC signals (6) | ~80 | Medium — new signal type, CONF |
| 5 | Moderate dim (8) | ~2 | Zero — reuses existing dim infra |
| 6 | Version bump | ~2 | Zero |

**Total: ~113 new/changed lines. Target: v2.7 1,411 → v2.8 ~1,524.**

## Resource Budget Check

| Resource | v2.7 | v2.8 | Limit |
|----------|------|------|-------|
| request.security calls | 11 | 11 | 40 |
| Tuple elements | 9 | 14 (+5) | 127 |
| max_labels_count | 500 | 500 | 500 |
| New inputs | 0 | 1 | — |
| New alertconditions | 0 | 2 | — |
| Lines of code | ~1,411 | ~1,524 | No limit |
