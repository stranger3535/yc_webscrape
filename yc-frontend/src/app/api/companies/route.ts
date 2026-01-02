import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const page = Math.max(1, parseInt(searchParams.get('page') || '1', 10));
    const limit = Math.min(50, Math.max(5, parseInt(searchParams.get('limit') || '20', 10)));
    const offset = (page - 1) * limit;
    const search = (searchParams.get('search') || '').trim();

    // Count total
    const countResult = await query('SELECT COUNT(*) as count FROM companies WHERE is_active = TRUE');
    const total = parseInt(countResult.rows[0].count as string);
    const totalPages = Math.ceil(total / limit);

    // Build query - JOIN with latest snapshot
    let whereClause = 'c.is_active = TRUE';
    const params: (string | number)[] = [];

    if (search) {
      params.push(`%${search}%`);
      whereClause += ` AND (c.name ILIKE $${params.length} OR s.description ILIKE $${params.length})`;
    }

    params.push(limit);
    params.push(offset);

    const companiesResult = await query(
      `SELECT 
        c.id,
        c.yc_company_id,
        c.name,
        c.domain as website,
        s.description,
        s.location,
        s.tags,
        s.stage,
        c.first_seen_at as created_at
      FROM companies c
      LEFT JOIN company_snapshots s ON c.id = s.company_id
      WHERE ${whereClause}
      ORDER BY c.id DESC 
      LIMIT $${params.length - 1} 
      OFFSET $${params.length}`,
      params
    );

    return NextResponse.json({
      companies: companiesResult.rows || [],
      pagination: { page, limit, total, totalPages }
    });

  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch companies', details: String(error) },
      { status: 500 }
    );
  }
}
