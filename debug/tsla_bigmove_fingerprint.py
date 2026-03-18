"""
TSLA Big-Move Fingerprint — Multi-Timeframe Analysis
Finds 5m bars with range > 1x ATR(14), then fingerprints:
  Phase 1: The big move itself (5m indicators)
  Phase 2: Pre-move context (1m lookback, 15m structure, daily context)
  Phase 3: Continuation (5s MFE/MAE)
"""
import os, sys, numpy as np, pandas as pd
from datetime import timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(BASE))), "trading_bot", "cache")
OUT_CSV = os.path.join(BASE, "tsla-bigmove-data.csv")
OUT_MD = os.path.join(BASE, "tsla-bigmove-fingerprint.md")

# ── Helpers ──────────────────────────────────────────────────
def compute_atr(h, l, c, period=14):
    prev_c = c.shift(1)
    tr = pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()

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
        print(f"  MISSING: {fpath}", file=sys.stderr)
        return None
    df = pd.read_parquet(fpath)
    df['date'] = pd.to_datetime(df['date'])
    if df['date'].dt.tz is None:
        df['date'] = df['date'].dt.tz_localize('US/Eastern')
    else:
        df['date'] = df['date'].dt.tz_convert('US/Eastern')
    return df.set_index('date').sort_index()

# ── Load all timeframes ──────────────────────────────────────
print("Loading TSLA data...", file=sys.stderr)
df5m = load_parquet("bars/tsla_5_mins_ib.parquet")
df1m = load_parquet("bars/tsla_1_min_ib.parquet")
df15m = load_parquet("bars/tsla_15_mins_ib.parquet")
dfD = load_parquet("bars/tsla_1_day_ib.parquet")
df5s = load_parquet("bars_highres/5sec/tsla_5_secs_ib.parquet")

# Daily: fix timezone (daily bars often tz-naive)
if dfD is not None and dfD.index.tz is None:
    dfD.index = dfD.index.tz_localize('US/Eastern')

# ── Prepare 5m indicators ───────────────────────────────────
print("Computing 5m indicators...", file=sys.stderr)
df5m['adx'], df5m['atr14'] = compute_adx(df5m['high'], df5m['low'], df5m['close'], 14)
df5m['ema9'] = df5m['close'].ewm(span=9, adjust=False).mean()
df5m['ema20'] = df5m['close'].ewm(span=20, adjust=False).mean()
df5m['ema50'] = df5m['close'].ewm(span=50, adjust=False).mean()
df5m['vol_sma20'] = df5m['volume'].rolling(20).mean()
df5m['vol_ratio'] = df5m['volume'] / df5m['vol_sma20'].replace(0, np.nan)

# VWAP (daily reset)
df5m['day'] = df5m.index.date
df5m['cum_vol'] = df5m.groupby('day')['volume'].cumsum()
df5m['cum_vp'] = df5m.groupby('day').apply(lambda g: (g['close'] * g['volume']).cumsum()).droplevel(0)
df5m['vwap'] = df5m['cum_vp'] / df5m['cum_vol'].replace(0, np.nan)

# Range and body
rng5m = df5m['high'] - df5m['low']
df5m['range_atr'] = rng5m / df5m['atr14'].replace(0, np.nan)
df5m['body_pct'] = (np.abs(df5m['close'] - df5m['open']) / rng5m.replace(0, np.nan) * 100).fillna(0)
df5m['direction'] = np.where(df5m['close'] > df5m['open'], 'bull', 'bear')

# ── Prepare 15m indicators ──────────────────────────────────
print("Computing 15m indicators...", file=sys.stderr)
df15m['ema20'] = df15m['close'].ewm(span=20, adjust=False).mean()
df15m['ema50'] = df15m['close'].ewm(span=50, adjust=False).mean()
df15m['atr14'] = compute_atr(df15m['high'], df15m['low'], df15m['close'], 14)

# ── Prepare daily context ───────────────────────────────────
if dfD is not None:
    dfD['prev_close'] = dfD['close'].shift(1)
    dfD['prev_range'] = (dfD['high'] - dfD['low']).shift(1)
    dfD['prev_atr'] = compute_atr(dfD['high'], dfD['low'], dfD['close'], 14).shift(1)

