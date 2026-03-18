# Missed Moves Scanner Report

**Generated:** 2026-03-04 20:23

**Data:** 13 symbols, 12 days (2026-02-11 to 2026-02-27), 54,794 1m candles

**Signals:** 1,841 (2026-01-20 to 2026-02-27)

**Overlapping symbol-days:** 143 (out of 143 candle symbol-days)

**Detection params:** >=0.5 ATR magnitude, >=3 bars (15 min), reversal threshold 0.75 ATR

## Section 1: Move Scanner Summary

**Total significant moves:** 971
- Up: 509, Down: 462
- Mean magnitude: 1.73 ATR, median: 1.66, max: 4.53
- Mean duration: 3.5 bars (17 min)

### By Symbol

| Symbol | Moves | Days | /Day | Avg ATR | Max ATR | Up | Down |
|--------|-------|------|------|---------|---------|-----|------|
| AAPL | 85 | 12 | 7.1 | 1.61 | 3.26 | 42 | 43 |
| AMD | 80 | 11 | 7.3 | 1.61 | 3.68 | 41 | 39 |
| AMZN | 76 | 11 | 6.9 | 1.81 | 3.55 | 43 | 33 |
| GLD | 85 | 12 | 7.1 | 1.78 | 3.93 | 50 | 35 |
| GOOGL | 63 | 10 | 6.3 | 1.56 | 3.11 | 34 | 29 |
| META | 87 | 12 | 7.2 | 1.79 | 3.40 | 49 | 38 |
| MSFT | 68 | 10 | 6.8 | 1.86 | 3.68 | 30 | 38 |
| NVDA | 68 | 10 | 6.8 | 1.72 | 3.07 | 38 | 30 |
| QQQ | 63 | 10 | 6.3 | 1.75 | 3.65 | 30 | 33 |
| SLV | 73 | 10 | 7.3 | 1.76 | 4.53 | 47 | 26 |
| SPY | 60 | 11 | 5.5 | 1.76 | 3.83 | 25 | 35 |
| TSLA | 73 | 10 | 7.3 | 1.78 | 3.36 | 38 | 35 |
| TSM | 90 | 12 | 7.5 | 1.75 | 3.73 | 42 | 48 |

### By Time Bucket

| Time | Moves | Avg ATR | Max ATR |
|------|-------|---------|---------|
| 9:30-9:45 | 94 | 1.68 | 3.54 |
| 9:45-10:00 | 45 | 1.62 | 3.81 |
| 10:00-10:30 | 102 | 1.51 | 3.40 |
| 10:30-11:00 | 111 | 1.63 | 3.27 |
| 11:00-12:00 | 156 | 1.71 | 3.55 |
| 12:00-14:00 | 260 | 1.83 | 4.53 |
| 14:00-15:00 | 129 | 1.84 | 3.73 |
| 15:00-16:00 | 74 | 1.87 | 3.68 |

## Section 2: Coverage Analysis

**All analysis below uses only overlapping symbol-days** (where we have both candles and signals).

**Total moves on overlap days:** 971

| Classification | Count | % | Total ATR |
|----------------|-------|---|-----------|
| CAUGHT | 32 | 3.3% | 57.9 |
| SIGNAL_FIRED_BUT_FAILED | 170 | 17.5% | 288.8 |
| LATE_CATCH | 3 | 0.3% | 5.9 |
| MISSED | 766 | 78.9% | 1332.0 |

**Total ATR in moves:** 1684.5
**ATR caught (CAUGHT):** 57.9 (3.4%)
**ATR with signal (CAUGHT + FIRED_BUT_FAILED + LATE):** 352.6 (20.9%)
**ATR missed:** 1332.0 (79.1%)

### Coverage by Symbol

| Symbol | Caught | Fired/Failed | Late | Missed | Total | Coverage % |
|--------|--------|-------------|------|--------|-------|-----------|
| AAPL | 4 | 15 | 0 | 66 | 85 | 22% |
| AMD | 0 | 13 | 0 | 67 | 80 | 16% |
| AMZN | 2 | 12 | 0 | 62 | 76 | 18% |
| GLD | 2 | 16 | 0 | 67 | 85 | 21% |
| GOOGL | 3 | 11 | 1 | 48 | 63 | 24% |
| META | 8 | 15 | 1 | 63 | 87 | 28% |
| MSFT | 3 | 13 | 0 | 52 | 68 | 24% |
| NVDA | 2 | 13 | 1 | 52 | 68 | 24% |
| QQQ | 3 | 13 | 0 | 47 | 63 | 25% |
| SLV | 0 | 13 | 0 | 60 | 73 | 18% |
| SPY | 1 | 9 | 0 | 50 | 60 | 17% |
| TSLA | 3 | 9 | 0 | 61 | 73 | 16% |
| TSM | 1 | 18 | 0 | 71 | 90 | 21% |

### Coverage by Time Bucket

| Time | Caught | Fired/Failed | Late | Missed | Coverage % |
|------|--------|-------------|------|--------|-----------|
| 9:30-9:45 | 20 | 68 | 1 | 5 | 95% |
| 9:45-10:00 | 7 | 26 | 1 | 11 | 76% |
| 10:00-10:30 | 5 | 40 | 0 | 57 | 44% |
| 10:30-11:00 | 0 | 8 | 0 | 103 | 7% |
| 11:00-12:00 | 0 | 3 | 0 | 153 | 2% |
| 12:00-14:00 | 0 | 13 | 1 | 246 | 5% |
| 14:00-15:00 | 0 | 8 | 0 | 121 | 6% |
| 15:00-16:00 | 0 | 4 | 0 | 70 | 5% |

