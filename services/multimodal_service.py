"""
Multimodal Document & Receipt OCR Ingestion Service for PocketSmart AI.
Leverages Google Gemini 3.7 Pro via the official google-genai SDK to extract
itemized transactions from images (PNG, JPG, WEBP) and PDF bank statements
into standard ExpenseItem models with token cost optimization and validation.
"""
import io
import mimetypes
from typing import List, Tuple, Optional
from PIL import Image
import pypdf
from google import genai
from google.genai import types

from schemas import (
    ExpenseItem,
    MultimodalOCRDocumentReport,
    ExtractedDocumentExpense,
)
from services.gemini_service import get_gemini_client

# Constraints for token optimization and cost control
MAX_IMAGE_DIMENSION = 1600  # Max width/height to avoid excessive vision tokens
MAX_PDF_PAGES = 3           # Max PDF statement pages to process in a single upload
SUPPORTED_MIME_TYPES = {
    "image/jpeg": "image/jpeg",
    "image/jpg": "image/jpeg",
    "image/png": "image/png",
    "image/webp": "image/webp",
    "application/pdf": "application/pdf",
}

MULTIMODAL_OCR_SYSTEM_PROMPT = """
You are PocketSmart Vision OCR, an elite financial document parser and OCR specialist.
Your task is to analyze receipt images, store receipts, invoices, or PDF bank statements and extract all individual expense transactions with high precision.

Rules:
1. Identify all debit/expense transactions or itemized receipt line items.
2. Normalize merchant names and descriptions (clean up OCR noise).
3. Standardize categories into canonical buckets: 'Housing', 'Groceries', 'Utilities', 'Food & Dining', 'Transportation', 'Shopping', 'Entertainment', 'Health', 'Personal Care', 'Debt & Bills', 'Other'.
4. Convert dates to YYYY-MM-DD if present on the document; otherwise return null.
5. If the document is a receipt with line items and a final Total, extract the individual line items if clearly legible, or extract the final receipt Total with the merchant name.
6. Note any OCR ambiguities, blurriness, or multi-currency conversions in 'unreadable_warning'.
7. Always return output strictly structured according to the MultimodalOCRDocumentReport schema.
"""


def optimize_image_bytes(image_bytes: bytes, mime_type: str) -> Tuple[bytes, str]:
    """
    Optimizes and downsamples images exceeding MAX_IMAGE_DIMENSION to reduce vision token costs.
    """
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Convert RGBA to RGB for JPEG optimization
            if img.mode in ("RGBA", "P") and mime_type in ("image/jpeg", "image/jpg"):
                img = img.convert("RGB")
            
            width, height = img.size
            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)
                
            out_buffer = io.BytesIO()
            format_name = "PNG" if "png" in mime_type else "JPEG"
            img.save(out_buffer, format=format_name, quality=85, optimize=True)
            return out_buffer.getvalue(), "image/png" if "png" in mime_type else "image/jpeg"
    except Exception:
        # Fallback to original bytes if PIL processing encounters an unexpected format
        return image_bytes, mime_type


def validate_pdf_pages(pdf_bytes: bytes) -> bytes:
    """
    Validates PDF statements and enforces a MAX_PDF_PAGES limit to prevent token overflows.
    """
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        if len(reader.pages) == 0:
            raise ValueError("The uploaded PDF file has no pages.")
        
        if len(reader.pages) > MAX_PDF_PAGES:
            writer = pypdf.PdfWriter()
            for i in range(MAX_PDF_PAGES):
                writer.add_page(reader.pages[i])
            truncated_stream = io.BytesIO()
            writer.write(truncated_stream)
            return truncated_stream.getvalue()
        return pdf_bytes
    except Exception as e:
        if "The uploaded PDF" in str(e):
            raise
        return pdf_bytes


def extract_expenses_from_document(
    file_bytes: bytes,
    file_name: str,
    mime_type: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Tuple[List[ExpenseItem], MultimodalOCRDocumentReport]:
    """
    Performs multimodal OCR on an uploaded receipt image or PDF bank statement
    using Gemini 3.7 Pro via the official google-genai SDK.
    
    Returns:
        Tuple of (List[ExpenseItem] normalized for baseline engine, MultimodalOCRDocumentReport)
    """
    # Detect & Validate MIME Type
    if not mime_type:
        guessed_type, _ = mimetypes.guess_type(file_name)
        mime_type = guessed_type or "application/octet-stream"
    
    clean_mime = mime_type.lower()
    if clean_mime not in SUPPORTED_MIME_TYPES:
        if file_name.lower().endswith((".jpg", ".jpeg")):
            clean_mime = "image/jpeg"
        elif file_name.lower().endswith(".png"):
            clean_mime = "image/png"
        elif file_name.lower().endswith(".webp"):
            clean_mime = "image/webp"
        elif file_name.lower().endswith(".pdf"):
            clean_mime = "application/pdf"
        else:
            raise ValueError(
                f"Unsupported document format '{mime_type}'. Supported formats: PNG, JPG, JPEG, WEBP, PDF."
            )

    # Pre-process & Optimize payload
    if clean_mime == "application/pdf":
        processed_bytes = validate_pdf_pages(file_bytes)
    else:
        processed_bytes, clean_mime = optimize_image_bytes(file_bytes, clean_mime)

    # Initialize Gemini client
    client = get_gemini_client(api_key=api_key)

    # Create inline media Part using official google-genai SDK types
    media_part = types.Part.from_bytes(
        data=processed_bytes,
        mime_type=clean_mime,
    )

    user_prompt = f"Please perform an intelligent OCR and financial expense extraction from this document ({file_name})."

    try:
        response = client.models.generate_content(
            model="gemini-3.7-pro",
            contents=[media_part, user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=MULTIMODAL_OCR_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=MultimodalOCRDocumentReport,
                temperature=0.1,
            ),
        )

        # Parse structured report
        if hasattr(response, "parsed") and response.parsed is not None:
            if isinstance(response.parsed, MultimodalOCRDocumentReport):
                report = response.parsed
            elif isinstance(response.parsed, dict):
                report = MultimodalOCRDocumentReport.model_validate(response.parsed)
            else:
                report = MultimodalOCRDocumentReport.model_validate_json(response.text)
        else:
            report = MultimodalOCRDocumentReport.model_validate_json(response.text)

        # Convert ExtractedDocumentExpense to standard ExpenseItem objects for baseline engine
        normalized_expenses: List[ExpenseItem] = []
        for doc_item in report.extracted_expenses:
            if doc_item.amount > 0:
                normalized_expenses.append(
                    ExpenseItem(
                        date=doc_item.date,
                        category=doc_item.category.strip().title() if doc_item.category else "Other",
                        description=f"{doc_item.merchant_or_description} ({report.institution_or_vendor or 'Receipt'})".strip(),
                        amount=round(float(doc_item.amount), 2),
                    )
                )

        return normalized_expenses, report

    except Exception as e:
        raise RuntimeError(f"Gemini 3.7 Pro Multimodal OCR Extraction failed: {str(e)}")
