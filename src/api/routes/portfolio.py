from datetime import date
from typing import Dict, List, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from portfolio import (
    PortfolioManager,
    AccountStatus,
    AllocationMethod,
)


router = APIRouter(prefix="/portfolio", tags=["portfolio"])


class AllocationMethodEnum(str, Enum):
    EQUAL_WEIGHT = "equal_weight"
    RISK_PARITY = "risk_parity"
    MANUAL = "manual"


class AccountStatusEnum(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class AccountStatusUpdateRequest(BaseModel):
    status: AccountStatusEnum = Field(..., description="目标状态")


class AccountCreateRequest(BaseModel):
    strategy_name: str = Field(..., description="策略名称", min_length=1, max_length=100)
    initial_capital: Optional[float] = Field(default=None, description="初始资金", ge=0)
    account_id: Optional[str] = Field(default=None, description="账户ID，不指定则自动生成")


class AccountResponse(BaseModel):
    account_id: str = Field(..., description="账户ID")
    strategy_name: str = Field(..., description="策略名称")
    initial_capital: float = Field(..., description="初始资金")
    total_value: float = Field(..., description="账户总市值")
    cash: float = Field(..., description="现金余额")
    total_profit: float = Field(..., description="总盈亏")
    return_rate: float = Field(..., description="收益率")
    status: AccountStatusEnum = Field(..., description="账户状态")
    position_count: int = Field(..., description="持仓数量")


class PositionResponse(BaseModel):
    symbol: str = Field(..., description="证券代码")
    quantity: int = Field(..., description="持仓数量")
    avg_cost: float = Field(..., description="平均成本")
    current_price: float = Field(..., description="当前价格")
    market_value: float = Field(..., description="市值")
    profit: float = Field(..., description="持仓盈亏")
    profit_pct: float = Field(..., description="盈亏百分比")


class PortfolioSummaryResponse(BaseModel):
    total_capital: float = Field(..., description="总资金")
    total_value: float = Field(..., description="组合总市值")
    total_profit: float = Field(..., description="组合总盈亏")
    return_rate: float = Field(..., description="组合收益率")
    account_count: int = Field(..., description="账户总数")
    active_accounts: int = Field(..., description="活跃账户数")
    position_count: int = Field(..., description="持仓数量")
    accounts: List[Dict] = Field(default_factory=list, description="账户摘要列表")
    positions: List[Dict] = Field(default_factory=list, description="持仓摘要列表")


class PnLSnapshotResponse(BaseModel):
    account_id: str = Field(..., description="账户ID")
    date: str = Field(..., description="日期")
    total_value: float = Field(..., description="账户总市值")
    cash: float = Field(..., description="现金余额")
    position_value: float = Field(..., description="持仓市值")
    position_profit: float = Field(..., description="持仓盈亏")
    daily_profit: float = Field(..., description="日盈亏")
    cumulative_profit: float = Field(..., description="累计盈亏")
    return_rate: float = Field(..., description="收益率")


class AllocateRequest(BaseModel):
    method: AllocationMethodEnum = Field(
        default=AllocationMethodEnum.EQUAL_WEIGHT,
        description="分配方法"
    )
    weights: Optional[Dict[str, float]] = Field(
        default=None,
        description="手动分配权重，method=manual时必填"
    )


class AllocationResponse(BaseModel):
    account_id: str = Field(..., description="账户ID")
    allocated_capital: float = Field(..., description="分配资金")
    weight: float = Field(..., description="权重")
    method: str = Field(..., description="分配方法")


class RebalanceRequest(BaseModel):
    method: AllocationMethodEnum = Field(
        default=AllocationMethodEnum.EQUAL_WEIGHT,
        description="再平衡方法"
    )


_portfolio_manager: Optional[PortfolioManager] = None


def get_portfolio_manager() -> PortfolioManager:
    global _portfolio_manager
    if _portfolio_manager is None:
        _portfolio_manager = PortfolioManager(total_capital=1_000_000.0)
    return _portfolio_manager


def _convert_status(status: AccountStatusEnum) -> AccountStatus:
    return AccountStatus(status.value)


def _convert_allocation_method(method: AllocationMethodEnum) -> AllocationMethod:
    return AllocationMethod(method.value)


def _account_to_response(account) -> AccountResponse:
    return AccountResponse(
        account_id=account.account_id,
        strategy_name=account.strategy_name,
        initial_capital=account.initial_capital,
        total_value=account.total_value,
        cash=account.cash,
        total_profit=account.total_profit,
        return_rate=account.return_rate,
        status=AccountStatusEnum(account.status.value),
        position_count=len(account.positions),
    )


def _position_to_response(position) -> PositionResponse:
    return PositionResponse(
        symbol=position.symbol,
        quantity=position.quantity,
        avg_cost=position.avg_cost,
        current_price=position.current_price,
        market_value=position.market_value,
        profit=position.profit,
        profit_pct=position.profit_pct,
    )


def _pnl_to_response(pnl) -> PnLSnapshotResponse:
    return PnLSnapshotResponse(
        account_id=pnl.account_id,
        date=str(pnl.date),
        total_value=pnl.total_value,
        cash=pnl.cash,
        position_value=pnl.position_value,
        position_profit=pnl.position_profit,
        daily_profit=pnl.daily_profit,
        cumulative_profit=pnl.cumulative_profit,
        return_rate=pnl.return_rate,
    )


@router.get(
    "/summary",
    response_model=PortfolioSummaryResponse,
    summary="获取组合摘要",
    description="获取投资组合的整体摘要信息，包括总资产、盈亏、账户和持仓概览。",
)
async def get_portfolio_summary(
    manager: PortfolioManager = Query(default_factory=get_portfolio_manager)
) -> PortfolioSummaryResponse:
    summary = manager.get_summary()
    return PortfolioSummaryResponse(
        total_capital=summary.total_capital,
        total_value=summary.total_value,
        total_profit=summary.total_profit,
        return_rate=summary.return_rate,
        account_count=summary.account_count,
        active_accounts=summary.active_accounts,
        position_count=summary.position_count,
        accounts=summary.accounts,
        positions=summary.positions,
    )


@router.get(
    "/accounts",
    response_model=List[AccountResponse],
    summary="获取账户列表",
    description="获取所有子账户列表。",
)
async def list_accounts(
    status: Optional[AccountStatusEnum] = Query(default=None, description="按状态过滤"),
    manager: PortfolioManager = Query(default_factory=get_portfolio_manager)
) -> List[AccountResponse]:
    accounts = list(manager.accounts.values())
    if status:
        accounts = [a for a in accounts if a.status.value == status.value]
    return [_account_to_response(a) for a in accounts]


@router.post(
    "/accounts",
    response_model=AccountResponse,
    status_code=201,
    summary="创建账户",
    description="创建一个新的策略子账户。",
)
async def create_account(
    request: AccountCreateRequest,
    manager: PortfolioManager = Query(default_factory=get_portfolio_manager)
) -> AccountResponse:
    account = manager.create_account(
        strategy_name=request.strategy_name,
        initial_capital=request.initial_capital,
        account_id=request.account_id,
    )
    return _account_to_response(account)


@router.get(
    "/accounts/{account_id}",
    response_model=AccountResponse,
    summary="获取账户详情",
    description="根据账户ID获取账户详细信息。",
    responses={
        404: {"description": "账户不存在"},
    }
)
async def get_account(
    account_id: str,
    manager: PortfolioManager = Query(default_factory=get_portfolio_manager)
) -> AccountResponse:
    account = manager.get_account(account_id)
    if not account:
        raise HTTPException(
            status_code=404,
            detail=f"Account not found: {account_id}"
        )
    return _account_to_response(account)


@router.put(
    "/accounts/{account_id}/status",
    response_model=AccountResponse,
    summary="更新账户状态",
    description="更新账户状态（暂停/恢复/关闭）。",
    responses={
        404: {"description": "账户不存在"},
        400: {"description": "无效的状态转换"},
    }
)
async def update_account_status(
    account_id: str,
    request: AccountStatusUpdateRequest,
    manager: PortfolioManager = Query(default_factory=get_portfolio_manager)
) -> AccountResponse:
    account = manager.get_account(account_id)
    if not account:
        raise HTTPException(
            status_code=404,
            detail=f"Account not found: {account_id}"
        )

    if request.status == AccountStatusEnum.PAUSED:
        success = manager.pause_account(account_id)
    elif request.status == AccountStatusEnum.ACTIVE:
        success = manager.resume_account(account_id)
    elif request.status == AccountStatusEnum.CLOSED:
        success = manager.remove_account(account_id)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {request.status}"
        )

    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to update account status to {request.status}"
        )

    account = manager.get_account(account_id)
    return _account_to_response(account)


