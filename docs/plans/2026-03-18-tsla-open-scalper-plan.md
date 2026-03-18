# TSLA Open Scalper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Pine Script v6 indicator that guides TSLA 0DTE/1DTE options trades through a 6-state decision machine from 9:20 to 9:45.

**Architecture:** Single-file overlay indicator on a 1m chart. State machine drives all visuals (labels, lines, table, bgcolor). 7 `request.security` / `request.security_lower_tf` calls fetch VIX, SPY, QQQ, and 30s sub-bar data (4x OHLC). All thresholds are TSLA-hardcoded from 280-day research.

**Tech Stack:** Pine Script v6, TradingView

**Spec:** `docs/plans/2026-03-18-tsla-open-scalper-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `TSLA_OpenScalper.pine` | The indicator — all logic, visuals, alerts in one file |
| `TSLA_OpenScalper.md` | Reference doc — inputs, rules, setup instructions |
| `TSLA_OpenScalper_TV.md` | TradingView publish description (~50 lines) |

## Testing Approach

Pine Script has no automated test framework. Each task is verified by:
1. Pasting the code into TradingView Pine Editor
2. Adding to a **TSLA 1m chart with Extended Hours ON**
3. Scrolling to a known date and visually confirming behavior
4. Checking Pine Editor console for compilation errors

**Reference dates for verification** (from research data):
- **2026-02-10** — VIX ~20 (moderate regime), good PM structure
- **2026-01-15** — VIX ~16 (calm), check that no hard-kill fires incorrectly
- **Any recent date** — check that premarket bars are visible and tracked

---

### Task 1: Indicator Skeleton + Time Detection

**Files:**
- Create: `TSLA_OpenScalper.pine`

This task creates the compilable shell: header, inputs, timezone/session detection, and the state variable declarations. No logic yet — just the framework that every subsequent task builds on.

- [ ] **Step 1: Create the indicator file with header, inputs, and session detection**

```pine
// © TSLA Open Scalper
// 0DTE/1DTE opening trade decision system (v1.0)
// Designed for TSLA on 1-min chart with Extended Hours ON
//@version=6
indicator("TSLA Open Scalper v1.0", overlay=true, max_labels_count=50, max_lines_count=10)

// ─── Inputs ────────────────────────────────────────────────
i_vixSymbol = input.string("CBOE:VIX", "VIX Symbol", tooltip="VIX data provider. Try TVC:VIX if CBOE:VIX fails.", group="Data")
i_slDistance = input.float(2.0, "Stop Loss Distance ($)", minval=0.5, step=0.5, tooltip="Distance below entry for SL line. Research: median max dip on HOLD days = $2.08", group="Trade")
i_showTable = input.bool(true, "Show Info Table", group="Visuals")
i_showBG    = input.bool(true, "Show Background Colors", group="Visuals")

// ─── Timezone & Session Detection ──────────────────────────
TZ = "America/New_York"

isPremarket   = not na(time(timeframe.period, "0400-0929:23456", TZ))
isRTH         = not na(time(timeframe.period, "0930-1600:23456", TZ))
newSession    = isPremarket and not isPremarket[1]  // first PM bar of day

// Time windows for state machine
is0920        = not na(time(timeframe.period, "0920-0920:23456", TZ))
is0925        = not na(time(timeframe.period, "0925-0925:23456", TZ))
is0929        = not na(time(timeframe.period, "0929-0929:23456", TZ))
is0930        = not na(time(timeframe.period, "0930-0930:23456", TZ))
is0931        = not na(time(timeframe.period, "0931-0931:23456", TZ))
is0935        = not na(time(timeframe.period, "0935-0935:23456", TZ))
is0940        = not na(time(timeframe.period, "0940-0940:23456", TZ))
is0945        = not na(time(timeframe.period, "0945-0945:23456", TZ))
isPreScan     = not na(time(timeframe.period, "0920-0929:23456", TZ))
isActiveWindow = not na(time(timeframe.period, "0920-0945:23456", TZ))

