"""
TSLA Open Scalper — Regime Detection Validation
Tests whether a market regime classifier can filter out bad DRIFT_DN (and other pattern) days.

Regime signals available at 9:29 (known before trade):
  pm_accel_2m   — 2m premarket acceleration (9:27→9:29)
  pm_position   — close_929 position within full PM range (0=bottom, 1=top)
  pm_slope      — linear slope of PM price action
  pm_r2         — R² of PM linear fit (1=trending, 0=choppy)
  vix_prev      — previous day VIX
  agree_count   — VWAP+EMA agreement with binary direction (0-2)
  pm_green_pct  — % green 1m bars in PM session
  pm_consec_down_bars — consecutive down bars at 9:29
  gap_pct       — opening gap %
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

df = pd.read_parquet('tsla_candle_fingerprints.parquet')
SPLIT_DATE = pd.Timestamp('2025-09-18')

# ─── Helper: compute PnL from bar1 close entry (PUT direction) ──────────────
# pnl_put_Nm uses bar0_open as reference. Adjust for bar1_close entry.
def drift_put_pnl(row, bars=7):
    """PnL for PUT entered at bar1_close, held for (bars-1) more bars."""
    col = f'pnl_put_{bars}m'
    if col not in row.index or pd.isna(row[col]):
        return np.nan
    entry_adj = row['bar0_open'] - row['bar1_close']  # adj from bar0_open to bar1_close
    return row[col] - entry_adj

def drift_call_pnl(row, bars=7):
    """PnL for CALL entered at bar1_close, held for (bars-1) more bars."""
    col = f'pnl_call_{bars}m'
    if col not in row.index or pd.isna(row[col]):
        return np.nan
    entry_adj = row['bar1_close'] - row['bar0_open']  # adj from bar0_open to bar1_close
    return row[col] - entry_adj


# ─── 1. DRIFT_DN Full Analysis ───────────────────────────────────────────────
dn = df[df['opening_pattern'] == 'DRIFT_DN'].copy()
dn['pnl'] = dn.apply(lambda r: drift_put_pnl(r, 7), axis=1)
dn['win'] = dn['pnl'] > 0

print("=" * 60)
print("DRIFT_DN BASE STATS (29 days)")
print("=" * 60)
print(f"N={len(dn)}, Total={dn['pnl'].sum():.2f}, WR={dn['win'].mean():.1%}, "
      f"Avg={dn['pnl'].mean():.3f}")

h1 = dn[dn.index < SPLIT_DATE]
h2 = dn[dn.index >= SPLIT_DATE]
print(f"\nH1: N={len(h1)}, Total={h1['pnl'].sum():.2f}, WR={h1['win'].mean():.1%}")
print(f"H2: N={len(h2)}, Total={h2['pnl'].sum():.2f}, WR={h2['win'].mean():.1%}")


# ─── 2. Feature comparison: winners vs losers ────────────────────────────────
print("\n" + "=" * 60)
print("FEATURE COMPARISON: Winners vs Losers (full period)")
print("=" * 60)
features = ['pm_accel_2m', 'pm_position', 'pm_r2', 'pm_slope',
            'vix_prev', 'agree_count', 'pm_green_pct', 'bar0_range',
            'gap_pct', 'pm_consec_down_bars']
w = dn[dn['win']]
l = dn[~dn['win']]
print(f"{'Feature':<22} {'Winners (avg)':>14} {'Losers (avg)':>14} {'Diff':>10}")
print("-" * 62)
for f in features:
    if f in dn.columns:
        wm = w[f].mean()
        lm = l[f].mean()
        print(f"{f:<22} {wm:>14.3f} {lm:>14.3f} {wm-lm:>10.3f}")


# ─── 3. Regime thresholds — grid search ──────────────────────────────────────
print("\n" + "=" * 60)
print("REGIME FILTER GRID SEARCH (skip if condition NOT met)")
print("=" * 60)

# Single-feature thresholds
candidates = {
    'pm_accel_2m < -0.2': dn['pm_accel_2m'] < -0.2,
    'pm_accel_2m < -0.4': dn['pm_accel_2m'] < -0.4,
    'pm_position < 0.35': dn['pm_position'] < 0.35,
    'pm_position < 0.25': dn['pm_position'] < 0.25,
    'pm_r2 > 0.50':       dn['pm_r2'] > 0.50,
    'pm_r2 > 0.65':       dn['pm_r2'] > 0.65,
    'pm_slope < -0.03':   dn['pm_slope'] < -0.03,
    'pm_slope < -0.05':   dn['pm_slope'] < -0.05,
    'agree_count >= 1':   dn['agree_count'] >= 1,
    'vix_prev < 28':      dn['vix_prev'] < 28,
    'vix_prev < 25':      dn['vix_prev'] < 25,
    'pm_consec_down >= 2': dn['pm_consec_down_bars'] >= 2,
}

print(f"{'Filter (TRADE if true)':<28} {'N':>4} {'Total':>7} {'Avg':>7} {'WR':>6} {'Skip':>5} {'Skip$':>7}")
print("-" * 65)
for name, mask in candidates.items():
    sub = dn[mask]
    skip = dn[~mask]
    if len(sub) == 0:
        continue
    print(f"{name:<28} {len(sub):>4} {sub['pnl'].sum():>7.2f} {sub['pnl'].mean():>7.3f} "
          f"{sub['win'].mean():>6.1%} {len(skip):>5} {skip['pnl'].sum():>7.2f}")


# ─── 4. Combined filters ─────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("COMBINED FILTERS (top combos)")
print("=" * 60)
combos = {
    'accel<-0.2 AND r2>0.50':    (dn['pm_accel_2m'] < -0.2) & (dn['pm_r2'] > 0.50),
    'accel<-0.2 AND pos<0.35':   (dn['pm_accel_2m'] < -0.2) & (dn['pm_position'] < 0.35),
    'r2>0.50 AND pos<0.35':      (dn['pm_r2'] > 0.50) & (dn['pm_position'] < 0.35),
    'slope<-0.03 AND r2>0.50':   (dn['pm_slope'] < -0.03) & (dn['pm_r2'] > 0.50),
    'slope<-0.03 AND pos<0.35':  (dn['pm_slope'] < -0.03) & (dn['pm_position'] < 0.35),
    'accel<-0.2 AND agree>=1':   (dn['pm_accel_2m'] < -0.2) & (dn['agree_count'] >= 1),
    'r2>0.50 AND agree>=1':      (dn['pm_r2'] > 0.50) & (dn['agree_count'] >= 1),
    'pos<0.35 AND agree>=1':     (dn['pm_position'] < 0.35) & (dn['agree_count'] >= 1),
    'slope<-0.03 AND agree>=1':  (dn['pm_slope'] < -0.03) & (dn['agree_count'] >= 1),
}
print(f"{'Filter':<34} {'N':>4} {'Total':>7} {'Avg':>7} {'WR':>6} {'Skip':>5} {'Skip$':>7}")
print("-" * 70)
for name, mask in combos.items():
    sub = dn[mask]
    skip = dn[~mask]
    if len(sub) < 5:
        continue
    print(f"{name:<34} {len(sub):>4} {sub['pnl'].sum():>7.2f} {sub['pnl'].mean():>7.3f} "
          f"{sub['win'].mean():>6.1%} {len(skip):>5} {skip['pnl'].sum():>7.2f}")


# ─── 5. Best filter H1/H2 validation ────────────────────────────────────────
print("\n" + "=" * 60)
print("H1/H2 VALIDATION FOR BEST FILTERS")
print("=" * 60)
best_filters = {
    'pm_r2 > 0.50': dn['pm_r2'] > 0.50,
    'pm_slope < -0.03': dn['pm_slope'] < -0.03,
    'accel<-0.2 AND r2>0.50': (dn['pm_accel_2m'] < -0.2) & (dn['pm_r2'] > 0.50),
    'r2>0.50 AND pos<0.35':   (dn['pm_r2'] > 0.50) & (dn['pm_position'] < 0.35),
    'slope<-0.03 AND pos<0.35': (dn['pm_slope'] < -0.03) & (dn['pm_position'] < 0.35),
}
for name, mask in best_filters.items():
    sub = dn[mask]
    if len(sub) < 4:
        continue
    s_h1 = sub[sub.index < SPLIT_DATE]
    s_h2 = sub[sub.index >= SPLIT_DATE]
    print(f"\n{name}")
    print(f"  Full: N={len(sub)}, Total={sub['pnl'].sum():.2f}, WR={sub['win'].mean():.1%}")
    if len(s_h1) > 0:
        print(f"  H1:   N={len(s_h1)}, Total={s_h1['pnl'].sum():.2f}, WR={s_h1['win'].mean():.1%}")
    if len(s_h2) > 0:
        print(f"  H2:   N={len(s_h2)}, Total={s_h2['pnl'].sum():.2f}, WR={s_h2['win'].mean():.1%}")


# ─── 6. Regime impact on ALL patterns ────────────────────────────────────────
print("\n" + "=" * 60)
print("REGIME IMPACT ON ALL PATTERNS (pm_r2 > 0.50 as 'TREND')")
print("=" * 60)
# Use the single strongest regime signal for cross-pattern test
regime_col = 'pm_r2'
thresh = 0.50

def get_pnl(row):
    pat = row['opening_pattern']
    direction_map = {
        'CRASH': 'put', 'DRIFT_DN': 'put',
        'SURGE': 'call', 'DRIFT_UP': 'call',
        'FAKEDN': 'put', 'FAKEUP': 'call',
        'INVV': 'call', 'VSHAPE': 'call',
    }
    d = direction_map.get(pat, 'call')
    col = f'pnl_{d}_7m'
    return row.get(col, np.nan)

df['system_pnl'] = df.apply(get_pnl, axis=1)
df['trending'] = df[regime_col] > thresh

print(f"\n{'Pattern':<12} {'All N':>6} {'All $':>7} {'Trend N':>8} {'Trend $':>8} {'Chop N':>7} {'Chop $':>7}")
print("-" * 60)
for pat in ['CRASH', 'SURGE', 'DRIFT_UP', 'DRIFT_DN', 'FAKEDN', 'FAKEUP', 'INVV', 'VSHAPE']:
    sub = df[df['opening_pattern'] == pat]
    if len(sub) < 3:
        continue
    trend = sub[sub['trending']]
    chop  = sub[~sub['trending']]
    print(f"{pat:<12} {len(sub):>6} {sub['system_pnl'].sum():>7.2f} "
          f"{len(trend):>8} {trend['system_pnl'].sum():>8.2f} "
          f"{len(chop):>7} {chop['system_pnl'].sum():>7.2f}")


# ─── 7. Proposed 3-state regime with best thresholds ────────────────────────
print("\n" + "=" * 60)
print("3-STATE REGIME SYSTEM SIMULATION")
print("=" * 60)
print("""
TREND:  pm_r2 > 0.65 — strongly directional PM (clear linear trend)
DRIFT:  0.30 < pm_r2 <= 0.65 — moderate direction
CHOP:   pm_r2 <= 0.30 — flat/noisy PM

