# TSLA Open Scalper — Reversal Pattern Rescue

Date: 2026-03-21 | N=252 days | Baseline: $761.00
H1=$385.40, H2=$375.60

**Target gaps**: INVV=$215.86, FAKEDN=$107.10, FAKEUP=$103.92, VSHAPE=$105.86

---

## LOOP 1: INVV Direction Rescue

INVV = GRR: bar0=G, bar1=R, bar2=R
Baseline INVV: $3.40 (n=36)
Issue: direction=always_call, bar0=G → 2x size, but 49/51 coin flip → amplified losses

| Metric | CALL@2m | PUT@2m |
|--------|---------|--------|
| Win rate | 47.2% | 52.8% |
| Total PnL | $1.70 | $-1.70 |

### Option A: Skip INVV entirely
Result: $757.60 (Δ-3.40) H1=392.04 H2=365.56 ✗ not robust

### Option B: INVV size=1x (reduce from 2x)
Result: $759.30 (Δ-1.70) H1=388.72 H2=370.58 ✗ not robust

### INVV PM Feature Sub-Filters
| Feature | Threshold | N CALL | N PUT | CALL total | PUT total | Best rule | Delta |
|---------|-----------|--------|-------|------------|-----------|-----------|-------|
| pm_r2 | 0.21 | 27 | 9 | -6.39 | 6.39 | pm_r2>=0.21→PUT | +12.78 |
| pm_accel_4m | 0.31 | 18 | 18 | 5.92 | -5.92 | pm_accel_4m>=0.31→CALL | +8.44 |
| bar0_range | 2.54 | 18 | 18 | 9.50 | -9.50 | bar0_range>=2.54→CALL | +15.60 |
| bar0_range | 3.16 | 9 | 27 | 11.53 | -11.53 | bar0_range>=3.16→CALL | +19.66 |
| bar0_body_pct | 0.22 | 27 | 9 | 10.63 | -10.63 | bar0_body_pct>=0.22→CALL | +17.86 |
| bar0_body_pct | 0.44 | 18 | 18 | 13.32 | -13.32 | bar0_body_pct>=0.44→CALL | +23.24 |
| bar0_body_pct | 0.68 | 9 | 27 | 14.25 | -14.25 | bar0_body_pct>=0.68→CALL | +25.10 |
| pm_green_pct | 0.60 | 9 | 27 | 5.97 | -5.97 | pm_green_pct>=0.60→CALL | +8.54 |

**Best INVV sub-filter**: bar0_body_pct>=0.68→CALL → Δ+25.10

### INVV 15sec Intrabar Sub-Signal
| 15sec feature | N CALL days | N PUT days | CALL total | PUT total | Delta |
|---------------|-------------|------------|------------|-----------|-------|
| bar15s_0_dir=G (n=24) | 13 | — | 7.45 | -7.45 | best=CALL |
| bar15s_0_dir=R (n=9) | — | 7 | -5.78 | 5.78 | best=PUT |
| bar15s_1_dir=G (n=15) | 10 | — | 11.72 | -11.72 | best=CALL |
| bar15s_1_dir=R (n=7) | — | 5 | -6.70 | 6.70 | best=PUT |
| bar15s_2_dir=G (n=17) | 10 | — | 6.62 | -6.62 | best=CALL |
| bar15s_2_dir=R (n=5) | — | 3 | -1.60 | 1.60 | best=PUT |
| bar15s_3_dir=G (n=11) | 6 | — | 6.60 | -6.60 | best=CALL |
| bar15s_3_dir=R (n=11) | — | 5 | -1.58 | 1.58 | best=PUT |

**Best 15sec rule**: bar15s_1_dir=G→CALL: Δ+20.04 ✓ ROBUST

---
## LOOP 2: FAKEDN Extended Exit

FAKEDN = RG (bar0=R, bar1=G, bar2≠G). Current exit=2m. Peak at 20m historically.
Baseline FAKEDN: $-3.10

### Exit Time Scan (FAKEDN under direction system)

