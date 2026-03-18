"""
Candidate Symbol Screen for KLB (Key Level Breakout) System
Evaluates which symbols best respect key levels (PD High/Low/Close).
Uses IB 5-minute parquet data, last 60 trading days.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ── Config ──────────────────────────────────────────────────────────────────
DATA_DIR = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars/"
CANDIDATES = ["AVGO", "NFLX", "CRM", "COIN", "PLTR", "IWM", "JPM", "ARM", "SMCI", "LLY", "XLE"]
BENCHMARKS = ["AMZN", "QQQ", "SPY"]
ALL_SYMBOLS = CANDIDATES + BENCHMARKS
TRADING_DAYS = 60
TOUCH_PCT = 0.001       # 0.1% proximity = "touch"
FOLLOW_BARS = 6         # 30 min follow-through window on 5m
CLEAN_BODY_PCT = 0.30   # body > 30% of range = clean candle

# ── Helper: Load & filter to RTH ────────────────────────────────────────────
def load_rth(symbol: str) -> pd.DataFrame:
    """Load 5m parquet, convert to ET, filter to regular hours 9:30-16:00."""
    path = f"{DATA_DIR}{symbol.lower()}_5_mins_ib.parquet"
    df = pd.read_parquet(path)
    # Convert Berlin → US/Eastern
    df['date'] = df['date'].dt.tz_convert('US/Eastern')
    # Filter to RTH: 9:30 inclusive to 15:55 inclusive (last bar starting before 16:00)
    df['time'] = df['date'].dt.time
    from datetime import time as dtime
    df = df[(df['time'] >= dtime(9, 30)) & (df['time'] < dtime(16, 0))].copy()
    df['trade_date'] = df['date'].dt.date
    df.drop(columns=['time'], inplace=True)
    return df


def compute_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Compute daily OHLCV from 5m RTH bars."""
    daily = df.groupby('trade_date').agg(
        d_open=('open', 'first'),
        d_high=('high', 'max'),
        d_low=('low', 'min'),
        d_close=('close', 'last'),
        d_volume=('volume', 'sum')
    ).reset_index()
    daily.sort_values('trade_date', inplace=True)
    return daily


