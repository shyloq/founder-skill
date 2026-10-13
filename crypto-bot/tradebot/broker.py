"""Brokers: PaperBroker (simulated, with fees/slippage) and CcxtBroker (real orders)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Trade:
    side: str
    price: float
    qty: float
    fee: float
    reason: str = ""


@dataclass
class PaperBroker:
    cash: float = 10_000.0
    fee_rate: float = 0.001   # 0.1% per fill
    slippage: float = 0.0005  # adverse price move per fill
    qty: float = 0.0
    trades: list[Trade] = field(default_factory=list)

    def equity(self, price: float) -> float:
        return self.cash + self.qty * price

    def buy(self, price: float, qty: float, reason: str = "") -> Trade | None:
        fill = price * (1 + self.slippage)
        qty = min(qty, self.cash / (fill * (1 + self.fee_rate)))
        if qty <= 0:
            return None
        fee = fill * qty * self.fee_rate
        self.cash -= fill * qty + fee
        self.qty += qty
        t = Trade("buy", fill, qty, fee, reason)
        self.trades.append(t)
        return t

    def sell_all(self, price: float, reason: str = "") -> Trade | None:
        if self.qty <= 0:
            return None
        fill = price * (1 - self.slippage)
        fee = fill * self.qty * self.fee_rate
        self.cash += fill * self.qty - fee
        t = Trade("sell", fill, self.qty, fee, reason)
        self.qty = 0.0
        self.trades.append(t)
        return t


class CcxtBroker:
    """Real market orders via ccxt. Only constructed when --live is passed."""

    def __init__(self, exchange, symbol: str):
        self.ex, self.symbol = exchange, symbol
        self.base, self.quote = symbol.split("/")

    def _bal(self, cur: str) -> float:
        return float(self.ex.fetch_balance().get("free", {}).get(cur, 0.0) or 0.0)

    @property
    def qty(self) -> float:
        return self._bal(self.base)

    def equity(self, price: float) -> float:
        return self._bal(self.quote) + self.qty * price

    def buy(self, price: float, qty: float, reason: str = ""):
        qty = float(self.ex.amount_to_precision(self.symbol, qty))
        o = self.ex.create_market_buy_order(self.symbol, qty)
        return Trade("buy", float(o.get("average") or price), qty, 0.0, reason)

    def sell_all(self, price: float, reason: str = ""):
        qty = float(self.ex.amount_to_precision(self.symbol, self.qty))
        if qty <= 0:
            return None
        o = self.ex.create_market_sell_order(self.symbol, qty)
        return Trade("sell", float(o.get("average") or price), qty, 0.0, reason)
