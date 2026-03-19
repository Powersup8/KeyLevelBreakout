#!/usr/bin/env python3
"""
TSLA Open-Scalp Deep Research Loop
====================================
Autonomous research script. Investigates TSLA market-open behavior
across ~15 hypotheses not covered by prior open-scalp-learnings.md.

Sends findings via Telegram. Writes full report to tsla-scalp-research.md.
Runs fully autonomously — no user input needed.

Prior findings (do NOT re-investigate):
  - Direction is 50/50 coin flip (Part B)
  - 5m rule: above open = HOLD 67% bull, below = BAIL 32% bull (Part F)
  - Level bounce $1-2 dip at 5d+ level = +21pp edge for NVDA/SPY, not TSLA (Part E)
  - Day high is early on bear days (9:34 median), late on bull days (Part C)
  - Basic scalp P&L killed by spreads (Part A)
"""

import os, sys, json, subprocess, textwrap
from pathlib import Path
from datetime import datetime, time as dtime, timedelta
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import pytz

# ── Paths ──────────────────────────────────────────────────────────────
DEBUG_DIR   = Path(__file__).parent
CACHE_DIR   = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache")
BARS_DIR    = CACHE_DIR / "bars"
HIGHRES_DIR = CACHE_DIR / "bars_highres" / "5sec"
NOTIFY      = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/personal_assistant/scripts/notify.py")
REPORT      = DEBUG_DIR / "tsla-scalp-research.md"
ET          = pytz.timezone("US/Eastern")

# ── Helpers ────────────────────────────────────────────────────────────

def notify(msg):
    if NOTIFY.exists():
        subprocess.run([sys.executable, str(NOTIFY), msg], capture_output=True, timeout=15)
    print(f"[NOTIFY] {msg}")

def load_1m(symbol="TSLA"):
    f = BARS_DIR / f"{symbol.lower()}_1_min_ib.parquet"
    df = pd.read_parquet(f).set_index("date").sort_index()
    df.index = pd.DatetimeIndex(df.index).tz_localize("UTC").tz_convert(ET) if df.index.tzinfo is None else df.index.tz_convert(ET)
    return df

def load_5m(symbol="TSLA"):
    f = BARS_DIR / f"{symbol.lower()}_5_mins_ib.parquet"
    df = pd.read_parquet(f).set_index("date").sort_index()
    df.index = pd.DatetimeIndex(df.index).tz_localize("UTC").tz_convert(ET) if df.index.tzinfo is None else df.index.tz_convert(ET)
    return df

def load_5s(symbol="TSLA"):
    f = HIGHRES_DIR / f"{symbol.lower()}_5_secs_ib.parquet"
    if not f.exists():
        return None
    df = pd.read_parquet(f).set_index("date").sort_index()
    df.index = pd.DatetimeIndex(df.index).tz_localize("UTC").tz_convert(ET) if df.index.tzinfo is None else df.index.tz_convert(ET)
    return df

def get_trading_days(df, start_time="09:30", end_time="15:59"):
    market = df.between_time(start_time, end_time)
    return sorted(set(market.index.date))

def build_daily(df_1m):
    """Build per-day summary from 1m data."""
    days = []
    trading_days = get_trading_days(df_1m)
    for d in trading_days:
        day = df_1m[df_1m.index.date == d]
        session = day.between_time("09:30", "15:59")
        if len(session) < 10:
            continue
        open_bar = session.iloc[0]
        open_px   = open_bar["open"]
        open_time = session.index[0]

        # 5m candle (bars 0-4 inclusive = 9:30,9:31,9:32,9:33,9:34)
        first5 = session.between_time("09:30", "09:34")
        # 30m
        first30 = session.between_time("09:30", "09:59")
        # pre-9:30 (pre-market last 30m if available)
        pre = day.between_time("09:00", "09:29")

        if len(first5) < 3:
            continue

        close5m  = first5.iloc[-1]["close"]
        high5m   = first5["high"].max()
        low5m    = first5["low"].min()
        range5m  = high5m - low5m

        close30m = first30.iloc[-1]["close"] if len(first30) >= 10 else np.nan
        day_high = session["high"].max()
        day_low  = session["low"].min()
        day_close = session.iloc[-1]["close"]
        vol_open_1m = session.iloc[0]["volume"] if "volume" in session.columns else np.nan

        # 1m first bar
        bar1_close = session.iloc[0]["close"]
        bar1_high  = session.iloc[0]["high"]
        bar1_low   = session.iloc[0]["low"]
        bar1_range = bar1_high - bar1_low
        bar1_green = bar1_close >= open_px

        # ORB (first 5m candle = use first5 H/L)
        orb_high = high5m
        orb_low  = low5m

        # 5m above/below open
        above_5m = close5m >= open_px

        # Day above open
        day_above = day_close >= open_px

        # pre-market
        pm_high = pre["high"].max() if len(pre) > 0 else np.nan
        pm_low  = pre["low"].min()  if len(pre) > 0 else np.nan
        pm_close = pre.iloc[-1]["close"] if len(pre) > 0 else np.nan

        # Overnight gap
        gap = open_px - pm_close if not np.isnan(pm_close) else np.nan

        # Dip from open in first 5m
        dip_5m = open_px - low5m  # positive = dipped below open

        days.append({
            "date": d,
            "open": open_px,
            "close5m": close5m,
            "close30m": close30m,
            "bar1_close": bar1_close,
            "bar1_range": bar1_range,
            "bar1_green": bar1_green,
            "high5m": high5m,
            "low5m": low5m,
            "range5m": range5m,
            "orb_high": orb_high,
            "orb_low": orb_low,
            "above_5m": above_5m,
            "day_high": day_high,
            "day_low": day_low,
            "day_close": day_close,
            "day_above": day_above,
            "day_high_above_open": day_high - open_px,
            "day_low_below_open": open_px - day_low,
            "pm_high": pm_high,
            "pm_low": pm_low,
            "pm_close": pm_close,
            "gap": gap,          # positive = gap up
            "dip_5m": dip_5m,    # positive = dipped below open
            "vol_open_1m": vol_open_1m,
            "session": session,  # full session for detailed analysis
        })
    return pd.DataFrame([{k: v for k, v in d.items() if k != "session"} for d in days]), days

