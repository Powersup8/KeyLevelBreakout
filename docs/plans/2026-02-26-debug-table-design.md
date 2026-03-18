# Debug Signal Table — Design Document

**Date:** 2026-02-26
**Status:** Approved
**Indicator:** KeyLevelBreakout.pine (v2.0 → v2.1)

---

## Problem

Reading label text from charts is tedious and error-prone. Labels overlap, text is small, timestamps require zooming in with grid lines. Post-session analysis of signal quality currently requires manual CSV export + label-by-label verification — the SPY analysis on Feb 25 took 20+ minutes for 6 labels.

## Solution

Dual-output debug system: a **chart table** (compact, visual) + **Pine Logs** (`log.info()`, full data export). Both togglable independently. Zero overhead when OFF.

## Architecture: Approach A — Parallel Array Storage

Signals are stored in typed `var` arrays as they fire. The chart table renders once on `barstate.islast` from the last N entries. `log.info()` fires immediately when each signal fires (no limit).

### Design Decisions

1. **Why parallel arrays (not a single string array)?** Each column has its own type (`int`/`float`/`string`), making table cell formatting and color-coding straightforward. Extending with new columns is trivial — add one array + one push/one cell.

2. **Why render on `barstate.islast` (not per-bar)?** Chart tables are expensive to create/delete. Rendering once on the last bar is standard practice for Pine info tables.

3. **Why `log.info()` fires at signal time (not on last bar)?** Log entries should capture the exact moment with full context. If the script errors before `barstate.islast`, log entries from earlier signals are still preserved.

4. **Why separate table vs log column sets?** Table width is limited (~8 columns max before readability suffers). Log output has no width limit. Core + OHLC for table; everything for log.

---

## New Inputs (Debug group)

```pine
i_debugTable = input.bool(false, "Show Signal Table",        group="Debug")
i_debugLog   = input.bool(false, "Log Signals (Pine Logs)",  group="Debug")
i_debugPos   = input.string("bottom_right", "Table Position",
    options=["top_left","top_center","top_right",
             "bottom_left","bottom_center","bottom_right"], group="Debug")
i_debugRows  = input.int(20, "Max Table Rows", minval=5, maxval=50, group="Debug")
```

Both OFF by default. Position configurable. Max rows controls table density.

---

## Data Arrays (13 total)

### Table arrays (8 columns)

| Array | Type | Content | Example |
|-------|------|---------|---------|
| `dbTime` | `int` | Bar timestamp (UNIX) | `1740500040` |
| `dbDir` | `string` | Direction symbol | `"▲"` / `"▼"` |
| `dbType` | `string` | Setup type | `"BRK"` / `"~"` / `"~~"` / `"◆"` |
| `dbLevels` | `string` | Level names | `"PM H + Week H"` |
| `dbVol` | `float` | Volume ratio | `9.3` |
| `dbClsPos` | `int` | Close position % | `66` |
| `dbConf` | `string` | Confirmation state | `"…"` / `"✓"` / `"✗"` / `"—"` |
| `dbOHLC` | `string` | Condensed OHLC | `"O690.19 H691.23 L690.10 C690.85"` |

### Log-only arrays (5 additional)

| Array | Type | Content |
|-------|------|---------|
| `dbATR` | `float` | ATR(14) at signal time |
| `dbVolRaw` | `float` | Raw volume value |
| `dbVolSMA` | `float` | Volume SMA baseline |
| `dbBuffer` | `float` | ATR buffer value |
| `dbLevelPrices` | `string` | Level prices (e.g., `"690.74 / 693.69"`) |

### Confirmation tracking

```pine
var int dbConfBullIdx = -1   // array index of last bull breakout
var int dbConfBearIdx = -1   // array index of last bear breakout
```

**Confirmation state rules:**
- Breakout fires → push `"…"` (monitoring), save array index
- Confirmed (window expiry, auto-promote) → `array.set(dbConf, savedIdx, "✓")`
- Failed (close back through level) → `array.set(dbConf, savedIdx, "✗")`
- Reversals / reclaims / retests → push `"—"` (not applicable)

