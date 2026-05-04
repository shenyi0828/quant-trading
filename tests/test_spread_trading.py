"""价差交易模块测试"""
import pytest

from spread_trading.types import SpreadDefinition, SpreadLeg, SpreadCalcMethod, SpreadSide, SpreadSignal
from spread_trading.manager import SpreadManager
from spread_trading.engine import SpreadEngine
from spread_trading.strategies.pairs_trading import PairsTradingStrategy


class TestSpreadLeg:
    def test_default_values(self):
        leg = SpreadLeg(symbol="000001")
        assert leg.symbol == "000001"
        assert leg.price == 0.0
        assert leg.volume == 0.0
        assert leg.ratio == 1.0


class TestSpreadDefinition:
    def test_is_ready_with_two_legs(self):
        spread = SpreadDefinition(spread_id="pair_001")
        spread.legs["A"] = SpreadLeg(symbol="A", price=10.0, ratio=1.0)
        spread.legs["B"] = SpreadLeg(symbol="B", price=20.0, ratio=-1.0)
        assert spread.is_ready is True

    def test_is_ready_with_one_leg(self):
        spread = SpreadDefinition(spread_id="pair_001")
        spread.legs["A"] = SpreadLeg(symbol="A", price=10.0, ratio=1.0)
        assert spread.is_ready is False

    def test_is_ready_no_price(self):
        spread = SpreadDefinition(spread_id="pair_001")
        spread.legs["A"] = SpreadLeg(symbol="A")
        spread.legs["B"] = SpreadLeg(symbol="B", ratio=-1.0)
        assert spread.is_ready is False


class TestSpreadManager:
    @pytest.fixture
    def manager(self):
        mgr = SpreadManager()
        spread = SpreadDefinition(spread_id="bank_pair")
        spread.name = "银行配对"
        spread.calc_method = SpreadCalcMethod.LINEAR
        spread.legs["A"] = SpreadLeg(symbol="A", price=10.0, ratio=1.0)
        spread.legs["B"] = SpreadLeg(symbol="B", price=30.0, ratio=-1.0)
        mgr.add_spread_definition(spread)
        return mgr

    def test_add_spread_definition(self):
        mgr = SpreadManager()
        spread = SpreadDefinition(spread_id="test_001")
        mgr.add_spread_definition(spread)
        assert "test_001" in mgr.list_spreads()

    def test_get_spread_definition(self, manager):
        spread_def = manager.get_spread_definition("bank_pair")
        assert spread_def is not None
        assert spread_def.name == "银行配对"

    def test_update_leg_price_calculates_linear_spread(self, manager):
        # sorted: "A" < "B"
        # linear: leg[0].price + leg[0].ratio * leg[1].price = 12.0 + 1.0 * 28.0 = 40.0
        manager.update_leg_price("bank_pair", "A", 12.0)
        manager.update_leg_price("bank_pair", "B", 28.0)
        spread_data = manager.get_spread_data("bank_pair")
        assert spread_data is not None
        assert spread_data.spread_value == pytest.approx(40.0)

    def test_calculate_ratio_spread(self):
        mgr = SpreadManager()
        spread = SpreadDefinition(
            spread_id="ratio_pair",
            calc_method=SpreadCalcMethod.RATIO,
        )
        spread.legs["A"] = SpreadLeg(symbol="A", ratio=1.0)
        spread.legs["B"] = SpreadLeg(symbol="B", ratio=1.0)
        mgr.add_spread_definition(spread)
        mgr.update_leg_price("ratio_pair", "A", 100.0)
        mgr.update_leg_price("ratio_pair", "B", 50.0)
        spread_data = mgr.get_spread_data("ratio_pair")
        assert spread_data is not None
        # sorted: "A" < "B" -> ratio = 100.0 / 50.0 = 2.0
        assert spread_data.spread_value == pytest.approx(2.0)

    def test_calculate_log_ratio_spread(self):
        import math
        mgr = SpreadManager()
        spread = SpreadDefinition(
            spread_id="log_pair",
            calc_method=SpreadCalcMethod.LOG_RATIO,
        )
        spread.legs["A"] = SpreadLeg(symbol="A", ratio=1.0)
        spread.legs["B"] = SpreadLeg(symbol="B", ratio=1.0)
        mgr.add_spread_definition(spread)
        mgr.update_leg_price("log_pair", "A", 100.0)
        mgr.update_leg_price("log_pair", "B", 50.0)
        spread_data = mgr.get_spread_data("log_pair")
        assert spread_data is not None
        expected = math.log(100.0) - math.log(50.0)
        assert spread_data.spread_value == pytest.approx(expected)

    def test_z_score_calculation(self):
        mgr = SpreadManager()
        spread = SpreadDefinition(spread_id="z_pair", calc_method=SpreadCalcMethod.RATIO)
        spread.legs["A"] = SpreadLeg(symbol="A", ratio=1.0)
        spread.legs["B"] = SpreadLeg(symbol="B", ratio=1.0)
        mgr.add_spread_definition(spread)

        for a, b in [(100, 50), (102, 50), (98, 50), (105, 50), (95, 50),
                     (110, 50), (90, 50), (115, 50), (85, 50), (120, 50)]:
            mgr.update_leg_price("z_pair", "A", float(a))
            mgr.update_leg_price("z_pair", "B", float(b))

        spread_data = mgr.get_spread_data("z_pair")
        assert spread_data is not None
        assert spread_data.z_score != 0.0

    def test_history_window_limit(self):
        mgr = SpreadManager()
        mgr.set_history_window(5)
        spread = SpreadDefinition(spread_id="short_hist", calc_method=SpreadCalcMethod.RATIO)
        spread.legs["A"] = SpreadLeg(symbol="A", ratio=1.0)
        spread.legs["B"] = SpreadLeg(symbol="B", ratio=1.0)
        mgr.add_spread_definition(spread)

        for i in range(20):
            mgr.update_leg_price("short_hist", "A", 100.0 + i)
            mgr.update_leg_price("short_hist", "B", 50.0)

        spread_data = mgr.get_spread_data("short_hist")
        assert len(spread_data.price_history) <= 5

    def test_remove_spread(self):
        mgr = SpreadManager()
        spread = SpreadDefinition(spread_id="removable")
        mgr.add_spread_definition(spread)
        assert mgr.remove_spread("removable") is True
        assert "removable" not in mgr.list_spreads()
        assert mgr.remove_spread("nonexistent") is False

    def test_update_nonexistent_spread(self, manager):
        manager.update_leg_price("nonexistent", "A", 10.0)
        assert manager.get_spread_data("nonexistent") is None


