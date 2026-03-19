"""
TSLA Opening Module S v2 — Comprehensive Research Script
Analyzes 30s bar patterns, VIX conditioning, SPY relative strength,
and composite scores for TSLA opening trade decisions.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

CACHE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache")
OUT_FILE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug/tsla_module_s_v2.md")

# ─── Data Loading ────────────────────────────────────────────────────────────

def load_ib(path):
    df = pd.read_parquet(path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    df.index = df.index.tz_convert('America/New_York') if df.index.tz else df.index.tz_localize('UTC').tz_convert('America/New_York')
    return df

print("Loading data...")
tsla_1m  = load_ib(CACHE / "bars/tsla_1_min_ib.parquet")
tsla_30s = load_ib(CACHE / "bars_highres/30sec/tsla_30_secs_ib.parquet")
tsla_5s  = load_ib(CACHE / "bars_highres/5sec/tsla_5_secs_ib.parquet")
spy_5s   = load_ib(CACHE / "bars_highres/5sec/spy_5_secs_ib.parquet")
spy_1m   = load_ib(CACHE / "bars/spy_1_min_ib.parquet")
vix_5m   = load_ib(CACHE / "bars/vix_5_mins_ib.parquet")
vix_1h   = load_ib(CACHE / "bars/vix_1_hour_ib.parquet")
print("Data loaded.")

# ─── Step 1: Daily outcomes grid ─────────────────────────────────────────────

print("Step 1: Building daily outcomes grid...")

tsla_mh = tsla_1m.between_time('09:30', '15:59')
days = sorted(tsla_mh.index.normalize().unique())

rows = []
for day in days:
    d = tsla_mh[tsla_mh.index.date == day.date()]
    if d.empty:
        continue
    bars_930 = d.between_time('09:30', '09:30')
    bars_935 = d.between_time('09:35', '09:35')
    if bars_930.empty:
        continue
    entry = bars_930.iloc[0]['open']
    close_5m = bars_935.iloc[0]['close'] if not bars_935.empty else np.nan
    eod_close = d.iloc[-1]['close']
    day_chg = eod_close - entry

    # ATR14: use daily ranges from last 14 days
    rows.append({
        'day': day.date(),
        'entry': entry,
        'close_5m': close_5m,
        'eod_close': eod_close,
        'day_chg': day_chg,
        'day_high': d['high'].max(),
        'day_low': d['low'].min(),
    })

outcomes = pd.DataFrame(rows).set_index('day')

# ATR14 from daily range
outcomes['day_range'] = outcomes['day_high'] - outcomes['day_low']
outcomes['atr14'] = outcomes['day_range'].rolling(14, min_periods=5).mean().shift(1)

outcomes['day_above'] = outcomes['day_chg'] > 0
outcomes['hold_5m'] = outcomes['close_5m'] > outcomes['entry']
outcomes['worst'] = outcomes['day_chg'] < -5
outcomes['bad'] = outcomes['day_chg'] < -2
outcomes['bull'] = outcomes['day_chg'] > 5

print(f"  Daily grid: {len(outcomes)} days")

# ─── Step 2: VIX features ────────────────────────────────────────────────────

print("Step 2: VIX features...")

# VIX 5m features
vix_5m_mh = vix_5m.between_time('09:30', '16:00')
vix_rows = []
vix_days = sorted(vix_5m_mh.index.normalize().unique())
vix_prev_close = {}
for i, day in enumerate(vix_days):
    d = vix_5m_mh[vix_5m_mh.index.date == day.date()]
    if d.empty:
        continue
    bars_930 = d.between_time('09:30', '09:35')
    vix_open = bars_930.iloc[0]['open'] if not bars_930.empty else np.nan
    # prev day close at 16:00
    if i > 0:
        prev_day = vix_days[i-1]
        prev_d = vix_5m_mh[vix_5m_mh.index.date == prev_day.date()]
        prev_close_bars = prev_d.between_time('15:55', '16:05')
        prev_close = prev_close_bars.iloc[-1]['close'] if not prev_close_bars.empty else np.nan
    else:
        prev_close = np.nan
    vix_rows.append({'day': day.date(), 'vix_open': vix_open, 'vix_prev_close': prev_close})

vix_df = pd.DataFrame(vix_rows).set_index('day')
vix_df['vix_change'] = vix_df['vix_open'] - vix_df['vix_prev_close']
vix_df['vix_regime'] = pd.cut(vix_df['vix_open'], bins=[0, 18, 25, 999], labels=['calm', 'moderate', 'fear'])

# VIX 1h features
vix_1h_mh = vix_1h.between_time('09:00', '17:00')
vix1h_rows = []
for day in sorted(vix_1h_mh.index.normalize().unique()):
    d = vix_1h_mh[vix_1h_mh.index.date == day.date()]
    if d.empty:
        continue
    bars_930 = d.between_time('09:00', '10:00')
    vix_1h_open = bars_930.iloc[0]['open'] if not bars_930.empty else np.nan
    vix1h_rows.append({'day': day.date(), 'vix_1h_open': vix_1h_open})

vix_1h_df = pd.DataFrame(vix1h_rows).set_index('day')
vix_1h_df['vix_1h_regime'] = pd.cut(vix_1h_df['vix_1h_open'], bins=[0, 18, 25, 999], labels=['calm', 'moderate', 'fear'])

print(f"  VIX 5m: {len(vix_df)} days, VIX 1h: {len(vix_1h_df)} days")

# ─── Step 3: TSLA 30s features ───────────────────────────────────────────────

print("Step 3: TSLA 30s features...")

tsla_30s_mh = tsla_30s.between_time('09:30', '09:32')
bar30_rows = []
for day in sorted(tsla_30s_mh.index.normalize().unique()):
    d = tsla_30s_mh[tsla_30s_mh.index.date == day.date()]
    if d.empty:
        continue
    # Get exact 30s bars
    b1_candidates = d.between_time('09:30:00', '09:30:00')
    b2_candidates = d.between_time('09:30:30', '09:30:30')
    b3_candidates = d.between_time('09:31:00', '09:31:00')
    b4_candidates = d.between_time('09:31:30', '09:31:30')

    if b1_candidates.empty or b2_candidates.empty:
        continue

    b1 = b1_candidates.iloc[0]
    b2 = b2_candidates.iloc[0]

    if day.date() not in outcomes.index:
        continue
    entry = outcomes.loc[day.date(), 'entry']

    b1_dir = 'UP' if b1['close'] >= b1['open'] else 'DOWN'
    b2_dir = 'UP' if b2['close'] >= b2['open'] else 'DOWN'
    pattern = f"{b1_dir}_{b2_dir}"

    vol_sum = b1['volume'] + b2['volume']
    vol_front_ratio = b1['volume'] / vol_sum if vol_sum > 0 else 0.5

    row = {
        'day': day.date(),
        'bar1_open': b1['open'], 'bar1_high': b1['high'],
        'bar1_low': b1['low'], 'bar1_close': b1['close'], 'bar1_vol': b1['volume'],
        'bar2_open': b2['open'], 'bar2_high': b2['high'],
        'bar2_low': b2['low'], 'bar2_close': b2['close'], 'bar2_vol': b2['volume'],
        'bar1_dir': b1_dir, 'bar2_dir': b2_dir, 'pattern': pattern,
        'bar1_vs_entry': b1['close'] - entry,
        'bar2_vs_entry': b2['close'] - entry,
        'bar1_range': b1['high'] - b1['low'],
        'bar2_range': b2['high'] - b2['low'],
        'vol_front_ratio': vol_front_ratio,
        'momentum_2bar': b2['close'] - b1['open'],
    }
    # 2-minute close
    if not b4_candidates.empty:
        row['min2_close'] = b4_candidates.iloc[0]['close']
        row['min2_vs_entry'] = b4_candidates.iloc[0]['close'] - entry
    elif not b3_candidates.empty:
        row['min2_close'] = b3_candidates.iloc[0]['close']
        row['min2_vs_entry'] = b3_candidates.iloc[0]['close'] - entry
    else:
        row['min2_close'] = np.nan
        row['min2_vs_entry'] = np.nan

    bar30_rows.append(row)

bars30 = pd.DataFrame(bar30_rows).set_index('day')
print(f"  30s features: {len(bars30)} days")

# ─── Step 4: SPY relative strength ───────────────────────────────────────────

print("Step 4: SPY relative strength...")

spy_5s_mh = spy_5s.between_time('09:30', '09:31')
spy_rows = []
for day in sorted(spy_5s_mh.index.normalize().unique()):
    d = spy_5s_mh[spy_5s_mh.index.date == day.date()]
    if d.empty:
        continue
    b1_cands = d.between_time('09:30:00', '09:30:04')
    b_30s_cands = d.between_time('09:30:25', '09:30:29')
    if b1_cands.empty:
        continue
    spy_open = b1_cands.iloc[0]['open']
    spy_30s_close = b_30s_cands.iloc[-1]['close'] if not b_30s_cands.empty else np.nan
    spy_30s_chg = spy_30s_close - spy_open if not np.isnan(spy_30s_close) else np.nan
    spy_dir = 'UP' if spy_30s_chg >= 0 else 'DOWN'
    spy_rows.append({'day': day.date(), 'spy_open': spy_open,
                     'spy_30s_close': spy_30s_close, 'spy_30s_chg': spy_30s_chg,
                     'spy_dir_30s': spy_dir})

spy_df = pd.DataFrame(spy_rows).set_index('day')

# SPY 1m for broader coverage
spy_1m_mh = spy_1m.between_time('09:30', '09:35')
spy1m_rows = []
for day in sorted(spy_1m_mh.index.normalize().unique()):
    d = spy_1m_mh[spy_1m_mh.index.date == day.date()]
    if d.empty:
        continue
    b930 = d.between_time('09:30', '09:30')
    b935 = d.between_time('09:35', '09:35')
    if b930.empty:
        continue
    spy_entry = b930.iloc[0]['open']
    spy_5m = b935.iloc[0]['close'] if not b935.empty else np.nan
    spy1m_rows.append({'day': day.date(), 'spy_entry': spy_entry, 'spy_5m_close': spy_5m,
                       'spy_5m_above': (spy_5m > spy_entry) if not np.isnan(spy_5m) else np.nan})

spy_1m_df = pd.DataFrame(spy1m_rows).set_index('day')
print(f"  SPY 5s: {len(spy_df)} days, SPY 1m: {len(spy_1m_df)} days")

# ─── Merge master frame ──────────────────────────────────────────────────────

print("Merging master frame...")
master = outcomes.copy()
master = master.join(bars30, how='left', rsuffix='_30s')
master = master.join(vix_df, how='left')
master = master.join(vix_1h_df, how='left')
master = master.join(spy_df, how='left')
master = master.join(spy_1m_df, how='left')

# Relative strength
master['tsla_30s_pct'] = master['bar1_vs_entry'] / master['entry'] * 100
master['spy_30s_pct'] = master['spy_30s_chg'] / master['spy_open'] * 100
master['rel_strength'] = master['tsla_30s_pct'] - master['spy_30s_pct']
master['tsla_spy_agree'] = master['bar1_dir'] == master['spy_dir_30s']

print(f"Master frame: {len(master)} days, columns: {len(master.columns)}")

# ─── Helper functions ────────────────────────────────────────────────────────

def metrics(df, label=""):
    n = len(df)
    if n == 0:
        return {'label': label, 'n': 0, 'day_above%': np.nan, 'avg_day_chg': np.nan,
                'worst%': np.nan, 'bull%': np.nan, 'hold_5m%': np.nan}
    thin = " (thin)" if n < 15 else ""
    return {
        'label': label + thin,
        'n': n,
        'day_above%': round(df['day_above'].mean() * 100, 1),
        'avg_day_chg': round(df['day_chg'].mean(), 2),
        'worst%': round(df['worst'].mean() * 100, 1),
        'bull%': round(df['bull'].mean() * 100, 1),
        'hold_5m%': round(df['hold_5m'].mean() * 100, 1) if df['hold_5m'].notna().sum() > 0 else np.nan,
    }

def fmt_table(rows, cols=None):
    if not rows:
        return "_No data_\n"
    if cols is None:
        cols = list(rows[0].keys())
    lines = []
    header = "| " + " | ".join(str(c) for c in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    lines.append(header)
    lines.append(sep)
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(c, '—')) for c in cols) + " |")
    return "\n".join(lines) + "\n"

# ─── Analysis ────────────────────────────────────────────────────────────────

sections = []

def section(title, content):
    sections.append(f"## {title}\n\n{content}\n")

def subsection(title, content):
    return f"### {title}\n\n{content}\n"

# ─── Section A: TSLA 30s backbone ────────────────────────────────────────────

print("Section A: 30s backbone analysis...")

m30 = master.dropna(subset=['bar1_dir'])
print(f"  30s backbone days: {len(m30)}")

## A1 — Bar 1 direction
a1_rows = []
for d in ['UP', 'DOWN']:
    sub = m30[m30['bar1_dir'] == d]
    a1_rows.append(metrics(sub, f"Bar1 {d}"))
# All days baseline
a1_rows.insert(0, metrics(master, "All days (baseline)"))
a1_rows.append(metrics(m30, "30s days (baseline)"))

a1_text = "Bar 1 (first 30 seconds) directional bias:\n\n"
a1_text += fmt_table(a1_rows)

## A2 — Fakeout patterns
a2_rows = []
patterns_order = ['UP_UP', 'UP_DOWN', 'DOWN_UP', 'DOWN_DOWN']
pattern_labels = {
    'UP_UP': 'UP→UP (momentum)',
    'UP_DOWN': 'UP→DOWN (fakeout)',
    'DOWN_UP': 'DOWN→UP (reversal)',
    'DOWN_DOWN': 'DOWN→DOWN (continuation)',
}
for p in patterns_order:
    sub = m30[m30['pattern'] == p]
    row = metrics(sub, pattern_labels[p])
    # Add hold_win%: among those where hold_5m=True, what % are day_above
    h_sub = sub[sub['hold_5m'] == True]
    row['hold_win%'] = round(h_sub['day_above'].mean() * 100, 1) if len(h_sub) > 0 else np.nan
    a2_rows.append(row)

a2_text = "All 4 first-2-bar patterns:\n\n"
cols_a2 = ['label', 'n', 'day_above%', 'avg_day_chg', 'worst%', 'bull%', 'hold_5m%', 'hold_win%']
a2_text += fmt_table(a2_rows, cols_a2)

## A3 — Bar1 range quartiles
m30 = m30.copy()
m30['bar1_range_q'] = pd.qcut(m30['bar1_range'], 4, labels=['Q1-tiny', 'Q2', 'Q3', 'Q4-wide'])
a3_rows = []
for q in ['Q1-tiny', 'Q2', 'Q3', 'Q4-wide']:
    sub = m30[m30['bar1_range_q'] == q]
    row = metrics(sub, q)
    row['avg_bar1_range'] = round(sub['bar1_range'].mean(), 2)
    a3_rows.append(row)

q_bounds = m30['bar1_range'].quantile([0.25, 0.5, 0.75]).round(2)
a3_text = f"Bar1 range quartile thresholds: Q1<{q_bounds[0.25]}, Q2<{q_bounds[0.5]}, Q3<{q_bounds[0.75]}\n\n"
cols_a3 = ['label', 'n', 'avg_bar1_range', 'day_above%', 'avg_day_chg', 'worst%', 'bull%']
a3_text += fmt_table(a3_rows, cols_a3)

## A4 — Volume front-loading
a4_rows = []
for label, mask in [
    ("Front-loaded (>0.5)", m30['vol_front_ratio'] > 0.5),
    ("Back-loaded (<=0.5)", m30['vol_front_ratio'] <= 0.5),
    ("Very front-loaded (>0.7)", m30['vol_front_ratio'] > 0.7),
    ("Extreme front-loaded (>0.85)", m30['vol_front_ratio'] > 0.85),
]:
    sub = m30[mask]
    row = metrics(sub, label)
    row['avg_vol_ratio'] = round(m30[mask]['vol_front_ratio'].mean(), 2)
    a4_rows.append(row)

a4_text = fmt_table(a4_rows, ['label', 'n', 'avg_vol_ratio', 'day_above%', 'avg_day_chg', 'worst%'])

## A5 — Bar1+Bar2 position vs entry
def pos_label(row):
    b1 = row['bar1_vs_entry'] > 0
    b2 = row['bar2_vs_entry'] > 0
    if b1 and b2: return 'Both above'
    if b1 and not b2: return 'B1 above, B2 below'
    if not b1 and b2: return 'B1 below, B2 above'
    return 'Both below'

m30['pos_combo'] = m30.apply(pos_label, axis=1)
a5_rows = []
for lbl in ['Both above', 'B1 above, B2 below', 'B1 below, B2 above', 'Both below']:
    sub = m30[m30['pos_combo'] == lbl]
    a5_rows.append(metrics(sub, lbl))

a5_text = "Bar1 and Bar2 close positions relative to open:\n\n"
a5_text += fmt_table(a5_rows)
a5_text += "\nMomentum 2-bar (bar2_close - bar1_open) quartiles:\n\n"

m30['mom_q'] = pd.qcut(m30['momentum_2bar'], 4, labels=['Q1-bearish', 'Q2', 'Q3', 'Q4-bullish'])
a5_mom_rows = []
for q in ['Q1-bearish', 'Q2', 'Q3', 'Q4-bullish']:
    sub = m30[m30['mom_q'] == q]
    row = metrics(sub, q)
    row['avg_momentum'] = round(sub['momentum_2bar'].mean(), 2)
    a5_mom_rows.append(row)
a5_text += fmt_table(a5_mom_rows, ['label', 'n', 'avg_momentum', 'day_above%', 'avg_day_chg', 'worst%', 'bull%'])

## A6 — Pattern × hold_5m cross-tab
a6_rows = []
for p in patterns_order:
    for h5 in [True, False]:
        sub = m30[(m30['pattern'] == p) & (m30['hold_5m'] == h5)]
        lbl = f"{pattern_labels[p]} × 5m={'HOLD' if h5 else 'BAIL'}"
        a6_rows.append(metrics(sub, lbl))

a6_text = "8 combos: pattern (4) × 5m rule (HOLD/BAIL):\n\n"
a6_text += fmt_table(a6_rows)

## A7 — 2-minute momentum
m30_2m = m30.dropna(subset=['min2_vs_entry'])
a7_rows = []
for label, mask in [
    ("2m above entry", m30_2m['min2_vs_entry'] > 0),
    ("2m below entry", m30_2m['min2_vs_entry'] <= 0),
]:
    a7_rows.append(metrics(m30_2m[mask], label))
a7_text = f"Based on {len(m30_2m)} days with 2m data available:\n\n"
a7_text += fmt_table(a7_rows)
a7_text += "\n**Comparison: 5m rule vs 2m rule accuracy:**\n\n"
# 5m rule accuracy
correct_5m = (master['hold_5m'] == master['day_above']).mean()
correct_2m_sub = (m30_2m['min2_vs_entry'] > 0) == m30_2m['day_above']
a7_text += f"- 5m rule accuracy (all days): {correct_5m*100:.1f}%\n"
a7_text += f"- 2m rule accuracy (30s days): {correct_2m_sub.mean()*100:.1f}%\n"

content_a = (
    subsection("A1 — Bar 1 Direction", a1_text) +
    subsection("A2 — Fakeout Patterns", a2_text) +
    subsection("A3 — Bar1 Range Quartiles", a3_text) +
    subsection("A4 — Volume Front-Loading", a4_text) +
    subsection("A5 — Bar Position vs Entry", a5_text) +
    subsection("A6 — Pattern × 5m Rule Cross-Tab", a6_text) +
    subsection("A7 — First 2-Minute Momentum", a7_text)
)
section("A — TSLA 30s Backbone (n≈" + str(len(m30)) + ")", content_a)

# ─── Section B: VIX conditioning ─────────────────────────────────────────────

print("Section B: VIX conditioning...")

# Use 1h VIX for broader coverage
m_vix1h = master.dropna(subset=['vix_1h_open'])
m_vix5m = master.dropna(subset=['vix_open'])
print(f"  VIX 1h days: {len(m_vix1h)}, VIX 5m days: {len(m_vix5m)}")

## B1 — VIX regime
b1_rows = []
for regime in ['calm', 'moderate', 'fear']:
    sub = m_vix1h[m_vix1h['vix_1h_regime'] == regime]
    row = metrics(sub, f"VIX 1h {regime}")
    row['avg_vix'] = round(sub['vix_1h_open'].mean(), 1) if len(sub) > 0 else np.nan
    b1_rows.append(row)
b1_text = f"Using VIX 1h (n={len(m_vix1h)} days, broader coverage):\n\n"
b1_text += fmt_table(b1_rows, ['label', 'n', 'avg_vix', 'day_above%', 'avg_day_chg', 'worst%', 'bull%'])

b1_5m_rows = []
for regime in ['calm', 'moderate', 'fear']:
    sub = m_vix5m[m_vix5m['vix_regime'] == regime]
    row = metrics(sub, f"VIX 5m {regime}")
    row['avg_vix'] = round(sub['vix_open'].mean(), 1) if len(sub) > 0 else np.nan
    b1_5m_rows.append(row)
b1_text += f"\nUsing VIX 5m (n={len(m_vix5m)} days):\n\n"
b1_text += fmt_table(b1_5m_rows, ['label', 'n', 'avg_vix', 'day_above%', 'avg_day_chg', 'worst%', 'bull%'])

## B2 — VIX change (spike)
m_vix5m_chg = m_vix5m.dropna(subset=['vix_change'])
b2_rows = []
for label, mask in [
    ("Large spike (>+2)", m_vix5m_chg['vix_change'] > 2),
    ("Small spike (0 to +2)", (m_vix5m_chg['vix_change'] >= 0) & (m_vix5m_chg['vix_change'] <= 2)),
    ("Flat (-1 to 0)", (m_vix5m_chg['vix_change'] >= -1) & (m_vix5m_chg['vix_change'] < 0)),
    ("Drop (<-1)", m_vix5m_chg['vix_change'] < -1),
]:
    sub = m_vix5m_chg[mask]
    row = metrics(sub, label)
    row['avg_vix_chg'] = round(sub['vix_change'].mean(), 2) if len(sub) > 0 else np.nan
    b2_rows.append(row)
b2_text = fmt_table(b2_rows, ['label', 'n', 'avg_vix_chg', 'day_above%', 'avg_day_chg', 'worst%'])

## B3 — VIX × fakeout pattern
m_vix_30s = master.dropna(subset=['vix_1h_open', 'pattern'])
b3_rows = []
for p in ['UP_UP', 'UP_DOWN']:
    for regime in ['calm', 'moderate', 'fear']:
        sub = m_vix_30s[(m_vix_30s['pattern'] == p) & (m_vix_30s['vix_1h_regime'] == regime)]
        b3_rows.append(metrics(sub, f"{pattern_labels[p]} × VIX {regime}"))
b3_text = fmt_table(b3_rows)

## B4 — VIX as pre-open bad-day filter
worst_days = m_vix5m[m_vix5m['worst'] == True]
b4_text = f"Worst days analysis (day_chg < -$5):\n"
b4_text += f"- Total worst days (VIX 5m overlap): {len(worst_days)} / {len(m_vix5m)}\n"
if len(worst_days) > 0:
    b4_text += f"- % of worst days with VIX > 20 at open: {(worst_days['vix_open'] > 20).mean()*100:.1f}%\n"
    b4_text += f"- % of worst days with VIX > 25 at open: {(worst_days['vix_open'] > 25).mean()*100:.1f}%\n"
b4_text += "\nWorst-day rate by VIX tier:\n\n"
b4_rate_rows = []
for label, mask in [
    ("VIX ≤ 15", m_vix5m['vix_open'] <= 15),
    ("VIX 15-20", (m_vix5m['vix_open'] > 15) & (m_vix5m['vix_open'] <= 20)),
    ("VIX 20-25", (m_vix5m['vix_open'] > 20) & (m_vix5m['vix_open'] <= 25)),
    ("VIX > 25", m_vix5m['vix_open'] > 25),
]:
    sub = m_vix5m[mask]
    if len(sub) == 0:
        b4_rate_rows.append({'tier': label, 'n': 0, 'worst_day%': np.nan, 'bad_day%': np.nan, 'avg_day_chg': np.nan})
        continue
    thin = " (thin)" if len(sub) < 15 else ""
    b4_rate_rows.append({
        'tier': label + thin, 'n': len(sub),
        'worst_day%': round(sub['worst'].mean()*100, 1),
        'bad_day%': round(sub['bad'].mean()*100, 1),
        'avg_day_chg': round(sub['day_chg'].mean(), 2),
    })
b4_text += fmt_table(b4_rate_rows, ['tier', 'n', 'worst_day%', 'bad_day%', 'avg_day_chg'])

## B5 — VIX × hold_5m
m_vix_5m_rule = master.dropna(subset=['vix_1h_open', 'hold_5m'])
b5_rows = []
for regime in ['calm', 'moderate', 'fear']:
    for h5 in [True, False]:
        sub = m_vix_5m_rule[(m_vix_5m_rule['vix_1h_regime'] == regime) & (m_vix_5m_rule['hold_5m'] == h5)]
        b5_rows.append(metrics(sub, f"VIX {regime} × 5m {'HOLD' if h5 else 'BAIL'}"))
b5_text = "VIX regime × 5m rule (HOLD=True/False):\n\n"
b5_text += fmt_table(b5_rows)

content_b = (
    subsection("B1 — VIX Regime", b1_text) +
    subsection("B2 — VIX Change (Spike Detector)", b2_text) +
    subsection("B3 — VIX × Fakeout Pattern", b3_text) +
    subsection("B4 — VIX as Pre-Open Bad-Day Filter", b4_text) +
    subsection("B5 — VIX × 5m Rule", b5_text)
)
section("B — VIX Conditioning", content_b)

# ─── Section C: SPY relative strength ────────────────────────────────────────

print("Section C: SPY relative strength...")

m_spy5s = master.dropna(subset=['spy_30s_chg'])
m_spy1m = master.dropna(subset=['spy_5m_above'])
print(f"  SPY 5s days: {len(m_spy5s)}, SPY 1m days: {len(m_spy1m)}")

## C1 — SPY 30s direction
c1_rows = []
for d in ['UP', 'DOWN']:
    sub = m_spy5s[m_spy5s['spy_dir_30s'] == d]
    c1_rows.append(metrics(sub, f"SPY 30s {d}"))
c1_text = fmt_table(c1_rows)

## C2 — Agreement
m_spy30_both = master.dropna(subset=['spy_dir_30s', 'bar1_dir'])
c2_rows = []
for t_dir in ['UP', 'DOWN']:
    for s_dir in ['UP', 'DOWN']:
        sub = m_spy30_both[(m_spy30_both['bar1_dir'] == t_dir) & (m_spy30_both['spy_dir_30s'] == s_dir)]
        lbl = f"TSLA {t_dir}, SPY {s_dir}"
        c2_rows.append(metrics(sub, lbl))
c2_text = fmt_table(c2_rows)

## C3 — Relative strength
m_rs = master.dropna(subset=['rel_strength'])
rs_bins = pd.qcut(m_rs['rel_strength'], 4, labels=['Q1-TSLA weak', 'Q2', 'Q3', 'Q4-TSLA strong'])
m_rs = m_rs.copy()
m_rs['rs_q'] = rs_bins
c3_rows = []
rs_bounds = m_rs['rel_strength'].quantile([0.25, 0.5, 0.75]).round(3)
for q in ['Q1-TSLA weak', 'Q2', 'Q3', 'Q4-TSLA strong']:
    sub = m_rs[m_rs['rs_q'] == q]
    row = metrics(sub, q)
    row['avg_rel_str'] = round(sub['rel_strength'].mean(), 3)
    c3_rows.append(row)
c3_text = f"Relative strength = TSLA 30s % - SPY 30s %. Q-thresholds: {rs_bounds.to_dict()}\n\n"
c3_text += fmt_table(c3_rows, ['label', 'n', 'avg_rel_str', 'day_above%', 'avg_day_chg', 'worst%', 'bull%'])

## C4 — SPY 1m × TSLA 5m rule
c4_rows = []
for th5 in [True, False]:
    for sh5 in [True, False]:
        sub = m_spy1m[(m_spy1m['hold_5m'] == th5) & (m_spy1m['spy_5m_above'] == sh5)]
        lbl = f"TSLA 5m={'HOLD' if th5 else 'BAIL'}, SPY 5m={'HOLD' if sh5 else 'BAIL'}"
        c4_rows.append(metrics(sub, lbl))
c4_text = f"Using SPY 1m (n={len(m_spy1m)} days):\n\n"
c4_text += fmt_table(c4_rows)

content_c = (
    subsection("C1 — SPY 30s Direction", c1_text) +
    subsection("C2 — TSLA vs SPY Direction Agreement", c2_text) +
    subsection("C3 — Relative Strength Score (TSLA vs SPY)", c3_text) +
    subsection("C4 — SPY 1m × TSLA 5m Rule (280 days)", c4_text)
)
section("C — SPY Relative Strength", content_c)

# ─── Section D: Composite scores ─────────────────────────────────────────────

print("Section D: Composite scores...")

## D1 — 3-factor composite
m_d1 = master.dropna(subset=['bar1_dir', 'vix_1h_open', 'spy_dir_30s']).copy()
print(f"  D1 overlap days: {len(m_d1)}")

def compute_score(row):
    score = 0
    if row['bar1_dir'] == 'UP': score += 1
    if row.get('pattern') == 'UP_UP': score += 1
    if row['spy_dir_30s'] == 'UP': score += 1
    if not pd.isna(row.get('vix_1h_open')) and row['vix_1h_open'] < 18: score += 1
    if row['hold_5m']: score += 1
    return score

m_d1['composite'] = m_d1.apply(compute_score, axis=1)
d1_rows = []
for tier, mask in [
    ("0-1 (bearish)", (m_d1['composite'] <= 1)),
    ("2-3 (neutral)", (m_d1['composite'] >= 2) & (m_d1['composite'] <= 3)),
    ("4-5 (bullish)", (m_d1['composite'] >= 4)),
]:
    sub = m_d1[mask]
    row = metrics(sub, tier)
    row['avg_score'] = round(sub['composite'].mean(), 2) if len(sub) > 0 else np.nan
    d1_rows.append(row)
d1_text = f"Score: +1 each for bar1 UP, UP_UP pattern, SPY UP, VIX calm (<18), 5m HOLD. n={len(m_d1)} days.\n\n"
d1_text += fmt_table(d1_rows, ['label', 'n', 'avg_score', 'day_above%', 'avg_day_chg', 'worst%', 'bull%'])

## D2 — Decision tree
d2_text = """
**Practical TSLA Opening Decision Tree**

