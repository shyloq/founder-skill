from __future__ import annotations

from dataclasses import dataclass

from .broker import PaperBroker
from .data import Candle
from .engine import Engine
from .risk import RiskConfig
from .strategy import EmaRsiStrategy


@dataclass
class Result:
    start_equity: float
    end_equity: float
    buy_hold_return: float
    max_drawdown: float
    n_trades: int
    win_rate: float

    @property
    def total_return(self) -> float:
        return self.end_equity / self.start_equity - 1

    def summary(self) -> str:
        return (f"return {self.total_return:+.1%} (buy&hold {self.buy_hold_return:+.1%}) | "
                f"max drawdown {self.max_drawdown:.1%} | round trips {self.n_trades} | "
                f"win rate {self.win_rate:.0%}")


def backtest(candles: list[Candle], strategy: EmaRsiStrategy | None = None,
             risk: RiskConfig | None = None, cash: float = 10_000.0) -> Result:
    strategy, risk = strategy or EmaRsiStrategy(), risk or RiskConfig()
    broker = PaperBroker(cash=cash)
    engine = Engine(strategy, risk, broker, cash)
    peak, mdd = cash, 0.0
    for i in range(strategy.warmup, len(candles)):
        engine.step(candles[: i + 1])  # no lookahead: only candles up to i
        eq = broker.equity(candles[i].close)
        peak = max(peak, eq)
        mdd = max(mdd, (peak - eq) / peak)
    if broker.qty > 0:
        broker.sell_all(candles[-1].close, "end")
    sells = [t for t in broker.trades if t.side == "sell"]
    wins, buy_cost = 0, None
    for t in broker.trades:
        if t.side == "buy":
            buy_cost = t.price
        elif buy_cost is not None and t.price > buy_cost:
            wins += 1
    start_px = candles[strategy.warmup].close
    return Result(cash, broker.cash, candles[-1].close / start_px - 1, mdd,
                  len(sells), wins / len(sells) if sells else 0.0)
