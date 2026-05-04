from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any, Type
from uuid import uuid4

from execution import OrderManager, SimGateway, Order, Trade, Position, Direction, OrderStatus
from execution.models import OrderRequest
from execution.types import Exchange, OrderType, TimeInForce, Offset
from risk_manager import RiskChecker, RiskContext, RiskResult, RiskAction
from strategy_engine.types import Order as StrategyOrder
from algo_trading import AlgoEngine, AlgoStatus, AlgoResult, AlgoStatistics, AlgoParams, BaseAlgo
from algo_trading.templates import TWAPAlgo, VWAPAlgo, IcebergAlgo
from algo_trading.types import TWAPParams, VWAPParams, IcebergParams


@dataclass
class TradingServiceSubmitResult:
    order_id: Optional[str] = None
    risk_result: Optional[RiskResult] = None
    accepted: bool = False
    message: str = ""


@dataclass
class AccountInfo:
    account_id: str
    balance: float = 0.0
    available: float = 0.0
    frozen: float = 0.0
    margin: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    positions: Dict[str, Position] = field(default_factory=dict)
    
    @property
    def total_value(self) -> float:
        return self.balance + self.unrealized_pnl


class TradingService:
    
    def __init__(
        self,
        gateway: SimGateway,
        risk_checker: RiskChecker,
        initial_capital: float = 100000.0
    ):
        self._gateway = gateway
        self._risk_checker = risk_checker
        self._initial_capital = initial_capital
        self._order_manager = OrderManager(gateway)
        
        self._account_info = AccountInfo(
            account_id="main",
            balance=initial_capital,
            available=initial_capital
        )
        
        self._daily_orders: List[Order] = []
        self._daily_pnl: float = 0.0
        self._daily_trades: int = 0
        self._current_prices: Dict[str, float] = {}
        
        self._order_callbacks: List[Callable[[Order], None]] = []
        self._trade_callbacks: List[Callable[[Trade], None]] = []
        self._risk_reject_callbacks: List[Callable[[RiskResult], None]] = []
        
        self._order_manager.register_order_callback(self._on_order_status)
        self._order_manager.register_trade_callback(self._on_trade)
        
        self._algo_engine: Optional[AlgoEngine] = None
        self._algo_callbacks: List[Callable[[str, AlgoResult, AlgoStatistics], None]] = []
    
    def register_order_callback(self, callback: Callable[[Order], None]):
        self._order_callbacks.append(callback)
    
    def register_trade_callback(self, callback: Callable[[Trade], None]):
        self._trade_callbacks.append(callback)
    
    def register_risk_reject_callback(self, callback: Callable[[RiskResult], None]):
        self._risk_reject_callbacks.append(callback)
    
    def get_risk_context(self) -> RiskContext:
        positions_dict: Dict[str, Any] = {}
        for pos in self._gateway.query_positions():
            positions_dict[pos.symbol] = pos
        
        return RiskContext(
            total_capital=self._initial_capital,
            available_cash=self._account_info.available,
            initial_capital=self._initial_capital,
            positions=positions_dict,
            daily_pnl=self._daily_pnl,
            daily_trades=self._daily_trades,
            daily_orders=self._daily_orders,
            current_date=datetime.now().date()
        )
    
    def submit_order(self, order_request: OrderRequest) -> TradingServiceSubmitResult:
        risk_context = self.get_risk_context()
        
        dummy_order = StrategyOrder(
            order_id=str(uuid4()),
            symbol=order_request.symbol,
            direction=order_request.direction,
            order_type=order_request.order_type,
            price=order_request.price,
            quantity=order_request.quantity,
            status=OrderStatus.PENDING,
            created_at=datetime.now().date()
        )
        
        risk_report = self._risk_checker.check(dummy_order, risk_context)
        
        if risk_report.is_rejected:
            result = TradingServiceSubmitResult(
                order_id=None,
                risk_result=risk_report.results[0] if risk_report.results else None,
                accepted=False,
                message=f"Order rejected by {risk_report.rejected_by}: {risk_report.rejected_message}"
            )
            for callback in self._risk_reject_callbacks:
                callback(result.risk_result)
            return result
        
        order_id = self._order_manager.create_order(
            symbol=order_request.symbol,
            exchange=order_request.exchange,
            direction=order_request.direction,
            offset=order_request.offset,
            quantity=order_request.quantity,
            price=order_request.price,
            order_type=order_request.order_type,
            time_in_force=order_request.time_in_force,
            reference=order_request.reference
        )
        
        if order_id:
            order = self._order_manager.query_order(order_id)
            if order:
                self._daily_orders.append(order)
                self._daily_trades += 1
        
        return TradingServiceSubmitResult(
            order_id=order_id,
            accepted=order_id is not None,
            message="Order submitted successfully" if order_id else "Failed to submit order"
        )
    
    def cancel_order(self, order_id: str) -> bool:
        return self._order_manager.cancel_order(order_id)
    
    def get_order(self, order_id: str) -> Optional[Order]:
        return self._order_manager.query_order(order_id)
    
    def get_active_orders(self) -> List[Order]:
        return self._order_manager.query_active_orders()
    
    def get_positions(self) -> List[Position]:
        return self._gateway.query_positions()
    
    def get_account_info(self) -> AccountInfo:
        positions = self._gateway.query_positions()
        self._account_info.positions = {pos.symbol: pos for pos in positions}
        
        total_unrealized = sum(
            (pos.current_price - pos.avg_cost) * pos.quantity 
            if pos.direction == Direction.LONG 
            else (pos.avg_cost - pos.current_price) * pos.quantity
            for pos in positions
            if pos.current_price > 0
        )
        self._account_info.unrealized_pnl = total_unrealized

        return self._account_info
    
    def update_market_price(self, symbol: str, price: float):
        self._current_prices[symbol] = price
        self._gateway.set_market_price(symbol, price)
    
    @property
    def algo_engine(self) -> AlgoEngine:
        if self._algo_engine is None:
            self._algo_engine = AlgoEngine(self._order_manager)
        return self._algo_engine
    
    def submit_algo_order(
        self,
        algo_type: str,
        params: AlgoParams,
        on_complete: Optional[Callable[[AlgoResult, AlgoStatistics], None]] = None,
    ) -> Optional[str]:
        algo_class = self._get_algo_class(algo_type)
        if algo_class is None:
            return None
        
        if on_complete is None:
            on_complete = self._default_algo_complete_callback
        
        algo_id = self.algo_engine.register_algo(algo_class, params, on_complete)
        
        self.algo_engine.start_algo(algo_id)
        
        return algo_id
    
    def _get_algo_class(self, algo_type: str) -> Optional[Type[BaseAlgo]]:
        algo_map = {
            "twap": TWAPAlgo,
            "vwap": VWAPAlgo,
            "iceberg": IcebergAlgo,
        }
        return algo_map.get(algo_type.lower())
    
    def register_algo_complete_callback(
        self,
        callback: Callable[[AlgoResult, AlgoStatistics], None]
    ):
        self._algo_callbacks.append(callback)
    
    def _default_algo_complete_callback(
        self,
        result: AlgoResult,
        statistics: AlgoStatistics
    ):
        for callback in self._algo_callbacks:
            callback(result, statistics)
    
    def get_algo_status(self, algo_id: str) -> Optional[AlgoStatus]:
        return self.algo_engine.get_algo_status(algo_id)
    
    def get_algo_statistics(self, algo_id: str) -> Optional[AlgoStatistics]:
        return self.algo_engine.get_algo_statistics(algo_id)
    
    def stop_algo(self, algo_id: str) -> bool:
        return self.algo_engine.stop_algo(algo_id)
    
    def pause_algo(self, algo_id: str) -> bool:
        return self.algo_engine.pause_algo(algo_id)
    
    def resume_algo(self, algo_id: str) -> bool:
        return self.algo_engine.resume_algo(algo_id)
    
    def get_all_algos(self) -> List[Any]:
        return self.algo_engine.get_all_algos()
    
    def _on_order_status(self, order: Order):
        for callback in self._order_callbacks:
            callback(order)
    
    def _on_trade(self, trade: Trade):
        if trade.direction == Direction.LONG:
            cost = trade.price * trade.quantity + trade.commission
            self._account_info.balance -= cost
        else:
            revenue = trade.price * trade.quantity - trade.commission
            self._account_info.balance += revenue
            self._daily_pnl += revenue
        
        self._account_info.available = self._account_info.balance
        
        for callback in self._trade_callbacks:
            callback(trade)