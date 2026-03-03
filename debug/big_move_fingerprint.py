"""
Big Move Fingerprint Analysis
Scans 5m candles across 13 symbols for significant moves, measures 5s follow-through,
and fingerprints what separates runners from fakeouts.
"""
import os, sys, numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(BASE))), "trading_bot", "cache")

SYMBOLS = ["SPY", "AAPL", "AMD", "AMZN", "GLD", "GOOGL", "META", "MSFT", "NVDA", "QQQ", "SLV", "TSLA", "TSM"]
# Analysis window: same as Pine log data
START = "2026-01-20"
END = "2026-03-02"

# ── Indicator computation ─────────────────────────────────
def compute_adx(h, l, c, period=14):
    prev_h, prev_l, prev_c = h.shift(1), l.shift(1), c.shift(1)
    tr = pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    plus_dm = np.where((h - prev_h > prev_l - l) & (h - prev_h > 0), h - prev_h, 0)
    minus_dm = np.where((prev_l - l > h - prev_h) & (prev_l - l > 0), prev_l - l, 0)
    atr = pd.Series(tr, index=h.index).ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=h.index).ewm(alpha=1/period, adjust=False).mean() / atr
    minus_di = 100 * pd.Series(minus_dm, index=h.index).ewm(alpha=1/period, adjust=False).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    return adx.fillna(0), atr

def load_and_prepare_5m(symbol):
    fpath = os.path.join(CACHE, "bars", f"{symbol.lower()}_5_mins_ib.parquet")
    if not os.path.exists(fpath):
        return None
    df = pd.read_parquet(fpath)
    df['date'] = pd.to_datetime(df['date'])
    if df['date'].dt.tz is None:
        df['date'] = df['date'].dt.tz_localize('US/Eastern')
    else:
        df['date'] = df['date'].dt.tz_convert('US/Eastern')
    df = df.set_index('date').sort_index()
    # Need context before START for EMA/ADX warmup
    warmup_start = pd.Timestamp(START, tz='US/Eastern') - timedelta(days=30)
    df = df.loc[warmup_start:]
    # Indicators
    df['adx'], df['atr14'] = compute_adx(df['high'], df['low'], df['close'], 14)
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['vol_sma20'] = df['volume'].rolling(20).mean()
    df['vol_ratio'] = df['volume'] / df['vol_sma20'].replace(0, np.nan)
    # Body
    rng = df['high'] - df['low']
    df['body_pct'] = (np.abs(df['close'] - df['open']) / rng.replace(0, np.nan) * 100).fillna(0)
    df['range_atr'] = rng / df['atr14'].replace(0, np.nan)
    df['direction'] = np.where(df['close'] > df['open'], 'bull', 'bear')
    # VWAP (reset daily)
    df['day'] = df.index.date
    df['cum_vol'] = df.groupby('day')['volume'].cumsum()
    df['cum_vp'] = df.groupby('day').apply(lambda g: (g['close'] * g['volume']).cumsum()).droplevel(0)
    df['vwap'] = df['cum_vp'] / df['cum_vol'].replace(0, np.nan)
    df['vwap_dist'] = (df['close'] - df['vwap']) / df['atr14'].replace(0, np.nan)
    # Daily ATR for threshold
    daily = df.groupby('day').agg({'high': 'max', 'low': 'min', 'close': 'last'})
    daily['daily_atr'] = (daily['high'] - daily['low']).rolling(14).mean()
    df['daily_atr'] = df['day'].map(daily['daily_atr'].shift(1))
    # EMA position
    df['above_ema9'] = df['close'] > df['ema9']
    df['above_ema20'] = df['close'] > df['ema20']
    df['above_ema50'] = df['close'] > df['ema50']
    # Trend: EMA20 > EMA50 = uptrend
    df['ema_trend'] = np.where(df['ema20'] > df['ema50'], 'up', 'down')
    # Previous bar info
    df['prev_body_pct'] = df['body_pct'].shift(1)
    df['prev_direction'] = df['direction'].shift(1)
    df['prev_vol_ratio'] = df['vol_ratio'].shift(1)
    # Trim to analysis window
    df = df.loc[START:END]
    return df

