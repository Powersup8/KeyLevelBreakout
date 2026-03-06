# v3.2 Data-Driven Upgrades — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement 5 data-driven changes to KeyLevelBreakout.pine (v3.1a → v3.2) that collectively add ~+24.6 ATR: suppress losing ORB L bull REVs, add 4 midday levels, enable EXREV bypass for bear REVs, resurrect FADE with new trigger, and reassign HIGH levels from BRK to REV.

**Architecture:** All changes are in a single Pine Script v6 file. Changes are ordered safest→riskiest. Each change touches specific sections: inputs, level calculations, raw signals, filtered signals, signal counts, label text, labels, alerts, logs, and plots. The file follows a top-down flow: inputs → calculations → raw signals → filtered signals → counts → labels → CONF → alerts → plots.

**Tech Stack:** Pine Script v6, TradingView indicator

**Design doc:** `docs/plans/2026-03-06-v32-data-driven-upgrades-design.md`

---

## Context for the Implementer

### File Structure (KeyLevelBreakout.pine, 1872 lines)

| Section | Lines | Purpose |
|---------|-------|---------|
| Inputs | 7-73 | Level toggles, filter settings, debug flags |
| Session detection | 75-84 | Time zones, session windows, `isPre950` |
| Level calculations | 86-152 | PM H/L, Yest OHLC, Week OHLC, ORB H/L, PD Mid, PD LH L |
| Zone bounds | 159-173 | Body-edge calculations for fill bands |
| Breakout/reversal flags | 175-200 | `var bool` flags, reset in `newRegular` block |
| CONF state | 222-296 | Retest tracking, FADE state, RNG state |
| Session reset | 297-319 | `if newRegular` block — resets all daily state |
| Evidence stack | 475-503 | `bodyRatio`, `fCandle_*`, `evStack*`, `fGate*`, `emaGate*` |
| Raw BRK signals | 742-761 | `rBullPMH`, `rBearPML`, etc. |
| Filtered BRK signals | 764-773 | `sigBullPMH`, etc. + gates |
| Flag updates | 776-797 | Set `xPMH`, `xPML` etc. after raw fire |
| Raw REV signals | 799-824 | `rRevBullPML`, `rRevBearPMH`, etc. |
| Filtered REV signals | 830-850 | `sigRevBullPML`, etc. + REV gate + EMA gate |
| REV flag updates | 852-870 | Set `rPMH`, `rPML` etc. |
| QBS signals | 879-889 | Quiet Before Storm |
| Combined signals | 891-898 | `anyBull`, `anyBear`, `anyRevBull`, `anyRevBear` |
| FADE signals | 900-915 | Failed breakout fade detection |
| RNG signals | 917-935 | Range+Vol breakout |
| BRK label text | 939-962 | `bullText`, `bearText` assembly |
| REV label text | 990-1053 | `revBullText`, `revBearText` assembly |
| FADE/RNG labels | 1142-1182 | Purple FADE, teal RNG labels |
| Combined labels | 1184-1243 | Merged BRK+REV labels with dimming |
| CONF monitoring | 1620-1700 | Retest checks, FADE trigger on CONF fail |
| Plots | 1808-1842 | Level lines + zone fills |
| Alerts | 1844-1872 | `alert()` + `alertcondition()` |

### Key Patterns

**Adding a new level** requires touching these sections (in order):
1. Input toggle (line ~13)
2. Level calculation (line ~152)
3. Breakout flag `var bool` (line ~188)
4. Session reset in `newRegular` (line ~319)
5. Raw signal (line ~761)
6. Filtered signal (line ~773 or ~850)
7. Flag update (line ~797)
8. Signal count `anyBull`/`anyBear` or `anyRevBull`/`anyRevBear` (line ~896)
9. Label text (line ~962 or ~1050)
10. Count expression (line ~974 or ~1053)
11. Plot line (line ~1820)

**Signal filtering pattern:**
```pine
// BRK: evidence stack + EMA gate
sigBullPMH = rBullPMH and (not i_firstOnly or not xPMH) and fGateBull and (emaGateBull or isPre950)

// REV: REV-only evidence stack + EMA gate (except PD Mid which has no EMA gate)
sigRevBullPML = rRevBullPML and (not i_firstOnly or not rPML) and fGateBull_rev and (emaGateBull or isPre950)
```

**Label text pattern:**
```pine
// BRK levels:
if sigBullPMH
    bullText := bullText + (bullText != "" ? " + " : "") + "PM H"

// REV levels:
if sigRevBullPML
    string pfx = i_showReclaim and hadBrkPML and rclBullOK ? "~~ " : "~ "
    revBullText := revBullText + (revBullText != "" ? " + " : "") + pfx + "PM L"
```

---

## Task 1: ORB L Bull REV Suppress

