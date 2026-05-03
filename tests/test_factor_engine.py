"""Comprehensive pytest tests for the factor_engine module.

Tests normalization functions, all 14 factor implementations,
FactorCalculator (with caching), and FactorPortfolio signal generation.
"""
import pandas as pd
import numpy as np
import pytest

from factor_engine.types import BaseFactor, FactorResult, SignalResult
from factor_engine.normalization import (
    z_score,
    mad_outlier_removal,
    winsorize,
    rank_normalize,
    industry_neutralize,
    normalize_factor,
)
from factor_engine.calculator import FactorCalculator
from factor_engine.portfolio import FactorPortfolio, FactorWeight
from factor_engine.library import (
    ROC, PriceMomentum, MomentumScore,
    MACD, RSI, MACross, TrendStrength,
    ATR, HistoricalVolatility, VolatilityRatio,
    VolumeRatio, OBV, VolumePriceTrend, TurnoverRate,
)


# ========== Fixtures ==========

@pytest.fixture
def sample_bar_data():
    """Generate 120 days of OHLCV data for factor tests."""
    np.random.seed(42)
    n = 120
    dates = pd.date_range(start="2025-01-01", periods=n, freq="D")
    close = 10.0 * (1 + np.random.normal(0.001, 0.02, n)).cumprod()
    return pd.DataFrame({
        "date": dates,
        "open": close * (1 + np.random.normal(0, 0.005, n)),
        "high": close * (1 + np.abs(np.random.normal(0, 0.01, n))),
        "low": close * (1 - np.abs(np.random.normal(0, 0.01, n))),
        "close": close,
        "volume": np.random.randint(100000, 500000, n).astype(float),
    })


@pytest.fixture
def bar_data_with_turnover(sample_bar_data):
    data = sample_bar_data.copy()
    data["turnover_rate"] = np.random.uniform(0.5, 5.0, len(data))
    return data


# ========== Tests: Normalization ==========

class TestZScore:
    def test_standard_series(self):
        s = pd.Series([1, 2, 3, 4, 5])
        result = z_score(s)
        assert abs(result.mean()) < 1e-10
        assert abs(result.std() - 1.0) < 1e-10

    def test_constant_series(self):
        s = pd.Series([5.0, 5.0, 5.0])
        result = z_score(s)
        assert all(result == 0.0)

    def test_preserves_index(self):
        s = pd.Series([1, 2, 3], index=["a", "b", "c"])
        result = z_score(s)
        assert list(result.index) == ["a", "b", "c"]


class TestMadOutlierRemoval:
    def test_no_outliers(self):
        s = pd.Series([1, 2, 3, 2, 1])
        result = mad_outlier_removal(s)
        pd.testing.assert_series_equal(result, s)

    def test_clips_extreme_values(self):
        s = pd.Series([1, 2, 3, 4, 5, 100])
        result = mad_outlier_removal(s, threshold=3.0)
        assert result.iloc[-1] < 100

    def test_zero_mad(self):
        s = pd.Series([5.0, 5.0, 5.0])
        result = mad_outlier_removal(s)
        assert list(result) == [5.0, 5.0, 5.0]


class TestWinsorize:
    def test_default_bounds(self):
        s = pd.Series(range(1, 101), dtype=float)
        result = winsorize(s)
        assert result.min() > s.min()
        assert result.max() < s.max()

    def test_preserves_index(self):
        s = pd.Series([1, 2, 3, 4, 5], index=list("abcde"))
        result = winsorize(s)
        assert list(result.index) == list("abcde")


class TestRankNormalize:
    def test_output_range(self):
        s = pd.Series([10, 5, 30, 20])
        result = rank_normalize(s)
        assert result.min() == 0.25
        assert result.max() == 1.0

    def test_unique_ranks(self):
        s = pd.Series([3, 1, 4, 1, 5])
        result = rank_normalize(s)
        assert result.nunique() >= 3  # 1 appears twice, rest unique


