# Installation Guide

Complete guide to setting up pysystemtrade for development and production use. This system is designed for enterprise-grade systematic futures trading with 24/7 operation capability.

## Prerequisites

### System Requirements
- **Python 3.10 or later** (required)
- **Operating System** - Linux (Ubuntu/RHEL recommended), macOS, or Windows
- **Memory** - Minimum 8GB RAM (32GB+ recommended for production with multiple strategies)
- **Storage** - 50GB+ free space (SSD recommended) for:
  - Time series data (Parquet/Arctic): 20-30GB
  - MongoDB operational data: 5-10GB  
  - Logs and backups: 10-15GB
  - System files: 5GB
- **Network** - Stable internet connection for real-time market data
- **Server** - Dedicated VPS/server recommended for production (99.9% uptime SLA)

### Required Knowledge
- **Python programming** - Intermediate to advanced level
- **Financial markets** - Futures trading, systematic strategies, risk management
- **System administration** - Linux command line, process management, cron jobs
- **Database management** - MongoDB operations, backup/restore procedures
- **DevOps basics** - Git, monitoring, logging, deployment automation
- **Quantitative finance** - Understanding of volatility, correlations, portfolio optimization

## Quick Installation

### 1. Clone the Repository

```bash
# Clone the main repository
git clone https://github.com/robcarver17/pysystemtrade.git
cd pysystemtrade

# Or clone your fork
git clone https://github.com/yourusername/pysystemtrade.git
cd pysystemtrade
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install in editable mode with development dependencies
python -m pip install --editable '.[dev]'

# Or regular installation
python -m pip install .
```

### 4. Verify Installation

```bash
# Run tests to verify installation
python -m pytest

# Check code formatting
black --check .
```

## Detailed Setup

### Python Environment Setup

#### Option 1: Using pyenv (Recommended)

```bash
# Install Python 3.10 using pyenv
pyenv install 3.10
pyenv local 3.10

# Create virtual environment
python -m venv venv
source venv/bin/activate
```

#### Option 2: Using conda

```bash
# Create conda environment
conda create -n pysystemtrade python=3.10
conda activate pysystemtrade

# Install pip in conda environment
conda install pip
```

### Development Dependencies

The `'.[dev]'` installation includes:
- **pytest** - Testing framework
- **black** - Code formatting (version 23.11.0)
- All production dependencies

### Core Dependencies

Key production dependencies include:
- **pandas 2.1.3** - Data manipulation and time series analysis
- **numpy ≥1.24.0** - High-performance numerical computing  
- **matplotlib ≥3.0.0** - Chart generation for reports
- **PyYAML 6.0.1** - Configuration management with environment variable support
- **scipy ≥1.0.0** - Advanced statistical functions and optimization
- **ib-insync 0.9.86** - Interactive Brokers API integration
- **pymongo 3.11.3** - MongoDB interface for operational data
- **pyarrow ≥16,<20** - High-performance Parquet time series storage
- **statsmodels 0.14.0** - Econometric analysis and forecasting

### Optional Production Dependencies
- **Arctic** - High-performance time series database (MongoDB-based)
- **psutil** - System monitoring and process management
- **smtplib** - Email notification system
- **crontab** - Process scheduling (Linux/macOS)
- **supervisord** - Advanced process control

## Database Setup

### Data Storage Architecture

pysystemtrade uses a sophisticated multi-tier data storage system:

1. **MongoDB** - Operational data (orders, positions, process control)
2. **Parquet** - High-performance time series storage 
3. **Arctic** (Optional) - Legacy time series database with MongoDB backend
4. **CSV** - Configuration data and backtesting datasets

### MongoDB (Production Required)

#### Install MongoDB

**Ubuntu/Debian:**
```bash
# Import MongoDB public GPG key
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Install MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org
```

**macOS:**
```bash
# Using Homebrew
brew tap mongodb/brew
brew install mongodb-community
```

#### Start MongoDB

```bash
# Linux
sudo systemctl start mongod

# macOS
brew services start mongodb/brew/mongodb-community

# Manual start with custom data directory
mongod --dbpath ~/data/mongodb/
```

#### Configure MongoDB

Create configuration file `/private/private_config.yaml`:

```yaml
# MongoDB settings
mongo_host: localhost
mongo_db: production  # Use separate DBs for prod/test
mongo_port: 27017

# Connection pooling for production
mongo_connect_timeout_ms: 10000
mongo_server_selection_timeout_ms: 5000

# Security (if authentication enabled)
# mongo_username: trader
# mongo_password: !ENV ${MONGO_PASSWORD:defaultpass}
```

#### Production MongoDB Configuration

For production deployment, configure MongoDB with:

```bash
# Create MongoDB configuration file /etc/mongod.conf
sudo nano /etc/mongod.conf
```

```yaml
# /etc/mongod.conf
storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true
  wiredTiger:
    engineConfig:
      cacheSizeGB: 8  # Adjust based on available RAM

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log
  logRotate: reopen

net:
  port: 27017
  bindIp: 127.0.0.1  # Restrict to localhost for security

# Enable authentication in production
# security:
#   authorization: enabled
```

### Parquet Files (High-Performance Time Series)

Parquet format provides superior performance for time series data:

```bash
# Create directory structure for Parquet data
mkdir -p ~/pysystemtrade_data/parquet/{adjusted_prices,multiple_prices,contract_prices,fx_prices,spreads}
```

Configure in `private_config.yaml`:
```yaml
# Parquet data paths
parquet_store_path: ~/pysystemtrade_data/parquet/
```

### CSV Files (Configuration & Backtesting)

CSV files are used for:
- **Configuration data** - Instrument parameters, roll calendars
- **Backtesting data** - Historical price data for research
- **Backup exports** - Emergency data recovery

No additional setup required - files are included in the repository.

## Interactive Brokers Setup (Optional)

### 1. Install IB Gateway or TWS

