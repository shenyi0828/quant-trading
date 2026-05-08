import numpy as np
from scipy.optimize import minimize
from typing import Optional, Tuple


class MarkowitzOptimizer:

    def __init__(
        self,
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray,
        weight_bounds: Optional[Tuple[float, float]] = None,
    ):
        self.expected_returns = np.asarray(expected_returns, dtype=float)
        self.cov_matrix = np.asarray(cov_matrix, dtype=float)
        self.n_assets = len(self.expected_returns)
        self.weight_bounds = weight_bounds or (0.0, 1.0)

    def _portfolio_return(self, weights: np.ndarray) -> float:
        return float(weights @ self.expected_returns)

    def _portfolio_variance(self, weights: np.ndarray) -> float:
        return float(weights @ self.cov_matrix @ weights)

    def _portfolio_std(self, weights: np.ndarray) -> float:
        return float(np.sqrt(self._portfolio_variance(weights)))

    def min_variance_portfolio(self) -> np.ndarray:
        constraints = ({
            "type": "eq",
            "fun": lambda w: np.sum(w) - 1.0,
        })
        bounds = [self.weight_bounds] * self.n_assets
        x0 = np.ones(self.n_assets) / self.n_assets

        result = minimize(
            self._portfolio_variance,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )
        if not result.success:
            raise RuntimeError(f"Min variance optimization failed: {result.message}")
        return result.x

    def max_sharpe_portfolio(self, risk_free_rate: float = 0.0) -> np.ndarray:
        def neg_sharpe(weights: np.ndarray) -> float:
            port_return = self._portfolio_return(weights)
            port_risk = self._portfolio_std(weights)
            if port_risk < 1e-12:
                return 0.0
            return -(port_return - risk_free_rate) / port_risk

        constraints = ({
            "type": "eq",
            "fun": lambda w: np.sum(w) - 1.0,
        })
        bounds = [self.weight_bounds] * self.n_assets
        x0 = np.ones(self.n_assets) / self.n_assets

        result = minimize(
            neg_sharpe,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )
        if not result.success:
            raise RuntimeError(f"Max Sharpe optimization failed: {result.message}")
        return result.x

    def target_return_portfolio(
        self, target_return: float
    ) -> np.ndarray:
        constraints = (
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
            {"type": "eq", "fun": lambda w: self._portfolio_return(w) - target_return},
        )
        bounds = [self.weight_bounds] * self.n_assets
        x0 = np.ones(self.n_assets) / self.n_assets

        result = minimize(
            self._portfolio_variance,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )
        if not result.success:
            raise RuntimeError(f"Target return optimization failed: {result.message}")
        return result.x
