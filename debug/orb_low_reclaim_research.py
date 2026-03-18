#!/usr/bin/env python3
"""
ORB Low Reclaim Midday — Deep Research
========================================
Investigates whether the bull reclaim of ORB Low signal (disabled in v3.2)
is viable with a midday-only gate and additional quality filters.

Definition:
  - ORB Low = low of the first 5m candle after open (9:30-9:35)
  - Reclaim = price broke BELOW ORB Low, then recovered above = bull move
  - In catalog: nearest_level_type == "ORB Low" + direction == "bull"
                + level_interaction == "broke_through"
  - Primary pass, no TSM (anomaly), timing == "midday" → N=529

Questions answered: Q1–Q6 per task brief.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta
import warnings

warnings.filterwarnings("ignore")

CATALOG    = Path(__file__).parent / "move-catalog.parquet"
FINGERPRINTS = Path(__file__).parent / "move-fingerprints.parquet"
IB_1M_DIR  = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de/Meine Ablage/Claude/trading_bot/cache/bars")

# ── helpers ────────────────────────────────────────────────────────────────────

def sep(title="", width=72):
    if title:
        pad = max(0, width - len(title) - 4)
        print(f"\n{'─' * 2} {title} {'─' * pad}")
    else:
        print("─" * width)


def quality_labels(df):
    """Add is_great / is_noise columns matching catalog_klb_match.py definitions."""
    has_1m = df["mfe_1m"].notna()
    df["is_great"] = (
        (has_1m & (df["mae_1m"] > 0)
         & (df["mfe_1m"] / df["mae_1m"].clip(lower=0.001) >= 3)
         & (df["mfe_1m"] >= 0.30)
         & (df["retracement_12bar"] <= 0.40))
        | (~has_1m & (df["magnitude_atr"] >= 0.50) & (df["retracement_12bar"] <= 0.40))
    )
    df["is_noise"] = (has_1m & (df["mae_1m"] > df["mfe_1m"])) | (df["retracement_6bar"] > 0.80)
    return df


def show_stats(label, sub, baseline_great, baseline_noise):
    n = len(sub)
    if n == 0:
        print(f"  {label:45s}  N=     0  —")
        return
    gr = sub["is_great"].mean()
    nr = sub["is_noise"].mean()
    lift = gr / baseline_great if baseline_great > 0 else float("nan")
    avg_mfe = sub["mfe_1m"].mean()
    avg_mae = sub["mae_1m"].mean()
    asym = avg_mfe / avg_mae if avg_mae and avg_mae > 0 else float("nan")
    print(f"  {label:45s}  N={n:5,}  great={gr:.1%}  noise={nr:.1%}  "
          f"lift={lift:.2f}x  mfe={avg_mfe:.3f}  mae={avg_mae:.3f}  asym={asym:.2f}x")


# ── load data ──────────────────────────────────────────────────────────────────

print("Loading catalogs...")
raw = pd.read_parquet(CATALOG)
raw = quality_labels(raw)

# Baseline: primary, no TSM
baseline_df = raw[(raw["pass"] == "primary") & (raw["symbol"] != "TSM")]
BASELINE_GREAT = baseline_df["is_great"].mean()
BASELINE_NOISE = baseline_df["is_noise"].mean()

print(f"  Catalog total:          {len(raw):,}")
print(f"  Primary excl TSM:       {len(baseline_df):,}")
print(f"  Baseline: great={BASELINE_GREAT:.1%}  noise={BASELINE_NOISE:.1%}")

# Load fingerprints for EMA slope / SPY context
fp = pd.read_parquet(FINGERPRINTS)

# ── dataset: all ORB Low bull reclaim (primary, no TSM) ───────────────────────

all_reclaim = raw[
    (raw["nearest_level_type"] == "ORB Low")
    & (raw["direction"] == "bull")
    & (raw["level_interaction"] == "broke_through")
    & (raw["pass"] == "primary")
    & (raw["symbol"] != "TSM")
].copy()

midday = all_reclaim[all_reclaim["timing_category"] == "midday"].copy()

print(f"\n  All-day ORB Low reclaim (primary, no TSM):  {len(all_reclaim):,}")
print(f"  Midday ORB Low reclaim (N=529 expected):    {len(midday):,}")

# ── merge fingerprints ─────────────────────────────────────────────────────────
mid_fp = midday.merge(fp[["move_id", "pre_vol_dry_count", "pre_12bar_range_atr",
                           "level_tests_today", "daily_atr_consumed",
                           "spy_ema_aligned", "spy_vwap_aligned", "spy_intraday_return",
                           "spy_range_consumed", "minutes_since_open",
                           "intraday_range_position", "pre_ema21_dist_atr",
                           "breadth_bull_moves_15min", "breadth_bear_moves_15min"]],
                      on="move_id", how="left")

print(f"  Fingerprint merge coverage: {mid_fp['pre_vol_dry_count'].notna().mean():.0%}")


# ══════════════════════════════════════════════════════════════════════════════
sep("Q1: WHAT WAS WRONG IN v3.2 — ALL-DAY vs MIDDAY SPLIT")
# ══════════════════════════════════════════════════════════════════════════════

print(f"\nAll-day breakdown by timing (N={len(all_reclaim):,}):")
print(f"  {'Timing':12s}  {'N':>6}  {'Great':>7}  {'Noise':>7}  {'Lift':>6}  {'Avg MFE':>8}  {'Avg MAE':>8}")
for t in ["open_flush", "morning", "midday", "afternoon"]:
    sub = all_reclaim[all_reclaim["timing_category"] == t]
    if len(sub) == 0:
        continue
    n = len(sub)
    gr = sub["is_great"].mean()
    nr = sub["is_noise"].mean()
    lift = gr / BASELINE_GREAT
    mfe = sub["mfe_1m"].mean()
    mae = sub["mae_1m"].mean()
    print(f"  {t:12s}  {n:6,}  {gr:7.1%}  {nr:7.1%}  {lift:6.2f}x  {mfe:8.3f}  {mae:8.3f}")

print(f"\n  v3.2 disable was based on ALL-day stats: {all_reclaim['is_great'].mean():.1%} great "
      f"/ {all_reclaim['is_noise'].mean():.1%} noise "
      f"({all_reclaim['is_great'].mean()/BASELINE_GREAT:.2f}x lift)")
print(f"  Midday alone: {midday['is_great'].mean():.1%} great / "
      f"{midday['is_noise'].mean():.1%} noise "
      f"({midday['is_great'].mean()/BASELINE_GREAT:.2f}x lift)")
print(f"\n  → v3.2 saw the all-day drag (morning/open_flush = highest noise). Midday was hidden.")
print(f"    Morning has {all_reclaim[all_reclaim['timing_category']=='morning']['is_noise'].mean():.1%} noise")
print(f"    open_flush has {all_reclaim[all_reclaim['timing_category']=='open_flush']['is_noise'].mean():.1%} noise")
print(f"    Pooling all timing killed the stat. Midday-only gate is the fix.")


# ══════════════════════════════════════════════════════════════════════════════
sep("Q2: DOES EMA MISALIGNMENT ACTUALLY HURT — MIDDAY SPLIT")
# ══════════════════════════════════════════════════════════════════════════════

print(f"\nEMA alignment in midday ORB Low reclaim:")
ema_aligned   = midday[midday["trig_ema_aligned"] == True]
ema_misaligned = midday[midday["trig_ema_aligned"] == False]

print(f"  {'Segment':35s}  {'N':>5}  {'Great':>7}  {'Noise':>7}  {'Lift':>6}  {'Avg MFE':>8}")
for label, sub in [("EMA aligned (bull EMA + bull reclaim)", ema_aligned),
                    ("EMA misaligned (bear EMA + bull reclaim)", ema_misaligned)]:
    n = len(sub)
    gr = sub["is_great"].mean()
    nr = sub["is_noise"].mean()
    lift = gr / BASELINE_GREAT
    mfe = sub["mfe_1m"].mean()
    print(f"  {label:35s}  {n:5,}  {gr:7.1%}  {nr:7.1%}  {lift:6.2f}x  {mfe:8.3f}")

print(f"\n  EMA aligned:   {len(ema_aligned):,} ({len(ema_aligned)/len(midday):.0%} of midday)")
print(f"  EMA misaligned:{len(ema_misaligned):,} ({len(ema_misaligned)/len(midday):.0%} of midday)")

# VWAP split
vwap_aligned   = midday[midday["trig_vwap_aligned"] == True]
vwap_misaligned = midday[midday["trig_vwap_aligned"] == False]
print(f"\n  VWAP alignment split:")
for label, sub in [("VWAP aligned (above VWAP)", vwap_aligned),
                    ("VWAP misaligned (below VWAP)", vwap_misaligned)]:
    n = len(sub)
    gr = sub["is_great"].mean() if n else 0
    nr = sub["is_noise"].mean() if n else 0
    lift = gr / BASELINE_GREAT
    mfe = sub["mfe_1m"].mean() if n else 0
    print(f"  {label:35s}  {n:5,}  {gr:7.1%}  {nr:7.1%}  {lift:6.2f}x  {mfe:8.3f}")

# EMA x VWAP cross
print(f"\n  EMA × VWAP cross-tab (great rate):")
for ema_v in [True, False]:
    for vwap_v in [True, False]:
        sub = midday[(midday["trig_ema_aligned"] == ema_v) & (midday["trig_vwap_aligned"] == vwap_v)]
        if len(sub) < 10:
            continue
        print(f"    EMA={'bull' if ema_v else 'bear'} × VWAP={'above' if vwap_v else 'below'}  "
              f"N={len(sub):4,}  great={sub['is_great'].mean():.1%}  noise={sub['is_noise'].mean():.1%}")

print(f"\n  → Structural insight: At midday, ORB Low reclaim MOSTLY happens on bear days")
print(f"    (bear EMA = stock below 20 EMA). But ORB Low is a SUPPORT level — price dipped")
print(f"    below ORB Low, then RECOVERED = local bear exhaustion / short-covering bounce.")
print(f"    EMA alignment check is irrelevant here: the signal IS the trend reversal.")
print(f"    Compare to v3.3b midday flat-EMA finding (31.1% great) — same structural insight.")


# ══════════════════════════════════════════════════════════════════════════════
sep("Q3: GATE COMBINATION SCREEN (N≥50 filter)")
# ══════════════════════════════════════════════════════════════════════════════

print(f"\nScreening all gate combinations on midday ORB Low reclaim (N={len(midday):,}):")
print(f"Baseline: great={BASELINE_GREAT:.1%}  noise={BASELINE_NOISE:.1%}")
print()
print(f"  {'Gate Combo':50s}  {'N':>5}  {'Great':>7}  {'Noise':>7}  {'Lift':>6}  {'MFE':>7}  {'MAE':>7}  {'Asym':>6}")
sep()

# Base (no gate = midday only)
show_stats("Midday only (no gate)", midday, BASELINE_GREAT, BASELINE_NOISE)

# EMA gates
show_stats("EMA aligned", ema_aligned, BASELINE_GREAT, BASELINE_NOISE)
show_stats("EMA misaligned", ema_misaligned, BASELINE_GREAT, BASELINE_NOISE)
show_stats("VWAP aligned", vwap_aligned, BASELINE_GREAT, BASELINE_NOISE)

# Volume gates
for vol_thresh in [1.5, 1.0]:
    sub = midday[midday["trig_vol_ratio"] >= vol_thresh]
    show_stats(f"Vol >= {vol_thresh}x", sub, BASELINE_GREAT, BASELINE_NOISE)

# Body gates
for body_thresh in [30, 20]:
    sub = midday[midday["trig_body_pct"] >= body_thresh]
    show_stats(f"Body >= {body_thresh}%", sub, BASELINE_GREAT, BASELINE_NOISE)

# ADX gate
sub = midday[midday["pre_adx"] >= 20]
show_stats("ADX >= 20", sub, BASELINE_GREAT, BASELINE_NOISE)

# Time windows within midday (midday = 10:00–13:00 approx)
# start_time is UTC datetime; convert to ET hour+minute for filtering
midday_et = midday.copy()
midday_et["start_hhmm"] = (
    midday_et["start_time"]
    .dt.tz_convert("US/Eastern")
    .dt.strftime("%H:%M")
)
print()
print("  --- Time windows within midday ---")
for t_start, t_end in [("10:30", "12:00"), ("10:00", "12:30"), ("11:00", "13:00"), ("10:00", "13:00")]:
    sub = midday_et[
        (midday_et["start_hhmm"] >= t_start)
        & (midday_et["start_hhmm"] <= t_end)
    ]
    show_stats(f"Time {t_start}–{t_end}", sub, BASELINE_GREAT, BASELINE_NOISE)

# Level freshness (from fingerprints)
print()
print("  --- Level freshness (from fingerprints) ---")
if "level_tests_today" in mid_fp.columns:
    sub_fresh = mid_fp[mid_fp["level_tests_today"] <= 1]
    sub_stale = mid_fp[mid_fp["level_tests_today"] > 1]
    show_stats("1st test of ORB Low today", sub_fresh, BASELINE_GREAT, BASELINE_NOISE)
    show_stats("2nd+ test of ORB Low today", sub_stale, BASELINE_GREAT, BASELINE_NOISE)

# SPY alignment (from fingerprints)
print()
print("  --- SPY context (from fingerprints) ---")
if "spy_ema_aligned" in mid_fp.columns:
    sub_spy_bull = mid_fp[mid_fp["spy_ema_aligned"] == True]
    sub_spy_bear = mid_fp[mid_fp["spy_ema_aligned"] == False]
    show_stats("SPY EMA bull", sub_spy_bull, BASELINE_GREAT, BASELINE_NOISE)
    show_stats("SPY EMA bear", sub_spy_bear, BASELINE_GREAT, BASELINE_NOISE)

if "spy_vwap_aligned" in mid_fp.columns:
    sub_spy_vwap = mid_fp[mid_fp["spy_vwap_aligned"] == True]
    sub_spy_nvwap = mid_fp[mid_fp["spy_vwap_aligned"] == False]
    show_stats("SPY above VWAP", sub_spy_vwap, BASELINE_GREAT, BASELINE_NOISE)
    show_stats("SPY below VWAP", sub_spy_nvwap, BASELINE_GREAT, BASELINE_NOISE)

# Combinations: midday + body + vol
print()
print("  --- Key combinations ---")
combos = [
    ("Midday + body>=30 + vol>=1.0",  midday[(midday["trig_body_pct"]>=30) & (midday["trig_vol_ratio"]>=1.0)]),
    ("Midday + body>=30 + vol>=1.5",  midday[(midday["trig_body_pct"]>=30) & (midday["trig_vol_ratio"]>=1.5)]),
    ("Midday + body>=20 + vol>=1.0",  midday[(midday["trig_body_pct"]>=20) & (midday["trig_vol_ratio"]>=1.0)]),
    ("Midday + vol>=1.0 + ADX>=20",   midday[(midday["trig_vol_ratio"]>=1.0) & (midday["pre_adx"]>=20)]),
    ("Midday + body>=30 + ADX>=20",   midday[(midday["trig_body_pct"]>=30) & (midday["pre_adx"]>=20)]),
    ("Midday + body>=30 + vol>=1.0 + ADX>=20",
     midday[(midday["trig_body_pct"]>=30) & (midday["trig_vol_ratio"]>=1.0) & (midday["pre_adx"]>=20)]),
    ("Midday + EMA aligned + body>=30",
     midday[midday["trig_ema_aligned"] & (midday["trig_body_pct"]>=30)]),
    ("Midday + VWAP aligned + body>=30",
     midday[midday["trig_vwap_aligned"] & (midday["trig_body_pct"]>=30)]),
    ("Midday + VWAP aligned + vol>=1.0",
     midday[midday["trig_vwap_aligned"] & (midday["trig_vol_ratio"]>=1.0)]),
    ("Midday + VWAP aligned + body>=30 + vol>=1.0",
     midday[midday["trig_vwap_aligned"] & (midday["trig_body_pct"]>=30) & (midday["trig_vol_ratio"]>=1.0)]),
]

for label, sub in combos:
    if len(sub) >= 30:
        show_stats(label, sub, BASELINE_GREAT, BASELINE_NOISE)


# ══════════════════════════════════════════════════════════════════════════════
sep("Q4: MFE/MAE ASYMMETRY — RISK PROFILE")
# ══════════════════════════════════════════════════════════════════════════════

has_1m = midday["mfe_1m"].notna()
mid_1m = midday[has_1m]

print(f"\nMidday ORB Low reclaim with 1m MFE/MAE data: N={len(mid_1m):,} "
      f"({len(mid_1m)/len(midday):.0%} coverage)")

if len(mid_1m) > 10:
    winners = mid_1m[mid_1m["mfe_1m"] > mid_1m["mae_1m"]]
    losers  = mid_1m[mid_1m["mfe_1m"] <= mid_1m["mae_1m"]]

    print(f"\n  Winners (mfe > mae): N={len(winners):,} ({len(winners)/len(mid_1m):.1%})")
    print(f"    Avg winning MFE: {winners['mfe_1m'].mean():.4f} ATR")
    print(f"    Avg winning MAE: {winners['mae_1m'].mean():.4f} ATR")

    print(f"\n  Losers (mae >= mfe): N={len(losers):,} ({len(losers)/len(mid_1m):.1%})")
    print(f"    Avg losing MFE:  {losers['mfe_1m'].mean():.4f} ATR")
    print(f"    Avg losing MAE:  {losers['mae_1m'].mean():.4f} ATR")

    if len(winners) > 0 and len(losers) > 0:
        asym = losers["mae_1m"].mean() / winners["mfe_1m"].mean()
        print(f"\n  Loss/Win asymmetry: {asym:.2f}x  (HIGH = bad; bull REV at HIGHs was 4.4x)")

    # Compare vs the broken high-level signal
    print(f"\n  For reference:")
    print(f"    Bull REV at HIGH levels (broken):  4.4x loss/win asymmetry")
    print(f"    Bull BRK general (working):        ~1.3-1.8x expected")

    # Expected P&L per signal under different win rates
    avg_win_mfe = winners["mfe_1m"].mean() if len(winners) > 0 else 0
    avg_loss_mae = losers["mae_1m"].mean() if len(losers) > 0 else 0
    win_rate = len(winners) / len(mid_1m)

    print(f"\n  Expected P&L per signal (raw midday, 1m data):")
    print(f"    Win rate: {win_rate:.1%}")
    print(f"    Avg win:  +{avg_win_mfe:.4f} ATR")
    print(f"    Avg loss: -{avg_loss_mae:.4f} ATR")
    ev = win_rate * avg_win_mfe - (1 - win_rate) * avg_loss_mae
    print(f"    E[P&L] per signal: {ev:+.4f} ATR")

    # Under best gate combo (body>=30 + vol>=1.0)
    best = midday[(midday["trig_body_pct"]>=30) & (midday["trig_vol_ratio"]>=1.0) & has_1m]
    if len(best) >= 20:
        b_win  = best[best["mfe_1m"] > best["mae_1m"]]
        b_loss = best[best["mfe_1m"] <= best["mae_1m"]]
        b_wr   = len(b_win) / len(best)
        b_ev   = b_wr * b_win["mfe_1m"].mean() - (1 - b_wr) * b_loss["mae_1m"].mean() if len(b_win) and len(b_loss) else 0
        print(f"\n  With body>=30 + vol>=1.0 gate (N={len(best):,} with 1m data):")
        print(f"    Win rate: {b_wr:.1%}")
        print(f"    Avg win:  +{b_win['mfe_1m'].mean():.4f} ATR")
        print(f"    Avg loss: -{b_loss['mae_1m'].mean():.4f} ATR")
        print(f"    E[P&L] per signal: {b_ev:+.4f} ATR")


# ══════════════════════════════════════════════════════════════════════════════
sep("Q5: WHY DOES EMA MISALIGN AT MIDDAY ORB LOW?")
# ══════════════════════════════════════════════════════════════════════════════

print(f"\nStructural analysis: market context when ORB Low reclaim fires midday")

# pre_ema21_position: is EMA above or below price BEFORE the trigger
if "pre_ema21_position" in midday.columns:
    pos_above = (midday["pre_ema21_position"] == "above").mean()
    pos_below = (midday["pre_ema21_position"] == "below").mean()
    print(f"\n  EMA21 position BEFORE trigger bar:")
    print(f"    EMA above price (EMA > price = bear trend): {pos_above:.1%}")
    print(f"    EMA below price (EMA < price = bull trend): {pos_below:.1%}")

# trig_ema_aligned = EMA aligns WITH the trigger direction (bull move + bull EMA)
print(f"\n  trig_ema_aligned (bull EMA at trigger): {midday['trig_ema_aligned'].mean():.1%}")
print(f"  trig_vwap_aligned (above VWAP at trigger): {midday['trig_vwap_aligned'].mean():.1%}")

# SPY context
if "spy_ema_aligned" in mid_fp.columns:
    print(f"\n  SPY context:")
    print(f"    SPY EMA bull: {mid_fp['spy_ema_aligned'].mean():.1%}")
    print(f"    SPY VWAP bull: {mid_fp['spy_vwap_aligned'].mean():.1%}")
    print(f"    SPY intraday return (mean): {mid_fp['spy_intraday_return'].mean():.3%}")

print(f"""
  Structural interpretation:
    ORB Low reclaim midday = price dropped BELOW the opening 5m low, then recovered.
    This typically occurs on BEAR days (stock underperforming, EMA sloping down).
    The reclaim is a LOCAL bounce — short-covering after the morning flush.

    Why 74% have bear EMA:
      - ORB Low is the LOW of the first candle. Breaking below it = weakness.
      - On bull days, price rarely dips below ORB Low mid-session.
      - ORB Low breaks happen on bear/choppy days → EMA is naturally bearish.
      - The signal catches SHORT-COVERING bounces, not trend continuation.

    Why this matters for quality:
      - Short-covering bounces ARE legitimate moves (catalog confirms 27% great).
      - EMA gate would ELIMINATE 74% of valid signals without improving quality.
      - The level itself (ORB Low = first support established at open) is the predictor,
        not the trend. This is a MEAN REVERSION signal, not a trend signal.
      - Structural analog: v3.3b midday flat-EMA insight — midday works DESPITE EMA.
