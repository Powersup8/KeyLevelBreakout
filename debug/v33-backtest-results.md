# KLB v3.3 Backtest Results
**Date:** 2026-03-08
**Data:** Pine logs → IB 1m bars, 60-min MFE/MAE window
**Symbols:** AAPL, AMD, AMZN, GLD, GOOGL, META, MSFT, NFLX, NVDA, SLV, SPY, TSLA, TSM, XLE
**v3.3 signals:** 11954 parsed, 11954 with MFE/MAE
**v3.2 signals:** 11468 parsed, 11468 with MFE/MAE

## 1. Overall Summary

| Metric | v3.2 | v3.3 | Delta |
|--------|------|------|-------|
| Total Signals | 11468 | 11954 | +486 |
| Win Rate | 40.1% | 40.4% | +0.3pp |
| Avg MFE (ATR) | 0.3331 | 0.3332 | +0.0001 |
| Avg MAE (ATR) | 0.3309 | 0.3268 | -0.0041 |
| Avg P&L/sig (ATR) | 0.0023 | 0.0064 | +0.0041 |
| Net ATR | 26.1 | 76.6 | +50.5 |

## 2. By Signal Type

### v3.3 Signal Types

| Type | N | Win% | Avg MFE | Avg MAE | Avg P&L | Net ATR |
|------|:-:|:----:|:-------:|:-------:|:-------:|:-------:|
| BRK | 2054 | 51.5% | 0.5555 | 0.2260 | 0.3295 | +676.8 |
| FADE | 614 | 62.7% | 0.4883 | 0.8005 | -0.3122 | -191.7 |
| QBS | 116 | 40.5% | 0.3662 | 0.5311 | -0.1649 | -19.1 |
| REV | 7347 | 45.5% | 0.3403 | 0.3932 | -0.0530 | -389.3 |
| RNG | 1823 | 0.0% | 0.0000 | 0.0000 | 0.0000 | +0.0 |

### v3.2 Signal Types (comparison)

| Type | N | Win% | Avg MFE | Avg MAE | Avg P&L | Net ATR |
|------|:-:|:----:|:-------:|:-------:|:-------:|:-------:|
| BRK | 1643 | 52.3% | 0.6029 | 0.2260 | 0.3769 | +619.2 |
| FADE | 610 | 62.8% | 0.4923 | 0.8002 | -0.3079 | -187.8 |
| QBS | 120 | 40.0% | 0.3614 | 0.5247 | -0.1633 | -19.6 |
| REV | 7274 | 45.5% | 0.3418 | 0.3948 | -0.0530 | -385.7 |
| RNG | 1821 | 0.0% | 0.0000 | 0.0000 | 0.0000 | +0.0 |

## 3. By Symbol

| Symbol | v3.3 N | Win% | Avg MFE | Avg MAE | Net ATR | v3.2 N | v3.2 ATR | Delta |
|--------|:------:|:----:|:-------:|:-------:|:-------:|:------:|:--------:|:-----:|
| SPY | 1554 | 45.0% | 0.2060 | 0.1825 | +36.5 | 772 | +22.0 | +14.5 |
| AAPL | 725 | 38.9% | 0.1672 | 0.1824 | -11.1 | 706 | -9.9 | -1.1 |
| AMD | 781 | 38.0% | 0.1731 | 0.1730 | +0.1 | 757 | -2.5 | +2.5 |
| AMZN | 741 | 40.9% | 0.1786 | 0.1644 | +10.6 | 714 | +11.5 | -0.9 |
| GLD | 699 | 40.1% | 0.1881 | 0.1599 | +19.7 | 672 | +19.3 | +0.4 |
| GOOGL | 768 | 39.2% | 0.1916 | 0.1801 | +8.9 | 737 | +11.3 | -2.4 |
| META | 749 | 38.2% | 0.1677 | 0.1684 | -0.5 | 732 | -0.6 | +0.0 |
| MSFT | 692 | 37.0% | 0.1813 | 0.1651 | +11.2 | 668 | +10.6 | +0.6 |
| NFLX | 741 | 37.8% | 0.1695 | 0.1640 | +4.0 | 713 | +2.0 | +2.1 |
| NVDA | 1441 | 41.8% | 1.4306 | 1.4696 | -56.3 | 1392 | -114.8 | +58.5 |
| QQQ | 0 | 0.0% | 0.0000 | 0.0000 | +0.0 | 635 | +26.8 | -26.8 |
| SLV | 651 | 40.9% | 0.1895 | 0.1746 | +9.7 | 625 | +8.2 | +1.5 |
| TSLA | 726 | 41.2% | 0.1744 | 0.1657 | +6.4 | 704 | +8.0 | -1.7 |
| TSM | 765 | 38.2% | 0.1747 | 0.1636 | +8.5 | 747 | +6.0 | +2.5 |
| XLE | 921 | 42.0% | 0.1888 | 0.1572 | +29.0 | 894 | +28.3 | +0.8 |

