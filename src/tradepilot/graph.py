from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from tradepilot.agents.analyst_nodes import (
    fundamental_agent, regime_agent, risk_agent, sentiment_agent, technical_agent,
)
from tradepilot.agents.master import master_node
from tradepilot.execution.paper import PaperExecutionEngine
from tradepilot.memory.store import TradeMemory
from tradepilot.risk.engine import validate_trade
from tradepilot.schemas import MarketSnapshot, TradingState, WalletSnapshot

ANALYST_NODES = {
    "technical": technical_agent,
    "fundamental": fundamental_agent,
    "sentiment": sentiment_agent,
    "regime": regime_agent,
    "risk": risk_agent,
}


def prepare_market(state: TradingState) -> dict:
    # Broker/data-provider integration will replace this with a live wallet + market snapshot.
    wallet = state.get("wallet") or WalletSnapshot(
        cash_available=float(state.get("capital", 0.0)),
        total_equity=float(state.get("capital", 0.0)),
        source="paper",
    )
    return {
        "wallet": wallet,
        "cash_available": wallet.deployable_cash,
        "portfolio_exposure": wallet.invested_value / wallet.total_equity if wallet.total_equity else 0.0,
    }


def retrieve_memory(state: TradingState) -> dict:
    return {"memory_context": TradeMemory().retrieve(state["asset"])}


def _make_analyst_wrapper(name: str):
    fn = ANALYST_NODES[name]

    def wrapper(state: TradingState) -> dict:
        # Each parallel node returns only its own report. The StateGraph reducer merges them.
        return fn(state)

    wrapper.__name__ = f"run_{name}_agent"
    return wrapper


def fan_out_analysts(state: TradingState) -> list[Send]:
    return [Send(f"{name}_agent", state) for name in ANALYST_NODES]


def route_master(state: TradingState) -> Literal["risk_gate", "fan_out", "end"]:
    status = state.get("final_status")
    if status == "FINALIZE":
        return "risk_gate"
    if status == "REANALYZE":
        return "fan_out"
    return "end"


def risk_gate(state: TradingState) -> dict:
    decision = state["master_decision"]
    risk = validate_trade(
        signal=decision.signal,
        capital=float(state.get("cash_available", state.get("capital", 0.0))),
        market=state["market"],
    )
    return {"risk_assessment": risk, "final_status": "RISK_APPROVED" if risk.approved else "NO_TRADE"}


def route_risk(state: TradingState) -> Literal["execute_paper", "end"]:
    return "execute_paper" if state["risk_assessment"].approved else "end"


def execute_paper(state: TradingState) -> dict:
    decision = state["master_decision"]
    risk = state["risk_assessment"]
    trade = PaperExecutionEngine().open_position(
        asset=state["asset"], side=decision.signal, quantity=risk.suggested_quantity,
        market=state["market"], thesis=decision.rationale,
        reports=[r.model_dump() for r in state["reports"].values()], master=decision.model_dump(),
    )
    return {"trade": trade, "execution_result": {"mode": "paper", "status": "OPEN", "trade_id": trade.trade_id}, "final_status": "EXECUTED_PAPER"}


def record_memory(state: TradingState) -> dict:
    trade = state.get("trade")
    if trade is not None:
        TradeMemory().save_episode(trade.model_dump())
    return {}


def build_graph():
    graph = StateGraph(TradingState)
    graph.add_node("prepare_market", prepare_market)
    graph.add_node("retrieve_memory", retrieve_memory)
    graph.add_node("fan_out", lambda state: {})
    graph.add_node("master", master_node)
    graph.add_node("risk_gate", risk_gate)
    graph.add_node("execute_paper", execute_paper)
    graph.add_node("record_memory", record_memory)
    for name in ANALYST_NODES:
        graph.add_node(f"{name}_agent", _make_analyst_wrapper(name))

    graph.add_edge(START, "prepare_market")
    graph.add_edge("prepare_market", "retrieve_memory")
    graph.add_conditional_edges("retrieve_memory", fan_out_analysts)
    for name in ANALYST_NODES:
        graph.add_edge(f"{name}_agent", "master")
    graph.add_conditional_edges("master", route_master, {"risk_gate": "risk_gate", "fan_out": "fan_out", "end": END})
    graph.add_conditional_edges("fan_out", fan_out_analysts)
    graph.add_conditional_edges("risk_gate", route_risk, {"execute_paper": "execute_paper", "end": END})
    graph.add_edge("execute_paper", "record_memory")
    graph.add_edge("record_memory", END)
    return graph.compile()


def demo_initial_state() -> TradingState:
    return {
        "cycle_id": "demo",
        "asset": "DEMO",
        "capital": 500.0,
        "wallet": WalletSnapshot(cash_available=500.0, total_equity=500.0, source="paper"),
        "market": MarketSnapshot(asset="DEMO", price=100.0, volume=150000, avg_volume=100000,
                                  rsi=61.0, trend="bullish", volatility="moderate", news_sentiment=0.55),
        "reports": {},
        "planning_trace": [],
        "analysis_round": 1,
        "max_analysis_rounds": 3,
    }
