import numpy as np
from scipy.optimize import minimize
from typing import Optional


class RiskParityOptimizer:

    def __init__(self, cov_matrix: np.ndarray):
        self.cov_matrix = np.asarray(cov_matrix, dtype=float)
        self.n_assets = self.cov_matrix.shape[0]

    def _risk_contribution(self, weights: np.ndarray) -> np.ndarray:
        portfolio_var = weights @ self.cov_matrix @ weights
        marginal_risk = self.cov_matrix @ weights
        risk_contribution = weights * marginal_risk / np.sqrt(portfolio_var)
        return risk_contribution

    def optimize_slsqp(self) -> np.ndarray:
        target_rc = 1.0 / self.n_assets

        def objective(weights):
            rc = self._risk_contribution(weights)
            rc_normalized = rc / rc.sum()
            return np.sum((rc_normalized - target_rc) ** 2)

        constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1.0},)
        bounds = [(0.0, 1.0)] * self.n_assets
        x0 = np.ones(self.n_assets) / self.n_assets

        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-12, "maxiter": 1000},
        )
        if not result.success:
            raise RuntimeError(f"Risk parity SLSQP failed: {result.message}")
        return result.x

    def optimize_ccd(self) -> np.ndarray:
        w = np.ones(self.n_assets) / self.n_assets

        for _ in range(10000):
            for asset_i in range(self.n_assets):
                var_i = self.cov_matrix[asset_i, asset_i]
                if var_i < 1e-12:
                    continue
                cov_i_other = self.cov_matrix[asset_i, :] @ w - var_i * w[asset_i]
                if abs(cov_i_other) < 1e-12:
                    continue
                w[asset_i] = (
                    -cov_i_other
                    + np.sqrt(cov_i_other**2 + 4 * var_i * (1.0 / self.n_assets) * (w @ self.cov_matrix @ w))
                ) / (2 * var_i)
                w[asset_i] = max(w[asset_i], 1e-10)
            w /= w.sum()
        return w


def risk_parity_weights(cov_matrix: np.ndarray, method: str = "slsqp") -> np.ndarray:
    optimizer = RiskParityOptimizer(cov_matrix)
    if method == "ccd":
        return optimizer.optimize_ccd()
    return optimizer.optimize_slsqp()
