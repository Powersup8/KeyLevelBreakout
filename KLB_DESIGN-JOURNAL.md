# KeyLevelBreakout v3.1 — Design Journal

| Doc | What's Inside |
|-----|---------------|
| [KLB_PLAYBOOK.md](KLB_PLAYBOOK.md) | Signal Catalog, Time Windows, Avoid List, Decision Flowchart, Execution, Symbols |
| [KLB_Reference.md](KLB_Reference.md) | Setup, Signal Types, Label Anatomy, CONF System, Levels, Filters, Visuals, Alerts, Settings |
| **KLB_DESIGN-JOURNAL.md** | The Idea, Data Foundation, Key Discoveries, Filter Validation, Evolution, Dead Ends |

---

## 1. The Idea

Key intraday levels -- yesterday's high and low, premarket extremes, the opening range, last week's boundaries -- are where institutional capital acts. Large players place orders at these prices, and when enough volume pushes through, the resulting move tends to follow through. The indicator detects when price breaks through or rejects these levels with volume confirmation, then tracks whether the move follows through or fails.

The goal: turn level-based price action from subjective chart reading into systematic, data-validated signals.

The approach was partly inspired by Tom Vorwald's TradeTheTraders method: volume and liquidity confirm breakouts, macro context matters, and levels are zones rather than exact prices. But where Vorwald's method stays discretionary, this indicator attempts to codify the decision with measurable filters and track every signal outcome.

From the beginning, the design philosophy has been: measure first, then build. Every feature was added because data showed an edge, and several "obvious" improvements were killed because data showed they were noise.

The indicator runs on a 1-minute chart with a 5-minute signal timeframe, tracking 13 US equities (SPY, AAPL, MSFT, NVDA, AMD, TSLA, GOOGL, META, AMZN, QQQ, GLD, SLV, TSM). It evolved over 28 versions across three months, from a simple breakout detector to a multi-layered evidence system.

---

## 2. Data Foundation

Three datasets drove the design. Every claim in this document traces back to one of them.

**Signal dataset (1,841 signals, 13 symbols, 28 days, Jan-Feb 2026).** Every breakout, reversal, reclaim, and retest signal from the indicator, enriched with 5-minute indicators: ADX, EMA(9/20/50), VWAP distance, relative strength vs SPY, volume ratio, and body percentage. Follow-through was measured via 5-second candle data: maximum favorable excursion (MFE) and maximum adverse excursion (MAE) over 60 minutes post-signal.

Signals were classified as GOOD (MFE > 0.3 ATR, MAE > -0.15 ATR), BAD (MAE < -0.2 ATR, MFE < 0.15 ATR), or NEUTRAL. This is the primary dataset for filter validation.

**Big-move dataset (9,596 significant 5m bars, 13 symbols).** Every 5-minute bar with body >= 60% and range >= 0.12 ATR, regardless of whether it happened at a key level. Classification: 84% runners, 3% fakeouts, 13% middle. This dataset answered a different question: what do the best bars in the market look like, independent of our indicator?

**Big-move 2x ATR dataset (2,069 moves, 13 symbols).** A stricter subset: bar range >= 2x the signal-timeframe ATR(14). About 3 moves per day per symbol, 65% runner rate overall. Pre-move volume ramp computed as the ratio of 3-bar recent volume average to 3-bar prior average. This dataset drove the v2.8 QBS/MC signals and cross-validated every TSLA-specific finding against the full 13-symbol universe.

All analysis scripts live in `debug/`: `multi_symbol_fingerprint.py`, `big_move_fingerprint.py`, `multisym_bigmove_fingerprint.py`, `momentum_analysis.py`, `strategy_backtest.py`. The pipeline works by exporting Pine Logs from TradingView, enriching them with 5-minute indicators computed from IB (Interactive Brokers) parquet data, and measuring follow-through with 5-second candle resolution. Every number in this document can be reproduced by running the corresponding script against the CSV files in `debug/`.

---

## 3. Key Discoveries

