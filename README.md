# Key Level Breakout

TradingView Pine Script v6 indicators that detect when a bullish/bearish candle closes through key price levels. Designed for US stocks (NYSE/NASDAQ) on 5-minute charts.

| Variant | File | Use Case |
|---------|------|----------|
| [Single-Symbol](KeyLevelBreakout.md) | `KeyLevelBreakout.pine` | Visual markers + arrows on one chart |
| [Multi-Symbol Scanner](KeyLevelScanner.md) | `KeyLevelScanner.pine` | Monitor up to 8 tickers with one alert |

## Levels

| Level | Source |
|-------|--------|
| **Premarket High/Low** | Tracked bar-by-bar during premarket (0400-0930 ET), frozen at open |
| **Yesterday High/Low** | Previous daily high/low via `request.security` (non-repainting) |
| **Last Week High/Low** | Previous weekly high/low via `request.security` (non-repainting) |
| **ORB High/Low** | High/low of the first 5-min bar at 9:30 ET |

## Breakout Logic

- **Bullish**: Candle is green + closes above a high level + previous close was at or below
- **Bearish**: Candle is red + closes below a low level + previous close was at or above