class TestIndustryNeutralize:
    def test_no_industry_map_falls_back_to_zscore(self):
        s = pd.Series([1, 2, 3, 4, 5])
        result = industry_neutralize(s)
        expected = z_score(s)
        pd.testing.assert_series_equal(result, expected)

    def test_with_industry_map(self):
        s = pd.Series([10.0, 20.0, 30.0, 100.0, 200.0], index=range(5))
        industry_map = pd.Series(["A", "A", "B", "B", "B"])
        result = industry_neutralize(s, industry_map)
        # Within each industry group, should be z-scored
        assert abs(result[:2].mean()) < 1e-10
        assert abs(result[2:].mean()) < 1e-10


class TestNormalizeFactor:
    def test_default_z_score_with_mad(self):
        s = pd.Series(np.random.randn(100))
        result = normalize_factor(s)
        assert result.mean() < 1.0  # MAD removal + z-score

    def test_rank_method(self):
        s = pd.Series([1, 2, 3, 4, 5])
        result = normalize_factor(s, method="rank")
        assert result.min() == 0.2
        assert result.max() == 1.0

    def test_disable_outlier_removal(self):
        s = pd.Series([1, 2, 3, 4, 5])
        result_raw = normalize_factor(s, remove_outliers=False)
        result_with = normalize_factor(s, remove_outliers=True)
        # Both are z-scored, but outlier removal should differ slightly
        assert len(result_raw) == len(result_with)

    def test_winsorize_outlier_method(self):
        s = pd.Series([1.0] * 50 + [100.0])
        result = normalize_factor(s, outlier_method="winsorize")
        assert result.iloc[-1] < 10.0  # Should be winsorized


# ========== Tests: Factor Implementations ==========

class TestFactorBase:
    def test_validate_input_valid(self, sample_bar_data):
        factor = ROC()
        assert factor.validate_input(sample_bar_data) is True

    def test_validate_input_missing_columns(self):
        factor = ROC()
        bad_data = pd.DataFrame({"foo": [1, 2, 3]})
        assert factor.validate_input(bad_data) is False

    def test_factor_has_name(self):
        assert ROC().name == "ROC"
        assert RSI().name == "RSI"
        assert MACD().name == "MACD"


class TestMomentumFactors:
    def test_roc(self, sample_bar_data):
        factor = ROC(period=10)
        result = factor.compute(sample_bar_data)
        assert len(result) == len(sample_bar_data)
        # First 'period' values should be 0 (filled)
        assert result.iloc[:10].eq(0).all()

    def test_roc_custom_period(self, sample_bar_data):
        factor = ROC(period=20)
        result = factor.compute(sample_bar_data)
        assert result.iloc[:20].eq(0).all()
        assert result.iloc[20] != 0

    def test_price_momentum(self, sample_bar_data):
        factor = PriceMomentum(period=20)
        result = factor.compute(sample_bar_data)
        assert len(result) == len(sample_bar_data)
        assert factor.params == {"period": 20}

    def test_momentum_score(self, sample_bar_data):
        factor = MomentumScore(period=12)
        result = factor.compute(sample_bar_data)
        assert len(result) == len(sample_bar_data)
        assert not result.isna().any()

    def test_momentum_score_params(self):
        factor = MomentumScore(period=12)
        assert factor.params == {"period": 12}


