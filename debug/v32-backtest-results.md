# KLB v3.2 vs v3.1 Backtest Results
**Date:** 2026-03-07
**Period:** Last 30 trading days
**Symbols:** SPY, AAPL, AMD, AMZN, GLD, GOOGL, META, MSFT, NFLX, NVDA, QQQ, SLV, TSLA, TSM, XLE
**Data:** IB 5-minute bars, 14-period ATR from daily

## Overall Summary

| Metric | v3.1 | v3.2 | Delta |
|--------|------|------|-------|
| Total Signals | 1214 | 3350 | +2136 |
| Win Rate | 12.6% | 8.5% | -4.1pp |
| Avg MFE (ATR) | 0.146 | 0.120 | -0.027 |
| Avg MAE (ATR) | 0.108 | 0.111 | +0.003 |
| Net ATR | 46.3 | 30.4 | -15.9 |

## Summary by Change

| Change | v3.1 Signals | v3.1 ATR | v3.2 Signals | v3.2 ATR | Delta ATR |
|--------|:---:|:---:|:---:|:---:|:---:|
| Change 1: ORB L Bull REV Suppress | 234 | +17.3 | 0 | +0.0 | -17.3 |
| Change 2: New Midday Levels | 0 | +0.0 | 1338 | -8.1 | -8.1 |
| Change 3: EXREV Bypass | 0 | +0.0 | 713 | +5.9 | +5.9 |
| Change 4: FADE Resurrection | 0 | +0.0 | 63 | -0.5 | -0.5 |
| Change 5: HIGH→REV Reassignment | 194 | +1.3 | 348 | -1.1 | -2.4 |
| **TOTAL (changes only)** | | | | | **-22.5** |

## Per-Change Detail

### Change 1: ORB L Bull REV Suppress
*Suppress bull REV at ORB Low*

| Metric | v3.1 | v3.2 |
|--------|------|------|
| Signals | 234 | 0 |
| Win Rate | 16.7% | 0.0% |
| Avg MFE | 0.169 | 0.000 |
| Avg MAE | 0.095 | 0.000 |
| Net ATR | +17.3 | +0.0 |

**Top 3 Best:**
- AAPL 2026-02-02 09:35 ORB Low REV bull MFE=0.674 MAE=0.021 P&L=0.654 [GOOD]
- TSM 2026-02-24 09:35 ORB Low REV bull MFE=0.632 MAE=0.045 P&L=0.587 [GOOD]
- AMD 2026-01-23 09:35 ORB Low REV bull MFE=0.575 MAE=0.026 P&L=0.549 [GOOD]

**Top 3 Worst:**
- GLD 2026-01-29 09:55 ORB Low REV bull MFE=0.000 MAE=2.523 P&L=-2.523 [BAD]
- SPY 2026-02-05 15:05 ORB Low REV bull MFE=0.028 MAE=0.379 P&L=-0.351 [BAD]
- XLE 2026-01-28 14:05 ORB Low REV bull MFE=0.021 MAE=0.370 P&L=-0.349 [SCRATCH]

### Change 2: New Midday Levels
*Today Open REV, PD Close REV, Week Open BRK, Month Open BRK*

| Metric | v3.1 | v3.2 |
|--------|------|------|
| Signals | 0 | 1338 |
| Win Rate | 0.0% | 7.2% |
| Avg MFE | 0.000 | 0.113 |
| Avg MAE | 0.000 | 0.119 |
| Net ATR | +0.0 | -8.1 |

**Top 3 Best:**
- SPY 2026-01-29 09:35 Today Open REV bear MFE=0.864 MAE=0.027 P&L=0.837 [GOOD]
- TSM 2026-02-03 09:35 Today Open EXREV bear MFE=0.907 MAE=0.087 P&L=0.819 [GOOD]
- GLD 2026-01-29 09:35 Today Open EXREV bear MFE=0.807 MAE=0.028 P&L=0.778 [GOOD]

