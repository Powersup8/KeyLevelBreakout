"""
Multi-Symbol Good Trade Fingerprint Analysis
Uses Pine logs (13 symbols) + 5m cache for indicators + 5s parquet for MFE/MAE
"""
import csv, re, os, sys, numpy as np
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(BASE))), "trading_bot", "cache")

FILE_SYMBOL_MAP = {
    "82a0f": "SPY", "42d0e": "AAPL", "842b7": "AMD", "95b93": "AMZN",
    "1d173": "GLD", "51c09": "GOOGL", "484bf": "META", "493eb": "MSFT",
    "7759b": "NVDA", "4e835": "QQQ", "65f3b": "SLV", "83e42": "TSLA", "369c4": "TSM",
}
SYMBOLS = list(set(FILE_SYMBOL_MAP.values()))
ET = timezone(timedelta(hours=-5))

# ── Load 5s candle data ──────────────────────────────────
def load_5s(symbol):
    fpath = os.path.join(CACHE, "bars_highres", "5sec", f"{symbol.lower()}_5_secs_ib.parquet")
    if not os.path.exists(fpath):
        return None
    df = pd.read_parquet(fpath)
    df['date'] = pd.to_datetime(df['date'], utc=True).dt.tz_convert('US/Eastern')
    df = df.set_index('date').sort_index()
    return df

# ── Load 5m candle data + compute indicators ─────────────
def load_5m(symbol):
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
    # Body %
    rng = df['high'] - df['low']
    df['body_pct'] = (np.abs(df['close'] - df['open']) / rng.replace(0, np.nan) * 100).fillna(0).astype(int)
    # EMA 20 / 50
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    # ADX 14
    df['adx'] = compute_adx(df, 14)
    # Daily VWAP (reset each day)
    df['cum_vol'] = df.groupby(df.index.date)['volume'].cumsum()
    df['cum_vp'] = df.groupby(df.index.date).apply(
        lambda g: (g['close'] * g['volume']).cumsum()
    ).droplevel(0)
    df['vwap'] = df['cum_vp'] / df['cum_vol'].replace(0, np.nan)
    return df

def compute_adx(df, period=14):
    """Compute ADX from OHLC data using Wilder smoothing."""
    h, l, c = df['high'], df['low'], df['close']
    prev_h, prev_l, prev_c = h.shift(1), l.shift(1), c.shift(1)
    tr = pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    plus_dm = np.where((h - prev_h > prev_l - l) & (h - prev_h > 0), h - prev_h, 0)
    minus_dm = np.where((prev_l - l > h - prev_h) & (prev_l - l > 0), prev_l - l, 0)
    # Wilder smoothing
    atr = pd.Series(tr, index=df.index).ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1/period, adjust=False).mean() / atr
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1/period, adjust=False).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    return adx.fillna(0).astype(int)

def lookup_5m(df5m, sig_dt):
    """Look up 5m bar at or just before signal time, return indicator values."""
    if df5m is None:
        return {}
    # Signal bar: find the 5m bar at or just before this time
    mask = df5m.index <= sig_dt
    if mask.sum() == 0:
        return {}
    bar = df5m.loc[mask].iloc[-1]
    return {
        'c_body': int(bar['body_pct']),
        'c_adx': int(bar['adx']),
        'c_ema20': bar['ema20'],
        'c_ema50': bar['ema50'],
        'c_close': bar['close'],
        'c_vwap': bar.get('vwap', np.nan),
    }

def compute_rs(spy_5m, stock_5m, sig_dt):
    """Compute RS = stock intraday % change - SPY intraday % change at signal time."""
    if spy_5m is None or stock_5m is None:
        return 0.0
    day = sig_dt.date()
    # Get day's open for both
    spy_day = spy_5m.loc[spy_5m.index.date == day]
    stk_day = stock_5m.loc[stock_5m.index.date == day]
    if len(spy_day) == 0 or len(stk_day) == 0:
        return 0.0
    spy_open = spy_day.iloc[0]['open']
    stk_open = stk_day.iloc[0]['open']
    # Get price at signal time
    spy_at = spy_day.loc[spy_day.index <= sig_dt]
    stk_at = stk_day.loc[stk_day.index <= sig_dt]
    if len(spy_at) == 0 or len(stk_at) == 0:
        return 0.0
    spy_pct = (spy_at.iloc[-1]['close'] / spy_open - 1) * 100
    stk_pct = (stk_at.iloc[-1]['close'] / stk_open - 1) * 100
    return stk_pct - spy_pct

