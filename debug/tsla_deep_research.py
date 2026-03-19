#!/usr/bin/env python3
"""
TSLA Open-Scalp Deep Research — Phase 2
========================================
8 focused modules extending the prior 14-module research loop.
Addresses:
  D01  ORB + 5m rule agreement (all 4 combos)
  D02  ORB width × ORB direction
  D03  Puts-path simulation on 5s bars (bar-by-bar TP/SL)
  D04  Fix R05 SPY divergence (rebuild SPY day metrics cleanly)
  D05  Fix R06 multi-day trend (.values shift, no index issues)
  D06  Deep-dip reversal + ORB confirmation
  D07  VWAP timing as hold/bail modifier
  D08  ORB direction × gap size

Runs fully autonomously. Writes to tsla-scalp-deep.md. Sends Telegram updates.
"""

import os, sys, subprocess, warnings
from pathlib import Path
from datetime import datetime, time as dtime
import pandas as pd
import numpy as np
import pytz

warnings.filterwarnings("ignore")

# ── Paths ───────────────────────────────────────────────────────────────────
DEBUG_DIR   = Path(__file__).parent
CACHE_DIR   = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache")
BARS_DIR    = CACHE_DIR / "bars"
HIGHRES_DIR = CACHE_DIR / "bars_highres" / "5sec"
NOTIFY_PY   = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/personal_assistant/scripts/notify.py")
REPORT      = DEBUG_DIR / "tsla-scalp-deep.md"
LOG         = DEBUG_DIR / "tsla_deep_loop.log"
ET          = pytz.timezone("US/Eastern")


# ── Notify helper ────────────────────────────────────────────────────────────

def notify(msg: str):
    """Send Telegram notification and print to stdout."""
    print(f"[NOTIFY] {msg}")
    if NOTIFY_PY.exists():
        try:
            subprocess.run(
                [sys.executable, str(NOTIFY_PY), msg],
                capture_output=True, timeout=15
            )
        except Exception as e:
            print(f"  [notify error] {e}")


# ── Data loaders ─────────────────────────────────────────────────────────────

