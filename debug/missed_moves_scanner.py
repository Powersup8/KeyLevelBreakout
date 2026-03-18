"""
Missed Moves Scanner — Scans ALL candle data for significant moves,
cross-references with signals fired, identifies MISSED moves and their fingerprint.

Uses a peak-trough detection approach with ATR-based filtering.
Outputs report to missed-moves-report.md.
"""

import pandas as pd
import numpy as np
import re
import warnings
from datetime import datetime, time as dtime
from pathlib import Path

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Paths & Config
# ---------------------------------------------------------------------------
BASE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView")
ARCHIVE = BASE / "debug" / "archive"
SIGNALS_PATH = BASE / "debug" / "enriched-signals.csv"
REPORT_PATH = BASE / "debug" / "missed-moves-report.md"

MARKET_OPEN = dtime(9, 30)
MARKET_CLOSE = dtime(16, 0)

# Move detection thresholds
MIN_ATR_MAG = 0.50     # minimum move magnitude (ATR)
MIN_BARS = 3           # minimum 5m bars for a move (15+ min)
REVERSAL_ATR = 0.75    # how much pullback triggers a new direction (ATR) - higher than MIN to avoid whipsaw


# ===========================================================================
# Step 1: Load 1m candle data
# ===========================================================================
def load_candle_data():
    all_frames = []
    csv_files = list(ARCHIVE.glob("BATS_*.csv"))
    print(f"Found {len(csv_files)} CSV files")

    for fpath in csv_files:
        m = re.match(r"BATS_([A-Z]+),", fpath.name)
        if not m:
            continue
        symbol = m.group(1)
        try:
            df = pd.read_csv(fpath)
        except Exception:
            continue

        df = df.rename(columns={df.columns[0]: "time", df.columns[1]: "open",
                                df.columns[2]: "high", df.columns[3]: "low",
                                df.columns[4]: "close"})
        vol_col = next((c for c in df.columns if c == "Volume"), None)
        if vol_col is None:
            vol_col = next((c for c in df.columns if "volume" in c.lower() and "ma" not in c.lower()), None)
        if vol_col is None:
            continue
        df = df.rename(columns={vol_col: "volume"})
        df["time"] = pd.to_datetime(df["time"], utc=True).dt.tz_convert("US/Eastern")
        df["symbol"] = symbol
        df["date"] = df["time"].dt.date
        t = df["time"].dt.time
        df = df[(t >= MARKET_OPEN) & (t <= MARKET_CLOSE)]
        all_frames.append(df[["symbol", "date", "time", "open", "high", "low", "close", "volume"]])

    candles = pd.concat(all_frames, ignore_index=True)
    candles = candles.drop_duplicates(subset=["symbol", "time"], keep="first")
    candles = candles.sort_values(["symbol", "time"]).reset_index(drop=True)

    print(f"Loaded {len(candles):,} 1m rows, {candles['symbol'].nunique()} symbols, "
          f"{candles['date'].min()} to {candles['date'].max()}")
    for s in sorted(candles["symbol"].unique()):
        sub = candles[candles["symbol"] == s]
        print(f"  {s}: {len(sub):,} rows, {sub['date'].nunique()} days")
    return candles


# ===========================================================================
# Step 2: Resample to 5m + indicators
# ===========================================================================
def resample_5m(candles_1m):
    results = []
    for (symbol, date), grp in candles_1m.groupby(["symbol", "date"]):
        grp = grp.sort_values("time").set_index("time")
        if len(grp) < 5:
            continue

        bars = grp.resample("5min").agg({
            "open": "first", "high": "max", "low": "min",
            "close": "last", "volume": "sum",
            "symbol": "first", "date": "first"
        }).dropna(subset=["open"])

        if len(bars) < 5:
            continue

        # ATR(14) with fillna for first bar
        bars["prev_close"] = bars["close"].shift(1)
        bars["tr"] = np.maximum(
            bars["high"] - bars["low"],
            np.maximum(
                (bars["high"] - bars["prev_close"]).abs(),
                (bars["low"] - bars["prev_close"]).abs()
            ))
        bars["tr"] = bars["tr"].fillna(bars["high"] - bars["low"])  # first bar
        bars["atr14"] = bars["tr"].rolling(14, min_periods=1).mean()

        # EMA(20)
        bars["ema20"] = bars["close"].ewm(span=20, adjust=False).mean()

        # VWAP
        bars["cum_vol"] = bars["volume"].cumsum()
        typical = (bars["high"] + bars["low"] + bars["close"]) / 3
        bars["cum_vp"] = (typical * bars["volume"]).cumsum()
        bars["vwap"] = bars["cum_vp"] / bars["cum_vol"].replace(0, np.nan)

        # Volume SMA(20)
        bars["vol_sma20"] = bars["volume"].rolling(20, min_periods=1).mean()

        bars = bars.reset_index()
        results.append(bars)

    bars_5m = pd.concat(results, ignore_index=True)
    print(f"Resampled to {len(bars_5m):,} 5m bars")
    return bars_5m


