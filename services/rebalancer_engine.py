"""
Autonomous Scenario Simulator & Financial Goal Rebalancer Engine.
Combines deterministic multi-month forward-looking mathematical modeling
with Google Gemini 3.7 Pro structured reasoning via the official google-genai SDK.
"""
from typing import List, Dict, Tuple, Optional
from google import genai
from google.genai import types

from schemas import (
    UserFinancialProfile,
    BaselineBudgetMetrics,
    FinancialMilestoneGoal,
    ScenarioTrajectory,
    CategoryCutPlan,
    AutonomousSimulationReport,
)
from services.gemini_service import get_gemini_client


def compute_deterministic_scenario_trajectory(
    income: float,
    current_spend: float,
    target_amount: float,
    starting_balance: float,
    timeline_months: int,
    spend_reduction_ratio: float,
    scenario_name: str,
    risk_level: str,
) -> ScenarioTrajectory:
    """
    Computes a mathematically exact month-by-month financial projection.
    
    spend_reduction_ratio:
      - 0.0: Status Quo (no changes to spend)
      - 0.20: Balanced Lifestyle (20% reduction in discretionary expenses)
      - 0.45: Aggressive Austerity (45% reduction in non-essential spend)
    """
    adjusted_spend = max(0.0, current_spend * (1.0 - spend_reduction_ratio))
    monthly_savings = income - adjusted_spend

    # Remaining principal to achieve
    needed_growth = max(0.0, target_amount - starting_balance)

    if monthly_savings > 0:
        months_to_goal = int((needed_growth / monthly_savings) + 0.9999)  # Ceiling division
    else:
        months_to_goal = 999  # Infinite runway if burn exceeds income

    goal_achieved = months_to_goal <= timeline_months

    # Generate cumulative monthly balance curves across the simulation window
    sim_horizon = max(timeline_months, min(months_to_goal, 36))
    cumulative_balances: List[float] = []
    current_balance = starting_balance

    for _ in range(sim_horizon):
        current_balance = round(current_balance + monthly_savings, 2)
        cumulative_balances.append(current_balance)

    return ScenarioTrajectory(
        scenario_name=scenario_name,
        monthly_burn_rate=round(adjusted_spend, 2),
        monthly_savings_accumulation=round(monthly_savings, 2),
        months_to_goal=months_to_goal,
        goal_achieved_within_target=goal_achieved,
        monthly_cumulative_balances=cumulative_balances,
        risk_level=risk_level,
    )


REBALANCER_SYSTEM_INSTRUCTION = """
You are the "PocketSmart Autonomous Strategist", a quantitative financial planner and algorithmic portfolio rebalancer.

Your mission:
1. Analyze the user's financial profile, deterministic multi-scenario trajectories, and target milestone goals (e.g. emergency fund, debt elimination, down payment).
2. Synthesize an actionable category reduction plan that achieves the goal within the user's timeline while minimizing lifestyle burnout.
3. Compare the Status Quo, Balanced, and Aggressive scenarios with realistic financial trade-offs.
4. Output strictly conformant JSON matching the AutonomousSimulationReport Pydantic schema.
"""


