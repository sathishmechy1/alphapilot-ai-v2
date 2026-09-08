import requests
import pandas as pd


BASE = "https://data-api.binance.vision"


class MarketDataError(RuntimeError):
    pass


def _get(path, params=None):
    try:
        response = requests.get(
            BASE + path,
            params=params,
            timeout=15,
            headers={
                "User-Agent": "AlphaPilot-Copilot/1.0",
                "Accept": "application/json",
            },
        )
    except requests.RequestException as exc:
        raise MarketDataError(f"Binance connection failed: {exc}") from exc

    if response.status_code == 403:
        raise MarketDataError(
            "Binance public market-data request was blocked with HTTP 403."
        )

    if not response.ok:
        raise MarketDataError(
            f"Binance REST HTTP {response.status_code}: "
            f"{response.text[:300]}"
        )

    try:
        return response.json()
    except Exception as exc:
        raise MarketDataError("Binance returned invalid JSON.") from exc


def _ticker(symbol):
    data = _get(
        "/api/v3/ticker/24hr",
        {"symbol": symbol.upper()},
    )

    if not isinstance(data, dict):
        raise MarketDataError("Invalid ticker response.")

    return data


def _klines(symbol):
    raw = _get(
        "/api/v3/klines",
        {
            "symbol": symbol.upper(),
            "interval": "1h",
            "limit": 48,
        },
    )

    if not isinstance(raw, list) or not raw:
        raise MarketDataError("Invalid candle response.")

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

    df = pd.DataFrame(raw, columns=columns)

    df["open_time"] = pd.to_datetime(
        df["open_time"],
        unit="ms",
    )

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(
        subset=["open", "high", "low", "close", "volume"]
    ).reset_index(drop=True)

    if df.empty:
        raise MarketDataError("No usable candle data returned.")

    return df


def _order_book(symbol):
    data = _get(
        "/api/v3/depth",
        {
            "symbol": symbol.upper(),
            "limit": 50,
        },
    )

    if not isinstance(data, dict):
        raise MarketDataError("Invalid order-book response.")

    if "bids" not in data or "asks" not in data:
        raise MarketDataError(
            "Order-book response is missing bids/asks."
        )

    return data


def snapshot(symbol):
    symbol = symbol.upper().strip()

    if not symbol:
        raise MarketDataError("Symbol is empty.")

    ticker = _ticker(symbol)
    candles = _klines(symbol)
    order_book = _order_book(symbol)

    return {
        "ticker": ticker,
        "klines": candles,
        "order_book": order_book,
        "source": "Binance Public Market Data",
        "mcp_tools": {},
        "mcp_error": None,
        }
