"""
TSLA Open Scalp Backtest Harness
Simulates v1.2c logic for any parameter configuration.
Returns standardized metrics for the supervisor.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field

CACHE = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache')

@dataclass
class Config:
    """All tunable parameters for the scalp system."""
    # PM confidence
    pm_pos_q1: float = 0.219          # PM position Q1 threshold
    accel_window: str = '2m'          # '2m' or '4m' — which bars for acceleration
    vix_low_kill: float = 15.0        # VIX <= this = hard kill
    vix_sweet_lo: float = 18.0        # VIX sweet spot low
    vix_sweet_hi: float = 25.0        # VIX sweet spot high

    # Fakeout
    fakeout_require_new_low: bool = True  # v1.2c: bar2 must break bar1 low

    # ORB
    orb_bars: int = 5                 # 9:30-9:34 = 5 bars
    min_orb_width: float = 1.0        # skip breakout if ORB < this
    breakout_timeout_hm: int = 955    # no break by this time = timeout

    # SL
    sl_fallback: float = 1.50         # before ORB freeze
    sl_mode: str = 'orb_low'          # 'orb_low', 'orb_low_025', 'orb_low_050', 'fixed_2'
    sl_skip_orb_bar: bool = True      # don't check SL on ORB freeze bar

    # Hold time (bars after breakout)
    hold_bars: int = 10               # exit N bars after breakout. 0 = EOD
    hold_max_bars: int = 390          # EOD fallback

    # Path efficiency filter
    use_path_eff: bool = False
    path_eff_lo: float = 0.094        # Q2 lower bound
    path_eff_hi: float = 0.202        # Q2 upper bound

    # Tier thresholds
    tier_high: int = 5
    tier_med: int = 3
    tier_low: int = 2


def load_data():
    """Load all required datasets."""
    def _load(fname):
        df = pd.read_parquet(CACHE / fname)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC').tz_convert('America/New_York')
        else:
            df.index = df.index.tz_convert('America/New_York')
        return df

    df1m = _load('bars/tsla_1_min_ib.parquet')
    df15 = _load('bars_highres/15sec/tsla_15_secs_ib.parquet')

    # VIX daily
    try:
        dfvix = _load('bars/vix_1_day_ib.parquet')
    except:
        dfvix = None

    # SPY/QQQ 1m
    try:
        dfspy = _load('bars/spy_1_min_ib.parquet')
        dfqqq = _load('bars/qqq_1_min_ib.parquet')
    except:
        dfspy = None
        dfqqq = None

    return df1m, df15, dfvix, dfspy, dfqqq


def run_backtest(cfg: Config, df1m, df15, dfvix=None, dfspy=None, dfqqq=None,
                 start_date=None, end_date=None):
    """
    Run the full scalp backtest with given config.
    Returns DataFrame of trades with outcomes.
    """
    days_15s = set(df15.index.normalize().unique())
    market_days = sorted(df1m.between_time('09:30', '16:00').index.normalize().unique())

    if start_date:
        market_days = [d for d in market_days if d >= pd.Timestamp(start_date, tz='America/New_York')]
    if end_date:
        market_days = [d for d in market_days if d <= pd.Timestamp(end_date, tz='America/New_York')]

    # Build VIX lookup
    vix_lookup = {}
    if dfvix is not None:
        for idx, row in dfvix.iterrows():
            d = idx.normalize()
            vix_lookup[d] = row['close']

    trades = []
    prev_close = None

    for d in market_days:
        mkt = df1m[df1m.index.normalize() == d].between_time('09:30', '16:00')
        if len(mkt) < 10:
            prev_close = None
            continue

        open_930 = mkt.iloc[0]['open']
        eod_close = mkt.iloc[-1]['close']

        # ── PM features from 15s ──
        pm_position = np.nan
        pm_accel = np.nan
        pm_late_trend = np.nan
        path_eff = np.nan

        if d in days_15s:
            pm15 = df15[df15.index.normalize() == d].between_time('04:00', '09:29:59')
            if len(pm15) >= 20:
                pm_h, pm_l = pm15['high'].max(), pm15['low'].min()
                pm_range = pm_h - pm_l

                # Position at 9:29
                b929 = pm15.between_time('09:29:00', '09:29:00')
                if len(b929) > 0 and pm_range > 0:
                    pm_position = (b929.iloc[-1]['close'] - pm_l) / pm_range

                # Accel: 2m window (9:27→9:29)
                if cfg.accel_window == '2m':
                    b927 = pm15.between_time('09:27:00', '09:27:00')
                    if len(b927) > 0 and len(b929) > 0:
                        pm_accel = b929.iloc[-1]['close'] - b927.iloc[0]['open']
                else:  # 4m
                    b925 = pm15.between_time('09:25:00', '09:25:00')
                    if len(b925) > 0 and len(b929) > 0:
                        pm_accel = b929.iloc[-1]['close'] - b925.iloc[0]['open']

                # Late trend (9:20→9:29)
                b920 = pm15.between_time('09:20:00', '09:20:00')
                if len(b920) > 0 and len(b929) > 0:
                    pm_late_trend = b929.iloc[-1]['close'] - b920.iloc[0]['open']

                # Path efficiency (close-to-close, 9:20-9:29)
                traj = pm15.between_time('09:20:00', '09:29:59')
                if len(traj) >= 10:
                    closes = traj['close'].values
                    net = closes[-1] - closes[0]
                    diffs = np.diff(closes)
                    path_len = np.sum(np.abs(diffs))
                    path_eff = abs(net) / path_len if path_len > 0 else 0

                # P9: 30s accel from 15s sub-bars on 9:29 bar
                sub15 = pm15.between_time('09:29:00', '09:29:59')
                if len(sub15) >= 4:
                    p9_30s_down = sub15.iloc[-1]['close'] < sub15.iloc[1]['close']
                elif len(b929) > 0:
                    p9_30s_down = b929.iloc[-1]['close'] < b929.iloc[-1]['open']
                else:
                    p9_30s_down = False
        else:
            p9_30s_down = False

        # ── VIX ──
        vix = np.nan
        # Try prev day VIX
        d_idx = market_days.index(d)
        if d_idx > 0:
            prev_d = market_days[d_idx - 1]
            vix = vix_lookup.get(prev_d, np.nan)
        if np.isnan(vix):
            vix = vix_lookup.get(d, np.nan)

        # ── SPY/QQQ PM alignment ──
        triple_align = False
        if dfspy is not None and dfqqq is not None:
            spy_pm = dfspy[dfspy.index.normalize() == d].between_time('09:20', '09:29')
            qqq_pm = dfqqq[dfqqq.index.normalize() == d].between_time('09:20', '09:29')
            if len(spy_pm) >= 5 and len(qqq_pm) >= 5:
                spy_up = spy_pm.iloc[-1]['close'] > spy_pm.iloc[0]['open']
                qqq_up = qqq_pm.iloc[-1]['close'] > qqq_pm.iloc[0]['open']
                tsla_up = not np.isnan(pm_late_trend) and pm_late_trend > 0
                triple_align = tsla_up and spy_up and qqq_up

        # ── Gap ──
        est_gap = 0
        if prev_close is not None:
            est_gap = open_930 - prev_close  # approximate (PM close vs prev RTH close)

        # ── Confidence scoring ──
        confidence = 0
        hard_kill = False

        if not np.isnan(pm_position) and pm_position > cfg.pm_pos_q1:
            confidence += 1
        if not np.isnan(pm_accel) and pm_accel > 0:
            confidence += 1
        if not np.isnan(vix) and cfg.vix_sweet_lo <= vix <= cfg.vix_sweet_hi:
            confidence += 1
        if triple_align:
            confidence += 1
        gap_danger = est_gap < -2 and not np.isnan(pm_late_trend) and abs(pm_late_trend) < 0.48
        if not gap_danger:
            confidence += 1

        # Hard kills
        if not np.isnan(vix) and vix <= cfg.vix_low_kill:
            hard_kill = True
        if not np.isnan(pm_position) and pm_position < cfg.pm_pos_q1 and p9_30s_down:
            hard_kill = True
        if gap_danger:
            hard_kill = True

        # Path efficiency filter
        if cfg.use_path_eff and not np.isnan(path_eff):
            if not (cfg.path_eff_lo <= path_eff <= cfg.path_eff_hi):
                confidence = max(0, confidence - 1)  # penalize, don't hard kill

        # Tier
        if hard_kill:
            tier = 'NO-GO'
        elif confidence >= cfg.tier_high:
            tier = 'HIGH'
        elif confidence >= cfg.tier_med:
            tier = 'MED'
        elif confidence >= cfg.tier_low:
            tier = 'LOW'
        else:
            tier = 'NO-GO'

        # ── Fakeout detection (30s bars from 15s data) ──
        fakeout = False
        shakeout = False
        if d in days_15s:
            rth15 = df15[df15.index.normalize() == d].between_time('09:30:00', '09:30:59')
            b1 = rth15.between_time('09:30:00', '09:30:29')
            b2 = rth15.between_time('09:30:30', '09:30:59')
            if len(b1) >= 1 and len(b2) >= 1:
                b1_o, b1_h, b1_l, b1_c = b1.iloc[0]['open'], b1['high'].max(), b1['low'].min(), b1.iloc[-1]['close']
                b2_o, b2_l, b2_c = b2.iloc[0]['open'], b2['low'].min(), b2.iloc[-1]['close']
                b1_up = b1_c >= b1_o
                b2_down = b2_c < b2_o
                b1_down = b1_c < b1_o

                if cfg.fakeout_require_new_low:
                    if b1_up and b2_down and b2_l < b1_l:
                        fakeout = True
                else:
                    if b1_up and b2_down:
                        fakeout = True

                if b1_down and b2_down and (b1_h - b1_l) <= 3.04:
                    shakeout = True

        # ── Only trade MED/HIGH days ──
        if tier not in ('MED', 'HIGH'):
            prev_close = eod_close
            continue

        # ── ORB build (9:30-9:34) ──
        orb_bars_data = mkt.between_time('09:30', '09:34')
        if len(orb_bars_data) < cfg.orb_bars:
            prev_close = eod_close
            continue

        orb_high = orb_bars_data['high'].max()
        orb_low = orb_bars_data['low'].min()
        orb_width = orb_high - orb_low

        # 5m rule
        close_934 = orb_bars_data.iloc[-1]['close']
        is_hold = close_934 > open_930

        # ── SL level ──
        if cfg.sl_mode == 'orb_low':
            sl_level = orb_low
        elif cfg.sl_mode == 'orb_low_025':
            sl_level = orb_low - 0.25
        elif cfg.sl_mode == 'orb_low_050':
            sl_level = orb_low - 0.50
        else:  # fixed_2
            sl_level = open_930 - 2.0

        # ── Check fallback SL hit during ORB build (9:30-9:33, not 9:34) ──
        fallback_sl = open_930 - cfg.sl_fallback
        orb_build = mkt.between_time('09:30', '09:33')
        fallback_hit = (orb_build['low'] <= fallback_sl).any() if len(orb_build) > 0 else False

        # ── ORB width filter ──
        orb_too_narrow = orb_width < cfg.min_orb_width

        # ── Breakout detection (9:35 onward) ──
        post_orb = mkt[mkt.index.map(lambda x: 935 <= x.hour * 100 + x.minute <= cfg.breakout_timeout_hm)]

        breakout_bar_idx = None
        breakout_type = None
        breakout_price = None

        if not orb_too_narrow:
            for i, (idx, bar) in enumerate(post_orb.iterrows()):
                hm_bar = idx.hour * 100 + idx.minute
                # Check SL hit (skip ORB freeze bar)
                if bar['low'] <= sl_level and not (hm_bar == 934):
                    breakout_type = 'SL_HIT'
                    breakout_bar_idx = i
                    breakout_price = sl_level
                    break
                # Bull breakout
                if bar['close'] > orb_high:
                    breakout_type = 'BULL'
                    breakout_bar_idx = i
                    breakout_price = bar['close']
                    break
                # Bear breakout
                if bar['close'] < orb_low:
                    breakout_type = 'BEAR'
                    breakout_bar_idx = i
                    breakout_price = bar['close']
                    break

        # ── Compute exit and P&L ──
        entry_price = open_930
        exit_price = eod_close  # default
        exit_reason = 'EOD'
        bars_held = len(mkt)

        if fallback_hit:
            exit_price = fallback_sl
            exit_reason = 'FALLBACK_SL'
            bars_held = 0
        elif breakout_type == 'SL_HIT':
            exit_price = sl_level
            exit_reason = 'ORB_SL'
            bars_held = breakout_bar_idx
        elif breakout_type == 'BEAR':
            exit_price = breakout_price
            exit_reason = 'BEAR_BREAK'
            bars_held = breakout_bar_idx
        elif breakout_type == 'BULL':
            # Hold for N bars after breakout, or EOD
            if cfg.hold_bars > 0 and breakout_bar_idx is not None:
                exit_bar_idx = breakout_bar_idx + cfg.hold_bars
                if exit_bar_idx < len(post_orb):
                    exit_price = post_orb.iloc[exit_bar_idx]['close']
                    exit_reason = f'HOLD_{cfg.hold_bars}'
                    bars_held = exit_bar_idx
                else:
                    exit_price = eod_close
                    exit_reason = 'EOD_AFTER_BULL'
                    bars_held = len(post_orb)
            else:
                exit_price = eod_close
                exit_reason = 'EOD_AFTER_BULL'
                bars_held = len(post_orb)

            # Check if SL hit during hold period
            if breakout_type == 'BULL' and breakout_bar_idx is not None and exit_reason.startswith('HOLD'):
                hold_window = post_orb.iloc[breakout_bar_idx:breakout_bar_idx + cfg.hold_bars + 1]
                if (hold_window['low'] <= sl_level).any():
                    exit_price = sl_level
                    exit_reason = 'SL_DURING_HOLD'
        elif orb_too_narrow:
            exit_reason = 'ORB_NARROW'
            exit_price = eod_close  # stayed in but no breakout signal

        pnl = exit_price - entry_price

        # ── MFE/MAE from entry ──
        post_entry = mkt.between_time('09:30', '15:59')
        mfe = (post_entry['high'].max() - entry_price) if len(post_entry) > 0 else 0
        mae = (entry_price - post_entry['low'].min()) if len(post_entry) > 0 else 0

        trades.append({
            'date': d,
            'tier': tier,
            'confidence': confidence,
            'hard_kill': hard_kill,
            'is_hold': is_hold,
            'fakeout': fakeout,
            'shakeout': shakeout,
            'orb_width': orb_width,
            'orb_narrow': orb_too_narrow,
            'sl_level': sl_level,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'pnl': pnl,
            'mfe': mfe,
            'mae': mae,
            'bars_held': bars_held,
            'breakout_type': breakout_type,
            'pm_position': pm_position,
            'pm_accel': pm_accel,
            'vix': vix,
            'path_eff': path_eff,
        })

        prev_close = eod_close

    return pd.DataFrame(trades)


def score_trades(df):
    """Score a set of trades. Returns dict of metrics."""
    if len(df) == 0:
        return {'n': 0, 'win_pct': 0, 'avg_pnl': 0, 'total_pnl': 0,
                'worst_pct': 0, 'sharpe': 0, 'score': 0, 'ev': 0}

    n = len(df)
    wins = (df['pnl'] > 0).sum()
    win_pct = wins / n * 100
    avg_pnl = df['pnl'].mean()
    total_pnl = df['pnl'].sum()
    worst_pct = (df['pnl'] < -5).mean() * 100
    std = df['pnl'].std()
    sharpe = avg_pnl / std * np.sqrt(252) if std > 0 else 0

    # Score: total_pnl * (win_rate / 50%) * min(1, n/50)
    score = total_pnl * (win_pct / 50) * min(1.0, n / 50)

    # EV per trade
    ev = avg_pnl

    return {
        'n': n,
        'win_pct': round(win_pct, 1),
        'avg_pnl': round(avg_pnl, 2),
        'total_pnl': round(total_pnl, 2),
        'worst_pct': round(worst_pct, 1),
        'sharpe': round(sharpe, 2),
        'score': round(score, 1),
        'ev': round(ev, 2),
    }


if __name__ == '__main__':
    print("Loading data...")
    df1m, df15, dfvix, dfspy, dfqqq = load_data()

    # Run baseline
    cfg = Config()
    print(f"Running baseline (v1.2c defaults)...")
    trades = run_backtest(cfg, df1m, df15, dfvix, dfspy, dfqqq)
    metrics = score_trades(trades)
    print(f"Trades: {metrics['n']}, Win: {metrics['win_pct']}%, Avg: ${metrics['avg_pnl']}, "
          f"Total: ${metrics['total_pnl']}, Worst: {metrics['worst_pct']}%, Sharpe: {metrics['sharpe']}, "
          f"Score: {metrics['score']}")

    # Exit reason breakdown
    print("\nExit reasons:")
    for reason, group in trades.groupby('exit_reason'):
        m = score_trades(group)
        print(f"  {reason:<20} n={m['n']:>3}  win={m['win_pct']:>5.1f}%  avg=${m['avg_pnl']:>6.2f}")
