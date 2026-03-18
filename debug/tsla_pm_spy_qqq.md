# TSLA P10/P11 — SPY and QQQ Premarket Trend as TSLA Opening Filters
*Generated: 2026-03-18 | TSLA days: 280 | SPY PM: 234 days | QQQ PM: 234 days*

## P10 — SPY Premarket Structure

### P10a — SPY PM Position at 9:29 (where does price sit in SPY's 4am–9:29 range)

Thresholds: Q25=0.277, Q50=0.558, Q75=0.798

| label | n | day_above% | avg_day_chg | worst% | bad% | bull% | hold_5m% |
|---|---|---|---|---|---|---|---|
| All SPY PM days (baseline) | 234 | 50.9 | -0.18 | 29.9 | 41.9 | 29.5 | 50.0 |
| SPY Q1-bottom (near PM low) | 59 | 50.8 | -0.83 | 28.8 | 35.6 | 23.7 | 52.5 |
| SPY Q2 (lower-mid) | 58 | 44.8 | -0.75 | 32.8 | 51.7 | 29.3 | 48.3 |
| SPY Q3 (upper-mid) | 58 | 56.9 | 1.41 | 29.3 | 37.9 | 32.8 | 44.8 |
| SPY Q4-top (near PM high) | 59 | 50.8 | -0.55 | 28.8 | 42.4 | 32.2 | 54.2 |

### P10b — SPY PM Late Trend (9:20–9:29 direction)

| label | n | day_above% | avg_day_chg | worst% | bad% | bull% | hold_5m% |
|---|---|---|---|---|---|---|---|
| All SPY PM days (baseline) | 234 | 50.9 | -0.18 | 29.9 | 41.9 | 29.5 | 50.0 |
| SPY PM late UP | 113 | 51.3 | -0.21 | 29.2 | 42.5 | 31.9 | 53.1 |
| SPY PM late DOWN | 121 | 50.4 | -0.16 | 30.6 | 41.3 | 27.3 | 47.1 |

### P10c — SPY PM Acceleration (9:25–9:29)

| label | n | day_above% | avg_day_chg | worst% | bad% | bull% | hold_5m% |
|---|---|---|---|---|---|---|---|
| All SPY PM days (baseline) | 234 | 50.9 | -0.18 | 29.9 | 41.9 | 29.5 | 50.0 |
| SPY accel strong DOWN (bot 33%) | 78 | 57.7 | 1.82 | 24.4 | 34.6 | 35.9 | 48.7 |
| SPY accel mid | 79 | 38.0 | -2.63 | 39.2 | 53.2 | 20.3 | 50.6 |
| SPY accel strong UP (top 33%) | 77 | 57.1 | 0.29 | 26.0 | 37.7 | 32.5 | 50.6 |

### P10d — SPY × TSLA PM Trend Alignment

| label | n | day_above% | avg_day_chg | worst% | bad% | bull% | hold_5m% |
|---|---|---|---|---|---|---|---|
| All aligned days (baseline) | 234 | 50.9 | -0.18 | 29.9 | 41.9 | 29.5 | 50.0 |
| SPY PM UP + TSLA PM UP | 55 | 58.2 | 0.36 | 23.6 | 38.2 | 38.2 | 52.7 |
| SPY PM UP + TSLA PM DOWN | 58 | 44.8 | -0.76 | 34.5 | 46.6 | 25.9 | 53.4 |
| SPY PM DOWN + TSLA PM UP | 54 | 59.3 | 0.67 | 22.2 | 35.2 | 31.5 | 44.4 |
| SPY PM DOWN + TSLA PM DOWN | 67 | 43.3 | -0.83 | 37.3 | 46.3 | 23.9 | 49.3 |

### P10e — Strategy Comparison with SPY PM Filters

| Strategy | Trades | Win% | Avg P&L | Worst% | Sharpe |
|---|---|---|---|---|---|
| 5m rule alone (SPY PM days) | 117 | 66.7% | 3.00 | 18.8% | 3.10 |
| 5m + SPY PM top half (position) | 58 | 74.1% | 4.50 | 13.8% | 3.01 |
| 5m + SPY PM late UP | 60 | 68.3% | 2.56 | 18.3% | 2.31 |
| 5m + SPY PM top + late UP | 33 | 78.8% | 3.86 | 12.1% | 2.69 |

## P11 — QQQ Premarket Structure

### P11a — QQQ PM Position at 9:29

Thresholds: Q25=0.274, Q50=0.576, Q75=0.765

