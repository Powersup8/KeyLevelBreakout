#!/usr/bin/env python3
"""
FADE & REV Deep-Dive Analysis for KLB v3.3
============================================
Investigates why FADE (-191.7 ATR) and REV (-389.3 ATR) are net negative
despite decent win rates (62.7% and 45.5% respectively).

Reuses data loading / parsing logic from v33_backtest.py.
"""

import sys
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ── Import everything from the backtest script ────────────────────────────────
# Rather than copy-pasting, we import directly.
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
import importlib.util

_bt_path = __import__('pathlib').Path(__file__).parent / 'v33_backtest.py'
_spec = importlib.util.spec_from_file_location('v33_backtest', _bt_path)
_bt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bt)

# Pull all we need
load_and_parse_logs = _bt.load_and_parse_logs
compute_dim_status  = _bt.compute_dim_status
load_1m             = _bt.load_1m
load_daily          = _bt.load_daily
compute_atr         = _bt.compute_atr
measure_mfe_mae     = _bt.measure_mfe_mae
sig_stats           = _bt.sig_stats
SYMBOLS             = _bt.SYMBOLS
BAR_DIR             = _bt.BAR_DIR


# ── Helpers ───────────────────────────────────────────────────────────────────

SEP = '─' * 72

def pct(n, d):
    return f"{n/d*100:.1f}%" if d else "N/A"

def fmt_sig(s, rank=None):
    ts = s.get('timestamp', '')
    if hasattr(ts, 'strftime'):
        ts = ts.strftime('%Y-%m-%d %H:%M')
    dim = f" DIM:{s.get('dim_reason')}" if s.get('is_dim') else ""
    prefix = f"#{rank:2d} " if rank is not None else "    "
    return (f"{prefix}{s.get('symbol','?'):5s} {ts} {s.get('sig_type','?'):5s} "
            f"{s.get('direction','?'):4s} {str(s.get('levels','?')):<24s} "
            f"vol={str(s.get('vol_ratio','?'))+'x':>6s}  "
            f"MFE={s.get('mfe_atr',0):7.3f}  MAE={s.get('mae_atr',0):7.3f}  "
            f"P&L={s.get('pnl_atr',0):+8.3f}  [{s.get('outcome','?'):4s}]{dim}")

def table_header(cols):
    hdr = "  ".join(f"{c[0]:<{c[1]}}" for c in cols)
    sep = "  ".join("─"*c[1] for c in cols)
    return hdr + "\n" + sep

def table_row(vals, cols):
    return "  ".join(f"{str(v):<{c[1]}}" for v, c in zip(vals, cols))

def breakdown(signals, key_fn, label, min_n=5):
    """Group signals by key_fn, print stats table."""
    groups = {}
    for s in signals:
        k = key_fn(s)
        groups.setdefault(k, []).append(s)

    rows = []
    for k, grp in groups.items():
        st = sig_stats(grp)
        rows.append((k, st['n'], st['win_rate'], st['avg_mfe'], st['avg_mae'],
                     st['avg_pnl'], st['net_atr']))
    rows.sort(key=lambda r: r[6])  # sort by net ATR ascending

    cols = [(label, 24), ('N', 5), ('Win%', 6), ('AvgMFE', 7), ('AvgMAE', 7),
            ('AvgP&L', 8), ('NetATR', 9)]
    print(table_header(cols))
    for r in rows:
        if r[1] < min_n:
            continue
        vals = [r[0], r[1], f"{r[2]:.1f}%", f"{r[3]:.3f}", f"{r[4]:.3f}",
                f"{r[5]:+.3f}", f"{r[6]:+.1f}"]
        print(table_row(vals, cols))

def time_bucket(s):
    try:
        h, m = map(int, s['time_str'].split(':'))
        if h < 10:
            return '09:30-09:59'
        elif h == 10:
            return '10:xx'
        elif h == 11:
            return '11:xx'
        elif h == 12:
            return '12:xx'
        elif h == 13:
            return '13:xx'
        elif h == 14:
            return '14:xx'
        else:
            return '15:xx'
    except:
        return 'unknown'

