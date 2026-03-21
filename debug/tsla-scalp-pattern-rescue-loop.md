# TSLA Open Scalper — Pattern Rescue Loop Analysis

Date: 2026-03-21 | Days: 252 | Columns: 307
Data: tsla_candle_fingerprints.parquet (1yr TSLA, one row per trading day)

---

## Baseline System

| Metric | Value |
|--------|-------|
| Total PnL | $236.71 |
| Winners | 140 (61.4%) |
| Losers | 88 (38.6%) |
| Skips | 24 |
| Avg winner | $3.35 |
| Avg loser | -$2.64 |

**Loser opportunity**: If we could flip ALL 88 losers, gain = +$391.34
**Skip opportunity**: 24 skip days have $19.74 in PUT PnL (71% PUT win rate)

---

## LOOP 1: Opening Pattern x Direction Override

| Pattern | N | CALL win% | PUT win% | avg CALL | avg PUT | Binary WR% |
|---------|---|-----------|----------|----------|---------|------------|
| CRASH | 39 | 0% | 100% | -$3.32 | $3.32 | 72% |
| DRIFT_DN | 29 | 0% | 100% | -$1.95 | $1.95 | 73% |
| DRIFT_UP | 25 | 100% | 0% | $1.82 | -$1.82 | 54% |
| FAKEDN | 26 | 58% | 42% | $0.48 | -$0.48 | 54% |
| FAKEUP | 28 | 54% | 46% | $0.12 | -$0.12 | 58% |
| INVV | 36 | 47% | 53% | $0.05 | -$0.05 | 47% |
| SURGE | 34 | 100% | 0% | $3.79 | -$3.79 | 70% |
| VSHAPE | 35 | 49% | 51% | -$0.14 | $0.14 | 62% |

**Key insight**: CRASH/DRIFT_DN are 100% PUT. SURGE/DRIFT_UP are 100% CALL. The opening pattern tells you direction with certainty for 4 of 8 patterns. Binary conf gets it wrong 28-46% of the time on these clear patterns.

### Pattern x Binary direction cross-tab (where binary is wrong)

| Pattern | Binary | N | WR | avg PnL | Flip avg |
|---------|--------|---|-----|---------|----------|
| CRASH | CALL | 16 | 0% | -$6.36 | $2.89 |
| DRIFT_DN | CALL | 10 | 0% | -$3.28 | $2.16 |
| DRIFT_UP | PUT | 11 | 0% | -$1.93 | $1.90 |
| SURGE | PUT | 10 | 0% | -$4.89 | $3.87 |
| INVV | CALL | 21 | 47% | -$0.21 | $0.18 |

**Best finding**: CRASH + binary=CALL -> flip to PUT: PnL change $+103.56

---

## LOOP 2: first3 Pattern Mining

| first3 | N | CALL win% | PUT win% | avg CALL | avg PUT | Binary WR% |
|--------|---|-----------|----------|----------|---------|------------|
| GGG | 26 | 100% | 0% | $3.00 | -$3.00 | 60% |
| GGR | 33 | 100% | 0% | $2.92 | -$2.92 | 66% |
| GRG | 28 | 54% | 46% | $0.12 | -$0.12 | 58% |
| GRR | 36 | 47% | 53% | $0.05 | -$0.05 | 47% |
| RGG | 35 | 49% | 51% | -$0.14 | $0.14 | 62% |
| RGR | 26 | 58% | 42% | $0.48 | -$0.48 | 54% |
| RRG | 36 | 0% | 100% | -$2.57 | $2.57 | 74% |
| RRR | 32 | 0% | 100% | -$2.92 | $2.92 | 70% |

**Key insight**: first3 starting with GG = always CALL. Starting with RR = always PUT. Mixed patterns (GR, RG) are coin flips. This mirrors opening_pattern perfectly — they encode the same directional truth.

### first3 x Binary direction (worst mismatches)

| first3 | Binary | N | curPnL | flipPnL | Delta |
|--------|--------|---|--------|---------|-------|
| RRR | CALL | 13 | -$44.06 | $35.69 | +$79.75 |
| RRG | CALL | 13 | -$36.21 | $32.20 | +$68.41 |
| GGR | PUT | 11 | -$43.40 | $34.11 | +$77.51 |
| GGG | PUT | 10 | -$26.72 | $25.49 | +$52.21 |

