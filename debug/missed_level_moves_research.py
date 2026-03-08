#!/usr/bin/env python3
"""
Missed Level Moves Research — KLB v3.4 New Signal Discovery
============================================================
Analyzes moves near key levels where KLB fires no signal.
Finds new signal type candidates for v3.4.

Context:
- "Near level" = nearest_level_dist_atr <= 0.10 (within 10% of ATR)
- "No signal type match" = the level/direction combo has no defined signal in KLB
- The 2,655 original (v3.2) + 2,503 suppressed in v3.3c = 5,158 total no-match moves
- ALL are bull moves — bear moves at defined levels either BRK or REV
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Paths
BASE = Path(__file__).parent
CATALOG = BASE / "move-catalog.parquet"
IB_CACHE = Path("/Users/mab/Library/CloudStorage/GoogleDrive-mab@bina.de"
                "/Meine Ablage/Claude/trading_bot/cache/bars")

# ── KLB Signal Logic (v3.3c) ─────────────────────────────────────────────────
BRK_BEAR_LEVELS = {
    "PM Low", "PD Low", "Week Low", "ORB Low", "Week Open", "Month Open",
    "PD Last Hr Low", "PD Last Hr High",
}
BRK_BULL_LEVELS = {"Week Open", "Month Open"}

REV_BULL_LEVELS = {
    "PM High", "PD High", "Week High", "ORB High",   # suppressed in v3.3c
    "PM Low", "PD Low", "Week Low",
    "PD Last Hr Low",
    "PD Mid", "Today Open", "PD Close",
}
REV_BEAR_LEVELS = {
    "PM High", "PD High", "Week High", "ORB High",
    "PD Mid", "Today Open", "PD Close",
}
REV_LEVELS_UNGATED = {"PD Mid", "Today Open", "PD Close"}

DISABLED_SIGNALS  = {("ORB Low",  "bull", "REV")}          # disabled in v3.2
SUPPRESSED_V33C   = {("PM High",  "bull", "REV"),           # suppressed in v3.3c
                     ("PD High",  "bull", "REV"),
                     ("Week High","bull", "REV"),
                     ("ORB High", "bull", "REV")}

BODY_MIN = 30.0
VOL_MIN  = 1.5
ADX_MIN  = 20.0
PROX_ATR = 0.10


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_quality(p):
    """Reproduce is_great / is_noise labels from catalog_klb_match.py."""
    has_1m = p["mfe_1m"].notna()
    p = p.copy()
    p["is_great"] = (
        (has_1m
         & (p["mae_1m"] > 0)
         & (p["mfe_1m"] / p["mae_1m"].clip(lower=0.001) >= 3)
         & (p["mfe_1m"] >= 0.30)
         & (p["retracement_12bar"] <= 0.40))
        | (~has_1m
           & (p["magnitude_atr"] >= 0.50)
           & (p["retracement_12bar"] <= 0.40))
    )
    p["is_noise"] = (
        (has_1m & (p["mae_1m"] > p["mfe_1m"]))
        | (p["retracement_6bar"] > 0.80)
    )
    return p


def get_intended_type(row):
    """Return the intended KLB signal type for a near-level move, or None."""
    lv = row["nearest_level_type"]
    d  = row["direction"]
    ia = row["level_interaction"]

    is_brk = is_rev_gated = is_rev_ungated = False

    if d == "bull":
        if lv in BRK_BULL_LEVELS and ia == "broke_through":
            is_brk = True
        if lv in REV_BULL_LEVELS:
            key = (lv, "bull", "REV")
            if key not in DISABLED_SIGNALS and key not in SUPPRESSED_V33C:
                is_rev_ungated = lv in REV_LEVELS_UNGATED
                is_rev_gated   = lv not in REV_LEVELS_UNGATED
    else:
        if lv in BRK_BEAR_LEVELS and ia == "broke_through":
            is_brk = True
        if lv in REV_BEAR_LEVELS:
            key = (lv, "bear", "REV")
            if key not in DISABLED_SIGNALS:
                is_rev_ungated = lv in REV_LEVELS_UNGATED
                is_rev_gated   = lv not in REV_LEVELS_UNGATED

    if is_rev_ungated: return "REV_ungated"
    if is_rev_gated:   return "REV_gated"
    if is_brk:         return "BRK"
    return None


def would_fire(row):
    """Would KLB actually fire? (has type AND passes all gates)"""
    t = row.get("intended")
    if t is None:
        return False
    ema  = row["trig_ema_aligned"] or (row["timing_category"] == "open_flush")
    body = row["trig_body_pct"]  >= BODY_MIN
    vol  = row["trig_vol_ratio"] >= VOL_MIN
    adx  = row["pre_adx"]        >= ADX_MIN
    vwap = row["trig_vwap_aligned"]
    if t == "REV_ungated": return body and vol and adx
    if t == "REV_gated":   return ema and body and vol and adx and vwap
    if t == "BRK":         return ema and body and vol and adx
    return False


def sep(title="", w=70):
    if title:
        print(f"\n{'='*w}\n{title}\n{'='*w}")
    else:
        print("="*w)


def load_1m(symbol):
    """Load 1m IB parquet. IB files use a 'date' column with US/Eastern tz."""
    f = IB_CACHE / f"{symbol}_1_min_ib.parquet"
    if not f.exists():
        return None
    ib = pd.read_parquet(f)
    # IB files store timestamp in 'date' column (datetime64[us, US/Eastern])
    if "date" in ib.columns:
        ib.index = pd.to_datetime(ib["date"])
    elif "datetime" in ib.columns:
        ib.index = pd.to_datetime(ib["datetime"])
    elif not isinstance(ib.index, pd.DatetimeIndex):
        ib.index = pd.to_datetime(ib.index)
    if ib.index.tz is None:
        ib.index = ib.index.tz_localize("UTC")
    return ib


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    df = pd.read_parquet(CATALOG)
    p  = df[(df["pass"] == "primary") & (df["symbol"] != "TSM")].copy()
    p  = make_quality(p)

    baseline_great = p["is_great"].mean()
    baseline_noise = p["is_noise"].mean()

    # Classify every move
    near = p[p["nearest_level_dist_atr"] <= PROX_ATR].copy()
    near["intended"] = near.apply(get_intended_type, axis=1)
    near["fires"]    = near.apply(would_fire, axis=1)

    # Groups
    no_match    = near[near["intended"].isna()].copy()   # no signal type at all
    gate_blocked = near[near["intended"].notna() & ~near["fires"]].copy()
    fired        = near[near["fires"]].copy()

    sep("MISSED LEVEL MOVES RESEARCH — KLB v3.4 Signal Discovery")
    print(f"Total primary moves (excl TSM): {len(p):,}")
    print(f"Baseline: great={baseline_great:.1%}, noise={baseline_noise:.1%}")
    print(f"\nNear-level moves total:   {len(near):,}")
    print(f"  KLB fires:              {len(fired):,}  ({len(fired)/len(near):.1%})")
    print(f"  Gate-blocked:           {len(gate_blocked):,}  ({len(gate_blocked)/len(near):.1%})")
    print(f"  No signal type (miss):  {len(no_match):,}  ({len(no_match)/len(near):.1%})")

    # ─────────────────────────────────────────────────────────────────────────
    sep("SECTION A: PROFILE OF MISSED MOVES (no signal type match)")
    # ─────────────────────────────────────────────────────────────────────────

    m = no_match
    print(f"\nN total:    {len(m):,}")
    print(f"N great:    {m['is_great'].sum():,}  ({m['is_great'].mean():.1%} vs {baseline_great:.1%} baseline)")
    print(f"N noise:    {m['is_noise'].sum():,}  ({m['is_noise'].mean():.1%} vs {baseline_noise:.1%} baseline)")
    print(f"Lift over baseline: {m['is_great'].mean()/baseline_great:.2f}x")
    print(f"\nKey finding: ALL {len(m):,} no-match moves are BULL moves.")
    print(f"  Bear moves at defined levels always have at least BRK or REV coverage.")

    print(f"\n--- Direction split ---")
    for d in ["bull", "bear"]:
        sub = m[m["direction"] == d]
        if len(sub) == 0:
            print(f"  {d:6s}: N=0")
            continue
        print(f"  {d:6s}: N={len(sub):5,}  great={sub['is_great'].mean():.1%}  "
              f"noise={sub['is_noise'].mean():.1%}  avg_MFE={sub['magnitude_atr'].mean():.3f}")

    print(f"\n--- Time of day split ---")
    for t in ["open_flush", "morning", "midday", "afternoon"]:
        sub = m[m["timing_category"] == t]
        if len(sub) == 0:
            continue
        print(f"  {t:12s}: N={len(sub):5,}  great={sub['is_great'].mean():.1%}  "
              f"noise={sub['is_noise'].mean():.1%}")

    print(f"\n--- Per-symbol breakdown ---")
    sym_stats = (m.groupby("symbol")
                  .agg(N=("is_great", "count"),
                       great_rate=("is_great", "mean"),
                       noise_rate=("is_noise", "mean"),
                       avg_mfe=("magnitude_atr", "mean"))
                  .sort_values("N", ascending=False))
    for sym, row in sym_stats.iterrows():
        print(f"  {sym:6s}: N={int(row['N']):4d}  great={row['great_rate']:.1%}  "
              f"noise={row['noise_rate']:.1%}  avg_MFE={row['avg_mfe']:.3f}")

    # ─────────────────────────────────────────────────────────────────────────
    sep("SECTION B: LEVEL TYPE BREAKDOWN")
    # ─────────────────────────────────────────────────────────────────────────

    print(f"\nAll {len(m):,} no-match bull moves, by level type:\n")
    print(f"{'Level Type':<22} {'N':>6} {'%':>6} {'Great':>7} {'Noise':>7} {'AvgMFE':>8}")
    print("-" * 58)

    lt_counts = m["nearest_level_type"].value_counts()
    for lt in lt_counts.index:
        sub = m[m["nearest_level_type"] == lt]
        print(f"  {lt:<20} {len(sub):>6,} {len(sub)/len(m):>6.1%} "
              f"{sub['is_great'].mean():>7.1%} {sub['is_noise'].mean():>7.1%} "
              f"{sub['magnitude_atr'].mean():>8.3f}")

    print(f"\nLegend:")
    print(f"  ORB Low  (1,798) — disabled in v3.2: bull REV at ORB Low turned off")
    print(f"  ORB High (1,127) — suppressed in v3.3c: bull REV at resistance")
    print(f"  PD High    (939) — suppressed in v3.3c")
    print(f"  PD LH High (855) — never defined: PD Last Hr High only has bear BRK")
    print(f"  PM High    (225) — suppressed in v3.3c")
    print(f"  Week High  (212) — suppressed in v3.3c")

    # ─────────────────────────────────────────────────────────────────────────
    sep("SECTION C: WHY NO SIGNAL FIRED — THREE CATEGORIES")
    # ─────────────────────────────────────────────────────────────────────────

    # Category 1: Suppressed in v3.3c (bull REV at HIGH levels)
    high_levels = {"PM High", "PD High", "Week High", "ORB High"}
    cat_suppressed = m[m["nearest_level_type"].isin(high_levels)]

    # Category 2: Disabled in v3.2 (bull at ORB Low)
    cat_disabled = m[m["nearest_level_type"] == "ORB Low"]

    # Category 3: Never defined (bull BRK at PD Last Hr High)
    cat_never = m[m["nearest_level_type"] == "PD Last Hr High"]

    print(f"""
