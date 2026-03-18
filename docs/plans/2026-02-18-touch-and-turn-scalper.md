# Touch & Turn Scalper — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Pine Script v6 indicator that detects liquidity candles on the 15m opening range, then signals touch-and-turn reversal entries on the 1m chart with Fibonacci-based TP and fixed 2:1 R:R.

**Architecture:** Single-timeframe indicator running on 1m chart. Pulls 15m opening candle OHLC and daily ATR via `request.security` (non-repainting). State machine tracks one trade per day: detect → qualify → arm → fill → exit.

**Tech Stack:** Pine Script v6, TradingView indicator API

**Design doc:** `docs/plans/2026-02-18-touch-and-turn-scalper-design.md`

**Testing:** Pine Script has no test framework. Each task includes manual verification steps in TradingView. Load the indicator on a 1m chart (e.g., META, NFLX, AAPL) and visually confirm behavior against known trading days.

---

### Task 1: Scaffold — Inputs, Data Sources, Session Detection

**Files:**
- Create: `TouchAndTurn.pine`

**Step 1: Write the indicator scaffold with inputs and data**

```pine
// © Touch & Turn Scalper
// Detects liquidity candles on the 15m opening range
// Signals reversal entries on 1m chart with Fibonacci TP
//@version=6
indicator("Touch & Turn", overlay=true, max_lines_count=500, max_labels_count=500)

// ─── Inputs ────────────────────────────────────────────────
i_tpLevel  = input.string("38.2%", "TP Level", options=["38.2%", "61.8%"], group="Parameters")
i_atrLen   = input.int(14, "ATR Length (Daily)", minval=1, group="Parameters")
i_session  = input.session("0930-1600", "Session", group="Parameters")

// ─── Daily ATR (non-repainting) ────────────────────────────
dailyATR = request.security(syminfo.tickerid, "D", ta.atr(i_atrLen)[1], lookahead=barmerge.lookahead_on)
atrThreshold = dailyATR * 0.25

// ─── 15m Opening Candle (confirmed bar only) ──────────────
[o15, h15, l15, c15] = request.security(syminfo.tickerid, "15",
     [open[1], high[1], low[1], close[1]], lookahead=barmerge.lookahead_on)

// ─── Session & Opening Bar Detection ──────────────────────
_t15       = time("15")
_t15chg    = ta.change(_t15)
new15bar   = not na(_t15chg) and _t15chg != 0

inSession  = not na(time(timeframe.period, i_session))
_sesChg    = ta.change(inSession ? 1 : 0)
sessionOpen = _sesChg > 0  // first bar of session

// ─── Debug: plot ATR value as label on session open ────────
if sessionOpen
    label.new(bar_index, high, "ATR: " + str.tostring(dailyATR, "#.##") +
         "\nThreshold: " + str.tostring(atrThreshold, "#.##"),
         style=label.style_label_down, color=color.gray, textcolor=color.white, size=size.small)
```

**Step 2: Verify in TradingView**

- Add to 1m chart on any US stock (META, NFLX, etc.)
- Confirm: gray debug labels appear at market open showing ATR value and 25% threshold
- Confirm: no errors in Pine Editor console

**Step 3: Commit**

```bash
git add TouchAndTurn.pine
git commit -m "feat: scaffold Touch & Turn indicator with inputs and data sources"
```

---

### Task 2: Opening Range Qualification

**Files:**
- Modify: `TouchAndTurn.pine`

**Step 1: Add state variables and qualification logic**

After the session detection block, add:

