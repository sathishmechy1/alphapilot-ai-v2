import requests
import pandas as pd

from mcp_bridge import snapshot_via_mcp, MCPError


BASE = "https://data-api.binance.vision"


# =========================================================
# PUBLIC BINANCE REST
# =========================================================

def _get(path, params=None):
    response = requests.get(
        BASE + path,
        params=params,
        timeout=15,
    )

    if not response.ok:
        raise RuntimeError(
            f"Binance REST HTTP {response.status_code}: "
            f"{response.text[:250]}"
        )

    return response.json()


def _rest_snapshot(symbol):

    symbol = symbol.upper().strip()

    # -------------------------------
    # 24h ticker
    # -------------------------------

    ticker = _get(
        "/api/v3/ticker/24hr",
        {"symbol": symbol},
    )

    # -------------------------------
    # Candles
    # -------------------------------

    raw_klines = _get(
        "/api/v3/klines",
        {
            "symbol": symbol,
            "interval": "1h",
            "limit": 48,
        },
    )

    columns = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_volume",
        "trades",
        "taker_buy_base",
        "taker_buy_quote",
        "ignore",
    ]

    klines = pd.DataFrame(
        raw_klines,
        columns=columns,
    )

    if not klines.empty:

        klines["open_time"] = pd.to_datetime(
            klines["open_time"],
            unit="ms",
        )

        for column in [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "quote_volume",
        ]:

            klines[column] = pd.to_numeric(
                klines[column],
                errors="coerce",
            )

    # -------------------------------
    # Order book
    # -------------------------------

    order_book = _get(
        "/api/v3/depth",
        {
            "symbol": symbol,
            "limit": 50,
        },
    )

    return {
        "ticker": ticker,
        "klines": klines,
        "order_book": order_book,
        "source": "Binance public REST fallback",
        "mcp_tools": {},
    }


# =========================================================
# NORMALIZE MCP DATA
# =========================================================

def _unwrap(value):

    if isinstance(value, dict):

        for key in [
            "data",
            "result",
            "ticker",
            "order_book",
            "orderBook",
            "klines",
            "candles",
            "items",
        ]:

            if key in value:

                candidate = value[key]

                if candidate is not value:
                    return candidate

    return value


def _normalize_ticker(value):

    value = _unwrap(value)

    if isinstance(value, list):

        if len(value) == 0:
            raise MCPError(
                "MCP ticker response was empty"
            )

        value = value[0]

    if not isinstance(value, dict):

        raise MCPError(
            "MCP ticker response does not contain a dictionary"
        )

    # Some APIs use slightly different names.
    if "priceChangePercent" not in value:

        if "price_change_percent" in value:
            value["priceChangePercent"] = value[
                "price_change_percent"
            ]

        elif "changePercent" in value:
            value["priceChangePercent"] = value[
                "changePercent"
            ]

    return value


def _normalize_order_book(value):

    value = _unwrap(value)

    if not isinstance(value, dict):

        raise MCPError(
            "MCP order-book response is not a dictionary"
        )

    # Normalize common naming variants.

    if "bids" not in value:

        for key in [
            "bid",
            "buyOrders",
            "buy_orders",
        ]:

            if key in value:
                value["bids"] = value[key]
                break

    if "asks" not in value:

        for key in [
            "ask",
            "sellOrders",
            "sell_orders",
        ]:

            if key in value:
                value["asks"] = value[key]
                break

    if "bids" not in value:
        value["bids"] = []

    if "asks" not in value:
        value["asks"] = []

    return value


