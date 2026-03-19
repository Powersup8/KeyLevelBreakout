# TSLA Open Scalper — Runner Identification Findings

**Date:** 2026-03-19

**Bull breakouts:** 57 trades

**Runners (PnL@20>0):** 43 (75%)
**Faders (PnL@20<=0):** 14 (25%)

## Baselines

| Strategy | N | Win% | Avg PnL | Total PnL | Sharpe |
|----------|---|------|---------|-----------|--------|
| All trades hold=3 | 122 | 50.8 | $0.8 | $97.73 | 2.96 |
| Bulls hold=3 | 57 | 93.0 | $3.77 | $215.17 | 21.56 |
| Bulls hold=20 | 57 | 75.4 | $4.44 | $253.15 | 8.28 |

## Feature Comparison: Runners vs Faders

| Feature | Runners (mean) | Faders (mean) | Delta | p-value | Signal? |
|---------|----------------|---------------|-------|---------|---------|
| tier             |      1.093 |      1.071 |  +0.022 | 0.8001 |     |
| confidence       |      3.605 |      3.429 |  +0.176 | 0.3876 |     |
| shakeout         |      0.070 |      0.071 |  -0.002 | 0.9839 |     |
| fakeout          |      0.070 |      0.071 |  -0.002 | 0.9839 |     |
| orb_width        |      5.319 |      4.558 |  +0.761 | 0.1154 |     |
| is_hold          |      0.791 |      0.571 |  +0.219 | 0.1628 |     |
| pm_position      |      0.583 |      0.678 |  -0.095 | 0.1230 |     |
| pm_accel         |      0.445 |      0.326 |  +0.120 | 0.6681 |     |
| vix              |     19.273 |     19.177 |  +0.096 | 0.9298 |     |
| path_eff         |      0.191 |      0.212 |  -0.021 | 0.5670 |     |
| brk_strength     |      0.643 |      0.740 |  -0.097 | 0.5387 |     |
| brk_timing       |      2.116 |      5.929 |  -3.812 | 0.0495 |  ** |
| brk_volume       | 575830.023 | 523618.214 | +52211.809 | 0.4385 |     |
| brk_bar_range    |      2.095 |      1.767 |  +0.328 | 0.2158 |     |
| brk_close_pos    |      0.840 |      0.840 |  +0.000 | 0.9963 |     |
| brk_vol_ratio    |      0.978 |      1.034 |  -0.055 | 0.5566 |     |

## Detailed Breakdowns

### By Confidence Score

| Confidence | N | Runner% | Avg PnL@3 | Avg PnL@20 |
|------------|---|---------|-----------|------------|
| 3 | 30 | 70% | $3.95 | $4.07 |
| 4 | 22 | 82% | $3.74 | $4.79 |
| 5 | 5 | 80% | $2.87 | $5.16 |

### By Tier

| Tier | N | Runner% | Avg PnL@3 | Avg PnL@20 |
|------|---|---------|-----------|------------|
| HIGH | 5 | 80% | $2.87 | $5.16 |
| MED | 52 | 75% | $3.86 | $4.37 |

### By Shakeout

| Shakeout | N | Runner% | Avg PnL@3 | Avg PnL@20 |
|----------|---|---------|-----------|------------|
| False | 53 | 75% | $3.92 | $4.61 |
| True | 4 | 75% | $1.84 | $2.26 |

### By 5m Hold Rule

| is_hold | N | Runner% | Avg PnL@3 | Avg PnL@20 |
|---------|---|---------|-----------|------------|
| False | 15 | 60% | $1.26 | $1.29 |
| True | 42 | 81% | $4.67 | $5.57 |

### By ORB Width Quartile

| Quartile | Range | N | Runner% | Avg PnL@20 |
|----------|-------|---|---------|------------|
| Q1 | $2.1-$3.8 | 15 | 73% | $2.94 |
| Q2 | $3.9-$4.8 | 14 | 71% | $3.34 |
| Q3 | $5.0-$6.2 | 14 | 71% | $3.26 |
| Q4 | $6.3-$10.5 | 14 | 86% | $8.33 |

### By Breakout Strength Quartile

