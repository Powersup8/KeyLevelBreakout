#!/usr/bin/env python3
"""
v2.8b MC Smart Filter Research
Find features that can distinguish the correct MC signal at market open,
instead of using a simple 9:50 time gate.
"""

import pandas as pd
import numpy as np
from collections import defaultdict

# ─── Load data ───────────────────────────────────────────────────────────────
signals = pd.read_csv('debug/v28a-signals.csv')
pairs = pd.read_csv('debug/v28a-mc-opposing-pairs.csv')

mc = signals[signals['line_type'] == 'MC'].copy()
mc['dt'] = pd.to_datetime(mc['datetime'], utc=True)
mc['date'] = mc['dt'].dt.date.astype(str)

# CONF rows for MC
conf_mc = signals[(signals['line_type'] == 'CONF') & (signals['conf_source'] == 'QBS/MC')].copy()
conf_mc['dt'] = pd.to_datetime(conf_mc['datetime'], utc=True)
conf_mc['date'] = conf_mc['dt'].dt.date.astype(str)

report = []
report.append("# v2.8b MC Smart Filter Research\n")
report.append("## Goal")
report.append("Find a smarter filter than the simple '9:50 time gate' for MC signals at market open.")
report.append(f"**Baseline:** First MC correct 45% (126 opposing pairs, coin flip).\n")
report.append(f"**Target:** Find features that predict which MC (bull or bear) is the correct one.\n")

# ─── Enrich pairs with full signal features ──────────────────────────────────
# For each pair, find the matching MC signals from the signals CSV

enriched = []
for _, p in pairs.iterrows():
    sym = p['symbol']
    date = p['date']

    day_mc = mc[(mc['symbol'] == sym) & (mc['date'] == date)]

    first_mc = day_mc[(day_mc['direction'] == p['first_dir']) & (day_mc['time'] == p['first_time'])]
    second_mc = day_mc[(day_mc['direction'] == p['second_dir']) & (day_mc['time'] == p['second_time'])]

    if len(first_mc) == 0 or len(second_mc) == 0:
        continue

    f = first_mc.iloc[0]
    s = second_mc.iloc[0]

    row = {
        'symbol': sym, 'date': date,
        'actual_dir': p['actual_dir'],
        'move_30m': p['move_30m'],
        'first_correct': p['first_correct'],
        'second_correct': p['second_correct'],
        # First signal features
        'first_dir': p['first_dir'], 'first_time': p['first_time'],
        'first_vol': f['vol'], 'first_ramp': f['ramp'],
        'first_close_pos': f['close_pos'], 'first_body': f['body'],
        'first_range_atr': f['range_atr'], 'first_adx': f['adx'],
        'first_ema': f['ema'], 'first_vwap': f['vwap'],
        # Second signal features
        'second_dir': p['second_dir'], 'second_time': p['second_time'],
        'second_vol': s['vol'], 'second_ramp': s['ramp'],
        'second_close_pos': s['close_pos'], 'second_body': s['body'],
        'second_range_atr': s['range_atr'], 'second_adx': s['adx'],
        'second_ema': s['ema'], 'second_vwap': s['vwap'],
    }

    # Get CONF results for this day
    day_conf = conf_mc[(conf_mc['symbol'] == sym) & (conf_mc['date'] == date)]
    first_conf = day_conf[day_conf['direction'] == p['first_dir']]
    second_conf = day_conf[day_conf['direction'] == p['second_dir']]
    row['first_conf'] = first_conf.iloc[0]['conf_result'] if len(first_conf) > 0 else 'none'
    row['second_conf'] = second_conf.iloc[0]['conf_result'] if len(second_conf) > 0 else 'none'

    enriched.append(row)

df = pd.DataFrame(enriched)
print(f"Enriched pairs: {len(df)} (of {len(pairs)} total)")
report.append(f"\n**Enriched pairs matched:** {len(df)} of {len(pairs)}\n")

