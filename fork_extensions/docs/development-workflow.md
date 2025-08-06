# Development Workflow

Best practices for developing with pysystemtrade - testing, formatting, debugging, and contributing.

## Development Environment Setup

### Recommended IDE Setup

**VS Code Extensions:**
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.blackEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true
}
```

**PyCharm Configuration:**
- Set interpreter to `./venv/bin/python`
- Enable Black formatting
- Configure pytest as test runner

### Git Workflow

#### Branch Strategy
```bash
# Main development
git checkout main
git pull upstream main

# Feature development
git checkout -b feature/your-feature-name
# ... make changes ...
git commit -m "Add your feature"
git push origin feature/your-feature-name
```

#### Fork Management (For Contributors)
```bash
# Add upstream remote
git remote add upstream https://github.com/robcarver17/pysystemtrade.git

# Keep fork up to date
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

## Code Quality

### Formatting with Black

```bash
# Format all code
black .

# Check formatting without making changes
black --check .

# Format specific file
black path/to/your/file.py

# Exclude specific files/directories
black . --exclude="(migrations/|venv/)"
```

**Black Configuration** (in `pyproject.toml`):
```toml
[tool.black]
line-length = 88
target-version = ["py310"]
required-version = "23.11.0"
```

### Code Style Guidelines

#### **Naming Conventions**
```python
# Classes: PascalCase
class TradingSystem:
    pass

# Functions and variables: snake_case
def calculate_forecast(price_data):
    instrument_code = "SOFR"
    
# Constants: UPPER_SNAKE_CASE
DEFAULT_VOL_TARGET = 25
MAX_FORECAST_LEVEL = 20
```

#### **Import Organization**
```python
# Standard library imports
import os
import sys
from datetime import datetime

# Third-party imports
import pandas as pd
import numpy as np

# pysystemtrade imports
from syscore.constants import arg_not_supplied
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
from systems.basesystem import System
```

#### **Documentation**
```python
def calculate_position_size(forecast, volatility, capital):
    """
    Calculate position size based on forecast and volatility.
    
    :param forecast: Trading signal forecast
    :type forecast: pd.Series
    
    :param volatility: Price volatility estimate
    :type volatility: pd.Series
    
    :param capital: Trading capital
    :type capital: float
    
    :returns: Position size
    :rtype: pd.Series
    """
    return forecast * capital / volatility
```

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest syscore/tests/test_algos.py

# Run specific test method
python -m pytest syscore/tests/test_algos.py::Test::test_robust_vol_calc

# Run tests with coverage
python -m pytest --cov=syscore

# Run tests in parallel
python -m pytest -n auto
```

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_examples.py         # End-to-end tests
├── syscore/tests/           # Core functionality
├── systems/tests/           # System integration
└── sysdata/tests/          # Data layer tests
```

### Writing Tests

#### **Unit Test Example**
```python
import unittest
import pandas as pd
from syscore.pandas.pdutils import dataframe_pad

class TestPdUtils(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_data = pd.Series([1, 2, 3], 
                                  index=pd.date_range('2020-01-01', periods=3))
    
    def test_dataframe_pad(self):
        """Test dataframe padding functionality"""
        result = dataframe_pad(self.test_data, 5)
        self.assertEqual(len(result), 5)
        self.assertAlmostEqual(result.iloc[-1], 3.0)

if __name__ == '__main__':
    unittest.main()
```

#### **System Integration Test**
```python
import pytest
from systems.provided.example.simplesystem import simplesystem

class TestSystemIntegration:
    
    def test_simple_system_creation(self):
        """Test that simple system creates successfully"""
        system = simplesystem()
        assert system is not None
        assert len(system.get_instrument_list()) > 0
    
    def test_system_generates_positions(self):
        """Test system generates valid positions"""
        system = simplesystem()
        positions = system.portfolio.get_notional_position("SOFR")
        assert isinstance(positions, pd.Series)
        assert len(positions) > 0
```

### Test Data Management

```python
# Use temporary directories for test data
import tempfile
import os

def test_csv_data_handling():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test CSV data
        test_file = os.path.join(temp_dir, "test_data.csv")
        # ... create test data ...
        
        # Run tests
        # ... test functionality ...
```

## Debugging

### Logging Configuration

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# System-specific logging
from syslogging.logger import get_logger
log = get_logger("MyComponent")
log.debug("Debug message")
log.info("Info message")
log.warning("Warning message")
log.error("Error message")
```

### Debugging System Issues

#### **Data Problems**
```python
# Check data availability
data = csvFuturesSimData()
instruments = data.get_instrument_list()
print(f"Available: {instruments}")

