"""SQLite 数据存储层"""
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from data_center.models.schema import (
    Stock, DailyBar as DailyBarModel, TradingDay, 
    init_database, get_session
)
from data_center.interfaces.data_source import (
    StockInfo, DailyBar as DailyBarData, TradingCalendar
)
from data_center.config import Config


class DataStorage:
    """数据持久化存储层"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(Config.DATABASE_PATH)
        Config.ensure_directories()
        self.session_factory = init_database(self.db_path)
    
    def _get_session(self) -> Session:
        return get_session(self.session_factory)
    
    # ========== 股票信息 ==========
    
    def save_stocks(self, stocks: List[StockInfo]) -> int:
        """批量保存股票信息"""
        session = self._get_session()
        try:
            for stock in stocks:
                existing = session.query(Stock).filter_by(code=stock.code).first()
                if existing:
                    existing.name = stock.name
                    existing.exchange = stock.exchange
                    existing.list_date = stock.list_date
                    existing.industry = stock.industry
                    existing.market_cap = stock.market_cap
                else:
                    session.add(Stock(
                        code=stock.code,
                        name=stock.name,
                        exchange=stock.exchange,
                        list_date=stock.list_date,
                        industry=stock.industry,
                        market_cap=stock.market_cap
                    ))
            session.commit()
            return len(stocks)
        finally:
            session.close()
    
    def list_stocks(self, exchange: Optional[str] = None) -> List[StockInfo]:
        """获取股票列表"""
        session = self._get_session()
        try:
            query = session.query(Stock)
            if exchange:
                query = query.filter_by(exchange=exchange)
            stocks = query.all()
            return [
                StockInfo(
                    code=s.code,
                    name=s.name,
                    exchange=s.exchange,
                    list_date=s.list_date,
                    industry=s.industry,
                    market_cap=s.market_cap
                )
                for s in stocks
            ]
        finally:
            session.close()
    
    # ========== 日K线数据 ==========
    
    def save_daily_bars(self, bars: List[DailyBarData]) -> int:
        """批量保存日K线数据"""
        session = self._get_session()
        try:
            for bar in bars:
                existing = session.query(DailyBarModel).filter_by(
                    symbol=bar.symbol, date=bar.date
                ).first()
                if existing:
                    existing.open = bar.open
                    existing.high = bar.high
                    existing.low = bar.low
                    existing.close = bar.close
                    existing.volume = bar.volume
                    existing.amount = bar.amount
                    existing.turnover_rate = bar.turnover_rate
                else:
                    session.add(DailyBarModel(
                        symbol=bar.symbol,
                        date=bar.date,
                        open=bar.open,
                        high=bar.high,
                        low=bar.low,
                        close=bar.close,
                        volume=bar.volume,
                        amount=bar.amount,
                        turnover_rate=bar.turnover_rate
                    ))
            session.commit()
            return len(bars)
        finally:
            session.close()
    
    def get_daily_bars(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date
    ) -> List[DailyBarData]:
        """查询日K线数据"""
        session = self._get_session()
        try:
            bars = session.query(DailyBarModel).filter(
                and_(
                    DailyBarModel.symbol == symbol,
                    DailyBarModel.date >= start_date,
                    DailyBarModel.date <= end_date
                )
            ).order_by(DailyBarModel.date).all()
            return [
                DailyBarData(
                    symbol=b.symbol,
                    date=b.date,
                    open=b.open,
                    high=b.high,
                    low=b.low,
                    close=b.close,
                    volume=b.volume,
                    amount=b.amount,
                    turnover_rate=b.turnover_rate
                )
                for b in bars
            ]
        finally:
            session.close()
    
    # ========== 交易日历 ==========
    
    def save_trading_calendar(self, calendar: List[TradingCalendar]) -> int:
        """保存交易日历"""
        session = self._get_session()
        try:
            for day in calendar:
                existing = session.query(TradingDay).filter_by(date=day.date).first()
                if existing:
                    existing.is_trading = day.is_trading
                    existing.is_weekend = day.is_weekend
                    existing.is_holiday = day.is_holiday
                else:
                    session.add(TradingDay(
                        date=day.date,
                        is_trading=day.is_trading,
                        is_weekend=day.is_weekend,
                        is_holiday=day.is_holiday
                    ))
            session.commit()
            return len(calendar)
        finally:
            session.close()
    
    def is_trading_day(self, date: date) -> bool:
        """判断是否为交易日"""
        session = self._get_session()
        try:
            day = session.query(TradingDay).filter_by(date=date).first()
            return day.is_trading if day else False
        finally:
            session.close()
    
    def get_trading_days(
        self, 
        year: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[TradingCalendar]:
        """获取交易日历"""
        session = self._get_session()
        try:
            query = session.query(TradingDay)
            if year:
                query = query.filter(
                    TradingDay.date >= date(year, 1, 1),
                    TradingDay.date <= date(year, 12, 31)
                )
            if start_date:
                query = query.filter(TradingDay.date >= start_date)
            if end_date:
                query = query.filter(TradingDay.date <= end_date)
            
            days = query.order_by(TradingDay.date).all()
            return [
                TradingCalendar(
                    date=d.date,
                    is_trading=d.is_trading,
                    is_weekend=d.is_weekend,
                    is_holiday=d.is_holiday
                )
                for d in days
            ]
        finally:
            session.close()