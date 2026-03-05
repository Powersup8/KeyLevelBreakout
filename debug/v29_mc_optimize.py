#!/usr/bin/env python3
"""
v29 MC Quality Scoring Optimization — 4 rounds + final comparison.

Rounds:
  2: Factor redundancy & clean factor set (removes CONF cheating)
  3: Threshold + weight optimization
  4: Validation (time-split, symbol-split, stability)
  5: Final head-to-head comparison

Data: enriched-signals.csv, post-9:50 only (N=1003).
Output: v29-mc-optimize.md
"""

import pandas as pd
import numpy as np
from itertools import combinations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ── Data loading ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
df_all = pd.read_csv(SCRIPT_DIR / 'enriched-signals.csv')

# Parse time into minutes
df_all['hour'] = df_all['time'].apply(lambda t: int(t.split(':')[0]))
df_all['minute'] = df_all['time'].apply(lambda t: int(t.split(':')[1]))
df_all['time_minutes'] = df_all['hour'] * 60 + df_all['minute']

# Post-9:50 filter
df = df_all[df_all['time_minutes'] >= 9*60+50].copy()

# Derived columns
df['pnl'] = df['mfe'] + df['mae']
df['win'] = df['mfe'] > df['mae'].abs()
df['runner'] = df['mfe'] >= 1.0
df['counter_vwap'] = ~df['with_trend']

# Date for time-split
df['date_parsed'] = pd.to_datetime(df['date'])

print(f"Post-9:50 signals: {len(df)}")
print(f"Mean PnL: {df['pnl'].mean():.4f}, Win%: {df['win'].mean():.1%}, Runner%: {df['runner'].mean():.1%}")

# ── Helper functions ──────────────────────────────────────────────────────────
def metrics(subset, label=""):
    """Compute standard metrics for a subset."""
    n = len(subset)
    if n == 0:
        return {'label': label, 'N': 0, 'pnl_per': 0, 'total_pnl': 0,
                'mfe_mae': 0, 'win_pct': 0, 'runner_pct': 0, 'avg_mfe': 0, 'avg_mae': 0}
    return {
        'label': label,
        'N': n,
        'pnl_per': subset['pnl'].mean(),
        'total_pnl': subset['pnl'].sum(),
        'mfe_mae': subset['mfe'].mean() / abs(subset['mae'].mean()) if subset['mae'].mean() != 0 else 0,
        'win_pct': subset['win'].mean(),
        'runner_pct': subset['runner'].mean(),
        'avg_mfe': subset['mfe'].mean(),
        'avg_mae': subset['mae'].mean(),
    }

def metrics_row(m):
    """Format metrics dict as markdown table row."""
    return (f"| {m['label']:<35s} | {m['N']:>5d} | {m['pnl_per']:>+7.3f} | "
            f"{m['total_pnl']:>+8.1f} | {m['mfe_mae']:>5.2f} | "
            f"{m['win_pct']:>5.1%} | {m['runner_pct']:>6.1%} | {m['avg_mfe']:>6.3f} | {m['avg_mae']:>7.3f} |")

METRICS_HEADER = (
    "| Config                              |     N | PnL/sig | Tot PnL | MFE/MAE | Win%  | Runner% | Avg MFE | Avg MAE |\n"
    "|-------------------------------------|-------|---------|---------|---------|-------|---------|---------|---------|"
)

def phi_coefficient(a, b):
    """Phi coefficient for two boolean series."""
    a, b = a.astype(int), b.astype(int)
    n = len(a)
    n11 = ((a == 1) & (b == 1)).sum()
    n10 = ((a == 1) & (b == 0)).sum()
    n01 = ((a == 0) & (b == 1)).sum()
    n00 = ((a == 0) & (b == 0)).sum()
    denom = np.sqrt((n11+n10)*(n01+n00)*(n11+n01)*(n10+n00))
    if denom == 0:
        return 0.0
    return (n11*n00 - n10*n01) / denom

# ── Build binary factor columns ──────────────────────────────────────────────
# These are the 8 factors from Round 1 (minus CONF which is cheating)
df['f_time_lt11'] = df['time_minutes'] < 11*60
df['f_adx_gt25'] = df['adx'] > 25
df['f_dir_bear'] = df['direction'] == 'bear'
df['f_vwap_below'] = df['vwap'] == 'below'
df['f_ema_aligned'] = ((df['direction'] == 'bull') & (df['ema'] == 'bull')) | \
                      ((df['direction'] == 'bear') & (df['ema'] == 'bear'))
df['f_counter_vwap'] = df['counter_vwap']
df['f_level_low'] = df['level_type'] == 'LOW'
df['f_type_brk'] = df['type'] == 'BRK'

FACTOR_NAMES = ['f_time_lt11', 'f_adx_gt25', 'f_dir_bear', 'f_vwap_below',
                'f_ema_aligned', 'f_counter_vwap', 'f_level_low', 'f_type_brk']

FACTOR_LABELS = {
    'f_time_lt11': 'Time < 11:00',
    'f_adx_gt25': 'ADX > 25',
    'f_dir_bear': 'Dir = Bear',
    'f_vwap_below': 'VWAP = Below',
    'f_ema_aligned': 'EMA Aligned',
    'f_counter_vwap': 'Counter-VWAP',
    'f_level_low': 'Level = LOW',
    'f_type_brk': 'Type = BRK',
}

out = []  # collect output lines

# ═══════════════════════════════════════════════════════════════════════════════
# ROUND 2: Clean Up — Remove Cheating + Test Redundancy
# ═══════════════════════════════════════════════════════════════════════════════
out.append("# v29 MC Quality Scoring Optimization\n")
out.append(f"**Data:** enriched-signals.csv, post-9:50 only, N={len(df)}")
out.append(f"**Date:** 2026-03-04\n")
out.append(f"**Baseline:** Mean PnL={df['pnl'].mean():.4f}, Win%={df['win'].mean():.1%}, "
           f"Runner%={df['runner'].mean():.1%}\n")

