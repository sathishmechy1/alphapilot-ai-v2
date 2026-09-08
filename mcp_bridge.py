import json
import requests

MCP_URL = "https://agent.binance.com/mcp/agentic"
PROTOCOL_VERSION = "2025-06-18"

class MCPError(RuntimeError):
    pass

def _parse_response(response):
    content_type = response.headers.get("content-type", "")
    if response.status_code >= 400:
        raise MCPError(f"Binance MCP HTTP {response.status_code}: {response.text[:300]}")

    if "text/event-stream" in content_type:
        events = []
        for block in response.text.split("\n\n"):
            data_lines = [line[5:].strip() for line in block.splitlines() if line.startswith("data:")]
            if data_lines:
                try:
                    events.append(json.loads("\n".join(data_lines)))
                except json.JSONDecodeError:
                    pass
        if not events:
            raise MCPError("Binance MCP returned an empty event stream")
        for event in reversed(events):
            if "result" in event or "error" in event:
                return event
        return events[-1]

    try:
        return response.json()
    except Exception as exc:
        raise MCPError(f"Unexpected Binance MCP response: {response.text[:300]}") from exc

def _post(payload, session_id=None):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id

    r = requests.post(MCP_URL, headers=headers, json=payload, timeout=20)
    result = _parse_response(r)
    if "error" in result:
        raise MCPError(str(result["error"]))
    return result, r.headers.get("Mcp-Session-Id") or session_id

def _initialize():
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "AlphaPilot AI", "version": "4.0.0"},
        },
    }
    result, session_id = _post(payload)
    if "result" not in result:
        raise MCPError("Binance MCP initialization failed")
    return session_id

def _notify_initialized(session_id):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Mcp-Session-Id": session_id,
    }
    payload = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {},
    }
    requests.post(MCP_URL, headers=headers, json=payload, timeout=10)

def list_tools():
    sid = _initialize()
    _notify_initialized(sid)
    result, _ = _post(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        sid,
    )
    return result.get("result", {}).get("tools", [])

def _schema(tool):
    return tool.get("inputSchema", {}) or {}

def _make_args(tool, symbol, preferred_limit=None):
    props = _schema(tool).get("properties", {}) or {}
    args = {}
    for key, spec in props.items():
        k = key.lower()
        if k in ("symbol", "symbols", "pair", "trading_pair"):
            if k == "symbols":
                args[key] = [symbol]
            else:
                args[key] = symbol
        elif k in ("interval", "timeframe", "window"):
            args[key] = "1h"
        elif k in ("limit", "depth", "levels", "size"):
            args[key] = preferred_limit or 50
        elif k in ("type",):
            # Leave optional enum parameters alone unless required.
            if "default" in spec:
                args[key] = spec["default"]
    return args

def _call_tool(tool, symbol, preferred_limit=None, request_id=10):
    sid = _initialize()
    _notify_initialized(sid)
    args = _make_args(tool, symbol, preferred_limit)
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {"name": tool["name"], "arguments": args},
    }
    result, _ = _post(payload, sid)
    return result.get("result", {})

def _tool_text(result):
    chunks = result.get("content", []) if isinstance(result, dict) else []
    text = []
    for item in chunks:
        if isinstance(item, dict) and item.get("type") == "text":
            text.append(item.get("text", ""))
    return "\n".join(text)

def _decode(text):
    try:
        return json.loads(text)
    except Exception:
        return text

def _pick(tools, groups):
    scored = []
    for tool in tools:
        hay = (tool.get("name", "") + " " + tool.get("description", "")).lower()
        score = sum(1 for term in groups if term in hay)
        if score:
            scored.append((score, tool))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored else None

def snapshot_via_mcp(symbol):
    symbol = symbol.upper()
    tools = list_tools()
    if not tools:
        raise MCPError("Binance MCP returned no tools")

    ticker_tool = _pick(tools, ["ticker", "24hr"])
    if ticker_tool is None:
        ticker_tool = _pick(tools, ["ticker"])

    book_tool = _pick(tools, ["order", "book"])
    if book_tool is None:
        book_tool = _pick(tools, ["depth"])

    candle_tool = _pick(tools, ["kline", "candlestick", "candle"])
    if candle_tool is None:
        candle_tool = _pick(tools, ["ohlcv"])

    if not ticker_tool or not book_tool or not candle_tool:
        names = [t.get("name", "") for t in tools]
        raise MCPError("Required market-data tools not found. Available: " + ", ".join(names[:30]))

    ticker_raw = _decode(_tool_text(_call_tool(ticker_tool, symbol, request_id=11)))
    book_raw = _decode(_tool_text(_call_tool(book_tool, symbol, preferred_limit=50, request_id=12)))
    candles_raw = _decode(_tool_text(_call_tool(candle_tool, symbol, preferred_limit=48, request_id=13)))

    return {
        "ticker": ticker_raw,
        "order_book": book_raw,
        "klines": candles_raw,
        "mcp_tools": {
            "ticker": ticker_tool["name"],
            "order_book": book_tool["name"],
            "klines": candle_tool["name"],
        },
    }
