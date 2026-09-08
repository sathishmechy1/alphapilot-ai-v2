import requests
import pandas as pd
from mcp_bridge import snapshot_via_mcp, MCPError, MCPAuthError

BASE = "https://data-api.binance.vision"

def _get(path, params=None):
    r = requests.get(BASE + path, params=params, timeout=10)
    if not r.ok:
        raise RuntimeError(f"Binance REST HTTP {r.status_code}: {r.text[:250]}")
    return r.json()

def _rest_snapshot(symbol):
    ticker = _get("/api/v3/ticker/24hr", {"symbol": symbol.upper()})
    raw = _get("/api/v3/klines", {"symbol": symbol.upper(), "interval": "1h", "limit": 48})
    cols = ["open_time","open","high","low","close","volume","close_time",
            "quote_volume","trades","taker_buy_base","taker_buy_quote","ignore"]
    df = pd.DataFrame(raw, columns=cols)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    for c in ["open","high","low","close","volume","quote_volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    book = _get("/api/v3/depth", {"symbol": symbol.upper(), "limit": 50})
    return {"ticker": ticker, "klines": df, "order_book": book,
            "source": "Binance public REST fallback",
            "mcp_tools": {}}

def snapshot(symbol):
    # MCP is the primary path. REST fallback keeps the public demo usable
    # when the remote MCP endpoint can't be used.
    #
    # Note on mcp_status: Binance's Agentic MCP server requires a valid,
    # per-account authorization for every call, including read-only ones
    # (see Binance's own docs for agent.binance.com/mcp/agentic). This
    # public, no-login demo has no such session, so an auth_required
    # (HTTP 401/403) outcome here is an expected, structural condition,
    # not a transient outage. Other failures (network errors, unexpected
    # response shapes, etc.) are tagged "unavailable" and may genuinely
    # be transient.
    try:
        raw = snapshot_via_mcp(symbol)
        ticker = raw["ticker"]
        book = raw["order_book"]
        candles = raw["klines"]

        # Normalize common MCP text/JSON shapes into the same internal format.
        if isinstance(ticker, list) and ticker:
            ticker = ticker[0]
        if isinstance(candles, dict):
            candles = candles.get("data") or candles.get("klines") or candles.get("candles") or candles
        if isinstance(book, dict):
            book = book.get("data") or book

        if not isinstance(ticker, dict) or not isinstance(book, dict):
            raise MCPError("MCP returned an unsupported market-data shape")

        if isinstance(candles, dict):
            raise MCPError("MCP candle tool returned an unsupported shape")

        # Binance-style kline arrays -> DataFrame
        if isinstance(candles, list):
            cols = ["open_time","open","high","low","close","volume","close_time",
                    "quote_volume","trades","taker_buy_base","taker_buy_quote","ignore"]
            df = pd.DataFrame(candles, columns=cols[:len(candles[0])] if candles else cols)
            if not df.empty and "open_time" in df:
                df["open_time"] = pd.to_datetime(pd.to_numeric(df["open_time"]), unit="ms")
            for c in ["open","high","low","close","volume","quote_volume"]:
                if c in df:
                    df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            raise MCPError("MCP candles were not returned as a list")

        return {"ticker": ticker, "klines": df, "order_book": book,
                "source": "Binance Agent OS MCP",
                "mcp_tools": raw["mcp_tools"]}

    except MCPAuthError as exc:
        data = _rest_snapshot(symbol)
        data["mcp_error"] = str(exc)
        data["mcp_status"] = "auth_required"
        return data

    except Exception as exc:
        data = _rest_snapshot(symbol)
        data["mcp_error"] = str(exc)
        data["mcp_status"] = "unavailable"
        return data
