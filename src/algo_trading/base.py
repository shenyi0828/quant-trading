"""算法基类

BaseAlgo 定义算法的生命周期和回调接口，
子类通过重写 on_tick/on_start 等方法实现具体拆单逻辑。
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from uuid import uuid4

from execution import OrderManager, Direction, Offset, Exchange, OrderType, TimeInForce, Order, Trade
from execution.models import OrderRequest
from algo_trading.types import AlgoStatus, AlgoResult, AlgoInstance, AlgoStatistics, AlgoParams


class BaseAlgo(ABC):
    """算法模板基类
    
    生命周期: init → on_start → on_tick/on_bar → on_order → on_trade → on_stop
    
    子算法需要重写:
    - on_start(): 初始化拆单逻辑
    - on_tick(): 实时价格处理和下单决策
    - on_bar(): K线数据处理（可选）
    
    提供的方法:
    - submit_order(): 提交拆单
    - cancel_all_orders(): 撤销所有活跃订单
    - update_statistics(): 更新执行统计
    """
    
    name: str = "BaseAlgo"
    
    def __init__(
        self,
        params: AlgoParams,
        order_manager: OrderManager,
        on_complete: Optional[Callable[[AlgoResult, AlgoStatistics], None]] = None,
    ):
        self._params = params
        self._order_manager = order_manager
        
        self._algo_id = str(uuid4())
        self._status = AlgoStatus.STOPPED
        self._variables: Dict[str, Any] = {}
        self._statistics = AlgoStatistics(
            algo_id=self._algo_id,
            total_quantity=params.total_quantity
        )
        self._child_orders: Dict[str, str] = {}  # local_id -> gateway_id
        
        self._on_complete_callback = on_complete
        
        self._order_manager.register_order_callback(self._on_order_callback)
        self._order_manager.register_trade_callback(self._on_trade_callback)
        
        self._init()
    
    def _init(self):
        """初始化算法内部状态"""
        self._variables["slice_count"] = 0
        self._variables["filled_total"] = 0
        self._variables["cost_total"] = 0.0
        self._variables["remaining"] = self._params.total_quantity
        self._variables["start_time"] = None
        self._statistics.created_at = datetime.now()
    
    @abstractmethod
    def on_start(self):
        """算法启动时的初始化逻辑
        
        子类在此实现拆单策略的初始化，如计算切片数量、时间间隔等。
        """
        pass
    
    def on_tick(self, tick_data: Dict[str, Any]):
        """处理实时 Tick 数据
        
        Args:
            tick_data: 包含 symbol, price, volume 等字段的字典
        """
        pass
    
    def on_bar(self, bar_data: Dict[str, Any]):
        """处理 Bar/K线数据
        
        Args:
            bar_data: 包含 symbol, open, high, low, close, volume 等字段
        """
        pass
    
    def on_order(self, order: Order):
        """处理订单状态更新
        
        子类可重写此方法实现订单状态变化的响应逻辑。
        """
        pass
    
    def on_trade(self, trade: Trade):
        """处理成交回报
        
        子类可重写此方法实现成交后的补单逻辑（如 Iceberg）。
        """
        pass
    
    def on_stop(self):
        """算法停止时的清理逻辑
        
        撤销所有未完成订单，计算最终统计。
        """
        self.cancel_all_orders()
        self._statistics.end_time = datetime.now()
        if self._statistics.start_time:
            self._statistics.duration_seconds = (
                self._statistics.end_time - self._statistics.start_time
            ).total_seconds()
    
    def on_complete(self, result: AlgoResult):
        """算法完成时的回调
        
        Args:
            result: 完成结果状态
        """
        if self._on_complete_callback:
            self._on_complete_callback(result, self._statistics)
    
    def start(self):
        """启动算法"""
        if self._status != AlgoStatus.STOPPED:
            return
        
        self._status = AlgoStatus.RUNNING
        self._statistics.start_time = datetime.now()
        self._variables["start_time"] = datetime.now()
        
        self.on_start()
    
    def stop(self):
        """停止算法"""
        if self._status == AlgoStatus.STOPPED:
            return
        
        self._status = AlgoStatus.STOPPED
        self.on_stop()
        
        result = self._determine_result()
        self.on_complete(result)
    
    def pause(self):
        """暂停算法"""
        if self._status != AlgoStatus.RUNNING:
            return
        
        self._status = AlgoStatus.PAUSED
        self.cancel_all_orders()
    
    def resume(self):
        """恢复算法"""
        if self._status != AlgoStatus.PAUSED:
            return
        
        self._status = AlgoStatus.RUNNING
    
    def submit_order(
        self,
        quantity: int,
        price: float = 0.0,
        order_type: OrderType = OrderType.LIMIT,
        reference: str = ""
    ) -> Optional[str]:
        """提交拆单
        
        Args:
            quantity: 本次下单数量
            price: 下单价格（0 表示市价）
            order_type: 订单类型
            reference: 参考标识
            
        Returns:
            订单 ID 或 None（失败时）
        """
        if self._status != AlgoStatus.RUNNING:
            return None
        
        if quantity <= 0:
            return None
        
        direction = Direction.LONG if self._params.direction == "buy" else Direction.SHORT
        offset = Offset.OPEN  # 算法交易默认开仓
        
        try:
            exchange = Exchange(self._params.exchange.lower())
        except ValueError:
            exchange = Exchange.SSE
        
        order_id = self._order_manager.create_order(
            symbol=self._params.symbol,
            exchange=exchange,
            direction=direction,
            offset=offset,
            quantity=quantity,
            price=price,
            order_type=order_type,
            time_in_force=TimeInForce.DAY,
            reference=f"{self.name}_{self._algo_id}_{reference}"
        )
        
        if order_id:
            self._child_orders[order_id] = order_id
            self._variables["slice_count"] += 1
            self._statistics.child_orders += 1
            self._statistics.active_orders += 1
        
        return order_id
    
    def cancel_all_orders(self) -> int:
        """撤销所有活跃订单
        
        Returns:
            撤销的订单数量
        """
        cancelled = 0
        for order_id in list(self._child_orders.keys()):
            if self._order_manager.cancel_order(order_id):
                cancelled += 1
        return cancelled
    
    def cancel_order(self, order_id: str) -> bool:
        """撤销指定订单"""
        return self._order_manager.cancel_order(order_id)
    
    def get_statistics(self) -> AlgoStatistics:
        """获取执行统计"""
        return self._statistics
    
    def get_status(self) -> AlgoStatus:
        """获取算法状态"""
        return self._status
    
    def get_instance(self) -> AlgoInstance:
        """获取算法实例信息"""
        return AlgoInstance(
            algo_id=self._algo_id,
            algo_name=self.name,
            algo_type=self.__class__.__name__,
            params=self._params.__dict__,
            status=self._status,
            statistics=self._statistics,
            variables=self._variables,
            created_at=self._statistics.created_at,
            started_at=self._statistics.start_time,
            completed_at=self._statistics.end_time,
        )
    
    def _on_order_callback(self, order: Order):
        """订单状态回调（内部）"""
        if order.order_id not in self._child_orders:
            return
        
        if order.is_completed:
            self._statistics.active_orders -= 1
            
            if order.status.value == "filled":
                self._statistics.completed_orders += 1
            elif order.status.value in ("cancelled", "rejected"):
                self._statistics.rejected_orders += 1
        
        self.on_order(order)
        
        self._check_completion()
    
    def _on_trade_callback(self, trade: Trade):
        """成交回报回调（内部）"""
        if trade.order_id not in self._child_orders:
            return
        
        self._variables["filled_total"] += trade.quantity
        self._variables["cost_total"] += trade.price * trade.quantity
        
        self._statistics.filled_quantity = self._variables["filled_total"]
        self._statistics.total_cost = self._variables["cost_total"]
        
        if self._statistics.filled_quantity > 0:
            self._statistics.avg_price = (
                self._statistics.total_cost / self._statistics.filled_quantity
            )
        
        self.on_trade(trade)
        
        self._check_completion()
    
    def _check_completion(self):
        """检查是否完成目标"""
        if self._statistics.is_complete:
            self._status = AlgoStatus.COMPLETED
            self.on_stop()
            self.on_complete(AlgoResult.SUCCESS)
    
    def _determine_result(self) -> AlgoResult:
        """根据执行情况确定结果状态"""
        if self._statistics.is_complete:
            return AlgoResult.SUCCESS
        elif self._statistics.filled_quantity > 0:
            return AlgoResult.PARTIAL
        elif self._statistics.rejected_orders > 0:
            return AlgoResult.REJECTED
        else:
            return AlgoResult.ERROR
    
    @property
    def algo_id(self) -> str:
        return self._algo_id
    
    @property
    def params(self) -> AlgoParams:
        return self._params
    
    @property
    def remaining(self) -> int:
        return self._params.total_quantity - self._statistics.filled_quantity