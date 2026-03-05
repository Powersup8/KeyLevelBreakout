#!/usr/bin/env python3
"""
Multi-symbol open study:
1. Level bounce: does dipping to a known level produce better bounces?
2. Direction study: above/below open at 30s-300s checkpoints
3. Day high and close stats

Symbols: TSLA, NVDA, AMZN, SPY
Data: 1m (primary), 5m (larger sample validation)
"""

import os
import pandas as pd
import numpy as np
import pytz
from datetime import datetime, timedelta
from collections import defaultdict

ET = pytz.timezone('US/Eastern')

BASE = os.path.dirname(os.path.abspath(__file__))
_PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(BASE)))
CACHE = os.path.join(_PROJ_ROOT, "trading_bot", "cache")
OUTPUT = os.path.join(BASE, "open-level-multi.md")

ZONE_DOLLARS = 1.00
LOOKBACKS = [2, 5, 10, 20, 50]
SYMBOLS = ['tsla', 'nvda', 'amzn', 'spy']
CHECKPOINTS_SEC = [30, 60, 120, 180, 300]  # direction study checkpoints


def load_symbol(symbol, timeframe):
    if timeframe == '1m':
        f = os.path.join(CACHE, "bars", f"{symbol}_1_min_ib.parquet")
    else:
        f = os.path.join(CACHE, "bars", f"{symbol}_5_mins_ib.parquet")
    if not os.path.exists(f):
        return None
    df = pd.read_parquet(f).set_index('date').sort_index()
    return df


def get_daily_ohlc(df):
    market = df.between_time('09:30', '15:59')
    days = {}
    for date in sorted(set(market.index.date)):
        day_start = ET.localize(datetime.combine(date, datetime.strptime("09:30:00", "%H:%M:%S").time()))
        day_end = ET.localize(datetime.combine(date, datetime.strptime("15:59:00", "%H:%M:%S").time()))
        day = df.loc[(df.index >= day_start) & (df.index <= day_end)]
        if len(day) < 3:
            continue
        days[date] = {
            'open': day.iloc[0]['open'],
            'high': day['high'].max(),
            'low': day['low'].min(),
            'close': day.iloc[-1]['close'],
        }
    return days


def get_levels(daily_ohlc, trading_days, day_idx):
    levels = {}
    if day_idx < 1:
        return levels
    prev = daily_ohlc[trading_days[day_idx - 1]]
    levels['prev_day_low'] = prev['low']
    levels['prev_day_high'] = prev['high']
    levels['prev_day_close'] = prev['close']
    for n in LOOKBACKS:
        if day_idx < n:
            continue
        lows = [daily_ohlc[trading_days[day_idx - i]]['low'] for i in range(1, n + 1)]
        highs = [daily_ohlc[trading_days[day_idx - i]]['high'] for i in range(1, n + 1)]
        levels[f'{n}d_low'] = min(lows)
        levels[f'{n}d_high'] = max(highs)
    return levels


