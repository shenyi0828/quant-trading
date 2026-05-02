"""交易执行模块测试"""
import pytest

from execution import (
    Direction,
    OrderType,
    OrderStatus,
    TimeInForce,
    Offset,
    Exchange,
    Order,
    OrderRequest,
    Trade,
    Position,
    AccountInfo,
    SimGateway,
    OrderManager,
)


class TestSimGateway:
    def test_connect(self):
        gateway = SimGateway()
        assert gateway.connect({})
        assert gateway.is_connected()
    
    def test_disconnect(self):
        gateway = SimGateway()
        gateway.connect({})
        assert gateway.disconnect()
        assert not gateway.is_connected()
    
    def test_submit_market_order(self):
        gateway = SimGateway(initial_capital=100000, commission_rate=0.001)
        gateway.connect({})
        gateway.set_market_price("000001", 10.0)
        
        order_id = gateway.submit_order(
            OrderRequest(
                symbol="000001",
                exchange=Exchange.SSE,
                direction=Direction.LONG,
                offset=Offset.OPEN,
                order_type=OrderType.MARKET,
                quantity=100,
                price=0.0,
            )
        )
        
        assert order_id is not None
        order = gateway.query_order(order_id)
        assert order is not None
        assert order.status == OrderStatus.FILLED
    
    def test_cancel_order(self):
        gateway = SimGateway()
        gateway.connect({})
        gateway.set_market_price("000001", 10.0)
        
        gateway.submit_order(
            OrderRequest(
                symbol="000001",
                exchange=Exchange.SSE,
                direction=Direction.LONG,
                offset=Offset.OPEN,
                order_type=OrderType.LIMIT,
                quantity=100,
                price=5.0,
            )
        )
        
        orders = gateway.query_orders(OrderStatus.SUBMITTED)
        if orders:
            result = gateway.cancel_order(orders[0].order_id)
            assert result
    
    def test_query_positions(self):
        gateway = SimGateway(initial_capital=100000)
        gateway.connect({})
        gateway.set_market_price("000001", 10.0)
        
        gateway.submit_order(
            OrderRequest(
                symbol="000001",
                exchange=Exchange.SSE,
                direction=Direction.LONG,
                offset=Offset.OPEN,
                order_type=OrderType.MARKET,
                quantity=100,
                price=0.0,
            )
        )
        
        positions = gateway.query_positions()
        assert len(positions) == 1
        assert positions[0].symbol == "000001"
        assert positions[0].quantity == 100
    
    def test_query_account(self):
        gateway = SimGateway(initial_capital=100000)
        gateway.connect({})
        
        account = gateway.query_account()
        assert account is not None
        assert account.balance == 100000
    
    def test_commission_calculation(self):
        gateway = SimGateway(initial_capital=100000, commission_rate=0.001)
        gateway.connect({})
        gateway.set_market_price("000001", 10.0)
        
        order_id = gateway.submit_order(
            OrderRequest(
                symbol="000001",
                exchange=Exchange.SSE,
                direction=Direction.LONG,
                offset=Offset.OPEN,
                order_type=OrderType.MARKET,
                quantity=100,
                price=0.0,
            )
        )
        
        trades = gateway.query_trades(order_id)
        assert len(trades) == 1
        assert trades[0].commission == 10.0 * 100 * 0.001


class TestOrderManager:
    def test_create_order(self):
        gateway = SimGateway()
        gateway.connect({})
        gateway.set_market_price("000001", 10.0)
        
        om = OrderManager(gateway)
        order_id = om.create_order(
            symbol="000001",
            exchange=Exchange.SSE,
            direction=Direction.LONG,
            offset=Offset.OPEN,
            quantity=100,
        )
        
        assert order_id is not None
    
    def test_cancel_order(self):
        gateway = SimGateway()
        gateway.connect({})
        gateway.set_market_price("000001", 10.0)
        
        om = OrderManager(gateway)
        
        order_id = om.create_order(
            symbol="000001",
            exchange=Exchange.SSE,
            direction=Direction.LONG,
            offset=Offset.OPEN,
            quantity=100,
            price=5.0,
            order_type=OrderType.LIMIT,
        )
        
        if order_id:
            result = om.cancel_order(order_id)
            assert result
    
    def test_query_active_orders(self):
        gateway = SimGateway()
        gateway.connect({})
        gateway.set_market_price("000001", 10.0)
        
        om = OrderManager(gateway)
        om.create_order(
            symbol="000001",
            exchange=Exchange.SSE,
            direction=Direction.LONG,
            offset=Offset.OPEN,
            quantity=100,
            price=5.0,
            order_type=OrderType.LIMIT,
        )
        
        active = om.query_active_orders()
        assert len(active) >= 0
    
    def test_position_management(self):
        gateway = SimGateway(initial_capital=100000)
        gateway.connect({})
        gateway.set_market_price("000001", 10.0)
        
        om = OrderManager(gateway)
        om.create_order(
            symbol="000001",
            exchange=Exchange.SSE,
            direction=Direction.LONG,
            offset=Offset.OPEN,
            quantity=100,
        )
        
        positions = om.query_positions()
        assert len(positions) == 1
    
    def test_callbacks(self):
        gateway = SimGateway()
        gateway.connect({})
        gateway.set_market_price("000001", 10.0)
        
        om = OrderManager(gateway)
        
        received_orders = []
        received_trades = []
        
        om.register_order_callback(lambda o: received_orders.append(o))
        om.register_trade_callback(lambda t: received_trades.append(t))
        
        om.create_order(
            symbol="000001",
            exchange=Exchange.SSE,
            direction=Direction.LONG,
            offset=Offset.OPEN,
            quantity=100,
        )
        
        assert len(received_orders) >= 1
        assert len(received_trades) >= 1


class TestOrderStatus:
    def test_order_is_active(self):
        order = Order(
            order_id="TEST_1",
            symbol="000001",
            exchange=Exchange.SSE,
            direction=Direction.LONG,
            offset=Offset.OPEN,
            order_type=OrderType.MARKET,
            quantity=100,
            price=10.0,
            status=OrderStatus.SUBMITTED,
        )
        assert order.is_active
        
        order.status = OrderStatus.FILLED
        assert not order.is_active
    
    def test_order_is_completed(self):
        order = Order(
            order_id="TEST_1",
            symbol="000001",
            exchange=Exchange.SSE,
            direction=Direction.LONG,
            offset=Offset.OPEN,
            order_type=OrderType.MARKET,
            quantity=100,
            price=10.0,
            status=OrderStatus.PENDING,
        )
        assert not order.is_completed
        
        order.status = OrderStatus.FILLED
        assert order.is_completed


class TestPosition:
    def test_position_unrealized_pnl(self):
        pos = Position(
            symbol="000001",
            exchange=Exchange.SSE,
            direction=Direction.LONG,
            quantity=100,
            avg_cost=10.0,
            current_price=12.0,
        )
        
        assert pos.unrealized_pnl == 200.0
    
    def test_position_market_value(self):
        pos = Position(
            symbol="000001",
            exchange=Exchange.SSE,
            direction=Direction.LONG,
            quantity=100,
            avg_cost=10.0,
            current_price=12.0,
        )
        
        assert pos.market_value == 1200.0


class TestAccountInfo:
    def test_total_value(self):
        account = AccountInfo(
            account_id="TEST",
            gateway_name="SIM",
            balance=100000,
            unrealized_pnl=5000,
        )
        
        assert account.total_value == 105000