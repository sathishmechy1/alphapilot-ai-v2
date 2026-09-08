from scoring import compute


def analyze(symbol, snap):
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
