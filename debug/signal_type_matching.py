#!/usr/bin/env python3
"""
Signal Type Matching Analysis
=============================
Which signals fire at wrong levels, and what's it costing us?

Analyzes the KLB enriched-signals.csv to understand:
A. Signal Type x Level Type matrix (count, win%, MFE, MAE, net ATR)
B. Direction x Level analysis (bull/bear at each level)
C. Combo/confluence analysis (single vs multi-level)
D. Level behavior over time (barrier vs magnet shift)
E. Recommendations for signal type reassignment + suppression

Uses:
  - enriched-signals.csv (1841 signals with MFE/MAE)
  - BATS TV 1m candle CSVs (for level behavior classification)
  - IB 5m parquet (for level behavior at touch points)
"""

import pandas as pd
import numpy as np
import os
import glob
from collections import defaultdict
from datetime import datetime, timedelta

# ── Paths ────────────────────────────────────────────────────────────────
BASE = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView"
DEBUG = os.path.join(BASE, "debug")
ENRICHED = os.path.join(DEBUG, "enriched-signals.csv")
BIG_MOVES = os.path.join(DEBUG, "big-moves.csv")
IB_CACHE = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars"
TV_CANDLE_DIR = DEBUG

# 13 symbols
SYMBOLS = ['SPY','AAPL','AMD','AMZN','GLD','GOOGL','META','MSFT','NVDA','QQQ','SLV','TSLA','TSM']

# ── Level classification ─────────────────────────────────────────────────
# Individual level names that can appear in multi-level combos
BARRIER_LEVELS = {'Yest H', 'Yest L', 'PM H', 'PM L', 'ORB H', 'ORB L', 'Week H', 'Week L'}
MAGNET_LEVELS  = {'PD Mid', 'PD Last Hr L', 'PD Last Hr H', 'VWAP', 'VWAP LB', 'VWAP UB'}

# Mapping: individual level -> expected signal type
EXPECTED_SIGNAL = {
    'Yest H': 'BRK', 'Yest L': 'BRK', 'PM H': 'BRK', 'PM L': 'BRK',
    'ORB H': 'BRK', 'ORB L': 'BRK', 'Week H': 'BRK', 'Week L': 'BRK',
    'PD Mid': 'REV', 'PD Last Hr L': 'REV', 'PD Last Hr H': 'REV',
    'VWAP': 'REV', 'VWAP LB': 'REV', 'VWAP UB': 'REV',
}


def load_enriched():
    """Load enriched signals and parse."""
    df = pd.read_csv(ENRICHED)
    # Parse time into minutes since midnight for bucketing
    def time_to_minutes(t):
        parts = t.split(':')
        return int(parts[0]) * 60 + int(parts[1])
    df['minutes'] = df['time'].apply(time_to_minutes)
    df['pnl'] = df['mfe'] + df['mae']
    df['winner'] = (df['mfe'] >= 0.20) & (df['mfe'] / df['mae'].abs().clip(lower=0.001) > 1.5)
    df['loser'] = (df['mae'] <= -0.20) & (df['mfe'] / df['mae'].abs().clip(lower=0.001) < 0.8)

    # Parse individual levels from combo strings
    df['level_list'] = df['levels'].apply(lambda x: [l.strip() for l in x.split('+')])
    df['n_levels'] = df['level_list'].apply(len)

    # Primary level = first in list
    df['primary_level'] = df['level_list'].apply(lambda x: x[0])
    return df


def load_tv_candles():
    """Load all TV 1m candle data for level behavior analysis."""
    pattern = os.path.join(TV_CANDLE_DIR, "BATS_*, 1_*.csv")
    files = glob.glob(pattern)
    # Exclude archive
    files = [f for f in files if '/archive/' not in f]

    all_dfs = []
    for f in files:
        basename = os.path.basename(f)
        # Extract symbol from BATS_SYMBOL, 1_hash.csv
        symbol = basename.split('_')[1].split(',')[0]
        if symbol not in SYMBOLS:
            continue
        try:
            df = pd.read_csv(f)
            df['symbol'] = symbol
            all_dfs.append(df)
        except Exception as e:
            print(f"  Warning: could not read {basename}: {e}")

    if not all_dfs:
        return None

    candles = pd.concat(all_dfs, ignore_index=True)
    # Parse time
    candles['datetime'] = pd.to_datetime(candles['time'])
    candles['date'] = candles['datetime'].dt.date
    candles['hour'] = candles['datetime'].dt.hour
    candles['minute'] = candles['datetime'].dt.minute
    candles['minutes_since_open'] = candles['hour'] * 60 + candles['minute']

    # Filter to RTH (9:30-16:00 ET)
    candles = candles[(candles['minutes_since_open'] >= 570) &
                      (candles['minutes_since_open'] < 960)].copy()
    return candles


