# TradePilot

TradePilot is a **LangGraph-based autonomous trading research and paper-trading system** designed around a parallel analyst architecture:

```text
Market state
     |
     +----> Technical analyst ----+
     +----> Fundamental analyst ---+
     +----> Sentiment analyst -----+----> Master
     +----> Regime analyst --------+       |
     +----> Risk analyst ----------+       +--> FINALIZE --> deterministic risk --> paper execution
                                          |
                                          +--> REANALYZE --> targeted analyst cycle --> Master
                                          |
                                          +--> NO_TRADE --> END
```

## Design principles

- Analysts run independently and report structured evidence.
- The master node can request **targeted re-analysis** instead of blindly repeating every analyst.
- The master cannot bypass the deterministic risk gate.
- `HOLD` / `NO_TRADE` is always a valid outcome.
- Every closed trade can be post-analyzed and stored as episodic memory.
- Reusable lessons are stored separately from raw trade episodes.
- The initial implementation is **paper-trading only**. No broker credentials or live-order code is included.
- The system makes no promise of profit and is intended for research, backtesting, and controlled validation.

## Project layout

```text
src/tradepilot/
├── agents/
│   ├── analyst_nodes.py      # parallel analyst nodes
│   └── master.py              # synthesis + re-analysis request
├── execution/
│   └── paper.py               # deterministic paper executor
├── memory/
│   └── store.py               # SQLite episodic/lesson/statistical memory
├── risk/
│   └── engine.py              # hard risk checks and sizing
├── graph.py                   # LangGraph workflow
├── schemas.py                 # shared Pydantic models / state
└── main.py                    # demo entry point

tests/
├── test_graph.py
├── test_memory.py
└── test_risk.py
```

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
cp .env.example .env
pytest
python -m tradepilot.main
```

## Important implementation note

This repo is intentionally a foundation rather than a live-money system. Before any broker integration, add historical backtesting, realistic transaction costs/slippage, paper-trading soak tests, monitoring, kill switches, broker idempotency, and independent execution controls.
# tradePilot
