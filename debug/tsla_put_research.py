"""
TSLA PUT Strategy Research on Weak Premarket (conf<=3) Days
All 6 tests: proxy conf, early entry, dip-bounce-turnaround, signal optimization, SL/TP, comparison
"""
import pandas as pd
import numpy as np
from datetime import time, timedelta
import warnings
warnings.filterwarnings('ignore')

BASE = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache"
TV_DEBUG = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug"

# ── Load data ──────────────────────────────────────────────────────────────
print("Loading data...")
tsla_5s = pd.read_parquet(f"{BASE}/bars_highres/5sec/tsla_5_secs_ib.parquet")
tsla_1m = pd.read_parquet(f"{BASE}/bars/tsla_1_min_ib.parquet")
tsla_1m['date'] = pd.to_datetime(tsla_1m['date'], utc=True).dt.tz_convert('US/Eastern')
tsla_1m = tsla_1m.set_index('date')
vix_d = pd.read_parquet(f"{BASE}/bars/vix_1_day_ib.parquet")
spy_1m = pd.read_parquet(f"{BASE}/bars/spy_1_min_ib.parquet")
spy_1m['date'] = pd.to_datetime(spy_1m['date'], utc=True).dt.tz_convert('US/Eastern')
spy_1m = spy_1m.set_index('date')
qqq_1m = pd.read_parquet(f"{BASE}/bars/qqq_1_min_ib.parquet")
qqq_1m['date'] = pd.to_datetime(qqq_1m['date'], utc=True).dt.tz_convert('US/Eastern')
qqq_1m = qqq_1m.set_index('date')

# 5sec already tz-aware
tsla_5s = tsla_5s.set_index('date')

# VIX: map to trading dates
vix_d['date'] = pd.to_datetime(vix_d['date'])
vix_d = vix_d.set_index('date')
vix_d.index = vix_d.index.normalize()

print(f"  TSLA 5sec: {len(tsla_5s)} bars, {tsla_5s.index.min().date()} to {tsla_5s.index.max().date()}")
print(f"  TSLA 1m: {len(tsla_1m)} bars, {tsla_1m.index.min().date()} to {tsla_1m.index.max().date()}")

# ── Parse pine logs for actual conf scores ─────────────────────────────────
print("\nParsing pine logs...")
pine_log = pd.read_csv(f"{TV_DEBUG}/pine-logs-TSLA Open Scalper v1.3b_72160.csv")
actual_conf = {}
for _, row in pine_log.iterrows():
    msg = row['Message']
    if 'PRE-SCAN' in msg:
        dt = pd.to_datetime(row['Date'])
        day = dt.date()
        import re
        m = re.search(r'conf=(\d)/5', msg)
        t = re.search(r'tier=(\S+)', msg)
        if m:
            actual_conf[day] = {
                'conf': int(m.group(1)),
                'tier': t.group(1) if t else '?',
                'msg': msg
            }

print(f"  Pine log days: {len(actual_conf)}")
for d in sorted(actual_conf.keys()):
    c = actual_conf[d]
    print(f"    {d}: conf={c['conf']} tier={c['tier']}")

# ── Build proxy conf for all 1m days ───────────────────────────────────────
print("\nBuilding proxy conf scores...")

# Get all TSLA trading dates from 1m data
tsla_dates = sorted(tsla_1m.index.normalize().unique())
# Convert to date objects for comparison
tsla_date_list = [d.date() for d in tsla_dates]

def get_bar1(df, day):
    """Get first bar of day"""
    try:
        day_data = df.loc[df.index.date == day]
        if len(day_data) == 0:
            return None
        return day_data.iloc[0]
    except:
        return None

def get_prev_close(df, day, date_list):
    """Get previous day's last bar close"""
    try:
        idx = date_list.index(day)
        if idx == 0:
            return None
        prev_day = date_list[idx - 1]
        prev_data = df.loc[df.index.date == prev_day]
        if len(prev_data) == 0:
            return None
        return prev_data.iloc[-1]['close']
    except:
        return None

def get_vix_prev_close(day):
    """Get VIX previous close"""
    try:
        # Find the most recent VIX data before this day
        vix_dates = vix_d.index[vix_d.index < pd.Timestamp(day)]
        if len(vix_dates) == 0:
            return None
        return vix_d.loc[vix_dates[-1], 'close']
    except:
        return None

