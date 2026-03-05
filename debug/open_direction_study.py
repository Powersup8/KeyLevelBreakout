#!/usr/bin/env python3
"""
TSLA open direction study: how often is price above/below open at 30s intervals.
Uses 5s, 1m, and 5m data for different historical depths.
"""

import os, sys
import pandas as pd
import numpy as np
import pytz
from datetime import datetime, timedelta
from collections import defaultdict

ET = pytz.timezone('US/Eastern')

BASE = os.path.dirname(os.path.abspath(__file__))
_PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(BASE)))
CACHE = os.path.join(_PROJ_ROOT, "trading_bot", "cache")
OUTPUT = os.path.join(BASE, "open-direction-study.md")

CHECKPOINTS = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300]  # seconds


def load_data():
    """Load all three timeframes."""
    data = {}

    # 5-second
    f5 = os.path.join(CACHE, "bars_highres", "5sec", "tsla_5_secs_ib.parquet")
    df = pd.read_parquet(f5).set_index('date').sort_index()
    data['5s'] = df
    print(f"5s:  {len(df):>8,} bars, {df.index.min().date()} to {df.index.max().date()}")

    # 1-minute
    f1 = os.path.join(CACHE, "bars", "tsla_1_min_ib.parquet")
    df = pd.read_parquet(f1).set_index('date').sort_index()
    data['1m'] = df
    print(f"1m:  {len(df):>8,} bars, {df.index.min().date()} to {df.index.max().date()}")

    # 5-minute
    f5m = os.path.join(CACHE, "bars", "tsla_5_mins_ib.parquet")
    df = pd.read_parquet(f5m).set_index('date').sort_index()
    data['5m'] = df
    print(f"5m:  {len(df):>8,} bars, {df.index.min().date()} to {df.index.max().date()}")

    return data


def analyze_timeframe(df, tf_label, bar_secs):
    """
    For each trading day, get the open price (9:30 bar open) and check
    where price is at each checkpoint.
    """
    market = df.between_time('09:30', '15:59')
    trading_days = sorted(set(market.index.date))

    results = []  # list of dicts, one per day

    for date in trading_days:
        day_start = ET.localize(datetime.combine(date, datetime.strptime("09:30:00", "%H:%M:%S").time()))
        day_end = ET.localize(datetime.combine(date, datetime.strptime("15:59:00", "%H:%M:%S").time()))
        window_end = day_start + timedelta(seconds=330)  # 5.5 min buffer
        day_bars = df.loc[(df.index >= day_start) & (df.index < window_end)]

        if len(day_bars) < 2:
            continue

        open_price = day_bars.iloc[0]['open']
        day_result = {'date': date, 'open': open_price}

        # Day close and day high from full RTH session
        full_day = df.loc[(df.index >= day_start) & (df.index <= day_end)]
        if len(full_day) > 0:
            day_result['day_close'] = full_day.iloc[-1]['close'] - open_price
            day_result['day_high'] = full_day['high'].max() - open_price
        else:
            day_result['day_close'] = None
            day_result['day_high'] = None

        for cp_secs in CHECKPOINTS:
            # Find the bar closest to this checkpoint
            target = day_start + timedelta(seconds=cp_secs)

            if bar_secs <= 5:
                # 5s data: look for exact bar
                tolerance = timedelta(seconds=5)
            elif bar_secs <= 60:
                # 1m data: the bar timestamped at 9:30 covers 9:30:00-9:30:59
                # For 30s checkpoint, we still only have the 9:30 bar close
                # For 60s, we have the 9:31 bar
                tolerance = timedelta(seconds=bar_secs)
            else:
                # 5m data: bar at 9:30 covers 9:30-9:35
                tolerance = timedelta(seconds=bar_secs)

            # Find nearest bar at or before target
            candidates = day_bars.loc[(day_bars.index <= target + tolerance) & (day_bars.index >= target - tolerance)]
            if len(candidates) == 0:
                # Try wider: get the last bar before target
                before = day_bars.loc[day_bars.index <= target]
                if len(before) > 0:
                    bar = before.iloc[-1]
                    price = bar['close']
                else:
                    day_result[f'cp_{cp_secs}'] = None
                    continue
            else:
                # Use the bar closest to target
                diffs = abs(candidates.index - target)
                bar = candidates.loc[candidates.index[diffs.argmin()]]
                price = bar['close']

            day_result[f'cp_{cp_secs}'] = price - open_price

        results.append(day_result)

    return results


