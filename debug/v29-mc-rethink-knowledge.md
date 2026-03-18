# MC Rethink — Comprehensive Knowledge Base
> Compiled: 2026-03-04 | Sources: 10 analysis files from v2.8a-v29 research

---

## 1. Current MC: What It Does, How It Works, Its Problems

### What MC Is
MC (Momentum Cascade) detects explosive volume surges on a single 5m bar. It fires when:
- **Volume ramp > 5x** (current bar volume vs average of prior 3-6 bars)
- **Range/ATR >= 1.5** (bar range at least 1.5x the signal-TF ATR(14))
- Directional candle (clear bull or bear)
- Once-per-direction-per-session guard (max 1 bull MC + 1 bear MC per day)
- ADX + body quality filter applied

MC does NOT generate trades directly. It auto-confirms subsequent BRK/REV/VWAP signals that fire in the same direction, acting as a "free CONF pass."

### MC Signal Volume
- **1,209 total MC signals** across 10 symbols, ~107 trading days (Sep 2025 - Mar 2026)
- **87 QBS signals** in same period (for comparison)
- Per symbol: 102-133 MC signals each

### The Core Problem: Opening Noise
**99.4% of MC signals fire before 9:50 ET.** Only 7 fire later.

| Time | Count | % |
|------|------:|--:|
| 9:30 | 30 | 2.5% |
| 9:35 | 521 | 43.1% |
| 9:40 | 391 | 32.3% |
| 9:45 | 260 | 21.5% |
| After 9:50 | 7 | 0.6% |

### The Opposing Pairs Problem
On **126 out of 167 days with MC** (for SPY/QQQ/AMD/AAPL), BOTH bull AND bear MC fire within 5-10 minutes at the open. This burns both once-per-session slots on noise.

- First signal correct: **45%** (coin flip)
- Second signal correct: **55%** (coin flip)
- No signal feature can distinguish correct from wrong at signal time
- Ramp, volume, range/ATR, body%, ADX, close position -- all indistinguishable between correct and wrong MC

**334 symbol-days** have both slots burned before 9:50. On those days, MC can never fire again.

### CONF as Filter: Weak
- CONF pass on one side only: 56% accuracy (only 8% above baseline)
- CONF star on one side: 50% accuracy (no edge)
- CONF is not a reliable arbiter between opposing MCs

### VWAP/EMA Alignment: INVERSE at Open
| Alignment | Correct | Wrong |
|-----------|---------|-------|
| Dir matches VWAP | 71% | **81%** |
| Dir matches EMA | 46% | 52% |

The "obvious" with-trend MC at 9:35 is the TRAP signal. The first MC matches VWAP 79% of the time and is usually wrong.

### MC-Confirmed Trade Performance
| Window | Trades | Total PnL | Avg PnL | Win% |
|--------|-------:|----------:|--------:|-----:|
| Before 9:50 | 147 | -3.44 | -0.023 | 34.7% |
| After 9:50 | 274 | +7.78 | +0.028 | 35.0% |

Pre-9:50 trades have **negative expectancy**. Post-9:50 trades are positive. But 201 post-9:50 trades get their CONF from an early MC that fired before 9:50 -- these are the core value of early MC (9.68 ATR total).

### By Symbol
| Symbol | MC# | Pairs | Trades | Avg PnL | Win% |
|--------|----:|------:|-------:|--------:|-----:|
| TSLA | 133 | 0 | 47 | +0.147 | 40.4% |
| GOOGL | 122 | 0 | 41 | +0.039 | 41.5% |
| META | 116 | 0 | 36 | +0.043 | 38.9% |
| AMD | 129 | 37 | 40 | +0.027 | 32.5% |
| MSFT | 117 | 0 | 44 | +0.009 | 34.1% |
| NVDA | 128 | 0 | 49 | -0.001 | 40.8% |
| QQQ | 106 | 26 | 41 | -0.019 | 36.6% |
| SPY | 102 | 25 | 36 | -0.036 | 33.3% |
| AMZN | 127 | 0 | 42 | -0.046 | 23.8% |
| AAPL | 129 | 38 | 45 | -0.070 | 26.7% |

