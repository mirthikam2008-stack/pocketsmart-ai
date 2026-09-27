# PocketSmart AI: Production Deployment Guide & Submission Dossier

Complete production delivery blueprint for **PocketSmart AI: Your Smart Budget & Recommendation Assistant**.

---

## 1. Git Repository Setup, Branching & Release Strategy

### Step 1: Initialize Git Repository & Verify Ignore Policies
Run these commands in PowerShell in the project root:

```powershell
# Initialize git repository
git init

# Verify that sensitive files (.env, secrets, venv) are excluded
git status --ignored
```

### Step 2: Configure Main Branch and Stage Verified Files
```powershell
# Stage all production files
git add .

# Initial commit
git commit -m "feat(core): initial production release of PocketSmart AI engine, UI, and test suite"

# Set primary branch
git branch -M main
```

### Step 3: Create Semantic Release Tag
```powershell
# Tag version 1.0.0
git tag -a v1.0.0 -m "Release v1.0.0: Production-grade PocketSmart AI with Gemini 3.7 Pro SDK integration"
```

### Step 4: Link Remote Repository & Push (GitHub)
```powershell
# Add your GitHub remote origin
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/pocketsmart-ai.git

# Push main branch and release tags
git push -u origin main
git push origin --tags
```

---

## 2. Production Deployment: Streamlit Community Cloud

Streamlit Community Cloud provides instant, managed hosting directly from GitHub.

### Step-by-Step Deployment:
1. Navigate to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
2. Click **"New app"**.
3. Select your repository: `YOUR_GITHUB_USERNAME/pocketsmart-ai`.
4. Set **Branch**: `main`.
5. Set **Main file path**: `app.py`.
6. Click **"Advanced settings..."**:
   - Set **Python version**: `3.11`
   - In the **Secrets** text box, add:
     ```toml
     GEMINI_API_KEY = "AIzaSyYourActualGoogleGeminiApiKeyHere"
     ```
7. Click **"Deploy!"**.
8. **Live Verification**: Streamlit will provision the container, install dependencies from `requirements.txt`, and assign a URL: `https://YOUR_APP_NAME.streamlit.app`.

---

## 3. Production Deployment: Google Cloud Run (Containerized)

Google Cloud Run provides serverless, autoscaling container execution with custom domain and secret manager support.

### Step 1: Install & Authenticate Google Cloud CLI
```powershell
# Authenticate gcloud
gcloud auth login

# Set your active GCP project
gcloud config set project YOUR_GCP_PROJECT_ID

# Enable required Google Cloud APIs
gcloud services enable run.googleapis.com \
                       artifactregistry.googleapis.com \
                       cloudbuild.googleapis.com \
                       secretmanager.googleapis.com
```

### Step 2: Provision Secret in Google Secret Manager (Recommended)
```powershell
# Create the secret definition
gcloud secrets create GEMINI_API_KEY --replication-policy="automatic"

# Add your Gemini API key payload
Write-Output -NoEnumerate "AIzaSyYourActualGoogleGeminiApiKeyHere" | gcloud secrets versions add GEMINI_API_KEY --data-file=-
```

### Step 3: Build & Submit Container Image via Cloud Build
```powershell
# Submit Dockerfile build to Google Container Registry / Artifact Registry
gcloud builds submit --tag gcr.io/YOUR_GCP_PROJECT_ID/pocketsmart-ai:v1.0.0 .
```

### Step 4: Deploy Container to Google Cloud Run
```powershell
gcloud run deploy pocketsmart-ai `
    --image gcr.io/YOUR_GCP_PROJECT_ID/pocketsmart-ai:v1.0.0 `
    --platform managed `
    --region us-central1 `
    --allow-unauthenticated `
    --memory 1Gi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 5 `
    --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest `
    --port 8080
```
Upon successful deployment, Google Cloud Run returns the secure production endpoint: `https://pocketsmart-ai-xxxxxxxx-uc.a.run.app`.

---

## 4. Post-Deployment Smoke Test & Verification Procedure

Follow this 4-step smoke test on the live production endpoint:

| Step | Action | Expected Output | Pass/Fail |
| :--- | :--- | :--- | :--- |
| **1. Endpoint Health** | Open `https://YOUR_DEPLOYED_URL` in browser. | Web app loads with title *"PocketSmart AI: Financial Command Center"*, dark modern FinTech theme, and 4 KPI cards. | [ ] |
| **2. CSV Ingestion** | Upload `sample_transactions.csv` in the sidebar. | Success alert: *"Loaded 15 transactions successfully!"*; KPI cards and Plotly charts update dynamically. | [ ] |
| **3. Deterministic 50/30/20** | Check the **50/30/20 Benchmark** chart under Tab 1. | Needs, Wants, and Savings bars match exact arithmetic allocations. | [ ] |
| **4. Live Gemini 3.7 Pro Audit** | Navigate to Tab 2 and click **"🚀 Run AI Financial Diagnostics"**. | Spinner runs and renders: Financial Health Score (0-100), Executive Summary, Budget Leaks, Anomalies, and Prioritized Recommendations. | [ ] |

---

## 5. Final Project Presentation & Submission Template

Use this template for final submission to stakeholders or hackathon/project portals:

```markdown
# 💳 PocketSmart AI: Your Smart Budget & Recommendation Assistant

## 🔗 Live Application & Assets
- 🌐 **Live Web Application (Streamlit Cloud):** https://YOUR_APP_NAME.streamlit.app
- ☁️ **Live Web Application (Google Cloud Run):** https://pocketsmart-ai-xxxxxxxx-uc.a.run.app
- 📂 **GitHub Repository:** https://github.com/YOUR_GITHUB_USERNAME/pocketsmart-ai
- 🎥 **Video Walkthrough Demo:** https://youtu.be/YOUR_DEMO_VIDEO_LINK

---

## 💡 Executive Summary & Solution
PocketSmart AI transforms personal budgeting from reactive expense tracking into an automated, proactive financial intelligence engine. It combines deterministic cash-flow mathematics (50/30/20 framework, savings gap formulas) with Google Gemini 3.7 Pro using the official `google-genai` Python SDK to detect subtle micro-spend leakage, highlight spending anomalies, and generate realistic, dollar-quantified recommendations to hit savings targets.

---

## 🏗️ Architecture & Technology Stack
- **Frontend / Dashboard:** Streamlit, Custom FinTech CSS tokens, Plotly Interactive Visualizations.
- **Computation Engine:** Deterministic Python Budget Engine (zero hallucinations for arithmetic).
- **Generative AI Core:** Google Gemini 3.7 Pro (`gemini-3.7-pro`) via official `google-genai` SDK.
- **Data Validation & Schemas:** Pydantic v2 structured JSON schema validation (`response_schema=AIAnalysisReport`).
- **Containerization & Cloud:** Docker, Google Cloud Run, Streamlit Community Cloud, Google Secret Manager.

---

## ✨ Key Differentiators
1. **Hybrid Deterministic + GenAI Architecture:** Math and accounting metrics are deterministically computed; GenAI handles contextual reasoning, behavioral advice, and leak pattern extraction.
2. **Strict Schema Enforcement:** 100% structured JSON output guarantees zero parsing failures in UI rendering.
3. **Enterprise Security:** Zero hardcoded credentials; protected by Google Secret Manager and Streamlit Secrets.
```
