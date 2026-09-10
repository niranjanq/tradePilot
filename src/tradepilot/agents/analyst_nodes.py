from __future__ import annotations

from tradepilot.planning import build_plan
from tradepilot.schemas import AgentReport, TradingState

ANALYSTS = ("technical", "fundamental", "sentiment", "regime", "risk")


def _targeted(state: TradingState, analyst: str) -> list[str]:
    return state.get("targeted_questions", {}).get(analyst, [])


def _report(state: TradingState, name: str, signal: str, confidence: float, thesis: str, evidence: list[str], risks: list[str]) -> dict:
    plan = build_plan(
        state,
        name,
        f"Evaluate {state['asset']} and determine whether {name} evidence supports a trade.",
        ["Inspect supplied market and wallet state", "Evaluate node-specific evidence", "Return a structured signal and risks"],
        evidence + [f"Cash available={state.get('cash_available', state.get('capital', 0.0)):.2f}"],
    )
    report = AgentReport(
        analyst=name,
        signal=signal,  # type: ignore[arg-type]
        confidence=confidence,
        thesis=thesis,
        evidence=evidence,
        risks=risks,
        questions=_targeted(state, name),
        plan=plan,
    )
    return {"reports": {name: report}, "planning_trace": [plan.model_dump()]}


def technical_agent(state: TradingState) -> dict:
    m = state["market"]
    trend = m.trend.lower()
    signal = "BUY" if trend == "bullish" else "SELL" if trend == "bearish" else "HOLD"
    return _report(state, "technical", signal, 0.78 if signal != "HOLD" else 0.55, f"Price/trend structure is currently {m.trend}.", [f"Trend={m.trend}", f"RSI={m.rsi}"], [f"Volatility={m.volatility}"])


def fundamental_agent(state: TradingState) -> dict:
    m = state["market"]
    signal = "BUY" if m.news_sentiment is not None and m.news_sentiment > 0.25 else "HOLD"
    return _report(state, "fundamental", signal, 0.62 if signal == "BUY" else 0.50, "Starter implementation treats positive external sentiment as a placeholder fundamental proxy.", [f"News sentiment proxy={m.news_sentiment}"], ["Real fundamental feeds are not wired yet."])


def sentiment_agent(state: TradingState) -> dict:
    m = state["market"]
    sentiment = m.news_sentiment or 0.0
    signal = "BUY" if sentiment > 0.30 else "SELL" if sentiment < -0.30 else "HOLD"
    return _report(state, "sentiment", signal, min(0.9, 0.5 + abs(sentiment) * 0.4), f"External sentiment proxy is {sentiment:.2f}.", [f"Sentiment={sentiment:.2f}"], ["Headline sentiment can change rapidly."])


def regime_agent(state: TradingState) -> dict:
    m = state["market"]
    state_name = "BULLISH" if m.trend == "bullish" else "BEARISH" if m.trend == "bearish" else "SIDEWAYS"
    signal = "BUY" if state_name == "BULLISH" else "SELL" if state_name == "BEARISH" else "HOLD"
    return _report(state, "regime", signal, 0.72, f"Detected market regime: {state_name}.", [f"Trend={m.trend}", f"Volatility={m.volatility}"], ["Regime classifications are provisional in the starter version."])


def risk_agent(state: TradingState) -> dict:
    m = state["market"]
    blocked = m.volatility.lower() == "extreme"
    signal = "HOLD" if blocked else "BUY" if m.trend == "bullish" else "SELL" if m.trend == "bearish" else "HOLD"
    return _report(state, "risk", signal, 0.85 if not blocked else 0.92, "Risk analyst checks whether market conditions and available capital are broadly tradeable.", [f"Volatility={m.volatility}", f"Deployable cash={state.get('cash_available', state.get('capital', 0.0)):.2f}"], ["Extreme volatility blocks new trades." if blocked else "Final limits are enforced by the deterministic risk engine."])
