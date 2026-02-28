# Unassigned BATS Candle Files Inventory

18 BATS candle CSV files not used in the Feb 25 or Feb 26 signal analyses.

## Group A: Feb 26 Partial Day (pre-market only, ~300 rows, end ~05:00-05:09)

| # | File | Symbol | Date | Time Coverage | Rows |
|---|------|--------|------|---------------|------|
| 1 | `BATS_AMD, 1_88bc2.csv` | AMD | 2026-02-25 to 2026-02-26 | 15:55 Feb 25 -- 05:07 Feb 26 | 301 |
| 2 | `BATS_GOOGL, 1_9ed5b.csv` | GOOGL | 2026-02-25 to 2026-02-26 | 15:32 Feb 25 -- 05:09 Feb 26 | 302 |

## Group B: Feb 26 Partial Day (pre-market through mid-morning, ~430-543 rows)

| # | File | Symbol | Date | Time Coverage | Rows |
|---|------|--------|------|---------------|------|
| 3 | `BATS_SPY, 1_713e6.csv` | SPY | 2026-02-26 | 10:57 -- 19:58 | 517 |
| 4 | `BATS_AMD, 1_9b405.csv` | AMD | 2026-02-26 | 10:57 -- 19:55 | 508 |
| 5 | `BATS_MSFT, 1_02d94.csv` | MSFT | 2026-02-26 | 10:57 -- 19:57 | 530 |
| 6 | `BATS_NVDA, 1_e27fb.csv` | NVDA | 2026-02-26 | 10:57 -- 19:58 | 543 |
| 7 | `BATS_AAPL, 1_94e03.csv` | AAPL | 2026-02-26 | 10:57 -- 19:46 | 434 |
| 8 | `BATS_TSLA, 1_e6afc.csv` | TSLA | 2026-02-26 | 10:57 -- 19:57 | 533 |

Note: These 6 files all start at 10:57 on Feb 26 and include extended-hours data. They contain extra columns (9 EMA, Short Entry, Long Entry, Volume MA) suggesting a newer export format.

## Group C: Feb 24 Partial Day (pre-market / intraday)

| # | File | Symbol | Date | Time Coverage | Rows |
|---|------|--------|------|---------------|------|
| 9 | `BATS_NVDA, 1_a81b6.csv` | NVDA | 2026-02-24 | 08:05 -- 19:58 (Feb 27) | 2685 |
| 10 | `BATS_AMD, 1_e859f.csv` | AMD | 2026-02-24 to 2026-02-27 | 19:44 (Feb 24) -- 19:58 (Feb 27) | 2685 |
| 11 | `BATS_TSLA, 1_6cbb7.csv` | TSLA | 2026-02-24 to 2026-02-27 | 15:27 (Feb 24) -- 19:55 (Feb 27) | 2685 |
| 12 | `BATS_SLV, 1_aa4d1.csv` | SLV | 2026-02-25 to 2026-02-27 | 04:46 (Feb 25) -- 19:53 (Feb 27) | 2696 |
| 13 | `BATS_AMZN, 1_22e1f.csv` | AMZN | 2026-02-24 to 2026-02-27 | 18:56 (Feb 24) -- 19:58 (Feb 27) | 2685 |
| 14 | `BATS_GOOGL, 1_d0e08.csv` | GOOGL | 2026-02-25 to 2026-02-27 | 05:01 (Feb 25) -- 19:52 (Feb 27) | 2685 |
| 15 | `BATS_META, 1_4e874.csv` | META | 2026-02-24 to 2026-02-27 | 11:09 (Feb 24) -- 19:53 (Feb 27) | 2685 |
| 16 | `BATS_MSFT, 1_7a317.csv` (*) | MSFT | 2026-02-25 to 2026-02-27 | 06:27 (Feb 25) -- 19:45 (Feb 27) | 2685 (*) |
| 17 | `BATS_TSM, 1_1768e.csv` | TSM | 2026-02-25 to 2026-02-27 | 07:15 (Feb 25) -- 19:58 (Feb 27) | 2685 |

(*) Note: `BATS_MSFT, 1_7a317.csv` -- hash `7a317` was listed as used in Feb 26 analysis but also appears in this newer glob. Included here for completeness as a multi-day file (Feb 25-27).

## Group D: Feb 24 to Feb 26 (large, ~1438 rows)

| # | File | Symbol | Date | Time Coverage | Rows |
|---|------|--------|------|---------------|------|
| 18 | `BATS_AMD, 1_3e32c.csv` | AMD | 2026-02-24 to 2026-02-26 | 16:26 (Feb 24) -- 09:40 (Feb 26) | 1438 |

## Group E: Multi-day Full (Feb 24-27, ~2685-3274 rows)

| # | File | Symbol | Date | Time Coverage | Rows |
|---|------|--------|------|---------------|------|
| 19 | `BATS_SPY, 1_9d4c2.csv` | SPY | 2026-02-24 to 2026-02-27 | 06:27 (unknown start) -- 19:58 (Feb 27) | 3274 |

Note: SPY has the largest file (3274 rows) spanning ~4 days of data.

## Summary by Symbol

| Symbol | New Files | Hashes |
|--------|-----------|--------|
| AMD | 4 | 88bc2, 3e32c, 9b405, e859f |
| SPY | 2 | 713e6, 9d4c2 |
| NVDA | 2 | e27fb, a81b6 |
| TSLA | 2 | e6afc, 6cbb7 |
| GOOGL | 2 | 9ed5b, d0e08 |
| MSFT | 2 | 02d94, 7a317(*) |
| AAPL | 1 | 94e03 |
| AMZN | 1 | 22e1f |
| META | 1 | 4e874 |
| SLV | 1 | aa4d1 |
| TSM | 1 | 1768e |
