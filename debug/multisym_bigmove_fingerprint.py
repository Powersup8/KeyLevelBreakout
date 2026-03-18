"""
Multi-Symbol Big-Move Fingerprint — Tests TSLA findings across all 13 symbols.
Threshold: 2x 5m-ATR(14). Features: pre-move vol ramp, gap context, time, ADX, etc.
Outputs: CSV + comparison report.
"""
import os, sys, numpy as np, pandas as pd
from datetime import timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(BASE))), "trading_bot", "cache")
OUT_CSV = os.path.join(BASE, "multisym-bigmove-data.csv")
OUT_MD = os.path.join(BASE, "multisym-bigmove-fingerprint.md")

SYMBOLS = ["SPY", "AAPL", "AMD", "AMZN", "GLD", "GOOGL", "META", "MSFT", "NVDA", "QQQ", "SLV", "TSLA", "TSM"]
# Use same window where 5s data exists for most symbols
START = "2025-12-15"
END = "2026-03-03"

def compute_adx(h, l, c, period=14):
    prev_h, prev_l, prev_c = h.shift(1), l.shift(1), c.shift(1)
    tr = pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    plus_dm = np.where((h - prev_h > prev_l - l) & (h - prev_h > 0), h - prev_h, 0)
    minus_dm = np.where((prev_l - l > h - prev_h) & (prev_l - l > 0), prev_l - l, 0)
    atr = pd.Series(tr, index=h.index).ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=h.index).ewm(alpha=1/period, adjust=False).mean() / atr
    minus_di = 100 * pd.Series(minus_dm, index=h.index).ewm(alpha=1/period, adjust=False).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1/period, adjust=False).mean().fillna(0), atr

def load_parquet(filename):
    fpath = os.path.join(CACHE, filename)
    if not os.path.exists(fpath):
        return None
    df = pd.read_parquet(fpath)
    df['date'] = pd.to_datetime(df['date'])
    if df['date'].dt.tz is None:
        df['date'] = df['date'].dt.tz_localize('US/Eastern')
    else:
        df['date'] = df['date'].dt.tz_convert('US/Eastern')
    return df.set_index('date').sort_index()

