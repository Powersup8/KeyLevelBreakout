# KLB System — Major Guidelines & Daily Improvement Prompt

## Mission

Build a TradingView indicator that alerts on key level breakouts and reversals with **high quality, not quantity**. Catch every major move. Suppress every fake. Ride the wave when it flows.

---

## Core Principles

### 1. Profit Over Signals
- Every signal must have positive expected value. If it doesn't, kill it.
- A missed move is better than a losing signal. But a missed MAJOR move means the system has a gap.
- Quality gates: EMA alignment, SPY regime, volume, candle body, ADX. Each validated with data.

### 2. Right Trigger for Right Pattern
- Barriers (Yest H/L, PM H/L, ORB, Week H/L) → BRK signals
- Magnets (PD Mid) → REV signals (touch-and-turn)
- Failures (CONF ✗) → FADE signals
- Compression (12-bar range + vol spike) → RNG signals
- Extended reversals (rejection at level) → EXREV (body < 30% bypass)
- If none of these fit → explore new trigger types

### 3. Direction Matters
- LOW levels >> HIGH levels (2x CONF rate)
- Bear breakouts at support = panic cascades = follow-through
- Bull breakouts at resistance = often fakeouts
- SPY regime confirms or contradicts direction

### 4. No Time Limits — But Context Awareness
- No hard time window cutoffs. Morning has edge, afternoon is harder — but good signals exist at any time.
- Use regime, volume, and pattern quality instead of clock-based filters.
- Coverage cliff (95% at open → 2% after 11:00) is the #1 gap to close.

### 5. Cross-Symbol Intelligence
- 15 symbols: SPY, QQQ, AAPL, AMZN, AMD, GOOGL, META, MSFT, NVDA, NFLX, TSLA, TSM, XLE, GLD, SLV
- When 4+ symbols move together = market regime shift (morning bear = +1.058 ATR, 63% win)
- SPY direction (>±0.3%) drives BAIL decisions for all symbols
- Individual stocks lead, NOT SPY/QQQ — they confirm

### 6. Data Over Intuition
- Every change must be backtested. Anecdotes inspire hypotheses; data validates or kills them.
- REV EMA exemption: intuition said yes (+1 compelling miss), data said no (-11.8 ATR, 99 signals). Data won.
- Track dead ends so we never revisit them.

---

## What We Have

### Data Infrastructure
- **IB cache pool**: 1s/5s (30 days), 15s/1m/5m/15m/1h/1d (180-360 days), 120+ symbols
- **TV 1m candles**: 15 symbols, 24+ days, BATS exchange
- **Enriched signals**: 1,841 signals with MFE/MAE (60-min follow-through from 5s data)
- **Big moves**: 9,596 significant bars, 2,069 moves at 2x ATR
- **Pine logs**: Per-symbol signal + CONF + BAIL logs from TradingView
- **Analysis scripts**: 20+ Python scripts in `debug/` for every analysis type

### Current System (v3.1a)
- 8 signal types: BRK, REV, Reclaim, Retest, QBS, FADE, RNG, (EXREV planned)
- 12 level types across 8 sources
- 9 configurable filters + EMA Hard Gate
- SPY regime-aware BAIL (aligned/neutral/opposed)
- Runner Score ①-⑥ (6 validated factors)
- Auto-Confirm R1 (EMA = instant ✓)
- ~+131 ATR estimated, 74% win rate on CONF signals

---

## Where We Need To Go

### Signal Quality
- Promote major moves with high conviction
- Suppress fakes, false breakouts, exhaustion bars
- Every signal type matches its level's behavior

### Coverage
- Close the midday desert (10:30-16:00)
- Explore wider timeframe levels (15m, 1h, daily) as support/resistance
- Find new level types from historical data that act as barriers
- Explore non-keylevel triggers for moves that happen between levels

### Cross-Symbol
- Detect market-wide regime shifts in real-time
- Use sector/index correlation to boost or suppress signals
- Track whether a move is isolated or part of a broad rotation

### Exit Management
- BAIL decisions driven by regime + context (started with SPY)
- Trailing stops adapted to signal quality and regime
- VWAP exit validated with data
- 5-min rule integration for open positions

---

## Daily Improvement Process

### After Market Close — Signal Review
1. **Read `debug/_toinvestigate.md`** for user-noted misses and anomalies
2. **Parse new pine logs** — what fired, what confirmed, what BAILed
3. **Scan for major moves** — across all 15 symbols, find every move ≥ 1 ATR
4. **Match signals to moves** — which moves did we catch? Which did we miss?

