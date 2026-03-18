#!/usr/bin/env python3
"""
KLB v3.5 vs v3.4 Comparison
============================
Reuses the v34_proper_comparison pipeline for signal loading/dedup,
and the v34_realistic_pnl pipeline for P&L simulation.

Analyses:
  1. Quick sanity check — signal counts by type, afternoon signals, SL sample
  2. Realistic P&L (SL from log + 60m exit): v3.4 vs v3.5
  3. Afternoon check — signals after 14:00 in each version
  4. SL adaptation visible in logs — morning vs midday slHard/ATR ratio
  5. NVDA check — bull REV (should be ~19, ORB L only), bear REV preserved

Usage:
    python3 v35_comparison.py
"""

import sys
import os
import glob
import time
import re
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

# ── Import pipeline from v34_proper_comparison ────────────────────────────────
from v34_proper_comparison import (
    find_files,
    filter_v34_by_date,
    dedup_files,
)

# ── Import from v33_backtest (the core parsing/IB pipeline) ───────────────────
from v33_backtest import (
    parse_pine_log   as parse_pine_log_v33,
    identify_symbol,
    load_1m,
    load_daily,
    compute_atr,
    SYMBOLS,
    BAR_DIR,
    LOG_DIR,
)

# ── Import simulate_trade from v34_realistic_pnl ──────────────────────────────
from v34_realistic_pnl import (
    parse_pine_log   as parse_pine_log_v34,   # has SL field support
    identify_symbol  as identify_symbol_v34,
    load_1m          as load_1m_v34,
    simulate_trade,
    EXIT_MINUTES,
    SL_ATR_FRAC,
    WIN_THRESH,
)

DIV  = '=' * 76
SDIV = '-' * 76

OUT_FILE = LOG_DIR / 'v35_comparison_results.txt'

_output_lines = []


def out(s=''):
    print(s)
    _output_lines.append(str(s))


# ── Helper: parse a log file to signals using v34 parser (SL-aware) ──────────

def load_version_signals(version, filepaths):
    """Parse all log files for a version. Returns list of raw signal dicts."""
    all_signals = []
    for fp in filepaths:
        short = Path(fp).stem.split('_')[-1]
        sigs = parse_pine_log_v34(fp)
        if not sigs:
            out(f'    {short}: 0 signals')
            continue
        sym = identify_symbol_v34(sigs)
        if sym is None:
            out(f'    {short}: could not identify symbol — skipping')
            continue
        for s in sigs:
            s['symbol'] = sym
            s['version'] = version
            s['log_file'] = short
        all_signals.extend(sigs)
        out(f'    {short}: {sym} — {len(sigs)} signals')
    # Exclude RNG
    all_signals = [s for s in all_signals if s.get('sig_type') != 'RNG']
    return all_signals


def simulate_version(signals, bars_by_sym):
    """Run simulate_trade on all signals. Returns list of result dicts."""
    rows = []
    no_data = no_result = 0
    for sig in signals:
        sym = sig.get('symbol')
        if sym not in bars_by_sym:
            no_data += 1
            continue
        r = simulate_trade(sig, bars_by_sym[sym])
        if r is None:
            no_result += 1
            continue
        r['symbol']   = sym
        r['version']  = sig.get('version')
        r['sig_type'] = sig.get('sig_type')
        r['direction']= sig.get('direction')
        r['levels']   = sig.get('levels', '')
        r['timestamp']= sig.get('timestamp')
        r['atr']      = sig.get('atr')
        r['sl_hard_price'] = sig.get('sl_hard')
        rows.append(r)
    out(f'  Simulated: {len(rows)} trades (no_data={no_data}, no_result={no_result})')
    return rows


def pnl_stats(rows, col='combined_pnl_60m'):
    """Return (N, win_pct, net_atr, per_sig) for a list of trade rows."""
    vals = [r[col] for r in rows if r.get(col) is not None]
    n = len(vals)
    if n == 0:
        return 0, float('nan'), 0.0, float('nan')
    arr = np.array(vals)
    win_pct = (arr > WIN_THRESH).sum() / n * 100
    net     = arr.sum()
    per_sig = net / n
    return n, win_pct, net, per_sig