Ranked from most impactful to least, based on how much indicator code each finding changed. Each discovery started as a hypothesis, was tested against one symbol, then cross-validated against all 13. Several "discoveries" were killed during cross-validation (see Dead Ends).

### Discovery 1: EMA alignment is the strongest filter (+13% gap)

Across 1,841 signals: 90% of GOOD signals had the 5-minute EMA(20) and EMA(50) aligned with the trade direction, compared to 78% of BAD signals. That 13-percentage-point gap was the widest of any single indicator tested, and it validated across all 13 symbols without exception.

This became the cornerstone of the v2.5 Evidence Stack. The logic is straightforward -- a breakout AGAINST the prevailing 5-minute trend is fighting institutional flow, and most of these are noise. Interestingly, for big moves (2x ATR bars), EMA alignment drops to near-zero differentiation. At that energy level, the move overpowers the trend. This is why QBS/MC signals skip the EMA filter.

### Discovery 2: LOW levels crush HIGH levels (+17% CONF rate gap)

Yesterday's Low: 30% CONF. Premarket Low: 27%. ORB Low: 27%. Compare that to Yesterday's High: 15%, ORB High: 14%.

Bear breakouts below support levels confirm at nearly 2x the rate of bull breakouts above resistance. The market adage "stocks take stairs up, elevator down" shows up clearly in the data -- panic selling at support creates sharper, more decisive breaks. This asymmetry influenced the Runner Score design, where bear signals at LOW levels get a +1 bonus.

### Discovery 3: VWAP proximity is the best follow-through zone

Moves originating within +/-0.1 ATR of VWAP showed 89% runner rate and 1.98 MFE -- 37% better than extended moves far from VWAP. This directly validated adding VWAP as a ninth level type in v2.7. The VWAP acts as an equilibrium point for institutional average cost; breaks at VWAP have maximum directional room to run because they catch the most participants offside.

### Discovery 4: The 5-minute gate is nearly perfect

If a signal is more than +0.05 ATR in profit after 5 minutes, and has EMA alignment plus VWAP alignment: 93% runner rate, 0% fakeout (n=1,411). This held across all 13 symbols with zero exceptions.

BAD signals peak their adverse move at minute 3.5; GOOD signals peak their favorable move at minute 23. And 85% of GOOD signals never reverse below -0.10 ATR -- once they go, they go. This became the 5-minute checkpoint in v2.7, which appends 5m✓ or 5m✗ to the label and fires a HOLD or BAIL alert.

### Discovery 5: Volume ramp follows a U-shaped pattern

Not linear -- both extremes are good.

Volume drying (< 0.5x ramp ratio) produced 68% runners and only 3% fakeouts: the "quiet before storm" consolidation pattern where sellers exhaust before a move. Explosive surge (> 5x ramp) produced 64% runners with the best MFE of 2.66: the momentum cascade where volume feeds on itself.

But moderate ramp (1-2x) was the WORST bucket: 56% runners, 7% fakeouts. This is the trap -- volume is picking up enough to look real, but it is distributed, not committed. This U-shape became the foundation of v2.8's QBS (Quiet Before Storm) and MC (Momentum Cascade) signals.

### Discovery 6: Body >= 80% is an inverse fakeout indicator

55% of fakeouts had body >= 80%, compared to only 36% of runners. Clean, full-body candles at the extreme of a move signal exhaustion, not conviction. This completely contradicts traditional technical analysis, which treats full-body candles as "strong."

Confirmed independently from both the signal dataset AND the big-move dataset (the gap was -19% in the 9,596-bar dataset). The body filter was lowered from 50% to 30%, and v2.8 added a ⚠ warning glyph when body >= 80%.

### Discovery 7: CONF ✓ has 0% BAD rate -- the golden rule

Across 110 confirmed signals, zero went bad. When a breakout survives long enough for the next signal to fire (auto-promote to confirmed status), it represents the highest conviction signal in the entire system.

