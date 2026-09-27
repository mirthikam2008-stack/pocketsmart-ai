"""
schemas_v2.py
Domain models and structured output schemas for Predictive Cash Flow Forecasting
and Autonomous Multi-Agent Debt Negotiation.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class CashFlowForecastPoint(BaseModel):
    day_offset: int = Field(description="Forward-looking day offset from baseline (1 to 90)")
    projected_balance: float = Field(description="Projected net checking/cash balance in USD")
    lower_bound: float = Field(description="Conservative lower bound (p10 confidence)")
    upper_bound: float = Field(description="Optimistic upper bound (p90 confidence)")
    is_deficit_risk: bool = Field(description="True if projected balance drops below safety reserve")


class PredictiveCashFlowReport(BaseModel):
    baseline_balance: float = Field(description="Starting cash balance at day 0")
    forecast_horizon_days: int = Field(description="Projection period (30 or 90 days)")
    projected_end_balance: float = Field(description="Estimated cash balance at end of horizon")
    burn_rate_daily: float = Field(description="Average daily net cash burn or accumulation")
    earliest_deficit_day: Optional[int] = Field(default=None, description="First day balance breaches zero, if any")
    forecast_trajectory: List[CashFlowForecastPoint] = Field(description="Granular daily forecast coordinates")
    ai_risk_assessment: str = Field(description="Executive qualitative risk summary from Gemini 3.7 Pro")


class DebtItem(BaseModel):
    creditor_name: str = Field(description="Financial institution or loan servicer")
    debt_type: Literal["CREDIT_CARD", "PERSONAL_LOAN", "AUTO_LOAN", "STUDENT_LOAN", "MEDICAL"] = Field(
        description="Classification of debt liability"
    )
    current_balance: float = Field(gt=0, description="Total balance currently owed in USD")
    annual_percentage_rate: float = Field(ge=0, description="Current annual interest rate (e.g., 24.99)")
    minimum_monthly_payment: float = Field(ge=0, description="Required monthly minimum installment")
    months_delinquent: int = Field(default=0, ge=0, description="Months past due (0 if in good standing)")


class NegotiationStrategy(BaseModel):
    strategy_type: Literal["APR_REDUCTION", "HARDSHIP_FORBEARANCE", "LUMP_SUM_SETTLEMENT"] = Field(
        description="Selected negotiation posture"
    )
    target_apr: Optional[float] = Field(default=None, description="Proposed reduced APR percentage")
    proposed_settlement_pct: Optional[float] = Field(
        default=None, description="Proposed settlement percentage of total balance"
    )
    target_monthly_relief_usd: float = Field(description="Projected monthly cash flow liberated")


class CreditorNegotiationDossier(BaseModel):
    creditor_name: str = Field(description="Target creditor or servicer")
    recommended_strategy: NegotiationStrategy = Field(description="Strategy chosen based on cashflow analysis")
    formal_letter_body: str = Field(description="Complete, legally styled negotiation correspondence")
    talking_points: List[str] = Field(description="Key bullet points for phone or chat representative dialogue")
    regulatory_disclaimer: str = Field(description="Mandatory consumer financial rights and fiduciary disclosure")