---

## Append Points

Signals are appended at 4 locations in the existing code:

1. **Bull combined label block** (~line 572) — breakout and/or reversal/reclaim
2. **Bear combined label block** (~line 670) — breakout and/or reversal/reclaim
3. **Bull retest detection** (~line 781) — ◆ retest signals
4. **Bear retest detection** (~line 815) — ◆ retest signals

A helper function `dbAppend(...)` handles all array pushes + `log.info()` to avoid duplication.

---

## Table Layout (8 columns)

```
┌──────┬───┬─────┬──────────────┬─────┬─────┬────┬──────────────────────────┐
│ Time │Dir│Type │ Levels       │ Vol │ Pos │Conf│ OHLC                     │
├──────┼───┼─────┼──────────────┼─────┼─────┼────┼──────────────────────────┤
│09:34 │ ▲ │ BRK │PM H + Week H │ 9.3x│ ^66 │ ✓  │O690.19 H691.23 L690.10.. │
│09:34 │ ▲ │  ~  │ ORB L        │ 9.3x│ ^66 │ —  │O690.19 H691.23 L690.10.. │
│09:44 │ ▼ │  ~  │ ORB H        │ 5.2x│ v58 │ —  │...                        │
│09:45 │ ▲ │  ◆  │ PM H         │ 5.2x│ ^42 │ —  │...                        │
│09:49 │ ▲ │ BRK │ ORB H        │ 1.8x│ ^78 │ ✗  │...                        │
│10:00 │ ▲ │  ◆  │ ORB H        │ 2.6x│ ^72 │ —  │...                        │
│10:04 │ ▼ │ ~~  │ ORB H        │ 2.5x│ v97 │ —  │...                        │
└──────┴───┴─────┴──────────────┴─────┴─────┴────┴──────────────────────────┘
```

**Color coding:**
- Header row: dark gray background, white text
- BRK bull rows: light green background
- BRK bear rows: light red background
- `~` / `~~` bull rows: light aqua background
- `~` / `~~` bear rows: light orange background
- `◆` retest rows: same as parent breakout direction
- Failed (✗) rows: gray text

Shows the last `i_debugRows` entries (most recent at bottom).

---

## Log Format

Fires `log.info()` immediately at signal time. Prefix `[KLB]` for easy filtering in Pine Logs panel.

### Signal log entries:
```
[KLB] 09:34 Bull BRK PM_H+Week_H vol=9.3 pos=66 O=690.19 H=691.23 L=690.10 C=690.85 ATR=1.25 rawVol=4521000 volSMA=486000 buf=0.06 prices=690.74/693.69
[KLB] 09:34 Bull ~ ORB_L vol=9.3 pos=66 O=690.19 H=691.23 L=690.10 C=690.85 ATR=1.25 rawVol=4521000 volSMA=486000 buf=0.06 prices=690.10
[KLB] 09:45 Bull ◆ PM_H vol=5.2 pos=42 O=690.73 H=691.32 L=690.63 C=690.92 ATR=1.25
```

### Confirmation change log entries:
```
[KLB] CONF 09:34 Bull BRK PM_H+Week_H → ✓
[KLB] CONF 09:49 Bull BRK ORB_H → ✗
```

---

## Impact

| Aspect | Detail |
|--------|--------|
| New lines | ~70-80 |
| Existing logic | Untouched — debug system observes, doesn't modify |
| Performance (OFF) | 13 empty array declarations only |
| Performance (ON) | Array pushes at signal time + table render on last bar |
| Files modified | `KeyLevelBreakout.pine` only |
| `request.security` | No new calls |

---

## Files Modified

| File | Changes |
|------|---------|
| `KeyLevelBreakout.pine` | New Debug inputs, array declarations, `dbAppend()` helper, `dbLog()` helper, 4 append call sites, table render block, confirmation state updates |
| `KeyLevelBreakout.md` | New Debug section in docs |
| `KeyLevelBreakout_Improvements.md` | Mark #11 as implemented |