This is why CONF ✓ gets the solid green/red color treatment and full-size labels: the data says "trust it." The ✓★ variant (CONF ✓ with >= 5x volume and >= 80% close position) had 27% GOOD and only 4.5% BAD -- the best signal-to-noise ratio of any signal type.

### Discovery 8: 10x+ volume beats 2-5x (corrected finding)

The initial TSLA-only analysis suggested 2-5x volume was the "sweet spot." When we expanded to all 13 symbols (n=1,841), the relationship turned out to be monotonic: 10x+ volume = 32% CONF rate and 0.50 MFE, while 2-5x = only 20% CONF.

The Runner Score volume factor was initially revised from 2-5x to >= 5x. However, the v2.8b audit (7,044 signals) revealed ⚡ contamination: 84% of 5-10x and 98% of 10x+ buckets were big-move exhaustion bars. For non-⚡ signals, 2-3x volume was the actual sweet spot (MFE 1.252, 54% win). The Runner Score vol factor was revised again to 2-5x in v2.9. This is a lesson in confounders -- the "monotonic more volume = better" finding was driven by a third variable (bar range/exhaustion), not volume itself.

---

## 4. Filter Validation

| Filter | Validated? | Evidence | Action Taken |
|--------|-----------|----------|-------------|
| EMA Alignment | YES | +13% gap, strongest single filter | v2.5, keep ON |
| VWAP Direction | YES | 54% with-trend vs 10% counter-trend CONF | v2.0, keep ON |
| ADX > 20 | YES (partial) | 20-25 best CONF (26%), < 20 worst (22%) | v2.5, threshold correct |
| Body Quality | NO | 49% good vs 48% bad -- zero differentiation | Lowered 50% to 30% in v2.7 |
| RS vs SPY | WEAK | -0.3% vs 0.0% -- tiny gap | Keep ON, low impact |

The Evidence Stack as a whole (all filters combined) reduced signals by roughly 70% while improving the GOOD:BAD ratio from 3.0:1 to 3.8:1. The key insight is that the stack's value comes almost entirely from EMA alignment and VWAP direction -- the other filters add marginal benefit but do not hurt.

For big moves (the 2x ATR dataset), the filter landscape shifts. EMA alignment drops to a -1% gap, VWAP alignment to -4%. At that energy level, the structural factors (volume ramp shape, time of day, 5-minute P&L) dominate over trend alignment. This is why QBS/MC signals in v2.8 use a reduced evidence stack: only ADX and body quality, skipping EMA and VWAP directional filters.

---

## 5. Evolution

**v1.0-v1.4 -- Foundation.** Four level types (yesterday's high/low, premarket high/low, opening range, last week's high/low), volume filter, ATR buffer for zone width, and confluence merging when multiple levels overlap. Basic breakout detection on a single timeframe. The core architecture -- request.security for signal-timeframe data, per-level state tracking, label + alert pipeline -- was established here and never needed rewriting.

**v1.5-v1.8 -- Structural expansion.** Cross-detection fix for signals spanning multiple bars. Added reversal, reclaim, and retest setups, expanding from "breakout only" to four signal types. Per-level tracking variables replaced a single global flag. Zone bands became visible on the chart. Retest-only mode added for conservative traders who prefer to wait for the pullback.

**v2.0 -- VWAP filter + label management.** Counter-trend reversals had approximately 10% win rate in early testing. Adding VWAP directional filtering was the first data-driven improvement and the proof of concept for "measure, then build." Session-long retest tracking replaced the per-bar approach.

**v2.1-v2.2 -- Debug infrastructure.** The signal table and Pine Logs CSV export made quantitative analysis possible for the first time. Found a log.info() spam bug firing 50-100x per bar on real-time ticks. Without this infrastructure -- the ability to export thousands of signals and analyze them in Python -- none of the later data-driven improvements would have happened. This was the most important "invisible" version.