// ─── State Machine Variables ───────────────────────────────
var int   state         = 0   // 0=SLEEP,1=PRE_SCAN,2=OPENING,3=FAKEOUT,4=RULE_5M,5=EXIT,6=DONE
var int   confidence    = 0
var string tier         = "—"
var bool  hard_kill     = false
var bool  fakeout_fired = false

// Premarket tracking
var float pm_high       = na
var float pm_low        = na
var float pm_position   = na
var float pm_accel      = na
var float pm_late_trend = na
var float close_929     = na
var float open_925      = na
var float open_920_tsla = na

// Cross-symbol PM
var float spy_920       = na
var float qqq_920       = na
var float spy_929       = na
var float qqq_929       = na

// Session / entry
var float prev_day_close = na
var float gap            = na
var float open_930       = na
var float close_935      = na

// Trade result
var bool  is_hold       = false

// Visual object IDs
var line  entryLine     = na
var line  slLine        = na
var line  exitLine      = na

// ─── Daily Reset (fires on PM start or RTH start if no PM) ─
newRTH = isRTH and not isRTH[1]
if newSession or (newRTH and not pmSeen)
    state         := 0
    confidence    := 0
    tier          := "—"
    hard_kill     := false
    fakeout_fired := false
    pm_high       := na
    pm_low        := na
    pm_position   := na
    pm_accel      := na
    pm_late_trend := na
    close_929     := na
    open_925      := na
    open_920_tsla := na
    spy_920       := na
    qqq_920       := na
    spy_929       := na
    qqq_929       := na
    gap           := na
    open_930      := na
    close_935     := na
    is_hold       := false
    entryLine     := na
    slLine        := na
    exitLine      := na

// ─── Prev Day Close (track last RTH bar) ──────────────────
if isRTH
    prev_day_close := close

// ─── Placeholder: state transitions added in later tasks ───
```

- [ ] **Step 2: Verify indicator compiles and loads**

Open TradingView → Pine Editor → paste code → Add to TSLA 1m chart with Extended Hours.
Expected: No errors. No visuals (everything is placeholder). Inputs visible in settings.

- [ ] **Step 3: Commit**

```
git add TSLA_OpenScalper.pine
git commit -m "feat: TSLA Open Scalper v1.0 skeleton — inputs, session detection, state vars"
```

---

### Task 2: Premarket Tracking (PM Features)

**Files:**
- Modify: `TSLA_OpenScalper.pine`

Add the premarket bar-by-bar tracking that computes PM high/low/range, position at 9:29, acceleration 9:25→9:29, and late trend 9:20→9:29. Also add a temporary debug label to verify PM values.

- [ ] **Step 1: Add PM tracking logic after the daily reset block**

Replace the `// ─── Placeholder` comment with:

```pine
// ─── STATE 0→1: Premarket Tracking ────────────────────────
if isPremarket and state == 0
    state := 1

if state == 1 and isPremarket
    // Track PM high/low
    if na(pm_high) or high > pm_high
        pm_high := high
    if na(pm_low) or low < pm_low
        pm_low := low

    // Store 9:20 open for late trend
    if is0920
        open_920_tsla := open

    // Store 9:25 open for acceleration
    if is0925
        open_925 := open

    // At 9:29: freeze PM features
    if is0929
        close_929 := close
        float pm_range = pm_high - pm_low
        pm_position := pm_range > 0 ? (close - pm_low) / pm_range : 0.5
        pm_accel := not na(open_925) ? close - open_925 : na
        pm_late_trend := not na(open_920_tsla) ? close - open_920_tsla : na
```

- [ ] **Step 2: Add a temporary debug label at 9:29 to verify PM values**

After the PM freeze block, add:

```pine
    // DEBUG: show PM values (remove after verification)
    if is0929
        label.new(bar_index, high,
             str.format("PM pos={0,number,#.##} acc={1,number,#.##} trend={2,number,#.##}",
             pm_position, pm_accel, pm_late_trend),
             style=label.style_label_down, color=color.gray, textcolor=color.white, size=size.small)
```

- [ ] **Step 3: Verify on chart**

Load on TSLA 1m Extended Hours. Scroll to a recent date.
Expected: Gray debug label at 9:29 bar showing PM position (0.0–1.0), acceleration, and late trend values. PM values should be `na` if Extended Hours is OFF.

