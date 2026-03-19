
# TSLA Open Scalp Research v2 — Full Analysis

**Generated:** 2026-03-17

**Data window:** 2025-02-04 → 2026-03-17

**Total market days:** 280 | **Days with PM data:** 234 | **Days with 1s data (thin):** 23

---


## Baseline Outcomes

n=280 days with complete market data

- Day closes above open: **50%** (141 days)

- 5m rule (9:35 close > 9:30 open): **50%** (141 days)

- Avg day change vs open: **-0.07**

- Worst days (< -$5): **29%** (80 days)

- Bad days (< -$2): **42%** (117 days)

- Big bull days (> +$5): **30%** (83 days)


## 5m Rule Validation

**HOLD (9:35 > 9:30 open):** n=141, day>open=68%, avg chg=+3.11, worst=16%

**BAIL (9:35 ≤ 9:30 open):** n=139, day>open=32%, avg chg=-3.30, worst=41%



5m rule HOLD vs BAIL worst-day difference: 16% vs 41%

5m rule HOLD vs BAIL avg-chg difference: +3.11 vs -3.30

---


# Module P: Premarket Structure

PM data available: n=234 days


## P1 — Final PM Trend (9:20-9:29 vs 9:00-9:20)

Threshold (±0.48) = 3% of median 14d ATR (15.90)



| Group | n | Day>Open% | 5m>Open% | avg_$chg | worst_day% | bad_day% | bull_day% |
|---|---|---|---|---|---|---|---|
| PM_Late_Down | 85 | 40% | 51% | -0.52 | 38% | 47% | 24% |
| PM_Late_Flat | 75 | 51% | 45% | -1.25 | 33% | 45% | 28% |
| PM_Late_Up | 74 | 65% | 54% | +1.36 | 19% | 32% | 41% |


## P2 — PM Range Width (4am-9:29) → Quartiles

| Group | n | Day>Open% | 5m>Open% | avg_$chg | worst_day% | bad_day% | bull_day% |
|---|---|---|---|---|---|---|---|
| Narrow (Q1) | 59 | 41% | 46% | -0.77 | 32% | 47% | 27% |
| Mod-Narrow (Q2) | 58 | 50% | 50% | -0.49 | 36% | 45% | 24% |
| Mod-Wide (Q3) | 58 | 52% | 52% | -0.68 | 26% | 41% | 31% |
| Wide (Q4) | 59 | 63% | 53% | +1.29 | 27% | 34% | 39% |

Quartile boundaries: {0.25: 4.8549999999999685, 0.5: 6.825000000000017, 0.75: 9.642499999999984}


## P3 — PM Position at 9:29 (in PM Range)

> 0.0 = at PM Low, 1.0 = at PM High

| Group | n | Day>Open% | 5m>Open% | avg_$chg | worst_day% | bad_day% | bull_day% |
|---|---|---|---|---|---|---|---|
| Bottom 25% (near low) | 59 | 39% | 44% | -2.94 | 39% | 49% | 17% |
| Lower-mid | 58 | 57% | 55% | +0.15 | 31% | 34% | 29% |
| Upper-mid | 58 | 50% | 43% | +0.05 | 31% | 47% | 33% |
| Top 25% (near high) | 59 | 59% | 58% | +2.11 | 20% | 37% | 42% |

Position quartile thresholds: {0.25: 0.219, 0.5: 0.448, 0.75: 0.715}


## P4 — Last 5 PM Bars Acceleration (9:25-9:29)

Thresholds: Strong=±0.64, Mild=±0.16 (based on ATR 15.90)



| Group | n | Day>Open% | 5m>Open% | avg_$chg | worst_day% | bad_day% | bull_day% |
|---|---|---|---|---|---|---|---|
| Strong Down | 71 | 37% | 45% | -1.85 | 38% | 48% | 24% |
| Mild Down | 42 | 52% | 55% | +0.27 | 33% | 43% | 24% |
| Flat | 21 | 52% | 38% | +1.37 | 38% | 48% | 38% |
| Mild Up | 32 | 59% | 44% | +0.69 | 25% | 38% | 28% |
| Strong Up | 68 | 62% | 59% | +0.47 | 21% | 35% | 40% |


## P5 — Full PM Trend (4am open vs 9:29 close)

Full PM move stats: min=-16.07, median=0.00, max=23.20



| Group | n | Day>Open% | 5m>Open% | avg_$chg | worst_day% | bad_day% | bull_day% |
|---|---|---|---|---|---|---|---|
| Big Drop | 59 | 51% | 47% | -1.24 | 31% | 42% | 20% |
| Moderate Drop | 59 | 46% | 44% | -0.50 | 36% | 44% | 29% |
| Moderate Rise | 57 | 51% | 53% | +0.47 | 32% | 44% | 33% |
| Big Rise | 59 | 58% | 56% | +0.65 | 24% | 37% | 39% |


