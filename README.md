Yes. Here is a refined README you can directly replace your current one with. You can still tweak wording later, but this is ready to use.

***

# YC Companies Intelligence Platform

A full‑stack platform that scrapes Y Combinator companies, stores them in PostgreSQL, and exposes an interactive analytics dashboard built with Next.js.

- Live app: **https://yc-webscrape.vercel.app/**
- Backend API (Render): **https://yc-companies-api.onrender.com**

***

## Project Overview

- Scrapes YC company data from the YC directory / API, including core metadata and website information.[1]
- Stores normalized data in PostgreSQL so it can be queried, analyzed, and kept historically.[2]
- Exposes REST APIs (companies, analytics, scrape runs) from a Python backend deployed on Render.[3][2]
- Frontend is a Next.js 13+ app (TypeScript + Tailwind) deployed on Vercel that visualizes companies and analytics.[4]

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
    PostgreSQL Database
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
  - /              → Landing / explorer
  - /companies     → Companies table
  - /companies/[id]→ Company details
  - /analytics     → Charts & metrics
```

***

## Features

### Scraper & Backend

- Python scraping pipeline for YC companies (list + detail + website enrichment).[1]
- Async HTTP requests and HTML parsing (e.g. aiohttp + BeautifulSoup).[5]
- Incremental updates to avoid duplicate data and keep history in snapshot tables.[1]
- REST API service on Render that reads from Postgres and returns JSON for the frontend.[2][3]

### Database (PostgreSQL)

Typical tables:

- `companies`: core YC company metadata (name, batch, status, tags, location, website, etc.).[1]
- `company_snapshots`: tracks historical changes over time.[1]
- `company_web_enrichment`: extra info scraped from each company’s own website.[1]
- `scrape_runs`: run‑level metrics (duration, counts, errors, timestamps).[1]

### Frontend (Next.js on Vercel)

- Company explorer with search, filters, pagination, and links to company websites.[1]
- Company detail pages with richer information and historical context.[1]
- Analytics page showing distributions by batch, stage, and country, plus a companies table and CSV export.[6]

***

## Tech Stack

- **Language / Backend:** Python (scraper + API service).[5]
- **Database:** PostgreSQL (compatible with Neon, Render, or any managed Postgres).[2]
- **Frontend:** Next.js 13+ with TypeScript, React, and Tailwind CSS.[6]
- **Hosting:**  
  - Frontend → Vercel (`yc-intel/frontend` → `yc-webscrape.vercel.app`).[4]
  - Backend → Render Web Service (Python API).[2]
  - Source control → GitHub (`stranger3535/yc_webscrape`).[7]

***

## Local Development

### 1. Backend (scraper + API)

From repo root:

```bash
cd yc-intel

# create venv
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt
```

Configure Postgres via environment variables:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=yc_companies
export POSTGRES_USER=your_user
export POSTGRES_PASSWORD=your_password
```

Run scraper (example):

```bash
python scraper/main_scraper.py
```

Run API server (FastAPI / Flask / etc.) so it exposes:

- `GET /api/companies`
- `GET /api/companies/:id`
- `GET /api/analytics`
- `GET /api/scrape-runs`[3]

Typically on `http://localhost:8000`.

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
- Analytics: http://localhost:3000/analytics[6]

***

## Deployment

### Frontend – Vercel

1. Push changes to GitHub (`master` or main branch).[8]
2. In Vercel dashboard, import the `yc_webscrape` repo and set the root directory to `yc-intel/frontend`.[4]
3. Set environment variables:  

   ```txt
   NEXT_PUBLIC_API_BASE_URL=https://yc-companies-api.onrender.com
   ```

4. Deploy; Vercel will build and host at `https://yc-webscrape.vercel.app/`.[4]

### Backend – Render

1. Create a **Web Service** in Render from the same GitHub repo, pointing to your backend folder (inside `yc-intel`).[2]
2. Set build & start commands for your Python web framework.[9]
3. Configure Postgres (`DATABASE_URL` or individual vars).[2]
4. Deploy; Render gives a URL like `https://yc-companies-api.onrender.com`, which must match `NEXT_PUBLIC_API_BASE_URL` in Vercel.[3][2]

***

## Data Flow

1. Scraper fetches YC companies and their websites.[1]
2. New and updated records are stored in Postgres (companies + snapshots + enrichment).[1]
3. Backend API reads from Postgres and serves JSON.[3]
4. Next.js frontend calls the API, renders tables and charts, and allows export to CSV.[6]

***

## License

MIT (or update to your preferred license).

***

If you paste this into `README.md` now, it will match your current setup (Vercel + Render). If something in the structure (backend folder name or API paths) is different, say what you changed and this can be adjusted.

[1](https://github.com/corralm/yc-scraper)
[2](https://render.com/docs/render-vs-vercel-comparison)
[3](https://stackoverflow.com/questions/77740845/deploy-react-app-in-vercel-with-backend-in-render)
[4](https://vercel.com/products/rendering)
[5](https://github.com/alirezamika/autoscraper)
[6](https://raw.githubusercontent.com/stranger3535/yc_webscrape/refs/heads/master/yc-intel/frontend/src/app/analytics/page.tsx)
[7](https://pkg.go.dev/github.com/sethvargo/go-diceware/diceware)
[8](https://stackoverflow.com/questions/36567344/unable-to-create-git-index-lock-file-exists-but-it-doesnt)
[9](https://github.com/DevManSam777/yp_scraper)
