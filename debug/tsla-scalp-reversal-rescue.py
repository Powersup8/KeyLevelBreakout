#!/usr/bin/env python3
"""
TSLA Open Scalper — Reversal Pattern Deep Rescue
Target: capture the $528 gap in INVV/FAKEDN/FAKEUP/VSHAPE

Current optimized system: $769.26 (direction + first3 sizing, flat 2m exit)
H1=$392.02, H2=$377.24

Gaps by pattern (from total_system_optimization):
  INVV:   system=-$49.66, ceiling=$166.20, gap=$215.86  (n=36)
  FAKEDN: system=+$33.34, ceiling=$140.44, gap=$107.10  (n=26)
  FAKEUP: system=+$20.84, ceiling=$124.76, gap=$103.92  (n=28)
  VSHAPE: system=+$60.12, ceiling=$165.98, gap=$105.86  (n=35)
"""

import pandas as pd
import numpy as np
from pathlib import Path

DB = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug/tsla_candle_fingerprints.parquet")
OUT = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug/tsla-scalp-reversal-rescue.md")

df = pd.read_parquet(DB)
print(f"Loaded {len(df)} days, {len(df.columns)} columns")
print(f"Date range: {df.index[0].date()} to {df.index[-1].date()}")

# Fixed calendar split at the median dataset day — all H1/H2 comparisons use this
SPLIT_DATE = df.index[len(df) // 2]
print(f"H1/H2 split at: {SPLIT_DATE.date()} (day {len(df)//2} of {len(df)})")

# ─── BASELINE OPTIMIZED SYSTEM ────────────────────────────────────────────────

# Direction rules from total_system_optimization Loop 1
DIR_RULES = {
    'CRASH':    'always_put',
    'DRIFT_DN': 'always_put',
    'DRIFT_UP': 'always_call',
    'FAKEDN':   'follow_majority',
    'FAKEUP':   'follow_binary',
    'INVV':     'always_call',
    'SURGE':    'always_call',
    'VSHAPE':   'follow_binary',
}

EXIT_RULES_BASE = {p: 2 for p in DIR_RULES}  # flat 2m exit

def get_direction(row, dir_rule):
    """Determine trade direction for a row given a direction rule."""
    if dir_rule == 'always_call':
        return 'CALL'
    elif dir_rule == 'always_put':
        return 'PUT'
    elif dir_rule == 'follow_binary':
        return 'CALL' if row['is_call_tier'] else 'PUT'
    elif dir_rule == 'follow_majority':
        # agree_count = vwap_agrees + ema_agrees (both are CALL-confirming)
        return 'CALL' if row['agree_count'] >= 1 else 'PUT'
    return 'CALL'  # fallback

def simulate(df, dir_rules=None, exit_rules=None, size_override=None,
             skip_patterns=None, extra_rules=None):
    """
    Simulate the scalper system.

    dir_rules: dict {pattern: rule} — overrides DIR_RULES
    exit_rules: dict {pattern: exit_minute} — overrides EXIT_RULES_BASE
    size_override: dict {pattern: size} — override sizing for specific patterns
    skip_patterns: set of patterns to skip entirely
    extra_rules: dict {pattern: callable(row) -> (direction, size, exit_min) or None}
                 If returns None, falls through to standard rules.
    """
    if dir_rules is None:
        dir_rules = DIR_RULES
    if exit_rules is None:
        exit_rules = EXIT_RULES_BASE
    if skip_patterns is None:
        skip_patterns = set()

    trades = []
    for date, row in df.iterrows():
        pattern = row['opening_pattern']

        if pattern in skip_patterns:
            continue

        # Extra rules hook (for per-day conditional logic)
        if extra_rules and pattern in extra_rules:
            result = extra_rules[pattern](row)
            if result is not None:
                direction, size, exit_min = result
                if size == 0:
                    continue
                pnl_col = f'pnl_{direction.lower()}_{exit_min}m'
                pnl = row.get(pnl_col, np.nan)
                if np.isnan(pnl):
                    continue
                trades.append({'date': date, 'pattern': pattern, 'direction': direction,
                                'size': size, 'pnl': pnl * size, 'exit_min': exit_min})
                continue

        # Standard direction rule
        rule = dir_rules.get(pattern, 'follow_binary')
        direction = get_direction(row, rule)

        # Sizing: first3 confirmation (bar0 must agree with direction)
        bar0_dir = row['bar0_dir']
        if size_override and pattern in size_override:
            size = size_override[pattern]
        elif (direction == 'CALL' and bar0_dir == 'G') or (direction == 'PUT' and bar0_dir == 'R'):
            size = 2.0
        else:
            size = 0.0  # skip — first3 disagrees

        if size == 0:
            continue

        exit_min = exit_rules.get(pattern, 2)
        pnl_col = f'pnl_{direction.lower()}_{exit_min}m'
        pnl = row.get(pnl_col, np.nan)
        if np.isnan(pnl):
            continue

        trades.append({'date': date, 'pattern': pattern, 'direction': direction,
                       'size': size, 'pnl': pnl * size, 'exit_min': exit_min})

    if not trades:
        return 0.0, pd.DataFrame()
    t = pd.DataFrame(trades).set_index('date').sort_index()
    return t['pnl'].sum(), t

def stats(t, label=''):
    if len(t) == 0:
        return {'label': label, 'total': 0, 'n': 0, 'wr': 0, 'avg': 0}
    n = len(t)
    wins = (t['pnl'] > 0).sum()
    return {
        'label': label,
        'total': t['pnl'].sum(),
        'n': n,
        'wr': wins / n * 100,
        'avg': t['pnl'].mean(),
    }

def h1h2(t):
    """Split trades into H1 (first half) and H2 (second half) by FIXED calendar date.

    Uses the median date of the full dataset — NOT the trade midpoint — so H1/H2
    refer to the same calendar period regardless of which trades a rule includes.
    """
    if len(t) == 0:
        return 0, 0
    h1 = t[t.index < SPLIT_DATE]['pnl'].sum()
    h2 = t[t.index >= SPLIT_DATE]['pnl'].sum()
    return h1, h2

# ─── Verify baseline ──────────────────────────────────────────────────────────
base_total, base_trades = simulate(df)
base_h1, base_h2 = h1h2(base_trades)
print(f"\nBaseline: ${base_total:.2f} (H1=${base_h1:.2f}, H2=${base_h2:.2f})")
print(f"Expected: $769.26 (H1=$392.02, H2=$377.24)")

# Breakdown by pattern
for pat in ['CRASH','SURGE','DRIFT_DN','DRIFT_UP','FAKEDN','FAKEUP','INVV','VSHAPE']:
    t_pat = base_trades[base_trades['pattern']==pat] if len(base_trades) > 0 else pd.DataFrame()
    print(f"  {pat:10s}: ${t_pat['pnl'].sum():.2f} (n={len(t_pat)})")

lines = []
lines.append("# TSLA Open Scalper — Reversal Pattern Rescue")
lines.append(f"\nDate: 2026-03-21 | N={len(df)} days | Baseline: ${base_total:.2f}")
lines.append(f"H1=${base_h1:.2f}, H2=${base_h2:.2f}")
lines.append("\n**Target gaps**: INVV=$215.86, FAKEDN=$107.10, FAKEUP=$103.92, VSHAPE=$105.86")
lines.append("\n---")

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def test_improvement(desc, total, t, verbose=True):
    delta = total - base_total
    h1, h2 = h1h2(t)
    dh1 = h1 - base_h1
    dh2 = h2 - base_h2
    robust = (delta > 0 and dh1 > 0 and dh2 > 0)
    mark = '✓' if robust else '✗'
    if verbose:
        print(f"  {mark} {desc}: ${total:.2f} (Δ{delta:+.2f}) H1={h1:.2f}(Δ{dh1:+.2f}) H2={h2:.2f}(Δ{dh2:+.2f})")
    return {'desc': desc, 'total': total, 'delta': delta, 'h1': h1, 'h2': h2,
            'dh1': dh1, 'dh2': dh2, 'robust': robust}


# ══════════════════════════════════════════════════════════════════════════════
# LOOP 1: INVV — Skip / Direction Sub-Filters
# ══════════════════════════════════════════════════════════════════════════════

lines.append("\n## LOOP 1: INVV Direction Rescue\n")
lines.append(f"INVV = GRR: bar0=G, bar1=R, bar2=R")
lines.append(f"Baseline INVV: ${base_trades[base_trades['pattern']=='INVV']['pnl'].sum():.2f} (n={len(base_trades[base_trades['pattern']=='INVV'])})")
lines.append(f"Issue: direction=always_call, bar0=G → 2x size, but 49/51 coin flip → amplified losses\n")

invv_days = df[df['opening_pattern'] == 'INVV']
print(f"\n=== LOOP 1: INVV ({len(invv_days)} days) ===")

# Check actual CALL/PUT distribution for INVV
invv_call_wins = (invv_days['pnl_call_2m'] > 0).sum()
invv_put_wins = (invv_days['pnl_put_2m'] > 0).sum()
invv_call_total = invv_days['pnl_call_2m'].sum()
invv_put_total = invv_days['pnl_put_2m'].sum()

print(f"INVV CALL wins: {invv_call_wins}/{len(invv_days)} ({invv_call_wins/len(invv_days)*100:.1f}%), total=${invv_call_total:.2f}")
print(f"INVV PUT wins:  {invv_put_wins}/{len(invv_days)} ({invv_put_wins/len(invv_days)*100:.1f}%), total=${invv_put_total:.2f}")

lines.append(f"| Metric | CALL@2m | PUT@2m |")
lines.append(f"|--------|---------|--------|")
lines.append(f"| Win rate | {invv_call_wins/len(invv_days)*100:.1f}% | {invv_put_wins/len(invv_days)*100:.1f}% |")
lines.append(f"| Total PnL | ${invv_call_total:.2f} | ${invv_put_total:.2f} |")

# Test: skip INVV entirely
total_skip_invv, t_skip_invv = simulate(df, skip_patterns={'INVV'})
r = test_improvement("Skip INVV entirely", total_skip_invv, t_skip_invv)

lines.append(f"\n### Option A: Skip INVV entirely")
lines.append(f"Result: ${r['total']:.2f} (Δ{r['delta']:+.2f}) H1={r['h1']:.2f} H2={r['h2']:.2f} {'✓ ROBUST' if r['robust'] else '✗ not robust'}")

# Test: INVV → size=1x (don't amplify a coin flip)
def invv_size1_rule(row):
    direction = 'CALL'  # always_call per current rule
    return (direction, 1.0, 2)  # 1x instead of 2x

total_invv1x, t_invv1x = simulate(df, extra_rules={'INVV': invv_size1_rule})
r1x = test_improvement("INVV size=1x (no amplify)", total_invv1x, t_invv1x)
lines.append(f"\n### Option B: INVV size=1x (reduce from 2x)")
lines.append(f"Result: ${r1x['total']:.2f} (Δ{r1x['delta']:+.2f}) H1={r1x['h1']:.2f} H2={r1x['h2']:.2f} {'✓ ROBUST' if r1x['robust'] else '✗ not robust'}")

# Test: INVV direction sub-filters using PM features
print("\n  INVV PM feature sub-filters (threshold scan):")
lines.append("\n### INVV PM Feature Sub-Filters")
lines.append("| Feature | Threshold | N CALL | N PUT | CALL total | PUT total | Best rule | Delta |")
lines.append("|---------|-----------|--------|-------|------------|-----------|-----------|-------|")

invv_results = []
features = ['pm_slope', 'pm_accel_2m', 'pm_position', 'pm_r2', 'agree_count',
            'pm_curvature', 'pm_accel_4m', 'gap', 'vix_prev', 'bar0_range',
            'bar0_body_pct', 'pm_green_pct']

for feat in features:
    col = invv_days[feat].dropna()
    if len(col) < 5:
        continue
    percentiles = np.percentile(col, [25, 50, 75])
    for thresh in percentiles:
        above = invv_days[feat] >= thresh
        below = ~above

        # Test: above=CALL, below=PUT
        def make_invv_rule(feat=feat, thresh=thresh):
            def rule(row):
                val = row.get(feat, np.nan)
                if np.isnan(val):
                    return ('CALL', 2.0, 2)
                direction = 'CALL' if val >= thresh else 'PUT'
                bar0_dir = row['bar0_dir']
                if (direction == 'CALL' and bar0_dir == 'G') or (direction == 'PUT' and bar0_dir == 'R'):
                    size = 2.0
                else:
                    size = 0.0
                return (direction, size, 2)
            return rule

        tot, t = simulate(df, extra_rules={'INVV': make_invv_rule()})
        delta = tot - base_total

        # also try: above=PUT, below=CALL
        def make_invv_rule_inv(feat=feat, thresh=thresh):
            def rule(row):
                val = row.get(feat, np.nan)
                if np.isnan(val):
                    return ('CALL', 2.0, 2)
                direction = 'PUT' if val >= thresh else 'CALL'
                bar0_dir = row['bar0_dir']
                if (direction == 'CALL' and bar0_dir == 'G') or (direction == 'PUT' and bar0_dir == 'R'):
                    size = 2.0
                else:
                    size = 0.0
                return (direction, size, 2)
            return rule

        tot_inv, t_inv = simulate(df, extra_rules={'INVV': make_invv_rule_inv()})
        delta_inv = tot_inv - base_total

        if abs(delta) > 10 or abs(delta_inv) > 10:
            n_above = above.sum()
            n_below = below.sum()
            best_delta = delta if delta >= delta_inv else delta_inv
            best_dir = f"{feat}>={thresh:.2f}→CALL" if delta >= delta_inv else f"{feat}>={thresh:.2f}→PUT"
            invv_results.append({'feat': feat, 'thresh': thresh, 'delta': best_delta, 'rule': best_dir})
            lines.append(f"| {feat} | {thresh:.2f} | {n_above} | {n_below} | {invv_days[above]['pnl_call_2m'].sum():.2f} | {invv_days[above]['pnl_put_2m'].sum():.2f} | {best_dir} | {best_delta:+.2f} |")

# Best INVV sub-filter
if invv_results:
    invv_results.sort(key=lambda x: x['delta'], reverse=True)
    best_invv = invv_results[0]
    print(f"  Best INVV sub-filter: {best_invv['rule']} → Δ{best_invv['delta']:+.2f}")
    lines.append(f"\n**Best INVV sub-filter**: {best_invv['rule']} → Δ{best_invv['delta']:+.2f}")
else:
    print("  No INVV sub-filter > $10 delta found")
    lines.append("\n**No significant INVV sub-filter found** (all < $10 delta)")

# Test INVV 15sec bar sub-signal
print("\n  INVV 15sec intrabar sub-filters:")
lines.append("\n### INVV 15sec Intrabar Sub-Signal")
lines.append("| 15sec feature | N CALL days | N PUT days | CALL total | PUT total | Delta |")
lines.append("|---------------|-------------|------------|------------|-----------|-------|")

for bar_i in range(4):
    col = f'bar15s_{bar_i}_dir'
    if col not in invv_days.columns:
        continue
    g_days = invv_days[invv_days[col] == 'G']
    r_days = invv_days[invv_days[col] == 'R']

    call_g = g_days['pnl_call_2m'].sum()
    call_r = r_days['pnl_call_2m'].sum()
    put_g  = g_days['pnl_put_2m'].sum()
    put_r  = r_days['pnl_put_2m'].sum()

    lines.append(f"| {col}=G (n={len(g_days)}) | {(g_days['pnl_call_2m']>0).sum()} | — | {call_g:.2f} | {put_g:.2f} | best={'CALL' if call_g>put_g else 'PUT'} |")
    lines.append(f"| {col}=R (n={len(r_days)}) | — | {(r_days['pnl_put_2m']>0).sum()} | {call_r:.2f} | {put_r:.2f} | best={'CALL' if call_r>put_r else 'PUT'} |")
    print(f"  bar15s_{bar_i}: G→CALL={call_g:.2f}/PUT={put_g:.2f} | R→CALL={call_r:.2f}/PUT={put_r:.2f}")

# Best INVV 15sec rule
best_invv_15s = None
best_invv_15s_delta = 0
for bar_i in range(4):
    col = f'bar15s_{bar_i}_dir'
    if col not in df.columns:
        continue
    for bar_dir, trade_dir in [('G', 'CALL'), ('G', 'PUT'), ('R', 'CALL'), ('R', 'PUT')]:
        def make_15s_rule(col=col, bar_dir=bar_dir, trade_dir=trade_dir):
            opp = 'PUT' if trade_dir == 'CALL' else 'CALL'
            def rule(row):
                d = row.get(col, '?')
                direction = trade_dir if d == bar_dir else opp
                b0 = row['bar0_dir']
                size = 2.0 if ((direction=='CALL' and b0=='G') or (direction=='PUT' and b0=='R')) else 0.0
                return (direction, size, 2)
            return rule
        tot, t = simulate(df, extra_rules={'INVV': make_15s_rule()})
        delta = tot - base_total
        if delta > best_invv_15s_delta:
            best_invv_15s_delta = delta
            best_invv_15s = (col, bar_dir, trade_dir, tot, t)

if best_invv_15s:
    col, bd, td, tot, t = best_invv_15s
    r = test_improvement(f"INVV 15sec: {col}={bd}→{td}", tot, t)
    lines.append(f"\n**Best 15sec rule**: {col}={bd}→{td}: Δ{r['delta']:+.2f} {'✓ ROBUST' if r['robust'] else '✗'}")


# ══════════════════════════════════════════════════════════════════════════════
# LOOP 2: FAKEDN — Extended Exit Optimization
# ══════════════════════════════════════════════════════════════════════════════

lines.append("\n---\n## LOOP 2: FAKEDN Extended Exit\n")
print(f"\n=== LOOP 2: FAKEDN ({len(df[df['opening_pattern']=='FAKEDN'])} days) ===")

fakedn_days = df[df['opening_pattern'] == 'FAKEDN']
base_fakedn = base_trades[base_trades['pattern'] == 'FAKEDN'] if len(base_trades) > 0 else pd.DataFrame()
print(f"Baseline FAKEDN PnL: ${base_fakedn['pnl'].sum():.2f} (n={len(base_fakedn)})")

lines.append(f"FAKEDN = RG (bar0=R, bar1=G, bar2≠G). Current exit=2m. Peak at 20m historically.")
lines.append(f"Baseline FAKEDN: ${base_fakedn['pnl'].sum():.2f}")
lines.append("\n### Exit Time Scan (FAKEDN under direction system)\n")
lines.append("| Exit min | FAKEDN PnL | System total | Delta | H1 | H2 | Robust? |")
lines.append("|----------|-----------|--------------|-------|----|----|---------|")

best_fakedn_exit = {'exit': 2, 'delta': 0, 'total': base_total, 't': base_trades}
for exit_min in range(1, 21):
    exit_rules_test = {**EXIT_RULES_BASE, 'FAKEDN': exit_min}
    tot, t = simulate(df, exit_rules=exit_rules_test)
    delta = tot - base_total
    h1, h2 = h1h2(t)
    dh1 = h1 - base_h1
    dh2 = h2 - base_h2
    robust = delta > 0 and dh1 > 0 and dh2 > 0
    fakedn_pnl = t[t['pattern']=='FAKEDN']['pnl'].sum() if len(t) > 0 else 0
    mark = '✓' if robust else ''
    lines.append(f"| {exit_min}m | ${fakedn_pnl:.2f} | ${tot:.2f} | {delta:+.2f} | {h1:.2f} | {h2:.2f} | {mark} |")
    if delta > best_fakedn_exit['delta']:
        best_fakedn_exit = {'exit': exit_min, 'delta': delta, 'total': tot, 't': t}

best_e = best_fakedn_exit
print(f"Best FAKEDN exit: {best_e['exit']}m → ${best_e['total']:.2f} (Δ{best_e['delta']:+.2f})")
r = test_improvement(f"FAKEDN exit@{best_e['exit']}m", best_e['total'], best_e['t'])
lines.append(f"\n**Best FAKEDN exit**: {best_e['exit']}m → Δ{r['delta']:+.2f} {'✓ ROBUST' if r['robust'] else '✗'}")


# ══════════════════════════════════════════════════════════════════════════════
# LOOP 3: VSHAPE — Exit Timing + 15sec Intrabar
# ══════════════════════════════════════════════════════════════════════════════

lines.append("\n---\n## LOOP 3: VSHAPE Exit + 15sec Signal\n")
print(f"\n=== LOOP 3: VSHAPE ({len(df[df['opening_pattern']=='VSHAPE'])} days) ===")

vshape_days = df[df['opening_pattern'] == 'VSHAPE']
base_vshape = base_trades[base_trades['pattern'] == 'VSHAPE'] if len(base_trades) > 0 else pd.DataFrame()
print(f"Baseline VSHAPE PnL: ${base_vshape['pnl'].sum():.2f} (n={len(base_vshape)})")

lines.append(f"VSHAPE = RGG. Peaks at 1m. Baseline: ${base_vshape['pnl'].sum():.2f}")
lines.append("\n### Exit Time Scan (VSHAPE)\n")
lines.append("| Exit min | VSHAPE PnL | System total | Delta | H1 | H2 | Robust? |")
lines.append("|----------|-----------|--------------|-------|----|----|---------|")

best_vs_exit = {'exit': 2, 'delta': 0, 'total': base_total, 't': base_trades}
for exit_min in range(1, 11):
    exit_rules_test = {**EXIT_RULES_BASE, 'VSHAPE': exit_min}
    tot, t = simulate(df, exit_rules=exit_rules_test)
    delta = tot - base_total
    h1, h2 = h1h2(t)
    dh1 = h1 - base_h1
    dh2 = h2 - base_h2
    robust = delta > 0 and dh1 > 0 and dh2 > 0
    vs_pnl = t[t['pattern']=='VSHAPE']['pnl'].sum() if len(t) > 0 else 0
    mark = '✓' if robust else ''
    lines.append(f"| {exit_min}m | ${vs_pnl:.2f} | ${tot:.2f} | {delta:+.2f} | {h1:.2f} | {h2:.2f} | {mark} |")
    if delta > best_vs_exit['delta']:
        best_vs_exit = {'exit': exit_min, 'delta': delta, 'total': tot, 't': t}

print(f"Best VSHAPE exit: {best_vs_exit['exit']}m → Δ{best_vs_exit['delta']:+.2f}")

# VSHAPE direction (follow_binary) — test always_call
exit_rules_vs1 = {**EXIT_RULES_BASE, 'VSHAPE': 1}
dir_rules_vs_call = {**DIR_RULES, 'VSHAPE': 'always_call'}
tot_vs_call1, t_vs_call1 = simulate(df, dir_rules=dir_rules_vs_call, exit_rules=exit_rules_vs1)
r_vc1 = test_improvement("VSHAPE always_call + exit@1m", tot_vs_call1, t_vs_call1)
lines.append(f"\n**VSHAPE always_call + exit@1m**: Δ{r_vc1['delta']:+.2f} {'✓' if r_vc1['robust'] else '✗'}")

# VSHAPE 15sec: does last 15sec of bar0 (bar15s_3) give signal?
lines.append("\n### VSHAPE 15sec Intrabar Analysis")
print("  VSHAPE 15sec bars:")
lines.append("| 15sec bar | G days WR | R days WR | G total CALL | R total CALL | Insight |")
lines.append("|-----------|-----------|-----------|--------------|--------------|---------|")
for bar_i in range(4):
    col = f'bar15s_{bar_i}_dir'
    if col not in vshape_days.columns:
        continue
    g_d = vshape_days[vshape_days[col] == 'G']
    r_d = vshape_days[vshape_days[col] == 'R']
    gwr = (g_d['pnl_call_2m'] > 0).mean() if len(g_d) > 0 else 0
    rwr = (r_d['pnl_call_2m'] > 0).mean() if len(r_d) > 0 else 0
    gt = g_d['pnl_call_2m'].sum()
    rt = r_d['pnl_call_2m'].sum()
    insight = "G=strong recovery" if abs(gwr - rwr) > 0.1 else "weak signal"
    lines.append(f"| {col} | {gwr*100:.1f}% (n={len(g_d)}) | {rwr*100:.1f}% (n={len(r_d)}) | {gt:.2f} | {rt:.2f} | {insight} |")
    print(f"  {col}: G→CALL_WR={gwr*100:.1f}% (n={len(g_d)}) R→CALL_WR={rwr*100:.1f}% (n={len(r_d)})")

# Best VSHAPE 15sec sub-filter
best_vs_15s = {'delta': 0}
for bar_i in range(4):
    col = f'bar15s_{bar_i}_dir'
    if col not in df.columns:
        continue
    for bar_dir, trade_dir in [('G', 'CALL'), ('G', 'PUT'), ('R', 'CALL'), ('R', 'PUT')]:
        opp = 'PUT' if trade_dir == 'CALL' else 'CALL'
        def make_vs_rule(col=col, bar_dir=bar_dir, trade_dir=trade_dir, opp=opp):
            def rule(row):
                d = row.get(col, '?')
                direction = trade_dir if d == bar_dir else opp
                b0 = row['bar0_dir']
                size = 2.0 if ((direction=='CALL' and b0=='G') or (direction=='PUT' and b0=='R')) else 0.0
                return (direction, size, 1)  # 1m exit for VSHAPE
            return rule
        tot, t = simulate(df, extra_rules={'VSHAPE': make_vs_rule()})
        delta = tot - base_total
        if delta > best_vs_15s['delta']:
            best_vs_15s = {'delta': delta, 'col': col, 'bar_dir': bar_dir, 'trade_dir': trade_dir,
                           'total': tot, 't': t}

if best_vs_15s['delta'] > 0:
    r = test_improvement(f"VSHAPE 15sec: {best_vs_15s['col']}={best_vs_15s['bar_dir']}→{best_vs_15s['trade_dir']}",
                         best_vs_15s['total'], best_vs_15s['t'])
    lines.append(f"\n**Best VSHAPE 15sec**: {best_vs_15s['col']}={best_vs_15s['bar_dir']}→{best_vs_15s['trade_dir']}: Δ{r['delta']:+.2f} {'✓' if r['robust'] else '✗'}")


# ══════════════════════════════════════════════════════════════════════════════
# LOOP 4: FAKEUP — Direction Sub-Filter
# ══════════════════════════════════════════════════════════════════════════════

lines.append("\n---\n## LOOP 4: FAKEUP Direction Sub-Filter\n")
print(f"\n=== LOOP 4: FAKEUP ({len(df[df['opening_pattern']=='FAKEUP'])} days) ===")

fakeup_days = df[df['opening_pattern'] == 'FAKEUP']
base_fakeup = base_trades[base_trades['pattern'] == 'FAKEUP'] if len(base_trades) > 0 else pd.DataFrame()
print(f"Baseline FAKEUP PnL: ${base_fakeup['pnl'].sum():.2f} (n={len(base_fakeup)})")

lines.append(f"FAKEUP = GRG (or GR+). Current: follow_binary. Baseline: ${base_fakeup['pnl'].sum():.2f}")
lines.append(f"Best_side_2m distribution:")

fakeup_call_days = (fakeup_days['best_side_2m'] == 'CALL').sum()
fakeup_put_days = (fakeup_days['best_side_2m'] == 'PUT').sum()
lines.append(f"- CALL wins: {fakeup_call_days} days ({fakeup_call_days/len(fakeup_days)*100:.1f}%)")
lines.append(f"- PUT wins:  {fakeup_put_days} days ({fakeup_put_days/len(fakeup_days)*100:.1f}%)")
print(f"  FAKEUP best_side_2m: CALL={fakeup_call_days} PUT={fakeup_put_days}")

# PM feature sub-filters for FAKEUP
lines.append("\n### FAKEUP PM Feature Sub-Filters")
lines.append("| Feature | Thresh | N above→CALL | N below→PUT | Delta |")
lines.append("|---------|--------|-------------|------------|-------|")

fakeup_results = []
for feat in ['pm_slope', 'pm_accel_2m', 'pm_position', 'agree_count', 'pm_green_pct',
             'gap', 'bar0_range', 'bar0_body_pct', 'pm_r2', 'pm_accel_4m']:
    col = fakeup_days[feat].dropna()
    if len(col) < 5:
        continue
    for thresh in np.percentile(col, [25, 50, 75]):
        for inv in [False, True]:
            def make_fu_rule(feat=feat, thresh=thresh, inv=inv):
                def rule(row):
                    val = row.get(feat, np.nan)
                    if np.isnan(val):
                        return None  # fall through to standard
                    if not inv:
                        direction = 'CALL' if val >= thresh else 'PUT'
                    else:
                        direction = 'PUT' if val >= thresh else 'CALL'
                    b0 = row['bar0_dir']
                    size = 2.0 if ((direction=='CALL' and b0=='G') or (direction=='PUT' and b0=='R')) else 0.0
                    return (direction, size, 2)
                return rule
            tot, t = simulate(df, extra_rules={'FAKEUP': make_fu_rule()})
            delta = tot - base_total
            if abs(delta) > 8:
                n_a = (fakeup_days[feat] >= thresh).sum()
                n_b = len(fakeup_days) - n_a
                direction_str = f">={thresh:.2f}→{'PUT' if inv else 'CALL'}"
                fakeup_results.append({'feat': feat, 'thresh': thresh, 'inv': inv,
                                       'delta': delta, 'dir': direction_str})
                h1, h2 = h1h2(t)
                lines.append(f"| {feat} | {thresh:.2f}{'(inv)' if inv else ''} | {n_a} | {n_b} | {delta:+.2f} |")

if fakeup_results:
    fakeup_results.sort(key=lambda x: x['delta'], reverse=True)
    best_fu = fakeup_results[0]
    print(f"Best FAKEUP sub-filter: {best_fu['feat']}{best_fu['dir']} → Δ{best_fu['delta']:+.2f}")
    lines.append(f"\n**Best FAKEUP sub-filter**: {best_fu['feat']} {best_fu['dir']} → Δ{best_fu['delta']:+.2f}")
else:
    print("  No FAKEUP sub-filter > $8 delta found")
    lines.append("\n**No significant FAKEUP sub-filter found**")

# Test FAKEUP follow_majority instead of follow_binary
dir_rules_fu_maj = {**DIR_RULES, 'FAKEUP': 'follow_majority'}
tot_fu_maj, t_fu_maj = simulate(df, dir_rules=dir_rules_fu_maj)
r_fu_maj = test_improvement("FAKEUP follow_majority", tot_fu_maj, t_fu_maj)
lines.append(f"\n**FAKEUP follow_majority**: Δ{r_fu_maj['delta']:+.2f} {'✓' if r_fu_maj['robust'] else '✗'}")


# ══════════════════════════════════════════════════════════════════════════════
# LOOP 5: INVV Delayed Entry (wait for bar3)
# ══════════════════════════════════════════════════════════════════════════════

lines.append("\n---\n## LOOP 5: INVV Delayed Entry (bar3 direction)\n")
print(f"\n=== LOOP 5: INVV Delayed Entry ===")

# Enter at bar3, exit at bar5 (2m later)
# PnL = bar5_close - bar3_close (CALL) or bar3_close - bar5_close (PUT)
# bar3_change = bar3_close - open_930, bar5_change = bar5_close - open_930
# So pnl_delayed_call = bar5_change - bar3_change = pnl_call_5m - pnl_call_3m (actually bar pnl not cumulative... need to recompute)

# Actually pnl_call_Xm = close_X - open_930
# Entry at bar3 = bar3_close, exit at bar5 = bar5_close
# delayed_pnl_call = bar5_close - bar3_close = pnl_call_5m - pnl_call_3m?
# NO: pnl_call_5m = bar5_close - open_930, pnl_call_3m = bar3_close - open_930
# So delayed = pnl_call_5m - pnl_call_3m... but we need to check sign carefully
# For CALL: profit = exit - entry = bar5 - bar3 = (bar5 - open) - (bar3 - open) = pnl_5m - pnl_3m
# For PUT:  profit = entry - exit = bar3 - bar5 = (bar3 - open) - (bar5 - open) = pnl_3m - pnl_5m

invv_delayed = invv_days.copy()
invv_delayed['pnl_call_delayed'] = invv_delayed['pnl_call_5m'] - invv_delayed['pnl_call_3m']  # enter@bar3, exit@bar5
invv_delayed['pnl_put_delayed']  = invv_delayed['pnl_put_5m']  - invv_delayed['pnl_put_3m']   # equiv

# bar3_dir as direction signal
b3_call_wins = (invv_delayed[invv_delayed['bar3_dir']=='G']['pnl_call_delayed'] > 0).sum()
b3_call_n = (invv_delayed['bar3_dir']=='G').sum()
b3_put_wins = (invv_delayed[invv_delayed['bar3_dir']=='R']['pnl_put_delayed'] > 0).sum()
b3_put_n = (invv_delayed['bar3_dir']=='R').sum()

call_total_b3g = invv_delayed[invv_delayed['bar3_dir']=='G']['pnl_call_delayed'].sum()
put_total_b3r = invv_delayed[invv_delayed['bar3_dir']=='R']['pnl_put_delayed'].sum()

print(f"  bar3=G → CALL (enter@3m, exit@5m): n={b3_call_n}, wins={b3_call_wins}, total=${call_total_b3g:.2f}")
print(f"  bar3=R → PUT  (enter@3m, exit@5m): n={b3_put_n},  wins={b3_put_wins},  total=${put_total_b3r:.2f}")

lines.append(f"Enter at 9:33 (bar3), exit at 9:35 (bar5). Pnl = bar5 - bar3 in direction of bar3.")
lines.append(f"\n| Trigger | N | Win rate | Total PnL |")
lines.append(f"|---------|---|----------|-----------|")
lines.append(f"| bar3=G → CALL | {b3_call_n} | {b3_call_wins/b3_call_n*100:.1f}% | ${call_total_b3g:.2f} |")
lines.append(f"| bar3=R → PUT  | {b3_put_n}  | {b3_put_wins/b3_put_n*100:.1f}%  | ${put_total_b3r:.2f}  |")

# Test combined: delayed entry for all INVV (no first3 confirmation needed since entering later)
# Replace INVV trades with delayed entries at full 1x size (no 2x since delayed)
invv_delay_total = call_total_b3g + put_total_b3r
base_invv_pnl = base_trades[base_trades['pattern']=='INVV']['pnl'].sum() if len(base_trades) > 0 else 0.0
delta_delayed = invv_delay_total - base_invv_pnl
lines.append(f"\nDelayed INVV total: ${invv_delay_total:.2f} vs system INVV: ${base_invv_pnl:.2f}")
lines.append(f"Delta (INVV only): {delta_delayed:+.2f}")


# ══════════════════════════════════════════════════════════════════════════════
# LOOP 6: Re-fit exit curves under direction system
# ══════════════════════════════════════════════════════════════════════════════

lines.append("\n---\n## LOOP 6: Re-fit Exit Curves Under Direction System\n")
print(f"\n=== LOOP 6: Re-fit exit curves ===")

lines.append("Previously: exit optimization HURT when combined with direction (−$56). But curves were")
lines.append("trained on BINARY direction PnL. Re-fitting on DIRECTION-CORRECTED PnL curves:\n")
lines.append("| Pattern | Direction | @1m | @2m | @3m | @5m | @7m | @10m | Best exit |")
lines.append("|---------|-----------|-----|-----|-----|-----|-----|------|-----------|")

best_exits_per_pattern = {}
for pat in ['CRASH','SURGE','DRIFT_DN','DRIFT_UP','FAKEDN','FAKEUP','INVV','VSHAPE']:
    pat_days = df[df['opening_pattern'] == pat]
    rule = DIR_RULES.get(pat, 'follow_binary')

    pnls_by_min = {}
    for exit_min in [1, 2, 3, 5, 7, 10, 15, 20]:
        total = 0
        for _, row in pat_days.iterrows():
            direction = get_direction(row, rule)
            bar0_dir = row['bar0_dir']
            # first3 sizing
            if (direction=='CALL' and bar0_dir=='G') or (direction=='PUT' and bar0_dir=='R'):
                size = 2.0
            else:
                size = 0.0
            if size == 0:
                continue
            pnl = row.get(f'pnl_{direction.lower()}_{exit_min}m', np.nan)
            if not np.isnan(pnl):
                total += pnl * size
        pnls_by_min[exit_min] = total

    best_min = max(pnls_by_min, key=pnls_by_min.get)
    best_exits_per_pattern[pat] = best_min

    row_str = f"| {pat} | {rule[:12]} | {pnls_by_min.get(1,0):.1f} | {pnls_by_min.get(2,0):.1f} | {pnls_by_min.get(3,0):.1f} | {pnls_by_min.get(5,0):.1f} | {pnls_by_min.get(7,0):.1f} | {pnls_by_min.get(10,0):.1f} | **{best_min}m** |"
    lines.append(row_str)
    print(f"  {pat}: best exit = {best_min}m (${pnls_by_min[best_min]:.2f})")

# Test using re-fitted exits for all patterns
tot_refit, t_refit = simulate(df, exit_rules=best_exits_per_pattern)
r_refit = test_improvement("Re-fitted exits (all patterns)", tot_refit, t_refit)
lines.append(f"\n**Re-fitted exits system**: ${r_refit['total']:.2f} (Δ{r_refit['delta']:+.2f}) {'✓ ROBUST' if r_refit['robust'] else '✗'}")
lines.append(f"H1={r_refit['h1']:.2f} H2={r_refit['h2']:.2f}")

# Test partial: only change exits where re-fit improved
lines.append("\n### Selective exit improvements (only robust per-pattern changes):\n")
lines.append("| Pattern | Old exit | New exit | Delta | Both halves? |")
lines.append("|---------|----------|----------|-------|--------------|")

robust_exit_changes = {}
for pat, new_exit in best_exits_per_pattern.items():
    old_exit = 2
    if new_exit == old_exit:
        continue
    exit_test = {**EXIT_RULES_BASE, pat: new_exit}
    tot_t, t_t = simulate(df, exit_rules=exit_test)
    delta = tot_t - base_total
    h1, h2 = h1h2(t_t)
    robust = delta > 0 and h1 > base_h1 and h2 > base_h2
    mark = '✓' if robust else '✗'
    lines.append(f"| {pat} | 2m | {new_exit}m | {delta:+.2f} | {mark} |")
    if robust:
        robust_exit_changes[pat] = new_exit

if robust_exit_changes:
    combined_exits = {**EXIT_RULES_BASE, **robust_exit_changes}
    tot_rc, t_rc = simulate(df, exit_rules=combined_exits)
    r_rc = test_improvement(f"Combined robust exit changes {list(robust_exit_changes.keys())}", tot_rc, t_rc)
    lines.append(f"\n**Stacked robust exit changes**: Δ{r_rc['delta']:+.2f} {'✓' if r_rc['robust'] else '✗'}")


# ══════════════════════════════════════════════════════════════════════════════
# LOOP 7: First3 sizing threshold tuning
# ══════════════════════════════════════════════════════════════════════════════

lines.append("\n---\n## LOOP 7: Sizing Tuning — Skip vs 1x vs 2x\n")
print(f"\n=== LOOP 7: Sizing tuning ===")

lines.append("Current: bar0 agrees → 2x, disagrees → 0x skip")
lines.append("Test: bar0 agrees → 2x, disagrees → 1x (trade anyway at reduced size)\n")
lines.append("| Pattern | Disagree→1x delta | Only-INVV change |")
lines.append("|---------|------------------|-----------------|")

# Test: disagree → 1x for each pattern individually
best_disagree_delta = 0
best_disagree_pattern = None
for pat in ['CRASH','SURGE','DRIFT_DN','DRIFT_UP','FAKEDN','FAKEUP','INVV','VSHAPE']:
    def make_disagree_1x(pat=pat):
        def rule(row):
            p = row['opening_pattern']
            if p != pat:
                return None
            dr = DIR_RULES.get(p, 'follow_binary')
            direction = get_direction(row, dr)
            b0 = row['bar0_dir']
            if (direction=='CALL' and b0=='G') or (direction=='PUT' and b0=='R'):
                size = 2.0
            else:
                size = 1.0  # trade anyway at 1x
            return (direction, size, 2)
        return rule
    tot, t = simulate(df, extra_rules={pat: make_disagree_1x()})
    delta = tot - base_total
    h1, h2 = h1h2(t)
    robust = delta > 0 and h1 > base_h1 and h2 > base_h2
    lines.append(f"| {pat} | {delta:+.2f} {'✓' if robust else '✗'} | — |")
    print(f"  {pat} disagree→1x: Δ{delta:+.2f} {'✓' if robust else ''}")
    if delta > best_disagree_delta:
        best_disagree_delta = delta
        best_disagree_pattern = (pat, tot, t)

if best_disagree_pattern:
    pat, tot, t = best_disagree_pattern
    r = test_improvement(f"Disagree→1x for {pat}", tot, t)
    lines.append(f"\n**Best sizing change**: {pat} disagree→1x: Δ{r['delta']:+.2f} {'✓' if r['robust'] else '✗'}")


# ══════════════════════════════════════════════════════════════════════════════
# LOOP 8: Grand Combined System
# ══════════════════════════════════════════════════════════════════════════════

lines.append("\n---\n## LOOP 8: Grand Combined System\n")
print(f"\n=== LOOP 8: Grand Combined ===")

lines.append("Building incrementally with all robust improvements:\n")
lines.append("| Step | Addition | PnL | Delta | H1 | H2 | Robust? |")
lines.append("|------|----------|-----|-------|----|----|---------|")

# Start with baseline
current_total = base_total
current_trades = base_trades
current_dir_rules = dict(DIR_RULES)
current_exit_rules = dict(EXIT_RULES_BASE)
current_extra_rules = {}
current_skip = set()
r5_robust = False
r6_robust = False
r7_robust = False

lines.append(f"| 0 | Baseline | ${base_total:.2f} | — | {base_h1:.2f} | {base_h2:.2f} | — |")

def try_add(desc, new_total, new_t, step_n):
    h1, h2 = h1h2(new_t)
    delta = new_total - base_total
    robust = h1 > base_h1 and h2 > base_h2
    lines.append(f"| {step_n} | {desc} | ${new_total:.2f} | {delta:+.2f} | {h1:.2f} | {h2:.2f} | {'✓' if robust else '✗'} |")
    return robust, h1, h2

# Step 1: Skip INVV vs best INVV fix (take whichever is better and robust)
# From Loop 1: skip INVV gave +delta
tot_skip, t_skip = simulate(df, skip_patterns={'INVV'})
r1_robust, _, _ = try_add("Skip INVV", tot_skip, t_skip, 1)
print(f"Step 1 Skip INVV: ${tot_skip:.2f} (Δ{tot_skip-base_total:+.2f}) {'✓' if r1_robust else '✗'}")

# Step 2: Best FAKEDN exit (from loop 2)
best_fakedn_e = best_fakedn_exit['exit']
exit_r2 = {**EXIT_RULES_BASE, 'FAKEDN': best_fakedn_e}
if r1_robust:
    tot_r2, t_r2 = simulate(df, skip_patterns={'INVV'}, exit_rules=exit_r2)
else:
    tot_r2, t_r2 = simulate(df, exit_rules=exit_r2)
r2_robust, _, _ = try_add(f"+ FAKEDN exit@{best_fakedn_e}m", tot_r2, t_r2, 2)
print(f"Step 2 FAKEDN exit@{best_fakedn_e}m: ${tot_r2:.2f} (Δ{tot_r2-base_total:+.2f}) {'✓' if r2_robust else '✗'}")

# Step 3: VSHAPE best exit
best_vs_e = best_vs_exit['exit']
exit_r3 = {**exit_r2, 'VSHAPE': best_vs_e}
skip_r3 = {'INVV'} if r1_robust else set()
tot_r3, t_r3 = simulate(df, skip_patterns=skip_r3, exit_rules=exit_r3)
r3_robust, _, _ = try_add(f"+ VSHAPE exit@{best_vs_e}m", tot_r3, t_r3, 3)
print(f"Step 3 VSHAPE exit@{best_vs_e}m: ${tot_r3:.2f} (Δ{tot_r3-base_total:+.2f}) {'✓' if r3_robust else '✗'}")

# Step 4: Robust exit changes from loop 6
if robust_exit_changes:
    exit_r4 = {**exit_r3, **robust_exit_changes}
    tot_r4, t_r4 = simulate(df, skip_patterns=skip_r3, exit_rules=exit_r4)
    r4_robust, _, _ = try_add(f"+ refit exits {list(robust_exit_changes.keys())}", tot_r4, t_r4, 4)
    print(f"Step 4 refit exits: ${tot_r4:.2f} (Δ{tot_r4-base_total:+.2f}) {'✓' if r4_robust else '✗'}")
    current_exit = exit_r4
    prev_total = tot_r4
    prev_trades = t_r4
else:
    current_exit = exit_r3
    prev_total = tot_r3
    prev_trades = t_r3

# Step 5: Best FAKEUP PM sub-filter (if found)
if fakeup_results:
    best_fu2 = fakeup_results[0]
    feat, thresh, inv = best_fu2['feat'], best_fu2['thresh'], best_fu2['inv']
    def make_best_fu(feat=feat, thresh=thresh, inv=inv):
        def rule(row):
            val = row.get(feat, np.nan)
            if np.isnan(val):
                return None
            if not inv:
                direction = 'CALL' if val >= thresh else 'PUT'
            else:
                direction = 'PUT' if val >= thresh else 'CALL'
            b0 = row['bar0_dir']
            size = 2.0 if ((direction=='CALL' and b0=='G') or (direction=='PUT' and b0=='R')) else 0.0
            return (direction, size, 2)
        return rule
    tot_r5, t_r5 = simulate(df, skip_patterns=skip_r3, exit_rules=current_exit,
                             extra_rules={'FAKEUP': make_best_fu()})
    r5_robust, _, _ = try_add(f"+ FAKEUP {feat}{'>=' if not inv else '<'}{thresh:.2f}", tot_r5, t_r5, 5)  # noqa: F841 (defined earlier)
    print(f"Step 5 FAKEUP sub-filter: ${tot_r5:.2f} (Δ{tot_r5-base_total:+.2f}) {'✓' if r5_robust else '✗'}")
    if r5_robust:
        prev_total = tot_r5
        prev_trades = t_r5

# Step 6: INVV bar15s_1=G→CALL direction filter (from Loop 1)
if best_invv_15s and best_invv_15s_delta > 0:
    col_i, bd_i, td_i, _, _ = best_invv_15s  # tuple: (col, bar_dir, trade_dir, tot, t)
    opp_i = 'PUT' if td_i == 'CALL' else 'CALL'
    cur_exit_invv = current_exit.get('INVV', 2)
    def make_invv_15s_final(col=col_i, bar_dir=bd_i, trade_dir=td_i, opp=opp_i, ex=cur_exit_invv):
        def rule(row):
            d = row.get(col, '?')
            direction = trade_dir if d == bar_dir else opp
            b0 = row['bar0_dir']
            size = 2.0 if ((direction=='CALL' and b0=='G') or (direction=='PUT' and b0=='R')) else 0.0
            return (direction, size, ex)
        return rule
    prev_extra = dict(prev_trades.attrs) if hasattr(prev_trades, 'attrs') else {}
    combined_extra_6 = {'INVV': make_invv_15s_final()}
    if fakeup_results and r5_robust:
        combined_extra_6['FAKEUP'] = make_best_fu()
    tot_r6, t_r6 = simulate(df, skip_patterns=skip_r3, exit_rules=current_exit,
                             extra_rules=combined_extra_6)
    r6_robust, _, _ = try_add(f"+ INVV {col_i}={bd_i}→{td_i}", tot_r6, t_r6, 6)  # noqa
    print(f"Step 6 INVV 15sec: ${tot_r6:.2f} (Δ{tot_r6-base_total:+.2f}) {'✓' if r6_robust else '✗'}")
    if r6_robust:
        prev_total = tot_r6
        prev_trades = t_r6

# Step 7: VSHAPE bar15s_1=G→CALL direction filter (from Loop 3)
if best_vs_15s and best_vs_15s.get('delta', 0) > 0 and best_vs_15s['delta'] > 0:
    col_v = best_vs_15s['col']
    bd_v  = best_vs_15s['bar_dir']
    td_v  = best_vs_15s['trade_dir']
    opp_v = 'PUT' if td_v == 'CALL' else 'CALL'
    cur_exit_vs = current_exit.get('VSHAPE', 2)
    def make_vs_15s_final(col=col_v, bar_dir=bd_v, trade_dir=td_v, opp=opp_v, ex=cur_exit_vs):
        def rule(row):
            d = row.get(col, '?')
            direction = trade_dir if d == bar_dir else opp
            b0 = row['bar0_dir']
            size = 2.0 if ((direction=='CALL' and b0=='G') or (direction=='PUT' and b0=='R')) else 0.0
            return (direction, size, ex)
        return rule
    # Build combined extra rules carrying forward all previous extra rules
    combined_extra_7 = {}
    if best_invv_15s and best_invv_15s_delta > 0 and r6_robust:
        combined_extra_7['INVV'] = make_invv_15s_final()
    if fakeup_results and r5_robust:
        combined_extra_7['FAKEUP'] = make_best_fu()
    combined_extra_7['VSHAPE'] = make_vs_15s_final()
    tot_r7, t_r7 = simulate(df, skip_patterns=skip_r3, exit_rules=current_exit,
                             extra_rules=combined_extra_7)
    r7_robust, _, _ = try_add(f"+ VSHAPE {col_v}={bd_v}→{td_v}", tot_r7, t_r7, 7)  # noqa
    print(f"Step 7 VSHAPE 15sec: ${tot_r7:.2f} (Δ{tot_r7-base_total:+.2f}) {'✓' if r7_robust else '✗'}")
    if r7_robust:
        prev_total = tot_r7
        prev_trades = t_r7

# Step 8: INVV delayed entry (enter@bar3, exit@bar5, follow bar3_dir, 1x size)
# PnL = (bar5_close - bar3_close) in direction of bar3
# = pnl_call_5m - pnl_call_3m  (CALL)  or  pnl_put_5m - pnl_put_3m  (PUT)
# This replaces INVV 9:30 entries with 9:33 entries — simulate separately then combine
def simulate_with_invv_delayed(df, base_trades, skip_patterns=None, exit_rules=None, extra_rules=None):
    """Replace INVV standard trades with delayed bar3 entry trades."""
    # Run standard sim but skip INVV
    skip_with_invv = (skip_patterns or set()) | {'INVV'}
    tot_no_invv, t_no_invv = simulate(df, skip_patterns=skip_with_invv,
                                       exit_rules=exit_rules, extra_rules=extra_rules)
    # Add delayed INVV trades
    invv_rows = df[df['opening_pattern'] == 'INVV']
    delayed_trades = []
    for date, row in invv_rows.iterrows():
        b3_dir = row.get('bar3_dir', '?')
        if b3_dir not in ('G', 'R'):
            continue
        direction = 'CALL' if b3_dir == 'G' else 'PUT'
        # pnl from entry at bar3 to exit at bar5
        call_entry = row.get('pnl_call_3m', np.nan)   # bar3_close - open_930
        call_exit  = row.get('pnl_call_5m', np.nan)   # bar5_close - open_930
        if np.isnan(call_entry) or np.isnan(call_exit):
            continue
        if direction == 'CALL':
            pnl = (call_exit - call_entry) * 1.0   # 1x size (no first3 gate)
        else:
            pnl = (call_entry - call_exit) * 1.0   # PUT: profit when price drops
        delayed_trades.append({'date': date, 'pattern': 'INVV', 'direction': direction,
                                'size': 1.0, 'pnl': pnl, 'exit_min': 5})
    if delayed_trades:
        t_delayed = pd.DataFrame(delayed_trades).set_index('date').sort_index()
        t_combined = pd.concat([t_no_invv, t_delayed]).sort_index()
        return t_combined['pnl'].sum(), t_combined
    return tot_no_invv, t_no_invv

# Build the extra_rules for step 8 (carry forward all robust extras)
combined_extra_8 = {}
if best_invv_15s and best_invv_15s_delta > 0 and r6_robust:
    pass  # delayed entry replaces INVV — 15sec filter no longer needed
if fakeup_results and r5_robust:
    combined_extra_8['FAKEUP'] = make_best_fu()
if best_vs_15s and best_vs_15s.get('delta', 0) > 0 and r7_robust:
    combined_extra_8['VSHAPE'] = make_vs_15s_final()

tot_r8, t_r8 = simulate_with_invv_delayed(df, prev_trades,
                                            skip_patterns=skip_r3,
                                            exit_rules=current_exit,
                                            extra_rules=combined_extra_8)
r8_robust, _, _ = try_add("+ INVV delayed entry (bar3→bar5)", tot_r8, t_r8, 8)
print(f"Step 8 INVV delayed: ${tot_r8:.2f} (Δ{tot_r8-base_total:+.2f}) {'✓' if r8_robust else '✗'}")
if r8_robust:
    prev_total = tot_r8
    prev_trades = t_r8

# Final
lines.append(f"\n**Final system**: ${prev_total:.2f} (Δ{prev_total-base_total:+.2f} vs baseline)")
h1f, h2f = h1h2(prev_trades)
lines.append(f"H1={h1f:.2f}, H2={h2f:.2f}")
lines.append(f"\nBaseline was: ${base_total:.2f} (H1={base_h1:.2f}, H2={base_h2:.2f})")
lines.append(f"Ceiling was:  $1,297.25 — new capture rate: {prev_total/1297.25*100:.1f}%")

# Pattern breakdown
lines.append("\n### Final System — PnL by Pattern\n")
lines.append("| Pattern | n_trades | total | avg | win_rate |")
lines.append("|---------|---------|-------|-----|----------|")
for pat in ['CRASH','SURGE','DRIFT_DN','DRIFT_UP','FAKEDN','FAKEUP','INVV','VSHAPE']:
    t_p = prev_trades[prev_trades['pattern']==pat] if len(prev_trades) > 0 else pd.DataFrame()
    if len(t_p) == 0:
        lines.append(f"| {pat} | 0 | $0.00 | — | — |")
        continue
    wr = (t_p['pnl'] > 0).mean() * 100
    lines.append(f"| {pat} | {len(t_p)} | ${t_p['pnl'].sum():.2f} | ${t_p['pnl'].mean():.2f} | {wr:.1f}% |")

print(f"\n=== FINAL COMBINED: ${prev_total:.2f} (Δ{prev_total-base_total:+.2f}) ===")
print(f"H1={h1f:.2f}, H2={h2f:.2f}")

# ─── QUARTERLY SYSTEM-LEVEL CHECK ────────────────────────────────────────────
lines.append("\n---\n## Quarterly System-Level Check\n")
lines.append("Purpose: sanity check that no single quarter is carrying the system.")
lines.append("Per-pattern rules NOT validated here (N too small per quarter).\n")

# Q1 2025 only 9 days — merge into Q2 for display, but show separately
QUARTERS = {
    'Q2-2025': ('2025-04-01', '2025-06-30'),
    'Q3-2025': ('2025-07-01', '2025-09-30'),
    'Q4-2025': ('2025-10-01', '2025-12-31'),
    'Q1-2026': ('2026-01-01', '2026-03-31'),
}

def quarter_pnl(t, start, end):
    if len(t) == 0:
        return 0, 0
    mask = (t.index >= start) & (t.index <= end)
    sub = t[mask]
    return sub['pnl'].sum(), len(sub)

lines.append("| Quarter | Days | Baseline | Combined | Delta | Green? |")
lines.append("|---------|------|---------|---------|-------|--------|")
print("\n=== Quarterly check ===")

all_green = True
for qname, (qs, qe) in QUARTERS.items():
    # count trading days in quarter
    n_days = ((df.index >= qs) & (df.index <= qe)).sum()
    b_pnl, b_n = quarter_pnl(base_trades, qs, qe)
    c_pnl, c_n = quarter_pnl(prev_trades, qs, qe)
    delta = c_pnl - b_pnl
    green = c_pnl > 0
    if not green:
        all_green = False
    mark = '✓' if green else '✗ LOSING'
    lines.append(f"| {qname} | {n_days} | ${b_pnl:.2f} ({b_n}t) | ${c_pnl:.2f} ({c_n}t) | {delta:+.2f} | {mark} |")
    print(f"  {qname}: baseline=${b_pnl:.2f} combined=${c_pnl:.2f} (Δ{delta:+.2f}) {mark}")

# Also show Q1-2025 partial (9 days)
qs, qe = '2025-01-01', '2025-03-31'
n_days = ((df.index >= qs) & (df.index <= qe)).sum()
b_pnl, _ = quarter_pnl(base_trades, qs, qe)
c_pnl, c_n = quarter_pnl(prev_trades, qs, qe)
lines.append(f"| Q1-2025* | {n_days} | ${b_pnl:.2f} | ${c_pnl:.2f} ({c_n}t) | {c_pnl-b_pnl:+.2f} | *partial (9d)* |")
print(f"  Q1-2025 (partial 9d): baseline=${b_pnl:.2f} combined=${c_pnl:.2f}")

verdict = "ALL 4 main quarters profitable ✓" if all_green else "WARNING: at least one quarter is losing ✗"
lines.append(f"\n**Verdict**: {verdict}")
lines.append(f"\n*Note: Q1-2025 only 9 days (Mar 19–31), excluded from verdict.*")
print(f"\n  {verdict}")

# Save
with open(OUT, 'w') as f:
    f.write('\n'.join(lines))
print(f"\nResults saved to {OUT}")
