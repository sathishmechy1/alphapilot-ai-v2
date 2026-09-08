def compute(data):
    change = data["change_pct"]
    pressure = data["pressure"]
    vr = data["volume_ratio"]
    closes = data["closes"]
    momentum = (closes[-1] / closes[-20] - 1) * 100 if len(closes) >= 20 else change

    score = 50
    score += max(-20, min(20, momentum * 4))
    score += max(-10, min(10, (pressure - 1) * 30))
    score += max(-10, min(10, (vr - 1) * 12))
    score = int(max(0, min(100, round(score))))

    regime = ("Constructive" if score >= 70 else
              "Cautious Positive" if score >= 55 else
              "Neutral / Cautious" if score >= 40 else "Defensive")
    momentum_label = ("Strong" if momentum > 2 else "Positive" if momentum > 0.5
                      else "Weak" if momentum < -1 else "Flat")
    volume_label = "High" if vr > 1.25 else "Normal" if vr >= 0.8 else "Low"
    pressure_label = ("Buy-side" if pressure > 1.08 else
                      "Sell-side" if pressure < 0.92 else "Balanced")
    risk_label = ("High" if score < 40 or abs(change) > 7 else
                  "Medium" if score < 60 else "Lower")

    return {"score": score, "regime": regime, "momentum": momentum,
            "momentum_label": momentum_label, "volume_label": volume_label,
            "pressure_label": pressure_label, "risk_label": risk_label}