### Coverage by Magnitude

| Magnitude | Caught | Fired/Failed | Late | Missed | Coverage % |
|-----------|--------|-------------|------|--------|-----------|
| 0.5-1.0 ATR | 0 | 14 | 1 | 54 | 22% |
| 1.0-1.5 ATR | 6 | 54 | 0 | 236 | 20% |
| 1.5-2.0 ATR | 18 | 57 | 0 | 251 | 23% |
| 2.0-3.0 ATR | 6 | 40 | 1 | 201 | 19% |
| 3.0+ ATR | 2 | 5 | 1 | 24 | 25% |

## Section 3: Missed Moves Inventory (Overlap Days)

**Total missed:** 766

| # | Symbol | Date | Start | Dir | ATR Mag | Bars | Vol | EMA | VWAP | Pattern |
|---|--------|------|-------|-----|---------|------|-----|-----|------|---------|
| 1 | SLV | 2026-02-17 | 12:55 | up | 4.53 | 5b | 1.3x | below | below | Failed_Breakout_Fade |
| 2 | SPY | 2026-02-26 | 13:30 | up | 3.83 | 3b | 2.4x | above | below | No_Signal_Zone |
| 3 | GLD | 2026-02-20 | 09:45 | down | 3.81 | 3b | 0.7x | above | above | Failed_Breakout_Fade |
| 4 | TSM | 2026-02-23 | 14:10 | down | 3.73 | 3b | 0.9x | above | below | Failed_Breakout_Fade |
| 5 | MSFT | 2026-02-27 | 15:05 | up | 3.68 | 3b | 1.2x | above | below | No_Signal_Zone |
| 6 | AMD | 2026-02-26 | 13:15 | up | 3.68 | 3b | 0.7x | below | below | No_Signal_Zone |
| 7 | QQQ | 2026-02-26 | 13:30 | up | 3.65 | 3b | 2.5x | above | below | No_Signal_Zone |
| 8 | GLD | 2026-02-13 | 11:10 | up | 3.55 | 3b | 0.8x | above | above | No_Signal_Zone |
| 9 | AMZN | 2026-02-19 | 13:40 | up | 3.55 | 3b | 0.6x | below | below | No_Signal_Zone |
| 10 | META | 2026-02-11 | 10:25 | up | 3.40 | 5b | 0.6x | below | below | Failed_Breakout_Fade |
| 11 | AMZN | 2026-02-26 | 13:30 | up | 3.38 | 4b | 1.5x | below | below | No_Signal_Zone |
| 12 | TSLA | 2026-02-18 | 13:05 | down | 3.36 | 3b | 0.6x | above | above | Failed_Breakout_Fade |
| 13 | MSFT | 2026-02-20 | 12:00 | down | 3.33 | 3b | 0.8x | above | above | No_Signal_Zone |
| 14 | META | 2026-02-12 | 11:30 | up | 3.27 | 5b | 0.7x | below | below | No_Signal_Zone |
| 15 | AAPL | 2026-02-11 | 14:25 | down | 3.26 | 3b | 1.6x | above | above | No_Signal_Zone |
| 16 | MSFT | 2026-02-19 | 14:20 | down | 3.22 | 3b | 1.1x | above | below | No_Signal_Zone |
| 17 | META | 2026-02-11 | 13:00 | up | 3.21 | 3b | 1.9x | below | below | No_Signal_Zone |
| 18 | GOOGL | 2026-02-26 | 14:00 | up | 3.11 | 4b | 0.9x | above | above | No_Signal_Zone |
| 19 | GOOGL | 2026-02-17 | 14:55 | down | 3.10 | 3b | 0.7x | below | above | No_Signal_Zone |
| 20 | AMZN | 2026-02-19 | 14:05 | down | 3.09 | 4b | 1.1x | above | above | No_Signal_Zone |
| 21 | MSFT | 2026-02-26 | 10:10 | down | 3.08 | 4b | 0.5x | above | above | Failed_Breakout_Fade |
| 22 | TSM | 2026-02-27 | 12:05 | down | 3.07 | 3b | 0.7x | above | above | No_Signal_Zone |
| 23 | AMZN | 2026-02-24 | 13:50 | down | 3.07 | 4b | 1.7x | above | above | No_Signal_Zone |
| 24 | SLV | 2026-02-18 | 14:10 | down | 3.05 | 3b | 0.6x | below | below | No_Signal_Zone |
| 25 | SLV | 2026-02-19 | 15:25 | up | 2.99 | 3b | 0.8x | above | above | No_Signal_Zone |
| 26 | TSLA | 2026-02-26 | 13:30 | up | 2.99 | 3b | 0.9x | above | below | No_Signal_Zone |
| 27 | AMZN | 2026-02-23 | 12:35 | up | 2.98 | 3b | 0.8x | below | below | No_Signal_Zone |
| 28 | TSM | 2026-02-26 | 10:00 | down | 2.97 | 4b | 0.6x | below | below | No_Signal_Zone |
| 29 | GLD | 2026-02-19 | 14:40 | up | 2.97 | 4b | 2.6x | below | below | No_Signal_Zone |
| 30 | MSFT | 2026-02-13 | 11:20 | up | 2.92 | 7b | 0.8x | below | below | Level_Desert_Grind |
| 31 | META | 2026-02-11 | 14:50 | up | 2.90 | 3b | 1.2x | above | above | No_Signal_Zone |
| 32 | TSM | 2026-02-24 | 13:00 | down | 2.88 | 5b | 0.9x | above | above | No_Signal_Zone |
| 33 | AMZN | 2026-02-20 | 12:20 | up | 2.88 | 3b | 0.8x | below | below | No_Signal_Zone |
| 34 | MSFT | 2026-02-25 | 14:20 | down | 2.86 | 4b | 1.2x | above | above | No_Signal_Zone |
| 35 | NVDA | 2026-02-25 | 13:50 | up | 2.86 | 3b | 0.6x | below | above | No_Signal_Zone |
| 36 | SLV | 2026-02-23 | 11:00 | up | 2.85 | 3b | 0.8x | below | below | Failed_Breakout_Fade |
| 37 | AAPL | 2026-02-18 | 15:30 | up | 2.85 | 3b | 1.1x | below | below | No_Signal_Zone |
| 38 | AMZN | 2026-02-12 | 13:55 | down | 2.84 | 3b | 1.3x | above | above | No_Signal_Zone |
| 39 | QQQ | 2026-02-26 | 14:00 | up | 2.83 | 4b | 0.9x | above | below | No_Signal_Zone |
| 40 | QQQ | 2026-02-24 | 11:45 | up | 2.83 | 5b | 0.6x | above | above | No_Signal_Zone |
| 41 | SPY | 2026-02-26 | 14:00 | up | 2.83 | 3b | 0.9x | above | above | No_Signal_Zone |
| 42 | TSLA | 2026-02-20 | 15:35 | up | 2.83 | 3b | 1.3x | below | above | No_Signal_Zone |
| 43 | GLD | 2026-02-24 | 12:00 | up | 2.79 | 3b | 0.9x | above | above | No_Signal_Zone |
| 44 | GOOGL | 2026-02-25 | 11:10 | up | 2.79 | 6b | 0.8x | below | below | Level_Desert_Grind |
| 45 | SPY | 2026-02-26 | 12:30 | down | 2.78 | 3b | 0.7x | below | below | No_Signal_Zone |
| 46 | SLV | 2026-02-17 | 11:55 | down | 2.77 | 3b | 0.9x | below | above | No_Signal_Zone |
| 47 | AMZN | 2026-02-26 | 13:50 | up | 2.77 | 3b | 0.5x | above | below | No_Signal_Zone |
| 48 | META | 2026-02-20 | 15:10 | down | 2.76 | 3b | 0.6x | below | above | No_Signal_Zone |
| 49 | QQQ | 2026-02-26 | 10:35 | up | 2.75 | 10b | 1.1x | below | below | Failed_Breakout_Fade |
| 50 | AMZN | 2026-02-26 | 12:35 | down | 2.74 | 4b | 0.8x | below | below | No_Signal_Zone |
| 51 | GOOGL | 2026-02-18 | 15:30 | up | 2.71 | 3b | 1.2x | below | below | No_Signal_Zone |
| 52 | META | 2026-02-26 | 14:05 | up | 2.71 | 3b | 0.5x | above | above | Post_CONF_Failure_Continuation |
| 53 | AMZN | 2026-02-27 | 11:40 | up | 2.70 | 4b | 0.6x | below | above | No_Signal_Zone |
| 54 | GLD | 2026-02-11 | 11:15 | up | 2.69 | 3b | 0.8x | below | below | No_Signal_Zone |
| 55 | QQQ | 2026-02-19 | 12:20 | down | 2.69 | 5b | 0.9x | above | above | No_Signal_Zone |
| 56 | AMD | 2026-02-26 | 12:30 | down | 2.69 | 3b | 0.7x | above | below | No_Signal_Zone |
| 57 | MSFT | 2026-02-23 | 10:50 | down | 2.68 | 3b | 1.0x | below | below | No_Signal_Zone |
| 58 | MSFT | 2026-02-19 | 10:05 | down | 2.68 | 6b | 0.9x | above | above | Failed_Breakout_Fade |
| 59 | QQQ | 2026-02-26 | 12:30 | down | 2.67 | 3b | 0.9x | below | below | No_Signal_Zone |
| 60 | TSLA | 2026-02-26 | 14:00 | up | 2.66 | 4b | 0.8x | above | below | No_Signal_Zone |
| 61 | AAPL | 2026-02-27 | 14:55 | up | 2.65 | 3b | 0.8x | below | below | No_Signal_Zone |
| 62 | AMD | 2026-02-24 | 11:50 | up | 2.65 | 3b | 0.8x | above | above | No_Signal_Zone |
| 63 | SLV | 2026-02-27 | 13:35 | up | 2.65 | 5b | 0.5x | below | below | Failed_Breakout_Fade |
| 64 | TSLA | 2026-02-26 | 13:15 | up | 2.64 | 3b | 0.7x | below | below | No_Signal_Zone |
| 65 | TSM | 2026-02-18 | 15:00 | down | 2.63 | 4b | 0.7x | below | below | No_Signal_Zone |
| 66 | AMD | 2026-02-24 | 14:00 | down | 2.62 | 4b | 0.7x | below | above | No_Signal_Zone |
| 67 | NVDA | 2026-02-26 | 12:15 | up | 2.62 | 3b | 0.6x | above | below | No_Signal_Zone |
| 68 | MSFT | 2026-02-17 | 12:35 | down | 2.59 | 3b | 0.7x | below | below | No_Signal_Zone |
| 69 | AMZN | 2026-02-24 | 13:00 | down | 2.58 | 3b | 0.9x | above | above | No_Signal_Zone |
| 70 | NVDA | 2026-02-26 | 14:15 | down | 2.56 | 4b | 0.8x | below | below | No_Signal_Zone |
| 71 | GLD | 2026-02-24 | 11:15 | down | 2.55 | 3b | 0.4x | above | above | No_Signal_Zone |
| 72 | GLD | 2026-02-12 | 14:50 | down | 2.54 | 4b | 0.7x | above | below | No_Signal_Zone |
| 73 | TSM | 2026-02-19 | 14:45 | up | 2.54 | 3b | 1.1x | below | below | No_Signal_Zone |
| 74 | NVDA | 2026-02-17 | 14:45 | down | 2.54 | 3b | 0.8x | above | above | No_Signal_Zone |
| 75 | AAPL | 2026-02-12 | 12:30 | down | 2.53 | 3b | 1.0x | below | below | No_Signal_Zone |
| 76 | AAPL | 2026-02-12 | 12:05 | down | 2.53 | 5b | 0.8x | below | below | No_Signal_Zone |
| 77 | SPY | 2026-02-26 | 10:30 | up | 2.52 | 3b | 1.2x | below | below | Failed_Breakout_Fade |
| 78 | SLV | 2026-02-26 | 10:30 | up | 2.52 | 3b | 0.8x | below | below | Failed_Breakout_Fade |
| 79 | TSM | 2026-02-23 | 10:30 | down | 2.51 | 4b | 0.6x | above | above | No_Signal_Zone |
| 80 | META | 2026-02-26 | 10:55 | up | 2.51 | 4b | 0.6x | below | below | No_Signal_Zone |
| 81 | TSLA | 2026-02-24 | 11:55 | up | 2.50 | 3b | 0.7x | above | above | No_Signal_Zone |
| 82 | SPY | 2026-02-24 | 13:00 | down | 2.49 | 4b | 0.5x | above | above | No_Signal_Zone |
| 83 | META | 2026-02-20 | 13:00 | down | 2.49 | 4b | 0.5x | below | above | No_Signal_Zone |
| 84 | TSM | 2026-02-20 | 12:40 | up | 2.48 | 3b | 0.9x | below | above | No_Signal_Zone |
| 85 | NVDA | 2026-02-27 | 14:05 | down | 2.47 | 3b | 0.8x | below | below | No_Signal_Zone |
| 86 | MSFT | 2026-02-17 | 12:55 | up | 2.46 | 5b | 1.0x | below | below | Failed_Breakout_Fade |
| 87 | META | 2026-02-18 | 14:40 | down | 2.46 | 3b | 1.1x | below | above | No_Signal_Zone |
| 88 | TSLA | 2026-02-23 | 12:15 | down | 2.45 | 3b | 0.5x | below | below | No_Signal_Zone |
| 89 | TSLA | 2026-02-20 | 11:55 | down | 2.44 | 3b | 0.7x | below | above | No_Signal_Zone |
| 90 | SLV | 2026-02-26 | 14:40 | up | 2.44 | 4b | 0.4x | above | above | No_Signal_Zone |
| 91 | AMD | 2026-02-23 | 12:45 | up | 2.43 | 7b | 0.6x | below | below | Failed_Breakout_Fade |
| 92 | TSM | 2026-02-26 | 14:00 | up | 2.42 | 3b | 0.9x | above | below | No_Signal_Zone |
| 93 | TSM | 2026-02-23 | 11:20 | up | 2.41 | 3b | 0.8x | below | below | No_Signal_Zone |
| 94 | SPY | 2026-02-17 | 10:40 | up | 2.41 | 4b | 0.8x | below | below | Failed_Breakout_Fade |
| 95 | SPY | 2026-02-23 | 14:25 | down | 2.41 | 3b | 0.8x | below | below | No_Signal_Zone |
| 96 | AMZN | 2026-02-23 | 15:15 | up | 2.40 | 3b | 0.8x | above | below | No_Signal_Zone |
| 97 | NVDA | 2026-02-26 | 11:40 | down | 2.40 | 3b | 0.6x | below | below | No_Signal_Zone |
| 98 | AMD | 2026-02-25 | 14:25 | down | 2.39 | 3b | 1.1x | below | below | No_Signal_Zone |
| 99 | AAPL | 2026-02-19 | 11:05 | up | 2.39 | 3b | 0.5x | below | below | No_Signal_Zone |
| 100 | GLD | 2026-02-12 | 12:40 | down | 2.39 | 4b | 0.1x | below | above | No_Signal_Zone |
| 101 | TSLA | 2026-02-17 | 10:40 | up | 2.39 | 5b | 0.6x | below | below | No_Signal_Zone |
| 102 | GLD | 2026-02-23 | 15:05 | up | 2.38 | 5b | 1.0x | above | above | No_Signal_Zone |
| 103 | TSLA | 2026-02-17 | 11:05 | up | 2.38 | 4b | 0.6x | above | above | No_Signal_Zone |
| 104 | TSM | 2026-02-11 | 11:20 | down | 2.38 | 3b | 0.5x | above | above | No_Signal_Zone |
| 105 | TSM | 2026-02-24 | 14:25 | up | 2.37 | 3b | 1.2x | below | above | No_Signal_Zone |
| 106 | AAPL | 2026-02-23 | 13:35 | down | 2.37 | 3b | 0.7x | above | above | No_Signal_Zone |
| 107 | META | 2026-02-12 | 12:30 | up | 2.37 | 4b | 0.5x | above | below | No_Signal_Zone |
| 108 | SPY | 2026-02-24 | 11:45 | up | 2.36 | 4b | 0.5x | above | above | No_Signal_Zone |
| 109 | AMD | 2026-02-24 | 15:10 | down | 2.36 | 3b | 1.0x | below | above | No_Signal_Zone |
| 110 | AAPL | 2026-02-18 | 11:30 | down | 2.35 | 3b | 1.0x | above | above | Failed_Breakout_Fade |
| 111 | SPY | 2026-02-18 | 15:15 | up | 2.35 | 4b | 1.1x | below | below | No_Signal_Zone |
| 112 | NVDA | 2026-02-20 | 11:45 | down | 2.34 | 5b | 0.6x | above | above | No_Signal_Zone |
| 113 | GLD | 2026-02-23 | 12:50 | up | 2.34 | 4b | 0.6x | above | above | No_Signal_Zone |
| 114 | NVDA | 2026-02-23 | 10:45 | down | 2.34 | 3b | 0.5x | below | below | No_Signal_Zone |
| 115 | MSFT | 2026-02-18 | 10:30 | up | 2.33 | 6b | 0.5x | above | above | Post_CONF_Failure_Continuation |
| 116 | AAPL | 2026-02-24 | 15:35 | up | 2.33 | 3b | 1.2x | below | below | Failed_Breakout_Fade |
| 117 | META | 2026-02-24 | 13:50 | down | 2.32 | 3b | 1.6x | above | above | No_Signal_Zone |
| 118 | TSLA | 2026-02-19 | 12:20 | down | 2.32 | 3b | 1.5x | above | above | No_Signal_Zone |
| 119 | AMD | 2026-02-25 | 10:40 | down | 2.31 | 3b | 0.7x | below | below | No_Signal_Zone |
| 120 | AMD | 2026-02-17 | 15:00 | down | 2.31 | 3b | 1.0x | above | above | No_Signal_Zone |
| 121 | GOOGL | 2026-02-20 | 10:15 | up | 2.30 | 4b | 0.6x | above | above | Failed_Breakout_Fade |
| 122 | TSLA | 2026-02-25 | 12:05 | down | 2.28 | 3b | 1.6x | above | above | No_Signal_Zone |
| 123 | QQQ | 2026-02-20 | 13:00 | down | 2.28 | 4b | 1.2x | above | above | No_Signal_Zone |
| 124 | AMZN | 2026-02-25 | 13:45 | up | 2.28 | 3b | 1.3x | above | below | No_Signal_Zone |
| 125 | TSLA | 2026-02-23 | 10:20 | down | 2.27 | 6b | 0.7x | below | below | Level_Desert_Grind |
| 126 | TSM | 2026-02-19 | 12:30 | down | 2.27 | 3b | 0.3x | below | below | No_Signal_Zone |
| 127 | NVDA | 2026-02-25 | 12:45 | down | 2.27 | 3b | 0.6x | above | above | No_Signal_Zone |
| 128 | GLD | 2026-02-26 | 13:05 | up | 2.26 | 4b | 0.5x | below | below | No_Signal_Zone |
| 129 | SPY | 2026-02-23 | 13:05 | up | 2.26 | 3b | 1.0x | above | below | No_Signal_Zone |
| 130 | AAPL | 2026-02-18 | 13:00 | up | 2.25 | 3b | 0.7x | above | above | No_Signal_Zone |
| 131 | MSFT | 2026-02-17 | 15:15 | down | 2.25 | 4b | 0.8x | below | below | No_Signal_Zone |
| 132 | QQQ | 2026-02-19 | 14:45 | up | 2.25 | 3b | 1.1x | below | below | No_Signal_Zone |
| 133 | META | 2026-02-24 | 14:25 | up | 2.25 | 3b | 0.8x | below | above | No_Signal_Zone |
| 134 | GLD | 2026-02-12 | 15:10 | down | 2.25 | 3b | 1.4x | below | below | No_Signal_Zone |
| 135 | GLD | 2026-02-27 | 13:45 | up | 2.24 | 3b | 1.0x | above | above | No_Signal_Zone |
| 136 | MSFT | 2026-02-20 | 11:30 | up | 2.23 | 3b | 0.7x | above | above | No_Signal_Zone |
| 137 | META | 2026-02-23 | 13:55 | down | 2.23 | 3b | 1.7x | below | below | No_Signal_Zone |
| 138 | GOOGL | 2026-02-17 | 10:40 | up | 2.23 | 4b | 0.7x | below | below | No_Signal_Zone |
| 139 | TSLA | 2026-02-26 | 10:30 | up | 2.23 | 5b | 1.1x | below | below | Failed_Breakout_Fade |
| 140 | GOOGL | 2026-02-25 | 12:20 | down | 2.22 | 3b | 0.4x | above | below | No_Signal_Zone |
| 141 | SLV | 2026-02-23 | 13:30 | up | 2.22 | 3b | 0.7x | above | above | No_Signal_Zone |
| 142 | QQQ | 2026-02-23 | 14:25 | down | 2.22 | 3b | 0.8x | below | below | No_Signal_Zone |
| 143 | NVDA | 2026-02-23 | 11:25 | up | 2.22 | 3b | 0.6x | below | below | No_Signal_Zone |
| 144 | AAPL | 2026-02-13 | 12:00 | up | 2.21 | 4b | 0.6x | above | below | No_Signal_Zone |
| 145 | TSLA | 2026-02-20 | 14:00 | down | 2.21 | 5b | 0.9x | above | above | No_Signal_Zone |
| 146 | AMD | 2026-02-20 | 11:55 | down | 2.21 | 3b | 0.7x | below | above | No_Signal_Zone |
| 147 | AMD | 2026-02-12 | 14:40 | down | 2.21 | 3b | 1.1x | above | below | No_Signal_Zone |
| 148 | NVDA | 2026-02-18 | 13:00 | down | 2.21 | 5b | 1.1x | above | above | No_Signal_Zone |
| 149 | GOOGL | 2026-02-25 | 10:30 | down | 2.20 | 4b | 0.6x | below | below | No_Signal_Zone |
| 150 | MSFT | 2026-02-18 | 13:05 | down | 2.19 | 5b | 1.0x | above | above | No_Signal_Zone |
| ... | _616 more_ | | | | | | | | | |

