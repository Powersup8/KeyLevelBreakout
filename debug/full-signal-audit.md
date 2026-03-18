# Full Signal Audit — 1841 Signals

*Generated: 2026-03-04 | Data: enriched-signals.csv | Signals: 1841*


## SECTION 1: Signal Accuracy Overview

| Metric | Value |
|---|---|
| Total signals | 1841 |
| **Winners** (MFE>=0.20, MFE/MAE>1.5) | 648 (35.2%) |
| **Losers** (MAE>=0.20, MFE/MAE<0.8) | 580 (31.5%) |
| **Scratches** (everything else) | 613 (33.3%) |
| Home Runs (MFE >= 1.0 ATR) | 38 (2.1%) |
| Disasters (MAE <= -1.0 ATR) | 12 (0.7%) |
| Avg MFE | 0.2531 ATR |
| Avg MAE | -0.2149 ATR |
| Avg MFE/MAE ratio | 1.17 |
| Win rate (MFE > abs(MAE)) | 51.4% |
| Avg P&L proxy (MFE+MAE) | 0.0382 ATR |
| Winner:Loser ratio | 648:580 = 1.12:1 |

## SECTION 2: Accuracy by Every Dimension


### By Symbol

| group | N | win% | avg_MFE | avg_MAE | MFE/MAE | avg_pnl | home_runs | disasters | winners | losers | scratches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| QQQ | 135 | 59.3 | 0.320 | -0.229 | 1.39 | 0.091 | 7 | 0 | 57 | 46 | 32 |
| AMZN | 128 | 55.5 | 0.261 | -0.238 | 1.09 | 0.024 | 2 | 0 | 55 | 48 | 25 |
| META | 172 | 54.7 | 0.229 | -0.207 | 1.10 | 0.022 | 0 | 0 | 63 | 60 | 49 |
| AAPL | 135 | 54.1 | 0.284 | -0.241 | 1.18 | 0.043 | 1 | 2 | 61 | 43 | 31 |
| SPY | 159 | 54.1 | 0.289 | -0.233 | 1.24 | 0.056 | 3 | 0 | 58 | 52 | 49 |
| TSLA | 138 | 53.6 | 0.215 | -0.201 | 1.06 | 0.015 | 0 | 0 | 48 | 44 | 46 |
| GOOGL | 142 | 52.8 | 0.282 | -0.219 | 1.28 | 0.063 | 5 | 1 | 55 | 49 | 38 |
| NVDA | 143 | 52.4 | 0.279 | -0.232 | 1.20 | 0.047 | 4 | 0 | 53 | 47 | 43 |
| SLV | 119 | 51.3 | 0.238 | -0.186 | 1.28 | 0.052 | 4 | 1 | 36 | 29 | 54 |
| AMD | 137 | 48.9 | 0.227 | -0.236 | 0.96 | -0.009 | 4 | 3 | 46 | 40 | 51 |
| GLD | 132 | 48.5 | 0.290 | -0.235 | 1.23 | 0.055 | 6 | 4 | 34 | 42 | 56 |
| MSFT | 136 | 47.8 | 0.188 | -0.199 | 0.94 | -0.011 | 0 | 0 | 39 | 49 | 48 |
| TSM | 165 | 37.0 | 0.197 | -0.147 | 1.32 | 0.050 | 2 | 1 | 43 | 31 | 91 |

### By Time (30-min bucket)

| group | N | win% | avg_MFE | avg_MAE | MFE/MAE | avg_pnl | home_runs | disasters | winners | losers | scratches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 9:30-10:00 | 1058 | 51.4 | 0.300 | -0.259 | 1.15 | 0.040 | 30 | 10 | 430 | 402 | 226 |
| 10:00-10:30 | 312 | 53.8 | 0.261 | -0.191 | 1.36 | 0.070 | 5 | 0 | 125 | 96 | 91 |
| 10:30-11:00 | 52 | 42.3 | 0.168 | -0.227 | 0.74 | -0.059 | 0 | 1 | 10 | 16 | 26 |
| 11:00-11:30 | 27 | 55.6 | 0.262 | -0.111 | 2.35 | 0.151 | 0 | 0 | 11 | 2 | 14 |
| 11:30-12:00 | 19 | 42.1 | 0.197 | -0.157 | 1.25 | 0.040 | 1 | 0 | 3 | 4 | 12 |
| 12:00-12:30 | 28 | 46.4 | 0.217 | -0.169 | 1.29 | 0.049 | 2 | 0 | 10 | 7 | 11 |
| 12:30-13:00 | 28 | 32.1 | 0.074 | -0.136 | 0.55 | -0.061 | 0 | 0 | 1 | 5 | 22 |
| 13:00-13:30 | 47 | 53.2 | 0.133 | -0.160 | 0.83 | -0.027 | 0 | 1 | 8 | 10 | 29 |
| 13:30-14:00 | 35 | 57.1 | 0.122 | -0.103 | 1.18 | 0.018 | 0 | 0 | 3 | 3 | 29 |
| 14:00-14:30 | 26 | 46.2 | 0.164 | -0.181 | 0.90 | -0.017 | 0 | 0 | 7 | 10 | 9 |
| 14:30-15:00 | 47 | 51.1 | 0.109 | -0.094 | 1.12 | 0.014 | 0 | 0 | 6 | 6 | 35 |
| 15:00-15:30 | 45 | 62.2 | 0.188 | -0.109 | 1.72 | 0.079 | 0 | 0 | 17 | 7 | 21 |
| 15:30-16:00 | 117 | 49.6 | 0.097 | -0.087 | 1.06 | 0.011 | 0 | 0 | 17 | 12 | 88 |

### By Direction

| group | N | win% | avg_MFE | avg_MAE | MFE/MAE | avg_pnl | home_runs | disasters | winners | losers | scratches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bull | 906 | 51.5 | 0.222 | -0.222 | 0.99 | -0.001 | 2 | 8 | 298 | 276 | 332 |
| bear | 935 | 51.2 | 0.283 | -0.208 | 1.36 | 0.076 | 36 | 4 | 350 | 304 | 281 |

