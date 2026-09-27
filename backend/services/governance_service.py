"""
services/governance_service.py
Automated Model Governance, Prompt Drift Detection, and Synthetic Grounding Benchmarks.
"""

import time
import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from schemas import (
    UserFinancialProfile,
    ExpenseItem,
    AIAnalysisReport
)
from services.budget_engine import compute_baseline_metrics
from services.gemini_service import analyze_financial_profile
from services.telemetry_service import telemetry_collector

class GovernanceBenchmarkResult(BaseModel):
    benchmark_timestamp: float = Field(default_factory=time.time)
    scenarios_evaluated: int
    schema_adherence_rate_pct: float
    arithmetic_grounding_score_pct: float
    avg_latency_ms: float
    avg_tokens_per_call: float
    detected_drift_flags: List[str]
    audit_verdict: str

def generate_synthetic_profiles() -> List[UserFinancialProfile]:
    """Generates synthetic test profiles representing distinct cashflow topologies."""
    return [
        UserFinancialProfile(
            monthly_income=6000.0,
            savings_target=1200.0,
            expenses=[
                ExpenseItem(category="Housing", description="Mortgage", amount=1800.0, is_essential=True),
                ExpenseItem(category="Food", description="Groceries", amount=600.0, is_essential=True),
                ExpenseItem(category="Leisure", description="Gym", amount=100.0, is_essential=False),
            ]
        ),
        UserFinancialProfile(
            monthly_income=2500.0,
            savings_target=300.0,
            expenses=[
                ExpenseItem(category="Rent", description="Apartment", amount=1400.0, is_essential=True),
                ExpenseItem(category="Groceries", description="Food", amount=400.0, is_essential=True),
                ExpenseItem(category="Transport", description="Car Loan", amount=500.0, is_essential=True),
                ExpenseItem(category="Dining", description="Restaurants", amount=350.0, is_essential=False),
            ]
        ),
        UserFinancialProfile(
            monthly_income=10000.0,
            savings_target=4000.0,
            expenses=[
                ExpenseItem(category="Housing", description="Rent", amount=3000.0, is_essential=True),
                ExpenseItem(category="Discretionary", description="Travel", amount=2500.0, is_essential=False),
            ]
        )
    ]

def evaluate_model_governance(api_key: str = None) -> GovernanceBenchmarkResult:
    """Runs automated synthetic test batteries to detect model drift and calculation grounding."""
    profiles = generate_synthetic_profiles()
    schema_successes = 0
    grounding_matches = 0
    total_latency = 0.0
    total_tokens = 0
    drift_flags = []

    for idx, profile in enumerate(profiles, start=1):
        metrics = compute_baseline_metrics(profile)
        start_t = time.time()
        
        try:
            # Execute analysis (live or deterministic fallback)
            report = analyze_financial_profile(profile, metrics, api_key_override=api_key)
            duration_ms = (time.time() - start_t) * 1000.0
            total_latency += duration_ms
            
            # 1. Verify Schema Adherence
            if isinstance(report, AIAnalysisReport) and 0 <= report.overall_health_score <= 100:
                schema_successes += 1
            else:
                drift_flags.append(f"Scenario {idx}: Schema typing or score boundary check failed.")
            
            # 2. Verify Arithmetic Grounding
            # AI summary must respect actual savings status (positive vs deficit)
            summary_lower = report.health_summary.lower()
            if metrics.actual_savings < 0:
                if "deficit" in summary_lower or "gap" in summary_lower or "exceed" in summary_lower or report.overall_health_score < 60:
                    grounding_matches += 1
                else:
                    drift_flags.append(f"Scenario {idx}: Deficit condition not reflected in health score/summary.")
            else:
                if metrics.savings_gap == 0:
                    if report.savings_feasibility in ["FEASIBLE", "MODERATE"]:
                        grounding_matches += 1
                    else:
                        drift_flags.append(f"Scenario {idx}: Healthy surplus marked unrealistic by model.")
                else:
                    grounding_matches += 1

        except Exception as e:
            drift_flags.append(f"Scenario {idx}: Exception during evaluation: {str(e)}")

    count = len(profiles)
    adherence_rate = (schema_successes / count) * 100.0
    grounding_score = (grounding_matches / count) * 100.0
    avg_latency = total_latency / count if count > 0 else 0.0
    
    # Check telemetry for average tokens
    summary = telemetry_collector.get_summary()
    avg_tokens = summary["total_tokens_consumed"] / summary["total_calls"] if summary["total_calls"] > 0 else 0.0

    if avg_tokens > 2500:
        drift_flags.append(f"High token drift detected: average tokens per call is {avg_tokens:.1f}.")

    verdict = "PASSED" if adherence_rate >= 95.0 and grounding_score >= 95.0 else "WARNING_DRIFT_DETECTED"

    return GovernanceBenchmarkResult(
        scenarios_evaluated=count,
        schema_adherence_rate_pct=round(adherence_rate, 2),
        arithmetic_grounding_score_pct=round(grounding_score, 2),
        avg_latency_ms=round(avg_latency, 2),
        avg_tokens_per_call=round(avg_tokens, 2),
        detected_drift_flags=drift_flags,
        audit_verdict=verdict
    )
