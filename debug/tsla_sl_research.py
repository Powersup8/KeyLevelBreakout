"""
TSLA Open Scalp — Stop Loss Optimization at 15s Resolution
Test SL distances from $0.50 to $5.00 and compare fixed vs dynamic (ORB-based) SL.
"""

import pandas as pd
import numpy as np
from pathlib import Path

CACHE = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache')

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
df15 = load('bars_highres/15sec/tsla_15_secs_ib.parquet')
df1m = load('bars/tsla_1_min_ib.parquet')
print(f"15s: {df15.shape}, 1m: {df1m.shape}")

days_15s = set(df15.index.normalize().unique())
market_days = sorted(df1m.between_time('09:30', '16:00').index.normalize().unique())

# ─────────────────────────────────────────────
# BUILD DAILY DATA WITH 15s INTRADAY PATHS
# ─────────────────────────────────────────────

rows = []
skip_no15s = 0
skip_mkt = 0
skip_hold = 0
for d in market_days:
    mkt_1m = df1m[df1m.index.normalize() == d].between_time('09:30', '16:00')
    if len(mkt_1m) < 10:
        skip_mkt += 1
        continue

    open_930 = mkt_1m.iloc[0]['open']
    eod_close = mkt_1m.iloc[-1]['close']

    # 5m rule: close of 9:34 bar (5 bars of RTH)
    bar_934 = mkt_1m.between_time('09:34', '09:34')
    close_934 = bar_934.iloc[0]['close'] if len(bar_934) > 0 else np.nan
    is_hold = close_934 > open_930 if not np.isnan(close_934) else None

    if not is_hold:
        skip_hold += 1
        continue  # only analyze HOLD days

    # ORB: high/low of 9:30-9:34 (5 bars)
    orb_bars = mkt_1m.between_time('09:30', '09:34')
    orb_high = orb_bars['high'].max() if len(orb_bars) > 0 else np.nan
    orb_low = orb_bars['low'].min() if len(orb_bars) > 0 else np.nan
    orb_width = orb_high - orb_low if not np.isnan(orb_high) else np.nan

    # First bar (9:30) low
    bar1_low = mkt_1m.iloc[0]['low']

    # ── 1m intraday path from entry (15s only covers premarket) ──
    lows_1m = mkt_1m['low'].values
    times_1m = mkt_1m.index

    # Max drawdown from entry (using 1m bar lows)
    max_dd = (open_930 - lows_1m).max()
    max_dd_idx = np.argmax(open_930 - lows_1m)
    max_dd_time = times_1m[max_dd_idx]

    # 10-minute window: 9:30-9:39 (10 bars)
    w10m = mkt_1m.between_time('09:30', '09:39')
    if len(w10m) > 0:
        max_dd_10m = (open_930 - w10m['low'].values).max()
        close_940 = w10m.iloc[-1]['close']
        pnl_10m = close_940 - open_930
    else:
        max_dd_10m = np.nan
        pnl_10m = np.nan

    # 25-minute window (ORB breakout zone): 9:30-9:55
    w25m = mkt_1m.between_time('09:30', '09:55')
    if len(w25m) > 0:
        max_dd_25m = (open_930 - w25m['low'].values).max()
    else:
        max_dd_25m = np.nan

    # PM volume (9:25-9:29) from 15s data if available
    if d in days_15s:
        pm15 = df15[df15.index.normalize() == d].between_time('09:25:00', '09:29:59')
        pm_vol = pm15['volume'].sum() if len(pm15) > 0 else np.nan
    else:
        pm_vol = np.nan

    rows.append({
        'date': d,
        'open_930': open_930,
        'eod_close': eod_close,
        'day_pnl': eod_close - open_930,
        'orb_high': orb_high,
        'orb_low': orb_low,
        'orb_width': orb_width,
        'bar1_low': bar1_low,
        'max_dd_full': max_dd,
        'max_dd_10m': max_dd_10m,
        'max_dd_25m': max_dd_25m,
        'max_dd_time': max_dd_time,
        'pnl_10m': pnl_10m,
        'pm_vol': pm_vol,
    })

print(f"Skipped: no_mkt={skip_mkt}, not_hold={skip_hold}, rows={len(rows)}")
df = pd.DataFrame(rows).set_index('date')
print(f"HOLD days: {len(df)}")

# ─────────────────────────────────────────────
# ANALYSIS 1: Drawdown Distribution
# ─────────────────────────────────────────────

print("\n" + "="*70)
print("MAX DRAWDOWN DISTRIBUTION ON HOLD DAYS (from 9:30 open)")
print("="*70)

