"""
v3.0 Deep Analysis — Cross-check pine logs against 10sec market data
Fixed: symbol matching (use latest date OHLC), timezone alignment, PnL computation
"""
import pandas as pd
import numpy as np
import csv
import re
import os
from pathlib import Path
from datetime import datetime, timedelta
import pytz
import warnings
warnings.filterwarnings('ignore')

ET = pytz.timezone('US/Eastern')

BASE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView")
DEBUG = BASE / "debug"
CACHE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache")
BARS_10S = CACHE / "bars_highres" / "10sec"

SYMBOLS = ['AAPL','AMD','AMZN','GLD','GOOGL','META','MSFT','NVDA','QQQ','SLV','SPY','TSLA','TSM']

# ── 1. Load 10sec market data ──
print("=" * 70)
print("LOADING 10-SEC MARKET DATA")
print("=" * 70)

market = {}
for sym in SYMBOLS:
    fp = BARS_10S / f"{sym.lower()}_10_secs_ib.parquet"
    if fp.exists():
        df = pd.read_parquet(fp)
        df['date'] = pd.to_datetime(df['date'], utc=True).dt.tz_convert('US/Eastern')
        df = df.set_index('date').sort_index()
        market[sym] = df
        print(f"  {sym}: {len(df):>6} bars, {df.index[0].date()} → {df.index[-1].date()}")

# ── 2. Parse v3.0 pine logs ──
print("\n" + "=" * 70)
print("PARSING v3.0 PINE LOGS")
print("=" * 70)

log_files = sorted(DEBUG.glob("pine-logs-Key Level Breakout v3.0b_*.csv"))
print(f"Found {len(log_files)} log files")

sig_pat = re.compile(
    r'\[KLB\]\s+(\d+:\d+)\s+(▲|▼)\s+'
    r'(BRK|~\s*~|~~\s*~*|◆[^◆]*)\s+'
    r'(.+?)\s+vol=([\d.]+)x\s+pos=([v^]\d+)\s+'
    r'vwap=(above|below)\s+ema=(bull|bear)\s+'
    r'rs=([+\-\d.]+)%\s+adx=(\d+)\s+body=(\d+)%\s+'
    r'ramp=([\d.]+)x\s+rangeATR=([\d.]+)\s*'
    r'(⚡)?\s*(⚠)?\s*'
    r'O([\d.]+)\s+H([\d.]+)\s+L([\d.]+)\s+C([\d.]+)\s+'
    r'ATR=([\d.]+)'
)
# FADE: "[KLB] 14:25 ▲ FADE at 684.83"
fade_pat = re.compile(r'\[KLB\]\s+(\d+:\d+)\s+(▲|▼)\s+FADE\s+at\s+([\d.]+)')
# RNG: "[KLB] 9:35 ▲ RNG range break vol=12.7x"
rng_pat = re.compile(r'\[KLB\]\s+(\d+:\d+)\s+(▲|▼)\s+RNG\s+range\s+break\s+vol=([\d.]+)x')
conf_pat = re.compile(r'\[KLB\]\s+CONF\s+(\d+:\d+)\s+(▲|▼)\s+(BRK|QBS|FADE|RNG)\s+→\s+(✓|✗|✓★)(?:\s*\((.+?)\))?')
check_pat = re.compile(r'\[KLB\]\s+5m CHECK\s+(\d+:\d+)\s+(▲|▼)\s+pnl=([-\d.]+)\s+→\s+(HOLD|BAIL)')

all_signals = []
all_confs = []
all_checks = []