def measure_mfe_mae_5s(df, entry_time, direction, entry_price, atr, minutes=60):
    if df is None or atr <= 0:
        return 0, 0
    start = entry_time + timedelta(seconds=5)
    end = entry_time + timedelta(minutes=minutes)
    mask = (df.index >= start) & (df.index <= end)
    window = df.loc[mask]
    if len(window) == 0:
        return 0, 0
    if direction == "bull":
        mfe = (window['high'].max() - entry_price) / atr
        mae = (window['low'].min() - entry_price) / atr
    else:
        mfe = (entry_price - window['low'].min()) / atr
        mae = (entry_price - window['high'].max()) / atr
    return mfe, mae

# ── Parse Pine log signals ────────────────────────────────
def parse_pine_log(fpath, symbol):
    signals = []
    conf_results = {}
    with open(fpath) as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) < 2:
                continue
            dt = datetime.fromisoformat(row[0])
            msg = row[1]
            
            if "CONF" in msg and "→" in msg:
                date_key = dt.strftime("%Y-%m-%d")
                direction = "bull" if "▲" in msg else "bear"
                result = "✓★" if "✓★" in msg else "✓" if "✓" in msg else "✗"
                conf_results[(date_key, direction)] = result
                continue
            
            if "◆" in msg and "BRK" not in msg:
                continue
            
            m_dir = "bull" if "▲" in msg else "bear" if "▼" in msg else None
            if not m_dir:
                continue
            m_type = "BRK" if "BRK" in msg else "REV" if ("~ " in msg or "~~" in msg) else None
            if not m_type:
                continue
            
            vol_m = re.search(r'vol=(\d+\.?\d*)x', msg)
            pos_m = re.search(r'pos=([v^])(\d+)', msg)
            vwap_m = re.search(r'vwap=(\w+)', msg)
            ema_m = re.search(r'ema=(\w+)', msg)
            rs_m = re.search(r'rs=([+-]?\d+\.?\d*)%', msg)
            adx_m = re.search(r'adx=(\d+)', msg)
            body_m = re.search(r'body=(\d+)%', msg)
            atr_m = re.search(r'ATR=(\d+\.?\d*)', msg)
            ohlc_m = re.search(r'O(\d+\.?\d*) H(\d+\.?\d*) L(\d+\.?\d*) C(\d+\.?\d*)', msg)
            
            levels = []
            for lvl in ["PM H", "PM L", "Yest H", "Yest L", "Week H", "Week L", "ORB H", "ORB L"]:
                if lvl in msg:
                    levels.append(lvl)
            
            hour = dt.hour
            minute = dt.minute
            total_min = hour * 60 + minute
            if total_min < 600:
                time_bucket = "9:30-10:00"
            elif total_min < 660:
                time_bucket = "10:00-11:00"
            elif total_min < 720:
                time_bucket = "11:00-12:00"
            else:
                time_bucket = "12:00+"
            
            vol = float(vol_m.group(1)) if vol_m else 0
            
            sig = {
                'symbol': symbol, 'dt': dt, 'date': dt.strftime("%Y-%m-%d"),
                'time': f"{hour}:{minute:02d}", 'direction': m_dir, 'type': m_type,
                'levels': levels, 'vol': vol,
                'pos': int(pos_m.group(2)) if pos_m else 0,
                'vwap': vwap_m.group(1) if vwap_m else "",
                'ema': ema_m.group(1) if ema_m else "",
                'rs': float(rs_m.group(1)) if rs_m else 0,
                'adx': int(adx_m.group(1)) if adx_m else 0,
                'body': int(body_m.group(1)) if body_m else 0,
                'atr': float(atr_m.group(1)) if atr_m else 0,
                'close': float(ohlc_m.group(4)) if ohlc_m else 0,
                'high': float(ohlc_m.group(2)) if ohlc_m else 0,
                'low': float(ohlc_m.group(3)) if ohlc_m else 0,
                'multi_level': len(levels) >= 2,
                'time_bucket': time_bucket,
                'vol_bucket': "<2x" if vol < 2 else "2-5x" if vol <= 5 else "5-10x" if vol <= 10 else "10x+",
                'level_type': "LOW" if any(l.endswith("L") for l in levels) else "HIGH",
                'with_trend': (m_dir == "bull" and vwap_m and vwap_m.group(1) == "above") or 
                              (m_dir == "bear" and vwap_m and vwap_m.group(1) == "below"),
            }
            signals.append(sig)
    
    # Match CONF
    for sig in signals:
        if sig['type'] == 'BRK':
            key = (sig['date'], sig['direction'])
            sig['conf'] = conf_results.get(key)
        else:
            sig['conf'] = None
    
    return signals

