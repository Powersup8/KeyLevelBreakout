#!/usr/bin/env python3
"""
v3.1 Backtest — Validate three KLB changes against enriched signals data.

Changes:
1. REV Exemption from EMA Hard Gate — REV signals no longer need EMA alignment
2. PD Mid → REV signal type — new level, can't backtest (not in historical data)
3. SPY Market Regime → BAIL Modifier — context-aware BAIL thresholds

Data:
- debug/enriched-signals.csv (1841 signals, MFE/MAE in ATR units)
- IB SPY 5m candles for regime classification
- IB per-symbol 1m candles for 5m PnL computation
"""
import sys, os
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).parent.parent
DEBUG = BASE / "debug"
CACHE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars")

# ── Load enriched signals ────────────────────────────────────────────────
signals = pd.read_csv(DEBUG / "enriched-signals.csv")
print(f"Loaded {len(signals)} signals", file=sys.stderr)

# Derive helper columns
signals['ema_aligned'] = (
    ((signals['direction'] == 'bull') & (signals['ema'] == 'bull')) |
    ((signals['direction'] == 'bear') & (signals['ema'] == 'bear'))
)
signals['is_rev'] = signals['type'] == 'REV'
signals['is_brk'] = signals['type'] == 'BRK'
signals['conf_pass'] = signals['conf'].isin(['✓', '✓★'])

# Parse time → minutes since midnight for easy comparisons
def time_to_minutes(t):
    parts = t.split(':')
    return int(parts[0]) * 60 + int(parts[1])

signals['time_min'] = signals['time'].apply(time_to_minutes)
signals['is_pre950'] = signals['time_min'] < (9*60 + 50)

# PnL proxy: MFE + MAE (MAE is negative)
signals['pnl'] = signals['mfe'] + signals['mae']
signals['win'] = signals['pnl'] > 0

# ── Load SPY data ────────────────────────────────────────────────────────
print("Loading SPY 5m data...", file=sys.stderr)
spy5m = pd.read_parquet(CACHE / "spy_5_mins_ib.parquet")
spy5m['date'] = pd.to_datetime(spy5m['date'])
# Convert from CET to ET (CET = ET + 6 hours)
spy5m['date_et'] = spy5m['date'].dt.tz_convert('US/Eastern')
spy5m = spy5m.set_index('date_et').sort_index()

# Compute SPY daily open (first bar at or after 9:30 ET)
spy5m['day'] = spy5m.index.date
spy_rth = spy5m.between_time('09:30', '16:00')

spy_day_open = spy_rth.groupby('day')['open'].first()
spy_day_open = spy_day_open.to_dict()

# ── Load per-symbol 1m data for 5m PnL computation ──────────────────────
print("Loading 1m candle data for 5m PnL...", file=sys.stderr)

symbol_1m = {}
SYMBOLS = signals['symbol'].unique()
for sym in SYMBOLS:
    fname = CACHE / f"{sym.lower()}_1_min_ib.parquet"
    if fname.exists():
        df = pd.read_parquet(fname)
        df['date'] = pd.to_datetime(df['date'])
        df['date_et'] = df['date'].dt.tz_convert('US/Eastern')
        df = df.set_index('date_et').sort_index()
        symbol_1m[sym] = df
        print(f"  Loaded {sym}: {len(df)} rows", file=sys.stderr)
    else:
        print(f"  WARNING: No 1m data for {sym}", file=sys.stderr)

# ── Compute 5m PnL for each signal ──────────────────────────────────────
print("Computing 5m PnL for each signal...", file=sys.stderr)

def compute_pnl_5m(row):
    """Compute PnL at 5 minutes after signal in ATR units."""
    sym = row['symbol']
    if sym not in symbol_1m:
        return np.nan

    df1m = symbol_1m[sym]
    date_str = row['date']
    time_str = row['time']
    atr = row['atr']
    direction = row['direction']
    entry_price = row['close']

    # Build timestamp
    h, m = map(int, time_str.split(':'))
    try:
        ts = pd.Timestamp(f"{date_str} {h:02d}:{m:02d}:00", tz='US/Eastern')
    except:
        return np.nan

    # Find close price 5 minutes later
    ts_5m = ts + pd.Timedelta(minutes=5)

    # Get bars in the 5-minute window
    mask = (df1m.index > ts) & (df1m.index <= ts_5m)
    bars = df1m.loc[mask]

    if len(bars) == 0:
        return np.nan

    close_5m = bars.iloc[-1]['close']

    if direction == 'bull':
        pnl = (close_5m - entry_price) / atr
    else:
        pnl = (entry_price - close_5m) / atr

    return round(pnl, 4)

