# KLB Pine Log Analysis — v3.7a

_Generated: 2026-03-12 09:32_

**Files processed:** 17 total (8 large, 9 small)

**Date range:** 2025-07-21 → 2026-03-11

**Total rows parsed into signal records:** 9,990


---

## 1. File → Symbol Mapping

| Hash | Symbol | Size (KB) | Type | Date Range | Parsed Rows |
|------|--------|-----------|------|------------|-------------|
| 32745 | **AAPL** | 184 | large | 2025-10-06 → 2026-03-11 | 1,040 |
| b0094 | **AMD** | 209 | large | 2025-10-06 → 2026-03-11 | 1,168 |
| a9160 | **AMZN** | 12 | small | 2025-10-06 → 2026-03-11 | 160 |
| ba5bd | **GLD** | 192 | large | 2025-09-29 → 2026-03-11 | 1,052 |
| 650b2 | **GOOGL** | 14 | small | 2025-10-06 → 2026-03-11 | 172 |
| fca86 | **META** | 13 | small | 2025-10-06 → 2026-03-11 | 169 |
| 4c0a5 | **MSFT** | 167 | large | 2025-10-06 → 2026-03-11 | 965 |
| 0d0bc | **MU** | 181 | large | 2025-10-06 → 2026-03-11 | 1,030 |
| 75eb2 | **NFLX** | 190 | large | 2025-10-06 → 2026-03-11 | 1,131 |
| e52f5 | **NVDA** | 12 | small | 2025-10-06 → 2026-03-11 | 163 |
| fce00 | **QQQ** | 12 | small | 2025-10-06 → 2026-03-11 | 151 |
| 892e4 | **SLV** | 159 | large | 2025-10-06 → 2026-03-11 | 899 |
| 6d48f | **SPY** | 10 | small | 2025-10-06 → 2026-03-09 | 152 |
| 22869 | **SPY** | 2 | small | 2026-02-02 → 2026-03-09 | 31 |
| 2e3a0 | **TSLA** | 12 | small | 2025-10-06 → 2026-03-11 | 165 |
| 8760a | **TSM** | 14 | small | 2025-10-06 → 2026-03-11 | 191 |
| a7371 | **XLE** | 235 | large | 2025-07-21 → 2026-03-11 | 1,351 |


---

## 2. Overall Signal Counts by Type

**Total signals:** 7,653

| Signal Type | Count | % of Total |
|-------------|-------|------------|
| BRK | 1,190 | 15.5% |
| REV | 3,788 | 49.5% |
| FADE | 719 | 9.4% |
| RNG | 1,834 | 24.0% |
| QBS | 122 | 1.6% |

**Also:** CONF rows: 1,251 | 5m CHECK rows: 1,086


---

## 3. Signal Counts by Symbol

| Symbol | Total | BRK | REV | FADE | RNG | QBS | Bull | Bear |
|--------|-------|-----|-----|------|-----|-----|------|------|
| **AAPL** | 766 | 139 | 456 | 50 | 119 | 2 | 334 | 432 |
| **AMD** | 848 | 167 | 513 | 54 | 111 | 3 | 316 | 532 |
| **AMZN** | 160 | 0 | 0 | 46 | 107 | 7 | 63 | 97 |
| **GLD** | 799 | 127 | 521 | 51 | 94 | 6 | 249 | 550 |
| **GOOGL** | 172 | 0 | 11 | 45 | 110 | 6 | 91 | 81 |
| **META** | 169 | 0 | 3 | 44 | 113 | 9 | 82 | 87 |
| **MSFT** | 691 | 143 | 388 | 37 | 117 | 6 | 287 | 404 |
| **MU** | 748 | 138 | 450 | 34 | 113 | 13 | 286 | 462 |
| **NFLX** | 765 | 192 | 403 | 48 | 118 | 4 | 294 | 471 |
| **NVDA** | 163 | 0 | 2 | 37 | 117 | 7 | 95 | 68 |
| **QQQ** | 149 | 1 | 3 | 36 | 102 | 7 | 77 | 72 |
| **SLV** | 671 | 116 | 430 | 32 | 87 | 6 | 221 | 450 |
| **SPY** | 183 | 0 | 0 | 46 | 133 | 4 | 97 | 86 |
| **TSLA** | 165 | 0 | 0 | 48 | 112 | 5 | 89 | 76 |
| **TSM** | 191 | 0 | 0 | 53 | 122 | 16 | 102 | 89 |
| **XLE** | 1013 | 167 | 608 | 58 | 159 | 21 | 392 | 621 |


