"""策略管理 API 路由

提供策略的创建、查询、更新、删除以及生命周期管理 REST API 端点。
"""
from datetime import datetime
from typing import Dict, Any, List, Optional, Type
from enum import Enum
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from dataclasses import dataclass, field

from strategy_engine.base import BaseStrategy
from strategy_engine.context import StrategyContext


router = APIRouter(prefix="/strategies", tags=["strategies"])


class StrategyStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class StrategyCreateRequest(BaseModel):
    name: str = Field(..., description="策略名称", min_length=1, max_length=100)
    class_name: str = Field(..., description="策略类名", min_length=1, max_length=100)
    symbol: str = Field(..., description="交易标的代码", min_length=1, max_length=20)
    params: Dict[str, Any] = Field(default_factory=dict, description="策略参数")
    initial_capital: float = Field(default=1000000.0, description="初始资金", gt=0)


class StrategyUpdateRequest(BaseModel):
    params: Dict[str, Any] = Field(..., description="策略参数")


class StrategyResponse(BaseModel):
    strategy_id: str = Field(..., description="策略ID")
    name: str = Field(..., description="策略名称")
    class_name: str = Field(..., description="策略类名")
    symbol: str = Field(..., description="交易标的代码")
    params: Dict[str, Any] = Field(default_factory=dict, description="策略参数")
    status: StrategyStatus = Field(..., description="策略状态")
    initial_capital: float = Field(..., description="初始资金")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")


class StrategyStatusResponse(BaseModel):
    strategy_id: str = Field(..., description="策略ID")
    status: StrategyStatus = Field(..., description="策略状态")
    cash: float = Field(..., description="可用现金")
    total_value: float = Field(..., description="总资产")
    total_profit: float = Field(..., description="总盈亏")
    return_rate: float = Field(..., description="收益率")
    positions: Dict[str, Any] = Field(default_factory=dict, description="持仓信息")
    orders_count: int = Field(default=0, description="订单数量")
    trades_count: int = Field(default=0, description="成交数量")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="错误详情")


@dataclass
class StrategyInfo:
    strategy_id: str
    name: str
    class_name: str
    symbol: str
    params: Dict[str, Any]
    initial_capital: float
    status: StrategyStatus = StrategyStatus.CREATED
    instance: Optional[BaseStrategy] = None
    context: Optional[StrategyContext] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class StrategyRegistry:
    def __init__(self):
        self._strategies: Dict[str, StrategyInfo] = {}
        self._strategy_classes: Dict[str, Type[BaseStrategy]] = {}
    
    def register_strategy_class(self, name: str, cls: Type[BaseStrategy]):
        self._strategy_classes[name] = cls
    
    def get_strategy_class(self, name: str) -> Optional[Type[BaseStrategy]]:
        return self._strategy_classes.get(name)
    
    def create_strategy(
        self,
        name: str,
        class_name: str,
        symbol: str,
        params: Dict[str, Any],
        initial_capital: float
    ) -> StrategyInfo:
        strategy_id = str(uuid.uuid4())
        info = StrategyInfo(
            strategy_id=strategy_id,
            name=name,
            class_name=class_name,
            symbol=symbol,
            params=params,
            initial_capital=initial_capital
        )
        self._strategies[strategy_id] = info
        return info
    
    def get_strategy(self, strategy_id: str) -> Optional[StrategyInfo]:
        return self._strategies.get(strategy_id)
    
    def get_all_strategies(self) -> List[StrategyInfo]:
        return list(self._strategies.values())
    
    def delete_strategy(self, strategy_id: str) -> bool:
        if strategy_id in self._strategies:
            del self._strategies[strategy_id]
            return True
        return False
    
    def update_strategy_params(
        self,
        strategy_id: str,
        params: Dict[str, Any]
    ) -> Optional[StrategyInfo]:
        info = self._strategies.get(strategy_id)
        if info:
            info.params = params
            info.updated_at = datetime.now()
            return info
        return None


_registry = StrategyRegistry()


def _get_strategy_or_404(strategy_id: str) -> StrategyInfo:
    info = _registry.get_strategy(strategy_id)
    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Strategy not found: {strategy_id}"
        )
    return info


