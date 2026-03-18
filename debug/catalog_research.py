#!/usr/bin/env python3
"""
KLB Move Catalog Research — Factor Screening Pipeline

Mines the 72K-move catalog to find:
1. Pre-move patterns that predict "great" moves (clean + big + sticky)
2. Noise filters — conditions where most moves fade

Design: docs/plans/2026-03-07-catalog-research-design.md
"""

import pandas as pd
import numpy as np
from pathlib import Path
from itertools import combinations
from datetime import datetime
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# ── Config ──────────────────────────────────────────────────────────────────────

CATALOG = Path(__file__).parent / "move-catalog.parquet"
OUT_DIR = Path(__file__).parent

# Great move thresholds
GREAT_MFE_MAE_RATIO = 3.0
GREAT_MFE_MIN = 0.30       # ATR
GREAT_RETRACE_MAX = 0.40   # retains ≥60% at 12 bars

# Fallback (no 1m data)
GREAT_FALLBACK_MAG = 0.50
GREAT_FALLBACK_RETRACE = 0.40

# Noise thresholds
NOISE_RETRACE_6BAR = 0.80  # fades >80% within 6 bars

# Combo search
MIN_COMBO_N = 50
MIN_COMBO_LIFT = 2.0
TOP_K_FACTORS = 8

# ── Load & Label ────────────────────────────────────────────────────────────────

def load_and_label():
    """Load catalog, compute is_great and is_noise labels."""
    df = pd.read_parquet(CATALOG)
    primary = df[df["pass"] == "primary"].copy()
    print(f"Loaded {len(primary):,} primary moves ({len(df.columns)} cols)")

    # Exclude TSM (anomalous data — 15K moves, 5x others)
    tsm_n = len(primary[primary["symbol"] == "TSM"])
    primary = primary[primary["symbol"] != "TSM"].copy()
    print(f"Excluded TSM ({tsm_n:,} moves) — {len(primary):,} remaining")

    has_1m = primary["mfe_1m"].notna()

    # ── Great move label ──
    # 1m-enriched: all three gates
    great_1m = (
        has_1m
        & (primary["mae_1m"] > 0)
        & ((primary["mfe_1m"] / primary["mae_1m"].clip(lower=0.001)) >= GREAT_MFE_MAE_RATIO)
        & (primary["mfe_1m"] >= GREAT_MFE_MIN)
        & (primary["retracement_12bar"] <= GREAT_RETRACE_MAX)
    )
    # Fallback: magnitude + retracement only
    great_fallback = (
        ~has_1m
        & (primary["magnitude_atr"] >= GREAT_FALLBACK_MAG)
        & (primary["retracement_12bar"] <= GREAT_FALLBACK_RETRACE)
    )
    primary["is_great"] = great_1m | great_fallback

    # ── Noise label ──
    noise_1m = has_1m & (primary["mae_1m"] > primary["mfe_1m"])
    noise_retrace = primary["retracement_6bar"] > NOISE_RETRACE_6BAR
    primary["is_noise"] = noise_1m | noise_retrace

    great_n = primary["is_great"].sum()
    noise_n = primary["is_noise"].sum()
    total = len(primary)
    print(f"\nLabels:")
    print(f"  Great moves: {great_n:,} ({great_n/total:.1%})")
    print(f"  Noise moves: {noise_n:,} ({noise_n/total:.1%})")
    print(f"  Neither:     {total - great_n - noise_n:,} ({(total-great_n-noise_n)/total:.1%})")

    return primary


# ── Factor Definitions ──────────────────────────────────────────────────────────

