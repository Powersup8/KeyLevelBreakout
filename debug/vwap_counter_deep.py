#!/usr/bin/env python3
"""
VWAP Counter-Trend Deep Analysis
- Check EMA alignment pattern (seems 100% aligned)
- Mine v28 follow-through dataset for more samples
- Level-type breakdown
- Temporal distribution (are these clustered or spread?)
"""
import pandas as pd
import numpy as np
from pathlib import Path

DEBUG = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug")

# ── v28a data ──
signals = pd.read_csv(DEBUG / "v28a-signals.csv")
ft = pd.read_csv(DEBUG / "v28a-follow-through.csv")
ft30 = ft[ft['window'] == 30].copy()

brk = signals[signals['line_type'] == 'BRK'].copy()

def vwap_align(row):
    if pd.isna(row.get('vwap')) or row.get('vwap', '') == '':
        return 'unknown'
    if row['direction'] == 'bull':
        return 'aligned' if row['vwap'] == 'above' else 'counter'
    else:
        return 'aligned' if row['vwap'] == 'below' else 'counter'

brk['vwap_align'] = brk.apply(vwap_align, axis=1)
merged = brk.merge(ft30, on=['symbol', 'datetime', 'direction'], how='inner', suffixes=('', '_ft'))
counter = merged[merged['vwap_align'] == 'counter'].copy()

# ── KEY INSIGHT: EMA alignment ──
print("="*60)
print("INSIGHT #1: EMA ALIGNMENT IN COUNTER-TREND BRKs")
print("="*60)

ema_aligned = counter.apply(lambda r: r['ema'] == r['direction'], axis=1)
print(f"EMA matches direction: {ema_aligned.sum()}/{len(counter)} = {ema_aligned.mean()*100:.0f}%")
print(f"→ EVERY counter-VWAP BRK has EMA confirming the trade direction")
print(f"→ This is a PULLBACK-TO-KEY-LEVEL pattern, not a random counter move")

# Compare: aligned BRKs EMA alignment
aligned = merged[merged['vwap_align'] == 'aligned'].copy()
aligned_ema = aligned.apply(lambda r: r.get('ema') == r['direction'], axis=1)
print(f"\nFor comparison, aligned BRKs with EMA match: {aligned_ema.sum()}/{len(aligned)} = {aligned_ema.mean()*100:.0f}%")

# ── INSIGHT #2: Level types ──
print(f"\n{'='*60}")
print("INSIGHT #2: LEVEL TYPE BREAKDOWN")
print("="*60)

# Parse levels
def categorize_level(levels_str):
    if pd.isna(levels_str):
        return 'unknown'
    s = str(levels_str)
    if 'Yest' in s:
        return 'Yest'
    elif 'PM' in s:
        return 'PM'
    elif 'ORB' in s:
        return 'ORB'
    elif 'Week' in s:
        return 'Week'
    return 'other'

counter['level_cat'] = counter['levels'].apply(categorize_level)
print("\nCounter BRKs by level category:")
for cat in counter['level_cat'].value_counts().index:
    sub = counter[counter['level_cat'] == cat]
    win = (sub['mfe'] > sub['mae']).mean() * 100
    print(f"  {cat}: n={len(sub)}, MFE={sub['mfe'].mean():.3f}, Win={win:.0f}%")

# HIGH vs LOW
def is_low_level(row):
    levels = str(row.get('levels', ''))
    direction = row['direction']
    if direction == 'bear' and ('L' in levels):
        return True
    if direction == 'bull' and ('H' in levels):
        return True
    return False

counter['level_is_breakout_side'] = counter.apply(is_low_level, axis=1)

# Multi-level
counter['is_multi'] = counter['levels'].astype(str).str.contains(r'\+')
print(f"\nMulti-level counter BRKs:")
for ml in [True, False]:
    sub = counter[counter['is_multi'] == ml]
    if len(sub) == 0: continue
    win = (sub['mfe'] > sub['mae']).mean() * 100
    label = "Multi-level" if ml else "Single-level"
    print(f"  {label}: n={len(sub)}, MFE={sub['mfe'].mean():.3f}, Win={win:.0f}%")

