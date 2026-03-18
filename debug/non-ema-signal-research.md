# Non-EMA Signal Research Report

_Generated: 2026-03-05 09:55_

## Context

**Problem:** 62% of significant intraday moves (15,798 moves, 27,299 ATR over 451 days) happen WITHOUT EMA alignment. Our current breakout/reversal entry loses money in these conditions:
- Non-EMA entry: **33% win, -0.120 ATR/signal**
- EMA-aligned entry: **57% win, +0.086 ATR/signal**

The moves ARE there (avg MFE 0.202 ATR) but MAE is huge (0.322 ATR) — we enter too early.

**Goal:** Find signal types profitable in non-EMA conditions. Benchmark: EMA-aligned baseline = 57% win, +0.086 ATR/signal.

**Data:** 5m parquet, full history (Jan 2024 – Mar 2026), 13 symbols. RTH only (9:30–16:00 ET).

**Backtest method:** Entry at signal bar close. Track MFE and MAE over next 6 bars (30 min). Win = MFE > |MAE|. P&L = MFE + MAE (MAE is negative).

## 1. Pre-Move Characterization

Analyzed **15,798 non-EMA moves** across 13 symbols (prior 12-bar window = 1 hour).

| Feature | Value |
|---------|-------|
| Volume pattern: RAMP | 36.8% |
| Volume pattern: DRY | 32.5% |
| Volume pattern: FLAT | 30.7% |
| Avg EMA spread (ATR) | 1.519 |
| EMA converging | 54.8% |
| At range high | 19.6% |
| At range low | 13.5% |
| Avg VWAP deviation (ATR) | 1.736 |
| Avg RSI | 50.6 |
| Avg ADX | 26.2 |

### Key Pre-Move Observations

- **Volume:** The most common pattern before a non-EMA move is volume RAMP (36.8%).
- **EMA configuration:** Average EMA spread = 1.519 ATR. 54.8% of pre-move windows show EMAs converging (shrinking spread).
- **VWAP proximity:** Average deviation = 1.736 ATR. Extended from VWAP (> 0.5 ATR).
- **Momentum state:** RSI avg 50.6 (neutral = 50), ADX avg 26.2 (moderate trend).

## 2. Signal Backtest Results

Ranked by avg P&L per signal (ATR). Benchmark: EMA-aligned = 57% win, +0.086 ATR/signal.

| Rank | Signal Type | N | Win% | Avg P&L | Total P&L | MFE | MAE | Coverage% |
|------|------------|---|------|---------|-----------|-----|-----|-----------|
| 1 | J_Morning_Gap_Fade | 2 | 100.0% | +4.118 | 8.2 | 4.420 | -0.302 | 0.1% |
| 2 | K_Combo_Vol_Range | 2,062 | 49.0% | +0.144 | 297.3 | 2.572 | -2.428 | 2.7% |
| 3 | F_EMA_Cross | 23,825 | 49.1% | +0.022 | 515.6 | 1.527 | -1.505 | 23.1% |
| 4 | H_VWAP_Cross | 3,657 | 48.8% | +0.021 | 78.5 | 2.330 | -2.309 | 3.6% |
| 5 | B_Range_Breakout | 6,714 | 48.4% | +0.001 | 3.9 | 2.277 | -2.276 | 5.2% |
| 6 | A_EMA_Conv_Break | 3,780 | 47.5% | -0.030 | -112.5 | 1.505 | -1.534 | 2.8% |
| 7 | G_RSI_Momentum_Flip | 20,762 | 48.4% | -0.049 | -1020.8 | 1.480 | -1.529 | 14.6% |
| 8 | M_Combo_RSI_VWAP | 4,823 | 48.5% | -0.055 | -263.7 | 1.482 | -1.537 | 4.5% |
| 9 | C_VWAP_Dev_Reversal | 31,188 | 48.7% | -0.058 | -1804.6 | 1.454 | -1.512 | 18.1% |
| 10 | D_Momentum_Shift | 6,002 | 49.0% | -0.087 | -522.7 | 1.393 | -1.480 | 6.3% |
| 11 | E_Volume_Spike_Dir | 3,688 | 48.0% | -0.168 | -619.4 | 2.448 | -2.616 | 3.7% |
| 12 | L_Combo_EMA_Conv_Vol | 512 | 44.7% | -0.350 | -179.0 | 2.338 | -2.687 | 0.7% |

