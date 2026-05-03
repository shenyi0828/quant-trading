"""实时行情推送接口

MarketDataFeed 定义实时行情推送的标准接口，
支持 WebSocket、UDP 等多种推送方式。
"""
from abc import ABC, abstractmethod
from typing import List, Callable, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TickData:
    """Tick 数据结构"""
    symbol: str
    exchange: str
    timestamp: datetime
    price: float
    volume: float
    turnover: float = 0.0
    open_interest: float = 0.0  # 期货持仓量
    bid_price: float = 0.0
    bid_volume: float = 0.0
    ask_price: float = 0.0
    ask_volume: float = 0.0
    last_price: float = 0.0
    high: float = 0.0
    low: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "exchange": self.exchange,
            "timestamp": self.timestamp.isoformat(),
            "price": self.price,
            "volume": self.volume,
            "turnover": self.turnover,
            "bid_price": self.bid_price,
            "bid_volume": self.bid_volume,
            "ask_price": self.ask_price,
            "ask_volume": self.ask_volume,
        }


class MarketDataFeed(ABC):
    """实时行情推送抽象基类
    
    所有实时数据源必须实现此接口:
    - connect(): 连接数据源
    - disconnect(): 断开连接
    - subscribe():订阅行情
    - unsubscribe(): 取消订阅
    
    回调机制:
    - on_tick(): Tick 数据回调
    - on_bar(): Bar 数据回调
    - on_error(): 错误回调
    """
    
    name: str = ""
    
    @abstractmethod
    def connect(self, config: Dict[str, Any]) -> bool:
        """连接数据源
        
        Args:
            config: 连接配置
            
        Returns:
            是否成功连接
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """断开连接"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """检查连接状态"""
        pass
    
    @abstractmethod
    def subscribe(self, symbols: List[str]) -> bool:
        """订阅行情
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            是否成功订阅
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, symbols: List[str]) -> bool:
        """取消订阅"""
        pass
    
    @abstractmethod
    def get_subscribed_symbols(self) -> List[str]:
        """获取已订阅的代码列表"""
        pass
    
    def register_tick_callback(self, callback: Callable[[TickData], None]):
        """注册 Tick 数据回调"""
        self._tick_callbacks.append(callback)
    
    def register_bar_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """注册 Bar 数据回调"""
        self._bar_callbacks.append(callback)
    
    def register_error_callback(self, callback: Callable[[str], None]):
        """注册错误回调"""
        self._error_callbacks.append(callback)
    
    _tick_callbacks: List[Callable[[TickData], None]] = []
    _bar_callbacks: List[Callable[[Dict[str, Any]], None]] = []
    _error_callbacks: List[Callable[[str], None]] = []
    
    def _emit_tick(self, tick: TickData):
        """推送 Tick 数据"""
        for callback in self._tick_callbacks:
            try:
                callback(tick)
            except Exception as e:
                self._emit_error(f"Tick callback error: {e}")
    
    def _emit_bar(self, bar: Dict[str, Any]):
        """推送 Bar 数据"""
        for callback in self._bar_callbacks:
            try:
                callback(bar)
            except Exception as e:
                self._emit_error(f"Bar callback error: {e}")
    
    def _emit_error(self, error_msg: str):
        """推送错误信息"""
        for callback in self._error_callbacks:
            try:
                callback(error_msg)
            except Exception:
                pass