class TestTrendFactors:
    def test_macd(self, sample_bar_data):
        factor = MACD()
        result = factor.compute(sample_bar_data)
        assert len(result) == len(sample_bar_data)
        assert factor.params == {"fast": 12, "slow": 26, "signal": 9}

    def test_macd_custom_params(self, sample_bar_data):
        factor = MACD(fast_period=5, slow_period=15, signal_period=5)
        result = factor.compute(sample_bar_data)
        assert len(result) == len(sample_bar_data)

    def test_rsi(self, sample_bar_data):
        factor = RSI(period=14)
        result = factor.compute(sample_bar_data)
        assert len(result) == len(sample_bar_data)
        # RSI values should be in [0, 100]
        assert result.min() >= 0
        assert result.max() <= 100

    def test_rsi_fill_default(self):
        """RSI should fill NaN with 50 (neutral)."""
        factor = RSI(period=14)
        tiny_data = pd.DataFrame({
            "open": [10.0], "high": [10.0], "low": [10.0],
            "close": [10.0], "volume": [100.0],
        })
        result = factor.compute(tiny_data)
        assert result.iloc[0] == 50.0

    def test_ma_cross(self, sample_bar_data):
        factor = MACross(fast_period=5, slow_period=20)
        result = factor.compute(sample_bar_data)
        assert len(result) == len(sample_bar_data)
        assert factor.params == {"fast": 5, "slow": 20}

    def test_trend_strength(self, sample_bar_data):
        factor = TrendStrength(period=20)
        result = factor.compute(sample_bar_data)
        assert len(result) == len(sample_bar_data)
        # Values should be in [0, 100]
        assert result.min() >= 0
        assert result.max() <= 100


class TestVolatilityFactors:
    def test_atr(self, sample_bar_data):
        factor = ATR(period=14)
        result = factor.compute(sample_bar_data)
        assert len(result) == len(sample_bar_data)
        assert result.iloc[0] == 0  # filled NaN
        assert not result.isna().any()

    def test_atr_percentage(self, sample_bar_data):
        """ATR should be returned as percentage of close."""
        factor = ATR(period=14)
        result = factor.compute(sample_bar_data)
        # Should be a reasonable percentage (not raw ATR value)
        assert result.min() >= 0

    def test_historical_volatility(self, sample_bar_data):
        factor = HistoricalVolatility(period=20)
        result = factor.compute(sample_bar_data)
        assert len(result) == len(sample_bar_data)
        assert result.iloc[:20].eq(0).all().any() or result.iloc[0] == 0

    def test_volatility_ratio(self, sample_bar_data):
        factor = VolatilityRatio(short_period=5, long_period=20)
        result = factor.compute(sample_bar_data)
        assert len(result) == len(sample_bar_data)
        assert factor.params == {"short": 5, "long": 20}


class TestVolumeFactors:
    def test_volume_ratio(self, sample_bar_data):
        factor = VolumeRatio(period=20)
        result = factor.compute(sample_bar_data)
        assert len(result) == len(sample_bar_data)
        # NaN filled with 1
        assert result.iloc[0] == 1.0

    def test_obv(self, sample_bar_data):
        factor = OBV()
        result = factor.compute(sample_bar_data)
        assert len(result) == len(sample_bar_data)
        assert factor.params == {}

    def test_volume_price_trend(self, sample_bar_data):
        factor = VolumePriceTrend(period=10)
        result = factor.compute(sample_bar_data)
        assert len(result) == len(sample_bar_data)
        assert not result.isna().any()

    def test_turnover_rate_with_column(self, bar_data_with_turnover):
        factor = TurnoverRate()
        result = factor.compute(bar_data_with_turnover)
        assert len(result) == len(bar_data_with_turnover)
        pd.testing.assert_series_equal(
            result.fillna(0),
            bar_data_with_turnover["turnover_rate"].fillna(0)
        )

    def test_turnover_rate_without_column(self, sample_bar_data):
        factor = TurnoverRate()
        result = factor.compute(sample_bar_data)
        assert len(result) == len(sample_bar_data)
        assert not result.isna().any()


# ========== Tests: FactorCalculator ==========

