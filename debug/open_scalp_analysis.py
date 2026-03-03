#!/usr/bin/env python3
"""
Open Scalp Analysis v3: TSLA call/put at open with active management.

Entry: Anytime within the open window (default 9:30:00-9:31:30).
       Tries multiple entry triggers to find the best window.
Exit:  Active TP/SL/trailing stop, forced exit at max hold time.

Uses 5-second candle data for bar-by-bar simulation.
"""

import os
import sys
import pandas as pd
import numpy as np
import pytz
from datetime import datetime, timedelta
from statistics import mean, median, stdev

ET = pytz.timezone('US/Eastern')

# ── Paths ─────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
_PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(BASE)))
PARQ_5S_DIR = os.path.join(_PROJ_ROOT, "trading_bot", "cache", "bars_highres", "5sec")
OUTPUT = os.path.join(BASE, "open-scalp-results.md")

# ── Config ─────────────────────────────────────────────────────────────
SYMBOL = "TSLA"
SPREAD_COST = 0.15
DELTA = 0.50
CONTRACT_MULT = 100
MAX_HOLD_SECS = 300       # default; overridden dynamically by hard exit time
HARD_EXIT_TIME = "09:35:00"  # must be out by this time
ENTRY_WINDOW_SECS = 120   # entry within first 120s (9:30:00-9:32:00)


def load_5s_data(symbol):
    fname = f"{symbol.lower()}_5_secs_ib.parquet"
    fpath = os.path.join(PARQ_5S_DIR, fname)
    if not os.path.exists(fpath):
        print(f"ERROR: {fpath} not found")
        sys.exit(1)
    df = pd.read_parquet(fpath)
    df = df.set_index('date').sort_index()
    print(f"Loaded {len(df):,} bars, {df.index.min()} to {df.index.max()}")
    return df


def get_trading_days(df):
    market = df.between_time('09:30', '15:59')
    return sorted(set(market.index.date))


def simulate_trade(bars_after_entry, entry_price, direction, tp, sl,
                   trail_start=None, trail_offset=None, max_secs=MAX_HOLD_SECS):
    """
    Bar-by-bar sim. direction='long'/'short'.
    Returns dict with exit_secs, exit_reason, pnl_stock, peak_pnl, trough_pnl.
    """
    peak = 0.0
    trough = 0.0
    trail_stop = None
    last_pnl = 0.0
    last_secs = 0.0
    t0 = bars_after_entry.index[0] if len(bars_after_entry) > 0 else None

    for idx, row in bars_after_entry.iterrows():
        if t0 is None:
            t0 = idx
        secs = (idx - t0).total_seconds() + 5
        if secs > max_secs:
            break

        if direction == 'long':
            best = row['high'] - entry_price
            worst = row['low'] - entry_price
            pnl = row['close'] - entry_price
        else:
            best = entry_price - row['low']
            worst = entry_price - row['high']
            pnl = entry_price - row['close']

        peak = max(peak, best)
        trough = min(trough, worst)
        last_pnl = pnl
        last_secs = secs

        # Profit target
        if best >= tp:
            return {'exit_secs': secs, 'exit_reason': 'TP', 'pnl_stock': tp,
                    'peak_pnl': peak, 'trough_pnl': trough}
        # Stop loss
        if worst <= -sl:
            return {'exit_secs': secs, 'exit_reason': 'SL', 'pnl_stock': -sl,
                    'peak_pnl': peak, 'trough_pnl': trough}
        # Trailing stop
        if trail_start is not None and trail_offset is not None:
            if best >= trail_start:
                new_trail = peak - trail_offset
                if trail_stop is None or new_trail > trail_stop:
                    trail_stop = new_trail
            if trail_stop is not None and pnl <= trail_stop:
                return {'exit_secs': secs, 'exit_reason': 'TRAIL',
                        'pnl_stock': max(trail_stop, pnl), 'peak_pnl': peak, 'trough_pnl': trough}

    # Time stop — use last bar WITHIN the window, not end of day
    if t0 is not None and last_secs > 0:
        return {'exit_secs': last_secs, 'exit_reason': 'TIME',
                'pnl_stock': last_pnl, 'peak_pnl': peak, 'trough_pnl': trough}
    return None