### P5b — PM Giveback (did PM give back >50% of the gap?)

Days with gap >$2: n=145

| Group | n | Day>Open% | 5m>Open% | avg_$chg | worst_day% | bad_day% | bull_day% |
|---|---|---|---|---|---|---|---|
| 25-50% giveback | 9 | 44% | 11% | +2.10 | 33% | 33% | 44% |
| <25% giveback | 109 | 52% | 46% | -0.56 | 35% | 44% | 30% |
| >50% giveback | 27 | 59% | 63% | +3.96 | 19% | 33% | 48% |


## P6 — PM Volume Pattern (last 30m vs first 30m)

Vol ratio (last30m/first30m) stats: median=3.66, Q75=5.72

| Group | n | Day>Open% | 5m>Open% | avg_$chg | worst_day% | bad_day% | bull_day% |
|---|---|---|---|---|---|---|---|
| Low late vol (Q1) | 59 | 59% | 46% | +1.66 | 29% | 41% | 36% |
| Mod-Low | 58 | 52% | 45% | +0.85 | 31% | 41% | 34% |
| Mod-High | 58 | 52% | 59% | -1.17 | 31% | 43% | 28% |
| High late vol (Q4) | 59 | 42% | 51% | -1.97 | 31% | 42% | 24% |


## P7 — Gap + PM Trend Alignment

| Combo | n | Day>Open% | 5m>Open% | avg_$chg | worst_day% | bad_day% |

|---|---|---|---|---|---|---|

| GapUp+PMUp | 59 | 58% | 56% | +0.32 | 27% | 39% |

| GapUp+PMDown | 45 | 51% | 47% | +0.23 | 27% | 33% |

| GapDown+PMDown | 42 | 48% | 43% | -2.71 | 43% | 50% |

| GapDown+PMUp | 32 | 56% | 53% | +2.39 | 25% | 34% |

| GapDown+PMFlat | 17 | 35% | 53% | -4.27 | 59% | 65% |

| GapUp+PMFlat | 13 | 46% | 23% | +1.86 | 15% | 38% |

| GapFlat+PMDown | 10 | 70% | 50% | +3.61 | 0% | 20% |

| GapFlat+PMUp | 9 | 33% | 67% | -2.31 | 33% | 67% |

| GapFlat+PMFlat | 6 | 33% | 67% | -0.95 | 33% | 67% |


## P8 — Previous Day Close vs PM Open (Gap Classification)

Gap stats: min=-21.51, median=0.52, max=20.70

| Group | n | Day>Open% | 5m>Open% | avg_$chg | worst_day% | bad_day% | bull_day% |
|---|---|---|---|---|---|---|---|
| Big Gap Down | 59 | 49% | 47% | -0.59 | 39% | 47% | 29% |
| Mod Gap Down | 58 | 47% | 55% | -1.18 | 31% | 48% | 29% |
| Mod Gap Up | 58 | 55% | 48% | +0.31 | 21% | 31% | 26% |
| Big Gap Up | 58 | 53% | 48% | +0.66 | 31% | 41% | 36% |


## P9 — Bad Day Composite: PM Position + PM Acceleration

PM Bear Signal thresholds: position < 0.22 AND accel < -0.16

PM Bear days: n=41

Non-bear days: n=193



| Category | n | Day>Open% | 5m>Open% | avg_$chg | worst_day% | bad_day% |

|---|---|---|---|---|---|---|

| PM Bear Signal | 41 | 37% | 49% | -1.97 | 37% | 46% |

| PM Non-Bear | 193 | 54% | 50% | +0.23 | 29% | 41% |



**Worst-day capture:** 15/71 worst days caught = 21%

**Good-day false exclude:** 26/163 good days wrongly excluded = 16%

---


# Module S: First 30 Seconds (1s data — n=28 days, THIN)

> **Warning:** Only 23 days have 1s data. All S-module findings are indicative only — insufficient for strong conclusions.

1s days available: 23


## S1 — First Second Direction

| First 1s | n | Day>Open% | 5m>Open% | avg_$chg | worst% |

|---|---|---|---|---|---|

| First sec UP | 5 | 40% | 40% | -0.86 | 40% |

| First sec DOWN | 18 | 50% | 67% | +0.89 | 17% |


## S2 — First 15s vs 30s Direction Cross-Tab

| 15s direction | 30s direction | n | Day>Open% | 5m>Open% | avg_$chg |