# ── Main analysis per symbol ─────────────────────────────────────────────────
def analyze_symbol(symbol: str) -> dict | None:
    try:
        df = load_rth(symbol)
    except Exception as e:
        print(f"  SKIP {symbol}: {e}")
        return None

    daily = compute_daily(df)
    # Limit to last N+1 trading days (need prior day for levels)
    if len(daily) < TRADING_DAYS + 1:
        print(f"  SKIP {symbol}: only {len(daily)} trading days")
        return None
    daily = daily.tail(TRADING_DAYS + 1).reset_index(drop=True)

    # Build key levels per day: PD High, PD Low, PD Close
    daily['pd_high'] = daily['d_high'].shift(1)
    daily['pd_low'] = daily['d_low'].shift(1)
    daily['pd_close'] = daily['d_close'].shift(1)
    # Drop first row (no prior day)
    daily = daily.iloc[1:].reset_index(drop=True)
    trade_dates = set(daily['trade_date'].tolist())

    # Filter 5m bars to these dates
    bars = df[df['trade_date'].isin(trade_dates)].copy()
    bars = bars.merge(daily[['trade_date', 'pd_high', 'pd_low', 'pd_close']], on='trade_date', how='left')

    # ── 1. Key Level Respect ──────────────────────────────────────────────
    touches = 0
    bounces = 0
    breaks = 0
    follow_through_atrs = []
    bounce_atrs = []

    # Daily ATR for normalization
    daily['d_range'] = daily['d_high'] - daily['d_low']
    daily['atr14'] = daily['d_range'].rolling(14, min_periods=5).mean()
    last_atr = daily['atr14'].iloc[-1]
    avg_atr = daily['atr14'].mean()
    avg_atr_pct = (daily['atr14'] / daily['d_close']).mean() * 100

    # Merge ATR into bars
    bars = bars.merge(daily[['trade_date', 'atr14']], on='trade_date', how='left')

    # Sort by date for forward-looking
    bars = bars.sort_values('date').reset_index(drop=True)

    for level_col in ['pd_high', 'pd_low', 'pd_close']:
        for i in range(len(bars)):
            row = bars.iloc[i]
            level = row[level_col]
            atr = row['atr14']
            if pd.isna(level) or pd.isna(atr) or atr == 0:
                continue

            threshold = level * TOUCH_PCT
            bar_low = row['low']
            bar_high = row['high']
            bar_close = row['close']
            bar_open = row['open']

            # Check if bar touches the level (price range includes level proximity)
            if bar_low - threshold <= level <= bar_high + threshold:
                touches += 1

                # Determine approach side: was price mostly above or below?
                mid = (bar_open + bar_close) / 2
                approached_from_above = mid > level

                # Did it break through? Close on opposite side of level
                if approached_from_above and bar_close < level - threshold:
                    broke_through = True
                elif not approached_from_above and bar_close > level + threshold:
                    broke_through = True
                else:
                    broke_through = False

                # Forward bars for follow-through measurement
                fwd = bars.iloc[i+1 : i+1+FOLLOW_BARS]
                if len(fwd) == 0:
                    continue
                # Only count same-day forward bars
                fwd = fwd[fwd['trade_date'] == row['trade_date']]
                if len(fwd) == 0:
                    continue

                if broke_through:
                    breaks += 1
                    # Follow-through: max excursion in break direction
                    if approached_from_above:  # broke down
                        excursion = level - fwd['low'].min()
                    else:  # broke up
                        excursion = fwd['high'].max() - level
                    follow_through_atrs.append(max(0, excursion) / atr)
                else:
                    bounces += 1
                    # Bounce quality: max excursion away from level
                    if approached_from_above:  # bounced up
                        excursion = fwd['high'].max() - level
                    else:  # bounced down
                        excursion = level - fwd['low'].min()
                    bounce_atrs.append(max(0, excursion) / atr)

    touch_rate = touches / len(bars) if len(bars) > 0 else 0
    bounce_rate = bounces / (bounces + breaks) if (bounces + breaks) > 0 else 0
    avg_follow_atr = np.mean(follow_through_atrs) if follow_through_atrs else 0
    avg_bounce_atr = np.mean(bounce_atrs) if bounce_atrs else 0

    # ── 2. Tradability Metrics ─────────────────────────────────────────────
    avg_daily_vol = daily['d_volume'].mean()
    # Spread proxy on 5m bars
    bars['spread_proxy'] = (bars['high'] - bars['low']) / bars['close']
    avg_spread = bars['spread_proxy'].mean() * 100  # as %
    # Clean candle ratio
    bars['body'] = (bars['close'] - bars['open']).abs()
    bars['range'] = bars['high'] - bars['low']
    bars['clean'] = (bars['body'] > CLEAN_BODY_PCT * bars['range']) & (bars['range'] > 0)
    clean_ratio = bars['clean'].mean() * 100

    # ── 3. SPY correlation ─────────────────────────────────────────────────
    # Will be filled in later with cross-symbol pass
    return {
        'symbol': symbol,
        'is_benchmark': symbol in BENCHMARKS,
        'touch_rate': touch_rate,
        'bounce_rate': bounce_rate * 100,
        'avg_follow_atr': avg_follow_atr,
        'avg_bounce_atr': avg_bounce_atr,
        'touches_per_day': touches / TRADING_DAYS,
        'atr14': last_atr,
        'atr_pct': avg_atr_pct,
        'avg_daily_vol': avg_daily_vol,
        'avg_spread_pct': avg_spread,
        'clean_candle_pct': clean_ratio,
        'daily_returns': daily.set_index('trade_date')['d_close'].pct_change().dropna()
    }


# ── Run all symbols ──────────────────────────────────────────────────────────
print("=" * 80)
print("KLB Candidate Symbol Screen — Last 60 Trading Days, 5m Bars")
print("=" * 80)
print()

results = []
for sym in ALL_SYMBOLS:
    print(f"  Analyzing {sym}...")
    r = analyze_symbol(sym)
    if r:
        results.append(r)

# ── SPY correlation ──────────────────────────────────────────────────────────
spy_ret = None
for r in results:
    if r['symbol'] == 'SPY':
        spy_ret = r['daily_returns']
        break

for r in results:
    if spy_ret is not None and r['symbol'] != 'SPY':
        # Align on common dates
        combined = pd.DataFrame({'sym': r['daily_returns'], 'spy': spy_ret}).dropna()
        r['spy_corr'] = combined['sym'].corr(combined['spy']) if len(combined) > 5 else np.nan
    else:
        r['spy_corr'] = 1.0 if r['symbol'] == 'SPY' else np.nan

# ── Composite Score ──────────────────────────────────────────────────────────
# Normalize each metric to 0-1 across the group, then weighted sum
df_res = pd.DataFrame([{k: v for k, v in r.items() if k != 'daily_returns'} for r in results])

def norm(series):
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(0.5, index=series.index)
    return (series - mn) / (mx - mn)

