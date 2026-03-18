#!/usr/bin/env python3
"""
KLB Exit Timing Research — When should we exit winning signals?
===============================================================
Analyzes the full 1m P&L path for winning v3.3c signals to find
the optimal exit rule (fixed time, trailing stop, or hybrid).

Steps:
  1. Load v3.3c signals (same pipeline as v33c_backtest.py)
  2. Filter to WIN signals with mfe_atr >= 0.10
  3. Reconstruct P&L at every minute (0-60m)
  4. Find time-to-peak, decay, and breakdowns by sig_type / time_of_day / tier
  5. Simulate 6 exit rules and compare net ATR vs 60m hold baseline
  6. Cross-reference with move catalog bars_to_mfe_1m

Usage: python3 exit_timing_research.py
Output: debug/exit_timing_research_results.txt (and console)
"""

import sys
import os
import glob
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import time as dtime

warnings.filterwarnings('ignore')

# ── Import shared infrastructure from v33_backtest ─────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

from v33_backtest import (
    parse_pine_log,
    identify_symbol,
    load_1m,
    load_daily,
    compute_atr,
    SYMBOLS,
    BAR_DIR,
    LOG_DIR,
)

# ── Config ──────────────────────────────────────────────────────────────────
V33C_GLOB = 'pine-logs-Key Level Breakout v3.3c_*.csv'
HIGH_LEVEL_KEYWORDS = ['PM H', 'ORB H', 'Yest H', 'Week H']

WIN_MFE_THRESHOLD = 0.10   # ATR — only analyze these "real winners"
FORWARD_MINUTES   = 60     # same window used in existing backtest

# Exit rule checkpoints (minutes post-signal)
CHECKPOINTS = [5, 10, 15, 20, 25, 30, 45, 60]

# Trailing stop levels (ATR units of drawdown from peak)
TRAIL_LEVELS = [0.10, 0.15, 0.20]

DIVIDER = '=' * 74
SUBDIV  = '-' * 74


# ── Bull REV at HIGH suppression (v3.3c rule) ────────────────────────────
def is_bull_rev_at_high(sig):
    if sig.get('direction') != 'bull':
        return False
    if 'REV' not in sig.get('sig_type', ''):
        return False
    levels = sig.get('levels', '')
    return any(kw in levels for kw in HIGH_LEVEL_KEYWORDS)


# ── Load v3.3c pine logs ─────────────────────────────────────────────────
def load_v33c_signals():
    files = sorted(glob.glob(str(LOG_DIR / V33C_GLOB)))
    print(f'  Found {len(files)} v3.3c log files')
    all_signals = []
    for fp in files:
        short = Path(fp).name.split('_')[-1].replace('.csv', '')
        signals = parse_pine_log(fp)
        if not signals:
            print(f'    {short}: 0 signals (empty)')
            continue
        symbol = identify_symbol(signals)
        if symbol is None:
            print(f'    {short}: could not identify symbol')
            continue
        for s in signals:
            s['symbol'] = symbol
            s['version'] = 'v33c'
            s['log_file'] = short
        all_signals.extend(signals)
        print(f'    {short}: {symbol} — {len(signals)} signals')
    return all_signals