---

## 4. CONF Rate

- **Total CONF rows:** 1,251
- **CONF ✓:** 1,220 (97.5%)
- **CONF ✗:** 31 (2.5%)

### CONF ✓ by signal type promoted:
| Type | CONF ✓ | CONF ✗ | Rate |
|------|--------|--------|------|
| BRK | 1190 | 0 | 100.0% |
| QBS | 30 | 31 | 49.2% |

### CONF rate by symbol:
| Symbol | CONF ✓ | CONF ✗ | Rate |
|--------|--------|--------|------|
| **AAPL** | 141 | 0 | 100.0% |
| **AMD** | 168 | 2 | 98.8% |
| **GLD** | 130 | 3 | 97.7% |
| **MSFT** | 146 | 3 | 98.0% |
| **MU** | 148 | 3 | 98.0% |
| **NFLX** | 195 | 1 | 99.5% |
| **QQQ** | 1 | 0 | 100.0% |
| **SLV** | 118 | 4 | 96.7% |
| **XLE** | 173 | 15 | 92.0% |


---

## 5. 5m CHECK (HOLD vs BAIL) Statistics

- **Total 5m CHECKs:** 1,086
- **HOLD:** 894 (82.3%)
- **BAIL:** 192 (17.7%)

**PnL at 5m check (in ATR fractions):**
- All checks avg pnl: -0.015
- HOLD checks avg pnl: +0.011 (n=894)
- BAIL checks avg pnl: -0.137 (n=192)
- Win rate at check time (pnl>0): 42.4%
  - HOLD win rate: 51.6%
  - BAIL win rate: 0.0%

### 5m CHECK by direction:
- Bull HOLD avg pnl: +0.017 (n=243), BAIL avg: -0.152 (n=42)
- Bear HOLD avg pnl: +0.009 (n=651), BAIL avg: -0.133 (n=150)

### 5m CHECK by symbol:
| Symbol | HOLD | BAIL | Bail% | HOLD avg pnl | BAIL avg pnl |
|--------|------|------|-------|--------------|--------------|
| **AAPL** | 101 | 32 | 24.1% | +0.004 | -0.138 |
| **AMD** | 127 | 23 | 15.3% | +0.006 | -0.142 |
| **GLD** | 106 | 14 | 11.7% | +0.010 | -0.109 |
| **MSFT** | 99 | 26 | 20.8% | +0.011 | -0.155 |
| **MU** | 111 | 20 | 15.3% | +0.009 | -0.166 |
| **NFLX** | 145 | 25 | 14.7% | +0.004 | -0.122 |
| **QQQ** | 1 | 0 | 0.0% | +0.000 | +0.000 |
| **SLV** | 84 | 22 | 20.8% | +0.013 | -0.136 |
| **XLE** | 120 | 30 | 20.0% | +0.032 | -0.122 |


---

## 6. Top Active Days

| Date | Signal Count |
|------|-------------|
| 2025-12-02 | 98 |
| 2025-11-06 | 93 |
| 2025-12-05 | 91 |
| 2026-01-28 | 91 |
| 2025-10-17 | 90 |
| 2025-12-04 | 89 |
| 2026-03-11 | 89 |
| 2026-02-23 | 88 |
| 2025-11-13 | 86 |
| 2025-11-19 | 86 |
| 2026-01-30 | 86 |
| 2025-11-03 | 85 |
| 2026-02-19 | 85 |
| 2026-01-13 | 84 |
| 2026-02-12 | 83 |


---

## 7. Time-of-Day Distribution

