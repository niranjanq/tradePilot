from __future__ import annotations

from tradepilot.schemas import AgentPlan, TradingState


def build_plan(state: TradingState, node: str, objective: str, actions: list[str], inputs: list[str]) -> AgentPlan:
    return AgentPlan(
        node=node,
        objective=objective,
        capital_available=float(state.get("cash_available", state.get("capital", 0.0))),
        portfolio_exposure=float(state.get("portfolio_exposure", 0.0)),
        inputs_considered=inputs,
        actions=actions,
        constraints=[
            "Capital availability must be respected.",
            "No trade is executed before deterministic risk validation.",
            "Planning is observable; private chain-of-thought is not persisted.",
        ],
    )
