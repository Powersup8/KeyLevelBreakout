# Midday Desert Research Report

**Generated:** 2026-03-06
**Script:** `debug/midday_desert_research.py`
**Data:** 13 symbols, 28 days (2026-01-20 to 2026-02-27), enriched signals + big moves + IB 5m/1d candles

---

## 1. Executive Summary

**The midday desert is real but the ATR sitting on the table is mostly unreachable.**

- **3,265 midday moves >= 1 ATR** happen across 13 symbols over 28 days (116.6/day).
- 92.4% of these moves are within 0.3% of at least one wider-timeframe level, so **levels are NOT the bottleneck** -- price is always near *something*.
- The real problem: midday moves are **structurally different** from morning moves. They are lower-volume (1.37x avg), lower-ADX (24.8 avg), and directionally random. No single trigger stands out.
- **Cross-symbol momentum = zero edge.** Even when 11/11 equities align on a single 5m bar, follow-through is 0.10 ATR (essentially noise).
- **Trend continuation = dead end.** Zero of 15 strong (>=1 ATR) morning trends produced a midday continuation of 0.5+ ATR.
- **Volume compression → expansion = too rare.** Only 6 events in 28 days, 0% hit 1 ATR.

### Best paths forward (ranked)

| Rank | Idea | Expected Impact | Complexity |
|------|------|----------------|------------|
| 1 | **Add Today's Open as a level** | ~16% of midday moves near it, 1.43 avg MFE | Low (1 line) |
| 2 | **Add PD Close as a level** | ~13% of moves near it, 1.38 avg MFE, 72% EMA-aligned | Low (1 line) |
| 3 | **Add Week Open as a level** | ~11% near it, 1.48 avg MFE | Low (1 line) |
| 4 | **Add Month Open as a level** | ~4.4% near it, **1.65 avg MFE** (highest) | Low (1 line) |
| 5 | **Extend CONF window (already in v3.0)** | Recovers 289 ATR from CONF failures | Done |
| 6 | **Ungate RNG time filter** | Vol compression is too rare midday -- marginal | Medium |

**Total estimated additional midday coverage: ~200-300 new level-proximate signals** if all four levels (Today Open, PD Close, Week Open, Month Open) are added. These are low-hanging fruit requiring minimal code changes.

**Warning: Midday quality filters show minimal edge.** EMA alignment lifts avg MFE from 1.46 to 1.48 (trivial). The best filter is "previous bar same direction + EMA" (1.56 avg MFE) but it cuts volume 68%. The honest truth: midday moves are largely random walks with an MFE of ~1.4 ATR and MAE of ~1.7 ATR. **The MAE exceeds MFE -- most midday signals would be net losers** unless entry timing is extremely precise.

---

## 2. Midday Move Anatomy

### 2.1 Signal Count by 30-Minute Bucket

| Bucket | Signals | /Day | Avg MFE | Avg MAE | Win Rate |
|--------|---------|------|---------|---------|----------|
| 09:30-10:00 | 1,058 | 37.8 | 0.300 | -0.259 | 51.4% |
| 10:00-10:30 | 312 | 11.1 | 0.261 | -0.191 | 53.8% |
| 10:30-11:00 | 52 | 1.9 | 0.168 | -0.227 | 42.3% |
| 11:00-11:30 | 27 | 1.0 | 0.262 | -0.111 | 55.6% |
| 11:30-12:00 | 19 | 0.7 | 0.197 | -0.157 | 42.1% |
| 12:00-12:30 | 28 | 1.0 | 0.217 | -0.169 | 46.4% |
| 12:30-13:00 | 28 | 1.0 | 0.074 | -0.136 | 32.1% |
| 13:00-13:30 | 47 | 1.7 | 0.133 | -0.160 | 53.2% |
| 13:30-14:00 | 35 | 1.2 | 0.122 | -0.103 | 57.1% |
| 14:00-14:30 | 26 | 0.9 | 0.164 | -0.181 | 46.2% |
| 14:30-15:00 | 47 | 1.7 | 0.109 | -0.094 | 51.1% |
| 15:00-15:30 | 45 | 1.6 | 0.188 | -0.109 | 62.2% |
| 15:30-16:00 | 117 | 4.2 | 0.097 | -0.087 | 49.6% |

**Key insight:** The drop is cliff-like. From 37.8 signals/day before 10:00 to 1.9/day at 10:30-11:00 and ~1.0/day after 11:00. The few midday signals that DO fire (11:00-11:30) actually have decent MFE (0.262) but there are simply too few of them.