@router.delete(
    "/accounts/{account_id}",
    response_model=Dict[str, str],
    summary="删除账户",
    description="移除指定的账户。",
    responses={
        404: {"description": "账户不存在"},
    }
)
async def delete_account(
    account_id: str,
    manager: PortfolioManager = Query(default_factory=get_portfolio_manager)
) -> Dict[str, str]:
    account = manager.get_account(account_id)
    if not account:
        raise HTTPException(
            status_code=404,
            detail=f"Account not found: {account_id}"
        )

    success = manager.remove_account(account_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to remove account: {account_id}"
        )

    return {"message": f"Account {account_id} removed successfully"}


@router.get(
    "/accounts/{account_id}/positions",
    response_model=List[PositionResponse],
    summary="获取账户持仓",
    description="获取指定账户的所有持仓信息。",
    responses={
        404: {"description": "账户不存在"},
    }
)
async def get_account_positions(
    account_id: str,
    manager: PortfolioManager = Query(default_factory=get_portfolio_manager)
) -> List[PositionResponse]:
    account = manager.get_account(account_id)
    if not account:
        raise HTTPException(
            status_code=404,
            detail=f"Account not found: {account_id}"
        )
    return [_position_to_response(p) for p in account.positions.values()]


@router.get(
    "/positions",
    response_model=List[PositionResponse],
    summary="获取聚合持仓",
    description="获取所有活跃账户的聚合持仓信息。",
)
async def get_aggregated_positions(
    manager: PortfolioManager = Query(default_factory=get_portfolio_manager)
) -> List[PositionResponse]:
    positions = manager.get_aggregated_positions()
    return [_position_to_response(p) for p in positions.values()]


