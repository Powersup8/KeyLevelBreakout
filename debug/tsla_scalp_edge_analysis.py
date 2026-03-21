#!/usr/bin/env python3
"""
TSLA Open Scalper — Edge Case Analysis
Replicates the Pine Script confidence scoring from 15sec data,
then analyzes misclassified days.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

BASE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache")

# ─── Load data ───────────────────────────────────────────────
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

print("Loading data...")
tsla_15s = load_15sec('tsla')
spy_15s = load_15sec('spy')
tsla_1m = load_1m('tsla')
vix_daily = load_vix()

# Build VIX prev close lookup (keyed by date)
vix_daily = vix_daily.sort_index()
vix_prev = vix_daily['close'].shift(1)  # previous day's close
vix_lookup = {}
for dt, val in vix_prev.items():
    vix_lookup[dt.date() if hasattr(dt, 'date') else dt] = val
# Also need current day -> prev close. VIX dates are trading dates.
# Map: for a given trading date, what was VIX close the prior trading day?
vix_dates = sorted(vix_daily.index)
vix_prev_close_map = {}
for i in range(1, len(vix_dates)):
    d = vix_dates[i]
    d_key = d.date() if hasattr(d, 'date') else d
    vix_prev_close_map[d_key] = vix_daily.loc[vix_dates[i-1], 'close']

# ─── Helper: resample 15sec to 1min bars ─────────────────────
def resample_to_1m(df_15s):
    """Resample 15-second bars to 1-minute OHLCV."""
    r = df_15s.resample('1min').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    return r

tsla_1m_from15s = resample_to_1m(tsla_15s)
spy_1m_from15s = resample_to_1m(spy_15s)

# ─── Get trading days from the 15sec data ────────────────────
tsla_15s_days = tsla_15s.index.normalize().unique()
# Get unique dates
all_dates = sorted(set(tsla_15s.index.date))
print(f"Total dates in 15sec data: {len(all_dates)}")

# ─── Build prev_day_close from 1m RTH data ───────────────────
# For each day, prev_day_close = last RTH close of the previous trading day
tsla_1m['hm'] = tsla_1m.index.hour * 100 + tsla_1m.index.minute
rth_bars = tsla_1m[(tsla_1m['hm'] >= 930) & (tsla_1m['hm'] <= 1559)]
daily_last_close = rth_bars.groupby(rth_bars.index.date)['close'].last()

# ─── Compute daily signals ───────────────────────────────────
results = []

for day in all_dates:
    day_str = str(day)

    # Get TSLA 15sec bars for this day
    day_tsla = tsla_15s[tsla_15s.index.date == day]
    day_spy = spy_15s[spy_15s.index.date == day]

    if len(day_tsla) == 0:
        continue

    # Get 1m bars from 15sec resample
    day_tsla_1m = tsla_1m_from15s[tsla_1m_from15s.index.date == day]
    day_spy_1m = spy_1m_from15s[spy_1m_from15s.index.date == day]

    # ── Premarket tracking ──
    pm_bars = day_tsla_1m[(day_tsla_1m.index.hour >= 4) &
                          ((day_tsla_1m.index.hour < 9) |
                           ((day_tsla_1m.index.hour == 9) & (day_tsla_1m.index.minute <= 29)))]

    if len(pm_bars) == 0:
        continue

    pm_high = pm_bars['high'].max()
    pm_low = pm_bars['low'].min()

    # Get specific bar values
    def get_bar(df_1m, h, m):
        mask = (df_1m.index.hour == h) & (df_1m.index.minute == m)
        bars = df_1m[mask]
        if len(bars) > 0:
            return bars.iloc[0]
        return None

    bar_920_tsla = get_bar(day_tsla_1m, 9, 20)
    bar_925 = get_bar(day_tsla_1m, 9, 25)
    bar_927 = get_bar(day_tsla_1m, 9, 27)
    bar_929 = get_bar(day_tsla_1m, 9, 29)
    bar_930 = get_bar(day_tsla_1m, 9, 30)
    bar_931 = get_bar(day_tsla_1m, 9, 31)
    bar_932 = get_bar(day_tsla_1m, 9, 32)
    bar_934 = get_bar(day_tsla_1m, 9, 34)

    bar_920_spy = get_bar(day_spy_1m, 9, 20)
    bar_929_spy = get_bar(day_spy_1m, 9, 29)

    if bar_929 is None or bar_930 is None:
        continue

    # PM position
    close_929 = bar_929['close']
    pm_range = pm_high - pm_low
    pm_position = (close_929 - pm_low) / pm_range if pm_range > 0 else 0.5

    # PM accel (2m: 9:27 open -> 9:29 close)
    pm_accel = close_929 - bar_927['open'] if bar_927 is not None else np.nan

    # PM late trend (9:20 open -> 9:29 close)
    open_920_tsla = bar_920_tsla['open'] if bar_920_tsla is not None else np.nan
    pm_late_trend = close_929 - open_920_tsla if not np.isnan(open_920_tsla) else np.nan

    # SPY 9:20->9:29
    spy_920 = bar_920_spy['close'] if bar_920_spy is not None else np.nan
    spy_929 = bar_929_spy['close'] if bar_929_spy is not None else np.nan

    # PM volume 9:25-9:29
    pm_vol_bars = day_tsla_1m[(day_tsla_1m.index.hour == 9) &
                              (day_tsla_1m.index.minute >= 25) &
                              (day_tsla_1m.index.minute <= 29)]
    pm_vol_5m = pm_vol_bars['volume'].sum() if len(pm_vol_bars) > 0 else 0

    # Prev day close
    prev_dates = [d for d in daily_last_close.index if d < day]
    prev_day_close = daily_last_close[prev_dates[-1]] if len(prev_dates) > 0 else np.nan

    # VIX prev close
    vix_pc = vix_prev_close_map.get(day, np.nan)

    # Gap
    est_gap = close_929 - prev_day_close if not np.isnan(prev_day_close) else 0

    # P9 hard kill: last 30s of 9:29 bar direction (use 15sec sub-bars)
    # 9:29:00 to 9:29:45 → 4 bars
    p9_mask = (day_tsla.index.hour == 9) & (day_tsla.index.minute == 29)
    p9_bars = day_tsla[p9_mask]
    p9_30s_down = False
    if len(p9_bars) >= 4:
        c_2945 = p9_bars.iloc[3]['close']
        c_2915 = p9_bars.iloc[1]['close']
        p9_30s_down = c_2945 < c_2915
    else:
        p9_30s_down = bar_929['close'] < bar_929['open']

    # ── Confidence scoring ──
    confidence = 0
    checks = [False] * 5

    # Check 1: PM Position > 0.219
    if pm_position > 0.219:
        confidence += 1
        checks[0] = True

    # Check 2: PM accel > 0
    if not np.isnan(pm_accel) and pm_accel > 0:
        confidence += 1
        checks[1] = True

    # Check 3: VIX sweet spot 18-25
    if not np.isnan(vix_pc) and 18 <= vix_pc <= 25:
        confidence += 1
        checks[2] = True

    # Check 4: Triple alignment (TSLA + SPY both up from 9:20)
    tsla_up = not np.isnan(pm_late_trend) and pm_late_trend > 0
    spy_up = not np.isnan(spy_929) and not np.isnan(spy_920) and spy_929 > spy_920
    # Note: Pine code checks QQQ too, but task says "TSLA+SPY both up" since QQQ not always avail
    # Actually Pine checks all 3. Let me check QQQ too for accuracy.
    # For simplicity and since the task says QQQ not always available, use TSLA+SPY.
    # But Pine code does: if tsla_up and spy_up and qqq_up → +1
    # Let me load QQQ 15sec too
    # Actually the note says "QQQ not always available" — let me check what happens
    # Pine: qqq_920 := qqq_close at 9:20 bar, qqq_929 := qqq_close at 9:29 bar
    # qqq_close = request.security("QQQ", "1", close) — this uses QQQ 1m close
    # For now, load QQQ
    # I'll handle this outside the loop - for now set qqq_up=True as placeholder
    qqq_up = True  # will be overwritten below

    if tsla_up and spy_up and qqq_up:
        confidence += 1
        checks[3] = True

    # Check 5: No gap danger
    gap_danger_flat = est_gap < -2 and not np.isnan(pm_late_trend) and abs(pm_late_trend) < 0.48
    if not gap_danger_flat:
        confidence += 1
        checks[4] = True

    # ── Hard kills ──
    hard_kill = False
    kill_reason = "none"

    if not np.isnan(vix_pc) and vix_pc <= 15:
        hard_kill = True
        kill_reason = "VIX"

    if pm_position < 0.219 and p9_30s_down:
        hard_kill = True
        kill_reason = "P9"

    if gap_danger_flat:
        hard_kill = True
        kill_reason = "GAP"

    if not np.isnan(pm_accel) and pm_accel < -1.50:
        hard_kill = True
        kill_reason = "ACCEL"

    if pm_vol_5m < 3000 and pm_vol_5m > 0 and confidence < 4:
        hard_kill = True
        kill_reason = "LOW_VOL"

    # Tier
    if hard_kill:
        tier = "NO-GO"
    elif confidence >= 5:
        tier = "HIGH"
    elif confidence >= 3:
        tier = "MED"
    elif confidence >= 2:
        tier = "LOW"
    else:
        tier = "NO-GO"

    is_put_day = confidence <= 2 or hard_kill

    # ── RTH outcome (use actual 1m data, fallback to 15sec resampled) ──
    def get_1m_bar(h, m):
        """Get 1m bar from actual 1m data first, then 15sec resampled."""
        mask = (tsla_1m.index.date == day) & (tsla_1m.index.hour == h) & (tsla_1m.index.minute == m)
        bars = tsla_1m[mask]
        if len(bars) > 0:
            return bars.iloc[0]
        # Fallback to 15sec resampled
        fb = get_bar(day_tsla_1m, h, m)
        return fb

    bar_930_rth = get_1m_bar(9, 30)
    bar_931_rth = get_1m_bar(9, 31)
    bar_932_rth = get_1m_bar(9, 32)
    bar_934_rth = get_1m_bar(9, 34)

    if bar_930_rth is None:
        continue

    open_930 = bar_930_rth['open']
    bar1_red = bar_930_rth['close'] < bar_930_rth['open']

    # pnl_1m = open_930 - close at 9:31 (positive = short wins)
    pnl_1m = open_930 - bar_931_rth['close'] if bar_931_rth is not None else np.nan

    # pnl_2m = open_930 - close at 9:32
    pnl_2m = open_930 - bar_932_rth['close'] if bar_932_rth is not None else np.nan

    # pnl_5m = open_930 - close at 9:34 (5 bars of RTH)
    pnl_5m = open_930 - bar_934_rth['close'] if bar_934_rth is not None else np.nan

    # 5m bail
    bail_5m = bar_934_rth['close'] < open_930 if bar_934_rth is not None else None

    # Day direction from 1m RTH
    rth_day = tsla_1m[(tsla_1m.index.date == day) & (tsla_1m['hm'] >= 930) & (tsla_1m['hm'] <= 1559)]
    if len(rth_day) > 0:
        day_open = rth_day.iloc[0]['open']
        day_close_val = rth_day.iloc[-1]['close']
        day_direction = "BULL" if day_close_val > day_open else "BEAR"
    else:
        day_direction = "N/A"

    results.append({
        'date': day,
        'open_930': open_930,
        'close_929': close_929,
        'pm_high': pm_high,
        'pm_low': pm_low,
        'pm_position': pm_position,
        'pm_accel': pm_accel,
        'pm_late_trend': pm_late_trend,
        'vix_pc': vix_pc,
        'est_gap': est_gap,
        'prev_day_close': prev_day_close,
        'spy_920': spy_920,
        'spy_929': spy_929,
        'tsla_up': tsla_up,
        'spy_up': spy_up,
        'p9_30s_down': p9_30s_down,
        'pm_vol_5m': pm_vol_5m,
        'check1': checks[0],
        'check2': checks[1],
        'check3': checks[2],
        'check4': checks[3],
        'check5': checks[4],
        'confidence': confidence,
        'tier': tier,
        'hard_kill': hard_kill,
        'kill_reason': kill_reason,
        'is_put_day': is_put_day,
        'bar1_red': bar1_red,
        'pnl_1m': pnl_1m,
        'pnl_2m': pnl_2m,
        'pnl_5m': pnl_5m,
        'bail_5m': bail_5m,
        'day_direction': day_direction,
    })

df = pd.DataFrame(results)
print(f"\nDays analyzed: {len(df)}")

# ── Now fix Check 4 with QQQ data ──
try:
    qqq_15s = load_15sec('qqq')
    qqq_1m = resample_to_1m(qqq_15s)

    for i, row in df.iterrows():
        day = row['date']
        day_qqq = qqq_1m[qqq_1m.index.date == day]
        bar_920_qqq = None
        bar_929_qqq = None
        mask920 = (day_qqq.index.hour == 9) & (day_qqq.index.minute == 20)
        mask929 = (day_qqq.index.hour == 9) & (day_qqq.index.minute == 29)
        if mask920.any():
            bar_920_qqq = day_qqq[mask920].iloc[0]
        if mask929.any():
            bar_929_qqq = day_qqq[mask929].iloc[0]

        qqq_920_val = bar_920_qqq['close'] if bar_920_qqq is not None else np.nan
        qqq_929_val = bar_929_qqq['close'] if bar_929_qqq is not None else np.nan
        qqq_up = not np.isnan(qqq_920_val) and not np.isnan(qqq_929_val) and qqq_929_val > qqq_920_val

        # Recompute check4 properly
        tsla_up = row['tsla_up']
        spy_up = row['spy_up']
        check4 = tsla_up and spy_up and qqq_up

        # Update confidence
        old_check4 = row['check4']
        if check4 != old_check4:
            conf_delta = 1 if check4 and not old_check4 else -1 if not check4 and old_check4 else 0
            new_conf = row['confidence'] + conf_delta
            df.at[i, 'confidence'] = new_conf
            df.at[i, 'check4'] = check4

            # Recompute tier
            hk = row['hard_kill']
            if hk:
                df.at[i, 'tier'] = "NO-GO"
            elif new_conf >= 5:
                df.at[i, 'tier'] = "HIGH"
            elif new_conf >= 3:
                df.at[i, 'tier'] = "MED"
            elif new_conf >= 2:
                df.at[i, 'tier'] = "LOW"
            else:
                df.at[i, 'tier'] = "NO-GO"

            # Recompute is_put_day
            df.at[i, 'is_put_day'] = new_conf <= 2 or hk

        df.at[i, 'qqq_up'] = qqq_up

    print("QQQ data loaded and Check 4 recomputed.")
except Exception as e:
    print(f"QQQ loading failed: {e}, using TSLA+SPY only for check4")
    df['qqq_up'] = True

# ─── Classification correctness ─────────────────────────────
# CALL day: conf>=3 and not hard_kill → correct if pnl_2m < 0 (price went up)
# PUT day: conf<=2 or hard_kill → correct if pnl_2m > 0 (price went down)
call_days = df[~df['is_put_day']].copy()
put_days = df[df['is_put_day']].copy()

call_days['correct'] = call_days['pnl_2m'] < 0  # price went up (CALL wins)
put_days['correct'] = put_days['pnl_2m'] > 0    # price went down (PUT wins)

call_days['misclassified'] = ~call_days['correct']
put_days['misclassified'] = ~put_days['correct']

print(f"\n{'='*60}")
print(f"CALL days: {len(call_days)} | Correct: {call_days['correct'].sum()} ({call_days['correct'].mean()*100:.1f}%) | Misclassified: {call_days['misclassified'].sum()}")
print(f"PUT days:  {len(put_days)} | Correct: {put_days['correct'].sum()} ({put_days['correct'].mean()*100:.1f}%) | Misclassified: {put_days['misclassified'].sum()}")

# CALL PnL: pnl_2m < 0 means long wins, so CALL pnl = -pnl_2m
call_days['call_pnl'] = -call_days['pnl_2m']  # positive = long wins
put_days['put_pnl'] = put_days['pnl_2m']      # positive = short wins

print(f"\nCALL total PnL (2m): ${call_days['call_pnl'].sum():.2f}")
print(f"PUT total PnL (2m):  ${put_days['put_pnl'].sum():.2f}")
print(f"Combined PnL:        ${call_days['call_pnl'].sum() + put_days['put_pnl'].sum():.2f}")

# ─── SECTION 3: Misclassified CALL days ──────────────────────
print(f"\n{'='*60}")
print("MISCLASSIFIED CALL DAYS (conf>=3, should have been PUT)")
print("="*60)
mis_call = call_days[call_days['misclassified']].sort_values('pnl_2m', ascending=False)

cols = ['date','confidence','tier','check1','check2','check3','check4','check5',
        'pm_accel','pm_late_trend','pm_position','vix_pc','est_gap',
        'pnl_2m','call_pnl','bar1_red','day_direction','spy_up','tsla_up','p9_30s_down']
print(mis_call[cols].to_string(index=False))

# Compare distributions
print(f"\n--- PM Accel distribution ---")
print(f"Misclassified CALL: mean={mis_call['pm_accel'].mean():.3f}, median={mis_call['pm_accel'].median():.3f}")
correct_call = call_days[call_days['correct']]
print(f"Correct CALL:       mean={correct_call['pm_accel'].mean():.3f}, median={correct_call['pm_accel'].median():.3f}")

print(f"\n--- PM Late Trend distribution ---")
print(f"Misclassified CALL: mean={mis_call['pm_late_trend'].mean():.3f}, median={mis_call['pm_late_trend'].median():.3f}")
print(f"Correct CALL:       mean={correct_call['pm_late_trend'].mean():.3f}, median={correct_call['pm_late_trend'].median():.3f}")

print(f"\n--- PM Position distribution ---")
print(f"Misclassified CALL: mean={mis_call['pm_position'].mean():.3f}, median={mis_call['pm_position'].median():.3f}")
print(f"Correct CALL:       mean={correct_call['pm_position'].mean():.3f}, median={correct_call['pm_position'].median():.3f}")

print(f"\n--- VIX distribution ---")
print(f"Misclassified CALL: mean={mis_call['vix_pc'].mean():.2f}, median={mis_call['vix_pc'].median():.2f}")
print(f"Correct CALL:       mean={correct_call['vix_pc'].mean():.2f}, median={correct_call['vix_pc'].median():.2f}")

print(f"\n--- Gap distribution ---")
print(f"Misclassified CALL: mean={mis_call['est_gap'].mean():.2f}, median={mis_call['est_gap'].median():.2f}")
print(f"Correct CALL:       mean={correct_call['est_gap'].mean():.2f}, median={correct_call['est_gap'].median():.2f}")

print(f"\n--- Bar1 Red rate ---")
print(f"Misclassified CALL: {mis_call['bar1_red'].mean()*100:.1f}%")
print(f"Correct CALL:       {correct_call['bar1_red'].mean()*100:.1f}%")

print(f"\n--- SPY up rate ---")
print(f"Misclassified CALL: {mis_call['spy_up'].mean()*100:.1f}%")
print(f"Correct CALL:       {correct_call['spy_up'].mean()*100:.1f}%")

print(f"\n--- Check combination frequency (misclassified) ---")
for c in range(5):
    pct_mis = mis_call[f'check{c+1}'].mean() * 100
    pct_cor = correct_call[f'check{c+1}'].mean() * 100
    print(f"  Check {c+1}: misclass={pct_mis:.0f}% correct={pct_cor:.0f}%")

# ─── SECTION 4: Misclassified PUT days ───────────────────────
print(f"\n{'='*60}")
print("MISCLASSIFIED PUT DAYS (conf<=2 or hard_kill, should have been CALL)")
print("="*60)
mis_put = put_days[put_days['misclassified']].sort_values('pnl_2m', ascending=True)

cols_put = ['date','confidence','tier','hard_kill','kill_reason',
            'check1','check2','check3','check4','check5',
            'pm_accel','pm_late_trend','pm_position','vix_pc','est_gap',
            'pnl_2m','put_pnl','bar1_red','day_direction']
print(mis_put[cols_put].to_string(index=False))

print(f"\n--- PM Accel distribution ---")
correct_put = put_days[put_days['correct']]
print(f"Misclassified PUT: mean={mis_put['pm_accel'].mean():.3f}, median={mis_put['pm_accel'].median():.3f}")
print(f"Correct PUT:       mean={correct_put['pm_accel'].mean():.3f}, median={correct_put['pm_accel'].median():.3f}")

print(f"\n--- Kill reason distribution ---")
print("Misclassified PUT kill reasons:")
print(mis_put['kill_reason'].value_counts().to_string())
print("\nCorrect PUT kill reasons:")
print(correct_put['kill_reason'].value_counts().to_string())

# ─── SECTION 5: Override rule testing ────────────────────────
print(f"\n{'='*60}")
print("OVERRIDE RULE TESTING")
print("="*60)

# Baseline: current system PnL
baseline_call_pnl = call_days['call_pnl'].sum()
baseline_put_pnl = put_days['put_pnl'].sum()
baseline_total = baseline_call_pnl + baseline_put_pnl
print(f"Baseline — CALL PnL: ${baseline_call_pnl:.2f}, PUT PnL: ${baseline_put_pnl:.2f}, Total: ${baseline_total:.2f}")

def test_override(df_all, rule_fn, rule_name):
    """Test an override rule that flips CALL->PUT days.
    rule_fn takes a row and returns True if the day should be flipped to PUT.
    """
    new_call = []
    new_put = []
    flipped = 0

    for _, row in df_all.iterrows():
        was_call = not row['is_put_day']
        should_flip = was_call and rule_fn(row)

        if should_flip:
            flipped += 1
            # This day becomes PUT: pnl = pnl_2m (positive = short wins)
            new_put.append(row['pnl_2m'])
        elif was_call:
            new_call.append(-row['pnl_2m'])  # CALL pnl
        else:
            new_put.append(row['pnl_2m'])    # already PUT

    call_pnl = sum(new_call)
    put_pnl = sum(new_put)
    total = call_pnl + put_pnl
    delta = total - baseline_total

    print(f"  {rule_name}: flipped={flipped}, CALL=${call_pnl:.2f}, PUT=${put_pnl:.2f}, Total=${total:.2f} (delta=${delta:+.2f})")
    return total, flipped, delta

# Also test overrides that flip PUT->CALL (rescue misclassified PUTs)
def test_rescue(df_all, rule_fn, rule_name):
    """Test a rescue rule that flips PUT->CALL days."""
    new_call = []
    new_put = []
    rescued = 0

    for _, row in df_all.iterrows():
        was_put = row['is_put_day']
        should_rescue = was_put and rule_fn(row)

        if should_rescue:
            rescued += 1
            new_call.append(-row['pnl_2m'])
        elif was_put:
            new_put.append(row['pnl_2m'])
        else:
            new_call.append(-row['pnl_2m'])

    call_pnl = sum(new_call)
    put_pnl = sum(new_put)
    total = call_pnl + put_pnl
    delta = total - baseline_total

    print(f"  {rule_name}: rescued={rescued}, CALL=${call_pnl:.2f}, PUT=${put_pnl:.2f}, Total=${total:.2f} (delta=${delta:+.2f})")
    return total, rescued, delta

print("\n--- CALL->PUT override rules (flip CALL days with bad signals) ---")

# Rule 1: pm_accel < -1.50 (current)
# Note: this is already in the system as hard kill. Test what happens WITHOUT it.
test_override(df, lambda r: not np.isnan(r['pm_accel']) and r['pm_accel'] < -1.50, "pm_accel < -1.50 (CURRENT)")

# Various accel thresholds
for thresh in [-2.0, -1.50, -1.0, -0.75, -0.50, -0.25, 0.0]:
    test_override(df, lambda r, t=thresh: not np.isnan(r['pm_accel']) and r['pm_accel'] < t, f"pm_accel < {thresh}")

print()
# Two-variable overrides
test_override(df, lambda r: not np.isnan(r['pm_accel']) and r['pm_accel'] < -0.5 and r['pm_late_trend'] < 0,
              "pm_accel < -0.5 AND trend < 0")
test_override(df, lambda r: not np.isnan(r['pm_accel']) and r['pm_accel'] < -0.75 and r['pm_late_trend'] < 0,
              "pm_accel < -0.75 AND trend < 0")
test_override(df, lambda r: not np.isnan(r['pm_accel']) and r['pm_accel'] < -1.0 and r['pm_late_trend'] < 0,
              "pm_accel < -1.0 AND trend < 0")
test_override(df, lambda r: not np.isnan(r['pm_accel']) and r['pm_accel'] < -0.5 and r['pm_position'] < 0.5,
              "pm_accel < -0.5 AND pos < 0.5")
test_override(df, lambda r: not np.isnan(r['pm_accel']) and r['pm_accel'] < -0.75 and r['pm_position'] < 0.5,
              "pm_accel < -0.75 AND pos < 0.5")

print()
# Bar1 based
test_override(df, lambda r: r['bar1_red'] == True, "bar1_red (flip all red bar1 CALLs)")
test_override(df, lambda r: not np.isnan(r['pm_accel']) and r['pm_accel'] < 0 and r['bar1_red'] == True,
              "pm_accel < 0 AND bar1_red")
test_override(df, lambda r: not np.isnan(r['pm_accel']) and r['pm_accel'] < -0.5 and r['bar1_red'] == True,
              "pm_accel < -0.5 AND bar1_red")

print()
# SPY divergence
test_override(df, lambda r: r['spy_up'] == False, "SPY down at 9:29")
test_override(df, lambda r: r['spy_up'] == False and not np.isnan(r['pm_accel']) and r['pm_accel'] < 0,
              "SPY down AND pm_accel < 0")

print()
# VIX ranges
test_override(df, lambda r: not np.isnan(r['vix_pc']) and r['vix_pc'] > 25, "VIX > 25")
test_override(df, lambda r: not np.isnan(r['vix_pc']) and r['vix_pc'] > 30, "VIX > 30")

print()
# Gap
test_override(df, lambda r: r['est_gap'] < -3, "gap < -3")
test_override(df, lambda r: r['est_gap'] < -5, "gap < -5")
test_override(df, lambda r: r['est_gap'] > 5, "gap > 5")

print()
# Trend
test_override(df, lambda r: not np.isnan(r['pm_late_trend']) and r['pm_late_trend'] < -1, "trend < -1")
test_override(df, lambda r: not np.isnan(r['pm_late_trend']) and r['pm_late_trend'] < -2, "trend < -2")

print()
# Combined best candidates
test_override(df, lambda r: not np.isnan(r['pm_accel']) and r['pm_accel'] < -0.5 and r['pm_late_trend'] < -1,
              "pm_accel < -0.5 AND trend < -1")
test_override(df, lambda r: not np.isnan(r['pm_accel']) and r['pm_accel'] < -0.75 and r['pm_late_trend'] < -0.5,
              "pm_accel < -0.75 AND trend < -0.5")
test_override(df, lambda r: not np.isnan(r['pm_accel']) and r['pm_accel'] < 0 and r['pm_late_trend'] < -1 and r['pm_position'] < 0.5,
              "accel < 0 AND trend < -1 AND pos < 0.5")

print("\n--- PUT->CALL rescue rules ---")
test_rescue(df, lambda r: r['pm_accel'] > 1.0 and r['pm_position'] > 0.7, "accel > 1.0 AND pos > 0.7")
test_rescue(df, lambda r: r['pm_accel'] > 0.5 and r['pm_position'] > 0.8, "accel > 0.5 AND pos > 0.8")
test_rescue(df, lambda r: r['kill_reason'] == 'LOW_VOL' and r['pm_accel'] > 0.5, "LOW_VOL kill AND accel > 0.5")

# ─── SECTION 6: Worst CALL days ──────────────────────────────
print(f"\n{'='*60}")
print("10 WORST CALL DAYS (largest CALL losses at 2m)")
print("="*60)
worst_call = call_days.nlargest(10, 'pnl_2m')  # pnl_2m positive = price dropped, CALL lost
cols_worst = ['date','confidence','tier','pm_accel','pm_late_trend','pm_position',
              'vix_pc','est_gap','pnl_2m','call_pnl','bar1_red','day_direction',
              'check1','check2','check3','check4','check5','spy_up','p9_30s_down']
print(worst_call[cols_worst].to_string(index=False))

print(f"\n--- Common patterns in worst 10 ---")
print(f"Bar1 Red rate: {worst_call['bar1_red'].mean()*100:.0f}%")
print(f"PM Accel mean: {worst_call['pm_accel'].mean():.3f}")
print(f"PM Trend mean: {worst_call['pm_late_trend'].mean():.3f}")
print(f"PM Pos mean:   {worst_call['pm_position'].mean():.3f}")
print(f"SPY up rate:   {worst_call['spy_up'].mean()*100:.0f}%")
print(f"VIX mean:      {worst_call['vix_pc'].mean():.1f}")
print(f"Day dir BEAR:  {(worst_call['day_direction']=='BEAR').mean()*100:.0f}%")

# ─── SECTION 7: Best PUT misses ──────────────────────────────
print(f"\n{'='*60}")
print("10 BIGGEST PUT GAINS ON CALL-CLASSIFIED DAYS (missed opportunities)")
print("="*60)
# These are CALL days where pnl_2m is most positive (price dropped, PUT would have won)
best_put_miss = call_days.nlargest(10, 'pnl_2m')
cols_miss = ['date','confidence','tier','pm_accel','pm_late_trend','pm_position',
             'vix_pc','est_gap','pnl_2m','bar1_red','day_direction',
             'check1','check2','check3','check4','check5']
print(best_put_miss[cols_miss].to_string(index=False))

# ─── SECTION 8: Summary stats ────────────────────────────────
print(f"\n{'='*60}")
print("SUMMARY STATISTICS")
print("="*60)

print(f"\nConf distribution:")
for c in range(6):
    n = (df['confidence'] == c).sum()
    pnl_call = -df[(df['confidence'] == c) & (~df['is_put_day'])]['pnl_2m'].sum()
    pnl_put = df[(df['confidence'] == c) & (df['is_put_day'])]['pnl_2m'].sum()
    n_call = (~df['is_put_day'] & (df['confidence'] == c)).sum()
    n_put = (df['is_put_day'] & (df['confidence'] == c)).sum()
    print(f"  conf={c}: n={n} (CALL:{n_call}, PUT:{n_put}), CALL_pnl=${pnl_call:.2f}, PUT_pnl=${pnl_put:.2f}")

print(f"\nTier distribution:")
for t in ['HIGH', 'MED', 'LOW', 'NO-GO']:
    n = (df['tier'] == t).sum()
    mask_call = (df['tier'] == t) & (~df['is_put_day'])
    mask_put = (df['tier'] == t) & (df['is_put_day'])
    pnl_c = -df[mask_call]['pnl_2m'].sum()
    pnl_p = df[mask_put]['pnl_2m'].sum()
    print(f"  {t}: n={n} (CALL:{mask_call.sum()}, PUT:{mask_put.sum()}), CALL_pnl=${pnl_c:.2f}, PUT_pnl=${pnl_p:.2f}")

# Win rates
print(f"\nWin rates by tier:")
for t in ['HIGH', 'MED', 'LOW', 'NO-GO']:
    mask_c = (df['tier'] == t) & (~df['is_put_day'])
    mask_p = (df['tier'] == t) & (df['is_put_day'])
    if mask_c.sum() > 0:
        wr_c = (df[mask_c]['pnl_2m'] < 0).mean() * 100
        print(f"  {t} CALL: {wr_c:.1f}% win (n={mask_c.sum()})")
    if mask_p.sum() > 0:
        wr_p = (df[mask_p]['pnl_2m'] > 0).mean() * 100
        print(f"  {t} PUT:  {wr_p:.1f}% win (n={mask_p.sum()})")

# ─── Without the -1.50 accel kill (what the system looked like before v1.4) ───
print(f"\n{'='*60}")
print("COMPARISON: WITH vs WITHOUT pm_accel < -1.50 HARD KILL")
print("="*60)

# Re-classify without the accel kill
no_accel_kill_results = []
for _, row in df.iterrows():
    # Remove accel hard kill
    hk = row['hard_kill']
    kr = row['kill_reason']
    conf = row['confidence']

    if kr == 'ACCEL':
        hk = False
        kr = 'none'

    # Recompute tier without accel kill
    if hk:
        t = "NO-GO"
    elif conf >= 5:
        t = "HIGH"
    elif conf >= 3:
        t = "MED"
    elif conf >= 2:
        t = "LOW"
    else:
        t = "NO-GO"

    is_put = conf <= 2 or hk

    no_accel_kill_results.append({
        'date': row['date'],
        'is_put_day_no_accel': is_put,
        'pnl_2m': row['pnl_2m'],
    })

df_noaccel = pd.DataFrame(no_accel_kill_results)
call_pnl_noaccel = -df_noaccel[~df_noaccel['is_put_day_no_accel']]['pnl_2m'].sum()
put_pnl_noaccel = df_noaccel[df_noaccel['is_put_day_no_accel']]['pnl_2m'].sum()
total_noaccel = call_pnl_noaccel + put_pnl_noaccel

print(f"Without accel kill: CALL=${call_pnl_noaccel:.2f}, PUT=${put_pnl_noaccel:.2f}, Total=${total_noaccel:.2f}")
print(f"With accel kill:    CALL=${baseline_call_pnl:.2f}, PUT=${baseline_put_pnl:.2f}, Total=${baseline_total:.2f}")
print(f"Delta from accel kill: ${baseline_total - total_noaccel:+.2f}")

# Show which days flipped
accel_flipped = df[df['kill_reason'] == 'ACCEL']
print(f"\nDays flipped by accel kill ({len(accel_flipped)}):")
for _, row in accel_flipped.iterrows():
    print(f"  {row['date']} conf={row['confidence']} accel={row['pm_accel']:.2f} pnl_2m={row['pnl_2m']:.2f} (as PUT: ${row['pnl_2m']:.2f}, as CALL: ${-row['pnl_2m']:.2f})")

# ─── Final optimal threshold search for accel ────────────────
print(f"\n{'='*60}")
print("OPTIMAL ACCEL THRESHOLD SEARCH")
print("="*60)

best_total = -9999
best_thresh = None
for thresh in np.arange(-3.0, 0.5, 0.05):
    total_pnl = 0
    for _, row in df.iterrows():
        # Recompute with this threshold instead of -1.50
        hk = row['hard_kill']
        kr = row['kill_reason']
        conf = row['confidence']

        # Remove old accel kill, add new threshold
        if kr == 'ACCEL':
            hk = False
        if not np.isnan(row['pm_accel']) and row['pm_accel'] < thresh:
            hk = True

        is_put = conf <= 2 or hk

        if is_put:
            total_pnl += row['pnl_2m']
        else:
            total_pnl += -row['pnl_2m']

    if total_pnl > best_total:
        best_total = total_pnl
        best_thresh = thresh

print(f"Best accel threshold: {best_thresh:.2f} → Total PnL: ${best_total:.2f}")
print(f"Current (-1.50):                  Total PnL: ${baseline_total:.2f}")
print(f"Improvement: ${best_total - baseline_total:+.2f}")

# Also test combined accel + trend thresholds
print(f"\n--- Combined accel + trend threshold optimization ---")
best_combo = (-9999, None, None)
for a_thresh in np.arange(-2.0, 0.25, 0.25):
    for t_thresh in np.arange(-3.0, 1.0, 0.5):
        total_pnl = 0
        flipped = 0
        for _, row in df.iterrows():
            hk = row['hard_kill']
            kr = row['kill_reason']
            conf = row['confidence']

            if kr == 'ACCEL':
                hk = False

            # New combo rule
            if (not np.isnan(row['pm_accel']) and row['pm_accel'] < a_thresh and
                not np.isnan(row['pm_late_trend']) and row['pm_late_trend'] < t_thresh):
                if not (conf <= 2 or hk):
                    flipped += 1
                hk = True

            is_put = conf <= 2 or hk
            if is_put:
                total_pnl += row['pnl_2m']
            else:
                total_pnl += -row['pnl_2m']

        if total_pnl > best_combo[0]:
            best_combo = (total_pnl, a_thresh, t_thresh, flipped)

print(f"Best combo: accel < {best_combo[1]:.2f} AND trend < {best_combo[2]:.1f} → Total PnL: ${best_combo[0]:.2f} (flips {best_combo[3]} days)")
print(f"Improvement over baseline: ${best_combo[0] - baseline_total:+.2f}")

print("\n\nDone. Writing report...")
