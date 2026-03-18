"""
TSLA Big-Move Comparison — 2x 5m-ATR vs 0.5x Daily ATR
Uses the pre-computed tsla-bigmove-data.csv and adds daily ATR reference.
"""
import os, sys, numpy as np, pandas as pd
from datetime import timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(BASE))), "trading_bot", "cache")
OUT_MD = os.path.join(BASE, "tsla-bigmove-comparison.md")

# ── Load pre-computed data ───────────────────────────────────
df = pd.read_csv(os.path.join(BASE, "tsla-bigmove-data.csv"))
print(f"Loaded {len(df)} pre-computed big moves", file=sys.stderr)

# ── Add daily ATR reference ──────────────────────────────────
dfD = pd.read_parquet(os.path.join(CACHE, "bars/tsla_1_day_ib.parquet"))
dfD['date'] = pd.to_datetime(dfD['date'])
dfD['daily_range'] = dfD['high'] - dfD['low']
# Compute daily ATR(14)
prev_c = dfD['close'].shift(1)
tr = pd.concat([dfD['high'] - dfD['low'], (dfD['high'] - prev_c).abs(), (dfD['low'] - prev_c).abs()], axis=1).max(axis=1)
dfD['daily_atr'] = tr.ewm(alpha=1/14, adjust=False).mean()
dfD['date_str'] = dfD['date'].dt.strftime('%Y-%m-%d')
daily_atr_map = dfD.set_index('date_str')['daily_atr'].shift(1).to_dict()  # use PRIOR day's ATR

# Map daily ATR to each move
df['daily_atr'] = df['date'].map(daily_atr_map)
df['range_daily_atr'] = (df['high'] - df['low']) / df['daily_atr'].replace(0, np.nan)

# Fix direction display
df['dir_label'] = df['direction'].apply(lambda d: 'Bull' if d == 'bull' else 'Bear')

# ── Define cohorts ───────────────────────────────────────────
cohorts = {
    '1x 5m-ATR (baseline)': df,
    '2x 5m-ATR': df[df['range_atr'] >= 2.0].copy(),
    '0.5x Daily ATR': df[df['range_daily_atr'] >= 0.5].copy(),
    '0.75x Daily ATR': df[df['range_daily_atr'] >= 0.75].copy(),
}

# ── Report ───────────────────────────────────────────────────
lines = []
lines.append("# TSLA Big-Move Comparison — Threshold Analysis")
lines.append(f"Base dataset: {len(df)} moves with range >= 1x 5m-ATR(14)")
lines.append("")

# Cohort summary
lines.append("## Cohort Overview")
lines.append("")
lines.append("| Cohort | n | Runners | Fakeouts | Middle | Runner% | Fakeout% | Avg MFE | Avg MAE | Per Day |")
lines.append("|--------|---|---------|----------|--------|---------|----------|---------|---------|---------|")
for name, sub in cohorts.items():
    n = len(sub)
    nr = (sub['outcome'] == 'runner').sum()
    nf = (sub['outcome'] == 'fakeout').sum()
    nm = n - nr - nf
    days = sub['date'].nunique()
    per_day = n / max(days, 1)
    lines.append(f"| {name} | {n} | {nr} | {nf} | {nm} | {nr/n*100:.0f}% | {nf/n*100:.0f}% | {sub['mfe'].mean():.2f} | {sub['mae'].mean():.2f} | {per_day:.1f} |")

lines.append("")

