"""Strategy runner - manages strategy lifecycle"""
import uuid
import threading
from datetime import date
from enum import Enum
from typing import Dict, List, Any, Optional, Type, Callable
from dataclasses import dataclass, field

from strategy_engine.base import BaseStrategy
from strategy_engine.context import StrategyContext
from strategy_engine.types import Order, Trade, Position
from data_center.api.data_api import DataAPI
from data_center.interfaces.data_source import DailyBar


class StrategyState(Enum):
    """Strategy state enumeration"""
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class StrategyInstance:
    """Strategy instance data structure"""
    strategy_id: str
    strategy: BaseStrategy
    context: StrategyContext
    symbols: List[str]
    params: Dict[str, Any]
    state: StrategyState = StrategyState.STOPPED
    current_prices: Dict[str, float] = field(default_factory=dict)
    bar_handlers: List[Callable] = field(default_factory=list)


class TradingService:
    """Trading service interface for order submission
    
    This is a simple trading service interface that can be extended to:
    - Connect to broker APIs
    - Simulate trading
    - Add risk controls
    """
    
    def __init__(self):
        self._orders: List[Order] = []
        self._trades: List[Trade] = []
        self._order_callbacks: List[Callable[[Order], None]] = []
        self._trade_callbacks: List[Callable[[Trade], None]] = []
    
    def submit_order(self, order: Order) -> bool:
        """Submit an order
        
        Args:
            order: Order object
            
        Returns:
            Whether submission was successful
        """
        self._orders.append(order)
        for callback in self._order_callbacks:
            callback(order)
        return True
    
    def record_trade(self, trade: Trade) -> None:
        """Record a trade
        
        Args:
            trade: Trade object
        """
        self._trades.append(trade)
        for callback in self._trade_callbacks:
            callback(trade)
    
    def get_orders(self) -> List[Order]:
        """Get all orders"""
        return self._orders.copy()
    
    def get_trades(self) -> List[Trade]:
        """Get all trades"""
        return self._trades.copy()
    
    def on_order(self, callback: Callable[[Order], None]) -> None:
        """Register order callback"""
        self._order_callbacks.append(callback)
    
    def on_trade(self, callback: Callable[[Trade], None]) -> None:
        """Register trade callback"""
        self._trade_callbacks.append(callback)