out.append("---\n")
out.append("## Round 2: Clean Up — Remove Cheating + Test Redundancy\n")

# 2a: Factor redundancy matrix
out.append("### 2a. Factor Redundancy Matrix\n")
out.append("**Phi Coefficient** (correlation for binary variables, >0.5 = redundant):\n")

# Header
header = "| Factor           |"
for fn in FACTOR_NAMES:
    header += f" {FACTOR_LABELS[fn][:10]:>10s} |"
out.append(header)
sep = "|------------------|"
for _ in FACTOR_NAMES:
    sep += "------------|"
out.append(sep)

for fi in FACTOR_NAMES:
    row = f"| {FACTOR_LABELS[fi]:<16s} |"
    for fj in FACTOR_NAMES:
        if fi == fj:
            row += "       --   |"
        else:
            phi = phi_coefficient(df[fi], df[fj])
            marker = " **" if abs(phi) > 0.5 else "   "
            row += f" {phi:>+6.3f}{marker} |"
    out.append(row)

out.append("")

# High correlations
out.append("**High correlations (|phi| > 0.3):**\n")
seen = set()
for fi, fj in combinations(FACTOR_NAMES, 2):
    phi = phi_coefficient(df[fi], df[fj])
    if abs(phi) > 0.3 and (fj, fi) not in seen:
        seen.add((fi, fj))
        out.append(f"- {FACTOR_LABELS[fi]} <-> {FACTOR_LABELS[fj]}: phi={phi:+.3f}")
out.append("")

# 2a continued: Conditional lift
out.append("### 2a (cont). Conditional Lift — Does Factor B Add Edge When A Is Already True?\n")
out.append("| Factor A (given) | Factor B (added) | MFE(A only) | MFE(A+B) | Lift  | N(A+B) |")
out.append("|------------------|------------------|-------------|----------|-------|--------|")

lift_data = []
for fi in FACTOR_NAMES:
    for fj in FACTOR_NAMES:
        if fi == fj:
            continue
        mask_a = df[fi]
        mask_ab = df[fi] & df[fj]
        if mask_a.sum() < 10 or mask_ab.sum() < 10:
            continue
        mfe_a = df.loc[mask_a, 'pnl'].mean()
        mfe_ab = df.loc[mask_ab, 'pnl'].mean()
        lift = mfe_ab - mfe_a
        lift_data.append((fi, fj, mfe_a, mfe_ab, lift, mask_ab.sum()))

# Show top 15 lifts and bottom 5
lift_data.sort(key=lambda x: x[4], reverse=True)
for fi, fj, mfe_a, mfe_ab, lift, n in lift_data[:15]:
    out.append(f"| {FACTOR_LABELS[fi]:<16s} | {FACTOR_LABELS[fj]:<16s} | {mfe_a:>+10.4f}  | {mfe_ab:>+7.4f} | {lift:>+5.3f} | {n:>6d} |")
out.append("| ...                | ...              |             |          |       |        |")
for fi, fj, mfe_a, mfe_ab, lift, n in lift_data[-5:]:
    out.append(f"| {FACTOR_LABELS[fi]:<16s} | {FACTOR_LABELS[fj]:<16s} | {mfe_a:>+10.4f}  | {mfe_ab:>+7.4f} | {lift:>+5.3f} | {n:>6d} |")

out.append("")

# 2b: Identify redundancies and build clean set
out.append("### 2b. Redundancy Analysis & Clean Factor Set\n")

# Check Dir=Bear vs VWAP=Below and Counter-VWAP
phi_bear_vwap = phi_coefficient(df['f_dir_bear'], df['f_vwap_below'])
phi_bear_counter = phi_coefficient(df['f_dir_bear'], df['f_counter_vwap'])
phi_vwap_counter = phi_coefficient(df['f_vwap_below'], df['f_counter_vwap'])

# Individual factor performance
out.append("**Individual factor MFE deltas (factor=True vs False):**\n")
out.append("| Factor           | N(True) | PnL(True) | PnL(False) | Delta  | Win%(T) | Win%(F) |")
out.append("|------------------|---------|-----------|------------|--------|---------|---------|")

factor_deltas = {}
for fn in FACTOR_NAMES:
    t = df[df[fn]]
    f_ = df[~df[fn]]
    if len(t) < 5 or len(f_) < 5:
        continue
    delta = t['pnl'].mean() - f_['pnl'].mean()
    factor_deltas[fn] = delta
    out.append(f"| {FACTOR_LABELS[fn]:<16s} | {len(t):>7d} | {t['pnl'].mean():>+9.4f} | {f_['pnl'].mean():>+9.4f}  | {delta:>+6.4f} | {t['win'].mean():>6.1%} | {f_['win'].mean():>6.1%} |")

out.append("")

# Decide which to keep
# Check specific redundancy: Dir=Bear, VWAP=Below, Counter-VWAP overlap
overlap_bear_vwap = (df['f_dir_bear'] & df['f_vwap_below']).sum()
overlap_bear_counter = (df['f_dir_bear'] & df['f_counter_vwap']).sum()
only_bear = df['f_dir_bear'].sum()
only_vwap = df['f_vwap_below'].sum()
only_counter = df['f_counter_vwap'].sum()

out.append(f"**Overlap check (bear/vwap/counter-VWAP):**")
out.append(f"- Dir=Bear: N={only_bear}, VWAP=Below: N={only_vwap}, Counter-VWAP: N={only_counter}")
out.append(f"- Bear AND VWAP=Below: N={overlap_bear_vwap} ({overlap_bear_vwap/only_bear:.0%} of bears)")
out.append(f"- Bear AND Counter-VWAP: N={overlap_bear_counter}")
out.append(f"- Phi(Bear, VWAP=Below)={phi_bear_vwap:+.3f}, Phi(Bear, Counter)={phi_bear_counter:+.3f}")
out.append("")

