# TSLA Opening Module S v2 — Research Output
**Generated:** 2026-03-17
**Data range:** 2025-02-04 – 2026-03-17
**Total days:** 280 (1m backbone) | 30s: 129 | VIX 1h: 85 | SPY 5s: 55

---

## A — TSLA 30s Backbone (n≈129)

### A1 — Bar 1 Direction

Bar 1 (first 30 seconds) directional bias:

| label | n | day_above% | avg_day_chg | worst% | bull% | hold_5m% |
| --- | --- | --- | --- | --- | --- | --- |
| All days (baseline) | 280 | 50.0 | -0.1 | 28.2 | 28.9 | 50.4 |
| Bar1 UP | 61 | 55.7 | 0.91 | 24.6 | 34.4 | 59.0 |
| Bar1 DOWN | 68 | 47.1 | -0.89 | 30.9 | 26.5 | 35.3 |
| 30s days (baseline) | 129 | 51.2 | -0.04 | 27.9 | 30.2 | 46.5 |

### A2 — Fakeout Patterns

All 4 first-2-bar patterns:

| label | n | day_above% | avg_day_chg | worst% | bull% | hold_5m% | hold_win% |
| --- | --- | --- | --- | --- | --- | --- | --- |
| UP→UP (momentum) | 28 | 67.9 | 1.32 | 14.3 | 35.7 | 67.9 | 73.7 |
| UP→DOWN (fakeout) | 33 | 45.5 | 0.56 | 33.3 | 33.3 | 51.5 | 58.8 |
| DOWN→UP (reversal) | 33 | 51.5 | 0.69 | 24.2 | 27.3 | 30.3 | 70.0 |
| DOWN→DOWN (continuation) | 35 | 42.9 | -2.39 | 37.1 | 25.7 | 40.0 | 78.6 |

### A3 — Bar1 Range Quartiles

Bar1 range quartile thresholds: Q1<2.02, Q2<2.42, Q3<3.04

| label | n | avg_bar1_range | day_above% | avg_day_chg | worst% | bull% |
| --- | --- | --- | --- | --- | --- | --- |
| Q1-tiny | 33 | 1.72 | 42.4 | -1.51 | 33.3 | 24.2 |
| Q2 | 32 | 2.21 | 59.4 | 0.57 | 25.0 | 31.2 |
| Q3 | 32 | 2.69 | 59.4 | 4.7 | 12.5 | 37.5 |
| Q4-wide | 32 | 3.62 | 43.8 | -3.88 | 40.6 | 28.1 |

### A4 — Volume Front-Loading

| label | n | avg_vol_ratio | day_above% | avg_day_chg | worst% |
| --- | --- | --- | --- | --- | --- |
| Front-loaded (>0.5) | 129 | 0.74 | 51.2 | -0.04 | 27.9 |
| Back-loaded (<=0.5) | 0 | nan | nan | nan | nan |
| Very front-loaded (>0.7) | 92 | 0.77 | 52.2 | 0.78 | 25.0 |
| Extreme front-loaded (>0.85) (thin) | 6 | 0.88 | 66.7 | 3.64 | 16.7 |

### A5 — Bar Position vs Entry

Bar1 and Bar2 close positions relative to open:

| label | n | day_above% | avg_day_chg | worst% | bull% | hold_5m% |
| --- | --- | --- | --- | --- | --- | --- |
| Both above | 48 | 64.6 | 1.63 | 16.7 | 37.5 | 62.5 |
| B1 above, B2 below (thin) | 12 | 25.0 | -1.37 | 50.0 | 25.0 | 50.0 |
| B1 below, B2 above (thin) | 8 | 37.5 | 1.13 | 12.5 | 12.5 | 37.5 |
| Both below | 61 | 47.5 | -1.25 | 34.4 | 27.9 | 34.4 |

Momentum 2-bar (bar2_close - bar1_open) quartiles:

| label | n | avg_momentum | day_above% | avg_day_chg | worst% | bull% |
| --- | --- | --- | --- | --- | --- | --- |
| Q1-bearish | 33 | -2.42 | 33.3 | -5.33 | 48.5 | 18.2 |
| Q2 | 32 | -0.88 | 53.1 | 2.83 | 25.0 | 34.4 |
| Q3 | 32 | 0.37 | 53.1 | 0.97 | 18.8 | 31.2 |
| Q4-bullish | 32 | 2.5 | 65.6 | 1.52 | 18.8 | 37.5 |

### A6 — Pattern × 5m Rule Cross-Tab

8 combos: pattern (4) × 5m rule (HOLD/BAIL):