proxy_scores = {}
for day in tsla_date_list:
    bar1 = get_bar1(tsla_1m, day)
    if bar1 is None:
        continue

    score = 0
    checks = {}

    # Check 1: PM position proxy = bar1 green (bullish open)
    bar1_red = bar1['close'] < bar1['open']
    if not bar1_red:  # green bar1 = bullish PM position
        score += 1
        checks['pm_pos'] = True
    else:
        checks['pm_pos'] = False

    # Check 2: PM acceleration - skip (no premarket data), give benefit of doubt = 0
    checks['pm_acc'] = False  # assume negative

    # Check 3: VIX sweet spot 18-25
    vix_close = get_vix_prev_close(day)
    if vix_close is not None and 18 <= vix_close <= 25:
        score += 1
        checks['vix'] = True
    else:
        checks['vix'] = False
    checks['vix_val'] = vix_close

    # Check 4: Triple alignment - SPY and QQQ bar1 green
    spy_bar1 = get_bar1(spy_1m, day)
    qqq_bar1 = get_bar1(qqq_1m, day)
    tsla_bar1_green = not bar1_red
    spy_green = spy_bar1 is not None and spy_bar1['close'] >= spy_bar1['open']
    qqq_green = qqq_bar1 is not None and qqq_bar1['close'] >= qqq_bar1['open']
    if tsla_bar1_green and spy_green and qqq_green:
        score += 1
        checks['align'] = True
    else:
        checks['align'] = False

    # Check 5: No gap danger (gap < 5% of price)
    prev_close = get_prev_close(tsla_1m, day, tsla_date_list)
    gap = None
    if prev_close is not None:
        gap = bar1['open'] - prev_close
        gap_pct = abs(gap) / prev_close * 100
        if gap_pct < 2.0:  # small gap = no danger
            score += 1
            checks['gap'] = True
        else:
            checks['gap'] = False
    else:
        checks['gap'] = True
        score += 1

    proxy_scores[day] = {
        'score': score,
        'bar1_red': bar1_red,
        'bar1_open': bar1['open'],
        'bar1_close': bar1['close'],
        'bar1_high': bar1['high'],
        'bar1_low': bar1['low'],
        'bar1_volume': bar1['volume'],
        'bar1_range': bar1['high'] - bar1['low'],
        'vix': vix_close,
        'gap': gap,
        'checks': checks,
    }

print(f"  Proxy scores computed for {len(proxy_scores)} days")

# ── Validate proxy against actual conf ─────────────────────────────────────
print("\n── PROXY VALIDATION ──")
print(f"{'Date':<12} {'Actual':>8} {'Proxy':>7} {'Match?':>7}")
matches = 0
total_overlap = 0
for day in sorted(actual_conf.keys()):
    if day in proxy_scores:
        total_overlap += 1
        ac = actual_conf[day]['conf']
        pc = proxy_scores[day]['score']
        # Match = both <=3 or both >=4
        cat_match = (ac <= 3 and pc <= 3) or (ac >= 4 and pc >= 4)
        if cat_match:
            matches += 1
        print(f"  {day}  conf={ac}  proxy={pc}  {'OK' if cat_match else 'MISS'}")

print(f"\n  Category match (<=3 vs >=4): {matches}/{total_overlap} = {matches/total_overlap*100:.0f}%")

# ── Classify all days ──────────────────────────────────────────────────────
conf_low_days = [d for d, s in proxy_scores.items() if s['score'] <= 3]
conf_high_days = [d for d, s in proxy_scores.items() if s['score'] >= 4]
all_days = list(proxy_scores.keys())

print(f"\n  conf<=3 (PUT candidates): {len(conf_low_days)} days")
print(f"  conf>=4 (CALL candidates): {len(conf_high_days)} days")

# ── Helper: measure short PnL at various horizons using 5sec data ──────────
def measure_short_pnl_5s(entry_price, entry_time, day_5s, horizons_sec=[30, 60, 120, 180, 300]):
    """Given entry price and time, measure PnL at various horizons. SHORT = profit when price drops."""
    results = {}
    for h in horizons_sec:
        target_time = entry_time + timedelta(seconds=h)
        future_bars = day_5s.loc[day_5s.index >= target_time]
        if len(future_bars) > 0:
            exit_price = future_bars.iloc[0]['close']
            pnl = entry_price - exit_price  # short PnL
            results[f'{h}s'] = pnl
        else:
            results[f'{h}s'] = np.nan

    # MFE/MAE within 5 minutes
    window = day_5s.loc[(day_5s.index >= entry_time) & (day_5s.index <= entry_time + timedelta(minutes=5))]
    if len(window) > 0:
        results['mfe_5m'] = entry_price - window['low'].min()  # max favorable (short)
        results['mae_5m'] = window['high'].max() - entry_price  # max adverse (short)
    else:
        results['mfe_5m'] = np.nan
        results['mae_5m'] = np.nan

    return results