# ===========================================================================
# Step 3: Detect significant moves — improved zig-zag
# ===========================================================================
def detect_moves(bars_5m):
    """
    Zig-zag with separate reversal threshold to avoid whipsaw.
    Also emits partial moves at end-of-day.
    """
    all_moves = []

    for (symbol, date), grp in bars_5m.groupby(["symbol", "date"]):
        grp = grp.sort_values("time").reset_index(drop=True)
        n = len(grp)
        if n < 5:
            continue

        H = grp["high"].values
        L = grp["low"].values
        C = grp["close"].values
        T = list(grp["time"])  # preserve tz-aware Timestamps (numpy strips tz)
        ATR = grp["atr14"].values
        EMA = grp["ema20"].values
        VWAP = grp["vwap"].values
        VOL = grp["volume"].values
        VOLSMA = grp["vol_sma20"].values

        def make_move(direction, si, ei):
            """Helper to create a move dict."""
            atr = ATR[si] if ATR[si] > 0 else ATR[min(si + 1, n - 1)]
            if atr <= 0 or np.isnan(atr):
                return None
            if direction == "up":
                mag = (H[ei] - L[si]) / atr
                sp, ep = float(L[si]), float(H[ei])
            else:
                mag = (H[si] - L[ei]) / atr
                sp, ep = float(H[si]), float(L[ei])
            dur = ei - si
            if dur < MIN_BARS or mag < MIN_ATR_MAG:
                return None
            vr = VOL[si] / VOLSMA[si] if VOLSMA[si] > 0 else 0
            return {
                "symbol": symbol, "date": date,
                "start_time": T[si],
                "end_time": T[ei],
                "direction": direction,
                "magnitude_atr": round(mag, 3),
                "duration_bars": dur,
                "start_price": round(sp, 4),
                "end_price": round(ep, 4),
                "atr": round(float(atr), 4),
                "vol_ratio": round(float(vr), 2),
                "ema_pos": "above" if C[si] > EMA[si] else "below",
                "vwap_pos": "above" if C[si] > VWAP[si] else "below",
            }

        # Zig-zag state
        direction = None   # "up" or "down"
        move_si = 0        # move start index
        run_hi = H[0]
        run_hi_idx = 0
        run_lo = L[0]
        run_lo_idx = 0

        # Determine initial direction from first 3 bars
        # If first 3 bars trend up, start up; else down
        if n >= 3:
            first3_hi = max(H[0], H[1], H[2])
            first3_lo = min(L[0], L[1], L[2])
            atr0 = ATR[2] if ATR[2] > 0 else ATR[0]
            if atr0 > 0:
                # Find which extreme comes first
                hi_idx = np.argmax(H[:3])
                lo_idx = np.argmin(L[:3])
                if lo_idx <= hi_idx:
                    # Low comes first or same bar -> start as up
                    direction = "up"
                    move_si = lo_idx
                    run_hi = first3_hi
                    run_hi_idx = hi_idx
                    run_lo = L[lo_idx]
                    run_lo_idx = lo_idx
                else:
                    direction = "down"
                    move_si = hi_idx
                    run_lo = first3_lo
                    run_lo_idx = lo_idx
                    run_hi = H[hi_idx]
                    run_hi_idx = hi_idx

        for i in range(3, n):
            atr = ATR[i] if ATR[i] > 0 and not np.isnan(ATR[i]) else ATR[max(0, i - 1)]
            if atr <= 0 or np.isnan(atr):
                continue

            if direction == "up":
                if H[i] > run_hi:
                    run_hi = H[i]
                    run_hi_idx = i
                # Check for reversal
                pullback = run_hi - L[i]
                if pullback / atr >= REVERSAL_ATR:
                    # Emit up move
                    mv = make_move("up", move_si, run_hi_idx)
                    if mv:
                        all_moves.append(mv)
                    # Switch to down
                    direction = "down"
                    move_si = run_hi_idx
                    run_lo = L[i]
                    run_lo_idx = i
                    run_hi = H[run_hi_idx]

            elif direction == "down":
                if L[i] < run_lo:
                    run_lo = L[i]
                    run_lo_idx = i
                bounce = H[i] - run_lo
                if bounce / atr >= REVERSAL_ATR:
                    mv = make_move("down", move_si, run_lo_idx)
                    if mv:
                        all_moves.append(mv)
                    direction = "up"
                    move_si = run_lo_idx
                    run_hi = H[i]
                    run_hi_idx = i
                    run_lo = L[run_lo_idx]

        # End of day — emit final pending move
        if direction == "up":
            mv = make_move("up", move_si, run_hi_idx)
            if mv:
                all_moves.append(mv)
        elif direction == "down":
            mv = make_move("down", move_si, run_lo_idx)
            if mv:
                all_moves.append(mv)

    moves_df = pd.DataFrame(all_moves)
    if len(moves_df) > 0:
        moves_df = moves_df.sort_values(["symbol", "date", "start_time"]).reset_index(drop=True)
    print(f"Found {len(moves_df):,} significant moves (>={MIN_ATR_MAG} ATR, >={MIN_BARS} bars)")
    if len(moves_df) > 0:
        n_symdays = moves_df.groupby(["symbol", "date"]).ngroups
        print(f"  Avg {len(moves_df) / n_symdays:.1f} moves/symbol-day")
        print(f"  Magnitude: mean={moves_df['magnitude_atr'].mean():.2f}, "
              f"median={moves_df['magnitude_atr'].median():.2f}, "
              f"max={moves_df['magnitude_atr'].max():.2f} ATR")
    return moves_df


