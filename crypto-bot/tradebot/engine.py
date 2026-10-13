"""One decision step shared by backtest, paper and live so they behave identically."""
from __future__ import annotations

from .data import Candle
from .risk import KillSwitch, RiskConfig, exit_prices, position_size
from .strategy import EmaRsiStrategy


class Engine:
    def __init__(self, strategy: EmaRsiStrategy, risk: RiskConfig, broker, start_equity: float):
        self.strategy, self.risk, self.broker = strategy, risk, broker
        self.kill = KillSwitch(risk, start_equity)
        self.stop = self.target = 0.0

    def step(self, history: list[Candle]) -> str | None:
        """Process the newest *closed* candle in `history`. Returns an action label or None."""
        c = history[-1]
        equity = self.broker.equity(c.close)
        halted = self.kill.update(equity)

        if self.broker.qty > 0:  # manage open position: stops are checked on intrabar range
            if c.low <= self.stop:
                self.broker.sell_all(self.stop, "stop-loss")
                return "stop-loss"
            if c.high >= self.target:
                self.broker.sell_all(self.target, "take-profit")
                return "take-profit"

        sig = self.strategy.signal([x.close for x in history])
        if sig == "sell" and self.broker.qty > 0:
            self.broker.sell_all(c.close, "signal")
            return "sell"
        if sig == "buy" and self.broker.qty == 0 and not halted:
            qty = position_size(equity, c.close, self.risk)
            if self.broker.buy(c.close, qty, "signal"):
                self.stop, self.target = exit_prices(c.close, self.risk)
                return "buy"
        if halted and self.broker.qty > 0:
            self.broker.sell_all(c.close, "kill-switch")
            return "kill-switch"
        return None