| Exit min | FAKEDN PnL | System total | Delta | H1 | H2 | Robust? |
|----------|-----------|--------------|-------|----|----|---------|
| 1m | $35.90 | $800.00 | +39.00 | 412.08 | 387.92 | ✓ |
| 2m | $-3.10 | $761.00 | +0.00 | 385.40 | 375.60 |  |
| 3m | $26.14 | $790.24 | +29.24 | 403.16 | 387.08 | ✓ |
| 4m | $15.30 | $779.40 | +18.40 | 396.82 | 382.58 | ✓ |
| 5m | $23.62 | $787.72 | +26.72 | 400.14 | 387.58 | ✓ |
| 6m | $9.90 | $774.00 | +13.00 | 395.44 | 378.56 | ✓ |
| 7m | $20.72 | $784.82 | +23.82 | 403.92 | 380.90 | ✓ |
| 8m | $25.74 | $789.84 | +28.84 | 402.50 | 387.34 | ✓ |
| 9m | $27.78 | $791.88 | +30.88 | 409.10 | 382.78 | ✓ |
| 10m | $22.94 | $787.04 | +26.04 | 404.12 | 382.92 | ✓ |
| 11m | $25.74 | $789.84 | +28.84 | 400.22 | 389.62 | ✓ |
| 12m | $28.26 | $792.36 | +31.36 | 400.84 | 391.52 | ✓ |
| 13m | $33.36 | $797.46 | +36.46 | 404.54 | 392.92 | ✓ |
| 14m | $41.64 | $805.74 | +44.74 | 408.96 | 396.78 | ✓ |
| 15m | $32.66 | $796.76 | +35.76 | 408.56 | 388.20 | ✓ |
| 16m | $27.90 | $792.00 | +31.00 | 403.06 | 388.94 | ✓ |
| 17m | $27.36 | $791.46 | +30.46 | 405.22 | 386.24 | ✓ |
| 18m | $41.74 | $805.84 | +44.84 | 414.70 | 391.14 | ✓ |
| 19m | $42.72 | $806.82 | +45.82 | 411.22 | 395.60 | ✓ |
| 20m | $38.52 | $802.62 | +41.62 | 404.80 | 397.82 | ✓ |

**Best FAKEDN exit**: 19m → Δ+45.82 ✓ ROBUST

---
## LOOP 3: VSHAPE Exit + 15sec Signal

VSHAPE = RGG. Peaks at 1m. Baseline: $19.16

### Exit Time Scan (VSHAPE)

| Exit min | VSHAPE PnL | System total | Delta | H1 | H2 | Robust? |
|----------|-----------|--------------|-------|----|----|---------|
| 1m | $60.12 | $801.96 | +40.96 | 405.76 | 396.20 | ✓ |
| 2m | $19.16 | $761.00 | +0.00 | 385.40 | 375.60 |  |
| 3m | $-31.74 | $710.10 | -50.90 | 363.66 | 346.44 |  |
| 4m | $-32.88 | $708.96 | -52.04 | 352.20 | 356.76 |  |
| 5m | $-41.18 | $700.66 | -60.34 | 353.44 | 347.22 |  |
| 6m | $-36.62 | $705.22 | -55.78 | 356.58 | 348.64 |  |
| 7m | $-37.66 | $704.18 | -56.82 | 357.70 | 346.48 |  |
| 8m | $-46.84 | $695.00 | -66.00 | 350.88 | 344.12 |  |
| 9m | $-43.66 | $698.18 | -62.82 | 352.02 | 346.16 |  |
| 10m | $-42.24 | $699.60 | -61.40 | 349.84 | 349.76 |  |

**VSHAPE always_call + exit@1m**: Δ-19.16 ✗

