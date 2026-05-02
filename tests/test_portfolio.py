"""组合管理模块测试"""
from datetime import date
import pytest

from portfolio import (
    PortfolioManager,
    AllocationEngine,
    PnLCalculator,
    AllocationMethod,
    AccountStatus,
    SubAccount,
    PositionInfo,
)


class TestAllocationEngine:
    def test_equal_weight_allocation(self):
        engine = AllocationEngine(total_capital=100000)
        account_ids = ["acc1", "acc2", "acc3"]
        
        allocations = engine.equal_weight(account_ids)
        
        assert len(allocations) == 3
        for acc_id in account_ids:
            assert acc_id in allocations
            assert allocations[acc_id].weight == pytest.approx(1.0 / 3)
            assert allocations[acc_id].allocated_capital == pytest.approx(100000 / 3)
            assert allocations[acc_id].method == AllocationMethod.EQUAL_WEIGHT
    
    def test_manual_weights_allocation(self):
        engine = AllocationEngine(total_capital=100000)
        weights = {"acc1": 0.5, "acc2": 0.3, "acc3": 0.2}
        
        allocations = engine.manual_weights(weights)
        
        assert len(allocations) == 3
        assert allocations["acc1"].allocated_capital == 50000
        assert allocations["acc2"].allocated_capital == 30000
        assert allocations["acc3"].allocated_capital == 20000
    
    def test_manual_weights_auto_normalize(self):
        engine = AllocationEngine(total_capital=100000)
        weights = {"acc1": 5, "acc2": 3, "acc3": 2}
        
        allocations = engine.manual_weights(weights)
        
        assert allocations["acc1"].weight == 0.5
        assert allocations["acc2"].weight == 0.3
        assert allocations["acc3"].weight == 0.2
    
    def test_risk_parity_not_implemented(self):
        engine = AllocationEngine(total_capital=100000)
        
        with pytest.raises(NotImplementedError):
            engine.risk_parity(["acc1", "acc2"])
    
    def test_summary(self):
        engine = AllocationEngine(total_capital=100000)
        engine.equal_weight(["acc1", "acc2"])
        
        summary = engine.summary()
        
        assert summary["total_capital"] == 100000
        assert summary["allocated_capital"] == 100000
        assert summary["unallocated_capital"] == 0
        assert summary["account_count"] == 2


class TestPnLCalculator:
    def test_calculate_account_pnl(self):
        calculator = PnLCalculator()
        account = SubAccount(
            account_id="test_acc",
            strategy_name="test_strategy",
            initial_capital=10000
        )
        account.positions["AAPL"] = PositionInfo(
            symbol="AAPL",
            quantity=100,
            avg_cost=150.0,
            current_price=160.0
        )
        
        snapshot = calculator.calculate_account_pnl(account, date(2024, 1, 1))
        
        assert snapshot.account_id == "test_acc"
        assert snapshot.total_value == 10000 + 100 * 160.0
        assert snapshot.position_profit == 100 * (160.0 - 150.0)
    
    def test_daily_pnl_tracking(self):
        calculator = PnLCalculator()
        account = SubAccount(
            account_id="test_acc",
            strategy_name="test_strategy",
            initial_capital=10000
        )
        
        calculator.calculate_account_pnl(account, date(2024, 1, 1))
        account.positions["AAPL"] = PositionInfo(
            symbol="AAPL", quantity=100, avg_cost=150.0, current_price=160.0
        )
        calculator.calculate_account_pnl(account, date(2024, 1, 2))
        
        daily_records = calculator.get_account_daily_pnl("test_acc")
        
        assert len(daily_records) == 2
    
    def test_portfolio_pnl(self):
        calculator = PnLCalculator()
        accounts = [
            SubAccount(account_id="acc1", strategy_name="s1", initial_capital=10000),
            SubAccount(account_id="acc2", strategy_name="s2", initial_capital=20000),
        ]
        
        results = calculator.calculate_portfolio_pnl(accounts, date(2024, 1, 1))
        
        assert len(results) == 2
        assert "acc1" in results
        assert "acc2" in results
    
    def test_get_dashboard_data(self):
        calculator = PnLCalculator()
        accounts = [
            SubAccount(account_id="acc1", strategy_name="s1", initial_capital=10000),
        ]
        accounts[0].positions["AAPL"] = PositionInfo(
            symbol="AAPL", quantity=10, avg_cost=100.0, current_price=110.0
        )
        
        data = calculator.get_dashboard_data(accounts)
        
        assert "total_value" in data
        assert "total_profit" in data
        assert "account_pnl" in data
        assert "position_pnl" in data


