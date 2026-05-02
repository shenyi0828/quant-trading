"""数据源接口定义"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional, Protocol
import pandas as pd


@dataclass
class StockInfo:
    """股票基本信息"""
    code: str  # 股票代码 (如: 000001)
    name: str  # 股票名称
    exchange: str  # 交易所 (SH: 上海, SZ: 深圳)
    list_date: Optional[date] = None  # 上市日期
    industry: Optional[str] = None  # 所属行业
    market_cap: Optional[float] = None  # 总市值 (元)


@dataclass
class DailyBar:
    """日K线数据 (OHLCV)"""
    symbol: str  # 股票代码
    date: date  # 交易日期
    open: float  # 开盘价
    high: float  # 最高价
    low: float  # 最低价
    close: float  # 收盘价
    volume: float  # 成交量 (手)
    amount: Optional[float] = None  # 成交额 (元)
    turnover_rate: Optional[float] = None  # 换手率 (%)


@dataclass
class TradingCalendar:
    """交易日历"""
    date: date  # 日期
    is_trading: bool  # 是否为交易日
    is_weekend: bool  # 是否为周末
    is_holiday: bool  # 是否为节假日


class IDataSource(Protocol):
    """数据源接口 - 支持多种数据源扩展"""
    
    def get_stock_list(self) -> List[StockInfo]:
        """获取 A 股股票列表
        
        Returns:
            股票基本信息列表
        """
        ...
    
    def get_daily_bars(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date
    ) -> List[DailyBar]:
        """获取日K线数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            日K线数据列表
        """
        ...
    
    def get_trading_calendar(
        self, 
        year: Optional[int] = None
    ) -> List[TradingCalendar]:
        """获取交易日历
        
        Args:
            year: 年份 (默认当前年份)
            
        Returns:
            交易日历列表
        """
        ...
    
    def is_trading_day(self, date: date) -> bool:
        """判断是否为交易日
        
        Args:
            date: 日期
            
        Returns:
            是否为交易日
        """
        ...


class BaseDataSource(ABC):
    """数据源基类 - 提供通用工具方法"""
    
    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """标准化股票代码 (去除前缀)"""
        # 移除可能的前缀 (sh, sz, SH, SZ 等)
        symbol = symbol.lower().replace("sh", "").replace("sz", "")
        return symbol.zfill(6)  # 补齐 6 位
    
    @staticmethod
    def get_exchange(symbol: str) -> str:
        """根据股票代码判断交易所"""
        code = symbol[:3]
        # 上海交易所: 600, 601, 603, 688 (科创板)
        if code in ("600", "601", "603", "688"):
            return "SH"
        # 深圳交易所: 000, 001, 002, 003, 300 (创业板)
        elif code in ("000", "001", "002", "003", "300"):
            return "SZ"
        else:
            return "SZ"  # 默认深圳