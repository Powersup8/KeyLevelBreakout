"""
KLB Daily Investigation — 2026-03-09
Parses v3.6 pine logs + IB 5m data to produce investigation-2026-03-09.md
"""
import glob
import re
import os
import pandas as pd
import numpy as np
from datetime import time, timedelta

TARGET_DATE = "2026-03-09"
IB_CACHE = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars/"
LOG_DIR = "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug/"
OUTPUT = LOG_DIR + "investigation-2026-03-09.md"

SYMBOLS = ["SPY","AAPL","AMD","AMZN","GLD","GOOGL","META","MSFT","NFLX","NVDA","QQQ","SLV","TSLA","TSM","XLE"]

# ── 1. Load all pine log files ─────────────────────────────────────────────────

def load_pine_logs():
    """Load all v3.6 pine log rows for TARGET_DATE."""
    files = sorted(glob.glob(LOG_DIR + "pine-logs-Key Level Breakout v3.6_*.csv"))
    rows = []
    for fpath in files:
        fhash = os.path.basename(fpath).replace("pine-logs-Key Level Breakout v3.6_","").replace(".csv","")
        with open(fpath, encoding="utf-8") as f:
            content = f.read()
        # Handle multiline quoted cells
        import csv, io
        reader = csv.reader(io.StringIO(content))
        next(reader)  # skip header
        for row in reader:
            if not row:
                continue
            date_str = row[0]
            msg = row[1] if len(row) > 1 else ""
            if not date_str.startswith(TARGET_DATE):
                continue
            rows.append({"file": fhash, "datetime_str": date_str, "msg": msg})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # Parse datetime (ET, -04:00 after DST)
    df["dt"] = pd.to_datetime(df["datetime_str"], utc=True).dt.tz_convert("America/New_York")
    df["time"] = df["dt"].dt.strftime("%H:%M")
    return df

# ── 2. Identify which symbol each log file covers ──────────────────────────────

def identify_symbols(log_df):
    """Assign symbol to each file hash using price from log messages."""
    if log_df.empty:
        return {}

    # Extract Open price from messages (O=xxx field)
    o_pattern = re.compile(r' O(\d+\.?\d*) ')

    file_prices = {}
    for fhash, grp in log_df.groupby("file"):
        prices = []
        for msg in grp["msg"]:
            m = o_pattern.search(msg)
            if m:
                prices.append(float(m.group(1)))
        if prices:
            file_prices[fhash] = np.median(prices)

    # Load reference open prices for 3/9 from IB daily
    ref_opens = {}
    for sym in SYMBOLS:
        try:
            df = pd.read_parquet(IB_CACHE + f"{sym.lower()}_1_day_ib.parquet")
            df["date"] = pd.to_datetime(df["date"])
            row = df[df["date"].dt.strftime("%Y-%m-%d") == TARGET_DATE]
            if len(row) == 0:
                row = df[df["date"].dt.strftime("%Y-%m-%d") == "2026-03-07"]
            if len(row) > 0:
                ref_opens[sym] = float(row.iloc[0]["open"])
        except Exception as e:
            pass

    # Also try from 5m data: first bar open on 3/9
    for sym in SYMBOLS:
        try:
            df = pd.read_parquet(IB_CACHE + f"{sym.lower()}_5_mins_ib.parquet")
            df["dt"] = pd.to_datetime(df["date"]).dt.tz_convert("America/New_York")
            df = df.set_index("dt")
            day = df[df.index.strftime("%Y-%m-%d") == TARGET_DATE]
            day = day.between_time("09:30","09:35")
            if len(day) > 0:
                ref_opens[sym] = float(day.iloc[0]["open"])
        except:
            pass

    # Match file → symbol by closest price
    file_symbol = {}
    used_symbols = set()
    for fhash, med_price in sorted(file_prices.items(), key=lambda x: x[1]):
        best_sym = None
        best_diff = float("inf")
        for sym, op in ref_opens.items():
            if sym in used_symbols:
                continue
            diff = abs(med_price - op) / max(op, 1)
            if diff < best_diff:
                best_diff = diff
                best_sym = sym
        if best_sym and best_diff < 0.05:  # within 5%
            file_symbol[fhash] = best_sym
            used_symbols.add(best_sym)
        else:
            file_symbol[fhash] = f"UNKNOWN({med_price:.0f})"

    return file_symbol

# ── 3. Parse signal messages ────────────────────────────────────────────────────

