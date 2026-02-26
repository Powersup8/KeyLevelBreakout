# KeyLevelBreakout — Label Reference

## What This Indicator Does

Imagine a price level on the chart — like yesterday's highest price ($150). This level matters because many traders are watching it. When price reaches this level, one of four things can happen:

**Breakout** — Price pushes through the level and keeps going. Like a runner breaking through a finish line tape. The level is defeated, momentum continues. *"Price broke above $150 — buyers are in control."*

**Retest** — After a breakout, price comes back to check if the level still holds. Like knocking on a door you just walked through to make sure it's still open. If it holds, the breakout is confirmed. *"Price broke $150, dipped back to $150, and bounced — $150 is now support."*

**Reversal** — Price approaches the level, pokes into it, but gets rejected. Like bouncing off a wall. The level wins, price turns around. *"Price tried to reach $150 but sellers pushed it back down."*

**Reclaim** — A breakout happened earlier but failed — price fell back through. Now price approaches the level again and gets rejected. This is stronger than a regular reversal because traders who bought the breakout are now trapped. *"Price broke $150, fell back below, tried again, rejected again — the breakout was a trap."*

### Reading the Labels

Each label has up to 3 parts, separated by line breaks:

```
Yest H              ← WHAT: which level (Yesterday High)
2.1x ^78            ← HOW STRONG: 2.1x average volume, close at 78% of candle range
◆³ Yest H 1.9x ^80 ← RETEST: came back 3 bars later, held with good quality
```

- **Volume ratio** (`2.1x`): How much more volume than normal. Higher = more conviction.
- **Close position** (`^78`): Where the candle closed within its range. `^78` means 78% toward the high — buyers dominated. `v85` means 85% toward the low — sellers dominated.
- **Retest bar count** (`◆³`): The small number shows how many bars after the breakout the retest happened.

## Label Format

### Breakout Label (default mode)

```
PM H + Yest H        ← Line 1: which level(s) broke (merged if confluent)
1.8x ^82             ← Line 2: volume ratio + close position %
◆³ PM H 2.1x ^85    ← Line 3+: retests (appended as they come in)
◆⁷ Yest H 1.4x ^71  ← one line per level retested
```

## Breakout Label (failed)

```
PM H + Yest H
1.8x ^82
✗                    ← price closed back through level → grayed out
```

## Reversal Label

```
~ Yest L              ← ~ prefix = reversal (rejection off zone)
1.5x ^74
```

## Reclaim Label

```
~~ Yest H             ← ~~ prefix = reclaim (reversal after failed breakout)
2.3x v85
```

## Retest-Only Mode

Breakout becomes a tiny gray `·` dot. Retest fires its own label:

```
◆³ ORB H              ← superscript = bars since breakout
2.1x ^85
```

## Setup Summary (Yest H = $150)

| Setup | Scenario | Label | Color |
|---|---|---|---|
| **Breakout** | Price closes above $150 on green candle with volume → LONG | `Yest H`<br>`2.1x ^78` | Green |
| **Retest** `◆` | 3 bars later, price dips back to $150, holds above → confirms LONG | `Yest H`<br>`2.1x ^78`<br>`◆³ Yest H 1.9x ^80` | Green (appended) |
| **Failed** `✗` | Price closes back below $150 → breakout dead | `Yest H`<br>`2.1x ^78`<br>`✗` | Gray |
| **Reversal** `~` | Wick enters $150 zone from below, close rejects below → SHORT | `~ Yest H`<br>`1.8x v82` | Orange |
| **Reclaim** `~~` | After failed breakout above $150, price approaches again, rejected below → SHORT | `~~ Yest H`<br>`2.3x v85` | Orange (brighter) |

## Timeline Example

### Single level (Yest H = $150)

```
Bar 1:  Price closes above $150        → Breakout fires (LONG)
                                          ┌────────────┐
                                          │ Yest H     │ green
                                          │ 2.1x ^78   │
                                          └────────────┘

Bar 4:  Price dips to $150, holds      → Retest detected
                                          ┌──────────────────────┐
                                          │ Yest H               │ green
                                          │ 2.1x ^78             │
                                          │ ◆³ Yest H 1.9x ^80  │
                                          └──────────────────────┘

                    ── OR ──

Bar 4:  Price closes below $150        → Failed
                                          ┌────────────┐
                                          │ Yest H     │ gray
                                          │ 2.1x ^78   │
                                          │ ✗          │
                                          └────────────┘

Bar 8:  Price approaches $150 again,   → Reclaim fires (SHORT)
        wick enters zone, rejected       ┌────────────┐
                                          │ ~~ Yest H  │ orange
                                          │ 2.3x v85   │
                                          └────────────┘
```

