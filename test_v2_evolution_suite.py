"""
test_v2_evolution_suite.py
Automated Verification Suite for Phase 2.1 Predictive Cash Flow Forecasting
and Phase 2.2 Autonomous Multi-Agent Debt Negotiation.
"""

from schemas import UserFinancialProfile, ExpenseItem
from schemas_v2 import DebtItem, PredictiveCashFlowReport, CreditorNegotiationDossier
from services.forecast_service import calculate_deterministic_cash_flow_curve, generate_predictive_cash_flow_report
from services.debt_agent_service import orchestrate_debt_negotiation


def run_v2_evolution_tests():
    print("=" * 75)
    print("[PocketSmart AI] PHASE 2.1 & 2.2 EVOLUTION VERIFICATION SUITE")
    print("=" * 75)

    # 1. Deterministic Cash Flow Curve Calculation
    profile = UserFinancialProfile(
        monthly_income=4500.0,
        savings_target=500.0,
        expenses=[
            ExpenseItem(category="Housing", description="Rent", amount=1500.0, is_essential=True),
            ExpenseItem(category="Food", description="Groceries", amount=600.0, is_essential=True),
            ExpenseItem(category="Discretionary", description="Entertainment", amount=300.0, is_essential=False)
        ]
    )
    starting_cash = 1000.0
    curve = calculate_deterministic_cash_flow_curve(starting_cash, profile, horizon_days=30)

    assert len(curve) == 30, f"Expected 30 daily coordinates, got {len(curve)}"
    assert curve[0].day_offset == 1
    assert curve[-1].day_offset == 30
    assert curve[-1].projected_balance > starting_cash, "Positive cash flow must expand projected balance"
    assert curve[-1].upper_bound > curve[-1].projected_balance > curve[-1].lower_bound
    print("[PASS] [1/4] Deterministic Cash Flow Trajectory & Funnel Bounds: PASSED")

    # 2. Predictive Cash Flow Report Deserialization
    report = generate_predictive_cash_flow_report(starting_cash, profile, horizon_days=30)
    assert isinstance(report, PredictiveCashFlowReport)
    assert report.forecast_horizon_days == 30
    assert report.burn_rate_daily == 70.0
    assert report.earliest_deficit_day is None
    print("[PASS] [2/4] Predictive Cash Flow Report Generation & Schema Typing: PASSED")

    # 3. Debt Negotiation Deterministic Strategy Evaluation
    high_apr_debt = DebtItem(
        creditor_name="Bank of America",
        debt_type="CREDIT_CARD",
        current_balance=8000.0,
        annual_percentage_rate=26.99,
        minimum_monthly_payment=240.0,
        months_delinquent=0
    )
    dossier = orchestrate_debt_negotiation(high_apr_debt, monthly_discretionary_income=500.0)

    assert isinstance(dossier, CreditorNegotiationDossier)
    assert dossier.recommended_strategy.strategy_type == "APR_REDUCTION"
    assert dossier.recommended_strategy.target_apr == 9.99
    assert dossier.recommended_strategy.target_monthly_relief_usd > 0.0
    print("[PASS] [3/4] Debt Negotiation Strategy Evaluation & Relief Targeting: PASSED")

    # 4. Agent Grounding Check & Quoted Ledger Consistency
    letter = dossier.formal_letter_body
    assert "$8,000.00" in letter or "8,000" in letter or "8000" in letter
    assert "26.99%" in letter or "26.99" in letter
    assert len(dossier.talking_points) >= 3
    print("[PASS] [4/4] Creditor Negotiation Grounding & Ledger Accuracy: PASSED")

    print("-" * 75)
    print("[SUCCESS] ALL PHASE 2.1 & 2.2 EVOLUTION MODULES PASSED WITH 100% ACCURACY")
    print("-" * 75)


if __name__ == "__main__":
    run_v2_evolution_tests()

