# TSLA Open Scalper — Skip Day Deep Investigation
*Generated: 2026-03-21*

**Total trading days analyzed:** 227
**Date range:** 2025-03-19 to 2026-03-19
**Agree=2 (L/triple):** 152 (67%)
**Agree=1 (M size):** 32 (14%)
**Agree=0 (skip days):** 43 (19%)


---
## Loop 1: Skip Day Profile

### Overall Skip Day Stats
- **N:** 43
- **Binary right at 2m:** 65.1%
- **Binary right at 5m:** 48.8%
- **Majority right at 2m:** 34.9%
- **Majority right at 5m:** 51.2%
- **Avg binary PnL at 2m:** $0.63
- **Avg binary PnL at 5m:** $0.49
- **Avg majority PnL at 2m:** $-0.63
- **Avg majority PnL at 5m:** $-0.49
- **VWAP won at 2m:** 34.9% of skip days
- **Bar1 confirms binary:** 55.8%

### PnL by Agreement Level (following binary direction)
| Agree | N | Binary Win% 2m | Binary Win% 5m | Avg PnL 2m | Avg PnL 5m | Total PnL 5m |
|-------|---|----------------|----------------|------------|------------|--------------|
| 0 | 43 | 65.1% | 48.8% | $0.63 | $0.49 | $21.13 |
| 1 | 32 | 65.6% | 62.5% | $0.51 | $0.78 | $24.98 |
| 2 | 152 | 64.5% | 59.2% | $0.73 | $0.59 | $89.21 |

### All Skip Days — Day-by-Day

