"""
TSLA Open Scalp — 15s Premarket Research
Replicate Module P at 15s resolution (251 days, 9:16–9:30 window)
Output: tsla-pm-15s-findings.md
"""

import pandas as pd
import numpy as np
from pathlib import Path
from io import StringIO

CACHE = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache')
OUT = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug')

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────

def load_15s():
    df = pd.read_parquet(CACHE / 'bars_highres/15sec/tsla_15_secs_ib.parquet')
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC').tz_convert('America/New_York')
    else:
        df.index = df.index.tz_convert('America/New_York')
    return df

def load_1m():
    df = pd.read_parquet(CACHE / 'bars/tsla_1_min_ib.parquet')
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC').tz_convert('America/New_York')
    else:
        df.index = df.index.tz_convert('America/New_York')
    return df

print("Loading data...")
df15 = load_15s()
df1m = load_1m()
print(f"15s: {df15.shape}, {df15.index.min()} to {df15.index.max()}")
print(f"1m:  {df1m.shape}, {df1m.index.min()} to {df1m.index.max()}")

# ─────────────────────────────────────────────
# BUILD DAILY FEATURES (1m for market session + 15s for PM)
# ─────────────────────────────────────────────

def build_daily(df1m, df15):
    rows = []
    market_days = df1m.between_time('09:30', '16:00').index.normalize().unique()
    market_days = sorted(market_days)

    # Rolling ATR
    daily_ranges = {}
    for d in market_days:
        day_mkt = df1m[df1m.index.normalize() == d].between_time('09:30', '16:00')
        if len(day_mkt) > 0:
            daily_ranges[d] = day_mkt['high'].max() - day_mkt['low'].min()
    atr_series = pd.Series(daily_ranges).rolling(14).mean().shift(1)

    # Days with 15s data
    days_15s = set(df15.index.normalize().unique())

    prev_close = None
    for d in market_days:
        mkt = df1m[df1m.index.normalize() == d].between_time('09:30', '16:00')
        if len(mkt) < 10:
            prev_close = None
            continue

        open_930 = mkt.iloc[0]['open']
        eod_close = mkt.iloc[-1]['close']
        bar_935 = mkt.between_time('09:35', '09:35')
        close_935 = bar_935.iloc[0]['close'] if len(bar_935) > 0 else np.nan

        row = {
            'date': d,
            'open_930': open_930,
            'eod_close': eod_close,
            'day_pnl': eod_close - open_930,
            'day_above_open': eod_close > open_930,
            'hold_signal': close_935 > open_930 if not np.isnan(close_935) else np.nan,
            'close_935': close_935,
            'worst_day': (eod_close - open_930) < -5.0,
            'atr_14': atr_series.get(d, np.nan),
            'prev_close': prev_close,
        }

        # ── 15s premarket features ──
        if d in days_15s:
            pm15 = df15[df15.index.normalize() == d].between_time('04:00', '09:29:59')

            if len(pm15) >= 20:
                pm_high = pm15['high'].max()
                pm_low = pm15['low'].min()
                pm_range = pm_high - pm_low
                row['pm_range'] = pm_range

                # ── P3 variants: PM position at different timestamps ──
                # 15s bars: 9:29:00, 9:29:15, 9:29:30, 9:29:45 are available
                for ts_label, t_start, t_end in [
                    ('9:28:00', '09:28:00', '09:28:00'),
                    ('9:28:30', '09:28:30', '09:28:30'),
                    ('9:29:00', '09:29:00', '09:29:00'),
                    ('9:29:15', '09:29:15', '09:29:15'),
                    ('9:29:30', '09:29:30', '09:29:30'),
                    ('9:29:45', '09:29:45', '09:29:45'),
                ]:
                    bars = pm15.between_time(t_start, t_end)
                    if len(bars) > 0:
                        c = bars.iloc[-1]['close']
                        row[f'pm_pos_{ts_label}'] = (c - pm_low) / pm_range if pm_range > 0 else 0.5
                        row[f'pm_close_{ts_label}'] = c
                    else:
                        row[f'pm_pos_{ts_label}'] = np.nan
                        row[f'pm_close_{ts_label}'] = np.nan

                # ── P4 variants: Acceleration over different windows ──
                # Original: 9:25→9:29 (4 min). Now test finer windows.
                windows = [
                    ('4m', '09:25:00', '09:29:45'),   # original ~4min
                    ('3m', '09:26:00', '09:29:45'),
                    ('2m', '09:27:00', '09:29:45'),
                    ('90s', '09:28:00', '09:29:45'),
                    ('60s', '09:28:45', '09:29:45'),
                    ('30s', '09:29:15', '09:29:45'),
                    ('15s', '09:29:30', '09:29:45'),
                ]
                for label, t_start, t_end in windows:
                    w = pm15.between_time(t_start, t_end)
                    if len(w) >= 1:
                        start_price = w.iloc[0]['open']
                        end_price = w.iloc[-1]['close']
                        row[f'accel_{label}'] = end_price - start_price
                    else:
                        row[f'accel_{label}'] = np.nan

                # ── P1 variant: Late trend at 15s (9:20→9:29:45) ──
                w920 = pm15.between_time('09:20:00', '09:20:00')
                w929 = pm15.between_time('09:29:45', '09:29:45')
                if len(w920) > 0 and len(w929) > 0:
                    row['late_trend_15s'] = w929.iloc[-1]['close'] - w920.iloc[0]['open']
                else:
                    row['late_trend_15s'] = np.nan

                # ── Trajectory shape: 9:20→9:30 in ~40 bars ──
                traj = pm15.between_time('09:20:00', '09:29:45')
                if len(traj) >= 20:
                    prices = traj['close'].values
                    total_move = prices[-1] - prices[0]

                    # Monotonicity: how many bars moved in same direction as total?
                    diffs = np.diff(prices)
                    if total_move > 0:
                        same_dir = (diffs > 0).sum()
                    elif total_move < 0:
                        same_dir = (diffs < 0).sum()
                    else:
                        same_dir = len(diffs) // 2
                    row['traj_monotonicity'] = same_dir / len(diffs) if len(diffs) > 0 else 0.5

                    # Path efficiency: |total move| / sum(|each bar move|)
                    path_length = np.sum(np.abs(diffs))
                    row['traj_efficiency'] = abs(total_move) / path_length if path_length > 0 else 0

                    # Backload: did move happen in first half or second half?
                    mid = len(prices) // 2
                    first_half_move = prices[mid] - prices[0]
                    second_half_move = prices[-1] - prices[mid]
                    row['traj_backload'] = second_half_move - first_half_move  # positive = 2nd half stronger

                    # Max drawdown from running high (for up trends) or running low (for down trends)
                    if total_move > 0:
                        running_high = np.maximum.accumulate(prices)
                        dd = (running_high - prices).max()
                        row['traj_max_dd'] = dd
                    else:
                        running_low = np.minimum.accumulate(prices)
                        dd = (prices - running_low).max()
                        row['traj_max_dd'] = dd
                else:
                    row['traj_monotonicity'] = np.nan
                    row['traj_efficiency'] = np.nan
                    row['traj_backload'] = np.nan
                    row['traj_max_dd'] = np.nan

                # ── Volume: last 5m at 15s resolution ──
                vol_last5m = pm15.between_time('09:24:00', '09:29:45')
                vol_last10m = pm15.between_time('09:19:00', '09:29:45')
                if len(vol_last5m) > 0 and len(vol_last10m) > 0:
                    v5 = vol_last5m['volume'].sum()
                    v10 = vol_last10m['volume'].sum()
                    row['pm_vol_last5m'] = v5
                    row['pm_vol_last10m'] = v10
                    # Volume acceleration: is volume ramping in last 5m vs prior 5m?
                    v_prior5 = v10 - v5
                    row['pm_vol_accel'] = v5 / v_prior5 if v_prior5 > 0 else np.nan
                else:
                    row['pm_vol_last5m'] = np.nan
                    row['pm_vol_last10m'] = np.nan
                    row['pm_vol_accel'] = np.nan

            else:
                row['pm_range'] = np.nan
        else:
            row['pm_range'] = np.nan

        prev_close = eod_close
        rows.append(row)

    return pd.DataFrame(rows).set_index('date')

