from __future__ import annotations

from typing import Any, Annotated, Literal, TypedDict
import operator
from pydantic import BaseModel, Field

Signal = Literal["BUY", "SELL", "HOLD"]
MasterStatus = Literal["FINALIZE", "REANALYZE", "NO_TRADE"]


class MarketSnapshot(BaseModel):
    asset: str
    price: float
    volume: float = 0.0
    avg_volume: float = 0.0
    rsi: float | None = None
    trend: str = "unknown"
    volatility: str = "unknown"
    news_sentiment: float | None = None
    timestamp: str | None = None


class AgentReport(BaseModel):
    analyst: str
    signal: Signal
    confidence: float = Field(ge=0.0, le=1.0)
    thesis: str
    evidence: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    approved: bool
    reason: str
    risk_per_trade: float
    position_fraction: float
    max_loss: float
    suggested_quantity: int = 0
    stop_loss: float | None = None
    take_profit: float | None = None


class MasterDecision(BaseModel):
    status: MasterStatus
    signal: Signal = "HOLD"
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    missing_evidence: list[str] = Field(default_factory=list)
    targeted_questions: dict[str, list[str]] = Field(default_factory=dict)


class TradeRecord(BaseModel):
    trade_id: str
    asset: str
    side: Literal["BUY", "SELL"]
    entry_price: float
    exit_price: float | None = None
    quantity: int
    pnl: float = 0.0
    pnl_pct: float = 0.0
    outcome: Literal["OPEN", "PROFIT", "LOSS", "BREAKEVEN"] = "OPEN"
    thesis: str
    market_snapshot: dict[str, Any]
    agent_reports: list[dict[str, Any]]
    master_decision: dict[str, Any]
    post_trade_analysis: dict[str, Any] | None = None


class TradingState(TypedDict, total=False):
    cycle_id: str
    asset: str
    capital: float
    market: MarketSnapshot
    memory_context: dict[str, Any]
    # Parallel analyst branches write concurrently; LangGraph merges by dict union.
    reports: Annotated[dict[str, AgentReport], operator.or_]
    master_decision: MasterDecision
    risk_assessment: RiskAssessment
    trade: TradeRecord
    execution_result: dict[str, Any]
    analysis_round: int
    max_analysis_rounds: int
    targeted_questions: dict[str, list[str]]
    final_status: str
