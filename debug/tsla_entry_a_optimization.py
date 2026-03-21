#!/usr/bin/env python3
"""
TSLA Open Scalper — Entry A Optimization
Entry A = days where bar0 (first 15sec) moves in PM VWAP direction.
Currently 60% of days, 49% win rate (no edge). Find filters or kill it.
"""

import os, sys
import pandas as pd
import numpy as np
from scipy import stats

# ── Paths ──
PARQ = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars_highres/15sec/tsla_15_secs_ib.parquet"
OUT = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug/tsla-scalp-entry-a-optimization.md"

def load():
    df = pd.read_parquet(PARQ)
    df['date'] = pd.to_datetime(df['date'], utc=True).dt.tz_convert('US/Eastern')
    df = df.set_index('date').sort_index()
    print(f"Loaded {len(df):,} bars, {df.index.min()} to {df.index.max()}")
    return df

def get_pm_vwap(day_bars):
    """Compute PM VWAP from 9:20-9:29 bars."""
    pm = day_bars.between_time('09:20', '09:28:59')
    if len(pm) < 5:
        return None, None, None, None
    tp = (pm['high'] + pm['low'] + pm['close']) / 3
    cum_tpv = (tp * pm['volume']).cumsum()
    cum_vol = pm['volume'].cumsum()
    vwap = cum_tpv / cum_vol
    vwap_val = vwap.iloc[-1] if cum_vol.iloc[-1] > 0 else None
    close_929 = pm['close'].iloc[-1]

    # PM curvature: 2nd derivative of last ~5 closes
    closes = pm['close'].values
    if len(closes) >= 5:
        d1 = np.diff(closes[-5:])
        d2 = np.diff(d1)
        curvature = np.mean(d2)
    else:
        curvature = 0.0

    return vwap_val, close_929, curvature, pm

