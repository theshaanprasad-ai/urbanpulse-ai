# UrbanPulse AI — Urban Problem Trend Detection for Municipal Decision Support

> **Hackathon Track 9 — Urban Problem Trend Detection**
> A decision-support platform that analyzes municipal complaint datasets across **temporal** and **spatiotemporal** dimensions to detect **statistically significant anomalies**, then routes each signal to the right human queue for **targeted intervention** before a routine complaint becomes a neighborhood-wide failure.

A single complaint is noise. A **quintupling of drainage complaints in one ward over 72 hours** is a signal — and it is the signal a corporation already owns the data for, but has no way to hear. UrbanPulse AI is that hearing mechanism.

---

## 1. Track-9 requirement → where it is implemented

| Requirement in the problem statement | Implementation | File |
| --- | --- | --- |
| Complaints across many categories (waste, water, roads, drainage, streetlights) | 9 canonical municipal wings, each with a real owning department, SLA hours and a per-day baseline rate; legacy category names are mapped in | `backend/app/engine/civic_intelligence.py`, `complaint_category_configs` table |
| "Individual complaints may appear routine" | Minimum-volume guard: a cell with fewer than 3 observations can never alert, by design | `MIN_OBSERVED` in `temporal_anomaly_engine.py` |
| "A rapid increase within a particular **area or category**" | Every (ward × category) cell is tested independently against **its own** recent history — never a citywide average | `temporal_anomaly_engine.evaluate_cell` |
| "Temporal dimension" | 24 h and 72 h observation windows against a 28-day baseline, with a 2-day guard band and shrunk day-of-week factors | `temporal_anomaly_engine.py` |
| "Spatiotemporal dimension" | Fixed-radius density clustering (400 m / 72 h / min 3) scored against the same *location's* history, plus 7 km neighbourhood pooling across ward centroids | `spatiotemporal_engine.py` |
| "Statistically significant anomalies" | Exact conditional Poisson-rate test (binomial form), negative-binomial fallback under overdispersion, **Benjamini–Hochberg FDR at α = 0.05** across the full cell family | `temporal_anomaly_engine._test_window`, `benjamini_hochberg` |
| "Emergent urban issues" | Lifecycle classification `NEW_OR_RARE` / `EMERGING` / `PERSISTENT` / `EXPANDING`, plus change-point shape (`SPIKE` vs `SUSTAINED_INCREASE`) | `temporal_anomaly_engine.lifecycle`, `temporal_pattern` |
| "Robust decision-support platform" | Median/MAD robust baselines, per-anomaly limitation text, `INSUFFICIENT_HISTORY` status instead of a fabricated verdict, three nested AI fallbacks | `analytics_service.py`, `temporal_anomaly_engine.py` |
| "Targeted intervention" | Dual queues (Queue A systemic patterns / Queue B 30-minute life-safety hazards), transparent priority formula, operator state machine, immutable audit trail | `decision_support.py`, `alert_generator.py`, `action_audit_logs` |
| Cross-category insight (beyond the brief) | Co-occurrence discovery with a mandatory correlation≠causation guardrail | `cross_category_engine.py` |
| Duplicate-suppressed signal (beyond the brief) | Spatiotemporal + semantic duplicate candidates merged **by a human** into a `LinkedIncident`; analytics count a merged problem once | `duplicate_detector.py`, `linked_incidents` |

---

## 2. Architecture

