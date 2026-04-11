# 🛡️ InsureTrust AI

**Real-time Fraudulent Insurance Claim Detection Platform**

> FinTech Hackathon Demo — AI-powered multi-model ensemble for detecting individual fraud, organized rings, and IRDAI Red Flag violations.

![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20Next.js%20%7C%20D3.js%20%7C%20NetworkX-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/insure-trust-ai.git
cd insure-trust-ai

# 2. Set up environment
cp .env.example .env
# Add your Groq API key (free from https://console.groq.com)

# 3. Launch with Docker
docker-compose up --build

# 4. Open in browser
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs

# 5. Upload demo_ring_fraud.json to see fraud ring animate! 🎯
```

## 🎯 Demo Flow

1. Open `http://localhost:3000`
2. Upload `backend/data/demo_claims/demo_ring_fraud.json` as the Claim Form
3. Watch the 7-step streaming pipeline process in real-time
4. See the fraud ring graph animate with pulsing red nodes
5. Review the risk score gauge (should score 85–95)
6. Check SHAP values, RFI violations, and AI summary
7. Use adjuster panel to approve/escalate/reject

### Demo Files

| File | Expected Score | Routing |
|------|---------------|---------|
| `demo_legit.json` | 15–30 | AUTO_APPROVED ✅ |
| `demo_individual_fraud.json` | 62–75 | HIGH_RISK_REVIEW ⚠ |
| `demo_ring_fraud.json` | 85–95 | AUTO_ESCALATED 🚨 |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Next.js 14 Frontend                 │
│  ClaimUploader → StreamingProgress → RiskGauge      │
│  FraudRingGraph (D3.js) ← Most Important Component  │
│  ShapWaterfall | RFIBadges | AdjusterPanel          │
└─────────────────┬───────────────────────────────────┘
                  │ SSE + REST API
┌─────────────────┴───────────────────────────────────┐
│                FastAPI Backend (8000)                 │
│                                                      │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ Image   │ │ NLP      │ │ Tabular  │ │ GNN     │ │
│  │ Stub    │ │ Stub     │ │ Stub     │ │ Stub    │ │
│  └────┬────┘ └────┬─────┘ └────┬─────┘ └────┬────┘ │
│       └───────────┼────────────┼─────────────┘      │
│              ┌────┴────────────┴────┐               │
│              │  Ensemble Fusion     │               │
│              │  weighted_sum × 100  │               │
│              │  + RFI points        │               │
│              └──────────┬───────────┘               │
│                         │                            │
│  ┌──────────┐  ┌───────┴──────┐  ┌───────────────┐ │
│  │ RFI      │  │ Graph Engine │  │ Audit Logger  │ │
│  │ Engine   │  │ (NetworkX)   │  │ (SQLite)      │ │
│  │ 10 Rules │  │ Ring Detect  │  │ Append-only   │ │
│  └──────────┘  └──────────────┘  └───────────────┘ │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ Groq LLM (async, non-blocking)               │   │
│  │ llama-3.1-8b-instant — summaries only        │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Database | SQLite (SQLAlchemy ORM) |
| Graph Engine | NetworkX (in-memory, Neo4j-compatible schema) |
| LLM | Groq SDK (free tier, llama-3.1-8b-instant) |
| Reports | ReportLab (PDF generation) |
| Frontend | Next.js 14, Tailwind CSS, D3.js v7 |
| Deploy | Docker Compose |

## 📦 Model Stubs

The ML models are developed separately. This project uses **stub functions** that return realistic mock data. When real models are ready, replace the functions in `backend/services/model_stubs.py`:

- `get_image_score()` → EfficientNet-B4 deepfake classifier
- `get_nlp_score()` → Sentence-transformers contradiction detector
- `get_tabular_score()` → XGBoost classifier
- `get_gnn_score()` → PyTorch Geometric GCN

## 🔍 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/claims/submit` | Submit claim (SSE streaming) |
| GET | `/claims/{id}` | Get claim details |
| GET | `/claims/{id}/summary` | Get LLM summary |
| PATCH | `/claims/{id}/decision` | Record adjuster decision |
| GET | `/claims/` | List all claims |
| GET | `/graph/data` | Full graph for D3.js |
| GET | `/dashboard/stats` | Dashboard statistics |
| GET | `/reports/{id}/pdf` | Download PDF report |
| GET | `/audit/{id}` | Audit trail |

## 🔐 Privacy

- Aadhaar & mobile numbers → SHA-256 hashed before storage
- Only last 4 digits displayed: `AADHAAR: ****-****-4521`
- No raw PII in logs, console, or API responses

## 📊 Scoring Formula

```
base_score = (image × 0.30 + nlp × 0.25 + tabular × 0.25 + graph × 0.20) × 100
final_score = min(100, base_score + total_rfi_points)

Routing:
  0–30:   AUTO_APPROVED     (green)
  31–60:  MANUAL_REVIEW     (yellow)
  61–79:  HIGH_RISK_REVIEW  (orange)
  80–100: AUTO_ESCALATED    (red)
```

## 🏃 Local Development (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

---

**Built for FinTech Hackathon 2025** | IRDAI Anti-Fraud Policy 2025 Compliant