# EMA aligned vs dir bear
phi_ema_bear = phi_coefficient(df['f_ema_aligned'], df['f_dir_bear'])
phi_ema_vwap = phi_coefficient(df['f_ema_aligned'], df['f_vwap_below'])
out.append(f"- Phi(EMA aligned, Bear)={phi_ema_bear:+.3f}, Phi(EMA, VWAP below)={phi_ema_vwap:+.3f}")
out.append("")

# Decision on clean set
out.append("**Decision:**")
out.append("- **REMOVE CONF** (not available at signal time — this was cheating)")
out.append(f"- Dir=Bear and VWAP=Below have phi={phi_bear_vwap:+.3f}. "
           f"They overlap {overlap_bear_vwap/only_bear:.0%} of the time.")

# Keep the one with higher delta
delta_bear = factor_deltas.get('f_dir_bear', 0)
delta_vwap = factor_deltas.get('f_vwap_below', 0)
if abs(phi_bear_vwap) > 0.5:
    if delta_bear > delta_vwap:
        out.append(f"  -> Keep Dir=Bear (delta={delta_bear:+.4f}), remove VWAP=Below (delta={delta_vwap:+.4f})")
        redundant = 'f_vwap_below'
    else:
        out.append(f"  -> Keep VWAP=Below (delta={delta_vwap:+.4f}), remove Dir=Bear (delta={delta_bear:+.4f})")
        redundant = 'f_dir_bear'
else:
    out.append(f"  -> Both kept (phi < 0.5, independent enough)")
    redundant = None

# Counter-VWAP: only 52 signals, check if it's just noise
out.append(f"- Counter-VWAP: only N={only_counter} signals. Check if meaningful or noise.")
counter_pnl = df[df['f_counter_vwap']]['pnl'].mean()
noncounter_pnl = df[~df['f_counter_vwap']]['pnl'].mean()
out.append(f"  Counter-VWAP PnL={counter_pnl:+.4f} vs non-counter={noncounter_pnl:+.4f}")
out.append("")

# Build clean factor set
clean_factors = [fn for fn in FACTOR_NAMES]
# Always remove factors with essentially zero or negative delta
removals = []
for fn in clean_factors[:]:
    delta = factor_deltas.get(fn, 0)
    if delta <= 0:
        removals.append((fn, delta))

# Remove redundant pair if applicable
if redundant and redundant in clean_factors:
    clean_factors.remove(redundant)
    out.append(f"  Removed: {FACTOR_LABELS[redundant]} (redundant)")

for fn, d in removals:
    if fn in clean_factors:
        clean_factors.remove(fn)
        out.append(f"  Removed: {FACTOR_LABELS[fn]} (delta={d:+.4f}, zero/negative)")

out.append(f"\n**Clean factor set ({len(clean_factors)} factors):**")
for fn in clean_factors:
    out.append(f"  - {FACTOR_LABELS[fn]} (delta={factor_deltas.get(fn, 0):+.4f})")
out.append("")

# 2c: Test score with clean factors
out.append("### 2c. Clean Score Distribution & Performance\n")

df['clean_score'] = sum(df[fn].astype(int) for fn in clean_factors)
max_score = df['clean_score'].max()

out.append(METRICS_HEADER)
for thresh in range(0, max_score + 1):
    subset = df[df['clean_score'] >= thresh]
    m = metrics(subset, f"Score >= {thresh}")
    out.append(metrics_row(m))

out.append("")

# Also show exact score bins
out.append("**By exact score:**\n")
out.append("| Score | N    | PnL/sig | Win%  | Runner% |")
out.append("|-------|------|---------|-------|---------|")
for s in range(0, max_score + 1):
    subset = df[df['clean_score'] == s]
    if len(subset) > 0:
        out.append(f"| {s}     | {len(subset):>4d} | {subset['pnl'].mean():>+7.3f} | {subset['win'].mean():>5.1%} | {subset['runner'].mean():>6.1%} |")

out.append("")
out.append("**Round 2 Learnings:**")
r2_best_thresh = None
r2_best_total = -999
for thresh in range(0, max_score + 1):
    subset = df[df['clean_score'] >= thresh]
    if len(subset) >= 20:
        total = subset['pnl'].sum()
        if total > r2_best_total:
            r2_best_total = total
            r2_best_thresh = thresh

r2_best = df[df['clean_score'] >= r2_best_thresh]
out.append(f"- Best threshold: Score >= {r2_best_thresh} (N={len(r2_best)}, "
           f"total PnL={r2_best['pnl'].sum():+.1f}, per-signal={r2_best['pnl'].mean():+.4f})")
out.append(f"- Clean set has {len(clean_factors)} factors (removed CONF + redundant/zero-delta factors)")
out.append("")


# ═══════════════════════════════════════════════════════════════════════════════
# ROUND 3: Optimize Thresholds + Weights
# ═══════════════════════════════════════════════════════════════════════════════
out.append("---\n")
out.append("## Round 3: Optimize Thresholds + Weights\n")

# 3a: Threshold optimization for continuous factors
out.append("### 3a. Threshold Optimization (Continuous Factors)\n")

# Time cutoff
out.append("**Time cutoff** (factor = time < X):\n")
out.append("| Cutoff  | N(True) | PnL(True) | PnL(False) | Delta  |")
out.append("|---------|---------|-----------|------------|--------|")
best_time = None
best_time_delta = -999
for cutoff in [10*60, 10*60+30, 11*60, 11*60+30, 12*60]:
    t = df[df['time_minutes'] < cutoff]
    f_ = df[df['time_minutes'] >= cutoff]
    if len(t) < 10 or len(f_) < 10:
        continue
    delta = t['pnl'].mean() - f_['pnl'].mean()
    h, m = divmod(cutoff, 60)
    out.append(f"| {h}:{m:02d}    | {len(t):>7d} | {t['pnl'].mean():>+9.4f} | {f_['pnl'].mean():>+9.4f}  | {delta:>+6.4f} |")
    if delta > best_time_delta:
        best_time_delta = delta
        best_time = cutoff