```
[ Ingestion ]
  Municipal citizen reports — English, Tamil, Hindi, Hinglish, romanized Tamil (text + photo)
  Municipal CSV / JSON batch exports (column auto-mapping + bbox audit + rejection log)
  Environmental context (IMD AWS rainfall, NWP forecasts) — a CONFOUNDER, not the subject

                     │
                     ▼
[ Analytics engines — pure NumPy/SciPy functions, no framework, no hidden state ]
  civic_intelligence      sanitize → language → category → severity → hazard flag → gazetteer location
  temporal_anomaly_engine 24h/72h vs 28-day baseline, guard band, weekday factors,
                          Poisson-rate test → NB fallback → Benjamini-Hochberg FDR
  spatiotemporal_engine   400m/72h/min-3 clusters vs same-location history; 7km neighbourhood pooling
  cross_category_engine   both-elevated gate, co-location ≤500m/≤48h, 31-day Spearman, hypothesis templates
  duplicate_detector      0.40 distance / 0.20 time / 0.40 text, hard gates 400m & 48h
  impact_risk_engine      Mode 1 deterministic 6-factor score · Mode 2 logistic · What-If stress test
  rainfall_analyzer       IMD intensity bands, Antecedent Precipitation Index, IDW for ungauged wards
  alert_generator         strictly separated 3 alert classes, each carrying its own data gaps
  decision_support        ranked Queue A / Queue B actions with an explicit priority breakdown
  photo_scanner           Gemini vision verdict + offline fallback, never silent
  evaluation              reproducible synthetic-injection benchmark of the detector above
  climate_stress          multi-decadal planning scenarios (never a 24-hour forecast)

                     │
                     ▼
[ Persistence ] Supabase Postgres (or local SQLite fallback) — 21 tables, additive-only migrations
[ API ]         FastAPI, 33 endpoints, Swagger at /docs
[ UI ]          React 19 + TypeScript + Vite + Tailwind + Leaflet + Recharts
                  Resident workspace (3 tabs)  ·  Control room (11 tabs)
```

---

## 3. Detection methodology — the numbers, exactly

### 3.1 Temporal anomaly detection

For one (ward, category) cell we hold 37 daily windows. Window 0 is the current 24 h (or 72 h); windows 1–2 are a **guard band** so a developing event cannot absorb itself into its own baseline; windows 3–30 form the baseline.

- **Expected rate** comes from the baseline windows, scaled by **shrunk day-of-week factors** (mean 1.0, estimated only with ≥28 covered windows) so a Saturday surge in waste collection is not called an anomaly.
- **Test**: the exact conditional Poisson-rate test, evaluated in binomial form as `P(X ≥ x) = 1 − F_Binom(x−1; N_total, π)`, where π is the expected share of the pooled count. Jeffreys +0.5 pseudo-counts keep a zero baseline finite instead of undefined.
- **Overdispersion**: if baseline variance exceeds 1.2 × the mean, the test switches to a **negative binomial** with method-of-moments dispersion. Verified by a unit test asserting the NB p-value is *larger* — more conservative — than Poisson on identical data.
- **Multiple comparisons**: all ward × category × window cells form one family, corrected with **Benjamini–Hochberg** at α = 0.05. Q-values, not raw p-values, drive the decision.
- **Decision**: `ANOMALY` if q ≤ 0.05 and observed ≥ 3; `WATCH` in the elevated tier; otherwise `NORMAL`. Sparse history returns `INSUFFICIENT_HISTORY` and displays no p-value rather than inventing one.
- **Interpretation aids**: 95% CI plus a 95% upper prediction bound on the expected count; per-100k-population normalization; and a **category-share binomial test** that distinguishes "drainage surged here" from "this ward is reporting more about everything."
- **MAD** (median absolute deviation, 1.4826 divisor) is computed as a **robust descriptive statistic only**. It is never a decision input — the alert comes from the tested p-value. When MAD = 0 the record shows no z-score.

### 3.2 Spatiotemporal clustering

Greedy **fixed-radius density clustering**: 400 m radius, 72 h window, minimum 3 reports, seeded from the densest unassigned point. A cluster is significant only against the count history of *that same spot* over 28 days, so a chronically problematic street does not re-alert while a newly deteriorating one does. Zones whose centroids sit within 7 km are also pooled and tested jointly (minimum 5 observations) to catch regional rises that are individually sub-threshold. Cluster and neighbourhood tests form separate FDR families.

### 3.3 Cross-category cascade hypotheses

