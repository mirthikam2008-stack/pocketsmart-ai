# PocketSmart AI: Final Project Submission & Operational Dossier
**Track:** Generative AI with Google  
**Core Model:** Google Gemini 3.7 Pro (`gemini-3.7-pro`)  
**Deployment Profile:** Cloud-Native Containerized Application (Google Cloud Run / Streamlit Community Cloud)

---

## 1. Executive Summary
PocketSmart AI resolves arithmetic hallucinations common in generic LLM finance tools by deploying a decoupled architecture:
1. **Deterministic Accounting Engine:** Pure Python/Pandas calculating 50/30/20 metrics, cashflows, and debt curves with 100% precision.
2. **Generative Reasoning Engine:** Google Gemini 3.7 Pro operating under strict Pydantic JSON schema constraints to perform qualitative leak detection, prioritized financial trade-offs, and multi-turn contextual advisory.

---

## 2. Verified Feature Implementation Matrix
| Feature Requirement | Technical Engine | Validation Asset |
| :--- | :--- | :--- |
| **Deterministic 50/30/20 Rule** | `services/budget_engine.py` | `test_pipeline.py::test_02` |
| **Pydantic Structured Diagnostics** | `services/gemini_service.py` | `schemas.py::AIAnalysisReport` |
| **Multimodal Statement OCR** | `services/multimodal_service.py` | `test_pipeline.py::test_05` |
| **Streaming Contextual Chat** | `services/chat_service.py` | `test_pipeline.py::test_06` |
| **Autonomous Multi-Scenario Rebalancer**| `services/rebalancer_engine.py` | `test_pipeline.py::test_07` |
| **PII Redaction & Tamper-Sealed Export** | `services/privacy_service.py`, `export_service.py` | `test_pipeline.py::test_08` |
| **Telemetry, Cost & Latency Tracking** | `services/telemetry_service.py` | `SessionTelemetry` |

---

## 3. Video Demonstration Storyboard (2:30 Target)
* **0:00 - 0:30 (Problem Statement & Ingestion):** Showcase dark FinTech dashboard; upload `sample_transactions.csv` and show instant sub-second KPI population.
* **0:30 - 1:00 (Multimodal Vision):** Upload a sample receipt/bill image; show dynamic OCR extraction directly appending to ledger rows.
* **1:00 - 1:40 (Gemini 3.7 Pro Diagnostics):** Trigger AI optimization; inspect Financial Health Score, identified micro-leaks, and structured action items.
* **1:40 - 2:10 (Autonomous Planner & Streaming Copilot):** Adjust milestone sliders; show multi-scenario lines; ask a grounding question in the chatcopilot.
* **2:10 - 2:30 (Compliance & Export):** Toggle High Privacy mode (showing PII redaction); download the cryptographic audit JSON and stylized PDF health report.

---

## 4. Viva / Evaluation Defense Highlights
* **Q: Why decouple deterministic arithmetic from Gemini 3.7 Pro?**  
  *A:* LLMs are probabilistic language models prone to calculation errors. PocketSmart AI computes all balances, percentages, and amortization curves deterministically in Python, feeding verified ground truth into Gemini 3.7 Pro solely for qualitative synthesis.
* **Q: How are parsing errors prevented across UI updates?**  
  *A:* Using the official `google-genai` SDK's native `response_schema` parameter backed by Pydantic v2 models, forcing valid JSON serialization directly at the model generation level.
* **Q: How does the system handle API rate limits in production?**  
  *A:* Integrated exponential backoff retry middleware with full-state circuit breaking and fallback deterministic heuristics inside `services/resilience_service.py`.