class StrategyRunner:
    """Strategy runner - manages strategy instance lifecycle
    
    Handles strategy registration, start, stop, pause, resume operations.
    Each strategy instance runs independently with its own context and state.
    
    Attributes:
        data_api: DataAPI for market data
        trading_service: TradingService for order submission
    """
    
    def __init__(self, data_api: DataAPI, trading_service: Optional[TradingService] = None):
        """Initialize strategy runner
        
        Args:
            data_api: DataAPI instance
            trading_service: TradingService instance (optional, creates new if not provided)
        """
        self._data_api = data_api
        self._trading_service = trading_service or TradingService()
        self._strategies: Dict[str, StrategyInstance] = {}
        self._lock = threading.RLock()
        self._bar_handlers: Dict[str, List[Callable[[str, DailyBar], None]]] = {}
    
    def register_strategy(
        self,
        strategy_class: Type[BaseStrategy],
        params: Dict[str, Any],
        symbols: List[str],
        initial_capital: float = 1000000.0
    ) -> str:
        """Register a strategy instance
        
        Args:
            strategy_class: Strategy class (must inherit BaseStrategy)
            params: Strategy parameters
            symbols: Trading symbols list
            initial_capital: Initial capital (default 1M)
            
        Returns:
            Strategy ID for subsequent operations
            
        Raises:
            ValueError: If parameters are invalid
        """
        if not symbols:
            raise ValueError("Must specify at least one trading symbol")
        
        if initial_capital <= 0:
            raise ValueError("Initial capital must be greater than 0")
        
        strategy_id = str(uuid.uuid4())
        
        strategy = strategy_class(name=strategy_class.__name__, params=params)
        context = StrategyContext(initial_capital=initial_capital)
        strategy.set_context(context)
        
        if symbols:
            strategy.set_symbol(symbols[0])
        
        strategy.on_init()
        
        instance = StrategyInstance(
            strategy_id=strategy_id,
            strategy=strategy,
            context=context,
            symbols=symbols,
            params=params,
            state=StrategyState.STOPPED
        )
        
        with self._lock:
            self._strategies[strategy_id] = instance
        
        return strategy_id
    
    def unregister_strategy(self, strategy_id: str) -> bool:
        """Unregister a strategy instance
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Whether unregistration was successful
            
        Raises:
            KeyError: If strategy does not exist
        """
        with self._lock:
            if strategy_id not in self._strategies:
                raise KeyError(f"Strategy not found: {strategy_id}")
            
            instance = self._strategies[strategy_id]
            
            if instance.state == StrategyState.RUNNING:
                self.stop_strategy(strategy_id)
            
            del self._strategies[strategy_id]
            
            if strategy_id in self._bar_handlers:
                del self._bar_handlers[strategy_id]
        
        return True
    
    def start_strategy(self, strategy_id: str) -> bool:
        """Start a strategy
        
        Sets strategy state to RUNNING, begins receiving market data and executing.
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Whether start was successful
            
        Raises:
            KeyError: If strategy does not exist
        """
        with self._lock:
            if strategy_id not in self._strategies:
                raise KeyError(f"Strategy not found: {strategy_id}")
            
            instance = self._strategies[strategy_id]
            
            if instance.state == StrategyState.RUNNING:
                return True
            
            instance.state = StrategyState.RUNNING
        
        return True
    
    def stop_strategy(self, strategy_id: str) -> bool:
        """Stop a strategy
        
        Sets strategy state to STOPPED, stops receiving market data.
        Strategy state is cleared, needs re-registration to run again.
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Whether stop was successful
            
        Raises:
            KeyError: If strategy does not exist
        """
        with self._lock:
            if strategy_id not in self._strategies:
                raise KeyError(f"Strategy not found: {strategy_id}")
            
            instance = self._strategies[strategy_id]
            instance.state = StrategyState.STOPPED
        
        return True
    
    def pause_strategy(self, strategy_id: str) -> bool:
        """Pause a strategy
        
        Sets strategy state to PAUSED, pauses market data reception.
        Strategy state is preserved, can be resumed via resume_strategy.
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Whether pause was successful
            
        Raises:
            KeyError: If strategy does not exist
        """
        with self._lock:
            if strategy_id not in self._strategies:
                raise KeyError(f"Strategy not found: {strategy_id}")
            
            instance = self._strategies[strategy_id]
            
            if instance.state != StrategyState.RUNNING:
                return False
            
            instance.state = StrategyState.PAUSED
        
        return True
    
    def resume_strategy(self, strategy_id: str) -> bool:
        """Resume a paused strategy
        
        Restores strategy state from PAUSED to RUNNING.
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Whether resume was successful
            
        Raises:
            KeyError: If strategy does not exist
        """
        with self._lock:
            if strategy_id not in self._strategies:
                raise KeyError(f"Strategy not found: {strategy_id}")
            
            instance = self._strategies[strategy_id]
            
            if instance.state != StrategyState.PAUSED:
                return False
            
            instance.state = StrategyState.RUNNING
        
        return True
    
    def get_strategy_status(self, strategy_id: str) -> StrategyState:
        """Get strategy status
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Strategy state
            
        Raises:
            KeyError: If strategy does not exist
        """
        with self._lock:
            if strategy_id not in self._strategies:
                raise KeyError(f"Strategy not found: {strategy_id}")
            
            return self._strategies[strategy_id].state
    
    def get_all_strategies(self) -> List[Dict[str, Any]]:
        """Get all registered strategy information
        
        Returns:
            Strategy info list, each containing:
            - strategy_id: Strategy ID
            - name: Strategy name
            - state: Strategy state
            - symbols: Trading symbols list
            - params: Strategy parameters
            - cash: Current cash
            - total_value: Total asset value
        """
        with self._lock:
            result = []
            for strategy_id, instance in self._strategies.items():
                result.append({
                    "strategy_id": strategy_id,
                    "name": instance.strategy.name,
                    "state": instance.state.value,
                    "symbols": instance.symbols,
                    "params": instance.params,
                    "cash": instance.context.cash,
                    "total_value": instance.context.total_value,
                    "positions": {
                        symbol: {
                            "quantity": pos.quantity,
                            "avg_cost": pos.avg_cost,
                            "current_price": pos.current_price,
                            "market_value": pos.market_value
                        }
                        for symbol, pos in instance.context.positions.items()
                    }
                })
            return result
    
    def update_prices(self, prices_dict: Dict[str, float]) -> None:
        """Update market prices
        
        Updates position market prices for all strategies to calculate current value and P&L.
        
        Args:
            prices_dict: Price dict, key is symbol, value is price
        """
        with self._lock:
            for instance in self._strategies.values():
                for symbol, price in prices_dict.items():
                    instance.context.update_position_price(symbol, price)
                    instance.current_prices[symbol] = price
    
    def on_bar(self, symbol: str, bar: DailyBar) -> None:
        """Handle market data
        
        When receiving new market data, notifies all running strategies.
        
        Args:
            symbol: Stock symbol
            bar: Daily bar data
        """
        with self._lock:
            for instance in self._strategies.values():
                if instance.state != StrategyState.RUNNING:
                    continue
                
                if symbol not in instance.symbols:
                    continue
                
                instance.context.current_date = bar.date
                instance.context.update_position_price(symbol, bar.close)
                instance.current_prices[symbol] = bar.close
                
                try:
                    instance.strategy.set_symbol(symbol)
                    instance.strategy.on_bar(bar)
                except Exception as e:
                    print(f"Strategy {instance.strategy_id} error processing {symbol}: {e}")
        
        if symbol in self._bar_handlers:
            for handler in self._bar_handlers[symbol]:
                try:
                    handler(symbol, bar)
                except Exception as e:
                    print(f"Bar handler error for {symbol}: {e}")
    
    def register_bar_handler(
        self,
        strategy_id: str,
        handler: Callable[[str, DailyBar], None]
    ) -> None:
        """Register bar handler
        
        Registers a bar processing callback for a specific strategy.
        
        Args:
            strategy_id: Strategy ID
            handler: Bar handler callback
        """
        with self._lock:
            if strategy_id not in self._strategies:
                raise KeyError(f"Strategy not found: {strategy_id}")
            
            instance = self._strategies[strategy_id]
            
            for symbol in instance.symbols:
                if symbol not in self._bar_handlers:
                    self._bar_handlers[symbol] = []
                self._bar_handlers[symbol].append(handler)
    
    def get_strategy_context(self, strategy_id: str) -> StrategyContext:
        """Get strategy context
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Strategy context object
            
        Raises:
            KeyError: If strategy does not exist
        """
        with self._lock:
            if strategy_id not in self._strategies:
                raise KeyError(f"Strategy not found: {strategy_id}")
            
            return self._strategies[strategy_id].context
    
    def get_strategy_positions(self, strategy_id: str) -> Dict[str, Position]:
        """Get strategy positions
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Position dict, key is symbol, value is position info
            
        Raises:
            KeyError: If strategy does not exist
        """
        return self.get_strategy_context(strategy_id).positions
    
    def get_strategy_orders(self, strategy_id: str) -> List[Order]:
        """Get strategy orders
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Order list
            
        Raises:
            KeyError: If strategy does not exist
        """
        return self.get_strategy_context(strategy_id).orders
    
    def get_strategy_trades(self, strategy_id: str) -> List[Trade]:
        """Get strategy trades
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Trade list
            
        Raises:
            KeyError: If strategy does not exist
        """
        return self.get_strategy_context(strategy_id).trades
    
    @property
    def trading_service(self) -> TradingService:
        """Get trading service"""
        return self._trading_service
    
    @property
    def data_api(self) -> DataAPI:
        """Get data API"""
        return self._data_api