# Check price data
prices = data.get_raw_price("SOFR")
print(f"Price data: {len(prices)} points")
print(f"Date range: {prices.index[0]} to {prices.index[-1]}")
```

#### **Configuration Issues**
```python
# Check system configuration
from sysdata.config.defaults import get_system_defaults_dict
defaults = get_system_defaults_dict()

# Print config values
for key, value in my_config.as_dict().items():
    print(f"{key}: {value}")
```

#### **System Stage Issues**
```python
# Debug system stages
system = simplesystem()
print(f"System stages: {system.stage_names}")

# Check specific stage
forecasts = system.rules.get_raw_forecast("SOFR", "ewmac")
print(f"Forecasts: {forecasts.describe()}")
```

### Performance Profiling

```python
# Profile system creation
import cProfile
import pstats

def create_system():
    return simplesystem()

# Run profiler
pr = cProfile.Profile()
pr.enable()
system = create_system()
pr.disable()

# Analyze results
stats = pstats.Stats(pr)
stats.sort_stats('tottime')
stats.print_stats(10)  # Top 10 time consumers
```

## Development Best Practices

### Code Organization

#### **Module Structure**
```python
# module_name.py

"""
Module docstring describing purpose and usage.
"""

# Imports at top
from typing import Optional
import pandas as pd

# Constants
DEFAULT_PARAMETER = 42

# Helper functions (private)
def _private_helper(data):
    """Private helper function."""
    pass

# Main classes and functions (public)
class PublicClass:
    """Public class with clear interface."""
    pass

def public_function(parameter: str) -> pd.DataFrame:
    """Public function with type hints."""
    pass
```

#### **Configuration Management**
```python
# Use configuration objects consistently
from sysdata.config.configdata import Config

# Load from file
config = Config("path.to.config.yaml")

# Programmatic creation with validation
config = Config()
if not hasattr(config, 'percentage_vol_target'):
    config.percentage_vol_target = 25
```

### Error Handling

```python
# Use appropriate exception types
from syscore.exceptions import missingData

def get_price_data(instrument_code):
    try:
        data = data_source.get_prices(instrument_code)
        if data.empty:
            raise missingData(f"No price data for {instrument_code}")
        return data
    except Exception as e:
        log.error(f"Error getting price data: {e}")
        raise
```

### Memory Management

```python
# Use context managers for resources
from contextlib import contextmanager

@contextmanager
def temporary_system():
    system = create_system()
    try:
        yield system
    finally:
        system.cache.delete_all()  # Clean up

# Usage
with temporary_system() as system:
    results = system.accounts.portfolio()
```

## Contributing Guidelines

### Code Review Process

1. **Self-Review Checklist:**
   - [ ] Code follows style guidelines
   - [ ] All tests pass
   - [ ] Documentation updated
   - [ ] No hardcoded values
   - [ ] Error handling included

2. **Pull Request Format:**
```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature  
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests pass locally

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
```

### Fork-Specific Development

**For this fork**, follow additional guidelines:

```python
# All new code goes in fork_extensions/
from fork_extensions.my_module import MyClass

# Import main pysystemtrade functionality
from systems.basesystem import System
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData

# Combine in your extensions
class ExtendedSystem(System):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add fork-specific functionality
```

### Documentation Standards

```python
def complex_calculation(data: pd.DataFrame, 
                       parameter: float = 1.0,
                       method: str = "default") -> pd.Series:
    """
    Perform complex calculation on time series data.
    
    This function implements the methodology described in 
    "Advanced Trading Systems" chapter 5.
    
    :param data: Input time series data with datetime index
    :type data: pd.DataFrame
    
    :param parameter: Calculation parameter (default: 1.0)
    :type parameter: float
    
    :param method: Calculation method ("default", "robust", "fast")  
    :type method: str
    
    :returns: Calculated values
    :rtype: pd.Series
    
    :raises ValueError: If data is empty or parameter is negative
    
    Example:
        >>> data = pd.DataFrame({'price': [100, 101, 99]})
        >>> result = complex_calculation(data, parameter=0.5)
        >>> print(result.head())
    """
    if data.empty:
        raise ValueError("Data cannot be empty")
        
    # Implementation here
    return result
```

## Continuous Integration

### Local Pre-commit Checks
```bash
# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "Running pre-commit checks..."

# Format code
black --check . || exit 1

# Run tests
python -m pytest || exit 1

echo "All checks passed!"
EOF

chmod +x .git/hooks/pre-commit
```

### Automated Testing
```yaml
# .github/workflows/test.yml (example)
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.10
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e '.[dev]'
    - name: Run tests
      run: python -m pytest
```

---

**Next:** [Configuration Guide](configuration.md) for system configuration details.