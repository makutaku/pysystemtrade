# Project Overview

## What is pysystemtrade?

**pysystemtrade** is a comprehensive, enterprise-grade systematic futures trading framework written in Python. It implements the trading methodology outlined in Rob Carver's book ["Systematic Trading"](https://www.systematicmoney.org/systematic-trading) and represents a production system that the author uses for live trading 20 hours a day, 5 days a week with real capital.

This is not an academic exercise or toy system - it's a professional trading infrastructure that handles millions of dollars in systematic futures trading across global markets.

## System Architecture Philosophy

### 🏗️ **Enterprise Design Principles**
- **Separation of Concerns** - Clear boundaries between data, strategy, execution, and monitoring
- **Fail-Safe Operations** - Multiple layers of risk controls and error handling
- **Production Reliability** - Designed for 24/7 operation with minimal intervention
- **Scalable Architecture** - Supports multiple strategies and hundreds of instruments
- **Audit Trail** - Complete trade and decision logging for regulatory compliance

### 🎯 **Complete Trading Ecosystem**

**Research & Development:**
- **Sophisticated Backtesting** - Multi-asset, multi-strategy with realistic costs
- **Strategy Development** - Modular trading rule framework with 20+ built-in rules
- **Performance Analysis** - Comprehensive risk and return analytics
- **Parameter Optimization** - Bayesian shrinkage and portfolio optimization

**Production Trading:**
- **Automated Execution** - Three-tier order management system
- **Real-time Risk Management** - Dynamic position limits and override controls  
- **Process Orchestration** - Cron-scheduled processes with dependency management
- **Live Monitoring** - Web dashboard and email alerting system

**Data Infrastructure:**
- **Multi-Backend Storage** - MongoDB (operational), Parquet (time series), CSV (config)
- **Real-time Feeds** - Interactive Brokers integration with tick-level data
- **Data Quality** - Spike detection, validation, and automated cleaning
- **Backup & Recovery** - Multiple backup strategies with offsite storage

## Technical Sophistication

### 📊 **Advanced Quantitative Methods**
- **Portfolio Optimization** - Mean-variance, shrinkage, and hierarchical methods
- **Risk Management** - Volatility targeting, correlation shock protection
- **Statistical Estimation** - Robust volatility, correlation pooling, Bayesian methods
- **Signal Processing** - EWMA filtering, breakout detection, carry analysis

### 🔧 **Production Engineering**
- **Three-Tier Order System** - Instrument → Contract → Broker order management
- **Execution Algorithms** - Market, limit, adaptive, and TWAP execution
- **Process Control** - Finite state machine process management
- **Data Pipelines** - Automated data collection, cleaning, and distribution

### 🛡️ **Risk & Compliance**
- **Position Limits** - Instrument, strategy, and portfolio-level controls
- **Override System** - Manual intervention capabilities for risk management
- **Audit Logging** - Complete trade and decision audit trail
- **Reconciliation** - Automated position and P&L reconciliation

## Core System Components

### Data Layer (`sysdata/`)
**Architecture:** dataBlob pattern provides unified access to multiple data sources
- **CSV Sources** - Configuration data and historical backtesting data
- **MongoDB** - Real-time operational data (orders, positions, process state)
- **Parquet** - High-performance time series storage
- **Interactive Brokers** - Live market data and trade execution

### Business Objects (`sysobjects/`)
**Domain Model:** Rich object model representing financial concepts
- **Instruments & Contracts** - Futures instrument and contract management
- **Price Data** - Multiple prices, adjusted prices with Panama stitching
- **Positions** - Hierarchical position tracking (instrument → contract → broker)
- **Roll Management** - Sophisticated contract roll scheduling and execution

### Trading System (`systems/`)
**Backtesting Engine:** Stage-based processing pipeline
- **Raw Data Stage** - Price processing and volatility calculation
- **Forecasting** - Trading rule execution and signal generation
- **Position Sizing** - Volatility-targeted position calculation
- **Portfolio Construction** - Multi-instrument optimization
- **Accounting** - P&L calculation and performance analytics

### Execution Engine (`sysexecution/`)
**Order Management:** Three-tier order processing system
- **Algorithm Framework** - Pluggable execution algorithms
- **Stack Processing** - Hierarchical order spawning and fill propagation
- **Market Data** - Real-time ticker objects and market analysis
- **Trade Quantity** - Multi-leg trade support and proportional sizing

### Production Framework (`sysproduction/`)
**Live Trading:** Complete production trading orchestration
- **Process Control** - Scheduled process execution with dependency management
- **Strategy Execution** - Multiple strategy types (buffered, optimized)
- **Reporting System** - Automated P&L, risk, and operational reports
- **Interactive Tools** - Order management and system administration

