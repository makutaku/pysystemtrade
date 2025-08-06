# Quick Start Guide

Get up and running with pysystemtrade in 10 minutes. This guide walks you through creating your first systematic trading strategy.

## Prerequisites

- Python 3.10+ installed
- pysystemtrade installed ([Installation Guide](installation.md))
- Basic Python knowledge
- 10 minutes of your time!

## Your First Trading System

### Step 1: Import Required Libraries

```python
# Data and system imports
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
from systems.basesystem import System
from systems.forecasting import Rules
from systems.provided.rules.ewmac import ewmac_forecast_with_defaults as ewmac

# Create data object
data = csvFuturesSimData()
print(f"Available instruments: {len(data.get_instrument_list())}")
print(f"Sample instruments: {data.get_instrument_list()[:5]}")
```

### Step 2: Build a Simple Trading Rule

```python
# Create a simple EWMAC (moving average crossover) rule
my_rules = Rules(dict(ewmac=ewmac))

# Create system with rules and data
my_system = System([my_rules], data)

# Get a forecast for an instrument
forecast = my_system.rules.get_raw_forecast("SOFR", "ewmac")
print(f"Latest SOFR forecast: {forecast.tail(3)}")
```

### Step 3: Scale and Cap Forecasts

```python
from systems.forecast_scale_cap import ForecastScaleCap
from sysdata.config.configdata import Config

# Create config with scaling parameters
my_config = Config()
my_config.forecast_scalars = dict(ewmac=2.65)  # From "Systematic Trading" book
my_config.use_forecast_scale_estimates = False

# Add forecast scaling stage
fcs = ForecastScaleCap()
my_system = System([fcs, my_rules], data, my_config)

# Get scaled forecast
scaled_forecast = my_system.forecastScaleCap.get_capped_forecast("SOFR", "ewmac")
print(f"Scaled forecast: {scaled_forecast.tail(3)}")
```

### Step 4: Add Position Sizing

```python
from systems.positionsizing import PositionSizing
from systems.rawdata import RawData

# Configure position sizing
my_config.percentage_vol_target = 25  # 25% annual volatility target
my_config.notional_trading_capital = 100000  # $100k capital
my_config.base_currency = "USD"

# Add required stages
raw_data = RawData()
position_size = PositionSizing()

my_system = System([fcs, my_rules, position_size, raw_data], data, my_config)

# Get position for instrument  
position = my_system.positionSize.get_subsystem_position("SOFR")
print(f"Position sizing: {position.tail(3)}")
```

### Step 5: Create a Complete System with P&L

```python
from systems.accounts.accounts_stage import Account

# Add accounting stage
accounts = Account()
my_system = System([fcs, my_rules, position_size, raw_data, accounts], 
                   data, my_config)

# Calculate P&L
profits = my_system.accounts.portfolio()
stats = profits.percent.stats()

print("System Performance:")
for stat_name, stat_value in stats[0]:
    print(f"{stat_name}: {stat_value}")
```

## Pre-Built System Example

Skip the setup with a pre-built system:

```python
from systems.provided.example.simplesystem import simplesystem

# Create complete system with sensible defaults
system = simplesystem()

# Get performance statistics
profits = system.accounts.portfolio()
print(f"Sharpe Ratio: {profits.sharpe():.3f}")
print(f"Annual Return: {profits.ann_mean():.1%}")
print(f"Annual Vol: {profits.ann_std():.1%}")

# Plot results (if matplotlib available)
try:
    profits.curve().plot()
    import matplotlib.pyplot as plt
    plt.title("System P&L Curve")
    plt.show()
except ImportError:
    print("Install matplotlib to see plots")
```

## Advanced Example: Multiple Trading Rules

```python
from systems.forecast_combine import ForecastCombine
from systems.trading_rules import TradingRule

# Define multiple EWMAC variations
ewmac_8 = TradingRule(dict(function=ewmac, other_args=dict(Lfast=8, Lslow=32)))
ewmac_32 = TradingRule(dict(function=ewmac, other_args=dict(Lfast=32, Lslow=128)))

# Create config with multiple rules
my_config = Config()
my_config.trading_rules = dict(ewmac8=ewmac_8, ewmac32=ewmac_32)
my_config.forecast_scalars = dict(ewmac8=5.3, ewmac32=2.65)
my_config.forecast_weights = dict(ewmac8=0.5, ewmac32=0.5)
my_config.forecast_div_multiplier = 1.1

# Add forecast combination
empty_rules = Rules()
combiner = ForecastCombine()

system = System([fcs, empty_rules, combiner, position_size, raw_data, accounts], 
                data, my_config)

# Get combined forecast
combined = system.combForecast.get_combined_forecast("SOFR")
print(f"Combined forecast: {combined.tail(3)}")
```

## Key Concepts Learned

### 1. **System Architecture**
- Systems are built from **stages** (Rules, ForecastScaleCap, etc.)
- **Data objects** provide price and configuration data
- **Config objects** control system behavior

### 2. **Data Flow**
```
Raw Prices → Trading Rules → Forecasts → Positions → P&L
```

### 3. **Configuration-Driven**
- System behavior controlled by config parameters
- Can be loaded from YAML files or created programmatically
- Sensible defaults provided

### 4. **Modular Design**
- Add/remove stages as needed
- Mix and match components
- Easy to test individual components

## Common Next Steps

### 1. **Explore Trading Rules**
```python
# Try different trading rules
from systems.provided.rules.breakout import breakout
from systems.provided.rules.carry import carry

# See available rules in systems/provided/rules/
```

### 2. **Use Real Data**
```python
# Set up database for real data (see Data Management guide)
from sysdata.sim.db_futures_sim_data import dbFuturesSimData
data = dbFuturesSimData()  # Uses MongoDB/Parquet
```

### 3. **Customize Configuration**
```python
# Load from YAML file
config = Config("path.to.your.config.yaml")

# Modify instruments traded
config.instruments = ["SOFR", "US10", "GOLD", "SP500"]
```

### 4. **Add Portfolio Management**
```python
from systems.portfolio import Portfolios

# Add portfolio stage for multiple instruments
portfolio = Portfolios()
system = System([..., portfolio], data, config)
```

## Troubleshooting Quick Issues

### **"No module named..." Error**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -e '.[dev]'
```

### **"No data for instrument" Error**
```python
# Check available instruments
data = csvFuturesSimData()
print(data.get_instrument_list())
```

### **Config Parameter Not Working**
```python
# Check system defaults
from sysdata.config.defaults import get_system_defaults_dict
defaults = get_system_defaults_dict()
print(defaults.keys())
```

## What's Next?

Now that you have a working system:

1. **Learn the Architecture** - Read [System Architecture](architecture.md)
2. **Understand Data Flow** - Study [Data Flow](data-flow.md)  
3. **Build Custom Strategies** - Check [Trading Strategies](trading-strategies.md)
4. **Go to Production** - See [Production Setup](production-setup.md)

## Additional Resources

- **Examples Directory** - `/examples/introduction/`
- **Provided Systems** - `/systems/provided/`
- **Configuration Examples** - `/systems/provided/example/`
- **Official Introduction** - Original docs in `/docs/introduction.md`

---

**Next:** [System Architecture](architecture.md) to understand how it all works.