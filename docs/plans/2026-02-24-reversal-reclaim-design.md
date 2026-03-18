# KeyLevelBreakout v1.7 — Reversal + Reclaim + Zone Setups

**Date:** 2026-02-24
**Status:** Approved for implementation
**Source:** PDH/PDL strategy video analysis (continuation, reversal, reclaim setups at key levels)

---

## Summary

Add two new signal types (Reversal, Reclaim) alongside the existing Continuation (breakout) signals in `KeyLevelBreakout.pine`. Introduce a "zone" concept (wick-to-body) for levels, replacing the single-price approach. All new features are toggleable; when disabled, behavior is identical to v1.6.

## Decisions

| Question | Decision |
|----------|----------|
| Architecture | Inside KeyLevelBreakout.pine (shared infrastructure) |
| Setups | All three: Continuation (refined), Reversal, Reclaim |
| Zone concept | Wick-to-body for D/W levels, ATR-derived for PM/ORB. Toggleable. |
| Time filter | 120-min window (9:30-11:30 ET) for Reversal/Reclaim only |
| Level scope | Toggleable per level type for Reversal/Reclaim |
| Approach | Integrated pipeline (~120 new lines) |

## New Inputs

```pine
// Group "Setups"
i_showReversal = input.bool(true,  "Show Reversal Setups")
i_showReclaim  = input.bool(true,  "Show Reclaim Setups")
i_setupWindow  = input.string("0930-1130", "Setup Active Window (ET)")

// Group "Zones"
i_useZones     = input.bool(true,  "Use Level Zones (wick-to-body)")
i_zoneATRPct   = input.float(3.0,  "Zone Width for PM/ORB (% of ATR)")

// Group "Reversal/Reclaim Toggles"
i_revPM   = input.bool(true, "PM H/L Reversal/Reclaim")
i_revYest = input.bool(true, "Yesterday H/L Reversal/Reclaim")
i_revWeek = input.bool(true, "Last Week H/L Reversal/Reclaim")
i_revORB  = input.bool(true, "ORB H/L Reversal/Reclaim")
```

## Zone Data

### Daily/Weekly — real body-to-wick zones

Expand existing `request.security` calls into tuples (net reduction from 4 calls to 2):

```pine
[yestHigh, yestLow, yestOpen, yestClose] = request.security(syminfo.tickerid, "D",
     [high[1], low[1], open[1], close[1]], lookahead = barmerge.lookahead_on)
[weekHigh, weekLow, weekOpen, weekClose] = request.security(syminfo.tickerid, "W",
     [high[1], low[1], open[1], close[1]], lookahead = barmerge.lookahead_on)
```

Zone computation:
```pine
// Yesterday High zone: body top → wick high
yestHBody = math.max(yestOpen, yestClose)
// Yesterday Low zone: wick low → body bottom
yestLBody = math.min(yestOpen, yestClose)
```

### PM/ORB — ATR-derived zones

No natural candle body, so derive zone width from ATR:
```pine
zoneWidth = dailyATR * i_zoneATRPct / 100
pmHBody   = pmHigh - zoneWidth
pmLBody   = pmLow  + zoneWidth
orbHBody  = orbHigh - zoneWidth
orbLBody  = orbLow  + zoneWidth
```

### Zones OFF fallback

When `i_useZones = false`: body edge = wick edge (zone collapses to single line). Existing breakout behavior with ATR buffer is preserved exactly.

## Setup Detection

### Reversal (single-bar pattern on signal TF)

Reversal at HIGH = bearish, at LOW = bullish (opposite of breakout):

```pine
bullReversal at LOW level (e.g., Yest L):
  - sigL <= zoneLBody            // wick dipped into the zone
  - sigC > zoneLBody             // close rejected above body edge
  - sigC > sigO                  // bullish candle
  - volPassBull                  // volume filter
  - isSetupWindow                // within active time window

bearReversal at HIGH level (e.g., Yest H):
  - sigH >= zoneHBody            // wick pushed into the zone
  - sigC < zoneHBody             // close rejected below body edge
  - sigC < sigO                  // bearish candle
  - volPassBear                  // volume filter
  - isSetupWindow                // within active time window
```

### Reclaim (context-enriched Reversal)

One extra state variable per level:
```pine
var bool hadBreakYH = false  // "was this level broken before this session?"
```

Lifecycle:
1. Breakout fires at Yest H → `xYH := true` (existing)
2. Price closes back below → `xYH := false` (existing re-arm) + `hadBreakYH := true` (NEW)
3. Reversal fires at Yest H → check `hadBreakYH`:
   - `true` → label as Reclaim ("break was a fake-out, level reclaimed")
   - `false` → label as plain Reversal

Reclaim state resets each session.

### Continuation (refined breakout)

When zones ON: breakout requires wick to clear the zone's outer edge (the wick tip). This replaces the ATR buffer's role — the zone IS the buffer. Close must hold beyond the raw level (unchanged).

When zones OFF: identical to current `bullBreak()` with ATR buffer.

## Time Window

```pine
isSetupWindow = not na(time(timeframe.period, i_setupWindow + ":23456", TZ))
```

- Reversal/Reclaim: only fire when `isSetupWindow == true`
- Continuation (breakout): fires anytime during regular session (unchanged)

## Labels & Visual Differentiation

| Setup | Bull Label | Bear Label | Color |
|-------|-----------|-----------|-------|
| Continuation | `Yest H 2.1x ^78` | `Yest L 1.8x v82` | Green / Red (existing) |
| Reversal | `~ Yest L 2.1x ^78` | `~ Yest H 1.8x v82` | Blue / Orange |
| Reclaim | `~~ Yest L 2.1x ^78` | `~~ Yest H 1.8x v82` | Blue / Orange (brighter) |

Note: Unicode characters may need testing on TradingView. Fallback to ASCII `~` / `~~` if needed.

## Alerts

Programmatic alerts (merged per direction per bar):
```
"Bullish reversal: ~ Yest L 2.1x ^78"
"Bearish reclaim: ~~ Yest H 1.8x v82"
```

New alertconditions:
- "Any Reversal"
- "Any Reclaim"
- "Any Setup" (breakout + reversal + reclaim)

## Signal Flags

Reversal/Reclaim get their own flags (`rPMH`, `rPML`, etc.) — independent from breakout flags (`xPMH`, `xPML`). Each fires once per level per session, re-arms when price moves away from the zone.

## Regression Safety

Every new feature is behind a toggle. When all new toggles are OFF:

| Component | Impact |
|-----------|--------|
| `bullBreak()` / `bearBreak()` | Unchanged |
| Breakout signals + flags | Unchanged |
| Post-breakout confirmation | Unchanged |
| Existing labels + colors | Unchanged |
| Existing alerts | Unchanged |
| Level lines | Unchanged |

The only change visible when all new features are OFF: `request.security` for D/W now returns tuples (more data fetched, but not used). No functional difference.

## Estimated Size

~120 new lines. File grows from 391 → ~510 lines.

## Files Modified

| File | Changes |
|------|---------|
| `KeyLevelBreakout.pine` | New inputs, zone data, reversal/reclaim helpers, signal evaluation, labels, alerts |
| `KeyLevelBreakout.md` | New sections for Reversal, Reclaim, Zones; updated inputs table; v1.7 changelog |
| `KeyLevelBreakout_Improvements.md` | Status updates |