# ── Phase 1: Find big moves ─────────────────────────────────
print("Finding big moves (range > 1x ATR)...", file=sys.stderr)
# Use a recent window with good data overlap across all timeframes
START = "2025-03-01"
END = "2026-03-03"
window = df5m.loc[START:END].copy()
# RTH only
window = window[(window.index.hour >= 9) & (window.index.hour < 16)]
window = window[~((window.index.hour == 9) & (window.index.minute < 30))]

big = window[window['range_atr'] >= 1.0].copy()
print(f"  Found {len(big)} big moves (>= 1x ATR) in {START} to {END}", file=sys.stderr)

# ── Phase 2+3: Build features for each big move ─────────────
print("Building multi-TF features...", file=sys.stderr)
rows = []
for ts, bar in big.iterrows():
    atr = bar['atr14']
    if atr <= 0 or pd.isna(atr):
        continue
    direction = bar['direction']

    # --- 5m bar features (Phase 1) ---
    feat = {
        'date': ts.strftime('%Y-%m-%d'),
        'time': ts.strftime('%H:%M'),
        'direction': direction,
        'open': round(bar['open'], 2),
        'high': round(bar['high'], 2),
        'low': round(bar['low'], 2),
        'close': round(bar['close'], 2),
        'range_atr': round(bar['range_atr'], 3),
        'body_pct': round(bar['body_pct'], 1),
        'vol_ratio': round(bar['vol_ratio'], 2) if not pd.isna(bar['vol_ratio']) else 0,
        'adx': round(bar['adx'], 1),
        'atr': round(atr, 4),
        'ema_aligned': 1 if (bar['ema20'] > bar['ema50']) == (direction == 'bull') else 0,
        'above_ema9': 1 if bar['close'] > bar['ema9'] else 0,
        'above_ema20': 1 if bar['close'] > bar['ema20'] else 0,
        'vwap_dist': round((bar['close'] - bar['vwap']) / atr, 3) if not pd.isna(bar['vwap']) else 0,
        'vwap_aligned': 1 if (bar['close'] > bar['vwap']) == (direction == 'bull') else 0,
        'time_bucket': (
            '09:30-10' if ts.hour == 9 else
            '10-11' if ts.hour == 10 else
            '11-12' if ts.hour == 11 else
            '12-13' if ts.hour == 12 else
            '13-14' if ts.hour == 13 else
            '14-15' if ts.hour == 14 else '15-16'
        ),
    }

    # --- 1m pre-move context (10 bars before) ---
    if df1m is not None:
        lookback_end = ts - timedelta(seconds=1)
        lookback_start = ts - timedelta(minutes=10)
        pre1m = df1m.loc[lookback_start:lookback_end]
        if len(pre1m) >= 5:
            pre_range = pre1m['high'].max() - pre1m['low'].min()
            feat['pre_compression'] = round(pre_range / atr, 3) if atr > 0 else 0
            # Volume ramp: ratio of last 3 bars avg vol to first 3 bars avg vol
            if len(pre1m) >= 6:
                first3_vol = pre1m['volume'].iloc[:3].mean()
                last3_vol = pre1m['volume'].iloc[-3:].mean()
                feat['pre_vol_ramp'] = round(last3_vol / max(first3_vol, 1), 2)
            else:
                feat['pre_vol_ramp'] = 1.0
            # Directional pressure: % of 1m bars closing in move direction
            if direction == 'bull':
                feat['pre_dir_pressure'] = round((pre1m['close'] > pre1m['open']).mean() * 100, 1)
            else:
                feat['pre_dir_pressure'] = round((pre1m['close'] < pre1m['open']).mean() * 100, 1)
            # Close location: avg (close - low) / (high - low) — >0.5 = buying pressure
            pre_rng = (pre1m['high'] - pre1m['low']).replace(0, np.nan)
            feat['pre_close_loc'] = round(((pre1m['close'] - pre1m['low']) / pre_rng).mean() * 100, 1)
            # Micro range breaks: how many 1m bars went outside then back inside the initial range
            if len(pre1m) >= 3:
                init_h = pre1m['high'].iloc[:3].max()
                init_l = pre1m['low'].iloc[:3].min()
                breaks = ((pre1m['high'] > init_h) | (pre1m['low'] < init_l)).sum()
                feat['pre_range_breaks'] = int(breaks)
            else:
                feat['pre_range_breaks'] = 0
            # Pre-move volume level (avg vol ratio)
            if 'vol_sma20' in df1m.columns:
                pre_vol_avg = pre1m['volume'].mean()
            feat['pre_avg_vol'] = round(pre1m['volume'].mean(), 0)
        else:
            feat.update({'pre_compression': np.nan, 'pre_vol_ramp': np.nan,
                        'pre_dir_pressure': np.nan, 'pre_close_loc': np.nan,
                        'pre_range_breaks': np.nan, 'pre_avg_vol': np.nan})

    # --- 15m context ---
    if df15m is not None:
        # Find the 15m bar that contains this 5m bar
        prior_15m = df15m.loc[:ts].iloc[-2:] if len(df15m.loc[:ts]) >= 2 else df15m.loc[:ts].iloc[-1:]
        if len(prior_15m) >= 1:
            cur15 = prior_15m.iloc[-1]
            feat['f15m_range_atr'] = round((cur15['high'] - cur15['low']) / atr, 3) if atr > 0 else 0
            # Position within 15m bar: 0=bottom, 100=top
            f15_rng = cur15['high'] - cur15['low']
            if f15_rng > 0:
                feat['f15m_position'] = round((bar['open'] - cur15['low']) / f15_rng * 100, 1)
            else:
                feat['f15m_position'] = 50.0
            # 15m trend
            feat['f15m_trend_aligned'] = 1 if (cur15['ema20'] > cur15['ema50']) == (direction == 'bull') else 0
            # Breakout of prior 15m bar?
            if len(prior_15m) >= 2:
                prev15 = prior_15m.iloc[-2]
                feat['f15m_breakout'] = 1 if (bar['high'] > prev15['high'] and direction == 'bull') or \
                                              (bar['low'] < prev15['low'] and direction == 'bear') else 0
            else:
                feat['f15m_breakout'] = np.nan
        else:
            feat.update({'f15m_range_atr': np.nan, 'f15m_position': np.nan,
                        'f15m_trend_aligned': np.nan, 'f15m_breakout': np.nan})

    # --- Daily context ---
    if dfD is not None:
        day = ts.date()
        day_ts = pd.Timestamp(day, tz='US/Eastern')
        # Try exact match or closest prior
        daily_row = dfD.loc[:day_ts]
        if len(daily_row) >= 1:
            d = daily_row.iloc[-1]
            # Gap: today's first price vs yesterday's close
            if not pd.isna(d.get('prev_close', np.nan)):
                day_open_bars = df5m[(df5m.index.date == day) & (df5m.index.hour == 9) & (df5m.index.minute == 30)]
                if len(day_open_bars) > 0:
                    gap = (day_open_bars.iloc[0]['open'] - d['prev_close']) / atr
                    feat['gap_atr'] = round(gap, 3)
                else:
                    feat['gap_atr'] = np.nan
            else:
                feat['gap_atr'] = np.nan
            # Day range position: where in today's range so far?
            day_bars = df5m[(df5m.index.date == day) & (df5m.index <= ts)]
            if len(day_bars) > 1:
                day_h, day_l = day_bars['high'].max(), day_bars['low'].min()
                day_rng = day_h - day_l
                if day_rng > 0:
                    feat['day_range_pos'] = round((bar['open'] - day_l) / day_rng * 100, 1)
                else:
                    feat['day_range_pos'] = 50.0
            else:
                feat['day_range_pos'] = np.nan
            # Prior day volatility (ATR expansion/contraction)
            if not pd.isna(d.get('prev_atr', np.nan)) and d['prev_atr'] > 0:
                feat['prev_day_atr'] = round(d['prev_atr'], 2)
            else:
                feat['prev_day_atr'] = np.nan
        else:
            feat.update({'gap_atr': np.nan, 'day_range_pos': np.nan, 'prev_day_atr': np.nan})

    # --- 5s MFE/MAE (Phase 3) ---
    if df5s is not None:
        entry_price = bar['close']
        entry_time = ts + timedelta(minutes=5)  # entry at close of 5m bar
        start_5s = entry_time + timedelta(seconds=5)
        end_5s = entry_time + timedelta(minutes=30)
        window_5s = df5s.loc[start_5s:end_5s]
        if len(window_5s) > 0:
            if direction == 'bull':
                mfe = (window_5s['high'].max() - entry_price) / atr
                mae = (window_5s['low'].min() - entry_price) / atr
            else:
                mfe = (entry_price - window_5s['low'].min()) / atr
                mae = (entry_price - window_5s['high'].max()) / atr
            feat['mfe'] = round(mfe, 3)
            feat['mae'] = round(mae, 3)
            # 5-minute check
            t5 = entry_time + timedelta(minutes=5)
            w5 = df5s.loc[start_5s:t5]
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

    rows.append(feat)
    if len(rows) % 100 == 0:
        print(f"  Processed {len(rows)} / {len(big)} moves...", file=sys.stderr)

