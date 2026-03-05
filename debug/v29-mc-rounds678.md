# v2.9 MC Replacement — Rounds 6-8
**Data:** 1841 signals, 28 days, 13 symbols
**Date range:** 2026-01-20 to 2026-02-27

# ROUND 6: EMA Gate — Hard Suppress vs Dim

## 6a: Non-EMA Signals Post-9:50 — Kill or Keep?

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| ALL post-9:50 | 1003 | 51.5 | 0.206 | -0.168 | 1.22 | 0.037 | 37.4 | 1.2 |
| EMA aligned | 795 | 55.0 | 0.215 | -0.152 | 1.42 | 0.064 | 50.7 | 1.3 |
| Non-EMA | 208 | 38.5 | 0.168 | -0.232 | 0.72 | -0.064 | -13.3 | 1.0 |

### Non-EMA post-9:50 by Signal Type

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| BRK | 109 | 41.3 | 0.182 | -0.196 | 0.93 | -0.014 | -1.5 | 1.8 |
| REV | 99 | 35.4 | 0.153 | -0.273 | 0.56 | -0.119 | -11.8 | 0.0 |

### Non-EMA post-9:50 by Time

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| 9:50-10:30 | 143 | 38.5 | 0.201 | -0.268 | 0.75 | -0.067 | -9.6 | 1.4 |
| 10:30-11:00 | 9 | 44.4 | 0.090 | -0.271 | 0.33 | -0.181 | -1.6 | 0.0 |
| 11:00-12:00 | 3 | 0.0 | 0.093 | -0.323 | 0.29 | -0.230 | -0.7 | 0.0 |
| 12:00+ | 53 | 39.6 | 0.097 | -0.125 | 0.78 | -0.028 | -1.5 | 0.0 |

### Non-EMA post-9:50 by Symbol (top/bottom)

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| SLV | 19 | 63.2 | 0.290 | -0.139 | 2.08 | 0.151 | 2.9 | 5.3 |
| GLD | 23 | 34.8 | 0.292 | -0.248 | 1.18 | 0.044 | 1.0 | 4.3 |
| TSLA | 14 | 50.0 | 0.162 | -0.160 | 1.01 | 0.002 | 0.0 | 0.0 |
| AAPL | 17 | 29.4 | 0.229 | -0.237 | 0.97 | -0.008 | -0.1 | 0.0 |
| TSM | 20 | 20.0 | 0.109 | -0.160 | 0.68 | -0.051 | -1.0 | 0.0 |
| META | 19 | 47.4 | 0.155 | -0.223 | 0.69 | -0.068 | -1.3 | 0.0 |
| QQQ | 12 | 41.7 | 0.143 | -0.233 | 0.61 | -0.090 | -1.1 | 0.0 |
| GOOGL | 13 | 38.5 | 0.140 | -0.265 | 0.53 | -0.125 | -1.6 | 0.0 |
| NVDA | 18 | 44.4 | 0.142 | -0.266 | 0.53 | -0.125 | -2.2 | 0.0 |
| MSFT | 12 | 41.7 | 0.088 | -0.217 | 0.41 | -0.129 | -1.5 | 0.0 |
| SPY | 18 | 27.8 | 0.139 | -0.296 | 0.47 | -0.157 | -2.8 | 0.0 |
| AMD | 16 | 31.2 | 0.082 | -0.290 | 0.28 | -0.209 | -3.3 | 0.0 |
| AMZN | 7 | 28.6 | 0.071 | -0.376 | 0.19 | -0.305 | -2.1 | 0.0 |

### Non-EMA Rescue Groups (post-9:50)

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| Counter-VWAP | 18 | 55.6 | 0.264 | -0.109 | 2.42 | 0.155 | 2.8 | 5.6 |
| With-VWAP | 190 | 36.8 | 0.159 | -0.244 | 0.65 | -0.085 | -16.1 | 0.5 |
| ADX > 40 | 14 | 42.9 | 0.517 | -0.278 | 1.86 | 0.239 | 3.3 | 7.1 |
| Vol >= 5x | 14 | 42.9 | 0.123 | -0.271 | 0.45 | -0.148 | -2.1 | 0.0 |
| Before 10:30 | 143 | 38.5 | 0.201 | -0.268 | 0.75 | -0.067 | -9.6 | 1.4 |

