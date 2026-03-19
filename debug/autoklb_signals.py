#!/usr/bin/env python3
"""
AutoKLB Signal Logic — v3.6 baseline
=====================================
The ONLY file the agent modifies. Contains all signal routing,
gate thresholds, suppressions, and quality override rules.

Contract: classify_signal(row) -> dict with keys:
  - would_fire: bool
  - signal_type: str | None  ("BRK", "REV", "FADE")
  - blocked_by: list[str]
  - is_dimmed: bool
"""

import numpy as np

# ══════════════════════════════════════════════════════════════════════════════
# GATE THRESHOLDS — agent can tune these
# ══════════════════════════════════════════════════════════════════════════════
BODY_PCT_MIN = 60.0  # loop E1: cascade body filter raise
VOL_RATIO_MIN = 0.0           # loop O3: disable BRK vol gate entirely (matches REV_VOL_MIN=0)
REV_VOL_MIN = 0.0              # loop L2: disable REV vol gate entirely
VOL_EXHAUSTION_MAX = 0.0       # loop Z1: dim-all extreme test
ADX_MIN = 0.0                 # loop: remove ADX gate
LEVEL_PROXIMITY_ATR = 0.65    # loop AM1: test tighter BRK proximity (0.70→0.65 — remove fringe signals)
FRESHNESS_MAX_TESTS = 0        # loop AT5: disable FRESHNESS gate (3→0 — AQ2 had 0→2=+1.7; confirm gate still adds value at current cleaner composition)
ATR_CONSUMED_MAX = 999.0       # loop Q5: fully disable ATR consumed filter
SPY_RANGE_EXHAUSTION = 0.0     # loop R1: fully disable SPY range exhaustion
REV_PROXIMITY_TOL = 0.35       # loop AZ1: cascade even tighter bear REV
BIG_CANDLE_ATR = 0.15          # loop E4: retry big-candle tighter at new baseline

# ── Quality override thresholds ──
QUIET_COIL_VOL_RAMP = 0.0     # loop D7: disable quiet coil vol ramp
QUIET_COIL_RANGE = 7.0        # loop F6: aggressive quiet coil range
MIDDAY_EMA_CHANGE = 0.0       # loop B5: disable midday flat gate entirely
BROAD_COIL_RANGE = 7.0        # loop F7: aggressive broad coil range
BROAD_COIL_SPY_MIN = 0.0      # loop Y4: fully open broad coil (no SPY req)
VWAP_RECLAIM_ENABLED = True   # loop AZ2: re-enable VRC at clean routing
VWAP_RECLAIM_MIN_BARS = 0     # loop Q3: no bar gap required for VWAP reclaim
RS_LEADERSHIP_MIN = 0.0       # loop Q4: fully disable RS leadership gate
RS_LEADERSHIP_VWAP_SKIP = True   # loop R2: RS leaders bypass VWAP too (cascade Q4)

# ══════════════════════════════════════════════════════════════════════════════
# SIGNAL ROUTING — agent can modify these sets
# ══════════════════════════════════════════════════════════════════════════════