**v2.3 -- Quality fixes from 3-day analysis (229 signals).** Four targeted bug fixes: diamond count display using bar_index instead of sigBarIdx, reclaim CONF gate ensuring ✗ must fire before re-signaling (11 labels changed), VWAP filter defaulting ON (25 counter-trend reversals suppressed), and a CONF race condition fix with an elapsed > 0 guard (2 race conditions eliminated). Small changes, but verified across 13 symbols and 6 weeks of data.

**v2.4 -- Visual tiers from 6-week analysis (3,753 signals).** The key insight was that ALL CONF passes are auto-promotes -- zero slow confirmations existed in the entire dataset. This justified the visual tier system: ✓ in lime green, ✓★ (>= 5x vol + >= 80% close position) in gold, afternoon dimming after 11:00 ET, chop day warning after 3+ consecutive CONF failures, and dead window-expiry code removal.

**v2.5 -- Evidence Stack Filters from 1,748-signal backtest.** The multi-symbol fingerprint analysis justified four filters: EMA alignment (strongest), RS vs SPY (weakest, but harmless), ADX > 20 (removes the worst bucket), and body quality (later found to be noise, lowered in v2.7). Reduced signals roughly 70%, improved GOOD:BAD from 3.0:1 to 3.8:1. Filter mode (Suppress vs Dim) gave the trader control over how aggressively to filter -- suppressing hides signals entirely, dimming shows them in gray with a `?` suffix.

**v2.6 -- Profitability features from 5-second momentum analysis.** Runner Score (5 factors displayed as ①-⑤), VWAP line plot (ta.vwap was computed but never drawn -- a one-line fix), SL reference lines at 0.10 and 0.15 ATR, and VWAP exit alert that fires when price crosses VWAP against the position. Shifted the indicator from "here is a signal" toward "here is a signal AND here is how to manage the trade." Also: reversal volume gate removed after discovering it blocked valid rejections (TSLA 2/25, 95% body at exact Week H, failed 1.5x SMA20 check).

**v2.7 -- Data-driven tuning from multi-symbol fingerprint (1,841) + big-move fingerprint (9,596).** Body filter lowered from 50% to 30% after finding zero differentiation. VWAP zone signals added as a ninth level type. 5-minute checkpoint added to evaluate signals after entry. Runner Score volume factor revised from 2-5x to >= 5x.

**v2.8 -- Big-move integration from 2,069 moves at 2x ATR.** QBS (Quiet Before Storm) and MC (Momentum Cascade) standalone signals based on the U-shaped volume ramp discovery. Body >= 80% fakeout warning (⚠ glyph). Big-move flag (⚡) for any signal on a bar >= 2x ATR. Moderate ramp dimming for the 1-2x trap bucket. Runner Score time window shifted from 10-11 to 9:30-10 (validated: 70% runner rate, MFE 2.36 in the first half hour). TSM added to D-tier (38% runner rate, the worst of all 13 symbols). closeLoc threshold lowered from 0.4 to 0.3.

---

## 6. Dead Ends

These are things we investigated, sometimes implemented, and ultimately found to be noise or harmful. They are documented here so we do not re-discover them. The dead ends consumed roughly 40% of total analysis time and are arguably more valuable than the successes -- they define the boundaries of what the data actually supports.

**Body percentage as a quality filter.** This was one of the earliest filter ideas: surely a candle with a big body is more "decisive" than one with long wicks? The data said otherwise. GOOD signals averaged 48.7% body, BAD averaged 47.9% -- a gap of 0.8 percentage points, which is pure noise.

The filter was kept but with a dramatically lowered threshold (30%), functioning more as a basic sanity check than a quality gate. And the reverse turned out to be true: body >= 80% is actually a fakeout warning (see Discovery 6).

**"2-5x volume is the sweet spot."** The initial TSLA-only analysis clearly showed a peak at 2-5x. But expanding to 13 symbols revealed this was TSLA-specific behavior. Multi-symbol data showed a monotonic relationship: more volume = better. The Runner Score was corrected before shipping.

