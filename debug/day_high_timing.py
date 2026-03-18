#!/usr/bin/env python3
"""
When does TSLA make its day high? Find patterns in timing.
Uses all available timeframes: 5s (46 days), 1m (271 days), 5m (526 days).
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
OUTPUT = os.path.join(BASE, "day-high-timing.md")


def load_all():
    data = {}
    for label, path, name in [
        ('5s', os.path.join(CACHE, "bars_highres", "5sec"), "tsla_5_secs_ib.parquet"),
        ('1m', os.path.join(CACHE, "bars"), "tsla_1_min_ib.parquet"),
        ('5m', os.path.join(CACHE, "bars"), "tsla_5_mins_ib.parquet"),
    ]:
        fpath = os.path.join(path, name)
        df = pd.read_parquet(fpath).set_index('date').sort_index()
        data[label] = df
        print(f"{label}: {len(df):>8,} bars, {df.index.min().date()} to {df.index.max().date()}")
    return data


def analyze_day_highs(df, label):
    """For each trading day, find when the day high occurred."""
    market = df.between_time('09:30', '15:59')
    trading_days = sorted(set(market.index.date))

    days = []
    for date in trading_days:
        day_start = ET.localize(datetime.combine(date, datetime.strptime("09:30:00", "%H:%M:%S").time()))
        day_end = ET.localize(datetime.combine(date, datetime.strptime("15:59:59", "%H:%M:%S").time()))
        day_bars = df.loc[(df.index >= day_start) & (df.index <= day_end)]

        if len(day_bars) < 10:
            continue

        open_price = day_bars.iloc[0]['open']
        close_price = day_bars.iloc[-1]['close']

        # Find the bar with the highest high
        high_idx = day_bars['high'].idxmax()
        high_price = day_bars.loc[high_idx, 'high']
        high_time = high_idx

        # Also find day low
        low_idx = day_bars['low'].idxmin()
        low_price = day_bars.loc[low_idx, 'low']
        low_time = low_idx

        # Minutes from open
        high_mins = (high_time - day_start).total_seconds() / 60
        low_mins = (low_time - day_start).total_seconds() / 60

        # Time bucket (30-min intervals)
        high_hour = high_time.strftime('%H:%M')
        high_bucket_30 = f"{high_time.hour}:{(high_time.minute // 30) * 30:02d}"
        high_bucket_60 = f"{high_time.hour}:00"

        # Day type
        day_bullish = close_price > open_price
        high_above_open = high_price - open_price
        low_below_open = open_price - low_price

        # Was high in first 5 min?
        first5 = day_bars.loc[day_bars.index < day_start + timedelta(minutes=5)]
        first5_high = first5['high'].max() if len(first5) > 0 else 0
        high_in_first5 = (high_price - first5_high) < 0.01

        # Was high in first 30 min?
        first30 = day_bars.loc[day_bars.index < day_start + timedelta(minutes=30)]
        first30_high = first30['high'].max() if len(first30) > 0 else 0
        high_in_first30 = (high_price - first30_high) < 0.01

        # Was high in last hour?
        last_hour = day_bars.loc[day_bars.index >= day_start + timedelta(hours=5, minutes=30)]
        last_hour_high = last_hour['high'].max() if len(last_hour) > 0 else 0
        high_in_last_hour = (high_price - last_hour_high) < 0.01

        # Opening direction (1m close vs open)
        first_bar_dir = 'up' if day_bars.iloc[0]['close'] >= open_price else 'down'

        # Did high come before or after low?
        high_before_low = high_mins < low_mins

        days.append({
            'date': date,
            'open': open_price,
            'close': close_price,
            'day_high': high_price,
            'day_low': low_price,
            'high_time': high_time,
            'low_time': low_time,
            'high_mins': high_mins,
            'low_mins': low_mins,
            'high_bucket_30': high_bucket_30,
            'high_bucket_60': high_bucket_60,
            'high_above_open': high_above_open,
            'low_below_open': low_below_open,
            'day_bullish': day_bullish,
            'first_bar_dir': first_bar_dir,
            'high_in_first5': high_in_first5,
            'high_in_first30': high_in_first30,
            'high_in_last_hour': high_in_last_hour,
            'high_before_low': high_before_low,
            'day_range': high_price - low_price,
        })

    return days


def main():
    data = load_all()
    print()

    out = []
    out.append("# TSLA Day High Timing Analysis\n")
    out.append("**Question:** When does TSLA make its day high? Are there patterns?\n")

    all_results = {}
    for label in ['5s', '1m', '5m']:
        print(f"Analyzing {label}...")
        all_results[label] = analyze_day_highs(data[label], label)
        print(f"  → {len(all_results[label])} days")

    # ── Use 1m as primary (best balance), show all three ──────────────
    for label in ['5s', '1m', '5m']:
        days = all_results[label]
        n = len(days)
        date_range = f"{days[0]['date']} to {days[-1]['date']}"

        out.append(f"\n---\n## {label} data — {n} days ({date_range})\n")

        # ── Time distribution (30-min buckets) ────────────────────────
        out.append("### Day High by Time Bucket (30-min)\n")
        buckets = defaultdict(int)
        for d in days:
            buckets[d['high_bucket_30']] += 1

        # Sort by time
        sorted_buckets = sorted(buckets.items(), key=lambda x: x[0])
        out.append("| Time Bucket | Count | % | Bar |")
        out.append("|-------------|-------|---|-----|")
        for bucket, count in sorted_buckets:
            pct = 100 * count / n
            bar = "█" * int(pct / 2)
            out.append(f"| {bucket} | {count} | {pct:.0f}% | {bar} |")

        # ── Time distribution (60-min buckets) ────────────────────────
        out.append("\n### Day High by Hour\n")
        buckets_60 = defaultdict(int)
        for d in days:
            buckets_60[d['high_bucket_60']] += 1

        sorted_60 = sorted(buckets_60.items(), key=lambda x: x[0])
        out.append("| Hour | Count | % | Bar |")
        out.append("|------|-------|---|-----|")
        for bucket, count in sorted_60:
            pct = 100 * count / n
            bar = "█" * int(pct / 2)
            out.append(f"| {bucket} | {count} | {pct:.0f}% | {bar} |")

        # ── Key stats ─────────────────────────────────────────────────
        out.append("\n### Key Stats\n")
        high_mins_list = [d['high_mins'] for d in days]
        out.append(f"- Avg time of day high: **{int(np.mean(high_mins_list))} min** after open ({_mins_to_time(np.mean(high_mins_list))})")
        out.append(f"- Median: **{int(np.median(high_mins_list))} min** ({_mins_to_time(np.median(high_mins_list))})")
        out.append(f"- High in first 5 min: **{sum(1 for d in days if d['high_in_first5'])}** ({100*sum(1 for d in days if d['high_in_first5'])/n:.0f}%)")
        out.append(f"- High in first 30 min: **{sum(1 for d in days if d['high_in_first30'])}** ({100*sum(1 for d in days if d['high_in_first30'])/n:.0f}%)")
        out.append(f"- High in last hour (15:00-16:00): **{sum(1 for d in days if d['high_in_last_hour'])}** ({100*sum(1 for d in days if d['high_in_last_hour'])/n:.0f}%)")
        out.append(f"- High before low: **{sum(1 for d in days if d['high_before_low'])}** ({100*sum(1 for d in days if d['high_before_low'])/n:.0f}%)")

    # ── Deep analysis on 1m data (271 days) ───────────────────────────
    days = all_results['1m']
    n = len(days)

    out.append(f"\n---\n## Deep Analysis (1m data, {n} days)\n")

    # ── Bullish vs Bearish day high timing ────────────────────────────
    out.append("### Day High Timing: Bullish vs Bearish Days\n")
    bull_days = [d for d in days if d['day_bullish']]
    bear_days = [d for d in days if not d['day_bullish']]

    out.append(f"| Metric | Bullish Days ({len(bull_days)}) | Bearish Days ({len(bear_days)}) |")
    out.append("|--------|------|------|")
    out.append(f"| Avg high time | {_mins_to_time(np.mean([d['high_mins'] for d in bull_days]))} | {_mins_to_time(np.mean([d['high_mins'] for d in bear_days]))} |")
    out.append(f"| Median high time | {_mins_to_time(np.median([d['high_mins'] for d in bull_days]))} | {_mins_to_time(np.median([d['high_mins'] for d in bear_days]))} |")
    out.append(f"| High in first 5m | {100*sum(1 for d in bull_days if d['high_in_first5'])/len(bull_days):.0f}% | {100*sum(1 for d in bear_days if d['high_in_first5'])/len(bear_days):.0f}% |")
    out.append(f"| High in first 30m | {100*sum(1 for d in bull_days if d['high_in_first30'])/len(bull_days):.0f}% | {100*sum(1 for d in bear_days if d['high_in_first30'])/len(bear_days):.0f}% |")
    out.append(f"| High in last hour | {100*sum(1 for d in bull_days if d['high_in_last_hour'])/len(bull_days):.0f}% | {100*sum(1 for d in bear_days if d['high_in_last_hour'])/len(bear_days):.0f}% |")
    out.append(f"| High before low | {100*sum(1 for d in bull_days if d['high_before_low'])/len(bull_days):.0f}% | {100*sum(1 for d in bear_days if d['high_before_low'])/len(bear_days):.0f}% |")
    out.append(f"| Avg high above open | ${np.mean([d['high_above_open'] for d in bull_days]):.2f} | ${np.mean([d['high_above_open'] for d in bear_days]):.2f} |")
    out.append(f"| Avg day range | ${np.mean([d['day_range'] for d in bull_days]):.2f} | ${np.mean([d['day_range'] for d in bear_days]):.2f} |")

    # Hourly distribution split by bull/bear
    out.append("\n### Hourly Distribution: Bull vs Bear Days\n")
    out.append("| Hour | Bull % | Bear % | Bull Count | Bear Count |")
    out.append("|------|--------|--------|------------|------------|")

    bull_buckets = defaultdict(int)
    bear_buckets = defaultdict(int)
    for d in bull_days:
        bull_buckets[d['high_bucket_60']] += 1
    for d in bear_days:
        bear_buckets[d['high_bucket_60']] += 1

    all_hours = sorted(set(list(bull_buckets.keys()) + list(bear_buckets.keys())))
    for hour in all_hours:
        bc = bull_buckets.get(hour, 0)
        brc = bear_buckets.get(hour, 0)
        out.append(f"| {hour} | {100*bc/len(bull_days):.0f}% | {100*brc/len(bear_days):.0f}% | {bc} | {brc} |")

    # ── Opening direction vs day high timing ──────────────────────────
    out.append("\n### Opening Direction vs Day High Timing\n")
    up_open = [d for d in days if d['first_bar_dir'] == 'up']
    down_open = [d for d in days if d['first_bar_dir'] == 'down']

    out.append(f"| Metric | Opens Up ({len(up_open)}) | Opens Down ({len(down_open)}) |")
    out.append("|--------|------|------|")
    out.append(f"| Avg high time | {_mins_to_time(np.mean([d['high_mins'] for d in up_open]))} | {_mins_to_time(np.mean([d['high_mins'] for d in down_open]))} |")
    out.append(f"| High in first 5m | {100*sum(1 for d in up_open if d['high_in_first5'])/len(up_open):.0f}% | {100*sum(1 for d in down_open if d['high_in_first5'])/len(down_open):.0f}% |")
    out.append(f"| High in first 30m | {100*sum(1 for d in up_open if d['high_in_first30'])/len(up_open):.0f}% | {100*sum(1 for d in down_open if d['high_in_first30'])/len(down_open):.0f}% |")
    out.append(f"| High in last hour | {100*sum(1 for d in up_open if d['high_in_last_hour'])/len(up_open):.0f}% | {100*sum(1 for d in down_open if d['high_in_last_hour'])/len(down_open):.0f}% |")
    out.append(f"| Closes bullish | {100*sum(1 for d in up_open if d['day_bullish'])/len(up_open):.0f}% | {100*sum(1 for d in down_open if d['day_bullish'])/len(down_open):.0f}% |")

    # ── Day high timing vs day range ──────────────────────────────────
    out.append("\n### Day High Timing vs Day Range\n")
    ranges = sorted(days, key=lambda d: d['day_range'])
    q1 = ranges[:n//4]
    q4 = ranges[3*n//4:]

    out.append(f"| Metric | Small Range (Q1, <${np.max([d['day_range'] for d in q1]):.0f}) | Large Range (Q4, >${np.min([d['day_range'] for d in q4]):.0f}) |")
    out.append("|--------|------|------|")
    out.append(f"| Avg high time | {_mins_to_time(np.mean([d['high_mins'] for d in q1]))} | {_mins_to_time(np.mean([d['high_mins'] for d in q4]))} |")
    out.append(f"| High in first 30m | {100*sum(1 for d in q1 if d['high_in_first30'])/len(q1):.0f}% | {100*sum(1 for d in q4 if d['high_in_first30'])/len(q4):.0f}% |")
    out.append(f"| High in last hour | {100*sum(1 for d in q1 if d['high_in_last_hour'])/len(q1):.0f}% | {100*sum(1 for d in q4 if d['high_in_last_hour'])/len(q4):.0f}% |")
    out.append(f"| Avg range | ${np.mean([d['day_range'] for d in q1]):.2f} | ${np.mean([d['day_range'] for d in q4]):.2f} |")

    # ── Cumulative: what % of day highs have occurred by time X ───────
    out.append("\n### Cumulative: % of Day Highs Occurred by Time X\n")
    out.append("| Time | % of Highs | Cumulative |")
    out.append("|------|-----------|------------|")
    cum = 0
    for mins in [5, 10, 15, 30, 60, 90, 120, 180, 240, 300, 330, 360, 390]:
        count = sum(1 for d in days if d['high_mins'] <= mins)
        pct = 100 * count / n
        bar = "█" * int(pct / 2.5)
        t = _mins_to_time(mins)
        out.append(f"| {t} ({mins}m) | {pct:.0f}% | {bar} |")

    # ── Day of week ───────────────────────────────────────────────────
    out.append("\n### Day High Timing by Day of Week\n")
    out.append("| Day | Count | Avg High Time | High in 1st 30m | High in Last Hour |")
    out.append("|-----|-------|---------------|-----------------|-------------------|")
    dow_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    for dow in range(5):
        dow_days = [d for d in days if d['date'].weekday() == dow]
        if not dow_days:
            continue
        out.append(f"| {dow_names[dow]} | {len(dow_days)} | {_mins_to_time(np.mean([d['high_mins'] for d in dow_days]))} | {100*sum(1 for d in dow_days if d['high_in_first30'])/len(dow_days):.0f}% | {100*sum(1 for d in dow_days if d['high_in_last_hour'])/len(dow_days):.0f}% |")

    # ── Monthly trend ─────────────────────────────────────────────────
    out.append("\n### Monthly Avg Day High Time\n")
    out.append("| Month | Days | Avg High Time | High in 1st 30m | Avg High Above Open |")
    out.append("|-------|------|---------------|-----------------|---------------------|")
    months = defaultdict(list)
    for d in days:
        m = f"{d['date'].year}-{d['date'].month:02d}"
        months[m].append(d)
    for m in sorted(months.keys()):
        md = months[m]
        out.append(f"| {m} | {len(md)} | {_mins_to_time(np.mean([d['high_mins'] for d in md]))} | {100*sum(1 for d in md if d['high_in_first30'])/len(md):.0f}% | ${np.mean([d['high_above_open'] for d in md]):.2f} |")

    # ── Write ─────────────────────────────────────────────────────────
    text = "\n".join(out) + "\n"
    with open(OUTPUT, 'w') as f:
        f.write(text)
    print(f"\nResults written to {OUTPUT}")
    print(text)


def _mins_to_time(mins):
    """Convert minutes-from-open to ET clock time string."""
    h = 9 + int((30 + mins) // 60)
    m = int((30 + mins) % 60)
    return f"{h}:{m:02d}"


if __name__ == '__main__':
    main()
