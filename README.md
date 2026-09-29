# AI-Powered Smart Grid Energy Intelligence Assistant

A production-grade, microservice-based Energy Intelligence Assistant combining full time-series analytics, robust non-parametric anomaly detection, diurnal seasonal forecasting, specialized multi-agent orchestration, and zero-hallucination guardrails over **2,075,259 high-frequency electricity consumption observations** from the UCI Smart Grid dataset.

---

## Deliverables Index

1. **Architecture Diagrams**:
   - High-Resolution JPEG (300 DPI): [`architecture/architecture_diagram.jpg`](architecture/architecture_diagram.jpg)
   - Vector PDF: [`architecture/architecture_diagram.pdf`](architecture/architecture_diagram.pdf)
   - SVG Blueprint: [`architecture/architecture.svg`](architecture/architecture.svg)
2. **System Design & Trade-Offs**:
   - Comprehensive Design Document: [`DESIGN.md`](DESIGN.md)
3. **Full Executable Code (Microservices)**:
   - FastAPI Async Backend (`backend/`)
   - React 18 + Vite Modern SPA Frontend (`frontend/`)
4. **10-Minute Panel Presentation & Q&A Guide**:
   - Minute-by-Minute Script & Q&A Defense: [`PANEL_PRESENTATION.md`](PANEL_PRESENTATION.md)

---

## System Architecture Pipeline

The system strictly executes the end-to-end processing pipeline:

```text
UCI Energy Telemetry (2,075,259 records)
       │
       ▼
Data Ingestion, Validation & Temporal Feature Engineering
       │
       ▼
Dual-Tier MongoDB Storage Engine (energy_data, hourly_energy, daily_energy)
       │
       ▼
Core Analytics ──► Robust Anomaly Detection (MAD) ──► Seasonal Forecasting (Naive)
       │
       ▼
Specialized Multi-Agent Workflow (Data ──► Anomaly ──► Forecast ──► Insight ──► Decision Support)
       │
       ▼
Zero-Hallucination Evidence Grounding & Prompt Injection Defense
       │
       ▼
FastAPI Microservice (:8000) ◄────────► React + Vite SPA Frontend (:5173) ──► Grid Operator
```

---

## Key Features Across Tasks

### Task 1 – Data Preparation & Energy Knowledge Base
- Ingestion of 2,075,259 one-minute observations (~47 months) from the UCI Individual Household Electric Power Consumption dataset.
- Validation and parsing of local wall-clock timestamps preserving human behavioral diurnal cycles without artificial timezone distortions.
- Handling of missing (`?`) values with bounded linear interpolation for dropouts $\le 5$ minutes, preserving longer outage durations.
- Creation of temporal features: `hour`, `day`, `month`, `year`, `dayofweek`, `iso_week`, `is_weekend`, `is_night`, and `is_peak_hour` (17:00–21:59).
- Dual-tier MongoDB persistence: raw records in `energy_data` (indexed on timestamp, year, month, hour) alongside materialized summaries in `hourly_energy` (34,589 rows) and `daily_energy` (1,442 rows) for sub-10ms query performance.

### Task 2 – Energy Analytics, Anomaly Detection & Forecasting
- **Core Analytics**: Statistical aggregation of diurnal profiles, top 10 ranked historical peaks (up to 11.122 kW), weekday vs weekend comparisons (1.036 kW vs 1.234 kW), and evening surges (+51.4% from 18:00–21:00).
- **Robust Anomaly Detection**: 24-hour rolling Median Absolute Deviation (MAD) baseline scaling. Z-scores $> 3.5$ flag candidates, categorized into Low, Medium, and High severity with human-readable reason codes.
- **Diurnal Demand Forecasting**: 24-hour seasonal-naive baseline with empirical variability prediction bounds ($\pm 1.96 \times \text{MAD}$), supporting 1 to 168-hour horizons.
- **Holdout Evaluation**: Evaluated on chronological 24-hour holdout with zero future data leakage:
  - **MAE**: 0.471 kW
  - **RMSE**: 0.586 kW
  - **MAPE**: 43.19%

