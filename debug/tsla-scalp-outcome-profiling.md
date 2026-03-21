# TSLA Open Scalp: Outcome-First Profiling

**Date:** 2026-03-20
**Dataset:** 137 trading days with full PM + RTH 15sec data (Sep 2025 - Mar 2026)
**Method:** Start from outcome (PUT vs CALL P&L), work backwards to premarket features

---

## 1. Day Categorization (Phase 2)

| Category | N | % | CALL_2m | PUT_2m | CALL_5m | PUT_5m | CALL_EOD | PUT_EOD |
|----------|---:|---:|--------:|-------:|--------:|-------:|---------:|--------:|
| A: Strong CALL | 30 | 21.6% | +3.47 | -3.47 | +4.08 | -4.08 | +3.95 | -3.95 |
| B: Strong PUT  | 35 | 25.2% | -3.12 | +3.12 | -3.67 | +3.67 | -4.53 | +4.53 |
| C: Weak CALL   | 29 | 20.9% | +0.71 | -0.71 | +0.91 | -0.91 | -0.83 | +0.83 |
| D: Weak PUT    | 35 | 25.2% | -0.83 | +0.83 | -1.10 | +1.10 | +0.55 | -0.55 |
| E: Reversal    |  5 |  3.6% | -2.73 | +2.73 | +2.24 | -2.24 | +5.94 | -5.94 |
| F: Fade        |  5 |  3.6% | +2.17 | -2.17 | -3.63 | +3.63 | -2.26 | +2.26 |

**Key takeaway:** ~47% of days have strong (>$1.50) directional moves in the first 2 minutes. The remaining ~46% are weak/marginal. Reversals and fades are rare (7%).

MFE shows even weak days have significant intraday swings — the issue is *timing*, not *magnitude*:
- Weak CALL: CALL_MFE_5m = $2.77, but closes at only +$0.91
- Weak PUT: PUT_MFE_5m = $2.84, but closes at only +$1.10

Category C (Weak CALL) actually loses by EOD (-$0.83), and Category D (Weak PUT) reverses to positive CALL by EOD (+$0.55). These weak categories are **noise** — the initial direction is unreliable.

---

## 2. Feature Profiles: What Separates Strong CALL from Strong PUT? (Phase 3)

### Cohen's d Ranking (A vs B separability)

| Rank | Feature | |d| | p-value | Direction |
|-----:|---------|----:|--------:|-----------|
| 1 | **gap** | 0.981 | 0.0009*** | Gap up = CALL |
| 2 | **gap_pct** | 0.969 | 0.0006*** | Same |
| 3 | consecutive_down_bars | 0.598 | 0.082 | More = PUT |
| 4 | opening_volume | 0.588 | 0.047* | Higher = CALL |
| 5 | pm_position | 0.560 | 0.032* | Higher = CALL |
| 6 | pm_direction_changes | 0.358 | 0.150 | More = CALL |
| 7 | pm_high_recency | 0.341 | 0.195 | Recent = CALL |
| 8 | spy_accel_2m | 0.331 | 0.394 | Negative = CALL?? |
| 9 | pm_low_recency | 0.319 | 0.162 | Far = CALL |
| 10 | pm_acceleration | 0.311 | 0.213 | Accelerating = CALL |
| 11 | pm_accel_2m | 0.290 | 0.193 | Positive = CALL |
| 12-25 | (all others) | <0.26 | >0.17 | Weak |

**Only gap/gap_pct are statistically significant (p < 0.001).** Everything else has large overlap.

### Category means for top features

**Gap:**
- Strong CALL: mean=+$3.98, P25=+$1.38, P75=+$6.09
- Strong PUT: mean=-$0.87, P25=-$5.45, P75=+$2.83
- Note: Fades have HUGE gaps (mean +$9.02) — gap up too much = fade risk

**PM Position:**
- Strong CALL: mean=0.66, median=0.73 (near PM high)
- Strong PUT: mean=0.49, median=0.53 (mid-range)
- Overlap is substantial — many PUT days also have high PM position

---

## 3. Decision Surface Analysis (Phase 4)

### Best split points (PUT below / CALL above threshold)

| Rank | Feature | Optimal Split | Avg PnL per trade |
|-----:|---------|---------------|------------------:|
| 1 | **gap** | $1.01 | **+$0.76** |
| 2 | **gap_pct** | 0.2% | +$0.76 |
| 3 | pm_position | 0.84 | +$0.66 |
| 4 | last_30s_direction | $0.10 | +$0.50 |
| 5 | pm_accel_4m | $0.40 | +$0.43 |
| 6 | opening_volume | 1.12M | +$0.43 |
| 7 | pm_accel_10m | $0.00 | +$0.42 |
| 8 | pm_accel_2m | -$0.05 | +$0.39 |

Gap dominates. The gap split at ~$1 gives: PUT win rate 63% below, CALL win rate 57% above.

