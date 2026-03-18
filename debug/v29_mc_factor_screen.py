#!/usr/bin/env python3
"""v29 MC Factor Screen: Full factor analysis for post-9:50 signals."""

import pandas as pd
import numpy as np
from pathlib import Path
from io import StringIO

DATA = Path(__file__).parent / "enriched-signals.csv"
OUT  = Path(__file__).parent / "v29-mc-factor-screen.md"

def parse_time(t):
    """Parse '10:35' → (10, 35)."""
    parts = str(t).split(":")
    return int(parts[0]), int(parts[1])

def after_950(t):
    h, m = parse_time(t)
    return h > 9 or (h == 9 and m >= 50)

def time_in_range(t, h_start, m_start, h_end, m_end):
    h, m = parse_time(t)
    mins = h * 60 + m
    return (h_start * 60 + m_start) <= mins < (h_end * 60 + m_end)

def compute_metrics(df_sub):
    """Compute standard metrics for a subset."""
    n = len(df_sub)
    if n == 0:
        return {"N": 0, "Avg_MFE": 0, "Avg_MAE": 0, "MFE_MAE": 0,
                "Win%": 0, "Runner%": 0, "Total_PnL": 0, "Per_Signal_PnL": 0}
    avg_mfe = df_sub["mfe"].mean()
    avg_mae = df_sub["mae"].mean()
    mfe_mae = avg_mfe / abs(avg_mae) if avg_mae != 0 else float("inf")
    win_pct = (df_sub["mfe"] > df_sub["mae"].abs()).mean() * 100
    runner_pct = (df_sub["mfe"] >= 1.0).mean() * 100
    # Simple PnL proxy: MFE - |MAE| per signal
    pnl_per = avg_mfe - abs(avg_mae)
    total_pnl = pnl_per * n
    return {
        "N": n, "Avg_MFE": round(avg_mfe, 4), "Avg_MAE": round(avg_mae, 4),
        "MFE_MAE": round(mfe_mae, 3), "Win%": round(win_pct, 1),
        "Runner%": round(runner_pct, 1), "Total_PnL": round(total_pnl, 3),
        "Per_Signal_PnL": round(pnl_per, 4)
    }