def parse_signals(log_df, file_symbol):
    """Extract structured signal rows from pine log."""
    signal_pat = re.compile(
        r'\[KLB\] (\d+:\d+) ([▲▼]) (BRK|REV|FADE|RNG|~+) (.+?)(?= vol=| pos=|$)'
    )
    vol_pat    = re.compile(r'vol=(\S+)')
    ema_pat    = re.compile(r'ema=(\S+)')
    adx_pat    = re.compile(r'adx=(\d+)')
    body_pat   = re.compile(r'body=(\d+)%')
    pos_pat    = re.compile(r'pos=([^\s]+)')
    atr_pat    = re.compile(r' ATR=(\d+\.?\d*)')
    o_pat      = re.compile(r' O(\d+\.?\d*) ')
    conf_pat   = re.compile(r'\[KLB\] CONF (\d+:\d+)')
    bail_pat   = re.compile(r'\[KLB\] (5m CHECK|BAIL|HOLD) (\d+:\d+).*?pnl=([+-]?\d+\.?\d*)')
    rng_pat    = re.compile(r'\[KLB\] (\d+:\d+) ([▲▼]) RNG range break vol=(\S+)')

    signals = []
    conf_times = {}  # (file, time) -> True
    bail_info = {}   # (file, time) -> {action, pnl}

    for _, row in log_df.iterrows():
        msg = row["msg"]
        fhash = row["file"]
        t = row["time"]
        sym = file_symbol.get(fhash, "?")

        # CONF events
        cm = conf_pat.search(msg)
        if cm:
            conf_times[(fhash, cm.group(1))] = True

        # BAIL/HOLD/CHECK events
        bm = bail_pat.search(msg)
        if bm:
            bail_info[(fhash, bm.group(2))] = {"action": bm.group(1), "pnl": float(bm.group(3))}

        # RNG signals (simpler format)
        rm = rng_pat.match(msg)
        if rm:
            signals.append({
                "time": rm.group(1), "sym": sym, "file": fhash,
                "dir": "▲" if rm.group(2) == "▲" else "▼",
                "type": "RNG", "level": "range break",
                "vol": rm.group(3), "ema": "", "adx": "",
                "body": "", "pos": "", "atr": "", "open": "",
                "conf": False, "exit_action": "", "exit_pnl": ""
            })
            continue

        # Skip non-signal lines (CONF, CHECK, BAIL, HOLD, ~~ lines without type)
        if "[KLB] CONF" in msg or "[KLB] 5m CHECK" in msg or "[KLB] BAIL" in msg or "[KLB] HOLD" in msg:
            continue
        # Skip DIM signals (start with ~ ~)
        if re.match(r'\[KLB\] \d+:\d+ [▲▼] ~ ~?', msg):
            continue

        # Real signals: BRK/REV/FADE
        sm = signal_pat.search(msg)
        if not sm:
            continue
        sig_time = sm.group(1)
        sig_dir = "▲" if sm.group(2) == "▲" else "▼"
        sig_type = sm.group(3)
        sig_level = sm.group(4).strip()

        vol_m  = vol_pat.search(msg)
        ema_m  = ema_pat.search(msg)
        adx_m  = adx_pat.search(msg)
        body_m = body_pat.search(msg)
        pos_m  = pos_pat.search(msg)
        atr_m  = atr_pat.search(msg)
        o_m    = o_pat.search(msg)

        signals.append({
            "time": sig_time, "sym": sym, "file": fhash,
            "dir": sig_dir, "type": sig_type, "level": sig_level,
            "vol": vol_m.group(1) if vol_m else "",
            "ema": ema_m.group(1) if ema_m else "",
            "adx": adx_m.group(1) if adx_m else "",
            "body": body_m.group(1) if body_m else "",
            "pos": pos_m.group(1) if pos_m else "",
            "atr": float(atr_m.group(1)) if atr_m else None,
            "open": float(o_m.group(1)) if o_m else None,
            "conf": False, "exit_action": "", "exit_pnl": ""
        })

    # Fill in CONF and exit info
    for sig in signals:
        key = (sig["file"], sig["time"])
        if key in conf_times:
            sig["conf"] = True
        if key in bail_info:
            sig["exit_action"] = bail_info[key]["action"]
            sig["exit_pnl"] = bail_info[key]["pnl"]

    return sorted(signals, key=lambda x: x["time"])

# ── 4. Load IB 5m data ──────────────────────────────────────────────────────────

def load_5m_data():
    """Load 5m IB bars for all symbols on 2026-03-09, RTH only (9:30-16:00 ET)."""
    data = {}
    for sym in SYMBOLS:
        try:
            df = pd.read_parquet(IB_CACHE + f"{sym.lower()}_5_mins_ib.parquet")
            # date column, already tz-aware (Europe/Berlin)
            df["dt"] = pd.to_datetime(df["date"]).dt.tz_convert("America/New_York")
            df = df.set_index("dt")
            day = df[df.index.strftime("%Y-%m-%d") == TARGET_DATE]
            day = day.between_time("09:30", "16:00")
            if len(day) > 0:
                data[sym] = day
        except Exception as e:
            print(f"  [WARN] {sym} 5m data not loaded: {e}")
    return data

def compute_atr(sym, period=14):
    """Compute 14-period ATR from daily bars."""
    try:
        df = pd.read_parquet(IB_CACHE + f"{sym.lower()}_1_day_ib.parquet")
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        df["prev_close"] = df["close"].shift(1)
        df["tr"] = df[["high","low","prev_close"]].apply(
            lambda r: max(r["high"]-r["low"], abs(r["high"]-r["prev_close"]), abs(r["low"]-r["prev_close"])), axis=1
        )
        df["atr"] = df["tr"].rolling(period).mean()
        # Get ATR for last day <= 2026-03-07 (last trading day before 3/9)
        row = df[df["date"].dt.strftime("%Y-%m-%d") <= "2026-03-07"].tail(1)
        if len(row) > 0:
            return float(row["atr"].iloc[0])
    except Exception as e:
        print(f"  [WARN] {sym} ATR failed: {e}")
    return None

# ── 5. Zig-zag move scanner ─────────────────────────────────────────────────────

