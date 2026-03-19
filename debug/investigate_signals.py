#!/usr/bin/env python3
"""
KLB Signal Investigation — v3.7a Pine Logs
Parses all log files, computes MFE/MAE from IB 5m data, writes report.
"""

import os, re, csv, glob
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
import numpy as np
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
LOG_DIR = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug"
BAR_DIR = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars"
REPORT_PATH = os.path.join(LOG_DIR, "investigation-all-signals.md")

# ── 1. PARSE LOGS ────────────────────────────────────────────

def parse_all_logs():
    """Parse all v3.7a log files, return deduplicated DataFrame."""
    files = glob.glob(os.path.join(LOG_DIR, "pine-logs-Key Level Breakout v3.7a_*.csv"))
    print(f"Found {len(files)} log files")

    rows = []
    seen = set()

    for fpath in files:
        with open(fpath, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                date_str = row.get("Date", "").strip()
                msg = row.get("Message", "").strip()
                if not date_str or not msg:
                    continue
                sym_m = re.match(r'\[KLB:(\w+)\]', msg)
                if not sym_m:
                    continue
                symbol = sym_m.group(1)
                key = (symbol, date_str, msg)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    ts = datetime.fromisoformat(date_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=ET)
                    ts_et = ts.astimezone(ET)
                except Exception:
                    continue
                rows.append({"symbol": symbol, "ts_et": ts_et,
                             "date": ts_et.date(), "time_str": ts_et.strftime("%H:%M"),
                             "msg": msg})

    df = pd.DataFrame(rows)
    print(f"Unique entries: {len(df)} across {df['symbol'].nunique()} symbols")
    return df


def classify_signals(df):
    """Extract tradeable signals and 5m checks from log entries."""
    signals, checks = [], []

    for _, r in df.iterrows():
        msg = r["msg"]
        sym = r["symbol"]
        ts = r["ts_et"]

        direction = "bull" if "▲" in msg else ("bear" if "▼" in msg else None)

        # ── 5m CHECK ──
        if "5m CHECK" in msg:
            pnl_m = re.search(r'pnl=([+-]?[\d.]+)', msg)
            bail_m = re.search(r'→ (BAIL|HOLD)', msg)
            spy_m = re.search(r'SPY([~✗✓])', msg)
            checks.append({
                "symbol": sym, "ts_et": ts, "date": r["date"], "time_str": r["time_str"],
                "direction": direction,
                "pnl": float(pnl_m.group(1)) if pnl_m else None,
                "action": bail_m.group(1) if bail_m else None,
                "spy_align": spy_m.group(1) if spy_m else None,
            })
            continue

        # ── Skip CONF-only entries (not signal fires) ──
        if msg.lstrip(r'[KLB:\w\]').strip().startswith("CONF"):
            continue
        if " CONF " in msg and "BRK" not in msg and "QBS" not in msg and "RNG" not in msg and "FADE" not in msg:
            continue

        # ── BRK / REV (~) / RECLAIM (~~) signal ──
        brk_m = re.search(r'\b(BRK|REV)\b', msg)
        rev_m = re.search(r'[▲▼] (~~?) (.+?) vol=', msg)  # e.g. "▲ ~ Yest L vol=" or "▲ ~~ Yest L vol="
        if (brk_m or rev_m) and "5m CHECK" not in msg and "CONF" not in msg:
            if rev_m:
                sig_type = "RECLAIM" if rev_m.group(1) == "~~" else "REV"
                level_info = rev_m.group(2).strip()
            else:
                sig_type = brk_m.group(1)
                level_m = re.search(r'(?:BRK|REV)\s+(.+?)\s+vol=', msg)
                level_info = level_m.group(1).strip() if level_m else ""
            # Extract context fields
            ctx = extract_context(msg)
            signals.append({
                "symbol": sym, "ts_et": ts, "date": r["date"], "time_str": r["time_str"],
                "sig_type": sig_type, "direction": direction,
                "level_info": level_info, **ctx, "msg": msg,
            })
            continue

        # ── RNG ──
        if "RNG range break" in msg:
            vol_m = re.search(r'vol=([\d.]+)x', msg)
            signals.append({
                "symbol": sym, "ts_et": ts, "date": r["date"], "time_str": r["time_str"],
                "sig_type": "RNG", "direction": direction,
                "level_info": "", "vol": float(vol_m.group(1)) if vol_m else None,
                "vwap": None, "ema": None, "adx": None, "atr_log": None,
                "body_pct": None, "rangeATR": None,
                "msg": msg,
            })
            continue

        # ── FADE ──
        if "FADE at" in msg:
            price_m = re.search(r'FADE at ([\d.]+)', msg)
            signals.append({
                "symbol": sym, "ts_et": ts, "date": r["date"], "time_str": r["time_str"],
                "sig_type": "FADE", "direction": direction,
                "level_info": price_m.group(1) if price_m else "",
                "vol": None, "vwap": None, "ema": None, "adx": None, "atr_log": None,
                "body_pct": None, "rangeATR": None,
                "msg": msg,
            })
            continue

        # ── QBS ──
        if " QBS" in msg and "5m CHECK" not in msg:
            ctx = extract_context(msg)
            signals.append({
                "symbol": sym, "ts_et": ts, "date": r["date"], "time_str": r["time_str"],
                "sig_type": "QBS", "direction": direction,
                "level_info": "", **ctx, "msg": msg,
            })
            continue

    sigs_df = pd.DataFrame(signals)
    chks_df = pd.DataFrame(checks)
    print(f"Signals: {len(sigs_df)} | 5m checks: {len(chks_df)}")
    if len(sigs_df) > 0:
        print("By type:", sigs_df["sig_type"].value_counts().to_dict())
        print("By symbol:", sigs_df["symbol"].value_counts().to_dict())
    return sigs_df, chks_df


def extract_context(msg):
    """Extract vol, vwap, ema, adx, ATR, body, rangeATR from a log message."""
    def g(pattern, cast=str, default=None):
        m = re.search(pattern, msg)
        if m:
            try:
                return cast(m.group(1))
            except Exception:
                return default
        return default

    return {
        "vol": g(r'vol=([\d.]+)x', float),
        "vwap": g(r'vwap=(\w+)', str),
        "ema": g(r'ema=(\w+)', str),
        "adx": g(r'adx=(\d+)', int),
        "atr_log": g(r'ATR=([\d.]+)', float),
        "body_pct": g(r'body=(\d+)%', int),
        "rangeATR": g(r'rangeATR=([\d.]+)', float),
    }


# ── 2. LOAD IB 5m BARS ───────────────────────────────────────

def load_bars(symbol):
    """Load IB 5m bars, return DataFrame indexed by ET timestamps."""
    fname = f"{symbol.lower()}_5_mins_ib.parquet"
    fpath = os.path.join(BAR_DIR, fname)
    if not os.path.exists(fpath):
        return None
    df = pd.read_parquet(fpath)
    # date column is the datetime (Berlin tz = same UTC offset as ET during trading)
    df = df.set_index("date")
    df.index = df.index.tz_convert(ET)
    df = df.between_time("09:30", "16:00")
    df = df.rename(columns={"open": "open", "high": "high", "low": "low", "close": "close"})
    return df


def build_atr_lookup(bars_df, lookback=14):
    """Precompute daily ATR for every trading date. Returns dict {date: atr}."""
    by_day = bars_df.groupby(bars_df.index.date)
    daily_ranges = {d: grp["high"].max() - grp["low"].min() for d, grp in by_day}
    sorted_dates = sorted(daily_ranges.keys())
    atr_lookup = {}
    for i, d in enumerate(sorted_dates):
        past = sorted_dates[max(0, i - lookback):i]
        if past:
            atr_lookup[d] = float(np.mean([daily_ranges[p] for p in past]))
        else:
            atr_lookup[d] = None
    return atr_lookup


def daily_atr(bars_df, date, lookback=14):
    """Daily ATR = mean daily range over trailing 14 trading days."""
    by_day = bars_df.groupby(bars_df.index.date)
    past_days = sorted(d for d in by_day.groups if d <= date)[-lookback:]
    if not past_days:
        return None
    ranges = [by_day.get_group(d)["high"].max() - by_day.get_group(d)["low"].min()
              for d in past_days]
    return float(np.mean(ranges))


# ── 3. COMPUTE OUTCOMES ──────────────────────────────────────

def compute_outcome(sig, bars_df, atr, day_bars_cache):
    """
    Find entry bar (signal time), look 20 bars forward.
    Returns: entry_price, mfe_atr, mae_atr, win, bars_to_mfe
    Win = reached 0.3 ATR favorable before 0.15 ATR adverse.
    day_bars_cache: dict {date: day_bars_df} precomputed for speed.
    """
    if atr is None or atr <= 0:
        return None

    ts = sig["ts_et"]
    direction = sig["direction"]
    if direction not in ("bull", "bear"):
        return None

    # Round to nearest 5m bar
    bar_min = (ts.minute // 5) * 5
    bar_ts = ts.replace(minute=bar_min, second=0, microsecond=0)

    sig_date = ts.date()
    day_bars = day_bars_cache.get(sig_date)
    if day_bars is None or len(day_bars) == 0:
        return None

    # Find entry bar: accept ±5 min tolerance within this day
    idx = day_bars.index
    window = idx[(idx >= bar_ts - timedelta(minutes=5)) & (idx <= bar_ts + timedelta(minutes=10))]
    if len(window) == 0:
        return None
    entry_ts = window[0]

    future = day_bars.loc[day_bars.index >= entry_ts].head(21)  # entry + 20 bars

    if len(future) < 2:
        return None

    entry_price = future.iloc[0]["close"]
    # Use numpy arrays for speed
    highs = future["high"].values[1:]
    lows = future["low"].values[1:]

    if direction == "bull":
        favs = highs - entry_price
        advs = entry_price - lows
    else:
        favs = entry_price - lows
        advs = highs - entry_price

    mfe = float(favs.max()) if len(favs) > 0 else 0.0
    mae = float(advs.max()) if len(advs) > 0 else 0.0
    bars_to_mfe = int(np.argmax(favs)) + 1 if len(favs) > 0 else 0

    # Win: 0.3 ATR favorable BEFORE 0.15 ATR adverse (check bar by bar)
    win = False
    running_mae = 0.0
    for i in range(len(favs)):
        if advs[i] > running_mae:
            running_mae = advs[i]
        if favs[i] >= 0.3 * atr and running_mae < 0.15 * atr:
            win = True
            break

    return {
        "entry_price": round(entry_price, 4),
        "mfe_atr": round(mfe / atr, 3),
        "mae_atr": round(mae / atr, 3),
        "win": win,
        "bars_to_mfe": bars_to_mfe,
        "atr": round(atr, 4),
    }


# ── 4. LINK CHECKS TO SIGNALS ────────────────────────────────

def link_checks(sigs_df, chks_df):
    """For each signal, find the 5m CHECK within 5-20 min after entry."""
    if len(chks_df) == 0:
        sigs_df = sigs_df.copy()
        sigs_df["bail_action"] = None
        sigs_df["pnl_at_check"] = None
        return sigs_df

    # Build per-symbol sorted checks list for efficient lookup
    chks_by_sym = {}
    for sym, grp in chks_df.groupby("symbol"):
        chks_by_sym[sym] = grp.sort_values("ts_et").reset_index(drop=True)

    bail_actions = []
    pnl_at_check = []

    for _, sig in sigs_df.iterrows():
        sym = sig["symbol"]
        ts = sig["ts_et"]
        sym_chks = chks_by_sym.get(sym)
        if sym_chks is None:
            bail_actions.append(None)
            pnl_at_check.append(None)
            continue
        win_start = ts + timedelta(minutes=3)
        win_end = ts + timedelta(minutes=20)
        mask = (sym_chks["ts_et"] >= win_start) & (sym_chks["ts_et"] <= win_end)
        matches = sym_chks[mask]
        if len(matches) > 0:
            c = matches.iloc[0]
            bail_actions.append(c["action"])
            pnl_at_check.append(c["pnl"])
        else:
            bail_actions.append(None)
            pnl_at_check.append(None)

    sigs_df = sigs_df.copy()
    sigs_df["bail_action"] = bail_actions
    sigs_df["pnl_at_check"] = pnl_at_check
    return sigs_df


# ── 5. HELPERS ───────────────────────────────────────────────

def tod(time_str):
    h, m = map(int, time_str.split(":"))
    t = h * 60 + m
    if t <= 10 * 60 + 30:
        return "morning"
    elif t <= 13 * 60:
        return "midday"
    else:
        return "afternoon"


def perf_table(df, col):
    rows = []
    for val, g in df.groupby(col):
        n = len(g)
        w = g["win"].sum()
        rows.append({
            col: val,
            "N": n,
            "Win%": round(100 * w / n, 1) if n else 0,
            "AvgMFE": round(g["mfe_atr"].mean(), 3),
            "AvgMAE": round(g["mae_atr"].mean(), 3),
            "MFE/MAE": round(g["mfe_atr"].mean() / g["mae_atr"].mean(), 2) if g["mae_atr"].mean() > 0 else np.nan,
        })
    return pd.DataFrame(rows).set_index(col)


# ── 6. WRITE REPORT ──────────────────────────────────────────

def write_report(sigs_df, chks_df, with_out):
    lines = []
    a = lines.append

    total_sigs = len(sigs_df)
    total_out = len(with_out)
    date_min = sigs_df["date"].min()
    date_max = sigs_df["date"].max()
    syms = sorted(sigs_df["symbol"].unique())
    overall_win = 100 * with_out["win"].mean() if total_out else 0

    bailed = with_out[with_out["bail_action"] == "BAIL"]
    held = with_out[with_out["bail_action"] == "HOLD"]
    no_check = with_out[with_out["bail_action"].isna()]

    # Tables
    tbl_type = perf_table(with_out, "sig_type")
    tbl_sym = perf_table(with_out, "symbol")
    with_out = with_out.copy()
    with_out["tod"] = with_out["time_str"].apply(tod)
    tbl_tod = perf_table(with_out, "tod").reindex(["morning", "midday", "afternoon"])
    tbl_dir = perf_table(with_out, "direction")

    fails = with_out[with_out["win"] == False]
    wins = with_out[with_out["win"] == True]

    a("# KLB Signal Investigation — All Signals\n")
    a(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} ET*\n")

    a("## 1. Coverage Summary\n")
    a(f"| Field | Value |")
    a(f"|-------|-------|")
    a(f"| Date range | {date_min} – {date_max} |")
    a(f"| Symbols | {', '.join(syms)} |")
    a(f"| Total signal entries | {total_sigs} |")
    a(f"| Signals with IB outcome | {total_out} |")
    a(f"| Overall win rate | {overall_win:.1f}% |")
    a(f"| 5m CHECK entries | {len(chks_df)} |")
    a(f"| BAIL triggered | {len(bailed)} |")
    a(f"| HOLD triggered | {len(held)} |")
    a("")

    a("## 2. Performance by Signal Type\n")
    a(tbl_type.to_markdown())
    a("")

    a("## 3. Performance by Symbol\n")
    a(tbl_sym.sort_values("Win%", ascending=False).to_markdown())
    a("")

    a("## 4. Performance by Time of Day\n")
    a(tbl_tod.to_markdown())
    a("")

    a("## 5. Performance by Direction\n")
    a(tbl_dir.to_markdown())
    a("")

    a("## 6. BAIL vs HOLD Analysis\n")
    if len(bailed) > 0 and len(held) > 0:
        a("| Outcome | N | Win% | AvgMFE | AvgMAE |")
        a("|---------|---|------|--------|--------|")
        a(f"| BAIL | {len(bailed)} | {100*bailed['win'].mean():.1f}% | {bailed['mfe_atr'].mean():.3f} | {bailed['mae_atr'].mean():.3f} |")
        a(f"| HOLD | {len(held)} | {100*held['win'].mean():.1f}% | {held['mfe_atr'].mean():.3f} | {held['mae_atr'].mean():.3f} |")
        a(f"| No check | {len(no_check)} | {100*no_check['win'].mean():.1f}% | {no_check['mfe_atr'].mean():.3f} | {no_check['mae_atr'].mean():.3f} |")
        a("")
        bail_mfe = bailed["mfe_atr"].mean()
        hold_mfe = held["mfe_atr"].mean()
        if bail_mfe > hold_mfe:
            a("**Note:** BAIL signals had higher MFE than HOLD — BAIL fires on moves that then continue (false bail).")
        else:
            a("**Note:** HOLD signals had higher MFE — BAIL correctly screens out weak entries.")
    else:
        a("Insufficient BAIL/HOLD data.")
    a("")

    a("## 7. Top 10 Best Signals (Highest MFE)\n")
    top10 = with_out.nlargest(10, "mfe_atr")[
        ["symbol","date","time_str","sig_type","direction","level_info","mfe_atr","mae_atr","win","bail_action","atr_log"]]
    a(top10.to_markdown(index=False))
    a("")

    a("## 8. Top 10 Worst Signals (Non-Winners, Highest MAE)\n")
    worst10 = fails.nlargest(10, "mae_atr")[
        ["symbol","date","time_str","sig_type","direction","level_info","mfe_atr","mae_atr","bail_action","ema","vwap","adx"]]
    a(worst10.to_markdown(index=False))
    a("")

    a("## 9. Failure Pattern Analysis\n")
    a(f"Total non-winners: {len(fails)} / {total_out}\n")

    a("### By Symbol")
    a(fails.groupby("symbol").size().sort_values(ascending=False).to_markdown())
    a("")

    a("### By Time of Day")
    fail_tod = fails.groupby("tod").size()
    a(fail_tod.to_markdown())
    a("")

    a("### By Signal Type")
    a(fails.groupby("sig_type").size().sort_values(ascending=False).to_markdown())
    a("")

    a("### EMA Context in Failures (where available)")
    ema_vals = fails["ema"].dropna().value_counts()
    if len(ema_vals):
        a(ema_vals.to_markdown())
    a("")

    a("### VWAP Context in Failures (where available)")
    vwap_vals = fails["vwap"].dropna().value_counts()
    if len(vwap_vals):
        a(vwap_vals.to_markdown())
    a("")

    a("### BAIL Regret: Signals that BAILed but MFE > 0.5 ATR\n")
    if len(bailed) > 0:
        regret = bailed[bailed["mfe_atr"] > 0.5].sort_values("mfe_atr", ascending=False)
        if len(regret) > 0:
            a(regret[["symbol","date","time_str","sig_type","direction","level_info","mfe_atr","mae_atr","pnl_at_check"]].head(10).to_markdown(index=False))
        else:
            a("None found — no BAILed signals with MFE > 0.5 ATR.")
    a("")

    a("## 10. Signal Distribution (Symbol × Type)\n")
    pivot = sigs_df.groupby(["symbol","sig_type"]).size().unstack(fill_value=0)
    a(pivot.to_markdown())
    a("")

    a("## 11. Date Coverage by Symbol\n")
    cov = sigs_df.groupby("symbol")["date"].agg(["min","max","count"]).rename(
        columns={"min":"First","max":"Last","count":"N_signals"})
    a(cov.to_markdown())
    a("")

    a("## 12. QBS Context Deep Dive\n")
    qbs = with_out[with_out["sig_type"] == "QBS"]
    if len(qbs) > 0:
        a(f"QBS signals with outcome: {len(qbs)}, Win%: {100*qbs['win'].mean():.1f}%\n")
        a("**QBS by EMA:**")
        if "ema" in qbs.columns:
            a(qbs.groupby("ema")[["win","mfe_atr","mae_atr"]].agg({"win": "mean", "mfe_atr": "mean", "mae_atr": "mean"}).round(3).to_markdown())
        a("")
        a("**QBS by VWAP:**")
        if "vwap" in qbs.columns:
            a(qbs.groupby("vwap")[["win","mfe_atr","mae_atr"]].agg({"win": "mean", "mfe_atr": "mean", "mae_atr": "mean"}).round(3).to_markdown())
    a("")

    a("## 13. SPY Context in 5m CHECKS\n")
    if "spy_align" in chks_df.columns:
        bail_chks = chks_df[chks_df["action"] == "BAIL"]
        hold_chks = chks_df[chks_df["action"] == "HOLD"]
        a("SPY alignment at BAIL:")
        a(bail_chks["spy_align"].value_counts().to_markdown())
        a("")
        a("SPY alignment at HOLD:")
        a(hold_chks["spy_align"].value_counts().to_markdown())
    a("")

    a("## 14. Key Findings\n")
    if len(tbl_type) > 0:
        best_type = tbl_type["Win%"].idxmax()
        worst_type = tbl_type["Win%"].idxmin()
        best_tod = tbl_tod["Win%"].idxmax() if not tbl_tod["Win%"].isna().all() else "N/A"
        worst_tod = tbl_tod["Win%"].idxmin() if not tbl_tod["Win%"].isna().all() else "N/A"
        best_sym = tbl_sym["Win%"].idxmax()
        worst_sym = tbl_sym["Win%"].idxmin()

        a(f"1. **Best signal type:** {best_type} — {tbl_type.loc[best_type,'Win%']}% win, MFE/MAE={tbl_type.loc[best_type,'MFE/MAE']:.2f}x")
        a(f"2. **Worst signal type:** {worst_type} — {tbl_type.loc[worst_type,'Win%']}% win")
        a(f"3. **Best time slot:** {best_tod} — {tbl_tod.loc[best_tod,'Win%']}% win")
        a(f"4. **Worst time slot:** {worst_tod} — {tbl_tod.loc[worst_tod,'Win%']}% win")
        a(f"5. **Best symbol:** {best_sym} — {tbl_sym.loc[best_sym,'Win%']}% win (N={tbl_sym.loc[best_sym,'N']})")
        a(f"6. **Worst symbol:** {worst_sym} — {tbl_sym.loc[worst_sym,'Win%']}% win (N={tbl_sym.loc[worst_sym,'N']})")
        a(f"7. **Overall win rate:** {overall_win:.1f}% across {total_out} signals")

    a("")
    a("### Action Items\n")
    a("- [ ] Investigate worst signal type for suppression or filter tightening")
    a("- [ ] Investigate afternoon performance — consider time gate")
    a("- [ ] Review BAIL regret cases — if frequent, consider loosening BAIL threshold")
    a("- [ ] Check EMA/VWAP conflict pattern in failures for a new filter")
    a("- [ ] Symbol-specific: review worst performer for structural issues")
    a("")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nReport written: {REPORT_PATH}")


# ── TEMPORAL ANALYSIS ────────────────────────────────────────

def write_temporal_report(df):
    """Slice win% by month, quarter, and trailing period windows."""
    import numpy as np
    lines = []
    a = lines.append
    REPORT = os.path.join(LOG_DIR, "investigation-temporal.md")

    df = df.copy()
    df["date_dt"] = pd.to_datetime(df["date"])
    df["month"]   = df["date_dt"].dt.to_period("M").astype(str)
    df["quarter"] = df["date_dt"].dt.to_period("Q").astype(str)

    latest = df["date_dt"].max()

    a("# KLB Signal Investigation — Temporal Analysis\n")
    a(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d')}  |  "
      f"Date range: {df['date_dt'].min().date()} – {latest.date()}  |  "
      f"N={len(df)} signals with outcomes\n")

    # ── MONTHLY ────────────────────────────────────────────────
    a("## 1. Monthly Performance\n")
    tbl = perf_table(df, "month")
    a(tbl.to_markdown())
    a("")

    # trend indicator: last 3 months vs prior 3
    months = sorted(df["month"].unique())
    if len(months) >= 6:
        recent3 = df[df["month"].isin(months[-3:])]
        prior3  = df[df["month"].isin(months[-6:-3])]
        r3w = 100 * recent3["win"].mean()
        p3w = 100 * prior3["win"].mean()
        a(f"**Trend:** Last 3 months ({months[-3]}–{months[-1]}): **{r3w:.1f}%** win  |  "
          f"Prior 3 ({months[-6]}–{months[-4]}): **{p3w:.1f}%** win  |  "
          f"Delta: **{r3w-p3w:+.1f}pp**\n")

    # ── QUARTERLY ──────────────────────────────────────────────
    a("## 2. Quarterly Performance\n")
    tbl_q = perf_table(df, "quarter")
    a(tbl_q.to_markdown())
    a("")

    # ── TRAILING WINDOWS ───────────────────────────────────────
    a("## 3. Trailing Window Comparison\n")
    windows = [30, 90, 180, 365]
    rows = []
    for days in windows:
        cutoff = latest - pd.Timedelta(days=days)
        sub = df[df["date_dt"] >= cutoff]
        if len(sub) == 0:
            continue
        rows.append({
            "Window": f"Last {days}d",
            "From": cutoff.date(),
            "N": len(sub),
            "Win%": round(100 * sub["win"].mean(), 1),
            "AvgMFE": round(sub["mfe_atr"].mean(), 3),
            "AvgMAE": round(sub["mae_atr"].mean(), 3),
            "MFE/MAE": round(sub["mfe_atr"].mean() / sub["mae_atr"].mean(), 2),
        })
    # full history
    rows.append({
        "Window": "All-time",
        "From": df["date_dt"].min().date(),
        "N": len(df),
        "Win%": round(100 * df["win"].mean(), 1),
        "AvgMFE": round(df["mfe_atr"].mean(), 3),
        "AvgMAE": round(df["mae_atr"].mean(), 3),
        "MFE/MAE": round(df["mfe_atr"].mean() / df["mae_atr"].mean(), 2),
    })
    a(pd.DataFrame(rows).set_index("Window").to_markdown())
    a("")

    # ── TRAILING 90d vs ALL-TIME — BY SIGNAL TYPE ──────────────
    a("## 4. Last 90d vs All-time — by Signal Type\n")
    cut90 = latest - pd.Timedelta(days=90)
    last90 = df[df["date_dt"] >= cut90]
    rows = []
    for stype in sorted(df["sig_type"].unique()):
        all_s  = df[df["sig_type"] == stype]
        l90_s  = last90[last90["sig_type"] == stype]
        if len(all_s) == 0:
            continue
        rows.append({
            "Type": stype,
            "Win%(all)": round(100 * all_s["win"].mean(), 1),
            "Win%(90d)": round(100 * l90_s["win"].mean(), 1) if len(l90_s) else "—",
            "N(all)": len(all_s),
            "N(90d)": len(l90_s),
            "Delta": round((100 * l90_s["win"].mean()) - (100 * all_s["win"].mean()), 1) if len(l90_s) else "—",
        })
    a(pd.DataFrame(rows).set_index("Type").to_markdown())
    a("")

    # ── LAST 90d — BY SYMBOL ───────────────────────────────────
    a("## 5. Last 90d — by Symbol\n")
    a(perf_table(last90, "symbol").sort_values("Win%", ascending=False).to_markdown())
    a("")

    # ── LAST 90d — BY TIME-OF-DAY ──────────────────────────────
    a("## 6. Last 90d — by Time of Day\n")
    last90c = last90.copy()
    last90c["tod"] = last90c["time_str"].apply(tod)
    a(perf_table(last90c, "tod").reindex(["morning","midday","afternoon"]).to_markdown())
    a("")

    # ── LAST 90d vs ALL — BY SYMBOL (delta table) ──────────────
    a("## 7. Symbol Trend: Last 90d vs All-time Win%\n")
    rows = []
    for sym in sorted(df["symbol"].unique()):
        all_s = df[df["symbol"] == sym]
        l90_s = last90[last90["symbol"] == sym]
        if len(all_s) < 10:
            continue
        w_all = round(100 * all_s["win"].mean(), 1)
        w_90  = round(100 * l90_s["win"].mean(), 1) if len(l90_s) >= 5 else None
        delta = round(w_90 - w_all, 1) if w_90 is not None else None
        trend = ("▲ improving" if delta and delta > 2 else
                 "▼ declining" if delta and delta < -2 else
                 "→ stable") if delta is not None else "—"
        rows.append({
            "Symbol": sym, "Win%(all)": w_all, "Win%(90d)": w_90 or "—",
            "Delta": delta or "—", "Trend": trend, "N(90d)": len(l90_s),
        })
    a(pd.DataFrame(rows).set_index("Symbol").to_markdown())
    a("")

    # ── MONTHLY BREAKDOWN BY SIGNAL TYPE (heatmap-style) ───────
    a("## 8. Monthly Win% by Signal Type\n")
    pivot = df.groupby(["month","sig_type"])["win"].mean().mul(100).unstack().round(1)
    a(pivot.to_markdown())
    a("")

    # ── BREAKPOINTS: FIND STRUCTURAL CHANGES ───────────────────
    a("## 9. Rolling 30-day Win% (breakpoint detection)\n")
    df_sorted = df.sort_values("date_dt")
    df_sorted["roll_win"] = df_sorted["win"].rolling(200, min_periods=50).mean().mul(100).round(1)
    # Sample at month-end dates
    monthly_snap = df_sorted.groupby("month")["roll_win"].last()
    for m, v in monthly_snap.items():
        bar = "█" * int(v / 2) if not np.isnan(v) else ""
        a(f"  {m}: {v:.1f}% {bar}")
    a("")

    a("## 10. Key Observations\n")
    # find best/worst months
    if len(tbl) > 0:
        best_m = tbl["Win%"].idxmax()
        worst_m = tbl["Win%"].idxmin()
        a(f"- Best month: **{best_m}** ({tbl.loc[best_m,'Win%']}% win, N={tbl.loc[best_m,'N']})")
        a(f"- Worst month: **{worst_m}** ({tbl.loc[worst_m,'Win%']}% win, N={tbl.loc[worst_m,'N']})")
    if len(tbl_q) > 0:
        best_q = tbl_q["Win%"].idxmax()
        worst_q = tbl_q["Win%"].idxmin()
        a(f"- Best quarter: **{best_q}** ({tbl_q.loc[best_q,'Win%']}%)")
        a(f"- Worst quarter: **{worst_q}** ({tbl_q.loc[worst_q,'Win%']}%)")
    if len(rows) > 0:
        df_rows = pd.DataFrame(rows)
        improving = df_rows[df_rows["Trend"] == "▲ improving"]["Symbol"].tolist()
        declining = df_rows[df_rows["Trend"] == "▼ declining"]["Symbol"].tolist()
        if improving:
            a(f"- Improving symbols (last 90d): {', '.join(improving)}")
        if declining:
            a(f"- Declining symbols (last 90d): {', '.join(declining)}")
    a("")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Temporal report: {REPORT}")


# ── MAIN ─────────────────────────────────────────────────────

def main():
    print("=== KLB Signal Investigation ===\n")

    # Parse
    df_all = parse_all_logs()
    sigs_df, chks_df = classify_signals(df_all)

    if len(sigs_df) == 0:
        print("ERROR: No signals parsed!")
        return

    # Load bars and precompute lookups
    print("\nLoading IB 5m bars...")
    bars_cache = {}
    atr_lookup_cache = {}   # sym -> {date: atr}
    day_bars_cache = {}     # sym -> {date: day_df}

    for sym in sorted(sigs_df["symbol"].unique()):
        b = load_bars(sym)
        if b is not None:
            bars_cache[sym] = b
            print(f"  {sym}: {len(b)} bars ({b.index[0].date()} – {b.index[-1].date()})")
            # Precompute ATR lookup (one pass)
            atr_lookup_cache[sym] = build_atr_lookup(b)
            # Precompute day bars dict
            by_day = b.groupby(b.index.date)
            day_bars_cache[sym] = {d: grp for d, grp in by_day}
        else:
            print(f"  {sym}: NOT FOUND")

    # Link bail/hold
    sigs_df = link_checks(sigs_df, chks_df)

    # Compute outcomes
    print("\nComputing outcomes...")
    outcome_records = []
    for _, sig in sigs_df.iterrows():
        sym = sig["symbol"]
        if sym not in bars_cache:
            outcome_records.append(None)
            continue
        atr = atr_lookup_cache[sym].get(sig["date"])
        out = compute_outcome(sig, bars_cache[sym], atr, day_bars_cache[sym])
        outcome_records.append(out)

    # Merge outcomes into df
    sigs_df = sigs_df.copy()
    sigs_df["mfe_atr"] = [o["mfe_atr"] if o else np.nan for o in outcome_records]
    sigs_df["mae_atr"] = [o["mae_atr"] if o else np.nan for o in outcome_records]
    sigs_df["win"] = [o["win"] if o else np.nan for o in outcome_records]
    sigs_df["atr"] = [o["atr"] if o else np.nan for o in outcome_records]

    with_out = sigs_df.dropna(subset=["mfe_atr", "win"]).copy()
    print(f"\nSignals with outcomes: {len(with_out)} / {len(sigs_df)}")

    # Summary
    print(f"\nOverall win%: {100*with_out['win'].mean():.1f}%")
    print("By type:\n", perf_table(with_out, "sig_type"))
    print("\nBy symbol:\n", perf_table(with_out, "symbol").sort_values("Win%", ascending=False))

    with_out["tod"] = with_out["time_str"].apply(tod)
    print("\nBy tod:\n", perf_table(with_out, "tod").reindex(["morning","midday","afternoon"]))

    # Save cache for fast re-analysis
    cache_path = os.path.join(LOG_DIR, "signals_cache.parquet")
    with_out.to_parquet(cache_path, index=False)
    print(f"\nCache saved: {cache_path}")

    # Write report (full)
    write_report(sigs_df, chks_df, with_out)

    # ── TEMPORAL ANALYSIS ────────────────────────────────────────
    write_temporal_report(with_out)


if __name__ == "__main__":
    main()