## Section 4: Missed Move Fingerprints


### Level Desert Grind (n=13)

- **Total ATR missed:** 24.5
- **Avg magnitude:** 1.89 ATR, max: 2.92
- **Avg duration:** 6.7 bars (33 min)
- **Avg vol ratio:** 0.7x
- **EMA above:** 5/13 (38%)
- **VWAP above:** 5/13 (38%)
- **Direction:** 6 up / 7 down
- **Time dist:** {'10:30-11:00': 4, '11:00-12:00': 4, '10:00-10:30': 3, '12:00-14:00': 2}
- **Top symbols:** {'AMD': 2, 'GOOGL': 2, 'MSFT': 2, 'NVDA': 2, 'GLD': 1}
- **Suggested fix:** Trend-continuation signal: EMA+VWAP alignment without key level requirement

### Failed Breakout Fade (n=110)

- **Total ATR missed:** 178.9
- **Avg magnitude:** 1.63 ATR, max: 4.53
- **Avg duration:** 3.7 bars (18 min)
- **Avg vol ratio:** 0.8x
- **EMA above:** 64/110 (58%)
- **VWAP above:** 64/110 (58%)
- **Direction:** 54 up / 56 down
- **Time dist:** {'10:00-10:30': 34, '10:30-11:00': 24, '12:00-14:00': 19, '9:45-10:00': 9}
- **Top symbols:** {'SLV': 13, 'AAPL': 12, 'AMD': 10, 'META': 10, 'MSFT': 10}
- **Suggested fix:** Failed-breakout fade: reverse signal when price closes back through level after breakout

