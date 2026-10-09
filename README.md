# UrbanPulse AI — AI-Powered Urban Issue Intelligence and Early-Warning Platform

> **Hackathon Solution: Decision-Support Platform for Spatiotemporal Anomaly Detection in Municipal Datasets**  
> *"UrbanPulse AI transforms fragmented municipal complaint data into explainable, spatiotemporal intelligence, detecting unusual civic issue patterns and helping authorities prioritize targeted investigation before problems escalate."*

---

## 🎯 The Core Problem We Solve

City authorities receive civic complaints across diverse municipal service wings:
- **Waste accumulation & garbage collection**
- **Water supply disruption & contamination**
- **Road damage, potholes & collapse**
- **Drainage, sewage overflows & storm runoff**
- **Streetlight outages & public illumination**
- **Power supply & exposed live electrical wires**
- **Public infrastructure asset damage**
- **Illegal dumping of commercial debris**

While individual complaints may appear routine, a rapid or clustered increase in complaints within a particular area or category indicates an **emerging systemic issue**. Detecting these patterns early allows municipal teams to intervene before situations compound into catastrophic failures.

**UrbanPulse AI** is a decision-support platform that analyzes municipal complaint datasets across temporal and spatiotemporal dimensions to detect **statistically significant anomalies**, evaluate **cross-category cascades**, and triage incidents into **dual operational queues** for targeted field intervention.

---

## 🏛️ System Architecture

```
                             URBANPULSE AI PLATFORM ARCHITECTURE
                                   
  [ Ingestion Layer: Multi-Source Municipal Inputs ]
   ├── Municipal Citizen Complaint Feeds (English, Tamil, Hindi, Hinglish)
   ├── Municipal CSV / JSON Batch Exporter (with automatic column mapping & bounding-box audit)
   └── Optional Environmental Context (IMD 24h AWS Rainfall & NWP Telemetry)
                         │
                         ▼
  [ Backend Intelligence Engine (Python 3.14 / FastAPI / SQLAlchemy / NumPy) ]
   ├── Data Sanitization & Multilingual NLP Parser (Prompt-injection safe, landmark gazetteer grounding)
   ├── Temporal Anomaly Engine:
   │    ├── Robust MAD (Median Absolute Deviation) Modified Z-score calculation
   │    ├── Poisson Count Dispersion Testing (Exact p-values with FDR Benjamini-Hochberg correction)
   │    ├── Rate-of-Rise Change-Point Pattern Detection (One-Time Spike, Sustained Increase, New/Rare)
   │    └── Minimum-Volume Safeguard (Prevents false alarms on sparse single-incident cells)
   ├── Spatiotemporal Density Engine:
   │    ├── Spatial Density Clustering (DBSCAN + spatial radius pooling)
   │    └── Neighbourhood Count Smoothing
   ├── Cross-Category Engine:
   │    ├── Spatiotemporal Co-Occurrence Discovery (Multi-service breakdown cascades)
   │    └── Correlation vs. Causation Guardrail Formulator (Candidate hypotheses)
   ├── Duplicate Detection & Incident Linker (Spatial proximity + token-level semantic Jaccard)
   └── Dual Operational Response Queue Generator:
        ├── Queue A: Emerging Multi-Incident Patterns & Escalations (Systemic field investigation)
        └── Queue B: High-Severity Immediate Hazards (Urgent life-safety triage: open manholes, live wires)
                         │
                         ▼
  [ Resident Mobile Web App (React 19 / Supabase Auth: email + password, no OTP) ]
   ├── Photo reporter: pick a problem type, snap a photo, add a landmark → Gemini vision verifies the
   │   issue is real, files the municipal report, and returns plain-language status
   ├── "Your reports" (this resident's submissions) and "Nearby city reports"
   └── One-tap switch to the Control room (full toolkit is never hidden from operators)
                         │
                         ▼
  [ Command Center Web Application (React 19 / TypeScript / Vite / Tailwind CSS / Leaflet) ]
   ├── 1. Operational Command Center: Multi-category volume health, anomaly counts, weather context
   ├── 2. Spatiotemporal Map: Ward boundaries, spatial clusters, non-invented coordinate markers
   ├── 3. Temporal Anomaly Explorer: Interactive MAD Z-scores, Poisson p-values, change-point patterns
   ├── 4. Cross-Category Patterns: Inter-department cascade hypotheses & correlation guardrails
   ├── 5. Civic Grievances & CSV Batch Ingestion: Drag-and-drop CSV importer with audit rejection log
   ├── 6. Dual-Queue Decision Actions: State machine (Review → Acknowledge → Assign → Resolve) with audit trail
   └── 7. Model Evaluation & Data Quality: 5-Fold cross-validation metrics, confusion matrix, coverage audit
```

