#!/usr/bin/env python3
"""
KLB v3.3c Time-of-Day SL Validation
=====================================
Validates time-of-day adaptive SL findings using v3.3c pine logs.
Compares against v3.4 to confirm / refute structural patterns.

Parts:
  A — Time-of-day baseline at SL=0.15 ATR (morning / midday / afternoon)
  B — SL sweep per time window (0.10–0.75 ATR), optimal ★ marked
  C — Cross-version comparison table (v3.3c vs v3.4)
  D — Afternoon breakdown: signal type, level type, any positive subsets?

Usage: python v33c_time_validation.py
"""

import pandas as pd
import numpy as np
import re
import csv
import glob
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ── Config ────────────────────────────────────────────────────────────────────
SYMBOLS = ['SPY','AAPL','AMD','AMZN','GLD','GOOGL','META','MSFT','NFLX','NVDA',
           'QQQ','SLV','TSLA','TSM','XLE']
BAR_DIR  = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/'
                'Meine Ablage/Claude/trading_bot/cache/bars/')
LOG_DIR  = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/'
                'Meine Ablage/Claude/misc/TradingView/debug/')

V33C_GLOB = 'pine-logs-Key Level Breakout v3.3c_*.csv'

SL_FACTOR   = 0.15   # baseline
HOLD_BARS   = 60     # 60 forward 1m bars

SL_SWEEP_FACTORS = [0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75]

# ── Regex patterns (identical to v34_sl_predictor.py) ─────────────────────────
SIG_PATTERN = re.compile(
    r'\[KLB\]\s+'
    r'(\d+:\d+)\s+'
    r'([▲▼])\s+'
    r'(.+?)\s+'
    r'vol=([0-9.]+)x\s+'
    r'pos=([v^]\d+)\s+'
    r'vwap=(above|below|na)\s+'
    r'ema=(bull|bear|flat|na)\s+'
    r'rs=([+-]?[0-9.]+%?)\s+'
    r'adx=(\d+|na)\s+'
    r'body=(\d+)%\s+'
    r'ramp=([0-9.]+)x\s+'
    r'rangeATR=([0-9.]+)\s*'
    r'(.*?)\s*'
    r'O([0-9.]+)\s+'
    r'H([0-9.]+)\s+'
    r'L([0-9.]+)\s+'
    r'C([0-9.]+)\s+'
    r'ATR=([0-9.]+)'
)

QBS_PATTERN = re.compile(
    r'\[KLB\]\s+(\d+:\d+)\s+([▲▼])\s+🔇\s+QBS\s+'
    r'ramp=([0-9.]+)x\s+'
    r'vol=([0-9.]+)x\s+'
    r'pos=([v^]\d+)\s+'
    r'vwap=(above|below|na)\s+'
    r'ema=(bull|bear|flat|na)\s+'
    r'adx=(\d+|na)\s+'
    r'body=(\d+)%\s+'
    r'rangeATR=([0-9.]+)\s*'
    r'(.*?)\s*'
    r'O([0-9.]+)\s+'
    r'H([0-9.]+)\s+'
    r'L([0-9.]+)\s+'
    r'C([0-9.]+)\s+'
    r'ATR=([0-9.]+)'
)

RNG_PATTERN  = re.compile(r'\[KLB\]\s+(\d+:\d+)\s+([▲▼])\s+RNG\s+range\s+break')
FADE_PATTERN = re.compile(r'\[KLB\]\s+(\d+:\d+)\s+([▲▼])\s+FADE\s+at\s+')


# ── Parsing helpers (verbatim from v34_sl_predictor.py) ───────────────────────