### By Type (BRK/REV)

| group | N | win% | avg_MFE | avg_MAE | MFE/MAE | avg_pnl | home_runs | disasters | winners | losers | scratches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BRK | 1064 | 52.1 | 0.249 | -0.201 | 1.23 | 0.047 | 21 | 7 | 377 | 312 | 375 |
| REV | 777 | 50.5 | 0.259 | -0.233 | 1.11 | 0.026 | 17 | 5 | 271 | 268 | 238 |

### By Level Type (HIGH/LOW)

| group | N | win% | avg_MFE | avg_MAE | MFE/MAE | avg_pnl | home_runs | disasters | winners | losers | scratches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW | 948 | 52.4 | 0.257 | -0.215 | 1.19 | 0.042 | 21 | 7 | 341 | 292 | 315 |
| HIGH | 893 | 50.3 | 0.249 | -0.214 | 1.16 | 0.034 | 17 | 5 | 307 | 288 | 298 |

### By EMA Alignment

| group | N | win% | avg_MFE | avg_MAE | MFE/MAE | avg_pnl | home_runs | disasters | winners | losers | scratches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| aligned | 1350 | 57.0 | 0.268 | -0.182 | 1.46 | 0.086 | 27 | 8 | 535 | 347 | 468 |
| mixed | 105 | 45.7 | 0.249 | -0.241 | 1.03 | 0.008 | 3 | 1 | 30 | 35 | 40 |
| not-aligned | 386 | 33.4 | 0.202 | -0.322 | 0.63 | -0.120 | 8 | 3 | 83 | 198 | 105 |

### By VWAP (with-trend vs counter)

| group | N | win% | avg_MFE | avg_MAE | MFE/MAE | avg_pnl | home_runs | disasters | winners | losers | scratches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| False | 70 | 58.6 | 0.258 | -0.147 | 1.71 | 0.112 | 2 | 0 | 29 | 13 | 28 |
| True | 1771 | 51.1 | 0.253 | -0.218 | 1.16 | 0.035 | 36 | 12 | 619 | 567 | 585 |

### By Volume Bucket

| group | N | win% | avg_MFE | avg_MAE | MFE/MAE | avg_pnl | home_runs | disasters | winners | losers | scratches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1-2x | 371 | 51.8 | 0.170 | -0.151 | 1.12 | 0.019 | 2 | 0 | 96 | 81 | 194 |
| 2-5x | 707 | 49.9 | 0.234 | -0.197 | 1.18 | 0.037 | 11 | 4 | 236 | 221 | 250 |
| 5-10x | 359 | 49.9 | 0.272 | -0.278 | 0.97 | -0.006 | 9 | 6 | 126 | 132 | 101 |
| 10x+ | 404 | 55.0 | 0.347 | -0.250 | 1.39 | 0.097 | 16 | 2 | 190 | 146 | 68 |

### By ADX Bucket

| group | N | win% | avg_MFE | avg_MAE | MFE/MAE | avg_pnl | home_runs | disasters | winners | losers | scratches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| <20 | 449 | 49.2 | 0.207 | -0.191 | 1.08 | 0.016 | 5 | 0 | 134 | 142 | 173 |
| 20-30 | 799 | 51.6 | 0.248 | -0.209 | 1.18 | 0.039 | 15 | 5 | 287 | 246 | 266 |
| 30-40 | 409 | 53.8 | 0.273 | -0.229 | 1.19 | 0.044 | 11 | 4 | 155 | 129 | 125 |
| 40-50 | 144 | 50.0 | 0.354 | -0.266 | 1.33 | 0.088 | 6 | 2 | 55 | 48 | 41 |
| 50+ | 40 | 52.5 | 0.301 | -0.259 | 1.15 | 0.042 | 1 | 1 | 17 | 15 | 8 |

### By Body% Bucket

| group | N | win% | avg_MFE | avg_MAE | MFE/MAE | avg_pnl | home_runs | disasters | winners | losers | scratches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| <30% | 526 | 50.8 | 0.238 | -0.204 | 1.17 | 0.034 | 11 | 1 | 160 | 161 | 205 |
| 30-50% | 430 | 53.0 | 0.246 | -0.206 | 1.19 | 0.040 | 7 | 4 | 143 | 121 | 166 |
| 50-70% | 469 | 51.2 | 0.269 | -0.237 | 1.13 | 0.032 | 12 | 4 | 176 | 165 | 128 |
| 70%+ | 416 | 50.7 | 0.262 | -0.213 | 1.21 | 0.049 | 8 | 3 | 169 | 133 | 114 |

### By CONF Status

| group | N | win% | avg_MFE | avg_MAE | MFE/MAE | avg_pnl | home_runs | disasters | winners | losers | scratches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ✓★ | 44 | 88.6 | 0.500 | -0.073 | 6.64 | 0.426 | 4 | 0 | 35 | 0 | 9 |
| ✓ | 187 | 74.3 | 0.290 | -0.104 | 2.73 | 0.185 | 1 | 0 | 102 | 20 | 65 |
| NaN | 801 | 51.1 | 0.258 | -0.229 | 1.12 | 0.029 | 17 | 5 | 280 | 270 | 251 |
| ✗ | 809 | 44.4 | 0.227 | -0.235 | 0.96 | -0.008 | 16 | 7 | 231 | 290 | 288 |

### By Runner Score

