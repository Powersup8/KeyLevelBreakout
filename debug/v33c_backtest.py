#!/usr/bin/env python3
"""
KLB v3.3c Backtest — Simulate suppression of bull REV signals at HIGH levels
=============================================================================
v3.3c change: SUPPRESS bull REV signals at HIGH levels (PM H, ORB H, Yest H, Week H).
Rationale: HIGH levels act as magnets (price is attracted back), not barriers.
A bull REV at a HIGH means "price bounced off the high" which often fails — the
high acts as a ceiling that has already been tested, reversals there are weak.

Simulation method:
  - Load all v3.3 signals with MFE/MAE (reusing v33_backtest pipeline)
  - Flag suppressed signals: bull + REV-type + level contains any HIGH key
  - Compare v3.3 vs v3.3c vs v3.2 stats

HIGH levels (strings to match in the 'levels' field):
  "PM H", "ORB H", "Yest H", "Week H"

Note: Combined levels like "VWAP + PM H" also suppressed if they contain a HIGH.
"""

import sys
import os

# ── Import from v33_backtest in same directory ────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

from v33_backtest import (
    load_and_parse_logs,
    compute_dim_status,
    load_1m,
    load_daily,
    compute_atr,
    measure_mfe_mae,
    sig_stats,
    format_sig,
    SYMBOLS,
    BAR_DIR,
    LOG_DIR,
)

import numpy as np
import pandas as pd

# ── Config ────────────────────────────────────────────────────────────────────
HIGH_LEVEL_KEYWORDS = ['PM H', 'ORB H', 'Yest H', 'Week H']
MAJOR_MFE_THRESHOLD = 1.0  # ATR — "major move" definition

DIVIDER = '=' * 72
SUBDIV  = '-' * 72


def is_bull_rev_at_high(sig):
    """Return True if signal should be suppressed by v3.3c rule."""
    if sig.get('direction') != 'bull':
        return False
    sig_type = sig.get('sig_type', '')
    if 'REV' not in sig_type:
        return False
    levels = sig.get('levels', '')
    for kw in HIGH_LEVEL_KEYWORDS:
        if kw in levels:
            return True
    return False


def print_stats_block(label, sigs, indent=''):
    st = sig_stats(sigs, label)
    print(f"{indent}{label}")
    print(f"{indent}  N={st['n']}  Win%={st['win_rate']:.1f}%  "
          f"Avg MFE={st['avg_mfe']:.4f}  Avg MAE={st['avg_mae']:.4f}  "
          f"Avg P&L={st['avg_pnl']:.4f}  Net ATR={st['net_atr']:+.2f}")
    return st


def compare_blocks(label_a, st_a, label_b, st_b, indent=''):
    delta_n    = st_b['n']    - st_a['n']
    delta_wr   = st_b['win_rate']  - st_a['win_rate']
    delta_mfe  = st_b['avg_mfe']   - st_a['avg_mfe']
    delta_mae  = st_b['avg_mae']   - st_a['avg_mae']
    delta_pnl  = st_b['avg_pnl']   - st_a['avg_pnl']
    delta_net  = st_b['net_atr']   - st_a['net_atr']
    print(f"{indent}Delta ({label_a} → {label_b}):  "
          f"N={delta_n:+d}  Win%={delta_wr:+.1f}pp  "
          f"AvgMFE={delta_mfe:+.4f}  AvgMAE={delta_mae:+.4f}  "
          f"AvgP&L={delta_pnl:+.4f}  NetATR={delta_net:+.2f}")


