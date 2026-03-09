#!/usr/bin/env python3
"""
KLB v3.4 Realistic P&L Backtest
=================================
Measures realistic trade-by-trade P&L using:
  - Entry at next 1m bar open (simulates 15-30s fill delay)
  - SL exit at slHard (0.15 ATR hard stop)
  - Time exits at 5/10/15/20/25/30/35/40/45/50/55/60 minutes
  - BAIL-aware variant (exit at 5m if 5m CHECK → BAIL)
  - Entry slippage analysis vs signal close price

Parses v3.4 Pine log CSVs (mtime = 8 März), deduplicates by first-20-line
fingerprint, and identifies the symbol by price matching against IB daily bars.

All P&L expressed in ATR units.

Usage:  python3 v34_realistic_pnl.py
Output: debug/v34_realistic_pnl_results.txt  (also prints to stdout)
"""

import re
import csv
import glob
import hashlib
import io
import warnings
from pathlib import Path
from datetime import time as dtime

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# ── Config ────────────────────────────────────────────────────────────────────
SYMBOLS   = ['SPY','AAPL','AMD','AMZN','GLD','GOOGL','META','MSFT',
             'NFLX','NVDA','QQQ','SLV','TSLA','TSM','XLE']
BAR_DIR   = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/'
                 'Meine Ablage/Claude/trading_bot/cache/bars/')
LOG_DIR   = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/'
                 'Meine Ablage/Claude/misc/TradingView/debug/')
OUT_FILE  = LOG_DIR / 'v34_realistic_pnl_results.txt'

V34_GLOB     = 'pine-logs-Key Level Breakout v3.4_*.csv'
EXIT_MINUTES = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
SL_ATR_FRAC  = 0.15          # slHard = 0.15 ATR from entry
WIN_THRESH   = 0.0            # P&L > 0 = win

DIVIDER = '=' * 76
SUBDIV  = '-' * 76


# ── Pine Log Parsing ──────────────────────────────────────────────────────────

# Main signal regex — captures time, direction, type+levels, plus all fields
SIG_PATTERN = re.compile(
    r'\[KLB\]\s+'
    r'(\d+:\d+)\s+'           # HH:MM
    r'([▲▼])\s+'              # direction
    r'(.+?)\s+'               # type+levels
    r'vol=([0-9.]+)x\s+'      # vol ratio
    r'pos=([v^]\d+)\s+'       # close position
    r'vwap=(above|below|na)\s+'
    r'ema=(bull|bear|na)\s+'
    r'rs=([+-]?[0-9.]+%?)\s+'
    r'adx=(\d+|na)\s+'
    r'body=(\d+)%\s+'
    r'ramp=([0-9.]+)x\s+'
    r'rangeATR=([0-9.]+)\s*'
    r'(.*?)\s*'               # flags (⚡ ⚠ 🔇 etc)
    r'O([0-9.]+)\s+'
    r'H([0-9.]+)\s+'
    r'L([0-9.]+)\s+'
    r'C([0-9.]+)\s+'
    r'ATR=([0-9.]+)'
    r'(?:\s+SL=([0-9.]+)/([0-9.]+))?'   # SL=slWarn/slHard  (optional)
)

RNG_PATTERN  = re.compile(
    r'\[KLB\]\s+(\d+:\d+)\s+([▲▼])\s+RNG\s+range\s+break\s+vol=([0-9.]+)x')
FADE_PATTERN = re.compile(
    r'\[KLB\]\s+(\d+:\d+)\s+([▲▼])\s+FADE\s+at\s+([0-9.]+)')
CHECK_PATTERN = re.compile(
    r'\[KLB\]\s+5m\s+CHECK\s+(\d+:\d+)\s+([▲▼])\s+pnl=([+-]?[0-9.]+)\s+'
    r'(SPY[✓✗~])\s+→\s+(HOLD|BAIL)')
QBS_PATTERN = re.compile(
    r'\[KLB\]\s+(\d+:\d+)\s+([▲▼])\s+🔇\s+QBS\s+'
    r'ramp=([0-9.]+)x\s+vol=([0-9.]+)x\s+pos=([v^]\d+)\s+'
    r'vwap=(above|below|na)\s+ema=(bull|bear|na)\s+'
    r'adx=(\d+|na)\s+body=(\d+)%\s+rangeATR=([0-9.]+)\s*'
    r'(.*?)\s*'
    r'O([0-9.]+)\s+H([0-9.]+)\s+L([0-9.]+)\s+C([0-9.]+)\s+ATR=([0-9.]+)'
    r'(?:\s+SL=([0-9.]+)/([0-9.]+))?'
)


def parse_type_levels(s):
    """Return (sig_type, levels_str)."""
    s = s.strip()
    if s.startswith('BRK '):
        return 'BRK', s[4:].strip()
    if s.startswith('~ x~ '):
        return 'REV', s[5:].strip()
    if s.startswith('~ ~~ ') or s.startswith('~~ '):
        return 'EXREV', (s[5:] if s.startswith('~ ~~ ') else s[3:]).strip()
    if s.startswith('~ ~ '):
        return 'REV', s[4:].strip()
    if s.startswith('~ '):
        return 'REV', s[2:].strip()
    return 'UNK', s


