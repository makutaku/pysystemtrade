






# Installation

```
conda create -n "pysystemtrade" python=3.10.13
conda activate "pysystemtrade"
```

```
git clone https://github.com/makutaku/pysystemtrade.git
cd pysystemtrade
git remote set-url origin https://<SECRET>>@github.com/makutaku/pysystemtrade.git
```

```
pip install cython
pip install -r requirements.txt
python setup.py develop
```

```
# conda install --file requirements.txt
```



# Verification

## Verify Installation
```
pytest --junit-xml=tests.xml
pytest --runslow  --disable-warnings
```

## Verify IB

```
from sysbrokers.IB.ib_orders_data import ibOrdersData
ib_orders_data = ibOrdersData(conn)
ib_orders_data.ib_client
ib_orders_data.ibconnection
```

```
from sysbrokers.IB.ib_Fx_prices_data import ibFxPricesData
from sysdata.data_blob import dataBlob
ibfxpricedata = ibFxPricesData(conn, dataBlob())
ibfxpricedata.get_list_of_fxcodes()  # codes must be in .csv file /sysbrokers/IB/ibConfigSpotFX.csv
ibfxpricedata.get_fx_prices("GBPUSD") # returns fxPrices object
```


## Verify MongoDB

```
from pymongo import MongoClient
mongo_port = 27017
mongo_host = "192.168.1.13"
client = MongoClient(mongo_host, mongo_port)
database_names = client.list_database_names()
database_names
```


# Data

1. Set up some static configuration information for instruments, and roll parameters
1. Get, and store, some historical data
1. Create, and store, roll calendars (these are not actually used once multiple prices are created, so the storage is temporary)
1. Create and store 'multiple' price series containing the relevant contracts we need for any given time period
1. Create and store back-adjusted prices: a single price series
1. Get, and store, spot FX prices

## Initialization
### Instrument configuration

1. Copy csv configs from PYST repository to share  
   ```
   repo_csv_config=data/futures/csvconfig
   csv_config=/data/pysystemtrade/csv_store
   mkdir -p "$csv_config"
   cp "$repo_csv_config"/instrumentconfig.csv "$csv_config"
   cp "$repo_csv_config"/rollconfig.csv "$csv_config"
   cp "$repo_csv_config"/spreadcosts.csv "$csv_config"
   ```
2. Ingest spread costs to mongo DB    
``` python sysinit/futures/repocsv_spread_costs.py ```
3. Ingest historical contract prices
   1. From the broker (Interactive Brokers)  
   ``` python sysinit/futures/seed_price_data_from_IB.py ```
   2. From an external data source (Barchart)  
   ```
   python sysinit/futures/contract_prices_from_csv_to_arctic.py /data/barchart/futures/1d --no-confirm --instruments GOLD,SP500_mini
   python sysinit/futures/contract_prices_from_csv_to_arctic.py /data/barchart/futures/1d --no-confirm
   ```
4. Generate roll calendars  
``` 
output_path="$csv_config"/roll_calendars_csv && \
mkdir -p "$output_path" && \
python sysinit/futures/rollcalendars_from_arcticprices_to_csv.py --instrument-code CORN --output-datapath "$output_path" --no-confirm 
```
7. Generate multiple prices  
```
output_path="$csv_config"/multiple_prices_csv && \
mkdir -p "$output_path" && \
python sysinit/futures/multipleprices_from_db_prices_and_csv_calendars_to_db.py --csv-roll-data-path /data/pysystemtrade/roll_calendars_csv --output-mode db_and_csv --csv-multiple-data-path "$output_path" --no-confirm   
```
8. Generate Adjusted Prices  
``` 
output_path="$csv_config"/adjusted_prices_csv && \
mkdir -p "$output_path" && \
python sysinit/futures/adjustedprices_from_db_multiple_to_db.py --output-mode db_and_csv --csv-adj-data-path "$output_path" --no-confirm
```
9. Import FX prices
```
output_path="$csv_config"/fx_prices_csv && \
mkdir -p "$output_path" && \
python sysinit/futures/spotfx_from_csv_to_db.py --output-mode db_and_csv --input-path /data/barchart/forex/1d --csv-fx-path "$output_path"
```

## Jobs

### run_daily_fx_and_contract_updates
07:00 - 23:50
* update_fx_prices:
  *   max_executions: 1
* update_sampled_contracts:
  *   max_executions: 1

### run_daily_prices_updates  
20:00 - 23:50
```
download_by_zone:
    ASIA: '07:00'
    EMEA: '18:00'
    US: '20:00'
```
* update_historical_prices:
  *   max_executions: 1

###  run_daily_update_multiple_adjusted_prices:
23:00 - 23:50
* update_multiple_adjusted_prices:
  * max_executions: 1


### run_capital_update
01:00 - 19:50
* update_total_capital:  
every 2 hours throughout the day; in a crisis I like to keep an eye on my account value
  *    frequency: 120
  *    max_executions: 10 # nominal figure, since uptime is a little less than 20 hours
* strategy_allocation:  
don't bother updating more often than we run backtests
  *    max_executions: 1   
    ` Error [Missing config element strategy_list] whilst allocating strategy margin `

###  run_stack_handler:
00:01 - 19:45
* check_external_position_break:  
  * frequency: 0
  * max_executions: -1
* spawn_children_from_new_instrument_orders:  
  * frequency: 0
  * max_executions: -1
* generate_force_roll_orders:  
  * frequency: 0
  * max_executions: 1
* create_broker_orders_from_contract_orders:  
  * frequency: 0
  * max_executions: -1
