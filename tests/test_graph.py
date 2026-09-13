from tradepilot.graph import build_graph, demo_initial_state
from tradepilot.schemas import WalletSnapshot


def test_graph_reaches_risk_or_paper_execution_or_no_trade():
    result = build_graph().invoke(demo_initial_state())
    assert result["final_status"] in {"RISK_APPROVED", "EXECUTED_PAPER", "NO_TRADE"}
    assert result["master_decision"].status in {"FINALIZE", "REANALYZE", "NO_TRADE"}


def test_wallet_is_visible_to_master_and_analysts():
    state = demo_initial_state()
    state["wallet"] = WalletSnapshot(cash_available=120.0, total_equity=500.0, invested_value=380.0)
    result = build_graph().invoke(state)
    assert result["cash_available"] in {0.0, 120.0}
    assert result["planning_trace"]
    assert all("capital_available" in trace for trace in result["planning_trace"])


def test_zero_wallet_cash_abstains():
    state = demo_initial_state()
    state["wallet"] = WalletSnapshot(cash_available=0.0, total_equity=500.0, invested_value=500.0)
    result = build_graph().invoke(state)
    assert result["final_status"] == "NO_TRADE"
    assert result["master_decision"].status == "NO_TRADE"


def test_paper_fill_reduces_cash_and_increases_exposure():
    result = build_graph().invoke(demo_initial_state())
    if result["final_status"] == "EXECUTED_PAPER":
        assert result["execution_result"]["remaining_cash"] < 500.0
        assert result["wallet"].invested_value > 0.0
        assert result["portfolio_exposure"] > 0.0
