#!/usr/bin/env python3
"""
KLB v3.3c — NVDA Bull REV Deep-Dive
=====================================
Investigates whether NVDA bull REV is broken across ALL levels, or just VWAP.
NVDA accounts for -299 ATR of the -356 ATR total for bull VWAP REV (84%).

Questions:
  1. Is NVDA bull REV broken at ALL levels, or just VWAP?
  2. Is the -299 ATR from a few extreme losers (long tail) or consistent underperformance?
  3. Distribution: WIN/LOSS/FLAT counts, P&L percentiles
  4. Time-of-day: is NVDA bull REV worse at certain times?
  5. Verdict + recommended action
"""

import sys
import os
import glob
import numpy as np
import pandas as pd

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

V33C_GLOB = 'pine-logs-Key Level Breakout v3.3c_*.csv'

DIVIDER = '=' * 72
SUBDIV  = '-' * 72

# ── Reference benchmarks from MEMORY.md ───────────────────────────────────────
HIGHS_WIN_AVG   = 0.225
HIGHS_LOSS_AVG  = 0.997
HIGHS_ASYMMETRY = HIGHS_LOSS_AVG / HIGHS_WIN_AVG   # 4.4x
HIGHS_WIN_PCT   = 40.0


def pnl_distribution(sigs, label='', indent='  '):
    """Print P&L distribution stats for a set of signals."""
    pnls = [s.get('pnl_atr', 0) for s in sigs if s.get('pnl_atr') is not None]
    if not pnls:
        print(f"{indent}{label}: no P&L data")
        return

    arr = np.array(pnls)
    wins   = (arr > 0).sum()
    losses = (arr < 0).sum()
    flats  = (arr == 0).sum()

    print(f"{indent}{label} — N={len(arr)}")
    print(f"{indent}  WIN={wins} ({100*wins/len(arr):.1f}%)  "
          f"LOSS={losses} ({100*losses/len(arr):.1f}%)  "
          f"FLAT={flats} ({100*flats/len(arr):.1f}%)")
    print(f"{indent}  Min={arr.min():+.3f}  P25={np.percentile(arr,25):+.3f}  "
          f"Med={np.median(arr):+.3f}  P75={np.percentile(arr,75):+.3f}  "
          f"Max={arr.max():+.3f}")
    print(f"{indent}  Mean={arr.mean():+.4f}  Std={arr.std():.4f}  "
          f"Net={arr.sum():+.2f} ATR")


def print_block(label, sigs, indent='  ', ref_asymmetry=HIGHS_ASYMMETRY):
    """Print stats block for a signal set."""
    st = sig_stats(sigs, label)
    n = st['n']
    if n == 0:
        print(f"{indent}{label}: N=0")
        return st

    win_sigs  = [s for s in sigs if s.get('outcome') == 'WIN']
    loss_sigs = [s for s in sigs if s.get('outcome') == 'LOSS']
    win_avg_mfe  = np.mean([s.get('mfe_atr', 0) for s in win_sigs])  if win_sigs  else 0
    loss_avg_mae = np.mean([s.get('mae_atr', 0) for s in loss_sigs]) if loss_sigs else 0
    asymmetry = loss_avg_mae / win_avg_mfe if win_avg_mfe > 0 else float('inf')

    print(f"{indent}{label}")
    print(f"{indent}  N={n}  Win%={st['win_rate']:.1f}%  "
          f"AvgMFE={st['avg_mfe']:.4f}  AvgMAE={st['avg_mae']:.4f}  "
          f"NetATR={st['net_atr']:+.2f}")
    print(f"{indent}  Win avg MFE={win_avg_mfe:.3f}  Loss avg MAE={loss_avg_mae:.3f}  "
          f"Asymmetry={asymmetry:.2f}x")
    return st


def level_key(sig):
    """Collapse level string to main level type for grouping."""
    lvl = sig.get('levels', '') or ''
    # Extract primary level tokens
    parts = [p.strip() for p in lvl.replace(' + ', '|').split('|')]
    return parts[0] if parts else 'unknown'


