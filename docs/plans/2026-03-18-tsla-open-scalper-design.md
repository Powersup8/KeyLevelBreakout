# TSLA Open Scalper — Indicator Design Spec

*Created: 2026-03-18 | Status: Approved*

## Overview

A standalone TradingView Pine Script v6 indicator for TSLA 0DTE/1DTE options trading at the open. Runs on a **1m chart with Extended Hours enabled**. Walks the trader through a 6-state decision machine from 9:20 to 9:45, showing exactly when to enter, add, bail, or take profit.

All thresholds are validated from TSLA-specific research (280 days, Feb 2025–Mar 2026). TSLA-hardcoded in v1, configurable inputs planned for v2.

## Research Foundation

Every rule in this indicator maps to validated findings:

| Signal | Source | Sample | Key Stat |
|---|---|---|---|
| 5m rule (core) | tsla-open-scalp-findings | 280 days | HOLD 66.7% win, +$3.10 avg |
| 10m exit for options | same | 280 days | 81.6% win, Sharpe 14.64 |
| PM position at 9:29 | P3 (tsla_open_research_v2) | 234 days | $5 P&L spread Q1→Q4 |
| PM acceleration 9:25–9:29 | P4 | 234 days | Strong down = 37% win |
| PM bear composite (P9) | P9 | 234 days | Catches 21% worst days, 16% false exclude |
| Gap down + PM flat | P7 | 234 days | 59% worst-day rate |
| VIX regime (1d prev-close) | V1 (tsla_vix1d_extension) | 254 days | Moderate 18–25 = 12% worst, +$2.66 avg |
| VIX ≤ 15 danger | V5 | 254 days | 44% worst-day rate |
| VIX moderate × HOLD | V3 | 254 days | 76.7% win, +$5.09 avg |
| Triple PM alignment × HOLD | P11d (tsla_pm_spy_qqq) | 234 days | 80% win, 8% worst |
| 30s fakeout (UP→DOWN) | A6 (tsla_module_s_v2) | 129 days | 31% win on BAIL, 56% worst |
| 30s bar1 range > $3.04 | A3 | 129 days | Chaotic, 44% win, -$3.88 avg |
| DOWN→DOWN + HOLD | A6 | 129 days | 78.6% win (shakeout reversal) |
| SL ~$2 on HOLD days | R11 | 280 days | Median max dip = $2.08 |

## Technical Architecture

### Chart Setup
- Symbol: TSLA
- Timeframe: 1 minute
- Extended Hours: ON (required for premarket bars)

### request.security Budget (7 of 40)

| # | Call | Data | Purpose |
|---|---|---|---|
| 1–4 | `request.security_lower_tf(syminfo.tickerid, "30S", open/high/low/close)` ×4 | TSLA 30s OHLC (each returns float[] array) | Fakeout pattern detection. 4 separate calls needed (no tuple destructuring). Requires Premium+ plan. |
| 2 | `request.security("CBOE:VIX", "D", close[1], lookahead=barmerge.lookahead_on)` | VIX prev-day close | Regime tier |
| 3 | `request.security("SPY", "1", close)` | SPY 1m close | SPY PM late trend (track 9:20→9:29) |
| 4 | `request.security("QQQ", "1", close)` | QQQ 1m close | QQQ PM late trend (track 9:20→9:29) |

### Native Computations (0 calls, from chart bars)
- TSLA PM high / low / range (4:00–9:29, tracked bar-by-bar, frozen at 9:30)
- TSLA PM position at 9:29: `(close_929 - pm_low) / pm_range`
- TSLA PM acceleration: `close_929 - open_925`
- TSLA PM late trend: `close_929 - open_920`
- 5m rule: `close_935 > open_930`
- Gap: `open_930 - prev_day_close`
- Previous day close: stored from prior session's last RTH bar

### State Variables
```
// ── State machine ──
var int   state         = 0    // 0=SLEEP, 1=PRE-SCAN, 2=OPENING, 3=FAKEOUT, 4=5M_RULE, 5=EXIT, 6=DONE
var int   confidence    = 0    // 0-5 score
var bool  hard_kill     = false
var bool  fakeout_fired = false

// ── Premarket tracking ──
var float pm_high       = na
var float pm_low        = na
var float pm_position   = na   // 0.0–1.0, where 9:29 close sits in PM range
var float pm_accel      = na   // close_929 - open_925
var float pm_late_trend = na   // close_929 - open_920
var float close_929     = na
var float open_925      = na
var float open_920      = na   // TSLA 9:20 open for late trend

// ── Cross-symbol PM tracking ──
var float spy_920       = na   // SPY 1m close at 9:20 bar
var float qqq_920       = na   // QQQ 1m close at 9:20 bar
var float spy_929       = na   // SPY 1m close at 9:29 bar
var float qqq_929       = na   // QQQ 1m close at 9:29 bar

// ── Session / entry ──
var float prev_day_close = na  // prior RTH session last close (for gap calc)
var float gap            = na  // open_930 - prev_day_close
var float open_930       = na  // entry price
var float close_935      = na
```