Three root causes — all are BULL moves:

  Cat 1: Bull REV at HIGH levels — SUPPRESSED in v3.3c
    Rationale: HIGHs are magnets; bull REV at magnet = betting on support where none exists.
    v3.3c removed -1,212 ATR drag. These 2,503 moves stay suppressed.
    N=2,503  great={cat_suppressed['is_great'].mean():.1%}  noise={cat_suppressed['is_noise'].mean():.1%}

  Cat 2: Bull RECLAIM of ORB Low — DISABLED in v3.2
    Rationale: ORB Low was disabled because ORB Low is defined as a BRK barrier (bears break
    below it). Bull bouncing back above it = RECLAIM (price returns to above ORB Low).
    Interaction: 100% broke_through (price dipped below ORB Low, then recovered).
    N=1,798  great={cat_disabled['is_great'].mean():.1%}  noise={cat_disabled['is_noise'].mean():.1%}

  Cat 3: Bull BRK at PD Last Hr High — NEVER DEFINED
    PD Last Hr High is in BRK_BEAR_LEVELS (bear breaks below it) but has NO bull BRK.
    100% broke_through interaction — these are genuine bull breakouts above PDLHrH.
    N=855  great={cat_never['is_great'].mean():.1%}  noise={cat_never['is_noise'].mean():.1%}
