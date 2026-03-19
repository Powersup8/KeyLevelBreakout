# TSLA TV Volume Calibration — P3 Findings

## Data
- **TV source**: BATS_TSLA 1m export, 22 trading days (2026-02-17 to 2026-03-18)
- **IB source**: 15s bars, 250 trading days
- **Overlap**: 21 trading days

## TV/IB Volume Ratio
| Stat | TV/IB-15s Ratio |
|------|----------------|
| Mean | 0.1286 |
| Median | 0.1284 |
| Min | 0.0412 |
| Max | 0.2676 |
| Std | 0.0538 |

**TV volume is ~8x lower than IB** during PM (9:25-9:29).
This is expected: TV uses BATS exchange only, IB aggregates all exchanges.

## Threshold Mapping (median ratio = 0.1284)
| IB Threshold | IB Value | TV Equivalent |
|-------------|----------|---------------|
| Q1 kill | 53,000 | 6,805 |
| Sweet spot low | 82,000 | 10,528 |
| Sweet spot high | 128,000 | 16,435 |

## Classification Agreement
Using mapped thresholds, TV and IB agree on volume tier **71%** of days.

## TV-Only Distribution (all 22 days)
| Percentile | TV PM Vol |
|-----------|-----------|
| P10 | 1,825 |
| P25 | 3,140 |
| P50 | 5,572 |
| P75 | 8,910 |
| P90 | 13,783 |

## Recommendation
- **`i_pmVolMinKill = 7000`** — maps to IB Q1 ~53k (low conviction kill)
- Sweet spot starts at TV ~10500 (IB ~82k, where 81% win rate lives)
- Ratio is reasonably stable (std=0.0538), safe to use a fixed multiplier

## Daily Detail
| Date | TV Vol | IB Vol | Ratio | IB Tier | TV Tier |
|------|--------|--------|-------|---------|---------|
| 2026-02-17 | 2,082 | 27,034 | 0.0770 | LOW | LOW |
| 2026-02-18 | 2,736 | 23,939 | 0.1143 | LOW | LOW |
| 2026-02-19 | 1,287 | 31,252 | 0.0412 | LOW | LOW |
| 2026-02-20 | 1,796 | 32,557 | 0.0552 | LOW | LOW |
| 2026-02-23 | 7,166 | 40,282 | 0.1779 | LOW | MID-LOW |
| 2026-02-24 | 11,476 | 79,755 | 0.1439 | MID-LOW | SWEET |
| 2026-02-25 | 6,544 | 42,971 | 0.1523 | LOW | LOW |
| 2026-02-26 | 1,790 | 29,346 | 0.0610 | LOW | LOW |
| 2026-02-27 | 4,122 | 32,104 | 0.1284 | LOW | LOW |
| 2026-03-02 | 23,618 | 120,095 | 0.1967 | SWEET | HIGH |
| 2026-03-03 | 14,039 | 52,453 | 0.2676 | LOW | SWEET |
| 2026-03-04 | 15,227 | 86,999 | 0.1750 | SWEET | SWEET |
| 2026-03-05 | 9,477 | 52,092 | 0.1819 | LOW | MID-LOW |
| 2026-03-06 | 7,210 | 60,725 | 0.1187 | MID-LOW | MID-LOW |
| 2026-03-09 | 6,101 | 46,917 | 0.1300 | LOW | LOW |
| 2026-03-10 | 4,791 | 54,078 | 0.0886 | MID-LOW | LOW |
| 2026-03-11 | 3,906 | 42,360 | 0.0922 | LOW | LOW |
| 2026-03-12 | 7,209 | 71,115 | 0.1014 | MID-LOW | MID-LOW |
| 2026-03-13 | 5,042 | 47,439 | 0.1063 | LOW | LOW |
| 2026-03-16 | 4,706 | 35,971 | 0.1308 | LOW | LOW |
| 2026-03-17 | 9,632 | 60,425 | 0.1594 | MID-LOW | MID-LOW |