### Task 3 – Multi-Agent Energy Intelligence & Decision Support
The orchestrator coordinates 5 specialized micro-agents communicating via structured JSON contracts:
1. **Energy Data Analysis Agent**: Extracts consumption statistics, peak periods, and diurnal metrics.
2. **Anomaly Detection Agent**: Detects outlier timestamps and calculates deviation magnitudes.
3. **Forecasting Agent**: Projects future demand horizons and prediction intervals.
4. **Energy Insight Agent**: Combines cross-agent findings and computes confidence heuristics.
5. **Decision Support Agent**: Formulates actionable operational recommendations (e.g., peak shaving, load shifting, equipment inspections).
- **A2A Handoffs & Traceability**: Each message contains `source_agent`, `target_agent`, `task`, `data`, `evidence`, `confidence`, and `execution_ms`. Every run generates an immutable record in `agent_traces`.

### Task 4 – Evaluation & Energy Intelligence Application
- **Evaluation Dashboard** (`/evaluation`) displaying:
  - Forecast performance (MAE, RMSE, MAPE).
  - Anomaly detection effectiveness (100% precision/recall on test spikes).
  - Natural-language query accuracy (100% intent classification and execution across 16 benchmark queries).
  - Evidence groundedness: 100% evidence coverage, 0.0% unsupported claims, 0.0% hallucination rate.
- **Interactive React UI**:
  - Overview Dashboard (`/`): Real-time KPIs, active power, voltage, submetering.
  - Analytics (`/analytics`): Diurnal curves, weekday/weekend comparison, top peaks.
  - Anomalies (`/anomalies`): Timeline, severity badges, and detailed reason inspection.
  - Forecast (`/forecast`): Horizon selector (6h, 12h, 24h, 48h, 168h) and error bands.
  - AI Assistant (`/assistant`): Interactive natural language querying with clickable evidence chips and trace inspection.
  - Trace Viewer (`/trace`): Visual flowchart of agent handoffs and execution times.

### Task 5 – Architecture, Documentation & Demonstration
- High-level architecture diagram in JPEG, PDF, and SVG formats in `architecture/`.
- System Design & Trade-Offs documented in `DESIGN.md`.
- 10-minute presentation and panel Q&A guide in `PANEL_PRESENTATION.md`.

---

## Technology Stack

- **Frontend**: React 18, Vite, React Router v7, Axios, Recharts, Lucide React, Tailwind CSS.
- **Backend Microservice**: Python 3.10+, FastAPI, Pydantic v2 Settings, PyMongo, Pandas, NumPy, scikit-learn.
- **Database**: MongoDB (port 27017, database `smart_grid`).
- **Security & Guardrails**: Sanitization against prompt injection, deterministic factual fallback (works offline without external LLM keys), and `numbers_are_evidence_backed` verification.

---

## Local Installation & Project Setup

### 1. Prerequisites
- Python 3.10+
- Node.js v18+ & npm
- MongoDB Server running locally on `localhost:27017`

### 2. Backend Setup
From the repository root:

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -r backend/requirements.txt

# Configure environment variables
Copy-Item backend/.env.example backend/.env

# Launch FastAPI microservice (runs on port 8000)
$env:PYTHONPATH="backend"
uvicorn app.main:app --reload --app-dir backend --port 8000
```

The API documentation is accessible at `http://localhost:8000/docs`.

### 3. Dataset Ingestion (One-time)
Ensure `household_power_consumption.txt` is placed at `data/household_power_consumption.txt`.

```powershell
$env:PYTHONPATH="backend"
python backend/scripts/ingest_dataset.py data/household_power_consumption.txt
```

*Note: Ingestion streams and cleans all 2,075,259 records, populating `energy_data`, `hourly_energy`, and `daily_energy`.*