## 3. Signal-by-Signal Analysis

### J. Morning Gap Fade

**Rationale:** At the 9:35 bar, if price gapped >0.5 ATR from prior close, fade the gap direction. Non-EMA only. Hypothesis: gaps without EMA alignment tend to fill.

**Verdict:** PROFITABLE
- N signals: 2
- Win rate: 100.0% (benchmark: 57%)
- Avg P&L: +4.118 ATR/signal (benchmark: +0.086)
- Total P&L: +8.2 ATR
- MFE/MAE: 4.420 / -0.302
- Coverage of known non-EMA moves: 0.1%

### K. Combo: Range Break + Vol Spike

**Rationale:** Range breakout (1hr H/L) AND volume ≥3x spike on same bar. More selective than B alone.

**Verdict:** PROFITABLE
- N signals: 2,062
- Win rate: 49.0% (benchmark: 57%)
- Avg P&L: +0.144 ATR/signal (benchmark: +0.086)
- Total P&L: +297.3 ATR
- MFE/MAE: 2.572 / -2.428
- Coverage of known non-EMA moves: 2.7%

### F. EMA9 x EMA20 Cross

**Rationale:** Classic trend change signal — EMA9 crosses EMA20. These fire naturally when EMAs just crossed (pre-full-alignment). Hypothesis: catch the regime change early.

**Verdict:** PROFITABLE
- N signals: 23,825
- Win rate: 49.1% (benchmark: 57%)
- Avg P&L: +0.022 ATR/signal (benchmark: +0.086)
- Total P&L: +515.6 ATR
- MFE/MAE: 1.527 / -1.505
- Coverage of known non-EMA moves: 23.1%

### H. VWAP Cross + Volume

**Rationale:** Price crosses VWAP with volume ≥1.5x confirmation. Non-EMA bars only. Hypothesis: VWAP is the institutional equilibrium — crossing it with volume = directional intent.

**Verdict:** PROFITABLE
- N signals: 3,657
- Win rate: 48.8% (benchmark: 57%)
- Avg P&L: +0.021 ATR/signal (benchmark: +0.086)
- Total P&L: +78.5 ATR
- MFE/MAE: 2.330 / -2.309
- Coverage of known non-EMA moves: 3.6%

### B. 1-Hour Range Breakout

**Rationale:** Price breaks above/below the prior 12-bar (1-hour) H/L with volume ≥1.5x. No EMA requirement. Hypothesis: range compression → expansion regardless of trend direction.

**Verdict:** PROFITABLE
- N signals: 6,714
- Win rate: 48.4% (benchmark: 57%)
- Avg P&L: +0.001 ATR/signal (benchmark: +0.086)
- Total P&L: +3.9 ATR
- MFE/MAE: 2.277 / -2.276
- Coverage of known non-EMA moves: 5.2%

### A. EMA Convergence Break

**Rationale:** EMAs bunching together (spread < 0.2 ATR) then price breaks out of the cluster. Hypothesis: EMA alignment is ABOUT to happen — catch the start before the system would normally detect it.

**Verdict:** LOSING
- N signals: 3,780
- Win rate: 47.5% (benchmark: 57%)
- Avg P&L: -0.030 ATR/signal (benchmark: +0.086)
- Total P&L: -112.5 ATR
- MFE/MAE: 1.505 / -1.534
- Coverage of known non-EMA moves: 2.8%

### G. RSI 50-Line Cross

**Rationale:** RSI crosses 50 from below (bull) or above (bear) — momentum regime change. Simple but robust. Hypothesis: RSI 50 cross = momentum shift that precedes price follow-through.

**Verdict:** LOSING
- N signals: 20,762
- Win rate: 48.4% (benchmark: 57%)
- Avg P&L: -0.049 ATR/signal (benchmark: +0.086)
- Total P&L: -1020.8 ATR
- MFE/MAE: 1.480 / -1.529
- Coverage of known non-EMA moves: 14.6%

### M. Combo: RSI 50 Cross + VWAP Cross

**Rationale:** Both RSI crosses 50 AND price crosses VWAP on same bar. Very selective, two independent momentum signals aligning.

**Verdict:** LOSING
- N signals: 4,823
- Win rate: 48.5% (benchmark: 57%)
- Avg P&L: -0.055 ATR/signal (benchmark: +0.086)
- Total P&L: -263.7 ATR
- MFE/MAE: 1.482 / -1.537
- Coverage of known non-EMA moves: 4.5%

### C. VWAP Deviation Reversal

**Rationale:** Price moves >1 ATR from VWAP (extended), then the next bar closes back toward VWAP. Hypothesis: mean-reversion trade when too extended from equilibrium.

**Verdict:** LOSING
- N signals: 31,188
- Win rate: 48.7% (benchmark: 57%)
- Avg P&L: -0.058 ATR/signal (benchmark: +0.086)
- Total P&L: -1804.6 ATR
- MFE/MAE: 1.454 / -1.512
- Coverage of known non-EMA moves: 18.1%

### D. 3-Bar Momentum Flip

**Rationale:** 3 consecutive bars in new direction after 2 bars in opposite direction. Hypothesis: catches the turn rather than the breakout — good for choppy non-trending conditions.

**Verdict:** LOSING
- N signals: 6,002
- Win rate: 49.0% (benchmark: 57%)
- Avg P&L: -0.087 ATR/signal (benchmark: +0.086)
- Total P&L: -522.7 ATR
- MFE/MAE: 1.393 / -1.480
- Coverage of known non-EMA moves: 6.3%

### E. Volume Spike + Direction

**Rationale:** Volume >3x average on a bar that moves >0.3 ATR in one direction. Hypothesis: unusually high volume on a directional bar = smart money showing hand.

**Verdict:** LOSING
- N signals: 3,688
- Win rate: 48.0% (benchmark: 57%)
- Avg P&L: -0.168 ATR/signal (benchmark: +0.086)
- Total P&L: -619.4 ATR
- MFE/MAE: 2.448 / -2.616
- Coverage of known non-EMA moves: 3.7%

### L. Combo: EMA Convergence + Vol

**Rationale:** EMA convergence break AND volume ≥2x. Adds volume confirmation to signal A.

**Verdict:** LOSING
- N signals: 512
- Win rate: 44.7% (benchmark: 57%)
- Avg P&L: -0.350 ATR/signal (benchmark: +0.086)
- Total P&L: -179.0 ATR
- MFE/MAE: 2.338 / -2.687
- Coverage of known non-EMA moves: 0.7%

## 4. Rankings by P&L

Only signals with positive P&L are worth implementing:

### Profitable Signals

| Signal | N | Win% | Avg P&L | Coverage% |
|--------|---|------|---------|-----------|
| J_Morning_Gap_Fade | 2 | 100.0% | +4.118 | 0.1% |
| K_Combo_Vol_Range | 2,062 | 49.0% | +0.144 | 2.7% |
| F_EMA_Cross | 23,825 | 49.1% | +0.022 | 23.1% |
| H_VWAP_Cross | 3,657 | 48.8% | +0.021 | 3.6% |
| B_Range_Breakout | 6,714 | 48.4% | +0.001 | 5.2% |

### Losing Signals (avoid)