### Why So Few Post-9:50 MC Signals?
MC requires ramp > 5x AND range/ATR >= 1.5. These extreme conditions are characteristic of the opening volatility burst and almost never occur later:
- Pre-9:50 avg ramp: **31.8x**
- Post-9:50 potential MC avg ramp: **6.5x** (barely above threshold)
- Even if slots weren't burned, only **7 additional signals** would fire after 9:50

**The fundamental issue: MC's detection criteria (explosive single-bar ramp) are inherently an opening-auction phenomenon. Real intraday momentum is gradual, multi-bar, and doesn't produce 5x volume spikes on individual bars.**

---

## 2. Volume Patterns: U-Shaped Ramp, Exhaustion, Drying, Explosion

### Pre-Move Volume Ramp Is U-Shaped (2069 big moves, 13 symbols, 2x 5m-ATR threshold)

| Vol Ramp | n | Runner% | Fakeout% | Avg MFE |
|----------|---|---------|----------|---------|
| <0.5x (drying) | 314 | **68%** | 3% | 1.92 |
| 0.5-1x (steady) | 490 | 67% | 6% | 1.79 |
| 1-2x (moderate) | 451 | **56%** | **7%** | 1.64 |
| 2-5x (surging) | 191 | 53% | 4% | 2.04 |
| >5x (explosive) | 316 | **64%** | 3% | **2.66** |

**Key insight: The U-shape.** Both ends (drying and explosive) produce better outcomes than the middle (moderate ramping). This is why MC's QBS counterpart (volume drying) also works.

### Volume Drying = Compression Before Explosion
- QBS fires on volume drying (<0.5x avg) -- 87 signals in dataset
- QBS fires throughout the day (67 after 9:50 vs only 7 MC after 9:50)
- Proves that volume-based patterns DO occur after 9:50 when detection criteria fit

### High Volume at Signal = Different Meaning by Context
- **At key level breakout:** Vol >= 10x = 32% CONF, 0.50 MFE (best). Institutional participation.
- **At general big bars:** Vol >= 2x = more fakeouts (15%) than runners (8%). Exhaustion/capitulation signal.
- **Resolution:** Volume meaning depends on whether it's AT a level (confirmation) or IN a move (exhaustion).

### Moderate Ramp (1-2x) = Worst Bucket
- 56% runner rate (worst), 7% fakeout rate (worst)
- In v2.8, moderate ramp was auto-dimmed on labels for this reason

---

## 3. What "Real" Momentum Looks Like (From Big-Move Data)

### Big Move Fingerprint (9,596 significant 5m bars, 13 symbols)
- **Runners** (MFE > 0.3 ATR): 8,098 (84%)
- **Fakeouts** (MFE < 0.1, MAE < -0.15): 268 (3%)

### The Strongest Differentiators (Runner vs Fakeout)

| Feature | Runners | Fakeouts | Gap | Direction |
|---------|---------|----------|-----|-----------|
| 5min P&L positive | 50% | 16% | **+34%** | Higher = runner |
| 5min P&L > 0.05 ATR | 31% | 2% | **+30%** | Higher = runner |
| Body >= 80% | 36% | 55% | **-19%** | Higher = FAKEOUT |
| Vol >= 2x | 8% | 15% | **-7%** | Higher = FAKEOUT |
| Before 11:00 | 24% | 16% | +8% | Morning = runner |
| Bear direction | 51% | 44% | +7% | Bear = runner |
| At VWAP (+-0.1 ATR) | 89% runner rate | | | VWAP zone = best |

### 5-Minute Gate Is THE Strongest Predictor
| 5min P&L bucket | n | Runner% | Fakeout% | Avg MFE |
|-----------------|---|---------|----------|---------|
| > +0.15 ATR | 896 | **98%** | **0%** | 1.98 |
| +0.05 to +0.15 | 1,870 | **91%** | **0%** | 1.62 |
| 0 to +0.05 | 2,628 | 78% | 3% | 1.32 |
| -0.05 to 0 | 1,646 | 86% | 3% | 1.42 |
| < -0.05 | 2,556 | 81% | 5% | 1.38 |

