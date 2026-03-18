#!/usr/bin/env python3
"""
Open Scalp — Indicator-Based Exit Analysis

Uses the best entry from open_scalp_analysis.py (wait_30s, puts-only focus),
then tests various indicator-based exits computed on 5s candle data:
  - EMA9 cross (close crosses against direction)
  - EMA20 cross
  - VWAP cross (cumulative intraday VWAP)
  - First red/green bar (reversal candle)
  - Price reclaim of 9:30 open
  - Momentum stall (3 consecutive bars against direction)
  - Combo: indicator exit + SL safety net

All exits have a hard time stop at 9:35:00.
"""

import os
import sys
import pandas as pd
import numpy as np
import pytz
from datetime import datetime, timedelta
from statistics import mean, median, stdev

ET = pytz.timezone('US/Eastern')

BASE = os.path.dirname(os.path.abspath(__file__))
_PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(BASE)))
PARQ_5S_DIR = os.path.join(_PROJ_ROOT, "trading_bot", "cache", "bars_highres", "5sec")
OUTPUT = os.path.join(BASE, "open-scalp-exits.md")

SYMBOL = "TSLA"
SPREAD_COST = 0.15
DELTA = 0.50
CONTRACT_MULT = 100
HARD_EXIT_TIME = "09:35:00"


def load_5s(symbol):
    fpath = os.path.join(PARQ_5S_DIR, f"{symbol.lower()}_5_secs_ib.parquet")
    df = pd.read_parquet(fpath).set_index('date').sort_index()
    print(f"Loaded {len(df):,} bars")
    return df


def opt_pnl(stock_pnl):
    return (stock_pnl * DELTA - SPREAD_COST) * CONTRACT_MULT


def fmt(val):
    return f"${val:+,.0f}" if abs(val) >= 1 else f"${val:+,.2f}"


def compute_ema(series, span):
    """EMA on a pandas Series."""
    return series.ewm(span=span, adjust=False).mean()


def compute_vwap(df_day):
    """Cumulative VWAP from 9:30. Requires 'close' and 'volume' columns."""
    tp = (df_day['high'] + df_day['low'] + df_day['close']) / 3
    cum_tp_vol = (tp * df_day['volume']).cumsum()
    cum_vol = df_day['volume'].cumsum()
    return cum_tp_vol / cum_vol.replace(0, np.nan)


