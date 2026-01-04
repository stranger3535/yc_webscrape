from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")

app = FastAPI(title="YC Companies API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

def get_db():
    return psycopg2.connect(NEON_DATABASE_URL, cursor_factory=RealDictCursor)

@app.get("/")
def root():
    return {"message": "YC API Running", "status": "ok"}

@app.get("/api/stats")
def get_stats():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT (SELECT COUNT(*) FROM companies) as total_companies")
    stats = cur.fetchone()
    cur.close()
    conn.close()
    return stats

@app.get("/api/companies")
def get_companies(page: int = 1, limit: int = 20):
    conn = get_db()
    cur = conn.cursor()
    offset = (page - 1) * limit
    cur.execute("SELECT id, name, slug, domain FROM companies ORDER BY id LIMIT %s OFFSET %s", (limit, offset))
    companies = cur.fetchall()
    cur.close()
    conn.close()
    return {"data": companies}

@app.get("/api/analytics")
def get_analytics():
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT batch, COUNT(DISTINCT company_id) as count FROM company_snapshots WHERE batch IS NOT NULL GROUP BY batch ORDER BY batch DESC LIMIT 20")
    batches = cur.fetchall()
    
    cur.execute("SELECT stage, COUNT(*) as count FROM company_snapshots WHERE stage IS NOT NULL GROUP BY stage ORDER BY count DESC")
    stages = cur.fetchall()
    
    cur.execute("SELECT location, COUNT(*) as count FROM company_snapshots WHERE location IS NOT NULL AND location != '' GROUP BY location ORDER BY count DESC LIMIT 15")
    locations = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return {"batches": batches, "stages": stages, "locations": locations}