# BRK levels (barriers — price breaks through)
BRK_BEAR_LEVELS = {
    "ORB Low",                        # loop AD6: removed Week Low from BRK_BEAR (weekly floor break test)
    # loop AP1: removed Week Low from BRK_BEAR (AD6/AI4 both neutral — test cleanup at 2102.6 baseline)
    "Month Open",                                  # loop V1: removed Week Open bear BRK
    "PD Last Hr High",                             # loop W2: removed PD Last Hr Low bear BRK
    "Today Open",                                   # loop U1: removed PD Close bear BRK
    "VWAP",                                       # loop G3: VWAP bear BRK
    "Yest High",                                  # loop J5: bear BRK below Yest High                               # loop T4: removed Yest Low bear BRK (late continuation)
    # loop AO4: removed Yest Low from BRK_BEAR (AI1 neutral re-add — test cleanup at new 2102.6 baseline)
    "ORB Low",                                     # loop K3: bear BRK below ORB Low
    "PD High",                                      # loop V8: bear BRK below PD High
    "PM High",                                      # loop V9: bear BRK below PM High
    "PD Close",                                    # loop AX5: gap fill break below prior close
    # loop AF3: removed Month High from BRK_BEAR (C1: AD4/AA5 cascade — monthly high pattern)
    # loop V2: removed Month Low bear BRK (late panic break)
}
BRK_BULL_LEVELS = {
    "Week Open", "Month Open",
    "PD Last Hr High",          # v3.4: added
    "Today Open",               # loop: Today Open BRK
    "PD High",                  # loop: PD High BRK                               # loop T2: removed PD Close (weak gap fill reclaim)
    "Yest High",                # loop AY2: re-add prior session high BRK
    # loop AD3: removed Yest High from BRK_BULL (prior day high BRK — first-move test)
    "Week High",               # loop D5: Week High bull BRK
    "Month Open",               # loop M1: bull BRK above Month Open
    "ORB High",                 # loop J3: bull BRK above ORB High
    "Yest Low",                  # loop AH3: re-add Yest Low to BRK_BULL (AA3 inverse — prior-day floor reclaim at 2089)
    "VWAP",                     # loop AY3: re-add VWAP BRK bull reclaim
    # loop AA2: removed VWAP from BRK_BULL (P3: W4 cascade — VWAP bull reclaim noise)
    "PM High",                  # loop K4: bull BRK above PM High
    # loop AC3: removed Week Low from BRK_BULL (U9: AA3/AB3 cascade — weekly floor reclaim)
    "ORB Low",                  # loop U10: bull BRK above ORB Low support
    # loop AC2: removed PD Last Hr Low from BRK_BULL (W5: AA3 cascade — last-hour reclaim)
    # loop AB3: removed Month Low from BRK_BULL (C2: AA3 cascade — monthly reclaim noise)
    # loop AD4: removed Month High from BRK_BULL (H2: monthly high breakout BRK test)
}

# REV levels — EMA gated
REV_LEVELS_GATED = {
    "PD Low",             # bull REV at LOWs  # loop AD2: removed Week Low REV_GATED
    "PD Last Hr Low",            # loop AJ3: re-add PD Last Hr Low to REV_LEVELS_GATED (AC5 inverse — GATED takes precedence over ungated, EMA filter)
    "Yest Low",                  # loop AI3: re-add Yest Low to REV_LEVELS_GATED (Y4 inverse — gated path takes precedence over AH2 ungated)
    "Month Low",                  # loop AI5: re-add Month Low to REV_LEVELS_GATED (AC4 inverse — monthly low gated bull REV, revives dead REV_BULL entry)
    "PD High",                   # loop AK4: re-add PD High to REV_LEVELS_GATED (AE4 inverse — bear-only gated REV at prior-day high)
    # loop AE4: removed PD High from REV_GATED (Z2 retry: bear REV at PD High, new composition)
    "Yest High",                 # loop AJ2: re-add Yest High to REV_LEVELS_GATED (Z1 inverse — bear-only gated REV at prior session high)
    "PD Last Hr High",                           # loop G1: bear REV at PD Last Hr High (gated)
    "Today Open",                               # loop AG5: gated bear REV at Today Open (bear-only: in REV_BEAR not REV_BULL)
    # loop AA4: removed PM High from REV gated (O1: Z1 cascade — premarket high ref)
    "Week High",                 # loop AK3: re-add Week High to REV_LEVELS_GATED (AA5 inverse — bear-only gated REV at weekly high)
    # loop AA5: removed Week High from REV gated (O2: Z1 cascade — weekly high ref)
    "Month High",                # loop AK5: re-add Month High to REV_LEVELS_GATED (AB2 inverse — bear-only gated REV at monthly high)
    "PD Close",                   # loop AM4: add PD Close to REV_LEVELS_GATED (dual-path: gated EMA-confirmed + ungated fallback — prior-day close quality upgrade)
    "PD Close",                   # loop AM4: add PD Close to REV_LEVELS_GATED (dual-path: gated EMA-confirmed + ungated fallback — prior-day close quality upgrade)
    # loop AB2: removed Month High from REV gated (C3: completing HIGH-side REV_GATED cleanup)
    "Week Open",                                 # loop G2: gated bear REV at Week Open rejection
    "VWAP",                                      # loop AI2: add VWAP to REV_LEVELS_GATED (bear-only gated VWAP rejection — ungated W4 was noise)
    "PD Mid",                     # loop AM3: add PD Mid to REV_LEVELS_GATED (dual-path: gated EMA-confirmed + ungated fallback — magnet REV quality upgrade)
    "PD Mid",                     # loop AM3: add PD Mid to REV_LEVELS_GATED (dual-path: gated EMA-confirmed + ungated fallback — magnet REV quality upgrade)
    "ORB Low",                    # loop AM5: add ORB Low to REV_LEVELS_GATED (dual-path: gated EMA-confirmed + ungated fallback — ORB range support quality upgrade)
    "ORB Low",                    # loop AM5: add ORB Low to REV_LEVELS_GATED (dual-path: gated EMA-confirmed + ungated fallback — ORB range support quality upgrade)
    # NOTE: other HIGHs suppressed; PD High enabled for bear REV only
}