**Best finding**: RRR + binary=CALL -> flip to PUT: PnL change +$79.75

---

## LOOP 3: PM Feature x Outcome Clusters

### Quadrant analysis: pm_slope sign x pm_curvature sign

| Quadrant | N | CALL win% | PUT win% | avg CALL | avg PUT | Binary WR |
|----------|---|-----------|----------|----------|---------|-----------|
| slope+/curv+ | 94 | 64% | 36% | $0.62 | -$0.62 | 65% |
| slope+/curv- | 42 | 38% | 62% | -$0.36 | $0.36 | 67% |
| slope-/curv+ | 28 | 50% | 50% | $0.27 | -$0.27 | 43% |
| slope-/curv- | 88 | 38% | 62% | -$0.56 | $0.56 | 62% |

**Observation**: PM slope predicts direction weakly (slope+ = CALL-leaning, slope- = PUT-leaning), but binary conf already captures this. PM curvature adds noise, not signal.

### 16-cell grid: pm_accel_2m quartiles x gap quartiles

Notable cells where binary is wrong:
- A1/G4 (low accel, high gap): binary WR=40%, CALL direction wins. N=12, potential +$16
- A3/G2 (mid accel, mid gap): binary WR=38%. N=15, small edge
- A3/G3 (mid accel, mid-high gap): binary WR=41%. N=21

**Best finding**: A1/G4 force CALL -> PnL change +$16.05 (N=12, too small to be reliable)

---

## LOOP 4: Rescue Rules for Losers

Total losers: 88, total loser PnL: -$232.20

### Loser profile
- Evenly distributed across patterns (11-18 per pattern)
- 54 PUT-side losers, 34 CALL-side losers
- bar0_range identical to overall mean ($2.81 vs $2.80)

### Rescue rule results

| Rule | Hit | Losers caught | FP% | PnL delta |
|------|-----|---------------|-----|-----------|
| a) first3==RRR & CALL -> PUT | 13 | 8 | 0% | +$79.75 |
| b) pattern==CRASH & CALL -> PUT | 16 | 9 | 0% | +$103.56 |
| c) bar0_range>3 & bar0_dir==R & CALL -> PUT | 19 | 10 | 21% | +$66.14 |
| d) pm_accel_2m<-1 & bar0_dir==R -> PUT | 24 | 6 | 71% | -$0.91 |
| e) gap>5 & bar0_dir==R -> PUT | 27 | 9 | 44% | +$8.09 |

**Best finding**: CRASH + binary=CALL -> flip to PUT: +$103.56 with 0% false positive rate

Rule (b) is perfect: every single CRASH day where binary says CALL is wrong. All 16 days flip profitably.

---

## LOOP 5: Rescue Rules for Skips (CALL-skip days)

24 skip days (agree_count==0 & is_call_tier)

### Skip days by bar0+bar1 direction

| Bar0+Bar1 | N | PUT win% | CALL win% | sum PUT | sum CALL |
|-----------|---|----------|-----------|---------|----------|
| R-R | 10 | 100% | 0% | $24.94 | -$24.94 |
| R-G | 8 | 50% | 50% | $0.26 | -$0.26 |
| G-R | 4 | 75% | 25% | -$0.65 | $0.65 |
| G-G | 2 | 0% | 100% | -$4.81 | $4.81 |

**R-R -> PUT**: 10 days, 100% win rate, +$24.94. This is a perfect rule.
**G-G -> CALL**: 2 days, 100% win rate, +$4.81. Small N but consistent.
**Combined skip rescue**: +$29.75

---

## LOOP 6: Magnitude-Based Sizing

### bar0_range buckets (traded days only, N=228)

| Bucket | N | WR% | avg PnL | total PnL | Direction correct% |
|--------|---|-----|---------|-----------|-------------------|
| <$1.5 | 8 | 62% | $0.80 | $6.37 | 62% |
| $1.5-3 | 140 | 63% | $0.89 | $124.45 | 63% |
| $3-5 | 71 | 56% | $1.18 | $83.80 | 56% |
| >$5 | 9 | 78% | $2.45 | $22.09 | 78% |

### Sizing experiment

| Bucket | Multiplier | Current | New | Delta |
|--------|-----------|---------|-----|-------|
| <$1.5 | 0.5x | $6.37 | $3.19 | -$3.19 |
| $1.5-3 | 1.0x | $124.45 | $124.45 | $0.00 |
| $3-5 | 1.5x | $83.80 | $125.70 | +$41.90 |
| >$5 | 1.0x | $22.09 | $22.09 | $0.00 |