def load_5s(symbol):
    fpath = os.path.join(CACHE, "bars_highres", "5sec", f"{symbol.lower()}_5_secs_ib.parquet")
    if not os.path.exists(fpath):
        return None
    df = pd.read_parquet(fpath)
    df['date'] = pd.to_datetime(df['date'], utc=True).dt.tz_convert('US/Eastern')
    df = df.set_index('date').sort_index()
    return df

def measure_mfe_mae(df5s, entry_time, direction, entry_price, atr, minutes=60):
    if df5s is None or atr <= 0:
        return 0, 0
    start = entry_time + timedelta(seconds=5)
    end = entry_time + timedelta(minutes=minutes)
    window = df5s.loc[start:end]
    if len(window) == 0:
        return 0, 0
    if direction == 'bull':
        mfe = (window['high'].max() - entry_price) / atr
        mae = (window['low'].min() - entry_price) / atr
    else:
        mfe = (entry_price - window['low'].min()) / atr
        mae = (entry_price - window['high'].max()) / atr
    return round(mfe, 3), round(mae, 3)

def measure_5min_check(df5s, entry_time, direction, entry_price, atr):
    """Check P&L at exactly 5 minutes — the early gate."""
    if df5s is None or atr <= 0:
        return 0
    t5 = entry_time + timedelta(minutes=5)
    window = df5s.loc[entry_time + timedelta(seconds=5):t5]
    if len(window) == 0:
        return 0
    last = window.iloc[-1]['close']
    if direction == 'bull':
        return round((last - entry_price) / atr, 3)
    else:
        return round((entry_price - last) / atr, 3)

# ── Main scan ─────────────────────────────────────────────
print("Scanning for big moves across 13 symbols...", file=sys.stderr)

all_moves = []
for sym in SYMBOLS:
    print(f"  Loading {sym}...", file=sys.stderr)
    df5m = load_and_prepare_5m(sym)
    if df5m is None:
        continue
    df5s = load_5s(sym)

    # Filter for "big bars": body >= 60%, range >= 0.12 ATR
    big = df5m[(df5m['body_pct'] >= 60) & (df5m['range_atr'] >= 0.12)].copy()
    # Only regular hours
    big = big[(big.index.hour >= 9) & (big.index.hour < 16)]
    big = big[~((big.index.hour == 9) & (big.index.minute < 30))]

    print(f"    {len(big)} big bars found, measuring follow-through...", file=sys.stderr)

    for idx, row in big.iterrows():
        mfe, mae = measure_mfe_mae(df5s, idx, row['direction'], row['close'], row['atr14'], 60)
        pnl_5m = measure_5min_check(df5s, idx, row['direction'], row['close'], row['atr14'])

        # EMA alignment
        if row['direction'] == 'bull':
            ema_aligned = row['above_ema20'] and row['above_ema50']
            with_ema_trend = row['ema_trend'] == 'up'
            vwap_aligned = row['close'] > row.get('vwap', 0)
        else:
            ema_aligned = not row['above_ema20'] and not row['above_ema50']
            with_ema_trend = row['ema_trend'] == 'down'
            vwap_aligned = row['close'] < row.get('vwap', 0)

        hour, minute = idx.hour, idx.minute
        tm = hour * 60 + minute
        if tm < 600: tb = "9:30-10:00"
        elif tm < 660: tb = "10:00-11:00"
        elif tm < 720: tb = "11:00-12:00"
        else: tb = "12:00+"

        all_moves.append({
            'symbol': sym, 'dt': idx, 'date': idx.strftime('%Y-%m-%d'),
            'time': f'{hour}:{minute:02d}',
            'direction': row['direction'],
            'open': row['open'], 'high': row['high'], 'low': row['low'], 'close': row['close'],
            'body_pct': int(row['body_pct']),
            'range_atr': round(row['range_atr'], 3),
            'vol_ratio': round(row['vol_ratio'], 2) if not np.isnan(row['vol_ratio']) else 0,
            'adx': int(row['adx']),
            'ema_aligned': ema_aligned,
            'with_ema_trend': with_ema_trend,
            'vwap_aligned': vwap_aligned,
            'vwap_dist': round(row['vwap_dist'], 3) if not np.isnan(row['vwap_dist']) else 0,
            'above_ema9': bool(row['above_ema9']),
            'above_ema20': bool(row['above_ema20']),
            'above_ema50': bool(row['above_ema50']),
            'ema_trend': row['ema_trend'],
            'prev_body_pct': int(row['prev_body_pct']) if not np.isnan(row['prev_body_pct']) else 0,
            'prev_same_dir': row['prev_direction'] == row['direction'],
            'prev_vol_ratio': round(row['prev_vol_ratio'], 2) if not np.isnan(row['prev_vol_ratio']) else 0,
            'time_bucket': tb,
            'mfe': mfe, 'mae': mae, 'pnl_5m': pnl_5m,
            'atr': round(row['atr14'], 2),
        })