### Confluent levels (ORB H + Yest H both at ~$150)

```
Bar 1:  Both levels break              → Merged breakout
                                          ┌──────────────────────────┐
                                          │ ORB H + Yest H           │ green
                                          │ 1.8x ^82                 │
                                          └──────────────────────────┘

Bar 4:  ORB H retested                 → First retest appended
                                          ┌──────────────────────────┐
                                          │ ORB H + Yest H           │
                                          │ 1.8x ^82                 │
                                          │ ◆³ ORB H 2.1x ^85       │
                                          └──────────────────────────┘

Bar 8:  Yest H retested                → Second retest appended
                                          ┌──────────────────────────┐
                                          │ ORB H + Yest H           │
                                          │ 1.8x ^82                 │
                                          │ ◆³ ORB H 2.1x ^85       │
                                          │ ◆⁷ Yest H 1.4x ^71      │
                                          └──────────────────────────┘
```

## Visual Examples with Price Action

All examples use **Yest H = $150.00** with zone body edge at $149.50 (wick-to-body zone = $149.50–$150.00).

Candle convention: **wide = body** (between open and close), **thin = wick** (shadows beyond the body).

### Example 1: Bullish Breakout → Retest Confirmed

```
           Bar 1 (GREEN)                Bar 4 (GREEN) — retest
           O:149.80 H:151.00            O:150.10 H:150.80
           C:150.60 L:149.60            C:150.70 L:149.80

  $151 ┤      │
$150.6 ┤   ┌──┘ ← C                       │
       │   │                            ┌──┘ ← C:150.70
$150.1 ┤   │                            │
  $150 ┤───│─────level──────────────────│─────────────
       │   └──┐ ← O                    └──┐ ← O:150.10
$149.8 ┤      │                            │ ← L:149.80
$149.6 ┤      │ ← L                       ·
       │
       │  ┌────────────┐              ┌──────────────────────┐
       │  │ Yest H     │              │ Yest H               │
       │  │ 2.1x ^78   │    becomes → │ 2.1x ^78             │
       │  └────────────┘              │ ◆³ Yest H 1.9x ^90  │
       │                              └──────────────────────┘
```

**Bar 1 breakout:** Green candle (C>O). Close $150.60 above level $150. Open $149.80 was below.
**^78:** (150.60−149.60)/(151.00−149.60) = 71%. Close in upper part of range → strong.
**Bar 4 retest:** Low $149.80 dipped to within buffer of $150, close $150.70 above → level held as support.

---

### Example 2: Bullish Breakout → Failed

```
           Bar 1 (GREEN)                Bar 5 (RED) — failure
           O:149.80 H:151.00            O:150.20 H:150.50
           C:150.60 L:149.60            C:148.90 L:148.70

  $151 ┤      │
$150.6 ┤   ┌──┘ ← C                    ┌──┐ ← O:150.20
       │   │                            │  │
  $150 ┤───│─────level──────────────────│──│──────────
       │   └──┐ ← O                    │  │
$149.6 ┤      │ ← L                    │  │
       │                               │  │
  $149 ┤                               │  └──┐ ← C:148.90
$148.7 ┤                               │     │ ← L:148.70
       │                               └─────┘
       │
       │  ┌────────────┐
       │  │ Yest H     │ gray
       │  │ 2.1x ^78   │
       │  │ ✗          │
       │  └────────────┘
```

**Why it failed:** Bar 5 is a red candle. Close $148.90 fell below $150 minus the re-arm buffer → breakout dead, label grayed out.

---

### Example 3: Bearish Reversal at HIGH Level

```
           Bar 1 (RED) — reversal
           O:149.90 H:150.80
           C:149.20 L:149.10

$150.8 ┤      │ ← H
       │   ┌──┘
  $150 ┤───│───── level ──────────
       │   └──┐ ← O:149.90
$149.5 ┤──zone│──body─ ─ ─ ─ ─ ─ ─
       │      │
$149.2 ┤      └──┐ ← C:149.20
$149.1 ┤         │ ← L:149.10
       │
       │  ┌────────────┐
       │  │ ~ Yest H   │ orange
       │  │ 1.8x v82   │
       │  └────────────┘
```