print(f"  Done — {len(rows)} moves fingerprinted", file=sys.stderr)

# ── Build dataframe and classify ─────────────────────────────
df = pd.DataFrame(rows)
# Classify: Runner / Fakeout / Middle
df['outcome'] = 'middle'
df.loc[df['mfe'] > 0.5, 'outcome'] = 'runner'
df.loc[(df['mfe'] < 0.1) & (df['mae'] < -0.3), 'outcome'] = 'fakeout'

# Save CSV
df.to_csv(OUT_CSV, index=False)
print(f"\nSaved {len(df)} rows to {OUT_CSV}", file=sys.stderr)

# ── Generate summary report ──────────────────────────────────
print("Generating report...", file=sys.stderr)

lines = []
lines.append(f"# TSLA Big-Move Fingerprint")
lines.append(f"Scanned: {len(df)} moves with range >= 1x ATR(14) on 5m")
lines.append(f"Period: {df['date'].min()} to {df['date'].max()}")

n_run = (df['outcome'] == 'runner').sum()
n_fake = (df['outcome'] == 'fakeout').sum()
n_mid = (df['outcome'] == 'middle').sum()
lines.append(f"Runners (MFE>0.5): {n_run} | Fakeouts (MFE<0.1, MAE<-0.3): {n_fake} | Middle: {n_mid}")
lines.append("")

