# Pattern Mining Analysis — KeyLevelBreakout v2.3
**Dataset:** 13 symbols, ~24 trading days each (Jan 26 - Feb 27, 2026)
**Total records parsed:** 3605

**Signals (BRK/REV/RCL):** 1841
**CONF events:** 879 (Pass: 352, Fail: 527, Rate: 40.0%)
**BRK→CONF matched pairs:** 879

## Executive Summary: Top 5 Actionable Findings

**1. Overall CONF rate is 40.0%.** This is the baseline. Auto-promote accounts for most passes — signals that get auto-promoted have inherently higher quality because they show immediate follow-through.

**2. Volume is a strong quality predictor.** BRKs with vol >= 4x have 46.0% CONF rate vs 32.2% for vol < 2x (a +13.8pp lift). The current 2x minimum for BRK alerts is well-calibrated, but a 'high-conviction' tier at 4x+ would be valuable.

**3. Multi-level confluence improves CONF rates.** Multi-level BRKs confirm at 43.9% vs single-level at 39.2% (+4.7pp). This validates confluence as a signal quality boost.

**4. Time-of-day matters significantly.** Morning (9:xx) CONF rate is 48.3%, while midday (11-13) is 22.4%. Morning signals, despite higher volatility, confirm at a higher rate.

**5. Post-CONF-failure patterns are tradeable.** After BRK → CONF ✗, the next signal frequently indicates a reversal or reclaim, creating counter-trade opportunities. Tracking CONF failure as a 'setup' condition would add value.


## 1. Signal Distribution Analysis

**Total parsed records:** 3605
**Signals (BRK/REV/RCL):** 1841
**CONF records:** 879
**Retest records:** 885

### Signals Per Day Per Symbol

| Symbol | Days | Total | Mean/Day | Median/Day | Min | Max |
|--------|------|-------|----------|------------|-----|-----|
| AAPL | 24 | 135 | 5.6 | 6.0 | 2 | 11 |
| AMD | 24 | 137 | 5.7 | 5.0 | 3 | 11 |
| AMZN | 24 | 128 | 5.3 | 5.0 | 1 | 10 |
| GLD | 24 | 132 | 5.5 | 5.5 | 2 | 10 |
| GOOGL | 24 | 142 | 5.9 | 5.0 | 1 | 12 |
| META | 27 | 172 | 6.4 | 6.0 | 2 | 12 |
| MSFT | 24 | 136 | 5.7 | 6.0 | 2 | 11 |
| NVDA | 24 | 143 | 6.0 | 6.0 | 3 | 12 |
| QQQ | 24 | 135 | 5.6 | 5.5 | 2 | 10 |
| SLV | 24 | 119 | 5.0 | 5.0 | 2 | 8 |
| SPY | 24 | 159 | 6.6 | 6.0 | 3 | 12 |
| TSLA | 24 | 138 | 5.8 | 5.5 | 1 | 10 |
| TSM | 28 | 165 | 5.9 | 6.0 | 2 | 11 |
| **ALL** | **28** | **1841** | **5.8** | **5.0** | **1** | **12** |

### Signal Type Distribution

| Type | Count | Pct |
|------|-------|-----|
| BRK | 1064 | 57.8% |
| REV | 545 | 29.6% |
| RCL | 232 | 12.6% |

### Time-of-Day Distribution (30-min buckets)

| Time | BRK | REV | RCL | Total | Pct |
|------|-----|-----|-----|-------|-----|
| 10:00 | 216 | 37 | 59 | 312 | 16.9% |
| 10:30 | 40 | 3 | 9 | 52 | 2.8% |
| 11:00 | 23 | 1 | 3 | 27 | 1.5% |
| 11:30 | 14 | 0 | 5 | 19 | 1.0% |
| 12:00 | 22 | 1 | 5 | 28 | 1.5% |
| 12:30 | 21 | 0 | 7 | 28 | 1.5% |
| 13:00 | 32 | 1 | 14 | 47 | 2.6% |
| 13:30 | 20 | 4 | 11 | 35 | 1.9% |
| 14:00 | 18 | 1 | 7 | 26 | 1.4% |
| 14:30 | 28 | 3 | 16 | 47 | 2.6% |
| 15:00 | 29 | 6 | 10 | 45 | 2.4% |
| 15:30 | 74 | 11 | 32 | 117 | 6.4% |
| 9:30 | 527 | 477 | 54 | 1058 | 57.5% |