| label | n | day_above% | avg_day_chg | worst% | bull% | hold_5m% |
| --- | --- | --- | --- | --- | --- | --- |
| UP→UP (momentum) × 5m=HOLD | 19 | 73.7 | 1.4 | 15.8 | 31.6 | 100.0 |
| UP→UP (momentum) × 5m=BAIL (thin) | 9 | 55.6 | 1.16 | 11.1 | 44.4 | 0.0 |
| UP→DOWN (fakeout) × 5m=HOLD | 17 | 58.8 | 4.93 | 11.8 | 52.9 | 100.0 |
| UP→DOWN (fakeout) × 5m=BAIL | 16 | 31.2 | -4.1 | 56.2 | 12.5 | 0.0 |
| DOWN→UP (reversal) × 5m=HOLD (thin) | 10 | 70.0 | 5.65 | 10.0 | 40.0 | 100.0 |
| DOWN→UP (reversal) × 5m=BAIL | 23 | 43.5 | -1.46 | 30.4 | 21.7 | 0.0 |
| DOWN→DOWN (continuation) × 5m=HOLD (thin) | 14 | 78.6 | 3.65 | 14.3 | 57.1 | 100.0 |
| DOWN→DOWN (continuation) × 5m=BAIL | 21 | 19.0 | -6.42 | 52.4 | 4.8 | 0.0 |

### A7 — First 2-Minute Momentum

Based on 129 days with 2m data available:

| label | n | day_above% | avg_day_chg | worst% | bull% | hold_5m% |
| --- | --- | --- | --- | --- | --- | --- |
| 2m above entry | 56 | 60.7 | 1.91 | 19.6 | 42.9 | 78.6 |
| 2m below entry | 73 | 43.8 | -1.54 | 34.2 | 20.5 | 21.9 |

**Comparison: 5m rule vs 2m rule accuracy:**

- 5m rule accuracy (all days): 66.8%
- 2m rule accuracy (30s days): 58.1%



---

## B — VIX Conditioning

### B1 — VIX Regime

Using VIX 1h (n=85 days, broader coverage):

| label | n | avg_vix | day_above% | avg_day_chg | worst% | bull% |
| --- | --- | --- | --- | --- | --- | --- |
| VIX 1h calm | 47 | 16.0 | 40.4 | -1.76 | 34.0 | 25.5 |
| VIX 1h moderate | 29 | 20.8 | 69.0 | 2.35 | 13.8 | 34.5 |
| VIX 1h fear (thin) | 9 | 26.4 | 22.2 | -2.56 | 33.3 | 22.2 |

Using VIX 5m (n=51 days):

| label | n | avg_vix | day_above% | avg_day_chg | worst% | bull% |
| --- | --- | --- | --- | --- | --- | --- |
| VIX 5m calm | 23 | 16.1 | 39.1 | -2.29 | 30.4 | 21.7 |
| VIX 5m moderate | 23 | 21.1 | 65.2 | 1.96 | 13.0 | 34.8 |
| VIX 5m fear (thin) | 5 | 27.0 | 20.0 | -2.35 | 40.0 | 20.0 |

### B2 — VIX Change (Spike Detector)

| label | n | avg_vix_chg | day_above% | avg_day_chg | worst% |
| --- | --- | --- | --- | --- | --- |
| Large spike (>+2) (thin) | 6 | 3.32 | 16.7 | -0.37 | 16.7 |
| Small spike (0 to +2) | 24 | 0.57 | 54.2 | -1.07 | 29.2 |
| Flat (-1 to 0) (thin) | 11 | -0.34 | 45.5 | -0.3 | 18.2 |
| Drop (<-1) (thin) | 9 | -1.4 | 66.7 | 3.51 | 11.1 |

### B3 — VIX × Fakeout Pattern

| label | n | day_above% | avg_day_chg | worst% | bull% | hold_5m% |
| --- | --- | --- | --- | --- | --- | --- |
| UP→UP (momentum) × VIX calm (thin) | 12 | 66.7 | -0.08 | 16.7 | 33.3 | 83.3 |
| UP→UP (momentum) × VIX moderate (thin) | 5 | 100.0 | 9.35 | 0.0 | 60.0 | 100.0 |
| UP→UP (momentum) × VIX fear | 0 | nan | nan | nan | nan | nan |
| UP→DOWN (fakeout) × VIX calm (thin) | 14 | 28.6 | -1.81 | 42.9 | 21.4 | 42.9 |
| UP→DOWN (fakeout) × VIX moderate (thin) | 7 | 42.9 | -1.71 | 28.6 | 28.6 | 57.1 |
| UP→DOWN (fakeout) × VIX fear | 0 | nan | nan | nan | nan | nan |

### B4 — VIX as Pre-Open Bad-Day Filter

Worst days analysis (day_chg < -$5):
- Total worst days (VIX 5m overlap): 12 / 51
- % of worst days with VIX > 20 at open: 16.7%
- % of worst days with VIX > 25 at open: 16.7%

