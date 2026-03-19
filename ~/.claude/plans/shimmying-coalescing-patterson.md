# KLB Move Catalog — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a comprehensive catalog of ALL tradeable moves (≥0.30 ATR) across 15 symbols over 500+ trading days — the foundation for all future signal research.

**Architecture:** Single Python script (`debug/build_move_catalog.py`) with 6 modular phases: load → levels → indicators → detect → enrich → classify. Two-pass zig-zag detection (0.30 ATR primary + 1.00 ATR large moves with parent-child linking). Outputs: parquet catalog (~46K moves), CSV summary, stats markdown.

**Tech Stack:** Python, pandas, numpy, parquet. IB 5m data (primary), 1m (MFE precision), daily (ATR/levels).

---

## Context

The v3.2 backtest revealed we need a better foundation for research. Current datasets are fragmented: `big-moves.csv` (9,596 significant bars), `enriched-signals.csv` (1,841 signals), `no-signal-zone-moves.csv` (25,304 unmapped moves). None captures full move context with levels, cross-symbol data, and pre/post patterns. This catalog unifies everything into one queryable dataset.

**Data scope:** 15 symbols × 511 common trading days (Feb 2024 – Mar 2026) = ~830K 5m bars → ~46K cataloged moves.

---

## Task 1: Data Loading & Indicators

**Files:** Create `debug/build_move_catalog.py`

**What to build:**
- Config block: paths, 15 symbols, thresholds (`MIN_ATR_MAG=0.30`, `REVERSAL_ATR=0.15`, `LARGE_ATR_MAG=1.00`)
- `load_data()`: Load 5m + daily parquet for all 15 symbols, convert Berlin→ET, filter RTH 9:30-16:00
- `compute_indicators()`: Add to 5m DataFrames: ATR14, EMA21, EMA50, VWAP (daily reset), ADX14, vol_sma20, vol_ratio, body_pct, range_atr