# -- Overall stats --
lines.append("## Overall Stats")
lines.append("")
lines.append(f"| Metric | All (n={len(df)}) | Runners (n={n_run}) | Fakeouts (n={n_fake}) | Gap |")
lines.append("|--------|-----|---------|----------|-----|")

def stat_row(label, col, fmt=".2f"):
    a = df[col].mean()
    r = df.loc[df['outcome']=='runner', col].mean() if n_run > 0 else 0
    f = df.loc[df['outcome']=='fakeout', col].mean() if n_fake > 0 else 0
    gap = r - f
    lines.append(f"| {label} | {a:{fmt}} | {r:{fmt}} | {f:{fmt}} | {gap:+{fmt}} |")

for label, col in [
    ('Avg MFE (ATR)', 'mfe'), ('Avg MAE (ATR)', 'mae'), ('Avg 5m P&L', 'pnl_5m'),
    ('Avg Body %', 'body_pct'), ('Avg Range/ATR', 'range_atr'), ('Avg Vol Ratio', 'vol_ratio'),
    ('Avg ADX', 'adx'), ('Avg VWAP Dist', 'vwap_dist'),
    ('Pre: Compression', 'pre_compression'), ('Pre: Vol Ramp', 'pre_vol_ramp'),
    ('Pre: Dir Pressure', 'pre_dir_pressure'), ('Pre: Close Loc', 'pre_close_loc'),
    ('Pre: Range Breaks', 'pre_range_breaks'),
    ('15m: Range/ATR', 'f15m_range_atr'), ('15m: Position', 'f15m_position'),
    ('Day: Range Position', 'day_range_pos'), ('Day: Gap/ATR', 'gap_atr'),
]:
    if col in df.columns:
        stat_row(label, col)

lines.append("")

# -- Percentage-based features --
lines.append("## Feature Rates (Runner vs Fakeout)")
lines.append("")
lines.append(f"| Feature | All | Runners | Fakeouts | Gap |")
lines.append("|---------|-----|---------|----------|-----|")

def pct_row(label, col):
    a = df[col].mean() * 100
    r = df.loc[df['outcome']=='runner', col].mean() * 100 if n_run > 0 else 0
    f = df.loc[df['outcome']=='fakeout', col].mean() * 100 if n_fake > 0 else 0
    gap = r - f
    lines.append(f"| {label} | {a:.0f}% | {r:.0f}% | {f:.0f}% | {gap:+.0f}% |")

