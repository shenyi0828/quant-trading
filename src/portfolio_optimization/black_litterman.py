import numpy as np
from typing import List, Optional, Tuple


class BlackLittermanModel:
    def __init__(
        self,
        cov_matrix: np.ndarray,
        market_weights: np.ndarray,
        risk_aversion: float = 2.5,
        tau: float = 0.05,
    ):
        self.cov_matrix = np.asarray(cov_matrix, dtype=float)
        self.market_weights = np.asarray(market_weights, dtype=float)
        self.risk_aversion = risk_aversion
        self.tau = tau
        self.n_assets = len(self.market_weights)
        self._views_P: List[np.ndarray] = []
        self._views_Q: List[float] = []
        self._views_Omega_diag: List[float] = []

    def equilibrium_returns(self) -> np.ndarray:
        return float(self.risk_aversion) * self.cov_matrix @ self.market_weights

    def bl_returns(self) -> np.ndarray:
        pi = self.equilibrium_returns()
        P = np.array(self._views_P) if self._views_P else np.eye(self.n_assets)
        Q = np.array(self._views_Q) if self._views_Q else pi
        tau_sigma = self.tau * self.cov_matrix

        if self._views_P:
            Omega = np.diag(self._views_Omega_diag) if self._views_Omega_diag else P @ tau_sigma @ P.T
        else:
            Omega = tau_sigma

        tau_sigma_inv = np.linalg.inv(tau_sigma)
        omega_inv = np.linalg.inv(Omega)

        post_cov = np.linalg.inv(tau_sigma_inv + P.T @ omega_inv @ P)
        post_mean = post_cov @ (tau_sigma_inv @ pi + P.T @ omega_inv @ Q)

        return post_mean

    def bl_portfolio(self) -> np.ndarray:
        post_returns = self.bl_returns()
        delta = self.risk_aversion
        cov_inv = np.linalg.inv(self.cov_matrix)
        w = cov_inv @ post_returns / delta
        w = w / np.sum(w)
        np.clip(w, 0, None, out=w)
        w /= w.sum()
        return w

    def add_absolute_view(self, asset_index: int, expected_return: float, confidence: Optional[float] = None):
        P_row = np.zeros(self.n_assets)
        P_row[asset_index] = 1.0
        self._views_P.append(P_row)
        self._views_Q.append(expected_return)
        var_i = self.tau * self.cov_matrix[asset_index, asset_index]
        self._views_Omega_diag.append(var_i / confidence if confidence else var_i)

    def add_relative_view(
        self, asset_a: int, asset_b: int, outperformance: float, confidence: Optional[float] = None
    ):
        P_row = np.zeros(self.n_assets)
        P_row[asset_a] = 1.0
        P_row[asset_b] = -1.0
        self._views_P.append(P_row)
        self._views_Q.append(outperformance)
        var_a = self.tau * self.cov_matrix[asset_a, asset_a]
        var_b = self.tau * self.cov_matrix[asset_b, asset_b]
        combined_var = var_a + var_b
        self._views_Omega_diag.append(combined_var / confidence if confidence else combined_var)