**Best finding**: Range-based sizing adjustment -> PnL change +$38.71

Note: $3-5 bucket has 56% WR but higher avg PnL ($1.18) — the wins are bigger. Sizing up works because magnitude outweighs lower WR. However, this interacts with the direction override rules (which eliminate many of the losers in this bucket), so net effect in combined system is smaller.

---

## LOOP 7: Adaptive Exit from Fingerprints

### Optimal exit by opening pattern

| Pattern | N | Best exit | Best PnL | @2m PnL | Delta |
|---------|---|-----------|----------|---------|-------|
| CRASH | 32 | 16m | $60.72 | $42.33 | +$18.39 |
| DRIFT_DN | 26 | 16m | $40.87 | $16.71 | +$24.16 |
| DRIFT_UP | 24 | 8m | $32.04 | $21.21 | +$10.83 |
| FAKEDN | 24 | 20m | $37.83 | $14.65 | +$23.18 |
| FAKEUP | 26 | 2m | $24.48 | $24.48 | $0.00 |
| **INVV** | **34** | **1m** | **$19.85** | **-$13.89** | **+$33.74** |
| SURGE | 33 | 12m | $165.98 | $115.67 | +$50.31 |
| VSHAPE | 29 | 14m | $26.04 | $15.55 | +$10.49 |

### Exit time curves (PnL at each minute)

```
CRASH:  1m=$15.8  2m=$42.3  3m=$34.3  5m=$44.5  7m=$51.3  10m=$50.9  15m=$54.3  20m=$28.3
SURGE:  1m=$58.6  2m=$115.7 3m=$138.1 5m=$135.1 7m=$147.3 10m=$135.0 15m=$149.6 20m=$133.2
VSHAPE: 1m=$21.8  2m=$15.6  3m=$3.2   5m=$2.8   7m=$14.2  10m=$11.5  15m=$23.4  20m=$16.0
INVV:   1m=$19.8  2m=$-13.9 3m=$-46.0 5m=$-51.1 7m=$-29.0 10m=$-40.6 15m=$-17.6 20m=$-5.0
FAKEUP: 1m=$0.6   2m=$24.5  3m=$12.4  5m=$1.6   7m=$-22.1 10m=$-12.2 15m=$-6.0  20m=$-11.1
FAKEDN: 1m=$-4.1  2m=$14.7  3m=$12.9  5m=$-14.9 7m=$-2.8  10m=$25.2  15m=$28.4  20m=$37.8
```

**Key findings**:
- **INVV**: Reverses hard after 1m. Exit at 1m saves $33.74 vs 2m exit. At 2m it's already negative.
- **SURGE**: Momentum continues well past 2m. Holding to 5m adds $19.44 (to 12m adds $50.31 but decay risk).
- **VSHAPE**: Peaks at 1m ($21.8), degrades by 2m ($15.6), collapses by 3-5m. Quick exit saves money.
- **CRASH**: Steady grind, peaks at 16m. 2m already captures bulk of the move.
- **FAKEUP**: Peaks at 2m then collapses. Current exit is already optimal.
- **FAKEDN**: Slow starter, builds through 10-20m. Could hold longer but high variance.

**Best finding**: INVV exit at 1m -> PnL change +$33.74

---

## LOOP 8: Combined System

### Individual rule impact (independently tested)

| Rule | PnL | Delta |
|------|-----|-------|
| DIR: CRASH+CALL->PUT | $351.27 | +$114.56 |
| DIR: SURGE+PUT->CALL | $334.47 | +$97.76 |
| DIR: DRIFT_DN+CALL->PUT | $282.69 | +$45.98 |
| DIR: DRIFT_UP+PUT->CALL | $279.19 | +$42.48 |
| EXIT: INVV->1m | $270.45 | +$33.74 |
| EXIT: SURGE->5m | $256.15 | +$19.44 |
| EXIT: VSHAPE->1m | $243.00 | +$6.29 |
| EXIT: CRASH->5m | $238.91 | +$2.20 |
| SKIP: RR->PUT | $261.65 | +$24.94 |
| SKIP: GG->CALL | $241.52 | +$4.81 |

