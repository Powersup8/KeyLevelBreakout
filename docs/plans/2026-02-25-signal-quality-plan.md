# Signal Quality v2.0 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reduce noise (counter-trend reversals, label clustering) and catch more good signals (late retests, afternoon reversals) in KeyLevelBreakout.pine.

**Architecture:** Four independent changes to a single Pine Script v6 indicator file, each toggleable via inputs with backward-compatible defaults. No test framework — verify visually on TradingView after each change.

**Tech Stack:** Pine Script v6, TradingView

---

### Task 1: VWAP Directional Filter on Reversals

**Files:**
- Modify: `KeyLevelBreakout.pine:349-355` (reversal helpers)

**Context:** Input `i_vwapFilter` (line 39) and `vwapVal = ta.vwap` (line 238) are already in the code. Just need to gate the reversal helper functions.

**Step 1: Add VWAP gate to bullRev helper**

Change line 349-351 from:
```pine
bullRev(float wick, float body) =>
    not na(wick) and not na(body) and isRegular and newSigBar and isSetupWindow
     and sigC > sigO and sigL <= body and sigC > body and volPassBull
```
to:
```pine
bullRev(float wick, float body) =>
    not na(wick) and not na(body) and isRegular and newSigBar and isSetupWindow
     and sigC > sigO and sigL <= body and sigC > body and volPassBull
     and (not i_vwapFilter or not na(vwapVal) and sigC > vwapVal)
```

**Step 2: Add VWAP gate to bearRev helper**

Change line 353-355 from:
```pine
bearRev(float wick, float body) =>
    not na(wick) and not na(body) and isRegular and newSigBar and isSetupWindow
     and sigC < sigO and sigH >= body and sigC < body and volPassBear
```
to:
```pine
bearRev(float wick, float body) =>
    not na(wick) and not na(body) and isRegular and newSigBar and isSetupWindow
     and sigC < sigO and sigH >= body and sigC < body and volPassBear
     and (not i_vwapFilter or not na(vwapVal) and sigC < vwapVal)
```

**Step 3: Verify on TradingView**

1. Load on 5m MSFT chart. With VWAP filter OFF: signals identical to before.
2. Toggle VWAP filter ON: counter-trend orange bear reversals during bullish sessions (above VWAP) should disappear. The cyan ORB L reversal at the bottom (below VWAP) should still fire.

**Step 4: Commit**
```
feat: add VWAP directional filter for reversals
```

---

### Task 2: Reversal Window Toggle

**Files:**
- Modify: `KeyLevelBreakout.pine:33-36` (setup inputs), `:349-355` (reversal helpers)

**Step 1: Add toggle input**

After line 34 (`i_showReversal`), add:
```pine
i_limitRevWin  = input.bool(false,  "Limit Reversal Window",           group="Setups")
```

**Step 2: Change reversal helpers to use conditional window**

In both `bullRev` and `bearRev`, replace `isSetupWindow` with:
```pine
(not i_limitRevWin or isSetupWindow)
```

So bullRev becomes (after Task 1):
```pine
bullRev(float wick, float body) =>
    not na(wick) and not na(body) and isRegular and newSigBar
     and (not i_limitRevWin or isSetupWindow)
     and sigC > sigO and sigL <= body and sigC > body and volPassBull
     and (not i_vwapFilter or not na(vwapVal) and sigC > vwapVal)
```

Same pattern for bearRev.

**Step 3: Verify on TradingView**

1. `Limit Reversal Window` OFF (default): reversals fire during entire regular session including afternoon.
2. Toggle ON + window "0930-1130": only reversals within that window. Matches old behavior.

**Step 4: Commit**
```
feat: make reversal time window optional (default full session)
```

---

### Task 3: Retest System Overhaul

**Files:**
- Modify: `KeyLevelBreakout.pine:29-31` (inputs), `:145-165` (state vars), `:682-770` (retest monitoring), `:685-695` (buildRetestSuffix)

This is the largest task. Changes in sub-steps:

**Step 1: Replace confirmBars input with dropdown**

Change line 30 from:
```pine
i_confirmBars = input.int(10,     "Confirmation Window (signal bars)", minval=3, maxval=30, group="Confirmation")
```
to:
```pine
i_retestWindow = input.string("Session", "Retest Window", options=["Short (50 min)", "Extended (2.5 hr)", "Session"], group="Confirmation")
```

Add after it (compute max elapsed in signal bars):
```pine
retestMaxElapsed = i_retestWindow == "Short (50 min)" ? 10 : i_retestWindow == "Extended (2.5 hr)" ? 30 : 99999
```

**Step 2: Add retest proximity input**

After the retest window input, add:
```pine
i_retestProx = input.float(3.0, "Retest Proximity (% of ATR)", minval=0.5, step=0.5, group="Confirmation")
```