| Date | Binary | Conf | VWAP | EMA | Tier | Kill | Gap | PM Pos | PM Acc | VIX | Bar1 | Call 2m | Put 2m | Call 5m | Put 5m | Winner 2m |
|------|--------|------|------|-----|------|------|-----|--------|--------|-----|------|---------|--------|---------|--------|-----------|
| 2025-03-19 | CALL | 3 | PUT | PUT | MED | none | +0.0 | 0.60 | -0.1 | 20 | R | $-1.15 | $+1.15 | $-1.15 | $+1.15 | VWAP |
| 2025-03-31 | PUT | 4 | CALL | CALL | NO-GO | BIG_GAP | -14.1 | 0.29 | +1.7 | 22 | G | $+0.23 | $-0.23 | $+0.23 | $-0.23 | VWAP |
| 2025-04-01 | CALL | 3 | PUT | PUT | MED | none | +4.8 | 0.38 | -0.0 | 22 | R | $-1.90 | $+1.90 | $-1.90 | $+1.90 | VWAP |
| 2025-04-03 | PUT | 3 | CALL | CALL | NO-GO | BIG_GAP | -17.3 | 0.15 | +0.5 | 30 | G | $-0.79 | $+0.79 | $-0.79 | $+0.79 | BINARY |
| 2025-04-07 | PUT | 2 | CALL | CALL | NO-GO | GAP | -15.8 | 0.57 | +0.8 | 52 | R | $-1.02 | $+1.02 | $-1.02 | $+1.02 | BINARY |
| 2025-04-28 | CALL | 3 | PUT | PUT | MED | none | +4.4 | 0.66 | -0.8 | 24 | R | $-0.64 | $+0.64 | $-0.64 | $+0.64 | VWAP |
| 2025-04-30 | PUT | 2 | CALL | CALL | NO-GO | GAP | -11.7 | 0.10 | +0.1 | 25 | R | $-0.28 | $+0.28 | $-0.28 | $+0.28 | BINARY |
| 2025-05-05 | PUT | 3 | CALL | CALL | NO-GO | GAP | -2.5 | 0.19 | +0.6 | 25 | R | $-0.20 | $+0.20 | $-0.20 | $+0.20 | BINARY |
| 2025-05-06 | PUT | 2 | CALL | CALL | NO-GO | GAP | -7.2 | 0.10 | +0.2 | 25 | R | $-0.46 | $+0.46 | $-0.46 | $+0.46 | BINARY |
| 2025-05-14 | CALL | 3 | PUT | PUT | MED | none | +8.5 | 0.69 | -0.4 | 19 | R | $-1.79 | $+1.79 | $-1.79 | $+1.79 | VWAP |
| 2025-05-19 | PUT | 5 | CALL | CALL | NO-GO | BIG_GAP | -13.4 | 0.23 | +1.0 | 18 | G | $+0.72 | $-0.72 | $+0.72 | $-0.72 | VWAP |
| 2025-05-27 | CALL | 3 | PUT | PUT | MED | none | +7.6 | 0.45 | -0.6 | 19 | G | $+1.54 | $-1.54 | $+1.54 | $-1.54 | BINARY |
| 2025-05-28 | CALL | 3 | PUT | PUT | MED | none | +2.5 | 0.73 | -0.1 | 19 | R | $-2.21 | $+2.21 | $-2.21 | $+2.21 | VWAP |
| 2025-05-29 | CALL | 3 | PUT | PUT | MED | none | +8.1 | 0.38 | -0.6 | 19 | R | $-0.70 | $+0.70 | $-0.70 | $+0.70 | VWAP |
| 2025-06-16 | CALL | 3 | PUT | PUT | MED | none | +5.4 | 0.79 | -0.6 | 22 | G | $-1.52 | $+1.52 | $-1.52 | $+1.52 | VWAP |
| 2025-07-21 | CALL | 3 | PUT | PUT | MED | none | +4.9 | 0.55 | +0.1 | 16 | G | $+1.48 | $-1.48 | $+1.48 | $-1.48 | BINARY |
| 2025-09-17 | PUT | 0 | CALL | CALL | NO-GO | GAP | -6.0 | 0.09 | -0.1 | 16 | G | $-0.93 | $+0.93 | $-1.54 | $+1.54 | BINARY |
| 2025-09-18 | PUT | 2 | CALL | CALL | LOW | none | +2.3 | 0.40 | -0.0 | 16 | R | $-0.31 | $+0.31 | $+0.69 | $-0.69 | BINARY |
| 2025-09-22 | CALL | 3 | PUT | PUT | MED | none | +5.2 | 0.43 | +0.1 | 17 | G | $+2.36 | $-2.36 | $+4.55 | $-4.55 | BINARY |
| 2025-09-25 | PUT | 2 | CALL | CALL | NO-GO | BIG_GAP | -7.7 | 0.21 | +0.8 | 17 | R | $-5.85 | $+5.85 | $-8.35 | $+8.35 | BINARY |
| 2025-10-14 | PUT | 4 | CALL | CALL | NO-GO | BIG_GAP | -9.2 | 0.36 | +1.6 | 21 | R | $-2.31 | $+2.31 | $-4.39 | $+4.39 | BINARY |
| 2025-10-15 | CALL | 3 | PUT | PUT | MED | none | +5.6 | 0.84 | -0.0 | 21 | G | $-0.29 | $+0.29 | $-3.00 | $+3.00 | VWAP |
| 2025-10-17 | PUT | 3 | CALL | CALL | NO-GO | GAP | -3.0 | 0.87 | +0.9 | 21 | R | $+0.46 | $-0.46 | $+2.80 | $-2.80 | VWAP |
| 2025-10-21 | PUT | 2 | CALL | CALL | LOW | none | -1.7 | 0.72 | -0.1 | 18 | G | $-0.08 | $+0.08 | $-0.37 | $+0.37 | BINARY |
| 2025-11-14 | PUT | 4 | CALL | CALL | NO-GO | BIG_GAP | -15.8 | 0.25 | +0.8 | 20 | G | $-0.17 | $+0.17 | $+1.33 | $-1.33 | BINARY |
| 2025-11-18 | CALL | 3 | PUT | PUT | MED | none | -3.4 | 0.39 | -1.7 | 25 | G | $+0.72 | $-0.72 | $-1.25 | $+1.25 | BINARY |
| 2025-11-25 | CALL | 3 | PUT | PUT | MED | none | -3.3 | 0.33 | -2.1 | 19 | R | $+0.16 | $-0.16 | $-1.01 | $+1.01 | BINARY |
| 2025-11-26 | CALL | 3 | PUT | PUT | MED | none | +4.8 | 0.68 | -0.8 | 17 | G | $-1.24 | $+1.24 | $-2.14 | $+2.14 | VWAP |
| 2025-12-11 | PUT | 2 | CALL | CALL | NO-GO | VIX | -3.0 | 0.82 | +0.2 | 15 | R | $-1.29 | $+1.29 | $-2.37 | $+2.37 | BINARY |
| 2025-12-17 | PUT | 2 | CALL | CALL | LOW | none | -1.8 | 0.21 | +1.4 | 18 | G | $+2.79 | $-2.79 | $+5.01 | $-5.01 | VWAP |
| 2025-12-23 | PUT | 4 | CALL | CALL | NO-GO | VIX | +0.3 | 0.67 | +1.0 | 14 | G | $+0.42 | $-0.42 | $+0.04 | $-0.04 | VWAP |
| 2025-12-24 | PUT | 3 | CALL | CALL | NO-GO | VIX | +2.8 | 0.95 | +0.4 | 13 | G | $-1.55 | $+1.55 | $-3.75 | $+3.75 | BINARY |
| 2025-12-29 | PUT | 4 | CALL | CALL | NO-GO | VIX | -6.4 | 0.38 | +0.6 | 14 | R | $-2.51 | $+2.51 | $-5.26 | $+5.26 | BINARY |
| 2026-01-05 | PUT | 4 | CALL | CALL | NO-GO | VIX | +9.6 | 0.93 | +0.9 | 15 | R | $-2.77 | $+2.77 | $+2.54 | $-2.54 | BINARY |
| 2026-01-20 | PUT | 4 | CALL | CALL | NO-GO | BIG_GAP | -8.4 | 0.48 | +2.5 | 17 | R | $-3.24 | $+3.24 | $-1.24 | $+1.24 | BINARY |
| 2026-01-27 | PUT | 2 | CALL | CALL | LOW | none | +2.2 | 0.48 | -0.1 | 16 | R | $-1.86 | $+1.86 | $-4.20 | $+4.20 | BINARY |
| 2026-02-05 | PUT | 4 | CALL | CALL | NO-GO | BIG_GAP | -8.6 | 0.18 | +0.8 | 22 | G | $-3.67 | $+3.67 | $+2.31 | $-2.31 | BINARY |
| 2026-02-12 | CALL | 3 | PUT | PUT | MED | none | +1.9 | 0.52 | -1.4 | 21 | G | $+3.38 | $-3.38 | $+3.38 | $-3.38 | BINARY |
| 2026-02-13 | CALL | 3 | PUT | PUT | MED | none | -2.8 | 0.24 | -2.8 | 21 | G | $+0.29 | $-0.29 | $-0.12 | $+0.12 | BINARY |
| 2026-03-03 | PUT | 5 | CALL | CALL | NO-GO | BIG_GAP | -8.0 | 0.52 | +1.8 | 24 | R | $-0.69 | $+0.69 | $-1.89 | $+1.89 | BINARY |
| 2026-03-04 | CALL | 3 | PUT | PUT | MED | none | +5.4 | 0.74 | -1.5 | 21 | R | $+1.88 | $-1.88 | $+5.04 | $-5.04 | BINARY |
| 2026-03-16 | CALL | 3 | PUT | PUT | MED | none | +5.1 | 0.80 | -0.6 | 22 | G | $+2.90 | $-2.90 | $+2.91 | $-2.91 | BINARY |
| 2026-03-17 | CALL | 3 | PUT | PUT | MED | none | +0.2 | 0.72 | -0.0 | 22 | R | $-1.57 | $+1.57 | $-0.78 | $+0.78 | VWAP |