def generate_autonomous_simulation(
    profile: UserFinancialProfile,
    metrics: BaselineBudgetMetrics,
    goal: FinancialMilestoneGoal,
    api_key: Optional[str] = None,
) -> AutonomousSimulationReport:
    """
    Simulates multi-scenario financial trajectories deterministically and synthesizes
    actionable category cut schedules using Gemini 3.7 Pro.
    """
    # 1. Compute Deterministic Trajectories
    status_quo = compute_deterministic_scenario_trajectory(
        income=metrics.monthly_income,
        current_spend=metrics.total_spend,
        target_amount=goal.target_amount,
        starting_balance=goal.current_savings_or_debt,
        timeline_months=goal.target_timeline_months,
        spend_reduction_ratio=0.0,
        scenario_name="Status Quo Runway",
        risk_level="High" if metrics.savings_gap > 0 else "Low",
    )

    balanced = compute_deterministic_scenario_trajectory(
        income=metrics.monthly_income,
        current_spend=metrics.total_spend,
        target_amount=goal.target_amount,
        starting_balance=goal.current_savings_or_debt,
        timeline_months=goal.target_timeline_months,
        spend_reduction_ratio=0.18,  # 18% realistic discretionary trim
        scenario_name="Balanced Lifestyle",
        risk_level="Moderate",
    )

    aggressive = compute_deterministic_scenario_trajectory(
        income=metrics.monthly_income,
        current_spend=metrics.total_spend,
        target_amount=goal.target_amount,
        starting_balance=goal.current_savings_or_debt,
        timeline_months=goal.target_timeline_months,
        spend_reduction_ratio=0.38,  # 38% aggressive austerity trim
        scenario_name="Aggressive Austerity",
        risk_level="High",
    )

    # 2. Construct Grounded Prompt for Gemini 3.7 Pro
    user_prompt = f"""
### FINANCIAL MILESTONE GOAL
- **Goal Type:** {goal.goal_type}
- **Target Amount:** ${goal.target_amount:,.2f}
- **Target Timeline:** {goal.target_timeline_months} Months
- **Starting Balance / Debt:** ${goal.current_savings_or_debt:,.2f}

### USER CASH FLOW PROFILE
- **Monthly Net Income:** ${metrics.monthly_income:,.2f}
- **Current Spend:** ${metrics.total_spend:,.2f}
- **Current Savings Rate:** {metrics.savings_rate_pct:.1f}%
- **Category Breakdown:** {metrics.category_breakdown}

### DETERMINISTIC TRAJECTORY MODELING:
1. **Status Quo**: Monthly Spend ${status_quo.monthly_burn_rate:,.2f} | Net Savings +${status_quo.monthly_savings_accumulation:,.2f}/mo | Months to Goal: {status_quo.months_to_goal} (Met: {status_quo.goal_achieved_within_target})
2. **Balanced Lifestyle**: Monthly Spend ${balanced.monthly_burn_rate:,.2f} | Net Savings +${balanced.monthly_savings_accumulation:,.2f}/mo | Months to Goal: {balanced.months_to_goal} (Met: {balanced.goal_achieved_within_target})
3. **Aggressive Austerity**: Monthly Spend ${aggressive.monthly_burn_rate:,.2f} | Net Savings +${aggressive.monthly_savings_accumulation:,.2f}/mo | Months to Goal: {aggressive.months_to_goal} (Met: {aggressive.goal_achieved_within_target})

Please formulate a strategic evaluation and concrete category reduction schedule to reach this milestone.
"""

    try:
        client = get_gemini_client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-3.7-pro",
            contents=user_prompt,
            config=types.GenerateContentConfig(

                system_instruction=REBALANCER_SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=AutonomousSimulationReport,
                temperature=0.2,
            ),
        )

        if hasattr(response, "parsed") and response.parsed is not None:
            if isinstance(response.parsed, AutonomousSimulationReport):
                report = response.parsed
            elif isinstance(response.parsed, dict):
                report = AutonomousSimulationReport.model_validate(response.parsed)
            else:
                report = AutonomousSimulationReport.model_validate_json(response.text)
        else:
            report = AutonomousSimulationReport.model_validate_json(response.text)

        # Enforce deterministic trajectory curves onto the report for guaranteed arithmetic accuracy
        report.status_quo_scenario = status_quo
        report.balanced_scenario = balanced
        report.aggressive_scenario = aggressive

        return report

    except Exception as e:
        # Fallback to pure deterministic report if API error occurs
        fallback_cuts: List[CategoryCutPlan] = []
        for cat, amt in metrics.category_breakdown.items():
            if "dining" in cat.lower() or "shopping" in cat.lower() or "entertainment" in cat.lower():
                cut = round(amt * 0.25, 2)
                fallback_cuts.append(
                    CategoryCutPlan(
                        category=cat,
                        current_spend=amt,
                        proposed_spend=round(amt - cut, 2),
                        monthly_cut_amount=cut,
                        rationale_and_tradeoffs="Trim non-essential discretionary allocation to fund target milestone.",
                    )
                )

        return AutonomousSimulationReport(
            milestone_summary=f"Automated evaluation for {goal.goal_type} (${goal.target_amount:,.2f} over {goal.target_timeline_months} months).",
            recommended_scenario="Balanced Lifestyle" if balanced.goal_achieved_within_target else "Aggressive Austerity",
            status_quo_scenario=status_quo,
            balanced_scenario=balanced,
            aggressive_scenario=aggressive,
            category_cut_schedule=fallback_cuts,
            strategic_advice="Maintain consistent savings habits and automate milestone deposits on salary day.",
        )


def calculate_deterministic_trajectories(
    profile: UserFinancialProfile,
    metrics: BaselineBudgetMetrics,
    goal: FinancialMilestoneGoal,
) -> Dict[str, ScenarioTrajectory]:
    """Computes all 3 deterministic trajectories as a dict."""
    status_quo = compute_deterministic_scenario_trajectory(
        income=metrics.monthly_income,
        current_spend=metrics.total_spend,
        target_amount=goal.target_amount,
        starting_balance=goal.current_savings_or_debt,
        timeline_months=goal.target_timeline_months,
        spend_reduction_ratio=0.0,
        scenario_name="Status Quo Runway",
        risk_level="High" if metrics.savings_gap > 0 else "Low",
    )

    balanced = compute_deterministic_scenario_trajectory(
        income=metrics.monthly_income,
        current_spend=metrics.total_spend,
        target_amount=goal.target_amount,
        starting_balance=goal.current_savings_or_debt,
        timeline_months=goal.target_timeline_months,
        spend_reduction_ratio=0.18,
        scenario_name="Balanced Lifestyle",
        risk_level="Moderate",
    )

    aggressive = compute_deterministic_scenario_trajectory(
        income=metrics.monthly_income,
        current_spend=metrics.total_spend,
        target_amount=goal.target_amount,
        starting_balance=goal.current_savings_or_debt,
        timeline_months=goal.target_timeline_months,
        spend_reduction_ratio=0.40,
        scenario_name="Aggressive Austerity",
        risk_level="High",
    )

    return {
        "status_quo": status_quo,
        "balanced": balanced,
        "aggressive": aggressive,
    }