* process_fills_stack:  
  * frequency: 0
  * max_executions: -1
* handle_completed_orders:  
  * frequency: 0
  * max_executions: -1
* refresh_additional_sampling_all_instruments:  
  * frequency: 60
  * max_executions: -1
* safe_stack_removal:  
  * run_on_completion_only: True

### run_systems
20:05 - 23:50

### run_strategy_order_generator
20:10 - 23:50


### run_reports: 
20:25 - 23:50  
depends on run_strategy_order_generator  
max_executions: 1  
* costs_report
* liquidity_report
* status_report
* roll_report
* daily_pandl_report
* reconcile_report
* trade_report
* strategy_report
* risk_report
* slippage_report
* instrument_risk_report
* min_capital
* duplicate_market
* remove_markets_report
* market_monitor_report
* account_curve_report


###  run_cleaners:  
20:20 - 23:50
* clean_backtest_states:  
  * max_executions: 1
* clean_echo_files:  
  * max_executions: 1
* clean_log_files:  
  * max_executions: 1


## Deprecated Price Updating Job
all this stuff happens once. the order matters.
* update_fx_prices:
  * max_executions: 1
* update_sampled_contracts:
  * max_executions: 1
* update_historical_prices:
  *  max_executions: 1
* update_multiple_adjusted_prices:  
  * max_executions: 1


process_configuration_previous_process:
  run_systems: 'run_daily_prices_updates' # no point running a backtest with stale prices.
  run_strategy_order_generator: 'run_systems' # will be no orders to generate until backtest system has run
  run_cleaners: 'run_strategy_order_generator' # wait until the main 'big 3' daily processes have run before tidying up
  run_backups: 'run_cleaners' # this can take a while, will be less stuff to back up if we've already cleaned
  run_reports: 'run_strategy_order_generator' # will be more interesting reports if we run after other stuff has close

## Other Issues

```
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
data=csvFuturesSimData()
data
```






###################

from systems.provided.futures_chapter15.basesystem import futures_system
system=futures_system()
system.portfolio.get_notional_position("EDOLLAR")








=================================================================================================================

MongoDB



docker run --rm -v /path/to/file/in/container:$(pwd) -w $(pwd) <image_id> rm /path/to/file/in/container


mongo                                             latest        2e123a0ccb4b   2 weeks ago     757MB


docker run --rm 2e123a0ccb4b rm -f /tmp/mongodb-27017.sock

docker run --rm -it 2e123a0ccb4b sh

docker run --rm -it f0bbeaaea8c38c99c547152a83a6e21d9e3e589ae06f4c94faccfb12c6f3bda6 sh



# PARQUET

```
# install the parquet CLI tool
pip install parquet-tools

# use the following command to show the contenet of all parquet files matching the pattern:
for file in ~/workspace/data/parquet/futures_contract_prices/GOLD_micro*.parquet; do echo $file; parquet-tools show "$file"; done




data/futures/adjusted_prices_csv/BEL20.csv      |  4312 ------
 data/futures/adjusted_prices_csv/EDOLLAR.csv    | 22442 ---------------------------
 data/futures/adjusted_prices_csv/LUMBER.csv     | 42563 ----------------------------------------------------
 data/futures/adjusted_prices_csv/MID-DAX.csv    | 28788 -----------------------------------
 data/futures/adjusted_prices_csv/NIFTY.csv      | 14997 ------------------
 data/futures/adjusted_prices_csv/RAPESEED.csv   | 29562 ------------------------------------
 data/futures/adjusted_prices_csv/USIRS10.csv    | 20302 -------------------------
 data/futures/adjusted_prices_csv/USIRS2ERIS.csv |   494 -
 data/futures/adjusted_prices_csv/USIRS5.csv     | 20418 -------------------------
 data/futures/adjusted_prices_csv/USIRS5ERIS.csv |  2109 ---
 data/futures/csvconfig/spreadcosts.csv          |     2 +-
 data/futures/multiple_prices_csv/BEL20.csv      |  4340 ------
 data/futures/multiple_prices_csv/EDOLLAR.csv    | 22462 ---------------------------
 data/futures/multiple_prices_csv/LUMBER.csv     | 42563 ----------------------------------------------------
 data/futures/multiple_prices_csv/MID-DAX.csv    | 28788 -----------------------------------
 data/futures/multiple_prices_csv/NIFTY.csv      | 14997 ------------------
 data/futures/multiple_prices_csv/RAPESEED.csv   | 29562 ------------------------------------
 data/futures/multiple_prices_csv/USIRS10.csv    | 20302 -------------------------
 data/futures/multiple_prices_csv/USIRS2ERIS.csv |   494 -
 data/futures/multiple_prices_csv/USIRS5.csv     | 20418 -------------------------
 data/futures/multiple_prices_csv/USIRS5ERIS.csv |  2109 ---
 data/futures/roll_calendars_csv/BITCOIN#1.csv   |    73 +
 data/futures/roll_calendars_csv/BITCOIN#2.csv   |    73 +
 data/futures/roll_calendars_csv/BITCOIN#3.csv   |    73 +
 data/futures/roll_calendars_csv/EDOLLAR#1.csv   |     5 +-
 data/futures/roll_calendars_csv/ETHEREUM#1.csv  |    35 +
 data/futures/roll_calendars_csv/ETHEREUM#2.csv  |    35 +
 data/futures/roll_calendars_csv/ETHEREUM#3.csv  |    35 +
 data/futures/roll_calendars_csv/IBEX_mini.csv   |   372 +
 data/futures/roll_calendars_csv/NIFTY-IN.csv    |    14 +

```