### VSHAPE 15sec Intrabar Analysis
| 15sec bar | G days WR | R days WR | G total CALL | R total CALL | Insight |
|-----------|-----------|-----------|--------------|--------------|---------|
| bar15s_0_dir | 66.7% (n=9) | 44.0% (n=25) | -0.28 | -3.67 | G=strong recovery |
| bar15s_1_dir | 66.7% (n=3) | 35.3% (n=17) | 0.88 | -11.58 | G=strong recovery |
| bar15s_2_dir | 20.0% (n=10) | 60.0% (n=10) | -8.08 | -2.62 | G=strong recovery |
| bar15s_3_dir | 57.1% (n=7) | 30.8% (n=13) | -1.37 | -9.33 | G=strong recovery |

**Best VSHAPE 15sec**: bar15s_1_dir=G→CALL: Δ+57.42 ✓

---
## LOOP 4: FAKEUP Direction Sub-Filter

FAKEUP = GRG (or GR+). Current: follow_binary. Baseline: $20.84
Best_side_2m distribution:
- CALL wins: 15 days (53.6%)
- PUT wins:  13 days (46.4%)

### FAKEUP PM Feature Sub-Filters
| Feature | Thresh | N above→CALL | N below→PUT | Delta |
|---------|--------|-------------|------------|-------|
| pm_slope | -0.08(inv) | 21 | 7 | -28.86 |
| pm_slope | -0.03 | 14 | 14 | -8.22 |
| pm_slope | -0.03(inv) | 14 | 14 | -26.58 |
| pm_slope | 0.02 | 7 | 21 | -10.84 |
| pm_slope | 0.02(inv) | 7 | 21 | -23.96 |
| pm_accel_2m | -0.81(inv) | 21 | 7 | -28.22 |
| pm_accel_2m | -0.29 | 14 | 14 | -16.08 |
| pm_accel_2m | -0.29(inv) | 14 | 14 | -18.72 |
| pm_accel_2m | 0.24 | 7 | 21 | -11.88 |
| pm_accel_2m | 0.24(inv) | 7 | 21 | -22.92 |
| pm_position | 0.17(inv) | 21 | 7 | -34.56 |
| pm_position | 0.41(inv) | 14 | 14 | -29.92 |
| pm_position | 0.66 | 7 | 21 | -15.92 |
| pm_position | 0.66(inv) | 7 | 21 | -18.88 |
| agree_count | 0.00 | 28 | 0 | -13.96 |
| agree_count | 0.00(inv) | 28 | 0 | -20.84 |
| agree_count | 0.00 | 28 | 0 | -13.96 |
| agree_count | 0.00(inv) | 28 | 0 | -20.84 |
| agree_count | 2.00 | 10 | 18 | -8.42 |
| agree_count | 2.00(inv) | 10 | 18 | -26.38 |
| pm_green_pct | 0.51 | 23 | 5 | -19.12 |
| pm_green_pct | 0.51(inv) | 23 | 5 | -15.68 |
| pm_green_pct | 0.54 | 18 | 10 | -9.74 |
| pm_green_pct | 0.54(inv) | 18 | 10 | -25.06 |
| pm_green_pct | 0.57 | 12 | 16 | -13.78 |
| pm_green_pct | 0.57(inv) | 12 | 16 | -21.02 |
| gap | -2.47(inv) | 21 | 7 | -32.18 |
| gap | -0.78(inv) | 14 | 14 | -30.32 |
| gap | 2.47(inv) | 7 | 21 | -32.18 |
| bar0_range | 2.21(inv) | 21 | 7 | -28.74 |
| bar0_range | 2.68 | 14 | 14 | +13.20 |
| bar0_range | 2.68(inv) | 14 | 14 | -48.00 |
| bar0_range | 3.21(inv) | 7 | 21 | -36.28 |
| bar0_body_pct | 0.24(inv) | 21 | 7 | -39.58 |
| bar0_body_pct | 0.56 | 14 | 14 | +14.78 |
| bar0_body_pct | 0.56(inv) | 14 | 14 | -49.58 |
| bar0_body_pct | 0.76(inv) | 7 | 21 | -39.34 |
| pm_r2 | 0.08 | 21 | 7 | -14.50 |
| pm_r2 | 0.08(inv) | 21 | 7 | -20.30 |
| pm_r2 | 0.40 | 14 | 14 | -12.14 |
| pm_r2 | 0.40(inv) | 14 | 14 | -22.66 |
| pm_r2 | 0.57 | 7 | 21 | -12.26 |
| pm_r2 | 0.57(inv) | 7 | 21 | -22.54 |
| pm_accel_4m | -0.38 | 21 | 7 | -8.02 |
| pm_accel_4m | -0.38(inv) | 21 | 7 | -26.78 |
| pm_accel_4m | -0.01(inv) | 14 | 14 | -31.76 |
| pm_accel_4m | 0.35 | 7 | 21 | -11.88 |
| pm_accel_4m | 0.35(inv) | 7 | 21 | -22.92 |