def scan_moves(bars, atr, threshold=0.8):
    """Simple zig-zag: find swings >= threshold * ATR."""
    if bars is None or len(bars) == 0 or atr is None or atr == 0:
        return []

    prices = bars["close"].values
    highs  = bars["high"].values
    lows   = bars["low"].values
    times  = bars.index

    min_move = threshold * atr
    moves = []

    i = 0
    while i < len(prices) - 1:
        # Look for up move
        best_high_i = i
        for j in range(i+1, len(prices)):
            if highs[j] > highs[best_high_i]:
                best_high_i = j
            if lows[j] < lows[i] - min_move * 0.3:
                break  # started going other way significantly

        # Up move: from low[i] to high[best_high_i]
        up_mag = highs[best_high_i] - lows[i]
        if up_mag >= min_move:
            moves.append({
                "start_time": times[i].strftime("%H:%M"),
                "end_time": times[best_high_i].strftime("%H:%M"),
                "dir": "▲",
                "start_price": lows[i],
                "end_price": highs[best_high_i],
                "magnitude": up_mag,
                "magnitude_atr": up_mag / atr
            })

        # Down move: from high[i] to low[best_low_i]
        best_low_i = i
        for j in range(i+1, len(prices)):
            if lows[j] < lows[best_low_i]:
                best_low_i = j
            if highs[j] > highs[i] + min_move * 0.3:
                break

        down_mag = highs[i] - lows[best_low_i]
        if down_mag >= min_move:
            moves.append({
                "start_time": times[i].strftime("%H:%M"),
                "end_time": times[best_low_i].strftime("%H:%M"),
                "dir": "▼",
                "start_price": highs[i],
                "end_price": lows[best_low_i],
                "magnitude": down_mag,
                "magnitude_atr": down_mag / atr
            })

        i += 1

    # Deduplicate: merge overlapping moves of same direction
    moves = sorted(moves, key=lambda m: (m["start_time"], m["dir"], -m["magnitude"]))
    result = []
    seen = set()
    for m in moves:
        key = (m["start_time"], m["dir"])
        if key not in seen:
            seen.add(key)
            result.append(m)

    return sorted(result, key=lambda m: m["start_time"])

# Better zig-zag: proper swing detection
def proper_zigzag(bars, atr, threshold=0.8):
    """
    Classic zig-zag with reversal detection.
    Identifies alternating swing highs/lows where each leg >= threshold * ATR.
    State machine: track current direction, extend pivot until a reversal of >= min_move is seen.
    """
    if bars is None or len(bars) == 0 or atr is None or atr == 0:
        return []

    min_move = threshold * atr
    highs  = bars["high"].values
    lows   = bars["low"].values
    times  = bars.index
    n = len(highs)
    if n < 2:
        return []

    # Build pivot list using classic zig-zag
    # direction: 1=up, -1=down, 0=undecided
    pivot_i = 0
    pivot_price = (highs[0] + lows[0]) / 2
    direction = 0
    extreme_i = 0
    extreme_price = pivot_price

    pivots = []  # list of (bar_index, price, 'H' or 'L')

    for i in range(1, n):
        if direction == 0:
            # Determine initial direction
            up_move = highs[i] - lows[pivot_i]
            dn_move = highs[pivot_i] - lows[i]
            if up_move >= min_move and up_move > dn_move:
                direction = 1
                extreme_i = pivot_i
                extreme_price = lows[pivot_i]
                pivots.append((extreme_i, extreme_price, 'L'))
                extreme_i = i
                extreme_price = highs[i]
            elif dn_move >= min_move:
                direction = -1
                extreme_i = pivot_i
                extreme_price = highs[pivot_i]
                pivots.append((extreme_i, extreme_price, 'H'))
                extreme_i = i
                extreme_price = lows[i]
        elif direction == 1:
            # In uptrend: extend the high or look for reversal down
            if highs[i] > extreme_price:
                extreme_price = highs[i]
                extreme_i = i
            elif extreme_price - lows[i] >= min_move:
                # Reversal down
                pivots.append((extreme_i, extreme_price, 'H'))
                direction = -1
                extreme_price = lows[i]
                extreme_i = i
        elif direction == -1:
            # In downtrend: extend the low or look for reversal up
            if lows[i] < extreme_price:
                extreme_price = lows[i]
                extreme_i = i
            elif highs[i] - extreme_price >= min_move:
                # Reversal up
                pivots.append((extreme_i, extreme_price, 'L'))
                direction = 1
                extreme_price = highs[i]
                extreme_i = i

    # Add final extreme
    if direction == 1:
        pivots.append((extreme_i, extreme_price, 'H'))
    elif direction == -1:
        pivots.append((extreme_i, extreme_price, 'L'))

    # Convert consecutive pivot pairs to moves
    moves = []
    for j in range(len(pivots) - 1):
        a = pivots[j]
        b = pivots[j+1]
        mag = abs(b[1] - a[1])
        if mag < min_move:
            continue
        if a[2] == 'L' and b[2] == 'H':
            moves.append({
                "start_time": times[a[0]].strftime("%H:%M"),
                "end_time": times[b[0]].strftime("%H:%M"),
                "dir": "▲",
                "start_price": round(a[1], 2),
                "end_price": round(b[1], 2),
                "magnitude": round(mag, 2),
                "magnitude_atr": round(mag / atr, 2)
            })
        elif a[2] == 'H' and b[2] == 'L':
            moves.append({
                "start_time": times[a[0]].strftime("%H:%M"),
                "end_time": times[b[0]].strftime("%H:%M"),
                "dir": "▼",
                "start_price": round(a[1], 2),
                "end_price": round(b[1], 2),
                "magnitude": round(mag, 2),
                "magnitude_atr": round(mag / atr, 2)
            })

    return moves

