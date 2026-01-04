'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Search, MapPin, TrendingUp } from 'lucide-react';

interface Company {
  id: number;
  name: string;
  slug: string;
  domain: string;
  is_active: boolean;
}

export default function Home() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const limit = 10;

  useEffect(() => {
    fetchCompanies();
  }, [page, search]);

  const fetchCompanies = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
        ...(search ? { search } : {}),
      });

      const res = await fetch(`/api/companies?${params}`);
      if (!res.ok) throw new Error('Failed to fetch');

      const result = await res.json();
      setCompanies(result.data || []);
    } catch (error) {
      console.error('Failed to fetch:', error);
      setCompanies([]);
    } finally {
      setLoading(false);
    }
  };

  const totalCompanies = 1000;

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <header className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <h1 className="text-4xl font-bold text-blue-600">YC Companies</h1>
          <p className="text-gray-600 mt-2">
            Explore {totalCompanies.toLocaleString()} Y Combinator funded startups
          </p>

          <nav className="flex gap-6 mt-4">
            <Link href="/" className="text-blue-600 font-medium border-b-2 border-blue-600">
              Home
            </Link>
            <Link href="/analytics" className="text-blue-600 font-medium hover:underline">
              Analytics
            </Link>
          </nav>
        </div>
      </header>

      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4 space-y-4">
          <div className="flex gap-4 flex-wrap">
            <div className="flex-1 min-w-64">
              <div className="relative">
                <Search className="absolute left-3 top-3 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search companies..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                  }}
                  className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          <p className="text-sm font-semibold text-gray-700">
            Showing {((page - 1) * limit + 1)} - {Math.min(page * limit, totalCompanies)} of {totalCompanies.toLocaleString()}
          </p>
        </div>
      </div>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading companies...</p>
          </div>
        ) : companies.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 text-lg">No companies found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {companies.map((company) => (
              <Link
                key={company.id}
                href={`/companies/${company.id}`}
                className="bg-white rounded-lg shadow hover:shadow-lg transition p-6 border border-gray-100 block"
              >
                <h3 className="text-xl font-bold text-blue-600 mb-2">
                  {company.name}
                </h3>

                <p className="text-sm text-gray-600 mb-3">
                  Y Combinator Portfolio Company
                </p>

                <div className="space-y-2 text-sm mb-4">
                  <div className="flex items-center gap-2 text-gray-700">
                    <TrendingUp className="w-4 h-4" />
                    <span className="font-medium">
                      {company.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-700">
                    <MapPin className="w-4 h-4" />
                    <span>San Francisco, CA</span>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 mb-4">
                  <span className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded font-semibold">
                    Technology
                  </span>
                  <span className="bg-green-100 text-green-700 text-xs px-2 py-1 rounded font-semibold">
                    B2B
                  </span>
                </div>

                {company.domain && (
                  <a
                    href={`https://${company.domain}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="text-blue-600 hover:underline text-sm font-medium"
                  >
                    Visit Website →
                  </a>
                )}
              </Link>
            ))}
          </div>
        )}

        <div className="flex justify-center gap-3 mt-12">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="px-6 py-2 bg-blue-600 text-white font-bold rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed shadow"
          >
            Previous
          </button>

          <span className="px-6 py-2 border-2 border-blue-600 rounded bg-white font-bold text-gray-900 flex items-center">
            Page {page} / {Math.ceil(totalCompanies / limit)}
          </span>

          <button
            onClick={() => setPage(page + 1)}
            disabled={page >= Math.ceil(totalCompanies / limit)}
            className="px-6 py-2 bg-blue-600 text-white font-bold rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed shadow"
          >
            Next
          </button>
        </div>
      </main>
    </div>
  );
}
