# TSLA Open Scalper — Reference Doc

**Version:** v1.3 | **Chart:** TSLA 1m, Extended Hours ON

## What It Does

An 8-state decision machine for TSLA 0DTE/1DTE options at the open. Guides you from pre-open assessment (9:20) through entry (9:30), ORB formation (9:30–9:35), breakout detection (9:35+), and dual exit (3-bar take-profit + 20-bar runner). Every threshold is validated from 280 days of TSLA research (Feb 2025–Mar 2026).

## Version History

- **v1.3:** Remove fallback SL (ORB low only), hold=3 default with dual exit labels, PM vol kill=7000
- **v1.2c:** Real 30s fakeout detection (15s/30s sub-bars), ORB-based dynamic SL, min ORB width filter
- **v1.1:** Replaced fixed-time 5m BAIL with ORB-based breakout detection
- **v1.0:** Initial state machine with pre-open scoring

## Setup

1. Open **TSLA** chart, set timeframe to **1 minute**
2. Enable **Extended Trading Hours** (Settings → Symbol → Extended Hours)
3. Add indicator from Pine Editor
4. Optional: create alert on the indicator (one alert covers all signal types)

## State Machine

| State | Time (ET) | What Happens |
|---|---|---|
| 0 SLEEP | before 9:20 | Nothing — chart is clean |
| 1 PRE-SCAN | 9:20–9:29 | PM tracking, confidence scoring, corner table appears |
| 2 OPENING | 9:30 | Entry line drawn, entry label placed |
| 3 FAKEOUT | 9:30 (bar close) | 30s sub-bar pattern check: fakeout, chaotic, or shakeout |
| 4 ORB BUILD | 9:31–9:33 | Tracking opening range high/low, no SL active |
| 5 ORB WATCH | 9:34+ | ORB frozen, SL = ORB low, watching for breakout |
| 6 BREAKOUT | when price breaks ORB | Bull or Bear, dual exit timer starts |
| 7 DONE | after runner exit/timeout | Lines remain, no new signals |

## Stop Loss Architecture (v1.3)

| Phase | Time | SL |
|---|---|---|
| ORB Build | 9:30–9:34 | **None** (fallback disabled by default). Research: removing the $1.50 fallback triples total PnL ($96 vs $32), Sharpe 2.48 vs 1.21. The 66 trades it stopped included 22 winners (+$71 missed). |
| ORB Watch | 9:35+ | **ORB low** (dynamic). ORB low kills 54 losers at -$2.77 avg while letting 47 winners through at +$4.13 avg. Net SL value: $175 vs $9 for fixed $2. |
| ORB Freeze Bar | 9:34 | **Skipped** — if this bar sets the ORB low, checking `low <= orb_low` would self-trigger. |

Optional: set Fallback SL > 0 to re-enable pre-ORB protection (e.g., $3.00 for conservative).

## Dual Exit System (v1.3)

After bull breakout, two exit labels fire at different times:

| Exit | Default | Label | Color | Research |
|---|---|---|---|---|
| **Primary (0DTE)** | 3 bars | "EXIT 3b — $X.XX" | Green, large | 93% bull win, $3.77 avg, Sharpe 2.96 |
| **Runner (1-2DTE)** | 20 bars | "RUNNER 20b — $X.XX" | Teal, normal | 75% bull win, $4.44 avg, captures 57%→100% of move |

**When to use which:**
- **0DTE:** Take the 3-bar exit. Gamma makes early moves most valuable, reversal risk is amplified ($0.24 extra cost per $2 reversal).
- **1-2DTE:** Consider holding to the runner exit. Theta pressure is low ($0.08 vs $0.30/hr), the extra $0.67 avg PnL translates to real option value with less gamma asymmetry.

Both labels always appear. The state machine transitions to DONE after the runner bar.

## Confidence Scoring (5 checks, +1 each)