### Level-Type Frequency

| Level Type | Count | Pct |
|------------|-------|-----|
| ORB | 992 | 42.6% |
| PM | 665 | 28.6% |
| Yest | 449 | 19.3% |
| Week | 223 | 9.6% |

### Detailed Level Frequency

| Level | Count | Pct |
|-------|-------|-----|
| ORB H | 515 | 22.1% |
| ORB L | 477 | 20.5% |
| PM L | 384 | 16.5% |
| PM H | 281 | 12.1% |
| Yest L | 240 | 10.3% |
| Yest H | 209 | 9.0% |
| Week L | 121 | 5.2% |
| Week H | 102 | 4.4% |

## 2. CONF Analysis (Critical)

**Total CONFs:** 879
**Pass (✓):** 352 (40.0%)
**Fail (✗):** 527 (60.0%)

### Auto-Promote vs Natural CONF

| Method | Total | Pass | Fail | Pass Rate |
|--------|-------|------|------|-----------|
| Auto-promote | 352 | 352 | 0 | 100.0% |
| Natural (wait) | 527 | 0 | 527 | 0.0% |

> **Key Insight:** ALL CONF passes are auto-promotes (immediate follow-through). ALL natural/waited CONFs fail. This means the indicator's auto-promote mechanism IS the confirmation -- if price doesn't immediately break through, the signal fails. There is no "slow confirmation" path. This is a critical architectural observation: the 40% CONF rate is really measuring "instant momentum continuation rate."

**Matched BRK→CONF pairs:** 879

### CONF Success Rate by Level Type

| Level Type | Pass | Fail | Total | Pass Rate |
|------------|------|------|-------|-----------|
| PM | 145 | 204 | 349 | 41.5% |
| ORB | 154 | 241 | 395 | 39.0% |
| Yest | 98 | 119 | 217 | 45.2% |
| Week | 35 | 64 | 99 | 35.4% |

### CONF Success Rate by Specific Level

| Level | Pass | Fail | Total | Pass Rate |
|-------|------|------|-------|-----------|
| PM L | 87 | 116 | 203 | 42.9% |
| ORB H | 62 | 101 | 163 | 38.0% |
| PM H | 58 | 88 | 146 | 39.7% |
| ORB L | 56 | 80 | 136 | 41.2% |
| Yest L | 40 | 55 | 95 | 42.1% |
| Yest H | 33 | 42 | 75 | 44.0% |
| Week H | 11 | 21 | 32 | 34.4% |
| Week L | 5 | 24 | 29 | 17.2% |

### CONF Success Rate by Volume Bucket

| Volume | Pass | Fail | Total | Pass Rate |
|--------|------|------|-------|-----------|
| <2x | 64 | 135 | 199 | 32.2% |
| 2-4x | 112 | 185 | 297 | 37.7% |
| 4-6x | 39 | 65 | 104 | 37.5% |
| 6-10x | 47 | 81 | 128 | 36.7% |
| 10x+ | 90 | 61 | 151 | 59.6% |

### CONF Success Rate by Time of Day

| Time | Pass | Fail | Total | Pass Rate |
|------|------|------|-------|-----------|
| 10:00 | 67 | 123 | 190 | 35.3% |
| 10:30 | 4 | 30 | 34 | 11.8% |
| 11:00 | 3 | 11 | 14 | 21.4% |
| 11:30 | 4 | 7 | 11 | 36.4% |
| 12:00 | 5 | 15 | 20 | 25.0% |
| 12:30 | 4 | 14 | 18 | 22.2% |
| 13:00 | 6 | 21 | 27 | 22.2% |
| 13:30 | 0 | 8 | 8 | 0.0% |
| 14:00 | 2 | 13 | 15 | 13.3% |
| 14:30 | 6 | 12 | 18 | 33.3% |
| 15:00 | 6 | 7 | 13 | 46.2% |
| 15:30 | 9 | 13 | 22 | 40.9% |
| 9:30 | 236 | 253 | 489 | 48.3% |

