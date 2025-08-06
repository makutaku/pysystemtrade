# Data Architecture Design

Comprehensive data management strategy and implementation for pysystemtrade's multi-backend data architecture.

## Executive Summary

The data architecture for pysystemtrade implements a **polyglot persistence strategy** optimized for systematic trading workloads. The design combines multiple specialized databases and storage systems, each optimized for specific data types and access patterns, unified through a sophisticated abstraction layer.

### **Data Architecture Vision**
*"A high-performance, reliable, and scalable data platform that provides unified access to heterogeneous data sources while optimizing for the specific characteristics of financial time series, operational data, and reference information."*

## Data Classification & Requirements

### **Data Type Taxonomy**

#### **1. Time Series Data (Hot Path - Performance Critical)**
- **Market Prices** - OHLCV data, tick data, adjusted prices
- **Analytics Results** - Volatility estimates, correlation matrices, forecasts
- **Performance Data** - Strategy P&L, attribution, risk metrics

**Characteristics:**
- High volume (millions of records)
- Sequential access patterns
- Append-heavy workloads
- Analytical query requirements
- Long retention periods (10+ years)

**Performance Requirements:**
- Write throughput: 100K+ records/second
- Query latency: <10ms for recent data
- Compression: 80%+ to optimize storage costs
- Analytical performance: Complex aggregations <1 second

#### **2. Operational Data (Transactional - Consistency Critical)**
- **Orders & Executions** - Order lifecycle, fills, trade records
- **Positions** - Real-time position tracking, reconciliation
- **Process Control** - System state, job status, dependencies

**Characteristics:**
- Medium volume (thousands of records)
- Random access patterns
- ACID transaction requirements
- Real-time consistency needs
- Medium retention (2-5 years)

**Performance Requirements:**
- Transaction throughput: 1K+ TPS
- Query latency: <1ms for operational queries
- Consistency: ACID compliance
- Availability: 99.99% uptime

#### **3. Reference Data (Configuration - Accuracy Critical)**
- **Instrument Definitions** - Contract specifications, parameters
- **Configuration** - System settings, strategy parameters
- **Static Data** - Holidays, exchanges, roll calendars

**Characteristics:**
- Low volume (hundreds of records)
- Read-heavy access patterns
- Infrequent updates
- Version control requirements
- Long retention (indefinite)

**Performance Requirements:**
- Query latency: <1ms (cached)
- Consistency: Strong consistency
- Versioning: Full audit trail
- Backup: Multiple redundant copies

### **Data Quality Requirements**

#### **Data Integrity Standards**
- **Completeness** - No missing critical data points
- **Accuracy** - Data matches authoritative sources within tolerance
- **Consistency** - No conflicts between related data elements
- **Timeliness** - Data available within defined SLAs
- **Validity** - Data conforms to business rules and formats

#### **Data Validation Framework**
```python
# Data Quality Validation Pipeline
class DataQualityFramework:
    def validate_price_data(self, price_data: pd.DataFrame):
        validators = [
            PriceRangeValidator(),      # Check for reasonable price ranges
            OHLCConsistencyValidator(), # Validate OHLC relationships
            VolumeValidator(),          # Check volume consistency
            GapDetectionValidator(),    # Identify data gaps
            SpikeDetectionValidator()   # Identify price spikes
        ]
        return self._run_validators(price_data, validators)
```

## Multi-Backend Architecture

### **Data Backend Strategy**

```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Architecture Overview                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Application Layer                                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   dataBlob                              │    │
│  │           (Unified Data Access Layer)                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Data Abstraction Layer                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │    │
│  │  │ Repository  │  │ Adapter     │  │ Factory     │     │    │
│  │  │ Pattern     │  │ Pattern     │  │ Pattern     │     │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                Storage Backends                         │    │
│  │                                                         │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │    │
│  │  │ MongoDB     │  │ Parquet     │  │ CSV Files   │     │    │
│  │  │             │  │ Files       │  │             │     │    │
│  │  │ Operational │  │ Time Series │  │ Reference   │     │    │
│  │  │ Data        │  │ Analytics   │  │ Data        │     │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │    │
│  │                                                         │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │    │
│  │  │ Redis       │  │ PostgreSQL  │  │ Arctic      │     │    │
│  │  │             │  │ (Future)    │  │ (Legacy)    │     │    │
│  │  │ Caching     │  │ Analytics   │  │ Time Series │     │    │
│  │  │ Session     │  │ Reporting   │  │ Storage     │     │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### **Backend Selection Rationale**

#### **MongoDB - Operational Data Store**
**Use Cases:** Orders, positions, process control, audit logs
**Selection Rationale:**
- **ACID Transactions** - Critical for financial data consistency
- **Flexible Schema** - Accommodates evolving order structures
- **High Availability** - Replica sets for 99.99% uptime
- **Rich Querying** - Complex aggregation pipelines for reporting
- **Horizontal Scaling** - Sharding support for growth

**Configuration Strategy:**
```yaml
# MongoDB Production Configuration
mongodb:
  replica_set: "pysystemtrade-rs"
  write_concern: "majority"
  read_concern: "majority" 
  indexes:
    - collection: "orders"
      keys: [{"order_id": 1}, {"instrument_code": 1}, {"datetime": 1}]
    - collection: "positions" 
      keys: [{"instrument_code": 1}, {"strategy_name": 1}, {"datetime": 1}]