## 6b: EMA Gate Pre-9:50

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| ALL pre-9:50 | 838 | 51.2 | 0.310 | -0.271 | 1.15 | 0.039 | 32.9 | 3.1 |
| EMA aligned | 555 | 59.8 | 0.343 | -0.226 | 1.52 | 0.118 | 65.2 | 3.1 |
| Non-EMA | 283 | 34.3 | 0.244 | -0.359 | 0.68 | -0.114 | -32.3 | 3.2 |

### Pre-9:50 Non-EMA by Time

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| < 9:50 | 283 | 34.3 | 0.244 | -0.359 | 0.68 | -0.114 | -32.3 | 3.2 |
| 9:30-9:40 | 145 | 31.7 | 0.267 | -0.360 | 0.74 | -0.093 | -13.5 | 4.1 |
| 9:40-9:50 | 138 | 37.0 | 0.221 | -0.357 | 0.62 | -0.136 | -18.8 | 2.2 |

## 6c: EMA Gate All Day vs After-9:50 Only

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| No EMA gate (all signals) | 1841 | 51.4 | 0.253 | -0.215 | 1.18 | 0.038 | 70.3 | 2.1 |
| EMA gate ALL DAY | 1350 | 57.0 | 0.268 | -0.182 | 1.47 | 0.086 | 115.9 | 2.0 |
| EMA gate AFTER 9:50 only | 1633 | 53.0 | 0.264 | -0.213 | 1.24 | 0.051 | 83.6 | 2.2 |
| EMA gate after 9:50 + pre-9:50 ADX>30 exempt | 1417 | 55.5 | 0.271 | -0.194 | 1.39 | 0.077 | 108.5 | 2.1 |

### 6 Verdict

- EMA-only total PnL: 115.9 (N=1350)
- All signals total PnL: 70.3 (N=1841)
- Non-EMA total PnL: -45.6 (N=491)
- Non-EMA signals are net negative

# ROUND 7: Score-Based Auto-Confirm (MC Replacement)

## 7a: 9-Factor Flat Score

Factors (1 point each): EMA Aligned, ADX>40, Counter-VWAP, Dir=Bear, Time<10:30, Body>40, Vol>=2x, Level=LOW, Type=BRK

### Score Distribution

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| Score 1 | 8 | 75.0 | 0.124 | -0.096 | 1.29 | 0.028 | 0.2 | 0.0 |
| Score 2 | 92 | 50.0 | 0.131 | -0.144 | 0.91 | -0.013 | -1.2 | 0.0 |
| Score 3 | 193 | 49.2 | 0.139 | -0.133 | 1.04 | 0.006 | 1.1 | 0.0 |
| Score 4 | 255 | 46.7 | 0.181 | -0.199 | 0.91 | -0.019 | -4.7 | 0.8 |
| Score 5 | 231 | 52.8 | 0.214 | -0.157 | 1.36 | 0.057 | 13.1 | 0.9 |
| Score 6 | 116 | 54.3 | 0.273 | -0.195 | 1.40 | 0.078 | 9.0 | 2.6 |
| Score 7 | 92 | 63.0 | 0.385 | -0.177 | 2.17 | 0.207 | 19.1 | 5.4 |
| Score 8 | 16 | 50.0 | 0.237 | -0.190 | 1.25 | 0.047 | 0.8 | 0.0 |

### Auto-Confirm at Score Thresholds

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% | CONF ✓% | CONF ✗% | No CONF% |
|---|---|---|---|---|---|---|---|---|---|---|---|
| >= 5 | 455 | 55.2 | 0.264 | -0.172 | 1.53 | 0.092 | 41.9 | 2.2 | 21.8 | 62.4 | 15.8 |
| >= 6 | 224 | 57.6 | 0.316 | -0.188 | 1.69 | 0.129 | 28.8 | 3.6 | 24.1 | 71.0 | 4.9 |
| >= 7 | 108 | 61.1 | 0.363 | -0.179 | 2.02 | 0.183 | 19.8 | 4.6 | 20.4 | 77.8 | 1.9 |

## 7b: Simple Auto-Confirm Rules

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| Baseline (all post-9:50) | 1003 | 51.5 | 0.206 | -0.168 | 1.22 | 0.037 | 37.4 | 1.2 |
| R1: EMA + Time<10:30 | 389 | 58.6 | 0.283 | -0.177 | 1.60 | 0.106 | 41.2 | 1.8 |
| R2: EMA + ADX>30 | 232 | 55.6 | 0.273 | -0.181 | 1.50 | 0.091 | 21.1 | 2.6 |
| R3: EMA + Time<10:30 + ADX>30 | 141 | 54.6 | 0.296 | -0.196 | 1.51 | 0.100 | 14.1 | 2.1 |
| R4: EMA + Time<10:30 + Bear | 204 | 59.3 | 0.335 | -0.185 | 1.81 | 0.150 | 30.6 | 3.4 |
| R5: EMA + Counter-VWAP | 34 | 58.8 | 0.199 | -0.136 | 1.46 | 0.062 | 2.1 | 0.0 |