## State Machine Detail

### STATE 0: SLEEP (before 9:20)
- No visuals, no computation
- Reset all state variables at session start (new trading day)

### STATE 1: PRE-SCAN (9:20–9:29)
- Corner table appears (top-right)
- Track PM high/low/range bar-by-bar
- At 9:20: store TSLA/SPY/QQQ 1m opens for late-trend calculation
- At 9:29 (final PM bar): compute all pre-open checks

**Confidence score (5 binary checks, +1 each):**

| Check | Pass condition | Fail = |
|---|---|---|
| PM Position | `pm_position_929 > 0.219` | Near PM low |
| PM Acceleration | `close_929 - open_925 > 0` | Decelerating into open |
| VIX Regime | `18 <= vix_prev_close <= 25` | Outside sweet spot (15–18 = neutral, no point/no kill) |
| Triple PM Align | TSLA + SPY + QQQ all trending up 9:20→9:29 | No broad alignment |
| No Danger Combo | NOT (gap < -$2 AND pm_late_trend flat) | Gap trap |

**Hard kills (override score → NO-GO):**
- `vix_prev_close <= 15` — 44% worst-day rate
- `pm_position_929 < 0.219 AND pm_accel < 0` — P9 bear composite
- `gap < -2 AND abs(pm_late_trend) < 0.48` — gap down + PM flat

**Tier mapping:**

| Score | Tier | Color | Action |
|---|---|---|---|
| 5 | HIGH | Bright green | Enter small at 9:30 |
| 3–4 | MED | Dim green | Enter small at 9:30, tight SL |
| 2 | LOW | Gray | Wait for 9:35 only |
| 0–1 or hard kill | NO-GO | Dim red | Skip entirely |

### STATE 2: OPENING (9:30:00)
- Store `open_930` = bar open price
- If tier >= MED: draw entry line + SL line
- SL = `open_930 - 2.00` (hardcoded TSLA value)
- Entry label below bar: "ENTERED (small)" or "WATCHING" depending on tier
- Lines: solid, width=2, extend 20 bars (to ~9:50)

### STATE 3: FAKEOUT CHECK (9:30:30–9:31:00)
- Uses 30s OHLC from `request.security_lower_tf` (returns array of 2 sub-bars per 1m bar)
- Evaluate on the 1m bar that closes at 9:31 (contains bar1=9:30:00 and bar2=9:30:30)
- **Latency note:** Pine evaluates at bar close, so fakeout detection fires at 9:31:00 — 30s after the fakeout pattern completes. This is inherent to Pine's execution model. The alert is still valuable (confirms what you may have seen live), but is not a real-time trigger.
- **Fallback (no 30s data):** If `request.security_lower_tf` returns empty array (plan limitation), skip STATE 3 entirely and show "30s unavailable" in table. All other states still function.

| Pattern | Detection | Action |
|---|---|---|
| bar1 UP → bar2 DOWN | 30s bar1 close > open, bar2 close < open | Label above bar: "EXIT — FAKEOUT" (size.large, red) |
| bar1 range > $3.04 | 30s bar1 high - low > 3.04 | Table updates: "CHAOTIC" warning |
| DOWN → DOWN | both bars close < open | Table note: "shakeout — watch for HOLD" |

If FAKEOUT fires → set `fakeout_fired = true`, bright red bgcolor flash.

### STATE 4: 5M RULE (9:35:00)
- On the 1m bar closing at 9:35: `close_935 = close`
- Compare to `open_930`

| Result | Label | Color | Action |
|---|---|---|---|
| HOLD (`close_935 > open_930`) | "HOLD — ADD SIZE" (size.large) | Green bgcolor | Add to position |
| BAIL (`close_935 <= open_930`) | "BAIL — EXIT ALL" (size.large) | Red bgcolor | Exit everything |

If `fakeout_fired` was true but HOLD fires → special label: "RECOVERY HOLD" (still valid, DOWN→DOWN + HOLD = 78.6% win).

### STATE 5: EXIT WINDOW (9:40:00)
- Label above bar: "EXIT — TAKE PROFIT" (green, size.large)
- Vertical green line at 9:40 bar
- Table updates countdown in bars from STATE 4 onward

### STATE 6: DONE (after 9:40)
- 9:40–9:45: amber bgcolor (8%) — "you should have exited" visual reminder
- Table shows countdown: "OVERHOLD: X bars past exit"
- At 9:45: amber label "OVERHOLD — CLOSE" if no earlier exit
- After 9:45: bgcolor returns to transparent, all lines/labels remain for post-analysis
- No more signals until next trading day

## Visual Design

### Corner Table (table.new, top-right)

4 rows, 2 columns. Updates at each state transition.

**Pre-scan (9:20–9:29):**
```
┌──────────────────────────────┐
│ TSLA OPEN SCALP       v1.0  │
│ State: PRE-SCAN → HIGH       │
│ VIX: 21.3 (moderate ✓)      │
│ PM: pos=0.72 acc=+0.8 ✓✓    │
│ Align: TSLA↑ SPY↑ QQQ↑ ✓    │
└──────────────────────────────┘
```

