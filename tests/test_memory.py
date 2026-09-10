from tradepilot.memory.store import TradeMemory


def test_memory_persists_episode_and_lesson(tmp_path):
    memory = TradeMemory(str(tmp_path / "memory.sqlite3"))
    memory.save_episode({"trade_id": "T1", "asset": "X", "outcome": "LOSS", "pnl": -4.0})
    memory.add_lesson("L1", "Avoid weak-volume breakouts", 0.8, ["T1"])
    context = memory.retrieve("X")
    assert context["episodes"][0]["trade_id"] == "T1"
    assert context["lessons"][0]["lesson_id"] == "L1"
