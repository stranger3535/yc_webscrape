import { NextResponse } from 'next/server';
import { query } from '@/lib/db';

export async function GET() {
  try {
    // Total companies
    const totalResult = await query('SELECT COUNT(*) as count FROM companies WHERE is_active = TRUE');
    const totalCompanies = parseInt(totalResult.rows[0].count as string);

    // By stage (get latest snapshot per company)
    const stageResult = await query(
      `WITH latest_snapshots AS (
        SELECT DISTINCT ON (company_id) company_id, stage, scraped_at
        FROM company_snapshots
        ORDER BY company_id, scraped_at DESC
      )
      SELECT s.stage, COUNT(c.id) as count 
      FROM companies c
      LEFT JOIN latest_snapshots s ON c.id = s.company_id
      WHERE c.is_active = TRUE AND s.stage IS NOT NULL
      GROUP BY s.stage 
      ORDER BY count DESC`
    );
    const byStage = Object.fromEntries(
      stageResult.rows.map((row: any) => [row.stage || 'Unknown', parseInt(row.count)])
    );

    // By batch - NEW
    const batchResult = await query(
      `WITH latest_snapshots AS (
        SELECT DISTINCT ON (company_id) company_id, batch, scraped_at
        FROM company_snapshots
        ORDER BY company_id, scraped_at DESC
      )
      SELECT s.batch, COUNT(c.id) as count 
      FROM companies c
      LEFT JOIN latest_snapshots s ON c.id = s.company_id
      WHERE c.is_active = TRUE AND s.batch IS NOT NULL
      GROUP BY s.batch 
      ORDER BY count DESC`
    );
    const byBatch = Object.fromEntries(
      batchResult.rows.map((row: any) => [row.batch || 'Unknown', parseInt(row.count)])
    );

    // By country
    const countryResult = await query(
      `WITH latest_snapshots AS (
        SELECT DISTINCT ON (company_id) company_id, location, scraped_at
        FROM company_snapshots
        ORDER BY company_id, scraped_at DESC
      )
      SELECT s.location, COUNT(c.id) as count 
      FROM companies c
      LEFT JOIN latest_snapshots s ON c.id = s.company_id
      WHERE c.is_active = TRUE AND s.location IS NOT NULL
      GROUP BY s.location 
      ORDER BY count DESC 
      LIMIT 20`
    );
    const byCountry = Object.fromEntries(
      countryResult.rows.map((row: any) => [row.location || 'Unknown', parseInt(row.count)])
    );

    // Top tags
    const tagsResult = await query(
      `WITH latest_snapshots AS (
        SELECT DISTINCT ON (company_id) company_id, tags, scraped_at
        FROM company_snapshots
        ORDER BY company_id, scraped_at DESC
      )
      SELECT s.tags, COUNT(c.id) as count 
      FROM companies c
      LEFT JOIN latest_snapshots s ON c.id = s.company_id
      WHERE c.is_active = TRUE AND s.tags IS NOT NULL
      GROUP BY s.tags 
      ORDER BY count DESC 
      LIMIT 30`
    );
    const tagCloud = tagsResult.rows.map((row: any) => ({
      name: row.tags || 'Unknown',
      count: parseInt(row.count)
    }));

    return NextResponse.json({
      totalCompanies,
      byStage,
      byBatch,
      byCountry,
      tagCloud
    });
  } catch (error) {
    console.error('Analytics Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch analytics', details: String(error) },
      { status: 500 }
    );
  }
}
