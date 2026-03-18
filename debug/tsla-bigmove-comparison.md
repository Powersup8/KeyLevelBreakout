# TSLA Big-Move Comparison — Threshold Analysis
Base dataset: 6761 moves with range >= 1x 5m-ATR(14)

## Cohort Overview

| Cohort | n | Runners | Fakeouts | Middle | Runner% | Fakeout% | Avg MFE | Avg MAE | Per Day |
|--------|---|---------|----------|--------|---------|----------|---------|---------|---------|
| 1x 5m-ATR (baseline) | 6761 | 858 | 67 | 5836 | 13% | 1% | 1.30 | -1.28 | 26.8 |
| 2x 5m-ATR | 654 | 107 | 6 | 541 | 16% | 1% | 1.83 | -1.94 | 2.7 |
| 0.5x Daily ATR | 15 | 2 | 0 | 13 | 13% | 0% | 3.75 | -0.37 | 1.2 |
| 0.75x Daily ATR | 1 | 0 | 0 | 1 | 0% | 0% | nan | nan | 1.0 |

---
## 2x 5m-ATR (n=654)

### Stats — Runner vs Fakeout

| Metric | All (n=654) | Runners (n=107) | Fakeouts (n=6) | Gap |
|--------|-----|---------|----------|-----|
| Avg MFE (ATR) | 1.83 | 2.09 | -0.06 | +2.15 |
| Avg MAE (ATR) | -1.94 | -1.79 | -2.78 | +0.99 |
| Avg 5m P&L | 0.11 | 0.29 | -1.28 | +1.57 |
| Avg Body % | 57.42 | 51.96 | 46.20 | +5.76 |
| Avg Range/5m-ATR | 2.81 | 3.15 | 2.51 | +0.64 |
| Avg Vol Ratio | 3.60 | 5.68 | 4.22 | +1.46 |
| Avg ADX | 26.84 | 28.44 | 22.65 | +5.79 |
| Avg VWAP Dist | -0.16 | 0.08 | 0.30 | -0.22 |
| Pre: Vol Ramp | 6.23 | 7.61 | 1.07 | +6.55 |
| Pre: Dir Pressure | 50.43 | 52.32 | 56.67 | -4.35 |
| Pre: Compression | 2.05 | 2.64 | 2.86 | -0.21 |
| 15m: Range/ATR | 4.02 | 4.47 | 3.96 | +0.51 |
| 15m: Position | 53.33 | 51.25 | 46.20 | +5.05 |
| Day: Gap/ATR | 0.30 | -0.34 | -0.25 | -0.09 |
| Day: Range Position | 51.39 | 51.00 | 36.60 | +14.40 |

### Feature Rates

| Feature | All | Runners | Fakeouts | Gap |
|---------|-----|---------|----------|-----|
| EMA aligned | 57% | 56% | 67% | -11% |
| VWAP aligned | 76% | 76% | 100% | -24% |
| Above EMA9 | 48% | 43% | 33% | +10% |
| Above EMA20 | 49% | 42% | 33% | +9% |
| 15m trend aligned | 54% | 63% | 67% | -4% |
| 15m breakout | 74% | 78% | 83% | -6% |
| Bull direction | 44% | 50% | 50% | +0% |
| 5min P&L positive | 11% | 66% | 0% | +66% |

### By Time of Day

| Time | n | Runners | Fakeouts | Runner% | Avg MFE |
|------|---|---------|----------|---------|---------|
| 09:30-10 | 428 | 84 | 3 | 20% | 1.97 |
| 10-11 | 39 | 7 | 0 | 18% | 1.27 |
| 11-12 | 15 | 0 | 0 | 0% | nan |
| 12-13 | 20 | 3 | 1 | 15% | 2.13 |
| 13-14 | 29 | 2 | 0 | 7% | 0.82 |
| 14-15 | 43 | 4 | 1 | 9% | 1.74 |
| 15-16 | 80 | 7 | 1 | 9% | 1.13 |

### Pre-Move Volume Ramp