h, m = divmod(best_time, 60)
out.append(f"\n-> **Best time cutoff: {h}:{m:02d}** (delta={best_time_delta:+.4f})\n")

# ADX cutoff
out.append("**ADX cutoff** (factor = ADX > X):\n")
out.append("| Cutoff | N(True) | PnL(True) | PnL(False) | Delta  |")
out.append("|--------|---------|-----------|------------|--------|")
best_adx = None
best_adx_delta = -999
for cutoff in [20, 25, 30, 35, 40]:
    t = df[df['adx'] > cutoff]
    f_ = df[df['adx'] <= cutoff]
    if len(t) < 10 or len(f_) < 10:
        continue
    delta = t['pnl'].mean() - f_['pnl'].mean()
    out.append(f"| {cutoff:>6d} | {len(t):>7d} | {t['pnl'].mean():>+9.4f} | {f_['pnl'].mean():>+9.4f}  | {delta:>+6.4f} |")
    if delta > best_adx_delta:
        best_adx_delta = delta
        best_adx = cutoff
out.append(f"\n-> **Best ADX cutoff: {best_adx}** (delta={best_adx_delta:+.4f})\n")

# Volume cutoff (for "not exhaustion" — vol < X is better? or vol > X?)
out.append("**Volume cutoff** (factor = vol >= X):\n")
out.append("| Cutoff | N(True) | PnL(True) | PnL(False) | Delta  |")
out.append("|--------|---------|-----------|------------|--------|")
best_vol = None
best_vol_delta = -999
for cutoff in [2, 3, 5, 8]:
    t = df[df['vol'] >= cutoff]
    f_ = df[df['vol'] < cutoff]
    if len(t) < 10 or len(f_) < 10:
        continue
    delta = t['pnl'].mean() - f_['pnl'].mean()
    out.append(f"| {cutoff:>6d} | {len(t):>7d} | {t['pnl'].mean():>+9.4f} | {f_['pnl'].mean():>+9.4f}  | {delta:>+6.4f} |")
    if delta > best_vol_delta:
        best_vol_delta = delta
        best_vol = cutoff
out.append(f"\n-> **Best vol cutoff: {best_vol}x** (delta={best_vol_delta:+.4f})\n")

# Also test vol < X (not-exhaustion filter)
out.append("**Volume NOT-exhaustion** (factor = vol < X):\n")
out.append("| Cutoff | N(True) | PnL(True) | PnL(False) | Delta  |")
out.append("|--------|---------|-----------|------------|--------|")
best_vol_cap = None
best_vol_cap_delta = -999
for cutoff in [5, 8, 10, 15, 20]:
    t = df[df['vol'] < cutoff]
    f_ = df[df['vol'] >= cutoff]
    if len(t) < 10 or len(f_) < 10:
        continue
    delta = t['pnl'].mean() - f_['pnl'].mean()
    out.append(f"| < {cutoff:<4d} | {len(t):>7d} | {t['pnl'].mean():>+9.4f} | {f_['pnl'].mean():>+9.4f}  | {delta:>+6.4f} |")
    if delta > best_vol_cap_delta:
        best_vol_cap_delta = delta
        best_vol_cap = cutoff
if best_vol_cap:
    out.append(f"\n-> **Best vol cap: < {best_vol_cap}x** (delta={best_vol_cap_delta:+.4f})\n")
else:
    out.append("\n-> No vol cap adds edge.\n")

# Body cutoff
out.append("**Body cutoff** (factor = body > X):\n")
out.append("| Cutoff | N(True) | PnL(True) | PnL(False) | Delta  |")
out.append("|--------|---------|-----------|------------|--------|")
best_body = None
best_body_delta = -999
for cutoff in [30, 40, 50, 60, 70, 80]:
    t = df[df['body'] > cutoff]
    f_ = df[df['body'] <= cutoff]
    if len(t) < 10 or len(f_) < 10:
        continue
    delta = t['pnl'].mean() - f_['pnl'].mean()
    out.append(f"| {cutoff:>6d} | {len(t):>7d} | {t['pnl'].mean():>+9.4f} | {f_['pnl'].mean():>+9.4f}  | {delta:>+6.4f} |")
    if delta > best_body_delta:
        best_body_delta = delta
        best_body = cutoff

# Also test body < X (body warn = fakeout)
out.append("")
out.append("**Body NOT-fakeout** (factor = body < X):\n")
out.append("| Cutoff | N(True) | PnL(True) | PnL(False) | Delta  |")
out.append("|--------|---------|-----------|------------|--------|")
best_body_cap = None
best_body_cap_delta = -999
for cutoff in [50, 60, 70, 80, 90]:
    t = df[df['body'] < cutoff]
    f_ = df[df['body'] >= cutoff]
    if len(t) < 10 or len(f_) < 10:
        continue
    delta = t['pnl'].mean() - f_['pnl'].mean()
    out.append(f"| < {cutoff:<4d} | {len(t):>7d} | {t['pnl'].mean():>+9.4f} | {f_['pnl'].mean():>+9.4f}  | {delta:>+6.4f} |")
    if delta > best_body_cap_delta:
        best_body_cap_delta = delta
        best_body_cap = cutoff

out.append(f"\n-> **Best body >X cutoff: {best_body}** (delta={best_body_delta:+.4f})" if best_body else "")
out.append(f"-> **Best body <X cutoff: < {best_body_cap}** (delta={best_body_cap_delta:+.4f})" if best_body_cap else "")
out.append("")

# Summary of best thresholds
out.append("**Threshold summary:**")
h, m = divmod(best_time, 60)
out.append(f"- Time: < {h}:{m:02d} (delta={best_time_delta:+.4f})")
out.append(f"- ADX: > {best_adx} (delta={best_adx_delta:+.4f})")
out.append(f"- Vol: >= {best_vol}x (delta={best_vol_delta:+.4f})")
if best_body:
    out.append(f"- Body >: > {best_body} (delta={best_body_delta:+.4f})")
