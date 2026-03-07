#!/usr/bin/env python3
"""
Match KLB v3.2 trigger rules against the move catalog.
For each move: would KLB fire a signal? Which gate blocks it?
"""

import pandas as pd
import numpy as np
from pathlib import Path

CATALOG = Path(__file__).parent / "move-catalog.parquet"

# ── KLB Signal Configuration ───────────────────────────────────────────────────

# Level → signal type mapping (v3.2)
# BRK levels (barriers — price breaks through)
BRK_LEVELS = {
    "PM Low", "PD Low", "Week Low", "ORB Low",       # bear BRK only
    "Week Open", "Month Open",                         # two-way BRK
    "PD Last Hr Low", "PD Last Hr High",               # BRK + REV
}

# REV levels (magnets — touch-and-turn)
REV_LEVELS_GATED = {
    "PM High", "PD High", "Week High", "ORB High",    # EMA gated REV
    "PM Low", "PD Low", "Week Low",                    # bull REV at LOWs (EMA gated)
    "PD Last Hr Low",                                  # bull REV (EMA gated)
}

REV_LEVELS_UNGATED = {
    "PD Mid", "Today Open", "PD Close",                # no EMA gate, no VWAP filter
}

# Which levels allow which direction
BRK_BEAR_LEVELS = {"PM Low", "PD Low", "Week Low", "ORB Low", "Week Open", "Month Open",
                    "PD Last Hr Low", "PD Last Hr High"}
BRK_BULL_LEVELS = {"Week Open", "Month Open"}  # Only WO/MO have bull BRK

REV_BULL_LEVELS = {"PM High", "PD High", "Week High", "ORB High",  # bull REV at HIGHs
                    "PM Low", "PD Low", "Week Low",                  # bull REV at LOWs
                    "PD Last Hr Low",                                # bull REV
                    "PD Mid", "Today Open", "PD Close"}             # magnet REV (ungated)

REV_BEAR_LEVELS = {"PM High", "PD High", "Week High", "ORB High",  # bear REV at HIGHs (EXREV)
                    "PD Mid", "Today Open", "PD Close"}             # magnet REV (ungated)

# ORB Low bull REV = DISABLED in v3.2
DISABLED_SIGNALS = {("ORB Low", "bull", "REV")}

# Gate thresholds
BODY_PCT_MIN = 30.0
VOL_RATIO_MIN = 1.5
ADX_MIN = 20.0
LEVEL_PROXIMITY_ATR = 0.10  # within 10% ATR to count as "at level"


def classify_signal(row):
    """For a single move, determine if KLB would fire and what blocks it."""
    level = row["nearest_level_type"]
    dist = row["nearest_level_dist_atr"]
    direction = row["direction"]
    ema = row["trig_ema_aligned"]
    body = row["trig_body_pct"]
    vol = row["trig_vol_ratio"]
    adx = row["pre_adx"]
    vwap = row["trig_vwap_aligned"]
    timing = row["timing_category"]
    interaction = row["level_interaction"]

    result = {
        "near_level": dist <= LEVEL_PROXIMITY_ATR,
        "signal_type": None,
        "would_fire": False,
        "blocked_by": [],
    }

    if not result["near_level"]:
        result["blocked_by"].append("no_level_nearby")
        return result

    # Determine possible signal type
    is_brk = False
    is_rev_gated = False
    is_rev_ungated = False

    if direction == "bull":
        if level in BRK_BULL_LEVELS and interaction == "broke_through":
            is_brk = True
        if level in REV_BULL_LEVELS:
            if level in REV_LEVELS_UNGATED:
                is_rev_ungated = True
            else:
                is_rev_gated = True
    else:  # bear
        if level in BRK_BEAR_LEVELS and interaction == "broke_through":
            is_brk = True
        if level in REV_BEAR_LEVELS:
            if level in REV_LEVELS_UNGATED:
                is_rev_ungated = True
            else:
                is_rev_gated = True

    # Check disabled signals
    if (level, direction, "REV") in DISABLED_SIGNALS:
        is_rev_gated = False
        is_rev_ungated = False

    if not is_brk and not is_rev_gated and not is_rev_ungated:
        result["blocked_by"].append("no_matching_signal_type")
        return result

    # Try each signal type, check gates
    # Priority: ungated REV > gated REV > BRK (most permissive first)

    if is_rev_ungated:
        # Magnet levels: body + vol + ADX only (no EMA, no VWAP)
        blocks = []
        if body < BODY_PCT_MIN:
            blocks.append("body_pct")
        if vol < VOL_RATIO_MIN:
            blocks.append("volume")
        if adx < ADX_MIN:
            blocks.append("adx")
        if not blocks:
            result["signal_type"] = "REV_ungated"
            result["would_fire"] = True
            return result
        # Try other types if this blocked
        result["blocked_by"] = blocks

    if is_rev_gated:
        blocks = []
        if not ema and timing != "open_flush":
            blocks.append("ema_gate")
        if body < BODY_PCT_MIN:
            blocks.append("body_pct")
        if vol < VOL_RATIO_MIN:
            blocks.append("volume")
        if adx < ADX_MIN:
            blocks.append("adx")
        # VWAP filter for gated REV (bull needs above VWAP, bear needs below)
        if not vwap:
            blocks.append("vwap_filter")
        if not blocks:
            result["signal_type"] = "REV_gated"
            result["would_fire"] = True
            return result
        if not result["blocked_by"]:
            result["blocked_by"] = blocks

    if is_brk:
        blocks = []
        if not ema and timing != "open_flush":
            blocks.append("ema_gate")
        if body < BODY_PCT_MIN:
            blocks.append("body_pct")
        if vol < VOL_RATIO_MIN:
            blocks.append("volume")
        if adx < ADX_MIN:
            blocks.append("adx")
        if not blocks:
            result["signal_type"] = "BRK"
            result["would_fire"] = True
            return result
        if not result["blocked_by"]:
            result["blocked_by"] = blocks

    return result


