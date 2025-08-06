# Business Logic Architecture

Domain model design and strategic patterns for pysystemtrade's systematic trading business logic.

## Executive Summary

The business logic architecture for pysystemtrade implements a sophisticated **Domain-Driven Design (DDD)** approach, organizing complex trading operations into cohesive domains with clear boundaries and responsibilities. The architecture emphasizes **financial accuracy**, **regulatory compliance**, and **operational reliability** while maintaining flexibility for strategy evolution.

### **Business Logic Vision**
*"A robust, compliant, and extensible business logic framework that accurately models systematic trading operations while providing the flexibility and safety required for managing substantial financial capital."*

## Domain Model Overview

### **Strategic Domain Decomposition**

```
┌─────────────────────────────────────────────────────────────────┐
│                      Business Domain Map                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Core Trading Domains                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │    │
│  │  │ Strategy    │    │ Portfolio   │    │ Risk        │  │    │
│  │  │ Domain      │────│ Domain      │────│ Management  │  │    │
│  │  │             │    │             │    │ Domain      │  │    │
│  │  └─────────────┘    └─────────────┘    └─────────────┘  │    │
│  │         │                   │                   │       │    │
│  └─────────│───────────────────│───────────────────│───────┘    │
│            │                   │                   │            │
│  ┌─────────│───────────────────│───────────────────│───────┐    │
│  │         ▼                   ▼                   ▼       │    │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │    │
│  │  │ Order       │    │ Execution   │    │ Position    │  │    │
│  │  │ Management  │────│ Domain      │────│ Management  │  │    │
│  │  │ Domain      │    │             │    │ Domain      │  │    │
│  │  └─────────────┘    └─────────────┘    └─────────────┘  │    │
│  │                                                         │    │
│  │  Supporting Domains                                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │    │
│  │  │ Market Data │    │ Instrument  │    │ Process     │  │    │
│  │  │ Domain      │    │ Reference   │    │ Control     │  │    │
│  │  │             │    │ Domain      │    │ Domain      │  │    │
│  │  └─────────────┘    └─────────────┘    └─────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  Infrastructure Domains                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │    │
│  │  │ Data        │    │ Integration │    │ Monitoring  │  │    │
│  │  │ Management  │    │ Domain      │    │ Domain      │  │    │
│  │  │ Domain      │    │             │    │             │  │    │
│  │  └─────────────┘    └─────────────┘    └─────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### **Domain Boundaries & Responsibilities**

#### **Core Trading Domains**

| Domain | Primary Responsibility | Key Entities | Business Rules |
|--------|----------------------|--------------|----------------|
| **Strategy Domain** | Trading signal generation & backtesting | Strategy, TradingRule, Forecast | Signal accuracy, rule combination |
| **Portfolio Domain** | Multi-asset portfolio construction | Portfolio, Asset, Allocation | Risk budgeting, correlation limits |
| **Risk Management** | Risk controls & monitoring | RiskLimit, Exposure, Stress | Position limits, VaR constraints |
| **Order Management** | Order lifecycle & execution | Order, Fill, Execution | Order validity, trade settlement |
| **Position Management** | Position tracking & reconciliation | Position, Transaction, P&L | Position accuracy, settlement |
| **Execution Domain** | Trade execution & routing | ExecutionAlgo, Venue, Route | Best execution, market impact |

#### **Supporting Domains**

| Domain | Primary Responsibility | Key Entities | Business Rules |
|--------|----------------------|--------------|----------------|
| **Market Data** | Price data management & quality | Price, Quote, MarketData | Data validity, timeliness |
| **Instrument Reference** | Contract specifications & lifecycle | Instrument, Contract, Calendar | Contract accuracy, roll dates |
| **Process Control** | System orchestration & monitoring | Process, Job, Schedule | Dependency management, SLA |

## Core Trading Domains Deep Dive

### **Strategy Domain Architecture**

The Strategy Domain encapsulates the quantitative research and signal generation capabilities, implementing sophisticated financial mathematics and trading logic.

#### **Domain Model**
```python
# Strategy Domain - Core Entities
class Strategy:
    """
    Aggregate root for trading strategy
    """
    def __init__(self, strategy_id: StrategyId, name: str, config: StrategyConfig):
        self.strategy_id = strategy_id
        self.name = name
        self.config = config
        self.trading_rules: List[TradingRule] = []
        self.instruments: List[Instrument] = []
        self.capital_allocation = CapitalAllocation()
        
    def add_trading_rule(self, rule: TradingRule, weight: float):
        """
        Add trading rule with validation of weight constraints
        """
        if not 0 <= weight <= 1:
            raise ValueError(f"Rule weight must be between 0 and 1, got {weight}")
            
        if sum(r.weight for r in self.trading_rules) + weight > 1:
            raise ValueError("Total rule weights cannot exceed 1.0")
            
        rule.weight = weight
        self.trading_rules.append(rule)
        
    def generate_signals(self, market_data: MarketData) -> Dict[Instrument, Signal]:
        """
        Generate trading signals using configured rules
        """
        signals = {}
        
        for instrument in self.instruments:
            instrument_signals = []
            
            for rule in self.trading_rules:
                if rule.applies_to_instrument(instrument):
                    rule_signal = rule.generate_signal(instrument, market_data)
                    weighted_signal = rule_signal * rule.weight
                    instrument_signals.append(weighted_signal)
                    
            # Combine signals using configured method
            combined_signal = self._combine_signals(instrument_signals)
            signals[instrument] = combined_signal
            
        return signals