print("Building daily features...")
daily = build_daily(df1m, df15)
has_15s = daily['pm_range'].notna()
d = daily[has_15s].copy()
print(f"Total days: {len(daily)}, with 15s PM data: {len(d)}")

# Only analyze HOLD signal days for most analyses
hold = d[d['hold_signal'] == True].copy()
bail = d[d['hold_signal'] == False].copy()
print(f"HOLD days: {len(hold)}, BAIL days: {len(bail)}")

# ─────────────────────────────────────────────
# ANALYSIS FUNCTIONS
# ─────────────────────────────────────────────

def quartile_analysis(df, col, label, outcome_col='day_pnl'):
    """Analyze outcome by quartiles of a column."""
    valid = df[df[col].notna()].copy()
    if len(valid) < 20:
        return f"\n### {label}\nInsufficient data (n={len(valid)})\n"

    q1, q2, q3 = valid[col].quantile([0.25, 0.5, 0.75])
    bins = [('Bottom 25%', valid[col] <= q1),
            ('Lower-mid', (valid[col] > q1) & (valid[col] <= q2)),
            ('Upper-mid', (valid[col] > q2) & (valid[col] <= q3)),
            ('Top 25%', valid[col] > q3)]

    lines = [f"\n### {label}"]
    lines.append(f"Range: {valid[col].min():.3f} to {valid[col].max():.3f}, median={q2:.3f}")
    lines.append(f"Q1={q1:.3f}, Q3={q3:.3f}\n")
    lines.append(f"| Quartile | Range | n | Win% | Avg P&L | Worst% |")
    lines.append(f"|---|---|---|---|---|---|")

    for name, mask in bins:
        subset = valid[mask]
        n = len(subset)
        if n == 0:
            continue
        win = (subset[outcome_col] > 0).mean() * 100
        avg = subset[outcome_col].mean()
        worst = (subset[outcome_col] < -5).mean() * 100
        lo, hi = subset[col].min(), subset[col].max()
        lines.append(f"| {name} | {lo:.3f}–{hi:.3f} | {n} | {win:.0f}% | ${avg:.2f} | {worst:.0f}% |")

    return '\n'.join(lines)


