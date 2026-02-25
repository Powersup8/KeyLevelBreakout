Detects breakouts, reversals, reclaims, and retests at key intraday levels on confirmed signal-TF candle closes. Designed for US equities on 1m/5m charts.

**Levels:** Premarket H/L, Yesterday H/L, Last Week H/L, ORB H/L (all toggleable).

**Four setup types:**

**Breakout** — signal-TF bar closes through a key level as a bullish/bearish candle, with prior bar(s) on the other side. Green/red labels.

**Reversal (~)** — wick enters level zone, close rejects back. Bull at LOW levels, bear at HIGH levels. Blue/orange labels. Setup Active Window only (default 9:30-11:30 ET).

**Reclaim (~~)** — reversal after a prior breakout was invalidated. "False breakout then rejection" pattern. Same colors, brighter.

**Retest (⟳)** — per-level tracking after breakout. Price dips back to broken level and holds on breakout side. Each retest shows bar count + PA quality: `⟳³ ORB H 2.1x ^85`.

**Level Zones:** Wick-to-body range for D/W (actual candle data), ATR-derived for PM/ORB. Toggleable. When Show Level Lines is on, shaded bands visualize zone width — wide band = strong rejection.

**Filters (toggleable):**
- **Volume** — above-average required (default 1.5x SMA). Directional 2-bar lookback.
- **ATR Buffer** — wick must push past level ± X% ATR(14), close holds beyond raw level.
- **Once Per Breakout** — one signal per level, re-arms on invalidation. Resets each session.

**Label format (line breaks):**
```
ORB H + Yest H
1.8x ^82
⟳³ ORB H 2.1x ^85
⟳⁷ Yest H 1.4x ^71
```
Line 1: level names (merged for confluence). Line 2: volume ratio + close position %. Line 3+: per-level retests with superscript bar count.

**Retest-Only Mode:** Suppress breakout labels (gray dot). Only retest signals fire their own labels and alerts. Reversals/reclaims unchanged.

**Post-Breakout Monitoring:** Each broken level tracked independently. Failure (✗) = price closes back through most conservative level. Auto-promotion (✓) when next breakout fires.

**Alerts:**
- Merged `alert()` per direction per bar (breakouts + reversals + retests)
- 7 `alertcondition()` entries for granular filtering
- Retest alerts: "Retest: ⟳³ ORB H 2.1x ^85"
- Failure alerts: "Failed: ORB H + Yest H"

**Setup:**
1. Add to chart (any TF <= Signal Timeframe)
2. Enable Extended Trading Hours (for premarket)
3. Add alert -> "Any alert() function call" for full coverage

**Signal Timeframe:** Breakouts evaluate on closed signal-TF bars (default 5m). Use 1m chart with 5m signals for detail without noise.