- [ ] **Step 4: Add Extended Hours guard**

After session detection, before state machine:

```pine
// ─── Extended Hours Guard ──────────────────────────────────
var bool pmSeen = false
if isPremarket
    pmSeen := true
if newSession
    pmSeen := false

// Warning if no PM data by 9:30
if is0930 and not pmSeen
    label.new(bar_index, high, "⚠ Extended Hours OFF — PM data missing",
         style=label.style_label_down, color=color.orange, textcolor=color.white, size=size.normal)
```

- [ ] **Step 5: Commit**

```
git add TSLA_OpenScalper.pine
git commit -m "feat(v1.0): premarket tracking — PM position, acceleration, late trend"
```

---

### Task 3: External Data (VIX, SPY, QQQ)

**Files:**
- Modify: `TSLA_OpenScalper.pine`

Add the 3 `request.security` calls for VIX prev-day close, SPY 1m close, and QQQ 1m close. Track SPY/QQQ values at 9:20 and 9:29 for triple alignment.

- [ ] **Step 1: Add request.security calls after inputs**

Insert after the inputs section:

```pine
// ─── External Data ─────────────────────────────────────────
vix_prev_close = request.security(i_vixSymbol, "D", close[1], lookahead=barmerge.lookahead_on)
spy_close      = request.security("SPY", "1", close)
qqq_close      = request.security("QQQ", "1", close)
```

- [ ] **Step 2: Track SPY/QQQ at 9:20 and 9:29 inside state 1 block**

Inside the `if state == 1 and isPremarket` block, after the TSLA 9:20/9:29 logic:

```pine
    // Track SPY/QQQ for triple alignment
    if is0920
        spy_920 := spy_close
        qqq_920 := qqq_close
    if is0929
        spy_929 := spy_close
        qqq_929 := qqq_close
```

- [ ] **Step 3: Update debug label to include VIX and alignment**

Replace the debug label text with:

```pine
    if is0929
        bool tsla_up = pm_late_trend > 0
        bool spy_up  = not na(spy_929) and not na(spy_920) ? spy_929 > spy_920 : false
        bool qqq_up  = not na(qqq_929) and not na(qqq_920) ? qqq_929 > qqq_920 : false
        string alignStr = str.format("T{0} S{1} Q{2}", tsla_up?"↑":"↓", spy_up?"↑":"↓", qqq_up?"↑":"↓")
        label.new(bar_index, high,
             str.format("PM={0,number,#.##} VIX={1,number,#.#} {2}",
             pm_position, nz(vix_prev_close), alignStr),
             style=label.style_label_down, color=color.gray, textcolor=color.white, size=size.small)
```

- [ ] **Step 4: Verify on chart**

Expected: Debug label at 9:29 shows PM position, VIX value (e.g., "VIX=21.3"), and triple alignment arrows (e.g., "T↑ S↑ Q↓").

- [ ] **Step 5: Commit**

```
git add TSLA_OpenScalper.pine
git commit -m "feat(v1.0): external data — VIX prev-day close, SPY/QQQ PM tracking"
```

---

### Task 4: Confidence Scoring + Hard Kills

**Files:**
- Modify: `TSLA_OpenScalper.pine`

Implement the 5-check confidence score and 3 hard-kill overrides at 9:29. Compute the tier (HIGH/MED/LOW/NO-GO).

- [ ] **Step 1: Add confidence scoring logic at 9:29**

Inside the `if is0929` block (after PM freeze), replace the debug label with:

