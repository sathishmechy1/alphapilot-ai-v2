import re
import streamlit as st
import plotly.graph_objects as go

from market_data import snapshot
from analyst import analyze


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="AlphaPilot Copilot",
    page_icon="🚀",
    layout="wide",
)


# ---------------------------------------------------------
# STYLING
# ---------------------------------------------------------
st.markdown(
    """
<style>
.stApp {
    background: radial-gradient(
        circle at 15% 0%,
        #17130a 0%,
        #0b0e11 34%
    );
    color: #f5f5f5;
}

.block-container {
    max-width: 1180px;
    padding-top: 2rem;
}

.hero,
.card {
    border-radius: 20px;
    background: #11151a;
    border: 1px solid #292e35;
}

.hero {
    padding: 28px 30px;
    margin-bottom: 22px;
    border-color: #5a481f;
}

.hero h1 {
    font-size: 2.7rem;
}

.hero p {
    font-size: 1.12rem;
    color: #c8cbd0;
}

.badge {
    display: inline-block;
    margin-top: 10px;
    padding: 5px 10px;
    border-radius: 999px;
    background: #211d12;
    border: 1px solid #5a481f;
    color: #f3ba2f;
}

.card {
    padding: 20px;
    height: 100%;
}

.score {
    font-size: 62px;
    line-height: 1;
    font-weight: 850;
    color: #f3ba2f;
}

.small {
    color: #8f969f;
    font-size: .8rem;
    text-transform: uppercase;
    letter-spacing: .08em;
}

.signal {
    padding: 10px 12px;
    border-radius: 10px;
    background: #171b20;
    border: 1px solid #252a30;
    margin: 7px 0;
}

.copilot {
    padding: 18px;
    border-radius: 16px;
    background: #101419;
    border: 1px solid #343a42;
    margin-bottom: 12px;
}

.footer {
    text-align: center;
    color: #6f767f;
    font-size: .78rem;
    padding: 28px 0 8px;
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_report" not in st.session_state:
    st.session_state.last_report = None

if "last_snapshot" not in st.session_state:
    st.session_state.last_snapshot = None

if "last_symbol" not in st.session_state:
    st.session_state.last_symbol = "SOLUSDT"


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.markdown(
    """
<div class="hero">
    <h1>🚀 AlphaPilot Copilot</h1>
    <p>
        Your explainable Binance market intelligence copilot.
    </p>
    <span class="badge">
        BINANCE AGENT OS • MCP-FIRST • ANALYTICS
    </span>
</div>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------
def extract_symbol(text):
    """
    Extract a Binance-style USDT symbol from a user message.
    """
    matches = re.findall(r"\b[A-Z]{2,12}USDT\b", text.upper())

    if matches:
        return matches[0]

    return st.session_state.last_symbol


def run_analysis(symbol):
    """
    Run the existing AlphaPilot intelligence engine.
    """
    snap = snapshot(symbol)
    report = analyze(symbol, snap)

    st.session_state.last_symbol = symbol
    st.session_state.last_snapshot = snap
    st.session_state.last_report = report

    return snap, report


def copilot_response(question, symbol, report, snap):
    """
    Deterministic Copilot response using AlphaPilot's
    existing quantitative engine.
    """

    m = report["metrics"]
    q = question.lower()

    score = m["alpha_score"]
    regime = m["regime"]

    # Overall analysis
    if (
        "analy" in q
        or "what do you think" in q
        or "outlook" in q
        or "overview" in q
        or "look like" in q
    ):
        return (
            f"### 🤖 AlphaPilot view on {symbol}\n\n"
            f"**Alpha Score: {score}/100 — {regime}**\n\n"
            f"{report['summary']}\n\n"
            f"**Key signals**\n"
            f"- Momentum: **{m['momentum']}/100**\n"
            f"- Volume: **{m['volume']}/100**\n"
            f"- Liquidity: **{m['liquidity']}/100**\n"
            f"- Sentiment proxy: **{m['sentiment']}/100**\n"
            f"- Risk: **{m['risk']}/100**\n\n"
            f"**Main watch-out:** {report['warnings'][0]}"
        )

    # Why score?
    if "why" in q and ("score" in q or "alpha" in q):
        weighted = {
            "Momentum": round(m["momentum"] * 0.30, 1),
            "Volume": round(m["volume"] * 0.20, 1),
            "Sentiment": round(m["sentiment"] * 0.20, 1),
            "Liquidity": round(m["liquidity"] * 0.15, 1),
            "Risk adjustment": round((100 - m["risk"]) * 0.15, 1),
        }

        explanation = "\n".join(
            f"- **{name}:** {value} points"
            for name, value in weighted.items()
        )

        return (
            f"### 🧠 Why {symbol} scored {score}/100\n\n"
            f"The Alpha Score is calculated from transparent quantitative "
            f"signals rather than an LLM guessing the score.\n\n"
            f"{explanation}\n\n"
            f"**Regime:** {regime}"
        )

    # Momentum
    if "momentum" in q:
        direction = (
            "strong"
            if m["momentum"] >= 70
            else "weak"
            if m["momentum"] < 40
            else "moderate"
        )

        return (
            f"### 📈 {symbol} momentum\n\n"
            f"Momentum is **{m['momentum']}/100**, which AlphaPilot "
            f"classifies as **{direction}**.\n\n"
            f"The score incorporates recent short-term and 24-hour "
            f"price movement."
        )

    # Volume
    if "volume" in q:
        activity = (
            "above baseline"
            if m["volume"] >= 65
            else "muted"
            if m["volume"] < 40
            else "near baseline"
        )

        return (
            f"### 📊 {symbol} volume\n\n"
            f"Volume score: **{m['volume']}/100**\n\n"
            f"Current volume ratio: **{m['volume_ratio']:.2f}x** "
            f"the recent baseline.\n\n"
            f"Trading activity is **{activity}**."
        )

    # Risk
    if "risk" in q:
        level = (
            "elevated"
            if m["risk"] >= 70
            else "relatively contained"
            if m["risk"] <= 40
            else "moderate"
        )

        return (
            f"### 🛡️ {symbol} risk\n\n"
            f"Risk score: **{m['risk']}/100**.\n\n"
            f"Current volatility risk is **{level}**.\n\n"
            f"**Watch-out:** {report['warnings'][0]}\n\n"
            f"**Invalidation:** {report['invalidations'][0]}"
        )

    # Liquidity / order book
    if (
        "order book" in q
        or "orderbook" in q
        or "liquidity" in q
        or "pressure" in q
    ):
        pressure = (
            "buy-side"
            if m["imbalance"] > 10
            else "sell-side"
            if m["imbalance"] < -10
            else "relatively balanced"
        )

        return (
            f"### 📚 {symbol} order-book pressure\n\n"
            f"Liquidity score: **{m['liquidity']}/100**\n\n"
            f"Order-book imbalance: **{m['imbalance']:.1f}%**.\n\n"
            f"Current pressure is **{pressure}**."
        )

    # Price
    if "price" in q or "current" in q:
        return (
            f"### 💰 {symbol}\n\n"
            f"Current price: **{m['price']:,.4f}**\n\n"
            f"24h change: **{m['change']:.2f}%**\n\n"
            f"24h range: **{m['range24']:.2f}%**"
        )

    # Default response
    return (
        f"### 🤖 AlphaPilot Copilot\n\n"
        f"I've analyzed **{symbol}**.\n\n"
        f"**Alpha Score:** {score}/100\n"
        f"**Regime:** {regime}\n"
        f"**Price:** {m['price']:,.4f}\n"
        f"**24h:** {m['change']:.2f}%\n"
        f"**Momentum:** {m['momentum']}/100\n"
        f"**Volume:** {m['volume']}/100\n"
        f"**Liquidity:** {m['liquidity']}/100\n"
        f"**Risk:** {m['risk']}/100\n\n"
        f"Try asking:\n"
        f"- Why is the score this high/low?\n"
        f"- How is momentum?\n"
        f"- What are the risks?\n"
        f"- What's the order-book pressure?\n"
    )


# ---------------------------------------------------------
# COPILOT CHAT
# ---------------------------------------------------------
st.subheader("🤖 AlphaPilot Copilot")

st.caption(
    "Ask about a Binance symbol. Examples: "
    "`Analyze SOLUSDT` · `Why is the score low?` · "
    "`What is the risk?`"
)


# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


prompt = st.chat_input(
    "Ask AlphaPilot about BTCUSDT, SOLUSDT, ETHUSDT..."
)


if prompt:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    symbol = extract_symbol(prompt)

    with st.chat_message("assistant"):

        with st.spinner(f"Analyzing {symbol}..."):

            try:
                snap, report = run_analysis(symbol)

                answer = copilot_response(
                    prompt,
                    symbol,
                    report,
                    snap,
                )

                st.markdown(answer)

                # Data-source status
                if snap.get("source") == "Binance Agent OS MCP":
                    st.success(
                        "🔌 Binance Agent OS MCP market-data path active."
                    )
                else:
                    st.warning(
                        "⚠️ Market data is currently using Binance "
                        "public REST fallback. Authenticated Agentic "
                        "MCP is not established in this Streamlit app yet."
                    )

            except Exception as exc:
                answer = (
                    f"Unable to analyze **{symbol}** right now.\n\n"
                    f"Technical detail: `{exc}`"
                )

                st.error(answer)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )


# ---------------------------------------------------------
# QUICK ANALYZE
# ---------------------------------------------------------
st.divider()

st.subheader("⚡ Quick Market Analysis")

c1, c2 = st.columns([1, 4])

with c1:
    quick_symbol = st.text_input(
        "Symbol",
        value=st.session_state.last_symbol,
        label_visibility="collapsed",
    ).upper().strip()

with c2:
    analyze_button = st.button(
        "🔎 Analyze Market",
        type="primary",
        use_container_width=True,
    )


if analyze_button and quick_symbol:

    try:

        with st.spinner(f"Querying Binance market data for {quick_symbol}..."):
            snap, report = run_analysis(quick_symbol)

        m = report["metrics"]
        k = snap["klines"]

        if snap.get("source") == "Binance Agent OS MCP":
            st.success(
                "🔌 Binance Agent OS MCP connected — "
                "market data retrieved through MCP."
            )
        else:
            st.warning(
                "⚠️ Binance MCP is not authenticated in this "
                "Streamlit app. Using public Binance market data."
            )

        # -------------------------------------------------
        # TOP METRICS
        # -------------------------------------------------
        a, b, c, d = st.columns(4)

        with a:
            st.metric(
                "Price",
                f'{m["price"]:,.4f}',
                f'{m["change"]:.2f}%',
            )

        with b:
            st.metric(
                "Alpha Score",
                f'{m["alpha_score"]}/100',
            )

        with c:
            st.metric(
                "Risk",
                f'{m["risk"]}/100',
            )

        with d:
            st.metric(
                "Volume Ratio",
                f'{m["volume_ratio"]:.2f}x',
            )

        # -------------------------------------------------
        # SCORE / REGIME
        # -------------------------------------------------
        st.divider()

        left, right = st.columns([1.15, 1])

        with left:

            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="small">Alpha Score</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                f'<div class="score">{m["alpha_score"]}'
                f'<span style="font-size:24px;color:#777">'
                f'/100</span></div>',
                unsafe_allow_html=True,
            )

            icon = (
                "🟢"
                if m["alpha_score"] >= 60
                else "🟡"
                if m["alpha_score"] >= 45
                else "🔴"
            )

            st.subheader(
                f"{icon} {m['regime']}"
            )

            st.write(report["summary"])

            st.markdown(
                '</div>',
                unsafe_allow_html=True,
            )

        with right:

            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="small">Risk Scanner</div>',
                unsafe_allow_html=True,
            )

            st.metric(
                "Risk",
                f'{m["risk"]}/100',
            )

            st.metric(
                "24h Range",
                f'{m["range24"]:.2f}%',
            )

            st.metric(
                "Order-book Bias",
                f'{m["imbalance"]:.1f}%',
            )

            st.markdown(
                '</div>',
                unsafe_allow_html=True,
            )

        # -------------------------------------------------
        # CHART
        # -------------------------------------------------
        st.subheader("📈 Price & Activity")

        fig = go.Figure(
            go.Candlestick(
                x=k["open_time"],
                open=k["open"],
                high=k["high"],
                low=k["low"],
                close=k["close"],
                name=quick_symbol,
            )
        )

        fig.update_layout(
            height=430,
            margin=dict(l=10, r=10, t=10, b=10),
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        # -------------------------------------------------
        # SIGNAL MATRIX
        # -------------------------------------------------
        st.subheader("🔎 Signal Matrix")

        cols = st.columns(4)

        signals = [
            ("Momentum", m["momentum"]),
            ("Volume", m["volume"]),
            ("Liquidity", m["liquidity"]),
            ("Sentiment", m["sentiment"]),
        ]

        for col, (name, value) in zip(cols, signals):

            with col:

                st.markdown(
                    f"""
                    <div class="signal">
                        <b>{name}</b><br>
                        <span style="font-size:1.4rem">
                            {value}/100
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # -------------------------------------------------
        # WHY THIS SCORE
        # -------------------------------------------------
        left, right = st.columns(2)

        with left:

            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True,
            )

            st.subheader("🧠 Why this score?")

            for name, value in [
                ("Momentum", m["momentum"]),
                ("Volume", m["volume"]),
                ("Liquidity", m["liquidity"]),
                ("Sentiment", m["sentiment"]),
            ]:

                st.markdown(
                    f"**{name} — {value}/100**"
                )

                st.progress(value / 100)

            st.markdown(
                '</div>',
                unsafe_allow_html=True,
            )

        with right:

            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True,
            )

            st.subheader("🛡️ AI Risk Brief")

            for item in report["warnings"]:
                st.warning("⚠ " + item)

            st.markdown(
                "**What could invalidate the setup?**"
            )

            for item in report["invalidations"]:
                st.write("• " + item)

            st.markdown(
                '</div>',
                unsafe_allow_html=True,
            )

        st.info(
            "Alpha Score is a transparent heuristic for this "
            "hackathon prototype. It is not financial advice "
            "or a guaranteed prediction."
        )

    except Exception as exc:

        st.error(
            f"Could not analyze {quick_symbol}."
        )

        st.caption(
            f"Technical detail: {exc}"
        )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.markdown(
    """
<div class="footer">
    AlphaPilot Copilot • Binance Agent OS Hackathon
    • Explainable Market Intelligence
</div>
""",
    unsafe_allow_html=True,
        )