@router.get(
    "/pnl",
    response_model=Dict[str, PnLSnapshotResponse],
    summary="获取盈亏快照",
    description="获取所有活跃账户的盈亏快照。",
)
async def get_pnl_snapshot(
    current_date: Optional[str] = Query(default=None, description="日期 (YYYY-MM-DD)"),
    manager: PortfolioManager = Query(default_factory=get_portfolio_manager)
) -> Dict[str, PnLSnapshotResponse]:
    target_date = None
    if current_date:
        try:
            target_date = date.fromisoformat(current_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format: {current_date}. Use YYYY-MM-DD."
            )

    snapshots = manager.calculate_pnl(target_date)
    return {
        account_id: _pnl_to_response(s)
        for account_id, s in snapshots.items()
    }


@router.post(
    "/allocate",
    response_model=List[AllocationResponse],
    summary="资金分配",
    description="按照指定方法分配资金到各账户。",
    responses={
        400: {"description": "分配参数无效"},
    }
)
async def allocate_capital(
    request: AllocateRequest,
    manager: PortfolioManager = Query(default_factory=get_portfolio_manager)
) -> List[AllocationResponse]:
    try:
        method = _convert_allocation_method(request.method)
        allocations = manager.allocate_capital(
            method=method,
            weights=request.weights,
        )
        return [
            AllocationResponse(
                account_id=a.account_id,
                allocated_capital=a.allocated_capital,
                weight=a.weight,
                method=a.method.value,
            )
            for a in allocations.values()
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post(
    "/rebalance",
    response_model=List[AllocationResponse],
    summary="组合再平衡",
    description="按照指定方法对组合进行再平衡。",
)
async def rebalance(
    request: RebalanceRequest,
    manager: PortfolioManager = Query(default_factory=get_portfolio_manager)
) -> List[AllocationResponse]:
    try:
        method = _convert_allocation_method(request.method)
        allocations = manager.rebalance(method=method)
        return [
            AllocationResponse(
                account_id=a.account_id,
                allocated_capital=a.allocated_capital,
                weight=a.weight,
                method=a.method.value,
            )
            for a in allocations.values()
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )