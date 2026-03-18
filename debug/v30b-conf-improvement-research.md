# v3.0b CONF Improvement Research
**Generated:** 2026-03-05 15:45
**Data:** 356 BRK signals across 8 symbols, 27 trading days
**Parquet match:** 177 signals with follow-through data

## 1. Executive Summary

**Key Findings:**

1. **CONF pass rate is already very high:** 313/335 = 93.4% (auto-R1 handles 286, auto-promote handles 27)
2. **Only 22 CONF failures** across 356 BRK signals in the v3.0b dataset.
3. **21 signals** had no CONF check at all (dimmed/suppressed). ALL are EMA-aligned.
4. **All 22 CONF failures are EMA-aligned and VWAP-aligned** -- the EMA hard gate already removed non-EMA signals.
5. **CONF failures cluster after 10:30** -- exactly where Auto-R1 stops. 100% pass before 10:00, drops to 30% at 12:00.
6. **Volume is the key differentiator:** Vol >= 3x = 98.3% CONF pass. All 22 failures have vol < 3.2x.
7. **CONF fail win rate: 56% at 30m** -- over half would have been profitable.
   Avg PnL: +0.0555 ATR. These are NOT universally bad.

**Best Scenario: C (Auto-R1 All-Day)**
- Extend EMA-based auto-confirm to all hours (remove time<10:30 restriction)
- Flips 43 signals from fail/dimmed to confirmed
- Net 30m PnL of flipped signals: +1.112 ATR
- HOLD filter remains effective as the safety net
- Zero code complexity increase (simpler rule: EMA = auto-confirm, period)

**Alternative: A (Auto-R1 to 11:00)**
- Conservative option: extend by just 30 min
- Captures the 10:30-10:59 boundary fails which are highest quality
- Lower risk, lower reward

**Warning:** Only 177/356 signals have parquet data. The win rates and PnL are from a limited sample. The true edge may differ from these estimates.

## 2. CONF Distribution
| Category | Count | % |
|----------|------:|--:|
| pass | 313 | 87.9% |
| fail | 22 | 6.2% |
| no_conf | 21 | 5.9% |

**CONF methods (among passes):**
- auto-R1: 286 (91.4%)
- auto-promote: 27 (8.6%)

## 3. CONF Profiles: What Distinguishes Pass from Fail

### 3a. Time of Day
| Time Window | Total | Pass | Fail | Pass Rate |
|-------------|------:|-----:|-----:|----------:|
| 9:30-10:00 | 183.0 | 183.0 | 0.0 | 100.0% |
| 10:00-11:00 | 114.0 | 108.0 | 6.0 | 94.7% |
| 13:00-14:00 | 5.0 | 4.0 | 1.0 | 80.0% |
| 11:00-12:00 | 7.0 | 5.0 | 2.0 | 71.4% |
| 15:00-16:00 | 10.0 | 7.0 | 3.0 | 70.0% |
| 14:00-15:00 | 6.0 | 3.0 | 3.0 | 50.0% |
| 12:00-13:00 | 10.0 | 3.0 | 7.0 | 30.0% |

### 3b. Volume
| Volume | Total | Pass | Fail | Pass Rate |
|--------|------:|-----:|-----:|----------:|
| 10x+ | 68.0 | 68.0 | 0.0 | 100.0% |
| 5-10x | 55.0 | 55.0 | 0.0 | 100.0% |
| 3-5x | 58.0 | 57.0 | 1.0 | 98.3% |
| 2-3x | 91.0 | 83.0 | 8.0 | 91.2% |
| 1-2x | 63.0 | 50.0 | 13.0 | 79.4% |

### 3c. EMA Alignment
| EMA Aligned | Total | Pass | Fail | Pass Rate |
|-------------|------:|-----:|-----:|----------:|
| True | 335.0 | 313.0 | 22.0 | 93.4% |

### 3d. Direction
| Direction | Total | Pass | Fail | Pass Rate |
|-----------|------:|-----:|-----:|----------:|
| bear | 193.0 | 181.0 | 12.0 | 93.8% |
| bull | 142.0 | 132.0 | 10.0 | 93.0% |