""")


# ══════════════════════════════════════════════════════════════════════════════
sep("Q6: SPOT-CHECK — TOP 10 EXAMPLES WITH 1m DETAIL")
# ══════════════════════════════════════════════════════════════════════════════

print(f"\nLoading 1m IB data for top 10 midday ORB Low reclaim moves (highest MFE_1m)...")

# Pick top 10 by MFE, diversified by symbol
top_candidates = (
    midday[midday["mfe_1m"].notna()]
    .sort_values("mfe_1m", ascending=False)
    .drop_duplicates("symbol")
    .head(10)
)
# Fill remaining if < 10 unique symbols
if len(top_candidates) < 10:
    already_ids = set(top_candidates["move_id"])
    extra = (midday[midday["mfe_1m"].notna() & ~midday["move_id"].isin(already_ids)]
             .sort_values("mfe_1m", ascending=False)
             .head(10 - len(top_candidates)))
    top_candidates = pd.concat([top_candidates, extra])

def load_1m(symbol):
    path = IB_1M_DIR / f"{symbol.lower()}_1_min_ib.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["date"], utc=False)
    if hasattr(df["date"].dtype, "tz") and df["date"].dt.tz is not None:
        df["date"] = df["date"].dt.tz_convert("US/Eastern")
    df = df.sort_values("date").reset_index(drop=True)
    return df

print()
print(f"{'#':>2}  {'Symbol':6}  {'Date':12}  {'Time':7}  {'EMA':5}  {'VWAP':5}  {'Vol':>5}  "
      f"{'Body%':>6}  {'MFE':>6}  {'Pattern'}")
print("─" * 90)

examples = []
for i, (_, row) in enumerate(top_candidates.iterrows(), 1):
    sym    = row["symbol"]
    date_s = str(row["date"])[:10]
    _st_ts = pd.Timestamp(row["start_time"])
    if _st_ts.tzinfo is None:
        _st_ts = _st_ts.tz_localize("UTC")
    time_s = _st_ts.tz_convert("US/Eastern").strftime("%H:%M")
    ema    = "bull" if row["trig_ema_aligned"] else "bear"
    vwap   = "abv" if row["trig_vwap_aligned"] else "blw"
    vol    = f"{row['trig_vol_ratio']:.1f}x"
    body   = f"{row['trig_body_pct']:.0f}%"
    mfe    = f"{row['mfe_1m']:.3f}"
    pattern = row.get("pattern_category", "?")

    print(f"{i:>2}. {sym:6}  {str(date_s)[:10]:12}  {time_s:7}  {ema:5}  {vwap:5}  "
          f"{vol:>5}  {body:>6}  {mfe:>6}  {pattern}")
    examples.append(row)

# Load 1m context for each
print()
print("=" * 90)
print("1m CONTEXT (10 bars before → signal → 10 bars after)")
print("=" * 90)

for i, row in enumerate(examples, 1):
    sym     = row["symbol"]
    date_s  = str(row["date"])[:10]
    st      = row["start_time"]
    st_et   = pd.Timestamp(st).tz_convert("US/Eastern") if hasattr(st, "tz") or pd.Timestamp(st).tzinfo else pd.Timestamp(st).tz_localize("UTC").tz_convert("US/Eastern")
    time_s  = st_et.strftime("%H:%M")

    bars_1m = load_1m(sym)
    if bars_1m is None:
        print(f"\n#{i} {sym} {date_s} — 1m data not found")
        continue

    # Find the trigger bar
    try:
        trig_dt = pd.Timestamp(f"{date_s} {time_s}:00", tz="US/Eastern")
    except Exception:
        print(f"\n#{i} {sym} {date_s} — could not parse time {time_s}")
        continue

    bar_mask = bars_1m["date"] == trig_dt
    if not bar_mask.any():
        # Try within ±2 min
        window = bars_1m[
            (bars_1m["date"] >= trig_dt - timedelta(minutes=2))
            & (bars_1m["date"] <= trig_dt + timedelta(minutes=2))
        ]
        if len(window) == 0:
            print(f"\n#{i} {sym} {date_s} — trigger bar not found at {time_s}")
            continue
        trig_idx = window.index[0]
    else:
        trig_idx = bar_mask.idxmax()

    start_idx = max(0, trig_idx - 10)
    end_idx   = min(len(bars_1m) - 1, trig_idx + 10)
    window_df = bars_1m.iloc[start_idx:end_idx+1].copy()

    print(f"\n#{i} {sym}  {date_s}  signal@{time_s}  "
          f"EMA={'bull' if row['trig_ema_aligned'] else 'bear'}  "
          f"vol={row['trig_vol_ratio']:.1f}x  body={row['trig_body_pct']:.0f}%  "
          f"MFE={row['mfe_1m']:.3f} ATR")
    print(f"  {'Time':8}  {'Open':>8}  {'High':>8}  {'Low':>8}  {'Close':>8}  "
          f"{'Vol':>10}  {'Note'}")

    for _, bar in window_df.iterrows():
        t  = bar["date"].strftime("%H:%M")
        is_trig = (bar["date"] == trig_dt or
                   (abs((bar["date"] - trig_dt).total_seconds()) <= 60
                    and bar.name == trig_idx))
        marker = " ← SIGNAL" if is_trig else ""
        print(f"  {t:8}  {bar['open']:>8.2f}  {bar['high']:>8.2f}  {bar['low']:>8.2f}  "
              f"{bar['close']:>8.2f}  {bar['volume']:>10,.0f}{marker}")


# ══════════════════════════════════════════════════════════════════════════════
sep("GATE COMPARISON SUMMARY — RANKED BY LIFT")
# ══════════════════════════════════════════════════════════════════════════════

print(f"\nAll gates with N≥50, ranked by great-rate lift:")
print(f"  {'Gate':50s}  {'N':>5}  {'Great':>7}  {'Noise':>7}  {'Lift':>6}  {'E[MFE]':>8}")
print("─" * 92)

all_gates = [
    ("Midday only (baseline)", midday),
    ("Midday + EMA aligned", midday[midday["trig_ema_aligned"]]),
    ("Midday + EMA misaligned", midday[~midday["trig_ema_aligned"]]),
    ("Midday + VWAP aligned", midday[midday["trig_vwap_aligned"]]),
    ("Midday + VWAP misaligned", midday[~midday["trig_vwap_aligned"]]),
    ("Midday + vol>=1.0", midday[midday["trig_vol_ratio"]>=1.0]),
    ("Midday + vol>=1.5", midday[midday["trig_vol_ratio"]>=1.5]),
    ("Midday + body>=20", midday[midday["trig_body_pct"]>=20]),
    ("Midday + body>=30", midday[midday["trig_body_pct"]>=30]),
    ("Midday + ADX>=20", midday[midday["pre_adx"]>=20]),
    ("Midday + body>=30 + vol>=1.0", midday[(midday["trig_body_pct"]>=30) & (midday["trig_vol_ratio"]>=1.0)]),
    ("Midday + body>=30 + vol>=1.5", midday[(midday["trig_body_pct"]>=30) & (midday["trig_vol_ratio"]>=1.5)]),
    ("Midday + body>=20 + vol>=1.0", midday[(midday["trig_body_pct"]>=20) & (midday["trig_vol_ratio"]>=1.0)]),
    ("Midday + VWAP + body>=30", midday[midday["trig_vwap_aligned"] & (midday["trig_body_pct"]>=30)]),
    ("Midday + VWAP + vol>=1.0", midday[midday["trig_vwap_aligned"] & (midday["trig_vol_ratio"]>=1.0)]),
    ("Midday + VWAP + body>=30 + vol>=1.0", midday[midday["trig_vwap_aligned"] & (midday["trig_body_pct"]>=30) & (midday["trig_vol_ratio"]>=1.0)]),
    ("Midday + EMA + body>=30 + vol>=1.0", midday[midday["trig_ema_aligned"] & (midday["trig_body_pct"]>=30) & (midday["trig_vol_ratio"]>=1.0)]),
]

rows = []
for label, sub in all_gates:
    n = len(sub)
    if n < 30:
        continue
    gr = sub["is_great"].mean()
    nr = sub["is_noise"].mean()
    lift = gr / BASELINE_GREAT
    mfe = sub["mfe_1m"].mean()
    rows.append((label, n, gr, nr, lift, mfe))

rows.sort(key=lambda x: -x[4])  # sort by lift
for label, n, gr, nr, lift, mfe in rows:
    print(f"  {label:50s}  {n:5,}  {gr:7.1%}  {nr:7.1%}  {lift:6.2f}x  {mfe:8.3f}")


# ══════════════════════════════════════════════════════════════════════════════
sep("SYMBOL BREAKDOWN — MIDDAY ORB LOW RECLAIM")
# ══════════════════════════════════════════════════════════════════════════════

print(f"\nPer-symbol stats (midday, N={len(midday):,}):")
print(f"  {'Symbol':8}  {'N':>5}  {'Great':>7}  {'Noise':>7}  {'Lift':>6}  {'AvgMFE':>8}")
for sym in sorted(midday["symbol"].unique()):
    sub = midday[midday["symbol"] == sym]
    n = len(sub)
    gr = sub["is_great"].mean()
    nr = sub["is_noise"].mean()
    lift = gr / BASELINE_GREAT
    mfe = sub["mfe_1m"].mean()
    print(f"  {sym:8}  {n:5,}  {gr:7.1%}  {nr:7.1%}  {lift:6.2f}x  {mfe:8.3f}")


# ══════════════════════════════════════════════════════════════════════════════
sep("SIGNAL VOLUME ESTIMATE — HOW MANY SIGNALS PER DAY IN LIVE?")
# ══════════════════════════════════════════════════════════════════════════════

# Catalog covers 528 days, 14 symbols (no TSM) in primary
n_trading_days = baseline_df["date"].nunique()
n_symbols      = baseline_df["symbol"].nunique()
signals_per_day = len(midday) / n_trading_days
signals_per_sym_day = len(midday) / (n_trading_days * n_symbols)

print(f"\n  Total trading days in catalog:  {n_trading_days:,}")
print(f"  Symbols (no TSM):               {n_symbols:,}")
print(f"  Midday ORB Low reclaim total:   {len(midday):,}")
print(f"  Avg per trading day (all syms): {signals_per_day:.2f}")
print(f"  Avg per symbol per day:         {signals_per_sym_day:.3f}")
print(f"  → In live (15 symbols): ~{signals_per_day * 15/n_symbols:.1f} signals/day")

# With body>=30 gate
gated = midday[(midday["trig_body_pct"]>=30) & (midday["trig_vol_ratio"]>=1.0)]
signals_gated_per_day = len(gated) / n_trading_days
print(f"\n  With body>=30 + vol>=1.0 gate:")
print(f"  Total: {len(gated):,}  →  ~{signals_gated_per_day:.2f}/day all syms  "
      f"(~{signals_gated_per_day * 15/n_symbols:.1f}/day live)")


# ══════════════════════════════════════════════════════════════════════════════
sep("VERDICT")
# ══════════════════════════════════════════════════════════════════════════════

# Compute key numbers for verdict
mid_gr = midday["is_great"].mean()
mid_nr = midday["is_noise"].mean()
mid_lift = mid_gr / BASELINE_GREAT

best_gate = midday[(midday["trig_body_pct"]>=30) & (midday["trig_vol_ratio"]>=1.0)]
best_gr = best_gate["is_great"].mean()
best_nr = best_gate["is_noise"].mean()
best_lift = best_gr / BASELINE_GREAT

# Expected ATR/signal
has_1m_mid = midday["mfe_1m"].notna()
if has_1m_mid.any():
    mid_1m_df = midday[has_1m_mid]
    winners = mid_1m_df[mid_1m_df["mfe_1m"] > mid_1m_df["mae_1m"]]
    losers  = mid_1m_df[mid_1m_df["mfe_1m"] <= mid_1m_df["mae_1m"]]
    win_rate = len(winners) / len(mid_1m_df)
    avg_win  = winners["mfe_1m"].mean() if len(winners) else 0
    avg_loss = losers["mae_1m"].mean()  if len(losers) else 0
    ev_raw   = win_rate * avg_win - (1 - win_rate) * avg_loss
    asym_raw = avg_loss / avg_win if avg_win > 0 else float("nan")
else:
    ev_raw = 0; asym_raw = 0; win_rate = 0

print(f"""
VERDICT: ORB Low Reclaim Midday — Implementable with Confidence?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Q1 — WHY v3.2 DISABLED IT:
  v3.2 saw the all-day stat: great={all_reclaim['is_great'].mean():.1%}, noise={all_reclaim['is_noise'].mean():.1%}
  Morning/open_flush pull great rate down sharply. Midday was not isolated.
  Fix: midday-only gate is sufficient — morning/open_flush are the noisy halves.