if best_body_cap:
    out.append(f"- Body <: < {best_body_cap} (delta={best_body_cap_delta:+.4f})")
out.append("")

# 3b: Weight optimization
out.append("### 3b. Weight Optimization\n")

# Rebuild factors with optimized thresholds
df['fo_time'] = df['time_minutes'] < best_time
df['fo_adx'] = df['adx'] > best_adx
df['fo_dir_bear'] = df['direction'] == 'bear'
df['fo_ema_aligned'] = df['f_ema_aligned']
df['fo_level_low'] = df['f_level_low']
df['fo_type_brk'] = df['f_type_brk']
df['fo_counter_vwap'] = df['f_counter_vwap']
# Volume with best cutoff
df['fo_vol'] = df['vol'] >= best_vol
# Body: use whichever direction was better
if best_body_delta > best_body_cap_delta and best_body_delta > 0:
    df['fo_body'] = df['body'] > best_body
    body_label = f"Body > {best_body}"
elif best_body_cap_delta > 0:
    df['fo_body'] = df['body'] < best_body_cap
    body_label = f"Body < {best_body_cap}"
else:
    df['fo_body'] = pd.Series(False, index=df.index)
    body_label = "Body (none)"

# Build optimized factor list (start from clean_factors, swap in optimized versions)
opt_factor_map = {
    'f_time_lt11': 'fo_time',
    'f_adx_gt25': 'fo_adx',
    'f_dir_bear': 'fo_dir_bear',
    'f_ema_aligned': 'fo_ema_aligned',
    'f_counter_vwap': 'fo_counter_vwap',
    'f_level_low': 'fo_level_low',
    'f_type_brk': 'fo_type_brk',
}

# All candidate optimized factors
all_opt_factors = ['fo_time', 'fo_adx', 'fo_dir_bear', 'fo_ema_aligned',
                   'fo_counter_vwap', 'fo_level_low', 'fo_type_brk', 'fo_vol', 'fo_body']

opt_factor_labels = {
    'fo_time': f'Time < {best_time//60}:{best_time%60:02d}',
    'fo_adx': f'ADX > {best_adx}',
    'fo_dir_bear': 'Dir = Bear',
    'fo_ema_aligned': 'EMA Aligned',
    'fo_counter_vwap': 'Counter-VWAP',
    'fo_level_low': 'Level = LOW',
    'fo_type_brk': 'Type = BRK',
    'fo_vol': f'Vol >= {best_vol}x',
    'fo_body': body_label,
}

# Compute deltas for optimized factors
opt_deltas = {}
for fn in all_opt_factors:
    t = df[df[fn]]
    f_ = df[~df[fn]]
    if len(t) >= 5 and len(f_) >= 5:
        opt_deltas[fn] = t['pnl'].mean() - f_['pnl'].mean()
    else:
        opt_deltas[fn] = 0.0

out.append("**Optimized factor deltas:**\n")
out.append("| Factor              | Delta  | N(True) |")
out.append("|---------------------|--------|---------|")
for fn in sorted(all_opt_factors, key=lambda x: opt_deltas[x], reverse=True):
    out.append(f"| {opt_factor_labels[fn]:<19s} | {opt_deltas[fn]:>+6.4f} | {df[fn].sum():>7d} |")
out.append("")

# Remove factors with negative/zero delta from the optimized set
opt_factors_positive = [fn for fn in all_opt_factors if opt_deltas[fn] > 0.005]
out.append(f"**Factors with positive delta (>{0.005}): {len(opt_factors_positive)}**")
for fn in opt_factors_positive:
    out.append(f"  - {opt_factor_labels[fn]} ({opt_deltas[fn]:+.4f})")
out.append("")

# Weight schemes
out.append("**Testing 4 weighting schemes:**\n")

def score_and_evaluate(df, factors, weights, scheme_name):
    """Score signals and find best threshold."""
    df_temp = df.copy()
    df_temp['score'] = sum(df_temp[fn].astype(int) * w for fn, w in zip(factors, weights))
    max_s = df_temp['score'].max()

    results = []
    for thresh in range(0, max_s + 1):
        subset = df_temp[df_temp['score'] >= thresh]
        if len(subset) >= 15:
            m = metrics(subset, f"{scheme_name} >= {thresh}")
            results.append((thresh, m))

    # Best by total PnL
    if results:
        best = max(results, key=lambda x: x[1]['total_pnl'])
        # Also find best per-signal (with N >= 30)
        viable = [r for r in results if r[1]['N'] >= 30]
        best_per = max(viable, key=lambda x: x[1]['pnl_per']) if viable else best
        return results, best, best_per
    return [], None, None

# Scheme 1: Flat (all = 1)
flat_weights = [1] * len(opt_factors_positive)
flat_results, flat_best, flat_best_per = score_and_evaluate(
    df, opt_factors_positive, flat_weights, "Flat")

# Scheme 2: Delta-proportional
if opt_factors_positive:
    min_delta = min(opt_deltas[fn] for fn in opt_factors_positive)
    if min_delta > 0:
        delta_weights = [max(1, round(opt_deltas[fn] / min_delta)) for fn in opt_factors_positive]
    else:
        delta_weights = flat_weights[:]
else:
    delta_weights = []
delta_results, delta_best, delta_best_per = score_and_evaluate(
    df, opt_factors_positive, delta_weights, "Delta-prop")

# Scheme 3: Binary-big (top 3 get +2, rest +1)
sorted_factors = sorted(opt_factors_positive, key=lambda fn: opt_deltas[fn], reverse=True)
big_weights = []
for i, fn in enumerate(opt_factors_positive):
    rank = sorted_factors.index(fn)
    big_weights.append(2 if rank < 3 else 1)
