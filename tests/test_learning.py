from tradepilot.execution.paper import PaperExecutionEngine
from tradepilot.memory.learning import close_and_learn
from tradepilot.memory.store import TradeMemory
from tradepilot.schemas import MarketSnapshot


def test_closed_trade_creates_memory_lesson(tmp_path):
    memory = TradeMemory(str(tmp_path / 'memory.sqlite3'))
    trade = PaperExecutionEngine().open_position(
        asset='X',
        side='BUY',
        quantity=1,
        market=MarketSnapshot(asset='X', price=100),
        thesis='breakout',
        reports=[],
        master={'status': 'FINALIZE', 'signal': 'BUY'},
    )
    closed = close_and_learn(memory, trade, MarketSnapshot(asset='X', price=110))
    context = memory.retrieve('X')
    assert closed.outcome == 'PROFIT'
    assert closed.post_trade_analysis is not None
    assert len(context['lessons']) == 1