# ── 6. Compute signal outcomes ──────────────────────────────────────────────────

def compute_outcomes(signals, bars_5m, atrs):
    """For each signal, compute: entry_price, mfe, outcome_5m, dir_correct."""
    for sig in signals:
        sym = sig["sym"]
        if sym not in bars_5m:
            sig["entry_price"] = sig["mfe"] = sig["outcome_5m"] = sig["dir_correct"] = ""
            continue

        bars = bars_5m[sym]
        atr = atrs.get(sym)
        sig_time = sig["time"]

        # Find entry bar
        entry_bars = bars[bars.index.strftime("%H:%M") == sig_time]
        if len(entry_bars) == 0:
            sig["entry_price"] = sig["mfe"] = sig["outcome_5m"] = sig["dir_correct"] = ""
            continue

        entry_idx = bars.index.get_loc(entry_bars.index[0])
        entry_price = float(bars.iloc[entry_idx]["close"])
        sig["entry_price"] = round(entry_price, 2)

        # Get next 12 bars (60 min)
        future = bars.iloc[entry_idx+1:entry_idx+13]
        if len(future) == 0:
            sig["mfe"] = sig["outcome_5m"] = sig["dir_correct"] = ""
            continue

        is_bull = sig["dir"] == "▲"

        if is_bull:
            mfe_price = future["high"].max()
            mfe_pts = mfe_price - entry_price
            outcome_5m_bar = future.iloc[0] if len(future) > 0 else None
            outcome_5m = float(outcome_5m_bar["close"]) - entry_price if outcome_5m_bar is not None else 0
        else:
            mfe_price = future["low"].min()
            mfe_pts = entry_price - mfe_price
            outcome_5m_bar = future.iloc[0] if len(future) > 0 else None
            outcome_5m = entry_price - float(outcome_5m_bar["close"]) if outcome_5m_bar is not None else 0

        atr_val = atr if atr else 1
        sig["mfe"] = round(mfe_pts / atr_val, 3) if atr_val else round(mfe_pts, 2)
        sig["outcome_5m"] = round(outcome_5m / atr_val, 3) if atr_val else round(outcome_5m, 2)
        sig["dir_correct"] = "✓" if outcome_5m > 0 else "✗"

# ── 7. Signal-to-move matching ──────────────────────────────────────────────────

def match_signals_to_moves(sym_moves, signals):
    """For each move, check if any signal within 15min of move start."""
    matched = {}
    for sym, moves in sym_moves.items():
        sym_sigs = [s for s in signals if s["sym"] == sym]
        for move in moves:
            mtime = move["start_time"]
            mhour, mmin = map(int, mtime.split(":"))
            m_mins = mhour * 60 + mmin

            catch_sig = None
            for sig in sym_sigs:
                shour, smin = map(int, sig["time"].split(":"))
                s_mins = shour * 60 + smin
                # Signal must be within [-5, +15] min of move start AND same direction
                if -5 <= (s_mins - m_mins) <= 15 and sig["dir"] == move["dir"]:
                    catch_sig = sig
                    break

            move["signal"] = catch_sig["time"] + " " + catch_sig["type"] if catch_sig else "❌ MISSED"
            matched[f"{sym}_{mtime}_{move['dir']}"] = move
    return matched

# ── 8. Cross-symbol analysis ────────────────────────────────────────────────────

def cross_symbol_events(bars_5m, atrs, threshold=0.8):
    """Find time windows where 4+ symbols moved in the same direction."""
    # For each 5m bar, check if close > open (up) or < open (down)
    symbol_dirs = {}
    for sym, bars in bars_5m.items():
        atr = atrs.get(sym, 1)
        bars = bars.copy()
        bars["pct_move"] = (bars["close"] - bars["open"]) / atr
        bars["dir"] = bars["pct_move"].apply(lambda x: "▲" if x > 0.1 else ("▼" if x < -0.1 else "~"))
        symbol_dirs[sym] = bars["dir"]

    # Align to common index
    all_times = sorted(set().union(*[set(v.index) for v in symbol_dirs.values()]))
    events = []
    for t in all_times:
        t_str = t.strftime("%H:%M")
        dirs = {"▲": [], "▼": []}
        for sym, ser in symbol_dirs.items():
            if t in ser.index:
                d = ser[t]
                if d in dirs:
                    dirs[d].append(sym)
        for d, syms in dirs.items():
            if len(syms) >= 4:
                events.append({"time": t_str, "dir": d, "count": len(syms), "symbols": syms})

    return events

# ── 9. Specific miss investigation ──────────────────────────────────────────────

