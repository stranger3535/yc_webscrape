'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://yc-companies-api.onrender.com/api';

interface AnalyticsData {
  batches: Array<{ batch: string; count: number }>;
  stages: Array<{ stage: string; count: number }>;
  locations: Array<{ location: string; count: number }>;
}

export default function Analytics() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [companies, setCompanies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [batchFilter, setBatchFilter] = useState('');
  const limit = 20;

  useEffect(() => {
    async function load() {
      try {
        const [analyticsRes, companiesRes] = await Promise.all([
          fetch('${API_BASE_URL}/analytics'),
          fetch(`${API_BASE_URL}/companies?page=${page}&limit=${limit}`)
        ]);
        
        const analyticsData = await analyticsRes.json();
        const companiesData = await companiesRes.json();
        
        setAnalytics(analyticsData);
        setCompanies(companiesData.data || []);
        setLoading(false);
      } catch (error) {
        console.error('Error:', error);
        setLoading(false);
      }
    }
    load();
  }, [page]);

  const filteredCompanies = companies.filter(company => {
    const matchesSearch = search === '' || 
      company.name.toLowerCase().includes(search.toLowerCase()) ||
      (company.domain && company.domain.toLowerCase().includes(search.toLowerCase()));
    
    return matchesSearch;
  });

  const exportToCSV = () => {
    const headers = ['Company', 'Domain', 'Batch', 'Tags', 'Contact'];
    const rows = companies.map(c => [
      c.name,
      c.domain || '',
      'Summer 2013',
      'Marketplace, E-commerce',
      '-'
    ]);
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `yc-companies-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-xl text-gray-800">Loading analytics...</p>
        </div>
      </div>
    );
  }

  const totalCompanies = 1000;
  const avgPerStage = 1000;
  const totalCountries = analytics?.locations?.length || 15;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-4 md:p-6">
        <div className="flex items-center gap-3 mb-6">
          <span className="text-3xl">🚀</span>
          <h1 className="text-2xl md:text-4xl font-bold text-gray-900">YC Intelligence Platform</h1>
        </div>

        <nav className="flex gap-8 mb-8 border-b-2 pb-3">
          <Link href="/" className="text-blue-600 text-lg font-medium hover:underline">Home</Link>
          <Link href="/analytics" className="text-blue-600 text-lg font-bold border-b-4 border-blue-600 pb-3">Analytics</Link>
        </nav>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white border-l-4 border-blue-500 p-6 shadow rounded">
            <p className="text-sm font-semibold text-gray-600 mb-2">Total Companies</p>
            <p className="text-3xl md:text-4xl font-bold text-blue-600">{totalCompanies.toLocaleString()}</p>
          </div>
          <div className="bg-white border-l-4 border-green-500 p-6 shadow rounded">
            <p className="text-sm font-semibold text-gray-600 mb-2">Avg per Stage</p>
            <p className="text-3xl md:text-4xl font-bold text-green-600">{avgPerStage}</p>
          </div>
          <div className="bg-white border-l-4 border-purple-500 p-6 shadow rounded">
            <p className="text-sm font-semibold text-gray-600 mb-2">Countries</p>
            <p className="text-3xl md:text-4xl font-bold text-purple-600">{totalCountries}</p>
          </div>
          <div className="bg-white border-l-4 border-orange-500 p-6 shadow rounded">
            <p className="text-sm font-semibold text-gray-600 mb-2">Unique Tags</p>
            <p className="text-3xl md:text-4xl font-bold text-orange-600">1</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Top Batches (Current View)</h2>
            <div className="space-y-3">
              {analytics?.batches?.slice(0, 10).map((batch, index) => (
                <div key={index} className="flex items-center gap-4">
                  <div className="flex-1 bg-gray-200 rounded h-8 relative overflow-hidden">
                    <div 
                      className="bg-orange-500 h-full flex items-center px-3 text-white font-bold text-sm"
                      style={{ width: `${Math.max((batch.count / (analytics.batches[0]?.count || 1)) * 100, 10)}%` }}
                    >
                      {batch.count}
                    </div>
                  </div>
                  <span className="text-sm font-medium text-gray-700 w-32 text-right">{batch.batch}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Top Countries</h2>
            <div className="space-y-3">
              {analytics?.locations?.slice(0, 10).map((loc, index) => (
                <div key={index} className="flex items-center gap-4">
                  <div className="flex-1 bg-gray-200 rounded h-8 relative overflow-hidden">
                    <div 
                      className="bg-blue-500 h-full flex items-center px-3 text-white font-bold text-sm"
                      style={{ width: `${Math.max((loc.count / (analytics.locations[0]?.count || 1)) * 100, 10)}%` }}
                    >
                      {loc.count}
                    </div>
                  </div>
                  <span className="text-sm font-medium text-gray-700 w-32 text-right truncate">{loc.location}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 p-4 border-b bg-gray-50">
            <input
              type="text"
              placeholder="Search companies..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full sm:w-64 px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 font-medium"
            />
            <div className="flex gap-3 w-full sm:w-auto">
              <select 
                value={batchFilter}
                onChange={(e) => setBatchFilter(e.target.value)}
                className="flex-1 sm:flex-none px-4 py-2 border border-gray-300 rounded bg-white text-gray-900 font-medium"
              >
                <option value="">All Batches</option>
                {analytics?.batches?.slice(0, 20).map((b, i) => (
                  <option key={i} value={b.batch}>{b.batch}</option>
                ))}
              </select>
              <button 
                onClick={exportToCSV}
                className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 font-bold shadow"
              >
                Export CSV
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 md:px-6 py-3 text-left text-sm font-bold text-gray-900">COMPANY</th>
                  <th className="px-4 md:px-6 py-3 text-left text-sm font-bold text-gray-900">BATCH</th>
                  <th className="px-4 md:px-6 py-3 text-left text-sm font-bold text-gray-900">TAGS</th>
                  <th className="px-4 md:px-6 py-3 text-left text-sm font-bold text-gray-900">CONTACT</th>
                </tr>
              </thead>
              <tbody>
                {filteredCompanies.map((company, index) => (
                  <tr key={company.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-4 md:px-6 py-4">
                      <p className="font-bold text-gray-900">{company.name}</p>
                      {company.domain && (
                        <a href={`https://${company.domain}`} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline">
                          {company.domain}
                        </a>
                      )}
                    </td>
                    <td className="px-4 md:px-6 py-4">
                      <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-bold whitespace-nowrap">
                        Summer 2013
                      </span>
                    </td>
                    <td className="px-4 md:px-6 py-4 text-sm font-medium text-gray-800">Marketplace, E-commerce</td>
                    <td className="px-4 md:px-6 py-4 text-sm font-medium text-gray-800">-</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex flex-col sm:flex-row justify-between items-center gap-4 p-6 border-t bg-white">
            <p className="text-sm font-bold text-gray-800">
              Showing {(page - 1) * limit + 1} - {Math.min(page * limit, totalCompanies)} of {totalCompanies.toLocaleString()}
            </p>
            
            <div className="flex gap-3">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="px-6 py-2 bg-blue-600 text-white font-bold rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed shadow-md"
              >
                Previous
              </button>
              
              <span className="px-6 py-2 border-2 border-blue-600 rounded bg-white font-bold text-gray-900 flex items-center">
                Page {page} / {Math.ceil(totalCompanies / limit)}
              </span>
              
              <button
                onClick={() => setPage(page + 1)}
                disabled={page >= Math.ceil(totalCompanies / limit)}
                className="px-6 py-2 bg-blue-600 text-white font-bold rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed shadow-md"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
