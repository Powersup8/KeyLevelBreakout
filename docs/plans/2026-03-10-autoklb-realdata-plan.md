# AutoKLB Real-Data Harness Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a real-data backtester (`autoklb_realdata.py`) that replays the KLB indicator against actual 1m IB bars, replacing the catalog-only eval with a dual-eval loop that guards against catalog recall bias.

**Architecture:** `autoklb_realdata.py` loads 1m IB parquets, resamples to 5m, computes EMA20/50 + ADX14 + VWAP from raw bars (strict Pine parity), fires signals via `classify_signal()`, and measures 60-bar forward MFE/MAE — identical metric to `autoklb_prepare.py` for direct comparison. `autoklb_eval.py` wraps both scripts and prints merged output. `autoklb_program.md` updated so the loop runs `autoklb_eval.py` and keeps/discards on `rd_val_score`.

**Tech Stack:** Python 3, pandas, numpy. No new dependencies. Data: IB 1m/daily parquets at `/Users/mab/.../trading_bot/cache/bars/`, `debug/key-levels-db.parquet`.

---

## Chunk 1: Real-Data Harness Core

### Task 1: Create `autoklb_realdata.py`

**Files:**
- Create: `debug/autoklb_realdata.py`
- Reference: `debug/autoklb_prepare.py` (mirrors metric + split logic)
- Reference: `debug/autoklb_signals.py` (imports classify_signal)
- Data: `/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars/{sym}_1_min_ib.parquet`
- Data: `/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars/{sym}_1_day_ib.parquet`
- Data: `debug/key-levels-db.parquet`

- [ ] **Step 1: Write `autoklb_realdata.py`**