### 2.2 Big Moves (>= 1 ATR) by Time Bucket

| Bucket | Moves | /Day | Avg ATR | Max ATR | Avg MFE | Avg Vol |
|--------|-------|------|---------|---------|---------|---------|
| 09:30-10:00 | 663 | 23.7 | 2.13 | 9.44 | 2.41 | 2.57x |
| 10:00-10:30 | 476 | 17.0 | 1.43 | 3.94 | 1.51 | 1.16x |
| 10:30-11:00 | 376 | 13.4 | 1.29 | 3.08 | 1.58 | 0.86x |
| 11:00-11:30 | 257 | 9.2 | 1.28 | 6.74 | 1.33 | 0.93x |
| 11:30-12:00 | 246 | 8.8 | 1.26 | 2.39 | 1.42 | 1.02x |
| 12:00-12:30 | 257 | 9.2 | 1.25 | 2.26 | 1.19 | 1.01x |
| 12:30-13:00 | 259 | 9.2 | 1.28 | 2.91 | 1.32 | 1.14x |
| 13:00-13:30 | 286 | 10.2 | 1.34 | 3.04 | 1.25 | 1.18x |
| 13:30-14:00 | 299 | 10.7 | 1.29 | 2.37 | 1.51 | 1.16x |
| 14:00-14:30 | 352 | 12.6 | 1.43 | 4.72 | 1.59 | 1.30x |
| 14:30-15:00 | 370 | 13.2 | 1.36 | 6.00 | 1.88 | 1.36x |
| 15:00-15:30 | 416 | 14.9 | 1.33 | 3.44 | 1.86 | 1.36x |
| 15:30-16:00 | 523 | 18.7 | 1.54 | 3.98 | 1.13 | 2.30x |

**Pattern:** Midday has 8-10 big moves per 30-min bucket (vs 24 in the morning). The moves are there but smaller (1.25-1.34 ATR vs 2.13 morning) and at lower volume (0.86-1.18x vs 2.57x morning). The afternoon pickup (14:00+) is notable -- 13-19 moves/bucket with higher MFE.

### 2.3 Why No Signals Midday?

**EMA alignment of midday big moves:**
- EMA aligned: 61.7% (vs ~65% morning)
- VWAP aligned: 62.0%
- ADX > 25: 38.6%

EMA alignment is NOT the gating issue -- 62% of midday moves are EMA-aligned. The problem is that **there are no key levels for price to interact with midday**. The existing levels (PM H/L, Yest H/L, ORB H/L, VWAP) are all established by 10:30 and price has moved past them.

### 2.4 Midday Move Characteristics

| Metric | Morning (<11:00) | Midday (>=11:00) |
|--------|------------------|------------------|
| Avg volume | 2.57x | 1.37x |
| Avg body % | ~80% | 77% |
| Avg ADX | ~30 | 24.8 |
| Prev same dir | ~50% | 46.4% |
| Low vol preceded (<0.5x) | rare | 8.1% |
| High vol move (>=3x) | ~20% | 4.6% |

Midday moves are **quieter, less directionally persistent, and lack volume conviction**. This explains why volume-based triggers (RNG) fail midday.

---

## 3. Wider-Timeframe Level Analysis

### 3.1 Level Proximity to Midday Moves (within 0.3% of price)

92.4% of midday big moves have at least one wider-TF level within 0.3%. The table below shows all level types ranked by hit rate (percentage of midday moves near that level):

**Levels already in KLB:**

| Level | Hits | Hit Rate | Avg MFE | Breakout % | EMA % |
|-------|------|----------|---------|------------|-------|
| VWAP | 1,225 | 37.5% | 1.43 | 48.7% | 72.7% |
| PD Mid | 340 | 10.4% | 1.36 | 49.4% | 68.5% |
| PD Low | 318 | 9.7% | 1.31 | 53.5% | 62.3% |
| PD High | 310 | 9.5% | 1.49 | 55.8% | 60.6% |

**NEW levels NOT in KLB (ranked by score = hit_rate x avg_mfe):**