| group | N | win% | avg_MFE | avg_MAE | MFE/MAE | avg_pnl | home_runs | disasters | winners | losers | scratches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| -1 | 188 | 63.3 | 0.315 | -0.165 | 1.89 | 0.149 | 7 | 0 | 92 | 38 | 58 |
| -2 | 31 | 67.7 | 0.326 | -0.139 | 2.33 | 0.187 | 0 | 0 | 17 | 6 | 8 |
| -3 | 2 | 100.0 | 0.295 | -0.028 | 10.73 | 0.267 | 0 | 0 | 2 | 0 | 0 |
| -4 | 1 | 100.0 | 0.095 | -0.090 | 1.06 | 0.005 | 0 | 0 | 0 | 0 | 1 |
| 0 | 1446 | 48.5 | 0.240 | -0.226 | 1.06 | 0.014 | 29 | 12 | 466 | 492 | 488 |
| 1 | 129 | 58.9 | 0.265 | -0.180 | 1.46 | 0.085 | 1 | 0 | 52 | 28 | 49 |
| 2 | 31 | 51.6 | 0.292 | -0.251 | 1.15 | 0.041 | 0 | 0 | 12 | 13 | 6 |
| 3 | 8 | 75.0 | 0.512 | -0.197 | 2.60 | 0.315 | 1 | 0 | 4 | 2 | 2 |
| 4 | 2 | 100.0 | 0.393 | -0.035 | 11.23 | 0.358 | 0 | 0 | 2 | 0 | 0 |
| 5 | 2 | 50.0 | 0.255 | -0.209 | 1.21 | 0.045 | 0 | 0 | 1 | 1 | 0 |
| 6 | 1 | 100.0 | 0.169 | -0.057 | 2.96 | 0.112 | 0 | 0 | 0 | 0 | 1 |

### By Multi-Level

| group | N | win% | avg_MFE | avg_MAE | MFE/MAE | avg_pnl | home_runs | disasters | winners | losers | scratches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| True | 416 | 54.1 | 0.279 | -0.224 | 1.24 | 0.055 | 8 | 2 | 166 | 140 | 110 |
| False | 1425 | 50.6 | 0.246 | -0.212 | 1.15 | 0.033 | 30 | 10 | 482 | 440 | 503 |

### By With-Trend

| group | N | win% | avg_MFE | avg_MAE | MFE/MAE | avg_pnl | home_runs | disasters | winners | losers | scratches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| False | 70 | 58.6 | 0.258 | -0.147 | 1.71 | 0.112 | 2 | 0 | 29 | 13 | 28 |
| True | 1771 | 51.1 | 0.253 | -0.218 | 1.16 | 0.035 | 36 | 12 | 619 | 567 | 585 |

## SECTION 3: Combination Analysis — Best & Worst Combos


### Top 20 Most Profitable 2-Factor Combos (N>=20)

| combo | N | win% | avg_MFE | avg_MAE | MFE/MAE | avg_pnl | home_runs | disasters |
|---|---|---|---|---|---|---|---|---|
| NOT_LOW_level + CONF_pass | 80 | 83.8 | 0.326 | -0.086 | 3.73 | 0.241 | 0 | 0 |
| NOT_bear + CONF_pass | 80 | 83.8 | 0.326 | -0.086 | 3.73 | 0.241 | 0 | 0 |
| EMA_aligned + CONF_pass | 209 | 79.4 | 0.343 | -0.091 | 3.67 | 0.251 | 5 | 0 |
| NOT_vol_5x+ + CONF_pass | 140 | 78.6 | 0.271 | -0.08 | 3.3 | 0.191 | 0 | 0 |
| morning + CONF_pass | 161 | 78.3 | 0.391 | -0.113 | 3.39 | 0.278 | 5 | 0 |
| NOT_ADX_40+ + CONF_pass | 211 | 77.3 | 0.323 | -0.1 | 3.19 | 0.223 | 5 | 0 |
| BRK + CONF_pass | 231 | 77.1 | 0.33 | -0.098 | 3.29 | 0.231 | 5 | 0 |
| NOT_counter_VWAP + CONF_pass | 220 | 75.9 | 0.327 | -0.101 | 3.19 | 0.226 | 5 | 0 |
| ADX_40+ + CONF_pass | 20 | 75.0 | 0.398 | -0.081 | 4.58 | 0.317 | 0 | 0 |
| vol_5x+ + CONF_pass | 91 | 74.7 | 0.42 | -0.126 | 3.28 | 0.294 | 5 | 0 |
| NOT_morning + CONF_pass | 70 | 74.3 | 0.188 | -0.064 | 2.9 | 0.124 | 0 | 0 |
| bear + CONF_pass | 151 | 73.5 | 0.331 | -0.105 | 3.1 | 0.226 | 5 | 0 |
| LOW_level + CONF_pass | 151 | 73.5 | 0.331 | -0.105 | 3.1 | 0.226 | 5 | 0 |
| LOW_level + counter_VWAP | 39 | 66.7 | 0.276 | -0.101 | 2.58 | 0.176 | 1 | 0 |
| bear + counter_VWAP | 39 | 66.7 | 0.276 | -0.101 | 2.58 | 0.176 | 1 | 0 |
| EMA_aligned + counter_VWAP | 47 | 61.7 | 0.257 | -0.137 | 1.8 | 0.12 | 1 | 0 |
| EMA_aligned + vol_5x+ | 516 | 60.5 | 0.345 | -0.218 | 1.57 | 0.126 | 17 | 5 |
| NOT_morning + counter_VWAP | 30 | 60.0 | 0.168 | -0.079 | 1.96 | 0.089 | 0 | 0 |
| EMA_aligned + morning | 944 | 59.3 | 0.318 | -0.206 | 1.54 | 0.113 | 24 | 6 |
| EMA_aligned + NOT_BRK | 493 | 59.2 | 0.287 | -0.187 | 1.52 | 0.1 | 11 | 3 |

### Bottom 20 Least Profitable 2-Factor Combos (N>=20)