### 3e. Level Category
| Level | Total | Pass | Fail | Pass Rate |
|-------|------:|-----:|-----:|----------:|
| PD | 43.0 | 43.0 | 0.0 | 100.0% |
| Week | 13.0 | 13.0 | 0.0 | 100.0% |
| PM | 136.0 | 129.0 | 7.0 | 94.9% |
| Yesterday | 63.0 | 57.0 | 6.0 | 90.5% |
| ORB | 80.0 | 71.0 | 9.0 | 88.8% |

### 3f. Symbol
| Symbol | Total | Pass | Fail | Pass Rate |
|--------|------:|-----:|-----:|----------:|
| AMD | 46.0 | 45.0 | 1.0 | 97.8% |
| AMZN | 42.0 | 41.0 | 1.0 | 97.6% |
| AAPL | 43.0 | 40.0 | 3.0 | 93.0% |
| META | 42.0 | 39.0 | 3.0 | 92.9% |
| QQQ | 41.0 | 38.0 | 3.0 | 92.7% |
| NVDA | 38.0 | 35.0 | 3.0 | 92.1% |
| SPY | 49.0 | 45.0 | 4.0 | 91.8% |
| TSLA | 34.0 | 30.0 | 4.0 | 88.2% |

### 3g. VWAP Alignment
| VWAP Aligned | Total | Pass | Fail | Pass Rate |
|--------------|------:|-----:|-----:|----------:|
| False | 8.0 | 8.0 | 0.0 | 100.0% |
| True | 327.0 | 305.0 | 22.0 | 93.3% |

### 3h. Low vs High Level
| Is Low Level | Total | Pass | Fail | Pass Rate |
|--------------|------:|-----:|-----:|----------:|
| False | 157.0 | 147.0 | 10.0 | 93.6% |
| True | 178.0 | 166.0 | 12.0 | 93.3% |

## 4. CONF Fail Follow-Through Analysis
**Critical question: Are all CONF failures bad?**


### 5-Minute Window
| Metric | CONF Pass (N=159) | CONF Fail (N=9) |
|--------|------:|------:|
| Avg PnL (ATR) | -0.0074 | 0.0048 |
| Win % | 50.9% | 33.3% |
| Avg MFE (ATR) | 0.0962 | 0.0709 |
| Avg MAE (ATR) | 0.1004 | 0.0665 |

### 15-Minute Window
| Metric | CONF Pass (N=159) | CONF Fail (N=9) |
|--------|------:|------:|
| Avg PnL (ATR) | 0.0085 | -0.0091 |
| Win % | 49.1% | 55.6% |
| Avg MFE (ATR) | 0.1573 | 0.1043 |
| Avg MAE (ATR) | 0.1577 | 0.0995 |

### 30-Minute Window
| Metric | CONF Pass (N=159) | CONF Fail (N=9) |
|--------|------:|------:|
| Avg PnL (ATR) | 0.0264 | 0.0555 |
| Win % | 53.5% | 55.6% |
| Avg MFE (ATR) | 0.2251 | 0.1637 |
| Avg MAE (ATR) | 0.2028 | 0.1368 |

### 60-Minute Window
| Metric | CONF Pass (N=159) | CONF Fail (N=9) |
|--------|------:|------:|
| Avg PnL (ATR) | 0.0419 | -0.1057 |
| Win % | 53.5% | 22.2% |
| Avg MFE (ATR) | 0.3040 | 0.1789 |
| Avg MAE (ATR) | 0.2488 | 0.2412 |

### "Good Fails" - CONF Failed But Signal Was Profitable

- CONF ✗ with 30m PnL > +0.1 ATR: **3** signals
- CONF ✗ with 60m PnL > +0.2 ATR: **1** signals
- CONF ✗ with any positive 30m PnL: **5** / 9 (56%)