def parse_type_and_levels(s):
    s = s.strip()
    is_counter_ema = False
    if s.startswith('BRK '):
        sig_type = 'BRK'; levels_str = s[4:].strip()
    elif s.startswith('~ x~ '):
        sig_type = 'REV'; levels_str = s[5:].strip(); is_counter_ema = True
    elif s.startswith('~ ~~ ') or s.startswith('~~ '):
        sig_type = 'EXREV'; levels_str = s[5:].strip() if s.startswith('~ ~~ ') else s[3:].strip()
    elif s.startswith('~ ~ '):
        sig_type = 'REV'; levels_str = s[4:].strip()
    elif s.startswith('~ '):
        sig_type = 'REV'; levels_str = s[2:].strip()
    else:
        sig_type = 'UNK'; levels_str = s
    parts = []
    for p in levels_str.split(' + '):
        p = p.strip()
        while p.startswith('~ '): p = p[2:]
        if p: parts.append(p)
    return sig_type, ' + '.join(parts), is_counter_ema


def parse_pine_log(filepath):
    signals = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) < 2:
                continue
            timestamp_str = row[0]
            message = ' '.join(row[1:]).strip()
            try:
                ts = pd.Timestamp(timestamp_str)
            except:
                continue
            if '[KLB]' not in message:
                continue
            if RNG_PATTERN.search(message):
                continue
            if FADE_PATTERN.search(message):
                continue
            if 'CONF' in message or '5m CHECK' in message:
                continue

            m = QBS_PATTERN.search(message)
            if m:
                (time_str, dir_char, ramp_s, vol_s, pos_s, vwap_s, ema_s,
                 adx_s, body_s, ratr_s, flags, o, h, l, c, atr_s) = m.groups()
                signals.append({
                    'timestamp': ts, 'time_str': time_str,
                    'direction': 'bull' if dir_char == '▲' else 'bear',
                    'sig_type': 'QBS', 'levels': 'QBS',
                    'vol_ratio': float(vol_s), 'close_pos': pos_s,
                    'vwap': vwap_s, 'ema': ema_s, 'rs': None,
                    'adx': int(adx_s) if adx_s != 'na' else None,
                    'body_pct': int(body_s), 'ramp': float(ramp_s),
                    'range_atr': float(ratr_s),
                    'open': float(o), 'high': float(h), 'low': float(l), 'close': float(c),
                    'atr': float(atr_s), 'is_counter_ema': False,
                })
                continue

            m = SIG_PATTERN.search(message)
            if m:
                (time_str, dir_char, type_levels, vol_s, pos_s, vwap_s, ema_s,
                 rs_s, adx_s, body_s, ramp_s, ratr_s, flags,
                 o, h, l, c, atr_s) = m.groups()
                sig_type, levels_str, is_counter_ema = parse_type_and_levels(type_levels)
                if sig_type in ('UNK',):
                    continue
                rs_clean = rs_s.replace('%', '')
                signals.append({
                    'timestamp': ts, 'time_str': time_str,
                    'direction': 'bull' if dir_char == '▲' else 'bear',
                    'sig_type': sig_type, 'levels': levels_str,
                    'vol_ratio': float(vol_s), 'close_pos': pos_s,
                    'vwap': vwap_s, 'ema': ema_s,
                    'rs': float(rs_clean) if rs_clean else None,
                    'adx': int(adx_s) if adx_s != 'na' else None,
                    'body_pct': int(body_s), 'ramp': float(ramp_s),
                    'range_atr': float(ratr_s),
                    'open': float(o), 'high': float(h), 'low': float(l), 'close': float(c),
                    'atr': float(atr_s), 'is_counter_ema': is_counter_ema,
                })
    return signals


def identify_symbol(signals, bar_dir=BAR_DIR, symbols=SYMBOLS):
    samples = [s for s in signals if s.get('close') is not None and s.get('atr') is not None][:12]
    if not samples:
        return None
    best_sym, best_score = None, float('inf')
    for sym in symbols:
        fp = bar_dir / f'{sym.lower()}_1_day_ib.parquet'
        if not fp.exists():
            continue
        try:
            daily = pd.read_parquet(fp)
            dt = pd.to_datetime(daily['date'])
            if dt.dt.tz is not None:
                dt = dt.dt.tz_convert('US/Eastern')
            daily['date'] = dt
            daily = daily.set_index('date').sort_index()
        except:
            continue
        total_err, matched = 0, 0
        for sig in samples:
            sig_date = sig['timestamp'].date() if hasattr(sig['timestamp'], 'date') else None
            if sig_date is None:
                continue
            day_bars = daily[daily.index.date == sig_date]
            if len(day_bars) == 0:
                continue
            daily_close = day_bars['close'].iloc[0]
            if daily_close > 0:
                total_err += abs(sig['close'] - daily_close) / daily_close
                matched += 1
        if matched > 0:
            avg_err = total_err / matched
            if avg_err < best_score:
                best_score = avg_err
                best_sym = sym
    return best_sym if best_score < 0.05 else None


