"""
Budget calculation engine for PocketSmart AI.
Performs deterministic mathematical aggregation, savings gap analysis,
and standard 50/30/20 budget framework comparisons.
"""
from typing import List, Dict, Tuple, Any

import pandas as pd
from schemas import (
    ExpenseItem,
    UserFinancialProfile,
    FiftyThirtyTwentyComparison,
    BaselineBudgetMetrics,
)

# Canonical categorization mappings for 50/30/20 allocation
NEEDS_CATEGORIES = {
    "housing",
    "rent",
    "mortgage",
    "utilities",
    "groceries",
    "healthcare",
    "health",
    "insurance",
    "transportation",
    "transit",
    "debt minimums",
    "bills",
}

WANTS_CATEGORIES = {
    "entertainment",
    "dining out",
    "food & dining",
    "shopping",
    "travel",
    "hobbies",
    "personal care",
    "subscriptions",
    "fitness",
    "leisure",
    "misc",
}


def parse_csv_transactions(file_stream) -> List[ExpenseItem]:
    """
    Parses an uploaded CSV file containing transactions and converts to List[ExpenseItem].
    Supports flexible column headers: amount, category, description, date.
    Accepts file object, stream, or raw string content.
    """
    import io
    if isinstance(file_stream, str):
        file_stream = io.StringIO(file_stream)

    try:
        df = pd.read_csv(file_stream, comment="#")
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {str(e)}")



    if df.empty:
        raise ValueError("The uploaded CSV file is empty.")

    # Normalize column names
    col_map = {}
    for col in df.columns:
        clean_col = str(col).strip().lower()
        if clean_col in ["amount", "cost", "price", "total", "spent"]:
            col_map[col] = "amount"
        elif clean_col in ["category", "type", "tag", "group"]:
            col_map[col] = "category"
        elif clean_col in ["description", "desc", "merchant", "item", "memo", "title"]:
            col_map[col] = "description"
        elif clean_col in ["date", "timestamp", "transaction_date"]:
            col_map[col] = "date"

    df = df.rename(columns=col_map)

    # Validate required columns
    required = ["amount"]
    missing = [req for req in required if req not in df.columns]
    if missing:
        raise ValueError(f"CSV missing mandatory column(s): {', '.join(missing)}. Please provide at least an 'amount' column.")

    if "category" not in df.columns:
        df["category"] = "General"
    if "description" not in df.columns:
        df["description"] = "Uncategorized Transaction"
    if "date" not in df.columns:
        df["date"] = None

    # Clean amount column
    df["amount"] = pd.to_numeric(df["amount"].astype(str).str.replace(r"[^\d.-]", "", regex=True), errors="coerce")
    df = df.dropna(subset=["amount"])
    df = df[df["amount"] > 0]

    expenses: List[ExpenseItem] = []
    for _, row in df.iterrows():
        expenses.append(
            ExpenseItem(
                date=str(row["date"]) if pd.notna(row["date"]) else None,
                category=str(row["category"]).strip() if pd.notna(row["category"]) else "General",
                description=str(row["description"]).strip() if pd.notna(row["description"]) else "Expense",
                amount=float(row["amount"]),
            )
        )

    if not expenses:
        raise ValueError("No valid positive expense items found in the CSV.")

    return expenses


def calculate_category_breakdown(expenses: List[ExpenseItem]) -> Dict[str, float]:
    """Calculates aggregate spending aggregated by category."""
    breakdown: Dict[str, float] = {}
    for item in expenses:
        cat = item.category.strip().title()
        breakdown[cat] = round(breakdown.get(cat, 0.0) + item.amount, 2)
    return breakdown


def calculate_fifty_thirty_twenty(
    income: float, category_breakdown: Any
) -> FiftyThirtyTwentyComparison:
    """
    Computes Needs (50%), Wants (30%), and Savings (20%) breakdown deterministically.
    Accepts category_breakdown as either Dict[str, float] or List[ExpenseItem].
    """
    if isinstance(category_breakdown, list):
        category_breakdown = calculate_category_breakdown(category_breakdown)

    needs_actual = 0.0
    wants_actual = 0.0

    for cat_name, amt in category_breakdown.items():

        lowered = cat_name.lower()
        if any(need in lowered for need in NEEDS_CATEGORIES):
            needs_actual += amt
        else:
            wants_actual += amt

    total_spent = needs_actual + wants_actual
    actual_savings = max(0.0, income - total_spent)

    needs_pct = (needs_actual / income * 100) if income > 0 else 0.0
    wants_pct = (wants_actual / income * 100) if income > 0 else 0.0
    savings_pct = (actual_savings / income * 100) if income > 0 else 0.0

    return FiftyThirtyTwentyComparison(
        needs_actual=round(needs_actual, 2),
        needs_pct=round(needs_pct, 1),
        needs_target=round(income * 0.50, 2),
        wants_actual=round(wants_actual, 2),
        wants_pct=round(wants_pct, 1),
        wants_target=round(income * 0.30, 2),
        savings_actual=round(actual_savings, 2),
        savings_pct=round(savings_pct, 1),
        savings_target=round(income * 0.20, 2),
    )


def compute_baseline_metrics(profile: UserFinancialProfile) -> BaselineBudgetMetrics:
    """
    Core mathematical engine that produces all baseline financial metrics deterministically.
    """
    total_spend = sum(exp.amount for exp in profile.expenses)
    actual_savings = profile.monthly_income - total_spend
    savings_gap = profile.savings_target - actual_savings
    
    savings_rate_pct = (actual_savings / profile.monthly_income * 100) if profile.monthly_income > 0 else 0.0
    expense_to_income_pct = (total_spend / profile.monthly_income * 100) if profile.monthly_income > 0 else 0.0
    
    category_breakdown = calculate_category_breakdown(profile.expenses)
    fifty_thirty_twenty = calculate_fifty_thirty_twenty(profile.monthly_income, category_breakdown)

    return BaselineBudgetMetrics(
        total_spend=round(total_spend, 2),
        monthly_income=round(profile.monthly_income, 2),
        target_savings=round(profile.savings_target, 2),
        actual_savings=round(actual_savings, 2),
        savings_gap=round(savings_gap, 2),
        savings_rate_pct=round(savings_rate_pct, 1),
        expense_to_income_pct=round(expense_to_income_pct, 1),
        category_breakdown=category_breakdown,
        fifty_thirty_twenty=fifty_thirty_twenty,
    )
