#!/usr/bin/env python3
"""
Practical implementation analysis:
In Pine Script, we can't compare two MCs side-by-side easily.
We need filters that work on a SINGLE MC signal at the moment it fires.

Key question: Can we suppress the FIRST MC and only take the SECOND?
Or can we evaluate each MC independently?
"""
import pandas as pd
import numpy as np

signals = pd.read_csv('debug/v28a-signals.csv')
pairs = pd.read_csv('debug/v28a-mc-opposing-pairs.csv')
mc = signals[signals['line_type'] == 'MC'].copy()
mc['dt'] = pd.to_datetime(mc['datetime'], utc=True)
mc['date'] = mc['dt'].dt.date.astype(str)
conf_mc = signals[(signals['line_type'] == 'CONF') & (signals['conf_source'] == 'QBS/MC')].copy()
conf_mc['dt'] = pd.to_datetime(conf_mc['datetime'], utc=True)
conf_mc['date'] = conf_mc['dt'].dt.date.astype(str)

# Enrich pairs with full signal features
enriched = []
for _, p in pairs.iterrows():
    sym, date = p['symbol'], p['date']
    day_mc = mc[(mc['symbol'] == sym) & (mc['date'] == date)]
    first_mc = day_mc[(day_mc['direction'] == p['first_dir']) & (day_mc['time'] == p['first_time'])]
    second_mc = day_mc[(day_mc['direction'] == p['second_dir']) & (day_mc['time'] == p['second_time'])]
    if len(first_mc) == 0 or len(second_mc) == 0: continue
    f, s = first_mc.iloc[0], second_mc.iloc[0]
    day_conf = conf_mc[(conf_mc['symbol'] == sym) & (conf_mc['date'] == date)]
    fc = day_conf[day_conf['direction'] == p['first_dir']]
    sc = day_conf[day_conf['direction'] == p['second_dir']]
    enriched.append({
        'first_correct': p['first_correct'], 'second_correct': p['second_correct'],
        'first_dir': p['first_dir'], 'second_dir': p['second_dir'],
        'first_time': p['first_time'], 'second_time': p['second_time'],
        'first_vwap': f['vwap'], 'second_vwap': s['vwap'],
        'first_ema': f['ema'], 'second_ema': s['ema'],
        'first_vol': f['vol'], 'second_vol': s['vol'],
        'first_ramp': f['ramp'], 'second_ramp': s['ramp'],
        'first_body': f['body'], 'second_body': s['body'],
        'first_adx': f['adx'], 'second_adx': s['adx'],
        'first_close_pos': f['close_pos'], 'second_close_pos': s['close_pos'],
        'first_range_atr': f['range_atr'], 'second_range_atr': s['range_atr'],
        'first_conf': fc.iloc[0]['conf_result'] if len(fc) > 0 else 'none',
        'second_conf': sc.iloc[0]['conf_result'] if len(sc) > 0 else 'none',
        'symbol': sym, 'date': date,
    })
df = pd.DataFrame(enriched)

def dir_matches_vwap(d, v):
    return (d == 'bull' and v == 'above') or (d == 'bear' and v == 'below')

def dir_matches_ema(d, e):
    return d == e  # both are 'bull' or 'bear'

print("=" * 70)
print("PRACTICAL MC FILTER ANALYSIS")
print("=" * 70)

# ═══════════════════════════════════════════════════════════════════════════
# APPROACH 1: "Skip First MC, Always Take Second"
# ═══════════════════════════════════════════════════════════════════════════
print("\n=== APPROACH 1: Skip first MC, take second ===")
print(f"Second correct: {df['second_correct'].sum()}/126 ({df['second_correct'].mean()*100:.0f}%)")
print("Simple but only 55% — not great.\n")

# ═══════════════════════════════════════════════════════════════════════════
# APPROACH 2: Single MC filter — evaluate each MC independently
# ═══════════════════════════════════════════════════════════════════════════
print("=== APPROACH 2: Single MC filters (applied to each MC independently) ===")
print("Test: does a feature at the MC bar itself predict whether it's correct?\n")

