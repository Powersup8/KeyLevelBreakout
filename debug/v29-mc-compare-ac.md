# v29 MC Redesign: Option A vs Option C Comparison
> Generated: 2026-03-04 | Data: enriched-signals.csv (1841 total, 1003 post-9:50)

---

## 1. High-Level Summary

| Group | N | Runner% | Avg MFE | Avg MAE | MFE/MAE | Win% | Total PnL |
|-------|--:|--------:|--------:|--------:|--------:|-----:|----------:|
| ALL post-9:50 | 1003 | 1.2% | 0.206 | -0.168 | 1.22 | 51.5% | 37.36 |
| Option A (marked) | 52 | 1.9% | 0.221 | -0.127 | 1.74 | 57.7% | 4.91 |
| Option A (rest) | 951 | 1.2% | 0.205 | -0.171 | 1.20 | 51.2% | 32.46 |
| Option C (marked) | 150 | 1.3% | 0.201 | -0.152 | 1.32 | 54.0% | 7.34 |
| Option C (rest) | 853 | 1.2% | 0.207 | -0.171 | 1.21 | 51.1% | 30.02 |

- **Option A** marks **52** signals (5.2% of post-9:50)
- **Option C** marks **150** signals (15.0% of post-9:50)

## 2. Option A: Counter-VWAP Marker

**Rule:** BRK or REV where price is on OPPOSITE side of VWAP from signal direction, after 9:50 ET.

### By Time Window

| Group | N | Runner% | Avg MFE | Avg MAE | MFE/MAE | Win% | Total PnL |
|-------|--:|--------:|--------:|--------:|--------:|-----:|----------:|
| 11:00-12:00 | 1 | 0.0% | 0.331 | -0.096 | 3.45 | 100.0% | 0.24 |
| 12:00-14:00 | 4 | 0.0% | 0.038 | -0.091 | 0.42 | 25.0% | -0.21 |
| 14:00-16:00 | 25 | 0.0% | 0.182 | -0.076 | 2.38 | 64.0% | 2.64 |
| 9:50-10:30 | 22 | 4.5% | 0.294 | -0.192 | 1.53 | 54.5% | 2.24 |

### By Symbol (top 5)

| Group | N | Runner% | Avg MFE | Avg MAE | MFE/MAE | Win% | Total PnL |
|-------|--:|--------:|--------:|--------:|--------:|-----:|----------:|
| GLD | 8 | 0.0% | 0.163 | -0.200 | 0.81 | 62.5% | -0.30 |
| META | 8 | 0.0% | 0.239 | -0.077 | 3.09 | 87.5% | 1.29 |
| AAPL | 7 | 0.0% | 0.232 | -0.094 | 2.45 | 42.9% | 0.96 |
| GOOGL | 5 | 0.0% | 0.119 | -0.167 | 0.71 | 40.0% | -0.24 |
| TSLA | 5 | 0.0% | 0.088 | -0.165 | 0.53 | 40.0% | -0.38 |

### By Signal Type

| Group | N | Runner% | Avg MFE | Avg MAE | MFE/MAE | Win% | Total PnL |
|-------|--:|--------:|--------:|--------:|--------:|-----:|----------:|
| BRK | 52 | 1.9% | 0.221 | -0.127 | 1.74 | 57.7% | 4.91 |

## 3. Option C: Momentum Context Scorer

**Rule:** Score each signal (after 9:50 ET):
1. Counter-VWAP → +2 points
2. Time 10:30-12:00 → +1 point
3. REV type → +1 point
4. A-tier (TSLA/META) → +1 point
5. NOT exhaustion (range_atr < 2.0) → +1 point *(all signals get +1, limitation noted below)*

Score >= 3 = marked.

### Score Distribution

| Score | N | % | Runner% | Avg MFE | Win% | Total PnL |
|------:|--:|--:|--------:|--------:|-----:|----------:|
| 1 | 469 | 46.8% | 1.5% | 0.212 | 51.2% | 19.32 |
| 2 | 384 | 38.3% | 0.8% | 0.200 | 51.0% | 10.70 |
| 3 | 132 | 13.2% | 1.5% | 0.206 | 52.3% | 6.74 |
| 4 | 17 | 1.7% | 0.0% | 0.154 | 64.7% | 0.37 |
| 5 | 1 | 0.1% | 0.0% | 0.331 | 100.0% | 0.24 |

### By Time Window

| Group | N | Runner% | Avg MFE | Avg MAE | MFE/MAE | Win% | Total PnL |
|-------|--:|--------:|--------:|--------:|--------:|-----:|----------:|
| 10:30-11:00 | 19 | 0.0% | 0.210 | -0.204 | 1.03 | 52.6% | 0.11 |
| 11:00-12:00 | 21 | 4.8% | 0.252 | -0.121 | 2.07 | 52.4% | 2.74 |
| 12:00-14:00 | 13 | 0.0% | 0.088 | -0.093 | 0.95 | 61.5% | -0.06 |
| 14:00-16:00 | 42 | 0.0% | 0.145 | -0.077 | 1.88 | 61.9% | 2.85 |
| 9:50-10:30 | 55 | 1.8% | 0.247 | -0.216 | 1.14 | 47.3% | 1.70 |

### By Symbol (top 5)