def investigate_misses(bars_5m, atrs, signals, log_df, file_symbol):
    """Investigate each user-noted miss."""
    findings = []

    def get_bars(sym, start, end):
        """Get bars for symbol between HH:MM times."""
        if sym not in bars_5m:
            return None
        b = bars_5m[sym]
        return b.between_time(start, end)

    def move_stats(bars, direction="▼"):
        """Compute move stats for a bar range."""
        if bars is None or len(bars) == 0:
            return "no data"
        start_p = bars.iloc[0]["open"]
        if direction == "▼":
            end_p = bars["low"].min()
            mag = start_p - end_p
        else:
            end_p = bars["high"].max()
            mag = end_p - start_p
        return start_p, end_p, mag

    # TSLA: opening signals 9:30 bull vs 9:35 bear
    tsla_sigs = [s for s in signals if s["sym"] == "TSLA" and s["time"] in ["9:30","9:35","9:40","9:45","9:50","10:00","10:05","10:10","10:12","10:15","10:20"]]
    tsla_bars_open = get_bars("TSLA", "09:30", "10:30")

    finding = "### TSLA Opening Signals (9:30 bull vs 9:35 bear)\n"
    finding += f"**Signals at open:**\n"
    for s in tsla_sigs:
        conf = "CONF✓" if s["conf"] else ""
        finding += f"  - {s['time']} {s['dir']} {s['type']} @ {s['level']} vol={s['vol']} ema={s['ema']} {conf}\n"

    if tsla_bars_open is not None and len(tsla_bars_open) > 0:
        atr = atrs.get("TSLA", 1)
        finding += f"\n**5m price action (TSLA, 9:30-10:30):**\n"
        for idx, row in tsla_bars_open.iterrows():
            t = idx.strftime("%H:%M")
            mv = (row["close"] - row["open"]) / atr
            finding += f"  {t}: O={row['open']:.2f} H={row['high']:.2f} L={row['low']:.2f} C={row['close']:.2f} ({mv:+.2f} ATR)\n"
    findings.append(finding)

    # TSLA: uptrend after 10:12 not covered
    tsla_bars_1012 = get_bars("TSLA", "10:10", "11:30")
    finding = "### TSLA Uptrend after 10:12\n"
    if tsla_bars_1012 is not None and len(tsla_bars_1012) > 0:
        atr = atrs.get("TSLA", 1)
        finding += "**5m bars 10:10-11:30:**\n"
        lo = tsla_bars_1012["low"].min()
        hi = tsla_bars_1012["high"].max()
        finding += f"  Range: {lo:.2f}–{hi:.2f}, swing={hi-lo:.2f} pts = {(hi-lo)/atr:.2f} ATR\n"
        for idx, row in tsla_bars_1012.iterrows():
            t = idx.strftime("%H:%M")
            finding += f"  {t}: O={row['open']:.2f} H={row['high']:.2f} L={row['low']:.2f} C={row['close']:.2f}\n"
        tsla_sigs_1012 = [s for s in signals if s["sym"]=="TSLA" and s["time"]>="10:10" and s["time"]<="11:30"]
        if tsla_sigs_1012:
            finding += "**Signals in window:** " + ", ".join(f"{s['time']} {s['dir']} {s['type']}" for s in tsla_sigs_1012) + "\n"
        else:
            finding += "**Signals in window:** NONE\n"
    findings.append(finding)

    # SPY: 9:36-9:53 downtrend signaled late at 9:44
    spy_bars_open = get_bars("SPY", "09:30", "10:15")
    finding = "### SPY 9:36-9:53 Downtrend (late signal at 9:44)\n"
    spy_sigs_open = [s for s in signals if s["sym"]=="SPY" and s["time"]<="10:00"]
    for s in spy_sigs_open:
        finding += f"  Signal: {s['time']} {s['dir']} {s['type']} @ {s['level']} vol={s['vol']} ema={s['ema']}\n"
    if spy_bars_open is not None:
        atr = atrs.get("SPY", 1)
        finding += "**5m bars SPY 9:30-10:15:**\n"
        for idx, row in spy_bars_open.iterrows():
            t = idx.strftime("%H:%M")
            mv = (row["close"] - row["open"]) / atr
            finding += f"  {t}: O={row['open']:.2f} C={row['close']:.2f} ({mv:+.2f} ATR)\n"
    findings.append(finding)

    # SPY/QQQ: 9:54-10:04 upmove missed
    finding = "### SPY/QQQ 9:54-10:04 Upmove Missed\n"
    for sym in ["SPY","QQQ"]:
        b = get_bars(sym, "09:50", "10:10")
        if b is not None and len(b) > 0:
            atr = atrs.get(sym, 1)
            finding += f"**{sym} bars:**\n"
            for idx, row in b.iterrows():
                t = idx.strftime("%H:%M")
                finding += f"  {t}: O={row['open']:.2f} C={row['close']:.2f}\n"
        sigs = [s for s in signals if s["sym"]==sym and "9:54" <= s["time"] <= "10:05"]
        sig_strs = [s["time"]+" "+s["dir"]+" "+s["type"] for s in sigs]
        finding += f"  {sym} signals: {sig_strs or 'NONE'}\n"
    findings.append(finding)

    # SPY/QQQ: 10:05-10:13 down massive
    finding = "### SPY/QQQ 10:05-10:13 Down Massive — No Signal\n"
    for sym in ["SPY","QQQ"]:
        b = get_bars(sym, "10:00", "10:20")
        if b is not None and len(b) > 0:
            atr = atrs.get(sym, 1)
            finding += f"**{sym} bars:**\n"
            for idx, row in b.iterrows():
                t = idx.strftime("%H:%M")
                mv = (row["close"] - row["open"]) / atr
                finding += f"  {t}: O={row['open']:.2f} C={row['close']:.2f} H={row['high']:.2f} L={row['low']:.2f} ({mv:+.2f} ATR)\n"
        sigs = [s for s in signals if s["sym"]==sym and "10:00" <= s["time"] <= "10:20"]
        sig_strs = [s["time"]+" "+s["dir"]+" "+s["type"] for s in sigs]
        finding += f"  {sym} signals in window: {sig_strs or 'NONE'}\n"
    findings.append(finding)

    # SPY/QQQ: 10:14 long uptrend missed
    finding = "### SPY/QQQ 10:14 Long Uptrend Missed\n"
    for sym in ["SPY","QQQ"]:
        b = get_bars(sym, "10:10", "12:00")
        if b is not None and len(b) > 0:
            atr = atrs.get(sym, 1)
            lo = b["low"].min()
            hi = b["high"].max()
            lo_t = b["low"].idxmin().strftime("%H:%M")
            hi_t = b["high"].idxmax().strftime("%H:%M")
            finding += f"**{sym}:** low={lo:.2f}@{lo_t} → high={hi:.2f}@{hi_t} = {(hi-lo)/atr:.2f} ATR\n"
        sigs = [s for s in signals if s["sym"]==sym and "10:10" <= s["time"] <= "12:00"]
        sig_strs = [s["time"]+" "+s["dir"]+" "+s["type"] for s in sigs]
        finding += f"  {sym} signals: {sig_strs or 'NONE'}\n"
    findings.append(finding)

    # NVDA: 9:33-10:44 down missed and signaled up
    finding = "### NVDA 9:33-10:44 Down — Missed and Signaled Up\n"
    nvda_bars = get_bars("NVDA", "09:30", "11:00")
    nvda_sigs = [s for s in signals if s["sym"]=="NVDA" and s["time"] <= "11:00"]
    finding += "**NVDA signals before 11:00:**\n"
    for s in nvda_sigs:
        conf = "CONF✓" if s["conf"] else ""
        finding += f"  {s['time']} {s['dir']} {s['type']} @ {s['level']} vol={s['vol']} ema={s['ema']} {conf}\n"
    if nvda_bars is not None and len(nvda_bars) > 0:
        atr = atrs.get("NVDA", 1)
        finding += "**NVDA 5m bars:**\n"
        for idx, row in nvda_bars.iterrows():
            t = idx.strftime("%H:%M")
            mv = (row["close"] - row["open"]) / atr
            finding += f"  {t}: O={row['open']:.2f} C={row['close']:.2f} H={row['high']:.2f} L={row['low']:.2f} ({mv:+.2f} ATR)\n"
    findings.append(finding)

    # META: false signals?
    finding = "### META Signals — False?\n"
    meta_sigs = [s for s in signals if s["sym"]=="META"]
    meta_bars = get_bars("META", "09:30", "16:00")
    finding += "**META signals:**\n"
    for s in meta_sigs:
        conf = "CONF✓" if s["conf"] else ""
        mfe_str = f" mfe={s.get('mfe','')} ATR" if s.get('mfe','') != "" else ""
        dc = s.get('dir_correct', '')
        finding += f"  {s['time']} {s['dir']} {s['type']} @ {s['level']} vol={s['vol']} ema={s['ema']} {conf}{mfe_str} {dc}\n"
    if meta_bars is not None and len(meta_bars) > 0:
        atr = atrs.get("META", 1)
        finding += "**META 5m price action:**\n"
        for idx, row in meta_bars.iterrows():
            t = idx.strftime("%H:%M")
            mv = (row["close"] - row["open"]) / atr
            finding += f"  {t}: O={row['open']:.2f} C={row['close']:.2f} ({mv:+.2f} ATR)\n"
    findings.append(finding)

    # AAPL: 15:19 upmove missed
    finding = "### AAPL 15:19 Upmove Missed\n"
    aapl_bars = get_bars("AAPL", "15:10", "16:00")
    aapl_sigs = [s for s in signals if s["sym"]=="AAPL" and s["time"] >= "15:10"]
    if aapl_bars is not None and len(aapl_bars) > 0:
        atr = atrs.get("AAPL", 1)
        finding += "**AAPL bars 15:10-16:00:**\n"
        for idx, row in aapl_bars.iterrows():
            t = idx.strftime("%H:%M")
            mv = (row["close"] - row["open"]) / atr
            finding += f"  {t}: O={row['open']:.2f} C={row['close']:.2f} H={row['high']:.2f} ({mv:+.2f} ATR)\n"
    sig_strs = [s["time"]+" "+s["dir"]+" "+s["type"] for s in aapl_sigs]
    finding += f"**Signals:** {sig_strs or 'NONE'}\n"
    findings.append(finding)

    return findings