**Best FAKEUP sub-filter**: bar0_body_pct >=0.56→CALL → Δ+14.78

**FAKEUP follow_majority**: Δ-5.20 ✗

---
## LOOP 5: INVV Delayed Entry (bar3 direction)

Enter at 9:33 (bar3), exit at 9:35 (bar5). Pnl = bar5 - bar3 in direction of bar3.

| Trigger | N | Win rate | Total PnL |
|---------|---|----------|-----------|
| bar3=G → CALL | 18 | 94.4% | $19.78 |
| bar3=R → PUT  | 18  | 72.2%  | $13.34  |

Delayed INVV total: $33.12 vs system INVV: $3.40
Delta (INVV only): +29.72

---
## LOOP 6: Re-fit Exit Curves Under Direction System

Previously: exit optimization HURT when combined with direction (−$56). But curves were
trained on BINARY direction PnL. Re-fitting on DIRECTION-CORRECTED PnL curves:

| Pattern | Direction | @1m | @2m | @3m | @5m | @7m | @10m | Best exit |
|---------|-----------|-----|-----|-----|-----|-----|------|-----------|
| CRASH | always_put | 168.9 | 258.9 | 257.7 | 270.1 | 275.2 | 257.5 | **7m** |
| SURGE | always_call | 150.5 | 257.9 | 274.4 | 274.5 | 291.3 | 282.2 | **20m** |
| DRIFT_DN | always_put | 50.6 | 113.0 | 99.9 | 76.4 | 103.2 | 105.0 | **2m** |
| DRIFT_UP | always_call | 40.5 | 91.0 | 63.2 | 59.3 | 45.5 | 61.3 | **2m** |
| FAKEDN | follow_major | 35.9 | -3.1 | 26.1 | 23.6 | 20.7 | 22.9 | **20m** |
| FAKEUP | follow_binar | 41.9 | 20.8 | 40.6 | 31.9 | 16.6 | 17.9 | **1m** |
| INVV | always_call | 98.0 | 3.4 | -73.7 | -60.9 | -48.1 | -50.0 | **1m** |
| VSHAPE | follow_binar | 60.1 | 19.2 | -31.7 | -41.2 | -37.7 | -42.2 | **1m** |

**Re-fitted exits system**: $1025.66 (Δ+264.66) ✓ ROBUST
H1=483.20 H2=542.46

### Selective exit improvements (only robust per-pattern changes):

| Pattern | Old exit | New exit | Delta | Both halves? |
|---------|----------|----------|-------|--------------|
| CRASH | 2m | 7m | +16.26 | ✗ |
| SURGE | 2m | 20m | +50.16 | ✓ |
| FAKEDN | 2m | 20m | +41.62 | ✓ |
| FAKEUP | 2m | 1m | +21.06 | ✓ |
| INVV | 2m | 1m | +94.60 | ✓ |
| VSHAPE | 2m | 1m | +40.96 | ✓ |

**Stacked robust exit changes**: Δ+248.40 ✓

---
## LOOP 7: Sizing Tuning — Skip vs 1x vs 2x

Current: bar0 agrees → 2x, disagrees → 0x skip
Test: bar0 agrees → 2x, disagrees → 1x (trade anyway at reduced size)