```pine
// ─── State Machine ────────────────────────────────────────
// 0=WAITING_FOR_OPEN, 1=QUALIFYING, 2=ARMED, 3=IN_TRADE, 4=DONE
var int   state      = 0
var float rangeHigh  = na
var float rangeLow   = na
var float rangeOpen  = na
var float rangeClose = na
var int   rangeBar   = na   // bar_index of the opening 15m bar close
var int   direction  = 0    // 1=long, -1=short
var float entryPrice = na
var float tpPrice    = na
var float slPrice    = na

// Reset at session open
if sessionOpen
    state := 0
    rangeHigh  := na
    rangeLow   := na
    rangeOpen  := na
    rangeClose := na
    rangeBar   := na
    direction  := 0
    entryPrice := na
    tpPrice    := na
    slPrice    := na

// ─── Qualifying: detect first completed 15m bar after open ─
// The first new15bar AFTER sessionOpen captures the completed opening candle
if state == 0 and new15bar and inSession and not sessionOpen
    rangeHigh  := h15
    rangeLow   := l15
    rangeOpen  := o15
    rangeClose := c15
    rangeBar   := bar_index

    candleRange = h15 - l15
    qualified   = candleRange >= atrThreshold

    if qualified
        // Determine direction: opposite to opening candle
        if c15 < o15   // bearish open → go long
            direction := 1
        else if c15 > o15  // bullish open → go short
            direction := -1
        else
            direction := 0  // doji — skip

        if direction != 0
            state := 2  // skip to ARMED (qualification + arming in one step)
        else
            state := 4  // DONE — doji, no trade
    else
        state := 4  // DONE — not qualified
```

**Step 2: Add qualification labels (replacing debug label)**

Remove the debug label from Task 1 and add:

```pine
// ─── Qualification Labels ─────────────────────────────────
var label qualLabel = na
if state == 2 and state[1] != 2
    if not na(qualLabel)
        label.delete(qualLabel)
    dirText = direction == 1 ? "LONG" : "SHORT"
    qualLabel := label.new(bar_index, direction == 1 ? low : high,
         "Qualified: " + dirText,
         style=direction == 1 ? label.style_label_up : label.style_label_down,
         color=direction == 1 ? color.green : color.red,
         textcolor=color.white, size=size.small)
else if state == 4 and state[1] != 4 and not na(rangeBar)
    if not na(qualLabel)
        label.delete(qualLabel)
    qualLabel := label.new(bar_index, high, "Not Qualified",
         style=label.style_label_down, color=color.gray, textcolor=color.white, size=size.small)
```

**Step 3: Verify in TradingView**

- Reload on 1m chart (META or NFLX)
- Scroll through multiple days
- Confirm: "Qualified: LONG" or "Qualified: SHORT" labels appear after the opening 15m candle on high-volatility days
- Confirm: "Not Qualified" labels appear on low-volatility days
- Confirm: direction matches candle color (red open → LONG, green open → SHORT)

**Step 4: Commit**

```bash
git add TouchAndTurn.pine
git commit -m "feat: add opening range qualification and direction detection"
```

---

### Task 3: Visuals — Range Box + Fibonacci Levels

**Files:**
- Modify: `TouchAndTurn.pine`

**Step 1: Draw the opening range box and Fibonacci lines**

After the qualification logic, add:

```pine
// ─── Visuals: Range Box + Fibonacci Lines ─────────────────
var box   rangeBox  = na
var line  fib382Ln  = na
var line  fib500Ln  = na
var line  fib618Ln  = na

// Draw on qualification (state just became 2 or 4 with valid range)
if not na(rangeBar) and (state == 2 or state == 4) and na(rangeBox)
    // Range box — extends to end of day (we'll use a far-right bar)
    boxColor = state == 2 ? color.new(color.blue, 90) : color.new(color.gray, 90)
    borderClr = state == 2 ? color.new(color.blue, 60) : color.new(color.gray, 60)
    rangeBox := box.new(rangeBar, rangeHigh, rangeBar + 390, rangeLow,
         bgcolor=boxColor, border_color=borderClr, border_width=1)

    if state == 2  // Only draw Fib lines for qualified setups
        range   = rangeHigh - rangeLow
        fib382  = rangeLow + range * 0.382
        fib500  = rangeLow + range * 0.5
        fib618  = rangeLow + range * 0.618
        farBar  = rangeBar + 390

        fib382Ln := line.new(rangeBar, fib382, farBar, fib382,
             color=color.new(color.purple, 30), style=line.style_dashed, width=1)
        fib500Ln := line.new(rangeBar, fib500, farBar, fib500,
             color=color.new(color.gray, 50), style=line.style_dotted, width=1)
        fib618Ln := line.new(rangeBar, fib618, farBar, fib618,
             color=color.new(color.purple, 30), style=line.style_dashed, width=1)

// Clean up previous day's drawings at session open
if sessionOpen
    if not na(rangeBox)
        box.delete(rangeBox)
        rangeBox := na
    if not na(fib382Ln)
        line.delete(fib382Ln)
        fib382Ln := na
    if not na(fib500Ln)
        line.delete(fib500Ln)
        fib500Ln := na
    if not na(fib618Ln)
        line.delete(fib618Ln)
        fib618Ln := na
```

