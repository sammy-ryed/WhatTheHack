import { NextResponse } from "next/server";

export async function GET() {
  try {
    const res = await fetch("http://127.0.0.1:8000/problems", {
      cache: "no-store", // 👈 avoids stale cache
    });

    if (!res.ok) {
      throw new Error(`FastAPI returned ${res.status}`);
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err: any) {
    console.error("❌ Error fetching stored problems:", err);
    return NextResponse.json(
      { error: "Backend not reachable", details: err.message },
      { status: 500 }
    );
  }
}
