#!/usr/bin/env python3
"""
KLB BAIL + Runner Score Research
=================================
Part 1: BAIL Analysis — when does BAIL help vs hurt?
Part 2: Runner Score Redesign — predict fast vs late peaking signals

Uses v3.3c pine logs + IB 1m data.

Output sections:
  A  BAIL accuracy table (correct/wrong by category, net ATR impact)
  B  BAIL decision improvement rules
  C  Runner score factor analysis table
  D  Proposed new runner score (factors, weights, thresholds)
  E  Simulated ATR improvement with new rules
  F  VERDICT — what to actually implement

Usage: python3 bail_runner_research.py
Output: debug/bail_runner_research_results.txt
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

# ── Config ───────────────────────────────────────────────────────────────────
V33C_GLOB = 'pine-logs-Key Level Breakout v3.3c_*.csv'
HIGH_LEVEL_KEYWORDS = ['PM H', 'ORB H', 'Yest H', 'Week H']
WIN_MFE_THRESHOLD = 0.10    # ATR — minimum MFE to be a "real winner"
FORWARD_MINUTES   = 60
CHECKPOINTS       = [5, 10, 15, 20, 25, 30, 45, 60]

OUT_FILE = LOG_DIR / 'bail_runner_research_results.txt'
DIV  = '=' * 74
SDIV = '-' * 74

BAIL_CHECK_MINUTES = 5   # CHECK fires at 5m post-signal
# After BAIL fires, what actually happens at these offsets from signal time?
BAIL_FUTURE_MINUTES = [10, 15, 20, 30, 45, 60]


# ── Helpers ──────────────────────────────────────────────────────────────────

def parse_time_str(time_str):
    """Parse 'HH:MM' into (hour, minute) ints."""
    try:
        h, m = time_str.split(':')
        return int(h), int(m)
    except Exception:
        return 12, 0


def time_of_day_bucket(time_str):
    h, m = parse_time_str(time_str)
    t = h * 60 + m
    if t < 10 * 60:          # < 10:00
        return 'morning'
    elif t < 11 * 60 + 30:   # 10:00–11:30
        return 'late_morning'
    elif t < 14 * 60:         # 11:30–14:00
        return 'midday'
    else:                     # 14:00+
        return 'afternoon'


def is_bull_rev_at_high(sig):
    if sig.get('direction') != 'bull':
        return False
    if 'REV' not in sig.get('sig_type', ''):
        return False
    levels = sig.get('levels', '')
    return any(kw in levels for kw in HIGH_LEVEL_KEYWORDS)


# ── Load v3.3c signals (with CHECK results attached) ─────────────────────────

def load_v33c_signals():
    """Load all v3.3c signals; CHECK results are attached by parse_pine_log."""
    files = sorted(glob.glob(str(LOG_DIR / V33C_GLOB)))
    print(f'  Found {len(files)} v3.3c log files')
    all_signals = []
    symbols_seen = {}

    for fp in files:
        short = Path(fp).name.split('_')[-1].replace('.csv', '')
        signals = parse_pine_log(fp)
        if not signals:
            print(f'    {short}: 0 signals')
            continue
        symbol = identify_symbol(signals)
        if symbol is None:
            print(f'    {short}: could not identify symbol — skipping')
            continue
        for s in signals:
            s['symbol'] = symbol
        all_signals.extend(signals)
        symbols_seen[symbol] = symbols_seen.get(symbol, 0) + len(signals)
        print(f'    {short}: {symbol} — {len(signals)} signals')

    print(f'\n  Total signals: {len(all_signals)}')
    for sym, cnt in sorted(symbols_seen.items()):
        print(f'    {sym}: {cnt}')
    return all_signals


# ── Build P&L path at checkpoints ────────────────────────────────────────────

def build_pnl_at_minutes(sig, bars_1m, atr, minutes_list):
    """
    Return dict with p&l (close-based) at each minute offset.
    Also returns peak_minute and peak_pnl over FORWARD_MINUTES window.
    """
    ts = sig['timestamp']
    direction = sig['direction']
    entry = sig.get('close')

    if entry is None or atr is None or atr == 0:
        return None

    if ts.tzinfo is None:
        ts_et = pd.Timestamp(ts, tz='US/Eastern')
    else:
        ts_et = ts.tz_convert('US/Eastern')

    start_time = ts_et + pd.Timedelta(minutes=1)
    eod = ts_et.normalize() + pd.Timedelta(hours=16)
    end_time = min(ts_et + pd.Timedelta(minutes=FORWARD_MINUTES), eod)

    mask = (bars_1m.index >= start_time) & (bars_1m.index <= end_time)
    forward = bars_1m[mask]
    if len(forward) == 0:
        return None

    # Close-based P&L in ATR units
    if direction == 'bull':
        pnl_series = (forward['close'] - entry) / atr
        mfe_series = (forward['high'] - entry) / atr
    else:
        pnl_series = (entry - forward['close']) / atr
        mfe_series = (entry - forward['low']) / atr

    minutes_arr = ((forward.index - start_time).total_seconds() / 60).astype(int).values + 1
    pnl_arr     = pnl_series.values
    mfe_arr     = mfe_series.values

    result = {}
    for cp in minutes_list:
        idxs = np.where(minutes_arr <= cp)[0]
        result[f'pnl_{cp}m'] = float(pnl_arr[idxs[-1]]) if len(idxs) > 0 else float(pnl_arr[-1])

    # Peak info
    peak_idx             = int(np.argmax(pnl_arr))
    result['peak_minute'] = int(minutes_arr[peak_idx])
    result['peak_pnl']    = float(pnl_arr[peak_idx])
    result['pnl_60m']     = float(pnl_arr[-1])
    result['mfe_60m']     = float(mfe_arr.max())

    # MFE at 5m (to compare with logged pnl_at_check, which is MFE-based)
    # (The 5m CHECK pnl in the log uses MFE, not close, per Pine code)
    idxs5 = np.where(minutes_arr <= 5)[0]
    if len(idxs5) > 0:
        result['mfe_5m'] = float(mfe_arr[idxs5[-1]])
    else:
        result['mfe_5m'] = float(mfe_arr[-1])

    return result


# ── Main measurement loop ─────────────────────────────────────────────────────

def measure_all_signals(signals):
    """
    For each signal, compute P&L path using IB 1m data.
    Returns enriched list of dicts.
    """
    # Group by symbol for batch loading
    by_symbol = {}
    for sig in signals:
        sym = sig.get('symbol')
        if sym not in by_symbol:
            by_symbol[sym] = []
        by_symbol[sym].append(sig)

    enriched = []
    for sym, sigs in sorted(by_symbol.items()):
        print(f'  Loading {sym} 1m bars...')
        try:
            bars_1m = load_1m(sym)
            daily   = load_daily(sym)
            atr_ser = compute_atr(daily)
        except Exception as e:
            print(f'    ERROR: {e}')
            continue

        for sig in sigs:
            ts      = sig['timestamp']
            sig_date = ts.date() if hasattr(ts, 'date') else None
            atr = sig.get('atr')
            if (atr is None or atr == 0) and sig_date and sig_date in atr_ser.index:
                atr = float(atr_ser[sig_date])
            if atr is None or atr == 0:
                continue

            # Full minutes list for both BAIL analysis and runner analysis
            all_mins = sorted(set(BAIL_FUTURE_MINUTES + [5, FORWARD_MINUTES]))
            path = build_pnl_at_minutes(sig, bars_1m, atr, all_mins)
            if path is None:
                continue

            rec = dict(sig)
            rec['atr_used'] = atr
            rec.update(path)
            rec['time_bucket'] = time_of_day_bucket(sig.get('time_str', '12:00'))
            rec['is_suppressed'] = is_bull_rev_at_high(sig)
            enriched.append(rec)

    return enriched


# ── BAIL-focused dataset ──────────────────────────────────────────────────────

def extract_bail_dataset(enriched):
    """
    Filter to signals that have a 5m CHECK result (BAIL or HOLD).
    Only BRK and QBS get checked per Pine code.
    Returns list of dicts with bail-specific fields.
    """
    result = []
    for rec in enriched:
        check = rec.get('check_result')
        if check not in ('BAIL', 'HOLD'):
            continue
        if rec.get('sig_type') not in ('BRK', 'QBS'):
            continue

        # The log-reported pnl_at_check is available via parse_pine_log's CHECK matching
        # We also have our computed pnl at 5m (close-based)
        # For BAIL analysis, the key question is: what happened AFTER the decision?
        # pnl_at_60m vs pnl_at_5m tells us if holding longer was better

        pnl_5m  = rec.get('pnl_5m', 0.0)   # close-based
        pnl_60m = rec.get('pnl_60m', 0.0)

        # BAIL is "correct" if the final outcome (60m) would have been WORSE than
        # exiting at 5m — i.e., holding cost more than it gave back.
        # pnl at 5m ~ bail exit P&L (approximate — true bail exit is at market price)
        bail_correct  = (check == 'BAIL') and (pnl_60m < pnl_5m)
        bail_wrong    = (check == 'BAIL') and (pnl_60m >= pnl_5m)
        hold_paid_off = (check == 'HOLD') and (pnl_60m > pnl_5m)

        # Recovery: among BAIL'd signals that recovered to positive by 60m
        recovered     = (check == 'BAIL') and (pnl_60m > 0.05)

        result.append({
            'timestamp':     rec['timestamp'],
            'symbol':        rec['symbol'],
            'sig_type':      rec['sig_type'],
            'direction':     rec['direction'],
            'time_str':      rec.get('time_str', ''),
            'time_bucket':   rec['time_bucket'],
            'check_result':  check,
            'logged_pnl':    None,   # not reliably stored by parse_pine_log
            'pnl_5m':        pnl_5m,
            'pnl_10m':       rec.get('pnl_10m', 0.0),
            'pnl_15m':       rec.get('pnl_15m', 0.0),
            'pnl_20m':       rec.get('pnl_20m', 0.0),
            'pnl_30m':       rec.get('pnl_30m', 0.0),
            'pnl_45m':       rec.get('pnl_45m', 0.0),
            'pnl_60m':       pnl_60m,
            'mfe_5m':        rec.get('mfe_5m', 0.0),
            'mfe_60m':       rec.get('mfe_60m', 0.0),
            'bail_correct':  bail_correct,
            'bail_wrong':    bail_wrong,
            'hold_paid_off': hold_paid_off,
            'recovered':     recovered,
            'vol_ratio':     rec.get('vol_ratio'),
            'range_atr':     rec.get('range_atr'),
            'body_pct':      rec.get('body_pct'),
            'ramp':          rec.get('ramp'),
            'ema':           rec.get('ema'),
            'vwap':          rec.get('vwap'),
            'is_big_move':   rec.get('is_big_move', False),
            'is_vol_drying': rec.get('is_vol_drying', False),
            'atr_used':      rec.get('atr_used'),
            # SPY alignment info comes from the logged spy field, stored by parse_pine_log
            # We reconstruct from pnl sign since logged spy isn't stored on signals
        })

    return result


# ── Runner dataset (winners only) ────────────────────────────────────────────

def classify_runner_type(pnl_arr_by_minute):
    """
    Classify the exit shape:
      fast_mover   : peaks in 0-15m and pnl_20m >= 0.8 * peak_pnl
      steady       : peaks in 15-35m
      late_bloomer : peaks in 35-60m, pnl_20m < 0.5 * peak_pnl
      fader        : pnl_60m < pnl_20m by > 0.15 ATR (gave it back)
    """
    peak_m = pnl_arr_by_minute.get('peak_minute', 60)
    peak_p = pnl_arr_by_minute.get('peak_pnl', 0.0)
    p20    = pnl_arr_by_minute.get('pnl_20m', 0.0)
    p60    = pnl_arr_by_minute.get('pnl_60m', 0.0)

    if peak_p <= 0:
        return 'loser'

    is_fader = (p20 - p60) > 0.15 and p20 > 0.05  # started positive but faded
    if is_fader:
        return 'fader'
    if peak_m <= 15 and p20 >= 0.8 * peak_p:
        return 'fast_mover'
    if peak_m >= 35 and p20 < 0.5 * peak_p:
        return 'late_bloomer'
    return 'steady'


def extract_runner_dataset(enriched):
    """
    Filter to winning signals (mfe_60m >= threshold, pnl_60m > 0),
    classify runner type, and attach signal features.
    """
    result = []
    for rec in enriched:
        if rec.get('is_suppressed'):
            continue
        mfe = rec.get('mfe_60m', 0.0)
        pnl = rec.get('pnl_60m', 0.0)

        # Include all signals where MFE is real (winner universe)
        if mfe < WIN_MFE_THRESHOLD:
            continue

        pnl_path = {
            'peak_minute': rec.get('peak_minute', 60),
            'peak_pnl':    rec.get('peak_pnl', 0.0),
            'pnl_20m':     rec.get('pnl_20m', 0.0),
            'pnl_60m':     rec.get('pnl_60m', 0.0),
        }
        runner_type = classify_runner_type(pnl_path)
        if runner_type == 'loser':
            continue

        # Parse close_pos to numeric
        pos_str = rec.get('close_pos', '')
        try:
            close_pos_num = int(pos_str[1:]) if pos_str and pos_str[0] in ('v', '^') else 50
            close_pos_side = pos_str[0] if pos_str else 'v'
        except Exception:
            close_pos_num = 50
            close_pos_side = 'v'

        result.append({
            'timestamp':      rec['timestamp'],
            'symbol':         rec['symbol'],
            'sig_type':       rec['sig_type'],
            'direction':      rec['direction'],
            'time_str':       rec.get('time_str', ''),
            'time_bucket':    rec['time_bucket'],
            'runner_type':    runner_type,
            'peak_minute':    rec.get('peak_minute', 60),
            'peak_pnl':       rec.get('peak_pnl', 0.0),
            'pnl_5m':         rec.get('pnl_5m', 0.0),
            'pnl_20m':        rec.get('pnl_20m', 0.0),
            'pnl_30m':        rec.get('pnl_30m', 0.0),
            'pnl_60m':        rec.get('pnl_60m', 0.0),
            'mfe_60m':        rec.get('mfe_60m', 0.0),
            # Signal features available at fire time
            'vol_ratio':      rec.get('vol_ratio') or 2.0,
            'range_atr':      rec.get('range_atr') or 1.0,
            'body_pct':       rec.get('body_pct') or 50,
            'ramp':           rec.get('ramp') or 1.0,
            'ema':            rec.get('ema', 'na'),
            'vwap':           rec.get('vwap', 'na'),
            'is_big_move':    int(rec.get('is_big_move', False)),
            'is_vol_drying':  int(rec.get('is_vol_drying', False)),
            'close_pos_num':  close_pos_num,
            'close_pos_side': close_pos_side,
            'ema_aligned':    int(
                (rec.get('direction') == 'bull' and rec.get('ema') == 'bull') or
                (rec.get('direction') == 'bear' and rec.get('ema') == 'bear')
            ),
            'vwap_aligned':   int(
                (rec.get('direction') == 'bull' and rec.get('vwap') == 'above') or
                (rec.get('direction') == 'bear' and rec.get('vwap') == 'below')
            ),
            'is_morning':     int(rec['time_bucket'] == 'morning'),
            'is_midday':      int(rec['time_bucket'] == 'midday'),
            'is_afternoon':   int(rec['time_bucket'] == 'afternoon'),
        })

    return result


# ── BAIL Analysis functions ───────────────────────────────────────────────────

def bail_accuracy_table(bail_df, out):
    """Section A: BAIL accuracy by category."""
    df = pd.DataFrame(bail_df)
    if df.empty:
        out.append('  NO BAIL/HOLD events found.')
        return

    bail = df[df.check_result == 'BAIL']
    hold = df[df.check_result == 'HOLD']

    out.append(f'Total signals with 5m CHECK: {len(df)}')
    out.append(f'  BAIL decisions: {len(bail)}  ({100*len(bail)/len(df):.1f}%)')
    out.append(f'  HOLD decisions: {len(hold)}  ({100*len(hold)/len(df):.1f}%)')
    out.append('')

    # ── BAIL accuracy ──
    out.append('BAIL Accuracy:')
    n_bail = len(bail)
    if n_bail > 0:
        n_correct = bail['bail_correct'].sum()
        n_wrong   = bail['bail_wrong'].sum()
        n_recover = bail['recovered'].sum()
        out.append(f'  Correct (holding would be worse):  {n_correct} / {n_bail}  '
                   f'({100*n_correct/n_bail:.1f}%)')
        out.append(f'  Wrong   (holding would be better): {n_wrong}  / {n_bail}  '
                   f'({100*n_wrong/n_bail:.1f}%)')
        out.append(f'  Recovered to positive by 60m:      {n_recover} / {n_bail}  '
                   f'({100*n_recover/n_bail:.1f}%)')

        # ATR cost of wrong BAIL decisions
        wrong_bail = bail[bail['bail_wrong']]
        if not wrong_bail.empty:
            missed_per_signal = (wrong_bail['pnl_60m'] - wrong_bail['pnl_5m'])
            total_missed = missed_per_signal.sum()
            out.append(f'  Net ATR missed from wrong BAILs: {total_missed:+.2f} ATR '
                       f'(avg {missed_per_signal.mean():+.3f} per signal)')

        # ATR saved by correct BAIL decisions
        correct_bail = bail[bail['bail_correct']]
        if not correct_bail.empty:
            saved_per_signal = (correct_bail['pnl_5m'] - correct_bail['pnl_60m'])
            total_saved = saved_per_signal.sum()
            out.append(f'  Net ATR saved from correct BAILs: {total_saved:+.2f} ATR '
                       f'(avg {saved_per_signal.mean():+.3f} per signal)')

        out.append('')
        out.append('BAIL by pnl_at_5m bucket (close-based):')
        out.append(f'  {"pnl_5m":>14}  {"N":>5}  {"Correct%":>9}  {"Avg_saved":>10}')
        buckets = [
            ('< -0.20',  bail['pnl_5m'] < -0.20),
            ('-0.20..0',  (bail['pnl_5m'] >= -0.20) & (bail['pnl_5m'] < 0)),
            ('0..+0.05',  (bail['pnl_5m'] >= 0) & (bail['pnl_5m'] < 0.05)),
            ('> +0.05',   bail['pnl_5m'] >= 0.05),
        ]
        for label, mask in buckets:
            sub = bail[mask]
            if len(sub) == 0:
                continue
            corr = sub['bail_correct'].mean() * 100
            saved = (sub['pnl_5m'] - sub['pnl_60m']).mean()
            out.append(f'  {label:>14}  {len(sub):>5}  {corr:>8.1f}%  {saved:>+10.3f}')

    out.append('')
    out.append('BAIL by SPY alignment (from logged pnl sign as proxy):')
    # We don't have SPY stored on the signal dict; use pnl_5m sign as proxy
    # Instead, break by time_bucket which correlates with regime quality
    out.append('  (Note: SPY alignment not stored per-signal; using time bucket as proxy)')
    for bucket in ['morning', 'late_morning', 'midday', 'afternoon']:
        sub = bail[bail['time_bucket'] == bucket] if len(bail) > 0 else bail
        if len(sub) == 0:
            continue
        corr = sub['bail_correct'].mean() * 100 if len(sub) > 0 else 0
        avg_pnl_5m  = sub['pnl_5m'].mean()
        avg_pnl_60m = sub['pnl_60m'].mean()
        out.append(f'  {bucket:<14}  N={len(sub):>4}  correct={corr:.1f}%  '
                   f'pnl@5m={avg_pnl_5m:+.3f}  pnl@60m={avg_pnl_60m:+.3f}')

    out.append('')
    out.append('HOLD outcomes:')
    if len(hold) > 0:
        paid_off = hold['hold_paid_off'].mean() * 100
        avg_p5   = hold['pnl_5m'].mean()
        avg_p60  = hold['pnl_60m'].mean()
        out.append(f'  HOLD paid off (60m > 5m):  {paid_off:.1f}%')
        out.append(f'  Avg pnl@5m:  {avg_p5:+.4f} ATR')
        out.append(f'  Avg pnl@60m: {avg_p60:+.4f} ATR')
        out.append(f'  Avg improvement from holding: {avg_p60-avg_p5:+.4f} ATR')

        out.append('')
        out.append('  HOLD pnl trajectory (mean ATR):')
        for cp in [5, 15, 30, 60]:
            col = f'pnl_{cp}m'
            if col in hold.columns:
                out.append(f'    {cp:>3}m: {hold[col].mean():+.4f}')


def bail_improvement_rules(bail_df, out):
    """Section B: What predicts a correct BAIL?"""
    df = pd.DataFrame(bail_df)
    bail = df[df.check_result == 'BAIL'].copy()

    if bail.empty:
        out.append('  No BAIL data.')
        return

    out.append('Feature analysis for BAIL correctness:')
    out.append(f'  {"Feature":>20}  {"Split":>10}  {"N_lo":>6}  {"Corr_lo%":>9}  '
               f'{"N_hi":>6}  {"Corr_hi%":>9}  {"Best_rule"}')
    out.append('  ' + '-' * 70)

    features = [
        ('pnl_5m',    0.0,    'pnl<0 vs pnl>=0'),
        ('pnl_5m',   -0.10,   'pnl<-0.10 vs pnl>=-0.10'),
        ('vol_ratio',  3.0,   'vol<3x vs vol>=3x'),
        ('range_atr',  1.0,   'range<1 vs range>=1'),
        ('body_pct',   70,    'body<70% vs body>=70%'),
    ]

    best_rules = []
    for feat, split, label in features:
        col = feat
        if col not in bail.columns:
            continue
        lo = bail[bail[col] < split]
        hi = bail[bail[col] >= split]
        if len(lo) == 0 or len(hi) == 0:
            continue
        corr_lo = lo['bail_correct'].mean() * 100
        corr_hi = hi['bail_correct'].mean() * 100
        rule = f'{col}<{split}→{corr_lo:.0f}%  {col}>={split}→{corr_hi:.0f}%'
        out.append(f'  {feat:>20}  {split:>10}  {len(lo):>6}  {corr_lo:>8.1f}%  '
                   f'{len(hi):>6}  {corr_hi:>8.1f}%  ({rule})')
        best_rules.append((abs(corr_lo - corr_hi), feat, split, corr_lo, corr_hi))

    out.append('')
    out.append('Decision tree: pnl_5m x time_bucket accuracy matrix:')
    out.append(f'  {"":>16}  ' + '  '.join(f'{b:>14}' for b in
                ['morning', 'late_morning', 'midday', 'afternoon']))
    for pnl_cat, mask_fn in [
        ('pnl<-0.10', lambda df: df['pnl_5m'] < -0.10),
        ('-0.10..0',  lambda df: (df['pnl_5m'] >= -0.10) & (df['pnl_5m'] < 0)),
        ('pnl>=0',    lambda df: df['pnl_5m'] >= 0),
    ]:
        row = [f'{pnl_cat:>16}']
        for bucket in ['morning', 'late_morning', 'midday', 'afternoon']:
            sub = bail[mask_fn(bail) & (bail['time_bucket'] == bucket)]
            if len(sub) == 0:
                row.append(f'  {"—":>12}  ')
            else:
                row.append(f'  {sub["bail_correct"].mean()*100:>10.1f}% N={len(sub):<3}')
        out.append('  ' + ''.join(row))

    out.append('')
    # Summarise key rule
    out.append('Proposed BAIL guard rule (from data):')
    bail_neg_deep = bail[bail['pnl_5m'] < -0.10]
    bail_neg_shallow = bail[(bail['pnl_5m'] >= -0.10) & (bail['pnl_5m'] < 0)]
    bail_pos = bail[bail['pnl_5m'] >= 0]

    def corr_str(sub):
        if len(sub) == 0:
            return 'N=0'
        return f'{sub["bail_correct"].mean()*100:.0f}% (N={len(sub)})'

    out.append(f'  pnl < -0.10 ATR at 5m:  BAIL correct {corr_str(bail_neg_deep)}  '
               f'→ BAIL is reliable')
    out.append(f'  -0.10 ≤ pnl < 0 at 5m:  BAIL correct {corr_str(bail_neg_shallow)}  '
               f'→ marginal')
    out.append(f'  pnl ≥ 0 at 5m:           BAIL correct {corr_str(bail_pos)}  '
               f'→ BAIL is WRONG here (suppress)')


# ── Runner Score Analysis ─────────────────────────────────────────────────────

def runner_factor_analysis(runner_df, out):
    """Section C: Factor analysis for fast vs late movers."""
    df = pd.DataFrame(runner_df)
    if df.empty:
        out.append('  No runner data.')
        return

    types = df['runner_type'].value_counts()
    out.append(f'Runner type distribution (N={len(df)}):')
    for rt, n in types.items():
        out.append(f'  {rt:<14}: {n:>5}  ({100*n/len(df):.1f}%)  '
                   f'avg_peak={df[df.runner_type==rt]["peak_minute"].mean():.1f}m  '
                   f'avg_pnl60={df[df.runner_type==rt]["pnl_60m"].mean():+.4f}')

    out.append('')
    out.append('Feature analysis — fast_mover vs late_bloomer:')
    fast = df[df['runner_type'] == 'fast_mover']
    late = df[df['runner_type'] == 'late_bloomer']
    out.append(f'  fast_mover N={len(fast)}, late_bloomer N={len(late)}')
    out.append('')

    features = [
        'vol_ratio', 'range_atr', 'body_pct', 'ramp',
        'ema_aligned', 'vwap_aligned',
        'is_big_move', 'is_vol_drying',
        'close_pos_num', 'is_morning', 'is_midday', 'is_afternoon',
    ]

    out.append(f'  {"Feature":>18}  {"Mean_fast":>10}  {"Mean_late":>10}  '
               f'{"Delta":>8}  {"Effect_dir"}')
    out.append('  ' + '-' * 65)

    factor_effects = []
    for feat in features:
        if feat not in df.columns:
            continue
        m_fast = fast[feat].mean() if len(fast) > 0 else 0
        m_late = late[feat].mean() if len(late) > 0 else 0
        delta  = m_fast - m_late
        direction = '↑fast' if delta > 0 else '↑late'
        out.append(f'  {feat:>18}  {m_fast:>10.3f}  {m_late:>10.3f}  '
                   f'{delta:>+8.3f}  {direction}')
        factor_effects.append((abs(delta), delta, feat, m_fast, m_late))

    # Sort by effect size
    factor_effects.sort(reverse=True)
    out.append('')
    out.append('Top features by separation (|delta| fast vs late):')
    for rank, (eff, delta, feat, mf, ml) in enumerate(factor_effects[:8], 1):
        out.append(f'  #{rank}: {feat:<18}  delta={delta:+.3f}  '
                   f'fast={mf:.3f}  late={ml:.3f}')

    out.append('')
    out.append('All runner types — peak_minute breakdown:')
    out.append(f'  {"runner_type":>14}  {"avg_pk":>8}  {"pnl@5m":>8}  '
               f'{"pnl@20m":>8}  {"pnl@60m":>8}  {"decay":>8}')
    for rt in ['fast_mover', 'steady', 'late_bloomer', 'fader']:
        sub = df[df.runner_type == rt]
        if len(sub) == 0:
            continue
        avg_pk  = sub['peak_minute'].mean()
        p5      = sub['pnl_5m'].mean()
        p20     = sub['pnl_20m'].mean()
        p60     = sub['pnl_60m'].mean()
        decay   = sub['pnl_30m'].mean() - p60   # gave back from 30m to 60m
        out.append(f'  {rt:>14}  {avg_pk:>8.1f}  {p5:>+8.4f}  '
                   f'{p20:>+8.4f}  {p60:>+8.4f}  {decay:>+8.4f}')

    return factor_effects


def propose_runner_score(factor_effects, runner_df, out):
    """Section D: Proposed runner score formula."""
    df = pd.DataFrame(runner_df)
    if df.empty or not factor_effects:
        out.append('  No data for runner score proposal.')
        return

    out.append('Proposed runner score factors (from data):')
    out.append('')
    out.append('  Score = sum of points below. HIGH score = late bloomer (hold longer).')
    out.append('  LOW score = fast mover (exit earlier).')
    out.append('')

    # Derive factor weights from actual data effects
    # For each top feature, define a simple threshold rule
    scoring_rules = []

    feat_map = {fe[2]: fe for fe in factor_effects}

    rules = [
        # (feature, threshold, direction, points, label)
        # Low vol = quiet coil = often fast mover (compress then pop)
        ('vol_ratio',    2.0, 'low_is_fast',   -1, 'vol_ratio < 2.0 → fast mover hint'),
        # High volume at entry = momentum = might sustain
        ('vol_ratio',    5.0, 'high_is_late',  +1, 'vol_ratio > 5.0 → vol exhaustion, fade fast'),
        # Large range candle = momentum already spent = fast peak
        ('range_atr',    1.5, 'high_is_fast',  -1, 'range_atr > 1.5 → big candle, peaks fast'),
        # Big body % = decisive momentum = sustains better
        ('body_pct',     80,  'high_is_late',  +1, 'body_pct > 80% → strong conviction → slower peak'),
        # Morning = tends to fast-move (open momentum)
        ('is_morning',   0.5, 'high_is_fast',  -1, 'morning → tends to peak faster'),
        # Midday = tends to sustain (less noise)
        ('is_midday',    0.5, 'high_is_late',  +1, 'midday → tends to sustain'),
        # EMA aligned = trend running = holds longer
        ('ema_aligned',  0.5, 'high_is_late',  +1, 'EMA aligned → trend support → later peak'),
        # Vol drying (QBS) = coiled, tends to pop fast
        ('is_vol_drying',0.5, 'high_is_fast',  -1, 'vol_drying → coiled pop → fast'),
    ]

    for feat, thresh, direction, pts, label in rules:
        if feat not in df.columns:
            continue
        effect_entry = feat_map.get(feat)
        eff = effect_entry[0] if effect_entry else 0

        # Check which group fast vs late falls
        if direction == 'low_is_fast':
            fast_mask = df['runner_type'] == 'fast_mover'
            late_mask = df['runner_type'] == 'late_bloomer'
            fast_pct = (df.loc[fast_mask, feat] < thresh).mean() if fast_mask.any() else 0
            late_pct = (df.loc[late_mask, feat] < thresh).mean() if late_mask.any() else 0
        elif direction == 'high_is_late':
            fast_mask = df['runner_type'] == 'fast_mover'
            late_mask = df['runner_type'] == 'late_bloomer'
            fast_pct = (df.loc[fast_mask, feat] >= thresh).mean() if fast_mask.any() else 0
            late_pct = (df.loc[late_mask, feat] >= thresh).mean() if late_mask.any() else 0
        else:
            fast_pct = late_pct = 0

        scoring_rules.append((feat, thresh, pts, label, fast_pct, late_pct))
        out.append(f'  [{pts:+d} pts]  {label}')
        out.append(f'          fast_movers_qualifying={fast_pct*100:.1f}%  '
                   f'late_bloomers_qualifying={late_pct*100:.1f}%')

    out.append('')
    out.append('Score interpretation:')
    out.append('  score <= -2 : Fast mover expected → exit at 15-20m')
    out.append('  score -1..+1: Uncertain → exit at 30m (balanced)')
    out.append('  score >= +2 : Late bloomer expected → hold to 45-60m')
    out.append('')

    # Compute score for each signal and check peak correlation
    def compute_score(row):
        score = 0
        if row.get('vol_ratio', 2) < 2.0:    score -= 1
        if row.get('vol_ratio', 2) > 5.0:    score += 1
        if row.get('range_atr', 1) > 1.5:    score -= 1
        if row.get('body_pct', 50) > 80:      score += 1
        if row.get('is_morning', 0):           score -= 1
        if row.get('is_midday', 0):            score += 1
        if row.get('ema_aligned', 0):          score += 1
        if row.get('is_vol_drying', 0):        score -= 1
        return score

    df['runner_score'] = df.apply(compute_score, axis=1)

    corr_with_peak = df['runner_score'].corr(df['peak_minute'])
    corr_with_pnl  = df['runner_score'].corr(df['pnl_60m'])
    out.append(f'Score correlation with peak_minute: r={corr_with_peak:+.3f}')
    out.append(f'Score correlation with pnl_60m:     r={corr_with_pnl:+.3f}')
    out.append('')

    # Score bucket breakdown
    out.append('Score bucket breakdown:')
    out.append(f'  {"Score":>8}  {"N":>5}  {"avg_peak_min":>14}  '
               f'{"pnl@20m":>9}  {"pnl@60m":>9}  {"fast%":>8}  {"late%":>8}')
    for score_val in sorted(df['runner_score'].unique()):
        sub = df[df['runner_score'] == score_val]
        avg_pk  = sub['peak_minute'].mean()
        p20     = sub['pnl_20m'].mean()
        p60     = sub['pnl_60m'].mean()
        fast_p  = (sub['runner_type'] == 'fast_mover').mean() * 100
        late_p  = (sub['runner_type'] == 'late_bloomer').mean() * 100
        out.append(f'  {score_val:>8}  {len(sub):>5}  {avg_pk:>14.1f}  '
                   f'{p20:>+9.4f}  {p60:>+9.4f}  {fast_p:>7.1f}%  {late_p:>7.1f}%')

    return df  # return with runner_score added


def simulate_exit_improvement(runner_df_with_score, out):
    """Section E: Simulate ATR improvement with runner score exit rules."""
    df = runner_df_with_score
    if df is None or df.empty:
        out.append('  No data.')
        return

    out.append('Exit strategy simulation (vs 60m hold baseline):')
    out.append('')

    # Baseline: always hold 60m
    baseline_pnl = df['pnl_60m'].mean()
    baseline_net = df['pnl_60m'].sum()
    out.append(f'  Baseline (60m hold):  avg={baseline_pnl:+.4f} ATR/sig  '
               f'net={baseline_net:+.2f} ATR  N={len(df)}')
    out.append('')

    strategies = [
        ('Exit at 20m',          'pnl_20m',  None),
        ('Exit at 30m',          'pnl_30m',  None),
        ('Score<=-2: 20m, else 60m', None,   'score_gate_20m'),
        ('Score<=-2: 20m, +/-1: 30m, >=2: 60m', None, 'tiered'),
        ('Score>= 2: 60m, else 30m', None,  'score_gate_60m'),
    ]

    for label, col, rule in strategies:
        if col:
            pnl_series = df[col]
        elif rule == 'score_gate_20m':
            pnl_series = df.apply(
                lambda r: r['pnl_20m'] if r['runner_score'] <= -2 else r['pnl_60m'], axis=1
            )
        elif rule == 'tiered':
            def tiered(r):
                s = r['runner_score']
                if s <= -2:   return r['pnl_20m']
                elif s >= 2:  return r['pnl_60m']
                else:         return r['pnl_30m']
            pnl_series = df.apply(tiered, axis=1)
        elif rule == 'score_gate_60m':
            pnl_series = df.apply(
                lambda r: r['pnl_60m'] if r['runner_score'] >= 2 else r['pnl_30m'], axis=1
            )
        else:
            continue

        avg_pnl = pnl_series.mean()
        net_pnl = pnl_series.sum()
        delta   = net_pnl - baseline_net
        out.append(f'  {label:<45}: avg={avg_pnl:+.4f}  net={net_pnl:+.2f}  '
                   f'delta vs baseline={delta:+.2f} ATR')

    out.append('')
    out.append('  Interpretation: positive delta = improvement over 60m hold baseline.')
    out.append('  Negative delta = worse than just holding 60m (common for early exits).')


def verdict(bail_df, runner_df_with_score, out):
    """Section F: Verdict — what to actually implement."""
    df_bail = pd.DataFrame(bail_df)
    df_run  = runner_df_with_score

    out.append('Based on the data analysis above:')
    out.append('')

    # BAIL verdict
    out.append('── BAIL MECHANISM ──')
    if not df_bail.empty:
        bail = df_bail[df_bail.check_result == 'BAIL']
        bail_pos = bail[bail['pnl_5m'] >= 0]
        bail_neg_deep = bail[bail['pnl_5m'] < -0.10]

        acc_deep = bail_neg_deep['bail_correct'].mean() * 100 if len(bail_neg_deep) > 0 else 0
        acc_pos  = bail_pos['bail_correct'].mean() * 100 if len(bail_pos) > 0 else 0

        if acc_deep > 70:
            out.append(f'  KEEP BAIL when pnl < -0.10 ATR at 5m  '
                       f'(correct {acc_deep:.0f}% of the time)')
        if acc_pos < 50:
            out.append(f'  SUPPRESS BAIL when pnl >= 0 at 5m  '
                       f'(only correct {acc_pos:.0f}% of the time — it is wrong)')
            out.append(f'  → Add Pine guard: if pnl_5m >= 0, HOLD always')

        wrong_bail = bail[bail['bail_wrong']]
        if not wrong_bail.empty:
            missed = (wrong_bail['pnl_60m'] - wrong_bail['pnl_5m']).sum()
            out.append(f'  Estimated ATR recovered by suppressing wrong BAILs: '
                       f'{missed:+.2f} ATR')

    out.append('')
    out.append('── RUNNER SCORE ──')
    if df_run is not None and not df_run.empty and 'runner_score' in df_run.columns:
        corr = df_run['runner_score'].corr(df_run['peak_minute'])
        out.append(f'  New score correlation with peak_minute: r={corr:+.3f}')

        if abs(corr) > 0.10:
            out.append('  Score has MEANINGFUL correlation — worth implementing.')
            out.append('  Recommended implementation:')
            out.append('    runner_score = vol_dim_bonus + body_bonus + ema_bonus')
            out.append('                   + midday_bonus - morning_penalty')
            out.append('                   - vol_drying_penalty - big_range_penalty')
            out.append('    score >= +2 → hold 60m (late bloomer)')
            out.append('    score <= -2 → exit at 20m (fast mover)')
            out.append('    else       → exit at 30m (default)')
        else:
            out.append(f'  Score correlation is WEAK (r={corr:.3f}) — runner score '
                       f'still not reliable with current features.')
            out.append('  → Do NOT implement runner score gating yet.')
            out.append('  → 60m hold remains the recommended default.')
    else:
        out.append('  No runner data available.')

    out.append('')
    out.append('── PRIORITY ORDER ──')
    out.append('  1. Fix BAIL gate first (highest expected ATR recovery, single Pine change)')
    out.append('  2. Runner score: pilot with runner_score field in Pine logs for 2 weeks')
    out.append('  3. Redesign runner score exit when N >= 500 signals with live data')


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(DIV)
    print('KLB BAIL + Runner Score Research')
    print(DIV)

    print('\n[1] Loading v3.3c signals...')
    all_signals = load_v33c_signals()

    print('\n[2] Measuring P&L paths for all signals...')
    enriched = measure_all_signals(all_signals)
    print(f'  Enriched: {len(enriched)} signals with P&L paths')

    print('\n[3] Extracting BAIL/HOLD dataset...')
    bail_data = extract_bail_dataset(enriched)
    print(f'  BAIL/HOLD events: {len(bail_data)}')

    print('\n[4] Extracting runner dataset (winners)...')
    runner_data = extract_runner_dataset(enriched)
    print(f'  Runner signals (winners): {len(runner_data)}')

    # ── Build report ────────────────────────────────────────────────────────
    output_lines = []

    def section(title, fn, *args):
        output_lines.append('')
        output_lines.append(DIV)
        output_lines.append(title)
        output_lines.append(DIV)
        return fn(*args, output_lines)

    # Section A
    section('SECTION A — BAIL Accuracy Table', bail_accuracy_table, bail_data)

    # Section B
    output_lines.append('')
    output_lines.append(DIV)
    output_lines.append('SECTION B — BAIL Decision Improvement Rules')
    output_lines.append(DIV)
    bail_improvement_rules(bail_data, output_lines)

    # Section C
    output_lines.append('')
    output_lines.append(DIV)
    output_lines.append('SECTION C — Runner Score Factor Analysis')
    output_lines.append(DIV)
    factor_effects = runner_factor_analysis(runner_data, output_lines)

    # Section D
    output_lines.append('')
    output_lines.append(DIV)
    output_lines.append('SECTION D — Proposed New Runner Score')
    output_lines.append(DIV)
    runner_df_with_score = None
    if factor_effects is not None:
        runner_df_with_score = propose_runner_score(
            factor_effects, runner_data, output_lines
        )

    # Section E
    output_lines.append('')
    output_lines.append(DIV)
    output_lines.append('SECTION E — Simulated ATR Improvement')
    output_lines.append(DIV)
    simulate_exit_improvement(runner_df_with_score, output_lines)

    # Section F
    output_lines.append('')
    output_lines.append(DIV)
    output_lines.append('SECTION F — VERDICT')
    output_lines.append(DIV)
    verdict(bail_data, runner_df_with_score, output_lines)

    output_lines.append('')
    output_lines.append(DIV)

    # ── Write output ─────────────────────────────────────────────────────────
    report = '\n'.join(output_lines)
    print('\n' + report)

    with open(OUT_FILE, 'w') as f:
        f.write(report)

    print(f'\n[DONE] Results written to: {OUT_FILE}')


if __name__ == '__main__':
    main()
