#!/usr/bin/env python3
"""
KLB v3.4 Stop-Loss Predictor
==============================
Parses v3.4 Pine logs (8 März only), measures SL outcomes with SL=0.15 ATR,
analyses features that predict SL hits, and tests filter candidates.

Usage: python v34_sl_predictor.py
"""

import pandas as pd
import numpy as np
import re
import csv
import glob
from pathlib import Path
from datetime import time as dtime
import warnings
warnings.filterwarnings('ignore')

# ── Config ────────────────────────────────────────────────────────────────────
SYMBOLS = ['SPY','AAPL','AMD','AMZN','GLD','GOOGL','META','MSFT','NFLX','NVDA','QQQ','SLV','TSLA','TSM','XLE']
BAR_DIR = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars/')
LOG_DIR = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug/')

V34_GLOB = 'pine-logs-Key Level Breakout v3.4_*.csv'
# Skip files modified on 9 März
SKIP_HASHES = {'c7802', 'ea7ff'}

SL_FACTOR = 0.15   # SL = entry ± 0.15 × ATR
HOLD_BARS = 60     # 60 forward 1m bars

# ── Regex patterns (re-used from v33_backtest.py) ─────────────────────────────
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

RNG_PATTERN = re.compile(
    r'\[KLB\]\s+(\d+:\d+)\s+([▲▼])\s+RNG\s+range\s+break'
)

FADE_PATTERN = re.compile(
    r'\[KLB\]\s+(\d+:\d+)\s+([▲▼])\s+FADE\s+at\s+'
)


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

            # Skip RNG / FADE
            if RNG_PATTERN.search(message):
                continue
            if FADE_PATTERN.search(message):
                continue
            # Skip CONF / CHECK / plain status lines
            if 'CONF' in message or '5m CHECK' in message:
                continue

            # QBS
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

            # Main BRK/REV
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
                continue
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
    """Add sl_hit (bool), pnl_60m, entry_price, sl_price to each signal."""
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

        # Entry = open of next 1m bar
        start_time = ts_et + pd.Timedelta(minutes=1)
        end_time = ts_et + pd.Timedelta(minutes=hold_bars)
        eod = ts_et.normalize() + pd.Timedelta(hours=16)
        end_time = min(end_time, eod)

        # Get forward bars
        fwd = bars_1m.loc[start_time:end_time]
        if len(fwd) == 0:
            sig.update({'sl_hit': None, 'pnl_60m': None, 'entry_price': entry, 'sl_price': sl_price})
            continue

        # Entry price = open of first forward bar
        entry_price = fwd['open'].iloc[0]
        sl_price_actual = entry_price - sl_dist if direction == 'bull' else entry_price + sl_dist

        # SL hit check
        sl_hit = False
        if direction == 'bull':
            if (fwd['low'] <= sl_price_actual).any():
                sl_hit = True
        else:
            if (fwd['high'] >= sl_price_actual).any():
                sl_hit = True

        # P&L at 60m = close of last forward bar
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
    h, m = ts.hour, ts.minute
    mins = h * 60 + m
    if mins < 11 * 60:
        return 'morning'
    elif mins < 14 * 60:
        return 'midday'
    else:
        return 'afternoon'


def classify_level_type(levels_str):
    levels_str = str(levels_str).upper()
    if any(x in levels_str for x in ['ORB H', 'ORB L']):
        return 'ORB'
    if any(x in levels_str for x in ['PM H', 'PM L']):
        return 'PM'
    if any(x in levels_str for x in ['VWAP']):
        return 'VWAP'
    if any(x in levels_str for x in ['YEST H', 'YEST L']):
        return 'YEST'
    if any(x in levels_str for x in ['PD CLS', 'PD LH', 'PD HL']):
        return 'PD'
    if any(x in levels_str for x in ['TODAY O', 'TODAY']):
        return 'TODAY_O'
    if any(x in levels_str for x in ['WEEK O', 'MON O']):
        return 'WEEK'
    if any(x in levels_str for x in ['52W', 'ATH', 'RND']):
        return 'MAJOR'
    return 'OTHER'


