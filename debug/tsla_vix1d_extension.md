# TSLA VIX 1d Extension — Full Dataset Regime Conditioning
*Generated: 2026-03-18 | TSLA: 280 days | VIX 1d overlap: 254 days*

Extends VIX conditioning from the 85-day VIX 1h window to the full ~250-day dataset.
Uses **prev-day VIX close** as the pre-open signal (known overnight, before 9:30).

## V1 — VIX Regime by Prev-Day Close (pre-open signal)

| label | n | day_above% | avg_day_chg | worst% | bad% | bull% | hold_5m% |
|---|---|---|---|---|---|---|---|
| All VIX days (baseline) | 254 | 50.8 | 0.34 | 26.0 | 40.6 | 29.1 | 49.6 |
| VIX prev calm | 146 | 46.6 | -0.87 | 28.8 | 43.8 | 27.4 | 47.9 |
| VIX prev moderate | 86 | 59.3 | 2.05 | 19.8 | 33.7 | 30.2 | 50.0 |
| VIX prev fear | 22 | 45.5 | 1.72 | 31.8 | 45.5 | 36.4 | 59.1 |

## V2 — VIX Regime by Same-Day Open (at-open)

| label | n | day_above% | avg_day_chg | worst% | bad% | bull% | hold_5m% |
|---|---|---|---|---|---|---|---|
| All VIX days (baseline) | 255 | 51.0 | 0.34 | 25.9 | 40.4 | 29.0 | 49.8 |
| VIX open calm | 139 | 45.3 | -1.00 | 28.8 | 44.6 | 27.3 | 48.2 |
| VIX open moderate | 92 | 60.9 | 2.21 | 19.6 | 32.6 | 31.5 | 47.8 |
| VIX open fear | 24 | 45.8 | 0.99 | 33.3 | 45.8 | 29.2 | 66.7 |

## V3 — VIX Prev-Day Regime × 5m Rule

| label | n | day_above% | avg_day_chg | worst% | bull% | hold_5m% |
|---|---|---|---|---|---|---|
| VIX calm × 5m=HOLD | 70 | 65.7 | 2.94 | 11.4 | 38.6 | 100 |
| VIX calm × 5m=BAIL | 76 | 28.9 | -4.38 | 44.7 | 17.1 | 0 |
| VIX moderate × 5m=HOLD | 43 | 76.7 | 5.09 | 11.6 | 46.5 | 100 |
| VIX moderate × 5m=BAIL | 43 | 41.9 | -1.00 | 27.9 | 14.0 | 0 |
| VIX fear × 5m=HOLD (thin) | 13 | 53.8 | 4.09 | 23.1 | 38.5 | 100 |
| VIX fear × 5m=BAIL (thin) | 9 | 33.3 | -1.70 | 44.4 | 33.3 | 0 |

## V4 — VIX Day-Over-Day Change (spike detector)

| label | n | avg_vix_chg | day_above% | avg_day_chg | worst% |
|---|---|---|---|---|---|
| Large spike (>+2) (thin) | 14 | 4.20 | 71.4 | 3.85 | 14.3 |
| Small spike (0 to +2) | 129 | 0.48 | 49.6 | 0.39 | 26.4 |
| Flat (-1 to 0) | 96 | -0.28 | 54.2 | 0.09 | 25.0 |
| Drop (<-1) (thin) | 15 | -1.78 | 20.0 | -1.72 | 40.0 |

## V5 — Worst-Day Rate by VIX Tier

| tier | n | worst_day% | bad_day% | avg_day_chg |
|---|---|---|---|---|
| VIX ≤ 15 | 25 | 44.0 | 64.0 | -2.38 |
| VIX 15-20 | 157 | 26.8 | 40.1 | -0.16 |
| VIX 20-25 | 50 | 12.0 | 28.0 | 2.66 |
| VIX > 25 | 22 | 31.8 | 45.5 | 1.72 |

## V6 — HOLD Day Outcomes by VIX Regime (sizing guide)

| VIX range | regime | n | HOLD win% | HOLD avg P&L | worst% | recommendation |
|---|---|---|---|---|---|---|
| 0-18 | calm | 70 | 65.7% | 2.94 | 11.4% | Reduce (complacency) |
| 18-25 | moderate | 43 | 76.7% | 5.09 | 11.6% | Full size (best regime) |
| 25-999 | fear (thin) | 13 | 53.8% | 4.09 | 23.1% | Skip / very small |

## V7 — Summary: Key Findings vs Prior VIX 1h (85 days)

| Metric | VIX 1h (85d, prior) | VIX 1d (this run) |
|---|---|---|
| Calm (<18) day_above% | 40.4% | 46.6% |
| Moderate (18-25) day_above% | 69.0% | 59.3% |
| Fear (>25) day_above% | 22.2% | 45.5% |
| Moderate × HOLD win% | 81.2% | 76.7% |
| Moderate × HOLD avg P&L | +$5.75 | $5.09 |
| n (VIX overlap) | 85 days | 254 days |
