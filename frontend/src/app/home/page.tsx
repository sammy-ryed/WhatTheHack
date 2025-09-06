"use client";

import { useEffect, useState } from "react";

interface Problem {
  id: number;
  reframed: string;
  domain: string;
  difficulty: string;
}

export default function HomePage() {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Load stored problems from backend
  useEffect(() => {
    fetch("/api/problems")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) setProblems(data);
      })
      .catch(() => setProblems([]));
  }, []);

  // Theme management
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  useEffect(() => {
    const saved = (localStorage.getItem("theme") as "light" | "dark") || "light";
    setTheme(saved);
  }, []);

  // Filter + search logic
  const filtered = problems.filter((item) => {
    const matchesFilter = filter === "All" || item.domain === filter;
    const matchesSearch =
      !search ||
      item.reframed.toLowerCase().includes(search.toLowerCase()) ||
      item.domain.toLowerCase().includes(search.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <main className="min-h-screen bg-[var(--bg)] text-[var(--text)] transition-colors">
      {/* Hamburger */}
      <button
        className="fixed top-5 left-5 z-50 cursor-pointer bg-[var(--card)] border border-[var(--border)] p-3 rounded-lg shadow-md"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label="Toggle sidebar menu"
      >
        <div className="w-6 h-[3px] bg-[var(--text)] mb-1" />
        <div className="w-6 h-[3px] bg-[var(--text)] mb-1" />
        <div className="w-6 h-[3px] bg-[var(--text)]" />
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 bg-[var(--card)] shadow-md transform transition-transform duration-300 flex flex-col gap-5 px-6 pt-24 z-40 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <h2 className="text-2xl font-bold">Menu</h2>
        <a href="/" className="hover:text-purple-500 text-lg">
          Landing
        </a>
        <a href="/feed" className="hover:text-purple-500 text-lg">
          Problem Feed
        </a>
      </aside>

      <div className="container max-w-5xl mx-auto p-6">
        {/* Header */}
        <div className="grid grid-cols-[1fr_auto] gap-3 items-center mb-6">
          <div className="flex flex-wrap gap-3 items-center">
            {/* Search */}
            <div className="relative flex-1 min-w-[220px] bg-[var(--card)] border border-[var(--border)] rounded-xl shadow p-2 pl-8">
              <svg
                className="absolute left-2 top-1/2 -translate-y-1/2 w-5 h-5 fill-[var(--muted)]"
                viewBox="0 0 24 24"
              >
                <path d="M10 2a8 8 0 105.293 14.293l4.707 4.707 1.414-1.414-4.707-4.707A8 8 0 0010 2zm0 2a6 6 0 110 12 6 6 0 010-12z" />
              </svg>
              <input
                type="search"
                placeholder="Search problems…"
                className="w-full bg-transparent outline-none text-[var(--text)]"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            {/* Filter */}
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="bg-[var(--card)] border border-[var(--border)] rounded-lg px-3 py-2 shadow text-[var(--text)]"
            >
              <option value="All">All</option>
              <option value="AI/ML">AI/ML</option>
              <option value="FinTech">FinTech</option>
              <option value="Blockchain">Blockchain</option>
              <option value="HealthTech">HealthTech</option>
              <option value="WebDev">WebDev</option>
              <option value="General Tech">General Tech</option>
            </select>

            {/* Theme toggle */}
            <button
              onClick={() => setTheme(theme === "light" ? "dark" : "light")}
              className="bg-[var(--card)] border border-[var(--border)] rounded-lg px-3 py-2 shadow text-xl"
            >
              {theme === "dark" ? "☀️" : "🌙"}
            </button>
          </div>
          <div className="text-sm text-[var(--muted)]">
            Showing {filtered.length} problem{filtered.length !== 1 ? "s" : ""}
          </div>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.length === 0 ? (
            <p className="col-span-full text-center text-[var(--muted)]">
              No results found
            </p>
          ) : (
            filtered.map((item) => (
              <article
                key={item.id}
                className="relative bg-[var(--card)] border-2 border-[var(--border)] rounded-2xl p-6 shadow transition transform hover:scale-105 hover:shadow-xl cursor-pointer overflow-hidden
                           before:content-[''] before:absolute before:inset-[-3px] before:rounded-2xl before:bg-[linear-gradient(135deg,#ff6ec4,#7873f5,#42e695,#ff9a9e)] before:bg-[length:400%_400%] before:opacity-0 hover:before:opacity-100 before:-z-10 before:transition-opacity before:duration-500"
              >
                <span className="inline-block text-sm bg-indigo-50 border border-indigo-200 px-3 py-1 rounded-full text-black mb-3">
                  {item.domain} | {item.difficulty}
                </span>
                <h3 className="text-xl font-bold mb-2 text-[var(--text)]">
                  {item.reframed}
                </h3>
              </article>
            ))
          )}
        </div>
      </div>
    </main>
  );
}
  