import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = "http://localhost:8000/api";

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const page = searchParams.get("page") || "1";
    const limit = searchParams.get("limit") || "20";
    const search = searchParams.get("search") || "";
    
    const params = new URLSearchParams({ page, limit });
    if (search) params.append("search", search);
    
    const url = `${API_BASE_URL}/companies?${params}`;
    const response = await fetch(url, {
      cache: "no-store"
    });
    
    if (!response.ok) {
      throw new Error("Failed to fetch companies");
    }
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch companies" }, { status: 500 });
  }
}
