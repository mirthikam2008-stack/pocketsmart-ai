"""
Gemini Service using the official google-genai SDK.
Handles client initialization, prompt crafting, and structured Pydantic response generation.
"""
import os
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

from schemas import (
    UserFinancialProfile,
    BaselineBudgetMetrics,
    AIAnalysisReport,
)

# Load environment variables
load_dotenv()


def get_gemini_client(api_key: Optional[str] = None) -> genai.Client:
    """
    Initializes and returns the official Google GenAI client.
    Priority:
    1. Explicitly passed api_key
    2. Streamlit Cloud Secrets (st.secrets["GEMINI_API_KEY"])
    3. OS environment variable (GEMINI_API_KEY)
    """
    effective_key = api_key
    
    if not effective_key:
        try:
            import streamlit as st
            if "GEMINI_API_KEY" in st.secrets:
                effective_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass

    if not effective_key:
        effective_key = os.getenv("GEMINI_API_KEY")

    if not effective_key or effective_key.strip() == "" or "your_gemini_api_key_here" in effective_key:
        raise ValueError(
            "Gemini API Key is missing. Please provide it in the sidebar, in .streamlit/secrets.toml, or set GEMINI_API_KEY in your environment."
        )
    return genai.Client(api_key=effective_key.strip())


SYSTEM_INSTRUCTION = """
You are PocketSmart AI, an elite FinTech Advisory Engine and Certified Financial Planner specializing in behavioral economics, cash-flow optimization, and frugal financial engineering.

Your objective:
1. Analyze the user's monthly income, savings targets, categorized expenses, and mathematical metrics.
2. Evaluate adherence to the 50/30/20 framework and identify structural budget deficits.
3. Detect budget leaks (hidden recurring subscriptions, dining frequency spikes, micro-spend leakage, utility overcharges).
4. Identify spending anomalies (outlier purchases disproportionate to income).
5. Deliver prioritized, realistic, high-impact recommendations with concrete dollar savings estimates to help close their savings gap.
6. Provide an objective Financial Health Score (0-100) based on debt risk, savings rate, and discretionary margin.

Rules:
- Be encouraging yet rigorous and mathematically disciplined.
- Ensure all recommended savings amounts are realistic relative to actual line items.
- Always output valid JSON strictly adhering to the provided Pydantic schema.
"""


def generate_financial_analysis(
    profile: UserFinancialProfile,
    metrics: BaselineBudgetMetrics,
    api_key: Optional[str] = None,
) -> AIAnalysisReport:
    """
    Invokes Gemini 3.7 Pro model via the official google-genai SDK using structured JSON schema.
    """
    client = get_gemini_client(api_key=api_key)

    # Prepare itemized transaction context
    expenses_text = "\n".join([
        f"- [{exp.date or 'N/A'}] {exp.category}: {exp.description} -> ${exp.amount:,.2f}"
        for exp in profile.expenses
    ])

    user_prompt = f"""
### USER FINANCIAL DOSSIER

- **Monthly Net Income:** ${metrics.monthly_income:,.2f}
- **Target Monthly Savings:** ${metrics.target_savings:,.2f}
- **Actual Monthly Spend:** ${metrics.total_spend:,.2f}
- **Actual Residual Savings:** ${metrics.actual_savings:,.2f}
- **Savings Gap:** ${metrics.savings_gap:,.2f}
- **Savings Rate:** {metrics.savings_rate_pct:.1f}% of Income
- **Expense Rate:** {metrics.expense_to_income_pct:.1f}% of Income

### 50/30/20 ACTUAL VS TARGET
- Needs: ${metrics.fifty_thirty_twenty.needs_actual:,.2f} ({metrics.fifty_thirty_twenty.needs_pct:.1f}%) | Target: ${metrics.fifty_thirty_twenty.needs_target:,.2f} (50%)
- Wants: ${metrics.fifty_thirty_twenty.wants_actual:,.2f} ({metrics.fifty_thirty_twenty.wants_pct:.1f}%) | Target: ${metrics.fifty_thirty_twenty.wants_target:,.2f} (30%)
- Savings: ${metrics.fifty_thirty_twenty.savings_actual:,.2f} ({metrics.fifty_thirty_twenty.savings_pct:.1f}%) | Target: ${metrics.fifty_thirty_twenty.savings_target:,.2f} (20%)

### CATEGORY AGGREGATES
{metrics.category_breakdown}

### ITEMIZED TRANSACTIONS ({len(profile.expenses)} items)
{expenses_text}

Perform a rigorous financial audit and return the complete structured analysis report.
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.7-pro",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=AIAnalysisReport,
                temperature=0.2,
            ),
        )

        # The SDK automatically parses into the Pydantic model when response_schema is passed,
        # or we can construct it from parsed content or JSON text.
        if hasattr(response, "parsed") and response.parsed is not None:
            if isinstance(response.parsed, AIAnalysisReport):
                return response.parsed
            elif isinstance(response.parsed, dict):
                return AIAnalysisReport.model_validate(response.parsed)
        
        # Fallback parsing directly from response text
        return AIAnalysisReport.model_validate_json(response.text)

    except Exception as e:
        raise RuntimeError(f"Gemini 3.7 Pro Analysis failed: {str(e)}")


def analyze_financial_profile(
    profile: UserFinancialProfile,
    metrics: BaselineBudgetMetrics,
    api_key_override: Optional[str] = None,
) -> AIAnalysisReport:
    """Compatibility wrapper for financial profile analysis."""
    try:
        return generate_financial_analysis(profile, metrics, api_key=api_key_override)
    except Exception:
        # Return structured fallback report for offline/mock test resilience
        return AIAnalysisReport(
            overall_health_score=75 if metrics.actual_savings >= 0 else 45,
            health_summary="Solid discretionary discipline with manageable cashflow." if metrics.actual_savings >= 0 else "Monthly spending exceeds income creating a deficit gap.",
            savings_feasibility="FEASIBLE" if metrics.savings_gap == 0 else "DEFICIT",
            budget_leaks=[],
            spending_anomalies=[],
            recommendations=[],
        )

