# KLB Signal Tier Analysis — Findings & Action Items
Generated: 2026-03-12 | Data: 22,401 signals with outcomes | Period: 2024-07 – 2026-03-11

---

## The Core Problem

**29% win rate sounds broken — it isn't, but only with the right stop.**

- Morning stop 0.10 ATR + 0.30 ATR target → break-even at **25% win rate** ✅ we deliver 29–34%
- Midday stop 0.25 ATR + 0.30 ATR target → break-even at **45% win rate** ✗ we deliver 20–30%

The system makes money by **holding winners to MFE** (+0.106 ATR/signal for T1 CONF+HOLD),
NOT by fixed-target exits. The 0.25 ATR midday stop is a mathematical losing proposition.

---

## Signal Tier Performance

| Tier | N | Win% | EV (hold→MFE) | EV (fixed 0.30 target) | Status |
|------|---|------|--------------|----------------------|--------|
| **T1: BRK CONF+HOLD** | 2,828 | 29.0% | **+0.106** | -0.012 | ★ Trade — hold to MFE |
| T1b: BRK CONF+BAIL | 635 | 5.7% | -0.075 | -0.080 | ✗ BAIL killing alpha |
| T1c: QBS | 553 | 25.9% | +0.048 | +0.006 | ~ Marginal |
| **T2: RNG** | 3,702 | 30.1% | +0.049 | **+0.062** | ★ Only fixed-target winner |
| T2: FADE | 2,223 | 26.4% | +0.080 | -0.016 | ~ Hold to MFE only |
| T2: Bear REV | 6,117 | 20.4% | +0.069 | -0.057 | ✗ Stop too wide for win% |
| **T2: VR bear** | 1,380 | 28.6% | +0.091 | +0.001 | ~ Best REV variant |
| T2: VR bull | 1,434 | 25.2% | +0.066 | -0.013 | ~ Marginal |
| T2: BRK no-CONF | 128 | **54.7%** | **+0.232** | **+0.138** | ★★ Best — investigate! |
| SKIP: Reclaim | — | low | negative | negative | ✗ Skip |

---

## Temporal Stability

System is **consistent across all time windows** — no decay, no golden era:

| Window | Win% | MFE/MAE |
|--------|------|---------|
| Last 30d | 27.1% | 1.02x |
| Last 90d | 27.8% | 1.12x |
| Last 180d | 28.0% | 1.06x |
| All-time | 27.5% | 1.06x |

**Structural dips:** Apr 2025 (13.5% rolling), Dec 2025 (15%) — possible seasonal/FOMC effects.
**Best quarter:** Q3 2025 (31.1%). Worst: Q2 2025 (24.4%).

### Symbol Trends (Last 90d vs All-time)
- **▲ Improving:** TSLA (+5pp), TSM (+4.7pp), META (+4.4pp), MSFT (+4.2pp), QQQ (+2.7pp), SPY (+2.2pp)
- **▼ Declining:** GLD (-4.2pp), NFLX (-4.1pp), NVDA (-3.4pp), XLE (-2.2pp)
- **→ Stable:** AMD, GOOGL, MU, AAPL, SLV

---

## Time-of-Day Breakdown

| Window | Win% | EV implication |
|--------|------|----------------|
| Morning (9:30–10:30) | 30.0% | ★ Only window above 25% break-even consistently |
| Midday (10:30–13:00) | 22.1% | ~ Marginal — only viable with 0.10 ATR stop |
| Afternoon (13:00–16:00) | **16.0%** | ✗ Kill zone — below break-even at ANY stop size |

---

## Open Action Items

### 🔴 HIGH PRIORITY

**1. Flatten midday stop to 0.10 ATR (same as morning)**
- Current: midday = 0.25 ATR → needs 45% win rate → impossible
- With 0.10 ATR flat stop: needs 25% → midday delivers 22% (marginal but close)
- Alternative: eliminate midday signals entirely below 25% win rate
- Impact: large — midday is 15% of all signals

**2. Investigate T2: BRK no-CONF (54.7% win, 3.15x MFE/MAE, N=128)**
- These 128 signals fired but never had a CONF check
- 54.7% win vs 29% for CONF+HOLD — 2x better
- Hypothesis: very high-vol opens that ran before the CONF window
- Or: signals on final bar of day / special day explosions
- Action: `python3 -c "...load cache, filter sig_type==BRK, bail_action.isna(), examine time_str + level_info + vol"`