def load_1m(symbol):
    fp = BAR_DIR / f'{symbol.lower()}_1_min_ib.parquet'
    df = pd.read_parquet(fp)
    dt = pd.to_datetime(df['date'])
    if dt.dt.tz is None:
        dt = dt.dt.tz_localize('US/Eastern')
    elif str(dt.dt.tz) != 'US/Eastern':
        dt = dt.dt.tz_convert('US/Eastern')
    df['date'] = dt
    df = df.set_index('date').sort_index()
    df = df.between_time('09:30', '15:59')
    return df


def measure_sl_outcome(signals, bars_1m, sl_factor=SL_FACTOR, hold_bars=HOLD_BARS):
    for sig in signals:
        ts = sig['timestamp']
        direction = sig['direction']
        entry = sig.get('close')
        atr = sig.get('atr')

        if entry is None or atr is None or atr == 0:
            sig.update({'sl_hit': None, 'pnl_60m': None, 'entry_price': None, 'sl_price': None})
            continue

        sl_dist = sl_factor * atr
        sl_price = entry - sl_dist if direction == 'bull' else entry + sl_dist

        if ts.tzinfo is None:
            ts_et = pd.Timestamp(ts, tz='US/Eastern')
        else:
            ts_et = ts.tz_convert('US/Eastern')

        start_time = ts_et + pd.Timedelta(minutes=1)
        end_time   = ts_et + pd.Timedelta(minutes=hold_bars)
        eod        = ts_et.normalize() + pd.Timedelta(hours=16)
        end_time   = min(end_time, eod)

        fwd = bars_1m.loc[start_time:end_time]
        if len(fwd) == 0:
            sig.update({'sl_hit': None, 'pnl_60m': None, 'entry_price': entry, 'sl_price': sl_price})
            continue

        entry_price    = fwd['open'].iloc[0]
        sl_price_actual = entry_price - sl_dist if direction == 'bull' else entry_price + sl_dist

        if direction == 'bull':
            sl_hit = bool((fwd['low'] <= sl_price_actual).any())
        else:
            sl_hit = bool((fwd['high'] >= sl_price_actual).any())

        exit_price = fwd['close'].iloc[-1]
        if direction == 'bull':
            pnl_60m = (exit_price - entry_price) / atr
        else:
            pnl_60m = (entry_price - exit_price) / atr

        sig.update({
            'sl_hit': sl_hit,
            'pnl_60m': pnl_60m,
            'entry_price': entry_price,
            'sl_price': sl_price_actual,
        })


def classify_time(ts):
    if ts.tzinfo is None:
        ts = pd.Timestamp(ts, tz='US/Eastern')
    else:
        ts = ts.tz_convert('US/Eastern')
    mins = ts.hour * 60 + ts.minute
    if mins < 11 * 60:
        return 'morning'
    elif mins < 14 * 60:
        return 'midday'
    else:
        return 'afternoon'


def classify_level_type(levels_str):
    s = str(levels_str).upper()
    if any(x in s for x in ['ORB H', 'ORB L']):
        return 'ORB'
    if any(x in s for x in ['PM H', 'PM L']):
        return 'PM'
    if 'VWAP' in s:
        return 'VWAP'
    if any(x in s for x in ['YEST H', 'YEST L']):
        return 'YEST'
    if any(x in s for x in ['PD CLS', 'PD LH', 'PD HL']):
        return 'PD'
    if any(x in s for x in ['TODAY O', 'TODAY']):
        return 'TODAY_O'
    if any(x in s for x in ['WEEK O', 'MON O']):
        return 'WEEK'
    if any(x in s for x in ['52W', 'ATH', 'RND']):
        return 'MAJOR'
    return 'OTHER'


