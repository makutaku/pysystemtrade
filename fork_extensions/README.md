# Fork Extensions

This directory contains all fork-specific additions and modifications to the pysystemtrade codebase.

## Purpose

Since this is a fork that regularly merges changes from the upstream repository, all new functionality is isolated here to prevent merge conflicts.

## Structure

- Put new Python modules and packages in this directory
- Use relative imports to reference the main pysystemtrade codebase
- Document any new functionality in this README

## Usage

To use fork extensions in your code:

```python
# Import main pysystemtrade functionality
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
from systems.provided.futures_chapter15.basesystem import futures_system

# Import fork extensions
from fork_extensions.your_module import YourClass
```

## Guidelines

1. **Never modify files outside this directory**
2. **Keep all fork-specific code isolated here**
3. **Document any dependencies on main codebase**
4. **Test that your extensions work with upstream merges**