**Risk:** Minimal — removal only. Eliminates 143 signals with 27% win rate, all net negative.
**ATR impact:** +12.5

**Files:**
- Modify: `KeyLevelBreakout.pine:835` (sigRevBullOL)
- Modify: `KeyLevelBreakout.pine:896` (anyRevBull)
- Modify: `KeyLevelBreakout.pine:1011-1015` (revBullText for ORB L)
- Modify: `KeyLevelBreakout.pine:1052` (revBullCount)

### Step 1: Suppress sigRevBullOL

At line 835, the current code is:
```pine
sigRevBullOL  = rRevBullOL  and (not i_firstOnly or not rOL)  and fGateBull_rev and (emaGateBull or isPre950)
```

Change to:
```pine
sigRevBullOL  = false  // v3.2: ORB L bull REV suppressed — 27% win, -12.5 ATR net negative
```

### Step 2: Verify no side effects

`sigRevBullOL` is referenced in:
- Line 896: `anyRevBull` — harmless (always false, OR chain still works)
- Line 1011-1015: label text — harmless (if-block never entered)
- Line 1052: `revBullCount` — harmless (always adds 0)
- Lines 859-860: flag tracking — harmless (never fires)

No other references. No removal needed — just setting to `false` is cleanest.

### Step 3: Commit

```bash
git add KeyLevelBreakout.pine
git commit -m "v3.2: suppress ORB L bull REV — 27% win, -12.5 ATR drain"
```

### Regression check
- All other REV signals should fire identically
- `anyRevBull` should fire slightly less often (ORB L signals removed)
- No impact on BRK, FADE, RNG, QBS, or bear signals

---

## Task 2: Add 4 Midday Levels

**Risk:** Low — purely additive, no existing logic touched.
**ATR impact:** Incremental midday coverage.

**Files:**
- Modify: `KeyLevelBreakout.pine` — 8 sections touched per level, ~50 new lines total

### New Levels

| Level | Variable | Type | Signal | Calculation | Color |
|-------|----------|------|--------|-------------|-------|
| Today's Open | `todayOpenLvl` | Magnet | REV | Already in `todayOpen` from line 105 | Lime |
| PD Close | `pdClose` | Magnet | REV | `yestClose` from line 105 | Lime |
| Week Open | `weekOpenLvl` | Barrier | BRK | `weekOpen` from line 109 | Fuchsia |
| Month Open | `monthOpen` | Barrier | BRK | new `request.security` call | Fuchsia |

**Important:** `todayOpen` and `yestClose` already exist as variables (line 105-106). `weekOpen` also exists (line 109). Only `monthOpen` needs a new `request.security` call.

### Step 1: Add input toggles

After line 13, add:
```pine
i_showTodayOpen = input.bool(true, "Today's Open",       group="Level Toggles")
i_showPDClose   = input.bool(true, "PD Close",           group="Level Toggles")
i_showWeekOpen  = input.bool(true, "Week Open",          group="Level Toggles")
i_showMonthOpen = input.bool(true, "Month Open",         group="Level Toggles")
```

### Step 2: Add monthOpen calculation

After line 110 (the weekOpen request.security), add:
```pine
// Month Open (non-repainting)
monthOpen = request.security(syminfo.tickerid, "M", open, lookahead = barmerge.lookahead_on)
```

Note: `todayOpen`, `yestClose`, and `weekOpen` already exist from lines 105-110.

### Step 3: Add breakout flags for BRK levels (Week Open, Month Open)

After line 188 (`xVWBL`), add:
```pine
var bool xWO  = false   // Week Open
var bool xMO  = false   // Month Open
```