## 4. By Time of Day

| Hour (ET) | N | Win% | Avg MFE | Avg MAE | Avg P&L | Net ATR |
|:---------:|:-:|:----:|:-------:|:-------:|:-------:|:-------:|
| 09:xx | 5932 | 36.6% | 0.3372 | 0.3160 | 0.0212 | +125.8 |
| 10:xx | 2495 | 46.9% | 0.3879 | 0.3716 | 0.0164 | +40.8 |
| 11:xx | 1017 | 48.3% | 0.3282 | 0.2968 | 0.0314 | +31.9 |
| 12:xx | 637 | 45.8% | 0.3136 | 0.3867 | -0.0731 | -46.6 |
| 13:xx | 555 | 38.7% | 0.2699 | 0.4225 | -0.1526 | -84.7 |
| 14:xx | 601 | 37.4% | 0.2621 | 0.2475 | 0.0146 | +8.8 |
| 15:xx | 717 | 37.1% | 0.2427 | 0.2418 | 0.0008 | +0.6 |

### Timing Buckets

| Bucket | N | Win% | Avg P&L | Net ATR |
|--------|:-:|:----:|:-------:|:-------:|
| Morning 9:30-11 | 8427 | 39.7% | 0.0198 | +166.6 |
| Midday 11-14 | 2209 | 45.2% | -0.0450 | -99.3 |
| Afternoon 14-16 | 1318 | 37.3% | 0.0071 | +9.4 |

## 5. Dim vs Non-Dim Performance (v3.3 Quality Filters)

Signals dimmed by v3.3 filters should have WORSE performance than non-dimmed.
If dimmed signals perform badly, the filters are working correctly.

| Status | N | Win% | Avg MFE | Avg MAE | Avg P&L | Net ATR |
|--------|:-:|:----:|:-------:|:-------:|:-------:|:-------:|
| Not Dimmed | 5290 | 32.1% | 0.2505 | 0.2794 | -0.0290 | -153.2 |
| Dimmed | 6664 | 47.0% | 0.3989 | 0.3644 | 0.0345 | +229.8 |

### By Dim Reason