def process_symbol(sym):
    """Process one symbol: find 2x ATR big moves, compute features, return list of dicts."""
    print(f"  {sym}: loading...", file=sys.stderr)
    s = sym.lower()
    df5m = load_parquet(f"bars/{s}_5_mins_ib.parquet")
    df1m = load_parquet(f"bars/{s}_1_min_ib.parquet")
    df5s = load_parquet(f"bars_highres/5sec/{s}_5_secs_ib.parquet")
    if df5m is None:
        print(f"  {sym}: no 5m data, skipping", file=sys.stderr)
        return []

    # Warmup period for indicators
    warmup_start = pd.Timestamp(START, tz='US/Eastern') - timedelta(days=60)
    df5m = df5m.loc[warmup_start:]

    # 5m indicators
    df5m['adx'], df5m['atr14'] = compute_adx(df5m['high'], df5m['low'], df5m['close'], 14)
    df5m['ema20'] = df5m['close'].ewm(span=20, adjust=False).mean()
    df5m['ema50'] = df5m['close'].ewm(span=50, adjust=False).mean()
    df5m['vol_sma20'] = df5m['volume'].rolling(20).mean()
    df5m['vol_ratio'] = df5m['volume'] / df5m['vol_sma20'].replace(0, np.nan)
    # VWAP
    df5m['day'] = df5m.index.date
    df5m['cum_vol'] = df5m.groupby('day')['volume'].cumsum()
    df5m['cum_vp'] = df5m.groupby('day').apply(
        lambda g: (g['close'] * g['volume']).cumsum(), include_groups=False
    ).droplevel(0)
    df5m['vwap'] = df5m['cum_vp'] / df5m['cum_vol'].replace(0, np.nan)
    # Range/body
    rng = df5m['high'] - df5m['low']
    df5m['range_atr'] = rng / df5m['atr14'].replace(0, np.nan)
    df5m['body_pct'] = (np.abs(df5m['close'] - df5m['open']) / rng.replace(0, np.nan) * 100).fillna(0)
    df5m['direction'] = np.where(df5m['close'] > df5m['open'], 'bull', 'bear')

    # Trim to analysis window, RTH only
    window = df5m.loc[START:END].copy()
    window = window[(window.index.hour >= 9) & (window.index.hour < 16)]
    window = window[~((window.index.hour == 9) & (window.index.minute < 30))]

    # 2x ATR filter
    big = window[window['range_atr'] >= 2.0].copy()
    print(f"  {sym}: {len(big)} moves >= 2x ATR", file=sys.stderr)
    if len(big) == 0:
        return []

    # Daily open for gap calc (precompute per day)
    day_opens = {}
    for day in window['day'].unique():
        day_bars = window[(window['day'] == day) & (window.index.hour == 9) & (window.index.minute == 30)]
        if len(day_bars) > 0:
            day_opens[day] = day_bars.iloc[0]['open']

    # Precompute prior-day close
    daily_closes = window.groupby('day')['close'].last().shift(1).to_dict()

    rows = []
    for ts, bar in big.iterrows():
        atr = bar['atr14']
        if atr <= 0 or pd.isna(atr):
            continue
        direction = bar['direction']
        day = ts.date()

        feat = {
            'symbol': sym,
            'date': ts.strftime('%Y-%m-%d'),
            'time': ts.strftime('%H:%M'),
            'direction': direction,
            'range_atr': round(bar['range_atr'], 3),
            'body_pct': round(bar['body_pct'], 1),
            'vol_ratio': round(bar['vol_ratio'], 2) if not pd.isna(bar['vol_ratio']) else 0,
            'adx': round(bar['adx'], 1),
            'atr': round(atr, 4),
            'ema_aligned': 1 if (bar['ema20'] > bar['ema50']) == (direction == 'bull') else 0,
            'vwap_aligned': 1 if (bar['close'] > bar['vwap']) == (direction == 'bull') else 0,
            'vwap_dist': round((bar['close'] - bar['vwap']) / atr, 3) if not pd.isna(bar['vwap']) else 0,
            'time_bucket': (
                '09:30-10' if ts.hour == 9 else
                '10-11' if ts.hour == 10 else
                '11-12' if ts.hour == 11 else
                '12-14' if ts.hour in (12, 13) else '14-16'
            ),
        }

        # 1m pre-move context (10 bars)
        if df1m is not None:
            pre1m = df1m.loc[ts - timedelta(minutes=10):ts - timedelta(seconds=1)]
            if len(pre1m) >= 5:
                # Vol ramp: last 3 / first 3
                first3 = pre1m['volume'].iloc[:3].mean()
                last3 = pre1m['volume'].iloc[-3:].mean()
                feat['pre_vol_ramp'] = round(last3 / max(first3, 1), 2)
                # Compression
                feat['pre_compression'] = round((pre1m['high'].max() - pre1m['low'].min()) / atr, 3)
                # Dir pressure
                if direction == 'bull':
                    feat['pre_dir_pressure'] = round((pre1m['close'] > pre1m['open']).mean() * 100, 1)
                else:
                    feat['pre_dir_pressure'] = round((pre1m['close'] < pre1m['open']).mean() * 100, 1)
            else:
                feat['pre_vol_ramp'] = np.nan
                feat['pre_compression'] = np.nan
                feat['pre_dir_pressure'] = np.nan
        else:
            feat['pre_vol_ramp'] = np.nan
            feat['pre_compression'] = np.nan
            feat['pre_dir_pressure'] = np.nan

        # Gap context
        prev_close = daily_closes.get(day)
        day_open = day_opens.get(day)
        if prev_close and day_open and atr > 0:
            feat['gap_atr'] = round((day_open - prev_close) / atr, 3)
        else:
            feat['gap_atr'] = np.nan

        # 5s MFE/MAE
        if df5s is not None:
            entry_price = bar['close']
            entry_time = ts + timedelta(minutes=5)
            w5s = df5s.loc[entry_time + timedelta(seconds=5):entry_time + timedelta(minutes=30)]
            if len(w5s) > 0:
                if direction == 'bull':
                    feat['mfe'] = round((w5s['high'].max() - entry_price) / atr, 3)
                    feat['mae'] = round((w5s['low'].min() - entry_price) / atr, 3)
                else:
                    feat['mfe'] = round((entry_price - w5s['low'].min()) / atr, 3)
                    feat['mae'] = round((entry_price - w5s['high'].max()) / atr, 3)
                # 5-min check
                w5 = df5s.loc[entry_time + timedelta(seconds=5):entry_time + timedelta(minutes=5)]
                if len(w5) > 0:
                    p5 = w5.iloc[-1]['close']
                    feat['pnl_5m'] = round(((p5 - entry_price) / atr if direction == 'bull'
                                           else (entry_price - p5) / atr), 3)
                else:
                    feat['pnl_5m'] = np.nan
            else:
                feat['mfe'] = np.nan
                feat['mae'] = np.nan
                feat['pnl_5m'] = np.nan
        else:
            feat['mfe'] = np.nan
            feat['mae'] = np.nan
            feat['pnl_5m'] = np.nan

        rows.append(feat)

    print(f"  {sym}: {len(rows)} fingerprinted", file=sys.stderr)
    return rows