# ── 10. Also extract DIM signals ──────────────────────────────────────────────

def parse_dim_signals(log_df, file_symbol):
    """Extract suppressed (DIM) signals for context."""
    dim_rows = []
    for _, row in log_df.iterrows():
        msg = row["msg"]
        fhash = row["file"]
        sym = file_symbol.get(fhash, "?")
        # DIM signals: ~ ~ or ~ x~
        m = re.match(r'\[KLB\] (\d+:\d+) ([▲▼]) ~[~x]? ~?\s+([\w\s\+~]+?)\s+vol=(\S+)', msg)
        if m:
            dim_rows.append({
                "time": m.group(1), "sym": sym, "dir": m.group(2),
                "level": m.group(3).strip(), "vol": m.group(4)
            })
    return dim_rows

# ── MAIN ────────────────────────────────────────────────────────────────────────

def main():
    print("=== KLB Investigation 2026-03-09 ===")

    print("1. Loading pine logs...")
    log_df = load_pine_logs()
    print(f"   {len(log_df)} rows for {TARGET_DATE}")

    print("2. Identifying symbols...")
    file_symbol = identify_symbols(log_df)
    for fh, sym in sorted(file_symbol.items(), key=lambda x: x[1]):
        print(f"   {fh} → {sym}")

    print("3. Parsing signals...")
    signals = parse_signals(log_df, file_symbol)
    dim_signals = parse_dim_signals(log_df, file_symbol)
    print(f"   {len(signals)} active signals, {len(dim_signals)} dim signals")

    print("4. Loading 5m IB data...")
    bars_5m = load_5m_data()
    print(f"   Loaded {len(bars_5m)} symbols")

    print("5. Computing ATRs...")
    atrs = {}
    for sym in SYMBOLS:
        atr = compute_atr(sym)
        atrs[sym] = atr
        if atr:
            print(f"   {sym}: ATR={atr:.2f}")

    print("6. Computing signal outcomes...")
    compute_outcomes(signals, bars_5m, atrs)

    print("7. Scanning moves...")
    sym_moves = {}
    for sym in SYMBOLS:
        if sym in bars_5m:
            moves = proper_zigzag(bars_5m[sym], atrs.get(sym), threshold=0.8)
            sym_moves[sym] = moves
            if moves:
                print(f"   {sym}: {len(moves)} moves ≥0.8 ATR")

    print("8. Matching signals to moves...")
    match_signals_to_moves(sym_moves, signals)

    print("9. Cross-symbol analysis...")
    cross_events = cross_symbol_events(bars_5m, atrs)

    print("10. Investigating misses...")
    miss_findings = investigate_misses(bars_5m, atrs, signals, log_df, file_symbol)

    print("11. Writing report...")
    write_report(signals, dim_signals, sym_moves, cross_events, miss_findings, atrs, file_symbol, bars_5m)
    print(f"    → {OUTPUT}")