| Dim Reason | N | Win% | Avg P&L | Net ATR |
|------------|:-:|:----:|:-------:|:-------:|
| counter_ema | 92 | 40.2% | 0.0243 | +2.2 |
| counter_ema,ema_dim | 125 | 48.8% | 0.3889 | +48.6 |
| counter_ema,ema_dim,exhaustion | 3 | 0.0% | -0.0419 | -0.1 |
| counter_ema,ema_dim,freshness | 219 | 40.2% | 0.2672 | +58.5 |
| counter_ema,ema_dim,freshness,exhaustion | 4 | 25.0% | -0.0950 | -0.4 |
| counter_ema,exhaustion | 1 | 100.0% | 0.0196 | +0.0 |
| counter_ema,freshness | 297 | 47.8% | 0.3258 | +96.8 |
| counter_ema,freshness,exhaustion | 18 | 27.8% | 0.0278 | +0.5 |
| ema_dim | 71 | 46.5% | -0.0527 | -3.7 |
| ema_dim,freshness | 27 | 40.7% | -0.0244 | -0.7 |
| exhaustion | 167 | 37.7% | 0.1032 | +17.2 |
| freshness | 3130 | 46.6% | -0.0115 | -36.0 |
| freshness,exhaustion | 139 | 32.4% | -0.0181 | -2.5 |
| none | 3471 | 48.5% | -0.0437 | -151.7 |
| override(broad_coil) | 1812 | 0.7% | 0.0015 | +2.8 |
| override(quiet_coil,broad_coil) | 7 | 28.6% | -0.6111 | -4.3 |
| vol_exhaust | 1494 | 50.9% | -0.0351 | -52.5 |
| vol_exhaust,counter_ema | 51 | 47.1% | 0.1574 | +8.0 |
| vol_exhaust,counter_ema,ema_dim | 2 | 100.0% | 0.5467 | +1.1 |
| vol_exhaust,counter_ema,ema_dim,freshness | 1 | 100.0% | 0.1579 | +0.2 |
| vol_exhaust,counter_ema,ema_dim,freshness,exhaustion | 1 | 100.0% | 0.0121 | +0.0 |
| vol_exhaust,counter_ema,freshness | 49 | 42.9% | 0.3707 | +18.2 |
| vol_exhaust,counter_ema,freshness,exhaustion | 1 | 0.0% | -0.0816 | -0.1 |
| vol_exhaust,ema_dim | 1 | 0.0% | -0.0798 | -0.1 |
| vol_exhaust,ema_dim,freshness | 1 | 100.0% | 0.1922 | +0.2 |
| vol_exhaust,ema_dim,freshness,exhaustion | 1 | 100.0% | 0.1494 | +0.1 |
| vol_exhaust,exhaustion | 17 | 35.3% | 0.5919 | +10.1 |
| vol_exhaust,freshness | 737 | 49.3% | 0.0829 | +61.1 |
| vol_exhaust,freshness,exhaustion | 15 | 60.0% | 0.2061 | +3.1 |

### Vol Exhaust Dim (vol > 5x)

| Group | N | Win% | Avg MFE | Avg MAE | Avg P&L | Net ATR |
|-------|:-:|:----:|:-------:|:-------:|:-------:|:-------:|
| Vol <= 5x | 7584 | 43.0% | 0.3483 | 0.3194 | 0.0289 | +218.9 |
| Vol > 5x | 3755 | 31.7% | 0.2775 | 0.2643 | 0.0132 | +49.4 |

### Vol Drying (🔇 = ramp < 0.5x)

| Group | N | Win% | Avg P&L | Net ATR |
|-------|:-:|:----:|:-------:|:-------:|
| Normal vol | 11509 | 40.3% | 0.0091 | +104.2 |
| Vol drying | 445 | 42.5% | -0.0620 | -27.6 |

### Quiet Coil (vol drying + rangeATR < 0.5)

| Group | N | Win% | Avg MFE | Avg MAE | Avg P&L | Net ATR |
|-------|:-:|:----:|:-------:|:-------:|:-------:|:-------:|
| Not Quiet Coil | 11947 | 40.4% | 0.3333 | 0.3266 | 0.0068 | +80.9 |
| Quiet Coil | 7 | 28.6% | 0.1102 | 0.7213 | -0.6111 | -4.3 |

**Quiet Coil signals (detail):**
- XLE 2025-10-08 10:55 REV bull VWAP vol=0.4x MFE=0.329 MAE=0.027 P&L=0.301 [WIN]
- SLV 2026-01-22 09:30 REV bull Today O vol=0.6x MFE=0.240 MAE=0.026 P&L=0.214 [WIN]
- SLV 2025-11-24 11:40 REV bull VWAP vol=0.6x MFE=0.068 MAE=0.045 P&L=0.023 [FLAT]
- NVDA 2026-01-26 11:30 REV bear VWAP vol=0.4x MFE=0.068 MAE=0.084 P&L=-0.017 [FLAT]
- AMZN 2025-10-29 10:30 REV bear Yest H vol=0.6x MFE=0.051 MAE=0.429 P&L=-0.378 [LOSS]
- GLD 2025-11-07 11:00 REV bear Yest H vol=0.3x MFE=0.016 MAE=0.477 P&L=-0.461 [LOSS]
- NVDA 2025-12-01 11:35 REV bull Yest H vol=0.2x MFE=0.000 MAE=3.960 P&L=-3.960 [LOSS]

