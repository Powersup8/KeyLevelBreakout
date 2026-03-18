# Plan: v2.4 Gap Analysis with 5s Candle Data

## Context

We have 6 open analysis gaps from the v2.4 master analysis (2,588 signals, 28 days, 13 symbols). Before making any more code changes to KeyLevelBreakout.pine, we want to close these gaps so decisions are evidence-based. We now have access to **5-second candle data** (from IB, parquet format) which gives 12x finer resolution than the previous 1m CSV data.

## What We're Building

**One Python script:** `debug/v24_gap_analysis.py`
**Output:** `debug/v24-gap-analysis.md`

## Data Sources

### Pine Logs (13 files, v2.4 with VWAP field)
- Located in `debug/pine-logs-Key Level Breakout_*.csv`
- Auto-detect symbol from first signal line (close price + ATR fingerprint)
- Reuse parsing patterns from `debug/pattern_mining.py` and `debug/follow_through.py`

### 5s Candles (11 of 13 symbols, parquet)
- Located in `/Users/mab/.../trading_bot/cache/bars_highres/5sec/{sym}_5_secs_ib.parquet`
- Columns: date, open, high, low, close, volume, average, barCount
- Coverage: Dec 11 – Feb 25 (covers 27 of 28 signal days)
- **Missing:** TSM (no file), GLD (ends Feb 4 — partial)

## The 6 Analyses

### Gap A: Jan 29 Cross-Validation
- **Question:** Do our key findings hold without the monster day (14 of top-20 signals)?
- **Method:** Run core metrics (CONF rate by time/volume/level) twice: full dataset vs. excluding Jan 29. Show deltas.
- **Data:** Pine logs only (no candle join needed)

### Gap B: Day-of-Week Effects
- **Question:** Do Monday/Friday differ from mid-week?
- **Method:** Group signals by weekday (Mon–Fri). Show: signal count, CONF rate, ✓★ count.
- **Data:** Pine logs only

### Gap C: Symbol × Time Interactions
- **Question:** Does AMZN have a different optimal window than SPY?
- **Method:** 2D pivot table — symbol rows × time-bucket columns (9:30-10, 10-11, 11-13, 13-16). Show CONF rate per cell. Highlight cells that deviate >10pp from column average.
- **Data:** Pine logs only

### Gap D: Reclaim (~~ ) Deep Dive
- **Question:** Why are reclaims 8.1% GOOD / 8.1% BAD? What predicts a good reclaim?
- **Method:** For each ~~ signal, measure:
  - Time elapsed since the prior BRK that it reclaims
  - Volume at reclaim vs volume at original BRK
  - 5s MFE/MAE at 30s, 1m, 2m, 5m, 15m, 30m windows
  - Group by: time-since-BRK bucket, volume bucket, level type
- **Data:** Pine logs + 5s candles

### Gap E: Multi-Level Breakout Quality
- **Question:** Does "PM H + Yest H" confluence actually boost follow-through (not just CONF)?
- **Method:** Compare single-level vs multi-level signals on:
  - CONF rate (from pine logs — already known: +4.7pp)
  - 5s MFE/MAE at 5m and 30m windows (NEW — measures actual move quality)
  - GOOD/BAD classification using 5s data
- **Data:** Pine logs + 5s candles

### Gap F: Counter-Trend Confidence Interval
- **Question:** Is 75 counter-trend signals enough to trust "10% CONF"?
- **Method:** Wilson score 95% confidence interval on proportion. Report: point estimate, CI bounds, required sample size for ±5pp precision.
- **Data:** Pine logs only (arithmetic)

## Script Architecture

```
1. PARSE pine logs (reuse regex patterns from pattern_mining.py)
   - Auto-map files to symbols via price fingerprinting
   - Extract: timestamp, type, direction, levels, vol, pos, vwap, ATR, close, conf result

2. LOAD 5s candles (parquet via pandas + pyarrow)
   - Only for the 11 available symbols
   - Index by datetime for fast lookup
   - Filter to regular trading hours (9:30-16:00 ET)

3. COMPUTE 5s MFE/MAE (reuse logic from follow_through.py, adapted for 5s)
   - Windows: 30s (6 bars), 1m (12), 2m (24), 5m (60), 15m (180), 30m (360)
   - Entry price = signal close price from pine log
   - Bull: MFE = max(high) - entry, MAE = entry - min(low)
   - Bear: MFE = entry - min(low), MAE = max(high) - entry
   - Normalize by ATR

4. RUN 6 analyses (A through F)

5. WRITE results to debug/v24-gap-analysis.md
```

## Key Reuse from Existing Scripts

- **Multi-line CSV joining:** from `pattern_mining.py` lines 44-58
- **Signal regex:** from `follow_through.py` line ~90 (handles BRK/~/~~, vol, pos, vwap, OHLC, ATR)
- **CONF regex:** from `follow_through.py` line ~91
- **MFE/MAE computation logic:** from `follow_through.py` (adapted from 1m to 5s windows)
- **Classification thresholds:** GOOD = MFE > 0.5 ATR & MFE > 2x MAE in 30m; BAD = MAE > 0.5 ATR in 15m

## Verification

1. Run: `python3 debug/v24_gap_analysis.py`
2. Check output file has all 6 sections (A-F)
3. Sanity check: total signal count should be ~2,500+ (matching v2.4 master analysis)
4. Sanity check: overall CONF rate should be ~51% (matching v2.4)
5. Compare 5s-based GOOD/BAD rates with previous 1m-based rates — should be similar or slightly higher (finer data captures more extremes)
