"""Trend-following strategy: fast/slow EMA crossover with an RSI overbought filter."""
from __future__ import annotations

from dataclasses import dataclass


def ema(values: list[float], period: int) -> list[float]:
    k, out = 2 / (period + 1), []
    for v in values:
        out.append(v if not out else v * k + out[-1] * (1 - k))
    return out


def rsi(values: list[float], period: int = 14) -> list[float]:
    """Wilder's RSI. First `period` entries are 50.0 (not enough data)."""
    out = [50.0] * len(values)
    if len(values) <= period:
        return out
    gains = losses = 0.0
    for i in range(1, period + 1):
        d = values[i] - values[i - 1]
        gains += max(d, 0)
        losses += max(-d, 0)
    avg_g, avg_l = gains / period, losses / period
    for i in range(period, len(values)):
        if i > period:
            d = values[i] - values[i - 1]
            avg_g = (avg_g * (period - 1) + max(d, 0)) / period
            avg_l = (avg_l * (period - 1) + max(-d, 0)) / period
        out[i] = 100.0 if avg_l == 0 else 100 - 100 / (1 + avg_g / avg_l)
    return out


@dataclass
class EmaRsiStrategy:
    fast: int = 12
    slow: int = 26
    rsi_period: int = 14
    rsi_max: float = 70.0  # don't open longs when overbought

    @property
    def warmup(self) -> int:
        return max(self.slow, self.rsi_period) + 2

    def signal(self, closes: list[float]) -> str:
        """Return 'buy' (enter/hold long), 'sell' (exit), or 'hold'. Uses only the data given."""
        if len(closes) < self.warmup:
            return "hold"
        f, s = ema(closes, self.fast), ema(closes, self.slow)
        crossed_up = f[-2] <= s[-2] and f[-1] > s[-1]
        crossed_down = f[-2] >= s[-2] and f[-1] < s[-1]
        if crossed_up and rsi(closes, self.rsi_period)[-1] < self.rsi_max:
            return "buy"
        if crossed_down:
            return "sell"
        return "hold"
