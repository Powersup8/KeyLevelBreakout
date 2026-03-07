# KLB Move Catalog — Stats Report

Generated: 2026-03-07 09:49

## Dataset Summary
- **Symbols:** 15 (AAPL, AMD, AMZN, GLD, GOOGL, META, MSFT, NFLX, NVDA, QQQ, SLV, SPY, TSLA, TSM, XLE)
- **Date range:** 2024-01-29 to 2026-03-06
- **Trading days:** 528
- **Primary moves (≥0.30 ATR):** 59,677
- **Large moves (≥1.00 ATR):** 12,555
- **Total rows:** 72,232
- **Columns:** 83

## Moves by Symbol
| Symbol | Primary | Large | Avg Mag | Avg Duration |
|--------|---------|-------|---------|-------------|
| AAPL | 3,171 | 196 | 0.44 | 7.0 |
| AMD | 3,005 | 209 | 0.44 | 7.1 |
| AMZN | 3,178 | 219 | 0.43 | 6.8 |
| GLD | 3,191 | 186 | 0.43 | 6.2 |
| GOOGL | 2,948 | 211 | 0.45 | 7.3 |
| META | 3,183 | 228 | 0.44 | 6.9 |
| MSFT | 3,102 | 215 | 0.44 | 7.2 |
| NFLX | 2,952 | 212 | 0.44 | 7.1 |
| NVDA | 3,231 | 218 | 0.43 | 6.4 |
| QQQ | 3,419 | 221 | 0.42 | 6.2 |
| SLV | 3,127 | 176 | 0.42 | 6.2 |
| SPY | 3,573 | 241 | 0.43 | 6.1 |
| TSLA | 3,058 | 205 | 0.43 | 7.0 |
| TSM | 15,501 | 9,620 | 1.33 | 2.0 |
| XLE | 3,038 | 198 | 0.44 | 7.4 |

## Magnitude Distribution (Primary)
- **small:** 36,490 (61.1%)
- **medium:** 13,368 (22.4%)
- **large:** 7,652 (12.8%)
- **mega:** 2,167 (3.6%)

## Speed Distribution (Primary)
- **explosive:** 41,834 (70.1%)
- **steady:** 10,105 (16.9%)
- **grinding:** 7,738 (13.0%)

## Timing Distribution (Primary)
- **open_flush:** 8,122 (13.6%)
- **morning:** 19,814 (33.2%)
- **midday:** 15,397 (25.8%)
- **afternoon:** 16,344 (27.4%)

## Pattern Distribution (Primary)
| Pattern | Count | % | Avg Magnitude |
|---------|-------|---|---------------|
| level_breakout | 24,692 | 41.4% | 0.442 |
| reversal | 14,564 | 24.4% | 0.831 |
| trend_continuation | 13,170 | 22.1% | 0.986 |
| gap_reversal | 3,668 | 6.1% | 0.514 |
| gap_continuation | 3,583 | 6.0% | 0.511 |

## Market Context (Primary)
- **broad_move:** 29,192 (48.9%)
- **sector_move:** 12,348 (20.7%)
- **isolated:** 18,137 (30.4%)

## Level Interaction (Primary)
- **broke_through:** 29,990 (50.3%)
- **no_interaction:** 29,687 (49.7%)

## Most Common Nearest Levels (Primary, top 10)
- **ORB Low:** 11,117
- **Today Open:** 10,263
- **ORB High:** 10,187
- **PD Low:** 4,050
- **PD High:** 3,921
- **PD Mid:** 3,267
- **Week Open:** 3,004
- **PD Close:** 2,535
- **PD Last Hr Low:** 2,531
- **PD Last Hr High:** 2,384

## Moves per Hour (Primary)
| Hour | Count | Avg Magnitude |
|------|-------|---------------|
| 13:00 | 8,145 | 0.644 |
| 14:00 | 14,050 | 0.602 |
| 15:00 | 11,110 | 0.578 |

## Direction Split (Primary)
- **bull:** 29,501 (49.4%)
- **bear:** 30,176 (50.6%)

## Comparison with Existing Datasets
- `enriched-signals.csv`: 1,841 KLB signals (24 days, 13 symbols)
- `big-moves.csv`: 9,596 significant 5m bars
- **This catalog:** 59,677 primary moves (528 days, 15 symbols)
- Join on symbol + overlapping time ranges to see which moves KLB catches/misses