def compare_accel_windows(df, windows_cols, label="Acceleration Window Comparison"):
    """Compare predictive power of different acceleration windows."""
    lines = [f"\n### {label}"]
    lines.append(f"| Window | n | Corr w/PnL | Up→Win% | Down→Win% | Spread |")
    lines.append(f"|---|---|---|---|---|---|")

    for col in windows_cols:
        valid = df[df[col].notna()].copy()
        n = len(valid)
        if n < 20:
            continue
        corr = valid[col].corr(valid['day_pnl'])
        up = valid[valid[col] > 0]
        down = valid[valid[col] < 0]
        win_up = (up['day_pnl'] > 0).mean() * 100 if len(up) > 0 else np.nan
        win_down = (down['day_pnl'] > 0).mean() * 100 if len(down) > 0 else np.nan
        spread = (win_up - win_down) if not np.isnan(win_up) and not np.isnan(win_down) else np.nan
        label_short = col.replace('accel_', '')
        lines.append(f"| {label_short} | {n} | {corr:.3f} | {win_up:.0f}% | {win_down:.0f}% | {spread:.0f}pp |")

    return '\n'.join(lines)


def compare_position_timestamps(df, pos_cols, label="PM Position Timestamp Comparison"):
    """Compare PM position measured at different timestamps."""
    lines = [f"\n### {label}"]
    lines.append(f"| Timestamp | n | Corr w/PnL | Low→Win% | High→Win% | Spread |")
    lines.append(f"|---|---|---|---|---|---|")

    for col in pos_cols:
        valid = df[df[col].notna()].copy()
        n = len(valid)
        if n < 20:
            continue
        corr = valid[col].corr(valid['day_pnl'])
        q1 = valid[col].quantile(0.25)
        q3 = valid[col].quantile(0.75)
        low = valid[valid[col] <= q1]
        high = valid[valid[col] >= q3]
        win_low = (low['day_pnl'] > 0).mean() * 100 if len(low) > 0 else np.nan
        win_high = (high['day_pnl'] > 0).mean() * 100 if len(high) > 0 else np.nan
        spread = (win_high - win_low) if not np.isnan(win_high) and not np.isnan(win_low) else np.nan
        ts = col.replace('pm_pos_', '')
        lines.append(f"| {ts} | {n} | {corr:.3f} | {win_low:.0f}% | {win_high:.0f}% | {spread:.0f}pp |")

    return '\n'.join(lines)