### Additional Rules

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% | CONF ✓% |
|---|---|---|---|---|---|---|---|---|---|
| R6: EMA + Vol>=5x | 38 | 63.2 | 0.233 | -0.163 | 1.43 | 0.070 | 2.6 | 0.0 | 15.8 |
| R7: EMA + Level=LOW | 413 | 55.2 | 0.216 | -0.153 | 1.41 | 0.063 | 26.1 | 1.5 | 20.8 |
| R8: EMA + Bear + Counter-VWAP | 20 | 75.0 | 0.229 | -0.094 | 2.43 | 0.135 | 2.7 | 0.0 | 30.0 |
| R9: EMA + Time<10:30 + Counter-VWAP | 16 | 43.8 | 0.173 | -0.225 | 0.77 | -0.052 | -0.8 | 0.0 | 12.5 |
| R10: EMA + ADX>30 + Counter-VWAP | 3 | 33.3 | 0.082 | -0.206 | 0.40 | -0.124 | -0.4 | 0.0 | 0.0 |

## 7c: Best Rules by Signal Type and Time

### R1: EMA + Time<10:30

**By Signal Type:**

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| BRK | 285 | 58.6 | 0.270 | -0.182 | 1.49 | 0.089 | 25.3 | 1.4 |
| REV | 104 | 58.7 | 0.318 | -0.165 | 1.92 | 0.152 | 15.8 | 2.9 |

**By Time Bucket:**

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| 9:50-10:30 | 389 | 58.6 | 0.283 | -0.177 | 1.60 | 0.106 | 41.2 | 1.8 |

### R4: EMA + Time<10:30 + Bear

**By Signal Type:**

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| BRK | 147 | 59.2 | 0.313 | -0.187 | 1.67 | 0.125 | 18.4 | 2.7 |
| REV | 57 | 59.6 | 0.395 | -0.181 | 2.18 | 0.213 | 12.2 | 5.3 |

**By Time Bucket:**

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| 9:50-10:30 | 204 | 59.3 | 0.335 | -0.185 | 1.81 | 0.150 | 30.6 | 3.4 |

### R3: EMA + Time<10:30 + ADX>30

**By Signal Type:**

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| BRK | 116 | 50.9 | 0.250 | -0.207 | 1.21 | 0.043 | 5.0 | 0.9 |
| REV | 25 | 72.0 | 0.511 | -0.147 | 3.48 | 0.364 | 9.1 | 8.0 |

**By Time Bucket:**

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| 9:50-10:30 | 141 | 54.6 | 0.296 | -0.196 | 1.51 | 0.100 | 14.1 | 2.1 |

# ROUND 8: Robustness + Final Configuration

## 8a: Robustness Check

### R1: EMA + Time<10:30

**Time Split:** First half (2026-01-21 to 2026-02-09), Second half (2026-02-10 to 2026-02-27)

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| First half (13 days) | 197 | 63.5 | 0.353 | -0.173 | 2.04 | 0.179 | 35.3 | 3.6 |
| Second half (13 days) | 192 | 53.6 | 0.212 | -0.181 | 1.17 | 0.030 | 5.8 | 0.0 |

**Symbols Net Positive:**

12/13 symbols net positive

| Symbol | N | Total PnL | Avg PnL |
|---|---|---|---|
| AMD | 33 | 5.68 | 0.172 |
| QQQ | 35 | 5.58 | 0.159 |
| AMZN | 38 | 4.58 | 0.121 |
| SLV | 20 | 4.53 | 0.227 |
| NVDA | 23 | 4.21 | 0.183 |
| TSLA | 27 | 4.08 | 0.151 |
| TSM | 32 | 3.03 | 0.095 |
| GOOGL | 28 | 2.83 | 0.101 |
| SPY | 44 | 2.67 | 0.061 |
| GLD | 26 | 2.09 | 0.080 |
| META | 33 | 1.74 | 0.053 |
| MSFT | 23 | 0.57 | 0.025 |
| AAPL | 27 | -0.43 | -0.016 |

