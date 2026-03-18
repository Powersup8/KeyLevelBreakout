# No Signal Zone — Tier Analysis

**Generated:** 2026-03-05
**Data:** IB parquet (primary) + TV CSV (fallback), 2024-04-25 to 2026-03-04
**Symbols:** AAPL, AMD, AMZN, GLD, GOOGL, META, MSFT, NVDA, QQQ, SLV, SPY, TSLA, TSM

## Overall Summary

- **Total significant moves detected:** 25,304
- **Caught (signal within ±15min):** 461 (1.8%)
- **Missed (No Signal Zone):** 24,843 (98.2%)
- **Total missed ATR:** 42713.2
- **Avg missed move magnitude:** 1.72 ATR

- **Signal date range:** 2026-01-20 to 2026-02-27 (28 days)
- **Move date range:** 2024-04-25 to 2026-03-04 (451 days)
- **Overlapping days:** 28
- **Days with moves but NO signals:** 423 (these are all auto-MISSED)

### Fair Comparison (overlapping dates only)
- **Missed moves on overlapping dates:** 1,979 (fair comparison)
- **Missed moves on non-overlap dates:** 22,864 (no signals to compare)

*All analysis below uses ONLY overlapping dates for fair comparison.*

## Tier Breakdown

| Tier | Criteria | Count | Total ATR | Avg Mag | Avg Duration |
|------|----------|------:|----------:|--------:|-------------:|
| S | ≥2.0 ATR | 538 | 1316.3 | 2.45 | 3.6 bars |
| A | 1.0-2.0 ATR | 1,285 | 1928.2 | 1.50 | 3.4 bars |
| B | 0.5-1.0 ATR | 156 | 134.6 | 0.86 | 3.4 bars |

## Per-Tier Indicator Profiles

| Metric | Tier S | Tier A | Tier B | Our Signals | Our GOOD |
|--------|-------:|-------:|-------:|------------:|---------:|
| EMA Aligned % | 37.5 | 38.3 | 34.6 | 94.3 | 97.4 |
| VWAP Aligned % | 48.9 | 44.8 | 36.5 | 96.2 | 95.2 |
| Regime Score 2 % | 36.2 | 34.7 | 29.5 | — | — |
| Regime Score 0 % | 49.8 | 51.6 | 58.3 | — | — |
| Bear Direction % | 45.9 | 49.9 | 59.0 | 50.8 | 65.4 |
| Avg Vol Ratio | 0.9 | 0.8 | 0.7 | — | — |
| Avg ADX | 17.9 | 13.5 | 7.7 | 26.4 | 26.2 |

## Time Distribution (Coarse — matches signal buckets)

| Time Bucket | Missed S | Missed A | Missed B | Our Signals | Our GOOD |
|-------------|:--------:|:--------:|:--------:|:-----------:|:--------:|
| 9:30-10:00 | 1% | 4% | 14% | 57% | 48% |
| 10:00-11:00 | 15% | 23% | 38% | 20% | 24% |
| 11:00-12:00 | 19% | 23% | 17% | 2% | 4% |
| 12:00+ | 64% | 50% | 31% | 20% | 23% |

## Time Distribution (Fine — 30min buckets)

| Time Bucket | Missed S | Missed A | Missed B | Missed All |
|-------------|:--------:|:--------:|:--------:|:----------:|
| 9:30-10:00 | 1% | 4% | 14% | 4% |
| 10:00-10:30 | 7% | 9% | 19% | 9% |
| 10:30-11:00 | 9% | 14% | 19% | 13% |
| 11:00-12:00 | 19% | 23% | 17% | 21% |
| 12:00-14:00 | 35% | 30% | 20% | 31% |
| 14:00-16:00 | 29% | 21% | 12% | 22% |

## Symbol Distribution (Missed Moves)

