"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

interface StoredProblem {
  id: number;
  reframed: string;
  domain: string;
  difficulty: string;
}

export default function FeedPage() {
  const [redditProblems, setRedditProblems] = useState<string[]>([]);
  const [storedProblems, setStoredProblems] = useState<StoredProblem[]>([]);
  const [loadingReddit, setLoadingReddit] = useState(true);
  const [loadingStored, setLoadingStored] = useState(true);
  const [saving, setSaving] = useState<string | null>(null); // track saving state

  // fetch Reddit problems
  useEffect(() => {
    fetch("/api/fetch")
      .then((res) => res.json())
      .then((data) => setRedditProblems(data.problems || []))
      .catch(() => setRedditProblems([]))
      .finally(() => setLoadingReddit(false));
  }, []);

  // fetch stored problems from DB
  const loadStoredProblems = () => {
    setLoadingStored(true);
    fetch("/api/problems")
      .then((res) => res.json())
      .then((data) => setStoredProblems(data || []))
      .catch(() => setStoredProblems([]))
      .finally(() => setLoadingStored(false));
  };

  useEffect(() => {
    loadStoredProblems();
  }, []);

  // Save + reframe handler
  const handleSave = async (text: string) => {
    setSaving(text);
    try {
      await fetch("/api/reframe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      loadStoredProblems(); // refresh DB feed
    } catch (err) {
      console.error("❌ Error saving problem:", err);
    } finally {
      setSaving(null);
    }
  };

  return (
    <main className="min-h-screen p-6 bg-black text-white space-y-10">
      <header className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">⚡ Problem Feed</h1>
        <Link
          href="/"
          className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 transition"
        >
          ← Back to Home
        </Link>
      </header>

      {/* Reddit feed */}
      <section>
        <h2 className="text-2xl font-bold mb-4">🔥 Fresh Reddit Problems</h2>
        <div className="grid gap-4">
          {loadingReddit ? (
            <p className="text-gray-400">Loading Reddit problems...</p>
          ) : redditProblems.length > 0 ? (
            redditProblems.map((p, x) => (
              <div key={x} className="bg-gray-900 p-4 rounded space-y-2">
                <p>{p}</p>
                <button
                  onClick={() => handleSave(p)}
                  disabled={saving === p}
                  className="px-3 py-1 rounded bg-green-600 hover:bg-green-500 disabled:opacity-50"
                >
                  {saving === p ? "⏳ Saving..." : "💾 Save & Reframe"}
                </button>
              </div>
            ))
          ) : (
            <p className="text-gray-400">No Reddit problems found.</p>
          )}
        </div>
      </section>

      {/* Stored problems feed */}
      <section>
        <h2 className="text-2xl font-bold mb-4">💾 Stored Problems</h2>
        <div className="grid gap-4">
          {loadingStored ? (
            <p className="text-gray-400">Loading stored problems...</p>
          ) : storedProblems.length > 0 ? (
            storedProblems.map((p) => (
              <div key={p.id} className="bg-gray-900 p-4 rounded">
                <h3 className="font-bold">{p.reframed}</h3>
                <p className="text-sm text-gray-400">
                  Domain: {p.domain} | Difficulty: {p.difficulty}
                </p>
              </div>
            ))
          ) : (
            <p className="text-gray-400">No problems saved yet.</p>
          )}
        </div>
      </section>
    </main>
  );
}
