import unittest

from tradebot.backtest import backtest
from tradebot.broker import PaperBroker
from tradebot.data import synthetic
from tradebot.risk import KillSwitch, RiskConfig, position_size
from tradebot.strategy import EmaRsiStrategy, ema, rsi


class StrategyTests(unittest.TestCase):
    def test_ema_constant(self):
        self.assertEqual(ema([5.0] * 10, 3), [5.0] * 10)

    def test_rsi_bounds(self):
        up = rsi([float(i) for i in range(1, 60)])
        self.assertEqual(up[-1], 100.0)
        down = rsi([float(i) for i in range(60, 1, -1)])
        self.assertEqual(down[-1], 0.0)

    def test_cross_up_buys_and_rsi_filter_blocks(self):
        closes = [100.0] * 40 + [90.0] * 10 + [100, 110, 120]
        sigs = lambda s: [s.signal(closes[: i + 1]) for i in range(len(closes))]
        self.assertIn("buy", sigs(EmaRsiStrategy(rsi_max=101.0)))
        self.assertNotIn("buy", sigs(EmaRsiStrategy(rsi_max=0.0)))
        self.assertIn("sell", sigs(EmaRsiStrategy()))


class RiskTests(unittest.TestCase):
    def test_size_loses_about_risk_at_stop(self):
        cfg = RiskConfig(max_position_pct=10)
        qty = position_size(10_000, 100, cfg)
        self.assertAlmostEqual(qty * 100 * cfg.stop_loss_pct, 100.0)

    def test_size_capped(self):
        self.assertLessEqual(position_size(1000, 10, RiskConfig(stop_loss_pct=0.0001)) * 10, 950.001)

    def test_killswitch(self):
        k = KillSwitch(RiskConfig(max_drawdown_pct=0.2), 1000)
        self.assertFalse(k.update(900))
        self.assertTrue(k.update(790))


class BrokerTests(unittest.TestCase):
    def test_round_trip_costs_fees(self):
        b = PaperBroker(cash=1000)
        b.buy(100, 5)
        b.sell_all(100)
        self.assertLess(b.cash, 1000)
        self.assertEqual(b.qty, 0)

    def test_cannot_overspend(self):
        b = PaperBroker(cash=100)
        t = b.buy(100, 50)
        self.assertLessEqual(t.price * t.qty + t.fee, 100.0001)


class BacktestTests(unittest.TestCase):
    def test_runs_and_is_deterministic(self):
        a, b = backtest(synthetic()), backtest(synthetic())
        self.assertEqual(a, b)
        self.assertGreater(a.n_trades, 0)
        self.assertGreater(a.end_equity, 0)


if __name__ == "__main__":
    unittest.main()