# ─── Helper: compute accuracy for a filter ───────────────────────────────────
def test_filter(df, name, pick_first_mask, pick_second_mask=None):
    """
    Given masks indicating when to pick first vs second, compute accuracy.
    pick_first_mask: boolean mask where True = pick first signal
    pick_second_mask: boolean mask where True = pick second signal
    If neither, skip that pair.
    """
    if pick_second_mask is None:
        pick_second_mask = ~pick_first_mask

    # Only count pairs where we make a decision
    decided = pick_first_mask | pick_second_mask
    n_decided = decided.sum()

    if n_decided == 0:
        return {'name': name, 'n': 0, 'correct': 0, 'accuracy': 0, 'vs_baseline': 0}

    correct = (
        (pick_first_mask & df['first_correct']) |
        (pick_second_mask & df['second_correct'])
    ).sum()

    acc = correct / n_decided * 100
    return {
        'name': name,
        'n': int(n_decided),
        'correct': int(correct),
        'accuracy': round(acc, 1),
        'vs_baseline': round(acc - 45, 1)
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Single-Feature Filters
# ═══════════════════════════════════════════════════════════════════════════════
report.append("\n---\n## Section 1: Single-Feature Filters\n")

results = []

# ─── 1a. Always pick second (baseline for "second is better") ────────────────
r = test_filter(df, "Always pick SECOND", pd.Series([False]*len(df)), pd.Series([True]*len(df)))
results.append(r)

# ─── 1b. Always pick first ──────────────────────────────────────────────────
r = test_filter(df, "Always pick FIRST", pd.Series([True]*len(df)), pd.Series([False]*len(df)))
results.append(r)

# ─── 2. EMA alignment ───────────────────────────────────────────────────────
# Pick the MC whose direction matches EMA
first_ema_match = (
    ((df['first_dir'] == 'bull') & (df['first_ema'] == 'bull')) |
    ((df['first_dir'] == 'bear') & (df['first_ema'] == 'bear'))
)
second_ema_match = (
    ((df['second_dir'] == 'bull') & (df['second_ema'] == 'bull')) |
    ((df['second_dir'] == 'bear') & (df['second_ema'] == 'bear'))
)
# Pick the one that matches EMA (if both or neither match, skip or use first)
ema_pick_first = first_ema_match & ~second_ema_match
ema_pick_second = second_ema_match & ~first_ema_match
r = test_filter(df, "Pick MC matching EMA (exclusive)", ema_pick_first, ema_pick_second)
results.append(r)

# Pick opposite of EMA (counter-trend at open)
r = test_filter(df, "Pick MC AGAINST EMA (counter-trend)", ema_pick_second, ema_pick_first)
results.append(r)

# ─── 3. VWAP alignment ──────────────────────────────────────────────────────
first_vwap_match = (
    ((df['first_dir'] == 'bull') & (df['first_vwap'] == 'above')) |
    ((df['first_dir'] == 'bear') & (df['first_vwap'] == 'below'))
)
second_vwap_match = (
    ((df['second_dir'] == 'bull') & (df['second_vwap'] == 'above')) |
    ((df['second_dir'] == 'bear') & (df['second_vwap'] == 'below'))
)
vwap_pick_first = first_vwap_match & ~second_vwap_match
vwap_pick_second = second_vwap_match & ~first_vwap_match
r = test_filter(df, "Pick MC matching VWAP (exclusive)", vwap_pick_first, vwap_pick_second)
results.append(r)

r = test_filter(df, "Pick MC AGAINST VWAP (counter-trend)", vwap_pick_second, vwap_pick_first)
results.append(r)

# ─── 4. ADX level ────────────────────────────────────────────────────────────
# Pick the one with higher ADX
adx_pick_first = df['first_adx'] > df['second_adx']
adx_pick_second = df['second_adx'] > df['first_adx']
r = test_filter(df, "Pick MC with HIGHER ADX", adx_pick_first, adx_pick_second)
results.append(r)
r = test_filter(df, "Pick MC with LOWER ADX", adx_pick_second, adx_pick_first)
results.append(r)

# ─── 5. Volume ratio ────────────────────────────────────────────────────────
vol_pick_first = df['first_vol'] > df['second_vol']
vol_pick_second = df['second_vol'] > df['first_vol']
r = test_filter(df, "Pick MC with HIGHER volume", vol_pick_first, vol_pick_second)
results.append(r)
r = test_filter(df, "Pick MC with LOWER volume", vol_pick_second, vol_pick_first)
results.append(r)

# ─── 6. Ramp ratio ──────────────────────────────────────────────────────────
ramp_pick_first = df['first_ramp'] > df['second_ramp']
ramp_pick_second = df['second_ramp'] > df['first_ramp']
r = test_filter(df, "Pick MC with HIGHER ramp", ramp_pick_first, ramp_pick_second)
results.append(r)
r = test_filter(df, "Pick MC with LOWER ramp", ramp_pick_second, ramp_pick_first)
results.append(r)

# ─── 7. Close position quality ──────────────────────────────────────────────
cp_pick_first = df['first_close_pos'] > df['second_close_pos']
cp_pick_second = df['second_close_pos'] > df['first_close_pos']
r = test_filter(df, "Pick MC with HIGHER close_pos", cp_pick_first, cp_pick_second)
results.append(r)
r = test_filter(df, "Pick MC with LOWER close_pos", cp_pick_second, cp_pick_first)
results.append(r)

# ─── 8. Body percentage ─────────────────────────────────────────────────────
body_pick_first = df['first_body'] > df['second_body']
body_pick_second = df['second_body'] > df['first_body']
r = test_filter(df, "Pick MC with HIGHER body%", body_pick_first, body_pick_second)
results.append(r)
r = test_filter(df, "Pick MC with LOWER body% (less exhaustion)", body_pick_second, body_pick_first)
results.append(r)

# ─── 9. Range ATR ───────────────────────────────────────────────────────────
ra_pick_first = df['first_range_atr'] > df['second_range_atr']
ra_pick_second = df['second_range_atr'] > df['first_range_atr']
r = test_filter(df, "Pick MC with HIGHER range_atr (bigger bar)", ra_pick_first, ra_pick_second)
results.append(r)
r = test_filter(df, "Pick MC with LOWER range_atr (smaller bar)", ra_pick_second, ra_pick_first)
results.append(r)

# ─── 10. CONF result ────────────────────────────────────────────────────────
conf_star_first = df['first_conf'] == 'star'
conf_star_second = df['second_conf'] == 'star'
r = test_filter(df, "Pick MC with STAR conf (exclusive)",
                conf_star_first & ~conf_star_second,
                conf_star_second & ~conf_star_first)
results.append(r)

conf_pass_first = df['first_conf'].isin(['star', 'pass'])
conf_pass_second = df['second_conf'].isin(['star', 'pass'])
r = test_filter(df, "Pick MC with PASS+ conf (exclusive)",
                conf_pass_first & ~conf_pass_second,
                conf_pass_second & ~conf_pass_first)
results.append(r)

# ─── Print Section 1 results ─────────────────────────────────────────────────
report.append("| Filter | n | Correct | Accuracy | vs 45% baseline |")
report.append("|--------|---|---------|----------|-----------------|")
for r in sorted(results, key=lambda x: x['accuracy'], reverse=True):
    report.append(f"| {r['name']} | {r['n']} | {r['correct']} | **{r['accuracy']}%** | {'+' if r['vs_baseline']>0 else ''}{r['vs_baseline']}% |")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: "Second Signal Wins" with Feature Confirmation
# ═══════════════════════════════════════════════════════════════════════════════
report.append("\n---\n## Section 2: Second Signal + Feature Confirmation\n")
report.append("Since second signal has 55% baseline, test if adding features improves it.\n")

results2 = []

# Second + second matches EMA
mask = second_ema_match
r = test_filter(df[mask], "Second + EMA match",
                pd.Series([False]*mask.sum()), pd.Series([True]*mask.sum()))
results2.append(r)

mask = ~second_ema_match
r = test_filter(df[mask], "Second + EMA mismatch",
                pd.Series([False]*mask.sum()), pd.Series([True]*mask.sum()))
results2.append(r)

# Second + VWAP
mask = second_vwap_match
r = test_filter(df[mask], "Second + VWAP match",
                pd.Series([False]*mask.sum()), pd.Series([True]*mask.sum()))
results2.append(r)

mask = ~second_vwap_match
r = test_filter(df[mask], "Second + VWAP mismatch",
                pd.Series([False]*mask.sum()), pd.Series([True]*mask.sum()))
results2.append(r)

# Second + higher ramp than first
mask = df['second_ramp'] > df['first_ramp']
r = test_filter(df[mask], "Second + higher ramp",
                pd.Series([False]*mask.sum()), pd.Series([True]*mask.sum()))
results2.append(r)

mask = df['second_ramp'] <= df['first_ramp']
r = test_filter(df[mask], "Second + lower ramp",
                pd.Series([False]*mask.sum()), pd.Series([True]*mask.sum()))
results2.append(r)

# Second + lower body (less wick exhaustion)
mask = df['second_body'] < df['first_body']
r = test_filter(df[mask], "Second + lower body%",
                pd.Series([False]*mask.sum()), pd.Series([True]*mask.sum()))
results2.append(r)

# Second + higher close_pos
mask = df['second_close_pos'] > df['first_close_pos']
r = test_filter(df[mask], "Second + higher close_pos",
                pd.Series([False]*mask.sum()), pd.Series([True]*mask.sum()))
results2.append(r)

# Second + CONF star
mask = df['second_conf'] == 'star'
r = test_filter(df[mask], "Second + CONF star",
                pd.Series([False]*mask.sum()), pd.Series([True]*mask.sum()))
results2.append(r)

# Second + CONF pass or star
mask = df['second_conf'].isin(['star', 'pass'])
r = test_filter(df[mask], "Second + CONF pass+",
                pd.Series([False]*mask.sum()), pd.Series([True]*mask.sum()))
results2.append(r)

report.append("| Filter | n | Correct | Accuracy | vs 55% (second) |")
report.append("|--------|---|---------|----------|-----------------|")
for r in sorted(results2, key=lambda x: x['accuracy'], reverse=True):
    vs = round(r['accuracy'] - 55, 1)
    report.append(f"| {r['name']} | {r['n']} | {r['correct']} | **{r['accuracy']}%** | {'+' if vs>0 else ''}{vs}% |")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: Gap Direction Analysis
# ═══════════════════════════════════════════════════════════════════════════════
report.append("\n---\n## Section 3: Gap / First Bar Direction\n")

# The first MC is usually at 9:35. Its direction could indicate the opening bar direction.
# Does the first bar direction (= first MC direction) predict actual_dir?

# First MC direction as proxy for opening bar
first_is_bull = df['first_dir'] == 'bull'
actual_is_bull = df['actual_dir'] == 'bull'

# If first bar is bull, does that predict bull day?
first_bull_right = (first_is_bull & actual_is_bull).sum()
first_bull_total = first_is_bull.sum()
first_bear_right = (~first_is_bull & ~actual_is_bull).sum()
first_bear_total = (~first_is_bull).sum()

report.append(f"**First MC bull -> actual bull:** {first_bull_right}/{first_bull_total} = {first_bull_right/first_bull_total*100:.0f}%")
report.append(f"**First MC bear -> actual bear:** {first_bear_right}/{first_bear_total} = {first_bear_right/first_bear_total*100:.0f}%")
report.append(f"*First MC direction = opening bar direction (proxy for gap)*\n")

# Does the move_30m magnitude correlate with feature differences?
report.append("### Move magnitude vs feature delta\n")
df['vol_delta'] = df['first_vol'] - df['second_vol']
df['ramp_delta'] = df['first_ramp'] - df['second_ramp']
df['body_delta'] = df['first_body'] - df['second_body']
df['range_delta'] = df['first_range_atr'] - df['second_range_atr']

# Correct = first_correct
# Check if the "correct" MC has systematically different features
correct_features = []
for _, row in df.iterrows():
    if row['first_correct']:
        correct_features.append({
            'vol': row['first_vol'], 'ramp': row['first_ramp'],
            'body': row['first_body'], 'range_atr': row['first_range_atr'],
            'close_pos': row['first_close_pos'], 'adx': row['first_adx'],
            'which': 'first'
        })
    else:
        correct_features.append({
            'vol': row['second_vol'], 'ramp': row['second_ramp'],
            'body': row['second_body'], 'range_atr': row['second_range_atr'],
            'close_pos': row['second_close_pos'], 'adx': row['second_adx'],
            'which': 'second'
        })

wrong_features = []
for _, row in df.iterrows():
    if not row['first_correct']:
        wrong_features.append({
            'vol': row['first_vol'], 'ramp': row['first_ramp'],
            'body': row['first_body'], 'range_atr': row['first_range_atr'],
            'close_pos': row['first_close_pos'], 'adx': row['first_adx'],
            'which': 'first'
        })
    else:
        wrong_features.append({
            'vol': row['second_vol'], 'ramp': row['second_ramp'],
            'body': row['second_body'], 'range_atr': row['second_range_atr'],
            'close_pos': row['second_close_pos'], 'adx': row['second_adx'],
            'which': 'second'
        })

cf = pd.DataFrame(correct_features)
wf = pd.DataFrame(wrong_features)

report.append("| Feature | Correct MC (mean) | Wrong MC (mean) | Delta |")
report.append("|---------|------------------|-----------------|-------|")
for feat in ['vol', 'ramp', 'body', 'range_atr', 'close_pos', 'adx']:
    cm = cf[feat].mean()
    wm = wf[feat].mean()
    delta = cm - wm
    pct = delta / wm * 100 if wm != 0 else 0
    report.append(f"| {feat} | {cm:.1f} | {wm:.1f} | {pct:+.0f}% |")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: Sequential Analysis — Does Second MC "Confirm" or "Reverse"?
# ═══════════════════════════════════════════════════════════════════════════════
report.append("\n---\n## Section 4: Sequential / Timing Analysis\n")

# Time gap between first and second MC
def time_to_min(t):
    h, m = t.split(':')
    return int(h) * 60 + int(m)

df['time_gap'] = df.apply(lambda r: time_to_min(r['second_time']) - time_to_min(r['first_time']), axis=1)

report.append("### Time gap between opposing MCs\n")
for gap in sorted(df['time_gap'].unique()):
    subset = df[df['time_gap'] == gap]
    second_right = subset['second_correct'].sum()
    n = len(subset)
    report.append(f"- **{gap}min gap:** n={n}, second correct={second_right}/{n} ({second_right/n*100:.0f}%)")

report.append("")

# Does LARGER time gap = more reliable second signal?
short_gap = df[df['time_gap'] <= 5]
long_gap = df[df['time_gap'] >= 10]
report.append(f"**Short gap (<=5min):** second correct {short_gap['second_correct'].sum()}/{len(short_gap)} ({short_gap['second_correct'].mean()*100:.0f}%)")
report.append(f"**Long gap (>=10min):** second correct {long_gap['second_correct'].sum()}/{len(long_gap)} ({long_gap['second_correct'].mean()*100:.0f}%)")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: Combination Filters
# ═══════════════════════════════════════════════════════════════════════════════
report.append("\n---\n## Section 5: Combination Filters\n")
report.append("Test multi-feature combinations.\n")

results5 = []

# ─── Combo 1: Second + EMA match + VWAP mismatch (counter-VWAP) ──────────
# The existing analysis showed VWAP alignment is INVERSE (wrong MC matches VWAP more)
# So: pick second MC when it DOES NOT match VWAP but DOES match EMA
mask = second_ema_match & ~second_vwap_match
sub = df[mask]
if len(sub) > 0:
    r = test_filter(sub, "Second + EMA match + VWAP counter",
                    pd.Series([False]*len(sub)), pd.Series([True]*len(sub)))
    results5.append(r)

# ─── Combo 2: Pick the one that matches EMA but NOT VWAP ─────────────────
first_ema_no_vwap = first_ema_match & ~first_vwap_match
second_ema_no_vwap = second_ema_match & ~second_vwap_match
r = test_filter(df, "EMA match + VWAP counter (exclusive)",
                first_ema_no_vwap & ~second_ema_no_vwap,
                second_ema_no_vwap & ~first_ema_no_vwap)
results5.append(r)

# ─── Combo 3: Second + higher ramp + EMA match ──────────────────────────
mask = (df['second_ramp'] > df['first_ramp']) & second_ema_match
sub = df[mask]
if len(sub) > 0:
    r = test_filter(sub, "Second + higher ramp + EMA match",
                    pd.Series([False]*len(sub)), pd.Series([True]*len(sub)))
    results5.append(r)

# ─── Combo 4: Pick against VWAP (the trap is the with-VWAP MC) ──────────
# At open, the "with VWAP" MC is the trap (81% of wrong MCs match VWAP)
# So pick the one that DOESN'T match VWAP
vwap_counter_first = ~first_vwap_match & second_vwap_match
vwap_counter_second = ~second_vwap_match & first_vwap_match
r = test_filter(df, "Pick AGAINST VWAP (counter-VWAP)",
                vwap_counter_first, vwap_counter_second)
results5.append(r)

# ─── Combo 5: Second + lower volume (reversal pattern) ──────────────────
mask = df['second_vol'] < df['first_vol']
sub = df[mask]
if len(sub) > 0:
    r = test_filter(sub, "Second + lower vol (reversal)",
                    pd.Series([False]*len(sub)), pd.Series([True]*len(sub)))
    results5.append(r)

# ─── Combo 6: Second + lower vol + EMA match ────────────────────────────
mask = (df['second_vol'] < df['first_vol']) & second_ema_match
sub = df[mask]
if len(sub) > 0:
    r = test_filter(sub, "Second + lower vol + EMA match",
                    pd.Series([False]*len(sub)), pd.Series([True]*len(sub)))
    results5.append(r)

# ─── Combo 7: Second + CONF star + EMA match ────────────────────────────
mask = (df['second_conf'] == 'star') & second_ema_match
sub = df[mask]
if len(sub) > 0:
    r = test_filter(sub, "Second + CONF star + EMA match",
                    pd.Series([False]*len(sub)), pd.Series([True]*len(sub)))
    results5.append(r)

# ─── Combo 8: Pick against VWAP + with EMA ──────────────────────────────
# Most promising: wrong MC aligns with VWAP, correct aligns with EMA is 50/50
# But counter-VWAP alone might be strong
# Try: the MC that is counter-VWAP AND has EMA alignment
first_counter_vwap_ema = ~first_vwap_match & first_ema_match
second_counter_vwap_ema = ~second_vwap_match & second_ema_match
r = test_filter(df, "Counter-VWAP + EMA match (exclusive)",
                first_counter_vwap_ema & ~second_counter_vwap_ema,
                second_counter_vwap_ema & ~first_counter_vwap_ema)
results5.append(r)

# ─── Combo 9: Second + time gap >= 10 ───────────────────────────────────
mask = df['time_gap'] >= 10
sub = df[mask]
if len(sub) > 0:
    r = test_filter(sub, "Second + gap >= 10min",
                    pd.Series([False]*len(sub)), pd.Series([True]*len(sub)))
    results5.append(r)

# ─── Combo 10: Second + gap >= 10 + EMA match ───────────────────────────
mask = (df['time_gap'] >= 10) & second_ema_match
sub = df[mask]
if len(sub) > 0:
    r = test_filter(sub, "Second + gap >= 10min + EMA match",
                    pd.Series([False]*len(sub)), pd.Series([True]*len(sub)))
    results5.append(r)

# ─── Combo 11: Second + gap >= 10 + counter-VWAP ────────────────────────
mask = (df['time_gap'] >= 10) & ~second_vwap_match
sub = df[mask]
if len(sub) > 0:
    r = test_filter(sub, "Second + gap >= 10min + counter-VWAP",
                    pd.Series([False]*len(sub)), pd.Series([True]*len(sub)))
    results5.append(r)

# ─── Combo 12: Higher ramp wins ─────────────────────────────────────────
# This is different from "pick higher ramp" — here we look at the ramp RATIO
df['ramp_ratio'] = df['second_ramp'] / df['first_ramp']
# When second has 2x+ ramp, does it win?
for thresh in [1.0, 1.5, 2.0]:
    mask = df['ramp_ratio'] >= thresh
    sub = df[mask]
    if len(sub) > 0:
        r = test_filter(sub, f"Second + ramp ratio >= {thresh}x",
                        pd.Series([False]*len(sub)), pd.Series([True]*len(sub)))
        results5.append(r)

# ─── Combo 13: CONF-based selection ──────────────────────────────────────
# Pick the MC whose CONF is star, suppress the one whose CONF failed
conf_first_star_second_fail = (df['first_conf'] == 'star') & (df['second_conf'] == 'fail')
conf_second_star_first_fail = (df['second_conf'] == 'star') & (df['first_conf'] == 'fail')
r = test_filter(df, "CONF star vs fail (exclusive)",
                conf_first_star_second_fail, conf_second_star_first_fail)
results5.append(r)

# ─── Combo 14: Both EMA and VWAP agree on one side ──────────────────────
# If EMA=bull and VWAP=above both point to BULL MC, pick that one
first_both_agree = first_ema_match & first_vwap_match
second_both_agree = second_ema_match & second_vwap_match
r = test_filter(df, "Both EMA+VWAP agree (exclusive)",
                first_both_agree & ~second_both_agree,
                second_both_agree & ~first_both_agree)
results5.append(r)

# ─── Combo 15: Neither EMA nor VWAP agree → pick second ─────────────────
neither_agree = ~first_both_agree & ~second_both_agree
sub = df[neither_agree]
if len(sub) > 0:
    r = test_filter(sub, "Neither agree -> pick second",
                    pd.Series([False]*len(sub)), pd.Series([True]*len(sub)))
    results5.append(r)

# ─── Combo 16: Volume * Range composite ─────────────────────────────────
df['first_power'] = df['first_vol'] * df['first_range_atr']
df['second_power'] = df['second_vol'] * df['second_range_atr']
power_first = df['first_power'] > df['second_power']
r = test_filter(df, "Pick HIGHER vol*range (power)", power_first, ~power_first)
results5.append(r)
r = test_filter(df, "Pick LOWER vol*range (power)", ~power_first, power_first)
results5.append(r)

# ─── Combo 17: ADX threshold ────────────────────────────────────────────
for adx_thresh in [20, 25, 30, 35, 40]:
    # When ADX is high at second MC time, is second more reliable?
    mask = df['second_adx'] >= adx_thresh
    sub = df[mask]
    if len(sub) > 0:
        r = test_filter(sub, f"Second + ADX >= {adx_thresh}",
                        pd.Series([False]*len(sub)), pd.Series([True]*len(sub)))
        results5.append(r)

# ─── Combo 18: Move magnitude cutoff ────────────────────────────────────
# Large moves are more directional
for move_thresh in [0.5, 1.0, 1.5, 2.0]:
    mask = df['move_30m'].abs() >= move_thresh
    sub = df[mask]
    if len(sub) > 0:
        second_right = sub['second_correct'].sum()
        r = test_filter(sub, f"Second + |move| >= {move_thresh}",
                        pd.Series([False]*len(sub)), pd.Series([True]*len(sub)))
        results5.append(r)

report.append("| Filter | n | Correct | Accuracy | vs 45% baseline |")
report.append("|--------|---|---------|----------|-----------------|")
for r in sorted(results5, key=lambda x: x['accuracy'], reverse=True):
    report.append(f"| {r['name']} | {r['n']} | {r['correct']} | **{r['accuracy']}%** | {'+' if r['vs_baseline']>0 else ''}{r['vs_baseline']}% |")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: VWAP Counter-Trend Deep Dive
# ═══════════════════════════════════════════════════════════════════════════════
report.append("\n---\n## Section 6: VWAP Counter-Trend Deep Dive\n")
report.append("The existing analysis showed WRONG MC aligns with VWAP 81% of the time.")
report.append("This means the 'obvious' with-VWAP MC at the open is the TRAP.\n")

# Check each pair: does the "correct" MC go against VWAP?
correct_vwap_counter = 0
correct_vwap_with = 0
for _, row in df.iterrows():
    if row['first_correct']:
        is_match = (row['first_dir'] == 'bull' and row['first_vwap'] == 'above') or \
                   (row['first_dir'] == 'bear' and row['first_vwap'] == 'below')
        if is_match:
            correct_vwap_with += 1
        else:
            correct_vwap_counter += 1
    else:
        is_match = (row['second_dir'] == 'bull' and row['second_vwap'] == 'above') or \
                   (row['second_dir'] == 'bear' and row['second_vwap'] == 'below')
        if is_match:
            correct_vwap_with += 1
        else:
            correct_vwap_counter += 1

report.append(f"**Correct MC aligns WITH VWAP:** {correct_vwap_with}/{len(df)} ({correct_vwap_with/len(df)*100:.0f}%)")
report.append(f"**Correct MC goes AGAINST VWAP:** {correct_vwap_counter}/{len(df)} ({correct_vwap_counter/len(df)*100:.0f}%)\n")

# Same for EMA
correct_ema_match = 0
correct_ema_counter = 0
for _, row in df.iterrows():
    if row['first_correct']:
        is_match = (row['first_dir'] == 'bull' and row['first_ema'] == 'bull') or \
                   (row['first_dir'] == 'bear' and row['first_ema'] == 'bear')
        if is_match:
            correct_ema_match += 1
        else:
            correct_ema_counter += 1
    else:
        is_match = (row['second_dir'] == 'bull' and row['second_ema'] == 'bull') or \
                   (row['second_dir'] == 'bear' and row['second_ema'] == 'bear')
        if is_match:
            correct_ema_match += 1
        else:
            correct_ema_counter += 1

report.append(f"**Correct MC aligns WITH EMA:** {correct_ema_match}/{len(df)} ({correct_ema_match/len(df)*100:.0f}%)")
report.append(f"**Correct MC goes AGAINST EMA:** {correct_ema_counter}/{len(df)} ({correct_ema_counter/len(df)*100:.0f}%)\n")

# VWAP by symbol
report.append("### VWAP Counter-Trend by Symbol\n")
report.append("| Symbol | Correct is counter-VWAP | n |")
report.append("|--------|------------------------|---|")
for sym in sorted(df['symbol'].unique()):
    sub = df[df['symbol'] == sym]
    counter = 0
    for _, row in sub.iterrows():
        if row['first_correct']:
            is_match = (row['first_dir'] == 'bull' and row['first_vwap'] == 'above') or \
                       (row['first_dir'] == 'bear' and row['first_vwap'] == 'below')
        else:
            is_match = (row['second_dir'] == 'bull' and row['second_vwap'] == 'above') or \
                       (row['second_dir'] == 'bear' and row['second_vwap'] == 'below')
        if not is_match:
            counter += 1
    report.append(f"| {sym} | {counter}/{len(sub)} ({counter/len(sub)*100:.0f}%) | {len(sub)} |")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7: "Wait and Confirm" Strategies
# ═══════════════════════════════════════════════════════════════════════════════
report.append("\n---\n## Section 7: Wait-and-Confirm Strategies\n")
report.append("Instead of picking at signal time, what if we WAIT for confirmation?\n")

# Strategy: Suppress both MCs at open. Wait for CONF on either. Pick the one that gets CONF.
# This is testing: does CONF pick the right one?
conf_picks_correct = 0
conf_picks_wrong = 0
conf_both = 0
conf_neither = 0

for _, row in df.iterrows():
    first_has_conf = row['first_conf'] in ['star', 'pass']
    second_has_conf = row['second_conf'] in ['star', 'pass']

    if first_has_conf and not second_has_conf:
        if row['first_correct']:
            conf_picks_correct += 1
        else:
            conf_picks_wrong += 1
    elif second_has_conf and not first_has_conf:
        if row['second_correct']:
            conf_picks_correct += 1
        else:
            conf_picks_wrong += 1
    elif first_has_conf and second_has_conf:
        conf_both += 1
    else:
        conf_neither += 1

total_conf_decided = conf_picks_correct + conf_picks_wrong
report.append(f"**Wait for CONF (pass+) on one side only:**")
report.append(f"- Decided: {total_conf_decided} pairs")
report.append(f"- Correct: {conf_picks_correct}/{total_conf_decided} ({conf_picks_correct/total_conf_decided*100:.0f}%)" if total_conf_decided > 0 else "- No decisions")
report.append(f"- Both got CONF: {conf_both} (undecided)")
report.append(f"- Neither got CONF: {conf_neither} (undecided)")
report.append(f"- Total coverage: {total_conf_decided}/{len(df)} ({total_conf_decided/len(df)*100:.0f}%)\n")

# Strategy: CONF star only (stricter)
star_picks_correct = 0
star_picks_wrong = 0
star_both = 0
star_neither = 0

for _, row in df.iterrows():
    first_star = row['first_conf'] == 'star'
    second_star = row['second_conf'] == 'star'

    if first_star and not second_star:
        if row['first_correct']:
            star_picks_correct += 1
        else:
            star_picks_wrong += 1
    elif second_star and not first_star:
        if row['second_correct']:
            star_picks_correct += 1
        else:
            star_picks_wrong += 1
    elif first_star and second_star:
        star_both += 1
    else:
        star_neither += 1

total_star_decided = star_picks_correct + star_picks_wrong
report.append(f"**Wait for CONF star on one side only:**")
report.append(f"- Decided: {total_star_decided} pairs")
report.append(f"- Correct: {star_picks_correct}/{total_star_decided} ({star_picks_correct/total_star_decided*100:.0f}%)" if total_star_decided > 0 else "- No decisions")
report.append(f"- Both got star: {star_both}")
report.append(f"- Neither got star: {star_neither}")
report.append(f"- Total coverage: {total_star_decided}/{len(df)} ({total_star_decided/len(df)*100:.0f}%)\n")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8: EMA Cross After First MC
# ═══════════════════════════════════════════════════════════════════════════════
report.append("\n---\n## Section 8: EMA State Between First and Second MC\n")

# Check if EMA state changes between first and second MC
ema_same = (df['first_ema'] == df['second_ema']).sum()
ema_changed = (df['first_ema'] != df['second_ema']).sum()
report.append(f"**EMA same on both signals:** {ema_same}/{len(df)} ({ema_same/len(df)*100:.0f}%)")
report.append(f"**EMA changed between signals:** {ema_changed}/{len(df)} ({ema_changed/len(df)*100:.0f}%)\n")

# When EMA changes, is second more reliable?
if ema_changed > 0:
    sub = df[df['first_ema'] != df['second_ema']]
    second_right = sub['second_correct'].sum()
    report.append(f"When EMA changes -> second correct: {second_right}/{len(sub)} ({second_right/len(sub)*100:.0f}%)")

# When EMA is same, does direction alignment matter?
sub = df[df['first_ema'] == df['second_ema']]
# In this case, one MC matches EMA and the other doesn't
# The one that matches EMA — is it correct?
ema_side_correct = 0
for _, row in sub.iterrows():
    if row['first_ema'] == row['first_dir']:
        # First matches EMA
        if row['first_correct']:
            ema_side_correct += 1
    else:
        # Second matches EMA (since EMA is same and directions are opposite)
        if row['second_correct']:
            ema_side_correct += 1
report.append(f"When EMA stable, EMA-aligned MC correct: {ema_side_correct}/{len(sub)} ({ema_side_correct/len(sub)*100:.0f}%)\n")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 9: Symbol-Specific Patterns
# ═══════════════════════════════════════════════════════════════════════════════
report.append("\n---\n## Section 9: Symbol-Specific Patterns\n")

report.append("| Symbol | n | 1st correct | 2nd correct | VWAP counter correct | EMA match correct |")
report.append("|--------|---|-------------|-------------|---------------------|-------------------|")
for sym in sorted(df['symbol'].unique()):
    sub = df[df['symbol'] == sym]
    n = len(sub)
    first_right = sub['first_correct'].sum()
    second_right = sub['second_correct'].sum()

    # VWAP counter = pick the one NOT matching VWAP
    vwap_counter_correct = 0
    ema_match_correct = 0
    vwap_decidable = 0
    ema_decidable = 0
    for _, row in sub.iterrows():
        f_vwap = (row['first_dir'] == 'bull' and row['first_vwap'] == 'above') or \
                 (row['first_dir'] == 'bear' and row['first_vwap'] == 'below')
        s_vwap = (row['second_dir'] == 'bull' and row['second_vwap'] == 'above') or \
                 (row['second_dir'] == 'bear' and row['second_vwap'] == 'below')

        # Counter-VWAP: pick the one NOT matching
        if f_vwap and not s_vwap:
            vwap_decidable += 1
            if row['second_correct']: vwap_counter_correct += 1
        elif s_vwap and not f_vwap:
            vwap_decidable += 1
            if row['first_correct']: vwap_counter_correct += 1

        f_ema = (row['first_dir'] == 'bull' and row['first_ema'] == 'bull') or \
                (row['first_dir'] == 'bear' and row['first_ema'] == 'bear')
        s_ema = (row['second_dir'] == 'bull' and row['second_ema'] == 'bull') or \
                (row['second_dir'] == 'bear' and row['second_ema'] == 'bear')
        if f_ema and not s_ema:
            ema_decidable += 1
            if row['first_correct']: ema_match_correct += 1
        elif s_ema and not f_ema:
            ema_decidable += 1
            if row['second_correct']: ema_match_correct += 1

    vwap_pct = f"{vwap_counter_correct}/{vwap_decidable} ({vwap_counter_correct/vwap_decidable*100:.0f}%)" if vwap_decidable > 0 else "n/a"
    ema_pct = f"{ema_match_correct}/{ema_decidable} ({ema_match_correct/ema_decidable*100:.0f}%)" if ema_decidable > 0 else "n/a"

    report.append(f"| {sym} | {n} | {first_right}/{n} ({first_right/n*100:.0f}%) | {second_right}/{n} ({second_right/n*100:.0f}%) | {vwap_pct} | {ema_pct} |")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 10: Solo MC Signals (no opposing pair)
# ═══════════════════════════════════════════════════════════════════════════════
report.append("\n---\n## Section 10: Solo MC Signals (no opposing pair)\n")

# Find days with only one MC direction
solo_data = []
all_mc_grouped = mc.groupby(['symbol', 'date'])
for (sym, date), grp in all_mc_grouped:
    dirs = grp['direction'].unique()
    if len(dirs) == 1:
        solo_data.append({
            'symbol': sym, 'date': date,
            'direction': dirs[0], 'time': grp.iloc[0]['time'],
            'vol': grp.iloc[0]['vol'], 'ramp': grp.iloc[0]['ramp'],
        })

solo = pd.DataFrame(solo_data)
report.append(f"**Solo MC signals (only one direction):** {len(solo)}")
report.append(f"**Opposing pair days:** {len(df)}")
report.append(f"**Total MC days:** {len(solo) + len(df)}\n")

# Solo MC by time
if len(solo) > 0:
    report.append("Solo MC time distribution:")
    report.append(str(solo['time'].value_counts().sort_index().to_string()))
    report.append("")

# Check solo MC against CONF
solo_with_conf = []
for _, s in solo.iterrows():
    day_conf = conf_mc[(conf_mc['symbol'] == s['symbol']) & (conf_mc['date'] == s['date']) &
                       (conf_mc['direction'] == s['direction'])]
    if len(day_conf) > 0:
        solo_with_conf.append({
            **s.to_dict(),
            'conf': day_conf.iloc[0]['conf_result']
        })

if len(solo_with_conf) > 0:
    sc = pd.DataFrame(solo_with_conf)
    report.append(f"Solo MC CONF results: {sc['conf'].value_counts().to_dict()}")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 11: Comprehensive Smart Filter Candidates
# ═══════════════════════════════════════════════════════════════════════════════
report.append("\n---\n## Section 11: Smart Filter Candidates (Ranked)\n")
report.append("Filters that beat the 45% baseline AND have reasonable coverage (n >= 20).\n")

all_results = results + results2 + results5
qualified = [r for r in all_results if r['accuracy'] > 50 and r['n'] >= 20]
qualified.sort(key=lambda x: (x['accuracy'], x['n']), reverse=True)

report.append("| Rank | Filter | n | Accuracy | vs baseline |")
report.append("|------|--------|---|----------|-------------|")
for i, r in enumerate(qualified, 1):
    report.append(f"| {i} | {r['name']} | {r['n']} | **{r['accuracy']}%** | +{r['vs_baseline']}% |")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 12: Recommendation
# ═══════════════════════════════════════════════════════════════════════════════
report.append("\n---\n## Section 12: Conclusion & Recommendation\n")

# Find the best practical filter
best = qualified[0] if qualified else None
if best:
    report.append(f"**Best single filter:** {best['name']} — {best['accuracy']}% on n={best['n']}")
else:
    report.append("**No filter significantly beat the baseline.**")

report.append("")
report.append("### Comparison vs 9:50 Time Gate")
report.append("- **9:50 time gate:** 79% accuracy (n=126) — simple, reliable")
report.append("- The question is whether any smart filter can approach 79% without losing the 9:30-9:50 window entirely.\n")

# Final verdict
if best and best['accuracy'] >= 65:
    report.append("### Verdict: SMART FILTER WORTH TESTING")
    report.append(f"The `{best['name']}` filter achieves {best['accuracy']}% accuracy on {best['n']} pairs.")
    report.append("This is meaningfully better than the 45% coin flip and could preserve MC signals during the open window.")
    report.append("\n**Implementation:** Instead of blanket-suppressing MC before 9:50, apply this filter to the 9:30-9:50 window.")
else:
    report.append("### Verdict: 9:50 TIME GATE REMAINS BEST")
    report.append("No feature or combination reliably distinguishes correct from wrong MC at the open.")
    report.append("The opening auction is genuinely noisy — all indicators (VWAP, EMA, ADX, volume, ramp) are unreliable during this window.")
    report.append("The 9:50 time gate (79% accuracy) remains the simplest and most effective solution.")

# Write report
with open('debug/v28b-mc-smart-filter.md', 'w') as f:
    f.write('\n'.join(report))

print("Report written to debug/v28b-mc-smart-filter.md")
print(f"\n=== TOP FILTERS ===")
for r in qualified[:10]:
    print(f"  {r['accuracy']}% (n={r['n']}) — {r['name']}")