def define_factors(df):
    """Define all factor columns with their bin specifications.
    Returns list of (name, series, bin_type) tuples.
    bin_type: 'categorical' | 'numeric_fixed' | 'numeric_quantile'
    """
    factors = []

    # --- Trend ---
    factors.append(("pre_ema21_slope", df["pre_ema21_slope"], "numeric_quantile", 5))
    factors.append(("pre_ema21_position", df["pre_ema21_position"], "categorical", None))
    adx_bins = pd.cut(df["pre_adx"], bins=[0, 20, 30, 40, 100],
                      labels=["<20", "20-30", "30-40", ">40"])
    factors.append(("pre_adx", adx_bins, "categorical", None))

    # --- VWAP ---
    factors.append(("pre_vwap_position", df["pre_vwap_position"], "categorical", None))
    factors.append(("pre_vwap_dist_atr", df["pre_vwap_dist_atr"], "numeric_quantile", 4))
    factors.append(("trig_vwap_aligned", df["trig_vwap_aligned"], "categorical", None))

    # --- Volume ---
    vol_bins = pd.cut(df["pre_vol_avg_ratio"], bins=[0, 0.5, 1.0, 2.0, 3.0, 100],
                      labels=["<0.5", "0.5-1", "1-2", "2-3", ">3"])
    factors.append(("pre_vol_avg_ratio", vol_bins, "categorical", None))
    trig_vol_bins = pd.cut(df["trig_vol_ratio"], bins=[0, 0.5, 1.0, 2.0, 3.0, 5.0, 100],
                           labels=["<0.5", "0.5-1", "1-2", "2-3", "3-5", ">5"])
    factors.append(("trig_vol_ratio", trig_vol_bins, "categorical", None))

    # --- Compression ---
    comp_bins = pd.cut(df["pre_compression"], bins=[0, 0.5, 0.85, 1.0, 100],
                       labels=["<0.5 (coiled)", "0.5-0.85", "0.85-1.0", ">1.0"])
    factors.append(("pre_compression", comp_bins, "categorical", None))

    # --- Candle ---
    factors.append(("trig_candle_type", df["trig_candle_type"], "categorical", None))
    factors.append(("trig_body_pct", df["trig_body_pct"], "numeric_quantile", 4))
    factors.append(("trig_range_atr", df["trig_range_atr"], "numeric_quantile", 4))
    factors.append(("trig_ema_aligned", df["trig_ema_aligned"], "categorical", None))

    # --- Timing ---
    factors.append(("timing_category", df["timing_category"], "categorical", None))
    if "start_time" in df.columns:
        hours = pd.to_datetime(df["start_time"]).dt.hour
        factors.append(("start_hour", hours, "categorical", None))
    factors.append(("day_of_week", df["day_of_week"], "categorical", None))

    # --- Level ---
    factors.append(("nearest_level_type", df["nearest_level_type"], "categorical", None))
    level_dist_bins = pd.cut(df["nearest_level_dist_atr"],
                             bins=[0, 0.05, 0.1, 0.2, 0.5, 100],
                             labels=["<0.05", "0.05-0.1", "0.1-0.2", "0.2-0.5", ">0.5"])
    factors.append(("nearest_level_dist_atr", level_dist_bins, "categorical", None))
    n_levels_bins = pd.cut(df["n_levels_within_05"], bins=[-1, 0, 2, 4, 8, 20],
                           labels=["0", "1-2", "3-4", "5-8", ">8"])
    factors.append(("n_levels_within_05", n_levels_bins, "categorical", None))
    factors.append(("level_interaction", df["level_interaction"], "categorical", None))

    # --- Context ---
    factors.append(("pattern_category", df["pattern_category"], "categorical", None))
    factors.append(("context_category", df["context_category"], "categorical", None))
    conc_bins = pd.cut(df["concurrent_symbols"], bins=[-1, 0, 3, 6, 9, 15],
                       labels=["0", "1-3", "4-6", "7-9", "10+"])
    factors.append(("concurrent_symbols", conc_bins, "categorical", None))
    factors.append(("spy_direction", df["spy_direction"], "categorical", None))
    factors.append(("gap_direction", df["gap_direction"], "categorical", None))

    # --- Direction ---
    factors.append(("direction", df["direction"], "categorical", None))

    # --- Magnitude category ---
    factors.append(("mag_category", df["mag_category"], "categorical", None))
    factors.append(("speed_category", df["speed_category"], "categorical", None))

    return factors