### Post CONF Failure Continuation (n=21)

- **Total ATR missed:** 33.5
- **Avg magnitude:** 1.60 ATR, max: 2.71
- **Avg duration:** 4.0 bars (20 min)
- **Avg vol ratio:** 0.6x
- **EMA above:** 15/21 (71%)
- **VWAP above:** 17/21 (81%)
- **Direction:** 14 up / 7 down
- **Time dist:** {'10:30-11:00': 13, '10:00-10:30': 3, '11:00-12:00': 2, '9:45-10:00': 1}
- **Top symbols:** {'QQQ': 4, 'MSFT': 3, 'GLD': 2, 'META': 2, 'SLV': 2}
- **Suggested fix:** CONF re-arm: re-enable signal after CONF failure if setup persists

### No Signal Zone (n=622)

- **Total ATR missed:** 1095.0
- **Avg magnitude:** 1.76 ATR, max: 3.83
- **Avg duration:** 3.3 bars (17 min)
- **Avg vol ratio:** 0.8x
- **EMA above:** 359/622 (58%)
- **VWAP above:** 367/622 (59%)
- **Direction:** 319 up / 303 down
- **Time dist:** {'12:00-14:00': 224, '11:00-12:00': 138, '14:00-15:00': 112, '15:00-16:00': 67}
- **Top symbols:** {'TSM': 63, 'AMZN': 57, 'GLD': 57, 'AMD': 55, 'AAPL': 53}
- **Suggested fix:** New level types (intraday pivots, round numbers) or lower signal threshold