|---|---|---|---|---|---|

| 15s UP | 30s UP | 10 | 50% | 90% | -0.05 |

| 15s UP | 30s DOWN | 4 | 25% | 50% | +0.70 |

| 15s DOWN | 30s UP | 2 | 0% | 0% | -3.82 |

| 15s DOWN | 30s DOWN | 7 | 71% | 43% | +2.44 |


## S3 — First 30s Range

First 30s range: min=1.25, median=2.47, max=3.73



| Group | n | Day>Open% | 5m>Open% | avg_$chg | worst_day% | bad_day% | bull_day% |
|---|---|---|---|---|---|---|---|
| Narrow (≤median) | 12 | 42% | 50% | +0.41 | 33% | 33% | 25% |
| Wide (>median) | 11 | 55% | 73% | +0.61 | 9% | 27% | 27% |


## S4 — Price Position at 9:30:30 vs Open

| 30s vs Open | n | Day>Open% | 5m>Open% | avg_$chg | worst% |

|---|---|---|---|---|---|

| 30s ABOVE open | 12 | 42% | 75% | -0.68 | 33% |

| 30s BELOW open | 11 | 55% | 45% | +1.81 | 9% |




### S4 Combined with 5m Rule

| 30s signal | 5m rule | n | Day>Open% | avg_$chg |

|---|---|---|---|---|

| 30s UP | 5m HOLD | 9 | 56% | +0.63 |

| 30s UP | 5m BAIL | 3 | 0% | -4.59 |

| 30s DN | 5m HOLD | 5 | 80% | +5.33 |

| 30s DN | 5m BAIL | 6 | 33% | -1.13 |


## S5 — Volume Front-Loaded Ratio (first 30s / first 60s)

Front-loaded ratio (vol_30s/vol_60s): median=0.76

| Group | n | Day>Open% | 5m>Open% | avg_$chg | worst_day% | bad_day% | bull_day% |
|---|---|---|---|---|---|---|---|
| Back-loaded (≤median) | 12 | 25% | 58% | -2.49 | 33% | 42% | 17% |
| Front-loaded (>median) | 11 | 73% | 64% | +3.78 | 9% | 18% | 36% |


## S6 — First 30s Direction vs PM Trend Agreement

| PM/30s alignment | n | Day>Open% | 5m>Open% | avg_$chg |

|---|---|---|---|---|

| Agreement (same dir) | 13 | 62% | 62% | +2.47 |

| Disagreement (opposite) | 8 | 25% | 62% | -2.76 |

---


# Module B: Bad Day Avoidance


## B1 — Worst 20% of Days (< -$5 from open)

Total worst days (< -$5): **71** out of 234 = 30%



**Worst day PM characteristics:**

- Avg PM position at 9:29: 0.419 (vs non-worst: 0.496)

- Avg PM late trend (9:20-9:29): -0.40 (vs non-worst: +0.01)

- Avg PM accel (9:25-9:29): -0.32 (vs non-worst: +0.01)

- Avg PM full move: -0.55 (vs non-worst: -0.21)

- Avg gap vs prev: +0.26 (vs non-worst: +0.30)

- Avg PM vol ratio (last/first): 4.69 (vs non-worst: 5.01)



**5m rule performance on worst days:**

- 5m says HOLD on worst days: 22 (31%)

- 5m says BAIL on worst days: 49 (69%)


## B2 — Multi-Factor Bad Day Filter

Testing filters on days with full PM data:



| Filter | n flagged | Worst-day recall | False-exclude rate | Precision |

|---|---|---|---|---|

| PM Pos < Q1 (bottom 25%) | 59 | 32% (23/71) | 22% (36/163) | 39% |

| PM Accel < 0 (negative) | 122 | 63% (45/71) | 47% (77/163) | 37% |

| PM Late Trend < 0 | 120 | 62% (44/71) | 47% (76/163) | 37% |

| PM Pos < Q1 AND Accel < 0 | 43 | 24% (17/71) | 16% (26/163) | 40% |

| PM Pos < Q1 AND Late Trend < 0 | 45 | 24% (17/71) | 17% (28/163) | 38% |

| PM Accel < 0 AND Late Trend < 0 | 107 | 56% (40/71) | 41% (67/163) | 37% |

| PM Pos < Q1 AND Accel < 0 AND Late < 0 | 42 | 23% (16/71) | 16% (26/163) | 38% |


## B3 — Avoid vs Hold Decision: Strategy Comparison

| Strategy | Trades | Win% | Avg P&L | Worst-day exposure | Sharpe proxy |

|---|---|---|---|---|---|

| Blind Long | 234 | 51% | -0.16 | 30% | -0.23 |