# ── Single-Factor Screen ────────────────────────────────────────────────────────

def screen_single_factor(df, name, binned_series, baseline_great, baseline_noise):
    """Screen one factor: compute per-bin great/noise rates and lift."""
    results = []
    valid = binned_series.notna()
    groups = df[valid].groupby(binned_series[valid])

    for bin_val, grp in groups:
        n = len(grp)
        if n < 20:
            continue
        great_rate = grp["is_great"].mean()
        noise_rate = grp["is_noise"].mean()
        great_lift = great_rate / max(baseline_great, 0.001)
        noise_lift = noise_rate / max(baseline_noise, 0.001)

        row = {
            "factor": name,
            "bin": str(bin_val),
            "N": n,
            "great_rate": round(great_rate, 4),
            "great_lift": round(great_lift, 2),
            "noise_rate": round(noise_rate, 4),
            "noise_lift": round(noise_lift, 2),
        }

        # Add MFE/MAE if available
        if "mfe_1m" in grp.columns:
            has_mfe = grp["mfe_1m"].notna()
            if has_mfe.sum() > 10:
                row["mean_mfe_1m"] = round(grp.loc[has_mfe, "mfe_1m"].mean(), 4)
                row["mean_mae_1m"] = round(grp.loc[has_mfe, "mae_1m"].mean(), 4)

        # Retracement
        if "retracement_12bar" in grp.columns:
            r12 = grp["retracement_12bar"].dropna()
            if len(r12) > 10:
                row["mean_retrace_12"] = round(r12.mean(), 4)

        results.append(row)

    return results


def run_single_factor_screen(df):
    """Run Phase 1: single-factor screen across all factors."""
    baseline_great = df["is_great"].mean()
    baseline_noise = df["is_noise"].mean()

    print(f"\n{'='*70}")
    print(f"PHASE 1: Single-Factor Screen")
    print(f"Baseline great rate: {baseline_great:.1%} | Baseline noise rate: {baseline_noise:.1%}")
    print(f"{'='*70}")

    factors = define_factors(df)
    all_results = []

    for name, series, bin_type, n_bins in factors:
        if bin_type == "numeric_quantile":
            try:
                binned = pd.qcut(series.dropna(), q=n_bins, duplicates="drop")
                # Re-index to match df
                full_binned = pd.Series(pd.NA, index=df.index, dtype="object")
                full_binned[binned.index] = binned.astype(str)
                series = full_binned
            except (ValueError, TypeError):
                continue
        elif bin_type == "categorical":
            series = series.astype(str)

        results = screen_single_factor(df, name, series, baseline_great, baseline_noise)
        all_results.extend(results)

    results_df = pd.DataFrame(all_results)

    # Find best great-lift factors
    print(f"\n  Top 15 bins by GREAT lift (N≥50):")
    top_great = results_df[results_df["N"] >= 50].nlargest(15, "great_lift")
    for _, r in top_great.iterrows():
        mfe = f"  MFE={r.get('mean_mfe_1m', 'n/a')}" if pd.notna(r.get("mean_mfe_1m")) else ""
        print(f"    {r['factor']:25s} = {r['bin']:15s}  N={r['N']:5d}  "
              f"great={r['great_rate']:.1%} ({r['great_lift']:.1f}x){mfe}")

    # Find worst noise-lift factors
    print(f"\n  Top 15 bins by NOISE lift (N≥50):")
    top_noise = results_df[results_df["N"] >= 50].nlargest(15, "noise_lift")
    for _, r in top_noise.iterrows():
        print(f"    {r['factor']:25s} = {r['bin']:15s}  N={r['N']:5d}  "
              f"noise={r['noise_rate']:.1%} ({r['noise_lift']:.1f}x)")

    # Best factor per group (highest max lift)
    print(f"\n  Best factor per group:")
    factor_best = results_df[results_df["N"] >= 50].loc[
        results_df[results_df["N"] >= 50].groupby("factor")["great_lift"].idxmax()
    ].nlargest(20, "great_lift")
    for _, r in factor_best.iterrows():
        print(f"    {r['factor']:25s} = {r['bin']:15s}  lift={r['great_lift']:.2f}x  N={r['N']:,}")

    return results_df