| # | Check | Pass Condition | Research Source |
|---|---|---|---|
| 1 | PM Position | 9:29 close > Q1 (0.219) in PM range | P3: $5 P&L spread Q1→Q4 |
| 2 | PM Acceleration | 2m window (9:27→9:29) > 0 | 15s research: 2m beats 4m, +3pp win, Sharpe 8→11 |
| 3 | VIX Regime | Prev-day close 18–25 | V1: 12% worst, +$2.66 avg (254 days) |
| 4 | Triple Alignment | TSLA + SPY + QQQ all up 9:20→9:29 | P11d: 80% win, 8% worst |
| 5 | No Danger Combo | NOT (gap < -$2 AND PM flat) | P7: 59% worst-day rate |

### Hard Kills (override score → NO-GO)

| Kill | Condition | Research |
|---|---|---|
| VIX danger | VIX prev-close ≤ 15 | V5: 44% worst-day rate |
| P9 bear | PM pos < 0.219 AND last 30s fading (15s sub-bars) | P9: catches 21% worst days |
| Gap trap | Gap < -$2 AND abs(PM trend) < 0.48 | P7: 59% worst-day rate |
| Low PM volume | TV PM vol (9:25–9:29) < 7,000 | TV vol ≈ 8× lower than IB: 7k TV ≈ 53k IB (Q1 kill) |

### Tier Mapping

| Score | Tier | Action |
|---|---|---|
| 5 | HIGH | Enter small at 9:30, full size at breakout |
| 3–4 | MED | Enter small at 9:30, standard size at breakout |
| 2 | LOW | Watch only, wait for breakout confirmation |
| 0–1 / hard kill | NO-GO | Skip the day |

## Fakeout Detection (v1.2c — real 30s sub-bars)

Uses `request.security_lower_tf("30S")` on the 9:30 bar for real A6 pattern detection:

| Signal | Detection | Action |
|---|---|---|
| FAKEOUT | 30s bar1 UP → bar2 DOWN AND bar2 low < bar1 low | Orange "FAKEOUT — watch ORB" (warning, not exit) |
| CHAOTIC | bar1 range > $3.04 | Orange warning |
| Shakeout | bar1 DOWN → bar2 DOWN, range ≤ $3.04 | Dip buy entry (bar low + 15%), if HOLD later = 78.6% win |

**Key v1.2c change:** Fakeout only fires if bar2 breaks bar1's low (real trap: 27% win, 64% worst). A simple UP→DOWN without new low is a normal pullback (48% win) — not a fakeout.

Falls back to 1m bar proxy (wick analysis) if 30s data unavailable.

## ORB Breakout

At 9:34, the 5-minute Opening Range (ORB) is frozen. After 9:35, each bar is checked for close above ORB high or below ORB low.

| Signal | Detection | Label | Research |
|---|---|---|---|
| ORB Bull | close > ORB high | Green "ORB BULL — ADD SIZE" | 93% win at 3-bar exit |
| ORB Bull + shakeout | Bull break after shakeout | Teal "ORB BULL — SHAKEOUT RECOVERY" | A6: DOWN→DOWN + HOLD = 78.6% win |
| ORB Bear | close < ORB low | Red "ORB BEAR — EXIT" | Immediate exit signal |
| No breakout | neither by 9:55 | Gray "ORB — NO BREAK (timeout)" | Range-bound day |

**Min ORB width filter:** Skip breakout if ORB range < $1.00 (configurable). All TSLA ORBs in backtesting were wider than $2.50, so this is a safety net.

## Inputs

| Input | Default | Description |
|---|---|---|
| VIX Symbol | CBOE:VIX | VIX data provider. Try TVC:VIX if unavailable |
| Hold Bars (0DTE) | 3 | Primary exit N bars after bull breakout |
| Runner Bars (1-2DTE) | 20 | Secondary exit label for runners |
| Fallback SL ($) | 0 (disabled) | Pre-ORB SL. Set > 0 to enable (e.g., 3.00 for conservative) |
| Min ORB Width ($) | 1.00 | Skip breakout if ORB range < this |
| Dip Entry Recovery (%) | 15.0 | On shakeout: enter at bar low + X% of range |
| PM Vol Min Kill | 7,000 | Hard kill if TV PM volume < this. Set 0 to disable |
| Show Info Table | true | Corner table visibility |
| Show Background Colors | true | Bgcolor bands visibility |
| Log Signals | false | Pine Logs debug output |

