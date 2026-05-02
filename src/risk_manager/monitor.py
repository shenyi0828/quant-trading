"""持仓监控与预警模块

提供持仓监控、止损止盈等功能
"""
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Dict, List, Optional, Callable

from strategy_engine.types import Position, Direction


class AlertType(Enum):
    """预警类型"""
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    POSITION_WARNING = "position_warning"
    LOSS_WARNING = "loss_warning"
    CONCENTRATION_WARNING = "concentration_warning"


@dataclass
class Alert:
    """预警信息"""
    alert_type: AlertType
    symbol: str
    message: str
    trigger_price: float
    current_price: float
    timestamp: date
    details: Dict = field(default_factory=dict)


@dataclass
class StopLossConfig:
    """止损配置"""
    symbol: str
    stop_loss_price: Optional[float] = None
    stop_loss_ratio: Optional[float] = None  # 相对于成本价的跌幅
    take_profit_price: Optional[float] = None
    take_profit_ratio: Optional[float] = None  # 相对于成本价的涨幅
    trailing_stop_ratio: Optional[float] = None  # 移动止损比例


class StopLossTakeProfit:
    """止损止盈引擎
    
    MVP阶段预留接口，后续完善
    
    功能：
    - 固定止损：价格跌破设定值触发
    - 比例止损：跌幅超过设定比例触发
    - 固定止盈：价格涨到设定值触发
    - 比例止盈：涨幅超过设定比例触发
    - 移动止损：随价格上涨动态调整止损位
    
    Example:
        sltp = StopLossTakeProfit()
        sltp.set_stop_loss("000001", stop_loss_ratio=0.1)  # 10%止损
        sltp.set_take_profit("000001", take_profit_ratio=0.2)  # 20%止盈
        
        alerts = sltp.check_positions(positions, current_prices)
    """
    
    def __init__(self):
        self._configs: Dict[str, StopLossConfig] = {}
        self._highest_prices: Dict[str, float] = {}
    
    def set_stop_loss(
        self,
        symbol: str,
        stop_loss_price: Optional[float] = None,
        stop_loss_ratio: Optional[float] = None
    ):
        """设置止损"""
        config = self._get_or_create_config(symbol)
        config.stop_loss_price = stop_loss_price
        config.stop_loss_ratio = stop_loss_ratio
    
    def set_take_profit(
        self,
        symbol: str,
        take_profit_price: Optional[float] = None,
        take_profit_ratio: Optional[float] = None
    ):
        """设置止盈"""
        config = self._get_or_create_config(symbol)
        config.take_profit_price = take_profit_price
        config.take_profit_ratio = take_profit_ratio
    
    def set_trailing_stop(self, symbol: str, trailing_ratio: float):
        """设置移动止损"""
        config = self._get_or_create_config(symbol)
        config.trailing_stop_ratio = trailing_ratio
    
    def remove_config(self, symbol: str):
        """移除配置"""
        if symbol in self._configs:
            del self._configs[symbol]
        if symbol in self._highest_prices:
            del self._highest_prices[symbol]
    
    def get_config(self, symbol: str) -> Optional[StopLossConfig]:
        """获取配置"""
        return self._configs.get(symbol)
    
    def _get_or_create_config(self, symbol: str) -> StopLossConfig:
        if symbol not in self._configs:
            self._configs[symbol] = StopLossConfig(symbol=symbol)
        return self._configs[symbol]
    
    def _calculate_stop_loss_price(self, position: Position, config: StopLossConfig) -> Optional[float]:
        """计算止损价格"""
        if config.stop_loss_price:
            return config.stop_loss_price
        if config.stop_loss_ratio and position.avg_cost:
            return position.avg_cost * (1 - config.stop_loss_ratio)
        return None
    
    def _calculate_take_profit_price(self, position: Position, config: StopLossConfig) -> Optional[float]:
        """计算止盈价格"""
        if config.take_profit_price:
            return config.take_profit_price
        if config.take_profit_ratio and position.avg_cost:
            return position.avg_cost * (1 + config.take_profit_ratio)
        return None
    
    def _update_trailing_stop(self, symbol: str, current_price: float, config: StopLossConfig):
        """更新移动止损"""
        if config.trailing_stop_ratio:
            highest = self._highest_prices.get(symbol, current_price)
            if current_price > highest:
                self._highest_prices[symbol] = current_price
    
    def check_positions(
        self,
        positions: Dict[str, Position],
        current_prices: Dict[str, float],
        current_date: date
    ) -> List[Alert]:
        """检查所有持仓是否触发止损止盈"""
        alerts = []
        
        for symbol, position in positions.items():
            if position.direction != Direction.LONG:
                continue
            
            config = self._configs.get(symbol)
            if not config:
                continue
            
            current_price = current_prices.get(symbol, position.current_price)
            self._update_trailing_stop(symbol, current_price, config)
            
            stop_loss_price = self._calculate_stop_loss_price(position, config)
            if stop_loss_price and current_price <= stop_loss_price:
                alerts.append(Alert(
                    alert_type=AlertType.STOP_LOSS,
                    symbol=symbol,
                    message=f"Stop loss triggered: {symbol} at {current_price:.2f} (stop: {stop_loss_price:.2f})",
                    trigger_price=stop_loss_price,
                    current_price=current_price,
                    timestamp=current_date,
                    details={
                        "avg_cost": position.avg_cost,
                        "stop_loss_ratio": config.stop_loss_ratio
                    }
                ))
            
            take_profit_price = self._calculate_take_profit_price(position, config)
            if take_profit_price and current_price >= take_profit_price:
                alerts.append(Alert(
                    alert_type=AlertType.TAKE_PROFIT,
                    symbol=symbol,
                    message=f"Take profit triggered: {symbol} at {current_price:.2f} (target: {take_profit_price:.2f})",
                    trigger_price=take_profit_price,
                    current_price=current_price,
                    timestamp=current_date,
                    details={
                        "avg_cost": position.avg_cost,
                        "take_profit_ratio": config.take_profit_ratio
                    }
                ))
        
        return alerts