# ── Combinatorial Search ────────────────────────────────────────────────────────

OUTCOME_FACTORS = {"mag_category", "speed_category", "duration_bars", "magnitude_atr"}

def run_combo_search(df, single_results):
    """Phase 2: Test top pre-move factor combinations (excludes outcome vars)."""
    baseline_great = df["is_great"].mean()

    # Exclude outcome factors — only use things we know BEFORE the move
    pre_move_results = single_results[~single_results["factor"].isin(OUTCOME_FACTORS)]

    # Pick top pre-move factors: best bin per factor, sorted by lift
    factor_best = pre_move_results[pre_move_results["N"] >= 50].loc[
        pre_move_results[pre_move_results["N"] >= 50].groupby("factor")["great_lift"].idxmax()
    ].nlargest(TOP_K_FACTORS, "great_lift")

    top_factors = list(factor_best["factor"].values)
    print(f"\n{'='*70}")
    print(f"PHASE 2: Combinatorial Search")
    print(f"Top {len(top_factors)} factors: {top_factors}")
    print(f"{'='*70}")

    # Rebuild binned columns for top factors
    factor_defs = {name: (series, bt, nb) for name, series, bt, nb in define_factors(df)}

    binned_cols = {}
    for fname in top_factors:
        if fname not in factor_defs:
            continue
        series, bt, nb = factor_defs[fname]
        if bt == "numeric_quantile":
            try:
                binned = pd.qcut(series.dropna(), q=nb, duplicates="drop")
                full = pd.Series(pd.NA, index=df.index, dtype="object")
                full[binned.index] = binned.astype(str)
                binned_cols[fname] = full
            except (ValueError, TypeError):
                continue
        else:
            binned_cols[fname] = series.astype(str)

        # Find the best bin for this factor
        best_row = factor_best[factor_best["factor"] == fname].iloc[0]
        best_bin = best_row["bin"]
        # Create boolean: is this the "good" bin?
        binned_cols[f"{fname}_best"] = (binned_cols[fname] == best_bin)

    # Test 2-way combos
    best_flags = [f for f in binned_cols if f.endswith("_best")]
    combo_results = []

    for combo in combinations(best_flags, 2):
        mask = df.index.isin(df.index)  # start with all True
        for c in combo:
            mask = mask & binned_cols[c].fillna(False)
        n = mask.sum()
        if n < MIN_COMBO_N:
            continue
        great_rate = df.loc[mask, "is_great"].mean()
        lift = great_rate / max(baseline_great, 0.001)
        if lift < MIN_COMBO_LIFT:
            continue
        noise_rate = df.loc[mask, "is_noise"].mean()
        names = [c.replace("_best", "") for c in combo]

        row = {
            "combo": " + ".join(names),
            "N": n,
            "great_rate": round(great_rate, 4),
            "lift": round(lift, 2),
            "noise_rate": round(noise_rate, 4),
            "score": round(lift * np.sqrt(n), 1),
        }
        # MFE
        mfe_vals = df.loc[mask, "mfe_1m"].dropna()
        if len(mfe_vals) > 5:
            row["mean_mfe_1m"] = round(mfe_vals.mean(), 4)
            mae_vals = df.loc[mask, "mae_1m"].dropna()
            row["mean_mae_1m"] = round(mae_vals.mean(), 4) if len(mae_vals) > 5 else np.nan

        combo_results.append(row)

    # Test 3-way combos
    for combo in combinations(best_flags, 3):
        mask = df.index.isin(df.index)
        for c in combo:
            mask = mask & binned_cols[c].fillna(False)
        n = mask.sum()
        if n < MIN_COMBO_N:
            continue
        great_rate = df.loc[mask, "is_great"].mean()
        lift = great_rate / max(baseline_great, 0.001)
        if lift < MIN_COMBO_LIFT:
            continue
        noise_rate = df.loc[mask, "is_noise"].mean()
        names = [c.replace("_best", "") for c in combo]
        row = {
            "combo": " + ".join(names),
            "N": n,
            "great_rate": round(great_rate, 4),
            "lift": round(lift, 2),
            "noise_rate": round(noise_rate, 4),
            "score": round(lift * np.sqrt(n), 1),
        }
        mfe_vals = df.loc[mask, "mfe_1m"].dropna()
        if len(mfe_vals) > 5:
            row["mean_mfe_1m"] = round(mfe_vals.mean(), 4)
            mae_vals = df.loc[mask, "mae_1m"].dropna()
            row["mean_mae_1m"] = round(mae_vals.mean(), 4) if len(mae_vals) > 5 else np.nan
        combo_results.append(row)

    combo_df = pd.DataFrame(combo_results)
    if len(combo_df) > 0:
        combo_df = combo_df.sort_values("score", ascending=False)
        print(f"\n  Top 15 combos (by lift × √N):")
        for _, r in combo_df.head(15).iterrows():
            mfe = f"  MFE={r.get('mean_mfe_1m', 'n/a')}" if pd.notna(r.get("mean_mfe_1m")) else ""
            print(f"    {r['combo']:50s}  N={r['N']:5d}  "
                  f"great={r['great_rate']:.1%} ({r['lift']:.1f}x)  "
                  f"noise={r['noise_rate']:.1%}{mfe}")
    else:
        print("  No combos met the threshold (N≥50, lift≥2x)")

    return combo_df