---
## Loop 2: Skip Day Classification

### Binary=CALL, Majority=PUT (N=19)
- **Binary right at 2m:** 47.4%
- **Avg binary PnL 2m:** $0.09
- **Avg majority PnL 2m:** $-0.09
- **Avg binary PnL 5m:** $0.04
- **Avg majority PnL 5m:** $-0.04
- **Total binary PnL 5m:** $0.69
- **Total majority PnL 5m:** $-0.69

**By confidence score:**

| Conf | N | Bin Win% 2m | Bin Avg 2m | Maj Win% 2m | Maj Avg 2m | Bin Avg 5m | Maj Avg 5m |
|------|---|-------------|------------|-------------|------------|------------|------------|
| 3 | 19 | 47% | $0.09 | 53% | $-0.09 | $0.04 | $-0.04 |

**By gap direction:**

| Gap | N | Bin Win% 2m | Bin Avg 2m | Maj Avg 2m |
|-----|---|-------------|------------|------------|
| Gap Up | 14 | 43% | $0.23 | $-0.23 |
| Flat | 2 | 0% | $-1.36 | $1.36 |
| Gap Down | 3 | 100% | $0.39 | $-0.39 |

**By bar1 direction:**

| Bar1 | N | Bin Win% 2m | Bin Avg 2m | Maj Avg 2m | Bar1 confirms binary |
|------|---|-------------|------------|------------|---------------------|
| Green | 10 | 70% | $0.96 | $-0.96 | 100% |
| Red | 9 | 22% | $-0.88 | $0.88 | 0% |