# ── Get 5sec days ──────────────────────────────────────────────────────────
sec5_dates = sorted(set(tsla_5s.index.date))
print(f"\n  5sec coverage: {len(sec5_dates)} days ({min(sec5_dates)} to {max(sec5_dates)})")

# Days with both proxy and 5sec data
conf_low_5s = sorted(set(conf_low_days) & set(sec5_dates))
conf_high_5s = sorted(set(conf_high_days) & set(sec5_dates))
all_5s = sorted(set(all_days) & set(sec5_dates))
print(f"  conf<=3 days with 5sec data: {len(conf_low_5s)}")
print(f"  conf>=4 days with 5sec data: {len(conf_high_5s)}")

# ══════════════════════════════════════════════════════════════════════════
# TEST 1: 10-Second Entry on conf<=3 Days
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "="*80)
print("TEST 1: 10-Second Entry SHORT on conf<=3 Days (5sec data)")
print("="*80)

def test_fixed_entry(day_list, entry_offset_sec=10, label=""):
    """Short at 9:30:XX, measure outcomes"""
    results = []
    for day in day_list:
        day_5s = tsla_5s.loc[tsla_5s.index.date == day]
        if len(day_5s) == 0:
            continue

        # Find bar at 9:30:offset
        target = day_5s.index[0] + timedelta(seconds=entry_offset_sec)
        entry_bars = day_5s.loc[day_5s.index <= target]
        if len(entry_bars) == 0:
            continue

        entry_bar = entry_bars.iloc[-1]
        entry_price = entry_bar['close']
        entry_time = entry_bars.index[-1]

        pnl = measure_short_pnl_5s(entry_price, entry_time, day_5s)
        pnl['day'] = day
        pnl['entry_price'] = entry_price
        pnl['entry_time'] = entry_time
        pnl['bar1_red'] = proxy_scores.get(day, {}).get('bar1_red', None)
        results.append(pnl)

    if not results:
        print(f"  {label}: No data")
        return pd.DataFrame()

    df = pd.DataFrame(results)
    return df

def print_entry_stats(df, label):
    if len(df) == 0:
        print(f"  {label}: No data")
        return

    print(f"\n  {label} (N={len(df)}):")
    for col in ['30s', '60s', '120s', '180s', '300s']:
        if col in df.columns:
            vals = df[col].dropna()
            if len(vals) > 0:
                win_pct = (vals > 0).mean() * 100
                avg = vals.mean()
                std = vals.std()
                sharpe = avg / std * np.sqrt(252) if std > 0 else 0
                print(f"    {col:>5}: avg=${avg:+.2f}  win={win_pct:.0f}%  std=${std:.2f}  sharpe={sharpe:.2f}  N={len(vals)}")

    mfe = df['mfe_5m'].dropna()
    mae = df['mae_5m'].dropna()
    if len(mfe) > 0:
        print(f"    MFE 5m: avg=${mfe.mean():.2f}  med=${mfe.median():.2f}  max=${mfe.max():.2f}")
        print(f"    MAE 5m: avg=${mae.mean():.2f}  med=${mae.median():.2f}  max=${mae.max():.2f}")

# Test on conf<=3, conf>=4, and all days
df_low = test_fixed_entry(conf_low_5s, 10, "conf<=3")
df_high = test_fixed_entry(conf_high_5s, 10, "conf>=4")
df_all = test_fixed_entry(all_5s, 10, "all")

print_entry_stats(df_low, "conf<=3 @9:30:10 SHORT")
print_entry_stats(df_high, "conf>=4 @9:30:10 SHORT")
print_entry_stats(df_all, "ALL days @9:30:10 SHORT")

# ══════════════════════════════════════════════════════════════════════════
# TEST 2: Multiple Early Entry Times
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "="*80)
print("TEST 2: Multiple Entry Times on conf<=3 Days")
print("="*80)

entry_offsets = [5, 10, 15, 20, 30, 45, 60]
t2_results = []
for offset in entry_offsets:
    df = test_fixed_entry(conf_low_5s, offset)
    if len(df) > 0:
        for horizon in ['30s', '60s', '120s', '180s', '300s']:
            vals = df[horizon].dropna()
            if len(vals) > 0:
                t2_results.append({
                    'entry': f"9:30:{offset:02d}",
                    'hold': horizon,
                    'N': len(vals),
                    'avg_pnl': vals.mean(),
                    'win_pct': (vals > 0).mean() * 100,
                    'sharpe': vals.mean() / vals.std() * np.sqrt(252) if vals.std() > 0 else 0,
                })

