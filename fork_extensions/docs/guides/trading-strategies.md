# Trading Strategies

Comprehensive guide to trading strategies in pysystemtrade - built-in rules, custom strategies, and strategy development.

## Overview

pysystemtrade implements systematic trading strategies through **trading rules** that generate **forecasts** from market data. These forecasts are then combined, scaled, and used to determine position sizes.

## Strategy Architecture

### Core Concepts

**Trading Rule** → **Forecast** → **Scaled Forecast** → **Position** → **P&L**

```python
# Basic trading rule structure
def my_trading_rule(price, fast_period, slow_period):
    """
    Generate trading forecast from price data.
    
    :param price: Price time series
    :param fast_period: Fast moving average period  
    :param slow_period: Slow moving average period
    :returns: Forecast series (-20 to +20 scale)
    """
    fast_ma = price.rolling(fast_period).mean()
    slow_ma = price.rolling(slow_period).mean()
    raw_signal = fast_ma - slow_ma
    
    # Scale to forecast range
    return raw_signal / price.rolling(64).std()
```

## Built-in Trading Rules

### 1. EWMAC (Exponentially Weighted Moving Average Crossover)

**Description:** Trend-following rule using exponentially weighted moving averages.

```python
from systems.provided.rules.ewmac import ewmac_forecast_with_defaults

# Basic EWMAC with default parameters (32, 128)
forecast = ewmac_forecast_with_defaults(price)

# Custom EWMAC parameters  
from systems.provided.rules.ewmac import ewmac
forecast = ewmac(price, Lfast=16, Lslow=64)
```

**Parameters:**
- `Lfast`: Fast average span (default: 32)
- `Lslow`: Slow average span (default: 128, or 4 × Lfast)

**Use Cases:**
- Trend following
- Medium-term momentum
- Works well in trending markets

### 2. Breakout Rules

**Description:** Trade breakouts from recent price ranges.

```python
from systems.provided.rules.breakout import breakout

# Breakout rule
forecast = breakout(price, lookback=40)
```

**Parameters:**
- `lookback`: Period for calculating breakout levels

**Variations:**
- `breakout`: Simple breakout
- `normalized_breakout`: Volatility-adjusted breakout

### 3. Carry Rules

**Description:** Trade based on futures curve slope (contango/backwardation).

```python
from systems.provided.rules.carry import carry

# Requires carry data (price differential between contracts)
forecast = carry(price, carry_data, smooth_days=90)
```

**Parameters:**
- `smooth_days`: Smoothing period for carry signal

**Use Cases:**
- Calendar spread trading
- Term structure exploitation
- Mean-reverting strategies

### 4. Mean Reversion Rules

**Description:** Trade reversals from price extremes.

```python
from systems.provided.rules.mr_wings import mrwings

# Mean reversion with wings
forecast = mrwings(price, 
                   lookback=20,    # Period for mean calculation
                   threshold=2.0)  # Standard deviation threshold
```

### 5. Momentum/Acceleration Rules

**Description:** Trade based on price acceleration patterns.

```python
from systems.provided.rules.accel import accel

# Price acceleration rule
forecast = accel(price, 
                 fast_period=16,
                 slow_period=64)
```

## Strategy Configuration

### Single Rule System

```python
from systems.basesystem import System
from systems.forecasting import Rules
from systems.provided.rules.ewmac import ewmac_forecast_with_defaults

# Create single rule system
data = csvFuturesSimData()
rules = Rules(dict(ewmac=ewmac_forecast_with_defaults))
system = System([rules], data)

# Get forecast
forecast = system.rules.get_raw_forecast("SOFR", "ewmac")
```

### Multi-Rule System

```python
from systems.trading_rules import TradingRule
from systems.forecast_combine import ForecastCombine
from sysdata.config.configdata import Config

# Define multiple rules
ewmac_fast = TradingRule(dict(
    function=ewmac,
    other_args=dict(Lfast=16, Lslow=64)
))

ewmac_slow = TradingRule(dict(
    function=ewmac, 
    other_args=dict(Lfast=64, Lslow=256)
))

breakout_rule = TradingRule(dict(
    function=breakout,
    other_args=dict(lookback=40)
))

# Configuration
config = Config()
config.trading_rules = dict(
    ewmac_fast=ewmac_fast,
    ewmac_slow=ewmac_slow, 
    breakout=breakout_rule
)

# Forecast scaling (from "Systematic Trading" book)
config.forecast_scalars = dict(
    ewmac_fast=4.0,
    ewmac_slow=2.0,
    breakout=10.0
)

# Forecast weights and diversification
config.forecast_weights = dict(
    ewmac_fast=0.4,
    ewmac_slow=0.4,
    breakout=0.2
)
config.forecast_div_multiplier = 1.2

# Create system with forecast combination
empty_rules = Rules()
combiner = ForecastCombine()
system = System([empty_rules, combiner, ...], data, config)
```

## Custom Trading Rules

### Simple Custom Rule

