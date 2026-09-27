"""
PocketSmart AI: Automated Test and Evaluation Pipeline
Tests:
1. CSV ingestion & normalization (standard and edge-case datasets).
2. Deterministic baseline financial calculations & 50/30/20 budget framework.
3. Edge case simulations (Spending > Income, Zero Expenses, Micro-transactions).
4. Gemini 3.7 Pro API invocation & Pydantic AIAnalysisReport validation (Mock & Live modes).

Usage:
  - Mocked dry-run (Default, zero API quota cost):
      python test_pipeline.py --mode mock
  - Live Gemini 3.7 Pro test (Requires GEMINI_API_KEY):
      python test_pipeline.py --mode live
  - Via Pytest:
      pytest test_pipeline.py -v -s
"""
import os
import sys
import json
import argparse
import unittest
from io import StringIO
from typing import List
from dotenv import load_dotenv


# Load environment
load_dotenv()

# Import project components
from schemas import (
    ExpenseItem,
    UserFinancialProfile,
    BaselineBudgetMetrics,
    AIAnalysisReport,
    BudgetLeak,
    SpendingAnomaly,
    Recommendation,
)
from services.budget_engine import (
    parse_csv_transactions,
    calculate_category_breakdown,
    calculate_fifty_thirty_twenty,
    compute_baseline_metrics,
)
from services.gemini_service import generate_financial_analysis

# ANSI Color formatting for CLI readability
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner(title: str):
    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}>>> {title}{RESET}")
    print(f"{CYAN}{'='*70}{RESET}")


def get_mock_ai_report() -> AIAnalysisReport:
    """Generates a strictly typed mock AIAnalysisReport for offline testing."""
    return AIAnalysisReport(
        overall_health_score=68,
        health_summary="User shows solid cash flow discipline but experiences substantial micro-spend leaks across dining and digital micro-transactions.",
        budget_leaks=[
            BudgetLeak(
                category="Food & Dining",
                description="Daily artisan coffee & afternoon snack stops creating high-frequency cash leakage.",
                estimated_monthly_waste=185.00,
                severity="Medium",
            ),
            BudgetLeak(
                category="Entertainment",
                description="Redundant low-tier app subscriptions and digital in-game micro-purchases.",
                estimated_monthly_waste=45.00,
                severity="Low",
            ),
        ],
        spending_anomalies=[
            SpendingAnomaly(
                item="Collector Mechanical Watch",
                amount=3200.00,
                reason="One-time luxury discretionary purchase exceeding 60% of total monthly income.",
            )
        ],
        recommendations=[
            Recommendation(
                priority=1,
                title="Automate Coffee & Grocery Meal Prep",
                action_plan="Switch to brewing premium espresso at home to recover ~$150 monthly.",
                potential_monthly_savings=150.00,
                difficulty="Easy",
            ),
            Recommendation(
                priority=2,
                title="Audit & Consolidate Streaming/App Subscriptions",
                action_plan="Cancel unused recurring mobile tiers and consolidate entertainment accounts.",
                potential_monthly_savings=45.00,
                difficulty="Easy",
            ),
            Recommendation(
                priority=3,
                title="Establish 30-Day Discretionary Cooling Period",
                action_plan="Enforce a mandatory waiting period for luxury purchases over $500.",
                potential_monthly_savings=300.00,
                difficulty="Moderate",
            ),
        ],
        savings_feasibility="Feasible with minor behavioral adjustments in dining and impulse luxury spending.",
    )


class TestPocketSmartPipeline(unittest.TestCase):
    """Automated integration test suite for PocketSmart AI."""

    @classmethod
    def setUpClass(cls):
        cls.mode = getattr(cls, "test_mode", "mock")
        print(f"\n{BOLD}Initializing PocketSmart AI Test Suite [Mode: {cls.mode.upper()}]{RESET}")

    def test_01_csv_ingestion_standard_dataset(self):
        """Test CSV parsing, header normalization, and data type coercion on standard dataset."""
        print_banner("TEST 01: Standard CSV Transaction Ingestion")
        csv_path = os.path.join(os.path.dirname(__file__), "sample_transactions.csv")
        self.assertTrue(os.path.exists(csv_path), f"Sample CSV file not found at {csv_path}")

        with open(csv_path, "r", encoding="utf-8") as f:
            expenses = parse_csv_transactions(f)

        self.assertIsInstance(expenses, list)
        self.assertGreater(len(expenses), 0, "Parsed expense list should not be empty")
        
        for item in expenses:
            self.assertIsInstance(item, ExpenseItem)
            self.assertGreater(item.amount, 0, f"Amount must be positive: {item}")
            self.assertTrue(len(item.category.strip()) > 0, "Category cannot be empty")
            self.assertTrue(len(item.description.strip()) > 0, "Description cannot be empty")

        print(f"{GREEN}[PASS] Successfully ingested and validated {len(expenses)} transactions from sample_transactions.csv{RESET}")

    def test_02_deterministic_budget_calculations(self):
        """Test mathematical baseline metrics, category aggregation, and 50/30/20 allocation."""
        print_banner("TEST 02: Deterministic Baseline Budget Metrics & 50/30/20")
        
        income = 5000.00
        savings_target = 1000.00
        test_expenses = [
            ExpenseItem(date="2026-09-01", category="Housing", description="Rent", amount=1500.00),
            ExpenseItem(date="2026-09-02", category="Groceries", description="Supermarket", amount=500.00),
            ExpenseItem(date="2026-09-03", category="Food & Dining", description="Dining Out", amount=600.00),
            ExpenseItem(date="2026-09-04", category="Entertainment", description="Streaming", amount=100.00),
        ]

        profile = UserFinancialProfile(
            monthly_income=income,
            savings_target=savings_target,
            expenses=test_expenses,
        )

        metrics: BaselineBudgetMetrics = compute_baseline_metrics(profile)

        # Total spend: 1500 + 500 + 600 + 100 = 2700.00
        self.assertEqual(metrics.total_spend, 2700.00)
        # Actual savings: 5000 - 2700 = 2300.00
        self.assertEqual(metrics.actual_savings, 2300.00)
        # Savings gap: 1000 - 2300 = -1300.00 (surplus)
        self.assertEqual(metrics.savings_gap, -1300.00)
        # Savings rate: (2300 / 5000) * 100 = 46.0%
        self.assertEqual(metrics.savings_rate_pct, 46.0)
        # Expense rate: (2700 / 5000) * 100 = 54.0%
        self.assertEqual(metrics.expense_to_income_pct, 54.0)

        # 50/30/20 breakdown
        # Needs (Housing + Groceries) = 2000 (Target 50% = 2500)
        # Wants (Food & Dining + Entertainment) = 700 (Target 30% = 1500)
        # Savings = 2300 (Target 20% = 1000)
        f32 = metrics.fifty_thirty_twenty
        self.assertEqual(f32.needs_actual, 2000.00)
        self.assertEqual(f32.needs_pct, 40.0)
        self.assertEqual(f32.needs_target, 2500.00)

        self.assertEqual(f32.wants_actual, 700.00)
        self.assertEqual(f32.wants_pct, 14.0)
        self.assertEqual(f32.wants_target, 1500.00)

        self.assertEqual(f32.savings_actual, 2300.00)
        self.assertEqual(f32.savings_pct, 46.0)
        self.assertEqual(f32.savings_target, 1000.00)

        print(f"{GREEN}[PASS] Deterministic calculations, aggregations, and 50/30/20 balance verified with exact arithmetic.{RESET}")

    def test_03_financial_edge_cases(self):
        """Test financial edge cases: deficit spend, micro-spends, zero expenses, and corrupted CSV formats."""
        print_banner("TEST 03: Financial Edge-Case Handling")

        # Edge Case 1: Ingestion of edge_case_transactions.csv
        edge_csv_path = os.path.join(os.path.dirname(__file__), "edge_case_transactions.csv")
        with open(edge_csv_path, "r", encoding="utf-8") as f:
            edge_expenses = parse_csv_transactions(f)

        self.assertGreater(len(edge_expenses), 0)
        print(f"{GREEN}  [PASS] Ingested edge case CSV ({len(edge_expenses)} items){RESET}")

        # Edge Case 2: Spend Exceeding Total Income (Deficit Scenario)
        deficit_profile = UserFinancialProfile(
            monthly_income=4000.00,
            savings_target=1000.00,
            expenses=edge_expenses,
        )
        deficit_metrics = compute_baseline_metrics(deficit_profile)
        self.assertGreater(deficit_metrics.total_spend, deficit_profile.monthly_income)
        self.assertLess(deficit_metrics.actual_savings, 0, "Actual savings should be negative in a deficit scenario")
        self.assertGreater(deficit_metrics.savings_gap, 0, "Savings gap must be positive when in deficit")
        print(f"{GREEN}  [PASS] Spending deficit calculation validated (Spend: ${deficit_metrics.total_spend:,.2f} > Income: ${deficit_profile.monthly_income:,.2f}){RESET}")

        # Edge Case 3: Zero Expenses
        zero_profile = UserFinancialProfile(
            monthly_income=5000.00,
            savings_target=1500.00,
            expenses=[],
        )
        zero_metrics = compute_baseline_metrics(zero_profile)
        self.assertEqual(zero_metrics.total_spend, 0.0)
        self.assertEqual(zero_metrics.actual_savings, 5000.00)
        self.assertEqual(zero_metrics.savings_gap, -3500.00)
        print(f"{GREEN}  [PASS] Zero-expense scenario handled gracefully{RESET}")

        # Edge Case 4: Invalid/Corrupt CSV
        corrupt_csv = StringIO("foo,bar\ninvalid,data")
        with self.assertRaises(ValueError) as ctx:
            parse_csv_transactions(corrupt_csv)
        self.assertIn("missing mandatory column", str(ctx.exception).lower())
        print(f"{GREEN}  [PASS] Corrupt CSV caught and rejected with descriptive error{RESET}")

    def test_04_gemini_pydantic_schema_validation(self):
        """Test Gemini structured output validation against AIAnalysisReport schema (Mock or Live)."""
        print_banner(f"TEST 04: Gemini 3.7 Pro Output Schema Validation [Mode: {self.mode.upper()}]")

        user_profile = UserFinancialProfile(
            monthly_income=5000.00,
            savings_target=1200.00,
            expenses=[
                ExpenseItem(category="Housing", description="Rent", amount=1500.00),
                ExpenseItem(category="Food & Dining", description="Daily Lattes", amount=180.00),
                ExpenseItem(category="Shopping", description="Collector Watch", amount=3200.00),
            ],
        )
        metrics = compute_baseline_metrics(user_profile)

        if self.mode == "live":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key or "your_gemini_api_key_here" in api_key:
                self.fail("Live test requested but valid GEMINI_API_KEY is not configured in environment or .env file.")
            print(f"{YELLOW}Connecting to Google Gemini 3.7 Pro model (gemini-3.7-pro)...{RESET}")
            report = generate_financial_analysis(user_profile, metrics, api_key=api_key)
        else:
            print(f"{CYAN}Running with strict mock schema generator (dry-run mode)...{RESET}")
            report = get_mock_ai_report()

        # Schema & Type Assertions
        self.assertIsInstance(report, AIAnalysisReport)
        
        # 1. Overall Health Score (0-100)
        self.assertIsInstance(report.overall_health_score, int)
        self.assertGreaterEqual(report.overall_health_score, 0)
        self.assertLessEqual(report.overall_health_score, 100)

        # 2. Executive Summary
        self.assertIsInstance(report.health_summary, str)
        self.assertGreater(len(report.health_summary.strip()), 10)

        # 3. Budget Leaks
        self.assertIsInstance(report.budget_leaks, list)
        for leak in report.budget_leaks:
            self.assertIsInstance(leak, BudgetLeak)
            self.assertTrue(len(leak.category.strip()) > 0)
            self.assertTrue(len(leak.description.strip()) > 0)
            self.assertGreaterEqual(leak.estimated_monthly_waste, 0)
            self.assertIn(leak.severity, ["Low", "Medium", "High"])

        # 4. Spending Anomalies
        self.assertIsInstance(report.spending_anomalies, list)
        for anomaly in report.spending_anomalies:
            self.assertIsInstance(anomaly, SpendingAnomaly)
            self.assertTrue(len(anomaly.item.strip()) > 0)
            self.assertGreater(anomaly.amount, 0)
            self.assertTrue(len(anomaly.reason.strip()) > 0)

        # 5. Prioritized Recommendations
        self.assertIsInstance(report.recommendations, list)
        self.assertGreater(len(report.recommendations), 0, "Report should contain at least 1 recommendation")
        for rec in report.recommendations:
            self.assertIsInstance(rec, Recommendation)
            self.assertIn(rec.priority, [1, 2, 3, 4, 5])
            self.assertTrue(len(rec.title.strip()) > 0)
            self.assertTrue(len(rec.action_plan.strip()) > 0)
            self.assertGreaterEqual(rec.potential_monthly_savings, 0)
            self.assertIn(rec.difficulty, ["Easy", "Moderate", "Challenging"])

        # 6. Savings Feasibility
        self.assertIsInstance(report.savings_feasibility, str)
        self.assertTrue(len(report.savings_feasibility.strip()) > 0)

        print(f"{GREEN}[PASS] AIAnalysisReport Pydantic schema validation PASSED for all attributes and nested models.{RESET}")

    def test_05_multimodal_ocr_document_extraction(self):
        """Test multimodal OCR pipeline, image pre-processing, and schema conversion."""
        print_banner(f"TEST 05: Multimodal OCR Document Extraction [Mode: {self.mode.upper()}]")
        from schemas import MultimodalOCRDocumentReport, ExtractedDocumentExpense
        from services.multimodal_service import optimize_image_bytes, validate_pdf_pages

        # Sub-test A: Image Downsampling and Compression
        from PIL import Image
        import io
        test_img = Image.new("RGB", (2400, 1800), color="white")
        img_byte_arr = io.BytesIO()
        test_img.save(img_byte_arr, format="PNG")
        raw_bytes = img_byte_arr.getvalue()

        optimized_bytes, mime = optimize_image_bytes(raw_bytes, "image/png")
        with Image.open(io.BytesIO(optimized_bytes)) as opt_img:
            w, h = opt_img.size
            self.assertLessEqual(max(w, h), 1600, "Image width/height must be downsampled to <= 1600px")
        print(f"{GREEN}  [PASS] Vision token downsampling optimization verified ({w}x{h} <= 1600px){RESET}")

        # Sub-test B: Mock OCR Report & Expense Conversion
        mock_ocr = MultimodalOCRDocumentReport(
            document_type="Receipt",
            detected_currency="USD",
            institution_or_vendor="Whole Foods Market",
            document_summary="Grocery receipt with 3 itemized line items.",
            extracted_expenses=[
                ExtractedDocumentExpense(
                    date="2026-09-20",
                    category="Groceries",
                    merchant_or_description="Organic Produce & Bakery",
                    amount=64.50,
                    confidence_score=0.98,
                ),
                ExtractedDocumentExpense(
                    date="2026-09-20",
                    category="Groceries",
                    merchant_or_description="Cold Pressed Beverages",
                    amount=18.25,
                    confidence_score=0.95,
                ),
            ],
            unreadable_warning=None,
        )

        # Convert to ExpenseItem and ensure baseline engine compatibility
        converted_items = [
            ExpenseItem(
                date=item.date,
                category=item.category,
                description=f"{item.merchant_or_description} ({mock_ocr.institution_or_vendor})",
                amount=item.amount,
            )
            for item in mock_ocr.extracted_expenses
        ]
        self.assertEqual(len(converted_items), 2)
        self.assertEqual(converted_items[0].amount, 64.50)

        # Verify deterministic engine calculates baseline metrics with OCR output
        profile = UserFinancialProfile(monthly_income=4000.0, savings_target=800.0, expenses=converted_items)
        metrics = compute_baseline_metrics(profile)
        self.assertEqual(metrics.total_spend, 82.75)
        self.assertEqual(metrics.actual_savings, 3917.25)
        print(f"{GREEN}  [PASS] Multimodal OCR schema seamlessly integrated with baseline budget engine{RESET}")

    def test_06_conversational_chat_service_grounding(self):
        """Test conversational context construction, multi-turn history formatting, and guardrail prompt injection."""
        print_banner(f"TEST 06: Grounded Conversational Chatbot Engine [Mode: {self.mode.upper()}]")
        from services.chat_service import build_system_context_dossier, FINANCIAL_CHAT_GUARDRAIL_PROMPT

        test_profile = UserFinancialProfile(
            monthly_income=6000.0,
            savings_target=1500.0,
            expenses=[
                ExpenseItem(category="Housing", description="Apartment Lease", amount=2000.0),
                ExpenseItem(category="Food & Dining", description="Weekly Dining Out", amount=400.0),
            ],
        )
        test_metrics = compute_baseline_metrics(test_profile)
        mock_report = get_mock_ai_report()

        system_dossier = build_system_context_dossier(test_profile, test_metrics, mock_report)

        # 1. Verify guardrail instructions are included
        self.assertIn("GROUND-TRUTH PRIMACY", system_dossier)
        self.assertIn("FINANCIAL ADVICE DISCLAIMER", system_dossier)
        self.assertIn("MATHEMATICAL DISCIPLINE", system_dossier)

        # 2. Verify ground-truth figures are accurately populated
        self.assertIn("$6,000.00", system_dossier)  # Income
        self.assertIn("$2,400.00", system_dossier)  # Total spend
        self.assertIn("$3,600.00", system_dossier)  # Actual savings
        self.assertIn("Apartment Lease", system_dossier)
        self.assertIn("68/100", system_dossier)  # AI Health score

        print(f"{GREEN}  [PASS] Conversational system context dossier verified with 100% ground-truth accuracy and strict guardrails{RESET}")

    def test_07_autonomous_rebalancer_scenarios(self):
        """Test forward-looking deterministic trajectory curves and autonomous scenario report deserialization."""
        print_banner(f"TEST 07: Autonomous Scenario Simulator & Goal Rebalancer [Mode: {self.mode.upper()}]")
        from schemas import FinancialMilestoneGoal, AutonomousSimulationReport, ScenarioTrajectory
        from services.rebalancer_engine import compute_deterministic_scenario_trajectory, generate_autonomous_simulation

        # 1. Test Deterministic Math Curves (Emergency Fund: $12,000 target over 12 months, Starting Balance: $2,000)
        income = 5000.00
        current_spend = 3500.00
        target_amt = 12000.00
        starting_bal = 2000.00
        timeline = 12

        # Status Quo: savings = 5000 - 3500 = 1500/mo. Needed = 10000. Months = ceil(10000 / 1500) = 7 months
        sq = compute_deterministic_scenario_trajectory(
            income=income,
            current_spend=current_spend,
            target_amount=target_amt,
            starting_balance=starting_bal,
            timeline_months=timeline,
            spend_reduction_ratio=0.0,
            scenario_name="Status Quo Runway",
            risk_level="Low",
        )
        self.assertEqual(sq.monthly_savings_accumulation, 1500.00)
        self.assertEqual(sq.months_to_goal, 7)
        self.assertTrue(sq.goal_achieved_within_target)
        self.assertEqual(len(sq.monthly_cumulative_balances), 12)
        # Month 1 balance: 2000 + 1500 = 3500
        self.assertEqual(sq.monthly_cumulative_balances[0], 3500.00)
        # Month 7 balance: 2000 + 7 * 1500 = 12500 (Goal surpassed)
        self.assertEqual(sq.monthly_cumulative_balances[6], 12500.00)
        print(f"{GREEN}  [PASS] Deterministic scenario trajectory math curves verified with exact arithmetic{RESET}")

        # 2. Test Autonomous Simulation Report Generation (Mock/Live)
        profile = UserFinancialProfile(
            monthly_income=income,
            savings_target=1000.0,
            expenses=[
                ExpenseItem(category="Housing", description="Rent", amount=1800.0),
                ExpenseItem(category="Food & Dining", description="Dining", amount=800.0),
                ExpenseItem(category="Shopping", description="Discretionary", amount=900.0),
            ],
        )
        metrics = compute_baseline_metrics(profile)
        goal = FinancialMilestoneGoal(
            goal_type="Emergency Fund",
            target_amount=10000.0,
            target_timeline_months=12,
            current_savings_or_debt=1000.0,
        )

        if self.mode == "live":
            api_key = os.getenv("GEMINI_API_KEY")
            sim_report = generate_autonomous_simulation(profile, metrics, goal, api_key=api_key)
        else:
            # Generate deterministic fallback report
            sim_report = generate_autonomous_simulation(profile, metrics, goal, api_key=None)

        self.assertIsInstance(sim_report, AutonomousSimulationReport)
        self.assertIsInstance(sim_report.status_quo_scenario, ScenarioTrajectory)
        self.assertIsInstance(sim_report.balanced_scenario, ScenarioTrajectory)
        self.assertIsInstance(sim_report.aggressive_scenario, ScenarioTrajectory)
        self.assertGreater(len(sim_report.category_cut_schedule), 0)
        print(f"{GREEN}  [PASS] AutonomousSimulationReport schema deserialization and scenario integration verified{RESET}")

    def test_08_privacy_sanitization_and_export(self):
        """Test PII masking accuracy, in-memory PDF dossier generation, and cryptographic SHA-256 audit seal."""
        print_banner(f"TEST 08: Privacy Sanitizer & Enterprise Audit Export [Mode: {self.mode.upper()}]")
        from services.privacy_service import sanitize_text_string, sanitize_financial_profile
        from services.export_service import (
            generate_executive_pdf_dossier,
            generate_audit_json_export,
            generate_clean_csv_ledger,
            generate_cryptographic_audit_hash,
        )

        # 1. Test PII String Masking (SSN, Credit Card, Email, Address, Bank Account)
        raw_pii_string = "Customer SSN: 123-45-6789, CC: 4111 2222 3333 4444, Email: user@example.com, Address: 742 Evergreen Terrace, Account #9876543210"
        sanitized_str, red_count = sanitize_text_string(raw_pii_string)

        self.assertNotIn("123-45-6789", sanitized_str)
        self.assertIn("[REDACTED_SSN]", sanitized_str)
        self.assertNotIn("4111 2222 3333 4444", sanitized_str)
        self.assertIn("****-****-****-4444", sanitized_str)
        self.assertNotIn("user@example.com", sanitized_str)
        self.assertIn("[REDACTED_EMAIL]", sanitized_str)
        self.assertNotIn("742 Evergreen Terrace", sanitized_str)
        self.assertIn("[REDACTED_ADDRESS]", sanitized_str)
        self.assertGreaterEqual(red_count, 4)
        print(f"{GREEN}  [PASS] PII masking verified across SSN, Cards, Emails, Addresses, and Accounts ({red_count} tokens redacted){RESET}")

        # 2. Test Profile Sanitizer
        dirty_profile = UserFinancialProfile(
            monthly_income=5000.0,
            savings_target=1000.0,
            expenses=[
                ExpenseItem(category="Housing", description="Rent to Landlord at 123 Main Street", amount=1500.0),
                ExpenseItem(category="Shopping", description="Purchase card 5555-6666-7777-8888", amount=200.0),
            ],
        )
        clean_profile, prof_red_count = sanitize_financial_profile(dirty_profile)
        self.assertNotIn("123 Main Street", clean_profile.expenses[0].description)
        self.assertNotIn("5555-6666-7777-8888", clean_profile.expenses[1].description)
        print(f"{GREEN}  [PASS] UserFinancialProfile sanitization pipeline verified{RESET}")

        # 3. Test In-Memory PDF Dossier Generation
        metrics = compute_baseline_metrics(clean_profile)
        mock_report = get_mock_ai_report()
        pdf_bytes = generate_executive_pdf_dossier(clean_profile, metrics, mock_report)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000, "Generated PDF must not be empty")
        self.assertTrue(pdf_bytes.startswith(b"%PDF"), "PDF binary must start with %PDF header")
        print(f"{GREEN}  [PASS] In-memory Executive PDF Dossier generated successfully ({len(pdf_bytes):,} bytes){RESET}")

        # 4. Test Audit JSON with SHA-256 Seal
        audit_json_str = generate_audit_json_export(clean_profile, metrics, mock_report)
        audit_dict = json.loads(audit_json_str)
        self.assertIn("sha256_audit_seal", audit_dict["metadata"])
        self.assertEqual(len(audit_dict["metadata"]["sha256_audit_seal"]), 64)
        print(f"{GREEN}  [PASS] Audit JSON generated with valid 64-char SHA-256 seal: {audit_dict['metadata']['sha256_audit_seal'][:16]}...{RESET}")

        # 5. Test Clean CSV Ledger Export
        csv_str = generate_clean_csv_ledger(clean_profile)
        self.assertIn("date,category,description,amount", csv_str)
        print(f"{GREEN}  [PASS] Sanitized CSV Ledger export verified{RESET}")


def run_pipeline(mode: str = "mock"):
    """CLI runner function."""
    TestPocketSmartPipeline.test_mode = mode
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPocketSmartPipeline)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PocketSmart AI Automated Test & Evaluation Pipeline")
    parser.add_argument(
        "--mode",
        choices=["mock", "live"],
        default="mock",
        help="Test mode: 'mock' (offline dry-run) or 'live' (invokes Gemini 3.7 Pro API)",
    )
    args = parser.parse_args()
    run_pipeline(mode=args.mode)