def compute_spy_chg(row):
    """Compute SPY % change from day open at signal time."""
    date_str = row['date']
    time_str = row['time']

    h, m = map(int, time_str.split(':'))
    try:
        ts = pd.Timestamp(f"{date_str} {h:02d}:{m:02d}:00", tz='US/Eastern')
    except:
        return np.nan

    day = ts.date()
    if day not in spy_day_open:
        return np.nan

    spy_open = spy_day_open[day]

    # Find SPY close at this time (use 5m bars, find nearest before)
    mask = (spy5m.index <= ts) & (spy5m.index >= ts - pd.Timedelta(minutes=5))
    bars = spy5m.loc[mask]

    if len(bars) == 0:
        # Try wider window
        mask = (spy5m.index <= ts) & (spy5m.index >= ts - pd.Timedelta(minutes=10))
        bars = spy5m.loc[mask]

    if len(bars) == 0:
        return np.nan

    spy_close = bars.iloc[-1]['close']
    chg = (spy_close - spy_open) / spy_open
    return round(chg, 6)

# Compute for all signals
signals['pnl_5m'] = signals.apply(compute_pnl_5m, axis=1)
signals['spy_chg'] = signals.apply(compute_spy_chg, axis=1)

pnl_5m_valid = signals['pnl_5m'].notna().sum()
spy_chg_valid = signals['spy_chg'].notna().sum()
print(f"  pnl_5m computed for {pnl_5m_valid}/{len(signals)} signals", file=sys.stderr)
print(f"  spy_chg computed for {spy_chg_valid}/{len(signals)} signals", file=sys.stderr)

# ══════════════════════════════════════════════════════════════════════════
# ANALYSIS
# ══════════════════════════════════════════════════════════════════════════
report = []
def p(line=""):
    report.append(line)

p("# v3.1 Backtest Results")
p()
p(f"**Date:** 2026-03-06")
p(f"**Signals:** {len(signals)} (enriched-signals.csv)")
p(f"**5m PnL coverage:** {pnl_5m_valid}/{len(signals)} ({pnl_5m_valid/len(signals)*100:.0f}%)")
p(f"**SPY regime coverage:** {spy_chg_valid}/{len(signals)} ({spy_chg_valid/len(signals)*100:.0f}%)")
p()

# ══════════════════════════════════════════════════════════════════════════
# CHANGE 1: REV Exemption from EMA Hard Gate
# ══════════════════════════════════════════════════════════════════════════
p("---")
p("## Change 1: REV Exemption from EMA Hard Gate")
p()
p("In v3.0b, REV signals required EMA alignment after 9:50 ET. In v3.1, REV")
p("signals are exempt from EMA gate (only need ADX + body gate).")
p()

# v3.0b EMA gate: after 9:50, non-EMA-aligned signals are suppressed
# REV signals that were EMA-misaligned AND after 9:50 = signals that would have been suppressed
rev = signals[signals['is_rev']].copy()
rev_post950 = rev[~rev['is_pre950']]
rev_pre950 = rev[rev['is_pre950']]

rev_post950_ema = rev_post950[rev_post950['ema_aligned']]
rev_post950_noema = rev_post950[~rev_post950['ema_aligned']]

p(f"### REV Signal Breakdown")
p(f"| Category | N | Avg PnL | Total PnL | Win% |")
p(f"|----------|---|---------|-----------|------|")

for label, subset in [
    ("All REV", rev),
    ("REV pre-9:50", rev_pre950),
    ("REV post-9:50 + EMA aligned", rev_post950_ema),
    ("REV post-9:50 + EMA misaligned (SUPPRESSED in v3.0b)", rev_post950_noema),
]:
    n = len(subset)
    avg_pnl = subset['pnl'].mean() if n > 0 else 0
    total_pnl = subset['pnl'].sum() if n > 0 else 0
    win_pct = subset['win'].mean() * 100 if n > 0 else 0
    p(f"| {label} | {n} | {avg_pnl:+.3f} | {total_pnl:+.1f} | {win_pct:.1f}% |")

p()
p(f"**Impact:** In v3.0b, {len(rev_post950_noema)} REV signals were suppressed by EMA gate after 9:50.")
p(f"These signals had total PnL of **{rev_post950_noema['pnl'].sum():+.1f} ATR**.")