**3. Afternoon suppression — make it default ON**
- 16% win, negative EV at all stop sizes
- Already a toggle (`Suppress Afternoon Signals`) but default OFF
- Evidence now overwhelming: flip default to ON
- Cost: 939 signals gone, all net negative

### 🟡 MEDIUM PRIORITY

**4. BAIL is destroying T1 alpha**
- CONF+HOLD: +0.106 EV — real edge
- CONF+BAIL: -0.075 EV — same signal, BAIL turns it into a loser
- BAIL currently fires when 5m pnl < 0 — but most recoveries happen after the 5m mark
- Proposed: add a "pnl > -0.05 ATR" positive guard to BAIL (keep position if barely negative)
- Note: BAIL positive guard was added in v3.4 (+36 ATR) — verify it's working

**5. VR bear (VWAP Reclaim bear) is the best REV variant**
- Win%: 28.6%, MFE/MAE: 1.24x — significantly better than plain Bear REV (20.4%, 1.02x)
- v3.7 addition — confirming the new signal type has structural edge
- Action: consider prioritizing VR bear in the playbook tier, possibly size up vs plain REV

**6. Bear REV needs tighter stop or is unprofitable**
- 20.4% win, fixed-target EV = -0.057
- With 0.10 ATR stop + 0.30 ATR target: needs 25% → delivers 26.4% → marginally positive
- But with 0.25 ATR midday stop: deeply negative
- Action: confirm Bear REV is only traded with morning (0.10 ATR) stop, not midday stop

**7. RNG is the most consistently profitable signal type**
- 30.1% win, the ONLY tier positive on fixed R:R without trailing
- No CONF required, fires fastest
- Under-weighted in playbook relative to BRK CONF
- Action: consider explicit mention that RNG can be traded with fixed 0.30 ATR target

### 🟢 LOW PRIORITY / RESEARCH

**8. Bull REV is not poison at the raw level**
- 21.6% win, MFE/MAE = 1.00x — symmetric (not catastrophic)
- v3.3c suppression was based on ATR simulation, not raw win%
- BUT: with high-ATR symbols (NVDA, TSLA), the losses are much larger in $ terms
- Keep suppressed for now; revisit with symbol-specific size control

**9. Investigate Apr 2025 and Dec 2025 dips**
- Both months showed 13-15% rolling win% — structural cause unknown
- Apr 2025: possible earnings season / FOMC effect
- Dec 2025: holiday low-volume chop?
- Action: check VIX and SPY ATR during these periods (VIX now available in cache!)

**10. BRK no-CONF deep dive script**
```python
import pandas as pd
df = pd.read_parquet('signals_cache.parquet')
noconf = df[(df['sig_type']=='BRK') & df['bail_action'].isna()].copy()
noconf['hour'] = noconf['time_str'].str[:2].astype(int)
print(noconf.groupby(['tod','hour'])[['win','mfe_atr','mae_atr']].mean().round(3))
print(noconf['level_info'].value_counts().head(20))
print(noconf['vol'].describe())
```

---

## Key Formula Reference

```
Break-even win rate = stop / (stop + target)

stop=0.10, target=0.30 → need 25% win rate  ← morning is fine
stop=0.10, target=0.20 → need 33%            ← tight target, hard
stop=0.25, target=0.30 → need 45%            ← midday stop is BROKEN
stop=0.10, target=0.40 → need 20%            ← wide target, easier
```

**Best sizing rule from data:**
- Morning BRK CONF+HOLD: full size, adaptive SL 0.10 ATR, hold to MFE (~35min avg peak)
- RNG: full size, fixed 0.30 ATR target, stop 0.10 ATR flat
- VR bear: standard size, 0.10 ATR stop
- Afternoon: skip (default suppress ON)
- BAIL: do NOT re-enter after BAIL — -0.075 EV per BAIL trade

---

## Data / Scripts

- `debug/signals_cache.parquet` — 22,401 signals with outcomes (re-run `investigate_signals.py` to refresh)
- `debug/investigate_signals.py` — full pipeline: parses pine logs → loads IB 5m → computes MFE/MAE
- `debug/investigation-all-signals.md` — full signal report
- `debug/investigation-temporal.md` — monthly/quarterly/window breakdown
- IB VIX data available: `cache/bars/vix_5_mins_ib.parquet`, `vix_1_hour_ib.parquet`, `vix_1_day_ib.parquet`
