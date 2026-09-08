def clamp(x): return max(0,min(100,float(x)))
def pct_return(close,p):
    if len(close)<=p:return 0.0
    return (close.iloc[-1]/close.iloc[-1-p]-1)*100

def compute(snap):
    t,k,ob=snap["ticker"],snap["klines"],snap["order_book"]; close,volume=k["close"],k["quote_volume"]
    change=float(t.get("priceChangePercent",0)); mom6=pct_return(close,6); mom24=pct_return(close,min(24,len(close)-1))
    baseline=volume.iloc[-25:-1].mean() if len(volume)>25 else volume.mean(); vr=float(volume.iloc[-1]/baseline) if baseline else 1
    ret=close.pct_change().dropna()*100; vol=float(ret.tail(24).std()) if len(ret)>1 else 0
    last=float(close.iloc[-1]); rng=(float(k["high"].tail(24).max())-float(k["low"].tail(24).min()))/last*100
    bids=sum(float(x[1]) for x in ob.get("bids",[])); asks=sum(float(x[1]) for x in ob.get("asks",[])); imb=((bids-asks)/(bids+asks)*100) if bids+asks else 0
    momentum=clamp(50+mom6*7+mom24*2+change*1.5); volume_score=clamp(50+(vr-1)*30); liquidity=clamp(50+imb*2); sentiment=clamp(50+change*2+(vr-1)*10); risk=clamp(35+vol*12+rng*1.2)
    alpha=.30*momentum+.20*volume_score+.20*sentiment+.15*liquidity+.15*(100-risk)
    regime="Bullish" if alpha>=75 else "Constructive" if alpha>=60 else "Neutral" if alpha>=45 else "Cautious" if alpha>=30 else "Bearish"
    return dict(alpha_score=round(alpha),regime=regime,momentum=round(momentum),volume=round(volume_score),liquidity=round(liquidity),sentiment=round(sentiment),risk=round(risk),price=last,change=change,volume_ratio=vr,range24=rng,imbalance=imb)