def load_ib_5m():
    """Load IB 5m parquet data for the 13 KLB symbols."""
    all_dfs = []
    for sym in SYMBOLS:
        fpath = os.path.join(IB_CACHE, f"{sym.lower()}_5_mins_ib.parquet")
        if not os.path.exists(fpath):
            continue
        try:
            df = pd.read_parquet(fpath)
            df['symbol'] = sym
            # Convert date to ET
            df['datetime'] = pd.to_datetime(df['date']).dt.tz_convert('US/Eastern')
            df['date_str'] = df['datetime'].dt.strftime('%Y-%m-%d')
            df['hour'] = df['datetime'].dt.hour
            df['minute'] = df['datetime'].dt.minute
            df['minutes_since_open'] = df['hour'] * 60 + df['minute']
            # RTH only
            df = df[(df['minutes_since_open'] >= 570) & (df['minutes_since_open'] < 960)]
            # Date range: Jan-Feb 2026 to match enriched signals
            df = df[df['date_str'] >= '2026-01-20']
            all_dfs.append(df)
        except Exception as e:
            print(f"  Warning: could not read IB 5m for {sym}: {e}")

    if not all_dfs:
        return None
    return pd.concat(all_dfs, ignore_index=True)


# ══════════════════════════════════════════════════════════════════════════
# SECTION A: Signal Type × Level Type Matrix
# ══════════════════════════════════════════════════════════════════════════

def analyze_signal_level_matrix(df):
    """Build full signal type x level type matrix."""
    print("\n" + "="*80)
    print("SECTION A: Signal Type × Level Type Matrix")
    print("="*80)

    results = {}

    # Explode multi-level signals to get per-level stats
    # But also analyze at the raw levels (combo) level

    # ── A1: By primary level × signal type ──
    print("\n── A1: Primary Level × Signal Type ──")
    for (level, sig_type), grp in df.groupby(['primary_level', 'type']):
        n = len(grp)
        win_rate = grp['winner'].mean() * 100
        avg_mfe = grp['mfe'].mean()
        avg_mae = grp['mae'].mean()
        net_atr = grp['pnl'].sum()
        avg_pnl = grp['pnl'].mean()
        results[(level, sig_type)] = {
            'n': n, 'win%': win_rate, 'avg_mfe': avg_mfe,
            'avg_mae': avg_mae, 'net_atr': net_atr, 'avg_pnl': avg_pnl
        }

    # Build pivot table
    levels_order = ['PM H', 'PM L', 'Yest H', 'Yest L', 'ORB H', 'ORB L',
                    'Week H', 'Week L', 'PD Mid', 'PD Last Hr L', 'PD Last Hr H',
                    'VWAP', 'VWAP LB', 'VWAP UB']

    print(f"\n{'Level':<12} {'Type':<5} {'N':>5} {'Win%':>6} {'MFE':>7} {'MAE':>8} {'NetATR':>8} {'AvgPnL':>8}")
    print("-" * 65)

    for level in levels_order:
        for sig_type in ['BRK', 'REV', 'Reclaim', 'Retest', 'QBS', 'FADE', 'RNG']:
            key = (level, sig_type)
            if key in results:
                r = results[key]
                flag = " ⚠️" if r['avg_pnl'] < -0.02 else " ✓" if r['avg_pnl'] > 0.05 else ""
                print(f"{level:<12} {sig_type:<5} {r['n']:>5} {r['win%']:>5.1f}% {r['avg_mfe']:>7.3f} {r['avg_mae']:>8.3f} {r['net_atr']:>8.1f} {r['avg_pnl']:>8.3f}{flag}")

    # Levels not in our predefined list
    other_levels = set(df['primary_level'].unique()) - set(levels_order)
    if other_levels:
        print(f"\n  Other levels found: {other_levels}")
        for level in sorted(other_levels):
            for sig_type in ['BRK', 'REV']:
                key = (level, sig_type)
                if key in results:
                    r = results[key]
                    print(f"{level:<12} {sig_type:<5} {r['n']:>5} {r['win%']:>5.1f}% {r['avg_mfe']:>7.3f} {r['avg_mae']:>8.3f} {r['net_atr']:>8.1f} {r['avg_pnl']:>8.3f}")

    # ── A2: Identify mismatches ──
    print("\n── A2: Mismatch Analysis ──")
    print("Signals where type doesn't match level's expected behavior:")
    print(f"\n{'Level':<12} {'Actual':<6} {'Expected':<8} {'N':>5} {'AvgPnL':>8} {'NetATR':>8}")
    print("-" * 55)

    mismatch_total_atr = 0
    for level, sig_type in sorted(results.keys()):
        expected = EXPECTED_SIGNAL.get(level, 'BRK')
        if sig_type != expected:
            r = results[(level, sig_type)]
            mismatch_total_atr += r['net_atr']
            # Also compare to the "correct" pairing if it exists
            correct_key = (level, expected)
            correct_pnl = results[correct_key]['avg_pnl'] if correct_key in results else 'N/A'
            flag = " DRAIN" if r['avg_pnl'] < 0 else ""
            print(f"{level:<12} {sig_type:<6} {expected:<8} {r['n']:>5} {r['avg_pnl']:>8.3f} {r['net_atr']:>8.1f}{flag}")

    print(f"\nTotal mismatch net ATR: {mismatch_total_atr:.1f}")

    return results


