"""集成测试: 策略 + 回测引擎联动

验证策略引擎与回测引擎的端到端联动:
- 策略可以注册到回测引擎
- 回测引擎逐bar驱动策略执行
- 策略的buy/sell调用产生订单并成交
- 回测结果包含正确的绩效指标
"""
import os
import sys
import pytest
from datetime import date
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pandas as pd
import numpy as np

from strategy_engine.base import BaseStrategy
from strategy_engine.context import StrategyContext
from strategy_engine.types import Direction, OrderType, OrderStatus, Order as StrategyOrder
from data_center.interfaces.data_source import DailyBar
from backtesting.engine import BacktestEngine
from backtesting.result import BacktestResult
from backtesting.broker import Broker


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

def _generate_ohlcvs(days: int = 200, seed: int = 42) -> list[DailyBar]:
    """生成模拟日线数据供回测使用。"""
    np.random.seed(seed)
    base = 10.0
    returns = np.random.normal(0.0005, 0.015, days)
    close = base * (1 + returns).cumprod()
    high = close * (1 + np.abs(np.random.normal(0, 0.008, days)))
    low = close * (1 - np.abs(np.random.normal(0, 0.008, days)))
    open_ = close * (1 + np.random.normal(0, 0.003, days))
    volume = np.random.randint(100000, 500000, days)

    bars = []
    for i in range(days):
        bars.append(DailyBar(
            symbol="600000",
            date=date(2025, 1, 1) + pd.Timedelta(days=i),
            open=float(open_[i]),
            high=float(high[i]),
            low=float(low[i]),
            close=float(close[i]),
            volume=float(volume[i]),
        ))
    return bars


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestStrategyBacktestIntegration:
    """策略 + 回测引擎集成测试。"""

    def test_backtest_with_mock_data_api(self):
        """使用模拟 DataAPI 的回测引擎可完整运行并返回结果。"""
        mock_api = MagicMock()
        mock_api.get_daily_bar.return_value = _generate_ohlcvs(200)

        engine = BacktestEngine(mock_api, initial_capital=100000, commission_rate=0.001)
        engine.add_strategy(
            DualThrustStrategy,
            symbol="600000",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 7, 1),
            params={"lookback": 10},
        )
        result = engine.run()

        assert isinstance(result, BacktestResult)
        assert result.initial_capital == 100000
        assert result.final_value > 0
        assert result.total_return is not None
        assert result.max_drawdown is not None
        assert result.sharpe_ratio is not None

    def test_strategy_generates_trades(self):
        mock_api = MagicMock()
        mock_api.get_daily_bar.return_value = _generate_ohlcvs(200, seed=42)

        engine = BacktestEngine(mock_api, initial_capital=100000, commission_rate=0.001)
        engine.add_strategy(
            BuyAndHoldStrategy,
            symbol="600000",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 7, 1),
        )
        result = engine.run()

        assert len(result.trades) > 0

    def test_strategy_cash_management(self):
        """回测过程中现金应从初始资金开始，买入减少、卖出增加。"""
        mock_api = MagicMock()
        mock_api.get_daily_bar.return_value = _generate_ohlcvs(200)

        engine = BacktestEngine(mock_api, initial_capital=50000, commission_rate=0.0)
        engine.add_strategy(
            BuyAndHoldStrategy,
            symbol="600000",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 7, 1),
        )
        result = engine.run()

        ctx = result.context
        assert ctx.cash < 50000  # bought something, cash decreased
        assert len(ctx.positions) > 0

    def test_backtest_result_metrics_consistency(self):
        """回测结果的各项指标应自洽。"""
        mock_api = MagicMock()
        mock_api.get_daily_bar.return_value = _generate_ohlcvs(150)

        engine = BacktestEngine(mock_api, initial_capital=100000, commission_rate=0.001)
        engine.add_strategy(
            DualThrustStrategy,
            symbol="600000",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 6, 1),
        )
        result = engine.run()

        # total_return 应等于 (final - initial) / initial
        expected_return = (result.final_value - result.initial_capital) / result.initial_capital
        assert abs(result.total_return - expected_return) < 1e-6

    def test_backtest_daily_values_tracking(self):
        """回测引擎应逐日记录资产值。"""
        mock_api = MagicMock()
        bars = _generate_ohlcvs(50)
        mock_api.get_daily_bar.return_value = bars

        engine = BacktestEngine(mock_api, initial_capital=100000, commission_rate=0.0)
        engine.add_strategy(
            BuyAndHoldStrategy,
            symbol="600000",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 1),
        )
        result = engine.run()

        # daily_values[0] = initial, then one per bar
        assert result.daily_values[0] == 100000
        # Should have initial + at least len(bars) entries
        assert len(result.daily_values) > len(bars)

    def test_strategy_not_enough_cash(self):
        """资金不足时策略不应产生订单。"""
        mock_api = MagicMock()
        mock_api.get_daily_bar.return_value = _generate_ohlcvs(50)

        engine = BacktestEngine(mock_api, initial_capital=100, commission_rate=0.001)
        engine.add_strategy(
            BuyAndHoldStrategy,
            symbol="600000",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 1),
        )
        result = engine.run()

        # With only $100, likely can't buy anything (minimum 100 shares at ~$10)
        assert len(result.trades) == 0

    def test_backtest_no_data_raises(self):
        """无数据时应抛出异常。"""
        mock_api = MagicMock()
        mock_api.get_daily_bar.return_value = []

        engine = BacktestEngine(mock_api, initial_capital=100000)
        engine.add_strategy(
            DualThrustStrategy,
            symbol="999999",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 1),
        )
        with pytest.raises(ValueError, match="No data"):
            engine.run()

    def test_backtest_no_strategy_raises(self):
        """未添加策略时运行应失败。"""
        mock_api = MagicMock()
        engine = BacktestEngine(mock_api, initial_capital=100000)
        with pytest.raises(ValueError, match="No strategy"):
            engine.run()


# ---------------------------------------------------------------------------
# Test strategy implementations
# ---------------------------------------------------------------------------

class BuyAndHoldStrategy(BaseStrategy):
    """简单买入持有策略，首个bar买入并持有。"""
    name: str = "BuyAndHold"
    has_bought: bool = False

    def on_init(self):
        pass

    def on_bar(self, bar: DailyBar):
        if not self.has_bought and not self.has_position():
            # Buy all we can afford
            qty = int(self.context.cash / bar.close / 100) * 100  # A-share lot = 100
            if qty >= 100:
                self.buy(qty, bar.close)
                self.has_bought = True


class DualThrustStrategy(BaseStrategy):
    """简化版 DualThrust 策略：通道突破时买入，跌破时卖出。"""
    name: str = "DualThrust"
    highs: list = []
    lows: list = []

    def on_init(self):
        self.highs = []
        self.lows = []

    def on_bar(self, bar: DailyBar):
        lookback = self.params.get("lookback", 10)
        self.highs.append(bar.high)
        self.lows.append(bar.low)

        if len(self.highs) < lookback + 1:
            return

        hh = max(self.highs[-(lookback + 1):-1])
        ll = min(self.lows[-(lookback + 1):-1])
        rng = max(hh - ll, 0.01)
        upper = bar.open + 0.5 * rng
        lower = bar.open - 0.5 * rng

        if bar.close > upper and not self.has_position():
            qty = int(self.context.cash / bar.close / 100) * 100
            if qty >= 100:
                self.buy(qty, bar.close)
        elif bar.close < lower and self.has_position():
            pos = self.get_position_quantity()
            if pos > 0:
                self.sell(pos, bar.close)
