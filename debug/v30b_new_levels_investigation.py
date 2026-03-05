"""
v3.0b New Levels Investigation
Analyzes PD Mid, PD Last Hr Low, and VWAP zone signals from live pine logs
to understand why they are negative in live vs positive in backtest.
"""

import pandas as pd
import numpy as np
import re
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

BASE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView")
DEBUG = BASE / "debug"
BARS5 = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars_highres/5sec")

# Symbol mapping: pine log file -> symbol
LOG_SYMBOL_MAP = {
    "pine-logs-Key Level Breakout v3.0b_01085.csv": "AAPL",
    "pine-logs-Key Level Breakout v3.0b_1f23e.csv": "QQQ",
    "pine-logs-Key Level Breakout v3.0b_21c43.csv": "TSLA",
    "pine-logs-Key Level Breakout v3.0b_2f230.csv": "AMZN",
    "pine-logs-Key Level Breakout v3.0b_67b51.csv": "META",
    "pine-logs-Key Level Breakout v3.0b_ba67a.csv": "AMD",
    "pine-logs-Key Level Breakout v3.0b_ccab3.csv": "NVDA",
    "pine-logs-Key Level Breakout v3.0b_cea64.csv": "SPY",
}

# Signal regex
sig_pat = re.compile(
    r'\[KLB\]\s+(\d+:\d+)\s+(▲|▼)\s+'
    r'(BRK|~\s*~|~~\s*~*|◆[^◆]*|~ ~)\s+'
    r'(.+?)\s+vol=([\d.]+)x\s+pos=([v^]\d+)\s+'
    r'vwap=(above|below)\s+ema=(bull|bear)\s+'
    r'rs=([+\-\d.]+)%\s+adx=(\d+)\s+body=(\d+)%\s+'
    r'ramp=([\d.]+)x\s+rangeATR=([\d.]+)\s*'
    r'(⚡)?\s*(⚠)?\s*'
    r'O([\d.]+)\s+H([\d.]+)\s+L([\d.]+)\s+C([\d.]+)\s+'
    r'ATR=([\d.]+)'
)


def parse_signal_type(raw_type):
    raw = raw_type.strip()
    if raw == 'BRK':
        return 'BRK'
    if raw.startswith('◆'):
        return 'RET'
    return 'REV'


def classify_new_level(levels):
    """
    Returns list of new-level categories present in the level string.
    PD_MID: 'PD Mid' in levels
    PD_LHR: 'PD LH L' in levels (Prior-Day Last Hour Low)
    VWAP_ZONE: VWAP appears in levels and signal type = REV (handled separately)
    """
    cats = []
    if 'PD Mid' in levels:
        cats.append('PD_MID')
    if 'PD LH L' in levels:
        cats.append('PD_LHR')
    return cats


def load_5sec(sym):
    """Load 5sec parquet for a symbol, normalized to US/Eastern."""
    f = BARS5 / f"{sym.lower()}_5_secs_ib.parquet"
    if not f.exists():
        raise FileNotFoundError(f"No 5sec data for {sym}")
    df = pd.read_parquet(f)
    df = df.sort_values('date').reset_index(drop=True)
    if df['date'].dt.tz is None:
        df['date'] = df['date'].dt.tz_localize('US/Eastern')
    else:
        df['date'] = df['date'].dt.tz_convert('US/Eastern')
    return df


def compute_pnl(day_bars, entry_time, entry_close, direction, atr, minutes_list):
    """
    Compute PnL in ATR at various minutes after signal.
    direction: '▲' (bull, we buy) or '▼' (bear, we sell)
    """
    sign = 1 if direction == '▲' else -1
    result = {}
    for m in minutes_list:
        target_time = entry_time + pd.Timedelta(minutes=m)
        future = day_bars[day_bars['date'] >= target_time]
        if len(future) == 0:
            result[m] = np.nan
            continue
        exit_close = future.iloc[0]['close']
        raw_pnl = (exit_close - entry_close) * sign
        result[m] = round(raw_pnl / atr, 3) if atr > 0 else np.nan
    return result