def analyze_day(df, date, levels, zone, bar_secs):
    day_start = ET.localize(datetime.combine(date, datetime.strptime("09:30:00", "%H:%M:%S").time()))
    day_end = ET.localize(datetime.combine(date, datetime.strptime("16:00:00", "%H:%M:%S").time()))

    # Full day bars
    full_day = df.loc[(df.index >= day_start) & (df.index <= day_end)]
    if len(full_day) < 3:
        return None

    open_price = full_day.iloc[0]['open']

    # First 5 minutes for dip
    first_5m = df.loc[(df.index >= day_start) & (df.index < day_start + timedelta(minutes=5))]
    if len(first_5m) < 1:
        return None

    dip_low = first_5m['low'].min()
    dip_size = open_price - dip_low
    if dip_size < 0.01:
        dip_low = open_price
        dip_size = 0

    # Level touch
    touched_levels = {}
    for name, level_price in levels.items():
        dist = dip_low - level_price
        if abs(dist) <= zone:
            touched_levels[name] = {'level': level_price, 'distance': dist}

    # Bounce from dip
    dip_time = first_5m['low'].idxmin()
    bounce_cps = [1, 2, 3, 5, 10, 15, 30]
    mfe_at = {}
    price_at = {}
    for cp_min in bounce_cps:
        cp_end = dip_time + timedelta(minutes=cp_min)
        window = df.loc[(df.index > dip_time) & (df.index <= cp_end) & (df.index <= day_end)]
        if len(window) > 0:
            mfe_at[cp_min] = window['high'].max() - dip_low
            price_at[cp_min] = window.iloc[-1]['close'] - dip_low
        else:
            mfe_at[cp_min] = 0
            price_at[cp_min] = 0

    rest_of_day = df.loc[(df.index > dip_time) & (df.index <= day_end)]
    day_mfe = rest_of_day['high'].max() - dip_low if len(rest_of_day) > 0 else 0
    day_close_from_dip = rest_of_day.iloc[-1]['close'] - dip_low if len(rest_of_day) > 0 else 0

    # Direction checkpoints (from open)
    dir_at = {}
    for cp_sec in CHECKPOINTS_SEC:
        target = day_start + timedelta(seconds=cp_sec)
        tolerance = timedelta(seconds=max(bar_secs, 5))
        candidates = full_day.loc[(full_day.index >= target - tolerance) & (full_day.index <= target + tolerance)]
        if len(candidates) > 0:
            diffs = abs(candidates.index - target)
            bar = candidates.loc[candidates.index[diffs.argmin()]]
            dir_at[cp_sec] = bar['close'] - open_price
        else:
            before = full_day.loc[full_day.index <= target]
            if len(before) > 0:
                dir_at[cp_sec] = before.iloc[-1]['close'] - open_price
            else:
                dir_at[cp_sec] = None

    # Day high and close
    day_high = full_day['high'].max()
    day_high_time = full_day['high'].idxmax().astimezone(ET)
    day_close = full_day.iloc[-1]['close']

    # Best level
    best_level = None
    if touched_levels:
        priority = ['prev_day_low', 'prev_day_high', 'prev_day_close'] + \
                   [f'{n}d_{t}' for n in LOOKBACKS for t in ['low', 'high']]
        for p in priority:
            if p in touched_levels:
                best_level = p
                break

    # Deepest lookback
    max_depth = 0
    if touched_levels:
        for lname in touched_levels:
            if lname.startswith('prev_day'):
                depth = 1
            else:
                try:
                    depth = int(lname.split('d_')[0])
                except ValueError:
                    depth = 0
            max_depth = max(max_depth, depth)

    return {
        'date': date,
        'open': open_price,
        'dip_low': dip_low,
        'dip_size': dip_size,
        'touched_levels': touched_levels,
        'has_level': len(touched_levels) > 0,
        'best_level': best_level,
        'max_depth': max_depth,
        'mfe_at': mfe_at,
        'price_at': price_at,
        'day_mfe': day_mfe,
        'day_close_from_dip': day_close_from_dip,
        'dir_at': dir_at,
        'day_high': day_high - open_price,
        'day_high_time': day_high_time,
        'day_close_vs_open': day_close - open_price,
    }


def dip_bucket(dip_size):
    if dip_size < 0.50:
        return '<$0.50'
    elif dip_size < 1.00:
        return '$0.50-1'
    elif dip_size < 2.00:
        return '$1-2'
    elif dip_size < 3.00:
        return '$2-3'
    else:
        return '$3+'