Best combo: **5min > 0.05 + EMA aligned + VWAP aligned = 93% runner, 0% fakeout** (n=1,411)

### Body >= 80% = FAKEOUT Indicator (INVERSE!)
- Fakeouts: 55% have body >= 80%
- Runners: only 36% have body >= 80%
- High body on a big bar = exhaustion candle, not continuation

### VWAP Proximity = Best Zone
| VWAP Distance (ATR) | n | Runner% | Avg MFE |
|---------------------|---|---------|---------|
| At VWAP (+-0.1) | 412 | **89%** | **1.98** |
| Far from VWAP (>0.3) | 4,529 | 83% | 1.42 |

Moves originating right at VWAP have 47% better MFE. This validates VWAP-as-signal-level.

### Multi-Symbol Big Move Validation (2,069 moves, 2x 5m-ATR threshold)
- **5-min P&L positive:** Validates across ALL 13 symbols (62% gap, every single symbol shows 0% fakeout rate when 5min is positive)
- **Pre-vol ramp:** Validates for 8/12 symbols (runners have higher pre-move ramp)
- **ADX:** Only validates for 4/12 symbols -- TSLA-specific, don't generalize
- **Gap down:** Only validates for 5/12 symbols -- TSLA/AMD specific

---

## 4. The Missed Moves Gap (What We're NOT Catching)

### March 3, 2026: 6 Significant Moves With Zero Signals

| Symbol | Window | Dir | Move (ATR) | Type |
|--------|--------|-----|------------|------|
| SPY | 10:30-13:40 | UP | 11.82x | Grinding rally, 3+ hours |
| QQQ | 10:30-13:40 | UP | 11.07x | Same event, correlated |
| NVDA | 10:55-11:05 | UP | 5.85x | Sharp burst, 10 min |
| AAPL | 10:10-12:30 | DOWN | 6.12x | Slow selloff, 2+ hours |
| AAPL | 12:30-14:40 | UP | 4.20x | Reversal grind, 2+ hours |
| TSLA | 10:44-11:25 | UP | 6.33x | Moderate burst, 40 min |

### Common Pattern in Missed Moves
1. **ALL had VWAP crossings** (6/6) -- VWAP-as-signal-level would have caught most
2. **All were impulsive** -- at least one 5m bar hit 2x+ ATR
3. **SPY/QQQ grinding rally**: 64-69% directional consistency over 39 bars. Average volume only 0.87-1.01x day average. **No single bar explosion, just relentless directional pressure.**
4. **Level Desert problem**: After initial morning breaks, all 8 key level types are either broken or far away. The indicator goes silent in the continuation zone.
5. **Mid-day timing**: Most windows start after 10:30, in the zone where MC slots are already burned

### Root Cause: What MC Misses
MC detects **explosive single-bar events** (ramp > 5x, range >= 1.5x ATR). Real intraday momentum is often:
- **Gradual**: No single bar explodes, but 10-40 consecutive bars grind in one direction
- **Average volume**: 0.87x-1.34x day average -- NOT the 5x+ ramp MC requires
- **Multi-hour**: 40 minutes to 3+ hours, not a single bar event
- **VWAP-crossing**: Almost always involves crossing or rejecting VWAP

The SPY 10:30-13:40 move ($11.24, 11.82x ATR) is the archetype: 64% directional consistency, 0.87x average volume, no single bar stands out. MC is structurally blind to this.

---

## 5. The VWAP Counter-Trend Pattern (What Works Best)

### Discovery: Counter-VWAP BRK Signals
Price on the **opposite side of VWAP** from the breakout direction. Example: price below VWAP, breaks UP through key level. This is a pullback-to-key-level pattern.

### Core Stats (n=36, 10 symbols, 26 days)

| | Counter | Best Aligned | All Aligned |
|---|---|---|---|
| n | 36 | 350 | 2,178 |
| MFE | 1.154 | 1.232 | 0.783 |
| MAE | **0.223** | 0.958 | 0.791 |
| MFE/MAE | **5.17x** | 1.29x | 0.99x |
| Win% | **83.3%** | 52.9% | 48.8% |