**Top 3 Worst:**
- GLD 2026-01-29 10:10 PD Close REV bull MFE=0.019 MAE=1.850 P&L=-1.831 [BAD]
- SLV 2026-01-29 10:05 PD Close REV bull MFE=0.076 MAE=1.403 P&L=-1.327 [BAD]
- TSM 2026-01-29 09:45 PD Close REV bull MFE=0.014 MAE=0.982 P&L=-0.968 [BAD]

**By Level:**
| Level | v3.1 N | v3.2 N | v3.2 Win% | v3.2 ATR |
|-------|:---:|:---:|:---:|:---:|
| Month Open | 0 | 54 | 11.1% | -1.1 |
| PD Close | 0 | 487 | 7.0% | -2.3 |
| Today Open | 0 | 679 | 6.3% | -3.3 |
| Week Open | 0 | 118 | 11.0% | -1.4 |

### Change 3: EXREV Bypass
*Bear REV body<30% bypasses EMA+quality gates*

| Metric | v3.1 | v3.2 |
|--------|------|------|
| Signals | 0 | 713 |
| Win Rate | 0.0% | 7.7% |
| Avg MFE | 0.000 | 0.106 |
| Avg MAE | 0.000 | 0.098 |
| Net ATR | +0.0 | +5.9 |

**Top 3 Best:**
- TSM 2026-02-03 09:35 Today Open EXREV bear MFE=0.907 MAE=0.087 P&L=0.819 [GOOD]
- GLD 2026-01-29 09:35 ORB High EXREV bear MFE=0.807 MAE=0.028 P&L=0.778 [GOOD]
- GLD 2026-01-29 09:35 Today Open EXREV bear MFE=0.807 MAE=0.028 P&L=0.778 [GOOD]

**Top 3 Worst:**
- GOOGL 2026-02-02 09:45 PD Close EXREV bear MFE=0.009 MAE=0.716 P&L=-0.707 [BAD]
- MSFT 2026-01-23 09:55 ORB High EXREV bear MFE=0.000 MAE=0.630 P&L=-0.630 [BAD]
- NVDA 2026-01-27 09:40 PD Close EXREV bear MFE=0.008 MAE=0.632 P&L=-0.625 [BAD]

**By Level:**
| Level | v3.1 N | v3.2 N | v3.2 Win% | v3.2 ATR |
|-------|:---:|:---:|:---:|:---:|
| ORB High | 0 | 175 | 13.7% | +9.7 |
| ORB Low | 0 | 79 | 0.0% | -0.9 |
| PD Close | 0 | 86 | 10.5% | -0.4 |
| PD High | 0 | 89 | 6.7% | +2.1 |
| PD Low | 0 | 68 | 7.4% | -1.0 |
| Today Open | 0 | 119 | 4.2% | -2.9 |
| Week High | 0 | 69 | 7.2% | +1.1 |
| Week Low | 0 | 28 | 3.6% | -2.0 |

### Change 4: FADE Resurrection
*Counter-EMA fail → with-EMA cross back within 6 bars*

| Metric | v3.1 | v3.2 |
|--------|------|------|
| Signals | 0 | 63 |
| Win Rate | 0.0% | 9.5% |
| Avg MFE | 0.000 | 0.129 |
| Avg MAE | 0.000 | 0.138 |
| Net ATR | +0.0 | -0.5 |

**Top 3 Best:**
- TSLA 2026-02-26 10:10 PD Low FADE bear MFE=0.449 MAE=0.000 P&L=0.449 [GOOD]
- TSM 2026-02-04 10:55 PD Low FADE bear MFE=0.396 MAE=0.032 P&L=0.364 [GOOD]
- SLV 2026-01-26 10:45 ORB High FADE bull MFE=0.353 MAE=0.020 P&L=0.333 [GOOD]

**Top 3 Worst:**
- TSLA 2026-02-03 10:10 Week Open FADE bear MFE=0.029 MAE=0.393 P&L=-0.364 [BAD]
- TSLA 2026-02-03 10:10 Month Open FADE bear MFE=0.029 MAE=0.393 P&L=-0.364 [BAD]
- TSLA 2026-02-26 10:30 Week Open FADE bear MFE=0.003 MAE=0.339 P&L=-0.337 [BAD]

