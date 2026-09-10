from tradepilot.graph import build_graph, demo_initial_state


def test_graph_reaches_risk_or_no_trade():
    result = build_graph().invoke(demo_initial_state())
    assert result["final_status"] in {"RISK_APPROVED", "NO_TRADE"}
    assert result["master_decision"].status in {"FINALIZE", "REANALYZE", "NO_TRADE"}