```

#### **Parquet - Time Series Analytics Store**
**Use Cases:** Price data, analytics results, performance metrics
**Selection Rationale:**
- **Columnar Storage** - Optimal for analytical workloads
- **Compression** - 80%+ compression ratios reduce storage costs
- **Schema Evolution** - Support for adding new columns over time
- **Ecosystem Integration** - Native Pandas/Arrow support
- **Query Performance** - Vectorized operations for fast analytics

**Storage Organization:**
```
parquet_data/
├── prices/
│   ├── daily/
│   │   └── year=2024/month=01/instrument=SOFR/data.parquet
│   └── intraday/
│       └── year=2024/month=01/day=15/instrument=SOFR/data.parquet
├── analytics/
│   ├── volatility/
│   └── correlations/
└── performance/
    ├── strategy_pnl/
    └── attribution/
```

#### **Redis - Caching & Session Store**
**Use Cases:** Query result caching, session management, real-time metrics
**Selection Rationale:**
- **In-Memory Performance** - Sub-millisecond access times
- **Data Structures** - Rich data types for complex caching scenarios
- **Pub/Sub Messaging** - Real-time event distribution
- **Persistence Options** - RDB snapshots and AOF logging
- **High Availability** - Redis Cluster and Sentinel support

**Cache Strategy:**
```python
# Redis Caching Configuration
cache_config = {
    'price_data': {'ttl': 300, 'strategy': 'write_through'},
    'analytics_results': {'ttl': 3600, 'strategy': 'lazy_loading'},
    'reference_data': {'ttl': 86400, 'strategy': 'write_behind'}
}
```

#### **CSV Files - Reference Data Store**
**Use Cases:** Configuration, instrument definitions, static data
**Selection Rationale:**
- **Version Control Friendly** - Git-compatible for change tracking
- **Human Readable** - Easy manual inspection and editing
- **Universal Format** - Compatible with all tools and systems
- **Simple Deployment** - No database setup required
- **Backup Simplicity** - File system level backup and restore

## Data Access Patterns

### **dataBlob - Unified Data Access Layer**

The `dataBlob` class provides a **unified interface** to all data backends, implementing the **Repository pattern** with automatic backend selection and failover capabilities.

#### **Architecture Benefits**
- **Abstraction** - Applications unaware of underlying storage
- **Flexibility** - Easy backend switching without code changes
- **Consistency** - Uniform API across all data types
- **Performance** - Backend-specific optimizations hidden from clients
- **Resilience** - Automatic failover and error handling

#### **Implementation Pattern**
```python
class dataBlob:
    """
    Unified data access orchestrator with automatic backend resolution
    """
    def __init__(self):
        self._initialize_backends()
        self._setup_connection_pooling()
        self._configure_caching()
    
    def add_class_list(self, data_classes: List[Type]):
        """
        Register data source classes with automatic naming resolution
        mongoFuturesContractData -> db_futures_contract
        """
        for data_class in data_classes:
            backend_type = self._determine_backend_type(data_class)
            attr_name = self._generate_attribute_name(data_class)
            instance = self._initialize_backend(data_class, backend_type)
            setattr(self, attr_name, instance)
```

### **Query Optimization Strategy**

#### **Hot Path Optimization**
Critical queries are optimized for sub-millisecond response times:

```python
# Optimized price data retrieval
class MongoOptimizedQueries:
    def get_latest_prices(self, instruments: List[str], limit: int = 1000):
        """
        Optimized query using compound indexes and projection
        """
        pipeline = [
            {'$match': {
                'instrument_code': {'$in': instruments},
                'datetime': {'$gte': self._get_start_date()}
            }},
            {'$sort': {'datetime': -1}},
            {'$limit': limit},
            {'$project': {'_id': 0, 'CLOSE': 1, 'datetime': 1, 'instrument_code': 1}}
        ]
        return list(self.collection.aggregate(pipeline, allowDiskUse=False))
