#!/usr/bin/env python3
"""Deep dive on bar1_red, gap, and combined overrides."""
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

BASE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache")

def load_15sec(sym):
    df = pd.read_parquet(BASE / f"bars_highres/15sec/{sym}_15_secs_ib.parquet")
    df['date'] = pd.to_datetime(df['date'], utc=True).dt.tz_convert('US/Eastern')
    df = df.set_index('date')
    return df

def load_1m(sym):
    df = pd.read_parquet(BASE / f"bars/{sym}_1_min_ib.parquet")
    df['date'] = pd.to_datetime(df['date'], utc=True).dt.tz_convert('US/Eastern')
    df = df.set_index('date')
    return df

def load_vix():
    df = pd.read_parquet(BASE / "bars/vix_1_day_ib.parquet")
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    return df

tsla_15s = load_15sec('tsla')
spy_15s = load_15sec('spy')
qqq_15s = load_15sec('qqq')
tsla_1m = load_1m('tsla')
vix_daily = load_vix()
tsla_1m['hm'] = tsla_1m.index.hour * 100 + tsla_1m.index.minute

def resample_to_1m(df_15s):
    r = df_15s.resample('1min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
    return r

tsla_1m_from15s = resample_to_1m(tsla_15s)
spy_1m_from15s = resample_to_1m(spy_15s)
qqq_1m_from15s = resample_to_1m(qqq_15s)

vix_dates = sorted(vix_daily.index)
vix_prev_close_map = {}
for i in range(1, len(vix_dates)):
    d = vix_dates[i]
    d_key = d.date() if hasattr(d, 'date') else d
    vix_prev_close_map[d_key] = vix_daily.loc[vix_dates[i-1], 'close']

rth_bars = tsla_1m[(tsla_1m['hm'] >= 930) & (tsla_1m['hm'] <= 1559)]
daily_last_close = rth_bars.groupby(rth_bars.index.date)['close'].last()

all_dates = sorted(set(tsla_15s.index.date))
results = []

for day in all_dates:
    day_tsla_1m = tsla_1m_from15s[tsla_1m_from15s.index.date == day]
    day_spy_1m = spy_1m_from15s[spy_1m_from15s.index.date == day]
    day_qqq_1m = qqq_1m_from15s[qqq_1m_from15s.index.date == day]

    def get_bar(df, h, m):
        mask = (df.index.hour == h) & (df.index.minute == m)
        bars = df[mask]
        return bars.iloc[0] if len(bars) > 0 else None

    bar_920 = get_bar(day_tsla_1m, 9, 20)
    bar_927 = get_bar(day_tsla_1m, 9, 27)
    bar_929 = get_bar(day_tsla_1m, 9, 29)

    if bar_929 is None:
        continue

    pm_bars = day_tsla_1m[(day_tsla_1m.index.hour >= 4) &
                          ((day_tsla_1m.index.hour < 9) |
                           ((day_tsla_1m.index.hour == 9) & (day_tsla_1m.index.minute <= 29)))]
    if len(pm_bars) == 0:
        continue

    pm_high = pm_bars['high'].max()
    pm_low = pm_bars['low'].min()
    close_929 = bar_929['close']
    pm_range = pm_high - pm_low
    pm_position = (close_929 - pm_low) / pm_range if pm_range > 0 else 0.5
    pm_accel = close_929 - bar_927['open'] if bar_927 is not None else np.nan
    open_920 = bar_920['open'] if bar_920 is not None else np.nan
    pm_late_trend = close_929 - open_920 if not np.isnan(open_920) else np.nan

    spy_920_bar = get_bar(day_spy_1m, 9, 20)
    spy_929_bar = get_bar(day_spy_1m, 9, 29)
    qqq_920_bar = get_bar(day_qqq_1m, 9, 20)
    qqq_929_bar = get_bar(day_qqq_1m, 9, 29)

    spy_920 = spy_920_bar['close'] if spy_920_bar is not None else np.nan
    spy_929 = spy_929_bar['close'] if spy_929_bar is not None else np.nan
    qqq_920 = qqq_920_bar['close'] if qqq_920_bar is not None else np.nan
    qqq_929 = qqq_929_bar['close'] if qqq_929_bar is not None else np.nan

    tsla_up = not np.isnan(pm_late_trend) and pm_late_trend > 0
    spy_up = not np.isnan(spy_929) and not np.isnan(spy_920) and spy_929 > spy_920
    qqq_up = not np.isnan(qqq_929) and not np.isnan(qqq_920) and qqq_929 > qqq_920

    prev_dates = [d for d in daily_last_close.index if d < day]
    prev_day_close = daily_last_close[prev_dates[-1]] if len(prev_dates) > 0 else np.nan
    vix_pc = vix_prev_close_map.get(day, np.nan)
    est_gap = close_929 - prev_day_close if not np.isnan(prev_day_close) else 0

    day_tsla = tsla_15s[tsla_15s.index.date == day]
    p9_mask = (day_tsla.index.hour == 9) & (day_tsla.index.minute == 29)
    p9_bars = day_tsla[p9_mask]
    p9_30s_down = False
    if len(p9_bars) >= 4:
        p9_30s_down = p9_bars.iloc[3]['close'] < p9_bars.iloc[1]['close']
    else:
        p9_30s_down = bar_929['close'] < bar_929['open']

    pm_vol_bars = day_tsla_1m[(day_tsla_1m.index.hour == 9) &
                              (day_tsla_1m.index.minute >= 25) &
                              (day_tsla_1m.index.minute <= 29)]
    pm_vol_5m = pm_vol_bars['volume'].sum() if len(pm_vol_bars) > 0 else 0

    confidence = 0
    checks = [False]*5
    if pm_position > 0.219: confidence += 1; checks[0] = True
    if not np.isnan(pm_accel) and pm_accel > 0: confidence += 1; checks[1] = True
    if not np.isnan(vix_pc) and 18 <= vix_pc <= 25: confidence += 1; checks[2] = True
    if tsla_up and spy_up and qqq_up: confidence += 1; checks[3] = True
    gap_danger_flat = est_gap < -2 and not np.isnan(pm_late_trend) and abs(pm_late_trend) < 0.48
    if not gap_danger_flat: confidence += 1; checks[4] = True

    hard_kill = False
    kill_reason = 'none'
    if not np.isnan(vix_pc) and vix_pc <= 15: hard_kill = True; kill_reason = 'VIX'
    if pm_position < 0.219 and p9_30s_down: hard_kill = True; kill_reason = 'P9'
    if gap_danger_flat: hard_kill = True; kill_reason = 'GAP'
    if not np.isnan(pm_accel) and pm_accel < -1.50: hard_kill = True; kill_reason = 'ACCEL'
    if pm_vol_5m < 3000 and pm_vol_5m > 0 and confidence < 4: hard_kill = True; kill_reason = 'LOW_VOL'

    is_put_day = confidence <= 2 or hard_kill

    def get_1m_bar_rth(h, m):
        mask = (tsla_1m.index.date == day) & (tsla_1m.index.hour == h) & (tsla_1m.index.minute == m)
        bars = tsla_1m[mask]
        if len(bars) > 0: return bars.iloc[0]
        return get_bar(day_tsla_1m, h, m)

    b930 = get_1m_bar_rth(9, 30)
    b931 = get_1m_bar_rth(9, 31)
    b932 = get_1m_bar_rth(9, 32)
    b934 = get_1m_bar_rth(9, 34)
    if b930 is None: continue

    open_930 = b930['open']
    bar1_red = b930['close'] < b930['open']
    pnl_1m = open_930 - b931['close'] if b931 is not None else np.nan
    pnl_2m = open_930 - b932['close'] if b932 is not None else np.nan
    pnl_5m = open_930 - b934['close'] if b934 is not None else np.nan

    results.append({
        'date': day, 'confidence': confidence, 'is_put_day': is_put_day,
        'hard_kill': hard_kill, 'kill_reason': kill_reason,
        'pm_accel': pm_accel, 'pm_late_trend': pm_late_trend, 'pm_position': pm_position,
        'vix_pc': vix_pc, 'est_gap': est_gap, 'bar1_red': bar1_red,
        'pnl_1m': pnl_1m, 'pnl_2m': pnl_2m, 'pnl_5m': pnl_5m,
        'tsla_up': tsla_up, 'spy_up': spy_up, 'qqq_up': qqq_up,
        'check1': checks[0], 'check2': checks[1], 'check3': checks[2],
        'check4': checks[3], 'check5': checks[4], 'pm_vol_5m': pm_vol_5m,
    })

df = pd.DataFrame(results)
call_days = df[~df['is_put_day']].copy()
put_days = df[df['is_put_day']].copy()

baseline = 0
for _, row in df.iterrows():
    if row['is_put_day']:
        baseline += row['pnl_2m']
    else:
        baseline += -row['pnl_2m']

print("=== BAR1 RED DEEP DIVE (CALL days only) ===")
print()
call_red = call_days[call_days['bar1_red']]
call_green = call_days[~call_days['bar1_red']]
print(f"CALL days with bar1 RED:   {len(call_red)} ({len(call_red)/len(call_days)*100:.0f}%)")
print(f"CALL days with bar1 GREEN: {len(call_green)} ({len(call_green)/len(call_days)*100:.0f}%)")
print()
print(f"Bar1 RED: pnl_2m mean={call_red['pnl_2m'].mean():.2f}")
print(f"  Win rate (CALL wins): {(call_red['pnl_2m'] < 0).mean()*100:.1f}%")
print(f"  Total CALL PnL: ${-call_red['pnl_2m'].sum():.2f}")
print(f"  If played as PUT: ${call_red['pnl_2m'].sum():.2f}")
print()
print(f"Bar1 GREEN: pnl_2m mean={call_green['pnl_2m'].mean():.2f}")
print(f"  Win rate (CALL wins): {(call_green['pnl_2m'] < 0).mean()*100:.1f}%")
print(f"  Total CALL PnL: ${-call_green['pnl_2m'].sum():.2f}")
print()

print("--- Bar1 RED CALL days detail (sorted by 2m loss) ---")
cols = ['date','confidence','pm_accel','pm_late_trend','pm_position','est_gap','pnl_1m','pnl_2m']
print(call_red.sort_values('pnl_2m', ascending=False)[cols].to_string(index=False))

print()
print("=== CAVEAT: bar1_red is POST-OPEN (available at 9:31) ===")
print("It's reactive, not predictive. Two options:")
print("  A) Use it to EXIT CALL at 9:31 (no flip to PUT)")
print("  B) Use it to FLIP to PUT at 9:31 (1 min PUT hold)")
print()

# A) Exit CALL early on bar1 red
total_exit_early = 0
for _, row in call_days.iterrows():
    if row['bar1_red']:
        total_exit_early += -row['pnl_1m']  # exit at 9:31
    else:
        total_exit_early += -row['pnl_2m']  # hold to 9:32
print(f"A) CALL PnL with early exit on bar1 red: ${total_exit_early:.2f}")
print(f"   CALL PnL holding all to 9:32:         ${-call_days['pnl_2m'].sum():.2f}")
print(f"   Delta: ${total_exit_early - (-call_days['pnl_2m'].sum()):+.2f}")

print()
# B) Flip to PUT at 9:31 (enter short at 9:31 close, exit 9:32 close)
# PUT pnl for that 1 min = close_931 - close_932 = pnl_2m - pnl_1m
total_flip_reactive = 0
n_flip = 0
for _, row in call_days.iterrows():
    if row['bar1_red'] and not np.isnan(row['pnl_1m']) and not np.isnan(row['pnl_2m']):
        # Lost the first minute as CALL: -pnl_1m
        call_loss_1m = -row['pnl_1m']
        # Then 1 min as PUT: pnl_2m - pnl_1m
        put_gain_1m = row['pnl_2m'] - row['pnl_1m']
        total_flip_reactive += call_loss_1m + put_gain_1m
        n_flip += 1
    elif row['bar1_red']:
        total_flip_reactive += -row['pnl_2m']  # fallback
    else:
        total_flip_reactive += -row['pnl_2m']
print(f"B) CALL PnL with reactive flip on bar1 red: ${total_flip_reactive:.2f}")
print(f"   Flipped: {n_flip} days")

print()
print("=== OVERFITTING CHECK: bar1_red by quarter ===")
call_days_c = call_days.copy()
call_days_c['quarter'] = pd.to_datetime(call_days_c['date']).dt.to_period('Q')
for q, grp in call_days_c.groupby('quarter'):
    red = grp[grp['bar1_red']]
    green = grp[~grp['bar1_red']]
    red_put_wr = f"{(red['pnl_2m'] > 0).mean()*100:.0f}%" if len(red) > 0 else "N/A"
    green_call_wr = f"{(green['pnl_2m'] < 0).mean()*100:.0f}%" if len(green) > 0 else "N/A"
    red_pnl = -red['pnl_2m'].sum() if len(red) > 0 else 0
    green_pnl = -green['pnl_2m'].sum() if len(green) > 0 else 0
    print(f"  {q}: RED n={len(red)} PUT_wr={red_put_wr} CALL_pnl=${red_pnl:.1f} | GREEN n={len(green)} CALL_wr={green_call_wr} CALL_pnl=${green_pnl:.1f}")

print()
print("=== GAP DEEP DIVE (CALL days only) ===")
for gap_t in [-3, -5, -8, -10]:
    gap_sub = call_days[call_days['est_gap'] < gap_t]
    if len(gap_sub) > 0:
        put_total = gap_sub['pnl_2m'].sum()
        put_wr = (gap_sub['pnl_2m'] > 0).mean()*100
        print(f"gap < {gap_t}: n={len(gap_sub)}, as PUT total=${put_total:.2f}, PUT wr={put_wr:.0f}%")

print()
print("=== DEFINITIVE PREDICTIVE OVERRIDE TESTS ===")
print("(All remove accel kill, then add one override)")
print()

def test_system(name, call_override_fn=None, put_rescue_fn=None):
    total = 0
    n_call = 0
    n_put = 0
    for _, row in df.iterrows():
        hk = row['hard_kill']
        kr = row['kill_reason']
        conf = row['confidence']
        if kr == 'ACCEL':
            hk = False
        is_put_base = conf <= 2 or hk
        is_put_final = is_put_base

        if call_override_fn and not is_put_base and call_override_fn(row):
            is_put_final = True
        if put_rescue_fn and is_put_base and put_rescue_fn(row):
            is_put_final = False

        if is_put_final:
            total += row['pnl_2m']
            n_put += 1
        else:
            total += -row['pnl_2m']
            n_call += 1
    delta = total - baseline
    print(f"  {name}: CALL={n_call} PUT={n_put} Total=${total:.2f} (delta=${delta:+.2f})")
    return total

print("--- Baseline variants ---")
test_system("current (with accel kill)", None, None)  # This will differ since we remove accel
# Actually for the "current" we need to keep accel kill
total_current = 0
for _, row in df.iterrows():
    if row['is_put_day']:
        total_current += row['pnl_2m']
    else:
        total_current += -row['pnl_2m']
print(f"  ACTUAL CURRENT: Total=${total_current:.2f}")

test_system("no accel kill (baseline for tests)")

print()
print("--- Single predictive overrides (CALL->PUT) ---")
test_system("gap < -5", lambda r: r['est_gap'] < -5)
test_system("gap < -8", lambda r: r['est_gap'] < -8)
test_system("gap < -10", lambda r: r['est_gap'] < -10)
test_system("gap < -5 AND accel < 0", lambda r: r['est_gap'] < -5 and not np.isnan(r['pm_accel']) and r['pm_accel'] < 0)
test_system("accel < 0", lambda r: not np.isnan(r['pm_accel']) and r['pm_accel'] < 0)
test_system("accel < -0.5", lambda r: not np.isnan(r['pm_accel']) and r['pm_accel'] < -0.5)

print()
print("--- PUT->CALL rescue overrides ---")
test_system("rescue: accel>1 pos>0.7", None, lambda r: r['pm_accel'] > 1.0 and r['pm_position'] > 0.7)
test_system("rescue: accel>0.5 pos>0.8", None, lambda r: not np.isnan(r['pm_accel']) and r['pm_accel'] > 0.5 and r['pm_position'] > 0.8)
test_system("rescue: VIX kill + accel>0 + conf>=3",
            None, lambda r: r['kill_reason'] == 'VIX' and not np.isnan(r['pm_accel']) and r['pm_accel'] > 0 and r['confidence'] >= 3)

print()
print("--- Combined overrides ---")
test_system("gap<-5 + rescue(accel>1,pos>0.7)",
            lambda r: r['est_gap'] < -5,
            lambda r: r['pm_accel'] > 1.0 and r['pm_position'] > 0.7)
test_system("gap<-8 + rescue(accel>1,pos>0.7)",
            lambda r: r['est_gap'] < -8,
            lambda r: r['pm_accel'] > 1.0 and r['pm_position'] > 0.7)
test_system("gap<-5 + rescue(VIX+accel>0+conf3)",
            lambda r: r['est_gap'] < -5,
            lambda r: r['kill_reason'] == 'VIX' and not np.isnan(r['pm_accel']) and r['pm_accel'] > 0 and r['confidence'] >= 3)

print()
print("=== RESCUE DETAIL: VIX kill + accel>0 + conf>=3 ===")
rescued = put_days[(put_days['kill_reason'] == 'VIX') &
                   (put_days['pm_accel'] > 0) &
                   (put_days['confidence'] >= 3)]
for _, r in rescued.iterrows():
    print(f"  {r['date']} conf={r['confidence']} accel={r['pm_accel']:.2f} vix={r['vix_pc']:.1f} pnl_2m={r['pnl_2m']:.2f} (as CALL: ${-r['pnl_2m']:.2f})")

print()
print("=== RESCUE DETAIL: accel>1 AND pos>0.7 ===")
rescued2 = put_days[(put_days['pm_accel'] > 1.0) & (put_days['pm_position'] > 0.7)]
for _, r in rescued2.iterrows():
    print(f"  {r['date']} conf={r['confidence']} accel={r['pm_accel']:.2f} pos={r['pm_position']:.3f} vix={r['vix_pc']:.1f} pnl_2m={r['pnl_2m']:.2f} kill={r['kill_reason']}")

print()
print("=== FULL GRID SEARCH: best single accel threshold (no accel kill base) ===")
best = (None, -9999)
for t in np.arange(-3.0, 1.0, 0.05):
    total = 0
    for _, row in df.iterrows():
        hk = row['hard_kill']
        kr = row['kill_reason']
        conf = row['confidence']
        if kr == 'ACCEL':
            hk = False
        is_put = conf <= 2 or hk
        # Override: accel < t flips CALL->PUT
        if not is_put and not np.isnan(row['pm_accel']) and row['pm_accel'] < t:
            is_put = True
        if is_put:
            total += row['pnl_2m']
        else:
            total += -row['pnl_2m']
    if total > best[1]:
        best = (t, total)
print(f"Best single accel threshold: {best[0]:.2f} -> Total=${best[1]:.2f} (delta vs current=${best[1]-total_current:+.2f})")

print()
print("=== WHAT 3/20/26 WOULD HAVE LOOKED LIKE ===")
day_320 = df[df['date'] == pd.Timestamp('2026-03-20').date()]
if len(day_320) > 0:
    r = day_320.iloc[0]
    print(f"  conf={r['confidence']} tier={'NO-GO' if r['hard_kill'] else ('HIGH' if r['confidence']>=5 else 'MED' if r['confidence']>=3 else 'LOW' if r['confidence']>=2 else 'NO-GO')}")
    print(f"  is_put={r['is_put_day']} kill={r['kill_reason']}")
    print(f"  pm_accel={r['pm_accel']:.2f} pm_trend={r['pm_late_trend']:.2f} pm_pos={r['pm_position']:.3f}")
    print(f"  vix={r['vix_pc']:.1f} gap={r['est_gap']:.1f}")
    print(f"  bar1_red={r['bar1_red']} pnl_1m={r['pnl_1m']:.2f} pnl_2m={r['pnl_2m']:.2f} pnl_5m={r['pnl_5m']:.2f}")
    print(f"  checks: {r['check1']} {r['check2']} {r['check3']} {r['check4']} {r['check5']}")
else:
    print("  3/20/26 not found in data")
