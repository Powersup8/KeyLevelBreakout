Detects breakouts, reversals, and reclaims at key intraday levels on confirmed signal-TF candle closes. Designed for US equities on 1m/5m charts.

**Levels tracked:** Premarket High/Low, Yesterday High/Low, Last Week High/Low, ORB High/Low (all toggleable).

**Three setup types:**

**Breakout (Continuation)** — signal-TF bar closes through a key level as a bullish/bearish candle, with prior bar(s) on the other side. Green/red labels.

**Reversal (~)** — wick enters a level zone but close rejects back. Bullish reversals fire at LOW levels, bearish at HIGH levels. Blue/orange labels. Only fires within the Setup Active Window (default 9:30-11:30 ET).

**Reclaim (~~)** — a reversal that fires after a prior breakout at the same level was invalidated. The "false breakout then rejection" pattern. Same blue/orange labels, brighter.

**Level Zones:** Each level becomes a range (wick-to-body) instead of a single price. Daily/weekly use actual candle body data. PM/ORB use ATR-derived width. Toggleable — when off, levels are single lines.

**Filters (all toggleable):**
- **Volume** — requires above-average volume (default 1.5x SMA). Directional 2-bar lookback borrows prior bar's volume only if same direction.
- **ATR Buffer** — wick must push past level +/- X% of daily ATR(14), close holds beyond raw level.
- **Once Per Breakout** — one signal per level, re-arms on invalidation. Resets each session.

**Label format:** `PM H 2.1x ^78` / `~ Yest L 1.8x ^72` / `~~ Yest H 2.3x v85`
- Level name (merged for confluence), volume ratio, close position %
- Label opacity scales with volume conviction

**Post-Breakout Confirmation:**
After a breakout fires, chart-TF bars are monitored:
- **checkmark** = follow-through (held N bars)
- **retest checkmark** = pulled back to level and held
- **X** = failed (closed back through, label turns gray)

**Alerts:**
- Merged `alert()` per direction per bar (breakouts + reversals)
- 7 `alertcondition()` entries for granular filtering
- Confirmation alerts: "Confirmed: ..." / "Failed: ..."

**Setup:**
1. Add to chart (any TF <= Signal Timeframe)
2. Enable Extended Trading Hours (for premarket)
3. Add alert -> "Any alert() function call" for full coverage

**Signal Timeframe:** Breakouts evaluate on closed signal-TF bars (default 5m). Use 1m chart with 5m signals for detail without noise.
