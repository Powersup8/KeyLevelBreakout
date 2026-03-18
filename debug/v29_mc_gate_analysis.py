"""
v29 MC 9:50 Gate Analysis
=========================
Analyzes the impact of a hypothetical 9:50 ET time gate on MC (Momentum Cascade) signals.

Questions answered:
1. How many MC signals fire before/after 9:50?
2. Of pre-9:50 MC, how many are "correct" (match 30-min direction)?
3. MFE/MAE for pre vs post 9:50 MC-confirmed trades
4. Trade simulation P&L pre vs post 9:50
5. Oracle scenario — keep only the correct signal from each opposing pair
6. Slot recovery — how many post-9:50 MC signals would we gain if we delayed?

Data sources:
- debug/v28a-signals.csv       — 11K+ parsed signals
- debug/v28a-mc-opposing-pairs.csv — 126 opposing pairs
- debug/v28a-follow-through.csv   — MFE/MAE (BRK/REV/VWAP only, no MC type)
- debug/v28a-trades.csv           — simulated trades (has QBS/MC conf_source)
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent

# ── Helpers ──────────────────────────────────────────────────────────────
def time_to_min(t):
    """Convert 'H:MM' or 'HH:MM' to minutes since midnight."""
    parts = str(t).split(':')
    return int(parts[0]) * 60 + int(parts[1])

GATE_MIN = 9 * 60 + 50  # 9:50 ET = 590 minutes

def before_gate(t):
    return time_to_min(t) < GATE_MIN

def load_csv(name):
    return pd.read_csv(BASE / name)


# ── Load data ────────────────────────────────────────────────────────────
sig = load_csv('v28a-signals.csv')
pairs = load_csv('v28a-mc-opposing-pairs.csv')
ft = load_csv('v28a-follow-through.csv')
trades = load_csv('v28a-trades.csv')

# ── 1. MC signal counts before/after 9:50 ───────────────────────────────
mc = sig[sig['line_type'] == 'MC'].copy()
mc['before_gate'] = mc['time'].apply(before_gate)
mc['date'] = mc['datetime'].str[:10]

n_before = mc['before_gate'].sum()
n_after = (~mc['before_gate']).sum()
n_total = len(mc)

# Per-time breakdown
time_counts = mc['time'].value_counts().sort_index()

# Per symbol-day: how many have 1 vs 2 MC signals
day_groups = mc.groupby(['symbol', 'date'])
day_counts = day_groups.size()
days_with_2 = (day_counts == 2).sum()
days_with_1 = (day_counts == 1).sum()

# Days with opposing directions
day_dirs = day_groups['direction'].apply(lambda x: set(x))
days_opposing = (day_dirs.apply(len) == 2).sum()

print("=" * 70)
print("1. MC SIGNAL COUNTS")
print("=" * 70)
print(f"Total MC signals:     {n_total}")
print(f"Before 9:50:          {n_before} ({n_before/n_total:.1%})")
print(f"After 9:50:           {n_after} ({n_after/n_total:.1%})")
print(f"\nTime breakdown:")
for t, c in time_counts.items():
    marker = " <-- after 9:50" if not before_gate(t) else ""
    print(f"  {t:>5}: {c:>4}{marker}")
print(f"\nSymbol-days with 1 MC: {days_with_1}")
print(f"Symbol-days with 2 MC: {days_with_2}")
print(f"Symbol-days with opposing dirs: {days_opposing}")


# ── 2. Accuracy of pre-9:50 MC signals (from opposing pairs) ────────────
pairs['first_min'] = pairs['first_time'].apply(time_to_min)
pairs['second_min'] = pairs['second_time'].apply(time_to_min)

# All 126 pairs have both signals before 9:50
pairs_before_gate = pairs[(pairs['first_min'] < GATE_MIN) & (pairs['second_min'] < GATE_MIN)]

first_correct_rate = pairs['first_correct'].mean()
second_correct_rate = pairs['second_correct'].mean()

# First signal is usually the earliest (9:30/9:35), second is later (9:40/9:45)
# "first_correct" means the first signal matched the actual 30-min direction

# How often is NEITHER correct? (both wrong = move was flat)
neither_correct = ((~pairs['first_correct']) & (~pairs['second_correct'])).sum()
both_correct = (pairs['first_correct'] & pairs['second_correct']).sum()

# Direction analysis of first signals
first_bull = (pairs['first_dir'] == 'bull').sum()
first_bear = (pairs['first_dir'] == 'bear').sum()

# Accuracy by first signal time
for t in sorted(pairs['first_time'].unique()):
    subset = pairs[pairs['first_time'] == t]
    print_later = (t, len(subset), subset['first_correct'].mean(), subset['second_correct'].mean())

print(f"\n{'=' * 70}")
print("2. OPPOSING PAIR ACCURACY (n=126 pairs)")
print("=" * 70)
print(f"All 126 pairs: both signals fire before 9:50")
print(f"\nFirst signal correct:  {pairs['first_correct'].sum()}/{len(pairs)} ({first_correct_rate:.1%})")
print(f"Second signal correct: {pairs['second_correct'].sum()}/{len(pairs)} ({second_correct_rate:.1%})")
print(f"Neither correct:       {neither_correct}/{len(pairs)} ({neither_correct/len(pairs):.1%})")
print(f"Both correct (flat):   {both_correct}/{len(pairs)} ({both_correct/len(pairs):.1%})")
print(f"\nFirst signal dir: bull={first_bull}, bear={first_bear}")
print(f"\nAccuracy by first_time:")
for t in sorted(pairs['first_time'].unique()):
    subset = pairs[pairs['first_time'] == t]
    print(f"  {t}: n={len(subset):>3}, 1st correct={subset['first_correct'].mean():.1%}, "
          f"2nd correct={subset['second_correct'].mean():.1%}")

# Accuracy by second_time
print(f"\nAccuracy by second_time:")
for t in sorted(pairs['second_time'].unique()):
    subset = pairs[pairs['second_time'] == t]
    print(f"  {t}: n={len(subset):>3}, 1st correct={subset['first_correct'].mean():.1%}, "
          f"2nd correct={subset['second_correct'].mean():.1%}")

# Move magnitude analysis
pairs['abs_move'] = pairs['move_30m'].abs()
correct_first = pairs[pairs['first_correct']]
correct_second = pairs[pairs['second_correct'] & ~pairs['first_correct']]
print(f"\n30-min move magnitude:")
print(f"  When 1st correct: avg |move| = {correct_first['abs_move'].mean():.2f} ATR")
print(f"  When 2nd correct: avg |move| = {correct_second['abs_move'].mean():.2f} ATR")
print(f"  When neither:     avg |move| = {pairs[~pairs['first_correct'] & ~pairs['second_correct']]['abs_move'].mean():.2f} ATR")

# ── 3. MFE/MAE for MC-confirmed trades pre vs post 9:50 ─────────────────
# MC signals don't have their own follow-through in the FT CSV (only BRK/REV/VWAP).
# But trades CSV has MC-confirmed trades with mfe_atr and pnl_atr.
mc_trades = trades[trades['conf_source'] == 'QBS/MC'].copy()
mc_trades['before_gate'] = mc_trades['time'].apply(before_gate)

# Also tag by conf_time (when the MC CONF event fired)
import re
def extract_hhmm(ts):
    m = re.search(r'T(\d{2}:\d{2})', str(ts))
    return m.group(1) if m else '00:00'

mc_trades['conf_hhmm'] = mc_trades['conf_time'].apply(extract_hhmm)
mc_trades['conf_before_gate'] = mc_trades['conf_hhmm'].apply(
    lambda t: time_to_min(t) < GATE_MIN
)

# Split by signal time (when the BRK happened that was confirmed by MC)
pre_trades = mc_trades[mc_trades['before_gate']]
post_trades = mc_trades[~mc_trades['before_gate']]

print(f"\n{'=' * 70}")
print("3. MC-CONFIRMED TRADE MFE/MAE (by signal_time)")
print("=" * 70)
for label, subset in [("Before 9:50", pre_trades), ("After 9:50", post_trades), ("All", mc_trades)]:
    if len(subset) == 0:
        print(f"\n{label}: no trades")
        continue
    print(f"\n{label} (n={len(subset)}):")
    print(f"  Avg MFE (ATR):  {subset['mfe_atr'].mean():.4f}")
    print(f"  Avg PnL (ATR):  {subset['pnl_atr'].mean():.4f}")
    print(f"  Total PnL (ATR): {subset['pnl_atr'].sum():.2f}")
    print(f"  Win rate:        {(subset['pnl_atr'] > 0).mean():.1%}")
    print(f"  Avg winner:      {subset[subset['pnl_atr']>0]['pnl_atr'].mean():.4f}" if (subset['pnl_atr']>0).any() else "  No winners")
    print(f"  Avg loser:       {subset[subset['pnl_atr']<=0]['pnl_atr'].mean():.4f}" if (subset['pnl_atr']<=0).any() else "  No losers")

# Also split by conf time (when MC CONF itself fired, which is typically 9:35-9:45)
pre_conf_trades = mc_trades[mc_trades['conf_before_gate']]
post_conf_trades = mc_trades[~mc_trades['conf_before_gate']]

print(f"\n--- By conf_time (when MC auto-confirmed) ---")
for label, subset in [("CONF before 9:50", pre_conf_trades), ("CONF after 9:50", post_conf_trades)]:
    if len(subset) == 0:
        print(f"\n{label}: no trades")
        continue
    print(f"\n{label} (n={len(subset)}):")
    print(f"  Avg MFE (ATR):  {subset['mfe_atr'].mean():.4f}")
    print(f"  Avg PnL (ATR):  {subset['pnl_atr'].mean():.4f}")
    print(f"  Total PnL (ATR): {subset['pnl_atr'].sum():.2f}")
    print(f"  Win rate:        {(subset['pnl_atr'] > 0).mean():.1%}")


# ── 4. Trade P&L breakdown ──────────────────────────────────────────────
print(f"\n{'=' * 70}")
print("4. MC TRADE P&L BREAKDOWN")
print("=" * 70)

# By time buckets
mc_trades['time_min'] = mc_trades['time'].apply(time_to_min)
buckets = [
    ("9:30-9:39", 570, 580),
    ("9:40-9:49", 580, 590),
    ("9:50-9:59", 590, 600),
    ("10:00-10:29", 600, 630),
    ("10:30-10:59", 630, 660),
    ("11:00-11:59", 660, 720),
    ("12:00+", 720, 1440),
]
print(f"\n{'Bucket':<14} {'N':>4} {'Total PnL':>10} {'Avg PnL':>9} {'Avg MFE':>9} {'Win%':>6}")
print("-" * 56)
for label, lo, hi in buckets:
    b = mc_trades[(mc_trades['time_min'] >= lo) & (mc_trades['time_min'] < hi)]
    if len(b) == 0:
        continue
    print(f"{label:<14} {len(b):>4} {b['pnl_atr'].sum():>10.2f} {b['pnl_atr'].mean():>9.4f} "
          f"{b['mfe_atr'].mean():>9.4f} {(b['pnl_atr']>0).mean():>6.1%}")

# Exit reason breakdown
print(f"\nExit reasons:")
for reason, grp in mc_trades.groupby('exit_reason'):
    print(f"  {reason:<15}: n={len(grp):>3}, avg PnL={grp['pnl_atr'].mean():.4f}")

# By direction
print(f"\nBy direction:")
for d, grp in mc_trades.groupby('direction'):
    print(f"  {d:<5}: n={len(grp):>3}, total PnL={grp['pnl_atr'].sum():.2f}, "
          f"avg PnL={grp['pnl_atr'].mean():.4f}, win%={( grp['pnl_atr']>0).mean():.1%}")


# ── 5. Oracle scenario — keep only the correct signal from each pair ─────
print(f"\n{'=' * 70}")
print("5. ORACLE SCENARIO — KEEP ONLY THE CORRECT MC SIGNAL")
print("=" * 70)

# For each of the 126 pairs, we know which direction was correct
# We need to find trades that were confirmed by the WRONG MC signal and remove them,
# while finding trades that WOULD have been confirmed by the correct MC signal.

# First, let's understand: each pair has a symbol+date. The MC fires bull and bear.
# Currently both signals fire, and BOTH can confirm subsequent BRK signals.
# In oracle mode, only the correct direction's MC fires.

# Tag each MC signal with its pair info
pairs['date_str'] = pairs['date']
mc_with_pairs = mc.merge(
    pairs[['symbol', 'date_str', 'first_dir', 'second_dir', 'actual_dir', 'first_correct', 'second_correct']],
    left_on=['symbol', 'date'],
    right_on=['symbol', 'date_str'],
    how='left'
)

# MC signals that are part of a pair: both fire, one is wrong
mc_in_pair = mc_with_pairs[mc_with_pairs['date_str'].notna()].copy()
mc_correct = mc_in_pair[mc_in_pair['direction'] == mc_in_pair['actual_dir']]
mc_wrong = mc_in_pair[mc_in_pair['direction'] != mc_in_pair['actual_dir']]

print(f"MC signals in opposing pairs: {len(mc_in_pair)}")
print(f"  Correct direction: {len(mc_correct)}")
print(f"  Wrong direction:   {len(mc_wrong)}")

# What trades were confirmed by wrong MC direction?
# We need to match trades to their confirming MC signal's direction
# The trade has conf_source=QBS/MC, and direction = trade direction
# If the trade direction matches the WRONG MC direction for that symbol+date, it's a bad confirm

mc_trades_with_pair = mc_trades.copy()
mc_trades_with_pair['date'] = mc_trades_with_pair['signal_time'].str[:10]

mc_trades_paired = mc_trades_with_pair.merge(
    pairs[['symbol', 'date_str', 'actual_dir', 'first_dir', 'second_dir']],
    left_on=['symbol', 'date'],
    right_on=['symbol', 'date_str'],
    how='left'
)

# Trades from days with opposing pairs
paired_trades = mc_trades_paired[mc_trades_paired['date_str'].notna()]
unpaired_trades = mc_trades_paired[mc_trades_paired['date_str'].isna()]

# Among paired trades, which were confirmed in the correct direction?
# The MC CONF applies to any BRK signal regardless of direction... but the BRK direction IS the trade direction
# So a bull BRK on a day where actual_dir=bear means the trade was against the 30-min flow
paired_trades_correct = paired_trades[paired_trades['direction'] == paired_trades['actual_dir']]
paired_trades_wrong = paired_trades[paired_trades['direction'] != paired_trades['actual_dir']]

print(f"\nMC-confirmed trades on pair days: {len(paired_trades)}")
print(f"  Trade dir = actual (correct): {len(paired_trades_correct)}, "
      f"total PnL={paired_trades_correct['pnl_atr'].sum():.2f}, "
      f"avg={paired_trades_correct['pnl_atr'].mean():.4f}")
print(f"  Trade dir != actual (wrong):  {len(paired_trades_wrong)}, "
      f"total PnL={paired_trades_wrong['pnl_atr'].sum():.2f}, "
      f"avg={paired_trades_wrong['pnl_atr'].mean():.4f}")
print(f"\nTrades on non-pair days: {len(unpaired_trades)}, "
      f"total PnL={unpaired_trades['pnl_atr'].sum():.2f}")

# Oracle P&L = keep correct-dir trades on pair days + all non-pair-day trades
oracle_pnl = paired_trades_correct['pnl_atr'].sum() + unpaired_trades['pnl_atr'].sum()
actual_pnl = mc_trades['pnl_atr'].sum()
removed_pnl = paired_trades_wrong['pnl_atr'].sum()

print(f"\n--- Oracle P&L Impact ---")
print(f"Current total MC PnL:  {actual_pnl:.2f} ATR")
print(f"Oracle total MC PnL:   {oracle_pnl:.2f} ATR (remove wrong-dir trades)")
print(f"Removed trades PnL:    {removed_pnl:.2f} ATR")
print(f"Oracle improvement:    {oracle_pnl - actual_pnl:.2f} ATR")

# Oracle MFE analysis
print(f"\nOracle MFE comparison:")
print(f"  Correct-dir trades: avg MFE={paired_trades_correct['mfe_atr'].mean():.4f}, "
      f"win%={(paired_trades_correct['pnl_atr']>0).mean():.1%}")
print(f"  Wrong-dir trades:   avg MFE={paired_trades_wrong['mfe_atr'].mean():.4f}, "
      f"win%={(paired_trades_wrong['pnl_atr']>0).mean():.1%}")


# ── 6. Slot recovery — what MC signals would fire after 9:50? ────────────
print(f"\n{'=' * 70}")
print("6. SLOT RECOVERY — MC SIGNALS BLOCKED BY EARLY FIRING")
print("=" * 70)

# MC is once-per-direction-per-session. If bull MC fires at 9:35 and bear MC at 9:40,
# both direction slots are burned. No more MC signals can fire that day for that symbol.
#
# If we delayed MC until 9:50, what would happen?
# We can't directly observe "blocked MC signals" — they never fire.
# But we CAN look at:
# a) How many days have both slots burned before 9:50 (= 126 pair days + some single-dir days)
# b) QBS signals (which are the OTHER volume pattern) — do they fire later?
# c) We can estimate: on pair days, if we kept only the correct signal,
#    the wrong direction's slot would be FREE for a later MC signal.

# Days where both directions burned before 9:50
mc_before = mc[mc['before_gate']].copy()
day_dir_before = mc_before.groupby(['symbol', 'date'])['direction'].apply(set)
both_burned = day_dir_before[day_dir_before.apply(len) == 2]
one_burned = day_dir_before[day_dir_before.apply(len) == 1]

print(f"Symbol-days with MC signals before 9:50:")
print(f"  Both slots burned:  {len(both_burned)}")
print(f"  One slot burned:    {len(one_burned)}")
print(f"  Total:              {len(both_burned) + len(one_burned)}")

# How many QBS signals fire (as a proxy for volume events)?
qbs = sig[sig['line_type'] == 'QBS'].copy()
qbs['before_gate'] = qbs['time'].apply(before_gate)
qbs['date'] = qbs['datetime'].str[:10]

print(f"\nQBS signals (for comparison):")
print(f"  Total:       {len(qbs)}")
print(f"  Before 9:50: {qbs['before_gate'].sum()}")
print(f"  After 9:50:  {(~qbs['before_gate']).sum()}")

# QBS signals after 9:50 — these show volume events DO happen later
qbs_after = qbs[~qbs['before_gate']]
print(f"\nQBS after 9:50 time distribution:")
for t in sorted(qbs_after['time'].unique()):
    c = len(qbs_after[qbs_after['time'] == t])
    print(f"  {t}: {c}")

# APPROACH: For slot recovery estimation, look at BRK signals confirmed by QBS/MC.
# If a BRK signal at 10:00 gets confirmed by an MC that fired at 9:35,
# in the "gate at 9:50" scenario, that MC wouldn't exist yet.
# Those BRK signals would LOSE their MC confirmation.
# HOWEVER, if a new MC fires at 9:50+ (because the slot wasn't burned), those same BRK signals
# might get confirmed by the later MC.

# Let's count how many MC-confirmed trades have conf_time before 9:50 but signal_time after 9:50
# These trades would be LOST if we gated MC at 9:50 (their confirming MC wouldn't exist yet)
mc_trades_with_timing = mc_trades.copy()
mc_trades_with_timing['conf_before'] = mc_trades_with_timing['conf_hhmm'].apply(
    lambda t: time_to_min(t) < GATE_MIN
)
mc_trades_with_timing['signal_before'] = mc_trades_with_timing['before_gate']

# Trades where signal is after 9:50 but conf came from MC that fired before 9:50
late_signal_early_conf = mc_trades_with_timing[
    (~mc_trades_with_timing['signal_before']) & mc_trades_with_timing['conf_before']
]
early_signal_early_conf = mc_trades_with_timing[
    mc_trades_with_timing['signal_before'] & mc_trades_with_timing['conf_before']
]
late_signal_late_conf = mc_trades_with_timing[
    (~mc_trades_with_timing['signal_before']) & (~mc_trades_with_timing['conf_before'])
]

print(f"\n--- Trade Timing Matrix ---")
print(f"Signal <9:50 + CONF <9:50:  {len(early_signal_early_conf):>3} trades, "
      f"PnL={early_signal_early_conf['pnl_atr'].sum():.2f}")
print(f"Signal ≥9:50 + CONF <9:50:  {len(late_signal_early_conf):>3} trades, "
      f"PnL={late_signal_early_conf['pnl_atr'].sum():.2f}")
print(f"Signal ≥9:50 + CONF ≥9:50:  {len(late_signal_late_conf):>3} trades, "
      f"PnL={late_signal_late_conf['pnl_atr'].sum():.2f}")
print(f"(Signal <9:50 + CONF ≥9:50 is impossible for MC)")

# The "late_signal_early_conf" trades are the ones AT RISK if we gate MC.
# With a gate, those MC CONFs wouldn't exist. The question is whether a LATER MC
# would fire in their place and still confirm those BRK signals.

# Estimate: on the 339 days with 2 MC signals (both pre-9:50), if we block all pre-9:50 MC,
# how many "replacement" MC signals would fire at 9:50?
# We can't know for certain, but we can check: on days with only 1 MC before 9:50,
# does a 2nd MC ever fire after 9:50? (In current data, MC after 9:50 is only 7 signals.)

mc_after = mc[~mc['before_gate']]
print(f"\nMC signals currently firing after 9:50: {len(mc_after)}")
print(f"Their times: {mc_after['time'].value_counts().to_dict()}")

# On days with late MC, what happened before?
for _, row in mc_after.iterrows():
    sym, dt = row['symbol'], row['date']
    same_day_mc = mc[(mc['symbol'] == sym) & (mc['date'] == dt)]
    early = same_day_mc[same_day_mc['before_gate']]
    print(f"  {sym} {dt} late MC at {row['time']} dir={row['direction']}: "
          f"early MC count={len(early)}, dirs={list(early['direction'])}")


# ── 7. Summary statistics and gate scenarios ─────────────────────────────
print(f"\n{'=' * 70}")
print("7. GATE SCENARIO COMPARISON")
print("=" * 70)

# Scenario A: Status quo (no gate)
print(f"\nScenario A: NO GATE (current)")
print(f"  MC signals:     {n_total}")
print(f"  MC trades:      {len(mc_trades)}")
print(f"  Total PnL:      {mc_trades['pnl_atr'].sum():.2f} ATR")
print(f"  Avg PnL:        {mc_trades['pnl_atr'].mean():.4f} ATR")
print(f"  Win rate:        {(mc_trades['pnl_atr']>0).mean():.1%}")

# Scenario B: Hard gate at 9:50 — suppress all MC before 9:50
# Trades that lose MC confirmation: those with conf_before_gate=True
# (Some might still get BRK confirmation, but we're looking at MC-only impact)
trades_lost = mc_trades_with_timing[mc_trades_with_timing['conf_before']]
trades_kept = mc_trades_with_timing[~mc_trades_with_timing['conf_before']]
print(f"\nScenario B: HARD GATE AT 9:50 (suppress all MC before 9:50)")
print(f"  Trades lost (conf<9:50): {len(trades_lost)}, PnL={trades_lost['pnl_atr'].sum():.2f}")
print(f"  Trades kept (conf≥9:50): {len(trades_kept)}, PnL={trades_kept['pnl_atr'].sum():.2f}")
print(f"  Net MC PnL:              {trades_kept['pnl_atr'].sum():.2f} ATR")
print(f"  NOTE: This doesn't account for NEW MC signals that would fire at 9:50+")

# Scenario C: Oracle — on pair days, only the correct MC fires
print(f"\nScenario C: ORACLE (pair days: keep only correct direction)")
print(f"  Oracle PnL:       {oracle_pnl:.2f} ATR")
print(f"  vs current:       {oracle_pnl - actual_pnl:+.2f} ATR")

# Scenario D: Gate at 9:50 + first signal only (delay to 9:50, then fire one direction)
# This is the most practical: wait until 9:50, check which direction has more evidence, fire once
# Estimated improvement = difference between wrong-dir and correct-dir trades on pair days
print(f"\nScenario D: WAIT UNTIL 9:50 (pick direction with more evidence)")
print(f"  Pair-day wrong-dir trade PnL:   {paired_trades_wrong['pnl_atr'].sum():.2f} ATR removed")
print(f"  Pair-day correct-dir trade PnL: {paired_trades_correct['pnl_atr'].sum():.2f} ATR kept")
print(f"  Estimated net gain:             {-paired_trades_wrong['pnl_atr'].sum():+.2f} ATR")
print(f"  (Assumes we can pick the right direction ~55% of time based on 30m momentum)")


# ── 8. Per-symbol breakdown ─────────────────────────────────────────────
print(f"\n{'=' * 70}")
print("8. PER-SYMBOL MC BREAKDOWN")
print("=" * 70)
print(f"{'Symbol':<8} {'MC#':>4} {'Pair#':>5} {'Trades':>6} {'PnL':>8} {'Avg':>8} {'Win%':>6}")
print("-" * 50)
for sym in sorted(mc['symbol'].unique()):
    sym_mc = mc[mc['symbol'] == sym]
    sym_pairs = pairs[pairs['symbol'] == sym]
    sym_trades = mc_trades[mc_trades['symbol'] == sym]
    pnl = sym_trades['pnl_atr'].sum() if len(sym_trades) > 0 else 0
    avg = sym_trades['pnl_atr'].mean() if len(sym_trades) > 0 else 0
    win = (sym_trades['pnl_atr'] > 0).mean() if len(sym_trades) > 0 else 0
    print(f"{sym:<8} {len(sym_mc):>4} {len(sym_pairs):>5} {len(sym_trades):>6} "
          f"{pnl:>8.2f} {avg:>8.4f} {win:>6.1%}")


# ── Write results to markdown ────────────────────────────────────────────
md_lines = []
md_lines.append("# v29 MC 9:50 Gate Analysis")
md_lines.append("")
md_lines.append(f"**Date:** 2026-03-04  ")
md_lines.append(f"**Data:** v28a signals ({n_total} MC signals, {len(mc_trades)} MC-confirmed trades, 126 opposing pairs)  ")
md_lines.append(f"**Question:** Should MC signals be delayed until 9:50 ET to avoid early noise?")
md_lines.append("")

md_lines.append("## 1. MC Signal Timing")
md_lines.append("")
md_lines.append(f"| Metric | Count | % |")
md_lines.append(f"|--------|------:|--:|")
md_lines.append(f"| Total MC signals | {n_total} | 100% |")
md_lines.append(f"| Before 9:50 | {n_before} | {n_before/n_total:.1%} |")
md_lines.append(f"| After 9:50 | {n_after} | {n_after/n_total:.0%} |")
md_lines.append("")
md_lines.append("**Time breakdown:**")
md_lines.append("")
md_lines.append("| Time | Count | % |")
md_lines.append("|------|------:|--:|")
for t, c in time_counts.items():
    md_lines.append(f"| {t} | {c} | {c/n_total:.1%} |")
md_lines.append("")
md_lines.append(f"**99.4% of MC signals fire before 9:50.** Only 7 fire later (11:05, 13:30-14:40).")
md_lines.append(f"On {days_with_2} symbol-days, BOTH bull and bear MC fire (opposing pair). "
                f"On {days_with_1} days, only one direction fires.")
md_lines.append("")

md_lines.append("## 2. Opposing Pair Accuracy")
md_lines.append("")
md_lines.append(f"All 126 opposing pairs fire entirely before 9:50. "
                f"The **second signal** is correct more often:")
md_lines.append("")
md_lines.append(f"| Signal | Correct | Rate |")
md_lines.append(f"|--------|--------:|-----:|")
md_lines.append(f"| 1st signal | {pairs['first_correct'].sum()} | {first_correct_rate:.1%} |")
md_lines.append(f"| 2nd signal | {pairs['second_correct'].sum()} | {second_correct_rate:.1%} |")
md_lines.append(f"| Neither | {neither_correct} | {neither_correct/len(pairs):.1%} |")
md_lines.append(f"| Both | {both_correct} | {both_correct/len(pairs):.1%} |")
md_lines.append("")
md_lines.append("**By timing:**")
md_lines.append("")
md_lines.append("| 1st Time | N | 1st Correct | 2nd Correct |")
md_lines.append("|----------|--:|------------:|------------:|")
for t in sorted(pairs['first_time'].unique()):
    s = pairs[pairs['first_time'] == t]
    md_lines.append(f"| {t} | {len(s)} | {s['first_correct'].mean():.1%} | {s['second_correct'].mean():.1%} |")
md_lines.append("")
md_lines.append(f"Average 30-min move when 1st correct: {correct_first['abs_move'].mean():.2f} ATR  ")
neither_move = pairs[~pairs['first_correct'] & ~pairs['second_correct']]['abs_move'].mean()
md_lines.append(f"Average 30-min move when neither correct: {neither_move:.2f} ATR (flat = both wrong)")
md_lines.append("")

md_lines.append("## 3. MC-Confirmed Trade Performance")
md_lines.append("")
md_lines.append("MC signals don't directly generate trades — they auto-confirm subsequent BRK/REV/VWAP signals. "
                "These are trades where `conf_source=QBS/MC`.")
md_lines.append("")
md_lines.append("### By Signal Time (when the BRK signal fired)")
md_lines.append("")
md_lines.append(f"| Window | Trades | Total PnL | Avg PnL | Avg MFE | Win% |")
md_lines.append(f"|--------|-------:|----------:|--------:|--------:|-----:|")
for label, lo, hi in buckets:
    b = mc_trades[(mc_trades['time_min'] >= lo) & (mc_trades['time_min'] < hi)]
    if len(b) == 0:
        continue
    md_lines.append(f"| {label} | {len(b)} | {b['pnl_atr'].sum():.2f} | "
                    f"{b['pnl_atr'].mean():.4f} | {b['mfe_atr'].mean():.4f} | "
                    f"{(b['pnl_atr']>0).mean():.1%} |")
md_lines.append("")

md_lines.append("### Pre vs Post 9:50")
md_lines.append("")
md_lines.append(f"| Group | N | Total PnL | Avg PnL | Avg MFE | Win% |")
md_lines.append(f"|-------|--:|----------:|--------:|--------:|-----:|")
for label, subset in [("Before 9:50", pre_trades), ("After 9:50", post_trades), ("All MC", mc_trades)]:
    md_lines.append(f"| {label} | {len(subset)} | {subset['pnl_atr'].sum():.2f} | "
                    f"{subset['pnl_atr'].mean():.4f} | {subset['mfe_atr'].mean():.4f} | "
                    f"{(subset['pnl_atr']>0).mean():.1%} |")
md_lines.append("")
md_lines.append(f"**Key finding:** Post-9:50 MC-confirmed trades ({len(post_trades)}) have "
                f"{'better' if post_trades['pnl_atr'].mean() > pre_trades['pnl_atr'].mean() else 'worse'} "
                f"avg PnL ({post_trades['pnl_atr'].mean():.4f} vs {pre_trades['pnl_atr'].mean():.4f} ATR).")
md_lines.append("")

md_lines.append("### Confirmation Timing Matrix")
md_lines.append("")
md_lines.append("| Scenario | N | PnL | Explanation |")
md_lines.append("|----------|--:|----:|-------------|")
md_lines.append(f"| Signal <9:50, CONF <9:50 | {len(early_signal_early_conf)} | "
                f"{early_signal_early_conf['pnl_atr'].sum():.2f} | BRK fires early, MC already confirmed |")
md_lines.append(f"| Signal >=9:50, CONF <9:50 | {len(late_signal_early_conf)} | "
                f"{late_signal_early_conf['pnl_atr'].sum():.2f} | BRK fires late, MC confirmed earlier |")
md_lines.append(f"| Signal >=9:50, CONF >=9:50 | {len(late_signal_late_conf)} | "
                f"{late_signal_late_conf['pnl_atr'].sum():.2f} | Both fire late (rare) |")
md_lines.append("")
md_lines.append(f"The {len(late_signal_early_conf)} trades in the middle row are **at risk** with a 9:50 gate: "
                f"their MC confirmation came from a pre-9:50 MC signal. With a gate, that MC wouldn't exist. "
                f"Whether they'd be recovered depends on a replacement MC firing at 9:50+.")
md_lines.append("")

md_lines.append("## 4. Oracle Scenario")
md_lines.append("")
md_lines.append("If we could magically pick only the correct MC direction on pair days:")
md_lines.append("")
md_lines.append(f"| Metric | Current | Oracle | Delta |")
md_lines.append(f"|--------|--------:|-------:|------:|")
md_lines.append(f"| Total MC PnL (ATR) | {actual_pnl:.2f} | {oracle_pnl:.2f} | {oracle_pnl-actual_pnl:+.2f} |")
md_lines.append(f"| Wrong-dir trades removed | — | {len(paired_trades_wrong)} | — |")
md_lines.append(f"| Wrong-dir PnL removed | — | {paired_trades_wrong['pnl_atr'].sum():.2f} | — |")
md_lines.append("")

if len(paired_trades_correct) > 0 and len(paired_trades_wrong) > 0:
    md_lines.append("**Correct vs wrong direction trades on pair days:**")
    md_lines.append("")
    md_lines.append(f"| Direction | N | Avg PnL | Avg MFE | Win% |")
    md_lines.append(f"|-----------|--:|--------:|--------:|-----:|")
    md_lines.append(f"| Correct dir | {len(paired_trades_correct)} | "
                    f"{paired_trades_correct['pnl_atr'].mean():.4f} | "
                    f"{paired_trades_correct['mfe_atr'].mean():.4f} | "
                    f"{(paired_trades_correct['pnl_atr']>0).mean():.1%} |")
    md_lines.append(f"| Wrong dir | {len(paired_trades_wrong)} | "
                    f"{paired_trades_wrong['pnl_atr'].mean():.4f} | "
                    f"{paired_trades_wrong['mfe_atr'].mean():.4f} | "
                    f"{(paired_trades_wrong['pnl_atr']>0).mean():.1%} |")
    md_lines.append("")

md_lines.append("## 5. Slot Recovery")
md_lines.append("")
md_lines.append("MC is once-per-direction-per-session. When both bull and bear MC fire before 9:50, "
                "both slots are burned — no MC can fire for the rest of the day.")
md_lines.append("")
md_lines.append(f"| Metric | Count |")
md_lines.append(f"|--------|------:|")
md_lines.append(f"| Days with both slots burned before 9:50 | {len(both_burned)} |")
md_lines.append(f"| Days with one slot burned before 9:50 | {len(one_burned)} |")
md_lines.append(f"| MC signals currently after 9:50 | {len(mc_after)} |")
md_lines.append("")
md_lines.append(f"Only {len(mc_after)} MC signals fire after 9:50 in current data. "
                f"This is because slots are almost always burned early.")
md_lines.append("")

# QBS comparison
qbs_after_count = (~qbs['before_gate']).sum()
md_lines.append(f"**QBS signals (volume drying pattern) for comparison:**")
md_lines.append(f"- Before 9:50: {qbs['before_gate'].sum()}")
md_lines.append(f"- After 9:50: {qbs_after_count}")
md_lines.append(f"- QBS fires throughout the day, proving volume patterns occur after 9:50.")
md_lines.append(f"- If MC slots weren't burned, we'd expect similar late-session MC signals.")
md_lines.append("")

md_lines.append("**Late MC analysis (7 signals that did fire after 9:50):**")
md_lines.append("")
for _, row in mc_after.iterrows():
    sym, dt = row['symbol'], row['date']
    same_day_mc = mc[(mc['symbol'] == sym) & (mc['date'] == dt)]
    early = same_day_mc[same_day_mc['before_gate']]
    md_lines.append(f"- {sym} {dt} at {row['time']} ({row['direction']}): "
                    f"{len(early)} early MC signals, dirs={list(early['direction'])}")
md_lines.append("")

md_lines.append("## 6. Per-Symbol Breakdown")
md_lines.append("")
md_lines.append(f"| Symbol | MC# | Pairs | Trades | Total PnL | Avg PnL | Win% |")
md_lines.append(f"|--------|----:|------:|-------:|----------:|--------:|-----:|")
for sym in sorted(mc['symbol'].unique()):
    sym_mc = mc[mc['symbol'] == sym]
    sym_pairs = pairs[pairs['symbol'] == sym]
    sym_trades = mc_trades[mc_trades['symbol'] == sym]
    pnl = sym_trades['pnl_atr'].sum() if len(sym_trades) > 0 else 0
    avg = sym_trades['pnl_atr'].mean() if len(sym_trades) > 0 else 0
    win = (sym_trades['pnl_atr'] > 0).mean() if len(sym_trades) > 0 else 0
    md_lines.append(f"| {sym} | {len(sym_mc)} | {len(sym_pairs)} | {len(sym_trades)} | "
                    f"{pnl:.2f} | {avg:.4f} | {win:.1%} |")
md_lines.append("")

md_lines.append("## 7. Recommendations")
md_lines.append("")

# Generate data-driven recommendations
if paired_trades_wrong['pnl_atr'].sum() < 0:
    md_lines.append("### The case FOR a 9:50 gate:")
    md_lines.append(f"- Wrong-direction trades on pair days cost {paired_trades_wrong['pnl_atr'].sum():.2f} ATR total")
    md_lines.append(f"- Removing them improves PnL by {-paired_trades_wrong['pnl_atr'].sum():.2f} ATR")
else:
    md_lines.append("### The case AGAINST a 9:50 gate:")
    md_lines.append(f"- Even wrong-direction trades are profitable ({paired_trades_wrong['pnl_atr'].sum():.2f} ATR)")

mc_before_pnl = pre_trades['pnl_atr'].sum()
mc_after_pnl = post_trades['pnl_atr'].sum()
md_lines.append("")
md_lines.append("### Trade-off analysis:")
md_lines.append(f"- Pre-9:50 signal trades: {len(pre_trades)} trades, {mc_before_pnl:.2f} ATR total PnL")
md_lines.append(f"- Post-9:50 signal trades: {len(post_trades)} trades, {mc_after_pnl:.2f} ATR total PnL")
md_lines.append(f"- {len(late_signal_early_conf)} trades confirmed by early MC but signaled after 9:50 "
                f"({late_signal_early_conf['pnl_atr'].sum():.2f} ATR) — these are the CORE value of early MC")

# Risk of gate
md_lines.append("")
md_lines.append("### Risk of implementing the gate:")
md_lines.append(f"- {len(late_signal_early_conf)} post-9:50 BRK trades currently get free MC confirmation")
md_lines.append(f"- With a gate, those trades would need a NEW MC to fire at 9:50+")
md_lines.append(f"- Currently only {len(mc_after)} MC signals fire after 9:50 (slots burned early)")
md_lines.append(f"- Unclear how many new MC signals would fire — volume patterns DO exist (QBS: {qbs_after_count} after 9:50)")

# Bottom line
md_lines.append("")
md_lines.append("### Bottom line:")
pnl_per_trade_pre = pre_trades['pnl_atr'].mean() if len(pre_trades) > 0 else 0
pnl_per_trade_post = post_trades['pnl_atr'].mean() if len(post_trades) > 0 else 0
if pnl_per_trade_post > pnl_per_trade_pre:
    md_lines.append(f"Post-9:50 trades have better per-trade PnL ({pnl_per_trade_post:.4f} vs {pnl_per_trade_pre:.4f} ATR). "
                    f"A gate would lose the {len(late_signal_early_conf)} 'free confirmation' trades "
                    f"({late_signal_early_conf['pnl_atr'].sum():.2f} ATR) unless replacement MC signals fire.")
else:
    md_lines.append(f"Pre-9:50 trades have better per-trade PnL ({pnl_per_trade_pre:.4f} vs {pnl_per_trade_post:.4f} ATR). "
                    f"The early MC confirmation is adding value.")
md_lines.append("")
md_lines.append(f"**Oracle analysis shows:** removing wrong-direction MC trades on pair days changes total PnL by "
                f"{oracle_pnl-actual_pnl:+.2f} ATR. The opposing pairs cost "
                f"{paired_trades_wrong['pnl_atr'].sum():.2f} ATR.")

# Write markdown
out_path = BASE / 'v29-mc-gate-analysis.md'
with open(out_path, 'w') as f:
    f.write('\n'.join(md_lines) + '\n')
print(f"\n\nResults written to {out_path}")