def parse_pine_log(filepath):
    """Parse a Pine log CSV → list of signal dicts + list of check dicts."""
    signals, checks = [], []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if len(row) < 2:
                continue
            timestamp_str = row[0]
            message = ' '.join(row[1:]).strip()
            if '[KLB]' not in message:
                continue

            try:
                ts = pd.Timestamp(timestamp_str)
            except Exception:
                continue

            # ── 5m CHECK ──
            m = CHECK_PATTERN.search(message)
            if m:
                t, dc, pnl_s, spy_s, action = m.groups()
                checks.append({
                    'timestamp': ts,
                    'direction': 'bull' if dc == '▲' else 'bear',
                    'pnl': float(pnl_s),
                    'spy': spy_s,
                    'action': action,
                })
                continue

            # ── RNG — skip (no clean entry/exit per spec) ──
            if RNG_PATTERN.search(message):
                continue

            # ── FADE ──
            m = FADE_PATTERN.search(message)
            if m:
                t, dc, lvl_price = m.groups()
                signals.append({
                    'timestamp': ts, 'time_str': t,
                    'direction': 'bull' if dc == '▲' else 'bear',
                    'sig_type': 'FADE', 'levels': f'at {lvl_price}',
                    'close': float(lvl_price), 'atr': None,
                    'sl_hard': None, 'check_result': None,
                })
                continue

            # ── QBS ──
            m = QBS_PATTERN.search(message)
            if m:
                (t, dc, ramp, vol, pos, vwap, ema, adx, body, ratr, flags,
                 o, h, l, c, atr, sl_warn, sl_hard) = m.groups()
                signals.append({
                    'timestamp': ts, 'time_str': t,
                    'direction': 'bull' if dc == '▲' else 'bear',
                    'sig_type': 'QBS', 'levels': 'QBS',
                    'close': float(c), 'atr': float(atr),
                    'sl_hard': float(sl_hard) if sl_hard else None,
                    'check_result': None,
                })
                continue

            # ── Main BRK/REV ──
            m = SIG_PATTERN.search(message)
            if m:
                (t, dc, tl, vol, pos, vwap, ema, rs, adx, body, ramp, ratr,
                 flags, o, h, l, c, atr, sl_warn, sl_hard) = m.groups()

                # Skip CONF lines that accidentally match (they have no OHLC fields
                # in this format) — already handled by the pattern requiring O H L C.
                if 'CONF' in message[:30]:
                    continue

                sig_type, levels_str = parse_type_levels(tl)
                if sig_type == 'UNK':
                    continue

                signals.append({
                    'timestamp': ts, 'time_str': t,
                    'direction': 'bull' if dc == '▲' else 'bear',
                    'sig_type': sig_type, 'levels': levels_str,
                    'close': float(c), 'atr': float(atr),
                    'sl_hard': float(sl_hard) if sl_hard else None,
                    'check_result': None,
                })
                continue

    # ── Attach 5m CHECK to nearest preceding confirmed signal ──
    # Match by direction, CHECK fires 5m after signal
    for chk in checks:
        best, best_dt = None, None
        for sig in signals:
            if sig['direction'] != chk['direction']:
                continue
            dt = (chk['timestamp'] - sig['timestamp']).total_seconds()
            if 0 < dt <= 600:  # 0 < dt ≤ 10 min
                if best_dt is None or dt < best_dt:
                    best, best_dt = sig, dt
        if best is not None:
            # Only assign if not already assigned (first check wins per signal)
            if best['check_result'] is None:
                best['check_result'] = chk['action']

    return signals


# ── File deduplication ────────────────────────────────────────────────────────

def file_fingerprint(filepath, n_lines=20):
    """Hash of first n_lines of file."""
    lines = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= n_lines:
                break
            lines.append(line)
    return hashlib.md5(''.join(lines).encode()).hexdigest()


def load_deduplicated_logs():
    """Load all v3.4 log files, deduplicating by content fingerprint."""
    files = sorted(glob.glob(str(LOG_DIR / V34_GLOB)))
    seen = set()
    unique_files = []
    for fp in files:
        fprint = file_fingerprint(fp)
        if fprint not in seen:
            seen.add(fprint)
            unique_files.append(fp)
    print(f'  v3.4 files: {len(files)} total, {len(unique_files)} unique')
    return unique_files


# ── Symbol identification ─────────────────────────────────────────────────────

