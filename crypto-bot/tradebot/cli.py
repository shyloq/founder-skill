"""CLI: backtest | paper | live."""
from __future__ import annotations

import argparse
import logging
import os
import time

from .backtest import backtest
from .broker import CcxtBroker, PaperBroker
from .data import fetch_live, load_csv, synthetic
from .engine import Engine
from .risk import RiskConfig
from .strategy import EmaRsiStrategy

log = logging.getLogger("tradebot")
TF_SECONDS = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "1d": 86400}


def make_exchange(name: str, authed: bool):
    import ccxt  # optional dependency: pip install ccxt
    kw = {"enableRateLimit": True}
    if authed:
        kw |= {"apiKey": os.environ["EXCHANGE_API_KEY"], "secret": os.environ["EXCHANGE_API_SECRET"]}
    return getattr(ccxt, name)(kw)


def run_loop(args, broker, ex):
    strat, risk = EmaRsiStrategy(), RiskConfig()
    engine = Engine(strat, risk, broker, broker.equity(0) if isinstance(broker, PaperBroker) else 0)
    last_ts = None
    while True:
        try:
            candles = fetch_live(ex, args.symbol, args.timeframe)[:-1]  # drop the unfinished candle
            if candles and candles[-1].ts != last_ts:
                last_ts = candles[-1].ts
                action = engine.step(candles)
                px = candles[-1].close
                log.info("close=%.2f equity=%.2f pos=%.6f action=%s",
                         px, broker.equity(px), broker.qty, action or "-")
        except Exception:  # network/exchange errors must not kill the loop
            log.exception("step failed; retrying next poll")
        time.sleep(min(TF_SECONDS[args.timeframe] / 6, 60))


def main(argv=None):
    p = argparse.ArgumentParser(prog="tradebot")
    p.add_argument("mode", choices=["backtest", "paper", "live"])
    p.add_argument("--symbol", default="BTC/USDT")
    p.add_argument("--timeframe", default="1h", choices=TF_SECONDS)
    p.add_argument("--exchange", default="binance")
    p.add_argument("--csv", help="backtest on this CSV instead of synthetic/live data")
    p.add_argument("--cash", type=float, default=10_000.0)
    p.add_argument("--i-understand-the-risk", action="store_true",
                   help="required for live mode; real money can be lost")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    if args.mode == "backtest":
        if args.csv:
            candles = load_csv(args.csv)
        else:
            log.info("no --csv given: using synthetic data (demo only, proves nothing about real markets)")
            candles = synthetic()
        print(backtest(candles, cash=args.cash).summary())
    elif args.mode == "paper":
        run_loop(args, PaperBroker(cash=args.cash), make_exchange(args.exchange, authed=False))
    else:
        if not args.i_understand_the_risk:
            p.error("live mode requires --i-understand-the-risk")
        ex = make_exchange(args.exchange, authed=True)
        run_loop(args, CcxtBroker(ex, args.symbol), ex)


if __name__ == "__main__":
    main()
