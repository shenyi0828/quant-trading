"""因子组合与信号生成"""
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from dataclasses import dataclass, field

from factor_engine.types import BaseFactor, SignalResult
from factor_engine.calculator import FactorCalculator
from factor_engine.normalization import normalize_factor


@dataclass
class FactorWeight:
    factor: BaseFactor
    weight: float = 1.0


class FactorPortfolio:
    def __init__(
        self,
        normalize: bool = True,
        normalize_method: str = "z_score"
    ):
        self.weights: List[FactorWeight] = []
        self.calculator = FactorCalculator(normalize=normalize, normalize_method=normalize_method)
    
    def add_factor(self, factor: BaseFactor, weight: float = 1.0):
        self.weights.append(FactorWeight(factor=factor, weight=weight))
    
    def clear_factors(self):
        self.weights.clear()
        self.calculator.clear_cache()
    
    def compute_scores(self, data: pd.DataFrame) -> pd.Series:
        if not self.weights:
            return pd.Series(0.0, index=data.index)
        
        total_weight = sum(w.weight for w in self.weights)
        
        factor_results = self.calculator.compute_multiple(
            [w.factor for w in self.weights],
            data,
            use_cache=True
        )
        
        scores = pd.Series(0.0, index=data.index)
        for fw in self.weights:
            result = factor_results[fw.factor.name]
            if result.normalized_values is not None:
                scores += result.normalized_values * fw.weight / total_weight
            else:
                scores += normalize_factor(result.values) * fw.weight / total_weight
        
        return scores
    
    def compute_signals(
        self,
        data: pd.DataFrame,
        top_pct: float = 0.2,
        bottom_pct: float = 0.2
    ) -> pd.DataFrame:
        scores = self.compute_scores(data)
        
        signals = pd.DataFrame(index=data.index)
        signals["score"] = scores
        
        signals["rank"] = scores.rank(ascending=True, pct=True)
        signals["bucket"] = pd.cut(scores.rank(pct=True), bins=10, labels=range(1, 11))
        
        signals["signal"] = 0
        top_threshold = scores.quantile(1 - top_pct)
        bottom_threshold = scores.quantile(bottom_pct)
        
        signals.loc[scores >= top_threshold, "signal"] = 1
        signals.loc[scores <= bottom_threshold, "signal"] = -1
        
        return signals
    
    def get_top_signals(
        self,
        data: pd.DataFrame,
        top_pct: float = 0.2
    ) -> pd.DataFrame:
        signals = self.compute_signals(data, top_pct=top_pct, bottom_pct=0)
        return signals[signals["signal"] == 1]
    
    def get_factor_correlations(self, data: pd.DataFrame) -> pd.DataFrame:
        if len(self.weights) < 2:
            return pd.DataFrame()
        
        results = self.calculator.compute_multiple(
            [w.factor for w in self.weights],
            data
        )
        
        factor_df = self.calculator.get_factor_dataframe(results)
        return factor_df.corr()
    
    def summary(self) -> Dict[str, Any]:
        return {
            "num_factors": len(self.weights),
            "factors": [
                {"name": fw.factor.name, "weight": fw.weight, "params": fw.factor.params}
                for fw in self.weights
            ],
            "total_weight": sum(fw.weight for fw in self.weights),
        }