print(f"\nTotal big moves: {len(all_moves)}", file=sys.stderr)

# ── Classify ──────────────────────────────────────────────
# Runners: MFE > 0.3 ATR (the move continues strongly)
# Fakeouts: MFE < 0.1 AND MAE < -0.15 (move reverses)
# Middle: everything else
runners = [m for m in all_moves if m['mfe'] > 0.3]
fakeouts = [m for m in all_moves if m['mfe'] < 0.1 and m['mae'] < -0.15]
middle = [m for m in all_moves if m not in runners and m not in fakeouts]

# ── Output ────────────────────────────────────────────────
out = []
def p(s=""): out.append(s)
def pct(lst, fn): return sum(1 for m in lst if fn(m)) * 100 / len(lst) if lst else 0
def avg(lst, fn): return sum(fn(m) for m in lst) / len(lst) if lst else 0

p("# Big Move Fingerprint — 13 Symbols")
p(f"Scanned: {len(all_moves)} significant 5m bars (body≥60%, range≥0.12 ATR)")
p(f"Period: {START} to {END}")
p(f"Runners (MFE>0.3): {len(runners)} | Fakeouts (MFE<0.1, MAE<-0.15): {len(fakeouts)} | Middle: {len(middle)}")
p()

# ── Fingerprint comparison ────────────────────────────────
p("## Runner vs Fakeout Fingerprint")
p()
p(f"| Metric | Runners (n={len(runners)}) | Fakeouts (n={len(fakeouts)}) | All (n={len(all_moves)}) | Gap |")
p("|--------|---------|----------|-----|-----|")

metrics = [
    ("Avg MFE (ATR)", lambda m: m['mfe']),
    ("Avg MAE (ATR)", lambda m: m['mae']),
    ("Avg P&L at 5min", lambda m: m['pnl_5m']),
    ("Avg Body %", lambda m: m['body_pct']),
    ("Avg Range (ATR)", lambda m: m['range_atr']),
    ("Avg Vol Ratio", lambda m: m['vol_ratio']),
    ("Avg ADX", lambda m: m['adx']),
    ("Avg VWAP Dist (ATR)", lambda m: m['vwap_dist']),
]
for name, fn in metrics:
    r = avg(runners, fn)
    f = avg(fakeouts, fn)
    a = avg(all_moves, fn)
    p(f"| {name} | {r:.2f} | {f:.2f} | {a:.2f} | {r-f:+.2f} |")

