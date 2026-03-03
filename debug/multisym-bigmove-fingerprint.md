# Multi-Symbol Big-Move Fingerprint (2x 5m-ATR)
Period: 2025-12-15 to 2026-03-03 | Symbols: 13 | Total moves: 2069

## Per-Symbol Overview

| Symbol | n | Runners | Fakeouts | Runner% | Avg MFE | Avg Vol | Avg PreVolRamp | Per Day |
|--------|---|---------|----------|---------|---------|---------|----------------|---------|
| SPY | 156 | 105 | 5 | 67% | 2.16 | 4.8x | 5.5x | 3.1 |
| AAPL | 197 | 124 | 15 | 63% | 1.86 | 5.6x | 18.8x | 3.7 |
| AMD | 168 | 116 | 8 | 69% | 2.09 | 5.9x | 5.9x | 3.2 |
| AMZN | 167 | 115 | 9 | 69% | 1.87 | 5.6x | 9.7x | 3.2 |
| GLD | 114 | 70 | 5 | 61% | 1.69 | 3.9x | 1.9x | 2.5 |
| GOOGL | 186 | 130 | 12 | 70% | 2.05 | 5.6x | 9.3x | 3.5 |
| META | 178 | 127 | 8 | 71% | 2.23 | 5.8x | 9.6x | 3.4 |
| MSFT | 175 | 119 | 8 | 68% | 2.06 | 5.7x | 6.2x | 3.3 |
| NVDA | 175 | 110 | 12 | 63% | 2.03 | 5.3x | 5.2x | 3.3 |
| QQQ | 181 | 130 | 5 | 72% | 2.58 | 4.8x | 4.5x | 3.5 |
| SLV | 76 | 43 | 3 | 57% | 1.71 | 4.0x | 1.4x | 1.9 |
| TSLA | 161 | 107 | 6 | 66% | 1.83 | 5.7x | 7.1x | 3.0 |
| TSM | 135 | 51 | 0 | 38% | 2.94 | 3.2x | 0.9x | 2.7 |
| **ALL** | **2069** | **1347** | **96** | **65%** | **2.07** | **5.2x** | **7.3x** | **39.0** |

## Cross-Validation: Do TSLA Findings Generalize?

### Finding 1: Pre-Move Volume Ramp
*TSLA: runners 7.6x ramp vs fakeouts 1.07x (+6.55 gap)*

| Symbol | Runner avg | Fakeout avg | Gap | Validates? |
|--------|-----------|------------|-----|-----------|
| SPY | 5.9x | 4.2x | +1.7 | YES |
| AAPL | 5.2x | 5.5x | -0.3 | NO |
| AMD | 6.2x | 1.1x | +5.1 | YES |
| AMZN | 11.1x | 1.2x | +9.9 | YES |
| GLD | 2.2x | 1.9x | +0.3 | NO |
| GOOGL | 10.3x | 3.2x | +7.1 | YES |
| META | 7.4x | 1.0x | +6.4 | YES |
| MSFT | 5.8x | 1.0x | +4.8 | YES |
| NVDA | 5.3x | 8.2x | -2.9 | NO |
| QQQ | 4.2x | 1.1x | +3.2 | YES |
| SLV | 1.6x | 1.5x | +0.0 | NO |
| TSLA | 7.6x | 1.0x | +6.5 | YES |
| TSM | 0.7x | — | — | n/a (no fakeouts) |

### Finding 2: ADX (runners higher)
*TSLA: runners 28.4 vs fakeouts 22.6 (+5.8 gap)*

| Symbol | Runner avg | Fakeout avg | Gap | Validates? |
|--------|-----------|------------|-----|-----------|
| SPY | 25.5 | 24.3 | +1.2 | NO |
| AAPL | 28.2 | 26.0 | +2.2 | YES |
| AMD | 30.3 | 28.4 | +1.9 | NO |
| AMZN | 26.4 | 21.5 | +4.9 | YES |
| GLD | 28.8 | 34.9 | -6.1 | NO |
| GOOGL | 27.5 | 22.0 | +5.4 | YES |
| META | 25.8 | 18.2 | +7.6 | YES |
| MSFT | 27.2 | 28.1 | -1.0 | NO |
| NVDA | 29.4 | 28.9 | +0.5 | NO |
| QQQ | 28.0 | 27.8 | +0.2 | NO |
| SLV | 32.0 | 40.3 | -8.3 | NO |
| TSLA | 28.4 | 22.7 | +5.8 | YES |
| TSM | 24.6 | — | — | n/a |

### Finding 3: 5-Min P&L Positive (strongest predictor)
*TSLA: 66% runners positive at 5min vs 0% fakeouts*

| Symbol | Runner 5m+ | Fakeout 5m+ | Gap | Validates? |
|--------|-----------|------------|-----|-----------|
| SPY | 62% | 0% | +62% | YES |
| AAPL | 63% | 0% | +63% | YES |
| AMD | 55% | 0% | +55% | YES |
| AMZN | 56% | 0% | +56% | YES |
| GLD | 64% | 0% | +64% | YES |
| GOOGL | 55% | 0% | +55% | YES |
| META | 67% | 0% | +67% | YES |
| MSFT | 64% | 0% | +64% | YES |
| NVDA | 63% | 0% | +63% | YES |
| QQQ | 65% | 0% | +65% | YES |
| SLV | 65% | 0% | +65% | YES |
| TSLA | 66% | 0% | +66% | YES |
| TSM | 61% | — | — | n/a |