def opt_pnl(stock_pnl):
    return (stock_pnl * DELTA - SPREAD_COST) * CONTRACT_MULT


def fmt(val):
    return f"${val:+,.0f}" if abs(val) >= 1 else f"${val:+,.2f}"


def find_entry(day_bars, window_start, window_end, trigger):
    """
    Find entry point within window using the given trigger.

    Triggers:
    - 'first_up_bar': enter at close of first bar where close > open
    - 'first_down_bar': enter at close of first bar where close < open
    - 'first_green_after_Ns': wait N seconds, then enter on first up bar
    - 'cum_up_Xbars': enter when X consecutive up bars seen
    - 'price_above_open': enter when price crosses above the 9:30 open
    - 'any_direction': enter on first bar that moves (up→long, down→short)
    - 'wait_Ns': just wait N seconds and enter at close of that bar
    - 'vwap_cross': enter when price crosses above VWAP (cumulative)

    Returns: (entry_price, direction, remaining_bars) or None
    """
    window = day_bars.loc[(day_bars.index >= window_start) & (day_bars.index <= window_end)]
    if len(window) == 0:
        return None

    open_price = day_bars.iloc[0]['open']  # 9:30 open

    if trigger == 'first_up_bar':
        for i, (idx, row) in enumerate(window.iterrows()):
            if row['close'] > row['open']:
                remaining = day_bars.loc[day_bars.index > idx]
                return row['close'], 'long', remaining
        return None

    elif trigger == 'first_down_bar':
        for i, (idx, row) in enumerate(window.iterrows()):
            if row['close'] < row['open']:
                remaining = day_bars.loc[day_bars.index > idx]
                return row['close'], 'short', remaining
        return None

    elif trigger == 'any_direction':
        for i, (idx, row) in enumerate(window.iterrows()):
            if row['close'] > row['open']:
                remaining = day_bars.loc[day_bars.index > idx]
                return row['close'], 'long', remaining
            elif row['close'] < row['open']:
                remaining = day_bars.loc[day_bars.index > idx]
                return row['close'], 'short', remaining
        return None

    elif trigger.startswith('wait_'):
        wait_secs = int(trigger.split('_')[1].replace('s', ''))
        target = window_start + timedelta(seconds=wait_secs)
        bars_at = day_bars.loc[(day_bars.index >= target) & (day_bars.index <= target + timedelta(seconds=10))]
        if len(bars_at) == 0:
            return None
        bar = bars_at.iloc[0]
        direction = 'long' if bar['close'] >= open_price else 'short'
        remaining = day_bars.loc[day_bars.index > bars_at.index[0]]
        return bar['close'], direction, remaining

    elif trigger == 'price_above_open':
        for i, (idx, row) in enumerate(window.iterrows()):
            if row['close'] > open_price:
                remaining = day_bars.loc[day_bars.index > idx]
                return row['close'], 'long', remaining
        return None

    elif trigger == 'price_below_open':
        for i, (idx, row) in enumerate(window.iterrows()):
            if row['close'] < open_price:
                remaining = day_bars.loc[day_bars.index > idx]
                return row['close'], 'short', remaining
        return None

    elif trigger == 'price_cross_open':
        # Enter long if crosses above open, short if below
        for i, (idx, row) in enumerate(window.iterrows()):
            if row['close'] > open_price:
                remaining = day_bars.loc[day_bars.index > idx]
                return row['close'], 'long', remaining
            elif row['close'] < open_price:
                remaining = day_bars.loc[day_bars.index > idx]
                return row['close'], 'short', remaining
        return None

    elif trigger.startswith('cum_up_'):
        n_bars_needed = int(trigger.split('_')[2].replace('bars', ''))
        consec = 0
        for i, (idx, row) in enumerate(window.iterrows()):
            if row['close'] > row['open']:
                consec += 1
            else:
                consec = 0
            if consec >= n_bars_needed:
                remaining = day_bars.loc[day_bars.index > idx]
                return row['close'], 'long', remaining
        return None

    elif trigger == 'biggest_bar':
        # Find the bar with the biggest absolute move in the window, trade in its direction
        if len(window) == 0:
            return None
        moves = (window['close'] - window['open']).abs()
        best_idx = moves.idxmax()
        bar = window.loc[best_idx]
        direction = 'long' if bar['close'] > bar['open'] else 'short'
        remaining = day_bars.loc[day_bars.index > best_idx]
        return bar['close'], direction, remaining

    return None