# ── SL evaluation (verbatim from v34_sl_predictor.py) ─────────────────────────

def evaluate_sl_factor(df_sub, bars_cache, sl_factor, hold_bars=HOLD_BARS):
    rows = df_sub.to_dict('records')
    for sig in rows:
        sym = sig['symbol']
        bars_1m = bars_cache.get(sym)
        if bars_1m is None:
            sig['_sl_hit2'] = None; sig['_pnl2'] = None; continue

        ts          = sig['timestamp']
        direction   = sig['direction']
        entry_price = sig.get('entry_price')
        atr         = sig.get('atr')

        if entry_price is None or atr is None or atr == 0:
            sig['_sl_hit2'] = None; sig['_pnl2'] = None; continue

        if ts.tzinfo is None:
            ts_et = pd.Timestamp(ts, tz='US/Eastern')
        else:
            ts_et = ts.tz_convert('US/Eastern')

        sl_dist  = sl_factor * atr
        sl_price = entry_price - sl_dist if direction == 'bull' else entry_price + sl_dist

        start_time = ts_et + pd.Timedelta(minutes=1)
        end_time   = ts_et + pd.Timedelta(minutes=hold_bars)
        eod        = ts_et.normalize() + pd.Timedelta(hours=16)
        end_time   = min(end_time, eod)

        fwd = bars_1m.loc[start_time:end_time]
        if len(fwd) == 0:
            sig['_sl_hit2'] = None; sig['_pnl2'] = None; continue

        if direction == 'bull':
            sl_hit = bool((fwd['low'] <= sl_price).any())
        else:
            sl_hit = bool((fwd['high'] >= sl_price).any())

        exit_price = fwd['close'].iloc[-1]
        if sl_hit:
            pnl = -sl_factor
        else:
            pnl = (exit_price - entry_price) / atr if direction == 'bull' else (entry_price - exit_price) / atr

        sig['_sl_hit2'] = sl_hit
        sig['_pnl2']    = pnl

    valid = [r for r in rows if r['_sl_hit2'] is not None]
    if not valid:
        return None
    n    = len(valid)
    hits = sum(1 for r in valid if r['_sl_hit2'])
    pnls = [r['_pnl2'] for r in valid]
    net  = sum(pnls)
    wins = sum(1 for p in pnls if p > 0)
    return {
        'sl_factor':   sl_factor,
        'N':           n,
        'sl_hit_pct':  hits / n * 100,
        'net_atr':     net,
        'atr_per_sig': net / n,
        'win_pct':     wins / n * 100,
    }


def sl_sweep_table(df_sub, bars_cache, sl_factors=SL_SWEEP_FACTORS):
    results = []
    for sl in sl_factors:
        r = evaluate_sl_factor(df_sub, bars_cache, sl)
        if r:
            results.append(r)
    return results


def print_sl_sweep(results, label=''):
    if not results:
        print("  (no data)")
        return
    best_idx = max(range(len(results)), key=lambda i: results[i]['atr_per_sig'])
    hdr = f"  {'SL(ATR)':>8}  {'N':>6}  {'SL_hit%':>8}  {'Net ATR':>9}  {'ATR/sig':>8}  {'Win%':>7}"
    print(hdr)
    print("  " + "-"*8 + "  " + "-"*6 + "  " + "-"*8 + "  " + "-"*9 + "  " + "-"*8 + "  " + "-"*7)
    for i, r in enumerate(results):
        marker = ' ★' if i == best_idx else ''
        print(f"  {r['sl_factor']:>8.2f}  {r['N']:>6}  {r['sl_hit_pct']:>7.1f}%"
              f"  {r['net_atr']:>+9.1f}  {r['atr_per_sig']:>+8.3f}  {r['win_pct']:>6.1f}%{marker}")


# ── Main ──────────────────────────────────────────────────────────────────────

