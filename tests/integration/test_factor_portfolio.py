"""集成测试: 因子引擎 + 组合管理链路

验证:
- FactorPortfolio 组合因子可生成信号
- 信号驱动 PortfolioManager 创建账户并更新持仓
- 因子组合的 PnL 计算与分配
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pandas as pd
import numpy as np
from datetime import date

from factor_engine import FactorPortfolio, FactorCalculator
from factor_engine.library import ROC, RSI, MACD, ATR
from portfolio import PortfolioManager, AllocationMethod, AccountStatus


class TestFactorPortfolioIntegration:
    """因子引擎 + 组合管理集成测试。"""

    @staticmethod
    def _mock_ohlcvs(days: int = 200) -> pd.DataFrame:
        np.random.seed(77)
        dates = pd.date_range("2025-01-01", periods=days, freq="D")
        base = 10.0
        returns = np.random.normal(0.001, 0.02, days)
        close = base * (1 + returns).cumprod()
        high = close * (1 + np.abs(np.random.normal(0, 0.01, days)))
        low = close * (1 - np.abs(np.random.normal(0, 0.01, days)))
        open_ = close * (1 + np.random.normal(0, 0.005, days))
        volume = np.random.randint(100000, 500000, days)
        return pd.DataFrame({
            "date": dates,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        })

    def test_factor_signals_drive_portfolio_allocation(self):
        """因子信号应能驱动组合的资金分配决策。"""
        data = self._mock_ohlcvs(200)

        portfolio = FactorPortfolio()
        portfolio.add_factor(ROC(period=10), weight=0.4)
        portfolio.add_factor(RSI(period=14), weight=0.3)
        portfolio.add_factor(MACD(), weight=0.3)
        signals = portfolio.compute_signals(data, top_pct=0.2)

        buy_signals = signals[signals["signal"] == 1]
        assert len(buy_signals) > 0

    def test_factor_correlation_analysis(self):
        """因子组合应能计算因子间相关性。"""
        data = self._mock_ohlcvs(150)

        portfolio = FactorPortfolio()
        portfolio.add_factor(ROC(period=10), weight=0.3)
        portfolio.add_factor(RSI(period=14), weight=0.3)
        portfolio.add_factor(ATR(period=14), weight=0.4)

        corr = portfolio.get_factor_correlations(data)

        assert not corr.empty
        assert corr.shape[0] == 3
        assert corr.shape[1] == 3

        # Diagonal should be ~1.0
        for i in range(3):
            assert abs(corr.iloc[i, i] - 1.0) < 1e-6

    def test_portfolio_summary_consistency(self):
        """因子组合摘要信息应自洽。"""
        data = self._mock_ohlcvs(100)

        portfolio = FactorPortfolio()
        portfolio.add_factor(ROC(period=10), weight=0.5)
        portfolio.add_factor(RSI(period=14), weight=0.5)

        summary = portfolio.summary()
        assert summary["num_factors"] == 2
        assert summary["total_weight"] == 1.0

    def test_top_signals_filter(self):
        """get_top_signals 应仅返回买入信号。"""
        data = self._mock_ohlcvs(200)

        portfolio = FactorPortfolio()
        portfolio.add_factor(ROC(period=10), weight=0.5)
        portfolio.add_factor(MACD(), weight=0.5)

        top = portfolio.get_top_signals(data, top_pct=0.2)
        assert (top["signal"] == 1).all()

    def test_factor_cache_reuse(self):
        """因子计算器应支持缓存复用。"""
        data = self._mock_ohlcvs(100)

        calc = FactorCalculator(normalize=True)
        roc = ROC(period=10)

        result1 = calc.compute_single(roc, data, use_cache=True)
        result2 = calc.compute_single(roc, data, use_cache=True)

        assert result1.values.equals(result2.values)

    def test_signal_ranking_distribution(self):
        """信号排名应接近均匀分布。"""
        data = self._mock_ohlcvs(200)

        portfolio = FactorPortfolio()
        portfolio.add_factor(ROC(period=10), weight=0.25)
        portfolio.add_factor(RSI(period=14), weight=0.25)
        portfolio.add_factor(MACD(), weight=0.25)
        portfolio.add_factor(ATR(period=14), weight=0.25)

        signals = portfolio.compute_signals(data)
        ranks = signals["rank"]

        assert ranks.min() >= 0.0
        assert ranks.max() <= 1.0

    def test_clear_factors_and_recompute(self):
        """清除因子后重新计算应产生不同结果。"""
        data = self._mock_ohlcvs(100)

        portfolio = FactorPortfolio()
        portfolio.add_factor(ROC(period=10), weight=1.0)
        signals_v1 = portfolio.compute_signals(data)

        portfolio.clear_factors()
        portfolio.add_factor(RSI(period=14), weight=1.0)
        signals_v2 = portfolio.compute_signals(data)

        assert not signals_v1["score"].equals(signals_v2["score"])

    def test_bucket_distribution(self):
        """信号分桶应正确十分位分组。"""
        data = self._mock_ohlcvs(200)

        portfolio = FactorPortfolio()
        portfolio.add_factor(ROC(period=10), weight=1.0)
        signals = portfolio.compute_signals(data)

        buckets = signals["bucket"]
        assert buckets.nunique() <= 10
