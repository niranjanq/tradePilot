from __future__ import annotations

from collections import Counter

from tradepilot.planning import build_plan
from tradepilot.schemas import AgentReport, MasterDecision, TradingState


def master_node(state: TradingState) -> dict:
    reports: dict[str, AgentReport] = state.get("reports", {})
    cash = float(state.get("cash_available", state.get("capital", 0.0)))
    exposure = float(state.get("portfolio_exposure", 0.0))
    plan = build_plan(
        state,
        "master",
        "Synthesize independent analyst evidence, account for available wallet capital, and decide whether evidence is sufficient to trade.",
        ["Compare analyst signals", "Check confidence and disagreement", "Check available capital and exposure", "Finalize, request targeted re-analysis, or abstain"],
        [f"Analyst reports={len(reports)}", f"Cash available={cash:.2f}", f"Portfolio exposure={exposure:.2f}"],
    )

    if not reports:
        decision = MasterDecision(status="NO_TRADE", rationale="No analyst reports available.", plan=plan)
        return {"master_decision": decision, "final_status": "NO_TRADE", "planning_trace": [plan.model_dump()]}

    votes = Counter(report.signal for report in reports.values())
    top_signal, top_count = votes.most_common(1)[0]
    avg_confidence = sum(r.confidence for r in reports.values()) / len(reports)
    disagreement = len(votes) > 1
    round_no = state.get("analysis_round", 1)
    max_rounds = state.get("max_analysis_rounds", 3)

    if cash <= 0:
        decision = MasterDecision(status="NO_TRADE", rationale="No deployable cash is available.", confidence=1.0, plan=plan)
        return {"master_decision": decision, "final_status": "NO_TRADE", "planning_trace": [plan.model_dump()]}

    if (disagreement or avg_confidence < 0.68) and round_no < max_rounds:
        questions: dict[str, list[str]] = {}
        for name, report in reports.items():
            if report.signal != top_signal:
                questions[name] = [
                    f"Reassess why your signal differs from the current consensus ({top_signal}).",
                    "Identify the strongest evidence that would invalidate your current view.",
                ]
        decision = MasterDecision(status="REANALYZE", signal="HOLD", confidence=avg_confidence,
            rationale="Analyst outputs are not sufficiently aligned for a final decision.",
            missing_evidence=["Cross-agent consensus", "Explicit invalidation conditions"], targeted_questions=questions, plan=plan)
        return {"master_decision": decision, "targeted_questions": questions, "analysis_round": round_no + 1,
                "final_status": "REANALYZE", "planning_trace": [plan.model_dump()]}

    if avg_confidence < 0.60:
        decision = MasterDecision(status="NO_TRADE", signal="HOLD", confidence=avg_confidence,
                                  rationale="Confidence remains too low after the allowed analysis rounds.", plan=plan)
        return {"master_decision": decision, "final_status": "NO_TRADE", "planning_trace": [plan.model_dump()]}

    decision = MasterDecision(status="FINALIZE", signal=top_signal, confidence=avg_confidence,
                              rationale=f"Consensus reached on {top_signal} with {top_count}/{len(reports)} aligned reports; deployable cash is {cash:.2f}.", plan=plan)  # type: ignore[arg-type]
    return {"master_decision": decision, "final_status": "FINALIZE", "planning_trace": [plan.model_dump()]}
