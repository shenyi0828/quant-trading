"""因子引擎模块"""
from factor_engine.types import BaseFactor, FactorResult, SignalResult
from factor_engine.calculator import FactorCalculator
from factor_engine.portfolio import FactorPortfolio, FactorWeight
from factor_engine.normalization import (
    z_score,
    mad_outlier_removal,
    winsorize,
    rank_normalize,
    normalize_factor,
)

__all__ = [
    "BaseFactor",
    "FactorResult",
    "SignalResult",
    "FactorCalculator",
    "FactorPortfolio",
    "FactorWeight",
    "z_score",
    "mad_outlier_removal",
    "winsorize",
    "rank_normalize",
    "normalize_factor",
]