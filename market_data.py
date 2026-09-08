import requests
import pandas as pd

BASE = "https://api.binance.com"

def _get(path, params=None):
    r = requests.get(BASE + path, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def ticker(symbol):
    return _get("/api/v3/ticker/24hr", {"symbol": symbol.upper()})

def klines(symbol, interval="1h", limit=48):
    raw = _get("/api/v3/klines", {"symbol": symbol.upper(), "interval": interval, "limit": limit})
    cols = ["open_time","open","high","low","close","volume","close_time","quote_volume",
            "trades","taker_buy_base","taker_buy_quote","ignore"]
    df = pd.DataFrame(raw, columns=cols)
    for c in ["open","high","low","close","volume","quote_volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def order_book(symbol, limit=50):
    return _get("/api/v3/depth", {"symbol": symbol.upper(), "limit": limit})

def snapshot(symbol):
    return {"ticker": ticker(symbol), "klines": klines(symbol), "order_book": order_book(symbol)}
