'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

interface Stats {
  totalCompanies: number;
  byStage: { [key: string]: number };
  byCountry: { [key: string]: number };
  tagCloud: { name: string; count: number }[];
  byBatch: { [key: string]: number };
}

interface Company {
  id: number;
  name: string;
  stage: string;
  location: string;
  tags: string;
  website?: string;
}

export default function Analytics() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    fetchCompanies();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/analytics');
      const data = await res.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const fetchCompanies = async () => {
    try {
      const res = await fetch('/api/companies?page=1&limit=10');
      const data = await res.json();
      setCompanies(data.companies || []);
    } catch (error) {
      console.error('Failed to fetch companies:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="flex justify-center items-center h-screen">Loading...</div>;
  if (!stats) return <div className="flex justify-center items-center h-screen">No data</div>;

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6'];

  const stageCount = Object.keys(stats.byStage).length || 1;
  const avgPerStage = stageCount > 0 ? Math.round(stats.totalCompanies / stageCount) : 0;
  const countryCount = Object.keys(stats.byCountry).length;
  const tagCount = stats.tagCloud.length;

  const stageData = Object.entries(stats.byStage).map(([name, value]) => ({ name, value }));
  const countryData = Object.entries(stats.byCountry).slice(0, 10).map(([name, value]) => ({ name, value }));
  const tagData = stats.tagCloud.slice(0, 15);
  const batchData = Object.entries(stats.byBatch || {})
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 10);

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-4xl font-bold text-blue-600 mb-4">YC Intelligence Platform</h1>
          
          {/* Navigation */}
          <nav className="flex gap-6">
            <Link href="/" className="text-blue-600 font-medium hover:underline">
              Home
            </Link>
            <Link href="/analytics" className="text-blue-600 font-medium hover:underline">
              Analytics
            </Link>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-6 rounded-lg shadow border-l-4 border-blue-500">
            <p className="text-gray-600 text-sm">Total Companies</p>
            <p className="text-3xl font-bold text-blue-600">{stats.totalCompanies.toLocaleString()}</p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow border-l-4 border-green-500">
            <p className="text-gray-600 text-sm">Avg per Stage</p>
            <p className="text-3xl font-bold text-green-600">{isFinite(avgPerStage) ? avgPerStage : 'N/A'}</p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow border-l-4 border-purple-500">
            <p className="text-gray-600 text-sm">Countries</p>
            <p className="text-3xl font-bold text-purple-600">{countryCount}</p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow border-l-4 border-orange-500">
            <p className="text-gray-600 text-sm">Unique Tags</p>
            <p className="text-3xl font-bold text-orange-600">{tagCount}</p>
          </div>
        </div>

        {/* Top Batches Chart - NEW */}
        {batchData.length > 0 && (
          <div className="bg-white p-6 rounded-lg shadow mb-8">
            <h2 className="text-xl font-bold mb-4">Top Batches (Current View)</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={batchData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#FF8C00" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Stage Distribution */}
          {stageData.length > 0 ? (
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-bold mb-4">Companies by Stage</h2>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie 
                    data={stageData} 
                    cx="50%" 
                    cy="50%" 
                    labelLine={false} 
                    label={({ name, value }) => `${name}: ${value}`} 
                    outerRadius={80}
                  >
                    {stageData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-bold mb-4">Companies by Stage</h2>
              <div className="flex items-center justify-center h-72 text-gray-500">
                <p>No stage data available</p>
              </div>
            </div>
          )}

          {/* Top Countries */}
          {countryData.length > 0 ? (
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-bold mb-4">Top Countries</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={countryData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-bold mb-4">Top Countries</h2>
              <div className="flex items-center justify-center h-72 text-gray-500">
                <p>No location data available</p>
              </div>
            </div>
          )}

          {/* Top Tags */}
          {tagData.length > 0 ? (
            <div className="bg-white p-6 rounded-lg shadow lg:col-span-2">
              <h2 className="text-xl font-bold mb-4">Top Tags ({tagData.length})</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={tagData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#10B981" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="bg-white p-6 rounded-lg shadow lg:col-span-2">
              <h2 className="text-xl font-bold mb-4">Top Tags</h2>
              <div className="flex items-center justify-center h-72 text-gray-500">
                <p>No tags data available</p>
              </div>
            </div>
          )}
        </div>

        {/* Company Table - NEW */}
        {companies.length > 0 && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b">
              <h2 className="text-xl font-bold">Companies Sample</h2>
            </div>
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">COMPANY</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">BATCH</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">TAGS</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">CONTACT</th>
                </tr>
              </thead>
              <tbody>
                {companies.map((company) => (
                  <tr key={company.id} className="border-b hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm">
                      <Link href={`/companies/${company.id}`} className="text-blue-600 hover:underline font-medium">
                        {company.name}
                      </Link>
                      {company.website && (
                        <p className="text-xs text-gray-500">{company.website}</p>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-medium">
                        {company.stage || 'Unknown'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {company.tags 
                        ? (Array.isArray(company.tags) ? company.tags : JSON.parse(company.tags || '[]'))
                            .slice(0, 2)
                            .join(', ')
                        : '-'
                      }
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">-</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