for lf in log_files:
    file_id = lf.stem.split('_')[-1]
    with open(lf) as fh:
        reader = csv.reader(fh)
        next(reader)
        for row in reader:
            if len(row) < 2:
                continue
            ts_str, msg = row[0], row[1]
            try:
                ts = pd.Timestamp(ts_str)
                if ts.tzinfo is not None:
                    ts = ts.tz_convert('US/Eastern')
                else:
                    ts = ts.tz_localize('US/Eastern')
            except:
                continue

            date_str = ts.strftime('%Y-%m-%d')

            m = sig_pat.search(msg)
            if m:
                sig_type_raw = m.group(3).strip()
                if sig_type_raw.startswith('~ ~'):
                    sig_type = 'REV'
                elif sig_type_raw.startswith('~~'):
                    sig_type = 'RCL'
                elif sig_type_raw.startswith('◆'):
                    sig_type = 'RET'
                else:
                    sig_type = sig_type_raw

                all_signals.append({
                    'file_id': file_id,
                    'date': date_str,
                    'time': m.group(1),
                    'ts': ts,
                    'dir': 'bull' if m.group(2) == '▲' else 'bear',
                    'type': sig_type,
                    'levels': m.group(4).strip(),
                    'vol': float(m.group(5)),
                    'closePos': int(m.group(6)[1:]),
                    'vwap': m.group(7),
                    'ema': m.group(8),
                    'rs': float(m.group(9)),
                    'adx': int(m.group(10)),
                    'body': int(m.group(11)),
                    'ramp': float(m.group(12)),
                    'rangeATR': float(m.group(13)),
                    'bigMove': m.group(14) == '⚡' if m.group(14) else False,
                    'bodyWarn': m.group(15) == '⚠' if m.group(15) else False,
                    'open': float(m.group(16)),
                    'high': float(m.group(17)),
                    'low': float(m.group(18)),
                    'close': float(m.group(19)),
                    'atr': float(m.group(20)),
                })
                continue

            # FADE signals have minimal log format
            fm = fade_pat.search(msg)
            if fm:
                fade_price = float(fm.group(3))
                all_signals.append({
                    'file_id': file_id, 'date': date_str, 'time': fm.group(1),
                    'ts': ts, 'dir': 'bull' if fm.group(2) == '▲' else 'bear',
                    'type': 'FADE', 'levels': 'FADE', 'vol': 0, 'closePos': 50,
                    'vwap': '', 'ema': '', 'rs': 0, 'adx': 0, 'body': 0,
                    'ramp': 0, 'rangeATR': 0, 'bigMove': False, 'bodyWarn': False,
                    'open': fade_price, 'high': fade_price, 'low': fade_price,
                    'close': fade_price, 'atr': 0,
                })
                continue

            # RNG signals have minimal log format
            rm = rng_pat.search(msg)
            if rm:
                all_signals.append({
                    'file_id': file_id, 'date': date_str, 'time': rm.group(1),
                    'ts': ts, 'dir': 'bull' if rm.group(2) == '▲' else 'bear',
                    'type': 'RNG', 'levels': 'RNG', 'vol': float(rm.group(3)),
                    'closePos': 50, 'vwap': '', 'ema': '', 'rs': 0, 'adx': 0,
                    'body': 0, 'ramp': 0, 'rangeATR': 0, 'bigMove': False,
                    'bodyWarn': False, 'open': 0, 'high': 0, 'low': 0,
                    'close': 0, 'atr': 0,
                })
                continue

            cm = conf_pat.search(msg)
            if cm:
                all_confs.append({
                    'file_id': file_id,
                    'date': date_str,
                    'time': cm.group(1),
                    'ts': ts,
                    'dir': 'bull' if cm.group(2) == '▲' else 'bear',
                    'type': cm.group(3),
                    'result': cm.group(4),
                    'note': cm.group(5) or '',
                })
                continue

            chm = check_pat.search(msg)
            if chm:
                all_checks.append({
                    'file_id': file_id,
                    'date': date_str,
                    'time': chm.group(1),
                    'ts': ts,
                    'dir': 'bull' if chm.group(2) == '▲' else 'bear',
                    'pnl': float(chm.group(3)),
                    'result': chm.group(4),
                })

sigs = pd.DataFrame(all_signals)
confs = pd.DataFrame(all_confs)
checks = pd.DataFrame(all_checks)
print(f"\nParsed: {len(sigs)} signals, {len(confs)} CONFs, {len(checks)} 5m checks")

# ── 3. Smart symbol matching ──
print("\n" + "=" * 70)
print("IDENTIFYING SYMBOLS")
print("=" * 70)

