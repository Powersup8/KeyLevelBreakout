# P2: Hold Time Optimization — Findings

**Date:** 2026-03-19
**Script:** `debug/tsla_hold_time_analysis.py`
**Method:** Backtest with `sl_fallback=999` (no fallback SL) to isolate pure hold-time effect

## Key Finding: The Fallback SL Dominates Everything

With the standard SL=1.50, **54 of 122 trades (44%) hit ORB_SL before the hold timer even matters**. The fallback SL masks the real hold-time effect. Removing it reveals:

| Hold | Win% | Avg PnL | Score | Sharpe |
|------|------|---------|-------|--------|
| 3    | 50.8 | $0.80   | 99.3  | 2.96   |
| 5    | 49.2 | $0.61   | 73.4  | 2.26   |
| 8    | 47.5 | $0.68   | 78.7  | 2.47   |
| 10   | 45.1 | $0.79   | 87.0  | 2.48   |
| 15   | 41.8 | $0.95   | 96.7  | 2.71   |
| 20   | 42.6 | $1.11   | 115.7 | 2.49   |

Without the SL noise floor, **longer hold = higher avg P&L but lower win rate**. The tradeoff is real.

## Bull Breakout Deep Dive (57 trades, no SL)

Bar-by-bar decay curve for bull breakout trades only:

| Hold | Win% | Avg PnL | Median PnL |
|------|------|---------|------------|
| 1    | 96.5 | $3.99   | $3.64      |
| 2    | 93.0 | $3.93   | $3.75      |
| 3    | 93.0 | $3.77   | $3.80      |
| 5    | 89.5 | $3.37   | $2.92      |
| 8    | 86.0 | $3.51   | $3.20      |
| 10   | 80.7 | $3.75   | $3.85      |
| 15   | 73.7 | $4.09   | $3.93      |
| 20   | 75.4 | $4.44   | $4.82      |

**Pattern:** Win rate drops from 97% at bar 1 to 81% at bar 10, while avg PnL stays flat ($3.77-$3.99 range through bar 10). The avg PnL *increases* at 15-20 bars only because winners that survive that long are big runners.

## Trade-by-Trade: Hold=3 vs Hold=10

Across 57 bull breakout trades:
- **Mean delta (PnL@10 - PnL@3): -$0.02** (essentially zero)
- **Median delta: -$0.03**
- Hold=10 better in 27 trades, Hold=3 better in 29 trades
- Max upside missed by exiting at 3: **+$13.75** (one outlier on 2025-12-16)
- Max downside avoided by exiting at 3: **-$10.57** (one outlier on 2025-03-28)

**The distribution is symmetric.** On average, you leave nothing on the table by exiting at bar 3 instead of bar 10.

## MFE Capture Ratio

| Hold | Avg MFE | Avg PnL | PnL/MFE@20 |
|------|---------|---------|-------------|
| 3    | $5.22   | $3.90   | 57.3%       |
| 5    | $5.45   | $3.51   | 51.6%       |
| 10   | $5.79   | $3.71   | 54.6%       |
| 20   | $6.79   | $3.99   | 58.8%       |

Hold=3 captures 57% of the total move available at hold=20, but with 93% win rate vs 75%.

## Options Execution Analysis

For a 0DTE TSLA ATM call at market open:
- **Delta ~0.50**, gamma ~0.03-0.05/$ move
- First $1 stock move = ~$0.52 option gain (delta + gamma pickup)
- Theta cost in 3 min: ~$0.01 (negligible)
- Theta cost in 10 min: ~$0.03-0.05 (still small)

**Critical insight:** After a $3-4 stock gain (typical bull breakout), delta is now ~0.65. A reversal now costs MORE in options than the early move gained. The asymmetry favors fast exits.

Hold=3 at $3.77 avg stock gain = **~$2.08 option gain** (avg delta ~0.55)
Hold=10 at $3.75 avg stock gain = **~$2.16 option gain** (avg delta ~0.575)
Difference: $0.08 per option contract — not worth the 12pp win rate drop.

## With vs Without Fallback SL

| Config | n | Win% | Avg PnL | Score | Sharpe |
|--------|---|------|---------|-------|--------|
| HOLD=3 +SL=1.50 | 122 | 28.7% | $0.34 | 23.7 | 1.73 |
| HOLD=3 NO_SL | 122 | 50.8% | $0.80 | 99.3 | 2.96 |
| HOLD=10 +SL=1.50 | 122 | 25.4% | $0.26 | 16.4 | 1.21 |
| HOLD=10 NO_SL | 122 | 45.1% | $0.79 | 87.0 | 2.48 |

The fallback SL destroys more value than hold time optimization can recover. **P3 (SL optimization) is a bigger lever than P2.**

## Recommendation

**Change default from HOLD=10 to HOLD=3.** Rationale:
1. Zero average P&L difference vs hold=10, but 12pp higher win rate on bull trades
2. 93% win rate on bull breakouts = better psychology and consistency
3. Options delta/gamma asymmetry favors fast exits (reversal risk is amplified)
4. 3 bars (3 minutes) is executable for options — one click market order, no urgency
5. Reduces exposure to SL_DURING_HOLD events (0 at hold=3 vs 4 at hold=10)

**Second priority:** Fix the fallback SL — it's the real profit killer (44% of trades, all losses).
