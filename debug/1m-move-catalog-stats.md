# KLB Move Catalog — Stats Report

Generated: 2026-03-07 09:00

## Dataset Summary
- **Symbols:** 15 (AAPL, AMD, AMZN, GLD, GOOGL, META, MSFT, NFLX, NVDA, QQQ, SLV, SPY, TSLA, TSM, XLE)
- **Date range:** 2024-04-25 to 2026-03-06
- **Trading days:** 453
- **Primary moves (≥0.30 ATR):** 26,662
- **Large moves (≥1.00 ATR):** 1,701
- **Total rows:** 28,363
- **Columns:** 56

## Moves by Symbol
| Symbol | Primary | Large | Avg Mag | Avg Duration |
|--------|---------|-------|---------|-------------|
| AAPL | 2,651 | 147 | 0.43 | 35.2 |
| AMD | 1,603 | 106 | 0.44 | 33.6 |
| AMZN | 2,192 | 140 | 0.43 | 35.8 |
| GLD | 2,038 | 118 | 0.43 | 34.8 |
| GOOGL | 2,165 | 141 | 0.44 | 36.2 |
| META | 1,736 | 122 | 0.43 | 33.6 |
| MSFT | 1,831 | 113 | 0.43 | 34.9 |
| NFLX | 1,035 | 71 | 0.44 | 32.3 |
| NVDA | 1,733 | 103 | 0.43 | 32.5 |
| QQQ | 1,809 | 132 | 0.44 | 31.7 |
| SLV | 1,719 | 96 | 0.42 | 31.4 |
| SPY | 1,856 | 133 | 0.44 | 31.5 |
| TSLA | 1,566 | 97 | 0.43 | 37.5 |
| TSM | 1,043 | 77 | 0.43 | 29.9 |
| XLE | 1,685 | 105 | 0.44 | 34.9 |

## Magnitude Distribution (Primary)
- **small:** 20,675 (77.5%)
- **medium:** 5,845 (21.9%)
- **large:** 141 (0.5%)
- **mega:** 1 (0.0%)

## Speed Distribution (Primary)
- **explosive:** 5,780 (21.7%)
- **steady:** 4,954 (18.6%)
- **grinding:** 15,928 (59.7%)

## Timing Distribution (Primary)
- **open_flush:** 6,500 (24.4%)
- **morning:** 8,741 (32.8%)
- **midday:** 5,897 (22.1%)
- **afternoon:** 5,524 (20.7%)

## Pattern Distribution (Primary)
| Pattern | Count | % | Avg Magnitude |
|---------|-------|---|---------------|
| level_breakout | 12,759 | 47.9% | 0.436 |
| reversal | 5,972 | 22.4% | 0.432 |
| gap_reversal | 3,114 | 11.7% | 0.438 |
| gap_continuation | 2,996 | 11.2% | 0.438 |
| trend_continuation | 1,821 | 6.8% | 0.428 |

## Market Context (Primary)
- **broad_move:** 13,137 (49.3%)
- **sector_move:** 5,434 (20.4%)
- **isolated:** 8,091 (30.3%)

## Level Interaction (Primary)
- **broke_through:** 17,278 (64.8%)
- **no_interaction:** 9,384 (35.2%)

## Most Common Nearest Levels (Primary, top 10)
- **Today Open:** 3,535
- **ORB Low:** 3,010
- **ORB High:** 2,639
- **PD Low:** 2,322
- **PD High:** 2,016
- **Week Open:** 1,727
- **PM Low:** 1,651
- **PM High:** 1,621
- **PD Mid:** 1,614
- **PD Close:** 1,362

## Moves per Hour (Primary)
| Hour | Count | Avg Magnitude |
|------|-------|---------------|
| 09:00 | 9,055 | 0.435 |
| 10:00 | 6,186 | 0.445 |
| 11:00 | 3,532 | 0.436 |
| 12:00 | 2,365 | 0.433 |
| 13:00 | 2,201 | 0.432 |
| 14:00 | 1,902 | 0.424 |
| 15:00 | 1,421 | 0.409 |

## Direction Split (Primary)
- **bull:** 13,160 (49.4%)
- **bear:** 13,502 (50.6%)

## Comparison with Existing Datasets
- `enriched-signals.csv`: 1,841 KLB signals (24 days, 13 symbols)
- `big-moves.csv`: 9,596 significant 5m bars
- **This catalog:** 26,662 primary moves (453 days, 15 symbols)
- Join on symbol + overlapping time ranges to see which moves KLB catches/misses
