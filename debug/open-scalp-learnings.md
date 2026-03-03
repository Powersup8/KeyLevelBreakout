# TSLA Open Scalp — Research Findings

**Date:** 2026-03-03
**Data:** 45 trading days (2025-12-22 to 2026-03-02), 5-second IB candles
**Script:** `debug/open_scalp_analysis.py`
**Full results:** `debug/open-scalp-results.md`

## Strategy

Buy ATM call or put within the first 120 seconds of market open, actively manage with TP/SL, must exit by 9:35:00.

**Entry rule:** Wait 30 seconds. At 9:30:30, compare bar close to 9:30:00 open price.
- Close ≥ open → buy **Call**
- Close < open → buy **Put**

**Assumptions:** Delta 0.50, spread $0.15/contract, 1 contract, 100 multiplier.

## Key Numbers

| Config | Trades | Win% | Avg P&L | Total P&L | Sharpe |
|--------|--------|------|---------|-----------|--------|
| **Puts only** (TP=$2, SL=$1) | **30** | **53%** | **+$17** | **+$515** | **3.6** |
| Both directions (TP=$2, SL=$1) | 44 | 48% | +$8 | +$355 | 1.7 |
| Calls only (TP=$2, SL=$1) | 14 | 36% | -$11 | -$160 | -2.4 |
| Calls only (best: TP=$0.75, SL=$0.25) | 14 | 43% | -$6 | -$85 | -3.8 |

**Per-trade risk:** $50/contract (SL $1.00 × 0.50 delta × 100)

## Findings

### 1. TSLA opens DOWN 64% of days
29 of 45 days, the 9:30:30 close was below the 9:30:00 open. Strong bearish bias at the open in this sample period (Dec 2025 – Mar 2026, TSLA trending $490 → $390).

### 2. Puts have edge, calls don't
Every TP/SL combination tested for calls-only was negative. Puts-only was positive at wider TP/SL settings. The asymmetry is large: puts +$515 vs calls -$160 at the same TP/SL.

### 3. Best entry: wait 30 seconds
Tested: first bar, first up/down bar, consecutive bars, wait 5/10/15/30/60/90/120/180/240/300s, biggest bar, price-cross-open. Winner: `wait_30s` — let the opening chaos settle, then read direction. Sharpe -3.7 (with TP=$0.75/SL=$0.50 baseline) was the least-bad trigger; all triggers were negative at tight TP/SL.

### 4. Wide TP/SL required
Tight stops ($0.25-$0.50) get clipped by TSLA's 5-second noise at the open. The only profitable configs use TP≥$1.50 and SL≥$0.75. Best: TP=$2.00, SL=$1.00 (2:1 R:R).

### 5. Extending exit window to 9:35 adds +$255
Old 120s hard exit: +$100 total. New 9:35 hard exit: +$355 total. Five trades that had the move but needed 130-245 seconds to reach TP now convert from TIME-stop (flat) to TP (winner).

### 6. Trailing stops underperform fixed TP/SL here
Best trailing config: +$17 total (SL=$1.00, trail start=$0.75, offset=$0.40). The open moves fast — a firm take-profit captures more than a trailing mechanism that gives back gains.

### 7. Opportunity ceiling is $4,598 (perfect exit)
With perfect timing within the 9:30-9:35 window: avg MFE $2.39, 80% of days reach ≥$1.00 MFE. Best config captures ~8% of this ceiling. There's theoretical edge, but noise prevents capture.

### 8. No data gaps
5-second data is gap-free at the open — 48 bars per day in 9:30-9:34, every day. Initial analysis had a bug (TIME-stop read end-of-day price instead of last bar within window) that inflated results by ~$492. Fixed.

### 9. Indicator-based exits underperform simple TP/SL
Tested EMA9, EMA20, VWAP cross, reversal bars, momentum stall, and combos (e.g., VWAP+TP$2, EMA9+trail). **None beat the simple TP=$2/SL=$1 baseline** for puts-only:

| Exit Strategy (Puts Only) | Total P&L | Win% | Sharpe |
|---|---|---|---|
| **Baseline TP=$2/SL=$1** | **+$454** | **55%** | **3.1** |
| VWAP or TP$2 + $1 SL | +$287 | 42% | 2.2 |
| 3-bar stall + $1 SL | +$137 | 48% | 1.1 |
| EMA9 or TP$2 + $1 SL | -$242 | 26% | -2.5 |

**Why:** EMA9 on 5-second bars is hyper-reactive — 94% of exits trigger as EMA9 crosses at avg 33s hold time, pulling you out before the TP can be reached. VWAP cross is more patient but still exits profitable trades prematurely. The open is too fast and noisy for indicator-based management — a firm take-profit at $2.00 simply captures more than any reactive mechanism.

**Script:** `debug/open_scalp_exits.py` | **Full results:** `debug/open-scalp-exits.md`

## Caveats / Why This May Not Work Live

1. **Regime-dependent:** TSLA was in a sustained downtrend ($490→$390). The put bias may flip in a bull trend.
2. **Spread underestimated:** Modeled $0.15, real TSLA 0DTE ATM spreads at 9:30 are $0.30-0.50+. Doubling spread to $0.30 cuts total P&L by ~$660 (wipes out all profit).
3. **Slippage:** Fast market at the open, fills may be worse than modeled.
4. **IV crush:** 0DTE options lose IV rapidly in the first minutes — delta-only model doesn't capture this.
5. **Sample size:** 45 days is small. Need 200+ for statistical confidence.
6. **Commission:** $0.65/contract/side = $1.30/round trip = $57 over 44 trades.

## Verdict

**Not tradeable as-is.** The put-direction edge (+$515) is real in-sample but:
- Gets wiped by realistic spread costs ($0.30+)
- Is regime-dependent (bearish TSLA sample)
- Has only 45 data points

If TSLA stays in a downtrend and you can get tight fills, the puts-only variant is marginally interesting. But this is not a reliable daily strategy.
