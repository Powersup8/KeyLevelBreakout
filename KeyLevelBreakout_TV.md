Detects breakouts, reversals, reclaims, and retests at key intraday levels on confirmed signal-TF candle closes. Designed for US equities on 1m/5m charts.

**Levels:** Premarket H/L, Yesterday H/L, Last Week H/L, ORB H/L (all toggleable).

**Four setup types:**

**Breakout** — signal-TF bar closes through a key level as a bullish/bearish candle, with prior bar(s) on the other side. Green/red labels.

**Reversal (~)** — wick enters level zone, close rejects back. Bull at LOW levels, bear at HIGH levels. Blue/orange labels. Fires all session by default; optionally limited to Setup Active Window.

**Reclaim (~~)** — reversal after a prior breakout was invalidated. "False breakout then rejection" pattern. Same colors, brighter.

**Retest (◆)** — per-level tracking after breakout, eligible from the very next chart bar. Price dips back to broken level (within configurable proximity) and holds on breakout side. Early retests (1-2 bars) are stronger signals. Independent label at retest bar + updates original breakout label. Configurable window: Short (50 min), Extended (2.5 hr), or Session (until invalidated). Format: `◆³ ORB H 2.1x ^85`.

**Level Zones:** Wick-to-body range for D/W (actual candle data), ATR-derived for PM/ORB. Toggleable. When Show Level Lines is on, shaded bands visualize zone width — wide band = strong rejection.

**Filters (toggleable):**
- **Volume** — above-average required (default 1.5x SMA). Directional 2-bar lookback.
- **ATR Buffer** — wick must push past level ± X% ATR(14), close holds beyond raw level.
- **VWAP Directional Filter** — suppress counter-trend reversals (bear above VWAP, bull below VWAP). On by default.
- **Once Per Breakout** — one signal per level, re-arms on invalidation. Resets each session.

**Label management:**
- Same-bar breakout + reversal in same direction → merged into one label
- Cooldown dimming: rapid same-direction signals within N bars render dimmer/smaller (default 2 signal bars)
- Vertical offset: adjacent labels shifted by ATR to prevent overlap

**Label format (line breaks):**
```
ORB H + Yest H
1.8x ^82
◆³ ORB H 2.1x ^85
◆⁷ Yest H 1.4x ^71
```
Line 1: level names (merged for confluence). Line 2: volume ratio + close position %. Line 3+: per-level retests with superscript bar count.

**Retest-Only Mode:** Suppress breakout labels (gray dot). Only retest signals fire their own labels and alerts. Reversals/reclaims unchanged.

**Post-Breakout Monitoring:** Breakout signals evaluated on signal-TF bars — labels are identical on 1m and 5m charts. Each broken level tracked independently. Retest detection runs on chart-TF bars for precision. Failure (✗) = close back through most conservative level, label grayed out. Auto-promotion (✓) when next breakout fires — label turns lime green. High-conviction (✓★, ≥5x vol + ≥80% close pos) turns gold.

**Visual Quality Tiers:**
- **CONF ✓** (lime green) — confirmed breakout, strong follow-through signal
- **CONF ✓★** (gold) — high-conviction confirmation (54% win, 0% loss in 6-week analysis)
- **CONF ✗** (gray) — failed confirmation
- **Afternoon signals** — dimmed after 11:00 ET (near-zero follow-through)
- **CHOP?** (orange) — warning after 3+ consecutive CONF failures at session start

**Alerts:**
- Merged `alert()` per direction per bar (breakouts + reversals)
- Retest alerts fire in all modes: "Retest: ◆³ ORB H 2.1x ^85"
- Failure alerts: "Failed: ORB H + Yest H"
- Reversal alerts: "Bullish reversal: ~ PM L 1.9x ^75"
- 7 `alertcondition()` entries for granular filtering

**Debug (togglable, off by default):**
- **Signal Table** — chart overlay with Time, Dir, Type, Levels, Vol, Pos, Conf, OHLC columns; color-coded by setup type; configurable position and max rows
- **Pine Logs** — `log.info()` with `[KLB]` prefix; full signal data + extended fields (ATR, raw volume, SMA, buffer, level prices) + confirmation state changes; one entry per confirmed bar (no real-time tick spam)

**Setup:**
1. Add to chart (any TF <= Signal Timeframe)
2. Enable Extended Trading Hours (for premarket)
3. Add alert -> "Any alert() function call" for full coverage

**Signal Timeframe:** All signals and failures evaluate on closed signal-TF bars (default 5m). Retest detection uses chart-TF bars for wick precision. Use 1m chart with 5m signals for detail without noise — labels are identical regardless of chart timeframe.