**Step 2: Verify in TradingView**

- Reload on 1m chart
- Confirm: blue shaded box appears on qualified days spanning the opening range
- Confirm: gray shaded box appears on non-qualified days
- Confirm: three Fibonacci lines (38.2%, 50%, 61.8%) appear inside the box on qualified days
- Confirm: Fibonacci lines do NOT appear on non-qualified days
- Confirm: old drawings are cleaned up at each new session open

**Step 3: Commit**

```bash
git add TouchAndTurn.pine
git commit -m "feat: add opening range box and Fibonacci level visuals"
```

---

### Task 4: Trade Levels + Entry Detection (ARMED → IN_TRADE)

**Files:**
- Modify: `TouchAndTurn.pine`

**Step 1: Calculate trade levels and draw entry/SL/TP lines**

After the Fibonacci visuals, add trade level calculation inside the qualification block (when state becomes 2):

```pine
// ─── Trade Level Calculation ──────────────────────────────
// (inside the state == 2 transition block, after direction is set)
var line  entryLn = na
var line  tpLn    = na
var line  slLn    = na

if state == 2 and state[1] != 2
    range    = rangeHigh - rangeLow
    fibMult  = i_tpLevel == "38.2%" ? 0.382 : 0.618

    if direction == 1  // LONG
        entryPrice := rangeLow
        tpPrice    := rangeLow + range * fibMult
        slPrice    := rangeLow - (tpPrice - rangeLow) / 2.0
    else  // SHORT
        entryPrice := rangeHigh
        tpPrice    := rangeHigh - range * fibMult
        slPrice    := rangeHigh + (rangeHigh - tpPrice) / 2.0

    farBar = rangeBar + 390

    entryLn := line.new(rangeBar, entryPrice, farBar, entryPrice,
         color=color.green, style=line.style_dashed, width=2)
    tpLn    := line.new(rangeBar, tpPrice,    farBar, tpPrice,
         color=color.blue,  style=line.style_dashed, width=2)
    slLn    := line.new(rangeBar, slPrice,    farBar, slPrice,
         color=color.red,   style=line.style_solid,  width=2)

    label.new(farBar, entryPrice, "Entry",
         style=label.style_label_left, color=color.new(color.green, 80), textcolor=color.green, size=size.small)
    label.new(farBar, tpPrice, "TP " + i_tpLevel,
         style=label.style_label_left, color=color.new(color.blue, 80), textcolor=color.blue, size=size.small)
    label.new(farBar, slPrice, "SL",
         style=label.style_label_left, color=color.new(color.red, 80), textcolor=color.red, size=size.small)
```

**Step 2: Add entry fill detection**

```pine
// ─── Entry Fill Detection ─────────────────────────────────
bool entryFilled = false

if state == 2
    // Check 90-minute timeout (bar_index distance from rangeBar)
    // On 1m chart, 90 bars ≈ 90 minutes
    if bar_index - rangeBar > 90
        state := 4  // DONE — timeout
        label.new(bar_index, direction == 1 ? low : high, "Timeout",
             style=direction == 1 ? label.style_label_up : label.style_label_down,
             color=color.gray, textcolor=color.white, size=size.small)
    else
        // Check if price touched entry level
        if direction == 1 and low <= entryPrice
            state := 3
            entryFilled := true
        else if direction == -1 and high >= entryPrice
            state := 3
            entryFilled := true

    if entryFilled
        label.new(bar_index, direction == 1 ? low : high,
             direction == 1 ? "Long Fill" : "Short Fill",
             style=direction == 1 ? label.style_label_up : label.style_label_down,
             color=direction == 1 ? color.green : color.red,
             textcolor=color.white, size=size.small)
```