## Section 5: Top 20 Largest Missed Moves


### #1: SLV 2026-02-17 — 4.53 ATR up
- **Time:** 12:55 -> 13:20 (5b = 25 min)
- **Price:** $65.43 -> $66.85
- **Context:** Vol 1.3x, EMA below, VWAP below
- **Pattern:** Failed_Breakout_Fade
- Opposite signal fired within 30min before (1 signals)

### #2: SPY 2026-02-26 — 3.83 ATR up
- **Time:** 13:30 -> 13:45 (3b = 15 min)
- **Price:** $685.43 -> $688.19
- **Context:** Vol 2.4x, EMA above, VWAP below
- **Pattern:** No_Signal_Zone

### #3: GLD 2026-02-20 — 3.81 ATR down
- **Time:** 09:45 -> 10:00 (3b = 15 min)
- **Price:** $465.10 -> $460.93
- **Context:** Vol 0.7x, EMA above, VWAP above
- **Pattern:** Failed_Breakout_Fade
- Opposite signal fired within 30min before (1 signals)

### #4: TSM 2026-02-23 — 3.73 ATR down
- **Time:** 14:10 -> 14:25 (3b = 15 min)
- **Price:** $369.82 -> $367.88
- **Context:** Vol 0.9x, EMA above, VWAP below
- **Pattern:** Failed_Breakout_Fade
- Opposite signal fired within 30min before (1 signals)