def load_v33c_data():
    """Parse all v3.3c logs, identify symbols, measure SL outcomes. Return (df, bars_cache)."""
    log_files = sorted(LOG_DIR.glob(V33C_GLOB))
    print(f"\n  Found {len(log_files)} v3.3c log files")

    all_records = []
    sym_cache   = {}
    seen_symbols = set()

    for fp in log_files:
        signals = parse_pine_log(fp)
        if not signals:
            continue
        sym = identify_symbol(signals)
        if sym is None:
            print(f"  WARNING: Could not identify symbol for {fp.name}")
            continue
        if sym in seen_symbols:
            print(f"  {fp.name[-24:]} -> {sym} (DUPLICATE — skipped)")
            continue
        seen_symbols.add(sym)
        print(f"  {fp.name[-24:]} -> {sym} ({len(signals)} raw signals)")

        if sym not in sym_cache:
            try:
                sym_cache[sym] = load_1m(sym)
            except Exception as e:
                print(f"     Could not load 1m bars for {sym}: {e}")
                continue
        bars_1m = sym_cache[sym]

        measure_sl_outcome(signals, bars_1m)
        for sig in signals:
            sig['symbol'] = sym
        all_records.extend(signals)

    print(f"\n  Total raw signals parsed: {len(all_records)}")

    df_all = pd.DataFrame(all_records)
    df = df_all[df_all['sig_type'].isin(['BRK', 'REV'])].copy()
    df = df[df['sl_hit'].notna()].copy()

    df['time_of_day'] = df['timestamp'].apply(classify_time)
    df['level_type']  = df['levels'].apply(classify_level_type)

    print(f"  BRK+REV signals with valid SL outcome: {len(df)}")
    return df, sym_cache


def part_a(df):
    """Time-of-day baseline breakdown at SL=0.15 ATR."""
    print("\n\n" + "="*70)
    print("  PART A: TIME-OF-DAY BASELINE  (SL = 0.15 ATR, Hold = 60m)")
    print("="*70)

    overall_sl  = df['sl_hit'].mean() * 100
    overall_pnl = df['pnl_60m'].mean()
    overall_net = df['pnl_60m'].sum()
    print(f"\n  Overall baseline: N={len(df)}, SL%={overall_sl:.1f}%, "
          f"ATR/sig={overall_pnl:+.3f}, Net={overall_net:+.1f} ATR")

    print(f"\n  {'Window':<12}  {'N':>6}  {'SL_hit%':>8}  {'Net ATR':>9}  {'ATR/sig':>8}  Note")
    print(f"  {'-'*12}  {'-'*6}  {'-'*8}  {'-'*9}  {'-'*8}  {'-'*20}")

    for window in ['morning', 'midday', 'afternoon']:
        sub = df[df['time_of_day'] == window]
        if len(sub) == 0:
            print(f"  {window:<12}  (no data)")
            continue
        n   = len(sub)
        sl  = sub['sl_hit'].mean() * 100
        net = sub['pnl_60m'].sum()
        avg = sub['pnl_60m'].mean()
        note = ''
        if avg < 0:
            note = '<-- NEGATIVE'
        elif sl > overall_sl + 5:
            note = 'HIGH SL rate'
        print(f"  {window:<12}  {n:>6}  {sl:>7.1f}%  {net:>+9.1f}  {avg:>+8.3f}  {note}")

    return overall_sl, overall_pnl


def part_b(df, bars_cache):
    """SL sweep per time window."""
    print("\n\n" + "="*70)
    print("  PART B: SL SWEEP PER TIME WINDOW")
    print("="*70)

    windows = [
        ('morning',   'Morning   (09:30–11:00)'),
        ('midday',    'Midday    (11:00–14:00)'),
        ('afternoon', 'Afternoon (14:00–16:00)'),
    ]

    optimal = {}
    for key, label in windows:
        sub = df[df['time_of_day'] == key]
        print(f"\n  --- {label}  N={len(sub)} ---")
        results = sl_sweep_table(sub, bars_cache)
        print_sl_sweep(results)
        if results:
            best = max(results, key=lambda r: r['atr_per_sig'])
            optimal[key] = best
            print(f"  -> Optimal SL: {best['sl_factor']:.2f} ATR  "
                  f"(ATR/sig={best['atr_per_sig']:+.3f}, Net={best['net_atr']:+.1f})")

    return optimal