# Weights: bounce_rate 25%, follow_through 25%, ATR% 20%, volume 15%, spy_corr_inv 15%
df_res['n_bounce'] = norm(df_res['bounce_rate'])
df_res['n_follow'] = norm(df_res['avg_follow_atr'])
df_res['n_atr_pct'] = norm(df_res['atr_pct'])
df_res['n_volume'] = norm(np.log10(df_res['avg_daily_vol']))  # log scale
df_res['n_corr_inv'] = norm(1 - df_res['spy_corr'].fillna(1))  # lower corr = higher score

df_res['composite'] = (
    0.25 * df_res['n_bounce'] +
    0.25 * df_res['n_follow'] +
    0.20 * df_res['n_atr_pct'] +
    0.15 * df_res['n_volume'] +
    0.15 * df_res['n_corr_inv']
)

df_res = df_res.sort_values('composite', ascending=False).reset_index(drop=True)

# ── Print Results ────────────────────────────────────────────────────────────
print()
print("## KLB Candidate Screen Results")
print()
print(f"| Rank | Symbol | Type | Bounce% | Follow ATR | Bounce ATR | Touch/Day | ATR% | AvgDailyVol | Spread% | Clean% | SPY Corr | Score |")
print(f"|------|--------|------|---------|------------|------------|-----------|------|-------------|---------|--------|----------|-------|")

for i, row in df_res.iterrows():
    rank = i + 1
    typ = "BENCH" if row['is_benchmark'] else "CAND"
    vol_str = f"{row['avg_daily_vol']/1e6:.1f}M"
    print(f"| {rank:4d} | {row['symbol']:6s} | {typ:4s} | {row['bounce_rate']:6.1f}% | "
          f"{row['avg_follow_atr']:10.3f} | {row['avg_bounce_atr']:10.3f} | "
          f"{row['touches_per_day']:9.1f} | {row['atr_pct']:3.1f}% | "
          f"{vol_str:>11s} | {row['avg_spread_pct']:6.3f}% | {row['clean_candle_pct']:5.1f}% | "
          f"{row['spy_corr']:8.3f} | {row['composite']:.3f} |")

print()
print("---")
print()

# ── Tier recommendations ─────────────────────────────────────────────────────
print("## Tier Recommendations")
print()
bench_avg = df_res[df_res['is_benchmark']]['composite'].mean()
top_candidates = df_res[(~df_res['is_benchmark']) & (df_res['composite'] >= bench_avg)]
good_candidates = df_res[(~df_res['is_benchmark']) & (df_res['composite'] < bench_avg) & (df_res['composite'] >= bench_avg * 0.8)]
skip_candidates = df_res[(~df_res['is_benchmark']) & (df_res['composite'] < bench_avg * 0.8)]

print(f"Benchmark average composite: {bench_avg:.3f}")
print()
if len(top_candidates) > 0:
    print(f"**ADD (>= benchmark avg):** {', '.join(top_candidates['symbol'].tolist())}")
if len(good_candidates) > 0:
    print(f"**MAYBE (within 80%):** {', '.join(good_candidates['symbol'].tolist())}")
if len(skip_candidates) > 0:
    print(f"**SKIP (below 80%):** {', '.join(skip_candidates['symbol'].tolist())}")

print()
print("---")
print()

# ── Key insight summary ──────────────────────────────────────────────────────
print("## Key Insights")
print()
# Highest bounce rate
best_bounce = df_res.loc[df_res['bounce_rate'].idxmax()]
print(f"- **Best level respect (bounce rate):** {best_bounce['symbol']} at {best_bounce['bounce_rate']:.1f}%")
# Best follow-through
best_follow = df_res.loc[df_res['avg_follow_atr'].idxmax()]
print(f"- **Best breakout follow-through:** {best_follow['symbol']} at {best_follow['avg_follow_atr']:.3f} ATR")
# Most uncorrelated with SPY
best_div = df_res[df_res['symbol'] != 'SPY'].loc[df_res[df_res['symbol'] != 'SPY']['spy_corr'].idxmin()]
print(f"- **Most SPY-uncorrelated:** {best_div['symbol']} at r={best_div['spy_corr']:.3f}")
# Highest ATR%
best_vol = df_res.loc[df_res['atr_pct'].idxmax()]
print(f"- **Highest ATR% (most volatile):** {best_vol['symbol']} at {best_vol['atr_pct']:.1f}%")
# Most active at levels
best_touch = df_res.loc[df_res['touches_per_day'].idxmax()]
print(f"- **Most level interactions/day:** {best_touch['symbol']} at {best_touch['touches_per_day']:.1f}")