# ── Detailed analysis for each tighter cohort ────────────────
for cohort_name in ['2x 5m-ATR', '0.5x Daily ATR']:
    sub = cohorts[cohort_name]
    n = len(sub)
    if n < 10:
        continue

    nr = (sub['outcome'] == 'runner').sum()
    nf = (sub['outcome'] == 'fakeout').sum()

    lines.append(f"---")
    lines.append(f"## {cohort_name} (n={n})")
    lines.append("")

    # Overall stats
    lines.append(f"### Stats — Runner vs Fakeout")
    lines.append("")
    lines.append(f"| Metric | All (n={n}) | Runners (n={nr}) | Fakeouts (n={nf}) | Gap |")
    lines.append("|--------|-----|---------|----------|-----|")

    for label, col in [
        ('Avg MFE (ATR)', 'mfe'), ('Avg MAE (ATR)', 'mae'), ('Avg 5m P&L', 'pnl_5m'),
        ('Avg Body %', 'body_pct'), ('Avg Range/5m-ATR', 'range_atr'), ('Avg Vol Ratio', 'vol_ratio'),
        ('Avg ADX', 'adx'), ('Avg VWAP Dist', 'vwap_dist'),
        ('Pre: Vol Ramp', 'pre_vol_ramp'), ('Pre: Dir Pressure', 'pre_dir_pressure'),
        ('Pre: Compression', 'pre_compression'),
        ('15m: Range/ATR', 'f15m_range_atr'), ('15m: Position', 'f15m_position'),
        ('Day: Gap/ATR', 'gap_atr'), ('Day: Range Position', 'day_range_pos'),
    ]:
        if col not in sub.columns:
            continue
        a = sub[col].mean()
        r = sub.loc[sub['outcome']=='runner', col].mean() if nr > 0 else 0
        f = sub.loc[sub['outcome']=='fakeout', col].mean() if nf > 0 else 0
        gap = r - f if (nr > 0 and nf > 0) else 0
        lines.append(f"| {label} | {a:.2f} | {r:.2f} | {f:.2f} | {gap:+.2f} |")

    lines.append("")

    # Feature rates
    lines.append(f"### Feature Rates")
    lines.append("")
    lines.append(f"| Feature | All | Runners | Fakeouts | Gap |")
    lines.append("|---------|-----|---------|----------|-----|")

    for label, col in [
        ('EMA aligned', 'ema_aligned'), ('VWAP aligned', 'vwap_aligned'),
        ('Above EMA9', 'above_ema9'), ('Above EMA20', 'above_ema20'),
        ('15m trend aligned', 'f15m_trend_aligned'), ('15m breakout', 'f15m_breakout'),
    ]:
        if col not in sub.columns:
            continue
        a = sub[col].mean() * 100
        r = sub.loc[sub['outcome']=='runner', col].mean() * 100 if nr > 0 else 0
        f = sub.loc[sub['outcome']=='fakeout', col].mean() * 100 if nf > 0 else 0
        gap = r - f if (nr > 0 and nf > 0) else 0
        lines.append(f"| {label} | {a:.0f}% | {r:.0f}% | {f:.0f}% | {gap:+.0f}% |")

    # Direction split
    bull_all = (sub['direction'] == 'bull').mean() * 100
    bull_r = (sub.loc[sub['outcome']=='runner', 'direction'] == 'bull').mean() * 100 if nr > 0 else 0
    bull_f = (sub.loc[sub['outcome']=='fakeout', 'direction'] == 'bull').mean() * 100 if nf > 0 else 0
    lines.append(f"| Bull direction | {bull_all:.0f}% | {bull_r:.0f}% | {bull_f:.0f}% | {bull_r - bull_f:+.0f}% |")

    if 'pnl_5m' in sub.columns:
        p5_all = (sub['pnl_5m'] > 0).mean() * 100
        p5_r = (sub.loc[sub['outcome']=='runner', 'pnl_5m'] > 0).mean() * 100 if nr > 0 else 0
        p5_f = (sub.loc[sub['outcome']=='fakeout', 'pnl_5m'] > 0).mean() * 100 if nf > 0 else 0
        lines.append(f"| 5min P&L positive | {p5_all:.0f}% | {p5_r:.0f}% | {p5_f:.0f}% | {p5_r - p5_f:+.0f}% |")

    lines.append("")

    # Time buckets
    lines.append(f"### By Time of Day")
    lines.append("")
    lines.append("| Time | n | Runners | Fakeouts | Runner% | Avg MFE |")
    lines.append("|------|---|---------|----------|---------|---------|")
    for bucket in ['09:30-10', '10-11', '11-12', '12-13', '13-14', '14-15', '15-16']:
        bsub = sub[sub['time_bucket'] == bucket]
        if len(bsub) < 3:
            continue
        bnr = (bsub['outcome'] == 'runner').sum()
        bnf = (bsub['outcome'] == 'fakeout').sum()
        rr = bnr / len(bsub) * 100
        lines.append(f"| {bucket} | {len(bsub)} | {bnr} | {bnf} | {rr:.0f}% | {bsub['mfe'].mean():.2f} |")

    lines.append("")

    # Pre-move vol ramp
    lines.append(f"### Pre-Move Volume Ramp")
    lines.append("")
    lines.append("| Vol Ramp | n | Runner% | Fakeout% | Avg MFE |")
    lines.append("|----------|---|---------|----------|---------|")
    if 'pre_vol_ramp' in sub.columns:
        vr = sub.dropna(subset=['pre_vol_ramp'])
        for lo, hi, label in [(0, 0.5, '<0.5 (drying)'), (0.5, 1.0, '0.5-1 (steady)'), (1.0, 2.0, '1-2x (ramping)'), (2.0, 999, '>2x (surging)')]:
            vsub = vr[(vr['pre_vol_ramp'] >= lo) & (vr['pre_vol_ramp'] < hi)]
            if len(vsub) < 3:
                continue
            rr = (vsub['outcome'] == 'runner').mean() * 100
            fr = (vsub['outcome'] == 'fakeout').mean() * 100
            lines.append(f"| {label} | {len(vsub)} | {rr:.0f}% | {fr:.0f}% | {vsub['mfe'].mean():.2f} |")

    lines.append("")

    # Gap context
    lines.append(f"### Gap Context")
    lines.append("")
    lines.append("| Gap | n | Runner% | Fakeout% | Avg MFE |")
    lines.append("|-----|---|---------|----------|---------|")
    if 'gap_atr' in sub.columns:
        gdf = sub.dropna(subset=['gap_atr'])
        for lo, hi, label in [(-99, -0.3, 'Gap Down'), (-0.3, 0.3, 'Flat'), (0.3, 99, 'Gap Up')]:
            gsub = gdf[(gdf['gap_atr'] >= lo) & (gdf['gap_atr'] < hi)]
            if len(gsub) < 3:
                continue
            rr = (gsub['outcome'] == 'runner').mean() * 100
            fr = (gsub['outcome'] == 'fakeout').mean() * 100
            lines.append(f"| {label} | {len(gsub)} | {rr:.0f}% | {fr:.0f}% | {gsub['mfe'].mean():.2f} |")

    lines.append("")

    # Top 10 runners
    lines.append(f"### Top 10 Runners")
    lines.append("")
    lines.append("| Date | Time | Dir | Range | Body | Vol | ADX | Pre VolRamp | 5mPnL | MFE | MAE |")
    lines.append("|------|------|-----|-------|------|-----|-----|-------------|-------|-----|-----|")
    top = sub.nlargest(10, 'mfe')
    for _, r in top.iterrows():
        d = 'Bull' if r['direction'] == 'bull' else 'Bear'
        lines.append(f"| {r['date']} | {r['time']} | {d} | {r['range_atr']:.1f} | {r['body_pct']:.0f}% | {r['vol_ratio']:.1f}x | {r['adx']:.0f} | {r.get('pre_vol_ramp', 0):.1f}x | {r.get('pnl_5m', 0):.2f} | {r['mfe']:.2f} | {r['mae']:.2f} |")

    lines.append("")