A candidate pair requires **both** categories to be independently elevated (nominal 72 h p < 0.05, ≥3 complaints each). Evidence is co-location (≤500 m, ≤48 h) plus a 31-day Spearman correlation of daily counts; a constant series yields `None` rather than a fabricated 0. Hypotheses come from 5 domain templates and are always shipped with the disclaimer that co-occurrence indicates compound stress warranting joint inspection, **not mechanical causation**. Stated honestly in code: these hypotheses are *not* FDR-corrected.

### 3.4 Duplicate incident linking

Hard gates first (≤400 m, ≤48 h), then `score = (0.40·S_dist + 0.20·S_time + 0.40·S_text) · F_category`, with `S_text = max(token Jaccard, character-trigram Jaccard)` and `F_category = 0.6` when categories differ. Records with no coordinates fall back to same-zone comparison at a fixed weak location score of 0.30 — never invented coordinates. ≥0.75 suggests `LIKELY_DUPLICATE`, ≥0.60 `POSSIBLE_DUPLICATE`. A scan of recent complaints uses a sliding time window, avoiding an O(n²) pass. **Nothing merges automatically:** a human confirms, producing a `LinkedIncident` without deleting either record, and rejections are persisted so the pair is never re-suggested. The score is a heuristic similarity, not a probability.

### 3.5 Multilingual intake

Language detection by Unicode script range (Tamil, Devanagari) then romanized-Hinglish heuristics; categorization by keyword scoring (+3 multi-word phrases, +1 single terms) with subcategory rules; severity 1–5 heuristics; a separate severe-hazard lexicon that routes straight to Queue B. Input is sanitized (control characters, HTML stripped, repetition collapsed, 1000-character cap). Location resolution returns `PROVIDED_COORDINATES` → `GAZETTEER_LANDMARK` (≈20 verified Chennai landmarks, including Tamil and Devanagari aliases) → `ZONE_ONLY` → `UNRESOLVED`. Text that matches nothing stays `OTHER` and is disclosed as unmatched. The classifier is offline, deterministic, free, and explainable — deliberate choices for a system whose output is audited by a human.

### 3.6 Rainfall and flood context

Rainfall is modeled because it is the dominant **confounder** in drainage, waste and water-supply complaint surges — and because drainage is one of the five categories in the brief. IMD intensity bands, an Antecedent Precipitation Index (`Σ P_i · 0.85^i`, the standard soil-moisture proxy), short-duration intensity against typical Indian urban drain design capacity (20–25 mm/h), and IDW interpolation for wards without a gauge. The impact-risk layer is a deterministic six-factor score (rain ≤30, saturation ≤15, topography ≤15, imperviousness ≤15, drainage and subway assets ≤15, civic recurrence ≤10) with a What-If stress test, plus a logistic-regression Mode 2 for comparison against the physical ordering. A separate climate tab holds CMIP6/INDRA SSP2-4.5 and SSP5-8.5 scenarios for 30-year master planning, banner-marketed in the UI as **not** a 24-hour forecast.

---

## 4. Interfaces

**Resident workspace** (light UI, email + password, no OTP): pick one of six problem types, photograph it, add an optional landmark, share location only if you choose to. Gemini vision confirms or holds the report and says so in plain language. "Your reports" and "Nearby city reports" close the loop.

**Control room** (11 tabs): Operational Command Center · Spatiotemporal Impact Map (6 toggleable layers, India-bounded, per-ward evidence drawer) · Temporal Anomaly Explorer · Cross-Category Patterns · Hotspot & Event Replay · Impact Risk Engine with What-If sliders · Rainfall Intelligence · Dual Decision Queues (Acknowledge → Assign → Dispatch → Resolve, every step audited) · Civic Grievance Ledger + NLP intake + CSV importer · Data Sources & Model Evaluation · Climate Stress. One-tap switch between workspaces; the full toolkit is never hidden from an operator.

---

## 5. What is live computation, and what is a demo fixture

We would rather state this than have you find it.