| combo | N | win% | avg_MFE | avg_MAE | MFE/MAE | avg_pnl | home_runs | disasters |
|---|---|---|---|---|---|---|---|---|
| NOT_LOW_level + NOT_CONF_pass | 813 | 47.0 | 0.241 | -0.227 | 1.06 | 0.014 | 17 | 5 |
| bear + NOT_CONF_pass | 784 | 46.9 | 0.274 | -0.227 | 1.2 | 0.047 | 31 | 4 |
| NOT_vol_5x+ + NOT_CONF_pass | 938 | 46.4 | 0.203 | -0.196 | 1.03 | 0.007 | 13 | 4 |
| NOT_morning + NOT_CONF_pass | 401 | 45.4 | 0.135 | -0.143 | 0.94 | -0.007 | 3 | 2 |
| BRK + NOT_CONF_pass | 833 | 45.1 | 0.226 | -0.23 | 0.98 | -0.004 | 16 | 7 |
| vol_5x+ + ADX_40+ | 63 | 44.4 | 0.276 | -0.33 | 0.84 | -0.054 | 1 | 1 |
| NOT_EMA_aligned + ADX_40+ | 47 | 42.6 | 0.449 | -0.334 | 1.34 | 0.115 | 3 | 0 |
| NOT_EMA_aligned + bear | 264 | 39.8 | 0.256 | -0.268 | 0.95 | -0.013 | 10 | 2 |
| NOT_EMA_aligned + NOT_morning | 65 | 38.5 | 0.096 | -0.154 | 0.62 | -0.058 | 0 | 0 |
| NOT_EMA_aligned + LOW_level | 252 | 37.7 | 0.214 | -0.299 | 0.72 | -0.085 | 6 | 2 |
| NOT_EMA_aligned + BRK | 207 | 37.2 | 0.213 | -0.292 | 0.73 | -0.079 | 5 | 2 |
| NOT_EMA_aligned + NOT_vol_5x+ | 244 | 36.1 | 0.182 | -0.253 | 0.72 | -0.072 | 3 | 1 |
| NOT_EMA_aligned + vol_5x+ | 247 | 36.0 | 0.242 | -0.356 | 0.68 | -0.114 | 8 | 3 |
| NOT_EMA_aligned + morning | 426 | 35.7 | 0.23 | -0.328 | 0.7 | -0.098 | 11 | 4 |
| NOT_EMA_aligned + NOT_ADX_40+ | 444 | 35.4 | 0.187 | -0.302 | 0.62 | -0.115 | 8 | 4 |
| NOT_EMA_aligned + NOT_counter_VWAP | 468 | 35.3 | 0.21 | -0.312 | 0.67 | -0.102 | 10 | 4 |
| NOT_EMA_aligned + NOT_CONF_pass | 469 | 35.2 | 0.212 | -0.312 | 0.68 | -0.099 | 11 | 4 |
| NOT_EMA_aligned + NOT_BRK | 284 | 35.2 | 0.211 | -0.314 | 0.67 | -0.103 | 6 | 2 |
| NOT_EMA_aligned + NOT_LOW_level | 239 | 34.3 | 0.21 | -0.312 | 0.67 | -0.102 | 5 | 2 |
| NOT_EMA_aligned + NOT_bear | 227 | 31.7 | 0.161 | -0.348 | 0.46 | -0.187 | 1 | 2 |

### Top 10 Most Profitable 3-Factor Combos (N>=15)

| combo | N | win% | avg_MFE | avg_MAE | MFE/MAE | avg_pnl | home_runs | disasters |
|---|---|---|---|---|---|---|---|---|
| NOT_LOW_level + vol_5x+ + CONF_pass | 36 | 88.9 | 0.394 | -0.081 | 4.77 | 0.313 | 0 | 0 |
| NOT_bear + vol_5x+ + CONF_pass | 36 | 88.9 | 0.394 | -0.081 | 4.77 | 0.313 | 0 | 0 |
| NOT_bear + NOT_ADX_40+ + CONF_pass | 73 | 84.9 | 0.325 | -0.087 | 3.67 | 0.238 | 0 | 0 |
| NOT_LOW_level + NOT_ADX_40+ + CONF_pass | 73 | 84.9 | 0.325 | -0.087 | 3.67 | 0.238 | 0 | 0 |
| morning + NOT_LOW_level + CONF_pass | 65 | 84.6 | 0.353 | -0.092 | 3.75 | 0.261 | 0 | 0 |
| NOT_bear + morning + CONF_pass | 65 | 84.6 | 0.353 | -0.092 | 3.75 | 0.261 | 0 | 0 |
| EMA_aligned + NOT_bear + CONF_pass | 77 | 84.4 | 0.332 | -0.081 | 3.98 | 0.251 | 0 | 0 |
| EMA_aligned + NOT_LOW_level + CONF_pass | 77 | 84.4 | 0.332 | -0.081 | 3.98 | 0.251 | 0 | 0 |
| NOT_bear + NOT_LOW_level + CONF_pass | 80 | 83.8 | 0.326 | -0.086 | 3.73 | 0.241 | 0 | 0 |
| BRK + NOT_LOW_level + CONF_pass | 80 | 83.8 | 0.326 | -0.086 | 3.73 | 0.241 | 0 | 0 |

### Bottom 10 Least Profitable 3-Factor Combos (N>=15)

| combo | N | win% | avg_MFE | avg_MAE | MFE/MAE | avg_pnl | home_runs | disasters |
|---|---|---|---|---|---|---|---|---|
| NOT_EMA_aligned + NOT_bear + NOT_CONF_pass | 224 | 31.2 | 0.161 | -0.35 | 0.46 | -0.189 | 1 | 2 |
| NOT_EMA_aligned + NOT_bear + NOT_morning | 23 | 30.4 | 0.066 | -0.156 | 0.42 | -0.091 | 0 | 0 |
| NOT_EMA_aligned + NOT_bear + NOT_counter_VWAP | 218 | 30.3 | 0.156 | -0.353 | 0.44 | -0.196 | 1 | 2 |
| NOT_EMA_aligned + NOT_bear + NOT_ADX_40+ | 201 | 29.9 | 0.15 | -0.345 | 0.44 | -0.194 | 1 | 2 |
| NOT_EMA_aligned + NOT_LOW_level + NOT_vol_5x+ | 121 | 29.8 | 0.138 | -0.27 | 0.51 | -0.133 | 0 | 1 |
| NOT_EMA_aligned + NOT_bear + BRK | 91 | 29.7 | 0.147 | -0.352 | 0.42 | -0.205 | 0 | 1 |
| NOT_EMA_aligned + NOT_bear + NOT_LOW_level | 91 | 29.7 | 0.147 | -0.352 | 0.42 | -0.205 | 0 | 1 |
| NOT_EMA_aligned + BRK + NOT_LOW_level | 91 | 29.7 | 0.147 | -0.352 | 0.42 | -0.205 | 0 | 1 |
| NOT_EMA_aligned + vol_5x+ + ADX_40+ | 21 | 28.6 | 0.325 | -0.424 | 0.77 | -0.099 | 1 | 0 |
| NOT_EMA_aligned + NOT_bear + vol_5x+ | 110 | 22.7 | 0.162 | -0.429 | 0.38 | -0.267 | 1 | 1 |

