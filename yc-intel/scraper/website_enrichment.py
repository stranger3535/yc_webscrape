import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import psycopg2
import re
import asyncio
import aiohttp
from typing import Optional

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def check_website(session: aiohttp.ClientSession, domain: str) -> dict:
    """Check company website for careers, blog, email."""
    if not domain:
        return {"has_careers_page": False, "has_blog": False, "contact_email": None}
    
    # Clean domain
    if domain.startswith(('http://', 'https://')):
        url = domain
    else:
        url = f"https://{domain}"
    
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as resp:
            if resp.status != 200:
                return {"has_careers_page": False, "has_blog": False, "contact_email": None}
            
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            
            # Check careers/jobs
            careers_links = soup.find_all("a", href=re.compile(r'(careers?|jobs)', re.I))
            has_careers = len(careers_links) > 0
            
            # Check blog
            blog_links = soup.find_all("a", href=re.compile(r'blog', re.I))
            has_blog = len(blog_links) > 0
            
            # Extract email
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', html)
            contact_email = emails[0] if emails else None
            
            return {
                "has_careers_page": has_careers,
                "has_blog": has_blog,
                "contact_email": contact_email
            }
    except:
        return {"has_careers_page": False, "has_blog": False, "contact_email": None}

async def enrich_all_websites():
    """Enrich all companies."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Get companies with domains
    cur.execute("SELECT id, domain FROM companies WHERE domain IS NOT NULL AND is_active = TRUE")
    companies = [{"db_id": row[0], "domain": row[1]} for row in cur.fetchall()]
    
    connector = aiohttp.TCPConnector(limit=20)
    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []
        for company in companies:  # All companies
            tasks.append(check_website(session, company["domain"]))
        
        results = await asyncio.gather(*tasks)
    
    # Save results
    updated = 0
    for i, company in enumerate(companies):
        enrichment = results[i]
        cur.execute("""
            INSERT INTO company_web_enrichment (company_id, has_careers_page, has_blog, contact_email, scraped_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (company_id) DO UPDATE SET
                has_careers_page = EXCLUDED.has_careers_page,
                has_blog = EXCLUDED.has_blog,
                contact_email = EXCLUDED.contact_email,
                scraped_at = NOW()
        """, (company["db_id"], enrichment["has_careers_page"], enrichment["has_blog"], enrichment["contact_email"]))
        
        if cur.rowcount == 1:
            updated += 1
    
    conn.commit()
    print(f"Updated {updated} companies with website data")
    cur.close()
    conn.close()

if __name__ == "__main__":
    asyncio.run(enrich_all_websites())
