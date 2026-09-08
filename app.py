import streamlit as st
from market_data import snapshot
from analyst import analyze

st.set_page_config(page_title="AlphaPilot AI", page_icon="🚀", layout="wide")
st.markdown('''<style>
.stApp{background:#0b0e11;color:#f5f5f5}.block-container{max-width:1100px}
.hero{padding:25px;border-radius:18px;background:#11151a;border:1px solid #3a321c;margin-bottom:20px}
.score{font-size:58px;font-weight:800;color:#f3ba2f}.card{padding:18px;border-radius:14px;background:#11151a;border:1px solid #252a30}
</style>''', unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>🚀 AlphaPilot AI</h1><p>Turn Binance market data into explainable crypto intelligence.</p><small>Read-only hackathon prototype</small></div>', unsafe_allow_html=True)

symbol = st.text_input("Enter a Binance symbol", "SOLUSDT").upper().strip()
if st.button("Analyze", type="primary"):
    try:
        with st.spinner("Analyzing market signals..."):
            report = analyze(symbol, snapshot(symbol))
        m = report["metrics"]
        a,b,c = st.columns(3)
        with a:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.caption(symbol)
            st.markdown(f'<div class="score">{m["alpha_score"]}/100</div>', unsafe_allow_html=True)
            st.subheader(("🟢 " if m["alpha_score"]>=60 else "🟡 " if m["alpha_score"]>=45 else "🔴 ")+m["regime"])
            st.write(report["summary"])
            st.markdown('</div>', unsafe_allow_html=True)
        with b:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Signal Matrix")
            st.metric("Momentum", f'{m["momentum"]}/100')
            st.metric("Volume", f'{m["volume"]}/100')
            st.metric("Liquidity", f'{m["liquidity"]}/100')
            st.metric("Sentiment Proxy", f'{m["sentiment"]}/100')
            st.markdown('</div>', unsafe_allow_html=True)
        with c:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Risk Scanner")
            st.metric("Risk", f'{m["risk"]}/100')
            st.metric("24h Change", f'{m["change"]:.2f}%')
            st.metric("Volume Ratio", f'{m["volume_ratio"]:.2f}x')
            st.metric("24h Range", f'{m["range24"]:.2f}%')
            st.markdown('</div>', unsafe_allow_html=True)
        st.divider()
        x,y = st.columns(2)
        with x:
            st.subheader("Why this score?")
            for item in report["positives"]: st.success("✓ "+item)
        with y:
            st.subheader("Risk flags")
            for item in report["warnings"]: st.warning("⚠ "+item)
        st.info("Alpha Score is a heuristic for a hackathon prototype, not financial advice or a guaranteed prediction.")
    except Exception as e:
        st.error(f"Could not analyze {symbol}. Check that the symbol exists on Binance and try again.")
