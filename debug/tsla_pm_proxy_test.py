"""
Test: Can 1m PM bars approximate 15s path efficiency?
Compare proxy metrics (computable on 1m chart) vs true 15s path efficiency.
"""

import pandas as pd
import numpy as np
from pathlib import Path

CACHE = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache')

def load(tf, fname):
    df = pd.read_parquet(CACHE / fname)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC').tz_convert('America/New_York')
    else:
        df.index = df.index.tz_convert('America/New_York')
    return df

print("Loading data...")
df15 = load('15s', 'bars_highres/15sec/tsla_15_secs_ib.parquet')
df1m = load('1m', 'bars/tsla_1_min_ib.parquet')

days_15s = set(df15.index.normalize().unique())
market_days = sorted(df1m.between_time('09:30', '16:00').index.normalize().unique())

rows = []
for d in market_days:
    if d not in days_15s:
        continue

    # ── 15s ground truth ──
    pm15 = df15[df15.index.normalize() == d].between_time('09:20:00', '09:29:59')
    if len(pm15) < 20:
        continue

    prices_15s = pm15['close'].values
    net_move = prices_15s[-1] - prices_15s[0]
    diffs_15s = np.diff(prices_15s)
    path_len_15s = np.sum(np.abs(diffs_15s))
    eff_15s = abs(net_move) / path_len_15s if path_len_15s > 0 else 0

    # Monotonicity at 15s
    if net_move > 0:
        mono_15s = (diffs_15s > 0).sum() / len(diffs_15s)
    elif net_move < 0:
        mono_15s = (diffs_15s < 0).sum() / len(diffs_15s)
    else:
        mono_15s = 0.5

    # ── 1m proxies ──
    pm1m = df1m[df1m.index.normalize() == d].between_time('09:20', '09:29')
    if len(pm1m) < 5:
        continue

    closes_1m = pm1m['close'].values
    highs_1m = pm1m['high'].values
    lows_1m = pm1m['low'].values
    opens_1m = pm1m['open'].values

    net_move_1m = closes_1m[-1] - opens_1m[0]

    # Proxy 1: Close-to-close path efficiency (same formula, fewer bars)
    diffs_1m = np.diff(closes_1m)
    path_len_1m_close = np.sum(np.abs(diffs_1m))
    proxy_eff_close = abs(net_move_1m) / path_len_1m_close if path_len_1m_close > 0 else 0

    # Proxy 2: Use OHLC — total intra-bar range as path length
    # Each bar traveled at least (high - low). Sum all bar ranges.
    bar_ranges = highs_1m - lows_1m
    path_len_1m_ohlc = np.sum(bar_ranges)
    proxy_eff_ohlc = abs(net_move_1m) / path_len_1m_ohlc if path_len_1m_ohlc > 0 else 0

    # Proxy 3: Net move / PM range (simplest possible)
    pm_range = highs_1m.max() - lows_1m.min()
    proxy_eff_range = abs(net_move_1m) / pm_range if pm_range > 0 else 0

    # Proxy 4: Monotonicity at 1m (% bars moving with trend)
    if net_move_1m > 0:
        mono_1m = (diffs_1m > 0).sum() / len(diffs_1m) if len(diffs_1m) > 0 else 0.5
    elif net_move_1m < 0:
        mono_1m = (diffs_1m < 0).sum() / len(diffs_1m) if len(diffs_1m) > 0 else 0.5
    else:
        mono_1m = 0.5

    # Proxy 5: Bar body consistency — how many bars have body in same direction as net?
    bodies = closes_1m - opens_1m
    if net_move_1m > 0:
        body_consistency = (bodies > 0).sum() / len(bodies)
    elif net_move_1m < 0:
        body_consistency = (bodies < 0).sum() / len(bodies)
    else:
        body_consistency = 0.5

    # Proxy 6: Average wick ratio — small wicks = cleaner bars
    body_sizes = np.abs(bodies)
    wick_sizes = bar_ranges - body_sizes
    avg_wick_ratio = np.mean(wick_sizes / bar_ranges) if np.all(bar_ranges > 0) else 0.5

    # ── Outcome ──
    mkt = df1m[df1m.index.normalize() == d].between_time('09:30', '16:00')
    if len(mkt) < 10:
        continue
    open_930 = mkt.iloc[0]['open']
    eod_close = mkt.iloc[-1]['close']
    bar_935 = mkt.between_time('09:35', '09:35')
    close_935 = bar_935.iloc[0]['close'] if len(bar_935) > 0 else np.nan
    hold = close_935 > open_930 if not np.isnan(close_935) else None

    rows.append({
        'date': d,
        'eff_15s': eff_15s,
        'mono_15s': mono_15s,
        'proxy_eff_close': proxy_eff_close,
        'proxy_eff_ohlc': proxy_eff_ohlc,
        'proxy_eff_range': proxy_eff_range,
        'proxy_mono_1m': mono_1m,
        'proxy_body_consistency': body_consistency,
        'proxy_wick_ratio': avg_wick_ratio,
        'hold': hold,
        'day_pnl': eod_close - open_930,
    })