class TradingRule:
    """
    Value object representing a trading rule with its parameters
    """
    def __init__(self, rule_id: RuleId, rule_type: RuleType, parameters: Dict):
        self.rule_id = rule_id
        self.rule_type = rule_type
        self.parameters = parameters
        self.weight = 0.0
        
        # Validate parameters for rule type
        self._validate_parameters()
        
    def generate_signal(self, instrument: Instrument, market_data: MarketData) -> Signal:
        """
        Generate trading signal for specific instrument
        """
        rule_generator = RuleGeneratorFactory.create(self.rule_type)
        return rule_generator.generate(instrument, market_data, self.parameters)
        
    def _validate_parameters(self):
        """
        Validate rule parameters against rule type constraints
        """
        validator = RuleParameterValidator.for_rule_type(self.rule_type)
        validator.validate(self.parameters)

class Signal:
    """
    Value object representing a trading signal
    """
    def __init__(self, instrument: Instrument, forecast: float, 
                 confidence: float, timestamp: datetime):
        if not -20 <= forecast <= 20:
            raise ValueError(f"Forecast must be between -20 and 20, got {forecast}")
            
        if not 0 <= confidence <= 1:
            raise ValueError(f"Confidence must be between 0 and 1, got {confidence}")
            
        self.instrument = instrument
        self.forecast = forecast
        self.confidence = confidence
        self.timestamp = timestamp
        
    def scaled_forecast(self, volatility_scalar: float) -> float:
        """
        Scale forecast by volatility for position sizing
        """
        return self.forecast * volatility_scalar
