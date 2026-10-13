"""Candle sources: CSV, synthetic (for tests/demos), and live via ccxt."""
from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Candle:
    ts: int  # unix ms
    open: float
    high: float
    low: float
    close: float
    volume: float


def load_csv(path: str) -> list[Candle]:
    """CSV columns: timestamp,open,high,low,close,volume (header row required)."""
    with open(path, newline="") as f:
        return [
            Candle(int(float(r["timestamp"])), float(r["open"]), float(r["high"]),
                   float(r["low"]), float(r["close"]), float(r["volume"]))
            for r in csv.DictReader(f)
        ]


def synthetic(n: int = 1500, seed: int = 7, start: float = 30000.0) -> list[Candle]:
    """Random walk with regime drift and a cycle, so trend strategies have something to find."""
    rng = random.Random(seed)
    price, out = start, []
    for i in range(n):
        drift = 0.0006 * math.sin(i / 120)
        o = price
        price = max(1.0, price * (1 + drift + rng.gauss(0, 0.008)))
        hi = max(o, price) * (1 + abs(rng.gauss(0, 0.002)))
        lo = min(o, price) * (1 - abs(rng.gauss(0, 0.002)))
        out.append(Candle(i * 3_600_000, o, hi, lo, price, rng.uniform(10, 100)))
    return out


def fetch_live(exchange, symbol: str, timeframe: str, limit: int = 300) -> list[Candle]:
    return [Candle(*row[:6]) for row in exchange.fetch_ohlcv(symbol, timeframe, limit=limit)]