def parse_pine_logs():
    """Parse all v3.0b pine log files and extract signals."""
    all_signals = []

    for log_name, symbol in LOG_SYMBOL_MAP.items():
        log_path = DEBUG / log_name
        if not log_path.exists():
            print(f"WARNING: {log_name} not found")
            continue

        df_log = pd.read_csv(log_path)

        for _, row in df_log.iterrows():
            msg = row['Message']
            ts_str = row['Date']

            if not isinstance(msg, str):
                continue
            if 'CONF' in msg or '5m CHECK' in msg or 'RNG range' in msg:
                continue

            m = sig_pat.search(msg)
            if not m:
                continue

            time_str = m.group(1)
            direction = m.group(2)
            raw_type = m.group(3)
            levels = m.group(4).strip()
            vol = float(m.group(5))
            vwap_pos = m.group(7)
            ema = m.group(8)
            adx = int(m.group(10))
            body = int(m.group(11))
            ramp = float(m.group(12))
            range_atr = float(m.group(13))
            is_lightning = bool(m.group(14))
            is_warn = bool(m.group(15))
            c_price = float(m.group(19))
            atr = float(m.group(20))

            sig_type = parse_signal_type(raw_type)

            ts = pd.Timestamp(ts_str)
            if ts.tzinfo is None:
                ts = ts.tz_localize('US/Eastern')
            else:
                ts = ts.tz_convert('US/Eastern')

            hour = ts.hour
            minute = ts.minute

            # Classify new levels
            level_cats = classify_new_level(levels)
            # VWAP zone = VWAP appears in levels AND it's a REV signal
            is_vwap_zone = 'VWAP' in levels and sig_type == 'REV'
            if is_vwap_zone:
                level_cats.append('VWAP_ZONE')

            ema_aligned = (direction == '▲' and ema == 'bull') or (direction == '▼' and ema == 'bear')

            if hour == 9:
                time_bucket = '9:30-10:00'
            elif hour == 10:
                time_bucket = '10:00-11:00'
            elif hour == 11:
                time_bucket = '11:00-12:00'
            else:
                time_bucket = '12:00+'

            all_signals.append({
                'symbol': symbol,
                'date': ts.date(),
                'timestamp': ts,
                'time_str': time_str,
                'direction': direction,
                'sig_type': sig_type,
                'levels': levels,
                'level_cats': level_cats,
                'has_pd_mid': 'PD_MID' in level_cats,
                'has_pd_lhr': 'PD_LHR' in level_cats,
                'has_vwap_zone': 'VWAP_ZONE' in level_cats,
                'is_new_level': len(level_cats) > 0,
                'vol': vol,
                'vwap_pos': vwap_pos,
                'ema': ema,
                'ema_aligned': ema_aligned,
                'adx': adx,
                'body': body,
                'ramp': ramp,
                'range_atr': range_atr,
                'is_lightning': is_lightning,
                'is_warn': is_warn,
                'c': c_price,
                'atr': atr,
                'hour': hour,
                'minute': minute,
                'time_bucket': time_bucket,
                'is_morning': hour < 11,
            })

    return pd.DataFrame(all_signals)


def add_follow_through(df_signals):
    """Add follow-through PnL columns using 5sec data."""
    minutes = [5, 15, 30, 60]
    for m in minutes:
        df_signals[f'pnl_{m}m'] = np.nan

    sym_bars = {}
    sym_day_bars = {}

    for idx, row in df_signals.iterrows():
        sym = row['symbol']

        if sym not in sym_bars:
            try:
                sym_bars[sym] = load_5sec(sym)
            except FileNotFoundError:
                print(f"WARNING: No 5sec data for {sym}")
                continue

        if sym not in sym_bars:
            continue

        bars = sym_bars[sym]
        day_key = (sym, str(row['date']))

        if day_key not in sym_day_bars:
            day_bars = bars[bars['date'].dt.date.astype(str) == str(row['date'])].copy()
            sym_day_bars[day_key] = day_bars
        else:
            day_bars = sym_day_bars[day_key]

        pnl = compute_pnl(
            day_bars, row['timestamp'], row['c'],
            row['direction'], row['atr'], minutes
        )
        for m in minutes:
            df_signals.at[idx, f'pnl_{m}m'] = pnl.get(m, np.nan)

    return df_signals


def pct_win(series):
    s = series.dropna()
    if len(s) == 0:
        return np.nan
    return round((s > 0).mean() * 100, 1)