def identify_symbol(signals, bar_dir=BAR_DIR, symbols=SYMBOLS):
    """Match signal prices to daily bars to identify the symbol."""
    samples = [s for s in signals if s.get('close') and s.get('atr')][:10]
    if not samples:
        return None

    best_sym, best_err = None, float('inf')
    for sym in symbols:
        fp = bar_dir / f'{sym.lower()}_1_day_ib.parquet'
        if not fp.exists():
            continue
        try:
            daily = pd.read_parquet(fp)
            dt = pd.to_datetime(daily['date'])
            if dt.dt.tz is not None:
                dt = dt.dt.tz_convert('US/Eastern')
            else:
                dt = dt.dt.tz_localize('US/Eastern')
            daily['date'] = dt
            daily = daily.set_index('date').sort_index()
        except Exception:
            continue

        total_err, matched = 0.0, 0
        for sig in samples:
            sig_date = sig['timestamp'].date()
            day_rows = daily[daily.index.date == sig_date]
            if len(day_rows) == 0:
                continue
            daily_close = day_rows['close'].iloc[0]
            if daily_close > 0:
                pct_err = abs(sig['close'] - daily_close) / daily_close
                total_err += pct_err
                matched += 1

        if matched > 0:
            avg_err = total_err / matched
            if avg_err < best_err:
                best_err, best_sym = avg_err, sym

    return best_sym if best_err < 0.05 else None


# ── IB bar loading ────────────────────────────────────────────────────────────

_bar_cache = {}

def load_1m(symbol):
    """Load 1m RTH bars, cached."""
    if symbol in _bar_cache:
        return _bar_cache[symbol]
    fp = BAR_DIR / f'{symbol.lower()}_1_min_ib.parquet'
    df = pd.read_parquet(fp)
    dt = pd.to_datetime(df['date'])
    if dt.dt.tz is None:
        dt = dt.dt.tz_localize('US/Eastern')
    else:
        dt = dt.dt.tz_convert('US/Eastern')
    df['date'] = dt
    df = df.set_index('date').sort_index()
    df = df.between_time('09:30', '15:59')
    _bar_cache[symbol] = df
    return df


# ── Core P&L simulation ───────────────────────────────────────────────────────

def simulate_trade(sig, bars_1m):
    """Simulate a single trade with realistic entry and multiple exits.

    Returns dict with:
      entry_price, signal_close, slippage_atr,
      sl_hit (bool), sl_hit_minutes,
      pnl_5m, pnl_10m, pnl_15m, pnl_30m, pnl_45m, pnl_60m,
      combined_pnl_5m .. combined_pnl_60m  (SL applies),
      bail_action
    """
    ts     = sig['timestamp']
    direct = sig['direction']
    sig_c  = sig.get('close')
    atr    = sig.get('atr')
    sl_hard_price = sig.get('sl_hard')   # may be None for FADE/old logs

    if sig_c is None or atr is None or atr == 0:
        return None

    # Normalise timezone
    if ts.tzinfo is None:
        ts_et = pd.Timestamp(ts, tz='US/Eastern')
    else:
        ts_et = ts.tz_convert('US/Eastern')

    # ── Entry: first 1m bar AFTER signal timestamp ──
    # Signal fires on the 5m bar close; the next 1m bar opens ~0-1 min later.
    entry_window_start = ts_et
    entry_window_end   = ts_et + pd.Timedelta(minutes=3)
    entry_bars = bars_1m[(bars_1m.index > entry_window_start) &
                         (bars_1m.index <= entry_window_end)]
    if len(entry_bars) == 0:
        return None
    entry_bar  = entry_bars.iloc[0]
    entry_price = entry_bar['open']

    # Slippage vs signal close
    if direct == 'bull':
        slippage = (entry_price - sig_c) / atr   # positive = worse fill
    else:
        slippage = (sig_c - entry_price) / atr

    # If sl_hard not in log, compute from ATR
    if sl_hard_price is None:
        if direct == 'bull':
            sl_hard_price = entry_price - SL_ATR_FRAC * atr
        else:
            sl_hard_price = entry_price + SL_ATR_FRAC * atr

    # ── Forward 1m bars up to 60m or EOD ──
    eod = ts_et.normalize() + pd.Timedelta(hours=16)
    end_time = min(ts_et + pd.Timedelta(minutes=60), eod)
    forward = bars_1m[(bars_1m.index > entry_window_start) &
                      (bars_1m.index <= end_time)]
    if len(forward) == 0:
        return None

    # ── SL hit detection ──
    sl_hit = False
    sl_hit_minutes = None
    sl_pnl = -SL_ATR_FRAC  # approximate; actual may differ slightly

    for i, (bar_ts, bar) in enumerate(forward.iterrows()):
        elapsed = (bar_ts - ts_et).total_seconds() / 60.0
        if direct == 'bull':
            if bar['low'] <= sl_hard_price:
                sl_hit = True
                sl_hit_minutes = elapsed
                sl_pnl = (sl_hard_price - entry_price) / atr
                break
        else:
            if bar['high'] >= sl_hard_price:
                sl_hit = True
                sl_hit_minutes = elapsed
                sl_pnl = (entry_price - sl_hard_price) / atr
                break

    # ── Time exit P&L (no SL) ──
    def pnl_at_minutes(mins):
        target_t = ts_et + pd.Timedelta(minutes=mins)
        target_t = min(target_t, eod)
        mask = forward.index <= target_t
        if not mask.any():
            return None
        bar = forward[mask].iloc[-1]
        c = bar['close']
        return (c - entry_price) / atr if direct == 'bull' else (entry_price - c) / atr

    time_pnls = {}
    for m in EXIT_MINUTES:
        time_pnls[m] = pnl_at_minutes(m)

    # ── Combined P&L (SL + time exit) ──
    combined_pnls = {}
    for m in EXIT_MINUTES:
        if sl_hit and sl_hit_minutes is not None and sl_hit_minutes <= m:
            combined_pnls[m] = sl_pnl
        else:
            combined_pnls[m] = time_pnls[m]

    return {
        'symbol':         sig.get('symbol'),
        'sig_type':       sig['sig_type'],
        'direction':      direct,
        'levels':         sig.get('levels', ''),
        'timestamp':      ts_et,
        'signal_close':   sig_c,
        'entry_price':    entry_price,
        'slippage_atr':   slippage,
        'atr':            atr,
        'sl_hit':         sl_hit,
        'sl_hit_minutes': sl_hit_minutes,
        'sl_pnl':         sl_pnl if sl_hit else None,
        'bail_action':    sig.get('check_result'),   # 'BAIL', 'HOLD', or None
        **{f'time_pnl_{m}m': time_pnls[m] for m in EXIT_MINUTES},
        **{f'combined_pnl_{m}m': combined_pnls[m] for m in EXIT_MINUTES},
    }