def build_days(df):
    """Build per-day feature dict for Entry A analysis."""
    days_data = []
    trading_dates = sorted(set(df.index.date))

    for dt in trading_dates:
        day_str = str(dt)
        day_bars = df.loc[day_str]

        # Get PM VWAP
        vwap_val, close_929, curvature, pm_bars = get_pm_vwap(day_bars)
        if vwap_val is None or close_929 is None:
            continue

        # VWAP direction
        if close_929 > vwap_val:
            direction = 'LONG'
        elif close_929 < vwap_val:
            direction = 'SHORT'
        else:
            continue

        vwap_distance = abs(close_929 - vwap_val)

        # RTH bars: 9:30:00 onwards
        rth = day_bars.between_time('09:30', '09:35')
        if len(rth) < 8:  # need at least bars 0-7 (2 min)
            continue

        bar0 = rth.iloc[0]  # 9:30:00-9:30:14
        open_930 = bar0['open']

        # Bar0 features
        b0_open = bar0['open']
        b0_close = bar0['close']
        b0_high = bar0['high']
        b0_low = bar0['low']
        b0_vol = bar0['volume']
        b0_range = b0_high - b0_low
        b0_body = abs(b0_close - b0_open)
        b0_wick_ratio = (b0_range - b0_body) / b0_range if b0_range > 0 else 0

        # First move in VWAP direction
        if direction == 'LONG':
            first_move = b0_close - b0_open
            going_right = first_move > 0
        else:
            first_move = b0_open - b0_close
            going_right = first_move > 0

        if not going_right:
            continue  # Only Entry A days

        # Bar1 features
        if len(rth) < 2:
            continue
        bar1 = rth.iloc[1]  # 9:30:15-9:30:29
        b1_close = bar1['close']

        if direction == 'LONG':
            bar1_continues = b1_close > b0_close
            bar1_reverses = b1_close < b0_open
            bar1_stalls = not bar1_continues and not bar1_reverses
            bar1_pulls_back = bar1['low'] < b0_close
        else:
            bar1_continues = b1_close < b0_close
            bar1_reverses = b1_close > b0_open
            bar1_stalls = not bar1_continues and not bar1_reverses
            bar1_pulls_back = bar1['high'] > b0_close

        # Pullback available: does price come back within $0.05 of open in first 30s RTH?
        first_30s = rth.iloc[0:2]  # bar0 + bar1
        if direction == 'LONG':
            pullback_available = any(first_30s['low'] <= open_930 + 0.05)
            # More precisely: after bar0, does bar1 or bar2 come back?
            pullback_bars = rth.iloc[1:3] if len(rth) >= 3 else rth.iloc[1:2]
            pullback_available = any(pullback_bars['low'] <= open_930 + 0.05)
        else:
            pullback_bars = rth.iloc[1:3] if len(rth) >= 3 else rth.iloc[1:2]
            pullback_available = any(pullback_bars['high'] >= open_930 - 0.05)

        # PnL at various points (entry at bar0 close = 9:30:15)
        entry_b0 = b0_close

        def get_pnl(entry, bar_idx, d):
            if bar_idx >= len(rth):
                return None
            p = rth.iloc[bar_idx]['close']
            return (p - entry) if d == 'LONG' else (entry - p)

        # PnL for entry at bar0 close
        pnl_1m = get_pnl(entry_b0, 3, direction)   # bar3 close = 9:30:45-ish -> actually 9:31:00
        pnl_90s = get_pnl(entry_b0, 5, direction)   # bar5 close = 9:31:15-ish -> 9:31:30
        pnl_2m = get_pnl(entry_b0, 7, direction)    # bar7 close = 9:31:45-ish -> 9:32:00

        # Actually let me be precise: bar0=9:30:00, bar1=9:30:15, bar2=9:30:30, bar3=9:30:45
        # bar4=9:31:00, bar5=9:31:15, bar6=9:31:30, bar7=9:31:45, bar8=9:32:00
        # Entry at bar0 close (end of 9:30:00-9:30:14 = 9:30:15)
        # PnL at 9:31:00 = bar4 close = index 4
        # PnL at 9:31:30 = bar6 close = index 6
        # PnL at 9:32:00 = bar8 close = index 8

        pnl_1m = get_pnl(entry_b0, 4, direction)
        pnl_90s = get_pnl(entry_b0, 6, direction)
        pnl_2m = get_pnl(entry_b0, 8, direction)

        # Entry at bar1 close
        entry_b1 = b1_close
        pnl_1m_b1 = get_pnl(entry_b1, 4, direction) if len(rth) > 4 else None
        pnl_2m_b1 = get_pnl(entry_b1, 8, direction) if len(rth) > 8 else None

        # Entry at bar2 close
        entry_b2 = rth.iloc[2]['close'] if len(rth) > 2 else None
        pnl_2m_b2 = get_pnl(entry_b2, 8, direction) if entry_b2 and len(rth) > 8 else None

        # Entry at bar3 close
        entry_b3 = rth.iloc[3]['close'] if len(rth) > 3 else None
        pnl_2m_b3 = get_pnl(entry_b3, 8, direction) if entry_b3 and len(rth) > 8 else None

        # Pullback entry: enter at open_930 if price returns within first 4 bars
        pullback_entry_price = None
        pullback_pnl_2m = None
        for i in range(1, min(4, len(rth))):
            b = rth.iloc[i]
            if direction == 'LONG' and b['low'] <= open_930 + 0.05:
                pullback_entry_price = open_930
                pullback_pnl_2m = get_pnl(open_930, 8, direction) if len(rth) > 8 else None
                break
            elif direction == 'SHORT' and b['high'] >= open_930 - 0.05:
                pullback_entry_price = open_930
                pullback_pnl_2m = get_pnl(open_930, 8, direction) if len(rth) > 8 else None
                break

        # MFE/MAE in first 2 minutes (bars 1-8)
        mfe = 0
        mae = 0
        for i in range(1, min(9, len(rth))):
            b = rth.iloc[i]
            if direction == 'LONG':
                mfe = max(mfe, b['high'] - entry_b0)
                mae = min(mae, b['low'] - entry_b0)
            else:
                mfe = max(mfe, entry_b0 - b['low'])
                mae = min(mae, entry_b0 - b['high'])

        days_data.append({
            'date': dt,
            'direction': direction,
            'first_move': first_move,
            'b0_range': b0_range,
            'b0_body': b0_body,
            'b0_wick_ratio': b0_wick_ratio,
            'b0_volume': b0_vol,
            'bar1_continues': bar1_continues,
            'bar1_stalls': bar1_stalls,
            'bar1_reverses': bar1_reverses,
            'bar1_pulls_back': bar1_pulls_back,
            'vwap_distance': vwap_distance,
            'pm_curvature': curvature,
            'pullback_available': pullback_available,
            'pnl_1m': pnl_1m,
            'pnl_90s': pnl_90s,
            'pnl_2m': pnl_2m,
            'pnl_1m_b1': pnl_1m_b1,
            'pnl_2m_b1': pnl_2m_b1,
            'pnl_2m_b2': pnl_2m_b2,
            'pnl_2m_b3': pnl_2m_b3,
            'pullback_entry_price': pullback_entry_price,
            'pullback_pnl_2m': pullback_pnl_2m,
            'entry_b0': entry_b0,
            'entry_b1': entry_b1,
            'open_930': open_930,
            'mfe': mfe,
            'mae': mae,
        })

    return pd.DataFrame(days_data)

