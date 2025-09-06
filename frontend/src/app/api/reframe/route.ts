import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const { text } = await req.json();

    const res = await fetch("http://127.0.0.1:8000/reframe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    if (!res.ok) throw new Error(`Status ${res.status}`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    console.error("❌ Error reframing problem:", err);
    return NextResponse.json({ error: "Backend not reachable" }, { status: 500 });
  }
}