| Vol Ramp | n | Runner% | Fakeout% | Avg MFE |
|----------|---|---------|----------|---------|
| <0.5 (drying) | 28 | 11% | 4% | 0.98 |
| 0.5-1 (steady) | 163 | 14% | 1% | 1.61 |
| 1-2x (ramping) | 197 | 12% | 2% | 1.55 |
| >2x (surging) | 192 | 17% | 0% | 2.17 |

### Gap Context

| Gap | n | Runner% | Fakeout% | Avg MFE |
|-----|---|---------|----------|---------|
| Gap Down | 240 | 21% | 1% | 1.81 |
| Flat | 46 | 11% | 0% | 2.23 |
| Gap Up | 368 | 14% | 1% | 1.81 |

### Top 10 Runners

| Date | Time | Dir | Range | Body | Vol | ADX | Pre VolRamp | 5mPnL | MFE | MAE |
|------|------|-----|-------|------|-----|-----|-------------|-------|-----|-----|
| 2026-01-22 | 12:45 | Bull | 2.4 | 90% | 1.5x | 31 | 0.9x | 1.00 | 6.68 | -0.10 |
| 2026-01-12 | 09:30 | Bull | 5.4 | 41% | 14.6x | 29 | 2.3x | -0.72 | 6.35 | -1.98 |
| 2026-01-28 | 09:30 | Bull | 3.6 | 46% | 3.0x | 25 | nanx | 1.95 | 5.41 | -0.67 |
| 2026-01-09 | 09:35 | Bull | 2.7 | 12% | 6.6x | 28 | 62.4x | 1.00 | 5.18 | -0.31 |
| 2026-01-16 | 09:30 | Bull | 6.7 | 93% | 17.6x | 18 | 1.5x | 2.77 | 4.89 | -2.78 |
| 2026-01-29 | 09:30 | Bear | 5.6 | 63% | 5.2x | 14 | nanx | 2.35 | 4.23 | -0.18 |
| 2026-01-23 | 09:35 | Bull | 2.2 | 23% | 6.4x | 16 | 36.0x | 0.22 | 4.11 | -1.41 |
| 2026-01-21 | 14:25 | Bull | 4.5 | 87% | 3.1x | 23 | 1.3x | 2.10 | 4.03 | -0.12 |
| 2026-02-10 | 09:30 | Bull | 4.6 | 60% | 1.9x | 19 | nanx | 2.02 | 3.84 | -1.23 |
| 2026-02-17 | 09:30 | Bear | 3.4 | 48% | 3.6x | 30 | nanx | -1.59 | 3.69 | -1.98 |

---
## 0.5x Daily ATR (n=15)

### Stats — Runner vs Fakeout

| Metric | All (n=15) | Runners (n=2) | Fakeouts (n=0) | Gap |
|--------|-----|---------|----------|-----|
| Avg MFE (ATR) | 3.75 | 3.75 | 0.00 | +0.00 |
| Avg MAE (ATR) | -0.37 | -0.37 | 0.00 | +0.00 |
| Avg 5m P&L | 1.38 | 1.38 | 0.00 | +0.00 |
| Avg Body % | 67.27 | 68.30 | 0.00 | +0.00 |
| Avg Range/5m-ATR | 3.82 | 5.99 | 0.00 | +0.00 |
| Avg Vol Ratio | 5.32 | 10.39 | 0.00 | +0.00 |
| Avg ADX | 28.93 | 20.20 | 0.00 | +0.00 |
| Avg VWAP Dist | -0.23 | -0.88 | 0.00 | +0.00 |
| Pre: Vol Ramp | 1.86 | 6.27 | 0.00 | +0.00 |
| Pre: Dir Pressure | 52.73 | 60.00 | 0.00 | +0.00 |
| Pre: Compression | 2.18 | 1.62 | 0.00 | +0.00 |
| 15m: Range/ATR | 4.90 | 7.70 | 0.00 | +0.00 |
| 15m: Position | 55.45 | 82.95 | 0.00 | +0.00 |
| Day: Gap/ATR | -0.11 | -2.20 | 0.00 | +0.00 |
| Day: Range Position | 52.68 | 45.40 | 0.00 | +0.00 |

### Feature Rates

