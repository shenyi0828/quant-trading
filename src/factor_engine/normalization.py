"""因子标准化工具"""
import numpy as np
import pandas as pd
from typing import Optional


def z_score(series: pd.Series) -> pd.Series:
    mean = series.mean()
    std = series.std()
    if std == 0 or pd.isna(std):
        return pd.Series(0.0, index=series.index)
    return (series - mean) / std


def mad_outlier_removal(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    median = series.median()
    mad = np.median(np.abs(series - median))
    
    if mad == 0:
        return series
    
    deviation = np.abs(series - median) / mad
    upper_bound = median + threshold * mad
    lower_bound = median - threshold * mad
    
    return series.clip(lower=lower_bound, upper=upper_bound)


def winsorize(series: pd.Series, lower: float = 0.025, upper: float = 0.975) -> pd.Series:
    lower_val = series.quantile(lower)
    upper_val = series.quantile(upper)
    return series.clip(lower=lower_val, upper=upper_val)


def rank_normalize(series: pd.Series) -> pd.Series:
    return series.rank(pct=True)


def industry_neutralize(series: pd.Series, industry_map: Optional[pd.Series] = None) -> pd.Series:
    if industry_map is None:
        return z_score(series)
    
    result = pd.Series(index=series.index, dtype=float)
    for industry in industry_map.unique():
        mask = industry_map == industry
        result[mask] = z_score(series[mask])
    return result


def normalize_factor(
    series: pd.Series,
    method: str = "z_score",
    remove_outliers: bool = True,
    outlier_method: str = "mad",
    outlier_threshold: float = 3.0
) -> pd.Series:
    if remove_outliers:
        if outlier_method == "mad":
            series = mad_outlier_removal(series, outlier_threshold)
        elif outlier_method == "winsorize":
            series = winsorize(series)
    
    if method == "z_score":
        return z_score(series)
    elif method == "rank":
        return rank_normalize(series)
    else:
        return series