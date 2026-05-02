"""数据查询 API"""
from datetime import date, datetime
from typing import List, Optional

from data_center.interfaces.data_source import StockInfo, DailyBar, TradingCalendar
from data_center.sources.akshare_source import AKShareSource
from data_center.storage.sqlite_storage import DataStorage
from data_center.config import Config


class DataAPI:
    """数据中心对外 API"""
    
    def __init__(self):
        self.source = AKShareSource()
        self.storage = DataStorage()
    
    def initialize(self) -> None:
        """初始化数据 (同步股票列表和交易日历)"""
        print("正在同步股票列表...")
        stocks = self.source.get_stock_list()
        self.storage.save_stocks(stocks)
        print(f"已同步 {len(stocks)} 只股票")
        
        print("正在同步交易日历...")
        current_year = datetime.now().year
        calendar = self.source.get_trading_calendar(current_year)
        self.storage.save_trading_calendar(calendar)
        print(f"已同步 {current_year} 年交易日历")
    
    def list_stocks(self, exchange: Optional[str] = None) -> List[StockInfo]:
        """获取 A 股股票列表
        
        Args:
            exchange: 交易所筛选 (SH/SZ), 默认全部
        
        Returns:
            股票信息列表
        """
        stocks = self.storage.list_stocks(exchange=exchange)
        if not stocks:
            stocks = self.source.get_stock_list()
            self.storage.save_stocks(stocks)
            stocks = self.storage.list_stocks(exchange=exchange)
        return stocks
    
    def get_daily_bar(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date
    ) -> List[DailyBar]:
        """获取日K线数据
        
        Args:
            symbol: 股票代码 (6位数字)
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            日K线数据列表 (OHLCV)
        """
        bars = self.storage.get_daily_bars(symbol, start_date, end_date)
        if not bars:
            bars = self.source.get_daily_bars(symbol, start_date, end_date)
            self.storage.save_daily_bars(bars)
        return bars
    
    def sync_daily_bars(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date,
        force: bool = False
    ) -> int:
        """同步日K线数据到本地
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            force: 强制重新获取
        
        Returns:
            同步的数据条数
        """
        if not force:
            existing = self.storage.get_daily_bars(symbol, start_date, end_date)
            if existing:
                return len(existing)
        
        bars = self.source.get_daily_bars(symbol, start_date, end_date)
        return self.storage.save_daily_bars(bars)
    
    def is_trading_day(self, date: date) -> bool:
        """判断是否为交易日
        
        Args:
            date: 查询日期
        
        Returns:
            是否为交易日
        """
        result = self.storage.is_trading_day(date)
        if not result and date.weekday() < 5:
            calendar = self.source.get_trading_calendar(date.year)
            self.storage.save_trading_calendar(calendar)
            return self.storage.is_trading_day(date)
        return result
    
    def get_trading_days(
        self, 
        year: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[TradingCalendar]:
        """获取交易日历
        
        Args:
            year: 年份 (默认当前年份)
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            交易日历列表
        """
        calendar = self.storage.get_trading_days(year, start_date, end_date)
        if not calendar:
            target_year = year or (start_date.year if start_date else datetime.now().year)
            calendar = self.source.get_trading_calendar(target_year)
            self.storage.save_trading_calendar(calendar)
            calendar = self.storage.get_trading_days(year, start_date, end_date)
        return calendar
    
    def get_last_trading_day(self, before: Optional[date] = None) -> Optional[date]:
        """获取最近的交易日
        
        Args:
            before: 截止日期 (默认今天)
        
        Returns:
            最近交易日日期
        """
        before = before or datetime.now().date()
        calendar = self.get_trading_days(year=before.year)
        
        trading_days = [d for d in calendar if d.is_trading and d.date <= before]
        return trading_days[-1].date if trading_days else None