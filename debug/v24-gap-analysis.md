# v2.4 Gap Analysis

**Generated:** 2026-03-01 18:10
**Symbols:** AAPL, AMD, AMZN, GLD, GOOGL, META, MSFT, NVDA, QQQ, SLV, SPY, TSLA, TSM (13 total)
**Date range:** 2026-01-20 to 2026-02-27 (28 trading days)
**Total signals:** 1841
**5s candle coverage:** 13/13 symbols

### Signal Breakdown
- BRK: 1064
- ~ (reversal): 545
- ~~ (reclaim): 232

---

## Gap A: Jan 29 Cross-Validation

**Question:** Do our key findings hold without the monster day?

- Jan 29 signals: 81
- All other days: 1760
- Total: 1841

### Core Metrics

| Metric        | Full dataset | Excl. Jan 29 | Delta |
|---------------|--------------|--------------|-------|
| Total signals | 1841         | 1760         | 81    |
| BRK signals   | 1064         | 1021         | 43    |
| BRK CONF rate | 40.0%        | 39.6%        |       |
| ✓★ count      | 99           | 91           | 8     |

### CONF Rate by Time Bucket

| Time    | Full  | Excl. Jan 29 |
|---------|-------|--------------|
| 9:30-10 | 31.5% | 31.3%        |
| 10-11   | 53.6% | 52.0%        |
| 11-13   | 39.7% | 39.7%        |
| 13-16   | 47.3% | 47.7%        |

### CONF Rate by Volume Bucket

| Volume | Full  | Excl. Jan 29 |
|--------|-------|--------------|
| <1.5x  | —     | —            |
| 1.5-2x | 40.2% | 40.3%        |
| 2-5x   | 48.5% | 47.8%        |
| 5-10x  | 38.4% | 37.1%        |
| 10x+   | 18.8% | 19.5%        |

---

## Gap B: Day-of-Week Effects

**Question:** Do Monday/Friday differ from mid-week?

| Day | Signals | BRK | CONF rate | ✓★ count | Avg vol |
|-----|---------|-----|-----------|----------|---------|
| Mon | 250     | 156 | 56.1%     | 21       | 7.1x    |
| Tue | 406     | 237 | 38.7%     | 25       | 6.2x    |
| Wed | 419     | 231 | 35.3%     | 14       | 5.7x    |
| Thu | 395     | 224 | 41.3%     | 25       | 5.8x    |
| Fri | 371     | 216 | 34.4%     | 14       | 5.5x    |

---

## Gap C: Symbol × Time Interactions

**Question:** Do symbols have different optimal time windows?

CONF rate per cell (BRK only). **Bold** = >10pp above column average, *italic* = >10pp below.

| Symbol      | 9:30-10 (avg 31%) | 10-11 (avg 54%) | 11-13 (avg 40%) | 13-16 (avg 47%) |
|-------------|-------------------|-----------------|-----------------|-----------------|
| AAPL        | 29% (n=38)        | **64% (n=14)**  | **75% (n=4)**   | *30% (n=10)*    |
| AMD         | 27% (n=41)        | 54% (n=13)      | *25% (n=4)*     | 40% (n=5)       |
| AMZN        | 32% (n=31)        | **69% (n=16)**  | **50% (n=2)**   | *33% (n=6)*     |
| GLD         | 28% (n=25)        | *27% (n=22)*    | *29% (n=7)*     | 44% (n=9)       |
| GOOGL       | 32% (n=41)        | 60% (n=15)      | *25% (n=4)*     | **58% (n=12)**  |
| META        | 27% (n=44)        | 57% (n=23)      | 33% (n=6)       | **67% (n=9)**   |
| MSFT        | 37% (n=38)        | 44% (n=9)       | 43% (n=7)       | *36% (n=11)*    |
| NVDA        | 33% (n=33)        | 55% (n=20)      | *25% (n=4)*     | 46% (n=13)      |
| QQQ         | 33% (n=33)        | **64% (n=25)**  | **50% (n=4)**   | *33% (n=3)*     |
| SLV         | *17% (n=24)*      | 47% (n=17)      | **67% (n=6)**   | 50% (n=10)      |
| SPY         | 34% (n=35)        | 61% (n=28)      | *29% (n=7)*     | 50% (n=6)       |
| TSLA        | 35% (n=31)        | *41% (n=17)*    | **50% (n=8)**   | 50% (n=8)       |
| TSM         | 38% (n=50)        | 50% (n=16)      | *20% (n=5)*     | **60% (n=10)**  |
| **Average** | 31% (n=464)       | 54% (n=235)     | 40% (n=68)      | 47% (n=112)     |

---

## Gap D: Reclaim (~~ ) Deep Dive

