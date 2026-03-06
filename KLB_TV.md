Detects breakouts, reversals, reclaims, retests, fades, and range breakouts at key intraday levels on confirmed signal-TF candle closes. Designed for US equities on 1m/5m charts.

**Levels:** Premarket H/L, Yesterday H/L, Last Week H/L, ORB H/L, PD Mid, PD Last Hr Low, VWAP Lower Band (all toggleable).

**Six setup types:**
- **Breakout** — bar closes through key level. Green/red labels.
- **Reversal (~)** — wick enters zone, close rejects. Blue/orange labels.
- **Reclaim (~~)** — reversal after invalidated breakout. Brighter labels.
- **Retest (◆)** — price returns to broken level and holds. Configurable window.
- **FADE** — after CONF ✗, price crosses back through level within 30 min. Purple labels. Once per level.
- **RNG** — 12-bar range breakout + volume ≥ 3× avg. No EMA required. Teal labels. Once per direction.

**Filters (toggleable):**
- Volume (1.5x SMA), ATR Buffer, VWAP Directional, Once Per Breakout
- **Evidence Stack:** 5m EMA Alignment, EMA Hard Gate (suppresses non-EMA after 9:50 ET, dims before), RS vs SPY, ADX > 20, Candle Body Quality
- Filter Mode: Suppress (default) or Dim

**CONF system:** 3 signal-TF bar window. Auto-Confirm R1: EMA aligned = instant ✓ (no time restriction — HOLD is the gatekeeper). CONF ✗ triggers potential FADE. Auto-promotion ✓ on next breakout (green/red). High-conviction ✓★ (gold).

**Visual elements:**
- Regime Score R0/R1/R2 (EMA + VWAP alignment). R1 bulls dimmed.
- Runner Score ①-⑥: EMA, regime=2, vol ≥10×, morning, SPY-aligned, CONF pass.
- Glyphs: 🔇 vol drying, ⚡ big move (≥2x ATR), ⚠ body ≥80%.
- QBS (cyan), FADE (purple), RNG (teal) standalone signals.
- CHOP? warning after 3+ consecutive failures.
- Afternoon dimming after 11:00 ET.

**Trade management:** VWAP line (toggleable), SL reference lines (0.10/0.15 ATR), VWAP exit alert.

**Alerts:** Breakout, reversal, retest, failure, QBS, FADE, RNG, VWAP exit. 11 alertconditions for granular filtering. Use "Any alert() function call" for full coverage.

**Debug:** Signal table overlay + Pine Logs (`[KLB]` prefix). Off by default.

**Setup:** Add to chart (any TF ≤ Signal TF), enable Extended Trading Hours, add alert. Use 1m chart with 5m signals for detail without noise.