### #5: MSFT 2026-02-27 — 3.68 ATR up
- **Time:** 15:05 -> 15:20 (3b = 15 min)
- **Price:** $393.04 -> $394.96
- **Context:** Vol 1.2x, EMA above, VWAP below
- **Pattern:** No_Signal_Zone

### #6: AMD 2026-02-26 — 3.68 ATR up
- **Time:** 13:15 -> 13:30 (3b = 15 min)
- **Price:** $201.50 -> $203.43
- **Context:** Vol 0.7x, EMA below, VWAP below
- **Pattern:** No_Signal_Zone

### #7: QQQ 2026-02-26 — 3.65 ATR up
- **Time:** 13:30 -> 13:45 (3b = 15 min)
- **Price:** $605.07 -> $608.03
- **Context:** Vol 2.5x, EMA above, VWAP below
- **Pattern:** No_Signal_Zone

### #8: GLD 2026-02-13 — 3.55 ATR up
- **Time:** 11:10 -> 11:25 (3b = 15 min)
- **Price:** $458.45 -> $462.58
- **Context:** Vol 0.8x, EMA above, VWAP above
- **Pattern:** No_Signal_Zone

### #9: AMZN 2026-02-19 — 3.55 ATR up
- **Time:** 13:40 -> 13:55 (3b = 15 min)
- **Price:** $204.00 -> $205.05
- **Context:** Vol 0.6x, EMA below, VWAP below
- **Pattern:** No_Signal_Zone

