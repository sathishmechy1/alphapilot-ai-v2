import re

import plotly.graph_objects as go
import streamlit as st

from market_data import snapshot
from scoring import compute


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="AlphaPilot Copilot",
    page_icon="🚀",
    layout="wide",
)


# =========================================================
# STYLE
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

.hero {
    padding: 28px 30px;
    margin-bottom: 22px;
    border-radius: 20px;
    background: #11151a;
    border: 1px solid #5a481f;
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
    border-radius: 20px;
    background: #11151a;
    border: 1px solid #292e35;
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

if "last_symbol" not in st.session_state:
    st.session_state.last_symbol = "SOLUSDT"

if "last_snapshot" not in st.session_state:
    st.session_state.last_snapshot = None

if "last_metrics" not in st.session_state:
    st.session_state.last_metrics = None


# =========================================================
# ALPHA REPORT
# =========================================================

def build_report(symbol, snap):
    """
    Build the explainable AlphaPilot report directly from
    scoring.py.

    This intentionally does NOT import or call analyst.py.
    """

    s = compute(snap)

    positives = []
    warnings = []
    invalidations = []

    if s["momentum"] >= 70:
        positives.append("strong short-term momentum")
    elif s["momentum"] < 40:
        warnings.append("weak short-term momentum")

    if s["volume"] >= 65:
        positives.append("above-baseline trading activity")
    elif s["volume"] < 40:
        warnings.append("muted volume")

    if s["liquidity"] >= 65:
        positives.append("supportive order-book imbalance")
    elif s["liquidity"] < 40:
        warnings.append("sell-side order-book pressure")

    if s["risk"] >= 70:
        warnings.append("elevated volatility risk")
        invalidations.append(
            "A sharp volatility expansion could quickly change the score."
        )
    elif s["risk"] <= 40:
        positives.append("relatively contained volatility")

    if s["change"] < -3:
        invalidations.append(
            "A continued 24h decline would weaken the momentum case."
        )

    if s["volume_ratio"] < 0.75:
        invalidations.append(
            "Further volume deterioration would reduce conviction."
        )

    if s["imbalance"] < -10:
        invalidations.append(
            "Persistent sell-side order-book pressure would be a bearish confirmation."
        )

    if not positives:
        positives.append("mixed market signals")

    if not warnings:
        warnings.append(
            "no major risk flag from the current snapshot"
        )

    if not invalidations:
        invalidations.append(
            "A material change in price, volume or order-book balance "
            "could change the signal."
        )

    summary = (
        f"{symbol} scores {s['alpha_score']}/100 and is currently "
        f"{s['regime'].lower()}. Strongest signals: "
        f"{', '.join(positives[:2])}. Main watch-outs: "
        f"{', '.join(warnings[:2])}."
    )

    return {
        "metrics": s,
        "positives": positives,
        "warnings": warnings,
        "invalidations": invalidations,
        "summary": summary,
    }


# =========================================================
# ANALYZE
# =========================================================

def run_analysis(symbol):

    symbol = symbol.upper().strip()

    snap = snapshot(symbol)

    report = build_report(
        symbol,
        snap,
    )

    st.session_state.last_symbol = symbol
    st.session_state.last_snapshot = snap
    st.session_state.last_metrics = report["metrics"]

    return snap, report


# =========================================================
# SYMBOL
# =========================================================

def extract_symbol(text):

    matches = re.findall(
        r"\b[A-Z]{2,12}USDT\b",
        text.upper(),
    )

    if matches:
        return matches[0]

    return st.session_state.last_symbol


# =========================================================
# COPILOT
# =========================================================

def answer_question(question, symbol, report):

    m = report["metrics"]
    q = question.lower()

    score = m["alpha_score"]

    # ---------------------------------------------
    # WHY SCORE
    # ---------------------------------------------

    if (
        ("why" in q or "explain" in q)
        and ("score" in q or "alpha" in q)
    ):

        return (
            f"### 🧠 Why {symbol} scored {score}/100\n\n"
            f"AlphaPilot uses a transparent quantitative model.\n\n"
            f"- 📈 Momentum: **{m['momentum']}/100** → "
            f"{m['momentum'] * 0.30:.1f} points\n"
            f"- 📊 Volume: **{m['volume']}/100** → "
            f"{m['volume'] * 0.20:.1f} points\n"
            f"- 🧠 Sentiment: **{m['sentiment']}/100** → "
            f"{m['sentiment'] * 0.20:.1f} points\n"
            f"- 💧 Liquidity: **{m['liquidity']}/100** → "
            f"{m['liquidity'] * 0.15:.1f} points\n"
            f"- 🛡️ Risk adjustment: "
            f"{(100 - m['risk']) * 0.15:.1f} points\n\n"
            f"**Regime:** {m['regime']}"
        )

    # ---------------------------------------------
    # RISK
    # ---------------------------------------------

    if "risk" in q:

        return (
            f"### 🛡️ {symbol} Risk\n\n"
            f"Risk score: **{m['risk']}/100**.\n\n"
            f"24h range: **{m['range24']:.2f}%**.\n\n"
            f"**Warning:** {report['warnings'][0]}\n\n"
            f"**Invalidation:** {report['invalidations'][0]}"
        )

    # ---------------------------------------------
    # MOMENTUM
    # ---------------------------------------------

    if "momentum" in q:

        return (
            f"### 📈 {symbol} Momentum\n\n"
            f"Momentum score: **{m['momentum']}/100**.\n\n"
            f"Recent price movement is contributing "
            f"to the current Alpha Score."
        )

    # ---------------------------------------------
    # VOLUME
    # ---------------------------------------------

    if "volume" in q:

        return (
            f"### 📊 {symbol} Volume\n\n"
            f"Volume score: **{m['volume']}/100**.\n\n"
            f"Current volume ratio: **{m['volume_ratio']:.2f}x** "
            f"recent baseline."
        )

    # ---------------------------------------------
    # ORDER BOOK
    # ---------------------------------------------

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
            f"### 📚 {symbol} Order Book\n\n"
            f"Liquidity score: **{m['liquidity']}/100**.\n\n"
            f"Imbalance: **{m['imbalance']:.1f}%**.\n\n"
            f"Current pressure is **{pressure}**."
        )

    # ---------------------------------------------
    # PRICE
    # ---------------------------------------------

    if "price" in q or "current" in q:

        return (
            f"### 💰 {symbol}\n\n"
            f"Current price: **{m['price']:,.4f}**\n\n"
            f"24h change: **{m['change']:.2f}%**\n\n"
            f"24h range: **{m['range24']:.2f}%**."
        )

    # ---------------------------------------------
    # DEFAULT / ANALYSIS
    # ---------------------------------------------

    return (
        f"### 🤖 AlphaPilot Analysis — {symbol}\n\n"
        f"**Alpha Score: {score}/100 — {m['regime']}**\n\n"
        f"{report['summary']}\n\n"
        f"**Signals**\n\n"
        f"- 📈 Momentum: **{m['momentum']}/100**\n"
        f"- 📊 Volume: **{m['volume']}/100**\n"
        f"- 💧 Liquidity: **{m['liquidity']}/100**\n"
        f"- 🧠 Sentiment: **{m['sentiment']}/100**\n"
        f"- 🛡️ Risk: **{m['risk']}/100**\n\n"
        f"**Main watch-out:** {report['warnings'][0]}"
    )