# ══════════════════════════════════════════════════════════════════════════
# SECTION B: Direction × Level Analysis
# ══════════════════════════════════════════════════════════════════════════

def analyze_direction_level(df):
    """Bull vs Bear at each level, broken by signal type."""
    print("\n" + "="*80)
    print("SECTION B: Direction × Level × Signal Type")
    print("="*80)

    print(f"\n{'Level':<12} {'Dir':<5} {'Type':<5} {'N':>5} {'Win%':>6} {'MFE':>7} {'MAE':>8} {'AvgPnL':>8} {'NetATR':>8}")
    print("-" * 75)

    results = {}
    for (level, direction, sig_type), grp in df.groupby(['primary_level', 'direction', 'type']):
        n = len(grp)
        if n < 5:
            continue
        win_rate = grp['winner'].mean() * 100
        avg_mfe = grp['mfe'].mean()
        avg_mae = grp['mae'].mean()
        avg_pnl = grp['pnl'].mean()
        net_atr = grp['pnl'].sum()
        results[(level, direction, sig_type)] = {
            'n': n, 'win%': win_rate, 'avg_mfe': avg_mfe,
            'avg_mae': avg_mae, 'avg_pnl': avg_pnl, 'net_atr': net_atr
        }
        flag = " <<<SUPPRESS" if avg_pnl < -0.04 else " ✓✓" if avg_pnl > 0.08 else ""
        print(f"{level:<12} {direction:<5} {sig_type:<5} {n:>5} {win_rate:>5.1f}% {avg_mfe:>7.3f} {avg_mae:>8.3f} {avg_pnl:>8.3f} {net_atr:>8.1f}{flag}")

    # ── Highlight best & worst combos ──
    print("\n── Top 10 BEST direction×level×type combos (by avg PnL, N≥10) ──")
    sorted_combos = sorted(
        [(k, v) for k, v in results.items() if v['n'] >= 10],
        key=lambda x: x[1]['avg_pnl'], reverse=True
    )
    for i, (k, v) in enumerate(sorted_combos[:10]):
        print(f"  {i+1}. {k[0]:<12} {k[1]:<5} {k[2]:<5} N={v['n']:>3}  PnL={v['avg_pnl']:>+.3f}  Win={v['win%']:.0f}%  NetATR={v['net_atr']:>+.1f}")

    print("\n── Bottom 10 WORST direction×level×type combos (by avg PnL, N≥10) ──")
    for i, (k, v) in enumerate(sorted_combos[-10:]):
        print(f"  {i+1}. {k[0]:<12} {k[1]:<5} {k[2]:<5} N={v['n']:>3}  PnL={v['avg_pnl']:>+.3f}  Win={v['win%']:.0f}%  NetATR={v['net_atr']:>+.1f}")

    return results


# ══════════════════════════════════════════════════════════════════════════
# SECTION C: Combo / Confluence Analysis
# ══════════════════════════════════════════════════════════════════════════