# ===========================================================================
# Step 4: Load signals and cross-reference
# ===========================================================================
def load_signals():
    sig = pd.read_csv(SIGNALS_PATH)
    sig["date"] = pd.to_datetime(sig["date"]).dt.date
    sig["time_obj"] = sig["time"].apply(lambda x: datetime.strptime(str(x), "%H:%M").time())
    sig["datetime"] = sig.apply(
        lambda r: pd.Timestamp(datetime.combine(r["date"], r["time_obj"]),
                               tz="US/Eastern"), axis=1)
    print(f"Loaded {len(sig):,} signals ({sig['date'].min()} to {sig['date'].max()})")
    return sig


def _tz(ts):
    ts = pd.Timestamp(ts)
    if ts.tzinfo is None:
        return ts.tz_localize("US/Eastern")
    return ts.tz_convert("US/Eastern")


def cross_reference(moves, signals):
    classifications = []
    sig_infos = []

    # Pre-index signals
    sig_idx = {}
    for (sym, dt), grp in signals.groupby(["symbol", "date"]):
        sig_idx[(sym, dt)] = grp

    for _, move in moves.iterrows():
        sym, dt = move["symbol"], move["date"]
        start = _tz(move["start_time"])
        end = _tz(move["end_time"])
        sig_dir = "bull" if move["direction"] == "up" else "bear"
        opp_dir = "bear" if sig_dir == "bull" else "bull"

        day_sigs = sig_idx.get((sym, dt))
        if day_sigs is None or len(day_sigs) == 0:
            classifications.append("MISSED")
            sig_infos.append({"had_opposite_before": False, "had_conf_fail_before": False,
                              "opposite_count": 0, "conf_fail_count": 0, "no_signals_today": True})
            continue

        dts = day_sigs["datetime"].apply(_tz)

        # Wide match: [-15min before move, first half of move or +15min whichever is larger]
        w_start = start - pd.Timedelta(minutes=15)
        move_dur_min = (end - start).total_seconds() / 60
        w_end_offset = max(15, move_dur_min / 2)
        w_end = start + pd.Timedelta(minutes=w_end_offset)
        if w_end > end:
            w_end = end

        dir_mask = day_sigs["direction"] == sig_dir
        early = day_sigs[(dts >= w_start) & (dts <= w_end) & dir_mask]
        late = day_sigs[(dts > w_end) & (dts <= end) & dir_mask]

        prior = start - pd.Timedelta(minutes=30)
        opp_mask = (dts >= prior) & (dts <= start) & (day_sigs["direction"] == opp_dir)
        cf_mask = (dts >= prior) & (dts <= start) & dir_mask & (day_sigs["conf"] == "\u2717")

        info = {
            "had_opposite_before": bool(opp_mask.sum() > 0),
            "had_conf_fail_before": bool(cf_mask.sum() > 0),
            "opposite_count": int(opp_mask.sum()),
            "conf_fail_count": int(cf_mask.sum()),
            "no_signals_today": False,
        }

        if len(early) > 0:
            conf_pass = early[early["conf"].isin(["\u2713", "\u2713\u2605"])]
            if len(conf_pass) > 0:
                cls = "CAUGHT"
                best = conf_pass.iloc[0]
            else:
                cls = "SIGNAL_FIRED_BUT_FAILED"
                best = early.iloc[0]
            info.update({"sig_time": str(best["time"]), "sig_type": best["type"],
                         "sig_conf": str(best.get("conf", "")),
                         "sig_levels": str(best.get("levels", ""))})
        elif len(late) > 0:
            cls = "LATE_CATCH"
            best = late.iloc[0]
            info.update({"sig_time": str(best["time"]), "sig_type": best["type"],
                         "sig_conf": str(best.get("conf", "")),
                         "sig_levels": str(best.get("levels", ""))})
        else:
            cls = "MISSED"

        classifications.append(cls)
        sig_infos.append(info)

    moves = moves.copy()
    moves["classification"] = classifications
    moves["sig_info"] = sig_infos

    print("\nClassification breakdown:")
    vc = moves["classification"].value_counts()
    for cls in ["CAUGHT", "SIGNAL_FIRED_BUT_FAILED", "LATE_CATCH", "MISSED"]:
        print(f"  {cls}: {vc.get(cls, 0)}")

    no_sig_count = sum(1 for info in sig_infos if info.get("no_signals_today"))
    print(f"  (Moves on days with NO signals for that symbol: {no_sig_count})")
    return moves


