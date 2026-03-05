# v29 MC Slot Recovery Analysis

**Question:** How many MC signals would fire after 9:50 ET if the
once-per-direction-per-session slot hadn't been burned at open?

**Criteria:** `ramp > 5.0` AND `range_atr >= 1.5` AND directional candle

## Key Finding

**Almost zero impact.** Only 7 non-MC signals after 9:50 meet MC criteria
across the entire dataset (11,461 signals, 107 trading days).
The slot burn is a non-issue because MC-qualifying bars are
concentrated at 9:30-9:45 and essentially never appear after 9:50.

## Actual MC Signal Distribution

Total MC signals: **1,209**

| Time | Count | % |
|------|------:|--:|
| 11:05 | 2 | 0.2% |
| 13:30 | 1 | 0.1% |
| 13:35 | 1 | 0.1% |
| 14:15 | 1 | 0.1% |
| 14:35 | 1 | 0.1% |
| 14:40 | 1 | 0.1% |
| 9:30 | 30 | 2.5% |
| 9:35 | 521 | 43.1% |
| 9:40 | 391 | 32.3% |
| 9:45 | 260 | 21.5% |

**97.4% of MC signals fire at 9:30-9:45.** Only 7 fire at 9:50+.

## Potential MC Signals (Non-MC meeting MC criteria)

| Category | Count |
|----------|------:|
| Total non-MC meeting MC criteria | 1,573 |
| Before 9:50 | 1,566 |
| After 9:50 | 7 |
| After 9:50 + slot was burned | 7 |
| After 9:50 + slot was open | 0 |

## The 7 Blocked Potential MC Signals

| Symbol | Date | Time | Type | Dir | Ramp | Range/ATR | Vol |
|--------|------|------|------|-----|-----:|----------:|----:|
| AMD | 2025-10-08 | 9:50 | BRK | bull | 5.7 | 3.1 | 8.0 |
| QQQ | 2025-10-10 | 11:05 | BRK | bear | 8.9 | 4.1 | 6.1 |
| QQQ | 2025-10-10 | 11:05 | REV | bear | 8.9 | 4.1 | 6.1 |
| META | 2025-11-28 | 9:50 | VWAP | bull | 5.7 | 3.0 | 10.3 |
| GOOGL | 2026-01-12 | 10:35 | REV | bear | 5.1 | 2.0 | 3.0 |
| TSLA | 2026-01-21 | 14:35 | REV | bull | 5.9 | 2.1 | 4.3 |
| AAPL | 2026-03-02 | 15:55 | REV | bull | 5.6 | 1.9 | 3.4 |

## Follow-Through Comparison (30-min window)

| Group | N | Avg MFE | Avg MAE | Avg Ratio |
|-------|--:|--------:|--------:|----------:|
| Pre-9:50 MC-qualifying (BRK/REV/VWAP) | 2,356 | 0.559 | 0.673 | 8.6 |
| Post-9:50 MC-qualifying (blocked) | 9 | 1.409 | 0.525 | 16.8 |

### Individual 30-min MFE/MAE for the 7 blocked signals

| Symbol | Time | Type | MFE | MAE | Ratio |
|--------|------|------|----:|----:|------:|
| AMD | 9:50 | BRK | 1.332 | -0.061 | 99.9 |
| QQQ | 11:05 | BRK | 2.105 | 0.424 | 5.0 |
| QQQ | 11:05 | REV | 2.105 | 0.424 | 5.0 |
| META | 9:50 | VWAP | 0.667 | 0.503 | 1.3 |
| GOOGL | 10:35 | REV | 0.525 | 0.735 | 0.7 |
| TSLA | 14:35 | REV | 1.257 | 0.043 | 29.3 |
| AAPL | 15:55 | REV | 0.479 | 1.810 | 0.3 |

## Symbol-Days Affected

Only **6** symbol-days would gain a post-9:50 MC signal
out of **870** total symbol-days with MC (0.7%).

| Symbol | Date | Potential MC count |
|--------|------|---------:|
| AMD | 2025-10-08 | 1 |
| QQQ | 2025-10-10 | 2 |
| META | 2025-11-28 | 1 |
| GOOGL | 2026-01-12 | 1 |
| TSLA | 2026-01-21 | 1 |
| AAPL | 2026-03-02 | 1 |

## Why So Few?

MC requires `ramp > 5.0` (volume surge vs prior 3-6 bars) AND `range_atr >= 1.5`
(bar range 1.5x the signal-TF ATR). These extreme conditions are characteristic
of the opening volatility burst (9:30-9:45) and almost never occur later in the day.

- Pre-9:50 avg ramp for MC: 31.8x
- Post-9:50 potential MC avg ramp: 6.5x
- The 7 post-9:50 signals have ramp 5.1-8.9x (barely above threshold)
  vs pre-9:50 MC avg of 32x

## Verdict

**No code change needed.** The once-per-direction-per-session MC slot blocks
only 7 signals across 107 trading days x 13 symbols. The MC-qualifying
conditions (extreme ramp + range) are inherently a first-30-minutes phenomenon.
Removing the slot limiter would add negligible value.