In the Filter Computations section (after line 239 `rearmBuf`), add:
```pine
retestBuf = not na(dailyATR) ? dailyATR * i_retestProx / 100.0 : rearmBuf
```

**Step 3: Change retest symbol from ⟳ to ◆**

In `buildRetestSuffix` (line 690), change:
```pine
            string line = "⟳" + toSup(bars) + " " + array.get(names, i)
```
to:
```pine
            string line = "◆" + toSup(bars) + " " + array.get(names, i)
```

**Step 4: Un-gate retest monitoring from newSigBar, use chart-TF data**

Change bull retest monitoring (line 698) from:
```pine
if i_confirm and bRTState == 1 and not na(bRTConsLvl) and newSigBar
```
to:
```pine
if i_confirm and bRTState == 1 and not na(bRTConsLvl) and isRegular
```

Inside the bull block, change elapsed and invalidation to use signal bars for timeout but chart-TF for detection:
```pine
    int elapsed = sigBarIdx - bRTStart
    if close < bRTConsLvl - rearmBuf
        bRTState := -1
```
(Change `sigC` → `close` for invalidation check only — detection uses chart-TF data.)

Change per-level retest detection (line 711) from:
```pine
                if sigL <= lvl + rearmBuf and sigC > lvl
```
to:
```pine
                if low <= lvl + retestBuf and close > lvl
```

Same changes for bear monitoring (line 730+):
- Gate: `isRegular` instead of `newSigBar`
- Invalidation: `close >` instead of `sigC >`
- Detection: `high >= lvl - retestBuf and close < lvl` instead of `sigH/sigC`

**Step 5: Add independent retest labels + alerts in normal mode**

In the bull retest `if anyNew` block (after line 716), replace:
```pine
        if anyNew
            string suffix = buildRetestSuffix(bRT, bRTBar, bRTInfo, bRTLvl, bullLvlNames, bRTStart, true)
            if i_retestOnly
                string rtText = str.substring(suffix, 1)
                label.new(bar_index + shapeOff, na, rtText,
                     yloc=yloc.belowbar, style=label.style_label_up,
                     color=bullColor, textcolor=color.black, size=size.small)
                alert("Retest: " + rtText, alert.freq_once_per_bar_close)
            else if not na(bRTLbl)
                label.set_text(bRTLbl, bRTBase + suffix)
```
with:
```pine
        if anyNew
            string suffix = buildRetestSuffix(bRT, bRTBar, bRTInfo, bRTLvl, bullLvlNames, bRTStart, true)
            string rtText = str.substring(suffix, 1)  // skip leading \n
            // Independent retest label (always, unless old)
            if not isOld
                label.new(bar_index, na, rtText,
                     yloc=yloc.belowbar, style=label.style_label_up,
                     color=bullColor, textcolor=color.black, size=size.small)
                alert("Retest: " + rtText, alert.freq_once_per_bar_close)
            // Also update original breakout label
            if not i_retestOnly and not na(bRTLbl)
                label.set_text(bRTLbl, bRTBase + suffix)
```

Same pattern for bear retest block.

Note: retest labels use `bar_index` (no shapeOff) since they occur on chart-TF bars, not signal-TF bars.

**Step 6: Replace i_confirmBars references with retestMaxElapsed**

Line 726 (bull timeout):
```pine
        if elapsed >= retestMaxElapsed and bRTState == 1
```

Line 758 (bear timeout):
```pine
        if elapsed >= retestMaxElapsed and sRTState == 1
```

**Step 7: Verify on TradingView**

1. "Session" mode: retests fire all day as long as breakout wasn't invalidated. Check SPY ORB H retest around 11:15.
2. "Short" mode: same as before (50 min window).
3. Retest label shows `◆³ ORB H 2.1x ^85` as independent label.
4. Alert fires: "Retest: ◆³ ORB H 2.1x ^85".
5. Original breakout label also updated with suffix.

**Step 8: Commit**
```
feat: overhaul retest system — session-long tracking, independent labels, ◆ symbol
```

---

### Task 4: Label Management (Merge + Cooldown + Offset)

**Files:**
- Modify: `KeyLevelBreakout.pine:529-677` (label creation section)

**Step 1: Add cooldown input and state vars**

After the existing inputs (around line 31), add:
```pine
i_cooldownBars = input.int(2, "Signal Cooldown (signal bars)", minval=0, maxval=10, group="Signals")
```

Before the label creation section (before `isOld` at line 529), add state vars:
```pine
var int lastBullSigBar = -999
var int lastBearSigBar = -999
```

**Step 2: Restructure label creation — merge breakout + reversal per direction**

Currently the code has separate blocks:
1. `if bullText != ""` → breakout label (lines 532-573)
2. `if revBullText != ""` → reversal label (lines 617-646)

Restructure to build ONE combined text per direction, then create ONE label:

```pine
// ─── Combined Bull Label ─────────────────────────────────
string combinedBullText = ""
if bullText != ""
    combinedBullText := bullText
if revBullText != ""
    combinedBullText := combinedBullText + (combinedBullText != "" ? "\n" : "") + revBullText
if combinedBullText != ""
    combinedBullText += bullQualLine != "" ? "\n" + bullQualLine : ""
    // Determine color: breakout color if breakout present, reversal color if reversal-only
    color lblColor = bullText != "" ? bullColor : revBullColor
    int totalCount = bullCount + revBullCount
    // Cooldown dimming
    bool isCooled = i_cooldownBars > 0 and (sigBarIdx - lastBullSigBar) <= i_cooldownBars
    color finalColor = isCooled ? color.new(color.gray, 70) : (isOld ? color.new(color.gray, 90) : lblColor)
    color finalText = isCooled ? color.new(color.gray, 50) : (isOld ? color.new(color.gray, 70) : color.black)
    size finalSize = isCooled ? size.tiny : (totalCount > 1 ? size.normal : size.small)

    if i_retestOnly and bullText != "" and not isOld
        label.new(bar_index + shapeOff, na, "·", yloc=yloc.belowbar,
             style=label.style_label_up, color=color.new(color.gray, 80),
             textcolor=color.new(color.gray, 60), size=size.tiny)
    else
        label lbl = label.new(bar_index + shapeOff, na, combinedBullText,
             yloc=yloc.belowbar, style=label.style_label_up,
             color=finalColor, textcolor=finalText, size=finalSize)
        if i_confirm and not isOld and bullText != ""
            bRTLbl  := lbl
            bRTBase := combinedBullText

    // Update cooldown tracker
    if not isOld and not isCooled
        lastBullSigBar := sigBarIdx

    // Confirmation setup (keep existing logic for breakout tracking)
    if bullText != "" and i_confirm and not isOld
        // ... existing bRT setup code (lines 549-573) stays here ...
```

Same pattern for combined bear label.

**Note:** The reversal label tracking (graying out superseded labels) and reclaim context moves into the combined block. The `revLblPMH` etc. tracking would reference the combined label.

**Step 3: Add vertical offset for adjacent labels**

Add state vars:
```pine
var int lastBullLblBar = -999
var int lastBearLblBar = -999
```

In label creation, check if previous label was within 1 bar:
```pine
    bool needsOffset = (bar_index + shapeOff - lastBullLblBar) <= 1 and lastBullLblBar >= 0
    if needsOffset and not na(dailyATR)
        label lbl = label.new(bar_index + shapeOff, low - dailyATR * 0.15,
             combinedBullText, yloc=yloc.price, style=label.style_label_up,
             color=finalColor, textcolor=finalText, size=finalSize)
    else
        label lbl = label.new(bar_index + shapeOff, na, combinedBullText,
             yloc=yloc.belowbar, style=label.style_label_up,
             color=finalColor, textcolor=finalText, size=finalSize)
    lastBullLblBar := bar_index + shapeOff
```

For bear labels: `high + dailyATR * 0.15` with `yloc.price`.

**Step 4: Move reversal supersede logic into combined block**

The reversal label graying (lines 618-631, 649-662) needs to run before label creation. Move it to before the combined label is created, so prior reversal labels get grayed when a new combined label fires.

**Step 5: Update alerts for combined labels**

In the alerts section (lines 805+), the alerts for breakouts and reversals stay separate (they describe different setup types). No change needed — alerts fire from their original conditions, not the label.

**Step 6: Verify on TradingView**

1. Same-bar breakout + reversal → single combined label, not two stacked.
2. Rapid signals at open → first signal full color, subsequent within 2 bars dimmed/tiny.
3. Adjacent labels → vertically offset, not overlapping.
4. All filters OFF → behavior matches pre-change (except merged labels).

**Step 7: Commit**
```
feat: label management — merge same-bar, cooldown dimming, vertical offset
```

---

### Task 5: Documentation Updates

**Files:**
- Modify: `KeyLevelBreakout.md`
- Modify: `KeyLevelBreakout_TV.md`
- Modify: `KeyLevelBreakout_Improvements.md`

**Step 1: Update KeyLevelBreakout.md**

- Add VWAP filter to Features and Inputs table
- Update reversal window description
- Rewrite retest section for new dropdown + independent labels + ◆ symbol
- Add label management description (merge, cooldown, offset)
- Add v2.0 changelog

**Step 2: Update KeyLevelBreakout_TV.md**

- Add VWAP filter bullet
- Update reversal and retest descriptions
- Mention label merge behavior

**Step 3: Update KeyLevelBreakout_Improvements.md**

- Mark VWAP filter (#3) as IMPLEMENTED v2.0
- Mark retest overhaul as IMPLEMENTED v2.0
- Update item #7 retest TODO as resolved
- Add note about label management

**Step 4: Commit**
```
docs: update all documentation for v2.0 signal quality improvements
```
