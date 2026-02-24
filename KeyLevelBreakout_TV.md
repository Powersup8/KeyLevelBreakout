Detects breakouts through key intraday levels on confirmed signal-TF candle closes. Designed for US equities on 1m/5m charts.

**Levels tracked:** Premarket High/Low, Yesterday High/Low, Last Week High/Low, ORB High/Low (all toggleable).

**How it works:**
A breakout fires when a completed signal-TF bar (default 5m) closes through a key level as a bullish/bearish candle, with the prior bar(s) on the opposite side. Labels appear directly on the chart with volume and conviction data.

**Filters (all toggleable):**
- **Volume** — requires above-average volume (default 1.5x SMA). Uses directional 2-bar lookback: borrows prior bar's volume only if it was moving in the same direction as the breakout.
- **ATR Buffer** — wick must push past level +/- X% of daily ATR(14), while close only needs to hold beyond the raw level. Separates momentum (wick) from conviction (close).
- **Once Per Breakout** — one signal per level, re-arms when price closes back through with a smaller ATR buffer. Resets each session.

**Label format:** `PM H 2.1x ^78`
- `PM H` = level name (merged for confluence: `PM H + Yest H`)
- `2.1x` = volume ratio vs baseline
- `^78` = close position (78% toward the high = strong buying pressure)
- Label opacity scales with volume conviction (bright = strong, faded = borderline)

**Post-Breakout Confirmation:**
After a breakout fires, subsequent chart-TF bars are monitored. The label updates with:
- **checkmark** = follow-through (price held for N bars)
- **retest checkmark** = price pulled back to the level and held (broken resistance became support)
- **X** = failed (price closed back through, label turns gray)

Fires separate "Confirmed" / "Failed" alerts.

**Alerts:**
- One merged `alert()` per direction per bar (e.g. "Bullish breakout: PM H + Yest H 2.1x ^78")
- 3 `alertcondition()` entries: "Any Bullish", "Any Bearish", "Any Breakout"
- Confirmation alerts: "Confirmed: ..." / "Failed: ..."

**Setup:**
1. Add to chart (works on any TF <= Signal Timeframe)
2. Enable Extended Trading Hours (required for premarket)
3. Add alert -> "Any alert() function call" for full coverage

**Signal Timeframe:** Breakouts evaluate on closed bars of the chosen TF (default 5m). Use a 1m chart with 5m signals for more detail while avoiding noise.