After line 200 (`rVWBL`), add reversal flags for REV levels (Today's Open, PD Close):
```pine
var bool rTodayOpen = false
var bool rPDClose   = false
```

### Step 4: Add session reset

In the `if newRegular` block (around line 319), add before the closing block:
```pine
    xWO := false
    xMO := false
    rTodayOpen := false
    rPDClose   := false
```

### Step 5: Add raw BRK signals for Week Open and Month Open

After line 750 (`rBearOL`), add:
```pine
rBullWO = i_showWeekOpen  and bullBreak(weekOpen)
rBearWO = i_showWeekOpen  and bearBreak(weekOpen)
rBullMO = i_showMonthOpen and bullBreak(monthOpen)
rBearMO = i_showMonthOpen and bearBreak(monthOpen)
```

### Step 6: Add filtered BRK signals for Week Open and Month Open

After line 773 (`sigBearVWBL`), add:
```pine
sigBullWO = rBullWO and (not i_firstOnly or not xWO) and fGateBull and (emaGateBull or isPre950)
sigBearWO = rBearWO and (not i_firstOnly or not xWO) and fGateBear and (emaGateBear or isPre950)
sigBullMO = rBullMO and (not i_firstOnly or not xMO) and fGateBull and (emaGateBull or isPre950)
sigBearMO = rBearMO and (not i_firstOnly or not xMO) and fGateBear and (emaGateBear or isPre950)
```

### Step 7: Add flag updates for Week Open and Month Open

After line 797 (`xVWBL := true`), add:
```pine
if rBullWO or rBearWO
    xWO := true
if rBullMO or rBearMO
    xMO := true
```

### Step 8: Add raw REV signals for Today's Open and PD Close

After line 759 (rRevBearPDMid section, around where PD Mid REV signals are), add:
```pine
// Today's Open REV: inline touch-and-turn (magnet level, no VWAP filter)
rRevBullTodayOpen = i_showTodayOpen and not na(todayOpen) and isRegular and newSigBar
     and (not i_limitRevWin or isSetupWindow)
     and sigC > sigO and sigL <= todayOpen and sigC > todayOpen
rRevBearTodayOpen = i_showTodayOpen and not na(todayOpen) and isRegular and newSigBar
     and (not i_limitRevWin or isSetupWindow)
     and sigC < sigO and sigH >= todayOpen and sigC < todayOpen

// PD Close REV: inline touch-and-turn (magnet level, no VWAP filter)
rRevBullPDClose = i_showPDClose and not na(yestClose) and isRegular and newSigBar
     and (not i_limitRevWin or isSetupWindow)
     and sigC > sigO and sigL <= yestClose and sigC > yestClose
rRevBearPDClose = i_showPDClose and not na(yestClose) and isRegular and newSigBar
     and (not i_limitRevWin or isSetupWindow)
     and sigC < sigO and sigH >= yestClose and sigC < yestClose
```

### Step 9: Add filtered REV signals for Today's Open and PD Close

After line 850 (`sigRevBearPDMid`), add:
```pine
// Today's Open + PD Close REV: no EMA gate — magnet levels (same pattern as PD Mid)
sigRevBullTodayOpen = rRevBullTodayOpen and (not i_firstOnly or not rTodayOpen) and fGateBull_rev
sigRevBearTodayOpen = rRevBearTodayOpen and (not i_firstOnly or not rTodayOpen) and fGateBear_rev
sigRevBullPDClose   = rRevBullPDClose   and (not i_firstOnly or not rPDClose)   and fGateBull_rev
sigRevBearPDClose   = rRevBearPDClose   and (not i_firstOnly or not rPDClose)   and fGateBear_rev
```

### Step 10: Add REV flag updates

After the REV flag update block (around line 870), add:
```pine
if rRevBullTodayOpen or rRevBearTodayOpen
    rTodayOpen := true
if rRevBullPDClose or rRevBearPDClose
    rPDClose := true
```

### Step 11: Update signal count aggregates

At line 892, update `anyBull` to include Week Open and Month Open:
```pine
anyBull = sigBullPMH or sigBullYH or sigBullWH or sigBullOH or sigBullWO or sigBullMO
```

At line 893, update `anyBear`:
```pine
anyBear = sigBearPML or sigBearYL or sigBearWL or sigBearOL or sigBearPDLH or sigBearVWBL or sigBearWO or sigBearMO
```

At line 896, update `anyRevBull`:
```pine
anyRevBull = sigRevBullPML or sigRevBullYL or sigRevBullWL or sigRevBullOL or sigRevBullVWAP or sigRevBullPDLH or sigRevBullVWBL or sigRevBullPDMid or sigRevBullTodayOpen or sigRevBullPDClose
```

At line 897, update `anyRevBear`:
```pine
anyRevBear = sigRevBearPMH or sigRevBearYH or sigRevBearWH or sigRevBearOH or sigRevBearVWAP or sigRevBearPDMid or sigRevBearTodayOpen or sigRevBearPDClose
```

### Step 12: Add BRK label text for Week Open and Month Open

After line 962 (end of `bearText` assembly), add:
```pine
if sigBullWO
    bullText := bullText + (bullText != "" ? " + " : "") + "Week O"
if sigBullMO
    bullText := bullText + (bullText != "" ? " + " : "") + "Month O"
if sigBearWO
    bearText := bearText + (bearText != "" ? " + " : "") + "Week O"
if sigBearMO
    bearText := bearText + (bearText != "" ? " + " : "") + "Month O"
```

### Step 13: Add REV label text for Today's Open and PD Close

After line 1023 (`sigRevBullPDMid` text), add:
```pine
if sigRevBullTodayOpen
    revBullText := revBullText + (revBullText != "" ? " + " : "") + "~ Today O"
if sigRevBullPDClose
    revBullText := revBullText + (revBullText != "" ? " + " : "") + "~ PD Cls"
```

After line 1050 (`sigRevBearPDMid` text), add:
```pine
if sigRevBearTodayOpen
    revBearText := revBearText + (revBearText != "" ? " + " : "") + "~ Today O"
if sigRevBearPDClose
    revBearText := revBearText + (revBearText != "" ? " + " : "") + "~ PD Cls"
```

### Step 14: Update count expressions

At line 973, update `bullCount`:
```pine
bullCount = (sigBullPMH ? 1 : 0) + (sigBullYH ? 1 : 0) + (sigBullWH ? 1 : 0) + (sigBullOH ? 1 : 0) + (sigBullWO ? 1 : 0) + (sigBullMO ? 1 : 0)
```

At line 974, update `bearCount`:
```pine
bearCount = (sigBearPML ? 1 : 0) + (sigBearYL ? 1 : 0) + (sigBearWL ? 1 : 0) + (sigBearOL ? 1 : 0) + (sigBearPDLH ? 1 : 0) + (sigBearVWBL ? 1 : 0) + (sigBearWO ? 1 : 0) + (sigBearMO ? 1 : 0)
```

At line 1052, update `revBullCount`:
```pine
revBullCount = (sigRevBullPML ? 1 : 0) + (sigRevBullYL ? 1 : 0) + (sigRevBullWL ? 1 : 0) + (sigRevBullOL ? 1 : 0) + (sigRevBullVWAP ? 1 : 0) + (sigRevBullPDLH ? 1 : 0) + (sigRevBullVWBL ? 1 : 0) + (sigRevBullPDMid ? 1 : 0) + (sigRevBullTodayOpen ? 1 : 0) + (sigRevBullPDClose ? 1 : 0)
```

At line 1053, update `revBearCount`:
```pine
revBearCount = (sigRevBearPMH ? 1 : 0) + (sigRevBearYH ? 1 : 0) + (sigRevBearWH ? 1 : 0) + (sigRevBearOH ? 1 : 0) + (sigRevBearVWAP ? 1 : 0) + (sigRevBearPDMid ? 1 : 0) + (sigRevBearTodayOpen ? 1 : 0) + (sigRevBearPDClose ? 1 : 0)
```

### Step 15: Add plot lines

After line 1820 (`VWAP Lower` plot), add:
```pine
plot(i_showLines and i_showTodayOpen and isRegular ? todayOpen : na, "Today Open", color.new(color.lime, 40), 1, plot.style_linebr)
plot(i_showLines and i_showPDClose   and isRegular ? yestClose : na, "PD Close",   color.new(color.lime, 40), 1, plot.style_linebr)
plot(i_showLines and i_showWeekOpen  and isRegular ? weekOpen  : na, "Week Open",  color.new(color.fuchsia, 40), 1, plot.style_linebr)
plot(i_showLines and i_showMonthOpen and isRegular ? monthOpen : na, "Month Open", color.new(color.fuchsia, 40), 1, plot.style_linebr)
```

### Step 16: Commit

```bash
git add KeyLevelBreakout.pine
git commit -m "v3.2: add 4 midday levels (Today Open, PD Close, Week Open, Month Open)"
```

### Regression check
- All existing signals should fire identically (additive only)
- New levels should show on chart with correct colors
- REV signals at Today Open/PD Close should fire without EMA gate
- BRK signals at Week Open/Month Open should fire with full evidence stack + EMA gate

---

## Task 3: EXREV Bypass (Bear Only)

**Risk:** Low-Medium — surgical addition to existing filter chain.
**ATR impact:** +4.3 (N=31, 45.2% win)
**What:** When a bear candle has body < 30% (strong rejection wick), bypass BOTH the candle quality filter AND the EMA gate. This catches extended reversals where the wick tells the story, not the body.

**Files:**
- Modify: `KeyLevelBreakout.pine` — 5 sections (~16 lines)

### Step 1: Add EXREV input toggle

After the filter inputs (find the Filters group section), add:
```pine
i_exrevGate = input.bool(true, "EXREV Bypass (Bear)",    group="Filters")
```

### Step 2: Add EXREV bypass variable

After line 503 (`emaGateBear_dim`), add:
```pine
// EXREV bypass: bear REV with tiny body (< 30%) = strong rejection wick
// Bypasses BOTH candle quality filter AND EMA gate (v3.2)
bool exrevBypass = i_exrevGate and bodyRatio < 0.30 and candleRange > 0
```

### Step 3: Modify 4 bear REV filtered signals to include EXREV bypass

At lines 837-840, change:
```pine
sigRevBearPMH = rRevBearPMH and (not i_firstOnly or not rPMH) and fGateBear_rev and (emaGateBear or isPre950)
sigRevBearYH  = rRevBearYH  and (not i_firstOnly or not rYH)  and fGateBear_rev and (emaGateBear or isPre950)
sigRevBearWH  = rRevBearWH  and (not i_firstOnly or not rWH)  and fGateBear_rev and (emaGateBear or isPre950)
sigRevBearOH  = rRevBearOH  and (not i_firstOnly or not rOH)  and fGateBear_rev and (emaGateBear or isPre950)
```

To:
```pine
sigRevBearPMH = rRevBearPMH and (not i_firstOnly or not rPMH) and (fGateBear_rev or exrevBypass) and (emaGateBear or isPre950 or exrevBypass)
sigRevBearYH  = rRevBearYH  and (not i_firstOnly or not rYH)  and (fGateBear_rev or exrevBypass) and (emaGateBear or isPre950 or exrevBypass)
sigRevBearWH  = rRevBearWH  and (not i_firstOnly or not rWH)  and (fGateBear_rev or exrevBypass) and (emaGateBear or isPre950 or exrevBypass)
sigRevBearOH  = rRevBearOH  and (not i_firstOnly or not rOH)  and (fGateBear_rev or exrevBypass) and (emaGateBear or isPre950 or exrevBypass)
```

### Step 4: Add EXREV prefix to label text

In the bear REV label text section (lines 1027-1046), modify each `pfx` assignment to detect EXREV. For each of the 4 bear REV levels (PMH, YH, WH, OH), change:
```pine
    string pfx = i_showReclaim and hadBrkPMH and rclBearOK ? "~~ " : "~ "
```
To:
```pine
    string pfx = exrevBypass ? "x~ " : (i_showReclaim and hadBrkPMH and rclBearOK ? "~~ " : "~ ")
```

Do this for all 4: `sigRevBearPMH` (line 1027), `sigRevBearYH` (line 1032), `sigRevBearWH` (line 1037), `sigRevBearOH` (line 1042).

### Step 5: Add EXREV label color

In the bear REV label creation section (find where bear reversal labels are created), when `exrevBypass` is true, use `#FF6600` (darker orange) instead of default REV color. Look for the bear label color and add:
```pine
// Use darker orange for EXREV signals
color revBearColor = exrevBypass ? color.new(#FF6600, dimAlpha) : color.new(bearLblColor, dimAlpha)
```

(The exact integration depends on how `bearLblColor` is used — adapt to match existing pattern.)

### Step 6: Commit

```bash
git add KeyLevelBreakout.pine
git commit -m "v3.2: EXREV bypass — bear REV body<30% skips candle+EMA gates (+4.3 ATR)"
```

### Regression check
- Bull REV signals should be completely unchanged
- Bear REV count should increase slightly (EXREV signals that were previously suppressed)
- Normal bear REVs (body > 30%) should be identical
- EXREV signals should show `x~ ` prefix in labels

---

## Task 4: FADE Resurrection

**Risk:** Medium — replaces existing FADE trigger with new definition, adds state tracking.
**ATR impact:** +7.8 (N=327, 52.9% win for EMA-aligned FADEs)

**Current FADE (broken):** Triggers on CONF failure only. Since CONF pass rate is now 99.7%, FADE never fires.

**New FADE:** Fires when a counter-EMA signal's level gets crossed back within 6 bars (30 min on 5m). Direction is WITH EMA trend. Decoupled from CONF.

**Files:**
- Modify: `KeyLevelBreakout.pine` — replace FADE state + detection (~60 lines)

### Step 1: Replace FADE state variables

At lines 285-291, replace the existing FADE state:
```pine
// Failed Breakout Fade state (v3.0)
var float fadeBullLevel = na    // level from failed bear BRK → bull fade
var float fadeBearLevel = na    // level from failed bull BRK → bear fade
var int   fadeBullBar   = 0     // bar_index when CONF failed
var int   fadeBearBar   = 0
var bool  fadeBullFired = false
var bool  fadeBearFired = false
```

With new state:
```pine
// FADE state (v3.2): counter-EMA signal crossback
// Watches for ANY signal that fired counter-EMA, then price crosses back through level
var float fadeWatchLevel  = na     // the level to watch for crossback
var int   fadeWatchDir    = 0      // original signal direction: +1=bull, -1=bear
var int   fadeWatchExpiry = 0      // bar_index when 6-bar window expires
var bool  fadeWatchActive = false  // is a watch currently active?
var bool  fadeFired       = false  // did FADE already fire this watch?
```

### Step 2: Update session reset

In the `if newRegular` block (lines 312-317), replace:
```pine
    fadeBullLevel := na
    fadeBearLevel := na
    fadeBullBar   := 0
    fadeBearBar   := 0
    fadeBullFired := false
    fadeBearFired := false
```

With:
```pine
    fadeWatchLevel  := na
    fadeWatchDir    := 0
    fadeWatchExpiry := 0
    fadeWatchActive := false
    fadeFired       := false
```

### Step 3: Add FADE watch setup (after signal detection)

After the combined signals section (after line 898), add the FADE watch setup logic. This fires whenever any BRK or REV signal fires counter-EMA:

```pine
// FADE watch setup (v3.2): any signal that fires counter-EMA starts a watch
// Counter-EMA = bull signal when EMA=bear, or bear signal when EMA=bull
// Only dim signals (pre-9:50 counter-EMA) can trigger FADE watches
bool newBullSignal = anyBull or anyRevBull
bool newBearSignal = anyBear or anyRevBear

// Determine the primary level for the watch (use first matching level price)
float bullSigLevel = sigBullPMH ? pmHigh : sigBullYH ? yestHigh : sigBullWH ? weekHigh : sigBullOH ? orbHigh : sigRevBullPML ? pmLow : sigRevBullYL ? yestLow : sigRevBullWL ? weekLow : sigRevBullOL ? orbLow : na
float bearSigLevel = sigBearPML ? pmLow : sigBearYL ? yestLow : sigBearWL ? weekLow : sigBearOL ? orbLow : sigRevBearPMH ? pmHigh : sigRevBearYH ? yestHigh : sigRevBearWH ? weekHigh : sigRevBearOH ? orbHigh : na

// Set up watch when counter-EMA signal fires
if newBullSignal and not fEMA_bull and not na(bullSigLevel)
    fadeWatchLevel  := bullSigLevel
    fadeWatchDir    := 1   // original was bull
    fadeWatchExpiry := bar_index + 6
    fadeWatchActive := true
    fadeFired       := false
if newBearSignal and not fEMA_bear and not na(bearSigLevel)
    fadeWatchLevel  := bearSigLevel
    fadeWatchDir    := -1  // original was bear
    fadeWatchExpiry := bar_index + 6
    fadeWatchActive := true
    fadeFired       := false
```

### Step 4: Replace FADE signal detection

At lines 899-915, replace the entire existing FADE detection:
```pine
// Failed Breakout Fade signals (v3.0b)
// NO EMA gate — FADE is contrarian...
int fadeWindow = slBars * 2
bool sigFadeBull = not na(fadeBullLevel) and not fadeBullFired
     and newSigBar and isRegular
     and sigC > fadeBullLevel
     and (bar_index - fadeBullBar) <= fadeWindow
bool sigFadeBear = not na(fadeBearLevel) and not fadeBearFired
     and newSigBar and isRegular
     and sigC < fadeBearLevel
     and (bar_index - fadeBearBar) <= fadeWindow
if sigFadeBull
    fadeBullFired := true
if sigFadeBear
    fadeBearFired := true
bool anyFade = sigFadeBull or sigFadeBear
```

With:
```pine
// FADE signal detection (v3.2): counter-EMA crossback
// Original was bull (counter-EMA) → price falls back through level → FADE fires BEAR (with EMA)
// Original was bear (counter-EMA) → price rises back through level → FADE fires BULL (with EMA)
bool sigFadeBull = false
bool sigFadeBear = false
if fadeWatchActive and not fadeFired and newSigBar and isRegular
    if bar_index > fadeWatchExpiry
        fadeWatchActive := false  // window expired
    else if fadeWatchDir == -1 and sigC > fadeWatchLevel  // was bear, now crossing back up = BULL FADE
        sigFadeBull := true
        fadeFired   := true
    else if fadeWatchDir == 1 and sigC < fadeWatchLevel   // was bull, now crossing back down = BEAR FADE
        sigFadeBear := true
        fadeFired   := true
bool anyFade = sigFadeBull or sigFadeBear
```

### Step 5: Remove old FADE triggers from CONF failure

At line 1644-1647 (bull BRK CONF failure → bear fade setup):
```pine
        // Set up FADE: failed bull BRK → potential bear fade
        fadeBearLevel := bRTConsLvl
        fadeBearBar   := bar_index
        fadeBearFired := false
```

Remove these 4 lines entirely (or comment out). The old variables no longer exist.

At line 1694-1697 (bear BRK CONF failure → bull fade setup):
```pine
        // Set up FADE: failed bear BRK → potential bull fade
        fadeBullLevel := sRTConsLvl
        fadeBullBar   := bar_index
        fadeBullFired := false
```

Remove these 4 lines entirely.

### Step 6: FADE labels stay the same

The FADE label code at lines 1142-1161 uses `sigFadeBull`/`sigFadeBear` which we've redefined. The labels, logs, and alerts will work without changes.

### Step 7: Commit

```bash
git add KeyLevelBreakout.pine
git commit -m "v3.2: resurrect FADE — counter-EMA crossback within 6 bars (+7.8 ATR)"
```

### Regression check
- FADE signals should now appear (previously 0)
- FADE fires in WITH-EMA direction (opposite of original counter-EMA signal)
- BRK and REV signals completely unchanged
- CONF logic works without FADE setup lines (CONF ✓/✗ still displays correctly)
- RNG, QBS unchanged

---

## Task 5: HIGH→REV Reassignment

**Risk:** High — structural change affecting 4 levels.
**ATR impact:** Large (HIGH levels underperform as BRK vs REV)

**What:** PM H, Yest H, ORB H, Week H move from BRK detection to REV detection. These levels behave as magnets (price bounces back), not barriers (price breaks through). LOW levels stay as BRK — they are true barriers.

**Files:**
- Modify: `KeyLevelBreakout.pine` — ~40 lines across multiple sections

### Step 1: Remove HIGH levels from raw BRK signals

At lines 743, 745, 747, 749, change:
```pine
rBullPMH = i_showPM   and bullBreak(pmHigh)
```
```pine
rBullYH  = i_showYest  and bullBreak(yestHigh)
```
```pine
rBullWH  = i_showWeek  and bullBreak(weekHigh)
```
```pine
rBullOH  = i_showORB   and not isORBwin and orbFirstDone and bullBreak(orbHigh)
```

To:
```pine
rBullPMH = false  // v3.2: PM H moved to REV (magnet, not barrier)
```
```pine
rBullYH  = false  // v3.2: Yest H moved to REV
```
```pine
rBullWH  = false  // v3.2: Week H moved to REV
```
```pine
rBullOH  = false  // v3.2: ORB H moved to REV
```

### Step 2: Add HIGH levels to raw REV signals

After line 809 (`rRevBearOH`), add bull REV signals at HIGH levels:
```pine
// Bull REV at HIGH levels (v3.2: HIGH = magnet, price bounces up from above)
rRevBullPMH = i_showReversal and i_showPM   and i_revPM   and bullRev(pmHigh,  pmHBody)
rRevBullYH  = i_showReversal and i_showYest  and i_revYest and bullRev(yestHigh, yestHBody)
rRevBullWH  = i_showReversal and i_showWeek  and i_revWeek and bullRev(weekHigh, weekHBody)
rRevBullOH  = i_showReversal and i_showORB   and i_revORB  and not isORBwin and orbFirstDone and bullRev(orbHigh, orbHBody)
```

Note: `rRevBearPMH`, `rRevBearYH`, `rRevBearWH`, `rRevBearOH` already exist (lines 806-809).

### Step 3: Add filtered REV signals for bull HIGH levels

After line 840 (`sigRevBearOH`), add:
```pine
// Bull REV at HIGH levels (v3.2)
sigRevBullPMH = rRevBullPMH and (not i_firstOnly or not rPMH) and fGateBull_rev and (emaGateBull or isPre950)
sigRevBullYH  = rRevBullYH  and (not i_firstOnly or not rYH)  and fGateBull_rev and (emaGateBull or isPre950)
sigRevBullWH  = rRevBullWH  and (not i_firstOnly or not rWH)  and fGateBull_rev and (emaGateBull or isPre950)
sigRevBullOH  = rRevBullOH  and (not i_firstOnly or not rOH)  and fGateBull_rev and (emaGateBull or isPre950)
```

### Step 4: Update signal aggregates

Remove HIGH bull levels from `anyBull` (line 892). Change:
```pine
anyBull = sigBullPMH or sigBullYH or sigBullWH or sigBullOH or sigBullWO or sigBullMO
```
To:
```pine
anyBull = sigBullWO or sigBullMO
```
(Only Week Open and Month Open remain as bull BRK levels after HIGH→REV.)

Add bull HIGH REV to `anyRevBull` (line 896):
```pine
anyRevBull = sigRevBullPML or sigRevBullYL or sigRevBullWL or sigRevBullOL or sigRevBullVWAP or sigRevBullPDLH or sigRevBullVWBL or sigRevBullPDMid or sigRevBullTodayOpen or sigRevBullPDClose or sigRevBullPMH or sigRevBullYH or sigRevBullWH or sigRevBullOH
```

### Step 5: Move label text from BRK to REV

In `bullText` assembly (lines 941-948), the `sigBullPMH`, `sigBullYH`, `sigBullWH`, `sigBullOH` blocks will never execute (all set to `false`). Leave them — they're harmless dead code.

In `revBullText` assembly (after line 1023), add HIGH level text blocks:
```pine
if sigRevBullPMH
    revBullText := revBullText + (revBullText != "" ? " + " : "") + "~ PM H"
if sigRevBullYH
    revBullText := revBullText + (revBullText != "" ? " + " : "") + "~ Yest H"
if sigRevBullWH
    revBullText := revBullText + (revBullText != "" ? " + " : "") + "~ Week H"
if sigRevBullOH
    revBullText := revBullText + (revBullText != "" ? " + " : "") + "~ ORB H"
```

### Step 6: Update count expressions

Remove HIGH from `bullCount` (line 973):
```pine
bullCount = (sigBullWO ? 1 : 0) + (sigBullMO ? 1 : 0)
```

Add HIGH to `revBullCount` (line 1052):
```pine
revBullCount = (sigRevBullPML ? 1 : 0) + (sigRevBullYL ? 1 : 0) + (sigRevBullWL ? 1 : 0) + (sigRevBullOL ? 1 : 0) + (sigRevBullVWAP ? 1 : 0) + (sigRevBullPDLH ? 1 : 0) + (sigRevBullVWBL ? 1 : 0) + (sigRevBullPDMid ? 1 : 0) + (sigRevBullTodayOpen ? 1 : 0) + (sigRevBullPDClose ? 1 : 0) + (sigRevBullPMH ? 1 : 0) + (sigRevBullYH ? 1 : 0) + (sigRevBullWH ? 1 : 0) + (sigRevBullOH ? 1 : 0)
```

### Step 7: Commit

```bash
git add KeyLevelBreakout.pine
git commit -m "v3.2: HIGH levels (PM/Yest/ORB/Week H) → REV signals (magnets not barriers)"
```

### Regression check
- Bear signals at HIGH levels should still work (already REV)
- Bull signals at HIGH levels should now appear as REV with `~ ` prefix
- LOW levels should be completely unchanged (still BRK)
- CONF monitoring may need attention — currently only tracks BRK signals. If HIGH levels no longer fire BRK, they won't get CONF tracking. This is correct behavior (REV signals don't need CONF).