```python
#!/usr/bin/env python3
"""
AutoKLB Real-Data Harness — v3.7 baseline
==========================================
Replays KLB signal logic against real 1m IB bars.
DO NOT MODIFY — this is the evaluation harness.

Pine replication (strict parity):
- Signal timeframe: 5m (resampled from 1m)
- EMA20, EMA50: ewm span=20/50 on 5m close
- ADX(14,14): Wilder DMI on 5m OHLCV
- VWAP: session-reset cumulative on 5m bars
- Daily ATR(14): Wilder on daily bars, prior day value
- Volume SMA: 20-bar SMA on 5m volume

Signals fire on 5m bar close (first 1m of that 5m period).
MFE/MAE: 60 1m-bar forward window from signal bar.
"""

import sys
import time
import importlib
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

# ── Paths ────────────────────────────────────────────────────────────────────
DEBUG_DIR = Path(__file__).parent
CACHE_DIR = Path(
    "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de"
    "/Meine Ablage/Claude/trading_bot/cache/bars"
)
LEVELS_PATH = DEBUG_DIR / "key-levels-db.parquet"

# ── Fixed constants — mirror autoklb_prepare.py ───────────────────────────
SYMBOLS = [
    "SPY", "AAPL", "AMD", "AMZN", "GLD", "GOOGL", "META",
    "MSFT", "NFLX", "NVDA", "QQQ", "SLV", "TSLA", "XLE",
]
EXCLUDE_SYMBOLS = {"TSM"}
TRAIN_END = date(2025, 9, 30)
VAL_END   = date(2026, 1, 31)
MIN_SIGNALS_RAMP = 100
WIN_RATE_BASELINE = 0.50
FORWARD_BARS = 60        # 60 1m bars = 60 min MFE/MAE window
COOLDOWN_5M  = 5         # 5 x 5m = 25 min cooldown per (level, direction)


# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════════════════════

def load_1m(symbol):
    """Load 1m IB bars, filter to RTH 09:30–16:00 ET, return tz-naive index."""
    path = CACHE_DIR / f"{symbol}_1_min_ib.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    if "date" in df.columns:
        df = df.set_index("date")
    df.index = pd.to_datetime(df.index)
    if df.index.tz is not None:
        df.index = df.index.tz_convert("US/Eastern").tz_localize(None)
    df = df.between_time("09:30", "16:00")
    return df[["open", "high", "low", "close", "volume"]].copy()


def load_daily_atr(symbol):
    """Load daily bars, compute Wilder ATR(14). Returns Series indexed by date."""
    path = CACHE_DIR / f"{symbol}_1_day_ib.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    if "date" in df.columns:
        df = df.set_index("date")
    df.index = pd.to_datetime(df.index).normalize()
    atr = _wilder_atr(df["high"], df["low"], df["close"], 14)
    # Use previous day's ATR (Pine: atr[1], non-repainting)
    return atr.shift(1)


# ══════════════════════════════════════════════════════════════════════════════
# INDICATOR COMPUTATION
# ══════════════════════════════════════════════════════════════════════════════

def _wilder_atr(high, low, close, period=14):
    """Wilder's ATR — EMA-style smoothing (alpha = 1/period)."""
    prev = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev).abs(),
        (low  - prev).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def _wilder_adx(high, low, close, period=14):
    """Wilder's ADX (DMI 14,14) — returns ADX Series."""
    prev_high  = high.shift(1)
    prev_low   = low.shift(1)
    prev_close = close.shift(1)

    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)

    up   = high - prev_high
    down = prev_low - low
    plus_dm  = np.where((up > down) & (up > 0),   up,   0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    plus_dm  = pd.Series(plus_dm,  index=high.index)
    minus_dm = pd.Series(minus_dm, index=high.index)

    alpha = 1 / period
    smooth_tr    = tr.ewm(alpha=alpha, min_periods=period, adjust=False).mean()
    smooth_plus  = plus_dm.ewm(alpha=alpha, min_periods=period, adjust=False).mean()
    smooth_minus = minus_dm.ewm(alpha=alpha, min_periods=period, adjust=False).mean()

    plus_di  = 100 * smooth_plus  / smooth_tr.replace(0, np.nan)
    minus_di = 100 * smooth_minus / smooth_tr.replace(0, np.nan)
    denom    = (plus_di + minus_di).replace(0, np.nan)
    dx       = 100 * (plus_di - minus_di).abs() / denom
    return dx.ewm(alpha=alpha, min_periods=period, adjust=False).mean()


def resample_5m(df_1m):
    """Resample 1m OHLCV → 5m, drop incomplete bars."""
    return df_1m.resample("5min", closed="left", label="left").agg({
        "open":   "first",
        "high":   "max",
        "low":    "min",
        "close":  "last",
        "volume": "sum",
    }).dropna(subset=["close"])


def compute_indicators(df_5m):
    """
    Compute 5m indicators. All values shifted by 1 (Pine [1] = prev confirmed bar).
    Returns df_5m with added columns:
      ema20_p, ema50_p  — EMA(20), EMA(50) of close, previous bar
      adx_p             — ADX(14), previous bar
      vwap_p            — session VWAP, previous bar
      close_p           — previous close
      close_p2          — two bars ago close
      vol_sma20_p       — volume SMA(20), previous bar
    """
    df = df_5m.copy()

    # EMA
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()

    # ADX
    df["adx"] = _wilder_adx(df["high"], df["low"], df["close"], 14)

    # Volume SMA(20)
    df["vol_sma20"] = df["volume"].rolling(20).mean()

    # Session VWAP — reset each calendar day
    df["_date"] = df.index.date
    df["_tp"]   = (df["high"] + df["low"] + df["close"]) / 3
    rows = []
    for day, grp in df.groupby("_date"):
        cum_tpv = (grp["_tp"] * grp["volume"]).cumsum()
        cum_vol = grp["volume"].cumsum()
        vwap = cum_tpv / cum_vol.replace(0, np.nan)
        rows.append(vwap)
    df["vwap"] = pd.concat(rows).sort_index()

    # Shift all by 1 (Pine lookahead_on equivalent — use previous confirmed bar)
    df["ema20_p"]    = df["ema20"].shift(1)
    df["ema50_p"]    = df["ema50"].shift(1)
    df["adx_p"]      = df["adx"].shift(1)
    df["vwap_p"]     = df["vwap"].shift(1)
    df["close_p"]    = df["close"].shift(1)
    df["close_p2"]   = df["close"].shift(2)
    df["vol_sma20_p"]= df["vol_sma20"].shift(1)

    df = df.drop(columns=["_date", "_tp", "ema20", "ema50", "adx", "vwap", "vol_sma20"])
    return df


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

def _timing(ts):
    """Map 5m bar timestamp to timing_category."""
    from datetime import time as dtime
    t = ts.time()
    if t < dtime(9, 35):  return "open_flush"
    if t < dtime(11, 30): return "morning"
    if t < dtime(14, 0):  return "midday"
    return "afternoon"


def _level_interaction(close, prev_close, bar_high, bar_low, level_price):
    """
    Classify how the bar interacted with the level.
    broke_through : close crossed the level vs prior close
    reversed_at   : bar extreme tested level but close stayed same side
    near          : within proximity but no clear test
    """
    if prev_close < level_price <= close:
        return "broke_through"   # bull broke above
    if prev_close > level_price >= close:
        return "broke_through"   # bear broke below
    if bar_low <= level_price <= bar_high:
        return "reversed_at"     # tested level intra-bar
    return "near"


def build_row(symbol, ts, bar, daily_atr, level_type, dist_atr, interaction):
    """Build a feature dict compatible with classify_signal()."""
    bar_range = bar["high"] - bar["low"]
    direction = "bull" if bar["close"] >= bar["open"] else "bear"
    body_pct  = (abs(bar["close"] - bar["open"]) / bar_range * 100
                 if bar_range > 0 else 0.0)

    ema20_p = bar["ema20_p"]
    ema50_p = bar["ema50_p"]
    ema_bull = ema20_p > ema50_p if not (pd.isna(ema20_p) or pd.isna(ema50_p)) else False
    ema_bear = ema20_p < ema50_p if not (pd.isna(ema20_p) or pd.isna(ema50_p)) else False
    ema_aligned = ema_bull if direction == "bull" else ema_bear

    vwap_p = bar["vwap_p"]
    vwap_bull = bar["close"] > vwap_p if not pd.isna(vwap_p) else False
    vwap_bear = bar["close"] < vwap_p if not pd.isna(vwap_p) else False
    vwap_aligned = vwap_bull if direction == "bull" else vwap_bear

    vol_sma = bar["vol_sma20_p"]
    vol_ratio = bar["volume"] / vol_sma if (not pd.isna(vol_sma) and vol_sma > 0) else 0.0

    trig_range_atr = bar_range / daily_atr if daily_atr > 0 else np.nan

    return {
        "nearest_level_type":    level_type,
        "nearest_level_dist_atr": dist_atr,
        "direction":             direction,
        "symbol":                symbol,
        "trig_ema_aligned":      ema_aligned,
        "trig_body_pct":         body_pct,
        "trig_vol_ratio":        vol_ratio,
        "pre_adx":               bar["adx_p"] if not pd.isna(bar["adx_p"]) else 0.0,
        "trig_vwap_aligned":     vwap_aligned,
        "timing_category":       _timing(ts),
        "level_interaction":     interaction,
        "pre_vol_avg_ratio":     vol_ratio,   # approximate with same-bar ratio
        "trig_range_atr":        trig_range_atr,
        "spy_magnitude_atr":     np.nan,      # not available without SPY alignment
    }


# ══════════════════════════════════════════════════════════════════════════════
# SIGNAL EMISSION
# ══════════════════════════════════════════════════════════════════════════════

def emit_signals(symbol, df_5m_ind, levels_sym, daily_atr_series):
    """
    Walk every 5m bar for one symbol, fire classify_signal(), return list of dicts.
    Deduplication: 5-bar cooldown per (level_type, direction).
    """
    import autoklb_signals as signals
    importlib.reload(signals)

    fired = []
    cooldown = {}   # (level_type, direction) → bar index of last fire

    bars = list(df_5m_ind.iterrows())
    for i, (ts, bar) in enumerate(bars):
        bar_date = ts.date()

        # Warmup guard
        if pd.isna(bar.get("ema20_p")) or pd.isna(bar.get("adx_p")):
            continue

        daily_atr = daily_atr_series.get(
            pd.Timestamp(bar_date), np.nan
        ) if daily_atr_series is not None else np.nan
        if np.isnan(daily_atr) or daily_atr <= 0:
            continue

        levels_today = levels_sym[
            levels_sym["date"] == pd.Timestamp(bar_date)
        ]
        if len(levels_today) == 0:
            continue

        prev_close = bar.get("close_p", np.nan)
        if pd.isna(prev_close):
            continue

        prox_atr = signals.LEVEL_PROXIMITY_ATR * 1.5  # search slightly wider

        for _, lvl in levels_today.iterrows():
            level_price = lvl["level_price"]
            dist_atr = abs(bar["close"] - level_price) / daily_atr

            if dist_atr > prox_atr:
                continue

            interaction = _level_interaction(
                bar["close"], prev_close,
                bar["high"], bar["low"],
                level_price,
            )
            direction = "bull" if bar["close"] >= bar["open"] else "bear"
            cd_key = (lvl["level_name"], direction)

            if cd_key in cooldown and (i - cooldown[cd_key]) < COOLDOWN_5M:
                continue

            row = build_row(
                symbol, ts, bar, daily_atr,
                lvl["level_name"], dist_atr, interaction,
            )
            result = signals.classify_signal(pd.Series(row))

            if result["would_fire"] and not result["is_dimmed"]:
                cooldown[cd_key] = i
                fired.append({
                    "symbol":      symbol,
                    "date":        bar_date,
                    "timestamp":   ts,
                    "direction":   direction,
                    "signal_type": result["signal_type"],
                    "level_type":  lvl["level_name"],
                    "timing":      _timing(ts),
                    "daily_atr":   daily_atr,
                })

    return fired


# ══════════════════════════════════════════════════════════════════════════════
# P&L ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def compute_forward_pnl(df_1m, signal_ts, direction, daily_atr, n=FORWARD_BARS):
    """
    Compute n-bar forward MFE/MAE from signal_ts on 1m bars.
    Returns (mfe_atr, mae_atr) or (nan, nan) if insufficient future bars.
    """
    idx = df_1m.index.searchsorted(signal_ts)
    if idx >= len(df_1m):
        return np.nan, np.nan

    entry = df_1m.iloc[idx]["close"]
    future = df_1m.iloc[idx + 1: idx + 1 + n]
    if len(future) < 5:   # need at least 5 bars for meaningful MFE/MAE
        return np.nan, np.nan

    if direction == "bull":
        mfe = (future["high"].max() - entry) / daily_atr
        mae = (entry - future["low"].min())  / daily_atr
    else:
        mfe = (entry - future["low"].min())  / daily_atr
        mae = (future["high"].max() - entry) / daily_atr

    return max(0.0, mfe), max(0.0, mae)


def compute_pnl(row):
    """Identical to autoklb_prepare.py — winners need mfe>=0.10 AND mfe>mae."""
    mfe, mae = row["mfe_1m"], row["mae_1m"]
    if mfe >= 0.10 and mfe > mae:
        return mfe - mae
    return -mae


def compute_score(df):
    """Identical composite metric to autoklb_prepare.py."""
    if len(df) == 0:
        return 0.0, 0.0, 0.0, 0
    pnls     = df["pnl_atr"]
    net_atr  = pnls.sum()
    n        = len(df)
    win_rate = (pnls > 0).mean()
    score    = net_atr * (win_rate / WIN_RATE_BASELINE) * min(1.0, n / MIN_SIGNALS_RAMP)
    return score, net_atr, win_rate, n


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    t0 = time.time()

    levels_db = pd.read_parquet(LEVELS_PATH)
    levels_db["date"] = pd.to_datetime(levels_db["date"])

    all_signals = []

    for symbol in SYMBOLS:
        if symbol in EXCLUDE_SYMBOLS:
            continue

        df_1m = load_1m(symbol)
        if df_1m is None or len(df_1m) == 0:
            continue

        daily_atr_s = load_daily_atr(symbol)
        daily_atr_map = {}
        if daily_atr_s is not None:
            for dt_idx, val in daily_atr_s.items():
                daily_atr_map[pd.Timestamp(dt_idx)] = val

        df_5m     = resample_5m(df_1m)
        df_5m_ind = compute_indicators(df_5m)

        levels_sym = levels_db[levels_db["symbol"] == symbol].copy()

        fired = emit_signals(symbol, df_5m_ind, levels_sym, daily_atr_map)

        for sig in fired:
            mfe, mae = compute_forward_pnl(
                df_1m, sig["timestamp"], sig["direction"], sig["daily_atr"]
            )
            if not (np.isnan(mfe) or np.isnan(mae)):
                sig["mfe_1m"] = mfe
                sig["mae_1m"] = mae
                all_signals.append(sig)

    if not all_signals:
        print("rd_train_score:    0.0")
        print("rd_val_score:      0.0")
        return

    df = pd.DataFrame(all_signals)
    df["date_dt"]  = pd.to_datetime(df["date"])
    df["pnl_atr"]  = df.apply(compute_pnl, axis=1)

    train = df[df["date_dt"] <= pd.Timestamp(TRAIN_END)]
    val   = df[
        (df["date_dt"] > pd.Timestamp(TRAIN_END)) &
        (df["date_dt"] <= pd.Timestamp(VAL_END))
    ]

    ts, tn, twr, tN = compute_score(train)
    vs, vn, vwr, vN = compute_score(val)

    elapsed = time.time() - t0

    print("---rd---")
    print(f"rd_train_score:    {ts:.1f}")
    print(f"rd_train_net_atr:  {tn:.1f}")
    print(f"rd_train_win_rate: {twr * 100:.1f}")
    print(f"rd_train_n:        {tN}")
    print(f"rd_val_score:      {vs:.1f}")
    print(f"rd_val_net_atr:    {vn:.1f}")
    print(f"rd_val_win_rate:   {vwr * 100:.1f}")
    print(f"rd_val_n:          {vN}")
    print(f"rd_total_seconds:  {elapsed:.1f}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify it imports cleanly**

```bash
cd "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView/debug"
python3 -c "import autoklb_realdata; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Run a single-symbol smoke test**

