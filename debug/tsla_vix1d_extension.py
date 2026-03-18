"""
TSLA VIX 1d Extension — Extends VIX regime conditioning from 85 to ~250 days
Uses VIX 1d prev-day close as pre-open signal (known overnight).
Output: debug/tsla_vix1d_extension.md
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

CACHE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache")
OUT   = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug/tsla_vix1d_extension.md")

def load_ib(path):
    df = pd.read_parquet(path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    df.index = df.index.tz_convert('America/New_York') if df.index.tz else df.index.tz_localize('UTC').tz_convert('America/New_York')
    return df

print("Loading data...")
tsla_1m = load_ib(CACHE / "bars/tsla_1_min_ib.parquet")

# VIX 1d: dates are tz-naive date-like values, treat as date-only
vix_1d_raw = pd.read_parquet(CACHE / "bars/vix_1_day_ib.parquet")
vix_1d_raw['date'] = pd.to_datetime(vix_1d_raw['date'])
vix_1d_raw['date_only'] = vix_1d_raw['date'].dt.date
vix_1d_raw = vix_1d_raw.sort_values('date').set_index('date_only')
print(f"TSLA 1m: {tsla_1m.shape}")
print(f"VIX 1d: {len(vix_1d_raw)} days, {vix_1d_raw.index.min()} → {vix_1d_raw.index.max()}")

# ─── TSLA daily outcomes grid ─────────────────────────────────────────────────
print("Building TSLA daily outcomes...")
tsla_mh = tsla_1m.between_time('09:30', '15:59')
days = sorted(tsla_mh.index.normalize().unique())

rows = []
for day in days:
    d = tsla_mh[tsla_mh.index.date == day.date()]
    if d.empty:
        continue
    b930 = d.between_time('09:30', '09:30')
    b935 = d.between_time('09:35', '09:35')
    if b930.empty:
        continue
    entry     = b930.iloc[0]['open']
    close_5m  = b935.iloc[0]['close'] if not b935.empty else np.nan
    eod_close = d.iloc[-1]['close']
    day_chg   = eod_close - entry
    rows.append({
        'day': day.date(),
        'entry': entry, 'close_5m': close_5m,
        'eod_close': eod_close, 'day_chg': day_chg,
        'day_high': d['high'].max(), 'day_low': d['low'].min(),
    })

outcomes = pd.DataFrame(rows).set_index('day')
outcomes['day_above'] = outcomes['day_chg'] > 0
outcomes['hold_5m']   = outcomes['close_5m'] > outcomes['entry']
outcomes['worst']     = outcomes['day_chg'] < -5
outcomes['bad']       = outcomes['day_chg'] < -2
outcomes['bull']      = outcomes['day_chg'] > 5
print(f"Outcomes: {len(outcomes)} days")

# ─── VIX 1d features ─────────────────────────────────────────────────────────
# Use prev-day VIX close as the pre-open signal (available overnight)
vix_dates = sorted(vix_1d_raw.index)

vix_rows = []
for day in outcomes.index:
    prev = [d for d in vix_dates if d < day]
    same = [d for d in vix_dates if d == day]

    prev_close = float(vix_1d_raw.loc[prev[-1], 'close']) if prev else np.nan
    same_open  = float(vix_1d_raw.loc[same[0],  'open'])  if same else np.nan
    same_close = float(vix_1d_raw.loc[same[0],  'close']) if same else np.nan

    vix_rows.append({
        'day': day,
        'vix_prev_close': prev_close,
        'vix_same_open':  same_open,
        'vix_same_close': same_close,
    })

vix_df = pd.DataFrame(vix_rows).set_index('day')
vix_df['vix_change_prev']  = vix_df['vix_same_open'] - vix_df['vix_prev_close']
vix_df['vix_regime_prev']  = pd.cut(vix_df['vix_prev_close'], bins=[0,18,25,999], labels=['calm','moderate','fear'])
vix_df['vix_regime_open']  = pd.cut(vix_df['vix_same_open'],  bins=[0,18,25,999], labels=['calm','moderate','fear'])

df = outcomes.join(vix_df)
n_vix = df['vix_prev_close'].notna().sum()
print(f"Merged: {len(df)} days, {n_vix} with VIX 1d data")

# ─── Helpers ──────────────────────────────────────────────────────────────────

HDR = "| label | n | day_above% | avg_day_chg | worst% | bad% | bull% | hold_5m% |"
SEP = "|---|---|---|---|---|---|---|---|"

def fmt_row(label, sub):
    if len(sub) == 0:
        return None
    n = len(sub)
    thin = " (thin)" if n < 20 else ""
    return (f"| {label}{thin} | {n} | {sub['day_above'].mean()*100:.1f} | "
            f"{sub['day_chg'].mean():.2f} | {sub['worst'].mean()*100:.1f} | "
            f"{sub['bad'].mean()*100:.1f} | {sub['bull'].mean()*100:.1f} | "
            f"{sub['hold_5m'].mean()*100:.1f} |")

# ─── Analysis ────────────────────────────────────────────────────────────────

lines = []
lines.append("# TSLA VIX 1d Extension — Full Dataset Regime Conditioning")
lines.append(f"*Generated: 2026-03-18 | TSLA: {len(df)} days | VIX 1d overlap: {n_vix} days*")
lines.append("")
lines.append("Extends VIX conditioning from the 85-day VIX 1h window to the full ~250-day dataset.")
lines.append("Uses **prev-day VIX close** as the pre-open signal (known overnight, before 9:30).")
lines.append("")

# ── V1: Regime by prev-day VIX close ─────────────────────────────────────────
lines.append("## V1 — VIX Regime by Prev-Day Close (pre-open signal)")
lines.append("")
vix_valid = df.dropna(subset=['vix_prev_close'])
lines.append(HDR); lines.append(SEP)
lines.append(fmt_row("All VIX days (baseline)", vix_valid))
for regime in ['calm', 'moderate', 'fear']:
    sub = vix_valid[vix_valid['vix_regime_prev'] == regime]
    r = fmt_row(f"VIX prev {regime}", sub)
    if r: lines.append(r)
lines.append("")

# ── V2: Regime by same-day open ───────────────────────────────────────────────
lines.append("## V2 — VIX Regime by Same-Day Open (at-open)")
lines.append("")
vix_valid2 = df.dropna(subset=['vix_same_open'])
lines.append(HDR); lines.append(SEP)
lines.append(fmt_row("All VIX days (baseline)", vix_valid2))
for regime in ['calm', 'moderate', 'fear']:
    sub = vix_valid2[vix_valid2['vix_regime_open'] == regime]
    r = fmt_row(f"VIX open {regime}", sub)
    if r: lines.append(r)
lines.append("")

# ── V3: VIX prev-day regime × 5m rule ────────────────────────────────────────
lines.append("## V3 — VIX Prev-Day Regime × 5m Rule")
lines.append("")
lines.append("| label | n | day_above% | avg_day_chg | worst% | bull% | hold_5m% |")
lines.append("|---|---|---|---|---|---|---|")
for regime in ['calm', 'moderate', 'fear']:
    for hold in [True, False]:
        sub  = vix_valid[(vix_valid['vix_regime_prev'] == regime) & (vix_valid['hold_5m'] == hold)]
        if len(sub) == 0: continue
        n    = len(sub)
        thin = " (thin)" if n < 20 else ""
        hs   = "HOLD" if hold else "BAIL"
        lines.append(f"| VIX {regime} × 5m={hs}{thin} | {n} | {sub['day_above'].mean()*100:.1f} | "
                     f"{sub['day_chg'].mean():.2f} | {sub['worst'].mean()*100:.1f} | "
                     f"{sub['bull'].mean()*100:.1f} | {sub['hold_5m'].mean()*100:.0f} |")
lines.append("")

# ── V4: VIX spike detector ────────────────────────────────────────────────────
lines.append("## V4 — VIX Day-Over-Day Change (spike detector)")
lines.append("")
lines.append("| label | n | avg_vix_chg | day_above% | avg_day_chg | worst% |")
lines.append("|---|---|---|---|---|---|")
for label, lo, hi in [("Large spike (>+2)", 2, 999), ("Small spike (0 to +2)", 0, 2),
                      ("Flat (-1 to 0)", -1, 0), ("Drop (<-1)", -999, -1)]:
    sub = vix_valid[(vix_valid['vix_change_prev'] > lo) & (vix_valid['vix_change_prev'] <= hi)]
    if len(sub) == 0: continue
    thin = " (thin)" if len(sub) < 20 else ""
    lines.append(f"| {label}{thin} | {len(sub)} | {sub['vix_change_prev'].mean():.2f} | "
                 f"{sub['day_above'].mean()*100:.1f} | {sub['day_chg'].mean():.2f} | "
                 f"{sub['worst'].mean()*100:.1f} |")
lines.append("")

# ── V5: Worst-day rate by VIX tier ────────────────────────────────────────────
lines.append("## V5 — Worst-Day Rate by VIX Tier")
lines.append("")
lines.append("| tier | n | worst_day% | bad_day% | avg_day_chg |")
lines.append("|---|---|---|---|---|")
for label, lo, hi in [("VIX ≤ 15", 0, 15), ("VIX 15-20", 15, 20),
                      ("VIX 20-25", 20, 25), ("VIX > 25", 25, 999)]:
    sub = vix_valid[(vix_valid['vix_prev_close'] > lo) & (vix_valid['vix_prev_close'] <= hi)]
    if len(sub) == 0: continue
    thin = " (thin)" if len(sub) < 20 else ""
    lines.append(f"| {label}{thin} | {len(sub)} | {sub['worst'].mean()*100:.1f} | "
                 f"{sub['bad'].mean()*100:.1f} | {sub['day_chg'].mean():.2f} |")
lines.append("")

# ── V6: Actionable sizing tiers (HOLD days only) ─────────────────────────────
lines.append("## V6 — HOLD Day Outcomes by VIX Regime (sizing guide)")
lines.append("")
lines.append("| VIX range | regime | n | HOLD win% | HOLD avg P&L | worst% | recommendation |")
lines.append("|---|---|---|---|---|---|---|")
for regime, lo, hi, rec in [
    ("calm",     0,  18, "Reduce (complacency)"),
    ("moderate", 18, 25, "Full size (best regime)"),
    ("fear",     25, 999, "Skip / very small"),
]:
    sub = vix_valid[(vix_valid['vix_prev_close'] > lo) & (vix_valid['vix_prev_close'] <= hi) & vix_valid['hold_5m']]
    if len(sub) == 0: continue
    thin = " (thin)" if len(sub) < 20 else ""
    lines.append(f"| {lo}-{hi} | {regime}{thin} | {len(sub)} | {sub['day_above'].mean()*100:.1f}% | "
                 f"{sub['day_chg'].mean():.2f} | {sub['worst'].mean()*100:.1f}% | {rec} |")
lines.append("")

# ── V7: Comparison summary vs prior VIX 1h results ───────────────────────────
lines.append("## V7 — Summary: Key Findings vs Prior VIX 1h (85 days)")
lines.append("")
vv = vix_valid
calm_h    = vv[(vv['vix_regime_prev']=='calm')     & vv['hold_5m']]
mod_h     = vv[(vv['vix_regime_prev']=='moderate') & vv['hold_5m']]
fear_h    = vv[(vv['vix_regime_prev']=='fear')      & vv['hold_5m']]

lines.append("| Metric | VIX 1h (85d, prior) | VIX 1d (this run) |")
lines.append("|---|---|---|")

def pct_or_na(sub, col):
    return f"{sub[col].mean()*100:.1f}%" if len(sub) > 0 else "N/A"
def avg_or_na(sub, col):
    return f"${sub[col].mean():.2f}" if len(sub) > 0 else "N/A"

calm_day    = vv[vv['vix_regime_prev']=='calm']
mod_day     = vv[vv['vix_regime_prev']=='moderate']
fear_day    = vv[vv['vix_regime_prev']=='fear']

lines.append(f"| Calm (<18) day_above% | 40.4% | {pct_or_na(calm_day,'day_above')} |")
lines.append(f"| Moderate (18-25) day_above% | 69.0% | {pct_or_na(mod_day,'day_above')} |")
lines.append(f"| Fear (>25) day_above% | 22.2% | {pct_or_na(fear_day,'day_above')} |")
lines.append(f"| Moderate × HOLD win% | 81.2% | {pct_or_na(mod_h,'day_above')} |")
lines.append(f"| Moderate × HOLD avg P&L | +$5.75 | {avg_or_na(mod_h,'day_chg')} |")
lines.append(f"| n (VIX overlap) | 85 days | {n_vix} days |")
lines.append("")

OUT.write_text("\n".join(lines))
print(f"\nOutput written to {OUT}")
