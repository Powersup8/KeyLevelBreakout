# Reversal + Reclaim + Zones Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Reversal and Reclaim signal types to KeyLevelBreakout.pine with wick-to-body zone detection, making it a complete PDH/PDL strategy tool.

**Architecture:** Integrated pipeline — new helpers and signal paths alongside existing breakout logic, sharing volume/ATR/confirmation filters. All new features behind toggles; when disabled, behavior is identical to v1.6. Reclaim piggybacks on existing invalidation tracking (breakout flag re-arm sets hadBreak context for subsequent reversals).

**Tech Stack:** Pine Script v6, TradingView indicator overlay. No automated tests — verify visually on TradingView after each task.

---

## Reference

- **Design doc:** `docs/plans/2026-02-24-reversal-reclaim-design.md`
- **Current file:** `KeyLevelBreakout.pine` (391 lines, v1.6)
- **Companion docs:** `KeyLevelBreakout.md`, `KeyLevelBreakout_Improvements.md`

---

### Task 1: Add New Inputs

**Files:**
- Modify: `KeyLevelBreakout.pine:30` (insert after line 30)

**Step 1: Add setup, zone, and per-level reversal inputs**

Insert after line 30 (after `i_confirmBars`):

```pine

// ─── Setup Inputs ──────────────────────────────────────
i_showReversal = input.bool(true,   "Show Reversal Setups",            group="Setups")
i_showReclaim  = input.bool(true,   "Show Reclaim Setups",             group="Setups")
i_setupWindow  = input.string("0930-1130", "Setup Active Window (ET)", group="Setups")

i_useZones     = input.bool(true,   "Use Level Zones (wick-to-body)",  group="Zones")
i_zoneATRPct   = input.float(3.0,   "Zone Width for PM/ORB (% of ATR)", minval=0, step=0.5, group="Zones")

i_revPM   = input.bool(true, "PM H/L Reversal/Reclaim",   group="Reversal/Reclaim Toggles")
i_revYest = input.bool(true, "Yest H/L Reversal/Reclaim", group="Reversal/Reclaim Toggles")
i_revWeek = input.bool(true, "Week H/L Reversal/Reclaim", group="Reversal/Reclaim Toggles")
i_revORB  = input.bool(true, "ORB H/L Reversal/Reclaim",  group="Reversal/Reclaim Toggles")
```

**Step 2: Verify**

Add to TradingView chart. Confirm 11 new inputs appear in Settings under groups "Setups", "Zones", and "Reversal/Reclaim Toggles". Existing inputs unchanged. No compile errors.

**Step 3: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(KLB): add v1.7 inputs for reversal, reclaim, zones"
```

---

### Task 2: Expand request.security for Zone Data + Compute Zone Bounds

**Files:**
- Modify: `KeyLevelBreakout.pine:53-58` (replace 4 lines with 4), insert ~12 lines after ORB block

**Step 1: Replace separate D/W request.security calls with tuples**

Replace lines 53-54:
```pine
yestHigh = request.security(syminfo.tickerid, "D", high[1], lookahead = barmerge.lookahead_on)
yestLow  = request.security(syminfo.tickerid, "D", low[1],  lookahead = barmerge.lookahead_on)
```
With:
```pine
[yestHigh, yestLow, yestOpen, yestClose] = request.security(syminfo.tickerid, "D",
     [high[1], low[1], open[1], close[1]], lookahead = barmerge.lookahead_on)
```

Replace lines 57-58:
```pine
weekHigh = request.security(syminfo.tickerid, "W", high[1], lookahead = barmerge.lookahead_on)
weekLow  = request.security(syminfo.tickerid, "W", low[1],  lookahead = barmerge.lookahead_on)
```
With:
```pine
[weekHigh, weekLow, weekOpen, weekClose] = request.security(syminfo.tickerid, "W",
     [high[1], low[1], open[1], close[1]], lookahead = barmerge.lookahead_on)
```

**Step 2: Add zone bound computations**

Insert after the ORB block (after line 73 in original, which ends `orbLow := math.min(orbLow, low)`):

```pine

