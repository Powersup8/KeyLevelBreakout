# Profitability Research: Minimizing MAE, Maximizing MFE

> Based on 1,748 signals, 13 symbols, 28 days. Grounded in our v2.4 data + academic/practitioner research.

---

## 1. What Predicts Big Runners vs Small Moves?

Our data reveals a paradox: CONF checkmark has the highest average GOOD MFE (0.94 ATR) while gold-star has lower (0.65 ATR), despite gold-star having 3x the GOOD rate (27% vs 10%).

**Why checkmark produces bigger moves:** Gold-star fires on the breakout candle itself (auto-promote = instant CONF). The move has already partially happened. Checkmark signals pass CONF later -- they are the breakouts that initially looked weaker but then built a base and launched. By the time CONF fires, institutional positioning is complete and the move accelerates from a stronger foundation.

**Runner characteristics from our data:**
- **LOW levels dominate:** Yest L GOOD moves avg 0.74 ATR, PM L avg 0.845 ATR (max 3.63 ATR). LOW levels mean the stock is being pushed DOWN through support -- when it bounces, shorts cover AND new longs pile in = double fuel.
- **GLD outlier:** 1.39 ATR avg GOOD MFE. GLD trends in sustained moves once it breaks. Fewer HFT algos hunting stops on commodity ETFs.
- **10:00-11:00 window:** MFE/MAE ratio peaks at 1.29 here. The open's noise has settled, real institutional flow is visible, and there is enough session left for moves to develop.
- **2-5x volume:** 58% CONF, 7.1% GOOD. The sweet spot. Below 2x = no conviction. Above 10x = opening-bar noise that reverses fast.

**Key insight:** The biggest runners share three traits: (1) they break LOW levels, (2) they occur at 2-5x volume, (3) they happen between 10:00-11:00. When all three align, you have a high-probability runner.

---

## 2. How to Minimize Counter-Movement (MAE)

Our BAD signals reach 0.30 ATR adverse by minute 5 and 0.60 ATR by minute 15. This is fast -- if a trade is going to fail, you know within 5 minutes. This creates a practical rule.

**What our data says about low-MAE setups:**
- **CONF checkmark:** Average MAE = 0.075 ATR (vs 0.256 for fails). The single best MAE filter.
- **10:00-11:00 window:** Only 1.6% BAD (vs 10.6% at 9:30-10:00). Morning noise is gone.
- **LOW levels:** Yest L has 3.3% BAD vs Yest H at 6.9%. LOW levels have natural support from the buyers who just pushed through.
- **TSLA:** 1.3% BAD -- lowest of all symbols. TSLA's wide ATR gives more room before a stop triggers.