# Use March 4 (latest date all symbols have) signals from each file
# Match close price against 10sec data close prices at that exact time
file_symbols = {}
for fid in sigs['file_id'].unique():
    fsigs = sigs[sigs['file_id'] == fid]
    # Use only standard signals (with close > 0) for matching
    std_sigs = fsigs[fsigs['close'] > 0]
    if len(std_sigs) == 0:
        file_symbols[fid] = None
        continue
    latest_date = std_sigs['date'].max()
    latest_sigs = std_sigs[std_sigs['date'] == latest_date]
    if len(latest_sigs) == 0:
        file_symbols[fid] = None
        continue

    sample = latest_sigs.iloc[0]
    sample_close = sample['close']
    sample_ts = sample['ts']

    best_sym = None
    best_dist = float('inf')
    for sym, mdf in market.items():
        # Look for bars within 10 min of signal time
        t0 = sample_ts - timedelta(minutes=10)
        t1 = sample_ts + timedelta(minutes=10)
        nearby = mdf[(mdf.index >= t0) & (mdf.index <= t1)]
        if len(nearby) > 0:
            # Find closest close price
            dist = abs(nearby['close'] - sample_close).min()
            pct_dist = dist / sample_close
            if pct_dist < best_dist:
                best_dist = pct_dist
                best_sym = sym

    file_symbols[fid] = best_sym
    n = len(fsigs)
    sym_str = best_sym if best_sym else '???'
    print(f"  {fid} → {sym_str:5s} ({n:3d} sigs, latest={latest_date}, "
          f"close=${sample_close:.2f}, match={best_dist:.6f})")

sigs['symbol'] = sigs['file_id'].map(file_symbols)
confs['symbol'] = confs['file_id'].map(file_symbols)
checks['symbol'] = checks['file_id'].map(file_symbols)

# ── 4. Overview ──
print("\n" + "=" * 70)
print("v3.0 SIGNAL OVERVIEW")
print("=" * 70)

print(f"\nTotal signals: {len(sigs)}")
print(f"Date range: {sigs['date'].min()} → {sigs['date'].max()}")
print(f"Days: {sigs['date'].nunique()}")
syms = sorted(sigs['symbol'].dropna().unique())
print(f"Symbols: {len(syms)} ({', '.join(syms)})")

print(f"\nPer day: {len(sigs)/sigs['date'].nunique():.1f} signals/day across {len(syms)} symbols "
      f"= {len(sigs)/sigs['date'].nunique()/len(syms):.1f}/day/symbol")

print(f"\n--- By Type ---")
for t in ['BRK', 'REV', 'RCL', 'RET', 'FADE', 'RNG']:
    g = sigs[sigs['type'] == t]
    if len(g) > 0:
        print(f"  {t}: {len(g)} ({100*len(g)/len(sigs):.1f}%)")

print(f"\n--- By Direction ---")
for d in ['bull', 'bear']:
    g = sigs[sigs['dir'] == d]
    print(f"  {d}: {len(g)} ({100*len(g)/len(sigs):.1f}%)")

# New v3.0 features
print(f"\n--- v3.0 New Features ---")
for kw, label in [('PD Mid', 'PD Mid'), ('PD LH', 'PD Last Hr Low'), ('VWAP', 'VWAP zone')]:
    c = sigs[sigs['levels'].str.contains(kw, na=False)]
    print(f"  {label}: {len(c)} signals")

fade = sigs[sigs['type'] == 'FADE']
rng = sigs[sigs['type'] == 'RNG']
print(f"  FADE: {len(fade)}")
print(f"  RNG: {len(rng)}")

auto_c = confs[confs['note'].str.contains('auto-R1', na=False)]
print(f"  Auto-Confirm R1: {len(auto_c)} / {len(confs)} CONFs ({100*len(auto_c)/max(len(confs),1):.0f}%)")

# EMA gate check (exclude FADE/RNG — they bypass EMA gate by design)
std_sigs = sigs[~sigs['type'].isin(['FADE', 'RNG'])]
ema_ok = std_sigs[((std_sigs['dir'] == 'bull') & (std_sigs['ema'] == 'bull')) |
                  ((std_sigs['dir'] == 'bear') & (std_sigs['ema'] == 'bear'))]
ema_bad = std_sigs[~std_sigs.index.isin(ema_ok.index)]
print(f"  EMA-aligned: {len(ema_ok)} ({100*len(ema_ok)/len(sigs):.0f}%)")
print(f"  EMA-misaligned (dimmed pre-9:50): {len(ema_bad)}")
if len(ema_bad) > 0:
    mins = ema_bad['time'].apply(lambda t: int(t.split(':')[0]) * 60 + int(t.split(':')[1]))
    post950 = (mins >= 590).sum()
    if post950 > 0:
        print(f"    ⚠️ {post950} non-EMA signals AFTER 9:50 — EMA gate leak!")
        for _, s in ema_bad[mins >= 590].head(5).iterrows():
            print(f"      {s['symbol']} {s['date']} {s['time']} {s['dir']} {s['type']} "
                  f"ema={s['ema']} levels={s['levels']}")
    else:
        print(f"    ✅ All {len(ema_bad)} are before 9:50 — EMA gate working correctly")