# ── Main ──────────────────────────────────────────────────
print("Loading Pine logs...", file=sys.stderr)
all_signals = []
import glob
for fpath in sorted(glob.glob(os.path.join(BASE, "pine-logs-Key Level Breakout_*.csv"))):
    suffix = fpath.split('_')[-1].replace('.csv', '')
    symbol = FILE_SYMBOL_MAP.get(suffix)
    if not symbol:
        continue
    sigs = parse_pine_log(fpath, symbol)
    all_signals.extend(sigs)
    print(f"  {symbol}: {len(sigs)} signals", file=sys.stderr)

print(f"\nTotal: {len(all_signals)} signals across {len(set(s['symbol'] for s in all_signals))} symbols", file=sys.stderr)

# Load 5m data for computed indicators
print("\nLoading 5m candle data (for ADX, EMA, Body, RS)...", file=sys.stderr)
fivem_cache = {}
for sym in SYMBOLS:
    df5 = load_5m(sym)
    if df5 is not None:
        fivem_cache[sym] = df5
        print(f"  {sym}: {len(df5)} bars (5m)", file=sys.stderr)
    else:
        print(f"  {sym}: NO 5m DATA", file=sys.stderr)

spy_5m = fivem_cache.get("SPY")

# Enrich signals with computed indicators
print("\nEnriching signals with 5m indicators...", file=sys.stderr)
for sig in all_signals:
    df5 = fivem_cache.get(sig['symbol'])
    vals = lookup_5m(df5, sig['dt'])
    if vals:
        # Use computed values if Pine log had 0 (old format)
        if sig['body'] == 0:
            sig['body'] = vals.get('c_body', 0)
        if sig['adx'] == 0:
            sig['adx'] = vals.get('c_adx', 0)
        # EMA alignment: check if close is on the right side of both EMAs
        c = vals.get('c_close', 0)
        e20 = vals.get('c_ema20', 0)
        e50 = vals.get('c_ema50', 0)
        if sig['ema'] == "" and c and e20 and e50:
            if c > e20 and c > e50:
                sig['ema'] = "bull"
            elif c < e20 and c < e50:
                sig['ema'] = "bear"
            else:
                sig['ema'] = "mixed"
        # VWAP from 5m data if missing
        vwap = vals.get('c_vwap', np.nan)
        if sig['vwap'] == "" and not np.isnan(vwap) and c:
            sig['vwap'] = "above" if c > vwap else "below"
            sig['with_trend'] = (sig['direction'] == "bull" and sig['vwap'] == "above") or \
                                (sig['direction'] == "bear" and sig['vwap'] == "below")
        # RS vs SPY
        if sig['rs'] == 0 and sig['symbol'] not in ("SPY", "QQQ", "GLD", "SLV"):
            sig['rs'] = compute_rs(spy_5m, df5, sig['dt'])