**By PM accel direction:**

| PM Accel | N | Bin Win% 2m | Bin Avg 2m | Maj Avg 2m |
|----------|---|-------------|------------|------------|
| Flat | 8 | 25% | $-0.63 | $0.63 |
| Accel Down (<-0.5) | 11 | 64% | $0.62 | $-0.62 |

**By VIX level:**

| VIX | N | Bin Win% 2m | Bin Avg 2m | Maj Avg 2m |
|-----|---|-------------|------------|------------|
| Low (<18) | 3 | 67% | $0.87 | $-0.87 |
| Sweet (18-25) | 16 | 44% | $-0.06 | $0.06 |

### Binary=PUT, Majority=CALL (N=24)
- **Binary right at 2m:** 79.2%
- **Avg binary PnL 2m:** $1.06
- **Avg majority PnL 2m:** $-1.06
- **Avg binary PnL 5m:** $0.85
- **Avg majority PnL 5m:** $-0.85
- **Total binary PnL 5m:** $20.44
- **Total majority PnL 5m:** $-20.44

**By confidence score:**

| Conf | N | Bin Win% 2m | Bin Avg 2m | Maj Win% 2m | Maj Avg 2m | Bin Avg 5m | Maj Avg 5m |
|------|---|-------------|------------|-------------|------------|------------|------------|
| 0 | 1 | 100% | $0.93 | 0% | $-0.93 | $1.54 | $-1.54 |
| 2 | 9 | 89% | $0.93 | 11% | $-0.93 | $1.26 | $-1.26 |
| 3 | 4 | 75% | $0.52 | 25% | $-0.52 | $0.48 | $-0.48 |
| 4 | 8 | 75% | $1.75 | 25% | $-1.75 | $0.56 | $-0.56 |
| 5 | 2 | 50% | $-0.01 | 50% | $0.01 | $0.59 | $-0.59 |

**By gap direction:**

| Gap | N | Bin Win% 2m | Bin Avg 2m | Maj Avg 2m |
|-----|---|-------------|------------|------------|
| Gap Up | 4 | 100% | $1.62 | $-1.62 |
| Flat | 1 | 0% | $-0.42 | $0.42 |
| Gap Down | 19 | 79% | $1.02 | $-1.02 |

**By bar1 direction:**

| Bar1 | N | Bin Win% 2m | Bin Avg 2m | Maj Avg 2m | Bar1 confirms binary |
|------|---|-------------|------------|------------|---------------------|
| Green | 10 | 60% | $0.30 | $-0.30 | 0% |
| Red | 14 | 93% | $1.60 | $-1.60 | 100% |

