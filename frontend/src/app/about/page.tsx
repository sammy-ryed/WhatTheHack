"use client";

import React, { useState } from "react";

interface TeamMember {
  id: number;
  name: string;
  role: string;
  photo: string;
  desc: string;
  github: string;
  linkedin: string;
}

const TEAM: TeamMember[] = [
  { id: 1, name: "Muskan", role: "Frontend Developer", photo: "muskan.jpg", desc: "Crafting digital magic where pixels meet functionality.", github: "https://github.com/squirrelk6755-ctrl", linkedin: "https://linkedin.com/in/muskan-26919b349/" },
  { id: 2, name: "Samarth Ryan Edward", role: "Backend Developer", photo: "samarth.jpg", desc: "poopy pants.", github: "https://github.com/sammy-ryed", linkedin: "https://www.linkedin.com/in/samarth-ryan-edward-a51047352/" },
  { id: 3, name: "Ayush Saini", role: "Frontend Developer", photo: "Ayush Saini.jpg", desc: "Optimizes interfaces for speed and clarity.", github: "https://github.com/saini07ayush", linkedin: "https://linkedin.com/in/saini07ayush" },
  { id: 4, name: "Arvin Mathew Saj", role: "Frontend Designer", photo: "arvin.jpg", desc: "Designs intuitive interfaces that feel natural.", github: "https://github.com/arvin-mathew", linkedin: "https://www.linkedin.com/in/arvin-mathew-564957341/" },
];

export default function AboutUsPage() {
  const [modalMember, setModalMember] = useState<TeamMember | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <main className="min-h-screen bg-[var(--bg)] text-[var(--text)] transition-colors font-sans relative p-8">

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
  <a href="/home" className="hover:text-purple-500 text-lg">Home</a>
</aside>



      {/* Hero Section */}
      <section className="text-center max-w-3xl mx-auto mb-16">
        <h1 className="text-6xl font-semibold mb-6" style={{ fontFamily: "'Barlow Semi Condensed', sans-serif" }}>
          WhatTheHack
        </h1>
        <p className="text-lg md:text-xl text-[var(--muted)] leading-relaxed">
          A clean, minimal portal to explore our coding projects. Search, filter, and browse effortlessly. Designed for clarity and speed.
        </p>
      </section>

      {/* Team Section */}
      <section className="max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-12 text-[var(--text)]" style={{ fontFamily: "'Barlow Semi Condensed', sans-serif" }}>
          Meet Our Team
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {TEAM.map((member) => (
            <div
              key={member.id}
              className="bg-[var(--card)] p-6 rounded-2xl shadow-md text-center cursor-pointer hover:shadow-xl hover:scale-105 transition-transform"
              onClick={() => setModalMember(member)}
            >
              <img
                src={member.photo}
                alt={member.name}
                className="w-28 h-28 mx-auto rounded-full border-2 border-[var(--border)] mb-4 object-cover"
              />
              <h3 className="text-xl font-semibold mb-1">{member.name}</h3>
              <p className="text-indigo-400">{member.role}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Modal */}
      {modalMember && (
        <div
          className="fixed inset-0 bg-black bg-opacity-70 flex justify-center items-center z-50"
          onClick={() => setModalMember(null)}
        >
          <div
            className="bg-[var(--card)] p-8 rounded-2xl max-w-sm text-center shadow-lg transition-transform transform scale-95 animate-fadeIn"
            onClick={(e) => e.stopPropagation()}
          >
            <span
              className="absolute top-3 right-5 cursor-pointer text-2xl text-[var(--muted)] hover:text-[var(--text)] transition"
              onClick={() => setModalMember(null)}
            >
              &times;
            </span>
            <img
              src={modalMember.photo}
              alt={modalMember.name}
              className="w-28 h-28 mx-auto rounded-full border-2 border-[var(--border)] mb-4 object-cover"
            />
            <h2 className="text-2xl font-semibold mb-1">{modalMember.name}</h2>
            <p className="text-indigo-400 font-medium">{modalMember.role}</p>
            <p className="mt-3 text-[var(--muted)]">{modalMember.desc}</p>
            <div className="mt-5 flex justify-center gap-4">
              <a
                href={modalMember.github}
                target="_blank"
                className="px-4 py-2 rounded-lg bg-gray-800 text-white hover:bg-gray-700 transition"
              >
                GitHub
              </a>
              <a
                href={modalMember.linkedin}
                target="_blank"
                className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-500 transition"
              >
                LinkedIn
              </a>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .animate-fadeIn {
          animation: fadeIn 0.2s ease forwards;
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </main>
  );
}