---

## Task 6: Version Bump + Final Cleanup

**Files:**
- Modify: `KeyLevelBreakout.pine:2,5` (version string)

### Step 1: Update version

At line 2:
```pine
// Detects bullish/bearish 5m candle closes through key levels (v3.2)
```

At line 5:
```pine
indicator("Key Level Breakout v3.2", overlay=true, max_labels_count=500, max_lines_count=200)
```

### Step 2: Final commit

```bash
git add KeyLevelBreakout.pine
git commit -m "v3.2: bump version — 5 data-driven upgrades complete"
```

### Step 3: Push

```bash
git push origin main
```

---

## Task 7: Update Documentation

**Files:**
- Modify: `KLB_DESIGN-JOURNAL.md` — add v3.2 section
- Modify: `KLB_Reference.md` — new levels, EXREV, FADE, HIGH→REV
- Modify: `KLB_PLAYBOOK.md` — updated signal catalog
- Modify: `MEMORY.md` — v3.2 features

### Step 1: Add v3.2 section to design journal

Summarize all 5 changes with ATR impact and line counts.

### Step 2: Update reference doc

- Add Today's Open, PD Close, Week Open, Month Open to level table
- Add EXREV bypass description
- Update FADE definition
- Note HIGH→REV reassignment

### Step 3: Update playbook