t2_df = pd.DataFrame(t2_results)
print("\n  Entry Time x Hold Period (avg PnL):")
pivot = t2_df.pivot(index='entry', columns='hold', values='avg_pnl')
if len(pivot) > 0:
    # Reorder columns
    for col in ['30s', '60s', '120s', '180s', '300s']:
        if col in pivot.columns:
            pivot[col] = pivot[col].map(lambda x: f"${x:+.2f}" if pd.notna(x) else "")
    print(pivot.to_string())

print("\n  Entry Time x Hold Period (win %):")
pivot_w = t2_df.pivot(index='entry', columns='hold', values='win_pct')
if len(pivot_w) > 0:
    for col in ['30s', '60s', '120s', '180s', '300s']:
        if col in pivot_w.columns:
            pivot_w[col] = pivot_w[col].map(lambda x: f"{x:.0f}%" if pd.notna(x) else "")
    print(pivot_w.to_string())

# ══════════════════════════════════════════════════════════════════════════
# TEST 3: Dip-Bounce-Turnaround Entry
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "="*80)
print("TEST 3: Dip-Bounce-Turnaround Entry on conf<=3 Days")
print("="*80)

def test_dip_bounce_turnaround(day_list, bounce_pcts=[0.10, 0.15, 0.20, 0.25, 0.33, 0.50]):
    """
    After 9:30 open:
    1. Track running low
    2. When price bounces UP from low by X% of (open - low), that's the bounce
    3. When next bar closes below bounce bar's low, that's turnaround = ENTRY SHORT
    Entry window: 9:30:00 to 9:35:00
    """
    all_results = []

    for bounce_pct in bounce_pcts:
        entries = []
        for day in day_list:
            day_5s = tsla_5s.loc[tsla_5s.index.date == day].copy()
            if len(day_5s) < 10:
                continue

            open_price = day_5s.iloc[0]['open']
            window_end = day_5s.index[0] + timedelta(minutes=5)
            window = day_5s.loc[day_5s.index <= window_end]

            running_low = open_price
            bounce_bar_idx = None
            bounce_bar_low = None
            entry_found = False

            for i in range(1, len(window)):
                bar = window.iloc[i]
                bar_time = window.index[i]

                # Update running low
                if bar['low'] < running_low:
                    running_low = bar['low']
                    bounce_bar_idx = None  # reset bounce tracking
                    continue

                dip_size = open_price - running_low
                if dip_size <= 0:
                    continue  # no dip yet

                # Check if this bar is a bounce
                bounce_threshold = running_low + dip_size * bounce_pct
                if bar['close'] >= bounce_threshold and bounce_bar_idx is None:
                    bounce_bar_idx = i
                    bounce_bar_low = bar['low']
                    bounce_bar_high = bar['high']
                    continue

                # Check for turnaround: close below bounce bar's low
                if bounce_bar_idx is not None and bar['close'] < bounce_bar_low:
                    # ENTRY SHORT at this bar's close
                    entry_price = bar['close']
                    entry_time = bar_time

                    pnl = measure_short_pnl_5s(entry_price, entry_time, day_5s)
                    pnl['day'] = day
                    pnl['entry_price'] = entry_price
                    pnl['entry_time'] = entry_time
                    pnl['dip_size'] = dip_size
                    pnl['bounce_pct'] = bounce_pct
                    pnl['stop'] = bounce_bar_high  # stop above bounce high
                    pnl['stop_dist'] = bounce_bar_high - entry_price
                    pnl['entry_delay'] = (entry_time - day_5s.index[0]).total_seconds()
                    entries.append(pnl)
                    entry_found = True
                    break

                # If price makes new low after bounce, reset
                if bounce_bar_idx is not None and bar['low'] < running_low:
                    running_low = bar['low']
                    bounce_bar_idx = None

        if entries:
            df = pd.DataFrame(entries)
            for horizon in ['30s', '60s', '120s', '180s', '300s']:
                vals = df[horizon].dropna()
                if len(vals) > 0:
                    all_results.append({
                        'bounce_pct': f"{bounce_pct*100:.0f}%",
                        'hold': horizon,
                        'N': len(vals),
                        'avg_pnl': vals.mean(),
                        'win_pct': (vals > 0).mean() * 100,
                        'avg_entry_delay': df['entry_delay'].mean(),
                        'avg_stop_dist': df['stop_dist'].mean(),
                        'mfe': df['mfe_5m'].mean(),
                        'mae': df['mae_5m'].mean(),
                    })

    return pd.DataFrame(all_results)

