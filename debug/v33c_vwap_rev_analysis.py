#!/usr/bin/env python3
"""
KLB v3.3c — Bull VWAP REV Analysis
====================================
Investigates whether bull REV signals at VWAP are structurally broken,
similar to the bull REV at HIGH levels finding that drove v3.3c.

Uses v3.3c actual Pine logs (bull REV at HIGHs already suppressed there).
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

DIVIDER = '=' * 72
SUBDIV  = '-' * 72

# v3.3c HIGHs benchmark (from MEMORY.md): wins avg +0.225, losses avg -0.997 (4.4x asymmetry)
HIGHS_WIN_AVG  = 0.225
HIGHS_LOSS_AVG = 0.997
HIGHS_ASYMMETRY = HIGHS_LOSS_AVG / HIGHS_WIN_AVG  # 4.4x


def is_vwap_rev(sig):
    """True if signal is a REV/EXREV type with VWAP in levels."""
    sig_type = sig.get('sig_type', '')
    if 'REV' not in sig_type:
        return False
    return 'VWAP' in sig.get('levels', '')


def print_block(label, sigs, indent='  '):
    """Print stats block for a signal set."""
    st = sig_stats(sigs, label)
    n = st['n']
    if n == 0:
        print(f"{indent}{label}: N=0")
        return st

    wins   = sum(1 for s in sigs if s.get('outcome') == 'WIN')
    losses = sum(1 for s in sigs if s.get('outcome') == 'LOSS')

    # Win/loss avg MFE and MAE for asymmetry calc
    win_sigs  = [s for s in sigs if s.get('outcome') == 'WIN']
    loss_sigs = [s for s in sigs if s.get('outcome') == 'LOSS']
    win_avg_mfe  = np.mean([s.get('mfe_atr', 0) for s in win_sigs])  if win_sigs  else 0
    loss_avg_mae = np.mean([s.get('mae_atr', 0) for s in loss_sigs]) if loss_sigs else 0
    asymmetry = loss_avg_mae / win_avg_mfe if win_avg_mfe > 0 else float('inf')

    print(f"{indent}{label}")
    print(f"{indent}  N={n}  Win%={st['win_rate']:.1f}%  "
          f"AvgMFE={st['avg_mfe']:.4f}  AvgMAE={st['avg_mae']:.4f}  "
          f"AvgP&L={st['avg_pnl']:.4f}  NetATR={st['net_atr']:+.2f}")
    print(f"{indent}  Win avg MFE={win_avg_mfe:.3f}  Loss avg MAE={loss_avg_mae:.3f}  "
          f"Asymmetry={asymmetry:.2f}x  "
          f"(Highs benchmark: {HIGHS_ASYMMETRY:.1f}x)")
    return st


def main():
    print(DIVIDER)
    print('KLB v3.3c — Bull VWAP REV Analysis')
    print('Question: Is bull REV at VWAP structurally broken like bull REV at HIGHs?')
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
        print(f'  {short}: {symbol} — {len(signals)} signals')

    print(f'  Total signals: {len(all_signals)}')
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

    # ── 3. Measure MFE/MAE ───────────────────────────────────────────────────
    print('Step 3: Measuring MFE/MAE...')
    for sym in symbols_seen:
        if sym not in ib_cache:
            continue
        bars_1m, atr_series = ib_cache[sym]
        sym_sigs = [s for s in all_signals if s['symbol'] == sym]
        measure_mfe_mae(sym_sigs, bars_1m, atr_series)
        matched = sum(1 for s in sym_sigs if s.get('mfe_atr') is not None
                      and (s['mfe_atr'] != 0 or s['mae_atr'] != 0))
        print(f'  {sym}: {len(sym_sigs)} signals, {matched} with data')

    # Filter to signals with MFE/MAE data
    sigs = [s for s in all_signals if s.get('mfe_atr') is not None]
    print(f'\n  Signals with MFE/MAE data: {len(sigs)} / {len(all_signals)}')
    print()

    # ── 4. Segment signals ───────────────────────────────────────────────────
    rev_sigs = [s for s in sigs if 'REV' in s.get('sig_type', '')]

    bull_vwap_rev  = [s for s in rev_sigs if s['direction'] == 'bull' and is_vwap_rev(s)]
    bear_vwap_rev  = [s for s in rev_sigs if s['direction'] == 'bear' and is_vwap_rev(s)]
    bull_novwap_rev = [s for s in rev_sigs if s['direction'] == 'bull' and not is_vwap_rev(s)]
    bear_novwap_rev = [s for s in rev_sigs if s['direction'] == 'bear' and not is_vwap_rev(s)]

    # ── 5. Print analysis ────────────────────────────────────────────────────
    print(DIVIDER)
    print('A. VWAP REV vs Baseline REV')
    print(SUBDIV)

    st_bvwap  = print_block('Bull VWAP REV',      bull_vwap_rev)
    st_brvwap = print_block('Bear VWAP REV',      bear_vwap_rev)
    st_bnov   = print_block('Bull non-VWAP REV (baseline)', bull_novwap_rev)
    st_brnov  = print_block('Bear non-VWAP REV (baseline)', bear_novwap_rev)

    # ── 6. Level combo breakdown ─────────────────────────────────────────────
    print()
    print(DIVIDER)
    print('B. Level Combo Breakdown for VWAP REV signals')
    print(SUBDIV)

    # Collect unique level combos containing VWAP among REV signals
    level_counts = {}
    for s in rev_sigs:
        if 'VWAP' in s.get('levels', ''):
            lvl = s.get('levels', 'unknown')
            level_counts[lvl] = level_counts.get(lvl, 0) + 1

    sorted_levels = sorted(level_counts.items(), key=lambda x: -x[1])
    print(f'  Found {len(sorted_levels)} unique VWAP-containing level combos:\n')

    hdr = f"  {'Level Combo':<30} {'N':>4} {'Bull N':>7} {'Bull Win%':>10} {'Bull Net':>10} {'Bear N':>7} {'Bear Win%':>10} {'Bear Net':>10}"
    print(hdr)
    print('  ' + '-' * (len(hdr) - 2))

    for lvl, _ in sorted_levels[:20]:  # top 20 combos
        bsigs = [s for s in rev_sigs if s.get('levels') == lvl and s['direction'] == 'bull']
        rsigs = [s for s in rev_sigs if s.get('levels') == lvl and s['direction'] == 'bear']
        st_b  = sig_stats(bsigs)
        st_r  = sig_stats(rsigs)
        total = st_b['n'] + st_r['n']
        lvl_display = (lvl[:28] + '..') if len(lvl) > 30 else lvl
        print(f"  {lvl_display:<30} {total:>4} "
              f"{st_b['n']:>7} {st_b['win_rate']:>9.1f}% {st_b['net_atr']:>+10.2f} "
              f"{st_r['n']:>7} {st_r['win_rate']:>9.1f}% {st_r['net_atr']:>+10.2f}")

    # ── 7. Per-symbol breakdown for VWAP REV ────────────────────────────────
    print()
    print(DIVIDER)
    print('C. Per-Symbol Breakdown for VWAP REV')
    print(SUBDIV)

    hdr2 = f"  {'Symbol':<6} {'Bull N':>7} {'Bull Win%':>10} {'Bull Net':>10} {'Bear N':>7} {'Bear Win%':>10} {'Bear Net':>10}"
    print(hdr2)
    print('  ' + '-' * (len(hdr2) - 2))

    for sym in SYMBOLS:
        bsigs = [s for s in bull_vwap_rev  if s['symbol'] == sym]
        rsigs = [s for s in bear_vwap_rev  if s['symbol'] == sym]
        if not bsigs and not rsigs:
            continue
        st_b = sig_stats(bsigs)
        st_r = sig_stats(rsigs)
        print(f"  {sym:<6} "
              f"{st_b['n']:>7} {st_b['win_rate']:>9.1f}% {st_b['net_atr']:>+10.2f} "
              f"{st_r['n']:>7} {st_r['win_rate']:>9.1f}% {st_r['net_atr']:>+10.2f}")

    # ── 8. Verdict ───────────────────────────────────────────────────────────
    print()
    print(DIVIDER)
    print('D. VERDICT')
    print(SUBDIV)

    n_bull = st_bvwap['n']
    n_bear = st_brvwap['n']
    bull_win  = st_bvwap['win_rate']
    bull_net  = st_bvwap['net_atr']
    bear_win  = st_brvwap['win_rate']
    bear_net  = st_brvwap['net_atr']
    bull_baseline_net = st_bnov['net_atr']
    bear_baseline_net = st_brnov['net_atr']

    # Asymmetry for bull VWAP REV
    bvwap_wins  = [s for s in bull_vwap_rev if s.get('outcome') == 'WIN']
    bvwap_losses = [s for s in bull_vwap_rev if s.get('outcome') == 'LOSS']
    bull_win_avg_mfe  = np.mean([s.get('mfe_atr', 0) for s in bvwap_wins])  if bvwap_wins  else 0
    bull_loss_avg_mae = np.mean([s.get('mae_atr', 0) for s in bvwap_losses]) if bvwap_losses else 0
    bull_asymmetry = bull_loss_avg_mae / bull_win_avg_mfe if bull_win_avg_mfe > 0 else float('inf')

    print(f'  Bull VWAP REV:  N={n_bull}  Win%={bull_win:.1f}%  Net={bull_net:+.2f} ATR')
    print(f'    Win avg MFE={bull_win_avg_mfe:.3f}  Loss avg MAE={bull_loss_avg_mae:.3f}  '
          f'Asymmetry={bull_asymmetry:.2f}x')
    print(f'    Bull non-VWAP REV baseline: Net={bull_baseline_net:+.2f} ATR')
    print()
    print(f'  Bear VWAP REV:  N={n_bear}  Win%={bear_win:.1f}%  Net={bear_net:+.2f} ATR')
    print(f'    Bear non-VWAP REV baseline: Net={bear_baseline_net:+.2f} ATR')
    print()

    # Decision logic
    print('  Benchmark comparison (v3.3c HIGHs suppression threshold):')
    print(f'    HIGHs: Win avg +{HIGHS_WIN_AVG:.3f} ATR  Loss avg -{HIGHS_LOSS_AVG:.3f} ATR  '
          f'Asymmetry {HIGHS_ASYMMETRY:.1f}x  Win% ~40%  Net ~-1212 ATR')
    print()

    suppress_recommended = (
        n_bull >= 10 and
        bull_win < 48 and
        bull_net < -20 and
        bull_asymmetry >= 2.5
    )

    if suppress_recommended:
        print('  RECOMMENDATION: SUPPRESS bull VWAP REV')
        print(f'    Rationale: Net={bull_net:+.2f} ATR, Win%={bull_win:.1f}%, '
              f'asymmetry={bull_asymmetry:.2f}x >= 2.5x threshold')
    elif n_bull < 10:
        print(f'  RECOMMENDATION: MONITOR (N={n_bull} too small for confident action)')
    elif bull_net < 0:
        print(f'  RECOMMENDATION: WATCH — negative edge (Net={bull_net:+.2f}) but '
              f'asymmetry={bull_asymmetry:.2f}x < 2.5x threshold')
    else:
        print(f'  RECOMMENDATION: KEEP bull VWAP REV — Net={bull_net:+.2f} ATR, '
              f'Win%={bull_win:.1f}%')

    print()
    print(DIVIDER)


if __name__ == '__main__':
    main()