### Finding 4: Gap Down → More Runners
*TSLA: gap down 21% runners vs gap up 14%*

| Symbol | Gap Down Runner% | Gap Up Runner% | Gap | Validates? |
|--------|-----------------|----------------|-----|-----------|
| SPY | 69% (n=55) | 71% (n=89) | -2% | FLAT |
| AAPL | 62% (n=86) | 65% (n=83) | -3% | NO |
| AMD | 80% (n=59) | 67% (n=95) | +12% | YES |
| AMZN | 78% (n=63) | 66% (n=74) | +12% | YES |
| GLD | 44% (n=32) | 73% (n=73) | -29% | NO |
| GOOGL | 73% (n=74) | 71% (n=92) | +2% | FLAT |
| META | 68% (n=84) | 74% (n=74) | -6% | NO |
| MSFT | 68% (n=75) | 72% (n=83) | -4% | NO |
| NVDA | 61% (n=62) | 67% (n=85) | -6% | NO |
| QQQ | 77% (n=78) | 69% (n=91) | +8% | YES |
| SLV | 59% (n=22) | 59% (n=51) | +0% | FLAT |
| TSLA | 69% (n=62) | 66% (n=89) | +3% | YES |
| TSM | 44% (n=50) | 24% (n=72) | +20% | YES |

### Finding 5: Morning 9:30-10 = Best Time
*TSLA: 20% runner rate at open vs <10% afternoon*

| Symbol | 9:30-10 Runner% | 10-11 Runner% | 14-16 Runner% | Morning edge? |
|--------|----------------|---------------|---------------|--------------|
| SPY | 72% (n=82) | 70% (n=23) | 54% (n=41) | YES |
| AAPL | 74% (n=117) | 33% (n=9) | 48% (n=64) | YES |
| AMD | 74% (n=138) | 67% (n=6) | 43% (n=21) | YES |
| AMZN | 74% (n=113) | 100% (n=6) | 48% (n=42) | YES |
| GLD | 56% (n=34) | 71% (n=28) | 58% (n=31) | NO/FLAT |
| GOOGL | 76% (n=135) | 67% (n=12) | 47% (n=32) | YES |
| META | 80% (n=122) | 70% (n=10) | 49% (n=39) | YES |
| MSFT | 75% (n=118) | 88% (n=8) | 48% (n=44) | YES |
| NVDA | 68% (n=120) | 60% (n=5) | 53% (n=45) | YES |
| QQQ | 77% (n=119) | 60% (n=20) | 60% (n=35) | YES |
| SLV | 43% (n=30) | 67% (n=9) | 71% (n=17) | NO/FLAT |
| TSLA | 69% (n=121) | 78% (n=9) | 48% (n=23) | YES |
| TSM | 42% (n=104) | 80% (n=5) | 10% (n=21) | YES |

## Combined Feature Ranking (All 13 Symbols)

| Metric | All | Runners | Fakeouts | Gap | Useful? |
|--------|-----|---------|----------|-----|---------|
| Avg MFE | 2.07 | 2.46 | -0.14 | +2.60 | YES |
| Avg MAE | -1.87 | -1.65 | -3.12 | +1.47 | YES |
| 5m P&L | 0.07 | 0.32 | -1.60 | +1.92 | YES |
| Vol Ratio | 5.19 | 5.11 | 4.01 | +1.11 | YES |
| Pre Vol Ramp | 7.33 | 6.26 | 3.10 | +3.16 | YES |
| ADX | 27.6 | 27.7 | 25.9 | +1.9 | weak |
| Body % | 56.2 | 55.9 | 63.5 | -7.6 | YES |
| VWAP Dist | -0.06 | -0.05 | 0.09 | -0.13 | weak |
| Pre Compression | 2.48 | 2.59 | 2.20 | +0.39 | weak |
| Pre Dir Pressure | 49.8 | 49.9 | 52.8 | -2.9 | YES |

| Feature | All | Runners | Fakeouts | Gap | Useful? |
|---------|-----|---------|----------|-----|---------|
| EMA aligned | 53% | 53% | 56% | -4% | weak |
| VWAP aligned | 78% | 77% | 81% | -4% | weak |
| Bull direction | 46% | 46% | 48% | -2% | weak |
| 5min P&L positive | 52% | 62% | 0% | +62% | YES |

## Time of Day (All Symbols Combined)

| Time | n | Runners | Fakeouts | Runner% | Avg MFE |
|------|---|---------|----------|---------|---------|
| 09:30-10 | 1353 | 953 | 43 | 70% | 2.36 |
| 10-11 | 150 | 103 | 6 | 69% | 1.75 |
| 11-12 | 28 | 16 | 5 | 57% | 1.71 |
| 12-14 | 83 | 50 | 8 | 60% | 1.26 |
| 14-16 | 455 | 225 | 34 | 49% | 1.41 |

## Pre-Move Volume Ramp (All Symbols)

| Vol Ramp | n | Runner% | Fakeout% | Avg MFE |
|----------|---|---------|----------|---------|
| <0.5 (drying) | 314 | 68% | 3% | 1.92 |
| 0.5-1 (steady) | 490 | 67% | 6% | 1.79 |
| 1-2x (ramping) | 451 | 56% | 7% | 1.64 |
| 2-5x (surging) | 191 | 53% | 4% | 2.04 |
| >5x (explosive) | 316 | 64% | 3% | 2.66 |

## Verdict: What Generalizes?

*(filled in after reviewing data above)*