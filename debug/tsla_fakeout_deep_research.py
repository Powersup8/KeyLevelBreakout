"""
TSLA Fakeout Deep Research — What opening patterns predict winners vs losers?
Uses IB 5s data (if available) or 15s data + 1m for outcomes.
Analyzes the first 60s at high resolution to find what separates good from bad opens.
"""

import pandas as pd
import numpy as np
from pathlib import Path

CACHE = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache')
OUT = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug')

def load(fname):
    df = pd.read_parquet(CACHE / fname)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC').tz_convert('America/New_York')
    else:
        df.index = df.index.tz_convert('America/New_York')
    return df

print("Loading data...")
df1m = load('bars/tsla_1_min_ib.parquet')

# Use 15s data (226 days RTH coverage) — build 30s bars from pairs of 15s bars
df_hires = load('bars_highres/15sec/tsla_15_secs_ib.parquet')
hires_tf = '15s'
print(f"Hi-res: {hires_tf}, {df_hires.shape}, {df_hires.index.min()} to {df_hires.index.max()}")
print(f"1m: {df1m.shape}")

# ─────────────────────────────────────────────
# BUILD DAILY FEATURES: first-minute microstructure + outcomes
# ─────────────────────────────────────────────

market_days = sorted(df1m.between_time('09:30', '16:00').index.normalize().unique())
hires_days = set(df_hires.index.normalize().unique()) if df_hires is not None else set()