```pine
    if is0929
        // ── Confidence scoring ──
        confidence := 0
        hard_kill := false

        // Check 1: PM Position > Q1
        if not na(pm_position) and pm_position > 0.219
            confidence += 1

        // Check 2: PM Acceleration positive
        if not na(pm_accel) and pm_accel > 0
            confidence += 1

        // Check 3: VIX sweet spot 18–25
        if not na(vix_prev_close) and vix_prev_close >= 18 and vix_prev_close <= 25
            confidence += 1

        // Check 4: Triple PM alignment (all up)
        bool tsla_up = not na(pm_late_trend) and pm_late_trend > 0
        bool spy_up  = not na(spy_929) and not na(spy_920) and spy_929 > spy_920
        bool qqq_up  = not na(qqq_929) and not na(qqq_920) and qqq_929 > qqq_920
        if tsla_up and spy_up and qqq_up
            confidence += 1

        // Check 5: No danger combo (gap down + PM flat)
        float est_gap = not na(prev_day_close) ? close - prev_day_close : 0
        bool gapDangerFlat = est_gap < -2 and not na(pm_late_trend) and math.abs(pm_late_trend) < 0.48
        if not gapDangerFlat
            confidence += 1

        // ── Hard kills ──
        if not na(vix_prev_close) and vix_prev_close <= 15
            hard_kill := true
        if not na(pm_position) and pm_position < 0.219 and not na(pm_accel) and pm_accel < 0
            hard_kill := true
        if gapDangerFlat
            hard_kill := true

        // ── Tier mapping ──
        tier := hard_kill ? "NO-GO" : confidence >= 5 ? "HIGH" : confidence >= 3 ? "MED" : confidence >= 2 ? "LOW" : "NO-GO"

        // Debug label (will be replaced by corner table in Task 6)
        color tierColor = tier == "HIGH" ? color.green : tier == "MED" ? color.lime : tier == "LOW" ? color.gray : color.red
        label.new(bar_index, low, str.format("{0} ({1}/5)", tier, confidence),
             style=label.style_label_up, color=tierColor, textcolor=color.white, size=size.normal)
```

- [ ] **Step 2: Verify on chart**

Scroll through several dates. Expected:
- Days with VIX 18–25 + strong PM should show HIGH/MED
- Days with VIX ≤ 15 should show NO-GO (hard kill)
- Days with PM position near bottom + negative accel should show NO-GO

- [ ] **Step 3: Commit**

```
git add TSLA_OpenScalper.pine
git commit -m "feat(v1.0): confidence scoring — 5 checks + 3 hard kills + tier mapping"
```

---

### Task 5: State 2 — Opening (Entry + SL Lines)

**Files:**
- Modify: `TSLA_OpenScalper.pine`

Implement the 9:30 state transition: store entry price, draw entry and SL lines, place entry label.

- [ ] **Step 1: Add State 2 logic after the premarket block**

```pine
// ─── STATE 2: OPENING (9:30) ──────────────────────────────
if is0930 and state == 1
    open_930 := open
    gap := not na(prev_day_close) ? open - prev_day_close : na
    state := 2

    // Draw entry + SL lines (extend 20 bars forward)
    if tier == "HIGH" or tier == "MED"
        entryLine := line.new(bar_index, open_930, bar_index + 20, open_930,
                     color=color.blue, width=2, style=line.style_solid)
        slLine    := line.new(bar_index, open_930 - i_slDistance, bar_index + 20, open_930 - i_slDistance,
                     color=color.red, width=2, style=line.style_solid)
        label.new(bar_index, low, "ENTERED (small)",
             style=label.style_label_up, color=color.blue, textcolor=color.white, size=size.normal)
    else if tier == "LOW"
        entryLine := line.new(bar_index, open_930, bar_index + 20, open_930,
                     color=color.gray, width=1, style=line.style_dashed)
        label.new(bar_index, low, "WATCHING",
             style=label.style_label_up, color=color.gray, textcolor=color.white, size=size.normal)
    // NO-GO: no lines, no label (already skipped)
```

- [ ] **Step 2: Verify on chart**

Expected: On GO days — solid blue entry line at 9:30 open price, solid red SL line $2 below, "ENTERED" label. On LOW days — dashed gray line, "WATCHING" label. On NO-GO — nothing drawn.

- [ ] **Step 3: Commit**

```
git add TSLA_OpenScalper.pine
git commit -m "feat(v1.0): state 2 opening — entry/SL lines and entry label"
```

---

### Task 6: State 3 — Fakeout Detection (30s Data)

**Files:**
- Modify: `TSLA_OpenScalper.pine`

Add `request.security_lower_tf` for 30s sub-bars. Detect fakeout patterns on the 9:31 bar. Include fallback for missing 30s data.

