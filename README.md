# TradePilot

TradePilot is a **LangGraph-based autonomous trading research and paper-trading system** designed around a parallel analyst architecture.

```text
Market + Wallet state
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

## Wallet-aware planning

Every graph cycle starts with a `WalletSnapshot`. The Master and every analyst can see deployable cash, total equity, invested value, reserved funds, and portfolio exposure. This allows the planning layer to explicitly account for available capital before recommending a trade.

The wallet is currently backed by the paper portfolio. A future broker adapter will populate the same schema from real account/broker APIs.

## Observable agent plans

TradePilot records an auditable planning trace for each node. A trace contains:

- objective
- capital available
- portfolio exposure
- inputs considered
- planned actions
- hard constraints

This is intentionally **not raw/private chain-of-thought**. It is a concise decision/audit trace suitable for logs, a UI, debugging, and evaluation.

## Design principles

- Analysts run independently and report structured evidence.
- The master node can request **targeted re-analysis** instead of blindly repeating every analyst.
- Wallet availability is considered before a final trade reaches the risk gate.
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
│   ├── analyst_nodes.py      # parallel analyst nodes + plans
│   └── master.py              # synthesis + wallet-aware planning
├── execution/
│   └── paper.py               # deterministic paper executor
├── memory/
│   └── store.py               # SQLite episodic/lesson/statistical memory
├── risk/
│   └── engine.py              # hard risk checks and sizing
├── planning.py                # observable node planning schema/helpers
├── graph.py                   # LangGraph workflow
├── schemas.py                 # wallet, reports, plans, and state
└── main.py                    # demo entry point

tests/
├── test_graph.py
├── test_memory.py
└── test_risk.py
```

## Run

```bash
uv sync
cp .env.example .env
uv run pytest
uv run python -m tradepilot.main
```

## Important implementation note

This repo is intentionally a foundation rather than a live-money system. Before any broker integration, add historical backtesting, realistic transaction costs/slippage, paper-trading soak tests, monitoring, kill switches, broker idempotency, independent execution controls, and a live wallet adapter. Never rely on an LLM alone for capital protection or order validation.