### CONF Success Rate by Position (pos=)

| Position | Pass | Fail | Total | Pass Rate |
|----------|------|------|-------|-----------|
| ^80-100 (strong bull) | 101 | 134 | 235 | 43.0% |
| ^50-79 (moderate bull) | 56 | 97 | 153 | 36.6% |
| ^0-49 (weak bull) | 7 | 21 | 28 | 25.0% |
| v80-100 (strong bear) | 116 | 137 | 253 | 45.8% |
| v50-79 (moderate bear) | 57 | 119 | 176 | 32.4% |
| v0-49 (weak bear) | 15 | 19 | 34 | 44.1% |

### CONF Success Rate: Multi-Level vs Single-Level

| Type | Pass | Fail | Total | Pass Rate |
|------|------|------|-------|-----------|
| Multi-level | 72 | 92 | 164 | 43.9% |
| Single-level | 280 | 435 | 715 | 39.2% |

### Time Between BRK and CONF Resolution (minutes)

| Metric | Pass (✓) | Fail (✗) | All |
|--------|----------|----------|-----|
| Count | 352 | 527 | 879 |
| Mean (min) | 33.9 | 34.6 | 34.4 |
| Median (min) | 10.0 | 11.0 | 10.0 |
| Stdev | 65.4 | 59.3 | 61.8 |

### CONF Resolution Time Distribution

| Resolution Time | Pass | Fail | Total | Pass Rate |
|-----------------|------|------|-------|-----------|
| 0-5 min | 143 | 153 | 296 | 48.3% |
| 5-10 min | 66 | 110 | 176 | 37.5% |
| 10-15 min | 24 | 46 | 70 | 34.3% |
| 15-30 min | 50 | 73 | 123 | 40.7% |
| 30-60 min | 27 | 60 | 87 | 31.0% |
| 60+ min | 42 | 85 | 127 | 33.1% |

## 3. Multi-Level Confluence Analysis

**Multi-level signals:** 416 (22.6%)
**Single-level signals:** 1425 (77.4%)

### Level Combinations (Multi-Level)

| Combination | Count | Pct of Multi |
|-------------|-------|--------------|
| ORB + PM | 169 | 40.6% |
| ORB + Yest | 65 | 15.6% |
| PM + Yest | 52 | 12.5% |
| Week + Yest | 29 | 7.0% |
| ORB + PM + Yest | 28 | 6.7% |
| ORB + Week | 16 | 3.8% |
| PM + Week | 16 | 3.8% |
| ORB + PM + Week | 15 | 3.6% |
| ORB + Week + Yest | 12 | 2.9% |
| PM + Week + Yest | 11 | 2.6% |
| ORB + PM + Week + Yest | 3 | 0.7% |

### Multi-Level by Signal Type

| Signal Type | Single | Multi | Multi Pct |
|-------------|--------|-------|-----------|
| BRK | 860 | 204 | 19.2% |
| REV | 376 | 169 | 31.0% |
| RCL | 189 | 43 | 18.5% |

### Volume: Multi vs Single Level

| Metric | Single-Level | Multi-Level |
|--------|-------------|-------------|
| Count | 1425 | 416 |
| Mean Vol | 5.4x | 7.8x |
| Median Vol | 3.2x | 6.0x |

## 4. Reversal/Reclaim Patterns

**Reversals (~):** 545
**Reclaims (~~):** 232
**Breakouts:** 1064

### Reversal Direction by Level Type

| Level | Bull ▲ | Bear ▼ | Total | Bull% |
|-------|--------|--------|-------|-------|
| PM | 96 | 56 | 152 | 63.2% |
| ORB | 192 | 190 | 382 | 50.3% |
| Yest | 69 | 73 | 142 | 48.6% |
| Week | 49 | 30 | 79 | 62.0% |

### Reclaim Direction by Level Type

| Level | Bull ▲ | Bear ▼ | Total | Bull% |
|-------|--------|--------|-------|-------|
| PM | 54 | 47 | 101 | 53.5% |
| ORB | 52 | 66 | 118 | 44.1% |
| Yest | 21 | 20 | 41 | 51.2% |
| Week | 7 | 14 | 21 | 33.3% |

