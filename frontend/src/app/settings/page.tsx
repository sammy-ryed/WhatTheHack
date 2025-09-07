"use client";

import { useState, useRef, useEffect } from "react";
import Image from "next/image";

export default function SettingsPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  const profileRef = useRef<HTMLDivElement>(null);

  // Close profile dropdown when clicking outside
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

  const saveChanges = () => {
    alert("Your settings have been saved!");
  };

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
            <a href="/premium" className="hover:text-green-400">
              WhatTheHack
            </a>
          </li>
          <li className="mb-4">
            <a href="/settings" className="text-green-400 font-semibold">
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
            {/* Hamburger styled like PremiumPage */}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label="Toggle sidebar menu"
              className="mr-4 p-3 rounded-lg shadow-md bg-[#21262d] border border-[#30363d]"
            >
              <div className="w-6 h-[3px] bg-white mb-1" />
              <div className="w-6 h-[3px] bg-white mb-1" />
              <div className="w-6 h-[3px] bg-white" />
            </button>
            <Image src="/dark.png" alt="WhatTheHack" width={56} height={56} />
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
                  Username: JohnDoe
                </div>
                <div className="block px-4 py-2 text-sm text-green-400">
                  Premium User
                </div>
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
        <main className="p-8 overflow-y-auto">
          {/* Profile Settings */}
          <section className="mb-12">
            <h2 className="text-2xl font-bold border-b border-gray-700 pb-2 mb-6">
              Profile Settings
            </h2>
            <div className="space-y-6">
              <div>
                <label
                  htmlFor="username"
                  className="block text-sm font-medium text-gray-300 mb-1"
                >
                  Username
                </label>
                <input
                  type="text"
                  id="username"
                  placeholder="JohnDoe"
                  className="w-full md:w-1/2 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-medium text-gray-300 mb-1"
                >
                  Email Address
                </label>
                <input
                  type="email"
                  id="email"
                  placeholder="JohnDoe@email.com"
                  className="w-full md:w-1/2 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label
                  htmlFor="bio"
                  className="block text-sm font-medium text-gray-300 mb-1"
                >
                  Bio
                </label>
                <textarea
                  id="bio"
                  rows={4}
                  className="w-full md:w-1/2 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="Tell us about yourself..."
                />
              </div>
            </div>
          </section>

          {/* Delete Account */}
          <section>
            <div className="border-2 border-red-500/50 rounded-lg p-4 md:w-1/2">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-red-400">Delete Account</h3>
                  <p className="text-sm text-gray-400">
                    Once you delete your account, there is no going back.
                  </p>
                </div>
                <button className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-semibold transition">
                  Delete
                </button>
              </div>
            </div>
          </section>

          {/* Save Button */}
          <div className="flex justify-start mt-10 border-t border-gray-700 pt-6">
            <button
              onClick={saveChanges}
              className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-lg font-semibold transition"
            >
              Save Changes
            </button>
          </div>
        </main>
      </div>
    </div>
  );
}