```bash
cd debug
python3 -c "
import autoklb_realdata as rd
import pandas as pd

# Load one symbol
df_1m = rd.load_1m('SPY')
print('1m rows:', len(df_1m))
print('date range:', df_1m.index[0], '-', df_1m.index[-1])

df_5m = rd.resample_5m(df_1m)
df_5m_ind = rd.compute_indicators(df_5m)
print('5m rows:', len(df_5m_ind))
print('ADX sample:', df_5m_ind['adx_p'].dropna().head(3).values)
print('VWAP sample:', df_5m_ind['vwap_p'].dropna().head(3).values)
"
```
Expected: 1m rows in thousands, 5m rows ~4-6x smaller, ADX/VWAP non-NaN and reasonable values.

- [ ] **Step 4: Run single-symbol signal test**

```bash
cd debug
python3 -c "
import autoklb_realdata as rd
import pandas as pd

df_1m = rd.load_1m('SPY')
daily_atr_s = rd.load_daily_atr('SPY')
daily_atr_map = {pd.Timestamp(dt): v for dt, v in daily_atr_s.items() if not pd.isna(v)}
df_5m_ind = rd.compute_indicators(rd.resample_5m(df_1m))
levels_db = pd.read_parquet(rd.LEVELS_PATH)
levels_db['date'] = pd.to_datetime(levels_db['date'])
levels_sym = levels_db[levels_db['symbol'] == 'SPY']

fired = rd.emit_signals('SPY', df_5m_ind, levels_sym, daily_atr_map)
print(f'SPY signals fired: {len(fired)}')
if fired:
    import pprint; pprint.pprint(fired[0])
"
```
Expected: signals fired > 0 (should be dozens to hundreds for SPY across full history).