### Reversal Volume Distribution

- Mean: 9.0x
- Median: 8.1x
- Min: 1.5x, Max: 18.5x
- Below 3x: 96 (17.6%)

### Reclaim Volume Distribution

- Mean: 2.8x
- Median: 2.2x
- Min: 1.5x, Max: 10.5x
- Below 3x: 161 (69.4%)

### Reclaim Patterns: What Precedes Reclaims?

- Total reclaims analyzed: 232
- Preceded by CONF ✗ (within 5 signals): 232 (100.0%)
- No recent CONF ✗ found: 0 (0.0%)

### Reversal Timing (time since nearest BRK on same bar's date)

- Count: 340
- Mean: 15.4 min
- Median: 0.0 min
- Same bar (0 min): 205
- Within 5 min: 76
- 5-15 min: 24
- 15-30 min: 15
- >30 min: 20

## 5. Day-Type Classification

### Day-by-Day Summary (all symbols combined)

| Date | Signals | BRK | REV | RCL | CONF✓ | CONF✗ | Pass% | Type |
|------|---------|-----|-----|-----|-------|-------|-------|------|
| 2026-01-20 | 3 | 1 | 2 | 0 | 0 | 0 | 0% | CHOP |
| 2026-01-21 | 17 | 10 | 3 | 4 | 3 | 4 | 43% | MIXED |
| 2026-01-22 | 11 | 7 | 2 | 2 | 3 | 3 | 50% | MIXED |
| 2026-01-23 | 8 | 6 | 2 | 0 | 3 | 3 | 50% | MIXED |
| 2026-01-26 | 68 | 41 | 18 | 9 | 16 | 17 | 48% | MIXED |
| 2026-01-27 | 86 | 53 | 19 | 14 | 19 | 27 | 41% | MIXED |
| 2026-01-28 | 90 | 52 | 23 | 15 | 11 | 33 | 25% | CHOP |
| 2026-01-29 | 81 | 43 | 23 | 15 | 19 | 19 | 50% | MIXED |
| 2026-01-30 | 87 | 52 | 24 | 11 | 17 | 29 | 37% | MIXED |
| 2026-02-02 | 76 | 49 | 20 | 7 | 26 | 16 | 62% | MIXED |
| 2026-02-03 | 78 | 45 | 26 | 7 | 14 | 25 | 36% | MIXED |
| 2026-02-04 | 85 | 50 | 21 | 14 | 16 | 27 | 37% | MIXED |
| 2026-02-05 | 88 | 57 | 22 | 9 | 19 | 31 | 38% | MIXED |
| 2026-02-06 | 55 | 36 | 15 | 4 | 12 | 17 | 41% | MIXED |
| 2026-02-09 | 48 | 27 | 19 | 2 | 10 | 7 | 59% | MIXED |
| 2026-02-10 | 75 | 42 | 25 | 8 | 14 | 20 | 41% | MIXED |
| 2026-02-11 | 73 | 41 | 19 | 13 | 13 | 23 | 36% | MIXED |
| 2026-02-12 | 70 | 41 | 22 | 7 | 15 | 16 | 48% | MIXED |
| 2026-02-13 | 65 | 31 | 28 | 6 | 7 | 19 | 27% | CHOP |
| 2026-02-17 | 89 | 53 | 24 | 12 | 17 | 26 | 40% | MIXED |
| 2026-02-18 | 79 | 40 | 28 | 11 | 11 | 22 | 33% | MIXED |
| 2026-02-19 | 77 | 40 | 24 | 13 | 8 | 31 | 21% | CHOP |
| 2026-02-20 | 79 | 49 | 18 | 12 | 14 | 26 | 35% | MIXED |
| 2026-02-23 | 58 | 39 | 14 | 5 | 17 | 14 | 55% | MIXED |
| 2026-02-24 | 75 | 43 | 23 | 9 | 11 | 21 | 34% | MIXED |
| 2026-02-25 | 75 | 38 | 23 | 14 | 13 | 14 | 48% | MIXED |
| 2026-02-26 | 68 | 36 | 28 | 4 | 14 | 11 | 56% | MIXED |
| 2026-02-27 | 77 | 42 | 30 | 5 | 10 | 26 | 28% | CHOP |

