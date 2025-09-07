// app/page.tsx
"use client";

import { useEffect } from "react";
import Link from "next/link";

export default function LandingPage() {
  useEffect(() => {
    // Dynamically load the starfield animation script
    const script = document.createElement("script");
    script.src = "/script.js";
    script.async = true;
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, []);

  return (
    <main className="w-full h-screen relative overflow-hidden">
      {/* Starfield background */}
      <canvas id="background" className="absolute inset-0 w-full h-full -z-10"></canvas>

      {/* Centered content */}
      <div className="content absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center text-white">
        <h1 className="text-5xl font-bold mb-6 drop-shadow-lg">WhatTheHack</h1>
        <p className="text-xl mb-8 drop-shadow-md">Where Problems Find You</p>

        <Link href="/home">
          <button className="px-6 py-3 rounded-lg font-semibold text-lg bg-gradient-to-r from-purple-500 to-cyan-500 hover:from-cyan-400 hover:to-blue-500 shadow-lg hover:scale-105 transition">
            Let&apos;s Find Your Problem
          </button>
        </Link>
      </div>
    </main>
  );
}
