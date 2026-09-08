import streamlit as st
import plotly.graph_objects as go
from market_data import snapshot
from analyst import analyze

st.set_page_config(page_title="AlphaPilot AI", page_icon="🚀", layout="wide")
st.title("🚀 AlphaPilot AI")
st.caption("Turn Binance market data into explainable crypto intelligence.")

with st.sidebar:
    st.header("Market Scanner")
    symbol = st.text_input("Symbol", "SOLUSDT").upper().strip()
    st.caption("Read-only market intelligence. No trades are placed.")

if st.button("🔎 Analyze Market", type="primary", use_container_width=True):
    with st.spinner("Retrieving live Binance market data..."):
        try:
            data = snapshot(symbol)
            result = analyze(data)
            st.session_state["alpha_data"] = data
            st.session_state["alpha_result"] = result
        except Exception as e:
            st.error(f"Unable to retrieve market data: {e}")

if "alpha_data" not in st.session_state:
    st.info("Enter a Binance symbol and tap Analyze Market.")
    st.markdown("### 🤖 Binance Agent OS / MCP")
    st.write("AlphaPilot uses live public Binance market data for the dashboard. "
             "For the Agent OS demonstration, use the connected Binance MCP agent in ChatGPT.")
    st.stop()

data = st.session_state["alpha_data"]
result = st.session_state["alpha_result"]

st.success("🟢 Live Binance market data")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Price", f"${data['price']:,.4f}", f"{data['change_pct']:.2f}%")
c2.metric("24h Volume", f"${data['quote_volume']/1e6:,.1f}M")
c3.metric("Volume Ratio", f"{data['volume_ratio']:.2f}x")
c4.metric("Alpha Score", f"{result['score']}/100", result["regime"])

st.markdown("---")
left, right = st.columns([2, 1])

with left:
    st.subheader("📈 Price & Activity")
    fig = go.Figure(go.Candlestick(
        x=data["times"], open=data["opens"], high=data["highs"],
        low=data["lows"], close=data["closes"], name=symbol
    ))
    fig.update_layout(height=430, margin=dict(l=10, r=10, t=10, b=10),
                      xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("🎯 Signal Matrix")
    st.metric("Momentum", result["momentum_label"])
    st.metric("Volume Activity", result["volume_label"])
    st.metric("Order-book Pressure", result["pressure_label"])
    st.metric("Risk", result["risk_label"])

st.markdown("---")
a, b = st.columns(2)
with a:
    st.subheader("🧠 Why this score?")
    st.write(result["explanation"])
    st.subheader("⚠️ Key Risks")
    for risk in result["risks"]:
        st.write(f"• {risk}")

with b:
    st.subheader("🤖 AI Risk Brief")
    st.write(result["risk_brief"])
    st.subheader("🚨 Invalidation Scenarios")
    for item in result["invalidations"]:
        st.write(f"• {item}")

st.markdown("---")
st.subheader("🤖 Binance Agent OS / MCP Demonstration")
st.info(
    "AlphaPilot's Streamlit dashboard uses public Binance market data. "
    "The connected Binance MCP agent is demonstrated separately in ChatGPT. "
    "The app does not claim an authenticated MCP session."
)
st.code("""Use the Binance MCP Server to analyze SOLUSDT.

Give me:
- Current price
- 24h change
- 24h volume
- Momentum
- Order-book pressure
- Volume activity
- Key risks
- Overall market regime

Use Binance MCP market data only.
Do not place any trades.""", language="text")
