"use client";

import { useEffect, useState } from "react";

interface Problem {
  id: number;
  title: string;
  reframed: string;
  small_description: string;
  description: string; // detailed description + suggested solution
  domain: string;
  difficulty: string;
  source: string; // new field
  novelty: number; // 👈 add this
}



export default function HomePage() {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [search, setSearch] = useState("");
  const [domainFilter, setDomainFilter] = useState("All");
  const [difficultyFilter, setDifficultyFilter] = useState("All");
  const [theme, setTheme] = useState<"light" | "dark">("dark"); // default dark
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedProblem, setSelectedProblem] = useState<Problem | null>(null);

  // Load stored problems
  useEffect(() => {
    fetch("/api/problems")
      .then((res) => res.json())
      .then((data) => Array.isArray(data) && setProblems(data))
      .catch(() => setProblems([]));
  }, []);

  // Apply theme on first client render
  useEffect(() => {
    const saved = (localStorage.getItem("theme") as "light" | "dark") || "dark";
    setTheme(saved);
    document.documentElement.setAttribute("data-theme", saved);
  }, []);

  const toggleTheme = () => {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
  };

  // Filter + search logic
  const filtered = problems.filter((item) => {
    const matchesDomain = domainFilter === "All" || item.domain === domainFilter;
    const matchesDifficulty = difficultyFilter === "All" || item.difficulty === difficultyFilter;
    const matchesSearch =
      !search ||
      item.title.toLowerCase().includes(search.toLowerCase()) ||
      item.reframed.toLowerCase().includes(search.toLowerCase()) ||
      item.domain.toLowerCase().includes(search.toLowerCase());
    return matchesDomain && matchesDifficulty && matchesSearch;
  });

  return (
    <main className="min-h-screen bg-[var(--bg)] text-[var(--text)] transition-colors">
      {/* Hamburger */}
      <button
        className="fixed top-5 left-5 z-50 p-3 rounded-lg shadow-md bg-[var(--card)] border border-[var(--border)]"
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
        <a href="/" className="hover:text-purple-500 text-lg">Landing</a>
        <a href="/about" className="hover:text-purple-500 text-lg">About Us</a>
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

            {/* Domain Filter */}
            <select
              value={domainFilter}
              onChange={(e) => setDomainFilter(e.target.value)}
              className="bg-[var(--card)] border border-[var(--border)] rounded-lg px-3 py-2 shadow text-[var(--text)]"
            >
              <option value="All">All Domains</option>
              <option value="AI/ML">AI/ML</option>
              <option value="FinTech">FinTech</option>
              <option value="Blockchain">Blockchain</option>
              <option value="HealthTech">HealthTech</option>
              <option value="WebDev">WebDev</option>
              <option value="General Tech">General Tech</option>
            </select>

            {/* Difficulty Filter */}
            <select
              value={difficultyFilter}
              onChange={(e) => setDifficultyFilter(e.target.value)}
              className="bg-[var(--card)] border border-[var(--border)] rounded-lg px-3 py-2 shadow text-[var(--text)]"
            >
              <option value="All">All Difficulties</option>
              <option value="Easy">Easy</option>
              <option value="Medium">Medium</option>
              <option value="Hard">Hard</option>
            </select>

            {/* Theme toggle */}
            <button
              onClick={toggleTheme}
              className="bg-[var(--card)] border border-[var(--border)] rounded-lg px-3 py-2 shadow text-xl"
            >
              {theme === "dark" ? "☀️" : "🌙"}
            </button>
          </div>

          <div className="text-sm text-[var(--muted)]">
            Showing {filtered.length} problem{filtered.length !== 1 ? "s" : ""}
          </div>
        </div>

        {/* Problem Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.length === 0 ? (
            <p className="col-span-full text-center text-[var(--muted)]">No results found</p>
          ) : (
            filtered.map((item) => (
              <article
                key={item.id}
                onClick={() => setSelectedProblem(item)}
                className="group relative bg-[var(--card)] border-2 border-[var(--border)] rounded-2xl p-6 shadow transition transform hover:scale-105 hover:shadow-xl cursor-pointer overflow-hidden
                           before:content-[''] before:absolute before:inset-[-3px] before:rounded-2xl before:bg-[linear-gradient(135deg,#ff6ec4,#7873f5,#42e695,#ff9a9e)] before:bg-[length:400%_400%] before:opacity-0 hover:before:opacity-100 before:-z-10 before:transition-opacity before:duration-500"
              >
                <span className="inline-block text-sm bg-indigo-50 border border-indigo-200 px-3 py-1 rounded-full text-black mb-3">
                  {item.domain} | {item.difficulty}
                </span>
              <p className="text-xs text-[var(--muted)] mb-2">
  Source: <span className="font-medium text-yellow-300">{item.source}</span>

</p>
                <h3 className="text-2xl font-bold mb-2 text-[var(--text)]">{item.title}</h3>

                {/* Small description on hover */}
                <p
                  className="mt-7 text-sm text-[var(--text)] opacity-0 translate-y-2 
                             group-hover:opacity-100 group-hover:translate-y-0 
                             transition-all duration-500 ease-out"
                >
                  {item.small_description}
                </p>
              </article>
            ))
          )}
        </div>
      </div>

      {/* Modal */}
{selectedProblem && (
  <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
    <div className="bg-[var(--card)] rounded-2xl max-w-lg w-full p-6 relative shadow-xl overflow-y-auto max-h-[90vh]">
      <button
        className="absolute top-3 right-3 text-xl font-bold"
        onClick={() => setSelectedProblem(null)}
      >
        ✕
      </button>
      <h2 className="text-3xl font-bold mb-4">{selectedProblem.title}</h2>
      <p className="text-lg font-semibold mb-2">Problem Statement:</p>
      <p className="mb-4">{selectedProblem.reframed}</p>
      <p className="text-lg font-semibold mb-2">Detailed Description & Suggested Solution:</p>
      <p className="mb-4">{selectedProblem.description}</p>
      <p className="mb-1"><strong>Domain:</strong> {selectedProblem.domain}</p>
      <p className="mb-1"><strong>Difficulty:</strong> {selectedProblem.difficulty}</p>
      <p><strong>Novelty:</strong> {selectedProblem.novelty} / 10</p>
    </div>
  </div>
)}

    </main>
  );
}