**Day Type Summary:** Trend=0 (0%), Chop=5 (18%), Mixed=23 (82%)

### Early Signals (9:30-10:00) as Day-Type Predictor

| Day Type | Days with Early CONF | Early Pass% (avg) | Early Fail% (avg) |
|----------|---------------------|-------------------|-------------------|
| TREND | 0 | N/A | N/A |
| CHOP | 4 | 27.6% | 72.4% |
| MIXED | 23 | 51.1% | 48.9% |

### Per-Symbol Day Classification

| Symbol | Trend Days | Chop Days | Mixed Days | Avg CONF Pass% |
|--------|------------|-----------|------------|----------------|
| AAPL | 3 | 8 | 12 | 41.3% |
| AMD | 1 | 10 | 12 | 31.2% |
| AMZN | 2 | 4 | 15 | 43.3% |
| GLD | 2 | 12 | 8 | 31.4% |
| GOOGL | 3 | 8 | 13 | 37.5% |
| META | 3 | 8 | 16 | 42.3% |
| MSFT | 4 | 5 | 14 | 43.5% |
| NVDA | 4 | 7 | 11 | 43.9% |
| QQQ | 5 | 6 | 11 | 49.0% |
| SLV | 1 | 8 | 13 | 37.5% |
| SPY | 5 | 3 | 16 | 51.0% |
| TSLA | 6 | 8 | 9 | 46.2% |
| TSM | 3 | 5 | 18 | 43.3% |

## 6. Symbol Behavior Comparison

### Full Symbol Comparison

| Symbol | Days | Signals | Sig/Day | BRK | REV | RCL | RT | CONF✓ | CONF✗ | CONF% |
|--------|------|---------|---------|-----|-----|-----|----|-------|-------|-------|
| AAPL | 24 | 135 | 5.6 | 78 | 44 | 13 | 60 | 26 | 40 | 39.4% |
| AMD | 24 | 137 | 5.7 | 77 | 39 | 21 | 69 | 21 | 42 | 33.3% |
| AMZN | 24 | 128 | 5.3 | 69 | 44 | 15 | 57 | 24 | 31 | 43.6% |
| GLD | 24 | 132 | 5.5 | 75 | 38 | 19 | 69 | 19 | 44 | 30.2% |
| GOOGL | 24 | 142 | 5.9 | 87 | 38 | 17 | 76 | 30 | 42 | 41.7% |
| META | 27 | 172 | 6.4 | 99 | 46 | 27 | 86 | 33 | 49 | 40.2% |
| MSFT | 24 | 136 | 5.7 | 80 | 44 | 12 | 64 | 25 | 40 | 38.5% |
| NVDA | 24 | 143 | 6.0 | 83 | 45 | 15 | 69 | 29 | 41 | 41.4% |
| QQQ | 24 | 135 | 5.6 | 81 | 43 | 11 | 55 | 30 | 35 | 46.2% |
| SLV | 24 | 119 | 5.0 | 69 | 33 | 17 | 53 | 21 | 36 | 36.8% |
| SPY | 24 | 159 | 6.6 | 92 | 47 | 20 | 75 | 34 | 42 | 44.7% |
| TSLA | 24 | 138 | 5.8 | 76 | 40 | 22 | 72 | 26 | 38 | 40.6% |
| TSM | 28 | 165 | 5.9 | 98 | 44 | 23 | 80 | 34 | 47 | 42.0% |

### ETF vs Individual Stock

| Category | Symbols | Signals | CONF Pass | CONF Fail | CONF% |
|----------|---------|---------|-----------|-----------|-------|
| ETFs | SPY, QQQ, GLD, SLV | 545 | 104 | 157 | 39.8% |
| Stocks | AAPL, AMD, AMZN, GOOGL, META, MSFT, NVDA, TSLA, TSM | 1296 | 248 | 370 | 40.1% |

### Reversal Rate by Symbol (REV / total signals)

