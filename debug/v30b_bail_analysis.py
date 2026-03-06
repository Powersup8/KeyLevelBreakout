#!/usr/bin/env python3
"""
v30b BAIL Investigation — Is the 5-Minute BAIL Check Too Aggressive on Trending Days?

Pine code shows: hold = pnl > 0.05 ATR (1 signal bar = ~5 min on 5m TF after CONF)
This script simulates that check + alternatives using IB 1m data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ── Paths ──────────────────────────────────────────────────────────
PROJECT = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView")
IB_BARS = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars")
SIGNALS_CSV = PROJECT / "debug" / "enriched-signals.csv"
OUTPUT_MD = PROJECT / "debug" / "v30b-bail-investigation.md"

# ── KLB symbols ────────────────────────────────────────────────────
KLB_SYMBOLS = ['SPY','AAPL','AMD','AMZN','GLD','GOOGL','META','MSFT','NVDA','QQQ','SLV','TSLA','TSM']

# ── Load signals ───────────────────────────────────────────────────
def load_signals():
    df = pd.read_csv(SIGNALS_CSV)
    # Only confirmed signals (those that got CONF pass)
    # conf = '✓' or '✓★'
    df['conf_pass'] = df['conf'].isin(['✓', '✓★'])
    return df

# ── Load IB 1m data for a symbol ──────────────────────────────────
def load_1m(symbol):
    fname = IB_BARS / f"{symbol.lower()}_1_min_ib.parquet"
    if not fname.exists():
        return None
    df = pd.read_parquet(fname)
    # Filter to regular trading hours (9:30-16:00 ET)
    df = df[df['date'].dt.hour * 60 + df['date'].dt.minute >= 9*60+30]
    df = df[df['date'].dt.hour * 60 + df['date'].dt.minute < 16*60]
    df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')
    df['time_str'] = df['date'].dt.strftime('%H:%M')
    return df

# ── Load SPY daily for trending day classification ────────────────
def load_spy_daily():
    fname = IB_BARS / "spy_1_day_ib.parquet"
    df = pd.read_parquet(fname)
    df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')
    df['daily_return'] = (df['close'] - df['open']) / df['open'] * 100
    df['daily_range'] = (df['high'] - df['low'])
    return df

# ── Simulate BAIL check ──────────────────────────────────────────
def simulate_bail(signals_df, threshold_atr=0.05, check_minutes=5):
    """
    For each confirmed signal, simulate the 5m checkpoint.
    Returns df with bail_result, pnl_at_check, pnl_at_30m, etc.
    """
    results = []

    # Cache 1m data per symbol
    cache_1m = {}
    for sym in KLB_SYMBOLS:
        data = load_1m(sym)
        if data is not None:
            cache_1m[sym] = data

    for _, sig in signals_df.iterrows():
        sym = sig['symbol']
        if sym not in cache_1m:
            continue

        bars = cache_1m[sym]
        date_str = sig['date']
        sig_time = sig['time']
        direction = sig['direction']
        atr = sig['atr']

        if pd.isna(atr) or atr == 0:
            continue

        # Find the signal bar in IB data
        day_bars = bars[bars['date_str'] == date_str].copy()
        if day_bars.empty:
            continue

        # Parse signal time (format like "9:35" or "10:05")
        try:
            sig_h, sig_m = [int(x) for x in sig_time.split(':')]
            sig_minutes = sig_h * 60 + sig_m
        except:
            continue

        day_bars = day_bars.sort_values('date')
        day_bars['minutes'] = day_bars['date'].dt.hour * 60 + day_bars['date'].dt.minute

        # Signal entry = close of the signal bar
        sig_bar = day_bars[day_bars['minutes'] == sig_minutes]
        if sig_bar.empty:
            # Try closest bar
            sig_bar = day_bars.iloc[(day_bars['minutes'] - sig_minutes).abs().argsort()[:1]]
            if abs(sig_bar['minutes'].iloc[0] - sig_minutes) > 2:
                continue

        entry_price = sig_bar['close'].iloc[0]

        # Get bars after entry
        after_entry = day_bars[day_bars['minutes'] > sig_minutes].copy()
        if after_entry.empty:
            continue

        # PnL at various time horizons (in ATR units)
        result = {
            'symbol': sym,
            'date': date_str,
            'time': sig_time,
            'direction': direction,
            'conf': sig['conf'],
            'entry_price': entry_price,
            'atr': atr,
            'ema': sig['ema'],
            'vwap': sig['vwap'],
            'adx': sig['adx'],
            'vol': sig['vol'],
            'time_bucket': sig['time_bucket'],
            'mfe_csv': sig['mfe'],
            'mae_csv': sig['mae'],
        }

        # Calculate PnL at check_minutes intervals
        for t in [5, 10, 15, 20, 30, 45, 60]:
            future_bar = after_entry[(after_entry['minutes'] >= sig_minutes + t) &
                                     (after_entry['minutes'] <= sig_minutes + t + 1)]
            if future_bar.empty:
                future_bar = after_entry[after_entry['minutes'] >= sig_minutes + t].head(1)

            if not future_bar.empty:
                future_price = future_bar['close'].iloc[0]
                if direction == 'bull':
                    pnl = (future_price - entry_price) / atr
                else:
                    pnl = (entry_price - future_price) / atr
                result[f'pnl_{t}m'] = pnl
            else:
                result[f'pnl_{t}m'] = np.nan

        # MFE/MAE over first 30 minutes
        bars_30m = after_entry[after_entry['minutes'] <= sig_minutes + 30]
        if not bars_30m.empty:
            if direction == 'bull':
                mfe_30 = (bars_30m['high'].max() - entry_price) / atr
                mae_30 = (bars_30m['low'].min() - entry_price) / atr
            else:
                mfe_30 = (entry_price - bars_30m['low'].min()) / atr
                mae_30 = (entry_price - bars_30m['high'].max()) / atr
            result['mfe_30m'] = mfe_30
            result['mae_30m'] = mae_30

        # MFE over full remaining day
        if not after_entry.empty:
            if direction == 'bull':
                mfe_day = (after_entry['high'].max() - entry_price) / atr
                mae_day = (after_entry['low'].min() - entry_price) / atr
            else:
                mfe_day = (entry_price - after_entry['low'].min()) / atr
                mae_day = (entry_price - after_entry['high'].max()) / atr
            result['mfe_day'] = mfe_day
            result['mae_day'] = mae_day

        # Current BAIL logic: hold if pnl_5m > 0.05
        pnl_5m = result.get('pnl_5m', np.nan)
        result['bail_current'] = 'HOLD' if (not pd.isna(pnl_5m) and pnl_5m > threshold_atr) else 'BAIL'

        results.append(result)

    return pd.DataFrame(results)


def classify_trending_days(spy_daily, results_df):
    """Classify each day as trending or choppy based on SPY behavior."""
    # Compute SPY ATR (14-day)
    spy_daily = spy_daily.sort_values('date')
    spy_daily['atr_14'] = spy_daily['daily_range'].rolling(14).mean()

    day_classification = {}
    for _, row in spy_daily.iterrows():
        ds = row['date_str']
        atr = row.get('atr_14', row['daily_range'])
        if pd.isna(atr) or atr == 0:
            atr = row['daily_range']

        # Trending = |close - open| > 0.6 * daily_range (directional)
        body = abs(row['close'] - row['open'])
        range_ = row['high'] - row['low']
        if range_ > 0:
            body_ratio = body / range_
        else:
            body_ratio = 0

        trend_dir = 'up' if row['close'] > row['open'] else 'down'

        # Also: trending if daily return > 0.5% in absolute terms
        ret = abs(row.get('daily_return', 0))

        if body_ratio > 0.5 and ret > 0.3:
            day_type = f'trending_{trend_dir}'
        elif body_ratio < 0.3 or ret < 0.15:
            day_type = 'choppy'
        else:
            day_type = 'mixed'

        day_classification[ds] = {
            'day_type': day_type,
            'spy_return': row.get('daily_return', 0),
            'body_ratio': body_ratio,
            'trend_dir': trend_dir
        }

    return day_classification


def compute_threshold_sweep(results_df):
    """Sweep multiple BAIL thresholds to find optimal."""
    thresholds = [-0.10, -0.05, 0.00, 0.02, 0.05, 0.08, 0.10, 0.15, 0.20]
    sweep_results = []

    for thr in thresholds:
        # Apply threshold
        conf_df = results_df[results_df['conf'].isin(['✓', '✓★'])].copy()
        if conf_df.empty:
            continue

        conf_df['decision'] = conf_df['pnl_5m'].apply(
            lambda x: 'HOLD' if (not pd.isna(x) and x > thr) else 'BAIL'
        )

        hold = conf_df[conf_df['decision'] == 'HOLD']
        bail = conf_df[conf_df['decision'] == 'BAIL']

        n_hold = len(hold)
        n_bail = len(bail)
        n_total = n_hold + n_bail

        # HOLD performance (assume we keep the trade — use pnl_30m as outcome)
        hold_pnl_30m = hold['pnl_30m'].dropna()
        hold_avg_pnl = hold_pnl_30m.mean() if len(hold_pnl_30m) > 0 else 0
        hold_total_pnl = hold_pnl_30m.sum() if len(hold_pnl_30m) > 0 else 0
        hold_winrate = (hold_pnl_30m > 0).mean() * 100 if len(hold_pnl_30m) > 0 else 0

        # BAIL performance (we exit — PnL = pnl_5m, the exit point)
        bail_pnl_exit = bail['pnl_5m'].dropna()
        bail_total_exit_pnl = bail_pnl_exit.sum() if len(bail_pnl_exit) > 0 else 0

        # What BAILed signals would have done at 30m (the counterfactual)
        bail_pnl_30m = bail['pnl_30m'].dropna()
        bail_would_win = (bail_pnl_30m > 0).sum() if len(bail_pnl_30m) > 0 else 0
        bail_counterfactual_pnl = bail_pnl_30m.sum() if len(bail_pnl_30m) > 0 else 0

        # Net PnL = HOLD trades at 30m + BAIL trades at 5m exit
        net_pnl = hold_total_pnl + bail_total_exit_pnl

        # Counterfactual: if we held everything (no BAIL at all)
        all_pnl_30m = conf_df['pnl_30m'].dropna()
        hold_all_pnl = all_pnl_30m.sum()

        sweep_results.append({
            'threshold': thr,
            'n_hold': n_hold,
            'n_bail': n_bail,
            'hold_pct': n_hold / n_total * 100 if n_total > 0 else 0,
            'bail_pct': n_bail / n_total * 100 if n_total > 0 else 0,
            'hold_avg_pnl_30m': hold_avg_pnl,
            'hold_total_pnl_30m': hold_total_pnl,
            'hold_winrate_30m': hold_winrate,
            'bail_exit_total_pnl': bail_total_exit_pnl,
            'bail_would_win_count': bail_would_win,
            'bail_would_win_pct': bail_would_win / len(bail_pnl_30m) * 100 if len(bail_pnl_30m) > 0 else 0,
            'bail_counterfactual_pnl': bail_counterfactual_pnl,
            'net_pnl_with_bail': net_pnl,
            'net_pnl_no_bail': hold_all_pnl,
            'bail_value_add': net_pnl - hold_all_pnl,
        })

    return pd.DataFrame(sweep_results)


def direction_aware_bail(results_df, day_classes):
    """Test direction-aware BAIL: wider threshold when signal matches day trend."""
    conf_df = results_df[results_df['conf'].isin(['✓', '✓★'])].copy()
    if conf_df.empty:
        return {}

    # Add day classification
    conf_df['day_type'] = conf_df['date'].map(lambda d: day_classes.get(d, {}).get('day_type', 'unknown'))
    conf_df['trend_dir'] = conf_df['date'].map(lambda d: day_classes.get(d, {}).get('trend_dir', 'unknown'))

    # Signal matches trend?
    conf_df['with_trend'] = (
        ((conf_df['direction'] == 'bull') & (conf_df['trend_dir'] == 'up')) |
        ((conf_df['direction'] == 'bear') & (conf_df['trend_dir'] == 'down'))
    )

    scenarios = {}

    # Scenario 1: Current (0.05 for all)
    conf_df['bail_s1'] = conf_df['pnl_5m'].apply(lambda x: x > 0.05 if not pd.isna(x) else False)

    # Scenario 2: Direction-aware (0.00 with-trend, 0.05 counter-trend)
    conf_df['bail_s2'] = conf_df.apply(
        lambda r: r['pnl_5m'] > (0.00 if r['with_trend'] else 0.05) if not pd.isna(r['pnl_5m']) else False, axis=1)

    # Scenario 3: Direction-aware wider (−0.05 with-trend, 0.05 counter-trend)
    conf_df['bail_s3'] = conf_df.apply(
        lambda r: r['pnl_5m'] > (-0.05 if r['with_trend'] else 0.05) if not pd.isna(r['pnl_5m']) else False, axis=1)

    # Scenario 4: Trending-day aware (−0.05 on trending days, 0.05 on choppy)
    conf_df['bail_s4'] = conf_df.apply(
        lambda r: r['pnl_5m'] > (-0.05 if 'trending' in str(r['day_type']) else 0.05) if not pd.isna(r['pnl_5m']) else False, axis=1)

    for scenario, col in [('Current (0.05 all)', 'bail_s1'),
                           ('Dir-aware (0.00/0.05)', 'bail_s2'),
                           ('Dir-aware (-0.05/0.05)', 'bail_s3'),
                           ('Trend-day (-0.05/0.05)', 'bail_s4')]:
        hold = conf_df[conf_df[col]]
        bail = conf_df[~conf_df[col]]

        hold_pnl = hold['pnl_30m'].dropna().sum()
        bail_pnl = bail['pnl_5m'].dropna().sum()  # exit at 5m
        net = hold_pnl + bail_pnl

        # Breakdown by trending/choppy
        trending = conf_df[conf_df['day_type'].str.contains('trending', na=False)]
        choppy = conf_df[conf_df['day_type'] == 'choppy']

        t_hold = trending[trending[col]]
        t_bail = trending[~trending[col]]
        t_net = t_hold['pnl_30m'].dropna().sum() + t_bail['pnl_5m'].dropna().sum()

        c_hold = choppy[choppy[col]]
        c_bail = choppy[~choppy[col]]
        c_net = c_hold['pnl_30m'].dropna().sum() + c_bail['pnl_5m'].dropna().sum()

        scenarios[scenario] = {
            'n_hold': len(hold),
            'n_bail': len(bail),
            'hold_pct': len(hold) / len(conf_df) * 100,
            'net_pnl': net,
            'trending_net': t_net,
            'choppy_net': c_net,
            'trending_n': len(trending),
            'choppy_n': len(choppy),
        }

    return scenarios, conf_df


def time_of_day_analysis(results_df):
    """Analyze BAIL rate by time of day."""
    conf_df = results_df[results_df['conf'].isin(['✓', '✓★'])].copy()
    if conf_df.empty:
        return {}

    time_groups = {}
    for bucket in conf_df['time_bucket'].unique():
        subset = conf_df[conf_df['time_bucket'] == bucket]
        n = len(subset)
        bail_n = len(subset[subset['bail_current'] == 'BAIL'])
        hold_n = n - bail_n

        hold_pnl = subset[subset['bail_current'] == 'HOLD']['pnl_30m'].dropna().sum()
        bail_at_5m = subset[subset['bail_current'] == 'BAIL']['pnl_5m'].dropna().sum()
        bail_counterfactual = subset[subset['bail_current'] == 'BAIL']['pnl_30m'].dropna()

        time_groups[bucket] = {
            'n': n,
            'bail_n': bail_n,
            'hold_n': hold_n,
            'bail_rate': bail_n / n * 100 if n > 0 else 0,
            'hold_pnl_30m': hold_pnl,
            'bail_exit_pnl': bail_at_5m,
            'net_pnl': hold_pnl + bail_at_5m,
            'bail_would_win': (bail_counterfactual > 0).sum(),
            'bail_would_win_pct': (bail_counterfactual > 0).mean() * 100 if len(bail_counterfactual) > 0 else 0,
        }

    return time_groups


def alternative_check_timing(results_df):
    """What if we checked at 10m or 15m instead of 5m?"""
    conf_df = results_df[results_df['conf'].isin(['✓', '✓★'])].copy()
    if conf_df.empty:
        return {}

    timing_results = {}
    for check_min in [5, 10, 15]:
        col = f'pnl_{check_min}m'
        if col not in conf_df.columns:
            continue

        hold_mask = conf_df[col].apply(lambda x: x > 0.05 if not pd.isna(x) else False)
        hold = conf_df[hold_mask]
        bail = conf_df[~hold_mask]

        hold_pnl = hold['pnl_30m'].dropna().sum()
        bail_pnl = bail[col].dropna().sum()

        bail_counterfactual = bail['pnl_30m'].dropna()

        timing_results[f'{check_min}m check'] = {
            'n_hold': len(hold),
            'n_bail': len(bail),
            'hold_pct': len(hold) / len(conf_df) * 100,
            'hold_pnl_30m': hold_pnl,
            'bail_exit_pnl': bail_pnl,
            'net_pnl': hold_pnl + bail_pnl,
            'bail_would_win': (bail_counterfactual > 0).sum(),
            'bail_would_win_pct': (bail_counterfactual > 0).mean() * 100 if len(bail_counterfactual) > 0 else 0,
        }

    return timing_results


def ema_aligned_bail(results_df):
    """Analyze BAIL separately for EMA-aligned vs non-aligned signals."""
    conf_df = results_df[results_df['conf'].isin(['✓', '✓★'])].copy()
    if conf_df.empty:
        return {}

    ema_groups = {}
    for ema_val in ['bull', 'bear', 'mixed']:
        subset = conf_df[conf_df['ema'] == ema_val]
        if subset.empty:
            continue

        # EMA aligned = bull direction + bull ema, or bear direction + bear ema
        aligned = subset[
            ((subset['direction'] == 'bull') & (subset['ema'] == 'bull')) |
            ((subset['direction'] == 'bear') & (subset['ema'] == 'bear'))
        ]
        not_aligned = subset[~subset.index.isin(aligned.index)]

        for label, group in [('aligned', aligned), ('not_aligned', not_aligned)]:
            if group.empty:
                continue
            bail_n = len(group[group['bail_current'] == 'BAIL'])
            hold_n = len(group) - bail_n

            hold_pnl = group[group['bail_current'] == 'HOLD']['pnl_30m'].dropna().sum()
            bail_pnl = group[group['bail_current'] == 'BAIL']['pnl_5m'].dropna().sum()
            bail_cf = group[group['bail_current'] == 'BAIL']['pnl_30m'].dropna()

            ema_groups[f'{ema_val}_{label}'] = {
                'n': len(group),
                'bail_n': bail_n,
                'hold_n': hold_n,
                'bail_rate': bail_n / len(group) * 100,
                'net_pnl': hold_pnl + bail_pnl,
                'bail_would_win': (bail_cf > 0).sum(),
                'bail_would_win_pct': (bail_cf > 0).mean() * 100 if len(bail_cf) > 0 else 0,
            }

    # Simpler: just EMA aligned (direction matches EMA) vs not
    conf_df['ema_aligned'] = (
        ((conf_df['direction'] == 'bull') & (conf_df['ema'] == 'bull')) |
        ((conf_df['direction'] == 'bear') & (conf_df['ema'] == 'bear'))
    )

    for label, group in [('EMA Aligned', conf_df[conf_df['ema_aligned']]),
                          ('Not EMA Aligned', conf_df[~conf_df['ema_aligned']])]:
        if group.empty:
            continue
        bail_n = len(group[group['bail_current'] == 'BAIL'])
        hold_n = len(group) - bail_n

        hold_pnl = group[group['bail_current'] == 'HOLD']['pnl_30m'].dropna().sum()
        bail_exit = group[group['bail_current'] == 'BAIL']['pnl_5m'].dropna().sum()
        bail_cf = group[group['bail_current'] == 'BAIL']['pnl_30m'].dropna()

        ema_groups[label] = {
            'n': len(group),
            'bail_n': bail_n,
            'hold_n': hold_n,
            'bail_rate': bail_n / len(group) * 100,
            'hold_pnl': hold_pnl,
            'bail_exit_pnl': bail_exit,
            'net_pnl': hold_pnl + bail_exit,
            'bail_would_win': (bail_cf > 0).sum(),
            'bail_would_win_pct': (bail_cf > 0).mean() * 100 if len(bail_cf) > 0 else 0,
        }

    return ema_groups


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════
def main():
    print("=" * 70)
    print("v30b BAIL Investigation")
    print("=" * 70)

    # Load data
    signals = load_signals()
    print(f"\nLoaded {len(signals)} signals ({signals['conf_pass'].sum()} CONF pass)")

    spy_daily = load_spy_daily()
    day_classes = classify_trending_days(spy_daily, None)

    # Simulate BAIL for all signals (including non-confirmed for comparison)
    print("\nSimulating BAIL checks using IB 1m data...")
    results = simulate_bail(signals, threshold_atr=0.05, check_minutes=5)
    print(f"Matched {len(results)} signals to IB data")

    # ── Q1: Current BAIL threshold analysis ────────────────────────
    print("\n" + "─" * 70)
    print("Q1: Current BAIL Threshold (pnl > 0.05 ATR at 5m)")
    print("─" * 70)

    conf_results = results[results['conf'].isin(['✓', '✓★'])]
    all_results = results.copy()

    bail_count = len(conf_results[conf_results['bail_current'] == 'BAIL'])
    hold_count = len(conf_results[conf_results['bail_current'] == 'HOLD'])
    total = bail_count + hold_count

    print(f"  Confirmed signals matched: {total}")
    print(f"  HOLD: {hold_count} ({hold_count/total*100:.1f}%)")
    print(f"  BAIL: {bail_count} ({bail_count/total*100:.1f}%)")

    # HOLD performance
    hold_df = conf_results[conf_results['bail_current'] == 'HOLD']
    bail_df = conf_results[conf_results['bail_current'] == 'BAIL']

    print(f"\n  HOLD signals — PnL at 30m:")
    h30 = hold_df['pnl_30m'].dropna()
    print(f"    N={len(h30)}, avg={h30.mean():.3f} ATR, sum={h30.sum():.1f} ATR")
    print(f"    Win rate: {(h30 > 0).mean()*100:.1f}%")
    print(f"    Avg MFE (30m): {hold_df['mfe_30m'].dropna().mean():.3f} ATR")

    print(f"\n  BAIL signals — what happened after:")
    b30 = bail_df['pnl_30m'].dropna()
    b5 = bail_df['pnl_5m'].dropna()
    print(f"    N={len(b30)}")
    print(f"    PnL at exit (5m): avg={b5.mean():.3f} ATR, sum={b5.sum():.1f} ATR")
    print(f"    PnL at 30m (counterfactual): avg={b30.mean():.3f} ATR, sum={b30.sum():.1f} ATR")
    print(f"    Would have been profitable at 30m: {(b30 > 0).sum()} / {len(b30)} ({(b30 > 0).mean()*100:.1f}%)")
    print(f"    Would have been profitable at 60m: {(bail_df['pnl_60m'].dropna() > 0).sum()} / {len(bail_df['pnl_60m'].dropna())}")

    # Net comparison
    hold_pnl = h30.sum()
    bail_exit_pnl = b5.sum()
    no_bail_pnl = conf_results['pnl_30m'].dropna().sum()

    print(f"\n  Net PnL comparison:")
    print(f"    With current BAIL: {hold_pnl + bail_exit_pnl:.1f} ATR (HOLD at 30m + BAIL at 5m)")
    print(f"    Without BAIL (hold all): {no_bail_pnl:.1f} ATR")
    print(f"    BAIL value-add: {(hold_pnl + bail_exit_pnl) - no_bail_pnl:.1f} ATR")

    # ── Q2: Threshold sweep ────────────────────────────────────────
    print("\n" + "─" * 70)
    print("Q2: Threshold Optimization Sweep")
    print("─" * 70)

    sweep = compute_threshold_sweep(results)
    print(f"\n  {'Threshold':>10} {'HOLD%':>7} {'BAIL%':>7} {'Net PnL':>10} {'No-BAIL':>10} {'Value Add':>10} {'BAIL→Win%':>10}")
    for _, row in sweep.iterrows():
        print(f"  {row['threshold']:>10.2f} {row['hold_pct']:>6.1f}% {row['bail_pct']:>6.1f}% "
              f"{row['net_pnl_with_bail']:>9.1f} {row['net_pnl_no_bail']:>9.1f} "
              f"{row['bail_value_add']:>9.1f} {row['bail_would_win_pct']:>9.1f}%")

    # ── Q3: Trending day analysis ──────────────────────────────────
    print("\n" + "─" * 70)
    print("Q3: Trending vs Choppy Day Analysis")
    print("─" * 70)

    day_classes = classify_trending_days(spy_daily, results)
    conf_results_copy = conf_results.copy()
    conf_results_copy['day_type'] = conf_results_copy['date'].map(
        lambda d: day_classes.get(d, {}).get('day_type', 'unknown'))
    conf_results_copy['trend_dir'] = conf_results_copy['date'].map(
        lambda d: day_classes.get(d, {}).get('trend_dir', 'unknown'))
    conf_results_copy['spy_return'] = conf_results_copy['date'].map(
        lambda d: day_classes.get(d, {}).get('spy_return', 0))

    for dtype in ['trending_up', 'trending_down', 'choppy', 'mixed']:
        subset = conf_results_copy[conf_results_copy['day_type'] == dtype]
        if subset.empty:
            continue
        bail_n = len(subset[subset['bail_current'] == 'BAIL'])
        hold_n = len(subset) - bail_n

        hold_pnl = subset[subset['bail_current'] == 'HOLD']['pnl_30m'].dropna().sum()
        bail_exit = subset[subset['bail_current'] == 'BAIL']['pnl_5m'].dropna().sum()
        bail_cf = subset[subset['bail_current'] == 'BAIL']['pnl_30m'].dropna()

        print(f"\n  {dtype.upper()} days (N={len(subset)}):")
        print(f"    BAIL rate: {bail_n}/{len(subset)} ({bail_n/len(subset)*100:.1f}%)")
        print(f"    Net PnL with BAIL: {hold_pnl + bail_exit:.1f} ATR")
        print(f"    BAILed → would win at 30m: {(bail_cf > 0).sum()}/{len(bail_cf)} ({(bail_cf > 0).mean()*100:.1f}%)" if len(bail_cf) > 0 else "    No BAILs")

        # With-trend signals on trending days
        if 'trending' in dtype:
            trend = 'bull' if 'up' in dtype else 'bear'
            with_trend = subset[subset['direction'] == trend]
            if not with_trend.empty:
                wt_bail = len(with_trend[with_trend['bail_current'] == 'BAIL'])
                wt_bail_cf = with_trend[with_trend['bail_current'] == 'BAIL']['pnl_30m'].dropna()
                print(f"    WITH-TREND signals: {len(with_trend)}, BAIL rate: {wt_bail/len(with_trend)*100:.1f}%")
                if len(wt_bail_cf) > 0:
                    print(f"      BAILed with-trend → would win: {(wt_bail_cf > 0).sum()}/{len(wt_bail_cf)} ({(wt_bail_cf > 0).mean()*100:.1f}%)")
                    print(f"      Counterfactual avg PnL: {wt_bail_cf.mean():.3f} ATR")

    # ── Q4: Direction-aware BAIL ───────────────────────────────────
    print("\n" + "─" * 70)
    print("Q4: Direction-Aware BAIL Scenarios")
    print("─" * 70)

    scenarios, conf_with_trend = direction_aware_bail(results, day_classes)

    print(f"\n  {'Scenario':<30} {'HOLD':>6} {'BAIL':>6} {'Net PnL':>10} {'Trend PnL':>10} {'Chop PnL':>10}")
    for name, data in scenarios.items():
        print(f"  {name:<30} {data['n_hold']:>6} {data['n_bail']:>6} "
              f"{data['net_pnl']:>9.1f} {data['trending_net']:>9.1f} {data['choppy_net']:>9.1f}")

    # ── Q5: Time-of-day analysis ──────────────────────────────────
    print("\n" + "─" * 70)
    print("Q5: Time-of-Day BAIL Analysis")
    print("─" * 70)

    tod = time_of_day_analysis(results)

    # Sort by time bucket
    time_order = ['9:30-10:00', '10:00-10:30', '10:30-11:00', '11:00-12:00',
                  '12:00-13:00', '13:00-14:00', '14:00-15:00', '15:00-16:00']

    print(f"\n  {'Time':>15} {'N':>5} {'BAIL%':>7} {'Net PnL':>10} {'BAIL→Win%':>10}")
    for t in time_order:
        if t in tod:
            d = tod[t]
            print(f"  {t:>15} {d['n']:>5} {d['bail_rate']:>6.1f}% {d['net_pnl']:>9.1f} {d['bail_would_win_pct']:>9.1f}%")

    # ── Q6: EMA-aligned analysis ──────────────────────────────────
    print("\n" + "─" * 70)
    print("Q6: EMA Alignment and BAIL")
    print("─" * 70)

    ema_analysis = ema_aligned_bail(results)

    for label in ['EMA Aligned', 'Not EMA Aligned']:
        if label in ema_analysis:
            d = ema_analysis[label]
            print(f"\n  {label}:")
            print(f"    N={d['n']}, BAIL rate: {d['bail_rate']:.1f}%")
            print(f"    Net PnL: {d['net_pnl']:.1f} ATR (HOLD: {d['hold_pnl']:.1f}, BAIL exit: {d['bail_exit_pnl']:.1f})")
            print(f"    BAILed → would win: {d['bail_would_win']} ({d['bail_would_win_pct']:.1f}%)")

    # ── Q7: Alternative check timing ──────────────────────────────
    print("\n" + "─" * 70)
    print("Q7: Alternative Check Timing (5m vs 10m vs 15m)")
    print("─" * 70)

    timing = alternative_check_timing(results)

    print(f"\n  {'Check At':>10} {'HOLD':>6} {'BAIL':>6} {'HOLD%':>7} {'Net PnL':>10} {'BAIL→Win%':>10}")
    for name, d in timing.items():
        print(f"  {name:>10} {d['n_hold']:>6} {d['n_bail']:>6} {d['hold_pct']:>6.1f}% "
              f"{d['net_pnl']:>9.1f} {d['bail_would_win_pct']:>9.1f}%")

    # ── Summary statistics for report ─────────────────────────────
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    # Best threshold from sweep
    best = sweep.loc[sweep['net_pnl_with_bail'].idxmax()]
    print(f"\n  Best threshold: {best['threshold']:.2f} ATR → {best['net_pnl_with_bail']:.1f} ATR net")
    print(f"  Current (0.05): {sweep[sweep['threshold']==0.05]['net_pnl_with_bail'].iloc[0]:.1f} ATR")
    print(f"  No BAIL at all: {sweep['net_pnl_no_bail'].iloc[0]:.1f} ATR")

    # Return everything for report generation
    return {
        'results': results,
        'conf_results': conf_results,
        'sweep': sweep,
        'day_classes': day_classes,
        'scenarios': scenarios,
        'tod': tod,
        'ema_analysis': ema_analysis,
        'timing': timing,
    }


def generate_report(data):
    """Generate comprehensive markdown report."""
    results = data['results']
    conf = data['conf_results']
    sweep = data['sweep']
    scenarios = data['scenarios']
    tod = data['tod']
    ema_analysis = data['ema_analysis']
    timing = data['timing']
    day_classes = data['day_classes']

    hold_df = conf[conf['bail_current'] == 'HOLD']
    bail_df = conf[conf['bail_current'] == 'BAIL']

    h30 = hold_df['pnl_30m'].dropna()
    b30 = bail_df['pnl_30m'].dropna()
    b5 = bail_df['pnl_5m'].dropna()

    no_bail_pnl = conf['pnl_30m'].dropna().sum()
    with_bail_pnl = h30.sum() + b5.sum()

    best_row = sweep.loc[sweep['net_pnl_with_bail'].idxmax()]

    # ── Build report ──────────────────────────────────────────────
    lines = []
    lines.append("# v3.0b BAIL Investigation — Is the 5-Minute Check Too Aggressive?")
    lines.append(f"\n**Date:** 2026-03-06")
    lines.append(f"**Data:** {len(conf)} confirmed signals matched to IB 1m data (from {len(results)} total)")
    lines.append(f"**Period:** {results['date'].min()} to {results['date'].max()}")
    lines.append("")

    # ── Executive Summary ──────────────────────────────────────────
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"The current BAIL threshold (**pnl > 0.05 ATR at 5m**) exits **{len(bail_df)}/{len(conf)}** "
                 f"({len(bail_df)/len(conf)*100:.0f}%) of confirmed signals.")
    lines.append(f"Of those BAILed signals, **{(b30 > 0).sum()}/{len(b30)}** ({(b30 > 0).mean()*100:.0f}%) "
                 f"would have been profitable at 30 minutes.")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Net PnL with current BAIL | **{with_bail_pnl:.1f} ATR** |")
    lines.append(f"| Net PnL without any BAIL | **{no_bail_pnl:.1f} ATR** |")
    lines.append(f"| BAIL value-add | **{with_bail_pnl - no_bail_pnl:.1f} ATR** |")
    lines.append(f"| Best threshold found | **{best_row['threshold']:.2f} ATR** → {best_row['net_pnl_with_bail']:.1f} ATR |")
    lines.append("")

    verdict = ""
    if with_bail_pnl > no_bail_pnl:
        verdict = "BAIL is net positive — it saves more on losers than it loses on false exits."
    else:
        verdict = "BAIL is net negative — it cuts too many winners. The threshold needs adjustment."
    lines.append(f"**Verdict:** {verdict}")
    lines.append("")

    # ── Section 1: Current Mechanics ───────────────────────────────
    lines.append("## 1. Current BAIL Mechanics (Pine Code)")
    lines.append("")
    lines.append("```")
    lines.append("Threshold: pnl > 0.05 ATR")
    lines.append("Timing: 1 signal bar after CONF pass (~5 min on 5m TF)")
    lines.append("PnL calc: (close - entry) / dailyATR for bulls, inverse for bears")
    lines.append("HOLD: pnl > 0.05 → add '5m✓' to label")
    lines.append("BAIL: pnl <= 0.05 → add '5m✗' to label")
    lines.append("```")
    lines.append("")

    # ── Section 2: HOLD vs BAIL Performance ────────────────────────
    lines.append("## 2. HOLD vs BAIL Performance")
    lines.append("")
    lines.append("### HOLD Signals")
    lines.append(f"- **N = {len(h30)}**, avg PnL at 30m: **{h30.mean():.3f} ATR**")
    lines.append(f"- Total PnL: **{h30.sum():.1f} ATR**")
    lines.append(f"- Win rate (30m): **{(h30 > 0).mean()*100:.1f}%**")
    lines.append(f"- Avg MFE (30m): **{hold_df['mfe_30m'].dropna().mean():.3f} ATR**")
    lines.append("")

    lines.append("### BAIL Signals (Counterfactual)")
    lines.append(f"- **N = {len(b30)}**")
    lines.append(f"- PnL at exit (5m): avg **{b5.mean():.3f} ATR**, total **{b5.sum():.1f} ATR**")
    lines.append(f"- If held to 30m: avg **{b30.mean():.3f} ATR**, total **{b30.sum():.1f} ATR**")
    lines.append(f"- Would have won at 30m: **{(b30 > 0).sum()}/{len(b30)} ({(b30 > 0).mean()*100:.1f}%)**")

    bail_60 = bail_df['pnl_60m'].dropna()
    if len(bail_60) > 0:
        lines.append(f"- Would have won at 60m: **{(bail_60 > 0).sum()}/{len(bail_60)} ({(bail_60 > 0).mean()*100:.1f}%)**")

    bail_day = bail_df['mfe_day'].dropna()
    if len(bail_day) > 0:
        lines.append(f"- MFE rest-of-day: avg **{bail_day.mean():.3f} ATR** (the move was there)")
    lines.append("")

    # ── Section 3: Threshold Sweep ─────────────────────────────────
    lines.append("## 3. Threshold Optimization")
    lines.append("")
    lines.append("| Threshold | HOLD% | BAIL% | Net PnL | No-BAIL PnL | Value Add | BAIL→Win% |")
    lines.append("|-----------|-------|-------|---------|-------------|-----------|-----------|")
    for _, row in sweep.iterrows():
        marker = " **" if row['threshold'] == best_row['threshold'] else ""
        marker2 = "**" if row['threshold'] == best_row['threshold'] else ""
        current = " ← current" if row['threshold'] == 0.05 else ""
        lines.append(f"| {marker}{row['threshold']:.2f}{marker2}{current} | {row['hold_pct']:.0f}% | {row['bail_pct']:.0f}% | "
                     f"{row['net_pnl_with_bail']:.1f} | {row['net_pnl_no_bail']:.1f} | "
                     f"{row['bail_value_add']:.1f} | {row['bail_would_win_pct']:.0f}% |")
    lines.append("")

    # ── Section 4: Trending Days ───────────────────────────────────
    lines.append("## 4. Trending vs Choppy Days")
    lines.append("")

    conf_copy = conf.copy()
    conf_copy['day_type'] = conf_copy['date'].map(
        lambda d: day_classes.get(d, {}).get('day_type', 'unknown'))
    conf_copy['trend_dir'] = conf_copy['date'].map(
        lambda d: day_classes.get(d, {}).get('trend_dir', 'unknown'))

    for dtype in ['trending_up', 'trending_down', 'choppy', 'mixed']:
        subset = conf_copy[conf_copy['day_type'] == dtype]
        if subset.empty:
            continue
        bail_n = len(subset[subset['bail_current'] == 'BAIL'])
        hold_n = len(subset) - bail_n

        hold_pnl = subset[subset['bail_current'] == 'HOLD']['pnl_30m'].dropna().sum()
        bail_exit = subset[subset['bail_current'] == 'BAIL']['pnl_5m'].dropna().sum()
        bail_cf = subset[subset['bail_current'] == 'BAIL']['pnl_30m'].dropna()

        lines.append(f"### {dtype.replace('_', ' ').title()} (N={len(subset)})")
        lines.append(f"- BAIL rate: **{bail_n/len(subset)*100:.0f}%** ({bail_n}/{len(subset)})")
        lines.append(f"- Net PnL with BAIL: **{hold_pnl + bail_exit:.1f} ATR**")
        if len(bail_cf) > 0:
            lines.append(f"- BAILed → would win at 30m: **{(bail_cf > 0).sum()}/{len(bail_cf)} ({(bail_cf > 0).mean()*100:.0f}%)**")
            lines.append(f"- BAILed counterfactual PnL: **{bail_cf.sum():.1f} ATR**")

        # With-trend breakdown
        if 'trending' in dtype:
            trend = 'bull' if 'up' in dtype else 'bear'
            wt = subset[subset['direction'] == trend]
            if not wt.empty:
                wt_bail = len(wt[wt['bail_current'] == 'BAIL'])
                wt_bail_cf = wt[wt['bail_current'] == 'BAIL']['pnl_30m'].dropna()
                lines.append(f"- **With-trend signals:** {len(wt)}, BAIL rate {wt_bail/len(wt)*100:.0f}%")
                if len(wt_bail_cf) > 0:
                    lines.append(f"  - BAILed with-trend → would win: **{(wt_bail_cf > 0).sum()}/{len(wt_bail_cf)} ({(wt_bail_cf > 0).mean()*100:.0f}%)**")
                    lines.append(f"  - Counterfactual avg: **{wt_bail_cf.mean():.3f} ATR**")
        lines.append("")

    # ── Section 5: Direction-Aware BAIL ────────────────────────────
    lines.append("## 5. Direction-Aware BAIL Scenarios")
    lines.append("")
    lines.append("| Scenario | HOLD | BAIL | Net PnL | Trending PnL | Choppy PnL |")
    lines.append("|----------|------|------|---------|--------------|------------|")
    for name, d in scenarios.items():
        lines.append(f"| {name} | {d['n_hold']} | {d['n_bail']} | "
                     f"**{d['net_pnl']:.1f}** | {d['trending_net']:.1f} | {d['choppy_net']:.1f} |")
    lines.append("")

    # ── Section 6: Time-of-Day ─────────────────────────────────────
    lines.append("## 6. Time-of-Day Analysis")
    lines.append("")
    lines.append("| Time Bucket | N | BAIL% | Net PnL | BAIL→Win% |")
    lines.append("|-------------|---|-------|---------|-----------|")
    time_order = ['9:30-10:00', '10:00-10:30', '10:30-11:00', '11:00-12:00',
                  '12:00-13:00', '13:00-14:00', '14:00-15:00', '15:00-16:00']
    for t in time_order:
        if t in tod:
            d = tod[t]
            lines.append(f"| {t} | {d['n']} | {d['bail_rate']:.0f}% | {d['net_pnl']:.1f} | {d['bail_would_win_pct']:.0f}% |")
    lines.append("")

    # ── Section 7: EMA Alignment ──────────────────────────────────
    lines.append("## 7. EMA Alignment and BAIL")
    lines.append("")
    for label in ['EMA Aligned', 'Not EMA Aligned']:
        if label in ema_analysis:
            d = ema_analysis[label]
            lines.append(f"### {label} (N={d['n']})")
            lines.append(f"- BAIL rate: **{d['bail_rate']:.0f}%**")
            lines.append(f"- Net PnL: **{d['net_pnl']:.1f} ATR**")
            lines.append(f"- BAILed → would win: **{d['bail_would_win']} ({d['bail_would_win_pct']:.0f}%)**")
            lines.append("")

    # ── Section 8: Check Timing ───────────────────────────────────
    lines.append("## 8. Alternative Check Timing")
    lines.append("")
    lines.append("| Check At | HOLD | BAIL | HOLD% | Net PnL | BAIL→Win% |")
    lines.append("|----------|------|------|-------|---------|-----------|")
    for name, d in timing.items():
        lines.append(f"| {name} | {d['n_hold']} | {d['n_bail']} | {d['hold_pct']:.0f}% | "
                     f"**{d['net_pnl']:.1f}** | {d['bail_would_win_pct']:.0f}% |")
    lines.append("")

    # ── Recommendations ───────────────────────────────────────────
    lines.append("## Recommendations")
    lines.append("")

    # Determine best approach
    if best_row['threshold'] != 0.05:
        lines.append(f"### 1. Adjust Threshold to {best_row['threshold']:.2f} ATR")
        improvement = best_row['net_pnl_with_bail'] - sweep[sweep['threshold']==0.05]['net_pnl_with_bail'].iloc[0]
        lines.append(f"- Improvement: **+{improvement:.1f} ATR** over current threshold")
        lines.append(f"- HOLD rate goes from {sweep[sweep['threshold']==0.05]['hold_pct'].iloc[0]:.0f}% to {best_row['hold_pct']:.0f}%")
        lines.append("")

    # Check if direction-aware helps
    best_scenario = max(scenarios.items(), key=lambda x: x[1]['net_pnl'])
    current_scenario_pnl = scenarios.get('Current (0.05 all)', {}).get('net_pnl', 0)
    if best_scenario[1]['net_pnl'] > current_scenario_pnl:
        lines.append(f"### 2. Direction-Aware BAIL: {best_scenario[0]}")
        lines.append(f"- Net PnL: **{best_scenario[1]['net_pnl']:.1f} ATR** vs current {current_scenario_pnl:.1f} ATR")
        lines.append(f"- Improvement: **+{best_scenario[1]['net_pnl'] - current_scenario_pnl:.1f} ATR**")
        lines.append("")

    # Check timing
    best_timing = max(timing.items(), key=lambda x: x[1]['net_pnl'])
    current_timing_pnl = timing.get('5m check', {}).get('net_pnl', 0)
    if best_timing[1]['net_pnl'] > current_timing_pnl:
        lines.append(f"### 3. Check at {best_timing[0]} instead of 5m")
        lines.append(f"- Net PnL: **{best_timing[1]['net_pnl']:.1f} ATR** vs current {current_timing_pnl:.1f} ATR")
        lines.append("")

    # Final recommendation
    lines.append("### Bottom Line")
    lines.append("")

    if with_bail_pnl - no_bail_pnl > 5:
        lines.append("The BAIL system IS adding value overall. The concern about trending days is real "
                     "but the damage from keeping losers on choppy days outweighs the missed moves on trending days.")
    elif with_bail_pnl - no_bail_pnl > -5:
        lines.append("The BAIL system is roughly **break-even** — it saves about as much as it costs. "
                     "A threshold adjustment or direction-aware approach could tip it positive.")
    else:
        lines.append("The BAIL system is **net negative** — it's cutting too many winners. "
                     "The trending-day problem is REAL and significant. Recommended fix above.")

    lines.append("")

    report = "\n".join(lines)

    with open(OUTPUT_MD, 'w') as f:
        f.write(report)

    print(f"\nReport saved to: {OUTPUT_MD}")
    return report


if __name__ == "__main__":
    data = main()
    report = generate_report(data)