| Signal | N | Win% | Avg P&L |
|--------|---|------|---------|
| A_EMA_Conv_Break | 3,780 | 47.5% | -0.030 |
| G_RSI_Momentum_Flip | 20,762 | 48.4% | -0.049 |
| M_Combo_RSI_VWAP | 4,823 | 48.5% | -0.055 |
| C_VWAP_Dev_Reversal | 31,188 | 48.7% | -0.058 |
| D_Momentum_Shift | 6,002 | 49.0% | -0.087 |
| E_Volume_Spike_Dir | 3,688 | 48.0% | -0.168 |
| L_Combo_EMA_Conv_Vol | 512 | 44.7% | -0.350 |

## 5. Recommendation

### Best Statistically Reliable Signal: K_Combo_Vol_Range
- N=2,062 signals, 49.0% win, avg P&L +0.144 ATR/signal
- Total P&L across all symbols: +297.3 ATR
- Covers 2.7% of known non-EMA moves
- **EXCEEDS benchmark** (0.086 ATR/signal). Strong implementation candidate.


**Note on J_Morning_Gap_Fade (top raw rank):** N=2 signals over 2 years = statistically meaningless.
The 100% win rate on 2 trades is noise. Not implementation-ready without much more data.

## 6. Comparison to EMA-Aligned Baseline

| Metric | EMA-Aligned (existing) | Best Reliable Non-EMA Signal |
|--------|----------------------|-----------------------------|
| Win rate | 57% | 49.0% |
| Avg P&L | +0.086 ATR | +0.144 ATR |
| N (per 2yr, all symbols) | ~1,841 total | 2,062 |
| Total P&L | — | +297.3 ATR |
| Verdict | Production ready | Implement (exceeds benchmark) |

## 7. Implementation Recommendation for Pine Script

**Signal to implement: K_Combo_Vol_Range**

This signal type **exceeds the EMA-aligned benchmark** (+0.144 vs +0.086 ATR/signal) with N=2,062 — statistically robust.

Pine Script implementation sketch:
```pine
// K: Range Breakout + Volume Spike (non-EMA)
// Prerequisites: not ema_aligned, RTH hours
roll_high = ta.highest(high, 12)[1]  // prior 12-bar high
roll_low  = ta.lowest(low, 12)[1]   // prior 12-bar low
vol_spike = volume / ta.sma(volume, 20) >= 3.0
ema_not_aligned = not (ema9 > ema20 and ema20 > ema50) and not (ema9 < ema20 and ema20 < ema50)
non_ema_brk_bull = close > roll_high and vol_spike and ema_not_aligned
non_ema_brk_bear = close < roll_low  and vol_spike and ema_not_aligned
```

## 8. Key Findings Summary

1. **Non-EMA conditions are genuinely difficult.** Win rates cluster around 48-49% for almost all signal types — essentially a coin flip vs the 57% baseline for EMA-aligned signals.
2. **Volume is the key differentiator.** The only signal that beat the benchmark (K: Range Break + Vol Spike ≥3x) adds volume as the primary filter. Volume is signal; direction alone is noise in non-EMA conditions.
3. **Pre-move: EMAs are already spread, not converging.** Avg EMA spread = 1.52 ATR (large), and 54.8% are actively converging — suggesting the move is a re-alignment event, not a continuation.
4. **VWAP is far away.** Avg deviation = 1.74 ATR — price is already extended from VWAP when non-EMA moves begin. This kills VWAP-based mean-reversion signals.
5. **EMA convergence break is a TRAP.** Signal A fired 3,780 times and lost money. Converging EMAs + breakout = whipsaw, not follow-through.
6. **Volume spike + direction is also a TRAP (-0.168 ATR).** High volume spikes in non-EMA conditions signal exhaustion/reversal, not continuation — consistent with our big-move fingerprint findings (vol ≥2x = more fakeouts).
7. **EMA Cross (F) fires 23,825 times** and barely breaks even (+0.022 ATR). It has the highest coverage (23.1% of known moves) but weak edge. Useful for timing only if combined with other filters.

---
_Research script: `debug/non_ema_signal_research.py`_