**CLEAN & DIRECT README.md** - Copy & paste as-is:

```markdown
# YC Companies Intelligence Platform

A production-grade data pipeline that scrapes Y Combinator companies, stores structured data in PostgreSQL, and provides analytics through a Next.js frontend.

## 🎯 Project Overview

This platform scrapes **1000+ Y Combinator funded startups** with 10+ data fields per company, implements incremental data synchronization with deduplication, and exposes comprehensive analytics through REST APIs and an interactive dashboard.

## 🏗️ Architecture
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   YC Website    │────▶│   Python Scraper │────▶│  PostgreSQL     │
│   (Algolia)     │     │   (asyncio)      │     │   (Neon Cloud)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ├─ list_scraper.py
                               ├─ detail_scraper.py
                               ├─ website_enrichment.py
                               └─ main_scraper.py
                                      │
                        ┌─────────────┴──────────────┐
                        │                            │
                ┌───────▼────────┐         ┌────────▼───────┐
                │  Next.js APIs  │         │  Next.js Pages │
                │  (4 endpoints) │         │  (3 pages)     │
                └───────┬────────┘         └────────┬───────┘
                        │                          │
                        └──────────┬───────────────┘
                                   │
                        ┌──────────▼────────────┐
                        │  Frontend Dashboard  │
                        │  (React + Tailwind)  │
                        └──────────────────────┘
```


## ✨ Features

### Backend (Python Scraper)
- Scrapes all YC companies from Algolia API
- Detail page extraction with BeautifulSoup
- Incremental sync with SHA256 data deduplication
- Website enrichment (careers/blog/email detection)
- Async processing with aiohttp (20 concurrent requests)
- Performance metrics (per-company timing)
- Comprehensive logging (scraper.log)
- Error handling & graceful degradation

### Database (PostgreSQL)
- **companies** - 1000 rows with company metadata
- **company_snapshots** - 1000+ historical records with deduplication
- **company_web_enrichment** - 998 enriched records
- **scrape_runs** - Performance metrics and execution history

### APIs (REST)
- `GET /api/companies` - Paginated list with search & filters
- `GET /api/companies/:id` - Company details + snapshot history
- `GET /api/analytics` - Stage/country/tag distribution
- `GET /api/scrape-runs` - Scrape execution history

### Frontend (Next.js)
- Company Explorer - Search, filter, paginate 1000 companies
- Company Detail Page - Full history, enrichment data, timeline
- Analytics Dashboard - Charts, metrics, company table

## 🚀 Tech Stack

**Backend:**
- Python 3.9+ (requests, BeautifulSoup4, psycopg2, asyncio, aiohttp)

**Database:**
- PostgreSQL 15 (Neon Cloud recommended)

**Frontend:**
- Next.js 16 (TypeScript, React 19, Tailwind CSS, Recharts)

**Deployment:**
- Vercel (frontend)
- Neon PostgreSQL (database)
- GitHub (source control)

## 📝 Quick Start

### Local Development

```bash
# Backend
cd yc-intel
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python scraper/main_scraper.py

# Frontend
cd yc-frontend
npm install
npm run dev
# Visit http://localhost:3000
````

### Vercel Deployment

1. Push to GitHub
2. Import repo in Vercel
3. Add `POSTGRES_URL` environment variable (Neon connection string)
4. Deploy

## 🔄 How It Works

1. **Scrapes** all YC companies from Algolia
2. **Stores** company data with SHA256 hashing for deduplication
3. **Tracks** changes in snapshots table
4. **Enriches** websites for careers/blog/email
5. **Logs** all metrics to scrape_runs
6. **Exposes** 4 REST APIs
7. **Displays** analytics through Next.js frontend

## 📊 Data Captured

- Company name, domain, location
- Funding stage, batch, employee range
- Tags, description, website features
- Historical change tracking
- Performance metrics per scrape run

## 🎯 Requirements Met

✅ Scrape 1000+ companies (10+ fields each)
✅ Incremental sync with deduplication
✅ Historical snapshots with timestamps
✅ Website enrichment (careers/blog/email)
✅ Performance metrics per company
✅ Master scraper orchestration
✅ Inactive company marking
✅ 4 REST API endpoints
✅ 3 frontend pages
✅ Analytics dashboard
✅ Comprehensive logging
✅ Error handling & graceful degradation
✅ Production-ready deployment

## 📄 License

MIT

## 👨‍💻 Author

Abhijith kp

---