### #10: META 2026-02-11 — 3.40 ATR up
- **Time:** 10:25 -> 10:50 (5b = 25 min)
- **Price:** $660.95 -> $673.80
- **Context:** Vol 0.6x, EMA below, VWAP below
- **Pattern:** Failed_Breakout_Fade
- Opposite signal fired within 30min before (2 signals)

### #11: AMZN 2026-02-26 — 3.38 ATR up
- **Time:** 13:30 -> 13:50 (4b = 20 min)
- **Price:** $205.52 -> $207.01
- **Context:** Vol 1.5x, EMA below, VWAP below
- **Pattern:** No_Signal_Zone

### #12: TSLA 2026-02-18 — 3.36 ATR down
- **Time:** 13:05 -> 13:20 (3b = 15 min)
- **Price:** $416.58 -> $413.93
- **Context:** Vol 0.6x, EMA above, VWAP above
- **Pattern:** Failed_Breakout_Fade
- Opposite signal fired within 30min before (1 signals)

### #13: MSFT 2026-02-20 — 3.33 ATR down
- **Time:** 12:00 -> 12:15 (3b = 15 min)
- **Price:** $399.56 -> $396.64
- **Context:** Vol 0.8x, EMA above, VWAP above
- **Pattern:** No_Signal_Zone

### #14: META 2026-02-12 — 3.27 ATR up
- **Time:** 11:30 -> 11:55 (5b = 25 min)
- **Price:** $645.48 -> $653.38
- **Context:** Vol 0.7x, EMA below, VWAP below
- **Pattern:** No_Signal_Zone

### #15: AAPL 2026-02-11 — 3.26 ATR down
- **Time:** 14:25 -> 14:40 (3b = 15 min)
- **Price:** $279.66 -> $278.59
- **Context:** Vol 1.6x, EMA above, VWAP above
- **Pattern:** No_Signal_Zone

### #16: MSFT 2026-02-19 — 3.22 ATR down
- **Time:** 14:20 -> 14:35 (3b = 15 min)
- **Price:** $398.49 -> $396.79
- **Context:** Vol 1.1x, EMA above, VWAP below
- **Pattern:** No_Signal_Zone

### #17: META 2026-02-11 — 3.21 ATR up
- **Time:** 13:00 -> 13:15 (3b = 15 min)
- **Price:** $657.04 -> $665.09
- **Context:** Vol 1.9x, EMA below, VWAP below
- **Pattern:** No_Signal_Zone

### #18: GOOGL 2026-02-26 — 3.11 ATR up
- **Time:** 14:00 -> 14:20 (4b = 20 min)
- **Price:** $306.62 -> $308.42
- **Context:** Vol 0.9x, EMA above, VWAP above
- **Pattern:** No_Signal_Zone

### #19: GOOGL 2026-02-17 — 3.10 ATR down
- **Time:** 14:55 -> 15:10 (3b = 15 min)
- **Price:** $303.02 -> $301.57
- **Context:** Vol 0.7x, EMA below, VWAP above
- **Pattern:** No_Signal_Zone

### #20: AMZN 2026-02-19 — 3.09 ATR down
- **Time:** 14:05 -> 14:25 (4b = 20 min)
- **Price:** $205.12 -> $204.25
- **Context:** Vol 1.1x, EMA above, VWAP above
- **Pattern:** No_Signal_Zone