# REV levels — ungated (no EMA, no VWAP)
REV_LEVELS_UNGATED = {
    "PD Mid", "PD Close",                          # loop W3: removed Today Open REV ungated
    "ORB Low",              # loop E3: ORB Low ungated bull REV path
    # loop Y1: removed Month Low from REV ungated (O5: monthly floor ungated test)
    "Week Low",             # loop L4: ungated bull REV at Week Low support
    # loop AJ1: removed Yest Low from REV_UNGATED (AH2 dead code — AI3 GATED takes precedence over ungated)
    "PD Last Hr Low",       # loop G4: PD Last Hr Low ungated bear REV path
    # loop Y2: removed Month High from REV ungated (N4: monthly ceiling ungated test)
    # loop X3: removed Yest High from REV ungated (1/2 — L3 duplicate)
    # loop X3: removed Yest High from REV ungated (2/2 — L3 duplicate)
    # loop W4: removed VWAP from REV ungated (tested noise)
}

# Direction routing
REV_BULL_LEVELS = {
    "PD Low", "Week Low",             # bull REV at LOWs  # loop AD1: removed PM Low REV_GATED (gated)
    "PD Last Hr Low",                            # bull REV (gated)
    "PD Mid", "PD Close",                          # loop W3: removed Today Open REV ungated          # magnet REV (ungated)
    "ORB Low",                                       # loop F2: ORB Low bull REV (ungated)
    "Yest Low",                                        # loop S2: bull REV at Yest Low
    "Month Low",                                         # loop C4: bull REV at Month Low support
    "Month High",                                            # loop AP3: add Month High to REV_BULL_LEVELS (gated bull bounce at monthly ceiling — not in DISABLED_SIGNALS, GATED path via AK5)
    "VWAP",                                              # loop AJ5: add VWAP to REV_BULL_LEVELS (bull direction: cascade AI2 gated VWAP — VWAP reclaim bull REV)
    "Yest High",                                             # loop AP2: add Yest High to REV_BULL_LEVELS (gated bull bounce at prior-session high — not in DISABLED_SIGNALS, GATED path via AJ2)
    # v3.3c: PM High, PD High, Week High, ORB High REMOVED for bull REV
}