# ── Reconstruct full 1m P&L path ─────────────────────────────────────────
def build_pnl_path(sig, bars_1m, atr):
    """
    Return a dict with p&l at each checkpoint minute and peak info.

    For bull: pnl_at_N = (close[signal+N] - entry) / ATR
    For bear: pnl_at_N = (entry - close[signal+N]) / ATR

    Additionally computes:
      - peak_minute  : minute (1-60) when running P&L peaks
      - pnl_at_peak  : peak P&L (in ATR)
      - pnl_at_60m   : P&L if held to 60m (or market close)
      - pnl_decay    : peak minus final (how much given back)
    """
    ts = sig['timestamp']
    direction = sig['direction']
    entry = sig.get('close')

    if entry is None or atr is None or atr == 0:
        return None

    # Localise to US/Eastern
    if ts.tzinfo is None:
        ts_et = pd.Timestamp(ts, tz='US/Eastern')
    else:
        ts_et = ts.tz_convert('US/Eastern')

    # Entry at next 1m bar after signal
    start_time = ts_et + pd.Timedelta(minutes=1)
    eod = ts_et.normalize() + pd.Timedelta(hours=16)
    end_time = min(ts_et + pd.Timedelta(minutes=FORWARD_MINUTES), eod)

    mask = (bars_1m.index >= start_time) & (bars_1m.index <= end_time)
    forward = bars_1m[mask].copy()

    if len(forward) == 0:
        return None

    # Running P&L using close prices (realised exit)
    if direction == 'bull':
        running_pnl = (forward['close'] - entry) / atr
    else:
        running_pnl = (entry - forward['close']) / atr

    # Running MFE using high/low (best possible)
    if direction == 'bull':
        running_mfe = (forward['high'] - entry) / atr
    else:
        running_mfe = (entry - forward['low']) / atr

    # Build minute-offset array (1 = first bar after signal) as numpy array
    minutes_arr = ((forward.index - start_time).total_seconds() / 60).astype(int).values + 1
    pnl_arr = running_pnl.values

    result = {'n_bars': len(forward)}

    # P&L at each checkpoint (using close of the bar at or before cp minutes)
    for cp in CHECKPOINTS:
        idxs = np.where(minutes_arr <= cp)[0]
        if len(idxs) > 0:
            result[f'pnl_at_{cp}m'] = pnl_arr[idxs[-1]]
        else:
            result[f'pnl_at_{cp}m'] = pnl_arr[-1]  # truncated — use final

    # Peak P&L (best close in direction)
    peak_pos = int(np.argmax(pnl_arr))
    result['pnl_at_peak']  = float(pnl_arr[peak_pos])
    result['peak_minute']  = int(minutes_arr[peak_pos])
    result['pnl_at_60m']   = float(pnl_arr[-1])
    result['pnl_decay']    = result['pnl_at_peak'] - result['pnl_at_60m']

    # MFE peak (using high/low for reference)
    result['mfe_peak'] = float(running_mfe.values.max())

    # Trailing stop simulation: exit when P&L drops trail_atr from running peak
    running_max_arr = np.maximum.accumulate(pnl_arr)
    for trail in TRAIL_LEVELS:
        drawdown = running_max_arr - pnl_arr
        triggered = np.where(drawdown >= trail)[0]
        if len(triggered) > 0:
            exit_pos = int(triggered[0])
            result[f'trail_{trail:.2f}_pnl']    = float(pnl_arr[exit_pos])
            result[f'trail_{trail:.2f}_minute']  = int(minutes_arr[exit_pos])
        else:
            result[f'trail_{trail:.2f}_pnl']    = float(pnl_arr[-1])
            result[f'trail_{trail:.2f}_minute']  = int(minutes_arr[-1])

    # Time+trail hybrid: exit at 30m OR when pnl >= 0.25 ATR, whichever first
    exited_early = False
    for pos, (min_i, pnl_val) in enumerate(zip(minutes_arr, pnl_arr)):
        if pnl_val >= 0.25 or min_i >= 30:
            result['hybrid_30m_025_pnl']    = float(pnl_val)
            result['hybrid_30m_025_minute'] = int(min_i)
            exited_early = True
            break
    if not exited_early:
        result['hybrid_30m_025_pnl']    = float(pnl_arr[-1])
        result['hybrid_30m_025_minute'] = int(minutes_arr[-1])

    return result


# ── Classify time of day ─────────────────────────────────────────────────
def classify_tod(ts):
    t = ts.time() if hasattr(ts, 'time') else ts
    if isinstance(t, pd.Timestamp):
        t = t.time()
    if dtime(9, 30) <= t < dtime(11, 0):
        return 'morning'
    elif dtime(11, 0) <= t < dtime(14, 0):
        return 'midday'
    else:
        return 'afternoon'


