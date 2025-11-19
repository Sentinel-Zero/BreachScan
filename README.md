# BreachScan

A small security lab project exploring vulnerability data pipelines and asset risk. The current focus is a lightweight backend that serves mock Tenable/Nessus-style asset data via a clean API.

> Goal: ingest Tenable/Nessus-style data, normalize it, and expose queryable endpoints for hosts and risk. Mock data today; real ingestion later.

---

## What's Included

- FastAPI backend with permissive CORS (for easy frontend experimentation)
- Mock assets dataset (`sample_assets.json`)
- Simple REST endpoints to list assets and fetch a single asset

---

## Project Structure

```text
BreachScan/
  breachscan_backend/
    app/
      __init__.py
      main.py             # FastAPI app
      sample_assets.json  # Mock asset/risk data
    requirements.txt
  .gitignore
  README.md
```

---

## Prerequisites

- Python 3.10+ (recommended)
- Windows PowerShell (commands below use PowerShell)

---

## Environment Configuration

Runtime settings and (future) credentials are loaded via `pydantic` BaseSettings in `breachscan_backend/app/config.py`. The loader looks for a `.env` file at the project root.

1. Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

2. Edit the new `.env` and fill in real values (leave Tenable keys blank if you are still using mock data):

```
TENABLE_ACCESS_KEY=your_access_key_here
TENABLE_SECRET_KEY=your_secret_key_here
TENABLE_BASE_URL=https://cloud.tenable.com
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=info
SCHEDULE_EXPANSION_LIMIT=4096
```

3. Restart the server after changes so settings reload.

Never commit a populated `.env` with real secrets; keep only `.env.example` under version control.

---

## Setup (Windows PowerShell)

1) Create and activate a virtual environment

```powershell
cd c:\_WorkSpace\BreachScan\breachscan_backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Run the Backend

From `breachscan_backend`:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running:

- API root: http://127.0.0.1:8000/
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

## API Endpoints

Base URL: `http://127.0.0.1:8000`

- GET `/assets`
  - Returns the full list of assets with basic risk info.
  - Example (PowerShell):

    ```powershell
    curl http://127.0.0.1:8000/assets
    ```

- GET `/assets/{asset_id}`
  - Returns a single asset by ID, or `{ "error": "Asset not found" }` if missing.
  - Example:

    ```powershell
    curl http://127.0.0.1:8000/assets/host-001
    ```

---

## Sample Data

- File: `breachscan_backend/app/sample_assets.json`
- The backend reads directly from this file. You can edit it to try different scenarios, add fields, or simulate higher risk assets.

---

## Roadmap (Ideas)

- Real ingestion from Tenable.io / Nessus Pro via `pyTenable`
- Normalization and enrichment (e.g., severity scoring, tags, owners)
- Query/filter parameters (risk thresholds, tags, business unit)
- Persistence (SQLite/Postgres) instead of JSON file
- Authn/z for protected endpoints
- Frontend to visualize assets and risk

---

## Notes

- CORS is currently wide open to simplify local development. Tighten `allow_origins` in `app/main.py` before exposing the service more broadly.
- Dependencies are listed in `breachscan_backend/requirements.txt`. Update as features evolve.
# BreachScanner

BreachScanner is a small security lab project for exploring vulnerability data pipelines.

The current goal is:

> Build a backend service that ingests Tenable/Nessus-style vulnerability data, normalizes it, and exposes a clean API for querying hosts and their risk.

Right now the backend uses **mock JSON data** that mimics Tenable/Nessus assets. Later, this can be swapped for real API calls (Tenable.io, Nessus Pro, etc.) or Go-based services.

---

## Project Structure (so far)

```text
BreachScanner/
  breachscanner_backend/
    .venv/                # Python virtual environment (not committed)
    app/
      __init__.py
      main.py             # FastAPI app
      sample_assets.json  # Mock asset/risk data
    requirements.txt
  .gitignore
  README.md

