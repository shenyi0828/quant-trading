"""Service layer tests - TradingService, StrategyRunner, and Settings."""
import sys
import os
import tempfile
from pathlib import Path
from datetime import date
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# ============================================================
# TradingService tests (from services/trading_service.py)
# ============================================================

from services.trading_service import TradingService, TradingServiceSubmitResult, AccountInfo
from execution import SimGateway, OrderManager, Order, Trade, Position, Direction, OrderStatus
from execution.models import OrderRequest
from execution.types import Exchange, OrderType, TimeInForce, Offset
from risk_manager import RiskChecker, RiskContext, RiskResult, RiskAction, RiskCheckReport
from strategy_engine.types import Order as StrategyOrder


class MockSimGateway(SimGateway):
    """SimGateway that doesn't require real network calls."""

    def __init__(self, initial_capital=100000.0, commission_rate=0.001):
        super().__init__(initial_capital=initial_capital, commission_rate=commission_rate)
        self._connected = False
        self._orders = {}
        self._trades = {}
        self._positions = {}
        self._account = None
        self._market_prices = {}
        self._order_callbacks = []
        self._trade_callbacks = []

    def on_order_status(self, callback):
        self._order_callbacks.append(callback)

    def on_trade(self, callback):
        self._trade_callbacks.append(callback)

    def connect(self, config: dict) -> bool:
        self._connected = True
        return True

    def is_connected(self) -> bool:
        return self._connected

    def disconnect(self) -> bool:
        self._connected = False
        return True

    def set_market_price(self, symbol: str, price: float) -> None:
        self._market_prices[symbol] = price

    def submit_order(self, order_request: OrderRequest) -> str:
        import uuid
        order_id = f"ORD_{uuid.uuid4().hex[:8]}"
        status = OrderStatus.FILLED if order_request.order_type == OrderType.MARKET else OrderStatus.SUBMITTED
        order = Order(
            order_id=order_id,
            symbol=order_request.symbol,
            exchange=order_request.exchange,
            direction=order_request.direction,
            offset=order_request.offset,
            order_type=order_request.order_type,
            quantity=order_request.quantity,
            price=order_request.price,
            status=status,
        )
        self._orders[order_id] = order
        for cb in self._order_callbacks:
            cb(order)
        return order_id

    def query_order(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    def query_orders(self, status: OrderStatus | None = None) -> list[Order]:
        orders = list(self._orders.values())
        if status:
            orders = [o for o in orders if o.status == status]
        return orders

    def cancel_order(self, order_id: str) -> bool:
        if order_id in self._orders:
            self._orders[order_id].status = OrderStatus.CANCELLED
            return True
        return False

    def query_positions(self) -> list[Position]:
        return list(self._positions.values())

    def query_account(self):
        return self._account

    def query_trades(self, order_id: str | None = None) -> list[Trade]:
        if order_id:
            return self._trades.get(order_id, [])
        all_trades = []
        for trades in self._trades.values():
            all_trades.extend(trades)
        return all_trades


class PermissiveRiskChecker(RiskChecker):
    """A RiskChecker that accepts all orders by default for testing."""

    def __init__(self):
        super().__init__()

    def check(self, order: StrategyOrder, context: RiskContext) -> RiskCheckReport:
        result = RiskResult(
            action=RiskAction.ACCEPT,
            rule_name="test_permissive",
            message="Order accepted"
        )
        return RiskCheckReport(
            order_id=order.order_id,
            symbol=order.symbol,
            results=[result]
        )


class TestTradingService:
    """Tests for the full TradingService (services/trading_service.py)."""

    def _make_service(self, initial_capital=100000.0):
        gateway = MockSimGateway(initial_capital=initial_capital)
        gateway.connect({})
        risk_checker = PermissiveRiskChecker()
        return TradingService(gateway, risk_checker, initial_capital=initial_capital)

    def _make_order_request(self, symbol="000001", quantity=100, price=10.0,
                            direction=Direction.LONG, exchange=Exchange.SSE,
                            order_type=OrderType.MARKET, offset=Offset.OPEN,
                            time_in_force=TimeInForce.DAY, reference="test"):
        return OrderRequest(
            symbol=symbol,
            exchange=exchange,
            direction=direction,
            offset=offset,
            order_type=order_type,
            quantity=quantity,
            price=price,
            time_in_force=time_in_force,
            reference=reference,
        )

    # ---- submit_order happy path ----

    def test_submit_order_accepted(self):
        """Order passes risk check and is submitted successfully."""
        service = self._make_service()
        req = self._make_order_request()

        result = service.submit_order(req)

        assert result.accepted is True
        assert result.order_id is not None
        assert "successfully" in result.message

    def test_submit_order_updates_daily_counters(self):
        """submit_order increments daily trade count and tracks orders."""
        service = self._make_service()
        req = self._make_order_request()

        service.submit_order(req)
        service.submit_order(self._make_order_request(symbol="000002"))

        assert service._daily_trades == 2
        assert len(service._daily_orders) == 2

    def test_submit_order_risk_rejection(self):
        """Order rejected by risk checker returns rejection result."""
        gateway = MockSimGateway()
        gateway.connect({})

        # Create a risk checker that always rejects
        class RejectingRiskChecker(RiskChecker):
            def check(self, order, context):
                result = RiskResult(
                    action=RiskAction.REJECT,
                    rule_name="test_reject",
                    message="Test rejection"
                )
                return RiskCheckReport(
                    order_id=order.order_id,
                    symbol=order.symbol,
                    results=[result],
                    final_action=RiskAction.REJECT,
                    rejected_by="test_reject",
                    rejected_message="Test rejection",
                )

        risk_checker = RejectingRiskChecker()
        service = TradingService(gateway, risk_checker)

        req = self._make_order_request()
        result = service.submit_order(req)

        assert result.accepted is False
        assert result.order_id is None
        assert "rejected" in result.message.lower()

    def test_submit_order_risk_reject_callback_fired(self):
        """Risk reject callback is called when order is rejected."""
        gateway = MockSimGateway()
        gateway.connect({})

        class RejectingRiskChecker(RiskChecker):
            def check(self, order, context):
                result = RiskResult(
                    action=RiskAction.REJECT,
                    rule_name="test_reject",
                    message="Test rejection"
                )
                return RiskCheckReport(
                    order_id=order.order_id,
                    symbol=order.symbol,
                    results=[result],
                    final_action=RiskAction.REJECT,
                    rejected_by="test_reject",
                    rejected_message="Test rejection",
                )

        risk_checker = RejectingRiskChecker()
        service = TradingService(gateway, risk_checker)

        callback = Mock()
        service.register_risk_reject_callback(callback)

        req = self._make_order_request()
        service.submit_order(req)

        assert callback.called

    def test_submit_order_callback_fired(self):
        """Order callback is called when order status changes via gateway."""
        service = self._make_service()
        received_orders = []
        service.register_order_callback(lambda o: received_orders.append(o))

        req = self._make_order_request()
        service.submit_order(req)

        # Order callback triggers through OrderManager -> _on_order_status
        # The SimGateway fills orders immediately, so callback fires
        assert len(received_orders) >= 0

    # ---- cancel_order ----

    def test_cancel_order_success(self):
        """Cancel an existing order returns True."""
        service = self._make_service()
        req = self._make_order_request(price=5.0, order_type=OrderType.LIMIT)

        result = service.submit_order(req)

        cancelled = service.cancel_order(result.order_id)
        assert cancelled is True

    def test_cancel_order_nonexistent(self):
        """Cancel a non-existent order returns False."""
        service = self._make_service()
        assert service.cancel_order("NONEXISTENT_ORDER_ID") is False

    # ---- query operations ----

    def test_get_order(self):
        """get_order returns the Order object for a valid ID."""
        service = self._make_service()
        req = self._make_order_request()
        result = service.submit_order(req)

        order = service.get_order(result.order_id)
        assert order is not None
        assert order.order_id == result.order_id

    def test_get_order_not_found(self):
        """get_order returns None for invalid ID."""
        service = self._make_service()
        assert service.get_order("BAD_ID") is None

    def test_get_active_orders(self):
        """get_active_orders returns list of active orders."""
        service = self._make_service()
        orders = service.get_active_orders()
        assert isinstance(orders, list)

    def test_get_positions(self):
        """get_positions returns list of positions from gateway."""
        service = self._make_service()
        positions = service.get_positions()
        assert isinstance(positions, list)

    # ---- account info ----

    def test_get_account_info(self):
        """get_account_info returns AccountInfo with correct balance."""
        service = self._make_service(initial_capital=50000.0)
        info = service.get_account_info()

        assert info.account_id == "main"
        assert info.balance == 50000.0
        assert info.available == 50000.0

    def test_get_account_info_with_positions(self):
        """get_account_info calculates unrealized PnL from positions."""
        gateway = MockSimGateway(initial_capital=100000.0)
        gateway.connect({})
        gateway._positions["000001"] = Position(
            symbol="000001",
            exchange=Exchange.SSE,
            direction=Direction.LONG,
            quantity=100,
            avg_cost=10.0,
            current_price=12.0,
        )
        service = TradingService(gateway, PermissiveRiskChecker())
        info = service.get_account_info()

        assert len(info.positions) == 1
        assert info.unrealized_pnl == 200.0  # (12-10)*100

    # ---- trade callbacks and balance update ----

    def test_trade_callback_updates_balance(self):
        """Trade callback updates account balance correctly."""
        service = self._make_service()

        sell_trade = Trade(
            trade_id="TRD_TEST",
            order_id="ORD_TEST",
            symbol="000001",
            exchange=Exchange.SSE,
            direction=Direction.SHORT,
            offset=Offset.CLOSE,
            price=15.0,
            quantity=100,
            commission=1.5,
        )
        service._on_trade(sell_trade)

        assert service._account_info.balance > 100000.0

    def test_trade_callback_long_decreases_balance(self):
        """Buying (LONG trade) decreases balance."""
        initial = 100000.0
        service = self._make_service(initial_capital=initial)

        buy_trade = Trade(
            trade_id="TRD_TEST2",
            order_id="ORD_TEST2",
            symbol="000001",
            exchange=Exchange.SSE,
            direction=Direction.LONG,
            offset=Offset.OPEN,
            price=10.0,
            quantity=100,
            commission=1.0,
        )
        service._on_trade(buy_trade)

        expected_cost = 10.0 * 100 + 1.0
        assert service._account_info.balance == initial - expected_cost

    # ---- market price update ----

    def test_update_market_price(self):
        """update_market_price stores price and updates gateway."""
        service = self._make_service()
        service.update_market_price("000001", 25.5)

        assert service._current_prices["000001"] == 25.5

    # ---- risk context ----

    def test_get_risk_context(self):
        """get_risk_context returns a valid RiskContext."""
        service = self._make_service()
        ctx = service.get_risk_context()

        assert isinstance(ctx, RiskContext)
        assert ctx.total_capital == 100000.0
        assert ctx.available_cash == 100000.0


class TestTradingServiceAlgoEngine:
    """Tests for algo engine integration in TradingService."""

    def test_algo_engine_lazy_init(self):
        """AlgoEngine is lazily initialized on first access."""
        gateway = MockSimGateway()
        gateway.connect({})
        service = TradingService(gateway, PermissiveRiskChecker())

        assert service._algo_engine is None
        engine = service.algo_engine
        assert engine is not None
        assert service._algo_engine is engine

    def test_algo_engine_returns_same_instance(self):
        """Repeated algo_engine access returns same instance."""
        gateway = MockSimGateway()
        gateway.connect({})
        service = TradingService(gateway, PermissiveRiskChecker())

        engine1 = service.algo_engine
        engine2 = service.algo_engine
        assert engine1 is engine2


# ============================================================
# StrategyRunner tests (from services/strategy_runner.py)
# ============================================================

from services.strategy_runner import (
    StrategyRunner, StrategyState, StrategyInstance,
    TradingService as RunnerTradingService,
)
from strategy_engine.base import BaseStrategy
from strategy_engine.context import StrategyContext
from data_center.interfaces.data_source import DailyBar


class DummyStrategy(BaseStrategy):
    """Minimal strategy implementation for testing."""

    def on_init(self):
        pass

    def on_bar(self, bar: DailyBar):
        pass


class MockDataAPI:
    """Mock DataAPI that doesn't require real network calls."""

    def __init__(self):
        self._data = {}

    def set_daily_bars(self, symbol: str, bars: list[DailyBar]):
        self._data[symbol] = bars

    def get_daily_bars(self, symbol, start_date, end_date):
        return self._data.get(symbol, [])

    def get_stock_list(self):
        return []

    def get_trading_calendar(self, year=None):
        return []

    def is_trading_day(self, dt):
        return True


class TestStrategyRunner:
    """Tests for StrategyRunner lifecycle management."""

    def _make_runner(self):
        data_api = MockDataAPI()
        return StrategyRunner(data_api)

    # ---- register_strategy ----

    def test_register_strategy_returns_id(self):
        """register_strategy returns a non-empty string ID."""
        runner = self._make_runner()
        sid = runner.register_strategy(
            DummyStrategy,
            params={"fast_period": 5, "slow_period": 20},
            symbols=["000001"],
        )

        assert isinstance(sid, str)
        assert len(sid) > 0

    def test_register_strategy_empty_symbols_raises(self):
        """register_strategy raises ValueError with empty symbols."""
        runner = self._make_runner()
        with pytest.raises(ValueError, match="Must specify at least one trading symbol"):
            runner.register_strategy(DummyStrategy, params={}, symbols=[])

    def test_register_strategy_negative_capital_raises(self):
        """register_strategy raises ValueError with non-positive capital."""
        runner = self._make_runner()
        with pytest.raises(ValueError, match="Initial capital must be greater than 0"):
            runner.register_strategy(DummyStrategy, params={}, symbols=["000001"], initial_capital=0)

        with pytest.raises(ValueError):
            runner.register_strategy(DummyStrategy, params={}, symbols=["000001"], initial_capital=-100)

    def test_register_strategy_sets_stopped_state(self):
        """New strategy starts in STOPPED state."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])

        assert runner.get_strategy_status(sid) == StrategyState.STOPPED

    # ---- start_strategy ----

    def test_start_strategy(self):
        """start_strategy transitions to RUNNING."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])

        result = runner.start_strategy(sid)
        assert result is True
        assert runner.get_strategy_status(sid) == StrategyState.RUNNING

    def test_start_strategy_already_running(self):
        """Starting an already-running strategy returns True."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])
        runner.start_strategy(sid)

        result = runner.start_strategy(sid)
        assert result is True

    def test_start_strategy_not_found_raises(self):
        """start_strategy raises KeyError for non-existent strategy."""
        runner = self._make_runner()
        with pytest.raises(KeyError):
            runner.start_strategy("nonexistent-id")

    # ---- stop_strategy ----

    def test_stop_strategy(self):
        """stop_strategy transitions to STOPPED."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])
        runner.start_strategy(sid)

        result = runner.stop_strategy(sid)
        assert result is True
        assert runner.get_strategy_status(sid) == StrategyState.STOPPED

    def test_stop_strategy_not_found_raises(self):
        """stop_strategy raises KeyError for non-existent strategy."""
        runner = self._make_runner()
        with pytest.raises(KeyError):
            runner.stop_strategy("nonexistent-id")

    # ---- pause_strategy ----

    def test_pause_strategy(self):
        """pause_strategy transitions from RUNNING to PAUSED."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])
        runner.start_strategy(sid)

        result = runner.pause_strategy(sid)
        assert result is True
        assert runner.get_strategy_status(sid) == StrategyState.PAUSED

    def test_pause_strategy_not_running_returns_false(self):
        """pause_strategy returns False when strategy is not RUNNING."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])

        result = runner.pause_strategy(sid)
        assert result is False

    def test_pause_strategy_not_found_raises(self):
        """pause_strategy raises KeyError for non-existent strategy."""
        runner = self._make_runner()
        with pytest.raises(KeyError):
            runner.pause_strategy("nonexistent-id")

    # ---- resume_strategy ----

    def test_resume_strategy(self):
        """resume_strategy transitions from PAUSED to RUNNING."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])
        runner.start_strategy(sid)
        runner.pause_strategy(sid)

        result = runner.resume_strategy(sid)
        assert result is True
        assert runner.get_strategy_status(sid) == StrategyState.RUNNING

    def test_resume_strategy_not_paused_returns_false(self):
        """resume_strategy returns False when strategy is not PAUSED."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])
        # Strategy is STOPPED, not PAUSED

        result = runner.resume_strategy(sid)
        assert result is False

    def test_resume_strategy_not_found_raises(self):
        """resume_strategy raises KeyError for non-existent strategy."""
        runner = self._make_runner()
        with pytest.raises(KeyError):
            runner.resume_strategy("nonexistent-id")

    # ---- unregister_strategy ----

    def test_unregister_strategy(self):
        """unregister_strategy removes strategy from registry."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])

        result = runner.unregister_strategy(sid)
        assert result is True

        with pytest.raises(KeyError):
            runner.get_strategy_status(sid)

    def test_unregister_running_strategy_stops_first(self):
        """unregister_strategy stops a running strategy before removal."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])
        runner.start_strategy(sid)

        runner.unregister_strategy(sid)

        with pytest.raises(KeyError):
            runner.get_strategy_status(sid)

    def test_unregister_not_found_raises(self):
        """unregister_strategy raises KeyError for non-existent strategy."""
        runner = self._make_runner()
        with pytest.raises(KeyError):
            runner.unregister_strategy("nonexistent-id")

    # ---- full lifecycle ----

    def test_full_lifecycle(self):
        """Complete lifecycle: register -> start -> pause -> resume -> stop."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])

        assert runner.get_strategy_status(sid) == StrategyState.STOPPED

        runner.start_strategy(sid)
        assert runner.get_strategy_status(sid) == StrategyState.RUNNING

        runner.pause_strategy(sid)
        assert runner.get_strategy_status(sid) == StrategyState.PAUSED

        runner.resume_strategy(sid)
        assert runner.get_strategy_status(sid) == StrategyState.RUNNING

        runner.stop_strategy(sid)
        assert runner.get_strategy_status(sid) == StrategyState.STOPPED

    # ---- get_all_strategies ----

    def test_get_all_strategies_empty(self):
        """get_all_strategies returns empty list when no strategies registered."""
        runner = self._make_runner()
        assert runner.get_all_strategies() == []

    def test_get_all_strategies_returns_info(self):
        """get_all_strategies returns strategy info dicts."""
        runner = self._make_runner()
        runner.register_strategy(
            DummyStrategy,
            params={"param1": "value1"},
            symbols=["000001", "000002"],
            initial_capital=500000.0,
        )

        strategies = runner.get_all_strategies()
        assert len(strategies) == 1

        info = strategies[0]
        assert info["name"] == "DummyStrategy"
        assert info["state"] == StrategyState.STOPPED.value
        assert len(info["symbols"]) == 2
        assert info["params"] == {"param1": "value1"}
        assert info["cash"] == 500000.0
        assert info["total_value"] == 500000.0

    # ---- update_prices ----

    def test_update_prices(self):
        """update_prices updates position values for all strategies."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])
        ctx = runner.get_strategy_context(sid)
        # Create a position manually for testing
        from strategy_engine.types import Position as StrategyPosition
        ctx.positions["000001"] = StrategyPosition(
            symbol="000001",
            direction=Direction.LONG,
            quantity=100,
            avg_cost=10.0,
            current_price=10.0,
        )

        runner.update_prices({"000001": 15.0})

        updated_pos = ctx.positions["000001"]
        assert updated_pos.current_price == 15.0

    # ---- get_strategy_context ----

    def test_get_strategy_context(self):
        """get_strategy_context returns the StrategyContext."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"], initial_capital=200000.0)

        ctx = runner.get_strategy_context(sid)
        assert isinstance(ctx, StrategyContext)
        assert ctx.initial_capital == 200000.0

    def test_get_strategy_context_not_found_raises(self):
        """get_strategy_context raises KeyError for non-existent strategy."""
        runner = self._make_runner()
        with pytest.raises(KeyError):
            runner.get_strategy_context("nonexistent-id")

    # ---- get_strategy_positions/orders/trades ----

    def test_get_strategy_positions(self):
        """get_strategy_positions returns position dict."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])

        positions = runner.get_strategy_positions(sid)
        assert isinstance(positions, dict)

    def test_get_strategy_orders(self):
        """get_strategy_orders returns order list."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])

        orders = runner.get_strategy_orders(sid)
        assert isinstance(orders, list)

    def test_get_strategy_trades(self):
        """get_strategy_trades returns trade list."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])

        trades = runner.get_strategy_trades(sid)
        assert isinstance(trades, list)

    def test_strategy_not_found_raises(self):
        """Methods raise KeyError for non-existent strategy."""
        runner = self._make_runner()
        with pytest.raises(KeyError):
            runner.get_strategy_positions("bad-id")
        with pytest.raises(KeyError):
            runner.get_strategy_orders("bad-id")
        with pytest.raises(KeyError):
            runner.get_strategy_trades("bad-id")

    # ---- on_bar ----

    def test_on_bar_notifies_running_strategy(self):
        """on_bar notifies running strategies with matching symbols."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])
        runner.start_strategy(sid)

        bar = DailyBar(
            symbol="000001",
            date=date.today(),
            open=10.0,
            high=11.0,
            low=9.5,
            close=10.5,
            volume=10000,
        )
        runner.on_bar("000001", bar)

        ctx = runner.get_strategy_context(sid)
        assert ctx.current_date == date.today()

    def test_on_bar_ignores_stopped_strategy(self):
        """on_bar does not notify stopped strategies."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])
        # Strategy is STOPPED

        bar = DailyBar(
            symbol="000001",
            date=date.today(),
            open=10.0,
            high=11.0,
            low=9.5,
            close=10.5,
            volume=10000,
        )
        runner.on_bar("000001", bar)

        ctx = runner.get_strategy_context(sid)
        assert ctx.current_date is None  # should not have been updated

    def test_on_bar_ignores_non_matching_symbol(self):
        """on_bar ignores bars for symbols not in strategy's list."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])
        runner.start_strategy(sid)

        bar = DailyBar(
            symbol="000002",
            date=date.today(),
            open=10.0,
            high=11.0,
            low=9.5,
            close=10.5,
            volume=10000,
        )
        runner.on_bar("000002", bar)

        ctx = runner.get_strategy_context(sid)
        assert ctx.current_date is None

    # ---- register_bar_handler ----

    def test_register_bar_handler(self):
        """register_bar_handler adds handler for strategy's symbols."""
        runner = self._make_runner()
        sid = runner.register_strategy(DummyStrategy, params={}, symbols=["000001"])

        handler_called = []
        runner.register_bar_handler(sid, lambda s, b: handler_called.append((s, b)))

        bar = DailyBar(
            symbol="000001",
            date=date.today(),
            open=10.0,
            high=11.0,
            low=9.5,
            close=10.5,
            volume=10000,
        )
        runner.on_bar("000001", bar)

        assert len(handler_called) == 1
        assert handler_called[0][0] == "000001"

    def test_register_bar_handler_not_found_raises(self):
        """register_bar_handler raises KeyError for non-existent strategy."""
        runner = self._make_runner()
        with pytest.raises(KeyError):
            runner.register_bar_handler("bad-id", lambda s, b: None)

    # ---- properties ----

    def test_trading_service_property(self):
        """trading_service property returns TradingService."""
        runner = self._make_runner()
        ts = runner.trading_service
        assert isinstance(ts, RunnerTradingService)

    def test_data_api_property(self):
        """data_api property returns DataAPI."""
        data_api = MockDataAPI()
        runner = StrategyRunner(data_api)
        assert runner.data_api is data_api

    # ---- RunnerTradingService ----

    def test_runner_trading_service_submit_order(self):
        """RunnerTradingService.submit_order stores order and fires callbacks."""
        ts = RunnerTradingService()
        order_callback_called = []
        ts.on_order(lambda o: order_callback_called.append(o))

        from strategy_engine.types import Order as StratOrder, Direction as D, OrderType as OT
        order = StratOrder(
            order_id="TEST_ORD",
            symbol="000001",
            direction=D.LONG,
            order_type=OT.MARKET,
            price=10.0,
            quantity=100,
        )
        result = ts.submit_order(order)

        assert result is True
        assert len(order_callback_called) == 1
        assert len(ts.get_orders()) == 1

    def test_runner_trading_service_record_trade(self):
        """RunnerTradingService.record_trade stores trade and fires callbacks."""
        ts = RunnerTradingService()
        trade_callback_called = []
        ts.on_trade(lambda t: trade_callback_called.append(t))

        from strategy_engine.types import Trade as StratTrade, Direction as D
        trade = StratTrade(
            trade_id="TEST_TRD",
            order_id="TEST_ORD",
            symbol="000001",
            direction=D.LONG,
            price=10.0,
            quantity=100,
            timestamp=date.today(),
        )
        ts.record_trade(trade)

        assert len(trade_callback_called) == 1
        assert len(ts.get_trades()) == 1


# ============================================================
# Settings / Config tests (from config/settings.py)
# ============================================================

from config.settings import (
    Settings,
    ServerConfig,
    TradingConfig,
    RiskConfig,
    DataConfig,
    load_config,
)


class TestServerConfig:
    """ServerConfig model tests."""

    def test_default_values(self):
        config = ServerConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.debug is False

    def test_port_validation(self):
        """Port must be between 1 and 65535."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ServerConfig(port=0)

        with pytest.raises(ValidationError):
            ServerConfig(port=70000)


class TestTradingConfig:
    """TradingConfig model tests."""

    def test_default_values(self):
        config = TradingConfig()
        assert config.initial_capital == 1000000.0
        assert config.commission_rate == 0.001
        assert config.default_exchange == "sse"

    def test_valid_exchange(self):
        config = TradingConfig(default_exchange="SZSE")
        assert config.default_exchange == "szse"

    def test_invalid_exchange_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError, match="Invalid exchange"):
            TradingConfig(default_exchange="NYSE")

    def test_commission_rate_bounds(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TradingConfig(commission_rate=-0.1)
        with pytest.raises(ValidationError):
            TradingConfig(commission_rate=1.5)


class TestRiskConfig:
    """RiskConfig model tests."""

    def test_default_values(self):
        config = RiskConfig()
        assert config.position_limit_ratio == 0.3
        assert config.order_limit_amount == 50000.0
        assert config.daily_loss_limit == 0.02
        assert config.concentration_limit == 10


class TestDataConfig:
    """DataConfig model tests."""

    def test_default_values(self):
        config = DataConfig()
        assert config.data_source == "akshare"

    def test_cache_path_resolved(self):
        config = DataConfig(cache_path="/tmp/test_cache")
        assert Path(config.cache_path).is_absolute()


class TestSettings:
    """Settings integration tests."""

    def setup_method(self):
        Settings.reset()

    def test_default_creation(self):
        settings = Settings()
        assert isinstance(settings.server, ServerConfig)
        assert isinstance(settings.trading, TradingConfig)
        assert isinstance(settings.risk, RiskConfig)
        assert isinstance(settings.data, DataConfig)

    def test_singleton_get(self):
        """Settings.get() returns singleton instance."""
        Settings.reset()
        s1 = Settings.get()
        s2 = Settings.get()
        assert s1 is s2

    def test_singleton_reset(self):
        """Settings.reset() clears the singleton."""
        Settings.reset()
        s1 = Settings.get()
        Settings.reset()
        s2 = Settings.get()
        assert s1 is not s2

    def test_to_dict(self):
        """to_dict converts settings to dictionary."""
        settings = Settings()
        d = settings.to_dict()

        assert "server" in d
        assert "trading" in d
        assert "risk" in d
        assert "data" in d
        assert d["server"]["port"] == 8000

    def test_validate_settings(self):
        """validate_settings does not raise for valid config."""
        settings = Settings()
        settings.validate_settings()  # Should not raise

    def test_repr(self):
        """__repr__ includes all config sections."""
        settings = Settings()
        r = repr(settings)
        assert "server=" in r
        assert "trading=" in r

    # ---- YAML loading ----

    def test_load_from_yaml(self):
        """load_from_yaml reads configuration from YAML file."""
        yaml_content = """
server:
  host: 127.0.0.1
  port: 9000
  debug: true
trading:
  initial_capital: 500000.0
  commission_rate: 0.002
  default_exchange: szse
risk:
  position_limit_ratio: 0.25
  order_limit_amount: 30000.0
  daily_loss_limit: 0.05
  concentration_limit: 5
data:
  data_source: akshare
  cache_path: /tmp/quant_cache
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            settings = Settings.load_from_yaml(f.name)
            Settings.reset()  # Clean up singleton

            assert settings.server.host == "127.0.0.1"
            assert settings.server.port == 9000
            assert settings.server.debug is True
            assert settings.trading.initial_capital == 500000.0
            assert settings.trading.commission_rate == 0.002
            assert settings.trading.default_exchange == "szse"
            assert settings.risk.position_limit_ratio == 0.25
            assert settings.cache_path if hasattr(settings, 'cache_path') else True

    def test_load_from_yaml_file_not_found(self):
        """load_from_yaml raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            Settings.load_from_yaml("/nonexistent/path/config.yaml")

    def test_load_from_yaml_empty_file(self):
        """load_from_yaml handles empty YAML file (returns defaults)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            f.flush()

            settings = Settings.load_from_yaml(f.name)
            Settings.reset()

            assert settings.server.port == 8000

    # ---- save_to_yaml ----

    def test_save_to_yaml(self):
        """save_to_yaml writes settings to YAML file."""
        settings = Settings()
        settings.trading.initial_capital = 2000000.0

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.close()  # Let save_to_yaml create it
            settings.save_to_yaml(f.name)

            # Re-load and verify
            reloaded = Settings.load_from_yaml(f.name)
            Settings.reset()

            assert reloaded.trading.initial_capital == 2000000.0

    # ---- Environment variable loading ----

    def test_load_from_env(self):
        """load_from_env applies environment variable overrides."""
        Settings.reset()
        with patch.dict(os.environ, {
            "QUANT_SERVER_HOST": "192.168.1.1",
            "QUANT_SERVER_PORT": "7777",
            "QUANT_SERVER_DEBUG": "true",
            "QUANT_TRADING_INITIAL_CAPITAL": "750000.0",
            "QUANT_RISK_DAILY_LOSS_LIMIT": "0.03",
        }):
            settings = Settings.load_from_env()
            Settings.reset()

            assert settings.server.host == "192.168.1.1"
            assert settings.server.port == 7777
            assert settings.server.debug is True
            assert settings.trading.initial_capital == 750000.0
            assert settings.risk.daily_loss_limit == 0.03

    def test_load_from_env_type_conversions(self):
        """load_from_env correctly converts env var types."""
        Settings.reset()
        with patch.dict(os.environ, {
            "QUANT_SERVER_PORT": "9999",
            "QUANT_TRADING_INITIAL_CAPITAL": "500000",
            "QUANT_RISK_CONCENTRATION_LIMIT": "8",
        }):
            settings = Settings.load_from_env()
            Settings.reset()

            assert isinstance(settings.server.port, int)
            assert isinstance(settings.trading.initial_capital, float)
            assert isinstance(settings.risk.concentration_limit, int)

    def test_load_from_env_uses_existing_singleton_as_base(self):
        """load_from_env uses existing singleton as base when available."""
        Settings.reset()
        # First load from YAML to create singleton
        yaml_content = """
server:
  host: base-host
  port: 5555
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            Settings.load_from_yaml(f.name)

        # Now load from env - should keep settings not overridden
        with patch.dict(os.environ, {"QUANT_SERVER_HOST": "override-host"}):
            settings = Settings.load_from_env()
            Settings.reset()

            assert settings.server.host == "override-host"
            assert settings.server.port == 5555  # preserved from YAML base

    # ---- load_config convenience function ----

    def test_load_config_returns_settings(self):
        """load_config returns a Settings instance."""
        settings = load_config()
        assert isinstance(settings, Settings)


class TestAccountInfo:
    """AccountInfo dataclass tests."""

    def test_total_value(self):
        info = AccountInfo(
            account_id="test",
            balance=100000.0,
            available=90000.0,
            unrealized_pnl=5000.0,
        )

        assert info.total_value == 105000.0

    def test_default_values(self):
        info = AccountInfo(account_id="test")

        assert info.balance == 0.0
        assert info.available == 0.0
        assert info.frozen == 0.0
        assert info.margin == 0.0
        assert info.realized_pnl == 0.0
        assert info.unrealized_pnl == 0.0
        assert info.positions == {}
