"""
app_v2_extensions.py
Streamlit UI Extensions rendering Plotly Cash Flow Forecasts and Autonomous Debt Negotiation Drafts.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from schemas import UserFinancialProfile
from schemas_v2 import DebtItem
from services.forecast_service import generate_predictive_cash_flow_report
from services.debt_agent_service import orchestrate_debt_negotiation


def render_predictive_forecast_tab(profile: UserFinancialProfile):
    """Renders 30/90-Day Cash Flow Forecast with Plotly Confidence Funnel."""
    st.subheader("📈 Predictive Cash Flow & Liquidity Runway (Phase 2.1)")
    st.markdown("Combines recurring interval modeling with **Gemini 3.7 Pro** risk analysis.")

    col1, col2 = st.columns([1, 1])
    with col1:
        starting_cash = st.number_input("Current Liquid Cash ($)", min_value=0.0, value=2500.0, step=100.0)
    with col2:
        horizon = st.radio("Forecast Horizon", [30, 90], horizontal=True)

    if st.button("Generate Predictive Cash Flow Forecast", type="primary", use_container_width=True):
        with st.spinner("Calculating stochastic forecast trajectories..."):
            report = generate_predictive_cash_flow_report(starting_cash, profile, horizon_days=horizon)

            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Projected Ending Cash", f"${report.projected_end_balance:,.2f}")
            kpi2.metric("Daily Net Flow", f"${report.burn_rate_daily:,.2f}/day")
            kpi3.metric(
                "Deficit Risk Day",
                f"Day {report.earliest_deficit_day}" if report.earliest_deficit_day else "Zero Deficit Detected"
            )

            st.info(f"**AI Risk Assessment:** {report.ai_risk_assessment}")

            df = pd.DataFrame([p.model_dump() for p in report.forecast_trajectory])

            fig = go.Figure()
            # Upper bound (p90)
            fig.add_trace(go.Scatter(
                x=df["day_offset"], y=df["upper_bound"],
                mode='lines', line=dict(width=0),
                showlegend=False, name="Optimistic (p90)"
            ))
            # Lower bound (p10) with fill
            fig.add_trace(go.Scatter(
                x=df["day_offset"], y=df["lower_bound"],
                mode='lines', line=dict(width=0),
                fill='tonexty', fillcolor='rgba(65, 105, 225, 0.15)',
                showlegend=False, name="Conservative (p10)"
            ))
            # Main projected balance
            fig.add_trace(go.Scatter(
                x=df["day_offset"], y=df["projected_balance"],
                mode='lines+markers', line=dict(color='#00D26A', width=3),
                name="Projected Net Cash"
            ))
            # Floor boundary
            fig.add_hline(y=0.0, line_dash="dash", line_color="red", annotation_text="Liquidity Zero Floor")

            fig.update_layout(
                title=f"{horizon}-Day Forward Cash Flow Projection",
                xaxis_title="Forward Days",
                yaxis_title="Projected Balance ($)",
                template="plotly_dark",
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)


def render_debt_negotiator_tab(net_discretionary: float = 200.0):
    """Renders Autonomous Agent Debt Negotiation Drawer."""
    st.subheader("🤝 Autonomous Creditor Negotiation Agent (Phase 2.2)")
    st.markdown("Synthesizes customized, legally styled negotiation correspondence grounded in verified obligations.")

    with st.form("negotiator_form"):
        col1, col2 = st.columns(2)
        with col1:
            creditor = st.text_input("Creditor / Servicer Name", value="Chase Card Services")
            debt_type = st.selectbox(
                "Debt Classification",
                ["CREDIT_CARD", "PERSONAL_LOAN", "AUTO_LOAN", "STUDENT_LOAN", "MEDICAL"]
            )
            balance = st.number_input("Current Outstanding Balance ($)", min_value=1.0, value=6500.0, step=100.0)
        with col2:
            apr = st.number_input("Current APR (%)", min_value=0.0, value=24.99, step=0.5)
            min_pay = st.number_input("Minimum Monthly Payment ($)", min_value=0.0, value=195.0, step=10.0)
            delinquent_months = st.number_input("Months Delinquent", min_value=0, max_value=60, value=0, step=1)

        hardship = st.text_area(
            "Hardship Circumstance",
            value="Unexpected medical expenses and reduced household discretionary income."
        )
        submitted = st.form_submit_button("Deploy Negotiation Agent", type="primary", use_container_width=True)

    if submitted:
        debt_item = DebtItem(
            creditor_name=creditor,
            debt_type=debt_type,
            current_balance=balance,
            annual_percentage_rate=apr,
            minimum_monthly_payment=min_pay,
            months_delinquent=delinquent_months
        )

        with st.spinner("Evaluating strategy and synthesizing correspondence via Gemini 3.7 Pro Agent..."):
            dossier = orchestrate_debt_negotiation(
                debt=debt_item,
                monthly_discretionary_income=net_discretionary,
                hardship_reason=hardship
            )

            st.success(f"Strategy Formulated: **{dossier.recommended_strategy.strategy_type}**")
            st.metric(
                "Target Monthly Cash Flow Relief",
                f"${dossier.recommended_strategy.target_monthly_relief_usd:,.2f}"
            )

            st.markdown("#### 📄 Formal Negotiation Correspondence")
            st.text_area("Copy Letter Body Below", dossier.formal_letter_body, height=260)
            st.download_button(
                label="Download Formal Letter (.txt)",
                data=dossier.formal_letter_body,
                file_name=f"debt_negotiation_{creditor.lower().replace(' ', '_')}.txt",
                mime="text/plain"
            )

            st.markdown("#### 🗣️ Representative Phone Talking Points")
            for point in dossier.talking_points:
                st.markdown(f"- {point}")

            st.caption(dossier.regulatory_disclaimer)