def print_pnl_row(label, rows, col='combined_pnl_60m', width=28):
    n, win, net, ps = pnl_stats(rows, col)
    if n == 0:
        out(f'  {label:<{width}}  N=   0   —')
        return {'n': n, 'win': win, 'net': net, 'ps': ps}
    out(f'  {label:<{width}}  N={n:4d}  Win={win:5.1f}%  Net={net:+8.1f} ATR  /sig={ps:+.3f}')
    return {'n': n, 'win': win, 'net': net, 'ps': ps}


def delta_row(label, sa, sb, width=28):
    if sa['n'] == 0 and sb['n'] == 0:
        return
    dn   = sb['n']   - sa['n']
    dw   = (sb['win'] - sa['win']) if (sa['n'] > 0 and sb['n'] > 0) else float('nan')
    dn_  = sb['net'] - sa['net']
    dp   = (sb['ps']  - sa['ps'])  if (sa['n'] > 0 and sb['n'] > 0) else float('nan')
    out(f'  {"  Δ "+label:<{width}}  ΔN={dn:+4d}  ΔWin={dw:+5.1f}%  ΔNet={dn_:+8.1f} ATR  Δ/sig={dp:+.3f}')


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    out(DIV)
    out('KLB v3.5 vs v3.4 — Comparison')
    out(DIV)

    # ── Discover files ─────────────────────────────────────────────────────────
    out('\nFinding log files...')
    v35_files_all = find_files('v3.5')
    v34_files_all = find_files('v3.4')
    out(f'  v3.5: {len(v35_files_all)} files found')
    out(f'  v3.4: {len(v34_files_all)} files found')

    out('\nFiltering v3.4 by date (8 März only)...')
    v34_files_all = filter_v34_by_date(v34_files_all)

    out('\nDeduplicating...')
    v35_files = dedup_files(v35_files_all)
    v34_files = dedup_files(v34_files_all)
    out(f'  v3.5: {len(v35_files)} unique files')
    out(f'  v3.4: {len(v34_files)} unique files')

    # ── Load signals ───────────────────────────────────────────────────────────
    out(f'\n{SDIV}')
    out('Loading v3.4 signals...')
    v34_sigs = load_version_signals('v3.4', v34_files)

    out(f'\n{SDIV}')
    out('Loading v3.5 signals...')
    v35_sigs = load_version_signals('v3.5', v35_files)

    out(f'\n  v3.4 total signals (excl RNG): {len(v34_sigs)}')
    out(f'  v3.5 total signals (excl RNG): {len(v35_sigs)}')

    # ── Pre-load 1m bars ───────────────────────────────────────────────────────
    all_syms = sorted(set(s['symbol'] for s in v34_sigs + v35_sigs if s.get('symbol')))
    bars_by_sym = {}
    for sym in all_syms:
        try:
            bars_by_sym[sym] = load_1m_v34(sym)
        except Exception as e:
            out(f'  WARNING: could not load 1m bars for {sym}: {e}')

    # ── Simulate trades ────────────────────────────────────────────────────────
    out(f'\n{SDIV}')
    out('Simulating v3.4 trades...')
    v34_trades = simulate_version(v34_sigs, bars_by_sym)

    out('\nSimulating v3.5 trades...')
    v35_trades = simulate_version(v35_sigs, bars_by_sym)

    df34 = pd.DataFrame(v34_trades) if v34_trades else pd.DataFrame()
    df35 = pd.DataFrame(v35_trades) if v35_trades else pd.DataFrame()

    # ══════════════════════════════════════════════════════════════════════════
    out(f'\n{DIV}')
    out('SECTION 1 — Quick Sanity Check: Signal Counts by Type')
    out(DIV)

    def count_by_type(sigs):
        counts = defaultdict(int)
        for s in sigs:
            counts[s.get('sig_type', 'UNK')] += 1
        return counts

    c34 = count_by_type(v34_sigs)
    c35 = count_by_type(v35_sigs)

    all_types = sorted(set(list(c34.keys()) + list(c35.keys())))
    out(f'\n  {"Type":<8} {"v3.4":>6} {"v3.5":>6} {"Δ":>6}')
    out(f'  {"-"*8} {"-"*6} {"-"*6} {"-"*6}')
    for t in ['BRK', 'REV', 'FADE', 'QBS', 'RNG']:
        n34 = c34.get(t, 0)
        n35 = c35.get(t, 0)
        out(f'  {t:<8} {n34:>6} {n35:>6} {n35-n34:>+6}')

    # Note: RNG was excluded from sigs already — recount from raw parse
    out('\n  (RNG excluded from signals list above — counted separately)')

    # Count from raw log files for RNG (parse first row of each)
    rng34 = rng35 = 0
    rng_pat = re.compile(r'\[KLB\].*RNG range break')
    for fp in v34_files:
        with open(fp, 'r', encoding='utf-8') as f:
            for line in f:
                if rng_pat.search(line):
                    rng34 += 1
    for fp in v35_files:
        with open(fp, 'r', encoding='utf-8') as f:
            for line in f:
                if rng_pat.search(line):
                    rng35 += 1
    out(f'  {"RNG":<8} {rng34:>6} {rng35:>6} {rng35-rng34:>+6}  (raw count from logs)')

    # ══════════════════════════════════════════════════════════════════════════
    out(f'\n{DIV}')
    out('SECTION 2 — Realistic P&L (SL from log + 60m exit)')
    out(DIV)

    out('\n  Overall (all signal types, SL=log slHard, exit=60m):')
    sa = print_pnl_row('v3.4', v34_trades)
    sb = print_pnl_row('v3.5', v35_trades)
    delta_row('v3.4→v3.5', sa, sb)

    out('\n  By signal type:')
    for t in ['BRK', 'REV', 'FADE', 'QBS']:
        t34 = [r for r in v34_trades if r.get('sig_type') == t]
        t35 = [r for r in v35_trades if r.get('sig_type') == t]
        out(f'\n  [{t}]')
        sta = print_pnl_row(f'    v3.4 {t}', t34, width=20)
        stb = print_pnl_row(f'    v3.5 {t}', t35, width=20)
        delta_row(t, sta, stb, width=20)

    out('\n  REV — direction breakdown:')
    for d in ['bull', 'bear']:
        r34 = [r for r in v34_trades if r.get('sig_type') == 'REV' and r.get('direction') == d]
        r35 = [r for r in v35_trades if r.get('sig_type') == 'REV' and r.get('direction') == d]
        out(f'\n    {d.upper()} REV:')
        sta = print_pnl_row(f'      v3.4 {d}', r34, width=18)
        stb = print_pnl_row(f'      v3.5 {d}', r35, width=18)
        delta_row(d, sta, stb, width=18)

    out('\n  Summary table:')
    out(f'  {"Version":<8} {"N":>5} {"SL hit%":>8} {"Net ATR":>9} {"/signal":>8} {"Win%":>6}')
    out(f'  {"-"*8} {"-"*5} {"-"*8} {"-"*9} {"-"*8} {"-"*6}')
    for label, trades in [('v3.4', v34_trades), ('v3.5', v35_trades)]:
        n, win, net, ps = pnl_stats(trades)
        sl_hit_pct = sum(1 for r in trades if r.get('sl_hit', False)) / max(len(trades), 1) * 100
        out(f'  {label:<8} {n:>5} {sl_hit_pct:>7.1f}% {net:>+9.1f} {ps:>+8.3f} {win:>5.1f}%')

    # ══════════════════════════════════════════════════════════════════════════
    out(f'\n{DIV}')
    out('SECTION 3 — Afternoon Check (signals after 14:00 ET)')
    out(DIV)

    def afternoon_signals(sigs):
        result = []
        for s in sigs:
            ts = s.get('timestamp')
            if ts is None:
                continue
            if hasattr(ts, 'tzinfo') and ts.tzinfo is not None:
                ts_et = ts.tz_convert('US/Eastern')
            else:
                ts_et = pd.Timestamp(ts, tz='US/Eastern')
            if ts_et.hour >= 14:
                result.append(s)
        return result

    aft34 = afternoon_signals(v34_sigs)
    aft35 = afternoon_signals(v35_sigs)

    out(f'\n  v3.4: {len(aft34)} signals after 14:00  ({len(aft34)/max(len(v34_sigs),1)*100:.1f}% of total)')
    out(f'  v3.5: {len(aft35)} signals after 14:00  ({len(aft35)/max(len(v35_sigs),1)*100:.1f}% of total)')
    out(f'  Δ: {len(aft35)-len(aft34):+d} afternoon signals')

    if aft35:
        out('\n  v3.5 afternoon signals by type:')
        ac35 = defaultdict(int)
        for s in aft35:
            ac35[s.get('sig_type', 'UNK')] += 1
        for t, cnt in sorted(ac35.items()):
            out(f'    {t}: {cnt}')

    # ══════════════════════════════════════════════════════════════════════════
    out(f'\n{DIV}')
    out('SECTION 4 — SL Adaptation in Logs (v3.5 morning vs midday slHard/ATR)')
    out(DIV)

    # Parse slHard directly from v3.5 logs — we have sl_hard_price and atr in trades
    # Need: sl_hard_price / atr ratio by time window

    def get_sl_ratio(sigs, sym_filter=None):
        """Return list of (timestamp, slHard/ATR) for signals with SL data."""
        result = []
        for s in sigs:
            if sym_filter and s.get('symbol') != sym_filter:
                continue
            sl_hard = s.get('sl_hard')
            atr     = s.get('atr')
            if sl_hard is None or atr is None or atr == 0:
                continue
            entry_c = s.get('close')
            if entry_c is None:
                continue
            direction = s.get('direction', 'bull')
            ts = s.get('timestamp')
            if ts is None:
                continue
            if hasattr(ts, 'tzinfo') and ts.tzinfo is not None:
                ts_et = ts.tz_convert('US/Eastern')
            else:
                ts_et = pd.Timestamp(ts, tz='US/Eastern')
            # slHard distance from close price (not entry, but close is available in log)
            if direction == 'bull':
                sl_dist = (entry_c - sl_hard) / atr
            else:
                sl_dist = (sl_hard - entry_c) / atr
            result.append((ts_et, sl_dist))
        return result

    sl_ratios_35 = get_sl_ratio(v35_sigs)
    sl_ratios_34 = get_sl_ratio(v34_sigs)

    def categorize_by_time(sl_ratios):
        morning  = [(ts, r) for ts, r in sl_ratios if ts.hour < 12]
        midday   = [(ts, r) for ts, r in sl_ratios if 12 <= ts.hour < 15]
        aft      = [(ts, r) for ts, r in sl_ratios if ts.hour >= 15]
        return morning, midday, aft

    m35, md35, a35 = categorize_by_time(sl_ratios_35)
    m34, md34, a34 = categorize_by_time(sl_ratios_34)

    out(f'\n  v3.5 SL=slHard distance from signal close (in ATR units):')
    out(f'  {"Window":<12} {"N":>5} {"Mean slDist":>12} {"Min":>8} {"Max":>8}')
    out(f'  {"-"*12} {"-"*5} {"-"*12} {"-"*8} {"-"*8}')
    for label, data in [('Morning', m35), ('Midday', md35), ('Afternoon', a35)]:
        vals = [r for _, r in data]
        if not vals:
            out(f'  {label:<12} {"0":>5}  —')
            continue
        arr = np.array(vals)
        out(f'  {label:<12} {len(arr):>5} {arr.mean():>12.4f} {arr.min():>8.4f} {arr.max():>8.4f}')

    out(f'\n  v3.4 SL=slHard distance from signal close (baseline comparison):')
    out(f'  {"Window":<12} {"N":>5} {"Mean slDist":>12} {"Min":>8} {"Max":>8}')
    out(f'  {"-"*12} {"-"*5} {"-"*12} {"-"*8} {"-"*8}')
    for label, data in [('Morning', m34), ('Midday', md34), ('Afternoon', a34)]:
        vals = [r for _, r in data]
        if not vals:
            out(f'  {label:<12} {"0":>5}  —')
            continue
        arr = np.array(vals)
        out(f'  {label:<12} {len(arr):>5} {arr.mean():>12.4f} {arr.min():>8.4f} {arr.max():>8.4f}')

    # Sample 5 morning + 5 midday from v3.5 with raw SL values
    out(f'\n  v3.5 sample signals (raw slHard, ATR, slDist from close):')
    out(f'  {"Time":<8} {"Symbol":<6} {"Dir":<5} {"Type":<5} {"Close":>8} {"SL":>8} {"ATR":>7} {"slDist/ATR":>11}')
    out(f'  {"-"*8} {"-"*6} {"-"*5} {"-"*5} {"-"*8} {"-"*8} {"-"*7} {"-"*11}')

    morning_sigs  = [(ts, s) for s, (ts, _) in zip(v35_sigs, get_sl_ratio(v35_sigs)) if ts.hour < 12]
    midday_sigs   = [(ts, s) for s, (ts, _) in zip(v35_sigs, get_sl_ratio(v35_sigs)) if 12 <= ts.hour < 15]

    # Cleaner approach: iterate v35_sigs directly
    sampled_m = sampled_md = 0
    for s in v35_sigs:
        if s.get('sl_hard') is None or s.get('atr') is None:
            continue
        ts = s.get('timestamp')
        if ts is None:
            continue
        if hasattr(ts, 'tzinfo') and ts.tzinfo is not None:
            ts_et = ts.tz_convert('US/Eastern')
        else:
            ts_et = pd.Timestamp(ts, tz='US/Eastern')
        hour = ts_et.hour
        if hour < 12 and sampled_m < 5:
            sl = s['sl_hard']
            atr = s['atr']
            c   = s.get('close', float('nan'))
            d   = s.get('direction', '?')
            dist = (c - sl) / atr if d == 'bull' else (sl - c) / atr
            out(f'  {s.get("time_str","?"):<8} {s.get("symbol","?"):<6} {d:<5} '
                f'{s.get("sig_type","?"):<5} {c:>8.2f} {sl:>8.2f} {atr:>7.4f} {dist:>11.4f}  [morning]')
            sampled_m += 1
        elif 12 <= hour < 15 and sampled_md < 5:
            sl = s['sl_hard']
            atr = s['atr']
            c   = s.get('close', float('nan'))
            d   = s.get('direction', '?')
            dist = (c - sl) / atr if d == 'bull' else (sl - c) / atr
            out(f'  {s.get("time_str","?"):<8} {s.get("symbol","?"):<6} {d:<5} '
                f'{s.get("sig_type","?"):<5} {c:>8.2f} {sl:>8.2f} {atr:>7.4f} {dist:>11.4f}  [midday]')
            sampled_md += 1
        if sampled_m >= 5 and sampled_md >= 5:
            break

    # ══════════════════════════════════════════════════════════════════════════
    out(f'\n{DIV}')
    out('SECTION 5 — NVDA Check')
    out(DIV)

    nvda34 = [s for s in v34_sigs if s.get('symbol') == 'NVDA']
    nvda35 = [s for s in v35_sigs if s.get('symbol') == 'NVDA']

    if not nvda34 and not nvda35:
        out('\n  No NVDA signals found (may not be in log files).')
    else:
        out(f'\n  {"Signal":<30} {"v3.4":>6} {"v3.5":>6} {"Δ":>5}')
        out(f'  {"-"*30} {"-"*6} {"-"*6} {"-"*5}')

        def nvda_count(sigs, stype, direction=None):
            return sum(1 for s in sigs
                       if s.get('sig_type') == stype
                       and (direction is None or s.get('direction') == direction))

        def nvda_count_level(sigs, stype, direction, keyword):
            return sum(1 for s in sigs
                       if s.get('sig_type') == stype
                       and s.get('direction') == direction
                       and keyword.lower() in s.get('levels', '').lower())

        categories = [
            ('Bull REV total',    lambda s: nvda_count(s, 'REV', 'bull')),
            ('Bull REV @ ORB L',  lambda s: nvda_count_level(s, 'REV', 'bull', 'ORB L')),
            ('Bull REV @ ORB L',  lambda s: nvda_count_level(s, 'REV', 'bull', 'orb l')),
            ('Bear REV total',    lambda s: nvda_count(s, 'REV', 'bear')),
            ('Bull BRK',          lambda s: nvda_count(s, 'BRK', 'bull')),
            ('Bear BRK',          lambda s: nvda_count(s, 'BRK', 'bear')),
            ('FADE',              lambda s: nvda_count(s, 'FADE')),
            ('All signals',       lambda s: len(s)),
        ]

        printed_orb = False
        for label, fn in categories:
            if 'ORB L' in label:
                if printed_orb:
                    continue
                printed_orb = True
                # Use single keyword check
                n34_orb = sum(1 for s in nvda34
                              if s.get('sig_type') == 'REV'
                              and s.get('direction') == 'bull'
                              and 'orb l' in s.get('levels', '').lower())
                n35_orb = sum(1 for s in nvda35
                              if s.get('sig_type') == 'REV'
                              and s.get('direction') == 'bull'
                              and 'orb l' in s.get('levels', '').lower())
                out(f'  {"Bull REV @ ORB L":<30} {n34_orb:>6} {n35_orb:>6} {n35_orb-n34_orb:>+5}')
                continue
            n34_ = fn(nvda34)
            n35_ = fn(nvda35)
            out(f'  {label:<30} {n34_:>6} {n35_:>6} {n35_-n34_:>+5}')

        # P&L comparison for NVDA (trades)
        nvda34_t = [r for r in v34_trades if r.get('symbol') == 'NVDA']
        nvda35_t = [r for r in v35_trades if r.get('symbol') == 'NVDA']

        out(f'\n  NVDA P&L (SL from log + 60m exit):')
        print_pnl_row('  v3.4 NVDA all', nvda34_t, width=22)
        print_pnl_row('  v3.5 NVDA all', nvda35_t, width=22)

        nvda34_bull_rev_t = [r for r in nvda34_t if r.get('sig_type')=='REV' and r.get('direction')=='bull']
        nvda35_bull_rev_t = [r for r in nvda35_t if r.get('sig_type')=='REV' and r.get('direction')=='bull']
        nvda34_bear_rev_t = [r for r in nvda34_t if r.get('sig_type')=='REV' and r.get('direction')=='bear']
        nvda35_bear_rev_t = [r for r in nvda35_t if r.get('sig_type')=='REV' and r.get('direction')=='bear']

        out('')
        print_pnl_row('  v3.4 NVDA Bull REV', nvda34_bull_rev_t, width=22)
        print_pnl_row('  v3.5 NVDA Bull REV', nvda35_bull_rev_t, width=22)
        print_pnl_row('  v3.4 NVDA Bear REV', nvda34_bear_rev_t, width=22)
        print_pnl_row('  v3.5 NVDA Bear REV', nvda35_bear_rev_t, width=22)

    # ══════════════════════════════════════════════════════════════════════════
    out(f'\n{DIV}')
    out('APPENDIX — Top 20 Levels by Count (v3.5)')
    out(DIV)
    from collections import Counter
    ctr = Counter(
        f"{s.get('direction','?')[0].upper()} {s.get('sig_type','?')} {s.get('levels','?')}"
        for s in v35_sigs
    )
    for item, cnt in ctr.most_common(20):
        out(f'  {cnt:4d}  {item}')

    # ── Save ───────────────────────────────────────────────────────────────────
    out(f'\n{DIV}')
    out(f'Results saved to: {OUT_FILE}')
    out(DIV)

    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(_output_lines))


if __name__ == '__main__':
    main()
