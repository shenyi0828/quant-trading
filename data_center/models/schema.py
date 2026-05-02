"""数据存储模型"""
from datetime import date, datetime
from typing import Optional
from sqlalchemy import Column, String, Float, Date, Boolean, Integer, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

Base = declarative_base()


class Stock(Base):
    """股票基本信息表"""
    __tablename__ = "stocks"
    
    code = Column(String(6), primary_key=True)
    name = Column(String(50), nullable=False)
    exchange = Column(String(2), nullable=False)
    list_date = Column(Date, nullable=True)
    industry = Column(String(50), nullable=True)
    market_cap = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_stocks_exchange", "exchange"),
    )


class DailyBar(Base):
    """日K线数据表"""
    __tablename__ = "daily_bars"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(6), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    amount = Column(Float, nullable=True)
    turnover_rate = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_daily_bars_symbol_date", "symbol", "date", unique=True),
        Index("idx_daily_bars_date", "date"),
    )


class TradingDay(Base):
    """交易日历表"""
    __tablename__ = "trading_days"
    
    date = Column(Date, primary_key=True)
    is_trading = Column(Boolean, nullable=False)
    is_weekend = Column(Boolean, nullable=False)
    is_holiday = Column(Boolean, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_trading_days_is_trading", "is_trading"),
    )


def init_database(db_path: str) -> sessionmaker:
    """初始化数据库连接和表结构"""
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def get_session(session_factory: sessionmaker) -> Session:
    """获取数据库会话"""
    return session_factory()