| Quartile | Range | N | Runner% | Avg PnL@20 |
|----------|-------|---|---------|------------|
| Q1 | $0.01-$0.29 | 15 | 73% | $4.02 |
| Q2 | $0.33-$0.56 | 14 | 100% | $9.89 |
| Q3 | $0.57-$0.85 | 14 | 57% | $1.79 |
| Q4 | $0.93-$1.98 | 14 | 71% | $2.09 |

### By Breakout Timing

| Timing | N | Runner% | Avg PnL@20 |
|--------|---|---------|------------|
| 9:35 (0m) | 20 | 90% | $5.24 |
| 9:36-38 (1-3m) | 22 | 73% | $3.33 |
| 9:39-45 (4-10m) | 9 | 78% | $5.89 |
| 9:46-55 (11-20m) | 6 | 33% | $3.69 |

### By Breakout Volume Ratio (vs ORB avg)

| Quartile | Range | N | Runner% | Avg PnL@20 |
|----------|-------|---|---------|------------|
| Q1 | 0.50-0.78x | 15 | 87% | $5.07 |
| Q2 | 0.80-0.96x | 14 | 64% | $2.71 |
| Q3 | 1.03-1.13x | 14 | 79% | $7.26 |
| Q4 | 1.15-1.87x | 14 | 71% | $2.68 |

### By PM Position Quartile

| Quartile | Range | N | Runner% | Avg PnL@20 |
|----------|-------|---|---------|------------|
| Q1 | 0.148-0.439 | 15 | 93% | $8.09 |
| Q2 | 0.453-0.653 | 14 | 64% | $1.36 |
| Q3 | 0.658-0.778 | 14 | 64% | $1.83 |
| Q4 | 0.794-0.955 | 14 | 79% | $6.21 |

## Runner Score Model (v2 — data-driven)

Only components where runner% when True > baseline 75%.

### Score Components (each +1 point)

| Component | N (True) | Runner% when True |
|-----------|----------|-------------------|
| brk_timing<=3 (before 9:39) | 42 | 81% |
| is_hold=True (5m rule) | 42 | 81% |
| confidence>=4 | 27 | 81% |
| orb_width>=P75 ($6.2) | 15 | 87% |

### Score Distribution

| Score | N | Runner% | Avg PnL@3 | Avg PnL@20 | Recommendation |
|-------|---|---------|-----------|------------|----------------|
| 0 | 3 | 67% | $1.80 | $2.60 | HOLD 3 |
| 1 | 10 | 40% | $1.81 | $-0.23 | HOLD 3 |
| 2 | 20 | 80% | $3.53 | $5.35 | HOLD 20 |
| 3 | 20 | 85% | $4.65 | $4.99 | HOLD 20 |
| 4 | 4 | 100% | $7.03 | $10.23 | HOLD 20 |

## Adaptive Strategy Backtest

For each threshold T: if runner_score >= T, hold 20 bars; else hold 3.

| Threshold | N@20 | N@3 | Total PnL | Avg PnL | Win% | Sharpe |
|-----------|------|-----|-----------|---------|------|--------|
| Flat hold=3 | 0 | 122 | $97.73 | $0.80 | 51% | 2.96 |
| Flat hold=20 | 122 | 0 | $135.71 | $1.11 | 43% | 2.49 |
| score >= 1 | 54 | 68 | $133.32 | $1.09 | 43% | 2.45 |
| score >= 2 | 44 | 78 | $153.70 | $1.26 | 47% | 3.13 |
| score >= 3 | 24 | 98 | $117.47 | $0.96 | 48% | 3.02 |
| score >= 4 | 4 | 118 | $110.55 | $0.91 | 51% | 3.16 |

## Summary and Recommendation

**Best adaptive threshold:** runner_score >= 2
**PnL improvement vs flat hold=3:** $55.97 (57%)
**Best Sharpe:** 3.13

### Decision Rule for Pine Script

```
runner_score = 0
if brk_timing <= 3min (before 9:39): runner_score += 1  // p=0.05, 90% at 9:35
if is_hold (5m rule): runner_score += 1                 // 81% runner rate
if confidence >= 4: runner_score += 1                   // 82% runner rate
if orb_width >= $6.2 (P75): runner_score += 1         // 86% runner, $8.33 avg

if runner_score >= 2: hold 20 bars (runner)
else: hold 3 bars (quick scalp)
```

### Key Combo: is_hold + early timing
- N=33, Runner%=85%, Avg PnL@20=$5.09
- This is the simplest 2-feature gate with strong signal.
