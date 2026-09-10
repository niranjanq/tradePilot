from __future__ import annotations

import uuid

from tradepilot.memory.store import TradeMemory
from tradepilot.schemas import MarketSnapshot, TradeRecord


def post_trade_analysis(trade: TradeRecord) -> dict:
    """Create a structured, auditable lesson from a closed trade.

    This starter implementation deliberately uses deterministic rules. An LLM-based
    reflection node can be layered on later to enrich the explanation, while the
    stored outcome and P&L remain source-of-truth data.
    """
    if trade.outcome == "OPEN":
        raise ValueError("Trade must be closed before post-trade analysis.")

    root_cause = "THESIS_SUCCESS" if trade.outcome == "PROFIT" else "THESIS_FAILURE"
    lesson = (
        "The trade thesis produced the expected direction; retain the setup as a candidate pattern."
        if trade.outcome == "PROFIT"
        else "The trade lost money; compare this market setup with future candidates before repeating it."
    )
    return {
        "root_cause": root_cause,
        "thesis_correct": trade.outcome == "PROFIT",
        "lesson": lesson,
        "confidence": 0.50,
    }


def close_and_learn(memory: TradeMemory, trade: TradeRecord, exit_market: MarketSnapshot) -> TradeRecord:
    from tradepilot.execution.paper import PaperExecutionEngine

    closed = PaperExecutionEngine().close_position(trade, exit_market)
    analysis = post_trade_analysis(closed)
    closed.post_trade_analysis = analysis
    memory.save_episode(closed.model_dump())
    memory.add_lesson(
        lesson_id=f"L-{uuid.uuid4().hex[:10]}",
        lesson=analysis["lesson"],
        confidence=analysis["confidence"],
        source_trade_ids=[closed.trade_id],
    )
    return closed