// ─── Zone Bounds ───────────────────────────────────────
// D/W levels: body edge from candle OHLC. PM/ORB: ATR-derived width.
// When zones OFF: body = wick (zone collapses to single line).
zoneWidth = i_useZones and not na(dailyATR) ? dailyATR * i_zoneATRPct / 100.0 : 0.0
pmHBody   = i_useZones ? pmHigh - zoneWidth : pmHigh
pmLBody   = i_useZones ? pmLow  + zoneWidth : pmLow
yestHBody = i_useZones and not na(yestOpen) ? math.max(yestOpen, yestClose) : yestHigh
yestLBody = i_useZones and not na(yestOpen) ? math.min(yestOpen, yestClose) : yestLow
weekHBody = i_useZones and not na(weekOpen) ? math.max(weekOpen, weekClose) : weekHigh
weekLBody = i_useZones and not na(weekOpen) ? math.min(weekOpen, weekClose) : weekLow
orbHBody  = i_useZones ? orbHigh - zoneWidth : orbHigh
orbLBody  = i_useZones ? orbLow  + zoneWidth : orbLow
```

**Step 3: Verify regression**

Add to chart. With `i_useZones = true` and `i_useZones = false`, existing breakout labels must be identical (zone data is computed but not yet used by breakout helpers). Compare label positions and text against v1.6.

**Step 4: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(KLB): expand request.security tuples, add zone bounds"
```

---

### Task 3: Time Window + Reversal/Reclaim State Variables + Session Resets

**Files:**
- Modify: `KeyLevelBreakout.pine` — insert in session detection section, state section, and reset block

**Step 1: Add time window detection**

Insert after `newRegular` (after line 38 in original):

```pine
isSetupWindow = not na(time(timeframe.period, i_setupWindow + ":23456", TZ))
```

**Step 2: Add reversal flags and hadBreak state**

Insert after breakout flags block (after line 83 in original, which ends `var bool xOL  = false`):

```pine

// ─── Reversal Flags (reset each regular session) ──────
var bool rPMH = false
var bool rPML = false
var bool rYH  = false
var bool rYL  = false
var bool rWH  = false
var bool rWL  = false
var bool rOH  = false
var bool rOL  = false

// ─── Reclaim Context (was this level broken + invalidated?) ──
var bool hadBrkPMH = false
var bool hadBrkPML = false
var bool hadBrkYH  = false
var bool hadBrkYL  = false
var bool hadBrkWH  = false
var bool hadBrkWL  = false
var bool hadBrkOH  = false
var bool hadBrkOL  = false
```

**Step 3: Add session resets for new state**

In the `if newRegular` block (after line 108 `xOL := false`), append:

```pine
    // Reset reversal flags
    rPMH := false
    rPML := false
    rYH  := false
    rYL  := false
    rWH  := false
    rWL  := false
    rOH  := false
    rOL  := false
    // Reset reclaim context
    hadBrkPMH := false
    hadBrkPML := false
    hadBrkYH  := false
    hadBrkYL  := false
    hadBrkWH  := false
    hadBrkWL  := false
    hadBrkOH  := false
    hadBrkOL  := false
```

**Step 4: Verify**

Compile in Pine Editor — no errors. Existing signals unchanged.

**Step 5: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(KLB): add reversal flags, hadBreak state, session resets"
```

---

### Task 4: Reversal Helper Functions

**Files:**
- Modify: `KeyLevelBreakout.pine` — insert after `bearBreak` helper (after line 193 in original)

**Step 1: Add reversal helper functions**

Insert after `bearBreak` function (after line 193):

```pine

// ─── Reversal Helpers ───────────────────────────────────
// Bull reversal at LOW level: wick dips into zone, close rejects above body edge.
// Bear reversal at HIGH level: wick pushes into zone, close rejects below body edge.
bullRev(float wick, float body) =>
    not na(wick) and not na(body) and isRegular and newSigBar and isSetupWindow
     and sigC > sigO and sigL <= body and sigC > body and volPassBull

bearRev(float wick, float body) =>
    not na(wick) and not na(body) and isRegular and newSigBar and isSetupWindow
     and sigC < sigO and sigH >= body and sigC < body and volPassBear