# ===========================================================================
# Step 5: Categorize
# ===========================================================================
def categorize(moves):
    cats = []
    for _, row in moves.iterrows():
        if row["classification"] != "MISSED":
            cats.append("")
            continue
        info = row["sig_info"]
        st = pd.Timestamp(row["start_time"])
        h, m = st.hour, st.minute

        if info.get("had_opposite_before"):
            cat = "Failed_Breakout_Fade"
        elif info.get("had_conf_fail_before"):
            cat = "Post_CONF_Failure_Continuation"
        elif h == 9 and m < 45 and row["duration_bars"] >= 4:
            cat = "Gap_and_Pullback"
        elif row["vol_ratio"] < 1.0 and row["duration_bars"] >= 6:
            cat = "Level_Desert_Grind"
        elif row["duration_bars"] >= 10:
            cat = "Level_Desert_Grind"
        else:
            cat = "No_Signal_Zone"
        cats.append(cat)

    moves = moves.copy()
    moves["pattern_category"] = cats
    return moves


def time_bucket(ts):
    ts = pd.Timestamp(ts)
    h, m = ts.hour, ts.minute
    if h == 9 and m < 45:   return "9:30-9:45"
    elif h == 9:             return "9:45-10:00"
    elif h == 10 and m < 30: return "10:00-10:30"
    elif h == 10:            return "10:30-11:00"
    elif h == 11:            return "11:00-12:00"
    elif h < 14:             return "12:00-14:00"
    elif h < 15:             return "14:00-15:00"
    else:                    return "15:00-16:00"