```python
import pandas as pd
from syscore.pandas.pdutils import rolling_avg

def rsi_rule(price, period=14, overbought=70, oversold=30):
    """
    RSI-based trading rule.
    
    :param price: Price series
    :param period: RSI calculation period
    :param overbought: Overbought threshold
    :param oversold: Oversold threshold
    :returns: Forecast series
    """
    # Calculate price changes
    delta = price.diff()
    
    # Separate gains and losses
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    
    # Calculate average gains and losses
    avg_gains = gains.rolling(period).mean()
    avg_losses = losses.rolling(period).mean()
    
    # Calculate RSI
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))
    
    # Generate signals
    forecast = pd.Series(0, index=price.index)
    forecast[rsi < oversold] = 10   # Buy signal
    forecast[rsi > overbought] = -10  # Sell signal
    
    return forecast

# Use in system
rsi_trading_rule = TradingRule(dict(
    function=rsi_rule,
    other_args=dict(period=14, overbought=75, oversold=25)
))
```

### Advanced Custom Rule

```python
def bollinger_mean_reversion(price, period=20, std_mult=2.0):
    """
    Bollinger Band mean reversion strategy.
    
    Trades against price moves beyond Bollinger Bands,
    expecting reversion to the mean.
    """
    # Calculate Bollinger Bands
    sma = price.rolling(period).mean()
    std = price.rolling(period).std()
    
    upper_band = sma + (std * std_mult)
    lower_band = sma - (std * std_mult)
    
    # Calculate band position (0 = lower band, 1 = upper band)
    band_position = (price - lower_band) / (upper_band - lower_band)
    
    # Generate mean reversion signals
    # Strong sell when price > upper band
    # Strong buy when price < lower band
    forecast = (0.5 - band_position) * 40  # Scale to ±20 range
    
    # Smooth the signal
    forecast = forecast.rolling(3).mean()
    
    return forecast.fillna(0)

# Advanced rule with multiple data inputs
def spread_trading_rule(price, volume, lookback=40):
    """
    Rule combining price and volume information.
    """
    # Price momentum
    price_mom = price / price.rolling(lookback).mean() - 1
    
    # Volume momentum  
    vol_mom = volume / volume.rolling(lookback).mean() - 1
    
    # Combined signal (price momentum confirmed by volume)
    forecast = price_mom * 20  # Base signal from price
    
    # Enhance signal when volume confirms
    volume_confirmation = vol_mom > 0
    forecast = forecast.where(volume_confirmation, forecast * 0.5)
    
    return forecast.fillna(0)
```

### Rule Testing and Validation

```python
def test_trading_rule(rule_function, price_data, **rule_args):
    """
    Test trading rule performance.
    """
    from systems.accounts.account_forecast import pandl_for_instrument_forecast
    
    # Generate forecast
    forecast = rule_function(price_data, **rule_args)
    
    # Calculate P&L
    account = pandl_for_instrument_forecast(forecast, price_data)
    
    # Performance statistics
    stats = account.percent.stats()
    print(f"Sharpe Ratio: {account.sharpe():.3f}")
    print(f"Annual Return: {account.ann_mean():.1%}")
    print(f"Max Drawdown: {stats[0][10][1]}")
    
    return account

# Test custom rule
price = data.get_raw_price("SOFR")
account = test_trading_rule(rsi_rule, price, period=14)
```

## Strategy Types

### 1. Trend Following Strategies

**Characteristics:**
- Follow price momentum
- Perform well in trending markets
- May struggle in choppy markets

**Examples:**
```python
# Multiple timeframe EWMAC
config.trading_rules = dict(
    ewmac_8_32=TradingRule(dict(function=ewmac, other_args=dict(Lfast=8, Lslow=32))),
    ewmac_16_64=TradingRule(dict(function=ewmac, other_args=dict(Lfast=16, Lslow=64))),
    ewmac_32_128=TradingRule(dict(function=ewmac, other_args=dict(Lfast=32, Lslow=128))),
    ewmac_64_256=TradingRule(dict(function=ewmac, other_args=dict(Lfast=64, Lslow=256)))
)
```

### 2. Mean Reversion Strategies

**Characteristics:**
- Trade against recent price moves
- Perform well in range-bound markets
- Risk of loss in trending markets

**Examples:**
```python
# Mean reversion combination
config.trading_rules = dict(
    bollinger_mr=TradingRule(dict(function=bollinger_mean_reversion)),
    rsi_mr=TradingRule(dict(function=rsi_rule)),
    mrwings=TradingRule(dict(function=mrwings))
)
```

### 3. Carry Strategies

**Characteristics:**
- Based on futures curve shape
- Term structure exploitation
- Calendar spread trading

**Examples:**
```python
# Carry strategy (requires carry data)
config.trading_rules = dict(
    carry=TradingRule(dict(
        function=carry,
        data=["rawdata.get_instrument_raw_carry_data"],
        other_args=dict(smooth_days=90)
    ))
)
```

