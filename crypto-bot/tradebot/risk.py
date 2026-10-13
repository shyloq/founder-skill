"""Position sizing and exit rules. Long-only, one position at a time."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskConfig:
    risk_per_trade: float = 0.01   # fraction of equity risked per trade
    stop_loss_pct: float = 0.03    # hard stop below entry
    take_profit_pct: float = 0.06  # take profit above entry
    max_position_pct: float = 0.95 # cap notional as fraction of equity
    max_drawdown_pct: float = 0.20 # kill switch: stop trading if equity falls this far from peak


def position_size(equity: float, price: float, cfg: RiskConfig) -> float:
    """Units to buy so that hitting the stop loses ~risk_per_trade of equity."""
    if price <= 0 or equity <= 0:
        return 0.0
    by_risk = equity * cfg.risk_per_trade / (price * cfg.stop_loss_pct)
    by_cap = equity * cfg.max_position_pct / price
    return min(by_risk, by_cap)


def exit_prices(entry: float, cfg: RiskConfig) -> tuple[float, float]:
    return entry * (1 - cfg.stop_loss_pct), entry * (1 + cfg.take_profit_pct)


class KillSwitch:
    def __init__(self, cfg: RiskConfig, equity: float):
        self.cfg, self.peak, self.tripped = cfg, equity, False

    def update(self, equity: float) -> bool:
        self.peak = max(self.peak, equity)
        if self.peak > 0 and (self.peak - equity) / self.peak >= self.cfg.max_drawdown_pct:
            self.tripped = True
        return self.tripped