**Step 3: Clean up trade lines at session open**

Add to the sessionOpen cleanup block:

```pine
    if not na(entryLn)
        line.delete(entryLn)
        entryLn := na
    if not na(tpLn)
        line.delete(tpLn)
        tpLn := na
    if not na(slLn)
        line.delete(slLn)
        slLn := na
```

**Step 4: Verify in TradingView**

- Reload on 1m chart
- Confirm: Entry, TP, and SL lines appear at correct levels on qualified days
- Confirm: For LONG — entry at range low, TP above, SL below
- Confirm: For SHORT — entry at range high, TP below, SL above
- Confirm: "Long Fill" or "Short Fill" label appears when price touches entry level
- Confirm: "Timeout" label appears when price doesn't reach entry within ~90 bars
- Confirm: TP distance from entry is 2x the SL distance (2:1 R:R)

**Step 5: Commit**

```bash
git add TouchAndTurn.pine
git commit -m "feat: add trade levels, entry detection, and 90-min timeout"
```

---

### Task 5: Trade Exit — TP, SL, Timeout

**Files:**
- Modify: `TouchAndTurn.pine`

**Step 1: Add TP/SL monitoring in IN_TRADE state**

```pine
// ─── Trade Exit Monitoring ────────────────────────────────
bool tpHit = false
bool slHit = false

if state == 3
    if direction == 1  // LONG
        if high >= tpPrice
            state := 4
            tpHit := true
            label.new(bar_index, high, "TP",
                 style=label.style_label_down, color=color.blue, textcolor=color.white, size=size.small)
        else if low <= slPrice
            state := 4
            slHit := true
            label.new(bar_index, low, "SL",
                 style=label.style_label_up, color=color.red, textcolor=color.white, size=size.small)
    else  // SHORT
        if low <= tpPrice
            state := 4
            tpHit := true
            label.new(bar_index, low, "TP",
                 style=label.style_label_up, color=color.blue, textcolor=color.white, size=size.small)
        else if high >= slPrice
            state := 4
            slHit := true
            label.new(bar_index, high, "SL",
                 style=label.style_label_down, color=color.red, textcolor=color.white, size=size.small)
```

**Step 2: Verify in TradingView**

- Reload on 1m chart, scroll through multiple days
- Confirm: "TP" labels appear in blue when price reaches the Fibonacci target
- Confirm: "SL" labels appear in red when price hits the stop loss
- Confirm: no further signals fire after TP or SL for that day
- Confirm: state correctly resets at next day's session open
- Count some wins vs losses — does it roughly match the strategy's expected ~70% win rate?

**Step 3: Commit**

```bash
git add TouchAndTurn.pine
git commit -m "feat: add TP and SL exit monitoring"
```

---

### Task 6: Alerts

**Files:**
- Modify: `TouchAndTurn.pine`

**Step 1: Add alert() calls and alertcondition() entries**

Add `alert()` calls inline where each event fires (qualified, entry fill, TP, SL, timeout). Then add at the bottom of the file:

```pine
// ─── Alerts ──────────────────────────────────────────────
// Inline alert() calls are placed at each event in the logic above.
// alertcondition() entries below for granular alert setup:

alertcondition(state == 2 and state[1] != 2,
     "Qualified Setup", "Touch&Turn: Qualified setup")
alertcondition(entryFilled,
     "Entry Filled", "Touch&Turn: Entry filled")
alertcondition(tpHit,
     "TP Hit", "Touch&Turn: TP hit")
alertcondition(slHit,
     "SL Hit", "Touch&Turn: SL hit")
alertcondition(state == 4 and state[1] == 2,
     "Timeout", "Touch&Turn: Timeout")
```