pct_metrics = [
    ("EMA aligned (EMA20+50)", lambda m: m['ema_aligned']),
    ("With EMA trend (EMA20>50)", lambda m: m['with_ema_trend']),
    ("VWAP aligned", lambda m: m['vwap_aligned']),
    ("Above EMA9", lambda m: m['above_ema9'] if m['direction']=='bull' else not m['above_ema9']),
    ("Bear direction", lambda m: m['direction'] == 'bear'),
    ("Prev bar same direction", lambda m: m['prev_same_dir']),
    ("Before 11:00", lambda m: m['time_bucket'] in ('9:30-10:00', '10:00-11:00')),
    ("9:30-10:00", lambda m: m['time_bucket'] == '9:30-10:00'),
    ("Vol ≥ 2x", lambda m: m['vol_ratio'] >= 2),
    ("Vol ≥ 5x", lambda m: m['vol_ratio'] >= 5),
    ("ADX 20-30", lambda m: 20 <= m['adx'] < 30),
    ("ADX ≥ 30", lambda m: m['adx'] >= 30),
    ("Body ≥ 80%", lambda m: m['body_pct'] >= 80),
    ("Range ≥ 0.2 ATR", lambda m: m['range_atr'] >= 0.2),
    ("5min P&L positive", lambda m: m['pnl_5m'] > 0),
    ("5min P&L > 0.05 ATR", lambda m: m['pnl_5m'] > 0.05),
]
for name, fn in pct_metrics:
    r = pct(runners, fn)
    f = pct(fakeouts, fn)
    a = pct(all_moves, fn)
    p(f"| {name} % | {r:.0f}% | {f:.0f}% | {a:.0f}% | {r-f:+.0f}% |")
p()

# ── Combined filter stacking ─────────────────────────────
p("## Filter Stacking — Combined Conditions")
p()
p("| Condition | n | Runner% | Fakeout% | Avg MFE | Avg MAE |")
p("|-----------|---|---------|----------|---------|---------|")

combos = [
    ("All big bars", lambda m: True),
    ("EMA aligned", lambda m: m['ema_aligned']),
    ("EMA aligned + VWAP aligned", lambda m: m['ema_aligned'] and m['vwap_aligned']),
    ("EMA + VWAP + ADX≥20", lambda m: m['ema_aligned'] and m['vwap_aligned'] and m['adx'] >= 20),
    ("EMA + VWAP + ADX≥20 + body≥80%", lambda m: m['ema_aligned'] and m['vwap_aligned'] and m['adx'] >= 20 and m['body_pct'] >= 80),
    ("EMA + VWAP + ADX≥20 + vol≥2x", lambda m: m['ema_aligned'] and m['vwap_aligned'] and m['adx'] >= 20 and m['vol_ratio'] >= 2),
    ("EMA + VWAP + before 11", lambda m: m['ema_aligned'] and m['vwap_aligned'] and m['time_bucket'] in ('9:30-10:00', '10:00-11:00')),
    ("EMA + VWAP + bear", lambda m: m['ema_aligned'] and m['vwap_aligned'] and m['direction'] == 'bear'),
    ("EMA + VWAP + bear + vol≥2x", lambda m: m['ema_aligned'] and m['vwap_aligned'] and m['direction'] == 'bear' and m['vol_ratio'] >= 2),
    ("EMA + VWAP + bear + ADX≥20 + before 11", lambda m: m['ema_aligned'] and m['vwap_aligned'] and m['direction'] == 'bear' and m['adx'] >= 20 and m['time_bucket'] in ('9:30-10:00', '10:00-11:00')),
    ("5min positive", lambda m: m['pnl_5m'] > 0),
    ("5min positive + EMA aligned", lambda m: m['pnl_5m'] > 0 and m['ema_aligned']),
    ("5min > 0.05 + EMA + VWAP", lambda m: m['pnl_5m'] > 0.05 and m['ema_aligned'] and m['vwap_aligned']),
    ("VWAP rejection (vwap_dist < -0.05 and bear)", lambda m: m['vwap_dist'] < -0.05 and m['direction'] == 'bear'),
    ("VWAP rejection + EMA aligned", lambda m: m['vwap_dist'] < -0.05 and m['direction'] == 'bear' and m['ema_aligned']),
    ("Prev bar same dir (momentum)", lambda m: m['prev_same_dir']),
    ("Prev same dir + EMA + VWAP", lambda m: m['prev_same_dir'] and m['ema_aligned'] and m['vwap_aligned']),
    ("Above EMA9 aligned", lambda m: m['above_ema9'] if m['direction']=='bull' else not m['above_ema9']),
    ("EMA9 + EMA20/50 + VWAP", lambda m: (m['above_ema9'] if m['direction']=='bull' else not m['above_ema9']) and m['ema_aligned'] and m['vwap_aligned']),
]
for name, fn in combos:
    subset = [m for m in all_moves if fn(m)]
    n = len(subset)
    if n < 5:
        continue
    r_pct = sum(1 for m in subset if m['mfe'] > 0.3) * 100 / n
    f_pct = sum(1 for m in subset if m['mfe'] < 0.1 and m['mae'] < -0.15) * 100 / n
    m_mfe = sum(m['mfe'] for m in subset) / n
    m_mae = sum(m['mae'] for m in subset) / n
    p(f"| {name} | {n} | {r_pct:.0f}% | {f_pct:.0f}% | {m_mfe:.2f} | {m_mae:.2f} |")