def _normalize_klines(value):

    value = _unwrap(value)

    if isinstance(value, dict):

        for key in [
            "data",
            "klines",
            "candles",
            "items",
        ]:

            if key in value:

                value = value[key]
                break

    if not isinstance(value, list):

        raise MCPError(
            "MCP candle response is not a list"
        )

    if len(value) == 0:

        raise MCPError(
            "MCP candle response was empty"
        )

    # -----------------------------------------------------
    # Binance-style arrays
    # -----------------------------------------------------

    if isinstance(value[0], (list, tuple)):

        columns = [
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_volume",
            "trades",
            "taker_buy_base",
            "taker_buy_quote",
            "ignore",
        ]

        width = len(value[0])

        df = pd.DataFrame(
            value,
            columns=columns[:width],
        )

    # -----------------------------------------------------
    # Dictionary candle objects
    # -----------------------------------------------------

    elif isinstance(value[0], dict):

        df = pd.DataFrame(value)

        rename_map = {
            "openTime": "open_time",
            "open_time": "open_time",
            "openPrice": "open",
            "open_price": "open",
            "highPrice": "high",
            "high_price": "high",
            "lowPrice": "low",
            "low_price": "low",
            "closePrice": "close",
            "close_price": "close",
            "volume": "volume",
            "quoteVolume": "quote_volume",
            "quote_volume": "quote_volume",
            "closeTime": "close_time",
        }

        df = df.rename(
            columns=rename_map
        )

    else:

        raise MCPError(
            "Unsupported MCP candle format"
        )

    # -----------------------------------------------------
    # Normalize numeric columns
    # -----------------------------------------------------

    if "open_time" in df.columns:

        numeric_time = pd.to_numeric(
            df["open_time"],
            errors="coerce",
        )

        df["open_time"] = pd.to_datetime(
            numeric_time,
            unit="ms",
            errors="coerce",
        )

    for column in [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
    ]:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    # -----------------------------------------------------
    # scoring.py needs quote_volume OR volume
    # -----------------------------------------------------

    if (
        "quote_volume" not in df.columns
        and "volume" not in df.columns
    ):

        raise MCPError(
            "MCP candles contain no volume field"
        )

    if "quote_volume" not in df.columns:

        df["quote_volume"] = df["volume"]

    return df


# =========================================================
# MAIN SNAPSHOT
# =========================================================

def snapshot(symbol):

    symbol = symbol.upper().strip()

    mcp_error = None

    # =====================================================
    # TRY BINANCE AGENTIC MCP FIRST
    # =====================================================

    try:

        raw = snapshot_via_mcp(symbol)

        if not isinstance(raw, dict):

            raise MCPError(
                "MCP returned an unexpected top-level response"
            )

        # ---------------------------------------------
        # Find ticker
        # ---------------------------------------------

        ticker_raw = raw.get("ticker")

        if ticker_raw is None:

            for key in [
                "price",
                "ticker_data",
                "tickerData",
                "market",
            ]:

                if key in raw:
                    ticker_raw = raw[key]
                    break

        if ticker_raw is None:

            raise MCPError(
                "MCP response does not contain ticker data"
            )

        # ---------------------------------------------
        # Find order book
        # ---------------------------------------------

        book_raw = raw.get("order_book")

        if book_raw is None:

            for key in [
                "orderBook",
                "orderbook",
                "depth",
                "book",
            ]:

                if key in raw:
                    book_raw = raw[key]
                    break

        if book_raw is None:

            raise MCPError(
                "MCP response does not contain order-book data"
            )

        # ---------------------------------------------
        # Find candles
        # ---------------------------------------------

        candles_raw = raw.get("klines")

        if candles_raw is None:

            for key in [
                "candles",
                "kline",
                "ohlcv",
                "price_history",
            ]:

                if key in raw:
                    candles_raw = raw[key]
                    break

        if candles_raw is None:

            raise MCPError(
                "MCP response does not contain candle data"
            )

        # ---------------------------------------------
        # Normalize
        # ---------------------------------------------

        ticker = _normalize_ticker(
            ticker_raw
        )

        order_book = _normalize_order_book(
            book_raw
        )

        klines = _normalize_klines(
            candles_raw
        )

        # ---------------------------------------------
        # Final schema validation
        # ---------------------------------------------

        if not isinstance(ticker, dict):
            raise MCPError("Invalid ticker")

        if not isinstance(order_book, dict):
            raise MCPError("Invalid order book")

        if klines.empty:
            raise MCPError("No candle data")

        required = [
            "open",
            "high",
            "low",
            "close",
        ]

        missing = [
            column
            for column in required
            if column not in klines.columns
        ]

        if missing:

            raise MCPError(
                "MCP candle data missing: "
                + ", ".join(missing)
            )

        return {
            "ticker": ticker,
            "klines": klines,
            "order_book": order_book,
            "source": "Binance Agent OS MCP",
            "mcp_tools": raw.get(
                "mcp_tools",
                {},
            ),
        }

    except Exception as exc:

        mcp_error = str(exc)

    # =====================================================
    # PUBLIC REST FALLBACK
    # =====================================================

    try:

        data = _rest_snapshot(
            symbol
        )

        data["mcp_error"] = mcp_error

        return data

    except Exception as rest_exc:

        raise RuntimeError(
            f"MCP failed: {mcp_error}; "
            f"REST fallback failed: {rest_exc}"
        )