| Level | Hits | Hit Rate | Avg MFE | Breakout % | EMA % | Score |
|-------|------|----------|---------|------------|-------|-------|
| **VWAP +1 sigma** | 1,185 | 36.3% | 1.48 | 47.8% | 65.2% | 53.9 |
| **VWAP -1 sigma** | 1,097 | 33.6% | 1.42 | 49.0% | 66.2% | 47.5 |
| **VWAP +2 sigma** | 561 | 17.2% | 1.58 | 55.4% | 56.7% | 27.2 |
| **VWAP -2 sigma** | 588 | 18.0% | 1.39 | 49.2% | 56.8% | 25.0 |
| **Today's Open** | 529 | 16.2% | 1.43 | 47.3% | 66.5% | 23.2 |
| **PD Close** | 423 | 13.0% | 1.38 | 56.5% | 72.3% | 18.0 |
| **Fib 23.6%** | 394 | 12.1% | 1.46 | 49.2% | 68.0% | 17.7 |
| **Week Open** | 347 | 10.6% | 1.48 | 47.6% | 64.3% | 15.6 |
| **Fib 38.2%** | 343 | 10.5% | 1.44 | 51.0% | 72.3% | 15.1 |
| **Fib 78.6%** | 334 | 10.2% | 1.43 | 49.1% | 68.0% | 14.6 |
| **Fib 61.8%** | 341 | 10.4% | 1.38 | 49.3% | 70.7% | 14.3 |
| **2D High** | 274 | 8.4% | 1.34 | 55.1% | 65.0% | 11.2 |
| **2D Low** | 207 | 6.3% | 1.45 | 53.6% | 56.0% | 9.2 |
| **Month Open** | 145 | 4.4% | **1.65** | 51.7% | 66.2% | 7.3 |
| **3D Low** | 158 | 4.8% | 1.48 | 54.4% | 57.0% | 7.1 |
| **5D Low** | 85 | 2.6% | **1.72** | 63.5% | 60.0% | 4.5 |
| **10D Low** | 59 | 1.8% | **1.80** | 64.4% | 62.7% | 3.2 |

### 3.2 Key Observations

1. **VWAP bands (1s, 2s) dominate** -- they cover 33-36% of midday moves individually. But they are dynamic levels that shift during the day, which is precisely why they capture midday activity where static levels fail.

2. **Today's Open** (16.2% hit rate, 1.43 MFE) is the single best *static* new level for midday. It is already known at market open and provides 66.5% EMA alignment -- the best of any new level.

3. **PD Close** (13.0%, 1.38 MFE) is notable for its 72.3% EMA alignment rate -- the highest of any new level. This makes it particularly attractive since EMA is our primary quality gate.

4. **Week Open** (10.6%, 1.48 MFE) and **Month Open** (4.4%, 1.65 MFE) are rarer but higher-quality levels.

5. **Multi-day highs/lows** (2D, 3D, 5D, 10D) follow a "rarer = better MFE" pattern. 10D Low has the highest MFE (1.80) but only 1.8% hit rate.

6. **Fibonacci levels** from prior day range show 10-12% hit rates with solid MFE. They overlap heavily with PD Mid/PD H/PD L which are already in KLB.

### 3.3 VWAP Band Analysis (tight 0.1 ATR proximity)

| Band | Hits | Coverage | Avg MFE | Reversal % | EMA % |
|------|------|----------|---------|------------|-------|
| VWAP | 1,323 | 40.5% | 1.41 | 51.3% | 73% |
| VWAP +1s | 1,285 | 39.4% | 1.51 | 52.6% | 64% |
| VWAP -1s | 1,229 | 37.6% | 1.38 | 51.3% | 66% |
| VWAP -2s | 613 | 18.8% | 1.39 | 52.4% | 54% |
| VWAP +2s | 559 | 17.1% | 1.52 | 46.7% | 55% |

Even at tight 0.1 ATR proximity, VWAP bands are near 93% of midday moves. Reversal vs breakout is ~50/50 across all bands -- **VWAP bands do not predict direction.** They merely mark where price IS, not where it's going.

---

## 4. Non-Keylevel Trigger Analysis

### 4.1 Volume Compression to Expansion (C8)

**Result: DEAD END**

Only **6 events** in 28 days where 12+ bars of < 0.5x avg volume were followed by a 3x+ volume bar after 11:00. Zero of them hit 1 ATR follow-through (avg MFE: 0.39 ATR).

**Why:** Midday volume is already low. Getting to 0.5x of an already-low average is extremely rare. When volume does spike midday, it tends to be a single bar event without sustained follow-through.

### 4.2 VWAP Band Touches (C9)

