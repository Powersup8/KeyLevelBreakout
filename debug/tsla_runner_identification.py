"""
TSLA Open Scalper — Runner Identification
Find features at ORB bull breakout time that predict which trades
will still be profitable at hold=20 bars.

Approach:
1. Run backtest at hold=3 and hold=20 (no SL for clean signal)
2. Compute extra breakout-time features from 1m bars
3. Compare runners (PnL@20 > 0) vs faders (PnL@20 <= 0)
4. Build simple threshold-based runner score
5. Backtest adaptive strategy: high score → hold 20, else → hold 3
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from tsla_scalp_backtest import Config, load_data, run_backtest, score_trades

REPO = Path('/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView')

def compute_breakout_features(trades_df, df1m):
    """Add breakout-time features from 1m bars to each bull trade."""
    extras = []
    for _, t in trades_df.iterrows():
        d = t['date']
        mkt = df1m[df1m.index.normalize() == d].between_time('09:30', '16:00')
        orb_bars = mkt.between_time('09:30', '09:34')
        post_orb = mkt[mkt.index.map(lambda x: 935 <= x.hour * 100 + x.minute <= 955)]

        orb_high = orb_bars['high'].max() if len(orb_bars) > 0 else np.nan

        # Find breakout bar
        brk_bar = None
        brk_idx = None
        for i, (idx, bar) in enumerate(post_orb.iterrows()):
            if bar['close'] > orb_high:
                brk_bar = bar
                brk_idx = idx
                break

        if brk_bar is None:
            extras.append({
                'brk_strength': np.nan, 'brk_volume': np.nan,
                'brk_timing': np.nan, 'brk_bar_range': np.nan,
                'brk_close_pos': np.nan, 'orb_vol_avg': np.nan,
                'brk_vol_ratio': np.nan,
            })
            continue

        brk_strength = brk_bar['close'] - orb_high  # $ above ORB high
        brk_volume = brk_bar['volume'] if 'volume' in brk_bar.index else np.nan
        brk_hm = brk_idx.hour * 100 + brk_idx.minute
        brk_timing = brk_hm - 935  # minutes from 9:35

        # Breakout bar range and close position
        bar_range = brk_bar['high'] - brk_bar['low']
        brk_close_pos = (brk_bar['close'] - brk_bar['low']) / bar_range if bar_range > 0 else 0.5

        # ORB average volume
        orb_vol = orb_bars['volume'].mean() if 'volume' in orb_bars.columns else np.nan
        vol_ratio = brk_volume / orb_vol if (orb_vol and orb_vol > 0) else np.nan

        extras.append({
            'brk_strength': brk_strength,
            'brk_volume': brk_volume,
            'brk_timing': brk_timing,
            'brk_bar_range': bar_range,
            'brk_close_pos': brk_close_pos,
            'orb_vol_avg': orb_vol,
            'brk_vol_ratio': vol_ratio,
        })

    return pd.DataFrame(extras, index=trades_df.index)


def run_adaptive_backtest(trades3, trades20, bulls, runner_mask):
    """
    Simulate adaptive strategy: runner_mask=True → use hold=20 PnL,
    else → use hold=3 PnL. Non-bull trades use hold=3 PnL.
    """
    # Start with hold=3 for everything
    pnls = trades3['pnl'].copy()

    # For bulls identified as runners, use hold=20 PnL
    bull_idx = bulls.index
    runner_idx = bulls[runner_mask].index
    pnls.loc[runner_idx] = trades20.loc[runner_idx, 'pnl']

    return pnls


def main():
    print("Loading data...")
    df1m, df15, dfvix, dfspy, dfqqq = load_data()

    # ── Run backtests at hold=3 and hold=20 (no SL for clean comparison) ──
    cfg3 = Config(hold_bars=3, sl_fallback=999.0)
    cfg20 = Config(hold_bars=20, sl_fallback=999.0)

    print("Running hold=3 backtest...")
    trades3 = run_backtest(cfg3, df1m, df15, dfvix, dfspy, dfqqq)
    print("Running hold=20 backtest...")
    trades20 = run_backtest(cfg20, df1m, df15, dfvix, dfspy, dfqqq)

    # Align on dates (should be identical)
    assert list(trades3['date']) == list(trades20['date']), "Trade dates don't match!"

    # Filter to bull breakouts only
    bull_mask = trades3['breakout_type'] == 'BULL'
    bulls3 = trades3[bull_mask].copy()
    bulls20 = trades20[bull_mask].copy()
    print(f"\nBull breakouts: {len(bulls3)} trades")

    # ── Compute extra breakout features ──
    print("Computing breakout features...")
    extra = compute_breakout_features(bulls3, df1m)
    bulls = bulls3.copy()
    for col in extra.columns:
        bulls[col] = extra[col].values
    bulls['pnl_20'] = bulls20['pnl'].values
    bulls['pnl_3'] = bulls3['pnl'].values
    bulls['is_runner'] = bulls['pnl_20'] > 0

    n_runners = bulls['is_runner'].sum()
    n_faders = (~bulls['is_runner']).sum()
    print(f"Runners (PnL@20>0): {n_runners} ({n_runners/len(bulls)*100:.0f}%)")
    print(f"Faders  (PnL@20≤0): {n_faders} ({n_faders/len(bulls)*100:.0f}%)")

    # ── Feature comparison ──
    features = ['tier', 'confidence', 'shakeout', 'fakeout', 'orb_width',
                'is_hold', 'pm_position', 'pm_accel', 'vix', 'path_eff',
                'brk_strength', 'brk_timing', 'brk_volume', 'brk_bar_range',
                'brk_close_pos', 'brk_vol_ratio']

    report_lines = []
    report_lines.append("# TSLA Open Scalper — Runner Identification Findings\n")
    report_lines.append(f"**Date:** 2026-03-19\n")
    report_lines.append(f"**Bull breakouts:** {len(bulls)} trades\n")
    report_lines.append(f"**Runners (PnL@20>0):** {n_runners} ({n_runners/len(bulls)*100:.0f}%)")
    report_lines.append(f"**Faders (PnL@20<=0):** {n_faders} ({n_faders/len(bulls)*100:.0f}%)\n")

    # Baselines
    m3_all = score_trades(trades3)
    m3_bull = score_trades(bulls3)
    m20_bull = score_trades(bulls20)
    report_lines.append("## Baselines\n")
    report_lines.append(f"| Strategy | N | Win% | Avg PnL | Total PnL | Sharpe |")
    report_lines.append(f"|----------|---|------|---------|-----------|--------|")
    report_lines.append(f"| All trades hold=3 | {m3_all['n']} | {m3_all['win_pct']} | ${m3_all['avg_pnl']} | ${m3_all['total_pnl']} | {m3_all['sharpe']} |")
    report_lines.append(f"| Bulls hold=3 | {m3_bull['n']} | {m3_bull['win_pct']} | ${m3_bull['avg_pnl']} | ${m3_bull['total_pnl']} | {m3_bull['sharpe']} |")
    report_lines.append(f"| Bulls hold=20 | {m20_bull['n']} | {m20_bull['win_pct']} | ${m20_bull['avg_pnl']} | ${m20_bull['total_pnl']} | {m20_bull['sharpe']} |")
    report_lines.append("")

    print("\n" + "="*70)
    print("FEATURE COMPARISON: Runners vs Faders")
    print("="*70)

    report_lines.append("## Feature Comparison: Runners vs Faders\n")
    report_lines.append("| Feature | Runners (mean) | Faders (mean) | Delta | p-value | Signal? |")
    report_lines.append("|---------|----------------|---------------|-------|---------|---------|")

    from scipy import stats

    feature_signals = {}
    for feat in features:
        if feat not in bulls.columns:
            continue
        col = bulls[feat]

        # Handle categorical
        if feat == 'tier':
            # Convert to numeric
            tier_map = {'HIGH': 2, 'MED': 1, 'LOW': 0}
            col = bulls['tier'].map(tier_map)
        elif col.dtype == bool or col.dtype == object:
            col = col.astype(float)

        r_vals = col[bulls['is_runner']]
        f_vals = col[~bulls['is_runner']]

        r_mean = r_vals.mean()
        f_mean = f_vals.mean()
        delta = r_mean - f_mean

        # t-test (drop NaN)
        r_clean = r_vals.dropna()
        f_clean = f_vals.dropna()
        if len(r_clean) >= 5 and len(f_clean) >= 5:
            tstat, pval = stats.ttest_ind(r_clean, f_clean, equal_var=False)
        else:
            pval = 1.0

        sig = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""
        feature_signals[feat] = {'r_mean': r_mean, 'f_mean': f_mean, 'delta': delta, 'pval': pval, 'sig': sig}

        line = f"| {feat:<16} | {r_mean:>10.3f} | {f_mean:>10.3f} | {delta:>+7.3f} | {pval:.4f} | {sig:>3} |"
        report_lines.append(line)
        print(f"  {feat:<16}  R={r_mean:>8.3f}  F={f_mean:>8.3f}  d={delta:>+7.3f}  p={pval:.4f} {sig}")

    report_lines.append("")

    # ── Detailed breakdowns for top features ──
    print("\n" + "="*70)
    print("DETAILED BREAKDOWNS")
    print("="*70)

    report_lines.append("## Detailed Breakdowns\n")

    # Confidence breakdown
    report_lines.append("### By Confidence Score\n")
    report_lines.append("| Confidence | N | Runner% | Avg PnL@3 | Avg PnL@20 |")
    report_lines.append("|------------|---|---------|-----------|------------|")
    print("\nBy Confidence:")
    for c in sorted(bulls['confidence'].unique()):
        sub = bulls[bulls['confidence'] == c]
        rr = sub['is_runner'].mean() * 100
        avg3 = sub['pnl_3'].mean()
        avg20 = sub['pnl_20'].mean()
        print(f"  conf={c}: n={len(sub):>3}, runner%={rr:.0f}%, avg@3=${avg3:.2f}, avg@20=${avg20:.2f}")
        report_lines.append(f"| {c} | {len(sub)} | {rr:.0f}% | ${avg3:.2f} | ${avg20:.2f} |")
    report_lines.append("")

    # Tier breakdown
    report_lines.append("### By Tier\n")
    report_lines.append("| Tier | N | Runner% | Avg PnL@3 | Avg PnL@20 |")
    report_lines.append("|------|---|---------|-----------|------------|")
    print("\nBy Tier:")
    for t in ['HIGH', 'MED']:
        sub = bulls[bulls['tier'] == t]
        if len(sub) == 0:
            continue
        rr = sub['is_runner'].mean() * 100
        avg3 = sub['pnl_3'].mean()
        avg20 = sub['pnl_20'].mean()
        print(f"  {t}: n={len(sub):>3}, runner%={rr:.0f}%, avg@3=${avg3:.2f}, avg@20=${avg20:.2f}")
        report_lines.append(f"| {t} | {len(sub)} | {rr:.0f}% | ${avg3:.2f} | ${avg20:.2f} |")
    report_lines.append("")

    # Shakeout
    report_lines.append("### By Shakeout\n")
    report_lines.append("| Shakeout | N | Runner% | Avg PnL@3 | Avg PnL@20 |")
    report_lines.append("|----------|---|---------|-----------|------------|")
    print("\nBy Shakeout:")
    for s in [False, True]:
        sub = bulls[bulls['shakeout'] == s]
        if len(sub) == 0:
            continue
        rr = sub['is_runner'].mean() * 100
        avg3 = sub['pnl_3'].mean()
        avg20 = sub['pnl_20'].mean()
        print(f"  shakeout={s}: n={len(sub):>3}, runner%={rr:.0f}%, avg@3=${avg3:.2f}, avg@20=${avg20:.2f}")
        report_lines.append(f"| {s} | {len(sub)} | {rr:.0f}% | ${avg3:.2f} | ${avg20:.2f} |")
    report_lines.append("")

    # is_hold (5m rule)
    report_lines.append("### By 5m Hold Rule\n")
    report_lines.append("| is_hold | N | Runner% | Avg PnL@3 | Avg PnL@20 |")
    report_lines.append("|---------|---|---------|-----------|------------|")
    print("\nBy 5m Hold Rule:")
    for h in [False, True]:
        sub = bulls[bulls['is_hold'] == h]
        if len(sub) == 0:
            continue
        rr = sub['is_runner'].mean() * 100
        avg3 = sub['pnl_3'].mean()
        avg20 = sub['pnl_20'].mean()
        print(f"  is_hold={h}: n={len(sub):>3}, runner%={rr:.0f}%, avg@3=${avg3:.2f}, avg@20=${avg20:.2f}")
        report_lines.append(f"| {h} | {len(sub)} | {rr:.0f}% | ${avg3:.2f} | ${avg20:.2f} |")
    report_lines.append("")

    # ORB width quantiles
    report_lines.append("### By ORB Width Quartile\n")
    report_lines.append("| Quartile | Range | N | Runner% | Avg PnL@20 |")
    report_lines.append("|----------|-------|---|---------|------------|")
    print("\nBy ORB Width Quartile:")
    bulls['orb_q'] = pd.qcut(bulls['orb_width'], 4, labels=['Q1','Q2','Q3','Q4'], duplicates='drop')
    for q in ['Q1','Q2','Q3','Q4']:
        sub = bulls[bulls['orb_q'] == q]
        if len(sub) == 0:
            continue
        rr = sub['is_runner'].mean() * 100
        avg20 = sub['pnl_20'].mean()
        lo, hi = sub['orb_width'].min(), sub['orb_width'].max()
        print(f"  {q} (${lo:.1f}-${hi:.1f}): n={len(sub):>3}, runner%={rr:.0f}%, avg@20=${avg20:.2f}")
        report_lines.append(f"| {q} | ${lo:.1f}-${hi:.1f} | {len(sub)} | {rr:.0f}% | ${avg20:.2f} |")
    report_lines.append("")

    # Breakout strength quantiles
    if 'brk_strength' in bulls.columns and bulls['brk_strength'].notna().sum() > 10:
        report_lines.append("### By Breakout Strength Quartile\n")
        report_lines.append("| Quartile | Range | N | Runner% | Avg PnL@20 |")
        report_lines.append("|----------|-------|---|---------|------------|")
        print("\nBy Breakout Strength Quartile:")
        valid = bulls[bulls['brk_strength'].notna()].copy()
        valid['str_q'] = pd.qcut(valid['brk_strength'], 4, labels=['Q1','Q2','Q3','Q4'], duplicates='drop')
        for q in ['Q1','Q2','Q3','Q4']:
            sub = valid[valid['str_q'] == q]
            if len(sub) == 0:
                continue
            rr = sub['is_runner'].mean() * 100
            avg20 = sub['pnl_20'].mean()
            lo, hi = sub['brk_strength'].min(), sub['brk_strength'].max()
            print(f"  {q} (${lo:.2f}-${hi:.2f}): n={len(sub):>3}, runner%={rr:.0f}%, avg@20=${avg20:.2f}")
            report_lines.append(f"| {q} | ${lo:.2f}-${hi:.2f} | {len(sub)} | {rr:.0f}% | ${avg20:.2f} |")
        report_lines.append("")

    # Breakout timing
    if 'brk_timing' in bulls.columns and bulls['brk_timing'].notna().sum() > 10:
        report_lines.append("### By Breakout Timing\n")
        report_lines.append("| Timing | N | Runner% | Avg PnL@20 |")
        report_lines.append("|--------|---|---------|------------|")
        print("\nBy Breakout Timing (mins from 9:35):")
        bins = [(-1, 0), (1, 3), (4, 10), (11, 20)]
        labels = ['9:35 (0m)', '9:36-38 (1-3m)', '9:39-45 (4-10m)', '9:46-55 (11-20m)']
        for (lo, hi), label in zip(bins, labels):
            sub = bulls[(bulls['brk_timing'] >= lo) & (bulls['brk_timing'] <= hi)]
            if len(sub) == 0:
                continue
            rr = sub['is_runner'].mean() * 100
            avg20 = sub['pnl_20'].mean()
            print(f"  {label}: n={len(sub):>3}, runner%={rr:.0f}%, avg@20=${avg20:.2f}")
            report_lines.append(f"| {label} | {len(sub)} | {rr:.0f}% | ${avg20:.2f} |")
        report_lines.append("")

    # Volume ratio
    if 'brk_vol_ratio' in bulls.columns and bulls['brk_vol_ratio'].notna().sum() > 10:
        report_lines.append("### By Breakout Volume Ratio (vs ORB avg)\n")
        report_lines.append("| Quartile | Range | N | Runner% | Avg PnL@20 |")
        report_lines.append("|----------|-------|---|---------|------------|")
        print("\nBy Breakout Vol Ratio:")
        valid = bulls[bulls['brk_vol_ratio'].notna()].copy()
        valid['vr_q'] = pd.qcut(valid['brk_vol_ratio'], 4, labels=['Q1','Q2','Q3','Q4'], duplicates='drop')
        for q in ['Q1','Q2','Q3','Q4']:
            sub = valid[valid['vr_q'] == q]
            if len(sub) == 0:
                continue
            rr = sub['is_runner'].mean() * 100
            avg20 = sub['pnl_20'].mean()
            lo, hi = sub['brk_vol_ratio'].min(), sub['brk_vol_ratio'].max()
            print(f"  {q} ({lo:.2f}-{hi:.2f}x): n={len(sub):>3}, runner%={rr:.0f}%, avg@20=${avg20:.2f}")
            report_lines.append(f"| {q} | {lo:.2f}-{hi:.2f}x | {len(sub)} | {rr:.0f}% | ${avg20:.2f} |")
        report_lines.append("")

    # pm_position
    if bulls['pm_position'].notna().sum() > 10:
        report_lines.append("### By PM Position Quartile\n")
        report_lines.append("| Quartile | Range | N | Runner% | Avg PnL@20 |")
        report_lines.append("|----------|-------|---|---------|------------|")
        print("\nBy PM Position:")
        valid = bulls[bulls['pm_position'].notna()].copy()
        valid['pm_q'] = pd.qcut(valid['pm_position'], 4, labels=['Q1','Q2','Q3','Q4'], duplicates='drop')
        for q in ['Q1','Q2','Q3','Q4']:
            sub = valid[valid['pm_q'] == q]
            if len(sub) == 0:
                continue
            rr = sub['is_runner'].mean() * 100
            avg20 = sub['pnl_20'].mean()
            lo, hi = sub['pm_position'].min(), sub['pm_position'].max()
            print(f"  {q} ({lo:.3f}-{hi:.3f}): n={len(sub):>3}, runner%={rr:.0f}%, avg@20=${avg20:.2f}")
            report_lines.append(f"| {q} | {lo:.3f}-{hi:.3f} | {len(sub)} | {rr:.0f}% | ${avg20:.2f} |")
        report_lines.append("")

    # ── BUILD RUNNER SCORE (v2 — data-driven) ──
    print("\n" + "="*70)
    print("BUILDING RUNNER SCORE (v2)")
    print("="*70)

    report_lines.append("## Runner Score Model (v2 — data-driven)\n")
    report_lines.append("Only components where runner% when True > baseline 75%.\n")

    bulls['runner_score'] = 0
    score_components = {}

    # 1. Early breakout: timing <= 3 (90% runner at 9:35, 73% at 9:36-38)
    #    This is the ONLY statistically significant feature (p=0.05)
    comp = 'brk_timing<=3 (before 9:39)'
    mask = bulls['brk_timing'] <= 3
    bulls.loc[mask, 'runner_score'] += 1
    r_rate = bulls.loc[mask, 'is_runner'].mean() if mask.sum() > 0 else 0
    score_components[comp] = {'n': mask.sum(), 'runner%': r_rate*100}

    # 2. is_hold = True: 81% runner, $5.57 avg@20 vs $1.29 without
    comp = 'is_hold=True (5m rule)'
    mask = bulls['is_hold'] == True
    bulls.loc[mask, 'runner_score'] += 1
    r_rate = bulls.loc[mask, 'is_runner'].mean() if mask.sum() > 0 else 0
    score_components[comp] = {'n': mask.sum(), 'runner%': r_rate*100}

    # 3. Confidence >= 4: 82% runner rate
    comp = 'confidence>=4'
    mask = bulls['confidence'] >= 4
    bulls.loc[mask, 'runner_score'] += 1
    r_rate = bulls.loc[mask, 'is_runner'].mean() if mask.sum() > 0 else 0
    score_components[comp] = {'n': mask.sum(), 'runner%': r_rate*100}

    # 4. Wide ORB (Q4: >= P75): 86% runner, $8.33 avg
    orb_p75 = bulls['orb_width'].quantile(0.75)
    comp = f'orb_width>=P75 (${orb_p75:.1f})'
    mask = bulls['orb_width'] >= orb_p75
    bulls.loc[mask, 'runner_score'] += 1
    r_rate = bulls.loc[mask, 'is_runner'].mean() if mask.sum() > 0 else 0
    score_components[comp] = {'n': mask.sum(), 'runner%': r_rate*100}

    # EXCLUDED (data shows these don't discriminate or hurt):
    # - shakeout: n=4, same 75% rate as baseline → noise
    # - brk_strength>median: 64% runner → WORSE than baseline
    # - pm_position>0.5: 70% → worse than baseline
    # - pm_accel>0: 79% → marginal, not worth complexity

    report_lines.append("### Score Components (each +1 point)\n")
    report_lines.append("| Component | N (True) | Runner% when True |")
    report_lines.append("|-----------|----------|-------------------|")
    print("\nScore Components:")
    for comp, vals in score_components.items():
        print(f"  {comp}: n={vals['n']}, runner%={vals['runner%']:.0f}%")
        report_lines.append(f"| {comp} | {vals['n']} | {vals['runner%']:.0f}% |")
    report_lines.append("")

    # Score distribution
    report_lines.append("### Score Distribution\n")
    report_lines.append("| Score | N | Runner% | Avg PnL@3 | Avg PnL@20 | Recommendation |")
    report_lines.append("|-------|---|---------|-----------|------------|----------------|")
    print("\nRunner Score Distribution:")
    for s in sorted(bulls['runner_score'].unique()):
        sub = bulls[bulls['runner_score'] == s]
        rr = sub['is_runner'].mean() * 100
        avg3 = sub['pnl_3'].mean()
        avg20 = sub['pnl_20'].mean()
        rec = "HOLD 20" if rr >= 80 else "HOLD 3" if rr < 70 else "BORDERLINE"
        print(f"  score={s}: n={len(sub):>3}, runner%={rr:.0f}%, avg@3=${avg3:.2f}, avg@20=${avg20:.2f} → {rec}")
        report_lines.append(f"| {s} | {len(sub)} | {rr:.0f}% | ${avg3:.2f} | ${avg20:.2f} | {rec} |")
    report_lines.append("")

    # ── BACKTEST ADAPTIVE STRATEGY ──
    print("\n" + "="*70)
    print("ADAPTIVE STRATEGY BACKTEST")
    print("="*70)

    report_lines.append("## Adaptive Strategy Backtest\n")
    report_lines.append("For each threshold T: if runner_score >= T, hold 20 bars; else hold 3.\n")
    report_lines.append("| Threshold | N@20 | N@3 | Total PnL | Avg PnL | Win% | Sharpe |")
    report_lines.append("|-----------|------|-----|-----------|---------|------|--------|")

    # Baseline: all hold=3
    all_pnl_3 = trades3['pnl']
    all_pnl_20 = trades20['pnl']

    base3_total = all_pnl_3.sum()
    base3_avg = all_pnl_3.mean()
    base3_win = (all_pnl_3 > 0).mean() * 100
    base3_sharpe = all_pnl_3.mean() / all_pnl_3.std() * np.sqrt(252) if all_pnl_3.std() > 0 else 0

    base20_total = all_pnl_20.sum()
    base20_avg = all_pnl_20.mean()
    base20_win = (all_pnl_20 > 0).mean() * 100
    base20_sharpe = all_pnl_20.mean() / all_pnl_20.std() * np.sqrt(252) if all_pnl_20.std() > 0 else 0

    print(f"  Flat hold=3:  total=${base3_total:.2f}, avg=${base3_avg:.2f}, win={base3_win:.0f}%, sharpe={base3_sharpe:.2f}")
    print(f"  Flat hold=20: total=${base20_total:.2f}, avg=${base20_avg:.2f}, win={base20_win:.0f}%, sharpe={base20_sharpe:.2f}")
    report_lines.append(f"| Flat hold=3 | 0 | {len(trades3)} | ${base3_total:.2f} | ${base3_avg:.2f} | {base3_win:.0f}% | {base3_sharpe:.2f} |")
    report_lines.append(f"| Flat hold=20 | {len(trades20)} | 0 | ${base20_total:.2f} | ${base20_avg:.2f} | {base20_win:.0f}% | {base20_sharpe:.2f} |")

    best_threshold = None
    best_total = base3_total
    best_sharpe = base3_sharpe

    for threshold in range(1, 8):
        # Build adaptive PnL: start with hold=3, upgrade bulls with score >= threshold to hold=20
        pnls = trades3['pnl'].copy()
        runner_mask = bulls['runner_score'] >= threshold
        if runner_mask.sum() == 0:
            continue
        # Get the original indices (in trades3) for these bulls
        bull_orig_idx = trades3[trades3['breakout_type'] == 'BULL'].index
        runner_orig_idx = bull_orig_idx[runner_mask.values]
        pnls.loc[runner_orig_idx] = trades20.loc[runner_orig_idx, 'pnl']

        n20 = runner_mask.sum()
        n3 = len(trades3) - n20
        total = pnls.sum()
        avg = pnls.mean()
        win = (pnls > 0).mean() * 100
        sharpe = pnls.mean() / pnls.std() * np.sqrt(252) if pnls.std() > 0 else 0

        if total > best_total:
            best_total = total
            best_threshold = threshold
            best_sharpe = sharpe

        print(f"  T>={threshold}: n@20={n20:>3}, n@3={n3:>3}, total=${total:.2f}, avg=${avg:.2f}, win={win:.0f}%, sharpe={sharpe:.2f}")
        report_lines.append(f"| score >= {threshold} | {n20} | {n3} | ${total:.2f} | ${avg:.2f} | {win:.0f}% | {sharpe:.2f} |")

    report_lines.append("")

    # ── Summary ──
    report_lines.append("## Summary and Recommendation\n")

    if best_threshold is not None:
        pnl_gain = best_total - base3_total
        report_lines.append(f"**Best adaptive threshold:** runner_score >= {best_threshold}")
        report_lines.append(f"**PnL improvement vs flat hold=3:** ${pnl_gain:.2f} ({pnl_gain/abs(base3_total)*100:.0f}%)")
        report_lines.append(f"**Best Sharpe:** {best_sharpe:.2f}\n")
    else:
        report_lines.append("**No threshold improved on flat hold=3.**\n")

    report_lines.append("### Decision Rule for Pine Script\n")
    report_lines.append("```")
    report_lines.append(f"runner_score = 0")
    report_lines.append(f"if brk_timing <= 3min (before 9:39): runner_score += 1  // p=0.05, 90% at 9:35")
    report_lines.append(f"if is_hold (5m rule): runner_score += 1                 // 81% runner rate")
    report_lines.append(f"if confidence >= 4: runner_score += 1                   // 82% runner rate")
    report_lines.append(f"if orb_width >= ${orb_p75:.1f} (P75): runner_score += 1         // 86% runner, $8.33 avg")
    if best_threshold:
        report_lines.append(f"\nif runner_score >= {best_threshold}: hold 20 bars (runner)")
        report_lines.append(f"else: hold 3 bars (quick scalp)")
    report_lines.append("```\n")

    # ── Key insight: is_hold + early timing combo ──
    combo = bulls[(bulls['is_hold'] == True) & (bulls['brk_timing'] <= 3)]
    if len(combo) > 0:
        combo_rr = combo['is_runner'].mean() * 100
        combo_avg20 = combo['pnl_20'].mean()
        report_lines.append(f"### Key Combo: is_hold + early timing")
        report_lines.append(f"- N={len(combo)}, Runner%={combo_rr:.0f}%, Avg PnL@20=${combo_avg20:.2f}")
        report_lines.append(f"- This is the simplest 2-feature gate with strong signal.\n")

    # Write report
    report_path = REPO / 'debug' / 'tsla-runner-findings.md'
    report_path.write_text('\n'.join(report_lines))
    print(f"\nReport written to {report_path}")


if __name__ == '__main__':
    main()