| Symbol | Tier S | Tier A | Tier B | Total Missed | Missed ATR |
|--------|-------:|-------:|-------:|-------------:|-----------:|
| AAPL | 47 | 96 | 15 | 158 | 263.6 |
| AMD | 32 | 108 | 20 | 160 | 255.1 |
| AMZN | 53 | 109 | 10 | 172 | 305.0 |
| GLD | 41 | 85 | 6 | 132 | 230.9 |
| GOOGL | 37 | 115 | 24 | 176 | 288.1 |
| META | 46 | 93 | 12 | 151 | 258.3 |
| MSFT | 55 | 96 | 14 | 165 | 291.0 |
| NVDA | 37 | 90 | 19 | 146 | 241.7 |
| QQQ | 41 | 102 | 6 | 149 | 256.5 |
| SLV | 43 | 82 | 8 | 133 | 236.7 |
| SPY | 28 | 95 | 4 | 127 | 219.2 |
| TSLA | 47 | 102 | 11 | 160 | 279.6 |
| TSM | 31 | 112 | 7 | 150 | 253.2 |

## Catchability Analysis

Which missed moves match our KNOWN edge (EMA aligned + regime 2 + morning)?

| Match Level | Count | % of Missed | ATR Sum | Avg Mag |
|-------------|------:|------------:|--------:|--------:|
| Full (EMA + Regime 2 + Morning) | 179 | 9.0% | 295.0 | 1.65 |
| Partial (EMA + Regime 2, any time) | 687 | 34.7% | 1185.9 | 1.73 |
| EMA Only | 748 | 37.8% | 1276.6 | 1.71 |
| No EMA (genuinely outside edge) | 1,231 | 62.2% | 2102.5 | 1.71 |

### Per-Tier Catchability

| Tier | Total | Full Match | % | EMA Gate Would Block |
|------|------:|-----------:|--:|---------------------:|
| S | 538 | 43 | 8% | 336 (62%) |
| A | 1285 | 115 | 9% | 793 (62%) |
| B | 156 | 21 | 13% | 102 (65%) |

## EMA Gate Impact

Our v3.0 EMA gate filters out non-EMA signals. How many missed moves would it also block?

- **EMA-aligned missed moves:** 748 (37.8%) — 1276.6 ATR
- **Non-EMA missed moves:** 1,231 (62.2%) — 2102.5 ATR

If we expanded our indicator to catch EMA-aligned moves in the No Signal Zone,
we'd target 748 moves worth 1276.6 ATR.
The 1,231 non-EMA moves (2102.5 ATR) are genuinely outside our edge.

## Top 20 Missed Tier S Moves

| # | Symbol | Date | Time | Dir | Mag | EMA | Regime | Vol | ADX |
|---|--------|------|------|-----|----:|:---:|-------:|----:|----:|
| 1 | TSLA | 2026-02-17 | 13:05 | bull | 4.33 | N | 0 | 0.6x | 18 |
| 2 | TSM | 2026-01-21 | 11:10 | bear | 4.06 | N | 0 | 0.9x | 0 |
| 3 | AAPL | 2026-01-22 | 13:55 | bull | 3.98 | Y | 2 | 1.6x | 13 |
| 4 | SPY | 2026-02-26 | 13:30 | bull | 3.83 | N | 0 | 2.5x | 38 |
| 5 | META | 2026-02-06 | 12:10 | bull | 3.69 | N | 1 | 0.6x | 23 |
| 6 | TSM | 2026-02-23 | 14:10 | bear | 3.64 | N | 1 | 0.8x | 12 |
| 7 | GLD | 2026-02-13 | 11:10 | bull | 3.63 | N | 1 | 0.7x | 0 |
| 8 | AMZN | 2026-02-23 | 13:20 | bear | 3.63 | N | 1 | 0.9x | 40 |
| 9 | QQQ | 2026-02-26 | 13:30 | bull | 3.63 | N | 0 | 1.7x | 41 |
| 10 | AMD | 2026-02-26 | 13:15 | bull | 3.62 | N | 0 | 0.9x | 23 |
| 11 | AMZN | 2026-01-26 | 15:35 | bear | 3.60 | N | 0 | 1.0x | 11 |
| 12 | AMZN | 2026-02-04 | 15:35 | bear | 3.59 | N | 1 | 1.4x | 17 |
| 13 | AMZN | 2026-01-27 | 13:10 | bull | 3.49 | Y | 2 | 0.8x | 24 |
| 14 | AMZN | 2026-02-19 | 13:40 | bull | 3.45 | N | 0 | 0.7x | 18 |
| 15 | MSFT | 2026-01-21 | 11:10 | bear | 3.40 | Y | 2 | 0.7x | 0 |
| 16 | META | 2026-01-22 | 12:25 | bull | 3.40 | Y | 2 | 1.2x | 51 |
| 17 | MSFT | 2026-01-20 | 14:30 | bull | 3.37 | N | 0 | 1.0x | 14 |
| 18 | META | 2026-02-11 | 10:25 | bull | 3.36 | N | 0 | 0.6x | 0 |
| 19 | TSLA | 2026-02-05 | 14:25 | bear | 3.36 | N | 0 | 1.1x | 14 |
| 20 | AMZN | 2026-02-26 | 13:30 | bull | 3.31 | N | 0 | 1.2x | 43 |

