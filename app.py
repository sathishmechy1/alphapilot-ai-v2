import streamlit as st
import plotly.graph_objects as go
from market_data import snapshot
from analyst import analyze

st.set_page_config(page_title="AlphaPilot AI", page_icon="🚀", layout="wide")
st.markdown("""<style>
.stApp{background:radial-gradient(circle at 15% 0%,#17130a 0%,#0b0e11 34%);color:#f5f5f5}
.block-container{max-width:1180px;padding-top:2rem}
.hero,.card{border-radius:20px;background:#11151a;border:1px solid #292e35}
.hero{padding:28px 30px;margin-bottom:22px;border-color:#5a481f}
.hero h1{font-size:2.7rem}.hero p{font-size:1.12rem;color:#c8cbd0}
.badge{display:inline-block;margin-top:10px;padding:5px 10px;border-radius:999px;background:#211d12;border:1px solid #5a481f;color:#f3ba2f}
.card{padding:20px;height:100%}.score{font-size:62px;line-height:1;font-weight:850;color:#f3ba2f}
.small{color:#8f969f;font-size:.8rem;text-transform:uppercase;letter-spacing:.08em}
.signal{padding:10px 12px;border-radius:10px;background:#171b20;border:1px solid #252a30;margin:7px 0}
.footer{text-align:center;color:#6f767f;font-size:.78rem;padding:28px 0 8px}
</style>""",unsafe_allow_html=True)

st.markdown("""<div class="hero"><h1>🚀 AlphaPilot AI</h1>
<p>Turn Binance market data into explainable crypto intelligence.</p>
<span class="badge">BINANCE AGENT OS • MCP-FIRST • READ-ONLY</span></div>""",unsafe_allow_html=True)

symbol=st.text_input("Enter a Binance symbol","SOLUSDT").upper().strip()
c1,c2=st.columns([1,5])
with c1: go_btn=st.button("⚡ Analyze",type="primary",use_container_width=True)
with c2: st.caption("Try: SOLUSDT · BTCUSDT · ETHUSDT · BNBUSDT")

if go_btn:
    try:
        with st.spinner(f"Querying Binance Agent OS for {symbol}..."):
            snap=snapshot(symbol); report=analyze(symbol,snap)
        m=report["metrics"]; k=snap["klines"]

        if snap.get("source") == "Binance Agent OS MCP":
            st.success("🔌 Binance Agent OS MCP connected — market data retrieved through MCP.")
            with st.expander("MCP tools used"):
                st.json(snap.get("mcp_tools", {}))
        else:
            st.warning("⚠️ Binance MCP was temporarily unavailable. Using public Binance market-data fallback.")
            if snap.get("mcp_error"):
                st.caption(snap["mcp_error"])

        st.divider()
        a,b,c=st.columns([1.15,1,1])
        with a:
            st.markdown('<div class="card">',unsafe_allow_html=True)
            st.markdown('<div class="small">Alpha Score</div>',unsafe_allow_html=True)
            st.markdown(f'<div class="score">{m["alpha_score"]}<span style="font-size:24px;color:#777">/100</span></div>',unsafe_allow_html=True)
            icon="🟢" if m["alpha_score"]>=60 else "🟡" if m["alpha_score"]>=45 else "🔴"
            st.subheader(f"{icon} {m['regime']}"); st.write(report["summary"])
            st.markdown('</div>',unsafe_allow_html=True)
        with b:
            st.markdown('<div class="card">',unsafe_allow_html=True)
            st.markdown('<div class="small">Market Snapshot</div>',unsafe_allow_html=True)
            st.metric("Price",f'{m["price"]:,.4f}'); st.metric("24h Change",f'{m["change"]:.2f}%'); st.metric("Volume Ratio",f'{m["volume_ratio"]:.2f}x')
            st.markdown('</div>',unsafe_allow_html=True)
        with c:
            st.markdown('<div class="card">',unsafe_allow_html=True)
            st.markdown('<div class="small">Risk Scanner</div>',unsafe_allow_html=True)
            st.metric("Risk",f'{m["risk"]}/100'); st.metric("24h Range",f'{m["range24"]:.2f}%'); st.metric("Order-book Bias",f'{m["imbalance"]:.1f}%')
            st.markdown('</div>',unsafe_allow_html=True)

        st.subheader("📈 Price & Activity")
        fig=go.Figure(go.Candlestick(x=k["open_time"],open=k["open"],high=k["high"],low=k["low"],close=k["close"],name=symbol))
        fig.update_layout(height=430,margin=dict(l=10,r=10,t=10,b=10),template="plotly_dark",xaxis_rangeslider_visible=False,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",showlegend=False)
        st.plotly_chart(fig,use_container_width=True)

        left,right=st.columns(2)
        with left:
            st.markdown('<div class="card">',unsafe_allow_html=True); st.subheader("🧠 Why this score?")
            for name,val in [("Momentum",m["momentum"]),("Volume",m["volume"]),("Liquidity",m["liquidity"]),("Sentiment proxy",m["sentiment"])]:
                st.markdown(f"**{name} — {val}/100**"); st.progress(val/100)
            st.markdown('</div>',unsafe_allow_html=True)
        with right:
            st.markdown('<div class="card">',unsafe_allow_html=True); st.subheader("🛡️ AI Risk Brief")
            for item in report["warnings"]: st.warning("⚠ "+item)
            st.markdown("**What could invalidate the setup?**")
            for item in report["invalidations"]: st.write("• "+item)
            st.markdown('</div>',unsafe_allow_html=True)

        st.subheader("🔎 Signal Matrix")
        cols=st.columns(4)
        for col,(name,val) in zip(cols,[("Momentum",m["momentum"]),("Volume",m["volume"]),("Liquidity",m["liquidity"]),("Sentiment",m["sentiment"])]):
            with col: st.markdown(f'<div class="signal"><b>{name}</b><br><span style="font-size:1.4rem">{val}/100</span></div>',unsafe_allow_html=True)
        st.info("Alpha Score is a transparent heuristic for this hackathon prototype. It is not financial advice or a guaranteed prediction.")
    except Exception as e:
        st.error(f"Could not analyze {symbol}."); st.caption(f"Technical detail: {e}")
else:
    st.markdown('<div class="card"><h3>How AlphaPilot works</h3><p>1️⃣ Binance Agent OS MCP → 2️⃣ market signals → 3️⃣ Alpha Score → 4️⃣ explainable risk analysis.</p></div>',unsafe_allow_html=True)

st.markdown('<div class="footer">AlphaPilot AI • Binance Agent OS Mini Hackathon • MCP-first read-only prototype</div>',unsafe_allow_html=True)
