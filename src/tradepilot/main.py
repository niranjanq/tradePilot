from __future__ import annotations

import argparse
from pprint import pprint

from tradepilot.graph import build_graph, demo_initial_state
from tradepilot.simulation import SCENARIOS, get_scenario, wallet_summary


def _money(value: float, currency: str = "INR") -> str:
    return f"{currency} {value:,.2f}"


def _print_plan(label: str, plan: dict) -> None:
    print(f"\n{label.upper()}")
    print("-" * 72)
    print(f"Objective: {plan.get('objective', '-')}")
    print(f"Capital available: {_money(float(plan.get('capital_available', 0.0)))}")
    print(f"Portfolio exposure: {float(plan.get('portfolio_exposure', 0.0)) * 100:.1f}%")
    for title, key in (("Inputs", "inputs_considered"), ("Actions", "actions"), ("Constraints", "constraints")):
        values = plan.get(key) or []
        print(f"{title}:")
        for value in values:
            print(f"  • {value}")


def print_simulation(result: dict, scenario_name: str) -> None:
    wallet = result.get("wallet")
    print("=" * 72)
    print("TRADEPILOT — PAPER SIMULATION")
    print(f"Scenario: {scenario_name}")
    print("=" * 72)

    if wallet is not None:
        summary = wallet_summary(wallet)
        print("\nWALLET")
        print("-" * 72)
        print(f"Total equity:      {_money(summary['total_equity'], summary['currency'])}")
        print(f"Cash available:    {_money(summary['cash_available'], summary['currency'])}")
        print(f"Invested value:    {_money(summary['invested_value'], summary['currency'])}")
        print(f"Reserved amount:   {_money(summary['reserved_amount'], summary['currency'])}")
        print(f"Deployable cash:   {_money(summary['deployable_cash'], summary['currency'])}")
        print(f"Portfolio exposure:{float(result.get('portfolio_exposure', 0.0)) * 100:6.1f}%")

    reports = result.get("reports", {}) or {}
    for name in ("technical", "fundamental", "sentiment", "regime", "risk"):
        report = reports.get(name)
        if not report:
            continue
        data = report.model_dump() if hasattr(report, "model_dump") else report
        print(f"\n{name.upper()} ANALYST")
        print("-" * 72)
        print(f"Signal: {data.get('signal', '-')}")
        print(f"Confidence: {float(data.get('confidence', 0.0)) * 100:.1f}%")
        print(f"Thesis: {data.get('thesis', '-')}")
        if data.get("evidence"):
            print("Evidence:")
            for item in data["evidence"]:
                print(f"  • {item}")
        if data.get("risks"):
            print("Risks:")
            for item in data["risks"]:
                print(f"  • {item}")
        if data.get("plan"):
            _print_plan("Planning", data["plan"])

    master = result.get("master_decision")
    if master:
        data = master.model_dump() if hasattr(master, "model_dump") else master
        print("\nMASTER")
        print("-" * 72)
        print(f"Decision: {data.get('status', '-')}")
        print(f"Signal: {data.get('signal', '-')}")
        print(f"Confidence: {float(data.get('confidence', 0.0)) * 100:.1f}%")
        print(f"Rationale: {data.get('rationale', '-')}")
        if data.get("plan"):
            _print_plan("Strategy plan", data["plan"])

    risk = result.get("risk_assessment")
    if risk:
        data = risk.model_dump() if hasattr(risk, "model_dump") else risk
        print("\nDETERMINISTIC RISK GATE")
        print("-" * 72)
        print(f"Approved: {data.get('approved')}")
        print(f"Maximum loss: {_money(float(data.get('max_loss', 0.0)))}")
        print(f"Position fraction: {float(data.get('position_fraction', 0.0)) * 100:.1f}%")
        print(f"Suggested quantity: {data.get('suggested_quantity', 0)}")
        print(f"Stop loss: {data.get('stop_loss', '-')}")
        print(f"Take profit: {data.get('take_profit', '-')}")
        print(f"Reason: {data.get('reason', '-')}")

    execution = result.get("execution_result")
    if execution:
        print("\nEXECUTION")
        print("-" * 72)
        print(f"Mode: {execution.get('mode', '-')}")
        print(f"Status: {execution.get('status', '-')}")
        print(f"Trade ID: {execution.get('trade_id', '-')}")

    trace = result.get("planning_trace", []) or []
    print("\nPLANNING TRACE SUMMARY")
    print("-" * 72)
    print(f"Recorded plan events: {len(trace)}")
    for item in trace:
        print(
            f"  • {item.get('node', '-')}: "
            f"capital={_money(float(item.get('capital_available', 0.0)))}; "
            f"exposure={float(item.get('portfolio_exposure', 0.0)) * 100:.1f}%"
        )

    print("\nFINAL STATUS")
    print("-" * 72)
    print(result.get("final_status", "-"))
    print("=" * 72)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a TradePilot paper simulation")
    parser.add_argument(
        "--scenario",
        default="baseline",
        choices=[scenario.name for scenario in SCENARIOS],
        help="Paper wallet scenario to simulate",
    )
    parser.add_argument("--raw", action="store_true", help="Print the raw graph state instead of the formatted simulation")
    args = parser.parse_args()

    scenario = get_scenario(args.scenario)
    state = demo_initial_state()
    state["wallet"] = scenario.wallet
    graph = build_graph()
    result = graph.invoke(state)

    if args.raw:
        pprint(result)
    else:
        print_simulation(result, scenario.name)


if __name__ == "__main__":
    main()
