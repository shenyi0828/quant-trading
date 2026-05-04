"""高级回测分析模块 — 参考 RQAlpha 和 BackTrader 的分析架构

提供:
- 回撤分析 (最大值、平均回撤、回撤持续时间)
- 滚动指标 (滚动夏普比率、滚动收益)
- 交易分析 (连续胜负、盈亏因子、期望值)
- 蒙特卡洛模拟
"""
from typing import List, Dict, Any, Optional, Tuple
import math
import random
from collections import deque


class DrawdownAnalyzer:
    """回撤分析"""

    def __init__(self):
        self._peak = 0.0
        self._drawdowns: List[Dict[str, Any]] = []
        self._current_dd: Optional[Dict[str, Any]] = None

    def update(self, value: float):
        if value > self._peak:
            if self._current_dd and self._current_dd["duration"] > 0:
                self._drawdowns.append(self._current_dd)
            self._peak = value
            self._current_dd = {
                "peak": value,
                "max_dd": 0.0,
                "start_value": value,
                "end_value": value,
                "duration": 0,
            }

        if self._current_dd:
            dd = (self._peak - value) / self._peak if self._peak > 0 else 0.0
            self._current_dd["max_dd"] = max(self._current_dd["max_dd"], dd)
            self._current_dd["end_value"] = value
            self._current_dd["duration"] += 1

    @property
    def max_drawdown(self) -> float:
        candidates = [d["max_dd"] for d in self._drawdowns]
        if self._current_dd:
            candidates.append(self._current_dd["max_dd"])
        return max(candidates) if candidates else 0.0

    @property
    def avg_drawdown(self) -> float:
        candidates = [d["max_dd"] for d in self._drawdowns]
        if self._current_dd:
            candidates.append(self._current_dd["max_dd"])
        return sum(candidates) / len(candidates) if candidates else 0.0

    @property
    def max_drawdown_duration(self) -> int:
        candidates = [d["duration"] for d in self._drawdowns]
        if self._current_dd:
            candidates.append(self._current_dd["duration"])
        return max(candidates) if candidates else 0

    @property
    def avg_drawdown_duration(self) -> float:
        candidates = [d["duration"] for d in self._drawdowns if d["duration"] > 0]
        if self._current_dd and self._current_dd["duration"] > 0:
            candidates.append(self._current_dd["duration"])
        return sum(candidates) / len(candidates) if candidates else 0.0

    def get_all_drawdowns(self) -> List[Dict[str, Any]]:
        return self._drawdowns[:]

    def get_drawdown_series(self, values: List[float]) -> List[float]:
        """生成回撤序列"""
        peak = 0.0
        series = []
        for v in values:
            peak = max(peak, v)
            dd = (peak - v) / peak if peak > 0 else 0.0
            series.append(dd)
        return series


class RollingMetrics:
    """滚动指标计算"""

    def __init__(self, window: int = 60):
        self._window = window
        self._values: deque = deque(maxlen=window + 1)

    def update(self, value: float) -> Dict[str, float]:
        self._values.append(value)

        if len(self._values) < 2:
            return {"rolling_return": 0.0, "rolling_sharpe": 0.0, "rolling_volatility": 0.0}

        prices = list(self._values)
        returns = [
            (prices[i] - prices[i - 1]) / prices[i - 1]
            for i in range(1, len(prices))
            if prices[i - 1] > 0
        ]

        rolling_return = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0.0
        rolling_volatility = self._calc_std(returns) * (252 ** 0.5) if len(returns) > 1 else 0.0

        mean_ret = sum(returns) / len(returns) if returns else 0.0
        annualized_mean = mean_ret * 252
        rolling_sharpe = (annualized_mean - 0.02) / rolling_volatility if rolling_volatility > 0 else 0.0

        return {
            "rolling_return": rolling_return,
            "rolling_sharpe": rolling_sharpe,
            "rolling_volatility": rolling_volatility,
        }

    @staticmethod
    def _calc_std(values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    def set_window(self, window: int):
        self._window = window
        self._values = deque(maxlen=window + 1)


class TradeAnalyzer:
    """交易分析"""

    def __init__(self):
        self._trades: List[Dict[str, Any]] = []

    def add_trade(self, pnl: float, is_win: bool):
        self._trades.append({"pnl": pnl, "is_win": is_win})

    def add_trades(self, pnls: List[float]):
        for pnl in pnls:
            self._trades.append({"pnl": pnl, "is_win": pnl > 0})

    @property
    def total_trades(self) -> int:
        return len(self._trades)

    @property
    def win_count(self) -> int:
        return sum(1 for t in self._trades if t["is_win"])

    @property
    def loss_count(self) -> int:
        return self.total_trades - self.win_count

    @property
    def win_rate(self) -> float:
        return self.win_count / self.total_trades if self.total_trades > 0 else 0.0

    @property
    def avg_win(self) -> float:
        wins = [t["pnl"] for t in self._trades if t["is_win"]]
        return sum(wins) / len(wins) if wins else 0.0

    @property
    def avg_loss(self) -> float:
        losses = [abs(t["pnl"]) for t in self._trades if not t["is_win"]]
        return sum(losses) / len(losses) if losses else 0.0

    @property
    def profit_factor(self) -> float:
        total_loss = sum(abs(t["pnl"]) for t in self._trades if not t["is_win"])
        if total_loss == 0:
            return float("inf") if self.win_count > 0 else 0.0
        total_win = sum(t["pnl"] for t in self._trades if t["is_win"])
        return total_win / total_loss

    @property
    def expectancy(self) -> float:
        total_pnl = sum(t["pnl"] for t in self._trades)
        return total_pnl / self.total_trades if self.total_trades > 0 else 0.0

    @property
    def max_consecutive_wins(self) -> int:
        return self._max_consecutive(True)

    @property
    def max_consecutive_losses(self) -> int:
        return self._max_consecutive(False)

    def _max_consecutive(self, is_win: bool) -> int:
        max_run = 0
        current_run = 0
        for t in self._trades:
            if t["is_win"] == is_win:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 0
        return max_run

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_trades": self.total_trades,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "win_rate": self.win_rate,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
            "profit_factor": self.profit_factor,
            "expectancy": self.expectancy,
            "max_consecutive_wins": self.max_consecutive_wins,
            "max_consecutive_losses": self.max_consecutive_losses,
            "total_pnl": sum(t["pnl"] for t in self._trades),
        }