```

#### **Cold Path Optimization**
Historical queries are optimized for throughput over latency:

```python
# Batch processing for historical data
class ParquetBatchProcessor:
    def get_historical_data_batch(self, instruments: List[str], 
                                date_range: Tuple[datetime, datetime]):
        """
        Parallel processing of multiple Parquet files
        """
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for instrument in instruments:
                future = executor.submit(
                    self._load_parquet_data, instrument, date_range
                )
                futures.append(future)
            
            results = {}
            for instrument, future in zip(instruments, futures):
                results[instrument] = future.result()
            
            return results
```

## Data Pipeline Architecture

### **ETL Pipeline Design**

```
┌─────────────────────────────────────────────────────────────────┐
│                      Data Pipeline Overview                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  External Sources                 Internal Processing           │
│  ┌─────────────┐                ┌─────────────┐                 │
│  │ Interactive │─────────────────│ Raw Data    │                 │
│  │ Brokers     │                │ Ingestion   │                 │
│  └─────────────┘                └─────────────┘                 │
│                                        │                        │
│  ┌─────────────┐                ┌─────────────┐                 │
│  │ Market Data │─────────────────│ Data        │                 │
│  │ Vendors     │                │ Validation  │                 │
│  └─────────────┘                └─────────────┘                 │
│                                        │                        │
│  ┌─────────────┐                ┌─────────────┐                 │
│  │ Reference   │─────────────────│ Data        │                 │
│  │ Data APIs   │                │ Transform   │                 │
│  └─────────────┘                └─────────────┘                 │
│                                        │                        │
│                                 ┌─────────────┐                 │
│                                 │ Data        │                 │
│                                 │ Storage     │                 │
│                                 └─────────────┘                 │
│                                        │                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Storage Layer                              │    │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │    │
│  │ │ MongoDB     │ │ Parquet     │ │ Redis Cache │        │    │
│  │ │ (Live)      │ │ (Archive)   │ │ (Hot)       │        │    │
│  │ └─────────────┘ └─────────────┘ └─────────────┘        │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### **Real-time Data Ingestion**

#### **Market Data Pipeline**
```python
class MarketDataPipeline:
    def __init__(self, data_blob):
        self.data_blob = data_blob
        self.validators = [
            PriceRangeValidator(),
            SpikeDetectionValidator(), 
            TimestampValidator()
        ]
        
    async def process_market_data(self, market_data_event):
        """
        Real-time market data processing pipeline
        """
        try:
            # 1. Validate incoming data
            validated_data = self._validate_data(market_data_event)
            
            # 2. Apply transformations
            transformed_data = self._transform_data(validated_data)
            
            # 3. Store in hot storage (Redis)
            await self._store_hot_data(transformed_data)
            
            # 4. Queue for cold storage (MongoDB/Parquet)
            await self._queue_for_persistence(transformed_data)
            
            # 5. Trigger downstream processes
            await self._trigger_analytics_update(transformed_data)
            
        except ValidationError as e:
            self._handle_validation_error(e, market_data_event)
        except Exception as e:
            self._handle_processing_error(e, market_data_event)
```

### **Batch Processing Architecture**

#### **End-of-Day Processing**
```python
class BatchProcessor:
    def run_end_of_day_processing(self):
        """
        Comprehensive end-of-day data processing
        """
        processing_steps = [
            self._reconcile_positions,
            self._calculate_daily_pnl,
            self._update_analytics_data,
            self._archive_to_parquet,
            self._generate_reports,
            self._backup_critical_data
        ]
        
        for step in processing_steps:
            try:
                step_result = step()
                self._log_step_completion(step.__name__, step_result)
            except Exception as e:
                self._handle_step_error(step.__name__, e)
                if self._is_critical_step(step):
                    raise
```

## Data Consistency & Integrity

### **ACID Compliance Strategy**

