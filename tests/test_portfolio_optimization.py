"""投资组合优化模块测试"""
import numpy as np
import pytest

from portfolio_optimization import (
    MarkowitzOptimizer,
    BlackLittermanModel,
    RiskParityOptimizer,
    risk_parity_weights,
    EfficientFrontier,
)


@pytest.fixture
def sample_data():
    returns = np.array([0.10, 0.15, 0.12, 0.08])
    cov = np.array([
        [0.04, 0.01, 0.005, 0.002],
        [0.01, 0.06, 0.015, 0.003],
        [0.005, 0.015, 0.05, 0.008],
        [0.002, 0.003, 0.008, 0.03],
    ])
    return returns, cov


@pytest.fixture
def market_weights():
    return np.array([0.3, 0.3, 0.2, 0.2])


class TestMarkowitzOptimizer:

    def test_min_variance(self, sample_data):
        returns, cov = sample_data
        opt = MarkowitzOptimizer(returns, cov)
        w = opt.min_variance_portfolio()
        assert np.isclose(w.sum(), 1.0)
        assert np.all(w >= -0.001)

    def test_max_sharpe(self, sample_data):
        returns, cov = sample_data
        opt = MarkowitzOptimizer(returns, cov)
        w = opt.max_sharpe_portfolio(risk_free_rate=0.03)
        assert np.isclose(w.sum(), 1.0)

    def test_target_return(self, sample_data):
        returns, cov = sample_data
        opt = MarkowitzOptimizer(returns, cov)
        w = opt.target_return_portfolio(0.11)
        assert np.isclose(w.sum(), 1.0)
        assert np.isclose(opt._portfolio_return(w), 0.11, atol=0.01)

    def test_portfolio_return(self, sample_data):
        returns, cov = sample_data
        opt = MarkowitzOptimizer(returns, cov)
        w = np.array([0.25, 0.25, 0.25, 0.25])
        assert np.isclose(opt._portfolio_return(w), returns.mean())

    def test_min_variance_has_lower_risk_than_equal(self, sample_data):
        returns, cov = sample_data
        opt = MarkowitzOptimizer(returns, cov)
        w_mv = opt.min_variance_portfolio()
        w_eq = np.array([0.25, 0.25, 0.25, 0.25])
        assert opt._portfolio_std(w_mv) <= opt._portfolio_std(w_eq)


class TestBlackLittermanModel:

    def test_equilibrium_returns(self, sample_data, market_weights):
        _, cov = sample_data
        model = BlackLittermanModel(cov, market_weights, risk_aversion=2.5)
        pi = model.equilibrium_returns()
        assert len(pi) == len(market_weights)

    def test_bl_returns_without_views(self, sample_data, market_weights):
        _, cov = sample_data
        model = BlackLittermanModel(cov, market_weights)
        pi = model.bl_returns()
        assert len(pi) == len(market_weights)
        assert np.isclose(pi, model.equilibrium_returns(), atol=1e-6).all()

    def test_absolute_view(self, sample_data, market_weights):
        _, cov = sample_data
        model = BlackLittermanModel(cov, market_weights)
        model.add_absolute_view(0, 0.20)
        post = model.bl_returns()
        assert post[0] > model.equilibrium_returns()[0]

    def test_relative_view(self, sample_data, market_weights):
        _, cov = sample_data
        model = BlackLittermanModel(cov, market_weights)
        model.add_relative_view(0, 1, 0.05)
        post = model.bl_returns()
        assert post[0] > post[1]

    def test_bl_portfolio(self, sample_data, market_weights):
        _, cov = sample_data
        model = BlackLittermanModel(cov, market_weights)
        w = model.bl_portfolio()
        assert np.isclose(w.sum(), 1.0)

    def test_multiple_views(self, sample_data, market_weights):
        _, cov = sample_data
        model = BlackLittermanModel(cov, market_weights)
        model.add_absolute_view(0, 0.18)
        model.add_relative_view(1, 2, 0.03)
        post = model.bl_returns()
        assert len(post) == 4


class TestRiskParityOptimizer:

    def test_slsqp_weights_sum_to_one(self, sample_data):
        _, cov = sample_data
        opt = RiskParityOptimizer(cov)
        w = opt.optimize_slsqp()
        assert np.isclose(w.sum(), 1.0)

    def test_ccd_weights_sum_to_one(self, sample_data):
        _, cov = sample_data
        opt = RiskParityOptimizer(cov)
        w = opt.optimize_ccd()
        assert np.isclose(w.sum(), 1.0)

    def test_risk_contribution_equal_slsqp(self, sample_data):
        _, cov = sample_data
        opt = RiskParityOptimizer(cov)
        w = opt.optimize_slsqp()
        rc = opt._risk_contribution(w)
        rc_norm = rc / rc.sum()
        target = np.ones(len(w)) / len(w)
        assert np.allclose(rc_norm, target, atol=0.10)

    def test_risk_contribution_equal_ccd(self, sample_data):
        _, cov = sample_data
        opt = RiskParityOptimizer(cov)
        w = opt.optimize_ccd()
        rc = opt._risk_contribution(w)
        rc_norm = rc / rc.sum()
        target = np.ones(len(w)) / len(w)
        assert np.allclose(rc_norm, target, atol=0.10)

    def test_risk_parity_weights_function(self, sample_data):
        _, cov = sample_data
        w = risk_parity_weights(cov, method="slsqp")
        assert len(w) == len(cov)
        assert np.isclose(w.sum(), 1.0)


class TestEfficientFrontier:

    def test_compute_frontier(self, sample_data):
        returns, cov = sample_data
        ef = EfficientFrontier(returns, cov)
        frontier = ef.compute_frontier(n_points=10)
        assert frontier.shape[1] == 2
        assert len(frontier) >= 2

    def test_frontier_data(self, sample_data):
        returns, cov = sample_data
        ef = EfficientFrontier(returns, cov)
        risks, returns_list = ef.get_frontier_data(n_points=20)
        assert len(risks) == len(returns_list)

    def test_max_sharpe_point(self, sample_data):
        returns, cov = sample_data
        ef = EfficientFrontier(returns, cov)
        risk, ret = ef.get_max_sharpe_point(risk_free_rate=0.03)
        assert risk > 0
        assert ret > 0.03

    def test_frontier_risk_increases(self, sample_data):
        returns, cov = sample_data
        ef = EfficientFrontier(returns, cov)
        frontier = ef.compute_frontier(n_points=30)
        for i in range(1, len(frontier)):
            assert frontier[i, 0] >= frontier[i - 1, 0] - 1e-8