- [ ] **Step 5: Run full evaluation**

```bash
cd debug
python3 autoklb_realdata.py
```
Expected: Prints `---rd---` block with `rd_train_score`, `rd_val_score`. Should complete in <5 minutes. Both scores should be positive (real edge exists in the data).

- [ ] **Step 6: Commit**

```bash
cd "/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/misc/TradingView"
git add debug/autoklb_realdata.py
git commit -m "autoklb: real-data harness — 5m indicator replay + 60-bar MFE/MAE eval"
```

---

### Task 2: Create `autoklb_eval.py` Wrapper

**Files:**
- Create: `debug/autoklb_eval.py`
- Reference: `debug/autoklb_prepare.py`, `debug/autoklb_realdata.py`

- [ ] **Step 1: Write the wrapper**

```python
#!/usr/bin/env python3
"""
AutoKLB Eval Wrapper — runs catalog eval + real-data eval in sequence.
Output is the union of both scripts' stdout; agent greps:
  - train_score / val_score     → catalog metrics
  - rd_train_score / rd_val_score → real-data metrics
Keep/discard loop is based on rd_val_score.
"""
import subprocess
import sys
from pathlib import Path

DEBUG_DIR = Path(__file__).parent


def run(script):
    r = subprocess.run(
        [sys.executable, str(DEBUG_DIR / script)],
        capture_output=True, text=True, cwd=str(DEBUG_DIR),
    )
    if r.stdout:
        print(r.stdout, end="")
    if r.stderr:
        print(r.stderr, end="", file=sys.stderr)
    return r.returncode


rc1 = run("autoklb_prepare.py")
rc2 = run("autoklb_realdata.py")
sys.exit(0 if rc1 == 0 else rc1)
```

