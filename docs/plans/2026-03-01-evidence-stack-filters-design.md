# Design: Evidence Stack Filters (v2.5)

**Date:** 2026-03-01
**Status:** Approved
**Goal:** Reduce bad signals by ~40% while maintaining GOOD follow-through rate

## Problem

v2.4 generates 1,841 actionable signals across 13 symbols in 28 days. Of these:
- Only **8.0%** have GOOD follow-through (MFE > 0.5 ATR in 30m, MFE > 2x MAE)
- **2.7%** are BAD (MAE > 0.5 ATR in 15m)
- The remaining **89.3%** are NEUTRAL — noise that clutters the chart

The BRK CONF rate is 40%, meaning 60% of breakout signals fail to confirm.

## Solution

Layer 4 independent, toggleable filters that suppress low-quality signals. Each filter is backed by both our data (1,748 signals with 5s candle follow-through) and external research.

## Backtest Results (5s candle data, Jan 20 - Feb 27 2026)

### All signal types (n=1,748)

| Filter | Signals kept | GOOD% | BAD% | GOOD:BAD |
|--------|-------------|-------|------|----------|
| Baseline (no filters) | 1,748 (100%) | 8.0% | 2.7% | 3.0:1 |
| 5m EMA alignment only | 967 (55%) | 7.3% | 2.2% | 3.3:1 |
| RS vs SPY only | 1,407 (80%) | 8.7% | 2.8% | 3.1:1 |
| ADX > 20 only | 1,630 (93%) | 7.7% | 2.6% | 3.0:1 |
| Candle body quality only | 1,207 (69%) | 8.1% | 3.4% | 2.4:1 |
| **All 4 combined** | **525 (30%)** | **8.0%** | **2.1%** | **3.8:1** |

### BRK signals only (n=1,006)

| Scenario | Count | GOOD% | BAD% | GOOD:BAD |
|----------|-------|-------|------|----------|
| Baseline | 1,006 | 7.5% | 2.4% | 3.1:1 |
| **All 4 filters** | **368** | **6.8%** | **1.4%** | **4.9:1** |

Key insight: Filters work as **risk reduction** (42% fewer BAD for BRK), not signal boosters. GOOD rate stays stable because it depends on market conditions, not entry selection.

## The 4 Filters

### Filter 1: 5m EMA Alignment

**What:** Require EMA(20) > EMA(50) on 5m timeframe for bull BRK, and EMA(20) < EMA(50) for bear BRK.

**Why:** Eliminates counter-momentum entries. Signals against the 5m trend are the primary source of failed breakouts.

**Evidence:**
- Our data: keeps 55% of signals, reduces BAD by 0.5pp
- External: "Single biggest improvement most traders can make" — multi-TF alignment is the most researched filter
- Already architecturally compatible: v2.4 uses `request.security()` for 5m signal timeframe

**Pine cost:** 2 `request.security()` calls (EMA20 + EMA50 on 5m)

**Pine implementation:**
```pine
ema20_5m = request.security(syminfo.tickerid, "5", ta.ema(close, 20))
ema50_5m = request.security(syminfo.tickerid, "5", ta.ema(close, 50))
bullMomentum = ema20_5m > ema50_5m
bearMomentum = ema20_5m < ema50_5m
fEMA = (isBull and bullMomentum) or (isBear and bearMomentum)
```

### Filter 2: Intraday RS vs SPY

**What:** For long signals, require the stock to be outperforming SPY on the day. For short signals, require underperformance.

**Why:** A stock breaking out while underperforming the market is counter-market — lower conviction.

**Evidence:**
- Our data: best standalone improvement to GOOD rate (+0.7pp)
- External: Quantpedia RS filter adds ~5% annual excess return
- Complements VWAP filter (VWAP = absolute trend, RS = relative strength)

**Pine cost:** 2 `request.security()` calls (SPY open + close)

**Pine implementation:**
```pine
spyC = request.security("SPY", timeframe.period, close)
spyO = request.security("SPY", "D", open)
stockDayOpen = request.security(syminfo.tickerid, "D", open)
stockChg = (close - stockDayOpen) / stockDayOpen
spyChg = (spyC - spyO) / spyO
rsVsSpy = stockChg - spyChg
fRS = (isBull and rsVsSpy > 0) or (isBear and rsVsSpy < 0)
```