def loop1_features(ddf):
    """Loop 1: What distinguishes Entry A winners from losers?"""
    out = []
    out.append("## Loop 1: Winner vs Loser Feature Analysis\n")

    valid = ddf.dropna(subset=['pnl_2m'])
    winners = valid[valid['pnl_2m'] > 0]
    losers = valid[valid['pnl_2m'] <= 0]

    out.append(f"Total Entry A days: {len(valid)}, Winners: {len(winners)} ({100*len(winners)/len(valid):.0f}%), Losers: {len(losers)}\n")

    features = ['first_move', 'b0_range', 'b0_body', 'b0_wick_ratio', 'b0_volume',
                'vwap_distance', 'pm_curvature']
    bool_features = ['bar1_continues', 'bar1_stalls', 'bar1_reverses', 'bar1_pulls_back', 'pullback_available']

    out.append("| Feature | Winners Mean | Losers Mean | Diff | p-value | Sig? |")
    out.append("|---------|-------------|-------------|------|---------|------|")

    for f in features:
        w = winners[f].dropna()
        l = losers[f].dropna()
        if len(w) < 3 or len(l) < 3:
            continue
        stat, p = stats.mannwhitneyu(w, l, alternative='two-sided')
        sig = "YES" if p < 0.05 else "no"
        out.append(f"| {f} | {w.mean():.4f} | {l.mean():.4f} | {w.mean()-l.mean():+.4f} | {p:.4f} | {sig} |")

    out.append("")
    out.append("| Boolean Feature | Winners % True | Losers % True | Diff | Chi2 p |")
    out.append("|----------------|----------------|---------------|------|--------|")

    for f in bool_features:
        w_pct = winners[f].mean() * 100
        l_pct = losers[f].mean() * 100
        # Chi-square
        ct = pd.crosstab(valid['pnl_2m'] > 0, valid[f])
        if ct.shape == (2, 2):
            chi2, p, _, _ = stats.chi2_contingency(ct)
        else:
            p = 1.0
        sig = "YES" if p < 0.05 else "no"
        out.append(f"| {f} | {w_pct:.0f}% | {l_pct:.0f}% | {w_pct-l_pct:+.0f}pp | {p:.4f} | {sig} |")

    out.append("")
    return "\n".join(out)

