#!/usr/bin/env python3
"""
Open Scalp — Always Buy Call in First 30s.

Entry logic (whichever comes first):
  A) Price dips → buy when it recovers 1/3 of the dip from low (min dip threshold)
  B) 30s passes without dip entry → buy at 30s close

Exit variants tested:
  1) Fixed hold: 30s, 60s, 90s, 120s, 5m
  2) Momentum fade: 2 or 3 consecutive down bars
  3) Combo: momentum OR max hold
  4) TP/SL with various holds
"""

import os, sys
import pandas as pd
import numpy as np
import pytz
from datetime import datetime, timedelta
from statistics import mean, stdev

ET = pytz.timezone('US/Eastern')

BASE = os.path.dirname(os.path.abspath(__file__))
_PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(BASE)))
PARQ_5S_DIR = os.path.join(_PROJ_ROOT, "trading_bot", "cache", "bars_highres", "5sec")
OUTPUT = os.path.join(BASE, "open-scalp-call30s.md")

SYMBOL = "TSLA"
SPREAD_COST = 0.15
DELTA = 0.50
CONTRACT_MULT = 100
HARD_EXIT_TIME = "09:35:00"


def load_5s(symbol):
    fpath = os.path.join(PARQ_5S_DIR, f"{symbol.lower()}_5_secs_ib.parquet")
    df = pd.read_parquet(fpath).set_index('date').sort_index()
    return df


def opt_pnl(stock_pnl):
    return (stock_pnl * DELTA - SPREAD_COST) * CONTRACT_MULT


def find_entry(day_bars, day_start, min_dip, recovery_pct):
    """
    Scan first 30s. Two paths:
      A) Price dips >= min_dip → enter when recovery_pct of dip is reclaimed
      B) 30s passes → enter at 30s bar close
    Returns (entry_price, entry_time, entry_type, dip_low, open_price) or None.
    """
    window_end = day_start + timedelta(seconds=30)
    scan_bars = day_bars.loc[(day_bars.index >= day_start) & (day_bars.index <= window_end + timedelta(seconds=5))]

    if len(scan_bars) < 2:
        return None

    open_price = scan_bars.iloc[0]['open']
    running_low = open_price
    bar_30s = None

    for idx, row in scan_bars.iterrows():
        secs = (idx - day_start).total_seconds()

        # Track running low
        if row['low'] < running_low:
            running_low = row['low']

        dip_size = open_price - running_low

        # Path A: dip recovery entry
        if dip_size >= min_dip:
            recovery_target = running_low + dip_size * recovery_pct
            if row['high'] >= recovery_target:
                return recovery_target, idx, 'DIP', running_low, open_price

        # Track 30s bar for fallback
        if secs >= 30 and bar_30s is None:
            bar_30s = (row['close'], idx)

    # Path B: no dip entry triggered, use 30s close
    if bar_30s:
        return bar_30s[0], bar_30s[1], '30s', running_low, open_price

    # Fallback: use last bar in window
    if len(scan_bars) > 0:
        last = scan_bars.iloc[-1]
        return last['close'], scan_bars.index[-1], '30s', running_low, open_price

    return None