for window, col in [('Full day', 'max_dd_full'), ('First 10m', 'max_dd_10m'), ('First 25m', 'max_dd_25m')]:
    vals = df[col].dropna()
    print(f"\n{window} (n={len(vals)}):")
    for pct in [25, 50, 75, 90, 95]:
        print(f"  P{pct}: ${vals.quantile(pct/100):.2f}")
    print(f"  Mean: ${vals.mean():.2f}, Max: ${vals.max():.2f}")

# ─────────────────────────────────────────────
# ANALYSIS 2: Fixed SL Sweep
# ─────────────────────────────────────────────

print("\n" + "="*70)
print("FIXED SL SWEEP: outcomes by SL distance (HOLD days, 10m exit)")
print("="*70)
print(f"{'SL $':<8} {'Survived':>9} {'Stopped':>8} {'Win%':>6} {'Avg PnL':>9} {'Stopped Recovered':>18}")
print("-"*62)

for sl in np.arange(0.50, 5.25, 0.25):
    stopped = df['max_dd_10m'] > sl
    survived = ~stopped
    n_surv = survived.sum()
    n_stop = stopped.sum()

    if n_surv > 0:
        # Survived: use 10m P&L
        surv_pnl = df.loc[survived, 'pnl_10m']
        win_pct = (surv_pnl > 0).mean() * 100
        avg_pnl = surv_pnl.mean()
    else:
        win_pct = 0
        avg_pnl = 0

    # Of stopped-out trades: how many would have been profitable at 10m if held?
    if n_stop > 0:
        would_have_won = (df.loc[stopped, 'pnl_10m'] > 0).sum()
        recovered_pct = would_have_won / n_stop * 100
    else:
        recovered_pct = 0

    # Expected value: survived * avg_pnl + stopped * (-sl)
    ev = (n_surv * avg_pnl + n_stop * (-sl)) / len(df) if len(df) > 0 else 0

    print(f"${sl:<7.2f} {n_surv:>8}/{len(df):<3} {n_stop:>7} {win_pct:>5.0f}% {avg_pnl:>8.2f} {recovered_pct:>17.0f}%")

# Same but EOD exit
print(f"\n{'SL $':<8} {'Survived':>9} {'Stopped':>8} {'EOD Win%':>9} {'EOD Avg':>9} {'EV':>8}")
print("-"*55)

for sl in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
    stopped_25m = df['max_dd_25m'] > sl
    survived = ~stopped_25m
    n_surv = survived.sum()
    n_stop = stopped_25m.sum()

    if n_surv > 0:
        surv_pnl = df.loc[survived, 'day_pnl']
        win_pct = (surv_pnl > 0).mean() * 100
        avg_pnl = surv_pnl.mean()
    else:
        win_pct = 0
        avg_pnl = 0

    ev = (n_surv * avg_pnl + n_stop * (-sl)) / len(df)
    print(f"${sl:<7.2f} {n_surv:>8}/{len(df):<3} {n_stop:>7} {win_pct:>8.0f}% {avg_pnl:>8.2f} {ev:>8.2f}")

# ─────────────────────────────────────────────
# ANALYSIS 3: ORB-Based Dynamic SL
# ─────────────────────────────────────────────

print("\n" + "="*70)
print("ORB-BASED DYNAMIC SL: orb_low vs orb_low - buffer")
print("="*70)

print(f"\nORB width distribution (HOLD days):")
ow = df['orb_width'].dropna()
for pct in [25, 50, 75, 90]:
    print(f"  P{pct}: ${ow.quantile(pct/100):.2f}")

for buffer_label, sl_col in [
    ('orb_low exact', 'orb_low'),
    ('bar1_low', 'bar1_low'),
]:
    sl_distances = df['open_930'] - df[sl_col]
    stopped = df['max_dd_25m'] > sl_distances
    survived = ~stopped
    n_surv = survived.sum()
    n_stop = stopped.sum()

    if n_surv > 0:
        surv_pnl = df.loc[survived, 'day_pnl']
        win_pct = (surv_pnl > 0).mean() * 100
        avg_pnl = surv_pnl.mean()
    else:
        win_pct = 0
        avg_pnl = 0

    avg_sl_dist = sl_distances.mean()
    med_sl_dist = sl_distances.median()
    # EV: survived * avg_pnl + stopped * (-median_sl_distance)
    ev = (n_surv * avg_pnl + n_stop * (-med_sl_dist)) / len(df)
    print(f"\n{buffer_label}:")
    print(f"  SL distance: mean=${avg_sl_dist:.2f}, median=${med_sl_dist:.2f}")
    print(f"  Survived: {n_surv}/{len(df)}, Stopped: {n_stop}")
    print(f"  Win%: {win_pct:.0f}%, Avg PnL: ${avg_pnl:.2f}, EV: ${ev:.2f}")