# Stack all MCs (first and second) into a flat list with correct/wrong label
flat_mcs = []
for _, row in df.iterrows():
    flat_mcs.append({
        'is_first': True, 'correct': row['first_correct'],
        'dir': row['first_dir'], 'vwap': row['first_vwap'],
        'ema': row['first_ema'], 'vol': row['first_vol'],
        'ramp': row['first_ramp'], 'body': row['first_body'],
        'adx': row['first_adx'], 'close_pos': row['first_close_pos'],
        'range_atr': row['first_range_atr'], 'conf': row['first_conf'],
        'time': row['first_time'], 'symbol': row['symbol'],
    })
    flat_mcs.append({
        'is_first': False, 'correct': row['second_correct'],
        'dir': row['second_dir'], 'vwap': row['second_vwap'],
        'ema': row['second_ema'], 'vol': row['second_vol'],
        'ramp': row['second_ramp'], 'body': row['second_body'],
        'adx': row['second_adx'], 'close_pos': row['second_close_pos'],
        'range_atr': row['second_range_atr'], 'conf': row['second_conf'],
        'time': row['time' if 'time' in row.index else 'first_time'],
    })

fmc = pd.DataFrame(flat_mcs)
fmc['vwap_match'] = fmc.apply(lambda r: dir_matches_vwap(r['dir'], r['vwap']), axis=1)
fmc['ema_match'] = fmc.apply(lambda r: dir_matches_ema(r['dir'], r['ema']), axis=1)

print(f"Total flat MC signals: {len(fmc)}")
print(f"Correct: {fmc['correct'].sum()}/{len(fmc)} ({fmc['correct'].mean()*100:.0f}%) — 50% by construction")
print()

# For each feature, compute accuracy when a condition holds
tests = [
    ("VWAP match (with-trend)", fmc['vwap_match']),
    ("VWAP counter (against-trend)", ~fmc['vwap_match']),
    ("EMA match", fmc['ema_match']),
    ("EMA counter", ~fmc['ema_match']),
    ("Vol >= 10", fmc['vol'] >= 10),
    ("Vol < 10", fmc['vol'] < 10),
    ("Vol < 5", fmc['vol'] < 5),
    ("Ramp >= 30", fmc['ramp'] >= 30),
    ("Ramp < 30", fmc['ramp'] < 30),
    ("Body >= 70", fmc['body'] >= 70),
    ("Body < 50", fmc['body'] < 50),
    ("ADX >= 30", fmc['adx'] >= 30),
    ("ADX < 25", fmc['adx'] < 25),
    ("Close_pos >= 90", fmc['close_pos'] >= 90),
    ("Close_pos < 70", fmc['close_pos'] < 70),
    ("Range ATR >= 3", fmc['range_atr'] >= 3),
    ("Range ATR < 2", fmc['range_atr'] < 2),
    ("Is first signal", fmc['is_first']),
    ("Is second signal", ~fmc['is_first']),
    ("CONF star", fmc['conf'] == 'star'),
    ("CONF pass+", fmc['conf'].isin(['star', 'pass'])),
    ("CONF fail", fmc['conf'] == 'fail'),
    ("Time 9:35", fmc['time'] == '9:35'),
    ("Time 9:40", fmc['time'] == '9:40'),
    ("Time 9:45", fmc['time'] == '9:45'),
]

print(f"{'Filter':<35} {'n':>5} {'correct':>8} {'accuracy':>9} {'vs 50%':>8}")
print("-" * 70)
for name, mask in sorted(tests, key=lambda x: x[1].sum(), reverse=True):
    sub = fmc[mask]
    n = len(sub)
    if n == 0: continue
    correct = sub['correct'].sum()
    acc = correct / n * 100
    marker = " ***" if acc >= 55 and n >= 30 else ""
    print(f"  {name:<33} {n:>5} {correct:>8} {acc:>8.0f}% {acc-50:>+7.1f}%{marker}")

# ═══════════════════════════════════════════════════════════════════════════
# APPROACH 3: "Suppress MC when VWAP-aligned" (single signal filter)
# ═══════════════════════════════════════════════════════════════════════════
print("\n\n=== APPROACH 3: Suppress VWAP-aligned MC at open ===")
print("Rule: If MC direction matches VWAP at the time of the signal, SKIP it.")
print("Rationale: The with-VWAP MC is the 'trap' signal.\n")

# At the open: first MC tends to be VWAP-aligned (79% of same-VWAP cases)
# If we suppress VWAP-aligned MCs, we suppress most first MCs and let through counter-VWAP MCs
# This is a single-signal filter — no comparison needed

# Apply to flat MCs
vwap_aligned = fmc[fmc['vwap_match']]
vwap_counter = fmc[~fmc['vwap_match']]

