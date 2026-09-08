def clamp(x):
    return max(0, min(100, float(x)))


def pct_return(close, p):
    if len(close) <= p:
        return 0.0

    return (
        close.iloc[-1] / close.iloc[-1 - p] - 1
    ) * 100


def compute(snap):

    ticker = snap["ticker"]
    klines = snap["klines"]
    order_book = snap["order_book"]

    # -----------------------------------------------------
    # PRICE DATA
    # -----------------------------------------------------

    close = klines["close"]

    # Binance kline data may expose either:
    #
    # quote_volume
    #
    # or:
    #
    # volume
    #
    # Prefer quote_volume because it represents quote-asset
    # traded value, but gracefully fall back to base volume.

    if "quote_volume" in klines.columns:
        volume = klines["quote_volume"]

    elif "volume" in klines.columns:
        volume = klines["volume"]

    else:
        raise ValueError(
            "Kline data contains neither 'quote_volume' nor 'volume'. "
            f"Available columns: {list(klines.columns)}"
        )

    # -----------------------------------------------------
    # 24H CHANGE
    # -----------------------------------------------------

    change = float(
        ticker.get("priceChangePercent", 0)
    )

    # -----------------------------------------------------
    # MOMENTUM
    # -----------------------------------------------------

    mom6 = pct_return(
        close,
        6,
    )

    mom24 = pct_return(
        close,
        min(24, len(close) - 1),
    )

    # -----------------------------------------------------
    # VOLUME
    # -----------------------------------------------------

    if len(volume) > 25:

        baseline = volume.iloc[-25:-1].mean()

    else:

        baseline = volume.mean()

    if baseline:

        vr = float(
            volume.iloc[-1] / baseline
        )

    else:

        vr = 1.0

    # -----------------------------------------------------
    # VOLATILITY
    # -----------------------------------------------------

    ret = (
        close.pct_change()
        .dropna()
        * 100
    )

    if len(ret) > 1:

        vol = float(
            ret.tail(24).std()
        )

    else:

        vol = 0.0

    # -----------------------------------------------------
    # CURRENT PRICE
    # -----------------------------------------------------

    last = float(
        close.iloc[-1]
    )

    # -----------------------------------------------------
    # 24H RANGE
    # -----------------------------------------------------

    range_high = float(
        klines["high"]
        .tail(24)
        .max()
    )

    range_low = float(
        klines["low"]
        .tail(24)
        .min()
    )

    rng = (
        (range_high - range_low)
        / last
        * 100
    )

    # -----------------------------------------------------
    # ORDER BOOK
    # -----------------------------------------------------

    bids = sum(
        float(x[1])
        for x in order_book.get("bids", [])
    )

    asks = sum(
        float(x[1])
        for x in order_book.get("asks", [])
    )

    if bids + asks:

        imb = (
            (bids - asks)
            / (bids + asks)
            * 100
        )

    else:

        imb = 0.0

    # -----------------------------------------------------
    # SIGNAL SCORES
    # -----------------------------------------------------

    momentum = clamp(
        50
        + mom6 * 7
        + mom24 * 2
        + change * 1.5
    )

    volume_score = clamp(
        50
        + (vr - 1) * 30
    )

    liquidity = clamp(
        50
        + imb * 2
    )

    sentiment = clamp(
        50
        + change * 2
        + (vr - 1) * 10
    )

    risk = clamp(
        35
        + vol * 12
        + rng * 1.2
    )

    # -----------------------------------------------------
    # ALPHA SCORE
    # -----------------------------------------------------

    alpha = (
        0.30 * momentum
        + 0.20 * volume_score
        + 0.20 * sentiment
        + 0.15 * liquidity
        + 0.15 * (100 - risk)
    )

    # -----------------------------------------------------
    # MARKET REGIME
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # RETURN
    # -----------------------------------------------------

    return {
        "alpha_score": round(alpha),
        "regime": regime,

        "momentum": round(momentum),
        "volume": round(volume_score),
        "liquidity": round(liquidity),
        "sentiment": round(sentiment),
        "risk": round(risk),

        "price": last,
        "change": change,
        "volume_ratio": vr,
        "range24": rng,
        "imbalance": imb,
    }