**Note:** Skip for SPY itself (always passes). For QQQ, could compare vs SPY or self-pass.

### Filter 3: ADX Trend Strength (5m)

**What:** Suppress signals when 5m ADX < 20 (no clear trend — chop).

**Why:** Replaces the current CHOP? label (3+ CONF fails, 50% false positive) with a principled, quantitative chop detector.

**Evidence:**
- Our data: mild standalone effect, but contributes to the combined stack
- External: Fidelity research confirms ADX < 20 = weak/no trend environment
- Directly addresses the chop problem that was partially solved in v2.4

**Pine cost:** 1 `request.security()` call (ADX on 5m — or can reuse the 5m security context)

**Pine implementation:**
```pine
adx_5m = request.security(syminfo.tickerid, "5", ta.adx(ta.dmi(14, 14), 14))
fADX = adx_5m > 20
```

### Filter 4: Candle Body Quality

**What:** Require breakout candle body > 50% of total range AND close in the favorable 60% of the range (top 60% for bull, bottom 60% for bear).

**Why:** Wick-heavy breakouts (mostly shadow, small body) indicate rejection, not conviction.

**Evidence:**
- Our data: worse alone (+0.7pp BAD!) but contributes to combined stack
- External: 74% continuation when candle closes near extreme (300-case study); body > 70% range = "strong conviction"
- Important: ONLY use in combination with other filters

**Pine cost:** 0 `request.security()` calls (pure OHLC math)

**Pine implementation:**
```pine
candleRange = high - low
bodyRatio = math.abs(close - open) / math.max(candleRange, 0.001)
closeLoc = isBull ? (close - low) / math.max(candleRange, 0.001) : (high - close) / math.max(candleRange, 0.001)
fCandle = bodyRatio > 0.5 and closeLoc > 0.6
```

## Implementation Details

### Pine Input Controls

```pine
// ── Evidence Stack Filters (v2.5) ──
i_fEMA    = input.bool(true, "5m EMA Alignment Filter",     group="Signal Filters")
i_fRS     = input.bool(true, "RS vs SPY Filter",            group="Signal Filters")
i_fADX    = input.bool(true, "ADX Trend Strength Filter",   group="Signal Filters")
i_fCandle = input.bool(true, "Candle Body Quality Filter",  group="Signal Filters")
i_fMode   = input.string("Suppress", "Filter Mode", options=["Suppress", "Dim"], group="Signal Filters")
```

### Filter Application

Filters apply **before** signal generation. A signal that fails any enabled filter is either:
- **Suppress mode:** Not generated at all (no label, no log, no CONF tracking)
- **Dim mode:** Generated with reduced visual prominence (gray color, smaller label, suffix `?`)

### Security Call Budget

v2.4 current calls: ~12 (signal TF, VWAP, levels, etc.)
New calls: 5 (EMA20_5m, EMA50_5m, SPY_close, SPY_dayOpen, ADX_5m)
Total: ~17 out of 40 maximum — well within budget.

### Logging

Add filter status to log output:
```
[KLB] 9:40 ▲ BRK PM H vol=5.5x pos=^94 vwap=above ema=aligned rs=+0.3% adx=28 body=72% ...
```

### Phased Rollout

1. **Phase 1:** Implement 5m EMA alignment + RS vs SPY (highest impact, 4 calls)
2. **Phase 2:** Add ADX chop filter (1 call, replaces CHOP? label)
3. **Phase 3:** Add candle body quality filter (0 calls)
4. **Phase 4:** Tune thresholds based on live results (2-4 weeks of data)

## Success Criteria

After 4 weeks of live data:
- BAD rate for filtered signals should be < 2.0% (vs 2.7% baseline)
- GOOD rate should be >= 7.0% (within noise of baseline 8.0%)
- Signal count should drop 40-70% (less chart clutter)
- GOOD:BAD ratio should be > 4:1 (vs 3:1 baseline)

## Risks

1. **Over-fitting to 28-day sample:** Mitigated by using general principles (momentum alignment, relative strength) rather than curve-fitted parameters
2. **Missing signals on trend reversals:** EMA filter will suppress early entries in trend changes. Mitigated by the Dim mode option
3. **SPY correlation assumption:** RS filter assumes stock-market correlation. May not apply to GLD/SLV. Consider excluding commodity ETFs from RS filter
4. **Security call budget:** 5 new calls is significant but well within the 40-call limit