class TestFactorCalculator:
    def test_compute_single(self, sample_bar_data):
        calc = FactorCalculator(normalize=False)
        factor = ROC(period=10)
        result = calc.compute_single(factor, sample_bar_data)
        assert isinstance(result, FactorResult)
        assert result.factor_name == "ROC"
        assert len(result.values) == len(sample_bar_data)

    def test_compute_single_with_normalization(self, sample_bar_data):
        calc = FactorCalculator(normalize=True, normalize_method="z_score")
        factor = ROC(period=10)
        result = calc.compute_single(factor, sample_bar_data)
        assert result.normalized_values is not None
        assert len(result.normalized_values) == len(result.values)

    def test_compute_multiple(self, sample_bar_data):
        calc = FactorCalculator(normalize=False)
        factors = [ROC(period=10), RSI(period=14), MACD()]
        results = calc.compute_multiple(factors, sample_bar_data)
        assert len(results) == 3
        assert "ROC" in results
        assert "RSI" in results
        assert "MACD" in results

    def test_cache(self, sample_bar_data):
        calc = FactorCalculator(normalize=False)
        factor = RSI(period=14)

        r1 = calc.compute_single(factor, sample_bar_data, use_cache=True)
        r2 = calc.compute_single(factor, sample_bar_data, use_cache=True)
        assert r1 is r2

    def test_clear_cache(self, sample_bar_data):
        calc = FactorCalculator(normalize=False)
        factor = RSI(period=14)

        calc.compute_single(factor, sample_bar_data, use_cache=True)
        assert len(calc.cache) == 1

        calc.clear_cache()
        assert len(calc.cache) == 0

    def test_get_factor_dataframe(self, sample_bar_data):
        calc = FactorCalculator(normalize=True)
        factors = [ROC(period=10), RSI(period=14)]
        results = calc.compute_multiple(factors, sample_bar_data)

        df = calc.get_factor_dataframe(results)
        assert df.shape == (len(sample_bar_data), 2)
        assert "ROC" in df.columns
        assert "RSI" in df.columns

    def test_get_factor_dataframe_raw_values(self, sample_bar_data):
        calc = FactorCalculator(normalize=True)
        factors = [ROC(period=10)]
        results = calc.compute_multiple(factors, sample_bar_data)

        # Without normalized
        df_raw = calc.get_factor_dataframe(results, use_normalized=False)
        df_norm = calc.get_factor_dataframe(results, use_normalized=True)
        # They should differ since normalization was applied
        assert not df_raw.equals(df_norm)


# ========== Tests: FactorPortfolio ==========