# ── Cross-cohort feature ranking ─────────────────────────────
lines.append("---")
lines.append("## Feature Ranking — Which Predictors Get STRONGER with Tighter Threshold?")
lines.append("")
lines.append("Comparing the Runner-Fakeout gap across cohorts (bigger gap = more useful predictor):")
lines.append("")
lines.append("| Feature | 1x 5m-ATR gap | 2x 5m-ATR gap | 0.5x Daily gap | Trend |")
lines.append("|---------|---------------|---------------|----------------|-------|")

for label, col, is_pct in [
    ('5min P&L positive', 'pnl_5m', True),
    ('Pre: Vol Ramp', 'pre_vol_ramp', False),
    ('Vol Ratio', 'vol_ratio', False),
    ('VWAP Dist', 'vwap_dist', False),
    ('Gap/ATR', 'gap_atr', False),
    ('EMA aligned', 'ema_aligned', True),
    ('Body %', 'body_pct', False),
    ('ADX', 'adx', False),
]:
    gaps = []
    for cname in ['1x 5m-ATR (baseline)', '2x 5m-ATR', '0.5x Daily ATR']:
        c = cohorts[cname]
        nr = (c['outcome'] == 'runner').sum()
        nf = (c['outcome'] == 'fakeout').sum()
        if col == 'pnl_5m' and is_pct:
            r = (c.loc[c['outcome']=='runner', col] > 0).mean() * 100 if nr > 0 else 0
            f = (c.loc[c['outcome']=='fakeout', col] > 0).mean() * 100 if nf > 0 else 0
        elif is_pct:
            r = c.loc[c['outcome']=='runner', col].mean() * 100 if nr > 0 else 0
            f = c.loc[c['outcome']=='fakeout', col].mean() * 100 if nf > 0 else 0
        else:
            r = c.loc[c['outcome']=='runner', col].mean() if nr > 0 else 0
            f = c.loc[c['outcome']=='fakeout', col].mean() if nf > 0 else 0
        gaps.append(r - f)

    trend = "↑ stronger" if abs(gaps[2]) > abs(gaps[0]) * 1.2 else ("↓ weaker" if abs(gaps[2]) < abs(gaps[0]) * 0.8 else "→ stable")
    fmt = ".0f" if is_pct else ".2f"
    lines.append(f"| {label} | {gaps[0]:+{fmt}} | {gaps[1]:+{fmt}} | {gaps[2]:+{fmt}} | {trend} |")

lines.append("")

with open(OUT_MD, 'w') as f:
    f.write('\n'.join(lines))
print(f"\nSaved comparison to {OUT_MD}", file=sys.stderr)
