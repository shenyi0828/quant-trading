"""交易网关抽象接口

ExecutionGateway 定义了与交易所/券商对接的标准接口，
参考 VeighNa 的多网关适配器设计，支持不同交易渠道的统一接入。
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime

from execution.models import Order, OrderRequest, Trade, Position, AccountInfo
from execution.types import OrderStatus


class ExecutionGateway(ABC):
    """交易执行网关抽象基类
    
    所有交易网关（实盘、模拟）必须实现此接口。
    网关负责：
    - 连接管理（connect/disconnect）
    - 订单执行（submit/cancel/query）
    - 获取账户/持仓信息
    - 接收市场数据推送（可选）
    """
    
    name: str = ""
    
    @abstractmethod
    def connect(self, config: Dict[str, Any]) -> bool:
        """连接网关
        
        Args:
            config: 网关配置参数
            
        Returns:
            是否成功连接
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """断开网关连接"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """检查网关连接状态"""
        pass
    
    @abstractmethod
    def submit_order(self, order_request: OrderRequest) -> Optional[str]:
        """提交订单
        
        Args:
            order_request: 订单请求
            
        Returns:
            订单ID，如果提交失败返回None
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """撤销订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否成功撤销
        """
        pass
    
    @abstractmethod
    def query_order(self, order_id: str) -> Optional[Order]:
        """查询订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单信息，如果不存在返回None
        """
        pass
    
    @abstractmethod
    def query_orders(self, status: Optional[OrderStatus] = None) -> List[Order]:
        """查询所有订单
        
        Args:
            status: 可选状态过滤
            
        Returns:
            订单列表
        """
        pass
    
    @abstractmethod
    def query_positions(self) -> List[Position]:
        """查询所有持仓"""
        pass
    
    @abstractmethod
    def query_account(self) -> Optional[AccountInfo]:
        """查询账户信息"""
        pass
    
    @abstractmethod
    def query_trades(self, order_id: Optional[str] = None) -> List[Trade]:
        """查询成交记录
        
        Args:
            order_id: 可选订单ID过滤
            
        Returns:
            成交记录列表
        """
        pass
    
    def on_order_status(self, callback: Callable[[Order], None]):
        """注册订单状态回调"""
        self._order_status_callback = callback
    
    def on_trade(self, callback: Callable[[Trade], None]):
        """注册成交回调"""
        self._trade_callback = callback
    
    def on_position(self, callback: Callable[[Position], None]):
        """注册持仓更新回调"""
        self._position_callback = callback
    
    def on_account(self, callback: Callable[[AccountInfo], None]):
        """注册账户更新回调"""
        self._account_callback = callback
    
    _order_status_callback: Optional[Callable[[Order], None]] = None
    _trade_callback: Optional[Callable[[Trade], None]] = None
    _position_callback: Optional[Callable[[Position], None]] = None
    _account_callback: Optional[Callable[[AccountInfo], None]] = None
    
    def _emit_order_status(self, order: Order):
        if self._order_status_callback:
            self._order_status_callback(order)
    
    def _emit_trade(self, trade: Trade):
        if self._trade_callback:
            self._trade_callback(trade)
    
    def _emit_position(self, position: Position):
        if self._position_callback:
            self._position_callback(position)
    
    def _emit_account(self, account: AccountInfo):
        if self._account_callback:
            self._account_callback(account)