def loop2_timing(ddf):
    """Loop 2: Entry Timing."""
    out = []
    out.append("## Loop 2: Entry Timing\n")
    out.append("| Entry Point | N | Win% | Avg PnL | Total PnL |")
    out.append("|-------------|---|------|---------|-----------|")

    entries = [
        ("Bar0 close (9:30:15)", 'pnl_2m'),
        ("Bar1 close (9:30:30)", 'pnl_2m_b1'),
        ("Bar2 close (9:30:45)", 'pnl_2m_b2'),
        ("Bar3 close (9:31:00)", 'pnl_2m_b3'),
        ("Pullback to open", 'pullback_pnl_2m'),
    ]

    for label, col in entries:
        v = ddf[col].dropna()
        n = len(v)
        if n == 0:
            out.append(f"| {label} | 0 | — | — | — |")
            continue
        win = (v > 0).mean() * 100
        avg = v.mean()
        total = v.sum()
        out.append(f"| {label} | {n} | {win:.0f}% | ${avg:.2f} | ${total:.2f} |")

    out.append("")
    return "\n".join(out)

def loop3_first_move_size(ddf):
    """Loop 3: Filter by First Move Size."""
    out = []
    out.append("## Loop 3: First Move Size Buckets\n")
    out.append("| Bucket | N | Win% | Avg PnL | Total PnL |")
    out.append("|--------|---|------|---------|-----------|")

    valid = ddf.dropna(subset=['pnl_2m'])
    buckets = [
        ("Tiny (<$0.20)", valid[valid['first_move'] < 0.20]),
        ("Small ($0.20-$0.50)", valid[(valid['first_move'] >= 0.20) & (valid['first_move'] < 0.50)]),
        ("Medium ($0.50-$1.00)", valid[(valid['first_move'] >= 0.50) & (valid['first_move'] < 1.00)]),
        ("Large (>$1.00)", valid[valid['first_move'] >= 1.00]),
    ]

    for label, sub in buckets:
        n = len(sub)
        if n == 0:
            out.append(f"| {label} | 0 | — | — | — |")
            continue
        win = (sub['pnl_2m'] > 0).mean() * 100
        avg = sub['pnl_2m'].mean()
        total = sub['pnl_2m'].sum()
        out.append(f"| {label} | {n} | {win:.0f}% | ${avg:.2f} | ${total:.2f} |")

    out.append("")
    return "\n".join(out)

def loop4_bar1_confirmation(ddf):
    """Loop 4: Second Bar Confirmation."""
    out = []
    out.append("## Loop 4: Bar1 Confirmation (enter at bar1 close)\n")
    out.append("| Bar1 Action | N | Win% 1m | Avg PnL 1m | Win% 2m | Avg PnL 2m | Total 2m |")
    out.append("|-------------|---|---------|------------|---------|------------|----------|")

    valid = ddf.dropna(subset=['pnl_2m_b1', 'pnl_1m_b1'])

    groups = [
        ("Continues", valid[valid['bar1_continues']]),
        ("Stalls", valid[valid['bar1_stalls']]),
        ("Reverses", valid[valid['bar1_reverses']]),
    ]

    for label, sub in groups:
        n = len(sub)
        if n == 0:
            out.append(f"| {label} | 0 | — | — | — | — | — |")
            continue
        w1m = (sub['pnl_1m_b1'] > 0).mean() * 100
        a1m = sub['pnl_1m_b1'].mean()
        w2m = (sub['pnl_2m_b1'] > 0).mean() * 100
        a2m = sub['pnl_2m_b1'].mean()
        t2m = sub['pnl_2m_b1'].sum()
        out.append(f"| {label} | {n} | {w1m:.0f}% | ${a1m:.2f} | {w2m:.0f}% | ${a2m:.2f} | ${t2m:.2f} |")

    out.append("")
    return "\n".join(out)

def loop5_wick(ddf):
    """Loop 5: Wick/Exhaustion Filter."""
    out = []
    out.append("## Loop 5: Wick/Exhaustion Filter\n")
    out.append("| Wick Category | N | Win% | Avg PnL | Total PnL |")
    out.append("|---------------|---|------|---------|-----------|")

    valid = ddf.dropna(subset=['pnl_2m'])
    buckets = [
        ("Clean (<30%)", valid[valid['b0_wick_ratio'] < 0.30]),
        ("Moderate (30-50%)", valid[(valid['b0_wick_ratio'] >= 0.30) & (valid['b0_wick_ratio'] < 0.50)]),
        ("High (>50%)", valid[valid['b0_wick_ratio'] >= 0.50]),
    ]

    for label, sub in buckets:
        n = len(sub)
        if n == 0:
            out.append(f"| {label} | 0 | — | — | — |")
            continue
        win = (sub['pnl_2m'] > 0).mean() * 100
        avg = sub['pnl_2m'].mean()
        total = sub['pnl_2m'].sum()
        out.append(f"| {label} | {n} | {win:.0f}% | ${avg:.2f} | ${total:.2f} |")

    out.append("")
    return "\n".join(out)

