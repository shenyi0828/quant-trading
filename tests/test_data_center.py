"""Comprehensive pytest tests for the data_center module.

Tests the storage layer, utility functions, and DataAPI with proper mocking
to avoid network dependencies (AKShare).
"""
import tempfile
from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from data_center.interfaces.data_source import (
    StockInfo,
    DailyBar,
    TradingCalendar,
    BaseDataSource,
)
from data_center.storage.sqlite_storage import DataStorage
from data_center.models.schema import init_database


# ========== Fixtures ==========

@pytest.fixture
def in_memory_storage():
    """Create a DataStorage instance backed by an in-memory SQLite DB."""
    storage = DataStorage(db_path=":memory:")
    return storage


@pytest.fixture()
def sample_stocks():
    return [
        StockInfo(code="600000", name="浦发银行", exchange="SH"),
        StockInfo(code="000001", name="平安银行", exchange="SZ"),
        StockInfo(code="600519", name="贵州茅台", exchange="SH"),
        StockInfo(code="000858", name="五粮液", exchange="SZ"),
    ]


@pytest.fixture
def sample_bars():
    return [
        DailyBar(symbol="600000", date=date(2025, 6, 2), open=10.0, high=10.5, low=9.8, close=10.3, volume=100000),
        DailyBar(symbol="600000", date=date(2025, 6, 3), open=10.3, high=10.8, low=10.1, close=10.6, volume=120000),
        DailyBar(symbol="600000", date=date(2025, 6, 4), open=10.6, high=11.0, low=10.4, close=10.9, volume=110000),
        DailyBar(symbol="000001", date=date(2025, 6, 2), open=15.0, high=15.5, low=14.8, close=15.3, volume=200000),
        DailyBar(symbol="000001", date=date(2025, 6, 3), open=15.3, high=15.8, low=15.1, close=15.6, volume=220000),
    ]


@pytest.fixture
def sample_trading_calendar():
    """Sample trading calendar for 2025-06-01 to 2025-06-30."""
    calendar = []
    for day in range(1, 31):
        d = date(2025, 6, day)
        is_weekend = d.weekday() >= 5
        # Weekdays, excluding 10th (holiday)
        is_trading = not is_weekend and day != 10
        calendar.append(TradingCalendar(
            date=d,
            is_trading=is_trading,
            is_weekend=is_weekend,
            is_holiday=not is_trading and not is_weekend,
        ))
    return calendar


# ========== Tests: Utility functions ==========

class TestBaseDataSourceUtils:
    class DummySource(BaseDataSource):
        """Concrete subclass to test static methods."""
        pass

    def test_normalize_symbol_with_prefix(self):
        assert self.DummySource.normalize_symbol("sh600000") == "600000"
        assert self.DummySource.normalize_symbol("sz000001") == "000001"
        assert self.DummySource.normalize_symbol("SH600519") == "600519"

    def test_normalize_symbol_short_code(self):
        """Short codes should be zero-padded to 6 digits."""
        assert self.DummySource.normalize_symbol("1") == "000001"
        assert self.DummySource.normalize_symbol("123") == "000123"

    def test_normalize_symbol_already_norm(self):
        assert self.DummySource.normalize_symbol("600000") == "600000"

    def test_get_exchange_shanghai(self):
        assert self.DummySource.get_exchange("600000") == "SH"
        assert self.DummySource.get_exchange("601000") == "SH"
        assert self.DummySource.get_exchange("603000") == "SH"
        assert self.DummySource.get_exchange("688000") == "SH"

    def test_get_exchange_shenzhen(self):
        assert self.DummySource.get_exchange("000001") == "SZ"
        assert self.DummySource.get_exchange("002000") == "SZ"
        assert self.DummySource.get_exchange("300000") == "SZ"

    def test_get_exchange_unknown_prefix(self):
        assert self.DummySource.get_exchange("999999") == "SZ"  # defaults to SZ


# ========== Tests: DataStorage ==========