# ── Process all symbols ──────────────────────────────────────
print(f"Multi-symbol big-move fingerprint ({START} to {END})...", file=sys.stderr)
all_rows = []
for sym in SYMBOLS:
    all_rows.extend(process_symbol(sym))

df = pd.DataFrame(all_rows)
df['outcome'] = 'middle'
df.loc[df['mfe'] > 0.5, 'outcome'] = 'runner'
df.loc[(df['mfe'] < 0.1) & (df['mae'] < -0.3), 'outcome'] = 'fakeout'
df.to_csv(OUT_CSV, index=False)
print(f"\nTotal: {len(df)} moves across {df['symbol'].nunique()} symbols → {OUT_CSV}", file=sys.stderr)

# ── Generate comparison report ───────────────────────────────
lines = []
lines.append("# Multi-Symbol Big-Move Fingerprint (2x 5m-ATR)")
lines.append(f"Period: {START} to {END} | Symbols: {len(SYMBOLS)} | Total moves: {len(df)}")
lines.append("")

# Per-symbol summary
lines.append("## Per-Symbol Overview")
lines.append("")
lines.append("| Symbol | n | Runners | Fakeouts | Runner% | Avg MFE | Avg Vol | Avg PreVolRamp | Per Day |")
lines.append("|--------|---|---------|----------|---------|---------|---------|----------------|---------|")
for sym in SYMBOLS:
    s = df[df['symbol'] == sym]
    if len(s) == 0:
        lines.append(f"| {sym} | 0 | — | — | — | — | — | — | — |")
        continue
    nr = (s['outcome'] == 'runner').sum()
    nf = (s['outcome'] == 'fakeout').sum()
    days = s['date'].nunique()
    lines.append(f"| {sym} | {len(s)} | {nr} | {nf} | {nr/len(s)*100:.0f}% | {s['mfe'].mean():.2f} | {s['vol_ratio'].mean():.1f}x | {s['pre_vol_ramp'].mean():.1f}x | {len(s)/max(days,1):.1f} |")

# Totals row
nr_all = (df['outcome'] == 'runner').sum()
nf_all = (df['outcome'] == 'fakeout').sum()
days_all = df['date'].nunique()
lines.append(f"| **ALL** | **{len(df)}** | **{nr_all}** | **{nf_all}** | **{nr_all/len(df)*100:.0f}%** | **{df['mfe'].mean():.2f}** | **{df['vol_ratio'].mean():.1f}x** | **{df['pre_vol_ramp'].mean():.1f}x** | **{len(df)/max(days_all,1):.1f}** |")
lines.append("")

# ── TSLA findings cross-validated ────────────────────────────
lines.append("## Cross-Validation: Do TSLA Findings Generalize?")
lines.append("")