big_results, big_best, big_best_per = score_and_evaluate(
    df, opt_factors_positive, big_weights, "Binary-big")

# Scheme 4: Minimal (top 3-4 only)
top_n = min(4, len(sorted_factors))
minimal_factors = sorted_factors[:top_n]
minimal_weights = [1] * top_n
minimal_results, minimal_best, minimal_best_per = score_and_evaluate(
    df, minimal_factors, minimal_weights, "Minimal")

# Report each scheme
schemes = [
    ("Flat", opt_factors_positive, flat_weights, flat_results, flat_best, flat_best_per),
    ("Delta-proportional", opt_factors_positive, delta_weights, delta_results, delta_best, delta_best_per),
    ("Binary-big", opt_factors_positive, big_weights, big_results, big_best, big_best_per),
    ("Minimal (top factors)", minimal_factors, minimal_weights, minimal_results, minimal_best, minimal_best_per),
]

for name, factors, weights, results, best, best_per in schemes:
    out.append(f"**{name}** — Factors: {', '.join(opt_factor_labels.get(fn, fn) for fn in factors)}")
    out.append(f"  Weights: {weights}")
    out.append("")
    out.append(METRICS_HEADER)
    for thresh, m in results:
        out.append(metrics_row(m))
    out.append("")
    if best:
        out.append(f"  -> Best total PnL: threshold={best[0]}, N={best[1]['N']}, "
                   f"total={best[1]['total_pnl']:+.1f}, per-signal={best[1]['pnl_per']:+.4f}")
    if best_per and best_per != best:
        out.append(f"  -> Best per-signal (N>=30): threshold={best_per[0]}, N={best_per[1]['N']}, "
                   f"per-signal={best_per[1]['pnl_per']:+.4f}")
    out.append("")

# Pick overall best scheme
all_bests = []
for name, factors, weights, results, best, best_per in schemes:
    if best:
        all_bests.append((name, factors, weights, best[0], best[1]))

overall_best = max(all_bests, key=lambda x: x[4]['total_pnl'])
out.append(f"**Round 3 Winner: {overall_best[0]}** at threshold >= {overall_best[3]}")
out.append(f"  N={overall_best[4]['N']}, total PnL={overall_best[4]['total_pnl']:+.1f}, "
           f"per-signal={overall_best[4]['pnl_per']:+.4f}, MFE/MAE={overall_best[4]['mfe_mae']:.2f}")
out.append("")

# Store best config for Round 4
BEST_NAME = overall_best[0]
BEST_FACTORS = overall_best[1]
BEST_WEIGHTS = overall_best[2]
BEST_THRESH = overall_best[3]

# Also check: is minimal competitive?
if minimal_best:
    min_total = minimal_best[1]['total_pnl']
    best_total = overall_best[4]['total_pnl']
    out.append(f"**Minimal vs Best:** Minimal total={min_total:+.1f} vs Best total={best_total:+.1f} "
               f"({min_total/best_total:.0%} capture)")
    out.append("")


# ═══════════════════════════════════════════════════════════════════════════════
# ROUND 4: Validation — Time Split + Symbol Split
# ═══════════════════════════════════════════════════════════════════════════════
out.append("---\n")
out.append("## Round 4: Validation\n")

# Compute score with best config
df['best_score'] = sum(df[fn].astype(int) * w for fn, w in zip(BEST_FACTORS, BEST_WEIGHTS))

# 4a: Time split
out.append("### 4a. Time Split (First Half vs Second Half by Date)\n")

dates_sorted = sorted(df['date_parsed'].unique())
mid = len(dates_sorted) // 2
mid_date = dates_sorted[mid]

first_half = df[df['date_parsed'] < mid_date]
second_half = df[df['date_parsed'] >= mid_date]

out.append(f"Split date: {mid_date.strftime('%Y-%m-%d')}")
out.append(f"First half: {len(first_half)} signals ({dates_sorted[0].strftime('%Y-%m-%d')} to "
           f"{(mid_date - pd.Timedelta(days=1)).strftime('%Y-%m-%d')})")
out.append(f"Second half: {len(second_half)} signals ({mid_date.strftime('%Y-%m-%d')} to "
           f"{dates_sorted[-1].strftime('%Y-%m-%d')})\n")

out.append(METRICS_HEADER)

# Baseline both halves
m1_base = metrics(first_half, "1st half: ALL")
m2_base = metrics(second_half, "2nd half: ALL")
out.append(metrics_row(m1_base))
out.append(metrics_row(m2_base))

# Best config both halves
fh_filtered = first_half[first_half['best_score'] >= BEST_THRESH]
sh_filtered = second_half[second_half['best_score'] >= BEST_THRESH]

m1_filt = metrics(fh_filtered, f"1st half: Score >= {BEST_THRESH}")
m2_filt = metrics(sh_filtered, f"2nd half: Score >= {BEST_THRESH}")
out.append(metrics_row(m1_filt))
out.append(metrics_row(m2_filt))
out.append("")

# Assess robustness
if m1_filt['N'] > 0 and m2_filt['N'] > 0:
    pnl_diff = abs(m1_filt['pnl_per'] - m2_filt['pnl_per'])
    avg_pnl = (m1_filt['pnl_per'] + m2_filt['pnl_per']) / 2
    out.append(f"**Robustness:** PnL/signal gap = {pnl_diff:.4f} "
               f"(avg={avg_pnl:+.4f})")
    if m1_filt['pnl_per'] > 0 and m2_filt['pnl_per'] > 0:
        out.append("  -> Both halves positive: ROBUST")
    elif m1_filt['pnl_per'] > 0 or m2_filt['pnl_per'] > 0:
        out.append("  -> Only one half positive: POTENTIALLY OVERFIT")
    else:
        out.append("  -> Neither half positive: BROKEN")
out.append("")