- Download from [Interactive Brokers website](https://www.interactivebrokers.com/en/index.php?f=5041)
- Install IB Gateway (recommended) or Trader Workstation
- Set up paper trading or live account

### 2. Configure IB Gateway

Gateway settings:
- **Socket port:** 4001
- **Trusted IP addresses:** 127.0.0.1 (localhost)
- **Read-only API:** OFF (for trading)
- **Download open orders on connection:** ON

### 3. Test Connection

```python
from sysbrokers.IB.ib_connection import connectionIB

# Test connection (adjust client_id as needed)
conn = connectionIB(999, ib_ipaddress="127.0.0.1", ib_port=4001)
print(conn)
```

## Configuration

### Configuration Hierarchy

pysystemtrade uses a sophisticated configuration system with inheritance:

1. **System defaults** (`sysdata/config/defaults.yaml`) - Base configuration
2. **Private config** (`private/private_config.yaml`) - User overrides  
3. **Environment variables** - Runtime overrides with `!ENV` tags
4. **Command-line arguments** - Process-specific overrides

### System Defaults

Main configuration in `sysdata/config/defaults.yaml`:
- **Base currency and volatility targeting**
- **Database connection defaults**
- **Logging levels and formats**  
- **System parameters** (correlation estimation, portfolio optimization)
- **Process scheduling and timeouts**
- **Risk management defaults**

### Private Configuration

Create `private/private_config.yaml` for sensitive and deployment-specific settings:

```yaml
# Database Configuration
mongo_host: localhost
mongo_db: production
mongo_port: 27017

# Trading Capital Management
base_currency: USD
percentage_vol_target: 20  # Annual volatility target
notional_trading_capital: 100000
max_risk_capital: 150000  # Maximum capital at risk

# Interactive Brokers Configuration
ib_ipaddress: 127.0.0.1
ib_port: 4001  # Gateway port (4002 for TWS)
ib_idoffset: 1000  # Client ID offset

# Email Notifications (Production)
email_address: !ENV ${TRADING_EMAIL:alerts@yourtrading.com}
email_pwd: !ENV ${EMAIL_APP_PASSWORD}
email_server: smtp.gmail.com
email_port: 587

# File Storage Paths
csv_data_path: ~/pysystemtrade_data/csv/
parquet_store_path: ~/pysystemtrade_data/parquet/
backup_directory: ~/pysystemtrade_backups/
email_store_filename: ~/pysystemtrade_data/logs/stored_emails.log

# Process Control
process_monitor_seconds: 60
max_executions_per_process: 1000
process_timeout_seconds: 1800

# Risk Management Overrides
max_position_contracts: 100
max_order_size_contracts: 50
position_limit_buffer: 0.1

# Strategy Configuration
strategy_list:
  - example_strategy
  - momentum_strategy
  
# Logging Levels (DEBUG, INFO, WARN, ERROR)
log_level: INFO
production_log_level: WARN
```

### Environment Variables

Use environment variables for sensitive data:

```bash
# .env file or system environment
export MONGO_PASSWORD="your_secure_password"
export TRADING_EMAIL="alerts@yourtrading.com"
export EMAIL_APP_PASSWORD="your_app_specific_password"
export IB_ACCOUNT="DU123456"  # Paper trading account
```

## Testing Your Installation

### Run Test Suite

```bash
# Run all tests (~45 seconds)
python -m pytest

# Run specific test module
python -m pytest syscore/tests/

# Run with verbose output
python -m pytest -v
```

### Test System Components

```python
# Test data loading
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
data = csvFuturesSimData()
print(data.get_instrument_list())

# Test simple system
from systems.provided.example.simplesystem import simplesystem
system = simplesystem()
print(system.portfolio.get_notional_position("SOFR").tail(5))
```

## Troubleshooting

### Common Issues

**1. Python Version Error**
```
Error: pysystemtrade requires Python 3.10.0 or later
```
Solution: Install Python 3.10+ using pyenv or system package manager

**2. MongoDB Connection Error**
```
ServerSelectionTimeoutError: localhost:27017
```
Solution: Ensure MongoDB is running and check connection settings

**3. Import Errors**
```
ModuleNotFoundError: No module named 'pandas'
```
Solution: Activate virtual environment and reinstall dependencies

**4. Permission Errors (Linux)**
```
error: externally-managed-environment
```
Solution: Use virtual environment or add `--break-system-packages` flag

### Getting Help

1. **Check logs** - Look in system logs for error details
2. **Search issues** - Check [GitHub Issues](https://github.com/robcarver17/pysystemtrade/issues)
3. **Documentation** - Review official docs and this guide
4. **Community** - Ask questions in GitHub Discussions

## Next Steps

Once installed:
1. **Read** - [Quick Start Guide](quick-start.md) 
2. **Explore** - Run examples in `/examples/`
3. **Learn** - Study [System Architecture](architecture.md)
4. **Build** - Create your first trading strategy

## Production Deployment

### Server Specifications

**Minimum Production Setup:**
- **CPU:** 4 cores, 2.5GHz+
- **RAM:** 16GB (32GB recommended)
- **Storage:** 100GB SSD
- **Network:** Stable broadband with redundancy
- **Uptime:** 99.9% SLA VPS/dedicated server

**Enterprise Setup:**
- **CPU:** 8+ cores, 3.0GHz+  
- **RAM:** 64GB+ for multiple strategies
- **Storage:** 500GB+ SSD with RAID
- **Network:** Dedicated fiber connection
- **Redundancy:** Hot standby server

### System Hardening

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash pysystemtrade
sudo usermod -aG sudo pysystemtrade

# Set up SSH key authentication
sudo mkdir /home/pysystemtrade/.ssh
sudo cp ~/.ssh/authorized_keys /home/pysystemtrade/.ssh/
sudo chown -R pysystemtrade:pysystemtrade /home/pysystemtrade/.ssh/
sudo chmod 700 /home/pysystemtrade/.ssh/
sudo chmod 600 /home/pysystemtrade/.ssh/authorized_keys

# Disable password authentication
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl reload sshd
```

### Process Management Setup

**Option 1: Systemd Services**

```bash
# Create systemd service file
sudo nano /etc/systemd/system/pysystemtrade-runner.service
```

```ini
[Unit]
Description=pysystemtrade Process Runner
After=mongodb.service
Requires=mongodb.service

[Service]
Type=simple
User=pysystemtrade
WorkingDirectory=/home/pysystemtrade/pysystemtrade
Environment=PYTHONPATH=/home/pysystemtrade/pysystemtrade
ExecStart=/home/pysystemtrade/venv/bin/python sysproduction/linux/scripts/run_processes.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable pysystemtrade-runner.service
sudo systemctl start pysystemtrade-runner.service
```

**Option 2: Supervisord (Recommended)**

```bash
# Install supervisord
sudo apt install supervisor

# Create configuration
sudo nano /etc/supervisor/conf.d/pysystemtrade.conf
```

```ini
[program:pysystemtrade_runner]
command=/home/pysystemtrade/venv/bin/python sysproduction/linux/scripts/run_processes.py
directory=/home/pysystemtrade/pysystemtrade
user=pysystemtrade
environment=PYTHONPATH="/home/pysystemtrade/pysystemtrade"
autostart=true
autorestart=true
startretries=3
redirect_stderr=true
stdout_logfile=/var/log/supervisor/pysystemtrade_runner.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
```

### Automated Backup System

```bash
# Create backup script
nano ~/pysystemtrade/scripts/backup_production.sh
```

```bash
#!/bin/bash
# Production backup script

BACKUP_DIR="/home/pysystemtrade/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# MongoDB backup
mongodump --host localhost --port 27017 --db production --out $BACKUP_DIR/mongodb/

# Parquet data backup
cp -r ~/pysystemtrade_data/parquet/ $BACKUP_DIR/parquet/

# Configuration backup
cp -r ~/pysystemtrade/private/ $BACKUP_DIR/private/
cp ~/pysystemtrade/CLAUDE.md $BACKUP_DIR/

# Compress and upload to remote storage
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
# rsync $BACKUP_DIR.tar.gz user@backup-server:/path/to/backups/

# Cleanup old backups (keep 30 days)
find /home/pysystemtrade/backups/ -name "*.tar.gz" -mtime +30 -delete
```

```bash
# Add to crontab for daily backups
crontab -e
# Add: 0 2 * * * /home/pysystemtrade/pysystemtrade/scripts/backup_production.sh
```

### Monitoring & Alerting Setup

**Log Monitoring:**

```bash
# Install log monitoring tools
sudo apt install logwatch fail2ban

# Configure logwatch for pysystemtrade logs
sudo nano /etc/logwatch/conf/services/pysystemtrade.conf
```

**Health Check Script:**

```python
# ~/pysystemtrade/scripts/health_check.py
import sys
from sysproduction.data.get_data import dataBlob

def health_check():
    try:
        data = dataBlob(log_name="health_check")
        # Check database connection
        instruments = data.db_futures_contract.get_list_of_all_instruments_with_contracts()
        assert len(instruments) > 0
        
        # Check processes
        process_status = data.db_process_control.get_dict_of_process_status()
        critical_processes = ['run_strategy_order_generator', 'run_stack_handler']
        
        for process in critical_processes:
            if process not in process_status or process_status[process] != 'RUNNING':
                raise Exception(f"Critical process {process} not running")
                
        return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

if __name__ == "__main__":
    sys.exit(0 if health_check() else 1)
```

### Security Measures

1. **Firewall Configuration:**

```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 27017/tcp  # MongoDB (localhost only)
```

2. **File Permissions:**

```bash
# Secure configuration files
chmod 600 private/private_config.yaml
chmod 600 ~/.ssh/authorized_keys

# Secure data directories
chmod 750 ~/pysystemtrade_data/
chmod 640 ~/pysystemtrade_data/logs/*
```

3. **MongoDB Security:**

```bash
# Enable MongoDB authentication (production)
mongo admin --eval 'db.createUser({user:"admin", pwd:"strongpassword", roles:["userAdminAnyDatabase"]})'
```

### Performance Optimization

1. **System Tuning:**

```bash
# Increase file descriptor limits
echo "pysystemtrade soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "pysystemtrade hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize MongoDB
echo "never" | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
```

2. **Python Optimization:**

```bash
# Use optimized Python build
export PYTHONOPTIMIZE=2
export PYTHONDONTWRITEBYTECODE=1
```

### Disaster Recovery

1. **Backup Strategy:** 
   - Daily automated backups
   - Weekly offsite replication
   - Monthly full system images

2. **Recovery Procedures:**
   - Document step-by-step recovery process
   - Test recovery quarterly
   - Maintain hot standby system

3. **Business Continuity:**
   - Emergency trading halt procedures
   - Manual override capabilities
   - Communication protocols

For detailed production setup, see the [Development Workflow](development-workflow.md) guide.

---

**Next:** [Quick Start Guide](quick-start.md) to build your first trading system.