| Period | Total | BRK | REV | FADE | RNG | QBS | % |
|--------|-------|-----|-----|------|-----|-----|---|
| morning (9:30-11) | 5642 | 821 | 2350 | 537 | 1834 | 100 | 73.7% |
| midday (11-14) | 1263 | 219 | 877 | 154 | 0 | 13 | 16.5% |
| afternoon (14-16) | 748 | 150 | 561 | 28 | 0 | 9 | 9.8% |

_Note: RNG fires exclusively at open (all 1,834 in morning window), inflating morning% to 73.7%._
_Excluding RNG: morning=3808/5819 = 65.4% of non-RNG signals._


---

## 8. Must-Trade Signal Summary (non-dim BRK + REV)

- **Non-dim BRK signals:** 1,190
- **Non-dim REV signals:** 3,083
- **Dim BRK signals:** 0
- **Dim REV signals:** 705

Note: dim detection uses 'x~' or '?' markers in message. If v3.7a doesn't emit these,
dim counts may undercount — check raw dim values above.

- Bull must-trade: 1,665 | Bear must-trade: 2,608


---

## 9. Volume Statistics

- BRK avg vol: 4.87x (n=1190)
- REV avg vol: 3.93x (n=3788)
- RNG avg vol: 10.15x (n=1834)


---

## 10. Anomalies & Patterns

**Multiple files for same symbol (potential duplicate coverage):**
- SPY: 22869, 6d48f

**Symbols with NO CONF rows:** AMZN, GOOGL, META, NVDA, SPY, TSLA, TSM

**Symbols with NO 5m CHECK rows:** AMZN, GOOGL, META, NVDA, SPY, TSLA, TSM

**AAPL: High REV rate** — 60% of signals are REV
**AMD: High REV rate** — 60% of signals are REV
**GLD: High REV rate** — 65% of signals are REV
**MSFT: High REV rate** — 56% of signals are REV
**MU: High REV rate** — 60% of signals are REV
**NFLX: High REV rate** — 53% of signals are REV
**SLV: High REV rate** — 64% of signals are REV
**XLE: High REV rate** — 60% of signals are REV


---

## 11. Daily Signal Count Heatmap (top 5 per symbol)

| Symbol | Best Day | Count | 2nd | Count | 3rd | Count |
|--------|----------|-------|-----|-------|-----|-------|
| **AAPL** | 2026-02-06 | 15 | 2025-11-12 | 14 | 2025-12-04 | 14 |
| **AMD** | 2025-12-22 | 21 | 2026-01-28 | 21 | 2025-12-02 | 19 |
| **AMZN** | 2025-11-24 | 4 | 2025-12-09 | 4 | 2026-01-09 | 4 |
| **GLD** | 2025-11-03 | 24 | 2025-12-05 | 24 | 2025-11-06 | 21 |
| **GOOGL** | 2026-03-11 | 14 | 2025-10-22 | 4 | 2026-01-27 | 4 |
| **META** | 2025-10-16 | 4 | 2026-03-11 | 4 | 2025-10-09 | 3 |
| **MSFT** | 2026-02-12 | 19 | 2025-12-16 | 15 | 2025-10-17 | 14 |
| **MU** | 2026-01-23 | 18 | 2025-10-31 | 17 | 2025-10-27 | 16 |
| **NFLX** | 2025-12-02 | 22 | 2026-01-13 | 18 | 2025-10-23 | 14 |
| **NVDA** | 2025-10-07 | 4 | 2025-10-09 | 4 | 2026-01-06 | 4 |
| **QQQ** | 2026-03-11 | 5 | 2025-12-09 | 4 | 2025-10-10 | 3 |
| **SLV** | 2026-01-21 | 20 | 2025-11-06 | 19 | 2026-02-05 | 16 |
| **SPY** | 2026-02-05 | 5 | 2026-02-06 | 4 | 2026-02-17 | 4 |
| **TSLA** | 2025-11-06 | 4 | 2025-11-19 | 4 | 2026-01-07 | 4 |
| **TSM** | 2025-12-02 | 6 | 2025-10-24 | 4 | 2025-11-03 | 4 |
| **XLE** | 2026-01-28 | 19 | 2025-09-18 | 17 | 2025-10-15 | 15 |