if len(rev_post950_noema) > 0:
    avg = rev_post950_noema['pnl'].mean()
    if avg > 0:
        p(f"Allowing them in v3.1 would ADD **{rev_post950_noema['pnl'].sum():+.1f} ATR** to performance.")
    else:
        p(f"Allowing them in v3.1 would COST **{rev_post950_noema['pnl'].sum():+.1f} ATR** — these are net negative.")

    p()
    p("#### Breakdown by direction:")
    p(f"| Direction | N | Avg PnL | Total PnL | Win% |")
    p(f"|-----------|---|---------|-----------|------|")
    for d in ['bull', 'bear']:
        sub = rev_post950_noema[rev_post950_noema['direction'] == d]
        n = len(sub)
        if n > 0:
            p(f"| {d} | {n} | {sub['pnl'].mean():+.3f} | {sub['pnl'].sum():+.1f} | {sub['win'].mean()*100:.1f}% |")

    p()
    p("#### Breakdown by time bucket:")
    p(f"| Time | N | Avg PnL | Total PnL | Win% |")
    p(f"|------|---|---------|-----------|------|")
    for tb in ['9:30-10:00', '10:00-11:00', '11:00-12:00', '12:00+']:
        sub = rev_post950_noema[rev_post950_noema['time_bucket'] == tb]
        n = len(sub)
        if n > 0:
            p(f"| {tb} | {n} | {sub['pnl'].mean():+.3f} | {sub['pnl'].sum():+.1f} | {sub['win'].mean()*100:.1f}% |")

    p()
    p("#### Breakdown by EMA state (misaligned only):")
    p(f"| EMA | N | Avg PnL | Total PnL | Win% |")
    p(f"|-----|---|---------|-----------|------|")
    for ema in ['bull', 'bear', 'mixed']:
        sub = rev_post950_noema[rev_post950_noema['ema'] == ema]
        n = len(sub)
        if n > 0:
            p(f"| {ema} | {n} | {sub['pnl'].mean():+.3f} | {sub['pnl'].sum():+.1f} | {sub['win'].mean()*100:.1f}% |")

# ── Also show: what v3.0b kept (post-950 + EMA aligned REV) vs what v3.1 adds ──
p()
p("#### Net impact on REV after 9:50:")
rev_v30b = rev_post950_ema  # v3.0b only kept these
rev_v31 = rev_post950       # v3.1 keeps all post-950 REV
p(f"- v3.0b: {len(rev_v30b)} REV signals, total PnL = {rev_v30b['pnl'].sum():+.1f} ATR")
p(f"- v3.1:  {len(rev_v31)} REV signals, total PnL = {rev_v31['pnl'].sum():+.1f} ATR")
p(f"- Delta: **{rev_v31['pnl'].sum() - rev_v30b['pnl'].sum():+.1f} ATR** from {len(rev_post950_noema)} additional signals")

# ══════════════════════════════════════════════════════════════════════════
# CHANGE 2: PD Mid → REV signal type
# ══════════════════════════════════════════════════════════════════════════
p()
p("---")
p("## Change 2: PD Mid → REV Signal Type")
p()
p("PD Mid is a **new level** added in v3.0 — it does not exist in the historical")
p("enriched-signals.csv data. Therefore this change **cannot be backtested** against")
p("historical signals.")
p()
p("**What we know from v3.0 research:**")
p("- PD Mid was estimated at +0.209 avg P&L in the new levels research")
p("- Changing from BRK to REV detection means touch-and-turn instead of close-through")
p("- REV signals tend to have tighter entries and lower MAE")
p("- Expected impact: slightly fewer triggers but better entry quality")
p()

# ══════════════════════════════════════════════════════════════════════════
# CHANGE 3: SPY Market Regime → BAIL Modifier
# ══════════════════════════════════════════════════════════════════════════
p("---")
p("## Change 3: SPY Market Regime → BAIL Modifier")
p()
p("Old BAIL: Hold if pnl_5m > 0.05 ATR (flat threshold for all signals)")
p("New BAIL:")
p("- Signal aligned with SPY direction (>0.3%) → NEVER BAIL")
p("- SPY neutral (±0.3%) → loose BAIL (pnl > -0.10 ATR)")
p("- Signal opposes SPY → strict BAIL (pnl > 0.05 ATR)")
p()