**Academic support (2025-2026 research):**
- Breakouts entering low-liquidity zones have longer continuation and less retracement ([Mittal & Choudhary, SSRN 2026](https://papers.ssrn.com/sol3/Delivery.cfm/5962358.pdf?abstractid=5962358)).
- ATR trailing stops between 1.5-2.0x ATR provide optimal balance for short-term momentum plays ([LuxAlgo](https://www.luxalgo.com/blog/5-atr-stop-loss-strategies-for-risk-control/)).
- Pullback entries after initial breakout reduce risk of false signals vs immediate entries ([TradeFundrr](https://tradefundrr.com/breakout-pullback-entry-method/)).

**Practical MAE reduction rules:**
1. **5-minute stop rule:** If MAE exceeds 0.15 ATR within 5 minutes, exit. GOOD signals average only 0.059 ATR MAE at 30 minutes -- they simply do not draw down much.
2. **Wait for CONF:** Trading only after CONF checkmark gives 0% BAD. The wait costs you some upside (you miss the initial 5m candle move) but eliminates catastrophic adverse excursion.
3. **Skip 9:30-10:00 unless gold-star:** This window has 10.6% BAD rate. Reserve it for the clearest setups only.

---

## 3. Can We Predict Checkmark BEFORE Confirmation?

This is the key question. CONF checkmark = 0% BAD, 0.94 ATR GOOD MFE. If we could identify which BRK signals will get checkmark before it fires, we could enter earlier and capture more of the move.

**What predicts CONF pass (from our data):**
- With-trend VWAP: 54% CONF vs 10% counter-trend (+44pp). Already implemented.
- 2-5x volume: 58% CONF. Already used for gold-star tier.
- 10:00-11:00 time: 60% CONF vs 45% at open. Not currently used as a CONF predictor.
- Yest L level: 60% CONF. The highest-CONF level.
- A-tier symbols (AMZN/QQQ/SPY): 59-62% CONF.

**Pre-CONF conviction score (proposed):**
Stack the factors. A BRK signal gets a point for each:
1. With-trend VWAP (already required)
2. Volume 2-5x (sweet spot)
3. Time 10:00-11:00
4. LOW level (Yest L, PM L, ORB L, Week L)
5. A/B-tier symbol (not AMD/MSFT/GLD)

Score 4-5 = very likely to confirm. Score 0-2 = likely to fail. This is not something to code into the indicator -- it is a mental checklist for trade decisions.

---

## 4. Practical Indicator Improvements (Pine Script)

Based on the data and research, here are 5 actionable improvements ranked by effort and impact:

### 4a. Time-Based Dimming Enhancement (LOW effort, HIGH impact)
Currently afternoon signals are dimmed after 11:00. Enhance to show time-tier context:
- 9:30-10:00 signals: add subtle warning marker (high variance window)
- 10:00-11:00 signals: highlight as prime window (perhaps a subtle outline or brighter color)
- This requires only label color logic changes, ~10 lines.

### 4b. "Runner Score" Label Suffix (MEDIUM effort, HIGH impact)
Add a numeric score (1-5) based on the conviction stack from Section 3. Display as a small number on the label (e.g., "BRK PM L 4"). This gives instant visual triage without mental calculation.
- Factors: VWAP aligned, vol 2-5x, time 10-11, LOW level, good symbol
- ~30-40 lines of logic to compute and display.

### 4c. ATR Trailing Stop Lines (MEDIUM effort, MEDIUM impact)
After CONF fires, draw a trailing stop line at entry minus 0.15 ATR (for longs). Trail it upward as price moves. This gives a clear visual exit level.
- Uses `line.new()` in Pine, auto-updates each bar
- ~40-50 lines. Requires tracking entry price per signal.

### 4d. 5-Minute MAE Alert (LOW effort, HIGH impact)
After a BRK signal fires, if price moves 0.15+ ATR against the signal within 5 bars (on 1m chart = 5 minutes), fire an alert or mark the label as failed early. This implements the "5-minute stop rule" from Section 2.
- Could be done as a simple bar-count tracker after signal, ~20 lines.
- Would need to track the BRK price and direction.

### 4e. Multi-Level Confluence Highlight (LOW effort, MEDIUM impact)
When a breakout hits 2+ levels simultaneously (e.g., "Yest L + Week L"), highlight it more prominently. Multi-level breakouts are rarer but represent stronger conviction.
- Already partially shown in label text. Just enhance the visual (e.g., larger label size for 2+ levels).
- ~5-10 lines.

---

## 5. Stop and Profit Management Framework

### Entry
- **Primary:** Enter on BRK signal, 2-5x volume, with-trend VWAP, 10:00-11:00, LOW level.
- **Confirmation:** After CONF checkmark, add to position (scale in). After CONF gold-star, go to full size.
- **Alternative (pullback entry):** If BRK fires but you miss it, wait for a 1-2 minute pullback toward the breakout level. Research shows pullback entries have tighter MAE and similar MFE. Our retest logic already captures this.

### Initial Stop
- **0.15 ATR** from entry. Our GOOD signals have avg MAE of 0.059 ATR -- a 0.15 ATR stop gives 2.5x breathing room while cutting true BAD signals (which hit 0.30 ATR by minute 5).

### Trailing Stop (based on ATR research)
- After 5 minutes in profit: trail at entry minus 0.10 ATR (tighten from 0.15)
- After 15 minutes in profit: trail at highest price minus 0.15 ATR
- After 30 minutes: trail at highest price minus 0.20 ATR (wider to let runners breathe)

### Profit Targets
- **Target 1:** 0.50 ATR (50% of GOOD threshold) -- take partial (1/3)
- **Target 2:** 0.75 ATR (average GOOD MFE at 30 min) -- take another 1/3
- **Runner:** Let final 1/3 ride with trailing stop. PM L signals average 0.845 ATR, GLD averages 1.39 ATR.

### Time Stop
- **30-minute max hold** for standard signals. MFE/MAE ratio peaks at 30 min (12.6x).
- **60-minute exception** for gold-star signals at LOW levels -- these have the runway for extended moves.

---

## 6. Priority Recommendations

| Priority | Action | Expected Impact | Effort |
|----------|--------|----------------|--------|
| 1 | **Use 5-min stop rule (0.15 ATR)** | Cuts BAD losses by ~50% | Execution discipline only |
| 2 | **Focus 10:00-11:00 window** | 60% CONF, 1.6% BAD | Execution discipline only |
| 3 | **Prefer LOW levels always** | 12.7% GOOD vs 4.3% for HIGH | Execution discipline only |
| 4 | **Add Runner Score to labels** | Instant triage, faster decisions | ~30 lines Pine Script |
| 5 | **Add ATR trailing stop lines** | Visual exit management | ~50 lines Pine Script |
| 6 | **Scale-in on CONF checkmark** | Capture 0.94 ATR avg GOOD MFE safely | Execution discipline only |

The first three cost nothing to implement -- they are purely execution discipline. Items 4-5 are indicator enhancements. Item 6 is a position management technique.

---

## Sources

- [Liquidity-Driven Breakout Reliability (Mittal & Choudhary, SSRN 2026)](https://papers.ssrn.com/sol3/Delivery.cfm/5962358.pdf?abstractid=5962358)
- [ATR Stop-Loss Strategies (LuxAlgo)](https://www.luxalgo.com/blog/5-atr-stop-loss-strategies-for-risk-control/)
- [Breakout Pullback Entry Method (TradeFundrr)](https://tradefundrr.com/breakout-pullback-entry-method/)
- [Multi-Timeframe Trend-Confirmed Breakout Strategy (FMZQuant)](https://medium.com/@FMZQuant/multi-timeframe-trend-confirmed-quantitative-breakout-trading-strategy-6375e1e3f54c)
- [Intraday Breakout Strategies on NSE (Wang & Gangwar, SSRN 2025)](https://papers.ssrn.com/sol3/Delivery.cfm/5198458.pdf?abstractid=5198458)
- [FinLLM-B: LLMs and Breakout Trading (arXiv 2024)](https://arxiv.org/pdf/2402.07536)