---

## 🔬 Statistical Detection Methodology

### 1. Robust Baseline Estimation (MAD)
Standard mean and standard deviation are susceptible to outlier pollution when historical complaint records contain previous crises. UrbanPulse AI calculates:
$$\text{MAD} = \text{median}(|x_i - \text{median}(X)|)$$
$$\text{Modified } Z\text{-Score} = \frac{0.6745 \times (x_t - \text{median}(X))}{\text{MAD}}$$
A baseline with $\text{MAD} = 0$ triggers special zero-baseline handling to detect rare or unprecedented issue emergence.

### 2. Poisson Count Dispersion Significance
Because complaint arrivals within fixed time windows follow discrete count distributions, count significance is tested via Poisson cumulative probability:
$$P(X \ge k) = 1 - \sum_{i=0}^{k-1} \frac{\lambda^i e^{-\lambda}}{i!}$$
Significance is categorized into rigorous tiers:
- **High Statistical Significance**: $p < 0.01$
- **Standard Statistical Significance**: $p < 0.05$
- **Elevated Heuristic Signal**: $p \ge 0.05$ with elevated MAD deviation

### 3. Change-Point & Pattern Classification
- `ONE_TIME_SPIKE`: Sudden sharp increase within a single 24h window that does not persist.
- `SUSTAINED_INCREASE`: Consecutive multi-day volume elevations exceeding baseline thresholds.
- `NEW_OR_RARE`: Grievance category with historically zero complaints experiencing sudden activity.
- `RECURRING_PERIODIC`: Cyclic weekly or bi-weekly reporting surges.

### 4. Cross-Category Co-Occurrence & Guardrails
Detects pairs of complaint categories (e.g., *Solid Waste* + *Stormwater Drainage*) that co-occur within a 450m spatial radius and a 48h temporal window. 
> **Scientific Integrity Guardrail**: Every cross-category discovery is flagged with an explicit notice emphasizing that co-occurrence indicates elevated compound stress for joint investigation, **not mechanical causality**.

---

## 🚦 Dual Operational Response Queues

UrbanPulse AI prevents operational paralysis by dividing action tasks into two queues:

1. **Queue A (Emerging Multi-Incident Patterns & Escalations)**
   - Focus: Proactive, systemic field investigation before issues escalate.
   - Triggers: Statistically validated temporal spikes, high-density spatial clusters, cross-category cascade hypotheses.
2. **Queue B (High-Severity Immediate Hazards)**
   - Focus: Urgent, immediate life-safety triage.
   - Triggers: Keyword-verified critical hazards (open manhole, live wire sparking, hospital route obstruction, trapped vehicle).
   - Target SLA: Immediate dispatch within 30 minutes.

---

## 🚀 Quickstart & Reproduction

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Node.js 18+ & npm

