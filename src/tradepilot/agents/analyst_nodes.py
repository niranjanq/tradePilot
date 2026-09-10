from __future__ import annotations

from tradepilot.schemas import AgentReport, TradingState

ANALYSTS = ("technical", "fundamental", "sentiment", "regime", "risk")


def _targeted(state: TradingState, analyst: str) -> list[str]:
    return state.get("targeted_questions", {}).get(analyst, [])


def technical_agent(state: TradingState) -> dict:
    m = state["market"]
    trend = m.trend.lower()
    signal = "BUY" if trend == "bullish" else "SELL" if trend == "bearish" else "HOLD"
    report = AgentReport(
        analyst="technical",
        signal=signal,
        confidence=0.78 if signal != "HOLD" else 0.55,
        thesis=f"Price/trend structure is currently {m.trend}.",
        evidence=[f"Trend={m.trend}", f"RSI={m.rsi}"],
        risks=[f"Volatility={m.volatility}"],
        questions=_targeted(state, "technical"),
    )
    return {"reports": {"technical": report}}


def fundamental_agent(state: TradingState) -> dict:
    m = state["market"]
    signal = "BUY" if m.news_sentiment is not None and m.news_sentiment > 0.25 else "HOLD"
    report = AgentReport(
        analyst="fundamental",
        signal=signal,
        confidence=0.62 if signal == "BUY" else 0.50,
        thesis="Starter implementation treats positive external sentiment as a placeholder fundamental proxy.",
        evidence=[f"News sentiment proxy={m.news_sentiment}"],
        risks=["Real fundamental feeds are not wired yet."],
        questions=_targeted(state, "fundamental"),
    )
    return {"reports": {"fundamental": report}}


def sentiment_agent(state: TradingState) -> dict:
    m = state["market"]
    sentiment = m.news_sentiment or 0.0
    signal = "BUY" if sentiment > 0.30 else "SELL" if sentiment < -0.30 else "HOLD"
    report = AgentReport(
        analyst="sentiment",
        signal=signal,
        confidence=min(0.9, 0.5 + abs(sentiment) * 0.4),
        thesis=f"External sentiment proxy is {sentiment:.2f}.",
        evidence=[f"Sentiment={sentiment:.2f}"],
        risks=["Headline sentiment can change rapidly."],
        questions=_targeted(state, "sentiment"),
    )
    return {"reports": {"sentiment": report}}


def regime_agent(state: TradingState) -> dict:
    m = state["market"]
    state_name = "BULLISH" if m.trend == "bullish" else "BEARISH" if m.trend == "bearish" else "SIDEWAYS"
    signal = "BUY" if state_name == "BULLISH" else "SELL" if state_name == "BEARISH" else "HOLD"
    report = AgentReport(
        analyst="regime",
        signal=signal,
        confidence=0.72,
        thesis=f"Detected market regime: {state_name}.",
        evidence=[f"Trend={m.trend}", f"Volatility={m.volatility}"],
        risks=["Regime classifications are provisional in the starter version."],
        questions=_targeted(state, "regime"),
    )
    return {"reports": {"regime": report}}


def risk_agent(state: TradingState) -> dict:
    m = state["market"]
    blocked = m.volatility.lower() == "extreme"
    report = AgentReport(
        analyst="risk",
        signal="HOLD" if blocked else "BUY" if m.trend == "bullish" else "SELL" if m.trend == "bearish" else "HOLD",
        confidence=0.85 if not blocked else 0.92,
        thesis="Risk analyst checks whether market conditions are broadly tradeable.",
        evidence=[f"Volatility={m.volatility}"],
        risks=["Extreme volatility blocks new trades." if blocked else "Risk limits are finalized by deterministic risk engine."],
        questions=_targeted(state, "risk"),
    )
    return {"reports": {"risk": report}}