### Gap split detail:

| Percentile | Gap Value | PUT win% below | CALL win% above | Avg PnL |
|-----------:|----------:|---------------:|----------------:|--------:|
| 10% | -$7.51 | 76.9% | 49.2% | +$0.31 |
| 30% | -$2.65 | 70.7% | 54.2% | +$0.69 |
| 50% | +$1.01 | 63.2% | 56.5% | **+$0.76** |
| 70% | +$3.46 | 60.0% | 61.9% | +$0.63 |
| 90% | +$8.35 | 56.9% | 78.6% | +$0.44 |

The P50 split (gap ~$1) is optimal because it balances both sides. Extreme gaps (P90) have very high CALL win rate (79%) but too few trades.

---

## 4. Interaction / Stacking Results (Phase 6)

### PUT side (bearish stacking)

| Filter Stack | N | PUT_2m | Win% |
|-------------|---:|-------:|-----:|
| gap < 0 | 61 | +$0.94 | 67.2% |
| + pm_accel_2m < 0 | 34 | +$1.02 | 70.6% |
| + pm_position < 0.5 | 30 | +$0.86 | 66.7% |
| + consecutive_down >= 1 (from gap<0 + accel<0) | 17 | +$1.27 | 70.6% |

### CALL side (bullish stacking)

| Filter Stack | N | CALL_2m | Win% |
|-------------|---:|--------:|-----:|
| gap > $1 | 69 | +$0.70 | 56.5% |
| + pm_accel_2m > 0 | 35 | **+$1.39** | **68.6%** |
| + pm_position > 0.5 | 34 | +$1.36 | 67.6% |
| + pm_acceleration > 0 | 31 | +$1.39 | 67.7% |

**Stacking helps on the CALL side** — adding pm_accel_2m > 0 to gap > $1 doubles the per-trade P&L (+$0.70 to +$1.39) while keeping 35 trades.

### Best 2-Feature Combos (both agree -> trade, disagree -> skip)

| Combo | N CALL | N PUT | Avg PnL | Win% | Skip |
|-------|-------:|------:|--------:|-----:|-----:|
| gap>0 & pm_accel_2m>0 | 37 | 34 | **+$1.19** | **70.4%** | 66 |
| gap>0 & pm_acceleration>0 | 38 | 33 | +$1.12 | 69.0% | 66 |
| gap>0 & pm_momentum_score>0 | 40 | 36 | +$1.15 | 68.4% | 61 |
| gap>0 & consec_down=0 | 29 | 29 | +$1.29 | 67.2% | 79 |

### Best 3-Feature Combos

| Combo | N CALL | N PUT | Avg PnL | Win% | Skip |
|-------|-------:|------:|--------:|-----:|-----:|
| gap>0 & accel_2m>0 & acceleration>0 | 33 | 31 | **+$1.24** | **70.3%** | 73 |
| gap>0 & momentum_score>0 & pos>0.5 | 38 | 32 | +$1.16 | 68.6% | 67 |

Adding a 3rd feature barely improves PnL over 2 features while cutting sample size. **2 features is the sweet spot.**

---

## 5. "Impossible Days" Analysis (Phase 7)

### Bullish PM but Strong PUT outcome

**5 days** where pm_accel_2m > 0, pm_position > 0.5, pm_velocity > 0, yet PUT_2m > $2.

| Date | Gap | Accel_2m | PM Pos | PUT_2m |
|------|----:|--------:|-------:|-------:|
| 2025-10-01 | -$0.80 | +1.54 | 0.86 | +$2.62 |
| 2025-10-08 | +$4.83 | +0.22 | 0.75 | +$3.92 |
| 2025-12-16 | -$2.88 | +1.42 | 0.63 | +$2.91 |
| 2026-01-05 | +$9.89 | +0.89 | 0.93 | +$2.77 |
| 2026-01-07 | +$2.99 | +0.32 | 0.92 | +$3.37 |

**What separates them from normal bullish days that went up?**

| Feature | Impossible (5) | Normal (15) | Diff |
|---------|---------------:|------------:|-----:|
| gap | +$2.81 | +$6.34 | -$3.53 |
| opening_volume | 851K | 1,171K | -320K |
| consecutive_down_bars | 1.8 | 0.5 | +1.3 |
| spy_accel_10m | -0.19 | +0.07 | -0.26 |
| vix_prev | 15.87 | 18.33 | -2.46 |

**Key signal: "impossible" PUT days had SMALLER gaps (+$2.81 vs +$6.34), LOWER opening volume, MORE consecutive down bars (last-second weakness), and SPY divergence (SPY falling while TSLA PM rising).**

### Bearish PM but Strong CALL outcome

**5 days** with opposite surprise. Key differentiator: **gap was less negative** (-$1.12 vs -$3.46) and **SPY was falling** (-0.23 vs +0.23 spy_accel_10m). These appear to be mean-reversion days where oversold PM bounced at the open.

