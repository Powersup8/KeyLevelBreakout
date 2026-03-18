# TSLA Open Scalper — Reference Doc

**Version:** v1.1a | **Chart:** TSLA 1m, Extended Hours ON

## What It Does

An 8-state decision machine for TSLA 0DTE/1DTE options at the open. Guides you from pre-open assessment (9:20) through entry (9:30), ORB formation (9:30–9:35), breakout detection (9:35+), and exit (10 bars after breakout). Every threshold is validated from 280 days of TSLA research (Feb 2025–Mar 2026).

**v1.1 upgrade:** Replaced the fixed-time 5m BAIL (which exited at the worst moment on shakeout days) with ORB-based breakout detection. The indicator now waits for price to tell you the direction instead of checking a clock.

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
| 4 ORB BUILD | 9:31–9:34 | Tracking opening range high/low |
| 5 ORB WATCH | 9:35+ | ORB box drawn (yellow zone), watching for breakout |
| 6 BREAKOUT | when price breaks ORB | Bull (close > ORB high) or Bear (close < ORB low) |
| 7 DONE | after exit/timeout | Lines remain, no new signals |

**SL Hit:** If price touches SL (entry − $2) during states 3–5, an immediate "SL HIT — EXIT" warning fires regardless of ORB state.

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

## ORB Breakout (v1.1 — replaces fixed 5m BAIL)

At 9:35, the 5-minute Opening Range (ORB) is frozen. After 9:35, each bar is checked for close above ORB high or below ORB low.

| Signal | Detection | Label | Research |
|---|---|---|---|
| ORB Bull | close > ORB high | Green "ORB BULL — ADD SIZE" | R01: 70% day above, +$3.98 avg |
| ORB Bull + shakeout | Bull break after shakeout detected | Teal "ORB BULL — SHAKEOUT RECOVERY" | A6: DOWN→DOWN + HOLD = 78.6% win |
| ORB Bear | close < ORB low | Red "ORB BEAR — EXIT" | R01: 29% day above, -$4.36 avg |
| No breakout | neither by 9:55 | Gray "ORB — NO BREAK (timeout)" | Range-bound day |

**5m rule** is still computed at 9:35 and shown as info in the table ("5m: above open ✓/✗"), but no longer triggers action.

**Exit:** 10 bars after bull breakout (optimal for 0DTE options, research: 81.6% win, Sharpe 14.64).

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

## Known Limitations (v1.1)

- **30s fakeout detection not available** — uses 1m bar proxy instead.
- **TSLA-specific thresholds** — dollar values ($2.00 SL, $3.04 chaotic, ORB) are hardcoded for TSLA.
- **ORB breakout on tight range days** — very narrow ORB may trigger false breakouts on noise. Consider adding minimum ORB width filter in v1.2.

## Research Files

- `debug/tsla-open-scalp-findings-2026-03-17.md` — consolidated findings
- `debug/tsla_vix1d_extension.md` — VIX 1d validation (254 days)
- `debug/tsla_pm_spy_qqq.md` — SPY/QQQ PM analysis (234 days)
- `debug/tsla-scalp-research.md` — R01–R14 initial research
- `debug/tsla-scalp-deep.md` — D01–D08 deep research
- `docs/plans/2026-03-18-tsla-open-scalper-design.md` — indicator spec