# ── Decision Tree Validation ────────────────────────────────────────────────────

def run_decision_tree(df):
    """Phase 3: Shallow decision tree for feature importance and threshold discovery."""
    print(f"\n{'='*70}")
    print(f"PHASE 3: Decision Tree Validation")
    print(f"{'='*70}")

    try:
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.model_selection import cross_val_score
    except ImportError:
        print("  sklearn not available — skipping decision tree")
        return None

    # Prepare numeric features
    feature_cols = [
        "pre_ema21_slope", "pre_adx", "pre_vwap_dist_atr", "pre_compression",
        "pre_vol_avg_ratio", "trig_body_pct", "trig_vol_ratio", "trig_range_atr",
        "nearest_level_dist_atr", "n_levels_within_05", "concurrent_symbols",
        "spy_magnitude_atr", "duration_bars", "magnitude_atr",
    ]
    # Add boolean features as 0/1
    bool_cols = ["trig_ema_aligned", "trig_vwap_aligned"]
    for col in bool_cols:
        if col in df.columns:
            df[f"{col}_num"] = df[col].astype(float)
            feature_cols.append(f"{col}_num")

    # Add categorical as dummies
    cat_cols = ["timing_category", "pattern_category", "direction", "gap_direction"]
    for col in cat_cols:
        if col in df.columns:
            dummies = pd.get_dummies(df[col], prefix=col, drop_first=True)
            for dc in dummies.columns:
                df[dc] = dummies[dc]
                feature_cols.append(dc)

    # Filter to rows with all features
    available = [c for c in feature_cols if c in df.columns]
    subset = df[available + ["is_great"]].dropna()
    X = subset[available].values
    y = subset["is_great"].values

    print(f"  Features: {len(available)}, Samples: {len(subset):,}")

    # Train and cross-validate
    tree = DecisionTreeClassifier(max_depth=5, min_samples_leaf=50, random_state=42)
    scores = cross_val_score(tree, X, y, cv=5, scoring="f1")
    print(f"  5-fold CV F1: {scores.mean():.3f} ± {scores.std():.3f}")

    # Fit on full data for feature importance
    tree.fit(X, y)
    importances = pd.Series(tree.feature_importances_, index=available)
    importances = importances[importances > 0.01].sort_values(ascending=False)

    print(f"\n  Feature importance (>1%):")
    for feat, imp in importances.items():
        print(f"    {feat:35s}  {imp:.3f}")

    # Extract top splits
    tree_rules = _extract_tree_rules(tree, available)
    if tree_rules:
        print(f"\n  Top tree paths to 'great' (leaf purity >50%):")
        for rule in tree_rules[:10]:
            print(f"    {rule}")

    return importances


