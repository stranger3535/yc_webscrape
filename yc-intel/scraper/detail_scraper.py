import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import psycopg2
from datetime import datetime
import hashlib
import json
import time
import re
import logging
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

load_dotenv()
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")


class PerformanceTracker:
    """Track performance metrics per company"""
    def __init__(self):
        self.metrics = {}
    
    def start(self, metric_name):
        self.metrics[metric_name] = time.time()
    
    def end(self, metric_name):
        if metric_name in self.metrics:
            elapsed = (time.time() - self.metrics[metric_name]) * 1000  # ms
            return elapsed
        return 0
    
    def get_summary(self):
        return {k: v for k, v in self.metrics.items() if isinstance(v, (int, float))}


class DetailScraper:
    def __init__(self):
        self.stats = {
            'total_processed': 0,
            'new_companies': 0,
            'updated_companies': 0,
            'unchanged_companies': 0,
            'failed_companies': 0,
            'start_time': datetime.now(),
            'slowest_company': {'name': '', 'time': 0},
            'performance_logs': []
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.ensure_tables()
    
    def ensure_tables(self):
        """Create missing tables if they don't exist"""
        logger.info("Ensuring database tables exist...")
        conn = psycopg2.connect(NEON_DATABASE_URL)
        cur = conn.cursor()
        
        # Create company_web_enrichment table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS company_web_enrichment (
                company_id INTEGER PRIMARY KEY REFERENCES companies(id) ON DELETE CASCADE,
                has_careers_page BOOLEAN,
                has_blog BOOLEAN,
                contact_email TEXT,
                scraped_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create scrape_runs table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scrape_runs (
                id SERIAL PRIMARY KEY,
                started_at TIMESTAMP,
                ended_at TIMESTAMP,
                total_companies INTEGER,
                new_companies INTEGER,
                updated_companies INTEGER,
                unchanged_companies INTEGER,
                failed_companies INTEGER,
                avg_time_per_company_ms NUMERIC,
                slowest_company_name TEXT,
                slowest_company_time_ms NUMERIC
            )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        logger.info("✓ Database tables ready")
    
    def get_companies_from_db(self):
        """Get all active companies for detail scraping."""
        conn = psycopg2.connect(NEON_DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT id, yc_company_id, slug, name FROM companies WHERE is_active = TRUE ORDER BY id")
        companies = [
            {"db_id": row[0], "yc_id": row[1], "slug": row[2], "name": row[3]} 
            for row in cur.fetchall()
        ]
        cur.close()
        conn.close()
        return companies

    def scrape_company_detail(self, slug: str, perf: PerformanceTracker) -> dict:
        """Scrape detail page with performance tracking."""
        url = f"https://www.ycombinator.com/companies/{slug}"
        
        try:
            # Track index page fetch time
            perf.start('index_fetch')
            resp = self.session.get(url, timeout=10)
            index_fetch_time = perf.end('index_fetch')
            
            if resp.status_code != 200:
                logger.warning(f"Failed to fetch {slug}: HTTP {resp.status_code}")
                return None
            
            # Track HTML parsing time
            perf.start('html_parse')
            soup = BeautifulSoup(resp.text, "html.parser")
            html_parse_time = perf.end('html_parse')
            
            # Extract batch (e.g., W21, S22)
            batch = None
            batch_elem = soup.find(text=re.compile(r'[WS]\d{2}'))
            if batch_elem:
                match = re.search(r'([WS]\d{2})', batch_elem)
                if match:
                    batch = match.group(1)
            
            # Extract stage (Active, Acquired, Public)
            stage = "Active"
            stage_indicators = soup.get_text().lower()
            if "acquired" in stage_indicators:
                stage = "Acquired"
            elif "public" in stage_indicators or "ipo" in stage_indicators:
                stage = "Public"
            
            # Extract description
            description = ""
            desc_elem = soup.find("p", class_="whitespace-pre-line")
            if not desc_elem:
                desc_elem = soup.find("div", class_="prose")
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            # Extract location
            location = ""
            location_elem = soup.find(text=re.compile(r'\w+,\s*\w+'))
            if location_elem:
                location = location_elem.strip()
            
            # Extract tags/industries
            tags = []
            tag_elements = soup.find_all("a", href=re.compile(r'/companies\?industry='))
            for tag_elem in tag_elements:
                tag_text = tag_elem.get_text(strip=True)
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)
            
            # Extract employee range
            employee_range = None
            emp_text = soup.get_text()
            emp_patterns = [
                r'(\d+-\d+)\s*employees',
                r'(\d+\s*-\s*\d+)\s*people',
                r'Team size:\s*(\d+-\d+)'
            ]
            for pattern in emp_patterns:
                match = re.search(pattern, emp_text, re.IGNORECASE)
                if match:
                    employee_range = match.group(1).replace(' ', '')
                    break
            
            return {
                "batch": batch,
                "stage": stage,
                "description": description,
                "location": location,
                "tags": tags,
                "employee_range": employee_range,
                "index_fetch_time": index_fetch_time,
                "html_parse_time": html_parse_time
            }
        
        except Exception as e:
            logger.error(f"Error scraping {slug}: {e}")
            return None

    def enrich_from_website(self, domain: str, perf: PerformanceTracker) -> dict:
        """Website enrichment with 3-second timeout."""
        if not domain or domain == '':
            return {
                "has_careers_page": False,
                "has_blog": False,
                "contact_email": None,
                "enrichment_time": 0
            }
        
        perf.start('enrichment')
        
        # Normalize domain
        if not domain.startswith('http'):
            domain = f"https://{domain}"
        
        enrichment_data = {
            "has_careers_page": False,
            "has_blog": False,
            "contact_email": None,
            "enrichment_time": 0
        }
        
        try:
            # Fetch homepage with 3-second timeout
            resp = self.session.get(domain, timeout=3, allow_redirects=True)
            if resp.status_code != 200:
                enrichment_data['enrichment_time'] = perf.end('enrichment')
                return enrichment_data
            
            html = resp.text.lower()
            
            # Check for careers/jobs page
            careers_patterns = ['/careers', '/jobs', '/join', '/hiring', '/work-with-us']
            enrichment_data['has_careers_page'] = any(pattern in html for pattern in careers_patterns)
            
            # Check for blog
            blog_patterns = ['/blog', '/news', '/articles', '/insights']
            enrichment_data['has_blog'] = any(pattern in html for pattern in blog_patterns)
            
            # Extract contact email
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, resp.text)
            if emails:
                # Filter out common non-contact emails
                valid_emails = [e for e in emails if not any(
                    x in e.lower() for x in ['noreply', 'no-reply', 'example', 'test']
                )]
                if valid_emails:
                    enrichment_data['contact_email'] = valid_emails[0]
            
        except requests.Timeout:
            logger.warning(f"Timeout enriching {domain}")
        except Exception as e:
            logger.warning(f"Error enriching {domain}: {e}")
        
        enrichment_data['enrichment_time'] = perf.end('enrichment')
        return enrichment_data

    def compute_hash(self, data: dict) -> str:
        """Compute SHA256 hash of snapshot data."""
        payload = json.dumps(data, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:32]

    def save_snapshot(self, db_company_id: int, detail_data: dict, perf: PerformanceTracker):
        """Save to company_snapshots if data changed."""
        perf.start('db_write')
        
        conn = psycopg2.connect(NEON_DATABASE_URL)
        cur = conn.cursor()
        
        data = {
            "batch": detail_data.get("batch"),
            "stage": detail_data.get("stage"),
            "description": detail_data.get("description"),
            "location": detail_data.get("location"),
            "tags": detail_data.get("tags", [])
        }
        
        data_hash = self.compute_hash(data)
        
        # Check if latest snapshot has same hash
        cur.execute("""
            SELECT data_hash FROM company_snapshots 
            WHERE company_id = %s 
            ORDER BY scraped_at DESC LIMIT 1
        """, (db_company_id,))
        latest_hash = cur.fetchone()
        
        changed = False
        if latest_hash and latest_hash[0] == data_hash:
            logger.info("  ➜ No change detected")
            self.stats['unchanged_companies'] += 1
        else:
            # Insert new snapshot
            cur.execute("""
                INSERT INTO company_snapshots 
                (company_id, batch, stage, description, location, tags, employee_range, scraped_at, data_hash)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, NOW(), %s)
            """, (
                db_company_id, 
                data["batch"], 
                data["stage"], 
                data["description"], 
                data["location"], 
                json.dumps(data["tags"]),
                detail_data.get("employee_range"),
                data_hash
            ))
            
            conn.commit()
            logger.info("  ✓ New snapshot saved")
            
            if latest_hash:
                self.stats['updated_companies'] += 1
            else:
                self.stats['new_companies'] += 1
            
            changed = True
        
        db_write_time = perf.end('db_write')
        
        cur.close()
        conn.close()
        
        return changed, db_write_time

    def save_web_enrichment(self, db_company_id: int, enrichment_data: dict):
        """Save website enrichment data."""
        conn = psycopg2.connect(NEON_DATABASE_URL)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO company_web_enrichment 
            (company_id, has_careers_page, has_blog, contact_email, scraped_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (company_id) DO UPDATE SET
                has_careers_page = EXCLUDED.has_careers_page,
                has_blog = EXCLUDED.has_blog,
                contact_email = EXCLUDED.contact_email,
                scraped_at = NOW()
        """, (
            db_company_id,
            enrichment_data['has_careers_page'],
            enrichment_data['has_blog'],
            enrichment_data['contact_email']
        ))
        
        conn.commit()
        cur.close()
        conn.close()

    def log_scrape_run(self):
        """Log scraping metrics to database."""
        duration = (datetime.now() - self.stats['start_time']).total_seconds()
        avg_time = (
            sum(p['total_time'] for p in self.stats['performance_logs']) / 
            len(self.stats['performance_logs'])
        ) if self.stats['performance_logs'] else 0
        
        # Print summary
        print("\n" + "="*70)
        print("SCRAPING COMPLETED - FINAL METRICS")
        print("="*70)
        print(f"Total Companies Processed:    {self.stats['total_processed']}")
        print(f"New Companies Added:          {self.stats['new_companies']}")
        print(f"Updated Companies:            {self.stats['updated_companies']}")
        print(f"Unchanged Companies:          {self.stats['unchanged_companies']}")
        print(f"Failed Companies:             {self.stats['failed_companies']}")
        print(f"Average Time per Company:     {avg_time:.2f}ms")
        print(f"Slowest Company:              {self.stats['slowest_company']['name']}")
        print(f"Slowest Company Time:         {self.stats['slowest_company']['time']:.2f}ms")
        print(f"Total Runtime:                {duration:.2f}s")
        print("="*70 + "\n")
        
        logger.info(f"Scraping completed in {duration:.2f}s")
        
        # Save to database
        try:
            conn = psycopg2.connect(NEON_DATABASE_URL)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO scrape_runs 
                (started_at, ended_at, total_companies, new_companies, updated_companies, 
                 unchanged_companies, failed_companies, avg_time_per_company_ms,
                 slowest_company_name, slowest_company_time_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                self.stats['start_time'],
                datetime.now(),
                self.stats['total_processed'],
                self.stats['new_companies'],
                self.stats['updated_companies'],
                self.stats['unchanged_companies'],
                self.stats['failed_companies'],
                avg_time,
                self.stats['slowest_company']['name'],
                self.stats['slowest_company']['time']
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            logger.info("✓ Metrics saved to scrape_runs table")
        except Exception as e:
            logger.error(f"Failed to save scrape run metrics: {e}")

    def run(self, limit=None):
        """Run the detail scraper with full performance tracking."""
        print("\n" + "="*70)
        print("YC COMPANIES DETAIL SCRAPER - Production Mode")
        print("="*70 + "\n")
        
        companies = self.get_companies_from_db()
        total = len(companies)
        
        if limit:
            companies = companies[:limit]
            logger.info(f"Found {total} companies, processing first {limit}")
        else:
            logger.info(f"Found {total} companies to scrape")
        
        print()
        
        for i, company in enumerate(companies, 1):
            perf = PerformanceTracker()
            company_start_time = time.time()
            
            print(f"[{i}/{len(companies)}] Processing: {company['name'][:40]}...")
            logger.info(f"Scraping company {i}/{len(companies)}: {company['slug']}")
            
            self.stats['total_processed'] += 1
            
            try:
                # Step 1: Scrape company detail page
                detail = self.scrape_company_detail(company['slug'], perf)
                
                if not detail:
                    logger.error(f"  ❌ Failed to scrape {company['slug']}")
                    self.stats['failed_companies'] += 1
                    continue
                
                # Step 2: Save snapshot (with data hash comparison)
                changed, db_write_time = self.save_snapshot(company['db_id'], detail, perf)
                
                # Step 3: Get domain for enrichment
                conn = psycopg2.connect(NEON_DATABASE_URL)
                cur = conn.cursor()
                cur.execute("SELECT domain FROM companies WHERE id = %s", (company['db_id'],))
                domain_row = cur.fetchone()
                domain = domain_row[0] if domain_row else None
                cur.close()
                conn.close()
                
                # Step 4: Website enrichment
                enrichment = self.enrich_from_website(domain, perf)
                self.save_web_enrichment(company['db_id'], enrichment)
                
                # Calculate total time for this company
                company_total_time = (time.time() - company_start_time) * 1000  # ms
                
                # Track performance
                performance_log = {
                    'company': company['name'],
                    'slug': company['slug'],
                    'index_fetch_time': detail.get('index_fetch_time', 0),
                    'html_parse_time': detail.get('html_parse_time', 0),
                    'db_write_time': db_write_time,
                    'enrichment_time': enrichment['enrichment_time'],
                    'total_time': company_total_time
                }
                self.stats['performance_logs'].append(performance_log)
                
                # Track slowest company
                if company_total_time > self.stats['slowest_company']['time']:
                    self.stats['slowest_company'] = {
                        'name': company['name'],
                        'time': company_total_time
                    }
                
                # Log detailed performance for this company
                logger.info(f"  Performance: Index={detail.get('index_fetch_time', 0):.0f}ms, "
                           f"Parse={detail.get('html_parse_time', 0):.0f}ms, "
                           f"DB={db_write_time:.0f}ms, "
                           f"Enrich={enrichment['enrichment_time']:.0f}ms, "
                           f"Total={company_total_time:.0f}ms")
                
                print(f"  ✓ Completed in {company_total_time:.0f}ms")
                
            except Exception as e:
                logger.error(f"  ❌ Error processing {company['slug']}: {e}")
                self.stats['failed_companies'] += 1
            
            # Respectful rate limiting
            time.sleep(0.5)
        
        # Log final metrics
        self.log_scrape_run()
        
        # Print top 5 slowest companies
        if self.stats['performance_logs']:
            print("\n" + "="*70)
            print("TOP 5 SLOWEST COMPANIES")
            print("="*70)
            sorted_logs = sorted(self.stats['performance_logs'], 
                               key=lambda x: x['total_time'], reverse=True)[:5]
            for idx, log in enumerate(sorted_logs, 1):
                print(f"{idx}. {log['company'][:40]}")
                print(f"   Total: {log['total_time']:.0f}ms | "
                      f"Fetch: {log['index_fetch_time']:.0f}ms | "
                      f"Parse: {log['html_parse_time']:.0f}ms | "
                      f"DB: {log['db_write_time']:.0f}ms | "
                      f"Enrich: {log['enrichment_time']:.0f}ms")
            print("="*70 + "\n")


if __name__ == "__main__":
    scraper = DetailScraper()
    
    # Run scraper
    # Set limit for testing (e.g., limit=10), remove limit to scrape all
    scraper.run(limit=10)  # ← Change to scraper.run() for full scrape
    
    print("\n✓ Scraping complete! Check scraper.log for detailed logs.")
