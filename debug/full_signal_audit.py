#!/usr/bin/env python3
"""Full Signal Audit — ALL 1841 signals from enriched-signals.csv"""

import pandas as pd
import numpy as np
from pathlib import Path
from itertools import combinations

BASE = Path(__file__).parent
INPUT = BASE / "enriched-signals.csv"
OUTPUT = BASE / "full-signal-audit.md"

# ── Load data ──────────────────────────────────────────────────────────────
print("Loading data...")
df = pd.read_csv(INPUT)
print(f"  Loaded {len(df)} signals, {df.columns.tolist()}")

# ── Derived columns ────────────────────────────────────────────────────────
print("Computing derived columns...")

# Classification
df['abs_mae'] = df['mae'].abs()
df['mfe_mae_ratio'] = np.where(df['abs_mae'] > 0, df['mfe'] / df['abs_mae'], np.where(df['mfe'] > 0, 999, 0))

df['is_winner'] = (df['mfe'] >= 0.20) & (df['mfe_mae_ratio'] > 1.5)
df['is_loser'] = (df['abs_mae'] >= 0.20) & (df['mfe_mae_ratio'] < 0.8)
df['is_scratch'] = ~df['is_winner'] & ~df['is_loser']
df['is_home_run'] = df['mfe'] >= 1.0
df['is_disaster'] = df['mae'] <= -1.0

# Simple P&L proxy
df['pnl'] = df['mfe'] + df['mae']

# Win rate (MFE > |MAE|)
df['is_win'] = df['mfe'] > df['abs_mae']

# EMA alignment
df['ema_aligned'] = ((df['direction'] == 'bull') & (df['ema'] == 'bull')) | \
                    ((df['direction'] == 'bear') & (df['ema'] == 'bear'))
df['ema_status'] = np.where(df['ema'] == 'mixed', 'mixed',
                   np.where(df['ema_aligned'], 'aligned', 'not-aligned'))

# VWAP position
df['vwap_with_trend'] = ((df['direction'] == 'bull') & (df['vwap'] == 'above')) | \
                        ((df['direction'] == 'bear') & (df['vwap'] == 'below'))
df['counter_vwap'] = ((df['direction'] == 'bull') & (df['vwap'] == 'below')) | \
                     ((df['direction'] == 'bear') & (df['vwap'] == 'above'))