def hour_bucket(sig):
    """Return hour-based time bucket string."""
    ts = sig.get('timestamp')
    if ts is None:
        return 'unknown'
    try:
        h = ts.hour
        if h < 10:
            return '09:30-09:59'
        elif h == 10:
            return '10:00-10:59'
        elif h == 11:
            return '11:00-11:59'
        elif h == 12:
            return '12:00-12:59'
        elif h == 13:
            return '13:00-13:59'
        elif h == 14:
            return '14:00-14:59'
        else:
            return '15:00-16:00'
    except Exception:
        return 'unknown'


def main():
    print(DIVIDER)
    print('KLB v3.3c — NVDA Bull REV Deep-Dive Analysis')
    print('Question: Is NVDA bull REV broken at ALL levels, or just VWAP?')
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
        matched = sum(1 for s in sym_sigs
                      if s.get('mfe_atr') is not None
                      and (s['mfe_atr'] != 0 or s['mae_atr'] != 0))
        print(f'  {sym}: {len(sym_sigs)} signals, {matched} with data')

    # Filter to signals with MFE/MAE data
    sigs = [s for s in all_signals if s.get('mfe_atr') is not None]
    print(f'\n  Signals with MFE/MAE data: {len(sigs)} / {len(all_signals)}')
    print()

    # ── 4. Segment: NVDA vs rest, bull vs bear, REV ──────────────────────────
    rev_sigs     = [s for s in sigs if 'REV' in s.get('sig_type', '')]
    brk_sigs     = [s for s in sigs if s.get('sig_type') == 'BRK']

    nvda_sigs    = [s for s in sigs     if s['symbol'] == 'NVDA']
    others_sigs  = [s for s in sigs     if s['symbol'] != 'NVDA']

    nvda_rev     = [s for s in rev_sigs if s['symbol'] == 'NVDA']
    others_rev   = [s for s in rev_sigs if s['symbol'] != 'NVDA']

    nvda_bull_rev   = [s for s in nvda_rev   if s['direction'] == 'bull']
    nvda_bear_rev   = [s for s in nvda_rev   if s['direction'] == 'bear']
    others_bull_rev = [s for s in others_rev if s['direction'] == 'bull']
    others_bear_rev = [s for s in others_rev if s['direction'] == 'bear']

    nvda_bull_brk   = [s for s in brk_sigs  if s['symbol'] == 'NVDA' and s['direction'] == 'bull']
    nvda_bear_brk   = [s for s in brk_sigs  if s['symbol'] == 'NVDA' and s['direction'] == 'bear']
    others_bull_brk = [s for s in brk_sigs  if s['symbol'] != 'NVDA' and s['direction'] == 'bull']

    # ── 5. Section A: NVDA vs others head-to-head ────────────────────────────
    print(DIVIDER)
    print('A. NVDA vs Others — Bull REV Head-to-Head')
    print(SUBDIV)

    print_block('NVDA bull REV (all levels)', nvda_bull_rev)
    print()
    print_block('Others bull REV (all levels)', others_bull_rev)
    print()
    print_block('NVDA bear REV (all levels — comparison)', nvda_bear_rev)
    print()
    print_block('Others bear REV (all levels — comparison)', others_bear_rev)
    print()

    # ── 6. Section B: NVDA bull REV by level type ────────────────────────────
    print(DIVIDER)
    print('B. NVDA Bull REV — Breakdown by Level Type')
    print(SUBDIV)

    # Group by primary level token
    level_groups = {}
    for s in nvda_bull_rev:
        lvl = level_key(s)
        level_groups.setdefault(lvl, []).append(s)

    # Sort by N desc
    sorted_levels = sorted(level_groups.items(), key=lambda x: -len(x[1]))

    hdr = f"  {'Level':<18} {'N':>4} {'Win%':>7} {'AvgMFE':>8} {'AvgMAE':>8} {'NetATR':>9} {'Asymm':>7}"
    print(hdr)
    print('  ' + '-' * 62)

    for lvl, lsigs in sorted_levels:
        st = sig_stats(lsigs)
        wins  = [s for s in lsigs if s.get('outcome') == 'WIN']
        losses= [s for s in lsigs if s.get('outcome') == 'LOSS']
        win_mfe  = np.mean([s.get('mfe_atr', 0) for s in wins])  if wins  else 0
        loss_mae = np.mean([s.get('mae_atr', 0) for s in losses]) if losses else 0
        asym = loss_mae / win_mfe if win_mfe > 0 else float('inf')
        asym_str = f'{asym:.1f}x' if asym != float('inf') else 'inf'
        print(f"  {lvl:<18} {st['n']:>4} {st['win_rate']:>6.1f}% "
              f"{st['avg_mfe']:>8.4f} {st['avg_mae']:>8.4f} "
              f"{st['net_atr']:>+9.2f} {asym_str:>7}")

    print()

    # ── 7. Section C: NVDA bear REV by level type (comparison) ───────────────
    print(DIVIDER)
    print('C. NVDA Bear REV — Breakdown by Level Type (for comparison)')
    print(SUBDIV)

    bear_level_groups = {}
    for s in nvda_bear_rev:
        lvl = level_key(s)
        bear_level_groups.setdefault(lvl, []).append(s)

    sorted_bear = sorted(bear_level_groups.items(), key=lambda x: -len(x[1]))

    print(hdr)
    print('  ' + '-' * 62)

    for lvl, lsigs in sorted_bear:
        st = sig_stats(lsigs)
        wins  = [s for s in lsigs if s.get('outcome') == 'WIN']
        losses= [s for s in lsigs if s.get('outcome') == 'LOSS']
        win_mfe  = np.mean([s.get('mfe_atr', 0) for s in wins])  if wins  else 0
        loss_mae = np.mean([s.get('mae_atr', 0) for s in losses]) if losses else 0
        asym = loss_mae / win_mfe if win_mfe > 0 else float('inf')
        asym_str = f'{asym:.1f}x' if asym != float('inf') else 'inf'
        print(f"  {lvl:<18} {st['n']:>4} {st['win_rate']:>6.1f}% "
              f"{st['avg_mfe']:>8.4f} {st['avg_mae']:>8.4f} "
              f"{st['net_atr']:>+9.2f} {asym_str:>7}")

    print()

    # ── 8. Section D: NVDA BRK baseline ──────────────────────────────────────
    print(DIVIDER)
    print('D. NVDA BRK Baseline (does BRK work on NVDA?)')
    print(SUBDIV)

    print_block('NVDA bull BRK', nvda_bull_brk)
    print()
    print_block('NVDA bear BRK', nvda_bear_brk)
    print()
    print_block('Others bull BRK (reference)', others_bull_brk)
    print()

    # ── 9. Section E: Time-of-day for NVDA bull REV ──────────────────────────
    print(DIVIDER)
    print('E. NVDA Bull REV — Time of Day Breakdown')
    print(SUBDIV)

    tod_groups = {}
    for s in nvda_bull_rev:
        bucket = hour_bucket(s)
        tod_groups.setdefault(bucket, []).append(s)

    buckets_sorted = sorted(tod_groups.keys())

    hdr2 = f"  {'Time':<14} {'N':>4} {'Win%':>7} {'NetATR':>9}"
    print(hdr2)
    print('  ' + '-' * 36)

    for bucket in buckets_sorted:
        lsigs = tod_groups[bucket]
        st = sig_stats(lsigs)
        print(f"  {bucket:<14} {st['n']:>4} {st['win_rate']:>6.1f}% {st['net_atr']:>+9.2f}")

    print()

    # ── 10. Section F: VWAP vs non-VWAP split within NVDA bull REV ──────────
    print(DIVIDER)
    print('F. NVDA Bull REV — VWAP vs Non-VWAP')
    print(SUBDIV)

    nvda_bull_rev_vwap    = [s for s in nvda_bull_rev if 'VWAP' in (s.get('levels') or '')]
    nvda_bull_rev_novwap  = [s for s in nvda_bull_rev if 'VWAP' not in (s.get('levels') or '')]

    print_block('NVDA bull REV at VWAP', nvda_bull_rev_vwap)
    print()
    print_block('NVDA bull REV NOT at VWAP', nvda_bull_rev_novwap)
    print()

    # ── 11. Section G: P&L distribution (long-tail vs consistent?) ───────────
    print(DIVIDER)
    print('G. P&L Distribution — Long Tail vs Consistent Underperformance?')
    print(SUBDIV)

    pnl_distribution(nvda_bull_rev,          'NVDA bull REV (all levels)')
    print()
    pnl_distribution(nvda_bull_rev_vwap,     'NVDA bull REV VWAP only')
    print()
    pnl_distribution(nvda_bull_rev_novwap,   'NVDA bull REV non-VWAP')
    print()
    pnl_distribution(others_bull_rev,        'Others bull REV (reference)')
    print()

    # Extreme losers for NVDA bull REV
    nvda_pnls = [(s.get('pnl_atr', 0), s.get('levels', ''), hour_bucket(s),
                  s.get('timestamp', ''))
                 for s in nvda_bull_rev if s.get('pnl_atr') is not None]
    nvda_pnls.sort(key=lambda x: x[0])
    print(f'  Top 10 worst NVDA bull REV losses:')
    for pnl, lvl, tod, ts in nvda_pnls[:10]:
        print(f'    {pnl:+.3f} ATR  [{tod}]  {lvl}  ({ts})')

    print()
    print(f'  Top 10 best NVDA bull REV wins:')
    for pnl, lvl, tod, ts in reversed(nvda_pnls[-10:]):
        print(f'    {pnl:+.3f} ATR  [{tod}]  {lvl}  ({ts})')

    print()

    # ── 12. VERDICT ───────────────────────────────────────────────────────────
    print(DIVIDER)
    print('H. VERDICT')
    print(SUBDIV)

    # Gather stats for verdict logic
    st_nvda_bull_rev     = sig_stats(nvda_bull_rev)
    st_others_bull_rev   = sig_stats(others_bull_rev)
    st_nvda_bull_brk     = sig_stats(nvda_bull_brk)

    nvda_wins  = [s for s in nvda_bull_rev if s.get('outcome') == 'WIN']
    nvda_losses= [s for s in nvda_bull_rev if s.get('outcome') == 'LOSS']
    nvda_win_mfe  = np.mean([s.get('mfe_atr', 0) for s in nvda_wins])  if nvda_wins  else 0
    nvda_loss_mae = np.mean([s.get('mae_atr', 0) for s in nvda_losses]) if nvda_losses else 0
    nvda_asym  = nvda_loss_mae / nvda_win_mfe if nvda_win_mfe > 0 else float('inf')

    nov_wins  = [s for s in nvda_bull_rev_novwap if s.get('outcome') == 'WIN']
    nov_losses= [s for s in nvda_bull_rev_novwap if s.get('outcome') == 'LOSS']
    nov_win_mfe  = np.mean([s.get('mfe_atr', 0) for s in nov_wins])  if nov_wins  else 0
    nov_loss_mae = np.mean([s.get('mae_atr', 0) for s in nov_losses]) if nov_losses else 0
    nov_asym  = nov_loss_mae / nov_win_mfe if nov_win_mfe > 0 else float('inf')

    print(f'  Summary:')
    print(f'    NVDA bull REV (all):      N={st_nvda_bull_rev["n"]}  '
          f'Win%={st_nvda_bull_rev["win_rate"]:.1f}%  '
          f'Net={st_nvda_bull_rev["net_atr"]:+.2f} ATR  '
          f'Asymm={nvda_asym:.2f}x')
    print(f'    NVDA bull REV (VWAP):     N={sig_stats(nvda_bull_rev_vwap)["n"]}  '
          f'Win%={sig_stats(nvda_bull_rev_vwap)["win_rate"]:.1f}%  '
          f'Net={sig_stats(nvda_bull_rev_vwap)["net_atr"]:+.2f} ATR')
    print(f'    NVDA bull REV (non-VWAP): N={sig_stats(nvda_bull_rev_novwap)["n"]}  '
          f'Win%={sig_stats(nvda_bull_rev_novwap)["win_rate"]:.1f}%  '
          f'Net={sig_stats(nvda_bull_rev_novwap)["net_atr"]:+.2f} ATR  '
          f'Asymm={nov_asym:.2f}x')
    print(f'    Others bull REV:           N={st_others_bull_rev["n"]}  '
          f'Win%={st_others_bull_rev["win_rate"]:.1f}%  '
          f'Net={st_others_bull_rev["net_atr"]:+.2f} ATR')
    print(f'    NVDA bull BRK (baseline): N={st_nvda_bull_brk["n"]}  '
          f'Win%={st_nvda_bull_brk["win_rate"]:.1f}%  '
          f'Net={st_nvda_bull_brk["net_atr"]:+.2f} ATR')
    print()

    # Check if VWAP is the main driver vs all levels broken
    vwap_net    = sig_stats(nvda_bull_rev_vwap)['net_atr']
    novwap_net  = sig_stats(nvda_bull_rev_novwap)['net_atr']
    vwap_n      = sig_stats(nvda_bull_rev_vwap)['n']
    novwap_n    = sig_stats(nvda_bull_rev_novwap)['n']
    total_net   = st_nvda_bull_rev['net_atr']

    # Tail check: are >50% of losses from bottom 10%?
    all_pnls = sorted([s.get('pnl_atr', 0) for s in nvda_bull_rev if s.get('pnl_atr') is not None])
    if all_pnls:
        tail_cutoff = int(len(all_pnls) * 0.10)
        tail_sum = sum(all_pnls[:tail_cutoff]) if tail_cutoff > 0 else 0
        total_loss_sum = sum(p for p in all_pnls if p < 0)
        tail_pct = (tail_sum / total_loss_sum * 100) if total_loss_sum < 0 else 0
    else:
        tail_pct = 0

    print(f'  Analysis:')
    print(f'    Bottom 10% of signals account for {abs(tail_pct):.1f}% of total losses')
    if abs(tail_pct) > 50:
        print(f'    → LONG TAIL pattern: extreme losers drive the P&L')
    else:
        print(f'    → CONSISTENT pattern: losses spread across many signals')

    if vwap_n > 0 and novwap_n > 0:
        vwap_share = abs(vwap_net) / (abs(vwap_net) + abs(novwap_net) + 0.001) * 100 if total_net < 0 else 0
        print(f'    VWAP share of total drag: {vwap_share:.0f}% '
              f'(VWAP={vwap_net:+.1f} non-VWAP={novwap_net:+.1f})')

    print()
    print(f'  Recommendation:')

    # Decision tree
    n_total = st_nvda_bull_rev['n']
    win_pct = st_nvda_bull_rev['win_rate']
    net     = st_nvda_bull_rev['net_atr']
    asym    = nvda_asym

    # Case 1: VWAP is the main culprit, non-VWAP is OK
    if vwap_n >= 5 and novwap_n >= 5:
        if novwap_net > -5 and vwap_net < -20:
            print(f'    (a) SUPPRESS NVDA bull REV only at VWAP')
            print(f'        VWAP is clearly the culprit: {vwap_net:+.2f} ATR')
            print(f'        Non-VWAP is acceptable: {novwap_net:+.2f} ATR')
        elif novwap_net < -20 and vwap_net < -20:
            print(f'    (b) SUPPRESS NVDA bull REV ENTIRELY')
            print(f'        Both VWAP ({vwap_net:+.2f}) and non-VWAP ({novwap_net:+.2f}) are negative')
            print(f'        Win%={win_pct:.1f}%  Asymmetry={asym:.2f}x')
        elif net < -10 and asym >= 3.0:
            print(f'    (c) POSITION-SIZE NVDA bull REV smaller')
            print(f'        Net={net:+.2f} ATR with {asym:.2f}x asymmetry — reduce size')
            print(f'        Not enough N to justify full suppression')
        else:
            print(f'    (d) NO CHANGE — monitor with more data')
            print(f'        Net={net:+.2f} ATR, N={n_total} — marginal or insufficient data')
    elif n_total < 10:
        print(f'    (d) NO CHANGE — N={n_total} too small for confident action')
    elif net < -30 and asym >= 3.0:
        print(f'    (b) SUPPRESS NVDA bull REV ENTIRELY')
        print(f'        Net={net:+.2f} ATR, Asymmetry={asym:.2f}x, Win%={win_pct:.1f}%')
    else:
        print(f'    (d) NO CHANGE — Net={net:+.2f} ATR, Win%={win_pct:.1f}%')
        print(f'        Asymmetry={asym:.2f}x — borderline, monitor')

    print()
    print(f'  Reference: v3.3c HIGHs suppression threshold was:')
    print(f'    Net ~ -1212 ATR  Win% ~40%  Asymmetry {HIGHS_ASYMMETRY:.1f}x')
    print()
    print(DIVIDER)


if __name__ == '__main__':
    main()