### 4. Hybrid Strategies

**Characteristics:**
- Combine multiple approaches
- Diversified signal sources
- More robust performance

```python
# Balanced hybrid approach
config.trading_rules = dict(
    # Trend following
    ewmac_32=TradingRule(dict(function=ewmac, other_args=dict(Lfast=32, Lslow=128))),
    breakout=TradingRule(dict(function=breakout, other_args=dict(lookback=40))),
    
    # Mean reversion
    mrwings=TradingRule(dict(function=mrwings, other_args=dict(lookback=20))),
    
    # Carry (if available)
    carry=TradingRule(dict(
        function=carry,
        data=["rawdata.get_instrument_raw_carry_data"],
        other_args=dict(smooth_days=90)
    ))
)

# Balanced weights
config.forecast_weights = dict(
    ewmac_32=0.3,
    breakout=0.3,
    mrwings=0.3,
    carry=0.1  # Lower weight for carry
)
```

## Portfolio Construction

### Instrument Selection

```python
# Define universe of instruments
config.instruments = [
    # Equity indices
    "SP500", "NASDAQ", "EUROSTX", "FTSE100",
    
    # Fixed income  
    "US10", "BUND", "JGB",
    
    # FX
    "GBP", "EUR", "JPY",
    
    # Commodities
    "CRUDE_W", "GOLD", "COPPER", "CORN"
]
```

### Position Sizing

```python
# Volatility targeting
config.percentage_vol_target = 20  # 20% annual volatility

# Capital allocation
config.notional_trading_capital = 1000000  # $1M

# Instrument diversification
config.instrument_div_multiplier = 1.5  # Boost for diversification

# Position limits (optional)
config.max_instrument_weight = 0.1  # Max 10% in any instrument
```

## Strategy Optimization

### Forecast Scaling Estimation

```python
# Estimate forecast scalars
config.use_forecast_scale_estimates = True
config.forecast_scalar_estimate = dict(
    pool_instruments=True,  # Pool across instruments
    date_method="expanding",  # Use expanding window
    rollyears=20  # 20 years of data
)
```

### Weight Estimation

```python
# Estimate forecast weights
config.use_forecast_weight_estimates = True
config.forecast_weight_estimate = dict(
    method="shrinkage",     # Shrinkage estimator
    date_method="expanding", 
    rollyears=5
)

# Estimate instrument weights  
config.use_instrument_weight_estimates = True
config.instrument_weight_estimate = dict(
    method="shrinkage",
    date_method="expanding",
    rollyears=3
)
```

## Performance Analysis

### System Diagnostics

```python
# Get system performance
profits = system.accounts.portfolio()

# Overall statistics
print(f"Sharpe Ratio: {profits.sharpe():.3f}")
print(f"Annual Return: {profits.ann_mean():.1%}")
print(f"Volatility: {profits.ann_std():.1%}")

# By instrument
for instrument in system.get_instrument_list():
    instr_profits = system.accounts.pandl_for_instrument(instrument)
    print(f"{instrument}: Sharpe = {instr_profits.sharpe():.3f}")

# By trading rule
for rule_name in system.rules.trading_rules():
    rule_profits = system.accounts.pandl_for_trading_rule(rule_name)
    print(f"{rule_name}: Sharpe = {rule_profits.sharpe():.3f}")
```

### Risk Analysis

```python
# Drawdown analysis
drawdowns = profits.percent.drawdown()
max_dd = drawdowns.min()
print(f"Maximum Drawdown: {max_dd:.1%}")

# Position analysis
for instrument in system.get_instrument_list():
    positions = system.portfolio.get_notional_position(instrument)
    max_pos = positions.abs().max()
    print(f"{instrument}: Max position = {max_pos:.1f}")

# Correlation analysis
returns_by_instrument = {}
for instrument in system.get_instrument_list():
    instr_profits = system.accounts.pandl_for_instrument(instrument)
    returns_by_instrument[instrument] = instr_profits.percent
    
correlation_matrix = pd.DataFrame(returns_by_instrument).corr()
print("Instrument Correlations:")
print(correlation_matrix)
```

## Advanced Topics

### Dynamic Position Sizing

```python
from systems.provided.dynamic_small_system_optimise.optimised_positions_stage import optimisedPositions

# Dynamic optimization system
config.use_instrument_weight_estimates = True
config.instrument_weight_estimate = dict(
    method="equal_weights",  # Start with equal weights
    date_method="expanding"
)

# Add optimization stage
optimizer = optimisedPositions()
system = System([..., optimizer], data, config)
```

### Risk Overlay

```python
from systems.risk_overlay import RiskOverlay

# Add risk overlay
config.max_instrument_weight = 0.15
config.max_cluster_weight = 0.3  # Max weight per asset class
config.risk_overlay = True

risk_overlay = RiskOverlay()
system = System([..., risk_overlay], data, config)
```

---

**Next:** [Production Setup](production-setup.md) for live trading deployment.