**Profile of 'good fails':**
- Time: ['10:30', '10:30', '12:45', '14:20', '14:40']
- Symbols: ['AAPL', 'AAPL', 'AAPL', 'QQQ', 'SPY']
- Levels: ['PM H', 'ORB H', 'ORB H', 'Yest H', 'PM H']
- EMA aligned: [True, True, True, True, True]
- Volume: [1.6, 1.8, 2.1, 1.7, 2.2]
- Direction: ['bull', 'bull', 'bull', 'bull', 'bull']

### All CONF ✗ Signal Details
| # | Symbol | Date | Time | Dir | Level | Vol | EMA | VWAP | ADX | 30m PnL | 30m MFE |
|---|--------|------|------|-----|-------|-----|-----|------|-----|---------|--------|
| 1 | META | 2026-01-26 | 10:30 | bull | ORB H | 1.9x | Y | Y | 41 | N/A | N/A |
| 2 | AMZN | 2026-01-30 | 13:20 | bear | ORB L | 2.0x | Y | Y | 34 | -0.259 | 0.103 |
| 3 | AMD | 2026-01-30 | 15:30 | bear | ORB L | 3.2x | Y | Y | 29 | -0.114 | 0.093 |
| 4 | AAPL | 2026-02-03 | 10:30 | bull | PM H | 1.6x | Y | Y | 21 | 0.217 | 0.218 |
| 5 | TSLA | 2026-02-03 | 14:10 | bear | Yest L | 2.8x | Y | Y | 37 | N/A | N/A |
| 6 | SPY | 2026-02-04 | 12:30 | bear | Yest L | 2.1x | Y | Y | 26 | N/A | N/A |
| 7 | TSLA | 2026-02-10 | 12:20 | bull | ORB H | 2.0x | Y | Y | 24 | N/A | N/A |
| 8 | AAPL | 2026-02-11 | 10:30 | bull | ORB H | 1.8x | Y | Y | 47 | 0.473 | 0.494 |
| 9 | QQQ | 2026-02-11 | 12:05 | bear | Yest L | 1.5x | Y | Y | 22 | N/A | N/A |
| 10 | SPY | 2026-02-13 | 15:30 | bear | ORB L | 1.9x | Y | Y | 35 | N/A | N/A |
| 11 | META | 2026-02-17 | 10:35 | bear | PM L | 1.9x | Y | Y | 22 | N/A | N/A |
| 12 | NVDA | 2026-02-18 | 15:00 | bear | ORB L | 2.1x | Y | Y | 29 | N/A | N/A |
| 13 | META | 2026-02-19 | 10:35 | bull | PM H | 2.0x | Y | Y | 30 | N/A | N/A |
| 14 | TSLA | 2026-02-19 | 11:20 | bull | PM H | 1.7x | Y | Y | 31 | N/A | N/A |
| 15 | NVDA | 2026-02-19 | 12:50 | bear | PM L | 1.9x | Y | Y | 27 | N/A | N/A |
| 16 | QQQ | 2026-02-19 | 12:50 | bear | ORB L | 1.7x | Y | Y | 24 | N/A | N/A |
| 17 | SPY | 2026-02-19 | 12:50 | bear | PM L | 1.5x | Y | Y | 27 | N/A | N/A |
| 18 | AAPL | 2026-02-23 | 12:45 | bull | ORB H | 2.1x | Y | Y | 27 | 0.161 | 0.175 |
| 19 | NVDA | 2026-03-02 | 11:50 | bull | Yest H | 1.5x | Y | Y | 40 | -0.008 | 0.039 |
| 20 | QQQ | 2026-03-02 | 14:20 | bull | Yest H | 1.7x | Y | Y | 20 | 0.048 | 0.063 |
| 21 | TSLA | 2026-03-03 | 10:30 | bear | Yest L | 1.8x | Y | Y | 23 | -0.068 | 0.092 |
| 22 | SPY | 2026-03-03 | 14:40 | bull | PM H | 2.2x | Y | Y | 23 | 0.050 | 0.196 |

## 5. 5m HOLD/BAIL Analysis