# Helper: compute runner-fakeout gap
def gap(sub, col, is_pct=False):
    nr = (sub['outcome'] == 'runner').sum()
    nf = (sub['outcome'] == 'fakeout').sum()
    if nr == 0 or nf == 0:
        return np.nan
    if is_pct:
        r = sub.loc[sub['outcome']=='runner', col].mean() * 100
        f = sub.loc[sub['outcome']=='fakeout', col].mean() * 100
    else:
        r = sub.loc[sub['outcome']=='runner', col].mean()
        f = sub.loc[sub['outcome']=='fakeout', col].mean()
    return r - f

# Finding 1: Pre-move vol ramp
lines.append("### Finding 1: Pre-Move Volume Ramp")
lines.append("*TSLA: runners 7.6x ramp vs fakeouts 1.07x (+6.55 gap)*")
lines.append("")
lines.append("| Symbol | Runner avg | Fakeout avg | Gap | Validates? |")
lines.append("|--------|-----------|------------|-----|-----------|")
for sym in SYMBOLS:
    s = df[df['symbol'] == sym]
    nr = (s['outcome'] == 'runner').sum()
    nf = (s['outcome'] == 'fakeout').sum()
    if nr == 0:
        continue
    r = s.loc[s['outcome']=='runner', 'pre_vol_ramp'].mean()
    f = s.loc[s['outcome']=='fakeout', 'pre_vol_ramp'].mean() if nf > 0 else np.nan
    g = r - f if nf > 0 else np.nan
    valid = "YES" if (not pd.isna(g) and g > 1.0) else ("n/a" if pd.isna(g) else "NO")
    lines.append(f"| {sym} | {r:.1f}x | {f:.1f}x | {g:+.1f} | {valid} |" if not pd.isna(f) else f"| {sym} | {r:.1f}x | — | — | n/a (no fakeouts) |")
lines.append("")

# Finding 2: ADX
lines.append("### Finding 2: ADX (runners higher)")
lines.append("*TSLA: runners 28.4 vs fakeouts 22.6 (+5.8 gap)*")
lines.append("")
lines.append("| Symbol | Runner avg | Fakeout avg | Gap | Validates? |")
lines.append("|--------|-----------|------------|-----|-----------|")
for sym in SYMBOLS:
    s = df[df['symbol'] == sym]
    nr = (s['outcome'] == 'runner').sum()
    nf = (s['outcome'] == 'fakeout').sum()
    if nr == 0:
        continue
    r = s.loc[s['outcome']=='runner', 'adx'].mean()
    f = s.loc[s['outcome']=='fakeout', 'adx'].mean() if nf > 0 else np.nan
    g = r - f if nf > 0 else np.nan
    valid = "YES" if (not pd.isna(g) and g > 2.0) else ("n/a" if pd.isna(g) else "NO")
    lines.append(f"| {sym} | {r:.1f} | {f:.1f} | {g:+.1f} | {valid} |" if not pd.isna(f) else f"| {sym} | {r:.1f} | — | — | n/a |")
lines.append("")

# Finding 3: 5-min P&L positive
lines.append("### Finding 3: 5-Min P&L Positive (strongest predictor)")
lines.append("*TSLA: 66% runners positive at 5min vs 0% fakeouts*")
lines.append("")
lines.append("| Symbol | Runner 5m+ | Fakeout 5m+ | Gap | Validates? |")
lines.append("|--------|-----------|------------|-----|-----------|")
for sym in SYMBOLS:
    s = df[df['symbol'] == sym].dropna(subset=['pnl_5m'])
    nr = (s['outcome'] == 'runner').sum()
    nf = (s['outcome'] == 'fakeout').sum()
    if nr == 0:
        continue
    r = (s.loc[s['outcome']=='runner', 'pnl_5m'] > 0).mean() * 100
    f = (s.loc[s['outcome']=='fakeout', 'pnl_5m'] > 0).mean() * 100 if nf > 0 else np.nan
    g = r - f if not pd.isna(f) else np.nan
    valid = "YES" if (not pd.isna(g) and g > 30) else ("n/a" if pd.isna(g) else "WEAK")
    lines.append(f"| {sym} | {r:.0f}% | {f:.0f}% | {g:+.0f}% | {valid} |" if not pd.isna(f) else f"| {sym} | {r:.0f}% | — | — | n/a |")
lines.append("")