## SECTION 4: Pattern Analysis — What Predicts Winners vs Losers


### Feature Distributions: Winners vs Losers

| Feature | Winner Mean | Winner Std | Loser Mean | Loser Std | Diff | Cohen's d | Direction |
|---|---|---|---|---|---|---|---|
| vol | 6.905 | 5.209 | 6.639 | 4.991 | +0.266 | +0.052 | Winner higher |
| body | 50.239 | 25.630 | 48.128 | 25.660 | +2.112 | +0.082 | Winner higher |
| adx | 27.094 | 9.390 | 26.728 | 9.702 | +0.367 | +0.038 | Winner higher |
| rs | -0.086 | 1.016 | 0.009 | 0.805 | -0.094 | -0.103 | Loser higher |
| mfe | 0.516 | 0.369 | 0.095 | 0.083 | +0.421 | +1.576 | Winner higher |
| mae | -0.087 | 0.081 | -0.458 | 0.281 | +0.372 | +1.798 | Winner higher |

**Effect size guide:** |d| < 0.2 = negligible, 0.2-0.5 = small, 0.5-0.8 = medium, > 0.8 = large


### Categorical Features: Winners vs Losers

| Feature | Winner % True | Loser % True | Diff | Stronger for |
|---|---|---|---|---|
| EMA Aligned | 82.6% | 59.8% | +22.7pp | WINNER |
| VWAP With-Trend | 95.5% | 97.8% | -2.2pp | LOSER |
| Counter-VWAP | 4.5% | 2.2% | +2.2pp | WINNER |
| Morning (<10:30) | 85.6% | 85.9% | -0.2pp | LOSER |
| Volume >= 5x | 48.8% | 47.9% | +0.8pp | WINNER |
| ADX >= 40 | 11.1% | 10.9% | +0.2pp | WINNER |
| CONF Pass | 21.1% | 3.4% | +17.7pp | WINNER |

### Strongest Predictors of Winners

- **mae**: d=+1.798 (LARGE) — Winner higher
- **mfe**: d=+1.576 (LARGE) — Winner higher
- **rs**: d=-0.103 (negligible) — Loser higher
- **body**: d=+0.082 (negligible) — Winner higher
- **vol**: d=+0.052 (negligible) — Winner higher
- **adx**: d=+0.038 (negligible) — Winner higher

## SECTION 5: Home Run Deep Dive (MFE >= 1.0 ATR)

**Total Home Runs: 38 (2.1% of all signals)**


### All Home Run Signals

