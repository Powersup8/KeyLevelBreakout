"""
v29 Momentum Patterns Analysis
Analyzes real intraday momentum patterns after 9:50 ET using v28a signal + follow-through data.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

BASE = Path(__file__).parent
OUT = BASE / "v29-momentum-patterns.md"

# ── Load data ──────────────────────────────────────────────────────────
sig = pd.read_csv(BASE / "v28a-signals.csv")
ft = pd.read_csv(BASE / "v28a-follow-through.csv")

print(f"Signals: {len(sig)} rows, Follow-through: {len(ft)} rows")

# ── Parse time ─────────────────────────────────────────────────────────
def parse_time_minutes(t):
    """Convert '9:35' or '13:20' to minutes since midnight."""
    if pd.isna(t):
        return np.nan
    parts = str(t).split(':')
    return int(parts[0]) * 60 + int(parts[1])

sig['time_min'] = sig['time'].apply(parse_time_minutes)
ft['time_min'] = ft['time'].apply(parse_time_minutes)

# Extract date for grouping — handle timezone-aware ISO strings
sig['date'] = pd.to_datetime(sig['datetime'], utc=True).dt.date
ft['date'] = pd.to_datetime(ft['datetime'], utc=True).dt.date

# ── Filter: actionable signal types only (not CONF, RETEST, 5mCHECK) ──
ACTION_TYPES = ['BRK', 'REV', 'RCL', 'VWAP', 'QBS', 'MC']
sig_act = sig[sig['line_type'].isin(ACTION_TYPES)].copy()
ft_act = ft.copy()  # follow-through already only has actionable signals

# After 9:50 filters
AFTER_950 = 9 * 60 + 50  # 590 minutes
sig_post = sig_act[sig_act['time_min'] > AFTER_950].copy()
ft_post = ft_act[ft_act['time_min'] > AFTER_950].copy()

# 30-min follow-through only
ft30 = ft_post[ft_post['window'] == 30].copy()

print(f"Actionable signals: {len(sig_act)}, after 9:50: {len(sig_post)}")
print(f"Follow-through after 9:50: {len(ft_post)}, 30-min window: {len(ft30)}")

# Helper: merge signal with 30-min FT
def merge_ft30(sig_df, ft_df):
    """Merge signals with 30-min follow-through on symbol+datetime+type+direction."""
    ft30_w = ft_df[ft_df['window'] == 30].copy()
    merged = sig_df.merge(
        ft30_w[['symbol', 'datetime', 'type', 'direction', 'mfe', 'mae', 'ratio', 'entry']],
        left_on=['symbol', 'datetime', 'line_type', 'direction'],
        right_on=['symbol', 'datetime', 'type', 'direction'],
        how='inner',
        suffixes=('', '_ft')
    )
    return merged

# ── Helper: stats summary ──────────────────────────────────────────────
def stats(df, label=""):
    n = len(df)
    if n == 0:
        return f"  {label}: n=0\n"
    mfe_med = df['mfe'].median()
    mfe_avg = df['mfe'].mean()
    mae_med = df['mae'].median()
    mae_avg = df['mae'].mean()
    ratio_med = df['ratio'].median() if 'ratio' in df.columns else 0
    pct_pos = (df['mfe'] > 0).mean() * 100
    pct_runner = (df['mfe'] >= 1.0).mean() * 100
    return (f"  {label}: n={n}, MFE avg={mfe_avg:.3f} med={mfe_med:.3f}, "
            f"MAE avg={mae_avg:.3f} med={mae_med:.3f}, "
            f"pos={pct_pos:.0f}%, runners(≥1.0)={pct_runner:.0f}%\n")

lines = []
def w(s):
    lines.append(s)
    print(s)

w("# v29 Momentum Patterns Analysis (After 9:50 ET)")
w(f"\nData: {len(sig)} signals, {len(ft)} follow-through rows")
w(f"Actionable signals after 9:50: {len(sig_post)}")
w(f"30-min follow-through after 9:50: {len(ft30)}")
w("")

# ════════════════════════════════════════════════════════════════════════
# 1. AFTER-9:50 BIG BARS (range_atr >= 1.5)
# ════════════════════════════════════════════════════════════════════════
w("## 1. After-9:50 Big Bars (range_atr >= 1.5)")
w("")

sig_post_numeric = sig_post.copy()
sig_post_numeric['range_atr'] = pd.to_numeric(sig_post_numeric['range_atr'], errors='coerce')
big_bars = sig_post_numeric[sig_post_numeric['range_atr'] >= 1.5]
w(f"Total big bars after 9:50: **{len(big_bars)}**")

# Merge with FT
big_bars_ft = merge_ft30(big_bars, ft_post)
w(f"With 30-min follow-through: {len(big_bars_ft)}")
w("")

if len(big_bars_ft) > 0:
    w("### By signal type:")
    for t in sorted(big_bars_ft['line_type'].unique()):
        sub = big_bars_ft[big_bars_ft['line_type'] == t]
        w(stats(sub, t))

    w("### By direction:")
    for d in ['bull', 'bear']:
        sub = big_bars_ft[big_bars_ft['direction'] == d]
        w(stats(sub, d))

    w("### By time bucket:")
    big_bars_ft['hour'] = big_bars_ft['time_min'] // 60
    for h in sorted(big_bars_ft['hour'].unique()):
        sub = big_bars_ft[big_bars_ft['hour'] == h]
        label = f"{h}:00-{h}:59"
        w(stats(sub, label))

    w("### Range ATR distribution:")
    for lo, hi, label in [(1.5, 2.0, "1.5-2.0"), (2.0, 3.0, "2.0-3.0"), (3.0, 99, "3.0+")]:
        sub = big_bars_ft[(big_bars_ft['range_atr'] >= lo) & (big_bars_ft['range_atr'] < hi)]
        w(stats(sub, label))

w("")

# ════════════════════════════════════════════════════════════════════════
# 2. VOLUME SURGE AFTER 9:50 (vol >= 5.0)
# ════════════════════════════════════════════════════════════════════════
w("## 2. Volume Surge After 9:50 (vol >= 5.0)")
w("")

sig_post_numeric['vol'] = pd.to_numeric(sig_post_numeric['vol'], errors='coerce')
vol_surge = sig_post_numeric[sig_post_numeric['vol'] >= 5.0]
w(f"Total vol surge signals after 9:50: **{len(vol_surge)}**")

vol_surge_ft = merge_ft30(vol_surge, ft_post)
w(f"With 30-min follow-through: {len(vol_surge_ft)}")
w("")

if len(vol_surge_ft) > 0:
    w("### Overall:")
    w(stats(vol_surge_ft, "vol>=5x"))

    w("### By volume bucket:")
    vol_surge_ft['vol'] = pd.to_numeric(vol_surge_ft['vol'], errors='coerce')
    for lo, hi, label in [(5, 10, "5-10x"), (10, 20, "10-20x"), (20, 999, "20x+")]:
        sub = vol_surge_ft[(vol_surge_ft['vol'] >= lo) & (vol_surge_ft['vol'] < hi)]
        w(stats(sub, label))

    w("### By signal type:")
    for t in sorted(vol_surge_ft['line_type'].unique()):
        sub = vol_surge_ft[vol_surge_ft['line_type'] == t]
        w(stats(sub, t))

    w("### Combined: vol>=5x AND range_atr>=1.5:")
    combined = vol_surge_ft[pd.to_numeric(vol_surge_ft['range_atr'], errors='coerce') >= 1.5]
    w(stats(combined, "vol>=5x + big bar"))

w("")

# ════════════════════════════════════════════════════════════════════════
# 3. CONSECUTIVE DIRECTIONAL BARS
# ════════════════════════════════════════════════════════════════════════
w("## 3. Consecutive Directional Bars (same symbol, same day, same direction)")
w("")

# Sort signals by symbol, date, time
consec_df = sig_act.copy()
consec_df['date'] = pd.to_datetime(consec_df['datetime'], utc=True).dt.date
consec_df = consec_df.sort_values(['symbol', 'date', 'time_min'])

# Find consecutive same-direction signals
consec_signals = []
for (sym, date), group in consec_df.groupby(['symbol', 'date']):
    rows = group.reset_index(drop=True)
    if len(rows) < 2:
        continue

    streak_start = 0
    for i in range(1, len(rows)):
        if rows.loc[i, 'direction'] == rows.loc[streak_start, 'direction']:
            # Continue streak - mark this signal as part of consecutive run
            streak_len = i - streak_start + 1
            if streak_len >= 2:
                # Mark the 2nd and 3rd signals in the streak
                consec_signals.append({
                    'symbol': sym,
                    'date': date,
                    'datetime': rows.loc[i, 'datetime'],
                    'time': rows.loc[i, 'time'],
                    'time_min': rows.loc[i, 'time_min'],
                    'line_type': rows.loc[i, 'line_type'],
                    'direction': rows.loc[i, 'direction'],
                    'streak_pos': streak_len,
                    'vol': rows.loc[i, 'vol'],
                    'range_atr': rows.loc[i, 'range_atr'],
                    'ema': rows.loc[i, 'ema'],
                    'vwap': rows.loc[i, 'vwap'],
                })
        else:
            streak_start = i

consec_df2 = pd.DataFrame(consec_signals)
w(f"Consecutive directional signals (2nd+ in streak): **{len(consec_df2)}**")

if len(consec_df2) > 0:
    # Filter to after 9:50
    consec_post = consec_df2[consec_df2['time_min'] > AFTER_950]
    w(f"After 9:50: {len(consec_post)}")

    # Merge with FT
    consec_ft = consec_post.merge(
        ft_post[ft_post['window'] == 30][['symbol', 'datetime', 'type', 'direction', 'mfe', 'mae', 'ratio']],
        left_on=['symbol', 'datetime', 'line_type', 'direction'],
        right_on=['symbol', 'datetime', 'type', 'direction'],
        how='inner'
    )
    w(f"With 30-min FT: {len(consec_ft)}")
    w("")

    if len(consec_ft) > 0:
        w("### By streak position:")
        for pos in sorted(consec_ft['streak_pos'].unique()):
            sub = consec_ft[consec_ft['streak_pos'] == pos]
            w(stats(sub, f"position {pos}"))

        w("### Consecutive vs Non-consecutive (all after 9:50, 30-min):")
        # Non-consecutive = all signals after 9:50 NOT in consecutive runs
        all_ft30_post = ft30.copy()
        w(stats(all_ft30_post, "ALL after 9:50"))
        w(stats(consec_ft, "CONSECUTIVE only"))

        # Non-consecutive
        consec_keys = set(zip(consec_ft['symbol'], consec_ft['datetime']))
        non_consec = all_ft30_post[~all_ft30_post.apply(
            lambda r: (r['symbol'], r['datetime']) in consec_keys, axis=1)]
        w(stats(non_consec, "NON-CONSECUTIVE"))

w("")

# ════════════════════════════════════════════════════════════════════════
# 4. VWAP CROSS MOMENTUM
# ════════════════════════════════════════════════════════════════════════
w("## 4. VWAP Cross Momentum")
w("")

# Find signals where VWAP status flips between consecutive signals
vwap_df = sig_act[sig_act['vwap'].isin(['above', 'below'])].copy()
vwap_df = vwap_df.sort_values(['symbol', 'date', 'time_min'])

vwap_cross_signals = []
for (sym, date), group in vwap_df.groupby(['symbol', 'date']):
    rows = group.reset_index(drop=True)
    for i in range(1, len(rows)):
        prev_vwap = rows.loc[i-1, 'vwap']
        curr_vwap = rows.loc[i, 'vwap']
        if prev_vwap != curr_vwap:
            vwap_cross_signals.append({
                'symbol': sym,
                'date': date,
                'datetime': rows.loc[i, 'datetime'],
                'time': rows.loc[i, 'time'],
                'time_min': rows.loc[i, 'time_min'],
                'line_type': rows.loc[i, 'line_type'],
                'direction': rows.loc[i, 'direction'],
                'vwap_from': prev_vwap,
                'vwap_to': curr_vwap,
                'vol': rows.loc[i, 'vol'],
                'ema': rows.loc[i, 'ema'],
                'range_atr': rows.loc[i, 'range_atr'],
            })

vwap_cross_df = pd.DataFrame(vwap_cross_signals)
w(f"VWAP cross signals (vwap flips between consecutive signals): **{len(vwap_cross_df)}**")

if len(vwap_cross_df) > 0:
    vwap_cross_post = vwap_cross_df[vwap_cross_df['time_min'] > AFTER_950]
    w(f"After 9:50: {len(vwap_cross_post)}")

    # Merge with FT
    vwap_cross_ft = vwap_cross_post.merge(
        ft_post[ft_post['window'] == 30][['symbol', 'datetime', 'type', 'direction', 'mfe', 'mae', 'ratio']],
        left_on=['symbol', 'datetime', 'line_type', 'direction'],
        right_on=['symbol', 'datetime', 'type', 'direction'],
        how='inner'
    )
    w(f"With 30-min FT: {len(vwap_cross_ft)}")
    w("")

    if len(vwap_cross_ft) > 0:
        w("### Overall VWAP cross:")
        w(stats(vwap_cross_ft, "VWAP cross"))

        w("### By cross direction:")
        for cross in ['below→above', 'above→below']:
            fr, to = cross.split('→')
            sub = vwap_cross_ft[(vwap_cross_ft['vwap_from'] == fr) & (vwap_cross_ft['vwap_to'] == to)]
            w(stats(sub, cross))

        w("### VWAP cross aligned with signal direction:")
        # Bull signal + crossing above VWAP = aligned
        aligned = vwap_cross_ft[
            ((vwap_cross_ft['direction'] == 'bull') & (vwap_cross_ft['vwap_to'] == 'above')) |
            ((vwap_cross_ft['direction'] == 'bear') & (vwap_cross_ft['vwap_to'] == 'below'))
        ]
        misaligned = vwap_cross_ft[
            ((vwap_cross_ft['direction'] == 'bull') & (vwap_cross_ft['vwap_to'] == 'below')) |
            ((vwap_cross_ft['direction'] == 'bear') & (vwap_cross_ft['vwap_to'] == 'above'))
        ]
        w(stats(aligned, "ALIGNED (bull+above / bear+below)"))
        w(stats(misaligned, "MISALIGNED (bull+below / bear+above)"))

w("")

# ════════════════════════════════════════════════════════════════════════
# 5. BEST INTRADAY MOMENTUM FINGERPRINT (runners after 9:50)
# ════════════════════════════════════════════════════════════════════════
w("## 5. Best Intraday Momentum Fingerprint (30-min MFE >= 1.0 ATR after 9:50)")
w("")

runners = ft30[ft30['mfe'] >= 1.0].copy()
non_runners = ft30[ft30['mfe'] < 1.0].copy()
w(f"Runners (MFE >= 1.0): **{len(runners)}** ({len(runners)/len(ft30)*100:.1f}%)")
w(f"Non-runners: {len(non_runners)}")
w("")

if len(runners) > 0:
    w("### Runner profile vs Non-runner:")
    w("")

    # Numeric columns to compare
    for col in ['vol', 'adx', 'body', 'ramp', 'range_atr']:
        runners[col] = pd.to_numeric(runners[col], errors='coerce')
        non_runners[col] = pd.to_numeric(non_runners[col], errors='coerce')
        r_med = runners[col].median()
        nr_med = non_runners[col].median()
        r_avg = runners[col].mean()
        nr_avg = non_runners[col].mean()
        w(f"  {col:12s}: runner avg={r_avg:.1f} med={r_med:.1f} | non-runner avg={nr_avg:.1f} med={nr_med:.1f} | gap={r_avg - nr_avg:+.1f}")

    w("")

    # Categorical columns
    for col in ['direction', 'ema', 'vwap', 'type']:
        w(f"  **{col}** distribution:")
        r_dist = runners[col].value_counts(normalize=True).sort_index()
        nr_dist = non_runners[col].value_counts(normalize=True).sort_index()
        all_vals = sorted(set(r_dist.index) | set(nr_dist.index))
        for v in all_vals:
            r_pct = r_dist.get(v, 0) * 100
            nr_pct = nr_dist.get(v, 0) * 100
            w(f"    {v:12s}: runner={r_pct:.0f}% | non-runner={nr_pct:.0f}% | gap={r_pct - nr_pct:+.0f}%")
        w("")

    # Boolean columns
    for col in ['is_bigmove', 'is_bodywarn']:
        r_pct = runners[col].astype(str).str.lower().isin(['true', '1']).mean() * 100
        nr_pct = non_runners[col].astype(str).str.lower().isin(['true', '1']).mean() * 100
        w(f"  {col:16s}: runner={r_pct:.0f}% | non-runner={nr_pct:.0f}% | gap={r_pct - nr_pct:+.0f}%")
    w("")

    # Time distribution
    w("  **Time distribution:**")
    runners['hour'] = runners['time_min'] // 60
    non_runners['hour'] = non_runners['time_min'] // 60
    for h in range(10, 16):
        r_pct = (runners['hour'] == h).mean() * 100
        nr_pct = (non_runners['hour'] == h).mean() * 100
        w(f"    {h}:00-{h}:59: runner={r_pct:.0f}% | non-runner={nr_pct:.0f}% | gap={r_pct - nr_pct:+.0f}%")
    w("")

    # Symbol distribution
    w("  **Symbol runner rate** (signals with MFE >= 1.0):")
    sym_total = ft30.groupby('symbol').size()
    sym_runners = runners.groupby('symbol').size()
    sym_rate = (sym_runners / sym_total * 100).sort_values(ascending=False)
    for sym in sym_rate.index:
        w(f"    {sym:6s}: {sym_rate[sym]:.0f}% ({sym_runners.get(sym, 0)}/{sym_total.get(sym, 0)})")

w("")

# ════════════════════════════════════════════════════════════════════════
# 6. WORST VS BEST COMPARISON (top 20% vs bottom 20% MFE after 9:50)
# ════════════════════════════════════════════════════════════════════════
w("## 6. Worst vs Best Comparison (Top 20% vs Bottom 20% MFE after 9:50)")
w("")

ft30_sorted = ft30.sort_values('mfe')
n = len(ft30_sorted)
bottom20 = ft30_sorted.head(int(n * 0.2)).copy()
top20 = ft30_sorted.tail(int(n * 0.2)).copy()

w(f"Bottom 20% (worst): n={len(bottom20)}, MFE range [{bottom20['mfe'].min():.3f}, {bottom20['mfe'].max():.3f}]")
w(f"Top 20% (best): n={len(top20)}, MFE range [{top20['mfe'].min():.3f}, {top20['mfe'].max():.3f}]")
w("")

w("### Feature comparison:")
w("")
w(f"{'Feature':16s} | {'Best (top 20%)':>20s} | {'Worst (bottom 20%)':>20s} | {'Gap':>10s}")
w(f"{'-'*16}-+-{'-'*20}-+-{'-'*20}-+-{'-'*10}")

for col in ['vol', 'adx', 'body', 'ramp', 'range_atr']:
    top20[col] = pd.to_numeric(top20[col], errors='coerce')
    bottom20[col] = pd.to_numeric(bottom20[col], errors='coerce')
    t_avg = top20[col].mean()
    b_avg = bottom20[col].mean()
    gap = t_avg - b_avg
    w(f"{col:16s} | {t_avg:20.2f} | {b_avg:20.2f} | {gap:+10.2f}")

w("")
w("### Categorical differences:")
w("")
for col in ['direction', 'ema', 'vwap', 'type']:
    w(f"**{col}:**")
    t_dist = top20[col].value_counts(normalize=True).sort_index()
    b_dist = bottom20[col].value_counts(normalize=True).sort_index()
    all_vals = sorted(set(t_dist.index) | set(b_dist.index))
    for v in all_vals:
        t_pct = t_dist.get(v, 0) * 100
        b_pct = b_dist.get(v, 0) * 100
        w(f"  {v:12s}: best={t_pct:.0f}% | worst={b_pct:.0f}% | gap={t_pct - b_pct:+.0f}%")
    w("")

# Boolean
for col in ['is_bigmove', 'is_bodywarn']:
    t_pct = top20[col].astype(str).str.lower().isin(['true', '1']).mean() * 100
    b_pct = bottom20[col].astype(str).str.lower().isin(['true', '1']).mean() * 100
    w(f"{col:16s}: best={t_pct:.0f}% | worst={b_pct:.0f}% | gap={t_pct - b_pct:+.0f}%")
w("")

# Time
w("**Time distribution:**")
top20['hour'] = top20['time_min'] // 60
bottom20['hour'] = bottom20['time_min'] // 60
for h in range(10, 16):
    t_pct = (top20['hour'] == h).mean() * 100
    b_pct = (bottom20['hour'] == h).mean() * 100
    w(f"  {h}:00-{h}:59: best={t_pct:.0f}% | worst={b_pct:.0f}% | gap={t_pct - b_pct:+.0f}%")
w("")

# Symbols
w("**Symbol distribution:**")
t_syms = top20['symbol'].value_counts(normalize=True).sort_values(ascending=False)
b_syms = bottom20['symbol'].value_counts(normalize=True).sort_values(ascending=False)
all_syms = sorted(set(t_syms.index) | set(b_syms.index))
for sym in all_syms:
    t_pct = t_syms.get(sym, 0) * 100
    b_pct = b_syms.get(sym, 0) * 100
    w(f"  {sym:6s}: best={t_pct:.0f}% | worst={b_pct:.0f}% | gap={t_pct - b_pct:+.0f}%")

w("")

# ════════════════════════════════════════════════════════════════════════
# 7. SUMMARY: KEY TAKEAWAYS
# ════════════════════════════════════════════════════════════════════════
w("## 7. Key Takeaways")
w("")

# Compute key findings dynamically
if len(runners) > 0 and len(non_runners) > 0:
    # Top differentiators
    diffs = {}
    for col in ['vol', 'adx', 'body', 'ramp', 'range_atr']:
        r_avg = runners[col].mean()
        nr_avg = non_runners[col].mean()
        if nr_avg != 0:
            diffs[col] = (r_avg - nr_avg) / abs(nr_avg) * 100
        else:
            diffs[col] = 0

    sorted_diffs = sorted(diffs.items(), key=lambda x: abs(x[1]), reverse=True)
    w("**Top numeric differentiators (runner vs non-runner, % difference):**")
    for col, pct in sorted_diffs:
        w(f"  - {col}: {pct:+.0f}%")
    w("")

# Runner rate by time bucket
w("**Runner rate by hour (after 9:50):**")
ft30['hour'] = ft30['time_min'] // 60
for h in range(10, 16):
    bucket = ft30[ft30['hour'] == h]
    if len(bucket) > 0:
        rate = (bucket['mfe'] >= 1.0).mean() * 100
        avg_mfe = bucket['mfe'].mean()
        w(f"  {h}:00-{h}:59: {rate:.0f}% runner rate (n={len(bucket)}, avg MFE={avg_mfe:.3f})")
w("")

# Best combo: high vol + big bar + EMA aligned
w("**Combo filters (after 9:50, 30-min):**")
ft30_num = ft30.copy()
for c in ['vol', 'range_atr', 'adx', 'body', 'ramp']:
    ft30_num[c] = pd.to_numeric(ft30_num[c], errors='coerce')

combos = [
    ("vol>=5 + range_atr>=1.5", (ft30_num['vol'] >= 5) & (ft30_num['range_atr'] >= 1.5)),
    ("vol>=5 + ema aligned", (ft30_num['vol'] >= 5) & (
        ((ft30_num['direction'] == 'bull') & (ft30_num['ema'] == 'bull')) |
        ((ft30_num['direction'] == 'bear') & (ft30_num['ema'] == 'bear'))
    )),
    ("range_atr>=1.5 + ema aligned", (ft30_num['range_atr'] >= 1.5) & (
        ((ft30_num['direction'] == 'bull') & (ft30_num['ema'] == 'bull')) |
        ((ft30_num['direction'] == 'bear') & (ft30_num['ema'] == 'bear'))
    )),
    ("vol>=5 + range_atr>=1.5 + ema aligned",
        (ft30_num['vol'] >= 5) & (ft30_num['range_atr'] >= 1.5) & (
        ((ft30_num['direction'] == 'bull') & (ft30_num['ema'] == 'bull')) |
        ((ft30_num['direction'] == 'bear') & (ft30_num['ema'] == 'bear'))
    )),
    ("big bar + ema + vwap aligned",
        (ft30_num['range_atr'] >= 1.5) & (
        ((ft30_num['direction'] == 'bull') & (ft30_num['ema'] == 'bull') & (ft30_num['vwap'] == 'above')) |
        ((ft30_num['direction'] == 'bear') & (ft30_num['ema'] == 'bear') & (ft30_num['vwap'] == 'below'))
    )),
]

for label, mask in combos:
    sub = ft30_num[mask]
    if len(sub) > 0:
        rate = (sub['mfe'] >= 1.0).mean() * 100
        avg_mfe = sub['mfe'].mean()
        avg_mae = sub['mae'].mean()
        w(f"  {label}: n={len(sub)}, runner={rate:.0f}%, MFE={avg_mfe:.3f}, MAE={avg_mae:.3f}")
    else:
        w(f"  {label}: n=0")
w("")

# ── Write output ───────────────────────────────────────────────────────
OUT.write_text('\n'.join(lines))
print(f"\nWritten to {OUT}")