# Finding 4: Gap down = more runners
lines.append("### Finding 4: Gap Down → More Runners")
lines.append("*TSLA: gap down 21% runners vs gap up 14%*")
lines.append("")
lines.append("| Symbol | Gap Down Runner% | Gap Up Runner% | Gap | Validates? |")
lines.append("|--------|-----------------|----------------|-----|-----------|")
for sym in SYMBOLS:
    s = df[df['symbol'] == sym].dropna(subset=['gap_atr'])
    gd = s[s['gap_atr'] < -0.3]
    gu = s[s['gap_atr'] > 0.3]
    if len(gd) < 3 or len(gu) < 3:
        continue
    rd = (gd['outcome'] == 'runner').mean() * 100
    ru = (gu['outcome'] == 'runner').mean() * 100
    g = rd - ru
    valid = "YES" if g > 3 else ("NO" if g < -3 else "FLAT")
    lines.append(f"| {sym} | {rd:.0f}% (n={len(gd)}) | {ru:.0f}% (n={len(gu)}) | {g:+.0f}% | {valid} |")
lines.append("")

# Finding 5: Morning is best
lines.append("### Finding 5: Morning 9:30-10 = Best Time")
lines.append("*TSLA: 20% runner rate at open vs <10% afternoon*")
lines.append("")
lines.append("| Symbol | 9:30-10 Runner% | 10-11 Runner% | 14-16 Runner% | Morning edge? |")
lines.append("|--------|----------------|---------------|---------------|--------------|")
for sym in SYMBOLS:
    s = df[df['symbol'] == sym]
    t1 = s[s['time_bucket'] == '09:30-10']
    t2 = s[s['time_bucket'] == '10-11']
    t3 = s[s['time_bucket'] == '14-16']
    r1 = (t1['outcome'] == 'runner').mean() * 100 if len(t1) >= 3 else np.nan
    r2 = (t2['outcome'] == 'runner').mean() * 100 if len(t2) >= 3 else np.nan
    r3 = (t3['outcome'] == 'runner').mean() * 100 if len(t3) >= 3 else np.nan
    edge = "YES" if (not pd.isna(r1) and not pd.isna(r3) and r1 > r3 + 5) else "NO/FLAT"
    lines.append(f"| {sym} | {r1:.0f}% (n={len(t1)}) | {r2:.0f}% (n={len(t2)}) | {r3:.0f}% (n={len(t3)}) | {edge} |" if not pd.isna(r1) else f"| {sym} | — | — | — | insufficient data |")
lines.append("")

# ── Overall feature ranking (all symbols combined) ───────────
lines.append("## Combined Feature Ranking (All 13 Symbols)")
lines.append("")
lines.append("| Metric | All | Runners | Fakeouts | Gap | Useful? |")
lines.append("|--------|-----|---------|----------|-----|---------|")

has_fakeouts = nf_all > 0
for label, col, fmt in [
    ('Avg MFE', 'mfe', '.2f'), ('Avg MAE', 'mae', '.2f'), ('5m P&L', 'pnl_5m', '.2f'),
    ('Vol Ratio', 'vol_ratio', '.2f'), ('Pre Vol Ramp', 'pre_vol_ramp', '.2f'),
    ('ADX', 'adx', '.1f'), ('Body %', 'body_pct', '.1f'),
    ('VWAP Dist', 'vwap_dist', '.2f'), ('Pre Compression', 'pre_compression', '.2f'),
    ('Pre Dir Pressure', 'pre_dir_pressure', '.1f'),
]:
    a = df[col].mean()
    r = df.loc[df['outcome']=='runner', col].mean() if nr_all > 0 else 0
    f = df.loc[df['outcome']=='fakeout', col].mean() if nf_all > 0 else 0
    g = r - f if has_fakeouts else 0
    useful = "YES" if abs(g) > (0.5 if fmt == '.2f' else 2) else "weak"
    lines.append(f"| {label} | {a:{fmt}} | {r:{fmt}} | {f:{fmt}} | {g:+{fmt}} | {useful} |")