**Statistically significant:** p = 0.000019 (binomial), p = 0.000166 (Mann-Whitney U). Bootstrap 95% CI: [69.4%, 94.4%].

### Why It Works
The key insight: when price has overshot past VWAP against the trend, the subsequent level break is a **trend resumption** signal with minimal drawdown (median MAE only 0.110 ATR). EMA confirms the trend, VWAP overshoot creates the entry, level break confirms resumption.

### Best Variants
- Bear counter at Yesterday Low, 10:xx: 92% win, best MFE
- Overall: bear counter (92%) > bull counter (78%)
- Yest H/L levels (89%) > PM H/L levels (67%)
- 10:xx (83%, MFE 2.023) > 9:xx (82%, MFE 1.022)

### Counter-VWAP Applied to MC Signals
At 9:35 specifically, **counter-VWAP MC signals have 93% CONF pass rate** vs 72% for VWAP-aligned. The "obvious" with-trend MC at 9:35 is a trap.

After 9:50: counter-VWAP MC trades have **+0.118 ATR expectancy** (best MC subgroup) vs +0.012 for VWAP-aligned.

### Frequency
~1-2 counter-VWAP BRK signals per week across all symbols. 22% of trading days have at least one.

---

## 6. Time-of-Day Patterns

### MC/Big Move Data

| Time | MC Count | Runner% (big moves) | Avg MFE (big moves) |
|------|---------|---------------------|---------------------|
| 9:30-10:00 | 1,202 (99.4%) | 70-92% | 2.35 |
| 10:00-11:00 | ~0 | 69-84% | 1.44-1.75 |
| 11:00-12:00 | ~0 | 57-85% | 1.27-1.71 |
| 12:00-14:00 | ~0 | 60-84% | 1.26-1.42 |
| 14:00-16:00 | ~0 | 49-84% | 1.41 |

### Key Timing Findings

1. **9:30-9:50 is noise for MC.** Direction from 9:50-10:20 matches 30-min outcome 79% of time. The opening auction is genuinely random.

2. **9:30-10:00 has best runner rate** (70-92%) and best MFE (2.35 ATR) for big moves -- but MC fires on noise there, not the real moves.

3. **10:00-11:00 still excellent** for big moves (69% runner, 1.75 MFE). This is the window MC is completely missing.

4. **14:00-16:00 is the fakeout zone.** 11 of top 20 fakeouts cluster at 15:00-15:50. Runner rate drops to 49%. End-of-day reversals dominate.

5. **Afternoon CONF = 0% GOOD.** From signal analysis: afternoon signals have 49% CONF rate but 0% GOOD follow-through. High CONF but zero quality.

6. **The ideal trade template fires at 9:30-10:00** but the 5-minute checkpoint at 5 minutes post-signal is what validates it.

### 9:50 Gate Recommendation
The v29 analysis concluded: **suppress MC before 9:50 ET.** This preserves the once-per-session slot for the real move. But the slot recovery analysis showed that only 7 MC signals would ever fire after 9:50 even with open slots -- the criteria are too extreme for post-open bars.

---

## 7. Raw Ideas for MC Redesign

### Problem Summary
MC in its current form is fundamentally broken:
1. Fires 99.4% of the time on opening noise (9:30-9:45)
2. Burns once-per-session slots on coin-flip direction calls
3. Even with a 9:50 gate, only 7 signals would fire post-open (criteria too extreme)
4. Misses the actual big intraday moves (gradual grinds, multi-bar trends)
5. Volume ramp > 5x almost never occurs after 9:50

### Ideas From Data

**A. Replace Single-Bar Ramp With Multi-Bar Momentum**
The missed moves show: real momentum is 10-40 bars of directional consistency, not one explosive bar. Instead of ramp > 5x on ONE bar, detect:
- N of last M bars in same direction (e.g., 7/10 bars up)
- Cumulative move > X ATR over last N bars
- This would catch the SPY 10:30-13:40 grind (64% directional consistency)