```

Note: `wick` param is the level's wick edge, `body` is the body edge. For bull reversal at LOW: `wick = yestLow, body = yestLBody`. For bear reversal at HIGH: `wick = yestHigh, body = yestHBody`. The `wick` param is included for `not na()` check but the zone check uses `body`.

**Step 2: Verify**

Compile — no errors. Functions defined but not yet called, so no visual change.

**Step 3: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(KLB): add bullRev/bearRev helper functions"
```

---

### Task 5: Reversal Signal Evaluation + Flag Management

**Files:**
- Modify: `KeyLevelBreakout.pine` — insert after breakout flag updates (after line 231 in original)

**Step 1: Add raw + filtered reversal signals**

Insert after the breakout flag update block (after line 231, which ends `xOL := true`):

```pine

// ─── Raw Reversal Signals ──────────────────────────────
// Bull reversal fires at LOW levels (rejection = buy). Bear at HIGH (rejection = sell).
rRevBullPML = i_showReversal and i_showPM   and i_revPM   and bullRev(pmLow,  pmLBody)
rRevBullYL  = i_showReversal and i_showYest  and i_revYest and bullRev(yestLow, yestLBody)
rRevBullWL  = i_showReversal and i_showWeek  and i_revWeek and bullRev(weekLow, weekLBody)
rRevBullOL  = i_showReversal and i_showORB   and i_revORB  and not isORBwin and bullRev(orbLow, orbLBody)

rRevBearPMH = i_showReversal and i_showPM   and i_revPM   and bearRev(pmHigh,  pmHBody)
rRevBearYH  = i_showReversal and i_showYest  and i_revYest and bearRev(yestHigh, yestHBody)
rRevBearWH  = i_showReversal and i_showWeek  and i_revWeek and bearRev(weekHigh, weekHBody)
rRevBearOH  = i_showReversal and i_showORB   and i_revORB  and not isORBwin and bearRev(orbHigh, orbHBody)

// ─── Filtered Reversal Signals ────────────────────────
sigRevBullPML = rRevBullPML and (not i_firstOnly or not rPML)
sigRevBullYL  = rRevBullYL  and (not i_firstOnly or not rYL)
sigRevBullWL  = rRevBullWL  and (not i_firstOnly or not rWL)
sigRevBullOL  = rRevBullOL  and (not i_firstOnly or not rOL)

sigRevBearPMH = rRevBearPMH and (not i_firstOnly or not rPMH)
sigRevBearYH  = rRevBearYH  and (not i_firstOnly or not rYH)
sigRevBearWH  = rRevBearWH  and (not i_firstOnly or not rWH)
sigRevBearOH  = rRevBearOH  and (not i_firstOnly or not rOH)

// Update reversal flags
if rRevBullPML
    rPML := true
if rRevBullYL
    rYL := true
if rRevBullWL
    rWL := true
if rRevBullOL
    rOL := true
if rRevBearPMH
    rPMH := true
if rRevBearYH
    rYH := true
if rRevBearWH
    rWH := true
if rRevBearOH
    rOH := true
```

**Step 2: Add reversal re-arming to invalidation block**

In the existing invalidation block (the `if i_firstOnly and newSigBar` section), append after the breakout re-arm lines:

```pine
    // Reversal re-arm: price moved decisively away from the rejection zone
    if rPMH and not na(pmHigh) and sigC > (pmHigh + rearmBuf)
        rPMH := false
    if rPML and not na(pmLow) and sigC < (pmLow - rearmBuf)
        rPML := false
    if rYH and not na(yestHigh) and sigC > (yestHigh + rearmBuf)
        rYH := false
    if rYL and not na(yestLow) and sigC < (yestLow - rearmBuf)
        rYL := false
    if rWH and not na(weekHigh) and sigC > (weekHigh + rearmBuf)
        rWH := false
    if rWL and not na(weekLow) and sigC < (weekLow - rearmBuf)
        rWL := false
    if rOH and not na(orbHigh) and sigC > (orbHigh + rearmBuf)
        rOH := false
    if rOL and not na(orbLow) and sigC < (orbLow - rearmBuf)
        rOL := false
```

**Step 3: Verify**