## Visual Elements

| Element | Color | When |
|---|---|---|
| Entry line | Cyan (#00BFFF), width 3 | 9:30, extends 25 bars |
| SL line | Bright red (#FF4444), width 3 | 9:34 (ORB freeze), at ORB low |
| ORB zone | Yellow dashed + fill | 9:34, ORB high to ORB low |
| Primary exit | Green label (large) | 3 bars after bull breakout |
| Runner exit | Teal label (normal) | 20 bars after bull breakout |
| Background | Green/Yellow/Red per state | 9:20–9:55 active window |
| Corner table | Top-right | RTH, shows state/tier/VIX/PM/entry/countdown |

## Alerts

One alert covers all signals (uses `alert()` with dynamic messages):

| Signal | Fires At | Message Example |
|---|---|---|
| GO | 9:29 | "TSLA GO: confidence HIGH (5/5) — enter small at open" |
| NO-GO | 9:29 | "TSLA NO-GO: P9 bear — skip today" |
| ORB Bull | breakout bar | "TSLA ORB BULL BREAK at 405.50 — ADD SIZE" |
| ORB Bear | breakout bar | "TSLA ORB BEAR BREAK at 398.20 — EXIT" |
| SL Hit | any bar 9:35+ | "TSLA SL HIT at 399.06 — EXIT NOW" |
| Primary Exit | 3 bars after breakout | "TSLA EXIT — 3 bars after bull breakout — TAKE PROFIT $3.80" |
| Runner Exit | 20 bars after breakout | "TSLA RUNNER EXIT — 20 bars — $4.50" |

## External Data (8 request.security calls)

| # | Symbol | Timeframe | Purpose |
|---|---|---|---|
| 1 | VIX (configurable) | Daily | Prev-day close for regime |
| 2 | SPY | 1m | PM late trend (9:20→9:29) |
| 3 | QQQ | 1m | PM late trend (9:20→9:29) |
| 4 | TSLA | 15S | P9 hard kill (last 30s of 9:29 bar) |
| 5-8 | TSLA | 30S × 4 | Fakeout detection (OHLC of 30s sub-bars) |

## Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| No labels at 9:29 | Extended Hours OFF | Enable in chart settings |
| VIX shows N/A | Wrong VIX symbol | Change input to TVC:VIX |
| No entry lines | Tier was LOW or NO-GO | Check confidence score in table |
| No SL line before 9:34 | Fallback SL disabled (default) | Normal — SL activates at ORB freeze |
| 15s/30s sub-bars missing | Plan doesn't support lower TF | Falls back to 1m proxy. Works on Premium. |

## Known Limitations (v1.3)

- **TSLA-specific thresholds** — dollar values ($3.04 chaotic, ORB width, PM vol kill) are calibrated for TSLA ~$400.
- **No SL during ORB build** (9:30–9:33) — by design. Flash crash during these 4 bars = unprotected. The data shows this is a net positive tradeoff.
- **TV volume ≠ IB volume** — PM vol kill threshold (7,000) is calibrated from 21 overlapping days. Will improve with more data.
- **Runner identification not yet implemented** — both exit labels always fire. Future: score at breakout time to recommend hold=3 vs hold=20.

## Research Files

- `debug/tsla-open-scalp-findings-2026-03-17.md` — consolidated findings (280 days)
- `debug/tsla-pm-15s-findings.md` — 15s PM research (251 days)
- `debug/tsla-fakeout-deep-research.md` — fakeout pattern analysis (137 days)
- `debug/tsla-scalp-optimization-report.md` — 61-experiment optimization sweep
- `debug/tsla-hold-time-findings.md` — hold time analysis (P2)
- `debug/tsla-tv-volume-calibration.md` — TV/IB volume ratio (P3)
- `debug/tsla_vix1d_extension.md` — VIX 1d validation (254 days)
- `debug/tsla_pm_spy_qqq.md` — SPY/QQQ PM analysis (234 days)
- `docs/plans/2026-03-19-session-handover.md` — session handover