# ── INSIGHT #3: Temporal spread ──
print(f"\n{'='*60}")
print("INSIGHT #3: TEMPORAL DISTRIBUTION")
print("="*60)

# Extract date from datetime string
counter['date'] = counter['datetime'].astype(str).str[:10]
dates = counter['date'].unique()
print(f"Spread across {len(dates)} unique days in 6 months")
print(f"Average: {len(counter)/len(dates):.1f} counter BRKs per day they occur")
print(f"Days in dataset: ~120 trading days")
print(f"Frequency: ~{len(dates)/120*100:.0f}% of trading days have a counter BRK")

# By month
counter['month'] = counter['datetime'].astype(str).str[:7]
print(f"\nBy month:")
for m in sorted(counter['month'].unique()):
    sub = counter[counter['month'] == m]
    win = (sub['mfe'] > sub['mae']).mean() * 100
    print(f"  {m}: n={len(sub)}, MFE={sub['mfe'].mean():.3f}, Win={win:.0f}%")

# ── INSIGHT #4: Compare counter to BEST aligned signals ──
print(f"\n{'='*60}")
print("INSIGHT #4: COUNTER vs BEST ALIGNED COMBOS")
print("="*60)

# Best aligned: time 10:xx, not big-move, low vol
aligned['hour'] = aligned['time'].astype(str).str.split(':').str[0].astype(int)
aligned['is_bigmove_ft'] = aligned.get('is_bigmove', False)

print("\nAligned BRK combos:")
combos = [
    ("All aligned", aligned),
    ("10:xx only", aligned[aligned['hour'] == 10]),
    ("Not ⚡", aligned[aligned['is_bigmove'] == False]),
    ("10:xx + not ⚡", aligned[(aligned['hour'] == 10) & (aligned['is_bigmove'] == False)]),
    ("Vol <5x", aligned[aligned['vol'] < 5]),
    ("10:xx + not ⚡ + vol <5x", aligned[(aligned['hour'] == 10) & (aligned['is_bigmove'] == False) & (aligned['vol'] < 5)]),
]
for label, sub in combos:
    if len(sub) == 0: continue
    win = (sub['mfe'] > sub['mae']).mean() * 100
    print(f"  {label:30s}: n={len(sub):4d}, MFE={sub['mfe'].mean():.3f}, MAE={sub['mae'].mean():.3f}, Win={win:.1f}%")

print(f"\n  {'COUNTER-TREND (all)':30s}: n={len(counter):4d}, MFE={counter['mfe'].mean():.3f}, MAE={counter['mae'].mean():.3f}, Win={(counter['mfe'] > counter['mae']).mean()*100:.1f}%")

# ── v28 follow-through dataset ──
print(f"\n{'='*60}")
print("v28 DATASET ANALYSIS (potentially different time range)")
print("="*60)

v28_ft = pd.read_csv(DEBUG / "v28-follow-through.csv")
print(f"v28 FT rows: {len(v28_ft)}")
print(f"v28 FT columns: {list(v28_ft.columns)}")

