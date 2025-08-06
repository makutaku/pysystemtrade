# API Reference

Quick reference for key pysystemtrade classes, methods, and interfaces.

## Core System Classes

### System (`systems.basesystem.System`)

Central orchestrator for all system components.

```python
from systems.basesystem import System

system = System(stage_list, data, config=None, log=None)
```

**Key Methods:**
```python
# Get instrument list
instruments = system.get_instrument_list()

# Access stages by name
forecasts = system.rules.get_raw_forecast(instrument_code, rule_name)
positions = system.portfolio.get_notional_position(instrument_code)
profits = system.accounts.portfolio()

# Cache management
system.cache.pickle("filename.pkl")
system.cache.unpickle("filename.pkl")
```

### Config (`sysdata.config.configdata.Config`)

Configuration object for system parameters.

```python
from sysdata.config.configdata import Config

# Load from YAML
config = Config("path.to.config.yaml")

# Create programmatically
config = Config(dict(
    percentage_vol_target=25,
    instruments=["SOFR", "SP500"]
))

# Access/modify parameters
config.percentage_vol_target = 20
config.trading_rules = {...}
```

## Data Classes

### simData (`sysdata.sim.sim_data.simData`)

Base class for simulation data interfaces.

```python
# CSV data
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
data = csvFuturesSimData()

# Database data  
from sysdata.sim.db_futures_sim_data import dbFuturesSimData
data = dbFuturesSimData()
```

**Key Methods:**
```python
# Instruments and data
instruments = data.get_instrument_list()
prices = data.daily_prices(instrument_code)
fx_rates = data.get_fx_for_instrument(instrument_code, base_currency)

# Instrument metadata
meta = data.get_instrument_object_with_meta_data(instrument_code)
raw_carry = data.get_instrument_raw_carry_data(instrument_code)

# System integration
system = System([...], data)
```

### dataBlob (`sysdata.data_blob.dataBlob`)

Central data access point abstracting multiple data sources.

```python
from sysdata.data_blob import dataBlob

data = dataBlob(
    class_list=[...],           # Data storage classes
    log_name="",               # Logger name
    csv_data_paths={},         # Custom CSV paths
    mongo_db=None,             # MongoDB connection
    ib_conn=None,              # IB connection  
    keep_original_prefix=False  # Preserve class names
)
```

**Dynamic Attributes:**
```python
# Access data storage objects (dynamically created)
adjusted_prices = data.db_futures_adjusted_prices
contract_data = data.db_futures_contract_data  
fx_prices = data.db_fx_prices

# Broker interfaces
broker_data = data.broker_futures_contract_price_data
```

## System Stages

### Rules (`systems.forecasting.Rules`)

Trading rules stage for generating forecasts.

```python
from systems.forecasting import Rules
from systems.trading_rules import TradingRule

# Simple rule definition
rules = Rules(dict(ewmac=ewmac_function))

# Advanced rule definition
rule = TradingRule(dict(
    function=my_function,
    data=["rawdata.daily_prices"],  # Data inputs
    other_args=dict(param1=value1)  # Parameters
))
rules = Rules(dict(my_rule=rule))
```

**Key Methods:**
```python
# Get forecasts
raw_forecast = rules.get_raw_forecast(instrument_code, rule_name)
all_rules = rules.trading_rules()
```

### ForecastScaleCap (`systems.forecast_scale_cap.ForecastScaleCap`)

Forecast scaling and capping stage.

```python
from systems.forecast_scale_cap import ForecastScaleCap

fcs = ForecastScaleCap()
```

**Key Methods:**
```python
# Get scaling and capping
scalar = fcs.get_forecast_scalar(instrument_code, rule_name)
capped = fcs.get_capped_forecast(instrument_code, rule_name)
```

**Configuration:**
```python
# Fixed scalars
config.forecast_scalars = dict(ewmac=2.65, breakout=10.0)
config.use_forecast_scale_estimates = False

# Estimated scalars
config.use_forecast_scale_estimates = True
```

### ForecastCombine (`systems.forecast_combine.ForecastCombine`)

Combines multiple forecasts with weights and diversification.

```python
from systems.forecast_combine import ForecastCombine

combiner = ForecastCombine()
```

**Key Methods:**
```python
# Get combined forecasts
weights = combiner.get_forecast_weights(instrument_code)
div_mult = combiner.get_forecast_diversification_multiplier(instrument_code)
combined = combiner.get_combined_forecast(instrument_code)
```

