"""
FADE Resurrection Backtest
==========================
Tests decoupled FADE signal: after ANY signal, if price reverses back through
the level within N bars (5m), fire a FADE in the opposite direction.

Old FADE: required CONF failure first (79 signals in v3.0b)
New FADE: fires after any signal where price crosses back through level

Uses:
- enriched-signals.csv (1841 signals, 13 symbols, Jan 20 - Feb 27 2026)
- IB 5m parquet candles from trading_bot/cache/bars/
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# --- Paths ---
DEBUG = Path(__file__).parent
CACHE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars")
SIGNALS_PATH = DEBUG / "enriched-signals.csv"
REPORT_PATH = DEBUG / "fade-resurrection-research.md"

SYMBOLS = ["SPY", "QQQ", "AAPL", "AMZN", "AMD", "GOOGL", "META", "MSFT", "NVDA", "TSLA", "TSM", "GLD", "SLV"]

# --- Parameters ---
FADE_WINDOWS = [2, 3, 4, 6, 8, 10]  # bars to check for crossback (5m each)
FADE_OUTCOME_BARS = 6  # bars to measure MFE/MAE after FADE fires (30 min)
EXTENDED_OUTCOME_BARS = 12  # 60 min for extended outcome


def load_candles():
    """Load 5m IB candles for all 13 symbols, convert to ET, filter RTH."""
    candles = {}
    for sym in SYMBOLS:
        fpath = CACHE / f"{sym.lower()}_5_mins_ib.parquet"
        if not fpath.exists():
            print(f"  WARNING: {fpath} not found, skipping {sym}")
            continue
        df = pd.read_parquet(fpath)
        df['date'] = pd.to_datetime(df['date'])
        # Convert Berlin -> US/Eastern
        df['date_et'] = df['date'].dt.tz_convert('US/Eastern')
        # Filter to RTH: 9:30 - 16:00 ET
        df = df[(df['date_et'].dt.hour * 60 + df['date_et'].dt.minute >= 9 * 60 + 30) &
                (df['date_et'].dt.hour * 60 + df['date_et'].dt.minute < 16 * 60)]
        # Filter to Jan-Feb 2026
        df = df[(df['date_et'].dt.year == 2026) &
                (df['date_et'].dt.month <= 2)]
        df = df.sort_values('date_et').reset_index(drop=True)
        candles[sym] = df
    return candles


def find_signal_bar(candle_df, sig_date, sig_time):
    """Find the candle bar index closest to the signal time."""
    # Parse signal time (e.g., "9:35") into hour:minute
    parts = sig_time.split(':')
    h, m = int(parts[0]), int(parts[1])
    # 5m bars are at :00, :05, :10, ... so round down to nearest 5min
    m_rounded = (m // 5) * 5

    # Find matching bars for this date
    mask = candle_df['date_et'].dt.date.astype(str) == sig_date
    day_bars = candle_df[mask]
    if day_bars.empty:
        return None, None

    # Find the bar at or just before signal time
    target_minutes = h * 60 + m_rounded
    day_bars = day_bars.copy()
    day_bars['minutes'] = day_bars['date_et'].dt.hour * 60 + day_bars['date_et'].dt.minute
    # Get bar at or closest before signal time
    candidates = day_bars[day_bars['minutes'] <= h * 60 + m]
    if candidates.empty:
        return None, None

    # Take the last bar at or before signal time
    bar_idx = candidates.index[-1]
    return bar_idx, candle_df.index.get_loc(bar_idx)


def check_crossback(candle_df, start_pos, level_price, direction, window_bars):
    """
    Check if price crosses BACK through level_price within window_bars.

    For BULL signal: price broke above level, crossback = close drops below level
    For BEAR signal: price broke below level, crossback = close rises above level

    Returns: (crossed_back: bool, crossback_bar_offset: int or None)
    """
    total_bars = len(candle_df)
    for i in range(1, window_bars + 1):
        pos = start_pos + i
        if pos >= total_bars:
            return False, None
        bar = candle_df.iloc[pos]
        if direction == 'bull':
            # Bull signal broke above level; crossback = price goes below
            if bar['close'] < level_price:
                return True, i
        else:
            # Bear signal broke below level; crossback = price goes above
            if bar['close'] > level_price:
                return True, i
    return False, None


def measure_fade_outcome(candle_df, fade_pos, fade_direction, atr, outcome_bars):
    """
    Measure MFE and MAE after FADE fires (in ATR multiples).

    fade_direction: the FADE direction (opposite of original signal)
    Returns: (mfe_atr, mae_atr) or (None, None) if insufficient bars
    """
    total_bars = len(candle_df)
    fade_close = candle_df.iloc[fade_pos]['close']

    mfe = 0.0
    mae = 0.0

    for i in range(1, outcome_bars + 1):
        pos = fade_pos + i
        if pos >= total_bars:
            break
        bar = candle_df.iloc[pos]

        if fade_direction == 'bull':
            # FADE is bullish: MFE = how high, MAE = how low
            excursion_high = (bar['high'] - fade_close) / atr
            excursion_low = (bar['low'] - fade_close) / atr
            mfe = max(mfe, excursion_high)
            mae = min(mae, excursion_low)
        else:
            # FADE is bearish: MFE = how low (inverted), MAE = how high (inverted)
            excursion_high = (fade_close - bar['low']) / atr
            excursion_low = (fade_close - bar['high']) / atr
            mfe = max(mfe, excursion_high)
            mae = min(mae, excursion_low)

    return mfe, mae


def run_backtest():
    """Main backtest: for each signal, check crossback and measure FADE outcome."""
    print("Loading signals...")
    signals = pd.read_csv(SIGNALS_PATH)
    print(f"  {len(signals)} signals loaded")

    print("Loading 5m candles...")
    candles = load_candles()
    print(f"  {len(candles)} symbols loaded")

    results = []

    for idx, sig in signals.iterrows():
        sym = sig['symbol']
        if sym not in candles:
            continue

        cdf = candles[sym]
        bar_idx, bar_pos = find_signal_bar(cdf, sig['date'], sig['time'])
        if bar_pos is None:
            continue

        # Use signal close as proxy for level price
        level_price = sig['close']
        atr = sig['atr']
        direction = sig['direction']
        fade_direction = 'bear' if direction == 'bull' else 'bull'

        # Check crossback at multiple windows
        for window in FADE_WINDOWS:
            crossed, cb_offset = check_crossback(cdf, bar_pos, level_price, direction, window)
            if crossed:
                # Measure outcome from the crossback bar
                fade_bar_pos = bar_pos + cb_offset
                mfe_30, mae_30 = measure_fade_outcome(cdf, fade_bar_pos, fade_direction, atr, FADE_OUTCOME_BARS)
                mfe_60, mae_60 = measure_fade_outcome(cdf, fade_bar_pos, fade_direction, atr, EXTENDED_OUTCOME_BARS)

                fade_close = cdf.iloc[fade_bar_pos]['close']
                fade_time_et = cdf.iloc[fade_bar_pos]['date_et']

                results.append({
                    'symbol': sym,
                    'date': sig['date'],
                    'orig_time': sig['time'],
                    'orig_direction': direction,
                    'orig_type': sig['type'],
                    'orig_levels': sig['levels'],
                    'orig_level_type': sig['level_type'],
                    'orig_conf': sig['conf'],
                    'orig_ema': sig['ema'],
                    'orig_vwap': sig['vwap'],
                    'orig_mfe': sig['mfe'],
                    'orig_mae': sig['mae'],
                    'atr': atr,
                    'level_price': level_price,
                    'fade_window': window,
                    'crossback_bars': cb_offset,
                    'fade_direction': fade_direction,
                    'fade_time': fade_time_et.strftime('%H:%M') if hasattr(fade_time_et, 'strftime') else str(fade_time_et),
                    'fade_close': fade_close,
                    'fade_mfe_30m': mfe_30,
                    'fade_mae_30m': mae_30,
                    'fade_mfe_60m': mfe_60,
                    'fade_mae_60m': mae_60,
                })

    df = pd.DataFrame(results)
    print(f"\n  Total FADE candidates across all windows: {len(df)}")
    return df, signals


def analyze_results(df, signals):
    """Analyze FADE backtest results and generate report."""
    lines = []
    lines.append("# FADE Resurrection Research")
    lines.append(f"\n**Date:** {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"**Source:** {len(signals)} signals from enriched-signals.csv (Jan 20 - Feb 27 2026)")
    lines.append(f"**Method:** For each signal, check if price crosses back through level within N bars (5m)")
    lines.append(f"**FADE direction:** Opposite of original signal direction")
    lines.append("")

    # =====================================================
    # SECTION 1: Overview by window size
    # =====================================================
    lines.append("## 1. FADE Count by Window Size")
    lines.append("")
    lines.append("| Window | Bars | Minutes | FADE Count | % of Signals | MFE 30m | MAE 30m | Net 30m | MFE 60m | Net 60m |")
    lines.append("|--------|------|---------|------------|-------------|---------|---------|---------|---------|---------|")

    for w in FADE_WINDOWS:
        sub = df[df.fade_window == w]
        # For each window, only take the FIRST crossback (smallest window that triggered)
        # Actually, let's analyze each window independently first
        n = len(sub)
        pct = n / len(signals) * 100
        mfe30 = sub.fade_mfe_30m.mean()
        mae30 = sub.fade_mae_30m.mean()
        net30 = mfe30 + mae30  # MAE is negative
        mfe60 = sub.fade_mfe_60m.mean()
        mae60 = sub.fade_mae_60m.mean()
        net60 = mfe60 + mae60
        lines.append(f"| {w} | {w} | {w*5} | {n} | {pct:.1f}% | {mfe30:.3f} | {mae30:.3f} | {net30:.3f} | {mfe60:.3f} | {net60:.3f} |")

    lines.append("")
    lines.append("*Each row shows ALL signals that had a crossback within that window.*")
    lines.append("*A signal with crossback at bar 2 appears in windows 2, 3, 4, 6, 8, 10.*")

    # =====================================================
    # SECTION 2: Deduplicated - earliest crossback only
    # =====================================================
    lines.append("")
    lines.append("## 2. Deduplicated FADEs (Earliest Crossback)")
    lines.append("")

    # For each original signal, keep only the smallest window that triggered
    dedup = df.sort_values('fade_window').drop_duplicates(
        subset=['symbol', 'date', 'orig_time', 'orig_direction'], keep='first'
    )

    lines.append(f"**Total unique FADEs (window ≤ 6 bars / 30 min): {len(dedup[dedup.fade_window <= 6])}**")
    lines.append(f"**Total unique FADEs (any window): {len(dedup)}**")
    lines.append("")

    # Use 6-bar window as the primary definition
    primary = dedup[dedup.fade_window <= 6].copy()
    lines.append(f"### Primary Definition: Crossback within 6 bars (30 min)")
    lines.append(f"- N = {len(primary)}")
    lines.append(f"- Mean MFE (30m): {primary.fade_mfe_30m.mean():.3f} ATR")
    lines.append(f"- Mean MAE (30m): {primary.fade_mae_30m.mean():.3f} ATR")
    lines.append(f"- Net (30m): {primary.fade_mfe_30m.mean() + primary.fade_mae_30m.mean():.3f} ATR")
    lines.append(f"- Mean MFE (60m): {primary.fade_mfe_60m.mean():.3f} ATR")
    lines.append(f"- Mean MAE (60m): {primary.fade_mae_60m.mean():.3f} ATR")
    lines.append(f"- Net (60m): {primary.fade_mfe_60m.mean() + primary.fade_mae_60m.mean():.3f} ATR")
    lines.append("")

    # Win rate: MFE > |MAE| means the favorable move was bigger than adverse
    primary['win_30m'] = primary.fade_mfe_30m > abs(primary.fade_mae_30m)
    primary['win_60m'] = primary.fade_mfe_60m > abs(primary.fade_mae_60m)
    lines.append(f"- Win rate (30m, MFE > |MAE|): {primary.win_30m.mean()*100:.1f}%")
    lines.append(f"- Win rate (60m, MFE > |MAE|): {primary.win_60m.mean()*100:.1f}%")
    lines.append("")

    # =====================================================
    # SECTION 3: Compare old vs new FADE
    # =====================================================
    lines.append("## 3. Old FADE vs New FADE")
    lines.append("")

    # Old FADE = CONF failure signals that have crossback
    old_fade = primary[primary.orig_conf == '✗'].copy()
    new_only = primary[primary.orig_conf != '✗'].copy()

    lines.append(f"| Metric | Old FADE (CONF ✗) | New-Only (CONF ✓/NaN) | All FADEs |")
    lines.append(f"|--------|-------------------|----------------------|-----------|")
    lines.append(f"| Count | {len(old_fade)} | {len(new_only)} | {len(primary)} |")
    if len(old_fade) > 0:
        lines.append(f"| MFE 30m | {old_fade.fade_mfe_30m.mean():.3f} | {new_only.fade_mfe_30m.mean():.3f} | {primary.fade_mfe_30m.mean():.3f} |")
        lines.append(f"| MAE 30m | {old_fade.fade_mae_30m.mean():.3f} | {new_only.fade_mae_30m.mean():.3f} | {primary.fade_mae_30m.mean():.3f} |")
        lines.append(f"| Net 30m | {old_fade.fade_mfe_30m.mean()+old_fade.fade_mae_30m.mean():.3f} | {new_only.fade_mfe_30m.mean()+new_only.fade_mae_30m.mean():.3f} | {primary.fade_mfe_30m.mean()+primary.fade_mae_30m.mean():.3f} |")
        old_fade['win_30m'] = old_fade.fade_mfe_30m > abs(old_fade.fade_mae_30m)
        new_only['win_30m'] = new_only.fade_mfe_30m > abs(new_only.fade_mae_30m)
        lines.append(f"| Win% 30m | {old_fade.win_30m.mean()*100:.1f}% | {new_only.win_30m.mean()*100:.1f}% | {primary.win_30m.mean()*100:.1f}% |")
    lines.append("")

    # =====================================================
    # SECTION 4: Crossback speed analysis
    # =====================================================
    lines.append("## 4. Crossback Speed (How fast does price reverse?)")
    lines.append("")
    lines.append("| Crossback Bars | Count | MFE 30m | MAE 30m | Net 30m | Win% 30m |")
    lines.append("|----------------|-------|---------|---------|---------|----------|")

    for cb in sorted(primary.crossback_bars.unique()):
        sub = primary[primary.crossback_bars == cb]
        sub_win = sub.fade_mfe_30m > abs(sub.fade_mae_30m)
        lines.append(f"| {cb} | {len(sub)} | {sub.fade_mfe_30m.mean():.3f} | {sub.fade_mae_30m.mean():.3f} | {sub.fade_mfe_30m.mean()+sub.fade_mae_30m.mean():.3f} | {sub_win.mean()*100:.1f}% |")

    lines.append("")

    # =====================================================
    # SECTION 5: By Symbol
    # =====================================================
    lines.append("## 5. By Symbol")
    lines.append("")
    lines.append("| Symbol | FADEs | MFE 30m | MAE 30m | Net 30m | Win% | Total ATR |")
    lines.append("|--------|-------|---------|---------|---------|------|-----------|")

    for sym in sorted(primary.symbol.unique()):
        sub = primary[primary.symbol == sym]
        w = (sub.fade_mfe_30m > abs(sub.fade_mae_30m)).mean() * 100
        net = sub.fade_mfe_30m.mean() + sub.fade_mae_30m.mean()
        total_atr = (sub.fade_mfe_30m + sub.fade_mae_30m).sum()
        lines.append(f"| {sym} | {len(sub)} | {sub.fade_mfe_30m.mean():.3f} | {sub.fade_mae_30m.mean():.3f} | {net:.3f} | {w:.1f}% | {total_atr:.1f} |")

    # Count symbols with positive net
    pos_syms = 0
    for sym in sorted(primary.symbol.unique()):
        sub = primary[primary.symbol == sym]
        if (sub.fade_mfe_30m.mean() + sub.fade_mae_30m.mean()) > 0:
            pos_syms += 1
    lines.append(f"\n**Positive symbols: {pos_syms}/{len(primary.symbol.unique())}**")
    lines.append("")

    # =====================================================
    # SECTION 6: By Time of Day
    # =====================================================
    lines.append("## 6. By Time of Day")
    lines.append("")

    # Parse fade time to get hour buckets
    primary['fade_hour'] = primary.fade_time.apply(lambda t: int(t.split(':')[0]))
    primary['time_bucket'] = primary.fade_hour.map(lambda h:
        'Morning (9:30-10:30)' if h < 11 else
        'Midday (11:00-13:00)' if h < 13 else
        'Afternoon (13:00-16:00)')

    lines.append("| Time Bucket | FADEs | MFE 30m | MAE 30m | Net 30m | Win% |")
    lines.append("|-------------|-------|---------|---------|---------|------|")
    for tb in ['Morning (9:30-10:30)', 'Midday (11:00-13:00)', 'Afternoon (13:00-16:00)']:
        sub = primary[primary.time_bucket == tb]
        if len(sub) == 0:
            continue
        w = (sub.fade_mfe_30m > abs(sub.fade_mae_30m)).mean() * 100
        net = sub.fade_mfe_30m.mean() + sub.fade_mae_30m.mean()
        lines.append(f"| {tb} | {len(sub)} | {sub.fade_mfe_30m.mean():.3f} | {sub.fade_mae_30m.mean():.3f} | {net:.3f} | {w:.1f}% |")
    lines.append("")

    # =====================================================
    # SECTION 7: By Direction
    # =====================================================
    lines.append("## 7. By FADE Direction")
    lines.append("")
    lines.append("| FADE Dir | Count | MFE 30m | MAE 30m | Net 30m | Win% 30m | MFE 60m | Net 60m |")
    lines.append("|----------|-------|---------|---------|---------|----------|---------|---------|")

    for d in ['bull', 'bear']:
        sub = primary[primary.fade_direction == d]
        if len(sub) == 0:
            continue
        w30 = (sub.fade_mfe_30m > abs(sub.fade_mae_30m)).mean() * 100
        net30 = sub.fade_mfe_30m.mean() + sub.fade_mae_30m.mean()
        net60 = sub.fade_mfe_60m.mean() + sub.fade_mae_60m.mean()
        lines.append(f"| {d} | {len(sub)} | {sub.fade_mfe_30m.mean():.3f} | {sub.fade_mae_30m.mean():.3f} | {net30:.3f} | {w30:.1f}% | {sub.fade_mfe_60m.mean():.3f} | {net60:.3f} |")
    lines.append("")

    # =====================================================
    # SECTION 8: By Level Type
    # =====================================================
    lines.append("## 8. By Level Type")
    lines.append("")
    lines.append("| Level Type | FADEs | MFE 30m | MAE 30m | Net 30m | Win% |")
    lines.append("|------------|-------|---------|---------|---------|------|")

    for lt in ['HIGH', 'LOW']:
        sub = primary[primary.orig_level_type == lt]
        if len(sub) == 0:
            continue
        w = (sub.fade_mfe_30m > abs(sub.fade_mae_30m)).mean() * 100
        net = sub.fade_mfe_30m.mean() + sub.fade_mae_30m.mean()
        lines.append(f"| {lt} | {len(sub)} | {sub.fade_mfe_30m.mean():.3f} | {sub.fade_mae_30m.mean():.3f} | {net:.3f} | {w:.1f}% |")
    lines.append("")

    # By specific level names (top 10 by count)
    lines.append("### By Specific Level")
    lines.append("")
    lines.append("| Level | FADEs | MFE 30m | MAE 30m | Net 30m | Win% |")
    lines.append("|-------|-------|---------|---------|---------|------|")
    top_levels = primary.orig_levels.value_counts().head(10).index
    for lv in top_levels:
        sub = primary[primary.orig_levels == lv]
        w = (sub.fade_mfe_30m > abs(sub.fade_mae_30m)).mean() * 100
        net = sub.fade_mfe_30m.mean() + sub.fade_mae_30m.mean()
        lines.append(f"| {lv} | {len(sub)} | {sub.fade_mfe_30m.mean():.3f} | {sub.fade_mae_30m.mean():.3f} | {net:.3f} | {w:.1f}% |")
    lines.append("")

    # =====================================================
    # SECTION 9: By Original Signal Type (BRK vs REV)
    # =====================================================
    lines.append("## 9. By Original Signal Type")
    lines.append("")
    lines.append("| Orig Type | FADEs | MFE 30m | MAE 30m | Net 30m | Win% |")
    lines.append("|-----------|-------|---------|---------|---------|------|")
    for t in ['BRK', 'REV']:
        sub = primary[primary.orig_type == t]
        if len(sub) == 0:
            continue
        w = (sub.fade_mfe_30m > abs(sub.fade_mae_30m)).mean() * 100
        net = sub.fade_mfe_30m.mean() + sub.fade_mae_30m.mean()
        lines.append(f"| {t} | {len(sub)} | {sub.fade_mfe_30m.mean():.3f} | {sub.fade_mae_30m.mean():.3f} | {net:.3f} | {w:.1f}% |")
    lines.append("")

    # =====================================================
    # SECTION 10: EMA alignment of FADE
    # =====================================================
    lines.append("## 10. EMA Alignment at FADE")
    lines.append("")
    lines.append("Does the FADE direction align with EMA? (orig_ema was for original signal)")
    lines.append("")

    # If original was bull + ema=bull, FADE is bear + ema=bull → FADE is counter-EMA
    # If original was bull + ema=bear, FADE is bear + ema=bear → FADE is with-EMA
    primary['fade_ema_aligned'] = primary.apply(lambda r:
        (r.fade_direction == 'bull' and r.orig_ema == 'bull') or
        (r.fade_direction == 'bear' and r.orig_ema == 'bear') or
        (r.fade_direction == 'bull' and r.orig_ema == 'bear') or  # This can't both be true
        False, axis=1)
    # Simpler: FADE ema aligned = FADE direction matches ema
    # But orig_ema was the EMA state at original signal time, same bar roughly
    primary['fade_ema_aligned'] = primary.apply(lambda r:
        (r.fade_direction == 'bull' and r.orig_ema in ['bull']) or
        (r.fade_direction == 'bear' and r.orig_ema in ['bear']),
        axis=1)

    lines.append("| EMA Aligned? | FADEs | MFE 30m | MAE 30m | Net 30m | Win% |")
    lines.append("|--------------|-------|---------|---------|---------|------|")
    for aligned in [True, False]:
        sub = primary[primary.fade_ema_aligned == aligned]
        if len(sub) == 0:
            continue
        w = (sub.fade_mfe_30m > abs(sub.fade_mae_30m)).mean() * 100
        net = sub.fade_mfe_30m.mean() + sub.fade_mae_30m.mean()
        label = "Yes" if aligned else "No"
        lines.append(f"| {label} | {len(sub)} | {sub.fade_mfe_30m.mean():.3f} | {sub.fade_mae_30m.mean():.3f} | {net:.3f} | {w:.1f}% |")

    # Also check 'mixed' ema
    mixed = primary[primary.orig_ema == 'mixed']
    if len(mixed) > 0:
        w = (mixed.fade_mfe_30m > abs(mixed.fade_mae_30m)).mean() * 100
        net = mixed.fade_mfe_30m.mean() + mixed.fade_mae_30m.mean()
        lines.append(f"| Mixed EMA | {len(mixed)} | {mixed.fade_mfe_30m.mean():.3f} | {mixed.fade_mae_30m.mean():.3f} | {net:.3f} | {w:.1f}% |")
    lines.append("")

    # =====================================================
    # SECTION 11: Combined best filters
    # =====================================================
    lines.append("## 11. Filter Combinations")
    lines.append("")

    filters = {
        'All FADEs': primary,
        'EMA aligned': primary[primary.fade_ema_aligned == True],
        'Morning only': primary[primary.fade_hour < 11],
        'Morning + EMA aligned': primary[(primary.fade_hour < 11) & (primary.fade_ema_aligned == True)],
        'Crossback ≤2 bars': primary[primary.crossback_bars <= 2],
        'Crossback ≤2 + EMA': primary[(primary.crossback_bars <= 2) & (primary.fade_ema_aligned == True)],
        'BRK only': primary[primary.orig_type == 'BRK'],
        'BRK + EMA aligned': primary[(primary.orig_type == 'BRK') & (primary.fade_ema_aligned == True)],
        'After CONF ✗': primary[primary.orig_conf == '✗'],
        'After CONF ✗ + EMA': primary[(primary.orig_conf == '✗') & (primary.fade_ema_aligned == True)],
    }

    lines.append("| Filter | N | MFE 30m | MAE 30m | Net 30m | Win% | Total ATR |")
    lines.append("|--------|---|---------|---------|---------|------|-----------|")
    for name, sub in filters.items():
        if len(sub) == 0:
            lines.append(f"| {name} | 0 | - | - | - | - | - |")
            continue
        w = (sub.fade_mfe_30m > abs(sub.fade_mae_30m)).mean() * 100
        net = sub.fade_mfe_30m.mean() + sub.fade_mae_30m.mean()
        total = (sub.fade_mfe_30m + sub.fade_mae_30m).sum()
        lines.append(f"| {name} | {len(sub)} | {sub.fade_mfe_30m.mean():.3f} | {sub.fade_mae_30m.mean():.3f} | {net:.3f} | {w:.1f}% | {total:.1f} |")
    lines.append("")

    # =====================================================
    # SECTION 12: Original signal outcome for FADE signals
    # =====================================================
    lines.append("## 12. Original Signal Outcome (Signals That Became FADEs)")
    lines.append("")
    lines.append("These original signals failed (price reversed). How bad were they?")
    lines.append("")
    lines.append(f"- Original MFE mean: {primary.orig_mfe.mean():.3f} ATR (lower = signal was weak)")
    lines.append(f"- Original MAE mean: {primary.orig_mae.mean():.3f} ATR (more negative = bigger adverse)")
    lines.append(f"- Original Net: {primary.orig_mfe.mean() + primary.orig_mae.mean():.3f} ATR")
    lines.append("")
    # Compare with ALL signals
    lines.append(f"- All signals MFE mean: {signals.mfe.mean():.3f} ATR")
    lines.append(f"- All signals MAE mean: {signals.mae.mean():.3f} ATR")
    lines.append(f"- All signals Net: {signals.mfe.mean() + signals.mae.mean():.3f} ATR")
    lines.append("")

    # =====================================================
    # SECTION 13: Key conclusions
    # =====================================================
    lines.append("## 13. Key Conclusions")
    lines.append("")

    total_net = primary.fade_mfe_30m.mean() + primary.fade_mae_30m.mean()
    total_atr = (primary.fade_mfe_30m + primary.fade_mae_30m).sum()

    if total_net > 0:
        lines.append(f"**VERDICT: New FADE is NET POSITIVE** (+{total_net:.3f} ATR/signal, {total_atr:.1f} total ATR)")
    else:
        lines.append(f"**VERDICT: New FADE is NET NEGATIVE** ({total_net:.3f} ATR/signal, {total_atr:.1f} total ATR)")
    lines.append("")
    lines.append(f"- New FADE produces **{len(primary)} signals** vs old FADE's 79 (from v3.0b CONF-dependent)")
    lines.append(f"- Crossback within 6 bars (30 min) = primary definition")
    lines.append(f"- {pos_syms}/{len(primary.symbol.unique())} symbols are net positive")
    lines.append("")

    # Best practical definition
    best_name = None
    best_net = -999
    best_n = 0
    for name, sub in filters.items():
        if len(sub) < 20:  # minimum sample
            continue
        net = sub.fade_mfe_30m.mean() + sub.fade_mae_30m.mean()
        if net > best_net:
            best_net = net
            best_name = name
            best_n = len(sub)

    if best_name:
        lines.append(f"**Best practical filter: {best_name}** (N={best_n}, Net={best_net:.3f} ATR)")
    lines.append("")

    report = '\n'.join(lines)
    return report, primary


def main():
    print("=" * 60)
    print("FADE Resurrection Backtest")
    print("=" * 60)

    df, signals = run_backtest()

    if len(df) == 0:
        print("No FADE candidates found!")
        return

    report, primary = analyze_results(df, signals)

    # Save report
    with open(REPORT_PATH, 'w') as f:
        f.write(report)
    print(f"\nReport saved to: {REPORT_PATH}")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    primary_6 = df.sort_values('fade_window').drop_duplicates(
        subset=['symbol', 'date', 'orig_time', 'orig_direction'], keep='first'
    )
    primary_6 = primary_6[primary_6.fade_window <= 6]
    print(f"Total unique FADEs (≤6 bars): {len(primary_6)}")
    print(f"Mean MFE 30m: {primary_6.fade_mfe_30m.mean():.3f} ATR")
    print(f"Mean MAE 30m: {primary_6.fade_mae_30m.mean():.3f} ATR")
    print(f"Net 30m: {primary_6.fade_mfe_30m.mean() + primary_6.fade_mae_30m.mean():.3f} ATR")
    win = (primary_6.fade_mfe_30m > abs(primary_6.fade_mae_30m)).mean() * 100
    print(f"Win rate: {win:.1f}%")
    total = (primary_6.fade_mfe_30m + primary_6.fade_mae_30m).sum()
    print(f"Total ATR: {total:.1f}")


if __name__ == '__main__':
    main()