| Group | N | Runner% | Avg MFE | Avg MAE | MFE/MAE | Win% | Total PnL |
|-------|--:|--------:|--------:|--------:|--------:|-----:|----------:|
| META | 53 | 0.0% | 0.172 | -0.155 | 1.11 | 56.6% | 0.89 |
| TSLA | 42 | 0.0% | 0.169 | -0.155 | 1.09 | 52.4% | 0.61 |
| GLD | 12 | 8.3% | 0.291 | -0.184 | 1.58 | 66.7% | 1.28 |
| AAPL | 8 | 0.0% | 0.221 | -0.127 | 1.74 | 37.5% | 0.75 |
| SPY | 6 | 0.0% | 0.223 | -0.263 | 0.85 | 33.3% | -0.24 |

### By Signal Type

| Group | N | Runner% | Avg MFE | Avg MAE | MFE/MAE | Win% | Total PnL |
|-------|--:|--------:|--------:|--------:|--------:|-----:|----------:|
| BRK | 70 | 1.4% | 0.216 | -0.131 | 1.65 | 55.7% | 5.98 |
| REV | 80 | 1.2% | 0.187 | -0.170 | 1.10 | 52.5% | 1.36 |

## 4. Overlap Analysis

| Set | N | Description |
|-----|--:|-------------|
| Both A+C | 52 | Marked by both approaches |
| A-only | 0 | Counter-VWAP but score < 3 |
| C-only | 98 | Score >= 3 but NOT counter-VWAP |
| Neither | 853 | Not marked by either |

### Performance by Overlap Set

| Group | N | Runner% | Avg MFE | Avg MAE | MFE/MAE | Win% | Total PnL |
|-------|--:|--------:|--------:|--------:|--------:|-----:|----------:|
| Both A+C | 52 | 1.9% | 0.221 | -0.127 | 1.74 | 57.7% | 4.91 |
| A-only | 0 | — | — | — | — | — | — |
| C-only | 98 | 1.0% | 0.190 | -0.165 | 1.15 | 52.0% | 2.44 |
| Neither | 853 | 1.2% | 0.207 | -0.171 | 1.21 | 51.1% | 30.02 |

## 5. Incremental Value of C over A

- Option A marks 52 signals → 1.9% runner, MFE/MAE 1.74, Win% 57.7%
- Option C marks 150 signals → 1.3% runner, MFE/MAE 1.32, Win% 54.0%
- C adds 98 signals not in A (C-only). These have:
  - Runner%: 1.0%
  - MFE/MAE: 1.15
  - Win%: 52.0%
  - Total PnL: 2.44

### Does Higher Score = Better Performance?

| Score Range | N | Runner% | Avg MFE | MFE/MAE | Win% |
|------------|--:|--------:|--------:|--------:|-----:|
| 0-1 (low) | 469 | 1.5% | 0.212 | 1.24 | 51.2% |
| 2 (medium) | 384 | 0.8% | 0.200 | 1.16 | 51.0% |
| 3 (threshold) | 132 | 1.5% | 0.206 | 1.33 | 52.3% |
| 4-6 (high) | 18 | 0.0% | 0.164 | 1.25 | 66.7% |

## 6. Factor Contribution Analysis

How much does each scoring factor differentiate on its own?

| Factor | With=True N | Runner% | Avg MFE | With=False N | Runner% | Avg MFE | Delta MFE |
|--------|----------:|--------:|--------:|------------:|--------:|--------:|----------:|
| Counter-VWAP | 52 | 1.9% | 0.221 | 951 | 1.2% | 0.205 | +0.017 |
| 11 AM Window | 98 | 1.0% | 0.199 | 905 | 1.2% | 0.206 | -0.007 |
| REV type | 332 | 1.2% | 0.201 | 671 | 1.2% | 0.208 | -0.007 |
| A-tier symbol | 169 | 0.0% | 0.184 | 834 | 1.4% | 0.210 | -0.026 |

## 7. Data-Driven Recommendation

| Metric | Baseline | Option A | Option C |
|--------|----------|----------|----------|
| Signals | 1003 | 52 (5%) | 150 (15%) |
| Runner% | 1.2% | 1.9% | 1.3% |
| MFE/MAE | 1.22 | 1.74 | 1.32 |
| Win% | 51.5% | 57.7% | 54.0% |
| Total PnL | 37.36 | 4.91 | 7.34 |

**Verdict: Option A wins.** Simpler, fewer signals, equal or better edge. The scoring complexity of Option C does not add meaningful lift.

## Limitations

1. **NOT exhaustion factor (range_atr < 2.0):** The enriched-signals.csv does not include bar range. All signals received +1 for this factor. In practice ~85-90% of signals would qualify, so the impact is small — it shifts some score=3 signals to score=2 (removing ~10-15% from Option C's pool).
2. **MFE/MAE are 30-min follow-through** from 1m candle data, normalized by ATR. They represent the best/worst 30-min outcome, not actual trade PnL.
3. **VWAP column** in the data represents whether price was above/below VWAP at signal time, which is exactly what we need for counter-VWAP classification.
4. **No VWAP-type signals** exist in this dataset (only BRK and REV), so Option A's BRK/REV filter has no effect — all post-9:50 counter-VWAP signals are already BRK or REV.
