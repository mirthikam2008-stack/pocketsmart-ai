# PocketSmart AI: Final Project Presentation, Video Script & Technical Defense Package

---

## 1. Executive Project Summary Dossier

### 1.1 Problem Statement
Modern personal financial management applications are largely **reactive and fragmented**. Traditional budget trackers present backward-looking charts without actionable guidance, while users struggle with hidden recurring micro-spend leaks, lifestyle creep, and unrealistic savings targets. Manual spreadsheet tracking is error-prone and lacks personalized, contextual advisory capabilities.

### 1.2 Solution Overview: PocketSmart AI
**PocketSmart AI** is an intelligent, dual-engine FinTech web application that transforms personal cash-flow management. By combining deterministic mathematical calculations with Google's state-of-the-art **Gemini 3.7 Pro** model via the official `google-genai` Python SDK, PocketSmart AI delivers:
- **Instant Ingestion**: Support for itemized expense inputs and bulk CSV statements with automatic header normalization.
- **Deterministic Baseline Analytics**: Zero-hallucination computation of total spend, savings gap, savings rates, and 50/30/20 standard budget benchmark adherence.
- **Deep Generative AI Audit**: Structured analysis generating an objective Financial Health Score (0–100), automated micro-leak detection with dollar impact quantification, transaction outlier anomaly detection, and prioritized, achievable recommendations.

### 1.3 Architecture: Division of Labor (Deterministic vs. Generative AI)

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                           PocketSmart AI UI                             │
│                      (Streamlit + Custom CSS)                           │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
   ┌───────────────────────────┐           ┌───────────────────────────┐
   │ Deterministic Math Engine │           │   Google Gemini 3.7 Pro   │
   │   (services/budget_engine)│           │ (services/gemini_service) │
   ├───────────────────────────┤           ├───────────────────────────┤
   │ • Total Spend & Savings   │           │ • Financial Health Score  │
   │ • Savings Target Gap      │           │ • Recurring Leak Detection│
   │ • 50/30/20 Calculations   │           │ • Spending Anomalies      │
   │ • CSV Normalization       │           │ • Actionable Advice Plans │
   └─────────────┬─────────────┘           └─────────────┬─────────────┘
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     ▼
                      ┌─────────────────────────────┐
                      │ Pydantic v2 Schema Pipeline │
                      │   (Strict JSON Validation)  │
                      └─────────────────────────────┘
