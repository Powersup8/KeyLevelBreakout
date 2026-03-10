"""
Move scan for 2026-03-09 across all 15 KLB symbols.
Threshold: 0.3 ATR (was 1.0). Goal: surface all tradeable scalping moves.
"""

import pandas as pd
import numpy as np
from pathlib import Path

CACHE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars")
SYMBOLS = ["SPY", "AAPL", "AMD", "AMZN", "GLD", "GOOGL", "META", "MSFT", "NFLX", "NVDA", "QQQ", "SLV", "TSLA", "TSM", "XLE"]
HIGHLIGHT = {"SPY", "QQQ", "NVDA", "TSLA", "META"}

# Berlin RTH for 2026-03-09: 14:30–21:00 Berlin (UTC+1)
# ET = Berlin - 5h → 09:30–16:00 ET
RTH_START_BERLIN = "14:30"
RTH_END_BERLIN   = "21:00"
TARGET_DATE      = "2026-03-09"  # Berlin date


def wilder_atr(daily: pd.DataFrame, period: int = 14) -> float:
    """14-period Wilder's ATR as of 2026-03-08 (day before scan date)."""
    # Filter to rows on or before 2026-03-08 (daily index is tz-naive date)
    cutoff = pd.Timestamp("2026-03-08")
    hist = daily[daily.index.normalize() <= cutoff].copy()
    if len(hist) < period + 1:
        return np.nan
    hist = hist.tail(period + 30)  # enough runway
    tr = pd.concat([
        hist["high"] - hist["low"],
        (hist["high"] - hist["close"].shift(1)).abs(),
        (hist["low"]  - hist["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    # Wilder smoothing
    atr = tr.iloc[:period].mean()
    for v in tr.iloc[period:]:
        atr = (atr * (period - 1) + v) / period
    return float(atr)


def load_5m(symbol: str) -> pd.DataFrame | None:
    path = CACHE / f"{symbol.lower()}_5_mins_ib.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    # 'date' is a column, not the index
    df = df.set_index("date")
    df.index = df.index.tz_convert("Europe/Berlin")
    # Filter to RTH on target date
    start = pd.Timestamp(f"{TARGET_DATE} {RTH_START_BERLIN}", tz="Europe/Berlin")
    end   = pd.Timestamp(f"{TARGET_DATE} {RTH_END_BERLIN}",   tz="Europe/Berlin")
    df = df[(df.index >= start) & (df.index <= end)].copy()
    return df if len(df) >= 3 else None


def load_daily(symbol: str) -> pd.DataFrame | None:
    path = CACHE / f"{symbol.lower()}_1_day_ib.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df.set_index("date")
    # Daily index is tz-naive — keep as-is for ATR computation
    return df


def berlin_to_et(ts: pd.Timestamp) -> str:
    """Convert Berlin timestamp to ET string (subtract 5h for post-DST)."""
    et = ts.tz_convert("US/Eastern")
    return et.strftime("%H:%M")


def zigzag_moves(bars: pd.DataFrame, atr: float, threshold: float = 0.3) -> list[dict]:
    """
    Simple zig-zag: track running swing high/low.
    When price reverses >= threshold*ATR from the swing extreme, record the completed move.
    """
    min_move = atr * threshold
    moves = []

    closes = bars["close"].values
    highs  = bars["high"].values
    lows   = bars["low"].values
    vols   = bars["volume"].values
    times  = bars.index

    if len(closes) < 2:
        return moves

    # Initialise
    swing_high = highs[0]
    swing_low  = lows[0]
    swing_high_idx = 0
    swing_low_idx  = 0
    direction = None  # 'bull' or 'bear', set after first reversal

    # Use a simple approach: track current trend
    # Start: assume neutral, first move determines direction
    pivot_idx = 0
    pivot_price = closes[0]
    pivot_high = highs[0]
    pivot_low  = lows[0]
    trend = None  # None until we establish first trend

    # Running extremes from pivot
    run_high = highs[0]
    run_low  = lows[0]
    run_high_idx = 0
    run_low_idx  = 0

    for i in range(1, len(closes)):
        h = highs[i]
        l = lows[i]

        if h > run_high:
            run_high = h
            run_high_idx = i
        if l < run_low:
            run_low = l
            run_low_idx = i

        if trend is None:
            # Establish trend on first significant move
            up_move   = run_high - pivot_low
            down_move = pivot_high - run_low
            if up_move >= min_move:
                trend = "bull"
                pivot_idx = run_low_idx if run_low_idx < run_high_idx else 0
                pivot_price = run_low
                run_high = h
                run_high_idx = i
            elif down_move >= min_move:
                trend = "bear"
                pivot_idx = run_high_idx if run_high_idx < run_low_idx else 0
                pivot_price = run_high
                run_low = l
                run_low_idx = i
        elif trend == "bull":
            # Look for bear reversal from swing high
            if run_high - l >= min_move:
                # Completed bull move: pivot → run_high
                start_i = pivot_idx
                end_i   = run_high_idx
                move_bars = bars.iloc[start_i:end_i+1]
                mag_pts = run_high - pivot_price
                moves.append({
                    "symbol":       "",
                    "direction":    "bull",
                    "start_time":   times[start_i],
                    "end_time":     times[end_i],
                    "start_price":  pivot_price,
                    "end_price":    run_high,
                    "magnitude_pts": round(mag_pts, 4),
                    "magnitude_atr": round(mag_pts / atr, 3),
                    "peak_vol":     int(move_bars["volume"].max()) if len(move_bars) else 0,
                })
                # New bear trend starts from swing high
                trend = "bear"
                pivot_idx   = run_high_idx
                pivot_price = run_high
                run_low     = l
                run_low_idx = i
                run_high    = h
                run_high_idx = i
        elif trend == "bear":
            # Look for bull reversal from swing low
            if h - run_low >= min_move:
                # Completed bear move: pivot → run_low
                start_i = pivot_idx
                end_i   = run_low_idx
                move_bars = bars.iloc[start_i:end_i+1]
                mag_pts = pivot_price - run_low
                moves.append({
                    "symbol":       "",
                    "direction":    "bear",
                    "start_time":   times[start_i],
                    "end_time":     times[end_i],
                    "start_price":  pivot_price,
                    "end_price":    run_low,
                    "magnitude_pts": round(mag_pts, 4),
                    "magnitude_atr": round(mag_pts / atr, 3),
                    "peak_vol":     int(move_bars["volume"].max()) if len(move_bars) else 0,
                })
                # New bull trend starts from swing low
                trend = "bull"
                pivot_idx   = run_low_idx
                pivot_price = run_low
                run_high    = h
                run_high_idx = i
                run_low     = l
                run_low_idx = i

    # Capture any in-progress final move if it meets threshold
    if trend == "bull" and run_high - pivot_price >= min_move:
        start_i = pivot_idx
        end_i   = run_high_idx
        move_bars = bars.iloc[start_i:end_i+1]
        mag_pts = run_high - pivot_price
        moves.append({
            "symbol":       "",
            "direction":    "bull",
            "start_time":   times[start_i],
            "end_time":     times[end_i],
            "start_price":  pivot_price,
            "end_price":    run_high,
            "magnitude_pts": round(mag_pts, 4),
            "magnitude_atr": round(mag_pts / atr, 3),
            "peak_vol":     int(move_bars["volume"].max()) if len(move_bars) else 0,
        })
    elif trend == "bear" and pivot_price - run_low >= min_move:
        start_i = pivot_idx
        end_i   = run_low_idx
        move_bars = bars.iloc[start_i:end_i+1]
        mag_pts = pivot_price - run_low
        moves.append({
            "symbol":       "",
            "direction":    "bear",
            "start_time":   times[start_i],
            "end_time":     times[end_i],
            "start_price":  pivot_price,
            "end_price":    run_low,
            "magnitude_pts": round(mag_pts, 4),
            "magnitude_atr": round(mag_pts / atr, 3),
            "peak_vol":     int(move_bars["volume"].max()) if len(move_bars) else 0,
        })

    return moves


def classify(mag_atr: float) -> str:
    if mag_atr >= 0.8:
        return "MAJOR"
    elif mag_atr >= 0.5:
        return "MEDIUM"
    else:
        return "scalp"


# ── Main ──────────────────────────────────────────────────────────────────────

all_moves = []
atr_map   = {}

print(f"\n{'='*70}")
print(f"  KLB MOVE SCAN — 2026-03-09  |  Threshold: 0.3 ATR")
print(f"{'='*70}\n")

for sym in SYMBOLS:
    bars  = load_5m(sym)
    daily = load_daily(sym)

    if bars is None or daily is None:
        print(f"  {sym:6s}  ⚠  no data")
        continue

    atr = wilder_atr(daily)
    if np.isnan(atr) or atr <= 0:
        print(f"  {sym:6s}  ⚠  ATR unavailable")
        continue

    atr_map[sym] = atr
    moves = zigzag_moves(bars, atr, threshold=0.3)

    for m in moves:
        m["symbol"] = sym
    all_moves.extend(moves)

    tag = " ★" if sym in HIGHLIGHT else ""
    print(f"  {sym:6s}{tag:2}  ATR={atr:.3f}  bars={len(bars):2d}  moves={len(moves)}")

# ── Convert times to ET, build DataFrame ──────────────────────────────────────

if not all_moves:
    print("\nNo moves found.")
else:
    df = pd.DataFrame(all_moves)
    df["start_et"] = df["start_time"].apply(berlin_to_et)
    df["end_et"]   = df["end_time"].apply(berlin_to_et)
    df["class"]    = df["magnitude_atr"].apply(classify)
    df["flag"]     = df["symbol"].apply(lambda s: "★" if s in HIGHLIGHT else " ")

    # Sort by start_time
    df = df.sort_values("start_time").reset_index(drop=True)

    # ── Full move table ────────────────────────────────────────────────────────
    print(f"\n{'─'*80}")
    print(f"  ALL MOVES  (sorted by start ET)")
    print(f"{'─'*80}")
    print(f"  {'F':1} {'SYM':6} {'DIR':4} {'START':5} {'END':5} {'PTS':>8} {'ATR':>6} {'CLASS':7} {'PEAK_VOL':>10}")
    print(f"  {'-'*76}")

    for _, r in df.iterrows():
        dir_arrow = "↑" if r["direction"] == "bull" else "↓"
        print(f"  {r['flag']:1} {r['symbol']:6} {dir_arrow:1} {r['direction']:4} "
              f"{r['start_et']:5} {r['end_et']:5} "
              f"{r['magnitude_pts']:8.3f} {r['magnitude_atr']:6.3f} "
              f"{r['class']:7} {r['peak_vol']:10,}")

    # ── Summary by symbol ──────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("  SUMMARY BY SYMBOL")
    print(f"{'─'*60}")
    print(f"  {'SYM':6} {'ATR':>7} {'#MOVES':>6} {'#MAJ':>5} {'#MED':>5} {'#SCA':>5} {'NET_DIR':>8}")
    print(f"  {'-'*56}")

    for sym in SYMBOLS:
        sub = df[df["symbol"] == sym]
        if sub.empty:
            continue
        atr = atr_map.get(sym, 0)
        n_maj = (sub["class"] == "MAJOR").sum()
        n_med = (sub["class"] == "MEDIUM").sum()
        n_sca = (sub["class"] == "scalp").sum()
        bull_atr = sub[sub["direction"] == "bull"]["magnitude_atr"].sum()
        bear_atr = sub[sub["direction"] == "bear"]["magnitude_atr"].sum()
        net = bull_atr - bear_atr
        net_str = f"+{net:.2f}" if net >= 0 else f"{net:.2f}"
        flag = "★" if sym in HIGHLIGHT else " "
        print(f"  {flag}{sym:5} {atr:7.3f} {len(sub):6d} {n_maj:5d} {n_med:5d} {n_sca:5d} {net_str:>8}")

    # ── Cross-symbol coordination windows ──────────────────────────────────────
    print(f"\n{'─'*70}")
    print("  COORDINATION WINDOWS  (3+ symbols same direction within 15 min)")
    print(f"{'─'*70}")

    # For each move, check how many other symbols had same-direction move within ±15min
    window_min = pd.Timedelta("15min")
    found_windows = []

    for _, row in df.iterrows():
        t     = row["start_time"]
        direc = row["direction"]
        # Find all moves in window with same direction
        mask = (
            (df["direction"] == direc) &
            (df["start_time"] >= t - window_min) &
            (df["start_time"] <= t + window_min) &
            (df["symbol"] != row["symbol"])
        )
        peers = df[mask]["symbol"].tolist()
        all_syms = [row["symbol"]] + peers
        if len(all_syms) >= 3:
            key = (direc, t.floor("15min"))
            found_windows.append({
                "window_start": t.floor("15min"),
                "direction":    direc,
                "symbols":      sorted(set(all_syms)),
                "n":            len(set(all_syms)),
            })

    if found_windows:
        coord_df = pd.DataFrame(found_windows).drop_duplicates(subset=["window_start", "direction"])
        coord_df = coord_df.sort_values("window_start")
        for _, r in coord_df.iterrows():
            et_str = berlin_to_et(r["window_start"].tz_localize("Europe/Berlin") if r["window_start"].tzinfo is None else r["window_start"])
            arrow  = "↑" if r["direction"] == "bull" else "↓"
            syms   = ", ".join(r["symbols"])
            stars  = [s for s in r["symbols"] if s in HIGHLIGHT]
            print(f"  {et_str}  {arrow} {r['direction']:4}  N={r['n']}  [{syms}]"
                  + (f"  ★{','.join(stars)}" if stars else ""))
    else:
        print("  None found.")

    # ── Major moves detail ─────────────────────────────────────────────────────
    majors = df[df["class"] == "MAJOR"].copy()
    if not majors.empty:
        print(f"\n{'─'*70}")
        print(f"  MAJOR MOVES DETAIL (≥0.8 ATR)  —  {len(majors)} total")
        print(f"{'─'*70}")
        for _, r in majors.iterrows():
            dir_arrow = "↑" if r["direction"] == "bull" else "↓"
            flag = "★ " if r["symbol"] in HIGHLIGHT else "  "
            print(f"  {flag}{r['symbol']:6} {dir_arrow} {r['start_et']}–{r['end_et']}  "
                  f"{r['magnitude_pts']:.3f}pts  {r['magnitude_atr']:.3f}ATR  vol={r['peak_vol']:,}")

    print(f"\n{'='*70}")
    print(f"  Total moves: {len(df)}  |  Major: {(df['class']=='MAJOR').sum()}  "
          f"|  Medium: {(df['class']=='MEDIUM').sum()}  "
          f"|  Scalp: {(df['class']=='scalp').sum()}")
    print(f"{'='*70}\n")