REV_BEAR_LEVELS = {
    # loop AS3: removed Week High from REV_BEAR_LEVELS (cascade AS2 — last high-side bear direction test at 2104.3)
    # loop AP4: removed Month Low from REV_BEAR_LEVELS (AL5 neutral add — AL4 proved failed-support thesis weak, test removal)
    "PD Mid", "Today Open", "PD Close",               # magnet REV (ungated)
    "PD Last Hr Low",                                  # loop E5: bear REV at prior support
    # loop AQ5: removed PD Last Hr High from REV_BEAR_LEVELS (F3 bear REV at prior high — test value at 2102.6 composition)
    "Week Low",                                        # loop M3: bear REV at Week Low
    # loop AR3: removed Yest High from REV_BEAR_LEVELS (S1 bear REV at prior session high — test value with FRESHNESS=2 at 2104.3)
    # loop AP5: removed Yest Low from REV_BEAR_LEVELS (AJ4 neutral add — test removal at new 2102.6 baseline)
    # loop AR4: removed VWAP from REV_BEAR_LEVELS (Z4 direction routing — test if gated VWAP bear REV adds value at 2104.3)
    # loop AR5: removed Month High from REV_BEAR_LEVELS (C3 bear REV at monthly ceiling — test value at 2104.3)
    "Week Open",                                         # loop G2: bear REV at Week Open rejection
}

# ── Suppressions ──
DISABLED_SIGNALS = {
    # ("ORB Low", "bull", "REV"),        # loop G5: re-enabled ORB Low bull REV
    ("PM High", "bull", "REV"),          # v3.3c: bull REV at HIGHs suppressed
    ("PD High", "bull", "REV"),          # v3.3c
    ("Week High", "bull", "REV"),        # v3.3c
    ("ORB High", "bull", "REV"),         # v3.3c
    # ("PM High", "bear", "REV"),        # loop: re-enabled Phase 16a
    # ("ORB High", "bear", "REV"),       # loop C4: re-enabled bear REV at ORB High
    # ("Week High", "bear", "REV"),      # loop: re-enabled Phase 16b
}

# Per-symbol suppressions
SYMBOL_DISABLED = {
    "NVDA": {
        ("*", "bull", "REV"),   # v3.3d
    },
}

# ── Timing ──
SUPPRESS_AFTERNOON = True                # loop I1: suppress -EV afternoon
ORB_LOW_RECLAIM_MIDDAY_ONLY = False      # loop: ORB Low reclaim all timings

# ══════════════════════════════════════════════════════════════════════════════
# SIGNAL CLASSIFICATION
# ══════════════════════════════════════════════════════════════════════════════

def _is_midday(timing):
    return timing == "midday"

def _is_afternoon(timing):
    return timing == "afternoon"

def _check_symbol_suppression(symbol, level, direction, sig_type):
    """Check per-symbol suppression rules."""
    if symbol not in SYMBOL_DISABLED:
        return False
    for rule in SYMBOL_DISABLED[symbol]:
        rlevel, rdir, rtype = rule
        if (rlevel == "*" or rlevel == level) and rdir == direction and rtype == sig_type:
            return True
    return False


