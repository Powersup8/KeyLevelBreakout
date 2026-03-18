# Exit Timing & Momentum Persistence Research

Compiled March 2026. Sources: academic papers (2024-2025), quant blogs, practitioner platforms.

---

## 1. How Long Does Intraday Breakout Momentum Persist?

- **Zarattini, Aziz & Barbon (2024, SSRN 4824172):** Intraday momentum on SPY persists long enough for same-day trend-following to yield 19.6% annualized / Sharpe 1.33 (2007-2024). Positions entered on abnormal demand/supply imbalance, exited at close.
- **Maroy (2025, SSRN 5095349):** Improved the above with VWAP-based exits achieving Sharpe >3.0 and >50% annualized. VWAP acts as a natural momentum-exhaustion signal.
- **QuantifiedStrategies ORB backtest:** Best ORB result on S&P 500 = 0.04% avg/trade with EOD exit; enhanced with daily filters = 0.27% avg/trade, 65% win rate on NQ futures.
- **Wang & Gangwar (2025, SSRN 5198458):** NSE block-based ORB tested 5/15/30-min ranges with 2, 3, and 5-bar holding periods. 5-min ORB performed best.
- **Practitioner consensus:** Breakout momentum is strongest in the first 30-60 minutes post-breakout. Volume fades by lunch; most daily highs/lows occur in first 30 min (~35%) or last 30 min.

**Key number:** The tradeable momentum window for intraday breakouts is roughly 30-120 minutes. After that, mean reversion dominates.

## 2. Optimal Trailing Stop Method

| Method | Best For | Settings | Backtest Notes |
|--------|----------|----------|----------------|
| **ATR trailing** | Intraday breakouts | 7-10 period ATR, 1.5-2.0x multiplier | 43% win rate on Dow 30 (297 stock-years). Standard choice. |
| **Chandelier exit** | Swing/trend | 3x ATR from period high | Underperformed % trailing in multi-year backtest (decodingmarkets.com) |
| **% trailing stop** | Trend capture | 20-25% from peak | Best long-term trend capture in comparative backtest |
| **Parabolic SAR** | Short momentum | Default (0.02/0.2) | Tightens too fast for breakouts; better for scalps |
| **VWAP-based exit** | Intraday momentum | Exit on VWAP cross | Sharpe >3.0 in Maroy (2025); best pure intraday exit |
| **Time-based (EOD)** | ORB strategies | Close at session end | Simple, avoids overnight; baseline for all ORB research |

**Recommendation for intraday breakouts:** ATR trailing (1.5-2x, 7-10 period) for the stop, with VWAP cross as the primary exit signal. Move stop to breakeven at +0.5 ATR profit.

## 3. MFE/MAE Analysis Best Practice

**Origin:** John Sweeney (1997, Wiley) — MAE identifies the drawdown threshold beyond which trades rarely recover. MFE identifies the profit peak you should be capturing.

**How professionals use MFE paths:**
1. **Plot MFE vs. Closed P&L scatter** — if MFE >> Closed P&L, exits are too late (giving back profit). Target: capture 60-80% of MFE.
2. **Exit Efficiency = Closed P&L / MFE** — measures what % of the available move you actually took. Track per-strategy.
3. **MFE duration scatter** — plot time-to-MFE vs. MFE magnitude. Identifies when trades peak.
4. **MAE threshold** — find the MAE level where winning trades stop appearing. Set stop just beyond that.
5. **R-multiple framing** — express MFE/MAE in risk units (R), not dollars. E.g., MFE = 3R, MAE = -0.5R.

**Key finding (TradesViz):** Trades need >5 minutes on average to reach MFE. Losses cluster at the 0-5 minute mark. Implication: don't exit breakout trades in the first 5 minutes unless stop is hit.

## 4. Typical Giveback Percentage

Hard empirical numbers on giveback are scarce in public literature. Practitioner-sourced estimates:

- **Breakout-and-run trades (TradeThisSwing):** Profit targets of 2-3x risk; sell in thirds as stock surges, implying 30-50% giveback if trailing with a single exit.
- **ORB strategies:** With EOD exit, giveback from intraday MFE averages 30-50% (implied by 0.04% avg closed P&L vs larger intraday swings).
- **Prop firm trailing drawdowns:** Real-time trailing stops set at $500 from a $3,000 peak = 83% giveback tolerance. This is too loose for breakouts.
- **Rule of thumb:** Well-managed breakout trades should give back 20-40% of MFE. If Exit Efficiency (Closed P&L / MFE) is consistently below 50%, exits need tightening.
- **Stepped exits help:** Selling 1/3 at +1R, 1/3 at +2R, trail the rest. Reduces giveback to ~25% on average.

## 5. Bar-by-Bar P&L Paths: When Does the Average Trade Peak?

- **First 30 minutes post-breakout:** Strongest momentum. ~35% of daily highs/lows form here.
- **5-minute MFE threshold:** Trades that reach MFE in <5 min tend to be losers (TradesViz). Winners need time to develop.
- **Breakout-and-run trades:** Peak typically several hours after entry (not minutes). Entry window is first 2 hours of session; best entries 45+ min after open.
- **10:00-11:00 AM window:** Our own v2.4 data shows 60% CONF rate and best MFE/MAE ratio (1.29) in this window, aligning with academic findings.
- **Post-lunch decay:** MFE/MAE drops below 1.0 in afternoon sessions (our data + multiple sources). Momentum decays sharply after 12:00 PM ET.
- **Average P&L path shape:** Fast rise in first 15-45 minutes, plateau for 30-90 minutes, then gradual decay. The "best exit" is typically 30-90 minutes after entry for breakout trades on liquid US equities.

## Summary: Actionable Numbers

| Metric | Value | Source |
|--------|-------|--------|
| Momentum persistence window | 30-120 min | Multiple academic + practitioner |
| Optimal ATR trailing settings | 1.5-2x, 7-10 period | Consensus |
| Best pure intraday exit signal | VWAP cross | Maroy 2025 |
| Min time before exiting | 5 min | TradesViz MFE data |
| Target Exit Efficiency | 60-80% of MFE | MFE/MAE best practice |
| Typical giveback (single exit) | 30-50% of MFE | Practitioner estimates |
| Typical giveback (scaled exit) | ~25% of MFE | Practitioner estimates |
| Average trade peak | 30-90 min post-entry | Composite estimate |
| Afternoon MFE/MAE | <1.0 (avoid) | v2.4 data + literature |