# =========================================================
# HERO
# =========================================================

st.markdown(
    """
<div class="hero">

<h1>🚀 AlphaPilot Copilot</h1>

<p>
Turn Binance market data into explainable crypto intelligence.
</p>

<span class="badge">
BINANCE AGENT OS • MCP-FIRST • ANALYTICS
</span>

</div>
""",
    unsafe_allow_html=True,
)


# =========================================================
# CHAT
# =========================================================

st.subheader("🤖 AlphaPilot Copilot")

st.caption(
    "Ask AlphaPilot about BTCUSDT, SOLUSDT, ETHUSDT, BNBUSDT..."
)


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

        try:

            with st.spinner(
                f"Analyzing {symbol}..."
            ):

                snap, report = run_analysis(
                    symbol
                )

                response = answer_question(
                    prompt,
                    symbol,
                    report,
                )

            st.markdown(response)

            if snap.get("source") == "Binance Agent OS MCP":

                st.success(
                    "🔌 Binance Agent OS MCP market-data path active."
                )

            else:

                st.warning(
                    "⚠️ Authenticated Binance Agentic MCP is not "
                    "connected to this Streamlit app yet. "
                    "Using Binance public market data."
                )

        except Exception as exc:

            response = (
                f"❌ Could not analyze **{symbol}**.\n\n"
                f"`{exc}`"
            )

            st.error(response)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
        }
    )