def loop6_volume(ddf):
    """Loop 6: Volume Filter."""
    out = []
    out.append("## Loop 6: Volume Filter\n")

    valid = ddf.dropna(subset=['pnl_2m'])
    med_vol = valid['b0_volume'].median()
    out.append(f"Median bar0 volume: {med_vol:.0f}\n")

    out.append("| Volume | N | Win% | Avg PnL | Total PnL |")
    out.append("|--------|---|------|---------|-----------|")

    for label, sub in [("High (>median)", valid[valid['b0_volume'] > med_vol]),
                       ("Low (<=median)", valid[valid['b0_volume'] <= med_vol])]:
        n = len(sub)
        win = (sub['pnl_2m'] > 0).mean() * 100
        avg = sub['pnl_2m'].mean()
        total = sub['pnl_2m'].sum()
        out.append(f"| {label} | {n} | {win:.0f}% | ${avg:.2f} | ${total:.2f} |")

    # Also try quartiles
    out.append("\n**Volume quartiles:**\n")
    out.append("| Quartile | N | Win% | Avg PnL |")
    out.append("|----------|---|------|---------|")
    for q, label in [(0.25, 'Q1 (lowest)'), (0.50, 'Q2'), (0.75, 'Q3'), (1.0, 'Q4 (highest)')]:
        lo = valid['b0_volume'].quantile(q - 0.25)
        hi = valid['b0_volume'].quantile(q)
        sub = valid[(valid['b0_volume'] > lo) & (valid['b0_volume'] <= hi)] if q > 0.25 else valid[valid['b0_volume'] <= hi]
        n = len(sub)
        if n == 0: continue
        win = (sub['pnl_2m'] > 0).mean() * 100
        avg = sub['pnl_2m'].mean()
        out.append(f"| {label} | {n} | {win:.0f}% | ${avg:.2f} |")

    out.append("")
    return "\n".join(out)

def loop7_vwap_conviction(ddf):
    """Loop 7: VWAP Conviction."""
    out = []
    out.append("## Loop 7: VWAP Conviction\n")

    valid = ddf.dropna(subset=['pnl_2m'])
    med = valid['vwap_distance'].median()
    out.append(f"Median VWAP distance: ${med:.2f}\n")

    out.append("| VWAP Conviction | N | Win% | Avg PnL | Total PnL |")
    out.append("|-----------------|---|------|---------|-----------|")

    for label, sub in [("Strong (>median)", valid[valid['vwap_distance'] > med]),
                       ("Weak (<=median)", valid[valid['vwap_distance'] <= med])]:
        n = len(sub)
        win = (sub['pnl_2m'] > 0).mean() * 100
        avg = sub['pnl_2m'].mean()
        total = sub['pnl_2m'].sum()
        out.append(f"| {label} | {n} | {win:.0f}% | ${avg:.2f} | ${total:.2f} |")

    # Quartiles
    out.append("\n**VWAP distance quartiles:**\n")
    out.append("| Quartile | N | Win% | Avg PnL |")
    out.append("|----------|---|------|---------|")
    for q, label in [(0.25, 'Q1 (closest)'), (0.50, 'Q2'), (0.75, 'Q3'), (1.0, 'Q4 (farthest)')]:
        lo = valid['vwap_distance'].quantile(q - 0.25)
        hi = valid['vwap_distance'].quantile(q)
        sub = valid[(valid['vwap_distance'] > lo) & (valid['vwap_distance'] <= hi)] if q > 0.25 else valid[valid['vwap_distance'] <= hi]
        n = len(sub)
        if n == 0: continue
        win = (sub['pnl_2m'] > 0).mean() * 100
        avg = sub['pnl_2m'].mean()
        out.append(f"| {label} | {n} | {win:.0f}% | ${avg:.2f} |")

    out.append("")
    return "\n".join(out)