**Result: NO EDGE**

17,502 VWAP band touch events midday across all symbols. Follow-through is negligible:
- Bounce rate (1 ATR): 0.0%
- Breakout rate (1 ATR): 0.0%

Per-bar VWAP band touches are noise. The issue is that a single 5m bar move at a VWAP band is too small relative to daily ATR to produce meaningful follow-through in the next 30 minutes.

### 4.3 Cross-Symbol Momentum (C10)

**Result: DEAD END**

| Alignment | Events | /Day | SPY MFE | SPY MAE | Hit 1 ATR |
|-----------|--------|------|---------|---------|-----------|
| 10+/11 aligned | 510 | 18.2 | 0.10 | 0.10 | 0.0% |
| 11/11 aligned | 233 | 8.3 | 0.11 | 0.10 | 0.0% |
| 3-bar streak (9+) | 51 | 1.8 | 0.10 | 0.17 | 0.0% |

Even perfect 11/11 cross-symbol alignment produces zero follow-through (0.11 ATR MFE). The alignment is already priced in by the time it's observable. This is a classic case of coincident indicator = no edge.

### 4.4 Pullback-and-Continuation (C11)

**Result: DEFINITIVELY DEAD**

Of 15 symbol-days with strong (>=1 ATR) morning moves, **zero** produced a midday continuation of 0.5+ ATR. The broader sample (79 days with >=0.5 ATR morning move) shows only 3.8% continuation rate.

| Morning Move | N | Cont Rate | Avg Pullback | Avg Continuation | Net Midday |
|-------------|---|-----------|-------------|-----------------|------------|
| >= 0.5 ATR | 79 | 3.8% | 0.29 ATR | 0.12 ATR | -0.07 ATR |
| >= 1.0 ATR | 15 | 0.0% | 0.52 ATR | 0.06 ATR | -0.34 ATR |
| >= 1.5 ATR | 1 | 0.0% | 1.24 ATR | 0.00 ATR | -1.00 ATR |

**The stronger the morning move, the worse the midday outcome.** Larger morning moves produce deeper pullbacks and near-zero continuation. This confirms that midday is structurally mean-reverting, not trend-continuing.

---

## 5. Quality Filters for Midday Signals

### 5.1 Filter Comparison on Midday Big Moves

| Filter | N | % of Total | Avg MFE | Avg MAE | MFE>=1 % |
|--------|---|-----------|---------|---------|----------|
| ADX > 40 | 324 | 9.9% | 1.56 | -1.69 | 54.0% |
| Prev same + EMA | 1,060 | 32.5% | 1.56 | -1.74 | 55.5% |
| Prev same dir | 1,516 | 46.4% | 1.54 | -1.72 | 55.0% |
| EMA + Vol>=2x | 318 | 9.7% | 1.48 | -1.80 | 50.9% |
| EMA aligned | 2,016 | 61.7% | 1.48 | -1.73 | 53.4% |
| ADX > 30 | 853 | 26.1% | 1.46 | -1.66 | 53.7% |
| **Baseline (all)** | **3,265** | **100%** | **1.46** | **-1.71** | **52.9%** |
| Vol >= 3x | 151 | 4.6% | 1.04 | -1.69 | 31.1% |

**Critical finding:** Even the best filter (ADX > 40) only lifts MFE from 1.46 to 1.56 -- a 7% improvement. And MAE exceeds MFE across ALL filters. **Midday trades are structurally losers** on average because you absorb 1.7 ATR adverse excursion for only 1.5 ATR favorable excursion.

The only filter that meaningfully changes the risk profile is "ADX > 40" (324 signals, ~10% of total), which narrows MAE to -1.69 while lifting MFE to 1.56. But this is a 0.13 net = barely breakeven after costs.

### 5.2 Implications

