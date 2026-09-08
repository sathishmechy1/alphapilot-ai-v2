from .scoring import compute

def analyze(symbol, snap):
    s = compute(snap)
    positives, warnings = [], []
    if s["momentum"] >= 70: positives.append("strong short-term momentum")
    elif s["momentum"] < 40: warnings.append("weak short-term momentum")
    if s["volume"] >= 65: positives.append("above-baseline trading activity")
    elif s["volume"] < 40: warnings.append("muted volume")
    if s["liquidity"] >= 65: positives.append("supportive order-book imbalance")
    elif s["liquidity"] < 40: warnings.append("sell-side order-book pressure")
    if s["risk"] >= 70: warnings.append("elevated volatility risk")
    elif s["risk"] <= 40: positives.append("relatively contained volatility")
    if not positives: positives.append("mixed market signals")
    if not warnings: warnings.append("no major risk flag from the current snapshot")
    summary = (f"{symbol} scores {s['alpha_score']}/100 and is currently {s['regime'].lower()}. "
               f"Strongest signals: {', '.join(positives[:2])}. "
               f"Main watch-outs: {', '.join(warnings[:2])}.")
    return {"metrics": s, "positives": positives, "warnings": warnings, "summary": summary}
