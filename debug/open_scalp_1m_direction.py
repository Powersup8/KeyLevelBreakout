#!/usr/bin/env python3
"""
Compare 30s direction vs 1m candle direction at TSLA open.
Also re-run the strategy using 1m close as direction signal.

Questions answered:
1. How often does TSLA close the 1st 1m candle bullish vs bearish?
2. How often does 30s direction disagree with 1m direction?
3. What's the intra-bar path? (dip first but close bullish, etc.)
4. Does using 1m direction improve the strategy?
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
OUTPUT = os.path.join(BASE, "open-scalp-1m-direction.md")

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


def simulate_trade(bars_after_entry, entry_price, direction, tp, sl, max_secs):
    peak = trough = last_pnl = 0.0
    last_secs = 0
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

        if best >= tp:
            return {'exit_secs': secs, 'exit_reason': 'TP', 'pnl_stock': tp,
                    'peak_pnl': peak, 'trough_pnl': trough}
        if worst <= -sl:
            return {'exit_secs': secs, 'exit_reason': 'SL', 'pnl_stock': -sl,
                    'peak_pnl': peak, 'trough_pnl': trough}

    if t0 is not None and last_secs > 0:
        return {'exit_secs': last_secs, 'exit_reason': 'TIME',
                'pnl_stock': last_pnl, 'peak_pnl': peak, 'trough_pnl': trough}
    return None


def main():
    df = load_5s(SYMBOL)
    market = df.between_time('09:30', '15:59')
    trading_days = sorted(set(market.index.date))
    print(f"Loaded {len(df):,} bars, {len(trading_days)} trading days")

    out = []
    out.append("# TSLA Open Scalp — 30s vs 1m Direction Analysis\n")
    out.append(f"**Data:** {len(trading_days)} trading days, 5-second candles\n")

    # ── Part 1: Direction comparison ──────────────────────────────────
    rows = []
    for date in trading_days:
        day_start = ET.localize(datetime.combine(date, datetime.strptime("09:30:00", "%H:%M:%S").time()))
        day_bars = df.loc[(df.index >= day_start) & (df.index < day_start + timedelta(minutes=5))]

        if len(day_bars) < 12:  # need at least 1 minute of data
            continue

        open_price = day_bars.iloc[0]['open']

        # 30s direction (bar at ~9:30:30)
        t30 = day_start + timedelta(seconds=30)
        bars_30 = day_bars.loc[(day_bars.index >= t30) & (day_bars.index <= t30 + timedelta(seconds=5))]
        if len(bars_30) == 0:
            continue
        close_30s = bars_30.iloc[0]['close']
        dir_30s = 'BULL' if close_30s >= open_price else 'BEAR'

        # 1m direction (last bar before 9:31:00)
        t1m = day_start + timedelta(seconds=55)
        bars_1m = day_bars.loc[(day_bars.index >= t1m) & (day_bars.index <= t1m + timedelta(seconds=10))]
        if len(bars_1m) == 0:
            continue
        close_1m = bars_1m.iloc[-1]['close']
        dir_1m = 'BULL' if close_1m >= open_price else 'BEAR'

        # Intra-bar path: track min/max within first 60s
        first_60 = day_bars.loc[day_bars.index < day_start + timedelta(seconds=60)]
        min_price = first_60['low'].min()
        max_price = first_60['high'].max()
        dip_from_open = open_price - min_price
        rally_from_open = max_price - open_price

        # When did direction first establish? Track 5s snapshots
        path_points = []
        for sec in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]:
            t = day_start + timedelta(seconds=sec)
            b = day_bars.loc[(day_bars.index >= t) & (day_bars.index <= t + timedelta(seconds=3))]
            if len(b) > 0:
                path_points.append(b.iloc[0]['close'] - open_price)

        rows.append({
            'date': date,
            'open': open_price,
            'close_30s': close_30s,
            'close_1m': close_1m,
            'dir_30s': dir_30s,
            'dir_1m': dir_1m,
            'agree': dir_30s == dir_1m,
            'move_30s': close_30s - open_price,
            'move_1m': close_1m - open_price,
            'dip': dip_from_open,
            'rally': rally_from_open,
            'path': path_points,
        })

    rdf = pd.DataFrame(rows)
    n = len(rdf)
    n_agree = rdf['agree'].sum()
    n_disagree = n - n_agree

    # 1m direction stats
    n_bull_1m = (rdf['dir_1m'] == 'BULL').sum()
    n_bear_1m = (rdf['dir_1m'] == 'BEAR').sum()
    n_bull_30s = (rdf['dir_30s'] == 'BULL').sum()
    n_bear_30s = (rdf['dir_30s'] == 'BEAR').sum()

    out.append("\n## Part 1: Direction Stats\n")
    out.append(f"| Metric | 30s | 1m |")
    out.append(f"|--------|-----|-----|")
    out.append(f"| Bullish days | {n_bull_30s} ({100*n_bull_30s/n:.0f}%) | {n_bull_1m} ({100*n_bull_1m/n:.0f}%) |")
    out.append(f"| Bearish days | {n_bear_30s} ({100*n_bear_30s/n:.0f}%) | {n_bear_1m} ({100*n_bear_1m/n:.0f}%) |")
    out.append(f"| **Agreement** | | **{n_agree}/{n} ({100*n_agree/n:.0f}%)** |")
    out.append(f"| Disagreement | | {n_disagree}/{n} ({100*n_disagree/n:.0f}%) |")

    # Disagreement detail
    disagree = rdf[~rdf['agree']]
    out.append(f"\n## Part 2: Disagreement Days (30s ≠ 1m)\n")
    if len(disagree) > 0:
        out.append(f"| Date | Open | 30s Dir | 30s Move | 1m Dir | 1m Move | Dip | Rally |")
        out.append(f"|------|------|---------|----------|--------|---------|-----|-------|")
        for _, r in disagree.iterrows():
            out.append(f"| {r['date']} | ${r['open']:.2f} | {r['dir_30s']} | ${r['move_30s']:+.2f} | {r['dir_1m']} | ${r['move_1m']:+.2f} | ${r['dip']:.2f} | ${r['rally']:.2f} |")

    # Dip-then-rally analysis
    out.append(f"\n## Part 3: Intra-Bar Path Analysis (first 60s)\n")
    dip_then_bull = rdf[(rdf['dip'] >= 0.50) & (rdf['dir_1m'] == 'BULL')]
    rally_then_bear = rdf[(rdf['rally'] >= 0.50) & (rdf['dir_1m'] == 'BEAR')]
    out.append(f"- Days with ≥$0.50 dip that closed 1m BULL: **{len(dip_then_bull)}** ({100*len(dip_then_bull)/n:.0f}%)")
    out.append(f"- Days with ≥$0.50 rally that closed 1m BEAR: **{len(rally_then_bear)}** ({100*len(rally_then_bear)/n:.0f}%)")
    out.append(f"- Avg dip (all days): ${rdf['dip'].mean():.2f}, Avg rally: ${rdf['rally'].mean():.2f}")

    # Show path for disagreement days
    if len(disagree) > 0:
        out.append(f"\n### 5s price path on disagreement days")
        out.append(f"Showing (close - open) at each 5s interval:\n")
        for _, r in disagree.iterrows():
            path_str = " → ".join(f"${p:+.2f}" for p in r['path'][:12])
            out.append(f"**{r['date']}** ({r['dir_30s']}→{r['dir_1m']}): {path_str}")

    # ── Part 4: Strategy comparison ──────────────────────────────────
    out.append(f"\n\n## Part 4: Strategy Comparison — 30s vs 1m Direction\n")
    out.append(f"Entry: wait_30s or wait_60s. TP=$2.00, SL=$1.00. Hard exit 9:35.\n")

    configs = [
        ('wait_15s', 15),
        ('wait_20s', 20),
        ('wait_30s (original)', 30),
        ('wait_60s (1m close)', 60),
    ]

    for only_dir in [None, 'short']:  # None=both, 'short'=puts only
        dir_label = "Puts Only" if only_dir == 'short' else "Both Directions"
        out.append(f"\n### {dir_label}\n")
        out.append(f"| Entry | Trades | Win% | Avg P&L | Total | Sharpe | TP% | SL% | TIME% |")
        out.append(f"|-------|--------|------|---------|-------|--------|-----|-----|-------|")

        for label, wait_secs in configs:
            trades = []
            for date in trading_days:
                day_start = ET.localize(datetime.combine(date, datetime.strptime("09:30:00", "%H:%M:%S").time()))
                hard_exit_ts = ET.localize(datetime.combine(date, datetime.strptime(HARD_EXIT_TIME, "%H:%M:%S").time()))
                day_bars = df.loc[(df.index >= day_start) & (df.index < hard_exit_ts + timedelta(seconds=10))]
                if len(day_bars) < 2:
                    continue

                open_price = day_bars.iloc[0]['open']
                target = day_start + timedelta(seconds=wait_secs)
                bars_at = day_bars.loc[(day_bars.index >= target) & (day_bars.index <= target + timedelta(seconds=10))]
                if len(bars_at) == 0:
                    continue

                bar = bars_at.iloc[0]
                direction = 'long' if bar['close'] >= open_price else 'short'

                if only_dir and direction != only_dir:
                    continue

                entry_price = bar['close']
                remaining = day_bars.loc[day_bars.index > bars_at.index[0]]
                if len(remaining) == 0:
                    continue

                max_hold = (hard_exit_ts - bars_at.index[0]).total_seconds()
                result = simulate_trade(remaining, entry_price, direction,
                                       tp=2.00, sl=1.00, max_secs=max_hold)
                if result:
                    result['date'] = date
                    result['direction'] = direction
                    result['entry_price'] = entry_price
                    result['opt_pnl'] = opt_pnl(result['pnl_stock'])
                    trades.append(result)

            if not trades:
                out.append(f"| {label} | 0 | — | — | — | — | — | — | — |")
                continue

            pnls = [t['opt_pnl'] for t in trades]
            wins = sum(1 for p in pnls if p > 0)
            total = sum(pnls)
            avg = mean(pnls)
            sharpe = (mean(pnls) / stdev(pnls)) * (len(pnls)**0.5) if len(pnls) > 1 and stdev(pnls) > 0 else 0
            tp_pct = sum(1 for t in trades if t['exit_reason'] == 'TP') / len(trades) * 100
            sl_pct = sum(1 for t in trades if t['exit_reason'] == 'SL') / len(trades) * 100
            time_pct = sum(1 for t in trades if t['exit_reason'] == 'TIME') / len(trades) * 100

            out.append(f"| {label} | {len(trades)} | {100*wins/len(trades):.0f}% | ${avg:+.0f} | ${total:+.0f} | {sharpe:.1f} | {tp_pct:.0f}% | {sl_pct:.0f}% | {time_pct:.0f}% |")

    # ── Part 5: Day-by-day comparison ─────────────────────────────────
    out.append(f"\n\n## Part 5: Day-by-Day — 30s vs 1m Entry (Puts Only, TP=$2/SL=$1)\n")
    out.append(f"| Date | 30s Dir | 1m Dir | Agree? | 30s P&L | 30s Exit | 1m P&L | 1m Exit |")
    out.append(f"|------|---------|--------|--------|---------|----------|--------|---------|")

    for date in trading_days:
        day_start = ET.localize(datetime.combine(date, datetime.strptime("09:30:00", "%H:%M:%S").time()))
        hard_exit_ts = ET.localize(datetime.combine(date, datetime.strptime(HARD_EXIT_TIME, "%H:%M:%S").time()))
        day_bars = df.loc[(df.index >= day_start) & (df.index < hard_exit_ts + timedelta(seconds=10))]
        if len(day_bars) < 12:
            continue

        open_price = day_bars.iloc[0]['open']

        results = {}
        for wait_secs, label in [(30, '30s'), (60, '1m')]:
            target = day_start + timedelta(seconds=wait_secs)
            bars_at = day_bars.loc[(day_bars.index >= target) & (day_bars.index <= target + timedelta(seconds=10))]
            if len(bars_at) == 0:
                results[label] = {'dir': '—', 'pnl': '—', 'exit': '—', 'is_put': False}
                continue

            bar = bars_at.iloc[0]
            direction = 'long' if bar['close'] >= open_price else 'short'
            results[label] = {'dir': 'CALL' if direction == 'long' else 'PUT', 'is_put': direction == 'short'}

            if direction != 'short':  # puts only
                results[label].update({'pnl': 'skip', 'exit': '—'})
                continue

            remaining = day_bars.loc[day_bars.index > bars_at.index[0]]
            if len(remaining) == 0:
                results[label].update({'pnl': '—', 'exit': '—'})
                continue

            max_hold = (hard_exit_ts - bars_at.index[0]).total_seconds()
            result = simulate_trade(remaining, bar['close'], direction,
                                   tp=2.00, sl=1.00, max_secs=max_hold)
            if result:
                pnl = opt_pnl(result['pnl_stock'])
                results[label].update({'pnl': f"${pnl:+.0f}", 'exit': f"{result['exit_reason']} {result['exit_secs']:.0f}s"})
            else:
                results[label].update({'pnl': '—', 'exit': '—'})

        r30 = results.get('30s', {'dir': '—', 'pnl': '—', 'exit': '—'})
        r1m = results.get('1m', {'dir': '—', 'pnl': '—', 'exit': '—'})
        agree = "✓" if r30['dir'] == r1m['dir'] else "✗"

        # Only show if at least one side is a put
        if r30.get('is_put') or r1m.get('is_put') or r30['dir'] != r1m['dir']:
            out.append(f"| {date} | {r30['dir']} | {r1m['dir']} | {agree} | {r30['pnl']} | {r30['exit']} | {r1m['pnl']} | {r1m['exit']} |")

    # ── Write output ──────────────────────────────────────────────────
    text = "\n".join(out) + "\n"
    with open(OUTPUT, 'w') as f:
        f.write(text)
    print(f"\nResults written to {OUTPUT}")
    print(text)


if __name__ == '__main__':
    main()
