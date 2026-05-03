"""集成测试: 数据 → 因子 → 策略 → 回测 全链路

验证:
- 模拟数据流经因子引擎产生信号
- 信号驱动策略在回测引擎中执行
- 全链路各模块数据格式一致、无断裂
- FastAPI 全链路 API 串联
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pandas as pd
import numpy as np
from datetime import date
from unittest.mock import MagicMock

from data_center.interfaces.data_source import DailyBar
from factor_engine import FactorPortfolio
from factor_engine.library import ROC, RSI, MACD
from strategy_engine.base import BaseStrategy
from backtesting.engine import BacktestEngine
from backtesting.result import BacktestResult


def _generate_ohlcvs(days: int = 200, seed: int = 99) -> list[DailyBar]:
    np.random.seed(seed)
    base = 20.0
    returns = np.random.normal(0.0005, 0.018, days)
    close = base * (1 + returns).cumprod()
    high = close * (1 + np.abs(np.random.normal(0, 0.01, days)))
    low = close * (1 - np.abs(np.random.normal(0, 0.01, days)))
    open_ = close * (1 + np.random.normal(0, 0.004, days))
    volume = np.random.randint(200000, 800000, days)

    bars = []
    for i in range(days):
        bars.append(DailyBar(
            symbol="000001",
            date=date(2025, 1, 1) + pd.Timedelta(days=i),
            open=float(open_[i]),
            high=float(high[i]),
            low=float(low[i]),
            close=float(close[i]),
            volume=float(volume[i]),
        ))
    return bars


class SignalDrivenStrategy(BaseStrategy):
    """基于因子信号的交易策略。"""

    name: str = "SignalDriven"
    last_signal: int = 0
    signal_history: list = []

    def on_init(self):
        self.last_signal = 0
        self.signal_history = []
        self._bars: list = []

    def on_bar(self, bar: DailyBar):
        self._bars.append(bar)

        lookback = self.params.get("lookback", 50)
        if len(self._bars) < lookback:
            return

        # Compute a rolling factor signal
        prices = pd.Series([b.close for b in self._bars[-lookback:]])
        roc_val = (prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]
        rsi_val = _simple_rsi(prices, 14)

        score = 0.5 * roc_val + 0.5 * (rsi_val - 50) / 50

        if score > 0.05 and not self.has_position():
            qty = int(self.context.cash / bar.close / 100) * 100
            if qty >= 100:
                self.buy(qty, bar.close)
                self.last_signal = 1
        elif score < -0.05 and self.has_position():
            pos = self.get_position_quantity()
            if pos > 0:
                self.sell(pos, bar.close)
                self.last_signal = -1
        else:
            self.last_signal = 0

        self.signal_history.append(self.last_signal)


def _simple_rsi(prices: pd.Series, period: int) -> float:
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(period).mean().iloc[-1]
    loss = (-delta.clip(upper=0)).rolling(period).mean().iloc[-1]
    if loss == 0 or pd.isna(loss):
        return 50.0
    rs = gain / loss
    return 100 - (100 / (1 + rs))


class TestFullPipelineIntegration:

    def test_data_to_signal_pipeline(self):
        """数据 → 因子计算的信号应可被策略消费。"""
        bars = _generate_ohlcvs(200)
        df = pd.DataFrame({
            "date": [b.date for b in bars],
            "open": [b.open for b in bars],
            "high": [b.high for b in bars],
            "low": [b.low for b in bars],
            "close": [b.close for b in bars],
            "volume": [b.volume for b in bars],
        })

        portfolio = FactorPortfolio()
        portfolio.add_factor(ROC(period=20), weight=0.5)
        portfolio.add_factor(RSI(period=14), weight=0.5)
        signals = portfolio.compute_signals(df, top_pct=0.2)

        assert "signal" in signals.columns
        assert set(signals["signal"].unique()).issubset({-1, 0, 1})

    def test_full_backtest_with_signal_strategy(self):
        """全链路: 模拟数据 → 信号策略 → 回测执行 → 绩效结果。"""
        mock_api = MagicMock()
        mock_api.get_daily_bar.return_value = _generate_ohlcvs(300, seed=42)

        engine = BacktestEngine(mock_api, initial_capital=200000, commission_rate=0.001)
        engine.add_strategy(
            SignalDrivenStrategy,
            symbol="000001",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            params={"lookback": 50},
        )
        result = engine.run()

        assert isinstance(result, BacktestResult)
        assert result.initial_capital == 200000
        assert result.final_value > 0
        assert len(result.trades) > 0

    def test_backtest_with_commission_impact(self):
        """手续费对回测结果应有可观测影响。"""
        mock_api = MagicMock()
        mock_api.get_daily_bar.return_value = _generate_ohlcvs(200, seed=10)

        engine_no_fee = BacktestEngine(mock_api, initial_capital=100000, commission_rate=0.0)
        engine_no_fee.add_strategy(
            SignalDrivenStrategy,
            symbol="000001",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        result_no_fee = engine_no_fee.run()

        mock_api = MagicMock()
        mock_api.get_daily_bar.return_value = _generate_ohlcvs(200, seed=10)

        engine_with_fee = BacktestEngine(mock_api, initial_capital=100000, commission_rate=0.003)
        engine_with_fee.add_strategy(
            SignalDrivenStrategy,
            symbol="000001",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        result_with_fee = engine_with_fee.run()

        assert result_with_fee.final_value <= result_no_fee.final_value

    def test_risk_check_before_backtest(self):
        """风控检查可作为回测前置校验。"""
        from risk_manager import RiskChecker, OrderLimitRule, RiskContext

        checker = RiskChecker()
        checker.add_rule(OrderLimitRule(max_amount=500000))
        ctx = RiskContext(total_capital=1000000, available_cash=1000000, initial_capital=1000000)

        from strategy_engine.types import Order as StrategyOrder, Direction, OrderType, OrderStatus

        order = StrategyOrder(
            order_id="PRE_CHECK_1",
            symbol="000001",
            direction=Direction.LONG,
            order_type=OrderType.MARKET,
            price=20.0,
            quantity=1000,
            status=OrderStatus.PENDING,
        )
        report = checker.check(order, ctx)

        # Should pass risk check, then we can run backtest
        assert report.is_accepted

    def test_multi_strategy_data_flow(self):
        """同一份数据驱动两个策略应产生独立的交易记录。"""
        mock_api_1 = MagicMock()
        mock_api_1.get_daily_bar.return_value = _generate_ohlcvs(200, seed=42)

        engine_1 = BacktestEngine(mock_api_1, initial_capital=100000, commission_rate=0.001)
        engine_1.add_strategy(
            SignalDrivenStrategy,
            symbol="000001",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            params={"lookback": 30},
        )
        result_1 = engine_1.run()

        mock_api_2 = MagicMock()
        mock_api_2.get_daily_bar.return_value = _generate_ohlcvs(200, seed=42)

        engine_2 = BacktestEngine(mock_api_2, initial_capital=100000, commission_rate=0.001)
        engine_2.add_strategy(
            SignalDrivenStrategy,
            symbol="000001",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            params={"lookback": 80},
        )
        result_2 = engine_2.run()

        # Different lookback parameters should produce different trade counts
        assert result_1.initial_capital == result_2.initial_capital
        assert result_1.final_value != result_2.final_value or result_1.trades != result_2.trades

    def test_api_health_and_portfolio_endpoint(self):
        """FastAPI 服务应响应 health 和 portfolio summary 端点。"""
        from fastapi.testclient import TestClient
        from api import app

        client = TestClient(app)

        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

        resp = client.get("/portfolio/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_capital" in data

    def test_api_strategy_lifecycle_and_order(self):
        """通过 API 完成策略创建 → 启动 → 下单全流程。"""
        from fastapi.testclient import TestClient
        from api import app
        from api.routes.strategies import _registry

        _registry._strategies.clear()
        _registry._strategy_classes.clear()
        from strategy_engine.examples.dual_thrust import DualThrust
        _registry.register_strategy_class("DualThrust", DualThrust)

        client = TestClient(app)

        resp = client.post(
            "/strategies",
            json={
                "name": "test_full_pipeline",
                "class_name": "DualThrust",
                "symbol": "600000",
                "params": {"N": 5, "K1": 0.5, "K2": 0.5},
                "initial_capital": 100000.0,
            },
        )
        assert resp.status_code == 201
        strategy_id = resp.json()["strategy_id"]

        resp = client.get(f"/strategies/{strategy_id}")
        assert resp.status_code == 200

        resp = client.post(f"/strategies/{strategy_id}/start")
        assert resp.status_code == 200
        status_data = resp.json()
        assert status_data["status"] == "running"
        assert status_data["cash"] == 100000.0

        resp = client.post(
            "/orders",
            json={
                "symbol": "000001",
                "exchange": "sse",
                "direction": "long",
                "offset": "open",
                "order_type": "market",
                "quantity": 100,
                "price": 10.0,
            },
        )
        assert resp.status_code == 201

        resp = client.get("/orders/active")
        assert resp.status_code == 200

    def test_api_risk_check_endpoint(self):
        """通过 API 执行风控 dry-run 检查。"""
        from fastapi.testclient import TestClient
        from api import app

        client = TestClient(app)

        resp = client.post(
            "/risk/check",
            json={
                "symbol": "000001",
                "direction": "long",
                "quantity": 100,
                "price": 10.0,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "is_accepted" in data
        assert "results" in data
