#!/usr/bin/env python3
"""
TSLA calls: HOLD or BAIL in the first minutes?

You're holding calls at the open. What early signals predict whether
this will be a good day (hold) or bad day (bail)?

For each day, compute:
- Early observables: price vs open at checkpoints, dip size, recovery speed
- Call outcome: day high above open, day close vs open, time of day high

Then split by early signals to find HOLD/BAIL rules.
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
OUTPUT = os.path.join(BASE, "open-hold-or-bail.md")


def load_data():
    f1 = os.path.join(CACHE, "bars", "tsla_1_min_ib.parquet")
    df = pd.read_parquet(f1).set_index('date').sort_index()
    print(f"1m: {len(df):,} bars, {df.index.min().date()} to {df.index.max().date()}")
    return df


def analyze_days(df):
    market = df.between_time('09:30', '15:59')
    trading_days = sorted(set(market.index.date))
    results = []

    # Need prev day for levels
    prev_day_ohlc = None

    for date in trading_days:
        day_start = ET.localize(datetime.combine(date, datetime.strptime("09:30:00", "%H:%M:%S").time()))
        day_end = ET.localize(datetime.combine(date, datetime.strptime("15:59:00", "%H:%M:%S").time()))
        full_day = df.loc[(df.index >= day_start) & (df.index <= day_end)]

        if len(full_day) < 30:
            prev_day_ohlc = {
                'open': full_day.iloc[0]['open'] if len(full_day) > 0 else 0,
                'high': full_day['high'].max() if len(full_day) > 0 else 0,
                'low': full_day['low'].min() if len(full_day) > 0 else 0,
                'close': full_day.iloc[-1]['close'] if len(full_day) > 0 else 0,
            }
            continue

        open_price = full_day.iloc[0]['open']

        # ── Early observables ────────────────────────────────────────
        # Price at checkpoints
        checkpoints = {
            '30s': 30, '1m': 60, '2m': 120, '3m': 180, '5m': 300,
            '10m': 600, '15m': 900, '30m': 1800
        }
        price_at = {}
        for label, secs in checkpoints.items():
            target = day_start + timedelta(seconds=secs)
            # Find nearest bar
            tolerance = timedelta(seconds=30)
            candidates = full_day.loc[(full_day.index >= target - tolerance) & (full_day.index <= target + tolerance)]
            if len(candidates) > 0:
                diffs = abs(candidates.index - target)
                bar = candidates.loc[candidates.index[diffs.argmin()]]
                price_at[label] = bar['close'] - open_price
            else:
                before = full_day.loc[full_day.index <= target]
                if len(before) > 0:
                    price_at[label] = before.iloc[-1]['close'] - open_price
                else:
                    price_at[label] = None

        # First 5m stats
        first_5m = full_day.loc[full_day.index < day_start + timedelta(minutes=5)]
        dip_low = first_5m['low'].min() - open_price  # negative = below open
        first_5m_high = first_5m['high'].max() - open_price
        first_5m_range = first_5m_high - dip_low

        # Recovery: how fast does price get back to open after dipping?
        if dip_low < -0.10:
            dip_time = first_5m['low'].idxmin()
            after_dip = full_day.loc[full_day.index > dip_time]
            recovered = after_dip[after_dip['close'] >= open_price]
            if len(recovered) > 0:
                recovery_secs = (recovered.index[0] - dip_time).total_seconds()
            else:
                recovery_secs = 9999  # never recovered in session
        else:
            recovery_secs = 0  # no dip

        # First bar color
        first_bar_green = full_day.iloc[0]['close'] >= full_day.iloc[0]['open']

        # ── Call outcomes ────────────────────────────────────────────
        day_high = full_day['high'].max() - open_price
        day_low = full_day['low'].min() - open_price
        day_close = full_day.iloc[-1]['close'] - open_price
        day_high_time = full_day['high'].idxmax().astimezone(ET)
        day_high_minutes = (day_high_time - day_start.astimezone(ET)).total_seconds() / 60

        # MFE at various hold durations (from open)
        hold_mfe = {}
        for label, secs in [('30m', 1800), ('1h', 3600), ('2h', 7200), ('eod', 23400)]:
            end = day_start + timedelta(seconds=secs)
            window = full_day.loc[(full_day.index >= day_start) & (full_day.index <= min(end, day_end))]
            if len(window) > 0:
                hold_mfe[label] = window['high'].max() - open_price
            else:
                hold_mfe[label] = 0

        # Classify day
        bull_day = day_close > 0.10
        bear_day = day_close < -0.10

        # Gap from previous day
        gap = None
        if prev_day_ohlc:
            gap = open_price - prev_day_ohlc['close']

        result = {
            'date': date,
            'open': open_price,
            'price_at': price_at,
            'dip_low': dip_low,
            'first_5m_high': first_5m_high,
            'first_5m_range': first_5m_range,
            'recovery_secs': recovery_secs,
            'first_bar_green': first_bar_green,
            'day_high': day_high,
            'day_low': day_low,
            'day_close': day_close,
            'day_high_minutes': day_high_minutes,
            'hold_mfe': hold_mfe,
            'bull_day': bull_day,
            'bear_day': bear_day,
            'gap': gap,
        }
        results.append(result)

        prev_day_ohlc = {
            'open': open_price,
            'high': full_day['high'].max(),
            'low': full_day['low'].min(),
            'close': full_day.iloc[-1]['close'],
        }

    return results


def format_results(results):
    out = []
    out.append("# TSLA Calls: HOLD or BAIL?\n")
    out.append(f"**Data:** {len(results)} trading days, 1-minute candles")
    out.append(f"**Setup:** You hold TSLA calls at market open. What early signals tell you to HOLD or BAIL?\n")

    # ══════════════════════════════════════════════════════════════════
    # BASELINE: What happens to calls on an average day?
    # ══════════════════════════════════════════════════════════════════
    out.append("## Baseline: Average Day Holding Calls\n")
    out.append(f"- Days: {len(results)}")
    out.append(f"- Day high above open: avg **${np.mean([r['day_high'] for r in results]):.2f}**, median ${np.median([r['day_high'] for r in results]):.2f}")
    out.append(f"- Day close vs open: avg **${np.mean([r['day_close'] for r in results]):+.2f}**")
    out.append(f"- Day low below open: avg ${np.mean([r['day_low'] for r in results]):.2f}")
    out.append(f"- % days close above open: **{100*sum(1 for r in results if r['bull_day'])/len(results):.0f}%**")
    out.append(f"- % days high ≥ $1 above open: **{100*sum(1 for r in results if r['day_high'] >= 1)/len(results):.0f}%**")
    out.append(f"- % days high ≥ $3 above open: **{100*sum(1 for r in results if r['day_high'] >= 3)/len(results):.0f}%**")
    out.append(f"- % days high ≥ $5 above open: **{100*sum(1 for r in results if r['day_high'] >= 5)/len(results):.0f}%**\n")

    out.append("### MFE by Hold Duration (from open)\n")
    out.append("| Hold | Avg MFE | Median MFE | ≥$1 | ≥$3 | ≥$5 |")
    out.append("|------|---------|------------|-----|-----|-----|")
    for label in ['30m', '1h', '2h', 'eod']:
        mfes = [r['hold_mfe'].get(label, 0) for r in results]
        avg = np.mean(mfes)
        med = np.median(mfes)
        ge1 = sum(1 for m in mfes if m >= 1) / len(mfes)
        ge3 = sum(1 for m in mfes if m >= 3) / len(mfes)
        ge5 = sum(1 for m in mfes if m >= 5) / len(mfes)
        out.append(f"| {label} | ${avg:.2f} | ${med:.2f} | {100*ge1:.0f}% | {100*ge3:.0f}% | {100*ge5:.0f}% |")

    # ══════════════════════════════════════════════════════════════════
    # SIGNAL 1: Price at checkpoint (above vs below open)
    # ══════════════════════════════════════════════════════════════════
    out.append("\n---\n## Signal 1: Price vs Open at Checkpoint\n")
    out.append("If price is above/below open at time T, what happens to your calls?\n")

    for cp_label in ['30s', '1m', '2m', '5m', '10m', '15m', '30m']:
        above = [r for r in results if r['price_at'].get(cp_label) is not None and r['price_at'][cp_label] > 0.10]
        below = [r for r in results if r['price_at'].get(cp_label) is not None and r['price_at'][cp_label] < -0.10]

        if not above or not below:
            continue

        out.append(f"### At {cp_label}\n")
        out.append(f"| Metric | Above open ({len(above)}) | Below open ({len(below)}) | Edge |")
        out.append(f"|--------|------------------------|-------------------------|------|")

        ah = np.mean([r['day_high'] for r in above])
        bh = np.mean([r['day_high'] for r in below])
        out.append(f"| Avg day high | ${ah:.2f} | ${bh:.2f} | ${ah-bh:+.2f} |")

        ac = np.mean([r['day_close'] for r in above])
        bc = np.mean([r['day_close'] for r in below])
        out.append(f"| Avg day close | ${ac:+.2f} | ${bc:+.2f} | ${ac-bc:+.2f} |")

        aw = sum(1 for r in above if r['bull_day']) / len(above)
        bw = sum(1 for r in below if r['bull_day']) / len(below)
        out.append(f"| % close above open | {100*aw:.0f}% | {100*bw:.0f}% | {100*(aw-bw):+.0f}pp |")

        # Avg day high time
        aht = np.mean([r['day_high_minutes'] for r in above])
        bht = np.mean([r['day_high_minutes'] for r in below])
        out.append(f"| Avg high time | {int(aht//60)}:{int(aht%60):02d} after open | {int(bht//60)}:{int(bht%60):02d} after open | |")

        # MFE at 30m and 1h
        a30 = np.mean([r['hold_mfe'].get('30m', 0) for r in above])
        b30 = np.mean([r['hold_mfe'].get('30m', 0) for r in below])
        out.append(f"| 30m MFE | ${a30:.2f} | ${b30:.2f} | ${a30-b30:+.2f} |")

        out.append("")

    # ══════════════════════════════════════════════════════════════════
    # SIGNAL 2: Dip size in first 5 minutes
    # ══════════════════════════════════════════════════════════════════
    out.append("\n---\n## Signal 2: Opening Dip Size\n")
    out.append("How far does TSLA drop below open in the first 5 minutes → call fate?\n")

    out.append("| Dip | Days | Avg Day High | Avg Day Close | % Bull | 30m MFE | Day High Time |")
    out.append("|-----|------|-------------|---------------|--------|---------|---------------|")

    dip_buckets = [
        ('No dip (≥$0)', 0, 999),
        ('$0 to -$0.50', -0.50, 0),
        ('-$0.50 to -$1', -1.0, -0.50),
        ('-$1 to -$2', -2.0, -1.0),
        ('-$2 to -$3', -3.0, -2.0),
        ('-$3+', -999, -3.0),
    ]

    for label, lo, hi in dip_buckets:
        group = [r for r in results if lo <= r['dip_low'] < hi]
        if not group:
            continue
        dh = np.mean([r['day_high'] for r in group])
        dc = np.mean([r['day_close'] for r in group])
        bull = sum(1 for r in group if r['bull_day']) / len(group)
        m30 = np.mean([r['hold_mfe'].get('30m', 0) for r in group])
        ht = np.mean([r['day_high_minutes'] for r in group])
        out.append(f"| {label} | {len(group)} | ${dh:.2f} | ${dc:+.2f} | {100*bull:.0f}% | ${m30:.2f} | {int(ht//60)}:{int(ht%60):02d} |")

    # ══════════════════════════════════════════════════════════════════
    # SIGNAL 3: Recovery speed after dip
    # ══════════════════════════════════════════════════════════════════
    out.append("\n---\n## Signal 3: Recovery Speed\n")
    out.append("After dipping below open, how fast does TSLA recover? → call fate?\n")

    dipped = [r for r in results if r['dip_low'] < -0.50]
    out.append(f"Days with ≥$0.50 dip: {len(dipped)}\n")

    out.append("| Recovery Time | Days | Avg Day High | Avg Day Close | % Bull | Avg Dip |")
    out.append("|---------------|------|-------------|---------------|--------|---------|")

    recovery_buckets = [
        ('< 1 min', 0, 60),
        ('1-2 min', 60, 120),
        ('2-5 min', 120, 300),
        ('5-15 min', 300, 900),
        ('15-30 min', 900, 1800),
        ('Never (session)', 1800, 99999),
    ]

    for label, lo, hi in recovery_buckets:
        group = [r for r in dipped if lo <= r['recovery_secs'] < hi]
        if not group:
            continue
        dh = np.mean([r['day_high'] for r in group])
        dc = np.mean([r['day_close'] for r in group])
        bull = sum(1 for r in group if r['bull_day']) / len(group)
        dip = np.mean([r['dip_low'] for r in group])
        out.append(f"| {label} | {len(group)} | ${dh:.2f} | ${dc:+.2f} | {100*bull:.0f}% | ${dip:.2f} |")

    # ══════════════════════════════════════════════════════════════════
    # SIGNAL 4: Combinations (the money table)
    # ══════════════════════════════════════════════════════════════════
    out.append("\n---\n## Signal 4: Combined Signals — The Decision Matrix\n")
    out.append("Combining early checkpoint + dip size for HOLD/BAIL decision.\n")

    # 5m checkpoint is the decision point
    combos = [
        ("5m UP + small dip (<$1)", lambda r: r['price_at'].get('5m', 0) > 0.10 and r['dip_low'] > -1.0),
        ("5m UP + big dip (≥$1)", lambda r: r['price_at'].get('5m', 0) > 0.10 and r['dip_low'] <= -1.0),
        ("5m DOWN + small dip (<$1)", lambda r: r['price_at'].get('5m', 0) < -0.10 and r['dip_low'] > -1.0),
        ("5m DOWN + big dip (≥$1)", lambda r: r['price_at'].get('5m', 0) < -0.10 and r['dip_low'] <= -1.0),
        ("5m UP + recovered <2m", lambda r: r['price_at'].get('5m', 0) > 0.10 and r['recovery_secs'] < 120),
        ("5m UP + NOT recovered <2m", lambda r: r['price_at'].get('5m', 0) > 0.10 and r['recovery_secs'] >= 120),
        ("5m DOWN + NOT recovered", lambda r: r['price_at'].get('5m', 0) < -0.10 and r['recovery_secs'] >= 300),
        ("5m UP + gap up", lambda r: r['price_at'].get('5m', 0) > 0.10 and r.get('gap') is not None and r['gap'] > 0.10),
        ("5m UP + gap down", lambda r: r['price_at'].get('5m', 0) > 0.10 and r.get('gap') is not None and r['gap'] < -0.10),
        ("5m DOWN + gap up", lambda r: r['price_at'].get('5m', 0) < -0.10 and r.get('gap') is not None and r['gap'] > 0.10),
        ("5m DOWN + gap down", lambda r: r['price_at'].get('5m', 0) < -0.10 and r.get('gap') is not None and r['gap'] < -0.10),
        ("1m UP + 5m UP", lambda r: r['price_at'].get('1m', 0) > 0.10 and r['price_at'].get('5m', 0) > 0.10),
        ("1m DOWN + 5m UP (reversal)", lambda r: r['price_at'].get('1m', 0) < -0.10 and r['price_at'].get('5m', 0) > 0.10),
        ("1m UP + 5m DOWN (fakeout)", lambda r: r['price_at'].get('1m', 0) > 0.10 and r['price_at'].get('5m', 0) < -0.10),
        ("1m DOWN + 5m DOWN", lambda r: r['price_at'].get('1m', 0) < -0.10 and r['price_at'].get('5m', 0) < -0.10),
        # Strong moves
        ("5m > +$1", lambda r: r['price_at'].get('5m', 0) > 1.0),
        ("5m > +$2", lambda r: r['price_at'].get('5m', 0) > 2.0),
        ("5m < -$1", lambda r: r['price_at'].get('5m', 0) < -1.0),
        ("5m < -$2", lambda r: r['price_at'].get('5m', 0) < -2.0),
        # 15m and 30m for comparison (later decisions)
        ("15m UP", lambda r: r['price_at'].get('15m', 0) > 0.10),
        ("15m DOWN", lambda r: r['price_at'].get('15m', 0) < -0.10),
        ("30m UP", lambda r: r['price_at'].get('30m', 0) > 0.10),
        ("30m DOWN", lambda r: r['price_at'].get('30m', 0) < -0.10),
    ]

    out.append("| Signal | Days | Day High | Day Close | % Bull | 30m MFE | 1h MFE | Action |")
    out.append("|--------|------|----------|-----------|--------|---------|--------|--------|")

    for label, filt in combos:
        group = [r for r in results if filt(r)]
        if len(group) < 3:
            continue
        dh = np.mean([r['day_high'] for r in group])
        dc = np.mean([r['day_close'] for r in group])
        bull = sum(1 for r in group if r['bull_day']) / len(group)
        m30 = np.mean([r['hold_mfe'].get('30m', 0) for r in group])
        m1h = np.mean([r['hold_mfe'].get('1h', 0) for r in group])

        if bull >= 0.65 and dc > 1.0:
            action = "**HOLD** ✓"
        elif bull >= 0.55:
            action = "LEAN HOLD"
        elif bull <= 0.35 and dc < -1.0:
            action = "**BAIL** ✗"
        elif bull <= 0.45:
            action = "LEAN BAIL"
        else:
            action = "NEUTRAL"

        out.append(f"| {label} | {len(group)} | ${dh:.2f} | ${dc:+.2f} | {100*bull:.0f}% | ${m30:.2f} | ${m1h:.2f} | {action} |")

    # ══════════════════════════════════════════════════════════════════
    # OPTIMAL EXIT TIMING
    # ══════════════════════════════════════════════════════════════════
    out.append("\n---\n## When to Take Profit (Call Holders)\n")
    out.append("If you decide to HOLD, when is the best time to sell?\n")

    # For bull days only
    bull_days = [r for r in results if r['bull_day']]
    out.append(f"### Bull days ({len(bull_days)} days)\n")

    out.append("| Checkpoint | Avg Price vs Open | % Still Above Open | Avg MFE to Here |")
    out.append("|------------|-------------------|-------------------|-----------------|")

    for cp in ['5m', '10m', '15m', '30m']:
        prices = [r['price_at'].get(cp, 0) for r in bull_days if r['price_at'].get(cp) is not None]
        if prices:
            avg_price = np.mean(prices)
            pct_above = sum(1 for p in prices if p > 0.10) / len(prices)
            # MFE from open to this checkpoint
            secs = {'5m': 300, '10m': 600, '15m': 900, '30m': 1800}[cp]
            out.append(f"| {cp} | ${avg_price:+.2f} | {100*pct_above:.0f}% | — |")

    out.append(f"\n- Avg day high: **${np.mean([r['day_high'] for r in bull_days]):.2f}**")
    out.append(f"- Avg time of day high: **{int(np.mean([r['day_high_minutes'] for r in bull_days])//60)}:{int(np.mean([r['day_high_minutes'] for r in bull_days])%60):02d}** after open")
    out.append(f"- Median time of day high: **{int(np.median([r['day_high_minutes'] for r in bull_days])//60)}:{int(np.median([r['day_high_minutes'] for r in bull_days])%60):02d}** after open")

    # For bear days
    bear_days = [r for r in results if r['bear_day']]
    out.append(f"\n### Bear days ({len(bear_days)} days) — when to get out\n")

    out.append("| Checkpoint | Avg Price vs Open | % Above Open | Window Closing |")
    out.append("|------------|-------------------|-------------|----------------|")

    for cp in ['1m', '2m', '3m', '5m', '10m', '15m', '30m']:
        prices = [r['price_at'].get(cp, 0) for r in bear_days if r['price_at'].get(cp) is not None]
        if prices:
            avg_price = np.mean(prices)
            pct_above = sum(1 for p in prices if p > 0.10) / len(prices)
            out.append(f"| {cp} | ${avg_price:+.2f} | {100*pct_above:.0f}% | |")

    out.append(f"\n- Even on bear days, avg day high above open: **${np.mean([r['day_high'] for r in bear_days]):.2f}**")
    out.append(f"- Avg time of day high (bear): **{int(np.mean([r['day_high_minutes'] for r in bear_days])//60)}:{int(np.mean([r['day_high_minutes'] for r in bear_days])%60):02d}** after open")
    out.append(f"- Bear day high ≥$1: **{100*sum(1 for r in bear_days if r['day_high'] >= 1)/len(bear_days):.0f}%**")

    return "\n".join(out) + "\n"


def main():
    df = load_data()
    results = analyze_days(df)
    print(f"Analyzed {len(results)} days")

    text = format_results(results)
    with open(OUTPUT, 'w') as f:
        f.write(text)
    print(f"\nResults written to {OUTPUT}")
    print(text)


if __name__ == '__main__':
    main()
