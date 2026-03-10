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
BODY_PCT_MIN = 0.0            # autoklb exp6: remove body% gate entirely
VOL_RATIO_MIN = 0.0           # autoklb exp2: remove vol gate entirely
VOL_EXHAUSTION_MAX = 5.0       # v3.3: trigger vol > 5x → dim
ADX_MIN = 0.0                 # autoklb exp9: remove ADX gate entirely
LEVEL_PROXIMITY_ATR = 0.20     # autoklb exp12: wider proximity gate
FRESHNESS_MAX_TESTS = 3        # v3.3: 3rd+ test at same level → dim
ATR_CONSUMED_MAX = 1.5         # v3.3: afternoon exhaustion threshold
SPY_RANGE_EXHAUSTION = 0.008   # v3.3: SPY range > 0.8% in exhaustion check
REV_PROXIMITY_TOL = 0.03       # v3.6: bear REV fires within 0.03 ATR of level

# ── Quality override thresholds ──
QUIET_COIL_VOL_RAMP = 0.5     # v3.3: pre-vol ramp < 0.5 = drying
QUIET_COIL_RANGE = 0.5        # v3.3: trigger range < 0.5 ATR = small
MIDDAY_EMA_CHANGE = 0.02      # v3.3b: EMA change < 0.02 ATR in 30m = flat
BROAD_COIL_RANGE = 0.5        # v3.3b: trigger range < 0.5 ATR
BROAD_COIL_SPY_MIN = 0.003    # v3.3b: SPY moving > 0.3%

# ══════════════════════════════════════════════════════════════════════════════
# SIGNAL ROUTING — agent can modify these sets
# ══════════════════════════════════════════════════════════════════════════════

# BRK levels (barriers — price breaks through)
BRK_BEAR_LEVELS = {
    "PM Low", "PD Low", "Week Low", "ORB Low",
    "Week Open", "Month Open",
    "PD Last Hr Low", "PD Last Hr High",
}
BRK_BULL_LEVELS = {
    "Week Open", "Month Open",
    "PD Last Hr High",          # v3.4: added
}

# REV levels — EMA gated
REV_LEVELS_GATED = {
    "PM Low", "PD Low", "Week Low",             # bull REV at LOWs
    "PD Last Hr Low",                            # bull REV
    # NOTE: PM High, PD High, Week High, ORB High removed — bull REV suppressed v3.3c
}

# REV levels — ungated (no EMA, no VWAP)
REV_LEVELS_UNGATED = {
    "PD Mid", "Today Open", "PD Close",
}

# Direction routing
REV_BULL_LEVELS = {
    "PM Low", "PD Low", "Week Low",             # bull REV at LOWs (gated)
    "PD Last Hr Low",                            # bull REV (gated)
    "PD Mid", "Today Open", "PD Close",          # magnet REV (ungated)
    # v3.3c: PM High, PD High, Week High, ORB High REMOVED for bull REV
}

REV_BEAR_LEVELS = {
    "PM High", "PD High", "Week High", "ORB High",  # bear REV (EXREV) — kept
    "PD Mid", "Today Open", "PD Close",               # magnet REV (ungated)
}

# ── Suppressions ──
DISABLED_SIGNALS = {
    ("ORB Low", "bull", "REV"),          # v3.2: disabled
    ("PM High", "bull", "REV"),          # v3.3c: bull REV at HIGHs suppressed
    ("PD High", "bull", "REV"),          # v3.3c
    ("Week High", "bull", "REV"),        # v3.3c
    ("ORB High", "bull", "REV"),         # v3.3c
}

# Per-symbol suppressions
SYMBOL_DISABLED = {
    "NVDA": {("*", "bull", "REV")},      # v3.3d: all NVDA bull REV suppressed
}

# ── Timing ──
SUPPRESS_AFTERNOON = False               # v3.5: toggleable, default off
ORB_LOW_RECLAIM_MIDDAY_ONLY = True       # v3.4: ORB Low bull REV = midday only

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
        if vol < VOL_RATIO_MIN:
            blocks.append("volume")
        if adx < ADX_MIN:
            blocks.append("adx")
        if not blocks:
            result["signal_type"] = "REV"
            result["would_fire"] = True
            result["is_dimmed"] = _check_dim(vol, pre_vol, trig_range, timing, spy_mag)
            return result
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
        if not vwap:
            blocks.append("vwap_filter")
        if not blocks:
            result["signal_type"] = "REV"
            result["would_fire"] = True
            result["is_dimmed"] = _check_dim(vol, pre_vol, trig_range, timing, spy_mag)
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
            result["is_dimmed"] = _check_dim(vol, pre_vol, trig_range, timing, spy_mag)
            return result
        if not result["blocked_by"]:
            result["blocked_by"] = blocks

    return result


def _check_dim(vol, pre_vol, trig_range, timing, spy_mag):
    """
    Check if signal should be dimmed (v3.3 quality filters).
    Returns False if a quality override (quiet coil, midday flat, broad coil) applies.
    """
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

    return is_vol_exhaust or is_exhausted
