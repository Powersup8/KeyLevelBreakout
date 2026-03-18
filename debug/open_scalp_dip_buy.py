#!/usr/bin/env python3
"""
Open Scalp — Buy-the-Dip Strategy.

Always go LONG (buy call). Wait for TSLA to dip in the first 30s,
enter when it recovers X% from the low, exit on momentum fade or time stop.

Entry logic:
  1. Track low within first 30s
  2. Require minimum dip size (e.g., $0.30)
  3. Enter when price recovers recovery_pct of the dip (from low toward open)

Exit logic (tested variants):
  A. Momentum fade: 2 or 3 consecutive down 5s bars
  B. New low: price drops below entry price by SL amount
  C. Time-if-losing: if P&L < 0 at N seconds, exit
  D. Fixed TP/SL
  E. Combinations

Hard exit: 9:35:00
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
OUTPUT = os.path.join(BASE, "open-scalp-dip-buy.md")

SYMBOL = "TSLA"
SPREAD_COST = 0.15
DELTA = 0.50
CONTRACT_MULT = 100
HARD_EXIT_TIME = "09:35:00"
DIP_WINDOW_SECS = 30


def load_5s(symbol):
    fpath = os.path.join(PARQ_5S_DIR, f"{symbol.lower()}_5_secs_ib.parquet")
    df = pd.read_parquet(fpath).set_index('date').sort_index()
    return df


def opt_pnl(stock_pnl):
    return (stock_pnl * DELTA - SPREAD_COST) * CONTRACT_MULT


def find_dip_entry(day_bars, day_start, min_dip, recovery_pct):
    """
    Scan bars in first 30s for a dip. Once dip is established,
    watch for recovery_pct bounce from low toward open.

    Returns (entry_price, entry_time, dip_low, open_price) or None.
    """
    window_end = day_start + timedelta(seconds=DIP_WINDOW_SECS)
    # Extend scan window — dip happens in first 30s but recovery can be after
    scan_end = day_start + timedelta(seconds=120)
    scan_bars = day_bars.loc[(day_bars.index >= day_start) & (day_bars.index < scan_end)]

    if len(scan_bars) < 2:
        return None

    open_price = scan_bars.iloc[0]['open']
    running_low = open_price
    dip_established = False

    for idx, row in scan_bars.iterrows():
        secs = (idx - day_start).total_seconds()

        # Track low during dip window
        if secs <= DIP_WINDOW_SECS:
            if row['low'] < running_low:
                running_low = row['low']
            dip_size = open_price - running_low
            if dip_size >= min_dip:
                dip_established = True

        # Once dip established, look for recovery
        if dip_established:
            dip_size = open_price - running_low
            recovery_target = running_low + dip_size * recovery_pct

            # Check if this bar reaches the recovery target
            if row['high'] >= recovery_target:
                entry_price = recovery_target
                return entry_price, idx, running_low, open_price

    return None


def simulate_dip_trade(bars_after_entry, entry_price, max_secs,
                       tp=None, sl=None,
                       momentum_exit=None,  # 'down_2bars', 'down_3bars'
                       time_if_losing=None):  # exit at N secs if P&L < 0
    """Bar-by-bar sim, always LONG."""
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

        # Momentum exit: consecutive down bars
        if momentum_exit:
            if prev_close is not None and row['close'] < prev_close:
                consecutive_down += 1
            else:
                consecutive_down = 0

            n_bars = int(momentum_exit.split('_')[1].replace('bars', ''))
            if consecutive_down >= n_bars and secs >= 10:  # min 10s hold
                return {'exit_secs': secs, 'exit_reason': 'MOM',
                        'pnl_stock': pnl, 'peak_pnl': peak, 'trough_pnl': trough}

        # Time-if-losing exit
        if time_if_losing and secs >= time_if_losing and pnl < 0:
            return {'exit_secs': secs, 'exit_reason': 'TIMELOSS',
                    'pnl_stock': pnl, 'peak_pnl': peak, 'trough_pnl': trough}

        prev_close = row['close']

    # Time stop
    if t0 is not None and last_secs > 0:
        return {'exit_secs': last_secs, 'exit_reason': 'TIME',
                'pnl_stock': last_pnl, 'peak_pnl': peak, 'trough_pnl': trough}
    return None


def run_strategy(df, trading_days, min_dip, recovery_pct, tp, sl,
                 momentum_exit=None, time_if_losing=None, label=""):
    trades = []
    for date in trading_days:
        day_start = ET.localize(datetime.combine(date, datetime.strptime("09:30:00", "%H:%M:%S").time()))
        hard_exit_ts = ET.localize(datetime.combine(date, datetime.strptime(HARD_EXIT_TIME, "%H:%M:%S").time()))
        day_bars = df.loc[(df.index >= day_start) & (df.index < hard_exit_ts + timedelta(seconds=10))]
        if len(day_bars) < 6:
            continue

        result = find_dip_entry(day_bars, day_start, min_dip, recovery_pct)
        if result is None:
            continue

        entry_price, entry_time, dip_low, open_price = result
        remaining = day_bars.loc[day_bars.index > entry_time]
        if len(remaining) == 0:
            continue

        max_hold = (hard_exit_ts - entry_time).total_seconds()
        trade = simulate_dip_trade(remaining, entry_price, max_hold,
                                   tp=tp, sl=sl,
                                   momentum_exit=momentum_exit,
                                   time_if_losing=time_if_losing)
        if trade:
            trade['date'] = date
            trade['entry_price'] = entry_price
            trade['dip_low'] = dip_low
            trade['open_price'] = open_price
            trade['dip_size'] = open_price - dip_low
            trade['entry_secs'] = (entry_time - day_start).total_seconds()
            trade['opt_pnl'] = opt_pnl(trade['pnl_stock'])
            trades.append(trade)

    return trades


def fmt_trades(trades):
    if not trades:
        return "0", "—", "—", "—", "—", "—", "—"
    pnls = [t['opt_pnl'] for t in trades]
    wins = sum(1 for p in pnls if p > 0)
    total = sum(pnls)
    avg = mean(pnls)
    sh = (mean(pnls) / stdev(pnls)) * (len(pnls)**0.5) if len(pnls) > 1 and stdev(pnls) > 0 else 0
    reasons = {}
    for t in trades:
        reasons[t['exit_reason']] = reasons.get(t['exit_reason'], 0) + 1
    breakdown = ", ".join(f"{k}:{v}" for k, v in sorted(reasons.items()))
    return (f"{len(trades)}", f"{100*wins/len(trades):.0f}%", f"${avg:+.0f}",
            f"${total:+.0f}", f"{sh:.1f}", f"{mean(t['entry_secs'] for t in trades):.0f}s", breakdown)


def main():
    df = load_5s(SYMBOL)
    market = df.between_time('09:30', '15:59')
    trading_days = sorted(set(market.index.date))
    print(f"Loaded {len(df):,} bars, {len(trading_days)} trading days\n")

    out = []
    out.append("# TSLA Open Scalp — Buy-the-Dip Strategy\n")
    out.append(f"**Data:** {len(trading_days)} trading days, 5-second candles")
    out.append(f"**Concept:** Always LONG. Wait for dip in first 30s, enter on recovery bounce.")
    out.append(f"**Hard exit:** 9:35:00\n")

    # ── Part 1: How often does TSLA dip at the open? ──────────────────
    out.append("## Part 1: Dip Frequency at Open (first 30s)\n")
    out.append("| Min Dip | Days with Dip | % | Avg Dip Size | Avg Entry (secs) |")
    out.append("|---------|---------------|---|-------------|-----------------|")

    for min_dip in [0.20, 0.30, 0.50, 0.75, 1.00, 1.50]:
        entries = []
        for date in trading_days:
            day_start = ET.localize(datetime.combine(date, datetime.strptime("09:30:00", "%H:%M:%S").time()))
            hard_exit_ts = ET.localize(datetime.combine(date, datetime.strptime(HARD_EXIT_TIME, "%H:%M:%S").time()))
            day_bars = df.loc[(df.index >= day_start) & (df.index < hard_exit_ts + timedelta(seconds=10))]
            if len(day_bars) < 6:
                continue
            result = find_dip_entry(day_bars, day_start, min_dip, 0.35)
            if result:
                entry_price, entry_time, dip_low, open_price = result
                entries.append({
                    'dip_size': open_price - dip_low,
                    'entry_secs': (entry_time - day_start).total_seconds(),
                })
        n_dip = len(entries)
        if n_dip > 0:
            avg_dip = mean(e['dip_size'] for e in entries)
            avg_entry = mean(e['entry_secs'] for e in entries)
            out.append(f"| ${min_dip:.2f} | {n_dip}/{len(trading_days)} | {100*n_dip/len(trading_days):.0f}% | ${avg_dip:.2f} | {avg_entry:.0f}s |")
        else:
            out.append(f"| ${min_dip:.2f} | 0 | 0% | — | — |")

    # ── Part 2: Recovery % sweep ──────────────────────────────────────
    out.append("\n## Part 2: Recovery % Sweep (min dip=$0.50, TP=$1.50, SL=$0.75)\n")
    out.append("| Recovery % | Trades | Win% | Avg P&L | Total | Sharpe | Avg Entry | Exits |")
    out.append("|-----------|--------|------|---------|-------|--------|-----------|-------|")

    for rec_pct in [0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60]:
        trades = run_strategy(df, trading_days, min_dip=0.50, recovery_pct=rec_pct,
                             tp=1.50, sl=0.75)
        cols = fmt_trades(trades)
        out.append(f"| {rec_pct:.0%} | {' | '.join(cols)} |")

    # ── Part 3: TP/SL grid (best recovery %) ─────────────────────────
    out.append("\n## Part 3: TP/SL Grid (min dip=$0.50, recovery=35%)\n")
    out.append("| TP | SL | Trades | Win% | Avg P&L | Total | Sharpe | Avg Entry | Exits |")
    out.append("|----|----| ------|------|---------|-------|--------|-----------|-------|")

    for tp in [0.50, 0.75, 1.00, 1.50, 2.00]:
        for sl in [0.25, 0.50, 0.75, 1.00]:
            trades = run_strategy(df, trading_days, min_dip=0.50, recovery_pct=0.35,
                                 tp=tp, sl=sl)
            cols = fmt_trades(trades)
            out.append(f"| ${tp:.2f} | ${sl:.2f} | {' | '.join(cols)} |")

    # ── Part 4: Momentum exit variants ────────────────────────────────
    out.append("\n## Part 4: Momentum & Time-if-Losing Exits (min dip=$0.50, recovery=35%)\n")
    out.append("| Exit Type | Params | Trades | Win% | Avg P&L | Total | Sharpe | Avg Entry | Exits |")
    out.append("|-----------|--------|--------|------|---------|-------|--------|-----------|-------|")

    # Momentum only (no TP/SL)
    for mom in ['down_2bars', 'down_3bars']:
        for sl in [0.75, 1.00]:
            trades = run_strategy(df, trading_days, min_dip=0.50, recovery_pct=0.35,
                                 tp=None, sl=sl, momentum_exit=mom)
            cols = fmt_trades(trades)
            out.append(f"| Momentum | {mom} SL=${sl} | {' | '.join(cols)} |")

    # Time-if-losing only
    for til in [30, 45, 60, 70, 80, 90, 120]:
        for sl in [0.75, 1.00]:
            trades = run_strategy(df, trading_days, min_dip=0.50, recovery_pct=0.35,
                                 tp=2.00, sl=sl, time_if_losing=til)
            cols = fmt_trades(trades)
            out.append(f"| Time-if-losing | {til}s SL=${sl} | {' | '.join(cols)} |")

    # Momentum + TP
    for mom in ['down_2bars', 'down_3bars']:
        for tp in [1.00, 1.50, 2.00]:
            trades = run_strategy(df, trading_days, min_dip=0.50, recovery_pct=0.35,
                                 tp=tp, sl=0.75, momentum_exit=mom)
            cols = fmt_trades(trades)
            out.append(f"| Mom+TP | {mom} TP=${tp} SL=$0.75 | {' | '.join(cols)} |")

    # Momentum + time-if-losing
    for mom in ['down_2bars', 'down_3bars']:
        for til in [60, 80]:
            trades = run_strategy(df, trading_days, min_dip=0.50, recovery_pct=0.35,
                                 tp=2.00, sl=0.75, momentum_exit=mom, time_if_losing=til)
            cols = fmt_trades(trades)
            out.append(f"| Mom+TIL | {mom} TIL={til}s TP=$2 SL=$0.75 | {' | '.join(cols)} |")

    # ── Part 5: Min dip sweep ─────────────────────────────────────────
    out.append("\n## Part 5: Min Dip Sweep (recovery=35%, TP=$1.50, SL=$0.75)\n")
    out.append("| Min Dip | Trades | Win% | Avg P&L | Total | Sharpe | Avg Entry | Exits |")
    out.append("|---------|--------|------|---------|-------|--------|-----------|-------|")

    for min_dip in [0.20, 0.30, 0.40, 0.50, 0.75, 1.00, 1.50]:
        trades = run_strategy(df, trading_days, min_dip=min_dip, recovery_pct=0.35,
                             tp=1.50, sl=0.75)
        cols = fmt_trades(trades)
        out.append(f"| ${min_dip:.2f} | {' | '.join(cols)} |")

    # ── Part 6: Day-by-day best config ────────────────────────────────
    out.append("\n## Part 6: Day-by-Day — Best Config\n")

    # Run with a reasonable config to show day-by-day
    trades = run_strategy(df, trading_days, min_dip=0.50, recovery_pct=0.35,
                         tp=1.50, sl=0.75)

    out.append(f"Config: min dip=$0.50, recovery=35%, TP=$1.50, SL=$0.75\n")
    out.append("| Date | Open | Dip Low | Dip$ | Entry | Entry(s) | Exit | Reason | Hold | Stock P&L | Opt P&L | Peak | Trough | Cum |")
    out.append("|------|------|---------|------|-------|----------|------|--------|------|-----------|---------|------|--------|-----|")

    cum = 0
    for t in trades:
        cum += t['opt_pnl']
        out.append(f"| {t['date']} | ${t['open_price']:.2f} | ${t['dip_low']:.2f} | ${t['dip_size']:.2f} | ${t['entry_price']:.2f} | {t['entry_secs']:.0f}s | ${t['entry_price']+t['pnl_stock']:.2f} | {t['exit_reason']} | {t['exit_secs']:.0f}s | ${t['pnl_stock']:+.2f} | ${t['opt_pnl']:+.0f} | ${t['peak_pnl']:+.2f} | ${t['trough_pnl']:+.2f} | ${cum:+.0f} |")

    out.append(f"\n**Total: ${cum:+.0f}** over {len(trades)} trades")

    # ── Part 7: MFE ceiling ───────────────────────────────────────────
    out.append("\n\n## Part 7: MFE Ceiling (perfect exit)\n")
    if trades:
        mfes = [t['peak_pnl'] for t in trades]
        maes = [t['trough_pnl'] for t in trades]
        perfect_pnls = [opt_pnl(m) for m in mfes]
        out.append(f"- Avg MFE: ${mean(mfes):.2f}, Median: ${sorted(mfes)[len(mfes)//2]:.2f}")
        out.append(f"- Avg MAE: ${mean(maes):.2f}")
        out.append(f"- MFE ≥ $0.50: {100*sum(1 for m in mfes if m >= 0.50)/len(mfes):.0f}%")
        out.append(f"- MFE ≥ $1.00: {100*sum(1 for m in mfes if m >= 1.00)/len(mfes):.0f}%")
        out.append(f"- Perfect-exit total: ${sum(perfect_pnls):+.0f}")

    # ── Write ─────────────────────────────────────────────────────────
    text = "\n".join(out) + "\n"
    with open(OUTPUT, 'w') as f:
        f.write(text)
    print(f"Results written to {OUTPUT}")
    print(text)


if __name__ == '__main__':
    main()
