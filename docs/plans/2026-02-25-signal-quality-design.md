# KeyLevelBreakout v2.0 — Signal Quality Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reduce noise (counter-trend reversals, label clustering) and catch more good signals (late retests, afternoon reversals).

**Source:** Analysis of 8 stocks (SPY, MSFT, QQQ, NVDA, TSLA, TSM, AMD, GOOGL) on 1m/5m charts, 2026-02-25.

---

## 1. Retest System Overhaul

**Problem:** Retests expire after 10 signal bars (~50 min). Most high-quality retests happen 1-2 hours later. After ~10:30, the indicator goes silent.

**Design:**

- **Detection runs every chart bar** (not `newSigBar`-gated). Uses chart-TF `close`/`high`/`low` for 1m precision on 1m charts.
- **Bull retest:** `low <= level + retestBuf and close > level`. Candle direction irrelevant.
- **Bear retest:** `high >= level - retestBuf and close < level`.
- **Window dropdown:** `Short (50 min)` / `Extended (2.5 hr)` / `Session` — replaces numeric input.
  - Short = 10 signal bars, Extended = 30 signal bars, Session = until invalidated or close.
- **Invalidation:** `close < level - rearmBuf` (bull) or `close > level + rearmBuf` (bear) → stop tracking, mark failure. Runs on chart-TF bars.
- **Own label:** Retest creates independent label at the retest bar. Format: `◆ ORB H\n2.1x ^85`. Also updates original breakout label.
- **Alert:** `alert("Retest: ◆ ORB H 2.1x ^85")` fires in normal mode (not just retest-only).
- **Symbol:** `◆` (diamond) for retest, `✗` for failure.
- **Proximity input:** `Retest Proximity (% of ATR)` (default 3%).

## 2. Reversal Time Window — Optional

**Problem:** Setup window 0930-1130 misses all afternoon reversals. GOOGL PM Low bounce at 12:00+ was missed.

**Design:**

- New toggle: `Limit Reversal Window` (default OFF).
- When OFF → reversals fire during entire regular session (0930-1600).
- When ON → existing `Setup Active Window` input controls the window.
- Existing time input remains visible for traders who want the focused window.

## 3. Label Management

**Problem:** Label clustering at open (3-5 labels in 15 min), overlapping labels from different setup types.

### 3a. Same-Bar Merge

Breakout + reversal firing on the same signal bar in the same direction → ONE combined label.
```
ORB H + ~ PM L
2.1x ^82
```

### 3b. Cooldown Dimming

After any signal fires in a direction, subsequent same-direction signals within N signal bars (default 2 = 10 min at 5m) render **dimmer**: higher alpha, `size.tiny`. Not suppressed — still visible.

State: `var int lastBullSigBar = 0`, `var int lastBearSigBar = 0`.

### 3c. Vertical Offset on Overlap

When a label lands within 1 bar of an existing same-direction label, use `yloc.price` with ATR-based vertical offset:
- Bull labels: `low - 0.15 * dailyATR`, second at `low - 0.30 * dailyATR`
- Bear labels: `high + 0.15 * dailyATR`, second at `high + 0.30 * dailyATR`

Track last few label bar_index values per direction to detect proximity.

## 4. VWAP Directional Filter

**Problem:** Counter-trend reversals are the #1 noise source. Bear reversals above VWAP during bullish sessions fail consistently.

**Design:**

- `vwapVal = ta.vwap` (Pine v6 built-in).
- Gate on **reversal helpers only** — breakouts unaffected.
- Bull reversal: suppressed when `sigC < vwapVal` (price below VWAP = bearish session, don't buy).
- Bear reversal: suppressed when `sigC > vwapVal` (price above VWAP = bullish session, don't sell).
- Input: `VWAP Directional Filter (reversals)` (default OFF).
- Default OFF preserves existing behavior.

## Files Modified

| File | Changes |
|------|---------|
| `KeyLevelBreakout.pine` | All 4 features |
| `KeyLevelBreakout.md` | Feature descriptions, inputs table, changelog |
| `KeyLevelBreakout_TV.md` | TradingView description update |
| `KeyLevelBreakout_Improvements.md` | Status updates |

## Implementation Order

1. VWAP filter (smallest, already partially in code)
2. Reversal window toggle (simple)
3. Retest overhaul (largest change)
4. Label management (merge + cooldown + offset)