- New level entries in signal catalog
- Updated level rankings (HIGH = magnet, LOW = barrier)

### Step 4: Update MEMORY.md

- v3.2 feature list
- Updated version history reference

### Step 5: Commit

```bash
git add KLB_DESIGN-JOURNAL.md KLB_Reference.md KLB_PLAYBOOK.md
git commit -m "docs: update all docs for v3.2 (new levels, EXREV, FADE, HIGH→REV)"
```

---

## Important Notes for Implementer

1. **Line numbers will shift** after each task. Task 1 is exact. For Tasks 2-6, use the section headers and variable names to locate insertion points, not hardcoded line numbers.

2. **Pine Script v6 quirks:**
   - No `let` or `const` — just use bare variable names
   - `var` means "persist across bars" (like `static` in C)
   - `bool` declarations inside `if` blocks need explicit `bool` type
   - Ternary: `condition ? a : b` (standard)
   - String concatenation: `+` operator

3. **Testing in TradingView:**
   - Paste full script into Pine Editor
   - Apply to any US stock chart (SPY recommended)
   - Switch to 1-minute timeframe with 5-minute signal TF
   - Check Pine Logs (if `i_debugLog` is on) for signal output
   - Verify labels appear at correct locations

4. **The FADE change (Task 4) has a dependency:** It removes code from the CONF monitoring section (lines 1644-1647 and 1694-1697). If Task 4 is done before examining those lines, read them first to verify the exact code to remove.

5. **EXREV bypass (Task 3) interacts with Task 5 (HIGH→REV):** When HIGH levels become REV signals, the EXREV bypass (bear REV body<30%) will also apply to bear REV at HIGH levels. This is the intended behavior — the EXREV bypass catches counter-EMA rejections at resistance levels.
