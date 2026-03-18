# TSLA Open Scalper

**0DTE/1DTE opening trade decision system for TSLA.**

Guides you through 5 decision points in 10 minutes (9:30–9:40 ET) using a state machine backed by 280 days of TSLA-specific research. Pre-open assessment scores confidence from premarket structure, VIX regime, and SPY/QQQ alignment. At the open, detects fakeout and shakeout patterns. At 9:35, fires the core HOLD/BAIL signal. At 9:40, signals exit for options.

## Key Signals

- **Pre-Open Score (9:29):** 5-check confidence tier (HIGH/MED/LOW/NO-GO) with 3 hard-kill overrides
- **Fakeout Detection (9:30):** Red bar with wick rejection → immediate exit warning
- **5-Minute Rule (9:35):** HOLD (66.7% win, 280 days) or BAIL. Shakeout pattern shows "MAY RECOVER" instead of hard exit
- **Exit Window (9:40):** 10m hold = optimal for 0DTE (81.6% win, Sharpe 14.64)

## Research-Backed Thresholds

| Signal | Win Rate | Sample |
|---|---|---|
| 5m HOLD | 66.7% | 280 days |
| VIX 18–25 × HOLD | 76.7% | 254 days |
| Triple PM UP × HOLD | 80.0% | 234 days |
| 10m exit (options) | 81.6% | 280 days |

## Setup

1. TSLA 1-minute chart
2. **Extended Trading Hours ON** (required for premarket data)
3. One alert covers all signals (GO, NO-GO, FAKEOUT, HOLD, BAIL)

## Visuals

- Corner table (top-right): state, tier, VIX, PM metrics
- Entry line (cyan) + SL line (red) at 9:30
- Background color bands: green=GO, red=BAIL, orange=exit window
- Labels at each decision point (no overlap)

## Data

3 request.security calls: VIX daily, SPY 1m, QQQ 1m.

TSLA-specific hardcoded thresholds. v2 will add configurable inputs for other tickers.