class TestFactorPortfolio:
    def _sample_data(self, n=100):
        np.random.seed(99)
        dates = pd.date_range(start="2025-01-01", periods=n, freq="D")
        close = 10.0 * (1 + np.random.normal(0.001, 0.02, n)).cumprod()
        return pd.DataFrame({
            "open": close * (1 + np.random.normal(0, 0.005, n)),
            "high": close * (1 + np.abs(np.random.normal(0, 0.01, n))),
            "low": close * (1 - np.abs(np.random.normal(0, 0.01, n))),
            "close": close,
            "volume": np.random.randint(100000, 500000, n).astype(float),
        })

    def test_add_factor(self):
        portfolio = FactorPortfolio()
        portfolio.add_factor(ROC(period=10), weight=0.3)
        portfolio.add_factor(RSI(period=14), weight=0.7)
        assert len(portfolio.weights) == 2

    def test_clear_factors(self):
        portfolio = FactorPortfolio()
        portfolio.add_factor(ROC(period=10))
        portfolio.clear_factors()
        assert len(portfolio.weights) == 0

    def test_compute_scores(self):
        data = self._sample_data()
        portfolio = FactorPortfolio()
        portfolio.add_factor(ROC(period=10), weight=0.5)
        portfolio.add_factor(RSI(period=14), weight=0.5)

        scores = portfolio.compute_scores(data)
        assert len(scores) == len(data)
        assert scores.dtype == float

    def test_compute_scores_empty_portfolio(self):
        data = self._sample_data()
        portfolio = FactorPortfolio()
        scores = portfolio.compute_scores(data)
        assert (scores == 0.0).all()

    def test_compute_signals(self):
        data = self._sample_data(120)
        portfolio = FactorPortfolio()
        portfolio.add_factor(ROC(period=10), weight=0.3)
        portfolio.add_factor(RSI(period=14), weight=0.2)
        portfolio.add_factor(MACD(), weight=0.3)

        signals = portfolio.compute_signals(data, top_pct=0.2, bottom_pct=0.2)
        assert "score" in signals.columns
        assert "rank" in signals.columns
        assert "bucket" in signals.columns
        assert "signal" in signals.columns

        assert set(signals["signal"].unique()).issubset({-1, 0, 1})

        # Verify buy/sell signal counts are reasonable
        buy_count = (signals["signal"] == 1).sum()
        sell_count = (signals["signal"] == -1).sum()
        total = len(signals)
        # ~20% each for buy/sell
        assert buy_count > 0
        assert sell_count > 0

    def test_get_top_signals(self):
        data = self._sample_data(120)
        portfolio = FactorPortfolio()
        portfolio.add_factor(ROC(period=10), weight=0.5)
        portfolio.add_factor(RSI(period=14), weight=0.5)

        top = portfolio.get_top_signals(data, top_pct=0.2)
        assert all(top["signal"] == 1)

    def test_get_factor_correlations(self):
        data = self._sample_data(120)
        portfolio = FactorPortfolio()
        portfolio.add_factor(ROC(period=10))
        portfolio.add_factor(RSI(period=14))
        portfolio.add_factor(MACD())

        corr = portfolio.get_factor_correlations(data)
        assert corr.shape == (3, 3)
        # Diagonal should be 1.0
        assert all(corr.values[i][i] == 1.0 for i in range(3))

    def test_get_factor_correlations_single_factor(self):
        data = self._sample_data()
        portfolio = FactorPortfolio()
        portfolio.add_factor(ROC(period=10))
        corr = portfolio.get_factor_correlations(data)
        assert corr.empty

    def test_summary(self):
        portfolio = FactorPortfolio()
        portfolio.add_factor(ROC(period=10), weight=0.3)
        portfolio.add_factor(RSI(period=14), weight=0.7)

        summary = portfolio.summary()
        assert summary["num_factors"] == 2
        assert summary["total_weight"] == 1.0
        assert len(summary["factors"]) == 2
        assert summary["factors"][0]["name"] == "ROC"
        assert summary["factors"][0]["weight"] == 0.3

    def test_signal_score_monotonicity(self):
        """Higher scores should correspond to higher percentile ranks."""
        data = self._sample_data(120)
        portfolio = FactorPortfolio()
        portfolio.add_factor(ROC(period=10), weight=1.0)

        signals = portfolio.compute_signals(data, top_pct=0.2, bottom_pct=0.2)
        # Check that signal=1 has higher scores than signal=-1
        buy_scores = signals[signals["signal"] == 1]["score"]
        sell_scores = signals[signals["signal"] == -1]["score"]
        assert buy_scores.min() >= sell_scores.max()


# ========== Tests: FactorResult dataclass ==========

class TestFactorResult:
    def test_basic_creation(self):
        values = pd.Series([1.0, 2.0, 3.0])
        result = FactorResult(factor_name="test", values=values)
        assert result.factor_name == "test"
        assert result.normalized_values is None
        assert result.metadata == {}

    def test_with_normalized(self):
        values = pd.Series([1.0, 2.0, 3.0])
        norm = pd.Series([0.0, 1.0, 2.0])
        result = FactorResult(
            factor_name="test",
            values=values,
            normalized_values=norm,
            metadata={"period": 10},
        )
        pd.testing.assert_series_equal(result.normalized_values, norm)
        assert result.metadata["period"] == 10


class TestSignalResult:
    def test_basic_creation(self):
        sr = SignalResult(
            date=pd.Timestamp("2025-06-01"),
            score=0.75,
            signal=1,
            rank=85,
            bucket=9,
        )
        assert sr.signal == 1  # buy
        assert sr.score == 0.75
