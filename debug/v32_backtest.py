#!/usr/bin/env python3
"""
KLB v3.2 vs v3.1 Backtest
==========================
Comprehensive comparison over last 30 trading days across 15 symbols.

Changes in v3.2:
  1. ORB L Bull REV Suppress
  2. 4 New Midday Levels (Today Open REV, PD Close REV, Week Open BRK, Month Open BRK)
  3. EXREV Bypass (bear REV body<30% bypasses EMA+quality gates)
  4. FADE Resurrection (counter-EMA CONF fail → with-EMA cross back within 6 bars)
  5. HIGH→REV Reassignment (bull BRK at HIGH levels → bull REV)

Data: IB 5-minute bars (Berlin tz → US/Eastern), 14-period ATR from daily bars.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import time as dtime
import warnings
warnings.filterwarnings('ignore')

# ── Config ────────────────────────────────────────────────────────────────────
SYMBOLS = ['SPY','AAPL','AMD','AMZN','GLD','GOOGL','META','MSFT','NFLX','NVDA','QQQ','SLV','TSLA','TSM','XLE']
BAR_DIR = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars/')
OUT_DIR = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug/')
N_DAYS = 30
TOUCH_PCT = 0.001   # 0.1% touch threshold
MFE_BARS = 6        # measure over 6 bars (30 min on 5m)
EMA_PERIOD = 21
VOL_AVG_PERIOD = 20
ATR_PERIOD = 14

HIGH_LEVELS = {'PD High', 'PM High', 'ORB High', 'Week High'}
LOW_LEVELS  = {'PD Low', 'PM Low', 'ORB Low', 'Week Low'}

# ── Data Loading ──────────────────────────────────────────────────────────────
def load_5m(symbol):
    """Load 5-minute bars, convert to ET, filter RTH."""
    fp = BAR_DIR / f'{symbol.lower()}_5_mins_ib.parquet'
    df = pd.read_parquet(fp)
    dt = pd.to_datetime(df['date'])
    if dt.dt.tz is None:
        dt = dt.dt.tz_localize('Europe/Berlin')
    df['date'] = dt.dt.tz_convert('US/Eastern')
    df = df.set_index('date').sort_index()
    # RTH filter: 9:30-16:00 ET (bar timestamp = bar START, so 15:55 is last bar)
    df = df.between_time('09:30', '15:55')
    return df

def load_daily(symbol):
    """Load daily bars for ATR computation."""
    fp = BAR_DIR / f'{symbol.lower()}_1_day_ib.parquet'
    df = pd.read_parquet(fp)
    dt = pd.to_datetime(df['date'])
    # Daily bars are tz-naive, just use as-is for ATR computation
    if dt.dt.tz is not None:
        dt = dt.dt.tz_convert('US/Eastern')
    df['date'] = dt
    df = df.set_index('date').sort_index()
    return df

def compute_atr(daily_df, period=ATR_PERIOD):
    """Compute ATR from daily bars. Returns Series indexed by date (date only)."""
    tr = pd.DataFrame({
        'hl': daily_df['high'] - daily_df['low'],
        'hc': (daily_df['high'] - daily_df['close'].shift(1)).abs(),
        'lc': (daily_df['low'] - daily_df['close'].shift(1)).abs()
    })
    tr['tr'] = tr.max(axis=1)
    atr = tr['tr'].ewm(span=period, adjust=False).mean()
    atr.index = atr.index.date
    return atr

# ── Indicator Computation ─────────────────────────────────────────────────────
def add_indicators(df):
    """Add EMA, volume ratio, body ratio, VWAP to 5m bars."""
    df = df.copy()
    df['ema21'] = df['close'].ewm(span=EMA_PERIOD, adjust=False).mean()
    df['vol_avg'] = df['volume'].rolling(VOL_AVG_PERIOD, min_periods=1).mean()
    df['vol_ratio'] = df['volume'] / df['vol_avg'].replace(0, np.nan)
    rng = df['high'] - df['low']
    df['body'] = (df['close'] - df['open']).abs()
    df['body_ratio'] = df['body'] / rng.replace(0, np.nan)
    df['body_ratio'] = df['body_ratio'].fillna(0)

    # VWAP (reset daily)
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    df['trade_date'] = df.index.date
    df['cum_tpv'] = df.groupby('trade_date').apply(lambda g: (g['tp'] * g['volume']).cumsum()).droplevel(0)
    df['cum_vol'] = df.groupby('trade_date')['volume'].cumsum()
    df['vwap'] = df['cum_tpv'] / df['cum_vol'].replace(0, np.nan)

    # EMA direction: bull if close > ema, bear if close < ema
    df['ema_bull'] = df['close'] > df['ema21']

    return df

# ── Level Computation ─────────────────────────────────────────────────────────
def compute_levels_for_day(day_bars, prior_day_bars, week_bars_prior, month_open, week_open):
    """
    Compute all price levels for a given trading day.
    Returns dict of {level_name: price}.
    """
    levels = {}

    if prior_day_bars is not None and len(prior_day_bars) > 0:
        levels['PD High'] = prior_day_bars['high'].max()
        levels['PD Low'] = prior_day_bars['low'].min()
        levels['PD Close'] = prior_day_bars['close'].iloc[-1]

    # ORB: first 30 min (9:30-10:00) = first 6 bars of 5m
    orb_bars = day_bars.between_time('09:30', '09:55')
    if len(orb_bars) >= 1:
        levels['ORB High'] = orb_bars['high'].max()
        levels['ORB Low'] = orb_bars['low'].min()

    # PM High/Low: use 9:00-9:25 bars if available (pre-market proxy)
    # Since we filter RTH, we load pre-market separately
    # For now, skip PM levels (we only have RTH data reliably)

    # Today's Open
    if len(day_bars) > 0:
        levels['Today Open'] = day_bars['open'].iloc[0]

    # Week Open & Month Open (passed in)
    if week_open is not None:
        levels['Week Open'] = week_open
    if month_open is not None:
        levels['Month Open'] = month_open

    # Week High/Low from prior days this week
    if week_bars_prior is not None and len(week_bars_prior) > 0:
        levels['Week High'] = week_bars_prior['high'].max()
        levels['Week Low'] = week_bars_prior['low'].min()

    # NOTE: Yest High/Low omitted -- identical to PD High/Low, would create duplicates

    return levels

# ── Signal Detection ──────────────────────────────────────────────────────────
def detect_signals(day_bars, levels, atr_val, version='v31'):
    """
    Detect all signals for a given day.
    Returns list of signal dicts.

    version: 'v31' or 'v32'
    """
    signals = []
    bars = day_bars.reset_index()
    n = len(bars)

    # Track failed breakouts for FADE detection (v3.2 only)
    failed_breakouts = []  # list of (bar_idx, level_name, level_price, original_direction)

    # Cooldown: once a signal fires at a level, block same level for 6 bars
    # Key: (level_name, sig_dir) -> last bar_idx that fired
    cooldown = {}
    COOLDOWN_BARS = 6

    for i in range(1, n):  # start from bar 1 to have a prior bar
        row = bars.iloc[i]
        prev = bars.iloc[i - 1]
        t = row['date']
        et_time = t.time()

        # Skip first bar (9:30) - used for ORB calc
        # Actually, signals can fire from 9:35 onwards
        if et_time < dtime(9, 35):
            continue

        is_post_950 = et_time >= dtime(9, 50)
        ema_bull = row['ema_bull']
        body_ratio = row['body_ratio']
        vol_ratio = row['vol_ratio'] if not np.isnan(row['vol_ratio']) else 0

        for level_name, level_price in levels.items():
            if level_price is None or np.isnan(level_price):
                continue

            touch_threshold = level_price * TOUCH_PCT
            bar_high = row['high']
            bar_low = row['low']
            bar_close = row['close']
            bar_open = row['open']
            prev_close = prev['close']

            # Determine approach side
            approached_from_below = prev_close < level_price
            approached_from_above = prev_close > level_price

            # Did bar touch the level?
            touched = bar_low <= level_price + touch_threshold and bar_high >= level_price - touch_threshold

            # Did bar cross through the level?
            crossed_above = prev_close <= level_price and bar_close > level_price + touch_threshold
            crossed_below = prev_close >= level_price and bar_close < level_price - touch_threshold

            # Bounced = touched but closed on same side as approach
            bounced_up = touched and approached_from_below and bar_close < level_price
            bounced_down = touched and approached_from_above and bar_close > level_price

            # ── Determine which signals are valid at this level ──
            sig_type = None
            sig_dir = None

            # --- BRK signals ---
            if crossed_above and approached_from_below:
                # Bull breakout
                sig_type = 'BRK'
                sig_dir = 'bull'
            elif crossed_below and approached_from_above:
                # Bear breakout
                sig_type = 'BRK'
                sig_dir = 'bear'

            # --- REV signals ---
            elif bounced_up and approached_from_below:
                # Bear reversal (came from below, bounced back down)
                sig_type = 'REV'
                sig_dir = 'bear'
            elif bounced_down and approached_from_above:
                # Bull reversal (came from above, bounced back up)
                sig_type = 'REV'
                sig_dir = 'bull'

            if sig_type is None:
                continue

            # ── Level-type filtering ──
            # Determine what signals each level allows
            is_high_level = level_name in HIGH_LEVELS
            is_low_level = level_name in LOW_LEVELS
            is_orb_low = level_name == 'ORB Low'
            is_pd_mid = level_name == 'PD Mid'  # not used currently
            is_today_open = level_name == 'Today Open'
            is_pd_close = level_name == 'PD Close'
            is_week_open = level_name == 'Week Open'
            is_month_open = level_name == 'Month Open'

            allowed = False

            if version == 'v31':
                # v3.1 rules:
                # HIGH levels: bull BRK, bear REV
                # LOW levels: bear BRK (bear breakout below), bull REV (bounce off low)
                # But also: bear BRK at HIGH is not standard... Let me think carefully.

                # Actually in KLB:
                # HIGH levels: expect bull BRK through resistance, bear REV at resistance
                # LOW levels: expect bear BRK through support, bull REV at support (bounce)
                # ORB L: bull REV fires (bounces off ORB low)

                if is_high_level:
                    if sig_type == 'BRK' and sig_dir == 'bull':
                        allowed = True
                    elif sig_type == 'REV' and sig_dir == 'bear':
                        allowed = True
                elif is_low_level:
                    if sig_type == 'BRK' and sig_dir == 'bear':
                        allowed = True
                    elif sig_type == 'REV' and sig_dir == 'bull':
                        allowed = True
                elif level_name in ('PD High', 'PD Low', 'PD Close'):
                    # PD High = high level, PD Low = low level
                    # Already handled above via HIGH_LEVELS/LOW_LEVELS
                    # PD Close: not a level in v3.1
                    allowed = False
                elif level_name in ('Today Open', 'Week Open', 'Month Open'):
                    # Not levels in v3.1
                    allowed = False
                else:
                    # Generic levels - allow BRK both ways, REV both ways
                    allowed = True

            elif version == 'v32':
                # v3.2 rules:
                if is_high_level:
                    # Change 5: HIGH→REV - bull BRK disabled, bull REV added
                    if sig_type == 'REV' and sig_dir == 'bull':
                        allowed = True  # NEW in v3.2
                    elif sig_type == 'REV' and sig_dir == 'bear':
                        allowed = True  # unchanged
                    elif sig_type == 'BRK' and sig_dir == 'bull':
                        allowed = False  # REMOVED in v3.2
                    elif sig_type == 'BRK' and sig_dir == 'bear':
                        allowed = True  # bear BRK at highs (breakdown from above)
                elif is_low_level:
                    if is_orb_low and sig_type == 'REV' and sig_dir == 'bull':
                        allowed = False  # Change 1: ORB L Bull REV suppress
                    elif sig_type == 'BRK' and sig_dir == 'bear':
                        allowed = True
                    elif sig_type == 'REV' and sig_dir == 'bull':
                        allowed = True  # bull REV at non-ORB lows still OK
                    else:
                        allowed = True
                elif is_today_open:
                    # Change 2: New level - REV signal, no EMA gate
                    if sig_type == 'REV':
                        allowed = True
                    else:
                        allowed = False
                elif is_pd_close:
                    # Change 2: New level - REV signal, no EMA gate
                    if sig_type == 'REV':
                        allowed = True
                    else:
                        allowed = False
                elif is_week_open:
                    # Change 2: New level - BRK signal, full gates
                    if sig_type == 'BRK':
                        allowed = True
                    else:
                        allowed = False
                elif is_month_open:
                    # Change 2: New level - BRK signal, full gates
                    if sig_type == 'BRK':
                        allowed = True
                    else:
                        allowed = False
                else:
                    allowed = True

            if not allowed:
                continue

            # ── Gate checks ──
            # Determine if this level/signal bypasses EMA gate
            no_ema_gate = False
            if version == 'v32':
                # Today Open and PD Close are REV with no EMA gate (like PD Mid)
                if level_name in ('Today Open', 'PD Close'):
                    no_ema_gate = True

            # EXREV bypass (Change 3, v3.2 only)
            is_exrev = False
            if version == 'v32' and sig_type == 'REV' and sig_dir == 'bear' and body_ratio < 0.30:
                is_exrev = True
                no_ema_gate = True  # bypasses EMA gate
                # Also bypasses body quality gate

            # Body quality gate (body > 30%)
            if body_ratio < 0.30 and not is_exrev:
                continue

            # Volume gate (> 1x average)
            if vol_ratio < 1.0:
                continue

            # EMA gate: after 9:50, signal direction must match EMA
            if is_post_950 and not no_ema_gate:
                ema_aligned = (sig_dir == 'bull' and ema_bull) or (sig_dir == 'bear' and not ema_bull)
                if not ema_aligned:
                    # Track for FADE (v3.2 Change 4)
                    if version == 'v32' and sig_type == 'BRK':
                        failed_breakouts.append({
                            'bar_idx': i,
                            'level_name': level_name,
                            'level_price': level_price,
                            'sig_dir': sig_dir,
                            'ema_bull': ema_bull
                        })
                    continue

            # ── Cooldown check ──
            cd_key = (level_name, sig_dir)
            if cd_key in cooldown and i - cooldown[cd_key] < COOLDOWN_BARS:
                continue  # too soon since last signal at this level+direction

            # ── Signal passed all gates ──
            cooldown[cd_key] = i  # update cooldown
            signals.append({
                'bar_idx': i,
                'time': t,
                'level_name': level_name,
                'level_price': level_price,
                'sig_type': 'EXREV' if is_exrev else sig_type,
                'sig_dir': sig_dir,
                'body_ratio': body_ratio,
                'vol_ratio': vol_ratio,
                'ema_bull': ema_bull,
                'close': bar_close,
                'atr': atr_val,
            })

            # Also track successful breakouts for potential FADE (if they fail later)
            if sig_type == 'BRK' and version == 'v32':
                # We'll check for failures below
                pass

    # ── FADE detection (v3.2 Change 4) ──
    if version == 'v32':
        # For BRK signals that PASSED gates but then fail (price returns within 3 bars),
        # AND the original was counter-EMA... wait, the spec says:
        # "After a CONF fail (failed breakout), if price was moving counter-EMA,
        #  watch for 6 bars for price to cross back through level with-EMA"
        #
        # But counter-EMA BRKs are already filtered by EMA gate...
        # The FADE logic fires on breakouts that WERE allowed but then fail.
        # Let me re-read: "After a CONF X (failed breakout), if price was moving counter-EMA"
        # This means the original breakout was counter-EMA. But those get filtered.
        # UNLESS they happened pre-9:50 (when EMA gate doesn't suppress).
        #
        # Also: failed_breakouts above captures counter-EMA BRKs that were SUPPRESSED by EMA gate.
        # The FADE watches these suppressed signals for a cross-back.

        for fb in failed_breakouts:
            fb_idx = fb['bar_idx']
            lp = fb['level_price']
            # Original was counter-EMA (that's why it was suppressed)
            # FADE direction = WITH EMA = opposite of original signal direction
            fade_dir = 'bull' if fb['ema_bull'] else 'bear'

            # Watch 6 bars after the failed breakout
            for j in range(fb_idx + 1, min(fb_idx + 7, n)):
                check_row = bars.iloc[j]
                # Check if price crosses back through level WITH EMA direction
                if fade_dir == 'bull' and check_row['close'] > lp + lp * TOUCH_PCT:
                    # Bullish FADE: price crossed back above level
                    signals.append({
                        'bar_idx': j,
                        'time': check_row['date'],
                        'level_name': fb['level_name'],
                        'level_price': lp,
                        'sig_type': 'FADE',
                        'sig_dir': fade_dir,
                        'body_ratio': check_row['body_ratio'] if 'body_ratio' in check_row else 0,
                        'vol_ratio': check_row['vol_ratio'] if 'vol_ratio' in check_row else 0,
                        'ema_bull': fb['ema_bull'],
                        'close': check_row['close'],
                        'atr': fb.get('atr', atr_val) if 'atr' in fb else atr_val,
                    })
                    break  # only one FADE per watch period
                elif fade_dir == 'bear' and check_row['close'] < lp - lp * TOUCH_PCT:
                    signals.append({
                        'bar_idx': j,
                        'time': check_row['date'],
                        'level_name': fb['level_name'],
                        'level_price': lp,
                        'sig_type': 'FADE',
                        'sig_dir': fade_dir,
                        'body_ratio': check_row['body_ratio'] if 'body_ratio' in check_row else 0,
                        'vol_ratio': check_row['vol_ratio'] if 'vol_ratio' in check_row else 0,
                        'ema_bull': fb['ema_bull'],
                        'close': check_row['close'],
                        'atr': fb.get('atr', atr_val) if 'atr' in fb else atr_val,
                    })
                    break

    return signals

# ── Outcome Measurement ───────────────────────────────────────────────────────
def measure_outcomes(signals, day_bars):
    """
    For each signal, measure MFE and MAE over next 6 bars.
    Classifies as GOOD/BAD/SCRATCH.
    """
    bars = day_bars.reset_index()
    n = len(bars)

    for sig in signals:
        idx = sig['bar_idx']
        atr = sig['atr']
        direction = sig['sig_dir']
        entry = sig['close']

        if atr is None or atr == 0 or np.isnan(atr):
            sig['mfe'] = 0
            sig['mae'] = 0
            sig['mfe_atr'] = 0
            sig['mae_atr'] = 0
            sig['pnl_atr'] = 0
            sig['outcome'] = 'SCRATCH'
            continue

        mfe = 0
        mae = 0
        mae_3bar = 0

        for j in range(idx + 1, min(idx + MFE_BARS + 1, n)):
            future = bars.iloc[j]
            if direction == 'bull':
                excursion_fav = future['high'] - entry
                excursion_adv = entry - future['low']
            else:
                excursion_fav = entry - future['low']
                excursion_adv = future['high'] - entry

            mfe = max(mfe, excursion_fav)
            mae = max(mae, excursion_adv)
            if j <= idx + 3:
                mae_3bar = max(mae_3bar, excursion_adv)

        mfe_atr = mfe / atr
        mae_atr = mae / atr
        mae_3bar_atr = mae_3bar / atr

        # Classification
        if mfe_atr > 0.30 and mae_atr < 0.15:
            outcome = 'GOOD'
        elif mae_3bar_atr > 0.15:
            outcome = 'BAD'
        else:
            outcome = 'SCRATCH'

        # P&L proxy: simplified MFE - MAE in ATR
        pnl_atr = mfe_atr - mae_atr

        sig['mfe'] = mfe
        sig['mae'] = mae
        sig['mfe_atr'] = mfe_atr
        sig['mae_atr'] = mae_atr
        sig['pnl_atr'] = pnl_atr
        sig['outcome'] = outcome

    return signals

# ── Main Backtest Logic ───────────────────────────────────────────────────────
def run_backtest():
    """Run the full v3.1 vs v3.2 backtest."""
    all_signals_v31 = []
    all_signals_v32 = []

    for symbol in SYMBOLS:
        print(f'  Processing {symbol}...', flush=True)

        try:
            df_5m = load_5m(symbol)
            df_daily = load_daily(symbol)
        except Exception as e:
            print(f'    ERROR loading {symbol}: {e}')
            continue

        atr_series = compute_atr(df_daily)
        df_5m = add_indicators(df_5m)

        # Get trading days (last N_DAYS)
        trade_dates = sorted(df_5m.index.date)
        unique_dates = sorted(set(trade_dates))
        if len(unique_dates) < N_DAYS + 2:
            print(f'    WARNING: only {len(unique_dates)} days for {symbol}')
        target_dates = unique_dates[-(N_DAYS + 1):]  # +1 for prior day context

        # Find week starts and month starts for Week Open / Month Open
        week_open_map = {}   # date -> week open price
        month_open_map = {}  # date -> month open price

        for d in unique_dates:
            day_data = df_5m[df_5m.index.date == d]
            if len(day_data) == 0:
                continue
            dt = pd.Timestamp(d)
            # Monday = 0
            if dt.weekday() == 0:
                week_open_map[d] = day_data['open'].iloc[0]
            # 1st of month
            if dt.day <= 3:
                # Find first trading day of month
                month_start = pd.Timestamp(d.replace(day=1))
                month_dates = [x for x in unique_dates if x.month == d.month and x.year == d.year]
                if month_dates and d == month_dates[0]:
                    month_open_map[d] = day_data['open'].iloc[0]

        # Propagate week_open and month_open forward
        current_week_open = None
        current_month_open = None
        week_open_by_date = {}
        month_open_by_date = {}

        for d in unique_dates:
            if d in week_open_map:
                current_week_open = week_open_map[d]
            week_open_by_date[d] = current_week_open
            if d in month_open_map:
                current_month_open = month_open_map[d]
            month_open_by_date[d] = current_month_open

        # Process each day
        for di in range(1, len(target_dates)):
            d = target_dates[di]
            d_prev = target_dates[di - 1]

            # Skip the extra prior-day-context day
            if d not in unique_dates[-(N_DAYS):]:
                continue

            day_bars = df_5m[df_5m.index.date == d]
            prior_bars = df_5m[df_5m.index.date == d_prev]

            if len(day_bars) < 6:  # need at least ORB bars
                continue

            # ATR
            atr_val = atr_series.get(d_prev, None)
            if atr_val is None or np.isnan(atr_val):
                # fallback: try current day or nearest
                for fallback_d in [d, d_prev]:
                    atr_val = atr_series.get(fallback_d, None)
                    if atr_val is not None and not np.isnan(atr_val):
                        break
            if atr_val is None or np.isnan(atr_val):
                atr_val = (day_bars['high'].max() - day_bars['low'].min())  # rough fallback

            # Week bars prior (for week high/low)
            dt_d = pd.Timestamp(d)
            # Find Monday of this week
            days_since_monday = dt_d.weekday()
            monday = d
            if days_since_monday > 0:
                # Get all bars from Monday to day before d
                week_dates = [x for x in unique_dates if x >= (pd.Timestamp(d) - pd.Timedelta(days=days_since_monday)).date() and x < d]
                week_bars_prior = df_5m[np.isin(df_5m.index.date, week_dates)] if week_dates else None
            else:
                week_bars_prior = None  # Monday itself - no prior week data

            # Levels
            levels = compute_levels_for_day(
                day_bars, prior_bars, week_bars_prior,
                month_open=month_open_by_date.get(d),
                week_open=week_open_by_date.get(d)
            )

            # Remove duplicate levels (Yest High = PD High, etc.)
            # Keep both names for tracking but deduplicate prices
            # Actually, keep them separate for signal-type tracking

            # Detect signals for v3.1
            sigs_v31 = detect_signals(day_bars, levels, atr_val, version='v31')
            sigs_v31 = measure_outcomes(sigs_v31, day_bars)
            for s in sigs_v31:
                s['symbol'] = symbol
                s['trade_date'] = d
            all_signals_v31.extend(sigs_v31)

            # Detect signals for v3.2
            sigs_v32 = detect_signals(day_bars, levels, atr_val, version='v32')
            sigs_v32 = measure_outcomes(sigs_v32, day_bars)
            for s in sigs_v32:
                s['symbol'] = symbol
                s['trade_date'] = d
            all_signals_v32.extend(sigs_v32)

    return all_signals_v31, all_signals_v32

# ── Analysis Functions ────────────────────────────────────────────────────────
def signal_stats(signals, label=''):
    """Compute aggregate stats for a list of signals."""
    if not signals:
        return {'n': 0, 'win_rate': 0, 'avg_mfe': 0, 'avg_mae': 0, 'net_atr': 0, 'label': label}
    n = len(signals)
    wins = sum(1 for s in signals if s['outcome'] == 'GOOD')
    losses = sum(1 for s in signals if s['outcome'] == 'BAD')
    scratches = sum(1 for s in signals if s['outcome'] == 'SCRATCH')
    avg_mfe = np.mean([s['mfe_atr'] for s in signals])
    avg_mae = np.mean([s['mae_atr'] for s in signals])
    net_atr = sum(s['pnl_atr'] for s in signals)
    win_rate = wins / n * 100 if n > 0 else 0
    return {
        'n': n, 'wins': wins, 'losses': losses, 'scratches': scratches,
        'win_rate': win_rate, 'avg_mfe': avg_mfe, 'avg_mae': avg_mae,
        'net_atr': net_atr, 'label': label
    }

def categorize_by_change(signals_v31, signals_v32):
    """
    Categorize signals by which v3.2 change they belong to.
    Returns dict of change_name -> {'v31': [...], 'v32': [...]}
    """
    changes = {
        'Change 1: ORB L Bull REV Suppress': {'v31': [], 'v32': [], 'desc': 'Suppress bull REV at ORB Low'},
        'Change 2: New Midday Levels': {'v31': [], 'v32': [], 'desc': 'Today Open REV, PD Close REV, Week Open BRK, Month Open BRK'},
        'Change 3: EXREV Bypass': {'v31': [], 'v32': [], 'desc': 'Bear REV body<30% bypasses EMA+quality gates'},
        'Change 4: FADE Resurrection': {'v31': [], 'v32': [], 'desc': 'Counter-EMA fail → with-EMA cross back within 6 bars'},
        'Change 5: HIGH→REV Reassignment': {'v31': [], 'v32': [], 'desc': 'Bull BRK at HIGH levels → Bull REV'},
    }

    # Change 1: ORB L bull REV exists in v3.1 but NOT in v3.2
    for s in signals_v31:
        if s['level_name'] == 'ORB Low' and s['sig_type'] == 'REV' and s['sig_dir'] == 'bull':
            changes['Change 1: ORB L Bull REV Suppress']['v31'].append(s)
    # v3.2 should have none of these
    for s in signals_v32:
        if s['level_name'] == 'ORB Low' and s['sig_type'] == 'REV' and s['sig_dir'] == 'bull':
            changes['Change 1: ORB L Bull REV Suppress']['v32'].append(s)

    # Change 2: New midday levels (only in v3.2)
    new_levels = {'Today Open', 'PD Close', 'Week Open', 'Month Open'}
    for s in signals_v32:
        if s['level_name'] in new_levels:
            changes['Change 2: New Midday Levels']['v32'].append(s)

    # Change 3: EXREV (only in v3.2)
    for s in signals_v32:
        if s['sig_type'] == 'EXREV':
            changes['Change 3: EXREV Bypass']['v32'].append(s)

    # Change 4: FADE (only in v3.2)
    for s in signals_v32:
        if s['sig_type'] == 'FADE':
            changes['Change 4: FADE Resurrection']['v32'].append(s)

    # Change 5: HIGH→REV - v3.1 had bull BRK at HIGH levels, v3.2 has bull REV instead
    for s in signals_v31:
        if s['level_name'] in HIGH_LEVELS and s['sig_type'] == 'BRK' and s['sig_dir'] == 'bull':
            changes['Change 5: HIGH→REV Reassignment']['v31'].append(s)
    for s in signals_v32:
        if s['level_name'] in HIGH_LEVELS and s['sig_type'] == 'REV' and s['sig_dir'] == 'bull':
            changes['Change 5: HIGH→REV Reassignment']['v32'].append(s)

    return changes

def top_signals(signals, n=3, best=True):
    """Return top N best or worst signals."""
    if not signals:
        return []
    key = 'pnl_atr'
    sorted_sigs = sorted(signals, key=lambda s: s.get(key, 0), reverse=best)
    return sorted_sigs[:n]

def format_signal(s):
    """Format a signal for display."""
    t = s.get('time', '')
    if hasattr(t, 'strftime'):
        t = t.strftime('%Y-%m-%d %H:%M')
    return (f"{s.get('symbol','?')} {t} {s.get('level_name','?')} "
            f"{s.get('sig_type','?')} {s.get('sig_dir','?')} "
            f"MFE={s.get('mfe_atr',0):.3f} MAE={s.get('mae_atr',0):.3f} "
            f"P&L={s.get('pnl_atr',0):.3f} [{s.get('outcome','?')}]")

# ── Report Generation ─────────────────────────────────────────────────────────
def generate_report(signals_v31, signals_v32):
    """Generate full markdown report."""
    lines = []
    lines.append('# KLB v3.2 vs v3.1 Backtest Results')
    lines.append(f'**Date:** 2026-03-07')
    lines.append(f'**Period:** Last {N_DAYS} trading days')
    lines.append(f'**Symbols:** {", ".join(SYMBOLS)}')
    lines.append(f'**Data:** IB 5-minute bars, 14-period ATR from daily')
    lines.append('')

    stats_v31 = signal_stats(signals_v31, 'v3.1 Total')
    stats_v32 = signal_stats(signals_v32, 'v3.2 Total')

    lines.append('## Overall Summary')
    lines.append('')
    lines.append(f'| Metric | v3.1 | v3.2 | Delta |')
    lines.append(f'|--------|------|------|-------|')
    lines.append(f'| Total Signals | {stats_v31["n"]} | {stats_v32["n"]} | {stats_v32["n"] - stats_v31["n"]:+d} |')
    lines.append(f'| Win Rate | {stats_v31["win_rate"]:.1f}% | {stats_v32["win_rate"]:.1f}% | {stats_v32["win_rate"] - stats_v31["win_rate"]:+.1f}pp |')
    lines.append(f'| Avg MFE (ATR) | {stats_v31["avg_mfe"]:.3f} | {stats_v32["avg_mfe"]:.3f} | {stats_v32["avg_mfe"] - stats_v31["avg_mfe"]:+.3f} |')
    lines.append(f'| Avg MAE (ATR) | {stats_v31["avg_mae"]:.3f} | {stats_v32["avg_mae"]:.3f} | {stats_v32["avg_mae"] - stats_v31["avg_mae"]:+.3f} |')
    lines.append(f'| Net ATR | {stats_v31["net_atr"]:.1f} | {stats_v32["net_atr"]:.1f} | {stats_v32["net_atr"] - stats_v31["net_atr"]:+.1f} |')
    lines.append('')

    # ── Per-Change Summary Table ──
    changes = categorize_by_change(signals_v31, signals_v32)

    lines.append('## Summary by Change')
    lines.append('')
    lines.append('| Change | v3.1 Signals | v3.1 ATR | v3.2 Signals | v3.2 ATR | Delta ATR |')
    lines.append('|--------|:---:|:---:|:---:|:---:|:---:|')

    total_delta = 0
    for name, data in changes.items():
        s31 = signal_stats(data['v31'])
        s32 = signal_stats(data['v32'])
        delta = s32['net_atr'] - s31['net_atr']
        total_delta += delta
        lines.append(f'| {name} | {s31["n"]} | {s31["net_atr"]:+.1f} | {s32["n"]} | {s32["net_atr"]:+.1f} | {delta:+.1f} |')

    lines.append(f'| **TOTAL (changes only)** | | | | | **{total_delta:+.1f}** |')
    lines.append('')

    # ── Per-Change Detail ──
    lines.append('## Per-Change Detail')
    lines.append('')

    for name, data in changes.items():
        lines.append(f'### {name}')
        lines.append(f'*{data["desc"]}*')
        lines.append('')

        s31 = signal_stats(data['v31'])
        s32 = signal_stats(data['v32'])

        lines.append(f'| Metric | v3.1 | v3.2 |')
        lines.append(f'|--------|------|------|')
        lines.append(f'| Signals | {s31["n"]} | {s32["n"]} |')
        lines.append(f'| Win Rate | {s31["win_rate"]:.1f}% | {s32["win_rate"]:.1f}% |')
        lines.append(f'| Avg MFE | {s31["avg_mfe"]:.3f} | {s32["avg_mfe"]:.3f} |')
        lines.append(f'| Avg MAE | {s31["avg_mae"]:.3f} | {s32["avg_mae"]:.3f} |')
        lines.append(f'| Net ATR | {s31["net_atr"]:+.1f} | {s32["net_atr"]:+.1f} |')
        lines.append('')

        # Top 3 best/worst for whichever version has signals
        sigs_to_show = data['v32'] if data['v32'] else data['v31']
        if sigs_to_show:
            lines.append('**Top 3 Best:**')
            for s in top_signals(sigs_to_show, 3, best=True):
                lines.append(f'- {format_signal(s)}')
            lines.append('')
            lines.append('**Top 3 Worst:**')
            for s in top_signals(sigs_to_show, 3, best=False):
                lines.append(f'- {format_signal(s)}')
            lines.append('')

        # By level breakdown
        all_sigs = data['v31'] + data['v32']
        if all_sigs:
            level_names = sorted(set(s['level_name'] for s in all_sigs))
            if len(level_names) > 1:
                lines.append('**By Level:**')
                lines.append('| Level | v3.1 N | v3.2 N | v3.2 Win% | v3.2 ATR |')
                lines.append('|-------|:---:|:---:|:---:|:---:|')
                for ln in level_names:
                    ln31 = [s for s in data['v31'] if s['level_name'] == ln]
                    ln32 = [s for s in data['v32'] if s['level_name'] == ln]
                    st31 = signal_stats(ln31)
                    st32 = signal_stats(ln32)
                    lines.append(f'| {ln} | {st31["n"]} | {st32["n"]} | {st32["win_rate"]:.1f}% | {st32["net_atr"]:+.1f} |')
                lines.append('')

    # ── Per-Symbol Breakdown ──
    lines.append('## Per-Symbol Breakdown')
    lines.append('')
    lines.append('| Symbol | v3.1 Signals | v3.1 Win% | v3.1 ATR | v3.2 Signals | v3.2 Win% | v3.2 ATR | Delta ATR |')
    lines.append('|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|')

    for sym in SYMBOLS:
        sym31 = [s for s in signals_v31 if s['symbol'] == sym]
        sym32 = [s for s in signals_v32 if s['symbol'] == sym]
        st31 = signal_stats(sym31)
        st32 = signal_stats(sym32)
        delta = st32['net_atr'] - st31['net_atr']
        lines.append(f'| {sym} | {st31["n"]} | {st31["win_rate"]:.1f}% | {st31["net_atr"]:+.1f} | {st32["n"]} | {st32["win_rate"]:.1f}% | {st32["net_atr"]:+.1f} | {delta:+.1f} |')
    lines.append('')

    # ── Time-of-Day Analysis ──
    lines.append('## Time-of-Day Analysis')
    lines.append('')
    lines.append('### v3.2 New Midday Level Signals by Hour')
    lines.append('')

    new_levels = {'Today Open', 'PD Close', 'Week Open', 'Month Open'}
    midday_sigs = [s for s in signals_v32 if s['level_name'] in new_levels]

    hours = sorted(set(s['time'].hour for s in midday_sigs)) if midday_sigs else []
    if hours:
        lines.append('| Hour (ET) | Signals | Win Rate | Avg MFE | Avg MAE | Net ATR |')
        lines.append('|:---------:|:-------:|:--------:|:-------:|:-------:|:-------:|')
        for h in hours:
            h_sigs = [s for s in midday_sigs if s['time'].hour == h]
            st = signal_stats(h_sigs)
            lines.append(f'| {h:02d}:00 | {st["n"]} | {st["win_rate"]:.1f}% | {st["avg_mfe"]:.3f} | {st["avg_mae"]:.3f} | {st["net_atr"]:+.1f} |')
        lines.append('')
    else:
        lines.append('*No midday level signals detected.*')
        lines.append('')

    lines.append('### All v3.2 Signals by Hour')
    lines.append('')
    all_hours = sorted(set(s['time'].hour for s in signals_v32)) if signals_v32 else []
    if all_hours:
        lines.append('| Hour (ET) | v3.1 Signals | v3.2 Signals | v3.2 Win% | v3.2 Net ATR |')
        lines.append('|:---------:|:---:|:---:|:---:|:---:|')
        for h in all_hours:
            h31 = [s for s in signals_v31 if s['time'].hour == h]
            h32 = [s for s in signals_v32 if s['time'].hour == h]
            st31 = signal_stats(h31)
            st32 = signal_stats(h32)
            lines.append(f'| {h:02d}:00 | {st31["n"]} | {st32["n"]} | {st32["win_rate"]:.1f}% | {st32["net_atr"]:+.1f} |')
        lines.append('')

    # ── Cross-Symbol Analysis ──
    lines.append('## Cross-Symbol Analysis: Which Symbols Benefit Most')
    lines.append('')

    for change_name, data in changes.items():
        sigs = data['v32'] if data['v32'] else data['v31']
        if not sigs:
            continue
        lines.append(f'### {change_name}')
        lines.append('')
        sym_list = sorted(set(s['symbol'] for s in sigs))
        if sym_list:
            lines.append('| Symbol | N | Win% | Net ATR |')
            lines.append('|--------|:-:|:----:|:-------:|')
            for sym in sym_list:
                ss = [s for s in sigs if s['symbol'] == sym]
                st = signal_stats(ss)
                lines.append(f'| {sym} | {st["n"]} | {st["win_rate"]:.1f}% | {st["net_atr"]:+.1f} |')
            lines.append('')

    # ── Signal Type Distribution ──
    lines.append('## Signal Type Distribution')
    lines.append('')
    lines.append('### v3.1')
    sig_types_31 = sorted(set(s['sig_type'] for s in signals_v31))
    lines.append('| Type | N | Win% | Avg MFE | Avg MAE | Net ATR |')
    lines.append('|------|:-:|:----:|:-------:|:-------:|:-------:|')
    for st_name in sig_types_31:
        sigs = [s for s in signals_v31 if s['sig_type'] == st_name]
        st = signal_stats(sigs)
        lines.append(f'| {st_name} | {st["n"]} | {st["win_rate"]:.1f}% | {st["avg_mfe"]:.3f} | {st["avg_mae"]:.3f} | {st["net_atr"]:+.1f} |')
    lines.append('')

    lines.append('### v3.2')
    sig_types_32 = sorted(set(s['sig_type'] for s in signals_v32))
    lines.append('| Type | N | Win% | Avg MFE | Avg MAE | Net ATR |')
    lines.append('|------|:-:|:----:|:-------:|:-------:|:-------:|')
    for st_name in sig_types_32:
        sigs = [s for s in signals_v32 if s['sig_type'] == st_name]
        st = signal_stats(sigs)
        lines.append(f'| {st_name} | {st["n"]} | {st["win_rate"]:.1f}% | {st["avg_mfe"]:.3f} | {st["avg_mae"]:.3f} | {st["net_atr"]:+.1f} |')
    lines.append('')

    return '\n'.join(lines)


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('='*70)
    print('KLB v3.2 vs v3.1 Backtest')
    print('='*70)
    print(f'Symbols: {len(SYMBOLS)}')
    print(f'Period: last {N_DAYS} trading days')
    print()

    print('Running backtest...')
    signals_v31, signals_v32 = run_backtest()

    print(f'\nv3.1: {len(signals_v31)} signals')
    print(f'v3.2: {len(signals_v32)} signals')
    print()

    # Generate and print report
    report = generate_report(signals_v31, signals_v32)
    print(report)

    # Save report
    report_path = OUT_DIR / 'v32-backtest-results.md'
    with open(report_path, 'w') as f:
        f.write(report)
    print(f'\nReport saved to: {report_path}')