def classify_signal(row):
    """
    For a single catalog move, determine if KLB v3.6 would fire a signal.

    Args:
        row: pandas Series with catalog columns

    Returns:
        dict with keys: would_fire, signal_type, blocked_by, is_dimmed
    """
    level = row["nearest_level_type"]
    dist = row["nearest_level_dist_atr"]
    direction = row["direction"]
    symbol = row["symbol"]
    ema = row["trig_ema_aligned"]
    body = row["trig_body_pct"]
    vol = row["trig_vol_ratio"]
    adx = row["pre_adx"]
    vwap = row["trig_vwap_aligned"]
    timing = row["timing_category"]
    interaction = row["level_interaction"]
    pre_vol = row.get("pre_vol_avg_ratio", np.nan)
    trig_range = row.get("trig_range_atr", np.nan)
    spy_mag = row.get("spy_magnitude_atr", np.nan)

    # v3.7: VWAP Reclaim fields
    prev_above_vwap  = row.get("prev_close_above_vwap",  False)
    prev2_above_vwap = row.get("prev2_close_above_vwap", False)
    close_above_vwap = row.get("close_above_vwap",       False)

    # v3.7: SPY reclaim DIM fields
    spy_above_vwap      = row.get("spy_above_vwap",      False)
    spy_prev_above_vwap = row.get("spy_prev_above_vwap",  False)
    rs_vs_spy           = row.get("rs_vs_spy",            0.0)
    rs_leading          = rs_vs_spy > RS_LEADERSHIP_MIN

    result = {
        "would_fire": False,
        "signal_type": None,
        "blocked_by": [],
        "is_dimmed": False,
    }

    # ── Afternoon suppression (v3.5) ──
    if SUPPRESS_AFTERNOON and _is_afternoon(timing):
        result["blocked_by"].append("afternoon_suppressed")
        return result

    # ── Proximity check ──
    # v3.6: bear REV gets proximity tolerance
    prox = LEVEL_PROXIMITY_ATR
    if direction == "bear" and level in REV_BEAR_LEVELS:
        prox = max(LEVEL_PROXIMITY_ATR, REV_PROXIMITY_TOL)

    if dist > prox:
        result["blocked_by"].append("no_level_nearby")
        return result

    # ── Determine possible signal types ──
    is_brk = False
    is_rev_gated = False
    is_rev_ungated = False

    # Check disabled signals first
    if (level, direction, "REV") in DISABLED_SIGNALS:
        pass  # REV disabled for this combo
    elif _check_symbol_suppression(symbol, level, direction, "REV"):
        pass  # symbol-specific suppression
    else:
        if direction == "bull":
            if level in REV_BULL_LEVELS:
                if level in REV_LEVELS_UNGATED:
                    is_rev_ungated = True
                elif level in REV_LEVELS_GATED:
                    is_rev_gated = True
        else:
            if level in REV_BEAR_LEVELS:
                if level in REV_LEVELS_UNGATED:
                    is_rev_ungated = True
                elif level in REV_LEVELS_GATED:
                    is_rev_gated = True

    # ORB Low reclaim: midday only (v3.4)
    if level == "ORB Low" and direction == "bull" and ORB_LOW_RECLAIM_MIDDAY_ONLY:
        if is_rev_gated and not _is_midday(timing):
            is_rev_gated = False

    if direction == "bull":
        if level in BRK_BULL_LEVELS and interaction == "broke_through":
            is_brk = True
    else:
        if level in BRK_BEAR_LEVELS and interaction == "broke_through":
            is_brk = True

    if not is_brk and not is_rev_gated and not is_rev_ungated:
        result["blocked_by"].append("no_matching_signal_type")
        return result

    # ── Try each signal type, check gates ──
    # Priority: ungated REV > gated REV > BRK

    if is_rev_ungated:
        blocks = []
        if body < BODY_PCT_MIN:
            blocks.append("body_pct")
        if vol < REV_VOL_MIN:
            blocks.append("volume")
        if adx < ADX_MIN:
            blocks.append("adx")
        if not blocks:
            result["signal_type"] = "REV"
            result["would_fire"] = True
            result["is_dimmed"] = _check_dim(
                vol, pre_vol, trig_range, timing, spy_mag,
                spy_above_vwap=spy_above_vwap,
                spy_prev_above_vwap=spy_prev_above_vwap,
                rs_vs_spy=rs_vs_spy, direction=direction,
            )
            return result
        result["blocked_by"] = blocks

    if is_rev_gated:
        blocks = []
        if not ema and timing != "open_flush" and not rs_leading:
            blocks.append("ema_gate")
        if body < BODY_PCT_MIN:
            blocks.append("body_pct")
        if vol < REV_VOL_MIN:
            blocks.append("volume")
        if adx < ADX_MIN:
            blocks.append("adx")
        if not vwap and not (rs_leading and RS_LEADERSHIP_VWAP_SKIP):
            blocks.append("vwap_filter")
        if not blocks:
            result["signal_type"] = "REV"
            result["would_fire"] = True
            result["is_dimmed"] = _check_dim(
                vol, pre_vol, trig_range, timing, spy_mag,
                spy_above_vwap=spy_above_vwap,
                spy_prev_above_vwap=spy_prev_above_vwap,
                rs_vs_spy=rs_vs_spy, direction=direction,
            )
            return result
        if not result["blocked_by"]:
            result["blocked_by"] = blocks

    if is_brk:
        blocks = []
        if not ema and timing != "open_flush" and not rs_leading:
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
            result["is_dimmed"] = _check_dim(
                vol, pre_vol, trig_range, timing, spy_mag,
                spy_above_vwap=spy_above_vwap,
                spy_prev_above_vwap=spy_prev_above_vwap,
                rs_vs_spy=rs_vs_spy, direction=direction,
            )
            return result
        if not result["blocked_by"]:
            result["blocked_by"] = blocks

    # ── v3.7: VWAP Reclaim signal ──
    # 2 consecutive prev bars on one side → close crosses to other side
    if VWAP_RECLAIM_ENABLED and not result["would_fire"]:
        _vwap_needs_prev2 = VWAP_RECLAIM_MIN_BARS >= 2
        is_bull_reclaim = (
            direction == "bull"
            and close_above_vwap
            and not prev_above_vwap
            and (not _vwap_needs_prev2 or not prev2_above_vwap)
            and not _check_symbol_suppression(symbol, "VWAP", "bull", "VRC")
        )
        is_bear_reclaim = (
            direction == "bear"
            and not close_above_vwap
            and prev_above_vwap
            and (not _vwap_needs_prev2 or prev2_above_vwap)
        )
        if is_bull_reclaim or is_bear_reclaim:
            result["would_fire"] = True
            result["signal_type"] = "VRC"
            result["is_dimmed"] = _check_dim(
                vol, pre_vol, trig_range, timing, spy_mag,
                spy_above_vwap=spy_above_vwap,
                spy_prev_above_vwap=spy_prev_above_vwap,
                rs_vs_spy=rs_vs_spy, direction=direction,
            )

    return result