def main():
    df = pd.read_csv(DATA)
    # Filter post-9:50
    mask_950 = df["time"].apply(after_950)
    df_post = df[mask_950].copy()
    n_total = len(df)
    n_post = len(df_post)

    lines = []
    lines.append("# v29 MC Factor Screen — Post-9:50 Signals\n")
    lines.append(f"**Data:** {n_total} total signals → {n_post} after 9:50 filter\n")
    lines.append(f"**Date:** 2026-03-04\n")

    # ── STEP 1: Full Factor Screen ──
    lines.append("\n## Step 1: Full Factor Screen\n")

    # Define all features as (name, mask_with)
    features = []

    # Binary/categorical
    features.append(("direction=bear", df_post["direction"] == "bear"))
    features.append(("type=BRK", df_post["type"] == "BRK"))
    features.append(("type=REV", df_post["type"] == "REV"))
    features.append(("vwap=below", df_post["vwap"] == "below"))
    features.append(("ema=bull", df_post["ema"] == "bull"))
    features.append(("with_trend=True", df_post["with_trend"] == True))
    features.append(("multi_level=True", df_post["multi_level"] == True))
    features.append(("level_type=LOW", df_post["level_type"] == "LOW"))

    # Counter-VWAP
    counter_vwap = ((df_post["direction"] == "bull") & (df_post["vwap"] == "below")) | \
                   ((df_post["direction"] == "bear") & (df_post["vwap"] == "above"))
    features.append(("Counter-VWAP", counter_vwap))

    # EMA aligned with direction
    ema_aligned = ((df_post["direction"] == "bull") & (df_post["ema"] == "bull")) | \
                  ((df_post["direction"] == "bear") & (df_post["ema"] == "bear"))
    features.append(("EMA-aligned", ema_aligned))

    # CONF pass
    conf_pass = df_post["conf"].isin(["✓", "✓★"])
    features.append(("conf=✓/✓★", conf_pass))

    # Body thresholds
    features.append(("body<50", df_post["body"] < 50))
    features.append(("body<80", df_post["body"] < 80))

    # Volume thresholds
    features.append(("vol<2", df_post["vol"] < 2))
    features.append(("vol<5", df_post["vol"] < 5))

    # ADX thresholds
    features.append(("adx>25", df_post["adx"] > 25))
    features.append(("adx<30", df_post["adx"] < 30))

    # RS
    if "rs" in df_post.columns and df_post["rs"].notna().sum() > 0:
        features.append(("rs>0", df_post["rs"] > 0))

    # Time-based
    features.append(("time<11:00", df_post["time"].apply(lambda t: time_in_range(t, 0, 0, 11, 0))))
    features.append(("time 10:00-11:00", df_post["time"].apply(lambda t: time_in_range(t, 10, 0, 11, 0))))
    features.append(("time 10:30-12:00", df_post["time"].apply(lambda t: time_in_range(t, 10, 30, 12, 0))))
    features.append(("time<14:00", df_post["time"].apply(lambda t: time_in_range(t, 0, 0, 14, 0))))
    features.append(("time 11:00-12:00", df_post["time"].apply(lambda t: time_in_range(t, 11, 0, 12, 0))))

    # Compute metrics for each feature
    results = []
    for name, mask in features:
        m_with = compute_metrics(df_post[mask])
        m_without = compute_metrics(df_post[~mask])
        delta_mfe = m_with["Avg_MFE"] - m_without["Avg_MFE"]
        delta_mae = m_with["Avg_MAE"] - m_without["Avg_MAE"]
        results.append({
            "Feature": name,
            "N_with": m_with["N"], "N_without": m_without["N"],
            "MFE_with": m_with["Avg_MFE"], "MFE_without": m_without["Avg_MFE"],
            "Delta_MFE": round(delta_mfe, 4),
            "MAE_with": m_with["Avg_MAE"], "MAE_without": m_without["Avg_MAE"],
            "Delta_MAE": round(delta_mae, 4),
            "Ratio_with": m_with["MFE_MAE"], "Ratio_without": m_without["MFE_MAE"],
            "Win%_with": m_with["Win%"], "Win%_without": m_without["Win%"],
            "Runner%_with": m_with["Runner%"], "Runner%_without": m_without["Runner%"],
        })

    # Sort by Delta_MFE descending
    results.sort(key=lambda x: x["Delta_MFE"], reverse=True)

    # Table
    lines.append("| Rank | Feature | N(with) | N(w/o) | MFE(with) | MFE(w/o) | **ΔMFE** | MAE(with) | MAE(w/o) | Ratio(w) | Ratio(w/o) | Win%(w) | Win%(w/o) | Run%(w) | Run%(w/o) |")
    lines.append("|------|---------|---------|--------|-----------|----------|----------|-----------|----------|----------|------------|---------|-----------|---------|-----------|")
    for i, r in enumerate(results, 1):
        lines.append(f"| {i} | {r['Feature']} | {r['N_with']} | {r['N_without']} | {r['MFE_with']:.4f} | {r['MFE_without']:.4f} | **{r['Delta_MFE']:+.4f}** | {r['MAE_with']:.4f} | {r['MAE_without']:.4f} | {r['Ratio_with']:.3f} | {r['Ratio_without']:.3f} | {r['Win%_with']:.1f} | {r['Win%_without']:.1f} | {r['Runner%_with']:.1f} | {r['Runner%_without']:.1f} |")

    lines.append(f"\n**Interpretation:** Positive ΔMFE = feature helps. Top factors are best filters.\n")

    # ── STEP 2: Build Revised Option C ──
    lines.append("\n## Step 2: Revised Option C Scoring\n")

    # Pick top positive-delta factors that are reasonably independent
    # We'll use the top factors, but need to check independence
    positive_factors = [(r["Feature"], r["Delta_MFE"]) for r in results if r["Delta_MFE"] > 0]
    lines.append("### Positive-delta factors (candidates):\n")
    for name, delta in positive_factors:
        lines.append(f"- **{name}**: ΔMFE = {delta:+.4f}")
    lines.append("")

    # Build scoring: Counter-VWAP gets +2 if positive, rest get +1
    # Identify which factors to include (top independent ones)
    # Exclude highly correlated pairs
    # We'll use these core factors for scoring:
    score_factors = []
    used_concepts = set()

    for r in results:
        name = r["Feature"]
        delta = r["Delta_MFE"]
        if delta <= 0:
            continue
        # Skip if concept already covered
        concept = None
        if "VWAP" in name and "Counter" in name:
            concept = "counter_vwap"
        elif "ema" in name.lower() or "EMA" in name:
            concept = "ema"
        elif "time" in name.lower():
            concept = "time"
        elif "body" in name.lower():
            concept = "body"
        elif "vol" in name.lower():
            concept = "vol"
        elif "adx" in name.lower():
            concept = "adx"
        elif "conf" in name.lower():
            concept = "conf"
        elif "trend" in name.lower():
            concept = "trend"
        elif "direction" in name.lower():
            concept = "direction"
        elif "level" in name.lower() and "type" in name.lower():
            concept = "level_type"
        elif "multi" in name.lower():
            concept = "multi_level"
        elif "type=" in name:
            concept = "signal_type"
        elif "rs" in name.lower():
            concept = "rs"
        elif "vwap" in name.lower():
            concept = "vwap_side"
        else:
            concept = name

        if concept in used_concepts:
            continue
        used_concepts.add(concept)
        score_factors.append((name, delta, concept))

    lines.append("### Selected scoring factors (one per concept, positive delta only):\n")
    lines.append("| Factor | ΔMFE | Points |")
    lines.append("|--------|------|--------|")

    # Assign points: Counter-VWAP = +2, others = +1
    scoring_rules = []
    for name, delta, concept in score_factors:
        pts = 2 if concept == "counter_vwap" else 1
        scoring_rules.append((name, pts, concept))
        lines.append(f"| {name} | {delta:+.4f} | {pts} |")

    max_score = sum(p for _, p, _ in scoring_rules)
    lines.append(f"\n**Max possible score: {max_score}**\n")

    # Compute score for each signal
    score_col = pd.Series(0, index=df_post.index)
    for name, pts, concept in scoring_rules:
        # Find the mask for this feature
        for feat_name, feat_mask in features:
            if feat_name == name:
                score_col += feat_mask.astype(int) * pts
                break

    df_post = df_post.copy()
    df_post["score"] = score_col

    # Score distribution
    lines.append("### Score Distribution:\n")
    lines.append("| Score | N | Avg MFE | Avg MAE | MFE/MAE | Win% | Runner% |")
    lines.append("|-------|---|---------|---------|---------|------|---------|")
    for s in sorted(df_post["score"].unique()):
        sub = df_post[df_post["score"] == s]
        m = compute_metrics(sub)
        lines.append(f"| {s} | {m['N']} | {m['Avg_MFE']:.4f} | {m['Avg_MAE']:.4f} | {m['MFE_MAE']:.3f} | {m['Win%']:.1f} | {m['Runner%']:.1f} |")

    # ── STEP 3: Compare Options ──
    lines.append("\n## Step 3: Option Comparison\n")

    # Baseline
    baseline = compute_metrics(df_post)

    # Option A: Counter-VWAP only
    opt_a = compute_metrics(df_post[counter_vwap])

    # Option C variants
    comparisons = [
        ("Baseline (all post-9:50)", baseline),
        ("Option A: Counter-VWAP only", opt_a),
    ]

    for thresh in [2, 3, 4, 5, 6]:
        sub = df_post[df_post["score"] >= thresh]
        if len(sub) > 0:
            m = compute_metrics(sub)
            comparisons.append((f"Revised C: score >= {thresh}", m))

    # Option A + best additional filters
    # Find the best non-VWAP factor
    best_addon = None
    best_addon_mask = None
    for name, delta, concept in score_factors:
        if concept == "counter_vwap":
            continue
        # Use first (highest delta) non-VWAP factor
        if best_addon is None:
            best_addon = name
            for feat_name, feat_mask in features:
                if feat_name == name:
                    best_addon_mask = feat_mask
                    break

    if best_addon_mask is not None:
        combined = counter_vwap & best_addon_mask
        m = compute_metrics(df_post[combined])
        comparisons.append((f"Option A + {best_addon}", m))

    # Also try top 2 addons
    addon_masks = []
    addon_names = []
    for name, delta, concept in score_factors:
        if concept == "counter_vwap":
            continue
        for feat_name, feat_mask in features:
            if feat_name == name:
                addon_masks.append(feat_mask)
                addon_names.append(name)
                break
        if len(addon_masks) >= 3:
            break

    if len(addon_masks) >= 2:
        combined2 = counter_vwap & addon_masks[0] & addon_masks[1]
        m = compute_metrics(df_post[combined2])
        comparisons.append((f"Option A + {addon_names[0]} + {addon_names[1]}", m))

    if len(addon_masks) >= 3:
        combined3 = counter_vwap & addon_masks[0] & addon_masks[1] & addon_masks[2]
        m = compute_metrics(df_post[combined3])
        comparisons.append((f"Option A + top3 addons", m))

    lines.append("| Option | N | Avg MFE | Avg MAE | MFE/MAE | Win% | Runner% | Total PnL | Per-Signal PnL |")
    lines.append("|--------|---|---------|---------|---------|------|---------|-----------|----------------|")
    for label, m in comparisons:
        lines.append(f"| {label} | {m['N']} | {m['Avg_MFE']:.4f} | {m['Avg_MAE']:.4f} | {m['MFE_MAE']:.3f} | {m['Win%']:.1f} | {m['Runner%']:.1f} | {m['Total_PnL']:.3f} | {m['Per_Signal_PnL']:.4f} |")

    # ── STEP 4: Interaction Analysis ──
    lines.append("\n## Step 4: Interaction Analysis (Factor + Counter-VWAP)\n")
    lines.append("Does each factor add value ON TOP of Counter-VWAP, or is it redundant?\n")

    lines.append("| Factor | CV+Factor N | CV+Factor MFE | CV+Factor Run% | CV only N | CV only MFE | CV only Run% | Factor only N | Factor only MFE | Factor only Run% | **Lift over CV** |")
    lines.append("|--------|-------------|---------------|----------------|-----------|-------------|--------------|---------------|-----------------|------------------|------------------|")

    for name, delta, concept in score_factors:
        if concept == "counter_vwap":
            continue
        for feat_name, feat_mask in features:
            if feat_name == name:
                # CV + factor
                both = counter_vwap & feat_mask
                m_both = compute_metrics(df_post[both])
                # CV only (without this factor)
                cv_only = counter_vwap & ~feat_mask
                m_cv_only = compute_metrics(df_post[cv_only])
                # Factor only (without CV)
                f_only = feat_mask & ~counter_vwap
                m_f_only = compute_metrics(df_post[f_only])
                # Lift = CV+Factor MFE minus CV-only MFE
                lift = m_both["Avg_MFE"] - m_cv_only["Avg_MFE"] if m_cv_only["N"] > 0 else 0
                lines.append(f"| {name} | {m_both['N']} | {m_both['Avg_MFE']:.4f} | {m_both['Runner%']:.1f} | {m_cv_only['N']} | {m_cv_only['Avg_MFE']:.4f} | {m_cv_only['Runner%']:.1f} | {m_f_only['N']} | {m_f_only['Avg_MFE']:.4f} | {m_f_only['Runner%']:.1f} | **{lift:+.4f}** |")
                break

    # Also do negative-delta factors that might still interact well with CV
    lines.append("\n### Negative-delta factors (checking if they interact with CV):\n")
    negative_factors = [(r["Feature"], r["Delta_MFE"]) for r in results if r["Delta_MFE"] <= 0]
    for name, delta in negative_factors[:5]:
        for feat_name, feat_mask in features:
            if feat_name == name:
                both = counter_vwap & feat_mask
                m_both = compute_metrics(df_post[both])
                cv_only = counter_vwap & ~feat_mask
                m_cv_only = compute_metrics(df_post[cv_only])
                lift = m_both["Avg_MFE"] - m_cv_only["Avg_MFE"] if m_cv_only["N"] > 0 else 0
                lines.append(f"- **{name}** (solo ΔMFE={delta:+.4f}): CV+factor MFE={m_both['Avg_MFE']:.4f} (n={m_both['N']}), CV w/o={m_cv_only['Avg_MFE']:.4f} (n={m_cv_only['N']}), lift={lift:+.4f}")
                break

    # ── Summary ──
    lines.append("\n## Summary & Recommendations\n")

    # Find best option
    best_label = ""
    best_per_signal = -999
    for label, m in comparisons:
        if m["Per_Signal_PnL"] > best_per_signal and m["N"] >= 20:
            best_per_signal = m["Per_Signal_PnL"]
            best_label = label

    lines.append(f"**Best per-signal PnL (N>=20):** {best_label} at {best_per_signal:+.4f} ATR/signal\n")

    # Find best total PnL
    best_total_label = ""
    best_total = -999
    for label, m in comparisons:
        if m["Total_PnL"] > best_total:
            best_total = m["Total_PnL"]
            best_total_label = label

    lines.append(f"**Best total PnL:** {best_total_label} at {best_total:+.3f} ATR\n")

    # Top 5 factor deltas
    lines.append("### Top 5 differentiating factors:\n")
    for i, r in enumerate(results[:5], 1):
        lines.append(f"{i}. **{r['Feature']}**: ΔMFE = {r['Delta_MFE']:+.4f} (n={r['N_with']}/{r['N_without']})")

    lines.append("")

    # Write output
    OUT.write_text("\n".join(lines))
    print(f"Results written to {OUT}")
    print(f"Post-9:50 signals: {n_post}/{n_total}")
    top3 = ", ".join(r["Feature"] + " (%+.4f)" % r["Delta_MFE"] for r in results[:3])
    print(f"Top 3 factors: {top3}")
    print(f"Best option (N>=20): {best_label} — {best_per_signal:+.4f}/signal")

if __name__ == "__main__":
    main()