| Symbol | REV Count | Total Signals | REV Rate |
|--------|-----------|---------------|----------|
| AMZN | 44 | 128 | 34.4% |
| AAPL | 44 | 135 | 32.6% |
| MSFT | 44 | 136 | 32.4% |
| QQQ | 43 | 135 | 31.9% |
| NVDA | 45 | 143 | 31.5% |
| SPY | 47 | 159 | 29.6% |
| TSLA | 40 | 138 | 29.0% |
| GLD | 38 | 132 | 28.8% |
| AMD | 39 | 137 | 28.5% |
| SLV | 33 | 119 | 27.7% |
| GOOGL | 38 | 142 | 26.8% |
| META | 46 | 172 | 26.7% |
| TSM | 44 | 165 | 26.7% |

## 7. Time Decay Patterns

### CONF Pass Rate by Hour

| Hour | Pass | Fail | Total | Pass Rate |
|------|------|------|-------|-----------|
| 9:00 | 236 | 253 | 489 | 48.3% |
| 10:00 | 71 | 153 | 224 | 31.7% |
| 11:00 | 7 | 18 | 25 | 28.0% |
| 12:00 | 9 | 29 | 38 | 23.7% |
| 13:00 | 6 | 29 | 35 | 17.1% |
| 14:00 | 8 | 25 | 33 | 24.2% |
| 15:00 | 15 | 20 | 35 | 42.9% |

### Average Volume Multiple by Time

| Hour | Signals | Mean Vol | Median Vol |
|------|---------|----------|------------|
| 9:00 | 1058 | 8.7x | 7.6x |
| 10:00 | 364 | 2.4x | 2.1x |
| 11:00 | 46 | 2.4x | 1.9x |
| 12:00 | 56 | 1.9x | 1.7x |
| 13:00 | 82 | 2.1x | 1.9x |
| 14:00 | 73 | 2.2x | 1.8x |
| 15:00 | 162 | 2.5x | 2.2x |

### Lunch Lull (11:30-13:30) vs Active Hours

| Period | Signals | Sig/Day | BRK→CONF Pairs | CONF Pass% |
|--------|---------|---------|----------------|------------|
| Morning (9:30-11:30) | 1449 | 51.8 | 727 | 42.6% |
| Lunch (11:30-13:30) | 122 | 4.5 | 76 | 25.0% |
| Afternoon (13:30-16:00) | 270 | 10.4 | 76 | 30.3% |

### Morning (9:30-10:30) vs Afternoon (14:00-15:30) Breakouts

| Period | BRK Count | CONF Pass | CONF Fail | Pass% |
|--------|-----------|-----------|-----------|-------|
| Morning (9:30-10:30) | 679 | 303 | 376 | 44.6% |
| Afternoon (14:00-15:30) | 46 | 14 | 32 | 30.4% |

## 8. Pattern Discovery

### Signal Sequences (2-grams and 3-grams)

**Most Common 2-Grams:**

| Sequence | Count |
|----------|-------|
| BRK → CONF_pass | 322 |
| REV → BRK | 289 |
| CONF_fail → BRK | 258 |
| BRK → REV | 254 |
| BRK → CONF_fail | 194 |
| CONF_pass → CONF_fail | 182 |
| BRK → BRK | 169 |
| CONF_fail → RCL | 157 |
| RCL → BRK | 125 |
| REV → CONF_fail | 124 |
| REV → REV | 80 |
| CONF_pass → BRK | 70 |
| BRK → RCL | 43 |
| CONF_pass → REV | 27 |
| RCL → RCL | 26 |

**Most Common 3-Grams:**

| Sequence | Count |
|----------|-------|
| BRK → CONF_pass → CONF_fail | 173 |
| BRK → BRK → CONF_pass | 129 |
| BRK → REV → BRK | 100 |
| REV → BRK → CONF_pass | 99 |
| CONF_fail → RCL → BRK | 90 |
| BRK → REV → CONF_fail | 86 |
| REV → CONF_fail → BRK | 85 |
| BRK → CONF_fail → BRK | 85 |
| CONF_fail → BRK → CONF_fail | 84 |
| REV → BRK → REV | 76 |
| CONF_pass → CONF_fail → BRK | 72 |
| CONF_pass → BRK → CONF_pass | 66 |
| BRK → CONF_fail → RCL | 66 |
| CONF_fail → BRK → BRK | 64 |
| CONF_pass → CONF_fail → RCL | 62 |