t3_df = test_dip_bounce_turnaround(conf_low_5s)
if len(t3_df) > 0:
    print("\n  Bounce % x Hold Period:")
    for bp in t3_df['bounce_pct'].unique():
        sub = t3_df[t3_df['bounce_pct'] == bp]
        n = sub['N'].iloc[0]
        delay = sub['avg_entry_delay'].iloc[0]
        stop = sub['avg_stop_dist'].iloc[0]
        print(f"\n  Bounce={bp} (N={n}, avg entry delay={delay:.0f}s, avg stop=${stop:.2f}):")
        for _, row in sub.iterrows():
            print(f"    {row['hold']:>5}: avg=${row['avg_pnl']:+.2f}  win={row['win_pct']:.0f}%  MFE=${row['mfe']:.2f}  MAE=${row['mae']:.2f}")

# ══════════════════════════════════════════════════════════════════════════
# TEST 4: Signal Optimization on conf<=3 Days
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "="*80)
print("TEST 4: Signal Optimization on conf<=3 Days")
print("="*80)

# Use 10-second entry as baseline
df_low_full = test_fixed_entry(conf_low_5s, 10)
if len(df_low_full) > 0:
    # Add more features
    for i, row in df_low_full.iterrows():
        day = row['day']
        ps = proxy_scores.get(day, {})
        df_low_full.loc[i, 'vix'] = ps.get('vix', np.nan)
        df_low_full.loc[i, 'gap'] = ps.get('gap', np.nan)
        df_low_full.loc[i, 'bar1_range'] = ps.get('bar1_range', np.nan)
        df_low_full.loc[i, 'bar1_volume'] = ps.get('bar1_volume', np.nan)
        df_low_full.loc[i, 'bar1_open'] = ps.get('bar1_open', np.nan)
        df_low_full.loc[i, 'bar1_close_ps'] = ps.get('bar1_close', np.nan)

    # Also get first 5sec bar direction
    for i, row in df_low_full.iterrows():
        day = row['day']
        day_5s = tsla_5s.loc[tsla_5s.index.date == day]
        if len(day_5s) > 0:
            first_5s = day_5s.iloc[0]
            df_low_full.loc[i, 'first_5s_red'] = first_5s['close'] < first_5s['open']
            df_low_full.loc[i, 'first_10s_vol'] = day_5s.iloc[:2]['volume'].sum() if len(day_5s) >= 2 else np.nan

    # Use 60s horizon as primary metric
    horizon = '60s'

    def split_stats(mask, label):
        sub = df_low_full[mask][horizon].dropna()
        anti = df_low_full[~mask][horizon].dropna()
        if len(sub) >= 3:
            print(f"  {label}:")
            print(f"    YES: N={len(sub):>3}  avg=${sub.mean():+.2f}  win={100*(sub>0).mean():.0f}%  med=${sub.median():+.2f}")
            if len(anti) >= 3:
                print(f"    NO:  N={len(anti):>3}  avg=${anti.mean():+.2f}  win={100*(anti>0).mean():.0f}%  med=${anti.median():+.2f}")

    print(f"\n  Signal splits (horizon={horizon}):\n")

    # a) Volume burst (top 50% volume in first 10s)
    vol_med = df_low_full['first_10s_vol'].median()
    split_stats(df_low_full['first_10s_vol'] >= vol_med, "a) High vol first 10s (>=median)")

    # b) Bar1 range (top 50%)
    range_med = df_low_full['bar1_range'].median()
    split_stats(df_low_full['bar1_range'] >= range_med, "b) Wide bar1 (range>=median)")

    # c) Gap direction
    split_stats(df_low_full['gap'] < 0, "c) Gap DOWN")
    split_stats(df_low_full['gap'] > 0, "c) Gap UP")

    # d) VIX > 20
    split_stats(df_low_full['vix'] > 20, "d) VIX > 20")

    # e) Bar1 red vs green
    split_stats(df_low_full['bar1_red'] == True, "e) Bar1 RED")

    # f) First 5sec bar red
    split_stats(df_low_full['first_5s_red'] == True, "f) First 5sec RED")

# ══════════════════════════════════════════════════════════════════════════
# TEST 5: Stop Loss and Profit Target Optimization
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "="*80)
print("TEST 5: Stop Loss and Profit Target Optimization")
print("="*80)