print(f"VWAP-aligned MCs: {len(vwap_aligned)}")
print(f"  Correct: {vwap_aligned['correct'].sum()}/{len(vwap_aligned)} ({vwap_aligned['correct'].mean()*100:.0f}%)")
print(f"VWAP-counter MCs: {len(vwap_counter)}")
print(f"  Correct: {vwap_counter['correct'].sum()}/{len(vwap_counter)} ({vwap_counter['correct'].mean()*100:.0f}%)")
print()

# But on opposing pair days, both MCs fire.
# If we suppress VWAP-aligned: what happens per pair?
print("Per-pair outcome of 'suppress VWAP-aligned' rule:")
both_suppressed = 0
both_allowed = 0
one_allowed = 0
one_allowed_correct = 0

for _, row in df.iterrows():
    f_vwap = dir_matches_vwap(row['first_dir'], row['first_vwap'])
    s_vwap = dir_matches_vwap(row['second_dir'], row['second_vwap'])
    f_allowed = not f_vwap
    s_allowed = not s_vwap

    if f_allowed and s_allowed:
        both_allowed += 1
    elif not f_allowed and not s_allowed:
        both_suppressed += 1
    else:
        one_allowed += 1
        if f_allowed and row['first_correct']:
            one_allowed_correct += 1
        elif s_allowed and row['second_correct']:
            one_allowed_correct += 1

print(f"  Both suppressed: {both_suppressed} (VWAP flipped, both match)")
print(f"  Both allowed: {both_allowed} (VWAP flipped, neither matches)")
print(f"  Exactly one allowed: {one_allowed}")
if one_allowed > 0:
    print(f"    Correct: {one_allowed_correct}/{one_allowed} ({one_allowed_correct/one_allowed*100:.0f}%)")
print()

# ═══════════════════════════════════════════════════════════════════════════
# APPROACH 4: Combined single-signal filters
# ═══════════════════════════════════════════════════════════════════════════
print("=== APPROACH 4: Combined single-signal suppression filters ===")
print("Suppress MC if it matches certain 'trap' characteristics.\n")

# A trap MC = with-VWAP + high volume + is first signal
combos = [
    ("VWAP-aligned + Vol >= 10", fmc['vwap_match'] & (fmc['vol'] >= 10)),
    ("VWAP-aligned + is_first", fmc['vwap_match'] & fmc['is_first']),
    ("VWAP-aligned + Vol >= 10 + is_first", fmc['vwap_match'] & (fmc['vol'] >= 10) & fmc['is_first']),
    ("Vol >= 12 + is_first", (fmc['vol'] >= 12) & fmc['is_first']),
    ("VWAP-aligned + range_atr >= 3", fmc['vwap_match'] & (fmc['range_atr'] >= 3)),
    ("is_first + range_atr >= 3", fmc['is_first'] & (fmc['range_atr'] >= 3)),
    ("VWAP-aligned + body < 60", fmc['vwap_match'] & (fmc['body'] < 60)),
]

for name, suppress_mask in combos:
    suppressed = fmc[suppress_mask]
    allowed = fmc[~suppress_mask]
    n_suppress = len(suppressed)
    n_allow = len(allowed)
    suppress_correct = suppressed['correct'].sum()
    allow_correct = allowed['correct'].sum()
    # Good filter: suppressed MCs are mostly WRONG, allowed MCs are mostly RIGHT
    print(f"  {name}:")
    print(f"    Suppressed: {n_suppress} MCs ({suppress_correct}/{n_suppress} = {suppress_correct/n_suppress*100:.0f}% correct — should be LOW)")
    print(f"    Allowed: {n_allow} MCs ({allow_correct}/{n_allow} = {allow_correct/n_allow*100:.0f}% correct — should be HIGH)")
    print()

# ═══════════════════════════════════════════════════════════════════════════
# APPROACH 5: "Don't suppress — delay and confirm"
# ═══════════════════════════════════════════════════════════════════════════
print("=== APPROACH 5: Don't suppress, but DELAY ===")
print("When first MC fires at open, don't count it immediately.")
print("Wait N bars. If no opposing MC fires, take it. If opposing fires, evaluate.\n")

# Check: on opposing-pair days, what's the gap?
def time_to_min(t):
    h, m = t.split(':')
    return int(h) * 60 + int(m)

