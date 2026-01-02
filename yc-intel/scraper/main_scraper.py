#!/usr/bin/env python3
"""
YC Companies Master Data Ingestion Pipeline

- Fetches YC companies from Algolia
- Normalizes and stores data in PostgreSQL
- Tracks historical changes via hashing
- Enriches company websites asynchronously
- Records operational scrape metrics
"""

import os
import time
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import psycopg2
import requests
import json
import hashlib
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from typing import Dict, List

# ------------------------------------------------------------------
# Configuration & Logging
# ------------------------------------------------------------------

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler("scraper.log", maxBytes=10 * 1024 * 1024, backupCount=5),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

ALGOLIA_URL = (
    "https://45bwzj1sgc-dsn.algolia.net/1/indexes/*/queries"
)
ALGOLIA_KEY = "f54e21fa3d794d0052b22b56683b9b3a"
ALGOLIA_APP_ID = "45BWZJ1SGC"


# ------------------------------------------------------------------
# Scraper Class
# ------------------------------------------------------------------

class YCScraper:
    def __init__(self):
        self.conn = psycopg2.connect(DATABASE_URL)
        self.cur = self.conn.cursor()

        self.metrics = {
            "total": 0,
            "new": 0,
            "updated": 0,
            "unchanged": 0,
            "failed": 0,
            "timings": [],
            "slowest": None,
            "slowest_time": 0.0,
        }

        self.scrape_run_id = None
        self.start_time = None

    # --------------------------------------------------------------
    # Scrape Run Tracking
    # --------------------------------------------------------------

    def start_scrape_run(self):
        self.start_time = time.time()
        self.cur.execute(
            """
            INSERT INTO scrape_runs (started_at)
            VALUES (NOW())
            RETURNING id
            """
        )
        self.scrape_run_id = self.cur.fetchone()[0]
        self.conn.commit()
        logger.info(f"Started scrape run #{self.scrape_run_id}")

    def end_scrape_run(self):
        runtime = time.time() - self.start_time
        avg_time = (
            sum(self.metrics["timings"]) / len(self.metrics["timings"])
            if self.metrics["timings"]
            else 0
        )

        self.cur.execute(
            """
            UPDATE scrape_runs
            SET ended_at = NOW(),
                total_companies = %s,
                new_companies = %s,
                updated_companies = %s,
                unchanged_companies = %s,
                failed_companies = %s,
                avg_time_per_company_ms = %s
            WHERE id = %s
            """,
            (
                self.metrics["total"],
                self.metrics["new"],
                self.metrics["updated"],
                self.metrics["unchanged"],
                self.metrics["failed"],
                round(avg_time * 1000, 2),
                self.scrape_run_id,
            ),
        )
        self.conn.commit()
        logger.info(f"Scrape run #{self.scrape_run_id} completed in {runtime:.2f}s")

    # --------------------------------------------------------------
    # Algolia List Fetch
    # --------------------------------------------------------------

    def scrape_list(self) -> List[Dict]:
        logger.info("Fetching company list from Algolia")
        companies = []
        page = 0

        headers = {
            "X-Algolia-API-Key": ALGOLIA_KEY,
            "X-Algolia-Application-Id": ALGOLIA_APP_ID,
        }

        while True:
            payload = {
                "requests": [
                    {
                        "indexName": "Company",
                        "query": "",
                        "page": page,
                        "hitsPerPage": 100,
                        "filters": "isAccredited:true",
                    }
                ]
            }

            try:
                resp = requests.post(
                    ALGOLIA_URL, json=payload, headers=headers, timeout=10
                )
                resp.raise_for_status()
                data = resp.json()

                hits = data["results"][0]["hits"]
                if not hits:
                    break

                companies.extend(hits)
                page += 1
                logger.info(f"Fetched page {page} ({len(hits)} companies)")

            except Exception as e:
                logger.error(f"Algolia fetch failed: {e}")
                break

        logger.info(f"Total companies discovered: {len(companies)}")
        return companies

    # --------------------------------------------------------------
    # Company Normalization
    # --------------------------------------------------------------

    def scrape_detail(self, company: Dict) -> Dict | None:
        start = time.time()
        name = company.get("name", "Unknown")

        try:
            website = company.get("website", "") or ""
            domain = (
                website.replace("https://", "")
                .replace("http://", "")
                .strip("/")
            )

            timing = time.time() - start
            self.metrics["timings"].append(timing)

            if timing > self.metrics["slowest_time"]:
                self.metrics["slowest"] = name
                self.metrics["slowest_time"] = timing

            return {
                "batch": company.get("batch"),
                "stage": company.get("stage", "Active"),
                "description": company.get("short_description"),
                "location": company.get("location"),
                "tags": json.dumps(company.get("tags", [])),
                "employee_range": company.get("employee_size"),
                "website": domain,
            }

        except Exception as e:
            logger.error(f"Detail processing failed for {name}: {e}")
            self.metrics["failed"] += 1
            return None

    # --------------------------------------------------------------
    # Database Persistence
    # --------------------------------------------------------------

    def save_company(self, company: Dict, detail: Dict) -> str:
        try:
            yc_id = company.get("id")
            name = company.get("name")

            self.cur.execute(
                "SELECT id FROM companies WHERE yc_company_id = %s",
                (yc_id,),
            )
            row = self.cur.fetchone()

            snapshot_payload = json.dumps(
                {
                    "batch": detail["batch"],
                    "stage": detail["stage"],
                    "description": detail["description"],
                    "location": detail["location"],
                    "tags": detail["tags"],
                    "employee_range": detail["employee_range"],
                },
                sort_keys=True,
            )
            data_hash = hashlib.sha256(snapshot_payload.encode()).hexdigest()

            if row:
                company_id = row[0]

                self.cur.execute(
                    """
                    SELECT data_hash
                    FROM company_snapshots
                    WHERE company_id = %s
                    ORDER BY scraped_at DESC
                    LIMIT 1
                    """,
                    (company_id,),
                )
                last = self.cur.fetchone()

                if last and last[0] == data_hash:
                    self.metrics["unchanged"] += 1
                    return "unchanged"

                self.cur.execute(
                    """
                    INSERT INTO company_snapshots
                    (company_id, batch, stage, description, location,
                     tags, employee_range, data_hash, scraped_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                    """,
                    (
                        company_id,
                        detail["batch"],
                        detail["stage"],
                        detail["description"],
                        detail["location"],
                        detail["tags"],
                        detail["employee_range"],
                        data_hash,
                    ),
                )

                self.cur.execute(
                    "UPDATE companies SET last_seen_at = NOW() WHERE id = %s",
                    (company_id,),
                )

                self.metrics["updated"] += 1
                return "updated"

            self.cur.execute(
                """
                INSERT INTO companies
                (yc_company_id, name, domain, first_seen_at, last_seen_at, is_active)
                VALUES (%s,%s,%s,NOW(),NOW(),TRUE)
                RETURNING id
                """,
                (yc_id, name, detail["website"]),
            )
            company_id = self.cur.fetchone()[0]

            self.cur.execute(
                """
                INSERT INTO company_snapshots
                (company_id, batch, stage, description, location,
                 tags, employee_range, data_hash, scraped_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                """,
                (
                    company_id,
                    detail["batch"],
                    detail["stage"],
                    detail["description"],
                    detail["location"],
                    detail["tags"],
                    detail["employee_range"],
                    data_hash,
                ),
            )

            self.metrics["new"] += 1
            return "new"

        except Exception as e:
            logger.error(f"DB save failed for {company.get('name')}: {e}")
            self.metrics["failed"] += 1
            return "failed"

        finally:
            self.conn.commit()

    # --------------------------------------------------------------
    # Website Enrichment
    # --------------------------------------------------------------

    async def enrich_website(self, session: aiohttp.ClientSession, domain: str) -> Dict:
        if not domain:
            return {"has_careers": False, "has_blog": False, "email": None}

        try:
            async with session.get(f"https://{domain}", timeout=3) as resp:
                if resp.status != 200:
                    return {"has_careers": False, "has_blog": False, "email": None}

                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")

                has_careers = bool(
                    soup.find("a", href=re.compile(r"(career|job)", re.I))
                )
                has_blog = bool(
                    soup.find("a", href=re.compile(r"blog", re.I))
                )

                emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", html)
                email = emails[0] if emails else None

                return {
                    "has_careers": has_careers,
                    "has_blog": has_blog,
                    "email": email,
                }

        except Exception:
            return {"has_careers": False, "has_blog": False, "email": None}

    async def enrich_all_companies(self):
        logger.info("Starting website enrichment")

        self.cur.execute(
            "SELECT id, domain FROM companies WHERE domain IS NOT NULL AND is_active"
        )
        companies = self.cur.fetchall()

        connector = aiohttp.TCPConnector(limit=20)
        async with aiohttp.ClientSession(connector=connector) as session:
            for company_id, domain in companies:
                result = await self.enrich_website(session, domain)

                try:
                    self.cur.execute(
                        """
                        INSERT INTO company_web_enrichment
                        (company_id, has_careers_page, has_blog, contact_email, scraped_at)
                        VALUES (%s,%s,%s,%s,NOW())
                        ON CONFLICT (company_id)
                        DO UPDATE SET
                            has_careers_page = EXCLUDED.has_careers_page,
                            has_blog = EXCLUDED.has_blog,
                            contact_email = EXCLUDED.contact_email,
                            scraped_at = NOW()
                        """,
                        (
                            company_id,
                            result["has_careers"],
                            result["has_blog"],
                            result["email"],
                        ),
                    )
                    self.conn.commit()
                except Exception as e:
                    logger.error(f"Enrichment failed for {company_id}: {e}")

        logger.info(f"Website enrichment complete ({len(companies)} companies)")

    # --------------------------------------------------------------
    # Reporting
    # --------------------------------------------------------------

    def print_summary(self):
        """Print final metrics"""
        if not self.metrics["timings"]:
            avg_time = min_time = max_time = 0
        else:
            avg_time = sum(self.metrics["timings"]) / len(self.metrics["timings"])
            min_time = min(self.metrics["timings"])
            max_time = max(self.metrics["timings"])

        logger.info("=" * 70)
        logger.info("SCRAPE SUMMARY - PRODUCTION METRICS")
        logger.info("=" * 70)
        logger.info(f"Total Companies Processed: {self.metrics['total']}")
        logger.info(f"New Companies Added:       {self.metrics['new']}")
        logger.info(f"Updated Companies:         {self.metrics['updated']}")
        logger.info(f"Unchanged Companies:       {self.metrics['unchanged']}")
        logger.info(f"Failed Companies:          {self.metrics['failed']}")
        logger.info("-" * 70)
        logger.info(f"Average Time per Company:  {avg_time:.3f}s")
        logger.info(f"Min Time per Company:      {min_time:.3f}s")
        logger.info(f"Max Time per Company:      {max_time:.3f}s")

        if self.metrics["slowest"]:
            logger.info(
                f"Slowest Company: {self.metrics['slowest']} "
                f"({self.metrics['slowest_time']:.3f}s)"
            )
        logger.info("=" * 70)

    # --------------------------------------------------------------
    # Orchestrator
    # --------------------------------------------------------------

    def run(self):
        self.start_scrape_run()

        try:
            companies = self.scrape_list()
            self.metrics["total"] = len(companies)

            for idx, company in enumerate(companies, start=1):
                if idx % 100 == 0:
                    logger.info(f"Progress: {idx}/{len(companies)}")

                detail = self.scrape_detail(company)
                if detail:
                    self.save_company(company, detail)

                time.sleep(0.1)

            asyncio.run(self.enrich_all_companies())
            self.end_scrape_run()
            self.print_summary()

        except Exception as e:
            logger.error("Fatal pipeline failure", exc_info=True)

        finally:
            self.cur.close()
            self.conn.close()


# ------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("YC Companies Master Scraper Started")
    scraper = YCScraper()
    scraper.run()
    logger.info("YC Companies Master Scraper Finished")