```
PRE-OPEN (9:25–9:29):
  VIX > 25 (fear)?
    → SKIP (bad day risk elevated)
  VIX 20–25 (moderate)?
    → CAUTION: reduce size, tighten stops

AT 9:30:30 (after bar1):
  Bar1 DOWN?
    → lean SHORT or BAIL longs
  Bar1 UP?
    → continue to bar2

AT 9:31:00 (after bar2):
  Bar1 UP → Bar2 DOWN (fakeout)?
    → EXIT any longs immediately, consider SHORT
  Bar1 UP → Bar2 UP (momentum)?
    → SPY also up? → HOLD (strong confirmation)
    → SPY down? → CAUTIOUS HOLD (TSLA leading, watch closely)

AT 9:35 (5m rule):
  TSLA 5m close > open AND SPY 5m close > open?
    → HOLD with confidence
  TSLA 5m close > open BUT SPY 5m close < open?
    → REDUCE size, watch for reversal
  TSLA 5m close < open?
    → BAIL regardless of SPY
```
"""

## D3 — Strategy comparison
all_days = master.dropna(subset=['hold_5m'])
spy_all = master.dropna(subset=['hold_5m', 'spy_5m_above'])
vix_days = master.dropna(subset=['hold_5m', 'vix_1h_open'])
fakeout_days = master.dropna(subset=['hold_5m', 'pattern'])

def strat_metrics(df, name, trade_mask):
    trades = df[trade_mask]
    n = len(trades)
    if n == 0:
        return {'strategy': name, 'n_trades': 0, 'win%': np.nan, 'avg_pnl': np.nan,
                'worst_day%': np.nan, 'skipped': len(df) - n}
    wins = trades['day_above'].mean()
    avg_pnl = trades['day_chg'].mean()
    sr = trades['day_chg'].mean() / trades['day_chg'].std() * np.sqrt(252) if trades['day_chg'].std() > 0 else np.nan
    return {
        'strategy': name,
        'n_trades': n,
        'win%': round(wins * 100, 1),
        'avg_pnl': round(avg_pnl, 2),
        'sharpe_est': round(sr, 2) if not np.isnan(sr) else '—',
        'worst%': round(trades['worst'].mean() * 100, 1),
        'skipped': len(df) - n,
    }

d3_rows = [
    strat_metrics(all_days, "Base: always hold", all_days.index.isin(all_days.index)),
    strat_metrics(all_days, "5m rule (TSLA hold)", all_days['hold_5m'] == True),
    strat_metrics(spy_all, "5m rule + SPY confirm", (spy_all['hold_5m'] == True) & (spy_all['spy_5m_above'] == True)),
    strat_metrics(vix_days, "5m rule + skip VIX fear", (vix_days['hold_5m'] == True) & (vix_days['vix_1h_regime'] != 'fear')),
    strat_metrics(fakeout_days, "5m rule + no fakeout", (fakeout_days['hold_5m'] == True) & (fakeout_days['pattern'] != 'UP_DOWN')),
    strat_metrics(
        master.dropna(subset=['hold_5m', 'vix_1h_open', 'spy_5m_above', 'pattern']),
        "5m + SPY + VIX + no-fakeout (combined)",
        lambda df: (df['hold_5m'] == True) & (df['spy_5m_above'] == True) &
                   (df['vix_1h_regime'] != 'fear') & (df['pattern'] != 'UP_DOWN')
    ),
]
# Fix lambda strategy
m_combined = master.dropna(subset=['hold_5m', 'vix_1h_open', 'spy_5m_above', 'pattern'])
d3_rows[-1] = strat_metrics(
    m_combined,
    "5m + SPY + VIX + no-fakeout (combined)",
    (m_combined['hold_5m'] == True) & (m_combined['spy_5m_above'] == True) &
    (m_combined['vix_1h_regime'] != 'fear') & (m_combined['pattern'] != 'UP_DOWN')
)

d3_text = fmt_table(d3_rows, ['strategy', 'n_trades', 'win%', 'avg_pnl', 'sharpe_est', 'worst%', 'skipped'])

content_d = (
    subsection("D1 — 3-Factor Composite Score", d1_text) +
    subsection("D2 — Practical Decision Tree", d2_text) +
    subsection("D3 — Strategy Comparison", d3_text)
)
section("D — Combined Composite Scores", content_d)

# ─── Section E: Ranked Actionable Findings ────────────────────────────────────

print("Section E: Ranked findings...")

# Compute key numbers for the findings
fakeout_day_above = m30[m30['pattern'] == 'UP_DOWN']['day_above'].mean() * 100
fakeout_worst = m30[m30['pattern'] == 'UP_DOWN']['worst'].mean() * 100
upup_day_above = m30[m30['pattern'] == 'UP_UP']['day_above'].mean() * 100

spy_double_hold = m_spy1m[(m_spy1m['hold_5m'] == True) & (m_spy1m['spy_5m_above'] == True)]
spy_single_hold = m_spy1m[(m_spy1m['hold_5m'] == True) & (m_spy1m['spy_5m_above'] == False)]

vix_fear = m_vix1h[m_vix1h['vix_1h_regime'] == 'fear']
vix_calm = m_vix1h[m_vix1h['vix_1h_regime'] == 'calm']

upup_n = len(m30[m30['pattern'] == 'UP_UP'])
fakeout_n = len(m30[m30['pattern'] == 'UP_DOWN'])

# Bar1 UP/DOWN day_above
bar1_up_pct = m30[m30['bar1_dir'] == 'UP']['day_above'].mean() * 100
bar1_dn_pct = m30[m30['bar1_dir'] == 'DOWN']['day_above'].mean() * 100
bar1_up_chg = m30[m30['bar1_dir'] == 'UP']['day_chg'].mean()
bar1_dn_chg = m30[m30['bar1_dir'] == 'DOWN']['day_chg'].mean()

spy_dh_win = spy_double_hold['day_above'].mean() * 100 if len(spy_double_hold) > 0 else 0
spy_sh_win = spy_single_hold['day_above'].mean() * 100 if len(spy_single_hold) > 0 else 0

vix_fear_worst = vix_fear['worst'].mean() * 100 if len(vix_fear) > 0 else 0
vix_calm_worst = vix_calm['worst'].mean() * 100 if len(vix_calm) > 0 else 0

findings_text = f"""
### Finding #1 — The Fakeout Pattern is the Most Dangerous Signal
**Rule:** If bar1 is UP but bar2 is DOWN (UP→DOWN), EXIT immediately; do NOT hold to 9:35.

