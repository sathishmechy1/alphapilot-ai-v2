def clamp(x):
    return max(0, min(100, float(x)))


def pct_return(close, periods):
    if len(close) <= periods:
        return 0.0

    start = float(close.iloc[-1 - periods])
    end = float(close.iloc[-1])

    if start == 0:
        return 0.0

    return (end / start - 1) * 100


def compute(snap):
    ticker = snap["ticker"]
    candles = snap["klines"]
    order_book = snap["order_book"]

    close = candles["close"]

    if "quote_volume" in candles.columns:
        volume = candles["quote_volume"]
    else:
        volume = candles["volume"]

    change = float(
        ticker.get("priceChangePercent", 0) or 0
    )

    mom6 = pct_return(close, 6)

    mom24 = pct_return(
        close,
        min(24, max(1, len(close) - 1)),
    )

    if len(volume) > 25:
        baseline = volume.iloc[-25:-1].mean()
    else:
        baseline = volume.mean()

    if baseline and baseline > 0:
        volume_ratio = float(
            volume.iloc[-1] / baseline
        )
    else:
        volume_ratio = 1.0

    returns = close.pct_change().dropna() * 100

    volatility = (
        float(returns.tail(24).std())
        if len(returns) > 1
        else 0.0
    )

    last_price = float(close.iloc[-1])

    high24 = float(candles["high"].tail(24).max())
    low24 = float(candles["low"].tail(24).min())

    range24 = (
        (high24 - low24) / last_price * 100
        if last_price
        else 0
    )

    bids = sum(
        float(level[1])
        for level in order_book.get("bids", [])
    )

    asks = sum(
        float(level[1])
        for level in order_book.get("asks", [])
    )

    total_book = bids + asks

    imbalance = (
        (bids - asks) / total_book * 100
        if total_book
        else 0
    )

    momentum = clamp(
        50
        + mom6 * 7
        + mom24 * 2
        + change * 1.5
    )

    volume_score = clamp(
        50 + (volume_ratio - 1) * 30
    )

    liquidity = clamp(
        50 + imbalance * 2
    )

    sentiment = clamp(
        50
        + change * 2
        + (volume_ratio - 1) * 10
    )

    risk = clamp(
        35
        + volatility * 12
        + range24 * 1.2
    )

    alpha = (
        0.30 * momentum
        + 0.20 * volume_score
        + 0.20 * sentiment
        + 0.15 * liquidity
        + 0.15 * (100 - risk)
    )

    if alpha >= 75:
        regime = "Bullish"
    elif alpha >= 60:
        regime = "Constructive"
    elif alpha >= 45:
        regime = "Neutral"
    elif alpha >= 30:
        regime = "Cautious"
    else:
        regime = "Bearish"

    return {
        "alpha_score": round(alpha),
        "regime": regime,
        "momentum": round(momentum),
        "volume": round(volume_score),
        "liquidity": round(liquidity),
        "sentiment": round(sentiment),
        "risk": round(risk),
        "price": last_price,
        "change": change,
        "volume_ratio": volume_ratio,
        "range24": range24,
        "imbalance": imbalance,
    }
