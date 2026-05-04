"""回测分析模块测试"""
import pytest
import json
import math
import random

from backtesting.analytics import DrawdownAnalyzer, RollingMetrics, TradeAnalyzer, MonteCarloSimulator
from backtesting.report import BacktestReport


class TestDrawdownAnalyzer:
    def test_no_data_returns_zero(self):
        dd = DrawdownAnalyzer()
        assert dd.max_drawdown == 0.0

    def test_max_drawdown_basic(self):
        dd = DrawdownAnalyzer()
        for v in [100, 110, 100, 90, 95, 90, 80, 85, 100, 110]:
            dd.update(v)
        assert dd.max_drawdown == pytest.approx(30 / 110, abs=0.01)

    def test_avg_drawdown(self):
        dd = DrawdownAnalyzer()
        for v in [100, 90, 95, 80, 100]:
            dd.update(v)
        assert dd.avg_drawdown > 0

    def test_max_drawdown_duration(self):
        dd = DrawdownAnalyzer()
        for v in [100, 99, 98, 97, 96, 95, 96, 97, 98, 100]:
            dd.update(v)
        assert dd.max_drawdown_duration > 0

    def test_drawdown_series(self):
        dd = DrawdownAnalyzer()
        series = dd.get_drawdown_series([100, 110, 90, 95, 80, 120])
        assert len(series) == 6
        assert series[0] == 0.0
        # Running peak at index 4 is 110 (not 120 yet), so dd = (110-80)/110
        assert series[4] == pytest.approx((110 - 80) / 110, abs=0.01)

    def test_all_drawdowns_tracking(self):
        dd = DrawdownAnalyzer()
        # 100 -> 90 (dd) -> 105 (new peak, stores the dd)
        for v in [100, 90, 105]:
            dd.update(v)
        all_dd = dd.get_all_drawdowns()
        assert len(all_dd) >= 1
        assert all_dd[0]["max_dd"] == pytest.approx(0.1, abs=0.01)

    def test_single_value(self):
        dd = DrawdownAnalyzer()
        dd.update(100.0)
        assert dd.max_drawdown == 0.0


class TestRollingMetrics:
    def test_empty_data(self):
        rm = RollingMetrics()
        result = rm.update(100.0)
        assert result["rolling_return"] == 0.0
        assert result["rolling_sharpe"] == 0.0

    def test_rolling_return_positive(self):
        rm = RollingMetrics(window=10)
        for v in [100, 101, 102, 103, 104, 105]:
            result = rm.update(v)
        assert result["rolling_return"] == pytest.approx(0.05)

    def test_rolling_return_negative(self):
        rm = RollingMetrics(window=10)
        for v in [100, 99, 98, 97, 96, 95]:
            result = rm.update(v)
        assert result["rolling_return"] == pytest.approx(-0.05)

    def test_set_window(self):
        rm = RollingMetrics(window=5)
        rm.set_window(10)
        assert rm._window == 10


class TestTradeAnalyzer:
    def test_empty_trades(self):
        ta = TradeAnalyzer()
        summary = ta.get_summary()
        assert summary["total_trades"] == 0
        assert summary["win_rate"] == 0.0

    def test_all_wins(self):
        ta = TradeAnalyzer()
        ta.add_trades([100, 200, 150])
        assert ta.total_trades == 3
        assert ta.win_count == 3
        assert ta.win_rate == 1.0
        assert ta.loss_count == 0

    def test_all_losses(self):
        ta = TradeAnalyzer()
        ta.add_trades([-100, -200, -150])
        assert ta.win_count == 0
        assert ta.win_rate == 0.0

    def test_mixed_trades(self):
        ta = TradeAnalyzer()
        ta.add_trades([100, -50, 200, -100, 150])
        assert ta.total_trades == 5
        assert ta.win_count == 3
        assert ta.loss_count == 2
        assert ta.win_rate == pytest.approx(0.6)
        assert ta.avg_win == pytest.approx((100 + 200 + 150) / 3)
        assert ta.avg_loss == pytest.approx(75.0)

    def test_profit_factor(self):
        ta = TradeAnalyzer()
        ta.add_trades([100, -50])
        assert ta.profit_factor == pytest.approx(2.0)

    def test_expectancy(self):
        ta = TradeAnalyzer()
        ta.add_trades([100, -50, 200, -100])
        total = 100 - 50 + 200 - 100  # = 150
        assert ta.expectancy == pytest.approx(150 / 4)

    def test_max_consecutive_wins(self):
        ta = TradeAnalyzer()
        ta.add_trades([100, 50, -100, 200, 150, 100])
        assert ta.max_consecutive_wins == 3

    def test_max_consecutive_losses(self):
        ta = TradeAnalyzer()
        ta.add_trades([-100, -50, 100, -200, -150, -100])
        assert ta.max_consecutive_losses == 3

    def test_profit_factor_infinite_on_no_losses(self):
        ta = TradeAnalyzer()
        ta.add_trades([100, 200])
        assert ta.profit_factor == float("inf")

    def test_add_trade_individual(self):
        ta = TradeAnalyzer()
        ta.add_trade(100, True)
        ta.add_trade(-50, False)
        assert ta.total_trades == 2