def analyze_combos(df):
    """Single level vs multi-level, rank combos."""
    print("\n" + "="*80)
    print("SECTION C: Combo / Confluence Analysis")
    print("="*80)

    # ── C1: Single vs Multi ──
    print("\n── C1: Single Level vs Multi-Level Signals ──")
    for label, grp in df.groupby(df['n_levels'].apply(lambda x: 'single' if x == 1 else 'multi')):
        n = len(grp)
        win_pct = grp['winner'].mean() * 100
        avg_pnl = grp['pnl'].mean()
        net_atr = grp['pnl'].sum()
        avg_mfe = grp['mfe'].mean()
        avg_mae = grp['mae'].mean()
        print(f"  {label:>6}: N={n:>5}  Win={win_pct:>5.1f}%  MFE={avg_mfe:.3f}  MAE={avg_mae:.3f}  AvgPnL={avg_pnl:>+.3f}  NetATR={net_atr:>+.1f}")

    # ── C2: Multi-level breakdown by count ──
    print("\n── C2: By Number of Levels ──")
    for n_lvl, grp in df.groupby('n_levels'):
        n = len(grp)
        win_pct = grp['winner'].mean() * 100
        avg_pnl = grp['pnl'].mean()
        net_atr = grp['pnl'].sum()
        print(f"  {n_lvl} levels: N={n:>5}  Win={win_pct:>5.1f}%  AvgPnL={avg_pnl:>+.3f}  NetATR={net_atr:>+.1f}")

    # ── C3: Rank all observed raw level combos ──
    print("\n── C3: All Level Combos Ranked by Avg PnL (N≥5) ──")
    print(f"  {'Levels':<35} {'Type':<5} {'N':>5} {'Win%':>6} {'MFE':>7} {'MAE':>8} {'AvgPnL':>8} {'NetATR':>8}")
    print("  " + "-" * 85)

    combo_results = {}
    for (levels, sig_type), grp in df.groupby(['levels', 'type']):
        n = len(grp)
        if n < 5:
            continue
        combo_results[(levels, sig_type)] = {
            'n': n,
            'win%': grp['winner'].mean() * 100,
            'avg_mfe': grp['mfe'].mean(),
            'avg_mae': grp['mae'].mean(),
            'avg_pnl': grp['pnl'].mean(),
            'net_atr': grp['pnl'].sum()
        }

    sorted_combos = sorted(combo_results.items(), key=lambda x: x[1]['avg_pnl'], reverse=True)
    for (levels, sig_type), v in sorted_combos:
        flag = " <<<" if v['avg_pnl'] < -0.04 else ""
        print(f"  {levels:<35} {sig_type:<5} {v['n']:>5} {v['win%']:>5.1f}% {v['avg_mfe']:>7.3f} {v['avg_mae']:>8.3f} {v['avg_pnl']:>8.3f} {v['net_atr']:>8.1f}{flag}")

    return combo_results


# ══════════════════════════════════════════════════════════════════════════
# SECTION D: Level Behavior Over Time (using IB 5m data)
# ══════════════════════════════════════════════════════════════════════════

def analyze_level_behavior_over_time(df):
    """How does level behavior change during the day?"""
    print("\n" + "="*80)
    print("SECTION D: Level Behavior Over Time")
    print("="*80)

    # Time buckets for intraday analysis
    time_buckets = [
        ('9:30-10:00', 570, 600),
        ('10:00-10:30', 600, 630),
        ('10:30-11:00', 630, 660),
        ('11:00-12:00', 660, 720),
        ('12:00-14:00', 720, 840),
        ('14:00-16:00', 840, 960),
    ]

    # ── D1: Signal type performance by time at each level ──
    print("\n── D1: Level Performance by Time of Day ──")
    print(f"  {'Level':<12} {'Time':<14} {'Type':<5} {'N':>5} {'Win%':>6} {'AvgPnL':>8}")
    print("  " + "-" * 55)

    for level in ['ORB H', 'ORB L', 'PM H', 'PM L', 'Yest H', 'Yest L', 'Week H', 'Week L']:
        level_df = df[df['primary_level'] == level]
        if len(level_df) < 10:
            continue

        for bucket_name, t_start, t_end in time_buckets:
            bucket_df = level_df[(level_df['minutes'] >= t_start) & (level_df['minutes'] < t_end)]
            if len(bucket_df) < 3:
                continue

            for sig_type in ['BRK', 'REV']:
                type_df = bucket_df[bucket_df['type'] == sig_type]
                if len(type_df) < 3:
                    continue
                n = len(type_df)
                win_pct = type_df['winner'].mean() * 100
                avg_pnl = type_df['pnl'].mean()
                flag = " !!!" if avg_pnl < -0.05 else ""
                print(f"  {level:<12} {bucket_name:<14} {sig_type:<5} {n:>5} {win_pct:>5.1f}% {avg_pnl:>8.3f}{flag}")
        print()

    # ── D2: BRK vs REV win rate shift during day ──
    print("\n── D2: BRK vs REV Performance Shift During Day ──")
    for bucket_name, t_start, t_end in time_buckets:
        bucket_df = df[(df['minutes'] >= t_start) & (df['minutes'] < t_end)]
        if len(bucket_df) < 10:
            continue
        brk = bucket_df[bucket_df['type'] == 'BRK']
        rev = bucket_df[bucket_df['type'] == 'REV']
        brk_pnl = brk['pnl'].mean() if len(brk) > 0 else 0
        rev_pnl = rev['pnl'].mean() if len(rev) > 0 else 0
        brk_win = brk['winner'].mean() * 100 if len(brk) > 0 else 0
        rev_win = rev['winner'].mean() * 100 if len(rev) > 0 else 0
        print(f"  {bucket_name:<14}  BRK: N={len(brk):>4} Win={brk_win:>5.1f}% PnL={brk_pnl:>+.3f}  |  REV: N={len(rev):>4} Win={rev_win:>5.1f}% PnL={rev_pnl:>+.3f}")

    # ── D3: Level "staleness" — how old is the level when signal fires? ──
    # ORB levels are fresh each day, PM levels are from yesterday's session
    # Yest H/L from yesterday, Week H/L can be multiple days old
    print("\n── D3: Level Age / Staleness Proxy ──")
    print("  (Level freshness: ORB=same day, PM/Yest=1 day, Week=1-5 days)")
    staleness_map = {
        'ORB H': 'Fresh (same-day)', 'ORB L': 'Fresh (same-day)',
        'PM H': '1-day old', 'PM L': '1-day old',
        'Yest H': '1-day old', 'Yest L': '1-day old',
        'Week H': '1-5 days old', 'Week L': '1-5 days old',
    }

    for staleness in ['Fresh (same-day)', '1-day old', '1-5 days old']:
        levels_in_group = [l for l, s in staleness_map.items() if s == staleness]
        grp = df[df['primary_level'].isin(levels_in_group)]
        if len(grp) < 5:
            continue
        n = len(grp)
        win_pct = grp['winner'].mean() * 100
        avg_pnl = grp['pnl'].mean()
        net_atr = grp['pnl'].sum()
        print(f"  {staleness:<20}: N={n:>5}  Win={win_pct:>5.1f}%  AvgPnL={avg_pnl:>+.3f}  NetATR={net_atr:>+.1f}")

    # ── D3b: Level staleness × time of day ──
    print("\n── D3b: Level Freshness × Time of Day ──")
    for staleness in ['Fresh (same-day)', '1-day old', '1-5 days old']:
        levels_in_group = [l for l, s in staleness_map.items() if s == staleness]
        grp = df[df['primary_level'].isin(levels_in_group)]
        if len(grp) < 5:
            continue
        print(f"\n  {staleness}:")
        for bucket_name, t_start, t_end in time_buckets:
            bucket_df = grp[(grp['minutes'] >= t_start) & (grp['minutes'] < t_end)]
            if len(bucket_df) < 3:
                continue
            n = len(bucket_df)
            avg_pnl = bucket_df['pnl'].mean()
            win_pct = bucket_df['winner'].mean() * 100
            print(f"    {bucket_name:<14}: N={n:>4}  Win={win_pct:>5.1f}%  PnL={avg_pnl:>+.3f}")