def format_all(all_results):
    out = []
    out.append("# Multi-Symbol Open Study: Level Bounce + Direction\n")
    out.append(f"**Symbols:** {', '.join(s.upper() for s in SYMBOLS)}")
    out.append(f"**Zone:** ±${ZONE_DOLLARS:.2f} from level = touch")
    out.append(f"**Lookbacks:** prev day, {', '.join(str(n)+'d' for n in LOOKBACKS)}\n")

    # ══════════════════════════════════════════════════════════════════
    # PART 1: Direction study (above/below open)
    # ══════════════════════════════════════════════════════════════════
    out.append("---\n# Part 1: Direction Study (above/below open at checkpoints)\n")

    for sym, tf_results in all_results.items():
        for tf_label, results in tf_results.items():
            if not results:
                continue
            n = len(results)
            out.append(f"\n## {sym.upper()} ({tf_label}, {n} days)\n")

            # Direction at each checkpoint
            cp_labels = []
            for cp in CHECKPOINTS_SEC:
                if cp < 60:
                    cp_labels.append(f"{cp}s")
                else:
                    cp_labels.append(f"{cp//60}m")

            header = "| Metric | " + " | ".join(cp_labels) + " | Day High | Day Close |"
            divider = "|--------|" + "|".join("------" for _ in CHECKPOINTS_SEC) + "|----------|-----------|"
            out.append(header)
            out.append(divider)

            # % above open
            above_pcts = []
            below_pcts = []
            avg_moves = []
            for cp in CHECKPOINTS_SEC:
                moves = [r['dir_at'].get(cp) for r in results if r['dir_at'].get(cp) is not None]
                if moves:
                    above = sum(1 for m in moves if m > 0.05) / len(moves)
                    below = sum(1 for m in moves if m < -0.05) / len(moves)
                    above_pcts.append(f"**{100*above:.0f}%**")
                    below_pcts.append(f"**{100*below:.0f}%**")
                    avg_moves.append(f"${np.mean(moves):+.2f}")
                else:
                    above_pcts.append("—")
                    below_pcts.append("—")
                    avg_moves.append("—")

            # Day high and close
            highs = [r['day_high'] for r in results]
            closes = [r['day_close_vs_open'] for r in results]
            high_above = sum(1 for h in highs if h > 0.05) / len(highs)
            close_above = sum(1 for c in closes if c > 0.05) / len(closes)
            close_below = sum(1 for c in closes if c < -0.05) / len(closes)

            out.append(f"| **% Above** | " + " | ".join(above_pcts) + f" | {100*high_above:.0f}% | {100*close_above:.0f}% |")
            out.append(f"| **% Below** | " + " | ".join(below_pcts) + f" | — | {100*close_below:.0f}% |")
            out.append(f"| Avg move | " + " | ".join(avg_moves) + f" | ${np.mean(highs):+.2f} | ${np.mean(closes):+.2f} |")

    # ══════════════════════════════════════════════════════════════════
    # PART 2: Level bounce comparison
    # ══════════════════════════════════════════════════════════════════
    out.append("\n\n---\n# Part 2: Level Bounce (level touch vs no level)\n")

    # Cross-symbol summary
    out.append("## Cross-Symbol Summary\n")
    out.append("| Symbol | TF | Days | Level% | Lvl 5m Win% | No-Lvl 5m Win% | Edge | Lvl 5m Price | No-Lvl 5m Price |")
    out.append("|--------|----|----- |--------|-------------|----------------|------|-------------|----------------|")

    for sym, tf_results in all_results.items():
        for tf_label, results in tf_results.items():
            if not results:
                continue
            wl = [r for r in results if r['has_level']]
            nl = [r for r in results if not r['has_level']]
            if not wl or not nl:
                continue
            lvl_pct = len(wl) / len(results)
            lvl_win = sum(1 for r in wl if r['price_at'].get(5, 0) > 0.01) / len(wl)
            no_win = sum(1 for r in nl if r['price_at'].get(5, 0) > 0.01) / len(nl)
            lvl_price = np.mean([r['price_at'].get(5, 0) for r in wl])
            no_price = np.mean([r['price_at'].get(5, 0) for r in nl])
            edge = lvl_win - no_win
            out.append(f"| {sym.upper()} | {tf_label} | {len(results)} | {100*lvl_pct:.0f}% | {100*lvl_win:.0f}% | {100*no_win:.0f}% | {100*edge:+.0f}pp | ${lvl_price:+.2f} | ${no_price:+.2f} |")

    # Per-symbol detail
    for sym, tf_results in all_results.items():
        for tf_label, results in tf_results.items():
            if not results:
                continue
            wl = [r for r in results if r['has_level']]
            nl = [r for r in results if not r['has_level']]
            if not wl:
                continue
            n = len(results)
            out.append(f"\n### {sym.upper()} ({tf_label}, {n} days)\n")

            # By level type
            level_types = defaultdict(list)
            for r in wl:
                for lname in r['touched_levels']:
                    level_types[lname].append(r)

            level_order = ['prev_day_low', 'prev_day_high', 'prev_day_close'] + \
                          [f'{n}d_{t}' for n in LOOKBACKS for t in ['low', 'high']]

            out.append("| Level | Days | 5m MFE | 5m Price | 5m Win% | Day Win% |")
            out.append("|-------|------|--------|----------|---------|----------|")
            for lname in level_order:
                group = level_types.get(lname, [])
                if not group:
                    continue
                mfe5 = np.mean([r['mfe_at'].get(5, 0) for r in group])
                price5 = np.mean([r['price_at'].get(5, 0) for r in group])
                win5 = sum(1 for r in group if r['price_at'].get(5, 0) > 0.01) / len(group)
                win_day = sum(1 for r in group if r['day_close_from_dip'] > 0.01) / len(group)
                out.append(f"| {lname} | {len(group)} | ${mfe5:.2f} | ${price5:+.2f} | {100*win5:.0f}% | {100*win_day:.0f}% |")

            # LOW vs HIGH
            low_lvl = [r for r in wl if any('low' in k for k in r['touched_levels'])]
            high_lvl = [r for r in wl if any('high' in k for k in r['touched_levels'])]
            if low_lvl and high_lvl:
                out.append(f"\n| Group | n | 5m Win% | 5m Price | Day Win% |")
                out.append(f"|-------|---|---------|----------|----------|")
                for label, grp in [("LOW", low_lvl), ("HIGH", high_lvl)]:
                    w5 = sum(1 for r in grp if r['price_at'].get(5, 0) > 0.01) / len(grp)
                    p5 = np.mean([r['price_at'].get(5, 0) for r in grp])
                    wd = sum(1 for r in grp if r['day_close_from_dip'] > 0.01) / len(grp)
                    out.append(f"| **{label}** | {len(grp)} | {100*w5:.0f}% | ${p5:+.2f} | {100*wd:.0f}% |")

            # Lookback depth
            depth_groups = defaultdict(list)
            for r in wl:
                depth_groups[r['max_depth']].append(r)

            out.append(f"\n| Depth | Days | 5m Win% | 5m Price | Day Win% |")
            out.append(f"|-------|------|---------|----------|----------|")
            for depth in sorted(depth_groups.keys()):
                group = depth_groups[depth]
                label = "prev_day" if depth == 1 else f"{depth}d"
                w5 = sum(1 for r in group if r['price_at'].get(5, 0) > 0.01) / len(group)
                p5 = np.mean([r['price_at'].get(5, 0) for r in group])
                wd = sum(1 for r in group if r['day_close_from_dip'] > 0.01) / len(group)
                out.append(f"| {label} | {len(group)} | {100*w5:.0f}% | ${p5:+.2f} | {100*wd:.0f}% |")

            # Dip-size controlled
            if nl:
                out.append(f"\n| Dip Bucket | Lvl n | No-Lvl n | Lvl 5m Win% | No-Lvl 5m Win% | Edge |")
                out.append(f"|------------|-------|----------|-------------|----------------|------|")
                for bkt in ['<$0.50', '$0.50-1', '$1-2', '$2-3', '$3+']:
                    lg = [r for r in wl if dip_bucket(r['dip_size']) == bkt]
                    ng = [r for r in nl if dip_bucket(r['dip_size']) == bkt]
                    if not lg or not ng:
                        continue
                    lw = sum(1 for r in lg if r['price_at'].get(5, 0) > 0.01) / len(lg)
                    nw = sum(1 for r in ng if r['price_at'].get(5, 0) > 0.01) / len(ng)
                    out.append(f"| {bkt} | {len(lg)} | {len(ng)} | {100*lw:.0f}% | {100*nw:.0f}% | {100*(lw-nw):+.0f}pp |")

    return "\n".join(out) + "\n"