**Question:** What predicts a good reclaim vs bad one?

Total reclaims: 232

### By Time Since Prior BRK

| Time since BRK | Count | GOOD | BAD | NEUTRAL | Unmatched | GOOD% | BAD% |
|----------------|-------|------|-----|---------|-----------|-------|------|
| <15m           | 45    | 2    | 3   | 39      | 1         | 4.5%  | 6.8% |
| 15-60m         | 86    | 3    | 1   | 72      | 10        | 3.9%  | 1.3% |
| 1-3h           | 33    | 1    | 0   | 30      | 2         | 3.2%  | 0.0% |
| 3h+            | 68    | 1    | 0   | 61      | 6         | 1.6%  | 0.0% |
| No prior BRK   | 0     | 0    | 0   | 0       | 0         | —     | —    |

### By Volume Ratio (Reclaim vol / BRK vol)

| Time since BRK | Count | GOOD | BAD | NEUTRAL | Unmatched | GOOD% | BAD% |
|----------------|-------|------|-----|---------|-----------|-------|------|
| <0.5x          | 105   | 4    | 2   | 89      | 10        | 4.2%  | 2.1% |
| 0.5-1x         | 73    | 2    | 2   | 64      | 5         | 2.9%  | 2.9% |
| 1-2x           | 47    | 1    | 0   | 42      | 4         | 2.3%  | 0.0% |
| 2x+            | 7     | 0    | 0   | 7       | 0         | 0.0%  | 0.0% |
| Unknown        | 0     | 0    | 0   | 0       | 0         | —     | —    |

### Reclaim MFE/MAE by Time Window (ATR-normalized)

| Window | Avg MFE/ATR | Avg MAE/ATR | Avg MFE/MAE | Coverage |
|--------|-------------|-------------|-------------|----------|
| 30s    | 0.025       | 0.026       | 2.00        | 213/232  |
| 1m     | 0.033       | 0.032       | 2.54        | 213/232  |
| 2m     | 0.047       | 0.043       | 3.89        | 213/232  |
| 5m     | 0.068       | 0.064       | 4.11        | 213/232  |
| 15m    | 0.108       | 0.113       | 4.57        | 213/232  |
| 30m    | 0.138       | 0.141       | 4.19        | 213/232  |

### By Level Type

| Level  | Count | GOOD | BAD | GOOD% | BAD% |
|--------|-------|------|-----|-------|------|
| ORB H  | 66    | 3    | 2   | 4.9%  | 3.3% |
| ORB L  | 52    | 0    | 1   | 0.0%  | 2.1% |
| PM H   | 47    | 2    | 1   | 4.5%  | 2.3% |
| PM L   | 54    | 1    | 0   | 2.1%  | 0.0% |
| Week H | 14    | 1    | 1   | 7.7%  | 7.7% |
| Week L | 7     | 0    | 0   | 0.0%  | 0.0% |
| Yest H | 20    | 0    | 0   | 0.0%  | 0.0% |
| Yest L | 21    | 0    | 0   | 0.0%  | 0.0% |

---

## Gap E: Multi-Level Breakout Quality

**Question:** Does level confluence boost follow-through (not just CONF)?

- Single-level signals: 1425
- Multi-level signals: 416

### CONF Rate (from pine logs)

| Group        | Total | BRK | CONF rate |
|--------------|-------|-----|-----------|
| Single-level | 1425  | 860 | 42.4%     |
| Multi-level  | 416   | 204 | 29.1%     |

### 5s Follow-Through Comparison

| Group        | Matched | GOOD | BAD | GOOD% | BAD% | MFE/ATR 5m | MFE/ATR 30m | MAE/ATR 15m |
|--------------|---------|------|-----|-------|------|------------|-------------|-------------|
| Single-level | 1347    | 106  | 35  | 7.9%  | 2.6% | 0.088      | 0.199       | 0.134       |
| Multi-level  | 401     | 34   | 12  | 8.5%  | 3.0% | 0.109      | 0.219       | 0.142       |

---

## Gap F: Counter-Trend Confidence Interval

**Question:** Is our counter-trend sample size sufficient?

### Wilson Score 95% Confidence Intervals

| Group         | N   | Passes | Point est. | 95% CI low | 95% CI high | CI width |
|---------------|-----|--------|------------|------------|-------------|----------|
| Counter-trend | 49  | 4      | 8.2%       | 3.2%       | 19.2%       | 16.0%    |
| With-trend    | 830 | 348    | 41.9%      | 38.6%      | 45.3%       | 6.7%     |

### Sample Size Requirements (for ±5pp precision at 95% confidence)

- Counter-trend: need **116** signals (have 49) → need 67 more
- With-trend: need **375** signals (have 830) → sufficient