def format_results(results_by_tf):
    """Format into markdown tables."""
    out = []
    out.append("# TSLA Open Direction Study\n")
    out.append("**Question:** How often is TSLA above or below its 9:30 open at each 30s checkpoint?\n")

    # ── Summary table per timeframe ───────────────────────────────────
    for tf_label, results in results_by_tf.items():
        n = len(results)
        date_range = f"{results[0]['date']} to {results[-1]['date']}"
        out.append(f"\n## {tf_label} data — {n} trading days ({date_range})\n")

        # Build column keys: checkpoints + day_high + day_close
        col_keys = [f'cp_{cp}' for cp in CHECKPOINTS] + ['day_high', 'day_close']
        col_labels = []
        for cp in CHECKPOINTS:
            label = f"{cp}s" if cp < 60 else f"{cp//60}m{cp%60:02d}s" if cp % 60 else f"{cp//60}m"
            col_labels.append(label)
        col_labels += ['Day High', 'Day Close']

        header = "| Checkpoint | " + " | ".join(col_labels) + " |"
        divider = "|-----------|" + "|".join("------" for _ in col_keys) + "|"

        out.append(header)
        out.append(divider)

        # Count above/below/flat
        row_data = {name: [] for name in ['above', 'below', 'flat', 'pct_above', 'pct_below', 'avg', 'median', 'avg_above', 'avg_below']}

        for key in col_keys:
            moves = [r[key] for r in results if r.get(key) is not None]
            if not moves:
                for name in row_data:
                    row_data[name].append("—")
                continue

            above = sum(1 for m in moves if m > 0.05)
            below = sum(1 for m in moves if m < -0.05)
            flat = len(moves) - above - below

            above_moves = [m for m in moves if m > 0.05]
            below_moves = [m for m in moves if m < -0.05]

            avg = np.mean(moves)
            med = np.median(moves)
            avg_a = np.mean(above_moves) if above_moves else 0
            avg_b = np.mean(below_moves) if below_moves else 0

            row_data['above'].append(f"{above} ({100*above/len(moves):.0f}%)")
            row_data['below'].append(f"{below} ({100*below/len(moves):.0f}%)")
            row_data['flat'].append(f"{flat}")
            row_data['pct_above'].append(f"**{100*above/len(moves):.0f}%**")
            row_data['pct_below'].append(f"**{100*below/len(moves):.0f}%**")
            row_data['avg'].append(f"${avg:+.2f}")
            row_data['median'].append(f"${med:+.2f}")
            row_data['avg_above'].append(f"${avg_a:+.2f}")
            row_data['avg_below'].append(f"${avg_b:+.2f}")

        out.append("| **Above open** | " + " | ".join(row_data['above']) + " |")
        out.append("| **Below open** | " + " | ".join(row_data['below']) + " |")
        out.append("| Flat | " + " | ".join(row_data['flat']) + " |")
        out.append("| **% Above** | " + " | ".join(row_data['pct_above']) + " |")
        out.append("| **% Below** | " + " | ".join(row_data['pct_below']) + " |")
        out.append("| Avg move | " + " | ".join(row_data['avg']) + " |")
        out.append("| Median move | " + " | ".join(row_data['median']) + " |")
        out.append("| Avg if above | " + " | ".join(row_data['avg_above']) + " |")
        out.append("| Avg if below | " + " | ".join(row_data['avg_below']) + " |")

    # ── Regime analysis (5m has 2 years) ──────────────────────────────
    if '5m' in results_by_tf:
        results = results_by_tf['5m']
        out.append("\n\n## Regime Breakdown (5m data, quarterly)\n")

        # Split by quarter
        quarters = defaultdict(list)
        for r in results:
            q = f"{r['date'].year}Q{(r['date'].month - 1)//3 + 1}"
            quarters[q].append(r)

        out.append("| Quarter | Days | % Below at 30s | % Below at 1m | % Below at 2m | % Below at 5m | Avg Move 5m |")
        out.append("|---------|------|---------------|--------------|--------------|--------------|------------|")

        for q in sorted(quarters.keys()):
            qr = quarters[q]
            n = len(qr)

            cols = [f"| {q} | {n}"]
            for cp in [30, 60, 120, 300]:
                moves = [r[f'cp_{cp}'] for r in qr if r.get(f'cp_{cp}') is not None]
                if moves:
                    below = sum(1 for m in moves if m < -0.05)
                    cols.append(f" {100*below/len(moves):.0f}%")
                else:
                    cols.append(" —")

            moves_5m = [r['cp_300'] for r in qr if r.get('cp_300') is not None]
            if moves_5m:
                cols.append(f" ${np.mean(moves_5m):+.2f}")
            else:
                cols.append(" —")

            out.append(" |".join(cols) + " |")

    # ── Monthly for 1m data ───────────────────────────────────────────
    if '1m' in results_by_tf:
        results = results_by_tf['1m']
        out.append("\n\n## Monthly Breakdown (1m data)\n")

        months = defaultdict(list)
        for r in results:
            m = f"{r['date'].year}-{r['date'].month:02d}"
            months[m].append(r)

        out.append("| Month | Days | % Below 30s | % Below 1m | % Below 2m | % Below 5m | Avg 5m Move |")
        out.append("|-------|------|------------|-----------|-----------|-----------|------------|")

        for m in sorted(months.keys()):
            mr = months[m]
            n = len(mr)
            cols = [f"| {m} | {n}"]
            for cp in [30, 60, 120, 300]:
                moves = [r[f'cp_{cp}'] for r in mr if r.get(f'cp_{cp}') is not None]
                if moves:
                    below = sum(1 for m in moves if m < -0.05)
                    cols.append(f" {100*below/len(moves):.0f}%")
                else:
                    cols.append(" —")
            moves_5m = [r['cp_300'] for r in mr if r.get('cp_300') is not None]
            if moves_5m:
                cols.append(f" ${np.mean(moves_5m):+.2f}")
            else:
                cols.append(" —")
            out.append(" |".join(cols) + " |")

    # ── Streak analysis ───────────────────────────────────────────────
    if '1m' in results_by_tf:
        results = results_by_tf['1m']
        out.append("\n\n## Streak Analysis (1m data, 60s checkpoint)\n")

        moves = [(r['date'], r.get('cp_60')) for r in results if r.get('cp_60') is not None]
        streak_below = 0
        streak_above = 0
        max_below = 0
        max_above = 0
        streaks_below = []
        streaks_above = []

        for date, move in moves:
            if move < -0.05:
                streak_below += 1
                if streak_above > 0:
                    streaks_above.append(streak_above)
                    streak_above = 0
            elif move > 0.05:
                streak_above += 1
                if streak_below > 0:
                    streaks_below.append(streak_below)
                    streak_below = 0
            else:
                if streak_below > 0:
                    streaks_below.append(streak_below)
                if streak_above > 0:
                    streaks_above.append(streak_above)
                streak_below = streak_above = 0

        if streak_below > 0:
            streaks_below.append(streak_below)
        if streak_above > 0:
            streaks_above.append(streak_above)

        out.append(f"- Longest streak below open at 1m: **{max(streaks_below) if streaks_below else 0} days**")
        out.append(f"- Longest streak above open at 1m: **{max(streaks_above) if streaks_above else 0} days**")
        out.append(f"- Avg streak below: {np.mean(streaks_below):.1f} days" if streaks_below else "")
        out.append(f"- Avg streak above: {np.mean(streaks_above):.1f} days" if streaks_above else "")

    return "\n".join(out) + "\n"


def main():
    data = load_data()
    print()

    results_by_tf = {}
    tf_configs = [
        ('5s', data['5s'], 5),
        ('1m', data['1m'], 60),
        ('5m', data['5m'], 300),
    ]

    for tf_label, df, bar_secs in tf_configs:
        print(f"Analyzing {tf_label}...")
        results_by_tf[tf_label] = analyze_timeframe(df, tf_label, bar_secs)
        print(f"  → {len(results_by_tf[tf_label])} days")

    text = format_results(results_by_tf)
    with open(OUTPUT, 'w') as f:
        f.write(text)
    print(f"\nResults written to {OUTPUT}")
    print(text)


if __name__ == '__main__':
    main()
