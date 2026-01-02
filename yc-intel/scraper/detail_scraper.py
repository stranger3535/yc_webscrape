import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import psycopg2
from datetime import datetime
import hashlib
import json

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_companies_from_db():
    """Get all active companies for detail scraping."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT id, yc_company_id, slug FROM companies WHERE is_active = TRUE")
    companies = [{"db_id": row[0], "yc_id": row[1], "slug": row[2]} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return companies

def scrape_company_detail(slug: str) -> dict:
    """Scrape detail page."""
    url = f"https://www.ycombinator.com/companies/{slug}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    resp = requests.get(url, headers=headers, timeout=10)
    
    if resp.status_code != 200:
        return None
    
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Extract fields (we'll adjust selectors after testing)
    batch = soup.find("span", class_="batch")  # Adjust selector
    stage = soup.find("span", class_="stage")   # Adjust selector
    description = soup.find("div", class_="description").text.strip() if soup.find("div", class_="description") else ""
    location = soup.find("span", class_="location").text.strip() if soup.find("span", class_="location") else ""
    tags = [tag.text.strip() for tag in soup.find_all("span", class_="tag")]
    
    return {
        "batch": batch.text.strip() if batch else None,
        "stage": stage.text.strip() if stage else None,
        "description": description,
        "location": location,
        "tags": tags
    }

def compute_hash(data: dict) -> str:
    """Compute SHA256 hash of snapshot data."""
    payload = json.dumps(data, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()

def save_snapshot(db_company_id: int, detail_data: dict):
    """Save to company_snapshots if changed."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    data = {
        "batch": detail_data.get("batch"),
        "stage": detail_data.get("stage"),
        "description": detail_data.get("description"),
        "location": detail_data.get("location"),
        "tags": detail_data.get("tags", [])
    }
    
    data_hash = compute_hash(data)
    
    # Check if latest snapshot has same hash
    cur.execute("""
        SELECT data_hash FROM company_snapshots 
        WHERE company_id = %s 
        ORDER BY scraped_at DESC LIMIT 1
    """, (db_company_id,))
    latest_hash = cur.fetchone()
    
    if latest_hash and latest_hash[0] == data_hash:
        print("No change")
        return
    
    # Insert new snapshot
    cur.execute("""
        INSERT INTO company_snapshots (company_id, batch, stage, description, location, tags, data_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (db_company_id, data["batch"], data["stage"], data["description"], data["location"], json.dumps(data["tags"]), data_hash))
    
    conn.commit()
    print("New snapshot saved")
    cur.close()
    conn.close()

if __name__ == "__main__":
    companies = get_companies_from_db()
    print(f"Found {len(companies)} companies to scrape details for")
    
    for i, company in enumerate(companies):
        print(f"\nScraping {company['slug']}...")
        detail = scrape_company_detail(company['slug'])
        if detail:
            save_snapshot(company['db_id'], detail)
        else:
            print("Failed to scrape detail")