**PnL Distribution (ATR units):**

| PnL Bucket | Count | % |
|---|---|---|
| <-1.5 | 0 | 0.0% |
| -1.5 to -1.0 | 0 | 0.0% |
| -1.0 to -0.5 | 13 | 3.3% |
| -0.5 to -0.25 | 49 | 12.6% |
| -0.25 to 0 | 99 | 25.4% |
| 0 to 0.25 | 98 | 25.2% |
| 0.25 to 0.5 | 83 | 21.3% |
| 0.5 to 1.0 | 42 | 10.8% |
| 1.0 to 1.5 | 2 | 0.5% |
| 1.5+ | 3 | 0.8% |

**Tail Dependency:** Top 10% of signals (38 signals) contribute 71.6% of total PnL

### R4: EMA + Time<10:30 + Bear

**Time Split:** First half (2026-01-26 to 2026-02-09), Second half (2026-02-10 to 2026-02-27)

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| First half (11 days) | 107 | 71.0 | 0.433 | -0.158 | 2.74 | 0.275 | 29.4 | 6.5 |
| Second half (12 days) | 97 | 46.4 | 0.228 | -0.216 | 1.06 | 0.013 | 1.2 | 0.0 |

**Symbols Net Positive:**

11/13 symbols net positive

| Symbol | N | Total PnL | Avg PnL |
|---|---|---|---|
| AMD | 22 | 5.34 | 0.243 |
| SLV | 11 | 4.97 | 0.452 |
| GLD | 10 | 3.60 | 0.360 |
| QQQ | 22 | 3.33 | 0.152 |
| NVDA | 14 | 2.66 | 0.190 |
| AMZN | 15 | 2.57 | 0.171 |
| GOOGL | 10 | 2.48 | 0.248 |
| SPY | 25 | 2.42 | 0.097 |
| TSLA | 19 | 2.05 | 0.108 |
| TSM | 17 | 1.91 | 0.112 |
| MSFT | 9 | 0.13 | 0.015 |
| META | 20 | -0.05 | -0.003 |
| AAPL | 10 | -0.82 | -0.082 |

**PnL Distribution (ATR units):**

| PnL Bucket | Count | % |
|---|---|---|
| <-1.5 | 0 | 0.0% |
| -1.5 to -1.0 | 0 | 0.0% |
| -1.0 to -0.5 | 6 | 2.9% |
| -0.5 to -0.25 | 32 | 15.7% |
| -0.25 to 0 | 45 | 22.1% |
| 0 to 0.25 | 32 | 15.7% |
| 0.25 to 0.5 | 53 | 26.0% |
| 0.5 to 1.0 | 31 | 15.2% |
| 1.0 to 1.5 | 2 | 1.0% |
| 1.5+ | 3 | 1.5% |

**Tail Dependency:** Top 10% of signals (20 signals) contribute 60.6% of total PnL

### R3: EMA + Time<10:30 + ADX>30

**Time Split:** First half (2026-01-23 to 2026-02-09), Second half (2026-02-10 to 2026-02-27)

| label | N | Win% | Avg MFE | Avg MAE | MFE/MAE | Avg PnL | Tot PnL | Runner% |
|---|---|---|---|---|---|---|---|---|
| First half (12 days) | 68 | 61.8 | 0.382 | -0.185 | 2.07 | 0.197 | 13.4 | 4.4 |
| Second half (12 days) | 73 | 47.9 | 0.216 | -0.207 | 1.04 | 0.009 | 0.6 | 0.0 |

**Symbols Net Positive:**

10/13 symbols net positive

| Symbol | N | Total PnL | Avg PnL |
|---|---|---|---|
| SLV | 10 | 4.94 | 0.494 |
| TSLA | 13 | 3.31 | 0.254 |
| GLD | 12 | 2.89 | 0.241 |
| QQQ | 13 | 1.84 | 0.141 |
| TSM | 10 | 1.81 | 0.181 |
| AMD | 11 | 0.81 | 0.074 |
| MSFT | 11 | 0.72 | 0.066 |
| SPY | 13 | 0.56 | 0.043 |
| META | 17 | 0.40 | 0.023 |
| GOOGL | 5 | 0.20 | 0.041 |
| NVDA | 6 | -0.59 | -0.098 |
| AAPL | 11 | -1.09 | -0.099 |
| AMZN | 9 | -1.73 | -0.192 |

