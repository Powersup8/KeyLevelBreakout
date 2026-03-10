"""
Research: Bear KLB signals during SPY VWAP reclaim — factor discrimination
What separates winners from losers when a bear signal fires while SPY is above VWAP?
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

CACHE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars")
OUTPUT = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug/spy_vwap_reclaim_bear_results.txt")

SYMBOLS = ['AAPL', 'AMD', 'AMZN', 'GLD', 'GOOGL', 'META', 'MSFT', 'NFLX', 'NVDA', 'QQQ', 'SLV', 'TSLA', 'TSM', 'XLE']
NY_TZ = 'America/New_York'


def load_5m(symbol):
    path = CACHE / f"{symbol.lower()}_5_mins_ib.parquet"
    df = pd.read_parquet(path)
    df['date'] = pd.to_datetime(df['date'])
    if df['date'].dt.tz is None:
        df['date'] = df['date'].dt.tz_localize('UTC')
    df['date'] = df['date'].dt.tz_convert(NY_TZ)
    df = df.sort_values('date').reset_index(drop=True)
    return df


def load_daily(symbol):
    path = CACHE / f"{symbol.lower()}_1_day_ib.parquet"
    df = pd.read_parquet(path)
    df['date'] = pd.to_datetime(df['date'])
    if df['date'].dt.tz is None:
        df['date'] = df['date'].dt.tz_localize('UTC')
    df['date'] = df['date'].dt.tz_convert(NY_TZ)
    df = df.sort_values('date').reset_index(drop=True)
    return df


def compute_wilder_atr(daily_df):
    """Compute 14-period Wilder's ATR on daily bars, return as series indexed by date (prev day's ATR)."""
    df = daily_df.copy()
    df['prev_close'] = df['close'].shift(1)
    df['tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            abs(df['high'] - df['prev_close']),
            abs(df['low'] - df['prev_close'])
        )
    )
    # Wilder's smoothing: RMA = ewm with alpha=1/14
    df['atr14'] = df['tr'].ewm(alpha=1/14, adjust=False).mean()
    # Shift by 1: use previous day's ATR for the current day
    df['atr14_prev'] = df['atr14'].shift(1)
    # Normalize date to date-only for merging
    df['trade_date'] = df['date'].dt.date
    return df[['trade_date', 'atr14_prev', 'close']].rename(columns={'close': 'prev_close_daily'})


def compute_daily_vwap(df_5m):
    """Compute rolling intraday VWAP, reset each trading day."""
    df = df_5m.copy()
    df['trade_date'] = df['date'].dt.date
    df['typical'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp_vol'] = df['typical'] * df['volume']
    df['cum_tp_vol'] = df.groupby('trade_date')['tp_vol'].cumsum()
    df['cum_vol'] = df.groupby('trade_date')['volume'].cumsum()
    df['vwap'] = df['cum_tp_vol'] / df['cum_vol']
    return df


def compute_ema(series, span):
    return series.ewm(span=span, adjust=False).mean()


def filter_market_hours(df):
    """Filter to 9:30-16:00 ET."""
    t = df['date'].dt.time
    start = pd.Timestamp('09:30').time()
    end = pd.Timestamp('16:00').time()
    return df[(t >= start) & (t < end)].copy()


def build_spy_features(spy_5m):
    """Build SPY VWAP reclaim features on 5m data."""
    spy = filter_market_hours(spy_5m).copy()
    spy = compute_daily_vwap(spy)

    spy['spy_above_vwap'] = (spy['close'] > spy['vwap']).astype(int)

    # Count consecutive bars above VWAP
    above = spy['spy_above_vwap'].values
    consec = np.zeros(len(above), dtype=int)
    for i in range(len(above)):
        if above[i] == 1:
            consec[i] = (consec[i-1] + 1) if i > 0 else 1
        else:
            consec[i] = 0
    spy['spy_consec_above_vwap'] = consec

    # SPY session open pct change
    spy['spy_session_open'] = spy.groupby('trade_date')['open'].transform('first')
    spy['spy_pct_from_open'] = (spy['close'] - spy['spy_session_open']) / spy['spy_session_open'] * 100

    # Vol SMA20
    spy['spy_vol_sma20'] = spy['volume'].rolling(20, min_periods=5).mean()

    return spy[['date', 'close', 'vwap', 'spy_above_vwap', 'spy_consec_above_vwap',
                'spy_pct_from_open', 'trade_date']].copy()


def analyze_symbol(sym, spy_features, sym_daily_atr):
    """Build signals for one symbol and compute features + outcomes."""
    df = load_5m(sym)
    df = filter_market_hours(df)
    df = compute_daily_vwap(df)

    # EMA20
    df['ema20'] = compute_ema(df['close'], 20)
    df['ema20_5ago'] = df['ema20'].shift(5)

    # Vol SMA20
    df['vol_sma20'] = df['volume'].rolling(20, min_periods=5).mean()

    # Session open for pct change
    df['session_open'] = df.groupby('trade_date')['open'].transform('first')
    df['sym_pct_from_open'] = (df['close'] - df['session_open']) / df['session_open'] * 100

    # Today's session high up to this bar (for resistance proxy)
    df['session_high_sofar'] = df.groupby('trade_date')['high'].cummax()

    # Merge SPY features
    df = df.merge(spy_features, on='date', how='left', suffixes=('', '_spy'))

    # Merge daily ATR (prev day)
    df['trade_date_key'] = df['trade_date']  # date obj
    df = df.merge(sym_daily_atr.rename(columns={'trade_date': 'trade_date_key'}),
                  on='trade_date_key', how='left')

    # Only keep rows where we have ATR and SPY data
    df = df.dropna(subset=['atr14_prev', 'spy_consec_above_vwap', 'vwap'])
    df = df[df['atr14_prev'] > 0]

    # Signal conditions
    is_bear_bar = df['close'] < df['open']
    vol_ok = df['volume'] > df['vol_sma20'] * 1.0
    range_ok = (df['high'] - df['low']) >= 0.3 * df['atr14_prev']
    spy_reclaim = df['spy_consec_above_vwap'] >= 2

    signals = df[is_bear_bar & vol_ok & range_ok & spy_reclaim].copy()

    if len(signals) == 0:
        return pd.DataFrame()

    # Compute MFE bear: signal_close - min(low[t+1..t+6])
    # We need forward-looking min low over next 6 bars
    lows = df['low'].values
    dates = df['date'].values
    close_vals = df['close'].values

    # Build index map
    df_reset = df.reset_index(drop=True)

    # For each signal row, find next 6 bars in same day
    results = []
    for idx_in_signals, row in signals.iterrows():
        # Find position in df_reset
        pos_list = df_reset.index[df_reset['date'] == row['date']].tolist()
        if not pos_list:
            continue
        pos = pos_list[0]

        trade_date = row['trade_date']
        future_rows = df_reset.iloc[pos+1:pos+7]
        future_rows = future_rows[future_rows['trade_date'] == trade_date]

        if len(future_rows) == 0:
            continue

        min_low = future_rows['low'].min()
        mfe_bear = row['close'] - min_low
        mfe_bear_atr = mfe_bear / row['atr14_prev']

        # Features
        symbol_above_vwap = int(row['close'] > row['vwap'])
        symbol_ema_bear = int(row['ema20'] < row['ema20_5ago']) if pd.notna(row['ema20_5ago']) else 0

        hour = row['date'].hour
        minute = row['date'].minute
        total_min = hour * 60 + minute
        if total_min < 10 * 60 + 30:
            time_bucket = 'morning'
        elif total_min < 14 * 60:
            time_bucket = 'midday'
        else:
            time_bucket = 'afternoon'
        # Refine: morning = 9:30-10:30
        if total_min >= 9 * 60 + 30 and total_min < 10 * 60 + 30:
            time_bucket = 'morning'
        elif total_min >= 10 * 60 + 30 and total_min < 14 * 60:
            time_bucket = 'midday'
        else:
            time_bucket = 'afternoon'

        # Resistance nearby: session high so far or prev_close_daily within 0.3 ATR above close
        close = row['close']
        atr = row['atr14_prev']
        resistance_nearby = 0
        # Today's session high so far (if above close and within 0.3 ATR)
        if pd.notna(row['session_high_sofar']):
            sh = row['session_high_sofar']
            if close <= sh <= close + 0.3 * atr:
                resistance_nearby = 1
        # Yesterday's close
        if pd.notna(row['prev_close_daily']):
            pd_close = row['prev_close_daily']
            if close <= pd_close <= close + 0.3 * atr:
                resistance_nearby = 1

        spy_dur = row['spy_consec_above_vwap']
        spy_reclaim_bucket = 'just_reclaimed' if spy_dur <= 3 else 'held'

        # Symbol weaker than SPY (lower % change from open)
        sym_weaker = int(row['sym_pct_from_open'] < row['spy_pct_from_open']) if pd.notna(row['spy_pct_from_open']) else 0

        # Symbol VWAP distance in ATR
        vwap_dist_atr = (close - row['vwap']) / atr if atr > 0 else 0
        # Bucket: far below (<-0.3), near (-0.3 to 0), above (>0)
        if vwap_dist_atr < -0.3:
            vwap_bucket = 'far_below'
        elif vwap_dist_atr < 0:
            vwap_bucket = 'near_below'
        else:
            vwap_bucket = 'above'

        results.append({
            'symbol': sym,
            'date': row['date'],
            'trade_date': trade_date,
            'close': close,
            'atr': atr,
            'mfe_bear': mfe_bear,
            'mfe_bear_atr': mfe_bear_atr,
            'win': int(mfe_bear_atr > 0.15),
            'lose': int(mfe_bear_atr < 0.05),
            'symbol_above_vwap': symbol_above_vwap,
            'symbol_ema_bear': symbol_ema_bear,
            'time_bucket': time_bucket,
            'resistance_nearby': resistance_nearby,
            'spy_reclaim_bucket': spy_reclaim_bucket,
            'spy_reclaim_bars': spy_dur,
            'sym_weaker': sym_weaker,
            'vwap_dist_atr': vwap_dist_atr,
            'vwap_bucket': vwap_bucket,
        })

    return pd.DataFrame(results)


def factor_table(df, factor_col, label):
    """Compute win/loss rates by factor bucket."""
    grouped = df.groupby(factor_col).agg(
        N=('win', 'count'),
        wins=('win', 'sum'),
        losses=('lose', 'sum')
    ).reset_index()
    grouped['win_rate'] = grouped['wins'] / grouped['N'] * 100
    grouped['loss_rate'] = grouped['losses'] / grouped['N'] * 100
    baseline_win = df['win'].mean() * 100
    grouped['lift'] = grouped['win_rate'] / baseline_win
    grouped = grouped.sort_values('win_rate', ascending=False)
    return grouped, baseline_win


def main():
    lines = []

    def p(s=''):
        print(s)
        lines.append(str(s))

    p("=" * 70)
    p("BEAR KLB SIGNALS DURING SPY VWAP RECLAIM — FACTOR ANALYSIS")
    p("=" * 70)

    # Load SPY
    p("\nLoading SPY data...")
    spy_5m = load_5m('SPY')
    spy_features = build_spy_features(spy_5m)
    p(f"  SPY 5m bars: {len(spy_5m):,} | market hours: {len(spy_features):,}")

    # Load SPY daily for date range reference
    spy_daily = load_daily('SPY')
    spy_daily_atr = compute_wilder_atr(spy_daily)

    # Collect signals from all symbols
    all_signals = []

    for sym in SYMBOLS:
        p(f"Processing {sym}...")
        try:
            daily = load_daily(sym)
            daily_atr = compute_wilder_atr(daily)
            sigs = analyze_symbol(sym, spy_features, daily_atr)
            if len(sigs) > 0:
                all_signals.append(sigs)
                wins = sigs['win'].sum()
                n = len(sigs)
                p(f"  {sym}: {n} signals, {wins} wins ({wins/n*100:.1f}%)")
            else:
                p(f"  {sym}: 0 signals")
        except Exception as e:
            p(f"  {sym}: ERROR — {e}")

    if not all_signals:
        p("No signals found!")
        return

    df = pd.concat(all_signals, ignore_index=True)

    p()
    p("=" * 70)
    p(f"TOTAL SIGNALS: {len(df):,}")

    # Date range
    min_date = df['trade_date'].min()
    max_date = df['trade_date'].max()
    n_days = (pd.Timestamp(max_date) - pd.Timestamp(min_date)).days
    n_months = n_days / 30
    p(f"Date range: {min_date} to {max_date} ({n_days} days, ~{n_months:.1f} months)")
    signals_per_month = len(df) / n_months if n_months > 0 else 0
    p(f"Signals/month: {signals_per_month:.1f}")

    baseline_win = df['win'].mean() * 100
    baseline_loss = df['lose'].mean() * 100
    neutral_pct = 100 - baseline_win - baseline_loss
    p(f"\nBaseline: Win={baseline_win:.1f}% | Loss={baseline_loss:.1f}% | Neutral={neutral_pct:.1f}%")
    p(f"Win condition: MFE > 0.15 ATR  |  Loss condition: MFE < 0.05 ATR")

    p()
    p("=" * 70)
    p("FACTOR ANALYSIS")
    p("=" * 70)

    factors = [
        ('symbol_above_vwap', 'Symbol above its own VWAP'),
        ('symbol_ema_bear', 'Symbol EMA20 trending down (bear)'),
        ('time_bucket', 'Time of day'),
        ('resistance_nearby', 'Resistance level within 0.3 ATR above'),
        ('spy_reclaim_bucket', 'SPY reclaim duration'),
        ('sym_weaker', 'Symbol weaker than SPY (underperforming)'),
        ('vwap_bucket', 'Symbol VWAP distance bucket'),
    ]

    factor_results = {}

    for col, label in factors:
        p(f"\n--- {label} ---")
        tbl, bw = factor_table(df, col, label)
        factor_results[col] = tbl
        p(f"{'Bucket':<22} {'N':>6} {'Win%':>7} {'Loss%':>7} {'Lift':>6}")
        p("-" * 52)
        for _, row in tbl.iterrows():
            marker = " <-- BEST" if row['win_rate'] == tbl['win_rate'].max() and row['N'] >= 20 else ""
            p(f"{str(row[col]):<22} {row['N']:>6} {row['win_rate']:>6.1f}% {row['loss_rate']:>6.1f}% {row['lift']:>6.2f}x{marker}")

    p()
    p("=" * 70)
    p("TOP 2-FACTOR COMBOS (N >= 20, win_rate >= 55%)")
    p("=" * 70)

    factor_cols = [col for col, _ in factors]
    combos = []

    for i, c1 in enumerate(factor_cols):
        for c2 in factor_cols[i+1:]:
            grouped = df.groupby([c1, c2]).agg(
                N=('win', 'count'),
                wins=('win', 'sum'),
                losses=('lose', 'sum')
            ).reset_index()
            grouped['win_rate'] = grouped['wins'] / grouped['N'] * 100
            grouped['loss_rate'] = grouped['losses'] / grouped['N'] * 100
            grouped['lift'] = grouped['win_rate'] / baseline_win

            good = grouped[(grouped['N'] >= 20) & (grouped['win_rate'] >= 55)]
            for _, row in good.iterrows():
                combos.append({
                    'f1': c1, 'v1': row[c1],
                    'f2': c2, 'v2': row[c2],
                    'N': row['N'],
                    'win_rate': row['win_rate'],
                    'loss_rate': row['loss_rate'],
                    'lift': row['lift'],
                })

    combos_df = pd.DataFrame(combos).sort_values('win_rate', ascending=False) if combos else pd.DataFrame()

    if len(combos_df) > 0:
        p(f"{'Factor1=Val':<35} {'Factor2=Val':<35} {'N':>5} {'Win%':>7} {'Loss%':>7} {'Lift':>6}")
        p("-" * 95)
        for _, row in combos_df.head(20).iterrows():
            f1_str = f"{row['f1']}={row['v1']}"
            f2_str = f"{row['f2']}={row['v2']}"
            p(f"{f1_str:<35} {f2_str:<35} {row['N']:>5} {row['win_rate']:>6.1f}% {row['loss_rate']:>6.1f}% {row['lift']:>6.2f}x")
    else:
        p("No combos found with N>=20 and win_rate>=55%")
        p("\nRelaxing to N>=15, win_rate>=52%:")
        if combos:
            combos_df2 = pd.DataFrame(combos).sort_values('win_rate', ascending=False)
        else:
            combos_df2 = pd.DataFrame()
            # Recompute without threshold
            for i, c1 in enumerate(factor_cols):
                for c2 in factor_cols[i+1:]:
                    grouped = df.groupby([c1, c2]).agg(
                        N=('win', 'count'),
                        wins=('win', 'sum'),
                        losses=('lose', 'sum')
                    ).reset_index()
                    grouped['win_rate'] = grouped['wins'] / grouped['N'] * 100
                    grouped['loss_rate'] = grouped['losses'] / grouped['N'] * 100
                    grouped['lift'] = grouped['win_rate'] / baseline_win
                    good2 = grouped[(grouped['N'] >= 15) & (grouped['win_rate'] >= 52)]
                    for _, row in good2.iterrows():
                        combos.append({
                            'f1': c1, 'v1': row[c1],
                            'f2': c2, 'v2': row[c2],
                            'N': row['N'],
                            'win_rate': row['win_rate'],
                            'loss_rate': row['loss_rate'],
                            'lift': row['lift'],
                        })
            combos_df2 = pd.DataFrame(combos).sort_values('win_rate', ascending=False) if combos else pd.DataFrame()

        if len(combos_df2) > 0:
            p(f"{'Factor1=Val':<35} {'Factor2=Val':<35} {'N':>5} {'Win%':>7} {'Loss%':>7} {'Lift':>6}")
            p("-" * 95)
            for _, row in combos_df2.head(20).iterrows():
                f1_str = f"{row['f1']}={row['v1']}"
                f2_str = f"{row['f2']}={row['v2']}"
                p(f"{f1_str:<35} {f2_str:<35} {row['N']:>5} {row['win_rate']:>6.1f}% {row['loss_rate']:>6.1f}% {row['lift']:>6.2f}x")

    # Best filter rule
    p()
    p("=" * 70)
    p("BEST FILTER RULE & COVERAGE")
    p("=" * 70)

    # Find best single factor for filtering
    best_single = None
    best_single_wr = 0
    for col, label in factors:
        tbl = factor_results[col]
        for _, row in tbl.iterrows():
            if row['N'] >= 20 and row['win_rate'] > best_single_wr:
                best_single_wr = row['win_rate']
                best_single = (col, row[col], row['N'], row['win_rate'], row['loss_rate'])

    if best_single:
        col, val, n, wr, lr = best_single
        mask = df[col] == val
        coverage = mask.sum() / len(df) * 100
        p(f"\nBest single filter: {col} == {val}")
        p(f"  Win rate: {wr:.1f}%  (baseline: {baseline_win:.1f}%,  lift: {wr/baseline_win:.2f}x)")
        p(f"  Loss rate: {lr:.1f}%")
        p(f"  N: {n}")
        p(f"  Coverage: {coverage:.1f}% of all signals PASS this filter")
        p(f"  Suppressed: {100-coverage:.1f}% of signals would be DIM/suppressed")
        spm_keep = signals_per_month * coverage / 100
        p(f"  Signals/month kept: {spm_keep:.1f} (from {signals_per_month:.1f} total)")

    if len(combos_df) > 0:
        best_combo = combos_df.iloc[0]
        mask2 = (df[best_combo['f1']] == best_combo['v1']) & (df[best_combo['f2']] == best_combo['v2'])
        cov2 = mask2.sum() / len(df) * 100
        p(f"\nBest 2-factor filter: {best_combo['f1']}=={best_combo['v1']} AND {best_combo['f2']}=={best_combo['v2']}")
        p(f"  Win rate: {best_combo['win_rate']:.1f}%  Loss rate: {best_combo['loss_rate']:.1f}%  N: {best_combo['N']}")
        p(f"  Coverage: {cov2:.1f}% of signals pass | Suppressed: {100-cov2:.1f}%")

    # Symbol breakdown
    p()
    p("=" * 70)
    p("SYMBOL BREAKDOWN")
    p("=" * 70)
    sym_tbl = df.groupby('symbol').agg(
        N=('win', 'count'),
        wins=('win', 'sum'),
        losses=('lose', 'sum')
    ).reset_index()
    sym_tbl['win_rate'] = sym_tbl['wins'] / sym_tbl['N'] * 100
    sym_tbl['loss_rate'] = sym_tbl['losses'] / sym_tbl['N'] * 100
    sym_tbl = sym_tbl.sort_values('win_rate', ascending=False)
    p(f"{'Symbol':<8} {'N':>5} {'Win%':>7} {'Loss%':>7}")
    p("-" * 32)
    for _, row in sym_tbl.iterrows():
        p(f"{row['symbol']:<8} {row['N']:>5} {row['win_rate']:>6.1f}% {row['loss_rate']:>6.1f}%")

    # Pine Script sketch
    p()
    p("=" * 70)
    p("PINE SCRIPT IMPLEMENTATION SKETCH")
    p("=" * 70)

    if best_single:
        col, val, n, wr, lr = best_single
        p(f"\n// Filter: bear signal during SPY VWAP reclaim — best condition: {col}=={val}")
        p(f"// Win rate: {wr:.1f}% vs {baseline_win:.1f}% baseline ({wr/baseline_win:.2f}x lift)")

    p("""
