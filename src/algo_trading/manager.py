"""算法订单管理器

AlgoOrderManager 管理算法拆单的生命周期，
跟踪父订单与子订单的关系，提供统计和监控功能。
"""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from execution import Order, Trade
from algo_trading.types import AlgoOrder, AlgoStatistics


class AlgoOrderManager:
    """算法订单管理
    
    管理 TWAP/VWAP/Iceberg 算法拆分的子订单:
    - create_child_order(): 创建子订单记录
    - update_child_order(): 更新子订单状态
    - get_child_orders(): 获取所有子订单
    - get_statistics(): 计算执行统计
    
    父订单与子订单关系:
    - 一个父订单 → 多个子订单（拆单）
    - 子订单独立执行，汇总到父订单统计
    """
    
    def __init__(self, algo_id: str, parent_order_id: str = ""):
        self._algo_id = algo_id
        self._parent_order_id = parent_order_id or str(uuid4())
        
        self._child_orders: Dict[str, AlgoOrder] = {}  # gateway_order_id -> AlgoOrder
        self._order_sequence: List[str] = []  # 保持下单顺序
        
        self._total_target = 0
        self._total_filled = 0
        self._total_cost = 0.0
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None
    
    def set_total_target(self, quantity: int):
        """设置目标总量"""
        self._total_target = quantity
    
    def create_child_order(
        self,
        gateway_order_id: str,
        slice_index: int,
        quantity: int,
        price: float,
    ) -> AlgoOrder:
        """创建子订单记录
        
        Args:
            gateway_order_id: 网关返回的订单 ID
            slice_index: 拆单序号
            quantity: 本次下单数量
            price: 本次下单价格
            
        Returns:
            创建的 AlgoOrder 对象
        """
        algo_order = AlgoOrder(
            algo_id=self._algo_id,
            parent_order_id=self._parent_order_id,
            child_order_id=gateway_order_id,
            slice_index=slice_index,
            quantity=quantity,
            price=price,
            status="submitted",
            created_at=datetime.now(),
        )
        
        self._child_orders[gateway_order_id] = algo_order
        self._order_sequence.append(gateway_order_id)
        
        if not self._start_time:
            self._start_time = datetime.now()
        
        return algo_order
    
    def update_child_order(self, gateway_order_id: str, order: Order):
        """更新子订单状态
        
        Args:
            gateway_order_id: 网关订单 ID
            order: 执行层的 Order 对象
        """
        algo_order = self._child_orders.get(gateway_order_id)
        if not algo_order:
            return
        
        algo_order.filled_quantity = order.filled_quantity
        algo_order.filled_price = order.average_price
        algo_order.status = order.status.value
        
        if order.is_completed:
            algo_order.filled_at = datetime.now()
        
        self._recalculate_totals()
    
    def record_trade(self, trade: Trade):
        """记录成交
        
        Args:
            trade: 执行层的 Trade 对象
        """
        algo_order = self._child_orders.get(trade.order_id)
        if not algo_order:
            return
        
        algo_order.filled_quantity += trade.quantity
        algo_order.filled_price = (
            (algo_order.filled_price * algo_order.filled_quantity + trade.price * trade.quantity)
            / (algo_order.filled_quantity + trade.quantity)
            if algo_order.filled_quantity > 0
            else trade.price
        )
        
        self._recalculate_totals()
    
    def cancel_child_order(self, gateway_order_id: str) -> bool:
        """标记子订单为撤销"""
        algo_order = self._child_orders.get(gateway_order_id)
        if not algo_order:
            return False
        
        algo_order.status = "cancelled"
        algo_order.filled_at = datetime.now()
        return True
    
    def get_child_order(self, gateway_order_id: str) -> Optional[AlgoOrder]:
        """获取单个子订单"""
        return self._child_orders.get(gateway_order_id)
    
    def get_child_orders(self) -> List[AlgoOrder]:
        """获取所有子订单（按下单顺序）"""
        return [
            self._child_orders[order_id]
            for order_id in self._order_sequence
            if order_id in self._child_orders
        ]
    
    def get_active_child_orders(self) -> List[AlgoOrder]:
        """获取活跃子订单（未完成）"""
        return [
            order for order in self.get_child_orders()
            if order.status in ("submitted", "partial", "pending")
        ]
    
    def get_filled_child_orders(self) -> List[AlgoOrder]:
        """获取已完成子订单"""
        return [
            order for order in self.get_child_orders()
            if order.status == "filled"
        ]
    
    def get_statistics(self) -> AlgoStatistics:
        """计算执行统计"""
        active_count = len(self.get_active_child_orders())
        filled_count = len(self.get_filled_child_orders())
        rejected_count = len([
            o for o in self.get_child_orders()
            if o.status in ("cancelled", "rejected")
        ])
        
        duration = 0.0
        if self._start_time:
            end = self._end_time or datetime.now()
            duration = (end - self._start_time).total_seconds()
        
        return AlgoStatistics(
            algo_id=self._algo_id,
            total_quantity=self._total_target,
            filled_quantity=self._total_filled,
            total_cost=self._total_cost,
            child_orders=len(self._child_orders),
            active_orders=active_count,
            completed_orders=filled_count,
            rejected_orders=rejected_count,
            start_time=self._start_time,
            end_time=self._end_time,
            duration_seconds=duration,
        )
    
    def mark_complete(self):
        """标记算法完成"""
        self._end_time = datetime.now()
    
    def _recalculate_totals(self):
        """重新计算总计数据"""
        self._total_filled = 0
        self._total_cost = 0.0
        
        for algo_order in self._child_orders.values():
            if algo_order.filled_quantity > 0:
                self._total_filled += algo_order.filled_quantity
                self._total_cost += algo_order.filled_price * algo_order.filled_quantity
    
    @property
    def algo_id(self) -> str:
        return self._algo_id
    
    @property
    def parent_order_id(self) -> str:
        return self._parent_order_id
    
    @property
    def child_count(self) -> int:
        return len(self._child_orders)
    
    @property
    def is_complete(self) -> bool:
        return self._total_filled >= self._total_target