df['time_gap'] = df.apply(lambda r: time_to_min(r['second_time']) - time_to_min(r['first_time']), axis=1)
print(f"Time gap distribution:")
print(f"  5 min: {(df['time_gap'] == 5).sum()} pairs")
print(f"  10 min: {(df['time_gap'] == 10).sum()} pairs")
print(f"  15 min: {(df['time_gap'] == 15).sum()} pairs (second at 9:45)")
print()

# If we wait 10 min after first MC:
# - 5min gap pairs: opposing fires at 5min, we see both => need to decide
# - 10min gap pairs: opposing fires exactly at 10min => we see both
# All opposing pairs happen within 15min
# So waiting 15 min = we always see both or know it's solo
print("After 15 min wait:")
print(f"  If no opposing: it's a solo MC day (531 days) -> take it")
print(f"  If opposing fired: 126 pairs -> need smart filter or 9:50 gate")
print()

# ═══════════════════════════════════════════════════════════════════════════
# APPROACH 6: Radical — suppress MC at open, use it only as CONF source
# ═══════════════════════════════════════════════════════════════════════════
print("=== APPROACH 6: MC as confirmation only (not signal) at open ===")
print("Don't use MC as a standalone signal before 9:50.")
print("Instead, MC before 9:50 counts as volume confirmation for BRK/REV signals.")
print("MC after 9:50 works normally.\n")

# Check: how many MC-only trades (MC confirmed but no BRK/REV) are before 9:50?
tr = pd.read_csv('debug/v28a-trades.csv')
tr['t_min'] = tr['time'].apply(time_to_min)
tr_mc = tr[tr['conf_source'].str.contains('MC', na=False)].copy()
early_mc = tr_mc[tr_mc['t_min'] < time_to_min('9:50')]
late_mc = tr_mc[tr_mc['t_min'] >= time_to_min('9:50')]

print(f"MC-conf trades before 9:50: {len(early_mc)}")
print(f"  Win rate: {(early_mc['pnl_atr'] > 0).mean()*100:.0f}%")
print(f"  Mean PnL/ATR: {early_mc['pnl_atr'].mean():.3f}")
print(f"MC-conf trades 9:50+: {len(late_mc)}")
print(f"  Win rate: {(late_mc['pnl_atr'] > 0).mean()*100:.0f}%")
print(f"  Mean PnL/ATR: {late_mc['pnl_atr'].mean():.3f}")
print()

# Check if MC+BRK vs MC-only at open differs
early_brk_mc = early_mc[early_mc['conf_source'] == 'QBS/MC']
print(f"Early QBS/MC trades: {len(early_brk_mc)}")
print(f"  Win rate: {(early_brk_mc['pnl_atr'] > 0).mean()*100:.0f}%")
print(f"  Mean PnL/ATR: {early_brk_mc['pnl_atr'].mean():.3f}")

# ═══════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("FINAL SUMMARY: PRACTICAL MC FILTER OPTIONS")
print("=" * 70)
print()
print("Option A: 9:50 TIME GATE (current proposal)")
print("  - Suppress all MC before 9:50")
print("  - Accuracy after 9:50: 79%")
print("  - Loses: all early MC signals (126 opposing + some solos)")
print("  - Simplicity: trivial to implement")
print()
print("Option B: COUNTER-VWAP FILTER (smart)")
print("  - At open: if MC dir matches VWAP -> suppress (it's the trap)")
print("  - If MC dir opposes VWAP -> take it (counter-trend reversal)")
print("  - Accuracy on exclusive pairs: 61.5% (n=52)")
print("  - Problem: 70/126 pairs both MCs match VWAP (VWAP flipped)")
print("  - Single-signal implementable: YES (just check dir vs VWAP at signal time)")
print()
print("Option C: HYBRID (Counter-VWAP + 9:50 gate fallback)")
print("  - At open: suppress VWAP-aligned MC, take counter-VWAP MC")
print("  - If BOTH got suppressed or both allowed: wait for 9:50")
print("  - Expected accuracy: ~72%")
print("  - More complex to implement")
print()
print("Option D: VOLUME THRESHOLD")
print("  - Suppress MC with vol >= 12 before 9:50 (the opening explosion)")
print("  - These are mostly wrong first signals")
print("  - Allows lower-vol reversal MCs through")
print()
print("RECOMMENDATION: Option A (9:50 gate) remains best.")
print("  61.5% counter-VWAP is better than 45% coin flip,")
print("  but far worse than 79% at 9:50.")
print("  The added complexity is not worth +16% over baseline")
print("  when a simple time gate gives +34% over baseline.")
