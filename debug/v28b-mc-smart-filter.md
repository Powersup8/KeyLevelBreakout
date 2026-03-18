# v2.8b MC Smart Filter Research (2026-03-04)

## Problem
MC (Momentum Cascade) signals fire both bull AND bear within 10 minutes at the open on 126/167 days. The first signal is correct only 45% of the time (coin flip). The proposed simple fix is "suppress before 9:50 ET" (79% accuracy). Can we do something smarter?

## Dataset
- **126 opposing pairs** (SPY, QQQ, AMD, AAPL) from Sep 2025 - Mar 2026
- **531 solo MC days** (only one direction fired)
- **981 MC signals** with CONF results
- **421 MC-confirmed trades** with PnL

---

## Section 1: Single-Feature Filters (Opposing Pairs)

When both bull and bear MC fire, pick the one with the indicated feature.

| Filter | n | Correct | Accuracy | vs 45% baseline |
|--------|---|---------|----------|-----------------|
| Pick MC AGAINST VWAP (counter-trend) | 52 | 32 | **61.5%** | +16.5% |
| Pick MC with LOWER close_pos | 119 | 68 | **57.1%** | +12.1% |
| Pick MC with HIGHER ADX | 106 | 60 | **56.6%** | +11.6% |
| Pick MC with PASS+ conf (exclusive) | 71 | 40 | **56.3%** | +11.3% |
| Pick MC with LOWER volume | 126 | 70 | **55.6%** | +10.6% |
| Pick MC with HIGHER body% | 123 | 68 | **55.3%** | +10.3% |
| Always pick SECOND | 126 | 69 | **54.8%** | +9.8% |
| Pick MC AGAINST EMA | 117 | 62 | **53.0%** | +8.0% |
| Pick MC with LOWER range_atr | 121 | 64 | **52.9%** | +7.9% |
| Pick MC with HIGHER ramp | 126 | 65 | **51.6%** | +6.6% |
| Pick MC matching VWAP (with-trend) | 52 | 20 | **38.5%** | -6.5% |

**Key finding:** Counter-VWAP is the strongest single feature. The with-VWAP MC at the open is a TRAP signal (only 38.5% correct).

---

## Section 2: VWAP Counter-Trend Deep Dive

### Why counter-VWAP only applies to 52/126 pairs

The filter requires exactly one MC to match VWAP and the other not to. This depends on whether VWAP changed between the two signals:

| VWAP state | n | Explanation |
|------------|---|-------------|
| **Same VWAP** | 52 | Both MCs see same VWAP -> one matches, one doesn't -> counter-VWAP can decide |
| **VWAP flipped** | 70 | Price crossed VWAP between MCs -> both match their respective VWAP -> filter can't decide |
| **Neither matches** | 4 | Both MCs against VWAP -> filter can't decide |

When VWAP is stable (52 pairs): **counter-VWAP = 62% correct, with-VWAP = 38% correct**.

The first MC matches VWAP 79% of the time on same-VWAP days -- it's the "obvious" with-trend move at the open, and it's usually wrong.

### VWAP-flipped cases (70 pairs)

In these cases, price whipsawed through VWAP. Features tested on these 70 pairs:

| Feature | Accuracy |
|---------|----------|
| Multi-score (vol+body+close_pos) | **67%** |
| Pick lower volume | 61% |
| Pick lower close_pos | 60% |
| Always pick second | 60% |
| Pick higher body% | 56% |
| Pick higher ADX | 56% |

### Best composite strategy on all 126 pairs

**Counter-VWAP (52 clear cases) + multi-score fallback (74 ambiguous): 81/126 = 64.3%**

Multi-score fallback: for each MC, score +1 for lower volume, higher body%, lower close_pos. Pick the MC with higher score.

---

## Section 3: Feature Comparison (Correct vs Wrong MC)