def _extract_tree_rules(tree, feature_names):
    """Extract decision paths from tree that lead to 'great' leaves."""
    from sklearn.tree import _tree

    tree_ = tree.tree_
    rules = []

    def recurse(node, path):
        if tree_.feature[node] == _tree.TREE_UNDEFINED:
            # Leaf node
            n_samples = tree_.n_node_samples[node]
            values = tree_.value[node][0]
            if len(values) >= 2 and values[1] > 0:
                great_rate = values[1] / values.sum()
                if great_rate > 0.5 and n_samples >= 30:
                    conditions = " AND ".join(path)
                    rules.append(f"{conditions} → great={great_rate:.0%} (N={n_samples})")
            return

        fname = feature_names[tree_.feature[node]]
        threshold = tree_.threshold[node]

        recurse(tree_.children_left[node], path + [f"{fname}≤{threshold:.3f}"])
        recurse(tree_.children_right[node], path + [f"{fname}>{threshold:.3f}"])

    recurse(0, [])
    return sorted(rules, key=lambda x: int(x.split("N=")[1].rstrip(")")), reverse=True)


# ── Report Writing ──────────────────────────────────────────────────────────────

def write_factor_report(single_results, combo_results, tree_importances, df):
    """Write all three markdown reports."""
    baseline_great = df["is_great"].mean()
    baseline_noise = df["is_noise"].mean()

    # ── Factor Screen Report ──
    with open(OUT_DIR / "catalog-factor-screen.md", "w") as f:
        f.write("# Move Catalog — Factor Screen Results\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"## Baseline\n")
        f.write(f"- **Great move rate:** {baseline_great:.1%} ({df['is_great'].sum():,} / {len(df):,})\n")
        f.write(f"- **Noise rate:** {baseline_noise:.1%} ({df['is_noise'].sum():,} / {len(df):,})\n")
        f.write(f"- **Definition:** Great = MFE/MAE≥3 + MFE≥0.30 + retrace12≤0.40 | "
                f"Noise = MAE>MFE or retrace6>0.80\n\n")

        # Group by factor, sorted by best lift
        f.write("## Single-Factor Results (sorted by best lift)\n\n")
        for factor_name in single_results.groupby("factor")["great_lift"].max().sort_values(ascending=False).index:
            factor_rows = single_results[single_results["factor"] == factor_name].sort_values("great_lift", ascending=False)
            f.write(f"### {factor_name}\n")
            f.write("| Bin | N | Great% | Lift | Noise% | MFE_1m | MAE_1m | Retrace12 |\n")
            f.write("|-----|---|--------|------|--------|--------|--------|----------|\n")
            for _, r in factor_rows.iterrows():
                mfe = f"{r.get('mean_mfe_1m', ''):.4f}" if pd.notna(r.get("mean_mfe_1m")) else ""
                mae = f"{r.get('mean_mae_1m', ''):.4f}" if pd.notna(r.get("mean_mae_1m")) else ""
                ret = f"{r.get('mean_retrace_12', ''):.4f}" if pd.notna(r.get("mean_retrace_12")) else ""
                f.write(f"| {r['bin']} | {r['N']:,} | {r['great_rate']:.1%} | "
                        f"{r['great_lift']:.2f}x | {r['noise_rate']:.1%} | {mfe} | {mae} | {ret} |\n")
            f.write("\n")

    print(f"\n  → {OUT_DIR / 'catalog-factor-screen.md'}")

    # ── Combo Rules Report ──
    with open(OUT_DIR / "catalog-combo-rules.md", "w") as f:
        f.write("# Move Catalog — Combination Rules\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"Baseline great rate: {baseline_great:.1%}\n")
        f.write(f"Min N: {MIN_COMBO_N} | Min lift: {MIN_COMBO_LIFT}x\n\n")

        if len(combo_results) > 0:
            f.write("## Top Combinations (by score = lift × √N)\n\n")
            f.write("| Combo | N | Great% | Lift | Noise% | MFE_1m | MAE_1m | Score |\n")
            f.write("|-------|---|--------|------|--------|--------|--------|-------|\n")
            for _, r in combo_results.head(30).iterrows():
                mfe = f"{r.get('mean_mfe_1m', ''):.4f}" if pd.notna(r.get("mean_mfe_1m")) else ""
                mae = f"{r.get('mean_mae_1m', ''):.4f}" if pd.notna(r.get("mean_mae_1m")) else ""
                f.write(f"| {r['combo']} | {r['N']:,} | {r['great_rate']:.1%} | "
                        f"{r['lift']:.1f}x | {r['noise_rate']:.1%} | {mfe} | {mae} | {r['score']:.0f} |\n")
        else:
            f.write("No combinations met the thresholds.\n")

        if tree_importances is not None:
            f.write("\n## Decision Tree Feature Importance\n\n")
            f.write("| Feature | Importance |\n")
            f.write("|---------|------------|\n")
            for feat, imp in tree_importances.items():
                f.write(f"| {feat} | {imp:.3f} |\n")

    print(f"  → {OUT_DIR / 'catalog-combo-rules.md'}")

    # ── Noise Filters Report ──
    with open(OUT_DIR / "catalog-noise-filters.md", "w") as f:
        f.write("# Move Catalog — Noise Filters (Don't Trade When...)\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"Baseline noise rate: {baseline_noise:.1%}\n\n")

        # Bins where noise rate is highest
        high_noise = single_results[
            (single_results["N"] >= 50) & (single_results["noise_lift"] >= 1.3)
        ].sort_values("noise_lift", ascending=False)

        f.write("## High-Noise Conditions (lift ≥ 1.3x baseline)\n\n")
        f.write("| Factor | Bin | N | Noise% | Lift | Great% |\n")
        f.write("|--------|-----|---|--------|------|--------|\n")
        for _, r in high_noise.head(25).iterrows():
            f.write(f"| {r['factor']} | {r['bin']} | {r['N']:,} | "
                    f"{r['noise_rate']:.1%} | {r['noise_lift']:.2f}x | {r['great_rate']:.1%} |\n")

    print(f"  → {OUT_DIR / 'catalog-noise-filters.md'}")


# ── Main ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import time as time_mod
    t0 = time_mod.time()

    print("=" * 60)
    print("KLB Move Catalog — Factor Research")
    print("=" * 60)

    # Load and label
    df = load_and_label()

    # Phase 1: Single-factor screen
    single_results = run_single_factor_screen(df)

    # Phase 2: Combinatorial search
    combo_results = run_combo_search(df, single_results)

    # Phase 3: Decision tree
    tree_importances = run_decision_tree(df)

    # Write reports
    print(f"\n{'='*70}")
    print("Writing reports...")
    write_factor_report(single_results, combo_results, tree_importances, df)

    elapsed = time_mod.time() - t0
    print(f"\n{'='*60}")
    print(f"Done in {elapsed:.1f}s")
    print(f"{'='*60}")