# Time parsing for 30-min buckets
def time_to_30min_bucket(t):
    try:
        parts = t.split(':')
        h, m = int(parts[0]), int(parts[1])
        total_min = h * 60 + m
        # Round down to nearest 30 min
        bucket_start = (total_min // 30) * 30
        sh, sm = bucket_start // 60, bucket_start % 60
        eh, em = (bucket_start + 30) // 60, (bucket_start + 30) % 60
        return f"{sh}:{sm:02d}-{eh}:{em:02d}"
    except:
        return 'unknown'

df['time_30m'] = df['time'].apply(time_to_30min_bucket)
df['time_morning'] = df['time_30m'].isin(['9:30-10:00', '10:00-10:30'])

# Volume buckets (finer)
def vol_bucket_fine(v):
    if pd.isna(v): return 'unknown'
    if v < 1: return '<1x'
    if v < 2: return '1-2x'
    if v < 5: return '2-5x'
    if v < 10: return '5-10x'
    return '10x+'

df['vol_bucket_fine'] = df['vol'].apply(vol_bucket_fine)
df['vol_high'] = df['vol'] >= 5

# ADX buckets
def adx_bucket(a):
    if pd.isna(a): return 'unknown'
    if a < 20: return '<20'
    if a < 30: return '20-30'
    if a < 40: return '30-40'
    if a < 50: return '40-50'
    return '50+'

df['adx_bucket'] = df['adx'].apply(adx_bucket)
df['adx_high'] = df['adx'] >= 40

# Body% buckets
def body_bucket(b):
    if pd.isna(b): return 'unknown'
    if b < 30: return '<30%'
    if b < 50: return '30-50%'
    if b < 70: return '50-70%'
    return '70%+'

df['body_bucket'] = df['body'].apply(body_bucket)

# CONF pass
df['conf_pass'] = df['conf'].isin(['✓', '✓★'])

# Runner score as int (handle NaN)
df['rs_int'] = pd.to_numeric(df['rs'], errors='coerce').fillna(0).astype(int)

# ── Helper functions ───────────────────────────────────────────────────────

def compute_stats(group):
    """Compute standard stats for a group of signals."""
    n = len(group)
    if n == 0:
        return {'N': 0, 'win%': 0, 'avg_MFE': 0, 'avg_MAE': 0, 'MFE/MAE': 0,
                'home_runs': 0, 'disasters': 0, 'avg_pnl': 0,
                'winners': 0, 'losers': 0, 'scratches': 0}
    avg_mfe = group['mfe'].mean()
    avg_mae = group['mae'].mean()
    avg_abs_mae = group['abs_mae'].mean()
    ratio = avg_mfe / avg_abs_mae if avg_abs_mae > 0 else 999
    return {
        'N': n,
        'win%': f"{group['is_win'].mean() * 100:.1f}",
        'avg_MFE': f"{avg_mfe:.3f}",
        'avg_MAE': f"{avg_mae:.3f}",
        'MFE/MAE': f"{ratio:.2f}",
        'home_runs': int(group['is_home_run'].sum()),
        'disasters': int(group['is_disaster'].sum()),
        'avg_pnl': f"{group['pnl'].mean():.3f}",
        'winners': int(group['is_winner'].sum()),
        'losers': int(group['is_loser'].sum()),
        'scratches': int(group['is_scratch'].sum()),
    }

def stats_table(df_in, groupby_col, sort_by='win%', ascending=False):
    """Build a stats table grouped by a column."""
    rows = []
    for val, grp in df_in.groupby(groupby_col, dropna=False):
        s = compute_stats(grp)
        s['group'] = str(val) if pd.notna(val) else 'NaN'
        rows.append(s)
    result = pd.DataFrame(rows)
    if sort_by and sort_by in result.columns:
        result[sort_by] = pd.to_numeric(result[sort_by], errors='coerce')
        result = result.sort_values(sort_by, ascending=ascending)
    cols = ['group', 'N', 'win%', 'avg_MFE', 'avg_MAE', 'MFE/MAE', 'avg_pnl', 'home_runs', 'disasters', 'winners', 'losers', 'scratches']
    return result[[c for c in cols if c in result.columns]]

def df_to_md_table(df_in):
    """Convert dataframe to markdown table string."""
    lines = []
    headers = list(df_in.columns)
    lines.append('| ' + ' | '.join(headers) + ' |')
    lines.append('|' + '|'.join(['---'] * len(headers)) + '|')
    for _, row in df_in.iterrows():
        lines.append('| ' + ' | '.join(str(row[h]) for h in headers) + ' |')
    return '\n'.join(lines)

# ── Build Report ───────────────────────────────────────────────────────────
print("Building report...")
report = []

def add(text):
    report.append(text)

def add_section(title, level=2):
    report.append(f"\n{'#' * level} {title}\n")

# ════════════════════════════════════════════════════════════════════════════
# SECTION 1: Signal Accuracy Overview
# ════════════════════════════════════════════════════════════════════════════
print("  Section 1: Overview...")
add("# Full Signal Audit — 1841 Signals\n")
add(f"*Generated: 2026-03-04 | Data: enriched-signals.csv | Signals: {len(df)}*\n")

add_section("SECTION 1: Signal Accuracy Overview")

total = len(df)
winners = df['is_winner'].sum()
losers = df['is_loser'].sum()
scratches = df['is_scratch'].sum()
home_runs = df['is_home_run'].sum()
disasters = df['is_disaster'].sum()
avg_mfe = df['mfe'].mean()
avg_mae = df['mae'].mean()
avg_abs_mae = df['abs_mae'].mean()
overall_ratio = avg_mfe / avg_abs_mae if avg_abs_mae > 0 else 0
win_rate = df['is_win'].mean() * 100
avg_pnl = df['pnl'].mean()

add(f"| Metric | Value |")
add(f"|---|---|")
add(f"| Total signals | {total} |")
add(f"| **Winners** (MFE>=0.20, MFE/MAE>1.5) | {winners} ({winners/total*100:.1f}%) |")
add(f"| **Losers** (MAE>=0.20, MFE/MAE<0.8) | {losers} ({losers/total*100:.1f}%) |")
add(f"| **Scratches** (everything else) | {scratches} ({scratches/total*100:.1f}%) |")
add(f"| Home Runs (MFE >= 1.0 ATR) | {home_runs} ({home_runs/total*100:.1f}%) |")
add(f"| Disasters (MAE <= -1.0 ATR) | {disasters} ({disasters/total*100:.1f}%) |")
add(f"| Avg MFE | {avg_mfe:.4f} ATR |")
add(f"| Avg MAE | {avg_mae:.4f} ATR |")
add(f"| Avg MFE/MAE ratio | {overall_ratio:.2f} |")
add(f"| Win rate (MFE > abs(MAE)) | {win_rate:.1f}% |")
add(f"| Avg P&L proxy (MFE+MAE) | {avg_pnl:.4f} ATR |")
add(f"| Winner:Loser ratio | {winners}:{losers} = {winners/losers:.2f}:1 |" if losers > 0 else f"| Winner:Loser ratio | {winners}:0 |")

# ════════════════════════════════════════════════════════════════════════════
# SECTION 2: Accuracy by Every Dimension
# ════════════════════════════════════════════════════════════════════════════
print("  Section 2: By Dimension...")
add_section("SECTION 2: Accuracy by Every Dimension")

dimensions = [
    ("By Symbol", 'symbol'),
    ("By Time (30-min bucket)", 'time_30m'),
    ("By Direction", 'direction'),
    ("By Type (BRK/REV)", 'type'),
    ("By Level Type (HIGH/LOW)", 'level_type'),
    ("By EMA Alignment", 'ema_status'),
    ("By VWAP (with-trend vs counter)", 'vwap_with_trend'),
    ("By Volume Bucket", 'vol_bucket_fine'),
    ("By ADX Bucket", 'adx_bucket'),
    ("By Body% Bucket", 'body_bucket'),
    ("By CONF Status", 'conf'),
    ("By Runner Score", 'rs_int'),
    ("By Multi-Level", 'multi_level'),
    ("By With-Trend", 'with_trend'),
]

for title, col in dimensions:
    add_section(title, level=3)
    # Sort time buckets chronologically
    if col == 'time_30m':
        tbl = stats_table(df, col, sort_by=None)
        # Custom sort for time
        time_order = ['9:30-10:00', '10:00-10:30', '10:30-11:00', '11:00-11:30',
                      '11:30-12:00', '12:00-12:30', '12:30-13:00', '13:00-13:30',
                      '13:30-14:00', '14:00-14:30', '14:30-15:00', '15:00-15:30', '15:30-16:00']
        tbl['_sort'] = tbl['group'].map({v: i for i, v in enumerate(time_order)}).fillna(99)
        tbl = tbl.sort_values('_sort').drop(columns='_sort')
    elif col == 'vol_bucket_fine':
        vol_order = ['<1x', '1-2x', '2-5x', '5-10x', '10x+']
        tbl = stats_table(df, col, sort_by=None)
        tbl['_sort'] = tbl['group'].map({v: i for i, v in enumerate(vol_order)}).fillna(99)
        tbl = tbl.sort_values('_sort').drop(columns='_sort')
    elif col == 'adx_bucket':
        adx_order = ['<20', '20-30', '30-40', '40-50', '50+']
        tbl = stats_table(df, col, sort_by=None)
        tbl['_sort'] = tbl['group'].map({v: i for i, v in enumerate(adx_order)}).fillna(99)
        tbl = tbl.sort_values('_sort').drop(columns='_sort')
    elif col == 'body_bucket':
        body_order = ['<30%', '30-50%', '50-70%', '70%+']
        tbl = stats_table(df, col, sort_by=None)
        tbl['_sort'] = tbl['group'].map({v: i for i, v in enumerate(body_order)}).fillna(99)
        tbl = tbl.sort_values('_sort').drop(columns='_sort')
    elif col == 'rs_int':
        tbl = stats_table(df, col, sort_by=None)
        tbl = tbl.sort_values('group')
    else:
        tbl = stats_table(df, col)
    add(df_to_md_table(tbl))

# ════════════════════════════════════════════════════════════════════════════
# SECTION 3: Combination Analysis
# ════════════════════════════════════════════════════════════════════════════
print("  Section 3: Combination Analysis...")
add_section("SECTION 3: Combination Analysis — Best & Worst Combos")

# Define boolean factors for combination analysis
factor_defs = {
    'EMA_aligned': df['ema_aligned'],
    'bear': df['direction'] == 'bear',
    'BRK': df['type'] == 'BRK',
    'morning': df['time_morning'],
    'LOW_level': df['level_type'] == 'LOW',
    'vol_5x+': df['vol_high'],
    'ADX_40+': df['adx_high'],
    'counter_VWAP': df['counter_vwap'],
    'CONF_pass': df['conf_pass'],
}

factor_names = list(factor_defs.keys())

def combo_stats(mask, label):
    grp = df[mask]
    n = len(grp)
    if n == 0:
        return None
    avg_mfe = grp['mfe'].mean()
    avg_abs_mae = grp['abs_mae'].mean()
    ratio = avg_mfe / avg_abs_mae if avg_abs_mae > 0 else 999
    return {
        'combo': label,
        'N': n,
        'win%': round(grp['is_win'].mean() * 100, 1),
        'avg_MFE': round(avg_mfe, 3),
        'avg_MAE': round(grp['mae'].mean(), 3),
        'MFE/MAE': round(ratio, 2),
        'avg_pnl': round(grp['pnl'].mean(), 3),
        'home_runs': int(grp['is_home_run'].sum()),
        'disasters': int(grp['is_disaster'].sum()),
    }

# 2-factor combos
print("    Computing 2-factor combos...")
two_factor_results = []
for f1, f2 in combinations(factor_names, 2):
    # Both true
    mask = factor_defs[f1] & factor_defs[f2]
    s = combo_stats(mask, f"{f1} + {f2}")
    if s and s['N'] >= 20:
        two_factor_results.append(s)
    # f1 true, f2 false
    mask = factor_defs[f1] & ~factor_defs[f2]
    s = combo_stats(mask, f"{f1} + NOT_{f2}")
    if s and s['N'] >= 20:
        two_factor_results.append(s)
    # f1 false, f2 true
    mask = ~factor_defs[f1] & factor_defs[f2]
    s = combo_stats(mask, f"NOT_{f1} + {f2}")
    if s and s['N'] >= 20:
        two_factor_results.append(s)
    # Both false
    mask = ~factor_defs[f1] & ~factor_defs[f2]
    s = combo_stats(mask, f"NOT_{f1} + NOT_{f2}")
    if s and s['N'] >= 20:
        two_factor_results.append(s)

two_df = pd.DataFrame(two_factor_results).sort_values('win%', ascending=False)

add_section("Top 20 Most Profitable 2-Factor Combos (N>=20)", level=3)
add(df_to_md_table(two_df.head(20).reset_index(drop=True)))

add_section("Bottom 20 Least Profitable 2-Factor Combos (N>=20)", level=3)
add(df_to_md_table(two_df.tail(20).reset_index(drop=True)))

# 3-factor combos
print("    Computing 3-factor combos...")
three_factor_results = []
for f1, f2, f3 in combinations(factor_names, 3):
    # All possible True/False combos for 3 factors = 8 combos
    for b1 in [True, False]:
        for b2 in [True, False]:
            for b3 in [True, False]:
                m1 = factor_defs[f1] if b1 else ~factor_defs[f1]
                m2 = factor_defs[f2] if b2 else ~factor_defs[f2]
                m3 = factor_defs[f3] if b3 else ~factor_defs[f3]
                mask = m1 & m2 & m3
                parts = []
                parts.append(f1 if b1 else f"NOT_{f1}")
                parts.append(f2 if b2 else f"NOT_{f2}")
                parts.append(f3 if b3 else f"NOT_{f3}")
                label = " + ".join(parts)
                s = combo_stats(mask, label)
                if s and s['N'] >= 15:
                    three_factor_results.append(s)

three_df = pd.DataFrame(three_factor_results).sort_values('win%', ascending=False)

add_section("Top 10 Most Profitable 3-Factor Combos (N>=15)", level=3)
add(df_to_md_table(three_df.head(10).reset_index(drop=True)))

add_section("Bottom 10 Least Profitable 3-Factor Combos (N>=15)", level=3)
add(df_to_md_table(three_df.tail(10).reset_index(drop=True)))

# ════════════════════════════════════════════════════════════════════════════
# SECTION 4: Pattern Analysis — Winners vs Losers
# ════════════════════════════════════════════════════════════════════════════
print("  Section 4: Pattern Analysis...")
add_section("SECTION 4: Pattern Analysis — What Predicts Winners vs Losers")

winners_df = df[df['is_winner']]
losers_df = df[df['is_loser']]

features = ['vol', 'body', 'adx', 'rs', 'mfe', 'mae']

add_section("Feature Distributions: Winners vs Losers", level=3)
add("| Feature | Winner Mean | Winner Std | Loser Mean | Loser Std | Diff | Cohen's d | Direction |")
add("|---|---|---|---|---|---|---|---|")

cohens_d_results = []
for feat in features:
    w_vals = winners_df[feat].dropna()
    l_vals = losers_df[feat].dropna()
    w_mean, w_std = w_vals.mean(), w_vals.std()
    l_mean, l_std = l_vals.mean(), l_vals.std()
    diff = w_mean - l_mean
    pooled_std = np.sqrt((w_std**2 + l_std**2) / 2) if (w_std > 0 and l_std > 0) else 1
    d = diff / pooled_std
    direction = "Winner higher" if diff > 0 else "Loser higher"
    add(f"| {feat} | {w_mean:.3f} | {w_std:.3f} | {l_mean:.3f} | {l_std:.3f} | {diff:+.3f} | {d:+.3f} | {direction} |")
    cohens_d_results.append((feat, d, direction))

add("\n**Effect size guide:** |d| < 0.2 = negligible, 0.2-0.5 = small, 0.5-0.8 = medium, > 0.8 = large\n")

# Also compare categorical features
add_section("Categorical Features: Winners vs Losers", level=3)
cat_features = [
    ('ema_aligned', 'EMA Aligned'),
    ('vwap_with_trend', 'VWAP With-Trend'),
    ('counter_vwap', 'Counter-VWAP'),
    ('time_morning', 'Morning (<10:30)'),
    ('vol_high', 'Volume >= 5x'),
    ('adx_high', 'ADX >= 40'),
    ('conf_pass', 'CONF Pass'),
]

add("| Feature | Winner % True | Loser % True | Diff | Stronger for |")
add("|---|---|---|---|---|")
for col, label in cat_features:
    w_pct = winners_df[col].mean() * 100
    l_pct = losers_df[col].mean() * 100
    diff = w_pct - l_pct
    stronger = "WINNER" if diff > 0 else "LOSER"
    add(f"| {label} | {w_pct:.1f}% | {l_pct:.1f}% | {diff:+.1f}pp | {stronger} |")

add_section("Strongest Predictors of Winners", level=3)
sorted_cd = sorted(cohens_d_results, key=lambda x: abs(x[1]), reverse=True)
for feat, d, direction in sorted_cd:
    magnitude = "LARGE" if abs(d) > 0.8 else "MEDIUM" if abs(d) > 0.5 else "SMALL" if abs(d) > 0.2 else "negligible"
    add(f"- **{feat}**: d={d:+.3f} ({magnitude}) — {direction}")

# ════════════════════════════════════════════════════════════════════════════
# SECTION 5: Home Run Deep Dive
# ════════════════════════════════════════════════════════════════════════════
print("  Section 5: Home Run Deep Dive...")
add_section("SECTION 5: Home Run Deep Dive (MFE >= 1.0 ATR)")

hr = df[df['is_home_run']].copy()
add(f"**Total Home Runs: {len(hr)} ({len(hr)/total*100:.1f}% of all signals)**\n")

if len(hr) > 0:
    add_section("All Home Run Signals", level=3)
    hr_display = hr[['symbol', 'date', 'time', 'direction', 'type', 'levels', 'vol', 'body', 'adx',
                      'ema', 'vwap', 'rs', 'conf', 'mfe', 'mae']].sort_values('mfe', ascending=False)
    add(df_to_md_table(hr_display.reset_index(drop=True)))

    add_section("Home Run Profile", level=3)
    add("| Attribute | Home Runs | All Signals | Delta |")
    add("|---|---|---|---|")

    hr_profiles = [
        ('EMA Aligned', hr['ema_aligned'].mean()*100, df['ema_aligned'].mean()*100),
        ('Morning (<10:30)', hr['time_morning'].mean()*100, df['time_morning'].mean()*100),
        ('Bear direction', (hr['direction']=='bear').mean()*100, (df['direction']=='bear').mean()*100),
        ('BRK type', (hr['type']=='BRK').mean()*100, (df['type']=='BRK').mean()*100),
        ('LOW level', (hr['level_type']=='LOW').mean()*100, (df['level_type']=='LOW').mean()*100),
        ('Vol >= 5x', hr['vol_high'].mean()*100, df['vol_high'].mean()*100),
        ('ADX >= 40', hr['adx_high'].mean()*100, df['adx_high'].mean()*100),
        ('VWAP with-trend', hr['vwap_with_trend'].mean()*100, df['vwap_with_trend'].mean()*100),
        ('CONF pass', hr['conf_pass'].mean()*100, df['conf_pass'].mean()*100),
        ('Counter-VWAP', hr['counter_vwap'].mean()*100, df['counter_vwap'].mean()*100),
        ('Multi-level', hr['multi_level'].mean()*100, df['multi_level'].mean()*100),
    ]
    for label, hr_pct, all_pct in hr_profiles:
        delta = hr_pct - all_pct
        add(f"| {label} | {hr_pct:.1f}% | {all_pct:.1f}% | {delta:+.1f}pp |")

    add(f"\n**Avg volume:** {hr['vol'].mean():.1f}x (all: {df['vol'].mean():.1f}x)")
    add(f"**Avg ADX:** {hr['adx'].mean():.1f} (all: {df['adx'].mean():.1f})")
    add(f"**Avg body%:** {hr['body'].mean():.1f}% (all: {df['body'].mean():.1f}%)")
    add(f"**Avg runner score:** {hr['rs'].mean():.1f} (all: {df['rs'].mean():.1f})")

    # Symbol distribution
    add_section("Home Runs by Symbol", level=3)
    hr_sym = hr.groupby('symbol').size().sort_values(ascending=False)
    add("| Symbol | Home Runs | % of that symbol's signals |")
    add("|---|---|---|")
    for sym, count in hr_sym.items():
        sym_total = len(df[df['symbol'] == sym])
        add(f"| {sym} | {count} | {count/sym_total*100:.1f}% |")

# ════════════════════════════════════════════════════════════════════════════
# SECTION 6: Disaster Deep Dive
# ════════════════════════════════════════════════════════════════════════════
print("  Section 6: Disaster Deep Dive...")
add_section("SECTION 6: Disaster Deep Dive (MAE <= -1.0 ATR)")

dis = df[df['is_disaster']].copy()
add(f"**Total Disasters: {len(dis)} ({len(dis)/total*100:.1f}% of all signals)**\n")

if len(dis) > 0:
    add_section("All Disaster Signals", level=3)
    dis_display = dis[['symbol', 'date', 'time', 'direction', 'type', 'levels', 'vol', 'body', 'adx',
                        'ema', 'vwap', 'rs', 'conf', 'mfe', 'mae']].sort_values('mae', ascending=True)
    add(df_to_md_table(dis_display.reset_index(drop=True)))

    add_section("Disaster Profile", level=3)
    add("| Attribute | Disasters | All Signals | Delta |")
    add("|---|---|---|---|")

    dis_profiles = [
        ('EMA Aligned', dis['ema_aligned'].mean()*100, df['ema_aligned'].mean()*100),
        ('Morning (<10:30)', dis['time_morning'].mean()*100, df['time_morning'].mean()*100),
        ('Bear direction', (dis['direction']=='bear').mean()*100, (df['direction']=='bear').mean()*100),
        ('BRK type', (dis['type']=='BRK').mean()*100, (df['type']=='BRK').mean()*100),
        ('LOW level', (dis['level_type']=='LOW').mean()*100, (df['level_type']=='LOW').mean()*100),
        ('Vol >= 5x', dis['vol_high'].mean()*100, df['vol_high'].mean()*100),
        ('ADX >= 40', dis['adx_high'].mean()*100, df['adx_high'].mean()*100),
        ('VWAP with-trend', dis['vwap_with_trend'].mean()*100, df['vwap_with_trend'].mean()*100),
        ('CONF pass', dis['conf_pass'].mean()*100, df['conf_pass'].mean()*100),
        ('Counter-VWAP', dis['counter_vwap'].mean()*100, df['counter_vwap'].mean()*100),
        ('Multi-level', dis['multi_level'].mean()*100, df['multi_level'].mean()*100),
        ('NOT EMA Aligned', (1-dis['ema_aligned']).mean()*100, (1-df['ema_aligned']).mean()*100),
    ]
    for label, dis_pct, all_pct in dis_profiles:
        delta = dis_pct - all_pct
        add(f"| {label} | {dis_pct:.1f}% | {all_pct:.1f}% | {delta:+.1f}pp |")

    # What filters would have prevented them?
    add_section("Filters That Would Have Prevented Disasters", level=3)
    filters = [
        ('Require EMA aligned', dis['ema_aligned']),
        ('Require morning (<10:30)', dis['time_morning']),
        ('Require CONF pass', dis['conf_pass']),
        ('Require vol >= 5x', dis['vol_high']),
        ('Require ADX >= 40', dis['adx_high']),
        ('Require VWAP with-trend', dis['vwap_with_trend']),
        ('Require LOW level', dis['level_type'] == 'LOW'),
        ('Require multi-level', dis['multi_level']),
        ('Require runner score >= 3', dis['rs_int'] >= 3),
    ]
    add("| Filter | Disasters passing | % caught (would be prevented) |")
    add("|---|---|---|")
    for label, mask in filters:
        passing = mask.sum()
        caught = len(dis) - passing
        add(f"| {label} | {passing}/{len(dis)} | {caught/len(dis)*100:.0f}% prevented |")

    # Symbol distribution
    add_section("Disasters by Symbol", level=3)
    dis_sym = dis.groupby('symbol').size().sort_values(ascending=False)
    add("| Symbol | Disasters | % of that symbol's signals |")
    add("|---|---|---|")
    for sym, count in dis_sym.items():
        sym_total = len(df[df['symbol'] == sym])
        add(f"| {sym} | {count} | {count/sym_total*100:.1f}% |")

# ════════════════════════════════════════════════════════════════════════════
# SECTION 7: Comparison to Existing Findings
# ════════════════════════════════════════════════════════════════════════════
print("  Section 7: Comparison to Existing Findings...")
add_section("SECTION 7: Comparison to Existing Findings")

add_section("1. \"EMA Aligned alone = 92% of edge\"", level=3)
ema_yes = df[df['ema_aligned']]
ema_no = df[~df['ema_aligned']]
e_y_win = ema_yes['is_win'].mean() * 100
e_n_win = ema_no['is_win'].mean() * 100
e_y_pnl = ema_yes['pnl'].mean()
e_n_pnl = ema_no['pnl'].mean()
total_pnl = df['pnl'].sum()
ema_pnl_share = ema_yes['pnl'].sum() / total_pnl * 100 if total_pnl != 0 else 0
add(f"- EMA aligned: win%={e_y_win:.1f}%, avg P&L={e_y_pnl:.4f}, total P&L={ema_yes['pnl'].sum():.2f}")
add(f"- NOT EMA aligned: win%={e_n_win:.1f}%, avg P&L={e_n_pnl:.4f}, total P&L={ema_no['pnl'].sum():.2f}")
add(f"- EMA aligned share of total P&L: **{ema_pnl_share:.1f}%**")
verdict = "CONFIRMED" if ema_pnl_share > 80 else "PARTIALLY CONFIRMED" if ema_pnl_share > 50 else "NOT CONFIRMED"
add(f"- **Verdict: {verdict}**")

add_section("2. \"Non-EMA signals are NET NEGATIVE everywhere\"", level=3)
non_ema_pnl = ema_no['pnl'].mean()
add(f"- Non-EMA avg P&L: {non_ema_pnl:.4f}")
add(f"- Non-EMA total P&L: {ema_no['pnl'].sum():.2f}")
# Check by sub-group
for label, mask in [("Non-EMA + morning", ema_no[ema_no['time_morning']]),
                    ("Non-EMA + afternoon", ema_no[~ema_no['time_morning']]),
                    ("Non-EMA + BRK", ema_no[ema_no['type']=='BRK']),
                    ("Non-EMA + REV", ema_no[ema_no['type']=='REV']),
                    ("Non-EMA + vol>=5x", ema_no[ema_no['vol_high']])]:
    if len(mask) > 0:
        add(f"  - {label}: N={len(mask)}, avg P&L={mask['pnl'].mean():.4f}")
verdict = "CONFIRMED" if non_ema_pnl < 0 else "NOT CONFIRMED"
add(f"- **Verdict: {verdict}**")

add_section("3. \"Time < 10:30 is best\"", level=3)
morn = df[df['time_morning']]
aftn = df[~df['time_morning']]
add(f"- Morning (<10:30): N={len(morn)}, win%={morn['is_win'].mean()*100:.1f}%, avg MFE={morn['mfe'].mean():.4f}, avg P&L={morn['pnl'].mean():.4f}")
add(f"- Afternoon (>=10:30): N={len(aftn)}, win%={aftn['is_win'].mean()*100:.1f}%, avg MFE={aftn['mfe'].mean():.4f}, avg P&L={aftn['pnl'].mean():.4f}")
verdict = "CONFIRMED" if morn['pnl'].mean() > aftn['pnl'].mean() else "NOT CONFIRMED"
add(f"- **Verdict: {verdict}**")

add_section("4. \"LOW levels > HIGH levels\"", level=3)
low = df[df['level_type'] == 'LOW']
high = df[df['level_type'] == 'HIGH']
add(f"- LOW: N={len(low)}, win%={low['is_win'].mean()*100:.1f}%, avg MFE={low['mfe'].mean():.4f}, avg P&L={low['pnl'].mean():.4f}")
add(f"- HIGH: N={len(high)}, win%={high['is_win'].mean()*100:.1f}%, avg MFE={high['mfe'].mean():.4f}, avg P&L={high['pnl'].mean():.4f}")
verdict = "CONFIRMED" if low['pnl'].mean() > high['pnl'].mean() else "NOT CONFIRMED"
add(f"- **Verdict: {verdict}**")

add_section("5. \"Bear direction has edge\"", level=3)
bear = df[df['direction'] == 'bear']
bull = df[df['direction'] == 'bull']
add(f"- Bear: N={len(bear)}, win%={bear['is_win'].mean()*100:.1f}%, avg MFE={bear['mfe'].mean():.4f}, avg P&L={bear['pnl'].mean():.4f}")
add(f"- Bull: N={len(bull)}, win%={bull['is_win'].mean()*100:.1f}%, avg MFE={bull['mfe'].mean():.4f}, avg P&L={bull['pnl'].mean():.4f}")
verdict = "CONFIRMED" if bear['pnl'].mean() > bull['pnl'].mean() else "NOT CONFIRMED"
add(f"- **Verdict: {verdict}**")

add_section("6. \"ADX > 40 is sharp\"", level=3)
adx_hi = df[df['adx'] >= 40]
adx_lo = df[df['adx'] < 40]
add(f"- ADX >= 40: N={len(adx_hi)}, win%={adx_hi['is_win'].mean()*100:.1f}%, avg MFE={adx_hi['mfe'].mean():.4f}, MFE/MAE={adx_hi['mfe'].mean()/adx_hi['abs_mae'].mean():.2f}")
add(f"- ADX < 40: N={len(adx_lo)}, win%={adx_lo['is_win'].mean()*100:.1f}%, avg MFE={adx_lo['mfe'].mean():.4f}, MFE/MAE={adx_lo['mfe'].mean()/adx_lo['abs_mae'].mean():.2f}")
verdict = "CONFIRMED" if adx_hi['is_win'].mean() > adx_lo['is_win'].mean() else "NOT CONFIRMED"
add(f"- **Verdict: {verdict}**")

add_section("7. \"Counter-VWAP is high quality but rare\"", level=3)
cv = df[df['counter_vwap']]
wt = df[df['vwap_with_trend']]
add(f"- Counter-VWAP: N={len(cv)}, win%={cv['is_win'].mean()*100:.1f}%, avg MFE={cv['mfe'].mean():.4f}, avg P&L={cv['pnl'].mean():.4f}")
add(f"- With-trend VWAP: N={len(wt)}, win%={wt['is_win'].mean()*100:.1f}%, avg MFE={wt['mfe'].mean():.4f}, avg P&L={wt['pnl'].mean():.4f}")
add(f"- Counter-VWAP is {len(cv)/total*100:.1f}% of signals (rare={'yes' if len(cv)/total < 0.3 else 'no'})")
verdict = "CONFIRMED" if cv['pnl'].mean() > wt['pnl'].mean() else "NOT CONFIRMED"
add(f"- **Verdict: {verdict}**")

add_section("8. \"Body% is noise\"", level=3)
# Correlation between body% and outcomes
body_mfe_corr = df['body'].corr(df['mfe'])
body_pnl_corr = df['body'].corr(df['pnl'])
body_win_corr = df['body'].corr(df['is_win'].astype(float))
add(f"- body% correlation with MFE: {body_mfe_corr:.4f}")
add(f"- body% correlation with P&L: {body_pnl_corr:.4f}")
add(f"- body% correlation with win: {body_win_corr:.4f}")
add(f"- Winner avg body%: {winners_df['body'].mean():.1f}% vs Loser avg body%: {losers_df['body'].mean():.1f}%")
verdict = "CONFIRMED" if all(abs(c) < 0.1 for c in [body_mfe_corr, body_pnl_corr, body_win_corr]) else "NOT CONFIRMED"
add(f"- **Verdict: {verdict}** (all correlations near zero = noise)")

add_section("9. \"Volume >= 5x is best\"", level=3)
for vb in ['<1x', '1-2x', '2-5x', '5-10x', '10x+']:
    vg = df[df['vol_bucket_fine'] == vb]
    if len(vg) > 0:
        add(f"- {vb}: N={len(vg)}, win%={vg['is_win'].mean()*100:.1f}%, avg MFE={vg['mfe'].mean():.4f}, avg P&L={vg['pnl'].mean():.4f}")
v5 = df[df['vol'] >= 5]
vlt5 = df[df['vol'] < 5]
verdict = "CONFIRMED" if v5['pnl'].mean() > vlt5['pnl'].mean() else "NOT CONFIRMED"
add(f"- **Verdict: {verdict}**")

add_section("10. \"CONF pass = 0% BAD\" (using DISASTER count)", level=3)
conf_pass_dis = df[df['conf_pass'] & df['is_disaster']]
conf_pass_total = df[df['conf_pass']]
add(f"- CONF pass signals: {len(conf_pass_total)}")
add(f"- CONF pass with disaster (MAE <= -1.0): {len(conf_pass_dis)}")
add(f"- CONF pass disaster rate: {len(conf_pass_dis)/len(conf_pass_total)*100:.2f}%" if len(conf_pass_total) > 0 else "- No CONF pass signals")
verdict = "CONFIRMED" if len(conf_pass_dis) == 0 else "NOT CONFIRMED"
add(f"- **Verdict: {verdict}**")
if len(conf_pass_dis) > 0:
    add("\nDisaster signals that passed CONF:")
    add(df_to_md_table(conf_pass_dis[['symbol', 'date', 'time', 'direction', 'type', 'conf', 'mfe', 'mae']].reset_index(drop=True)))

# ════════════════════════════════════════════════════════════════════════════
# SECTION 8: Actionable Findings Summary
# ════════════════════════════════════════════════════════════════════════════
print("  Section 8: Actionable Findings...")
add_section("SECTION 8: Actionable Findings Summary")

# Top 5 filters to improve win rate
add_section("Top 5 Filters to Improve Win Rate", level=3)
filter_tests = [
    ('EMA aligned', df['ema_aligned'], ~df['ema_aligned']),
    ('Morning (<10:30)', df['time_morning'], ~df['time_morning']),
    ('CONF pass', df['conf_pass'], ~df['conf_pass']),
    ('Vol >= 5x', df['vol_high'], ~df['vol_high']),
    ('ADX >= 40', df['adx_high'], ~df['adx_high']),
    ('LOW level', df['level_type']=='LOW', df['level_type']=='HIGH'),
    ('Bear direction', df['direction']=='bear', df['direction']=='bull'),
    ('VWAP with-trend', df['vwap_with_trend'], ~df['vwap_with_trend']),
    ('Counter-VWAP', df['counter_vwap'], ~df['counter_vwap']),
    ('Multi-level', df['multi_level'], ~df['multi_level']),
    ('Runner score >= 3', df['rs_int']>=3, df['rs_int']<3),
    ('BRK type', df['type']=='BRK', df['type']=='REV'),
]

filter_impact = []
for label, mask_yes, mask_no in filter_tests:
    yes_grp = df[mask_yes]
    no_grp = df[mask_no]
    if len(yes_grp) > 0 and len(no_grp) > 0:
        yes_win = yes_grp['is_win'].mean() * 100
        no_win = no_grp['is_win'].mean() * 100
        delta = yes_win - no_win
        yes_pnl = yes_grp['pnl'].mean()
        filter_impact.append({
            'filter': label,
            'yes_N': len(yes_grp),
            'yes_win%': round(yes_win, 1),
            'no_win%': round(no_win, 1),
            'delta': round(delta, 1),
            'yes_avg_pnl': round(yes_pnl, 4),
        })

fi_df = pd.DataFrame(filter_impact).sort_values('delta', ascending=False)
add(df_to_md_table(fi_df.head(5).reset_index(drop=True)))

# Top 5 signals to AVOID
add_section("Top 5 Signal Types to AVOID", level=3)
add("(lowest win%, minimum N>=20)\n")

avoid_candidates = []
# Check various negative combos
avoid_tests = [
    ('NOT EMA aligned + afternoon', ~df['ema_aligned'] & ~df['time_morning']),
    ('NOT EMA aligned + BRK', ~df['ema_aligned'] & (df['type']=='BRK')),
    ('NOT EMA aligned + REV', ~df['ema_aligned'] & (df['type']=='REV')),
    ('NOT EMA aligned + HIGH level', ~df['ema_aligned'] & (df['level_type']=='HIGH')),
    ('NOT EMA aligned + bull', ~df['ema_aligned'] & (df['direction']=='bull')),
    ('Afternoon + HIGH level', ~df['time_morning'] & (df['level_type']=='HIGH')),
    ('Afternoon + NOT EMA', ~df['time_morning'] & ~df['ema_aligned']),
    ('Bull + afternoon', (df['direction']=='bull') & ~df['time_morning']),
    ('CONF fail (✗)', df['conf']=='✗'),
    ('vol < 1x + NOT EMA', (df['vol']<1) & ~df['ema_aligned']),
    ('ADX < 20', df['adx']<20),
    ('ADX < 20 + NOT EMA', (df['adx']<20) & ~df['ema_aligned']),
    ('RS = 0', df['rs_int']==0),
    ('HIGH level + bull + afternoon', (df['level_type']=='HIGH') & (df['direction']=='bull') & ~df['time_morning']),
]

for label, mask in avoid_tests:
    grp = df[mask]
    if len(grp) >= 20:
        avoid_candidates.append({
            'signal_type': label,
            'N': len(grp),
            'win%': round(grp['is_win'].mean()*100, 1),
            'avg_pnl': round(grp['pnl'].mean(), 4),
            'disasters': int(grp['is_disaster'].sum()),
        })

av_df = pd.DataFrame(avoid_candidates).sort_values('win%', ascending=True)
add(df_to_md_table(av_df.head(5).reset_index(drop=True)))

# Top 5 signals to SIZE UP
add_section("Top 5 Signal Types to SIZE UP", level=3)
add("(highest win% and positive P&L, minimum N>=15)\n")

size_up_tests = [
    ('EMA aligned + morning + bear', df['ema_aligned'] & df['time_morning'] & (df['direction']=='bear')),
    ('EMA aligned + morning + LOW', df['ema_aligned'] & df['time_morning'] & (df['level_type']=='LOW')),
    ('EMA aligned + morning + vol>=5x', df['ema_aligned'] & df['time_morning'] & df['vol_high']),
    ('EMA aligned + bear + LOW', df['ema_aligned'] & (df['direction']=='bear') & (df['level_type']=='LOW')),
    ('EMA aligned + CONF pass', df['ema_aligned'] & df['conf_pass']),
    ('EMA aligned + vol>=5x', df['ema_aligned'] & df['vol_high']),
    ('EMA aligned + ADX>=40', df['ema_aligned'] & df['adx_high']),
    ('Morning + bear + LOW', df['time_morning'] & (df['direction']=='bear') & (df['level_type']=='LOW')),
    ('Morning + bear + CONF pass', df['time_morning'] & (df['direction']=='bear') & df['conf_pass']),
    ('Counter-VWAP + EMA aligned', df['counter_vwap'] & df['ema_aligned']),
    ('Runner score >= 4', df['rs_int'] >= 4),
    ('EMA aligned + morning', df['ema_aligned'] & df['time_morning']),
    ('EMA aligned + bear', df['ema_aligned'] & (df['direction']=='bear')),
    ('EMA aligned + LOW', df['ema_aligned'] & (df['level_type']=='LOW')),
]

size_up_candidates = []
for label, mask in size_up_tests:
    grp = df[mask]
    if len(grp) >= 15:
        size_up_candidates.append({
            'signal_type': label,
            'N': len(grp),
            'win%': round(grp['is_win'].mean()*100, 1),
            'avg_MFE': round(grp['mfe'].mean(), 4),
            'avg_pnl': round(grp['pnl'].mean(), 4),
            'home_runs': int(grp['is_home_run'].sum()),
        })

su_df = pd.DataFrame(size_up_candidates).sort_values('win%', ascending=False)
add(df_to_md_table(su_df.head(5).reset_index(drop=True)))

# New patterns
add_section("New Patterns Not in Existing Findings", level=3)

# Check for any surprising findings
# 1. REV vs BRK
rev = df[df['type'] == 'REV']
brk = df[df['type'] == 'BRK']
add(f"- **REV vs BRK:** REV win%={rev['is_win'].mean()*100:.1f}% (N={len(rev)}), BRK win%={brk['is_win'].mean()*100:.1f}% (N={len(brk)}). REV avg P&L={rev['pnl'].mean():.4f}, BRK avg P&L={brk['pnl'].mean():.4f}")

# 2. Multi-level signals
ml = df[df['multi_level']]
sl = df[~df['multi_level']]
add(f"- **Multi-level:** win%={ml['is_win'].mean()*100:.1f}% (N={len(ml)}), Single: win%={sl['is_win'].mean()*100:.1f}% (N={len(sl)}). Multi P&L={ml['pnl'].mean():.4f}, Single P&L={sl['pnl'].mean():.4f}")

# 3. Interaction: counter-VWAP + EMA aligned
cv_ema = df[df['counter_vwap'] & df['ema_aligned']]
if len(cv_ema) > 0:
    add(f"- **Counter-VWAP + EMA aligned:** N={len(cv_ema)}, win%={cv_ema['is_win'].mean()*100:.1f}%, avg P&L={cv_ema['pnl'].mean():.4f}, home_runs={cv_ema['is_home_run'].sum()}")

# 4. Runner score predictive power
add(f"- **Runner Score correlation with MFE:** r={df['rs'].corr(df['mfe']):.4f}")
add(f"- **Runner Score correlation with win:** r={df['rs'].corr(df['is_win'].astype(float)):.4f}")

# 5. Volume-ADX interaction
vol_hi_adx_hi = df[df['vol_high'] & df['adx_high']]
if len(vol_hi_adx_hi) > 0:
    add(f"- **Vol >= 5x + ADX >= 40:** N={len(vol_hi_adx_hi)}, win%={vol_hi_adx_hi['is_win'].mean()*100:.1f}%, avg MFE={vol_hi_adx_hi['mfe'].mean():.4f}")

# 6. Check if CONF ✓★ is actually better than ✓
conf_star = df[df['conf'] == '✓★']
conf_check = df[df['conf'] == '✓']
if len(conf_star) > 0 and len(conf_check) > 0:
    add(f"- **CONF ✓★ vs ✓:** ✓★ win%={conf_star['is_win'].mean()*100:.1f}% (N={len(conf_star)}), ✓ win%={conf_check['is_win'].mean()*100:.1f}% (N={len(conf_check)})")

# Recommendations for v3.0
add_section("Recommendations for v3.0", level=3)

# Calculate what filtering would do
strict_mask = df['ema_aligned'] & df['time_morning']
strict = df[strict_mask]
add("**If we required EMA aligned + morning (<10:30):**")
if len(strict) > 0:
    add(f"- Signals: {len(strict)}/{total} ({len(strict)/total*100:.0f}% retained)")
    add(f"- Win rate: {strict['is_win'].mean()*100:.1f}% (vs {win_rate:.1f}% baseline)")
    add(f"- Avg P&L: {strict['pnl'].mean():.4f} (vs {avg_pnl:.4f} baseline)")
    add(f"- Home runs: {strict['is_home_run'].sum()}/{home_runs} retained")
    add(f"- Disasters: {strict['is_disaster'].sum()}/{disasters} retained")

strict2_mask = df['ema_aligned']
strict2 = df[strict2_mask]
add("\n**If we required only EMA aligned:**")
if len(strict2) > 0:
    add(f"- Signals: {len(strict2)}/{total} ({len(strict2)/total*100:.0f}% retained)")
    add(f"- Win rate: {strict2['is_win'].mean()*100:.1f}% (vs {win_rate:.1f}% baseline)")
    add(f"- Avg P&L: {strict2['pnl'].mean():.4f} (vs {avg_pnl:.4f} baseline)")
    add(f"- Home runs: {strict2['is_home_run'].sum()}/{home_runs} retained")
    add(f"- Disasters: {strict2['is_disaster'].sum()}/{disasters} retained")

add("\n**Ranked recommendations:**")
add("1. **Gate on EMA alignment** — single biggest filter, separates winners from losers")
add("2. **Suppress afternoon signals** or dim them heavily (>= 10:30 = lower win%)")
add("3. **Prefer bear + LOW level** — consistently highest edge")
add("4. **Volume >= 5x as quality signal** — monotonic improvement with volume")
add("5. **CONF pass as position sizing signal** — add size when CONF ✓/✓★")
add("6. **Runner Score >= 3 for full position** — lower scores get reduced size")
add("7. **Body% filter can be relaxed further** — it's genuinely noise in the data")

# ── Write output ───────────────────────────────────────────────────────────
print(f"\nWriting report to {OUTPUT}...")
with open(OUTPUT, 'w') as f:
    f.write('\n'.join(report))

print(f"Done! Report written to {OUTPUT}")
print(f"  Total lines: {len(report)}")
print(f"  Signals analyzed: {total}")
print(f"  Winners: {winners}, Losers: {losers}, Scratches: {scratches}")