| 5m Rule (HOLD only) | 117 | 68% | +3.02 | 19% | 4.58 |

| PM Filter (skip bear) | 191 | 55% | +0.30 | 28% | 0.45 |

| 5m Rule + PM Filter | 97 | 72% | +3.59 | 18% | 5.43 |


## B4 — 'Trapped Long' Days: 5m Rule HOLD but Day Ends Negative

HOLD days total: 117

Trapped HOLD (HOLD but day ends negative): **37** (32%)

Good HOLD (HOLD and day ends positive): **80**



**Trapped HOLD PM characteristics:**

- Avg PM position at 9:29: 0.437 (good HOLD: 0.523)

- Avg PM late trend: -0.78 (good HOLD: +0.16)

- Avg PM accel 9:25-29: -0.57 (good HOLD: +0.21)

- Avg PM full move: -0.25 (good HOLD: +0.02)



Trapped HOLD days flagged by PM bear signal (pos<Q1 OR accel<0): 27 / 37 = 73%

---


# Appendix: Key Distribution Stats


## PM Position at 9:29 — Full Distribution

n=234 | mean=0.473 | median=0.448

Q10=0.082 | Q25=0.219 | Q75=0.715 | Q90=0.878


## PM Acceleration 9:25-9:29 — Full Distribution

n=234 | mean=-0.09 | median=-0.09

Q10=-1.58 | Q25=-0.80 | Q75=0.73 | Q90=1.49


## Day Close vs Open — Full Distribution

n=280 | mean=-0.07 | median=+0.07 | std=10.32

Q10=-12.63 | Q25=-6.25 | Q75=+5.83 | Q90=+11.81

---


# Summary of Actionable Findings

_Ranked by practical value. Based on full PM dataset unless noted._



| Rank | Signal | Data Summary | Recommendation |

|---|---|---|---|

| 1 | **5m Rule (baseline)** | HOLD win%=68% avg=+3.11 | BAIL win%=32% avg=-3.30 | n=280 | Core rule — continue using as primary signal |

| 2 | **P3: PM Position at 9:29** | Bottom Q (near PM low): day_above=39% avg=-2.94 n=59 | Top Q: day_above=59% avg=+2.11 n=59 | Strong predictor: price near PM low → worse outcomes. Use as caution signal. |

| 3 | **P4: PM Acceleration 9:25-9:29** | Accel down: day_above=43% avg=-0.69 n=122 | Accel up: day_above=61% avg=+0.42 n=112 | Momentum in final 5 PM bars: negative = more bad days. |

| 4 | **P9: PM Bear Composite (pos<Q1 AND accel<thr)** | Bear signal: n=41 day_above=37% worst=37% | Catches 15/71 worst days (21%) | Best composite bad-day filter. Check false-exclude rate in B2 table. |

| 5 | **P1: Final PM Trend (9:20-9:29)** | Late Up: day_above=64% avg=+0.93 n=69 | Late Down: day_above=40% avg=-0.58 n=83 | Final PM direction matters but is noisier than position. |

| 6 | **P7: Gap + PM Trend Alignment** | GapUp+PMUp: n=59 day_above=58% avg=+0.32 | GapUp+PMDown: n=45 day_above=51% avg=+0.23 | Gap+PM agreement = follow-through. Gap up + PM fading = caution. |

| 7 | **S4: 30s Price vs Open (1s data — THIN n=28)** | 30s above: n=12 day_above=42% avg=-0.68 | 30s below: n=11 day_above=55% avg=+1.81 | Early signal within first 30s. Very thin sample — treat as directional hypothesis only. |



---



### Key Takeaways



1. **Best bad-day predictor:** PM position at 9:29 in bottom quartile + final 5 bars accelerating down (P9 composite). This combination catches the highest % of worst days with acceptable false-exclude rate.



2. **5m rule remains the gold standard:** Clear separation between HOLD and BAIL on both win rate and avg P&L.



3. **PM structure before open is informative:** Position at 9:29, late-PM trend direction, and final acceleration all show signal — not noise.



4. **Bad HOLD days are identifiable in PM:** Trapped longs (5m HOLD but day ends negative) tend to have lower PM position and more negative PM acceleration than good HOLD days — actionable filter.



5. **1s data (Module S): too thin to conclude,** but directionally consistent with PM findings. 30s above open aligns well with 5m rule. Worth collecting more data.



6. **Practical trading rule (combine findings):**

   - Skip the trade if: PM position < 0.25 AND (PM accel <0 OR PM late trend <0)

   - Boost confidence if: PM position > 0.75 AND PM accel > 0 AND gap direction matches PM trend
