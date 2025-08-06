# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Installation and Setup
- Install in editable mode with dev dependencies: `python -m pip install --editable '.[dev]'`
- Regular installation: `python -m pip install .`
- Requires Python 3.10 or later

### Testing
- Run all tests: `python -m pytest` (takes ~45 seconds, 61 passed + 10 skipped)
- Run specific test module: `python -m pytest syscore/tests/` 
- Run tests with coverage using tox: `tox`
- Test configuration is defined in pyproject.toml under `[tool.pytest.ini_options]`
- Tests are located in multiple directories (syscore/tests, sysdata/tests, systems/tests, etc.)
- Tests include doctests from various modules
- Some tests may be skipped if optional dependencies (like Arctic) are not installed

### Code Formatting
- Use Black for code formatting: `black .`
- Black configuration: line-length 88, target Python 3.10+
- Black version pinned to 23.11.0

## Architecture Overview

### Core System Design
- **Systems-based architecture**: The framework is built around `System` objects that process data through stages
- **Stage-based processing**: Each system consists of stages (rawdata → forecasting → portfolio → accounts)
- **Data abstraction layer**: Clean separation between data sources (CSV, MongoDB, Parquet, Arctic) and business logic

### Key Components

#### Data Layer (`sysdata/`)
- **Data sources**: Supports CSV, MongoDB, Arctic (time series), and Parquet backends
- **Data blob pattern**: `dataBlob` class provides unified interface to different data backends
- **Configuration management**: Centralized config system with defaults and production overrides

#### Broker Integration (`sysbrokers/`)
- **Interactive Brokers integration**: Primary broker via ib-insync library
- **Abstracted broker interface**: Generic broker classes that can be extended for other brokers
- **Real-time data handling**: Price feeds, order management, position tracking

#### Systems Framework (`systems/`)
- **Modular stages**: Each stage (forecasting, portfolio, etc.) is independent and testable
- **Configuration-driven**: Systems configured via YAML files
- **Backtesting support**: Full backtesting framework with realistic cost modeling

#### Production Framework (`sysproduction/`)
- **Live trading system**: Production-ready automated trading
- **Process management**: Handles multiple concurrent processes
- **Monitoring and reporting**: Comprehensive reporting and alerting system
- **Risk management**: Position limits, capital management, override controls

### Data Flow
1. **Raw data** → Price data from brokers/CSV files  
2. **Systems processing** → Trading signals and positions via stage-based pipeline
3. **Production execution** → Order generation, execution, and monitoring
4. **Storage** → Results stored in chosen backend (MongoDB, Arctic, etc.)

### Trading Strategy Types
- **Classic buffered positions**: Traditional systematic trading approach
- **Dynamic optimized positions**: Portfolio optimization with constraints
- **Custom strategies**: Framework for implementing bespoke trading strategies

## Important File Locations
- Main configuration: `sysdata/config/defaults.yaml`
- Example systems: `systems/provided/`
- Production scripts: `sysproduction/run_*.py`
- Interactive tools: `sysproduction/interactive_*.py`
- Trading rules: `systems/provided/rules/`

## Development Notes
- This is a production trading system used by the author daily
- Heavy emphasis on robustness, monitoring, and risk management
- Extensive logging and error handling throughout
- Configuration-driven design allows easy system modifications
- Multiple data backend support enables flexible deployment options

## Fork-Specific Instructions
**IMPORTANT**: This is a fork of the original pysystemtrade repository. Since we frequently merge changes from the upstream repository:

- **DO NOT modify existing directories or files** in the main codebase
- **CREATE ALL NEW FILES** in the `/fork_extensions/` directory at the project root
- This prevents merge conflicts and keeps fork-specific additions separate
- Use imports to reference the main codebase from fork_extensions when needed
- Document any new functionality in `/fork_extensions/README.md`