class MonteCarloSimulator:
    """蒙特卡洛模拟 — 评估策略稳健性"""

    def __init__(self, n_simulations: int = 1000):
        self._n_simulations = n_simulations

    def run(
        self,
        daily_returns: List[float],
        initial_capital: float = 100000.0,
    ) -> Dict[str, Any]:
        """运行蒙特卡洛模拟

        通过有放回抽样重排日收益率，模拟不同市场路径。
        """
        if not daily_returns:
            return self._empty_result(initial_capital)

        results = []
        for _ in range(self._n_simulations):
            shuffled = random.sample(daily_returns, len(daily_returns))
            equity_curve = [initial_capital]
            for ret in shuffled:
                equity_curve.append(equity_curve[-1] * (1 + ret))

            final_value = equity_curve[-1]
            total_return = (final_value - initial_capital) / initial_capital

            # 计算最大回撤
            peak = equity_curve[0]
            max_dd = 0.0
            for v in equity_curve:
                peak = max(peak, v)
                dd = (peak - v) / peak if peak > 0 else 0.0
                max_dd = max(max_dd, dd)

            results.append({
                "final_value": final_value,
                "total_return": total_return,
                "max_drawdown": max_dd,
            })

        return self._aggregate(results, initial_capital)

    def run_position_based(
        self,
        trades: List[float],
        initial_capital: float = 100000.0,
        risk_per_trade: float = 0.01,
    ) -> Dict[str, Any]:
        """基于交易的蒙特卡洛模拟

        随机重排交易顺序和结果，模拟不同交易路径。
        """
        if not trades:
            return self._empty_result(initial_capital)

        results = []
        for _ in range(self._n_simulations):
            shuffled = random.sample(trades, len(trades))
            equity = initial_capital
            max_equity = equity
            max_dd = 0.0

            pnl_values = []
            for pnl in shuffled:
                equity += pnl
                pnl_values.append(pnl)
                max_equity = max(max_equity, equity)
                dd = (max_equity - equity) / max_equity if max_equity > 0 else 0.0
                max_dd = max(max_dd, dd)

            results.append({
                "final_value": equity,
                "total_return": (equity - initial_capital) / initial_capital,
                "max_drawdown": max_dd,
            })

        return self._aggregate(results, initial_capital)

    def _aggregate(self, results: List[Dict], initial_capital: float) -> Dict[str, Any]:
        final_values = sorted([r["final_value"] for r in results])
        returns_list = sorted([r["total_return"] for r in results])
        dd_list = sorted([r["max_drawdown"] for r in results])

        n = len(results)

        return {
            "n_simulations": n,
            "initial_capital": initial_capital,
            "median_final_value": final_values[n // 2],
            "mean_final_value": sum(final_values) / n,
            "percentile_5_final_value": final_values[int(n * 0.05)],
            "percentile_95_final_value": final_values[int(n * 0.95)],
            "percentile_5_return": returns_list[int(n * 0.05)],
            "median_return": returns_list[n // 2],
            "percentile_95_return": returns_list[int(n * 0.95)],
            "mean_return": sum(returns_list) / n,
            "mean_max_drawdown": sum(dd_list) / n,
            "worst_drawdown": max(dd_list),
            "best_return": returns_list[-1],
            "worst_return": returns_list[0],
        }

    def _empty_result(self, initial_capital: float) -> Dict[str, Any]:
        return {
            "n_simulations": 0,
            "initial_capital": initial_capital,
            "median_final_value": initial_capital,
            "mean_final_value": initial_capital,
            "percentile_5_final_value": initial_capital,
            "percentile_95_final_value": initial_capital,
            "percentile_5_return": 0.0,
            "median_return": 0.0,
            "percentile_95_return": 0.0,
            "mean_return": 0.0,
            "mean_max_drawdown": 0.0,
            "worst_drawdown": 0.0,
            "best_return": 0.0,
            "worst_return": 0.0,
        }
