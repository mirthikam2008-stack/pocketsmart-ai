"""
PocketSmart AI: Smart Budget & Recommendation Assistant
Streamlit Web Application
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List

from schemas import ExpenseItem, UserFinancialProfile
from services.budget_engine import (
    parse_csv_transactions,
    compute_baseline_metrics,
)
from services.gemini_service import generate_financial_analysis

# Page Configuration
st.set_page_config(
    page_title="PocketSmart AI | Budget & Recommendation Assistant",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for modern FinTech aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 20px;
        color: white;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    .metric-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    .metric-delta-pos {
        font-size: 0.85rem;
        color: #10B981;
        font-weight: 600;
    }
    .metric-delta-neg {
        font-size: 0.85rem;
        color: #EF4444;
        font-weight: 600;
    }
    .score-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 2.2rem;
        font-weight: 800;
        border-radius: 50%;
        width: 90px;
        height: 90px;
        background: radial-gradient(circle, #3B82F6 0%, #1D4ED8 100%);
        color: white;
        box-shadow: 0 0 25px rgba(59, 130, 246, 0.5);
    }
    .rec-card {
        border-left: 4px solid #3B82F6;
        background: rgba(30, 41, 59, 0.5);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initializes session state for expenses and analysis state."""
    if "expenses" not in st.session_state:
        st.session_state.expenses = [
            ExpenseItem(date="2026-09-01", category="Housing", description="Rent / Mortgage", amount=1500.0),
            ExpenseItem(date="2026-09-02", category="Groceries", description="Weekly Supermarket", amount=245.50),
            ExpenseItem(date="2026-09-03", category="Utilities", description="Power & Water", amount=140.0),
            ExpenseItem(date="2026-09-04", category="Food & Dining", description="Restaurants & Cafes", amount=165.0),
            ExpenseItem(date="2026-09-05", category="Entertainment", description="Streaming Subscriptions", amount=45.99),
            ExpenseItem(date="2026-09-06", category="Transportation", description="Gas & Transit Pass", amount=95.0),
        ]
    if "ai_report" not in st.session_state:
        st.session_state.ai_report = None


init_session_state()

# -------------------------------------------------------------
# Sidebar: Configuration & Data Input
# -------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/isometric/96/money-box.png", width=64)
    st.title("PocketSmart AI")
    st.caption("AI-Powered Budget & Advisory Engine")
    st.divider()

    st.subheader("🔑 Gemini API Settings")
    sidebar_api_key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="AIzaSy...",
        help="Enter your Google Gemini API key or set GEMINI_API_KEY in .env",
    )

    st.divider()
    st.subheader("💵 Income & Goals")
    income_input = st.number_input(
        "Net Monthly Income ($)",
        min_value=100.0,
        max_value=1000000.0,
        value=5000.0,
        step=100.0,
        format="%.2f",
    )
    savings_target_input = st.number_input(
        "Target Monthly Savings ($)",
        min_value=0.0,
        max_value=1000000.0,
        value=1200.0,
        step=50.0,
        format="%.2f",
    )

    st.divider()
    st.subheader("🛡️ Financial Privacy & Compliance")
    privacy_mode = st.toggle("🔒 High Privacy / Ephemeral Mode", value=True, help="Automatically scrubs PII (SSN, card numbers, emails, addresses) before sending prompts to Google Gemini.")

    st.divider()
    st.subheader("📁 CSV & Statement Ingestion")
    uploaded_file = st.file_uploader("Upload bank CSV file", type=["csv"], key="csv_uploader")
    if uploaded_file is not None:
        try:
            parsed_items = parse_csv_transactions(uploaded_file)
            st.session_state.expenses = parsed_items
            st.success(f"Loaded {len(parsed_items)} CSV transactions successfully!")
        except Exception as e:
            st.error(f"Error loading CSV: {str(e)}")

    st.divider()
    st.subheader("📸 Multimodal OCR Ingestion")
    st.caption("Upload receipts (PNG, JPG) or PDF statements for Gemini 3.7 Pro Vision extraction.")
    uploaded_doc = st.file_uploader(
        "Upload Receipt or Statement",
        type=["png", "jpg", "jpeg", "webp", "pdf"],
        key="doc_uploader",
    )
    if uploaded_doc is not None:
        if st.button("🔍 Extract Transactions with AI", type="secondary", use_container_width=True):
            with st.spinner("Extracting transactions via Gemini 3.7 Pro Vision OCR..."):
                try:
                    from services.multimodal_service import extract_expenses_from_document
                    doc_bytes = uploaded_doc.getvalue()
                    new_expenses, ocr_report = extract_expenses_from_document(
                        file_bytes=doc_bytes,
                        file_name=uploaded_doc.name,
                        mime_type=uploaded_doc.type,
                        api_key=sidebar_api_key,
                    )
                    if new_expenses:
                        st.session_state.expenses.extend(new_expenses)
                        st.success(f"Extracted {len(new_expenses)} items from {ocr_report.document_type} ({ocr_report.institution_or_vendor or 'Vendor'})!")
                        if ocr_report.unreadable_warning:
                            st.warning(f"Note: {ocr_report.unreadable_warning}")
                        st.rerun()
                    else:
                        st.warning("No expense transactions could be extracted from this document.")
                except Exception as doc_err:
                    st.error(f"Multimodal OCR Error: {str(doc_err)}")

