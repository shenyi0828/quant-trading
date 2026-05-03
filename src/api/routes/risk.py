"""风险管理 API 路由"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from risk_manager import (
    RiskRule,
    RiskChecker,
    RiskContext,
    RiskResult,
    RiskAction,
    PositionLimitRule,
    OrderLimitRule,
    DailyLossLimitRule,
    ConcentrationRule,
    RiskCheckReport,
    PositionMonitor,
    Alert,
    AlertType,
)
from strategy_engine.types import Direction, Position, Order, OrderType, OrderStatus


router = APIRouter(tags=["risk"])


class RiskActionEnum(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    WARN = "warn"


class DirectionEnum(str, Enum):
    LONG = "long"
    SHORT = "short"


class AlertTypeEnum(str, Enum):
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    POSITION_WARNING = "position_warning"
    LOSS_WARNING = "loss_warning"
    CONCENTRATION_WARNING = "concentration_warning"


class RuleTypeEnum(str, Enum):
    POSITION_LIMIT = "position_limit"
    ORDER_LIMIT = "order_limit"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    CONCENTRATION = "concentration"


class RuleAddRequest(BaseModel):
    rule_type: RuleTypeEnum = Field(..., description="规则类型")
    name: str = Field(..., description="规则名称", min_length=1, max_length=50)
    enabled: bool = Field(default=True, description="是否启用")
    params: Dict[str, Any] = Field(default_factory=dict, description="规则参数")


class OrderCheckRequest(BaseModel):
    symbol: str = Field(..., description="股票代码")
    direction: DirectionEnum = Field(..., description="交易方向")
    quantity: int = Field(..., description="委托数量", gt=0)
    price: float = Field(..., description="委托价格", ge=0)


class RiskContextUpdateRequest(BaseModel):
    total_capital: Optional[float] = Field(None, description="总资金", ge=0)
    available_cash: Optional[float] = Field(None, description="可用现金", ge=0)
    daily_pnl: Optional[float] = Field(None, description="当日盈亏")
    daily_trades: Optional[int] = Field(None, description="当日交易次数", ge=0)


class RuleResponse(BaseModel):
    name: str = Field(..., description="规则名称")
    rule_type: str = Field(..., description="规则类型")
    enabled: bool = Field(..., description="是否启用")
    description: str = Field(default="", description="规则描述")
    params: Dict[str, Any] = Field(default_factory=dict, description="规则参数")


class RiskResultResponse(BaseModel):
    action: RiskActionEnum = Field(..., description="检查结果动作")
    rule_name: str = Field(..., description="规则名称")
    message: str = Field(default="", description="结果消息")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")


class RiskCheckResponse(BaseModel):
    order_id: str = Field(..., description="订单ID")
    symbol: str = Field(..., description="股票代码")
    results: List[RiskResultResponse] = Field(default_factory=list, description="各规则检查结果")
    final_action: RiskActionEnum = Field(..., description="最终动作")
    rejected_by: Optional[str] = Field(default=None, description="拒绝规则名称")
    rejected_message: Optional[str] = Field(default=None, description="拒绝原因")
    is_accepted: bool = Field(..., description="是否通过检查")
    has_warnings: bool = Field(default=False, description="是否有警告")


class RiskStatusResponse(BaseModel):
    total_capital: float = Field(..., description="总资金")
    available_cash: float = Field(..., description="可用现金")
    total_position_value: float = Field(..., description="持仓总市值")
    total_value: float = Field(..., description="总资产")
    daily_pnl: float = Field(..., description="当日盈亏")
    daily_return_rate: float = Field(..., description="当日收益率")
    total_trades: int = Field(..., description="当日交易次数")
    position_count: int = Field(..., description="持仓数量")
    active_rules_count: int = Field(..., description="活跃规则数量")


class AlertResponse(BaseModel):
    alert_type: AlertTypeEnum = Field(..., description="预警类型")
    symbol: str = Field(..., description="股票代码")
    message: str = Field(..., description="预警消息")
    trigger_price: float = Field(..., description="触发价格")
    current_price: float = Field(..., description="当前价格")
    timestamp: Optional[datetime] = Field(default=None, description="时间戳")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")


class RiskContextResponse(BaseModel):
    total_capital: float = Field(..., description="总资金")
    available_cash: float = Field(..., description="可用现金")
    initial_capital: float = Field(..., description="初始资金")
    total_position_value: float = Field(..., description="持仓总市值")
    total_value: float = Field(..., description="总资产")
    total_profit: float = Field(..., description="总盈亏")
    return_rate: float = Field(..., description="收益率")
    daily_pnl: float = Field(..., description="当日盈亏")
    daily_return_rate: float = Field(..., description="当日收益率")
    daily_trades: int = Field(..., description="当日交易次数")
    positions: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="持仓信息")
    current_date: Optional[date] = Field(default=None, description="当前日期")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="错误详情")


class SuccessResponse(BaseModel):
    message: str = Field(..., description="响应消息")


_risk_checker: RiskChecker
_position_monitor: PositionMonitor
_risk_context: RiskContext


def get_risk_checker() -> RiskChecker:
    global _risk_checker
    try:
        return _risk_checker
    except NameError:
        _risk_checker = RiskChecker()
        _risk_checker.add_rule(PositionLimitRule(max_ratio=0.3))
        _risk_checker.add_rule(OrderLimitRule(max_amount=500000))
        _risk_checker.add_rule(DailyLossLimitRule(max_loss_ratio=0.02))
        _risk_checker.add_rule(ConcentrationRule(max_concentration=0.4, min_positions=3))
        return _risk_checker


def get_position_monitor() -> PositionMonitor:
    global _position_monitor
    try:
        return _position_monitor
    except NameError:
        _position_monitor = PositionMonitor()
        _position_monitor.set_warning_threshold(loss_ratio=0.05)
        _position_monitor.set_position_warning_threshold(weight=0.3)
        return _position_monitor


def get_risk_context_dep() -> RiskContext:
    global _risk_context
    try:
        return _risk_context
    except NameError:
        _risk_context = RiskContext(
            total_capital=1000000.0,
            available_cash=1000000.0,
            initial_capital=1000000.0,
            positions={},
            current_date=date.today()
        )
        return _risk_context


def _create_rule_from_request(request: RuleAddRequest) -> RiskRule:
    rule_classes = {
        RuleTypeEnum.POSITION_LIMIT: PositionLimitRule,
        RuleTypeEnum.ORDER_LIMIT: OrderLimitRule,
        RuleTypeEnum.DAILY_LOSS_LIMIT: DailyLossLimitRule,
        RuleTypeEnum.CONCENTRATION: ConcentrationRule,
    }
    if request.rule_type not in rule_classes:
        raise HTTPException(status_code=400, detail=f"Unknown rule type: {request.rule_type}")
    rule_class = rule_classes[request.rule_type]
    default_params = {
        RuleTypeEnum.POSITION_LIMIT: {"max_position_ratio": 0.1},
        RuleTypeEnum.ORDER_LIMIT: {"max_order_value": 1000000},
        RuleTypeEnum.DAILY_LOSS_LIMIT: {"max_daily_loss_ratio": 0.02},
        RuleTypeEnum.CONCENTRATION: {"max_positions": 10},
    }
    params = {**default_params[request.rule_type], **request.params}
    try:
        rule = rule_class(**params, name=request.name)
        if not request.enabled:
            rule.disable()
        return rule
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create rule: {str(e)}")


def _rule_to_response(rule: RiskRule) -> RuleResponse:
    params = {}
    if hasattr(rule, "max_position_ratio"):
        params["max_position_ratio"] = rule.max_position_ratio
    if hasattr(rule, "max_order_value"):
        params["max_order_value"] = rule.max_order_value
    if hasattr(rule, "max_daily_loss_ratio"):
        params["max_daily_loss_ratio"] = rule.max_daily_loss_ratio
    if hasattr(rule, "max_positions"):
        params["max_positions"] = rule.max_positions
    return RuleResponse(
        name=rule.name,
        rule_type=rule.__class__.__name__,
        enabled=rule.enabled,
        description=rule.description if hasattr(rule, "description") else "",
        params=params
    )


def _result_to_response(result: RiskResult) -> RiskResultResponse:
    return RiskResultResponse(
        action=RiskActionEnum(result.action.value),
        rule_name=result.rule_name,
        message=result.message,
        details=result.details
    )


def _report_to_response(report: RiskCheckReport) -> RiskCheckResponse:
    return RiskCheckResponse(
        order_id=report.order_id,
        symbol=report.symbol,
        results=[_result_to_response(r) for r in report.results],
        final_action=RiskActionEnum(report.final_action.value),
        rejected_by=report.rejected_by,
        rejected_message=report.rejected_message,
        is_accepted=report.is_accepted,
        has_warnings=report.has_warnings
    )


def _alert_to_response(alert: Alert) -> AlertResponse:
    return AlertResponse(
        alert_type=AlertTypeEnum(alert.alert_type.value),
        symbol=alert.symbol,
        message=alert.message,
        trigger_price=alert.trigger_price,
        current_price=alert.current_price,
        timestamp=alert.timestamp,
        details=alert.details
    )


def _create_dry_run_order(request: OrderCheckRequest) -> Order:
    return Order(
        order_id="dry_run_" + datetime.now().strftime("%Y%m%d%H%M%S"),
        symbol=request.symbol,
        direction=Direction(request.direction.value),
        order_type=OrderType.MARKET,
        price=request.price,
        quantity=request.quantity,
        status=OrderStatus.PENDING,
        created_at=date.today()
    )


@router.get("/risk/rules", response_model=List[RuleResponse], summary="获取所有风险规则")
async def list_rules(checker: RiskChecker = Depends(get_risk_checker)) -> List[RuleResponse]:
    rules = checker.get_all_rules()
    return [_rule_to_response(r) for r in rules]


@router.post("/risk/rules", response_model=RuleResponse, status_code=201, summary="添加风险规则")
async def add_rule(request: RuleAddRequest, checker: RiskChecker = Depends(get_risk_checker)) -> RuleResponse:
    existing = checker.get_rule(request.name)
    if existing:
        raise HTTPException(status_code=400, detail=f"Rule with name '{request.name}' already exists")
    rule = _create_rule_from_request(request)
    checker.add_rule(rule)
    return _rule_to_response(rule)


@router.get("/risk/rules/{rule_name}", response_model=RuleResponse, summary="获取规则详情")
async def get_rule(rule_name: str, checker: RiskChecker = Depends(get_risk_checker)) -> RuleResponse:
    rule = checker.get_rule(rule_name)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule not found: {rule_name}")
    return _rule_to_response(rule)


@router.put("/risk/rules/{rule_name}/enable", response_model=SuccessResponse, summary="启用规则")
async def enable_rule(rule_name: str, checker: RiskChecker = Depends(get_risk_checker)) -> SuccessResponse:
    success = checker.enable_rule(rule_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Rule not found: {rule_name}")
    return SuccessResponse(message=f"Rule '{rule_name}' enabled successfully")


@router.put("/risk/rules/{rule_name}/disable", response_model=SuccessResponse, summary="禁用规则")
async def disable_rule(rule_name: str, checker: RiskChecker = Depends(get_risk_checker)) -> SuccessResponse:
    success = checker.disable_rule(rule_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Rule not found: {rule_name}")
    return SuccessResponse(message=f"Rule '{rule_name}' disabled successfully")


@router.delete("/risk/rules/{rule_name}", response_model=SuccessResponse, summary="删除规则")
async def remove_rule(rule_name: str, checker: RiskChecker = Depends(get_risk_checker)) -> SuccessResponse:
    success = checker.remove_rule(rule_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Rule not found: {rule_name}")
    return SuccessResponse(message=f"Rule '{rule_name}' removed successfully")


@router.post("/risk/check", response_model=RiskCheckResponse, summary="订单风险检查(dry-run)")
async def check_order(
    request: OrderCheckRequest,
    checker: RiskChecker = Depends(get_risk_checker),
    context: RiskContext = Depends(get_risk_context_dep)
) -> RiskCheckResponse:
    order = _create_dry_run_order(request)
    report = checker.check(order, context)
    return _report_to_response(report)


@router.get("/risk/status", response_model=RiskStatusResponse, summary="获取风险状态摘要")
async def get_risk_status(
    checker: RiskChecker = Depends(get_risk_checker),
    context: RiskContext = Depends(get_risk_context_dep)
) -> RiskStatusResponse:
    rules = checker.get_all_rules()
    enabled_rules = [r for r in rules if r.enabled]
    return RiskStatusResponse(
        total_capital=context.total_capital,
        available_cash=context.available_cash,
        total_position_value=context.total_position_value,
        total_value=context.total_value,
        daily_pnl=context.daily_pnl,
        daily_return_rate=context.daily_return_rate,
        total_trades=context.daily_trades,
        position_count=len([p for p in context.positions.values() if p.quantity > 0]),
        active_rules_count=len(rules)
    )


@router.get("/risk/alerts", response_model=List[AlertResponse], summary="获取预警列表")
async def list_alerts(
    limit: int = Query(default=20, ge=1, le=100),
    alert_type: Optional[AlertTypeEnum] = Query(default=None),
    monitor: PositionMonitor = Depends(get_position_monitor),
    context: RiskContext = Depends(get_risk_context_dep)
) -> List[AlertResponse]:
    alerts = monitor.monitor(
        positions=context.positions,
        context=context,
        current_date=context.current_date
    )
    if alert_type:
        alerts = [a for a in alerts if a.alert_type.value == alert_type.value]
    alerts = alerts[:limit]
    return [_alert_to_response(a) for a in alerts]


@router.get("/risk/context", response_model=RiskContextResponse, summary="获取风险上下文")
async def read_risk_context(context: RiskContext = Depends(get_risk_context_dep)) -> RiskContextResponse:
    positions_dict = {}
    for symbol, pos in context.positions.items():
        positions_dict[symbol] = {
            "quantity": pos.quantity,
            "avg_cost": pos.avg_cost,
            "current_price": pos.current_price,
            "market_value": pos.market_value,
            "profit": pos.profit,
        }
    return RiskContextResponse(
        total_capital=context.total_capital,
        available_cash=context.available_cash,
        initial_capital=context.initial_capital,
        total_position_value=context.total_position_value,
        total_value=context.total_value,
        total_profit=context.total_profit,
        return_rate=context.return_rate,
        daily_pnl=context.daily_pnl,
        daily_return_rate=context.daily_return_rate,
        daily_trades=context.daily_trades,
        positions=positions_dict,
        current_date=context.current_date
    )


@router.put("/risk/context", response_model=RiskContextResponse, summary="更新风险上下文")
async def update_risk_context(
    request: RiskContextUpdateRequest,
    context: RiskContext = Depends(get_risk_context_dep)
) -> RiskContextResponse:
    if request.total_capital is not None:
        context.total_capital = request.total_capital
    if request.available_cash is not None:
        context.available_cash = request.available_cash
    if request.daily_pnl is not None:
        context.daily_pnl = request.daily_pnl
    if request.daily_trades is not None:
        context.daily_trades = request.daily_trades
    positions_dict = {}
    for symbol, pos in context.positions.items():
        positions_dict[symbol] = {
            "quantity": pos.quantity,
            "avg_cost": pos.avg_cost,
            "current_price": pos.current_price,
            "market_value": pos.market_value,
            "profit": pos.profit,
        }
    return RiskContextResponse(
        total_capital=context.total_capital,
        available_cash=context.available_cash,
        initial_capital=context.initial_capital,
        total_position_value=context.total_position_value,
        total_value=context.total_value,
        total_profit=context.total_profit,
        return_rate=context.return_rate,
        daily_pnl=context.daily_pnl,
        daily_return_rate=context.daily_return_rate,
        daily_trades=context.daily_trades,
        positions=positions_dict,
        current_date=context.current_date
    )