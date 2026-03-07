# Move Catalog Research — Design

**Date:** 2026-03-07
**Goal:** Mine the 72K-move catalog to (1) find pre-move patterns that predict great moves, and (2) identify which moves to catch vs skip.

## Target Definition

A move is **"great"** if it passes all three gates:

| Gate | Threshold | Column |
|------|-----------|--------|
| Clean entry | MFE_1m / MAE_1m ≥ 3.0 | `mfe_1m`, `mae_1m` |
| Sufficient size | MFE_1m ≥ 0.30 ATR | `mfe_1m` |
| Sticky | Retains ≥60% at 12 bars | `retracement_12bar ≤ 0.40` |

Moves without 1m data use fallback: `magnitude_atr ≥ 0.50 AND retracement_12bar ≤ 0.40`.

A move is **"noise"** if: `MAE_1m > MFE_1m OR retracement_6bar > 0.80`.

## Approach: Factor Screening Pipeline

### Phase 1 — Single-Factor Screen

For each pre-move column, bin values and measure per bin:
- N, great-move rate, noise rate, lift vs baseline
- Mean MFE_1m, MAE_1m, retracement_12bar

**Factors to screen (9 groups, ~20 columns):**

| Group | Columns | Bins |
|-------|---------|------|
| Trend | `pre_ema21_slope`, `pre_ema21_position`, `pre_adx` | Slope: 5 quantiles. ADX: <20, 20-30, 30-40, >40 |
| VWAP | `pre_vwap_position`, `pre_vwap_dist_atr`, `trig_vwap_aligned` | Position: above/below. Dist: 3 bins |
| Volume | `pre_vol_avg_ratio`, `trig_vol_ratio` | <0.5, 0.5-1, 1-2, 2-3, >3 |
| Compression | `pre_compression` | <0.5 (coiled), 0.5-0.85, 0.85-1.0, >1.0 |
| Candle | `trig_body_pct`, `trig_candle_type`, `trig_range_atr`, `trig_ema_aligned` | By type, body% quartiles |
| Timing | `timing_category`, hour, `day_of_week` | Categories + hourly |
| Level | `nearest_level_type`, `nearest_level_dist_atr`, `n_levels_within_05`, `level_interaction` | By type, distance bins |
| Context | `pattern_category`, `context_category`, `concurrent_symbols`, `spy_direction`, `gap_direction` | Categories, concurrent bins |
| Prior move | direction vs previous, `duration_bars` | Same/opposite, duration quartiles |

### Phase 2 — Combinatorial Search

Top 8 factors by lift → test all 2-way (28) and 3-way (56) combos.
Keep combos with **N ≥ 50** and **great-rate ≥ 2× baseline**.
Rank by `lift × sqrt(N)`.

### Phase 3 — Decision Tree Validation

Shallow tree (depth 4-5) on `is_great`. Purpose: confirm factor ranking via feature importance, surface threshold values, cross-validated accuracy check.

### Phase 4 — Rule Set Output

Top 10-15 findings → concrete rules with:
- Condition, N, great-rate, lift, avg MFE, avg MAE
- KLB recommendation: new signal / quality gate / suppression rule

## Outputs

| File | Content |
|------|---------|
| `debug/catalog-factor-screen.md` | All single-factor tables, ranked by lift |
| `debug/catalog-combo-rules.md` | Top combination rules with recommendations |
| `debug/catalog-noise-filters.md` | Suppression rules ("don't trade when...") |

## Script

`debug/catalog_research.py` — single script, ~300-400 lines. Pure pandas + sklearn DecisionTreeClassifier. Runtime <30s.

## What This Enables

- Improve existing KLB signals: quality gates based on pre-move context
- Discover new opportunities: midday patterns, concurrent-symbol regimes, level-density setups
- Exit research: which pre-move conditions predict sticky vs fading moves
