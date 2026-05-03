"""AKShare 实时行情推送

基于定时器轮询的占位实现，用于演示和测试。
实际生产环境应使用 WebSocket 接入实时数据源。
"""
import threading
import time
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional

from data_center.realtime.feed import MarketDataFeed, TickData


class AKShareFeed(MarketDataFeed):
    """AKShare 实时行情（占位实现）
    
    使用定时轮询模拟实时推送:
    - 每 interval_seconds 秒获取一次行情
    - 通过回调推送 Tick 数据
    
    注意: 这是占位实现，实际 WebSocket 接入需要:
    - 接入券商/交易所实时数据接口
    - 或使用第三方数据服务商 WebSocket API
    """
    
    name: str = "akshare_feed"
    
    def __init__(self, interval_seconds: int = 3):
        self._interval = interval_seconds
        self._connected = False
        self._subscribed_symbols: List[str] = []
        self._poll_thread: Optional[threading.Thread] = None
        self._running = False
        
        self._tick_callbacks: List[Callable[[TickData], None]] = []
        self._bar_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._error_callbacks: List[Callable[[str], None]] = []
        
        self._last_prices: Dict[str, float] = {}
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """连接（初始化）"""
        self._connected = True
        return True
    
    def disconnect(self) -> bool:
        """断开连接"""
        self.stop_polling()
        self._connected = False
        return True
    
    def is_connected(self) -> bool:
        return self._connected
    
    def subscribe(self, symbols: List[str]) -> bool:
        """订阅行情"""
        if not self._connected:
            return False
        
        for symbol in symbols:
            if symbol not in self._subscribed_symbols:
                self._subscribed_symbols.append(symbol)
        
        if not self._running:
            self.start_polling()
        
        return True
    
    def unsubscribe(self, symbols: List[str]) -> bool:
        """取消订阅"""
        for symbol in symbols:
            if symbol in self._subscribed_symbols:
                self._subscribed_symbols.remove(symbol)
        
        if not self._subscribed_symbols:
            self.stop_polling()
        
        return True
    
    def get_subscribed_symbols(self) -> List[str]:
        return self._subscribed_symbols.copy()
    
    def start_polling(self):
        """启动轮询线程"""
        if self._running:
            return
        
        self._running = True
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()
    
    def stop_polling(self):
        """停止轮询"""
        self._running = False
        if self._poll_thread:
            self._poll_thread.join(timeout=2)
            self._poll_thread = None
    
    def register_tick_callback(self, callback: Callable[[TickData], None]):
        self._tick_callbacks.append(callback)
    
    def register_bar_callback(self, callback: Callable[[Dict[str, Any]], None]):
        self._bar_callbacks.append(callback)
    
    def register_error_callback(self, callback: Callable[[str], None]):
        self._error_callbacks.append(callback)
    
    def _poll_loop(self):
        """轮询循环"""
        while self._running:
            try:
                self._fetch_and_emit()
            except Exception as e:
                self._emit_error(f"Poll error: {e}")
            
            time.sleep(self._interval)
    
    def _fetch_and_emit(self):
        """获取行情并推送"""
        for symbol in self._subscribed_symbols:
            tick = self._fetch_tick(symbol)
            if tick:
                self._emit_tick(tick)
    
    def _fetch_tick(self, symbol: str) -> Optional[TickData]:
        """获取单个标的的 Tick 数据
        
        占位实现 - 使用模拟数据
        实际实现应调用 AKShare 或 WebSocket API
        """
        try:
            last_price = self._last_prices.get(symbol, 10.0)
            
            mock_price = last_price + (time.time() % 10 - 5) * 0.01
            
            self._last_prices[symbol] = mock_price
            
            return TickData(
                symbol=symbol,
                exchange="SH" if symbol[:3] in ("600", "601", "603") else "SZ",
                timestamp=datetime.now(),
                price=mock_price,
                volume=1000,
                turnover=mock_price * 1000,
                bid_price=mock_price - 0.01,
                bid_volume=500,
                ask_price=mock_price + 0.01,
                ask_volume=500,
                last_price=last_price,
            )
        except Exception:
            return None
    
    def _emit_tick(self, tick: TickData):
        """推送 Tick"""
        for callback in self._tick_callbacks:
            try:
                callback(tick)
            except Exception as e:
                self._emit_error(f"Callback error: {e}")
    
    def _emit_error(self, error_msg: str):
        """推送错误"""
        for callback in self._error_callbacks:
            try:
                callback(error_msg)
            except Exception:
                pass