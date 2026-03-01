# Pine Log Inventory -- Unanalyzed Files

14 pine log files not used in the Feb 25 or Feb 26 signal analyses.

## Category A: Feb 27 Data (new day, usable for Feb 27 analysis)

9 files contain Feb 27 signals. Symbol identification verified against BATS candle data.

| Hash | Symbol | Full Range | Feb 27 Coverage | Feb 27 Signals | Lines |
|------|--------|-----------|-----------------|----------------|-------|
| 332ac | SPY | Jan 26 -- Feb 27 | 09:35--15:15 | 14 | 347 |
| e4ccc | AMD | Jan 26 -- Feb 27 | 09:35--15:55 | 20 | 298 |
| c303a | NVDA | Jan 26 -- Feb 27 | 09:35--14:56 | 22 | 310 |
| e923d | TSLA | Jan 26 -- Feb 27 | 09:35--15:55 | 9 | 306 |
| 99efc | TSM | Jan 20 -- Feb 27 | 09:35--13:35 | 6 | 369 |
| 90fcf | SLV | Jan 26 -- Feb 27 | 09:35--13:25 | 8 | 252 |
| b5978 | AMZN | Jan 26 -- Feb 27 | 09:35--15:55 | 14 | 288 |
| 4e22e | GOOGL | Jan 26 -- Feb 27 | 09:35--15:55 | 21 | 317 |
| bc0f1 | META | Jan 20 -- Feb 27 | 09:30--15:55 | 5 | 380 |

**Missing for Feb 27:** AAPL, MSFT, QQQ (not exported yet).

## Category B: Duplicate / Overlapping Exports (no new day)

5 files that only cover dates already analyzed (Jan 20 -- Feb 26). These are re-exports or extended versions of files used in the Feb 25/26 analyses.

| Hash | Symbol | Full Range | Latest Day Covered | Lines | Notes |
|------|--------|-----------|-------------------|-------|-------|
| f8b60 | QQQ | Jan 26 -- Feb 25 | Feb 25 (09:30--09:45) | 225 | Feb 25 QQQ signals |
| 2ca26 | SPY | Jan 20 -- Feb 25 | Feb 25 (09:35--11:45) | 382 | Overlaps 4415c (Feb 25 SPY) |
| 100be | SPY | Jan 20 -- Feb 25 | Feb 25 (09:35--11:45) | 361 | Near-duplicate of 2ca26 |
| ad8bc | AMD | Jan 20 -- Feb 26 | Feb 26 (09:35--09:41) | 424 | Overlaps Feb 25 + Feb 26 AMD |
| b6d10 | NVDA | Jan 26 -- Feb 26 | Feb 26 (09:30--09:50) | 288 | Overlaps Feb 26 NVDA |

## Symbol Identification Method

Symbols were identified by matching pine log OHLC prices on specific dates against BATS candle data files (which contain the ticker name). Key cross-references:
- BATS_TSLA 6cbb7: Feb 27 9:30 O=402.94 -> matches e923d
- BATS_TSM 1768e: Feb 27 9:30 O=370.14 -> matches 99efc
- BATS_NVDA a81b6: Feb 27 9:30 O=181.25 -> matches c303a
- BATS_AMD e859f: Feb 27 9:30 O=200.11 -> matches e4ccc
- BATS_SPY 9d4c2: Feb 27 9:30 O=683.06 -> matches 332ac
- BATS_GOOGL d0e08: Feb 27 9:30 O=304.19 -> matches 4e22e
- BATS_META 4e874: Feb 27 9:30 O=643.45 -> matches bc0f1
- BATS_SLV aa4d1: Feb 27 9:30 O=83.255 -> matches 90fcf
- BATS_AMZN 22e1f: Feb 27 9:30 O=206.83 -> matches b5978
- BATS_QQQ 2db23: Feb 25 8:19 O=610.70 -> matches f8b60
