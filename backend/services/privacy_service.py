"""
Financial Privacy, PII Sanitizer & Zero-Data-Leakage Guardrail Module.
Scrubs Personally Identifiable Information (PII) including Social Security Numbers,
credit card numbers, IBAN/bank account numbers, email addresses, phone numbers,
and physical addresses before prompts are dispatched to LLM providers.
"""
import re
from typing import List, Tuple
from schemas import ExpenseItem, UserFinancialProfile

# Compiled Regex patterns for deterministic PII detection
SSN_REGEX = re.compile(r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b|\b\d{15,16}\b")
IBAN_REGEX = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
STREET_ADDRESS_REGEX = re.compile(
    r"\b\d{1,5}\s+(?:[A-Za-z0-9.-]+\s+){1,4}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Terrace|Ter|Place|Pl|Square|Sq|Trail|Trl)\b",
    re.IGNORECASE,
)
ACCOUNT_NUM_REGEX = re.compile(r"\b(?:Account|Acct|ACC|ACT)[\s#:]*([0-9A-Z]{6,16})\b", re.IGNORECASE)



def sanitize_text_string(text: str) -> Tuple[str, int]:
    """
    Sanitizes raw text strings by masking all identifiable PII tokens.
    Returns Tuple of (sanitized_text, count_of_redactions).
    """
    if not text:
        return text, 0

    redaction_count = 0
    sanitized = text

    # 1. Mask Social Security Numbers / Tax IDs
    matches = SSN_REGEX.findall(sanitized)
    if matches:
        redaction_count += len(matches)
        sanitized = SSN_REGEX.sub("[REDACTED_SSN]", sanitized)

    # 2. Mask Credit / Debit Card Numbers (Retaining last 4 digits)
    def mask_cc(match):
        raw_cc = re.sub(r"[-\s]", "", match.group(0))
        last_four = raw_cc[-4:] if len(raw_cc) >= 4 else "XXXX"
        return f"****-****-****-{last_four}"

    cards = CREDIT_CARD_REGEX.findall(sanitized)
    if cards:
        redaction_count += len(cards)
        sanitized = CREDIT_CARD_REGEX.sub(mask_cc, sanitized)

    # 3. Mask IBAN / Bank Accounts
    ibans = IBAN_REGEX.findall(sanitized)
    if ibans:
        redaction_count += len(ibans)
        sanitized = IBAN_REGEX.sub("[REDACTED_IBAN]", sanitized)

    # 4. Mask Explicit Account Numbers
    accts = ACCOUNT_NUM_REGEX.findall(sanitized)
    if accts:
        redaction_count += len(accts)
        sanitized = ACCOUNT_NUM_REGEX.sub(r"Account: ****-****", sanitized)

    # 5. Mask Emails
    emails = EMAIL_REGEX.findall(sanitized)
    if emails:
        redaction_count += len(emails)
        sanitized = EMAIL_REGEX.sub("[REDACTED_EMAIL]", sanitized)

    # 6. Mask Phone Numbers
    phones = PHONE_REGEX.findall(sanitized)
    if phones:
        redaction_count += len(phones)
        sanitized = PHONE_REGEX.sub("[REDACTED_PHONE]", sanitized)

    # 7. Mask Physical Street Addresses
    addresses = STREET_ADDRESS_REGEX.findall(sanitized)
    if addresses:
        redaction_count += len(addresses)
        sanitized = STREET_ADDRESS_REGEX.sub("[REDACTED_ADDRESS]", sanitized)

    return sanitized, redaction_count


def sanitize_financial_profile(profile: UserFinancialProfile) -> Tuple[UserFinancialProfile, int]:
    """
    Produces an anonymized copy of the user's financial profile with all
    merchant names and transaction descriptions stripped of PII.
    """
    total_redactions = 0
    sanitized_expenses: List[ExpenseItem] = []

    for item in profile.expenses:
        clean_desc, red_count = sanitize_text_string(item.description)
        clean_cat, cat_red = sanitize_text_string(item.category)
        total_redactions += (red_count + cat_red)

        sanitized_expenses.append(
            ExpenseItem(
                date=item.date,
                category=clean_cat,
                description=clean_desc,
                amount=item.amount,
            )
        )

    sanitized_profile = UserFinancialProfile(
        monthly_income=profile.monthly_income,
        savings_target=profile.savings_target,
        expenses=sanitized_expenses,
    )

    return sanitized_profile, total_redactions


# Backward compatibility aliases
sanitize_financial_text = sanitize_text_string
sanitize_user_profile = sanitize_financial_profile
