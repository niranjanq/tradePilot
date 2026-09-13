from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tradepilot.schemas import MarketSnapshot, TradeRecord, WalletSnapshot


@dataclass(frozen=True)
class SimulationScenario:
    name: str
    description: str
    wallet: WalletSnapshot


SCENARIOS: tuple[SimulationScenario, ...] = (
    SimulationScenario(
        name="baseline",
        description="Fresh paper account with all capital available.",
        wallet=WalletSnapshot(cash_available=500.0, total_equity=500.0, invested_value=0.0),
    ),
    SimulationScenario(
        name="low_cash",
        description="Most capital is already invested; only a small amount remains deployable.",
        wallet=WalletSnapshot(cash_available=120.0, total_equity=500.0, invested_value=380.0),
    ),
    SimulationScenario(
        name="no_cash",
        description="No cash remains available for a new position.",
        wallet=WalletSnapshot(cash_available=0.0, total_equity=500.0, invested_value=500.0),
    ),
)


def get_scenario(name: str = "baseline") -> SimulationScenario:
    for scenario in SCENARIOS:
        if scenario.name == name:
            return scenario
    available = ", ".join(s.name for s in SCENARIOS)
    raise ValueError(f"Unknown simulation scenario '{name}'. Available: {available}")


def apply_paper_fill(wallet: WalletSnapshot, *, side: str, price: float, quantity: int) -> WalletSnapshot:
    """Update the simulated wallet after an opening paper fill."""
    notional = max(0.0, price * quantity)
    cash = wallet.cash_available
    invested = wallet.invested_value

    if side == "BUY":
        cash = max(0.0, cash - notional)
        invested += notional
    elif side == "SELL":
        cash += notional
        invested = max(0.0, invested - notional)

    return WalletSnapshot(
        cash_available=cash,
        total_equity=wallet.total_equity,
        invested_value=invested,
        reserved_amount=wallet.reserved_amount,
        currency=wallet.currency,
        source=wallet.source,
    )


def settle_paper_close(wallet: WalletSnapshot, trade: TradeRecord, market: MarketSnapshot) -> WalletSnapshot:
    """Return the simulated wallet after closing a paper position."""
    entry_value = trade.entry_price * trade.quantity
    exit_value = market.price * trade.quantity
    cash = wallet.cash_available + exit_value
    invested = max(0.0, wallet.invested_value - entry_value)
    pnl = trade.pnl
    equity = max(0.0, cash + invested + pnl)

    return WalletSnapshot(
        cash_available=cash,
        total_equity=equity,
        invested_value=invested,
        reserved_amount=wallet.reserved_amount,
        currency=wallet.currency,
        source=wallet.source,
    )


def wallet_summary(wallet: WalletSnapshot) -> dict[str, Any]:
    return {
        "total_equity": wallet.total_equity,
        "cash_available": wallet.cash_available,
        "invested_value": wallet.invested_value,
        "reserved_amount": wallet.reserved_amount,
        "deployable_cash": wallet.deployable_cash,
        "currency": wallet.currency,
        "source": wallet.source,
    }
