# Plan: Directional Volume + Close Position + Post-Breakout Confirmation

## Context

Three improvements to `KeyLevelBreakout.pine` emerged from volume/breakout research:

1. **Directional Volume Borrowing** — the blind `max(sigVol, sigVolPrev)` can borrow opposing-direction volume (e.g., a big red candle's 3x volume validates a bullish breakout). Fix: only borrow if the prior bar moved in the same direction.

2. **Close Position Ratio** — research shows where the close sits within the bar's range is the best single-bar proxy for buying/selling pressure. Display as informational metric in labels.

3. **Post-Breakout Confirmation** — after the 5m breakout signal fires, monitor on the chart timeframe (1m) for follow-through, retest-and-hold, or failure. Update the label text with ✓, ⟳✓, or ✗.

## Changes to `KeyLevelBreakout.pine`

### 1. New Inputs (after line 25)

```pine
i_closePos    = input.bool(true,  "Show Close Position %",           group="Quality")

i_confirm     = input.bool(true,  "Post-Breakout Confirmation",     group="Confirmation")
i_confirmBars = input.int(10,     "Confirmation Window (chart bars)", minval=3, maxval=30, group="Confirmation")
```

No input needed for directional volume — it replaces the existing undirected logic (always better).

### 2. Confirmation State Variables (after line 78, before the `newRegular` block)

Must be declared before `newRegular` so the session reset can reference them.

```pine
// ─── Post-Breakout Confirmation State ───────────────────
var label  lastBullLbl       = na
var string lastBullText      = ""
var float  lastBullLvl       = na
var int    lastBullStart     = 0
var int    lastBullState     = 0  // 0=none, 1=monitoring, 2=retest-confirmed, 3=time-confirmed, -1=failed
var int    prevBullConfState = 0

var label  lastBearLbl       = na
var string lastBearText      = ""
var float  lastBearLvl       = na
var int    lastBearStart     = 0
var int    lastBearState     = 0
var int    prevBearConfState = 0
```

### 3. Session Reset (append to `newRegular` block, lines 80-88)

```pine
    // Reset confirmation state at session open
    if i_confirm
        lastBullState     := 0
        lastBearState     := 0
        prevBullConfState := 0
        prevBearConfState := 0
```

### 4. Directional Volume + Close Position (replace lines 114-120)

Replace the blind `sigVolMax` with directional borrowing, split all vol variables by direction, add close position computation:

```pine
// Directional volume: borrow prior bar only if it moved in the same direction
sigVolBull   = sigPC > sigPC2 ? math.max(nz(sigVol), nz(sigVolPrev)) : nz(sigVol)
sigVolBear   = sigPC < sigPC2 ? math.max(nz(sigVol), nz(sigVolPrev)) : nz(sigVol)
volPassBull  = not i_volFilter or na(volThreshold) or sigVolBull > volThreshold
volPassBear  = not i_volFilter or na(volThreshold) or sigVolBear > volThreshold
volRatioBull = not na(volBase) and volBase > 0 ? sigVolBull / volBase : na
volRatioBear = not na(volBase) and volBase > 0 ? sigVolBear / volBase : na
bullVolStr   = i_volFilter and not na(volRatioBull) ? " " + str.tostring(volRatioBull, "#.#") + "x" : ""
bearVolStr   = i_volFilter and not na(volRatioBear) ? " " + str.tostring(volRatioBear, "#.#") + "x" : ""
bullVolAlpha = i_volFilter and not na(volRatioBull) ? math.max(0, math.round(60 - volRatioBull * 20)) : 0
bearVolAlpha = i_volFilter and not na(volRatioBear) ? math.max(0, math.round(60 - volRatioBear * 20)) : 0
bullColor    = color.new(color.green, bullVolAlpha)
bearColor    = color.new(color.red, bearVolAlpha)

// Close position: where did the close land within the bar's range? (0-100%)
sigRng       = sigH - sigL
bullClosePos = sigRng > 0 ? math.round((sigC - sigL) / sigRng * 100) : na
bearClosePos = sigRng > 0 ? math.round((sigH - sigC) / sigRng * 100) : na
```

- When `sigPC == sigPC2` (flat prior bar), both directions fall back to breakout-bar-only volume. Correct.
- When volume filter is OFF, `volPassBull/Bear = true` regardless. No regression.

### 5. Breakout Helpers (lines 146-156)

Change `volPass` → `volPassBull` in `bullBreak`, `volPassBear` in `bearBreak`. Two single-word edits.

### 6. Close Position Strings (insert after bearText builder, ~line 220)

```pine
bullPosStr = i_closePos and not na(bullClosePos) ? " ^" + str.tostring(bullClosePos) : ""
bearPosStr = i_closePos and not na(bearClosePos) ? " v" + str.tostring(bearClosePos) : ""
```

Compact format: `^78` = "close at 78% toward the high", `v82` = "close at 82% toward the low".

### 7. Label Creation + Confirmation Capture (replace lines 227-238)

Labels now use directional vol strings + close position. Capture state for confirmation monitoring.

```pine
if bullText != ""
    string fullBullText = bullText + bullVolStr + bullPosStr
    label lbl = label.new(bar_index + shapeOff, na, fullBullText,
         yloc=yloc.belowbar, style=label.style_label_up,
         color=isOld ? color.new(color.gray, 90) : bullColor,
         textcolor=isOld ? color.new(color.gray, 70) : color.white,
         size=bullCount > 1 ? size.normal : size.small)
    if i_confirm and not isOld
        if lastBullState == 1
            lastBullState := 3
            label.set_text(lastBullLbl, lastBullText + " ✓")
        float lvl = na
        if sigBullPMH
            lvl := na(lvl) ? pmHigh : math.min(lvl, pmHigh)
        if sigBullYH
            lvl := na(lvl) ? yestHigh : math.min(lvl, yestHigh)
        if sigBullWH
            lvl := na(lvl) ? weekHigh : math.min(lvl, weekHigh)
        if sigBullOH
            lvl := na(lvl) ? orbHigh : math.min(lvl, orbHigh)
        lastBullLbl   := lbl
        lastBullText  := fullBullText
        lastBullLvl   := lvl
        lastBullStart := bar_index
        lastBullState := 1

if bearText != ""
    string fullBearText = bearText + bearVolStr + bearPosStr
    label lbl = label.new(bar_index + shapeOff, na, fullBearText,
         yloc=yloc.abovebar, style=label.style_label_down,
         color=isOld ? color.new(color.gray, 90) : bearColor,
         textcolor=isOld ? color.new(color.gray, 70) : color.white,
         size=bearCount > 1 ? size.normal : size.small)
    if i_confirm and not isOld
        if lastBearState == 1
            lastBearState := 3
            label.set_text(lastBearLbl, lastBearText + " ✓")
        float lvl = na
        if sigBearPML
            lvl := na(lvl) ? pmLow : math.max(lvl, pmLow)
        if sigBearYL
            lvl := na(lvl) ? yestLow : math.max(lvl, yestLow)
        if sigBearWL
            lvl := na(lvl) ? weekLow : math.max(lvl, weekLow)
        if sigBearOL
            lvl := na(lvl) ? orbLow : math.max(lvl, orbLow)
        lastBearLbl   := lbl
        lastBearText  := fullBearText
        lastBearLvl   := lvl
        lastBearStart := bar_index
        lastBearState := 1
```

- **Confluence level tracking:** lowest broken level for bull (hardest to hold), highest for bear.
- **Auto-promotion:** if a previous breakout was still monitoring when a new one fires, promote to confirmed (it survived until the next breakout).
- **`not isOld` guard:** don't start monitoring ancient historical labels.

### 8. Confirmation Monitoring Block (insert before "Level Lines" section)

Runs every chart bar (not gated by `newSigBar`) for real-time feedback:

```pine
// ─── Post-Breakout Confirmation Monitoring ────────────────
if i_confirm and lastBullState == 1 and not na(lastBullLvl)
    int elapsed = bar_index - lastBullStart
    if close < lastBullLvl - rearmBuf
        lastBullState := -1
        label.set_text(lastBullLbl, lastBullText + " ✗")
        label.set_color(lastBullLbl, color.new(color.gray, 60))
        label.set_textcolor(lastBullLbl, color.new(color.gray, 40))
    else if elapsed >= 2 and low <= lastBullLvl + rearmBuf and close > lastBullLvl
        lastBullState := 2
        label.set_text(lastBullLbl, lastBullText + " ⟳✓")
    else if elapsed >= i_confirmBars
        lastBullState := 3
        label.set_text(lastBullLbl, lastBullText + " ✓")

if i_confirm and lastBearState == 1 and not na(lastBearLvl)
    int elapsed = bar_index - lastBearStart
    if close > lastBearLvl + rearmBuf
        lastBearState := -1
        label.set_text(lastBearLbl, lastBearText + " ✗")
        label.set_color(lastBearLbl, color.new(color.gray, 60))
        label.set_textcolor(lastBearLbl, color.new(color.gray, 40))
    else if elapsed >= 2 and high >= lastBearLvl - rearmBuf and close < lastBearLvl
        lastBearState := 2
        label.set_text(lastBearLbl, lastBearText + " ⟳✓")
    else if elapsed >= i_confirmBars
        lastBearState := 3
        label.set_text(lastBearLbl, lastBearText + " ✓")

// Confirmation alerts (fire once per state transition)
if i_confirm
    if lastBullState != prevBullConfState
        if lastBullState == 2 or lastBullState == 3
            alert("Confirmed: " + lastBullText, alert.freq_once_per_bar_close)
        if lastBullState == -1
            alert("Failed: " + lastBullText, alert.freq_once_per_bar_close)
        prevBullConfState := lastBullState
    if lastBearState != prevBearConfState
        if lastBearState == 2 or lastBearState == 3
            alert("Confirmed: " + lastBearText, alert.freq_once_per_bar_close)
        if lastBearState == -1
            alert("Failed: " + lastBearText, alert.freq_once_per_bar_close)
        prevBearConfState := lastBearState
```

- **`elapsed >= 2`** prevents instant retest confirmation on the bar right after breakout.
- **Failure uses `rearmBuf`** — consistent with invalidation logic.
- **Retest zone:** price wick reaches within `rearmBuf` of the level, then close holds on the right side.
- **State transition detection** ensures alerts fire exactly once.

### 9. Alert Text Update (lines 251-253)

Include volume + close position in breakout alerts:

```pine
alert("Bullish breakout: " + bullText + bullVolStr + bullPosStr, ...)
alert("Bearish breakout: " + bearText + bearVolStr + bearPosStr, ...)
```

### 10. Documentation

- **KeyLevelBreakout.md**: Update Features bullets, Inputs table (3 new rows), add "Post-Breakout Confirmation" section, add v1.6 changelog
- **KeyLevelBreakout_Improvements.md**: Mark Volume and ATR as "further refined v1.6", add confirmation as implemented

## Files Modified

| File | Changes |
|------|---------|
| `KeyLevelBreakout.pine` | 10 edit groups (~+76 lines, 264→~340) |
| `KeyLevelBreakout.md` | Feature descriptions, inputs table, new section, changelog |
| `KeyLevelBreakout_Improvements.md` | Status updates |

## Verification

- Volume filter OFF → `volPassBull/Bear = true`, no regression
- ATR buffer OFF → `effLvl = level`, wick check collapses to `sigC > level`, no regression
- Confirmation OFF → no state tracking, no label updates, no confirmation alerts
- Close position OFF → no `^XX`/`vXX` in labels
- Prior bar flat (`sigPC == sigPC2`) → falls back to breakout-bar-only volume
- Confluence → tracks most conservative level (lowest for bull, highest for bear)
- Rapid successive breakouts → previous monitoring auto-promotes to confirmed
- Session open → confirmation state resets
- Unicode characters (✓, ✗, ⟳) → test on TradingView web; if rendering issues, fall back to ASCII