def simulate_exit(bars_after_entry, entry_price, max_secs,
                  fixed_hold=None, momentum_bars=None, tp=None, sl=None):
    """
    Always LONG. Exit on:
      - fixed_hold: exit at exactly N seconds
      - momentum_bars: exit after N consecutive down bars (min 10s hold)
      - tp/sl: fixed take profit / stop loss
      - max_secs: hard time stop
    """
    peak = trough = last_pnl = 0.0
    last_secs = 0
    t0 = bars_after_entry.index[0] if len(bars_after_entry) > 0 else None
    consecutive_down = 0
    prev_close = None

    for idx, row in bars_after_entry.iterrows():
        if t0 is None:
            t0 = idx
        secs = (idx - t0).total_seconds() + 5
        if secs > max_secs:
            break

        pnl = row['close'] - entry_price
        best = row['high'] - entry_price
        worst = row['low'] - entry_price
        peak = max(peak, best)
        trough = min(trough, worst)
        last_pnl = pnl
        last_secs = secs

        # TP
        if tp and best >= tp:
            return {'exit_secs': secs, 'exit_reason': 'TP', 'pnl_stock': tp,
                    'peak_pnl': peak, 'trough_pnl': trough}
        # SL
        if sl and worst <= -sl:
            return {'exit_secs': secs, 'exit_reason': 'SL', 'pnl_stock': -sl,
                    'peak_pnl': peak, 'trough_pnl': trough}

        # Fixed hold exit
        if fixed_hold and secs >= fixed_hold:
            return {'exit_secs': secs, 'exit_reason': 'HOLD', 'pnl_stock': pnl,
                    'peak_pnl': peak, 'trough_pnl': trough}

        # Momentum exit
        if momentum_bars and secs >= 10:
            if prev_close is not None and row['close'] < prev_close:
                consecutive_down += 1
            else:
                consecutive_down = 0
            if consecutive_down >= momentum_bars:
                return {'exit_secs': secs, 'exit_reason': 'MOM', 'pnl_stock': pnl,
                        'peak_pnl': peak, 'trough_pnl': trough}

        prev_close = row['close']

    # Time stop
    if t0 is not None and last_secs > 0:
        return {'exit_secs': last_secs, 'exit_reason': 'TIME',
                'pnl_stock': last_pnl, 'peak_pnl': peak, 'trough_pnl': trough}
    return None


def run_backtest(df, trading_days, min_dip, recovery_pct,
                 fixed_hold=None, momentum_bars=None, tp=None, sl=None):
    trades = []
    for date in trading_days:
        day_start = ET.localize(datetime.combine(date, datetime.strptime("09:30:00", "%H:%M:%S").time()))
        hard_exit_ts = ET.localize(datetime.combine(date, datetime.strptime(HARD_EXIT_TIME, "%H:%M:%S").time()))
        day_bars = df.loc[(df.index >= day_start) & (df.index < hard_exit_ts + timedelta(seconds=10))]
        if len(day_bars) < 6:
            continue

        result = find_entry(day_bars, day_start, min_dip, recovery_pct)
        if result is None:
            continue

        entry_price, entry_time, entry_type, dip_low, open_price = result
        remaining = day_bars.loc[day_bars.index > entry_time]
        if len(remaining) == 0:
            continue

        max_hold = (hard_exit_ts - entry_time).total_seconds()
        trade = simulate_exit(remaining, entry_price, max_hold,
                             fixed_hold=fixed_hold, momentum_bars=momentum_bars,
                             tp=tp, sl=sl)
        if trade:
            trade['date'] = date
            trade['entry_price'] = entry_price
            trade['entry_type'] = entry_type
            trade['entry_secs'] = (entry_time - day_start).total_seconds()
            trade['dip_low'] = dip_low
            trade['open_price'] = open_price
            trade['dip_size'] = open_price - dip_low
            trade['opt_pnl'] = opt_pnl(trade['pnl_stock'])
            trades.append(trade)
    return trades


def fmt(trades):
    if not trades:
        return "0 | — | — | — | — | — | — | —"
    pnls = [t['opt_pnl'] for t in trades]
    wins = sum(1 for p in pnls if p > 0)
    total = sum(pnls)
    avg = mean(pnls)
    sh = (mean(pnls) / stdev(pnls)) * (len(pnls)**0.5) if len(pnls) > 1 and stdev(pnls) > 0 else 0
    avg_hold = mean(t['exit_secs'] for t in trades)
    reasons = {}
    for t in trades:
        reasons[t['exit_reason']] = reasons.get(t['exit_reason'], 0) + 1
    rx = ", ".join(f"{k}:{v}" for k, v in sorted(reasons.items()))
    dip_entries = sum(1 for t in trades if t['entry_type'] == 'DIP')
    return f"{len(trades)} | {100*wins/len(trades):.0f}% | ${avg:+.0f} | ${total:+.0f} | {sh:.1f} | {avg_hold:.0f}s | DIP:{dip_entries}/30s:{len(trades)-dip_entries} | {rx}"


