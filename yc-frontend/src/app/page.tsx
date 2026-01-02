'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Search, MapPin, TrendingUp } from 'lucide-react';

interface Company {
  id: number;
  name: string;
  description: string;
  website?: string;
  stage: string;
  location: string;
  tags: string | string[];
  created_at: string;
}

interface ApiResponse {
  companies: Company[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

export default function Home() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [stage, setStage] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    fetchCompanies();
  }, [page, search, stage]);

  const fetchCompanies = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '20',
        ...(search ? { search } : {}),
        ...(stage ? { stage } : {}),
      });

      const res = await fetch(`/api/companies?${params}`);
      if (!res.ok) throw new Error('Failed to fetch');

      const data: ApiResponse = await res.json();

      setCompanies(data.companies || []);
      setTotalPages(data.pagination?.totalPages || 0);
      setTotal(data.pagination?.total || 0);
    } catch (error) {
      console.error('Failed to fetch:', error);
      setCompanies([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <header className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <h1 className="text-4xl font-bold text-blue-600">YC Companies</h1>
          <p className="text-gray-600 mt-2">
            Explore {total.toLocaleString()} Y Combinator funded startups
          </p>

          <nav className="flex gap-6 mt-4">
            <Link href="/" className="text-blue-600 font-medium hover:underline">
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

            <select
              value={stage}
              onChange={(e) => {
                setStage(e.target.value);
                setPage(1);
              }}
              className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Stages</option>
              <option value="seed">Seed</option>
              <option value="series_a">Series A</option>
              <option value="series_b">Series B</option>
              <option value="series_c">Series C</option>
              <option value="series_d">Series D+</option>
            </select>
          </div>

          <p className="text-sm text-gray-600">
            Showing {total > 0 ? ((page - 1) * 20 + 1).toLocaleString() : 0} -{' '}
            {Math.min(page * 20, total).toLocaleString()} of {total.toLocaleString()}
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
            {companies.map((company) => {
              const tagsArray =
                Array.isArray(company.tags)
                  ? company.tags
                  : (() => {
                      try {
                        return JSON.parse(company.tags || '[]');
                      } catch {
                        return [];
                      }
                    })();

              return (
                <Link
                  key={company.id}
                  href={`/companies/${company.id}`}
                  className="bg-white rounded-lg shadow hover:shadow-lg transition p-6 border border-gray-100 block"
                >
                  <h3 className="text-xl font-bold text-blue-600 mb-2">
                    {company.name}
                  </h3>

                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                    {company.description || 'No description'}
                  </p>

                  <div className="space-y-2 text-sm mb-4">
                    <div className="flex items-center gap-2 text-gray-700">
                      <TrendingUp className="w-4 h-4" />
                      <span className="font-medium">
                        {company.stage || 'Unknown'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-700">
                      <MapPin className="w-4 h-4" />
                      <span>{company.location || 'Unknown'}</span>
                    </div>
                  </div>

                  {tagsArray.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-4">
                      {tagsArray.slice(0, 3).map((tag: string, i: number) => (
                        <span
                          key={i}
                          className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}

                  {company.website && (
                    <a
                      href={`https://${company.website}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.preventDefault()}
                      className="text-blue-600 hover:underline text-sm font-medium"
                    >
                      Visit Website →
                    </a>
                  )}
                </Link>
              );
            })}
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex justify-center gap-2 mt-12">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="px-4 py-2 border rounded-lg disabled:opacity-50 hover:bg-gray-50"
            >
              Previous
            </button>

            <div className="flex items-center gap-2">
              <input
                type="number"
                value={page}
                onChange={(e) =>
                  setPage(
                    Math.max(
                      1,
                      Math.min(totalPages, Number(e.target.value) || 1)
                    )
                  )
                }
                className="w-12 px-2 py-2 border rounded-lg text-center"
                min="1"
                max={totalPages}
              />
              <span className="text-gray-600">/ {totalPages}</span>
            </div>

            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="px-4 py-2 border rounded-lg disabled:opacity-50 hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
