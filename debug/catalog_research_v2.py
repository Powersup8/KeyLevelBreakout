#!/usr/bin/env python3
"""Near-level factor screen: what pre-move conditions predict great moves AT levels?"""

import pandas as pd
import numpy as np
from itertools import combinations

df = pd.read_parquet("debug/move-catalog.parquet")
p = df[(df["pass"] == "primary") & (df["symbol"] != "TSM")].copy()

# Label
has_1m = p["mfe_1m"].notna()
p["is_great"] = (
    (has_1m & (p["mae_1m"] > 0)
     & (p["mfe_1m"] / p["mae_1m"].clip(lower=0.001) >= 3)
     & (p["mfe_1m"] >= 0.30)
     & (p["retracement_12bar"] <= 0.40))
    | (~has_1m & (p["magnitude_atr"] >= 0.50) & (p["retracement_12bar"] <= 0.40))
)
p["is_noise"] = (has_1m & (p["mae_1m"] > p["mfe_1m"])) | (p["retracement_6bar"] > 0.80)

baseline = p["is_great"].mean()
print(f"Full dataset: {len(p):,} moves, great={baseline:.1%}")

# ── Subset: moves near key levels (within 0.2 ATR) ──
near_level = p[p["nearest_level_dist_atr"] <= 0.20].copy()
bl_level = near_level["is_great"].mean()
print(f"Near-level subset: {len(near_level):,} moves, great={bl_level:.1%}")

# ── Define pre-move boolean conditions ──
conditions = {}

# Timing
conditions["midday"] = near_level["timing_category"] == "midday"
conditions["afternoon"] = near_level["timing_category"] == "afternoon"
conditions["morning"] = near_level["timing_category"] == "morning"
conditions["open_flush"] = near_level["timing_category"] == "open_flush"

# Trend/Regime
conditions["adx>30"] = near_level["pre_adx"] > 30
conditions["adx<20"] = near_level["pre_adx"] < 20
conditions["ema_aligned"] = near_level["trig_ema_aligned"] == True
conditions["vwap_aligned"] = near_level["trig_vwap_aligned"] == True
conditions["both_aligned"] = conditions["ema_aligned"] & conditions["vwap_aligned"]

# Volume
conditions["low_prevol"] = near_level["pre_vol_avg_ratio"] < 0.5
conditions["normal_prevol"] = (near_level["pre_vol_avg_ratio"] >= 0.5) & (near_level["pre_vol_avg_ratio"] <= 1.5)
conditions["high_trig_vol"] = near_level["trig_vol_ratio"] > 2
conditions["low_trig_vol"] = near_level["trig_vol_ratio"] < 1

# Level context
conditions["dense_levels(>5)"] = near_level["n_levels_within_05"] > 5
conditions["broke_through"] = near_level["level_interaction"] == "broke_through"

# Pattern
conditions["level_breakout"] = near_level["pattern_category"] == "level_breakout"
conditions["reversal"] = near_level["pattern_category"] == "reversal"

# Candle
conditions["big_body"] = near_level["trig_body_pct"] > 70
conditions["small_range"] = near_level["trig_range_atr"] < 0.5

# Context
conditions["broad_move"] = near_level["context_category"] == "broad_move"
conditions["isolated"] = near_level["context_category"] == "isolated"
conditions["spy_bull"] = near_level["spy_direction"] == "bull"

# Compression
conditions["compressed(<0.5)"] = near_level["pre_compression"] < 0.5

# Direction
conditions["bull"] = near_level["direction"] == "bull"
conditions["bear"] = near_level["direction"] == "bear"

# EMA slope
conditions["flat_ema"] = near_level["pre_ema21_slope"].abs() < 0.005
conditions["trending_ema"] = near_level["pre_ema21_slope"].abs() > 0.02

# ── Single factors ──
print(f"\n{'='*70}")
print(f"NEAR-LEVEL SINGLE FACTORS (within 0.2 ATR of level)")
print(f"Baseline great rate: {bl_level:.1%}")
print(f"{'='*70}")

singles = []
for name, mask in conditions.items():
    n = mask.sum()
    if n < 30:
        continue
    great_r = near_level.loc[mask, "is_great"].mean()
    noise_r = near_level.loc[mask, "is_noise"].mean()
    lift = great_r / bl_level
    singles.append({"name": name, "N": n, "great_pct": great_r, "lift": lift, "noise_pct": noise_r})