# ===========================================================================
# Step 6: Report
# ===========================================================================
def generate_report(moves, signals, candles_1m):
    lines = []
    L = lines.append

    moves = moves.copy()
    moves["time_bucket"] = moves["start_time"].apply(time_bucket)

    # Compute overlap: symbol-days with both candles AND signals
    candle_keys = set(zip(candles_1m["symbol"], candles_1m["date"]))
    candle_symdays = set()
    for s, d in candle_keys:
        candle_symdays.add((s, d))
    signal_keys = set(zip(signals["symbol"], signals["date"]))
    overlap_keys = candle_symdays & signal_keys

    overlap_mask = moves.apply(lambda r: (r["symbol"], r["date"]) in overlap_keys, axis=1)
    om = moves[overlap_mask]  # overlap moves
    om_missed = om[om["classification"] == "MISSED"]
    om_caught = om[om["classification"] == "CAUGHT"]
    om_ff = om[om["classification"] == "SIGNAL_FIRED_BUT_FAILED"]
    om_late = om[om["classification"] == "LATE_CATCH"]

    # -----------------------------------------------------------------------
    L("# Missed Moves Scanner Report")
    L(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    L(f"\n**Data:** {candles_1m['symbol'].nunique()} symbols, "
      f"{candles_1m['date'].nunique()} days ({candles_1m['date'].min()} to {candles_1m['date'].max()}), "
      f"{len(candles_1m):,} 1m candles")
    L(f"\n**Signals:** {len(signals):,} ({signals['date'].min()} to {signals['date'].max()})")
    L(f"\n**Overlapping symbol-days:** {len(overlap_keys)} (out of {len(candle_symdays)} candle symbol-days)")
    L(f"\n**Detection params:** >={MIN_ATR_MAG} ATR magnitude, >={MIN_BARS} bars ({MIN_BARS * 5} min), "
      f"reversal threshold {REVERSAL_ATR} ATR")

    # ==== Section 1 ====
    L("\n## Section 1: Move Scanner Summary\n")
    L(f"**Total significant moves:** {len(moves):,}")
    L(f"- Up: {len(moves[moves['direction'] == 'up']):,}, "
      f"Down: {len(moves[moves['direction'] == 'down']):,}")
    L(f"- Mean magnitude: {moves['magnitude_atr'].mean():.2f} ATR, "
      f"median: {moves['magnitude_atr'].median():.2f}, "
      f"max: {moves['magnitude_atr'].max():.2f}")
    L(f"- Mean duration: {moves['duration_bars'].mean():.1f} bars ({moves['duration_bars'].mean() * 5:.0f} min)")

    L("\n### By Symbol\n")
    L("| Symbol | Moves | Days | /Day | Avg ATR | Max ATR | Up | Down |")
    L("|--------|-------|------|------|---------|---------|-----|------|")
    for sym in sorted(moves["symbol"].unique()):
        sub = moves[moves["symbol"] == sym]
        days = sub["date"].nunique()
        L(f"| {sym} | {len(sub)} | {days} | {len(sub) / max(days, 1):.1f} | "
          f"{sub['magnitude_atr'].mean():.2f} | {sub['magnitude_atr'].max():.2f} | "
          f"{len(sub[sub['direction'] == 'up'])} | {len(sub[sub['direction'] == 'down'])} |")

    L("\n### By Time Bucket\n")
    L("| Time | Moves | Avg ATR | Max ATR |")
    L("|------|-------|---------|---------|")
    for tb in ["9:30-9:45", "9:45-10:00", "10:00-10:30", "10:30-11:00",
               "11:00-12:00", "12:00-14:00", "14:00-15:00", "15:00-16:00"]:
        sub = moves[moves["time_bucket"] == tb]
        if len(sub):
            L(f"| {tb} | {len(sub)} | {sub['magnitude_atr'].mean():.2f} | {sub['magnitude_atr'].max():.2f} |")

    # ==== Section 2 ====
    L("\n## Section 2: Coverage Analysis\n")
    L("**All analysis below uses only overlapping symbol-days** (where we have both candles and signals).\n")
    L(f"**Total moves on overlap days:** {len(om):,}")

    L("\n| Classification | Count | % | Total ATR |")
    L("|----------------|-------|---|-----------|")
    for cls in ["CAUGHT", "SIGNAL_FIRED_BUT_FAILED", "LATE_CATCH", "MISSED"]:
        sub = om[om["classification"] == cls]
        pct = len(sub) / max(len(om), 1) * 100
        L(f"| {cls} | {len(sub)} | {pct:.1f}% | {sub['magnitude_atr'].sum():.1f} |")

    if len(om) > 0:
        total_atr = om["magnitude_atr"].sum()
        L(f"\n**Total ATR in moves:** {total_atr:.1f}")
        L(f"**ATR caught (CAUGHT):** {om_caught['magnitude_atr'].sum():.1f} "
          f"({om_caught['magnitude_atr'].sum() / max(total_atr, 0.01) * 100:.1f}%)")
        L(f"**ATR with signal (CAUGHT + FIRED_BUT_FAILED + LATE):** "
          f"{(om_caught['magnitude_atr'].sum() + om_ff['magnitude_atr'].sum() + om_late['magnitude_atr'].sum()):.1f} "
          f"({(om_caught['magnitude_atr'].sum() + om_ff['magnitude_atr'].sum() + om_late['magnitude_atr'].sum()) / max(total_atr, 0.01) * 100:.1f}%)")
        L(f"**ATR missed:** {om_missed['magnitude_atr'].sum():.1f} "
          f"({om_missed['magnitude_atr'].sum() / max(total_atr, 0.01) * 100:.1f}%)")

    L("\n### Coverage by Symbol\n")
    L("| Symbol | Caught | Fired/Failed | Late | Missed | Total | Coverage % |")
    L("|--------|--------|-------------|------|--------|-------|-----------|")
    for sym in sorted(om["symbol"].unique()):
        sub = om[om["symbol"] == sym]
        c = len(sub[sub["classification"] == "CAUGHT"])
        ff = len(sub[sub["classification"] == "SIGNAL_FIRED_BUT_FAILED"])
        lt = len(sub[sub["classification"] == "LATE_CATCH"])
        ms = len(sub[sub["classification"] == "MISSED"])
        cov = (c + ff + lt) / max(len(sub), 1) * 100
        L(f"| {sym} | {c} | {ff} | {lt} | {ms} | {len(sub)} | {cov:.0f}% |")

    L("\n### Coverage by Time Bucket\n")
    L("| Time | Caught | Fired/Failed | Late | Missed | Coverage % |")
    L("|------|--------|-------------|------|--------|-----------|")
    for tb in ["9:30-9:45", "9:45-10:00", "10:00-10:30", "10:30-11:00",
               "11:00-12:00", "12:00-14:00", "14:00-15:00", "15:00-16:00"]:
        sub = om[om["time_bucket"] == tb]
        if len(sub):
            c = len(sub[sub["classification"] == "CAUGHT"])
            ff = len(sub[sub["classification"] == "SIGNAL_FIRED_BUT_FAILED"])
            lt = len(sub[sub["classification"] == "LATE_CATCH"])
            ms = len(sub[sub["classification"] == "MISSED"])
            cov = (c + ff + lt) / max(len(sub), 1) * 100
            L(f"| {tb} | {c} | {ff} | {lt} | {ms} | {cov:.0f}% |")

    L("\n### Coverage by Magnitude\n")
    L("| Magnitude | Caught | Fired/Failed | Late | Missed | Coverage % |")
    L("|-----------|--------|-------------|------|--------|-----------|")
    for (lo, hi), lbl in [((0.5, 1.0), "0.5-1.0"), ((1.0, 1.5), "1.0-1.5"),
                           ((1.5, 2.0), "1.5-2.0"), ((2.0, 3.0), "2.0-3.0"), ((3.0, 100), "3.0+")]:
        sub = om[(om["magnitude_atr"] >= lo) & (om["magnitude_atr"] < hi)]
        if len(sub):
            c = len(sub[sub["classification"] == "CAUGHT"])
            ff = len(sub[sub["classification"] == "SIGNAL_FIRED_BUT_FAILED"])
            lt = len(sub[sub["classification"] == "LATE_CATCH"])
            ms = len(sub[sub["classification"] == "MISSED"])
            cov = (c + ff + lt) / max(len(sub), 1) * 100
            L(f"| {lbl} ATR | {c} | {ff} | {lt} | {ms} | {cov:.0f}% |")

    # ==== Section 3 ====
    L("\n## Section 3: Missed Moves Inventory (Overlap Days)\n")
    L(f"**Total missed:** {len(om_missed):,}\n")

    if len(om_missed) > 0:
        ms = om_missed.sort_values("magnitude_atr", ascending=False)
        L("| # | Symbol | Date | Start | Dir | ATR Mag | Bars | Vol | EMA | VWAP | Pattern |")
        L("|---|--------|------|-------|-----|---------|------|-----|-----|------|---------|")
        for i, (_, row) in enumerate(ms.iterrows()):
            if i >= 150:
                L(f"| ... | _{len(ms) - 150} more_ | | | | | | | | | |")
                break
            st = pd.Timestamp(row["start_time"])
            L(f"| {i + 1} | {row['symbol']} | {row['date']} | {st.strftime('%H:%M')} | "
              f"{row['direction']} | {row['magnitude_atr']:.2f} | {row['duration_bars']}b | "
              f"{row['vol_ratio']:.1f}x | {row['ema_pos']} | {row['vwap_pos']} | {row['pattern_category']} |")

    # ==== Section 4 ====
    L("\n## Section 4: Missed Move Fingerprints\n")

    for cat in ["Gap_and_Pullback", "Level_Desert_Grind", "Failed_Breakout_Fade",
                 "Post_CONF_Failure_Continuation", "No_Signal_Zone"]:
        sub = om_missed[om_missed["pattern_category"] == cat]
        if len(sub) == 0:
            continue
        L(f"\n### {cat.replace('_', ' ')} (n={len(sub)})\n")
        L(f"- **Total ATR missed:** {sub['magnitude_atr'].sum():.1f}")
        L(f"- **Avg magnitude:** {sub['magnitude_atr'].mean():.2f} ATR, "
          f"max: {sub['magnitude_atr'].max():.2f}")
        L(f"- **Avg duration:** {sub['duration_bars'].mean():.1f} bars ({sub['duration_bars'].mean() * 5:.0f} min)")
        L(f"- **Avg vol ratio:** {sub['vol_ratio'].mean():.1f}x")

        ea = (sub["ema_pos"] == "above").sum()
        va = (sub["vwap_pos"] == "above").sum()
        L(f"- **EMA above:** {ea}/{len(sub)} ({ea / len(sub) * 100:.0f}%)")
        L(f"- **VWAP above:** {va}/{len(sub)} ({va / len(sub) * 100:.0f}%)")

        up = (sub["direction"] == "up").sum()
        L(f"- **Direction:** {up} up / {len(sub) - up} down")

        sub_tb = sub.copy()
        sub_tb["tb"] = sub_tb["start_time"].apply(time_bucket)
        tb_dist = sub_tb["tb"].value_counts().head(4).to_dict()
        sym_dist = sub["symbol"].value_counts().head(5).to_dict()
        L(f"- **Time dist:** {tb_dist}")
        L(f"- **Top symbols:** {sym_dist}")

        suggestions = {
            "Gap_and_Pullback": "ORB pullback signal: after strong opening bar, signal on pullback to ORB level",
            "Level_Desert_Grind": "Trend-continuation signal: EMA+VWAP alignment without key level requirement",
            "Failed_Breakout_Fade": "Failed-breakout fade: reverse signal when price closes back through level after breakout",
            "Post_CONF_Failure_Continuation": "CONF re-arm: re-enable signal after CONF failure if setup persists",
            "No_Signal_Zone": "New level types (intraday pivots, round numbers) or lower signal threshold",
        }
        L(f"- **Suggested fix:** {suggestions.get(cat, 'Investigate')}")

    # ==== Section 5 ====
    L("\n## Section 5: Top 20 Largest Missed Moves\n")

    if len(om_missed) > 0:
        top20 = om_missed.sort_values("magnitude_atr", ascending=False).head(20)
        for rank, (_, row) in enumerate(top20.iterrows(), 1):
            st = pd.Timestamp(row["start_time"])
            et = pd.Timestamp(row["end_time"])
            info = row["sig_info"]
            L(f"\n### #{rank}: {row['symbol']} {row['date']} — "
              f"{row['magnitude_atr']:.2f} ATR {row['direction']}")
            L(f"- **Time:** {st.strftime('%H:%M')} -> {et.strftime('%H:%M')} "
              f"({row['duration_bars']}b = {row['duration_bars'] * 5} min)")
            L(f"- **Price:** ${row['start_price']:.2f} -> ${row['end_price']:.2f}")
            L(f"- **Context:** Vol {row['vol_ratio']:.1f}x, EMA {row['ema_pos']}, VWAP {row['vwap_pos']}")
            L(f"- **Pattern:** {row['pattern_category']}")
            if info.get("had_opposite_before"):
                L(f"- Opposite signal fired within 30min before ({info['opposite_count']} signals)")
            if info.get("had_conf_fail_before"):
                L(f"- Same-direction CONF failure within 30min ({info['conf_fail_count']} failures)")

    # ==== Section 6 ====
    L("\n## Section 6: Pattern Frequency and Value\n")

    if len(om_missed) > 0:
        L("| Pattern | Count | % | Total ATR | Avg ATR | Top Time |")
        L("|---------|-------|---|-----------|---------|----------|")
        for cat in om_missed["pattern_category"].value_counts().index:
            sub = om_missed[om_missed["pattern_category"] == cat]
            pct = len(sub) / len(om_missed) * 100
            sub_tb = sub.copy()
            sub_tb["tb"] = sub_tb["start_time"].apply(time_bucket)
            top_tb = sub_tb["tb"].value_counts().index[0]
            L(f"| {cat} | {len(sub)} | {pct:.0f}% | "
              f"{sub['magnitude_atr'].sum():.1f} | {sub['magnitude_atr'].mean():.2f} | {top_tb} |")

    # ==== Section 7 ====
    L("\n## Section 7: Recommendations\n")

    if len(om_missed) > 0:
        pat_atr = om_missed.groupby("pattern_category")["magnitude_atr"].agg(["sum", "count", "mean"])
        pat_atr = pat_atr.sort_values("sum", ascending=False)

        fixes = {
            "Level_Desert_Grind": "Add trend-continuation signal: EMA/VWAP alignment without key level. Largest opportunity.",
            "No_Signal_Zone": "Add intraday pivots / round numbers as level types, or lower volume threshold.",
            "Gap_and_Pullback": "Add ORB pullback retest signal for strong opens.",
            "Failed_Breakout_Fade": "Detect breakout failure and fire reverse signal.",
            "Post_CONF_Failure_Continuation": "Re-arm signal after CONF failure if setup persists.",
        }

        L("### Priority-Ranked Improvements\n")
        L("| # | Pattern | Total Missed ATR | Count | Fix |")
        L("|---|---------|-----------------|-------|-----|")
        for rank, (cat, row) in enumerate(pat_atr.iterrows(), 1):
            L(f"| {rank} | {cat} | {row['sum']:.1f} | {int(row['count'])} | {fixes.get(cat, 'Investigate')} |")

        L("\n### Symbols With Most Missed ATR\n")
        sym_atr = om_missed.groupby("symbol")["magnitude_atr"].agg(["sum", "count", "mean"])
        sym_atr = sym_atr.sort_values("sum", ascending=False)
        for sym, row in sym_atr.iterrows():
            L(f"- **{sym}:** {row['sum']:.1f} ATR ({int(row['count'])} moves, avg {row['mean']:.2f})")

        L("\n### Time Buckets With Most Missed ATR\n")
        om_missed_tb = om_missed.copy()
        om_missed_tb["tb"] = om_missed_tb["start_time"].apply(time_bucket)
        tb_atr = om_missed_tb.groupby("tb")["magnitude_atr"].agg(["sum", "count"])
        tb_atr = tb_atr.sort_values("sum", ascending=False)
        for tb, row in tb_atr.iterrows():
            L(f"- **{tb}:** {row['sum']:.1f} ATR ({int(row['count'])} moves)")

        L("\n### What We Catch Well\n")
        if len(om_caught) > 0:
            L(f"Caught {len(om_caught)} moves ({om_caught['magnitude_atr'].sum():.1f} ATR) with CONF signals:\n")
            for _, row in om_caught.sort_values("magnitude_atr", ascending=False).head(5).iterrows():
                st = pd.Timestamp(row["start_time"])
                info = row["sig_info"]
                L(f"- {row['symbol']} {row['date']} {st.strftime('%H:%M')} — "
                  f"{row['magnitude_atr']:.2f} ATR {row['direction']} "
                  f"(signal: {info.get('sig_type', '?')} {info.get('sig_levels', '')} "
                  f"at {info.get('sig_time', '?')}, conf: {info.get('sig_conf', '?')})")
        else:
            L("No moves were classified as CAUGHT with confirmed signals on overlap days.")
            L("\nThis likely means signals fire at different times than when the zig-zag detects move starts.")
            L("The zig-zag measures from swing lows/highs, while signals fire at level touches/breaks.")
            L("**Consider:** Widening the match window beyond [-5min, +10min] or matching anywhere during the move.")

        L("\n### Signals Fired But CONF Failed\n")
        if len(om_ff) > 0:
            L(f"{len(om_ff)} moves had matching signals without CONF, "
              f"totaling {om_ff['magnitude_atr'].sum():.1f} ATR.\n")
            L("**These are directly recoverable** if CONF criteria are relaxed:\n")
            for _, row in om_ff.sort_values("magnitude_atr", ascending=False).head(10).iterrows():
                st = pd.Timestamp(row["start_time"])
                info = row["sig_info"]
                L(f"- {row['symbol']} {row['date']} {st.strftime('%H:%M')} — "
                  f"{row['magnitude_atr']:.2f} ATR {row['direction']} "
                  f"(signal: {info.get('sig_type', '?')} {info.get('sig_levels', '')} "
                  f"at {info.get('sig_time', '?')})")

        L("\n### Late Catches\n")
        if len(om_late) > 0:
            L(f"{len(om_late)} moves had signals that fired late (after first 10min), "
              f"totaling {om_late['magnitude_atr'].sum():.1f} ATR.\n")
            for _, row in om_late.sort_values("magnitude_atr", ascending=False).head(10).iterrows():
                st = pd.Timestamp(row["start_time"])
                info = row["sig_info"]
                L(f"- {row['symbol']} {row['date']} {st.strftime('%H:%M')} — "
                  f"{row['magnitude_atr']:.2f} ATR {row['direction']} "
                  f"(signal: {info.get('sig_type', '?')} at {info.get('sig_time', '?')})")

    L("\n---")
    L(f"\n*Report generated by missed_moves_scanner.py on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    return "\n".join(lines)


# ===========================================================================
# Main
# ===========================================================================
def main():
    print("=" * 60)
    print("MISSED MOVES SCANNER")
    print("=" * 60)

    print("\n--- Step 1: Loading 1m candle data ---")
    candles_1m = load_candle_data()

    print("\n--- Step 2: Resampling to 5m ---")
    bars_5m = resample_5m(candles_1m)

    print("\n--- Step 3: Detecting significant moves ---")
    moves = detect_moves(bars_5m)

    if len(moves) == 0:
        print("ERROR: No moves detected! Check thresholds.")
        return

    print("\n--- Step 4: Cross-referencing with signals ---")
    signals = load_signals()
    moves = cross_reference(moves, signals)

    print("\n--- Step 5: Categorizing missed moves ---")
    moves = categorize(moves)

    print("\n--- Step 6: Generating report ---")
    report = generate_report(moves, signals, candles_1m)
    with open(REPORT_PATH, "w") as f:
        f.write(report)

    print(f"\nReport written to: {REPORT_PATH}")

    missed = moves[moves["classification"] == "MISSED"]
    caught = moves[moves["classification"] == "CAUGHT"]
    ff = moves[moves["classification"] == "SIGNAL_FIRED_BUT_FAILED"]
    late = moves[moves["classification"] == "LATE_CATCH"]
    print(f"\n{'=' * 60}")
    print(f"SUMMARY: {len(moves)} moves, {moves['symbol'].nunique()} symbols, {moves['date'].nunique()} days")
    print(f"CAUGHT: {len(caught)} | FIRED_FAILED: {len(ff)} | LATE: {len(late)} | MISSED: {len(missed)}")
    print(f"Missed ATR: {missed['magnitude_atr'].sum():.1f}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
