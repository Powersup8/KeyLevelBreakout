"""
TSLA P10/P11 — SPY and QQQ Premarket Trend as TSLA Opening Filters
234 days of SPY + QQQ 1m PM data cross-tabbed with TSLA outcomes.
Output: debug/tsla_pm_spy_qqq.md
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

CACHE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache")
OUT   = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug/tsla_pm_spy_qqq.md")

def load_ib(path):
    df = pd.read_parquet(path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    df.index = df.index.tz_convert('America/New_York') if df.index.tz else df.index.tz_localize('UTC').tz_convert('America/New_York')
    return df

print("Loading data...")
tsla_1m = load_ib(CACHE / "bars/tsla_1_min_ib.parquet")
spy_1m  = load_ib(CACHE / "bars/spy_1_min_ib.parquet")
qqq_1m  = load_ib(CACHE / "bars/qqq_1_min_ib.parquet")

# ─── TSLA daily outcomes ──────────────────────────────────────────────────────
print("Building TSLA daily outcomes...")
tsla_mh = tsla_1m.between_time('09:30', '15:59')
days = sorted(tsla_mh.index.normalize().unique())

rows = []
for day in days:
    d = tsla_mh[tsla_mh.index.date == day.date()]
    if d.empty: continue
    b930 = d.between_time('09:30', '09:30')
    b935 = d.between_time('09:35', '09:35')
    if b930.empty: continue
    entry     = b930.iloc[0]['open']
    close_5m  = b935.iloc[0]['close'] if not b935.empty else np.nan
    eod_close = d.iloc[-1]['close']
    rows.append({
        'day': day.date(), 'entry': entry, 'close_5m': close_5m,
        'eod_close': eod_close, 'day_chg': eod_close - entry,
        'day_high': d['high'].max(), 'day_low': d['low'].min(),
    })

outcomes = pd.DataFrame(rows).set_index('day')
outcomes['day_above'] = outcomes['day_chg'] > 0
outcomes['hold_5m']   = outcomes['close_5m'] > outcomes['entry']
outcomes['worst']     = outcomes['day_chg'] < -5
outcomes['bad']       = outcomes['day_chg'] < -2
outcomes['bull']      = outcomes['day_chg'] > 5
print(f"Outcomes: {len(outcomes)} days")

# ─── PM features builder ──────────────────────────────────────────────────────
def build_pm_features(df1m, sym):
    """Extract PM structure (4am–9:29) for each market day."""
    rows = []
    market_days = df1m.between_time('09:30', '16:00').index.normalize().unique()
    for d in sorted(market_days):
        pm = df1m[df1m.index.normalize() == d].between_time('04:00', '09:29')
        if len(pm) < 5:
            continue
        row = {'day': d.date()}

        pm_open  = pm.iloc[0]['open']
        pm_high  = pm['high'].max()
        pm_low   = pm['low'].min()
        pm_range = pm_high - pm_low
        close_929 = pm.iloc[-1]['close']

        row[f'{sym}_pm_position']  = (close_929 - pm_low) / pm_range if pm_range > 0 else 0.5
        row[f'{sym}_pm_range']     = pm_range
        row[f'{sym}_pm_full_move'] = close_929 - pm_open

        # Late trend 9:20–9:29
        pm_920 = pm.between_time('09:20', '09:29')
        row[f'{sym}_pm_late_trend'] = (pm_920.iloc[-1]['close'] - pm_920.iloc[0]['open']
                                       if len(pm_920) >= 5 else np.nan)

        # Acceleration 9:25–9:29
        pm_925 = pm.between_time('09:25', '09:29')
        row[f'{sym}_pm_accel'] = (pm_925.iloc[-1]['close'] - pm_925.iloc[0]['open']
                                  if len(pm_925) >= 3 else np.nan)

        rows.append(row)
    return pd.DataFrame(rows).set_index('day')

print("Building PM features (SPY, QQQ, TSLA)...")
spy_pm  = build_pm_features(spy_1m,  'spy')
qqq_pm  = build_pm_features(qqq_1m,  'qqq')
tsla_pm = build_pm_features(tsla_1m, 'tsla')
print(f"  SPY PM: {len(spy_pm)}  QQQ PM: {len(qqq_pm)}  TSLA PM: {len(tsla_pm)}")

df = outcomes.join(spy_pm).join(qqq_pm).join(tsla_pm)
n_spy  = df['spy_pm_position'].notna().sum()
n_qqq  = df['qqq_pm_position'].notna().sum()
n_tsla = df['tsla_pm_position'].notna().sum()
print(f"Merged: {len(df)} total | SPY PM: {n_spy} | QQQ PM: {n_qqq} | TSLA PM: {n_tsla}")

# ─── Helpers ──────────────────────────────────────────────────────────────────
HDR = "| label | n | day_above% | avg_day_chg | worst% | bad% | bull% | hold_5m% |"
SEP = "|---|---|---|---|---|---|---|---|"

def fmt_row(label, sub):
    if len(sub) == 0: return None
    n    = len(sub)
    thin = " (thin)" if n < 25 else ""
    return (f"| {label}{thin} | {n} | {sub['day_above'].mean()*100:.1f} | "
            f"{sub['day_chg'].mean():.2f} | {sub['worst'].mean()*100:.1f} | "
            f"{sub['bad'].mean()*100:.1f} | {sub['bull'].mean()*100:.1f} | "
            f"{sub['hold_5m'].mean()*100:.1f} |")

def sharpe(sub):
    s = sub['day_chg'].std()
    return sub['day_chg'].mean() / s * np.sqrt(len(sub)) if s > 0 else 0.0

# ─── Output ───────────────────────────────────────────────────────────────────
lines = []
lines.append("# TSLA P10/P11 — SPY and QQQ Premarket Trend as TSLA Opening Filters")
lines.append(f"*Generated: 2026-03-18 | TSLA days: {len(df)} | SPY PM: {n_spy} days | QQQ PM: {n_qqq} days*")
lines.append("")

# ── P10: SPY PM conditioning ──────────────────────────────────────────────────
lines.append("## P10 — SPY Premarket Structure")
lines.append("")

spy_v = df.dropna(subset=['spy_pm_position'])

# P10a: SPY PM position quartiles
lines.append("### P10a — SPY PM Position at 9:29 (where does price sit in SPY's 4am–9:29 range)")
lines.append("")
spy_q = spy_v['spy_pm_position'].quantile([0.25, 0.5, 0.75])
lines.append(f"Thresholds: Q25={spy_q[0.25]:.3f}, Q50={spy_q[0.5]:.3f}, Q75={spy_q[0.75]:.3f}")
lines.append("")
lines.append(HDR); lines.append(SEP)
lines.append(fmt_row("All SPY PM days (baseline)", spy_v))
spy_v = spy_v.copy()
spy_v['spy_pos_q'] = pd.qcut(spy_v['spy_pm_position'], 4, labels=['Q1-bottom','Q2','Q3','Q4-top'])
for ql, qd in [('Q1-bottom','near PM low'),('Q2','lower-mid'),('Q3','upper-mid'),('Q4-top','near PM high')]:
    r = fmt_row(f"SPY {ql} ({qd})", spy_v[spy_v['spy_pos_q'] == ql])
    if r: lines.append(r)
lines.append("")

# P10b: SPY PM late trend
lines.append("### P10b — SPY PM Late Trend (9:20–9:29 direction)")
lines.append("")
spy_t = spy_v.dropna(subset=['spy_pm_late_trend'])
lines.append(HDR); lines.append(SEP)
lines.append(fmt_row("All SPY PM days (baseline)", spy_t))
for label, cond in [("SPY PM late UP",   spy_t['spy_pm_late_trend'] > 0),
                    ("SPY PM late DOWN", spy_t['spy_pm_late_trend'] <= 0)]:
    r = fmt_row(label, spy_t[cond])
    if r: lines.append(r)
lines.append("")

# P10c: SPY PM acceleration 9:25–9:29
lines.append("### P10c — SPY PM Acceleration (9:25–9:29)")
lines.append("")
spy_a = spy_v.dropna(subset=['spy_pm_accel'])
accel_q = spy_a['spy_pm_accel'].quantile([0.33, 0.67])
lines.append(HDR); lines.append(SEP)
lines.append(fmt_row("All SPY PM days (baseline)", spy_a))
for label, cond in [
    ("SPY accel strong DOWN (bot 33%)", spy_a['spy_pm_accel'] <= accel_q[0.33]),
    ("SPY accel mid",                  (spy_a['spy_pm_accel'] > accel_q[0.33]) & (spy_a['spy_pm_accel'] <= accel_q[0.67])),
    ("SPY accel strong UP (top 33%)",  spy_a['spy_pm_accel'] > accel_q[0.67]),
]:
    r = fmt_row(label, spy_a[cond])
    if r: lines.append(r)
lines.append("")

# P10d: SPY × TSLA PM trend alignment
lines.append("### P10d — SPY × TSLA PM Trend Alignment")
lines.append("")
al = df.dropna(subset=['spy_pm_late_trend', 'tsla_pm_late_trend']).copy()
al['spy_up']  = al['spy_pm_late_trend'] > 0
al['tsla_up'] = al['tsla_pm_late_trend'] > 0
lines.append(HDR); lines.append(SEP)
lines.append(fmt_row("All aligned days (baseline)", al))
for sd, td in [(True, True), (True, False), (False, True), (False, False)]:
    r = fmt_row(f"SPY PM {'UP' if sd else 'DOWN'} + TSLA PM {'UP' if td else 'DOWN'}",
                al[(al['spy_up'] == sd) & (al['tsla_up'] == td)])
    if r: lines.append(r)
lines.append("")

# P10e: Strategy comparison with SPY PM filters
lines.append("### P10e — Strategy Comparison with SPY PM Filters")
lines.append("")
lines.append("| Strategy | Trades | Win% | Avg P&L | Worst% | Sharpe |")
lines.append("|---|---|---|---|---|---|")

def strat_row(label, sub):
    if len(sub) == 0: return None
    n = len(sub)
    thin = " (thin)" if n < 25 else ""
    return (f"| {label}{thin} | {n} | {sub['day_above'].mean()*100:.1f}% | "
            f"{sub['day_chg'].mean():.2f} | {sub['worst'].mean()*100:.1f}% | "
            f"{sharpe(sub):.2f} |")

h_all = spy_t[spy_t['hold_5m']]
h_spy_up = spy_t[spy_t['hold_5m'] & (spy_t['spy_pm_late_trend'] > 0)]
h_spy_top = spy_t[spy_t['hold_5m'] & (spy_t['spy_pm_position'] >= spy_q[0.5])]
h_both = spy_t[spy_t['hold_5m'] & (spy_t['spy_pm_late_trend'] > 0) & (spy_t['spy_pm_position'] >= spy_q[0.5])]

lines.append(strat_row("5m rule alone (SPY PM days)", h_all))
lines.append(strat_row("5m + SPY PM top half (position)", h_spy_top))
lines.append(strat_row("5m + SPY PM late UP", h_spy_up))
lines.append(strat_row("5m + SPY PM top + late UP", h_both))
lines.append("")

# ── P11: QQQ PM conditioning ──────────────────────────────────────────────────
lines.append("## P11 — QQQ Premarket Structure")
lines.append("")

qqq_v = df.dropna(subset=['qqq_pm_position'])

# P11a: QQQ PM position quartiles
lines.append("### P11a — QQQ PM Position at 9:29")
lines.append("")
qqq_q = qqq_v['qqq_pm_position'].quantile([0.25, 0.5, 0.75])
lines.append(f"Thresholds: Q25={qqq_q[0.25]:.3f}, Q50={qqq_q[0.5]:.3f}, Q75={qqq_q[0.75]:.3f}")
lines.append("")
lines.append(HDR); lines.append(SEP)
lines.append(fmt_row("All QQQ PM days (baseline)", qqq_v))
qqq_v = qqq_v.copy()
qqq_v['qqq_pos_q'] = pd.qcut(qqq_v['qqq_pm_position'], 4, labels=['Q1-bottom','Q2','Q3','Q4-top'])
for ql, qd in [('Q1-bottom','near PM low'),('Q2','lower-mid'),('Q3','upper-mid'),('Q4-top','near PM high')]:
    r = fmt_row(f"QQQ {ql} ({qd})", qqq_v[qqq_v['qqq_pos_q'] == ql])
    if r: lines.append(r)
lines.append("")

# P11b: QQQ PM late trend
lines.append("### P11b — QQQ PM Late Trend (9:20–9:29 direction)")
lines.append("")
qqq_t = qqq_v.dropna(subset=['qqq_pm_late_trend'])
lines.append(HDR); lines.append(SEP)
lines.append(fmt_row("All QQQ PM days (baseline)", qqq_t))
for label, cond in [("QQQ PM late UP",   qqq_t['qqq_pm_late_trend'] > 0),
                    ("QQQ PM late DOWN", qqq_t['qqq_pm_late_trend'] <= 0)]:
    r = fmt_row(label, qqq_t[cond])
    if r: lines.append(r)
lines.append("")

# P11c: TSLA + SPY + QQQ triple alignment
lines.append("### P11c — Triple PM Alignment: TSLA + SPY + QQQ")
lines.append("")
lines.append("All three markets trending same direction in the last 10 PM minutes:")
lines.append("")
tri = df.dropna(subset=['tsla_pm_late_trend','spy_pm_late_trend','qqq_pm_late_trend']).copy()
tri['all_up']   = (tri['tsla_pm_late_trend'] > 0) & (tri['spy_pm_late_trend'] > 0) & (tri['qqq_pm_late_trend'] > 0)
tri['all_down'] = (tri['tsla_pm_late_trend'] <= 0) & (tri['spy_pm_late_trend'] <= 0) & (tri['qqq_pm_late_trend'] <= 0)
tri['mixed']    = ~(tri['all_up'] | tri['all_down'])

lines.append(HDR); lines.append(SEP)
lines.append(fmt_row("All triple-aligned days (baseline)", tri))
for label, mask in [("All three PM UP", tri['all_up']),
                    ("All three PM DOWN", tri['all_down']),
                    ("Mixed directions", tri['mixed'])]:
    r = fmt_row(label, tri[mask])
    if r: lines.append(r)
lines.append("")

# P11d: Triple alignment × 5m rule
lines.append("### P11d — Triple Alignment × 5m Rule")
lines.append("")
lines.append("| label | n | day_above% | avg_day_chg | worst% | hold_5m% |")
lines.append("|---|---|---|---|---|---|")
for pm_mask, pm_label in [(tri['all_up'], "all PM UP"), (~tri['all_up'], "NOT all PM UP")]:
    pm_sub = tri[pm_mask]
    for hold in [True, False]:
        sub  = pm_sub[pm_sub['hold_5m'] == hold]
        if len(sub) == 0: continue
        thin = " (thin)" if len(sub) < 15 else ""
        hs   = "HOLD" if hold else "BAIL"
        lines.append(f"| PM {pm_label} × 5m={hs}{thin} | {len(sub)} | "
                     f"{sub['day_above'].mean()*100:.1f} | {sub['day_chg'].mean():.2f} | "
                     f"{sub['worst'].mean()*100:.1f} | {sub['hold_5m'].mean()*100:.0f} |")
lines.append("")

# ── P12: Combined — TSLA P9 bear composite + SPY PM ──────────────────────────
lines.append("## P12 — Combined Filter: TSLA P9 Bear + SPY PM Trend")
lines.append("")
lines.append("TSLA P9 bear = PM position < 0.219 (Q1) AND accel < 0 (from prior research).")
lines.append("Testing whether adding SPY PM direction improves bad-day avoidance.")
lines.append("")

TSLA_Q1 = 0.219
combo = df.dropna(subset=['tsla_pm_position','tsla_pm_accel','spy_pm_late_trend']).copy()
combo['tsla_bear']  = (combo['tsla_pm_position'] < TSLA_Q1) & (combo['tsla_pm_accel'] < 0)
combo['spy_pm_up']  = combo['spy_pm_late_trend'] > 0
combo['qqq_pm_up']  = combo['qqq_pm_late_trend'] > 0 if 'qqq_pm_late_trend' in combo else False

lines.append("| Strategy | Trades | Win% | Avg P&L | Worst% | Sharpe |")
lines.append("|---|---|---|---|---|---|")

for label, mask in [
    ("5m rule (combo days)",            combo['hold_5m']),
    ("5m + skip TSLA P9 bear",          combo['hold_5m'] & ~combo['tsla_bear']),
    ("5m + SPY PM late UP",             combo['hold_5m'] & combo['spy_pm_up']),
    ("5m + skip TSLA P9 + SPY PM UP",   combo['hold_5m'] & ~combo['tsla_bear'] & combo['spy_pm_up']),
]:
    sub = combo[mask]
    if len(sub) == 0: continue
    thin = " (thin)" if len(sub) < 20 else ""
    r = (f"| {label}{thin} | {len(sub)} | {sub['day_above'].mean()*100:.1f}% | "
         f"{sub['day_chg'].mean():.2f} | {sub['worst'].mean()*100:.1f}% | {sharpe(sub):.2f} |")
    lines.append(r)
lines.append("")

# ── P13: SPY PM bear composite (mirror of TSLA P9) ───────────────────────────
lines.append("## P13 — SPY PM Bear Composite (mirror of TSLA P9)")
lines.append("")
lines.append("Test the same P9 logic on SPY: position < Q1 AND accel < 0.")
lines.append("")
spy_b = df.dropna(subset=['spy_pm_position','spy_pm_accel']).copy()
spy_q1_thresh = float(spy_v['spy_pm_position'].quantile(0.25))
spy_b['spy_bear'] = (spy_b['spy_pm_position'] < spy_q1_thresh) & (spy_b['spy_pm_accel'] < 0)
n_spy_bear = spy_b['spy_bear'].sum()
lines.append(f"SPY Q1 threshold: {spy_q1_thresh:.3f}")
lines.append(f"SPY bear days: {n_spy_bear} / {len(spy_b)} = {n_spy_bear/len(spy_b)*100:.0f}%")
lines.append("")
lines.append(HDR); lines.append(SEP)
lines.append(fmt_row("SPY PM bear days", spy_b[spy_b['spy_bear']]))
lines.append(fmt_row("SPY PM non-bear days", spy_b[~spy_b['spy_bear']]))
lines.append("")

n_worst_spy = spy_b['worst'].sum()
n_worst_caught = spy_b[spy_b['spy_bear'] & spy_b['worst']].shape[0]
n_good = spy_b[~spy_b['worst']].shape[0]
n_good_excluded = spy_b[spy_b['spy_bear'] & ~spy_b['worst']].shape[0]
lines.append(f"Worst-day capture: {n_worst_caught}/{n_worst_spy} = {n_worst_caught/n_worst_spy*100:.0f}%")
lines.append(f"Good-day false-exclude: {n_good_excluded}/{n_good} = {n_good_excluded/n_good*100:.0f}%")
lines.append("")

OUT.write_text("\n".join(lines))
print(f"\nOutput written to {OUT}")