def test_sl_tp(day_list, entry_offset_sec=10, stop_losses=[1, 1.5, 2, 3], profit_targets=[0.5, 1, 1.5, 2, 3]):
    """Test SL/TP combinations on short entries"""
    results = []

    for sl in stop_losses:
        for tp in profit_targets:
            trades = []
            for day in day_list:
                day_5s = tsla_5s.loc[tsla_5s.index.date == day]
                if len(day_5s) < 10:
                    continue

                # Entry at offset
                target = day_5s.index[0] + timedelta(seconds=entry_offset_sec)
                entry_bars = day_5s.loc[day_5s.index <= target]
                if len(entry_bars) == 0:
                    continue

                entry_price = entry_bars.iloc[-1]['close']
                entry_time = entry_bars.index[-1]

                # Walk forward max 5 minutes
                max_time = entry_time + timedelta(minutes=5)
                future = day_5s.loc[(day_5s.index > entry_time) & (day_5s.index <= max_time)]

                pnl = None
                for _, bar in future.iterrows():
                    # Check stop loss (price goes UP for short)
                    if bar['high'] >= entry_price + sl:
                        pnl = -sl
                        break
                    # Check profit target (price goes DOWN for short)
                    if bar['low'] <= entry_price - tp:
                        pnl = tp
                        break

                if pnl is None:
                    # Time exit at 5 min
                    if len(future) > 0:
                        pnl = entry_price - future.iloc[-1]['close']
                    else:
                        continue

                trades.append(pnl)

            if trades:
                trades_arr = np.array(trades)
                results.append({
                    'SL': f"${sl:.1f}",
                    'TP': f"${tp:.1f}",
                    'N': len(trades_arr),
                    'win_pct': (trades_arr > 0).mean() * 100,
                    'avg_pnl': trades_arr.mean(),
                    'total_pnl': trades_arr.sum(),
                    'sharpe': trades_arr.mean() / trades_arr.std() * np.sqrt(252) if trades_arr.std() > 0 else 0,
                    'expectancy': trades_arr.mean(),
                })

    return pd.DataFrame(results)

# Also test "above bar1 high" and "above 9:30 open" as stops
def test_dynamic_sl(day_list, entry_offset_sec=10, sl_type='bar1_high', profit_targets=[0.5, 1, 1.5, 2, 3]):
    results = []
    for tp in profit_targets:
        trades = []
        sl_dists = []
        for day in day_list:
            day_5s = tsla_5s.loc[tsla_5s.index.date == day]
            if len(day_5s) < 10:
                continue

            target = day_5s.index[0] + timedelta(seconds=entry_offset_sec)
            entry_bars = day_5s.loc[day_5s.index <= target]
            if len(entry_bars) == 0:
                continue

            entry_price = entry_bars.iloc[-1]['close']
            entry_time = entry_bars.index[-1]

            if sl_type == 'bar1_high':
                sl_level = day_5s.loc[day_5s.index <= day_5s.index[0] + timedelta(minutes=1), 'high'].max()
            else:  # open
                sl_level = day_5s.iloc[0]['open']

            sl_dist = sl_level - entry_price
            if sl_dist <= 0:
                sl_dist = 1.0  # minimum
                sl_level = entry_price + 1.0
            sl_dists.append(sl_dist)

            max_time = entry_time + timedelta(minutes=5)
            future = day_5s.loc[(day_5s.index > entry_time) & (day_5s.index <= max_time)]

            pnl = None
            for _, bar in future.iterrows():
                if bar['high'] >= sl_level:
                    pnl = -(sl_level - entry_price)
                    break
                if bar['low'] <= entry_price - tp:
                    pnl = tp
                    break

            if pnl is None:
                if len(future) > 0:
                    pnl = entry_price - future.iloc[-1]['close']
                else:
                    continue
            trades.append(pnl)

        if trades:
            trades_arr = np.array(trades)
            results.append({
                'SL': sl_type,
                'TP': f"${tp:.1f}",
                'N': len(trades_arr),
                'avg_sl_dist': np.mean(sl_dists),
                'win_pct': (trades_arr > 0).mean() * 100,
                'avg_pnl': trades_arr.mean(),
                'total_pnl': trades_arr.sum(),
            })
    return pd.DataFrame(results)

sl_tp_df = test_sl_tp(conf_low_5s)
if len(sl_tp_df) > 0:
    print("\n  Fixed SL x TP Grid (avg PnL):")
    pivot = sl_tp_df.pivot(index='SL', columns='TP', values='avg_pnl')
    pivot = pivot.map(lambda x: f"${x:+.2f}" if pd.notna(x) else "")
    print(pivot.to_string())

    print("\n  Fixed SL x TP Grid (win %):")
    pivot_w = sl_tp_df.pivot(index='SL', columns='TP', values='win_pct')
    pivot_w = pivot_w.map(lambda x: f"{x:.0f}%" if pd.notna(x) else "")
    print(pivot_w.to_string())

    print("\n  Fixed SL x TP Grid (total PnL):")
    pivot_t = sl_tp_df.pivot(index='SL', columns='TP', values='total_pnl')
    pivot_t = pivot_t.map(lambda x: f"${x:+.1f}" if pd.notna(x) else "")
    print(pivot_t.to_string())

    # Best combos
    print("\n  Top 5 SL/TP combos by avg PnL:")
    top = sl_tp_df.nlargest(5, 'avg_pnl')
    for _, row in top.iterrows():
        print(f"    SL={row['SL']} TP={row['TP']}: avg=${row['avg_pnl']:+.2f}  win={row['win_pct']:.0f}%  total=${row['total_pnl']:+.1f}  N={row['N']}")