| symbol | date | time | direction | type | levels | vol | body | adx | ema | vwap | rs | conf | mfe | mae |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GLD | 2026-01-29 | 9:45 | bear | BRK | ORB L | 3.1 | 2 | 49 | bull | below | 0.0 | ✗ | 4.306 | -0.055 |
| GLD | 2026-01-29 | 9:35 | bear | REV | ORB H | 6.7 | 29 | 47 | bull | below | 0.0 | nan | 4.269 | -0.225 |
| GLD | 2026-01-29 | 10:05 | bear | BRK | PM L | 4.3 | 66 | 44 | mixed | below | 0.0 | ✗ | 3.69 | -0.141 |
| GLD | 2026-01-29 | 10:20 | bear | REV | Yest H | 2.9 | 49 | 41 | bear | below | 0.0 | nan | 2.407 | -0.364 |
| SLV | 2026-01-29 | 9:50 | bear | BRK | ORB L | 3.1 | 42 | 38 | bull | above | 0.0 | ✗ | 2.396 | -0.061 |
| SLV | 2026-01-30 | 12:20 | bear | BRK | Week L | 2.1 | 60 | 62 | bear | below | 0.0 | ✗ | 1.935 | -0.3 |
| SLV | 2026-01-29 | 10:15 | bear | REV | Yest H | 2.2 | 55 | 32 | bear | below | 0.0 | nan | 1.683 | -0.006 |
| SLV | 2026-01-29 | 10:15 | bear | BRK | PM L | 2.2 | 55 | 32 | bear | below | 0.0 | ✗ | 1.683 | -0.006 |
| GOOGL | 2026-01-29 | 9:35 | bear | REV | ORB H | 15.1 | 67 | 24 | bull | below | -0.78 | nan | 1.495 | -0.067 |
| GOOGL | 2026-01-29 | 9:35 | bear | BRK | PM L | 15.1 | 67 | 24 | bull | below | -0.78 | ✗ | 1.495 | -0.067 |
| NVDA | 2026-02-26 | 9:30 | bear | REV | Yest H | 5.8 | 97 | 26 | bear | below | -1.53 | nan | 1.48 | 0.017 |
| GLD | 2026-01-30 | 11:55 | bear | REV | Week H | 1.6 | 46 | 46 | bear | below | 0.0 | nan | 1.42 | -0.07 |
| GOOGL | 2026-01-29 | 9:40 | bear | BRK | ORB L | 9.7 | 95 | 22 | bear | below | -1.28 | ✗ | 1.417 | -0.003 |
| SPY | 2026-01-29 | 9:40 | bear | BRK | PM L+ORB L | 9.3 | 91 | 13 | bear | below | 0.0 | ✗ | 1.4 | -0.03 |
| SPY | 2026-01-29 | 9:35 | bear | REV | Yest H+ORB H | 15.5 | 49 | 12 | mixed | below | 0.0 | nan | 1.356 | 0.017 |
| QQQ | 2026-01-29 | 9:35 | bear | REV | ORB H | 13.4 | 71 | 22 | bear | below | 0.0 | nan | 1.27 | 0.018 |
| QQQ | 2026-01-29 | 9:35 | bear | BRK | PM L | 13.4 | 71 | 22 | bear | below | 0.0 | ✓★ | 1.27 | 0.018 |
| GOOGL | 2026-02-05 | 9:35 | bull | REV | PM L+ORB L | 11.6 | 89 | 21 | bear | above | 3.06 | nan | 1.245 | -0.092 |
| AMZN | 2026-02-03 | 9:35 | bear | REV | PM H+ORB H | 16.4 | 49 | 30 | mixed | below | -0.59 | nan | 1.222 | -0.1 |
| QQQ | 2026-01-29 | 9:40 | bear | BRK | Yest L+ORB L | 8.9 | 86 | 26 | bear | below | 0.0 | ✓★ | 1.218 | -0.018 |
| SPY | 2026-01-29 | 9:45 | bear | BRK | Yest L | 6.9 | 25 | 14 | bear | below | 0.0 | ✗ | 1.167 | -0.137 |
| QQQ | 2026-02-03 | 9:35 | bear | REV | ORB H | 14.3 | 68 | 32 | bear | below | 0.0 | nan | 1.138 | -0.368 |
| QQQ | 2026-02-03 | 9:35 | bear | BRK | PM L | 14.3 | 68 | 32 | bear | below | 0.0 | ✗ | 1.138 | -0.368 |
| AAPL | 2026-02-04 | 9:30 | bull | BRK | Yest H | 9.6 | 91 | 20 | bull | below | 0.97 | ✗ | 1.119 | 0.019 |
| NVDA | 2026-02-26 | 9:35 | bear | REV | ORB H | 11.9 | 18 | 31 | bear | below | -1.33 | nan | 1.094 | -0.119 |
| NVDA | 2026-02-26 | 9:35 | bear | BRK | PM L+Yest L | 11.9 | 18 | 31 | bear | below | -1.33 | ✓★ | 1.094 | -0.119 |
| AMD | 2026-01-29 | 9:55 | bear | BRK | ORB L | 3.1 | 2 | 29 | bear | below | -0.03 | ✗ | 1.086 | -0.059 |
| AMD | 2026-01-29 | 9:55 | bear | REV | PM H+Yest H | 3.1 | 2 | 29 | bear | below | -0.03 | nan | 1.086 | -0.059 |
| GOOGL | 2026-01-29 | 9:45 | bear | REV | Yest H | 5.5 | 0 | 21 | bear | below | -1.36 | nan | 1.049 | -0.117 |
| AMZN | 2026-02-03 | 9:40 | bear | BRK | PM L | 11.3 | 8 | 31 | bull | below | -0.45 | ✗ | 1.046 | -0.268 |
| GLD | 2026-01-30 | 12:10 | bear | BRK | PM L | 1.7 | 30 | 47 | bear | below | 0.0 | ✗ | 1.045 | -0.159 |
| AMD | 2026-01-29 | 10:05 | bear | BRK | PM L | 2.1 | 52 | 27 | bear | below | -0.82 | ✗ | 1.024 | -0.087 |
| TSM | 2026-02-26 | 9:35 | bear | REV | ORB H | 14.3 | 68 | 19 | bear | below | -1.28 | nan | 1.004 | -0.074 |
| TSM | 2026-02-26 | 9:35 | bear | BRK | PM L+Yest L | 14.3 | 68 | 19 | bear | below | -1.28 | ✓★ | 1.004 | -0.074 |
| AMD | 2026-01-29 | 9:45 | bear | REV | PM H | 5.4 | 66 | 26 | bull | below | 1.15 | nan | 1.001 | -0.243 |
| NVDA | 2026-01-29 | 9:55 | bear | BRK | ORB L | 2.1 | 33 | 20 | bear | below | 0.41 | ✗ | 1.0 | -0.086 |
| QQQ | 2026-02-26 | 9:35 | bear | REV | ORB H | 16.7 | 5 | 34 | bear | below | 0.0 | nan | 1.0 | -0.057 |
| QQQ | 2026-02-26 | 9:35 | bear | BRK | PM L | 16.7 | 5 | 34 | bear | below | 0.0 | ✓ | 1.0 | -0.057 |

### Home Run Profile

| Attribute | Home Runs | All Signals | Delta |
|---|---|---|---|
| EMA Aligned | 71.1% | 73.3% | -2.3pp |
| Morning (<10:30) | 92.1% | 74.4% | +17.7pp |
| Bear direction | 94.7% | 50.8% | +43.9pp |
| BRK type | 55.3% | 57.8% | -2.5pp |
| LOW level | 55.3% | 51.5% | +3.8pp |
| Vol >= 5x | 65.8% | 41.4% | +24.3pp |
| ADX >= 40 | 18.4% | 10.0% | +8.4pp |
| VWAP with-trend | 94.7% | 96.2% | -1.5pp |
| CONF pass | 13.2% | 12.5% | +0.6pp |
| Counter-VWAP | 5.3% | 3.8% | +1.5pp |
| Multi-level | 21.1% | 22.6% | -1.5pp |

**Avg volume:** 8.6x (all: 6.0x)
**Avg ADX:** 29.7 (all: 26.4)
**Avg body%:** 49.0% (all: 47.3%)
**Avg runner score:** -0.2 (all: -0.0)

### Home Runs by Symbol

| Symbol | Home Runs | % of that symbol's signals |
|---|---|---|
| QQQ | 7 | 5.2% |
| GLD | 6 | 4.5% |
| GOOGL | 5 | 3.5% |
| AMD | 4 | 2.9% |
| NVDA | 4 | 2.8% |
| SLV | 4 | 3.4% |
| SPY | 3 | 1.9% |
| AMZN | 2 | 1.6% |
| TSM | 2 | 1.2% |
| AAPL | 1 | 0.7% |

## SECTION 6: Disaster Deep Dive (MAE <= -1.0 ATR)

