# v29 MC 9:50 Gate Analysis

**Date:** 2026-03-04  
**Data:** v28a signals (1209 MC signals, 421 MC-confirmed trades, 126 opposing pairs)  
**Question:** Should MC signals be delayed until 9:50 ET to avoid early noise?

## 1. MC Signal Timing

| Metric | Count | % |
|--------|------:|--:|
| Total MC signals | 1209 | 100% |
| Before 9:50 | 1202 | 99.4% |
| After 9:50 | 7 | 1% |

**Time breakdown:**

| Time | Count | % |
|------|------:|--:|
| 11:05 | 2 | 0.2% |
| 13:30 | 1 | 0.1% |
| 13:35 | 1 | 0.1% |
| 14:15 | 1 | 0.1% |
| 14:35 | 1 | 0.1% |
| 14:40 | 1 | 0.1% |
| 9:30 | 30 | 2.5% |
| 9:35 | 521 | 43.1% |
| 9:40 | 391 | 32.3% |
| 9:45 | 260 | 21.5% |

**99.4% of MC signals fire before 9:50.** Only 7 fire later (11:05, 13:30-14:40).
On 339 symbol-days, BOTH bull and bear MC fire (opposing pair). On 531 days, only one direction fires.

## 2. Opposing Pair Accuracy

All 126 opposing pairs fire entirely before 9:50. The **second signal** is correct more often:

| Signal | Correct | Rate |
|--------|--------:|-----:|
| 1st signal | 57 | 45.2% |
| 2nd signal | 69 | 54.8% |
| Neither | 0 | 0.0% |
| Both | 0 | 0.0% |

**By timing:**

| 1st Time | N | 1st Correct | 2nd Correct |
|----------|--:|------------:|------------:|
| 9:30 | 6 | 83.3% | 16.7% |
| 9:35 | 90 | 45.6% | 54.4% |
| 9:40 | 30 | 36.7% | 63.3% |

Average 30-min move when 1st correct: 1.69 ATR  
Average 30-min move when neither correct: nan ATR (flat = both wrong)

## 3. MC-Confirmed Trade Performance

MC signals don't directly generate trades — they auto-confirm subsequent BRK/REV/VWAP signals. These are trades where `conf_source=QBS/MC`.

### By Signal Time (when the BRK signal fired)

| Window | Trades | Total PnL | Avg PnL | Avg MFE | Win% |
|--------|-------:|----------:|--------:|--------:|-----:|
| 9:30-9:39 | 20 | -0.66 | -0.0332 | 0.1921 | 40.0% |
| 9:40-9:49 | 127 | -2.78 | -0.0219 | 0.2175 | 33.9% |
| 9:50-9:59 | 69 | 3.35 | 0.0485 | 0.2859 | 43.5% |
| 10:00-10:29 | 86 | 5.21 | 0.0605 | 0.3016 | 33.7% |
| 10:30-10:59 | 22 | 1.20 | 0.0546 | 0.2923 | 50.0% |
| 11:00-11:59 | 21 | -1.03 | -0.0493 | 0.2109 | 14.3% |
| 12:00+ | 76 | -0.95 | -0.0125 | 0.2071 | 30.3% |

### Pre vs Post 9:50

| Group | N | Total PnL | Avg PnL | Avg MFE | Win% |
|-------|--:|----------:|--------:|--------:|-----:|
| Before 9:50 | 147 | -3.44 | -0.0234 | 0.2140 | 34.7% |
| After 9:50 | 274 | 7.78 | 0.0284 | 0.2637 | 35.0% |
| All MC | 421 | 4.34 | 0.0103 | 0.2464 | 34.9% |

**Key finding:** Post-9:50 MC-confirmed trades (274) have better avg PnL (0.0284 vs -0.0234 ATR).

### Confirmation Timing Matrix

| Scenario | N | PnL | Explanation |
|----------|--:|----:|-------------|
| Signal <9:50, CONF <9:50 | 137 | -4.09 | BRK fires early, MC already confirmed |
| Signal >=9:50, CONF <9:50 | 201 | 9.68 | BRK fires late, MC confirmed earlier |
| Signal >=9:50, CONF >=9:50 | 73 | -1.90 | Both fire late (rare) |

The 201 trades in the middle row are **at risk** with a 9:50 gate: their MC confirmation came from a pre-9:50 MC signal. With a gate, that MC wouldn't exist. Whether they'd be recovered depends on a replacement MC firing at 9:50+.

## 4. Oracle Scenario