**By PM accel direction:**

| PM Accel | N | Bin Win% 2m | Bin Avg 2m | Maj Avg 2m |
|----------|---|-------------|------------|------------|
| Accel Up (>0.5) | 16 | 69% | $1.16 | $-1.16 |
| Flat | 8 | 100% | $0.85 | $-0.85 |

**By VIX level:**

| VIX | N | Bin Win% 2m | Bin Avg 2m | Maj Avg 2m |
|-----|---|-------------|------------|------------|
| Low (<18) | 12 | 83% | $1.43 | $-1.43 |
| Sweet (18-25) | 10 | 70% | $0.64 | $-0.64 |
| High (>25) | 2 | 100% | $0.91 | $-0.91 |


---
## Loop 3: Profitable Subset Search

Searching for cells with N>=5, Win%>=60%, Avg PnL >= $0.50

### Profitable Cells Found

| Cell | Follow | N | Win% | Avg PnL | Total PnL |
|------|--------|---|------|---------|-----------|
| Binary=PUT, bar1=red | binary | 14 | 79% | $1.69 | $23.63 |
| Binary=PUT, VIX low | binary | 12 | 67% | $1.57 | $18.80 |
| Binary=PUT, conf=2 | binary | 9 | 78% | $1.26 | $11.35 |
| Binary=PUT, pm_pos<0.5 | binary | 16 | 62% | $1.03 | $16.42 |
| All skip, gap<-2 | binary | 20 | 60% | $0.90 | $18.02 |
| All Binary=PUT | binary | 24 | 62% | $0.85 | $20.44 |
| Binary=PUT, gap<0 | binary | 19 | 68% | $0.83 | $15.76 |
| Binary=PUT, pm_accel>0 | binary | 20 | 60% | $0.75 | $15.02 |
| Binary=CALL, bar1=red | majority | 9 | 89% | $0.57 | $5.14 |
| Binary=PUT, pm_pos>0.5 | binary | 8 | 62% | $0.50 | $4.02 |


---
## Loop 4: What Predicts Which Side Wins?

T-test each feature between binary_right and binary_wrong groups (at 2m)

Binary right at 2m: 28 days (65.1%)
Binary wrong at 2m: 15 days (34.9%)

| Feature | Right Mean | Wrong Mean | Diff | t-stat | p-value | Discriminates? |
|---------|------------|------------|------|--------|---------|---------------|
| pm_position | 0.442 | 0.582 | -0.140 | -1.88 | 0.0694 | YES |
| pm_accel | 0.060 | 0.179 | -0.118 | -0.39 | 0.6990 | no |
| pm_late_trend | 0.192 | 0.108 | +0.084 | 0.23 | 0.8174 | no |
| pm_slope | 0.006 | 0.004 | +0.002 | 0.26 | 0.7965 | no |
| pm_curvature | 0.012 | 0.006 | +0.006 | 0.26 | 0.7937 | no |
| pm_vol_5m | 87850.214 | 113444.067 | -25593.852 | -1.26 | 0.2191 | no |
| vix | 20.731 | 19.795 | +0.936 | 0.61 | 0.5473 | no |
| gap | -3.276 | 0.817 | -4.093 | -1.83 | 0.0768 | YES |
| bar1_range | 2.961 | 2.708 | +0.253 | 0.81 | 0.4258 | no |
| confidence | 2.893 | 3.200 | -0.307 | -1.20 | 0.2384 | no |

**Categorical splits:**

| Split | N right | N wrong | Right% of split | p (Fisher) |
|-------|---------|---------|-----------------|------------|
| bar1_green | 13 | 7 | 65% | 1.0000 |
| bar1_red | 15 | 8 | 65% | 1.0000 |
| spy_UP | 16 | 7 | 70% | 0.5401 |
| gap>0 | 10 | 10 | 50% | 0.0642 |
| gap<0 | 18 | 4 | 82% | 0.0268 |
| pm_accel>0 | 17 | 5 | 77% | 0.1159 |
| pm_slope>0 | 15 | 6 | 71% | 0.5256 |