Compile — no errors. Reversal signals now computed but no labels yet. Check Data Window or use `plotchar` temporarily to verify signals fire at expected locations.

**Step 4: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(KLB): add reversal signal evaluation + flag management"
```

---

### Task 6: Reclaim State Tracking

**Files:**
- Modify: `KeyLevelBreakout.pine` — in the existing invalidation block (breakout re-arm section)

**Step 1: Set hadBreak flags when breakout gets invalidated**

In the existing invalidation block, modify each breakout re-arm to also set hadBreak. For each existing re-arm line, add a `hadBrk` assignment. Example — replace:

```pine
    if xPMH and not na(pmHigh) and sigC <= (pmHigh - rearmBuf)
        xPMH := false
```

With:

```pine
    if xPMH and not na(pmHigh) and sigC <= (pmHigh - rearmBuf)
        xPMH := false
        hadBrkPMH := true
```

Apply the same pattern to all 8 breakout re-arm blocks:
- `xPMH → hadBrkPMH`, `xPML → hadBrkPML`
- `xYH → hadBrkYH`, `xYL → hadBrkYL`
- `xWH → hadBrkWH`, `xWL → hadBrkWL`
- `xOH → hadBrkOH`, `xOL → hadBrkOL`

**Step 2: Verify**

Compile — no errors. The hadBreak state is now tracked but not yet used in labels (that comes in Task 7).

**Step 3: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(KLB): set hadBreak flags on breakout invalidation for reclaim"
```

---

### Task 7: Reversal/Reclaim Labels + Colors

**Files:**
- Modify: `KeyLevelBreakout.pine` — insert after existing `bearText`/`bearCount` block, before `isOld`

**Step 1: Add combined reversal signal booleans**

Insert after the existing `anyBreakout` line (which is `anyBreakout = anyBull or anyBear`):

```pine

anyRevBull = sigRevBullPML or sigRevBullYL or sigRevBullWL or sigRevBullOL
anyRevBear = sigRevBearPMH or sigRevBearYH or sigRevBearWH or sigRevBearOH
anyReversal = anyRevBull or anyRevBear
```

**Step 2: Add reversal label text builder**

Insert after the existing `bearCount` line (before `isOld`):

```pine

// ─── Reversal/Reclaim Label Text ──────────────────────
revBullText = ""
revBullHasReclaim = false
if sigRevBullPML
    string pfx = i_showReclaim and hadBrkPML ? "~~ " : "~ "
    revBullText := revBullText + (revBullText != "" ? " + " : "") + pfx + "PM L"
    if i_showReclaim and hadBrkPML
        revBullHasReclaim := true
if sigRevBullYL
    string pfx = i_showReclaim and hadBrkYL ? "~~ " : "~ "
    revBullText := revBullText + (revBullText != "" ? " + " : "") + pfx + "Yest L"
    if i_showReclaim and hadBrkYL
        revBullHasReclaim := true
if sigRevBullWL
    string pfx = i_showReclaim and hadBrkWL ? "~~ " : "~ "
    revBullText := revBullText + (revBullText != "" ? " + " : "") + pfx + "Week L"
    if i_showReclaim and hadBrkWL
        revBullHasReclaim := true
if sigRevBullOL
    string pfx = i_showReclaim and hadBrkOL ? "~~ " : "~ "
    revBullText := revBullText + (revBullText != "" ? " + " : "") + pfx + "ORB L"
    if i_showReclaim and hadBrkOL
        revBullHasReclaim := true

revBearText = ""
revBearHasReclaim = false
if sigRevBearPMH
    string pfx = i_showReclaim and hadBrkPMH ? "~~ " : "~ "
    revBearText := revBearText + (revBearText != "" ? " + " : "") + pfx + "PM H"
    if i_showReclaim and hadBrkPMH
        revBearHasReclaim := true
if sigRevBearYH
    string pfx = i_showReclaim and hadBrkYH ? "~~ " : "~ "
    revBearText := revBearText + (revBearText != "" ? " + " : "") + pfx + "Yest H"
    if i_showReclaim and hadBrkYH
        revBearHasReclaim := true
if sigRevBearWH
    string pfx = i_showReclaim and hadBrkWH ? "~~ " : "~ "
    revBearText := revBearText + (revBearText != "" ? " + " : "") + pfx + "Week H"
    if i_showReclaim and hadBrkWH
        revBearHasReclaim := true
if sigRevBearOH
    string pfx = i_showReclaim and hadBrkOH ? "~~ " : "~ "
    revBearText := revBearText + (revBearText != "" ? " + " : "") + pfx + "ORB H"
    if i_showReclaim and hadBrkOH
        revBearHasReclaim := true

revBullCount = (sigRevBullPML ? 1 : 0) + (sigRevBullYL ? 1 : 0) + (sigRevBullWL ? 1 : 0) + (sigRevBullOL ? 1 : 0)
revBearCount = (sigRevBearPMH ? 1 : 0) + (sigRevBearYH ? 1 : 0) + (sigRevBearWH ? 1 : 0) + (sigRevBearOH ? 1 : 0)
```