def loop8_curvature(ddf):
    """Loop 8: PM Curvature + Going Right."""
    out = []
    out.append("## Loop 8: PM Curvature\n")

    valid = ddf.dropna(subset=['pnl_2m'])

    # Curvature aligned with direction?
    # For LONG: positive curvature = accelerating up = good?
    # For SHORT: negative curvature = accelerating down = good?
    # Normalize: aligned_curvature = curvature * (1 if LONG else -1)
    valid = valid.copy()
    valid['aligned_curv'] = valid['pm_curvature'] * valid['direction'].map({'LONG': 1, 'SHORT': -1})

    med = valid['aligned_curv'].median()
    out.append(f"Aligned curvature: positive = PM accelerating into VWAP direction\n")

    out.append("| Curvature | N | Win% | Avg PnL | Total PnL |")
    out.append("|-----------|---|------|---------|-----------|")

    for label, sub in [("Accelerating (>0)", valid[valid['aligned_curv'] > 0]),
                       ("Decelerating (<=0)", valid[valid['aligned_curv'] <= 0])]:
        n = len(sub)
        if n == 0: continue
        win = (sub['pnl_2m'] > 0).mean() * 100
        avg = sub['pnl_2m'].mean()
        total = sub['pnl_2m'].sum()
        out.append(f"| {label} | {n} | {win:.0f}% | ${avg:.2f} | ${total:.2f} |")

    out.append("")
    return "\n".join(out)

def loop9_combos(ddf):
    """Loop 9: Combo Search."""
    out = []
    out.append("## Loop 9: Combo Search\n")

    valid = ddf.dropna(subset=['pnl_2m']).copy()
    valid['aligned_curv'] = valid['pm_curvature'] * valid['direction'].map({'LONG': 1, 'SHORT': -1})
    med_vwap = valid['vwap_distance'].median()
    med_vol = valid['b0_volume'].median()

    combos = []

    # Define filter functions
    filters = {
        'small_move': lambda d: d['first_move'] < 0.50,
        'tiny_move': lambda d: d['first_move'] < 0.20,
        'bar1_cont': lambda d: d['bar1_continues'],
        'bar1_no_rev': lambda d: ~d['bar1_reverses'],
        'clean_wick': lambda d: d['b0_wick_ratio'] < 0.30,
        'mod_wick': lambda d: d['b0_wick_ratio'] < 0.50,
        'strong_vwap': lambda d: d['vwap_distance'] > med_vwap,
        'accel_curv': lambda d: d['aligned_curv'] > 0,
        'high_vol': lambda d: d['b0_volume'] > med_vol,
        'low_vol': lambda d: d['b0_volume'] <= med_vol,
        'pullback_avail': lambda d: d['pullback_available'],
    }

    # Test singles
    out.append("### Single Filters\n")
    out.append("| Filter | N | Win% | Avg PnL | Total PnL |")
    out.append("|--------|---|------|---------|-----------|")

    single_results = {}
    for name, f in filters.items():
        sub = valid[f(valid)]
        n = len(sub)
        if n < 5: continue
        win = (sub['pnl_2m'] > 0).mean() * 100
        avg = sub['pnl_2m'].mean()
        total = sub['pnl_2m'].sum()
        out.append(f"| {name} | {n} | {win:.0f}% | ${avg:.2f} | ${total:.2f} |")
        single_results[name] = avg

    # Test top combos (2-way)
    out.append("\n### Best 2-Way Combos\n")
    out.append("| Combo | N | Win% | Avg PnL | Total PnL |")
    out.append("|-------|---|------|---------|-----------|")

    combo_results = []
    filter_names = list(filters.keys())
    for i in range(len(filter_names)):
        for j in range(i+1, len(filter_names)):
            n1, n2 = filter_names[i], filter_names[j]
            mask = filters[n1](valid) & filters[n2](valid)
            sub = valid[mask]
            n = len(sub)
            if n < 5: continue
            win = (sub['pnl_2m'] > 0).mean() * 100
            avg = sub['pnl_2m'].mean()
            total = sub['pnl_2m'].sum()
            combo_results.append((f"{n1} + {n2}", n, win, avg, total))

    combo_results.sort(key=lambda x: x[3], reverse=True)
    for label, n, win, avg, total in combo_results[:15]:
        out.append(f"| {label} | {n} | {win:.0f}% | ${avg:.2f} | ${total:.2f} |")

    # Test top 3-way combos
    out.append("\n### Best 3-Way Combos\n")
    out.append("| Combo | N | Win% | Avg PnL | Total PnL |")
    out.append("|-------|---|------|---------|-----------|")

    combo3_results = []
    for i in range(len(filter_names)):
        for j in range(i+1, len(filter_names)):
            for k in range(j+1, len(filter_names)):
                n1, n2, n3 = filter_names[i], filter_names[j], filter_names[k]
                mask = filters[n1](valid) & filters[n2](valid) & filters[n3](valid)
                sub = valid[mask]
                n = len(sub)
                if n < 5: continue
                win = (sub['pnl_2m'] > 0).mean() * 100
                avg = sub['pnl_2m'].mean()
                total = sub['pnl_2m'].sum()
                combo3_results.append((f"{n1} + {n2} + {n3}", n, win, avg, total))

    combo3_results.sort(key=lambda x: x[3], reverse=True)
    for label, n, win, avg, total in combo3_results[:10]:
        out.append(f"| {label} | {n} | {win:.0f}% | ${avg:.2f} | ${total:.2f} |")

    out.append("")
    return "\n".join(out)