# Load 5s data and measure MFE/MAE
print("\nLoading 5s candle data...", file=sys.stderr)
candle_cache = {}
for sym in set(s['symbol'] for s in all_signals):
    df = load_5s(sym)
    if df is not None:
        candle_cache[sym] = df
        print(f"  {sym}: {len(df)} bars (5s)", file=sys.stderr)
    else:
        print(f"  {sym}: NO 5s DATA", file=sys.stderr)

print("\nMeasuring MFE/MAE...", file=sys.stderr)
for sig in all_signals:
    df = candle_cache.get(sig['symbol'])
    if df is not None:
        mfe, mae = measure_mfe_mae_5s(df, sig['dt'], sig['direction'], sig['close'], sig['atr'], minutes=60)
        sig['mfe'] = mfe
        sig['mae'] = mae
    else:
        sig['mfe'] = 0
        sig['mae'] = 0

# ── Analysis ──────────────────────────────────────────────
out = []
def p(s=""):
    out.append(s)

good = [s for s in all_signals if s['conf'] in ('✓', '✓★')]
bad = [s for s in all_signals if s['conf'] == '✗']
revs = [s for s in all_signals if s['type'] == 'REV']

p("# Multi-Symbol Good Trade Fingerprint — 13 Symbols")
p(f"Data: {len(all_signals)} signals, {len(good)} CONF ✓/✓★, {len(bad)} CONF ✗, {len(revs)} reversals")
p(f"Symbols: {', '.join(sorted(set(s['symbol'] for s in all_signals)))}")
p(f"5s MFE/MAE coverage: {len(candle_cache)}/{len(set(s['symbol'] for s in all_signals))} symbols")
p()

# ── Good vs Bad comparison table ──────────────────────────
def pct(sigs, fn):
    return sum(1 for s in sigs if fn(s)) * 100 / len(sigs) if sigs else 0
def avg(sigs, fn):
    return sum(fn(s) for s in sigs) / len(sigs) if sigs else 0

p("## Fingerprint: Good vs Bad Breakouts")
p()
p("| Metric | GOOD (n={}) | BAD (n={}) | Delta |".format(len(good), len(bad)))
p("|--------|------------|-----------|-------|")

metrics = [
    ("Avg Volume (x)", lambda s: s['vol']),
    ("Avg Body %", lambda s: s['body']),
    ("Avg ADX", lambda s: s['adx']),
    ("Avg RS %", lambda s: s['rs']),
    ("Avg MFE (ATR, 60m)", lambda s: s['mfe']),
    ("Avg MAE (ATR, 60m)", lambda s: s['mae']),
]
for name, fn in metrics:
    g = avg(good, fn)
    b = avg(bad, fn)
    p(f"| {name} | {g:.1f} | {b:.1f} | {g-b:+.1f} |")

pct_metrics = [
    ("VWAP aligned", lambda s: s['with_trend']),
    ("EMA aligned", lambda s: (s['direction']=='bull' and s['ema']=='bull') or (s['direction']=='bear' and s['ema']=='bear')),
    ("ADX ≥ 25", lambda s: s['adx'] >= 25),
    ("ADX ≥ 35", lambda s: s['adx'] >= 35),
    ("Body ≥ 70%", lambda s: s['body'] >= 70),
    ("Vol 2-5x", lambda s: 2 <= s['vol'] <= 5),
    ("Vol ≥ 5x", lambda s: s['vol'] >= 5),
    ("Multi-level", lambda s: s['multi_level']),
    ("Before 11:00", lambda s: s['time_bucket'] in ('9:30-10:00', '10:00-11:00')),
    ("9:30-10:00", lambda s: s['time_bucket'] == '9:30-10:00'),
    ("LOW levels", lambda s: s['level_type'] == 'LOW'),
    ("Bear direction", lambda s: s['direction'] == 'bear'),
]
for name, fn in pct_metrics:
    g = pct(good, fn)
    b = pct(bad, fn)
    p(f"| {name} % | {g:.0f}% | {b:.0f}% | {g-b:+.0f}% |")
p()