| Pattern | Disagree→1x delta | Only-INVV change |
|---------|------------------|-----------------|
| CRASH | +0.00 ✗ | — |
| SURGE | +0.00 ✗ | — |
| DRIFT_DN | +0.00 ✗ | — |
| DRIFT_UP | +0.00 ✗ | — |
| FAKEDN | +11.02 ✓ | — |
| FAKEUP | +6.98 ✗ | — |
| INVV | +0.00 ✗ | — |
| VSHAPE | +4.58 ✓ | — |

**Best sizing change**: FAKEDN disagree→1x: Δ+11.02 ✓

---
## LOOP 8: Grand Combined System

Building incrementally with all robust improvements:

| Step | Addition | PnL | Delta | H1 | H2 | Robust? |
|------|----------|-----|-------|----|----|---------|
| 0 | Baseline | $761.00 | — | 385.40 | 375.60 | — |
| 1 | Skip INVV | $757.60 | -3.40 | 392.04 | 365.56 | ✗ |
| 2 | + FAKEDN exit@19m | $806.82 | +45.82 | 411.22 | 395.60 | ✓ |
| 3 | + VSHAPE exit@1m | $847.78 | +86.78 | 431.58 | 416.20 | ✓ |
| 4 | + refit exits ['SURGE', 'FAKEDN', 'FAKEUP', 'INVV', 'VSHAPE'] | $1009.40 | +248.40 | 485.48 | 523.92 | ✓ |
| 5 | + FAKEUP bar0_body_pct>=0.56 | $1003.12 | +242.12 | 481.10 | 522.02 | ✓ |
| 6 | + INVV bar15s_1_dir=G→CALL | $964.06 | +203.06 | 450.18 | 513.88 | ✓ |
| 7 | + VSHAPE bar15s_1_dir=G→CALL | $980.52 | +219.52 | 462.60 | 517.92 | ✓ |
| 8 | + INVV delayed entry (bar3→bar5) | $954.70 | +193.70 | 473.41 | 481.29 | ✓ |

**Final system**: $954.70 (Δ+193.70 vs baseline)
H1=473.41, H2=481.29

Baseline was: $761.00 (H1=385.40, H2=375.60)
Ceiling was:  $1,297.25 — new capture rate: 73.6%

### Final System — PnL by Pattern

| Pattern | n_trades | total | avg | win_rate |
|---------|---------|-------|-----|----------|
| CRASH | 39 | $258.90 | $6.64 | 100.0% |
| SURGE | 34 | $308.04 | $9.06 | 85.3% |
| DRIFT_DN | 29 | $112.96 | $3.90 | 100.0% |
| DRIFT_UP | 25 | $90.96 | $3.64 | 100.0% |
| FAKEDN | 13 | $38.52 | $2.96 | 61.5% |
| FAKEUP | 14 | $35.62 | $2.54 | 85.7% |
| INVV | 36 | $33.12 | $0.92 | 83.3% |
| VSHAPE | 32 | $76.58 | $2.39 | 100.0% |

---
## Quarterly System-Level Check

Purpose: sanity check that no single quarter is carrying the system.
Per-pattern rules NOT validated here (N too small per quarter).

| Quarter | Days | Baseline | Combined | Delta | Green? |
|---------|------|---------|---------|-------|--------|
| Q2-2025 | 62 | $195.60 (52t) | $205.46 (57t) | +9.86 | ✓ |
| Q3-2025 | 64 | $191.92 (53t) | $258.52 (56t) | +66.60 | ✓ |
| Q4-2025 | 64 | $175.30 (53t) | $236.47 (54t) | +61.17 | ✓ |
| Q1-2026 | 53 | $172.52 (42t) | $196.02 (47t) | +23.50 | ✓ |
| Q1-2025* | 9 | $25.66 | $58.23 (8t) | +32.57 | *partial (9d)* |

**Verdict**: ALL 4 main quarters profitable ✓

*Note: Q1-2025 only 9 days (Mar 19–31), excluded from verdict.*