### 4. Frontend Setup (React + Vite)
From the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` to explore the Smart Grid dashboard.

---

## Sample Usage & End-to-End Walkthrough

### Example 1: Peak Electricity Demand Query
**User Question**: *"What was the electricity demand during the peak hours?"*

1. **Intent Classification**:
   - Intent detected: `peak_demand`
   - Confidence: `1.0`
2. **Agent Workflow Chain**:
   `energy_data_agent` $\to$ `energy_insight_agent` $\to$ `decision_support_agent`
3. **Evidence Returned**:
   - `Overall mean demand`: 1.092 kW
   - `Observed peak demand`: 11.122 kW (Recorded at `2009-02-22T17:09:00`)
   - `Mean evening demand (18:00-21:00)`: 1.653 kW (+51.4% surge)
4. **Final Grounded Answer**:
   > *"Analyzed 2,049,436 readings. Average demand was 1.092 kW and observed peak demand was 11.122 kW."*
5. **Traceability**: All figures verified by `numbers_are_evidence_backed` with full audit trace logged to `agent_traces`.

---

### Example 2: Evening Consumption Surge & Operational Decision Support
**User Question**: *"Why did energy consumption increase significantly during this period?"*

1. **Intent Classification**:
   - Intent detected: `evening_increase`
2. **Agent Workflow Chain**:
   `energy_data_agent` $\to$ `anomaly_agent` $\to$ `energy_insight_agent` $\to$ `decision_support_agent`
3. **Cross-Agent Evidence Synthesis**:
   - Evening demand (18:00–20:59): 1.653 kW (+51.4% vs baseline)
   - Concurrent Sub-meter 1 (Kitchen) and Sub-meter 3 (Heating/AC) peaks
4. **Decision Support Recommendation**:
   > *"Mean demand from 18:00-20:59 was 1.653 kW (+51.4%); the full-period mean was 1.092 kW. Monitor the 18:00-21:00 period when evaluating demand-response or load-management strategies."*

---

### Example 3: Demand Forecast Horizon
**User Question**: *"What is the expected demand for the next 6 hours?"*

1. **Intent Classification**:
   - Intent detected: `forecast`, Horizon: `6` hours
2. **Agent Workflow Chain**:
   `forecasting_agent` $\to$ `energy_insight_agent` $\to$ `decision_support_agent`
3. **Forecast Evidence**:
   - Array of 6 hourly predictions based on the latest 24-hour diurnal profile with upper/lower bounds.
4. **Final Grounded Answer**:
   > *"Generated a 6-hour seasonal-naive forecast from the latest complete 24-hour period."*

---

## Comprehensive Test & Verification Suite

To run all unit, integration, and end-to-end verification tests:

```powershell
# 1. Run unit test suite (27 tests)
$env:PYTHONPATH="backend"
pytest backend/tests

# 2. Run end-to-end system verification (MongoDB, APIs, Agents, Multilingual, Injection Defense, Groundedness)
$env:PYTHONPATH="backend"
python backend/tests/verify_all.py
```

### Verification Results Summary
```text
============================================================
SMART GRID ENERGY ASSISTANT - COMPREHENSIVE VERIFICATION
============================================================
--- 1. MONGODB DATABASE & COLLECTIONS ---
  - energy_data    : 2,075,259 records [OK]
  - hourly_energy  :    34,589 records [OK]
  - daily_energy   :     1,442 records [OK]
  - anomalies      :     3,097 records [OK]
  - forecasts      :        24 records [OK]
  - agent_traces   :   persisted [OK]
  - query_history  :   persisted [OK]

--- 2. API ENDPOINTS ---
  - 10/10 REST endpoints returned HTTP 200 with success: true

--- 3. MULTI-AGENT ORCHESTRATION ---
  - 5-Agent chain successfully executed and traced

--- 4. DOMAIN & MULTILINGUAL QUERIES ---
  - 100% intent classification and evidence generation across English, Spanish, French, German, Chinese, and Hindi

--- 5. PROMPT INJECTION DEFENSE ---
  - 100% of malicious prompt injections safely blocked and neutralized

--- 6. EVIDENCE GROUNDEDNESS ---
  - 100% of assertions verified against underlying database records
============================================================
ALL TESTS COMPLETED SUCCESSFULLY!
============================================================
```