def avg_pnl(series):
    s = series.dropna()
    if len(s) == 0:
        return np.nan
    return round(s.mean(), 3)


def total_pnl(series):
    s = series.dropna()
    return round(s.sum(), 1)


def summarize(df, label=""):
    n = len(df)
    if n == 0:
        return f"{label}: N=0"
    w15 = pct_win(df['pnl_15m'])
    w30 = pct_win(df['pnl_30m'])
    w60 = pct_win(df['pnl_60m'])
    a30 = avg_pnl(df['pnl_30m'])
    t30 = total_pnl(df['pnl_30m'])
    return (f"{label}: N={n}, win%@30m={w30}%, avg@30m={a30}, total@30m={t30} ATR "
            f"| win@15m={w15}%, win@60m={w60}%")


def build_signal_table(df, sort_col='pnl_30m'):
    """Build a detailed signal-by-signal table."""
    cols = ['date', 'time_str', 'symbol', 'direction', 'sig_type', 'levels',
            'vol', 'ema_aligned', 'adx', 'vwap_pos', 'body',
            'is_lightning', 'is_warn',
            'pnl_15m', 'pnl_30m', 'pnl_60m']
    df_out = df[cols].copy()
    df_out = df_out.sort_values(sort_col, ascending=False)
    return df_out


def analyze_backtest():
    """Analyze the original backtest to understand what it measured."""
    bt_path = DEBUG / "no-signal-zone-moves.csv"
    if not bt_path.exists():
        return "no-signal-zone-moves.csv not found"

    df = pd.read_csv(bt_path)

    # The backtest tested moves NEAR levels within 0.15 ATR (TIGHT_ATR)
    # using 5m candle data from 2024-2026
    # It measured MFE over next 6 bars (30 min) from the level-touch bar
    # It was NOT looking at BRK/REV from our indicator — it was "backdoor" testing
    # of whether these levels had ANY predictive value at all

    # Key differences vs live:
    # 1. Backtest: ANY 5m bar touching level within 0.15 ATR → hypothetical trade
    #    Live: Signal must pass vol filter, EMA gate, first-cross, etc.
    # 2. Backtest: tested after 10:30 (midday focus)
    #    Live: these levels fire all day (including 9:30-10:30)
    # 3. Backtest: VWAP_LOWER = VWAP - VWAP_STD (standard deviation band)
    #    Live:     VWAP_LOWER = VWAP - ATR(14)  (completely different calculation!)
    # 4. Backtest: direction for PD_MID = EMA direction (neutral level)
    #    Live: PD_MID fires as BRK in any direction the price crosses
    # 5. Backtest: measured MFE (best outcome), not close-at-30m
    #    The win% is based on whether move continued AT ALL, not specific exit

    results = {
        'total_rows': len(df),
        'date_range': f"{df['date'].min()} to {df['date'].max()}",
        'symbols': sorted(df['symbol'].unique()),
        'time_distribution': df['time_bucket'].value_counts().to_dict(),
        'ema_aligned_rate': round(df['ema_aligned'].mean() * 100, 1),
        'vol_mean': round(df['vol_ratio'].mean(), 2),
        'vol_median': round(df['vol_ratio'].median(), 2),
        'classification': df['classification'].value_counts().to_dict(),
        'direction': df['direction'].value_counts().to_dict(),
    }
    return results