**After 9:35 HOLD:**
```
┌──────────────────────────────┐
│ TSLA OPEN SCALP       v1.0  │
│ ▶ HOLD — ADD SIZE            │
│ Entry: $401.20  SL: $399.20  │
│ Exit target: 9:40 (5 bars)   │
└──────────────────────────────┘
```

### Background Colors
Subtle bgcolor bands during active window only (9:20–9:45):

| State | Color | Opacity |
|---|---|---|
| PRE-SCAN computing | Gray | 5% |
| GO (score 3+) | Green | 8% |
| NO-GO | Red | 8% |
| FAKEOUT EXIT | Red | 15% (flash) |
| HOLD confirmed | Green | 10% |
| BAIL confirmed | Red | 12% |
| EXIT window | Amber | 8% |
| After 9:45 | Transparent | 0% |

### Chart Lines

| Line | Style | Color | Width | Extent |
|---|---|---|---|---|
| Entry price | Solid horizontal | Blue | 2 | 9:30 → 9:50 (20 bars) |
| Stop-loss | Solid horizontal | Red | 2 | 9:30 → 9:50 (20 bars) |
| 9:40 exit marker | Solid vertical | Green | 1 | Full visible price range |

### Labels (no overlaps)

| Time | Position | Size | Content |
|---|---|---|---|
| 9:29 | Below bar | normal | Confidence tier + score |
| 9:30 | Below bar | normal | "ENTERED" or "WATCHING" |
| 9:31 | Above bar | large (if triggered) | "EXIT — FAKEOUT" |
| 9:35 | Below bar | large | "HOLD — ADD" or "BAIL — EXIT ALL" |
| 9:40 | Above bar | large | "EXIT — TAKE PROFIT" |

Labels alternate above/below bars, and are spaced 4–5 bars apart. No overlap possible.

## Alerts

Use `alert()` (not `alertcondition()`) — allows dynamic messages with `str.format()` at runtime.

| ID | Fires at | Condition | Example Message |
|---|---|---|---|
| `pre_open_go` | 9:29 | confidence >= 3 AND no hard kill | "TSLA GO: confidence HIGH (5/5) — enter small at open" |
| `pre_open_nogo` | 9:29 | confidence < 2 OR hard kill | "TSLA NO-GO: P9 bear composite — skip today" |
| `fakeout_exit` | 9:31 | bar1 UP → bar2 DOWN detected | "TSLA FAKEOUT — EXIT NOW" |
| `hold_add` | 9:35 | close_935 > open_930 | "TSLA HOLD — ADD SIZE (confidence: HIGH)" |
| `bail_exit` | 9:35 | close_935 <= open_930 | "TSLA BAIL — EXIT ALL" |

Note: `alert()` fires programmatically per bar. User creates ONE generic alert on the indicator; all 5 conditions fire through it with dynamic messages.

## File Structure & Versioning

- `TSLA_OpenScalper.pine` — the indicator (single file, version in line 2 header comment)
- `TSLA_OpenScalper.md` — reference doc (inputs, rules, setup instructions)
- `TSLA_OpenScalper_TV.md` — TradingView publish description

**Versioning scheme:** Major updates increment minor number (v1.0 → v1.1 → v1.2). Minor changes/fixes get a letter suffix (v1.1 → v1.1a → v1.1b). Major rewrites increment major number (v1.x → v2.0). Every code change bumps the version.

## Future (v2+)

- Configurable thresholds via input fields (generalize beyond TSLA)
- ATR-normalized dollar values for multi-ticker support
- Put signal (BAIL → enter puts, research R14: 62% win, +$2.46 avg)
- 15s premarket data integration when collection reaches 60+ days
- Options P&L estimation panel (delta × stock move approximation)

## Constraints & Assumptions

- Extended Hours MUST be enabled — indicator logs a warning label if PM bars are missing
- TSLA-specific: all dollar thresholds ($2.00 SL, $3.04 bar range, $2 gap) are hardcoded
- 30s data requires `request.security_lower_tf` (not `request.security`) and TradingView Premium+ plan. Fallback: skip fakeout detection, all other states still function.
- VIX symbol may vary by data provider (CBOE:VIX vs TVC:VIX) — make configurable input
- Indicator is overlay=true — shares the price chart pane
- Half-days (early close 1:00 PM): 9:20–9:45 window is unaffected, but `prev_day_close` must use last RTH bar of prior session regardless of close time. Reset logic should key off session boundary, not 16:00 specifically.
- Delayed opens / circuit breakers: if 9:30 bar is missing, state machine stays in SLEEP. Add guard: only transition to OPENING if a valid 9:30 bar exists.
- Fakeout detection has ~30s latency (Pine evaluates at 1m bar close). This is documented, not a bug — the alert confirms what the trader may have already noticed.