# ══════════════════════════════════════════════════════════════════════════
# SECTION D-EXTRA: Level Touch Behavior (Breakout vs Bounce vs False Break)
# ══════════════════════════════════════════════════════════════════════════

def analyze_level_touch_behavior(candles_unused):
    """
    For each level type, classify touches as:
    - Breakout: price crosses and stays crossed for 6+ bars (30 min on 5m)
    - Bounce: price touches then reverses
    - False break: price crosses but comes back within 6 bars
    Uses IB 5m parquet data with levels derived from price history.
    """
    print("\n" + "="*80)
    print("SECTION D-EXTRA: Level Touch Behavior Classification (IB 5m data)")
    print("="*80)

    # Load IB 5m data
    all_dfs = []
    for sym in SYMBOLS:
        fpath = os.path.join(IB_CACHE, f"{sym.lower()}_5_mins_ib.parquet")
        if not os.path.exists(fpath):
            continue
        try:
            df = pd.read_parquet(fpath)
            df['symbol'] = sym
            df['datetime'] = pd.to_datetime(df['date']).dt.tz_convert('US/Eastern')
            df['cal_date'] = df['datetime'].dt.date
            df['hour'] = df['datetime'].dt.hour
            df['minute'] = df['datetime'].dt.minute
            df['minutes_since_open'] = df['hour'] * 60 + df['minute']
            # RTH only
            df = df[(df['minutes_since_open'] >= 570) & (df['minutes_since_open'] < 960)]
            df = df[df['cal_date'] >= pd.Timestamp('2026-01-20').date()]
            all_dfs.append(df)
        except Exception as e:
            print(f"  Warning: {sym}: {e}")

    if not all_dfs:
        print("  No IB data available, skipping.")
        return None

    ib5m = pd.concat(all_dfs, ignore_index=True)
    print(f"  Loaded {len(ib5m)} IB 5m bars for {ib5m['symbol'].nunique()} symbols")

    # Compute levels per symbol-date
    # For each trading day, compute: Yest H/L, ORB H/L (first 30 min = 6 bars at 5m)
    results = {}
    all_touches = []

    for sym in SYMBOLS:
        sym_df = ib5m[ib5m['symbol'] == sym].sort_values('datetime').copy()
        dates = sorted(sym_df['cal_date'].unique())

        for i, dt in enumerate(dates):
            day_df = sym_df[sym_df['cal_date'] == dt].copy()
            if len(day_df) < 12:
                continue

            # ORB: first 6 bars (30 min at 5m)
            orb_bars = day_df.head(6)
            orb_h = orb_bars['high'].max()
            orb_l = orb_bars['low'].min()

            # Yesterday's H/L
            yest_h = yest_l = None
            if i > 0:
                prev_dt = dates[i-1]
                prev_df = sym_df[sym_df['cal_date'] == prev_dt]
                if len(prev_df) > 0:
                    yest_h = prev_df['high'].max()
                    yest_l = prev_df['low'].min()

            # For each level, find touches and classify
            levels_to_check = {
                'ORB H': (orb_h, True),
                'ORB L': (orb_l, False),
            }
            if yest_h is not None:
                levels_to_check['Yest H'] = (yest_h, True)
                levels_to_check['Yest L'] = (yest_l, False)

            # Only check after ORB is established (after first 30 min)
            post_orb = day_df.iloc[6:]
            if len(post_orb) < 6:
                continue

            for level_name, (level_price, is_high) in levels_to_check.items():
                if level_price is None or np.isnan(level_price):
                    continue

                # Find first touch: bar where high >= level (for HIGH) or low <= level (for LOW)
                if is_high:
                    touch_mask = post_orb['high'] >= level_price
                else:
                    touch_mask = post_orb['low'] <= level_price

                touches = post_orb[touch_mask]
                if len(touches) == 0:
                    continue

                # First touch only
                touch_idx = touches.index[0]
                touch_pos = post_orb.index.get_loc(touch_idx)

                # Get next 6 bars (30 min at 5m)
                future = post_orb.iloc[touch_pos+1:touch_pos+7]
                if len(future) < 4:
                    continue

                touch_minute = post_orb.loc[touch_idx, 'minutes_since_open']

                # Classify
                if is_high:
                    bars_above = (future['close'] > level_price).sum()
                    if bars_above >= len(future) * 0.7:
                        outcome = 'breakout'
                    elif bars_above <= len(future) * 0.3:
                        outcome = 'bounce'
                    else:
                        outcome = 'false_break'
                else:
                    bars_below = (future['close'] < level_price).sum()
                    if bars_below >= len(future) * 0.7:
                        outcome = 'breakout'
                    elif bars_below <= len(future) * 0.3:
                        outcome = 'bounce'
                    else:
                        outcome = 'false_break'

                all_touches.append({
                    'symbol': sym, 'date': dt, 'level': level_name,
                    'level_price': level_price, 'outcome': outcome,
                    'touch_minute': touch_minute
                })

    if not all_touches:
        print("  No touches classified.")
        return None

    touches_df = pd.DataFrame(all_touches)
    print(f"  Classified {len(touches_df)} level touches")

    # Aggregate by level
    print(f"\n  {'Level':<12} {'N':>5} {'Breakout%':>10} {'Bounce%':>10} {'FalseBreak%':>12} {'Behavior':<10}")
    print("  " + "-" * 65)

    for level in ['ORB H', 'ORB L', 'Yest H', 'Yest L']:
        ldf = touches_df[touches_df['level'] == level]
        if len(ldf) == 0:
            continue
        n = len(ldf)
        brk_pct = (ldf['outcome'] == 'breakout').mean() * 100
        bnc_pct = (ldf['outcome'] == 'bounce').mean() * 100
        fb_pct = (ldf['outcome'] == 'false_break').mean() * 100
        behavior = "BARRIER" if brk_pct > bnc_pct else "MAGNET"
        results[level] = {
            'total': n, 'breakout%': brk_pct, 'bounce%': bnc_pct,
            'false_break%': fb_pct, 'behavior': behavior
        }
        print(f"  {level:<12} {n:>5} {brk_pct:>9.1f}% {bnc_pct:>9.1f}% {fb_pct:>11.1f}%  {behavior}")

    # Touch behavior by time of day
    print(f"\n  Touch Behavior by Time of Day:")
    print(f"  {'Level':<12} {'Time':<14} {'N':>5} {'Breakout%':>10} {'Bounce%':>10}")
    print("  " + "-" * 55)

    time_bins = [(570, 600, '9:30-10'), (600, 660, '10-11'), (660, 720, '11-12'), (720, 960, '12-16')]
    for level in ['ORB H', 'ORB L', 'Yest H', 'Yest L']:
        ldf = touches_df[touches_df['level'] == level]
        for t_start, t_end, t_label in time_bins:
            tdf = ldf[(ldf['touch_minute'] >= t_start) & (ldf['touch_minute'] < t_end)]
            if len(tdf) < 3:
                continue
            n = len(tdf)
            brk_pct = (tdf['outcome'] == 'breakout').mean() * 100
            bnc_pct = (tdf['outcome'] == 'bounce').mean() * 100
            print(f"  {level:<12} {t_label:<14} {n:>5} {brk_pct:>9.1f}% {bnc_pct:>9.1f}%")

    return results