```

| Component | Responsibility | Rationale |
| :--- | :--- | :--- |
| **Deterministic Engine** (`budget_engine.py`) | Accounting sums, 50/30/20 breakdown, percentage calculations, savings gaps. | Elimination of LLM arithmetic hallucinations; 100% deterministic accuracy. |
| **Generative AI Core** (`gemini_service.py`) | Behavioral audit, leak extraction, outlier detection, goal feasibility analysis. | Deep contextual reasoning, semantic pattern recognition, tailored financial planning. |
| **Pydantic Validation** (`schemas.py`) | Strict type enforcement on inputs and LLM JSON outputs. | Guaranteed UI stability and zero schema/deserialization crashes. |

### 1.4 Technology Stack
- **Frontend / Visualizations**: Python 3.11, Streamlit, Plotly Express & Graph Objects.
- **AI / LLM Infrastructure**: Google Gemini 3.7 Pro (`gemini-3.7-pro`), official `google-genai` Python SDK, Pydantic v2.
- **Deployment & Security**: Docker, Google Cloud Run, Streamlit Community Cloud, Google Secret Manager.

---

## 2. Video Demonstration Script (2–3 Minutes)

**Target Duration**: 2 minutes 30 seconds  
**Visual Style**: Screen recording of browser window with clear voiceover.

### Scene 1: Introduction & Architecture (0:00 – 0:35)
* **[Screen]**: Home screen of PocketSmart AI showing dark FinTech UI and KPI metric cards.
* **[Narration]**:  
  *"Welcome to PocketSmart AI: Your Smart Budget & Recommendation Assistant. Traditional budgeting apps show you historical charts but fail to tell you how to actually fix your cash leaks. PocketSmart AI changes that by pairing deterministic financial mathematics with the reasoning power of Google Gemini 3.7 Pro via the official google-genai SDK. Let’s explore how it works in real-time."*

### Scene 2: Data Ingestion & Deterministic Analytics (0:35 – 1:10)
* **[Screen]**: In the sidebar, set Monthly Income to `$5,000` and Savings Target to `$1,200`. Drag and drop `sample_transactions.csv` into the uploader.
* **[Narration]**:  
  *"In the sidebar, we set a monthly net income of $5,000 and a savings target of $1,200. We can add line items manually or upload a bank CSV. As soon as the CSV is uploaded, our deterministic engine normalizes transaction columns and computes baseline KPIs: total spend, actual residual savings, and savings gap. Under Tab 1, we immediately see interactive Plotly donut charts for category distribution and a grouped bar chart comparing actual spending against the standard 50% Needs, 30% Wants, and 20% Savings benchmark. Because all accounting is handled in pure Python, there is zero risk of LLM arithmetic errors."*

### Scene 3: Running Gemini 3.7 Pro AI Financial Diagnostics (1:10 – 2:00)
* **[Screen]**: Switch to Tab 2 (*"Gemini 3.7 Pro AI Analysis"*). Click *"🚀 Run AI Financial Diagnostics"*.
* **[Narration]**:  
  *"Now let's activate Gemini 3.7 Pro. When we click 'Run AI Financial Diagnostics', the application injects the verified financial metrics and itemized transactions into Gemini 3.7 Pro using strict Pydantic JSON schema validation.*
  *(Pause as results render)*  
  *Look at the output: Gemini assigns an objective Financial Health Score of 78/100, provides an executive summary, and evaluates our savings feasibility. Notice the identified Budget Leaks: it automatically flags recurring micro-spends like daily artisan coffee and digital subscriptions, estimating monthly waste with dollar precision. It also highlights spending anomalies and delivers prioritized, ranked recommendations with concrete action plans and realistic monthly savings projections."*

### Scene 4: Edge Cases, Security & Conclusion (2:00 – 2:30)
* **[Screen]**: Show `edge_case_transactions.csv` handling or the clean terminal running `python test_pipeline.py --mode mock`.
* **[Narration]**:  
  *"Our codebase includes an automated test pipeline with 100% assertion pass rates on edge cases like deficit spending and micro-transactions. With full containerization via Docker and zero hardcoded credentials, PocketSmart AI is production-ready for deployment on Google Cloud Run and Streamlit Community Cloud. Thank you!"*

---

## 3. Viva / Technical Defense Q&A

### Q1: Why use `gemini-3.7-pro` instead of smaller models or generic LLMs?
**Answer**:  
`gemini-3.7-pro` provides superior multi-step reasoning, mathematical discipline, and strict JSON schema adherence. In financial advisory tasks, the model must simultaneously correlate individual transaction frequencies against category ceilings, evaluate behavioral trade-offs, and rank recommendations by ROI. Smaller models frequently violate complex nested schemas or generate generic advice without estimating realistic dollar savings.

### Q2: How does the application guarantee zero hallucinations in calculations?
**Answer**:  
We implemented a **strict architectural division of labor**. All numerical accounting—including total spend, actual savings, savings gaps, category aggregations, and 50/30/20 target thresholds—is computed deterministically in `services/budget_engine.py` using pure Python and Pandas. The Gemini model is provided pre-computed metrics and asked to perform qualitative reasoning, leak detection, and behavioral synthesis. It does not perform primary bookkeeping arithmetic.

### Q3: How is structured output enforced with the official `google-genai` SDK?
**Answer**:  
In `services/gemini_service.py`, we pass the Pydantic schema directly into the Gemini request configuration:
```python
config=types.GenerateContentConfig(
    system_instruction=SYSTEM_INSTRUCTION,
    response_mime_type="application/json",
    response_schema=AIAnalysisReport,
    temperature=0.2,
)
```
This forces the model engine to output tokens conforming to the JSON schema corresponding to the `AIAnalysisReport` Pydantic class. The SDK automatically parses the response into verified Python objects, preventing JSON decode exceptions and type mismatches.

### Q4: How does the application handle edge cases such as budget deficits (`Spend > Income`) or zero expenses?
**Answer**:  
Our baseline engine calculates negative residual savings and flags a positive savings gap. The prompt explicitly supplies actual savings and expense-to-income percentages (e.g., `120%`). When Gemini evaluates deficit profiles, its system prompt directs it to lower the Financial Health Score, classify discretionary purchases as severe anomalies, and generate aggressive expense triage recommendations rather than optimistic investment advice.

### Q5: What security guardrails are implemented for API keys and sensitive customer data?
**Answer**:  
1. **Zero Hardcoded Secrets**: Keys are never stored in source files; `.env` and `secrets.toml` are enforced in `.gitignore`.
2. **Hierarchical Key Resolution**: `get_gemini_client()` securely resolves credentials in order: runtime sidebar input, `st.secrets` on Streamlit Cloud, and Google Secret Manager/environment variables on Cloud Run.
3. **Data Privacy**: No transaction data is persisted to disk; all data remains in-memory within the user's isolated session state.

### Q6: How is token consumption and cost managed when users upload large CSVs?
**Answer**:  
1. In `services/budget_engine.py`, transactions are aggregated into category totals before prompt construction.
2. For itemized listings, descriptions and amounts are compressed into single-line markdown formats (`- [Date] Category: Description -> $Amount`), stripping redundant metadata columns.
3. Temperature is locked to `0.2` to minimize speculative token generation while maximizing deterministic schema compliance.

### Q7: What makes the Docker container production-ready for Google Cloud Run?
**Answer**:  
The `Dockerfile` is built on a lightweight `python:3.11-slim` base with:
- Minimal system dependencies (`curl` for health checks).
- Dynamic `$PORT` binding (`--server.port=${PORT:-8080}`).
- Disabled CORS and XSRF flags (`--server.enableCORS=false`, `--server.enableXsrfProtection=false`) to ensure stable WebSocket streaming over Cloud Run reverse proxies.
- A built-in container health check querying `http://localhost:${PORT}/_stcore/health`.