# ORB low with buffers
for buf in [0.25, 0.50, 0.75, 1.00]:
    sl_level = df['orb_low'] - buf
    sl_distances = df['open_930'] - sl_level
    stopped = df['max_dd_25m'] > sl_distances
    survived = ~stopped
    n_surv = survived.sum()
    n_stop = stopped.sum()

    if n_surv > 0:
        surv_pnl = df.loc[survived, 'day_pnl']
        win_pct = (surv_pnl > 0).mean() * 100
        avg_pnl = surv_pnl.mean()
    else:
        win_pct = 0
        avg_pnl = 0

    avg_sl_dist = sl_distances.mean()
    med_sl_dist = sl_distances.median()
    ev = (n_surv * avg_pnl + n_stop * (-med_sl_dist)) / len(df)
    print(f"\norb_low - ${buf:.2f}:")
    print(f"  SL distance: mean=${avg_sl_dist:.2f}, median=${med_sl_dist:.2f}")
    print(f"  Survived: {n_surv}/{len(df)}, Stopped: {n_stop}")
    print(f"  Win%: {win_pct:.0f}%, Avg PnL: ${avg_pnl:.2f}, EV: ${ev:.2f}")

# ─────────────────────────────────────────────
# ANALYSIS 4: When does the max drawdown happen?
# ─────────────────────────────────────────────

print("\n" + "="*70)
print("TIMING: When does max drawdown happen on HOLD days?")
print("="*70)

df['dd_hour'] = df['max_dd_time'].apply(lambda x: x.hour)
df['dd_minute'] = df['max_dd_time'].apply(lambda x: x.minute)
df['dd_hm'] = df['dd_hour'] * 100 + df['dd_minute']

# Buckets
buckets = [
    ('9:30-9:34 (ORB)', 930, 934),
    ('9:35-9:39', 935, 939),
    ('9:40-9:44', 940, 944),
    ('9:45-9:55', 945, 955),
    ('9:56-10:30', 956, 1030),
    ('After 10:30', 1031, 1600),
]

for label, lo, hi in buckets:
    mask = (df['dd_hm'] >= lo) & (df['dd_hm'] <= hi)
    n = mask.sum()
    pct = n / len(df) * 100
    avg_dd = df.loc[mask, 'max_dd_full'].mean() if n > 0 else 0
    print(f"  {label:<22} {n:>4} days ({pct:>4.0f}%)  avg dd=${avg_dd:.2f}")

# ─────────────────────────────────────────────
# ANALYSIS 5: Best SL Strategy Comparison
# ─────────────────────────────────────────────

print("\n" + "="*70)
print("HEAD-TO-HEAD: Fixed $2 vs ORB Low vs ORB Low-$0.50 (25m window, EOD P&L)")
print("="*70)

strategies = {
    'Fixed $2.00': df['open_930'] - 2.00,
    'Fixed $1.50': df['open_930'] - 1.50,
    'Fixed $2.50': df['open_930'] - 2.50,
    'ORB Low': df['orb_low'],
    'ORB Low - $0.25': df['orb_low'] - 0.25,
    'ORB Low - $0.50': df['orb_low'] - 0.50,
    'Bar1 Low': df['bar1_low'],
    'Bar1 Low - $0.25': df['bar1_low'] - 0.25,
}

print(f"{'Strategy':<22} {'SL dist':>8} {'Survived':>9} {'Stop':>5} {'Win%':>6} {'Avg PnL':>9} {'EV':>8}")
print("-"*70)

for name, sl_levels in strategies.items():
    sl_dist = df['open_930'] - sl_levels
    stopped = df['max_dd_25m'] > sl_dist
    survived = ~stopped
    n_surv = survived.sum()
    n_stop = stopped.sum()
    med_dist = sl_dist.median()

    if n_surv > 0:
        surv_pnl = df.loc[survived, 'day_pnl']
        win_pct = (surv_pnl > 0).mean() * 100
        avg_pnl = surv_pnl.mean()
    else:
        win_pct = 0
        avg_pnl = 0

    ev = (n_surv * avg_pnl + n_stop * (-med_dist)) / len(df)
    print(f"{name:<22} ${med_dist:>6.2f} {n_surv:>8}/{len(df):<3} {n_stop:>4} {win_pct:>5.0f}% {avg_pnl:>8.2f} {ev:>8.2f}")

print("\nDone.")