def main():
    all_results = {}

    for symbol in SYMBOLS:
        print(f"\n{'='*50}")
        print(f"  {symbol.upper()}")
        print(f"{'='*50}")
        all_results[symbol] = {}

        for tf_label, bar_secs in [('1m', 60), ('5m', 300)]:
            df = load_symbol(symbol, tf_label)
            if df is None:
                print(f"  {tf_label}: no data")
                continue
            print(f"  {tf_label}: {len(df):,} bars, {df.index.min().date()} to {df.index.max().date()}")

            daily_ohlc = get_daily_ohlc(df)
            trading_days = sorted(daily_ohlc.keys())
            print(f"  {tf_label}: {len(trading_days)} trading days")

            results = []
            min_idx = max(LOOKBACKS)
            for i in range(min_idx, len(trading_days)):
                levels = get_levels(daily_ohlc, trading_days, i)
                result = analyze_day(df, trading_days[i], levels, ZONE_DOLLARS, bar_secs)
                if result:
                    results.append(result)

            all_results[symbol][tf_label] = results
            wl = sum(1 for r in results if r['has_level'])
            print(f"  {tf_label}: {len(results)} analyzed, {wl} level touch")

    text = format_all(all_results)
    with open(OUTPUT, 'w') as f:
        f.write(text)
    print(f"\nResults written to {OUTPUT}")
    # Print summary only
    for line in text.split('\n'):
        if line.startswith('#') or line.startswith('|') or line.startswith('**'):
            print(line)


if __name__ == '__main__':
    main()