rows = []
for d in market_days:
    mkt = df1m[df1m.index.normalize() == d].between_time('09:30', '16:00')
    if len(mkt) < 10:
        continue

    open_930 = mkt.iloc[0]['open']
    eod_close = mkt.iloc[-1]['close']

    # 5m rule (9:34 close vs 9:30 open)
    b934 = mkt.between_time('09:34', '09:34')
    close_934 = b934.iloc[0]['close'] if len(b934) > 0 else np.nan
    is_hold = close_934 > open_930 if not np.isnan(close_934) else None

    # ORB (9:30-9:34)
    orb_bars = mkt.between_time('09:30', '09:34')
    orb_high = orb_bars['high'].max()
    orb_low = orb_bars['low'].min()

    # 10m P&L
    b940 = mkt.between_time('09:39', '09:39')
    pnl_10m = b940.iloc[0]['close'] - open_930 if len(b940) > 0 else np.nan

    # ORB breakout outcome (did bull break happen by 9:55?)
    post_orb = mkt.between_time('09:35', '09:55')
    orb_bull_break = (post_orb['close'] > orb_high).any() if len(post_orb) > 0 else False
    orb_bear_break = (post_orb['close'] < orb_low).any() if len(post_orb) > 0 else False

    row = {
        'date': d,
        'open_930': open_930,
        'day_pnl': eod_close - open_930,
        'pnl_10m': pnl_10m,
        'is_hold': is_hold,
        'orb_high': orb_high,
        'orb_low': orb_low,
        'orb_width': orb_high - orb_low,
        'orb_bull_break': orb_bull_break,
        'orb_bear_break': orb_bear_break,
    }

    # ── 1m bar features (always available) ──
    bar1_1m = mkt.iloc[0]  # 9:30 bar
    row['bar1_1m_open'] = bar1_1m['open']
    row['bar1_1m_high'] = bar1_1m['high']
    row['bar1_1m_low'] = bar1_1m['low']
    row['bar1_1m_close'] = bar1_1m['close']
    row['bar1_1m_range'] = bar1_1m['high'] - bar1_1m['low']
    row['bar1_1m_body'] = bar1_1m['close'] - bar1_1m['open']
    row['bar1_1m_up'] = bar1_1m['close'] >= bar1_1m['open']
    row['bar1_1m_upper_wick'] = bar1_1m['high'] - max(bar1_1m['open'], bar1_1m['close'])
    row['bar1_1m_lower_wick'] = min(bar1_1m['open'], bar1_1m['close']) - bar1_1m['low']
    row['bar1_1m_body_pct'] = abs(bar1_1m['close'] - bar1_1m['open']) / row['bar1_1m_range'] if row['bar1_1m_range'] > 0 else 0
    row['bar1_1m_vol'] = bar1_1m['volume']

    # ── Hi-res 30s bar features (from 15s data — 2 bars per 30s window) ──
    if d in hires_days:
        day_hr = df_hires[df_hires.index.normalize() == d]

        # Bar1: 9:30:00-9:30:29 (two 15s bars: 9:30:00 and 9:30:15)
        b1 = day_hr.between_time('09:30:00', '09:30:29')
        # Bar2: 9:30:30-9:30:59 (two 15s bars: 9:30:30 and 9:30:45)
        b2 = day_hr.between_time('09:30:30', '09:30:59')

        if len(b1) >= 1 and len(b2) >= 1:
            b1_o, b1_h, b1_l, b1_c = b1.iloc[0]['open'], b1['high'].max(), b1['low'].min(), b1.iloc[-1]['close']
            b2_o, b2_h, b2_l, b2_c = b2.iloc[0]['open'], b2['high'].max(), b2['low'].min(), b2.iloc[-1]['close']

            b1_move = b1_c - b1_o
            b2_move = b2_c - b2_o
            b1_range = b1_h - b1_l
            b2_range = b2_h - b2_l
            b1_up = b1_c >= b1_o
            b2_up = b2_c >= b2_o

            row['b1_open'] = b1_o
            row['b1_close'] = b1_c
            row['b1_high'] = b1_h
            row['b1_low'] = b1_l
            row['b1_move'] = b1_move
            row['b1_range'] = b1_range
            row['b1_up'] = b1_up
            row['b2_open'] = b2_o
            row['b2_close'] = b2_c
            row['b2_high'] = b2_h
            row['b2_low'] = b2_l
            row['b2_move'] = b2_move
            row['b2_range'] = b2_range
            row['b2_up'] = b2_up

            # A6 pattern
            if b1_up and not b2_up:
                row['a6_pattern'] = 'UP_DN'
            elif b1_up and b2_up:
                row['a6_pattern'] = 'UP_UP'
            elif not b1_up and not b2_up:
                row['a6_pattern'] = 'DN_DN'
            else:
                row['a6_pattern'] = 'DN_UP'

            # Giveback metrics
            if abs(b1_move) > 0.01:
                row['giveback_pct'] = -b2_move / b1_move  # positive = bar2 reversed bar1
            else:
                row['giveback_pct'] = 0
            row['giveback_abs'] = abs(b2_move)

            # Peak-to-close: how much did price fall from the first 30s high?
            row['peak_to_b2_close'] = b1_h - b2_c
            row['peak_to_b2_close_pct'] = (b1_h - b2_c) / b1_range if b1_range > 0 else 0

            # Did price make new lows in bar2?
            row['b2_below_b1_low'] = b2_l < b1_l

            # Volume shift: bar2 vol vs bar1 vol
            b1_vol = b1['volume'].sum()
            b2_vol = b2['volume'].sum()
            row['vol_shift'] = b2_vol / b1_vol if b1_vol > 0 else np.nan

            # ── Microstructure: 15s-level analysis within first 60s ──
            first60 = day_hr.between_time('09:30:00', '09:30:59')
            if len(first60) >= 3:
                prices = first60['close'].values
                # Time to peak: which 5s bar had the highest price?
                peak_idx = np.argmax(first60['high'].values)
                row['time_to_peak_bars'] = peak_idx
                row['time_to_peak_pct'] = peak_idx / len(first60)  # 0=first bar, 1=last bar

                # Momentum decay: split into thirds
                n = len(prices)
                t1 = prices[n//3] - prices[0]
                t2 = prices[2*n//3] - prices[n//3]
                t3 = prices[-1] - prices[2*n//3]
                row['momentum_t1'] = t1
                row['momentum_t2'] = t2
                row['momentum_t3'] = t3
                row['momentum_decay'] = t3 - t1  # negative = fading

                # Max drawdown from peak within first 60s
                running_high = np.maximum.accumulate(first60['high'].values)
                dd = (running_high - first60['low'].values).max()
                row['first60s_max_dd'] = dd

                # Recovery: did price recover after hitting the low?
                low_idx = np.argmin(first60['low'].values)
                if low_idx < len(prices) - 1:
                    recovery = prices[-1] - first60['low'].values[low_idx]
                    row['recovery_from_low'] = recovery
                else:
                    row['recovery_from_low'] = 0

    rows.append(row)

df = pd.DataFrame(rows).set_index('date')
has_30s = df['a6_pattern'].notna()
print(f"Total days: {len(df)}, with 30s data: {has_30s.sum()}")

# ─────────────────────────────────────────────
# ANALYSIS
# ─────────────────────────────────────────────

report = []
report.append("# TSLA Fakeout Deep Research — Opening Pattern Analysis")
report.append(f"*Date: 2026-03-18 | {has_30s.sum()} days with sub-30s data, {len(df)} total*\n")

# ── Section 1: A6 Pattern × Outcome ──
report.append("## 1. A6 Pattern Baseline (30s bars)\n")

d30 = df[has_30s].copy()
report.append("| Pattern | n | Day Win% | Avg P&L | ORB Bull% | Worst% |")
report.append("|---|---|---|---|---|---|")
for pat in ['UP_UP', 'UP_DN', 'DN_UP', 'DN_DN']:
    subset = d30[d30['a6_pattern'] == pat]
    n = len(subset)
    if n == 0: continue
    win = (subset['day_pnl'] > 0).mean() * 100
    avg = subset['day_pnl'].mean()
    orb_bull = subset['orb_bull_break'].mean() * 100
    worst = (subset['day_pnl'] < -5).mean() * 100
    report.append(f"| {pat} | {n} | {win:.0f}% | ${avg:.2f} | {orb_bull:.0f}% | {worst:.0f}% |")

# ── Section 2: UP→DOWN deep dive — what separates winners from losers? ──
report.append("\n## 2. UP→DOWN Deep Dive — Winner vs Loser Anatomy\n")

updn = d30[d30['a6_pattern'] == 'UP_DN'].copy()
if len(updn) > 0:
    winners = updn[updn['day_pnl'] > 0]
    losers = updn[updn['day_pnl'] <= 0]

    report.append(f"UP→DOWN days: {len(updn)} total, {len(winners)} winners, {len(losers)} losers\n")

    metrics = [
        ('b1_move', 'Bar1 move ($)'),
        ('b2_move', 'Bar2 move ($)'),
        ('b1_range', 'Bar1 range ($)'),
        ('giveback_pct', 'Giveback (bar2/bar1)'),
        ('giveback_abs', 'Giveback absolute ($)'),
        ('peak_to_b2_close', 'Peak to bar2 close ($)'),
        ('peak_to_b2_close_pct', 'Peak to bar2 close (% of bar1 range)'),
        ('b2_below_b1_low', 'Bar2 made new low'),
        ('vol_shift', 'Volume shift (bar2/bar1)'),
        ('time_to_peak_pct', 'Time to peak (0=start, 1=end)'),
        ('momentum_decay', 'Momentum decay (t3-t1)'),
        ('first60s_max_dd', 'First 60s max drawdown ($)'),
        ('recovery_from_low', 'Recovery from low ($)'),
        ('bar1_1m_body_pct', '1m bar body % of range'),
    ]

    report.append("| Metric | Winners avg | Losers avg | Spread | Discriminant? |")
    report.append("|---|---|---|---|---|")
    for col, label in metrics:
        if col not in updn.columns:
            continue
        w_val = winners[col].mean() if len(winners) > 0 else np.nan
        l_val = losers[col].mean() if len(losers) > 0 else np.nan
        spread = w_val - l_val if not np.isnan(w_val) and not np.isnan(l_val) else np.nan
        # Simple discrimination test
        disc = ""
        if not np.isnan(spread):
            if abs(spread) > 0.1 * max(abs(w_val), abs(l_val), 0.01):
                disc = "YES" if abs(spread) > 0.3 * max(abs(w_val), abs(l_val), 0.01) else "maybe"
        report.append(f"| {label} | {w_val:.3f} | {l_val:.3f} | {spread:+.3f} | {disc} |")

# ── Section 3: Giveback threshold analysis ──
report.append("\n## 3. Giveback Threshold — Does Severity Matter?\n")

if len(updn) > 0:
    report.append("| Giveback % | n | Day Win% | Avg P&L | ORB Bull% | Worst% | Verdict |")
    report.append("|---|---|---|---|---|---|---|")

    thresholds = [
        ('<20% (mild pullback)', updn['giveback_pct'] < 0.20),
        ('20-40%', (updn['giveback_pct'] >= 0.20) & (updn['giveback_pct'] < 0.40)),
        ('40-60%', (updn['giveback_pct'] >= 0.40) & (updn['giveback_pct'] < 0.60)),
        ('60-80%', (updn['giveback_pct'] >= 0.60) & (updn['giveback_pct'] < 0.80)),
        ('>80% (hard reversal)', updn['giveback_pct'] >= 0.80),
    ]

    for label, mask in thresholds:
        subset = updn[mask]
        n = len(subset)
        if n == 0: continue
        win = (subset['day_pnl'] > 0).mean() * 100
        avg = subset['day_pnl'].mean()
        orb_bull = subset['orb_bull_break'].mean() * 100
        worst = (subset['day_pnl'] < -5).mean() * 100
        verdict = "OK" if win >= 50 else "WARN" if win >= 35 else "DANGER"
        report.append(f"| {label} | {n} | {win:.0f}% | ${avg:.2f} | {orb_bull:.0f}% | {worst:.0f}% | {verdict} |")

# ── Section 4: Other discriminating factors for UP→DOWN ──
report.append("\n## 4. Other Factors Within UP→DOWN\n")

if len(updn) > 0:
    # Bar2 made new low (below bar1 low)?
    report.append("### Bar2 breaks bar1 low?")
    for val, label in [(True, 'Yes — new low'), (False, 'No — held above')]:
        if 'b2_below_b1_low' not in updn.columns:
            break
        subset = updn[updn['b2_below_b1_low'] == val]
        if len(subset) == 0: continue
        win = (subset['day_pnl'] > 0).mean() * 100
        avg = subset['day_pnl'].mean()
        worst = (subset['day_pnl'] < -5).mean() * 100
        report.append(f"- {label}: n={len(subset)}, Win={win:.0f}%, Avg=${avg:.2f}, Worst={worst:.0f}%")

    # Volume shift
    report.append("\n### Volume acceleration (bar2 vol / bar1 vol)")
    if 'vol_shift' in updn.columns:
        med = updn['vol_shift'].median()
        lo = updn[updn['vol_shift'] <= med]
        hi = updn[updn['vol_shift'] > med]
        for label, subset in [('Low vol shift (selling dries up)', lo), ('High vol shift (selling intensifies)', hi)]:
            if len(subset) == 0: continue
            win = (subset['day_pnl'] > 0).mean() * 100
            avg = subset['day_pnl'].mean()
            report.append(f"- {label}: n={len(subset)}, Win={win:.0f}%, Avg=${avg:.2f}")

    # Time to peak
    report.append("\n### Time to peak within first 60s")
    if 'time_to_peak_pct' in updn.columns:
        early = updn[updn['time_to_peak_pct'] < 0.3]
        mid = updn[(updn['time_to_peak_pct'] >= 0.3) & (updn['time_to_peak_pct'] < 0.6)]
        late = updn[updn['time_to_peak_pct'] >= 0.6]
        for label, subset in [('Early peak (<30%)', early), ('Mid peak (30-60%)', mid), ('Late peak (>60%)', late)]:
            if len(subset) == 0: continue
            win = (subset['day_pnl'] > 0).mean() * 100
            avg = subset['day_pnl'].mean()
            report.append(f"- {label}: n={len(subset)}, Win={win:.0f}%, Avg=${avg:.2f}")

    # Momentum decay
    report.append("\n### Momentum decay (3rd third move - 1st third move)")
    if 'momentum_decay' in updn.columns:
        accel = updn[updn['momentum_decay'] > 0]
        decel = updn[updn['momentum_decay'] <= 0]
        for label, subset in [('Accelerating (recovering)', accel), ('Decelerating (fading)', decel)]:
            if len(subset) == 0: continue
            win = (subset['day_pnl'] > 0).mean() * 100
            avg = subset['day_pnl'].mean()
            worst = (subset['day_pnl'] < -5).mean() * 100
            report.append(f"- {label}: n={len(subset)}, Win={win:.0f}%, Avg=${avg:.2f}, Worst={worst:.0f}%")

# ── Section 5: Cross with HOLD/BAIL and ORB ──
report.append("\n## 5. UP→DOWN × 5m Rule × ORB Outcome\n")

if len(updn) > 0:
    report.append("| Pattern | 5m | ORB | n | Win% | Avg P&L | Worst% |")
    report.append("|---|---|---|---|---|---|---|")

    for hold_label, hold_val in [('HOLD', True), ('BAIL', False)]:
        for orb_label, orb_val in [('Bull break', True), ('Bear/None', False)]:
            if hold_val is not None:
                subset = updn[(updn['is_hold'] == hold_val) & (updn['orb_bull_break'] == orb_val)]
            else:
                subset = updn[updn['orb_bull_break'] == orb_val]
            if len(subset) < 3: continue
            win = (subset['day_pnl'] > 0).mean() * 100
            avg = subset['day_pnl'].mean()
            worst = (subset['day_pnl'] < -5).mean() * 100
            report.append(f"| UP_DN | {hold_label} | {orb_label} | {len(subset)} | {win:.0f}% | ${avg:.2f} | {worst:.0f}% |")

# ── Section 6: What about ALL patterns × giveback? ──
report.append("\n## 6. All Patterns — Giveback as Universal Metric\n")
report.append("Does giveback % matter even for non-UP→DOWN patterns?\n")

for pat in ['UP_UP', 'UP_DN', 'DN_UP', 'DN_DN']:
    subset = d30[d30['a6_pattern'] == pat]
    if len(subset) < 5 or 'giveback_pct' not in subset.columns:
        continue
    report.append(f"\n### {pat}")
    med = subset['giveback_pct'].median()
    lo = subset[subset['giveback_pct'] <= med]
    hi = subset[subset['giveback_pct'] > med]
    for label, s in [('Low giveback', lo), ('High giveback', hi)]:
        if len(s) == 0: continue
        win = (s['day_pnl'] > 0).mean() * 100
        avg = s['day_pnl'].mean()
        report.append(f"- {label}: n={len(s)}, Win={win:.0f}%, Avg=${avg:.2f}")

# ── Section 7: Recommendations ──
report.append("\n---\n## 7. Recommendations\n")
report.append("*(Filled after reviewing results)*\n")

report_text = '\n'.join(report)
outfile = OUT / 'tsla-fakeout-deep-research.md'
outfile.write_text(report_text)
print(f"\nReport written to {outfile}")
print(f"Report: {len(report_text)} chars")