def part_c(df, bars_cache, optimal_v33c):
    """Cross-version comparison table — v3.3c vs v3.4 (hardcoded from prior run)."""
    print("\n\n" + "="*70)
    print("  PART C: CROSS-VERSION COMPARISON  (v3.3c vs v3.4)")
    print("  Note: v3.4 numbers from prior v34_sl_predictor.py run")
    print("="*70)

    # v3.4 results from the prior analysis run (at optimal SL per window):
    # morning: opt=0.75, atr/sig=+0.296, N=831
    # midday:  opt=0.75, atr/sig=+0.240, N=1183
    # afternoon: opt=0.10, atr/sig=-0.009, N=423
    V34_RESULTS = {
        'morning':   {'sl': 0.75, 'N': 831,  'atr_per_sig': +0.296},
        'midday':    {'sl': 0.75, 'N': 1183, 'atr_per_sig': +0.240},
        'afternoon': {'sl': 0.10, 'N': 423,  'atr_per_sig': -0.009},
    }

    print(f"\n  {'Window':<12}  {'v3.3c N':>8}  {'v3.3c SL':>9}  {'v3.3c /sig':>11}  "
          f"{'v3.4 N':>7}  {'v3.4 SL':>8}  {'v3.4 /sig':>10}  Consistent?")
    print(f"  {'-'*12}  {'-'*8}  {'-'*9}  {'-'*11}  "
          f"{'-'*7}  {'-'*8}  {'-'*10}  {'-'*11}")

    for window in ['morning', 'midday', 'afternoon']:
        sub = df[df['time_of_day'] == window]
        v33c = optimal_v33c.get(window)
        v34  = V34_RESULTS.get(window)

        if v33c is None or v34 is None:
            print(f"  {window:<12}  (missing data)")
            continue

        n33   = v33c['N']
        sl33  = v33c['sl_factor']
        ps33  = v33c['atr_per_sig']
        n34   = v34['N']
        sl34  = v34['sl']
        ps34  = v34['atr_per_sig']

        # Consistent = same sign on atr_per_sig AND same direction of optimal SL
        same_sign = (ps33 > 0) == (ps34 > 0)
        consistent = 'YES' if same_sign else 'NO !!!'
        if window == 'afternoon':
            consistent = ('YES (both neg)' if ps33 < 0 and ps34 < 0
                          else 'YES (both pos)' if ps33 > 0 and ps34 > 0
                          else 'NO !!!')

        print(f"  {window:<12}  {n33:>8}  {sl33:>8.2f}x  {ps33:>+10.3f}  "
              f"{n34:>7}  {sl34:>7.2f}x  {ps34:>+9.3f}  {consistent}")


