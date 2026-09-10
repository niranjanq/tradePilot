from __future__ import annotations

import uuid

from tradepilot.schemas import MarketSnapshot, TradeRecord


class PaperExecutionEngine:
    """Deterministic paper executor. It never calls a broker."""

    def open_position(self, *, asset: str, side: str, quantity: int, market: MarketSnapshot, thesis: str, reports: list[dict], master: dict) -> TradeRecord:
        return TradeRecord(
            trade_id=f"PAPER-{uuid.uuid4().hex[:10]}",
            asset=asset,
            side=side,  # type: ignore[arg-type]
            entry_price=market.price,
            quantity=quantity,
            thesis=thesis,
            market_snapshot=market.model_dump(),
            agent_reports=reports,
            master_decision=master,
        )

    def close_position(self, trade: TradeRecord, market: MarketSnapshot) -> TradeRecord:
        trade.exit_price = market.price
        gross = (market.price - trade.entry_price) * trade.quantity
        trade.pnl = gross if trade.side == "BUY" else -gross
        trade.pnl_pct = (trade.pnl / (trade.entry_price * trade.quantity)) * 100
        if trade.pnl > 0:
            trade.outcome = "PROFIT"
        elif trade.pnl < 0:
            trade.outcome = "LOSS"
        else:
            trade.outcome = "BREAKEVEN"
        return trade