def main():
    print(DIVIDER)
    print('KLB v3.3c Backtest — Suppress bull REV at HIGH levels')
    print('v3.3c rule: bull + REV + level in [PM H, ORB H, Yest H, Week H] → SUPPRESS')
    print(DIVIDER)
    print()

    # ── 1. Parse logs ──────────────────────────────────────────────────────────
    print('Step 1: Parsing v3.3 logs...')
    signals_v33, _ = load_and_parse_logs('v33')
    print(f'  Total v3.3 raw signals: {len(signals_v33)}')
    print()

    print('Step 2: Parsing v3.2 logs...')
    signals_v32, _ = load_and_parse_logs('v32')
    print(f'  Total v3.2 raw signals: {len(signals_v32)}')
    print()

    # ── 2. Compute dim status (v3.3 quality filters) ──────────────────────────
    print('Step 3: Computing dim status for v3.3...')
    signals_v33 = compute_dim_status(signals_v33)

    # ── 3. Load IB 1m data and measure MFE/MAE ──────────────────────────────
    symbols_v33 = sorted(set(s['symbol'] for s in signals_v33))
    symbols_v32 = sorted(set(s['symbol'] for s in signals_v32))
    all_symbols  = sorted(set(symbols_v33) | set(symbols_v32))

    print(f'Symbols (v3.3): {symbols_v33}')
    print()

    ib_cache = {}
    print('Step 4: Loading IB 1m data...')
    for sym in all_symbols:
        print(f'  {sym}...', end=' ', flush=True)
        try:
            bars_1m    = load_1m(sym)
            daily_df   = load_daily(sym)
            atr_series = compute_atr(daily_df)
            ib_cache[sym] = (bars_1m, atr_series)
            print(f'{len(bars_1m)} bars')
        except Exception as exc:
            print(f'ERROR: {exc}')

    print()
    print('Step 5: Measuring MFE/MAE for v3.3 signals...')
    for sym in symbols_v33:
        if sym not in ib_cache:
            continue
        bars_1m, atr_series = ib_cache[sym]
        sym_sigs = [s for s in signals_v33 if s['symbol'] == sym]
        measure_mfe_mae(sym_sigs, bars_1m, atr_series)
        matched = sum(1 for s in sym_sigs
                      if s.get('mfe_atr') is not None and
                         (s['mfe_atr'] != 0 or s['mae_atr'] != 0))
        print(f'  {sym}: {len(sym_sigs)} signals, {matched} with MFE/MAE data')

    print()
    print('Step 6: Measuring MFE/MAE for v3.2 signals...')
    for sym in symbols_v32:
        if sym not in ib_cache:
            continue
        bars_1m, atr_series = ib_cache[sym]
        sym_sigs = [s for s in signals_v32 if s['symbol'] == sym]
        measure_mfe_mae(sym_sigs, bars_1m, atr_series)
        matched = sum(1 for s in sym_sigs
                      if s.get('mfe_atr') is not None and
                         (s['mfe_atr'] != 0 or s['mae_atr'] != 0))
        print(f'  {sym}: {len(sym_sigs)} signals, {matched} with MFE/MAE data')

    # ── 4. Build working datasets ──────────────────────────────────────────────
    v33_all   = [s for s in signals_v33 if s.get('mfe_atr') is not None]
    v32_all   = [s for s in signals_v32 if s.get('mfe_atr') is not None]

    # v3.3c: remove suppressed signals
    suppressed = [s for s in v33_all if is_bull_rev_at_high(s)]
    v33c_all   = [s for s in v33_all if not is_bull_rev_at_high(s)]

    print()
    print(DIVIDER)
    print('RESULTS')
    print(DIVIDER)

    # ══════════════════════════════════════════════════════════════════════════
    # A. OVERALL SUMMARY — v3.2 / v3.3 / v3.3c
    # ══════════════════════════════════════════════════════════════════════════
    print()
    print('A. OVERALL SUMMARY')
    print(SUBDIV)

    st32  = print_stats_block('v3.2 ', v32_all)
    st33  = print_stats_block('v3.3 ', v33_all)
    st33c = print_stats_block('v3.3c', v33c_all)
    print()
    compare_blocks('v3.2', st32,  'v3.3',  st33)
    compare_blocks('v3.3', st33,  'v3.3c', st33c)
    compare_blocks('v3.2', st32,  'v3.3c', st33c)

    # ══════════════════════════════════════════════════════════════════════════
    # B. SUPPRESSED SIGNALS (the ones v3.3c removes)
    # ══════════════════════════════════════════════════════════════════════════
    print()
    print('B. SUPPRESSED SIGNALS (bull REV at HIGH levels)')
    print(SUBDIV)
    print(f'  Count removed:  {len(suppressed)}')

    if suppressed:
        st_sup = sig_stats(suppressed)
        atr_saved = sum(s.get('pnl_atr', 0) for s in suppressed)
        print(f'  Win%:           {st_sup["win_rate"]:.1f}%')
        print(f'  Avg MFE:        {st_sup["avg_mfe"]:.4f} ATR')
        print(f'  Avg MAE:        {st_sup["avg_mae"]:.4f} ATR')
        print(f'  Avg P&L/sig:    {st_sup["avg_pnl"]:.4f} ATR')
        print(f'  Net P&L (sum):  {atr_saved:+.4f} ATR'
              f'  ← {"SAVING" if atr_saved < 0 else "GIVING UP"} this by suppressing')

        print()
        print('  Level breakdown:')
        for kw in HIGH_LEVEL_KEYWORDS:
            kw_sigs = [s for s in suppressed if kw in s.get('levels', '')]
            if kw_sigs:
                st_kw = sig_stats(kw_sigs)
                print(f'    {kw:<10}  N={st_kw["n"]}  Win%={st_kw["win_rate"]:.1f}%  '
                      f'Avg P&L={st_kw["avg_pnl"]:.4f}  Net ATR={st_kw["net_atr"]:+.2f}')

        print()
        print('  Suppressed signal detail:')
        for s in sorted(suppressed, key=lambda x: x.get('pnl_atr', 0), reverse=True):
            ts = s.get('timestamp', '')
            if hasattr(ts, 'strftime'):
                ts = ts.strftime('%Y-%m-%d %H:%M')
            print(f'    {s.get("symbol","?"):5} {ts}  {s.get("sig_type","?"):6} '
                  f'{s.get("direction","?")}  levels=[{s.get("levels","?")}]  '
                  f'MFE={s.get("mfe_atr",0):.3f}  MAE={s.get("mae_atr",0):.3f}  '
                  f'P&L={s.get("pnl_atr",0):.3f}  [{s.get("outcome","?")}]')

    # ══════════════════════════════════════════════════════════════════════════
    # C. BREAKDOWN BY SIGNAL TYPE (v3.3 vs v3.3c)
    # ══════════════════════════════════════════════════════════════════════════
    print()
    print('C. BREAKDOWN BY SIGNAL TYPE')
    print(SUBDIV)

    all_types = sorted(set(s.get('sig_type', '?') for s in v33_all))
    hdr = f"  {'Type':<10} {'v3.3 N':>7} {'v3.3 Win%':>10} {'v3.3 P&L':>10} {'v3.3 Net':>10} " \
          f"{'v3.3c N':>8} {'v3.3c Win%':>11} {'v3.3c P&L':>10} {'v3.3c Net':>10} {'Delta':>8}"
    print(hdr)
    print('  ' + '-' * (len(hdr) - 2))

    for t in all_types:
        s33_t  = [s for s in v33_all  if s.get('sig_type') == t]
        s33c_t = [s for s in v33c_all if s.get('sig_type') == t]
        st_t3  = sig_stats(s33_t)
        st_t3c = sig_stats(s33c_t)
        delta_net = st_t3c['net_atr'] - st_t3['net_atr']
        print(f"  {t:<10} {st_t3['n']:>7} {st_t3['win_rate']:>9.1f}% {st_t3['avg_pnl']:>10.4f} "
              f"{st_t3['net_atr']:>+10.2f} "
              f"{st_t3c['n']:>8} {st_t3c['win_rate']:>10.1f}% {st_t3c['avg_pnl']:>10.4f} "
              f"{st_t3c['net_atr']:>+10.2f} {delta_net:>+8.2f}")

    # ══════════════════════════════════════════════════════════════════════════
    # D. WIN RATE COMPARISON (v3.2 / v3.3 / v3.3c)
    # ══════════════════════════════════════════════════════════════════════════
    print()
    print('D. WIN RATE COMPARISON')
    print(SUBDIV)

    for label, sigs in [('v3.2 ', v32_all), ('v3.3 ', v33_all), ('v3.3c', v33c_all)]:
        n = len(sigs)
        if n == 0:
            print(f'  {label}  N=0')
            continue
        wins   = sum(1 for s in sigs if s.get('outcome') == 'WIN')
        losses = sum(1 for s in sigs if s.get('outcome') == 'LOSS')
        flats  = sum(1 for s in sigs if s.get('outcome') == 'FLAT')
        net    = sum(s.get('pnl_atr', 0) for s in sigs)
        print(f'  {label}  N={n:3d}  WIN={wins:3d} ({wins/n*100:.1f}%)  '
              f'LOSS={losses:3d} ({losses/n*100:.1f}%)  FLAT={flats:3d} ({flats/n*100:.1f}%)  '
              f'Net={net:+.2f} ATR')

    # ══════════════════════════════════════════════════════════════════════════
    # E. PER-SYMBOL COMPARISON
    # ══════════════════════════════════════════════════════════════════════════
    print()
    print('E. PER-SYMBOL COMPARISON (v3.2 vs v3.3 vs v3.3c)')
    print(SUBDIV)
    hdr2 = (f"  {'Symbol':<6} "
            f"{'v3.2 N':>7} {'v3.2 Net':>9} "
            f"{'v3.3 N':>7} {'v3.3 Net':>9} {'v3.3 Win%':>10} "
            f"{'v3.3c N':>8} {'v3.3c Net':>10} {'v3.3c Win%':>11} "
            f"{'D(3.3→3.3c)':>12}")
    print(hdr2)
    print('  ' + '-' * (len(hdr2) - 2))

    for sym in SYMBOLS:
        s32  = [s for s in v32_all  if s['symbol'] == sym]
        s33  = [s for s in v33_all  if s['symbol'] == sym]
        s33c = [s for s in v33c_all if s['symbol'] == sym]
        if not s33 and not s32:
            continue
        st32_s  = sig_stats(s32)
        st33_s  = sig_stats(s33)
        st33c_s = sig_stats(s33c)
        delta   = st33c_s['net_atr'] - st33_s['net_atr']
        print(f"  {sym:<6} "
              f"{st32_s['n']:>7} {st32_s['net_atr']:>+9.2f} "
              f"{st33_s['n']:>7} {st33_s['net_atr']:>+9.2f} {st33_s['win_rate']:>9.1f}% "
              f"{st33c_s['n']:>8} {st33c_s['net_atr']:>+10.2f} {st33c_s['win_rate']:>10.1f}% "
              f"{delta:>+12.2f}")

    # ══════════════════════════════════════════════════════════════════════════
    # F. MAJOR MOVES COVERAGE (MFE >= 1.0 ATR)
    # ══════════════════════════════════════════════════════════════════════════
    print()
    print('F. MAJOR MOVES COVERAGE (MFE >= 1.0 ATR)')
    print(SUBDIV)

    maj32  = [s for s in v32_all  if s.get('mfe_atr', 0) >= MAJOR_MFE_THRESHOLD]
    maj33  = [s for s in v33_all  if s.get('mfe_atr', 0) >= MAJOR_MFE_THRESHOLD]
    maj33c = [s for s in v33c_all if s.get('mfe_atr', 0) >= MAJOR_MFE_THRESHOLD]
    sup_major = [s for s in suppressed if s.get('mfe_atr', 0) >= MAJOR_MFE_THRESHOLD]

    n32  = len(v32_all)
    n33  = len(v33_all)
    n33c = len(v33c_all)

    print(f'  v3.2:  major={len(maj32)} / {n32} signals  ({len(maj32)/n32*100:.1f}% are major)')
    print(f'  v3.3:  major={len(maj33)} / {n33} signals  ({len(maj33)/n33*100:.1f}% are major)')
    print(f'  v3.3c: major={len(maj33c)} / {n33c} signals ({len(maj33c)/n33c*100:.1f}% are major)')
    print()
    print(f'  Suppressed signals that were major moves (MFE >= 1.0 ATR):  {len(sup_major)}')
    if suppressed:
        print(f'  (= {len(sup_major)/len(suppressed)*100:.1f}% of suppressed had MFE >= 1 ATR)')

    if sup_major:
        print()
        print('  Major moves being lost by v3.3c suppression:')
        for s in sorted(sup_major, key=lambda x: x.get('mfe_atr', 0), reverse=True):
            ts = s.get('timestamp', '')
            if hasattr(ts, 'strftime'):
                ts = ts.strftime('%Y-%m-%d %H:%M')
            print(f'    {s.get("symbol","?"):5} {ts}  {s.get("sig_type","?"):6} '
                  f'levels=[{s.get("levels","?")}]  '
                  f'MFE={s.get("mfe_atr",0):.3f}  MAE={s.get("mae_atr",0):.3f}  '
                  f'P&L={s.get("pnl_atr",0):.3f}  [{s.get("outcome","?")}]')

    print()
    print(SUBDIV)
    print('SUMMARY')
    print(SUBDIV)
    print(f'  Suppressed: {len(suppressed)} bull REV at HIGH signals')
    if suppressed:
        sup_net = sum(s.get('pnl_atr', 0) for s in suppressed)
        sup_wins = sum(1 for s in suppressed if s.get('outcome') == 'WIN')
        print(f'  Suppressed net P&L: {sup_net:+.2f} ATR  '
              f'(suppressing {"SAVES" if sup_net < 0 else "COSTS"} {abs(sup_net):.2f} ATR)')
        print(f'  Suppressed win rate: {sup_wins}/{len(suppressed)} = '
              f'{sup_wins/len(suppressed)*100:.1f}%')
        print(f'  Major moves lost: {len(sup_major)} '
              f'({len(sup_major)/len(suppressed)*100:.1f}% of suppressed)')
    net_v33  = sum(s.get('pnl_atr', 0) for s in v33_all)
    net_v33c = sum(s.get('pnl_atr', 0) for s in v33c_all)
    net_v32  = sum(s.get('pnl_atr', 0) for s in v32_all)
    print()
    print(f'  Net ATR:  v3.2={net_v32:+.2f}  v3.3={net_v33:+.2f}  v3.3c={net_v33c:+.2f}')
    print(f'  v3.3 → v3.3c delta: {net_v33c - net_v33:+.2f} ATR')
    print(f'  v3.2 → v3.3c delta: {net_v33c - net_v32:+.2f} ATR')
    print(DIVIDER)


if __name__ == '__main__':
    main()