- [ ] **Step 1: Add 30s request.security_lower_tf after other external data calls**

```pine
// 30s sub-bars for fakeout detection (Premium+ required)
// request.security_lower_tf returns float[] array — one element per sub-bar within each 1m bar
// 4 separate calls needed (no tuple destructuring support). Budget: 7 of 40 total.
sub_open  = request.security_lower_tf(syminfo.tickerid, "30S", open)
sub_high  = request.security_lower_tf(syminfo.tickerid, "30S", high)
sub_low   = request.security_lower_tf(syminfo.tickerid, "30S", low)
sub_close = request.security_lower_tf(syminfo.tickerid, "30S", close)
```

Note: If `request.security_lower_tf` is not available or 30S is unsupported, this will cause a compile error. In that case, comment out these 4 calls and set a `has30s_available = false` flag. See fallback in Step 3.

- [ ] **Step 2: Add fakeout detection at 9:31**

```pine
// ─── STATE 3: FAKEOUT CHECK (same 9:30 bar — evaluated at bar close ~9:31) ──
// Pine evaluates at bar close. The 1m bar with time=9:30 closes at ~9:31.
// Its 30s sub-bars are: bar1=9:30:00-9:30:29, bar2=9:30:30-9:30:59.
// State 2 already ran above (setting state=2), so this fires on the same bar.
if is0930 and state == 2
    state := 3
    bool has30s = array.size(sub_open) >= 2

    if has30s
        float b1_open  = array.get(sub_open, 0)
        float b1_high  = array.get(sub_high, 0)
        float b1_low   = array.get(sub_low, 0)
        float b1_close = array.get(sub_close, 0)
        float b2_open  = array.get(sub_open, 1)
        float b2_close = array.get(sub_close, 1)

        bool b1_up   = b1_close >= b1_open
        bool b2_down = b2_close < b2_open
        bool b1_down = b1_close < b1_open
        float b1_range = b1_high - b1_low

        // Fakeout: bar1 UP → bar2 DOWN
        if b1_up and b2_down
            fakeout_fired := true
            label.new(bar_index, high, "EXIT — FAKEOUT",
                 style=label.style_label_down, color=color.red, textcolor=color.white, size=size.large)

        // Chaotic: bar1 range > $3.04
        if b1_range > 3.04 and not fakeout_fired
            label.new(bar_index, high, "⚠ CHAOTIC",
                 style=label.style_label_down, color=color.orange, textcolor=color.white, size=size.small)

        // Shakeout: DOWN → DOWN (note only, no exit)
        if b1_down and b2_down
            label.new(bar_index, low, "shakeout — watch",
                 style=label.style_label_up, color=color.gray, textcolor=color.white, size=size.tiny)
    else
        state := 3  // skip fakeout, advance state anyway
```

- [ ] **Step 3: Add fallback if 30s data is unavailable**

If the 30s call fails to compile, replace the `request.security_lower_tf` call with:

```pine
// Fallback: no 30s data available
var bool has30s_available = false
// (set to true if request.security_lower_tf compiles)
```

And guard the fakeout block: `if is0931 and state == 2 and has30s_available`

- [ ] **Step 4: Verify on chart**

Expected: On days with fakeout patterns, a red "EXIT — FAKEOUT" label appears above the 9:31 bar. On chaotic days, an orange warning. On shakeout days, a small gray note.

- [ ] **Step 5: Commit**

```
git add TSLA_OpenScalper.pine
git commit -m "feat(v1.0): state 3 fakeout detection — 30s patterns with fallback"
```

---

### Task 7: State 4 — 5-Minute Rule (HOLD/BAIL)

**Files:**
- Modify: `TSLA_OpenScalper.pine`

The core decision: at 9:35, compare close to 9:30 open. HOLD or BAIL. Handle the recovery-HOLD special case.

- [ ] **Step 1: Add 5m rule logic at 9:35**