// SPY VWAP reclaim detection (on symbol chart using security())
spy_vwap = ta.vwap(hlc3)  // or request.security("SPY", ...)
spy_above_vwap = close > spy_vwap  // proxy: symbol above its own VWAP
spy_sustained_reclaim = spy_above_vwap and spy_above_vwap[1]  // 2+ bars

// Bear signal conditions
bear_bar = close < open
vol_above_avg = volume > ta.sma(volume, 20)
sig_range = (high - low) >= 0.3 * atr14

// Base bear signal during SPY reclaim
base_signal = bear_bar and vol_above_avg and sig_range and spy_sustained_reclaim

// Best quality filter (from research):
sym_above_vwap = close > ta.vwap(hlc3)
ema20 = ta.ema(close, 20)
sym_ema_bear = ema20 < ema20[5]
sym_weaker_spy = (close / close[1] - 1) < (spy_close / spy_close[1] - 1)

// Apply filter — DIM if not meeting quality conditions
bear_hq = base_signal and sym_ema_bear  // counter-trend with-EMA: highest lift
// or: bear_hq = base_signal and not sym_above_vwap  // symbol below own VWAP
""")

    p("=" * 70)
    p(f"Results saved to: {OUTPUT}")

    # Save
    with open(OUTPUT, 'w') as f:
        f.write('\n'.join(lines))

    p("Done.")


if __name__ == '__main__':
    main()