## 6. Confirmation (CONF) Analysis

| CONF Status | N | Win% | Avg P&L | Net ATR |
|-------------|:-:|:----:|:-------:|:-------:|
| Pass (✓/✓★) | 2087 | 51.5% | 0.3218 | +671.6 |
| Fail (✗) | 0 | 0.0% | 0.0000 | +0.0 |
| No CONF | 9867 | 38.1% | -0.0603 | -595.0 |

### 5m Checkpoint (HOLD vs BAIL)

| Action | N | Win% | Avg P&L | Net ATR |
|--------|:-:|:----:|:-------:|:-------:|
| HOLD | 1502 | 52.0% | 0.2894 | +434.6 |
| BAIL | 339 | 25.7% | 0.1305 | +44.2 |

## 7. v3.3 vs v3.2 Signal Comparison

- **Common signals:** 8760
- **New in v3.3:** 368 (quiet coil EMA bypass, etc.)
- **Removed in v3.3:** 596 (suppressed by new filters)

### New v3.3 Signals
N=404, Win%=46.0%, Avg P&L=0.1382, Net ATR=+55.8

**Top 5:**
- NVDA 2026-03-05 10:20 BRK bear PD LH L vol=1.4x MFE=8.744 MAE=0.000 P&L=8.744 [WIN] DIM:freshness
- NVDA 2026-03-03 10:20 BRK bear PM L vol=1.1x MFE=8.663 MAE=0.000 P&L=8.663 [WIN] DIM:freshness
- NVDA 2026-01-05 12:05 BRK bear PD LH L vol=1.1x MFE=8.469 MAE=0.000 P&L=8.469 [WIN] DIM:freshness
- NVDA 2026-03-06 15:00 BRK bear Yest L vol=1.5x MFE=8.135 MAE=0.000 P&L=8.135 [WIN] DIM:freshness
- NVDA 2025-12-23 10:30 BRK bear PM L vol=1.4x MFE=5.622 MAE=0.000 P&L=5.622 [WIN] DIM:freshness

**Bottom 5:**
- NVDA 2026-02-11 15:25 BRK bull Week O + Month O vol=1.4x MFE=0.000 MAE=8.956 P&L=-8.956 [LOSS]
- GLD 2026-01-30 13:40 BRK bear Week L vol=1.2x MFE=0.000 MAE=1.865 P&L=-1.865 [LOSS] DIM:exhaustion
- SLV 2026-01-29 10:45 BRK bear VW Band vol=1.0x MFE=0.000 MAE=0.998 P&L=-0.998 [LOSS]
- SPY 2026-02-17 10:35 BRK bear PM L + Yest L + Week L vol=1.1x MFE=0.039 MAE=0.865 P&L=-0.827 [LOSS] DIM:freshness
- SPY 2026-02-17 10:35 BRK bear PM L + Yest L + Week L vol=1.1x MFE=0.039 MAE=0.865 P&L=-0.827 [LOSS] DIM:freshness

### Removed from v3.2 (rightly dimmed/suppressed?)
N=707, Win%=44.8%, Avg P&L=0.0417, Net ATR=+29.5

If these were losers, v3.3 filters are working correctly.

### Signal Type Changes (6 signals)

| Symbol | Time | v3.2 Type | v3.3 Type | v3.3 P&L |
|--------|------|-----------|-----------|----------|
| NVDA | 12-01 12:05 | REV | BRK | -0.017 |
| SPY | 10-30 09:35 | BRK | RNG | +0.000 |
| SPY | 01-02 11:00 | FADE | BRK | -0.005 |
| SPY | 10-31 13:20 | FADE | BRK | -0.326 |
| XLE | 09-30 10:05 | FADE | BRK | +0.359 |
| NVDA | 02-17 13:25 | BRK | REV | -8.295 |