# -------------------------------------------------------------
# Main Application Content
# -------------------------------------------------------------
st.title("💳 PocketSmart AI: Financial Command Center")
st.write("Deterministic cash-flow analytics fused with Google Gemini 3.7 Pro financial intelligence.")

# Expense Management Section
with st.expander("📝 Manage & Add Itemized Expenses", expanded=False):
    col1, col2, col3, col4, col5 = st.columns([2, 3, 3, 2, 2])
    with col1:
        new_date = st.date_input("Date")
    with col2:
        new_cat = st.selectbox(
            "Category",
            ["Housing", "Groceries", "Utilities", "Food & Dining", "Transportation", "Shopping", "Entertainment", "Health", "Personal Care", "Debt & Bills", "Other"],
        )
    with col3:
        new_desc = st.text_input("Description", placeholder="e.g. Amazon Electronics")
    with col4:
        new_amt = st.number_input("Amount ($)", min_value=0.01, value=50.0, step=5.0)
    with col5:
        st.write("")
        st.write("")
        if st.button("➕ Add Expense", use_container_width=True):
            if new_desc.strip():
                st.session_state.expenses.append(
                    ExpenseItem(
                        date=str(new_date),
                        category=new_cat,
                        description=new_desc.strip(),
                        amount=float(new_amt),
                    )
                )
                st.success("Expense added!")
                st.rerun()

    if st.session_state.expenses:
        expenses_df = pd.DataFrame([e.model_dump() for e in st.session_state.expenses])
        st.dataframe(expenses_df, use_container_width=True, height=200)
        if st.button("🗑️ Clear All Expenses"):
            st.session_state.expenses = []
            st.rerun()

# Build current profile & deterministic metrics
raw_user_profile = UserFinancialProfile(
    monthly_income=float(income_input),
    savings_target=float(savings_target_input),
    expenses=st.session_state.expenses,
)

# Apply PII Sanitizer if Privacy Mode is enabled
from services.privacy_service import sanitize_financial_profile
if privacy_mode:
    user_profile, red_count = sanitize_financial_profile(raw_user_profile)
else:
    user_profile = raw_user_profile
    red_count = 0

metrics = compute_baseline_metrics(user_profile)

# -------------------------------------------------------------
# Top KPI Metric Cards
# -------------------------------------------------------------
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Monthly Income</div>
        <div class="metric-value">${metrics.monthly_income:,.2f}</div>
        <div class="metric-delta-pos">Base Inflow</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Total Spend</div>
        <div class="metric-value">${metrics.total_spend:,.2f}</div>
        <div class="metric-delta-neg">{metrics.expense_to_income_pct:.1f}% of Income</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    is_positive = metrics.actual_savings >= 0
    delta_class = "metric-delta-pos" if is_positive else "metric-delta-neg"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Actual Savings</div>
        <div class="metric-value">${metrics.actual_savings:,.2f}</div>
        <div class="{delta_class}">{metrics.savings_rate_pct:.1f}% Savings Rate</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    gap_on_track = metrics.savings_gap <= 0
    gap_label = "On Track / Surplus" if gap_on_track else f"Shortfall: ${metrics.savings_gap:,.2f}"
    gap_class = "metric-delta-pos" if gap_on_track else "metric-delta-neg"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Savings Target Gap</div>
        <div class="metric-value">${abs(metrics.savings_gap):,.2f}</div>
        <div class="{gap_class}">{gap_label}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# -------------------------------------------------------------
# Interactive Visualizations & Tabs
# -------------------------------------------------------------
tab_charts, tab_ai, tab_scenarios, tab_export = st.tabs([
    "📊 Financial Visualizations & 50/30/20",
    "🤖 Gemini 3.7 Pro AI Analysis",
    "🎯 Autonomous Scenario Planner",
    "📥 Export & Compliance Center",
])

with tab_charts:
    col_chart_left, col_chart_right = st.columns(2)

    with col_chart_left:
        st.subheader("Category Spend Distribution")
        if metrics.category_breakdown:
            cat_df = pd.DataFrame(
                list(metrics.category_breakdown.items()),
                columns=["Category", "Amount"],
            )
            fig_pie = px.pie(
                cat_df,
                values="Amount",
                names="Category",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Prism,
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            fig_pie.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E2E8F0"),
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expenses logged yet.")

    with col_chart_right:
        st.subheader("50/30/20 Benchmark Comparison")
        f32 = metrics.fifty_thirty_twenty
        categories = ["Needs (50%)", "Wants (30%)", "Savings (20%)"]
        actual_vals = [f32.needs_actual, f32.wants_actual, f32.savings_actual]
        target_vals = [f32.needs_target, f32.wants_target, f32.savings_target]

        fig_bar = go.Figure(data=[
            go.Bar(name="Actual ($)", x=categories, y=actual_vals, marker_color="#3B82F6"),
            go.Bar(name="Target ($)", x=categories, y=target_vals, marker_color="#10B981"),
        ])
        fig_bar.update_layout(
            barmode="group",
            margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# -------------------------------------------------------------
# Gemini 3.7 Pro AI Analysis Section
# -------------------------------------------------------------
with tab_ai:
    st.subheader("🧠 Deep Financial Audit with Google Gemini 3.7 Pro")
    st.write(
        "Leverage Gemini 3.7 Pro via the official `google-genai` SDK with strict JSON schema validation to extract actionable savings recommendations, detect micro-leaks, and evaluate goal feasibility."
    )

    if st.button("🚀 Run AI Financial Diagnostics", type="primary", use_container_width=True):
        if not st.session_state.expenses:
            st.warning("Please add at least one expense before running the analysis.")
        else:
            with st.spinner("Analyzing cash flow, budget leaks, and generating recommendations..."):
                try:
                    report = generate_financial_analysis(
                        profile=user_profile,
                        metrics=metrics,
                        api_key=sidebar_api_key,
                    )
                    st.session_state.ai_report = report
                    st.success("Analysis Complete!")
                except Exception as err:
                    st.error(f"AI Analysis Encountered an Error: {str(err)}")

    if st.session_state.ai_report is not None:
        report = st.session_state.ai_report

        st.divider()
        col_score, col_summary = st.columns([1, 3])

        with col_score:
            st.markdown("#### Health Score")
            st.markdown(
                f"""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                    <div class="score-badge">{report.overall_health_score}</div>
                    <span style="margin-top: 8px; font-weight: 600; color: #94A3B8;">/ 100</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_summary:
            st.markdown("#### Executive Summary")
            st.info(report.health_summary)
            st.markdown(f"**🎯 Savings Goal Feasibility:** {report.savings_feasibility}")

        st.divider()
        col_leaks, col_anomalies = st.columns(2)

        with col_leaks:
            st.subheader("💧 Identified Budget Leaks")
            if report.budget_leaks:
                for leak in report.budget_leaks:
                    st.warning(
                        f"**{leak.category}** (Est. Monthly Waste: **${leak.estimated_monthly_waste:,.2f}** | Severity: **{leak.severity}**)\n\n"
                        f"{leak.description}"
                    )
            else:
                st.success("No significant recurring budget leaks detected!")

        with col_anomalies:
            st.subheader("⚠️ Spending Anomalies")
            if report.spending_anomalies:
                for anomaly in report.spending_anomalies:
                    st.error(
                        f"**{anomaly.item}** — **${anomaly.amount:,.2f}**\n\n"
                        f"{anomaly.reason}"
                    )
            else:
                st.success("No irregular spending anomalies identified.")

        st.divider()
        st.subheader("💡 Prioritized Actionable Recommendations")
        for rec in sorted(report.recommendations, key=lambda x: x.priority):
            st.markdown(
                f"""
                <div class="rec-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-weight: 700; font-size: 1.1rem; color: #60A5FA;">
                            #{rec.priority} {rec.title}
                        </span>
                        <span style="background: rgba(16, 185, 129, 0.2); color: #34D399; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">
                            Save ~${rec.potential_monthly_savings:,.2f}/mo
                        </span>
                    </div>
                    <p style="margin-bottom: 6px; color: #CBD5E1;">{rec.action_plan}</p>
                    <small style="color: #94A3B8;">Effort Level: <strong>{rec.difficulty}</strong></small>
                </div>
                """,
                unsafe_allow_html=True,
            )

# -------------------------------------------------------------
# Phase 3: Autonomous Scenario Planner & Goal Rebalancer Tab
# -------------------------------------------------------------
with tab_scenarios:
    st.subheader("🎯 Autonomous Milestone Rebalancer & Scenario Engine")
    st.write(
        "Simulate forward-looking cash-flow growth and debt paydown curves across **3 deterministic scenarios** (Status Quo, Balanced, and Aggressive) synthesized with Gemini 3.7 Pro quantitative planning."
    )

    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
    with col_g1:
        goal_type = st.selectbox(
            "Milestone Target Type",
            ["Emergency Fund (3-6mo)", "Debt Paydown (Snowball/Avalanche)", "Home Down Payment", "Major Purchase / Vehicle"],
        )
    with col_g2:
        target_amt = st.number_input("Target Amount ($)", min_value=100.0, value=10000.0, step=500.0)
    with col_g3:
        target_months = st.slider("Target Timeline (Months)", min_value=1, max_value=48, value=12)
    with col_g4:
        starting_bal = st.number_input("Starting Balance / Current Debt ($)", min_value=0.0, value=1000.0, step=250.0)

    from schemas import FinancialMilestoneGoal
    milestone_goal = FinancialMilestoneGoal(
        goal_type=goal_type,
        target_amount=float(target_amt),
        target_timeline_months=int(target_months),
        current_savings_or_debt=float(starting_bal),
    )

    if st.button("⚡ Run Autonomous Scenario Simulation", type="primary", use_container_width=True):
        with st.spinner("Simulating multi-scenario trajectories and optimizing budget schedules..."):
            try:
                from services.rebalancer_engine import generate_autonomous_simulation
                sim_report = generate_autonomous_simulation(
                    profile=user_profile,
                    metrics=metrics,
                    goal=milestone_goal,
                    api_key=sidebar_api_key,
                )
                st.session_state.sim_report = sim_report
                st.success("Autonomous Simulation Complete!")
            except Exception as sim_err:
                st.error(f"Simulation Error: {str(sim_err)}")

    if "sim_report" in st.session_state and st.session_state.sim_report is not None:
        s_rep = st.session_state.sim_report

        st.divider()
        st.markdown(f"### 📋 Strategic Summary: **{s_rep.recommended_scenario} Recommended**")
        st.info(s_rep.milestone_summary)
        st.markdown(f"**💡 Quantitative Strategic Advice:** {s_rep.strategic_advice}")

        # KPI Comparison Cards across the 3 scenarios
        c_sq, c_bal, c_agg = st.columns(3)
        with c_sq:
            sq = s_rep.status_quo_scenario
            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid #94A3B8;">
                <div class="metric-title">1. Status Quo Runway</div>
                <div class="metric-value">{sq.months_to_goal if sq.months_to_goal < 999 else '∞'} mos</div>
                <small style="color: #94A3B8;">Monthly Burn: <b>${sq.monthly_burn_rate:,.2f}</b></small><br>
                <small style="color: {'#10B981' if sq.goal_achieved_within_target else '#EF4444'}; font-weight: 600;">
                    {'✅ Met within deadline' if sq.goal_achieved_within_target else '❌ Misses target timeline'}
                </small>
            </div>
            """, unsafe_allow_html=True)

        with c_bal:
            bal = s_rep.balanced_scenario
            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid #3B82F6;">
                <div class="metric-title">2. Balanced Lifestyle (Rec)</div>
                <div class="metric-value">{bal.months_to_goal} mos</div>
                <small style="color: #94A3B8;">Monthly Savings: <b>+${bal.monthly_savings_accumulation:,.2f}/mo</b></small><br>
                <small style="color: {'#10B981' if bal.goal_achieved_within_target else '#EF4444'}; font-weight: 600;">
                    {'✅ Met within deadline' if bal.goal_achieved_within_target else '❌ Requires more time'}
                </small>
            </div>
            """, unsafe_allow_html=True)

        with c_agg:
            agg = s_rep.aggressive_scenario
            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid #10B981;">
                <div class="metric-title">3. Aggressive Austerity</div>
                <div class="metric-value">{agg.months_to_goal} mos</div>
                <small style="color: #94A3B8;">Max Savings: <b>+${agg.monthly_savings_accumulation:,.2f}/mo</b></small><br>
                <small style="color: #10B981; font-weight: 600;">🚀 Fastest Track ({agg.risk_level} Effort)</small>
            </div>
            """, unsafe_allow_html=True)

        # Plotly Cumulative Trajectory Chart
        st.write("")
        st.subheader("📈 Forward-Looking Balance & Paydown Trajectory")
        
        # Build DataFrame for trajectory curves
        max_len = max(
            len(sq.monthly_cumulative_balances),
            len(bal.monthly_cumulative_balances),
            len(agg.monthly_cumulative_balances),
        )
        months_axis = [f"Month {i+1}" for i in range(max_len)]
        
        fig_traj = go.Figure()
        fig_traj.add_trace(go.Scatter(
            x=months_axis,
            y=sq.monthly_cumulative_balances,
            mode="lines+markers",
            name="Status Quo",
            line=dict(color="#94A3B8", dash="dash"),
        ))
        fig_traj.add_trace(go.Scatter(
            x=months_axis,
            y=bal.monthly_cumulative_balances,
            mode="lines+markers",
            name="Balanced Lifestyle",
            line=dict(color="#3B82F6", width=3),
        ))
        fig_traj.add_trace(go.Scatter(
            x=months_axis,
            y=agg.monthly_cumulative_balances,
            mode="lines+markers",
            name="Aggressive Austerity",
            line=dict(color="#10B981", width=3),
        ))
        # Target threshold line
        fig_traj.add_hline(
            y=milestone_goal.target_amount,
            line_dash="dot",
            line_color="#F59E0B",
            annotation_text=f"Target Goal: ${milestone_goal.target_amount:,.2f}",
            annotation_position="bottom right",
        )
        fig_traj.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0"),
            margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_traj, use_container_width=True)

        # Granular Category Cut Schedule
        if s_rep.category_cut_schedule:
            st.subheader("✂️ Proposed Category Reduction Schedule")
            cuts_data = [
                {
                    "Category": c.category,
                    "Current Monthly Spend": f"${c.current_spend:,.2f}",
                    "Proposed Target Spend": f"${c.proposed_spend:,.2f}",
                    "Monthly Savings": f"+${c.monthly_cut_amount:,.2f}/mo",
                    "Rationale & Trade-offs": c.rationale_and_tradeoffs,
                }
                for c in s_rep.category_cut_schedule
            ]
            st.dataframe(pd.DataFrame(cuts_data), use_container_width=True)

# -------------------------------------------------------------
# Phase 4: Export & Compliance Center Tab
# -------------------------------------------------------------
with tab_export:
    st.subheader("📥 Enterprise Export & Compliance Center")
    st.write(
        "Generate audit-ready, cryptographically verified financial reports and export clean ledgers without local disk retention."
    )

    from services.export_service import (
        generate_executive_pdf_dossier,
        generate_audit_json_export,
        generate_clean_csv_ledger,
    )

    col_e1, col_e2, col_e3 = st.columns(3)

    # 1. Executive PDF Dossier
    with col_e1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">📄 Executive Dossier (PDF)</div>
            <p style="font-size: 0.85rem; color: #94A3B8;">Formatted PDF summary with KPI cards, 50/30/20 compliance tables, budget leaks, and AI recommendations.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        pdf_bytes = generate_executive_pdf_dossier(
            profile=user_profile,
            metrics=metrics,
            ai_report=st.session_state.ai_report,
            sim_report=st.session_state.get("sim_report"),
        )
        st.download_button(
            label="⬇️ Download Executive PDF",
            data=pdf_bytes,
            file_name="pocketsmart_financial_dossier.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )

    # 2. Audit-Ready Structured JSON
    with col_e2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">🔐 Audit Snapshot (JSON)</div>
            <p style="font-size: 0.85rem; color: #94A3B8;">Complete schema state with SHA-256 tamper-evident cryptographic seal for regulatory audit compliance.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        audit_json = generate_audit_json_export(
            profile=user_profile,
            metrics=metrics,
            ai_report=st.session_state.ai_report,
            sim_report=st.session_state.get("sim_report"),
        )
        st.download_button(
            label="⬇️ Download Audit JSON",
            data=audit_json,
            file_name="pocketsmart_audit_snapshot.json",
            mime="application/json",
            use_container_width=True,
        )

    # 3. Clean Sanitized CSV Ledger
    with col_e3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">📊 Normalized Ledger (CSV)</div>
            <p style="font-size: 0.85rem; color: #94A3B8;">Sanitized spreadsheet with normalized categories and stripped PII ready for Excel or accounting tools.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        clean_csv = generate_clean_csv_ledger(user_profile)
        st.download_button(
            label="⬇️ Download Ledger CSV",
            data=clean_csv,
            file_name="pocketsmart_clean_ledger.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.divider()
    st.markdown("### 🔒 Privacy & Compliance Architecture")
    if privacy_mode:
        st.success(f"🛡️ **High Privacy Mode Active**: All transaction feeds are scrubbed of PII before sending to Google Cloud. ({red_count} sensitive tokens redacted in active profile).")
    else:
        st.warning("⚠️ High Privacy Mode is currently disabled. Raw descriptions will be sent to the Gemini API.")



# -------------------------------------------------------------
# Phase 2: Grounded Multi-Turn Financial Chatbot ("Ask PocketSmart AI")
# -------------------------------------------------------------
st.write("")
st.divider()
st.subheader("💬 Ask PocketSmart AI (Real-Time Financial Copilot)")
st.caption("Ask questions about your budget, test hypothetical purchases, or brainstorm savings plans grounded in your verified financial data.")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": f"Hello! I'm your **PocketSmart Copilot**. I'm grounded in your monthly net income of **${metrics.monthly_income:,.2f}** and current spend of **${metrics.total_spend:,.2f}**. How can I help you optimize your cash flow today?"}
    ]

# Suggested Quick-Prompt Pills
st.markdown("**Suggested Questions:**")
col_p1, col_p2, col_p3 = st.columns(3)
quick_prompt = None

with col_p1:
    if st.button("✂️ How can I cut $200 from dining?", use_container_width=True):
        quick_prompt = "How can I cut $200 from my food and dining budget based on my transactions?"
with col_p2:
    if st.button("✈️ Can I afford a $1,200 vacation?", use_container_width=True):
        quick_prompt = "Can I afford a $1,200 vacation next month given my current savings gap?"
with col_p3:
    if st.button("📊 Explain my 50/30/20 balance", use_container_width=True):
        quick_prompt = "Explain my 50/30/20 balance and how to rebalance my Wants vs Savings."

# Render existing chat messages
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input Handler
user_input = st.chat_input("Ask PocketSmart Copilot a financial question...") or quick_prompt

if user_input:
    # Append user message
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Stream assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            from services.chat_service import stream_chat_response
            response_generator = stream_chat_response(
                messages=st.session_state.chat_history,
                profile=user_profile,
                metrics=metrics,
                ai_report=st.session_state.ai_report,
                api_key=sidebar_api_key,
            )
            for chunk in response_generator:
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})
        except Exception as chat_err:
            error_msg = f"⚠️ Chat encountered an error: {str(chat_err)}"
            message_placeholder.markdown(error_msg)
            st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