**Why it's a reversal:** Wick pushed INTO the zone (H:$150.80 > body edge $149.50), but close rejected BELOW the body edge ($149.20 < $149.50). Red candle (C<O). Sellers defended the level → SHORT.
**v82:** (150.80−149.20)/(150.80−149.10) = 94%. Close near the low → strong selling pressure.

---

### Example 4: Breakout → Failed → Reclaim

This is a 3-act story at the same level:

```
  ACT 1: BREAKOUT (GREEN)       ACT 2: FAILED (RED)          ACT 3: RECLAIM (RED)
  O:149.80 C:150.60              O:150.20 C:148.90             O:149.90 C:149.10
  H:151.00 L:149.60              H:150.50 L:148.70             H:150.80 L:149.00

  $151 ┤    │
$150.6 ┤ ┌──┘ ← C              ┌──┐ ← O                          │ ← H
  $150 ┤─│──── level ──────────│──│───── level ──────────────── ──┘───── level ──
       │ └──┐ ← O              │  │                            ┌──┘ ← O:149.90
$149.5 ┤    │ ← L              │  │                            │
       │                       │  │                            │
  $149 ┤                       │  └──┐ ← C                    └──┐ ← C:149.10
$148.7 ┤                       │     │ ← L                       │ ← L:149.00
       │                       └─────┘                           ·
       │  ┌────────────┐     ┌────────────┐                   ┌────────────┐
       │  │ Yest H     │     │ Yest H     │ gray              │ ~~ Yest H  │ orange
       │  │ 2.1x ^78   │     │ 2.1x ^78   │                   │ 2.3x v85   │
       │  └────────────┘     │ ✗          │                   └────────────┘
       │                     └────────────┘
```

**Act 1:** Green candle closes above $150 → LONG signal.
**Act 2:** Red candle closes at $148.90, below $150 → breakout failed, `hadBrk = true`.
**Act 3:** Wick reaches $150.80 (into zone), but close rejects at $149.10 → **Reclaim** (not just reversal) because prior breakout failed. The `~~` prefix signals trapped longs → SHORT.

---

### Example 5: Confluent Breakout → Per-Level Retests

Two levels near each other: **ORB H = $149.80**, **Yest H = $150.20**

```
           Bar 1 (GREEN)       Bar 4 (GREEN)         Bar 8 (GREEN)
           O:149.50 C:150.90   O:150.30 C:150.10     O:150.10 C:150.80
           H:151.30 L:149.40   H:150.40 L:149.70     H:150.90 L:150.00

$151.3 ┤   │ ← H
  $151 ┤   │
$150.9 ┤┌──┘ ← C                                        ┌──┘ ← C:150.80
       ││
$150.2 ┤│───── Yest H ──────── ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ──│──── Yest H ────
       ││                     ┌──┐ ← O:150.30          │
$149.8 ┤│───── ORB H ─────────│──│── ORB H ── ─ ─ ─ ──└──┐ ← O:150.10
       ││                     │  └──┐ ← C:150.10       ← L:150.00
$149.5 ┤└──┐ ← O              │     │ ← L:149.70
       │   │ ← L:149.40       └─────┘
       │
       │  ┌──────────────────────────┐
       │  │ ORB H + Yest H           │
       │  │ 1.8x ^82                 │
       │  │ ◆³ ORB H 2.1x ^57       │
       │  │ ◆⁷ Yest H 1.4x ^89      │
       │  └──────────────────────────┘
```

**Bar 1:** Both levels break on same green candle → merged label.
**Bar 4:** Low $149.70 dips near ORB H ($149.80), close $150.10 holds above → ORB H retest. ^57: (150.10−149.70)/(150.40−149.70)=57%.
**Bar 8:** Low $150.00 dips near Yest H ($150.20), close $150.80 holds above → Yest H retest. ^89: (150.80−150.00)/(150.90−150.00)=89%.

---

### Example 6: Retest Quality — What the Candle Tells You

After a bullish breakout above Yest H = $150, price comes back. The retest candle's shape tells you how strong the hold is:

**6a) Strong retest — green candle, wick dips to level, close recovers near high**
```
           O:150.10 H:150.80 C:150.70 L:149.80

$150.8 ┤   │ ← H
$150.7 ┤┌──┘ ← C                ^90: (150.70−149.80)/(150.80−149.80) = 90%
       ││                       → close near the high, buyers in control
  $150 ┤│──── level ────────    ◆³ Yest H 1.9x ^90
       │└──┐ ← O:150.10
$149.8 ┤   │ ← L
```
Wick tested $150, buyers pushed it right back up. Best quality retest.

**6b) Decent retest — red candle, wick dips, close still above level**
```
           O:150.70 H:150.80 C:150.20 L:149.80

$150.8 ┤   │ ← H
$150.7 ┤┌──┘ ← O                ^40: (150.20−149.80)/(150.80−149.80) = 40%
       ││   body                → sellers pushed down, but level held
$150.2 ┤└──┐ ← C:150.20         ◆³ Yest H 1.5x ^40
  $150 ┤───│── level ────────   close above $150 → level held
$149.8 ┤   │ ← L                red candle, but retest valid
```
Bearish candle — sellers present, but $150 held. `^40` = contested, still valid, lower quality.

**6c) Weak retest — red candle, sellers dominated, close barely holds**
```
           O:150.70 H:150.80 C:150.05 L:149.95

$150.8 ┤   │ ← H
$150.7 ┤┌──┘ ← O                ^12: (150.05−149.95)/(150.80−149.95) = 12%
       ││   body                → sellers dominated, close barely above level
       ││
       ││
$150.05┤└──┐ ← C:150.05         ◆³ Yest H 1.2x ^12
  $150 ┤───│── level ────────   close just $0.05 above level!
$149.95┤   │ ← L                warning: level is very weak
```
Close barely above $150. `^12` screams weakness. Level hanging by a thread. Next candle may fail.

**6d) NOT a retest — close below level → FAILURE**
```
           O:150.50 H:150.80 C:149.40 L:149.20

$150.8 ┤   │ ← H
$150.5 ┤┌──┘ ← O                ✗ FAILED
       ││                       close $149.40 below level − rearmBuf
  $150 ┤││─── level ────────    → breakout is dead, label grays out
       ││
       ││
$149.4 ┤└┘─┐ ← C:149.40
$149.2 ┤   │ ← L
```
Close fell well below $150. Not a retest — it's a failure. Breakout invalidated.

**What the close position `^` number tells you at a retest:**

| ^Value | Meaning | What it tells you |
|--------|---------|-------------------|
| `^80+` | Close near the high | Strong hold — buyers in control |
| `^50-79` | Close in upper half | Decent hold — contested but held |
| `^20-49` | Close in lower half | Weak hold — sellers present, be cautious |
| `^1-19` | Close barely above level | Very weak — level may break next bar |
| (failure) | Close below level | Not a retest — breakout failed |

---

### Key Differences at a Glance

```
                    BREAKOUT          RETEST            REVERSAL          RECLAIM
                    ════════          ══════            ════════          ═══════
What happens?       Closes through    Pulls back,       Wick enters       Same as reversal,
                    the level         holds on           zone, close       but after a prior
                                      breakout side      rejects out       breakout failed

Prior breakout?     No                Yes (held)         No                Yes (failed)

Direction?          With the break    Confirms break     Against approach   Against trapped side

Candle?             Green (bull)      Green at support   Red at resistance  Red at resistance
                    Red (bear)        Red at resistance  Green at support   Green at support

When?               Any time          2+ bars after      Setup window       Setup window
                                      breakout           (9:30-11:30)       (9:30-11:30)

Label?              New label         Appended to        New label          New label
                                      breakout label     ~ prefix           ~~ prefix
```

## Metrics

| Symbol | Meaning | Example |
|--------|---------|---------|
| `1.8x` | Volume ratio vs baseline | 1.8x average volume |
| `^82` | Bull close position (82% toward high) | Strong buying |
| `v85` | Bear close position (85% toward low) | Strong selling |
| `◆³` | Retest detected 3 bars after breakout | |
| `✓` | Auto-promoted (survived until next breakout) | |
| `✗` | Failed (closed back through level) | |
| `~` | Reversal (rejection) | |
| `~~` | Reclaim (reversal after failed breakout) | |

## Colors

| Color | Meaning |
|-------|---------|
| Green | Bullish breakout (opacity scales with volume) |
| Red | Bearish breakout (opacity scales with volume) |
| Blue | Bullish reversal/reclaim |
| Orange | Bearish reversal/reclaim |
| Gray | Failed or old (faded) |
