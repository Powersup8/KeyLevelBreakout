#!/usr/bin/env python3
"""
KLB HQ Signal Research — Deep Analysis of High-Quality Winning Signals
=======================================================================
Loads v3.3c signals, measures MFE/MAE, defines HQ signals as
  WIN and mfe_atr >= 0.25 ATR
and runs 7 analytical sections on that universe.

Sections:
  1. HQ signal universe profile
  2. Entry quality factors (vol_ratio, range_atr, body_pct, ramp, etc.)
  3. Context factors (fingerprint match: daily_atr_consumed, level_tests, etc.)
  4. Hold optimisation for HQ signals (P&L path + peak distribution)
  5. Symbol-specific profiles (top 5 symbols by HQ count)
  6. Multi-angle improvement assessment (A-H)
  7. VERDICT — top 3 improvements

Usage:  python3 debug/hq_signal_research.py
Output: debug/hq_signal_research_results.txt (and console)
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

# ── Import shared infrastructure ─────────────────────────────────────────────
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

# ── Config ────────────────────────────────────────────────────────────────────
V33C_GLOB      = 'pine-logs-Key Level Breakout v3.3c_*.csv'
HIGH_LEVEL_KW  = ['PM H', 'ORB H', 'Yest H', 'Week H']
HQ_MFE_THRESH  = 0.25    # ATR — HQ = WIN + mfe >= 0.25 ATR
WIN_MFE_THRESH = 0.10    # ATR — used for MFE/MAE measurement (same as backtest)
FORWARD_MINS   = 60
CHECKPOINTS    = [10, 20, 30, 45, 60]
FP_MATCH_MINS  = 5       # fingerprint match window ±5 min

CATALOG_PATH      = LOG_DIR / 'move-catalog.parquet'
FINGERPRINT_PATH  = LOG_DIR / 'move-fingerprints.parquet'
OUT_PATH          = LOG_DIR / 'hq_signal_research_results.txt'

DIVIDER = '=' * 76
SUBDIV  = '-' * 76

# ── Helpers ───────────────────────────────────────────────────────────────────

def is_bull_rev_at_high(sig):
    if sig.get('direction') != 'bull':
        return False
    if 'REV' not in sig.get('sig_type', ''):
        return False
    return any(kw in sig.get('levels', '') for kw in HIGH_LEVEL_KW)


def classify_tod(ts):
    t = ts.time() if hasattr(ts, 'time') else ts
    if isinstance(t, pd.Timestamp):
        t = t.time()
    if dtime(9, 30) <= t < dtime(11, 0):
        return 'morning'
    elif dtime(11, 0) <= t < dtime(14, 0):
        return 'midday'
    return 'afternoon'


def classify_tier(mfe_atr):
    if mfe_atr >= 0.60:
        return 'S'
    elif mfe_atr >= 0.40:
        return 'A'
    return 'B'


def effect_label(delta):
    """Label effect size (in ATR units)."""
    a = abs(delta)
    if a >= 0.10:
        return '***'
    elif a >= 0.05:
        return '**'
    elif a >= 0.02:
        return '*'
    return '.'


def fmt(val, fmt_spec='.3f'):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return 'n/a'
    return format(val, fmt_spec)


# ── Step 1: Load v3.3c signals ────────────────────────────────────────────────

def load_v33c_signals():
    files = sorted(glob.glob(str(LOG_DIR / V33C_GLOB)))
    print(f'  Found {len(files)} v3.3c log files')
    all_signals = []
    for fp in files:
        short   = Path(fp).name.split('_')[-1].replace('.csv', '')
        signals = parse_pine_log(fp)
        if not signals:
            continue
        symbol = identify_symbol(signals)
        if symbol is None:
            continue
        for s in signals:
            s['symbol']   = symbol
            s['version']  = 'v33c'
            s['log_file'] = short
        all_signals.extend(signals)
        print(f'    {short}: {symbol} — {len(signals)} signals')
    return all_signals


# ── Step 2: Measure MFE/MAE and build P&L paths ──────────────────────────────

def measure_and_build(signals, ib_cache):
    """
    For each signal: measure mfe_atr, mae_atr, outcome.
    Then build P&L path at CHECKPOINTS for signals with data.
    Returns enriched list of dicts (one per signal).
    """
    enriched = []

    for sig in signals:
        sym = sig['symbol']
        if sym not in ib_cache:
            continue
        bars_1m, atr_ser = ib_cache[sym]

        ts = sig['timestamp']
        sig_date = ts.date() if hasattr(ts, 'date') else pd.Timestamp(ts).date()

        atr_val = sig.get('atr')
        if not atr_val:
            atr_val = atr_ser.get(sig_date)
        if not atr_val or atr_val == 0:
            continue

        entry = sig.get('close')
        if entry is None:
            continue

        # Timezone normalise
        if ts.tzinfo is None:
            ts_et = pd.Timestamp(ts, tz='US/Eastern')
        else:
            ts_et = ts.tz_convert('US/Eastern')

        start_time = ts_et + pd.Timedelta(minutes=1)
        eod        = ts_et.normalize() + pd.Timedelta(hours=16)
        end_time   = min(ts_et + pd.Timedelta(minutes=FORWARD_MINS), eod)

        mask = (bars_1m.index >= start_time) & (bars_1m.index <= end_time)
        fwd  = bars_1m[mask]
        if len(fwd) == 0:
            continue

        direction = sig['direction']
        if direction == 'bull':
            fav = fwd['high'] - entry
            adv = entry - fwd['low']
        else:
            fav = entry - fwd['low']
            adv = fwd['high'] - entry

        mfe     = max(0, fav.max())
        mae     = max(0, adv.max())
        mfe_atr = mfe / atr_val
        mae_atr = mae / atr_val

        if mfe_atr >= WIN_MFE_THRESH and mfe > mae:
            outcome = 'WIN'
        elif mae_atr > mfe_atr and mae_atr >= WIN_MFE_THRESH:
            outcome = 'LOSS'
        else:
            outcome = 'FLAT'

        # Build P&L path using close prices
        if direction == 'bull':
            pnl_series = (fwd['close'] - entry) / atr_val
        else:
            pnl_series = (entry - fwd['close']) / atr_val

        minutes_arr = ((fwd.index - start_time).total_seconds() / 60).astype(int).values + 1
        pnl_arr     = pnl_series.values

        path = {}
        for cp in CHECKPOINTS:
            idxs = np.where(minutes_arr <= cp)[0]
            path[f'pnl_{cp}m'] = float(pnl_arr[idxs[-1]]) if len(idxs) > 0 else float(pnl_arr[-1])

        peak_pos          = int(np.argmax(pnl_arr))
        path['pnl_peak']  = float(pnl_arr[peak_pos])
        path['peak_min']  = int(minutes_arr[peak_pos])
        path['pnl_60m']   = float(pnl_arr[-1])
        path['pnl_decay'] = path['pnl_peak'] - path['pnl_60m']

        # Partial-exit simulation (50% at 20m, 50% at 60m)
        path['partial_20_60'] = 0.5 * path['pnl_20m'] + 0.5 * path['pnl_60m']

        # Parse time string from signal
        ts_parts = sig.get('time_str', '12:00').split(':')
        try:
            sig_hour = int(ts_parts[0])
            sig_min  = int(ts_parts[1]) if len(ts_parts) > 1 else 0
        except Exception:
            sig_hour, sig_min = 12, 0

        row = {
            'symbol'       : sym,
            'timestamp'    : ts,
            'ts_et'        : ts_et,
            'sig_type'     : sig.get('sig_type', '?'),
            'direction'    : direction,
            'levels'       : sig.get('levels', ''),
            'mfe_atr'      : mfe_atr,
            'mae_atr'      : mae_atr,
            'pnl_atr'      : mfe_atr - mae_atr,
            'outcome'      : outcome,
            'atr'          : atr_val,
            'entry'        : entry,
            'vol_ratio'    : sig.get('vol_ratio'),
            'range_atr'    : sig.get('range_atr'),
            'body_pct'     : sig.get('body_pct'),
            'ramp'         : sig.get('ramp'),
            'close_pos'    : sig.get('close_pos', ''),
            'ema'          : sig.get('ema'),
            'vwap'         : sig.get('vwap'),
            'is_vol_drying': sig.get('is_vol_drying', False),
            'is_big_move'  : sig.get('is_big_move', False),
            'is_dim'       : sig.get('is_dim', False),
            'sig_hour'     : sig_hour,
            'sig_min'      : sig_min,
            'tod'          : classify_tod(ts_et),
            'tier'         : classify_tier(mfe_atr),
        }
        row.update(path)
        enriched.append(row)

    return pd.DataFrame(enriched)


# ── Section helpers ───────────────────────────────────────────────────────────

def group_stats(df, col, label='', bins=None, labels=None, n_min=5):
    """
    Show avg MFE by group. Returns list of (group_label, N, avg_mfe).
    """
    rows = []
    if bins:
        col_cut = pd.cut(df[col], bins=bins, labels=labels)
        groups  = col_cut.dropna().unique()
        for g in labels:
            sub = df[col_cut == g]
            if len(sub) >= n_min:
                rows.append((str(g), len(sub), sub['mfe_atr'].mean()))
    else:
        for g, sub in df.groupby(col):
            if len(sub) >= n_min:
                rows.append((str(g), len(sub), sub['mfe_atr'].mean()))
    return rows


def factor_effect(hq, col, split_val=None, bins=None, labels=None,
                  use_flag=False, n_min=10):
    """
    For a single factor compute: high group avg MFE vs low group avg MFE.
    Returns dict with keys: low_n, low_mfe, high_n, high_mfe, delta, effect
    """
    valid = hq[hq[col].notna()].copy()
    if len(valid) < n_min * 2:
        return None

    if use_flag:
        lo = valid[~valid[col]]
        hi = valid[valid[col]]
    elif split_val is not None:
        lo = valid[valid[col] <= split_val]
        hi = valid[valid[col] > split_val]
    elif bins is not None:
        cuts = pd.cut(valid[col], bins=bins, labels=labels)
        lo   = valid[cuts == labels[0]]
        hi   = valid[cuts == labels[-1]]
    else:
        med  = valid[col].median()
        lo   = valid[valid[col] <= med]
        hi   = valid[valid[col] > med]

    if len(lo) < n_min or len(hi) < n_min:
        return None

    return {
        'low_n'  : len(lo),
        'low_mfe': lo['mfe_atr'].mean(),
        'high_n' : len(hi),
        'high_mfe': hi['mfe_atr'].mean(),
        'delta'  : hi['mfe_atr'].mean() - lo['mfe_atr'].mean(),
    }


def pnl_path_row(sub, label):
    n = len(sub)
    if n == 0:
        return f'  {label:<30}  N=0'
    avgs = {cp: sub[f'pnl_{cp}m'].mean() for cp in CHECKPOINTS}
    return (f'  {label:<30}  N={n:>4}  '
            + '  '.join(f'@{cp}m={avgs[cp]:+.3f}' for cp in CHECKPOINTS)
            + f'  peak={sub["pnl_peak"].mean():.3f}@{sub["peak_min"].mean():.0f}m')


def peak_dist(sub, label, indent='  '):
    n = len(sub)
    if n == 0:
        return
    buckets = [(0, 10), (10, 20), (20, 30), (30, 45), (45, 60)]
    print(f'{indent}{label} (N={n}):')
    cumul = 0
    for lo, hi in buckets:
        cnt = ((sub['peak_min'] > lo) & (sub['peak_min'] <= hi)).sum()
        pct = cnt / n * 100
        cumul += pct
        bar = '█' * int(pct / 3)
        print(f'{indent}  {lo:>2}-{hi:>2}m: {cnt:>3} ({pct:>5.1f}%) cumul={cumul:>5.1f}% {bar}')
    for t in [20, 30]:
        pct = (sub['peak_min'] <= t).mean() * 100
        print(f'{indent}  Peaked by {t}m: {pct:.1f}%')


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    output_lines = []

    class Tee:
        def write(self, s):
            sys.__stdout__.write(s)
            output_lines.append(s)
        def flush(self):
            sys.__stdout__.flush()

    sys.stdout = Tee()

    print(DIVIDER)
    print('KLB HQ Signal Research — Deep Analysis of Winning Signals')
    print(f'HQ definition: WIN + mfe_atr >= {HQ_MFE_THRESH} ATR  |  v3.3c logs  |  60m window')
    print(DIVIDER)
    print()

    # ── Load signals ──────────────────────────────────────────────────────────
    print('Loading v3.3c pine logs...')
    all_raw = load_v33c_signals()
    print(f'  Total raw: {len(all_raw)}')
    # Apply v3.3c suppression
    signals = [s for s in all_raw if not is_bull_rev_at_high(s)]
    print(f'  After suppression: {len(signals)}')
    print()

    # ── Load IB data ─────────────────────────────────────────────────────────
    print('Loading IB 1m data...')
    ib_cache = {}
    for sym in sorted(set(s['symbol'] for s in signals)):
        try:
            bars_1m  = load_1m(sym)
            daily_df = load_daily(sym)
            atr_ser  = compute_atr(daily_df)
            ib_cache[sym] = (bars_1m, atr_ser)
            print(f'  {sym}: {len(bars_1m)} bars')
        except Exception as e:
            print(f'  {sym}: ERROR {e}')
    print()

    # ── Measure MFE/MAE and build enriched DataFrame ──────────────────────────
    print('Measuring MFE/MAE and building P&L paths...')
    df = measure_and_build(signals, ib_cache)
    print(f'  Total signals with data: {len(df)}')

    # HQ filter
    hq = df[(df['outcome'] == 'WIN') & (df['mfe_atr'] >= HQ_MFE_THRESH)].copy()
    print(f'  HQ signals (WIN + mfe >= {HQ_MFE_THRESH}): {len(hq)}')
    print()

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1: HQ Signal Universe
    # ══════════════════════════════════════════════════════════════════════════
    print(DIVIDER)
    print('SECTION 1 — HQ SIGNAL UNIVERSE')
    print(SUBDIV)

    total_with_data = len(df)
    n_win  = (df['outcome'] == 'WIN').sum()
    n_hq   = len(hq)
    print(f'  Total signals with MFE/MAE data: {total_with_data}')
    print(f'  Winning signals (mfe >= 0.10):   {n_win} ({n_win/total_with_data*100:.1f}%)')
    print(f'  HQ signals (WIN + mfe >= 0.25):  {n_hq} ({n_hq/total_with_data*100:.1f}%)')
    print()

    # By signal type
    print('  By signal type:')
    hdr = f"  {'Type':<10} {'N':>5} {'% of HQ':>8} {'Avg MFE':>9} {'Avg MAE':>9} {'Avg P&L':>9}"
    print(hdr)
    print('  ' + '-' * (len(hdr) - 2))
    for stype, sub in hq.groupby('sig_type'):
        pct = len(sub) / n_hq * 100
        print(f"  {stype:<10} {len(sub):>5} {pct:>7.1f}%"
              f"  {sub['mfe_atr'].mean():>8.3f}"
              f"  {sub['mae_atr'].mean():>8.3f}"
              f"  {sub['pnl_atr'].mean():>8.3f}")

    # By symbol
    print()
    print('  By symbol (sorted by HQ count):')
    hdr = f"  {'Symbol':<7} {'N':>5} {'% of HQ':>8} {'Avg MFE':>9} {'Best type':<10}"
    print(hdr)
    print('  ' + '-' * (len(hdr) - 2))
    sym_counts = hq.groupby('symbol').size().sort_values(ascending=False)
    for sym in sym_counts.index:
        sub  = hq[hq['symbol'] == sym]
        pct  = len(sub) / n_hq * 100
        best_type = sub.groupby('sig_type')['mfe_atr'].mean().idxmax() if len(sub) > 0 else '?'
        print(f"  {sym:<7} {len(sub):>5} {pct:>7.1f}%"
              f"  {sub['mfe_atr'].mean():>8.3f}"
              f"  {best_type}")

    # By time of day
    print()
    print('  By time of day:')
    for tod in ['morning', 'midday', 'afternoon']:
        sub = hq[hq['tod'] == tod]
        print(f"  {tod:<12} N={len(sub):>4}  avg MFE={sub['mfe_atr'].mean():.3f}  "
              f"avg peak@{sub['peak_min'].mean():.0f}m")

    # Top 20 individual monsters by MFE
    print()
    print('  Top 20 individual HQ signals by MFE (the monsters):')
    hdr = f"  {'#':<3} {'Symbol':<7} {'Date/Time':<20} {'Type':<8} {'Dir':<5} {'MFE':>7} {'MAE':>7} {'Peak@':>7} {'Levels'}"
    print(hdr)
    print('  ' + '-' * (len(hdr) - 2))
    top20 = hq.nlargest(20, 'mfe_atr')
    for i, (_, row) in enumerate(top20.iterrows(), 1):
        ts_str = row['ts_et'].strftime('%Y-%m-%d %H:%M') if hasattr(row['ts_et'], 'strftime') else str(row['timestamp'])
        print(f"  {i:<3} {row['symbol']:<7} {ts_str:<20} {row['sig_type']:<8} "
              f"{row['direction']:<5} {row['mfe_atr']:>6.3f}  {row['mae_atr']:>6.3f}"
              f"  {row['peak_min']:>5}m  {str(row['levels'])[:40]}")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2: Entry Quality Factors
    # ══════════════════════════════════════════════════════════════════════════
    print()
    print(DIVIDER)
    print('SECTION 2 — ENTRY QUALITY FACTORS (on HQ signals)')
    print(SUBDIV)
    print('  Effect = high_group_avg_mfe - low_group_avg_mfe  (* p<0.05 proxy)')
    print()

    factors = []

    # vol_ratio quartiles
    vr = hq['vol_ratio'].dropna()
    if len(vr) >= 20:
        q25, q75 = vr.quantile(0.25), vr.quantile(0.75)
        lo_v = hq[hq['vol_ratio'] <= q25]
        hi_v = hq[hq['vol_ratio'] > q75]
        delta_v = hi_v['mfe_atr'].mean() - lo_v['mfe_atr'].mean()
        factors.append(('vol_ratio (Q4 vs Q1)', len(lo_v), lo_v['mfe_atr'].mean(),
                        len(hi_v), hi_v['mfe_atr'].mean(), delta_v,
                        f'Q1<={q25:.1f}x vs Q4>{q75:.1f}x'))

    # range_atr (trigger bar size)
    ra = hq['range_atr'].dropna()
    if len(ra) >= 20:
        med_ra = ra.median()
        lo_r = hq[hq['range_atr'] <= med_ra]
        hi_r = hq[hq['range_atr'] > med_ra]
        delta_r = hi_r['mfe_atr'].mean() - lo_r['mfe_atr'].mean()
        factors.append(('range_atr (large vs small)', len(lo_r), lo_r['mfe_atr'].mean(),
                        len(hi_r), hi_r['mfe_atr'].mean(), delta_r,
                        f'split at median={med_ra:.2f}'))

    # body_pct
    bp = hq['body_pct'].dropna()
    if len(bp) >= 20:
        med_bp = bp.median()
        lo_b = hq[hq['body_pct'] <= med_bp]
        hi_b = hq[hq['body_pct'] > med_bp]
        delta_b = hi_b['mfe_atr'].mean() - lo_b['mfe_atr'].mean()
        factors.append(('body_pct (high vs low)', len(lo_b), lo_b['mfe_atr'].mean(),
                        len(hi_b), hi_b['mfe_atr'].mean(), delta_b,
                        f'split at median={med_bp:.0f}%'))

    # ramp (vol acceleration)
    rp = hq['ramp'].dropna()
    if len(rp) >= 20:
        med_rp = rp.median()
        lo_rp = hq[hq['ramp'] <= med_rp]
        hi_rp = hq[hq['ramp'] > med_rp]
        delta_rp = hi_rp['mfe_atr'].mean() - lo_rp['mfe_atr'].mean()
        factors.append(('ramp/vol_accel (high vs low)', len(lo_rp), lo_rp['mfe_atr'].mean(),
                        len(hi_rp), hi_rp['mfe_atr'].mean(), delta_rp,
                        f'split at median={med_rp:.2f}x'))

    # close_pos (distance from level — parse ^ prefix)
    def parse_pos_pct(pos):
        try:
            return float(str(pos).lstrip('^v'))
        except Exception:
            return None
    if 'close_pos' in hq.columns:
        hq = hq.copy()
        hq['pos_pct'] = hq['close_pos'].apply(parse_pos_pct)
        pp = hq['pos_pct'].dropna()
        if len(pp) >= 20:
            med_pp = pp.median()
            lo_pp = hq[hq['pos_pct'] <= med_pp]
            hi_pp = hq[hq['pos_pct'] > med_pp]
            delta_pp = hi_pp['mfe_atr'].mean() - lo_pp['mfe_atr'].mean()
            factors.append(('close_pos (far vs close)', len(lo_pp), lo_pp['mfe_atr'].mean(),
                            len(hi_pp), hi_pp['mfe_atr'].mean(), delta_pp,
                            f'split at median pos={med_pp:.0f}%'))

    # EMA alignment
    ema_valid = hq[hq['ema'].notna() & (hq['ema'] != 'na')]
    if len(ema_valid) >= 20:
        ema_align = ema_valid[
            ((ema_valid['direction'] == 'bull') & (ema_valid['ema'] == 'bull')) |
            ((ema_valid['direction'] == 'bear') & (ema_valid['ema'] == 'bear'))
        ]
        ema_mis = ema_valid[~ema_valid.index.isin(ema_align.index)]
        if len(ema_align) >= 5 and len(ema_mis) >= 5:
            delta_ema = ema_align['mfe_atr'].mean() - ema_mis['mfe_atr'].mean()
            factors.append(('ema_aligned vs misaligned', len(ema_mis), ema_mis['mfe_atr'].mean(),
                            len(ema_align), ema_align['mfe_atr'].mean(), delta_ema, ''))

    # is_vol_drying (quiet coil)
    qc_y = hq[hq['is_vol_drying'] == True]
    qc_n = hq[hq['is_vol_drying'] == False]
    if len(qc_y) >= 5 and len(qc_n) >= 5:
        delta_qc = qc_y['mfe_atr'].mean() - qc_n['mfe_atr'].mean()
        factors.append(('is_vol_drying (yes vs no)', len(qc_n), qc_n['mfe_atr'].mean(),
                        len(qc_y), qc_y['mfe_atr'].mean(), delta_qc, '🔇'))

    # is_big_move (SPY context)
    bm_y = hq[hq['is_big_move'] == True]
    bm_n = hq[hq['is_big_move'] == False]
    if len(bm_y) >= 5 and len(bm_n) >= 5:
        delta_bm = bm_y['mfe_atr'].mean() - bm_n['mfe_atr'].mean()
        factors.append(('is_big_move ⚡ (yes vs no)', len(bm_n), bm_n['mfe_atr'].mean(),
                        len(bm_y), bm_y['mfe_atr'].mean(), delta_bm, '⚡'))

    # Sort by |delta| descending
    factors.sort(key=lambda x: abs(x[5]), reverse=True)

    hdr = (f"  {'Factor':<35} {'Low N':>6} {'Low MFE':>8} "
           f"{'High N':>7} {'High MFE':>9} {'Delta':>8} {'Sig':>5}")
    print(hdr)
    print('  ' + '-' * (len(hdr) - 2))
    for name, ln, lm, hn, hm, d, note in factors:
        print(f"  {name:<35} {ln:>6} {lm:>8.3f} {hn:>7} {hm:>9.3f} "
              f"{d:>+8.3f} {effect_label(d):>5}   {note}")

    print()
    print('  Detailed breakdowns:')

    # vol_ratio quartile detail
    if 'vol_ratio' in hq.columns and hq['vol_ratio'].notna().sum() >= 10:
        vr_valid = hq['vol_ratio'].dropna()
        cuts = pd.qcut(vr_valid, 4, labels=['Q1_quiet', 'Q2', 'Q3', 'Q4_loud'])
        cuts = cuts.reindex(hq.index)
        print()
        print('  vol_ratio quartile breakdown:')
        for lbl in ['Q1_quiet', 'Q2', 'Q3', 'Q4_loud']:
            sub = hq[cuts == lbl]
            if len(sub) >= 3:
                print(f'    {lbl:<12}  N={len(sub):>4}  avg vol={hq.loc[sub.index, "vol_ratio"].mean():.2f}x  '
                      f'avg MFE={sub["mfe_atr"].mean():.3f}  avg peak@{sub["peak_min"].mean():.0f}m')

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3: Context Factors (fingerprint match)
    # ══════════════════════════════════════════════════════════════════════════
    print()
    print(DIVIDER)
    print('SECTION 3 — CONTEXT FACTORS (move-fingerprints match)')
    print(SUBDIV)

    # Load catalog + fingerprints
    fp_df = None
    mc_df = None
    hq_fp = None

    try:
        mc_df = pd.read_parquet(CATALOG_PATH)
        print(f'  Catalog: {len(mc_df)} moves')
    except Exception as e:
        print(f'  Catalog load failed: {e}')

    try:
        fp_df = pd.read_parquet(FINGERPRINT_PATH)
        print(f'  Fingerprints: {len(fp_df)} rows, {len(fp_df.columns)} cols')
    except Exception as e:
        print(f'  Fingerprints load failed: {e}')

    if fp_df is not None and mc_df is not None:
        # Merge fingerprints into catalog
        cat_fp = mc_df.merge(fp_df, on='move_id', how='left')
        print(f'  Catalog+FP merged: {len(cat_fp)} rows, '
              f'{cat_fp["daily_atr_consumed"].notna().sum()} with daily_atr_consumed')

        # Convert catalog start_time to timezone-aware for matching
        cat_fp['start_ts'] = pd.to_datetime(cat_fp['start_time'])
        if cat_fp['start_ts'].dt.tz is None:
            cat_fp['start_ts'] = cat_fp['start_ts'].dt.tz_localize('US/Eastern')
        else:
            cat_fp['start_ts'] = cat_fp['start_ts'].dt.tz_convert('US/Eastern')

        # Match HQ signals to catalog moves (by symbol + timestamp proximity)
        print(f'  Matching {len(hq)} HQ signals to catalog within ±{FP_MATCH_MINS}m...')
        matched_rows = []
        for _, sig_row in hq.iterrows():
            sym = sig_row['symbol']
            ts  = sig_row['ts_et']
            sub_cat = cat_fp[cat_fp['symbol'] == sym]
            if len(sub_cat) == 0:
                continue
            dt = (sub_cat['start_ts'] - ts).abs().dt.total_seconds() / 60
            close = sub_cat[dt <= FP_MATCH_MINS]
            if len(close) == 0:
                continue
            best_idx = dt[dt <= FP_MATCH_MINS].idxmin()
            cat_row  = cat_fp.loc[best_idx]
            combo = {**sig_row.to_dict(), **{f'fp_{c}': cat_row.get(c) for c in [
                'daily_atr_consumed', 'level_tests_today', 'pre_12bar_range_atr',
                'breadth_bear_moves_15min', 'breadth_bull_moves_15min',
                'leader_score', 'spy_intraday_return', 'spy_range_consumed',
                'spy_ema_aligned', 'spy_vwap_aligned', 'pre_vol_dry_count',
                'magnitude_atr', 'timing_category', 'concurrent_symbols',
            ]}}
            matched_rows.append(combo)

        hq_fp = pd.DataFrame(matched_rows)
        n_matched = len(hq_fp)
        print(f'  Matched: {n_matched} / {len(hq)} HQ signals ({n_matched/len(hq)*100:.1f}%)')
        print()

    context_factors = []  # populated below if fingerprint match succeeded

    if hq_fp is not None and len(hq_fp) >= 10:
        # Build context factors cleanly
        context_factors = []
        for col_name, display, split, invert_flag in [
            ('daily_atr_consumed',      'daily_atr_consumed low(<50%) vs high',   0.5,  True),
            ('pre_12bar_range_atr',     'pre_12bar_range quiet vs loud',           None, True),
            ('pre_vol_dry_count',       'pre_vol_dry_count high vs low',           None, False),
            ('leader_score',            'leader_score high vs low',                None, False),
            ('spy_range_consumed',      'spy_range_consumed low vs high',          None, True),
            ('concurrent_symbols',      'concurrent_symbols high vs low',          None, False),
            ('level_tests_today',       'level_tests_today 1st vs 2nd+',           1.0,  True),
            ('breadth_bear_moves_15min','breadth_bear_moves low vs high',          None, True),
        ]:
            col_full = f'fp_{col_name}'
            if col_full not in hq_fp.columns:
                continue
            valid = hq_fp[hq_fp[col_full].notna()].copy()
            if len(valid) < 16:
                continue
            if split is not None:
                lo = valid[valid[col_full] <= split]
                hi = valid[valid[col_full] > split]
            else:
                med = valid[col_full].median()
                lo  = valid[valid[col_full] <= med]
                hi  = valid[valid[col_full] > med]
            if invert_flag:
                lo, hi = hi, lo   # 'high group' means favourable (low consumed, etc.)
            if len(lo) < 5 or len(hi) < 5:
                continue
            delta = hi['mfe_atr'].mean() - lo['mfe_atr'].mean()
            context_factors.append((display, len(lo), lo['mfe_atr'].mean(),
                                    len(hi), hi['mfe_atr'].mean(), delta))

        context_factors.sort(key=lambda x: abs(x[5]), reverse=True)

        hdr = (f"  {'Factor':<42} {'Low N':>6} {'Low MFE':>8} "
               f"{'High N':>7} {'High MFE':>9} {'Delta':>8} {'Sig':>5}")
        print(hdr)
        print('  ' + '-' * (len(hdr) - 2))
        for name, ln, lm, hn, hm, d in context_factors:
            print(f"  {name:<42} {ln:>6} {lm:>8.3f} {hn:>7} {hm:>9.3f} "
                  f"{d:>+8.3f} {effect_label(d):>5}")

        # Level freshness detail
        print()
        print('  Level freshness detail (level_tests_today on HQ signals):')
        fp_lt = f'fp_level_tests_today'
        if fp_lt in hq_fp.columns:
            for tests in [0, 1, 2, 3]:
                sub = hq_fp[hq_fp[fp_lt] == tests]
                if len(sub) >= 3:
                    print(f'    tests={tests}  N={len(sub):>4}  avg MFE={sub["mfe_atr"].mean():.3f}')
            sub_3p = hq_fp[hq_fp[fp_lt] >= 3]
            if len(sub_3p) >= 3:
                print(f'    tests=3+  N={len(sub_3p):>4}  avg MFE={sub_3p["mfe_atr"].mean():.3f}')

        # daily_atr_consumed buckets
        print()
        print('  daily_atr_consumed buckets on HQ signals:')
        dac = 'fp_daily_atr_consumed'
        if dac in hq_fp.columns:
            for lo_b, hi_b in [(0, 0.3), (0.3, 0.5), (0.5, 0.7), (0.7, 1.0)]:
                sub = hq_fp[(hq_fp[dac] >= lo_b) & (hq_fp[dac] < hi_b)]
                if len(sub) >= 3:
                    print(f'    {lo_b:.0%}-{hi_b:.0%}  N={len(sub):>4}  '
                          f'avg MFE={sub["mfe_atr"].mean():.3f}  '
                          f'avg peak@{sub["peak_min"].mean():.0f}m')

        # breadth: 4+ symbols together
        print()
        print('  Cross-symbol breadth on HQ signals:')
        cs = 'fp_concurrent_symbols'
        if cs in hq_fp.columns:
            for thresh in [2, 3, 4]:
                sub_y = hq_fp[hq_fp[cs] >= thresh]
                sub_n = hq_fp[hq_fp[cs] < thresh]
                if len(sub_y) >= 3:
                    print(f'    concurrent >= {thresh}:  N={len(sub_y):>4}  '
                          f'avg MFE={sub_y["mfe_atr"].mean():.3f}  '
                          f'vs <{thresh}: N={len(sub_n)}  avg MFE={sub_n["mfe_atr"].mean():.3f}  '
                          f'delta={sub_y["mfe_atr"].mean()-sub_n["mfe_atr"].mean():+.3f}')

    else:
        print('  (fingerprint match skipped — insufficient data or load error)')

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 4: Hold Optimisation for HQ Signals
    # ══════════════════════════════════════════════════════════════════════════
    print()
    print(DIVIDER)
    print('SECTION 4 — HOLD OPTIMISATION FOR HQ SIGNALS')
    print(SUBDIV)

    print()
    print('  P&L path at checkpoints (avg over HQ signals):')
    print(pnl_path_row(hq, 'All HQ signals'))
    print()
    print('  By signal type:')
    for stype, sub in hq.groupby('sig_type'):
        print(pnl_path_row(sub, f'{stype} (N={len(sub)})'))
    print()
    print('  By time of day:')
    for tod in ['morning', 'midday', 'afternoon']:
        sub = hq[hq['tod'] == tod]
        print(pnl_path_row(sub, f'{tod}'))

    # Peak distribution
    print()
    peak_dist(hq, 'All HQ signals')

    print()
    print('  By signal type:')
    for stype, sub in hq.groupby('sig_type'):
        peak_dist(sub, f'{stype}')

    # Early vs late peak split
    print()
    early_hq = hq[hq['peak_min'] <= 20]
    late_hq  = hq[hq['peak_min'] > 30]
    print(f'  Early-peak (0-20m) HQ signals: N={len(early_hq)}')
    print(f'  Late-peak  (30m+)  HQ signals: N={len(late_hq)}')

    if len(early_hq) >= 5 and len(late_hq) >= 5:
        print()
        print('  What distinguishes early vs late peak HQ signals?')
        for col_name in ['vol_ratio', 'range_atr', 'body_pct', 'ramp']:
            e_vals = early_hq[col_name].dropna()
            l_vals = late_hq[col_name].dropna()
            if len(e_vals) >= 5 and len(l_vals) >= 5:
                print(f'    {col_name:<15}  early={e_vals.mean():.3f}  late={l_vals.mean():.3f}  '
                      f'delta={l_vals.mean()-e_vals.mean():+.3f}')
        if hq_fp is not None:
            for fp_col in ['fp_pre_12bar_range_atr', 'fp_daily_atr_consumed', 'fp_level_tests_today']:
                if fp_col not in hq_fp.columns:
                    continue
                early_fp = hq_fp[hq_fp['peak_min'] <= 20][fp_col].dropna()
                late_fp  = hq_fp[hq_fp['peak_min'] > 30][fp_col].dropna()
                if len(early_fp) >= 5 and len(late_fp) >= 5:
                    print(f'    {fp_col:<30}  early={early_fp.mean():.3f}  late={late_fp.mean():.3f}  '
                          f'delta={late_fp.mean()-early_fp.mean():+.3f}')

    # Net ATR under different exit rules on HQ signals only
    print()
    print('  Net ATR under different exit rules (HQ signals only):')
    hdr_exit = f"  {'Exit rule':<35} {'N':>5} {'Net ATR':>9} {'Avg P&L':>9} {'vs 60m':>8}"
    print(hdr_exit)
    print('  ' + '-' * (len(hdr_exit) - 2))
    base_net = hq['pnl_60m'].sum()
    rules_exit = [
        ('Hold 60m (baseline)',          'pnl_60m'),
        ('Exit at 10m',                  'pnl_10m'),
        ('Exit at 20m',                  'pnl_20m'),
        ('Exit at 30m',                  'pnl_30m'),
        ('Exit at 45m',                  'pnl_45m'),
        ('Partial: 50%@20m + 50%@60m',  'partial_20_60'),
    ]
    for label, col_r in rules_exit:
        net = hq[col_r].sum()
        avg = hq[col_r].mean()
        vs  = net - base_net
        print(f"  {label:<35} {len(hq):>5} {net:>+8.2f}  {avg:>+8.4f}  {vs:>+7.2f}")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 5: Symbol-Specific Profiles
    # ══════════════════════════════════════════════════════════════════════════
    print()
    print(DIVIDER)
    print('SECTION 5 — SYMBOL-SPECIFIC PROFILES (top 5 by HQ count)')
    print(SUBDIV)

    top5_syms = hq.groupby('symbol').size().sort_values(ascending=False).head(5).index.tolist()

    for sym in top5_syms:
        sub = hq[hq['symbol'] == sym]
        print()
        print(f'  {sym}:  N={len(sub)}  avg MFE={sub["mfe_atr"].mean():.3f}  '
              f'avg peak@{sub["peak_min"].mean():.0f}m')

        # Best sig type
        type_mfe = sub.groupby('sig_type')['mfe_atr'].agg(['count', 'mean'])
        type_mfe = type_mfe[type_mfe['count'] >= 2].sort_values('mean', ascending=False)
        if len(type_mfe) > 0:
            best_type = type_mfe.index[0]
            print(f'    Best sig type: {best_type}  '
                  f'(N={int(type_mfe.loc[best_type, "count"])}  '
                  f'avg MFE={type_mfe.loc[best_type, "mean"]:.3f})')
        else:
            print('    Best sig type: insufficient data')

        # Type breakdown
        for stype, tsub in sub.groupby('sig_type'):
            if len(tsub) >= 2:
                print(f'    {stype:<8}  N={len(tsub):>3}  avg MFE={tsub["mfe_atr"].mean():.3f}  '
                      f'avg peak@{tsub["peak_min"].mean():.0f}m')

        # Best TOD
        tod_mfe = sub.groupby('tod')['mfe_atr'].agg(['count', 'mean'])
        tod_mfe = tod_mfe[tod_mfe['count'] >= 2].sort_values('mean', ascending=False)
        if len(tod_mfe) > 0:
            best_tod = tod_mfe.index[0]
            print(f'    Best time: {best_tod}  '
                  f'(N={int(tod_mfe.loc[best_tod, "count"])}  '
                  f'avg MFE={tod_mfe.loc[best_tod, "mean"]:.3f})')

        # NVDA specific: direction breakdown
        if sym == 'NVDA':
            for direc in ['bull', 'bear']:
                dsub = sub[sub['direction'] == direc]
                if len(dsub) >= 2:
                    print(f'    NVDA {direc}: N={len(dsub)}  avg MFE={dsub["mfe_atr"].mean():.3f}  '
                          f'avg peak@{dsub["peak_min"].mean():.0f}m')
                    # Type breakdown within direction
                    for stype, tsub in dsub.groupby('sig_type'):
                        if len(tsub) >= 2:
                            print(f'      {stype:<8}  N={len(tsub):>3}  avg MFE={tsub["mfe_atr"].mean():.3f}')

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 6: Multi-Angle Improvement Assessment
    # ══════════════════════════════════════════════════════════════════════════
    print()
    print(DIVIDER)
    print('SECTION 6 — IMPROVEMENT MENU (A-H)')
    print(SUBDIV)
    print()

    improvements = []

    # A: ATR consumed gate (<50% at signal)
    label_A = 'A. ATR consumed gate (<50%)'
    if hq_fp is not None and 'fp_daily_atr_consumed' in hq_fp.columns:
        dac_valid = hq_fp[hq_fp['fp_daily_atr_consumed'].notna()]
        pass_A    = dac_valid[dac_valid['fp_daily_atr_consumed'] < 0.5]
        fail_A    = dac_valid[dac_valid['fp_daily_atr_consumed'] >= 0.5]
        pct_pass  = len(pass_A) / len(dac_valid) * 100 if len(dac_valid) > 0 else 0
        mfe_delta = pass_A['mfe_atr'].mean() - dac_valid['mfe_atr'].mean() if len(pass_A) > 0 else 0
        signals_lost = len(fail_A)
        net_gain  = pass_A['mfe_atr'].sum() - dac_valid['mfe_atr'].sum()  # relative
        improvements.append((label_A, len(pass_A), pct_pass, mfe_delta, net_gain, 'Med'))
    else:
        improvements.append((label_A, 0, 0, 0, 0, 'Med'))

    # B: Level freshness hard gate (1st test only)
    label_B = 'B. Level freshness gate (1st test)'
    if hq_fp is not None and 'fp_level_tests_today' in hq_fp.columns:
        lt_valid  = hq_fp[hq_fp['fp_level_tests_today'].notna()]
        pass_B    = lt_valid[lt_valid['fp_level_tests_today'] <= 1]
        fail_B    = lt_valid[lt_valid['fp_level_tests_today'] > 1]
        pct_pass  = len(pass_B) / len(lt_valid) * 100 if len(lt_valid) > 0 else 0
        mfe_delta = pass_B['mfe_atr'].mean() - lt_valid['mfe_atr'].mean() if len(pass_B) > 0 else 0
        net_gain  = pass_B['mfe_atr'].sum() - lt_valid['mfe_atr'].sum()
        improvements.append((label_B, len(pass_B), pct_pass, mfe_delta, net_gain, 'Low'))
    else:
        improvements.append((label_B, 0, 0, 0, 0, 'Low'))

    # C: Quiet pre-move gate (pre_12bar_range_atr < median)
    label_C = 'C. Quiet pre-move gate (pre_12bar < med)'
    if hq_fp is not None and 'fp_pre_12bar_range_atr' in hq_fp.columns:
        qpm_valid = hq_fp[hq_fp['fp_pre_12bar_range_atr'].notna()]
        med_qpm   = qpm_valid['fp_pre_12bar_range_atr'].median()
        pass_C    = qpm_valid[qpm_valid['fp_pre_12bar_range_atr'] < med_qpm]
        pct_pass  = len(pass_C) / len(qpm_valid) * 100 if len(qpm_valid) > 0 else 0
        mfe_delta = pass_C['mfe_atr'].mean() - qpm_valid['mfe_atr'].mean() if len(pass_C) > 0 else 0
        net_gain  = pass_C['mfe_atr'].sum() - qpm_valid['mfe_atr'].sum()
        improvements.append((label_C, len(pass_C), pct_pass, mfe_delta, net_gain, 'Med'))
    else:
        improvements.append((label_C, 0, 0, 0, 0, 'Med'))

    # D: Partial profit rule (50%@20m + 50%@60m)
    label_D = 'D. Partial profit (50%@20m + 50%@60m)'
    net_60m    = hq['pnl_60m'].sum()
    net_partial = hq['partial_20_60'].sum()
    delta_D    = net_partial - net_60m
    avg_delta_D = delta_D / len(hq) if len(hq) > 0 else 0
    improvements.append((label_D, len(hq), 100.0, avg_delta_D, delta_D, 'Low'))

    # E: NVDA bear REV 2x size
    label_E = 'E. NVDA bear REV 2x size'
    nvda_bear_rev = hq[(hq['symbol'] == 'NVDA') & (hq['direction'] == 'bear') &
                       (hq['sig_type'].str.contains('REV', na=False))]
    if len(nvda_bear_rev) > 0:
        extra_gain_E = nvda_bear_rev['pnl_atr'].sum()  # 1x extra per signal
        avg_delta_E  = extra_gain_E / len(hq) if len(hq) > 0 else 0
        improvements.append((label_E, len(nvda_bear_rev), len(nvda_bear_rev)/len(hq)*100,
                              avg_delta_E, extra_gain_E, 'Low'))
    else:
        improvements.append((label_E, 0, 0, 0, 0, 'Low'))

    # F: BAIL positive guard (pnl>=0 at 5m → suppress BAIL)
    label_F = 'F. BAIL positive guard (already known: +36 ATR)'
    # Estimate proportion of HQ signals affected
    # HQ signals by definition won, so many would have been BAILed when positive
    hq_positive_5m = hq[hq['pnl_10m'] > 0]  # proxy using 10m (closest to 5m CHECK)
    improvements.append((label_F, len(hq_positive_5m),
                         len(hq_positive_5m)/len(hq)*100 if len(hq) > 0 else 0,
                         0.0, 36.0, 'Low'))  # +36 ATR already measured externally

    # G: Cross-symbol confirmation (2+ others triggering same direction in 5m)
    label_G = 'G. Cross-symbol confirmation (4+ concurrent)'
    if hq_fp is not None and 'fp_concurrent_symbols' in hq_fp.columns:
        cs_valid = hq_fp[hq_fp['fp_concurrent_symbols'].notna()]
        pass_G   = cs_valid[cs_valid['fp_concurrent_symbols'] >= 4]
        pct_pass = len(pass_G) / len(cs_valid) * 100 if len(cs_valid) > 0 else 0
        mfe_delta_G = pass_G['mfe_atr'].mean() - cs_valid['mfe_atr'].mean() if len(pass_G) > 0 else 0
        net_gain_G  = pass_G['mfe_atr'].sum() - cs_valid['mfe_atr'].sum()
        improvements.append((label_G, len(pass_G), pct_pass, mfe_delta_G, net_gain_G, 'High'))
    else:
        improvements.append((label_G, 0, 0, 0, 0, 'High'))

    # H: Time-of-day sizing (morning 1x, midday 1.5x)
    label_H = 'H. TOD sizing (midday 1.5x vs morning 1x)'
    mid_hq  = hq[hq['tod'] == 'midday']
    morn_hq = hq[hq['tod'] == 'morning']
    if len(mid_hq) > 0 and len(morn_hq) > 0:
        # Extra 0.5x on midday signals
        extra_H   = mid_hq['pnl_60m'].sum() * 0.5
        avg_H     = extra_H / len(hq) if len(hq) > 0 else 0
        delta_mfe = mid_hq['mfe_atr'].mean() - morn_hq['mfe_atr'].mean()
        improvements.append((label_H, len(mid_hq), len(mid_hq)/len(hq)*100, avg_H/len(hq) if len(hq)>0 else 0,
                              extra_H, 'Low'))
    else:
        improvements.append((label_H, 0, 0, 0, 0, 'Low'))

    # Print improvement table
    hdr = (f"  {'Improvement':<44} {'N pass':>7} {'% pass':>7} "
           f"{'ΔAvgMFE':>9} {'Net ATR':>9} {'Complexity':>12}")
    print(hdr)
    print('  ' + '-' * (len(hdr) - 2))
    for label, n_pass, pct_pass, d_mfe, net_atr, complexity in improvements:
        print(f"  {label:<44} {n_pass:>7} {pct_pass:>6.1f}%"
              f"  {d_mfe:>+8.4f}  {net_atr:>+8.2f}  {complexity:>12}")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 7: VERDICT
    # ══════════════════════════════════════════════════════════════════════════
    print()
    print(DIVIDER)
    print('SECTION 7 — VERDICT (top 3 improvements by ATR gain × implementability)')
    print(SUBDIV)
    print()

    # Score: net_atr magnitude × complexity_score (Low=3, Med=2, High=1)
    complexity_map = {'Low': 3, 'Med': 2, 'High': 1}
    scored = []
    for label, n_pass, pct_pass, d_mfe, net_atr, complexity in improvements:
        score = abs(net_atr) * complexity_map.get(complexity, 1)
        scored.append((score, net_atr, label, d_mfe, n_pass, complexity))
    scored.sort(key=lambda x: x[0], reverse=True)

    print('  Ranked by (|Net ATR| × implementability_score):')
    print()
    for rank, (score, net_atr, label, d_mfe, n_pass, complexity) in enumerate(scored[:3], 1):
        print(f'  #{rank}: {label}')
        print(f'       Net ATR estimate: {net_atr:+.1f}  |  ΔAvg MFE: {d_mfe:+.4f}  |  '
              f'Complexity: {complexity}  |  N signals: {n_pass}')
        print()

    print()
    print('  Key conclusions:')
    print()

    # Summarize top entry quality finding
    if factors:
        top_entry = factors[0]
        print(f'  Entry quality: Top factor = "{top_entry[0]}" — '
              f'delta MFE = {top_entry[5]:+.3f} ATR {effect_label(top_entry[5])}')

    # Context finding
    if hq_fp is not None and len(context_factors) > 0:
        top_ctx = context_factors[0]
        print(f'  Context: Top factor = "{top_ctx[0]}" — '
              f'delta MFE = {top_ctx[5]:+.3f} ATR {effect_label(top_ctx[5])}')

    # Hold
    best_hold_key = max(rules_exit, key=lambda x: hq[x[1]].sum())[0]
    best_hold_net = max(hq[r[1]].sum() for r in rules_exit)
    print(f'  Hold: Best exit rule = "{best_hold_key}" — net ATR = {best_hold_net:+.2f}')

    # TOD
    morning_mfe = hq[hq['tod'] == 'morning']['mfe_atr'].mean()
    midday_mfe  = hq[hq['tod'] == 'midday']['mfe_atr'].mean()
    print(f'  TOD: Midday avg MFE = {midday_mfe:.3f} ATR vs Morning = {morning_mfe:.3f} ATR '
          f'(delta = {midday_mfe - morning_mfe:+.3f})')

    print()
    print(DIVIDER)
    print(f'Analysis complete. Based on {len(hq)} HQ signals.')
    print(DIVIDER)

    # ── Save output ────────────────────────────────────────────────────────────
    sys.stdout = sys.__stdout__
    OUT_PATH.write_text(''.join(output_lines), encoding='utf-8')
    print(f'\nResults saved to: {OUT_PATH}')


if __name__ == '__main__':
    main()