# ─────────────────────────────────────────────
# RUN ANALYSES
# ─────────────────────────────────────────────

report = []
report.append("# TSLA 15s Premarket Research — Module P at High Resolution")
report.append(f"*Date: 2026-03-18 | Data: {len(d)} days with 15s PM, {len(hold)} HOLD / {len(bail)} BAIL*\n")
report.append("---\n")

# ── Section 1: PM Position — which timestamp is best? ──
report.append("## 1. PM Position Timestamp — When to Measure\n")
report.append("Original Module P used 1m bar at 9:29. Now testing 15s snapshots.\n")

pos_cols = [c for c in d.columns if c.startswith('pm_pos_')]
report.append(compare_position_timestamps(d, pos_cols, "All Days"))
report.append(compare_position_timestamps(hold, pos_cols, "HOLD Days Only"))

# Best position col for detailed quartile analysis
report.append("\n## 1b. PM Position Quartile Detail (best timestamp)\n")
for col in pos_cols:
    report.append(quartile_analysis(d, col, f"All days — {col.replace('pm_pos_', '')}"))
    report.append(quartile_analysis(hold, col, f"HOLD days — {col.replace('pm_pos_', '')}"))

# ── Section 2: Acceleration — which window is best? ──
report.append("\n---\n## 2. Acceleration Window — Optimal Measurement Period\n")
report.append("Original: 9:25→9:29 (4min). Now testing windows from 15s to 4min.\n")

accel_cols = [c for c in d.columns if c.startswith('accel_')]
report.append(compare_accel_windows(d, accel_cols, "All Days"))
report.append(compare_accel_windows(hold, accel_cols, "HOLD Days Only"))

# Detailed quartile for top performers
report.append("\n## 2b. Best Acceleration Windows — Quartile Detail\n")
for col in accel_cols:
    report.append(quartile_analysis(d, col, f"All days — {col.replace('accel_', '')}"))

# ── Section 3: Trajectory Shape ──
report.append("\n---\n## 3. PM Trajectory Shape (9:20–9:30)\n")
report.append("Does HOW price gets there matter, or just where it ends up?\n")

for col, label in [
    ('traj_monotonicity', 'Monotonicity (% bars moving with trend)'),
    ('traj_efficiency', 'Path Efficiency (|net move| / total path)'),
    ('traj_backload', 'Backload (2nd half move - 1st half move)'),
    ('traj_max_dd', 'Max Drawdown from running extremes'),
]:
    report.append(quartile_analysis(d, col, f"All days — {label}"))
    report.append(quartile_analysis(hold, col, f"HOLD days — {label}"))

# ── Section 4: Volume Ramp ──
report.append("\n---\n## 4. PM Volume Ramp (15s resolution)\n")
report.append("Is volume acceleration in last 5min predictive?\n")

for col, label in [
    ('pm_vol_last5m', 'PM Volume Last 5min'),
    ('pm_vol_accel', 'Volume Acceleration (last 5m / prior 5m)'),
]:
    report.append(quartile_analysis(d, col, f"All days — {label}"))
    report.append(quartile_analysis(hold, col, f"HOLD days — {label}"))

# ── Section 5: Combined Signals (PM filter at 15s) ──
report.append("\n---\n## 5. Combined PM Filter — 15s Optimized\n")

# Replicate the original PM filter but with 15s position
# Original: pm_position > 0.219 AND pm_accel > 0
# Test with different position timestamps and accel windows

report.append("### 5a. Original Filter (1m equivalent) vs 15s candidates\n")