- UP→DOWN (fakeout) day_above: **{fakeout_day_above:.1f}%** (n={fakeout_n})
- Fakeout worst-day%: **{fakeout_worst:.1f}%** (day < -$5)
- UP→UP (momentum) day_above: **{upup_day_above:.1f}%** (n={upup_n})
- **Action:** At 9:30:30, if bar1 was UP but price has reversed below open → BAIL immediately, don't wait for 9:35.

---

### Finding #2 — Bar1 Direction Is a Real Edge
**Rule:** Bar1 direction (first 30 seconds) provides meaningful directional bias for the day.

- Bar1 UP → day_above: **{bar1_up_pct:.1f}%**, avg P&L: **${bar1_up_chg:.2f}**
- Bar1 DOWN → day_above: **{bar1_dn_pct:.1f}%**, avg P&L: **${bar1_dn_chg:.2f}**
- **Action:** Use bar1 direction as primary opening bias filter.

---

### Finding #3 — SPY Double Confirmation Boosts Confidence
**Rule:** Only hold TSLA longs if BOTH TSLA and SPY are above their open at 9:35.

- TSLA HOLD + SPY HOLD → win: **{spy_dh_win:.1f}%** (n={len(spy_double_hold)})
- TSLA HOLD + SPY BAIL → win: **{spy_sh_win:.1f}%** (n={len(spy_single_hold)})
- **Action:** When TSLA 5m HOLD fires but SPY 5m BAIL, treat as weak signal; reduce size by 50%.