# ── Output helpers ────────────────────────────────────────────────────────────

def pnl_table(trades_df, col_prefix, header='', per_type=False):
    """Print a win%/net ATR table for time exits."""
    lines = []
    if header:
        lines.append(header)

    col_headers = f"{'Exit':>6}  {'N':>5}  {'Win%':>6}  {'Net ATR':>9}  {'/signal':>9}"
    lines.append(col_headers)
    lines.append(SUBDIV)

    for m in EXIT_MINUTES:
        col = f'{col_prefix}{m}m'
        sub = trades_df[trades_df[col].notna()].copy()
        if len(sub) == 0:
            lines.append(f'{m:>5}m  {"–":>5}  {"–":>6}  {"–":>9}  {"–":>9}')
            continue
        vals = sub[col]
        n = len(vals)
        win_pct = (vals > WIN_THRESH).sum() / n * 100
        net = vals.sum()
        per_sig = net / n
        lines.append(f'{m:>5}m  {n:>5}  {win_pct:>5.1f}%  {net:>+9.2f}  {per_sig:>+9.4f}')

    return '\n'.join(lines)


def type_breakdown(trades_df, col, exit_label):
    """Per-type breakdown for a single exit column."""
    lines = [f'\n  Type breakdown at {exit_label}:']
    lines.append(f"  {'Type':>6}  {'N':>5}  {'Win%':>6}  {'Net ATR':>9}  {'/signal':>9}")
    lines.append('  ' + '-' * 40)
    for sig_type in ['BRK', 'REV', 'EXREV', 'FADE', 'QBS']:
        sub = trades_df[(trades_df['sig_type'] == sig_type) & trades_df[col].notna()]
        if len(sub) == 0:
            continue
        vals = sub[col]
        n = len(vals)
        win_pct = (vals > WIN_THRESH).sum() / n * 100
        net = vals.sum()
        per_sig = net / n
        lines.append(f"  {sig_type:>6}  {n:>5}  {win_pct:>5.1f}%  {net:>+9.2f}  {per_sig:>+9.4f}")
    return '\n'.join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    output_lines = []

    def out(s=''):
        print(s)
        output_lines.append(s)

    out(DIVIDER)
    out('KLB v3.4 — Realistic P&L Backtest')
    out('Entry = next 1m bar open  |  SL = 0.15 ATR hard stop  |  P&L in ATR')
    out(DIVIDER)

    # ── Load & deduplicate logs ──
    out('\n[1] Loading Pine logs ...')
    unique_files = load_deduplicated_logs()

    all_signals = []
    skipped_files = 0

    for fp in unique_files:
        signals = parse_pine_log(fp)
        if not signals:
            skipped_files += 1
            continue

        # Identify symbol
        sym = identify_symbol(signals)
        if sym is None:
            skipped_files += 1
            continue

        for sig in signals:
            sig['symbol'] = sym
        all_signals.extend(signals)

    # Exclude RNG (already skipped in parser) — confirm
    all_signals = [s for s in all_signals if s['sig_type'] != 'RNG']

    out(f'  Total signals loaded: {len(all_signals)}')
    out(f'  Files skipped (no symbol match): {skipped_files}')

    by_type = pd.Series([s['sig_type'] for s in all_signals]).value_counts()
    out(f'  Signal types: {dict(by_type)}')

    # ── Simulate trades ──
    out('\n[2] Simulating trades ...')

    trade_rows = []
    symbols_used = set(s.get('symbol') for s in all_signals if s.get('symbol'))

    # Pre-load 1m bars for all needed symbols
    bars_by_sym = {}
    for sym in symbols_used:
        try:
            bars_by_sym[sym] = load_1m(sym)
        except Exception as e:
            out(f'  WARNING: could not load 1m bars for {sym}: {e}')

    no_data, no_result = 0, 0
    for sig in all_signals:
        sym = sig.get('symbol')
        if sym not in bars_by_sym:
            no_data += 1
            continue
        result = simulate_trade(sig, bars_by_sym[sym])
        if result is None:
            no_result += 1
            continue
        trade_rows.append(result)

    out(f'  Simulated: {len(trade_rows)} trades  '
        f'(no data: {no_data}, no result: {no_result})')

    df = pd.DataFrame(trade_rows)
    if df.empty:
        out('  ERROR: No trades to analyse.')
        return

    out(f'  Coverage by type:\n  {df["sig_type"].value_counts().to_dict()}')

    # ─────────────────────────────────────────────────────────────────────────
    out('\n' + DIVIDER)
    out('SECTION 1 — Entry Slippage Analysis')
    out(DIVIDER)

    slip = df['slippage_atr'].dropna()
    out(f'  N signals with slippage data: {len(slip)}')
    out(f'  Mean slippage:    {slip.mean():+.4f} ATR')
    out(f'  Median slippage:  {slip.median():+.4f} ATR')
    out(f'  Std dev:          {slip.std():.4f} ATR')
    out(f'  P25/P75:          {slip.quantile(0.25):+.4f} / {slip.quantile(0.75):+.4f}')
    out(f'  > +0.05 ATR (worse): {(slip > 0.05).sum()} ({(slip > 0.05).mean()*100:.1f}%)')
    out(f'  < -0.05 ATR (better): {(slip < -0.05).sum()} ({(slip < -0.05).mean()*100:.1f}%)')
    out(f'  Within ±0.05 ATR: {((slip.abs() <= 0.05)).sum()} ({((slip.abs() <= 0.05)).mean()*100:.1f}%)')

    # Slippage by direction
    for d in ['bull', 'bear']:
        sub = df[df['direction'] == d]['slippage_atr'].dropna()
        if len(sub):
            out(f'  {d.upper()} mean slippage: {sub.mean():+.4f} ATR  (N={len(sub)})')

    # ─────────────────────────────────────────────────────────────────────────
    out('\n' + DIVIDER)
    out('SECTION 2 — SL Hit Rate by Signal Type')
    out(DIVIDER)

    sl_col = 'sl_hit'
    overall_sl = df[sl_col].mean() * 100
    out(f'\n  Overall SL hit rate: {overall_sl:.1f}%  (N={len(df)})')
    out(f'\n  {"Type":>6}  {"N":>5}  {"SL%":>6}  {"Avg SL min":>10}  {"SL-only net ATR":>16}')
    out('  ' + '-' * 55)

    for sig_type in ['BRK', 'REV', 'EXREV', 'FADE', 'QBS']:
        sub = df[df['sig_type'] == sig_type]
        if len(sub) == 0:
            continue
        sl_rate = sub[sl_col].mean() * 100
        sl_trades = sub[sub[sl_col]]
        avg_sl_min = sl_trades['sl_hit_minutes'].mean() if len(sl_trades) else float('nan')
        sl_only_net = sl_trades['sl_pnl'].sum() if len(sl_trades) else 0.0
        out(f'  {sig_type:>6}  {len(sub):>5}  {sl_rate:>5.1f}%  '
            f'{avg_sl_min:>10.1f}  {sl_only_net:>+16.2f}')

    # ─────────────────────────────────────────────────────────────────────────
    out('\n' + DIVIDER)
    out('SECTION 3 — Full Exit Comparison: No SL vs SL=0.15 ATR (all 12 checkpoints)')
    out(DIVIDER)

    # Build combined delta table
    out('\n  All signals — No SL vs SL=0.15 ATR comparison:')
    hdr = (f"  {'Exit':>6}  {'N':>5}  {'NoSL Win%':>9}  {'NoSL Net':>9}  {'NoSL/sig':>9}"
           f"  {'SL Win%':>8}  {'SL Net':>9}  {'SL/sig':>9}  {'Delta/sig':>10}")
    out(hdr)
    out('  ' + '-' * 90)

    # Find best SL/sig for ★ marking
    best_m_comb, best_per_sig_comb = None, float('-inf')
    for m in EXIT_MINUTES:
        col = f'combined_pnl_{m}m'
        sub = df[df[col].notna()]
        if len(sub) == 0:
            continue
        per_sig = sub[col].sum() / len(sub)
        if per_sig > best_per_sig_comb:
            best_per_sig_comb, best_m_comb = per_sig, m

    for m in EXIT_MINUTES:
        t_col = f'time_pnl_{m}m'
        c_col = f'combined_pnl_{m}m'
        t_sub = df[df[t_col].notna()].copy()
        c_sub = df[df[c_col].notna()].copy()
        if len(t_sub) == 0 and len(c_sub) == 0:
            continue
        t_vals = t_sub[t_col]
        c_vals = c_sub[c_col]
        t_n    = len(t_vals)
        c_n    = len(c_vals)
        t_win  = (t_vals > WIN_THRESH).sum() / t_n * 100 if t_n else float('nan')
        c_win  = (c_vals > WIN_THRESH).sum() / c_n * 100 if c_n else float('nan')
        t_net  = t_vals.sum()
        c_net  = c_vals.sum()
        t_ps   = t_net / t_n  if t_n else float('nan')
        c_ps   = c_net / c_n  if c_n else float('nan')
        delta  = c_ps - t_ps
        star   = ' ★' if m == best_m_comb else '  '
        out(f"  {m:>5}m{star} {t_n:>5}  {t_win:>8.1f}%  {t_net:>+9.2f}  {t_ps:>+9.4f}"
            f"  {c_win:>7.1f}%  {c_net:>+9.2f}  {c_ps:>+9.4f}  {delta:>+10.4f}")

    out(f'\n  ★ Best SL+time exit: {best_m_comb}m  ({best_per_sig_comb:+.4f} ATR/signal)')

    # ─────────────────────────────────────────────────────────────────────────
    out('\n' + DIVIDER)
    out('SECTION 4 — Per-Type Optimal Exit (SL=0.15 ATR, all 12 checkpoints)')
    out(DIVIDER)

    for sig_type in ['BRK', 'REV', 'QBS']:
        sub_type = df[df['sig_type'] == sig_type]
        if len(sub_type) == 0:
            continue
        out(f'\n  {sig_type} signals ({len(sub_type)} total):')
        out(f"  {'Exit':>6}  {'N':>5}  {'Win%':>6}  {'Net ATR':>9}  {'/signal':>9}")
        out('  ' + '-' * 44)
        best_m_t, best_ps_t = None, float('-inf')
        rows_t = []
        for m in EXIT_MINUTES:
            col = f'combined_pnl_{m}m'
            sub = sub_type[sub_type[col].notna()]
            if len(sub) == 0:
                rows_t.append((m, None, None, None, None))
                continue
            vals   = sub[col]
            n      = len(vals)
            win_p  = (vals > WIN_THRESH).sum() / n * 100
            net    = vals.sum()
            per_s  = net / n
            rows_t.append((m, n, win_p, net, per_s))
            if per_s > best_ps_t:
                best_ps_t, best_m_t = per_s, m
        for (m, n, win_p, net, per_s) in rows_t:
            if n is None:
                out(f'  {m:>5}m  {"–":>5}  {"–":>6}  {"–":>9}  {"–":>9}')
                continue
            star = ' ★' if m == best_m_t else '  '
            out(f'  {m:>5}m{star} {n:>5}  {win_p:>5.1f}%  {net:>+9.2f}  {per_s:>+9.4f}')
        if best_m_t:
            out(f'  → ★ {sig_type} optimal exit: {best_m_t}m  ({best_ps_t:+.4f} ATR/signal)')

    # ─────────────────────────────────────────────────────────────────────────
    out('\n' + DIVIDER)
    out('SECTION 5 — BAIL Comparison')
    out(DIVIDER)

    bail_sigs  = df[df['bail_action'] == 'BAIL']
    hold_sigs  = df[df['bail_action'] == 'HOLD']
    no_check   = df[df['bail_action'].isna()]

    out(f'\n  5m CHECK coverage: BAIL={len(bail_sigs)}, HOLD={len(hold_sigs)}, no-check={len(no_check)}')

    # Strategy A: BAIL-aware = exit at 5m if BAIL, else combined 60m
    # Strategy B: Hold-only  = combined 60m regardless
    def bail_aware_pnl(row):
        if row['bail_action'] == 'BAIL':
            return row['combined_pnl_5m']   # forced exit at 5m (SL may have hit earlier)
        return row['combined_pnl_60m']

    df['bail_aware_pnl'] = df.apply(bail_aware_pnl, axis=1)
    df['hold_only_pnl']  = df['combined_pnl_60m']

    # Only compare rows where we have 60m data
    cmp = df[df['combined_pnl_60m'].notna() & df['bail_aware_pnl'].notna()].copy()
    N = len(cmp)

    if N > 0:
        bail_net  = cmp['bail_aware_pnl'].sum()
        hold_net  = cmp['hold_only_pnl'].sum()
        diff      = bail_net - hold_net

        bail_win  = (cmp['bail_aware_pnl'] > WIN_THRESH).mean() * 100
        hold_win  = (cmp['hold_only_pnl']  > WIN_THRESH).mean() * 100

        out(f'\n  {"Strategy":>20}  {"N":>5}  {"Win%":>6}  {"Net ATR":>9}  {"/signal":>9}')
        out('  ' + '-' * 58)
        out(f'  {"BAIL-aware (BAIL→5m)":>20}  {N:>5}  {bail_win:>5.1f}%  '
            f'{bail_net:>+9.2f}  {bail_net/N:>+9.4f}')
        out(f'  {"Hold to 60m":>20}  {N:>5}  {hold_win:>5.1f}%  '
            f'{hold_net:>+9.2f}  {hold_net/N:>+9.4f}')
        out(f'\n  BAIL-aware delta vs hold-only: {diff:+.2f} ATR  ({diff/N:+.4f}/signal)')
        winner = 'BAIL-aware' if diff > 0 else 'Hold-to-60m'
        out(f'  → {winner} is better for signals with CHECK data.')

        # How much did BAIL save/cost?
        bail_mask = cmp['bail_action'] == 'BAIL'
        if bail_mask.any():
            bailed = cmp[bail_mask]
            bailed_5m  = bailed['combined_pnl_5m'].sum()
            bailed_60m = bailed['combined_pnl_60m'].sum()
            delta_bail = bailed_5m - bailed_60m
            out(f'\n  BAIL detail (N={len(bailed)} signals bailed at 5m):')
            out(f'    5m P&L sum:   {bailed_5m:+.2f} ATR')
            out(f'    60m P&L sum:  {bailed_60m:+.2f} ATR')
            out(f'    BAIL saved:   {delta_bail:+.2f} ATR  ({delta_bail/len(bailed):+.4f}/signal)')

    # ─────────────────────────────────────────────────────────────────────────
    out('\n' + DIVIDER)
    out('SECTION 6 — Best Exit Strategy Summary')
    out(DIVIDER)

    out(f'\n  {"Strategy":>32}  {"N":>5}  {"Net ATR":>9}  {"/signal":>9}')
    out('  ' + '-' * 65)

    results_for_ranking = []
    for m in EXIT_MINUTES:
        for use_sl in [False, True]:
            prefix = 'combined_pnl_' if use_sl else 'time_pnl_'
            label  = f'{"SL+":6}{m}m' if use_sl else f'{"No-SL":6}{m}m'
            col    = f'{prefix}{m}m'
            sub    = df[df[col].notna()]
            if len(sub) == 0:
                continue
            n = len(sub)
            net = sub[col].sum()
            per_sig = net / n
            results_for_ranking.append((per_sig, net, n, label, col))
            out(f'  {label:>32}  {n:>5}  {net:>+9.2f}  {per_sig:>+9.4f}')

    # BAIL-aware
    if N > 0:
        label = f'{"BAIL+SL+60m":>32}'
        per_sig = bail_net / N
        out(f'  {label}  {N:>5}  {bail_net:>+9.2f}  {per_sig:>+9.4f}')
        results_for_ranking.append((per_sig, bail_net, N, 'BAIL+SL+60m', 'bail_aware_pnl'))

    # Announce winner
    if results_for_ranking:
        winner = max(results_for_ranking, key=lambda x: x[0])
        out(f'\n  ★ WINNER: {winner[3].strip()}  '
            f'({winner[1]:+.2f} ATR total, {winner[0]:+.4f}/signal, N={winner[2]})')

    # ─────────────────────────────────────────────────────────────────────────
    out('\n' + DIVIDER)
    out('SECTION 7 — Stop-Loss Size Sweep  (entry = next 1m open, exit = 60m close)')
    out(DIVIDER)

    SL_SIZES = [0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 0.25, 0.30,
                0.40, 0.50, 0.75, 1.00, None]   # None = no SL

    # Build a per-signal forward-bar record (entry + 60 bars of low/high/close)
    # to avoid re-reading parquet. We pull this directly from bars_by_sym.
    out('\n  Building forward-bar records for SL sweep ...')

    fwd_records = []   # one dict per simulated signal
    for sig in all_signals:
        sym = sig.get('symbol')
        if sym not in bars_by_sym:
            continue
        bars_1m = bars_by_sym[sym]
        atr = sig.get('atr')
        sig_c = sig.get('close')
        if sig_c is None or atr is None or atr == 0:
            continue
        ts = sig['timestamp']
        if ts.tzinfo is None:
            ts_et = pd.Timestamp(ts, tz='US/Eastern')
        else:
            ts_et = ts.tz_convert('US/Eastern')

        entry_bars_w = bars_1m[(bars_1m.index > ts_et) &
                                (bars_1m.index <= ts_et + pd.Timedelta(minutes=3))]
        if len(entry_bars_w) == 0:
            continue
        entry_price = entry_bars_w.iloc[0]['open']

        eod = ts_et.normalize() + pd.Timedelta(hours=16)
        end_t = min(ts_et + pd.Timedelta(minutes=60), eod)
        fwd = bars_1m[(bars_1m.index > ts_et) & (bars_1m.index <= end_t)]
        if len(fwd) == 0:
            continue

        # Store elapsed minutes + low/high/close per bar (enough for sweep)
        bar_lows   = []
        bar_highs  = []
        bar_closes = []
        bar_mins   = []
        for bar_ts, bar in fwd.iterrows():
            elapsed = (bar_ts - ts_et).total_seconds() / 60.0
            bar_mins.append(elapsed)
            bar_lows.append(bar['low'])
            bar_highs.append(bar['high'])
            bar_closes.append(bar['close'])

        fwd_records.append({
            'sig_type':    sig['sig_type'],
            'direction':   sig['direction'],
            'entry_price': entry_price,
            'atr':         atr,
            'bar_mins':    bar_mins,
            'bar_lows':    bar_lows,
            'bar_highs':   bar_highs,
            'bar_closes':  bar_closes,
        })

    out(f'  Forward records: {len(fwd_records)}  (excludes RNG + missing data)')

    def sweep_sl(records, sl_atr, sig_type_filter=None):
        """Simulate all trades at a given SL size (None = no SL).
        Returns (N, sl_pct, nohit_pct, net_atr, per_sig, win_pct)."""
        pnls = []
        sl_hits = 0
        for rec in records:
            if sig_type_filter and rec['sig_type'] != sig_type_filter:
                continue
            entry   = rec['entry_price']
            atr_val = rec['atr']
            direct  = rec['direction']
            mins    = rec['bar_mins']
            lows    = rec['bar_lows']
            highs   = rec['bar_highs']
            closes  = rec['bar_closes']

            if sl_atr is not None:
                sl_price = (entry - sl_atr * atr_val if direct == 'bull'
                            else entry + sl_atr * atr_val)

            hit = False
            pnl = None
            for i, elapsed in enumerate(mins):
                if elapsed > 60.0:
                    break
                if sl_atr is not None:
                    if direct == 'bull' and lows[i] <= sl_price:
                        pnl = -sl_atr
                        hit = True
                        break
                    elif direct == 'bear' and highs[i] >= sl_price:
                        pnl = -sl_atr
                        hit = True
                        break

            if not hit:
                # Use close of last bar within 60m
                c60 = closes[-1]
                if direct == 'bull':
                    pnl = (c60 - entry) / atr_val
                else:
                    pnl = (entry - c60) / atr_val

            if pnl is None:
                continue
            if hit:
                sl_hits += 1
            pnls.append(pnl)

        n = len(pnls)
        if n == 0:
            return n, float('nan'), float('nan'), float('nan'), float('nan'), float('nan')
        arr = np.array(pnls)
        sl_pct    = sl_hits / n * 100
        nohit_pct = (n - sl_hits) / n * 100
        net_atr   = arr.sum()
        per_sig   = net_atr / n
        win_pct   = (arr > 0).sum() / n * 100
        return n, sl_pct, nohit_pct, net_atr, per_sig, win_pct

    # ── Overall sweep table ──
    out('\n  Overall (all types, 60m exit):\n')
    out(f"  {'SL':>7}  {'SL%':>6}  {'NoHit%':>7}  {'Net ATR':>9}  {'/signal':>9}  {'Win%':>6}")
    out('  ' + '─' * 57)

    best_sl_overall, best_ps_overall = None, float('-inf')
    sweep_results = []
    for sl in SL_SIZES:
        n, sl_pct, nohit_pct, net_atr, per_sig, win_pct = sweep_sl(fwd_records, sl)
        sweep_results.append((sl, n, sl_pct, nohit_pct, net_atr, per_sig, win_pct))
        if per_sig > best_ps_overall:
            best_ps_overall, best_sl_overall = per_sig, sl

    for (sl, n, sl_pct, nohit_pct, net_atr, per_sig, win_pct) in sweep_results:
        sl_label = f'{sl:.2f}' if sl is not None else 'NO_SL'
        star = ' ★' if sl == best_sl_overall else '  '
        out(f"  {sl_label:>7}{star}{sl_pct:>5.1f}%  {nohit_pct:>6.1f}%"
            f"  {net_atr:>+9.2f}  {per_sig:>+9.4f}  {win_pct:>5.1f}%")

    best_label = f'{best_sl_overall:.2f}' if best_sl_overall is not None else 'NO_SL'
    out(f'\n  ★ Overall winner: SL={best_label}  ({best_ps_overall:+.4f} ATR/signal)')

    # ── Per-type sweep tables ──
    for sig_type in ['BRK', 'REV', 'QBS']:
        type_records = [r for r in fwd_records if r['sig_type'] == sig_type]
        if not type_records:
            continue
        out(f'\n  {sig_type} signals ({len(type_records)} total):\n')
        out(f"  {'SL':>7}  {'SL%':>6}  {'NoHit%':>7}  {'Net ATR':>9}  {'/signal':>9}  {'Win%':>6}")
        out('  ' + '─' * 57)

        best_sl_t, best_ps_t = None, float('-inf')
        type_sweep = []
        for sl in SL_SIZES:
            n, sl_pct, nohit_pct, net_atr, per_sig, win_pct = sweep_sl(fwd_records, sl, sig_type_filter=sig_type)
            type_sweep.append((sl, n, sl_pct, nohit_pct, net_atr, per_sig, win_pct))
            if per_sig > best_ps_t:
                best_ps_t, best_sl_t = per_sig, sl

        for (sl, n, sl_pct, nohit_pct, net_atr, per_sig, win_pct) in type_sweep:
            sl_label = f'{sl:.2f}' if sl is not None else 'NO_SL'
            star = ' ★' if sl == best_sl_t else '  '
            out(f"  {sl_label:>7}{star}{sl_pct:>5.1f}%  {nohit_pct:>6.1f}%"
                f"  {net_atr:>+9.2f}  {per_sig:>+9.4f}  {win_pct:>5.1f}%")

        best_label = f'{best_sl_t:.2f}' if best_sl_t is not None else 'NO_SL'
        out(f'\n  ★ {sig_type} winner: SL={best_label}  ({best_ps_t:+.4f} ATR/signal)')

    # ── Save to file ──
    out('\n' + DIVIDER)
    out(f'Results saved to: {OUT_FILE}')

    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))


if __name__ == '__main__':
    main()