# ══════════════════════════════════════════════════════════════════════════
# SECTION E: Recommendations
# ══════════════════════════════════════════════════════════════════════════

def generate_recommendations(df, matrix_results, dir_results, combo_results):
    """Synthesize all findings into actionable recommendations."""
    print("\n" + "="*80)
    print("SECTION E: Recommendations")
    print("="*80)

    # ── E1: Signal type reassignment candidates ──
    print("\n── E1: Signal Type Reassignment Candidates ──")
    print("  (Where the 'wrong' signal type outperforms the 'right' one)")

    for level in ['PM H', 'PM L', 'Yest H', 'Yest L', 'ORB H', 'ORB L', 'Week H', 'Week L']:
        brk_key = (level, 'BRK')
        rev_key = (level, 'REV')
        brk_pnl = matrix_results.get(brk_key, {}).get('avg_pnl', None)
        rev_pnl = matrix_results.get(rev_key, {}).get('avg_pnl', None)
        brk_n = matrix_results.get(brk_key, {}).get('n', 0)
        rev_n = matrix_results.get(rev_key, {}).get('n', 0)

        if brk_pnl is not None and rev_pnl is not None and brk_n >= 10 and rev_n >= 10:
            better = "BRK" if brk_pnl > rev_pnl else "REV"
            worse = "REV" if better == "BRK" else "BRK"
            expected = EXPECTED_SIGNAL.get(level, 'BRK')

            if better != expected:
                atr_gap = abs(brk_pnl - rev_pnl)
                print(f"  {level}: {better} beats {worse} by {atr_gap:.3f} avg PnL (expected: {expected})")
                print(f"    {better}: N={matrix_results[(level, better)]['n']}, PnL={matrix_results[(level, better)]['avg_pnl']:+.3f}")
                print(f"    {worse}: N={matrix_results[(level, worse)]['n']}, PnL={matrix_results[(level, worse)]['avg_pnl']:+.3f}")

    # ── E2: Suppression candidates ──
    print("\n── E2: Suppression Candidates (net negative, N≥10) ──")
    print("  These level×type×direction combos are losing ATR and should be suppressed:")

    suppress_list = []
    if dir_results:
        for (level, direction, sig_type), v in sorted(dir_results.items(), key=lambda x: x[1]['avg_pnl']):
            if v['avg_pnl'] < -0.03 and v['n'] >= 10:
                atr_drain = v['net_atr']
                suppress_list.append((level, direction, sig_type, v['n'], v['avg_pnl'], atr_drain))

    total_suppression_atr = 0
    for level, direction, sig_type, n, avg_pnl, atr_drain in suppress_list:
        total_suppression_atr += abs(atr_drain)
        print(f"  SUPPRESS: {level:<12} {direction:<5} {sig_type:<5}  N={n:>3}  PnL={avg_pnl:>+.3f}  ATR drain={atr_drain:>+.1f}")

    print(f"\n  Total recoverable ATR from suppression: {total_suppression_atr:.1f}")

    # ── E3: Ideal signal type mapping ──
    print("\n── E3: Ideal Signal Type Mapping (data-driven) ──")
    print("  Based on which signal type performs best at each level:")

    for level in ['PM H', 'PM L', 'Yest H', 'Yest L', 'ORB H', 'ORB L', 'Week H', 'Week L']:
        best_type = None
        best_pnl = -999
        for sig_type in ['BRK', 'REV']:
            key = (level, sig_type)
            if key in matrix_results and matrix_results[key]['n'] >= 10:
                if matrix_results[key]['avg_pnl'] > best_pnl:
                    best_pnl = matrix_results[key]['avg_pnl']
                    best_type = sig_type

        if best_type:
            expected = EXPECTED_SIGNAL.get(level, 'BRK')
            match = "✓" if best_type == expected else "CHANGE →"
            print(f"  {level:<12}: Best = {best_type:<5} (PnL={best_pnl:>+.3f})  Expected: {expected:<5}  {match}")

    # ── E4: Direction gating recommendations ──
    print("\n── E4: Direction Gating Recommendations ──")
    for level in ['PM H', 'PM L', 'Yest H', 'Yest L', 'ORB H', 'ORB L', 'Week H', 'Week L']:
        for sig_type in ['BRK', 'REV']:
            bull_key = (level, 'bull', sig_type)
            bear_key = (level, 'bear', sig_type)

            bull_v = dir_results.get(bull_key)
            bear_v = dir_results.get(bear_key)

            if bull_v and bear_v:
                gap = bull_v['avg_pnl'] - bear_v['avg_pnl']
                if abs(gap) > 0.06:
                    better = "bull" if gap > 0 else "bear"
                    worse = "bear" if gap > 0 else "bull"
                    print(f"  {level} {sig_type}: {better} >> {worse} (gap={abs(gap):.3f} PnL)")
                    print(f"    {better}: N={dir_results[(level, better, sig_type)]['n']}  PnL={dir_results[(level, better, sig_type)]['avg_pnl']:+.3f}")
                    print(f"    {worse}: N={dir_results[(level, worse, sig_type)]['n']}  PnL={dir_results[(level, worse, sig_type)]['avg_pnl']:+.3f}")