# ── Report Writer ────────────────────────────────────────────────────────────────

def write_report(signals, dim_signals, sym_moves, cross_events, miss_findings, atrs, file_symbol, bars_5m):
    lines = []

    lines.append("# KLB Daily Investigation — 2026-03-09\n")
    lines.append(f"*Generated from v3.6 pine logs + IB 5m data*\n")
    lines.append(f"*DST note: 2026-03-08 was US DST change. All times ET (UTC-4).*\n")

    # Symbol identification
    lines.append("\n## Symbol Identification\n")
    lines.append("| File Hash | Symbol | ATR |\n|-----------|--------|-----|\n")
    for fh, sym in sorted(file_symbol.items(), key=lambda x: x[1]):
        atr = atrs.get(sym)
        atr_str = f"{atr:.2f}" if atr is not None else "?"
        lines.append(f"| {fh} | {sym} | {atr_str} |\n")

    # Section 1: Signal Scorecard
    lines.append("\n## 1. Signal Scorecard\n")
    if signals:
        lines.append("| Time | Sym | Type | Dir | Level | Vol | EMA | ADX | Body | CONF | Exit | PnL | MFE | Dir✓ |\n")
        lines.append("|------|-----|------|-----|-------|-----|-----|-----|------|------|------|-----|-----|------|\n")
        for s in signals:
            conf = "✓" if s["conf"] else ""
            mfe = f"{s.get('mfe','')}" if s.get("mfe","") != "" else ""
            dc = s.get("dir_correct", "")
            pnl = s.get("exit_pnl","")
            exit_a = s.get("exit_action","")
            lines.append(f"| {s['time']} | {s['sym']} | {s['type']} | {s['dir']} | {s['level'][:30]} | {s['vol']} | {s['ema']} | {s['adx']} | {s['body']}% | {conf} | {exit_a} | {pnl} | {mfe} | {dc} |\n")
    else:
        lines.append("*No active signals found for this date.*\n")

    # Dim signals summary
    lines.append(f"\n**Suppressed (DIM) signals:** {len(dim_signals)} total\n")
    if dim_signals:
        dim_by_sym = {}
        for d in dim_signals:
            dim_by_sym.setdefault(d["sym"], []).append(d)
        for sym, ds in sorted(dim_by_sym.items()):
            lines.append(f"- **{sym}**: {len(ds)} suppressed — " +
                         ", ".join(f"{d['time']} {d['dir']} {d['level'][:20]}" for d in ds[:5]) +
                         ("..." if len(ds)>5 else "") + "\n")

    # Section 2: Move Scan
    lines.append("\n## 2. Move Scan (≥0.8 ATR)\n")
    lines.append("| Symbol | Start | End | Dir | Magnitude (ATR) | Signal Caught? |\n")
    lines.append("|--------|-------|-----|-----|-----------------|----------------|\n")
    total_moves = 0
    for sym in SYMBOLS:
        moves = sym_moves.get(sym, [])
        for m in moves:
            total_moves += 1
            lines.append(f"| {sym} | {m['start_time']} | {m['end_time']} | {m['dir']} | {m['magnitude_atr']} | {m.get('signal','?')} |\n")
    if total_moves == 0:
        lines.append("*No significant moves found (check data availability).*\n")

    # Section 3: Signal-to-Move Match
    lines.append("\n## 3. Signal-to-Move Match\n")
    caught = sum(1 for sym in SYMBOLS for m in sym_moves.get(sym,[]) if "❌" not in m.get("signal","❌"))
    missed = sum(1 for sym in SYMBOLS for m in sym_moves.get(sym,[]) if "❌" in m.get("signal","❌"))
    lines.append(f"- **Total moves ≥0.8 ATR:** {total_moves}\n")
    lines.append(f"- **Caught:** {caught}\n")
    lines.append(f"- **Missed:** {missed}\n")
    lines.append(f"- **Capture rate:** {caught/total_moves*100:.0f}%\n" if total_moves > 0 else "")

    sig_confs = [s for s in signals if s["conf"]]
    sig_total = len(signals)
    mfe_vals = [s["mfe"] for s in signals if isinstance(s.get("mfe"), float)]
    dir_correct = [s for s in signals if s.get("dir_correct") == "✓"]

    lines.append(f"\n**Signal quality:**\n")
    lines.append(f"- Total signals: {sig_total}\n")
    lines.append(f"- CONF rate: {len(sig_confs)}/{sig_total} = {len(sig_confs)/sig_total*100:.0f}%\n" if sig_total > 0 else "")
    lines.append(f"- Direction correct (5m): {len(dir_correct)}/{sig_total} = {len(dir_correct)/sig_total*100:.0f}%\n" if sig_total > 0 else "")
    lines.append(f"- Avg MFE (ATR): {np.mean(mfe_vals):.3f}\n" if mfe_vals else "")

    # Section 4: Miss Investigation
    lines.append("\n## 4. Miss Investigation\n")
    for finding in miss_findings:
        lines.append(finding + "\n")

    # Section 5: Cross-Symbol Events
    lines.append("\n## 5. Cross-Symbol Events\n")
    if cross_events:
        lines.append("| Time | Dir | Count | Symbols |\n|------|-----|-------|---------|\n")
        for e in sorted(cross_events, key=lambda x: x["time"]):
            syms_str = ", ".join(e["symbols"])
            lines.append(f"| {e['time']} | {e['dir']} | {e['count']} | {syms_str} |\n")
    else:
        lines.append("*No 4+ symbol coordinated moves found.*\n")

    # Add SPY regime notes
    if "SPY" in bars_5m:
        spy_bars = bars_5m["SPY"]
        spy_atr = atrs.get("SPY", 1)
        lines.append("\n**SPY regime summary:**\n")
        spy_open = float(spy_bars.iloc[0]["open"]) if len(spy_bars) > 0 else 0
        spy_close = float(spy_bars.iloc[-1]["close"]) if len(spy_bars) > 0 else 0
        spy_hi = float(spy_bars["high"].max())
        spy_lo = float(spy_bars["low"].min())
        lines.append(f"- Open: {spy_open:.2f}, Close: {spy_close:.2f}, High: {spy_hi:.2f}, Low: {spy_lo:.2f}\n")
        lines.append(f"- Day range: {spy_hi-spy_lo:.2f} pts = {(spy_hi-spy_lo)/spy_atr:.2f} ATR\n")
        lines.append(f"- Net: {spy_close-spy_open:+.2f} pts ({(spy_close-spy_open)/spy_atr:+.2f} ATR)\n")

    # Section 6: Synthesis
    lines.append("\n## 6. Synthesis & Action Items\n")

    lines.append("### Key Patterns\n")

    # Auto-analyze: which types fired, outcomes
    type_stats = {}
    for s in signals:
        t = s["type"]
        if t not in type_stats:
            type_stats[t] = {"n":0, "conf":0, "correct":0, "mfe_sum":0, "mfe_n":0}
        type_stats[t]["n"] += 1
        if s["conf"]: type_stats[t]["conf"] += 1
        if s.get("dir_correct") == "✓": type_stats[t]["correct"] += 1
        if isinstance(s.get("mfe"), float):
            type_stats[t]["mfe_sum"] += s["mfe"]
            type_stats[t]["mfe_n"] += 1

    lines.append("| Type | N | CONF% | Dir✓% | Avg MFE |\n|------|---|-------|-------|----------|\n")
    for t, st in sorted(type_stats.items()):
        conf_pct = f"{st['conf']/st['n']*100:.0f}%" if st['n'] > 0 else "?"
        dir_pct = f"{st['correct']/st['n']*100:.0f}%" if st['n'] > 0 else "?"
        avg_mfe = f"{st['mfe_sum']/st['mfe_n']:.3f}" if st['mfe_n'] > 0 else "?"
        lines.append(f"| {t} | {st['n']} | {conf_pct} | {dir_pct} | {avg_mfe} |\n")

    lines.append("\n### Action Items\n")
    lines.append("*[To be filled in after reviewing findings above]*\n")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.writelines(lines)

if __name__ == "__main__":
    main()
