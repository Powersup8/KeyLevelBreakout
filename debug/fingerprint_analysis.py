#!/usr/bin/env python3
"""Fingerprint analysis: cluster moves, find patterns, identify predictive signatures.
Phases 2-4: normalize → cluster → analyze per cluster → predictive matching.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
import warnings
warnings.filterwarnings("ignore")

DEBUG = Path(__file__).parent
CATALOG_PATH = DEBUG / "move-catalog.parquet"
FINGERPRINT_PATH = DEBUG / "move-fingerprints.parquet"

# Features to use for clustering (exclude IDs, categoricals, shape)
CONTEXT_FEATURES = [
    # Prior move history
    "moves_today_count", "moves_today_bull_pct", "cumulative_atr_today",
    "day_net_atr", "prev_move_magnitude", "prev_move_gap_bars",
    # Pre-move price action
    "pre_12bar_trend_slope", "pre_12bar_range_atr", "pre_6bar_acceleration",
    "pre_consecutive_same_dir", "pre_narrow_bar_count",
    "pre_ema21_dist_atr", "pre_ema50_dist_atr",
    # Volume
    "pre_vol_slope", "pre_vol_spike_count", "pre_vol_dry_count", "trig_vol_vs_pre12",
    # SPY
    "spy_adx", "spy_intraday_return", "spy_range_consumed",
    "spy_vol_ratio", "spy_ema_slope", "spy_range_position",
    # Breadth
    "breadth_above_vwap", "breadth_above_ema",
    "breadth_bull_moves_15min", "breadth_bear_moves_15min", "breadth_net",
    # Cross-symbol
    "leader_score", "tech_same_dir_count", "commodity_same_dir_count",
    "symbol_daily_bias",
    # Level
    "level_zone_width_atr", "second_nearest_dist_atr", "level_sandwich_ratio",
    "level_tests_today", "nearest_support_atr", "nearest_resistance_atr",
    # Intraday
    "minutes_since_open", "intraday_range_position", "daily_atr_consumed",
]

SHAPE_FEATURES = [
    "shape_5pt_0", "shape_5pt_1", "shape_5pt_2", "shape_5pt_3", "shape_5pt_4",
    "shape_max_dd_position", "shape_front_loaded", "shape_pause_count",
    "shape_direction_changes",
]

ALL_FEATURES = CONTEXT_FEATURES + SHAPE_FEATURES


def load_data():
    """Load catalog + fingerprints, merge, label great/noise."""
    cat = pd.read_parquet(CATALOG_PATH)
    cat = cat[cat["pass"] == "primary"].copy()
    fp = pd.read_parquet(FINGERPRINT_PATH)
    df = cat.merge(fp, on="move_id", how="inner")

    # Label great/noise (same as catalog_research)
    has_1m = df["mfe_1m"].notna()
    df["is_great"] = (
        (has_1m & (df["mae_1m"] > 0)
         & (df["mfe_1m"] / df["mae_1m"].clip(lower=0.001) >= 3)
         & (df["mfe_1m"] >= 0.30)
         & (df["retracement_12bar"] <= 0.40))
        | (~has_1m & (df["magnitude_atr"] >= 0.50) & (df["retracement_12bar"] <= 0.40))
    )
    df["is_noise"] = (has_1m & (df["mae_1m"] > df["mfe_1m"])) | (df["retracement_6bar"] > 0.80)
    return df


def cluster_moves(df, features, n_components=15, eps=1.5, min_samples=50):
    """PCA → DBSCAN clustering."""
    # Select and clean features
    X = df[features].copy()
    # Fill NaN with median
    for col in X.columns:
        X[col] = X[col].fillna(X[col].median())
    # Standardize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    # PCA
    pca = PCA(n_components=min(n_components, len(features)))
    X_pca = pca.fit_transform(X_scaled)
    explained = pca.explained_variance_ratio_.cumsum()
    print(f"  PCA: {len(features)} features → {n_components} components "
          f"({explained[-1]:.1%} variance explained)")
    # DBSCAN
    db = DBSCAN(eps=eps, min_samples=min_samples, n_jobs=-1)
    labels = db.fit_predict(X_pca)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    print(f"  DBSCAN: {n_clusters} clusters, {n_noise:,} noise points ({n_noise/len(df):.1%})")
    return labels, X_pca, X_scaled, scaler, pca


def analyze_clusters(df, labels, features):
    """Per-cluster analysis: size, great rate, defining features."""
    df = df.copy()
    df["cluster"] = labels

    baseline_great = df["is_great"].mean()
    baseline_noise = df["is_noise"].mean()

    print(f"\n{'='*70}")
    print(f"CLUSTER ANALYSIS (baseline: great={baseline_great:.1%}, noise={baseline_noise:.1%})")
    print(f"{'='*70}")

    # Global feature means for comparison
    global_means = {}
    for f in features:
        vals = df[f].dropna()
        if len(vals) > 0:
            global_means[f] = (vals.mean(), vals.std())

    clusters = sorted(df["cluster"].unique())
    cluster_stats = []

    for cl in clusters:
        sub = df[df["cluster"] == cl]
        n = len(sub)
        gr = sub["is_great"].mean()
        nr = sub["is_noise"].mean()
        lift = gr / baseline_great if baseline_great > 0 else 0
        avg_mag = sub["magnitude_atr"].mean()
        avg_mfe = sub["mfe_1m"].dropna().mean() if sub["mfe_1m"].notna().any() else np.nan

        # Find defining features (most different from global mean)
        deviations = []
        for f in features:
            if f not in global_means:
                continue
            gm, gs = global_means[f]
            if gs < 1e-6:
                continue
            cv = sub[f].dropna().mean()
            z = (cv - gm) / gs
            deviations.append((f, z, cv, gm))
        deviations.sort(key=lambda x: abs(x[1]), reverse=True)

        cluster_stats.append({
            "cluster": cl, "n": n, "great_pct": gr, "noise_pct": nr,
            "lift": lift, "avg_mag": avg_mag, "avg_mfe": avg_mfe,
            "top_features": deviations[:5],
        })

    # Sort by lift
    cluster_stats.sort(key=lambda x: x["lift"], reverse=True)

    for cs in cluster_stats:
        cl = cs["cluster"]
        label = "NOISE" if cl == -1 else f"C{cl}"
        bar = "█" * int(cs["lift"] * 10) if cs["lift"] < 5 else "█" * 50
        print(f"\n  {label:6s}  N={cs['n']:6,}  great={cs['great_pct']:.1%} "
              f"({cs['lift']:.2f}x)  noise={cs['noise_pct']:.1%}  "
              f"mag={cs['avg_mag']:.2f}  {bar}")

        # Top defining features
        for fname, z, cv, gm in cs["top_features"]:
            direction = "▲" if z > 0 else "▼"
            print(f"         {direction} {fname:30s}  z={z:+.1f}  "
                  f"(cluster={cv:.2f} vs global={gm:.2f})")

    return cluster_stats


def find_best_worst_clusters(df, labels):
    """Identify the highest-great and highest-noise clusters."""
    df = df.copy()
    df["cluster"] = labels

    print(f"\n{'='*70}")
    print("ACTIONABLE CLUSTERS")
    print(f"{'='*70}")

    baseline_great = df["is_great"].mean()

    for cl in sorted(df["cluster"].unique()):
        if cl == -1:
            continue
        sub = df[df["cluster"] == cl]
        gr = sub["is_great"].mean()
        nr = sub["is_noise"].mean()
        n = len(sub)

        if gr > baseline_great * 1.3 and n >= 50:
            # Break down by direction, timing, level
            print(f"\n  HIGH-GREAT C{cl}: N={n:,}, great={gr:.1%}, noise={nr:.1%}")
            for col, vals in [("direction", ["bull", "bear"]),
                              ("timing_category", ["open_flush", "morning", "midday", "afternoon"])]:
                parts = []
                for v in vals:
                    s = sub[sub[col] == v]
                    if len(s) > 0:
                        parts.append(f"{v}={len(s)}")
                print(f"    {col}: {', '.join(parts)}")

            # Level types
            lt = sub["nearest_level_type"].value_counts().head(5)
            print(f"    top levels: {', '.join(f'{k}({v})' for k, v in lt.items())}")

        elif nr > 0.15 and n >= 50:
            print(f"\n  HIGH-NOISE C{cl}: N={n:,}, great={gr:.1%}, noise={nr:.1%}")
            lt = sub["nearest_level_type"].value_counts().head(3)
            print(f"    top levels: {', '.join(f'{k}({v})' for k, v in lt.items())}")


def knn_analysis(df, features, k=50):
    """For each great-move tier, find what context looks like using KNN."""
    print(f"\n{'='*70}")
    print(f"KNN PATTERN MATCHING — What predicts great vs noise?")
    print(f"{'='*70}")

    # Prepare feature matrix
    X = df[features].copy()
    for col in X.columns:
        X[col] = X[col].fillna(X[col].median())
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    nn = NearestNeighbors(n_neighbors=k, n_jobs=-1)
    nn.fit(X_scaled)

    # For each move, get KNN great rate
    distances, indices = nn.kneighbors(X_scaled)
    knn_great_rates = np.array([df.iloc[idx]["is_great"].mean() for idx in indices])
    df = df.copy()
    df["knn_great_rate"] = knn_great_rates

    # How well does KNN separate great from noise?
    actual_great = df["is_great"]
    top_quartile = df["knn_great_rate"] >= df["knn_great_rate"].quantile(0.75)
    bottom_quartile = df["knn_great_rate"] <= df["knn_great_rate"].quantile(0.25)

    print(f"\n  KNN (k={k}) separation:")
    print(f"    Top quartile:    N={top_quartile.sum():,}  "
          f"great={df.loc[top_quartile, 'is_great'].mean():.1%}  "
          f"noise={df.loc[top_quartile, 'is_noise'].mean():.1%}")
    print(f"    Bottom quartile: N={bottom_quartile.sum():,}  "
          f"great={df.loc[bottom_quartile, 'is_great'].mean():.1%}  "
          f"noise={df.loc[bottom_quartile, 'is_noise'].mean():.1%}")
    print(f"    Separation ratio: "
          f"{df.loc[top_quartile, 'is_great'].mean() / max(df.loc[bottom_quartile, 'is_great'].mean(), 0.001):.2f}x")

    # What features define top quartile vs bottom?
    print(f"\n  Features that distinguish top from bottom quartile:")
    for f in features:
        top_v = df.loc[top_quartile, f].dropna().mean()
        bot_v = df.loc[bottom_quartile, f].dropna().mean()
        glob_std = df[f].dropna().std()
        if glob_std > 1e-6:
            diff_z = (top_v - bot_v) / glob_std
            if abs(diff_z) > 0.3:
                print(f"    {f:35s}  top={top_v:+.3f}  bot={bot_v:+.3f}  Δz={diff_z:+.2f}")

    return df


def context_vs_shape_analysis(df):
    """Compare clustering with context-only vs shape-only vs combined."""
    print(f"\n{'='*70}")
    print("CONTEXT vs SHAPE: Which matters more for predicting great moves?")
    print(f"{'='*70}")

    baseline = df["is_great"].mean()

    for name, features in [("Context only", CONTEXT_FEATURES),
                           ("Shape only", SHAPE_FEATURES),
                           ("Combined", ALL_FEATURES)]:
        X = df[features].copy()
        for col in X.columns:
            X[col] = X[col].fillna(X[col].median())
        scaler = StandardScaler()
        X_s = scaler.fit_transform(X)
        nn = NearestNeighbors(n_neighbors=50, n_jobs=-1)
        nn.fit(X_s)
        _, indices = nn.kneighbors(X_s)
        knn_gr = np.array([df.iloc[idx]["is_great"].mean() for idx in indices])

        top_q = knn_gr >= np.quantile(knn_gr, 0.75)
        bot_q = knn_gr <= np.quantile(knn_gr, 0.25)
        top_great = df.iloc[np.where(top_q)[0]]["is_great"].mean()
        bot_great = df.iloc[np.where(bot_q)[0]]["is_great"].mean()
        sep = top_great / max(bot_great, 0.001)

        print(f"  {name:15s}: top-Q great={top_great:.1%}, bot-Q great={bot_great:.1%}, "
              f"separation={sep:.2f}x")


def main():
    print("=" * 70)
    print("FINGERPRINT ANALYSIS")
    print("=" * 70)

    print("\nLoading data...")
    df = load_data()
    print(f"  {len(df):,} moves, great={df['is_great'].mean():.1%}, "
          f"noise={df['is_noise'].mean():.1%}")

    # Exclude TSM (anomalous move count)
    df = df[df["symbol"] != "TSM"].copy()
    print(f"  After TSM exclusion: {len(df):,} moves")

    # Phase 1: Context vs Shape comparison
    context_vs_shape_analysis(df)

    # Phase 2: KNN analysis with context features
    print("\n\nPhase 2: KNN pattern matching...")
    df = knn_analysis(df, CONTEXT_FEATURES, k=50)

    # Phase 3: Clustering
    print("\n\nPhase 3: Clustering with combined features...")
    labels, X_pca, X_scaled, scaler, pca = cluster_moves(
        df, ALL_FEATURES, n_components=15, eps=2.0, min_samples=80)

    # Phase 4: Cluster analysis
    stats = analyze_clusters(df, labels, ALL_FEATURES)
    find_best_worst_clusters(df, labels)

    # Phase 5: Great-move fingerprint deep dive
    print(f"\n{'='*70}")
    print("GREAT MOVE FINGERPRINT — What defines great moves?")
    print(f"{'='*70}")
    great = df[df["is_great"]]
    noise = df[df["is_noise"]]
    rest = df[~df["is_great"] & ~df["is_noise"]]

    print(f"\n  Feature comparison (great vs noise):")
    diffs = []
    for f in CONTEXT_FEATURES:
        gv = great[f].dropna().mean()
        nv = noise[f].dropna().mean()
        gs = df[f].dropna().std()
        if gs > 1e-6:
            z = (gv - nv) / gs
            diffs.append((f, z, gv, nv))
    diffs.sort(key=lambda x: abs(x[1]), reverse=True)
    for f, z, gv, nv in diffs[:20]:
        direction = "▲" if z > 0 else "▼"
        print(f"    {direction} {f:35s}  z={z:+.2f}  great={gv:+.3f}  noise={nv:+.3f}")


if __name__ == "__main__":
    main()