def main():
    df = pd.read_parquet(CATALOG)
    p = df[(df["pass"] == "primary") & (df["symbol"] != "TSM")].copy()

    # Label great/noise
    has_1m = p["mfe_1m"].notna()
    p["is_great"] = (
        (has_1m & (p["mae_1m"] > 0)
         & (p["mfe_1m"] / p["mae_1m"].clip(lower=0.001) >= 3)
         & (p["mfe_1m"] >= 0.30)
         & (p["retracement_12bar"] <= 0.40))
        | (~has_1m & (p["magnitude_atr"] >= 0.50) & (p["retracement_12bar"] <= 0.40))
    )
    p["is_noise"] = (has_1m & (p["mae_1m"] > p["mfe_1m"])) | (p["retracement_6bar"] > 0.80)

    baseline_great = p["is_great"].mean()
    baseline_noise = p["is_noise"].mean()

    print("=" * 70)
    print(f"KLB v3.2 Signal Matching vs Move Catalog")
    print(f"{'=' * 70}")
    print(f"Total primary moves (excl TSM): {len(p):,}")
    print(f"Baseline: great={baseline_great:.1%}, noise={baseline_noise:.1%}")

    # Classify each move
    print("\nClassifying moves...")
    results = p.apply(classify_signal, axis=1, result_type="expand")
    p["near_level"] = results["near_level"]
    p["signal_type"] = results["signal_type"]
    p["would_fire"] = results["would_fire"]
    p["blocked_by"] = results["blocked_by"]

    fired = p[p["would_fire"]]
    missed = p[~p["would_fire"]]

    print(f"\n{'=' * 70}")
    print("SIGNAL MATCHING RESULTS")
    print(f"{'=' * 70}")
    print(f"  Would fire:  {len(fired):,} ({len(fired)/len(p):.1%})")
    print(f"  Would miss:  {len(missed):,} ({len(missed)/len(p):.1%})")

    # ── Fired signals breakdown ──
    print(f"\n  FIRED — by signal type:")
    for st in ["REV_ungated", "REV_gated", "BRK"]:
        sub = fired[fired["signal_type"] == st]
        if len(sub) == 0:
            continue
        gr = sub["is_great"].mean()
        nr = sub["is_noise"].mean()
        print(f"    {st:15s}  N={len(sub):5,}  great={gr:.1%}  noise={nr:.1%}")

    print(f"\n  FIRED — by level type:")
    for lt in fired["nearest_level_type"].value_counts().index:
        sub = fired[fired["nearest_level_type"] == lt]
        gr = sub["is_great"].mean()
        nr = sub["is_noise"].mean()
        print(f"    {lt:20s}  N={len(sub):5,}  great={gr:.1%}  noise={nr:.1%}")

    print(f"\n  FIRED — by timing:")
    for t in ["open_flush", "morning", "midday", "afternoon"]:
        sub = fired[fired["timing_category"] == t]
        if len(sub) == 0:
            continue
        gr = sub["is_great"].mean()
        nr = sub["is_noise"].mean()
        print(f"    {t:15s}  N={len(sub):5,}  great={gr:.1%}  noise={nr:.1%}")

    print(f"\n  FIRED — great rate: {fired['is_great'].mean():.1%} "
          f"(vs {baseline_great:.1%} baseline, {fired['is_great'].mean()/baseline_great:.2f}x)")
    print(f"  FIRED — noise rate: {fired['is_noise'].mean():.1%} "
          f"(vs {baseline_noise:.1%} baseline)")

    # ── Missed moves breakdown ──
    print(f"\n{'=' * 70}")
    print("MISSED MOVES — WHY?")
    print(f"{'=' * 70}")

    # Primary block reasons
    block_counts = {}
    for blocks in missed["blocked_by"]:
        for b in blocks:
            block_counts[b] = block_counts.get(b, 0) + 1

    print(f"\n  Block reasons (a move can have multiple):")
    for reason, count in sorted(block_counts.items(), key=lambda x: -x[1]):
        pct = count / len(missed) * 100
        print(f"    {reason:25s}  {count:6,}  ({pct:.1f}%)")

    # Missed great moves
    missed_great = missed[missed["is_great"]]
    print(f"\n  Missed GREAT moves: {len(missed_great):,} ({len(missed_great)/p['is_great'].sum():.1%} of all great)")

    print(f"\n  Missed great — block reasons:")
    great_blocks = {}
    for blocks in missed_great["blocked_by"]:
        for b in blocks:
            great_blocks[b] = great_blocks.get(b, 0) + 1
    for reason, count in sorted(great_blocks.items(), key=lambda x: -x[1]):
        pct = count / len(missed_great) * 100
        print(f"    {reason:25s}  {count:6,}  ({pct:.1f}%)")

    # Missed great by timing
    print(f"\n  Missed great — by timing:")
    for t in ["open_flush", "morning", "midday", "afternoon"]:
        sub = missed_great[missed_great["timing_category"] == t]
        if len(sub) > 0:
            print(f"    {t:15s}  {len(sub):5,} missed great moves")

    # Missed great by pattern
    print(f"\n  Missed great — by pattern:")
    for pat in missed_great["pattern_category"].value_counts().index:
        sub = missed_great[missed_great["pattern_category"] == pat]
        print(f"    {pat:22s}  {len(sub):5,}")

    # ── What if we relaxed gates? ──
    print(f"\n{'=' * 70}")
    print("WHAT IF WE RELAXED GATES?")
    print(f"{'=' * 70}")

    near = p[p["near_level"]].copy()
    total_near = len(near)
    great_near = near["is_great"].sum()

    gates = {
        "body_pct": near["trig_body_pct"] >= BODY_PCT_MIN,
        "volume": near["trig_vol_ratio"] >= VOL_RATIO_MIN,
        "adx": near["pre_adx"] >= ADX_MIN,
        "ema_gate": near["trig_ema_aligned"] | (near["timing_category"] == "open_flush"),
        "vwap_filter": near["trig_vwap_aligned"],
    }

    print(f"\n  Near-level moves: {total_near:,} ({great_near:,} great)")
    print(f"\n  Gate pass rates and impact on great moves:")
    for gate_name, mask in gates.items():
        pass_n = mask.sum()
        pass_great = near.loc[mask, "is_great"].sum()
        fail_n = (~mask).sum()
        fail_great = near.loc[~mask, "is_great"].sum()
        pass_great_rate = near.loc[mask, "is_great"].mean()
        fail_great_rate = near.loc[~mask, "is_great"].mean() if fail_n > 0 else 0
        print(f"    {gate_name:15s}  pass={pass_n:6,} ({pass_great_rate:.1%} great)  "
              f"fail={fail_n:6,} ({fail_great_rate:.1%} great)  "
              f"great lost by gate: {fail_great:,}")

    # Combined: what passes ALL gates?
    all_pass = gates["body_pct"] & gates["volume"] & gates["adx"] & gates["ema_gate"]
    all_pass_n = all_pass.sum()
    all_pass_great = near.loc[all_pass, "is_great"].sum()
    all_pass_great_rate = near.loc[all_pass, "is_great"].mean()
    print(f"\n  All core gates (body+vol+adx+ema): {all_pass_n:,} pass "
          f"({all_pass_great_rate:.1%} great, {all_pass_great:,} great moves)")
    print(f"  Great moves lost by gating: {great_near - all_pass_great:,} "
          f"({(great_near - all_pass_great)/great_near:.1%})")

    # ── Opportunity: moves near levels that pass all gates but have no signal type match ──
    print(f"\n{'=' * 70}")
    print("OPPORTUNITY: Near level + passes gates but no signal type match")
    print(f"{'=' * 70}")

    no_type = missed[missed["near_level"]].copy()
    no_type_reason = no_type[no_type["blocked_by"].apply(lambda x: "no_matching_signal_type" in x)]
    if len(no_type_reason) > 0:
        print(f"\n  {len(no_type_reason):,} moves near levels with no matching signal type")
        print(f"  Great rate: {no_type_reason['is_great'].mean():.1%}")
        print(f"\n  By level type:")
        for lt in no_type_reason["nearest_level_type"].value_counts().head(10).index:
            sub = no_type_reason[no_type_reason["nearest_level_type"] == lt]
            gr = sub["is_great"].mean()
            print(f"    {lt:20s}  N={len(sub):5,}  great={gr:.1%}  dir: "
                  f"bull={len(sub[sub['direction']=='bull']):,} bear={len(sub[sub['direction']=='bear']):,}")


if __name__ == "__main__":
    main()