singles_df = pd.DataFrame(singles).sort_values("lift", ascending=False)
print(f"\n  {'Name':25s}  {'N':>6s}  {'Great':>7s}  {'Lift':>5s}  {'Noise':>7s}")
print(f"  {'-'*25}  {'-'*6}  {'-'*7}  {'-'*5}  {'-'*7}")
for _, r in singles_df.iterrows():
    print(f"  {r['name']:25s}  {r['N']:6.0f}  {r['great_pct']:7.1%}  {r['lift']:5.2f}x  {r['noise_pct']:7.1%}")

# ── 2-way combos ──
print(f"\n{'='*70}")
print(f"NEAR-LEVEL 2-WAY COMBOS (lift >= 1.3x, N >= 30)")
print(f"{'='*70}")

combos = []
names = list(conditions.keys())
for a, b in combinations(names, 2):
    mask = conditions[a] & conditions[b]
    n = mask.sum()
    if n < 30:
        continue
    great_r = near_level.loc[mask, "is_great"].mean()
    lift = great_r / bl_level
    if lift < 1.3:
        continue
    noise_r = near_level.loc[mask, "is_noise"].mean()
    mfe_mask = mask & has_1m[near_level.index].reindex(near_level.index, fill_value=False)
    mfe_val = near_level.loc[mfe_mask, "mfe_1m"].mean() if mfe_mask.sum() > 5 else float("nan")
    combos.append({"combo": f"{a} + {b}", "N": n, "great_pct": great_r,
                    "lift": lift, "noise_pct": noise_r, "mfe_1m": mfe_val})

combos_df = pd.DataFrame(combos).sort_values("lift", ascending=False) if combos else pd.DataFrame()
print(f"  Found {len(combos_df)} combos meeting threshold\n")
if len(combos_df) > 0:
    for _, r in combos_df.head(25).iterrows():
        mfe_str = f"  MFE={r['mfe_1m']:.3f}" if pd.notna(r["mfe_1m"]) else ""
        print(f"  {r['combo']:45s}  N={r['N']:5.0f}  great={r['great_pct']:.1%} ({r['lift']:.2f}x)"
              f"  noise={r['noise_pct']:.1%}{mfe_str}")

# ── 3-way combos ──
print(f"\n{'='*70}")
print(f"NEAR-LEVEL 3-WAY COMBOS (lift >= 1.5x, N >= 30)")
print(f"{'='*70}")

combos3 = []
for a, b, c in combinations(names, 3):
    mask = conditions[a] & conditions[b] & conditions[c]
    n = mask.sum()
    if n < 30:
        continue
    great_r = near_level.loc[mask, "is_great"].mean()
    lift = great_r / bl_level
    if lift < 1.5:
        continue
    noise_r = near_level.loc[mask, "is_noise"].mean()
    combos3.append({"combo": f"{a} + {b} + {c}", "N": n, "great_pct": great_r,
                     "lift": lift, "noise_pct": noise_r})

combos3_df = pd.DataFrame(combos3).sort_values("lift", ascending=False) if combos3 else pd.DataFrame()
print(f"  Found {len(combos3_df)} combos meeting threshold\n")
if len(combos3_df) > 0:
    for _, r in combos3_df.head(20).iterrows():
        print(f"  {r['combo']:55s}  N={r['N']:5.0f}  great={r['great_pct']:.1%} ({r['lift']:.2f}x)"
              f"  noise={r['noise_pct']:.1%}")

# ── Level-type breakdown ──
print(f"\n{'='*70}")
print(f"GREAT RATE BY LEVEL TYPE (near-level subset)")
print(f"{'='*70}")
for lt in near_level["nearest_level_type"].value_counts().index:
    sub = near_level[near_level["nearest_level_type"] == lt]
    if len(sub) < 30:
        continue
    gr = sub["is_great"].mean()
    nr = sub["is_noise"].mean()
    lift = gr / bl_level
    print(f"  {lt:20s}  N={len(sub):5d}  great={gr:.1%} ({lift:.2f}x)  noise={nr:.1%}")
