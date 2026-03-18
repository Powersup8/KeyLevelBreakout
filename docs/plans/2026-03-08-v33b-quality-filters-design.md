# v3.3b Design: Three Remaining Quality Filters

**Date:** 2026-03-08
**Status:** Approved
**Scope:** 3 changes to KeyLevelBreakout.pine — 2 safe (dim overrides) + 1 aggressive (EMA gate bypass)

---

## Context

v3.3 implemented 5 fingerprint-driven changes (vol gate, exhaustion dim, exhaustion filter, level freshness, quiet coil dim override). Three research findings remain unimplemented:

1. Midday + flat EMA → 31.1% great (1.55x), 2.2% noise, N=541
2. Small range + broad move → 32.1% great (1.6x), 1.0% noise, N=193
3. Quiet coil EMA bypass → catches Tier S monsters (40% EMA-misaligned)

---

## Change 1: Midday Flat-EMA Boost (Safe — Dim Override)

**Research basis:** `catalog_research_v2.py` — midday + flat_ema → 31.1% great (1.55x lift). Adding both_aligned → 35.5% (1.78x, N=124). Midday is NOT the desert we thought — it's the BEST timing when EMA is flat.

**Implementation:**
```pine
// Existing: isMidday = etHour >= 11 and etHour < 14
// Existing: ema20_5m (signal-TF EMA21)
// New: detect flat EMA slope over last 6 bars, normalized by daily ATR
bool isMiddayFlat = isMidday and not na(ema20_5m) and not na(dailyATR) and dailyATR > 0
     and math.abs(ema20_5m - nz(ema20_5m[6])) / dailyATR < 0.02
```

**Wiring:** Add `and not isMiddayFlat` to isDimBull and isDimBear (same pattern as quiet coil override).

**Effect:** Midday signals with flat EMA show at full brightness instead of being dimmed by evidence stack, vol moderate, or regime dim.

---

## Change 2: Small Range + Broad Move Boost (Safe — Dim Override)

**Research basis:** `catalog_research_v2.py` — small_range + broad_move → 32.1% great (1.6x), 1.0% noise, N=193. When the whole market moves and the trigger bar is quiet, it's high quality.

**Implementation:**
```pine
// Existing: sigRangeATR (signal bar range / ATR)
// Existing: spyChg (SPY intraday % change)
// New: SPY as proxy for broad market move (> 0.3% intraday)
bool isBroadCoil = sigRangeATR < 0.5 and math.abs(spyChg) > 0.003
```

**Wiring:** Add `and not isBroadCoil` to isDimBull and isDimBear.

**Overlap with quiet coil:** Quiet coil checks volume drying + small range. Broad coil checks SPY momentum + small range. They're complementary — different angles on the same "compression at a level" thesis. Either independently overrides dim.

**Why 0.3% threshold:** Research used "4+ concurrent symbols" as broad move definition. SPY moving 0.3%+ correlates with broad market participation — below the exhaustion threshold (0.8%) but above noise.

---

## Change 3: Quiet Coil EMA Hard Gate Bypass (Aggressive)

**Research basis:** Tier S monsters (104 moves, MFE≥0.60, ratio≥5x) are 40% EMA-misaligned. The EMA hard gate (+0.128 MFE, 92% of edge in signal audit) blocks some of the best moves when they come from compression. Quiet coil independently predicts 35.8% great rate (1.8x) with only 1.5% noise.

**Implementation:**

Currently every signal definition checks EMA:
```pine
sigBullPMH = rBullPMH and ... and fGateBull and (emaGateBull or isPre950)
```

Refactor: create a unified EMA pass variable that includes quiet coil bypass:
```pine
bool emaPassBull = emaGateBull or isPre950 or isQuietCoil
bool emaPassBear = emaGateBear or isPre950 or isQuietCoil
```

Then replace `(emaGateBull or isPre950)` with `emaPassBull` in all signal definitions. Same for bear. Also for REV signals.

**Note on EXREV:** EXREV signals already have their own bypass (`exrevBypass`). The quiet coil bypass is a separate path — both can fire independently.

**Risk assessment:**
- EMA is the #1 quality factor in the signal audit
- But signal audit was filtered to KLB fires — in the full catalog, EMA alignment is flat (1.00x lift)
- Quiet coil's 35.8% great rate is strong enough to trust even without EMA
- If this proves noisy in live testing, we can tighten by adding `and sigRangeATR < 0.3` or restricting to BRK-only

---

## Signal Flow After All Changes

```
Bar arrives
  ├─ Compute isQuietCoil, isMiddayFlat, isBroadCoil
  ├─ Compute emaPassBull/Bear (includes quiet coil bypass)
  ├─ Signal definitions use emaPassBull/Bear (gate level)
  ├─ Signal fires → increment touch counters
  ├─ isDimBull/Bear computed:
  │   ├─ (evidence stack + vol moderate + EMA dim + regime + exhaust + freshness)
  │   └─ AND NOT (isQuietCoil OR isMiddayFlat OR isBroadCoil)  ← dim overrides
  └─ Label rendered with final color/size
```

---

## Testing

- Load v3.3b in TradingView on SPY, TSLA, NVDA
- Check midday signals: flat-EMA midday should show full brightness
- Check quiet coil: signals should fire even without EMA alignment when vol is drying + range small
- Compare signal count vs v3.3 — expect slight increase from EMA bypass
- Monitor noise: any quiet coil + no-EMA signals that clearly fail?