```pine
// ─── STATE 4: 5M RULE (9:35) ──────────────────────────────
if is0935 and (state == 2 or state == 3)
    close_935 := close
    state := 4
    is_hold := not na(close_935) and not na(open_930) and close_935 > open_930

    if is_hold
        // HOLD
        if fakeout_fired
            label.new(bar_index, low, "RECOVERY HOLD",
                 style=label.style_label_up, color=color.teal, textcolor=color.white, size=size.large)
        else
            label.new(bar_index, low, "HOLD — ADD SIZE",
                 style=label.style_label_up, color=color.green, textcolor=color.white, size=size.large)
    else
        // BAIL
        label.new(bar_index, low, "BAIL — EXIT ALL",
             style=label.style_label_up, color=color.red, textcolor=color.white, size=size.large)
```

Note: `is_hold` must be declared in the state variables section (Task 1): `var bool is_hold = false` and reset in the daily reset block.

- [ ] **Step 2: Verify on chart**

Scroll through dates. Expected:
- Days where 9:35 close > 9:30 open → green "HOLD — ADD SIZE" label
- Days where 9:35 close ≤ 9:30 open → red "BAIL — EXIT ALL" label
- Days with fakeout + recovery → teal "RECOVERY HOLD" label

- [ ] **Step 3: Commit**

```
git add TSLA_OpenScalper.pine
git commit -m "feat(v1.0): state 4 five-minute rule — HOLD/BAIL/RECOVERY decision"
```

---

### Task 8: States 5+6 — Exit Window + Done

**Files:**
- Modify: `TSLA_OpenScalper.pine`

Add the 9:40 exit signal and 9:45 overhold warning.

- [ ] **Step 1: Add exit and done logic**

```pine
// ─── STATE 5: EXIT WINDOW (9:40) ──────────────────────────
if is0940 and state == 4
    state := 5
    if is_hold
        label.new(bar_index, high, "EXIT — TAKE PROFIT",
             style=label.style_label_down, color=color.green, textcolor=color.white, size=size.large)
        exitLine := line.new(bar_index, low, bar_index, high,
                    color=color.green, width=1, style=line.style_solid)

// ─── STATE 6: DONE (after 9:40, starting 9:41) ────────────
// Transition one bar after EXIT window — amber overhold zone from 9:41+
bool isPast0940 = isRTH and not is0940 and not is0930 and not is0935 and state == 5
if isPast0940
    state := 6

if is0945 and state == 6 and is_hold
    label.new(bar_index, high, "OVERHOLD — CLOSE",
         style=label.style_label_down, color=color.orange, textcolor=color.white, size=size.normal)
```

- [ ] **Step 2: Verify on chart**

Expected: On HOLD days — green "EXIT" label at 9:40 with vertical line, amber "OVERHOLD" at 9:45. On BAIL days — no exit labels (already out).

- [ ] **Step 3: Commit**

```
git add TSLA_OpenScalper.pine
git commit -m "feat(v1.0): states 5+6 — exit window at 9:40, overhold warning at 9:45"
```

---

### Task 9: Corner Table

**Files:**
- Modify: `TSLA_OpenScalper.pine`

Add the info table (top-right) that shows state, metrics, and actions. Updates at each state transition. This replaces the debug labels from earlier tasks.

- [ ] **Step 1: Create table and update logic**

Add at the end of the script (after all state logic):