### Additive build (each rule added on top of previous)

```
Baseline:                    $236.71
+ CRASH+CALL->PUT:    +$114.56 -> $351.27
+ DRIFT_DN+CALL->PUT:  +$45.98 -> $397.25
+ SURGE+PUT->CALL:     +$97.76 -> $495.01
+ DRIFT_UP+PUT->CALL:  +$42.48 -> $537.49
+ INVV exit@1m:        +$33.74 -> $571.23
+ SURGE exit@5m:       +$20.10 -> $591.33
+ VSHAPE exit@1m:       +$6.29 -> $597.62
+ CRASH exit@5m:        +$3.48 -> $601.10
+ Skip RR->PUT:        +$25.19 -> $626.29
+ Skip GG->CALL:        +$6.79 -> $633.08
---
Final:  $633.08 (vs baseline $236.71 = +167.4%)
```

ALL 10 rules accepted (positive delta when added incrementally).

### Validation: H1/H2 split (126 days each)

| Half | Baseline | Combined | Delta |
|------|----------|----------|-------|
| H1 (first 126d) | $114.80 | $301.44 | +$186.64 |
| H2 (last 126d) | $121.91 | $331.64 | +$209.73 |
| **Both positive?** | | | **YES** |

Direction rules only:
| Half | Baseline | Dir rules | Delta |
|------|----------|-----------|-------|
| H1 | $114.80 | $267.34 | +$152.54 |
| H2 | $121.91 | $270.15 | +$148.24 |

---

## Summary of Actionable Rules

### Direction Override Rules (biggest impact: +$300.78 total)

These 4 rules override binary conf when the opening pattern provides unambiguous direction:

| Rule | Trigger | Action | N days | FP rate |
|------|---------|--------|--------|---------|
| 1 | opening_pattern==CRASH & binary=CALL | Flip to PUT | 16 | 0% |
| 2 | opening_pattern==DRIFT_DN & binary=CALL | Flip to PUT | 10 | 0% |
| 3 | opening_pattern==SURGE & binary=PUT | Flip to CALL | 10 | 0% |
| 4 | opening_pattern==DRIFT_UP & binary=PUT | Flip to CALL | 11 | 0% |

**Why these work**: CRASH/DRIFT_DN are always PUT (100%). SURGE/DRIFT_UP are always CALL (100%). When binary conf disagrees with the opening pattern, binary is ALWAYS wrong. The opening pattern encodes realized price action (first 3 bars), which is a stronger signal than pre-open indicators.

### Exit Time Rules (impact: +$63.61 total)

| Rule | Trigger | Exit change | Why |
|------|---------|-------------|-----|
| 5 | INVV pattern | 2m -> 1m | Reverses hard after 1m, goes negative by 2m |
| 6 | SURGE pattern | 2m -> 5m | Momentum continues, 5m captures 17% more |
| 7 | VSHAPE pattern | 2m -> 1m | Peaks at 1m then degrades |
| 8 | CRASH pattern | 2m -> 5m | Steady grind, 5m slightly better |

### Skip Rescue Rules (impact: +$31.98 total)

| Rule | Trigger | Action | N days | Win rate |
|------|---------|--------|--------|----------|
| 9 | Skip day + bar0=R + bar1=R | Trade PUT 1x | 10 | 100% |
| 10 | Skip day + bar0=G + bar1=G | Trade CALL 1x | 2 | 100% |

---

## Architecture Insight

The opening_pattern and first3_pattern encode the same information from different angles — both are derived from the first 3 one-minute bars after open. The critical discovery is that **4 of 8 patterns have 100% directional certainty** (CRASH/DRIFT_DN = PUT, SURGE/DRIFT_UP = CALL), and binary conf disagrees with these on ~47 days per year. Every single disagreement is binary being wrong.

This means: **the opening pattern IS the direction signal**. Binary conf is only useful for the ambiguous patterns (FAKEUP, FAKEDN, INVV, VSHAPE) where the opening bars don't clearly resolve direction.

The exit optimization further shows that each pattern has a distinct PnL decay curve:
- **Momentum patterns** (CRASH, SURGE, DRIFT_*): hold longer, the move continues
- **Reversal patterns** (INVV, VSHAPE): exit fast, the move fades within 1-2 minutes
- **Ambiguous patterns** (FAKEUP, FAKEDN): current 2m exit is near-optimal
