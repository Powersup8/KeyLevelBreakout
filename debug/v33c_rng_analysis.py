#!/usr/bin/env python3
"""
KLB v3.3c — RNG Signal MFE/MAE Analysis
==========================================
RNG signals log no OHLC data (just time + direction + vol).
This script looks up the IB 1m bar at the signal timestamp to get
the entry price, then runs the standard MFE/MAE measurement.

Answers: Is the RNG signal type useful?
"""

import sys
import os
import glob

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

from v33_backtest import (
    parse_pine_log,
    identify_symbol,
    load_1m,
    load_daily,
    compute_atr,
    measure_mfe_mae,
    sig_stats,
    SYMBOLS,
    BAR_DIR,
    LOG_DIR,
)

import numpy as np
import pandas as pd

# ── Config ────────────────────────────────────────────────────────────────────
V33C_GLOB = 'pine-logs-Key Level Breakout v3.3c_*.csv'
MAX_LOOKUP_MINUTES = 5   # max gap allowed when matching signal ts to 1m bar

DIVIDER = '=' * 72
SUBDIV  = '-' * 72


def fill_rng_entry(rng_sigs, bars_1m, atr_series):
    """Look up IB 1m bar close for each RNG signal to populate entry price.

    RNG signals have no OHLC in the log. We find the nearest 1m bar within
    MAX_LOOKUP_MINUTES and use its close as the entry price.

    Mutates signals in place, setting 'close' and 'atr'.
    """
    for sig in rng_sigs:
        ts = sig['timestamp']

        # Normalise to US/Eastern
        if ts.tzinfo is None:
            ts_et = pd.Timestamp(ts, tz='US/Eastern')
        else:
            ts_et = ts.tz_convert('US/Eastern')

        sig_date = ts_et.date()

        # Look up ATR for that date
        if sig_date in atr_series.index:
            sig['atr'] = float(atr_series[sig_date])

        # Find closest 1m bar within MAX_LOOKUP_MINUTES
        window_start = ts_et - pd.Timedelta(minutes=MAX_LOOKUP_MINUTES)
        window_end   = ts_et + pd.Timedelta(minutes=MAX_LOOKUP_MINUTES)
        mask = (bars_1m.index >= window_start) & (bars_1m.index <= window_end)
        nearby = bars_1m[mask]

        if len(nearby) == 0:
            continue  # no bar found — leave close=None so measure_mfe_mae skips it

        # Pick the closest bar by timestamp
        diffs = pd.Series(
            (nearby.index - ts_et).total_seconds(),
            index=nearby.index
        ).abs()
        closest_idx = diffs.idxmin()
        bar = nearby.loc[closest_idx]
        sig['close'] = float(bar['close'])


def print_block(label, sigs, indent='  '):
    """Print stats block for a signal set."""
    st = sig_stats(sigs, label)
    n = st['n']
    if n == 0:
        print(f"{indent}{label}: N=0")
        return st
    print(f"{indent}{label}")
    print(f"{indent}  N={n}  Win%={st['win_rate']:.1f}%  "
          f"AvgMFE={st['avg_mfe']:.4f}  AvgMAE={st['avg_mae']:.4f}  "
          f"AvgP&L={st['avg_pnl']:.4f}  NetATR={st['net_atr']:+.2f}")
    return st


def time_of_day(sig):
    """Classify signal time into morning/midday/afternoon."""
    time_str = sig.get('time_str', '')
    try:
        parts = time_str.split(':')
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
    except Exception:
        # Fallback: parse from timestamp
        ts = sig['timestamp']
        hour = ts.hour
        minute = ts.minute

    total_min = hour * 60 + minute
    if total_min < 11 * 60:
        return 'morning (9:30-11)'
    elif total_min < 14 * 60:
        return 'midday (11-14)'
    else:
        return 'afternoon (14-16)'