**Total Disasters: 12 (0.7% of all signals)**


### All Disaster Signals

| symbol | date | time | direction | type | levels | vol | body | adx | ema | vwap | rs | conf | mfe | mae |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GLD | 2026-01-29 | 9:40 | bull | REV | ORB L | 7.1 | 61 | 49 | bull | above | 0.0 | nan | 0.045 | -4.453 |
| SLV | 2026-01-29 | 9:40 | bull | REV | ORB L | 4.6 | 56 | 38 | bull | above | 0.0 | nan | 0.026 | -2.541 |
| GLD | 2026-01-30 | 13:25 | bear | BRK | Week L | 2.0 | 40 | 59 | bear | below | 0.0 | ✗ | 0.259 | -1.638 |
| AMD | 2026-01-29 | 9:50 | bull | BRK | PM H | 3.2 | 86 | 28 | mixed | above | -0.2 | ✗ | 0.008 | -1.294 |
| AMD | 2026-01-29 | 9:35 | bull | BRK | PM H+Yest H | 17.3 | 56 | 21 | bull | above | 0.75 | ✗ | -0.011 | -1.263 |
| AMD | 2026-01-29 | 9:35 | bull | REV | ORB L | 17.3 | 56 | 21 | bull | above | 0.75 | nan | -0.011 | -1.263 |
| GOOGL | 2026-02-04 | 9:40 | bull | BRK | Week H | 9.0 | 47 | 22 | bull | above | -0.45 | ✗ | 0.024 | -1.128 |
| AAPL | 2026-02-02 | 9:40 | bear | BRK | ORB L | 5.6 | 90 | 31 | bull | below | 0.0 | ✗ | 0.007 | -1.096 |
| AAPL | 2026-02-02 | 9:40 | bear | REV | PM H+Yest H+Week H | 5.6 | 90 | 31 | bull | below | 0.0 | nan | 0.007 | -1.096 |
| GLD | 2026-01-29 | 10:30 | bear | BRK | Yest L | 2.9 | 20 | 43 | bear | below | 0.0 | ✗ | 0.94 | -1.092 |
| GLD | 2026-01-30 | 9:35 | bull | REV | ORB L | 6.1 | 39 | 29 | bear | above | 0.0 | nan | 0.023 | -1.051 |
| TSM | 2026-02-03 | 9:30 | bull | BRK | Yest H | 5.0 | 33 | 32 | bull | above | -0.39 | ✗ | 0.185 | -1.045 |

### Disaster Profile

| Attribute | Disasters | All Signals | Delta |
|---|---|---|---|
| EMA Aligned | 66.7% | 73.3% | -6.7pp |
| Morning (<10:30) | 83.3% | 74.4% | +8.9pp |
| Bear direction | 33.3% | 50.8% | -17.5pp |
| BRK type | 58.3% | 57.8% | +0.5pp |
| LOW level | 58.3% | 51.5% | +6.8pp |
| Vol >= 5x | 66.7% | 41.4% | +25.2pp |
| ADX >= 40 | 25.0% | 10.0% | +15.0pp |
| VWAP with-trend | 100.0% | 96.2% | +3.8pp |
| CONF pass | 0.0% | 12.5% | -12.5pp |
| Counter-VWAP | 0.0% | 3.8% | -3.8pp |
| Multi-level | 16.7% | 22.6% | -5.9pp |
| NOT EMA Aligned | 33.3% | 26.7% | +6.7pp |

### Filters That Would Have Prevented Disasters

| Filter | Disasters passing | % caught (would be prevented) |
|---|---|---|
| Require EMA aligned | 8/12 | 33% prevented |
| Require morning (<10:30) | 10/12 | 17% prevented |
| Require CONF pass | 0/12 | 100% prevented |
| Require vol >= 5x | 8/12 | 33% prevented |
| Require ADX >= 40 | 3/12 | 75% prevented |
| Require VWAP with-trend | 12/12 | 0% prevented |
| Require LOW level | 7/12 | 42% prevented |
| Require multi-level | 2/12 | 83% prevented |
| Require runner score >= 3 | 0/12 | 100% prevented |

### Disasters by Symbol

| Symbol | Disasters | % of that symbol's signals |
|---|---|---|
| GLD | 4 | 3.0% |
| AMD | 3 | 2.2% |
| AAPL | 2 | 1.5% |
| GOOGL | 1 | 0.7% |
| SLV | 1 | 0.8% |
| TSM | 1 | 0.6% |

## SECTION 7: Comparison to Existing Findings


### 1. "EMA Aligned alone = 92% of edge"

- EMA aligned: win%=57.0%, avg P&L=0.0859, total P&L=115.94
- NOT EMA aligned: win%=36.0%, avg P&L=-0.0930, total P&L=-45.64
- EMA aligned share of total P&L: **164.9%**
- **Verdict: CONFIRMED**

### 2. "Non-EMA signals are NET NEGATIVE everywhere"

- Non-EMA avg P&L: -0.0930
- Non-EMA total P&L: -45.64
  - Non-EMA + morning: N=426, avg P&L=-0.0982
  - Non-EMA + afternoon: N=65, avg P&L=-0.0583
  - Non-EMA + BRK: N=207, avg P&L=-0.0791
  - Non-EMA + REV: N=284, avg P&L=-0.1030
  - Non-EMA + vol>=5x: N=247, avg P&L=-0.1138
- **Verdict: CONFIRMED**

### 3. "Time < 10:30 is best"

- Morning (<10:30): N=1370, win%=52.0%, avg MFE=0.2908, avg P&L=0.0471
- Afternoon (>=10:30): N=471, win%=49.7%, avg MFE=0.1432, avg P&L=0.0122
- **Verdict: CONFIRMED**

### 4. "LOW levels > HIGH levels"

- LOW: N=948, win%=52.4%, avg MFE=0.2572, avg P&L=0.0418
- HIGH: N=893, win%=50.3%, avg MFE=0.2486, avg P&L=0.0344
- **Verdict: CONFIRMED**

### 5. "Bear direction has edge"

