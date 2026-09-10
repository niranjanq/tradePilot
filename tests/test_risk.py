from tradepilot.risk.engine import validate_trade
from tradepilot.schemas import MarketSnapshot


def test_risk_gate_blocks_hold():
    market = MarketSnapshot(asset="X", price=100, trend="bullish")
    result = validate_trade(signal="HOLD", capital=500, market=market)
    assert result.approved is False


def test_risk_gate_respects_small_capital():
    market = MarketSnapshot(asset="X", price=100, trend="bullish")
    result = validate_trade(signal="BUY", capital=500, market=market)
    assert result.approved is True
    assert result.suggested_quantity == 1