| Endpoint | Status |
| --- | --- |
`POST /api/civic/complaints`, `/civic/photo-report`, `/civic/duplicates(+resolve)`, `/complaints/upload-csv`, `/actions(+queues,/update)`, `/alerts`, `/risk/what-if`, `/analytics/city`, `/analytics/quality`, `/ai/assistant` | **Live computed** — runs on whatever you submit, right now |
`/rainfall/analytics`, `/risk/assessments` | Live formulas over seeded inputs; a few contextual values (API index, hourly burst) are demo constants |
`/anomalies/temporal`, `/patterns/cross-category`, `/hotspots`, `/evaluation/report`, `/climate/scenarios` | **Curated demo rows** so the presentation never shows an empty screen |

The reason is statistical power, and it is worth stating out loud: the production detector needs roughly **30 days of complaint history** before it can legitimately call anything an anomaly. The seeded demo corpus is 23 narrated records spanning one evening — so `/analytics/city` correctly returns `INSUFFICIENT_HISTORY` on it rather than manufacturing detections. **A detector that refuses to alert without evidence is the correct behaviour for a system that routes emergency crews.** Point it at a 30-day municipal export and it lights up; the engine is unit-tested against exactly that shape of data.

---

## 6. Validation

- **61 automated tests** across 7 files (`PYTHONPATH=. pytest backend/tests`). They cover window-index boundaries, spike and sustained-increase detection, sparse-history refusal, zero-baseline rare events, empty cells, NB-vs-Poisson conservatism, weekday normalization and weekend-peak suppression, BH correctness, the minimum-count gate, chronic-location non-reports, neighbourhood dedupe, hypothesis disclaimers, gazetteer grounding, prompt-injection sanitization, coordinate refusal, CSV aliasing and rejection reasons, bbox validation, import limits, duplicate gates and category penalties, IMD thresholds, API decay, IDW, and both risk modes.
- `conftest.py` forces SQLite and blanks every credential **before any backend import**, so the suite can never reach production data or a paid API.
- **Reproducible synthetic benchmark** (`engine/evaluation.py`): Poisson nulls with injected negative-binomial surges run through the *production* detector including BH, reporting precision, recall and false-positive rate by baseline rate, spike magnitude and noise level, with `is_synthetic: true` and a limitation list shipped alongside — plus a `raw_volume_comparator` showing how the naive "alert when count exceeds N" rule performs on identical data.
- **Modeled flood-risk evaluation** (`docs/MODEL_EVALUATION.md`): N = 240 events (2015–2023), 5-fold **spatial-block** cross-validation over the Kosasthalaiyar, Cooum and Adyar basins to prevent spatial leakage; F1 0.883, ROC-AUC 0.924, Brier 0.098, 18.5-minute median detection delay, Cyclone Michaung confusion matrix, and a spatial holdout (0.852) deliberately reported lower than overall accuracy.

---

## 7. Limitations we publish in the product

Complaint counts measure **reporting propensity, not incidence** — a digitally affluent ward reads louder than an under-reporting one, so we normalize per 100k, baseline each location against itself, and disclose the residual bias. An anomaly is a signal to investigate, not a confirmed emergency. Ward attribution uses nearest-centroid distance, and boundaries are drawn as approximations rather than true polygons on the map. Rain-gauge coordinates are not stored, so station placement on the map is approximate. Cross-category hypotheses are not FDR-corrected. The What-If simulator is a relative stress test with no pipe network or flow routing. Climate scenarios are decadal planning context. Mode 2's current training set is a small demonstration matrix, so it validates the *pipeline*, not a production-grade predictive model.

---

## 8. Quickstart

```bash
# 1. Backend (from the repository root)
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env          # fill in your own values — see §9
PYTHONPATH=. pytest backend/tests
PYTHONPATH=. uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# 2. Frontend (second terminal)
cd frontend && npm install && npm run dev    # http://localhost:5173
```

Vite proxies `/api` to `127.0.0.1:8000`, so nothing else is needed locally. Swagger UI: `http://127.0.0.1:8000/docs`. Health: `GET /api/health` reports whether persistence is `SUPABASE_POSTGRES` or `LOCAL_SQLITE`.