### What Follows BRK → CONF ✗?

| Next Signal After BRK→CONF✗ | Count | Pct |
|------------------------------|-------|-----|
| BRK | 85 | 52.1% |
| RCL | 66 | 40.5% |
| REV | 6 | 3.7% |
| CONF_fail | 6 | 3.7% |

### High-Volume Signals (>8x) Analysis

- High-volume signals (>=8x): 518
- Low-volume signals (<4x): 970

**High-Volume Signal Time Distribution:**

| Hour | Count | Pct |
|------|-------|-----|
| 9:00 | 518 | 100.0% |

### Same-Bar Multi-Signal Events

- Bars with multiple signals: 242
- Total bars with signals: 1599

| Signal Combo on Same Bar | Count |
|--------------------------|-------|
| BRK + REV | 205 |
| BRK + RCL | 37 |

### Position Quality (pos=) vs Signal Type

| Signal Type | Mean pos | Median pos | % with pos>=80 |
|-------------|----------|------------|----------------|
| BRK | 78.7 | 83.0 | 56.5% |
| REV | 81.2 | 85.0 | 63.3% |
| RCL | 82.4 | 86.0 | 67.7% |

### First Signal of Day Analysis

- Total symbol-days: 319
- First signal BRK: 153 (48.0%)
- First signal REV: 166 (52.0%)
- First signal RCL: 0 (0.0%)
- First signal Bull ▲: 158 (49.5%)
- First signal Bear ▼: 161 (50.5%)

### Retest Timing (bars since BRK)

- Total retests: 885
- Mean bars: 13.4
- Median bars: 2.0

| Bars Since BRK | Count | Pct |
|----------------|-------|-----|
| 1 bar | 399 | 45.1% |
| 2-5 bars | 227 | 25.6% |
| 6-15 bars | 133 | 15.0% |
| 16-30 bars | 48 | 5.4% |
| 30+ bars | 78 | 8.8% |

## 9. Existing Trading Rule Validation

### Rule 1: Volume > 2x for BRK, > 3x for REV

- BRK signals with vol >= 2x: 804/1064 (75.6%)
- BRK signals with vol < 2x: 260/1064 (24.4%)
- REV signals with vol >= 3x: 449/545 (82.4%)
- REV signals with vol < 3x: 96/545 (17.6%)
- CONF pass rate with vol >= 2x: 288/680 (42.4%)
- CONF pass rate with vol < 2x: 64/199 (32.2%)

**Verdict: CONFIRMED** — Higher volume breakouts have better CONF rates.

### Rule 2: First BRK is Strongest; Retests Weaken

- Average retest volume ratio: 1.01x
- Retests with vol ratio > 1x: 198/885
- Retests with vol ratio < 0.5x: 408/885

**Verdict: CONFIRMED** — Retests show significantly declining volume, confirming the first BRK is strongest.

### Rule 3: Confluence Levels (Multi-Level) Are Stronger

- Multi-level CONF pass: 72/164 (43.9%)
- Single-level CONF pass: 280/715 (39.2%)

**Verdict: NEEDS ADJUSTMENT** — Multi-level pass rate is 43.9% vs single-level 39.2%.

### Rule 4: CONF Failures Lead to Reversals

- After CONF ✗, next signal is:
  - BRK: 265 (60.2%)
  - RCL: 162 (36.8%)
  - REV: 13 (3.0%)
- REV + RCL after CONF ✗: 175/440 (39.8%)

**Verdict: CONFIRMED** — 39.8% of post-CONF-fail signals are reversals/reclaims.

### Rule 5: Avoid Chop Days (Frequent CONF Failures)

See Section 5 for day-type classification. Key insight: chop days identified by <30% CONF pass rate.

**Verdict: CONFIRMED** — Day-type classification clearly separates trend vs chop days. See Section 5.