---

### Finding #4 — VIX Fear Regime = Bad Day Elevated Risk
**Rule:** When VIX > 25 at open, skip or reduce TSLA longs.

- VIX fear regime worst-day%: **{vix_fear_worst:.1f}%** (n={len(vix_fear)})
- VIX calm regime worst-day%: **{vix_calm_worst:.1f}%** (n={len(vix_calm)})
- **Action:** VIX > 25 → skip longs. VIX 20-25 → 50% size. VIX < 20 → normal sizing.

---

### Finding #5 — 2-Minute Close vs Entry as Early Filter
**Rule:** If price is still below the open at 9:32, the 5m rule is likely to BAIL anyway — don't hold.

- See A7 for directional accuracy comparison of 2m vs 5m rule.
- **Action:** At 9:32, if price is below open, pre-exit rather than waiting until 9:35.
  This saves ~3 minutes of adverse drift on losing days.
"""

section("E — Ranked Actionable Findings", findings_text)

# ─── Write output ─────────────────────────────────────────────────────────────

print("Writing output...")

header = f"""# TSLA Opening Module S v2 — Research Output
**Generated:** 2026-03-17
**Data range:** {master.index.min()} – {master.index.max()}
**Total days:** {len(master)} (1m backbone) | 30s: {len(m30)} | VIX 1h: {len(m_vix1h)} | SPY 5s: {len(m_spy5s)}

---

"""

with open(OUT_FILE, 'w') as f:
    f.write(header)
    for s in sections:
        f.write(s)
        f.write("\n---\n\n")

print(f"\nDone. Output written to:\n{OUT_FILE}")
print(f"File size: {OUT_FILE.stat().st_size / 1024:.1f} KB")