#### **Transaction Boundaries**
```python
class TransactionManager:
    def execute_trade_transaction(self, trade_details):
        """
        Atomic execution of multi-step trade operations
        """
        with self.mongodb_client.start_session() as session:
            with session.start_transaction():
                try:
                    # 1. Update order status
                    self._update_order_status(trade_details.order_id, 
                                            "filled", session)
                    
                    # 2. Update position
                    self._update_position(trade_details.instrument_code,
                                        trade_details.quantity, session)
                    
                    # 3. Record trade
                    self._record_trade(trade_details, session)
                    
                    # 4. Update P&L
                    self._update_pnl(trade_details, session)
                    
                    # Transaction commits automatically
                    
                except Exception:
                    # Transaction rolls back automatically
                    raise
```

### **Data Validation Framework**

#### **Multi-Layer Validation**
```python
class DataValidationPipeline:
    def __init__(self):
        self.validators = {
            'input': [SchemaValidator(), BusinessRuleValidator()],
            'processing': [ConsistencyValidator(), RangeValidator()],
            'output': [IntegrityValidator(), CompletenessValidator()]
        }
    
    def validate_data(self, data, validation_level='input'):
        """
        Execute validation pipeline for specified level
        """
        validators = self.validators[validation_level]
        validation_results = []
        
        for validator in validators:
            result = validator.validate(data)
            validation_results.append(result)
            
            if result.is_critical_failure():
                raise ValidationError(f"Critical validation failure: {result}")
                
        return ValidationSummary(validation_results)
```

## Performance Optimization

### **Caching Strategy**

#### **Multi-Level Cache Architecture**
```
┌─────────────────────────────────────────────────────────────────┐
│                     Caching Architecture                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  L1 Cache - Application Memory                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Python Dict Cache - Hot Data (< 1MB)                   │    │
│  │ TTL: 30 seconds | Hit Rate: 95%                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│  L2 Cache - Redis Distributed                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Redis Cache - Warm Data (< 100MB)                      │    │
│  │ TTL: 5 minutes | Hit Rate: 85%                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│  L3 Storage - Database                                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ MongoDB/Parquet - Cold Data (Unlimited)                │    │
│  │ Query Time: 10-100ms | Hit Rate: 100%                  │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

#### **Cache Implementation**
```python
class HierarchicalCache:
    def __init__(self):
        self.l1_cache = {}  # In-memory Python dict
        self.l2_cache = redis.Redis()  # Distributed Redis
        self.cache_stats = CacheStatistics()
        
    def get(self, key: str):
        """
        Multi-level cache lookup with promotion
        """
        # L1 Cache check
        if key in self.l1_cache:
            self.cache_stats.record_hit('L1')
            return self.l1_cache[key]
            
        # L2 Cache check  
        l2_result = self.l2_cache.get(key)
        if l2_result:
            # Promote to L1 cache
            self.l1_cache[key] = l2_result
            self.cache_stats.record_hit('L2')
            return l2_result
            
        # Cache miss - fetch from database
        self.cache_stats.record_miss()
        return None
```

### **Database Optimization**

#### **MongoDB Index Strategy**
```python
# Strategic index configuration for performance
MONGODB_INDEXES = {
    'orders': [
        # Primary query patterns
        {'keys': [('order_id', 1)], 'unique': True},
        {'keys': [('instrument_code', 1), ('datetime', -1)]},
        {'keys': [('strategy_name', 1), ('order_status', 1)]},
        
        # Compound indexes for complex queries
        {'keys': [('instrument_code', 1), ('strategy_name', 1), ('datetime', -1)]},
        {'keys': [('order_status', 1), ('created_datetime', -1)]},
        
        # Text search capabilities
        {'keys': [('$**', 'text')]}
    ],
    
    'positions': [
        {'keys': [('instrument_code', 1), ('strategy_name', 1), ('datetime', -1)]},
        {'keys': [('datetime', -1)]},  # Time-based queries
        {'keys': [('position_size', 1)]}  # Risk queries
    ]
}
```

#### **Parquet Optimization**
```python
class ParquetOptimizer:
    def optimize_storage(self, data_df: pd.DataFrame, partition_cols: List[str]):
        """
        Optimize Parquet storage with partitioning and compression
        """
        optimized_df = (
            data_df
            .astype({
                'price': 'float32',  # Reduce precision for price data
                'volume': 'int32',   # Optimize integer types
                'instrument_code': 'category'  # Use categories for repeated strings
            })
        )
        
        # Write with optimized settings
        optimized_df.to_parquet(
            path,
            engine='pyarrow',
            compression='snappy',  # Balance compression vs speed
            partition_cols=partition_cols,
            row_group_size=50000,  # Optimize for query patterns
            use_dictionary=['instrument_code']  # Dictionary encoding
        )
