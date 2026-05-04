"""回测报告生成 — JSON 格式输出供 API 消费"""
from typing import List, Dict, Any, Optional
import json
from datetime import date, datetime

from backtesting.analytics import DrawdownAnalyzer, RollingMetrics, TradeAnalyzer, MonteCarloSimulator


class BacktestReport:
    """回测报告生成器

    整合所有分析模块的结果，生成完整的 JSON 报告供前端 API 消费。
    """

    def __init__(
        self,
        strategy_name: str = "",
        symbol: str = "",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        initial_capital: float = 100000.0,
    ):
        self.strategy_name = strategy_name
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital

        self.drawdown_analyzer = DrawdownAnalyzer()
        self.rolling_metrics = RollingMetrics()
        self.trade_analyzer = TradeAnalyzer()
        self.mc_simulator = MonteCarloSimulator()

        self._daily_values: List[float] = [initial_capital]
        self._daily_returns: List[float] = []

    def add_daily_value(self, value: float):
        """添加每日净值"""
        self._daily_values.append(value)

    def add_trade_pnl(self, pnl: float):
        """添加交易盈亏"""
        self.trade_analyzer.add_trade(pnl, pnl > 0)

    def finalize(self, daily_returns: Optional[List[float]] = None) -> Dict[str, Any]:
        """生成最终报告"""
        # 更新回撤分析
        for value in self._daily_values:
            self.drawdown_analyzer.update(value)

        # 计算每日收益率
        if daily_returns:
            self._daily_returns = daily_returns
        elif len(self._daily_values) >= 2:
            self._daily_returns = [
                (self._daily_values[i] - self._daily_values[i - 1]) / self._daily_values[i - 1]
                for i in range(1, len(self._daily_values))
                if self._daily_values[i - 1] > 0
            ]

        # 滚动指标
        rolling_results = []
        rm = RollingMetrics()
        for value in self._daily_values:
            result = rm.update(value)
            rolling_results.append(result)

        # 蒙特卡洛模拟
        mc_result = {}
        if self._daily_returns:
            mc_result = self.mc_simulator.run(self._daily_returns, self.initial_capital)

        return {
            "summary": {
                "strategy_name": self.strategy_name,
                "symbol": self.symbol,
                "start_date": str(self.start_date) if self.start_date else "",
                "end_date": str(self.end_date) if self.end_date else "",
                "initial_capital": self.initial_capital,
                "final_value": self._daily_values[-1] if self._daily_values else self.initial_capital,
                "total_return": self._calc_total_return(),
                "annualized_return": self._calc_annualized_return(),
                "trading_days": len(self._daily_values) - 1,
            },
            "performance": {
                "sharpe_ratio": self._calc_sharpe_ratio(),
                "calmar_ratio": self._calc_calmar_ratio(),
                "sortino_ratio": self._calc_sortino_ratio(),
                "max_drawdown": self.drawdown_analyzer.max_drawdown,
                "avg_drawdown": self.drawdown_analyzer.avg_drawdown,
                "max_drawdown_duration": self.drawdown_analyzer.max_drawdown_duration,
                "avg_drawdown_duration": self.drawdown_analyzer.avg_drawdown_duration,
            },
            "trades": self.trade_analyzer.get_summary(),
            "drawdown": {
                "series": self.drawdown_analyzer.get_drawdown_series(self._daily_values),
                "periods": self.drawdown_analyzer.get_all_drawdowns(),
            },
            "rolling_metrics": {
                "latest": rolling_results[-1] if rolling_results else {},
                "series": rolling_results[::5],  # 采样，每5天一个点
            },
            "monte_carlo": mc_result,
            "equity_curve": self._daily_values,
        }

    def to_json(self, indent: int = 2) -> str:
        """生成 JSON 字符串"""
        report = self.finalize()
        return json.dumps(report, indent=indent, default=str)

    def _calc_total_return(self) -> float:
        if not self._daily_values or self.initial_capital == 0:
            return 0.0
        return (self._daily_values[-1] - self.initial_capital) / self.initial_capital

    def _calc_annualized_return(self) -> float:
        total_return = self._calc_total_return()
        days = len(self._daily_values) - 1
        if days <= 0:
            return 0.0
        return (1 + total_return) ** (252 / days) - 1

    def _calc_sharpe_ratio(self) -> float:
        if len(self._daily_returns) < 2:
            return 0.0
        mean_ret = sum(self._daily_returns) / len(self._daily_returns)
        variance = sum((r - mean_ret) ** 2 for r in self._daily_returns) / (len(self._daily_returns) - 1)
        std = variance ** 0.5
        if std == 0:
            return 0.0
        annualized_std = std * (252 ** 0.5)
        return (mean_ret * 252 - 0.02) / annualized_std

    def _calc_calmar_ratio(self) -> float:
        dd = self.drawdown_analyzer.max_drawdown
        if dd == 0:
            return 0.0
        return self._calc_annualized_return() / dd

    def _calc_sortino_ratio(self) -> float:
        if len(self._daily_returns) < 2:
            return 0.0
        mean_ret = sum(self._daily_returns) / len(self._daily_returns)
        downside_returns = [r for r in self._daily_returns if r < 0]
        if not downside_returns:
            return 0.0
        downside_std = (sum(r ** 2 for r in downside_returns) / len(self._daily_returns)) ** 0.5
        annualized_std = downside_std * (252 ** 0.5)
        if annualized_std == 0:
            return 0.0
        return (mean_ret * 252 - 0.02) / annualized_std