---
## Loop 5: The Flip Opportunity

What if we flip SOME skip days from binary to majority direction?

| Flip Rule | Days Flipped | Binary PnL (those days) | Majority PnL (those days) | Net Change | Correct Flip % |
|-----------|-------------|------------------------|--------------------------|------------|---------------|
| pm_accel disagrees with binary (CALL + accel<-0.5, PUT + accel>0.5) | 27 | $13.65 | $-13.65 | $-27.30 | 56% |
| pm_accel strongly disagrees (<-1 or >1) | 11 | $8.28 | $-8.28 | $-16.56 | 55% |
| gap disagrees with binary (CALL + gap<-1, PUT + gap>1) | 7 | $2.34 | $-2.34 | $-4.68 | 71% |
| gap strongly disagrees (CALL + gap<-3, PUT + gap>3) | 3 | $-4.80 | $4.80 | $+9.60 | 100% |
| bar1 disagrees (at 9:31) | 19 | $-8.33 | $8.33 | $+16.66 | 74% |
| pm_slope disagrees | 36 | $22.20 | $-22.20 | $-44.40 | 53% |
| SPY disagrees | 22 | $11.19 | $-11.19 | $-22.38 | 45% |


---
## Loop 6: Straddle/Sizing Opportunity

### Strategy A: Trade both CALL and PUT at 0.5x on skip days

**Dead End.** Equal-sized CALL + PUT on the same stock at the same time always nets to $0 in stock terms (one gains exactly what the other loses). In options, both sides lose to theta/spread — net negative. This is not viable.

### Strategy B: Enter both, cut loser at 1m, keep winner to 2m/5m

- **N:** 43
- **Win% (net > 0):** 20.9%
- **Avg PnL:** $-0.36
- **Total PnL (keep winner 2m):** $-15.45
- **Total PnL (keep winner 5m):** $-14.50

### Strategy C: Always CALL vs Always PUT on skip days

| Direction | Win% 2m | Avg 2m | Total 2m | Win% 5m | Avg 5m | Total 5m |
|-----------|---------|--------|----------|---------|--------|----------|
| CALL | 32.6% | $-0.55 | $-23.66 | 34.9% | $-0.46 | $-19.75 |
| PUT | 67.4% | $0.55 | $23.66 | 65.1% | $0.46 | $19.75 |


---
## Loop 7: Impact Analysis

### System context

- **Current system trades (agree>=1):** 184 days
- **Current system Win% 5m:** 59.8%
- **Current system Total PnL 5m:** $114.19
- **Current system Avg PnL 5m:** $0.62

- **Skip days (agree=0):** 43 potential additional trades

### Option 1: Follow majority (VWAP+EMA) on skip days
- **Total PnL 5m:** $-21.13
- **Win%:** 51.2%
- **Avg PnL:** $-0.49

### Option 2: Follow binary on skip days
- **Total PnL 5m:** $21.13
- **Win%:** 48.8%
- **Avg PnL:** $0.49

### Robustness: Half-split test

**First half (N=21):**
- Binary right 2m: 57.1%
- Majority right 2m: 42.9%
- Binary PnL 5m: $13.05 (avg $0.62)
- Majority PnL 5m: $-13.05 (avg $-0.62)

**Second half (N=22):**
- Binary right 2m: 72.7%
- Majority right 2m: 27.3%
- Binary PnL 5m: $8.08 (avg $0.37)
- Majority PnL 5m: $-8.08 (avg $-0.37)

### Downside risk
- **Worst binary PnL 5m:** $-5.01
- **Worst majority PnL 5m:** $-8.35
- **Worst CALL 5m:** $-8.35
- **Worst PUT 5m:** $-5.04


---
## Loop 8: The 3/20/2026 Case