def main():
    print(DIVIDER)
    print('KLB v3.3c — RNG Signal MFE/MAE Analysis')
    print('Entry price derived from IB 1m bar at signal timestamp.')
    print(DIVIDER)
    print()

    # ── 1. Parse v3.3c logs ──────────────────────────────────────────────────
    files = sorted(glob.glob(str(LOG_DIR / V33C_GLOB)))
    print(f'Step 1: Parsing v3.3c logs ({len(files)} files)...')

    all_signals = []
    for fp in files:
        short = os.path.basename(fp).split('_')[-1].replace('.csv', '')
        signals = parse_pine_log(fp)
        if not signals:
            print(f'  {short}: 0 signals (empty)')
            continue
        symbol = identify_symbol(signals)
        if symbol is None:
            print(f'  {short}: could not identify symbol')
            continue
        for s in signals:
            s['symbol'] = symbol
            s['version'] = 'v3.3c'
        all_signals.extend(signals)

    rng_all = [s for s in all_signals if s.get('sig_type') == 'RNG']
    print(f'  Total signals: {len(all_signals)}')
    print(f'  RNG signals:   {len(rng_all)}')
    print()

    # ── 2. Load IB 1m data ───────────────────────────────────────────────────
    symbols_seen = sorted(set(s['symbol'] for s in all_signals))
    print(f'Step 2: Loading IB 1m data for {symbols_seen}...')

    ib_cache = {}
    for sym in symbols_seen:
        try:
            bars_1m    = load_1m(sym)
            daily_df   = load_daily(sym)
            atr_series = compute_atr(daily_df)
            ib_cache[sym] = (bars_1m, atr_series)
            print(f'  {sym}: {len(bars_1m)} bars')
        except Exception as exc:
            print(f'  {sym}: ERROR — {exc}')

    print()

    # ── 3. Fill entry prices for RNG signals ─────────────────────────────────
    print('Step 3: Filling RNG entry prices from IB 1m bars...')
    filled = 0
    skipped = 0
    for sym in symbols_seen:
        if sym not in ib_cache:
            continue
        bars_1m, atr_series = ib_cache[sym]
        sym_rng = [s for s in rng_all if s['symbol'] == sym]
        fill_rng_entry(sym_rng, bars_1m, atr_series)
        sym_filled  = sum(1 for s in sym_rng if s.get('close') is not None)
        sym_skipped = len(sym_rng) - sym_filled
        print(f'  {sym}: {len(sym_rng)} RNG signals, {sym_filled} filled, {sym_skipped} skipped')
        filled  += sym_filled
        skipped += sym_skipped

    print(f'  Total filled: {filled}, skipped (no IB bar): {skipped}')
    print()

    # ── 4. Measure MFE/MAE for RNG signals ───────────────────────────────────
    print('Step 4: Measuring MFE/MAE for RNG signals...')
    for sym in symbols_seen:
        if sym not in ib_cache:
            continue
        bars_1m, atr_series = ib_cache[sym]
        sym_rng = [s for s in rng_all if s['symbol'] == sym]
        measure_mfe_mae(sym_rng, bars_1m, atr_series)

    # Filter to signals with actual MFE/MAE data (non-FLAT from missing entry)
    rng_sigs = [s for s in rng_all
                if s.get('mfe_atr') is not None
                and (s.get('close') is not None)]

    # Additionally exclude those that got FLAT purely due to missing entry
    # (close was None → measure_mfe_mae sets outcome=FLAT, mfe_atr=0)
    # We include all that had close filled, even if truly flat
    print(f'  RNG signals with entry filled: {len(rng_sigs)} / {len(rng_all)}')
    print()

    if not rng_sigs:
        print('ERROR: No RNG signals with data. Check log files and IB data.')
        return

    # ── 5. Print analysis ────────────────────────────────────────────────────
    print(DIVIDER)
    print('A. OVERALL RNG STATS')
    print(SUBDIV)

    st_all = print_block('All RNG',  rng_sigs)
    st_bull = print_block('Bull RNG', [s for s in rng_sigs if s['direction'] == 'bull'])
    st_bear = print_block('Bear RNG', [s for s in rng_sigs if s['direction'] == 'bear'])

    # ── 6. Time-of-day breakdown ─────────────────────────────────────────────
    print()
    print(DIVIDER)
    print('B. TIME-OF-DAY BREAKDOWN')
    print(SUBDIV)

    tod_buckets = ['morning (9:30-11)', 'midday (11-14)', 'afternoon (14-16)']
    hdr = f"  {'Bucket':<25} {'N':>5} {'Win%':>7} {'AvgMFE':>8} {'AvgMAE':>8} {'NetATR':>9}"
    print(hdr)
    print('  ' + '-' * (len(hdr) - 2))

    for bucket in tod_buckets:
        bucket_sigs = [s for s in rng_sigs if time_of_day(s) == bucket]
        if not bucket_sigs:
            print(f"  {bucket:<25} N=0")
            continue
        st = sig_stats(bucket_sigs)
        print(f"  {bucket:<25} {st['n']:>5} {st['win_rate']:>6.1f}% "
              f"{st['avg_mfe']:>8.4f} {st['avg_mae']:>8.4f} {st['net_atr']:>+9.2f}")

    # Also bull/bear split per bucket
    print()
    print('  Bull/Bear split by time of day:')
    hdr2 = f"  {'Bucket':<25} {'Bull N':>7} {'Bull Win%':>10} {'Bull Net':>9} {'Bear N':>7} {'Bear Win%':>10} {'Bear Net':>9}"
    print(hdr2)
    print('  ' + '-' * (len(hdr2) - 2))
    for bucket in tod_buckets:
        bsigs = [s for s in rng_sigs if time_of_day(s) == bucket and s['direction'] == 'bull']
        rsigs = [s for s in rng_sigs if time_of_day(s) == bucket and s['direction'] == 'bear']
        st_b = sig_stats(bsigs)
        st_r = sig_stats(rsigs)
        print(f"  {bucket:<25} "
              f"{st_b['n']:>7} {st_b['win_rate']:>9.1f}% {st_b['net_atr']:>+9.2f} "
              f"{st_r['n']:>7} {st_r['win_rate']:>9.1f}% {st_r['net_atr']:>+9.2f}")

    # ── 7. Per-symbol breakdown ───────────────────────────────────────────────
    print()
    print(DIVIDER)
    print('C. PER-SYMBOL BREAKDOWN')
    print(SUBDIV)

    hdr3 = f"  {'Symbol':<6} {'N':>5} {'Win%':>7} {'AvgMFE':>8} {'AvgMAE':>8} {'NetATR':>9} {'Bull N':>7} {'Bull Net':>9} {'Bear N':>7} {'Bear Net':>9}"
    print(hdr3)
    print('  ' + '-' * (len(hdr3) - 2))

    for sym in SYMBOLS:
        ssigs = [s for s in rng_sigs if s['symbol'] == sym]
        if not ssigs:
            continue
        st = sig_stats(ssigs)
        bsigs = [s for s in ssigs if s['direction'] == 'bull']
        rsigs = [s for s in ssigs if s['direction'] == 'bear']
        st_b = sig_stats(bsigs)
        st_r = sig_stats(rsigs)
        print(f"  {sym:<6} {st['n']:>5} {st['win_rate']:>6.1f}% "
              f"{st['avg_mfe']:>8.4f} {st['avg_mae']:>8.4f} {st['net_atr']:>+9.2f} "
              f"{st_b['n']:>7} {st_b['net_atr']:>+9.2f} "
              f"{st_r['n']:>7} {st_r['net_atr']:>+9.2f}")

    # ── 8. Verdict ───────────────────────────────────────────────────────────
    print()
    print(DIVIDER)
    print('D. VERDICT — Is RNG Useful?')
    print(SUBDIV)

    n_total  = st_all['n']
    win_rate = st_all['win_rate']
    net_atr  = st_all['net_atr']
    avg_pnl  = st_all['avg_pnl']

    print(f'  Overall: N={n_total}  Win%={win_rate:.1f}%  Net={net_atr:+.2f} ATR  '
          f'Avg P&L/sig={avg_pnl:+.4f} ATR')
    print()

    if n_total < 20:
        verdict = 'INSUFFICIENT DATA — too few signals for confident verdict'
    elif net_atr > 0 and win_rate >= 50:
        verdict = 'USEFUL — positive net ATR and win rate >= 50%'
    elif net_atr > 0 and win_rate < 50:
        verdict = 'MARGINAL — positive net ATR but sub-50% win rate (check MAE/MFE ratio)'
    elif net_atr < -10:
        verdict = 'DRAG — negative net ATR, consider suppressing or redesigning RNG'
    else:
        verdict = 'NEUTRAL — near-zero edge, RNG signals are noise (flat expected value)'

    print(f'  Verdict: {verdict}')
    print()

    # Context vs other signal types
    print('  Context: Non-RNG signal types have OHLC and direct MFE/MAE from Pine.')
    print('  RNG entry prices are IB 1m bar closes — may be 1-5 min after signal.')
    print('  This adds noise but should be directionally correct.')
    print()
    print(DIVIDER)


if __name__ == '__main__':
    main()