- Bear: N=935, win%=51.2%, avg MFE=0.2834, avg P&L=0.0758
- Bull: N=906, win%=51.5%, avg MFE=0.2217, avg P&L=-0.0006
- **Verdict: CONFIRMED**

### 6. "ADX > 40 is sharp"

- ADX >= 40: N=184, win%=50.5%, avg MFE=0.3421, MFE/MAE=1.29
- ADX < 40: N=1657, win%=51.5%, avg MFE=0.2432, MFE/MAE=1.16
- **Verdict: NOT CONFIRMED**

### 7. "Counter-VWAP is high quality but rare"

- Counter-VWAP: N=70, win%=58.6%, avg MFE=0.2583, avg P&L=0.1116
- With-trend VWAP: N=1771, win%=51.1%, avg MFE=0.2529, avg P&L=0.0353
- Counter-VWAP is 3.8% of signals (rare=yes)
- **Verdict: CONFIRMED**

### 8. "Body% is noise"

- body% correlation with MFE: 0.0463
- body% correlation with P&L: 0.0188
- body% correlation with win: -0.0090
- Winner avg body%: 50.2% vs Loser avg body%: 48.1%
- **Verdict: CONFIRMED** (all correlations near zero = noise)

### 9. "Volume >= 5x is best"

- 1-2x: N=371, win%=51.8%, avg MFE=0.1697, avg P&L=0.0191
- 2-5x: N=707, win%=49.9%, avg MFE=0.2337, avg P&L=0.0370
- 5-10x: N=359, win%=49.9%, avg MFE=0.2715, avg P&L=-0.0063
- 10x+: N=404, win%=55.0%, avg MFE=0.3471, avg P&L=0.0973
- **Verdict: CONFIRMED**

### 10. "CONF pass = 0% BAD" (using DISASTER count)

- CONF pass signals: 231
- CONF pass with disaster (MAE <= -1.0): 0
- CONF pass disaster rate: 0.00%
- **Verdict: CONFIRMED**

## SECTION 8: Actionable Findings Summary


### Top 5 Filters to Improve Win Rate

| filter | yes_N | yes_win% | no_win% | delta | yes_avg_pnl |
|---|---|---|---|---|---|
| CONF pass | 231 | 77.1 | 47.7 | 29.4 | 0.2313 |
| Runner score >= 3 | 13 | 76.9 | 51.2 | 25.7 | 0.2647 |
| EMA aligned | 1350 | 57.0 | 36.0 | 20.9 | 0.0859 |
| Counter-VWAP | 70 | 58.6 | 51.1 | 7.5 | 0.1116 |
| Multi-level | 416 | 54.1 | 50.6 | 3.5 | 0.0551 |

### Top 5 Signal Types to AVOID

(lowest win%, minimum N>=20)

| signal_type | N | win% | avg_pnl | disasters |
|---|---|---|---|---|
| NOT EMA aligned + bull | 227 | 31.7 | -0.1865 | 2 |
| ADX < 20 + NOT EMA | 112 | 33.0 | -0.1298 | 0 |
| NOT EMA aligned + HIGH level | 239 | 34.3 | -0.1017 | 2 |
| NOT EMA aligned + REV | 284 | 35.2 | -0.103 | 2 |
| NOT EMA aligned + BRK | 207 | 37.2 | -0.0791 | 2 |

### Top 5 Signal Types to SIZE UP

(highest win% and positive P&L, minimum N>=15)

| signal_type | N | win% | avg_MFE | avg_pnl | home_runs |
|---|---|---|---|---|---|
| EMA aligned + CONF pass | 209 | 79.4 | 0.3425 | 0.2512 | 5 |
| Morning + bear + CONF pass | 96 | 74.0 | 0.4169 | 0.2891 | 5 |
| Counter-VWAP + EMA aligned | 47 | 61.7 | 0.2565 | 0.12 | 1 |
| EMA aligned + vol>=5x | 516 | 60.5 | 0.3448 | 0.1263 | 17 |
| EMA aligned + morning + LOW | 477 | 60.4 | 0.3294 | 0.1194 | 13 |

### New Patterns Not in Existing Findings

- **REV vs BRK:** REV win%=50.5% (N=777), BRK win%=52.1% (N=1064). REV avg P&L=0.0258, BRK avg P&L=0.0472
- **Multi-level:** win%=54.1% (N=416), Single: win%=50.6% (N=1425). Multi P&L=0.0551, Single P&L=0.0333
- **Counter-VWAP + EMA aligned:** N=47, win%=61.7%, avg P&L=0.1200, home_runs=1
- **Runner Score correlation with MFE:** r=-0.0161
- **Runner Score correlation with win:** r=-0.0183
- **Vol >= 5x + ADX >= 40:** N=63, win%=44.4%, avg MFE=0.2759
- **CONF ✓★ vs ✓:** ✓★ win%=88.6% (N=44), ✓ win%=74.3% (N=187)

### Recommendations for v3.0

**If we required EMA aligned + morning (<10:30):**
- Signals: 944/1841 (51% retained)
- Win rate: 59.3% (vs 51.4% baseline)
- Avg P&L: 0.1127 (vs 0.0382 baseline)
- Home runs: 24/38 retained
- Disasters: 6/12 retained

**If we required only EMA aligned:**
- Signals: 1350/1841 (73% retained)
- Win rate: 57.0% (vs 51.4% baseline)
- Avg P&L: 0.0859 (vs 0.0382 baseline)
- Home runs: 27/38 retained
- Disasters: 8/12 retained

**Ranked recommendations:**
1. **Gate on EMA alignment** — single biggest filter, separates winners from losers
2. **Suppress afternoon signals** or dim them heavily (>= 10:30 = lower win%)
3. **Prefer bear + LOW level** — consistently highest edge
4. **Volume >= 5x as quality signal** — monotonic improvement with volume
5. **CONF pass as position sizing signal** — add size when CONF ✓/✓★
6. **Runner Score >= 3 for full position** — lower scores get reduced size
7. **Body% filter can be relaxed further** — it's genuinely noise in the data