**ADX fine-tuning above the threshold.** Once you establish ADX > 20 as the floor (it removes the worst bucket at 22% CONF), trying to optimize further is futile. Average ADX for GOOD signals: 26.2. For BAD: 27.2. The difference is -1.0 -- wrong direction and statistically meaningless. ADX tells you "is there a trend?" but not "which side wins."

**Afternoon CONF as a positive signal.** The afternoon CONF rate of 49% looks respectable in isolation. But follow-through analysis revealed 0% GOOD outcomes after 11:00 ET. The breakouts confirm in the sense that price continues, but they do not RUN -- the move dies before reaching meaningful profit targets. MFE/MAE ratio of 0.90 means negative expectancy even when the signal "works." Afternoon dimming was the correct response: show the signals, but make them visually subdued so the trader knows to be skeptical.

**Reclaims as trade signals.** Only 3% reached GOOD follow-through while 8.1% went BAD -- a ratio of roughly 1:3, the worst of any signal type. Reclaims represent price returning to a level it already broke, which means the original breakout failed. Trading the "second chance" sounds appealing in theory, but the data says it is not a strong foundation. The indicator still tracks reclaims for completeness, but the playbook says: skip unless CONF ✓ follows.

**Symbol-specific parameter tuning.** CONF rates ranged from 6% (GLD) to 35% (GOOGL). The spread seems wide enough to justify per-symbol rules, but the actual parameter differences (ADX thresholds, volume multipliers, body ratios) were too narrow to be reliable across samples. GLD is genuinely an outlier that should probably just be avoided for breakout trading entirely.

**Per-signal body/close-position as hard gates.** Close position >= 80% showed a +9.9 percentage point lift in one analysis. But it is too restrictive -- it cuts 70% of valid signals to catch a marginal edge, and the effect did not replicate cleanly across the full 13-symbol dataset. This is textbook overfitting: impressive in-sample, useless out-of-sample.

**High volume at the signal bar for general big moves.** In the 9,596-bar big-move dataset, 15% of fakeouts had vol >= 2x compared to only 8% of runners. Outside the context of key level breakouts, high volume on the move bar itself is an exhaustion signal, not a conviction signal. This is the opposite of the key-level finding, where volume at breakout confirms institutional participation. The lesson: context is everything. The same metric (high volume) is bullish at a key level and bearish in the open market.

**Window expiry for CONF tracking.** Early versions had a configurable time window after which unconfirmed signals would expire. Analysis of 3,753 signals in v2.4 revealed that 100% of CONF passes were auto-promotes (the next signal fired before any time window elapsed). The window expiry code was dead code -- it never triggered in production. Removed in v2.4 with zero impact on behavior.

**Chop day detection tuning.** v2.4 added a "CHOP?" warning label that fires after 3+ consecutive CONF failures. The idea was sound, but the implementation had a 50% false positive rate -- it frequently flagged normal afternoon doldrums as chop days. The feature remains in the code as a visual cue, but it was never tightened enough to be actionable.

---

## 7. Three Pillars of Trade Quality

After analyzing 11,000+ data points across three datasets, 13 symbols, and 28 trading days, the findings converge on three pillars. If you remember nothing else from this document, remember these:

**1. Direction + Level.** Bear breakout at a LOW level (yesterday's low, premarket low, ORB low) confirms at roughly 2x the rate of bull breakouts at HIGH levels. The strongest setup in the dataset is a bear break of yesterday's low with EMA alignment. Direction is not symmetric, and neither are levels. This asymmetry is structural -- fear moves faster than greed, and support breaks trigger stop-loss cascades that create self-reinforcing moves.

**2. Location.** Signals near VWAP (+/-0.1 ATR) produce the best follow-through: 89% runner rate and 1.98 MFE. Extended signals far from VWAP have already moved -- the easy money is gone. The VWAP acts as an institutional average cost anchor, and breaks from it catch the most participants offside. This is why the v2.7 VWAP zone signal was added as a ninth level type -- the data demanded it.

**3. Momentum confirmation.** If a signal is positive at the 5-minute mark with EMA alignment and VWAP alignment, the runner rate reaches 93% with 0% fakeouts. The 5-minute gate is the single most reliable predictor across all 13 symbols, with zero exceptions in cross-validation. The practical implication is clear: enter at the signal, evaluate at 5 minutes, and if the position is underwater, exit immediately rather than hoping for a reversal.

What traditional technical analysis emphasizes -- full-body candles as "strong," high volume as "confirming" -- is either noise (body%) or context-dependent (volume). The data repeatedly favored structural factors (which level, which direction, where relative to VWAP) over candle aesthetics. The indicator was built to reflect what the data actually shows, not what the textbooks say.

---

## 8. Future Ideas

These are data-justified improvements that were deferred due to scope constraints or because they need more validation. Listed roughly by expected impact.

- HIGH-level dimming: ORB H has 14% CONF vs Yest L at 30% -- a visual penalty for weak levels would reduce false confidence
- GLD special handling: 6% CONF is an extreme outlier; may warrant exclusion or separate parameterization
- FVG-based retest quality: treat the retest zone as a Fair Value Gap for more precise zone targeting
- 15m-based weekly zones: derive zone width from the 15m candle that made the weekly extreme, instead of fixed ATR width
- Level proximity warning: alert when price approaches a key level before the break happens
- Current Week H/L as a level type: intraweek extremes are actively watched by swing traders
- Backtest strategy version: validate P&L with systematic TP/SL rules against 5-second data
- Scanner upgrade: add reversals, retests, and volume ramp signals to KeyLevelScanner.pine
- Volume ramp as filter (not just signal): dim or suppress any BRK/REV with moderate (1-2x) ramp
- Cross-symbol momentum: fire alert when 3+ symbols break the same direction simultaneously

---

**v2.8b -- Big-move size correction.** ⚡ signals (bar range ≥ 2x ATR) had 48% lower MFE than normal signals (0.598 vs 1.152) -- entry at exhaustion. Removed `size.large` from ⚡ on BRK/REV labels and QBS/MC labels. The ⚡ glyph remains as an informational marker. Multi-level confluence (2+ levels) still gets `size.large`.

**v2.9 -- Audit-driven fixes from 7,044-signal analysis (Sep 2025–Mar 2026, 10 symbols, ~100 days).** Four data-validated changes:

1. **MC 9:50 ET time gate.** 126 opposing MC pairs (both bull AND bear within 5-10 min at open) showed 45% accuracy -- a coin flip. No signal feature at fire time could distinguish correct from wrong. Direction from 9:50 onward matched 30-min outcome 79% of the time. Suppressing MC before 9:50 prevents the once-per-session slot from being burned on opening auction noise. Analysis: `debug/v28a-mc-analysis.md`, `debug/v28b-mc-smart-filter.md`.

2. **Runner Score vol factor: ≥5x → 2-5x.** The v2.8b volume investigation found ⚡ contamination: 84% of 5-10x and 98% of 10x+ volume buckets were big-move bars (exhaustion, not conviction). Non-⚡ sweet spot: 2-3x volume (MFE 1.252, 54% win, MFE/MAE 1.42). Analysis: `debug/v28b-volume-investigation.md`.

3. **✓★ gold criteria rework.** Both old criteria were broken: ≥5x vol = worst MFE bucket (0.859 vs 1.178 for <5x), ≥80% close position = overfitting (didn't replicate, cut 70% of signals). New definition: BRK source + vol < 5x + hour ≤ 10. Result: +23.10 ATR total (vs old +2.74), 42% win (vs 32%), 8/10 symbols profitable, max drawdown -1.95 ATR. Analysis: `debug/v28b-volume-investigation.md`.

4. **QBS/MC ✓★ removal.** QBS/MC ✓★ was net negative (-1.47 ATR). The volume explosion that triggers these signals already implies high vol, so the ≥5x gate was meaningless. Always plain ✓ now.

**v3.0 -- MC rethink, EMA gate, new signals from 8 rounds of optimization (1,841 signals, 25,304 significant moves, 9,596 big-move bars).** The largest structural change since v2.5. Three phases: cleanup, new signals, and display overhaul.

**Phase 1 — Cleanup.** Three changes driven by the MC rethink analysis (8 optimization rounds, `debug/v29-mc-rounds678.md`):

1. *Killed MC entirely (~30 lines removed).* 99.4% of MC signals fired on opening noise. Opposing bull+bear pairs within 5-10 minutes at open showed 45% accuracy — a coin flip. No signal feature at fire time could distinguish correct from wrong. Even with the 9:50 ET gate from v2.9, only 7 MC signals would have survived. The once-per-session slot was consistently burned on noise. QBS remains — its volume-drying pattern has genuine edge (68% runner, 3% fakeout).

2. *EMA Hard Gate all-day (+45.6 ATR recovered).* The dominant finding from factor ranking: EMA alignment accounts for 92% of all scoring edge. Non-EMA signals were net negative BOTH pre-9:50 (-32.3 ATR, N=283) AND post-9:50 (-13.3 ATR, N=208). After 9:50 ET, signals against EMA are now suppressed entirely. Before 9:50, they are dimmed only (EMA not fully established at open). This reduced signals from 1,841 to ~1,350 while increasing PnL from +70.3 to +115.9 ATR (+65%). Validated: 12/13 symbols positive, both time-halves positive.

3. *Auto-Confirm R1 (EMA = instant CONF ✓, no time restriction).* Originally gated to before 10:30 ET, but v3.0b research showed the 10:30 cliff caused 22 unnecessary CONF failures — 56% of which were profitable. HOLD/BAIL (83% win vs 51%) is the real gatekeeper, making the time restriction redundant. Now: EMA-aligned = auto-confirm all day. Recovers ~1.1 ATR/27 days from previously-rejected afternoon signals.

**Phase 2 — New signals.** Four additions to cover gaps in the signal landscape:

4. *Three new levels: PD Last Hr Low (prior day 15:00-16:00 low), PD Mid ((PDH+PDL)/2), VWAP Lower Band (VWAP - ATR).* These levels provide midday coverage where the original 8 levels were sparse. All three participate in existing BRK/REV detection without new signal logic.

5. *CONF window expanded 1→3 bars.* Signals now get 15 minutes (on 5m TF) to confirm instead of 5 minutes. This was the single highest-impact parameter change — many valid breakouts needed 2-3 bars to attract the follow-through signal that triggers auto-promote.

6. *FADE signal.* After CONF ✗ (failed breakout), if price crosses back through the level in the opposite direction within 30 minutes, fire a reverse signal. Purple labels. Trades the failure — when a breakout fails, the trapped participants create fuel for the reversal.

7. *RNG (Range+Vol) signal.* 12-bar range breakout combined with volume ≥ 3× SMA(20). Teal labels. The critical finding: this is the ONLY profitable non-EMA signal type. During the MC rethink analysis, 10 of 14 non-EMA signal designs lost money. RNG survived because range compression followed by volume expansion is a mechanical edge independent of trend alignment.

**Phase 3 — Display overhaul.**

8. *Regime Score R0/R1/R2.* Combines EMA alignment (+1) and VWAP alignment (+1) into a 0-2 score displayed on every label. R1 bull signals are dimmed — at 31.2% win rate, they actively harm performance. R1 bear and R2 signals display normally.

9. *Runner Score redesign.* New 5 factors: EMA aligned, regime=2, vol ≥10x, morning (<11:00), CONF pass. Replaces the v2.9 factors (VWAP aligned, vol 2-5x, time 9:30-10, level quality, not D-tier). The redesign reflects the factor ranking analysis where EMA and regime dominated all other factors.

**Key discoveries from the MC rethink:**

- EMA alignment is the dominant factor — 92% of all scoring edge. Every other factor (ADX, VWAP, vol, time) is marginal by comparison.
- Counter-VWAP signals have high per-signal quality but are too rare (N=52) to build a system around.
- Volume surges after 9:50 are exhaustion, not continuation — the opening 20 minutes are the only window where volume surge has genuine directional signal.
- 1HR H/L levels (tested as candidates) are traps despite coverage — they lose money because they fire in the afternoon noise zone.

**Dead ends from this cycle:**
- Complex 9-factor scoring system (marginal +4.4 ATR over EMA alone — not worth the complexity)
- Smart filtering of opposing MC pairs at open (tested 6 approaches, nothing worked)
- Consecutive bar streaks as a factor (no edge)
- VWAP crosses after 9:50 as a signal (no edge)
- A-tier symbol filter (TSLA/META — negative delta -0.026 when tested as a factor)
- 11 AM window as a scoring factor (negative delta when properly tested)

**Expected impact:** Fewer but higher-quality signals. Midday coverage from new levels. Target: +150 ATR (up from +70.3 in v2.9).

Analysis files: `debug/v29-mc-rethink-knowledge.md`, `debug/v29-mc-rounds678.md`, `debug/v29-mc-factor-screen.md`, `debug/v29-mc-optimize.md`.

**v3.1 -- SPY Market Regime, PD Mid REV conversion, and the REV EMA experiment (231 CONF signals, 99 counter-EMA REVs).** Two validated changes and one reverted experiment, all driven by the March 5 investigation and BAIL analysis.

1. *SPY Market Regime → BAIL Modifier (+15.5 ATR).* The BAIL system (5-minute checkpoint after CONF pass) was a flat `pnl > 0.05 ATR` threshold. Analysis showed BAIL was net NEGATIVE by -10.6 ATR — 64% of BAILed signals would have been profitable at 30 minutes. The fix: use SPY's intraday change as regime context. Three states: SPY up >0.3% = BULL, down >0.3% = BEAR, else NEUTRAL. Signal aligned with SPY → never BAIL (hold always). SPY neutral → loose BAIL (pnl > -0.10 ATR). Signal opposes SPY → strict BAIL (pnl > 0.05 ATR, unchanged). Result: 104 signals change from BAIL to HOLD, total PnL +36.5 → +52.0 ATR, win rate 63.6% → 74.0%. SPY-aligned signals gained +8.1 ATR, neutral signals +7.4 ATR. No new `request.security()` calls — SPY data already existed. Runner Score: SPY-aligned added as 6th factor (max score ⑥).

2. *PD Mid → REV signal type.* PD Mid was firing as BRK (breakout) in v3.0. Research showed it's a magnet level — 63% of crosses return to the level. BRK at a magnet = wrong signal type (4/4 BAILed in March 5 data). Changed detection from `bullBreak`/`bearBreak` to `bullRev`/`bearRev` (touch-and-turn). Moved from BRK filtered section to REV section. No EMA gate on PD Mid REV — this is a new signal type with no historical EMA gate data.

3. *REV EMA exemption — TESTED AND REVERTED (-11.8 ATR).* The TSLA 10:16 miss (March 5) was a compelling case: EMA Hard Gate killed a bearish REV at Yesterday's High after a 7-point rally flipped EMAs to bull. The hypothesis was that reversals are counter-trend by nature, so the EMA gate is logically contradictory for REVs. Backtest: 99 counter-EMA REV signals had -11.8 ATR total, 35.4% win rate. Bears especially bad: 27.5% win, -7.0 ATR. The EMA gate catches more bad REVs than good ones. **Data > intuition.** EMA gate stays on all REV signals. Separate investigation launched into what alternate trigger could catch high-quality extended reversals like TSLA 10:16.

Analysis files: `debug/v30b-bail-investigation.md`, `debug/v31-backtest-results.md`, `debug/investigation-2026-03-05.md`, `debug/v30b-move-scanner-research.md`, `docs/plans/2026-03-06-v31-regime-rev-fade-design.md`.

*Last updated: 2026-03-06 | v3.1 | Data: Sep 2025–Mar 2026*