### Quantitative Framework (`sysquant/`)
**Analytics Engine:** Advanced statistical and optimization methods
- **Portfolio Optimization** - Multiple approaches (shrinkage, handcraft, equal weight)
- **Statistical Estimation** - Correlation, volatility, and mean return estimation
- **Risk Analytics** - Portfolio risk calculation and stress testing

## Production Capabilities

### 🔄 **Automated Operations**
- **Daily Backtesting** - Overnight system runs to generate new positions
- **Order Generation** - Automated strategy order creation throughout the day
- **Execution Management** - Continuous order processing and execution
- **Risk Monitoring** - Real-time position and risk monitoring
- **Data Updates** - Automated price and reference data updates

### 📈 **Strategy Management**
- **Multi-Strategy** - Simultaneous execution of different strategies
- **Dynamic Capital** - Automated capital allocation across strategies  
- **Performance Tracking** - Strategy-level P&L and risk attribution
- **Override Controls** - Manual intervention and risk management

### 🔍 **Monitoring & Reporting**
- **Process Dashboard** - HTML dashboard showing all process states
- **Email Alerting** - Critical error and status notifications
- **Performance Reports** - Daily P&L, risk, and execution quality reports
- **Trade Analysis** - Slippage, execution costs, and timing analysis

## System Components

### Core Modules

| Module | Purpose |
|--------|---------|
| `systems/` | Backtesting framework and trading strategies |
| `sysdata/` | Data storage and access layer |
| `sysbrokers/` | Broker integration (Interactive Brokers) |
| `sysproduction/` | Live trading and production management |
| `sysexecution/` | Order management and execution |
| `sysobjects/` | Data objects and business logic |
| `sysquant/` | Quantitative analysis and optimization |

### Data Flow

```
Raw Data → Systems Processing → Production Execution → Storage
    ↓              ↓                      ↓             ↓
Price data → Signals/Positions → Orders/Fills → Database
```

## Trading Methodology

### Stage-Based Processing
1. **Raw Data** - Price data from brokers/CSV files
2. **Trading Rules** - Generate forecasts from price data
3. **Forecast Scaling** - Normalize forecasts to target volatility
4. **Forecast Combination** - Combine multiple trading rules
5. **Position Sizing** - Size positions based on volatility targeting
6. **Portfolio Construction** - Combine multiple instruments
7. **Execution** - Generate and execute trades

### Built-in Trading Rules
- **EWMAC** - Exponentially weighted moving average crossover
- **Breakout** - Price breakout strategies
- **Carry** - Futures curve slope trading
- **Mean Reversion** - Price reversion strategies
- **Momentum** - Trend following strategies

## Use Cases

### 1. **Backtesting**
Perfect for:
- Strategy research and development
- Historical performance analysis
- Risk assessment and optimization
- Academic research

### 2. **Live Trading**
Ideal for:
- Systematic futures trading
- Multi-strategy portfolio management
- Institutional trading operations
- Individual systematic traders

### 3. **Research Platform**
Great for:
- Quantitative finance research
- Strategy development
- Market microstructure analysis
- Portfolio optimization studies

## Who Should Use pysystemtrade?

### ✅ **Ideal Users**
- **Systematic traders** looking for a complete framework
- **Quantitative researchers** needing robust backtesting
- **Python developers** comfortable with complex systems
- **Futures traders** wanting professional-grade tools

### ⚠️ **Consider Carefully If You're**
- **New to Python** - steep learning curve
- **Equity-focused** - designed primarily for futures
- **Day trader** - built for longer-term systematic strategies
- **Beginner trader** - requires significant trading knowledge

## Getting Started

1. **Read the Documentation** - Start with [Installation Guide](installation.md)
2. **Set Up Environment** - Install dependencies and configure system
3. **Try Examples** - Run provided examples and tutorials
4. **Build Your Strategy** - Develop and backtest your trading rules
5. **Go Live** - Deploy to production with real capital

## Support and Resources

- **Official Repository** - [github.com/robcarver17/pysystemtrade](https://github.com/robcarver17/pysystemtrade)
- **Author's Blog** - [qoppac.blogspot.com](https://qoppac.blogspot.com)
- **Book** - ["Systematic Trading" by Rob Carver](https://www.systematicmoney.org/systematic-trading)
- **Issues** - [GitHub Issues](https://github.com/robcarver17/pysystemtrade/issues)

## License and Disclaimer

- **License** - GNU GPL v3
- **Disclaimer** - No warranty. Use at your own risk. Trading involves significant financial risk.

---

**Next:** [Installation Guide](installation.md) to get started with pysystemtrade.