def pct(x, n):
    return f"{100*x/n:.0f}%" if n > 0 else "N/A"

def avg(series):
    s = series.dropna()
    return f"${s.mean():.2f}" if len(s) > 0 else "N/A"

def med(series):
    s = series.dropna()
    return f"${s.median():.2f}" if len(s) > 0 else "N/A"

# ── Report writer ──────────────────────────────────────────────────────
lines = []

def w(s=""):
    lines.append(s)
    print(s)

def save_report():
    REPORT.write_text("\n".join(lines))

# ══════════════════════════════════════════════════════════════════════
# RESEARCH MODULES
# ══════════════════════════════════════════════════════════════════════

def R01_orb_breakout(daily, days_list):
    """Opening Range Breakout: does breaking ORB H/L predict day direction?"""
    w("## R01: Opening Range Breakout (ORB)")
    w()
    w("ORB defined as first 5m candle H/L (9:30-9:34). After 9:35, price breaks above ORB High or below ORB Low.")
    w()

    rows = []
    for d_row, d_full in zip(daily.itertuples(), days_list):
        session = d_full["session"]
        after_orb = session.between_time("09:35", "15:59")
        if len(after_orb) < 5:
            continue

        # When does price first break ORB High?
        orb_h = d_row.orb_high
        orb_l = d_row.orb_low
        first_bull_break = None
        first_bear_break = None
        for bar in after_orb.itertuples():
            if first_bull_break is None and bar.high > orb_h:
                mins = (bar.Index - session.index[0]).seconds // 60
                first_bull_break = mins
            if first_bear_break is None and bar.low < orb_l:
                mins = (bar.Index - session.index[0]).seconds // 60
                first_bear_break = mins
            if first_bull_break and first_bear_break:
                break

        bull_first = (first_bull_break is not None and
                      (first_bear_break is None or first_bull_break < first_bear_break))
        bear_first = (first_bear_break is not None and
                      (first_bull_break is None or first_bear_break < first_bull_break))

        rows.append({
            "date": d_row.date,
            "bull_break_first": bull_first,
            "bear_break_first": bear_first,
            "neither": not bull_first and not bear_first,
            "day_above": d_row.day_above,
            "day_close_vs_open": d_row.day_close - d_row.open,
            "day_high_above_open": d_row.day_high_above_open,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        w("No data.")
        return

    bull = df[df["bull_break_first"]]
    bear = df[df["bear_break_first"]]
    neither = df[df["neither"]]

    w(f"| ORB Break | Days | Day Above Open | Avg Day Close | Avg Day High |")
    w(f"|-----------|------|----------------|---------------|--------------|")
    for label, sub in [("Bull (ORB High first)", bull), ("Bear (ORB Low first)", bear), ("Neither", neither)]:
        n = len(sub)
        if n == 0: continue
        da = pct(sub["day_above"].sum(), n)
        dc = avg(sub["day_close_vs_open"])
        dh = avg(sub["day_high_above_open"])
        w(f"| {label} | {n} | {da} | {dc} | {dh} |")
    w()
    w(f"*n={len(df)} days total*")
    w()

    # Time-to-break distribution
    w("### ORB Bull break timing")
    bull_breaks = []
    bear_breaks = []
    for d_row, d_full in zip(daily.itertuples(), days_list):
        session = d_full["session"]
        after_orb = session.between_time("09:35", "15:59")
        orb_h = d_row.orb_high
        orb_l = d_row.orb_low
        for bar in after_orb.itertuples():
            if bar.high > orb_h:
                bull_breaks.append((bar.Index - session.index[0]).seconds // 60)
                break
        for bar in after_orb.itertuples():
            if bar.low < orb_l:
                bear_breaks.append((bar.Index - session.index[0]).seconds // 60)
                break
    if bull_breaks:
        s = pd.Series(bull_breaks)
        w(f"- Bull break: {len(bull_breaks)} days break ORB High. Median at {s.median():.0f}m. 25th pct={s.quantile(.25):.0f}m, 75th={s.quantile(.75):.0f}m")
    if bear_breaks:
        s = pd.Series(bear_breaks)
        w(f"- Bear break: {len(bear_breaks)} days break ORB Low. Median at {s.median():.0f}m. 25th pct={s.quantile(.25):.0f}m, 75th={s.quantile(.75):.0f}m")
    w()


def R02_first_bar_size(daily):
    """Does the size of the first 1m candle predict the day?"""
    w("## R02: First 1m Bar Size as Momentum Predictor")
    w()
    w("Hypothesis: a large opening bar (high range) signals a momentum day.")
    w()

    df = daily.dropna(subset=["bar1_range", "day_close"])
    df = df.copy()
    df["close_vs_open"] = df["day_close"] - df["open"]

    # Quartile split
    q25, q50, q75 = df["bar1_range"].quantile([0.25, 0.50, 0.75]).values

    buckets = [
        (f"Q1 tiny (≤${q25:.2f})", df[df["bar1_range"] <= q25]),
        (f"Q2 small (${q25:.2f}-${q50:.2f})", df[(df["bar1_range"] > q25) & (df["bar1_range"] <= q50)]),
        (f"Q3 medium (${q50:.2f}-${q75:.2f})", df[(df["bar1_range"] > q50) & (df["bar1_range"] <= q75)]),
        (f"Q4 large (>${q75:.2f})", df[df["bar1_range"] > q75]),
    ]

    w(f"| Bar Size | Days | 5m Above Open | Day Above | Avg Day Close | Avg Day High |")
    w(f"|----------|------|---------------|-----------|---------------|--------------|")
    for label, sub in buckets:
        n = len(sub)
        if n == 0: continue
        f5 = pct(sub["above_5m"].sum(), n)
        da = pct(sub["day_above"].sum(), n)
        dc = avg(sub["close_vs_open"])
        dh = avg(sub["day_high_above_open"])
        w(f"| {label} | {n} | {f5} | {da} | {dc} | {dh} |")
    w()

    # Green vs red first bar
    w("### Green vs Red First Bar")
    w(f"| 1st Bar | Days | 5m Above | Day Above | Avg Day Close |")
    w(f"|---------|------|----------|-----------|---------------|")
    for label, sub in [("Green (close≥open)", df[df["bar1_green"]]), ("Red (close<open)", df[~df["bar1_green"]])]:
        n = len(sub)
        f5 = pct(sub["above_5m"].sum(), n)
        da = pct(sub["day_above"].sum(), n)
        dc = avg(sub["close_vs_open"])
        w(f"| {label} | {n} | {f5} | {da} | {dc} |")
    w()


def R03_gap_tiers(daily):
    """Overnight gap size tiers — does extreme gap predict direction?"""
    w("## R03: Overnight Gap Size Tiers")
    w()
    w("Prior: gap up adds +6pp edge (weak). Test extreme gaps (>$3, >$5, >$10).")
    w()

    df = daily.dropna(subset=["gap"])
    df = df.copy()
    df["close_vs_open"] = df["day_close"] - df["open"]

    tiers = [
        ("Gap Up >$10",  df[df["gap"] > 10]),
        ("Gap Up $5-10", df[(df["gap"] > 5) & (df["gap"] <= 10)]),
        ("Gap Up $2-5",  df[(df["gap"] > 2) & (df["gap"] <= 5)]),
        ("Gap Up $0-2",  df[(df["gap"] > 0) & (df["gap"] <= 2)]),
        ("Flat (±$0)",   df[df["gap"].abs() <= 0.5]),
        ("Gap Dn $0-2",  df[(df["gap"] < 0) & (df["gap"] >= -2)]),
        ("Gap Dn $2-5",  df[(df["gap"] < -2) & (df["gap"] >= -5)]),
        ("Gap Dn $5-10", df[(df["gap"] < -5) & (df["gap"] >= -10)]),
        ("Gap Dn >$10",  df[df["gap"] < -10]),
    ]

    w(f"| Gap Tier | Days | 5m Above | Day Above | Avg Day Close | Avg Day High |")
    w(f"|----------|------|----------|-----------|---------------|--------------|")
    for label, sub in tiers:
        n = len(sub)
        if n == 0: continue
        f5 = pct(sub["above_5m"].sum(), n)
        da = pct(sub["day_above"].sum(), n)
        dc = avg(sub["close_vs_open"])
        dh = avg(sub["day_high_above_open"])
        w(f"| {label} | {n} | {f5} | {da} | {dc} | {dh} |")
    w()


def R04_pm_proximity(daily):
    """Pre-market level proximity — does opening near PM High/Low predict direction?"""
    w("## R04: Pre-Market Level Proximity at Open")
    w()
    w("Hypothesis: opening near PM High → fade/reversal. Near PM Low → bounce.")
    w()

    df = daily.dropna(subset=["pm_high", "pm_low"])
    df = df.copy()
    df["pm_range"] = df["pm_high"] - df["pm_low"]
    df["open_vs_pm_mid"] = df["open"] - (df["pm_high"] + df["pm_low"]) / 2
    df["close_vs_open"] = df["day_close"] - df["open"]

    # Distance from PM High / PM Low
    df["dist_pm_high"] = (df["pm_high"] - df["open"]).abs()
    df["dist_pm_low"]  = (df["pm_low"]  - df["open"]).abs()
    df["near_pm_high"]  = df["dist_pm_high"] < df["pm_range"] * 0.15
    df["near_pm_low"]   = df["dist_pm_low"]  < df["pm_range"] * 0.15
    df["at_pm_mid"]     = df["open_vs_pm_mid"].abs() < df["pm_range"] * 0.15
    df["above_pm_high"] = df["open"] > df["pm_high"]
    df["below_pm_low"]  = df["open"] < df["pm_low"]

    buckets = [
        ("Open above PM High (gap up beyond PM)",    df[df["above_pm_high"]]),
        ("Open near PM High (within 15% PM range)",  df[df["near_pm_high"] & ~df["above_pm_high"]]),
        ("Open at PM mid",                           df[df["at_pm_mid"]]),
        ("Open near PM Low (within 15% PM range)",   df[df["near_pm_low"] & ~df["below_pm_low"]]),
        ("Open below PM Low (gap down beyond PM)",   df[df["below_pm_low"]]),
    ]

    w(f"| Open Position | Days | 5m Above | Day Above | Avg Day Close | Avg Day High |")
    w(f"|---------------|------|----------|-----------|---------------|--------------|")
    for label, sub in buckets:
        n = len(sub)
        if n == 0: continue
        f5 = pct(sub["above_5m"].sum(), n)
        da = pct(sub["day_above"].sum(), n)
        dc = avg(sub["close_vs_open"])
        dh = avg(sub["day_high_above_open"])
        w(f"| {label} | {n} | {f5} | {da} | {dc} | {dh} |")
    w()


def R05_spy_divergence(daily_tsla, daily_spy):
    """TSLA vs SPY 5m divergence — does mismatch predict reversal?"""
    w("## R05: TSLA vs SPY Divergence at 5m")
    w()
    w("Hypothesis: when TSLA and SPY diverge at 5m, TSLA reverts toward SPY.")
    w()

    # Merge on date
    tsla = daily_tsla.set_index("date")[["above_5m", "day_above", "day_close", "open"]].copy()
    tsla["close_vs_open"] = tsla["day_close"] - tsla["open"]
    spy  = daily_spy.set_index("date")[["above_5m"]].rename(columns={"above_5m": "spy_above_5m"})
    merged = tsla.join(spy, how="inner").dropna()

    buckets = [
        ("TSLA ↑ SPY ↑ (agree, bull)",   merged[ merged["above_5m"] &  merged["spy_above_5m"]]),
        ("TSLA ↑ SPY ↓ (TSLA beats SPY)", merged[ merged["above_5m"] & ~merged["spy_above_5m"]]),
        ("TSLA ↓ SPY ↑ (TSLA lags SPY)", merged[~merged["above_5m"] &  merged["spy_above_5m"]]),
        ("TSLA ↓ SPY ↓ (agree, bear)",   merged[~merged["above_5m"] & ~merged["spy_above_5m"]]),
    ]

    w(f"| Scenario | Days | TSLA Day Above | Avg TSLA Day Close | Avg TSLA Day High |")
    w(f"|----------|------|----------------|--------------------|-------------------|")
    for label, sub in buckets:
        n = len(sub)
        if n == 0: continue
        da = pct(sub["day_above"].sum(), n)
        dc = avg(sub["close_vs_open"])
        dh = avg(sub["day_high_above_open"])
        w(f"| {label} | {n} | {da} | {dc} | {dh} |")
    w()


def R06_multi_day_trend(daily):
    """Prior N days trend as opening direction predictor."""
    w("## R06: Multi-Day Prior Trend as Predictor")
    w()
    w("Does TSLA being up/down for 3-5 consecutive days predict opening direction?")
    w()

    df = daily.copy().sort_values("date").reset_index(drop=True)
    df["close_vs_open"] = df["day_close"] - df["open"]
    df["prev1_bull"] = df["day_above"].shift(1)
    df["prev2_bull"] = df["day_above"].shift(2)
    df["prev3_bull"] = df["day_above"].shift(3)
    df = df.dropna(subset=["prev1_bull", "prev2_bull", "prev3_bull"])

    buckets = [
        ("3 bull days prior",  df[ df["prev1_bull"] &  df["prev2_bull"] &  df["prev3_bull"]]),
        ("2 bull, 1 bear",     df[ df["prev1_bull"] &  df["prev2_bull"] & ~df["prev3_bull"]]),
        ("1 bull, 2 bear",     df[ df["prev1_bull"] & ~df["prev2_bull"] & ~df["prev3_bull"]]),
        ("3 bear days prior",  df[~df["prev1_bull"] & ~df["prev2_bull"] & ~df["prev3_bull"]]),
        ("Prev day bull",      df[ df["prev1_bull"]]),
        ("Prev day bear",      df[~df["prev1_bull"]]),
    ]

    w(f"| Prior Trend | Days | 5m Above | Day Above | Avg Day Close |")
    w(f"|-------------|------|----------|-----------|---------------|")
    for label, sub in buckets:
        n = len(sub)
        if n == 0: continue
        f5 = pct(sub["above_5m"].sum(), n)
        da = pct(sub["day_above"].sum(), n)
        dc = avg(sub["close_vs_open"])
        w(f"| {label} | {n} | {f5} | {da} | {dc} |")
    w()


def R07_volume_signature(daily):
    """First-minute volume as predictor."""
    w("## R07: Opening Volume Signature")
    w()
    w("High opening volume = momentum confirmation or exhaustion?")
    w()

    df = daily.dropna(subset=["vol_open_1m"]).copy()
    df["close_vs_open"] = df["day_close"] - df["open"]

    # Rolling 20-day avg of first-minute volume
    df = df.sort_values("date").reset_index(drop=True)
    df["vol_ma20"] = df["vol_open_1m"].rolling(20, min_periods=10).mean().shift(1)
    df = df.dropna(subset=["vol_ma20"])
    df["vol_ratio"] = df["vol_open_1m"] / df["vol_ma20"]

    q25, q50, q75 = df["vol_ratio"].quantile([0.25, 0.50, 0.75]).values

    buckets = [
        (f"Very high vol (>{q75:.1f}x avg)", df[df["vol_ratio"] > q75]),
        (f"High vol ({q50:.1f}-{q75:.1f}x)",  df[(df["vol_ratio"] > q50) & (df["vol_ratio"] <= q75)]),
        (f"Normal vol ({q25:.1f}-{q50:.1f}x)", df[(df["vol_ratio"] > q25) & (df["vol_ratio"] <= q50)]),
        (f"Low vol (<{q25:.1f}x)",              df[df["vol_ratio"] <= q25]),
    ]

    w(f"| Volume Tier | Days | 5m Above | Day Above | Avg Day Close | Avg Day High |")
    w(f"|-------------|------|----------|-----------|---------------|--------------|")
    for label, sub in buckets:
        n = len(sub)
        if n == 0: continue
        f5 = pct(sub["above_5m"].sum(), n)
        da = pct(sub["day_above"].sum(), n)
        dc = avg(sub["close_vs_open"])
        dh = avg(sub["day_high_above_open"])
        w(f"| {label} | {n} | {f5} | {da} | {dc} | {dh} |")
    w()


def R08_orb_range_width(daily):
    """Narrow ORB → big breakout? Wide ORB → range day?"""
    w("## R08: ORB Range Width → Day Character")
    w()
    w("Narrow ORB (tight first 5m) often precedes large breakout moves.")
    w()

    df = daily.dropna(subset=["range5m"]).copy()
    df["close_vs_open"] = df["day_close"] - df["open"]
    df["day_range"] = df["day_high"] - df["day_low"]
    df["range_expansion"] = df["day_range"] / df["range5m"]

    q25, q50, q75 = df["range5m"].quantile([0.25, 0.50, 0.75]).values

    buckets = [
        (f"Narrow ORB (≤${q25:.2f})", df[df["range5m"] <= q25]),
        (f"Small ORB (${q25:.2f}-${q50:.2f})", df[(df["range5m"] > q25) & (df["range5m"] <= q50)]),
        (f"Wide ORB (${q50:.2f}-${q75:.2f})", df[(df["range5m"] > q50) & (df["range5m"] <= q75)]),
        (f"Very wide ORB (>${q75:.2f})", df[df["range5m"] > q75]),
    ]

    w(f"| ORB Width | Days | Day Above | Avg Day Close | Avg Day Range | Avg Range Expansion |")
    w(f"|-----------|------|-----------|---------------|---------------|---------------------|")
    for label, sub in buckets:
        n = len(sub)
        if n == 0: continue
        da = pct(sub["day_above"].sum(), n)
        dc = avg(sub["close_vs_open"])
        dr = avg(sub["day_range"])
        re = f"{sub['range_expansion'].mean():.1f}x" if len(sub) > 0 else "N/A"
        w(f"| {label} | {n} | {da} | {dc} | {dr} | {re} |")
    w()


def R09_second_chance_entry(daily, days_list):
    """After initial open move, does price return to open level for second entry?"""
    w("## R09: Second-Chance Entry (Return to Open After 15m)")
    w()
    w("After 5m above open (hold signal), price sometimes pulls back to open price. "
      "Is that a buying opportunity?")
    w()

    results = []
    for d_row, d_full in zip(daily.itertuples(), days_list):
        if not d_row.above_5m:
            continue
        session = d_full["session"]
        open_px = d_row.open
        after15m = session.between_time("09:45", "15:59")

        # Find first return to within $0.50 of open after 9:45
        returned = False
        ret_time = None
        for bar in after15m.itertuples():
            if abs(bar.low - open_px) <= 0.50 or abs(bar.close - open_px) <= 0.50:
                returned = True
                ret_time = bar.Index
                break

        if returned and ret_time:
            # From return point, what happens next?
            after_ret = session[session.index > ret_time]
            if len(after_ret) < 5:
                continue
            # Did it recover to +$1 above open within 30m?
            window = after_ret.iloc[:30]
            recovered_1 = (window["high"] > open_px + 1.0).any()
            outcome_close = session.iloc[-1]["close"] - open_px
            mins_to_ret = (ret_time - session.index[0]).seconds // 60
            results.append({
                "returned": True,
                "mins_to_return": mins_to_ret,
                "recovered_1": recovered_1,
                "day_close_vs_open": outcome_close,
                "day_above": d_row.day_above,
            })
        else:
            results.append({"returned": False})

    if not results:
        w("No data.")
        return

    df = pd.DataFrame(results)
    returned = df[df["returned"]]
    not_returned = df[~df["returned"]]

    n_total = len(df)
    n_ret = len(returned)
    w(f"Of {n_total} days with 5m above open:")
    w(f"- **{n_ret} days ({pct(n_ret, n_total)})** returned to within $0.50 of open after 9:45")
    w(f"- **{len(not_returned)} days ({pct(len(not_returned), n_total)})** held above open all day")
    w()

    if len(returned) > 5:
        rec1 = returned["recovered_1"].sum()
        w(f"When price returns to open after 9:45 (n={n_ret}):")
        w(f"- Recovered to +$1 within 30m: {rec1} ({pct(rec1, n_ret)})")
        w(f"- Day close vs open: avg={avg(returned['day_close_vs_open'])}, med={med(returned['day_close_vs_open'])}")
        w(f"- Day above open: {pct(returned['day_above'].sum(), n_ret)}")
        w()

        # Timing of return
        s = returned["mins_to_return"]
        w(f"Return timing: median {s.median():.0f}m after open, range {s.min():.0f}-{s.max():.0f}m")
    w()


def R10_combined_strategy_sim(daily):
    """Simulate: 5m above open + level touch → buy call. What's the raw P&L?"""
    w("## R10: Combined Strategy Simulation (5m Rule + Level Touch)")
    w()
    w("Simulate call buying: enter at 9:35 when 5m above open. "
      "TP=$3/$5, SL=$1/$2. Raw stock-side P&L (no spread).")
    w()

    df = daily.copy()
    df["close_vs_open"] = df["day_close"] - df["open"]

    # Signal: 5m above open
    signal = df[df["above_5m"]].copy()
    n_sig = len(signal)

    if n_sig == 0:
        w("No signals.")
        return

    # Outcome: from 9:35 close to various TP/SL targets
    # Since we don't have bar-by-bar sim here, use day_high / day_low as proxy:
    # TP hit if day_high >= open + TP, SL hit if day_low <= open - SL
    # Assume TP hits first if both possible (conservative)

    w(f"Signal: 5m above open = {n_sig} days ({pct(n_sig, len(df))} of days)")
    w()
    w("| Config | Trades | Win% (TP hit) | Avg Raw P&L | Notes |")
    w("|--------|--------|---------------|-------------|-------|")

    for tp, sl in [(1.0, 0.5), (2.0, 1.0), (3.0, 1.5), (5.0, 2.0), (3.0, 1.0), (5.0, 1.0)]:
        tp_hit = (signal["day_high_above_open"] >= tp).sum()
        sl_hit = (signal["day_low_below_open"] >= sl).sum()
        # Conservative: SL hits unless TP >= SL and day range supports TP
        wins = tp_hit  # not adjusting for intraday path
        avg_pnl = (tp_hit * tp - (n_sig - tp_hit) * sl) / n_sig
        w(f"| TP=${tp} SL=${sl} | {n_sig} | {pct(tp_hit, n_sig)} | ${avg_pnl:.2f} | raw, ignores path |")

    w()
    w("### Enhanced: 5m above + $2 above open (stronger signal)")
    strong = df[df["close5m"] >= df["open"] + 2.0].copy()
    n_s = len(strong)
    w(f"Signal: 5m close ≥ open+$2 = {n_s} days")
    if n_s > 5:
        for tp, sl in [(3.0, 1.5), (5.0, 2.0), (5.0, 1.0)]:
            tp_hit = (strong["day_high_above_open"] >= tp).sum()
            avg_pnl = (tp_hit * tp - (n_s - tp_hit) * sl) / n_s
            w(f"| TP=${tp} SL=${sl} | {n_s} | {pct(tp_hit, n_s)} | ${avg_pnl:.2f} | |")
    w()


def R11_reversal_pattern(daily, days_list):
    """1m down → 5m up (reversal) — the single strongest HOLD signal. Quantify entry timing."""
    w("## R11: Reversal Pattern Deep-Dive (1m Down → 5m Up)")
    w()
    w("Part F found: '1m DOWN → 5m UP = 72% bull, +$3.67 avg' (n=32). "
      "Find optimal entry timing for this reversal.")
    w()

    results = []
    for d_row, d_full in zip(daily.itertuples(), days_list):
        session = d_full["session"]
        open_px = d_row.open
        bar1 = session.iloc[0]
        is_1m_down = bar1["close"] < open_px
        is_5m_up   = d_row.above_5m

        if not (is_1m_down and is_5m_up):
            continue

        # When exactly did price cross back above open in bars 2-5?
        bars = session.between_time("09:31", "09:34")
        reclaim_bar = None
        reclaim_px  = None
        for i, bar in enumerate(bars.itertuples()):
            if bar.close >= open_px:
                reclaim_bar = i + 2  # bar number (1-indexed from open)
                reclaim_px  = bar.close
                break

        # Max dip below open in first 5m
        max_dip = open_px - d_row.low5m

        results.append({
            "date": d_row.date,
            "reclaim_bar": reclaim_bar,
            "max_dip": max_dip,
            "day_close_vs_open": d_row.day_close - open_px,
            "day_above": d_row.day_above,
            "day_high_above_open": d_row.day_high_above_open,
        })

    df = pd.DataFrame(results)
    n = len(df)
    w(f"Reversal days (1m red → 5m green): **{n} days**")
    w()

    if n > 5:
        w(f"- Day above open: {pct(df['day_above'].sum(), n)}")
        w(f"- Avg day close vs open: {avg(df['day_close_vs_open'])}")
        w(f"- Avg day high above open: {avg(df['day_high_above_open'])}")
        w(f"- Median max dip below open: {med(df['max_dip'])}")
        w()

        # Reclaim timing
        rc = df["reclaim_bar"].dropna()
        if len(rc) > 0:
            w("### Reclaim bar distribution")
            for bar_n in sorted(rc.unique()):
                cnt = (rc == bar_n).sum()
                label = {2: "9:31", 3: "9:32", 4: "9:33", 5: "9:34"}.get(int(bar_n), f"bar {int(bar_n)}")
                w(f"  - Reclaim at {label}: {cnt} days ({pct(cnt, n)})")
            w()

        # Dip depth split
        w("### Dip depth split")
        shallow = df[df["max_dip"] <= 1.0]
        medium  = df[(df["max_dip"] > 1.0) & (df["max_dip"] <= 3.0)]
        deep    = df[df["max_dip"] > 3.0]
        for label, sub in [("Shallow dip (≤$1)", shallow), ("Medium dip ($1-3)", medium), ("Deep dip (>$3)", deep)]:
            nn = len(sub)
            if nn == 0: continue
            da = pct(sub["day_above"].sum(), nn)
            dc = avg(sub["day_close_vs_open"])
            w(f"  - {label}: n={nn}, day_above={da}, avg_close={dc}")
    w()


def R12_vwap_cross_timing(daily, days_list, df_1m):
    """When does TSLA first cross VWAP? Early cross = strong day?"""
    w("## R12: VWAP Cross Timing")
    w()
    w("Compute intraday VWAP and find when price first crosses it. "
      "Early VWAP reclaim (before 10am) = strong day signal?")
    w()

    results = []
    for d_row, d_full in zip(daily.itertuples(), days_list):
        session = d_full["session"]
        if len(session) < 30:
            continue

        # Compute VWAP
        session = session.copy()
        session["tp"] = (session["high"] + session["low"] + session["close"]) / 3
        session["cumvol"] = session["volume"].cumsum()
        session["cumtpvol"] = (session["tp"] * session["volume"]).cumsum()
        session["vwap"] = session["cumtpvol"] / session["cumvol"].replace(0, np.nan)

        open_px = d_row.open
        open_time = session.index[0]

        # First cross above VWAP after 9:35
        after35 = session[session.index.time >= dtime(9, 35)]
        first_above_vwap = None
        for bar in after35.itertuples():
            if bar.close > bar.vwap:
                first_above_vwap = (bar.Index - open_time).seconds // 60
                break

        first_below_vwap = None
        for bar in after35.itertuples():
            if bar.close < bar.vwap:
                first_below_vwap = (bar.Index - open_time).seconds // 60
                break

        results.append({
            "date": d_row.date,
            "above_5m": d_row.above_5m,
            "day_above": d_row.day_above,
            "day_close_vs_open": d_row.day_close - open_px,
            "day_high_above_open": d_row.day_high_above_open,
            "first_above_vwap_min": first_above_vwap,
            "first_below_vwap_min": first_below_vwap,
        })

    df = pd.DataFrame(results)
    df_with_vwap = df.dropna(subset=["first_above_vwap_min"])

    w(f"Days with VWAP cross above (after 9:35): {len(df_with_vwap)} of {len(df)}")
    w()

    buckets = [
        ("Early cross (before 10am, <30m)",  df_with_vwap[df_with_vwap["first_above_vwap_min"] < 30]),
        ("Mid cross (10-11am, 30-90m)",       df_with_vwap[(df_with_vwap["first_above_vwap_min"] >= 30) & (df_with_vwap["first_above_vwap_min"] < 90)]),
        ("Late cross (after 11am, >90m)",     df_with_vwap[df_with_vwap["first_above_vwap_min"] >= 90]),
        ("Never above VWAP (after 9:35)",     df[df["first_above_vwap_min"].isna()]),
    ]

    w(f"| VWAP Cross Timing | Days | Day Above | Avg Day Close | Avg Day High |")
    w(f"|-------------------|------|-----------|---------------|--------------|")
    for label, sub in buckets:
        n = len(sub)
        if n == 0: continue
        da = pct(sub["day_above"].sum(), n)
        dc = avg(sub["day_close_vs_open"])
        dh = avg(sub["day_high_above_open"])
        w(f"| {label} | {n} | {da} | {dc} | {dh} |")
    w()


def R13_time_to_first_big_move(daily, days_list):
    """How quickly does TSLA make a $3/$5 move from open? Is speed predictive?"""
    w("## R13: Time-to-First-$3/$5 Move")
    w()

    results = []
    for d_row, d_full in zip(daily.itertuples(), days_list):
        session = d_full["session"]
        open_px = d_row.open
        open_time = session.index[0]
        t3_up = t5_up = t3_dn = t5_dn = None

        for bar in session.itertuples():
            mins = (bar.Index - open_time).seconds // 60
            if t3_up is None and bar.high >= open_px + 3:
                t3_up = mins
            if t5_up is None and bar.high >= open_px + 5:
                t5_up = mins
            if t3_dn is None and bar.low <= open_px - 3:
                t3_dn = mins
            if t5_dn is None and bar.low <= open_px - 5:
                t5_dn = mins

        results.append({
            "date": d_row.date,
            "day_above": d_row.day_above,
            "day_close_vs_open": d_row.day_close - open_px,
            "t3_up": t3_up, "t5_up": t5_up,
            "t3_dn": t3_dn, "t5_dn": t5_dn,
            "first_move_bull": t3_up is not None and (t3_dn is None or t3_up < t3_dn),
        })

    df = pd.DataFrame(results)
    w(f"n={len(df)} days")
    w()

    for target, col_up, col_dn in [("$3", "t3_up", "t3_dn"), ("$5", "t5_up", "t5_dn")]:
        hit_up = df[col_up].notna().sum()
        hit_dn = df[col_dn].notna().sum()
        w(f"**{target} move:**")
        w(f"- Hits +{target} up: {hit_up} days ({pct(hit_up, len(df))}), median {df[col_up].median():.0f}m after open")
        w(f"- Hits -{target} down: {hit_dn} days ({pct(hit_dn, len(df))}), median {df[col_dn].median():.0f}m after open")
        w()

    # Early $3 move (within 30m) — predictive of day direction?
    early_bull = df[(df["t3_up"].notna()) & (df["t3_up"] < 30) & df["first_move_bull"]]
    early_bear = df[(df["t3_dn"].notna()) & (df["t3_dn"] < 30) & ~df["first_move_bull"]]

    w(f"| Early Move (<30m) | Days | Day Above | Avg Day Close |")
    w(f"|-------------------|------|-----------|---------------|")
    for label, sub in [("Bull $3 within 30m", early_bull), ("Bear $3 within 30m", early_bear)]:
        n = len(sub)
        if n == 0: continue
        da = pct(sub["day_above"].sum(), n)
        dc = avg(sub["day_close_vs_open"])
        w(f"| {label} | {n} | {da} | {dc} |")
    w()


def R14_puts_only_5m_filter(daily):
    """Puts-only strategy over 271 days: enter when 5m below open."""
    w("## R14: Puts-Only with 5m Direction Filter (Full 271-Day Simulation)")
    w()
    w("Prior research only tested puts on 47-day downtrend window. "
      "Now: puts on any day where 5m close < open (the BAIL signal). "
      "Entry at 9:35, using day_low as SL proxy and day_high as TP obstacle.")
    w()

    df = daily.copy()
    # Signal: 5m below open
    signal = df[~df["above_5m"]].copy()
    signal["close_vs_open"] = signal["day_close"] - signal["open"]
    # For puts: profit if price falls; day_low = best case, day_high = worst case
    # Proxy: gain = open - day_close (raw directional); ignore path
    signal["put_raw"] = signal["open"] - signal["day_close"]

    n_sig = len(signal)
    w(f"Signal days (5m below open): {n_sig} of {len(df)} ({pct(n_sig, len(df))})")
    w()
    w(f"- Day ends below open (put wins raw): {pct((signal['day_close'] < signal['open']).sum(), n_sig)}")
    w(f"- Avg raw put P&L (open - day_close): {avg(signal['put_raw'])}")
    w(f"- Median raw put P&L: {med(signal['put_raw'])}")
    w()

    # TP/SL grid (using day_low_below_open as TP, day_high_above_open as risk)
    w("| Config | Trades | Win% (TP hit) | Avg Raw P&L |")
    w("|--------|--------|---------------|-------------|")
    for tp, sl in [(1.0, 0.5), (2.0, 1.0), (3.0, 1.5), (5.0, 2.0)]:
        tp_hit = (signal["day_low_below_open"] >= tp).sum()
        avg_pnl = (tp_hit * tp - (n_sig - tp_hit) * sl) / n_sig
        w(f"| TP=${tp} SL=${sl} | {n_sig} | {pct(tp_hit, n_sig)} | ${avg_pnl:.2f} |")
    w()

    # Combined: 5m below + 5m close further below (strong signal)
    w("### Enhanced: 5m close ≤ open-$2 (strong bear)")
    strong = signal[signal["close5m"] <= signal["open"] - 2.0]
    n_s = len(strong)
    w(f"Strong signal days: {n_s}")
    if n_s > 5:
        w(f"- Day ends below open: {pct((strong['day_close'] < strong['open']).sum(), n_s)}")
        for tp, sl in [(3.0, 1.5), (5.0, 2.0)]:
            tp_hit = (strong["day_low_below_open"] >= tp).sum()
            avg_pnl = (tp_hit * tp - (n_s - tp_hit) * sl) / n_s
            w(f"  TP=${tp}/SL=${sl}: win={pct(tp_hit, n_s)}, avg P&L=${avg_pnl:.2f}")
    w()


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    w(f"# TSLA Open-Scalp Deep Research")
    w(f"*Generated: {today}*")
    w()
    w("Extends prior open-scalp-learnings.md (Parts A-F). Investigates 14 new hypotheses.")
    w()

    notify("TSLA scalp research starting. Loading data (~30s)...")

    # Load data
    print("Loading 1m data...")
    df_1m_tsla = load_1m("TSLA")
    print("Loading 5m data...")
    df_5m_tsla = load_5m("TSLA")
    print("Loading SPY 1m data...")
    df_1m_spy  = load_1m("SPY")
    print("Building daily summaries...")
    daily_tsla, days_list_tsla = build_daily(df_1m_tsla)
    daily_spy,  _              = build_daily(df_1m_spy)

    n_days = len(daily_tsla)
    date_range = f"{daily_tsla['date'].min()} to {daily_tsla['date'].max()}"
    notify(f"Data loaded: {n_days} TSLA trading days ({date_range}). Starting 14 research modules...")

    save_report()

    modules = [
        ("R01: ORB Breakout",         lambda: R01_orb_breakout(daily_tsla, days_list_tsla)),
        ("R02: First Bar Size",        lambda: R02_first_bar_size(daily_tsla)),
        ("R03: Gap Tiers",             lambda: R03_gap_tiers(daily_tsla)),
        ("R04: PM Proximity",          lambda: R04_pm_proximity(daily_tsla)),
        ("R05: SPY Divergence",        lambda: R05_spy_divergence(daily_tsla, daily_spy)),
        ("R06: Multi-Day Trend",       lambda: R06_multi_day_trend(daily_tsla)),
        ("R07: Volume Signature",      lambda: R07_volume_signature(daily_tsla)),
        ("R08: ORB Width",             lambda: R08_orb_range_width(daily_tsla)),
        ("R09: Second-Chance Entry",   lambda: R09_second_chance_entry(daily_tsla, days_list_tsla)),
        ("R10: Combined Strat Sim",    lambda: R10_combined_strategy_sim(daily_tsla)),
        ("R11: Reversal Deep-Dive",    lambda: R11_reversal_pattern(daily_tsla, days_list_tsla)),
        ("R12: VWAP Cross Timing",     lambda: R12_vwap_cross_timing(daily_tsla, days_list_tsla, df_1m_tsla)),
        ("R13: Time-to-Big-Move",      lambda: R13_time_to_first_big_move(daily_tsla, days_list_tsla)),
        ("R14: Puts-Only 5m Filter",   lambda: R14_puts_only_5m_filter(daily_tsla)),
    ]

    key_findings = []

    for i, (name, fn) in enumerate(modules):
        print(f"\n{'='*50}")
        print(f"Running {name} ({i+1}/{len(modules)})...")
        try:
            fn()
            save_report()
            # Send progress every 3 modules
            if (i + 1) % 3 == 0:
                notify(f"TSLA research: {i+1}/{len(modules)} modules done. Latest: {name}. Report: tsla-scalp-research.md")
        except Exception as e:
            w(f"*Error in {name}: {e}*")
            w()
            print(f"  ERROR: {e}")
            save_report()

    # Final summary
    w("---")
    w()
    w("## Summary: Key Findings")
    w()
    w("*(Auto-generated placeholder — review the module outputs above for specific findings)*")
    w()
    w("### Questions for next session")
    w("1. Which modules showed strongest edges? Should we simulate those with actual options P&L (spread costs)?")
    w("2. R05 SPY divergence: if TSLA lags SPY at 5m, is that a buy or a warning?")
    w("3. R11 reversal: is the reclaim timing (9:31 vs 9:34) predictive of day strength?")
    w("4. R14 puts-only: is there a structural TSLA bearish bias at open worth exploiting?")
    w()

    save_report()
    notify(
        f"TSLA scalp research COMPLETE. {len(modules)} modules analyzed. "
        f"Report: debug/tsla-scalp-research.md. "
        f"Review findings and tell me which hypotheses to simulate with real P&L."
    )
    print("\nDone. Report written to tsla-scalp-research.md")


if __name__ == "__main__":
    main()
