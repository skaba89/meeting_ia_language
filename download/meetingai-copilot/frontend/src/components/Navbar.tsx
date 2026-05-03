'use client';

import React from 'react';
import Link from 'next/link';
import { FileAudio, LogOut, User, Settings } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();

  const initials = user?.full_name
    ? user.full_name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'U';

  return (
    <nav className="sticky top-0 z-50 border-b border-border bg-white/80 backdrop-blur-xl shadow-sm">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Logo */}
        <Link href="/dashboard" className="flex items-center gap-2.5 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary-600 to-accent-600 shadow-glow transition-transform duration-200 group-hover:scale-105">
            <FileAudio className="h-5 w-5 text-white" />
          </div>
          <span className="text-lg font-bold text-dark">
            Meeting<span className="gradient-text">AI</span>
          </span>
        </Link>

        {/* Right side */}
        <div className="flex items-center gap-4">
          {user && (
            <div className="flex items-center gap-3">
              <div className="hidden items-center gap-2.5 sm:flex">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-accent-500 text-xs font-bold text-white shadow-sm">
                  {initials}
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-medium text-dark leading-tight">
                    {user.full_name}
                  </span>
                  <span className="text-xs text-muted leading-tight truncate max-w-[150px]">
                    {user.email}
                  </span>
                </div>
              </div>
              <button
                onClick={logout}
                className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-muted transition-all duration-200 hover:bg-red-50 hover:text-error"
                title="Sign out"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Sign out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