# ══════════════════════════════════════════════════════════════════════════
# SECTION F: Conf Pass Analysis by Level×Type
# ══════════════════════════════════════════════════════════════════════════

def analyze_conf_by_level_type(df):
    """How does CONF pass/fail interact with level×type?"""
    print("\n" + "="*80)
    print("SECTION F: Confirmation Status × Level × Type")
    print("="*80)

    # CONF values: ✓, ✓★, ✗, NaN (no conf yet / REV signals)
    df['conf_status'] = df['conf'].fillna('none')

    print(f"\n{'Level':<12} {'Type':<5} {'Conf':<6} {'N':>5} {'Win%':>6} {'AvgPnL':>8} {'NetATR':>8}")
    print("-" * 60)

    for level in ['ORB H', 'ORB L', 'PM H', 'PM L', 'Yest H', 'Yest L', 'Week H', 'Week L']:
        level_df = df[df['primary_level'] == level]
        for sig_type in ['BRK', 'REV']:
            type_df = level_df[level_df['type'] == sig_type]
            for conf in ['✓', '✓★', '✗', 'none']:
                conf_df = type_df[type_df['conf_status'] == conf]
                if len(conf_df) < 3:
                    continue
                n = len(conf_df)
                win_pct = conf_df['winner'].mean() * 100
                avg_pnl = conf_df['pnl'].mean()
                net_atr = conf_df['pnl'].sum()
                print(f"{level:<12} {sig_type:<5} {conf:<6} {n:>5} {win_pct:>5.1f}% {avg_pnl:>8.3f} {net_atr:>8.1f}")
        print()