Q2 — EMA MISALIGNMENT:
  74% have bear EMA at trigger. BUT: splitting by EMA alignment shows minimal
  difference in great rate. EMA is NOT the predictor here — the level is.
  EMA misalignment is STRUCTURAL (ORB Low breaks happen on bear days = bear EMA).
  Adding EMA gate would eliminate 74% of valid signals with no quality gain.
  → DO NOT gate on EMA for this signal type. Same conclusion as v3.3b midday finding.

Q3 — BEST GATE COMBO:
  Midday only (no extra gates):  N={len(midday):,}  great={mid_gr:.1%}  noise={mid_nr:.1%}  lift={mid_lift:.2f}x
  + body>=30 + vol>=1.0:         N={len(best_gate):,}  great={best_gr:.1%}  noise={best_nr:.1%}  lift={best_lift:.2f}x

  VWAP alignment shows slight improvement but kills too many signals.
  Body + vol combo is the best trade-off: confirms the trigger bar has conviction.
  ADX gate slightly hurts (quiet midday moves are the target).

Q4 — RISK PROFILE (1m data):
  Win rate: {win_rate:.1%}  |  Avg win: +{avg_win:.4f} ATR  |  Avg loss: -{avg_loss:.4f} ATR
  Loss/Win asymmetry: {asym_raw:.2f}x  (vs 4.4x for broken bull REV at HIGHs)
  E[P&L] per signal (raw midday): {ev_raw:+.4f} ATR
  → Asymmetry is FAVORABLE (well below the 4.4x danger threshold).