| Feature | Correct MC (mean) | Wrong MC (mean) | Delta |
|---------|------------------|-----------------|-------|
| vol | 8.6 | 9.5 | -10% |
| ramp | 35.1 | 35.1 | 0% |
| body | 62.2 | 59.1 | +5% |
| range_atr | 3.3 | 3.4 | -3% |
| close_pos | 80.0 | 80.2 | 0% |
| adx | 29.7 | 29.4 | +1% |

The correct MC has slightly lower volume and higher body%. Ramp, close_pos, and ADX are indistinguishable.

---

## Section 4: Sequential / Timing Analysis

### Time gap between opposing MCs

- **5min gap:** n=90, second correct 57%
- **10min gap:** n=36, second correct 50%

Longer gap does NOT help. EMA rarely changes between the two signals (93% stable).

### First signal timing

| First MC time | n |
|---------------|---|
| 9:30 | 6 |
| 9:35 | 90 |
| 9:40 | 30 |

90/126 first signals are at 9:35 (the opening explosion bar).

---

## Section 5: CONF-Based Filtering

**Wait for CONF to pick a side:**
- CONF pass+ on one side only: 56% accuracy (n=71)
- CONF star on one side only: 50% accuracy (n=38)
- Both get CONF: 14 pairs (undecided)
- Neither gets CONF: 41 pairs (undecided)

CONF is not a reliable arbiter between opposing MCs.

---

## Section 6: Counter-VWAP as Universal Quality Filter

A surprising finding when looking at ALL MC signals (not just opposing pairs):

### MC CONF quality by VWAP alignment at 9:35

| Alignment | CONF pass+ | n |
|-----------|------------|---|
| VWAP-counter at 9:35 | **93%** | 60 |
| VWAP-aligned at 9:35 | 72% | 316 |

At 9:35 specifically, counter-VWAP MC signals have 93% CONF pass rate! This is extraordinary.

### By time slot

| Time | VWAP-counter pass+ | VWAP-aligned pass+ |
|------|--------------------|--------------------|
| 9:35 | **93%** (56/60) | 72% (227/316) |
| 9:40 | 66% (55/83) | 62% (146/235) |
| 9:45 | 47% (35/75) | 46% (86/185) |

The counter-VWAP quality edge is strongest at 9:35 and fades by 9:45.

### Counter-VWAP quality by symbol

| Symbol | Counter-VWAP pass+ |
|--------|-------------------|
| SPY | 92% (24/26) |
| MSFT | 83% (15/18) |
| GOOGL | 75% (18/24) |
| AAPL | 70% (21/30) |
| TSLA | 70% (21/30) |
| META | 67% (12/18) |
| AMD | 62% (13/21) |
| QQQ | 57% (8/14) |
| NVDA | 52% (12/23) |
| AMZN | 48% (12/25) |

---

## Section 7: Trade Profitability (The Dealbreaker)

Despite counter-VWAP having better direction accuracy, **early MC trades lose money regardless:**

| Window | VWAP filter | n | Win rate | Mean PnL/ATR |
|--------|------------|---|----------|-------------|
| Before 9:50 | Counter-VWAP | 18 | 28% | **-0.065** |
| Before 9:50 | VWAP-aligned | 129 | 36% | **-0.018** |
| After 9:50 | Counter-VWAP | 41 | 41% | **+0.118** |
| After 9:50 | VWAP-aligned | 226 | 34% | **+0.012** |

**After 9:50, counter-VWAP MC trades have the best expectancy of any MC subgroup: +0.118 ATR per trade.**

But before 9:50, even counter-VWAP MCs have negative expectancy. The problem isn't just direction -- it's that the opening auction lacks follow-through. Moves reverse, stop losses get hit, regardless of initial direction correctness.

---

## Section 8: Solo MC Signals

| Category | n |
|----------|---|
| Solo MC days (one direction only) | 531 |
| Opposing pair days | 126 |
| Total MC days | 657 |

Solo MCs: CONF pass+ rate = 69% (star=201, pass=167, fail=163). These are unambiguous and don't suffer from the opposing-pair problem.

---

## Section 9: Implementation Options

