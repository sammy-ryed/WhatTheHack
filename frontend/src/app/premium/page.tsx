"use client";

import { useState, useRef, useEffect } from "react";
import Image from "next/image";

export default function PremiumPage() {
  // Sidebar closed by default
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [toggles, setToggles] = useState<{ [key: string]: boolean }>({});

  const profileRef = useRef<HTMLDivElement>(null);

  const handleToggle = (name: string) => {
    setToggles((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  const saveSettings = () => {
    const settings = Object.entries(toggles).map(([name, active]) => ({
      name,
      active,
    }));
    console.log("Saved Settings:", settings);
    alert("Settings saved! Check the console for details.");
  };

  // Close profile dropdown if clicked outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        profileRef.current &&
        !profileRef.current.contains(event.target as Node)
      ) {
        setProfileOpen(false);
      }
    }
    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, []);

  return (
    <div className="bg-[#0d1117] text-white min-h-screen flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`fixed w-64 bg-[#161b22] p-4 h-full transform z-50 transition-transform duration-300 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <h2 className="text-xl font-bold mb-6">Menu</h2>
        <ul>
          <li className="mb-4">
            <a href="/home" className="hover:text-green-400">
              Home
            </a>
          </li>
          <li className="mb-4">
            <a href="/premium" className="text-green-400 font-semibold">
              WhatTheActualHack
            </a>
          </li>
          <li className="mb-4">
            <a href="/settings" className="hover:text-green-400">
              Settings
            </a>
          </li>
        </ul>
      </aside>

      {/* Main Content */}
      <div
        id="mainContent"
        className={`flex-1 flex flex-col transition-all duration-300 ${
          sidebarOpen ? "ml-64" : "ml-0"
        }`}
      >
        {/* Header */}
        <header className="bg-[#161b22] p-4 flex items-center justify-between">
          <div className="flex items-center">
            {/* Hamburger styled like Home page */}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label="Toggle sidebar menu"
              className="mr-4 p-3 rounded-lg shadow-md bg-[#21262d] border border-[#30363d]"
            >
              <div className="w-6 h-[3px] bg-white mb-1" />
              <div className="w-6 h-[3px] bg-white mb-1" />
              <div className="w-6 h-[3px] bg-white" />
            </button>
            <Image src="/dark.png" alt="WhatTheActualHack" width={56} height={56} />
          </div>

          <div className="relative" ref={profileRef}>
            <button
              onClick={() => setProfileOpen(!profileOpen)}
              className="focus:outline-none"
            >
              <div className="w-8 h-8 bg-gray-500 rounded-full hover:bg-gray-400 flex items-center justify-center">
                <span className="text-lg font-semibold">J</span>
              </div>
            </button>
            {profileOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-gray-700 rounded-md shadow-lg py-1 z-20">
                <div className="block px-4 py-2 text-sm text-gray-300">
                  Username: What??
                </div>
                <a
                  href="/premium"
                  className="block px-4 py-2 text-sm text-green-300 hover:bg-green-600"
                >
                  Premium User
                </a>
                <a
                  href="/settings"
                  className="block px-4 py-2 text-sm text-gray-300 hover:bg-gray-600"
                >
                  Settings
                </a>
                <a
                  href="#"
                  className="block px-4 py-2 text-sm text-gray-300 hover:bg-gray-600"
                >
                  Logout
                </a>
              </div>
            )}
          </div>
        </header>

        {/* Main Sections */}
        <main className="p-6 overflow-y-auto">
          {/* Manage APIs */}
          <Section
            title="Manage APIs"
            items={[
              { name: "GitHub Scraper", desc: "Scrape GitHub repositories" },
              { name: "Reddit Scraper", desc: "Collect data from Reddit" },
              { name: "Internal Knowledge Base", desc: "Query internal documents" },
            ]}
            toggles={toggles}
            handleToggle={handleToggle}
          />

          {/* Manage LLMs */}
          <Section
            title="Manage LLMs"
            items={[
              { name: "GPT-4", desc: "OpenAI's most advanced model" },
              { name: "Claude", desc: "Anthropic's advanced LLM" },
              { name: "LLaMA 3", desc: "Meta's open-source model" },
              { name: "Gemini Pro", desc: "Google DeepMind's model" },
            ]}
            toggles={toggles}
            handleToggle={handleToggle}
          />

          <div className="flex justify-end">
            <button
              onClick={saveSettings}
              className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-lg font-semibold transition"
            >
              Save Settings
            </button>
          </div>
        </main>
      </div>
    </div>
  );
}

function Section({
  title,
  items,
  toggles,
  handleToggle,
}: {
  title: string;
  items: { name: string; desc: string }[];
  toggles: { [key: string]: boolean };
  handleToggle: (name: string) => void;
}) {
  return (
    <section className="mb-10">
      <h2 className="text-xl font-bold mb-4">{title}</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {items.map(({ name, desc }) => (
          <div
            key={name}
            className="bg-[#161b22] p-4 rounded-lg shadow hover:scale-105 transition"
          >
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-semibold">{name}</h3>
                <p className="text-sm text-gray-400">{desc}</p>
              </div>
              <button
                onClick={() => handleToggle(name)}
                className={`relative w-12 h-6 rounded-full ${
                  toggles[name] ? "bg-green-500" : "bg-gray-600"
                }`}
              >
                <span
                  className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transform transition ${
                    toggles[name] ? "translate-x-6" : ""
                  }`}
                />
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