def run_strategy(df, trading_days, trigger, tp, sl, trail_start=None, trail_offset=None,
                 window_offset_s=0, window_duration_s=ENTRY_WINDOW_SECS, only_direction=None):
    """Run a full strategy across all days. only_direction='long'/'short' to filter.
    Max hold = time from entry until HARD_EXIT_TIME (default 9:35:00)."""
    hard_exit_t = datetime.strptime(HARD_EXIT_TIME, "%H:%M:%S").time()
    trades = []
    for date in trading_days:
        day_start = ET.localize(datetime.combine(date, datetime.strptime("09:30:00", "%H:%M:%S").time()))
        hard_exit_ts = ET.localize(datetime.combine(date, hard_exit_t))
        day_end = day_start + timedelta(hours=6, minutes=30)
        day_bars = df.loc[(df.index >= day_start) & (df.index < day_end)]
        if len(day_bars) < 30:
            continue

        w_start = day_start + timedelta(seconds=window_offset_s)
        w_end = w_start + timedelta(seconds=window_duration_s)

        entry = find_entry(day_bars, w_start, w_end, trigger)
        if entry is None:
            continue

        entry_price, direction, remaining = entry

        if only_direction and direction != only_direction:
            continue

        # Dynamic max hold: time remaining until hard exit
        entry_time = remaining.index[0] if len(remaining) > 0 else w_end
        max_hold = max(10, (hard_exit_ts - entry_time).total_seconds())

        result = simulate_trade(remaining, entry_price, direction, tp, sl,
                                trail_start, trail_offset, max_secs=max_hold)
        if result is None:
            continue

        trades.append({
            'date': date,
            'direction': direction,
            'entry_price': entry_price,
            'open_price': day_bars.iloc[0]['open'],
            **result,
        })

    return trades


def summarize(trades, label=""):
    """Return summary dict for a set of trades."""
    if not trades:
        return None
    pnls = [opt_pnl(t['pnl_stock']) for t in trades]
    wins = sum(1 for p in pnls if p > 0)
    n = len(pnls)
    exits = {}
    for t in trades:
        exits[t['exit_reason']] = exits.get(t['exit_reason'], 0) + 1
    return {
        'label': label,
        'n': n,
        'win_pct': 100 * wins / n,
        'avg_pnl': mean(pnls),
        'total_pnl': sum(pnls),
        'sharpe': mean(pnls) / stdev(pnls) * (252**0.5) if n > 2 and stdev(pnls) > 0 else 0,
        'best': max(pnls),
        'worst': min(pnls),
        'avg_hold': mean(t['exit_secs'] for t in trades),
        'exits': exits,
    }


