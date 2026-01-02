import requests
import json
from typing import List, Dict

ALGOLIA_URL = "https://45bwzj1sgc-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(3.35.1)%3B%20Browser%3B%20JS%20Helper%20(3.16.1)&x-algolia-application-id=45BWZJ1SGC&x-algolia-api-key=MjBjYjRiMzY0NzdhZWY0NjExY2NhZjYxMGIxYjc2MTAwNWFkNTkwNTc4NjgxYjU0YzFhYTY2ZGQ5OGY5NDMxZnJlc3RyaWN0SW5kaWNlcz0lNUIlMjJZQ0NvbXBhbnlfcHJvZHVjdGlvbiUyMiUyQyUyMllDQ29tcGFueV9CeV9MYXVuY2hfRGF0ZV9wcm9kdWN0aW9uJTIyJTVEJnRhZ0ZpbHRlcnM9JTVCJTIyeWNkY19wdWJsaWMlMjIlNUQmYW5hbHl0aWNzVGFncz0lNUIlMjJ5Y2RjJTIyJTVE"

def scrape_all_companies() -> List[Dict]:
    """Fetch all YC companies via pagination."""
    all_companies = []
    page = 0
    hits_per_page = 100  # Max Algolia usually allows
    
    while True:
        print(f"Fetching page {page}...")
        body = {
            "requests": [
                {
                    "indexName": "YCCompany_production",
                    "params": f"query=&hitsPerPage={hits_per_page}&page={page}"
                }
            ]
        }
        
        resp = requests.post(ALGOLIA_URL, json=body, timeout=15)
        data = resp.json()
        hits = data["results"][0]["hits"]
        
        if not hits:
            break
            
        all_companies.extend(hits)
        print(f"Got {len(hits)} companies (total so far: {len(all_companies)})")
        
        page += 1
        
        if len(hits) < hits_per_page:
            break
    
    return all_companies

def main():
    companies = scrape_all_companies()
    print(f"\nTotal companies scraped: {len(companies)}")
    
    # Print first 3 with all fields
    for i, company in enumerate(companies[:3]):
        print(f"\nCompany {i+1}:")
        print(json.dumps(company, indent=2)[:500] + "...")

if __name__ == "__main__":
    main()