def _fix_tz(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure DatetimeIndex is in US/Eastern timezone."""
    idx = pd.DatetimeIndex(df.index)
    if idx.tzinfo is None:
        idx = idx.tz_localize("UTC")
    return df.set_axis(idx.tz_convert(ET), axis=0)


def load_1m(symbol: str = "TSLA") -> pd.DataFrame:
    f = BARS_DIR / f"{symbol.lower()}_1_min_ib.parquet"
    df = pd.read_parquet(f).set_index("date").sort_index()
    return _fix_tz(df)


def load_5s(symbol: str = "TSLA") -> pd.DataFrame | None:
    f = HIGHRES_DIR / f"{symbol.lower()}_5_secs_ib.parquet"
    if not f.exists():
        print(f"  [warn] 5s file not found: {f}")
        return None
    df = pd.read_parquet(f).set_index("date").sort_index()
    return _fix_tz(df)


# ── Daily summary builder (identical to prior script) ────────────────────────

def get_trading_days(df: pd.DataFrame):
    market = df.between_time("09:30", "15:59")
    return sorted(set(market.index.date))


def build_daily(df_1m: pd.DataFrame):
    """
    Build per-day summary. Returns (daily_df, days_list).
    days_list is a list of dicts; each dict includes key 'session' (the full
    1m session DataFrame for that day) for modules that need bar-by-bar access.
    """
    days = []
    for d in get_trading_days(df_1m):
        day     = df_1m[df_1m.index.date == d]
        session = day.between_time("09:30", "15:59")
        if len(session) < 10:
            continue

        open_px   = session.iloc[0]["open"]
        first5    = session.between_time("09:30", "09:34")
        first30   = session.between_time("09:30", "09:59")
        pre       = day.between_time("09:00", "09:29")

        if len(first5) < 3:
            continue

        close5m   = first5.iloc[-1]["close"]
        high5m    = first5["high"].max()
        low5m     = first5["low"].min()
        range5m   = high5m - low5m
        close30m  = first30.iloc[-1]["close"] if len(first30) >= 10 else np.nan

        day_high  = session["high"].max()
        day_low   = session["low"].min()
        day_close = session.iloc[-1]["close"]
        vol_open  = session.iloc[0]["volume"] if "volume" in session.columns else np.nan

        bar1       = session.iloc[0]
        bar1_range = bar1["high"] - bar1["low"]
        bar1_green = bar1["close"] >= open_px

        pm_high  = pre["high"].max()  if len(pre) > 0 else np.nan
        pm_low   = pre["low"].min()   if len(pre) > 0 else np.nan
        pm_close = pre.iloc[-1]["close"] if len(pre) > 0 else np.nan
        gap      = open_px - pm_close if not np.isnan(pm_close) else np.nan

        days.append({
            "date": d,
            "open": open_px,
            "close5m": close5m,
            "close30m": close30m,
            "bar1_close": bar1["close"],
            "bar1_range": bar1_range,
            "bar1_green": bar1_green,
            "high5m": high5m,
            "low5m": low5m,
            "range5m": range5m,
            "orb_high": high5m,
            "orb_low": low5m,
            "above_5m": close5m >= open_px,
            "day_high": day_high,
            "day_low": day_low,
            "day_close": day_close,
            "day_above": day_close >= open_px,
            "day_high_above_open": day_high - open_px,
            "day_low_below_open": open_px - day_low,
            "pm_high": pm_high,
            "pm_low": pm_low,
            "pm_close": pm_close,
            "gap": gap,
            "dip_5m": open_px - low5m,
            "vol_open_1m": vol_open,
            "session": session,
        })

    # Separate scalar dataframe from full dicts
    scalar_keys = [k for k in days[0].keys() if k != "session"]
    daily_df = pd.DataFrame([{k: r[k] for k in scalar_keys} for r in days])
    return daily_df, days


# ── ORB direction helper (shared by D01, D02, D06, D08) ─────────────────────

def compute_orb_direction(daily_df: pd.DataFrame, days_list: list) -> pd.DataFrame:
    """
    For each day: determine whether ORB High or ORB Low breaks first after 9:35.
    Returns daily_df with added columns: orb_bull_first, orb_bear_first, orb_neither.
    """
    results = []
    for row, d in zip(daily_df.itertuples(), days_list):
        session   = d["session"]
        after_orb = session.between_time("09:35", "15:59")
        orb_h     = row.orb_high
        orb_l     = row.orb_low
        bull_min  = None
        bear_min  = None

        for bar in after_orb.itertuples():
            if bull_min is None and bar.high > orb_h:
                bull_min = (bar.Index - session.index[0]).seconds // 60
            if bear_min is None and bar.low < orb_l:
                bear_min = (bar.Index - session.index[0]).seconds // 60
            if bull_min is not None and bear_min is not None:
                break

        bull_first = bull_min is not None and (bear_min is None or bull_min < bear_min)
        bear_first = bear_min is not None and (bull_min is None or bear_min < bull_min)
        results.append({
            "orb_bull_first": bull_first,
            "orb_bear_first": bear_first,
            "orb_neither":    not bull_first and not bear_first,
        })

    orb_df = pd.DataFrame(results)
    return pd.concat([daily_df.reset_index(drop=True), orb_df], axis=1)


# ── Formatting helpers ────────────────────────────────────────────────────────

def pct(x, n) -> str:
    return f"{100*x/n:.0f}%" if n > 0 else "N/A"

def avgf(series) -> str:
    s = series.dropna()
    return f"${s.mean():.2f}" if len(s) > 0 else "N/A"

def medf(series) -> str:
    s = series.dropna()
    return f"${s.median():.2f}" if len(s) > 0 else "N/A"


# ── Report writer ─────────────────────────────────────────────────────────────

_lines: list[str] = []

def w(s: str = ""):
    _lines.append(s)
    print(s)

def save_report():
    REPORT.write_text("\n".join(_lines))

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    entry = f"[{ts}] {msg}"
    print(entry)
    with open(LOG, "a") as f:
        f.write(entry + "\n")


# ══════════════════════════════════════════════════════════════════════════════
# RESEARCH MODULES
# ══════════════════════════════════════════════════════════════════════════════

def D01_orb_5m_agreement(daily_with_orb: pd.DataFrame):
    """
    D01: ORB direction × 5m rule — all 4 combinations.

    Prior research:
      - R01: ORB bull break → 70% day above
      - Prior Part F: 5m above open → 67% bull
    Question: when they agree vs conflict, what is the actual outcome?
    """
    w("## D01: ORB Direction × 5m Rule Agreement")
    w()
    w("Tests all 4 combos of ORB first-break direction and 5m-close vs open.")
    w("This shows whether the two signals are independent or redundant,")
    w("and which combination is most actionable.")
    w()

    df = daily_with_orb.copy()
    df["close_vs_open"] = df["day_close"] - df["open"]

    # 4 combinations: (ORB direction) × (5m above)
    combos = [
        ("ORB Bull + 5m Above (double bull)",  df[ df["orb_bull_first"] &  df["above_5m"]]),
        ("ORB Bull + 5m Below (conflict)",     df[ df["orb_bull_first"] & ~df["above_5m"]]),
        ("ORB Bear + 5m Above (conflict)",     df[~df["orb_bull_first"] &  df["above_5m"] & ~df["orb_neither"]]),
        ("ORB Bear + 5m Below (double bear)",  df[ df["orb_bear_first"] & ~df["above_5m"]]),
        ("ORB Neither (no break)",             df[ df["orb_neither"]]),
        ("ALL days (baseline)",                df),
    ]

    w("| Combo | Days | Day Above % | Avg Day Close | Avg Day High | Avg Day Low |")
    w("|-------|------|-------------|---------------|--------------|-------------|")
    for label, sub in combos:
        n = len(sub)
        if n == 0:
            continue
        da  = pct(sub["day_above"].sum(), n)
        dc  = avgf(sub["close_vs_open"])
        dh  = avgf(sub["day_high_above_open"])
        dl  = avgf(-sub["day_low_below_open"])   # negative = below open
        w(f"| {label} | {n} | {da} | {dc} | {dh} | {dl} |")
    w()

    # Conflict days detail
    conflict = df[(df["orb_bull_first"] & ~df["above_5m"]) |
                  (~df["orb_bull_first"] & df["above_5m"] & ~df["orb_neither"])]
    n_c = len(conflict)
    if n_c > 0:
        w(f"**Conflict days** (ORB vs 5m disagree): {n_c} days = "
          f"{pct(n_c, len(df))} of all days")
        w(f"- Day above open: {pct(conflict['day_above'].sum(), n_c)}")
        w(f"- Avg close vs open: {avgf(conflict['close_vs_open'])}")
        w()

    w(f"*n={len(df)} total trading days*")
    w()


def D02_orb_width_x_direction(daily_with_orb: pd.DataFrame):
    """
    D02: ORB width × ORB direction.

    R08 found: narrow ORB (≤$3.73) → 40% day above (bearish tilt).
    But did narrow ORB break bull or bear first? Width may only matter
    in the context of the breakout direction.
    """
    w("## D02: ORB Width × ORB Direction")
    w()
    w("Narrow ORB alone showed 40% bull days. But does ORB direction override?")
    w("Split by width quartile AND ORB break direction.")
    w()

    df = daily_with_orb.dropna(subset=["range5m"]).copy()
    df["close_vs_open"] = df["day_close"] - df["open"]

    q25, q50 = df["range5m"].quantile([0.25, 0.50]).values

    width_buckets = [
        (f"Narrow ORB (≤${q25:.2f})", df[df["range5m"] <= q25]),
        (f"Mid ORB (${q25:.2f}-${q50:.2f})", df[(df["range5m"] > q25) & (df["range5m"] <= q50)]),
        (f"Wide ORB (>${q50:.2f})", df[df["range5m"] > q50]),
    ]

    w("| ORB Width | Break Direction | Days | Day Above % | Avg Day Close | Avg Day High |")
    w("|-----------|-----------------|------|-------------|---------------|--------------|")
    for width_label, wdf in width_buckets:
        for dir_label, cond in [
            ("Bull break first", wdf["orb_bull_first"]),
            ("Bear break first", wdf["orb_bear_first"]),
            ("Neither",          wdf["orb_neither"]),
        ]:
            sub = wdf[cond]
            n   = len(sub)
            if n < 3:
                continue
            da  = pct(sub["day_above"].sum(), n)
            dc  = avgf(sub["close_vs_open"])
            dh  = avgf(sub["day_high_above_open"])
            w(f"| {width_label} | {dir_label} | {n} | {da} | {dc} | {dh} |")
    w()

    # Narrow ORB breakdown special focus (R08 finding)
    narrow = df[df["range5m"] <= q25]
    w(f"**Narrow ORB focus** (≤${q25:.2f}, n={len(narrow)}):")
    bull_n = narrow[narrow["orb_bull_first"]]
    bear_n = narrow[narrow["orb_bear_first"]]
    if len(bull_n) > 0:
        w(f"- Narrow + bull break: {len(bull_n)} days → {pct(bull_n['day_above'].sum(), len(bull_n))} day above, avg close {avgf(bull_n['close_vs_open'])}")
    if len(bear_n) > 0:
        w(f"- Narrow + bear break: {len(bear_n)} days → {pct(bear_n['day_above'].sum(), len(bear_n))} day above, avg close {avgf(bear_n['close_vs_open'])}")
    w()


def D03_puts_path_5s_simulation(daily_df: pd.DataFrame, df_5s: pd.DataFrame | None):
    """
    D03: Bar-by-bar puts simulation on 5s data.

    R14 showed: 5m close ≤ open-$2 → TP=$3 appears to hit 100% (using day H/L proxy).
    But the proxy assumes TP always hits before SL, which is wrong on path-dependent options.

    This module verifies using actual 5s bars:
      - Signal: 5m close ≤ open - $2 (strong bear)
      - Entry: short at first 5s bar on or after 09:35:00
      - TP: open - $3  (put profit target)
      - SL: open + $1.50 (put stop loss)
      - Check SL BEFORE TP on each bar (conservative)
    """
    w("## D03: Puts-Path Simulation (5s Bars, Bar-by-Bar)")
    w()
    w("Signal: 5m close ≤ open−$2. Enter short at 9:35. TP=open−$3, SL=open+$1.50.")
    w("Bar-by-bar on 5s data: SL is checked before TP on each bar (conservative).")
    w()

    if df_5s is None:
        w("*5s data not available. Skipping.*")
        w()
        return

    # Filter signal days
    signal_days = daily_df[daily_df["close5m"] <= daily_df["open"] - 2.0].copy()
    n_sig = len(signal_days)
    w(f"Signal days (5m close ≤ open−$2): **{n_sig}** of {len(daily_df)}")
    w()

    if n_sig == 0:
        w("No signal days found.")
        w()
        return

    results = []
    for row in signal_days.itertuples():
        d      = row.date
        open_px = row.open
        tp_px  = open_px - 3.0
        sl_px  = open_px + 1.50

        # Get 5s bars for this day, starting at 9:35
        day_5s = df_5s[df_5s.index.date == d]
        after_entry = day_5s[day_5s.index.time >= dtime(9, 35)]

        if len(after_entry) < 5:
            # Not enough 5s bars — skip (don't include in stats)
            continue

        # Entry at the first bar's open
        entry_px = after_entry.iloc[0]["open"]
        outcome  = "open_till_close"  # default: no TP or SL hit
        exit_px  = day_5s[day_5s.index.date == d].iloc[-1]["close"]
        mins_to_exit = len(after_entry) * 5 / 60  # approximate

        for i, bar in enumerate(after_entry.itertuples()):
            # On each bar: check low (bearish path) and high (adverse move)
            # For a short position: SL = price going UP, TP = price going DOWN
            if bar.high >= sl_px:
                outcome    = "SL"
                exit_px    = sl_px
                mins_to_exit = i * 5 / 60
                break
            if bar.low <= tp_px:
                outcome    = "TP"
                exit_px    = tp_px
                mins_to_exit = i * 5 / 60
                break

        # P&L for a short: entry - exit (positive = profit)
        pnl = entry_px - exit_px

        results.append({
            "date":          d,
            "open":          open_px,
            "entry":         entry_px,
            "tp_px":         tp_px,
            "sl_px":         sl_px,
            "outcome":       outcome,
            "exit_px":       exit_px,
            "pnl":           pnl,
            "mins_to_exit":  mins_to_exit,
        })

    if not results:
        w("No trades simulated (insufficient 5s bars on signal days).")
        w()
        return

    df = pd.DataFrame(results)
    n = len(df)
    tp_hits   = (df["outcome"] == "TP").sum()
    sl_hits   = (df["outcome"] == "SL").sum()
    open_eod  = (df["outcome"] == "open_till_close").sum()

    w(f"**Simulated {n} trades** (may be fewer than signal days if 5s data missing):")
    w(f"- TP hit (open−$3): {tp_hits} ({pct(tp_hits, n)}) ← actual path-verified")
    w(f"- SL hit (open+$1.50): {sl_hits} ({pct(sl_hits, n)})")
    w(f"- No exit (held to EOD): {open_eod} ({pct(open_eod, n)})")
    w()

    avg_pnl  = df["pnl"].mean()
    med_pnl  = df["pnl"].median()
    avg_mins = df["mins_to_exit"].mean()

    w(f"**P&L (stock price, short):**")
    w(f"- Avg P&L: ${avg_pnl:.2f}")
    w(f"- Median P&L: ${med_pnl:.2f}")
    w(f"- Avg time to exit: {avg_mins:.0f} min")
    w()

    # Breakdown by outcome
    w("| Outcome | Trades | Avg P&L | Avg Min to Exit |")
    w("|---------|--------|---------|-----------------|")
    for label in ["TP", "SL", "open_till_close"]:
        sub = df[df["outcome"] == label]
        nn  = len(sub)
        if nn == 0:
            continue
        ap  = sub["pnl"].mean()
        am  = sub["mins_to_exit"].mean()
        w(f"| {label} | {nn} | ${ap:.2f} | {am:.0f}m |")
    w()

    # Compare with prior R14 proxy (no path check)
    w("**Comparison with R14 proxy (day L/H only, no path):**")
    tp_proxy = (daily_df["close5m"] <= daily_df["open"] - 2.0) & \
               (daily_df["day_low_below_open"] >= 3.0)
    n_proxy  = (daily_df["close5m"] <= daily_df["open"] - 2.0).sum()
    n_tp_p   = tp_proxy.sum()
    w(f"- R14 proxy TP hits: {n_tp_p}/{n_proxy} = {pct(n_tp_p, n_proxy)}")
    w(f"- D03 actual TP hits: {tp_hits}/{n} = {pct(tp_hits, n)}")
    w(f"- **Verdict:** {'Path check reduced win rate' if tp_hits/n < n_tp_p/n_proxy*0.9 else 'Path check confirms high win rate'}")
    w()


def D04_spy_divergence_fixed(daily_tsla: pd.DataFrame, daily_spy: pd.DataFrame):
    """
    D04: Fix R05 SPY divergence.

    R05 failed because 'day_high_above_open' was missing from SPY daily.
    Fix: rebuild SPY daily metrics internally so all required columns exist.
    Show TSLA outcome for all 4 combinations of TSLA/SPY day direction.
    """
    w("## D04: TSLA vs SPY Day Direction (R05 Fixed)")
    w()
    w("Both TSLA and SPY daily summaries are built with the same build_daily().")
    w("Join on date and cross-tabulate day direction (up/down).")
    w()

    # Compute needed SPY metrics — daily_spy already has day_above from build_daily
    t = daily_tsla.set_index("date")[
        ["above_5m", "day_above", "day_close", "open",
         "day_high_above_open", "day_low_below_open"]
    ].copy()
    t["close_vs_open"] = t["day_close"] - t["open"]

    s = daily_spy.set_index("date")[["day_above"]].rename(
        columns={"day_above": "spy_day_above"}
    )

    merged = t.join(s, how="inner").dropna(subset=["spy_day_above"])
    n_total = len(merged)
    w(f"Days with both TSLA + SPY data: {n_total}")
    w()

    combos = [
        ("TSLA Up / SPY Up",   merged[ merged["day_above"] &  merged["spy_day_above"]]),
        ("TSLA Up / SPY Down", merged[ merged["day_above"] & ~merged["spy_day_above"]]),
        ("TSLA Down / SPY Up", merged[~merged["day_above"] &  merged["spy_day_above"]]),
        ("TSLA Down / SPY Down", merged[~merged["day_above"] & ~merged["spy_day_above"]]),
    ]

    w("| Scenario | Days | TSLA 5m Above | Avg TSLA Close | Avg TSLA High |")
    w("|----------|------|---------------|----------------|---------------|")
    for label, sub in combos:
        n = len(sub)
        if n == 0:
            continue
        f5  = pct(sub["above_5m"].sum(), n)
        dc  = avgf(sub["close_vs_open"])
        dh  = avgf(sub["day_high_above_open"])
        w(f"| {label} | {n} | {f5} | {dc} | {dh} |")
    w()

    # 5m divergence (original R05 intent): TSLA 5m vs SPY 5m at 9:35
    spy_5m = daily_spy.set_index("date")[["above_5m"]].rename(
        columns={"above_5m": "spy_above_5m"}
    )
    merged2 = t.join(spy_5m, how="inner").dropna(subset=["spy_above_5m"])
    w(f"### 5m Divergence (at 9:35) — n={len(merged2)} days")
    w()
    combos_5m = [
        ("TSLA↑ SPY↑ (agree bull)",  merged2[ merged2["above_5m"] &  merged2["spy_above_5m"]]),
        ("TSLA↑ SPY↓ (TSLA leads)", merged2[ merged2["above_5m"] & ~merged2["spy_above_5m"]]),
        ("TSLA↓ SPY↑ (TSLA lags)",  merged2[~merged2["above_5m"] &  merged2["spy_above_5m"]]),
        ("TSLA↓ SPY↓ (agree bear)", merged2[~merged2["above_5m"] & ~merged2["spy_above_5m"]]),
    ]
    w("| 5m Scenario | Days | TSLA Day Above | Avg TSLA Close | Avg TSLA High |")
    w("|-------------|------|----------------|----------------|---------------|")
    for label, sub in combos_5m:
        n = len(sub)
        if n == 0:
            continue
        da  = pct(sub["day_above"].sum(), n)
        dc  = avgf(sub["close_vs_open"])
        dh  = avgf(sub["day_high_above_open"])
        w(f"| {label} | {n} | {da} | {dc} | {dh} |")
    w()


def D05_multi_day_trend_fixed(daily_df: pd.DataFrame):
    """
    D05: Fix R06 multi-day trend.

    R06 failed because boolean Series.shift() on non-reset index caused NaN misalignment.
    Fix: sort by date, reset_index, use .values for the boolean array before shifting,
    then create new columns from plain numpy arrays.
    """
    w("## D05: Multi-Day Prior Trend as Predictor (R06 Fixed)")
    w()
    w("Does prior 3-day direction predict today's open behavior?")
    w("Fix: use numpy .values to avoid index misalignment in boolean shifts.")
    w()

    df = daily_df.copy().sort_values("date").reset_index(drop=True)
    df["close_vs_open"] = df["day_close"] - df["open"]

    # Use numpy array for shift to avoid index-based alignment issues
    day_above_arr = df["day_above"].values.astype(bool)
    df["prev1"] = np.concatenate([[np.nan], day_above_arr[:-1]])
    df["prev2"] = np.concatenate([[np.nan, np.nan], day_above_arr[:-2]])
    df["prev3"] = np.concatenate([[np.nan, np.nan, np.nan], day_above_arr[:-3]])

    df = df.dropna(subset=["prev1", "prev2", "prev3"]).copy()
    df["prev1"] = df["prev1"].astype(bool)
    df["prev2"] = df["prev2"].astype(bool)
    df["prev3"] = df["prev3"].astype(bool)

    buckets = [
        ("3 bull days prior",             df[ df["prev1"] &  df["prev2"] &  df["prev3"]]),
        ("2 bull + 1 bear (prev3 bear)",  df[ df["prev1"] &  df["prev2"] & ~df["prev3"]]),
        ("1 bull + 2 bear (prev2-3 bear)",df[ df["prev1"] & ~df["prev2"] & ~df["prev3"]]),
        ("3 bear days prior",             df[~df["prev1"] & ~df["prev2"] & ~df["prev3"]]),
        ("Prev day bull (any)",           df[ df["prev1"]]),
        ("Prev day bear (any)",           df[~df["prev1"]]),
        ("ALL days (baseline)",           df),
    ]

    w("| Prior 3 Days | Days | 5m Above | Day Above | Avg Day Close | Avg Day High |")
    w("|--------------|------|----------|-----------|---------------|--------------|")
    for label, sub in buckets:
        n = len(sub)
        if n == 0:
            continue
        f5  = pct(sub["above_5m"].sum(), n)
        da  = pct(sub["day_above"].sum(), n)
        dc  = avgf(sub["close_vs_open"])
        dh  = avgf(sub["day_high_above_open"])
        w(f"| {label} | {n} | {f5} | {da} | {dc} | {dh} |")
    w()

    # Streaks: consecutive bull or bear days
    w("### Streak analysis (prior 5 days)")
    df["streak"] = 0
    for i in range(1, len(df)):
        prev_streak = df.loc[i-1, "streak"]
        if df.loc[i-1, "day_above"]:
            df.loc[i, "streak"] = max(prev_streak + 1, 1)
        else:
            df.loc[i, "streak"] = min(prev_streak - 1, -1)

    for streak_val, label in [
        (3, "After 3+ bull days"),
        (4, "After 4+ bull days"),
        (-3, "After 3+ bear days"),
        (-4, "After 4+ bear days"),
    ]:
        if streak_val > 0:
            sub = df[df["streak"] >= streak_val]
        else:
            sub = df[df["streak"] <= streak_val]
        n = len(sub)
        if n < 3:
            continue
        da = pct(sub["day_above"].sum(), n)
        dc = avgf(sub["close_vs_open"])
        w(f"- {label}: n={n}, day_above={da}, avg close={dc}")
    w()


def D06_deep_dip_reversal_plus_orb(daily_with_orb: pd.DataFrame, days_list: list):
    """
    D06: Deep dip reversal + ORB direction confirmation.

    R11 found: deep dip >$3 then recovers (1m down → 5m up) = 70% bull day.
    Question: when ORB also breaks bull first, does it raise the win rate further?
    And what happens on reversal days where ORB breaks bear?
    """
    w("## D06: Deep Dip Reversal × ORB Confirmation")
    w()
    w("R11: reversal day (1m red → 5m green) = 70% bull. "
      "Does ORB direction improve that? Or contradict it?")
    w()

    results = []
    for row, d in zip(daily_with_orb.itertuples(), days_list):
        session = d["session"]
        open_px = row.open
        bar1    = session.iloc[0]

        is_1m_red  = bar1["close"] < open_px
        is_5m_green = row.above_5m
        is_reversal = is_1m_red and is_5m_green
        max_dip     = open_px - row.low5m   # positive = dipped below open

        results.append({
            "date":               row.date,
            "is_reversal":        is_reversal,
            "max_dip":            max_dip,
            "deep_dip":           max_dip > 3.0,
            "orb_bull_first":     row.orb_bull_first,
            "orb_bear_first":     row.orb_bear_first,
            "day_above":          row.day_above,
            "day_close_vs_open":  row.day_close - open_px,
            "day_high_above_open": row.day_high_above_open,
        })

    df = pd.DataFrame(results)
    rev      = df[df["is_reversal"]]
    non_rev  = df[~df["is_reversal"]]

    w(f"Reversal days (1m red → 5m green): **{len(rev)}** of {len(df)}")
    w()

    # Reversal days: split by ORB direction
    w("### Reversal days × ORB direction")
    w("| Sub-group | Days | Day Above | Avg Day Close | Avg Day High |")
    w("|-----------|------|-----------|---------------|--------------|")
    combos = [
        ("Rev + ORB Bull (double confirmation)", rev[ rev["orb_bull_first"]]),
        ("Rev + ORB Bear (contradiction)",        rev[ rev["orb_bear_first"]]),
        ("Rev + ORB Neither",                     rev[ rev["orb_bull_first"] == False][rev["orb_bear_first"] == False]),
        ("Rev ALL (baseline)",                    rev),
        ("Non-reversal + ORB Bull",               non_rev[non_rev["orb_bull_first"]]),
        ("Non-reversal ALL (baseline)",           non_rev),
    ]
    for label, sub in combos:
        n = len(sub)
        if n < 3:
            continue
        da  = pct(sub["day_above"].sum(), n)
        dc  = avgf(sub["day_close_vs_open"])
        dh  = avgf(sub["day_high_above_open"])
        w(f"| {label} | {n} | {da} | {dc} | {dh} |")
    w()

    # Deep dip reversal (>$3) split
    w("### Deep dip reversal (>$3) × ORB direction")
    deep_rev = rev[rev["deep_dip"]]
    w(f"Deep dip reversal days (dip >$3 + 1m red → 5m green): **{len(deep_rev)}**")
    if len(deep_rev) >= 3:
        for label, sub in [
            ("Deep rev + ORB Bull", deep_rev[deep_rev["orb_bull_first"]]),
            ("Deep rev + ORB Bear", deep_rev[deep_rev["orb_bear_first"]]),
            ("Deep rev ALL",        deep_rev),
        ]:
            n = len(sub)
            if n < 2:
                continue
            da  = pct(sub["day_above"].sum(), n)
            dc  = avgf(sub["day_close_vs_open"])
            w(f"  - {label}: n={n}, day_above={da}, avg close={dc}")
    w()


def D07_vwap_timing_as_exit(daily_df: pd.DataFrame, days_list: list):
    """
    D07: VWAP cross timing as hold/bail modifier.

    R12 found late VWAP cross = bad day. Now: for days where 5m is above open
    (hold signal), does the VWAP cross timing predict whether to exit early?
    Split: early VWAP (<30m), mid (30-90m), late (>90m), never crosses.
    """
    w("## D07: VWAP Cross Timing as Exit Signal (for 5m-Above Days)")
    w()
    w("On HOLD days (5m above open), when TSLA crosses VWAP affects outcome.")
    w("Early VWAP reclaim = strong. Late = exit signal.")
    w()

    results = []
    for row, d in zip(daily_df.itertuples(), days_list):
        session = d["session"]
        if len(session) < 30:
            continue

        # Compute VWAP intraday (requires volume)
        if "volume" not in session.columns:
            continue
        s = session.copy()
        s["tp"]       = (s["high"] + s["low"] + s["close"]) / 3
        cumvol        = s["volume"].cumsum().replace(0, np.nan)
        s["vwap"]     = (s["tp"] * s["volume"]).cumsum() / cumvol
        open_px       = row.open
        open_time     = session.index[0]

        # First cross ABOVE VWAP (for hold days: bullish reclaim)
        after35 = s[s.index.time >= dtime(9, 35)]
        first_above_vwap_min = None
        for bar in after35.itertuples():
            if hasattr(bar, 'vwap') and not np.isnan(bar.vwap) and bar.close > bar.vwap:
                first_above_vwap_min = (bar.Index - open_time).seconds // 60
                break

        # First cross BELOW VWAP (exit signal)
        first_below_vwap_min = None
        for bar in after35.itertuples():
            if hasattr(bar, 'vwap') and not np.isnan(bar.vwap) and bar.close < bar.vwap:
                first_below_vwap_min = (bar.Index - open_time).seconds // 60
                break

        results.append({
            "date":                   row.date,
            "above_5m":               row.above_5m,
            "day_above":              row.day_above,
            "day_close_vs_open":      row.day_close - open_px,
            "day_high_above_open":    row.day_high_above_open,
            "first_above_vwap_min":   first_above_vwap_min,
            "first_below_vwap_min":   first_below_vwap_min,
        })

    df = pd.DataFrame(results)
    hold_days = df[df["above_5m"]]
    n_hold = len(hold_days)
    w(f"Hold days (5m above open): **{n_hold}** of {len(df)}")
    w()

    # VWAP cross timing split (for hold days only)
    hd = hold_days.copy()
    buckets = [
        ("Early VWAP reclaim (<30m)",     hd[hd["first_above_vwap_min"] < 30]),
        ("Mid VWAP reclaim (30-90m)",      hd[(hd["first_above_vwap_min"] >= 30) & (hd["first_above_vwap_min"] < 90)]),
        ("Late VWAP reclaim (>90m)",       hd[hd["first_above_vwap_min"] >= 90]),
        ("Never above VWAP after 9:35",   hd[hd["first_above_vwap_min"].isna()]),
        ("ALL hold days (baseline)",       hd),
    ]

    w("| VWAP Timing (Hold Days) | Days | Day Above | Avg Day Close | Avg Day High |")
    w("|-------------------------|------|-----------|---------------|--------------|")
    for label, sub in buckets:
        n = len(sub)
        if n == 0:
            continue
        da  = pct(sub["day_above"].sum(), n)
        dc  = avgf(sub["day_close_vs_open"])
        dh  = avgf(sub["day_high_above_open"])
        w(f"| {label} | {n} | {da} | {dc} | {dh} |")
    w()

    # For late VWAP cross: if we exit at VWAP (open approx), what is the P&L?
    late = hd[hd["first_above_vwap_min"] >= 90].dropna(subset=["first_above_vwap_min"])
    if len(late) > 0:
        w(f"**Late VWAP cross ({len(late)} days):** "
          f"day above={pct(late['day_above'].sum(), len(late))}, "
          f"avg close={avgf(late['day_close_vs_open'])}")
        w("If exited at VWAP cross (stock ≈ open), would have avoided negative days.")
    w()

    # Also: for BAIL days (5m below open), does early VWAP cross signal reversal?
    bail_days = df[~df["above_5m"]]
    n_bail = len(bail_days)
    if n_bail > 0:
        w(f"### Bail days (5m below open): VWAP as reversal signal")
        w(f"Bail days with early VWAP cross above (<30m): potential reversal?")
        bail_early = bail_days[bail_days["first_above_vwap_min"] < 30]
        n_be = len(bail_early)
        if n_be > 2:
            w(f"- Bail + early VWAP reclaim: {n_be} days → "
              f"day above={pct(bail_early['day_above'].sum(), n_be)}, "
              f"avg close={avgf(bail_early['day_close_vs_open'])}")
        bail_no_vwap = bail_days[bail_days["first_above_vwap_min"].isna()]
        n_bnv = len(bail_no_vwap)
        if n_bnv > 2:
            w(f"- Bail + never crosses VWAP: {n_bnv} days → "
              f"day above={pct(bail_no_vwap['day_above'].sum(), n_bnv)}, "
              f"avg close={avgf(bail_no_vwap['day_close_vs_open'])}")
    w()


def D08_orb_direction_x_gap(daily_with_orb: pd.DataFrame):
    """
    D08: ORB direction × gap size.

    Does the overnight gap direction reinforce or contradict the ORB breakout signal?
    E.g., gap up + ORB bull = strong? Gap up + ORB bear = fade?
    """
    w("## D08: ORB Direction × Gap Size")
    w()
    w("Does gap direction reinforce or contradict ORB direction signal?")
    w("Gap up + ORB bull = momentum? Gap up + ORB bear = gap fade?")
    w()

    df = daily_with_orb.dropna(subset=["gap"]).copy()
    df["close_vs_open"] = df["day_close"] - df["open"]
    df["gap_up"]   = df["gap"] > 1.0    # gap up > $1
    df["gap_down"] = df["gap"] < -1.0   # gap down > $1
    df["gap_flat"] = df["gap"].abs() <= 1.0

    combos = [
        ("Gap Up + ORB Bull",   df[ df["gap_up"]   &  df["orb_bull_first"]]),
        ("Gap Up + ORB Bear",   df[ df["gap_up"]   &  df["orb_bear_first"]]),
        ("Gap Up + Neither",    df[ df["gap_up"]   &  df["orb_neither"]]),
        ("Gap Flat + ORB Bull", df[ df["gap_flat"] &  df["orb_bull_first"]]),
        ("Gap Flat + ORB Bear", df[ df["gap_flat"] &  df["orb_bear_first"]]),
        ("Gap Down + ORB Bull", df[ df["gap_down"] &  df["orb_bull_first"]]),
        ("Gap Down + ORB Bear", df[ df["gap_down"] &  df["orb_bear_first"]]),
        ("Gap Down + Neither",  df[ df["gap_down"] &  df["orb_neither"]]),
        ("ALL days",            df),
    ]

    w("| Gap × ORB | Days | Day Above | Avg Day Close | Avg Day High | Avg Day Low |")
    w("|-----------|------|-----------|---------------|--------------|-------------|")
    for label, sub in combos:
        n = len(sub)
        if n < 3:
            continue
        da  = pct(sub["day_above"].sum(), n)
        dc  = avgf(sub["close_vs_open"])
        dh  = avgf(sub["day_high_above_open"])
        dl  = avgf(-sub["day_low_below_open"])
        w(f"| {label} | {n} | {da} | {dc} | {dh} | {dl} |")
    w()

    # Extreme gaps
    extreme_up   = df[df["gap"] >  5.0]
    extreme_down = df[df["gap"] < -5.0]
    for label, sub in [("Extreme gap up (>$5)", extreme_up), ("Extreme gap down (<-$5)", extreme_down)]:
        n = len(sub)
        if n < 3:
            continue
        orb_agrees = (
            (sub["gap_up"] & sub["orb_bull_first"]) |
            (~sub["gap_up"] & sub["orb_bear_first"])
        ).sum()
        w(f"**{label}** (n={n}): ORB agrees with gap direction = {pct(orb_agrees, n)}, "
          f"day above={pct(sub['day_above'].sum(), n)}")
    w()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    log(f"tsla_deep_research.py starting — {today}")

    # ── Report header ─────────────────────────────────────────────────────
    w(f"# TSLA Open-Scalp Deep Research — Phase 2")
    w(f"*Generated: {today}*")
    w()
    w("8 focused modules extending the prior 14-module research loop (tsla-scalp-research.md).")
    w()
    w("**Modules:**")
    w("- D01: ORB direction × 5m rule agreement (all 4 combos)")
    w("- D02: ORB width × ORB direction")
    w("- D03: Puts-path simulation on 5s bars (bar-by-bar, SL checked before TP)")
    w("- D04: Fix R05 SPY divergence")
    w("- D05: Fix R06 multi-day trend")
    w("- D06: Deep dip reversal × ORB confirmation")
    w("- D07: VWAP cross timing as hold/bail modifier")
    w("- D08: ORB direction × gap size")
    w()
    w("---")
    w()

    notify("TSLA deep research Phase 2 starting. Loading data...")

    # ── Load data ─────────────────────────────────────────────────────────
    log("Loading TSLA 1m...")
    df_1m_tsla = load_1m("TSLA")

    log("Loading SPY 1m...")
    df_1m_spy = load_1m("SPY")

    log("Loading TSLA 5s...")
    df_5s_tsla = load_5s("TSLA")

    log("Building TSLA daily summary...")
    daily_tsla, days_list_tsla = build_daily(df_1m_tsla)

    log("Building SPY daily summary...")
    daily_spy, _ = build_daily(df_1m_spy)

    log("Computing ORB directions...")
    daily_with_orb = compute_orb_direction(daily_tsla, days_list_tsla)

    n_days   = len(daily_tsla)
    date_min = daily_tsla["date"].min()
    date_max = daily_tsla["date"].max()
    log(f"Data ready: {n_days} TSLA days ({date_min} to {date_max})")
    notify(f"Data loaded: {n_days} TSLA days ({date_min} to {date_max}). Running 8 modules...")

    save_report()

    # ── Module runner ─────────────────────────────────────────────────────
    modules = [
        ("D01: ORB + 5m Agreement",
         lambda: D01_orb_5m_agreement(daily_with_orb)),

        ("D02: ORB Width × Direction",
         lambda: D02_orb_width_x_direction(daily_with_orb)),

        ("D03: Puts 5s Simulation",
         lambda: D03_puts_path_5s_simulation(daily_tsla, df_5s_tsla)),

        ("D04: SPY Divergence (fixed)",
         lambda: D04_spy_divergence_fixed(daily_tsla, daily_spy)),

        ("D05: Multi-Day Trend (fixed)",
         lambda: D05_multi_day_trend_fixed(daily_tsla)),

        ("D06: Deep Dip + ORB",
         lambda: D06_deep_dip_reversal_plus_orb(daily_with_orb, days_list_tsla)),

        ("D07: VWAP Timing Exit",
         lambda: D07_vwap_timing_as_exit(daily_tsla, days_list_tsla)),

        ("D08: ORB × Gap Size",
         lambda: D08_orb_direction_x_gap(daily_with_orb)),
    ]

    completed = []
    failed    = []

    for i, (name, fn) in enumerate(modules):
        print(f"\n{'='*60}")
        log(f"Running {name} ({i+1}/{len(modules)})...")
        try:
            fn()
            save_report()
            completed.append(name)
            # Notify after each module with a key snippet
            notify(f"[{i+1}/{len(modules)}] {name} done. Check tsla-scalp-deep.md.")
        except Exception as e:
            import traceback
            err = traceback.format_exc()
            w(f"*ERROR in {name}: {e}*")
            w()
            log(f"  ERROR in {name}: {e}")
            log(err)
            failed.append((name, str(e)))
            save_report()

    # ── Final summary ─────────────────────────────────────────────────────
    w("---")
    w()
    w("## Summary")
    w()
    w(f"Completed: {len(completed)}/{len(modules)} modules")
    if failed:
        w()
        w("### Errors")
        for name, err in failed:
            w(f"- **{name}**: {err}")
    w()
    w("### Action items")
    w("1. D01: If double-bull (ORB bull + 5m above) is ≥75% → use as primary entry filter")
    w("2. D01: If conflict combos are still 50/50 → ignore either signal when they disagree")
    w("3. D02: If narrow ORB + bull break is strong → add width filter to entry rules")
    w("4. D03: If actual path TP% < R14 proxy → R14 was overfit; re-size TP/SL targets")
    w("5. D06: If deep-dip + ORB bull ≥80% → strongest bull signal in dataset")
    w("6. D07: If late VWAP cross on hold days = negative day → use as hard exit rule")
    w("7. D08: If gap + ORB agreement > 80% → combined signal for opening momentum")
    w()

    save_report()

    summary = (
        f"TSLA deep research Phase 2 COMPLETE. "
        f"{len(completed)}/{len(modules)} modules done. "
        f"{'Errors: ' + str(len(failed)) + '.' if failed else 'No errors.'} "
        f"Report: debug/tsla-scalp-deep.md"
    )
    log(summary)
    notify(summary)
    print(f"\nDone. Report: {REPORT}")


if __name__ == "__main__":
    main()