```

#### **Strategy Services**
```python
class StrategyExecutionService:
    """
    Domain service for strategy execution orchestration
    """
    def __init__(self, portfolio_service: PortfolioService,
                 risk_service: RiskService,
                 position_service: PositionService):
        self.portfolio_service = portfolio_service
        self.risk_service = risk_service  
        self.position_service = position_service
        
    def execute_strategy(self, strategy: Strategy, market_data: MarketData) -> StrategyResult:
        """
        Execute complete strategy workflow with risk controls
        """
        try:
            # 1. Generate trading signals
            signals = strategy.generate_signals(market_data)
            
            # 2. Convert signals to target positions
            target_positions = self.portfolio_service.calculate_target_positions(
                signals, strategy.capital_allocation
            )
            
            # 3. Apply risk controls
            risk_adjusted_positions = self.risk_service.apply_risk_controls(
                target_positions, strategy.risk_limits
            )
            
            # 4. Generate orders for position changes
            current_positions = self.position_service.get_current_positions(strategy)
            orders = self._generate_orders(current_positions, risk_adjusted_positions)
            
            return StrategyResult(
                strategy_id=strategy.strategy_id,
                signals=signals,
                target_positions=risk_adjusted_positions,
                orders=orders,
                execution_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            return StrategyResult.failed(strategy.strategy_id, str(e))
            
    def _generate_orders(self, current_positions: Dict[Instrument, Position],
                        target_positions: Dict[Instrument, Position]) -> List[Order]:
        """
        Generate orders to transition from current to target positions
        """
        orders = []
        
        all_instruments = set(current_positions.keys()) | set(target_positions.keys())
        
        for instrument in all_instruments:
            current_position = current_positions.get(instrument, Position.zero())
            target_position = target_positions.get(instrument, Position.zero())
            
            position_delta = target_position.quantity - current_position.quantity
            
            if abs(position_delta) > instrument.minimum_trade_size:
                order = Order.create_market_order(
                    instrument=instrument,
                    quantity=position_delta,
                    strategy_id=strategy.strategy_id
                )
                orders.append(order)
                
        return orders
```

### **Portfolio Domain Architecture**

The Portfolio Domain handles multi-asset portfolio construction, optimization, and risk budgeting with sophisticated quantitative methods.

#### **Domain Model**
```python
class Portfolio:
    """
    Aggregate root for portfolio management
    """
    def __init__(self, portfolio_id: PortfolioId, strategy: Strategy):
        self.portfolio_id = portfolio_id
        self.strategy = strategy
        self.positions: Dict[Instrument, Position] = {}
        self.capital_allocation = CapitalAllocation()
        self.risk_budget = RiskBudget()
        self.optimization_config = OptimizationConfig()
        
    def add_position(self, position: Position):
        """
        Add position with validation against risk limits
        """
        if not self.risk_budget.can_accommodate_position(position):
            raise RiskLimitExceeded(f"Position {position} exceeds risk budget")
            
        self.positions[position.instrument] = position
        self._rebalance_if_needed()
        
    def calculate_portfolio_risk(self) -> PortfolioRisk:
        """
        Calculate comprehensive portfolio risk metrics
        """
        return PortfolioRisk(
            total_var=self._calculate_var(),
            correlation_risk=self._calculate_correlation_risk(),
            concentration_risk=self._calculate_concentration_risk(),
            tail_risk=self._calculate_tail_risk()
        )
        
    def optimize_weights(self, signals: Dict[Instrument, Signal],
                        constraints: OptimizationConstraints) -> Dict[Instrument, float]:
        """
        Optimize portfolio weights using configured method
        """
        optimizer = PortfolioOptimizerFactory.create(self.optimization_config.method)
        
        return optimizer.optimize(
            signals=signals,
            current_positions=self.positions,
            constraints=constraints,
            risk_model=self.risk_budget.risk_model
        )

class Position:
    """
    Value object representing a position in an instrument
    """
    def __init__(self, instrument: Instrument, quantity: float, 
                 average_price: float, timestamp: datetime):
        self.instrument = instrument
        self.quantity = quantity
        self.average_price = average_price
        self.timestamp = timestamp
        
        # Calculate derived values
        self.notional_value = quantity * average_price * instrument.multiplier
        self.market_value = self._calculate_market_value()
        
    def update_with_fill(self, fill: Fill) -> 'Position':
        """
        Create new position updated with fill (immutable)
        """
        new_quantity = self.quantity + fill.quantity
        
        if new_quantity == 0:
            return Position.zero(self.instrument)
            
        # Calculate new average price
        current_cost = self.quantity * self.average_price
        fill_cost = fill.quantity * fill.price
        new_cost = current_cost + fill_cost
        new_average_price = new_cost / new_quantity
        
        return Position(
            instrument=self.instrument,
            quantity=new_quantity,
            average_price=new_average_price,
            timestamp=fill.timestamp
        )
        
    def calculate_pnl(self, market_price: float) -> PnL:
        """
        Calculate unrealized P&L at given market price
        """
        unrealized_pnl = (market_price - self.average_price) * self.quantity
        
        return PnL(
            realized=0.0,  # No realized P&L for open position
            unrealized=unrealized_pnl,
            total=unrealized_pnl
        )
        
    @classmethod
    def zero(cls, instrument: Instrument) -> 'Position':
        """
        Create zero position for instrument
        """
        return cls(instrument, 0.0, 0.0, datetime.utcnow())

class CapitalAllocation:
    """
    Value object managing capital allocation across strategies and instruments
    """
    def __init__(self, total_capital: float, base_currency: str = "USD"):
        if total_capital <= 0:
            raise ValueError("Total capital must be positive")
            
        self.total_capital = total_capital
        self.base_currency = base_currency
        self.strategy_allocations: Dict[StrategyId, float] = {}
        self.reserved_capital = 0.0
        
    def allocate_to_strategy(self, strategy_id: StrategyId, allocation_percent: float):
        """
        Allocate percentage of capital to strategy
        """
        if not 0 < allocation_percent <= 1:
            raise ValueError("Allocation must be between 0 and 1")
            
        total_allocated = sum(self.strategy_allocations.values()) + allocation_percent
        
        if total_allocated > 1.0:
            raise ValueError("Total allocations cannot exceed 100%")
            
        self.strategy_allocations[strategy_id] = allocation_percent
        
    def get_available_capital(self, strategy_id: StrategyId) -> float:
        """
        Get available capital for strategy
        """
        allocation = self.strategy_allocations.get(strategy_id, 0.0)
        return (self.total_capital - self.reserved_capital) * allocation
        
    def reserve_capital(self, amount: float, reason: str):
        """
        Reserve capital for margin, risk management, etc.
        """
        if amount < 0:
            raise ValueError("Reserved amount must be positive")
            
        if self.reserved_capital + amount > self.total_capital * 0.5:
            raise ValueError("Cannot reserve more than 50% of total capital")
            
        self.reserved_capital += amount
```

#### **Portfolio Services**
```python
class PortfolioOptimizationService:
    """
    Domain service for portfolio optimization
    """
    def __init__(self, risk_model: RiskModel, 
                 optimization_engine: OptimizationEngine):
        self.risk_model = risk_model
        self.optimization_engine = optimization_engine
        
    def optimize_portfolio(self, portfolio: Portfolio, 
                          signals: Dict[Instrument, Signal],
                          constraints: OptimizationConstraints) -> OptimizationResult:
        """
        Optimize portfolio using mean-variance or alternative methods
        """
        # 1. Prepare optimization inputs
        expected_returns = self._calculate_expected_returns(signals)
        covariance_matrix = self.risk_model.get_covariance_matrix(portfolio.instruments)
        current_weights = self._get_current_weights(portfolio)
        
        # 2. Set up optimization problem
        optimization_problem = OptimizationProblem(
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            current_weights=current_weights,
            constraints=constraints
        )
        
        # 3. Solve optimization
        optimal_weights = self.optimization_engine.solve(optimization_problem)
        
        # 4. Apply transaction cost adjustments
        adjusted_weights = self._adjust_for_transaction_costs(
            current_weights, optimal_weights, portfolio.transaction_costs
        )
        
        return OptimizationResult(
            optimal_weights=adjusted_weights,
            expected_return=self._calculate_portfolio_return(adjusted_weights, expected_returns),
            expected_risk=self._calculate_portfolio_risk(adjusted_weights, covariance_matrix),
            turnover=self._calculate_turnover(current_weights, adjusted_weights)
        )
        
    def _calculate_expected_returns(self, signals: Dict[Instrument, Signal]) -> np.ndarray:
        """
        Convert signals to expected returns for optimization
        """
        returns = []
        for instrument, signal in signals.items():
            # Convert forecast to expected return using volatility scaling
            expected_return = signal.forecast * instrument.volatility_target / 100
            returns.append(expected_return)
            
        return np.array(returns)
        
    def _adjust_for_transaction_costs(self, current_weights: np.ndarray,
                                    optimal_weights: np.ndarray,
                                    transaction_costs: Dict[Instrument, float]) -> np.ndarray:
        """
        Adjust optimal weights for transaction cost impact
        """
        adjusted_weights = optimal_weights.copy()
        
        for i, (current_w, optimal_w) in enumerate(zip(current_weights, optimal_weights)):
            weight_change = abs(optimal_w - current_w)
            transaction_cost = transaction_costs.get(self.instruments[i], 0.001)
            
            # If transaction cost exceeds expected benefit, don't trade
            if weight_change * transaction_cost > abs(optimal_w - current_w) * 0.1:
                adjusted_weights[i] = current_w
                
        return adjusted_weights
```

### **Risk Management Domain Architecture**

The Risk Management Domain implements comprehensive risk controls and monitoring, ensuring systematic adherence to risk limits and regulatory requirements.

#### **Domain Model**
```python
class RiskManager:
    """
    Aggregate root for risk management
    """
    def __init__(self, risk_limits: RiskLimits, risk_model: RiskModel):
        self.risk_limits = risk_limits
        self.risk_model = risk_model
        self.risk_monitors: List[RiskMonitor] = []
        self.active_breaches: List[RiskBreach] = []
        
    def add_risk_monitor(self, monitor: RiskMonitor):
        """
        Add risk monitor with validation
        """
        if monitor.risk_type in [m.risk_type for m in self.risk_monitors]:
            raise ValueError(f"Risk monitor for {monitor.risk_type} already exists")
            
        self.risk_monitors.append(monitor)
        
    def evaluate_portfolio_risk(self, portfolio: Portfolio) -> RiskEvaluation:
        """
        Comprehensive risk evaluation of portfolio
        """
        risk_metrics = {}
        violations = []
        
        for monitor in self.risk_monitors:
            try:
                metric = monitor.calculate_risk_metric(portfolio, self.risk_model)
                risk_metrics[monitor.risk_type] = metric
                
                # Check against limits
                if self.risk_limits.is_violated(monitor.risk_type, metric.value):
                    violation = RiskViolation(
                        risk_type=monitor.risk_type,
                        current_value=metric.value,
                        limit=self.risk_limits.get_limit(monitor.risk_type),
                        severity=self._calculate_severity(metric.value, monitor.risk_type)
                    )
                    violations.append(violation)
                    
            except Exception as e:
                # Log error but don't fail entire risk evaluation
                logging.error(f"Risk monitor {monitor.risk_type} failed: {e}")
                
        return RiskEvaluation(
            portfolio_id=portfolio.portfolio_id,
            risk_metrics=risk_metrics,
            violations=violations,
            overall_risk_score=self._calculate_overall_risk_score(risk_metrics),
            evaluation_timestamp=datetime.utcnow()
        )
        
    def apply_risk_controls(self, proposed_orders: List[Order]) -> List[Order]:
        """
        Apply risk controls to proposed orders
        """
        approved_orders = []
        
        for order in proposed_orders:
            risk_check = self._evaluate_order_risk(order)
            
            if risk_check.approved:
                approved_orders.append(order)
            else:
                # Log rejected order with reason
                self._log_order_rejection(order, risk_check.rejection_reason)
                
                # Create modified order if possible
                modified_order = self._create_risk_adjusted_order(order, risk_check)
                if modified_order:
                    approved_orders.append(modified_order)
                    
        return approved_orders

class RiskLimits:
    """
    Value object defining comprehensive risk limits
    """
    def __init__(self):
        self.position_limits: Dict[Instrument, PositionLimit] = {}
        self.portfolio_limits = PortfolioLimits()
        self.strategy_limits: Dict[StrategyId, StrategyLimits] = {}
        
    def add_position_limit(self, instrument: Instrument, 
                          max_position: float, max_daily_volume: float):
        """
        Add position limit for specific instrument
        """
        self.position_limits[instrument] = PositionLimit(
            instrument=instrument,
            max_position=max_position,
            max_daily_volume=max_daily_volume,
            concentration_limit=0.05  # 5% max concentration
        )
        
    def is_violated(self, risk_type: RiskType, current_value: float) -> bool:
        """
        Check if risk limit is violated
        """
        limit = self._get_limit_for_risk_type(risk_type)
        
        if risk_type in [RiskType.VAR, RiskType.EXPECTED_SHORTFALL]:
            return current_value > limit  # Higher is worse
        elif risk_type == RiskType.CORRELATION:
            return abs(current_value) > limit  # Absolute value check
        else:
            return current_value > limit

class RiskMonitor:
    """
    Base class for specific risk monitoring implementations
    """
    def __init__(self, risk_type: RiskType, calculation_frequency: timedelta):
        self.risk_type = risk_type
        self.calculation_frequency = calculation_frequency
        self.last_calculation = None
        
    def calculate_risk_metric(self, portfolio: Portfolio, 
                            risk_model: RiskModel) -> RiskMetric:
        """
        Calculate risk metric - to be implemented by subclasses
        """
        raise NotImplementedError()
        
    def needs_recalculation(self) -> bool:
        """
        Check if risk metric needs recalculation
        """
        if self.last_calculation is None:
            return True
            
        return datetime.utcnow() - self.last_calculation > self.calculation_frequency

class VaRMonitor(RiskMonitor):
    """
    Value at Risk monitoring implementation
    """
    def __init__(self, confidence_level: float = 0.95, time_horizon_days: int = 1):
        super().__init__(RiskType.VAR, timedelta(hours=1))
        self.confidence_level = confidence_level
        self.time_horizon_days = time_horizon_days
        
    def calculate_risk_metric(self, portfolio: Portfolio, 
                            risk_model: RiskModel) -> RiskMetric:
        """
        Calculate portfolio Value at Risk
        """
        # Get portfolio weights and covariance matrix
        weights = self._get_portfolio_weights(portfolio)
        cov_matrix = risk_model.get_covariance_matrix(portfolio.instruments)
        
        # Calculate portfolio variance
        portfolio_variance = weights.T @ cov_matrix @ weights
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # Calculate VaR using normal distribution assumption
        from scipy.stats import norm
        var_multiplier = norm.ppf(1 - self.confidence_level)
        
        daily_var = portfolio.total_value * portfolio_volatility * var_multiplier
        scaled_var = daily_var * np.sqrt(self.time_horizon_days)
        
        self.last_calculation = datetime.utcnow()
        
        return RiskMetric(
            risk_type=RiskType.VAR,
            value=abs(scaled_var),  # VaR is typically reported as positive
            confidence_level=self.confidence_level,
            time_horizon=self.time_horizon_days,
            calculation_timestamp=self.last_calculation
        )

class ConcentrationRiskMonitor(RiskMonitor):
    """
    Portfolio concentration risk monitoring
    """
    def __init__(self):
        super().__init__(RiskType.CONCENTRATION, timedelta(minutes=30))
        
    def calculate_risk_metric(self, portfolio: Portfolio, 
                            risk_model: RiskModel) -> RiskMetric:
        """
        Calculate concentration risk using Herfindahl-Hirschman Index
        """
        weights = self._get_portfolio_weights(portfolio)
        
        # Calculate HHI (sum of squared weights)
        hhi = np.sum(weights ** 2)
        
        # Normalize to 0-1 scale (1 = perfectly concentrated)
        n_instruments = len(portfolio.positions)
        normalized_hhi = (hhi - 1/n_instruments) / (1 - 1/n_instruments)
        
        self.last_calculation = datetime.utcnow()
        
        return RiskMetric(
            risk_type=RiskType.CONCENTRATION,
            value=normalized_hhi,
            additional_info={'hhi_raw': hhi, 'n_instruments': n_instruments},
            calculation_timestamp=self.last_calculation
        )
```

## Service Layer Architecture

### **Application Services**

Application services orchestrate domain operations and manage transaction boundaries, providing the interface between external systems and domain logic.

#### **Trading Service**
```python
class TradingApplicationService:
    """
    Application service orchestrating trading operations
    """
    def __init__(self, 
                 strategy_repository: StrategyRepository,
                 portfolio_repository: PortfolioRepository,
                 risk_manager: RiskManager,
                 order_service: OrderService,
                 event_publisher: EventPublisher):
        self.strategy_repository = strategy_repository
        self.portfolio_repository = portfolio_repository
        self.risk_manager = risk_manager
        self.order_service = order_service
        self.event_publisher = event_publisher
        
    @transactional
    def execute_trading_cycle(self, strategy_id: StrategyId, 
                            market_data: MarketData) -> TradingCycleResult:
        """
        Execute complete trading cycle with full transaction management
        """
        try:
            # 1. Load strategy and portfolio
            strategy = self.strategy_repository.get_by_id(strategy_id)
            portfolio = self.portfolio_repository.get_by_strategy(strategy_id)
            
            # 2. Generate trading signals
            signals = strategy.generate_signals(market_data)
            
            # 3. Optimize portfolio
            optimization_result = self._optimize_portfolio(portfolio, signals)
            
            # 4. Apply risk controls
            risk_evaluation = self.risk_manager.evaluate_portfolio_risk(portfolio)
            if risk_evaluation.has_critical_violations():
                return TradingCycleResult.failed("Critical risk violations detected")
                
            # 5. Generate orders
            orders = self._generate_orders(portfolio, optimization_result.optimal_weights)
            
            # 6. Apply pre-trade risk checks
            approved_orders = self.risk_manager.apply_risk_controls(orders)
            
            # 7. Submit orders for execution
            execution_results = []
            for order in approved_orders:
                result = self.order_service.submit_order(order)
                execution_results.append(result)
                
            # 8. Update portfolio with executed orders
            self._update_portfolio_with_executions(portfolio, execution_results)
            
            # 9. Publish events
            trading_event = TradingCycleCompletedEvent(
                strategy_id=strategy_id,
                signals=signals,
                orders_submitted=len(approved_orders),
                execution_results=execution_results
            )
            self.event_publisher.publish(trading_event)
            
            return TradingCycleResult.successful(execution_results)
            
        except Exception as e:
            # Publish failure event
            failure_event = TradingCycleFailedEvent(strategy_id, str(e))
            self.event_publisher.publish(failure_event)
            
            # Re-raise for transaction rollback
            raise
            
    def _optimize_portfolio(self, portfolio: Portfolio, 
                          signals: Dict[Instrument, Signal]) -> OptimizationResult:
        """
        Optimize portfolio weights using configured method
        """
        optimization_service = PortfolioOptimizationService(
            risk_model=self.risk_manager.risk_model,
            optimization_engine=OptimizationEngineFactory.create_default()
        )
        
        constraints = OptimizationConstraints(
            max_weight=0.10,  # 10% max position
            max_turnover=0.20,  # 20% max turnover
            sector_limits=portfolio.sector_limits
        )
        
        return optimization_service.optimize_portfolio(portfolio, signals, constraints)
```

### **Domain Services**

Domain services encapsulate business logic that doesn't naturally fit within a single entity or value object.

#### **Position Reconciliation Service**
```python
class PositionReconciliationService:
    """
    Domain service for position reconciliation and accuracy validation
    """
    def __init__(self, position_repository: PositionRepository,
                 execution_repository: ExecutionRepository,
                 broker_integration: BrokerIntegration):
        self.position_repository = position_repository
        self.execution_repository = execution_repository
        self.broker_integration = broker_integration
        
    def reconcile_positions(self, strategy_id: StrategyId, 
                          reconciliation_date: date) -> ReconciliationResult:
        """
        Comprehensive position reconciliation across multiple sources
        """
        # 1. Get positions from different sources
        system_positions = self.position_repository.get_positions_by_strategy(
            strategy_id, reconciliation_date
        )
        
        broker_positions = self.broker_integration.get_positions(reconciliation_date)
        
        calculated_positions = self._calculate_positions_from_executions(
            strategy_id, reconciliation_date
        )
        
        # 2. Compare positions across sources
        reconciliation_report = ReconciliationReport()
        
        all_instruments = set(system_positions.keys()) | set(broker_positions.keys())
        
        for instrument in all_instruments:
            system_pos = system_positions.get(instrument, Position.zero(instrument))
            broker_pos = broker_positions.get(instrument, Position.zero(instrument))
            calc_pos = calculated_positions.get(instrument, Position.zero(instrument))
            
            # Check for discrepancies
            system_broker_diff = abs(system_pos.quantity - broker_pos.quantity)
            system_calc_diff = abs(system_pos.quantity - calc_pos.quantity)
            
            if system_broker_diff > instrument.minimum_trade_size:
                discrepancy = PositionDiscrepancy(
                    instrument=instrument,
                    system_position=system_pos.quantity,
                    broker_position=broker_pos.quantity,
                    difference=system_broker_diff,
                    discrepancy_type=DiscrepancyType.SYSTEM_BROKER
                )
                reconciliation_report.add_discrepancy(discrepancy)
                
            if system_calc_diff > instrument.minimum_trade_size:
                discrepancy = PositionDiscrepancy(
                    instrument=instrument,
                    system_position=system_pos.quantity,
                    calculated_position=calc_pos.quantity,
                    difference=system_calc_diff,
                    discrepancy_type=DiscrepancyType.SYSTEM_CALCULATION
                )
                reconciliation_report.add_discrepancy(discrepancy)
                
        # 3. Generate reconciliation actions
        reconciliation_actions = self._generate_reconciliation_actions(
            reconciliation_report.discrepancies
        )
        
        return ReconciliationResult(
            strategy_id=strategy_id,
            reconciliation_date=reconciliation_date,
            report=reconciliation_report,
            actions=reconciliation_actions,
            status=self._determine_reconciliation_status(reconciliation_report)
        )
        
    def _calculate_positions_from_executions(self, strategy_id: StrategyId,
                                           as_of_date: date) -> Dict[Instrument, Position]:
        """
        Calculate positions by replaying all executions
        """
        executions = self.execution_repository.get_executions_by_strategy(
            strategy_id, start_date=None, end_date=as_of_date
        )
        
        positions = {}
        
        for execution in executions:
            if execution.instrument not in positions:
                positions[execution.instrument] = Position.zero(execution.instrument)
                
            positions[execution.instrument] = positions[execution.instrument].update_with_fill(
                Fill.from_execution(execution)
            )
            
        return positions
```

## Event-Driven Architecture Integration

### **Domain Events**

Domain events capture significant business occurrences and enable loose coupling between bounded contexts.

#### **Trading Domain Events**
```python
class DomainEvent:
    """
    Base class for domain events
    """
    def __init__(self, event_id: str = None, occurred_at: datetime = None):
        self.event_id = event_id or str(uuid.uuid4())
        self.occurred_at = occurred_at or datetime.utcnow()
        
class SignalGeneratedEvent(DomainEvent):
    """
    Published when trading signals are generated
    """
    def __init__(self, strategy_id: StrategyId, 
                 signals: Dict[Instrument, Signal], **kwargs):
        super().__init__(**kwargs)
        self.strategy_id = strategy_id
        self.signals = signals
        
class PortfolioOptimizedEvent(DomainEvent):
    """
    Published when portfolio optimization is completed
    """
    def __init__(self, portfolio_id: PortfolioId,
                 optimization_result: OptimizationResult, **kwargs):
        super().__init__(**kwargs)
        self.portfolio_id = portfolio_id
        self.optimization_result = optimization_result
        
class RiskLimitBreachedEvent(DomainEvent):
    """
    Published when risk limits are breached
    """
    def __init__(self, portfolio_id: PortfolioId,
                 risk_violation: RiskViolation, **kwargs):
        super().__init__(**kwargs)
        self.portfolio_id = portfolio_id
        self.risk_violation = risk_violation
        self.severity = risk_violation.severity
```

### **Event Handlers**
```python
class RiskAlertEventHandler:
    """
    Handle risk-related events with appropriate responses
    """
    def __init__(self, alert_service: AlertService,
                 risk_repository: RiskRepository):
        self.alert_service = alert_service
        self.risk_repository = risk_repository
        
    def handle_risk_limit_breached(self, event: RiskLimitBreachedEvent):
        """
        Handle risk limit breach with escalating responses
        """
        # 1. Record the breach
        risk_breach = RiskBreach(
            portfolio_id=event.portfolio_id,
            violation=event.risk_violation,
            occurred_at=event.occurred_at
        )
        self.risk_repository.save_breach(risk_breach)
        
        # 2. Determine response based on severity
        if event.severity == Severity.CRITICAL:
            # Immediate trading halt
            self.alert_service.send_critical_alert(
                f"CRITICAL: Risk limit breached for portfolio {event.portfolio_id}. "
                f"Trading halted automatically."
            )
            
            # Publish trading halt event
            halt_event = TradingHaltRequestedEvent(
                portfolio_id=event.portfolio_id,
                reason=f"Risk limit breach: {event.risk_violation.risk_type}",
                requested_by="RiskManager"
            )
            self.event_publisher.publish(halt_event)
            
        elif event.severity == Severity.HIGH:
            # Alert but continue trading with restrictions
            self.alert_service.send_high_priority_alert(
                f"HIGH: Risk limit breached for portfolio {event.portfolio_id}. "
                f"Review required."
            )
            
        else:
            # Log and monitor
            self.alert_service.send_info_alert(
                f"Risk limit exceeded for portfolio {event.portfolio_id}. "
                f"Monitoring situation."
            )
```

## Testing Strategy

### **Domain Testing Approach**

#### **Unit Testing - Domain Logic**
```python
class TestStrategy:
    """
    Comprehensive testing of Strategy domain logic
    """
    def test_strategy_signal_generation(self):
        """
        Test signal generation with various market conditions
        """
        # Arrange
        strategy = Strategy("test_strategy", "Test Strategy", StrategyConfig())
        
        # Add EWMAC rule
        ewmac_rule = TradingRule("ewmac_16_64", RuleType.EWMAC, 
                               {"fast_span": 16, "slow_span": 64})
        strategy.add_trading_rule(ewmac_rule, weight=0.5)
        
        # Add breakout rule
        breakout_rule = TradingRule("breakout_20", RuleType.BREAKOUT,
                                  {"lookback_days": 20})
        strategy.add_trading_rule(breakout_rule, weight=0.5)
        
        # Create test market data
        market_data = create_test_market_data_with_trend()
        
        # Act
        signals = strategy.generate_signals(market_data)
        
        # Assert
        assert len(signals) > 0
        for instrument, signal in signals.items():
            assert -20 <= signal.forecast <= 20
            assert 0 <= signal.confidence <= 1
            
    def test_risk_limit_validation(self):
        """
        Test risk limit enforcement
        """
        # Arrange
        risk_limits = RiskLimits()
        risk_limits.add_position_limit(
            Instrument("SOFR"), max_position=100, max_daily_volume=50
        )
        
        portfolio = Portfolio("test_portfolio", Strategy("test", "Test", {}))
        
        # Act & Assert
        with pytest.raises(RiskLimitExceeded):
            large_position = Position(Instrument("SOFR"), 150, 100.0, datetime.utcnow())
            portfolio.add_position(large_position)
```

#### **Integration Testing - Cross-Domain Interactions**
```python
class TestTradingWorkflow:
    """
    Integration tests for complete trading workflows
    """
    def test_complete_trading_cycle(self):
        """
        Test complete trading cycle from signals to execution
        """
        # Arrange - Set up complete system
        data_blob = create_test_data_blob()
        trading_service = TradingApplicationService(...)
        
        # Act - Execute trading cycle
        result = trading_service.execute_trading_cycle(
            strategy_id="test_strategy",
            market_data=create_test_market_data()
        )
        
        # Assert - Verify all steps completed successfully
        assert result.success
        assert len(result.execution_results) > 0
        assert all(er.status == ExecutionStatus.COMPLETED 
                  for er in result.execution_results)
```

---

**Next:** [Integration Architecture](04-integration-architecture.md) - External system integration patterns and protocols