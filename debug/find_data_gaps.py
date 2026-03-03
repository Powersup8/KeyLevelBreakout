#!/usr/bin/env python3
"""Find missing 5s bars in TSLA data around market open (9:30-9:34)."""

import os
import pandas as pd
import pytz
from datetime import datetime, timedelta

ET = pytz.timezone('US/Eastern')
BASE = os.path.dirname(os.path.abspath(__file__))
_PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(BASE)))
PARQ_5S_DIR = os.path.join(_PROJ_ROOT, "trading_bot", "cache", "bars_highres", "5sec")

df = pd.read_parquet(os.path.join(PARQ_5S_DIR, "tsla_5_secs_ib.parquet"))
df = df.set_index('date').sort_index()

market = df.between_time('09:30', '15:59')
trading_days = sorted(set(market.index.date))

# Suspect days from the analysis (TIME exits with |stock P&L| >> $1 SL)
suspect_days = {
    '2026-01-12': -9.58,
    '2026-01-16': -3.78,
    '2026-01-26': +7.58,
    '2026-01-27': +4.65,
    '2026-02-04': +13.77,
    '2026-02-19': -5.49,
    '2026-02-26': +5.49,
}

print("=== TSLA 5s Data Gaps at Open (9:30:00 - 9:34:00) ===\n")
print(f"{'Date':12} {'Bars':>5} {'Expected':>8} {'Missing':>7} {'1st Bar':>12} {'Gaps':}")
print("-" * 90)

all_gaps = []

for date in trading_days:
    day_start = ET.localize(datetime.combine(date, datetime.strptime("09:30:00", "%H:%M:%S").time()))
    window_end = day_start + timedelta(minutes=4)

    window = df.loc[(df.index >= day_start) & (df.index < window_end)]

    if len(window) == 0:
        print(f"{date}   NO DATA in 9:30-9:34 window")
        continue

    first_bar_time = window.index[0]
    first_offset = (first_bar_time - day_start).total_seconds()

    # Expected: one bar every 5 seconds = 48 bars in 4 minutes
    expected = 48
    actual = len(window)
    missing = expected - actual

    # Find specific gaps (where consecutive bars are >5s apart)
    gaps = []
    for i in range(1, len(window)):
        gap = (window.index[i] - window.index[i-1]).total_seconds()
        if gap > 6:  # more than 5s + 1s tolerance
            gap_start = window.index[i-1]
            gap_end = window.index[i]
            gap_start_local = gap_start.strftime('%H:%M:%S')
            gap_end_local = gap_end.strftime('%H:%M:%S')
            n_missing = int(gap / 5) - 1
            # Price jump during gap
            price_before = window.iloc[i-1]['close']
            price_after = window.iloc[i]['open']
            price_jump = price_after - price_before
            gaps.append({
                'date': date,
                'from': gap_start_local,
                'to': gap_end_local,
                'gap_secs': gap,
                'bars_missing': n_missing,
                'price_before': price_before,
                'price_after': price_after,
                'price_jump': price_jump,
            })

    suspect_flag = " <<<" if str(date) in suspect_days else ""
    gap_str = "; ".join(f"{g['from']}-{g['to']} ({g['gap_secs']:.0f}s, ${g['price_jump']:+.2f})" for g in gaps)
    first_bar_str = f"+{first_offset:.0f}s" if first_offset > 0 else "0s"

    if missing > 0 or gaps:
        print(f"{date}  {actual:5} {expected:8} {missing:7}  {first_bar_str:>10}  {gap_str}{suspect_flag}")
        all_gaps.extend(gaps)

print(f"\n\n=== Suspect Days Detail (TIME exits with |P&L| >> SL) ===\n")

for date_str, expected_pnl in suspect_days.items():
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    day_start = ET.localize(datetime.combine(date, datetime.strptime("09:30:00", "%H:%M:%S").time()))
    window_end = day_start + timedelta(minutes=4)
    window = df.loc[(df.index >= day_start) & (df.index < window_end)]

    print(f"\n--- {date_str} (TIME exit stock P&L: ${expected_pnl:+.2f}) ---")
    print(f"  Bars in 9:30-9:34: {len(window)}")

    if len(window) > 0:
        print(f"  First bar: {window.index[0].strftime('%H:%M:%S')} O={window.iloc[0]['open']:.2f} C={window.iloc[0]['close']:.2f}")
        # Show entry bar (at 9:30:30)
        entry_target = day_start + timedelta(seconds=30)
        entry_bars = window.loc[(window.index >= entry_target) & (window.index <= entry_target + timedelta(seconds=10))]
        if len(entry_bars) > 0:
            eb = entry_bars.iloc[0]
            print(f"  Entry bar (~9:30:30): {entry_bars.index[0].strftime('%H:%M:%S')} O={eb['open']:.2f} C={eb['close']:.2f}")
        else:
            # Find nearest bar
            after = window.loc[window.index >= entry_target]
            if len(after) > 0:
                eb = after.iloc[0]
                print(f"  Nearest bar after 9:30:30: {after.index[0].strftime('%H:%M:%S')} O={eb['open']:.2f} C={eb['close']:.2f}")
            else:
                print(f"  No bar at or after 9:30:30!")

    # Show all bars in the first 2.5 minutes
    show_end = day_start + timedelta(seconds=150)
    show_window = df.loc[(df.index >= day_start) & (df.index < show_end)]
    print(f"  All bars 9:30:00-9:32:30 ({len(show_window)} bars):")
    for idx, row in show_window.iterrows():
        t = idx.strftime('%H:%M:%S')
        gap_flag = ""
        print(f"    {t}  O={row['open']:7.2f}  H={row['high']:7.2f}  L={row['low']:7.2f}  C={row['close']:7.2f}  V={row.get('volume', 0):>8.0f}")

print(f"\n\n=== Summary ===")
print(f"Total days: {len(trading_days)}")
print(f"Days with gaps in 9:30-9:34: {len(set(g['date'] for g in all_gaps))}")
print(f"Total gaps: {len(all_gaps)}")
if all_gaps:
    avg_gap = sum(g['gap_secs'] for g in all_gaps) / len(all_gaps)
    max_gap = max(g['gap_secs'] for g in all_gaps)
    avg_jump = sum(abs(g['price_jump']) for g in all_gaps) / len(all_gaps)
    max_jump = max(abs(g['price_jump']) for g in all_gaps)
    print(f"Avg gap: {avg_gap:.0f}s, Max gap: {max_gap:.0f}s")
    print(f"Avg price jump during gap: ${avg_jump:.2f}, Max: ${max_jump:.2f}")