## 8. By Level

| Level | N | Win% | Avg MFE | Avg MAE | Avg P&L | Net ATR |
|-------|:-:|:----:|:-------:|:-------:|:-------:|:-------:|
| range | 1823 | 0.0% | 0.0000 | 0.0000 | 0.0000 | +0.0 |
| ORB H | 1217 | 45.9% | 0.3305 | 0.3531 | -0.0226 | -27.5 |
| VWAP | 997 | 45.1% | 0.3775 | 0.2873 | 0.0902 | +89.9 |
| Yest H | 891 | 42.9% | 0.3799 | 0.3029 | 0.0770 | +68.6 |
| PM H | 818 | 41.9% | 0.2894 | 0.4120 | -0.1226 | -100.3 |
| PM L | 505 | 45.9% | 0.4878 | 0.2759 | 0.2118 | +107.0 |
| Week H | 449 | 45.0% | 0.3867 | 0.3957 | -0.0090 | -4.0 |
| Today O | 420 | 62.1% | 0.5389 | 0.3710 | 0.1679 | +70.5 |
| ORB L | 400 | 53.2% | 0.4946 | 0.1807 | 0.3140 | +125.6 |
| Yest L | 359 | 49.6% | 0.3425 | 0.2664 | 0.0761 | +27.3 |
| PD LH L | 265 | 57.7% | 0.6480 | 0.2673 | 0.3807 | +100.9 |
| PD Cls | 188 | 52.7% | 0.4157 | 0.2762 | 0.1395 | +26.2 |
| Week L | 175 | 39.4% | 0.2084 | 0.4577 | -0.2493 | -43.6 |
| PM H + ORB H | 150 | 56.0% | 0.3099 | 0.3485 | -0.0387 | -5.8 |
| VWAP + ORB H | 146 | 41.8% | 0.2147 | 0.4588 | -0.2441 | -35.6 |
| VWAP + Today O | 133 | 36.1% | 0.6716 | 0.4543 | 0.2173 | +28.9 |
| PM L + ORB L | 126 | 50.8% | 0.6785 | 0.1838 | 0.4947 | +62.3 |
| QBS | 116 | 40.5% | 0.3662 | 0.5311 | -0.1649 | -19.1 |
| VWAP + PM H | 105 | 38.1% | 0.1806 | 0.8408 | -0.6602 | -69.3 |
| PM H + Yest H | 87 | 39.1% | 0.1620 | 0.2995 | -0.1375 | -12.0 |
| Month O | 85 | 57.6% | 0.6818 | 0.6254 | 0.0565 | +4.8 |
| PM L + PD LH L | 73 | 38.4% | 0.3539 | 0.2342 | 0.1197 | +8.7 |
| Week O | 71 | 52.1% | 0.2472 | 0.2174 | 0.0298 | +2.1 |
| Yest H + ORB H | 70 | 45.7% | 0.3037 | 0.3717 | -0.0680 | -4.8 |
| Yest L + PD LH L | 59 | 44.1% | 0.4726 | 0.3600 | 0.1126 | +6.6 |

## 9. Big Move Analysis (rangeATR >= 2.0)

| Group | N | Win% | Avg MFE | Avg MAE | Avg P&L | Net ATR |
|-------|:-:|:----:|:-------:|:-------:|:-------:|:-------:|
| Normal | 8676 | 36.7% | 0.2798 | 0.2933 | -0.0134 | -116.4 |
| Big Move ⚡ | 3278 | 50.2% | 0.4744 | 0.4155 | 0.0589 | +193.1 |

## 10. Top 10 Best & Worst Signals

