import requests

BASE = "https://data-api.binance.vision"

def _get(path, params):
    r = requests.get(BASE + path, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def snapshot(symbol):
    ticker = _get("/api/v3/ticker/24hr", {"symbol": symbol})
    depth = _get("/api/v3/depth", {"symbol": symbol, "limit": 20})
    klines = _get("/api/v3/klines", {"symbol": symbol, "interval": "15m", "limit": 80})

    closes = [float(x[4]) for x in klines]
    opens = [float(x[1]) for x in klines]
    highs = [float(x[2]) for x in klines]
    lows = [float(x[3]) for x in klines]
    volumes = [float(x[5]) for x in klines]
    times = [x[0] for x in klines]

    bid_value = sum(float(p) * float(q) for p, q in depth["bids"])
    ask_value = sum(float(p) * float(q) for p, q in depth["asks"])
    pressure = bid_value / ask_value if ask_value else 1.0

    recent = sum(volumes[-10:]) / 10
    prior = sum(volumes[-30:-10]) / 20
    volume_ratio = recent / prior if prior else 1.0

    return {
        "symbol": symbol, "price": float(ticker["lastPrice"]),
        "change_pct": float(ticker["priceChangePercent"]),
        "quote_volume": float(ticker["quoteVolume"]), "pressure": pressure,
        "volume_ratio": volume_ratio, "closes": closes, "opens": opens,
        "highs": highs, "lows": lows, "times": times,
    }