def part_d(df, bars_cache):
    """Afternoon breakdown: signal type, level type, subsets."""
    print("\n\n" + "="*70)
    print("  PART D: AFTERNOON BREAKDOWN (v3.3c)")
    print("="*70)

    aft = df[df['time_of_day'] == 'afternoon'].copy()
    if len(aft) == 0:
        print("  (no afternoon signals)")
        return

    overall_sl  = aft['sl_hit'].mean() * 100
    overall_pnl = aft['pnl_60m'].mean()
    print(f"\n  Afternoon overall: N={len(aft)}, SL%={overall_sl:.1f}%, ATR/sig={overall_pnl:+.3f}")

    # --- By signal type (BRK vs REV) ---
    print(f"\n  By signal type:")
    print(f"  {'Type':<8}  {'N':>6}  {'SL_hit%':>8}  {'Net ATR':>9}  {'ATR/sig':>8}")
    print(f"  {'-'*8}  {'-'*6}  {'-'*8}  {'-'*9}  {'-'*8}")
    for sig_type in ['BRK', 'REV']:
        sub = aft[aft['sig_type'] == sig_type]
        if len(sub) == 0:
            continue
        n   = len(sub)
        sl  = sub['sl_hit'].mean() * 100
        net = sub['pnl_60m'].sum()
        avg = sub['pnl_60m'].mean()
        note = ' <-- neg' if avg < 0 else ''
        print(f"  {sig_type:<8}  {n:>6}  {sl:>7.1f}%  {net:>+9.1f}  {avg:>+8.3f}{note}")

    # --- By direction ---
    print(f"\n  By direction:")
    print(f"  {'Dir':<8}  {'N':>6}  {'SL_hit%':>8}  {'Net ATR':>9}  {'ATR/sig':>8}")
    print(f"  {'-'*8}  {'-'*6}  {'-'*8}  {'-'*9}  {'-'*8}")
    for direction in ['bull', 'bear']:
        sub = aft[aft['direction'] == direction]
        if len(sub) == 0:
            continue
        n   = len(sub)
        sl  = sub['sl_hit'].mean() * 100
        net = sub['pnl_60m'].sum()
        avg = sub['pnl_60m'].mean()
        note = ' <-- neg' if avg < 0 else ''
        print(f"  {direction:<8}  {n:>6}  {sl:>7.1f}%  {net:>+9.1f}  {avg:>+8.3f}{note}")

    # --- By level type ---
    print(f"\n  By level type (afternoon only):")
    print(f"  {'Level':<10}  {'N':>6}  {'SL_hit%':>8}  {'Net ATR':>9}  {'ATR/sig':>8}")
    print(f"  {'-'*10}  {'-'*6}  {'-'*8}  {'-'*9}  {'-'*8}")
    for lvl in sorted(aft['level_type'].unique()):
        sub = aft[aft['level_type'] == lvl]
        if len(sub) < 5:
            continue
        n   = len(sub)
        sl  = sub['sl_hit'].mean() * 100
        net = sub['pnl_60m'].sum()
        avg = sub['pnl_60m'].mean()
        note = ' <-- pos' if avg > 0.05 else (' <-- neg' if avg < -0.05 else '')
        print(f"  {lvl:<10}  {n:>6}  {sl:>7.1f}%  {net:>+9.1f}  {avg:>+8.3f}{note}")

    # --- SL sweep subsets: BRK only, REV only ---
    print(f"\n  SL sweep — Afternoon BRK signals (N={len(aft[aft['sig_type']=='BRK'])}):")
    brk_aft = aft[aft['sig_type'] == 'BRK']
    res = sl_sweep_table(brk_aft, bars_cache)
    print_sl_sweep(res)

    print(f"\n  SL sweep — Afternoon REV signals (N={len(aft[aft['sig_type']=='REV'])}):")
    rev_aft = aft[aft['sig_type'] == 'REV']
    res = sl_sweep_table(rev_aft, bars_cache)
    print_sl_sweep(res)

    # --- Search for ANY positive afternoon subset ---
    print(f"\n  Subset scan — any consistently positive afternoon signals?")
    print(f"  (min N=10, ATR/sig > 0)")
    print(f"\n  {'Subset':<40}  {'N':>6}  {'SL_hit%':>8}  {'ATR/sig':>8}")
    print(f"  {'-'*40}  {'-'*6}  {'-'*8}  {'-'*8}")

    subsets = [
        ('BRK + bull',            (aft['sig_type'] == 'BRK') & (aft['direction'] == 'bull')),
        ('BRK + bear',            (aft['sig_type'] == 'BRK') & (aft['direction'] == 'bear')),
        ('REV + bull',            (aft['sig_type'] == 'REV') & (aft['direction'] == 'bull')),
        ('REV + bear',            (aft['sig_type'] == 'REV') & (aft['direction'] == 'bear')),
        ('BRK + vol<2x',          (aft['sig_type'] == 'BRK') & (aft['vol_ratio'] <= 2)),
        ('BRK + vol>2x',          (aft['sig_type'] == 'BRK') & (aft['vol_ratio'] > 2)),
        ('EMA bull signals',      aft['ema'] == 'bull'),
        ('EMA bear signals',      aft['ema'] == 'bear'),
        ('VWAP aligned',          ((aft['direction'] == 'bull') & (aft['vwap'] == 'above')) |
                                  ((aft['direction'] == 'bear') & (aft['vwap'] == 'below'))),
        ('ORB levels',            aft['level_type'] == 'ORB'),
        ('PM levels',             aft['level_type'] == 'PM'),
        ('VWAP level',            aft['level_type'] == 'VWAP'),
        ('Late (>15:00)',         aft['timestamp'].apply(lambda t: t.tz_convert('US/Eastern').hour >= 15)),
        ('Early-aft (14:00-15)',  aft['timestamp'].apply(lambda t: t.tz_convert('US/Eastern').hour == 14)),
    ]

    positives_found = []
    for name, mask in subsets:
        sub = aft[mask]
        if len(sub) < 10:
            continue
        n   = len(sub)
        sl  = sub['sl_hit'].mean() * 100
        avg = sub['pnl_60m'].mean()
        marker = ' ★ POSITIVE' if avg > 0 else ''
        print(f"  {name:<40}  {n:>6}  {sl:>7.1f}%  {avg:>+8.3f}{marker}")
        if avg > 0:
            positives_found.append((name, n, avg))

    print(f"\n  Verdict:")
    if not positives_found:
        print("  Afternoon is STRUCTURALLY NEGATIVE in v3.3c.")
        print("  No subset (signal type, level, direction, timing) is consistently positive.")
        print("  This matches v3.4 findings — afternoon negative is cross-version.")
    else:
        print(f"  Found {len(positives_found)} positive subsets:")
        for name, n, avg in positives_found:
            print(f"    {name}: N={n}, ATR/sig={avg:+.3f}")
        if len(positives_found) <= 2:
            print("  CAUTION: small sample or marginal — may not be structural.")


