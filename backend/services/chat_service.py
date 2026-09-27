"""
Conversational Financial Advisory Chat Service for PocketSmart AI.
Utilizes Google Gemini 3.7 Pro via the official google-genai SDK
with grounded user financial context, multi-turn session memory,
streaming responses, and strict FinTech guardrails.
"""
from typing import List, Dict, Generator, Optional
from google import genai
from google.genai import types

from schemas import (
    UserFinancialProfile,
    BaselineBudgetMetrics,
    AIAnalysisReport,
)
from services.gemini_service import get_gemini_client


FINANCIAL_CHAT_GUARDRAIL_PROMPT = """
You are "PocketSmart Copilot", an elite Certified Financial Advisory AI and personal cash-flow coach.

### STRICT OPERATIONAL & CONVERSATIONAL GUARDRAILS:
1. **GROUND-TRUTH PRIMACY**:
   - You MUST reference and remain 100% consistent with the USER'S CURRENT FINANCIAL CONTEXT injected below.
   - Never invent or contradict the baseline numbers (Income, Total Spend, Actual Savings, Savings Gap, 50/30/20 breakdown).
   - If the user asks whether they can afford a specific purchase, calculate the exact impact against their actual residual savings and current savings gap.

2. **MATHEMATICAL DISCIPLINE**:
   - Perform all arithmetic calculations step-by-step and verify them against the user's logged figures.
   - When suggesting budget cuts, cite specific line items from their logged expenses and show before/after numbers.

3. **FINANCIAL ADVICE DISCLAIMER**:
   - You provide educational budgeting and cash-flow coaching. If asked about tax law, legal estate planning, or specific stock picks/crypto speculation, explicitly clarify that you are an AI financial coach and advise consulting a licensed fiduciary financial planner or CPA.
   - Refuse investment speculation and high-risk gambling advice.

4. **COMMUNICATION STYLE**:
   - Concise, supportive, empathetic, and actionable. Use bullet points and clear bold headings.
"""


def build_system_context_dossier(
    profile: UserFinancialProfile,
    metrics: BaselineBudgetMetrics,
    ai_report: Optional[AIAnalysisReport] = None,
) -> str:
    """
    Constructs an immutable financial dossier injected into the chat session as system context.
    """
    f32 = metrics.fifty_thirty_twenty
    expenses_snippet = "\n".join([
        f"- [{exp.date or 'N/A'}] {exp.category}: {exp.description} (${exp.amount:,.2f})"
        for exp in profile.expenses[:30]  # Cap at 30 items for token efficiency
    ])

    report_context = ""
    if ai_report:
        leaks_txt = ", ".join([f"{l.category}: {l.description} (${l.estimated_monthly_waste}/mo)" for l in ai_report.budget_leaks])
        report_context = f"""
### PREVIOUS AI DIAGNOSTIC FINDINGS:
- **Financial Health Score:** {ai_report.overall_health_score}/100
- **Health Summary:** {ai_report.health_summary}
- **Detected Budget Leaks:** {leaks_txt or 'None'}
- **Savings Feasibility:** {ai_report.savings_feasibility}
"""

    return f"""
{FINANCIAL_CHAT_GUARDRAIL_PROMPT}

### CURRENT USER FINANCIAL GROUND TRUTH:
- **Monthly Net Income:** ${metrics.monthly_income:,.2f}
- **Target Monthly Savings:** ${metrics.target_savings:,.2f}
- **Actual Monthly Spend:** ${metrics.total_spend:,.2f}
- **Actual Residual Savings:** ${metrics.actual_savings:,.2f}
- **Savings Target Gap:** ${metrics.savings_gap:,.2f} ({'Shortfall' if metrics.savings_gap > 0 else 'Surplus'})
- **Savings Rate:** {metrics.savings_rate_pct:.1f}%
- **50/30/20 Status:**
  * Needs (50%): Actual ${f32.needs_actual:,.2f} ({f32.needs_pct:.1f}%) | Target: ${f32.needs_target:,.2f}
  * Wants (30%): Actual ${f32.wants_actual:,.2f} ({f32.wants_pct:.1f}%) | Target: ${f32.wants_target:,.2f}
  * Savings (20%): Actual ${f32.savings_actual:,.2f} ({f32.savings_pct:.1f}%) | Target: ${f32.savings_target:,.2f}
- **Category Spend Aggregates:** {metrics.category_breakdown}
- **Recent Itemized Transactions ({len(profile.expenses)} items):**
{expenses_snippet}
{report_context}
"""


def stream_chat_response(
    messages: List[Dict[str, str]],
    profile: UserFinancialProfile,
    metrics: BaselineBudgetMetrics,
    ai_report: Optional[AIAnalysisReport] = None,
    api_key: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Streams a conversational response from Gemini 3.7 Pro using the official google-genai SDK,
    maintaining multi-turn context and grounding against verified financial data.
    """
    client = get_gemini_client(api_key=api_key)
    system_instruction = build_system_context_dossier(profile, metrics, ai_report)

    # Convert conversation history into google-genai Content types
    contents: List[types.Content] = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])],
            )
        )

    try:
        response_stream = client.models.generate_content_stream(
            model="gemini-3.7-pro",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.4,
            ),
        )

        for chunk in response_stream:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        yield f"\n⚠️ **Chat Service Error**: {str(e)}"