def simulate_indicator_exit(day_bars, entry_time, entry_price, direction, sl,
                            exit_type, hard_exit_ts):
    """
    Bar-by-bar sim with indicator-based exit.

    exit_type: 'ema9', 'ema20', 'vwap', 'reversal_bar', 'open_reclaim',
               'momentum_stall', 'ema9+tp', 'vwap+trail'
    """
    post = day_bars.loc[day_bars.index > entry_time]
    max_secs = max(10, (hard_exit_ts - entry_time).total_seconds())

    # Pre-compute indicators on the full day (need history before entry)
    day_bars = day_bars.copy()
    day_bars['ema9'] = compute_ema(day_bars['close'], 9)
    day_bars['ema20'] = compute_ema(day_bars['close'], 20)
    day_bars['vwap'] = compute_vwap(day_bars)
    open_price = day_bars.iloc[0]['open']

    post = day_bars.loc[day_bars.index > entry_time]

    peak = 0.0
    trough = 0.0
    last_pnl = 0.0
    last_secs = 0.0
    t0 = post.index[0] if len(post) > 0 else None
    consec_against = 0
    prev_close = entry_price

    for idx, row in post.iterrows():
        if t0 is None:
            t0 = idx
        secs = (idx - t0).total_seconds() + 5
        if secs > max_secs:
            break

        if direction == 'long':
            pnl = row['close'] - entry_price
            best = row['high'] - entry_price
            worst = row['low'] - entry_price
        else:
            pnl = entry_price - row['close']
            best = entry_price - row['low']
            worst = entry_price - row['high']

        peak = max(peak, best)
        trough = min(trough, worst)
        last_pnl = pnl
        last_secs = secs

        # Always check SL first
        if worst <= -sl:
            return {'exit_secs': secs, 'exit_reason': 'SL', 'pnl_stock': -sl,
                    'peak_pnl': peak, 'trough_pnl': trough}

        # ── Indicator exits ──
        if exit_type == 'ema9':
            # Exit when close crosses EMA9 against direction
            if direction == 'long' and row['close'] < row['ema9'] and secs > 10:
                return {'exit_secs': secs, 'exit_reason': 'EMA9', 'pnl_stock': pnl,
                        'peak_pnl': peak, 'trough_pnl': trough}
            if direction == 'short' and row['close'] > row['ema9'] and secs > 10:
                return {'exit_secs': secs, 'exit_reason': 'EMA9', 'pnl_stock': pnl,
                        'peak_pnl': peak, 'trough_pnl': trough}

        elif exit_type == 'ema20':
            if direction == 'long' and row['close'] < row['ema20'] and secs > 15:
                return {'exit_secs': secs, 'exit_reason': 'EMA20', 'pnl_stock': pnl,
                        'peak_pnl': peak, 'trough_pnl': trough}
            if direction == 'short' and row['close'] > row['ema20'] and secs > 15:
                return {'exit_secs': secs, 'exit_reason': 'EMA20', 'pnl_stock': pnl,
                        'peak_pnl': peak, 'trough_pnl': trough}

        elif exit_type == 'vwap':
            if not np.isnan(row['vwap']):
                if direction == 'long' and row['close'] < row['vwap'] and secs > 10:
                    return {'exit_secs': secs, 'exit_reason': 'VWAP', 'pnl_stock': pnl,
                            'peak_pnl': peak, 'trough_pnl': trough}
                if direction == 'short' and row['close'] > row['vwap'] and secs > 10:
                    return {'exit_secs': secs, 'exit_reason': 'VWAP', 'pnl_stock': pnl,
                            'peak_pnl': peak, 'trough_pnl': trough}

        elif exit_type == 'reversal_bar':
            # Exit on first bar that closes against our direction
            if direction == 'long' and row['close'] < row['open'] and secs > 5:
                return {'exit_secs': secs, 'exit_reason': 'REV', 'pnl_stock': pnl,
                        'peak_pnl': peak, 'trough_pnl': trough}
            if direction == 'short' and row['close'] > row['open'] and secs > 5:
                return {'exit_secs': secs, 'exit_reason': 'REV', 'pnl_stock': pnl,
                        'peak_pnl': peak, 'trough_pnl': trough}

        elif exit_type == 'open_reclaim':
            # Exit if price reclaims the 9:30 open (momentum dead)
            if direction == 'long' and row['close'] < open_price and secs > 15:
                return {'exit_secs': secs, 'exit_reason': 'OPEN', 'pnl_stock': pnl,
                        'peak_pnl': peak, 'trough_pnl': trough}
            if direction == 'short' and row['close'] > open_price and secs > 15:
                return {'exit_secs': secs, 'exit_reason': 'OPEN', 'pnl_stock': pnl,
                        'peak_pnl': peak, 'trough_pnl': trough}

        elif exit_type == 'momentum_stall':
            # Exit after 3 consecutive bars closing against direction
            bar_against = False
            if direction == 'long' and row['close'] < prev_close:
                bar_against = True
            if direction == 'short' and row['close'] > prev_close:
                bar_against = True
            consec_against = consec_against + 1 if bar_against else 0
            if consec_against >= 3 and secs > 15:
                return {'exit_secs': secs, 'exit_reason': 'STALL', 'pnl_stock': pnl,
                        'peak_pnl': peak, 'trough_pnl': trough}

        elif exit_type == 'ema9+tp2':
            # Combo: EMA9 cross OR TP $2.00
            if best >= 2.00:
                return {'exit_secs': secs, 'exit_reason': 'TP', 'pnl_stock': 2.00,
                        'peak_pnl': peak, 'trough_pnl': trough}
            if direction == 'long' and row['close'] < row['ema9'] and secs > 10:
                return {'exit_secs': secs, 'exit_reason': 'EMA9', 'pnl_stock': pnl,
                        'peak_pnl': peak, 'trough_pnl': trough}
            if direction == 'short' and row['close'] > row['ema9'] and secs > 10:
                return {'exit_secs': secs, 'exit_reason': 'EMA9', 'pnl_stock': pnl,
                        'peak_pnl': peak, 'trough_pnl': trough}

        elif exit_type == 'vwap+tp2':
            if best >= 2.00:
                return {'exit_secs': secs, 'exit_reason': 'TP', 'pnl_stock': 2.00,
                        'peak_pnl': peak, 'trough_pnl': trough}
            if not np.isnan(row['vwap']):
                if direction == 'long' and row['close'] < row['vwap'] and secs > 10:
                    return {'exit_secs': secs, 'exit_reason': 'VWAP', 'pnl_stock': pnl,
                            'peak_pnl': peak, 'trough_pnl': trough}
                if direction == 'short' and row['close'] > row['vwap'] and secs > 10:
                    return {'exit_secs': secs, 'exit_reason': 'VWAP', 'pnl_stock': pnl,
                            'peak_pnl': peak, 'trough_pnl': trough}

        elif exit_type == 'ema9+trail':
            # EMA9 exit only after profit, else hold; + trail from peak
            trail_offset = 0.30
            if peak >= 0.30:
                trail_level = peak - trail_offset
                if pnl <= trail_level:
                    return {'exit_secs': secs, 'exit_reason': 'TRAIL', 'pnl_stock': max(trail_level, pnl),
                            'peak_pnl': peak, 'trough_pnl': trough}
            if direction == 'long' and row['close'] < row['ema9'] and pnl > 0 and secs > 10:
                return {'exit_secs': secs, 'exit_reason': 'EMA9', 'pnl_stock': pnl,
                        'peak_pnl': peak, 'trough_pnl': trough}
            if direction == 'short' and row['close'] > row['ema9'] and pnl > 0 and secs > 10:
                return {'exit_secs': secs, 'exit_reason': 'EMA9', 'pnl_stock': pnl,
                        'peak_pnl': peak, 'trough_pnl': trough}

        prev_close = row['close']

    # Time stop
    if t0 is not None and last_secs > 0:
        return {'exit_secs': last_secs, 'exit_reason': 'TIME', 'pnl_stock': last_pnl,
                'peak_pnl': peak, 'trough_pnl': trough}
    return None