# =========================================================
# QUICK ANALYSIS
# =========================================================

st.divider()

st.subheader("⚡ Quick Market Analysis")

symbol_input = st.text_input(
    "Binance Symbol",
    value=st.session_state.last_symbol,
)


analyze_button = st.button(
    "🔎 Analyze Market",
    type="primary",
    use_container_width=True,
)


if analyze_button:

    symbol = symbol_input.upper().strip()

    try:

        with st.spinner(
            f"Querying Binance market data for {symbol}..."
        ):

            snap, report = run_analysis(
                symbol
            )

        m = report["metrics"]

        # ---------------------------------------------
        # SOURCE
        # ---------------------------------------------

        if snap.get("source") == "Binance Agent OS MCP":

            st.success(
                "🔌 Binance Agent OS MCP connected."
            )

        else:

            st.warning(
                "⚠️ Using Binance public market data. "
                "Authenticated Agentic MCP is not connected "
                "to this Streamlit app yet."
            )

        # ---------------------------------------------
        # METRICS
        # ---------------------------------------------

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

        # ---------------------------------------------
        # SCORE
        # ---------------------------------------------

        st.divider()

        left, right = st.columns(2)

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

            st.subheader(
                "🛡️ Risk Scanner"
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

        # ---------------------------------------------
        # CHART
        # ---------------------------------------------

        st.subheader(
            "📈 Price & Activity"
        )

        k = snap["klines"]

        fig = go.Figure(
            go.Candlestick(
                x=k["open_time"],
                open=k["open"],
                high=k["high"],
                low=k["low"],
                close=k["close"],
                name=symbol,
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

        # ---------------------------------------------
        # SIGNAL MATRIX
        # ---------------------------------------------

        st.subheader(
            "🔎 Signal Matrix"
        )

        cols = st.columns(4)

        for col, (name, value) in zip(
            cols,
            [
                ("Momentum", m["momentum"]),
                ("Volume", m["volume"]),
                ("Liquidity", m["liquidity"]),
                ("Sentiment", m["sentiment"]),
            ],
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

        # ---------------------------------------------
        # EXPLANATION / RISK
        # ---------------------------------------------

        left, right = st.columns(2)

        with left:

            st.markdown(
                '<div class="card">',
                unsafe_allow_html=True,
            )

            st.subheader(
                "🧠 Why this score?"
            )

            st.markdown(
                f"**Momentum — {m['momentum']}/100**"
            )
            st.progress(
                m["momentum"] / 100
            )

            st.markdown(
                f"**Volume — {m['volume']}/100**"
            )
            st.progress(
                m["volume"] / 100
            )

            st.markdown(
                f"**Liquidity — {m['liquidity']}/100**"
            )
            st.progress(
                m["liquidity"] / 100
            )

            st.markdown(
                f"**Sentiment — {m['sentiment']}/100**"
            )
            st.progress(
                m["sentiment"] / 100
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

            for warning in report["warnings"]:

                st.warning(
                    "⚠ " + warning
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

        st.info(
            "Alpha Score is a transparent heuristic for this "
            "hackathon prototype. It is not financial advice "
            "or a guaranteed prediction."
        )

    except Exception as exc:

        st.error(
            f"Could not analyze {symbol}."
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
