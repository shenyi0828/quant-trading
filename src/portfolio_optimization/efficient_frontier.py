import numpy as np
from typing import List, Tuple


class EfficientFrontier:

    def __init__(
        self,
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray,
        weight_bounds: Tuple[float, float] = (0.0, 1.0),
    ):
        from portfolio_optimization.markowitz import MarkowitzOptimizer
        self.expected_returns = np.asarray(expected_returns, dtype=float)
        self.cov_matrix = np.asarray(cov_matrix, dtype=float)
        self.weight_bounds = weight_bounds
        self.optimizer = MarkowitzOptimizer(expected_returns, cov_matrix, weight_bounds)

    def compute_frontier(self, n_points: int = 50) -> np.ndarray:
        min_var_w = self.optimizer.min_variance_portfolio()
        min_ret = self.optimizer._portfolio_return(min_var_w)

        max_ret_weights = np.zeros(len(self.expected_returns))
        max_asset = np.argmax(self.expected_returns)
        max_ret_weights[max_asset] = 1.0
        max_ret = self.expected_returns[max_asset]

        target_returns = np.linspace(min_ret, max_ret, n_points)
        frontier = []
        for target in target_returns:
            try:
                w = self.optimizer.target_return_portfolio(float(target))
                risk = self.optimizer._portfolio_std(w)
                ret = self.optimizer._portfolio_return(w)
                frontier.append((risk, ret))
            except RuntimeError:
                continue
        return np.array(frontier)

    def get_frontier_data(self, n_points: int = 50) -> Tuple[List[float], List[float]]:
        frontier = self.compute_frontier(n_points)
        return frontier[:, 0].tolist(), frontier[:, 1].tolist()

    def get_max_sharpe_point(self, risk_free_rate: float = 0.0) -> Tuple[float, float]:
        w = self.optimizer.max_sharpe_portfolio(risk_free_rate)
        risk = self.optimizer._portfolio_std(w)
        ret = self.optimizer._portfolio_return(w)
        return risk, ret