# Filter to CONF pass signals only (BAIL only applies after confirmation)
conf = signals[signals['conf_pass']].copy()
has_5m = conf[conf['pnl_5m'].notna()].copy()
has_both = has_5m[has_5m['spy_chg'].notna()].copy()

p(f"**CONF pass signals:** {len(conf)}")
p(f"**With 5m PnL data:** {len(has_5m)}")
p(f"**With 5m PnL + SPY data:** {len(has_both)}")
p()

if len(has_both) > 0:
    # Classify SPY regime for each signal
    def classify_spy(row):
        spy_chg = row['spy_chg']
        direction = row['direction']

        if pd.isna(spy_chg):
            return 'unknown'

        # SPY is up > 0.3%
        if spy_chg > 0.003:
            if direction == 'bull':
                return 'aligned'    # bull + SPY up
            else:
                return 'opposed'    # bear + SPY up
        # SPY is down > 0.3%
        elif spy_chg < -0.003:
            if direction == 'bear':
                return 'aligned'    # bear + SPY down
            else:
                return 'opposed'    # bull + SPY down
        # SPY neutral
        else:
            return 'neutral'

    has_both['spy_regime'] = has_both.apply(classify_spy, axis=1)

    # Old BAIL: pnl_5m > 0.05
    has_both['old_hold'] = has_both['pnl_5m'] > 0.05

    # New BAIL
    def new_bail_hold(row):
        regime = row['spy_regime']
        pnl_5m = row['pnl_5m']
        if regime == 'aligned':
            return True  # Never bail
        elif regime == 'neutral':
            return pnl_5m > -0.10  # Loose bail
        else:  # opposed
            return pnl_5m > 0.05   # Strict bail (same as old)

    has_both['new_hold'] = has_both.apply(new_bail_hold, axis=1)

    # Compute outcomes for old vs new
    # When BAIL: PnL = pnl_5m (you exit at 5 min)
    # When HOLD: PnL = mfe + mae (full 60-min outcome)
    has_both['old_pnl'] = np.where(has_both['old_hold'], has_both['pnl'], has_both['pnl_5m'])
    has_both['new_pnl'] = np.where(has_both['new_hold'], has_both['pnl'], has_both['pnl_5m'])

    p("### SPY Regime Distribution (CONF pass signals)")
    p(f"| SPY Regime | N | % |")
    p(f"|------------|---|---|")
    for regime in ['aligned', 'neutral', 'opposed']:
        sub = has_both[has_both['spy_regime'] == regime]
        p(f"| {regime} | {len(sub)} | {len(sub)/len(has_both)*100:.1f}% |")

    p()
    p("### Old vs New BAIL Decision Counts")
    p(f"| BAIL Rule | HOLD | BAIL |")
    p(f"|-----------|------|------|")
    p(f"| Old (flat 0.05) | {has_both['old_hold'].sum()} | {(~has_both['old_hold']).sum()} |")
    p(f"| New (SPY-aware) | {has_both['new_hold'].sum()} | {(~has_both['new_hold']).sum()} |")

    p()
    old_total = has_both['old_pnl'].sum()
    new_total = has_both['new_pnl'].sum()
    old_avg = has_both['old_pnl'].mean()
    new_avg = has_both['new_pnl'].mean()

    p("### Total PnL Comparison")
    p(f"| Metric | Old BAIL | New BAIL | Delta |")
    p(f"|--------|----------|----------|-------|")
    p(f"| Total PnL (ATR) | {old_total:+.1f} | {new_total:+.1f} | **{new_total - old_total:+.1f}** |")
    p(f"| Avg PnL (ATR) | {old_avg:+.3f} | {new_avg:+.3f} | {new_avg - old_avg:+.3f} |")
    p(f"| Win % | {(has_both['old_pnl'] > 0).mean()*100:.1f}% | {(has_both['new_pnl'] > 0).mean()*100:.1f}% | {((has_both['new_pnl'] > 0).mean() - (has_both['old_pnl'] > 0).mean())*100:+.1f}pp |")

    p()
    p("### Breakdown by SPY Regime")
    p(f"| Regime | N | Old Hold% | New Hold% | Old PnL | New PnL | Delta |")
    p(f"|--------|---|-----------|-----------|---------|---------|-------|")
    for regime in ['aligned', 'neutral', 'opposed']:
        sub = has_both[has_both['spy_regime'] == regime]
        n = len(sub)
        if n > 0:
            oh = sub['old_hold'].mean() * 100
            nh = sub['new_hold'].mean() * 100
            op = sub['old_pnl'].sum()
            np_ = sub['new_pnl'].sum()
            p(f"| {regime} | {n} | {oh:.0f}% | {nh:.0f}% | {op:+.1f} | {np_:+.1f} | {np_ - op:+.1f} |")

    # ── Deep dive: Where does the new BAIL differ from old? ──
    p()
    p("### Signals Where Decision Changes")
    p()

    # New HOLD but old BAIL (loosened)
    loosened = has_both[(has_both['new_hold']) & (~has_both['old_hold'])].copy()
    # New BAIL but old HOLD (tightened) — shouldn't happen given the rules, but check
    tightened = has_both[(~has_both['new_hold']) & (has_both['old_hold'])].copy()

    p(f"- **Loosened** (old=BAIL, new=HOLD): {len(loosened)} signals")
    if len(loosened) > 0:
        p(f"  - These signals were bailed in v3.0b but now held to completion")
        p(f"  - Their 5m PnL (what old got): {loosened['pnl_5m'].sum():+.1f} ATR")
        p(f"  - Their full PnL (what new gets): {loosened['pnl'].sum():+.1f} ATR")
        p(f"  - Net gain from loosening: **{loosened['pnl'].sum() - loosened['pnl_5m'].sum():+.1f} ATR**")

        p()
        p("  Loosened by regime:")
        for regime in ['aligned', 'neutral']:
            sub = loosened[loosened['spy_regime'] == regime]
            if len(sub) > 0:
                p(f"  - {regime}: {len(sub)} signals, 5m PnL={sub['pnl_5m'].sum():+.1f}, full PnL={sub['pnl'].sum():+.1f}, delta={sub['pnl'].sum() - sub['pnl_5m'].sum():+.1f}")

    p(f"- **Tightened** (old=HOLD, new=BAIL): {len(tightened)} signals")
    if len(tightened) > 0:
        p(f"  - These signals were held in v3.0b but now bailed")
        p(f"  - Their full PnL (what old got): {tightened['pnl'].sum():+.1f} ATR")
        p(f"  - Their 5m PnL (what new gets): {tightened['pnl_5m'].sum():+.1f} ATR")
        p(f"  - Net change: **{tightened['pnl_5m'].sum() - tightened['pnl'].sum():+.1f} ATR**")

    # ── Breakdown: aligned signals deep dive ──
    p()
    p("### Deep Dive: Aligned Signals (Never BAIL in v3.1)")
    aligned = has_both[has_both['spy_regime'] == 'aligned'].copy()
    if len(aligned) > 0:
        # Among aligned, how many had pnl_5m <= 0.05 (would have been bailed before)?
        would_bail_old = aligned[~aligned['old_hold']]
        would_hold_old = aligned[aligned['old_hold']]

        p(f"| Category | N | Full PnL | Win% |")
        p(f"|----------|---|----------|------|")
        p(f"| Aligned + old would HOLD | {len(would_hold_old)} | {would_hold_old['pnl'].sum():+.1f} | {would_hold_old['win'].mean()*100:.1f}% |")
        p(f"| Aligned + old would BAIL | {len(would_bail_old)} | {would_bail_old['pnl'].sum():+.1f} | {would_bail_old['win'].mean()*100:.1f}% |")
        p()
        p(f"The {len(would_bail_old)} signals that old BAIL would exit — their full outcome is")
        p(f"**{would_bail_old['pnl'].sum():+.1f} ATR** vs early exit at **{would_bail_old['pnl_5m'].sum():+.1f} ATR**.")
        if len(would_bail_old) > 0:
            p(f"Holding them gains **{would_bail_old['pnl'].sum() - would_bail_old['pnl_5m'].sum():+.1f} ATR**.")

    # ── Breakdown: neutral signals deep dive ──
    p()
    p("### Deep Dive: Neutral Signals (Loose BAIL: pnl > -0.10)")
    neutral = has_both[has_both['spy_regime'] == 'neutral'].copy()
    if len(neutral) > 0:
        p(f"| Category | N | Full PnL | 5m PnL | Win% |")
        p(f"|----------|---|----------|--------|------|")
        # In old: bail if pnl_5m <= 0.05
        # In new: bail if pnl_5m <= -0.10
        # Difference: signals with -0.10 < pnl_5m <= 0.05 now HOLD
        newly_held = neutral[(neutral['pnl_5m'] > -0.10) & (neutral['pnl_5m'] <= 0.05)]
        still_bailed = neutral[neutral['pnl_5m'] <= -0.10]
        still_held = neutral[neutral['pnl_5m'] > 0.05]

        p(f"| Still HOLD (pnl_5m > 0.05) | {len(still_held)} | {still_held['pnl'].sum():+.1f} | {still_held['pnl_5m'].sum():+.1f} | {still_held['win'].mean()*100:.1f}% |")
        p(f"| Newly HOLD (-0.10 < pnl_5m <= 0.05) | {len(newly_held)} | {newly_held['pnl'].sum():+.1f} | {newly_held['pnl_5m'].sum():+.1f} | {newly_held['win'].mean()*100:.1f}% |")
        p(f"| Still BAIL (pnl_5m <= -0.10) | {len(still_bailed)} | {still_bailed['pnl'].sum():+.1f} | {still_bailed['pnl_5m'].sum():+.1f} | n/a |")