**Step 3: Add label creation for reversals**

Insert after the existing `if bearText != ""` label block (after the closing of bearText label creation and confirmation capture), before the post-breakout confirmation monitoring section:

```pine

// ─── Reversal/Reclaim Labels ────────────────────────────
revBullAlpha = revBullHasReclaim ? math.max(0, bullVolAlpha - 10) : bullVolAlpha
revBearAlpha = revBearHasReclaim ? math.max(0, bearVolAlpha - 10) : bearVolAlpha
revBullColor = color.new(color.blue, revBullAlpha)
revBearColor = color.new(color.orange, revBearAlpha)

if revBullText != ""
    string fullRevBullText = revBullText + bullVolStr + bullPosStr
    label.new(bar_index + shapeOff, na, fullRevBullText,
         yloc=yloc.belowbar, style=label.style_label_up,
         color=isOld ? color.new(color.gray, 90) : revBullColor,
         textcolor=isOld ? color.new(color.gray, 70) : color.white,
         size=revBullCount > 1 ? size.normal : size.small)

if revBearText != ""
    string fullRevBearText = revBearText + bearVolStr + bearPosStr
    label.new(bar_index + shapeOff, na, fullRevBearText,
         yloc=yloc.abovebar, style=label.style_label_down,
         color=isOld ? color.new(color.gray, 90) : revBearColor,
         textcolor=isOld ? color.new(color.gray, 70) : color.white,
         size=revBearCount > 1 ? size.normal : size.small)
```

**Step 4: Verify**

Add to chart on a stock with recent PDH/PDL activity. Look for:
- Blue labels (below bar) for bullish reversals at LOW levels
- Orange labels (above bar) for bearish reversals at HIGH levels
- "~" prefix for plain reversals, "~~" for reclaims (if a prior breakout was invalidated at that level)
- Labels only appear within the 9:30-11:30 ET window
- Existing green/red breakout labels unchanged

**Step 5: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(KLB): add reversal/reclaim label creation with colors"
```

---

### Task 8: Reversal/Reclaim Alerts

**Files:**
- Modify: `KeyLevelBreakout.pine` — in the alerts section

**Step 1: Add programmatic alerts for reversals**

Insert after the existing breakout `alert()` calls (after `alert("Bearish breakout: ...")`):

```pine
if revBullText != ""
    alert("Bullish reversal: " + revBullText + bullVolStr + bullPosStr, alert.freq_once_per_bar_close)
if revBearText != ""
    alert("Bearish reversal: " + revBearText + bearVolStr + bearPosStr, alert.freq_once_per_bar_close)