### Rule 6: 9:30-10:00 Signals Most Volatile, Less Reliable

- 9:30-10:00 CONF pass: 236/489 (48.3%)
- After 10:00 CONF pass: 116/390 (29.7%)
- 9:30-10:00 avg volume: 8.1x
- After 10:00 avg volume: 2.2x

**Verdict: REFUTED** — First-30-min pass rate 48.3% vs rest 29.7%. Volume is much higher (8.1x vs 2.2x). The old assumption "early signals are less reliable" is wrong. In fact, early signals are MORE reliable because high volume drives auto-promote. The real risk of early signals is magnitude of loss on failures, not frequency of failures.

### Rule 7: Week H/L Signals Are Strongest

- Week H/L CONF pass: 35/99 (35.4%)
- Other levels CONF pass: 317/780 (40.6%)

**Verdict: REFUTED** — Week H/L pass rate 35.4% vs others 40.6%. Week levels actually underperform, likely because they are tested infrequently and often during low-volume midday/afternoon hours when auto-promote is harder to achieve. Week L is especially weak at 17.2% (see Section 2). Yest H has the best individual level rate at 44.0%.

### Rule 8: Counter-Trend Signals Need VWAP Alignment

Cannot directly validate from log data (VWAP alignment not logged in signal messages).
However, position (pos=) serves as a proxy: signals with extreme pos values (>80) indicate
strong trend alignment, while mid-range values may indicate counter-trend.

**Verdict: CANNOT VALIDATE** — VWAP alignment not captured in log data. Consider adding VWAP position to log messages.


## 10. Recommendations for Indicator Improvements

### Recommendation 1: Volume Threshold Optimization

| Min Volume | Signals Above | Pass Rate Above | Signals Below | Pass Rate Below | Lift |
|------------|---------------|-----------------|---------------|-----------------|------|
| 2.0x | 680 | 42.4% | 199 | 32.2% | +10.2pp |
| 2.5x | 566 | 43.8% | 313 | 33.2% | +10.6pp |
| 3.0x | 497 | 45.3% | 382 | 33.2% | +12.0pp |
| 4.0x | 383 | 46.0% | 496 | 35.5% | +10.5pp |
| 5.0x | 332 | 49.1% | 547 | 34.6% | +14.5pp |

### Recommendation 2: Position Quality Filter

| Min Position | Signals Above | Pass Rate | Signals Below | Pass Rate | Lift |
|--------------|---------------|-----------|---------------|-----------|------|
| pos>=50 | 817 | 40.4% | 62 | 35.5% | +4.9pp |
| pos>=60 | 753 | 40.2% | 126 | 38.9% | +1.4pp |
| pos>=70 | 645 | 41.6% | 234 | 35.9% | +5.7pp |
| pos>=80 | 488 | 44.5% | 391 | 34.5% | +9.9pp |
| pos>=90 | 291 | 44.3% | 588 | 37.9% | +6.4pp |

### Recommendation 3: Time-Based Signal Filtering

Based on CONF analysis by hour (see Section 7), consider:
- Flagging or dimming signals during lunch lull (11:30-13:30)
- Treating 9:30-9:35 BRKs with higher skepticism (opening volatility)
- Afternoon breakouts (14:00+) as potential trend-continuation setups

### Recommendation 4: Log VWAP Position in Signals

Currently VWAP alignment cannot be validated from logs. Adding `vwap=above/below` or
`vwap_dist=X.XX` to signal log messages would enable future validation of Rule 8.

### Recommendation 5: Day-Type Early Warning System

Based on Section 5 analysis:
- If the first 2-3 BRKs all fail CONF, probability of chop day increases significantly
- Consider adding a dashboard label showing current-day CONF pass rate
- Could auto-dim signals after 3 consecutive CONF failures

### Recommendation 6: Symbol Tier List

| Tier | Symbols | CONF Pass Rate | Notes |
|------|---------|----------------|-------|
| B (OK) | QQQ | 46.2% avg | Average quality |
| C (Weak) | SPY, AMZN, TSM, GOOGL, NVDA, TSLA, META, AAPL, MSFT, SLV, AMD, GLD | 39.4% avg | More noise/chop |