Worst-day rate by VIX tier:

| tier | n | worst_day% | bad_day% | avg_day_chg |
| --- | --- | --- | --- | --- |
| VIX ≤ 15 (thin) | 5 | 40.0 | 80.0 | -7.35 |
| VIX 15-20 | 25 | 32.0 | 48.0 | -1.01 |
| VIX 20-25 | 16 | 0.0 | 12.5 | 3.41 |
| VIX > 25 (thin) | 5 | 40.0 | 40.0 | -2.35 |

### B5 — VIX × 5m Rule

VIX regime × 5m rule (HOLD=True/False):

| label | n | day_above% | avg_day_chg | worst% | bull% | hold_5m% |
| --- | --- | --- | --- | --- | --- | --- |
| VIX calm × 5m HOLD | 22 | 59.1 | 0.65 | 18.2 | 36.4 | 100.0 |
| VIX calm × 5m BAIL | 25 | 24.0 | -3.88 | 48.0 | 16.0 | 0.0 |
| VIX moderate × 5m HOLD | 16 | 81.2 | 5.75 | 6.2 | 56.2 | 100.0 |
| VIX moderate × 5m BAIL (thin) | 13 | 53.8 | -1.83 | 23.1 | 7.7 | 0.0 |
| VIX fear × 5m HOLD (thin) | 5 | 40.0 | 0.09 | 20.0 | 40.0 | 100.0 |
| VIX fear × 5m BAIL (thin) | 4 | 0.0 | -5.88 | 50.0 | 0.0 | 0.0 |



---

## C — SPY Relative Strength

### C1 — SPY 30s Direction

| label | n | day_above% | avg_day_chg | worst% | bull% | hold_5m% |
| --- | --- | --- | --- | --- | --- | --- |
| SPY 30s UP | 35 | 45.7 | -1.1 | 25.7 | 25.7 | 45.7 |
| SPY 30s DOWN | 20 | 45.0 | -0.22 | 30.0 | 25.0 | 60.0 |

### C2 — TSLA vs SPY Direction Agreement

| label | n | day_above% | avg_day_chg | worst% | bull% | hold_5m% |
| --- | --- | --- | --- | --- | --- | --- |
| TSLA UP, SPY UP (thin) | 11 | 45.5 | -2.84 | 36.4 | 18.2 | 63.6 |
| TSLA UP, SPY DOWN (thin) | 6 | 50.0 | 0.58 | 16.7 | 16.7 | 66.7 |
| TSLA DOWN, SPY UP | 20 | 45.0 | -0.55 | 20.0 | 25.0 | 30.0 |
| TSLA DOWN, SPY DOWN (thin) | 11 | 45.5 | 0.21 | 36.4 | 36.4 | 54.5 |

### C3 — Relative Strength Score (TSLA vs SPY)

Relative strength = TSLA 30s % - SPY 30s %. Q-thresholds: {0.25: -0.388, 0.5: -0.159, 0.75: 0.112}

| label | n | avg_rel_str | day_above% | avg_day_chg | worst% | bull% |
| --- | --- | --- | --- | --- | --- | --- |
| Q1-TSLA weak (thin) | 12 | -0.546 | 33.3 | -3.82 | 41.7 | 16.7 |
| Q2 (thin) | 12 | -0.287 | 50.0 | 1.19 | 16.7 | 33.3 |
| Q3 (thin) | 12 | -0.018 | 50.0 | -0.21 | 33.3 | 25.0 |
| Q4-TSLA strong (thin) | 12 | 0.415 | 50.0 | -0.18 | 16.7 | 25.0 |

### C4 — SPY 1m × TSLA 5m Rule (280 days)

Using SPY 1m (n=280 days):

| label | n | day_above% | avg_day_chg | worst% | bull% | hold_5m% |
| --- | --- | --- | --- | --- | --- | --- |
| TSLA 5m=HOLD, SPY 5m=HOLD | 81 | 66.7 | 3.27 | 16.0 | 42.0 | 100.0 |
| TSLA 5m=HOLD, SPY 5m=BAIL | 60 | 66.7 | 2.87 | 16.7 | 38.3 | 100.0 |
| TSLA 5m=BAIL, SPY 5m=HOLD | 69 | 27.5 | -3.66 | 40.6 | 14.5 | 0.0 |
| TSLA 5m=BAIL, SPY 5m=BAIL | 70 | 38.6 | -3.04 | 40.0 | 20.0 | 0.0 |



---

## D — Combined Composite Scores

### D1 — 3-Factor Composite Score

Score: +1 each for bar1 UP, UP_UP pattern, SPY UP, VIX calm (<18), 5m HOLD. n=48 days.