| Feature | All | Runners | Fakeouts | Gap |
|---------|-----|---------|----------|-----|
| EMA aligned | 73% | 100% | 0% | +0% |
| VWAP aligned | 80% | 100% | 0% | +0% |
| Above EMA9 | 47% | 0% | 0% | +0% |
| Above EMA20 | 47% | 0% | 0% | +0% |
| 15m trend aligned | 67% | 100% | 0% | +0% |
| 15m breakout | 80% | 100% | 0% | +0% |
| Bull direction | 33% | 0% | 0% | +0% |
| 5min P&L positive | 13% | 100% | 0% | +100% |

### By Time of Day

| Time | n | Runners | Fakeouts | Runner% | Avg MFE |
|------|---|---------|----------|---------|---------|
| 09:30-10 | 10 | 2 | 0 | 20% | 3.75 |
| 10-11 | 4 | 0 | 0 | 0% | nan |

### Pre-Move Volume Ramp

| Vol Ramp | n | Runner% | Fakeout% | Avg MFE |
|----------|---|---------|----------|---------|
| 0.5-1 (steady) | 4 | 0% | 0% | nan |
| 1-2x (ramping) | 3 | 0% | 0% | nan |
| >2x (surging) | 4 | 25% | 0% | 3.27 |

### Gap Context

| Gap | n | Runner% | Fakeout% | Avg MFE |
|-----|---|---------|----------|---------|
| Gap Down | 9 | 22% | 0% | 3.75 |
| Gap Up | 6 | 0% | 0% | nan |

### Top 10 Runners

| Date | Time | Dir | Range | Body | Vol | ADX | Pre VolRamp | 5mPnL | MFE | MAE |
|------|------|-----|-------|------|-----|-----|-------------|-------|-----|-----|
| 2026-01-29 | 09:30 | Bear | 5.6 | 63% | 5.2x | 14 | nanx | 2.35 | 4.23 | -0.18 |
| 2026-01-06 | 09:30 | Bear | 6.3 | 73% | 15.5x | 26 | 6.3x | 0.40 | 3.27 | -0.55 |
| 2025-04-07 | 10:10 | Bull | 3.9 | 76% | 2.2x | 30 | 0.5x | nan | nan | nan |
| 2025-04-07 | 10:15 | Bear | 2.1 | 32% | 1.7x | 30 | 2.4x | nan | nan | nan |
| 2025-04-07 | 10:20 | Bear | 2.0 | 86% | 1.4x | 28 | 0.8x | nan | nan | nan |
| 2025-06-05 | 15:15 | Bear | 2.3 | 46% | 2.6x | 69 | 1.5x | nan | nan | nan |
| 2025-06-23 | 09:30 | Bull | 4.4 | 53% | 6.2x | 21 | 2.5x | nan | nan | nan |
| 2025-07-24 | 09:30 | Bear | 2.9 | 55% | 7.4x | 33 | nanx | nan | nan | nan |
| 2025-08-11 | 09:30 | Bull | 4.4 | 70% | 5.2x | 20 | nanx | nan | nan | nan |
| 2025-08-22 | 10:00 | Bull | 5.0 | 77% | 4.1x | 25 | 0.8x | nan | nan | nan |

---
## Feature Ranking — Which Predictors Get STRONGER with Tighter Threshold?

Comparing the Runner-Fakeout gap across cohorts (bigger gap = more useful predictor):

| Feature | 1x 5m-ATR gap | 2x 5m-ATR gap | 0.5x Daily gap | Trend |
|---------|---------------|---------------|----------------|-------|
| 5min P&L positive | +67 | +66 | +100 | ↑ stronger |
| Pre: Vol Ramp | +0.75 | +6.55 | +6.27 | ↑ stronger |
| Vol Ratio | +0.29 | +1.46 | +10.39 | ↑ stronger |
| VWAP Dist | +0.30 | -0.22 | -0.88 | ↑ stronger |
| Gap/ATR | -0.38 | -0.09 | -2.20 | ↑ stronger |
| EMA aligned | -4 | -11 | +100 | ↑ stronger |
| Body % | -1.72 | +5.76 | +68.30 | ↑ stronger |
| ADX | +0.75 | +5.79 | +20.20 | ↑ stronger |
