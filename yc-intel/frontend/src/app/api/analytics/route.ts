import { NextResponse } from "next/server";

const API_BASE_URL = "http://localhost:8000/api";

export async function GET() {
  try {
    const url = `${API_BASE_URL}/analytics`;
    const response = await fetch(url, {
      cache: "no-store"
    });
    
    if (!response.ok) {
      throw new Error("Failed to fetch analytics");
    }
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: "Failed to fetch analytics" }, { status: 500 });
  }
}