df = pd.DataFrame(rows).set_index('date')
hold_df = df[df['hold'] == True].copy()
print(f"Days: {len(df)}, HOLD: {len(hold_df)}")

# ─────────────────────────────────────────────
# CORRELATION ANALYSIS
# ─────────────────────────────────────────────

proxies = [
    ('proxy_eff_close', 'Close-to-close efficiency'),
    ('proxy_eff_ohlc', 'OHLC range efficiency'),
    ('proxy_eff_range', 'Net move / PM range'),
    ('proxy_mono_1m', 'Monotonicity (1m closes)'),
    ('proxy_body_consistency', 'Body direction consistency'),
    ('proxy_wick_ratio', 'Avg wick ratio'),
]

print("\n" + "="*70)
print("CORRELATION WITH 15s PATH EFFICIENCY (ground truth)")
print("="*70)
print(f"{'Proxy':<32} {'Corr':>8} {'Rank Corr':>10}")
print("-"*52)
for col, name in proxies:
    corr = df[col].corr(df['eff_15s'])
    rank_corr = df[col].rank().corr(df['eff_15s'].rank())
    print(f"{name:<32} {corr:>8.3f} {rank_corr:>10.3f}")

# ─────────────────────────────────────────────
# QUARTILE MATCH: does the proxy put days in the same buckets?
# ─────────────────────────────────────────────

print("\n" + "="*70)
print("QUARTILE AGREEMENT: what % of days land in same quartile?")
print("="*70)

eff_q = pd.qcut(df['eff_15s'], 4, labels=[1,2,3,4])
for col, name in proxies:
    try:
        proxy_q = pd.qcut(df[col], 4, labels=[1,2,3,4], duplicates='drop')
        match = (eff_q == proxy_q).mean() * 100
        # Also check: does it at least get the "sweet spot" (Q2) right?
        is_q2_true = (eff_q == 2)
        is_q2_proxy = (proxy_q == 2)
        precision = (is_q2_true & is_q2_proxy).sum() / is_q2_proxy.sum() * 100 if is_q2_proxy.sum() > 0 else 0
        recall = (is_q2_true & is_q2_proxy).sum() / is_q2_true.sum() * 100 if is_q2_true.sum() > 0 else 0
        print(f"{name:<32} Match: {match:.0f}%  |  Q2 precision: {precision:.0f}%, recall: {recall:.0f}%")
    except Exception as e:
        print(f"{name:<32} Error: {e}")

# ─────────────────────────────────────────────
# THE REAL TEST: does the proxy reproduce the 81% win finding?
# ─────────────────────────────────────────────

print("\n" + "="*70)
print("HOLD DAY OUTCOMES BY PROXY QUARTILE (vs 15s ground truth)")
print("="*70)

print("\n--- Ground truth: 15s path efficiency ---")
for q_label, lo, hi in [('Q1 (choppy)', 0, 0.25), ('Q2 (sweet spot)', 0.25, 0.5),
                          ('Q3 (clean)', 0.5, 0.75), ('Q4 (straight)', 0.75, 1.0)]:
    q_vals = hold_df['eff_15s'].quantile([lo, hi])
    mask = (hold_df['eff_15s'] >= hold_df['eff_15s'].quantile(lo)) & \
           (hold_df['eff_15s'] < hold_df['eff_15s'].quantile(hi))
    if hi >= 1.0:
        mask = mask | (hold_df['eff_15s'] == hold_df['eff_15s'].max())
    subset = hold_df[mask]
    if len(subset) == 0:
        continue
    win = (subset['day_pnl'] > 0).mean() * 100
    avg = subset['day_pnl'].mean()
    worst = (subset['day_pnl'] < -5).mean() * 100
    print(f"  {q_label:<20} n={len(subset):>3}  Win={win:.0f}%  Avg=${avg:.2f}  Worst={worst:.0f}%")

for col, name in proxies:
    print(f"\n--- {name} ---")
    try:
        quartiles = pd.qcut(hold_df[col], 4, labels=['Q1','Q2','Q3','Q4'], duplicates='drop')
    except:
        print("  Could not create quartiles (too few unique values)")
        continue
    for q in ['Q1','Q2','Q3','Q4']:
        subset = hold_df[quartiles == q]
        if len(subset) == 0:
            continue
        win = (subset['day_pnl'] > 0).mean() * 100
        avg = subset['day_pnl'].mean()
        worst = (subset['day_pnl'] < -5).mean() * 100
        print(f"  {q:<20} n={len(subset):>3}  Win={win:.0f}%  Avg=${avg:.2f}  Worst={worst:.0f}%")

print("\nDone.")
