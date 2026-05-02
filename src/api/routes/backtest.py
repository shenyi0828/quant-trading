from typing import Dict, List, Any, Optional, Type
from datetime import date
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from dataclasses import dataclass
import uuid

from backtesting.engine import BacktestEngine
from backtesting.result import BacktestResult
from data_center.api.data_api import DataAPI
from strategy_engine.base import BaseStrategy
from strategy_engine.examples.dual_thrust import DualThrust

router = APIRouter(prefix="/backtest", tags=["backtest"])


class BacktestRunRequest(BaseModel):
    strategy_type: str = Field(default="DualThrust")
    symbol: str
    start_date: date
    end_date: date
    initial_capital: float = Field(default=100000.0)
    params: Optional[Dict[str, Any]] = None


class BacktestSummaryResponse(BaseModel):
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    final_value: float
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float


class TradeResponse(BaseModel):
    trade_id: str
    order_id: str
    symbol: str
    direction: str
    price: float
    quantity: int
    timestamp: str
    commission: float


class DailyValueResponse(BaseModel):
    date: str
    value: float


class BacktestResultResponse(BaseModel):
    id: str
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    final_value: float
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    days: int


@dataclass
class BacktestRegistry:
    results: Dict[str, BacktestResult] = None
    data_api: DataAPI = None
    
    def __post_init__(self):
        self.results = {}
        self.data_api = DataAPI()
    
    def run_backtest(
        self,
        strategy_cls: Type[BaseStrategy],
        symbol: str,
        start_date: date,
        end_date: date,
        initial_capital: float,
        params: Dict[str, Any]
    ) -> BacktestResult:
        engine = BacktestEngine(
            data_api=self.data_api,
            initial_capital=initial_capital
        )
        engine.add_strategy(
            strategy_class=strategy_cls,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            params=params
        )
        return engine.run()
    
    def store_result(self, result: BacktestResult) -> str:
        result_id = str(uuid.uuid4())
        self.results[result_id] = result
        return result_id
    
    def get_result(self, result_id: str) -> Optional[BacktestResult]:
        return self.results.get(result_id)


_backtest_registry: BacktestRegistry = BacktestRegistry()
_available_strategies: Dict[str, Type[BaseStrategy]] = {
    "DualThrust": DualThrust
}


def get_backtest_registry() -> BacktestRegistry:
    return _backtest_registry


def register_backtest_strategy(name: str, cls: Type[BaseStrategy]) -> None:
    _available_strategies[name] = cls


@router.post("/run", response_model=BacktestResultResponse)
def run_backtest(request: BacktestRunRequest) -> BacktestResultResponse:
    registry = get_backtest_registry()
    
    strategy_cls = _available_strategies.get(request.strategy_type)
    if strategy_cls is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown strategy type: {request.strategy_type}"
        )
    
    try:
        result = registry.run_backtest(
            strategy_cls=strategy_cls,
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            params=request.params or {}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    result_id = registry.store_result(result)
    
    return BacktestResultResponse(
        id=result_id,
        strategy_name=result.strategy_name,
        symbol=result.symbol,
        start_date=str(result.start_date),
        end_date=str(result.end_date),
        initial_capital=result.initial_capital,
        final_value=result.final_value,
        total_return=result.total_return,
        annualized_return=result.annualized_return,
        max_drawdown=result.max_drawdown,
        sharpe_ratio=result.sharpe_ratio,
        days=result.days
    )


@router.get("/results/{result_id}", response_model=BacktestResultResponse)
def get_backtest_result(result_id: str) -> BacktestResultResponse:
    registry = get_backtest_registry()
    result = registry.get_result(result_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Backtest result not found: {result_id}")
    
    return BacktestResultResponse(
        id=result_id,
        strategy_name=result.strategy_name,
        symbol=result.symbol,
        start_date=str(result.start_date),
        end_date=str(result.end_date),
        initial_capital=result.initial_capital,
        final_value=result.final_value,
        total_return=result.total_return,
        annualized_return=result.annualized_return,
        max_drawdown=result.max_drawdown,
        sharpe_ratio=result.sharpe_ratio,
        days=result.days
    )


@router.get("/results/{result_id}/summary", response_model=BacktestSummaryResponse)
def get_backtest_summary(result_id: str) -> BacktestSummaryResponse:
    registry = get_backtest_registry()
    result = registry.get_result(result_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Backtest result not found: {result_id}")
    
    return BacktestSummaryResponse(
        strategy_name=result.strategy_name,
        symbol=result.symbol,
        start_date=str(result.start_date),
        end_date=str(result.end_date),
        initial_capital=result.initial_capital,
        final_value=result.final_value,
        total_return=result.total_return,
        annualized_return=result.annualized_return,
        max_drawdown=result.max_drawdown,
        sharpe_ratio=result.sharpe_ratio
    )


@router.get("/results/{result_id}/trades", response_model=List[TradeResponse])
def get_backtest_trades(result_id: str) -> List[TradeResponse]:
    registry = get_backtest_registry()
    result = registry.get_result(result_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Backtest result not found: {result_id}")
    
    return [
        TradeResponse(
            trade_id=t.trade_id,
            order_id=t.order_id,
            symbol=t.symbol,
            direction=t.direction.value,
            price=t.price,
            quantity=t.quantity,
            timestamp=str(t.timestamp),
            commission=t.commission
        )
        for t in result.trades
    ]


@router.get("/results/{result_id}/daily-values", response_model=List[DailyValueResponse])
def get_backtest_daily_values(result_id: str) -> List[DailyValueResponse]:
    registry = get_backtest_registry()
    result = registry.get_result(result_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Backtest result not found: {result_id}")
    
    start = result.start_date
    
    return [
        DailyValueResponse(
            date=str(start + __import__("datetime").timedelta(days=i)) if i > 0 else str(start),
            value=v
        )
        for i, v in enumerate(result.daily_values)
    ]


@router.get("/strategies")
def list_available_strategies() -> List[Dict[str, str]]:
    return [
        {"name": name, "class": cls.__name__}
        for name, cls in _available_strategies.items()
    ]