# Pct features
lines.append("")
lines.append("| Feature | All | Runners | Fakeouts | Gap | Useful? |")
lines.append("|---------|-----|---------|----------|-----|---------|")
for label, col in [('EMA aligned', 'ema_aligned'), ('VWAP aligned', 'vwap_aligned')]:
    a = df[col].mean() * 100
    r = df.loc[df['outcome']=='runner', col].mean() * 100 if nr_all > 0 else 0
    f = df.loc[df['outcome']=='fakeout', col].mean() * 100 if nf_all > 0 else 0
    g = r - f if has_fakeouts else 0
    useful = "YES" if abs(g) > 5 else "weak"
    lines.append(f"| {label} | {a:.0f}% | {r:.0f}% | {f:.0f}% | {g:+.0f}% | {useful} |")

# Bull direction + 5m positive
a = (df['direction'] == 'bull').mean() * 100
r = (df.loc[df['outcome']=='runner', 'direction'] == 'bull').mean() * 100 if nr_all > 0 else 0
f = (df.loc[df['outcome']=='fakeout', 'direction'] == 'bull').mean() * 100 if nf_all > 0 else 0
lines.append(f"| Bull direction | {a:.0f}% | {r:.0f}% | {f:.0f}% | {r-f:+.0f}% | {'YES' if abs(r-f) > 5 else 'weak'} |")

p5df = df.dropna(subset=['pnl_5m'])
a = (p5df['pnl_5m'] > 0).mean() * 100
r = (p5df.loc[p5df['outcome']=='runner', 'pnl_5m'] > 0).mean() * 100 if nr_all > 0 else 0
f = (p5df.loc[p5df['outcome']=='fakeout', 'pnl_5m'] > 0).mean() * 100 if nf_all > 0 else 0
lines.append(f"| 5min P&L positive | {a:.0f}% | {r:.0f}% | {f:.0f}% | {r-f:+.0f}% | {'YES' if abs(r-f) > 20 else 'weak'} |")

lines.append("")

# ── Time of day combined ─────────────────────────────────────
lines.append("## Time of Day (All Symbols Combined)")
lines.append("")
lines.append("| Time | n | Runners | Fakeouts | Runner% | Avg MFE |")
lines.append("|------|---|---------|----------|---------|---------|")
for bucket in ['09:30-10', '10-11', '11-12', '12-14', '14-16']:
    sub = df[df['time_bucket'] == bucket]
    if len(sub) < 3:
        continue
    nr = (sub['outcome'] == 'runner').sum()
    nf = (sub['outcome'] == 'fakeout').sum()
    lines.append(f"| {bucket} | {len(sub)} | {nr} | {nf} | {nr/len(sub)*100:.0f}% | {sub['mfe'].mean():.2f} |")

lines.append("")

# ── Vol ramp combined ────────────────────────────────────────
lines.append("## Pre-Move Volume Ramp (All Symbols)")
lines.append("")
lines.append("| Vol Ramp | n | Runner% | Fakeout% | Avg MFE |")
lines.append("|----------|---|---------|----------|---------|")
vr = df.dropna(subset=['pre_vol_ramp'])
for lo, hi, label in [(0, 0.5, '<0.5 (drying)'), (0.5, 1.0, '0.5-1 (steady)'), (1.0, 2.0, '1-2x (ramping)'), (2.0, 5.0, '2-5x (surging)'), (5.0, 999, '>5x (explosive)')]:
    sub = vr[(vr['pre_vol_ramp'] >= lo) & (vr['pre_vol_ramp'] < hi)]
    if len(sub) < 3:
        continue
    rr = (sub['outcome'] == 'runner').mean() * 100
    fr = (sub['outcome'] == 'fakeout').mean() * 100
    lines.append(f"| {label} | {len(sub)} | {rr:.0f}% | {fr:.0f}% | {sub['mfe'].mean():.2f} |")

lines.append("")

# ── Summary verdict ──────────────────────────────────────────
lines.append("## Verdict: What Generalizes?")
lines.append("")
lines.append("*(filled in after reviewing data above)*")

with open(OUT_MD, 'w') as f:
    f.write('\n'.join(lines))
print(f"Report saved to {OUT_MD}", file=sys.stderr)
print("Done!", file=sys.stderr)