### For Each Missed Move — Deep Investigation
1. **Why did we miss it?** — No level nearby? Level existed but wrong signal type? Suppressed by filter?
2. **Was there a level?** — Check existing levels first. Then check wider timeframe data (15m, 1h, daily) for historical support/resistance.
3. **Was there a pattern before?** — Volume footprint, price action, cross-symbol correlation. What happened in the 5-30 minutes before the move?
4. **Could a different trigger catch it?** — If no keylevel, could RNG, QBS, EXREV, or a new trigger type have fired?
5. **Is this isolated or systemic?** — One symbol or many? Same time? Same sector?

### For Each Signal That Fired — Outcome Analysis
1. **Did it profit?** — MFE/MAE from 5s data, 5m PnL, 30m PnL
2. **Did BAIL help or hurt?** — Would holding have been better? SPY regime at the time?
3. **Was it the right signal type?** — BRK at a magnet = wrong. REV at a barrier = wrong.
4. **Runner Score accuracy** — Did high-score signals outperform low-score?

### Synthesis — Pattern Discovery
1. **Compare across symbols** — Same pattern at same time = market regime. Different times = symbol-specific.
2. **Compare to historical findings** — Does this confirm or contradict what we know?
3. **Update the system** — If a pattern is validated across multiple days and symbols, implement it.
4. **Track dead ends** — If something looked promising but failed validation, document it.

### Implementation Cycle
1. **Hypothesize** from missed moves and anomalies
2. **Backtest** against enriched-signals.csv and IB cache data
3. **Implement** if positive across multiple symbols and time periods
4. **Validate** with new pine logs (forward test)
5. **Iterate** — fix bugs, tighten filters, expand coverage

---

## The Prompt — Daily Analysis Session

```
Read debug/_toinvestigate.md for new entries. Parse new pine logs in debug/.
Load IB 5m candle data for all 15 symbols for today's date.

1. SIGNAL REVIEW: Parse all signals, CONF, and BAIL from today's pine logs.
   For each: outcome (HOLD/BAIL), 5m PnL, SPY regime, Runner Score.

2. MOVE SCAN: Find every move ≥ 1 ATR across all 15 symbols today.
   For each: start time, end time, magnitude, direction, which symbol(s).

3. MATCH: Which moves did we catch? Which did we miss?
   For misses: why? (no level, wrong type, suppressed, no trigger)

4. INVESTIGATE MISSES: For each missed move:
   - Check all existing levels at that price/time
   - Check 15m/1h/daily levels from IB cache (historical S/R)
   - Check cross-symbol: did other symbols move at the same time?
   - Check pre-move footprint: volume pattern, price action, candle shape
   - Propose: what trigger COULD have caught this?

5. INVESTIGATE SIGNALS: For each signal today:
   - Was it profitable? How far did it run (MFE)?
   - Was BAIL correct? Would opposite decision have been better?
   - Was it the right signal type for this level?

6. CROSS-SYMBOL: Were there coordinated moves (4+ symbols)?
   - Time, direction, magnitude
   - Did our system detect the regime shift?

7. SYNTHESIS: What patterns emerge? What should change?
   Save detailed report to debug/investigation-YYYY-MM-DD.md
   Update debug/_toinvestigate.md with findings and action items.
```

---

## Validation Protocol — Every Change Must Pass This

1. **Backtest the change** against enriched-signals.csv / IB cache data. Net positive ATR required.
2. **Regression check** — verify existing signals are NOT degraded. Compare before/after:
   - Signal count (did we lose good ones?)
   - Win rate per signal type (did quality drop?)
   - ATR per signal type (did profitability shift?)
   - CONF rate, BAIL rate, HOLD rate
3. **Cross-symbol check** — must be positive across multiple symbols, not just one.
4. **Side-effect scan** — every filter/gate change can cascade. Check:
   - Does this interact with EMA gate, candle filter, evidence stack, CONF logic, BAIL logic?
   - Does it change which signals get dimmed/suppressed?
   - Does it affect Runner Score or label display?
5. **Document the result** — pass or fail, record in design journal with data.

Only implement if steps 1-4 pass. If any step shows regression, investigate before proceeding.

---

## Red Lines — Never Do This

- Never add a feature without backtesting it first
- Never implement without regression-checking existing signals
- Never optimize for one symbol (must work across 13)
- Never trust anecdotes over aggregate data
- Never add complexity that doesn't pay for itself in ATR
- Never revisit documented dead ends without new data
- Never use time-window cutoffs as a substitute for signal quality