class TestDataStorage:
    def test_save_and_list_stocks(self, in_memory_storage, sample_stocks):
        count = in_memory_storage.save_stocks(sample_stocks)
        assert count == 4

        stocks = in_memory_storage.list_stocks()
        assert len(stocks) == 4
        codes = {s.code for s in stocks}
        assert codes == {"600000", "000001", "600519", "000858"}

    def test_list_stocks_by_exchange(self, in_memory_storage, sample_stocks):
        in_memory_storage.save_stocks(sample_stocks)

        sh_stocks = in_memory_storage.list_stocks(exchange="SH")
        assert len(sh_stocks) == 2
        assert all(s.exchange == "SH" for s in sh_stocks)

        sz_stocks = in_memory_storage.list_stocks(exchange="SZ")
        assert len(sz_stocks) == 2
        assert all(s.exchange == "SZ" for s in sz_stocks)

    def test_save_stocks_upsert(self, in_memory_storage):
        """Saving the same code twice should update, not duplicate."""
        stock1 = StockInfo(code="600000", name="浦发银行", exchange="SH")
        stock2 = StockInfo(code="600000", name="浦发银行(更新)", exchange="SH")

        in_memory_storage.save_stocks([stock1])
        in_memory_storage.save_stocks([stock2])

        stocks = in_memory_storage.list_stocks()
        assert len(stocks) == 1
        assert stocks[0].name == "浦发银行(更新)"

    def test_save_and_get_daily_bars(self, in_memory_storage, sample_bars):
        count = in_memory_storage.save_daily_bars(sample_bars)
        assert count == 5

        bars = in_memory_storage.get_daily_bars(
            "600000", date(2025, 6, 2), date(2025, 6, 3)
        )
        assert len(bars) == 2
        assert bars[0].close == 10.3
        assert bars[1].close == 10.6

    def test_get_daily_bars_ordered_by_date(self, in_memory_storage, sample_bars):
        in_memory_storage.save_daily_bars(sample_bars)

        bars = in_memory_storage.get_daily_bars(
            "600000", date(2025, 6, 2), date(2025, 6, 4)
        )
        assert len(bars) == 3
        # Verify ascending date order
        assert bars[0].date < bars[1].date < bars[2].date

    def test_get_daily_bars_by_symbol(self, in_memory_storage, sample_bars):
        in_memory_storage.save_daily_bars(sample_bars)

        bars_000001 = in_memory_storage.get_daily_bars(
            "000001", date(2025, 6, 1), date(2025, 6, 30)
        )
        assert len(bars_000001) == 2
        assert all(b.symbol == "000001" for b in bars_000001)

        bars_600519 = in_memory_storage.get_daily_bars(
            "600519", date(2025, 6, 1), date(2025, 6, 30)
        )
        assert len(bars_600519) == 0

    def test_save_daily_bars_upsert(self, in_memory_storage):
        """Saving the same bar twice should update, not duplicate."""
        bar1 = DailyBar(symbol="600000", date=date(2025, 6, 1), open=10.0, high=10.5, low=9.8, close=10.3, volume=100000)
        bar2 = DailyBar(symbol="600000", date=date(2025, 6, 1), open=10.0, high=10.5, low=9.8, close=11.0, volume=150000)

        in_memory_storage.save_daily_bars([bar1])
        in_memory_storage.save_daily_bars([bar2])

        bars = in_memory_storage.get_daily_bars("600000", date(2025, 6, 1), date(2025, 6, 1))
        assert len(bars) == 1
        assert bars[0].close == 11.0
        assert bars[0].volume == 150000

    def test_save_and_query_trading_calendar(self, in_memory_storage, sample_trading_calendar):
        count = in_memory_storage.save_trading_calendar(sample_trading_calendar)
        assert count == 30

        assert in_memory_storage.is_trading_day(date(2025, 6, 2))  # Monday
        assert not in_memory_storage.is_trading_day(date(2025, 6, 10))  # Holiday
        assert not in_memory_storage.is_trading_day(date(2025, 6, 7))   # Saturday

    def test_get_trading_days_by_year(self, in_memory_storage, sample_trading_calendar):
        in_memory_storage.save_trading_calendar(sample_trading_calendar)

        # No data for 2026
        days_2026 = in_memory_storage.get_trading_days(year=2026)
        assert len(days_2026) == 0

        days_2025 = in_memory_storage.get_trading_days(year=2025)
        assert len(days_2025) == 30

    def test_get_trading_days_by_date_range(self, in_memory_storage, sample_trading_calendar):
        in_memory_storage.save_trading_calendar(sample_trading_calendar)

        days = in_memory_storage.get_trading_days(
            start_date=date(2025, 6, 15), end_date=date(2025, 6, 20)
        )
        assert len(days) == 6
        assert days[0].date == date(2025, 6, 15)
        assert days[-1].date == date(2025, 6, 20)

    def test_is_trading_day_unknown_date_returns_false(self, in_memory_storage):
        """Dates not in the calendar should return False."""
        assert in_memory_storage.is_trading_day(date(2025, 1, 1)) is False

    def test_empty_storage_returns_empty_lists(self, in_memory_storage):
        assert in_memory_storage.list_stocks() == []
        assert in_memory_storage.get_daily_bars("600000", date(2025, 1, 1), date(2025, 12, 31)) == []
        assert in_memory_storage.get_trading_days(year=2025) == []


