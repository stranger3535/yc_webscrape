'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, Calendar, MapPin, Users, Tag } from 'lucide-react';
import Link from 'next/link';

interface Company {
  id: number;
  yc_company_id: string;
  name: string;
  domain: string;
  first_seen_at: string;
}

interface Snapshot {
  id: number;
  batch: string;
  stage: string;
  description: string;
  location: string;
  tags: string[];
  employee_range: string;
  scraped_at: string;
}

interface Enrichment {
  has_careers_page: boolean;
  has_blog: boolean;
  contact_email: string;
}

interface CompanyDetail {
  company: Company;
  snapshots: Snapshot[];
  enrichment: Enrichment;
}

export default function CompanyDetail({ params }: { params: { id: string } }) {
  const [data, setData] = useState<CompanyDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/companies/${params.id}`)
      .then(res => res.json())
      .then(setData)
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) return <div className="flex justify-center items-center h-screen">Loading...</div>;
  if (!data) return <div className="flex justify-center items-center h-screen">Not found</div>;

  const company = data.company;
  const latest = data.snapshots[0];
  const enrichment = data.enrichment;

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <Link href="/" className="flex items-center gap-2 text-blue-600 hover:underline mb-4">
            <ArrowLeft className="w-4 h-4" />
            Back to Companies
          </Link>
          <h1 className="text-4xl font-bold text-blue-600">{company.name}</h1>
          <p className="text-gray-600 mt-2">{latest?.description || 'No description'}</p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        {/* Company Info */}
        <div className="bg-white p-8 rounded-lg shadow space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-gray-600 text-sm">Website</p>
              {company.domain ? (
                <a href={`https://${company.domain}`} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline font-medium">
                  {company.domain}
                </a>
              ) : (
                <p className="text-gray-500">N/A</p>
              )}
            </div>

            <div>
              <p className="text-gray-600 text-sm">Stage</p>
              <p className="text-lg font-bold text-blue-600">{latest?.stage || 'Unknown'}</p>
            </div>

            <div>
              <p className="text-gray-600 text-sm">Batch</p>
              <p className="text-lg font-bold">{latest?.batch || 'Unknown'}</p>
            </div>

            <div>
              <p className="text-gray-600 text-sm">Location</p>
              <p className="text-lg font-bold">{latest?.location || 'Unknown'}</p>
            </div>

            <div>
              <p className="text-gray-600 text-sm">Employee Range</p>
              <p className="text-lg font-bold">{latest?.employee_range || 'N/A'}</p>
            </div>

            <div>
              <p className="text-gray-600 text-sm">First Seen</p>
              <p className="text-lg font-bold">{new Date(company.first_seen_at).toLocaleDateString()}</p>
            </div>
          </div>

          {/* Website Enrichment */}
          {enrichment && (
            <div className="border-t pt-6">
              <h3 className="text-xl font-bold mb-4">Website Features</h3>
              <div className="space-y-2">
                <p className={enrichment.has_careers_page ? 'text-green-600' : 'text-gray-500'}>
                  {enrichment.has_careers_page ? '✓' : '✗'} Careers page
                </p>
                <p className={enrichment.has_blog ? 'text-green-600' : 'text-gray-500'}>
                  {enrichment.has_blog ? '✓' : '✗'} Blog
                </p>
                {enrichment.contact_email && (
                  <p className="text-green-600">
                    ✓ Contact: {enrichment.contact_email}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Tags */}
        {latest?.tags && (
          <div className="bg-white p-8 rounded-lg shadow">
            <h3 className="text-xl font-bold mb-4">Tags</h3>
            <div className="flex flex-wrap gap-2">
              {(Array.isArray(latest.tags) ? latest.tags : JSON.parse(latest.tags || '[]')).map((tag: string) => (
                <span key={tag} className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Snapshot History */}
        <div className="bg-white p-8 rounded-lg shadow">
          <h3 className="text-xl font-bold mb-4">History ({data.snapshots.length} snapshots)</h3>
          <div className="space-y-4">
            {data.snapshots.map((snapshot, idx) => (
              <div key={snapshot.id} className="border-l-4 border-blue-500 pl-4 py-2">
                <p className="text-gray-600 text-sm">
                  {new Date(snapshot.scraped_at).toLocaleString()}
                </p>
                <p className="font-medium">{snapshot.stage} • {snapshot.batch}</p>
                {idx > 0 && (
                  <p className="text-sm text-gray-500 mt-1">
                    Changed from: {data.snapshots[idx - 1].stage}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