**Conclusion: ~12.5% of "clear-signal" days are genuine surprises.** SPY divergence is the best (but not strong) clue.

---

## 6. Computed Indicator Results (Phase 8)

| Indicator | Cohen's d (A vs B) | p-value | Best Split PnL |
|-----------|------------------:|--------:|---------------:|
| **Gap / PM Range** | **+0.889** | **0.004** | **+$0.81** |
| Gap-Momentum Alignment | +0.359 | 0.161 | +$0.31 |
| PM Direction Changes | +0.358 | 0.150 | +$0.31 |
| PM Momentum Score | +0.276 | 0.143 | +$0.51 |
| Directional Conviction | +0.142 | 0.462 | +$0.25 |
| Opening Energy | +0.096 | 0.421 | +$0.34 |
| Gap Digestion | +0.051 | 0.518 | +$0.12 |
| PM Regime (R^2) | +0.033 | 0.685 | +$0.27 |

**Gap / PM Range is the best composite indicator** (d=0.889, p=0.004). It normalizes the overnight gap by PM trading range — essentially measuring "how significant is the gap relative to today's PM activity?"

Binary indicators (PM Exhaustion, PM Capitulation) had too few instances (4-7 days) to be useful.

**Gap-Momentum Alignment** (sign of gap matches sign of pm_accel): when aligned, CALL_2m = +$0.22 (51% win). When opposed, CALL_2m = -$0.35 (42% win). This is the momentum-confirmation signal.

---

## 7. Bottom Line

### Single Best Discriminator: **GAP**

- Cohen's d = 0.98 (large effect)
- p < 0.001 (highly significant)
- Best split at ~$1: avg PnL = +$0.76/trade at 62% win rate
- Explains more variance than ALL other premarket features combined

### Best 2-Feature Combo: **Gap > 0 AND pm_accel_2m > 0**

- Avg PnL = **+$1.19/trade** at **70.4% win rate**
- Trades 71 of 137 days (52% participation)
- Both features must agree on direction; skip when they disagree
- This is 57% higher PnL than gap alone (+$0.76)

### Best 3-Feature Combo: **Gap > 0 AND pm_accel_2m > 0 AND pm_acceleration > 0**

- Avg PnL = +$1.24/trade at 70.3% win rate
- Trades 64 of 137 days (47% participation)
- Marginal improvement over 2 features (+$0.05) — not worth the complexity

### One-Side Best Strategies

**CALL entry (bullish):**
- gap > $1 + accel_2m > 0: N=35, CALL_2m=+$1.39, 68.6% win, total +$48.6

**PUT entry (bearish):**
- gap < -$3: N=36, PUT_2m=+$1.28, 72.2% win, total +$46.0
- gap < 0 + accel_2m < 0 + consec_down >= 1: N=17, PUT_2m=+$1.27, 70.6% win

### Comparison to Binary Confidence System

| Approach | Avg PnL/trade | Win Rate | Trades | Total PnL |
|----------|-------------:|--------:|-------:|----------:|
| Baseline (always PUT) | +$0.05 | 53.3% | 137 | +$7.3 |
| Gap split only | +$0.76 | 62.0% | 137 | +$104.1 |
| **Gap + accel_2m combo** | **+$1.19** | **70.4%** | **71** | **+$84.5** |
| Gap>$1 + accel_2m>0 (CALL only) | +$1.39 | 68.6% | 35 | +$48.6 |
| Gap<-$3 (PUT only) | +$1.28 | 72.2% | 36 | +$46.0 |

**The gap+acceleration combo produces 16x the per-trade PnL of the baseline** and trades about half the days. The "skip when signals disagree" approach is key — it avoids the ~46% of days that are weak/marginal.

### What Doesn't Work

- **PM Smoothness / R^2**: No discriminating power (d=0.03)
- **VIX**: No signal (d=0.08, p=0.76)
- **PM Range**: No signal (d=0.04)
- **SPY momentum**: Weak and paradoxical (SPY moving down correlated with TSLA CALL days)
- **PM volume**: Weak discriminator despite intuitive appeal
- **Close position gates**: Previously known dead end, confirmed here

### Caveats

1. **139 trading days** is a small sample. The gap + accel combo's 70% win rate has a 95% CI of roughly 59-80%.
2. **Gap is the dominant signal** — and it's trivially available pre-market. The question is whether options pricing already discounts it.
3. **~12% of "clear signal" days are genuine surprises** that no premarket feature can predict. This sets a hard ceiling on accuracy.
4. **Fades (gap up, then drop)** are rare (3.6%) but devastating. The 5 Fade days had mean gap = +$9.02. Extreme gaps (>$8) are fade risk.
5. The 15sec data only covers ~9 months. A full year (including different volatility regimes) might show different patterns.