# ══════════════════════════════════════════════════════════════════════════
# SECTION G: EMA-Aligned Split
# ══════════════════════════════════════════════════════════════════════════

def analyze_ema_split(df):
    """EMA aligned vs not, split by level×type."""
    print("\n" + "="*80)
    print("SECTION G: EMA Alignment × Level × Type")
    print("="*80)

    # EMA alignment: ema column = 'bull'/'bear'/'mixed'
    # For bull signals, aligned = ema=='bull'. For bear, aligned = ema=='bear'.
    def is_ema_aligned(row):
        if row['direction'] == 'bull' and row['ema'] == 'bull':
            return True
        if row['direction'] == 'bear' and row['ema'] == 'bear':
            return True
        return False

    df['ema_aligned'] = df.apply(is_ema_aligned, axis=1)

    print(f"\n{'Level':<12} {'Type':<5} {'EMA':<8} {'N':>5} {'Win%':>6} {'AvgPnL':>8} {'NetATR':>8}")
    print("-" * 60)

    for level in ['ORB H', 'ORB L', 'PM H', 'PM L', 'Yest H', 'Yest L', 'Week H', 'Week L']:
        level_df = df[df['primary_level'] == level]
        for sig_type in ['BRK', 'REV']:
            type_df = level_df[level_df['type'] == sig_type]
            for ema_label, ema_val in [('aligned', True), ('against', False)]:
                ema_df = type_df[type_df['ema_aligned'] == ema_val]
                if len(ema_df) < 5:
                    continue
                n = len(ema_df)
                win_pct = ema_df['winner'].mean() * 100
                avg_pnl = ema_df['pnl'].mean()
                net_atr = ema_df['pnl'].sum()
                flag = " !!!" if avg_pnl < -0.04 else " ✓✓" if avg_pnl > 0.06 else ""
                print(f"{level:<12} {sig_type:<5} {ema_label:<8} {n:>5} {win_pct:>5.1f}% {avg_pnl:>8.3f} {net_atr:>8.1f}{flag}")
        print()


# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════

def main():
    print("Signal Type Matching Analysis")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Load data
    print("\nLoading enriched signals...")
    df = load_enriched()
    print(f"  Loaded {len(df)} signals")
    print(f"  Signal types: {df['type'].value_counts().to_dict()}")
    print(f"  Level types: {df['level_type'].value_counts().to_dict()}")
    print(f"  Primary levels: {df['primary_level'].value_counts().to_dict()}")

    print("\nLoading TV 1m candles...")
    candles = load_tv_candles()
    if candles is not None:
        print(f"  Loaded {len(candles)} RTH candle rows")
    else:
        print("  No TV candle data loaded")

    # Run all analyses
    matrix_results = analyze_signal_level_matrix(df)
    dir_results = analyze_direction_level(df)
    combo_results = analyze_combos(df)
    analyze_level_behavior_over_time(df)
    touch_results = analyze_level_touch_behavior(None)
    analyze_conf_by_level_type(df)
    analyze_ema_split(df)
    generate_recommendations(df, matrix_results, dir_results, combo_results)

    print("\n" + "="*80)
    print("Analysis complete.")
    print("="*80)


if __name__ == "__main__":
    main()
