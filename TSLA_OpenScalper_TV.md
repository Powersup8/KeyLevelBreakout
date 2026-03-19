# TSLA Open Scalper

**0DTE/1DTE opening trade decision system for TSLA.**

Guides you through 6 decision points in 25 minutes (9:20–9:55 ET) using a state machine backed by 280 days of TSLA-specific research. Pre-open assessment scores confidence from premarket structure, VIX regime, and SPY/QQQ alignment. Real 30s sub-bar fakeout detection at the open. ORB-based breakout with dynamic SL. Dual exit system: 3-bar for 0DTE, 20-bar for runners.

## Key Signals

- **Pre-Open Score (9:29):** 5-check confidence tier (HIGH/MED/LOW/NO-GO) with 4 hard-kill overrides (VIX, P9 bear, gap trap, low PM volume)
- **Fakeout Detection (9:30):** Real 30s sub-bars — only fires on true traps (bar2 breaks bar1 low: 27% win, 64% worst)
- **ORB Breakout (9:35+):** Bull (close > ORB high) or Bear (close < ORB low). SL = ORB low.
- **Primary Exit (3 bars):** 93% bull win, Sharpe 2.96 — optimal for 0DTE options
- **Runner Exit (20 bars):** 75% bull win, $4.44 avg — for 1-2DTE runners

## Research-Backed Thresholds

| Signal | Win Rate | Sample |
|---|---|---|
| ORB Bull → 3-bar exit | 93.0% | 57 bull trades |
| VIX 18–25 × HOLD | 76.7% | 254 days |
| Triple PM UP × HOLD | 80.0% | 234 days |
| Shakeout recovery | 78.6% | 137 days |

## Setup

1. TSLA 1-minute chart
2. **Extended Trading Hours ON** (required for premarket data)
3. One alert covers all signals (GO, NO-GO, breakout, SL hit, exits)

## Visuals

- Corner table (top-right): state, tier, VIX, PM metrics, exit countdown
- Entry line (cyan) at 9:30, SL line (red) at ORB freeze (9:34)
- ORB zone (yellow dashed + fill) from 9:34
- Primary exit (green) + runner exit (teal) labels after bull breakout
- Background color bands: green=GO, yellow=ORB, red=bear/exit

## Data

8 request.security calls: VIX daily, SPY 1m, QQQ 1m, TSLA 15s (P9 kill), TSLA 30s × 4 (fakeout OHLC).

TSLA-specific hardcoded thresholds. v2 will add ATR-normalized inputs for other tickers.