def _check_dim(vol, pre_vol, trig_range, timing, spy_mag,
               spy_above_vwap=False, spy_prev_above_vwap=False,
               rs_vs_spy=0.0, direction="bull"):
    """
    Check if signal should be dimmed (v3.3 quality filters).
    Returns False if a quality override (quiet coil, midday flat, broad coil) applies.
    """
    # ── v3.7: large-candle bypass — 2+ ATR bar = directional conviction, skip all dim ──
    if not np.isnan(trig_range) and trig_range >= BIG_CANDLE_ATR:
        return False

    # ── Quality overrides (cancel dim) ──
    is_quiet_coil = (
        not np.isnan(pre_vol) and pre_vol < QUIET_COIL_VOL_RAMP
        and not np.isnan(trig_range) and trig_range < QUIET_COIL_RANGE
    )
    if is_quiet_coil:
        return False

    is_midday_flat = _is_midday(timing)
    # Note: can't check EMA slope change from catalog — approximate with timing only
    if is_midday_flat:
        return False

    is_broad_coil = (
        not np.isnan(trig_range) and trig_range < BROAD_COIL_RANGE
        and not np.isnan(spy_mag) and abs(spy_mag) > BROAD_COIL_SPY_MIN * 100
        # spy_magnitude_atr is in ATR units, not pct — approximate
    )
    if is_broad_coil:
        return False

    # ── Dim conditions ──
    is_vol_exhaust = not np.isnan(vol) and vol > VOL_EXHAUSTION_MAX
    is_exhausted = (
        _is_afternoon(timing)
        # Can't fully check ATR consumed + SPY range from catalog
        # Approximate: afternoon = exhaustion signal
    )

    # v3.7: SPY sustained VWAP reclaim → dim bear signals in midday or outperforming
    is_spy_reclaim_dim = (
        direction == "bear"
        and spy_above_vwap and spy_prev_above_vwap
        and (_is_midday(timing) or rs_vs_spy > 0)
    )

    return is_vol_exhaust or is_exhausted  # loop H5: disable spy_reclaim_dim filter