@router.get(
    "/",
    response_model=List[StrategyResponse],
    summary="获取所有策略",
    description="获取所有策略列表。",
    responses={
        200: {"description": "策略列表", "model": List[StrategyResponse]},
    }
)
async def list_strategies() -> List[StrategyResponse]:
    strategies = _registry.get_all_strategies()
    return [
        StrategyResponse(
            strategy_id=s.strategy_id,
            name=s.name,
            class_name=s.class_name,
            symbol=s.symbol,
            params=s.params,
            status=s.status,
            initial_capital=s.initial_capital,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in strategies
    ]


@router.post(
    "/",
    response_model=StrategyResponse,
    status_code=201,
    summary="创建策略",
    description="创建一个新的策略配置。",
    responses={
        201: {"description": "策略创建成功", "model": StrategyResponse},
        400: {"description": "请求参数无效", "model": ErrorResponse},
    }
)
async def create_strategy(request: StrategyCreateRequest) -> StrategyResponse:
    strategy_class = _registry.get_strategy_class(request.class_name)
    if not strategy_class:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown strategy class: {request.class_name}"
        )
    
    info = _registry.create_strategy(
        name=request.name,
        class_name=request.class_name,
        symbol=request.symbol,
        params=request.params,
        initial_capital=request.initial_capital
    )
    
    return StrategyResponse(
        strategy_id=info.strategy_id,
        name=info.name,
        class_name=info.class_name,
        symbol=info.symbol,
        params=info.params,
        status=info.status,
        initial_capital=info.initial_capital,
        created_at=info.created_at,
        updated_at=info.updated_at,
    )


@router.get(
    "/{strategy_id}",
    response_model=StrategyResponse,
    summary="获取策略详情",
    description="根据策略ID获取策略详细信息。",
    responses={
        200: {"description": "策略详情", "model": StrategyResponse},
        404: {"description": "策略不存在", "model": ErrorResponse},
    }
)
async def get_strategy(strategy_id: str) -> StrategyResponse:
    info = _get_strategy_or_404(strategy_id)
    return StrategyResponse(
        strategy_id=info.strategy_id,
        name=info.name,
        class_name=info.class_name,
        symbol=info.symbol,
        params=info.params,
        status=info.status,
        initial_capital=info.initial_capital,
        created_at=info.created_at,
        updated_at=info.updated_at,
    )


@router.put(
    "/{strategy_id}",
    response_model=StrategyResponse,
    summary="更新策略参数",
    description="更新策略的参数配置。只能更新未运行状态的策略。",
    responses={
        200: {"description": "策略更新成功", "model": StrategyResponse},
        400: {"description": "策略状态不允许更新", "model": ErrorResponse},
        404: {"description": "策略不存在", "model": ErrorResponse},
    }
)
async def update_strategy(
    strategy_id: str,
    request: StrategyUpdateRequest
) -> StrategyResponse:
    info = _get_strategy_or_404(strategy_id)
    
    if info.status == StrategyStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Cannot update strategy while running. Please stop or pause first."
        )
    
    updated_info = _registry.update_strategy_params(strategy_id, request.params)
    if not updated_info:
        raise HTTPException(
            status_code=500,
            detail="Failed to update strategy"
        )
    
    return StrategyResponse(
        strategy_id=updated_info.strategy_id,
        name=updated_info.name,
        class_name=updated_info.class_name,
        symbol=updated_info.symbol,
        params=updated_info.params,
        status=updated_info.status,
        initial_capital=updated_info.initial_capital,
        created_at=updated_info.created_at,
        updated_at=updated_info.updated_at,
    )


@router.delete(
    "/{strategy_id}",
    status_code=204,
    summary="删除策略",
    description="删除指定的策略配置。",
    responses={
        204: {"description": "策略删除成功"},
        400: {"description": "策略状态不允许删除", "model": ErrorResponse},
        404: {"description": "策略不存在", "model": ErrorResponse},
    }
)
async def delete_strategy(strategy_id: str):
    info = _get_strategy_or_404(strategy_id)
    
    if info.status == StrategyStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete strategy while running. Please stop first."
        )
    
    success = _registry.delete_strategy(strategy_id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete strategy"
        )
    
    return None


@router.post(
    "/{strategy_id}/start",
    response_model=StrategyStatusResponse,
    summary="启动策略",
    description="启动策略实例，创建策略上下文并调用初始化方法。",
    responses={
        200: {"description": "策略启动成功", "model": StrategyStatusResponse},
        400: {"description": "策略状态不允许启动", "model": ErrorResponse},
        404: {"description": "策略不存在", "model": ErrorResponse},
        500: {"description": "策略启动失败", "model": ErrorResponse},
    }
)
async def start_strategy(strategy_id: str) -> StrategyStatusResponse:
    info = _get_strategy_or_404(strategy_id)
    
    if info.status == StrategyStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Strategy is already running"
        )
    
    strategy_class = _registry.get_strategy_class(info.class_name)
    if not strategy_class:
        raise HTTPException(
            status_code=500,
            detail=f"Strategy class not found: {info.class_name}"
        )
    
    try:
        instance = strategy_class(
            name=info.name,
            params=info.params
        )
        
        context = StrategyContext(initial_capital=info.initial_capital)
        
        instance.set_context(context)
        instance.set_symbol(info.symbol)
        
        instance.on_init()
        
        info.instance = instance
        info.context = context
        info.status = StrategyStatus.RUNNING
        info.error_message = None
        info.updated_at = datetime.now()
        
    except Exception as e:
        info.status = StrategyStatus.ERROR
        info.error_message = str(e)
        info.updated_at = datetime.now()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start strategy: {str(e)}"
        )
    
    return StrategyStatusResponse(
        strategy_id=info.strategy_id,
        status=info.status,
        cash=info.context.cash,
        total_value=info.context.total_value,
        total_profit=info.context.total_profit,
        return_rate=info.context.return_rate,
        positions={
            symbol: {
                "direction": pos.direction.value,
                "quantity": pos.quantity,
                "avg_cost": pos.avg_cost,
                "current_price": pos.current_price,
                "market_value": pos.market_value,
                "profit": pos.profit,
            }
            for symbol, pos in info.context.positions.items()
        },
        orders_count=len(info.context.orders),
        trades_count=len(info.context.trades),
    )