**PnL Distribution (ATR units):**

| PnL Bucket | Count | % |
|---|---|---|
| <-1.5 | 0 | 0.0% |
| -1.5 to -1.0 | 0 | 0.0% |
| -1.0 to -0.5 | 7 | 5.0% |
| -0.5 to -0.25 | 21 | 14.9% |
| -0.25 to 0 | 36 | 25.5% |
| 0 to 0.25 | 30 | 21.3% |
| 0.25 to 0.5 | 29 | 20.6% |
| 0.5 to 1.0 | 15 | 10.6% |
| 1.0 to 1.5 | 0 | 0.0% |
| 1.5+ | 3 | 2.1% |

**Tail Dependency:** Top 10% of signals (14 signals) contribute 89.6% of total PnL

## 8b: Concrete Indicator Changes

Based on all findings, the recommended changes are:

### What Gets Killed
1. **MC signal generation** — Remove the Momentum Cascade (🔊) signal logic entirely
   - MC generates standalone signals that compete with BRK/REV signals
   - Its "auto-confirm subsequent signals" feature adds complexity without clear edge

2. **MC auto-confirm** — Remove the mechanism that auto-confirms later signals after MC fires

### What Gets Added / Changed
1. **EMA Hard Gate (post-9:50)** — After 9:50, suppress (not just dim) non-EMA-aligned signals
   - Pre-9:50 signals keep current behavior (EMA not yet established)
   - This replaces the evidence stack "dim" approach with a hard filter after 9:50

2. **Simple Auto-Confirm Rule** — Replace MC's auto-confirm with a deterministic rule:
   - Best candidate depends on 7b results (EMA + Time<10:30, or EMA + Counter-VWAP)
   - Signals meeting the rule get CONF ✓ marker without waiting for price follow-through
   - Much simpler than MC's momentum-detection logic

3. **QBS (🔇) stays** — QBS (Quiet Before Storm) is independent of MC and may still add value
   - Its removal should be evaluated separately

### Features Affected
- Evidence stack dim mode: The post-9:50 EMA gate makes dim redundant for non-EMA signals
- Runner Score: No change needed (already includes EMA as factor)
- Labels: MC-related glyphs (🔊) removed; auto-confirm ✓ logic simplified
- Alerts: MC-specific alertconditions removed

## 8c: Head-to-Head Comparison

| Config | Description | N | Per-Sig PnL | Total PnL | Win% | Complexity |
|---|---|---|---|---|---|---|
| Current v2.9 (as-is) | All signals, MC active | 1841 | 0.038 | 70.3 | 51.4 | ~1613 lines (current) |
| Kill MC, no replacement | Remove MC logic, keep all BRK/REV | 1841 | 0.038 | 70.3 | 51.4 | -~80 lines (MC removal) |
| Kill MC + EMA hard gate | Suppress non-EMA after 9:50 | 1633 | 0.051 | 83.6 | 53.0 | -~80 lines MC, +~5 lines gate |
| Kill MC + auto-confirm R1 | EMA+Time<10:30 auto-confirms | 1841 (389 auto-conf) | 0.038 | 70.3 | 51.4 | -~80 lines MC, +~10 lines rule |
| Kill MC + EMA gate + auto-confirm | Best of both | 1633 (389 auto-conf) | 0.051 | 83.6 | 53.0 | -~80 lines MC, +~15 lines |

### Key Insight

The EMA hard gate removes 208 signals with total PnL = -13.3 ATR.
This is beneficial — those signals average -0.064 ATR each.

## Final Recommendation

**Config: Kill MC + EMA Hard Gate + Simple Auto-Confirm (R1: EMA + Time<10:30)**

This is the cleanest option because:
1. **Removes ~80 lines** of MC complexity (signal generation + auto-confirm + alerts)
2. **EMA hard gate** eliminates net-negative non-EMA signals post-9:50 (simple boolean check)
3. **Auto-confirm rule** (EMA + Time<10:30) gives traders immediate confidence on the best signals
4. **QBS (🔇) can stay** — evaluate separately, it's independent of MC

### Implementation Order
1. Remove MC signal generation and auto-confirm logic
2. Add EMA hard gate: `if post950 and not ema_aligned then suppress`
3. Add auto-confirm rule: `if ema_aligned and time < 10:30 then auto_conf = true`
4. Clean up MC-specific alerts, labels, glyphs
5. Bump version to v3.0 (major: signal philosophy change)