## Section 6: Pattern Frequency and Value

| Pattern | Count | % | Total ATR | Avg ATR | Top Time |
|---------|-------|---|-----------|---------|----------|
| No_Signal_Zone | 622 | 81% | 1095.0 | 1.76 | 12:00-14:00 |
| Failed_Breakout_Fade | 110 | 14% | 178.9 | 1.63 | 10:00-10:30 |
| Post_CONF_Failure_Continuation | 21 | 3% | 33.5 | 1.60 | 10:30-11:00 |
| Level_Desert_Grind | 13 | 2% | 24.5 | 1.89 | 10:30-11:00 |

## Section 7: Recommendations

### Priority-Ranked Improvements

| # | Pattern | Total Missed ATR | Count | Fix |
|---|---------|-----------------|-------|-----|
| 1 | No_Signal_Zone | 1095.0 | 622 | Add intraday pivots / round numbers as level types, or lower volume threshold. |
| 2 | Failed_Breakout_Fade | 178.9 | 110 | Detect breakout failure and fire reverse signal. |
| 3 | Post_CONF_Failure_Continuation | 33.5 | 21 | Re-arm signal after CONF failure if setup persists. |
| 4 | Level_Desert_Grind | 24.6 | 13 | Add trend-continuation signal: EMA/VWAP alignment without key level. Largest opportunity. |

### Symbols With Most Missed ATR

- **TSM:** 127.0 ATR (71 moves, avg 1.79)
- **GLD:** 117.7 ATR (67 moves, avg 1.76)
- **AMZN:** 112.8 ATR (62 moves, avg 1.82)
- **META:** 112.3 ATR (63 moves, avg 1.78)
- **TSLA:** 109.9 ATR (61 moves, avg 1.80)
- **AAPL:** 108.5 ATR (66 moves, avg 1.64)
- **AMD:** 107.9 ATR (67 moves, avg 1.61)
- **SLV:** 105.5 ATR (60 moves, avg 1.76)
- **MSFT:** 97.7 ATR (52 moves, avg 1.88)
- **SPY:** 87.8 ATR (50 moves, avg 1.76)
- **NVDA:** 87.8 ATR (52 moves, avg 1.69)
- **QQQ:** 79.2 ATR (47 moves, avg 1.68)
- **GOOGL:** 77.8 ATR (48 moves, avg 1.62)

### Time Buckets With Most Missed ATR

- **12:00-14:00:** 446.3 ATR (246 moves)
- **11:00-12:00:** 261.1 ATR (153 moves)
- **14:00-15:00:** 223.5 ATR (121 moves)
- **10:30-11:00:** 165.2 ATR (103 moves)
- **15:00-16:00:** 130.0 ATR (70 moves)
- **10:00-10:30:** 82.9 ATR (57 moves)
- **9:45-10:00:** 17.4 ATR (11 moves)
- **9:30-9:45:** 5.6 ATR (5 moves)

### What We Catch Well

Caught 32 moves (57.9 ATR) with CONF signals:

- GLD 2026-02-23 09:30 — 3.54 ATR up (signal: BRK PM H at 9:35, conf: ✓★)
- TSLA 2026-02-26 10:10 — 3.15 ATR down (signal: BRK Yest L at 10:15, conf: ✓)
- TSM 2026-02-26 09:30 — 2.77 ATR down (signal: BRK PM L+Yest L at 9:35, conf: ✓★)
- QQQ 2026-02-26 09:55 — 2.67 ATR down (signal: BRK ORB L at 9:50, conf: ✓)
- META 2026-02-25 09:30 — 2.14 ATR up (signal: BRK Yest H at 9:30, conf: ✓)

### Signals Fired But CONF Failed

170 moves had matching signals without CONF, totaling 288.8 ATR.

**These are directly recoverable** if CONF criteria are relaxed:

- GLD 2026-02-26 13:35 — 3.93 ATR up (signal: REV PM L at 13:40)
- MSFT 2026-02-13 10:30 — 3.27 ATR down (signal: BRK ORB L at 10:40)
- AAPL 2026-02-17 13:35 — 3.21 ATR up (signal: BRK Yest H at 13:25)
- META 2026-02-18 15:30 — 3.12 ATR up (signal: REV Week L at 15:35)
- AMD 2026-02-17 09:35 — 3.06 ATR down (signal: BRK Yest L+Week L at 9:45)
- NVDA 2026-02-20 13:30 — 2.85 ATR up (signal: BRK PM H at 13:35)
- AMZN 2026-02-13 14:50 — 2.76 ATR down (signal: REV ORB H at 15:00)
- AMZN 2026-02-20 09:50 — 2.69 ATR up (signal: BRK Yest H at 9:35)
- QQQ 2026-02-23 09:30 — 2.67 ATR down (signal: BRK ORB L at 9:45)
- SLV 2026-02-17 09:30 — 2.65 ATR down (signal: BRK Week L at 9:40)

### Late Catches

3 moves had signals that fired late (after first 10min), totaling 5.9 ATR.

- NVDA 2026-02-27 12:00 — 3.07 ATR down (signal: BRK at 12:20)
- META 2026-02-26 09:50 — 2.13 ATR down (signal: REV at 10:10)
- GOOGL 2026-02-20 09:35 — 0.68 ATR down (signal: REV at 9:55)

---

*Report generated by missed_moves_scanner.py on 2026-03-04 20:23*