# 4b: Symbol split
out.append("### 4b. Symbol Split\n")
out.append("| Symbol | N(all) | N(filt) | PnL/sig(all) | PnL/sig(filt) | Win%(filt) | Runner%(filt) |")
out.append("|--------|--------|---------|--------------|---------------|------------|---------------|")

for sym in sorted(df['symbol'].unique()):
    sym_all = df[df['symbol'] == sym]
    sym_filt = df[(df['symbol'] == sym) & (df['best_score'] >= BEST_THRESH)]
    pnl_all = sym_all['pnl'].mean() if len(sym_all) > 0 else 0
    if len(sym_filt) > 0:
        pnl_f = sym_filt['pnl'].mean()
        win_f = sym_filt['win'].mean()
        run_f = sym_filt['runner'].mean()
    else:
        pnl_f = 0
        win_f = 0
        run_f = 0
    out.append(f"| {sym:<6s} | {len(sym_all):>6d} | {len(sym_filt):>7d} | {pnl_all:>+12.4f} | "
               f"{pnl_f:>+13.4f} | {win_f:>9.1%} | {run_f:>12.1%} |")

# Count symbols with positive PnL after filter
sym_positive = 0
sym_total = 0
for sym in df['symbol'].unique():
    sym_filt = df[(df['symbol'] == sym) & (df['best_score'] >= BEST_THRESH)]
    if len(sym_filt) >= 3:
        sym_total += 1
        if sym_filt['pnl'].mean() > 0:
            sym_positive += 1

out.append(f"\n**{sym_positive}/{sym_total} symbols with positive PnL** (of those with N>=3)")
out.append("")

# 4c: Stability test
out.append("### 4c. Stability Test (Score Cliff Check)\n")
out.append(f"Testing thresholds around best ({BEST_THRESH}):\n")
out.append(METRICS_HEADER)

for t in range(max(0, BEST_THRESH - 2), min(df['best_score'].max() + 1, BEST_THRESH + 3)):
    subset = df[df['best_score'] >= t]
    m = metrics(subset, f"Score >= {t}")
    out.append(metrics_row(m))

out.append("")

# Check for cliff
pnl_at_thresh = {}
for t in range(max(0, BEST_THRESH - 2), min(df['best_score'].max() + 1, BEST_THRESH + 3)):
    subset = df[df['best_score'] >= t]
    if len(subset) >= 10:
        pnl_at_thresh[t] = subset['pnl'].mean()

if BEST_THRESH in pnl_at_thresh:
    below = pnl_at_thresh.get(BEST_THRESH - 1, None)
    above = pnl_at_thresh.get(BEST_THRESH + 1, None)
    best_pnl = pnl_at_thresh[BEST_THRESH]
    if below and above:
        drop_below = best_pnl - below
        drop_above = best_pnl - above
        out.append(f"**Cliff analysis:**")
        out.append(f"- Score {BEST_THRESH-1}: {below:+.4f} (drop={drop_below:+.4f})")
        out.append(f"- Score {BEST_THRESH}: {best_pnl:+.4f} (BEST)")
        out.append(f"- Score {BEST_THRESH+1}: {above:+.4f} (drop={drop_above:+.4f})")
        if abs(drop_below) > 0.05 or (above and abs(drop_above) > 0.05):
            out.append("- -> SHARP CLIFF — potentially fragile")
        else:
            out.append("- -> Smooth gradient — robust")
out.append("")


# ═══════════════════════════════════════════════════════════════════════════════
# ROUND 5: Final Comparison
# ═══════════════════════════════════════════════════════════════════════════════
out.append("---\n")
out.append("## Round 5: Final Comparison\n")

# Config 1: Baseline
baseline = metrics(df, "Baseline (all post-9:50)")

# Config 2: Counter-VWAP only
counter = metrics(df[df['counter_vwap']], "Counter-VWAP only")

# Config 3: Original 11-factor score >= 6
# Reconstruct original Round 1 scoring (11 factors, flat)
# Original had: time<11, adx>25, bear, vwap_below, ema_aligned, counter_vwap,
#               level_low, type_brk, multi_level, vol>2, conf (cheating!)
df['r1_score'] = (
    df['f_time_lt11'].astype(int) +
    df['f_adx_gt25'].astype(int) +
    df['f_dir_bear'].astype(int) +
    df['f_vwap_below'].astype(int) +
    df['f_ema_aligned'].astype(int) +
    df['f_counter_vwap'].astype(int) +
    df['f_level_low'].astype(int) +
    df['f_type_brk'].astype(int) +
    df['multi_level'].astype(int) +
    (df['vol'] >= 2).astype(int) +
    df['conf'].isin(['✓', '✓★']).astype(int)  # CHEATING factor
)
r1_c = metrics(df[df['r1_score'] >= 6], "Round 1: 11-factor >= 6 (w/ CONF)")

# Config 4: Best from Round 3
best_r3 = metrics(df[df['best_score'] >= BEST_THRESH],
                  f"Best R3: {BEST_NAME} >= {BEST_THRESH}")

# Config 5: Minimal viable
# Find fewest factors that get 80% of best edge
best_edge = overall_best[4]['total_pnl']
minimal_found = None
for n_top in range(1, len(sorted_factors) + 1):
    top_facs = sorted_factors[:n_top]
    temp_score = sum(df[fn].astype(int) for fn in top_facs)
    for t in range(1, n_top + 1):
        subset = df[temp_score >= t]
        if len(subset) >= 20 and subset['pnl'].sum() >= 0.8 * best_edge:
            minimal_found = (n_top, t, top_facs, subset)
            break
    if minimal_found:
        break

if minimal_found:
    n_facs, thresh, facs, subset = minimal_found
    min_viable = metrics(subset,
                         f"Minimal: {n_facs} factors >= {thresh}")
    min_viable_factors = facs
    min_viable_thresh = thresh
else:
    # Fallback: use top 2
    top2 = sorted_factors[:2]
    temp_score = sum(df[fn].astype(int) for fn in top2)
    subset = df[temp_score >= 1]
    min_viable = metrics(subset, "Minimal: top 2 >= 1")
    min_viable_factors = top2
    min_viable_thresh = 1