| label | n | day_above% | avg_day_chg | worst% | bad% | bull% | hold_5m% |
|---|---|---|---|---|---|---|---|
| All QQQ PM days (baseline) | 234 | 50.9 | -0.18 | 29.9 | 41.9 | 29.5 | 50.0 |
| QQQ Q1-bottom (near PM low) | 59 | 47.5 | -1.18 | 30.5 | 40.7 | 22.0 | 50.8 |
| QQQ Q2 (lower-mid) | 58 | 53.4 | 0.35 | 24.1 | 39.7 | 31.0 | 43.1 |
| QQQ Q3 (upper-mid) | 58 | 50.0 | -0.11 | 39.7 | 44.8 | 31.0 | 53.4 |
| QQQ Q4-top (near PM high) | 59 | 52.5 | 0.21 | 25.4 | 42.4 | 33.9 | 52.5 |

### P11b — QQQ PM Late Trend (9:20–9:29 direction)

| label | n | day_above% | avg_day_chg | worst% | bad% | bull% | hold_5m% |
|---|---|---|---|---|---|---|---|
| All QQQ PM days (baseline) | 234 | 50.9 | -0.18 | 29.9 | 41.9 | 29.5 | 50.0 |
| QQQ PM late UP | 108 | 55.6 | 0.15 | 24.1 | 37.0 | 27.8 | 52.8 |
| QQQ PM late DOWN | 126 | 46.8 | -0.47 | 34.9 | 46.0 | 31.0 | 47.6 |

### P11c — Triple PM Alignment: TSLA + SPY + QQQ

All three markets trending same direction in the last 10 PM minutes:

| label | n | day_above% | avg_day_chg | worst% | bad% | bull% | hold_5m% |
|---|---|---|---|---|---|---|---|
| All triple-aligned days (baseline) | 234 | 50.9 | -0.18 | 29.9 | 41.9 | 29.5 | 50.0 |
| All three PM UP | 47 | 59.6 | 0.40 | 19.1 | 36.2 | 36.2 | 53.2 |
| All three PM DOWN | 62 | 41.9 | -0.59 | 37.1 | 46.8 | 25.8 | 48.4 |
| Mixed directions | 125 | 52.0 | -0.20 | 30.4 | 41.6 | 28.8 | 49.6 |

### P11d — Triple Alignment × 5m Rule

| label | n | day_above% | avg_day_chg | worst% | hold_5m% |
|---|---|---|---|---|---|
| PM all PM UP × 5m=HOLD | 25 | 80.0 | 3.33 | 8.0 | 100 |
| PM all PM UP × 5m=BAIL | 22 | 36.4 | -2.93 | 31.8 | 0 |
| PM NOT all PM UP × 5m=HOLD | 92 | 63.0 | 2.92 | 21.7 | 100 |
| PM NOT all PM UP × 5m=BAIL | 95 | 34.7 | -3.48 | 43.2 | 0 |

## P12 — Combined Filter: TSLA P9 Bear + SPY PM Trend

TSLA P9 bear = PM position < 0.219 (Q1) AND accel < 0 (from prior research).
Testing whether adding SPY PM direction improves bad-day avoidance.

| Strategy | Trades | Win% | Avg P&L | Worst% | Sharpe |
|---|---|---|---|---|---|
| 5m rule (combo days) | 117 | 66.7% | 3.00 | 18.8% | 3.10 |
| 5m + skip TSLA P9 bear | 97 | 71.1% | 3.59 | 17.5% | 3.35 |
| 5m + SPY PM late UP | 60 | 68.3% | 2.56 | 18.3% | 2.31 |
| 5m + skip TSLA P9 + SPY PM UP | 50 | 70.0% | 2.90 | 20.0% | 2.33 |

## P13 — SPY PM Bear Composite (mirror of TSLA P9)

Test the same P9 logic on SPY: position < Q1 AND accel < 0.

SPY Q1 threshold: 0.277
SPY bear days: 38 / 234 = 16%

| label | n | day_above% | avg_day_chg | worst% | bad% | bull% | hold_5m% |
|---|---|---|---|---|---|---|---|
| SPY PM bear days | 38 | 50.0 | -1.11 | 31.6 | 34.2 | 26.3 | 60.5 |
| SPY PM non-bear days | 196 | 51.0 | -0.00 | 29.6 | 43.4 | 30.1 | 48.0 |

Worst-day capture: 12/70 = 17%
Good-day false-exclude: 26/164 = 16%
