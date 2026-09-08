from scoring import compute

def analyze(data):
    s = compute(data)
    explanation = (
        f"The Alpha Score is {s['score']}/100 because short-term momentum is "
        f"{s['momentum_label'].lower()}, volume activity is {s['volume_label'].lower()}, "
        f"and order-book pressure is {s['pressure_label'].lower()}. "
        f"The current regime is {s['regime']}."
    )
    risks = [
        "Short-term momentum can reverse quickly in volatile crypto markets.",
        "Order-book pressure is a snapshot and can change rapidly.",
        "A volume spike without sustained price follow-through can be a false signal."
    ]
    risk_brief = (
        f"{data['symbol']} is currently in a {s['regime'].lower()} regime. "
        f"Momentum is {s['momentum_label'].lower()} and volume is {s['volume_label'].lower()}. "
        "Treat the score as decision support, not a trading instruction."
    )
    invalidations = [
        "Momentum turns materially negative on the next candle sequence.",
        "Sell-side order-book pressure becomes dominant.",
        "Price falls while volume expands, indicating stronger downside participation."
    ]
    return {**s, "explanation": explanation, "risks": risks,
            "risk_brief": risk_brief, "invalidations": invalidations}