out.append(METRICS_HEADER)
for m in [baseline, counter, r1_c, best_r3, min_viable]:
    out.append(metrics_row(m))
out.append("")

# What's the simplest change?
out.append("### What's the Simplest Change That Captures the Most Edge?\n")

# Test each single factor as a filter
out.append("**Single-factor filters (best to worst by total PnL improvement vs baseline):**\n")
out.append("| Factor              | N    | PnL/sig | Total PnL | vs Baseline |")
out.append("|---------------------|------|---------|-----------|-------------|")

baseline_total = df['pnl'].sum()
single_results = []
for fn in all_opt_factors:
    subset = df[df[fn]]
    if len(subset) >= 20:
        total = subset['pnl'].sum()
        improve = total - baseline_total
        single_results.append((fn, len(subset), subset['pnl'].mean(), total, improve))

single_results.sort(key=lambda x: x[2], reverse=True)  # by per-signal PnL
for fn, n, per, total, improve in single_results:
    out.append(f"| {opt_factor_labels[fn]:<19s} | {n:>4d} | {per:>+7.3f} | {total:>+9.1f} | {improve:>+11.1f} |")

out.append("")

# Test pairs
out.append("**Best 2-factor combinations (by per-signal PnL, N>=30):**\n")
out.append("| Factor A            | Factor B            | N    | PnL/sig | Total PnL |")
out.append("|---------------------|---------------------|------|---------|-----------|")

pair_results = []
for fi, fj in combinations(all_opt_factors, 2):
    subset = df[df[fi] & df[fj]]
    if len(subset) >= 30:
        pair_results.append((fi, fj, len(subset), subset['pnl'].mean(), subset['pnl'].sum()))

pair_results.sort(key=lambda x: x[3], reverse=True)
for fi, fj, n, per, total in pair_results[:10]:
    out.append(f"| {opt_factor_labels[fi]:<19s} | {opt_factor_labels[fj]:<19s} | {n:>4d} | {per:>+7.3f} | {total:>+9.1f} |")

out.append("")

# Final answer
out.append("### Summary & Recommendation\n")

# Determine the simplest good option
if pair_results:
    best_pair = pair_results[0]
    pair_pnl = best_pair[3]
    pair_total = best_pair[4]
    best_r3_per = overall_best[4]['pnl_per']

    out.append(f"**Simplest high-edge option:** {opt_factor_labels[best_pair[0]]} + "
               f"{opt_factor_labels[best_pair[1]]}")
    out.append(f"  N={best_pair[2]}, PnL/sig={pair_pnl:+.4f}, Total={pair_total:+.1f}")
    out.append(f"  Captures {pair_total/overall_best[4]['total_pnl']:.0%} of best config's total PnL")
    out.append("")

out.append(f"**Full optimized scoring:** {BEST_NAME} with {len(BEST_FACTORS)} factors, threshold >= {BEST_THRESH}")
out.append(f"  Factors: {', '.join(opt_factor_labels.get(fn, fn) for fn in BEST_FACTORS)}")
out.append(f"  Weights: {BEST_WEIGHTS}")
out.append(f"  N={overall_best[4]['N']}, PnL/sig={overall_best[4]['pnl_per']:+.4f}, "
           f"Total={overall_best[4]['total_pnl']:+.1f}")
out.append("")

if minimal_found:
    out.append(f"**Minimal viable ({minimal_found[0]} factors >= {minimal_found[1]}):** "
               f"{', '.join(opt_factor_labels.get(fn, fn) for fn in minimal_found[2])}")
    out.append(f"  Captures {min_viable['total_pnl']/overall_best[4]['total_pnl']:.0%} of best config")
    out.append("")

out.append("**Key takeaways:**")
out.append("1. CONF was cheating — removing it forces honest scoring")
out.append(f"2. The best {len(BEST_FACTORS)}-factor model captures the edge without look-ahead bias")

# Robustness assessment
if m1_filt['pnl_per'] > 0 and m2_filt['pnl_per'] > 0:
    out.append("3. Time-split validation: BOTH halves positive — scoring is robust")
else:
    out.append("3. Time-split validation: CAUTION — scoring may be overfit")

out.append(f"4. Symbol coverage: {sym_positive}/{sym_total} symbols profitable with scoring")

# Is 2 factors enough?
if pair_results and pair_results[0][4] >= 0.6 * overall_best[4]['total_pnl']:
    out.append(f"5. **2 factors may be enough:** best pair captures "
               f"{pair_results[0][4]/overall_best[4]['total_pnl']:.0%} of full model")
else:
    out.append(f"5. Full model needed — best 2-factor pair captures only "
               f"{pair_results[0][4]/overall_best[4]['total_pnl']:.0%}")

out.append("")

# ── Write output ──────────────────────────────────────────────────────────────
output_path = SCRIPT_DIR / 'v29-mc-optimize.md'
output_path.write_text('\n'.join(out))
print(f"\nResults written to: {output_path}")
print(f"Total lines: {len(out)}")

# Print quick summary
print("\n=== QUICK SUMMARY ===")
print(f"Best config: {BEST_NAME}, {len(BEST_FACTORS)} factors, threshold >= {BEST_THRESH}")
print(f"  N={overall_best[4]['N']}, PnL/sig={overall_best[4]['pnl_per']:+.4f}, "
      f"Total={overall_best[4]['total_pnl']:+.1f}")
print(f"Time-split: 1st half PnL/sig={m1_filt['pnl_per']:+.4f}, "
      f"2nd half={m2_filt['pnl_per']:+.4f}")
if pair_results:
    print(f"Simplest edge: {opt_factor_labels[pair_results[0][0]]} + "
          f"{opt_factor_labels[pair_results[0][1]]} "
          f"(N={pair_results[0][2]}, PnL/sig={pair_results[0][3]:+.4f})")