# Dynamic SL
for sl_type in ['bar1_high', 'open']:
    dyn = test_dynamic_sl(conf_low_5s, sl_type=sl_type)
    if len(dyn) > 0:
        print(f"\n  Dynamic SL={sl_type}:")
        for _, row in dyn.iterrows():
            sl_d = f"(avg dist=${row['avg_sl_dist']:.2f})" if 'avg_sl_dist' in row else ""
            print(f"    TP={row['TP']}: avg=${row['avg_pnl']:+.2f}  win={row['win_pct']:.0f}%  total=${row['total_pnl']:+.1f}  {sl_d}")

# Trailing stop test
print("\n  Trailing Stop Test:")
def test_trailing_stop(day_list, entry_offset_sec=10, initial_sl=2.0, trail_trigger=1.0, trail_to=0.0):
    """After $1 profit, move stop to entry (breakeven)"""
    trades = []
    for day in day_list:
        day_5s = tsla_5s.loc[tsla_5s.index.date == day]
        if len(day_5s) < 10:
            continue
        target = day_5s.index[0] + timedelta(seconds=entry_offset_sec)
        entry_bars = day_5s.loc[day_5s.index <= target]
        if len(entry_bars) == 0:
            continue
        entry_price = entry_bars.iloc[-1]['close']
        entry_time = entry_bars.index[-1]

        max_time = entry_time + timedelta(minutes=5)
        future = day_5s.loc[(day_5s.index > entry_time) & (day_5s.index <= max_time)]

        current_sl = entry_price + initial_sl
        trail_activated = False
        pnl = None

        for _, bar in future.iterrows():
            short_pnl = entry_price - bar['low']

            # Check if trail trigger hit
            if not trail_activated and short_pnl >= trail_trigger:
                trail_activated = True
                current_sl = entry_price + trail_to  # move stop to entry

            # Check stop
            if bar['high'] >= current_sl:
                if trail_activated:
                    pnl = -(trail_to)  # breakeven or small loss
                else:
                    pnl = -initial_sl
                break

        if pnl is None:
            if len(future) > 0:
                pnl = entry_price - future.iloc[-1]['close']
            else:
                continue
        trades.append(pnl)

    if trades:
        trades_arr = np.array(trades)
        return {
            'N': len(trades_arr),
            'win_pct': (trades_arr > 0).mean() * 100,
            'avg_pnl': trades_arr.mean(),
            'total_pnl': trades_arr.sum(),
        }
    return None

for sl, trigger, trail in [(2, 1, 0), (2, 0.5, 0), (3, 1, 0), (1.5, 0.5, 0)]:
    r = test_trailing_stop(conf_low_5s, initial_sl=sl, trail_trigger=trigger, trail_to=trail)
    if r:
        print(f"    SL=${sl} trail@${trigger} to $0: N={r['N']}  avg=${r['avg_pnl']:+.2f}  win={r['win_pct']:.0f}%  total=${r['total_pnl']:+.1f}")

# ══════════════════════════════════════════════════════════════════════════
# TEST 6: Side-by-Side Comparison
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "="*80)
print("TEST 6: Side-by-Side Comparison")
print("="*80)

# CALL strategy stats from pine logs (existing indicator)
# Count wins/losses from pine log
call_wins = 0
call_losses = 0
call_pnls = []
for _, row in pine_log.iterrows():
    msg = row['Message']
    if 'EXIT TAKE_PROFIT' in msg or 'EXIT RUNNER' in msg:
        m = re.search(r'pnl=([-\d.]+)', msg)
        if m:
            pnl = float(m.group(1))
            call_pnls.append(pnl)
            if pnl > 0:
                call_wins += 1
            else:
                call_losses += 1
    elif 'SL HIT' in msg:
        m = re.search(r'loss=([-\d.]+)', msg)
        if m:
            call_losses += 1
            call_pnls.append(float(m.group(1)))
    elif 'ORB BEAR BREAK' in msg or 'ORB TIMEOUT' in msg:
        m = re.search(r'pnl=([-\d.]+)', msg)
        if m:
            pnl = float(m.group(1))
            if pnl <= 0:
                call_losses += 1
            call_pnls.append(pnl)