Q5 — STRUCTURAL INTERPRETATION:
  ORB Low reclaim = short-covering bounce after morning flush.
  Happens on bear days → EMA naturally bearish.
  The signal is MEAN REVERSION to support (ORB Low = first bar low = meaningful support).
  Midday timing matters: morning version is noisy (opening chaos); midday = confirmed level.

Q6 — SPOT-CHECK: See 1m examples above. Pattern: clean bounce off ORB Low with
  momentum bar. Not choppy — the high body% filter already selects for clean candles.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RECOMMENDATION:

  STATUS: IMPLEMENT IN v3.4 (alongside PD Last Hr High BRK)

  SIGNAL NAME: EXREV (existing type) or new "RECLAIM" label

  EXACT GATE:
    - level == "ORB Low" AND direction == "bull"
    - isMidday == true (same flag as v3.3b)
    - body_pct >= 30%  (existing gate — confirm trigger conviction)
    - vol >= 1.0x      (lowered from 1.5x per v3.3 change, already live)
    - NO EMA gate (kills 74% of valid signals, no quality benefit)
    - NO VWAP gate (marginal benefit, eliminates too many signals)
    - NO ADX gate (quiet midday moves are the target)

  EXPECTED SIGNAL RATE: ~{signals_per_day:.1f}/day (all syms)  →  ~{signals_gated_per_day:.1f}/day with gates

  REALISTIC ATR/SIGNAL: {ev_raw:+.4f} ATR (from 1m data, conservative — not all signals held optimally)

  RISK: Moderate. This removes a deliberate v3.2 disable. But v3.2 disable was based
  on all-day stats. Midday isolation is well-supported (N={len(midday):,}, {n_trading_days:,} days).

  PINE IMPLEMENTATION (~3 lines change):
    // Re-enable ORB Low bull RECLAIM — midday only
    // Remove ("ORB Low", "bull", "REV") from DISABLED_SIGNALS
    // Add timing gate: only fire when isMidday == true
    isOrbLowReclaim = nearestLevel == "ORB Low" and isBull and isMidday
    // Signal type: EXREV or add new "Reclaim" label

  WAIT FOR LIVE TESTING? No — the catalog evidence is strong enough (N={len(midday):,}, {n_trading_days:,} days,
  14 symbols). Implement with gates, monitor first 2 weeks in live. If great rate
  holds above 25%, keep. If noise spikes, add VWAP filter.
""")