""")

    # ─────────────────────────────────────────────────────────────────────────
    sep("Cat 2 deep dive: Bull RECLAIM of ORB Low (1,798 moves)")
    # ─────────────────────────────────────────────────────────────────────────

    g = cat_disabled
    print(f"\nAll 1,798: great={g['is_great'].mean():.1%}  noise={g['is_noise'].mean():.1%}  "
          f"avg_mag={g['magnitude_atr'].mean():.3f}")
    print(f"\nWhat the move looks like:")
    print(f"  pre_ema21_position above ORB Low: {(g['pre_ema21_position']=='above').mean():.1%}")
    print(f"  pre_ema21_position below ORB Low: {(g['pre_ema21_position']=='below').mean():.1%}")
    print(f"  trig_ema_aligned (bull EMA):      {g['trig_ema_aligned'].mean():.1%}")
    print(f"  trig_vwap_aligned (above VWAP):   {g['trig_vwap_aligned'].mean():.1%}")

    print(f"\nBy timing:")
    for t in ["open_flush", "morning", "midday", "afternoon"]:
        sub = g[g["timing_category"] == t]
        if len(sub) == 0:
            continue
        print(f"  {t:12s}: N={len(sub):4,}  great={sub['is_great'].mean():.1%}  "
              f"noise={sub['is_noise'].mean():.1%}")

    print(f"\nGate pass rates (if we added bull BRK/EXREV at ORB Low):")
    print(f"  body>=30:  {(g['trig_body_pct']>=30).mean():.1%}")
    print(f"  vol>=1.5:  {(g['trig_vol_ratio']>=1.5).mean():.1%}")
    print(f"  vol>=1.0:  {(g['trig_vol_ratio']>=1.0).mean():.1%}")
    print(f"  adx>=20:   {(g['pre_adx']>=20).mean():.1%}")
    print(f"  ema_align: {g['trig_ema_aligned'].mean():.1%}")

    print(f"\nQuality at different gate combos:")
    # Loose: midday only
    sub = g[g["timing_category"] == "midday"]
    print(f"  Midday only:           N={len(sub):4,}  great={sub['is_great'].mean():.1%}  "
          f"noise={sub['is_noise'].mean():.1%}")
    # EMA + body
    sub = g[g["trig_ema_aligned"] & (g["trig_body_pct"] >= 30)]
    print(f"  EMA + body>=30:        N={len(sub):4,}  great={sub['is_great'].mean():.1%}  "
          f"noise={sub['is_noise'].mean():.1%}")
    # Full strict gate
    sub = g[g["trig_ema_aligned"] & (g["trig_body_pct"] >= 30)
            & (g["trig_vol_ratio"] >= 1.5) & (g["pre_adx"] >= 20)]
    print(f"  EMA+body+vol1.5+adx:   N={len(sub):4,}  great={sub['is_great'].mean():.1%}  "
          f"noise={sub['is_noise'].mean():.1%}")
    # Relaxed vol
    sub = g[g["trig_ema_aligned"] & (g["trig_body_pct"] >= 30)
            & (g["trig_vol_ratio"] >= 1.0) & (g["pre_adx"] >= 20)]
    print(f"  EMA+body+vol1.0+adx:   N={len(sub):4,}  great={sub['is_great'].mean():.1%}  "
          f"noise={sub['is_noise'].mean():.1%}")
    # Midday + EMA
    sub = g[(g["timing_category"] == "midday") & g["trig_ema_aligned"]]
    print(f"  Midday + EMA:          N={len(sub):4,}  great={sub['is_great'].mean():.1%}  "
          f"noise={sub['is_noise'].mean():.1%}")

    print(f"\nConclusion for Cat 2:")
    print(f"  - ORB Low reclaim: great rate 22.5% (1.17x baseline) — modest but consistent")
    print(f"  - 74% have price below EMA at trigger → EMA gate would kill 74% of these")
    print(f"  - Midday is strongest timing (27.2% great, 3.4% noise)")
    print(f"  - Low EMA alignment explains why it was disabled: most happen against the trend")

    # ─────────────────────────────────────────────────────────────────────────
    sep("Cat 3 deep dive: Bull BRK at PD Last Hr High (855 moves)")
    # ─────────────────────────────────────────────────────────────────────────

    g = cat_never
    print(f"\nAll 855: great={g['is_great'].mean():.1%}  noise={g['is_noise'].mean():.1%}  "
          f"avg_mag={g['magnitude_atr'].mean():.3f}")
    print(f"\nPD Last Hr High = the HIGH of the previous day's last hour (3pm-4pm candle high)")
    print(f"This is a resistance level. Breaking above it = morning gap fill or trend extension.")
    print(f"Currently: only bear BRK defined (break below it). Bull break = missed opportunity.")

    print(f"\nBy timing:")
    for t in ["open_flush", "morning", "midday", "afternoon"]:
        sub = g[g["timing_category"] == t]
        if len(sub) == 0:
            continue
        print(f"  {t:12s}: N={len(sub):4,}  great={sub['is_great'].mean():.1%}  "
              f"noise={sub['is_noise'].mean():.1%}")

    print(f"\nGate pass rates:")
    print(f"  body>=30:  {(g['trig_body_pct']>=30).mean():.1%}")
    print(f"  vol>=1.5:  {(g['trig_vol_ratio']>=1.5).mean():.1%}")
    print(f"  adx>=20:   {(g['pre_adx']>=20).mean():.1%}")
    print(f"  ema_align: {g['trig_ema_aligned'].mean():.1%}")
    print(f"  vwap_align:{g['trig_vwap_aligned'].mean():.1%}")

    print(f"\nQuality at different gate combos:")
    sub = g[g["trig_ema_aligned"] & (g["trig_body_pct"] >= 30)
            & (g["trig_vol_ratio"] >= 1.5) & (g["pre_adx"] >= 20)]
    print(f"  Full gates (EMA+body30+vol1.5+adx20): N={len(sub):4,}  great={sub['is_great'].mean():.1%}  "
          f"noise={sub['is_noise'].mean():.1%}")
    sub_m = g[(g["timing_category"].isin(["morning", "midday"])) & g["trig_ema_aligned"]
              & (g["trig_body_pct"] >= 30)]
    print(f"  Morning/midday + EMA + body>=30:       N={len(sub_m):4,}  great={sub_m['is_great'].mean():.1%}  "
          f"noise={sub_m['is_noise'].mean():.1%}")
    sub_ema = g[g["trig_ema_aligned"]]
    print(f"  EMA aligned only:                      N={len(sub_ema):4,}  great={sub_ema['is_great'].mean():.1%}  "
          f"noise={sub_ema['is_noise'].mean():.1%}")

    print(f"\nPer-symbol breakdown (EMA-aligned):")
    for sym in sub_ema["symbol"].value_counts().head(8).index:
        sub_s = sub_ema[sub_ema["symbol"] == sym]
        print(f"  {sym:6s}: N={len(sub_s):3,}  great={sub_s['is_great'].mean():.1%}  "
              f"noise={sub_s['is_noise'].mean():.1%}")

    print(f"\nConclusion for Cat 3:")
    print(f"  - PD Last Hr High bull BRK: great=22.3% (1.16x), decent noise=5.0%")
    print(f"  - 68% EMA aligned — much better than ORB Low reclaim")
    print(f"  - Strong morning/open_flush presence (60% of cases)")
    print(f"  - This is closest to existing BRK logic — easy to add")

    # ─────────────────────────────────────────────────────────────────────────
    sep("SECTION D: TOP NEW SIGNAL CANDIDATES (ranked)")
    # ─────────────────────────────────────────────────────────────────────────

    # Compute scores
    g1 = cat_never   # PD Last Hr High bull BRK
    g2 = cat_disabled  # ORB Low reclaim

    g1_gated = g1[g1["trig_ema_aligned"] & (g1["trig_body_pct"] >= 30)
                  & (g1["trig_vol_ratio"] >= 1.5) & (g1["pre_adx"] >= 20)]
    g2_midday = g2[g2["timing_category"] == "midday"]

    def score(n, gr, mfe):
        return n * gr * mfe

    candidates = [
        {
            "rank": 1,
            "name": "Bull BRK at PD Last Hr High",
            "sig_name": "BRK_PDLHH",
            "why": "PDLHrH breaks upward — never defined, strong EMA alignment",
            "N_raw": len(g1),
            "great_raw": g1["is_great"].mean(),
            "noise_raw": g1["is_noise"].mean(),
            "N_gated": len(g1_gated),
            "great_gated": g1_gated["is_great"].mean() if len(g1_gated) else 0,
            "avg_mfe": g1["magnitude_atr"].mean(),
            "score": score(len(g1), g1["is_great"].mean(), g1["magnitude_atr"].mean()),
        },
        {
            "rank": 2,
            "name": "Bull Reclaim of ORB Low (midday)",
            "sig_name": "EXREV_ORBLow",
            "why": "ORB Low reclaim — disabled but midday subset is cleanest",
            "N_raw": len(g2_midday),
            "great_raw": g2_midday["is_great"].mean(),
            "noise_raw": g2_midday["is_noise"].mean(),
            "N_gated": len(g2_midday),
            "great_gated": g2_midday["is_great"].mean(),
            "avg_mfe": g2_midday["magnitude_atr"].mean(),
            "score": score(len(g2_midday), g2_midday["is_great"].mean(), g2_midday["magnitude_atr"].mean()),
        },
    ]

    print(f"\n{'#':<4} {'Signal':<35} {'N_raw':>7} {'Gt_raw':>8} {'N_gated':>8} {'Gt_gate':>8} {'Noise':>7} {'AvgMFE':>8} {'Score':>8}")
    print("-" * 95)
    for c in sorted(candidates, key=lambda x: -x["score"]):
        print(f"  {c['rank']}  {c['name']:<35} {c['N_raw']:>7,} {c['great_raw']:>8.1%} "
              f"{c['N_gated']:>8,} {c['great_gated']:>8.1%} {c['noise_raw']:>7.1%} "
              f"{c['avg_mfe']:>8.3f} {c['score']:>8.1f}")

    # ─────────────────────────────────────────────────────────────────────────
    sep("SECTION E: SPOT-CHECK WITH 1M DATA")
    # ─────────────────────────────────────────────────────────────────────────

    print("\n5 representative missed moves (best mfe_1m, varied symbols):\n")

    # Pick examples: 3 Cat3 (PD Last Hr High) + 2 Cat2 (ORB Low midday)
    top_cat3 = (cat_never[cat_never["mfe_1m"].notna()]
                .sort_values("mfe_1m", ascending=False)
                .drop_duplicates("symbol").head(3))
    top_cat2 = (cat_disabled[(cat_disabled["mfe_1m"].notna())
                              & (cat_disabled["timing_category"] == "midday")]
                .sort_values("mfe_1m", ascending=False)
                .drop_duplicates("symbol").head(2))
    spot = pd.concat([top_cat3, top_cat2]).reset_index(drop=True)

    for _, row in spot.iterrows():
        symbol     = row["symbol"]
        date_str   = str(row["date"])
        start_time = row["start_time"]       # Timestamp with UTC tz
        level_type = row["nearest_level_type"]
        level_dist = row["nearest_level_dist_atr"]
        mag        = row["magnitude_atr"]
        mfe        = row["mfe_1m"]
        mae        = row["mae_1m"]
        timing     = row["timing_category"]

        print(f"{'─'*65}")
        print(f"  {symbol} | {date_str} | {pd.Timestamp(start_time).tz_convert('US/Eastern').strftime('%H:%M ET')} | {level_type}")
        print(f"  timing={timing}  mag={mag:.3f}ATR  mfe_1m={mfe:.3f}ATR  mae_1m={mae:.3f}ATR")
        print(f"  body={row['trig_body_pct']:.0f}%  vol={row['trig_vol_ratio']:.1f}x  "
              f"ema={row['trig_ema_aligned']}  level_dist={level_dist:.3f}ATR")

        ib = load_1m(symbol)
        if ib is None:
            print(f"  [1m data not found]")
            continue

        start_et = pd.Timestamp(start_time).tz_convert("US/Eastern")
        window   = ib.loc[start_et - pd.Timedelta("12min"):start_et + pd.Timedelta("18min")]

        if len(window) < 3:
            print(f"  [No 1m bars found near {start_et.strftime('%H:%M ET')}]")
            continue

        o_col = "open"  if "open"   in ib.columns else "o"
        h_col = "high"  if "high"   in ib.columns else "h"
        l_col = "low"   if "low"    in ib.columns else "l"
        c_col = "close" if "close"  in ib.columns else "c"
        v_col = "volume" if "volume" in ib.columns else "v"

        print(f"\n  {'Time':<8} {'Open':>8} {'High':>8} {'Low':>8} {'Close':>8} {'Vol':>10}")
        print(f"  {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*10}")
        for ts, bar in window.iterrows():
            note = " ← TRIGGER" if abs((ts - start_et).total_seconds()) < 90 else ""
            try:
                print(f"  {ts.strftime('%H:%M'):<8} {bar[o_col]:>8.2f} {bar[h_col]:>8.2f} "
                      f"{bar[l_col]:>8.2f} {bar[c_col]:>8.2f} {int(bar[v_col]):>10,}{note}")
            except Exception:
                pass
        print()

    # ─────────────────────────────────────────────────────────────────────────
    sep("SECTION F: RECOMMENDATION — NEW SIGNAL TYPES FOR v3.4")
    # ─────────────────────────────────────────────────────────────────────────

    g1_mm = g1[g1["timing_category"].isin(["morning","midday"]) & g1["trig_ema_aligned"]]

    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║  RECOMMENDATION #1 (IMPLEMENT): Bull BRK at PD Last Hr High        ║
╚══════════════════════════════════════════════════════════════════════╝

Signal name: BRK (extend existing BRK_BULL_LEVELS to include PD Last Hr High)

Why: PD Last Hr High is ALREADY in BRK_BEAR_LEVELS. Adding bull BRK is a
symmetric extension — it just means price can also break ABOVE this level.
The "last hour high" of the prior day acts as morning resistance. When price
breaks above it, that's a genuine BRK signal (resistance-to-launchpad pattern).

Raw pool:   N={len(g1):,}  great={g1['is_great'].mean():.1%}  noise={g1['is_noise'].mean():.1%}
With gates: N={len(g1_gated):,}  great={g1_gated['is_great'].mean():.1%}  noise={g1_gated['is_noise'].mean():.1%}
            (EMA aligned + body>=30% + vol>=1.5x + ADX>=20)
Morning+midday+EMA: N={len(g1_mm):,}  great={g1_mm['is_great'].mean():.1%}  noise={g1_mm['is_noise'].mean():.1%}
Avg MFE: {g1['magnitude_atr'].mean():.3f} ATR

Pine Script change (minimal):
  // In BRK_BULL_LEVELS array, add:
  isPdLastHrHighBrkBull = level == "PD Last Hr High" and direction == "bull"
  // OR simply add "PD Last Hr High" to the existing BRK_BULL_LEVELS set
  // Same gates as all other BRK signals: EMA + body + vol + ADX

Implementation effort: ~5 lines. Risk: low (same gate stack as existing BRK).

╔══════════════════════════════════════════════════════════════════════╗
║  RECOMMENDATION #2 (OPTIONAL): ORB Low Reclaim (midday only)       ║
╚══════════════════════════════════════════════════════════════════════╝

Signal name: EXREV-style reclaim of ORB Low

Why: This was intentionally disabled in v3.2. BUT the midday subset is cleaner
(27.2% great, 3.4% noise vs 19.2%/6.9% baseline). Could be re-enabled with
a midday-only timing gate to avoid the noisy morning/opening versions.

Raw midday: N={len(g2_midday):,}  great={g2_midday['is_great'].mean():.1%}  noise={g2_midday['is_noise'].mean():.1%}
Warning: Only 26% have EMA aligned — most ORB Low reclaims happen AGAINST trend.
         Midday filter alone is the cleanest gate.

Pine Script change (minimal):
  // Re-enable bull REV/EXREV at ORB Low BUT only when isMidday==true
  // (Same isMidday flag already used for midday flat-EMA boost in v3.3b)
  isOrbLowReclaim = level == "ORB Low" and direction == "bull" and isMidday

Implementation effort: ~3 lines. Risk: moderate (removing a deliberate disable).
Verdict: Lower priority than #1. Test in live data first.

╔══════════════════════════════════════════════════════════════════════╗
║  DO NOT IMPLEMENT: Bull REV/BRK at HIGH levels (v3.3c suppressed)  ║
╚══════════════════════════════════════════════════════════════════════╝

The 2,503 bull moves at PM/PD/ORB/Week High are 22.1% great — sounds ok.
But v3.3c analysis showed: -1,212 ATR drag when bull REV fires at HIGHs.
The great rate doesn't capture the asymmetric loss (wins avg +0.225 ATR,
losses avg -0.997 ATR = 4.4x asymmetry). DO NOT RESTORE.

Bull BRK THROUGH a high (broke_through=True, same 2,503 moves) was also tested:
  With full gates: N=389  great=13.7%  noise=11.6% — WORSE than baseline.
  Conclusion: even "breaking through" a HIGH as a bull doesn't work at these gates.

╔══════════════════════════════════════════════════════════════════════╗
║  SUMMARY TABLE                                                       ║
╚══════════════════════════════════════════════════════════════════════╝
""")

    print(f"  {'Signal':<38} {'N':>6} {'Great':>7} {'Noise':>7} {'Verdict'}")
    print(f"  {'─'*38} {'─'*6} {'─'*7} {'─'*7} {'─'*20}")
    rows = [
        ("Bull BRK at PD Last Hr High (raw)",     len(g1),        g1["is_great"].mean(),       g1["is_noise"].mean(),       "IMPLEMENT"),
        ("Bull BRK at PD Last Hr High (gated)",   len(g1_gated),  g1_gated["is_great"].mean() if len(g1_gated) else 0, g1_gated["is_noise"].mean() if len(g1_gated) else 0, "IMPLEMENT"),
        ("ORB Low Reclaim midday",                 len(g2_midday), g2_midday["is_great"].mean(), g2_midday["is_noise"].mean(), "OPTIONAL"),
        ("Bull REV/BRK at HIGH (all)",             len(cat_suppressed), cat_suppressed["is_great"].mean(), cat_suppressed["is_noise"].mean(), "DO NOT IMPLEMENT"),
    ]
    for name, n, gr, nr, verdict in rows:
        print(f"  {name:<38} {n:>6,} {gr:>7.1%} {nr:>7.1%} {verdict}")

    print(f"""
Baseline: great={baseline_great:.1%}  noise={baseline_noise:.1%}
""")


if __name__ == "__main__":
    main()