- [ ] **Step 2: Run the wrapper and verify merged output**

```bash
cd debug
python3 autoklb_eval.py 2>&1 | grep -E "^(train_score|val_score|rd_train_score|rd_val_score):"
```
Expected: 4 lines — catalog train/val scores + real-data train/val scores.

- [ ] **Step 3: Commit**

```bash
git add debug/autoklb_eval.py
git commit -m "autoklb: eval wrapper — runs catalog + real-data harness in sequence"
```

---

### Task 3: Sync v3.7 Features to `autoklb_signals.py`

**Files:**
- Modify: `debug/autoklb_signals.py`
- Reference: `KeyLevelBreakout.pine` (v3.7 diff: big-candle bypass, VWAP Reclaim, SPY reclaim DIM)

Three v3.7 additions:
1. **Large-candle bypass** — `trig_range_atr >= 2.0` → skip DIM (already has `trig_range_atr` in interface)
2. **VWAP Reclaim signal** — new `VRC` type, fires when 2 prev bars on one side of VWAP then close crosses
3. **SPY reclaim DIM** — SPY held above VWAP 2+ bars → dim bear signals in midday/outperform

- [ ] **Step 1: Add large-candle bypass to `_check_dim`**

In `autoklb_signals.py`, locate `_check_dim` and add this BEFORE the dim-condition checks:

```python
# v3.7: large-candle bypass — 2+ ATR bar = directional conviction, skip all dim
BIG_CANDLE_ATR = 2.0
```

At the top of the constants block, then in `_check_dim` body add after the broad-coil check:

```python
    if not np.isnan(trig_range) and trig_range >= BIG_CANDLE_ATR:
        return False
```

- [ ] **Step 2: Add VWAP Reclaim fields to classify_signal interface**

Add these to the constants block:
```python
VWAP_RECLAIM_ENABLED = True   # v3.7: VWAP crossover signal
```

In `classify_signal()`, after the existing field reads, add:
```python
    prev_above_vwap  = row.get("prev_close_above_vwap",  False)
    prev2_above_vwap = row.get("prev2_close_above_vwap", False)
    close_above_vwap = row.get("close_above_vwap",       False)
```

Add VWAP Reclaim logic right before the final `return result`:
```python
    # ── v3.7: VWAP Reclaim signal ──
    # 2 consecutive prev bars on one side → close crosses to other side
    if VWAP_RECLAIM_ENABLED and not result["would_fire"]:
        is_bull_reclaim = (
            direction == "bull"
            and close_above_vwap
            and not prev_above_vwap
            and not prev2_above_vwap
            and not _check_symbol_suppression(symbol, "VWAP", "bull", "VRC")
        )
        is_bear_reclaim = (
            direction == "bear"
            and not close_above_vwap
            and prev_above_vwap
            and prev2_above_vwap
        )
        if is_bull_reclaim or is_bear_reclaim:
            result["would_fire"] = True
            result["signal_type"] = "VRC"
            result["is_dimmed"] = _check_dim(vol, pre_vol, trig_range, timing, spy_mag)
```

Also add NVDA bull VRC suppression to SYMBOL_DISABLED:
```python
SYMBOL_DISABLED = {
    "NVDA": {
        ("*", "bull", "REV"),   # v3.3d
        ("*", "bull", "VRC"),   # v3.7: NVDA bull VWAP Reclaim suppressed
    },
}
```

- [ ] **Step 3: Add SPY reclaim DIM fields**

Add new fields in `classify_signal()` reads:
```python
    spy_above_vwap      = row.get("spy_above_vwap",      False)
    spy_prev_above_vwap = row.get("spy_prev_above_vwap",  False)
    rs_vs_spy           = row.get("rs_vs_spy",            0.0)
```

Pass `spy_above_vwap`, `spy_prev_above_vwap`, `rs_vs_spy` into `_check_dim` by expanding its signature:

```python
def _check_dim(vol, pre_vol, trig_range, timing, spy_mag,
               spy_above_vwap=False, spy_prev_above_vwap=False,
               rs_vs_spy=0.0, direction="bull"):
```

Add to dim conditions in `_check_dim`:
```python
    # v3.7: SPY sustained VWAP reclaim → dim bear signals in midday or outperforming
    is_spy_reclaim_dim = (
        direction == "bear"
        and spy_above_vwap and spy_prev_above_vwap
        and (_is_midday(timing) or rs_vs_spy > 0)
    )
```

