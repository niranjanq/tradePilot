from __future__ import annotations

from pprint import pprint

from tradepilot.graph import build_graph, demo_initial_state


def main() -> None:
    graph = build_graph()
    result = graph.invoke(demo_initial_state())
    pprint({
        "status": result.get("final_status"),
        "round": result.get("analysis_round"),
        "master": result.get("master_decision").model_dump() if result.get("master_decision") else None,
        "risk": result.get("risk_assessment").model_dump() if result.get("risk_assessment") else None,
        "execution": result.get("execution_result"),
    })


if __name__ == "__main__":
    main()