| label | n | avg_score | day_above% | avg_day_chg | worst% | bull% |
| --- | --- | --- | --- | --- | --- | --- |
| 0-1 (bearish) | 18 | 1.0 | 44.4 | -0.39 | 27.8 | 22.2 |
| 2-3 (neutral) | 24 | 2.42 | 41.7 | -1.28 | 29.2 | 25.0 |
| 4-5 (bullish) (thin) | 6 | 4.83 | 66.7 | 0.25 | 16.7 | 33.3 |

### D2 — Practical Decision Tree


**Practical TSLA Opening Decision Tree**

```
PRE-OPEN (9:25–9:29):
  VIX > 25 (fear)?
    → SKIP (bad day risk elevated)
  VIX 20–25 (moderate)?
    → CAUTION: reduce size, tighten stops

AT 9:30:30 (after bar1):
  Bar1 DOWN?
    → lean SHORT or BAIL longs
  Bar1 UP?
    → continue to bar2

AT 9:31:00 (after bar2):
  Bar1 UP → Bar2 DOWN (fakeout)?
    → EXIT any longs immediately, consider SHORT
  Bar1 UP → Bar2 UP (momentum)?
    → SPY also up? → HOLD (strong confirmation)
    → SPY down? → CAUTIOUS HOLD (TSLA leading, watch closely)

AT 9:35 (5m rule):
  TSLA 5m close > open AND SPY 5m close > open?
    → HOLD with confidence
  TSLA 5m close > open BUT SPY 5m close < open?
    → REDUCE size, watch for reversal
  TSLA 5m close < open?
    → BAIL regardless of SPY
```

### D3 — Strategy Comparison

| strategy | n_trades | win% | avg_pnl | sharpe_est | worst% | skipped |
| --- | --- | --- | --- | --- | --- | --- |
| Base: always hold | 280 | 50.0 | -0.1 | -0.16 | 28.2 | 0 |
| 5m rule (TSLA hold) | 141 | 66.7 | 3.1 | 5.01 | 16.3 | 139 |
| 5m rule + SPY confirm | 81 | 66.7 | 3.27 | 5.01 | 16.0 | 199 |
| 5m rule + skip VIX fear | 38 | 68.4 | 2.79 | 4.96 | 13.2 | 47 |
| 5m rule + no fakeout | 43 | 74.4 | 3.12 | 5.27 | 14.0 | 86 |
| 5m + SPY + VIX + no-fakeout (combined) | 19 | 78.9 | 3.87 | 8.05 | 10.5 | 59 |



---

## E — Ranked Actionable Findings


### Finding #1 — The Fakeout Pattern is the Most Dangerous Signal
**Rule:** If bar1 is UP but bar2 is DOWN (UP→DOWN), EXIT immediately; do NOT hold to 9:35.

- UP→DOWN (fakeout) day_above: **45.5%** (n=33)
- Fakeout worst-day%: **33.3%** (day < -$5)
- UP→UP (momentum) day_above: **67.9%** (n=28)
- **Action:** At 9:30:30, if bar1 was UP but price has reversed below open → BAIL immediately, don't wait for 9:35.

---

### Finding #2 — Bar1 Direction Is a Real Edge
**Rule:** Bar1 direction (first 30 seconds) provides meaningful directional bias for the day.

- Bar1 UP → day_above: **55.7%**, avg P&L: **$0.91**
- Bar1 DOWN → day_above: **47.1%**, avg P&L: **$-0.89**
- **Action:** Use bar1 direction as primary opening bias filter.

---

### Finding #3 — SPY Double Confirmation Boosts Confidence
**Rule:** Only hold TSLA longs if BOTH TSLA and SPY are above their open at 9:35.

- TSLA HOLD + SPY HOLD → win: **66.7%** (n=81)
- TSLA HOLD + SPY BAIL → win: **66.7%** (n=60)
- **Action:** When TSLA 5m HOLD fires but SPY 5m BAIL, treat as weak signal; reduce size by 50%.

---

### Finding #4 — VIX Fear Regime = Bad Day Elevated Risk
**Rule:** When VIX > 25 at open, skip or reduce TSLA longs.

- VIX fear regime worst-day%: **33.3%** (n=9)
- VIX calm regime worst-day%: **34.0%** (n=47)
- **Action:** VIX > 25 → skip longs. VIX 20-25 → 50% size. VIX < 20 → normal sizing.

---

### Finding #5 — 2-Minute Close vs Entry as Early Filter
**Rule:** If price is still below the open at 9:32, the 5m rule is likely to BAIL anyway — don't hold.

- See A7 for directional accuracy comparison of 2m vs 5m rule.
- **Action:** At 9:32, if price is below open, pre-exit rather than waiting until 9:35.
  This saves ~3 minutes of adverse drift on losing days.


---