# PUT strategy - best from tests above
# Use the 10-second entry with best SL/TP combo
if len(df_low) > 0 and '60s' in df_low.columns:
    put_pnls = df_low['60s'].dropna().values

    print(f"\n  {'Metric':<25} {'CALL (pine log)':>18} {'PUT @9:30:10 60s':>18}")
    print(f"  {'─'*25} {'─'*18} {'─'*18}")

    call_arr = np.array(call_pnls) if call_pnls else np.array([0])
    put_arr = put_pnls

    print(f"  {'N trades':<25} {len(call_arr):>18} {len(put_arr):>18}")

    call_wr = (call_arr > 0).mean() * 100 if len(call_arr) > 0 else 0
    put_wr = (put_arr > 0).mean() * 100 if len(put_arr) > 0 else 0
    print(f"  {'Win %':<25} {call_wr:>17.0f}% {put_wr:>17.0f}%")

    print(f"  {'Avg PnL':<25} ${call_arr.mean():>16.2f} ${put_arr.mean():>16.2f}")
    print(f"  {'Total PnL':<25} ${call_arr.sum():>16.2f} ${put_arr.sum():>16.2f}")
    print(f"  {'Std Dev':<25} ${call_arr.std():>16.2f} ${put_arr.std():>16.2f}")

    if len(df_low) > 0:
        mfe = df_low['mfe_5m'].dropna()
        mae = df_low['mae_5m'].dropna()
        print(f"  {'Avg MFE (5m)':<25} {'n/a':>18} ${mfe.mean():>16.2f}")
        print(f"  {'Avg MAE (5m)':<25} {'n/a':>18} ${mae.mean():>16.2f}")

# ── Also run comparison with 1m data for larger sample ─────────────────
print("\n" + "="*80)
print("BONUS: 1m Bar Analysis (full dataset, larger N)")
print("="*80)

def test_1m_short(day_list, hold_bars=1):
    """Short at bar1 close (9:30), hold for N bars"""
    trades = []
    for day in day_list:
        day_1m = tsla_1m.loc[tsla_1m.index.date == day]
        if len(day_1m) < hold_bars + 1:
            continue
        entry = day_1m.iloc[0]['close']
        exit_price = day_1m.iloc[hold_bars]['close']
        pnl = entry - exit_price  # short

        # MFE/MAE
        window = day_1m.iloc[1:hold_bars+1]
        mfe = entry - window['low'].min()
        mae = window['high'].max() - entry

        trades.append({'pnl': pnl, 'mfe': mfe, 'mae': mae, 'day': day})
    return pd.DataFrame(trades)

print("\n  1m Short Entry at bar1 close (N = full dataset):")
for hold in [1, 2, 3, 5]:
    for label, days in [("conf<=3", conf_low_days), ("conf>=4", conf_high_days), ("ALL", all_days)]:
        df = test_1m_short(days, hold)
        if len(df) > 0:
            pnl = df['pnl']
            print(f"    {label:>8} hold={hold}m: N={len(df):>4}  avg=${pnl.mean():+.2f}  win={100*(pnl>0).mean():.0f}%  total=${pnl.sum():+.1f}  MFE=${df['mfe'].mean():.2f}  MAE=${df['mae'].mean():.2f}")

print("\n\n  conf<=3 day details (with proxy score):")
for day in sorted(conf_low_5s)[-20:]:
    ps = proxy_scores[day]
    day_5s = tsla_5s.loc[tsla_5s.index.date == day]
    if len(day_5s) == 0:
        continue
    open_p = day_5s.iloc[0]['open']
    # 1min close
    bar10 = day_5s.loc[day_5s.index <= day_5s.index[0] + timedelta(seconds=10)]
    if len(bar10) > 0:
        entry = bar10.iloc[-1]['close']
    else:
        continue
    # 60s close
    bar60 = day_5s.loc[day_5s.index <= day_5s.index[0] + timedelta(seconds=70)]
    if len(bar60) > 0:
        exit_60 = bar60.iloc[-1]['close']
        pnl_60 = entry - exit_60
    else:
        pnl_60 = 0

    print(f"    {day}  proxy={ps['score']}  open=${open_p:.2f}  bar1_red={ps['bar1_red']}  vix={ps.get('vix','?')}  gap=${ps.get('gap',0):.2f}  60s_pnl=${pnl_60:+.2f}")

print("\nDone.")