Include `is_spy_reclaim_dim` in the return:
```python
    return is_vol_exhaust or is_exhausted or is_spy_reclaim_dim
```

Update all three `_check_dim(...)` call sites in `classify_signal()` to pass the new args.

- [ ] **Step 4: Verify catalog eval still passes**

```bash
cd debug
python3 autoklb_prepare.py 2>&1 | grep "^val_score:"
```
Expected: score close to current value (no regression from v3.7 additions). VWAP Reclaim won't fire in catalog eval because catalog rows won't have `close_above_vwap` — defaults to False, so no change.

- [ ] **Step 5: Commit**

```bash
git add debug/autoklb_signals.py
git commit -m "autoklb: sync v3.7 — big-candle bypass, VWAP Reclaim signal, SPY reclaim DIM"
```

---

### Task 4: Update `autoklb_program.md` Loop Instructions

**Files:**
- Modify: `debug/autoklb_program.md`

- [ ] **Step 1: Update loop command and keep/discard rule**

Replace the "Experiment loop" section in `autoklb_program.md`:

```markdown
## Experiment loop

LOOP FOREVER:

1. Read current `autoklb_signals.py` + results history
2. Propose ONE change (parameter tweak or routing modification)
3. `git commit` the change
4. Run: `cd debug && python3 autoklb_eval.py > autoklb_run.log 2>&1`
5. Check catalog: `grep "^train_score:\|^val_score:" debug/autoklb_run.log`
6. Check real-data: `grep "^rd_train_score:\|^rd_val_score:" debug/autoklb_run.log`
7. If both greps empty → crash. Run `tail -50 debug/autoklb_run.log`, fix or skip.
8. Log to results.tsv (all 8 score columns)
9. **KEEP** if `rd_val_score` improved (or equal) AND `rd_train_score` didn't drop >5%
10. **DISCARD** (`git reset --hard HEAD~1`) otherwise
11. REPEAT

**NEVER STOP.** Do not ask the human if you should continue. Run until interrupted.
```

- [ ] **Step 2: Update results.tsv header**

`autoklb_results.tsv` gains 4 new columns:
```
commit	train_score	val_score	train_n	val_n	rd_train_score	rd_val_score	rd_train_n	rd_val_n	status	description
```

- [ ] **Step 3: Commit**

```bash
git add debug/autoklb_program.md debug/autoklb_results.tsv
git commit -m "autoklb: update loop to dual-eval — rd_val_score is the new target"
```

---

### Task 5: End-to-End Validation

- [ ] **Step 1: Run full dual eval and record baseline**

```bash
cd debug
python3 autoklb_eval.py > autoklb_run.log 2>&1
grep -E "^(train_score|val_score|rd_train_score|rd_val_score):" autoklb_run.log
```
Expected: 4 lines. Record `rd_val_score` as the new baseline for future experiments.

- [ ] **Step 2: Sanity check — catalog vs real-data inflation ratio**

The catalog `val_score` (817.5 from last session) should be higher than `rd_val_score`. The ratio is the "catalog inflation factor" — how much the recall-only eval overstates quality. Expected ratio: 2–5x (i.e., rd_val_score in range 150–400).

If `rd_val_score` is near 0 or negative, debug by checking:
```bash
python3 -c "
import autoklb_realdata as rd, pandas as pd
df_1m = rd.load_1m('SPY')
daily_atr_s = rd.load_daily_atr('SPY')
daily_atr_map = {pd.Timestamp(dt): v for dt, v in daily_atr_s.items() if not pd.isna(v)}
df_5m_ind = rd.compute_indicators(rd.resample_5m(df_1m))
levels_db = pd.read_parquet(rd.LEVELS_PATH)
levels_db['date'] = pd.to_datetime(levels_db['date'])
fired = rd.emit_signals('SPY', df_5m_ind, levels_db[levels_db.symbol=='SPY'], daily_atr_map)
print(len(fired), 'SPY signals before MFE/MAE')
"
```

- [ ] **Step 3: Update results.tsv with dual-eval baseline row**

Append a new baseline row with all 8 score columns.

- [ ] **Step 4: Commit**

```bash
git add debug/autoklb_results.tsv
git commit -m "autoklb: dual-eval baseline recorded — rd_val_score is new optimization target"
```