**B. VWAP Cross + Momentum = New Signal**
All 6 missed moves on March 3 had VWAP crossings. A signal that fires on VWAP cross WITH directional momentum behind it would catch these. Combine: VWAP crossed + last N bars directional + EMA aligned.

**C. Counter-VWAP as Primary Quality Filter**
After 9:50, counter-VWAP signals have +0.118 ATR expectancy (best subgroup). Instead of MC being a volume signal, make it a counter-VWAP momentum signal: detect trend resumption after VWAP overshoot.

**D. Lower Ramp Threshold, Add Time Filter**
Current: ramp > 5x (almost never post-open). Alternative: ramp > 2x + time > 9:50 + EMA aligned. Would generate more signals but need quality filter. QBS already fires post-9:50 with lower thresholds.

**E. Cumulative Volume Approach**
Instead of single-bar volume spike, detect cumulative volume over N bars exceeding threshold. Trending moves accumulate volume even when no single bar spikes.

**F. 5-Minute Gate as Confirmation**
The 5-min P&L is the single strongest predictor of runner vs fakeout (93% accuracy when > +0.05 ATR + EMA + VWAP). Instead of MC auto-confirming at signal time, delay confirmation by 5 minutes and check price action.

**G. Directional Pressure Score**
Count bars-in-direction over a rolling window. When score exceeds threshold AND price is crossing/near VWAP, fire a "momentum building" signal. This would detect the grinding trends MC misses.

**H. The "Level Desert" Solution**
After all key levels are broken, MC-style signals become the only way to generate signals. A redesigned MC that detects momentum continuation (not just volume spikes) would fill this gap.

### The VWAP Counter-Trend Insight (Most Actionable)
The counter-VWAP BRK finding (83% win, 5.17x MFE/MAE, p < 0.0002) suggests the best "momentum" signal is actually a mean-reversion setup:
- Trend intact (EMA aligned)
- Price overshoots past VWAP (counter-trend dip)
- Key level break confirms resumption
- This isn't MC-style "momentum cascade" -- it's a pullback continuation pattern

### What NOT to Do
- Don't try smart filtering of opposing MC pairs at open (counter-VWAP accuracy: 62%, but trade expectancy still negative before 9:50)
- Don't raise MC thresholds further (already only 7 post-9:50 signals)
- Don't rely on ADX to filter MC (only validates for 4/12 symbols)
- Don't use body% as quality filter (inverse relationship: high body = fakeout)

---

## Appendix: Data Sources & Counts

| Source | n | Coverage |
|--------|---|----------|
| MC signals parsed | 1,209 | 10 symbols, Sep 2025 - Mar 2026 |
| MC opposing pairs | 126 | SPY/QQQ/AMD/AAPL |
| MC-confirmed trades | 421 | With PnL |
| Solo MC days | 531 | One direction only |
| Big move bars (all) | 9,596 | 13 symbols, Jan-Mar 2026 |
| Big moves (2x ATR) | 2,069 | 13 symbols, Dec 2025 - Mar 2026 |
| Counter-VWAP BRKs | 36 | 10 symbols, 26 days |
| Missed moves (Mar 3) | 6 | 4 symbols, 1 day |
| QBS signals | 87 | 10 symbols |
| Total BRK signals | 1,575 | 10 symbols |
| Signal analysis (enriched) | 1,841 | 13 symbols |

### Key Files
- `v28a-signal-audit.md` -- Full signal audit (7044 signals)
- `v28a-mc-analysis.md` -- MC opposing pairs (126 pairs)
- `v28b-mc-smart-filter.md` -- 14-dimension smart filter research
- `v28a-vwap-counter-analysis.md` -- VWAP counter-trend BRK (n=36, 83% win)
- `v29-mc-gate-analysis.md` -- MC 9:50 gate P&L analysis
- `v29-mc-slot-recovery.md` -- Slot recovery (only 7 would fire)
- `2026-03-03-missed-moves.md` -- 6 missed multi-ATR moves
- `big-move-fingerprint.md` -- 9596 bar fingerprint
- `multisym-bigmove-fingerprint.md` -- 2069 big moves, 13 symbols
- `deep-analysis-findings.md` -- Master analysis findings