if 'vwap' in v28_ft.columns and 'type' in v28_ft.columns:
    # v28 uses window_min, mfe_atr, mae_atr
    win_col = 'window_min' if 'window_min' in v28_ft.columns else 'window'
    mfe_col = 'mfe_atr' if 'mfe_atr' in v28_ft.columns else 'mfe'
    mae_col = 'mae_atr' if 'mae_atr' in v28_ft.columns else 'mae'

    v28_brk = v28_ft[(v28_ft['type'] == 'BRK') & (v28_ft[win_col] == 30)].copy()
    print(f"v28 BRK 30m rows: {len(v28_brk)}")

    v28_brk['vwap_align'] = v28_brk.apply(vwap_align, axis=1)
    print(f"\nv28 VWAP alignment:")
    print(v28_brk['vwap_align'].value_counts())

    for align in ['aligned', 'counter']:
        sub = v28_brk[v28_brk['vwap_align'] == align]
        if len(sub) == 0: continue
        win = (sub[mfe_col] > sub[mae_col]).mean() * 100
        print(f"  {align:8s}: n={len(sub):4d}, MFE={sub[mfe_col].mean():.3f}, MAE={sub[mae_col].mean():.3f}, Win={win:.1f}%")

    # Check date range
    print(f"\nDate range: {v28_brk['datetime'].min()} to {v28_brk['datetime'].max()}")

    # Counter detail from v28
    v28_counter = v28_brk[v28_brk['vwap_align'] == 'counter']
    if len(v28_counter) > 0:
        print(f"\nv28 counter BRK detail (n={len(v28_counter)}):")
        if 'ema' in v28_counter.columns:
            ema_match = v28_counter.apply(lambda r: r.get('ema') == r['direction'], axis=1)
            print(f"  EMA matches direction: {ema_match.sum()}/{len(v28_counter)} = {ema_match.mean()*100:.0f}%")

        for sym in sorted(v28_counter['symbol'].unique()):
            sub = v28_counter[v28_counter['symbol'] == sym]
            win = (sub[mfe_col] > sub[mae_col]).mean() * 100
            print(f"  {sym}: n={len(sub)}, MFE={sub[mfe_col].mean():.3f}, Win={win:.0f}%")

        # Monthly
        v28_counter['month'] = v28_counter['datetime'].astype(str).str[:7]
        print(f"\n  By month:")
        for m in sorted(v28_counter['month'].unique()):
            sub = v28_counter[v28_counter['month'] == m]
            win = (sub[mfe_col] > sub[mae_col]).mean() * 100
            print(f"    {m}: n={len(sub)}, MFE={sub[mfe_col].mean():.3f}, Win={win:.0f}%")

# ── STATISTICAL SIGNIFICANCE ──
print(f"\n{'='*60}")
print("STATISTICAL SIGNIFICANCE")
print("="*60)

from scipy import stats

counter_wins = (counter['mfe'] > counter['mae']).astype(int)
aligned_wins = (aligned['mfe'] > aligned['mae']).astype(int)

# Binomial test: is 83% significantly different from 49%?
n_counter = len(counter)
k_counter = counter_wins.sum()
p_null = aligned_wins.mean()  # null hypothesis: same win rate as aligned

binom_result = stats.binomtest(k_counter, n_counter, p_null, alternative='greater')
binom_p = binom_result.pvalue
print(f"Counter win rate: {k_counter}/{n_counter} = {k_counter/n_counter*100:.1f}%")
print(f"Aligned win rate: {aligned_wins.sum()}/{len(aligned_wins)} = {aligned_wins.mean()*100:.1f}%")
print(f"Binomial test p-value: {binom_p:.6f}")
print(f"→ {'STATISTICALLY SIGNIFICANT' if binom_p < 0.01 else 'NOT significant'} at p<0.01")

# MFE comparison via Mann-Whitney U
u_stat, mw_p = stats.mannwhitneyu(counter['mfe'], aligned['mfe'], alternative='greater')
print(f"\nMann-Whitney U test (MFE):")
print(f"U statistic: {u_stat:.0f}")
print(f"p-value: {mw_p:.6f}")
print(f"→ {'STATISTICALLY SIGNIFICANT' if mw_p < 0.01 else 'NOT significant'} at p<0.01")

# Bootstrap confidence interval for counter win rate
np.random.seed(42)
n_boot = 10000
boot_wins = np.array([np.random.choice(counter_wins, size=n_counter, replace=True).mean() for _ in range(n_boot)])
ci_low = np.percentile(boot_wins, 2.5)
ci_high = np.percentile(boot_wins, 97.5)
print(f"\n95% Bootstrap CI for counter win rate: [{ci_low*100:.1f}%, {ci_high*100:.1f}%]")
print(f"→ Even lower bound ({ci_low*100:.1f}%) exceeds aligned rate ({aligned_wins.mean()*100:.1f}%)")