p()

# ── By symbol ─────────────────────────────────────────────
p("## Runner Rate by Symbol")
p()
p("| Symbol | Big Bars | Runners | Runner% | Avg MFE (runner) |")
p("|--------|----------|---------|---------|------------------|")
for sym in SYMBOLS:
    s_all = [m for m in all_moves if m['symbol'] == sym]
    s_run = [m for m in runners if m['symbol'] == sym]
    if not s_all:
        continue
    r_pct = len(s_run) * 100 / len(s_all)
    mfe_r = avg(s_run, lambda m: m['mfe']) if s_run else 0
    p(f"| {sym} | {len(s_all)} | {len(s_run)} | {r_pct:.0f}% | {mfe_r:.2f} |")
p()

# ── Top runners ───────────────────────────────────────────
p("## Top 30 Runners (by MFE)")
p()
p("| Symbol | Date | Time | Dir | Body | Range | Vol | ADX | EMA | VWAP | VDist | 5mPnL | MFE | MAE |")
p("|--------|------|------|-----|------|-------|-----|-----|-----|------|-------|-------|-----|-----|")
for m in sorted(runners, key=lambda x: -x['mfe'])[:30]:
    ema = "✓" if m['ema_aligned'] else "✗"
    vwap = "✓" if m['vwap_aligned'] else "✗"
    d = "▲" if m['direction'] == 'bull' else "▼"
    p(f"| {m['symbol']} | {m['date']} | {m['time']} | {d} | {m['body_pct']}% | {m['range_atr']:.2f} | {m['vol_ratio']:.1f}x | {m['adx']} | {ema} | {vwap} | {m['vwap_dist']:+.2f} | {m['pnl_5m']:+.2f} | {m['mfe']:.2f} | {m['mae']:.2f} |")
p()

# ── Fakeout analysis ──────────────────────────────────────
p("## Top 20 Fakeouts (worst MAE)")
p()
p("| Symbol | Date | Time | Dir | Body | Range | Vol | ADX | EMA | VWAP | VDist | 5mPnL | MFE | MAE |")
p("|--------|------|------|-----|------|-------|-----|-----|-----|------|-------|-------|-----|-----|")
for m in sorted(fakeouts, key=lambda x: x['mae'])[:20]:
    ema = "✓" if m['ema_aligned'] else "✗"
    vwap = "✓" if m['vwap_aligned'] else "✗"
    d = "▲" if m['direction'] == 'bull' else "▼"
    p(f"| {m['symbol']} | {m['date']} | {m['time']} | {d} | {m['body_pct']}% | {m['range_atr']:.2f} | {m['vol_ratio']:.1f}x | {m['adx']} | {ema} | {vwap} | {m['vwap_dist']:+.2f} | {m['pnl_5m']:+.2f} | {m['mfe']:.2f} | {m['mae']:.2f} |")
p()