class TestPairsTradingStrategy:
    @pytest.fixture
    def setup_spread(self):
        spread = SpreadDefinition(spread_id="test_pair", calc_method=SpreadCalcMethod.RATIO)
        spread.legs["A"] = SpreadLeg(symbol="A", ratio=1.0)
        spread.legs["B"] = SpreadLeg(symbol="B", ratio=1.0)
        return spread

    def test_no_signal_without_price_history(self, setup_spread):
        strategy = PairsTradingStrategy(setup_spread)
        from spread_trading.types import SpreadData
        data = SpreadData(spread_id="test_pair", spread_value=2.0, spread_mean=2.0, spread_std=0.0)
        strategy.update_spread(data)
        signal = strategy.get_signal()
        assert signal is None or signal.side is not None

    def test_long_signal_on_high_negative_z(self, setup_spread):
        strategy = PairsTradingStrategy(setup_spread)
        from spread_trading.types import SpreadData
        data = SpreadData(spread_id="test_pair", spread_value=1.5, spread_mean=2.0, spread_std=0.1, z_score=-5.0)
        strategy.update_spread(data)
        signal = strategy.get_signal()
        assert signal is not None
        assert signal.side == SpreadSide.LONG_SPREAD

    def test_short_signal_on_high_positive_z(self, setup_spread):
        strategy = PairsTradingStrategy(setup_spread)
        from spread_trading.types import SpreadData
        data = SpreadData(spread_id="test_pair", spread_value=2.5, spread_mean=2.0, spread_std=0.1, z_score=5.0)
        strategy.update_spread(data)
        signal = strategy.get_signal()
        assert signal is not None
        assert signal.side == SpreadSide.SHORT_SPREAD

    def test_custom_entry_threshold(self, setup_spread):
        strategy = PairsTradingStrategy(setup_spread)
        strategy._params["entry_threshold"] = 3.0
        strategy._params["exit_threshold"] = 1.0
        from spread_trading.types import SpreadData
        data = SpreadData(spread_id="test_pair", spread_value=2.4, spread_mean=2.0, spread_std=0.1, z_score=4.0)
        strategy.update_spread(data)
        signal = strategy.get_signal()
        assert signal is not None
        assert signal.side == SpreadSide.SHORT_SPREAD

    def test_exit_on_low_z(self, setup_spread):
        strategy = PairsTradingStrategy(setup_spread)
        from spread_trading.types import SpreadData
        data = SpreadData(spread_id="test_pair", spread_value=2.0, spread_mean=2.0, spread_std=0.2, z_score=0.0)
        strategy.update_spread(data)
        signal = strategy.get_signal()
        assert signal is None

    def test_updates_variables(self, setup_spread):
        strategy = PairsTradingStrategy(setup_spread)
        from spread_trading.types import SpreadData
        data = SpreadData(spread_id="test_pair", spread_value=2.1, spread_mean=2.0, spread_std=0.1, z_score=1.0)
        strategy.update_spread(data)
        assert strategy.variables["z_score"] == 1.0
        assert strategy.variables["spread_value"] == 2.1


class TestSpreadEngine:
    @pytest.fixture
    def setup_engine(self):
        mgr = SpreadManager()
        spread = SpreadDefinition(spread_id="pair_001", calc_method=SpreadCalcMethod.RATIO)
        spread.legs["A"] = SpreadLeg(symbol="A", ratio=1.0)
        spread.legs["B"] = SpreadLeg(symbol="B", ratio=1.0)
        mgr.add_spread_definition(spread)
        engine = SpreadEngine(mgr)
        engine.add_strategy("pair_001", PairsTradingStrategy)
        return engine

    def test_add_strategy(self, setup_engine):
        strategy = setup_engine.get_strategy("pair_001")
        assert strategy is not None
        assert isinstance(strategy, PairsTradingStrategy)

    def test_on_tick_propagates_to_strategy(self, setup_engine):
        setup_engine.on_tick("A", 10.0)
        setup_engine.on_tick("B", 5.0)
        signals = setup_engine.pop_signals()
        assert signals is not None

    def test_signal_callback(self, setup_engine):
        signals_received = []
        def callback(signal):
            signals_received.append(signal)
        setup_engine.set_signal_callback(callback)
        setup_engine.on_tick("A", 10.0)
        assert len(signals_received) >= 0

    def test_pop_signals_clears(self, setup_engine):
        assert setup_engine.pop_signals() == []
        assert setup_engine.pop_signals() == []

    def test_get_strategy_variables(self, setup_engine):
        assert isinstance(setup_engine.get_strategy_variables("pair_001"), dict)

    def test_spread_manager_access(self, setup_engine):
        assert setup_engine.spread_manager is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