def loop10_skip_vs_filter(ddf, all_df, df):
    """Loop 10: Skip Entry A entirely?"""
    out = []
    out.append("## Loop 10: Skip Entry A Entirely?\n")

    valid_a = ddf.dropna(subset=['pnl_2m'])

    # Build Entry B days (going wrong)
    trading_dates = sorted(set(df.index.date))
    entry_b_pnls = []

    for dt in trading_dates:
        day_str = str(dt)
        day_bars = df.loc[day_str]

        vwap_val, close_929, curvature, pm_bars = get_pm_vwap(day_bars)
        if vwap_val is None or close_929 is None:
            continue

        if close_929 > vwap_val:
            direction = 'LONG'
        elif close_929 < vwap_val:
            direction = 'SHORT'
        else:
            continue

        rth = day_bars.between_time('09:30', '09:35')
        if len(rth) < 9:
            continue

        bar0 = rth.iloc[0]
        if direction == 'LONG':
            first_move = bar0['close'] - bar0['open']
            going_right = first_move > 0
        else:
            first_move = bar0['open'] - bar0['close']
            going_right = first_move > 0

        if going_right:
            continue  # Skip Entry A days, only Entry B

        # Entry B: bounce. Enter at bar0 close (going wrong), direction is OPPOSITE of VWAP
        # Actually Entry B = going wrong, then bounces. Let's measure PnL in VWAP direction
        # from bar1 close (wait for bounce confirmation)
        entry = rth.iloc[1]['close']
        exit_price = rth.iloc[8]['close'] if len(rth) > 8 else rth.iloc[-1]['close']
        if direction == 'LONG':
            pnl = exit_price - entry
        else:
            pnl = entry - exit_price
        entry_b_pnls.append(pnl)

    out.append("| Approach | N | Win% | Avg PnL | Total PnL |")
    out.append("|----------|---|------|---------|-----------|")

    # A) Entry A unfiltered
    a_pnl = valid_a['pnl_2m']
    out.append(f"| Entry A unfiltered | {len(a_pnl)} | {(a_pnl>0).mean()*100:.0f}% | ${a_pnl.mean():.2f} | ${a_pnl.sum():.2f} |")

    # B) Entry B only
    b_pnl = pd.Series(entry_b_pnls)
    if len(b_pnl) > 0:
        out.append(f"| Entry B only (going wrong) | {len(b_pnl)} | {(b_pnl>0).mean()*100:.0f}% | ${b_pnl.mean():.2f} | ${b_pnl.sum():.2f} |")

    # Best filtered A (use bar1_continues as proxy for best filter from loop 9)
    best_a = valid_a[valid_a['bar1_continues']]['pnl_2m']
    if len(best_a) > 0:
        out.append(f"| Entry A + bar1 continues | {len(best_a)} | {(best_a>0).mean()*100:.0f}% | ${best_a.mean():.2f} | ${best_a.sum():.2f} |")

    # C) On Entry A days, wait for pullback
    pb = valid_a.dropna(subset=['pullback_pnl_2m'])['pullback_pnl_2m']
    if len(pb) > 0:
        out.append(f"| Entry A -> pullback entry | {len(pb)} | {(pb>0).mean()*100:.0f}% | ${pb.mean():.2f} | ${pb.sum():.2f} |")

    # Combined system
    out.append("\n**Combined system (best A approach + Entry B):**\n")
    if len(best_a) > 0 and len(b_pnl) > 0:
        combined = pd.concat([best_a, b_pnl], ignore_index=True)
        out.append(f"| Combined | {len(combined)} | {(combined>0).mean()*100:.0f}% | ${combined.mean():.2f} | ${combined.sum():.2f} |")

    out.append("")
    return "\n".join(out)