Midday signals require **different exit management** than morning signals. The 5m MFE/MAE on big-move bars favors reversal entries with tight stops rather than breakout entries with wide targets. Any midday implementation would need:
- Tighter stops (MAE tolerance)
- Faster exits (don't hold for continuation)
- Reversal bias at 2-sigma VWAP bands

---

## 6. Recommendations

### Tier 1: Implement (low effort, clear benefit)

1. **Add Today's Open level** -- 16.2% of midday moves touch it, 1.43 avg MFE, 66.5% EMA-aligned. Single line addition to Pine Script.

2. **Add Prior Day Close level** -- 13.0% hit rate, 1.38 avg MFE, 72.3% EMA alignment (highest). Often coincides with overnight gap fills.

3. **Add Week Open level** -- 10.6% hit rate, 1.48 avg MFE. Significant psychological level.

4. **Add Month Open level** -- 4.4% hit rate, **1.65 avg MFE** (best). Rare but high-quality.

**Combined estimated impact:** ~200-300 additional level interactions per study period. These are levels where price DOES interact midday, providing the indicator with something to signal on.

### Tier 2: Investigate further

5. **VWAP +/- 1 sigma as display levels** -- 36-37% hit rate is extremely high. However, the 50/50 reversal/breakout split means these cannot be used as directional signals without additional confirmation. They would be useful as **visual reference** on the chart but not as signal triggers.

6. **ADX > 40 as midday quality gate** -- The only filter that meaningfully improves midday MFE. But N=324 (10% of moves) is small and would need more data to validate.

### Tier 3: Do NOT implement

7. **Cross-symbol momentum** -- Zero edge at any alignment threshold. Dead end.

8. **Ungating RNG time filter** -- Volume compression events are 6/month midday. Not worth the complexity.

9. **Trend continuation signal** -- Morning moves do NOT continue midday. 0% success rate.

10. **Multi-day highs/lows** (2D, 3D, 5D) -- Low hit rates (4-8%) and overlap with existing levels. Not worth chart clutter.

11. **Fibonacci levels from prior day** -- 10-12% hit rates but heavily overlap with PD Mid/PD High/PD Low already in KLB.

---

## 7. Data Tables

### 7.1 Midday Big Moves by Symbol

| Symbol | Moves | Avg ATR | Avg MFE | Bull % |
|--------|-------|---------|---------|--------|
| TSLA | 275 | 1.35 | 1.45 | 45.1% |
| NVDA | 270 | 1.33 | 1.65 | 48.5% |
| SPY | 269 | 1.34 | 1.43 | 48.7% |
| AAPL | 265 | 1.40 | 1.84 | 47.9% |
| AMZN | 256 | 1.34 | 1.27 | 54.3% |
| GOOGL | 251 | 1.33 | 1.43 | 49.4% |
| MSFT | 251 | 1.39 | 1.45 | 49.0% |
| META | 248 | 1.34 | 1.52 | 49.2% |
| QQQ | 244 | 1.33 | 1.39 | 47.5% |
| SLV | 242 | 1.40 | 1.64 | 53.7% |
| TSM | 237 | 1.31 | 0.88 | 47.3% |
| GLD | 230 | 1.47 | 1.64 | 53.9% |
| AMD | 227 | 1.28 | 1.34 | 47.6% |

### 7.2 New Level Types — Expected Signals and Total MFE

| Level | Signals | Avg MFE | Total MFE | EMA % | Avg Move ATR |
|-------|---------|---------|-----------|-------|-------------|
| VWAP +1 sigma | 1,185 | 1.48 | 1,759 | 65.2% | 1.37 |
| VWAP -1 sigma | 1,097 | 1.42 | 1,552 | 66.2% | 1.34 |
| VWAP +2 sigma | 561 | 1.58 | 886 | 56.7% | 1.35 |
| VWAP -2 sigma | 588 | 1.39 | 818 | 56.8% | 1.35 |
| Today's Open | 529 | 1.43 | 758 | 66.5% | 1.37 |
| PD Close | 423 | 1.38 | 584 | 72.3% | 1.36 |
| Fib 23.6% | 394 | 1.46 | 576 | 68.0% | 1.35 |
| Week Open | 347 | 1.48 | 512 | 64.3% | 1.36 |
| Month Open | 145 | 1.65 | 240 | 66.2% | 1.33 |

---

## 8. Bottom Line

The midday desert exists because the KLB system's levels are morning-centric (ORB, PM H/L establish at open; PD H/L are tested early). Adding Today's Open, PD Close, Week Open, and Month Open gives the system something to anchor midday signals to.

**However, expectations must be tempered.** Midday moves have worse MFE/MAE ratios than morning moves. Any midday signals will need tighter risk management or a reversal bias rather than the breakout bias that works in the morning. The biggest risk is adding noise signals that dilute overall win rate.

**Recommended next step:** Add the four new levels (Today Open, PD Close, Week Open, Month Open) as a v3.1 feature and track their signal quality separately in Pine logs for 2-4 weeks before drawing conclusions about midday signal viability.