# ── By symbol ────────────────────────────────────────────
p("## CONF Rate by Symbol")
p()
p("| Symbol | Signals | Good | Bad | CONF Rate | Avg MFE (good) | Avg MAE (good) |")
p("|--------|---------|------|-----|-----------|----------------|----------------|")
for sym in sorted(set(s['symbol'] for s in all_signals)):
    sym_good = [s for s in good if s['symbol'] == sym]
    sym_bad = [s for s in bad if s['symbol'] == sym]
    total = len(sym_good) + len(sym_bad)
    rate = len(sym_good) * 100 / total if total else 0
    mfe_g = avg(sym_good, lambda s: s['mfe']) if sym_good else 0
    mae_g = avg(sym_good, lambda s: s['mae']) if sym_good else 0
    p(f"| {sym} | {total} | {len(sym_good)} | {len(sym_bad)} | {rate:.0f}% | {mfe_g:.2f} | {mae_g:.2f} |")
p()

# ── Time analysis ─────────────────────────────────────────
p("## CONF Rate by Time Bucket")
p()
p("| Time | Good | Bad | CONF Rate | Avg MFE (good) |")
p("|------|------|-----|-----------|----------------|")
for tb in ["9:30-10:00", "10:00-11:00", "11:00-12:00", "12:00+"]:
    tb_good = [s for s in good if s['time_bucket'] == tb]
    tb_bad = [s for s in bad if s['time_bucket'] == tb]
    total = len(tb_good) + len(tb_bad)
    rate = len(tb_good) * 100 / total if total else 0
    mfe_g = avg(tb_good, lambda s: s['mfe']) if tb_good else 0
    p(f"| {tb} | {len(tb_good)} | {len(tb_bad)} | {rate:.0f}% | {mfe_g:.2f} |")
p()

# ── Volume analysis ───────────────────────────────────────
p("## CONF Rate by Volume Bucket")
p()
p("| Volume | Good | Bad | CONF Rate | Avg MFE (good) |")
p("|--------|------|-----|-----------|----------------|")
for vb in ["<2x", "2-5x", "5-10x", "10x+"]:
    vb_good = [s for s in good if s['vol_bucket'] == vb]
    vb_bad = [s for s in bad if s['vol_bucket'] == vb]
    total = len(vb_good) + len(vb_bad)
    rate = len(vb_good) * 100 / total if total else 0
    mfe_g = avg(vb_good, lambda s: s['mfe']) if vb_good else 0
    p(f"| {vb} | {len(vb_good)} | {len(vb_bad)} | {rate:.0f}% | {mfe_g:.2f} |")
p()

# ── Level type analysis ──────────────────────────────────
p("## CONF Rate by Level Type")
p()
level_counts = defaultdict(lambda: {'good': 0, 'bad': 0, 'mfe': []})
for s in good:
    for l in s['levels']:
        level_counts[l]['good'] += 1
        level_counts[l]['mfe'].append(s['mfe'])
for s in bad:
    for l in s['levels']:
        level_counts[l]['bad'] += 1

p("| Level | Good | Bad | CONF Rate | Avg MFE (good) |")
p("|-------|------|-----|-----------|----------------|")
for lvl in ["PM H", "PM L", "Yest H", "Yest L", "Week H", "Week L", "ORB H", "ORB L"]:
    lc = level_counts[lvl]
    total = lc['good'] + lc['bad']
    rate = lc['good'] * 100 / total if total else 0
    mfe = sum(lc['mfe']) / len(lc['mfe']) if lc['mfe'] else 0
    p(f"| {lvl} | {lc['good']} | {lc['bad']} | {rate:.0f}% | {mfe:.2f} |")
p()

# ── ADX analysis ─────────────────────────────────────────
p("## CONF Rate by ADX Range")
p()
p("| ADX | Good | Bad | CONF Rate | Avg MFE (good) |")
p("|-----|------|-----|-----------|----------------|")
for lo, hi, label in [(0, 20, "<20"), (20, 25, "20-25"), (25, 30, "25-30"), (30, 35, "30-35"), (35, 50, "35-50"), (50, 999, "50+")]:
    ag = [s for s in good if lo <= s['adx'] < hi]
    ab = [s for s in bad if lo <= s['adx'] < hi]
    total = len(ag) + len(ab)
    rate = len(ag) * 100 / total if total else 0
    mfe = avg(ag, lambda s: s['mfe']) if ag else 0
    p(f"| {label} | {len(ag)} | {len(ab)} | {rate:.0f}% | {mfe:.2f} |")