### Top 10 Best
- NVDA 2026-01-29 10:10 FADE bear at 435.67 vol=Nonex MFE=46.064 MAE=0.000 P&L=46.064 [WIN]
- NVDA 2026-01-26 09:50 FADE bear at 391.97 vol=Nonex MFE=38.498 MAE=0.000 P&L=38.498 [WIN]
- NVDA 2026-03-05 09:40 FADE bear at 399.95 vol=Nonex MFE=33.296 MAE=0.000 P&L=33.296 [WIN]
- NVDA 2026-01-28 09:50 REV bear PM H vol=3.6x MFE=12.757 MAE=0.000 P&L=12.757 [WIN] DIM:freshness
- NVDA 2026-01-29 10:15 BRK bear ORB L + PD LH L vol=1.9x MFE=12.620 MAE=0.000 P&L=12.620 [WIN]
- NVDA 2026-01-28 10:10 REV bear ORB H vol=1.5x MFE=12.559 MAE=0.000 P&L=12.559 [WIN] DIM:freshness
- NVDA 2026-01-29 15:30 BRK bear PD LH L vol=1.8x MFE=12.518 MAE=0.000 P&L=12.518 [WIN]
- NVDA 2026-01-28 09:30 REV bear VWAP + Today O vol=2.0x MFE=12.499 MAE=0.000 P&L=12.499 [WIN]
- NVDA 2026-01-30 11:10 REV bear Yest H vol=0.4x MFE=12.473 MAE=0.000 P&L=12.473 [WIN] DIM:freshness
- NVDA 2026-01-30 10:15 BRK bear PM L vol=2.0x MFE=12.412 MAE=0.000 P&L=12.412 [WIN] DIM:freshness

### Top 10 Worst
- NVDA 2026-01-06 09:50 FADE bull at 325.53 vol=Nonex MFE=0.000 MAE=25.061 P&L=-25.061 [LOSS]
- NVDA 2026-01-07 12:25 FADE bull at 341.7 vol=Nonex MFE=0.000 MAE=28.468 P&L=-28.468 [LOSS]
- NVDA 2026-01-07 10:10 FADE bull at 341.7 vol=Nonex MFE=0.000 MAE=28.694 P&L=-28.694 [LOSS]
- NVDA 2026-02-20 11:35 FADE bull at 422.87 vol=Nonex MFE=0.000 MAE=36.951 P&L=-36.951 [LOSS]
- NVDA 2026-02-20 10:25 FADE bull at 422.87 vol=Nonex MFE=0.000 MAE=36.970 P&L=-36.970 [LOSS]
- NVDA 2026-01-23 13:10 FADE bull at 397.5 vol=Nonex MFE=0.000 MAE=37.374 P&L=-37.374 [LOSS]
- NVDA 2026-01-23 09:55 FADE bull at 397.5 vol=Nonex MFE=0.000 MAE=37.420 P&L=-37.420 [LOSS]
- NVDA 2026-02-02 09:35 FADE bull at 412.18 vol=Nonex MFE=0.000 MAE=38.600 P&L=-38.600 [LOSS]
- NVDA 2026-02-24 09:45 FADE bull at 430.01 vol=Nonex MFE=0.000 MAE=39.197 P&L=-39.197 [LOSS]
- NVDA 2026-01-27 10:00 FADE bull at 410.55 vol=Nonex MFE=0.000 MAE=42.970 P&L=-42.970 [LOSS]

## 11. EMA Alignment

| EMA | N | Win% | Avg MFE | Avg MAE | Avg P&L | Net ATR |
|-----|:-:|:----:|:-------:|:-------:|:-------:|:-------:|
| Aligned | 7948 | 46.3% | 0.3836 | 0.3606 | 0.0231 | +183.3 |
| Counter | 1569 | 48.9% | 0.4043 | 0.3501 | 0.0542 | +85.1 |

## 12. Direction

| Dir | N | Win% | Avg P&L | Net ATR |
|-----|:-:|:----:|:-------:|:-------:|
| Bull | 5496 | 37.0% | -0.3676 | -2020.3 |
| Bear | 6458 | 43.3% | 0.3247 | +2096.9 |
