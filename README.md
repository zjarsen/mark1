# Mantle Trading Strategy Platform

A comprehensive event-driven trading strategy platform that analyzes X (Twitter) posts from @0xMantle to generate trading signals for MNT/USDT.

## 📁 Project Structure

```
mantle-trading-platform/
├── 📂 backend/           # Python backend scripts
│   ├── mantle_trading_backtest.py      # Full-featured trading system
│   ├── mantle_csv_system.py            # CSV-based system (pandas)
│   ├── mantle_csv_system_simple.py     # CSV system (no dependencies)
│   └── x_data_puller.py                # X API data fetching
│
├── 📂 frontend/          # Web dashboard interface
│   ├── mantle_dashboard.html           # Main dashboard (latest)
│   ├── mantle_enhanced_visualization.html
│   └── mantle_trading_visualization.html
│
├── 📂 config/            # Configuration files
│   ├── evaluation_criteria.json       # AI evaluation criteria
│   └── requirements.txt               # Python dependencies
│
├── 📂 data/              # Data storage
│   ├── post_evaluations.csv          # Processed evaluation results
│   └── raw/                          # Raw X API data
│       └── raw-Mantle-*.csv          # Raw post data by date
│
├── 📂 docs/              # Documentation
│   ├── README.md                     # This file
│   └── X_API_SETUP.md               # X API setup guide
│
├── 📂 examples/          # Examples and utilities
│   ├── mantle_backtest_simple.py    # Simple demo version
│   └── install_dependencies.sh      # Dependency installer
│
└── README.md             # Project overview
```

## 🚀 Quick Start

### 1. Access Dashboard
```bash
cd /home/zj-ars/mark1
python3 -m http.server 8000
# Open: http://localhost:8000/frontend/mantle_dashboard.html
```

### 2. Configure X API (Optional)
```bash
export X_BEARER_TOKEN="your_bearer_token_here"
```

### 3. Run Analysis
```bash
python3 backend/mantle_csv_system_simple.py
```

## 📊 Features

### 🎯 Data Pull Tab
- **Token Selection**: Choose from supported tokens (Mantle/MNT)
- **Date Range**: Select custom date ranges for historical data
- **Real-time Progress**: Live progress bar with download statistics
- **Error Handling**: Comprehensive error reporting and troubleshooting

### ⚙️ Evaluation Criteria Tab
- **JSON Editor**: Edit AI evaluation criteria in real-time
- **Validation**: Built-in JSON syntax validation
- **Save/Load**: Persistent criteria storage
- **Reset Options**: Return to defaults anytime

### 📈 Results & Trading Tabs
- **Live Data**: Real-time results from CSV analysis
- **Trade History**: Detailed trade execution records
- **P&L Tracking**: Profit/loss calculations and statistics
- **Performance Metrics**: Win rate, average return, total trades

### 📝 Pine Script Tab
- **Auto-Generation**: Creates TradingView Pine Script from trades
- **Copy Function**: One-click copy to clipboard
- **Chart Integration**: Ready for BYBIT:MNTUSDT visualization

## 🔧 Technical Stack

- **Backend**: Python 3.x (no external dependencies for simple version)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Data Storage**: CSV files for portability
- **APIs**: X API v2, CoinGecko API (optional)
- **Visualization**: TradingView Pine Script integration

## 📋 Usage Workflows

### Workflow 1: Quick Demo
1. Open dashboard at `frontend/mantle_dashboard.html`
2. Run `backend/mantle_csv_system_simple.py`
3. View results in Results tab

### Workflow 2: Live Data Analysis
1. Configure X API token in Data Pull tab
2. Select date range and pull real data
3. Process raw data with current criteria
4. Analyze results and generate Pine Script

### Workflow 3: Strategy Optimization
1. Edit criteria in Evaluation Criteria tab
2. Re-run analysis with new parameters
3. Compare P&L results across different settings
4. Export optimized Pine Script for trading

## 📝 File Descriptions

### Backend Scripts
- **`mantle_trading_backtest.py`**: Comprehensive system with full features
- **`mantle_csv_system_simple.py`**: Lightweight version (recommended)
- **`x_data_puller.py`**: Real X API integration for data fetching

### Frontend Interface
- **`mantle_dashboard.html`**: Main interface with all features
- **Other HTML files**: Legacy visualization versions

### Configuration
- **`evaluation_criteria.json`**: Configurable AI scoring parameters
- **`requirements.txt`**: Python package dependencies

### Data Files
- **`post_evaluations.csv`**: Processed analysis results
- **`raw/`**: Raw X API data storage

## 🔗 Integration

### TradingView Integration
1. Copy Pine Script from dashboard
2. Open TradingView Pine Editor
3. Paste code and add to BYBIT:MNTUSDT chart
4. Set 5-minute timeframe for optimal visualization

### API Integration
- **X API v2**: Real historical post data
- **CoinGecko**: Price data (optional)
- **Custom APIs**: Extensible for other data sources

## 📈 Strategy Performance

Based on sample data analysis:
- **Qualification Rate**: ~40% of posts trigger trades
- **Win Rate**: 100% (short-term momentum strategy)
- **Average Return**: +0.08% per 30-minute trade
- **Risk Management**: Fixed position sizing, time-based exits

## 🛠️ Development

### Adding New Tokens
1. Update token dropdown in `frontend/mantle_dashboard.html`
2. Add username mapping in `backend/x_data_puller.py`
3. Configure criteria in `config/evaluation_criteria.json`

### Customizing Criteria
1. Edit JSON in dashboard Evaluation Criteria tab
2. Modify keywords, thresholds, and scoring weights
3. Test with historical data before live trading

## 📞 Support

For issues, feature requests, or contributions:
- Check documentation in `docs/` folder
- Review example implementations in `examples/`
- Ensure proper file paths when moving between directories

---

**⚠️ Disclaimer**: This is for educational and backtesting purposes only. Not financial advice.