def main():
    df = load()
    print("Building Entry A days...")
    ddf = build_days(df)
    print(f"Entry A days: {len(ddf)}")

    if len(ddf) == 0:
        print("ERROR: No Entry A days found!")
        return

    # Summary stats
    valid = ddf.dropna(subset=['pnl_2m'])
    print(f"  With valid 2m PnL: {len(valid)}")
    print(f"  Win rate: {(valid['pnl_2m'] > 0).mean()*100:.1f}%")
    print(f"  Avg PnL: ${valid['pnl_2m'].mean():.2f}")
    print(f"  Total PnL: ${valid['pnl_2m'].sum():.2f}")
    print()

    sections = []
    sections.append("# TSLA Open Scalper — Entry A Optimization")
    sections.append(f"*Generated: 2026-03-20 | Data: {len(ddf)} Entry A days from 15sec bars*\n")
    sections.append(f"**Baseline:** {len(valid)} days, {(valid['pnl_2m']>0).mean()*100:.0f}% win, ${valid['pnl_2m'].mean():.2f} avg, ${valid['pnl_2m'].sum():.2f} total (2m hold)\n")
    sections.append("---\n")

    print("Loop 1: Feature analysis...")
    sections.append(loop1_features(ddf))

    print("Loop 2: Entry timing...")
    sections.append(loop2_timing(ddf))

    print("Loop 3: First move size...")
    sections.append(loop3_first_move_size(ddf))

    print("Loop 4: Bar1 confirmation...")
    sections.append(loop4_bar1_confirmation(ddf))

    print("Loop 5: Wick filter...")
    sections.append(loop5_wick(ddf))

    print("Loop 6: Volume filter...")
    sections.append(loop6_volume(ddf))

    print("Loop 7: VWAP conviction...")
    sections.append(loop7_vwap_conviction(ddf))

    print("Loop 8: PM curvature...")
    sections.append(loop8_curvature(ddf))

    print("Loop 9: Combo search...")
    sections.append(loop9_combos(ddf))

    print("Loop 10: Skip vs filter...")
    sections.append(loop10_skip_vs_filter(ddf, ddf, df))

    # Write conclusion
    sections.append("---\n")
    sections.append("## Conclusion\n")
    sections.append("*See combo results above for the single best approach.*")

    report = "\n".join(sections)
    print(report)

    with open(OUT, 'w') as f:
        f.write(report)
    print(f"\nWritten to: {OUT}")

if __name__ == '__main__':
    main()