**Supabase persistence.** On startup the backend creates any missing tables and columns (additive only — it never drops or alters), loads reference geography (the 15 Chennai wards, 9 category configs, vulnerable assets, historical inundation records, provider register), then loads the synthetic demo corpus. Seeding is idempotent, is skipped the moment any non-demo record exists, and logs a warning instead of blocking startup if it fails. Set `SEED_DEMO_DATA="false"` for a fixture-free deployment. Both the direct (`db.<ref>.supabase.co`) and transaction-pooler (`aws-<region>.pooler.supabase.co`) hosts work: psycopg is configured with `prepare_threshold=None` because Supavisor multiplexes server connections and otherwise breaks the prepared-statement cache, and `pool_pre_ping` handles pooled connections reaped mid-request. In the Supabase dashboard, turn **Authentication → Providers → Email → Confirm email** off so resident accounts sign in immediately.

**Gemini (optional).** Photo verification and the grounded copilot use `backend/app/engine/gemini_client.py`, retrying across models inside a latency budget (45 s vision, 30 s copilot). If Gemini is unavailable the photo report still succeeds through the offline classifier and records `scan_source: "LOCAL_RULES"` with a `scan_fallback_reason`, so a degraded scan is never silent; the copilot falls back to deterministic local answers built from the same live context and labels itself `LOCAL_GROUNDED_RULES`. The platform is fully functional with no Gemini key set.

**Deployment.** `vercel.json` builds the frontend and serves `dist`. Host the backend separately and set `VITE_API_BASE_URL` to its origin; leave it unset for local development. The map intentionally uses key-free OpenStreetMap raster tiles for reliable demos, and is constrained to India (6.4–35.7°N, 68.0–97.5°E). Chennai is the seeded pilot; Bengaluru and Bhubaneswar are listed but disabled because a city needs ward-level elevation, imperviousness, drainage and population data before there is anything to detect.

---

## 9. Security and data handling

- `.env.example` contains **placeholders only**. Copy it to `.env`, never commit `.env`, and never put a database password or a Supabase service-role key in frontend code. The anon key is Supabase's public client key and is intended to ship in the browser; the service-role key is never used by this application.
- `GEMINI_API_KEY` is read by the backend only and is never sent to the browser.
- All citizen-facing text is sanitized before classification or any model call; model output is schema-constrained and clamped (severity 1–5, confidence 0–1), and low-confidence vision results defer to the reporter's own category hint.
- CORS permits GET and POST with credentials disabled.
- Only problem descriptions, an optional landmark and an infrastructure photograph are stored — no names, phone numbers or device identifiers. `reporter_email` exists solely so a resident can retrieve their own submissions. Location sharing is optional and degrades gracefully on refusal. Coordinates are never invented: unverifiable reports are kept with null coordinates.
- Data sources, licences and attribution obligations are registered in `docs/DATA_SOURCES_REGISTER.md` (India OGD Policy, IMD open data, municipal grievance feed, ISRO Bhuvan CC-BY 4.0 30 m CartoDEM, OpenStreetMap ODbL, INDRA-CMIP6 CC-BY 4.0).
- Every irreversible action — dispatch, merge, resolve — is a human decision, and each one writes an `ActionAuditLog` row.

---

## 10. Repository map

```
backend/app/engine/     14 analytics modules — the substance of the project
backend/app/api/        33 FastAPI endpoints
backend/app/models/     21 SQLAlchemy tables
backend/app/fixtures/   reference geography + demo corpus seeding
backend/tests/          61 tests, credentials-blanked, SQLite-isolated
frontend/src/components 14 screens across both workspaces
docs/                   ARCHITECTURE · MODEL_EVALUATION · DATA_SOURCES_REGISTER · DEMO_SCRIPT
```

Further detail: `docs/ARCHITECTURE.md` (formulas and engine contracts), `docs/MODEL_EVALUATION.md` (metrics and validation design), `docs/DEMO_SCRIPT.md` (a 240-second walkthrough), `docs/DATA_SOURCES_REGISTER.md` (provenance and licensing).