# ══════════════════════════════════════════════════════════════════════════
# COMBINED SUMMARY
# ══════════════════════════════════════════════════════════════════════════
p()
p("---")
p("## Combined Summary")
p()

change1_delta = rev_post950_noema['pnl'].sum() if len(rev_post950_noema) > 0 else 0
change2_delta = 0  # Can't measure
if len(has_both) > 0:
    change3_delta = new_total - old_total
else:
    change3_delta = 0

p(f"| Change | Description | ATR Impact | Signals Affected |")
p(f"|--------|-------------|------------|------------------|")
p(f"| 1. REV EMA Exemption | Allow REV without EMA after 9:50 | **{change1_delta:+.1f}** | {len(rev_post950_noema)} |")
p(f"| 2. PD Mid → REV | New level, no historical data | n/a | n/a |")
p(f"| 3. SPY BAIL Modifier | Context-aware BAIL thresholds | **{change3_delta:+.1f}** | {len(has_both)} |")
p(f"| **Total measurable** | | **{change1_delta + change3_delta:+.1f}** | |")
p()

if change1_delta + change3_delta > 0:
    p(f"**Net positive impact of {change1_delta + change3_delta:+.1f} ATR.** v3.1 is an improvement.")
elif change1_delta + change3_delta < 0:
    p(f"**Net negative impact of {change1_delta + change3_delta:+.1f} ATR.** Review individual changes.")