class TestPortfolioManager:
    def test_create_account(self):
        manager = PortfolioManager(total_capital=100000)
        
        account = manager.create_account("strategy_a")
        
        assert account.strategy_name == "strategy_a"
        assert account.account_id.startswith("ACC_")
        assert account.status == AccountStatus.ACTIVE
    
    def test_create_multiple_accounts(self):
        manager = PortfolioManager(total_capital=100000)
        
        acc1 = manager.create_account("strategy_a")
        acc2 = manager.create_account("strategy_b")
        
        assert len(manager.accounts) == 2
        assert acc1.account_id != acc2.account_id
    
    def test_remove_account(self):
        manager = PortfolioManager(total_capital=100000)
        account = manager.create_account("strategy_a")
        
        result = manager.remove_account(account.account_id)
        
        assert result is True
        assert manager.accounts[account.account_id].status == AccountStatus.CLOSED
    
    def test_pause_and_resume_account(self):
        manager = PortfolioManager(total_capital=100000)
        account = manager.create_account("strategy_a")
        
        manager.pause_account(account.account_id)
        assert manager.accounts[account.account_id].status == AccountStatus.PAUSED
        
        manager.resume_account(account.account_id)
        assert manager.accounts[account.account_id].status == AccountStatus.ACTIVE
    
    def test_update_position(self):
        manager = PortfolioManager(total_capital=100000)
        account = manager.create_account("strategy_a")
        
        position = manager.update_position(
            account.account_id,
            symbol="AAPL",
            quantity=100,
            avg_cost=150.0,
            current_price=160.0
        )
        
        assert position is not None
        assert account.positions["AAPL"].quantity == 100
        assert account.positions["AAPL"].profit == 1000.0
    
    def test_get_aggregated_positions(self):
        manager = PortfolioManager(total_capital=100000)
        acc1 = manager.create_account("s1", initial_capital=50000)
        acc2 = manager.create_account("s2", initial_capital=50000)
        
        manager.update_position(acc1.account_id, "AAPL", 50, 150.0, 160.0)
        manager.update_position(acc2.account_id, "AAPL", 50, 150.0, 160.0)
        
        aggregated = manager.get_aggregated_positions()
        
        assert "AAPL" in aggregated
        assert aggregated["AAPL"].quantity == 100
    
    def test_allocate_capital_equal_weight(self):
        manager = PortfolioManager(total_capital=100000)
        manager.create_account("s1")
        manager.create_account("s2")
        
        allocations = manager.allocate_capital(AllocationMethod.EQUAL_WEIGHT)
        
        assert len(allocations) == 2
        for allocation in allocations.values():
            assert allocation.allocated_capital == 50000
    
    def test_get_summary(self):
        manager = PortfolioManager(total_capital=100000)
        acc1 = manager.create_account("s1", initial_capital=50000)
        acc2 = manager.create_account("s2", initial_capital=50000)
        
        manager.update_position(acc1.account_id, "AAPL", 100, 100.0, 110.0)
        
        summary = manager.get_summary()
        
        assert summary.total_capital == 100000
        assert summary.account_count == 2
        assert summary.active_accounts == 2
        assert len(summary.accounts) == 2
    
    def test_calculate_pnl(self):
        manager = PortfolioManager(total_capital=100000)
        acc1 = manager.create_account("s1", initial_capital=50000)
        
        manager.update_position(acc1.account_id, "AAPL", 100, 100.0, 110.0)
        
        snapshots = manager.calculate_pnl(date(2024, 1, 1))
        
        assert len(snapshots) == 1
        assert acc1.account_id in snapshots
    
    def test_to_dict(self):
        manager = PortfolioManager(total_capital=100000)
        manager.create_account("s1")
        
        data = manager.to_dict()
        
        assert data["total_capital"] == 100000
        assert data["account_count"] == 1
        assert len(data["accounts"]) == 1


class TestPositionInfo:
    def test_market_value(self):
        position = PositionInfo(
            symbol="AAPL",
            quantity=100,
            avg_cost=150.0,
            current_price=160.0
        )
        
        assert position.market_value == 16000.0
    
    def test_profit(self):
        position = PositionInfo(
            symbol="AAPL",
            quantity=100,
            avg_cost=150.0,
            current_price=160.0
        )
        
        assert position.profit == 1000.0
    
    def test_profit_pct(self):
        position = PositionInfo(
            symbol="AAPL",
            quantity=100,
            avg_cost=150.0,
            current_price=160.0
        )
        
        assert position.profit_pct == 10.0 / 150.0


class TestSubAccount:
    def test_total_value(self):
        account = SubAccount(
            account_id="test",
            strategy_name="test",
            initial_capital=10000
        )
        account.positions["AAPL"] = PositionInfo(
            symbol="AAPL", quantity=10, avg_cost=100.0, current_price=110.0
        )
        
        assert account.total_value == 10000 + 10 * 110.0
    
    def test_return_rate(self):
        account = SubAccount(
            account_id="test",
            strategy_name="test",
            initial_capital=10000
        )
        account.positions["AAPL"] = PositionInfo(
            symbol="AAPL", quantity=10, avg_cost=100.0, current_price=110.0
        )
        
        expected_value = 10000 + 10 * 110.0
        expected_return_rate = (expected_value - 10000) / 10000
        assert account.return_rate == pytest.approx(expected_return_rate)
    
    def test_update_position_price(self):
        account = SubAccount(
            account_id="test",
            strategy_name="test",
            initial_capital=10000
        )
        account.positions["AAPL"] = PositionInfo(
            symbol="AAPL", quantity=10, avg_cost=100.0, current_price=100.0
        )
        
        account.update_position_price("AAPL", 120.0)
        
        assert account.positions["AAPL"].current_price == 120.0
        assert account.positions["AAPL"].profit == 200.0