| Metric | HOLD (N=85) | BAIL (N=228) |
|--------|------:|------:|
| Avg 30m PnL | 0.1605 | -0.0249 |
| Win % (30m) | 79.5% | 43.5% |
| Total 30m PnL | 7.061 | -2.859 |
| Avg 30m MFE | 0.3562 | 0.1749 |

## 6. Scenario Simulation
Test alternative CONF criteria by re-classifying signals.

### Scenario Comparison Table
| Scenario | Flipped | 30m PnL | 60m PnL | Avg MFE | Win% | Worst | Total Pass |
|----------|--------:|--------:|--------:|--------:|-----:|------:|-----------:|
| C: Auto-R1 all-day (EMA only) | 43 | 1.112 | 0.151 | 0.143 | 26% | -0.259 | 356 |
| E: EMA + VWAP aligned any time | 42 | 1.112 | 0.151 | 0.143 | 26% | -0.259 | 355 |
| I: EMA + ADX>=30 any time | 15 | 0.923 | 0.488 | 0.253 | 27% | -0.259 | 328 |
| A: Auto-R1 to 11:00 | 8 | 0.809 | -0.131 | 0.272 | 38% | -0.068 | 321 |
| B: Auto-R1 to 12:00 | 11 | 0.802 | -0.177 | 0.225 | 27% | -0.068 | 324 |
| J: EMA + VWAP + time<12 | 11 | 0.802 | -0.177 | 0.225 | 27% | -0.068 | 324 |
| G: Yesterday levels auto-confirm | 11 | 0.360 | -0.315 | 0.150 | 18% | -0.068 | 324 |
| H: EMA + time<11 + vol>=2x | 2 | 0.188 | 0.213 | 0.282 | 50% | 0.188 | 315 |
| F: EMA + time<11:00 for bears | 4 | 0.120 | -0.175 | 0.187 | 25% | -0.068 | 317 |
| D: Vol >= 3x auto-confirm | 8 | -0.061 | 0.282 | 0.083 | 38% | -0.199 | 321 |

## 7. Risk Analysis

### C: Auto-R1 all-day (EMA only)
- Flipped signals: 43
- Total 30m PnL of flipped: 1.112 ATR
- Avg per-signal: 0.0259 ATR
- Worst single signal: -0.259 ATR
- Win rate: 26%

### E: EMA + VWAP aligned any time
- Flipped signals: 42
- Total 30m PnL of flipped: 1.112 ATR
- Avg per-signal: 0.0265 ATR
- Worst single signal: -0.259 ATR
- Win rate: 26%

### I: EMA + ADX>=30 any time
- Flipped signals: 15
- Total 30m PnL of flipped: 0.923 ATR
- Avg per-signal: 0.0615 ATR
- Worst single signal: -0.259 ATR
- Win rate: 27%

## 8. Top 20 'Missed by CONF' Signals
CONF ✗ signals sorted by 30m MFE (what was available but missed).

| # | Symbol | Date | Time | Dir | Level | Vol | EMA | 30m PnL | 30m MFE | 60m PnL |
|---|--------|------|------|-----|-------|-----|-----|---------|---------|--------:|
| 1 | AAPL | 2026-02-11 | 10:30 | bull | ORB H | 1.8x | Y | 0.473 | 0.494 | 0.208 |
| 2 | AAPL | 2026-02-03 | 10:30 | bull | PM H | 1.6x | Y | 0.217 | 0.218 | -0.164 |
| 3 | SPY | 2026-03-03 | 14:40 | bull | PM H | 2.2x | Y | 0.050 | 0.196 | -0.029 |
| 4 | AAPL | 2026-02-23 | 12:45 | bull | ORB H | 2.1x | Y | 0.161 | 0.175 | 0.189 |
| 5 | AMZN | 2026-01-30 | 13:20 | bear | ORB L | 2.0x | Y | -0.259 | 0.103 | -0.392 |
| 6 | AMD | 2026-01-30 | 15:30 | bear | ORB L | 3.2x | Y | -0.114 | 0.093 | -0.114 |
| 7 | TSLA | 2026-03-03 | 10:30 | bear | Yest L | 1.8x | Y | -0.068 | 0.092 | -0.388 |
| 8 | QQQ | 2026-03-02 | 14:20 | bull | Yest H | 1.7x | Y | 0.048 | 0.063 | -0.214 |
| 9 | NVDA | 2026-03-02 | 11:50 | bull | Yest H | 1.5x | Y | -0.008 | 0.039 | -0.047 |