p()

# ── Individual good trades ────────────────────────────────
p("## All Good Trades (sorted by MFE)")
p()
p("| Symbol | Date | Time | Dir | Levels | Vol | Body | ADX | VWAP | EMA | RS | MFE | MAE |")
p("|--------|------|------|-----|--------|-----|------|-----|------|-----|----|-----|-----|")
for s in sorted(good, key=lambda x: -x['mfe']):
    p(f"| {s['symbol']} | {s['date']} | {s['time']} | {'▲' if s['direction']=='bull' else '▼'} | {'+'.join(s['levels'])} | {s['vol']:.1f}x | {s['body']}% | {s['adx']} | {s['vwap']} | {s['ema']} | {s['rs']:+.1f}% | {s['mfe']:.2f} | {s['mae']:.2f} |")
p()

# ── Reversal analysis ────────────────────────────────────
p("## Reversal Signal Analysis (no CONF, measured by MFE)")
p()
good_rev = [s for s in revs if s['mfe'] > 0.3]
bad_rev = [s for s in revs if s['mfe'] < 0.1 and s['mae'] < -0.15]
p(f"Good reversals (MFE > 0.3 ATR): {len(good_rev)}")
p(f"Bad reversals (MFE < 0.1, MAE < -0.15): {len(bad_rev)}")
p()
if good_rev:
    p("### Top Reversals by MFE")
    p()
    p("| Symbol | Date | Time | Dir | Levels | Vol | Body | ADX | MFE | MAE |")
    p("|--------|------|------|-----|--------|-----|------|-----|-----|-----|")
    for s in sorted(good_rev, key=lambda x: -x['mfe'])[:15]:
        p(f"| {s['symbol']} | {s['date']} | {s['time']} | {'▲' if s['direction']=='bull' else '▼'} | {'+'.join(s['levels'])} | {s['vol']:.1f}x | {s['body']}% | {s['adx']} | {s['mfe']:.2f} | {s['mae']:.2f} |")
p()

# ── Key findings ──────────────────────────────────────────
p("## Key Findings")
p()
# Strongest differentiators
diffs = []
for name, fn in pct_metrics:
    g = pct(good, fn)
    b = pct(bad, fn)
    diffs.append((abs(g-b), name, g, b))
diffs.sort(reverse=True)
p("### Strongest Differentiators (by absolute gap)")
p()
for delta, name, g, b in diffs[:8]:
    p(f"- **{name}**: GOOD {g:.0f}% vs BAD {b:.0f}% (gap: {delta:.0f}%)")

output_path = os.path.join(BASE, "multi-symbol-fingerprint.md")
with open(output_path, 'w') as f:
    f.write('\n'.join(out))
print(f"\nWritten to {output_path}", file=sys.stderr)

# ── Export enriched signals as CSV for reuse ─────────────
csv_path = os.path.join(BASE, "enriched-signals.csv")
rows = []
for s in all_signals:
    rows.append({
        'symbol': s['symbol'], 'date': s['date'], 'time': s['time'],
        'direction': s['direction'], 'type': s['type'],
        'levels': '+'.join(s['levels']), 'vol': s['vol'],
        'body': s['body'], 'adx': s['adx'],
        'vwap': s['vwap'], 'ema': s['ema'], 'rs': round(s['rs'], 2),
        'atr': s['atr'], 'close': s['close'],
        'multi_level': s['multi_level'], 'with_trend': s['with_trend'],
        'conf': s.get('conf', ''), 'mfe': round(s['mfe'], 3), 'mae': round(s['mae'], 3),
        'time_bucket': s['time_bucket'], 'vol_bucket': s['vol_bucket'],
        'level_type': s['level_type'],
    })
pd.DataFrame(rows).to_csv(csv_path, index=False)
print(f"Enriched signals saved to {csv_path} ({len(rows)} rows)", file=sys.stderr)
