"""AKShare 数据源适配器"""
import os
import time
from datetime import date, datetime, timedelta
from typing import List, Optional
import pandas as pd

os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)

try:
    import akshare as ak
except ImportError:
    raise ImportError("请安装 akshare: pip install akshare")

from data_center.interfaces.data_source import (
    StockInfo, DailyBar, TradingCalendar, BaseDataSource
)
from data_center.config import Config


class AKShareSource(BaseDataSource):
    """AKShare 数据源实现"""
    
    def __init__(self):
        self.timeout = Config.AKSHARE_REQUEST_TIMEOUT
        self.max_retries = Config.AKSHARE_MAX_RETRIES
    
    def _retry_request(self, func, *args, **kwargs):
        """带重试的请求"""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # 指数退避
    
    def get_stock_list(self) -> List[StockInfo]:
        """获取 A 股股票列表"""
        stocks = []
        
        try:
            df_sh = self._retry_request(ak.stock_info_sh_name_code, symbol="主板A股")
            for _, row in df_sh.iterrows():
                code = str(row.get("证券代码", row.get("code", ""))).strip()
                name = str(row.get("证券简称", row.get("name", ""))).strip()
                if code and name:
                    stocks.append(StockInfo(
                        code=self.normalize_symbol(code),
                        name=name,
                        exchange="SH"
                    ))
        except Exception:
            pass
        
        try:
            df_sh_kcb = self._retry_request(ak.stock_info_sh_name_code, symbol="科创板")
            for _, row in df_sh_kcb.iterrows():
                code = str(row.get("证券代码", row.get("code", ""))).strip()
                name = str(row.get("证券简称", row.get("name", ""))).strip()
                if code and name:
                    stocks.append(StockInfo(
                        code=self.normalize_symbol(code),
                        name=name,
                        exchange="SH"
                    ))
        except Exception:
            pass
        
        try:
            df_sz = self._retry_request(ak.stock_info_sz_name_code, symbol="A股列表")
            for _, row in df_sz.iterrows():
                code = str(row.get("A股代码", row.get("code", ""))).strip()
                name = str(row.get("A股简称", row.get("name", ""))).strip()
                if code and name:
                    stocks.append(StockInfo(
                        code=self.normalize_symbol(code),
                        name=name,
                        exchange="SZ"
                    ))
        except Exception:
            pass
        
        return stocks
    
    def get_daily_bars(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date
    ) -> List[DailyBar]:
        """获取日K线数据"""
        symbol = self.normalize_symbol(symbol)
        exchange = self.get_exchange(symbol)
        ak_symbol = f"{exchange.lower()}{symbol}"
        
        try:
            df = self._retry_request(
                ak.stock_zh_a_hist,
                symbol=ak_symbol,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust=""  # 不复权
            )
            
            bars = []
            for _, row in df.iterrows():
                try:
                    bar_date = datetime.strptime(str(row["日期"]), "%Y-%m-%d").date()
                    bars.append(DailyBar(
                        symbol=symbol,
                        date=bar_date,
                        open=float(row["开盘"]),
                        high=float(row["最高"]),
                        low=float(row["最低"]),
                        close=float(row["收盘"]),
                        volume=float(row["成交量"]),
                        amount=float(row.get("成交额", 0)),
                        turnover_rate=float(row.get("换手率", 0)) if "换手率" in row else None
                    ))
                except (ValueError, KeyError):
                    continue
            
            return bars
        except Exception as e:
            raise RuntimeError(f"获取 {symbol} K线数据失败: {e}")
    
    def get_trading_calendar(self, year: Optional[int] = None) -> List[TradingCalendar]:
        """获取交易日历"""
        year = year or datetime.now().year
        
        try:
            df = self._retry_request(ak.tool_trade_date_hist_sina)
            trade_dates = set()
            for d in df["trade_date"].tolist():
                try:
                    trade_dates.add(datetime.strptime(str(d), "%Y-%m-%d").date())
                except ValueError:
                    continue
            
            calendar = []
            start = date(year, 1, 1)
            end = date(year, 12, 31)
            
            current = start
            while current <= end:
                is_trading = current in trade_dates
                is_weekend = current.weekday() >= 5
                
                calendar.append(TradingCalendar(
                    date=current,
                    is_trading=is_trading,
                    is_weekend=is_weekend,
                    is_holiday=not is_trading and not is_weekend
                ))
                current += timedelta(days=1)
            
            return calendar
        except Exception as e:
            raise RuntimeError(f"获取交易日历失败: {e}")
    
    def is_trading_day(self, date: date) -> bool:
        """判断是否为交易日"""
        try:
            df = self._retry_request(ak.tool_trade_date_hist_sina)
            trade_dates = set()
            for d in df["trade_date"].tolist():
                try:
                    trade_dates.add(datetime.strptime(str(d), "%Y-%m-%d").date())
                except ValueError:
                    continue
            return date in trade_dates
        except Exception:
            return date.weekday() < 5  # 失败时简单判断非周末