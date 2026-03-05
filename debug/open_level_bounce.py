#!/usr/bin/env python3
"""
TSLA open level bounce study v2:
When the opening dip touches a known key level, does it bounce better?

Levels (all known before market open):
- Previous day low / high / close
- N-day low/high (N = 2, 5, 10, 20, 50)

Uses 1m data (271 days) for precision.
Uses 5m data (525 days) for larger sample validation.

v2: extended lookbacks (up to 50 days), dip-size-controlled comparison.
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
OUTPUT = os.path.join(BASE, "open-level-bounce.md")

ZONE_DOLLARS = 1.00
LOOKBACKS = [2, 5, 10, 20, 50]  # N-day low/high


def load_data():
    data = {}
    f1 = os.path.join(CACHE, "bars", "tsla_1_min_ib.parquet")
    df = pd.read_parquet(f1).set_index('date').sort_index()
    data['1m'] = df
    print(f"1m: {len(df):>8,} bars, {df.index.min().date()} to {df.index.max().date()}")

    f5 = os.path.join(CACHE, "bars", "tsla_5_mins_ib.parquet")
    df = pd.read_parquet(f5).set_index('date').sort_index()
    data['5m'] = df
    print(f"5m: {len(df):>8,} bars, {df.index.min().date()} to {df.index.max().date()}")
    return data


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


def get_levels_for_day(daily_ohlc, trading_days, day_idx):
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


def analyze_day(df, date, levels, zone):
    day_start = ET.localize(datetime.combine(date, datetime.strptime("09:30:00", "%H:%M:%S").time()))
    day_end = ET.localize(datetime.combine(date, datetime.strptime("16:00:00", "%H:%M:%S").time()))

    first_5m = df.loc[(df.index >= day_start) & (df.index < day_start + timedelta(minutes=5))]
    if len(first_5m) < 1:
        return None

    open_price = first_5m.iloc[0]['open']
    dip_low = first_5m['low'].min()
    dip_size = open_price - dip_low

    if dip_size < 0.10:
        dip_low = open_price

    touched_levels = {}
    for name, level_price in levels.items():
        dist = dip_low - level_price
        if abs(dist) <= zone:
            touched_levels[name] = {'level': level_price, 'distance': dist}

    dip_time = first_5m['low'].idxmin()
    checkpoints = [1, 2, 3, 5, 10, 15, 30]
    mfe_at = {}
    price_at = {}

    for cp_min in checkpoints:
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

    # Categorize best level by specificity
    best_level = None
    if touched_levels:
        # Prefer more specific (shorter lookback) levels
        priority = ['prev_day_low', 'prev_day_high', 'prev_day_close',
                     '2d_low', '2d_high', '5d_low', '5d_high',
                     '10d_low', '10d_high', '20d_low', '20d_high',
                     '50d_low', '50d_high']
        for p in priority:
            if p in touched_levels:
                best_level = p
                break
        if not best_level:
            best_level = list(touched_levels.keys())[0]

    return {
        'date': date,
        'open': open_price,
        'dip_low': dip_low,
        'dip_size': dip_size,
        'touched_levels': touched_levels,
        'has_level': len(touched_levels) > 0,
        'best_level': best_level,
        'mfe_at': mfe_at,
        'price_at': price_at,
        'day_mfe': day_mfe,
        'day_close_from_dip': day_close_from_dip,
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


def format_results(results_by_tf):
    out = []
    out.append("# TSLA Open Level Bounce Study v2\n")
    out.append(f"**Zone:** ±${ZONE_DOLLARS:.2f} from level = touch")
    out.append(f"**Lookbacks:** prev day, {', '.join(str(n)+'d' for n in LOOKBACKS)}")
    out.append(f"**Question:** When the opening dip hits a known key level, does it bounce better?\n")

    for tf_label, results in results_by_tf.items():
        n = len(results)
        if n == 0:
            out.append(f"\n---\n\n## {tf_label} data — 0 days (no data)\n")
            continue
        date_range = f"{results[0]['date']} to {results[-1]['date']}"
        out.append(f"\n---\n\n## {tf_label} data — {n} days ({date_range})\n")

        with_level = [r for r in results if r['has_level']]
        without_level = [r for r in results if not r['has_level']]

        out.append(f"- Level touch: **{len(with_level)}** ({100*len(with_level)/n:.0f}%)")
        out.append(f"- No level: **{len(without_level)}** ({100*len(without_level)/n:.0f}%)")
        out.append(f"- Avg dip (with): **${np.mean([r['dip_size'] for r in with_level]):.2f}** | "
                    f"(without): **${np.mean([r['dip_size'] for r in without_level]):.2f}**\n")

        # ── Main comparison ──────────────────────────────────────────
        out.append("### Bounce Comparison (from dip low)\n")
        checkpoints = [1, 2, 3, 5, 10, 15, 30]
        header = "| Metric | " + " | ".join(f"{cp}m" for cp in checkpoints) + " | Day |"
        divider = "|--------|" + "|".join("------" for _ in checkpoints) + "|------|"
        out.append(header)
        out.append(divider)

        for label, group in [("**MFE (level)**", with_level), ("MFE (no level)", without_level)]:
            vals = [f"${np.mean([r['mfe_at'].get(cp, 0) for r in group]):.2f}" for cp in checkpoints]
            out.append(f"| {label} | " + " | ".join(vals) + f" | ${np.mean([r['day_mfe'] for r in group]):.2f} |")

        for label, group in [("**Price (level)**", with_level), ("Price (no level)", without_level)]:
            vals = [f"${np.mean([r['price_at'].get(cp, 0) for r in group]):+.2f}" for cp in checkpoints]
            out.append(f"| {label} | " + " | ".join(vals) + f" | ${np.mean([r['day_close_from_dip'] for r in group]):+.2f} |")

        for label, group in [("**Win% (level)**", with_level), ("Win% (no level)", without_level)]:
            wins = []
            for cp in checkpoints:
                pos = sum(1 for r in group if r['price_at'].get(cp, 0) > 0.10)
                wins.append(f"{100*pos/len(group):.0f}%")
            day_pos = sum(1 for r in group if r['day_close_from_dip'] > 0.10)
            out.append(f"| {label} | " + " | ".join(wins) + f" | {100*day_pos/len(group):.0f}% |")

        # ── By level type ────────────────────────────────────────────
        out.append("\n### By Level Type\n")
        level_types = defaultdict(list)
        for r in with_level:
            for lname in r['touched_levels']:
                level_types[lname].append(r)

        level_order = ['prev_day_low', 'prev_day_high', 'prev_day_close']
        for n in LOOKBACKS:
            level_order += [f'{n}d_low', f'{n}d_high']

        out.append("| Level | Days | Avg Dip | 5m MFE | 5m Price | 5m Win% | 15m MFE | Day Win% |")
        out.append("|-------|------|---------|--------|----------|---------|---------|----------|")

        for lname in level_order:
            group = level_types.get(lname, [])
            if not group:
                continue
            avg_dip = np.mean([r['dip_size'] for r in group])
            mfe5 = np.mean([r['mfe_at'].get(5, 0) for r in group])
            price5 = np.mean([r['price_at'].get(5, 0) for r in group])
            mfe15 = np.mean([r['mfe_at'].get(15, 0) for r in group])
            win5 = sum(1 for r in group if r['price_at'].get(5, 0) > 0.10) / len(group)
            win_day = sum(1 for r in group if r['day_close_from_dip'] > 0.10) / len(group)
            out.append(f"| {lname} | {len(group)} | ${avg_dip:.2f} | ${mfe5:.2f} | ${price5:+.2f} | {100*win5:.0f}% | ${mfe15:.2f} | {100*win_day:.0f}% |")

        # ── LOW vs HIGH levels ───────────────────────────────────────
        out.append("\n### LOW Levels vs HIGH Levels (aggregated)\n")
        low_levels = [r for r in with_level if any('low' in k for k in r['touched_levels'])]
        high_levels = [r for r in with_level if any('high' in k for k in r['touched_levels'])]

        out.append("| Group | Days | 5m MFE | 5m Price | 5m Win% | 15m MFE | Day Win% |")
        out.append("|-------|------|--------|----------|---------|---------|----------|")
        for label, group in [("LOW levels", low_levels), ("HIGH levels", high_levels)]:
            if not group:
                continue
            mfe5 = np.mean([r['mfe_at'].get(5, 0) for r in group])
            price5 = np.mean([r['price_at'].get(5, 0) for r in group])
            mfe15 = np.mean([r['mfe_at'].get(15, 0) for r in group])
            win5 = sum(1 for r in group if r['price_at'].get(5, 0) > 0.10) / len(group)
            win_day = sum(1 for r in group if r['day_close_from_dip'] > 0.10) / len(group)
            out.append(f"| **{label}** | {len(group)} | ${mfe5:.2f} | ${price5:+.2f} | {100*win5:.0f}% | ${mfe15:.2f} | {100*win_day:.0f}% |")

        # ── Dip-size-controlled comparison ───────────────────────────
        out.append("\n### Dip Size Controlled: Level vs No-Level (same dip size)\n")
        out.append("| Dip Bucket | Level n | No-Lvl n | Lvl 5m Win% | No-Lvl 5m Win% | Edge | Lvl 5m Price | No-Lvl 5m Price |")
        out.append("|------------|---------|----------|-------------|----------------|------|-------------|----------------|")

        buckets = ['<$0.50', '$0.50-1', '$1-2', '$2-3', '$3+']
        for bkt in buckets:
            lvl_grp = [r for r in with_level if dip_bucket(r['dip_size']) == bkt]
            no_grp = [r for r in without_level if dip_bucket(r['dip_size']) == bkt]
            if not lvl_grp or not no_grp:
                continue
            lvl_win = sum(1 for r in lvl_grp if r['price_at'].get(5, 0) > 0.10) / len(lvl_grp)
            no_win = sum(1 for r in no_grp if r['price_at'].get(5, 0) > 0.10) / len(no_grp)
            lvl_price = np.mean([r['price_at'].get(5, 0) for r in lvl_grp])
            no_price = np.mean([r['price_at'].get(5, 0) for r in no_grp])
            edge = lvl_win - no_win
            out.append(f"| {bkt} | {len(lvl_grp)} | {len(no_grp)} | {100*lvl_win:.0f}% | {100*no_win:.0f}% | {100*edge:+.0f}pp | ${lvl_price:+.2f} | ${no_price:+.2f} |")

        # ── Lookback depth: does longer lookback = stronger level? ───
        out.append("\n### Lookback Depth: Does Older Level = Stronger Bounce?\n")
        out.append("Only counting the *deepest* (longest lookback) level each day touches.\n")
        out.append("| Deepest Level | Days | 5m Win% | 5m Price | 15m MFE | Day Win% |")
        out.append("|---------------|------|---------|----------|---------|----------|")

        # For each day, find the deepest lookback level it touched
        depth_groups = defaultdict(list)
        for r in with_level:
            max_depth = 0
            for lname in r['touched_levels']:
                if lname.startswith('prev_day'):
                    depth = 1
                else:
                    try:
                        depth = int(lname.split('d_')[0])
                    except ValueError:
                        depth = 0
                max_depth = max(max_depth, depth)
            depth_groups[max_depth].append(r)

        for depth in sorted(depth_groups.keys()):
            group = depth_groups[depth]
            label = f"prev_day only" if depth == 1 else f"{depth}d level"
            mfe5 = np.mean([r['mfe_at'].get(5, 0) for r in group])
            price5 = np.mean([r['price_at'].get(5, 0) for r in group])
            mfe15 = np.mean([r['mfe_at'].get(15, 0) for r in group])
            win5 = sum(1 for r in group if r['price_at'].get(5, 0) > 0.10) / len(group)
            win_day = sum(1 for r in group if r['day_close_from_dip'] > 0.10) / len(group)
            out.append(f"| {label} | {len(group)} | {100*win5:.0f}% | ${price5:+.2f} | ${mfe15:.2f} | {100*win_day:.0f}% |")

        # ── Dip size table (all days) ────────────────────────────────
        out.append("\n### Dip Size vs Bounce (all days)\n")
        out.append("| Dip Size | Days | Has Level% | 5m MFE | 5m Price | 5m Win% |")
        out.append("|----------|------|-----------|--------|----------|---------|")

        for bkt in buckets:
            bucket = [r for r in results if dip_bucket(r['dip_size']) == bkt]
            if not bucket:
                continue
            has_lvl = sum(1 for r in bucket if r['has_level']) / len(bucket)
            mfe5 = np.mean([r['mfe_at'].get(5, 0) for r in bucket])
            price5 = np.mean([r['price_at'].get(5, 0) for r in bucket])
            win5 = sum(1 for r in bucket if r['price_at'].get(5, 0) > 0.10) / len(bucket)
            out.append(f"| {bkt} | {len(bucket)} | {100*has_lvl:.0f}% | ${mfe5:.2f} | ${price5:+.2f} | {100*win5:.0f}% |")

    return "\n".join(out) + "\n"


def main():
    data = load_data()

    results_by_tf = {}
    for tf_label, df in [('1m', data['1m']), ('5m', data['5m'])]:
        daily_ohlc = get_daily_ohlc(df)
        trading_days = sorted(daily_ohlc.keys())
        print(f"\n{tf_label}: {len(trading_days)} trading days")

        results = []
        min_idx = max(LOOKBACKS)  # need enough lookback
        for i in range(min_idx, len(trading_days)):
            levels = get_levels_for_day(daily_ohlc, trading_days, i)
            result = analyze_day(df, trading_days[i], levels, ZONE_DOLLARS)
            if result:
                results.append(result)

        results_by_tf[tf_label] = results
        print(f"  Analyzed: {len(results)} days, level touch: {sum(1 for r in results if r['has_level'])}")

    text = format_results(results_by_tf)
    with open(OUTPUT, 'w') as f:
        f.write(text)
    print(f"\nResults written to {OUTPUT}")
    print(text)


if __name__ == '__main__':
    main()