# ── 5. CONF analysis ──
print("\n" + "=" * 70)
print("CONFIRMATION ANALYSIS")
print("=" * 70)

print(f"Total: {len(confs)}")
for r in ['✓', '✓★', '✗']:
    c = confs[confs['result'] == r]
    print(f"  {r}: {len(c)} ({100*len(c)/max(len(confs),1):.0f}%)")

print(f"\nAuto-Confirm R1: {len(auto_c)} (all ✓: {(auto_c['result'] == '✓').all() if len(auto_c) > 0 else 'N/A'})")
manual = confs[~confs['note'].str.contains('auto-R1', na=False)]
if len(manual) > 0:
    print(f"Standard CONF ({len(manual)}):")
    for r in ['✓', '✓★', '✗']:
        c = manual[manual['result'] == r]
        print(f"  {r}: {len(c)} ({100*len(c)/len(manual):.0f}%)")

# ── 6. 5m Check ──
print("\n" + "=" * 70)
print("5-MINUTE CHECK ANALYSIS")
print("=" * 70)

if len(checks) > 0:
    holds = checks[checks['result'] == 'HOLD']
    bails = checks[checks['result'] == 'BAIL']
    print(f"HOLD: {len(holds)} ({100*len(holds)/len(checks):.0f}%) avg pnl={holds['pnl'].mean():.3f}")
    print(f"BAIL: {len(bails)} ({100*len(bails)/len(checks):.0f}%) avg pnl={bails['pnl'].mean():.3f}")

# ── 6b. Enrich FADE/RNG with market data prices ──
print("\nEnriching FADE/RNG signals with market data...")
for idx, row in sigs.iterrows():
    if row['type'] in ('FADE', 'RNG') and (row['close'] == 0 or row['atr'] == 0):
        sym = row.get('symbol')
        if sym and sym in market:
            mdf = market[sym]
            sig_ts = row['ts']
            # Get close from nearest 10sec bar
            nearby = mdf[(mdf.index >= sig_ts - timedelta(seconds=30)) & (mdf.index <= sig_ts + timedelta(seconds=30))]
            if len(nearby) > 0:
                diffs = [(abs((t - sig_ts).total_seconds()), i) for i, t in enumerate(nearby.index)]
                bar = nearby.iloc[min(diffs)[1]]
                if row['close'] == 0:
                    sigs.at[idx, 'close'] = bar['close']
                    sigs.at[idx, 'open'] = bar['open']
                    sigs.at[idx, 'high'] = bar['high']
                    sigs.at[idx, 'low'] = bar['low']
            # Get ATR from nearest standard signal on same day/file
            day_sigs = sigs[(sigs['file_id'] == row['file_id']) & (sigs['date'] == row['date']) & (sigs['atr'] > 0)]
            if len(day_sigs) > 0 and row['atr'] == 0:
                sigs.at[idx, 'atr'] = day_sigs.iloc[0]['atr']
enriched_fade = sigs[(sigs['type'] == 'FADE') & (sigs['close'] > 0)]
enriched_rng = sigs[(sigs['type'] == 'RNG') & (sigs['close'] > 0)]
print(f"  FADE enriched: {len(enriched_fade)} / {len(sigs[sigs['type']=='FADE'])}")
print(f"  RNG enriched: {len(enriched_rng)} / {len(sigs[sigs['type']=='RNG'])}")

# ── 7. Follow-through using 10sec data ──
print("\n" + "=" * 70)
print("FOLLOW-THROUGH (10-sec data)")
print("=" * 70)