Rules:
  CRASH/SURGE: trade in all regimes (large-body filter already applied)
  DRIFT_UP/DN: trade in TREND only; skip in DRIFT/CHOP
  Reversal patterns (INVV/VSHAPE/FAKEUP/FAKEDN): trade in all regimes (bar entry is regime-neutral)
""")

def regime(row):
    r2 = row.get('pm_r2', 0.5)
    if r2 > 0.65:   return 'TREND'
    elif r2 > 0.30: return 'DRIFT'
    else:           return 'CHOP'

df['regime'] = df.apply(regime, axis=1)
drift_patterns = ['DRIFT_UP', 'DRIFT_DN']

# Simulate: skip DRIFT in DRIFT/CHOP regime
df['sim_pnl'] = df['system_pnl']
skip_mask = df['opening_pattern'].isin(drift_patterns) & (df['regime'] != 'TREND')
df.loc[skip_mask, 'sim_pnl'] = 0

orig = df['system_pnl'].sum()
sim  = df['sim_pnl'].sum()
skipped_pnl = df.loc[skip_mask, 'system_pnl'].sum()

print(f"Original system P&L (all days):  ${orig:.2f}")
print(f"With DRIFT regime filter:         ${sim:.2f}  (delta: {sim-orig:+.2f})")
print(f"  Skipped trades P&L would have been: ${skipped_pnl:.2f}")
print(f"  Days skipped: {skip_mask.sum()}")

# Per-pattern breakdown
print(f"\n{'Pattern':<12} {'N traded':>9} {'PnL traded':>11} {'N skipped':>10} {'PnL skipped':>12}")
print("-" * 55)
for pat in drift_patterns:
    kept  = df[(df['opening_pattern'] == pat) & (df['regime'] == 'TREND')]
    skip  = df[(df['opening_pattern'] == pat) & (df['regime'] != 'TREND')]
    print(f"{pat:<12} {len(kept):>9} {kept['system_pnl'].sum():>11.2f} "
          f"{len(skip):>10} {skip['system_pnl'].sum():>12.2f}")

# H1/H2
sim_h1 = df[df.index < SPLIT_DATE]['sim_pnl'].sum()
sim_h2 = df[df.index >= SPLIT_DATE]['sim_pnl'].sum()
orig_h1 = df[df.index < SPLIT_DATE]['system_pnl'].sum()
orig_h2 = df[df.index >= SPLIT_DATE]['system_pnl'].sum()
print(f"\nH1: orig=${orig_h1:.2f} → sim=${sim_h1:.2f}  ({sim_h1-orig_h1:+.2f})")
print(f"H2: orig=${orig_h2:.2f} → sim=${sim_h2:.2f}  ({sim_h2-orig_h2:+.2f})")

print("\nDone.")