### 1. Run Backend
```bash
# From repository root
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run all 61 automated unit and integration tests
PYTHONPATH=.. pytest

# Start the FastAPI server
PYTHONPATH=.. uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Run Frontend
```bash
# In a new terminal window
cd frontend
npm install
npm run dev
```

Visit **http://localhost:5173** to access UrbanPulse.

Residents sign in with email and password (no verification). The default **Resident** view is a simple photo reporter. Switch to **Control room** for the full anomaly, pattern, queue, rainfall, and evaluation toolkit.

In the Supabase dashboard, turn **Authentication → Providers → Email → Confirm email** OFF so accounts can sign in immediately.

### 2a. Supabase live persistence

On startup the backend creates any missing tables/columns (additive only — it never drops or alters), then loads **reference geography** (pilot cities, the 15 Chennai administrative zones, the 9 complaint category configs, vulnerable assets, historical waterlogging, climate scenarios, data-source registry). Reference rows are required for the API and map to work and are re-created idempotently.

On top of that it loads the **synthetic Chennai demo dataset** (23 multilingual complaints, anomaly records, cross-category patterns, and the two seeded queues) so the control room is populated for a first demo. This is skipped automatically as soon as any non-demo record exists — a real citizen photo report, or a CSV import — so live data is never mixed with fixtures. To start from a clean, fixture-free database set:

```env
SEED_DEMO_DATA="false"
```

Every seeding step is idempotent and safe across restarts, and a seeding failure logs a warning instead of blocking startup.

To persist uploaded data in your Supabase project, create a root `.env` from `.env.example` and set:

```env
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_ANON_KEY="your-anon-key"
SUPABASE_DB_URL="postgresql+psycopg://postgres:[DATABASE_PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres"
DATA_MODE="LIVE"
```

You can use either `SUPABASE_DB_PASSWORD` (recommended) or the complete `SUPABASE_DB_URL`. Do not edit `.env.example`; copy it to `.env` first. The app loads `.env` from the project root and `backend/.env`. Use the database password from **Supabase → Project Settings → Database**, not the publishable/anon key. Install the new driver with `pip install -r backend/requirements.txt`, then fully restart the backend. `/api/health` reports whether persistence is `SUPABASE_POSTGRES` or `LOCAL_SQLITE`.

Both the **direct** (`db.<ref>.supabase.co`) and **transaction-pooler** (`aws-<region>.pooler.supabase.co`) hostnames work: the Postgres driver is configured to send statements unprepared, because Supavisor multiplexes server connections and otherwise breaks psycopg's prepared-statement cache.

The supplied Supabase URL and public keys should be placed in your local ignored `.env`; they are intentionally not committed to this project. Never put the database password or a Supabase service-role key in frontend code.

### 2b. Optional Gemini Copilot & photo verification

Two features use Gemini, both through `backend/app/engine/gemini_client.py`:

- **Citizen photo verification** (`POST /api/civic/photo-report`) — the uploaded photo is sent to Gemini vision, which returns a structured verdict: category, severity, confidence, visible cues, and `problem_confirmed`. A photo the model cannot confirm as a real civic issue is filed but held for review, and the resident is told so plainly rather than being shown a false success.
- **Monsoon Copilot** (`POST /api/ai/assistant`) — grounded in the dashboard's current evidence.

`gemini-3.8-flash` is the current general-access model id (older `gemini-2.5-flash` / `gemini-2.0-flash` ids now return `404` for new keys). The shared endpoint intermittently returns `503` under load and can exceed a single timeout, so calls retry with backoff inside a latency budget (45s vision, 30s copilot) before falling back. If Gemini is unavailable, the photo report still succeeds via the offline civic classifier and the response records `scan_source: "LOCAL_RULES"` with a `scan_fallback_reason`, so a degraded scan is never silent.

To enable Gemini responses, set `GEMINI_API_KEY` in the root `.env` (or `backend/.env`, never committed) and restart the backend. The key is used only by the backend; it is never sent to the browser. The map uses OpenStreetMap tiles and does not require a map API key for local demos.

### 2c. India-only map and weather providers

The map is constrained to India (`6.4–35.7°N`, `68.0–97.5°E`) and the pilot cities are Chennai, Bengaluru, and Bhubaneswar. Incoming complaint coordinates are validated against the same India bounds.

| Provider | Environment variable | What is needed | Use in this project |
| --- | --- | --- | --- |
| **IMD official API** | `IMD_API_KEY` | Register at the [IMD API portal](https://api.imd.gov.in/public/register.php), generate a development/production key, and configure the required JWT/server access described in the [IMD user guide](https://api.imd.gov.in/public/IMD_API_Portal_User_Guide.pdf). | Official warnings and India-specific observations. |
| **Open-Meteo** | `OPEN_METEO_API_KEY` | No key for normal, low-volume, non-commercial use. A commercial customer key/plan may be required for higher-volume use. | Forecast context and fallback weather data. |
| **ISRO Bhuvan** | `BHUVAN_NRSC_TOKEN` | Bhuvan/NRSC account and token if protected layers are enabled. | India geospatial/elevation layers. |
| **3D map provider (optional)** | `MAP_TILES_TOKEN` | A MapLibre-compatible vector/terrain tile provider, such as MapTiler, with a public style URL and token. | True pitched terrain and 3D buildings. |

The current map intentionally stays on key-free OpenStreetMap raster tiles for reliable local demos. A true pitched terrain/3D-building view requires a vector/terrain provider; Gemini, IMD, and Open-Meteo keys do not provide map 3D tiles.

### 3. API Documentation
- Interactive OpenAPI / Swagger UI: **http://127.0.0.1:8000/docs**
- Health Endpoint: `GET /api/health`
- Categories Endpoint: `GET /api/categories`
- Temporal Anomalies Endpoint: `GET /api/anomalies/temporal`
- Cross-Category Patterns: `GET /api/patterns/cross-category`
- Dual Queues: `GET /api/actions/queues`
- CSV Batch Upload: `POST /api/complaints/upload-csv`
- Citizen Photo Report (Gemini vision verification): `POST /api/civic/photo-report`
