# TSLA Open Scalper — Final Out-of-Sample Validation Report

**Generated**: 2026-03-20
**Data range**: 2025-03-19 to 2026-03-19 (252 trading days)
**Train period**: first 175 days (2025-03-19 to 2025-11-25)
**Test period**: last 77 days (2025-11-26 to 2026-03-19)

## Overview

- Total days: 252
- Days with signals (not killed): 188
- Days killed: 64 (25%)
- Kill reasons: {'P9': 27, 'VIX<=15': 20, 'gap_flat': 11, 'gap<-5': 6}
- Days with trades: 214
- Skipped (stall/no_bounce): 38
- Size distribution: L=191, M=12, S(skip)=49
- Entry types: A=42, B=58, flat_1m=114

## Test 1: Walk-Forward Validation

**Train** (175 cal days, 157 trades):
  - Raw PnL (1x): $49.72 | per trade: $0.32 | per cal day: $0.28
  - Sized PnL (3x/1x/0x): $184.26 | per trade: $1.17 | per cal day: $1.05
  - Win%: 55.4% (87/157)
**Test** (77 cal days, 57 trades):
  - Raw PnL (1x): $42.26 | per trade: $0.74 | per cal day: $0.55
  - Sized PnL (3x/1x/0x): $81.96 | per trade: $1.44 | per cal day: $1.06
  - Win%: 57.9% (33/57)

**Test/Train per-day ratio (sized)**: 1.01
**Test period sized PnL**: $81.96
**PASS criteria**: Test PnL > 0: PASS
**PASS criteria**: Ratio >= 0.60: PASS

## Test 2: Two-Half Split

**Half 1 (first 126 days)**: 122 trades, Raw PnL: $51.01, Sized PnL: $171.16, Win%: 55.7%
**Half 2 (last 126 days)**: 92 trades, Raw PnL: $40.97, Sized PnL: $95.07, Win%: 56.5%

**PASS criteria**: Both halves positive: PASS

## Test 3: Monthly PnL

| Month | Trades | Wins | Win% | Raw PnL | Sized PnL | Avg Sized |
|-------|--------|------|------|---------|-----------|-----------|
| 2025-03 | 9 | 4 | 44% | $-6.58 | $6.06 | $0.67 |
| 2025-04 | 21 | 10 | 48% | $1.79 | $-1.32 ** | $-0.06 |
| 2025-05 | 21 | 13 | 62% | $12.10 | $24.71 | $1.18 |
| 2025-06 | 20 | 15 | 75% | $41.47 | $123.39 | $6.17 |
| 2025-07 | 22 | 13 | 59% | $11.29 | $40.68 | $1.85 |
| 2025-08 | 21 | 10 | 48% | $-8.47 | $-23.05 ** | $-1.10 |
| 2025-09 | 14 | 6 | 43% | $-6.23 | $-16.23 ** | $-1.16 |
| 2025-10 | 15 | 8 | 53% | $-2.05 | $18.03 | $1.20 |
| 2025-11 | 15 | 9 | 60% | $6.73 | $11.99 | $0.80 |
| 2025-12 | 18 | 12 | 67% | $29.71 | $59.28 | $3.29 |
| 2026-01 | 14 | 7 | 50% | $6.25 | $15.56 | $1.11 |
| 2026-02 | 13 | 7 | 54% | $-2.25 | $-1.23 ** | $-0.09 |
| 2026-03 | 11 | 6 | 55% | $8.22 | $8.36 | $0.76 |

**Losing months**: 4 of 13
**Max monthly drawdown**: $-23.05
**PASS criteria**: <= 2 losing months: FAIL

## Test 4: Worst-Case Analysis

**Worst single day (sized)**: 2025-05-12 → $-23.85 (raw: $-7.95, size: L)
**Worst 3-trade streak**: $-25.15 (trades 125-127)
**Max single-trade raw loss**: $-7.95
**Max single-trade loss at 3x**: $-23.85
**PASS criteria**: Max loss at 3x < $8: FAIL
**Overall win%**: 56.1% (120/214)
**% of ALL days that are winners**: 47.6%

## Test 5: Comparison Table

### 1x Flat Binary (enter every non-killed day at 9:30 open, exit 2 min later)

**Train Period**

| System | PnL | Win% | Trades | $/trade | Sharpe |
|--------|-----|------|--------|---------|--------|
| Binary flat 1x | $49.72 | 55% | 157 | $0.32 | 1.83 |
| Binary + sizing 3x/1x/0x | $184.26 | 46% | 125 | $1.47 | 2.90 |
| Full system (smart entry) | $13.79 | 53% | 36 | $0.38 | 0.79 |

**Test Period**

| System | PnL | Win% | Trades | $/trade | Sharpe |
|--------|-----|------|--------|---------|--------|
| Binary flat 1x | $42.26 | 58% | 57 | $0.74 | 5.41 |
| Binary + sizing 3x/1x/0x | $81.96 | 44% | 45 | $1.82 | 4.42 |
| Full system (smart entry) | $81.96 | 56% | 45 | $1.82 | 4.42 |


## Test 6: Quarterly Stability

| Quarter | Trades | Wins | Win% | Raw PnL | Sized PnL | $/trade |
|---------|--------|------|------|---------|-----------|---------|
| 2025-Q1 | 9 | 4 | 44% | $-6.58 | $6.06 | $0.67 |
| 2025-Q2 | 62 | 38 | 61% | $55.36 | $146.78 | $2.37 |
| 2025-Q3 | 57 | 29 | 51% | $-3.41 | $1.40 | $0.02 |
| 2025-Q4 | 48 | 29 | 60% | $34.39 | $89.31 | $1.86 |
| 2026-Q1 | 38 | 20 | 53% | $12.22 | $22.68 | $0.60 |

## Test 7: Entry Quality (Test Period Only)

**Entry A**: 22 trades, Win%: 55%, Raw PnL: $7.40, Avg: $0.34, Sized PnL: $9.69
**Entry B**: 35 trades, Win%: 60%, Raw PnL: $34.86, Avg: $1.00, Sized PnL: $72.27
**Entry flat_1m**: 0 trades

**Skipped (test)**: stall=20, no_bounce=0

---
## VERDICT

| Criterion | Result | Value |
|-----------|--------|-------|
| Test period PnL > 0 | PASS | $81.96 |
| Test/train per-day ratio >= 0.60 | PASS | 1.01 |
| Both halves positive | PASS | H1=$171.16, H2=$95.07 |
| Losing months <= 2 | FAIL | 4 of 13 |
| Max loss at 3x < $8 | FAIL | $23.85 |

### **OVERALL: FAIL**

Failed criteria: Losing months <= 2, Max loss at 3x < $8