import os
from dotenv import load_dotenv
import psycopg2
import requests
from datetime import datetime
from typing import List, Dict

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

ALGOLIA_URL = "https://45bwzj1sgc-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(3.35.1)%3B%20Browser%3B%20JS%20Helper%20(3.16.1)&x-algolia-application-id=45BWZJ1SGC&x-algolia-api-key=MjBjYjRiMzY0NzdhZWY0NjExY2NhZjYxMGIxYjc2MTAwNWFkNTkwNTc4NjgxYjU0YzFhYTY2ZGQ5OGY5NDMxZnJlc3RyaWN0SW5kaWNlcz0lNUIlMjJZQ0NvbXBhbnlfcHJvZHVjdGlvbiUyMiUyQyUyMllDQ29tcGFueV9CeV9MYXVuY2hfRGF0ZV9wcm9kdWN0aW9uJTIyJTVEJnRhZ0ZpbHRlcnM9JTVCJTIyeWNkY19wdWJsaWMlMjIlNUQmYW5hbHl0aWNzVGFncz0lNUIlMjJ5Y2RjJTIyJTVE"

def scrape_all_companies() -> List[Dict]:
    """Fetch all YC companies via pagination."""
    all_companies = []
    page = 0
    hits_per_page = 100
    
    while True:
        print(f"Fetching page {page}...")
        body = {
            "requests": [{"indexName": "YCCompany_production", "params": f"query=&hitsPerPage={hits_per_page}&page={page}"}]
        }
        resp = requests.post(ALGOLIA_URL, json=body, timeout=15)
        data = resp.json()
        hits = data["results"][0]["hits"]
        
        if not hits:
            break
        all_companies.extend(hits)
        print(f"Got {len(hits)} companies (total: {len(all_companies)})")
        page += 1
        if len(hits) < hits_per_page:
            break
    
    return all_companies

def upsert_companies(companies: List[Dict]):
    """Insert/update companies table with slug."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    new_count = 0
    existing_count = 0
    
    for company in companies:
        yc_company_id = str(company.get("id"))
        name = company.get("name", "").strip()
        slug = company.get("slug")
        domain = company.get("website", "").replace("http://", "").replace("https://", "").split("/")[0] if company.get("website") else None
        
        # Upsert logic
        cur.execute("""
            INSERT INTO companies (yc_company_id, name, domain, slug, last_seen_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (yc_company_id) DO UPDATE SET
                name = EXCLUDED.name,
                domain = EXCLUDED.domain,
                slug = EXCLUDED.slug,
                last_seen_at = NOW(),
                is_active = TRUE
        """, (yc_company_id, name, domain, slug))
        
        if cur.rowcount == 1:
            new_count += 1
        else:
            existing_count += 1
    
    conn.commit()
    print(f"Inserted {new_count} new companies, updated {existing_count}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    companies = scrape_all_companies()
    upsert_companies(companies)
