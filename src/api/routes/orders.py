"""订单管理 API 路由

提供订单提交、查询、撤销等 REST API 端点。
"""
from datetime import datetime
from typing import List, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from execution import (
    Direction,
    OrderType,
    OrderStatus,
    TimeInForce,
    Offset,
    Exchange,
    OrderManager,
    SimGateway,
)


router = APIRouter(prefix="/orders", tags=["orders"])


class DirectionEnum(str, Enum):
    LONG = "long"
    SHORT = "short"


class OrderTypeEnum(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TimeInForceEnum(str, Enum):
    DAY = "day"
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"


class OffsetEnum(str, Enum):
    OPEN = "open"
    CLOSE = "close"
    CLOSE_TODAY = "close_today"


class ExchangeEnum(str, Enum):
    SSE = "sse"
    SZSE = "szse"
    SHFE = "shfe"
    CFFEX = "cffex"
    DCE = "dce"
    CZCE = "czce"


class OrderCreateRequest(BaseModel):
    symbol: str = Field(..., description="证券代码", min_length=1, max_length=20)
    exchange: ExchangeEnum = Field(..., description="交易所")
    direction: DirectionEnum = Field(..., description="交易方向")
    offset: OffsetEnum = Field(..., description="开平仓方向")
    order_type: OrderTypeEnum = Field(..., description="订单类型")
    quantity: int = Field(..., description="委托数量", gt=0)
    price: float = Field(default=0.0, description="委托价格", ge=0)
    time_in_force: TimeInForceEnum = Field(default=TimeInForceEnum.DAY, description="订单有效期类型")
    stop_price: float = Field(default=0.0, description="止损价格", ge=0)
    reference: str = Field(default="", description="参考信息", max_length=100)


class OrderResponse(BaseModel):
    order_id: str = Field(..., description="订单ID")
    symbol: str = Field(..., description="证券代码")
    exchange: ExchangeEnum = Field(..., description="交易所")
    direction: DirectionEnum = Field(..., description="交易方向")
    offset: OffsetEnum = Field(..., description="开平仓方向")
    order_type: OrderTypeEnum = Field(..., description="订单类型")
    quantity: int = Field(..., description="委托数量")
    price: float = Field(..., description="委托价格")
    status: OrderStatusEnum = Field(..., description="订单状态")
    time_in_force: TimeInForceEnum = Field(..., description="订单有效期类型")
    stop_price: float = Field(default=0.0, description="止损价格")
    filled_quantity: int = Field(default=0, description="已成交数量")
    filled_price: float = Field(default=0.0, description="成交价格")
    average_price: float = Field(default=0.0, description="平均成交价格")
    commission: float = Field(default=0.0, description="手续费")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")
    submitted_at: Optional[datetime] = Field(default=None, description="提交时间")
    filled_at: Optional[datetime] = Field(default=None, description="成交时间")
    cancelled_at: Optional[datetime] = Field(default=None, description="撤销时间")
    rejected_reason: str = Field(default="", description="拒绝原因")
    reference: str = Field(default="", description="参考信息")
    gateway_name: str = Field(default="", description="网关名称")


class TradeResponse(BaseModel):
    trade_id: str = Field(..., description="成交ID")
    order_id: str = Field(..., description="订单ID")
    symbol: str = Field(..., description="证券代码")
    exchange: ExchangeEnum = Field(..., description="交易所")
    direction: DirectionEnum = Field(..., description="交易方向")
    offset: OffsetEnum = Field(..., description="开平仓方向")
    price: float = Field(..., description="成交价格")
    quantity: int = Field(..., description="成交数量")
    commission: float = Field(default=0.0, description="手续费")
    timestamp: Optional[datetime] = Field(default=None, description="成交时间")
    gateway_name: str = Field(default="", description="网关名称")


class OrderCreateResponse(BaseModel):
    order_id: str = Field(..., description="订单ID")
    message: str = Field(default="Order submitted successfully", description="响应消息")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="错误详情")


_order_manager: Optional[OrderManager] = None


def get_order_manager() -> OrderManager:
    global _order_manager
    if _order_manager is None:
        gateway = SimGateway()
        gateway.connect({})
        _order_manager = OrderManager(gateway)
    return _order_manager


def _convert_direction(direction: DirectionEnum) -> Direction:
    return Direction(direction.value)


def _convert_order_type(order_type: OrderTypeEnum) -> OrderType:
    return OrderType(order_type.value)


def _convert_time_in_force(tif: TimeInForceEnum) -> TimeInForce:
    return TimeInForce(tif.value)


def _convert_offset(offset: OffsetEnum) -> Offset:
    return Offset(offset.value)


def _convert_exchange(exchange: ExchangeEnum) -> Exchange:
    return Exchange(exchange.value)


def _order_to_response(order) -> OrderResponse:
    return OrderResponse(
        order_id=order.order_id,
        symbol=order.symbol,
        exchange=ExchangeEnum(order.exchange.value),
        direction=DirectionEnum(order.direction.value),
        offset=OffsetEnum(order.offset.value),
        order_type=OrderTypeEnum(order.order_type.value),
        quantity=order.quantity,
        price=order.price,
        status=OrderStatusEnum(order.status.value),
        time_in_force=TimeInForceEnum(order.time_in_force.value),
        stop_price=order.stop_price,
        filled_quantity=order.filled_quantity,
        filled_price=order.filled_price,
        average_price=order.average_price,
        commission=order.commission,
        created_at=order.created_at,
        updated_at=order.updated_at,
        submitted_at=order.submitted_at,
        filled_at=order.filled_at,
        cancelled_at=order.cancelled_at,
        rejected_reason=order.rejected_reason,
        reference=order.reference,
        gateway_name=order.gateway_name,
    )