# ── Classify tier based on mfe_atr ──────────────────────────────────────
def classify_tier(mfe_atr):
    if mfe_atr >= 0.60:
        return 'S'
    elif mfe_atr >= 0.40:
        return 'A'
    else:
        return 'B'


# ── P&L path summary ─────────────────────────────────────────────────────
def pnl_path_summary(paths_df, label='All'):
    """Print average P&L at each checkpoint and peak stats."""
    n = len(paths_df)
    if n == 0:
        print(f'  {label}: N=0')
        return
    print(f'\n  {label} (N={n}):')
    cols = [f'pnl_at_{cp}m' for cp in CHECKPOINTS]
    avgs = {cp: paths_df[f'pnl_at_{cp}m'].mean() for cp in CHECKPOINTS}
    avg_peak  = paths_df['pnl_at_peak'].mean()
    avg_decay = paths_df['pnl_decay'].mean()
    avg_peak_min = paths_df['peak_minute'].mean()

    line = '    Exit@: ' + '  '.join(f'{cp:>3}m={avgs[cp]:+.3f}' for cp in CHECKPOINTS)
    print(line)
    print(f'    Peak:  avg_peak={avg_peak:.3f} ATR  avg_peak_minute={avg_peak_min:.1f}m  avg_decay={avg_decay:.3f} ATR')


# ── Time-to-peak distribution ────────────────────────────────────────────
def peak_distribution(paths_df, label='All'):
    buckets = [(0, 5), (5, 10), (10, 15), (15, 20), (20, 30), (30, 45), (45, 60)]
    n = len(paths_df)
    if n == 0:
        return
    print(f'\n  Time-to-Peak Distribution — {label} (N={n}):')
    cumulative = 0
    for lo, hi in buckets:
        count = ((paths_df['peak_minute'] > lo) & (paths_df['peak_minute'] <= hi)).sum()
        pct   = count / n * 100
        cumulative += pct
        bar = '█' * int(pct / 2)
        print(f'    {lo:>2}-{hi:>2}m: {count:>4} ({pct:>5.1f}%)  cumul={cumulative:>5.1f}%  {bar}')
    # Over 60
    over60 = (paths_df['peak_minute'] > 60).sum()
    print(f'    >60m:  {over60:>4} ({over60/n*100:>5.1f}%)')

    # Key thresholds
    for thresh in [10, 15, 20, 30]:
        pct_by = (paths_df['peak_minute'] <= thresh).mean() * 100
        print(f'    Peaked by {thresh:>2}m: {pct_by:.1f}%')


# ── Exit rule simulation ─────────────────────────────────────────────────
def simulate_exit_rules(paths_df):
    """Compute net ATR for each exit rule across all winning signals."""
    n = len(paths_df)
    if n == 0:
        return {}

    rules = {}

    # 1. Baseline: hold 60m
    rules['hold_60m'] = {
        'label'    : 'Hold 60m (baseline)',
        'net_atr'  : paths_df['pnl_at_60m'].sum(),
        'avg_pnl'  : paths_df['pnl_at_60m'].mean(),
        'pct_pos'  : (paths_df['pnl_at_60m'] > 0).mean() * 100,
    }

    # 2-3. Fixed exits
    for cp in [15, 20, 25, 30]:
        col = f'pnl_at_{cp}m'
        rules[f'fixed_{cp}m'] = {
            'label'   : f'Fixed exit {cp}m',
            'net_atr' : paths_df[col].sum(),
            'avg_pnl' : paths_df[col].mean(),
            'pct_pos' : (paths_df[col] > 0).mean() * 100,
        }

    # 4-6. Trailing stops
    for trail in TRAIL_LEVELS:
        col = f'trail_{trail:.2f}_pnl'
        if col in paths_df.columns:
            rules[f'trail_{trail:.2f}'] = {
                'label'   : f'Trailing stop {trail:.2f} ATR',
                'net_atr' : paths_df[col].sum(),
                'avg_pnl' : paths_df[col].mean(),
                'pct_pos' : (paths_df[col] > 0).mean() * 100,
            }

    # 7. Hybrid 30m / 0.25 ATR
    if 'hybrid_30m_025_pnl' in paths_df.columns:
        rules['hybrid_30m_025'] = {
            'label'   : 'Hybrid: exit@30m OR pnl≥0.25ATR',
            'net_atr' : paths_df['hybrid_30m_025_pnl'].sum(),
            'avg_pnl' : paths_df['hybrid_30m_025_pnl'].mean(),
            'pct_pos' : (paths_df['hybrid_30m_025_pnl'] > 0).mean() * 100,
        }

    return rules