@router.post(
    "/{strategy_id}/stop",
    response_model=StrategyStatusResponse,
    summary="停止策略",
    description="停止运行中的策略实例。",
    responses={
        200: {"description": "策略停止成功", "model": StrategyStatusResponse},
        400: {"description": "策略状态不允许停止", "model": ErrorResponse},
        404: {"description": "策略不存在", "model": ErrorResponse},
    }
)
async def stop_strategy(strategy_id: str) -> StrategyStatusResponse:
    info = _get_strategy_or_404(strategy_id)
    
    if info.status not in [StrategyStatus.RUNNING, StrategyStatus.PAUSED]:
        raise HTTPException(
            status_code=400,
            detail="Strategy is not running or paused"
        )
    
    response = StrategyStatusResponse(
        strategy_id=info.strategy_id,
        status=StrategyStatus.STOPPED,
        cash=info.context.cash if info.context else 0,
        total_value=info.context.total_value if info.context else 0,
        total_profit=info.context.total_profit if info.context else 0,
        return_rate=info.context.return_rate if info.context else 0,
        positions={},
        orders_count=len(info.context.orders) if info.context else 0,
        trades_count=len(info.context.trades) if info.context else 0,
    )
    
    info.status = StrategyStatus.STOPPED
    info.instance = None
    info.context = None
    info.updated_at = datetime.now()
    
    return response


@router.post(
    "/{strategy_id}/pause",
    response_model=StrategyStatusResponse,
    summary="暂停策略",
    description="暂停运行中的策略实例。",
    responses={
        200: {"description": "策略暂停成功", "model": StrategyStatusResponse},
        400: {"description": "策略状态不允许暂停", "model": ErrorResponse},
        404: {"description": "策略不存在", "model": ErrorResponse},
    }
)
async def pause_strategy(strategy_id: str) -> StrategyStatusResponse:
    info = _get_strategy_or_404(strategy_id)
    
    if info.status != StrategyStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Strategy is not running"
        )
    
    context = info.context
    if context is None:
        raise HTTPException(
            status_code=500,
            detail="Strategy context not initialized"
        )
    
    info.status = StrategyStatus.PAUSED
    info.updated_at = datetime.now()
    
    return StrategyStatusResponse(
        strategy_id=info.strategy_id,
        status=info.status,
        cash=context.cash,
        total_value=context.total_value,
        total_profit=context.total_profit,
        return_rate=context.return_rate,
        positions={
            symbol: {
                "direction": pos.direction.value,
                "quantity": pos.quantity,
                "avg_cost": pos.avg_cost,
                "current_price": pos.current_price,
                "market_value": pos.market_value,
                "profit": pos.profit,
            }
            for symbol, pos in context.positions.items()
        },
        orders_count=len(context.orders),
        trades_count=len(context.trades),
    )


@router.get(
    "/{strategy_id}/status",
    response_model=StrategyStatusResponse,
    summary="获取策略状态",
    description="获取策略的运行状态和账户信息。",
    responses={
        200: {"description": "策略状态", "model": StrategyStatusResponse},
        404: {"description": "策略不存在", "model": ErrorResponse},
    }
)
async def get_strategy_status(strategy_id: str) -> StrategyStatusResponse:
    info = _get_strategy_or_404(strategy_id)
    
    if info.context:
        return StrategyStatusResponse(
            strategy_id=info.strategy_id,
            status=info.status,
            cash=info.context.cash,
            total_value=info.context.total_value,
            total_profit=info.context.total_profit,
            return_rate=info.context.return_rate,
            positions={
                symbol: {
                    "direction": pos.direction.value,
                    "quantity": pos.quantity,
                    "avg_cost": pos.avg_cost,
                    "current_price": pos.current_price,
                    "market_value": pos.market_value,
                    "profit": pos.profit,
                }
                for symbol, pos in info.context.positions.items()
            },
            orders_count=len(info.context.orders),
            trades_count=len(info.context.trades),
        )
    else:
        return StrategyStatusResponse(
            strategy_id=info.strategy_id,
            status=info.status,
            cash=0,
            total_value=0,
            total_profit=0,
            return_rate=0,
            positions={},
            orders_count=0,
            trades_count=0,
        )


def register_strategy_class(name: str, cls: Type[BaseStrategy]):
    _registry.register_strategy_class(name, cls)