def asymmetry(signals, label):
    """Show winner vs loser size asymmetry."""
    wins  = [s for s in signals if s.get('outcome') == 'WIN']
    losses= [s for s in signals if s.get('outcome') == 'LOSS']
    flats = [s for s in signals if s.get('outcome') == 'FLAT']

    avg_win_mfe  = np.mean([s.get('mfe_atr',0) for s in wins])  if wins  else 0
    avg_loss_mae = np.mean([s.get('mae_atr',0) for s in losses]) if losses else 0
    avg_win_pnl  = np.mean([s.get('pnl_atr',0) for s in wins])  if wins  else 0
    avg_loss_pnl = np.mean([s.get('pnl_atr',0) for s in losses]) if losses else 0

    n = len(signals)
    print(f"  Total: {n}   WIN: {len(wins)} ({pct(len(wins),n)})   "
          f"LOSS: {len(losses)} ({pct(len(losses),n)})   FLAT: {len(flats)} ({pct(len(flats),n)})")
    print(f"  Avg winner  MFE:  {avg_win_mfe:+.3f} ATR   Avg winner  P&L: {avg_win_pnl:+.3f} ATR")
    print(f"  Avg loser   MAE:  {avg_loss_mae:+.3f} ATR   Avg loser   P&L: {avg_loss_pnl:+.3f} ATR")
    ratio = avg_loss_mae / avg_win_mfe if avg_win_mfe else float('inf')
    print(f"  Loss/Win ratio (MAE/MFE): {ratio:.2f}x  "
          f"{'BAD — losses much larger than wins' if ratio > 1.2 else 'OK'}")
    net = sum(s.get('pnl_atr',0) for s in signals)
    print(f"  Net ATR: {net:+.1f}")

def top_worst(signals, n=10, label=''):
    print(f"\n  --- Top {n} WORST ({label}) ---")
    worst = sorted(signals, key=lambda s: s.get('pnl_atr', 0))[:n]
    for i, s in enumerate(worst):
        print(fmt_sig(s, i+1))