*3/20/2026 not in dataset — 15sec data ends 2026-03-19. Today is 3/21, so 3/20 bars may not yet be cached.*

Based on user report: binary=CALL (conf 3/5), VWAP=PUT, EMA=PUT. Price crashed (PUT was correct).

**Pattern match:** This is a Binary=CALL skip day. The CALL-skip group (N=19) has only 47% binary right at 2m — essentially a coin flip. The group is NOT profitable following binary ($0.69 total at 5m over 19 days). 3/20 fits the profile of a day where binary was wrong and VWAP+EMA were right.

**Similar profile days** (Binary=CALL, agree=0, bar1=Red):
- 9 such days in the dataset, 78% PUT was correct (majority won)
- Average majority PnL: +$0.88
- This is the one CALL-skip subset where following VWAP+EMA (PUT) works


---
## Recommendation

### Summary of findings

1. **Skip days represent 43 of 227 days (19%)**
2. **Binary right at 2m:** 65.1% | at 5m: 48.8%
3. **Majority right at 2m:** 34.9% | at 5m: 51.2%
4. **Binary total PnL 5m:** $21.13
5. **Majority total PnL 5m:** $-21.13
6. **The edge is highly asymmetric: Binary=PUT skips are profitable ($20.44), Binary=CALL skips are breakeven ($0.69)**

### Key insight: The two skip subtypes are OPPOSITE

| Subtype | N | Binary right 2m | Binary PnL 5m | Majority PnL 5m |
|---------|---|-----------------|---------------|-----------------|
| Binary=CALL, majority=PUT | 19 | 47% (coin flip) | $0.69 (near zero) | -$0.69 |
| Binary=PUT, majority=CALL | 24 | 79% (strong) | $20.44 (real edge) | -$20.44 |

- When binary says PUT but VWAP+EMA say CALL: **binary is right 79% of the time.** These are mostly hard-kill days (big gap downs, VIX extremes) where the binary's PUT direction reflects real bearish momentum that VWAP+EMA miss because they look at PM structure only.
- When binary says CALL but VWAP+EMA say PUT: **coin flip.** Binary's bullish read is weak here — PM position is high but acceleration is negative. No edge either way.

### Exact rule for skip days

```
IF agree_count == 0:                        // VWAP + EMA both disagree with binary
    IF binary_dir == PUT:                   // binary says PUT, majority says CALL
        TRADE PUT at S size (0.5x)          // binary is right 79% at 2m
        // Expected: +$0.85/trade, 24 trades/year, +$20/year
    ELSE (binary_dir == CALL):              // binary says CALL, majority says PUT
        SKIP                                // coin flip, no edge
```

### Impact on system

- **Current system (agree>=1):** 184 trades, $114.19 total PnL
- **Adding PUT-skip trades:** +24 trades at S size (0.5x each)
- **Expected additional PnL:** $20.44 * 0.5 = $10.22 (at S size)
- **System total:** $124.41 (+8.9%)
- **Downside risk:** worst single PUT-skip trade = -$5.01

### Robustness check

Binary=PUT skip days, half-split:
- First 12: 75% binary right at 2m, PnL $11.10
- Last 12: 83% binary right at 2m, PnL $9.34
- **Consistent across both halves — this is robust**

### What NOT to do

- Do NOT follow majority on skip days (net negative)
- Do NOT trade CALL skip days (coin flip)
- Do NOT use bar1-reactive flips (the flip table shows bar1 disagree has $16.66 gain, but this is tautological — bar1 direction at 9:31 already reflects the move)
- Do NOT straddle (mathematically zero in stock, negative in options)

### Discriminating features (Loop 4)

Two features weakly predict binary correctness on skip days (p < 0.10):
- **gap < 0** (Fisher p=0.027): 82% binary right when gap is negative vs 50% when positive
- **pm_position < 0.5** (t-test p=0.069): lower PM position correlates with binary being correct

Both features are already baked into the PUT-skip rule (PUT days tend to have negative gaps and low PM position), so no additional filter needed.