def main():
    df = load_5s(SYMBOL)
    market = df.between_time('09:30', '15:59')
    trading_days = sorted(set(market.index.date))
    print(f"Loaded {len(df):,} bars, {len(trading_days)} trading days\n")

    out = []
    out.append("# TSLA Open Scalp — Always Call, First 30s Entry\n")
    out.append(f"**Data:** {len(trading_days)} trading days, 5-second candles")
    out.append("**Entry:** Dip recovery (1/3 from low) OR 30s close, whichever first. Always LONG.")
    out.append(f"**Hard exit:** {HARD_EXIT_TIME}\n")

    # ── Part 1: Entry stats ───────────────────────────────────────────
    out.append("## Part 1: Entry Type Distribution\n")
    out.append("| Min Dip | DIP entries | 30s entries | Total | Avg Dip | Avg Entry Time |")
    out.append("|---------|-------------|-------------|-------|---------|----------------|")
    for min_dip in [0.20, 0.30, 0.50, 0.75, 1.00]:
        trades = run_backtest(df, trading_days, min_dip=min_dip, recovery_pct=0.33, fixed_hold=60)
        dips = [t for t in trades if t['entry_type'] == 'DIP']
        t30s = [t for t in trades if t['entry_type'] == '30s']
        avg_dip = mean(t['dip_size'] for t in dips) if dips else 0
        avg_entry = mean(t['entry_secs'] for t in trades) if trades else 0
        out.append(f"| ${min_dip:.2f} | {len(dips)} | {len(t30s)} | {len(trades)} | ${avg_dip:.2f} | {avg_entry:.0f}s |")

    # ── Part 2: Fixed hold comparison ─────────────────────────────────
    out.append("\n## Part 2: Fixed Hold Duration (min dip=$0.30, recovery=33%)\n")
    out.append("| Hold | Trades | Win% | Avg P&L | Total | Sharpe | Avg Hold | Entry Type | Exits |")
    out.append("|------|--------|------|---------|-------|--------|----------|------------|-------|")

    for hold in [15, 30, 45, 60, 90, 120, 180, 300]:
        trades = run_backtest(df, trading_days, min_dip=0.30, recovery_pct=0.33, fixed_hold=hold)
        out.append(f"| {hold}s | {fmt(trades)} |")

    # ── Part 3: Momentum exit ─────────────────────────────────────────
    out.append("\n## Part 3: Momentum Exit — Sell When Up Stops (min dip=$0.30, recovery=33%)\n")
    out.append("| Exit | Trades | Win% | Avg P&L | Total | Sharpe | Avg Hold | Entry Type | Exits |")
    out.append("|------|--------|------|---------|-------|--------|----------|------------|-------|")

    for mom in [2, 3, 4]:
        trades = run_backtest(df, trading_days, min_dip=0.30, recovery_pct=0.33, momentum_bars=mom)
        out.append(f"| {mom} down bars | {fmt(trades)} |")

    # Momentum + SL
    for mom in [2, 3]:
        for sl in [0.50, 0.75, 1.00]:
            trades = run_backtest(df, trading_days, min_dip=0.30, recovery_pct=0.33,
                                momentum_bars=mom, sl=sl)
            out.append(f"| {mom} down + SL=${sl} | {fmt(trades)} |")

    # Momentum + TP + SL
    for mom in [2, 3]:
        for tp in [1.00, 1.50, 2.00]:
            trades = run_backtest(df, trading_days, min_dip=0.30, recovery_pct=0.33,
                                momentum_bars=mom, tp=tp, sl=0.75)
            out.append(f"| {mom} down + TP=${tp} SL=$0.75 | {fmt(trades)} |")

    # ── Part 4: TP/SL grid (no momentum) ─────────────────────────────
    out.append("\n## Part 4: TP/SL Grid (min dip=$0.30, recovery=33%)\n")
    out.append("| TP | SL | Trades | Win% | Avg P&L | Total | Sharpe | Avg Hold | Entry Type | Exits |")
    out.append("|----|----| ------|------|---------|-------|--------|----------|------------|-------|")
    for tp in [0.50, 0.75, 1.00, 1.50, 2.00]:
        for sl in [0.25, 0.50, 0.75, 1.00]:
            trades = run_backtest(df, trading_days, min_dip=0.30, recovery_pct=0.33, tp=tp, sl=sl)
            out.append(f"| ${tp} | ${sl} | {fmt(trades)} |")

    # ── Part 5: Min dip sweep with best exit ──────────────────────────
    out.append("\n## Part 5: Min Dip Sweep (recovery=33%, best exits from above)\n")
    out.append("| Min Dip | Exit | Trades | Win% | Avg P&L | Total | Sharpe | Avg Hold | Entry Type | Exits |")
    out.append("|---------|------|--------|------|---------|-------|--------|----------|------------|-------|")
    for min_dip in [0.00, 0.20, 0.30, 0.50, 0.75, 1.00]:
        # Fixed 60s hold
        trades = run_backtest(df, trading_days, min_dip=min_dip, recovery_pct=0.33, fixed_hold=60)
        out.append(f"| ${min_dip:.2f} | Hold 60s | {fmt(trades)} |")
        # Momentum 3 bars + SL
        trades = run_backtest(df, trading_days, min_dip=min_dip, recovery_pct=0.33,
                            momentum_bars=3, sl=0.75)
        out.append(f"| ${min_dip:.2f} | 3down+SL$0.75 | {fmt(trades)} |")

    # ── Part 6: Day-by-day best config ────────────────────────────────
    out.append("\n## Part 6: Day-by-Day\n")

    # Pick the best config from above (will adjust after seeing results)
    trades = run_backtest(df, trading_days, min_dip=0.30, recovery_pct=0.33,
                         momentum_bars=3, sl=0.75)

    out.append(f"Config: min dip=$0.30, recovery=33%, exit=3 down bars OR SL=$0.75\n")
    out.append("| Date | Open | Entry | Type | Entry(s) | Dip$ | Exit | Reason | Hold | Stock P&L | Opt P&L | Peak | Trough | Cum |")
    out.append("|------|------|-------|------|----------|------|------|--------|------|-----------|---------|------|--------|-----|")

    cum = 0
    for t in trades:
        cum += t['opt_pnl']
        exit_price = t['entry_price'] + t['pnl_stock']
        out.append(f"| {t['date']} | ${t['open_price']:.2f} | ${t['entry_price']:.2f} | {t['entry_type']} | {t['entry_secs']:.0f}s | ${t['dip_size']:.2f} | ${exit_price:.2f} | {t['exit_reason']} | {t['exit_secs']:.0f}s | ${t['pnl_stock']:+.2f} | ${t['opt_pnl']:+.0f} | ${t['peak_pnl']:+.2f} | ${t['trough_pnl']:+.2f} | ${cum:+.0f} |")

    out.append(f"\n**Total: ${cum:+.0f}** over {len(trades)} trades")

    # MFE
    if trades:
        mfes = [t['peak_pnl'] for t in trades]
        out.append(f"\nMFE: avg ${mean(mfes):.2f}, ≥$0.50: {100*sum(1 for m in mfes if m >= 0.50)/len(mfes):.0f}%, ≥$1.00: {100*sum(1 for m in mfes if m >= 1.00)/len(mfes):.0f}%")
        out.append(f"Perfect exit: ${sum(opt_pnl(m) for m in mfes):+.0f}")

    # ── Write ─────────────────────────────────────────────────────────
    text = "\n".join(out) + "\n"
    with open(OUTPUT, 'w') as f:
        f.write(text)
    print(f"Results written to {OUTPUT}")
    print(text)


if __name__ == '__main__':
    main()