## 9. Dimmed/Suppressed Signals (no_conf) Analysis

**21 signals** never received a CONF check.
These are typically afternoon EMA-aligned signals that were dimmed.

With parquet data: 9 signals
- Avg 30m PnL: 0.0680 ATR
- Win %: 66.7%
- Avg MFE: 0.1233 ATR
- Total PnL: 0.612 ATR

**EMA-aligned no_conf signals:** 9
- Avg 30m PnL: 0.0680 ATR
- Win %: 66.7%
- Total PnL: 0.612 ATR

**Time distribution:**
- 15:00-16:00: 8
- 13:00-14:00: 5
- 12:00-13:00: 3
- 10:00-11:00: 2
- 14:00-15:00: 2
- 11:00-12:00: 1

**EMA aligned:** 21 / 21 (100%)

## 10. HOLD Filter Robustness
Does HOLD still filter well if we auto-confirm more signals?


**Auto-R1 signals:**
- HOLD: N=42, avg PnL=0.1859, win=83%
- BAIL: N=107, avg PnL=-0.0268, win=42%

**Auto-promote signals:**
- HOLD: N=2, avg PnL=-0.3743, win=0%
- BAIL: N=8, avg PnL=0.0009, win=62%

**All signals:**
- HOLD: N=44, avg PnL=0.1605, win=80%
- BAIL: N=115, avg PnL=-0.0249, win=43%

## 11. Cross-Tabulation: EMA x Time x CONF
Deep look at interaction effects.


**EMA-Aligned:**
| Time | Total | Pass | Fail | Pass% | Avg 30m PnL |
|------|------:|-----:|-----:|------:|------------:|
| 9:30-10:00 | 183 | 183 | 0 | 100% | 0.0321 |
| 10:00-11:00 | 114 | 108 | 6 | 95% | 0.0446 |
| 11:00-12:00 | 7 | 5 | 2 | 71% | -0.0078 |
| 12:00-13:00 | 10 | 3 | 7 | 30% | 0.0702 |
| 13:00-14:00 | 5 | 4 | 1 | 80% | -0.1009 |
| 14:00-15:00 | 6 | 3 | 3 | 50% | 0.0150 |
| 15:00-16:00 | 10 | 7 | 3 | 70% | -0.1692 |

## 12. FADE Signal Performance
Total FADEs: 26

| Symbol | Date | Time | Direction | Price |
|--------|------|------|-----------|------:|
| AAPL | 2026-02-03 | 10:50 | bear | 269.27 |
| AAPL | 2026-02-11 | 14:50 | bear | 276.83 |
| AAPL | 2026-02-23 | 14:45 | bear | 266.87 |
| QQQ | 2026-02-11 | 12:25 | bull | 611.01 |
| QQQ | 2026-02-19 | 13:15 | bull | 602.35 |
| QQQ | 2026-03-02 | 15:10 | bear | 608.32 |
| TSLA | 2026-02-03 | 14:30 | bull | 414.50 |
| TSLA | 2026-02-10 | 13:30 | bear | 423.93 |
| TSLA | 2026-02-19 | 12:50 | bear | 412.29 |
| TSLA | 2026-03-03 | 11:05 | bull | 388.25 |
| AMZN | 2026-01-30 | 13:40 | bull | 238.62 |
| META | 2026-01-26 | 10:50 | bear | 669.84 |
| META | 2026-02-17 | 10:55 | bull | 631.51 |
| META | 2026-02-19 | 10:55 | bear | 643.91 |
| META | 2026-02-19 | 11:45 | bear | 645.00 |
| META | 2026-03-03 | 14:15 | bear | 655.88 |
| AMD | 2026-01-30 | 15:50 | bull | 235.75 |
| NVDA | 2026-02-18 | 15:40 | bull | 187.38 |
| NVDA | 2026-02-19 | 14:00 | bull | 186.51 |
| NVDA | 2026-02-20 | 11:30 | bear | 188.95 |
| NVDA | 2026-02-27 | 15:00 | bull | 179.18 |
| NVDA | 2026-03-02 | 12:10 | bear | 182.59 |
| SPY | 2026-02-03 | 14:25 | bull | 684.83 |
| SPY | 2026-02-04 | 13:30 | bull | 684.03 |
| SPY | 2026-02-13 | 15:50 | bull | 680.83 |
| SPY | 2026-02-19 | 13:15 | bull | 682.83 |