class TestMonteCarloSimulator:
    def test_empty_returns(self):
        mc = MonteCarloSimulator()
        result = mc.run([], 100000.0)
        assert result["n_simulations"] == 0
        assert result["median_final_value"] == 100000.0

    def test_positive_returns(self):
        random.seed(42)
        mc = MonteCarloSimulator()
        returns = [float(random.gauss(0.002, 0.02)) for _ in range(60)]
        result = mc.run(returns, 100000.0)
        assert result["n_simulations"] > 0
        assert result["median_final_value"] > 0
        assert result["mean_return"] is not None

    def test_percentiles_are_ordered(self):
        random.seed(42)
        mc = MonteCarloSimulator()
        returns = [float(random.gauss(0.001, 0.015)) for _ in range(100)]
        result = mc.run(returns, 100000.0)
        assert result["percentile_5_return"] <= result["percentile_95_return"]
        assert result["percentile_5_final_value"] <= result["percentile_95_final_value"]

    def test_position_based_empty(self):
        mc = MonteCarloSimulator()
        result = mc.run_position_based([], 100000.0)
        assert result["n_simulations"] == 0

    def test_position_basic(self):
        random.seed(42)
        mc = MonteCarloSimulator()
        trades = [random.uniform(-500, 1000) for _ in range(50)]
        result = mc.run_position_based(trades, 100000.0)
        assert result["mean_max_drawdown"] >= 0
        assert result["worst_drawdown"] >= 0


class TestBacktestReport:
    def test_basic_report(self):
        from datetime import date
        report = BacktestReport(
            strategy_name="TestStrategy",
            symbol="000001",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            initial_capital=100000.0,
        )
        values = [100000.0]
        for i in range(1, 31):
            values.append(values[-1] * (1 + random.gauss(0.001, 0.015)))
            report.add_daily_value(values[-1])
        for _ in range(10):
            pnl = random.uniform(-500, 800)
            report.add_trade_pnl(pnl)
        result = report.finalize()
        assert result["summary"]["strategy_name"] == "TestStrategy"
        assert result["summary"]["initial_capital"] == 100000.0
        assert result["performance"]["max_drawdown"] is not None
        assert result["trades"]["total_trades"] == 10

    def test_to_json(self):
        report = BacktestReport(strategy_name="JsonTest", initial_capital=100000.0)
        for v in [100000.0, 101000.0, 99000.0, 102000.0]:
            report.add_daily_value(v)
        report.add_trade_pnl(1000.0)
        report.add_trade_pnl(-1000.0)
        json_str = report.to_json()
        parsed = json.loads(json_str)
        assert parsed["summary"]["strategy_name"] == "JsonTest"

    def test_empty_report(self):
        report = BacktestReport()
        result = report.finalize()
        assert result["summary"]["final_value"] == 100000.0
        assert result["summary"]["total_return"] == 0.0

    def test_daily_returns_provided(self):
        report = BacktestReport(initial_capital=100000.0)
        for v in [100000.0, 101000.0, 99000.0]:
            report.add_daily_value(v)
        result = report.finalize(daily_returns=[0.01, -0.0198])
        assert result["summary"]["final_value"] == 99000.0

    def test_metrics_calculated(self):
        random.seed(42)
        report = BacktestReport(initial_capital=100000.0)
        values = [100000.0]
        for _ in range(100):
            values.append(values[-1] * (1 + random.gauss(0.001, 0.015)))
            report.add_daily_value(values[-1])
        report.add_trade_pnl(500.0)
        result = report.finalize()
        assert result["performance"]["sharpe_ratio"] is not None
        assert result["performance"]["calmar_ratio"] is not None
        assert result["performance"]["sortino_ratio"] is not None


if __name__ == "__main__":
    random.seed(42)
    pytest.main([__file__, "-v"])