else:
    p(f"**Net neutral impact.** Changes roughly cancel out.")

# ── Additional analysis: what if we also look at ALL signals (not just CONF pass)? ──
p()
p("---")
p("## Appendix: EMA Gate Impact on ALL Signals (not just REV)")
p()
p("For context, here is the EMA gate impact across ALL signal types after 9:50:")
p()

post950 = signals[~signals['is_pre950']]
post950_ema = post950[post950['ema_aligned']]
post950_noema = post950[~post950['ema_aligned']]

p(f"| Category | N | Avg PnL | Total PnL | Win% |")
p(f"|----------|---|---------|-----------|------|")
p(f"| Post-9:50 EMA aligned | {len(post950_ema)} | {post950_ema['pnl'].mean():+.3f} | {post950_ema['pnl'].sum():+.1f} | {post950_ema['win'].mean()*100:.1f}% |")
p(f"| Post-9:50 EMA misaligned | {len(post950_noema)} | {post950_noema['pnl'].mean():+.3f} | {post950_noema['pnl'].sum():+.1f} | {post950_noema['win'].mean()*100:.1f}% |")

p()
p("By type, EMA misaligned after 9:50:")
p(f"| Type | N | Avg PnL | Total PnL | Win% |")
p(f"|------|---|---------|-----------|------|")
for t in ['BRK', 'REV']:
    sub = post950_noema[post950_noema['type'] == t]
    n = len(sub)
    if n > 0:
        p(f"| {t} | {n} | {sub['pnl'].mean():+.3f} | {sub['pnl'].sum():+.1f} | {sub['win'].mean()*100:.1f}% |")

p()
p("This confirms whether exempting REV from EMA gate is justified while keeping it for BRK.")

# ── Write report ──
output = "\n".join(report)
outfile = DEBUG / "v31-backtest-results.md"
with open(outfile, 'w') as f:
    f.write(output)

print(f"\nReport saved to {outfile}", file=sys.stderr)
print(output)