def compute_ft(row, mkt):
    sym = row['symbol']
    if sym not in mkt or pd.isna(sym):
        return {}
    mdf = mkt[sym]
    sig_ts = row['ts']
    entry = row['close']
    atr = row['atr']
    d = row['dir']
    if atr <= 0:
        return {}

    results = {}
    for w in [5, 15, 30, 60]:
        end = sig_ts + timedelta(minutes=w)
        wd = mdf[(mdf.index > sig_ts) & (mdf.index <= end)]
        if len(wd) < 3:  # need meaningful data
            continue
        if d == 'bull':
            mfe = (wd['high'].max() - entry) / atr
            mae = (entry - wd['low'].min()) / atr
            pnl = (wd.iloc[-1]['close'] - entry) / atr
        else:
            mfe = (entry - wd['low'].min()) / atr
            mae = (wd['high'].max() - entry) / atr
            pnl = (entry - wd.iloc[-1]['close']) / atr
        # Sanity check: if MFE > 10 ATR in 60 min, data is suspicious
        if mfe > 10:
            continue
        results[f'mfe_{w}'] = round(mfe, 4)
        results[f'mae_{w}'] = round(mae, 4)
        results[f'pnl_{w}'] = round(pnl, 4)
    return results

print("Computing follow-through...")
ft_list = []
for idx, row in sigs.iterrows():
    r = compute_ft(row, market)
    r['idx'] = idx
    ft_list.append(r)
ft_df = pd.DataFrame(ft_list).set_index('idx')
sf = sigs.join(ft_df)

has = sf[sf['pnl_15'].notna()].copy()
print(f"Signals with valid follow-through: {len(has)} / {len(sigs)}")

