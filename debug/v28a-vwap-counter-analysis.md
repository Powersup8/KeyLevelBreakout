# v2.8a VWAP Counter-Trend BRK Analysis (2026-03-04)

## Discovery
BRK signals where price is on the **opposite side of VWAP** from the breakout direction show dramatically better performance than aligned signals.

## The Signal
Price below VWAP → breaks UP through key level (or above VWAP → breaks DOWN). EMA confirms direction. This is a **pullback-to-key-level** pattern: trend intact (EMA), VWAP overshoot creates entry, level break confirms resumption.

## Core Stats (n=36, 6 months, 10 symbols, 26 days)

| | Counter | Best Aligned Combo | All Aligned |
|---|---|---|---|
| n | 36 | 350 | 2,178 |
| MFE | 1.154 | 1.232 | 0.783 |
| MAE | **0.223** | 0.958 | 0.791 |
| MFE/MAE | **5.17x** | 1.29x | 0.99x |
| Win% | **83.3%** | 52.9% | 48.8% |

MFE is comparable but **MAE is 3.5x lower** — median MAE only 0.110 ATR.

## Statistical Significance

- Binomial test: p = 0.000019
- Mann-Whitney U (MFE): p = 0.000166
- Bootstrap 95% CI for win rate: [69.4%, 94.4%]
- Lower bound (69%) still exceeds aligned baseline (49%)

## Breakdowns

### By Level Type
| Level | n | MFE | Win% |
|-------|---|-----|------|
| Yest H/L | 27 | 1.226 | 89% |
| PM H/L | 9 | 0.937 | 67% |

### By Direction
| Dir | n | MFE | Win% |
|-----|---|-----|------|
| Bear counter (above VWAP, break down) | 13 | 1.412 | 92% |
| Bull counter (below VWAP, break up) | 23 | 1.008 | 78% |

### By Volume
| Vol | n | MFE | Win% |
|-----|---|-----|------|
| <2x | 9 | 1.854 | 89% |
| 2-5x | 12 | 1.063 | 75% |
| 5-10x | 5 | 0.880 | 80% |
| 10x+ | 10 | 0.770 | 90% |

### By Hour
| Hour | n | MFE | Win% |
|------|---|-----|------|
| 9:xx | 28 | 1.022 | 82% |
| 10:xx | 6 | 2.023 | 83% |

### By Big-Move Flag
| | n | MFE | Win% |
|--|---|-----|------|
| Normal bar | 12 | 1.545 | 83% |
| ⚡ Big-move | 24 | 0.958 | 83% |

### By Symbol
| Symbol | n | MFE | Win% |
|--------|---|-----|------|
| TSLA | 4 | 2.102 | 100% |
| META | 2 | 2.326 | 100% |
| AMD | 2 | 1.389 | 100% |
| SPY | 5 | 1.277 | 80% |
| GOOGL | 5 | 1.005 | 80% |
| AAPL | 9 | 0.905 | 78% |
| MSFT | 3 | 0.897 | 100% |
| NVDA | 2 | 0.854 | 50% |
| AMZN | 3 | 0.440 | 67% |
| QQQ | 1 | 0.427 | 100% |

### By Month (consistency check)
| Month | n | MFE | Win% |
|-------|---|-----|------|
| 2025-10 | 9 | 0.526 | 89% |
| 2025-11 | 6 | 1.150 | 50% |
| 2025-12 | 6 | 0.904 | 67% |
| 2026-01 | 5 | 1.073 | 100% |
| 2026-02 | 10 | 1.911 | 100% |

## Best Variant
Bear counter at Yesterday Low, 10:xx, normal bar size, vol <5x. Bearish trend pullback above VWAP that slices down through yesterday's low.

## Frequency
~1-2 per week across all symbols. 22% of trading days have at least one.

## Key Insight
100% of counter-trend BRKs have EMA aligned with trade direction (but so do all aligned BRKs — EMA alignment is a prerequisite in the indicator). The differentiator is VWAP position: when price has overshot past VWAP against the trend, the subsequent level break is a **trend resumption** signal with minimal drawdown.

## Limitation
n=36 is statistically significant (p < 0.0002) for the overall finding. Sub-breakdowns (Yest > PM, bear > bull) need more observations to confirm.

## Data Files
- `debug/vwap_counter_analysis.py` — initial analysis script
- `debug/vwap_counter_deep.py` — deep analysis with stats tests
- Source: `debug/v28a-signals.csv` + `debug/v28a-follow-through.csv`