```

**Step 2: Add new alertcondition entries**

Insert after the existing `alertcondition(anyBreakout, ...)`:

```pine
alertcondition(anyRevBull,  "Any Bullish Reversal",        "Bullish reversal detected")
alertcondition(anyRevBear,  "Any Bearish Reversal",        "Bearish reversal detected")
alertcondition(anyReversal, "Any Reversal",                "Reversal detected (bull or bear)")
alertcondition(anyBreakout or anyReversal, "Any Setup",    "Breakout or reversal detected")
```

**Step 3: Verify**

In TradingView alert dialog, confirm new entries appear: "Any Bullish Reversal", "Any Bearish Reversal", "Any Reversal", "Any Setup". "Any alert() function call" should now catch both breakout and reversal alerts.

**Step 4: Commit**

```bash
git add KeyLevelBreakout.pine
git commit -m "feat(KLB): add reversal/reclaim alerts and alertconditions"
```

---

### Task 9: Update Documentation

**Files:**
- Modify: `KeyLevelBreakout.md`
- Modify: `KeyLevelBreakout_Improvements.md`

**Step 1: Update KeyLevelBreakout.md**

Add to Features section (after "Confluence merging" bullet):
- **Reversal setups** — detects rejection off level zones (wick enters zone, close rejects); bullish reversals at LOW levels, bearish at HIGH levels
- **Reclaim setups** — context-enriched reversal when a prior breakout at that level was invalidated (false breakout → rejection)
- **Level zones** — wick-to-body zones for D/W levels, ATR-derived for PM/ORB (toggleable)
- **Setup time window** — configurable active window for Reversal/Reclaim (default 9:30-11:30 ET)

Add new rows to Inputs table:
| Show Reversal Setups | On | Setups | Enable reversal signal detection |
| Show Reclaim Setups | On | Setups | Enable reclaim labeling (reversal after failed breakout) |
| Setup Active Window (ET) | 0930-1130 | Setups | Time window for reversal/reclaim signals |
| Use Level Zones | On | Zones | Use wick-to-body zones instead of single-price levels |
| Zone Width for PM/ORB | 3.0 | Zones | ATR% zone width for levels without candle body data |
| PM H/L Reversal/Reclaim | On | Rev/Reclaim Toggles | Enable reversal/reclaim at premarket levels |
| Yest H/L Reversal/Reclaim | On | Rev/Reclaim Toggles | Enable reversal/reclaim at yesterday levels |
| Week H/L Reversal/Reclaim | On | Rev/Reclaim Toggles | Enable reversal/reclaim at weekly levels |
| ORB H/L Reversal/Reclaim | On | Rev/Reclaim Toggles | Enable reversal/reclaim at opening range levels |

Add new section "Reversal & Reclaim Setups" explaining the three setup types.

Add v1.7 changelog entry:
- **v1.7** — Reversal + Reclaim + Zones: wick-to-body zone detection for all levels (D/W from candle body, PM/ORB from ATR); reversal signals at level zones (~ prefix); reclaim signals when prior breakout invalidated (~~ prefix); configurable setup time window (default 9:30-11:30 ET); per-level toggles; blue/orange label colors; new alert conditions

**Step 2: Update KeyLevelBreakout_Improvements.md**

Mark items 4 (Level Confluence) and 7 (Retest Detection) status. Add note that Reversal/Reclaim setups were implemented in v1.7.

**Step 3: Commit**

```bash
git add KeyLevelBreakout.md KeyLevelBreakout_Improvements.md
git commit -m "docs: update KLB docs for v1.7 reversal/reclaim/zones"
```

---

## Verification Checklist

After all tasks complete, verify on TradingView:

- [ ] All new toggles OFF → signals identical to v1.6 (no new labels appear)
- [ ] `i_showReversal` ON, `i_useZones` OFF → reversals fire with zero-width zones (strict: wick must touch exact level)
- [ ] `i_showReversal` ON, `i_useZones` ON → reversals fire within body-to-wick zone
- [ ] `i_showReclaim` OFF → all reversals labeled "~" (no "~~" prefix)
- [ ] `i_showReclaim` ON + breakout at level that later invalidates → next reversal at that level shows "~~" prefix
- [ ] Reversal labels are blue (bull) / orange (bear), distinct from green/red breakouts
- [ ] Labels only appear within `i_setupWindow` (default 9:30-11:30 ET)
- [ ] Per-level toggles work (e.g., `i_revPM = false` suppresses PM reversals)
- [ ] `i_firstOnly` ON → each reversal fires once per level per session, re-arms when price moves away
- [ ] Existing breakout signals, post-breakout confirmation, and alerts all unchanged
- [ ] All alert conditions appear in TradingView alert dialog
- [ ] No Pine compile errors or warnings
