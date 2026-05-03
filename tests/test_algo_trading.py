"""算法交易模块测试"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from execution import SimGateway, OrderManager, Direction, Offset, Exchange, OrderType
from algo_trading import (
    AlgoEngine,
    AlgoStatus,
    AlgoResult,
    AlgoStatistics,
    TWAPParams,
    VWAPParams,
    IcebergParams,
    AlgoOrderManager,
)
from algo_trading.templates import TWAPAlgo, VWAPAlgo, IcebergAlgo


def create_order_manager() -> OrderManager:
    gateway = SimGateway(initial_capital=1000000, commission_rate=0.001)
    gateway.connect({})
    gateway.set_market_price("000001", 10.0)
    gateway.set_market_price("600000", 15.0)
    return OrderManager(gateway)


class TestTWAPParams:
    def test_twap_params_creation(self):
        params = TWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=1000,
            total_duration=60,
            interval=5,
        )
        
        assert params.symbol == "000001"
        assert params.total_quantity == 1000
        assert params.total_duration == 60
        assert params.interval == 5
    
    def test_twap_params_price_limit(self):
        params = TWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=1000,
            total_duration=60,
            interval=5,
            price_limit=12.0,
        )
        
        assert params.price_limit == 12.0


class TestTWAPAlgo:
    def test_twap_slice_calculation(self):
        om = create_order_manager()
        params = TWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=1000,
            total_duration=60,
            interval=5,
        )
        
        algo = TWAPAlgo(params, om)
        
        expected_slices = 12
        assert algo.slice_count == expected_slices
        
        expected_slice_qty = 84
        assert algo.slice_quantity >= expected_slice_qty
    
    def test_twap_start(self):
        om = create_order_manager()
        params = TWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=100,
            total_duration=10,
            interval=5,
        )
        
        algo = TWAPAlgo(params, om)
        algo.start()
        
        assert algo.get_status() == AlgoStatus.RUNNING
        assert algo.current_slice >= 1
    
    def test_twap_stop(self):
        om = create_order_manager()
        params = TWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=100,
            total_duration=10,
            interval=5,
        )
        
        algo = TWAPAlgo(params, om)
        algo.start()
        algo.stop()
        
        assert algo.get_status() == AlgoStatus.STOPPED
    
    def test_twap_pause_resume(self):
        om = create_order_manager()
        params = TWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=100,
            total_duration=10,
            interval=5,
        )
        
        algo = TWAPAlgo(params, om)
        algo.start()
        algo.pause()
        
        assert algo.get_status() == AlgoStatus.PAUSED
        
        algo.resume()
        assert algo.get_status() == AlgoStatus.RUNNING
    
    def test_twap_statistics(self):
        om = create_order_manager()
        params = TWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=100,
            total_duration=10,
            interval=5,
        )
        
        algo = TWAPAlgo(params, om)
        algo.start()
        
        stats = algo.get_statistics()
        assert stats.algo_id == algo.algo_id
        assert stats.total_quantity == 100


class TestVWAPParams:
    def test_vwap_params_creation(self):
        params = VWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=1000,
            target_pov=0.1,
            max_pov=0.3,
        )
        
        assert params.symbol == "000001"
        assert params.target_pov == 0.1
        assert params.max_pov == 0.3
    
    def test_vwap_pov_constraints(self):
        params = VWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=1000,
            target_pov=0.05,
            max_pov=0.15,
        )
        
        assert params.target_pov < params.max_pov


class TestVWAPAlgo:
    def test_vwap_start(self):
        om = create_order_manager()
        params = VWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=100,
            target_pov=0.1,
        )
        
        algo = VWAPAlgo(params, om)
        algo.start()
        
        assert algo.get_status() == AlgoStatus.RUNNING
    
    def test_vwap_with_volume_profile(self):
        om = create_order_manager()
        params = VWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=1000,
            target_pov=0.1,
        )
        
        volume_profile = [
            {"interval": 0, "volume": 50000, "percentage": 0.1},
            {"interval": 1, "volume": 80000, "percentage": 0.16},
            {"interval": 2, "volume": 100000, "percentage": 0.2},
        ]
        
        algo = VWAPAlgo(params, om, volume_profile=volume_profile)
        algo.start()
        
        assert algo.get_status() == AlgoStatus.RUNNING
        assert algo.target_pov == 0.1
    
    def test_vwap_tick_handling(self):
        om = create_order_manager()
        params = VWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=100,
            target_pov=0.1,
        )
        
        algo = VWAPAlgo(params, om)
        algo.start()
        
        tick_data = {
            "symbol": "000001",
            "price": 10.5,
            "volume": 1000,
        }
        
        algo.on_tick(tick_data)
        
        assert algo.current_interval_volume >= 0


class TestIcebergParams:
    def test_iceberg_params_creation(self):
        params = IcebergParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=1000,
            display_quantity=100,
            price=10.0,
        )
        
        assert params.symbol == "000001"
        assert params.display_quantity == 100
        assert params.price == 10.0
    
    def test_iceberg_params_randomize(self):
        params = IcebergParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=1000,
            display_quantity=100,
            price=10.0,
            randomize=True,
        )
        
        assert params.randomize


class TestIcebergAlgo:
    def test_iceberg_start(self):
        om = create_order_manager()
        params = IcebergParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=500,
            display_quantity=50,
            price=10.0,
        )
        
        algo = IcebergAlgo(params, om)
        algo.start()
        
        assert algo.get_status() == AlgoStatus.RUNNING
        assert algo.hidden_remaining == 500
    
    def test_iceberg_display_quantity(self):
        om = create_order_manager()
        params = IcebergParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=500,
            display_quantity=50,
            price=10.0,
        )
        
        algo = IcebergAlgo(params, om)
        
        assert algo.display_quantity == 50
    
    def test_iceberg_hidden_remaining(self):
        om = create_order_manager()
        params = IcebergParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=500,
            display_quantity=50,
            price=10.0,
        )
        
        algo = IcebergAlgo(params, om)
        algo.start()
        
        remaining = algo.hidden_remaining
        assert remaining >= 0
        assert remaining <= 500
    
    def test_iceberg_order_tracking(self):
        om = create_order_manager()
        params = IcebergParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=500,
            display_quantity=50,
            price=10.0,
        )
        
        algo = IcebergAlgo(params, om)
        algo.start()
        
        stats = algo.get_statistics()
        assert stats.total_quantity == 500


class TestAlgoEngine:
    def test_engine_creation(self):
        om = create_order_manager()
        engine = AlgoEngine(om)
        
        assert engine.order_manager == om
        assert engine.algo_count == 0
    
    def test_register_twap_algo(self):
        om = create_order_manager()
        engine = AlgoEngine(om)
        
        params = TWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=100,
            total_duration=10,
            interval=5,
        )
        
        algo_id = engine.register_algo(TWAPAlgo, params)
        
        assert algo_id is not None
        assert engine.algo_count == 1
    
    def test_register_vwap_algo(self):
        om = create_order_manager()
        engine = AlgoEngine(om)
        
        params = VWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=100,
        )
        
        algo_id = engine.register_algo(VWAPAlgo, params)
        
        assert algo_id is not None
        assert engine.algo_count == 1
    
    def test_register_iceberg_algo(self):
        om = create_order_manager()
        engine = AlgoEngine(om)
        
        params = IcebergParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=500,
            display_quantity=50,
            price=10.0,
        )
        
        algo_id = engine.register_algo(IcebergAlgo, params)
        
        assert algo_id is not None
        assert engine.algo_count == 1
    
    def test_start_algo(self):
        om = create_order_manager()
        engine = AlgoEngine(om)
        
        params = TWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=100,
            total_duration=10,
            interval=5,
        )
        
        algo_id = engine.register_algo(TWAPAlgo, params)
        result = engine.start_algo(algo_id)
        
        assert result
        assert engine.get_algo_status(algo_id) == AlgoStatus.RUNNING
    
    def test_stop_algo(self):
        om = create_order_manager()
        engine = AlgoEngine(om)
        
        params = TWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=100,
            total_duration=10,
            interval=5,
        )
        
        algo_id = engine.register_algo(TWAPAlgo, params)
        engine.start_algo(algo_id)
        result = engine.stop_algo(algo_id)
        
        assert result
        assert engine.get_algo_status(algo_id) == AlgoStatus.STOPPED
    
    def test_pause_resume_algo(self):
        om = create_order_manager()
        engine = AlgoEngine(om)
        
        params = TWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=100,
            total_duration=10,
            interval=5,
        )
        
        algo_id = engine.register_algo(TWAPAlgo, params)
        engine.start_algo(algo_id)
        
        engine.pause_algo(algo_id)
        assert engine.get_algo_status(algo_id) == AlgoStatus.PAUSED
        
        engine.resume_algo(algo_id)
        assert engine.get_algo_status(algo_id) == AlgoStatus.RUNNING
    
    def test_unregister_algo(self):
        om = create_order_manager()
        engine = AlgoEngine(om)
        
        params = TWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=100,
            total_duration=10,
            interval=5,
        )
        
        algo_id = engine.register_algo(TWAPAlgo, params)
        
        result = engine.unregister_algo(algo_id)
        assert result
        assert engine.algo_count == 0
    
    def test_get_all_algos(self):
        om = create_order_manager()
        engine = AlgoEngine(om)
        
        params1 = TWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=100,
            total_duration=10,
            interval=5,
        )
        
        params2 = IcebergParams(
            symbol="600000",
            exchange="sse",
            direction="buy",
            total_quantity=500,
            display_quantity=50,
            price=15.0,
        )
        
        engine.register_algo(TWAPAlgo, params1)
        engine.register_algo(IcebergAlgo, params2)
        
        all_algos = engine.get_all_algos()
        
        assert len(all_algos) == 2
    
    def test_tick_distribution(self):
        om = create_order_manager()
        engine = AlgoEngine(om)
        
        params = TWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=100,
            total_duration=10,
            interval=5,
        )
        
        algo_id = engine.register_algo(TWAPAlgo, params)
        engine.start_algo(algo_id)
        
        tick_data = {
            "symbol": "000001",
            "price": 10.5,
            "volume": 1000,
        }
        
        engine.on_tick(tick_data)
        
        assert engine.get_algo_status(algo_id) == AlgoStatus.RUNNING
    
    def test_stop_all_algos(self):
        om = create_order_manager()
        engine = AlgoEngine(om)
        
        params1 = TWAPParams(
            symbol="000001",
            exchange="sse",
            direction="buy",
            total_quantity=100,
            total_duration=10,
            interval=5,
        )
        
        params2 = IcebergParams(
            symbol="600000",
            exchange="sse",
            direction="buy",
            total_quantity=500,
            display_quantity=50,
            price=15.0,
        )
        
        id1 = engine.register_algo(TWAPAlgo, params1)
        id2 = engine.register_algo(IcebergAlgo, params2)
        
        engine.start_algo(id1)
        engine.start_algo(id2)
        
        stopped_count = engine.stop_all_algos()
        
        assert stopped_count == 2


class TestAlgoOrderManager:
    def test_creation(self):
        mgr = AlgoOrderManager("test_algo", "parent_001")
        
        assert mgr.algo_id == "test_algo"
        assert mgr.parent_order_id == "parent_001"
        assert mgr.child_count == 0
    
    def test_set_total_target(self):
        mgr = AlgoOrderManager("test_algo", "parent_001")
        mgr.set_total_target(1000)
        
        stats = mgr.get_statistics()
        assert stats.total_quantity == 1000
    
    def test_create_child_order(self):
        mgr = AlgoOrderManager("test_algo", "parent_001")
        mgr.set_total_target(1000)
        
        child = mgr.create_child_order(
            gateway_order_id="child_001",
            slice_index=0,
            quantity=100,
            price=10.0,
        )
        
        assert child.child_order_id == "child_001"
        assert child.quantity == 100
        assert child.price == 10.0
        assert mgr.child_count == 1
    
    def test_get_child_orders(self):
        mgr = AlgoOrderManager("test_algo", "parent_001")
        mgr.set_total_target(500)
        
        mgr.create_child_order("child_001", 0, 100, 10.0)
        mgr.create_child_order("child_002", 1, 100, 10.5)
        
        children = mgr.get_child_orders()
        
        assert len(children) == 2
        assert children[0].slice_index == 0
        assert children[1].slice_index == 1
    
    def test_get_statistics(self):
        mgr = AlgoOrderManager("test_algo", "parent_001")
        mgr.set_total_target(500)
        
        mgr.create_child_order("child_001", 0, 100, 10.0)
        mgr.create_child_order("child_002", 1, 100, 10.5)
        
        stats = mgr.get_statistics()
        
        assert stats.child_orders == 2
        assert stats.total_quantity == 500
    
    def test_is_complete(self):
        mgr = AlgoOrderManager("test_algo", "parent_001")
        mgr.set_total_target(0)
        
        assert mgr.is_complete
        
        mgr.set_total_target(100)
        assert not mgr.is_complete


class TestAlgoStatistics:
    def test_fill_rate(self):
        stats = AlgoStatistics(
            algo_id="test",
            total_quantity=100,
            filled_quantity=50,
        )
        
        assert stats.fill_rate == 0.5
    
    def test_is_complete(self):
        stats = AlgoStatistics(
            algo_id="test",
            total_quantity=100,
            filled_quantity=100,
        )
        
        assert stats.is_complete
        
        stats.filled_quantity = 50
        assert not stats.is_complete
    
    def test_zero_fill_rate(self):
        stats = AlgoStatistics(
            algo_id="test",
            total_quantity=100,
            filled_quantity=0,
        )
        
        assert stats.fill_rate == 0.0
    
    def test_avg_price_calculation(self):
        stats = AlgoStatistics(
            algo_id="test",
            total_quantity=100,
            filled_quantity=50,
            total_cost=500.0,
        )
        
        assert stats.avg_price == 10.0


class TestAlgoStatus:
    def test_status_values(self):
        assert AlgoStatus.STOPPED.value == "stopped"
        assert AlgoStatus.RUNNING.value == "running"
        assert AlgoStatus.PAUSED.value == "paused"
        assert AlgoStatus.COMPLETED.value == "completed"


class TestAlgoResult:
    def test_result_values(self):
        assert AlgoResult.SUCCESS.value == "success"
        assert AlgoResult.PARTIAL.value == "partial"
        assert AlgoResult.TIMEOUT.value == "timeout"
        assert AlgoResult.REJECTED.value == "rejected"
        assert AlgoResult.ERROR.value == "error"