for label, col in [
    ('EMA aligned', 'ema_aligned'), ('VWAP aligned', 'vwap_aligned'),
    ('Above EMA9', 'above_ema9'), ('Above EMA20', 'above_ema20'),
    ('15m trend aligned', 'f15m_trend_aligned'), ('15m breakout', 'f15m_breakout'),
]:
    if col in df.columns:
        pct_row(label, col)

# Direction
dir_bull_all = (df['direction'] == 'bull').mean() * 100
dir_bull_run = (df.loc[df['outcome']=='runner', 'direction'] == 'bull').mean() * 100 if n_run > 0 else 0
dir_bull_fake = (df.loc[df['outcome']=='fakeout', 'direction'] == 'bull').mean() * 100 if n_fake > 0 else 0
lines.append(f"| Bull direction | {dir_bull_all:.0f}% | {dir_bull_run:.0f}% | {dir_bull_fake:.0f}% | {dir_bull_run - dir_bull_fake:+.0f}% |")

# 5m positive
if 'pnl_5m' in df.columns:
    p5_all = (df['pnl_5m'] > 0).mean() * 100
    p5_run = (df.loc[df['outcome']=='runner', 'pnl_5m'] > 0).mean() * 100 if n_run > 0 else 0
    p5_fake = (df.loc[df['outcome']=='fakeout', 'pnl_5m'] > 0).mean() * 100 if n_fake > 0 else 0
    lines.append(f"| 5min P&L positive | {p5_all:.0f}% | {p5_run:.0f}% | {p5_fake:.0f}% | {p5_run - p5_fake:+.0f}% |")

lines.append("")

# -- Time buckets --
lines.append("## By Time of Day")
lines.append("")
lines.append("| Time | n | Runners | Fakeouts | Runner% | Avg MFE |")
lines.append("|------|---|---------|----------|---------|---------|")
for bucket in ['09:30-10', '10-11', '11-12', '12-13', '13-14', '14-15', '15-16']:
    sub = df[df['time_bucket'] == bucket]
    if len(sub) == 0:
        continue
    nr = (sub['outcome'] == 'runner').sum()
    nf = (sub['outcome'] == 'fakeout').sum()
    rr = nr / len(sub) * 100 if len(sub) > 0 else 0
    lines.append(f"| {bucket} | {len(sub)} | {nr} | {nf} | {rr:.0f}% | {sub['mfe'].mean():.2f} |")

lines.append("")

# -- Pre-move compression buckets --
lines.append("## Pre-Move Compression (1m 10-bar range / ATR)")
lines.append("")
lines.append("| Compression | n | Runner% | Fakeout% | Avg MFE |")
lines.append("|-------------|---|---------|----------|---------|")
if 'pre_compression' in df.columns:
    comp = df.dropna(subset=['pre_compression'])
    for lo, hi, label in [(0, 0.3, '<0.3 (tight)'), (0.3, 0.6, '0.3-0.6'), (0.6, 1.0, '0.6-1.0'), (1.0, 99, '>1.0 (wide)')]:
        sub = comp[(comp['pre_compression'] >= lo) & (comp['pre_compression'] < hi)]
        if len(sub) < 3:
            continue
        rr = (sub['outcome'] == 'runner').mean() * 100
        fr = (sub['outcome'] == 'fakeout').mean() * 100
        lines.append(f"| {label} | {len(sub)} | {rr:.0f}% | {fr:.0f}% | {sub['mfe'].mean():.2f} |")

lines.append("")

# -- Volume ramp buckets --
lines.append("## Pre-Move Volume Ramp (last 3 bars / first 3 bars)")
lines.append("")
lines.append("| Vol Ramp | n | Runner% | Fakeout% | Avg MFE |")
lines.append("|----------|---|---------|----------|---------|")
if 'pre_vol_ramp' in df.columns:
    vr = df.dropna(subset=['pre_vol_ramp'])
    for lo, hi, label in [(0, 0.5, '<0.5 (drying)'), (0.5, 1.0, '0.5-1.0 (steady)'), (1.0, 2.0, '1-2x (ramping)'), (2.0, 999, '>2x (surging)')]:
        sub = vr[(vr['pre_vol_ramp'] >= lo) & (vr['pre_vol_ramp'] < hi)]
        if len(sub) < 3:
            continue
        rr = (sub['outcome'] == 'runner').mean() * 100
        fr = (sub['outcome'] == 'fakeout').mean() * 100
        lines.append(f"| {label} | {len(sub)} | {rr:.0f}% | {fr:.0f}% | {sub['mfe'].mean():.2f} |")

lines.append("")

# -- 15m breakout vs continuation --
lines.append("## 15m Context: Breakout vs Inside Move")
lines.append("")
if 'f15m_breakout' in df.columns:
    for val, label in [(1, '15m Breakout'), (0, 'Inside 15m range')]:
        sub = df[df['f15m_breakout'] == val]
        if len(sub) < 3:
            continue
        rr = (sub['outcome'] == 'runner').mean() * 100
        fr = (sub['outcome'] == 'fakeout').mean() * 100
        lines.append(f"- **{label}** (n={len(sub)}): {rr:.0f}% runners, {fr:.0f}% fakeouts, MFE {sub['mfe'].mean():.2f}")

lines.append("")

# -- Gap context --
lines.append("## Daily Gap Context")
lines.append("")
lines.append("| Gap | n | Runner% | Fakeout% | Avg MFE |")
lines.append("|-----|---|---------|----------|---------|")
if 'gap_atr' in df.columns:
    gdf = df.dropna(subset=['gap_atr'])
    for lo, hi, label in [(-99, -0.3, 'Gap Down (>0.3 ATR)'), (-0.3, 0.3, 'Flat (<0.3 ATR)'), (0.3, 99, 'Gap Up (>0.3 ATR)')]:
        sub = gdf[(gdf['gap_atr'] >= lo) & (gdf['gap_atr'] < hi)]
        if len(sub) < 3:
            continue
        rr = (sub['outcome'] == 'runner').mean() * 100
        fr = (sub['outcome'] == 'fakeout').mean() * 100
        lines.append(f"| {label} | {len(sub)} | {rr:.0f}% | {fr:.0f}% | {sub['mfe'].mean():.2f} |")

lines.append("")

# -- Top 20 runners --
lines.append("## Top 20 Runners (by MFE)")
lines.append("")
lines.append("| Date | Time | Dir | Range | Body | Vol | ADX | Compression | VolRamp | 5mPnL | MFE | MAE |")
lines.append("|------|------|-----|-------|------|-----|-----|-------------|---------|-------|-----|-----|")
top = df.nlargest(20, 'mfe')
for _, r in top.iterrows():
    lines.append(f"| {r['date']} | {r['time']} | {r['direction'][:1].upper()} | {r['range_atr']:.1f} | {r['body_pct']:.0f}% | {r['vol_ratio']:.1f}x | {r['adx']:.0f} | {r.get('pre_compression', 0):.2f} | {r.get('pre_vol_ramp', 0):.1f}x | {r.get('pnl_5m', 0):.2f} | {r['mfe']:.2f} | {r['mae']:.2f} |")

lines.append("")

# -- Top 10 fakeouts --
lines.append("## Top 10 Fakeouts (worst MAE)")
lines.append("")
lines.append("| Date | Time | Dir | Range | Body | Vol | ADX | Compression | VolRamp | 5mPnL | MFE | MAE |")
lines.append("|------|------|-----|-------|------|-----|-----|-------------|---------|-------|-----|-----|")
fakes = df[df['outcome'] == 'fakeout'].nsmallest(10, 'mae')
for _, r in fakes.iterrows():
    lines.append(f"| {r['date']} | {r['time']} | {r['direction'][:1].upper()} | {r['range_atr']:.1f} | {r['body_pct']:.0f}% | {r['vol_ratio']:.1f}x | {r['adx']:.0f} | {r.get('pre_compression', 0):.2f} | {r.get('pre_vol_ramp', 0):.1f}x | {r.get('pnl_5m', 0):.2f} | {r['mfe']:.2f} | {r['mae']:.2f} |")

# Write report
with open(OUT_MD, 'w') as f:
    f.write('\n'.join(lines))
print(f"Saved report to {OUT_MD}", file=sys.stderr)
print("Done!", file=sys.stderr)