class PositionMonitor:
    """持仓监控器
    
    提供持仓监控、预警通知等功能
    
    Example:
        monitor = PositionMonitor()
        monitor.set_warning_threshold(loss_ratio=0.05)  # 5%亏损预警
        monitor.set_position_warning_threshold(weight=0.3)  # 单股超30%预警
        
        alerts = monitor.monitor(positions, context)
    """
    
    def __init__(self):
        self._loss_warning_ratio: float = 0.05
        self._position_warning_weight: float = 0.3
        self._callbacks: List[Callable[[Alert], None]] = []
        self._stop_loss_engine: StopLossTakeProfit = StopLossTakeProfit()
    
    def set_warning_threshold(self, loss_ratio: float):
        """设置亏损预警阈值"""
        self._loss_warning_ratio = loss_ratio
    
    def set_position_warning_threshold(self, weight: float):
        """设置单股仓位预警阈值"""
        self._position_warning_weight = weight
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """添加预警回调"""
        self._callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[Alert], None]):
        """移除预警回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def get_stop_loss_engine(self) -> StopLossTakeProfit:
        """获取止损止盈引擎"""
        return self._stop_loss_engine
    
    def monitor(
        self,
        positions: Dict[str, Position],
        context,
        current_prices: Optional[Dict[str, float]] = None,
        current_date: Optional[date] = None
    ) -> List[Alert]:
        alerts = []
        
        if current_prices is None:
            current_prices = {s: p.current_price for s, p in positions.items()}
        
        if current_date is None:
            current_date = context.current_date or date.today()
        
        total_value = context.total_value
        
        for symbol, position in positions.items():
            if position.quantity <= 0:
                continue
            
            current_price = current_prices.get(symbol, position.current_price)
            
            position_weight = position.market_value / total_value if total_value > 0 else 0
            if position_weight > self._position_warning_weight:
                alerts.append(Alert(
                    alert_type=AlertType.POSITION_WARNING,
                    symbol=symbol,
                    message=f"Position weight too high: {symbol} at {position_weight:.2%} (threshold: {self._position_warning_weight:.2%})",
                    trigger_price=position.avg_cost,
                    current_price=current_price,
                    timestamp=current_date,
                    details={
                        "weight": position_weight,
                        "threshold": self._position_warning_weight,
                        "market_value": position.market_value
                    }
                ))
            
            if position.profit < 0:
                loss_ratio = abs(position.profit) / (position.avg_cost * position.quantity)
                if loss_ratio > self._loss_warning_ratio:
                    alerts.append(Alert(
                        alert_type=AlertType.LOSS_WARNING,
                        symbol=symbol,
                        message=f"Position loss warning: {symbol} loss {loss_ratio:.2%} (threshold: {self._loss_warning_ratio:.2%})",
                        trigger_price=position.avg_cost,
                        current_price=current_price,
                        timestamp=current_date,
                        details={
                            "loss_ratio": loss_ratio,
                            "threshold": self._loss_warning_ratio,
                            "profit": position.profit
                        }
                    ))
        
        sltp_alerts = self._stop_loss_engine.check_positions(positions, current_prices, current_date)
        alerts.extend(sltp_alerts)
        
        for alert in alerts:
            for callback in self._callbacks:
                callback(alert)
        
        return alerts
    
    def __repr__(self) -> str:
        return f"PositionMonitor(loss_warning={self._loss_warning_ratio:.2%}, position_warning={self._position_warning_weight:.2%})"