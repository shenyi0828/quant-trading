"""集成测试: 风控 + 交易执行联动

验证:
- 风控规则拦截/放行订单后，交易执行网关的行为
- PositionMonitor 预警触发与 SimGateway 下单联动
- 风控上下文与执行账户状态一致性
"""
import os
import sys
import pytest
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from risk_manager import (
    RiskContext,
    RiskResult,
    RiskAction,
    RiskChecker,
    PositionLimitRule,
    OrderLimitRule,
    DailyLossLimitRule,
    ConcentrationRule,
)
from risk_manager.monitor import PositionMonitor, Alert, AlertType
from strategy_engine.types import Order as StrategyOrder, Position, Direction, OrderType, OrderStatus
from execution import (
    Direction as ExecDirection,
    OrderType as ExecOrderType,
    OrderStatus as ExecOrderStatus,
    TimeInForce,
    Offset,
    Exchange,
    OrderRequest,
    SimGateway,
    OrderManager,
)


class TestRiskExecutionIntegration:
    """风控 + 交易执行集成测试。"""

    def _make_strategy_order(self, order_id: str, symbol: str, price: float, qty: int, direction=Direction.LONG):
        return StrategyOrder(
            order_id=order_id,
            symbol=symbol,
            direction=direction,
            order_type=OrderType.MARKET,
            price=price,
            quantity=qty,
            status=OrderStatus.PENDING,
            created_at=date.today(),
        )

    def _make_exec_request(self, symbol: str, direction=ExecDirection.LONG, qty: int = 100, price: float = 10.0):
        return OrderRequest(
            symbol=symbol,
            exchange=Exchange.SSE,
            direction=direction,
            offset=Offset.OPEN,
            order_type=ExecOrderType.MARKET,
            quantity=qty,
            price=price,
        )

    def test_risk_reject_prevents_execution(self):
        """风控拒绝的订单不应被执行网关提交。"""
        # Strict order limit: max $100
        checker = RiskChecker()
        checker.add_rule(OrderLimitRule(max_amount=100))

        ctx = RiskContext(total_capital=10000, available_cash=10000, initial_capital=10000)
        order = self._make_strategy_order("ORD_1", "000001", 10.0, 100)
        report = checker.check(order, ctx)

        # The order should be rejected
        assert report.is_rejected

        # If rejected, we should not proceed to execution
        gateway = SimGateway(initial_capital=10000)
        gateway.connect({})

        # In integration flow: rejected orders are NOT sent to gateway
        exec_order_id = None
        if report.is_accepted:
            exec_order_id = gateway.submit_order(self._make_exec_request("000001"))

        assert exec_order_id is None
        assert len(gateway.query_trades()) == 0

    def test_risk_accept_allows_execution(self):
        """风控放行的订单应能正常执行。"""
        checker = RiskChecker()
        checker.add_rule(OrderLimitRule(max_amount=50000))
        ctx = RiskContext(total_capital=100000, available_cash=100000, initial_capital=100000)
        order = self._make_strategy_order("ORD_2", "000001", 10.0, 100)
        report = checker.check(order, ctx)

        assert report.is_accepted

        gateway = SimGateway(initial_capital=100000)
        gateway.connect({})
        gateway.set_market_price("000001", 10.0)
        exec_order_id = gateway.submit_order(self._make_exec_request("000001", qty=100, price=10.0))

        assert exec_order_id is not None
        trades = gateway.query_trades(exec_order_id)
        assert len(trades) == 1

    def test_position_limit_with_existing_position(self):
        """已有持仓时，仓位限制应正确叠加计算。"""
        checker = RiskChecker()
        checker.add_rule(PositionLimitRule(max_ratio=0.3))

        ctx = RiskContext(
            total_capital=100000,
            available_cash=70000,
            initial_capital=100000,
            positions={
                "000001": Position(
                    symbol="000001",
                    direction=Direction.LONG,
                    quantity=2000,
                    avg_cost=10.0,
                    current_price=10.0,
                )
            }
        )

        # New buy order that would exceed 30% limit
        order = self._make_strategy_order("ORD_3", "000001", 10.0, 2000)
        report = checker.check(order, ctx)

        assert report.is_rejected
        assert report.rejected_by == "position_limit"

    def test_concentration_rule_blocks_overweight(self):
        """集中度规则应阻止单只股票超过上限。"""
        checker = RiskChecker()
        checker.add_rule(ConcentrationRule(max_concentration=0.4, min_positions=3))

        ctx = RiskContext(
            total_capital=100000,
            available_cash=50000,
            initial_capital=100000,
            positions={
                "000001": Position(
                    symbol="000001",
                    direction=Direction.LONG,
                    quantity=5000,
                    avg_cost=10.0,
                    current_price=10.0,
                )
            }
        )

        order = self._make_strategy_order("ORD_4", "000001", 10.0, 5000)
        report = checker.check(order, ctx)

        assert report.is_rejected
        assert report.rejected_by == "concentration_limit"

    def test_daily_loss_limit_halts_trading(self):
        """日亏损触发后所有新买单应被拦截。"""
        checker = RiskChecker()
        checker.add_rule(DailyLossLimitRule(max_loss_ratio=0.02))

        ctx = RiskContext(
            total_capital=100000,
            available_cash=100000,
            initial_capital=100000,
            daily_pnl=-3000,  # 3% loss already
        )

        order = self._make_strategy_order("ORD_5", "000001", 10.0, 100)
        report = checker.check(order, ctx)

        assert report.is_rejected
        assert report.rejected_by == "daily_loss_limit"

    def test_sell_orders_bypass_position_limit(self):
        """卖单应始终通过仓位限制（减仓不受限）。"""
        checker = RiskChecker()
        checker.add_rule(PositionLimitRule(max_ratio=0.1))

        ctx = RiskContext(
            total_capital=100000,
            available_cash=90000,
            initial_capital=100000,
            positions={
                "000001": Position(
                    symbol="000001",
                    direction=Direction.LONG,
                    quantity=1000,
                    avg_cost=10.0,
                    current_price=10.0,
                )
            }
        )

        order = self._make_strategy_order("ORD_6", "000001", 10.0, 100, direction=Direction.SHORT)
        report = checker.check(order, ctx)

        assert report.is_accepted

    def test_position_monitor_triggers_alert_on_loss(self):
        """PositionMonitor 应在持仓亏损超标时产生预警。"""
        monitor = PositionMonitor()
        monitor.set_warning_threshold(loss_ratio=0.05)

        positions = {
            "000001": Position(
                symbol="000001",
                direction=Direction.LONG,
                quantity=100,
                avg_cost=10.0,
                current_price=9.0,
            )
        }
        ctx = RiskContext(total_capital=10000, available_cash=9000, initial_capital=10000)

        alerts = monitor.monitor(positions, ctx)
        loss_alerts = [a for a in alerts if a.alert_type == AlertType.LOSS_WARNING]

        assert len(loss_alerts) == 1
        assert loss_alerts[0].symbol == "000001"

    def test_sltp_integrated_with_gateway(self):
        """止损引擎触发时应能通过网关平仓。"""
        monitor = PositionMonitor()
        sltp = monitor.get_stop_loss_engine()
        sltp.set_stop_loss("000001", stop_loss_ratio=0.1)

        positions = {
            "000001": Position(
                symbol="000001",
                direction=Direction.LONG,
                quantity=100,
                avg_cost=10.0,
                current_price=8.5,
            )
        }
        ctx = RiskContext(total_capital=10000, available_cash=9000, initial_capital=10000)

        alerts = monitor.monitor(positions, ctx)
        stop_alerts = [a for a in alerts if a.alert_type == AlertType.STOP_LOSS]
        assert len(stop_alerts) == 1

        # Execute stop-loss sell through gateway
        gateway = SimGateway(initial_capital=10000)
        gateway.connect({})
        gateway.set_market_price("000001", 8.5)

        order_id = gateway.submit_order(OrderRequest(
            symbol="000001",
            exchange=Exchange.SSE,
            direction=ExecDirection.SHORT,
            offset=Offset.CLOSE,
            order_type=ExecOrderType.MARKET,
            quantity=100,
            price=8.5,
        ))

        assert order_id is not None
        trades = gateway.query_trades(order_id)
        assert len(trades) == 1
        assert trades[0].price == 8.5

    def test_multi_rule_chain_order(self):
        """多规则链中第一个拒绝的规则应短路后续检查。"""
        checker = RiskChecker()
        checker.add_rule(OrderLimitRule(max_amount=50000))
        checker.add_rule(PositionLimitRule(max_ratio=0.3))
        checker.add_rule(DailyLossLimitRule(max_loss_ratio=0.05))

        ctx = RiskContext(
            total_capital=100000,
            available_cash=100000,
            initial_capital=100000,
            daily_pnl=-6000,
        )

        # Order value = 10 * 6000 = 60000 > 50000 -> rejected by order_limit first
        order = self._make_strategy_order("ORD_7", "000001", 10.0, 6000)
        report = checker.check(order, ctx)

        assert report.is_rejected
        assert report.rejected_by == "order_limit"

    def test_gateway_position_updates_after_fill(self):
        """网关成交后持仓应自动更新。"""
        gateway = SimGateway(initial_capital=100000, commission_rate=0.001)
        gateway.connect({})
        gateway.set_market_price("600519", 1800.0)

        order_id = gateway.submit_order(OrderRequest(
            symbol="600519",
            exchange=Exchange.SSE,
            direction=ExecDirection.LONG,
            offset=Offset.OPEN,
            order_type=ExecOrderType.MARKET,
            quantity=100,
            price=1800.0,
        ))

        positions = gateway.query_positions()
        assert len(positions) == 1
        assert positions[0].symbol == "600519"
        assert positions[0].quantity == 100
        assert positions[0].avg_cost == 1800.0

        account = gateway.query_account()
        assert account.balance < 100000  # cash deducted