### Q8: How does the testing suite ensure reliability across environments?
**Answer**:  
`test_pipeline.py` provides two distinct execution modes:
- **Mock Mode**: Generates structured mock Pydantic reports to validate UI components, arithmetic engines, and edge cases in CI/CD environments without using API quota.
- **Live Mode**: Executes genuine API handshakes against `gemini-3.7-pro` using live environment credentials to confirm end-to-end cloud connectivity.

---

## 4. Final Submission Readiness Checklist

| Category | Verification Item | Status | Verified File / Location |
| :--- | :--- | :--- | :--- |
| **SDK & Model** | Official `google-genai` SDK used (`from google import genai`) | ✅ PASSED | `services/gemini_service.py` |
| **SDK & Model** | Target model set to `gemini-3.7-pro` | ✅ PASSED | `services/gemini_service.py` |
| **Structured Output** | Pydantic v2 schemas for all Gemini outputs | ✅ PASSED | `schemas.py` |
| **Structured Output** | `response_schema=AIAnalysisReport` & `response_mime_type="application/json"` | ✅ PASSED | `services/gemini_service.py` |
| **Calculations** | Deterministic calculations & 50/30/20 benchmark allocation | ✅ PASSED | `services/budget_engine.py` |
| **Data Ingestion** | CSV parsing with flexible column alias normalization | ✅ PASSED | `services/budget_engine.py` |
| **User Interface** | Streamlit UI with Plotly charts and FinTech CSS theme | ✅ PASSED | `app.py` |
| **Test Automation** | Test pipeline covering math, CSV, edge cases, schema | ✅ PASSED | `test_pipeline.py` |
| **Datasets** | Standard and edge-case transaction datasets provided | ✅ PASSED | `sample_transactions.csv`, `edge_case_transactions.csv` |
| **Deployment** | Production Dockerfile with dynamic `$PORT` & healthcheck | ✅ PASSED | `Dockerfile` |
| **Deployment** | Comprehensive guides for Streamlit Cloud & Cloud Run | ✅ PASSED | `DEPLOYMENT_GUIDE.md`, `DEPLOYMENT_CHECKLIST.md` |
| **Security** | Zero hardcoded keys and strict `.gitignore` rules | ✅ PASSED | `.gitignore`, `.env.example` |