If we could magically pick only the correct MC direction on pair days:

| Metric | Current | Oracle | Delta |
|--------|--------:|-------:|------:|
| Total MC PnL (ATR) | 4.34 | 6.71 | +2.38 |
| Wrong-dir trades removed | — | 21 | — |
| Wrong-dir PnL removed | — | -2.38 | — |

**Correct vs wrong direction trades on pair days:**

| Direction | N | Avg PnL | Avg MFE | Win% |
|-----------|--:|--------:|--------:|-----:|
| Correct dir | 36 | -0.0430 | 0.1773 | 30.6% |
| Wrong dir | 21 | -0.1132 | 0.1096 | 14.3% |

## 5. Slot Recovery

MC is once-per-direction-per-session. When both bull and bear MC fire before 9:50, both slots are burned — no MC can fire for the rest of the day.

| Metric | Count |
|--------|------:|
| Days with both slots burned before 9:50 | 334 |
| Days with one slot burned before 9:50 | 534 |
| MC signals currently after 9:50 | 7 |

Only 7 MC signals fire after 9:50 in current data. This is because slots are almost always burned early.

**QBS signals (volume drying pattern) for comparison:**
- Before 9:50: 20
- After 9:50: 67
- QBS fires throughout the day, proving volume patterns occur after 9:50.
- If MC slots weren't burned, we'd expect similar late-session MC signals.

**Late MC analysis (7 signals that did fire after 9:50):**

- GOOGL 2025-12-11 at 13:30 (bull): 0 early MC signals, dirs=[]
- GOOGL 2025-12-11 at 13:35 (bear): 0 early MC signals, dirs=[]
- SPY 2025-10-10 at 11:05 (bear): 1 early MC signals, dirs=['bull']
- QQQ 2025-10-10 at 11:05 (bear): 1 early MC signals, dirs=['bull']
- QQQ 2025-12-10 at 14:15 (bear): 1 early MC signals, dirs=['bull']
- TSLA 2026-01-21 at 14:35 (bull): 0 early MC signals, dirs=[]
- AAPL 2026-01-21 at 14:40 (bull): 1 early MC signals, dirs=['bear']

## 6. Per-Symbol Breakdown

| Symbol | MC# | Pairs | Trades | Total PnL | Avg PnL | Win% |
|--------|----:|------:|-------:|----------:|--------:|-----:|
| AAPL | 129 | 38 | 45 | -3.14 | -0.0697 | 26.7% |
| AMD | 129 | 37 | 40 | 1.07 | 0.0267 | 32.5% |
| AMZN | 127 | 0 | 42 | -1.92 | -0.0457 | 23.8% |
| GOOGL | 122 | 0 | 41 | 1.60 | 0.0389 | 41.5% |
| META | 116 | 0 | 36 | 1.54 | 0.0429 | 38.9% |
| MSFT | 117 | 0 | 44 | 0.41 | 0.0093 | 34.1% |
| NVDA | 128 | 0 | 49 | -0.02 | -0.0005 | 40.8% |
| QQQ | 106 | 26 | 41 | -0.80 | -0.0194 | 36.6% |
| SPY | 102 | 25 | 36 | -1.29 | -0.0359 | 33.3% |
| TSLA | 133 | 0 | 47 | 6.89 | 0.1466 | 40.4% |

## 7. Recommendations

### The case FOR a 9:50 gate:
- Wrong-direction trades on pair days cost -2.38 ATR total
- Removing them improves PnL by 2.38 ATR

### Trade-off analysis:
- Pre-9:50 signal trades: 147 trades, -3.44 ATR total PnL
- Post-9:50 signal trades: 274 trades, 7.78 ATR total PnL
- 201 trades confirmed by early MC but signaled after 9:50 (9.68 ATR) — these are the CORE value of early MC

### Risk of implementing the gate:
- 201 post-9:50 BRK trades currently get free MC confirmation
- With a gate, those trades would need a NEW MC to fire at 9:50+
- Currently only 7 MC signals fire after 9:50 (slots burned early)
- Unclear how many new MC signals would fire — volume patterns DO exist (QBS: 67 after 9:50)

### Bottom line:
Post-9:50 trades have better per-trade PnL (0.0284 vs -0.0234 ATR). A gate would lose the 201 'free confirmation' trades (9.68 ATR) unless replacement MC signals fire.

**Oracle analysis shows:** removing wrong-direction MC trades on pair days changes total PnL by +2.38 ATR. The opposing pairs cost -2.38 ATR.
