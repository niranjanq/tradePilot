from __future__ import annotations

import math

from tradepilot.schemas import MarketSnapshot, RiskAssessment


def validate_trade(
    *,
    signal: str,
    capital: float,
    market: MarketSnapshot,
    max_risk_fraction: float = 0.01,
    max_position_fraction: float = 0.50,
) -> RiskAssessment:
    if signal not in {"BUY", "SELL"}:
        return RiskAssessment(
            approved=False,
            reason="Only BUY or SELL reaches the risk gate.",
            risk_per_trade=0.0,
            position_fraction=0.0,
            max_loss=0.0,
        )

    if capital <= 0 or market.price <= 0:
        return RiskAssessment(
            approved=False,
            reason="Invalid capital or market price.",
            risk_per_trade=0.0,
            position_fraction=0.0,
            max_loss=0.0,
        )

    # Conservative deterministic starter rule: risk 1% of equity with a 5% stop distance.
    stop_distance = market.price * 0.05
    max_loss = capital * max_risk_fraction
    quantity_by_risk = math.floor(max_loss / stop_distance) if stop_distance else 0
    max_notional = capital * max_position_fraction
    quantity_by_capital = math.floor(max_notional / market.price)
    quantity = max(0, min(quantity_by_risk, quantity_by_capital))

    approved = quantity >= 1
    position_fraction = (quantity * market.price) / capital if capital else 0.0
    return RiskAssessment(
        approved=approved,
        reason=("Trade passes deterministic starter limits." if approved else "Trade is too small for the configured risk limits."),
        risk_per_trade=max_risk_fraction,
        position_fraction=position_fraction,
        max_loss=max_loss,
        suggested_quantity=quantity,
        stop_loss=market.price * 0.95 if signal == "BUY" else market.price * 1.05,
        take_profit=market.price * 1.10 if signal == "BUY" else market.price * 0.90,
    )