**By Level:**
| Level | v3.1 N | v3.2 N | v3.2 Win% | v3.2 ATR |
|-------|:---:|:---:|:---:|:---:|
| Month Open | 0 | 5 | 0.0% | -0.6 |
| ORB High | 0 | 11 | 9.1% | +0.9 |
| ORB Low | 0 | 13 | 0.0% | -0.3 |
| PD High | 0 | 6 | 0.0% | -0.1 |
| PD Low | 0 | 11 | 27.3% | +0.6 |
| Week High | 0 | 1 | 0.0% | -0.3 |
| Week Low | 0 | 6 | 33.3% | +0.2 |
| Week Open | 0 | 10 | 0.0% | -0.8 |

### Change 5: HIGH→REV Reassignment
*Bull BRK at HIGH levels → Bull REV*

| Metric | v3.1 | v3.2 |
|--------|------|------|
| Signals | 194 | 348 |
| Win Rate | 5.2% | 4.9% |
| Avg MFE | 0.113 | 0.092 |
| Avg MAE | 0.107 | 0.095 |
| Net ATR | +1.3 | -1.1 |

**Top 3 Best:**
- MSFT 2026-01-23 09:35 PD High REV bull MFE=0.830 MAE=0.020 P&L=0.810 [GOOD]
- AMZN 2026-02-20 09:35 PD High REV bull MFE=0.485 MAE=0.014 P&L=0.471 [GOOD]
- MSFT 2026-02-10 09:35 PD High REV bull MFE=0.479 MAE=0.028 P&L=0.451 [GOOD]

**Top 3 Worst:**
- SLV 2026-01-29 10:00 PD High REV bull MFE=0.042 MAE=1.566 P&L=-1.524 [BAD]
- SLV 2026-01-29 10:00 Week High REV bull MFE=0.042 MAE=1.566 P&L=-1.524 [BAD]
- GOOGL 2026-02-03 09:50 PD High REV bull MFE=0.011 MAE=0.452 P&L=-0.442 [BAD]

**By Level:**
| Level | v3.1 N | v3.2 N | v3.2 Win% | v3.2 ATR |
|-------|:---:|:---:|:---:|:---:|
| ORB High | 105 | 175 | 1.1% | -0.3 |
| PD High | 51 | 102 | 9.8% | +0.9 |
| Week High | 38 | 71 | 7.0% | -1.7 |

## Per-Symbol Breakdown

| Symbol | v3.1 Signals | v3.1 Win% | v3.1 ATR | v3.2 Signals | v3.2 Win% | v3.2 ATR | Delta ATR |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| SPY | 104 | 18.3% | +5.3 | 289 | 13.8% | +6.8 | +1.5 |
| AAPL | 64 | 7.8% | +1.8 | 208 | 1.4% | -2.7 | -4.5 |
| AMD | 81 | 16.0% | +5.0 | 201 | 8.5% | +1.2 | -3.7 |
| AMZN | 78 | 9.0% | +2.4 | 208 | 7.2% | -2.2 | -4.7 |
| GLD | 89 | 12.4% | -0.7 | 232 | 7.8% | +2.6 | +3.3 |
| GOOGL | 77 | 7.8% | +2.6 | 247 | 6.1% | +0.8 | -1.8 |
| META | 94 | 7.4% | +1.7 | 222 | 4.5% | -1.6 | -3.3 |
| MSFT | 76 | 9.2% | +3.0 | 191 | 7.3% | +4.7 | +1.7 |
| NFLX | 51 | 5.9% | +0.2 | 169 | 7.1% | +3.3 | +3.1 |
| NVDA | 88 | 13.6% | +3.5 | 231 | 10.0% | +4.5 | +0.9 |
| QQQ | 80 | 11.2% | +1.0 | 248 | 12.1% | +2.7 | +1.7 |
| SLV | 68 | 11.8% | +4.1 | 191 | 9.4% | +1.9 | -2.1 |
| TSLA | 91 | 9.9% | +5.0 | 281 | 5.7% | +0.7 | -4.3 |
| TSM | 78 | 24.4% | +6.8 | 207 | 13.5% | +3.3 | -3.5 |
| XLE | 95 | 18.9% | +4.7 | 225 | 12.0% | +4.4 | -0.3 |