### Option A: 9:50 Time Gate (Recommended)
- Suppress all MC before 9:50 ET
- Direction accuracy after 9:50: **79%**
- Trade expectancy after 9:50: **+0.028 ATR** (all MCs), **+0.118 ATR** (counter-VWAP subset)
- Complexity: trivial (one time check)
- Preserves once-per-session MC slot for the real move

### Option B: Counter-VWAP Filter at Open
- Suppress MC when direction matches VWAP (the trap signal)
- Allow MC when direction opposes VWAP
- Direction accuracy on exclusive pairs: **61.5%** (n=52)
- Trade expectancy before 9:50: **-0.065 ATR** (still negative!)
- Complexity: low (check direction vs VWAP)
- Problem: 70/126 pairs have ambiguous VWAP (flipped between signals)

### Option C: Counter-VWAP + Multi-Score Composite
- Counter-VWAP for clear cases + vol/body/close_pos scoring for ambiguous cases
- Direction accuracy: **64.3%** (n=126)
- Requires storing features of both opposing MCs and comparing
- Complexity: moderate (~30 lines Pine Script)
- Trade expectancy: still negative before 9:50

### Option D: Hybrid (Counter-VWAP + 9:50 Gate)
- At 9:35-9:45: only allow counter-VWAP MCs through
- Ambiguous cases: wait until 9:50
- Expected direction accuracy: **~72%**
- Complexity: moderate
- Still has negative trade expectancy on early signals

### Option E: 9:50 Gate + Counter-VWAP Bonus (Post-9:50)
- Use 9:50 gate as-is for suppression
- After 9:50: prioritize counter-VWAP MC signals
- Counter-VWAP trades after 9:50 have **+0.118 ATR** expectancy (best subgroup)
- Complexity: low (add VWAP check to post-9:50 MC evaluation)

---

## Section 10: Conclusion

### The 9:50 time gate remains the best approach

No smart filter overcomes the fundamental problem: **the opening auction (9:30-9:50) lacks follow-through**. Even when we correctly identify direction at the open (64.3% with the best composite filter), trades before 9:50 have negative expectancy.

The issue is not just which MC to pick -- it's that the entire 9:30-9:50 window is structurally noisy. Prices whipsaw, stops get hit, and directional moves don't sustain.

### One actionable insight: Counter-VWAP after 9:50

The counter-VWAP finding IS useful, just not for the opening window. **After 9:50, counter-VWAP MC trades have +0.118 ATR expectancy vs +0.012 for VWAP-aligned**. This could be used as a quality ranking factor for MC signals after 9:50 (not a suppression filter, but a confidence boost).

### Summary of findings

| Approach | Direction Accuracy | Trade Expectancy | Complexity |
|----------|-------------------|-----------------|------------|
| No filter (coin flip at open) | 45% | -0.023 ATR | None |
| Counter-VWAP only | 61.5% (n=52) | -0.065 ATR | Low |
| Composite (VWAP + multi-score) | 64.3% (n=126) | Negative | Moderate |
| **9:50 time gate** | **79%** | **+0.028 ATR** | **Trivial** |
| 9:50 gate + counter-VWAP boost | 79% | +0.118 ATR* | Low |

*Counter-VWAP subset only (n=41)

**Recommendation:** Implement Option A (9:50 time gate) with Option E (counter-VWAP as quality bonus after 9:50).

## Analysis Scripts
- `debug/v28b_mc_smart_filter.py` -- Main analysis (single/combo filters, all 126 pairs)
- `debug/v28b_vwap_deep.py` -- VWAP counter-trend deep dive (flipped vs stable)
- `debug/v28b_vwap_flip.py` -- VWAP-flipped cases analysis (70 ambiguous pairs)
- `debug/v28b_practical.py` -- Implementation feasibility + trade profitability
- `debug/v28b_solo_vwap.py` -- Solo MC analysis + universal VWAP quality filter
- `debug/v28b_final.py` -- Final composite strategy + delay analysis