# ── Time analysis ─────────────────────────────────────────
p("## Runner Rate by Time")
p()
p("| Time | Big Bars | Runners | Runner% | Avg MFE |")
p("|------|----------|---------|---------|---------|")
for tb in ["9:30-10:00", "10:00-11:00", "11:00-12:00", "12:00+"]:
    t_all = [m for m in all_moves if m['time_bucket'] == tb]
    t_run = [m for m in runners if m['time_bucket'] == tb]
    if not t_all:
        continue
    p(f"| {tb} | {len(t_all)} | {len(t_run)} | {len(t_run)*100/len(t_all):.0f}% | {avg(t_all, lambda m: m['mfe']):.2f} |")
p()

# ── 5-minute gate effectiveness ───────────────────────────
p("## 5-Minute Gate: Early P&L Predicts Outcome")
p()
p("| 5min P&L bucket | n | Runner% | Fakeout% | Avg MFE | Avg MAE |")
p("|-----------------|---|---------|----------|---------|---------|")
for lo, hi, label in [(-999, -0.05, "< -0.05"), (-0.05, 0, "-0.05 to 0"), (0, 0.05, "0 to +0.05"), (0.05, 0.15, "+0.05 to +0.15"), (0.15, 999, "> +0.15")]:
    bucket = [m for m in all_moves if lo <= m['pnl_5m'] < hi]
    if not bucket:
        continue
    r = sum(1 for m in bucket if m['mfe'] > 0.3) * 100 / len(bucket)
    f = sum(1 for m in bucket if m['mfe'] < 0.1 and m['mae'] < -0.15) * 100 / len(bucket)
    p(f"| {label} | {len(bucket)} | {r:.0f}% | {f:.0f}% | {avg(bucket, lambda m: m['mfe']):.2f} | {avg(bucket, lambda m: m['mae']):.2f} |")
p()

# ── VWAP distance analysis ────────────────────────────────
p("## VWAP Distance: How Far From VWAP Matters")
p()
p("| VWAP Distance (ATR) | n | Runner% | Avg MFE | Interpretation |")
p("|---------------------|---|---------|---------|----------------|")
for lo, hi, label, interp in [
    (-999, -0.3, "Far below (<-0.3)", "Extended short"),
    (-0.3, -0.1, "Below (-0.3 to -0.1)", "Bearish, near VWAP"),
    (-0.1, 0.1, "At VWAP (±0.1)", "Inflection zone"),
    (0.1, 0.3, "Above (0.1 to 0.3)", "Bullish, near VWAP"),
    (0.3, 999, "Far above (>0.3)", "Extended long"),
]:
    bucket = [m for m in all_moves if lo <= m['vwap_dist'] < hi]
    if len(bucket) < 5:
        continue
    r = sum(1 for m in bucket if m['mfe'] > 0.3) * 100 / len(bucket)
    mfe = avg(bucket, lambda m: m['mfe'])
    p(f"| {label} | {len(bucket)} | {r:.0f}% | {mfe:.2f} | {interp} |")
p()

# ── Key findings ──────────────────────────────────────────
p("## Key Findings")
p()

# Strongest differentiators
diffs = []
for name, fn in pct_metrics:
    r = pct(runners, fn)
    f = pct(fakeouts, fn)
    gap = r - f
    diffs.append((abs(gap), name, r, f, gap))
diffs.sort(reverse=True)
p("### Strongest Differentiators (Runner vs Fakeout)")
p()
for delta, name, r, f, gap in diffs[:10]:
    direction = "Runners higher" if gap > 0 else "Fakeouts higher"
    p(f"- **{name}**: Runners {r:.0f}% vs Fakeouts {f:.0f}% (gap: {gap:+.0f}%) — {direction}")

# Write output
output_path = os.path.join(BASE, "big-move-fingerprint.md")
with open(output_path, 'w') as f:
    f.write('\n'.join(out))
print(f"\nWritten to {output_path}", file=sys.stderr)

# Also save moves as CSV
csv_path = os.path.join(BASE, "big-moves.csv")
pd.DataFrame(all_moves).drop(columns=['dt']).to_csv(csv_path, index=False)
print(f"Moves saved to {csv_path} ({len(all_moves)} rows)", file=sys.stderr)
