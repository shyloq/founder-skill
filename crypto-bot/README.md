# tradebot

A small, long-only crypto trading bot: EMA(12/26) crossover with an RSI filter, fixed-fraction
position sizing, stop-loss / take-profit, and a max-drawdown kill switch. The same `Engine`
drives backtests, paper trading and live trading.

```
python -m tradebot backtest                      # synthetic demo data
python -m tradebot backtest --csv btc_1h.csv     # CSV: timestamp,open,high,low,close,volume
pip install -r requirements.txt
python -m tradebot paper --symbol BTC/USDT --timeframe 1h   # live prices, simulated fills
EXCHANGE_API_KEY=... EXCHANGE_API_SECRET=... \
  python -m tradebot live --symbol BTC/USDT --i-understand-the-risk
python -m unittest discover -s tests
```

## Read before using real money
- The default strategy is a textbook example, **not a proven edge**. Backtest it on real data
  from several market regimes, then paper trade for weeks, before risking anything.
- Backtests ignore partial fills, outages and exchange rejections, and results on synthetic data mean nothing.
- Use API keys with **trading only, no withdrawal** permission, and IP-whitelist them.
- Start with an amount you can afford to lose entirely. Live mode places market orders.
- Position state lives in memory (stop/target are not persisted); a restart while holding a position loses them.
- Not financial advice.

## Layout
`strategy.py` signals · `risk.py` sizing, exits, kill switch · `broker.py` paper + ccxt ·
`engine.py` per-candle decision · `backtest.py` · `cli.py`
