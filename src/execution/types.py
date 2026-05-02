"""交易执行模块类型定义

参考 VeighNa 和 WonderTrader 的设计模式，定义执行模块所需的枚举类型。
"""
from enum import Enum


class Direction(Enum):
    """交易方向"""
    LONG = "long"      # 买入/做多
    SHORT = "short"    # 卖出/做空


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"    # 市价单
    LIMIT = "limit"      # 限价单
    STOP = "stop"        # 止损单
    STOP_LIMIT = "stop_limit"  # 止损限价单


class OrderStatus(Enum):
    """订单状态
    
    状态流转: PENDING → SUBMITTED → (PARTIAL/FILLED) → (CANCELLED/REJECTED)
    """
    PENDING = "pending"        # 待提交（本地创建，未发送到网关）
    SUBMITTED = "submitted"    # 已提交（已发送到网关）
    PARTIAL = "partial"        # 部分成交
    FILLED = "filled"          # 完全成交
    CANCELLED = "cancelled"    # 已撤销
    REJECTED = "rejected"      # 已拒绝（被网关拒绝）
    EXPIRED = "expired"        # 已过期


class TimeInForce(Enum):
    """订单有效期类型"""
    DAY = "day"            # 当日有效
    GTC = "gtc"            # Good Till Cancel，撤销前有效
    IOC = "ioc"            # Immediate Or Cancel，立即成交或撤销
    FOK = "fok"            # Fill Or Kill，全部成交或撤销


class Offset(Enum):
    """开平仓方向"""
    OPEN = "open"      # 开仓
    CLOSE = "close"    # 平仓
    CLOSE_TODAY = "close_today"  # 平今仓（期货）


class Exchange(Enum):
    """交易所"""
    SSE = "sse"        # 上海证券交易所
    SZSE = "szse"      # 深圳证券交易所
    SHFE = "shfe"      # 上海期货交易所
    CFFEX = "cffex"    # 中国金融期货交易所
    DCE = "dce"        # 大连商品交易所
    CZCE = "czce"      # 郑州商品交易所


class ProductType(Enum):
    """产品类型"""
    STOCK = "stock"       # 股票
    FUTURES = "futures"   # 期货
    OPTION = "option"     # 期权
    FUND = "fund"         # 基金
    BOND = "bond"         # 债券