if len(has) > 0:
    print(f"\n--- Overall ---")
    for w in [5, 15, 30, 60]:
        sub = has[has[f'pnl_{w}'].notna()]
        if len(sub) > 0:
            print(f"  {w}m: N={len(sub):>4}, MFE={sub[f'mfe_{w}'].mean():.3f}, "
                  f"MAE={sub[f'mae_{w}'].mean():.3f}, PnL={sub[f'pnl_{w}'].mean():.3f}, "
                  f"Win%={100*(sub[f'pnl_{w}']>0).mean():.1f}%, Total={sub[f'pnl_{w}'].sum():.1f}")

    print(f"\n--- By Type ---")
    for t in ['BRK', 'REV', 'RCL', 'RET', 'FADE', 'RNG']:
        sub = has[(has['type'] == t) & has['pnl_15'].notna()]
        if len(sub) > 0:
            print(f"  {t}: N={len(sub):>4}, 15m PnL={sub['pnl_15'].mean():+.3f}, "
                  f"Win%={100*(sub['pnl_15']>0).mean():.1f}%, Total={sub['pnl_15'].sum():+.1f}")

    print(f"\n--- By Direction ---")
    for d in ['bull', 'bear']:
        sub = has[(has['dir'] == d) & has['pnl_15'].notna()]
        if len(sub) > 0:
            print(f"  {d}: N={len(sub):>4}, 15m PnL={sub['pnl_15'].mean():+.3f}, "
                  f"Win%={100*(sub['pnl_15']>0).mean():.1f}%, Total={sub['pnl_15'].sum():+.1f}")

    print(f"\n--- By EMA Alignment ---")
    has['ema_match'] = ((has['dir'] == 'bull') & (has['ema'] == 'bull')) | \
                       ((has['dir'] == 'bear') & (has['ema'] == 'bear'))
    for match, label in [(True, 'EMA-Aligned'), (False, 'EMA-Misaligned')]:
        sub = has[(has['ema_match'] == match) & has['pnl_15'].notna()]
        if len(sub) > 0:
            print(f"  {label}: N={len(sub):>4}, 15m PnL={sub['pnl_15'].mean():+.3f}, "
                  f"Win%={100*(sub['pnl_15']>0).mean():.1f}%, Total={sub['pnl_15'].sum():+.1f}")

    print(f"\n--- v3.0 New Levels ---")
    for kw, label in [('PD Mid', 'PD Mid'), ('PD LH', 'PD Last Hr Low'), ('VWAP', 'VWAP zone')]:
        sub = has[has['levels'].str.contains(kw, na=False) & has['pnl_15'].notna()]
        if len(sub) > 0:
            print(f"  {label}: N={len(sub):>3}, 15m PnL={sub['pnl_15'].mean():+.3f}, "
                  f"Win%={100*(sub['pnl_15']>0).mean():.1f}%, Total={sub['pnl_15'].sum():+.1f}")
        else:
            print(f"  {label}: 0 with follow-through data")

    # Original levels for comparison
    print(f"\n--- Original Levels ---")
    for kw, label in [('PM ', 'Premarket'), ('Yest', 'Yesterday'), ('ORB', 'ORB'), ('Week', 'Week')]:
        sub = has[has['levels'].str.contains(kw, na=False) & has['pnl_15'].notna()]
        if len(sub) > 0:
            print(f"  {label}: N={len(sub):>3}, 15m PnL={sub['pnl_15'].mean():+.3f}, "
                  f"Win%={100*(sub['pnl_15']>0).mean():.1f}%, Total={sub['pnl_15'].sum():+.1f}")

    print(f"\n--- By Time ---")
    has['mins'] = has['time'].apply(lambda t: int(t.split(':')[0]) * 60 + int(t.split(':')[1]))
    for lo, hi, label in [(570, 600, '9:30-10'), (600, 660, '10-11'), (660, 720, '11-12'), (720, 960, '12+')]:
        sub = has[(has['mins'] >= lo) & (has['mins'] < hi) & has['pnl_15'].notna()]
        if len(sub) > 0:
            print(f"  {label}: N={len(sub):>4}, 15m PnL={sub['pnl_15'].mean():+.3f}, "
                  f"Win%={100*(sub['pnl_15']>0).mean():.1f}%, Total={sub['pnl_15'].sum():+.1f}")

    print(f"\n--- By Symbol ---")
    for sym in sorted(has['symbol'].dropna().unique()):
        sub = has[(has['symbol'] == sym) & has['pnl_15'].notna()]
        if len(sub) > 0:
            print(f"  {sym:5s}: N={len(sub):>4}, 15m PnL={sub['pnl_15'].mean():+.3f}, "
                  f"Win%={100*(sub['pnl_15']>0).mean():.1f}%, Total={sub['pnl_15'].sum():+.1f}")

    print(f"\n--- By Volume ---")
    for lo, hi, label in [(0, 1.5, '<1.5x'), (1.5, 3, '1.5-3x'), (3, 5, '3-5x'),
                          (5, 10, '5-10x'), (10, 999, '10x+')]:
        sub = has[(has['vol'] >= lo) & (has['vol'] < hi) & has['pnl_15'].notna()]
        if len(sub) > 0:
            print(f"  {label:7s}: N={len(sub):>4}, 15m PnL={sub['pnl_15'].mean():+.3f}, "
                  f"Win%={100*(sub['pnl_15']>0).mean():.1f}%, Total={sub['pnl_15'].sum():+.1f}")

    # Regime
    print(f"\n--- Regime Score ---")
    has['vwap_match'] = ((has['dir'] == 'bull') & (has['vwap'] == 'above')) | \
                        ((has['dir'] == 'bear') & (has['vwap'] == 'below'))
    has['regime'] = has['ema_match'].astype(int) + has['vwap_match'].astype(int)
    for r in [0, 1, 2]:
        sub = has[(has['regime'] == r) & has['pnl_15'].notna()]
        if len(sub) > 0:
            print(f"  R{r}: N={len(sub):>4}, 15m PnL={sub['pnl_15'].mean():+.3f}, "
                  f"Win%={100*(sub['pnl_15']>0).mean():.1f}%, Total={sub['pnl_15'].sum():+.1f}")

    # R1 bull vs bear
    r1 = has[has['regime'] == 1]
    if len(r1) > 0:
        for d in ['bull', 'bear']:
            sub = r1[(r1['dir'] == d) & r1['pnl_15'].notna()]
            if len(sub) > 0:
                print(f"  R1 {d}: N={len(sub):>3}, PnL={sub['pnl_15'].mean():+.3f}, "
                      f"Win%={100*(sub['pnl_15']>0).mean():.1f}%")

    # ADX
    print(f"\n--- ADX ---")
    for lo, hi, label in [(0, 20, '<20'), (20, 30, '20-30'), (30, 40, '30-40'), (40, 100, '40+')]:
        sub = has[(has['adx'] >= lo) & (has['adx'] < hi) & has['pnl_15'].notna()]
        if len(sub) > 0:
            print(f"  ADX {label:5s}: N={len(sub):>4}, PnL={sub['pnl_15'].mean():+.3f}, "
                  f"Win%={100*(sub['pnl_15']>0).mean():.1f}%")

    # Auto-R1 performance
    print(f"\n--- Auto-Confirm R1 Performance ---")
    ac_set = set()
    for _, ac in auto_c.iterrows():
        ac_set.add((ac['file_id'], ac['date']))
    auto_sigs = has[has.apply(lambda r: (r['file_id'], r['date']) in ac_set and r['type'] == 'BRK', axis=1)]
    if len(auto_sigs) > 0:
        sub = auto_sigs[auto_sigs['pnl_15'].notna()]
        print(f"  N={len(sub)}, 15m PnL={sub['pnl_15'].mean():+.3f}, "
              f"Win%={100*(sub['pnl_15']>0).mean():.1f}%, Total={sub['pnl_15'].sum():+.1f}")

    # 5m check correlation
    print(f"\n--- 5m Check → 30m Outcome ---")
    for result in ['HOLD', 'BAIL']:
        ch_sub = checks[checks['result'] == result]
        ch_keys = set((c['file_id'], c['date']) for _, c in ch_sub.iterrows())
        matched = has[has.apply(lambda r: (r['file_id'], r['date']) in ch_keys, axis=1)]
        if len(matched) > 0 and 'pnl_30' in matched.columns:
            msub = matched[matched['pnl_30'].notna()]
            if len(msub) > 0:
                print(f"  {result}: N={len(msub)}, 30m PnL={msub['pnl_30'].mean():+.3f}, "
                      f"Win%={100*(msub['pnl_30']>0).mean():.1f}%")

    # TOP/BOTTOM signals
    print(f"\n--- Top 10 Best (30m PnL) ---")
    if 'pnl_30' in has.columns:
        best = has[has['pnl_30'].notna()].nlargest(10, 'pnl_30')
        for _, s in best.iterrows():
            print(f"  {s['symbol']:5s} {s['date']} {s['time']} {s['dir']:4s} {s['type']:3s} "
                  f"{s['levels'][:22]:22s} vol={s['vol']:.1f}x 30m={s['pnl_30']:+.3f}")

        print(f"\n--- Top 10 Worst (30m PnL) ---")
        worst = has[has['pnl_30'].notna()].nsmallest(10, 'pnl_30')
        for _, s in worst.iterrows():
            print(f"  {s['symbol']:5s} {s['date']} {s['time']} {s['dir']:4s} {s['type']:3s} "
                  f"{s['levels'][:22]:22s} vol={s['vol']:.1f}x 30m={s['pnl_30']:+.3f}")