**Patterns to follow:**
- TZ conversion: `scan_major_moves.py` line 32-33
- ADX: `big_move_fingerprint.py` lines 20-30 (Wilder's ewm)
- VWAP: `missed_moves_scanner.py` (cumulative typical*vol / cumulative vol)

**Verify:** Print summary table — 15 symbols loaded, date range, bar counts, indicator NaN check.

---

## Task 2: Level Computation

**What to build:**
- `compute_levels(daily, bars_5m)` → dict `levels[symbol][date]` with all levels

**Levels (13 types):**

| Level | Source | Available |
|-------|--------|-----------|
| PD High/Low/Close/Mid | daily[date-1] | At open |
| PD Last Hr Low/High | 5m bars date-1 15:00-16:00 | At open |
| PM High/Low | 5m bars 04:00-09:30 (when available) | At open |
| ORB High/Low | 5m bars 9:30-10:00 | After 10:00 only |
| Today's Open | First RTH bar open | At open |
| Week High/Low | daily Mon..date-1 | At open |
| Week Open | Monday's open | At open |
| Month Open | 1st trading day of month | At open |

**Pattern:** `scan_major_moves.py` lines 159-189 for PD/ORB/PM levels.

**Verify:** Print level counts per symbol-day, spot-check SPY 2026-03-06 levels against known values.

---

## Task 3: Move Detection (Zig-Zag)

**What to build:**
- `detect_moves(bars_5m)` → list of move dicts

**Algorithm:** Adapted from `missed_moves_scanner.py` lines 134-279.

**Two-pass detection:**
1. Primary: MIN_ATR_MAG=0.30, reversal=0.15 ATR → ~46K moves
2. Large: MIN_ATR_MAG=1.00, reversal=0.50 ATR → ~10K moves
3. Link: child moves within large move time range get `parent_move_id`

**Per move, capture:** symbol, date, direction, start_idx, end_idx, peak_idx, start/end/peak price, magnitude_atr, magnitude_pct, duration_bars

**Verify:** Print move count per symbol, histogram of magnitudes, spot-check TSLA 2026-03-06 moves against known price action.

---

## Task 4: Context Enrichment

**What to build:**
- `enrich_context(moves, bars_5m, indicators, levels)` → adds ~35 context columns per move

**Context groups:**

| Group | Columns | Source |
|-------|---------|--------|
| Pre-move (5 bars before) | ema21_slope, ema21_position, vwap_position, vwap_dist_atr, adx, vol_avg_ratio, prev_move_dir, prev_move_mag, compression | Indicators + prior move |
| Trigger bar | body_pct, range_atr, vol_ratio, candle_type, ema_aligned, vwap_aligned | bars[start_idx] |
| During move | bars_to_peak, max_drawdown_atr, smoothness | bars[start:end] |
| Post-move | retracement_6/12/24bar, continuation_flag, reversal_magnitude | bars[end:end+24] |
| Level context | nearest_level_type, nearest_level_dist_atr, level_interaction, levels_within_05, n_levels_within_05 | levels dict |
| Day context | day_of_week, spy_daily_regime, gap_direction, gap_magnitude_atr | Daily data |

**Candle types:** big_body (≥70%), doji (<15%), hammer, shooting_star, marubozu (≥90%), indecisive

**Level interaction:** broke_through / bounced_off / no_interaction (based on 0.1 ATR proximity)

**Important:** ORB levels only available after 10:00 ET — check time before including.

**Verify:** Print NaN counts per column, spot-check 10 random moves for correctness.

---

## Task 5: Cross-Symbol Analysis & Classification

**What to build:**
- `cross_symbol_analysis(all_moves)` → adds spy_direction, spy_magnitude_atr, concurrent_symbols, is_broad_move
- `classify_moves(moves_df)` → adds 5 category columns

**Cross-symbol:** For each move, count other symbols with moves starting within ±15 min in same direction. SPY direction from 5-bar momentum at move start.

**Categories:**
- `mag_category`: small (0.3-0.5), medium (0.5-1.0), large (1.0-2.0), mega (>2.0)
- `speed_category`: explosive (<5 bars), steady (5-12), grinding (>12)
- `timing_category`: open_flush (9:30-9:45), morning (9:45-11:00), midday (11:00-13:00), afternoon (13:00-16:00)
- `pattern_category`: gap_continuation, gap_reversal, level_breakout, level_bounce, range_breakout, reversal, fade_mean_reversion, trend_continuation, unclassified
- `context_category`: broad_move (4+), sector_move (2-3), isolated

**Pattern classification priority:** gap_continuation/reversal (open only) → level_breakout → level_bounce → range_breakout → reversal → fade → trend_continuation → unclassified

**Verify:** Print distribution tables for each category, check that categories are reasonable.

---

## Task 6: Export & Stats Report

**What to build:**
- `export_results(moves_df)` → 3 output files

**Outputs:**
1. `debug/move-catalog.parquet` — Full catalog (~58 columns, ~46K rows)
2. `debug/move-catalog-summary.csv` — First 1000 rows for quick inspection
3. `debug/move-catalog-stats.md` — Summary report with:
   - Dataset summary (symbols, dates, total moves)
   - Distribution by: symbol, magnitude, speed, timing, pattern, market context
   - Level interaction stats (which levels most common, breakout vs bounce rates)
   - Cross-symbol coordination (broad vs isolated)
   - Time-of-day coverage (moves per hour bucket)
   - Comparison note: how this relates to existing enriched-signals.csv

**Also:** Add progress reporting every 100 symbol-days, crash recovery checkpoint.

**Verify:** Load the parquet back, confirm row count and schema. Read the stats report.

---

## Task 7: Run & Validate

Run `debug/build_move_catalog.py` end-to-end. Expected runtime: 5-10 minutes.

**Validation checks:**
1. Row count ~46K primary moves + ~10K large moves
2. All 15 symbols present, date range Feb 2024 – Mar 2026
3. No column is >50% NaN (except 1m MFE/MAE and PM levels which have limited coverage)
4. Spot-check 5 known moves from `_toinvestigate.md` entries — are they in the catalog?
5. Cross-reference with enriched-signals.csv — what fraction of signal times match a catalog move?

**If errors:** Fix and re-run. The checkpoint system allows resuming from last good point.

---

## Estimated Output

~46,000 primary moves + ~10,000 large moves = **~56,000 total rows** with 58 columns of context each. This is THE canonical dataset for all future KLB research.

**Research it enables:**
- Which pattern categories produce highest MFE?
- Do broad moves have higher continuation?
- Which levels produce the best breakouts vs bounces?
- What does the pre-move look like for mega moves?
- Signal matching: join with enriched-signals.csv to see which moves KLB catches/misses
- Trigger design: which combinations of context predict tradeable moves?
