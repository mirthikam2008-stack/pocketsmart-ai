# PocketSmart AI: Pre-Deployment Readiness & Verification Checklist

This document details the complete pre-flight validation procedure before deploying PocketSmart AI to **Streamlit Community Cloud** or **Google Cloud Run**.

---

## 1. Automated Test Suite Execution

Run the automated verification suite locally before triggering deployment pipelines.

### A. Mocked Offline Dry-Run (Fast, zero API quota usage)
```powershell
python test_pipeline.py --mode mock
```
*Expected Output:* `OK` (All 4 test suites pass: CSV Ingestion, 50/30/20 Math, Edge Cases, Pydantic Schema).

### B. Live Gemini 3.7 Pro Validation (Live API verification)
```powershell
python test_pipeline.py --mode live
```
*Expected Output:* `OK` with successful connection to `gemini-3.7-pro` and verified schema adherence.

---

## 2. Pre-Deployment Verification Checklist

| Category | Item | Verification Method | Status |
| :--- | :--- | :--- | :--- |
| **Security** | No hardcoded API keys | Ripgrep search: `grep -r "AIzaSy" .` | [ ] Verified |
| **Security** | `.env` ignored in Git | Check `.gitignore` contains `.env` and `.venv` | [ ] Verified |
| **Environment** | `GEMINI_API_KEY` present | Check local `.env` or Streamlit Secrets / Cloud Run env vars | [ ] Verified |
| **Data Ingestion** | CSV parsing resilience | Tested standard + edge case datasets (`sample_transactions.csv`, `edge_case_transactions.csv`) | [ ] Verified |
| **Calculations** | 50/30/20 & Savings Gap | Deterministic pure Python engine tested with unit assertions | [ ] Verified |
| **Schema Integrity**| Pydantic `AIAnalysisReport` | All fields (`health_summary`, `budget_leaks`, `spending_anomalies`, `recommendations`, `savings_feasibility`) strictly validated | [ ] Verified |
| **Container** | Dockerfile builds cleanly | `docker build -t pocketsmart-ai .` | [ ] Verified |

---

## 3. Step-by-Step Troubleshooting Guide

### Issue 1: `ModuleNotFoundError: No module named '...'`
- **Cause:** Virtual environment not active or dependencies missing.
- **Remediation:**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

### Issue 2: `ValueError: Gemini API Key is missing`
- **Cause:** `GEMINI_API_KEY` is not defined in `.env` or was entered as a placeholder.
- **Remediation:**
  1. Open `.env`.
  2. Set `GEMINI_API_KEY=AIzaSy...` (your actual Gemini API key from Google AI Studio).
  3. Or pass it interactively into the sidebar in the Streamlit UI.

### Issue 3: `ValueError: CSV missing mandatory column(s): amount`
- **Cause:** Uploaded CSV does not have an identifiable amount column.
- **Remediation:** Ensure the CSV header contains `amount`, `cost`, `price`, `total`, or `spent`. The parser automatically normalizes these aliases.

### Issue 4: Docker Container Fails on Cloud Run
- **Cause:** Hardcoded port mismatch.
- **Remediation:** Ensure `server.port=8080` and `server.address=0.0.0.0` are specified in `Dockerfile` and `PORT` environment variable is accepted.