def _trade_to_response(trade) -> TradeResponse:
    return TradeResponse(
        trade_id=trade.trade_id,
        order_id=trade.order_id,
        symbol=trade.symbol,
        exchange=ExchangeEnum(trade.exchange.value),
        direction=DirectionEnum(trade.direction.value),
        offset=OffsetEnum(trade.offset.value),
        price=trade.price,
        quantity=trade.quantity,
        commission=trade.commission,
        timestamp=trade.timestamp,
        gateway_name=trade.gateway_name,
    )


@router.get(
    "",
    response_model=List[OrderResponse],
    summary="查询所有订单",
    description="查询所有订单列表，支持按状态过滤。",
    responses={
        200: {"description": "订单列表", "model": List[OrderResponse]},
    }
)
async def list_orders(
    status: Optional[OrderStatusEnum] = Query(
        default=None,
        description="按订单状态过滤"
    ),
    manager: OrderManager = Depends(get_order_manager)
) -> List[OrderResponse]:
    all_orders = manager._gateway.query_orders()
    if status:
        all_orders = [o for o in all_orders if o.status.value == status.value]
    return [_order_to_response(o) for o in all_orders]


@router.post(
    "",
    response_model=OrderCreateResponse,
    status_code=201,
    summary="提交新订单",
    description="创建并提交一个新的交易订单。支持市价单、限价单、止损单等多种订单类型。",
    responses={
        201: {"description": "订单提交成功", "model": OrderCreateResponse},
        400: {"description": "请求参数无效", "model": ErrorResponse},
    }
)
async def create_order(
    request: OrderCreateRequest,
    manager: OrderManager = Depends(get_order_manager)
) -> OrderCreateResponse:
    if request.order_type == OrderTypeEnum.LIMIT and request.price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Limit order must have a positive price"
        )

    if request.order_type in (OrderTypeEnum.STOP, OrderTypeEnum.STOP_LIMIT) and request.stop_price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Stop order must have a positive stop price"
        )

    manager.update_market_price(request.symbol, request.price or 10.0)

    order_id = manager.create_order(
        symbol=request.symbol,
        exchange=_convert_exchange(request.exchange),
        direction=_convert_direction(request.direction),
        offset=_convert_offset(request.offset),
        quantity=request.quantity,
        price=request.price,
        order_type=_convert_order_type(request.order_type),
        time_in_force=_convert_time_in_force(request.time_in_force),
        reference=request.reference,
    )

    if not order_id:
        raise HTTPException(
            status_code=400,
            detail="Failed to create order. Please check your parameters."
        )

    return OrderCreateResponse(order_id=order_id)


@router.get(
    "/active",
    response_model=List[OrderResponse],
    summary="查询活动订单",
    description="查询所有未完成的活动订单（状态为 PENDING、SUBMITTED 或 PARTIAL）。",
    responses={
        200: {"description": "活动订单列表", "model": List[OrderResponse]},
    }
)
async def list_active_orders(
    manager: OrderManager = Depends(get_order_manager)
) -> List[OrderResponse]:
    orders = manager.query_active_orders()
    return [_order_to_response(o) for o in orders]


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="查询订单状态",
    description="根据订单ID查询订单的详细信息和当前状态。",
    responses={
        200: {"description": "订单详情", "model": OrderResponse},
        404: {"description": "订单不存在", "model": ErrorResponse},
    }
)
async def get_order(
    order_id: str,
    manager: OrderManager = Depends(get_order_manager)
) -> OrderResponse:
    order = manager.query_order(order_id)
    if not order:
        raise HTTPException(
            status_code=404,
            detail=f"Order not found: {order_id}"
        )

    return _order_to_response(order)


@router.delete(
    "/{order_id}",
    response_model=OrderCreateResponse,
    summary="撤销订单",
    description="撤销指定的未完成订单。只能撤销状态为 PENDING、SUBMITTED 或 PARTIAL 的订单。",
    responses={
        200: {"description": "订单撤销成功", "model": OrderCreateResponse},
        404: {"description": "订单不存在", "model": ErrorResponse},
        400: {"description": "订单无法撤销", "model": ErrorResponse},
    }
)
async def cancel_order(
    order_id: str,
    manager: OrderManager = Depends(get_order_manager)
) -> OrderCreateResponse:
    order = manager.query_order(order_id)
    if not order:
        raise HTTPException(
            status_code=404,
            detail=f"Order not found: {order_id}"
        )

    success = manager.cancel_order(order_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order {order_id}. Order may already be completed or cancelled."
        )

    return OrderCreateResponse(
        order_id=order_id,
        message="Order cancelled successfully"
    )


@router.get(
    "/{order_id}/trades",
    response_model=List[TradeResponse],
    summary="查询订单成交记录",
    description="查询指定订单的所有成交记录。",
    responses={
        200: {"description": "成交记录列表", "model": List[TradeResponse]},
        404: {"description": "订单不存在", "model": ErrorResponse},
    }
)
async def get_order_trades(
    order_id: str,
    manager: OrderManager = Depends(get_order_manager)
) -> List[TradeResponse]:
    order = manager.query_order(order_id)
    if not order:
        raise HTTPException(
            status_code=404,
            detail=f"Order not found: {order_id}"
        )

    trades = manager.query_trades(order_id)
    return [_trade_to_response(t) for t in trades]


@router.get(
    "/trades/all",
    response_model=List[TradeResponse],
    summary="查询所有成交记录",
    description="查询所有成交记录列表。",
    responses={
        200: {"description": "成交记录列表", "model": List[TradeResponse]},
    }
)
async def list_trades(
    manager: OrderManager = Depends(get_order_manager)
) -> List[TradeResponse]:
    trades = manager.query_trades()
    return [_trade_to_response(t) for t in trades]