```pine
// ─── Corner Table ──────────────────────────────────────────
var table infoTable = table.new(position.top_right, 2, 5,
     bgcolor=color.new(color.black, 80), border_width=1, border_color=color.gray)

if i_showTable and isActiveWindow
    // Row 0: Title
    table.cell(infoTable, 0, 0, "TSLA OPEN SCALP", text_color=color.white, text_size=size.small)
    table.cell(infoTable, 1, 0, "v1.0", text_color=color.gray, text_size=size.tiny)

    // Row 1: State + tier
    string stateStr = state == 0 ? "SLEEP" : state == 1 ? "PRE-SCAN" : state == 2 ? "OPENING" :
                      state == 3 ? "FAKEOUT" : state == 4 ? (is_hold ? "HOLD" : "BAIL") :
                      state == 5 ? "EXIT" : "DONE"
    color stateColor = tier == "HIGH" ? color.green : tier == "MED" ? color.lime :
                       tier == "LOW" ? color.gray : tier == "NO-GO" ? color.red : color.white
    table.cell(infoTable, 0, 1, stateStr, text_color=stateColor, text_size=size.normal)
    table.cell(infoTable, 1, 1, tier != "—" ? str.format("{0} ({1}/5)", tier, confidence) : "",
               text_color=stateColor, text_size=size.small)

    // Row 2: VIX
    string vixStr = not na(vix_prev_close) ? str.format("VIX: {0,number,#.#}", vix_prev_close) : "VIX: N/A"
    string vixLabel = not na(vix_prev_close) ? (vix_prev_close <= 15 ? " ✗" : vix_prev_close >= 18 and vix_prev_close <= 25 ? " ✓" : "") : ""
    color vixColor = not na(vix_prev_close) ? (vix_prev_close <= 15 ? color.red : vix_prev_close >= 18 and vix_prev_close <= 25 ? color.green : color.gray) : color.gray
    table.cell(infoTable, 0, 2, vixStr + vixLabel, text_color=vixColor, text_size=size.small)

    // Row 3: PM metrics
    string pmStr = not na(pm_position) ? str.format("PM: pos={0,number,#.##} acc={1,number,#.#}", pm_position, nz(pm_accel)) : "PM: waiting..."
    table.cell(infoTable, 0, 3, pmStr, text_color=color.white, text_size=size.small)

    // Row 4: Alignment or action
    if state <= 1
        bool tsla_up = not na(pm_late_trend) and pm_late_trend > 0
        bool spy_up  = not na(spy_929) and not na(spy_920) and spy_929 > spy_920
        bool qqq_up  = not na(qqq_929) and not na(qqq_920) and qqq_929 > qqq_920
        string alignStr = str.format("T{0} S{1} Q{2}", tsla_up?"↑":"↓", spy_up?"↑":"↓", qqq_up?"↑":"↓")
        table.cell(infoTable, 0, 4, "Align: " + alignStr, text_color=color.white, text_size=size.small)
    else if state >= 2 and not na(open_930)
        string entryStr = str.format("Entry: {0,number,#.##}  SL: {1,number,#.##}", open_930, open_930 - i_slDistance)
        table.cell(infoTable, 0, 4, entryStr, text_color=color.white, text_size=size.small)

if not isActiveWindow or not i_showTable
    table.clear(infoTable, 0, 0, 1, 4)
```

- [ ] **Step 2: Remove all debug labels from Tasks 2–4**

Delete any `label.new(...` lines that were marked as debug/temporary.

- [ ] **Step 3: Verify on chart**

Expected: Table appears top-right during 9:20–9:45 window. Shows state, tier, VIX, PM metrics, alignment or entry/SL prices depending on state. Disappears after 9:45.

- [ ] **Step 4: Commit**

```
git add TSLA_OpenScalper.pine
git commit -m "feat(v1.0): corner table — state/tier/VIX/PM/alignment info panel"
```

---

### Task 10: Background Colors

**Files:**
- Modify: `TSLA_OpenScalper.pine`

Add subtle bgcolor bands that shift with each state transition.

- [ ] **Step 1: Add bgcolor logic at the end of the script (before table)**

```pine
// ─── Background Colors ─────────────────────────────────────
color bgColor = na
if i_showBG and isActiveWindow
    if state == 1
        bgColor := tier == "—" ? color.new(color.gray, 95) :  // computing
                   tier == "NO-GO" ? color.new(color.red, 92) :
                   color.new(color.green, 92)
    else if state == 2 or state == 3
        if fakeout_fired
            bgColor := color.new(color.red, 85)  // fakeout flash
        else
            bgColor := tier == "NO-GO" ? color.new(color.red, 92) : color.new(color.green, 92)
    else if state == 4
        bgColor := is_hold ? color.new(color.green, 90) : color.new(color.red, 88)
    else if state == 5
        bgColor := color.new(color.orange, 92)  // EXIT window
    else if state == 6
        bgColor := color.new(color.orange, 92)  // overhold zone (9:41–9:45)

bgcolor(bgColor)
```

- [ ] **Step 2: Verify on chart**

Expected: Subtle colored background bands during 9:20–9:45. Green for GO, red for NO-GO/BAIL/fakeout, amber for exit window. Transparent after 9:45.

- [ ] **Step 3: Commit**

```
git add TSLA_OpenScalper.pine
git commit -m "feat(v1.0): background colors — state-driven bgcolor bands"
```

---

### Task 11: Alerts

**Files:**
- Modify: `TSLA_OpenScalper.pine`

Add `alert()` calls at each decision point with dynamic messages.

- [ ] **Step 1: Add alert() calls inside each state transition**

At 9:29 (inside confidence scoring block):
```pine
        // Alert: pre-open assessment
        if not hard_kill and confidence >= 3
            alert(str.format("TSLA GO: confidence {0} ({1}/5) — enter small at open", tier, confidence), alert.freq_once_per_bar)
        if hard_kill or confidence < 2
            string reason = hard_kill ? (not na(vix_prev_close) and vix_prev_close <= 15 ? "VIX ≤ 15" :
                           (not na(pm_position) and pm_position < 0.219 and not na(pm_accel) and pm_accel < 0 ? "P9 bear" : "gap trap")) : "low score"
            alert(str.format("TSLA NO-GO: {0} — skip today", reason), alert.freq_once_per_bar)
```

At 9:31 (inside fakeout block, after fakeout_fired := true):
```pine
            alert("TSLA FAKEOUT — EXIT NOW", alert.freq_once_per_bar)
```

At 9:35 (inside 5m rule block):
```pine
    if close_935 > open_930
        alert(str.format("TSLA HOLD — ADD SIZE (confidence: {0})", tier), alert.freq_once_per_bar)
    else
        alert("TSLA BAIL — EXIT ALL", alert.freq_once_per_bar)
```

- [ ] **Step 2: Verify**

Check Pine Editor console — no compilation errors. Alerts won't fire on historical data (only live). Confirm the `alert()` calls are syntactically correct.

- [ ] **Step 3: Commit**

```
git add TSLA_OpenScalper.pine
git commit -m "feat(v1.0): alerts — dynamic messages at each decision point"
```

---

### Task 12: Documentation

**Files:**
- Create: `TSLA_OpenScalper.md`
- Create: `TSLA_OpenScalper_TV.md`

- [ ] **Step 1: Write reference doc**

`TSLA_OpenScalper.md` — full reference including:
- Setup instructions (1m chart, Extended Hours ON, how to create alert)
- All inputs with descriptions
- State machine explanation with timing
- Confidence scoring details (all 5 checks + 3 hard kills)
- Research references for each threshold
- Troubleshooting (no PM bars, VIX N/A, 30s unavailable)

- [ ] **Step 2: Write TradingView description**

`TSLA_OpenScalper_TV.md` — concise (~50 lines):
- What it does (one paragraph)
- Key signals (5m rule, PM filter, fakeout detection)
- Setup requirements
- Win rates and research basis

- [ ] **Step 3: Commit**

```
git add TSLA_OpenScalper.md TSLA_OpenScalper_TV.md
git commit -m "docs: TSLA Open Scalper reference doc and TV description"
```

---

### Task 13: Final Verification + Cleanup

**Files:**
- Modify: `TSLA_OpenScalper.pine`

- [ ] **Step 1: Remove any remaining debug labels**

Search for "DEBUG" or temporary labels. Remove them.

- [ ] **Step 2: Full walkthrough on 3 dates**

Load on TSLA 1m Extended Hours. Check these scenarios:
1. **A good day** — VIX moderate, PM position high, all align → should show HIGH, ENTERED, HOLD
2. **A bad day** — VIX ≤ 15 or P9 bear → should show NO-GO, no entry
3. **A fakeout day** — bar1 UP → bar2 DOWN → should show FAKEOUT EXIT, then either BAIL or RECOVERY HOLD

- [ ] **Step 3: Verify version string matches everywhere**

Header comment (line 2), table title, both docs.

- [ ] **Step 4: Final commit**

```
git add -A
git commit -m "feat: TSLA Open Scalper v1.0 — complete indicator with all states, table, alerts, docs"
```
