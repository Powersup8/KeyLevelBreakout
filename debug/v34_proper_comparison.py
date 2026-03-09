#!/usr/bin/env python3
"""
KLB v3.3c vs v3.4 Proper Backtest Comparison
==============================================
Uses the v33_backtest pipeline (parse → identify symbol → measure MFE/MAE from IB 1m).
Filters v3.4 files to those modified on 8 März (not 9 März).
Deduplicates log files by first-20-rows fingerprint.

Usage:
    python3 v34_proper_comparison.py
"""

import sys
import os
import glob
import time
from pathlib import Path
from collections import defaultdict

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

# Import the full pipeline from v33_backtest
from v33_backtest import (
    parse_pine_log,
    identify_symbol,
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

DIV  = '=' * 72
SDIV = '-' * 72

# ── File discovery ────────────────────────────────────────────────────────────

def find_files(version):
    """Return log file paths for a version string (e.g. 'v3.3c', 'v3.4')."""
    pattern = str(LOG_DIR / f"pine-logs-Key Level Breakout {version}_*.csv")
    return sorted(glob.glob(pattern))

def filter_v34_by_date(filepaths):
    """Keep only files modified on day 8 (8 März)."""
    kept = []
    removed = []
    for fp in filepaths:
        mtime = os.path.getmtime(fp)
        day = time.strftime("%d", time.localtime(mtime))
        if day == "08":
            kept.append(fp)
        else:
            removed.append(fp)
    if removed:
        print(f"  Removed {len(removed)} file(s) with mtime != 8 März:")
        for fp in removed:
            print(f"    {os.path.basename(fp)}")
    return kept

def dedup_files(filepaths):
    """Remove duplicate log files by fingerprinting first 20 content lines."""
    seen_fps = set()
    unique = []
    skipped = []
    for fp in filepaths:
        try:
            with open(fp, encoding='utf-8') as f:
                lines = [f.readline() for _ in range(21)]
            key = tuple(lines)
        except Exception:
            key = (fp,)
        if key not in seen_fps:
            seen_fps.add(key)
            unique.append(fp)
        else:
            skipped.append(fp)
    if skipped:
        print(f"  Deduplicated {len(skipped)} duplicate file(s):")
        for fp in skipped:
            print(f"    {os.path.basename(fp)}")
    return unique

# ── Load and enrich signals ───────────────────────────────────────────────────

def load_version(version, filepaths, ib_cache):
    """Parse logs, identify symbols, measure MFE/MAE. Returns list of signal dicts."""
    all_signals = []

    for fp in filepaths:
        short = Path(fp).stem.split('_')[-1]
        sigs = parse_pine_log(fp)
        if not sigs:
            print(f"    {short}: 0 signals (empty or parse fail)")
            continue

        symbol = identify_symbol(sigs)
        if symbol is None:
            print(f"    {short}: could not identify symbol — skipping")
            continue

        for s in sigs:
            s['symbol'] = symbol
            s['version'] = version
            s['log_file'] = short

        all_signals.extend(sigs)
        print(f"    {short}: {symbol} — {len(sigs)} signals")

    # Load IB data for any new symbols
    symbols_needed = sorted(set(s['symbol'] for s in all_signals))
    for sym in symbols_needed:
        if sym not in ib_cache:
            try:
                bars_1m = load_1m(sym)
                daily   = load_daily(sym)
                atr_s   = compute_atr(daily)
                ib_cache[sym] = (bars_1m, atr_s)
                print(f"    IB data loaded: {sym} ({len(bars_1m)} 1m bars)")
            except Exception as e:
                print(f"    IB data FAILED for {sym}: {e}")

    # Measure MFE/MAE
    for sym in symbols_needed:
        if sym not in ib_cache:
            continue
        bars_1m, atr_s = ib_cache[sym]
        sym_sigs = [s for s in all_signals if s['symbol'] == sym]
        measure_mfe_mae(sym_sigs, bars_1m, atr_s)
        matched = sum(1 for s in sym_sigs if s.get('mfe_atr') is not None)
        print(f"    MFE/MAE: {sym} {matched}/{len(sym_sigs)} matched")

    # Filter to signals with MFE/MAE data
    with_data = [s for s in all_signals if s.get('mfe_atr') is not None]
    print(f"  {version}: {len(all_signals)} total signals, {len(with_data)} with MFE/MAE")
    return with_data

# ── Reporting helpers ─────────────────────────────────────────────────────────

def pr(label, sigs, width=30):
    """Print one stats row and return stats dict."""
    st = sig_stats(sigs)
    if st['n'] == 0:
        print(f"  {label:<{width}}  N=0   —")
        return st
    print(f"  {label:<{width}}  N={st['n']:4d}  Win={st['win_rate']:5.1f}%  "
          f"Net={st['net_atr']:+8.1f} ATR  /sig={st['avg_pnl']:+.3f}")
    return st

def delta(label, sa, sb, width=30):
    if sa['n'] == 0 and sb['n'] == 0:
        return
    dn   = sb['n']       - sa['n']
    dw   = sb['win_rate']- sa['win_rate']
    dnet = sb['net_atr'] - sa['net_atr']
    dps  = sb['avg_pnl'] - sa['avg_pnl']
    print(f"  {'  Δ '+label:<{width}}  ΔN={dn:+4d}  ΔWin={dw:+5.1f}%  "
          f"ΔNet={dnet:+8.1f} ATR  Δ/sig={dps:+.3f}")

# ── Signal classification helpers ────────────────────────────────────────────

def by_type(sigs, t):
    return [s for s in sigs if s.get('sig_type') == t]

def by_dir(sigs, d):
    return [s for s in sigs if s.get('direction') == d]

def by_sym(sigs, sym):
    return [s for s in sigs if s.get('symbol') == sym]

def level_contains(sigs, *keywords):
    result = []
    for s in sigs:
        lvl = s.get('levels', '').lower()
        if any(k.lower() in lvl for k in keywords):
            result.append(s)
    return result

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(DIV)
    print("KLB v3.3c vs v3.4 — Proper Backtest Comparison")
    print(DIV)

    # ── Discover files ────────────────────────────────────────────────────────
    print("\nFinding log files...")
    v33c_files_all = find_files('v3.3c')
    v34_files_all  = find_files('v3.4')
    print(f"  v3.3c: {len(v33c_files_all)} files found")
    print(f"  v3.4:  {len(v34_files_all)} files found")

    print("\nFiltering v3.4 by date (8 März only)...")
    v34_files_all = filter_v34_by_date(v34_files_all)

    print("\nDeduplicating...")
    v33c_files = dedup_files(v33c_files_all)
    v34_files  = dedup_files(v34_files_all)
    print(f"  v3.3c: {len(v33c_files)} unique files")
    print(f"  v3.4:  {len(v34_files)} unique files")

    # ── Load signals ──────────────────────────────────────────────────────────
    ib_cache = {}  # shared IB data cache

    print(f"\n{SDIV}")
    print("Loading v3.3c signals...")
    v33c = load_version('v3.3c', v33c_files, ib_cache)

    print(f"\n{SDIV}")
    print("Loading v3.4 signals...")
    v34  = load_version('v3.4',  v34_files,  ib_cache)

    # Exclude RNG from stats (MFE/MAE unreliable)
    def excl_rng(sigs):
        return [s for s in sigs if s.get('sig_type') != 'RNG']

    a = excl_rng(v33c)
    b = excl_rng(v34)

    # ── Section 1: Overall Summary ────────────────────────────────────────────
    print(f"\n{DIV}")
    print("SECTION 1 — Overall Summary (RNG excluded from win/ATR)")
    print(DIV)

    sa = pr("v3.3c", a)
    sb = pr("v3.4",  b)
    delta("v3.3c→v3.4", sa, sb)

    rng_a = by_type(v33c, 'RNG')
    rng_b = by_type(v34,  'RNG')
    print(f"\n  RNG signals (counts only): v3.3c={len(rng_a)}  v3.4={len(rng_b)}")

    # ── Section 2: By Signal Type ─────────────────────────────────────────────
    print(f"\n{DIV}")
    print("SECTION 2 — By Signal Type")
    print(DIV)

    for t in ['BRK', 'REV', 'FADE', 'QBS']:
        ta = by_type(a, t)
        tb = by_type(b, t)
        print(f"\n  [{t}]")
        sta = pr(f"  v3.3c", ta)
        stb = pr(f"  v3.4",  tb)
        delta(f"v3.3c→v3.4", sta, stb)

    # REV split by direction
    print(f"\n  [REV — direction breakdown]")
    for d in ['bull', 'bear']:
        ta = [s for s in by_type(a, 'REV') if s.get('direction') == d]
        tb = [s for s in by_type(b, 'REV') if s.get('direction') == d]
        print(f"\n    {d.upper()} REV:")
        sta = pr(f"    v3.3c {d}", ta, width=20)
        stb = pr(f"    v3.4  {d}", tb, width=20)
        delta(f"{d}", sta, stb, width=20)

    # ── Section 3: NVDA Deep-Dive ─────────────────────────────────────────────
    print(f"\n{DIV}")
    print("SECTION 3 — NVDA Deep-Dive")
    print(DIV)

    nvda_a = by_sym(a, 'NVDA')
    nvda_b = by_sym(b, 'NVDA')

    if not nvda_a and not nvda_b:
        print("  No NVDA signals found (symbol may not be in log files).")
    else:
        for label, sigs in [("v3.3c", nvda_a), ("v3.4", nvda_b)]:
            print(f"\n  NVDA {label}:")
            bull_rev = [s for s in sigs if s.get('sig_type') == 'REV' and s.get('direction') == 'bull']
            bear_rev = [s for s in sigs if s.get('sig_type') == 'REV' and s.get('direction') == 'bear']
            pr(f"    Bull REV", bull_rev, width=16)
            pr(f"    Bear REV", bear_rev, width=16)
            pr(f"    All",      sigs,     width=16)

        nvda_br_a = [s for s in nvda_a if s.get('sig_type') == 'REV' and s.get('direction') == 'bull']
        nvda_br_b = [s for s in nvda_b if s.get('sig_type') == 'REV' and s.get('direction') == 'bull']
        cut = len(nvda_br_a) - len(nvda_br_b)
        net_a = sum(s.get('pnl_atr', 0) for s in nvda_br_a)
        net_b = sum(s.get('pnl_atr', 0) for s in nvda_br_b)
        print(f"\n  NVDA Bull REV removed: {cut} signals")
        print(f"  Net ATR impact: v3.3c={net_a:+.1f}  v3.4={net_b:+.1f}  Δ={net_b-net_a:+.1f}")

    # ── Section 4: New v3.4 Signals ───────────────────────────────────────────
    print(f"\n{DIV}")
    print("SECTION 4 — New v3.4 Signals")
    print(DIV)

    # New bull BRK at PD Last Hr High
    pdlh_kws = ['last hr', 'pdlasthr', 'pd lh', 'pd last', 'last hour']
    pdlh_a = [s for s in a if s.get('sig_type')=='BRK' and s.get('direction')=='bull'
              and any(k in s.get('levels','').lower() for k in pdlh_kws)]
    pdlh_b = [s for s in b if s.get('sig_type')=='BRK' and s.get('direction')=='bull'
              and any(k in s.get('levels','').lower() for k in pdlh_kws)]

    print(f"\n  [New: Bull BRK at PD Last Hr High]")
    pr("  v3.3c (baseline)", pdlh_a, width=24)
    pr("  v3.4  (new level)", pdlh_b, width=24)
    if pdlh_b:
        print("  By symbol (v3.4):")
        for sym in sorted(set(s['symbol'] for s in pdlh_b)):
            pr(f"    {sym}", [s for s in pdlh_b if s['symbol']==sym], width=12)

    # Bull REV at ORB L (re-enabled midday)
    orbl_a = [s for s in a if s.get('sig_type')=='REV' and s.get('direction')=='bull'
              and 'orb l' in s.get('levels','').lower()]
    orbl_b = [s for s in b if s.get('sig_type')=='REV' and s.get('direction')=='bull'
              and 'orb l' in s.get('levels','').lower()]

    print(f"\n  [Bull REV at ORB L (re-enabled midday)]")
    pr("  v3.3c", orbl_a, width=16)
    pr("  v3.4",  orbl_b, width=16)
    if orbl_b:
        print("  By symbol (v3.4):")
        for sym in sorted(set(s['symbol'] for s in orbl_b)):
            pr(f"    {sym}", [s for s in orbl_b if s['symbol']==sym], width=12)

    # ── Section 5: Signals Cut ────────────────────────────────────────────────
    print(f"\n{DIV}")
    print("SECTION 5 — Signals Cut (v3.3c > v3.4, by level)")
    print(DIV)

    def level_key(s):
        """Normalise level name for grouping."""
        # Levels field may be e.g. "PM L + Yest L" — use full string
        return (s.get('direction',''), s.get('sig_type',''), s.get('levels',''))

    from collections import Counter
    lc_a = defaultdict(list)
    lc_b = defaultdict(list)
    for s in a:
        lc_a[level_key(s)].append(s)
    for s in b:
        lc_b[level_key(s)].append(s)

    all_keys = set(lc_a.keys()) | set(lc_b.keys())

    header = f"  {'Level':<50} {'v3.3c':>7} {'v3.4':>5} {'Δ':>5} {'v3.3c Win%':>10} {'v3.4 Win%':>9} {'ΔNet':>8}  Flag"
    print(header)
    print(f"  {'-'*50} {'-'*7} {'-'*5} {'-'*5} {'-'*10} {'-'*9} {'-'*8}  ----")

    flags = []
    for key in sorted(all_keys):
        dir_, typ_, lvl_ = key
        if typ_ == 'RNG':
            continue
        sa_l = lc_a.get(key, [])
        sb_l = lc_b.get(key, [])
        na, nb = len(sa_l), len(sb_l)
        if na == 0 and nb == 0:
            continue
        win_a = (100*sum(1 for s in sa_l if s.get('outcome')=='WIN')/na) if na else 0
        win_b = (100*sum(1 for s in sb_l if s.get('outcome')=='WIN')/nb) if nb else 0
        net_a = sum(s.get('pnl_atr',0) for s in sa_l)
        net_b = sum(s.get('pnl_atr',0) for s in sb_l)
        d_net = net_b - net_a

        flag = ''
        if na > 0 and nb == 0:
            flag = 'REMOVED'
        elif na >= 5 and win_a > 55 and nb < na * 0.5:
            flag = 'SIG.DROP'

        if flag:
            flags.append((key, na, nb, win_a, win_b, d_net, flag))

        # Print rows with at least 3 total signals
        if na + nb >= 3:
            key_str = f"{dir_[0].upper()} {typ_} {lvl_}"[:50]
            print(f"  {key_str:<50} {na:>7} {nb:>5} {nb-na:>+5} "
                  f"{win_a:>9.1f}% {win_b:>8.1f}% {d_net:>+8.1f}  {flag}")

    if flags:
        print(f"\n  FLAGS:")
        for key, na, nb, win_a, win_b, d_net, flag in flags:
            dir_, typ_, lvl_ = key
            print(f"    [{flag}] {dir_} {typ_} '{lvl_}': "
                  f"v3.3c N={na} Win={win_a:.1f}%  →  v3.4 N={nb} Win={win_b:.1f}%  ΔNet={d_net:+.1f}")
    else:
        print("\n  No flags raised.")

    # ── Section 6: Symbol Breakdown ───────────────────────────────────────────
    print(f"\n{DIV}")
    print("SECTION 6 — Symbol Breakdown (excl. RNG)")
    print(DIV)

    all_symbols = sorted(set(s['symbol'] for s in a) | set(s['symbol'] for s in b))
    print(f"\n  {'Symbol':<10} {'v3.3c N':>7} {'v3.3c Net':>10} {'v3.4 N':>6} {'v3.4 Net':>9} {'Δ Net':>8}  Flag")
    print(f"  {'-'*10} {'-'*7} {'-'*10} {'-'*6} {'-'*9} {'-'*8}  ----")
    for sym in all_symbols:
        sa_s = by_sym(a, sym)
        sb_s = by_sym(b, sym)
        na   = len(sa_s)
        nb   = len(sb_s)
        neta = sum(s.get('pnl_atr',0) for s in sa_s)
        netb = sum(s.get('pnl_atr',0) for s in sb_s)
        dnet = netb - neta
        flag = 'DROP>20' if dnet < -20 else ''
        print(f"  {sym:<10} {na:>7} {neta:>+10.1f} {nb:>6} {netb:>+9.1f} {dnet:>+8.1f}  {flag}")

    # ── Appendix: Top levels sanity check ─────────────────────────────────────
    print(f"\n{DIV}")
    print("APPENDIX — Top Levels by Count (v3.4, sanity check)")
    print(DIV)
    from collections import Counter
    ctr = Counter(f"{s.get('direction','?')[0].upper()} {s.get('sig_type','?')} {s.get('levels','?')}" for s in b)
    for item, cnt in ctr.most_common(25):
        print(f"  {cnt:4d}  {item}")

    print(f"\n{DIV}")
    print("Done.")
    print(DIV)

if __name__ == '__main__':
    main()
