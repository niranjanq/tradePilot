from __future__ import annotations

from collections import Counter

from tradepilot.schemas import AgentReport, MasterDecision, TradingState


def master_node(state: TradingState) -> dict:
    reports: dict[str, AgentReport] = state.get("reports", {})
    if not reports:
        return {"master_decision": MasterDecision(status="NO_TRADE", rationale="No analyst reports available."), "final_status": "NO_TRADE"}

    votes = Counter(report.signal for report in reports.values())
    top_signal, top_count = votes.most_common(1)[0]
    avg_confidence = sum(r.confidence for r in reports.values()) / len(reports)
    disagreement = len(votes) > 1

    round_no = state.get("analysis_round", 1)
    max_rounds = state.get("max_analysis_rounds", 3)

    # First pass: disagreement or weak confidence asks for targeted analysis.
    if (disagreement or avg_confidence < 0.68) and round_no < max_rounds:
        questions: dict[str, list[str]] = {}
        for name, report in reports.items():
            if report.signal != top_signal:
                questions[name] = [
                    f"Reassess why your signal differs from the current consensus ({top_signal}).",
                    "Identify the strongest evidence that would invalidate your current view.",
                ]
        decision = MasterDecision(
            status="REANALYZE",
            signal="HOLD",
            confidence=avg_confidence,
            rationale="Analyst outputs are not sufficiently aligned for a final decision.",
            missing_evidence=["Cross-agent consensus", "Explicit invalidation conditions"],
            targeted_questions=questions,
        )
        return {
            "master_decision": decision,
            "targeted_questions": questions,
            "analysis_round": round_no + 1,
            "final_status": "REANALYZE",
        }

    if avg_confidence < 0.60:
        decision = MasterDecision(
            status="NO_TRADE",
            signal="HOLD",
            confidence=avg_confidence,
            rationale="Confidence remains too low after the allowed analysis rounds.",
        )
        return {"master_decision": decision, "final_status": "NO_TRADE"}

    decision = MasterDecision(
        status="FINALIZE",
        signal=top_signal,  # type: ignore[arg-type]
        confidence=avg_confidence,
        rationale=f"Consensus reached on {top_signal} with {top_count}/{len(reports)} aligned reports.",
    )
    return {"master_decision": decision, "final_status": "FINALIZE"}