def main():
    print("=== TSLA Open Scalp v3 — Finding the Best Window ===\n")

    df = load_5s_data(SYMBOL)
    trading_days = get_trading_days(df)
    print(f"{len(trading_days)} trading days: {trading_days[0]} to {trading_days[-1]}\n")

    lines = []
    lines.append("# TSLA Open Scalp v3 — Finding the Best Entry & Exit")
    lines.append(f"\n**Concept:** Buy call/put within first 120s, active management, must exit by {HARD_EXIT_TIME}")
    lines.append(f"**Data:** {len(trading_days)} trading days, 5-second candle data")
    lines.append(f"**Assumptions:** Delta={DELTA}, Spread=${SPREAD_COST:.2f}, 1 contract")
    lines.append(f"**Date range:** {trading_days[0]} to {trading_days[-1]}")

    # ══════════════════════════════════════════════════════════════════
    # PART 1: Find best ENTRY TRIGGER
    # ══════════════════════════════════════════════════════════════════
    lines.append("\n\n---\n## Part 1: Entry Trigger Comparison")
    lines.append(f"Fixed exit: TP=$0.75, SL=$0.50. Entry: first {ENTRY_WINDOW_SECS}s. Hard exit: {HARD_EXIT_TIME}")
    lines.append("")
    lines.append("| Trigger | Trades | Win% | Avg P&L | Total | Sharpe | Avg Hold | TP% | SL% | TIME% |")
    lines.append("|---------|--------|------|---------|-------|--------|----------|-----|-----|-------|")

    triggers = [
        'any_direction',
        'first_up_bar',
        'first_down_bar',
        'price_cross_open',
        'cum_up_2bars',
        'cum_up_3bars',
        'wait_5s',
        'wait_10s',
        'wait_15s',
        'wait_30s',
        'wait_60s',
        'wait_90s',
        'wait_120s',
        'wait_180s',
        'wait_240s',
        'wait_300s',
        'biggest_bar',
    ]

    best_trigger = None
    best_trigger_total = -999999

    for trigger in triggers:
        trades = run_strategy(df, trading_days, trigger, tp=0.75, sl=0.50)
        s = summarize(trades, trigger)
        if not s:
            continue

        if s['total_pnl'] > best_trigger_total:
            best_trigger_total = s['total_pnl']
            best_trigger = trigger

        ex = s['exits']
        lines.append(
            f"| {trigger} | {s['n']} | {s['win_pct']:.0f}% | {fmt(s['avg_pnl'])} | "
            f"{fmt(s['total_pnl'])} | {s['sharpe']:.1f} | {s['avg_hold']:.0f}s | "
            f"{100*ex.get('TP',0)/s['n']:.0f}% | {100*ex.get('SL',0)/s['n']:.0f}% | "
            f"{100*ex.get('TIME',0)/s['n']:.0f}% |"
        )

    lines.append(f"\n**Best trigger: `{best_trigger}`** ({fmt(best_trigger_total)} total)")

    # ══════════════════════════════════════════════════════════════════
    # PART 2: Find best ENTRY WINDOW
    # ══════════════════════════════════════════════════════════════════
    lines.append("\n\n---\n## Part 2: Entry Window Optimization")
    lines.append(f"Fixed trigger: `{best_trigger}`. Fixed exit: TP=$0.75, SL=$0.50")
    lines.append("")
    lines.append("| Window Start | Duration | Trades | Win% | Avg P&L | Total | Sharpe |")
    lines.append("|-------------|----------|--------|------|---------|-------|--------|")

    best_window = None
    best_window_total = -999999

    for offset in [0, 5, 10, 15, 30, 60, 90, 120, 180, 240]:
        for duration in [30, 60, 90, 120, 180, 300]:
            trades = run_strategy(df, trading_days, best_trigger, tp=0.75, sl=0.50,
                                  window_offset_s=offset, window_duration_s=duration)
            s = summarize(trades)
            if not s or s['n'] < 10:
                continue

            mins, secs = divmod(offset, 60)
            start_str = f"9:{30+mins}:{secs:02d}"

            if s['total_pnl'] > best_window_total:
                best_window_total = s['total_pnl']
                best_window = (offset, duration)

            lines.append(
                f"| {start_str} | {duration}s | {s['n']} | {s['win_pct']:.0f}% | "
                f"{fmt(s['avg_pnl'])} | {fmt(s['total_pnl'])} | {s['sharpe']:.1f} |"
            )

    if best_window:
        bo, bd = best_window
        bm, bs = divmod(bo, 60)
        bw_str = f"9:{30+bm}:{bs:02d}"
        lines.append(f"\n**Best window: {bw_str} + {bd}s** ({fmt(best_window_total)} total)")
    else:
        bo, bd = 0, 300
        bw_str = "9:30:00"

    # ══════════════════════════════════════════════════════════════════
    # PART 3: Find best TP/SL with best trigger + window
    # ══════════════════════════════════════════════════════════════════
    lines.append("\n\n---\n## Part 3: Exit Optimization (TP/SL Grid)")
    lines.append(f"Trigger: `{best_trigger}`, Window: {bw_str}+{bd}s")
    lines.append("")
    lines.append("| TP | SL | Win% | Avg P&L | Total | Sharpe | Avg Hold | TP% | SL% | TIME% |")
    lines.append("|----|----| -----|---------|-------|--------|----------|-----|-----|-------|")

    tp_sl_combos = [
        (0.25, 0.15), (0.25, 0.25), (0.25, 0.50),
        (0.50, 0.25), (0.50, 0.50), (0.50, 0.75),
        (0.75, 0.25), (0.75, 0.50), (0.75, 0.75), (0.75, 1.00),
        (1.00, 0.50), (1.00, 0.75), (1.00, 1.00),
        (1.50, 0.50), (1.50, 0.75), (1.50, 1.00),
        (2.00, 0.75), (2.00, 1.00), (2.00, 1.50),
    ]

    best_exit = None
    best_exit_total = -999999

    for tp, sl in tp_sl_combos:
        trades = run_strategy(df, trading_days, best_trigger, tp=tp, sl=sl,
                              window_offset_s=bo, window_duration_s=bd)
        s = summarize(trades)
        if not s:
            continue

        if s['total_pnl'] > best_exit_total:
            best_exit_total = s['total_pnl']
            best_exit = (tp, sl)

        ex = s['exits']
        lines.append(
            f"| ${tp:.2f} | ${sl:.2f} | {s['win_pct']:.0f}% | {fmt(s['avg_pnl'])} | "
            f"{fmt(s['total_pnl'])} | {s['sharpe']:.1f} | {s['avg_hold']:.0f}s | "
            f"{100*ex.get('TP',0)/s['n']:.0f}% | {100*ex.get('SL',0)/s['n']:.0f}% | "
            f"{100*ex.get('TIME',0)/s['n']:.0f}% |"
        )

    if best_exit:
        btp, bsl = best_exit
    else:
        btp, bsl = 0.75, 0.50

    lines.append(f"\n**Best exit: TP=${btp:.2f}, SL=${bsl:.2f}** ({fmt(best_exit_total)} total)")

    # ══════════════════════════════════════════════════════════════════
    # PART 4: Trailing stop variants with best trigger + window
    # ══════════════════════════════════════════════════════════════════
    lines.append("\n\n---\n## Part 4: Trailing Stop Variants")
    lines.append(f"Trigger: `{best_trigger}`, Window: {bw_str}+{bd}s")
    lines.append("")
    lines.append("| SL | Trail Start | Trail Offset | Win% | Avg P&L | Total | Sharpe | TRAIL% | SL% | TIME% |")
    lines.append("|----|-------------|------------- |------|---------|-------|--------|--------|-----|-------|")

    trail_combos = [
        (0.25, 0.15, 0.10), (0.25, 0.20, 0.15),
        (0.50, 0.20, 0.15), (0.50, 0.30, 0.20), (0.50, 0.50, 0.25),
        (0.75, 0.30, 0.20), (0.75, 0.50, 0.25), (0.75, 0.50, 0.30),
        (1.00, 0.50, 0.25), (1.00, 0.50, 0.30), (1.00, 0.75, 0.40),
    ]

    best_trail = None
    best_trail_total = -999999

    for sl, ts, to in trail_combos:
        trades = run_strategy(df, trading_days, best_trigger, tp=999, sl=sl,
                              trail_start=ts, trail_offset=to,
                              window_offset_s=bo, window_duration_s=bd)
        s = summarize(trades)
        if not s:
            continue

        if s['total_pnl'] > best_trail_total:
            best_trail_total = s['total_pnl']
            best_trail = (sl, ts, to)

        ex = s['exits']
        lines.append(
            f"| ${sl:.2f} | ${ts:.2f} | ${to:.2f} | {s['win_pct']:.0f}% | "
            f"{fmt(s['avg_pnl'])} | {fmt(s['total_pnl'])} | {s['sharpe']:.1f} | "
            f"{100*ex.get('TRAIL',0)/s['n']:.0f}% | {100*ex.get('SL',0)/s['n']:.0f}% | "
            f"{100*ex.get('TIME',0)/s['n']:.0f}% |"
        )

    # ══════════════════════════════════════════════════════════════════
    # PART 5: MFE ceiling — what's the theoretical max?
    # ══════════════════════════════════════════════════════════════════
    lines.append("\n\n---\n## Part 5: Opportunity Ceiling (Perfect Exit)")
    lines.append(f"Using `{best_trigger}` trigger. What's the MFE within 120s?")
    lines.append("")

    trades = run_strategy(df, trading_days, best_trigger, tp=999, sl=999,
                          window_offset_s=bo, window_duration_s=bd)
    if trades:
        mfes = [t['peak_pnl'] for t in trades]
        maes = [abs(t['trough_pnl']) for t in trades]
        pct_50c = 100 * sum(1 for m in mfes if m >= 0.50) / len(mfes)
        pct_1 = 100 * sum(1 for m in mfes if m >= 1.00) / len(mfes)
        pct_2 = 100 * sum(1 for m in mfes if m >= 2.00) / len(mfes)

        lines.append(f"- **MFE:** avg ${mean(mfes):.2f}, median ${median(mfes):.2f}, max ${max(mfes):.2f}")
        lines.append(f"- **MAE:** avg ${mean(maes):.2f}, median ${median(maes):.2f}, max ${max(maes):.2f}")
        lines.append(f"- MFE ≥ $0.50: **{pct_50c:.0f}%** | ≥ $1.00: **{pct_1:.0f}%** | ≥ $2.00: **{pct_2:.0f}%**")
        lines.append(f"- Perfect-exit P&L: {fmt(sum(opt_pnl(m) for m in mfes))} total, {fmt(opt_pnl(mean(mfes)))} avg")

    # ══════════════════════════════════════════════════════════════════
    # PART 6: Day-by-day with best config
    # ══════════════════════════════════════════════════════════════════
    lines.append("\n\n---\n## Part 6: Day-by-Day — Best Configuration")
    lines.append(f"Trigger: `{best_trigger}`, Window: {bw_str}+{bd}s, TP=${btp:.2f}, SL=${bsl:.2f}")
    lines.append("")
    lines.append("| Date | Dir | Entry | Exit$ | Reason | Hold | Stock P&L | Call P&L | Peak | Trough | Cum P&L |")
    lines.append("|------|-----|-------|-------|--------|------|-----------|---------|------|--------|---------|")

    trades = run_strategy(df, trading_days, best_trigger, tp=btp, sl=bsl,
                          window_offset_s=bo, window_duration_s=bd)

    cumulative = 0
    for t in trades:
        p = opt_pnl(t['pnl_stock'])
        cumulative += p
        dir_label = "CALL" if t['direction'] == 'long' else "PUT"
        exit_price = t['entry_price'] + t['pnl_stock'] * (1 if t['direction'] == 'long' else -1)
        lines.append(
            f"| {t['date']} | {dir_label} | ${t['entry_price']:.2f} | ${exit_price:.2f} | "
            f"{t['exit_reason']} | {t['exit_secs']:.0f}s | ${t['pnl_stock']:+.2f} | "
            f"{fmt(p)} | ${t['peak_pnl']:.2f} | ${t['trough_pnl']:.2f} | {fmt(cumulative)} |"
        )

    lines.append(f"\n**Cumulative: {fmt(cumulative)}** over {len(trades)} trades ({len(trading_days)} days)")

    # ══════════════════════════════════════════════════════════════════
    # SUMMARY
    # ══════════════════════════════════════════════════════════════════
    # ══════════════════════════════════════════════════════════════════
    # PART 7: CALLS ONLY — bullish entries only
    # ══════════════════════════════════════════════════════════════════
    lines.append("\n\n---\n## Part 7: CALLS ONLY (Bullish Entries)")
    lines.append("Skip bearish days entirely — only buy calls when first move is up.")
    lines.append("")

    # 7a: Trigger comparison (calls only)
    lines.append("### 7a) Trigger Comparison (calls only)")
    lines.append("| Trigger | Trades | Win% | Avg P&L | Total | Sharpe | TP% | SL% | TIME% |")
    lines.append("|---------|--------|------|---------|-------|--------|-----|-----|-------|")

    call_triggers = ['first_up_bar', 'price_above_open', 'cum_up_2bars',
                     'wait_5s', 'wait_10s', 'wait_15s', 'wait_30s', 'wait_60s',
                     'wait_90s', 'wait_120s', 'wait_180s', 'wait_240s', 'wait_300s']
    best_call_trigger = None
    best_call_trigger_total = -999999

    for trigger in call_triggers:
        trades = run_strategy(df, trading_days, trigger, tp=0.75, sl=0.50,
                              only_direction='long')
        s = summarize(trades, trigger)
        if not s or s['n'] < 3:
            continue
        if s['total_pnl'] > best_call_trigger_total:
            best_call_trigger_total = s['total_pnl']
            best_call_trigger = trigger
        ex = s['exits']
        lines.append(
            f"| {trigger} | {s['n']} | {s['win_pct']:.0f}% | {fmt(s['avg_pnl'])} | "
            f"{fmt(s['total_pnl'])} | {s['sharpe']:.1f} | "
            f"{100*ex.get('TP',0)/s['n']:.0f}% | {100*ex.get('SL',0)/s['n']:.0f}% | "
            f"{100*ex.get('TIME',0)/s['n']:.0f}% |"
        )

    if not best_call_trigger:
        best_call_trigger = 'wait_30s'
    lines.append(f"\n**Best call trigger: `{best_call_trigger}`**")

    # 7b: TP/SL grid (calls only, best trigger)
    lines.append("")
    lines.append(f"### 7b) TP/SL Grid — Calls Only, `{best_call_trigger}`")
    lines.append("| TP | SL | Trades | Win% | Avg P&L | Total | Sharpe | Avg Hold | TP% | SL% | TIME% |")
    lines.append("|----|----| ------|------|---------|-------|--------|----------|-----|-----|-------|")

    best_call_exit = None
    best_call_exit_total = -999999

    for tp, sl in tp_sl_combos:
        trades = run_strategy(df, trading_days, best_call_trigger, tp=tp, sl=sl,
                              window_offset_s=bo, window_duration_s=bd, only_direction='long')
        s = summarize(trades)
        if not s:
            continue
        if s['total_pnl'] > best_call_exit_total:
            best_call_exit_total = s['total_pnl']
            best_call_exit = (tp, sl)
        ex = s['exits']
        lines.append(
            f"| ${tp:.2f} | ${sl:.2f} | {s['n']} | {s['win_pct']:.0f}% | "
            f"{fmt(s['avg_pnl'])} | {fmt(s['total_pnl'])} | {s['sharpe']:.1f} | {s['avg_hold']:.0f}s | "
            f"{100*ex.get('TP',0)/s['n']:.0f}% | {100*ex.get('SL',0)/s['n']:.0f}% | "
            f"{100*ex.get('TIME',0)/s['n']:.0f}% |"
        )

    if best_call_exit:
        ctp, csl = best_call_exit
    else:
        ctp, csl = 0.75, 0.50

    lines.append(f"\n**Best call exit: TP=${ctp:.2f}, SL=${csl:.2f}** ({fmt(best_call_exit_total)})")

    # 7c: Day-by-day (calls only, best config)
    lines.append("")
    lines.append(f"### 7c) Day-by-Day — Calls Only, `{best_call_trigger}`, TP=${ctp:.2f}, SL=${csl:.2f}")
    lines.append("| Date | Entry | Exit$ | Reason | Hold | Stock P&L | Call P&L | Peak | Trough | Cum P&L |")
    lines.append("|------|-------|-------|--------|------|-----------|---------|------|--------|---------|")

    call_trades = run_strategy(df, trading_days, best_call_trigger, tp=ctp, sl=csl,
                               window_offset_s=bo, window_duration_s=bd, only_direction='long')
    cum = 0
    for t in call_trades:
        p = opt_pnl(t['pnl_stock'])
        cum += p
        exit_price = t['entry_price'] + t['pnl_stock']
        lines.append(
            f"| {t['date']} | ${t['entry_price']:.2f} | ${exit_price:.2f} | "
            f"{t['exit_reason']} | {t['exit_secs']:.0f}s | ${t['pnl_stock']:+.2f} | "
            f"{fmt(p)} | ${t['peak_pnl']:.2f} | ${t['trough_pnl']:.2f} | {fmt(cum)} |"
        )

    lines.append(f"\n**Calls only cumulative: {fmt(cum)}** over {len(call_trades)} trades")

    # 7d: MFE ceiling for calls only
    call_ceiling = run_strategy(df, trading_days, best_call_trigger, tp=999, sl=999,
                                window_offset_s=bo, window_duration_s=bd, only_direction='long')
    if call_ceiling:
        mfes = [t['peak_pnl'] for t in call_ceiling]
        maes = [abs(t['trough_pnl']) for t in call_ceiling]
        lines.append(f"\n**Opportunity ceiling (perfect exit):** {len(call_ceiling)} trades, "
                     f"avg MFE ${mean(mfes):.2f}, avg MAE ${mean(maes):.2f}, "
                     f"perfect total {fmt(sum(opt_pnl(m) for m in mfes))}")

    # 7e: Comparison — calls vs puts vs both
    lines.append("")
    lines.append("### 7e) Head-to-Head: Calls vs Puts vs Both")
    lines.append(f"Using `{best_trigger}`, TP=${btp:.2f}, SL=${bsl:.2f}")
    lines.append("| Direction | Trades | Win% | Avg P&L | Total | Sharpe |")
    lines.append("|-----------|--------|------|---------|-------|--------|")

    for dir_label, dir_filter in [("Calls only", 'long'), ("Puts only", 'short'), ("Both", None)]:
        trades = run_strategy(df, trading_days, best_trigger, tp=btp, sl=bsl,
                              window_offset_s=bo, window_duration_s=bd, only_direction=dir_filter)
        s = summarize(trades)
        if s:
            lines.append(f"| {dir_label} | {s['n']} | {s['win_pct']:.0f}% | {fmt(s['avg_pnl'])} | {fmt(s['total_pnl'])} | {s['sharpe']:.1f} |")

    lines.append("\n\n---\n## Summary — Best Configuration Found")
    lines.append(f"- **Entry trigger:** `{best_trigger}`")
    lines.append(f"- **Entry window:** {bw_str} + {bd}s")
    lines.append(f"- **Exit (fixed TP/SL):** TP=${btp:.2f}, SL=${bsl:.2f} → {fmt(best_exit_total)} total")
    if best_trail:
        btsl, btts, btto = best_trail
        lines.append(f"- **Exit (trailing):** SL=${btsl:.2f}, trail start=${btts:.2f}, offset=${btto:.2f} → {fmt(best_trail_total)} total")
    lines.append(f"- **Sample size:** {len(trading_days)} days — small, results may not generalize")
    lines.append(f"- **Real caveats:** spreads at 9:30 wider ($0.30-0.50+), 0DTE IV crush, slippage")
    lines.append(f"- **Per-trade risk:** SL=${bsl:.2f} × delta × 100 = ${bsl * DELTA * CONTRACT_MULT:.0f}/contract")

    report = "\n".join(lines)
    with open(OUTPUT, 'w') as f:
        f.write(report)

    print(report)
    print(f"\n\nWritten to {OUTPUT}")


if __name__ == '__main__':
    main()
