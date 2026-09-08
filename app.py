import inspect
import re

import plotly.graph_objects as go
import streamlit as st

import analyst
from market_data import snapshot


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AlphaPilot Copilot",
    page_icon="🚀",
    layout="wide",
)


# =========================================================
# CUSTOM CSS
# =========================================================

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
    padding: 12px;
    border-radius: 10px;
    background: #171b20;
    border: 1px solid #252a30;
    margin: 7px 0;
}

.copilot-card {
    padding: 18px;
    border-radius: 16px;
    background: #101419;
    border: 1px solid #343a42;
    margin-bottom: 15px;
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


# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_report" not in st.session_state:
    st.session_state.last_report = None

if "last_snapshot" not in st.session_state:
    st.session_state.last_snapshot = None

if "last_symbol" not in st.session_state:
    st.session_state.last_symbol = "SOLUSDT"


# =========================================================
# COMPATIBILITY ANALYZER
# =========================================================

def run_alpha_analysis(symbol, snap):
    """
    Supports both possible analyst.py versions:

        analyze(symbol, snap)

    and:

        analyze(snap)

    This prevents the deployed Streamlit app from failing
    if an older analyst.py version is still being loaded.
    """

    fn = analyst.analyze

    try:
        signature = inspect.signature(fn)
        params = list(signature.parameters.values())

        positional = [
            p
            for p in params
            if p.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]

        if len(positional) >= 2:
            return fn(symbol, snap)

        return fn(snap)

    except (TypeError, ValueError):
        # Fallback for unusual callable signatures
        try:
            return fn(symbol, snap)
        except TypeError:
            return fn(snap)


# =========================================================
# SYMBOL EXTRACTION
# =========================================================

def extract_symbol(text):
    """
    Finds symbols such as:
    BTCUSDT
    ETHUSDT
    SOLUSDT
    BNBUSDT
    """

    matches = re.findall(
        r"\b[A-Z]{2,12}USDT\b",
        text.upper(),
    )

    if matches:
        return matches[0]

    return st.session_state.last_symbol


# =========================================================
# RUN ANALYSIS
# =========================================================

def run_analysis(symbol):

    symbol = symbol.upper().strip()

    snap = snapshot(symbol)

    report = run_alpha_analysis(
        symbol,
        snap,
    )

    st.session_state.last_symbol = symbol
    st.session_state.last_snapshot = snap
    st.session_state.last_report = report

    return snap, report


# =========================================================
# COPILOT RESPONSE ENGINE
# =========================================================

def copilot_response(question, symbol, report, snap):

    m = report["metrics"]

    q = question.lower().strip()

    score = m["alpha_score"]
    regime = m["regime"]

    # -----------------------------------------------------
    # GENERAL ANALYSIS
    # -----------------------------------------------------

    if (
        "analy" in q
        or "outlook" in q
        or "overview" in q
        or "what do you think" in q
        or "how does" in q
    ):

        return (
            f"### 🤖 AlphaPilot view on {symbol}\n\n"
            f"**Alpha Score: {score}/100 — {regime}**\n\n"
            f"{report['summary']}\n\n"
            f"**Signal Matrix**\n\n"
            f"- 📈 Momentum: **{m['momentum']}/100**\n"
            f"- 📊 Volume: **{m['volume']}/100**\n"
            f"- 💧 Liquidity: **{m['liquidity']}/100**\n"
            f"- 🧠 Sentiment proxy: **{m['sentiment']}/100**\n"
            f"- 🛡️ Risk: **{m['risk']}/100**\n\n"
            f"**Main watch-out:** "
            f"{report['warnings'][0]}"
        )

    # -----------------------------------------------------
    # WHY SCORE
    # -----------------------------------------------------

    if (
        ("why" in q or "explain" in q)
        and ("score" in q or "alpha" in q)
    ):

        momentum_points = m["momentum"] * 0.30
        volume_points = m["volume"] * 0.20
        sentiment_points = m["sentiment"] * 0.20
        liquidity_points = m["liquidity"] * 0.15
        risk_points = (100 - m["risk"]) * 0.15

        return (
            f"### 🧠 Why {symbol} scored {score}/100\n\n"
            f"AlphaPilot uses a transparent weighted model:\n\n"
            f"- **Momentum:** {m['momentum']}/100 → "
            f"{momentum_points:.1f} points\n"
            f"- **Volume:** {m['volume']}/100 → "
            f"{volume_points:.1f} points\n"
            f"- **Sentiment:** {m['sentiment']}/100 → "
            f"{sentiment_points:.1f} points\n"
            f"- **Liquidity:** {m['liquidity']}/100 → "
            f"{liquidity_points:.1f} points\n"
            f"- **Risk adjustment:** "
            f"{risk_points:.1f} points\n\n"
            f"**Current regime:** {regime}\n\n"
            f"The LLM/Copilot layer does not invent the Alpha Score; "
            f"it explains the deterministic AlphaPilot calculation."
        )

    # -----------------------------------------------------
    # MOMENTUM
    # -----------------------------------------------------

    if "momentum" in q:

        if m["momentum"] >= 70:
            strength = "strong"
        elif m["momentum"] < 40:
            strength = "weak"
        else:
            strength = "moderate"

        return (
            f"### 📈 {symbol} momentum\n\n"
            f"Momentum score: **{m['momentum']}/100**.\n\n"
            f"AlphaPilot currently considers momentum **{strength}**.\n\n"
            f"The calculation considers recent short-term and "
            f"24-hour price movement."
        )

    # -----------------------------------------------------
    # VOLUME
    # -----------------------------------------------------

    if "volume" in q:

        if m["volume"] >= 65:
            activity = "above baseline"
        elif m["volume"] < 40:
            activity = "muted"
        else:
            activity = "near baseline"

        return (
            f"### 📊 {symbol} volume\n\n"
            f"Volume score: **{m['volume']}/100**\n\n"
            f"Volume ratio: **{m['volume_ratio']:.2f}x** "
            f"the recent baseline.\n\n"
            f"Trading activity is currently **{activity}**."
        )

    # -----------------------------------------------------
    # RISK
    # -----------------------------------------------------

    if "risk" in q:

        if m["risk"] >= 70:
            level = "elevated"
        elif m["risk"] <= 40:
            level = "relatively contained"
        else:
            level = "moderate"

        return (
            f"### 🛡️ {symbol} risk\n\n"
            f"Risk score: **{m['risk']}/100**.\n\n"
            f"Current volatility risk is **{level}**.\n\n"
            f"**Warning:** {report['warnings'][0]}\n\n"
            f"**Invalidation:** {report['invalidations'][0]}"
        )

    # -----------------------------------------------------
    # ORDER BOOK
    # -----------------------------------------------------

    if (
        "order book" in q
        or "orderbook" in q
        or "liquidity" in q
        or "pressure" in q
    ):

        if m["imbalance"] > 10:
            pressure = "buy-side"
        elif m["imbalance"] < -10:
            pressure = "sell-side"
        else:
            pressure = "relatively balanced"

        return (
            f"### 📚 {symbol} order-book pressure\n\n"
            f"Liquidity score: **{m['liquidity']}/100**\n\n"
            f"Order-book imbalance: **{m['imbalance']:.1f}%**.\n\n"
            f"Current pressure is **{pressure}**."
        )

    # -----------------------------------------------------
    # PRICE
    # -----------------------------------------------------

    if (
        "price" in q
        or "current price" in q
        or "how much" in q
    ):

        return (
            f"### 💰 {symbol}\n\n"
            f"Current price: **{m['price']:,.4f}**\n\n"
            f"24h change: **{m['change']:.2f}%**\n\n"
            f"24h range: **{m['range24']:.2f}%**"
        )

    # -----------------------------------------------------
    # DEFAULT
    # -----------------------------------------------------

    return (
        f"### 🤖 AlphaPilot Copilot\n\n"
        f"I analyzed **{symbol}** using the current "
        f"AlphaPilot market snapshot.\n\n"
        f"**Alpha Score:** {score}/100\n\n"
        f"**Regime:** {regime}\n\n"
        f"**Price:** {m['price']:,.4f}\n\n"
        f"**24h change:** {m['change']:.2f}%\n\n"
        f"**Momentum:** {m['momentum']}/100\n\n"
        f"**Volume:** {m['volume']}/100\n\n"
        f"**Liquidity:** {m['liquidity']}/100\n\n"
        f"**Risk:** {m['risk']}/100\n\n"
        f"Try asking:\n\n"
        f"- `Analyze SOLUSDT`\n"
        f"- `Why is the score low?`\n"
        f"- `How is momentum?`\n"
        f"- `What is the risk?`\n"
        f"- `What's the order-book pressure?`\n"
        f"- `What is the current price?`"
    )


# =========================================================
# HERO
# =========================================================

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


# =========================================================
# COPILOT
# =========================================================

st.subheader("🤖 AlphaPilot Copilot")

st.caption(
    "Ask AlphaPilot about a Binance symbol. "
    "Examples: Analyze SOLUSDT · Why is the score low? · "
    "What is the risk?"
)


# Display conversation history

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Chat input

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

        try:

            with st.spinner(
                f"Analyzing {symbol}..."
            ):

                snap, report = run_analysis(symbol)

                answer = copilot_response(
                    prompt,
                    symbol,
                    report,
                    snap,
                )

            st.markdown(answer)

            # ---------------------------------------------
            # DATA SOURCE
            # ---------------------------------------------

            if snap.get("source") == "Binance Agent OS MCP":

                st.success(
                    "🔌 Binance Agent OS MCP market-data path active."
                )

            else:

                st.warning(
                    "⚠️ Binance Agentic MCP authentication is not "
                    "established in this Streamlit app yet. "
                    "Market data is currently using Binance public REST."
                )

        except Exception as exc:

            answer = (
                f"### ❌ Analysis error\n\n"
                f"Could not analyze **{symbol}**.\n\n"
                f"Technical detail:\n\n"
                f"`{exc}`"
            )

            st.error(answer)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )


# =========================================================
# QUICK MARKET ANALYSIS
# =========================================================

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


# =========================================================
# ANALYSIS DASHBOARD
# =========================================================

if analyze_button and quick_symbol:

    try:

        with st.spinner(
            f"Querying Binance market data for {quick_symbol}..."
        ):

            snap, report = run_analysis(
                quick_symbol
            )

        m = report["metrics"]
        k = snap["klines"]

        # -------------------------------------------------
        # SOURCE STATUS
        # -------------------------------------------------

        if snap.get("source") == "Binance Agent OS MCP":

            st.success(
                "🔌 Binance Agent OS MCP connected — "
                "market data retrieved through MCP."
            )

        else:

            st.warning(
                "⚠️ Binance Agentic MCP is not authenticated "
                "in this Streamlit app. Using public Binance "
                "market data."
            )

            if snap.get("mcp_error"):
                st.caption(
                    "MCP status: "
                    + str(snap["mcp_error"])
                )

        # -------------------------------------------------
        # TOP METRICS
        # -------------------------------------------------

        st.divider()

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
        # ALPHA SCORE + RISK
        # -------------------------------------------------

        st.divider()

        left, right = st.columns(
            [1.15, 1]
        )

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
                f"""
                <div class="score">
                    {m["alpha_score"]}
                    <span style="font-size:24px;color:#777">
                        /100
                    </span>
                </div>
                """,
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

            st.write(
                report["summary"]
            )

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
        # PRICE CHART
        # -------------------------------------------------

        st.subheader(
            "📈 Price & Activity"
        )

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
            margin=dict(
                l=10,
                r=10,
                t=10,
                b=10,
            ),
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

        st.subheader(
            "🔎 Signal Matrix"
        )

        cols = st.columns(4)

        signals = [
            ("Momentum", m["momentum"]),
            ("Volume", m["volume"]),
            ("Liquidity", m["liquidity"]),
            ("Sentiment", m["sentiment"]),
        ]

        for col, (name, value) in zip(
            cols,
            signals,
        ):

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
        # WHY SCORE + RISK
        # -------------------------------------------------

        left, right = st.columns(2)

        with left:

            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True,
            )

            st.subheader(
                "🧠 Why this score?"
            )

            for name, value in [
                ("Momentum", m["momentum"]),
                ("Volume", m["volume"]),
                ("Liquidity", m["liquidity"]),
                ("Sentiment", m["sentiment"]),
            ]:

                st.markdown(
                    f"**{name} — {value}/100**"
                )

                st.progress(
                    value / 100
                )

            st.markdown(
                '</div>',
                unsafe_allow_html=True,
            )

        with right:

            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True,
            )

            st.subheader(
                "🛡️ AI Risk Brief"
            )

            for item in report["warnings"]:

                st.warning(
                    "⚠ " + item
                )

            st.markdown(
                "**What could invalidate the setup?**"
            )

            for item in report["invalidations"]:

                st.write(
                    "• " + item
                )

            st.markdown(
                '</div>',
                unsafe_allow_html=True,
            )

        # -------------------------------------------------
        # DISCLAIMER
        # -------------------------------------------------

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


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
<div class="footer">
    AlphaPilot Copilot • Binance Agent OS Hackathon
    • Explainable Market Intelligence
</div>
""",
    unsafe_allow_html=True,
)