**Configuration:**
```python
# Fixed weights
config.forecast_weights = dict(ewmac=0.6, breakout=0.4)
config.forecast_div_multiplier = 1.1

# Estimated weights
config.use_forecast_weight_estimates = True
config.use_forecast_div_mult_estimates = True
```

### PositionSizing (`systems.positionsizing.PositionSizing`)

Volatility-targeted position sizing.

```python
from systems.positionsizing import PositionSizing

pos_sizing = PositionSizing()
```

**Key Methods:**
```python
# Position sizing components
vol_scalar = pos_sizing.get_volatility_scalar(instrument_code)
cash_vol = pos_sizing.get_instrument_currency_vol(instrument_code)
position = pos_sizing.get_subsystem_position(instrument_code)
```

**Configuration:**
```python
config.percentage_vol_target = 25  # 25% annual vol target
config.notional_trading_capital = 1000000  # $1M capital
config.base_currency = "USD"
```

### Portfolios (`systems.portfolio.Portfolios`)

Portfolio construction across multiple instruments.

```python
from systems.portfolio import Portfolios

portfolio = Portfolios()
```

**Key Methods:**
```python
# Portfolio positions
weights = portfolio.get_instrument_weights()
div_mult = portfolio.get_instrument_diversification_multiplier()  
position = portfolio.get_notional_position(instrument_code)
```

**Configuration:**
```python
# Fixed weights
config.instrument_weights = dict(SP500=0.4, SOFR=0.3, GOLD=0.3)
config.instrument_div_multiplier = 1.5

# Estimated weights
config.use_instrument_weight_estimates = True
```

### Accounts (`systems.accounts.accounts_stage.Account`)

P&L calculation and performance tracking.

```python
from systems.accounts.accounts_stage import Account

accounts = Account()
```

**Key Methods:**
```python
# P&L calculation
portfolio_pandl = accounts.portfolio()
instrument_pandl = accounts.pandl_for_instrument(instrument_code)
rule_pandl = accounts.pandl_for_trading_rule(rule_name)

# Performance statistics  
stats = portfolio_pandl.stats()
sharpe = portfolio_pandl.sharpe()
annual_return = portfolio_pandl.ann_mean()
```

## Data Objects

### Futures Contracts (`sysobjects.contracts.futuresContract`)

Individual futures contract representation.

```python
from sysobjects.contracts import futuresContract

contract = futuresContract(instrument_code, contract_date)
contract = futuresContract("SOFR", "202403")
```

### Adjusted Prices (`sysobjects.adjusted_prices.futuresAdjustedPrices`)

Back-adjusted continuous price series.

```python
from sysobjects.adjusted_prices import futuresAdjustedPrices

# Create from multiple prices
adjusted = futuresAdjustedPrices.stitch_multiple_prices(
    multiple_prices, 
    forward_fill=True
)
```

### Multiple Prices (`sysobjects.multiple_prices.futuresMultiplePrices`)

Price series with contract information.

```python
from sysobjects.multiple_prices import futuresMultiplePrices

# Contains: PRICE, CARRY, FORWARD columns
# Plus: PRICE_CONTRACT, CARRY_CONTRACT, FORWARD_CONTRACT
```

## Trading Rules

### Built-in Rules

```python
# EWMAC (Exponentially Weighted Moving Average Crossover)
from systems.provided.rules.ewmac import ewmac, ewmac_forecast_with_defaults

forecast = ewmac(price, Lfast=32, Lslow=128)
forecast = ewmac_forecast_with_defaults(price)  # Uses defaults

# Breakout
from systems.provided.rules.breakout import breakout
forecast = breakout(price, lookback=40)

# Carry
from systems.provided.rules.carry import carry
forecast = carry(price, carry_data, smooth_days=90)

# Mean Reversion
from systems.provided.rules.mr_wings import mrwings
forecast = mrwings(price, lookback=20)
```

### Custom Rule Template

```python
def custom_rule(price, param1=10, param2=0.5):
    """
    Custom trading rule template.
    
    :param price: Price series
    :param param1: First parameter
    :param param2: Second parameter
    :returns: Forecast series (-20 to +20 range)
    """
    # Your trading logic here
    signal = price.rolling(param1).mean()
    
    # Scale to appropriate range
    volatility = price.diff().rolling(64).std()
    forecast = signal / volatility * param2
    
    # Cap at ±20
    return forecast.clip(-20, 20)

# Use in system
from systems.trading_rules import TradingRule

rule = TradingRule(dict(
    function=custom_rule,
    other_args=dict(param1=20, param2=1.0)
))
```

