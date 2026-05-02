"""因子计算器"""
from typing import Dict, List, Optional, Any
import pandas as pd

from factor_engine.types import BaseFactor, FactorResult
from factor_engine.normalization import normalize_factor


class FactorCalculator:
    def __init__(self, normalize: bool = True, normalize_method: str = "z_score"):
        self.normalize = normalize
        self.normalize_method = normalize_method
        self.cache: Dict[str, FactorResult] = {}
    
    def compute_single(
        self, 
        factor: BaseFactor, 
        data: pd.DataFrame,
        use_cache: bool = False
    ) -> FactorResult:
        cache_key = f"{factor.name}_{factor.params}"
        
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        values = factor.compute(data)
        
        normalized = None
        if self.normalize:
            normalized = normalize_factor(values, method=self.normalize_method)
        
        result = FactorResult(
            factor_name=factor.name,
            values=values,
            normalized_values=normalized,
            metadata={"params": factor.params}
        )
        
        if use_cache:
            self.cache[cache_key] = result
        
        return result
    
    def compute_multiple(
        self,
        factors: List[BaseFactor],
        data: pd.DataFrame,
        use_cache: bool = False
    ) -> Dict[str, FactorResult]:
        results = {}
        for factor in factors:
            results[factor.name] = self.compute_single(factor, data, use_cache)
        return results
    
    def clear_cache(self):
        self.cache.clear()
    
    def get_factor_dataframe(
        self,
        results: Dict[str, FactorResult],
        use_normalized: bool = True
    ) -> pd.DataFrame:
        df = pd.DataFrame(index=results[list(results.keys())[0]].values.index)
        for name, result in results.items():
            if use_normalized and result.normalized_values is not None:
                df[name] = result.normalized_values
            else:
                df[name] = result.values
        return df