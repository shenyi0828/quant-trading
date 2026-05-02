"""参数优化器"""
from typing import Type, Dict, Any, List, Callable, Tuple
from multiprocessing import Pool, cpu_count
from datetime import date
import itertools

from data_center.api.data_api import DataAPI
from strategy_engine.base import BaseStrategy
from backtesting.engine import BacktestEngine
from backtesting.result import BacktestResult


def run_single_backtest(args: Tuple) -> Dict[str, Any]:
    data_api_path, strategy_class_name, symbol, start_date, end_date, initial_capital, commission_rate, params = args
    
    from data_center.api.data_api import DataAPI
    from strategy_engine.examples.dual_thrust import DualThrust
    
    strategy_class = DualThrust
    
    engine = BacktestEngine(
        data_api=DataAPI(),
        initial_capital=initial_capital,
        commission_rate=commission_rate
    )
    
    engine.add_strategy(
        strategy_class=strategy_class,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        params=params
    )
    
    try:
        result = engine.run()
        return {
            "params": params,
            "total_return": result.total_return,
            "sharpe_ratio": result.sharpe_ratio,
            "max_drawdown": result.max_drawdown,
            "trade_metrics": result.trade_metrics,
        }
    except Exception as e:
        return {
            "params": params,
            "error": str(e),
            "total_return": -1.0,
            "sharpe_ratio": -999.0,
            "max_drawdown": 1.0,
        }


class ParameterOptimizer:
    def __init__(
        self,
        data_api: DataAPI,
        strategy_class: Type[BaseStrategy],
        symbol: str,
        start_date: date,
        end_date: date,
        initial_capital: float = 100000,
        commission_rate: float = 0.001
    ):
        self.data_api = data_api
        self.strategy_class = strategy_class
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
    
    def grid_search(
        self,
        param_grid: Dict[str, List[Any]],
        n_workers: int = None,
        metric: str = "sharpe_ratio"
    ) -> List[Dict[str, Any]]:
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        
        param_combinations = list(itertools.product(*param_values))
        
        n_workers = n_workers or min(cpu_count(), len(param_combinations))
        
        args_list = [
            (
                "",
                self.strategy_class.__name__,
                self.symbol,
                self.start_date,
                self.end_date,
                self.initial_capital,
                self.commission_rate,
                dict(zip(param_names, combo))
            )
            for combo in param_combinations
        ]
        
        results = []
        with Pool(n_workers) as pool:
            results = pool.map(run_single_backtest, args_list)
        
        valid_results = [r for r in results if "error" not in r]
        
        valid_results.sort(key=lambda x: x.get(metric, 0), reverse=True)
        
        return valid_results
    
    def single_run(self, params: Dict[str, Any]) -> BacktestResult:
        engine = BacktestEngine(
            data_api=self.data_api,
            initial_capital=self.initial_capital,
            commission_rate=self.commission_rate
        )
        
        engine.add_strategy(
            strategy_class=self.strategy_class,
            symbol=self.symbol,
            start_date=self.start_date,
            end_date=self.end_date,
            params=params
        )
        
        return engine.run()