## Top 20 Missed Tier S Moves (ALL dates)

| # | Symbol | Date | Time | Dir | Mag | EMA | Regime | Vol | ADX |
|---|--------|------|------|-----|----:|:---:|-------:|----:|----:|
| 1 | SPY | 2025-10-10 | 10:45 | bear | 11.77 | N | 0 | 0.4x | 0 |
| 2 | AMD | 2025-10-02 | 15:40 | bear | 10.70 | N | 0 | 1.4x | 16 |
| 3 | SPY | 2025-05-27 | 13:10 | bull | 10.70 | Y | 2 | 0.7x | 53 |
| 4 | SPY | 2025-05-19 | 11:40 | bear | 8.85 | N | 0 | 1.3x | 0 |
| 5 | TSM | 2025-12-01 | 14:25 | bull | 8.31 | N | 1 | 1.6x | 20 |
| 6 | AMZN | 2024-04-30 | 12:15 | bear | 6.89 | Y | 2 | 1.1x | 44 |
| 7 | GOOGL | 2025-04-17 | 10:10 | bear | 6.68 | Y | 2 | 0.4x | 0 |
| 8 | AAPL | 2025-09-02 | 15:00 | bull | 6.06 | Y | 1 | 3.6x | 23 |
| 9 | GLD | 2025-02-27 | 09:30 | bear | 5.84 | N | 1 | 1.0x | 0 |
| 10 | NVDA | 2025-11-28 | 13:00 | bear | 5.71 | Y | 2 | 5.9x | 36 |
| 11 | SLV | 2025-09-23 | 14:40 | bear | 5.69 | Y | 2 | 0.6x | 19 |
| 12 | GLD | 2025-12-18 | 10:55 | bull | 5.32 | Y | 2 | 0.4x | 0 |
| 13 | AMD | 2025-01-29 | 12:35 | bear | 5.23 | N | 0 | 1.1x | 25 |
| 14 | AMZN | 2024-09-24 | 15:40 | bull | 5.12 | Y | 2 | 1.6x | 17 |
| 15 | SPY | 2025-05-20 | 14:05 | bear | 5.12 | Y | 2 | 0.9x | 15 |
| 16 | AAPL | 2025-09-09 | 13:45 | bear | 5.09 | N | 1 | 1.1x | 26 |
| 17 | SLV | 2025-12-30 | 14:25 | bear | 5.08 | N | 0 | 0.5x | 23 |
| 18 | AMZN | 2025-06-18 | 15:40 | bear | 5.04 | Y | 2 | 1.1x | 20 |
| 19 | GLD | 2024-07-29 | 11:00 | bear | 4.97 | Y | 2 | 0.6x | 0 |
| 20 | SLV | 2025-11-07 | 11:15 | bull | 4.92 | N | 0 | 0.7x | 0 |

## Conclusions

### ATR Budget (overlapping dates)
- **Total missed:** 3379.1 ATR across 1,979 moves
- **Catchable (EMA + Regime 2):** 1185.9 ATR (35%)
- **EMA-only (partial edge):** 90.6 ATR (3%)
- **Outside our edge (no EMA):** 2102.5 ATR (62%)

### Time Split
- **Morning missed (before 11:00):** 516 moves, 779.2 ATR
- **Afternoon missed (after 11:00):** 1,463 moves, 2599.9 ATR

### Key Takeaways

1. **EMA alignment:** 38% of missed moves are EMA-aligned (vs 94% of our signals, 97% of GOOD)
2. **Regime score 2:** 35% of missed moves have full regime alignment
3. **Direction:** 50% bear (vs 51% of our signals)
4. **Morning EMA rate:** 41% vs **Afternoon EMA rate:** 37%
5. **Tier S home runs:** 538 moves, 38% EMA aligned, 36% regime 2