def bucket(val, breaks, labels):
    """Bucket a numeric value into a category."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return 'NA'
    for i, b in enumerate(breaks):
        if val < b:
            return labels[i]
    return labels[-1]


def feature_table(df, feature_col, outcome_col='sl_hit', pnl_col='pnl_60m'):
    """Return a summary DataFrame for a feature column."""
    rows = []
    for val in sorted(df[feature_col].dropna().unique()):
        subset = df[df[feature_col] == val]
        n = len(subset)
        n_with_outcome = subset[outcome_col].notna().sum()
        sl_rate = subset[outcome_col].mean() * 100 if n_with_outcome > 0 else float('nan')
        mean_pnl = subset[pnl_col].mean()
        rows.append({'bucket': val, 'N': n, 'SL_hit_pct': round(sl_rate, 1),
                     'mean_pnl_atr': round(mean_pnl, 3) if not np.isnan(mean_pnl) else float('nan')})
    return pd.DataFrame(rows).set_index('bucket')


def print_feature_table(name, df_table, baseline_sl):
    print(f"\n{'='*60}")
    print(f"  {name}  (baseline SL rate: {baseline_sl:.1f}%)")
    print(f"{'='*60}")
    print(f"  {'Bucket':<18} {'N':>6}  {'SL%':>7}  {'Δ vs base':>10}  {'P&L/sig':>9}")
    print(f"  {'-'*18} {'-'*6}  {'-'*7}  {'-'*10}  {'-'*9}")
    for bucket_name, row in df_table.iterrows():
        delta = row['SL_hit_pct'] - baseline_sl
        marker = ' ★' if delta < -5 else ('  !' if delta > 5 else '')
        print(f"  {str(bucket_name):<18} {row['N']:>6}  {row['SL_hit_pct']:>6.1f}%  {delta:>+9.1f}pp  {row['mean_pnl_atr']:>+8.3f}{marker}")


def simulate_filter(df, mask, name):
    """Show impact of filtering OUT signals matching mask."""
    removed = df[mask]
    kept = df[~mask]
    if len(kept) == 0:
        return None
    outcome = kept['sl_hit'].notna()
    sl_rate = kept.loc[outcome, 'sl_hit'].mean() * 100
    pnl = kept['pnl_60m'].mean()
    baseline_sl = df['sl_hit'].mean() * 100
    baseline_pnl = df['pnl_60m'].mean()
    delta_sl = sl_rate - baseline_sl
    delta_pnl = pnl - baseline_pnl
    passes = (delta_sl < -5) and (delta_pnl > 0.005) and (len(kept) >= 500)
    return {
        'filter': name,
        'N_removed': len(removed),
        'N_kept': len(kept),
        'SL_kept_%': round(sl_rate, 1),
        'delta_SL_pp': round(delta_sl, 1),
        'pnl_kept': round(pnl, 3),
        'delta_pnl': round(delta_pnl, 3),
        'passes': passes,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

SL_SWEEP_FACTORS = [0.10, 0.12, 0.15, 0.18, 0.20, 0.22, 0.25, 0.30, 0.35, 0.40, 0.50, 0.75]


def evaluate_sl_factor(df_sub, bars_cache, sl_factor, hold_bars=HOLD_BARS):
    """
    Re-evaluate SL outcomes for df_sub at a given sl_factor.
    Returns dict with sl_hit_pct, net_atr, atr_per_sig, win_pct, n.
    """
    rows = df_sub.to_dict('records')

    for sig in rows:
        sym = sig['symbol']
        bars_1m = bars_cache.get(sym)
        if bars_1m is None:
            sig['_sl_hit2'] = None
            sig['_pnl2'] = None
            continue

        ts = sig['timestamp']
        direction = sig['direction']
        entry_price = sig.get('entry_price')
        atr = sig.get('atr')

        if entry_price is None or atr is None or atr == 0:
            sig['_sl_hit2'] = None
            sig['_pnl2'] = None
            continue

        if ts.tzinfo is None:
            ts_et = pd.Timestamp(ts, tz='US/Eastern')
        else:
            ts_et = ts.tz_convert('US/Eastern')

        sl_dist = sl_factor * atr
        sl_price = entry_price - sl_dist if direction == 'bull' else entry_price + sl_dist

        start_time = ts_et + pd.Timedelta(minutes=1)
        end_time = ts_et + pd.Timedelta(minutes=hold_bars)
        eod = ts_et.normalize() + pd.Timedelta(hours=16)
        end_time = min(end_time, eod)

        fwd = bars_1m.loc[start_time:end_time]
        if len(fwd) == 0:
            sig['_sl_hit2'] = None
            sig['_pnl2'] = None
            continue

        # Use the same entry_price already computed (open of first bar after signal)
        if direction == 'bull':
            sl_hit = bool((fwd['low'] <= sl_price).any())
        else:
            sl_hit = bool((fwd['high'] >= sl_price).any())

        exit_price = fwd['close'].iloc[-1]
        if sl_hit:
            pnl = -sl_factor
        else:
            if direction == 'bull':
                pnl = (exit_price - entry_price) / atr
            else:
                pnl = (entry_price - exit_price) / atr

        sig['_sl_hit2'] = sl_hit
        sig['_pnl2'] = pnl

    valid = [r for r in rows if r['_sl_hit2'] is not None]
    if not valid:
        return None
    n = len(valid)
    hits = sum(1 for r in valid if r['_sl_hit2'])
    pnls = [r['_pnl2'] for r in valid]
    net_atr = sum(pnls)
    # win = pnl > 0
    wins = sum(1 for p in pnls if p > 0)
    return {
        'sl_factor': sl_factor,
        'N': n,
        'sl_hit_pct': hits / n * 100,
        'net_atr': net_atr,
        'atr_per_sig': net_atr / n,
        'win_pct': wins / n * 100,
    }


def sl_sweep_table(df_sub, bars_cache, sl_factors=SL_SWEEP_FACTORS, label=''):
    """Run SL sweep and return list of result dicts."""
    results = []
    for sl in sl_factors:
        r = evaluate_sl_factor(df_sub, bars_cache, sl)
        if r:
            results.append(r)
    return results


def print_sl_sweep(results, label=''):
    """Print a formatted SL sweep table, marking the best ATR/sig row."""
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


def run_adaptive_sl_sections(df, bars_cache):
    """Parts A–D: time-of-day SL sweep + adaptive strategy comparison."""

    SL_FACTORS = SL_SWEEP_FACTORS

    morning   = df[df['time_of_day'] == 'morning']
    midday    = df[df['time_of_day'] == 'midday']
    afternoon = df[df['time_of_day'] == 'afternoon']

    # ── Part A: Morning SL sweep ───────────────────────────────────────────────
    print("\n\n" + "="*70)
    print("  PART A: MORNING SL SWEEP  (09:30–11:00)")
    print(f"  N={len(morning)} signals")
    print("="*70)
    res_morning = sl_sweep_table(morning, bars_cache, SL_FACTORS)
    print_sl_sweep(res_morning)

    best_morning_sl = max(res_morning, key=lambda r: r['atr_per_sig'])['sl_factor'] if res_morning else 0.15

    # ── Part B: Midday + Afternoon SL sweep ────────────────────────────────────
    print("\n\n" + "="*70)
    print("  PART B: MIDDAY SL SWEEP  (11:00–14:00)")
    print(f"  N={len(midday)} signals")
    print("="*70)
    res_midday = sl_sweep_table(midday, bars_cache, SL_FACTORS)
    print_sl_sweep(res_midday)
    best_midday_sl = max(res_midday, key=lambda r: r['atr_per_sig'])['sl_factor'] if res_midday else 0.15

    print("\n\n" + "="*70)
    print("  PART B: AFTERNOON SL SWEEP  (14:00–16:00)")
    print(f"  N={len(afternoon)} signals")
    print("="*70)
    res_afternoon = sl_sweep_table(afternoon, bars_cache, SL_FACTORS)
    print_sl_sweep(res_afternoon)
    best_afternoon_sl = max(res_afternoon, key=lambda r: r['atr_per_sig'])['sl_factor'] if res_afternoon else 0.15

    print(f"\n  Best morning SL: {best_morning_sl:.2f} ATR")
    print(f"  Best midday  SL: {best_midday_sl:.2f} ATR")
    print(f"  Best afternoon SL: {best_afternoon_sl:.2f} ATR")

    # ── Part C: Adaptive strategy comparison ──────────────────────────────────
    print("\n\n" + "="*70)
    print("  PART C: ADAPTIVE SL STRATEGY COMPARISON")
    print("="*70)

    strategies = [
        ('Flat 0.15 ATR (current)',   0.15, 0.15, 0.15),
        ('Flat 0.75 ATR (overall opt)', 0.75, 0.75, 0.75),
        ('Time-adaptive',             best_morning_sl, best_midday_sl, best_afternoon_sl),
        ('No SL (hold 60m)',          999.0, 999.0, 999.0),
    ]

    print(f"\n  {'Strategy':<35}  {'N':>6}  {'SL_hit%':>8}  {'Net ATR':>9}  {'ATR/sig':>8}  {'Win%':>7}")
    print("  " + "-"*35 + "  " + "-"*6 + "  " + "-"*8 + "  " + "-"*9 + "  " + "-"*8 + "  " + "-"*7)

    best_net = None
    best_strat_name = ''
    strat_results = []

    for strat_name, sl_m, sl_d, sl_a in strategies:
        # Evaluate each time window with its own SL, then aggregate
        parts = [
            (morning,   sl_m),
            (midday,    sl_d),
            (afternoon, sl_a),
        ]
        combined = []
        for subset, sl_f in parts:
            r = evaluate_sl_factor(subset, bars_cache, sl_f)
            if r:
                combined.append(r)
        if not combined:
            continue

        total_n   = sum(r['N'] for r in combined)
        total_net = sum(r['net_atr'] for r in combined)
        total_hits= sum(r['sl_hit_pct'] * r['N'] / 100 for r in combined)
        # Re-compute wins: need raw pnl > 0 count — approximate via win_pct
        total_wins= sum(r['win_pct'] * r['N'] / 100 for r in combined)

        sl_hit_pct = total_hits / total_n * 100 if total_n > 0 else 0
        atr_per_sig= total_net / total_n if total_n > 0 else 0
        win_pct    = total_wins / total_n * 100 if total_n > 0 else 0

        marker = ''
        if best_net is None or total_net > best_net:
            best_net = total_net
            best_strat_name = strat_name
            marker = ' ★'

        strat_results.append((strat_name, total_n, sl_hit_pct, total_net, atr_per_sig, win_pct, marker))

    # Print with ★ on winner (re-scan to place correctly)
    best_net2 = max(r[3] for r in strat_results) if strat_results else None
    for strat_name, total_n, sl_hit_pct, total_net, atr_per_sig, win_pct, _ in strat_results:
        marker = ' ★' if total_net == best_net2 else ''
        print(f"  {strat_name:<35}  {total_n:>6}  {sl_hit_pct:>7.1f}%"
              f"  {total_net:>+9.1f}  {atr_per_sig:>+8.3f}  {win_pct:>6.1f}%{marker}")

    # ── Part D: Morning vol filter combo ───────────────────────────────────────
    print("\n\n" + "="*70)
    print("  PART D: MORNING VOL FILTER COMBO")
    print("  Morning signals split by vol ≤2x vs vol >2x")
    print("="*70)

    morn_lo_vol = morning[morning['vol_ratio'] <= 2.0]
    morn_hi_vol = morning[morning['vol_ratio'] >  2.0]

    print(f"\n  Morning vol ≤2x  (N={len(morn_lo_vol)})")
    res_mlo = sl_sweep_table(morn_lo_vol, bars_cache, SL_FACTORS)
    print_sl_sweep(res_mlo)

    print(f"\n  Morning vol >2x  (N={len(morn_hi_vol)})")
    res_mhi = sl_sweep_table(morn_hi_vol, bars_cache, SL_FACTORS)
    print_sl_sweep(res_mhi)

    # Threshold scan: vol ≤ X where tight SL (0.15) beats baseline
    print("\n  Morning vol threshold scan — flat 0.15 ATR SL:")
    print(f"  {'Vol ≤':<10}  {'N':>6}  {'SL_hit%':>8}  {'ATR/sig':>8}")
    print("  " + "-"*10 + "  " + "-"*6 + "  " + "-"*8 + "  " + "-"*8)
    for thresh in [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]:
        sub = morning[morning['vol_ratio'] <= thresh]
        if len(sub) < 10:
            continue
        r = evaluate_sl_factor(sub, bars_cache, 0.15)
        if r:
            print(f"  vol ≤{thresh:<5.1f}  {r['N']:>6}  {r['sl_hit_pct']:>7.1f}%  {r['atr_per_sig']:>+8.3f}")

    # Overall recommendation
    print("\n\n" + "="*70)
    print("  PART C–D RECOMMENDATION")
    print("="*70)
    if strat_results:
        best_row = max(strat_results, key=lambda r: r[3])
        print(f"\n  ★ Best strategy: '{best_row[0]}'")
        print(f"    Net ATR={best_row[3]:+.1f}  ATR/sig={best_row[4]:+.4f}  Win%={best_row[5]:.1f}%")
    print(f"\n  Morning: best SL={best_morning_sl:.2f} ATR | "
          f"Midday: {best_midday_sl:.2f} ATR | "
          f"Afternoon: {best_afternoon_sl:.2f} ATR")
    print()


def main():
    print("\n" + "="*70)
    print("  KLB v3.4 Stop-Loss Predictor")
    print("="*70)

    # ── Step 0: Load logs ─────────────────────────────────────────────────────
    log_files = sorted(LOG_DIR.glob(V34_GLOB))
    log_files_8m = []
    for fp in log_files:
        hash_part = fp.stem.split('_')[-1]
        if hash_part in SKIP_HASHES:
            print(f"  Skipping (9 März): {fp.name}")
            continue
        # Check mtime for safety
        import os
        mtime = os.path.getmtime(fp)
        mdate = pd.Timestamp(mtime, unit='s', tz='UTC').tz_convert('Europe/Berlin').date()
        if str(mdate) == '2026-03-09':
            print(f"  Skipping (mtime 9 März): {fp.name}")
            continue
        log_files_8m.append(fp)

    print(f"\n  Using {len(log_files_8m)} log files (8 März only)\n")

    # Parse + identify symbols
    all_records = []
    sym_cache = {}  # symbol -> bars_1m
    seen_symbols = set()  # deduplicate: only 1 file per symbol

    for fp in log_files_8m:
        signals = parse_pine_log(fp)
        if not signals:
            continue
        sym = identify_symbol(signals)
        if sym is None:
            print(f"  ⚠  Could not identify symbol for {fp.name}")
            continue
        if sym in seen_symbols:
            print(f"  {fp.name[-20:]} → {sym} (DUPLICATE — skipped)")
            continue
        seen_symbols.add(sym)
        print(f"  {fp.name[-20:]} → {sym} ({len(signals)} raw signals)")

        # Load 1m bars (cached)
        if sym not in sym_cache:
            try:
                sym_cache[sym] = load_1m(sym)
            except Exception as e:
                print(f"     ✗ Could not load 1m bars for {sym}: {e}")
                continue
        bars_1m = sym_cache[sym]

        # SL outcome
        measure_sl_outcome(signals, bars_1m)

        for sig in signals:
            sig['symbol'] = sym
        all_records.extend(signals)

    print(f"\n  Total raw signals parsed: {len(all_records)}")

    df_all = pd.DataFrame(all_records)

    # ── Filter to BRK + REV only (skip QBS, EXREV, RNG, FADE) ───────────────
    df = df_all[df_all['sig_type'].isin(['BRK', 'REV'])].copy()
    df = df[df['sl_hit'].notna()].copy()
    print(f"  BRK+REV signals with valid SL outcome: {len(df)}")

    # ── Add feature columns ───────────────────────────────────────────────────
    # Time of day
    df['time_of_day'] = df['timestamp'].apply(classify_time)

    # Level type
    df['level_type'] = df['levels'].apply(classify_level_type)

    # Bucketed features
    df['vol_bucket'] = df['vol_ratio'].apply(
        lambda v: bucket(v, [1, 2, 3, 5], ['<1x', '1-2x', '2-3x', '3-5x', '>5x']))
    df['pos_pct'] = df['close_pos'].apply(
        lambda p: int(p[1:]) if isinstance(p, str) and len(p) > 1 else None)
    df['pos_bucket'] = df['pos_pct'].apply(
        lambda v: bucket(v, [25, 50, 75], ['<25', '25-50', '50-75', '>75']))
    df['adx_bucket'] = df['adx'].apply(
        lambda v: bucket(v, [20, 30, 40], ['<20', '20-30', '30-40', '>40']))
    df['body_bucket'] = df['body_pct'].apply(
        lambda v: bucket(v, [30, 50, 70], ['<30', '30-50', '50-70', '>70']))
    df['range_atr_bucket'] = df['range_atr'].apply(
        lambda v: bucket(v, [0.3, 0.6, 1.0], ['<0.3', '0.3-0.6', '0.6-1.0', '>1.0']))
    df['ramp_bucket'] = df['ramp'].apply(
        lambda v: bucket(v, [0.5, 1.0, 2.0], ['<0.5', '0.5-1x', '1-2x', '>2x']))
    df['rs_bucket'] = df['rs'].apply(
        lambda v: bucket(v, [-1, 0, 1], ['<-1%', '-1-0%', '0-1%', '>1%']))

    baseline_sl = df['sl_hit'].mean() * 100
    baseline_pnl = df['pnl_60m'].mean()
    print(f"\n  Baseline SL rate: {baseline_sl:.1f}%")
    print(f"  Baseline P&L/signal: {baseline_pnl:+.3f} ATR")
    n_sl = int(df['sl_hit'].sum())
    n_surv = len(df) - n_sl
    print(f"  SL_HIT: {n_sl}  SURVIVED: {n_surv}")

    # ── Step 2: Feature importance tables ────────────────────────────────────
    print("\n\n" + "="*70)
    print("  STEP 2: FEATURE IMPORTANCE")
    print("="*70)

    features = [
        ('vol_bucket', 'Volume ratio'),
        ('pos_bucket', 'Position in range (percentile)'),
        ('adx_bucket', 'ADX'),
        ('body_bucket', 'Body %'),
        ('range_atr_bucket', 'Range (ATR)'),
        ('time_of_day', 'Time of day'),
        ('sig_type', 'Signal type'),
        ('direction', 'Direction'),
        ('ema', 'EMA alignment'),
        ('vwap', 'VWAP alignment'),
        ('ramp_bucket', 'Volume ramp'),
        ('rs_bucket', 'Relative strength vs SPY'),
        ('level_type', 'Level type'),
        ('symbol', 'Symbol'),
    ]

    for col, name in features:
        tbl = feature_table(df, col)
        print_feature_table(name, tbl, baseline_sl)

    # ── Step 3: Filter simulation ──────────────────────────────────────────────
    print("\n\n" + "="*70)
    print("  STEP 3: FILTER SIMULATION")
    print(f"  Baseline: N={len(df)}, SL%={baseline_sl:.1f}%, P&L/sig={baseline_pnl:+.3f}")
    print(f"  Filter criteria: SL drop >5pp, P&L improve >0.005 ATR, N>=500")
    print("="*70)

    # Build candidate filters
    filters = []

    # Vol-based
    filters.append(('vol>5x remove', df['vol_ratio'] > 5))
    filters.append(('vol>3x remove', df['vol_ratio'] > 3))
    filters.append(('vol<1x remove', df['vol_ratio'] < 1))

    # Body
    filters.append(('body<30% remove', df['body_pct'] < 30))
    filters.append(('body>70% only (remove <70)', df['body_pct'] < 70))

    # Range ATR
    filters.append(('rangeATR>1.0 remove', df['range_atr'] > 1.0))
    filters.append(('rangeATR>0.6 remove', df['range_atr'] > 0.6))

    # ADX
    filters.append(('adx>30 remove', df['adx'].notna() & (df['adx'] > 30)))
    filters.append(('adx>40 remove', df['adx'].notna() & (df['adx'] > 40)))

    # Time of day
    filters.append(('afternoon remove', df['time_of_day'] == 'afternoon'))
    filters.append(('morning remove', df['time_of_day'] == 'morning'))

    # EMA
    filters.append(('ema=flat remove', df['ema'] == 'flat'))
    filters.append(('counter-EMA remove', df['is_counter_ema']))

    # Ramp
    filters.append(('ramp>2x remove', df['ramp'] > 2.0))

    # Position
    filters.append(('pos<25 remove (extremes low)', df['pos_pct'].notna() & (df['pos_pct'] < 25)))
    filters.append(('pos>75 remove (extremes high)', df['pos_pct'].notna() & (df['pos_pct'] > 75)))

    # VWAP
    filters.append(('vwap misaligned: bull+below or bear+above',
                    ((df['direction'] == 'bull') & (df['vwap'] == 'below')) |
                    ((df['direction'] == 'bear') & (df['vwap'] == 'above'))))

    print(f"\n  {'Filter':<45} {'Removed':>8}  {'Kept':>6}  {'SL%':>6}  {'ΔSL':>7}  {'P&L':>7}  {'ΔPNL':>7}  {'Pass?':>6}")
    print(f"  {'-'*45} {'-'*8}  {'-'*6}  {'-'*6}  {'-'*7}  {'-'*7}  {'-'*7}  {'-'*6}")

    passing_filters = []
    filter_results = []
    for fname, mask in filters:
        r = simulate_filter(df, mask, fname)
        if r is None:
            continue
        filter_results.append((fname, mask, r))
        pass_str = '★ YES' if r['passes'] else 'no'
        print(f"  {fname:<45} {r['N_removed']:>8}  {r['N_kept']:>6}  "
              f"{r['SL_kept_%']:>5.1f}%  {r['delta_SL_pp']:>+6.1f}pp  "
              f"{r['pnl_kept']:>+6.3f}  {r['delta_pnl']:>+6.3f}  {pass_str:>6}")
        if r['passes']:
            passing_filters.append((fname, mask))

    # ── Step 4: Combination filters ────────────────────────────────────────────
    print("\n\n" + "="*70)
    print("  STEP 4: COMBINATION FILTERS")
    print("="*70)

    # Use top single filters + some logic combos
    combo_defs = []

    # Take up to 5 passing filters and test pairwise
    pf = passing_filters[:5]
    for i in range(len(pf)):
        for j in range(i+1, len(pf)):
            n1, m1 = pf[i]
            n2, m2 = pf[j]
            combo_defs.append((f"{n1}  AND  {n2}", m1 | m2))

    # Manual combos based on known patterns
    combo_defs.append(('rangeATR>0.6 + vol>3x', (df['range_atr'] > 0.6) | (df['vol_ratio'] > 3)))
    combo_defs.append(('body<30% + adx>30', (df['body_pct'] < 30) | (df['adx'].notna() & (df['adx'] > 30))))
    combo_defs.append(('afternoon + vol>3x', (df['time_of_day'] == 'afternoon') | (df['vol_ratio'] > 3)))
    combo_defs.append(('counter-EMA + vol>3x', df['is_counter_ema'] | (df['vol_ratio'] > 3)))
    combo_defs.append(('counter-EMA + rangeATR>0.6',
                       df['is_counter_ema'] | (df['range_atr'] > 0.6)))
    combo_defs.append(('vwap misalign + rangeATR>0.6',
                       (((df['direction'] == 'bull') & (df['vwap'] == 'below')) |
                        ((df['direction'] == 'bear') & (df['vwap'] == 'above'))) |
                       (df['range_atr'] > 0.6)))

    print(f"\n  {'Combo filter':<55} {'Removed':>8}  {'Kept':>6}  {'SL%':>6}  {'ΔSL':>7}  {'P&L':>7}  {'ΔPNL':>7}  {'Pass?':>6}")
    print(f"  {'-'*55} {'-'*8}  {'-'*6}  {'-'*6}  {'-'*7}  {'-'*7}  {'-'*7}  {'-'*6}")

    best_combos = []
    for cname, cmask in combo_defs:
        r = simulate_filter(df, cmask, cname)
        if r is None:
            continue
        pass_str = '★ YES' if r['passes'] else 'no'
        print(f"  {cname:<55} {r['N_removed']:>8}  {r['N_kept']:>6}  "
              f"{r['SL_kept_%']:>5.1f}%  {r['delta_SL_pp']:>+6.1f}pp  "
              f"{r['pnl_kept']:>+6.3f}  {r['delta_pnl']:>+6.3f}  {pass_str:>6}")
        if r['passes']:
            best_combos.append((cname, r))

    # ── Step 5: Summary ────────────────────────────────────────────────────────
    print("\n\n" + "="*70)
    print("  STEP 5: SUMMARY & RECOMMENDATIONS")
    print("="*70)
    print(f"\n  Dataset: {len(df)} BRK+REV signals | "
          f"SL={SL_FACTOR}×ATR | Hold={HOLD_BARS}m")
    print(f"  Baseline: {baseline_sl:.1f}% SL rate | {baseline_pnl:+.3f} ATR/sig")

    all_passing = [(n, r) for n, _, r in filter_results if r['passes']] + best_combos
    if all_passing:
        print(f"\n  Filters passing all 3 criteria (SL drop >5pp, ΔPNL >0.005, N>=500):\n")
        for fname, r in sorted(all_passing, key=lambda x: x[1]['delta_pnl'], reverse=True):
            print(f"  ★ {fname}")
            print(f"      N kept={r['N_kept']} ({r['N_removed']} removed)  "
                  f"SL={r['SL_kept_%']:.1f}% (Δ{r['delta_SL_pp']:+.1f}pp)  "
                  f"P&L={r['pnl_kept']:+.3f} (Δ{r['delta_pnl']:+.3f})")
    else:
        print("\n  No single filter or combo passed all 3 criteria.")
        print("  See per-feature tables above for directional guidance.")

    # Distribution stats by symbol
    print("\n\n  Signal counts by symbol:")
    sym_stats = df.groupby('symbol').agg(
        N=('sl_hit', 'count'),
        SL_pct=('sl_hit', lambda x: round(x.mean()*100, 1)),
        pnl=('pnl_60m', lambda x: round(x.mean(), 3))
    ).sort_values('N', ascending=False)
    print(sym_stats.to_string())

    print("\n  Signal counts by type × direction:")
    td = df.groupby(['sig_type', 'direction']).agg(
        N=('sl_hit', 'count'),
        SL_pct=('sl_hit', lambda x: round(x.mean()*100, 1)),
        pnl=('pnl_60m', lambda x: round(x.mean(), 3))
    )
    print(td.to_string())

    # ── Parts A–D: Time-of-day adaptive SL sweep ──────────────────────────────
    run_adaptive_sl_sections(df, sym_cache)

    print("\n" + "="*70)
    print("  Done.")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