# ── Main ─────────────────────────────────────────────────────────────────
def main():
    import io
    # Tee output to both console and file
    out_path = LOG_DIR / 'exit_timing_research_results.txt'
    output_lines = []

    class Tee:
        def write(self, s):
            sys.stdout_real.write(s)
            output_lines.append(s)
        def flush(self):
            sys.stdout_real.flush()

    sys.stdout_real = sys.stdout
    sys.stdout = Tee()

    print(DIVIDER)
    print('KLB Exit Timing Research — Optimal Exit for Winning Signals')
    print('v3.3c logs  |  1m IB price path  |  60-min forward window')
    print(DIVIDER)
    print()

    # ── Step 1: Load v3.3c signals ────────────────────────────────────────
    print('Step 1: Loading v3.3c pine logs...')
    all_signals = load_v33c_signals()
    print(f'  Total raw signals: {len(all_signals)}')

    # Apply v3.3c suppression (bull REV at HIGH)
    signals = [s for s in all_signals if not is_bull_rev_at_high(s)]
    print(f'  After v3.3c suppression: {len(signals)}')
    print()

    # ── Step 2: Load IB 1m data ───────────────────────────────────────────
    print('Step 2: Loading IB 1m data + ATR...')
    ib_cache = {}
    symbols_needed = sorted(set(s['symbol'] for s in signals))
    for sym in symbols_needed:
        print(f'  {sym}...', end=' ', flush=True)
        try:
            bars_1m  = load_1m(sym)
            daily_df = load_daily(sym)
            atr_ser  = compute_atr(daily_df)
            ib_cache[sym] = (bars_1m, atr_ser)
            print(f'{len(bars_1m)} bars')
        except Exception as e:
            print(f'ERROR: {e}')
    print()

    # ── Step 3: Measure MFE/MAE + build P&L paths ─────────────────────────
    print('Step 3: Measuring MFE/MAE (60m window) and building P&L paths...')

    enriched = []
    for sig in signals:
        sym = sig['symbol']
        if sym not in ib_cache:
            continue
        bars_1m, atr_ser = ib_cache[sym]

        ts = sig['timestamp']
        if hasattr(ts, 'date'):
            sig_date = ts.date()
        else:
            sig_date = pd.Timestamp(ts).date()

        atr_val = sig.get('atr')
        if atr_val is None or atr_val == 0:
            atr_val = atr_ser.get(sig_date)

        if atr_val is None or atr_val == 0:
            continue

        entry = sig.get('close')
        if entry is None:
            continue

        # Quick MFE/MAE check (using existing measure_mfe_mae logic inline)
        if ts.tzinfo is None:
            ts_et = pd.Timestamp(ts, tz='US/Eastern')
        else:
            ts_et = ts.tz_convert('US/Eastern')

        start_time = ts_et + pd.Timedelta(minutes=1)
        eod        = ts_et.normalize() + pd.Timedelta(hours=16)
        end_time   = min(ts_et + pd.Timedelta(minutes=FORWARD_MINUTES), eod)

        mask   = (bars_1m.index >= start_time) & (bars_1m.index <= end_time)
        fwd    = bars_1m[mask]
        if len(fwd) == 0:
            continue

        direction = sig['direction']
        if direction == 'bull':
            fav  = (fwd['high'] - entry)
            adv  = (entry - fwd['low'])
        else:
            fav  = (entry - fwd['low'])
            adv  = (fwd['high'] - entry)

        mfe     = max(0, fav.max())
        mae     = max(0, adv.max())
        mfe_atr = mfe / atr_val
        mae_atr = mae / atr_val

        # WIN: mfe >= 0.10 ATR AND mfe > mae
        if not (mfe_atr >= WIN_MFE_THRESHOLD and mfe > mae):
            continue

        # Build full P&L path
        path = build_pnl_path(sig, bars_1m, atr_val)
        if path is None:
            continue

        tod  = classify_tod(ts)
        tier = classify_tier(mfe_atr)

        row = {
            'symbol'      : sym,
            'timestamp'   : ts,
            'sig_type'    : sig.get('sig_type', '?'),
            'direction'   : direction,
            'mfe_atr'     : mfe_atr,
            'mae_atr'     : mae_atr,
            'tod'         : tod,
            'tier'        : tier,
            'atr'         : atr_val,
        }
        row.update(path)
        enriched.append(row)

    df = pd.DataFrame(enriched)
    print(f'  Total winning signals with P&L paths: {len(df)}')
    if len(df) == 0:
        print('  ERROR: No winning signals found — check log files')
        sys.stdout = sys.stdout_real
        return
    print()

    # ── Step 4: Aggregate Analysis ───────────────────────────────────────
    print(DIVIDER)
    print('SECTION A — P&L PATH (average P&L if you exited at exactly Nm)')
    print(SUBDIV)
    pnl_path_summary(df, 'All winning signals')

    # By signal type
    print()
    print('  Breakdown by signal type:')
    for stype in sorted(df['sig_type'].unique()):
        sub = df[df['sig_type'] == stype]
        pnl_path_summary(sub, f'{stype} (N={len(sub)})')

    print()
    print(DIVIDER)
    print('SECTION B — TIME-TO-PEAK DISTRIBUTION')
    print(SUBDIV)
    peak_distribution(df, 'All winning signals')

    print()
    print('  By signal type:')
    for stype in sorted(df['sig_type'].unique()):
        sub = df[df['sig_type'] == stype]
        peak_distribution(sub, stype)

    print()
    print(DIVIDER)
    print('SECTION C — P&L DECAY ANALYSIS')
    print(SUBDIV)

    early_peak  = df[df['peak_minute'] <= 15]
    mid_peak    = df[(df['peak_minute'] > 15) & (df['peak_minute'] <= 30)]
    late_peak   = df[df['peak_minute'] > 30]

    for label, sub in [('Early peak (0-15m)', early_peak),
                        ('Mid peak (15-30m)',  mid_peak),
                        ('Late peak (30m+)',   late_peak)]:
        n = len(sub)
        if n == 0:
            continue
        avg_decay   = sub['pnl_decay'].mean()
        avg_peak    = sub['pnl_at_peak'].mean()
        avg_at_60   = sub['pnl_at_60m'].mean()
        decay_pct   = avg_decay / avg_peak * 100 if avg_peak > 0 else 0
        print(f'\n  {label} (N={n}):')
        print(f'    Avg peak P&L:  {avg_peak:.3f} ATR')
        print(f'    Avg at 60m:    {avg_at_60:.3f} ATR')
        print(f'    Avg decay:     {avg_decay:.3f} ATR ({decay_pct:.1f}% of peak given back)')

    print()
    print(DIVIDER)
    print('SECTION D — BREAKDOWN BY SIGNAL TYPE')
    print(SUBDIV)

    hdr = (f"  {'Type':<8} {'N':>5} {'AvgPeak':>8} {'PeakMin':>8} "
           f"{'Pnl@15m':>8} {'Pnl@20m':>8} {'Pnl@30m':>8} {'Pnl@60m':>8} {'Decay':>7}")
    print(hdr)
    print('  ' + '-' * (len(hdr) - 2))
    for stype in sorted(df['sig_type'].unique()):
        sub = df[df['sig_type'] == stype]
        n   = len(sub)
        print(f"  {stype:<8} {n:>5}"
              f"  {sub['pnl_at_peak'].mean():>7.3f}"
              f"  {sub['peak_minute'].mean():>7.1f}"
              f"  {sub['pnl_at_15m'].mean():>7.3f}"
              f"  {sub['pnl_at_20m'].mean():>7.3f}"
              f"  {sub['pnl_at_30m'].mean():>7.3f}"
              f"  {sub['pnl_at_60m'].mean():>7.3f}"
              f"  {sub['pnl_decay'].mean():>6.3f}")

    print()
    print(DIVIDER)
    print('SECTION E — BREAKDOWN BY TIME-OF-DAY')
    print(SUBDIV)

    hdr = (f"  {'TOD':<12} {'N':>5} {'AvgPeak':>8} {'PeakMin':>8} "
           f"{'Pnl@15m':>8} {'Pnl@20m':>8} {'Pnl@30m':>8} {'Pnl@60m':>8} {'Decay':>7}")
    print(hdr)
    print('  ' + '-' * (len(hdr) - 2))
    for tod in ['morning', 'midday', 'afternoon']:
        sub = df[df['tod'] == tod]
        n   = len(sub)
        if n == 0:
            continue
        print(f"  {tod:<12} {n:>5}"
              f"  {sub['pnl_at_peak'].mean():>7.3f}"
              f"  {sub['peak_minute'].mean():>7.1f}"
              f"  {sub['pnl_at_15m'].mean():>7.3f}"
              f"  {sub['pnl_at_20m'].mean():>7.3f}"
              f"  {sub['pnl_at_30m'].mean():>7.3f}"
              f"  {sub['pnl_at_60m'].mean():>7.3f}"
              f"  {sub['pnl_decay'].mean():>6.3f}")

    print()
    print(DIVIDER)
    print('SECTION F — BREAKDOWN BY TIER (great moves vs regular)')
    print(SUBDIV)

    tier_order = ['S', 'A', 'B']
    hdr = (f"  {'Tier':<6} {'N':>5} {'AvgMFE':>8} {'AvgPeak':>8} {'PeakMin':>8} "
           f"{'Pnl@15m':>8} {'Pnl@20m':>8} {'Pnl@30m':>8} {'Pnl@60m':>8} {'Decay':>7}")
    print(hdr)
    print('  ' + '-' * (len(hdr) - 2))
    for tier in tier_order:
        sub = df[df['tier'] == tier]
        n   = len(sub)
        if n == 0:
            continue
        print(f"  {tier:<6} {n:>5}"
              f"  {sub['mfe_atr'].mean():>7.3f}"
              f"  {sub['pnl_at_peak'].mean():>7.3f}"
              f"  {sub['peak_minute'].mean():>7.1f}"
              f"  {sub['pnl_at_15m'].mean():>7.3f}"
              f"  {sub['pnl_at_20m'].mean():>7.3f}"
              f"  {sub['pnl_at_30m'].mean():>7.3f}"
              f"  {sub['pnl_at_60m'].mean():>7.3f}"
              f"  {sub['pnl_decay'].mean():>6.3f}")

    # Extra: do tier S/A runs longer than tier B?
    sa_df = df[df['tier'].isin(['S', 'A'])]
    b_df  = df[df['tier'] == 'B']
    if len(sa_df) and len(b_df):
        print()
        print(f'  Tier S/A (N={len(sa_df)}): avg peak@{sa_df["peak_minute"].mean():.1f}m  '
              f'peaked_by_20m={( sa_df["peak_minute"] <= 20).mean()*100:.1f}%')
        print(f'  Tier B   (N={len(b_df)}): avg peak@{b_df["peak_minute"].mean():.1f}m  '
              f'peaked_by_20m={(b_df["peak_minute"] <= 20).mean()*100:.1f}%')

    # ── Step 5: Exit rule simulation ──────────────────────────────────────
    print()
    print(DIVIDER)
    print('SECTION G — EXIT RULE SIMULATION (net ATR across all winning signals)')
    print(SUBDIV)
    print('  NOTE: These are winning signals only (mfe_atr>=0.10). Net ATR reflects')
    print('  how much of the winner\'s move is captured under each rule.')
    print()

    rules = simulate_exit_rules(df)
    baseline_net = rules.get('hold_60m', {}).get('net_atr', 0)

    hdr = f"  {'Rule':<38} {'N':>5} {'Net ATR':>9} {'Avg P&L':>9} {'%Pos':>7} {'vs 60m':>9}"
    print(hdr)
    print('  ' + '-' * (len(hdr) - 2))
    rule_order = ['hold_60m', 'fixed_15m', 'fixed_20m', 'fixed_25m', 'fixed_30m',
                  'trail_0.10', 'trail_0.15', 'trail_0.20', 'hybrid_30m_025']
    for key in rule_order:
        if key not in rules:
            continue
        r   = rules[key]
        vs  = r['net_atr'] - baseline_net
        vs_str = f'{vs:+.2f}'
        n   = len(df)
        print(f"  {r['label']:<38} {n:>5}"
              f"  {r['net_atr']:>+8.2f}"
              f"  {r['avg_pnl']:>+8.4f}"
              f"  {r['pct_pos']:>6.1f}%"
              f"  {vs_str:>9}")

    # Per-signal-type breakdown of best rules
    print()
    print('  Per-signal-type: best exit rule (max net ATR across fixed exits)')
    print()
    per_type_hdr = (f"  {'Type':<8} {'N':>4}  "
                    f"{'@15m':>7} {'@20m':>7} {'@30m':>7} {'@60m':>7} {'trail0.15':>10} {'best':>8}")
    print(per_type_hdr)
    print('  ' + '-' * (len(per_type_hdr) - 2))
    for stype in sorted(df['sig_type'].unique()):
        sub = df[df['sig_type'] == stype]
        n   = len(sub)
        nets = {
            '@15m'     : sub['pnl_at_15m'].sum(),
            '@20m'     : sub['pnl_at_20m'].sum(),
            '@30m'     : sub['pnl_at_30m'].sum(),
            '@60m'     : sub['pnl_at_60m'].sum(),
            'trail0.15': sub['trail_0.15_pnl'].sum() if 'trail_0.15_pnl' in sub.columns else 0,
        }
        best_rule = max(nets, key=nets.get)
        print(f"  {stype:<8} {n:>4}"
              f"  {nets['@15m']:>+6.2f}"
              f"  {nets['@20m']:>+6.2f}"
              f"  {nets['@30m']:>+6.2f}"
              f"  {nets['@60m']:>+6.2f}"
              f"  {nets['trail0.15']:>+9.2f}"
              f"  {best_rule:>8}")

    # ── Step 6: Move catalog cross-reference ─────────────────────────────
    print()
    print(DIVIDER)
    print('SECTION H — MOVE CATALOG CROSS-REFERENCE (bars_to_mfe_1m)')
    print(SUBDIV)

    try:
        mc_path = LOG_DIR / 'move-catalog.parquet'
        mc = pd.read_parquet(mc_path)

        # Filter to moves that KLB fires on (approximate: tier S/A/B + great_move or high MFE)
        # Use moves with mfe_1m data and filter to higher quality
        mc_valid = mc[mc['bars_to_mfe_1m'].notna()].copy()

        print(f'  Move catalog: {len(mc)} total, {len(mc_valid)} with bars_to_mfe_1m')
        print()

        # Distribution for all valid moves
        def btm_distribution(sub_mc, label):
            n = len(sub_mc)
            if n == 0:
                return
            b = sub_mc['bars_to_mfe_1m']
            print(f'  {label} (N={n}):')
            for thresh in [10, 15, 20, 30, 45]:
                pct = (b <= thresh).mean() * 100
                print(f'    Peak by {thresh:>2}m: {pct:.1f}%')
            print(f'    Median peak: {b.median():.0f}m  Mean: {b.mean():.1f}m')

        btm_distribution(mc_valid, 'All catalog moves with 1m data')

        # Great moves (mag_category or mfe_1m high)
        # Use mfe_1m >= 0.40 as proxy for tier A/S
        if 'mfe_1m' in mc_valid.columns:
            mc_tier_sa = mc_valid[mc_valid['mfe_1m'] >= 0.40]
            mc_tier_b  = mc_valid[mc_valid['mfe_1m'] < 0.40]
            print()
            btm_distribution(mc_tier_sa, 'Catalog Tier S/A proxy (mfe_1m >= 0.40 ATR)')
            print()
            btm_distribution(mc_tier_b,  'Catalog Tier B proxy (mfe_1m < 0.40 ATR)')

        # By signal type if available
        if 'sig_type' in mc_valid.columns:
            print()
            for stype in ['BRK', 'REV']:
                sub = mc_valid[mc_valid['sig_type'] == stype]
                if len(sub) > 10:
                    btm_distribution(sub, f'Catalog {stype} moves')
                    print()

        # By timing_category if available
        if 'timing_category' in mc_valid.columns:
            print()
            for cat in ['morning', 'midday', 'afternoon']:
                sub = mc_valid[mc_valid['timing_category'] == cat]
                if len(sub) > 10:
                    btm_distribution(sub, f'Catalog {cat}')
                    print()

    except Exception as e:
        print(f'  Move catalog load failed: {e}')

    # ── Step 7: Final Recommendation ─────────────────────────────────────
    print()
    print(DIVIDER)
    print('SECTION I — SUMMARY AND RECOMMENDATION')
    print(SUBDIV)

    # Find best rule overall
    best_rule_key  = max(rules, key=lambda k: rules[k]['net_atr'])
    best_rule      = rules[best_rule_key]
    baseline       = rules['hold_60m']
    gain_vs_60m    = best_rule['net_atr'] - baseline['net_atr']
    n_signals      = len(df)

    print(f'\n  Analysis based on {n_signals} winning signals (mfe_atr >= 0.10)')
    print()
    print(f'  Best exit rule:  {best_rule["label"]}')
    print(f'  Net ATR:         {best_rule["net_atr"]:+.2f}  (vs {baseline["net_atr"]:+.2f} at 60m hold)')
    print(f'  Gain vs 60m:     {gain_vs_60m:+.2f} ATR ({gain_vs_60m/n_signals*100:+.2f}% per signal)')
    print()

    # Additional insights
    pct_peaked_by_20m = (df['peak_minute'] <= 20).mean() * 100
    pct_peaked_by_30m = (df['peak_minute'] <= 30).mean() * 100
    avg_decay_all     = df['pnl_decay'].mean()

    print(f'  Key findings:')
    print(f'    {pct_peaked_by_20m:.1f}% of winners have peaked by 20m')
    print(f'    {pct_peaked_by_30m:.1f}% of winners have peaked by 30m')
    print(f'    Avg peak P&L: {df["pnl_at_peak"].mean():.3f} ATR')
    print(f'    Avg at 60m:   {df["pnl_at_60m"].mean():.3f} ATR')
    print(f'    Avg decay:    {avg_decay_all:.3f} ATR ({avg_decay_all/df["pnl_at_peak"].mean()*100:.1f}% of peak given back)')
    print()

    # Signal-type specific
    print('  Signal-type optimal exits (max net ATR among fixed exits):')
    for stype in sorted(df['sig_type'].unique()):
        sub = df[df['sig_type'] == stype]
        n   = len(sub)
        nets_fixed = {cp: sub[f'pnl_at_{cp}m'].sum() for cp in CHECKPOINTS}
        best_cp = max(nets_fixed, key=nets_fixed.get)
        pct_by_best = (sub['peak_minute'] <= best_cp).mean() * 100
        print(f'    {stype:<8} N={n:>3}  best_fixed_exit={best_cp}m  '
              f'net_ATR={nets_fixed[best_cp]:+.2f}  '
              f'{pct_by_best:.0f}% peaked by then')

    print()
    print(DIVIDER)

    # Restore stdout and save file
    sys.stdout = sys.stdout_real
    out_path.write_text(''.join(output_lines), encoding='utf-8')
    print(f'\nResults saved to: {out_path}')


if __name__ == '__main__':
    main()
