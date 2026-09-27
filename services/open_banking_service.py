"""
services/open_banking_service.py
Plaid / Salt Edge Open-Banking Ingestion, Webhook Verification, and State Normalization.
"""

import hmac
import hashlib
import json
from typing import Dict, Any, List, Tuple
from schemas import ExpenseItem

def verify_webhook_signature(payload_bytes: bytes, signature_header: str, webhook_secret: str) -> bool:
    """Verifies Plaid/banking HMAC-SHA256 webhook signatures against the shared secret."""
    if not signature_header or not webhook_secret:
        return False
    expected_mac = hmac.new(webhook_secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_mac, signature_header)

def normalize_open_banking_transactions(webhook_data: Dict[str, Any]) -> Tuple[List[ExpenseItem], int]:
    """
    Normalizes bank payload transactions into internal ExpenseItem models.
    Filters out pending transactions and deduplicates posted entries.
    """
    raw_txs = webhook_data.get("transactions", [])
    seen_ids = set()
    normalized_items: List[ExpenseItem] = []
    ignored_pending_count = 0

    category_mapping = {
        "Food and Drink": "Dining & Groceries",
        "Travel": "Transit & Travel",
        "Payment": "Transfers & Debt",
        "Shops": "Shopping",
        "Recreation": "Entertainment",
        "Service": "Bills & Services",
    }

    for tx in raw_txs:
        # Ignore unposted transactions to prevent double counting
        if tx.get("pending", False):
            ignored_pending_count += 1
            continue

        tx_id = tx.get("transaction_id")
        if tx_id in seen_ids:
            continue
        seen_ids.add(tx_id)

        amount = float(tx.get("amount", 0.0))
        # Plaid convention: positive amount indicates money spent by the user
        if amount <= 0:
            continue

        merchant = tx.get("merchant_name") or tx.get("name") or "Unspecified Merchant"
        raw_categories = tx.get("category", ["Miscellaneous"])
        primary_cat = raw_categories[0] if raw_categories else "Miscellaneous"
        mapped_cat = category_mapping.get(primary_cat, primary_cat)

        # Classify necessity
        is_essential = mapped_cat in ["Housing", "Dining & Groceries", "Bills & Services", "Utilities"]

        normalized_items.append(
            ExpenseItem(
                category=mapped_cat,
                description=merchant,
                amount=amount,
                is_essential=is_essential
            )
        )

    return normalized_items, ignored_pending_count