# ── 8. Missed moves check ──
print("\n" + "=" * 70)
print("MISSED MOVES COVERAGE")
print("=" * 70)

nsz_file = DEBUG / "no-signal-zone-moves.csv"
if nsz_file.exists():
    nsz = pd.read_csv(nsz_file)
    sig_dates = set(sigs['date'].unique())
    sig_syms = set(sigs['symbol'].dropna().unique())

    # Only check moves for symbols and dates we have signals for
    overlap = nsz[(nsz['date'].isin(sig_dates)) & (nsz['symbol'].isin(sig_syms))]
    print(f"Missed moves on our dates+symbols: {len(overlap)}")
    if len(overlap) > 0 and 'magnitude' in overlap.columns:
        print(f"  Avg magnitude: {overlap['magnitude'].mean():.2f} ATR")
        print(f"  Tier S (≥2 ATR): {(overlap['magnitude'] >= 2).sum()}")
        print(f"  Tier A (1-2 ATR): {((overlap['magnitude'] >= 1) & (overlap['magnitude'] < 2)).sum()}")

        # Check time distribution
        if 'time' in overlap.columns:
            overlap_t = overlap.copy()
            overlap_t['mins'] = overlap_t['time'].apply(
                lambda t: int(t.split(':')[0]) * 60 + int(t.split(':')[1]) if isinstance(t, str) and ':' in str(t) else 0)
            morning = overlap_t[overlap_t['mins'] < 660]
            afternoon = overlap_t[overlap_t['mins'] >= 660]
            print(f"  Morning (<11): {len(morning)} ({100*len(morning)/len(overlap):.0f}%)")
            print(f"  Afternoon (11+): {len(afternoon)} ({100*len(afternoon)/len(overlap):.0f}%)")

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
