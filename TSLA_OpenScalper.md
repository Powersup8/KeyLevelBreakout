# TSLA Open Scalper — Reference Doc

**Version:** v1.0d | **Chart:** TSLA 1m, Extended Hours ON

## What It Does

A 6-state decision machine for TSLA 0DTE/1DTE options at the open. Guides you from pre-open assessment (9:20) through entry (9:30), hold/bail (9:35), and exit (9:40). Every threshold is validated from 280 days of TSLA research (Feb 2025–Mar 2026).

## Setup

1. Open **TSLA** chart, set timeframe to **1 minute**
2. Enable **Extended Trading Hours** (Settings → Symbol → Extended Hours)
3. Add indicator from Pine Editor
4. Optional: create alert on the indicator (one alert covers all 5 signal types)

## State Machine

| State | Time (ET) | What Happens |
|---|---|---|
| 0 SLEEP | before 9:20 | Nothing — chart is clean |
| 1 PRE-SCAN | 9:20–9:29 | PM tracking, confidence scoring, corner table appears |
| 2 OPENING | 9:30 | Entry/SL lines drawn, entry label placed |
| 3 FAKEOUT | 9:30 (bar close) | 1m bar pattern check: fakeout, chaotic, or shakeout |
| 4 5M RULE | 9:35 | HOLD (add size) or BAIL (exit) |
| 5 EXIT | 9:40 | Take profit signal for options |
| 6 DONE | after 9:40 | Overhold warning at 9:45, then quiet |

## Confidence Scoring (5 checks, +1 each)

| # | Check | Pass Condition | Research Source |
|---|---|---|---|
| 1 | PM Position | 9:29 close > Q1 (0.219) in PM range | P3: $5 P&L spread Q1→Q4 |
| 2 | PM Acceleration | 9:25→9:29 move > 0 | P4: strong down = 37% win |
| 3 | VIX Regime | Prev-day close 18–25 | V1: 12% worst, +$2.66 avg |
| 4 | Triple Alignment | TSLA + SPY + QQQ all up 9:20→9:29 | P11d: 80% win, 8% worst |
| 5 | No Danger Combo | NOT (gap < -$2 AND PM flat) | P7: 59% worst-day rate |

### Hard Kills (override score → NO-GO)

| Kill | Condition | Research |
|---|---|---|
| VIX danger | VIX prev-close ≤ 15 | V5: 44% worst-day rate |
| P9 bear | PM pos < 0.219 AND PM accel < 0 | P9: catches 21% worst days |
| Gap trap | Gap < -$2 AND abs(PM trend) < 0.48 | P7: 59% worst-day rate |

### Tier Mapping

| Score | Tier | Action |
|---|---|---|
| 5 | HIGH | Enter small at 9:30, full size at 9:35 if HOLD |
| 3–4 | MED | Enter small at 9:30, tight SL |
| 2 | LOW | Watch only, wait for 9:35 confirmation |
| 0–1 / hard kill | NO-GO | Skip the day |

## Fakeout Detection (1m bar proxy)

Since 30s `request.security_lower_tf` is not available, uses the 9:30 1m bar's OHLC:

| Signal | Detection | Action |
|---|---|---|
| FAKEOUT | Red bar + upper wick > body | EXIT label (red) |
| CHAOTIC | Bar range > $3.04 | Warning label (orange) |
| Shakeout | Red bar, no wick rejection | Watch label — if BAIL fires, shows "MAY RECOVER" (orange) |

## 5-Minute Rule

At 9:35: compare close to 9:30 open.

| Result | Label | Research |
|---|---|---|
| HOLD (close > open) | Green "HOLD — ADD SIZE" | 66.7% win, +$3.10 avg (280 days) |
| BAIL (close ≤ open) | Red "BAIL — EXIT ALL" | 32% win, -$3.30 avg |
| BAIL + shakeout | Orange "BAIL — SHAKEOUT, MAY RECOVER" | DOWN→DOWN + HOLD = 78.6% win |
| HOLD + prior fakeout | Teal "RECOVERY HOLD" | Shakeout reversal confirmed |

## Visual Elements

| Element | Color | When |
|---|---|---|
| Entry line | Cyan (#00BFFF), width 3 | 9:30, extends 20 bars |
| SL line | Bright red (#FF4444), width 3 | 9:30, at entry − $2.00 |
| Exit marker | Green vertical line | 9:40 |
| Background | Green (GO), Red (BAIL/NO-GO), Orange (exit/overhold) | 9:20–9:45 |
| Corner table | Top-right | 9:20–9:45, shows state/tier/VIX/PM/entry |

## Inputs

| Input | Default | Description |
|---|---|---|
| VIX Symbol | CBOE:VIX | VIX data provider. Try TVC:VIX if unavailable |
| Stop Loss Distance | $2.00 | SL below entry. Research: median max dip = $2.08 |
| Show Info Table | true | Corner table visibility |
| Show Background Colors | true | Bgcolor bands visibility |

## Alerts

One alert covers all signals (uses `alert()` with dynamic messages):

| Signal | Fires At | Message Example |
|---|---|---|
| GO | 9:29 | "TSLA GO: confidence HIGH (5/5) — enter small at open" |
| NO-GO | 9:29 | "TSLA NO-GO: P9 bear — skip today" |
| FAKEOUT | 9:30 | "TSLA FAKEOUT — EXIT NOW" |
| HOLD | 9:35 | "TSLA HOLD — ADD SIZE (confidence: MED)" |
| BAIL | 9:35 | "TSLA BAIL — EXIT ALL" |

## External Data (3 request.security calls)

| # | Symbol | Timeframe | Purpose |
|---|---|---|---|
| 1 | VIX (configurable) | Daily | Prev-day close for regime |
| 2 | SPY | 1m | PM late trend (9:20→9:29) |
| 3 | QQQ | 1m | PM late trend (9:20→9:29) |

## Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| No labels at 9:29 | Extended Hours OFF | Enable in chart settings |
| VIX shows N/A | Wrong VIX symbol | Change input to TVC:VIX |
| No entry lines | Tier was LOW or NO-GO | Check confidence score in table |
| Labels at wrong time | Timezone mismatch | Chart must use ET (UTC-4/5) |

## Known Limitations (v1.0)

- **Fixed-time BAIL at 9:35 can exit at the worst moment** — shakeout days may recover after BAIL. The orange "MAY RECOVER" label mitigates but doesn't solve this. v1.1 will add ORB-based signals.
- **30s fakeout detection not available** — uses 1m bar proxy instead.
- **TSLA-specific thresholds** — dollar values ($2.00 SL, $3.04 chaotic) are hardcoded for TSLA.

## Research Files

- `debug/tsla-open-scalp-findings-2026-03-17.md` — consolidated findings
- `debug/tsla_vix1d_extension.md` — VIX 1d validation (254 days)
- `debug/tsla_pm_spy_qqq.md` — SPY/QQQ PM analysis (234 days)
- `debug/tsla-scalp-research.md` — R01–R14 initial research
- `debug/tsla-scalp-deep.md` — D01–D08 deep research
- `docs/plans/2026-03-18-tsla-open-scalper-design.md` — indicator spec