```

## Disaster Recovery & Backup

### **Backup Strategy**

#### **Multi-Tier Backup Architecture**
```
┌─────────────────────────────────────────────────────────────────┐
│                      Backup Architecture                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Tier 1 - Real-time Replication                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ MongoDB Replica Set - Real-time sync                   │    │
│  │ RPO: 0 seconds | RTO: 30 seconds                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  Tier 2 - Automated Backups                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Hourly Snapshots - Local storage                       │    │
│  │ RPO: 1 hour | RTO: 15 minutes                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  Tier 3 - Offsite Archives                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Daily Archives - Cloud storage                          │    │
│  │ RPO: 24 hours | RTO: 2 hours                           │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

#### **Backup Implementation**
```python
class BackupOrchestrator:
    def __init__(self):
        self.backup_strategies = {
            'critical': RealTimeReplicationStrategy(),
            'operational': AutomatedBackupStrategy(),
            'archival': OffsiteArchiveStrategy()
        }
    
    def execute_backup_plan(self, backup_level: str):
        """
        Execute comprehensive backup plan
        """
        strategy = self.backup_strategies[backup_level]
        
        backup_manifest = BackupManifest()
        backup_manifest.add_data_source('mongodb_operational')
        backup_manifest.add_data_source('parquet_timeseries') 
        backup_manifest.add_data_source('configuration_files')
        
        return strategy.execute_backup(backup_manifest)
```

### **Data Recovery Procedures**

#### **Point-in-Time Recovery**
```python
class DataRecoveryManager:
    def restore_to_point_in_time(self, target_datetime: datetime):
        """
        Restore system data to specific point in time
        """
        recovery_plan = RecoveryPlan()
        
        # 1. Stop all trading processes
        recovery_plan.add_step(StopTradingProcesses())
        
        # 2. Restore MongoDB to target time
        recovery_plan.add_step(RestoreMongoDBPITR(target_datetime))
        
        # 3. Restore Parquet data 
        recovery_plan.add_step(RestoreParquetData(target_datetime))
        
        # 4. Validate data consistency
        recovery_plan.add_step(ValidateDataConsistency())
        
        # 5. Restart trading processes
        recovery_plan.add_step(RestartTradingProcesses())
        
        return recovery_plan.execute()
```

## Future Evolution & Scalability

### **Scaling Strategy**

#### **Horizontal Scaling Plan**
```
Phase 1 - Single Node (Current)
├── MongoDB (Single instance)
├── Parquet (Local storage)
└── Redis (Single instance)

Phase 2 - Local Cluster (6-12 months)
├── MongoDB (3-node replica set)
├── Parquet (Distributed file system)
└── Redis (Cluster mode)

Phase 3 - Multi-Region (1-2 years)
├── MongoDB (Sharded cluster)
├── Parquet (Multi-region replication)
└── Redis (Global clusters)
```

#### **Data Partitioning Strategy**
```python
class DataPartitioningStrategy:
    def partition_time_series_data(self, data_type: str):
        """
        Implement time-based partitioning for optimal performance
        """
        if data_type == 'price_data':
            return {
                'partition_by': 'datetime',
                'partition_size': '1_month',
                'retention_policy': '10_years',
                'compression': 'snappy'
            }
        elif data_type == 'analytics_results':
            return {
                'partition_by': 'calculation_date',
                'partition_size': '1_quarter', 
                'retention_policy': '5_years',
                'compression': 'gzip'
            }
```

### **Technology Evolution**

#### **Future Technology Integration**
- **Stream Processing** - Apache Kafka/Pulsar for real-time event streaming
- **Graph Database** - Neo4j for complex relationship queries
- **Time Series Database** - InfluxDB for specialized time series workloads
- **Data Lake** - Delta Lake for unified analytics platform

#### **Cloud Integration Strategy**
```python
# Future cloud-native data architecture
class CloudDataArchitecture:
    def __init__(self):
        self.storage_tiers = {
            'hot': 'Redis/ElastiCache',      # < 1 day
            'warm': 'MongoDB Atlas',          # 1 day - 1 year  
            'cold': 'S3/Parquet',            # 1 year - 10 years
            'archive': 'S3 Glacier'          # > 10 years
        }
    
    def implement_data_lifecycle_management(self):
        """
        Automated data lifecycle management across storage tiers
        """
        pass
```

---

**Next:** [Business Logic Architecture](03-business-logic-architecture.md) - Domain model and service design patterns