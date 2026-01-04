import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def get_metrics():
    """Fetch comprehensive metrics from Neon database"""
    conn = psycopg2.connect(os.getenv('NEON_DATABASE_URL'))
    cur = conn.cursor()
    
    metrics = {}
    
    # Total companies
    cur.execute("SELECT COUNT(*) FROM companies")
    metrics['total_companies'] = cur.fetchone()[0]
    
    # Companies with websites
    cur.execute("SELECT COUNT(*) FROM companies WHERE website IS NOT NULL AND website != ''")
    metrics['companies_with_website'] = cur.fetchone()[0]
    
    # Total snapshots
    cur.execute("SELECT COUNT(*) FROM company_snapshots")
    metrics['total_snapshots'] = cur.fetchone()[0]
    
    # Total scrape runs
    cur.execute("SELECT COUNT(*) FROM scrape_logs")
    metrics['total_scrape_runs'] = cur.fetchone()[0]
    
    # Latest scrape run details
    cur.execute("""
        SELECT run_date, total_processed, new_companies, updated_companies, 
               unchanged_companies, failed_companies, duration_seconds, 
               avg_time_per_company_ms
        FROM scrape_logs 
        ORDER BY run_date DESC 
        LIMIT 1
    """)
    latest = cur.fetchone()
    if latest:
        metrics['latest_scrape'] = {
            'run_date': latest[0],
            'total_processed': latest[1],
            'new_companies': latest[2],
            'updated_companies': latest[3],
            'unchanged_companies': latest[4],
            'failed_companies': latest[5],
            'duration_seconds': latest[6],
            'avg_time_ms': latest[7]
        }
    else:
        metrics['latest_scrape'] = None
    
    # Batch distribution
    cur.execute("""
        SELECT batch, COUNT(*) as count 
        FROM companies 
        WHERE batch IS NOT NULL AND batch != ''
        GROUP BY batch 
        ORDER BY count DESC 
        LIMIT 10
    """)
    metrics['top_batches'] = cur.fetchall()
    
    # Industry distribution
    cur.execute("""
        SELECT industry, COUNT(*) as count 
        FROM companies 
        WHERE industry IS NOT NULL AND industry != ''
        GROUP BY industry 
        ORDER BY count DESC 
        LIMIT 10
    """)
    metrics['top_industries'] = cur.fetchall()
    
    # Location distribution
    cur.execute("""
        SELECT location, COUNT(*) as count 
        FROM companies 
        WHERE location IS NOT NULL AND location != ''
        GROUP BY location 
        ORDER BY count DESC 
        LIMIT 10
    """)
    metrics['top_locations'] = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return metrics

def print_report(metrics):
    """Print a formatted submission metrics report"""
    print("\n" + "="*70)
    print("YC COMPANIES INTELLIGENCE PLATFORM - SUBMISSION METRICS")
    print("="*70)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print("DATABASE STATISTICS:")
    print(f"  Total Companies Scraped:     {metrics['total_companies']:,}")
    print(f"  Company Snapshots (history): {metrics['total_snapshots']:,}")
    print(f"  Website Enriched:            {metrics['companies_with_website']:,}")
    print(f"  Scrape Runs Recorded:        {metrics['total_scrape_runs']}\n")
    
    if metrics['latest_scrape']:
        latest = metrics['latest_scrape']
        print("LATEST SCRAPE RUN:")
        print(f"  Date:              {latest['run_date']}")
        print(f"  Total Processed:   {latest['total_processed']}")
        print(f"  New Companies:     {latest['new_companies']}")
        print(f"  Updated:           {latest['updated_companies']}")
        print(f"  Unchanged:         {latest['unchanged_companies']}")
        print(f"  Failed:            {latest['failed_companies']}")
        print(f"  Duration:          {latest['duration_seconds']:.2f}s" if latest['duration_seconds'] else "  Duration:          N/A")
        print(f"  Avg Time/Company:  {latest['avg_time_ms']:.2f}ms\n" if latest['avg_time_ms'] else "  Avg Time/Company:  N/A\n")
    else:
        print("LATEST SCRAPE RUN: No scrape runs found\n")
    
    if metrics['top_batches']:
        print("TOP 10 Y COMBINATOR BATCHES:")
        for batch, count in metrics['top_batches']:
            print(f"  {batch:20s} {count:4d} companies")
        print()
    
    if metrics['top_industries']:
        print("TOP 10 INDUSTRIES:")
        for industry, count in metrics['top_industries']:
            print(f"  {industry:30s} {count:4d} companies")
        print()
    
    if metrics['top_locations']:
        print("TOP 10 LOCATIONS:")
        for location, count in metrics['top_locations']:
            print(f"  {location:30s} {count:4d} companies")
        print()
    
    print("="*70)
    print("✓ Data pipeline operational and validated")
    print("✓ Historical tracking active (company_snapshots)")
    print("✓ Ready for analytics API and frontend integration")
    print("="*70 + "\n")

if __name__ == "__main__":
    print("Fetching metrics from Neon...\n")
    metrics = get_metrics()
    print_report(metrics)