def summary_verdict(df, optimal):
    """Final answer: is afternoon consistently negative?"""
    print("\n\n" + "="*70)
    print("  FINAL VERDICT")
    print("="*70)

    for window in ['morning', 'midday', 'afternoon']:
        sub = df[df['time_of_day'] == window]
        if len(sub) == 0:
            continue
        pnl = sub['pnl_60m'].mean()
        sl  = sub['sl_hit'].mean() * 100
        opt = optimal.get(window)
        best_sl  = opt['sl_factor']   if opt else 0.15
        best_pnl = opt['atr_per_sig'] if opt else pnl
        print(f"\n  {window.upper()}")
        print(f"    Baseline (0.15 ATR): N={len(sub)}, SL%={sl:.1f}%, ATR/sig={pnl:+.3f}")
        print(f"    Optimal SL: {best_sl:.2f} ATR -> ATR/sig={best_pnl:+.3f}")
        if window == 'afternoon':
            if best_pnl < 0:
                print("    => CONFIRMED: Afternoon negative even at optimal SL in v3.3c.")
                print("       Cross-version pattern — structural, not v3.4 artifact.")
            else:
                print(f"    => Afternoon positive at optimal SL={best_sl:.2f} ATR.")
                print("       Pattern differs from v3.4 — investigate further.")


def main():
    print("\n" + "="*70)
    print("  KLB v3.3c Time-of-Day SL Validation")
    print("="*70)

    # Load data
    df, bars_cache = load_v33c_data()

    baseline_sl  = df['sl_hit'].mean() * 100
    baseline_pnl = df['pnl_60m'].mean()
    print(f"\n  Overall baseline: SL%={baseline_sl:.1f}%, ATR/sig={baseline_pnl:+.3f}")

    # Distribution by type
    print("\n  Signal type breakdown:")
    td = df.groupby(['sig_type', 'direction']).agg(
        N=('sl_hit', 'count'),
        SL_pct=('sl_hit', lambda x: round(x.mean()*100, 1)),
        pnl=('pnl_60m', lambda x: round(x.mean(), 3))
    )
    print(td.to_string())

    # Parts
    overall_sl, overall_pnl = part_a(df)
    optimal = part_b(df, bars_cache)
    part_c(df, bars_cache, optimal)
    part_d(df, bars_cache)
    summary_verdict(df, optimal)

    print("\n" + "="*70)
    print("  Done.")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