def main():
    print("=== TSLA Open Scalp — Indicator Exit Analysis ===\n")

    df = load_5s(SYMBOL)
    trading_days = sorted(set(df.between_time('09:30', '15:59').index.date))
    print(f"{len(trading_days)} trading days\n")

    hard_exit_t = datetime.strptime(HARD_EXIT_TIME, "%H:%M:%S").time()

    # ── Collect entry data (wait_30s trigger) ──
    entries = []
    for date in trading_days:
        day_start = ET.localize(datetime.combine(date, datetime.strptime("09:30:00", "%H:%M:%S").time()))
        hard_exit_ts = ET.localize(datetime.combine(date, hard_exit_t))
        day_end = day_start + timedelta(hours=6, minutes=30)
        day_bars = df.loc[(df.index >= day_start) & (df.index < day_end)]
        if len(day_bars) < 60:
            continue

        # Wait 30s, check direction
        target = day_start + timedelta(seconds=30)
        entry_bars = day_bars.loc[(day_bars.index >= target) & (day_bars.index <= target + timedelta(seconds=10))]
        if len(entry_bars) == 0:
            continue

        bar = entry_bars.iloc[0]
        open_price = day_bars.iloc[0]['open']
        direction = 'long' if bar['close'] >= open_price else 'short'

        entries.append({
            'date': date,
            'direction': direction,
            'entry_price': bar['close'],
            'entry_time': entry_bars.index[0],
            'open_price': open_price,
            'day_bars': day_bars,
            'hard_exit_ts': hard_exit_ts,
        })

    lines = []
    lines.append("# TSLA Open Scalp — Indicator-Based Exit Comparison")
    lines.append(f"\n**Entry:** wait 30s, direction vs 9:30 open. **Hard exit:** {HARD_EXIT_TIME}")
    lines.append(f"**Data:** {len(entries)} days, 5-second candles")
    lines.append(f"**Assumptions:** Delta={DELTA}, Spread=${SPREAD_COST:.2f}")

    # ── Exit strategies to test ──
    exit_configs = [
        # (exit_type, sl, label)
        ('ema9',           1.00, 'EMA9 cross + $1 SL'),
        ('ema20',          1.00, 'EMA20 cross + $1 SL'),
        ('vwap',           1.00, 'VWAP cross + $1 SL'),
        ('reversal_bar',   1.00, 'First reversal bar + $1 SL'),
        ('open_reclaim',   1.00, 'Open reclaim + $1 SL'),
        ('momentum_stall', 1.00, '3-bar stall + $1 SL'),
        ('ema9+tp2',       1.00, 'EMA9 or TP $2 + $1 SL'),
        ('vwap+tp2',       1.00, 'VWAP or TP $2 + $1 SL'),
        ('ema9+trail',     1.00, 'EMA9 (profit only) + $0.30 trail + $1 SL'),
        # Tighter SL variants
        ('ema9',           0.50, 'EMA9 cross + $0.50 SL'),
        ('vwap',           0.50, 'VWAP cross + $0.50 SL'),
        ('ema9+tp2',       0.50, 'EMA9 or TP $2 + $0.50 SL'),
        ('vwap+tp2',       0.50, 'VWAP or TP $2 + $0.50 SL'),
        # Wider SL
        ('ema9+tp2',       1.50, 'EMA9 or TP $2 + $1.50 SL'),
        ('vwap+tp2',       1.50, 'VWAP or TP $2 + $1.50 SL'),
    ]

    # ── Compare: both directions, puts only ──
    for dir_label, dir_filter in [("Both Directions", None), ("Puts Only", 'short')]:
        lines.append(f"\n\n---\n## {dir_label}")
        lines.append("")
        lines.append("| Exit Strategy | SL | Trades | Win% | Avg P&L | Total | Sharpe | Avg Hold | Exit Breakdown |")
        lines.append("|---------------|----|--------|------|---------|-------|--------|----------|----------------|")

        # Baseline: fixed TP=$2/SL=$1
        baseline_pnls = []
        for e in entries:
            if dir_filter and e['direction'] != dir_filter:
                continue
            from open_scalp_analysis import simulate_trade
            post = e['day_bars'].loc[e['day_bars'].index > e['entry_time']]
            max_hold = max(10, (e['hard_exit_ts'] - e['entry_time']).total_seconds())
            r = simulate_trade(post, e['entry_price'], e['direction'], 2.00, 1.00, max_secs=max_hold)
            if r:
                baseline_pnls.append(opt_pnl(r['pnl_stock']))

        if baseline_pnls:
            n = len(baseline_pnls)
            w = sum(1 for p in baseline_pnls if p > 0)
            s = mean(baseline_pnls) / stdev(baseline_pnls) * (252**0.5) if n > 2 and stdev(baseline_pnls) > 0 else 0
            lines.append(
                f"| **Baseline: TP=$2 SL=$1** | $1.00 | {n} | {100*w/n:.0f}% | "
                f"{fmt(mean(baseline_pnls))} | {fmt(sum(baseline_pnls))} | {s:.1f} | — | — |"
            )

        for exit_type, sl, label in exit_configs:
            pnls = []
            exits = {}
            hold_times = []

            for e in entries:
                if dir_filter and e['direction'] != dir_filter:
                    continue

                r = simulate_indicator_exit(
                    e['day_bars'], e['entry_time'], e['entry_price'],
                    e['direction'], sl, exit_type, e['hard_exit_ts']
                )
                if r:
                    pnls.append(opt_pnl(r['pnl_stock']))
                    exits[r['exit_reason']] = exits.get(r['exit_reason'], 0) + 1
                    hold_times.append(r['exit_secs'])

            if not pnls or len(pnls) < 3:
                continue

            n = len(pnls)
            w = sum(1 for p in pnls if p > 0)
            total = sum(pnls)
            sharpe = mean(pnls) / stdev(pnls) * (252**0.5) if stdev(pnls) > 0 else 0
            avg_hold = mean(hold_times)

            # Exit breakdown string
            breakdown = ", ".join(f"{k}:{100*v/n:.0f}%" for k, v in sorted(exits.items()))

            lines.append(
                f"| {label} | ${sl:.2f} | {n} | {100*w/n:.0f}% | "
                f"{fmt(mean(pnls))} | {fmt(total)} | {sharpe:.1f} | {avg_hold:.0f}s | {breakdown} |"
            )

    # ── Day-by-day for best indicator exit ──
    lines.append("\n\n---\n## Day-by-Day: Best Indicator Exits (Puts Only)")
    lines.append("")

    # Run top 3 exits for puts and show side by side
    top_exits = [
        ('ema9+tp2', 1.00, 'EMA9/TP$2'),
        ('vwap+tp2', 1.00, 'VWAP/TP$2'),
        ('ema9+trail', 1.00, 'EMA9+trail'),
    ]

    header = "| Date | Dir | Entry |"
    divider = "|------|-----|-------|"
    for _, _, lbl in top_exits:
        header += f" {lbl} P&L | Exit |"
        divider += "------------|------|"
    header += " Baseline |"
    divider += "----------|"
    lines.append(header)
    lines.append(divider)

    for e in entries:
        if e['direction'] != 'short':
            continue

        row_str = f"| {e['date']} | PUT | ${e['entry_price']:.2f} |"

        for exit_type, sl, lbl in top_exits:
            r = simulate_indicator_exit(
                e['day_bars'], e['entry_time'], e['entry_price'],
                e['direction'], sl, exit_type, e['hard_exit_ts']
            )
            if r:
                p = opt_pnl(r['pnl_stock'])
                row_str += f" {fmt(p)} | {r['exit_reason']} {r['exit_secs']:.0f}s |"
            else:
                row_str += " — | — |"

        # Baseline
        from open_scalp_analysis import simulate_trade
        post = e['day_bars'].loc[e['day_bars'].index > e['entry_time']]
        max_hold = max(10, (e['hard_exit_ts'] - e['entry_time']).total_seconds())
        rb = simulate_trade(post, e['entry_price'], e['direction'], 2.00, 1.00, max_secs=max_hold)
        if rb:
            row_str += f" {fmt(opt_pnl(rb['pnl_stock']))} |"
        else:
            row_str += " — |"

        lines.append(row_str)

    report = "\n".join(lines)
    with open(OUTPUT, 'w') as f:
        f.write(report)
    print(report)
    print(f"\n\nWritten to {OUTPUT}")


if __name__ == '__main__':
    main()