def top_best(signals, n=10, label=''):
    print(f"\n  --- Top {n} BEST ({label}) ---")
    best = sorted(signals, key=lambda s: s.get('pnl_atr', 0), reverse=True)[:n]
    for i, s in enumerate(best):
        print(fmt_sig(s, i+1))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print('='*72)
    print('FADE & REV Deep-Dive — KLB v3.3')
    print('='*72)
    print()

    # ── 1. Load & parse v3.3 logs ─────────────────────────────────────────────
    print('Loading v3.3 Pine logs...')
    signals_v33, _ = load_and_parse_logs('v33')
    print(f'  {len(signals_v33)} signals parsed')

    print('Computing dim status...')
    signals_v33 = compute_dim_status(signals_v33)

    # ── 2. Load IB data & measure MFE/MAE ────────────────────────────────────
    symbols_seen = sorted(set(s['symbol'] for s in signals_v33))
    print(f'\nSymbols: {symbols_seen}')
    ib_cache = {}
    for sym in symbols_seen:
        print(f'  Loading {sym}...', end=' ', flush=True)
        try:
            bars = load_1m(sym)
            daily = load_daily(sym)
            atr_s = compute_atr(daily)
            ib_cache[sym] = (bars, atr_s)
            print(f'{len(bars)} 1m bars')
        except Exception as e:
            print(f'ERROR: {e}')

    print('\nMeasuring MFE/MAE...')
    for sym in symbols_seen:
        if sym not in ib_cache:
            continue
        bars, atr_s = ib_cache[sym]
        sigs = [s for s in signals_v33 if s['symbol'] == sym]
        measure_mfe_mae(sigs, bars, atr_s)
        matched = sum(1 for s in sigs if s.get('mfe_atr') is not None
                      and (s.get('mfe_atr',0) != 0 or s.get('mae_atr',0) != 0))
        print(f'  {sym}: {len(sigs)} signals, {matched} with data')

    # Filter to signals with outcome data
    all_sigs = [s for s in signals_v33 if s.get('outcome') is not None]
    fade_all = [s for s in all_sigs if s.get('sig_type') == 'FADE']
    rev_all  = [s for s in all_sigs if s.get('sig_type') == 'REV']
    brk_all  = [s for s in all_sigs if s.get('sig_type') == 'BRK']

    print(f'\nSignals with outcome: FADE={len(fade_all)}, REV={len(rev_all)}, BRK={len(brk_all)}')

    # ═══════════════════════════════════════════════════════════════════════════
    print('\n' + '='*72)
    print('SECTION 1 — BRK BASELINE (reference)')
    print('='*72)
    asymmetry(brk_all, 'BRK')

    # ═══════════════════════════════════════════════════════════════════════════
    print('\n' + '='*72)
    print('SECTION 2 — FADE DEEP-DIVE')
    print('='*72)

    print('\n[2.0] Overall FADE asymmetry')
    asymmetry(fade_all, 'FADE')

    print(f'\n[2.1] FADE by Symbol (min N=3)')
    breakdown(fade_all, lambda s: s.get('symbol','?'), 'Symbol', min_n=3)

    print(f'\n[2.2] FADE by Direction')
    breakdown(fade_all, lambda s: s.get('direction','?'), 'Direction', min_n=1)

    print(f'\n[2.3] FADE bull vs bear — asymmetry detail')
    fade_bull = [s for s in fade_all if s.get('direction') == 'bull']
    fade_bear = [s for s in fade_all if s.get('direction') == 'bear']
    print(f'  BULL FADE ({len(fade_bull)} signals):')
    asymmetry(fade_bull, 'FADE bull')
    print(f'  BEAR FADE ({len(fade_bear)} signals):')
    asymmetry(fade_bear, 'FADE bear')

    print(f'\n[2.4] FADE by Time of Day')
    breakdown(fade_all, time_bucket, 'Time', min_n=3)

    print(f'\n[2.5] FADE by Symbol+Direction (min N=3)')
    breakdown(fade_all, lambda s: f"{s.get('symbol','?')} {s.get('direction','?')}",
              'Sym+Dir', min_n=3)

    print(f'\n[2.6] FADE by Time+Direction (min N=3)')
    breakdown(fade_all, lambda s: f"{time_bucket(s)} {s.get('direction','?')}",
              'Time+Dir', min_n=3)

    print(f'\n[2.7] FADE Dimmed vs Not Dimmed')
    breakdown(fade_all, lambda s: 'Dimmed' if s.get('is_dim') else 'Not Dimmed',
              'Dim Status', min_n=1)

    top_worst(fade_all, 10, 'FADE')
    top_best(fade_all, 10, 'FADE')

    # NVDA-only FADE
    nvda_fade = [s for s in fade_all if s.get('symbol') == 'NVDA']
    non_nvda_fade = [s for s in fade_all if s.get('symbol') != 'NVDA']
    print(f'\n[2.8] FADE: NVDA vs Everyone Else')
    print(f'  NVDA FADE ({len(nvda_fade)} signals):')
    asymmetry(nvda_fade, 'NVDA FADE')
    print(f'  Non-NVDA FADE ({len(non_nvda_fade)} signals):')
    asymmetry(non_nvda_fade, 'Non-NVDA FADE')

    print(f'\n[2.9] Non-NVDA FADE by Symbol (min N=3)')
    breakdown(non_nvda_fade, lambda s: s.get('symbol','?'), 'Symbol', min_n=3)

    print(f'\n[2.10] Non-NVDA FADE by Direction')
    breakdown(non_nvda_fade, lambda s: s.get('direction','?'), 'Direction', min_n=1)

    top_worst(non_nvda_fade, 10, 'Non-NVDA FADE')

    # ═══════════════════════════════════════════════════════════════════════════
    print('\n' + '='*72)
    print('SECTION 3 — REV DEEP-DIVE')
    print('='*72)

    print('\n[3.0] Overall REV asymmetry')
    asymmetry(rev_all, 'REV')

    print(f'\n[3.1] REV by Symbol (min N=10)')
    breakdown(rev_all, lambda s: s.get('symbol','?'), 'Symbol', min_n=10)

    print(f'\n[3.2] REV by Direction')
    breakdown(rev_all, lambda s: s.get('direction','?'), 'Direction', min_n=1)

    print(f'\n[3.3] REV bull vs bear — asymmetry detail')
    rev_bull = [s for s in rev_all if s.get('direction') == 'bull']
    rev_bear = [s for s in rev_all if s.get('direction') == 'bear']
    print(f'  BULL REV ({len(rev_bull)} signals):')
    asymmetry(rev_bull, 'REV bull')
    print(f'  BEAR REV ({len(rev_bear)} signals):')
    asymmetry(rev_bear, 'REV bear')

    print(f'\n[3.4] REV by Time of Day')
    breakdown(rev_all, time_bucket, 'Time', min_n=10)

    print(f'\n[3.5] REV by Level Type (top 20, min N=10)')
    breakdown(rev_all, lambda s: s.get('levels','?'), 'Level', min_n=10)

    print(f'\n[3.6] REV by EMA Alignment')
    breakdown(rev_all, lambda s: s.get('ema','?'), 'EMA', min_n=1)

    print(f'\n[3.7] REV Dimmed vs Not Dimmed')
    breakdown(rev_all, lambda s: 'Dimmed' if s.get('is_dim') else 'Not Dimmed',
              'Dim Status', min_n=1)

    print(f'\n[3.8] REV by Dim Reason (min N=5)')
    breakdown(rev_all, lambda s: s.get('dim_reason') or 'none', 'Dim Reason', min_n=5)

    print(f'\n[3.9] REV by Symbol+Direction (min N=10)')
    breakdown(rev_all, lambda s: f"{s.get('symbol','?')} {s.get('direction','?')}",
              'Sym+Dir', min_n=10)

    print(f'\n[3.10] REV by Level+Direction (min N=10)')
    breakdown(rev_all, lambda s: f"{s.get('levels','?')[:20]} {s.get('direction','?')}",
              'Level+Dir', min_n=10)

    print(f'\n[3.11] REV Counter-EMA vs With-EMA')
    breakdown(rev_all, lambda s: 'counter_ema' if s.get('is_counter_ema') else 'with_ema',
              'EMA Gate', min_n=1)

    top_worst(rev_all, 10, 'REV')
    top_best(rev_all, 10, 'REV')

    # NVDA-only REV
    nvda_rev = [s for s in rev_all if s.get('symbol') == 'NVDA']
    non_nvda_rev = [s for s in rev_all if s.get('symbol') != 'NVDA']
    print(f'\n[3.12] REV: NVDA vs Everyone Else')
    print(f'  NVDA REV ({len(nvda_rev)} signals):')
    asymmetry(nvda_rev, 'NVDA REV')
    print(f'  Non-NVDA REV ({len(non_nvda_rev)} signals):')
    asymmetry(non_nvda_rev, 'Non-NVDA REV')

    print(f'\n[3.13] Non-NVDA REV by Symbol (min N=10)')
    breakdown(non_nvda_rev, lambda s: s.get('symbol','?'), 'Symbol', min_n=10)

    print(f'\n[3.14] Non-NVDA REV — asymmetry')
    asymmetry(non_nvda_rev, 'Non-NVDA REV')

    print(f'\n[3.15] Non-NVDA REV by Level (min N=10)')
    breakdown(non_nvda_rev, lambda s: s.get('levels','?'), 'Level', min_n=10)

    print(f'\n[3.16] Non-NVDA REV by Time')
    breakdown(non_nvda_rev, time_bucket, 'Time', min_n=10)

    # ═══════════════════════════════════════════════════════════════════════════
    print('\n' + '='*72)
    print('SECTION 4 — WHAT IF WE FILTERED NVDA FROM FADE+REV?')
    print('='*72)
    fade_no_nvda = [s for s in fade_all if s.get('symbol') != 'NVDA']
    rev_no_nvda  = [s for s in rev_all  if s.get('symbol') != 'NVDA']
    all_no_nvda  = [s for s in all_sigs if s.get('symbol') != 'NVDA']

    print(f'\nAll signals (excl. NVDA):')
    asymmetry(all_no_nvda, 'All excl NVDA')
    print(f'\nFADE (excl. NVDA) — {len(fade_no_nvda)} signals:')
    asymmetry(fade_no_nvda, 'FADE excl NVDA')
    print(f'\nREV (excl. NVDA) — {len(rev_no_nvda)} signals:')
    asymmetry(rev_no_nvda, 'REV excl NVDA')

    # ═══════════════════════════════════════════════════════════════════════════
    print('\n' + '='*72)
    print('SECTION 5 — SPECIFIC PROBLEM PATTERNS')
    print('='*72)

    # Bull FADE detailed — this is catastrophic per results
    fade_bull_nvda = [s for s in fade_all if s.get('direction') == 'bull' and s.get('symbol') == 'NVDA']
    fade_bull_nonvda = [s for s in fade_all if s.get('direction') == 'bull' and s.get('symbol') != 'NVDA']
    print(f'\n[5.1] Bull FADE by Symbol')
    breakdown([s for s in fade_all if s.get('direction') == 'bull'],
              lambda s: s.get('symbol','?'), 'Symbol', min_n=1)

    print(f'\n[5.2] Bear FADE by Symbol')
    breakdown([s for s in fade_all if s.get('direction') == 'bear'],
              lambda s: s.get('symbol','?'), 'Symbol', min_n=1)

    print(f'\n[5.3] REV bull PM H level (known loser from results)')
    rev_pmh_bull = [s for s in rev_all if 'PM H' in str(s.get('levels',''))
                    and s.get('direction') == 'bull']
    rev_pmh_bear = [s for s in rev_all if 'PM H' in str(s.get('levels',''))
                    and s.get('direction') == 'bear']
    print(f'  REV PM H bull ({len(rev_pmh_bull)} signals):')
    if rev_pmh_bull:
        asymmetry(rev_pmh_bull, 'REV PM H bull')
    print(f'  REV PM H bear ({len(rev_pmh_bear)} signals):')
    if rev_pmh_bear:
        asymmetry(rev_pmh_bear, 'REV PM H bear')

    print(f'\n[5.4] REV ORB H level (worst level from results: -27.5 ATR)')
    rev_orbh = [s for s in rev_all if s.get('levels','') == 'ORB H']
    print(f'  REV ORB H ({len(rev_orbh)} signals):')
    if rev_orbh:
        asymmetry(rev_orbh, 'REV ORB H')
        breakdown(rev_orbh, lambda s: s.get('direction','?'), 'Direction', min_n=1)

    print(f'\n[5.5] REV VWAP (best level: +89.9 ATR)')
    rev_vwap = [s for s in rev_all if s.get('levels','') == 'VWAP']
    print(f'  REV VWAP ({len(rev_vwap)} signals):')
    if rev_vwap:
        asymmetry(rev_vwap, 'REV VWAP')
        breakdown(rev_vwap, lambda s: s.get('direction','?'), 'Direction', min_n=1)

    print(f'\n[5.6] REV VWAP+PM H (worst combo: -69.3 ATR)')
    rev_vwap_pmh = [s for s in rev_all if 'VWAP' in str(s.get('levels',''))
                    and 'PM H' in str(s.get('levels',''))]
    print(f'  REV VWAP+PM H ({len(rev_vwap_pmh)} signals):')
    if rev_vwap_pmh:
        asymmetry(rev_vwap_pmh, 'REV VWAP+PM H')
        breakdown(rev_vwap_pmh, lambda s: s.get('direction','?'), 'Direction', min_n=1)
        top_worst(rev_vwap_pmh, 5, 'REV VWAP+PM H')

    print(f'\n[5.7] REV by vol range quartiles')
    rev_with_vol = [s for s in rev_all if s.get('vol_ratio') is not None]
    if rev_with_vol:
        vols = [s.get('vol_ratio',1) for s in rev_with_vol]
        p25, p50, p75 = np.percentile(vols, [25,50,75])
        def vol_bucket(s):
            v = s.get('vol_ratio',1)
            if v <= p25:  return f'<={p25:.1f}x (Q1)'
            elif v <= p50: return f'<={p50:.1f}x (Q2)'
            elif v <= p75: return f'<={p75:.1f}x (Q3)'
            else:           return f'>{p75:.1f}x (Q4)'
        print(f'  Vol quartiles: Q1<={p25:.1f}x, Q2<={p50:.1f}x, Q3<={p75:.1f}x')
        breakdown(rev_with_vol, vol_bucket, 'Vol Bucket', min_n=5)

    # ═══════════════════════════════════════════════════════════════════════════
    print('\n' + '='*72)
    print('SECTION 6 — ACTIONABLE SUMMARY')
    print('='*72)

    # Compute key stats for summary
    st_fade = sig_stats(fade_all)
    st_rev  = sig_stats(rev_all)
    st_brk  = sig_stats(brk_all)
    st_fade_nvda = sig_stats(nvda_fade)
    st_fade_nonnvda = sig_stats(non_nvda_fade)
    st_rev_nvda  = sig_stats(nvda_rev)
    st_rev_nonnvda = sig_stats(non_nvda_rev)

    fade_bull_st = sig_stats([s for s in fade_all if s.get('direction')=='bull'])
    fade_bear_st = sig_stats([s for s in fade_all if s.get('direction')=='bear'])
    rev_bull_st  = sig_stats([s for s in rev_all  if s.get('direction')=='bull'])
    rev_bear_st  = sig_stats([s for s in rev_all  if s.get('direction')=='bear'])

    print(f"""
FADE Summary ({st_fade['n']} signals, {st_fade['win_rate']:.1f}% win, {st_fade['net_atr']:+.1f} ATR):
  Bull FADE: {fade_bull_st['n']} signals, {fade_bull_st['win_rate']:.1f}% win, {fade_bull_st['net_atr']:+.1f} ATR
  Bear FADE: {fade_bear_st['n']} signals, {fade_bear_st['win_rate']:.1f}% win, {fade_bear_st['net_atr']:+.1f} ATR
  NVDA FADE: {st_fade_nvda['n']} signals, {st_fade_nvda['win_rate']:.1f}% win, {st_fade_nvda['net_atr']:+.1f} ATR
  Non-NVDA:  {st_fade_nonnvda['n']} signals, {st_fade_nonnvda['win_rate']:.1f}% win, {st_fade_nonnvda['net_atr']:+.1f} ATR

REV Summary ({st_rev['n']} signals, {st_rev['win_rate']:.1f}% win, {st_rev['net_atr']:+.1f} ATR):
  Bull REV:  {rev_bull_st['n']} signals, {rev_bull_st['win_rate']:.1f}% win, {rev_bull_st['net_atr']:+.1f} ATR
  Bear REV:  {rev_bear_st['n']} signals, {rev_bear_st['win_rate']:.1f}% win, {rev_bear_st['net_atr']:+.1f} ATR
  NVDA REV:  {st_rev_nvda['n']} signals, {st_rev_nvda['win_rate']:.1f}% win, {st_rev_nvda['net_atr']:+.1f} ATR
  Non-NVDA:  {st_rev_nonnvda['n']} signals, {st_rev_nonnvda['win_rate']:.1f}% win, {st_rev_nonnvda['net_atr']:+.1f} ATR

BRK reference ({st_brk['n']} signals, {st_brk['win_rate']:.1f}% win, {st_brk['net_atr']:+.1f} ATR)
""")

    print('Done.')


if __name__ == '__main__':
    main()