## Time-of-Day Analysis

### v3.2 New Midday Level Signals by Hour

| Hour (ET) | Signals | Win Rate | Avg MFE | Avg MAE | Net ATR |
|:---------:|:-------:|:--------:|:-------:|:-------:|:-------:|
| 09:00 | 414 | 14.0% | 0.171 | 0.183 | -5.0 |
| 10:00 | 170 | 12.9% | 0.146 | 0.157 | -1.9 |
| 11:00 | 83 | 4.8% | 0.104 | 0.086 | +1.5 |
| 12:00 | 116 | 4.3% | 0.091 | 0.081 | +1.2 |
| 13:00 | 136 | 1.5% | 0.072 | 0.082 | -1.3 |
| 14:00 | 165 | 1.8% | 0.073 | 0.077 | -0.7 |
| 15:00 | 254 | 0.8% | 0.059 | 0.067 | -2.0 |

### All v3.2 Signals by Hour

| Hour (ET) | v3.1 Signals | v3.2 Signals | v3.2 Win% | v3.2 Net ATR |
|:---------:|:---:|:---:|:---:|:---:|
| 09:00 | 494 | 957 | 19.4% | +31.9 |
| 10:00 | 196 | 481 | 11.6% | +0.5 |
| 11:00 | 53 | 221 | 6.3% | +3.0 |
| 12:00 | 81 | 304 | 3.3% | +0.7 |
| 13:00 | 95 | 348 | 1.1% | -3.0 |
| 14:00 | 124 | 425 | 2.4% | +0.1 |
| 15:00 | 171 | 614 | 1.0% | -2.9 |

## Cross-Symbol Analysis: Which Symbols Benefit Most

### Change 1: ORB L Bull REV Suppress

| Symbol | N | Win% | Net ATR |
|--------|:-:|:----:|:-------:|
| AAPL | 20 | 20.0% | +2.6 |
| AMD | 12 | 16.7% | +1.2 |
| AMZN | 14 | 21.4% | +1.6 |
| GLD | 18 | 5.6% | -1.7 |
| GOOGL | 12 | 8.3% | +1.7 |
| META | 17 | 5.9% | -0.1 |
| MSFT | 16 | 25.0% | +2.7 |
| NFLX | 7 | 14.3% | +0.8 |
| NVDA | 17 | 11.8% | +0.3 |
| QQQ | 18 | 27.8% | +2.4 |
| SLV | 13 | 7.7% | +0.6 |
| SPY | 26 | 15.4% | +1.2 |
| TSLA | 10 | 20.0% | +1.4 |
| TSM | 11 | 27.3% | +1.6 |
| XLE | 23 | 21.7% | +1.1 |

### Change 2: New Midday Levels

| Symbol | N | Win% | Net ATR |
|--------|:-:|:----:|:-------:|
| AAPL | 86 | 1.2% | -1.2 |
| AMD | 86 | 1.2% | -2.1 |
| AMZN | 91 | 4.4% | -1.6 |
| GLD | 72 | 8.3% | -2.4 |
| GOOGL | 106 | 4.7% | -1.0 |
| META | 91 | 3.3% | -0.7 |
| MSFT | 68 | 7.4% | +0.9 |
| NFLX | 65 | 4.6% | +1.0 |
| NVDA | 95 | 7.4% | -2.2 |
| QQQ | 92 | 13.0% | -0.1 |
| SLV | 72 | 12.5% | +1.8 |
| SPY | 115 | 13.0% | +1.6 |
| TSLA | 120 | 5.0% | -2.9 |
| TSM | 77 | 11.7% | -1.5 |
| XLE | 102 | 9.8% | +2.3 |

