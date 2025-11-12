'use client';

import Link from "next/link";
import { ThemeToggle } from "./ThemeToggle";

export function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-neutral-200/60 dark:border-slate-800/60 bg-white/95 dark:bg-slate-950/95 backdrop-blur-xl shadow-sm transition-colors duration-300">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-20 items-center justify-between">
          <div className="flex items-center gap-8">
            <Link
              href="/"
              className="flex items-center gap-3 text-xl font-bold tracking-tight text-neutral-900 dark:text-slate-100 hover:opacity-80 transition-opacity"
            >
              <svg
                className="h-7 w-7"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
              <span className="hidden sm:inline">Senate Tracker</span>
            </Link>

            <nav className="hidden md:flex items-center gap-8 ml-4" aria-label="Main navigation">
              <Link
                href="/"
                className="text-sm font-semibold text-neutral-600 dark:text-slate-400 hover:text-neutral-900 dark:hover:text-slate-100 transition-colors relative py-1 after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0 hover:after:w-full after:bg-neutral-900 dark:after:bg-slate-100 after:transition-all"
              >
                Trades
              </Link>
              <Link
                href="/senators"
                className="text-sm font-semibold text-neutral-600 dark:text-slate-400 hover:text-neutral-900 dark:hover:text-slate-100 transition-colors relative py-1 after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0 hover:after:w-full after:bg-neutral-900 dark:after:bg-slate-100 after:transition-all"
              >
                Senators
              </Link>
              <Link
                href="/stats"
                className="text-sm font-semibold text-neutral-600 dark:text-slate-400 hover:text-neutral-900 dark:hover:text-slate-100 transition-colors relative py-1 after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0 hover:after:w-full after:bg-neutral-900 dark:after:bg-slate-100 after:transition-all"
              >
                Statistics
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <ThemeToggle />
            <a
              href="https://efdsearch.senate.gov/search/"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:inline-flex items-center gap-1.5 text-sm text-neutral-600 dark:text-slate-400 hover:text-neutral-900 dark:hover:text-slate-100 transition-colors"
            >
              <span>Official Source</span>
              <svg
                className="h-3.5 w-3.5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </header>
  );
}
