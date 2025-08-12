# Mantle (MNT/USDT) Event-Driven Trading Strategy Backtest

A comprehensive Python script for backtesting an event-driven trading strategy based on X (Twitter) posts from @0xMantle.

## Features

- **X Posts Analysis**: Simulates fetching and analyzing historical posts from @0xMantle
- **AI Impact Assessment**: Simulates Grok AI scoring system (1-10) for post impact
- **Real-time Price Data**: Fetches historical prices from CoinGecko API with 5-minute resolution
- **Trading Simulation**: Executes buy/sell trades with configurable parameters
- **P&L Calculation**: Detailed profit/loss tracking with zero fees/slippage
- **Results Visualization**: Comprehensive results table and summary statistics
- **TradingView Integration**: Generates Pine Script code for chart visualization

## Strategy Details

- **Monitoring**: @0xMantle X account posts
- **Trigger**: High-impact posts (score >7) trigger $1,000 USDT buy orders
- **Hold Period**: Exactly 30 minutes per trade
- **Trading Pair**: MNT/USDT (Binance simulation)
- **Position Stacking**: Multiple trades can overlap

### High-Impact Criteria (User Configurable)

The AI assessment looks for these categories:
- **Major Partnerships**: partnership, collaboration, integrate, alliance
- **Major Launches**: launch, mainnet, release, deploy, live  
- **Major Rewards**: rewards, airdrop, incentive, staking
- **Milestones**: milestone, upgrade, listing, exchange
- **Strategic Shifts**: strategic, roadmap, vision, future

Low-impact keywords (ignored): ama, meme, gm, gn, thread, reminder

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Set optional environment variables for live data:

```bash
export COINGECKO_API_KEY="your_coingecko_api_key"
export X_BEARER_TOKEN="your_twitter_bearer_token"
```

**Note**: The script includes sample data fallback, so it works without API keys.

## Usage

```bash
python mantle_trading_backtest.py
```

## Customization

Modify the `TradingConfig` class to adjust:

- Position size (`POSITION_SIZE_USDT`)
- Hold duration (`HOLD_DURATION_MINUTES`) 
- Impact threshold (`HIGH_IMPACT_THRESHOLD`)
- Date range (`START_DATE`, `END_DATE`)
- Assessment keywords (`HIGH_IMPACT_KEYWORDS`, `LOW_IMPACT_KEYWORDS`)

## Output

The script provides:

1. **Processing Log**: Real-time analysis of each post
2. **Trades Table**: Detailed breakdown of all executed trades
3. **Summary Statistics**: Total P&L, win rate, average return
4. **Pine Script Code**: Copy-paste ready code for TradingView

## TradingView Integration

1. Copy the generated Pine Script code
2. Open TradingView and go to Pine Editor
3. Paste the code and add to chart
4. Set chart to BINANCE:MNTUSDT, 5-minute timeframe
5. View buy/sell signals with position highlighting

## Example Output

```
TRADES TABLE:
Trade#  Post Time        Buy Price  Sell Price  MNT Bought  P&L ($)  Return (%)
1       2024-08-10 10:30  0.5800     0.5950      1724.14    25.86     2.59
2       2024-08-11 09:45  0.6100     0.5980      1639.34   -19.67    -1.97
3       2024-08-12 12:00  0.6200     0.6450      1612.90    40.32     4.03

SUMMARY STATISTICS:
Total Trades: 3
Total P&L: $46.51
Average Return: 1.55%
Win Rate: 66.7%
```

## Limitations

- Uses sample data when API keys unavailable
- CoinGecko free tier provides daily prices (interpolated to 5-minute)
- X API v2 implementation requires proper authentication
- No transaction fees or slippage included

## License

This script is for educational and backtesting purposes only. Not financial advice.