combos = []
for pos_col in ['pm_pos_9:29:00', 'pm_pos_9:29:30', 'pm_pos_9:29:45']:
    for accel_col in ['accel_4m', 'accel_2m', 'accel_60s', 'accel_30s']:
        pos_valid = d[pos_col].notna() & d[accel_col].notna() & d['hold_signal'].notna()
        valid = d[pos_valid].copy()
        if len(valid) < 50:
            continue

        # Use original thresholds
        q1_pos = valid[pos_col].quantile(0.25)

        pm_pass = (valid[pos_col] > q1_pos) & (valid[accel_col] > 0)
        pm_fail = ~pm_pass

        hold_pass = valid[pm_pass & (valid['hold_signal'] == True)]
        hold_fail = valid[pm_fail & (valid['hold_signal'] == True)]
        hold_only = valid[valid['hold_signal'] == True]

        n_pass = len(hold_pass)
        n_fail = len(hold_fail)
        n_hold = len(hold_only)

        if n_pass < 5 or n_hold < 10:
            continue

        win_pass = (hold_pass['day_pnl'] > 0).mean() * 100
        avg_pass = hold_pass['day_pnl'].mean()
        worst_pass = (hold_pass['day_pnl'] < -5).mean() * 100

        win_hold = (hold_only['day_pnl'] > 0).mean() * 100
        avg_hold = hold_only['day_pnl'].mean()

        # Sharpe proxy
        sharpe = avg_pass / hold_pass['day_pnl'].std() * np.sqrt(252) if hold_pass['day_pnl'].std() > 0 else 0

        combos.append({
            'pos': pos_col.replace('pm_pos_', ''),
            'accel': accel_col.replace('accel_', ''),
            'n_trades': n_pass,
            'n_excluded': n_fail,
            'win': win_pass,
            'avg_pnl': avg_pass,
            'worst': worst_pass,
            'sharpe': sharpe,
            'improvement_win': win_pass - win_hold,
            'improvement_pnl': avg_pass - avg_hold,
        })

combos_df = pd.DataFrame(combos).sort_values('sharpe', ascending=False)

report.append("| Pos@  | Accel | Trades | Win% | Avg P&L | Worst% | Sharpe | ΔWin | ΔP&L |")
report.append("|---|---|---|---|---|---|---|---|---|")
for _, r in combos_df.head(15).iterrows():
    report.append(f"| {r['pos']} | {r['accel']} | {r['n_trades']} | {r['win']:.0f}% | ${r['avg_pnl']:.2f} | {r['worst']:.0f}% | {r['sharpe']:.1f} | {r['improvement_win']:+.0f}pp | ${r['improvement_pnl']:+.2f} |")

# ── Section 6: Hard Kill Refinement ──
report.append("\n---\n## 6. Hard Kill Refinement at 15s\n")
report.append("Can we tighten the P9 bear composite with finer PM data?\n")

# P9 original: pm_position < Q1 AND accel < 0
for pos_col in ['pm_pos_9:29:00', 'pm_pos_9:29:45']:
    for accel_col in ['accel_4m', 'accel_60s', 'accel_30s']:
        valid = d[d[pos_col].notna() & d[accel_col].notna()].copy()
        if len(valid) < 50:
            continue
        q1 = valid[pos_col].quantile(0.25)
        bear = (valid[pos_col] < q1) & (valid[accel_col] < 0)

        bear_days = valid[bear]
        non_bear = valid[~bear]

        worst_caught = (bear_days['day_pnl'] < -5).sum()
        worst_total = (valid['day_pnl'] < -5).sum()
        false_exclude = (bear_days['day_pnl'] > 0).sum()

        p = pos_col.replace('pm_pos_', '')
        a = accel_col.replace('accel_', '')
        report.append(f"\n**P9 variant: pos@{p} + accel_{a}**")
        report.append(f"- Flagged: {len(bear_days)} days ({len(bear_days)/len(valid)*100:.0f}%)")
        report.append(f"- Worst days caught: {worst_caught}/{worst_total} ({worst_caught/worst_total*100:.0f}%)" if worst_total > 0 else "- No worst days")
        report.append(f"- False excludes: {false_exclude} ({false_exclude/len(bear_days)*100:.0f}%)" if len(bear_days) > 0 else "")
        report.append(f"- Bear avg P&L: ${bear_days['day_pnl'].mean():.2f}, Win%: {(bear_days['day_pnl']>0).mean()*100:.0f}%")
        report.append(f"- Non-bear avg P&L: ${non_bear['day_pnl'].mean():.2f}, Win%: {(non_bear['day_pnl']>0).mean()*100:.0f}%")

# ── Section 7: Summary ──
report.append("\n---\n## 7. Summary & Recommendations\n")
report.append("*(Filled in after reviewing results above)*\n")

# Write report
report_text = '\n'.join(report)
outfile = OUT / 'tsla-pm-15s-findings.md'
outfile.write_text(report_text)
print(f"\nReport written to {outfile}")
print(f"Report length: {len(report_text)} chars, {len(report)} lines")
