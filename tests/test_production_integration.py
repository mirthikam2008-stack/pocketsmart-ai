"""
test_production_integration.py
Unified 9-Stage Production Integration & Subsystem Verification Suite for PocketSmart AI.
"""

import sys
import json
import time
from typing import List

# Import all core domain schemas and services
from schemas import (
    UserFinancialProfile,
    ExpenseItem,
    AIAnalysisReport,
    MultimodalOCRDocumentReport,
    AutonomousSimulationReport
)
from services.budget_engine import (
    compute_baseline_metrics,
    calculate_fifty_thirty_twenty,
    parse_csv_transactions
)
from services.privacy_service import sanitize_user_profile, sanitize_financial_text
from services.export_service import generate_executive_pdf_report, generate_audit_json_snapshot
from services.telemetry_service import telemetry_collector
from services.resilience_service import resilience_engine, CircuitBreakerOpenException

def run_production_audit():
    print("=" * 70)
    print("[PocketSmart AI] COMPLETE 9-STAGE PRODUCTION INTEGRATION AUDIT")
    print("=" * 70)
    
    # -------------------------------------------------------------
    # Stage 1: Baseline Deterministic Arithmetic & 50/30/20 Checks
    # -------------------------------------------------------------
    profile = UserFinancialProfile(
        monthly_income=5000.0,
        savings_target=1000.0,
        expenses=[
            ExpenseItem(category="Housing", description="Rent", amount=1500.0, is_essential=True),
            ExpenseItem(category="Groceries", description="Food", amount=500.0, is_essential=True),
            ExpenseItem(category="Entertainment", description="Streaming", amount=200.0, is_essential=False),
        ]
    )
    metrics = compute_baseline_metrics(profile)
    assert metrics.total_spend == 2200.0, f"Total spend mismatch: {metrics.total_spend}"
    assert metrics.actual_savings == 2800.0, f"Actual savings mismatch: {metrics.actual_savings}"
    assert metrics.savings_gap == -1800.0, f"Savings gap mismatch: {metrics.savings_gap}"

    
    split = calculate_fifty_thirty_twenty(profile.monthly_income, profile.expenses)
    assert split.target_needs_amount == 2500.0
    assert split.target_wants_amount == 1500.0
    assert split.target_savings_amount == 1000.0
    print("[PASS] [Stage 1/9] Deterministic Baseline Arithmetic & 50/30/20 Allocation: PASSED")

    # -------------------------------------------------------------
    # Stage 2: CSV Normalization & Ingestion
    # -------------------------------------------------------------
    csv_mock = "Transaction Date,Merchant,Spent,Type\n2025-01-01,Supermarket,85.50,Groceries\n2025-01-02,Coffee Shop,6.75,Dining"
    parsed_expenses = parse_csv_transactions(csv_mock)
    assert len(parsed_expenses) == 2
    assert parsed_expenses[0].amount == 85.50
    assert parsed_expenses[1].amount == 6.75
    print("[PASS] [Stage 2/9] CSV Normalization & Dynamic Column Aliasing: PASSED")

    # -------------------------------------------------------------
    # Stage 3: Extreme Deficit & Micro-Spend Edge Case Simulation
    # -------------------------------------------------------------
    deficit_profile = UserFinancialProfile(
        monthly_income=2000.0,
        savings_target=500.0,
        expenses=[
            ExpenseItem(category="Luxury", description="Exotic Car Rental", amount=3500.0, is_essential=False)
        ]
    )
    deficit_metrics = compute_baseline_metrics(deficit_profile)
    assert deficit_metrics.actual_savings == -1500.0
    assert deficit_metrics.savings_gap == 2000.0
    assert deficit_metrics.savings_rate_percent < 0
    print("[PASS] [Stage 3/9] Extreme Deficit & Negative Cashflow Simulation: PASSED")

    # -------------------------------------------------------------
    # Stage 4: Pydantic Schema Validation & Type Enforcement
    # -------------------------------------------------------------
    sample_report_json = {
        "overall_health_score": 82,
        "health_summary": "Solid discretionary discipline with minor leakage.",
        "savings_feasibility": "FEASIBLE",
        "budget_leaks": [
            {
                "category": "Subscriptions",
                "description": "Recurring Monthly subscriptions that are unused",
                "estimated_monthly_waste": 45.0,
                "severity": "Low"
            }
        ],
        "spending_anomalies": [
            {
                "item": "Dining Out",
                "amount": 250.0,
                "reason": "Significant spike on weekend compared to benchmark"
            }
        ],
        "recommendations": [
            {
                "priority": 1,
                "title": "Trim Dining Budget",
                "action_plan": "Pack lunch 3 days a week to reduce restaurant spend",
                "potential_monthly_savings": 150.0,
                "difficulty": "Easy"
            }
        ]
    }
    validated_report = AIAnalysisReport.model_validate(sample_report_json)
    assert validated_report.overall_health_score == 82
    assert len(validated_report.budget_leaks) == 1
    assert validated_report.recommendations[0].priority == 1
    print("[PASS] [Stage 4/9] Pydantic JSON Output Schema Deserialization: PASSED")

    # -------------------------------------------------------------
    # Stage 5: Multimodal OCR Document Extraction Verification
    # -------------------------------------------------------------
    from schemas import ExtractedDocumentExpense
    mock_ocr = MultimodalOCRDocumentReport(
        document_type="Bank Statement",
        detected_currency="USD",
        institution_or_vendor="Chase Bank",
        document_summary="Checking statement with 2 extracted items.",
        unreadable_warning=None,
        extracted_expenses=[
            ExtractedDocumentExpense(category="Utilities", merchant_or_description="Electric Bill", amount=120.0),
            ExtractedDocumentExpense(category="Shopping", merchant_or_description="Apparel Store", amount=45.0)
        ]
    )
    assert len(mock_ocr.extracted_expenses) == 2
    assert mock_ocr.extracted_expenses[0].amount == 120.0
    print("[PASS] [Stage 5/9] Multimodal OCR Statement Extraction Schema: PASSED")


    # -------------------------------------------------------------
    # Stage 6: Conversational Chat Context Grounding
    # -------------------------------------------------------------
    from services.chat_service import build_system_context_dossier
    dossier = build_system_context_dossier(profile, metrics, validated_report)
    assert "GROUND-TRUTH PRIMACY" in dossier
    assert "$5,000.00" in dossier
    assert "$2,200.00" in dossier
    assert "$2,800.00" in dossier
    print("[PASS] [Stage 6/9] Conversational System Dossier Context Grounding: PASSED")

    # -------------------------------------------------------------
    # Stage 7: Autonomous Rebalancer Amortization Trajectory
    # -------------------------------------------------------------
    from services.rebalancer_engine import calculate_deterministic_trajectories
    from schemas import FinancialMilestoneGoal
    goal = FinancialMilestoneGoal(
        goal_name="Emergency Fund",
        target_amount=6000.0,
        timeline_months=12,
        current_starting_balance=1200.0
    )
    trajectories = calculate_deterministic_trajectories(profile, metrics, goal)
    assert "status_quo" in trajectories
    assert "balanced" in trajectories
    assert "aggressive" in trajectories
    assert len(trajectories["balanced"].cumulative_balance_curve) == 12
    print("[PASS] [Stage 7/9] Autonomous Multi-Scenario Amortization Curves: PASSED")

    # -------------------------------------------------------------
    # Stage 8: PII Sanitization & SHA-256 Cryptographic Export
    # -------------------------------------------------------------
    raw_sensitive_text = "Wire $500 to John Doe at 4532-1122-3344-5566, SSN: 123-45-6789, email: john@example.com"
    sanitized_text, redactions = sanitize_financial_text(raw_sensitive_text)
    assert "123-45-6789" not in sanitized_text
    assert "john@example.com" not in sanitized_text
    assert redactions >= 3
    
    pdf_buffer = generate_executive_pdf_report(profile, metrics, validated_report, trajectories["balanced"])
    assert pdf_buffer.getvalue().startswith(b"%PDF")
    
    json_snapshot = generate_audit_json_snapshot(profile, metrics, validated_report, trajectories)
    snapshot_data = json.loads(json_snapshot)
    assert "sha256_audit_seal" in snapshot_data
    assert len(snapshot_data["sha256_audit_seal"]) == 64
    print("[PASS] [Stage 8/9] PII Sanitization & Tamper-Sealed PDF/JSON Export: PASSED")

    # -------------------------------------------------------------
    # Stage 9: Telemetry Cost Logging & Resilience Circuit Breaker
    # -------------------------------------------------------------
    start_time = time.time()
    call_metric = telemetry_collector.record_call(
        endpoint_name="test_audit_inference",
        model="gemini-3.7-pro",
        duration_ms=45.2,
        prompt_tokens=1200,
        completion_tokens=350,
        success=True
    )
    assert call_metric.prompt_tokens == 1200
    assert call_metric.completion_tokens == 350
    assert call_metric.estimated_cost_usd > 0.0
    
    summary = telemetry_collector.get_summary()
    assert summary["total_calls"] >= 1
    assert summary["total_tokens_consumed"] >= 1550

    # Test Circuit Breaker logic
    def failing_op():
        raise ConnectionResetError("Simulated socket drop")
    
    breaker_tripped = False
    try:
        # Trip breaker through repeated forced failures
        for _ in range(4):
            try:
                resilience_engine.execute_with_retry("test_circuit", failing_op, max_retries=1, initial_delay=0.01)
            except Exception:
                pass
        # Next call should immediately be blocked by the open circuit
        resilience_engine.execute_with_retry("test_circuit", failing_op, max_retries=1)
    except CircuitBreakerOpenException:
        breaker_tripped = True
    except Exception:
        pass
    
    assert breaker_tripped, "Circuit breaker failed to trip after consecutive failures"
    resilience_engine.circuit_open = False  # Reset state
    resilience_engine.failure_count = 0
    print("[PASS] [Stage 9/9] FinOps Telemetry Cost Tracking & Circuit Breaker: PASSED")

    print("-" * 70)
    print("[SUCCESS] ALL 9 SUBSYSTEMS PASSED FULL INTEGRATION VERIFICATION WITH 100% ACCURACY")
    print("-" * 70)

if __name__ == "__main__":
    run_production_audit()