# ========== Tests: Data models ==========

class TestDataModels:
    def test_stock_info_defaults(self):
        s = StockInfo(code="600000", name="测试", exchange="SH")
        assert s.list_date is None
        assert s.industry is None
        assert s.market_cap is None

    def test_daily_bar_optional_fields(self):
        b = DailyBar(symbol="600000", date=date(2025, 6, 1), open=10.0, high=10.5, low=9.8, close=10.3, volume=100000)
        assert b.amount is None
        assert b.turnover_rate is None

    def test_trading_calendar(self):
        tc = TradingCalendar(date=date(2025, 6, 1), is_trading=True, is_weekend=True, is_holiday=False)
        assert tc.date == date(2025, 6, 1)
        assert tc.is_trading is True
        assert tc.is_weekend is True


# ========== Tests: DataAPI (with mocked AKShare source) ==========

class TestDataAPIMock:
    """Tests DataAPI with a mocked AKShareSource to avoid network calls."""

    def _make_api(self, storage, source):
        """Patch DataAPI to use the given storage and source."""
        from unittest.mock import patch, MagicMock

        api = MagicMock()
        api.storage = storage
        api.source = source
        # Bind the real methods onto the mock
        from data_center.api.data_api import DataAPI
        for attr in ["list_stocks", "get_daily_bar", "sync_daily_bars",
                     "is_trading_day", "get_trading_days", "get_last_trading_day"]:
            setattr(api, attr, getattr(DataAPI, attr).__get__(api, DataAPI))
        return api

    def test_list_stocks_from_storage(self, in_memory_storage, sample_stocks):
        api = self._make_api(in_memory_storage, None)

        in_memory_storage.save_stocks(sample_stocks)
        result = api.list_stocks()
        assert len(result) == 4
        # Source should not be called since storage has data
        assert result[0].code in {"600000", "000001", "600519", "000858"}

    def test_list_stocks_fallback_to_source(self, in_memory_storage):
        """If storage is empty, should fall back to source."""
        mock_source = MagicMock()
        mock_source.get_stock_list.return_value = [
            StockInfo(code="000001", name="平安银行", exchange="SZ"),
        ]
        api = self._make_api(in_memory_storage, mock_source)

        result = api.list_stocks()
        assert len(result) == 1
        assert result[0].code == "000001"
        mock_source.get_stock_list.assert_called_once()
        # Verify data was saved to storage
        assert len(in_memory_storage.list_stocks()) == 1

    def test_list_stocks_exchange_filter(self, in_memory_storage, sample_stocks):
        in_memory_storage.save_stocks(sample_stocks)
        api = self._make_api(in_memory_storage, None)

        sh_stocks = api.list_stocks(exchange="SH")
        assert len(sh_stocks) == 2

    def test_get_daily_bar_from_storage(self, in_memory_storage, sample_bars):
        api = self._make_api(in_memory_storage, None)
        in_memory_storage.save_daily_bars(sample_bars)

        bars = api.get_daily_bar("600000", date(2025, 6, 2), date(2025, 6, 3))
        assert len(bars) == 2
        assert bars[0].close == 10.3

    def test_get_daily_bar_fallback_to_source(self, in_memory_storage):
        mock_source = MagicMock()
        mock_source.get_daily_bars.return_value = [
            DailyBar(symbol="600000", date=date(2025, 6, 2), open=10.0, high=10.5, low=9.8, close=10.3, volume=100000),
        ]
        api = self._make_api(in_memory_storage, mock_source)

        bars = api.get_daily_bar("600000", date(2025, 6, 2), date(2025, 6, 2))
        assert len(bars) == 1
        mock_source.get_daily_bars.assert_called_once()
        # Verify data was saved to storage
        cached = in_memory_storage.get_daily_bars("600000", date(2025, 6, 2), date(2025, 6, 2))
        assert len(cached) == 1

    def test_is_trading_day_from_storage(self, in_memory_storage, sample_trading_calendar):
        api = self._make_api(in_memory_storage, None)
        in_memory_storage.save_trading_calendar(sample_trading_calendar)

        assert api.is_trading_day(date(2025, 6, 2)) is True
        assert api.is_trading_day(date(2025, 6, 7)) is False

    def test_get_trading_days_fallback_to_source(self, in_memory_storage):
        mock_source = MagicMock()
        mock_source.get_trading_calendar.return_value = [
            TradingCalendar(date=date(2025, 1, 1), is_trading=False, is_weekend=False, is_holiday=True),
        ]
        api = self._make_api(in_memory_storage, mock_source)

        result = api.get_trading_days(year=2025)
        assert len(result) == 1
        mock_source.get_trading_calendar.assert_called_once_with(2025)

    def test_get_last_trading_day(self, in_memory_storage, sample_trading_calendar):
        api = self._make_api(in_memory_storage, None)
        in_memory_storage.save_trading_calendar(sample_trading_calendar)

        last = api.get_last_trading_day(before=date(2025, 6, 20))
        assert last is not None
        assert last <= date(2025, 6, 20)

    def test_sync_daily_bars(self, in_memory_storage):
        mock_source = MagicMock()
        mock_source.get_daily_bars.return_value = [
            DailyBar(symbol="000001", date=date(2025, 6, 2), open=10.0, high=10.5, low=9.8, close=10.3, volume=100000),
            DailyBar(symbol="000001", date=date(2025, 6, 3), open=10.3, high=10.8, low=10.1, close=10.6, volume=120000),
        ]
        api = self._make_api(in_memory_storage, mock_source)

        count = api.sync_daily_bars("000001", date(2025, 6, 2), date(2025, 6, 3))
        assert count == 2
        # Verify data persisted
        cached = in_memory_storage.get_daily_bars("000001", date(2025, 6, 2), date(2025, 6, 3))
        assert len(cached) == 2

    def test_sync_daily_bars_force_overwrite(self, in_memory_storage):
        mock_source = MagicMock()
        mock_source.get_daily_bars.return_value = [
            DailyBar(symbol="000001", date=date(2025, 6, 2), open=10.0, high=10.5, low=9.8, close=50.0, volume=100000),
        ]
        api = self._make_api(in_memory_storage, mock_source)

        # First save
        api.sync_daily_bars("000001", date(2025, 6, 2), date(2025, 6, 2))
        # Force overwrite
        count = api.sync_daily_bars("000001", date(2025, 6, 2), date(2025, 6, 2), force=True)
        assert count == 1

        cached = in_memory_storage.get_daily_bars("000001", date(2025, 6, 2), date(2025, 6, 2))
        assert cached[0].close == 50.0
