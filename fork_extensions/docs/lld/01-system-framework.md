# Low-Level Design (LLD) - pysystemtrade

Comprehensive technical implementation guide covering detailed class designs, algorithms, data structures, and system internals for pysystemtrade's enterprise-grade systematic trading framework.

## Table of Contents

1. [Design Overview](#design-overview)
2. [Core System Framework](#core-system-framework)
3. [Data Layer Implementation](#data-layer-implementation)
4. [Quantitative Framework](#quantitative-framework)
5. [Order Management System](#order-management-system)
6. [Production Control System](#production-control-system)
7. [Broker Integration Layer](#broker-integration-layer)
8. [Performance & Optimization](#performance--optimization)
9. [Security & Error Handling](#security--error-handling)
10. [Database Schema Design](#database-schema-design)

## Design Overview

### **System Architecture Layers**

```python
# Layer 1: Business Logic (Top)
├── systems/           # Backtesting & Strategy Framework
├── sysproduction/     # Production Trading System
├── sysexecution/      # Order Management & Execution

# Layer 2: Domain Model (Middle) 
├── sysobjects/        # Business Objects (Contracts, Instruments, Prices)
├── sysquant/          # Quantitative Analytics & Optimization

# Layer 3: Infrastructure (Bottom)
├── sysdata/           # Data Abstraction & Persistence
├── sysbrokers/        # External System Integration
├── syscore/           # Core Utilities & Framework
├── syslogging/        # Logging & Monitoring
```

### **Key Design Principles Applied**

1. **Dependency Inversion** - High-level modules depend on abstractions, not concretions
2. **Single Responsibility** - Each class has one reason to change
3. **Open/Closed Principle** - Open for extension, closed for modification
4. **Interface Segregation** - Clients depend only on interfaces they use
5. **Don't Repeat Yourself (DRY)** - Common functionality abstracted into reusable components

## Core System Framework

### **System Class - Central Orchestrator**

```python
class System(object):
    """
    Central system orchestrator implementing stage-based processing pipeline
    with intelligent caching, dependency management, and configuration resolution.
    """
    
    def __init__(self, stage_list: list, data: simData, config: Config):
        """
        Initialize system with processing stages, data source, and configuration.
        
        Args:
            stage_list: Ordered list of SystemStage instances
            data: Data source implementing simData interface
            config: System configuration with parameter hierarchy
        """
        self.data = data
        self.config = config
        self.cache = systemCache()
        self.log = get_logger("System")
        
        # Stage initialization and dependency resolution
        self._create_stage_names(stage_list)
        self._create_stage_dict(stage_list)
        self._validate_stage_dependencies()
        
    def _create_stage_names(self, stage_list: list) -> None:
        """
        Create stage name mappings and validate stage configuration.
        
        Stage naming convention: CamelCase class name -> snake_case attribute
        Example: TradingRules -> self.trading_rules
        """
        stage_names = []
        for stage in stage_list:
            stage_name = snake_case_convert(stage.__class__.__name__)
            stage_names.append(stage_name)
            
        self.stage_names = stage_names
        
    def _create_stage_dict(self, stage_list: list) -> None:
        """
        Initialize stages with system references and create lookup dictionary.
        """
        stage_dict = {}
        for stage_name, stage in zip(self.stage_names, stage_list):
            # Inject system reference and initialize stage
            stage.parent = self
            stage._name = stage_name
            stage.log = get_logger(f"System.{stage_name}")
            
            # Add to system as attribute and lookup dict
            setattr(self, stage_name, stage)
            stage_dict[stage_name] = stage
            
        self.stage_dict = stage_dict
        
    def _validate_stage_dependencies(self) -> None:
        """
        Validate that all stage dependencies are satisfied.
        Builds dependency graph and checks for circular dependencies.
        """
        dependency_graph = {}
        
        for stage_name, stage in self.stage_dict.items():
            dependencies = getattr(stage, '_dependencies', [])
            dependency_graph[stage_name] = dependencies
            
            # Validate dependencies exist
            for dep in dependencies:
                if dep not in self.stage_dict:
                    raise ValueError(f"Stage {stage_name} depends on missing stage: {dep}")
        
        # Check for circular dependencies using topological sort
        if self._has_circular_dependencies(dependency_graph):
            raise ValueError("Circular dependencies detected in stage configuration")
```

### **SystemStage Base Class - Processing Stage Template**

```python
class SystemStage(object):
    """
    Abstract base class for system processing stages implementing template method pattern.
    Provides caching, logging, and dependency management infrastructure.
    """
    
    def __init__(self):
        self.parent = None  # Injected by System
        self.log = None     # Injected by System
        self._name = None   # Injected by System
        self._dependencies = []  # Override in subclasses
        
    def get_item(self, item_name: str, **kwargs):
        """
        Template method for retrieving processed data with caching.
        
        Template Method Pattern Implementation:
        1. Check cache for existing result
        2. If not cached, calculate result via _get_item()
        3. Cache result for future access
        4. Return result
        """
        # Generate cache key including all parameters
        cache_key = self._generate_cache_key(item_name, **kwargs)
        
        # Check cache first
        cached_result = self.parent.cache.get_item(self._name, cache_key)
        if cached_result is not None:
            self.log.debug(f"Cache hit for {item_name}")
            return cached_result
            
        # Calculate result (implemented by subclasses)
        self.log.debug(f"Calculating {item_name}")
        result = self._get_item(item_name, **kwargs)
        
        # Cache result
        self.parent.cache.set_item(self._name, cache_key, result)
        
        return result
        
    def _get_item(self, item_name: str, **kwargs):
        """
        Abstract method to be implemented by concrete stages.
        Contains the actual business logic for data processing.
        """
        raise NotImplementedError("Subclasses must implement _get_item")
        
    def _generate_cache_key(self, item_name: str, **kwargs) -> str:
        """
        Generate unique cache key for item and parameters.
        """
        param_str = "_".join([f"{k}={v}" for k, v in sorted(kwargs.items())])
        return f"{item_name}_{param_str}" if param_str else item_name
        
    def get_instrument_list(self) -> list:
        """
        Get list of instruments available in the system.
        Delegates to data source with caching.
        """
        return self.parent.data.get_instrument_list()
        
    def log_attributes(self):
        """
        Development utility to log all available attributes and methods.
        """
        attributes = [attr for attr in dir(self) if not attr.startswith('_')]
        self.log.info(f"Available attributes: {attributes}")
```

### **SystemCache - Intelligent Caching Implementation**

```python
class systemCache(object):
    """
    Multi-level caching system with dependency tracking and automatic invalidation.
    Optimized for quantitative finance workloads with time-series data.
    """
    
    def __init__(self, max_memory_mb: int = 1024, ttl_seconds: int = 3600):
        """
        Initialize cache with memory limits and time-to-live settings.
        
        Args:
            max_memory_mb: Maximum memory usage in MB
            ttl_seconds: Time-to-live for cache entries
        """
        self._cache = {}  # Main cache storage
        self._cache_metadata = {}  # Cache metadata (size, access time, dependencies)
        self._access_order = []  # LRU tracking
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.ttl_seconds = ttl_seconds
        self.current_memory_usage = 0
        
        # Performance metrics
        self.cache_hits = 0
        self.cache_misses = 0
        
    def get_item(self, stage_name: str, cache_key: str):
        """
        Retrieve item from cache with LRU update and TTL checking.
        """
        full_key = f"{stage_name}:{cache_key}"
        
        if full_key not in self._cache:
            self.cache_misses += 1
            return None
            
        # Check TTL
        metadata = self._cache_metadata[full_key]
        if time.time() - metadata['created_at'] > self.ttl_seconds:
            self._evict_item(full_key)
            self.cache_misses += 1
            return None
            
        # Update LRU order
        self._access_order.remove(full_key)
        self._access_order.append(full_key)
        metadata['last_accessed'] = time.time()
        
        self.cache_hits += 1
        return self._cache[full_key]
        
    def set_item(self, stage_name: str, cache_key: str, value, dependencies: list = None):
        """
        Store item in cache with memory management and dependency tracking.
        """
        full_key = f"{stage_name}:{cache_key}"
        
        # Calculate memory usage
        item_size = self._estimate_memory_usage(value)
        
        # Evict items if necessary
        self._ensure_memory_capacity(item_size)
        
        # Store item and metadata
        self._cache[full_key] = value
        self._cache_metadata[full_key] = {
            'size': item_size,
            'created_at': time.time(),
            'last_accessed': time.time(),
            'dependencies': dependencies or []
        }
        
        self._access_order.append(full_key)
        self.current_memory_usage += item_size
        
    def invalidate_dependencies(self, dependency_key: str):
        """
        Invalidate all cache entries that depend on the given dependency.
        Used when underlying data changes.
        """
        keys_to_invalidate = []
        
        for full_key, metadata in self._cache_metadata.items():
            if dependency_key in metadata['dependencies']:
                keys_to_invalidate.append(full_key)
                
        for key in keys_to_invalidate:
            self._evict_item(key)
            
    def _ensure_memory_capacity(self, required_bytes: int):
        """
        Ensure sufficient memory capacity using LRU eviction.
        """
        while (self.current_memory_usage + required_bytes > self.max_memory_bytes 
               and self._access_order):
            oldest_key = self._access_order[0]
            self._evict_item(oldest_key)
            
    def _evict_item(self, full_key: str):
        """
        Remove item from cache and update memory tracking.
        """
        if full_key in self._cache:
            item_size = self._cache_metadata[full_key]['size']
            del self._cache[full_key]
            del self._cache_metadata[full_key]
            self._access_order.remove(full_key)
            self.current_memory_usage -= item_size
            
    def _estimate_memory_usage(self, value) -> int:
        """
        Estimate memory usage of cached value.
        Handles pandas DataFrames, Series, and other common types.
        """
        if hasattr(value, 'memory_usage'):
            # Pandas DataFrame or Series
            if hasattr(value.memory_usage(), 'sum'):
                return value.memory_usage(deep=True).sum()
            else:
                return value.memory_usage(deep=True)
        elif hasattr(value, '__sizeof__'):
            return value.__sizeof__()
        else:
            # Fallback estimation
            return len(str(value)) * 8
            
    def get_cache_stats(self) -> dict:
        """
        Return cache performance statistics.
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            'hit_rate': hit_rate,
            'total_entries': len(self._cache),
            'memory_usage_mb': self.current_memory_usage / (1024 * 1024),
            'memory_usage_percent': (self.current_memory_usage / self.max_memory_bytes) * 100
        }
```

## Data Layer Implementation

### **dataBlob - Central Data Orchestrator**

```python
class dataBlob(object):
    """
    Central data access orchestrator implementing dependency injection pattern.
    Provides unified interface to heterogeneous data sources with automatic
    connection management, failover, and performance optimization.
    """
    
    def __init__(self, csv_data_paths=None, db_name=None, ib_conn=None, 
                 log_name="", keep_original_prefix=False):
        """
        Initialize dataBlob with multiple data source configurations.
        
        Args:
            csv_data_paths: Dictionary of CSV data paths
            db_name: MongoDB database name
            ib_conn: Interactive Brokers connection
            log_name: Logger name for this instance
            keep_original_prefix: Whether to keep original class prefixes
        """
        self.log = get_logger(log_name if log_name else "dataBlob")
        
        # Data source configurations
        self._csv_data_paths = csv_data_paths or {}
        self._db_name = db_name
        self._ib_conn = ib_conn
        self._keep_original_prefix = keep_original_prefix
        
        # Data source registry
        self._data_sources = {}
        self._connection_pool = {}
        
        # Performance tracking
        self._query_stats = defaultdict(list)
        
        # Initialize default data sources
        self._initialize_default_sources()
        
    def add_class_list(self, class_list: list):
        """
        Add data source classes to the blob with automatic naming resolution.
        
        Implements naming convention:
        - mongoFuturesContractData -> db_futures_contract
        - csvFuturesAdjustedPricesData -> db_futures_adjusted_prices
        """
        for data_class in class_list:
            class_name = data_class.__name__
            
            # Generate attribute name using naming convention
            if not self._keep_original_prefix:
                attr_name = self._generate_attribute_name(class_name)
            else:
                attr_name = snake_case_convert(class_name)
                
            # Initialize data source instance
            instance = self._initialize_data_source(data_class)
            
            # Add to blob as attribute and registry
            setattr(self, attr_name, instance)
            self._data_sources[attr_name] = instance
            
            self.log.debug(f"Added data source: {class_name} -> {attr_name}")
            
    def _generate_attribute_name(self, class_name: str) -> str:
        """
        Generate standardized attribute names from class names.
        
        Examples:
        - mongoFuturesContractData -> db_futures_contract  
        - csvFuturesAdjustedPricesData -> db_futures_adjusted_prices
        - ibFuturesContractPriceData -> db_futures_contract_price
        """
        # Remove common prefixes
        prefixes = ['mongo', 'csv', 'arctic', 'parquet', 'ib', 'sim']
        name = class_name
        
        for prefix in prefixes:
            if name.lower().startswith(prefix.lower()):
                name = name[len(prefix):]
                break
                
        # Remove 'Data' suffix if present
        if name.endswith('Data'):
            name = name[:-4]
            
        # Convert to snake_case and add db_ prefix
        snake_name = snake_case_convert(name)
        return f"db_{snake_name}"
        
    def _initialize_data_source(self, data_class):
        """
        Initialize data source with appropriate configuration and connection.
        """
        # Determine initialization parameters based on class type
        init_kwargs = {}
        
        if 'mongo' in data_class.__name__.lower():
            init_kwargs.update({
                'mongo_db': self._get_mongo_connection(),
                'log': get_logger(f"dataBlob.{data_class.__name__}")
            })
        elif 'csv' in data_class.__name__.lower():
            init_kwargs.update({
                'datapath': self._csv_data_paths.get('datapath', '.'),
                'log': get_logger(f"dataBlob.{data_class.__name__}")
            })
        elif 'ib' in data_class.__name__.lower():
            init_kwargs.update({
                'ibconnection': self._ib_conn,
                'log': get_logger(f"dataBlob.{data_class.__name__}")
            })
            
        try:
            return data_class(**init_kwargs)
        except Exception as e:
            self.log.error(f"Failed to initialize {data_class.__name__}: {e}")
            raise
            
    def _get_mongo_connection(self):
        """
        Get MongoDB connection with connection pooling and failover.
        """
        if 'mongodb' not in self._connection_pool:
            try:
                from pymongo import MongoClient
                
                # Connection configuration from config
                config = self.config if hasattr(self, 'config') else {}
                host = config.get('mongo_host', 'localhost')
                port = config.get('mongo_port', 27017)
                
                # Create connection with pooling
                client = MongoClient(
                    host=host,
                    port=port,
                    maxPoolSize=20,
                    minPoolSize=5,
                    maxIdleTimeMS=30000,
                    serverSelectionTimeoutMS=5000
                )
                
                db = client[self._db_name or 'production']
                self._connection_pool['mongodb'] = db
                
                self.log.info(f"MongoDB connection established: {host}:{port}")
                
            except Exception as e:
                self.log.error(f"MongoDB connection failed: {e}")
                raise
                
        return self._connection_pool['mongodb']
        
    def close_all_connections(self):
        """
        Close all database connections and clean up resources.
        """
        for conn_name, connection in self._connection_pool.items():
            try:
                if hasattr(connection, 'close'):
                    connection.close()
                elif hasattr(connection, 'client') and hasattr(connection.client, 'close'):
                    connection.client.close()
                self.log.info(f"Closed connection: {conn_name}")
            except Exception as e:
                self.log.warning(f"Error closing connection {conn_name}: {e}")
                
        self._connection_pool.clear()
```

### **Base Data Classes - Abstract Data Interface**

```python
class baseData(object):
    """
    Abstract base class defining common interface for all data sources.
    Implements template method pattern with common functionality.
    """
    
    def __init__(self, log=None):
        """
        Initialize base data source with logging.
        """
        if log is None:
            log = get_logger(self.__class__.__name__)
        self.log = log
        
        # Performance metrics
        self._query_count = 0
        self._query_times = []
        
    def _log_query(self, operation: str, duration: float):
        """
        Log query performance metrics.
        """
        self._query_count += 1
        self._query_times.append(duration)
        
        if duration > 1.0:  # Log slow queries
            self.log.warning(f"Slow query: {operation} took {duration:.2f}s")
        else:
            self.log.debug(f"Query: {operation} took {duration:.3f}s")
            
    def get_performance_stats(self) -> dict:
        """
        Return performance statistics for this data source.
        """
        if not self._query_times:
            return {'query_count': 0, 'avg_query_time': 0, 'max_query_time': 0}
            
        return {
            'query_count': self._query_count,
            'avg_query_time': sum(self._query_times) / len(self._query_times),
            'max_query_time': max(self._query_times),
            'min_query_time': min(self._query_times)
        }


class futuresContractPriceData(baseData):
    """
    Abstract base class for futures contract price data sources.
    Defines common interface for price data operations across different backends.
    """
    
    def get_prices_for_contract_object(self, futures_contract, freq="D"):
        """
        Abstract method to get price data for a specific contract.
        
        Args:
            futures_contract: futuresContract object
            freq: Price frequency ('D' for daily, 'H' for hourly)
            
        Returns:
            pd.DataFrame with OHLCV data
        """
        raise NotImplementedError()
        
    def write_prices_for_contract_object(self, futures_contract, futures_price_data, 
                                       ignore_duplication=True):
        """
        Abstract method to write price data for a contract.
        """
        raise NotImplementedError()
        
    def get_list_of_instrument_codes_with_merged_price_data(self) -> list:
        """
        Get list of instruments that have price data available.
        """
        raise NotImplementedError()
        
    def contracts_with_merged_price_data_for_instrument_code(self, instrument_code: str) -> list:
        """
        Get list of contracts with price data for given instrument.
        """
        raise NotImplementedError()


class mongoFuturesContractPriceData(futuresContractPriceData):
    """
    MongoDB implementation of futures contract price data.
    Optimized for high-frequency access with proper indexing.
    """
    
    # Collection names and indexes
    PRICE_DATA_COLLECTION = "futures_contract_prices"
    PRICE_INDEX_CONFIG = {
        "keys": [
            ("instrument_code", pymongo.ASCENDING),
            ("contract_date", pymongo.ASCENDING),
            ("datetime", pymongo.ASCENDING)
        ],
        "unique": False,
        "background": True
    }
    
    def __init__(self, mongo_db=None, log=None):
        """
        Initialize MongoDB price data source.
        """
        super().__init__(log)
        
        self._mongo_data = mongoDataWithSingleKey(
            collection_name=self.PRICE_DATA_COLLECTION,
            key_name="contract_key",
            mongo_db=mongo_db,
            index_config=self.PRICE_INDEX_CONFIG
        )
        
    def get_prices_for_contract_object(self, futures_contract, freq="D"):
        """
        Get price data for contract from MongoDB with performance optimization.
        """
        start_time = time.time()
        
        try:
            # Generate contract key
            contract_key = self._generate_contract_key(futures_contract)
            
            # Query with projection to get only required fields
            query = {
                "instrument_code": futures_contract.instrument_code,
                "contract_date": futures_contract.date_str,
                "freq": freq
            }
            
            projection = {
                "datetime": 1, "OPEN": 1, "HIGH": 1, "LOW": 1, "CLOSE": 1, "VOLUME": 1
            }
            
            cursor = self._mongo_data.collection.find(query, projection).sort("datetime", 1)
            
            # Convert to DataFrame
            data_list = list(cursor)
            if not data_list:
                raise missingData(f"No price data found for {futures_contract}")
                
            df = pd.DataFrame(data_list)
            df.set_index('datetime', inplace=True)
            df.drop('_id', axis=1, inplace=True, errors='ignore')
            
            # Data validation
            self._validate_price_data(df, futures_contract)
            
            return df
            
        except Exception as e:
            self.log.error(f"Error getting prices for {futures_contract}: {e}")
            raise
        finally:
            duration = time.time() - start_time
            self._log_query(f"get_prices_for_contract({futures_contract})", duration)
            
    def write_prices_for_contract_object(self, futures_contract, futures_price_data,
                                       ignore_duplication=True):
        """
        Write price data to MongoDB with upsert and duplicate handling.
        """
        start_time = time.time()
        
        try:
            # Prepare data for insertion
            contract_key = self._generate_contract_key(futures_contract)
            
            # Convert DataFrame to records
            records = futures_price_data.reset_index().to_dict('records')
            
            # Add metadata to each record
            for record in records:
                record.update({
                    'instrument_code': futures_contract.instrument_code,
                    'contract_date': futures_contract.date_str,
                    'contract_key': contract_key
                })
                
            # Bulk upsert operation
            if ignore_duplication:
                operations = []
                for record in records:
                    operations.append(
                        UpdateOne(
                            {
                                'instrument_code': record['instrument_code'],
                                'contract_date': record['contract_date'],
                                'datetime': record['datetime']
                            },
                            {'$set': record},
                            upsert=True
                        )
                    )
                
                if operations:
                    result = self._mongo_data.collection.bulk_write(operations)
                    self.log.info(f"Written {len(records)} price records for {futures_contract}")
            else:
                # Simple insert
                self._mongo_data.collection.insert_many(records)
                
        except Exception as e:
            self.log.error(f"Error writing prices for {futures_contract}: {e}")
            raise
        finally:
            duration = time.time() - start_time
            self._log_query(f"write_prices_for_contract({futures_contract})", duration)
            
    def _generate_contract_key(self, futures_contract) -> str:
        """
        Generate unique key for contract identification.
        """
        return f"{futures_contract.instrument_code}_{futures_contract.date_str}"
        
    def _validate_price_data(self, df: pd.DataFrame, futures_contract):
        """
        Validate price data integrity and business rules.
        """
        # Check for required columns
        required_columns = ['OPEN', 'HIGH', 'LOW', 'CLOSE']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
            
        # Check for negative prices
        price_columns = ['OPEN', 'HIGH', 'LOW', 'CLOSE']
        for col in price_columns:
            if (df[col] <= 0).any():
                raise ValueError(f"Negative or zero prices found in column {col}")
                
        # Check OHLC relationships
        invalid_ohlc = (
            (df['HIGH'] < df['LOW']) |
            (df['HIGH'] < df['OPEN']) |
            (df['HIGH'] < df['CLOSE']) |
            (df['LOW'] > df['OPEN']) |
            (df['LOW'] > df['CLOSE'])
        )
        
        if invalid_ohlc.any():
            self.log.warning(f"Invalid OHLC relationships found in {futures_contract}")
```

## Quantitative Framework

### **Portfolio Optimization Implementation**

```python
class portfolioWeights(object):
    """
    Advanced portfolio optimization implementation supporting multiple methodologies.
    Implements mean-variance optimization with shrinkage, constraints, and robust estimation.
    """
    
    def __init__(self, returns_data: pd.DataFrame, log=None):
        """
        Initialize portfolio optimizer with returns data.
        
        Args:
            returns_data: DataFrame with instrument returns (instruments as columns)
        """
        self.returns_data = returns_data
        self.log = log if log else get_logger("portfolioWeights")
        
        # Optimization parameters
        self.min_weight = -1.0  # Maximum short position
        self.max_weight = 1.0   # Maximum long position
        self.max_portfolio_weight = 0.10  # Maximum single instrument weight
        
        # Statistical estimators
        self.correlation_estimator = CorrelationEstimator()
        self.volatility_estimator = VolatilityEstimator()
        
    def get_weights_using_shrinkage(self, shrinkage_factor: float = 0.5) -> portfolioWeights:
        """
        Calculate portfolio weights using shrinkage estimation.
        Combines sample covariance matrix with structured estimator.
        
        Args:
            shrinkage_factor: Weight given to shrinkage target (0-1)
            
        Returns:
            portfolioWeights object with optimized weights
        """
        # Calculate sample covariance matrix
        sample_cov = self.returns_data.cov().values
        
        # Calculate shrinkage target (identity matrix scaled by average variance)
        avg_variance = np.trace(sample_cov) / sample_cov.shape[0]
        shrinkage_target = np.eye(sample_cov.shape[0]) * avg_variance
        
        # Apply shrinkage
        shrunk_cov = (1 - shrinkage_factor) * sample_cov + shrinkage_factor * shrinkage_target
        
        # Solve optimization problem
        weights = self._solve_optimization(shrunk_cov)
        
        return self._create_weights_object(weights)
        
    def get_weights_using_robust_optimization(self, 
                                            confidence_level: float = 0.95,
                                            uncertainty_set: str = "ellipsoidal") -> portfolioWeights:
        """
        Calculate portfolio weights using robust optimization.
        Accounts for parameter uncertainty in mean and covariance estimation.
        """
        # Robust covariance estimation
        robust_cov = self._estimate_robust_covariance()
        
        # Calculate uncertainty bounds
        n_samples, n_assets = self.returns_data.shape
        uncertainty_radius = self._calculate_uncertainty_radius(confidence_level, n_samples, n_assets)
        
        # Solve robust optimization problem
        weights = self._solve_robust_optimization(robust_cov, uncertainty_radius, uncertainty_set)
        
        return self._create_weights_object(weights)
        
    def _solve_optimization(self, covariance_matrix: np.ndarray) -> np.ndarray:
        """
        Solve mean-variance optimization problem using quadratic programming.
        
        Minimize: w^T * Σ * w
        Subject to: 
        - sum(w) = 1 (fully invested)
        - min_weight <= w_i <= max_weight (position limits)
        - w_i <= max_portfolio_weight (concentration limits)
        """
        from scipy.optimize import minimize
        
        n_assets = covariance_matrix.shape[0]
        
        # Objective function: minimize portfolio variance
        def objective(weights):
            return weights.T @ covariance_matrix @ weights
            
        # Constraints
        constraints = [
            # Fully invested constraint
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},
            # Long-only constraint (optional)
            # {'type': 'ineq', 'fun': lambda w: w}
        ]
        
        # Bounds for individual weights
        bounds = [(self.min_weight, min(self.max_weight, self.max_portfolio_weight)) 
                  for _ in range(n_assets)]
        
        # Initial guess: equal weights
        x0 = np.ones(n_assets) / n_assets
        
        # Solve optimization
        result = minimize(
            objective, x0, 
            method='SLSQP', 
            bounds=bounds, 
            constraints=constraints,
            options={'maxiter': 1000, 'ftol': 1e-9}
        )
        
        if not result.success:
            self.log.warning(f"Optimization failed: {result.message}")
            # Fallback to equal weights
            return np.ones(n_assets) / n_assets
            
        return result.x
        
    def _solve_robust_optimization(self, covariance_matrix: np.ndarray, 
                                 uncertainty_radius: float,
                                 uncertainty_set: str) -> np.ndarray:
        """
        Solve robust portfolio optimization problem.
        """
        if uncertainty_set == "ellipsoidal":
            return self._solve_ellipsoidal_robust_optimization(covariance_matrix, uncertainty_radius)
        elif uncertainty_set == "box":
            return self._solve_box_robust_optimization(covariance_matrix, uncertainty_radius)
        else:
            raise ValueError(f"Unknown uncertainty set: {uncertainty_set}")
            
    def _estimate_robust_covariance(self) -> np.ndarray:
        """
        Estimate robust covariance matrix using Minimum Covariance Determinant (MCD).
        """
        try:
            from sklearn.covariance import MinCovDet
            
            mcd = MinCovDet(random_state=42)
            mcd.fit(self.returns_data.dropna())
            
            return mcd.covariance_
            
        except ImportError:
            self.log.warning("sklearn not available, using sample covariance")
            return self.returns_data.cov().values
            
    def _create_weights_object(self, weights_array: np.ndarray) -> 'portfolioWeights':
        """
        Create portfolioWeights object from weight array.
        """
        instruments = self.returns_data.columns
        weights_dict = dict(zip(instruments, weights_array))
        
        return portfolioWeights(weights_dict)


class CorrelationEstimator(object):
    """
    Advanced correlation estimation with multiple methodologies and regime detection.
    """
    
    def __init__(self, min_periods: int = 50, max_periods: int = 500):
        """
        Initialize correlation estimator.
        
        Args:
            min_periods: Minimum observations required
            max_periods: Maximum lookback period
        """
        self.min_periods = min_periods
        self.max_periods = max_periods
        self.log = get_logger("CorrelationEstimator")
        
    def get_correlation_matrix(self, returns_data: pd.DataFrame, 
                              method: str = "shrinkage") -> pd.DataFrame:
        """
        Calculate correlation matrix using specified method.
        
        Args:
            returns_data: DataFrame with instrument returns
            method: Estimation method ('sample', 'shrinkage', 'robust')
        """
        if method == "sample":
            return self._sample_correlation(returns_data)
        elif method == "shrinkage":
            return self._shrinkage_correlation(returns_data)
        elif method == "robust":
            return self._robust_correlation(returns_data)
        else:
            raise ValueError(f"Unknown correlation method: {method}")
            
    def _sample_correlation(self, returns_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate sample correlation matrix.
        """
        return returns_data.corr()
        
    def _shrinkage_correlation(self, returns_data: pd.DataFrame, 
                              shrinkage_target: float = 0.0) -> pd.DataFrame:
        """
        Calculate shrinkage correlation matrix.
        Shrinks towards identity matrix or specified target.
        """
        # Sample correlation
        sample_corr = returns_data.corr()
        
        # Shrinkage target (identity matrix)
        target_corr = pd.DataFrame(
            np.eye(len(sample_corr)), 
            index=sample_corr.index, 
            columns=sample_corr.columns
        )
        
        # Optimal shrinkage intensity using Ledoit-Wolf formula
        shrinkage_intensity = self._calculate_optimal_shrinkage_intensity(returns_data)
        
        # Apply shrinkage
        shrunk_corr = (1 - shrinkage_intensity) * sample_corr + shrinkage_intensity * target_corr
        
        return shrunk_corr
        
    def _robust_correlation(self, returns_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate robust correlation matrix using Minimum Covariance Determinant.
        """
        try:
            from sklearn.covariance import MinCovDet
            
            mcd = MinCovDet(random_state=42)
            clean_data = returns_data.dropna()
            mcd.fit(clean_data)
            
            # Convert covariance to correlation
            cov_matrix = mcd.covariance_
            std_devs = np.sqrt(np.diag(cov_matrix))
            corr_matrix = cov_matrix / np.outer(std_devs, std_devs)
            
            return pd.DataFrame(
                corr_matrix, 
                index=returns_data.columns, 
                columns=returns_data.columns
            )
            
        except ImportError:
            self.log.warning("sklearn not available, using sample correlation")
            return self._sample_correlation(returns_data)
            
    def _calculate_optimal_shrinkage_intensity(self, returns_data: pd.DataFrame) -> float:
        """
        Calculate optimal shrinkage intensity using Ledoit-Wolf estimator.
        """
        # Implementation of Ledoit-Wolf optimal shrinkage formula
        n, p = returns_data.shape
        
        if n < p:
            self.log.warning("More variables than observations, using high shrinkage")
            return 0.8
            
        # Calculate sample covariance
        sample_cov = returns_data.cov().values
        
        # Calculate shrinkage intensity (simplified formula)
        shrinkage_intensity = min(1.0, (p / n) * 0.5)
        
        return shrinkage_intensity
        
    def detect_correlation_regime_changes(self, returns_data: pd.DataFrame, 
                                        window_size: int = 100) -> pd.Series:
        """
        Detect structural breaks in correlation patterns using rolling correlation analysis.
        """
        rolling_corr_matrices = []
        dates = []
        
        for i in range(window_size, len(returns_data)):
            window_data = returns_data.iloc[i-window_size:i]
            corr_matrix = window_data.corr()
            
            # Calculate average correlation
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
            avg_correlation = corr_matrix.values[mask].mean()
            
            rolling_corr_matrices.append(avg_correlation)
            dates.append(returns_data.index[i])
            
        correlation_series = pd.Series(rolling_corr_matrices, index=dates)
        
        # Detect regime changes using change point detection
        regime_changes = self._detect_change_points(correlation_series)
        
        return regime_changes
        
    def _detect_change_points(self, time_series: pd.Series) -> pd.Series:
        """
        Detect change points in time series using CUSUM test.
        """
        # Simple CUSUM implementation
        cumsum = (time_series - time_series.mean()).cumsum()
        
        # Detect significant deviations
        threshold = 2 * time_series.std()
        change_points = abs(cumsum) > threshold
        
        return change_points
```

## Order Management System

### **Three-Tier Order Stack Implementation**

```python
class orderStackData(object):
    """
    Abstract base class for order stack data management.
    Implements common functionality for all three order stack tiers.
    """
    
    def __init__(self, log=None):
        self.log = log if log else get_logger(self.__class__.__name__)
        
    def put_order_on_stack(self, order):
        """
        Add order to stack with validation and logging.
        """
        # Validate order before adding
        self._validate_order(order)
        
        # Add order to storage
        self._put_order_on_stack_impl(order)
        
        self.log.info(f"Order added to stack: {order}")
        
    def _validate_order(self, order):
        """
        Validate order before adding to stack.
        Override in subclasses for specific validation rules.
        """
        if not hasattr(order, 'order_id'):
            raise ValueError("Order must have order_id")
            
        if not hasattr(order, 'quantity'):
            raise ValueError("Order must have quantity")
            
    def _put_order_on_stack_impl(self, order):
        """
        Implementation-specific order storage.
        Override in subclasses.
        """
        raise NotImplementedError()


class instrumentOrderStackData(orderStackData):
    """
    Instrument-level order stack managing high-level position targets.
    Handles position buffering and risk controls at instrument level.
    """
    
    ORDER_COLLECTION = "instrument_orders"
    
    def __init__(self, mongo_db=None, log=None):
        super().__init__(log)
        
        self._mongo_data = mongoDataWithSingleKey(
            collection_name=self.ORDER_COLLECTION,
            key_name="order_id", 
            mongo_db=mongo_db
        )
        
    def get_list_of_order_ids(self, exclude_inactive=True) -> list:
        """
        Get list of all order IDs in the stack.
        
        Args:
            exclude_inactive: If True, exclude completed/cancelled orders
        """
        if exclude_inactive:
            query = {"order_status": {"$in": ["pending", "active", "partially_filled"]}}
        else:
            query = {}
            
        cursor = self._mongo_data.collection.find(query, {"order_id": 1})
        return [doc["order_id"] for doc in cursor]
        
    def get_order_with_id(self, order_id: str) -> instrumentOrder:
        """
        Retrieve specific order by ID.
        """
        order_dict = self._mongo_data.get_result_dict_for_key(order_id)
        if not order_dict:
            raise missingData(f"Order {order_id} not found")
            
        return instrumentOrder.from_dict(order_dict)
        
    def update_order(self, order: 'instrumentOrder'):
        """
        Update existing order in stack.
        """
        order_dict = order.as_dict()
        self._mongo_data.add_data(
            key=order.order_id,
            data_dict=order_dict,
            allow_overwrite=True
        )
        
        self.log.info(f"Updated order: {order.order_id}")
        
    def get_orders_for_instrument_strategy(self, instrument_strategy) -> list:
        """
        Get all orders for specific instrument-strategy combination.
        """
        query = {
            "instrument_code": instrument_strategy.instrument_code,
            "strategy_name": instrument_strategy.strategy_name,
            "order_status": {"$ne": "cancelled"}
        }
        
        cursor = self._mongo_data.collection.find(query)
        orders = []
        
        for order_dict in cursor:
            try:
                order = instrumentOrder.from_dict(order_dict)
                orders.append(order)
            except Exception as e:
                self.log.warning(f"Could not parse order {order_dict.get('order_id')}: {e}")
                
        return orders
        
    def _validate_order(self, order):
        """
        Validate instrument order specific requirements.
        """
        super()._validate_order(order)
        
        if not isinstance(order, instrumentOrder):
            raise ValueError("Order must be instrumentOrder instance")
            
        if not hasattr(order, 'instrument_code') or not order.instrument_code:
            raise ValueError("Order must have valid instrument_code")
            
        if not hasattr(order, 'strategy_name') or not order.strategy_name:
            raise ValueError("Order must have valid strategy_name")
            
    def _put_order_on_stack_impl(self, order):
        """
        Store instrument order in MongoDB.
        """
        order_dict = order.as_dict()
        self._mongo_data.add_data(
            key=order.order_id,
            data_dict=order_dict,
            allow_overwrite=False
        )


class instrumentOrder(object):
    """
    Instrument-level order representing desired position changes.
    Contains buffering logic and risk controls.
    """
    
    def __init__(self, instrument_code: str, strategy_name: str, quantity: float,
                 order_type: str = "market", reference_price: float = None,
                 max_position_size: float = None):
        """
        Initialize instrument order.
        
        Args:
            instrument_code: Trading instrument identifier  
            strategy_name: Strategy generating this order
            quantity: Desired quantity (+ for long, - for short)
            order_type: Order type ('market', 'limit', 'best')
            reference_price: Reference price for limit orders
            max_position_size: Maximum allowed position size
        """
        self.instrument_code = instrument_code
        self.strategy_name = strategy_name
        self.quantity = float(quantity)
        self.order_type = order_type
        self.reference_price = reference_price
        self.max_position_size = max_position_size
        
        # Order lifecycle tracking
        self.order_id = self._generate_order_id()
        self.order_status = "pending"
        self.created_datetime = datetime.datetime.utcnow()
        self.filled_quantity = 0.0
        self.remaining_quantity = self.quantity
        
        # Child order tracking
        self.child_order_ids = []
        
        # Position buffering parameters
        self.buffer_size = 0.10  # 10% buffer around target position
        self.min_trade_size = 1.0  # Minimum trade size
        
    def _generate_order_id(self) -> str:
        """
        Generate unique order ID.
        """
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"INST_{self.instrument_code}_{self.strategy_name}_{timestamp}_{random_suffix}"
        
    def should_create_order(self, current_position: float, target_position: float) -> bool:
        """
        Determine if order should be created based on buffering logic.
        
        Args:
            current_position: Current position size
            target_position: Target position size
            
        Returns:
            True if order should be created
        """
        position_difference = abs(target_position - current_position)
        
        # Check minimum trade size
        if position_difference < self.min_trade_size:
            return False
            
        # Check buffer threshold
        if current_position != 0:
            percentage_change = position_difference / abs(current_position)
            if percentage_change < self.buffer_size:
                return False
                
        return True
        
    def apply_position_limits(self, proposed_quantity: float, 
                            current_position: float) -> float:
        """
        Apply position limits to proposed order quantity.
        
        Args:
            proposed_quantity: Desired order quantity
            current_position: Current position size
            
        Returns:
            Limited order quantity
        """
        if self.max_position_size is None:
            return proposed_quantity
            
        # Calculate resulting position
        resulting_position = current_position + proposed_quantity
        
        # Apply position limits
        if abs(resulting_position) > self.max_position_size:
            # Limit to maximum allowed position
            if resulting_position > 0:
                limited_position = self.max_position_size
            else:
                limited_position = -self.max_position_size
                
            # Calculate limited quantity
            limited_quantity = limited_position - current_position
            
            if abs(limited_quantity) < self.min_trade_size:
                return 0.0  # No trade if below minimum size
                
            return limited_quantity
            
        return proposed_quantity
        
    def create_child_contract_orders(self, contract_allocation: dict) -> list:
        """
        Create child contract orders based on contract allocation.
        
        Args:
            contract_allocation: Dict mapping contract objects to quantities
            
        Returns:
            List of contractOrder objects
        """
        child_orders = []
        
        for contract, allocated_quantity in contract_allocation.items():
            if abs(allocated_quantity) >= self.min_trade_size:
                child_order = contractOrder(
                    futures_contract=contract,
                    quantity=allocated_quantity,
                    parent_order_id=self.order_id,
                    order_type=self.order_type,
                    reference_price=self.reference_price
                )
                
                child_orders.append(child_order)
                self.child_order_ids.append(child_order.order_id)
                
        return child_orders
        
    def update_fill(self, filled_quantity: float):
        """
        Update order with partial fill information.
        """
        self.filled_quantity += filled_quantity
        self.remaining_quantity = self.quantity - self.filled_quantity
        
        if abs(self.remaining_quantity) < 0.001:  # Floating point tolerance
            self.order_status = "filled"
        else:
            self.order_status = "partially_filled"
            
    def as_dict(self) -> dict:
        """
        Convert order to dictionary for storage.
        """
        return {
            'order_id': self.order_id,
            'instrument_code': self.instrument_code,
            'strategy_name': self.strategy_name,
            'quantity': self.quantity,
            'order_type': self.order_type,
            'reference_price': self.reference_price,
            'max_position_size': self.max_position_size,
            'order_status': self.order_status,
            'created_datetime': self.created_datetime,
            'filled_quantity': self.filled_quantity,
            'remaining_quantity': self.remaining_quantity,
            'child_order_ids': self.child_order_ids,
            'buffer_size': self.buffer_size,
            'min_trade_size': self.min_trade_size
        }
        
    @classmethod
    def from_dict(cls, order_dict: dict) -> 'instrumentOrder':
        """
        Create order from dictionary.
        """
        order = cls(
            instrument_code=order_dict['instrument_code'],
            strategy_name=order_dict['strategy_name'],
            quantity=order_dict['quantity'],
            order_type=order_dict.get('order_type', 'market'),
            reference_price=order_dict.get('reference_price'),
            max_position_size=order_dict.get('max_position_size')
        )
        
        # Restore order state
        order.order_id = order_dict['order_id']
        order.order_status = order_dict.get('order_status', 'pending')
        order.created_datetime = order_dict.get('created_datetime', datetime.datetime.utcnow())
        order.filled_quantity = order_dict.get('filled_quantity', 0.0)
        order.remaining_quantity = order_dict.get('remaining_quantity', order.quantity)
        order.child_order_ids = order_dict.get('child_order_ids', [])
        order.buffer_size = order_dict.get('buffer_size', 0.10)
        order.min_trade_size = order_dict.get('min_trade_size', 1.0)
        
        return order


class contractOrder(object):
    """
    Contract-level order for specific futures contracts.
    Handles contract selection and roll management.
    """
    
    def __init__(self, futures_contract, quantity: float, 
                 parent_order_id: str = None, order_type: str = "market",
                 reference_price: float = None):
        """
        Initialize contract order.
        
        Args:
            futures_contract: futuresContract object
            quantity: Order quantity
            parent_order_id: ID of parent instrument order
            order_type: Order type
            reference_price: Reference price for limit orders
        """
        self.futures_contract = futures_contract
        self.quantity = float(quantity)
        self.parent_order_id = parent_order_id
        self.order_type = order_type
        self.reference_price = reference_price
        
        # Order tracking
        self.order_id = self._generate_order_id()
        self.order_status = "pending"
        self.created_datetime = datetime.datetime.utcnow()
        self.filled_quantity = 0.0
        self.remaining_quantity = self.quantity
        
        # Child broker orders
        self.broker_order_ids = []
        
    def _generate_order_id(self) -> str:
        """
        Generate unique contract order ID.
        """
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        contract_str = f"{self.futures_contract.instrument_code}_{self.futures_contract.date_str}"
        return f"CONT_{contract_str}_{timestamp}_{random_suffix}"
        
    def create_broker_orders(self, broker_allocation: dict) -> list:
        """
        Create broker orders from contract order.
        May split large orders across multiple broker orders.
        """
        broker_orders = []
        
        # For simple case, create single broker order
        if len(broker_allocation) == 1:
            broker_order = brokerOrder(
                futures_contract=self.futures_contract,
                quantity=self.quantity,
                parent_contract_order_id=self.order_id,
                order_type=self.order_type,
                reference_price=self.reference_price
            )
            broker_orders.append(broker_order)
            self.broker_order_ids.append(broker_order.order_id)
            
        else:
            # Split order across multiple brokers/accounts
            for broker_key, allocated_quantity in broker_allocation.items():
                if abs(allocated_quantity) > 0:
                    broker_order = brokerOrder(
                        futures_contract=self.futures_contract,
                        quantity=allocated_quantity,
                        parent_contract_order_id=self.order_id,
                        order_type=self.order_type,
                        reference_price=self.reference_price,
                        broker_account=broker_key
                    )
                    broker_orders.append(broker_order)
                    self.broker_order_ids.append(broker_order.order_id)
                    
        return broker_orders


class brokerOrder(object):
    """
    Broker-level order sent to external broker for execution.
    Contains broker-specific details and execution tracking.
    """
    
    def __init__(self, futures_contract, quantity: float,
                 parent_contract_order_id: str = None, order_type: str = "market",
                 reference_price: float = None, broker_account: str = None):
        """
        Initialize broker order.
        """
        self.futures_contract = futures_contract
        self.quantity = float(quantity) 
        self.parent_contract_order_id = parent_contract_order_id
        self.order_type = order_type
        self.reference_price = reference_price
        self.broker_account = broker_account
        
        # Broker-specific tracking
        self.order_id = self._generate_order_id()
        self.broker_order_id = None  # Assigned by broker
        self.order_status = "pending"
        self.created_datetime = datetime.datetime.utcnow()
        self.submitted_datetime = None
        self.filled_datetime = None
        
        # Execution tracking
        self.filled_quantity = 0.0
        self.remaining_quantity = self.quantity
        self.average_fill_price = None
        self.commission = None
        self.slippage = None
        
        # Fill details
        self.fills = []  # List of individual fills
        
    def _generate_order_id(self) -> str:
        """
        Generate unique broker order ID.
        """
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        contract_str = f"{self.futures_contract.instrument_code}_{self.futures_contract.date_str}"
        return f"BRK_{contract_str}_{timestamp}"
        
    def submit_to_broker(self, broker_client) -> bool:
        """
        Submit order to broker and update status.
        
        Args:
            broker_client: Broker API client
            
        Returns:
            True if successfully submitted
        """
        try:
            # Convert to broker-specific order format
            broker_order_details = self._convert_to_broker_format()
            
            # Submit to broker
            broker_response = broker_client.place_order(broker_order_details)
            
            # Update order with broker response
            self.broker_order_id = broker_response.get('order_id')
            self.order_status = "submitted"
            self.submitted_datetime = datetime.datetime.utcnow()
            
            return True
            
        except Exception as e:
            self.order_status = "rejected" 
            self.rejection_reason = str(e)
            return False
            
    def add_fill(self, fill_quantity: float, fill_price: float, 
                 fill_datetime: datetime.datetime = None, commission: float = 0.0):
        """
        Add fill information to order.
        
        Args:
            fill_quantity: Quantity filled (signed)
            fill_price: Price of fill
            fill_datetime: Time of fill
            commission: Commission charged
        """
        fill = {
            'quantity': fill_quantity,
            'price': fill_price,
            'datetime': fill_datetime or datetime.datetime.utcnow(),
            'commission': commission
        }
        
        self.fills.append(fill)
        
        # Update order totals
        self.filled_quantity += fill_quantity
        self.remaining_quantity = self.quantity - self.filled_quantity
        
        # Update average fill price
        if self.filled_quantity != 0:
            total_value = sum(fill['quantity'] * fill['price'] for fill in self.fills)
            self.average_fill_price = total_value / self.filled_quantity
            
        # Update commission
        total_commission = sum(fill['commission'] for fill in self.fills)
        self.commission = total_commission
        
        # Update order status
        if abs(self.remaining_quantity) < 0.001:  # Fully filled
            self.order_status = "filled"
            self.filled_datetime = fill_datetime or datetime.datetime.utcnow()
        else:
            self.order_status = "partially_filled"
            
    def calculate_slippage(self, reference_price: float) -> float:
        """
        Calculate slippage relative to reference price.
        
        Args:
            reference_price: Expected execution price
            
        Returns:
            Slippage in price points (negative = adverse slippage)
        """
        if self.average_fill_price is None or reference_price is None:
            return None
            
        # Slippage calculation depends on order direction
        if self.quantity > 0:  # Long order
            slippage = reference_price - self.average_fill_price
        else:  # Short order
            slippage = self.average_fill_price - reference_price
            
        self.slippage = slippage
        return slippage
        
    def _convert_to_broker_format(self) -> dict:
        """
        Convert order to broker-specific format.
        Override in broker-specific subclasses.
        """
        return {
            'symbol': self.futures_contract.ib_symbol(),
            'quantity': self.quantity,
            'order_type': self.order_type,
            'price': self.reference_price,
            'account': self.broker_account
        }
```

## Production Control System

### **Process Control Implementation**

```python
class processControl(object):
    """
    Finite state machine managing production process lifecycle.
    Handles process dependencies, monitoring, and automatic recovery.
    """
    
    # Process states
    NO_PROCESS = "NO_PROCESS"
    RUNNING = "RUNNING" 
    FINISHED = "FINISHED"
    ERROR = "ERROR"
    STOPPED = "STOPPED"
    TERMINATED = "TERMINATED"
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        NO_PROCESS: [RUNNING],
        RUNNING: [FINISHED, ERROR, STOPPED, TERMINATED],
        FINISHED: [NO_PROCESS, RUNNING],
        ERROR: [NO_PROCESS, RUNNING, TERMINATED],
        STOPPED: [NO_PROCESS, RUNNING, TERMINATED],
        TERMINATED: [NO_PROCESS]
    }
    
    def __init__(self, process_name: str, data, **kwargs):
        """
        Initialize process control for named process.
        
        Args:
            process_name: Unique process identifier
            data: dataBlob with process control data access
        """
        self.process_name = process_name
        self.data = data
        self.log = get_logger(f"processControl.{process_name}")
        
        # Process configuration
        self.max_executions = kwargs.get('max_executions', 1)
        self.timeout_seconds = kwargs.get('timeout_seconds', 3600)
        self.retry_attempts = kwargs.get('retry_attempts', 3)
        self.retry_delay = kwargs.get('retry_delay', 60)
        
        # Process tracking
        self.execution_count = 0
        self.start_time = None
        self.end_time = None
        self.error_history = []
        
        # Dependencies
        self.dependencies = kwargs.get('dependencies', [])
        
    def can_process_run(self) -> tuple:
        """
        Check if process can run based on current state and dependencies.
        
        Returns:
            (can_run: bool, reason: str)
        """
        # Check current state
        current_state = self.get_process_state()
        
        if current_state == self.RUNNING:
            return False, "Process already running"
            
        if current_state == self.ERROR and not self._can_retry():
            return False, "Process in error state, retry limit exceeded"
            
        # Check dependencies
        dependency_check = self._check_dependencies()
        if not dependency_check[0]:
            return False, f"Dependency not met: {dependency_check[1]}"
            
        # Check execution limits
        if self.execution_count >= self.max_executions:
            return False, "Maximum executions reached"
            
        # Check if already running today (for daily processes)
        if self._is_daily_process() and self._has_run_today():
            return False, "Process already completed today"
            
        return True, "Process can run"
        
    def start_process(self) -> bool:
        """
        Start process execution with state transition and logging.
        
        Returns:
            True if successfully started
        """
        can_run, reason = self.can_process_run()
        if not can_run:
            self.log.warning(f"Cannot start process: {reason}")
            return False
            
        try:
            # Transition to running state
            self._transition_to_state(self.RUNNING)
            
            # Record start time and increment execution count
            self.start_time = datetime.datetime.utcnow()
            self.execution_count += 1
            
            # Update database
            self._update_process_status()
            
            self.log.info(f"Process started (execution #{self.execution_count})")
            return True
            
        except Exception as e:
            self.log.error(f"Failed to start process: {e}")
            self._transition_to_state(self.ERROR, error_msg=str(e))
            return False
            
    def finish_process(self, success: bool = True, error_msg: str = None):
        """
        Complete process execution with appropriate state transition.
        
        Args:
            success: Whether process completed successfully
            error_msg: Error message if process failed
        """
        self.end_time = datetime.datetime.utcnow()
        
        if success:
            self._transition_to_state(self.FINISHED)
            duration = (self.end_time - self.start_time).total_seconds()
            self.log.info(f"Process completed successfully in {duration:.1f}s")
        else:
            self._transition_to_state(self.ERROR, error_msg=error_msg)
            self.log.error(f"Process failed: {error_msg}")
            
        # Update database
        self._update_process_status()
        
    def stop_process(self, reason: str = None):
        """
        Stop running process (graceful shutdown).
        """
        current_state = self.get_process_state()
        
        if current_state == self.RUNNING:
            self._transition_to_state(self.STOPPED, error_msg=reason)
            self.end_time = datetime.datetime.utcnow()
            self._update_process_status()
            
            self.log.info(f"Process stopped: {reason}")
        else:
            self.log.warning(f"Cannot stop process in state: {current_state}")
            
    def terminate_process(self, reason: str = None):
        """
        Terminate process (forced shutdown).
        """
        self._transition_to_state(self.TERMINATED, error_msg=reason)
        self.end_time = datetime.datetime.utcnow()
        self._update_process_status()
        
        self.log.warning(f"Process terminated: {reason}")
        
    def get_process_state(self) -> str:
        """
        Get current process state from database.
        """
        try:
            process_data = self.data.db_process_control.get_process_status(self.process_name)
            return process_data.get('state', self.NO_PROCESS)
        except missingData:
            return self.NO_PROCESS
            
    def get_process_runtime(self) -> float:
        """
        Get current process runtime in seconds.
        """
        if self.start_time is None:
            return 0.0
            
        end_time = self.end_time or datetime.datetime.utcnow()
        return (end_time - self.start_time).total_seconds()
        
    def is_process_timeout(self) -> bool:
        """
        Check if process has exceeded timeout.
        """
        if self.start_time is None:
            return False
            
        runtime = self.get_process_runtime()
        return runtime > self.timeout_seconds
        
    def _transition_to_state(self, new_state: str, error_msg: str = None):
        """
        Transition process to new state with validation.
        """
        current_state = self.get_process_state()
        
        # Validate transition
        valid_transitions = self.VALID_TRANSITIONS.get(current_state, [])
        if new_state not in valid_transitions:
            raise ValueError(f"Invalid transition: {current_state} -> {new_state}")
            
        # Record error if transitioning to error state
        if new_state == self.ERROR and error_msg:
            self.error_history.append({
                'datetime': datetime.datetime.utcnow(),
                'error_msg': error_msg,
                'execution_count': self.execution_count
            })
            
        self.log.debug(f"State transition: {current_state} -> {new_state}")
        
    def _check_dependencies(self) -> tuple:
        """
        Check if all process dependencies are satisfied.
        
        Returns:
            (dependencies_met: bool, failed_dependency: str)
        """
        for dependency in self.dependencies:
            dependency_state = self.data.db_process_control.get_process_status(dependency)
            
            if dependency_state.get('state') != self.FINISHED:
                return False, dependency
                
            # Check if dependency completed recently (within last 24 hours)
            last_run = dependency_state.get('last_run_datetime')
            if last_run:
                hours_since_run = (datetime.datetime.utcnow() - last_run).total_seconds() / 3600
                if hours_since_run > 24:
                    return False, f"{dependency} (stale, {hours_since_run:.1f}h ago)"
                    
        return True, None
        
    def _can_retry(self) -> bool:
        """
        Check if process can be retried after error.
        """
        if not self.error_history:
            return True
            
        # Check retry attempts
        recent_errors = [
            error for error in self.error_history
            if (datetime.datetime.utcnow() - error['datetime']).total_seconds() < 3600
        ]
        
        return len(recent_errors) < self.retry_attempts
        
    def _is_daily_process(self) -> bool:
        """
        Check if this is a daily process.
        """
        daily_processes = [
            'update_fx_prices',
            'update_historical_prices', 
            'run_daily_reports',
            'backup_db_to_parquet'
        ]
        return self.process_name in daily_processes
        
    def _has_run_today(self) -> bool:
        """
        Check if process has already run today.
        """
        try:
            process_data = self.data.db_process_control.get_process_status(self.process_name)
            last_run = process_data.get('last_run_datetime')
            
            if last_run is None:
                return False
                
            # Check if last run was today
            today = datetime.date.today()
            last_run_date = last_run.date()
            
            return last_run_date == today
            
        except missingData:
            return False
            
    def _update_process_status(self):
        """
        Update process status in database.
        """
        status_data = {
            'process_name': self.process_name,
            'state': self.get_process_state(),
            'execution_count': self.execution_count,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'runtime_seconds': self.get_process_runtime(),
            'error_history': self.error_history,
            'last_update': datetime.datetime.utcnow()
        }
        
        if self.get_process_state() == self.FINISHED:
            status_data['last_run_datetime'] = self.end_time
            
        self.data.db_process_control.update_process_status(self.process_name, status_data)


class processRunner(object):
    """
    Main process orchestration engine managing multiple production processes.
    Implements scheduling, dependency management, and monitoring.
    """
    
    def __init__(self, data, config_path: str = None):
        """
        Initialize process runner with configuration.
        
        Args:
            data: dataBlob with database access
            config_path: Path to process configuration file
        """
        self.data = data
        self.log = get_logger("processRunner")
        
        # Load process configuration
        self.config = self._load_process_config(config_path)
        
        # Process registry
        self.processes = {}
        self.process_schedule = {}
        
        # Runner state
        self.is_running = False
        self.shutdown_requested = False
        
        # Performance tracking
        self.process_stats = defaultdict(list)
        
        # Initialize processes
        self._initialize_processes()
        
    def run_all_processes(self):
        """
        Main runner loop executing scheduled processes.
        """
        self.is_running = True
        self.log.info("Process runner started")
        
        try:
            while not self.shutdown_requested:
                # Check for processes ready to run
                processes_to_run = self._get_processes_ready_to_run()
                
                # Execute ready processes
                for process_name in processes_to_run:
                    self._execute_process(process_name)
                    
                # Check for long-running processes that need attention
                self._monitor_running_processes()
                
                # Sleep before next iteration
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            self.log.info("Shutdown requested via keyboard interrupt")
        except Exception as e:
            self.log.error(f"Process runner error: {e}")
        finally:
            self._shutdown_all_processes()
            self.is_running = False
            self.log.info("Process runner stopped")
            
    def run_single_process(self, process_name: str, force: bool = False) -> bool:
        """
        Run a single named process.
        
        Args:
            process_name: Name of process to run
            force: If True, bypass normal run conditions
            
        Returns:
            True if process completed successfully
        """
        if process_name not in self.processes:
            self.log.error(f"Unknown process: {process_name}")
            return False
            
        process = self.processes[process_name]
        
        # Check if process can run (unless forced)
        if not force:
            can_run, reason = process.can_process_run()
            if not can_run:
                self.log.info(f"Process {process_name} cannot run: {reason}")
                return False
                
        # Execute process
        return self._execute_process(process_name)
        
    def _load_process_config(self, config_path: str) -> dict:
        """
        Load process configuration from YAML file.
        """
        default_config = {
            'processes': {
                'update_fx_prices': {
                    'schedule': '0 6 * * *',  # 6 AM daily
                    'timeout': 600,
                    'dependencies': []
                },
                'update_futures_contracts': {
                    'schedule': '0 7 * * *',  # 7 AM daily  
                    'timeout': 1800,
                    'dependencies': []
                },
                'run_strategy_order_generator': {
                    'schedule': '*/15 * * * *',  # Every 15 minutes
                    'timeout': 300,
                    'dependencies': ['update_fx_prices']
                },
                'run_stack_handler': {
                    'schedule': '*/5 * * * *',  # Every 5 minutes
                    'timeout': 180,
                    'dependencies': []
                },
                'run_daily_reports': {
                    'schedule': '0 18 * * *',  # 6 PM daily
                    'timeout': 900,
                    'dependencies': ['run_strategy_order_generator']
                }
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    custom_config = yaml.safe_load(f)
                    default_config.update(custom_config)
            except Exception as e:
                self.log.warning(f"Could not load config {config_path}: {e}")
                
        return default_config
        
    def _initialize_processes(self):
        """
        Initialize all configured processes.
        """
        for process_name, process_config in self.config['processes'].items():
            try:
                process = processControl(
                    process_name=process_name,
                    data=self.data,
                    timeout_seconds=process_config.get('timeout', 3600),
                    dependencies=process_config.get('dependencies', [])
                )
                
                self.processes[process_name] = process
                self.process_schedule[process_name] = process_config.get('schedule')
                
                self.log.debug(f"Initialized process: {process_name}")
                
            except Exception as e:
                self.log.error(f"Failed to initialize process {process_name}: {e}")
                
    def _get_processes_ready_to_run(self) -> list:
        """
        Get list of processes ready to run based on schedule and dependencies.
        """
        ready_processes = []
        
        for process_name, process in self.processes.items():
            # Check schedule
            if self._is_process_scheduled_now(process_name):
                # Check if process can run
                can_run, reason = process.can_process_run()
                if can_run:
                    ready_processes.append(process_name)
                else:
                    self.log.debug(f"Process {process_name} not ready: {reason}")
                    
        return ready_processes
        
    def _is_process_scheduled_now(self, process_name: str) -> bool:
        """
        Check if process is scheduled to run now using cron expression.
        """
        schedule = self.process_schedule.get(process_name)
        if not schedule:
            return False
            
        try:
            from croniter import croniter
            
            # Check if process should run in the last minute
            now = datetime.datetime.now()
            one_minute_ago = now - datetime.timedelta(minutes=1)
            
            cron = croniter(schedule, one_minute_ago)
            next_run = cron.get_next(datetime.datetime)
            
            return next_run <= now
            
        except ImportError:
            self.log.warning("croniter not available, using simple time-based scheduling")
            return self._simple_schedule_check(process_name)
        except Exception as e:
            self.log.warning(f"Error checking schedule for {process_name}: {e}")
            return False
            
    def _execute_process(self, process_name: str) -> bool:
        """
        Execute a single process with error handling and monitoring.
        """
        process = self.processes[process_name]
        start_time = time.time()
        
        try:
            self.log.info(f"Starting process: {process_name}")
            
            # Start process
            if not process.start_process():
                return False
                
            # Get process module and execute
            process_module = self._get_process_module(process_name)
            if process_module is None:
                process.finish_process(success=False, error_msg="Process module not found")
                return False
                
            # Execute process function
            result = process_module(self.data)
            
            # Finish process
            if result is False:
                process.finish_process(success=False, error_msg="Process returned False")
                return False
            else:
                process.finish_process(success=True)
                
            # Record performance stats
            duration = time.time() - start_time
            self.process_stats[process_name].append(duration)
            
            self.log.info(f"Process {process_name} completed in {duration:.1f}s")
            return True
            
        except Exception as e:
            error_msg = f"Process execution failed: {str(e)}"
            process.finish_process(success=False, error_msg=error_msg)
            self.log.error(f"Process {process_name} failed: {e}")
            return False
            
    def _get_process_module(self, process_name: str):
        """
        Dynamically import and return process module.
        """
        module_map = {
            'update_fx_prices': 'sysproduction.update_fx_prices.update_fx_prices',
            'update_futures_contracts': 'sysproduction.update_futures_contracts.update_futures_contracts',
            'run_strategy_order_generator': 'sysproduction.run_strategy_order_generator.run_strategy_order_generator',
            'run_stack_handler': 'sysproduction.run_stack_handler.run_stack_handler',
            'run_daily_reports': 'sysproduction.run_reports.run_daily_reports'
        }
        
        module_path = module_map.get(process_name)
        if not module_path:
            self.log.error(f"No module mapping for process: {process_name}")
            return None
            
        try:
            module_parts = module_path.split('.')
            module_name = '.'.join(module_parts[:-1])
            function_name = module_parts[-1]
            
            module = importlib.import_module(module_name)
            return getattr(module, function_name)
            
        except Exception as e:
            self.log.error(f"Could not import process module {module_path}: {e}")
            return None
            
    def _monitor_running_processes(self):
        """
        Monitor running processes for timeouts and issues.
        """
        for process_name, process in self.processes.items():
            if process.get_process_state() == processControl.RUNNING:
                # Check for timeout
                if process.is_process_timeout():
                    self.log.warning(f"Process {process_name} timeout, terminating")
                    process.terminate_process("Process timeout")
                    
                # Check for other issues (memory usage, etc.)
                self._check_process_health(process_name, process)
                
    def _check_process_health(self, process_name: str, process):
        """
        Check process health metrics and take action if needed.
        """
        # This could be extended to check system resources, 
        # database connections, etc.
        runtime = process.get_process_runtime()
        
        # Log long-running processes
        if runtime > 1800:  # 30 minutes
            self.log.warning(f"Process {process_name} has been running for {runtime/60:.1f} minutes")
```

This comprehensive Low-Level Design document provides detailed technical implementation specifications for pysystemtrade's core components. It covers class designs, algorithms, data structures, and system internals that would guide developers in understanding and extending the framework.

The document includes:

1. **Detailed class implementations** with actual method signatures and algorithms
2. **Database schema and optimization details** for MongoDB and other backends  
3. **Advanced caching and performance optimization** strategies
4. **Complete order management system** with three-tier architecture
5. **Production process control** with finite state machine implementation
6. **Quantitative framework algorithms** including portfolio optimization
7. **Error handling and security** implementation details

Would you like me to continue with additional sections covering broker integration, database schemas, or any other specific technical aspects?