# TSLA Big-Move Fingerprint — Multi-Timeframe Design

**Date:** 2026-03-03
**Symbol:** TSLA only (expand later if patterns hold)
**Data:** 5s, 1m, 5m, 15m, daily parquet from IB cache

---

## Goal

Two-phase fingerprint of TSLA moves > 1x ATR(14) on the 5m timeframe:
1. **Pre-move:** What conditions exist 1-10 minutes BEFORE the big move?
2. **Continuation:** Which big moves keep running vs reverse?

## Phase 1 — Find Big Moves (5m)

- Load `tsla_5_mins_ib.parquet`, compute ATR(14)
- Filter: `(high - low) / ATR(14) >= 1.0` — range of a single 5m bar exceeds the 14-period ATR
- RTH only (9:30-16:00)
- Record: timestamp, direction, OHLCV, body%, range/ATR

## Phase 2 — Pre-Move Context (1m + 15m + daily)

For each big move, look backwards:

### 1m lookback (10 bars before)
- **Compression ratio:** range of 10-bar window / ATR — tight base = setup
- **Volume ramp:** slope of volume over 10 bars (linear regression) — accelerating?
- **Directional pressure:** % of 1m bars closing in eventual move direction
- **Close location trend:** avg (close - low) / (high - low) — buying or selling pressure
- **Micro-range breaks:** how many times did 1m break then reclaim the 10-bar range?

### 15m context (current + prior bar)
- **15m range position:** where in the current 15m bar's range did the move start? (bottom/mid/top)
- **15m trend:** is 15m EMA20 > EMA50? Same direction as the big move?
- **Breakout of 15m range?** Did the big 5m bar break out of the prior 15m high/low?

### Daily context
- **Gap:** open vs prior close — gap up/down/flat?
- **Day range position:** where in today's range was price before the move?
- **Prior day's ATR:** was yesterday volatile or quiet? (expansion after contraction)

## Phase 3 — At-the-Move Features (5m bar itself)

Standard indicators on the big bar:
- Body %, direction, volume ratio (vs SMA20)
- ADX(14), EMA9/20/50 alignment, VWAP distance
- Time of day bucket

## Phase 4 — Continuation (5s follow-through)

- MFE/MAE over 30 min from 5s data
- P&L at 5 minutes (early gate)
- Classify: Runner (MFE > 0.5 ATR), Fakeout (MFE < 0.1, MAE < -0.3), Middle

## Output

- CSV with all features per big move
- Summary markdown with fingerprint tables (runner vs fakeout)
- Top pre-move predictors ranked by gap between runner and fakeout
