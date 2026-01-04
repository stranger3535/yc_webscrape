# YC Companies Intelligence Platform

A full‑stack platform that scrapes Y Combinator companies, stores them in Neon Postgres, and exposes an interactive analytics dashboard built with Next.js.

- Live app: **https://yc-webscrape.vercel.app/**
- Backend API (Render): **https://yc-companies-api.onrender.com**

***

## Project Overview

- Scrapes YC company data from the YC directory / API, including core metadata and website information.
- Stores normalized data in Neon serverless Postgres for querying, analytics, and historical tracking.
- Exposes REST APIs (companies, analytics, scrape runs) from a Python backend deployed on Render.
- Frontend is a Next.js 13+ app (TypeScript + Tailwind) deployed on Vercel that visualizes companies and analytics.

***

## Architecture

```text
YC Directory / YC API
          │
          │  HTTP (requests / aiohttp)
          ▼
  Python Scraper (async)
          │
          │  psycopg2 / SQL
          ▼
   Neon Postgres Database
 (companies, snapshots,
  enrichment, scrape_runs)
          │
          │  JSON over HTTPS
          ▼
 Backend API (Render, Python)
  - GET /api/companies
  - GET /api/companies/:id
  - GET /api/analytics
  - GET /api/scrape-runs
          │
          │  NEXT_PUBLIC_API_BASE_URL
          ▼
Next.js Frontend (Vercel)
  - /               → Landing / explorer
  - /companies      → Companies table
  - /companies/[id] → Company details
  - /analytics      → Charts & metrics
```

***

## Features

### Scraper & Backend

- Python scraping pipeline for YC companies (list, detail, and website enrichment).
- Async HTTP requests and HTML parsing (e.g. aiohttp + BeautifulSoup).
- Incremental updates to avoid duplicates and keep history in snapshot tables.
- REST API on Render that reads from Neon Postgres and returns JSON for the frontend.

### Database (Neon Postgres)

Typical tables:

- `companies`: core YC company metadata (name, batch, status, tags, location, website, etc.).
- `company_snapshots`: tracks historical changes over time.
- `company_web_enrichment`: extra info scraped from each company’s own website.
- `scrape_runs`: run‑level metrics (duration, counts, errors, timestamps).

### Frontend (Next.js on Vercel)

- Company explorer with search, filters, pagination, and links to company websites.
- Company detail pages with richer information and historical context.
- Analytics page showing distributions by batch, stage, and country, plus a companies table and CSV export.

***

## Tech Stack

- **Language / Backend:** Python (scraper + API service).
- **Database:** Neon serverless Postgres (managed Postgres on Neon).
- **Frontend:** Next.js 13+ with TypeScript, React, and Tailwind CSS.
- **Hosting:**  
  - Frontend → Vercel (`yc-intel/frontend` → `yc-webscrape.vercel.app`).
  - Backend → Render Web Service (Python API).
  - Source control → GitHub (`stranger3535/yc_webscrape`).

***

## Local Development

### 1. Backend (scraper + API)

From repo root:

```bash
cd yc_intel

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt
```

Configure Neon Postgres via environment variables:

```bash
# Option 1: single connection string from Neon
export DATABASE_URL="postgresql://USER:12341@HOST/neondb?sslmode=require"
```

Or split if your code expects individual fields:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=neondb
export POSTGRES_USER=yc_web
export POSTGRES_PASSWORD=12341
```

Run scraper (example):

```bash
python scraper/detail_scraper.py
```

Run API server (FastAPI / Flask / etc.) so it exposes:

- `GET /api/companies`
- `GET /api/companies/:id`
- `GET /api/analytics`
- `GET /api/scrape-runs`

Typically served on `http://localhost:8000`.

### 2. Frontend (Next.js)

From repo root:

```bash
cd yc-intel/frontend

npm install
npm run dev
```

Environment config (`yc-intel/frontend/.env.local`):

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Then:

- App: http://localhost:3000  
- Analytics: http://localhost:3000/analytics

***

## Deployment

### Frontend – Vercel

1. Push changes to GitHub (`master` or main).
2. In Vercel, import the `yc_webscrape` repo and set the root directory to `yc-intel/frontend`.
3. Set environment variables:

   ```txt
   NEXT_PUBLIC_API_BASE_URL=https://yc-companies-api.onrender.com
   ```

4. Deploy; Vercel builds and hosts at `https://yc-webscrape.vercel.app/`.

### Backend – Render

1. Create a **Web Service** in Render from this GitHub repo, pointing to your backend folder (inside `yc-intel`).
2. Set build & start commands for your Python web framework.
3. Configure Neon in Render:

   ```txt
   DATABASE_URL = <Neon connection string with sslmode=require>
   ``` [5][4]

4. Deploy; Render gives a URL like `https://yc-companies-api.onrender.com`, which must match `NEXT_PUBLIC_API_BASE_URL` in Vercel.

***

## Data Flow

1. Scraper fetches YC companies and their websites.
2. New and updated records are stored in Neon Postgres (companies + snapshots + enrichment).
3. Backend API reads from Neon and serves JSON.
4. Next.js frontend calls the API, renders tables and charts, and supports CSV export.

***

## License

MIT (or update to your preferred license).

***