## Production Classes

### Production Data Interfaces

```python
# Diagnostic (read-only) interfaces
from sysproduction.data.prices import diagPrices
from sysproduction.data.positions import diagPositions
from sysproduction.data.orders import dataOrders

diag_prices = diagPrices()
prices = diag_prices.get_adjusted_prices("SOFR")

# Update (write) interfaces  
from sysproduction.data.prices import updatePrices
update_prices = updatePrices()
update_prices.add_adjusted_prices("SOFR", new_prices)
```

### Order Management

```python
from sysexecution.orders.instrument_orders import instrumentOrder
from sysexecution.orders.contract_orders import contractOrder

# Create orders
instr_order = instrumentOrder(
    instrument_code="SOFR",
    trade_qty=10,
    order_type="market"
)

contract_order = contractOrder(
    contract=futuresContract("SOFR", "202403"),
    trade_qty=10,
    order_type="limit",
    limit_price=98.50
)
```

## Utilities

### Core Utilities (`syscore`)

```python
# Date utilities
from syscore.dateutils import month_from_contract_letter

# Pandas utilities
from syscore.pandas.pdutils import dataframe_pad, from_scalar_values_to_ts

# Math utilities  
from syscore.maths import sign, Ewm

# Constants
from syscore.constants import arg_not_supplied, missing_data
```

### Performance Analysis (`sysobjects.accounts`)

```python
# Account curve analysis
profits = system.accounts.portfolio()

# Statistics
stats = profits.stats()  # Comprehensive statistics
sharpe = profits.sharpe()
annual_return = profits.ann_mean()
annual_vol = profits.ann_std()

# Drawdown analysis
drawdown = profits.drawdown()
max_drawdown = drawdown.min()

# Time-based returns
daily = profits.daily
weekly = profits.weekly  
monthly = profits.monthly
annual = profits.annual

# Plotting
profits.curve().plot()  # Cumulative P&L
drawdown.plot()        # Drawdown chart
```

## Configuration Reference

### System Parameters

```python
config = Config()

# Capital and risk
config.notional_trading_capital = 1000000
config.percentage_vol_target = 25
config.base_currency = "USD"

# Instruments
config.instruments = ["SOFR", "SP500", "GOLD"]

# Trading rules
config.trading_rules = {
    "ewmac": TradingRule(...)
}

# Forecast scaling
config.forecast_scalars = {"ewmac": 2.65}
config.forecast_cap = 20.0

# Forecast combination
config.forecast_weights = {"ewmac": 1.0}
config.forecast_div_multiplier = 1.0

# Portfolio construction  
config.instrument_weights = {"SOFR": 0.5, "SP500": 0.5}
config.instrument_div_multiplier = 1.5

# Position limits
config.max_instrument_weight = 0.2
config.max_portfolio_leverage = 2.0
```

### Database Configuration

```python
# MongoDB
config.mongo_host = "localhost"
config.mongo_db = "production"  
config.mongo_port = 27017

# Parquet
config.parquet_store_path = "/path/to/parquet/data"

# CSV paths
config.csv_data_paths = {
    "csvFuturesAdjustedPricesData": "/custom/path/adjusted/",
    "csvFuturesMultiplePricesData": "/custom/path/multiple/"
}
```

## Common Patterns

### System Creation Pattern

```python
# 1. Import components
from systems.basesystem import System
from systems.forecasting import Rules
from systems.forecast_scale_cap import ForecastScaleCap
# ... other imports

# 2. Create data
data = csvFuturesSimData()

# 3. Create config
config = Config()
config.instruments = ["SOFR", "SP500"]
# ... set parameters

# 4. Create stages
rules = Rules()
fcs = ForecastScaleCap()
# ... other stages

# 5. Create system
system = System([rules, fcs, ...], data, config)
```

### Error Handling Pattern

```python
from syscore.exceptions import missingData

try:
    prices = data.get_raw_price(instrument_code)
    if prices.empty:
        raise missingData(f"No data for {instrument_code}")
except missingData as e:
    log.warning(f"Data issue: {e}")
    # Handle gracefully
```

---

**Next:** [Configuration Guide](configuration.md) for detailed configuration options.