## 13. Simulated HOLD Filter for Newly-Confirmed Signals
If we auto-confirm more signals, would the 5m HOLD filter catch the bad ones?

**Simulated 5m check for 18 would-be-confirmed signals:**

| Group | Count | Avg 30m PnL | Win% | Total PnL |
|-------|------:|------------:|-----:|----------:|
| Sim HOLD | 8 | 0.1495 | 88% | 1.196 |
| Sim BAIL | 10 | -0.0085 | 40% | -0.085 |

Conclusion: HOLD still filters effectively

## 14. Afternoon Signal Deep Dive
The 170 missed moves are mostly afternoon. What does afternoon data look like?

| Window | Count | CONF Pass | CONF Fail | No CONF | With Data |
|--------|------:|----------:|----------:|--------:|----------:|
| Morning <11 | 299 | 291 | 6 | 2 | 154 |
| Afternoon >=11 | 57 | 22 | 16 | 19 | 23 |

**Afternoon signals with follow-through data (N=23):**
- pass: N=9, avg PnL=-0.0865, win=44%, total=-0.779 ATR
- fail: N=6, avg PnL=-0.0203, win=50%, total=-0.122 ATR
- no_conf: N=8, avg PnL=0.0530, win=62%, total=0.424 ATR

## 15. The 10:30 Boundary Problem
Auto-R1 cuts off at 10:30. What happens right after?

| Window | Total | Pass | Fail | Pass% |
|--------|------:|-----:|-----:|------:|
| 10:00-10:29 | 103 | 103 | 0 | 100% |
| 10:30-10:59 | 11 | 5 | 6 | 45% |
| 11:00-11:59 | 7 | 5 | 2 | 71% |
| 12:00-12:59 | 10 | 3 | 7 | 30% |

**10:30-10:59 failures (6):**
- AAPL 2026-02-03 10:30 bull PM H vol=1.6x 30m PnL=0.217
- AAPL 2026-02-11 10:30 bull ORB H vol=1.8x 30m PnL=0.473
- TSLA 2026-03-03 10:30 bear Yest L vol=1.8x 30m PnL=-0.068
- META 2026-01-26 10:30 bull ORB H vol=1.9x 30m PnL=N/A
- META 2026-02-17 10:35 bear PM L vol=1.9x 30m PnL=N/A
- META 2026-02-19 10:35 bull PM H vol=2.0x 30m PnL=N/A

## 16. Volume as CONF Predictor
All 22 CONF failures have vol < 3.2x. Volume >= 3x = 98.3% pass rate.

**CONF fail volume distribution:**
- Min: 1.5x
- Max: 3.2x
- Median: 1.9x
- Mean: 1.9x
- All < 2x: 13 (59%)
- All < 3x: 21 (95%)

## 17. Net Impact Assessment
What is the maximum recoverable ATR from CONF improvements?

- Total signals not confirmed: 43 (18 with data)
- Total 30m PnL of unconfirmed signals: 1.112 ATR
- Positive-only subset: 1.876 ATR from 11 signals
- Negative subset: -0.764 ATR from 7 signals

**Context:** The 170 missed moves from the missed-moves database represent 288.8 ATR.
However, this v3.0b log data covers only 8 symbols x ~27 days. The missed moves span more symbols and time.
The CONF improvement potential per day is: 0.041 ATR/day across 8 symbols.