### Change 3: EXREV Bypass

| Symbol | N | Win% | Net ATR |
|--------|:-:|:----:|:-------:|
| AAPL | 54 | 3.7% | +0.6 |
| AMD | 41 | 9.8% | -1.4 |
| AMZN | 38 | 5.3% | -0.7 |
| GLD | 52 | 7.7% | +2.6 |
| GOOGL | 55 | 0.0% | -2.4 |
| META | 40 | 0.0% | -1.7 |
| MSFT | 54 | 7.4% | +0.4 |
| NFLX | 54 | 11.1% | +1.6 |
| NVDA | 43 | 2.3% | -1.2 |
| QQQ | 56 | 19.6% | +2.5 |
| SLV | 44 | 4.5% | +0.7 |
| SPY | 56 | 14.3% | +2.6 |
| TSLA | 41 | 2.4% | -0.6 |
| TSM | 51 | 15.7% | +2.9 |
| XLE | 34 | 5.9% | +0.1 |

### Change 4: FADE Resurrection

| Symbol | N | Win% | Net ATR |
|--------|:-:|:----:|:-------:|
| AAPL | 2 | 0.0% | +0.0 |
| AMD | 6 | 0.0% | -0.9 |
| AMZN | 5 | 0.0% | -0.2 |
| GLD | 2 | 0.0% | +0.2 |
| GOOGL | 2 | 50.0% | +0.3 |
| META | 1 | 0.0% | -0.2 |
| MSFT | 3 | 0.0% | +0.1 |
| NFLX | 3 | 0.0% | +0.4 |
| NVDA | 5 | 0.0% | +0.1 |
| QQQ | 4 | 0.0% | +0.1 |
| SLV | 10 | 10.0% | -0.8 |
| SPY | 1 | 0.0% | -0.0 |
| TSLA | 9 | 33.3% | +0.1 |
| TSM | 8 | 12.5% | +0.1 |
| XLE | 2 | 0.0% | +0.1 |

### Change 5: HIGH→REV Reassignment

| Symbol | N | Win% | Net ATR |
|--------|:-:|:----:|:-------:|
| AAPL | 18 | 0.0% | -1.1 |
| AMD | 4 | 0.0% | -0.2 |
| AMZN | 24 | 20.8% | +2.5 |
| GLD | 36 | 0.0% | -0.9 |
| GOOGL | 19 | 5.3% | -1.1 |
| META | 24 | 8.3% | +0.2 |
| MSFT | 20 | 15.0% | +2.4 |
| NFLX | 21 | 0.0% | +0.9 |
| NVDA | 22 | 13.6% | +0.8 |
| QQQ | 31 | 6.5% | +0.3 |
| SLV | 26 | 0.0% | -3.0 |
| SPY | 32 | 3.1% | +0.1 |
| TSLA | 26 | 0.0% | +0.1 |
| TSM | 25 | 0.0% | -1.0 |
| XLE | 20 | 0.0% | -1.1 |

## Signal Type Distribution

### v3.1
| Type | N | Win% | Avg MFE | Avg MAE | Net ATR |
|------|:-:|:----:|:-------:|:-------:|:-------:|
| BRK | 436 | 9.2% | 0.128 | 0.122 | +2.4 |
| REV | 778 | 14.5% | 0.157 | 0.100 | +43.9 |

### v3.2
| Type | N | Win% | Avg MFE | Avg MAE | Net ATR |
|------|:-:|:----:|:-------:|:-------:|:-------:|
| BRK | 619 | 9.5% | 0.137 | 0.133 | +2.6 |
| EXREV | 713 | 7.7% | 0.106 | 0.098 | +5.9 |
| FADE | 63 | 9.5% | 0.129 | 0.138 | -0.5 |
| REV | 1955 | 8.5% | 0.119 | 0.108 | +22.5 |