def main():
    print("=" * 70)
    print("v3.0b NEW LEVELS INVESTIGATION")
    print("=" * 70)

    # 1. Parse pine logs
    print("\n[1] Parsing pine log files...")
    df_sigs = parse_pine_logs()
    print(f"Total signals parsed: {len(df_sigs)}")
    print(f"Symbols: {sorted(df_sigs['symbol'].unique())}")
    print(f"Date range: {df_sigs['date'].min()} to {df_sigs['date'].max()}")

    # 2. Add follow-through
    print("\n[2] Computing follow-through using 5sec data...")
    df_sigs = add_follow_through(df_sigs)

    # 3. Split datasets
    df_pd_mid = df_sigs[df_sigs['has_pd_mid']].copy()
    df_pd_lhr = df_sigs[df_sigs['has_pd_lhr']].copy()
    df_vwap = df_sigs[df_sigs['has_vwap_zone']].copy()
    df_old = df_sigs[~df_sigs['is_new_level']].copy()

    print(f"\nNew-level signals:")
    print(f"  PD Mid: {len(df_pd_mid)}")
    print(f"  PD LH L: {len(df_pd_lhr)}")
    print(f"  VWAP Zone: {len(df_vwap)}")

    # 4. Top-level summary
    print("\n[3] OVERALL PERFORMANCE SUMMARY")
    print("-" * 60)
    print(summarize(df_pd_mid, "PD Mid"))
    print(summarize(df_pd_lhr, "PD LH L"))
    print(summarize(df_vwap, "VWAP Zone"))
    print(summarize(df_old, "Original levels"))

    # 5. Detailed breakdown for each new level
    results = {}

    for level_name, df_level in [("PD_MID", df_pd_mid), ("PD_LHR", df_pd_lhr), ("VWAP_ZONE", df_vwap)]:
        print(f"\n[4] DEEP DIVE: {level_name}")
        print("-" * 60)
        r = {'name': level_name, 'n': len(df_level)}

        if len(df_level) == 0:
            print("  No signals")
            continue

        # Signal type breakdown
        print("\n  -- Signal Type --")
        for st in ['BRK', 'REV', 'RET']:
            sub = df_level[df_level['sig_type'] == st]
            print(f"  {st}: {summarize(sub)}")

        # Time breakdown
        print("\n  -- Time Bucket --")
        for tb in ['9:30-10:00', '10:00-11:00', '11:00-12:00', '12:00+']:
            sub = df_level[df_level['time_bucket'] == tb]
            if len(sub) > 0:
                print(f"  {tb}: {summarize(sub)}")

        # EMA alignment
        print("\n  -- EMA Alignment --")
        for ema_val in [True, False]:
            sub = df_level[df_level['ema_aligned'] == ema_val]
            label = "EMA aligned" if ema_val else "EMA counter"
            print(f"  {label}: {summarize(sub)}")

        # Direction
        print("\n  -- Direction --")
        for d in ['▲', '▼']:
            sub = df_level[df_level['direction'] == d]
            label = "Bull" if d == '▲' else "Bear"
            print(f"  {label}: {summarize(sub)}")

        # Volume
        print("\n  -- Volume --")
        for lo, hi, label in [(0, 1, '<1x'), (1, 2, '1-2x'), (2, 5, '2-5x'), (5, 999, '≥5x')]:
            sub = df_level[(df_level['vol'] >= lo) & (df_level['vol'] < hi)]
            print(f"  {label}: {summarize(sub)}")

        # ADX
        print("\n  -- ADX --")
        for lo, hi, label in [(0, 20, '<20'), (20, 30, '20-30'), (30, 40, '30-40'), (40, 999, '≥40')]:
            sub = df_level[(df_level['adx'] >= lo) & (df_level['adx'] < hi)]
            print(f"  {label}: {summarize(sub)}")

        # Symbol breakdown
        print("\n  -- Symbol --")
        for sym in sorted(df_level['symbol'].unique()):
            sub = df_level[df_level['symbol'] == sym]
            print(f"  {sym}: {summarize(sub)}")

        # Lightning flag
        print("\n  -- Lightning flag --")
        for flag in [True, False]:
            sub = df_level[df_level['is_lightning'] == flag]
            label = "Lightning (⚡)" if flag else "No lightning"
            print(f"  {label}: {summarize(sub)}")

        r['breakdown_done'] = True
        results[level_name] = r

    # 6. Winners vs Losers analysis
    print("\n[5] WINNERS vs LOSERS ANALYSIS (30m PnL)")
    print("-" * 60)

    all_new = df_sigs[df_sigs['is_new_level']].copy()
    if len(all_new) > 0:
        winners = all_new[all_new['pnl_30m'] > 0.1]
        losers = all_new[all_new['pnl_30m'] < -0.1]
        neutral = all_new[(all_new['pnl_30m'] >= -0.1) & (all_new['pnl_30m'] <= 0.1)]

        print(f"\nWinners (30m PnL > +0.1 ATR): {len(winners)}")
        print(f"Losers  (30m PnL < -0.1 ATR): {len(losers)}")
        print(f"Neutral (-0.1 to +0.1 ATR):  {len(neutral)}")

        def profile(df_sub, label):
            if len(df_sub) == 0:
                return
            print(f"\n  {label} Profile:")
            print(f"    EMA aligned: {df_sub['ema_aligned'].mean()*100:.0f}%")
            print(f"    Morning (before 11am): {(df_sub['hour'] < 11).mean()*100:.0f}%")
            print(f"    Mean ADX: {df_sub['adx'].mean():.1f}")
            print(f"    Mean vol: {df_sub['vol'].mean():.1f}x")
            print(f"    Lightning: {df_sub['is_lightning'].mean()*100:.0f}%")
            print(f"    Body warn (⚠): {df_sub['is_warn'].mean()*100:.0f}%")
            print(f"    BRK/REV/RET: {(df_sub['sig_type']=='BRK').sum()}/{(df_sub['sig_type']=='REV').sum()}/{(df_sub['sig_type']=='RET').sum()}")
            print(f"    Bull/Bear: {(df_sub['direction']=='▲').sum()}/{(df_sub['direction']=='▼').sum()}")
            print(f"    Time buckets: {df_sub['time_bucket'].value_counts().to_dict()}")
            print(f"    Top symbols: {df_sub['symbol'].value_counts().head(4).to_dict()}")
            print(f"    VWAP aligned: {(df_sub['vwap_pos'] == ('above' if True else 'x')).sum()} - {'above' in df_sub['vwap_pos'].values}")

        profile(winners, "WINNERS")
        profile(losers, "LOSERS")

    # 7. Backtest comparison
    print("\n[6] BACKTEST vs LIVE COMPARISON")
    print("-" * 60)
    bt_results = analyze_backtest()
    if isinstance(bt_results, dict):
        print(f"\nBacktest dataset (no-signal-zone-moves.csv):")
        print(f"  Total rows: {bt_results['total_rows']:,}")
        print(f"  Date range: {bt_results['date_range']}")
        print(f"  Symbols: {bt_results['symbols']}")
        print(f"  EMA aligned rate: {bt_results['ema_aligned_rate']}%")
        print(f"  Vol ratio: mean={bt_results['vol_mean']}, median={bt_results['vol_median']}")
        print(f"  Time distribution: {bt_results['time_distribution']}")
        print(f"  Classification: {bt_results['classification']}")

    print("\n  KEY DIFFERENCES (Backtest vs Live):")
    print("  1. VWAP Lower computation: backtest = VWAP - VWAP_STD; live = VWAP - ATR(14)")
    print("     These are very different levels! VWAP_STD is often <0.5x ATR early in the day.")
    print("  2. Backtest: ANY bar touching level within 0.15 ATR → hypothetical trade")
    print("     Live: Signal must pass vol filter, EMA gate, first-cross guard, etc.")
    print("  3. Backtest: tested AFTER 10:30 only (midday focus for 'treasure hunt')")
    print("     Live: these levels fire all day, including 9:30-10:30 open")
    print("  4. Backtest: PD_MID direction = EMA direction (neutral level)")
    print("     Live: PD_MID fires as BRK or REV in any direction price crosses")
    print("  5. Backtest measured MFE over 6 bars, not mark-to-market at exactly 30m")
    print("  6. Backtest: VWAP_LOWER treated as LOW level (bull reversal off it)")
    print("     Live: VWAP Lower Band fires as bearish BRK (sigBearVWBL)")
    print("     → Direction is OPPOSITE in the implementation vs backtest assumption!")

    # 8. Signal-by-signal tables
    print("\n[7] SIGNAL-BY-SIGNAL TABLES")
    print("-" * 60)

    for level_name, df_level in [("PD_MID", df_pd_mid), ("PD_LHR", df_pd_lhr), ("VWAP_ZONE", df_vwap)]:
        print(f"\n=== {level_name} signals (sorted by 30m PnL, best to worst) ===")
        if len(df_level) == 0:
            print("  No signals")
            continue
        tbl = build_signal_table(df_level, 'pnl_30m')
        with pd.option_context('display.max_rows', 200, 'display.max_colwidth', 40,
                               'display.width', 160):
            print(tbl.to_string(index=False))

    return df_sigs, df_pd_mid, df_pd_lhr, df_vwap


if __name__ == '__main__':
    df_sigs, df_pd_mid, df_pd_lhr, df_vwap = main()
