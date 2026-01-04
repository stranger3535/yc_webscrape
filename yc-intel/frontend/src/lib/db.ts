const API_BASE_URL = 'http://localhost:8000/api';

export async function getCompanies(page = 1, limit = 20, search = '') {
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
    ...(search && { search })
  });
  
  const response = await fetch(`${API_BASE_URL}/companies?${params}`);
  if (!response.ok) throw new Error('Failed to fetch companies');
  return response.json();
}

export async function getCompanyDetail(id: number) {
  const response = await fetch(`${API_BASE_URL}/companies/${id}`);
  if (!response.ok) throw new Error('Failed to fetch company');
  return response.json();
}

export async function getAnalytics() {
  const response = await fetch(`${API_BASE_URL}/analytics`);
  if (!response.ok) throw new Error('Failed to fetch analytics');
  return response.json();
}

export async function getStats() {
  const response = await fetch(`${API_BASE_URL}/stats`);
  if (!response.ok) throw new Error('Failed to fetch stats');
  return response.json();
}