And the inline alert() messages:

- At qualification: `alert("Touch&Turn: Qualified " + (direction == 1 ? "LONG" : "SHORT") + " setup – " + syminfo.ticker, alert.freq_once_per_bar_close)`
- At entry fill: `alert("Touch&Turn: Entry filled " + (direction == 1 ? "LONG" : "SHORT") + " – " + syminfo.ticker, alert.freq_once_per_bar_close)`
- At TP: `alert("Touch&Turn: TP hit – " + syminfo.ticker, alert.freq_once_per_bar_close)`
- At SL: `alert("Touch&Turn: SL hit – " + syminfo.ticker, alert.freq_once_per_bar_close)`
- At timeout: `alert("Touch&Turn: Timeout – " + syminfo.ticker, alert.freq_once_per_bar_close)`

**Step 2: Verify in TradingView**

- Open alert dialog → Condition: Touch & Turn → "Any alert() function call"
- Confirm all 5 alertcondition entries appear in the dropdown
- No need to actually trigger alerts — visual labels already confirm logic correctness

**Step 3: Commit**

```bash
git add TouchAndTurn.pine
git commit -m "feat: add alerts for all trade events"
```

---

### Task 7: Plot Shapes (Entry Markers)

**Files:**
- Modify: `TouchAndTurn.pine`

**Step 1: Add plotshape markers for entry fills**

```pine
// ─── Plot Shapes ──────────────────────────────────────────
plotshape(entryFilled and direction == 1,
     "Long Entry", shape.triangleup, location.belowbar, color.green, size=size.small, text="Long")
plotshape(entryFilled and direction == -1,
     "Short Entry", shape.triangledown, location.abovebar, color.red, size=size.small, text="Short")
```

**Step 2: Verify in TradingView**

- Confirm green triangles appear below bar on long fills
- Confirm red triangles appear above bar on short fills

**Step 3: Commit**

```bash
git add TouchAndTurn.pine
git commit -m "feat: add plotshape entry markers"
```

---

### Task 8: Documentation

**Files:**
- Create: `TouchAndTurn.md`
- Modify: `README.md`

**Step 1: Write TouchAndTurn.md**

Follow the same structure as `EMAPullback.md`: Strategy Logic, Inputs table, Visuals table, Setup instructions, Alert Messages, Non-Repainting section. Content sourced from the design doc.

**Step 2: Update README.md**

Add a row to the Indicators table:

```markdown
| [Touch & Turn](TouchAndTurn.md) | `TouchAndTurn.pine` | Liquidity candle reversal on 15m opening range (Fibonacci TP) |
```

**Step 3: Verify**

- Read both files, confirm accuracy against implemented code
- Confirm all inputs, visuals, and alerts documented

**Step 4: Commit**

```bash
git add TouchAndTurn.md README.md
git commit -m "docs: add Touch & Turn documentation and update README"
```

---

### Task 9: Final Review & Cleanup

**Files:**
- Review: `TouchAndTurn.pine`

**Step 1: Review full script**

- Read the complete file top to bottom
- Confirm code follows same style as `EMAPullback.pine` (section headers, naming, formatting)
- Remove any debug labels/code left from development
- Confirm `max_lines_count` and `max_labels_count` are sufficient

**Step 2: Verify in TradingView — full walkthrough**

- Load on 1m META chart, scroll through at least 5 trading days
- For each day, confirm:
  - Range box appears (blue or gray)
  - Fibonacci lines appear on qualified days
  - Entry/TP/SL lines at correct levels
  - Fill markers appear when price touches entry
  - TP or SL labels appear at trade exit
  - Timeout label appears when no fill within 90 min
  - No signals after trade completes for that day
  - Clean reset at next day's open

**Step 3: Commit cleanup if needed**

```bash
git add TouchAndTurn.pine
git commit -m "chore: cleanup and final review of Touch & Turn indicator"
```
