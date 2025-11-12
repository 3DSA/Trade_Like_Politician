'use client';

import { useEffect, useState } from 'react';
import { TradingStats } from '@/types';
import { getOverallStats } from '@/lib/api';
import { formatCurrency, formatDate } from '@/lib/utils';

export function StatsClient() {
  const [stats, setStats] = useState<TradingStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getOverallStats();
        setStats(data);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch statistics');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="h-12 w-12 animate-spin rounded-full border-3 border-slate-200 dark:border-slate-700 border-t-slate-900 dark:border-t-slate-100"></div>
        <p className="mt-6 text-sm font-medium text-slate-600 dark:text-slate-400">Loading statistics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/30 p-8 text-center transition-colors duration-300">
        <svg
          className="mx-auto h-16 w-16 text-red-400 dark:text-red-500 mb-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <p className="text-base font-semibold text-red-900 dark:text-red-400 mb-2">Error loading statistics</p>
        <p className="text-sm text-red-700 dark:text-red-500">{error}</p>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  const statCards = [
    {
      title: 'Total Transactions',
      value: stats.total_transactions.toLocaleString(),
      icon: (
        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      gradient: 'from-slate-600 to-slate-700 dark:from-slate-500 dark:to-slate-600',
    },
    {
      title: 'Estimated Volume',
      value: formatCurrency(stats.total_volume_estimate),
      icon: (
        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      gradient: 'from-teal-600 to-teal-700 dark:from-teal-500 dark:to-teal-600',
    },
    {
      title: 'Active Senators',
      value: stats.total_senators.toLocaleString(),
      icon: (
        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
      gradient: 'from-blue-600 to-blue-700 dark:from-blue-500 dark:to-blue-600',
    },
    {
      title: 'Total Filings',
      value: stats.total_filings.toLocaleString(),
      icon: (
        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      gradient: 'from-amber-600 to-amber-700 dark:from-amber-500 dark:to-amber-600',
    },
  ];

  return (
    <>
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, idx) => (
          <div
            key={idx}
            className="relative overflow-hidden rounded-2xl border border-neutral-200/60 dark:border-slate-800/60 bg-white dark:bg-slate-900 p-8 shadow-lg shadow-neutral-200/50 dark:shadow-slate-900/50 hover:shadow-xl dark:hover:shadow-slate-900/70 transition-all duration-300"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-3">{stat.title}</p>
                <p className="text-3xl font-bold text-slate-900 dark:text-slate-100">{stat.value}</p>
              </div>
              <div className={`flex-shrink-0 rounded-xl bg-gradient-to-br ${stat.gradient} p-3 text-white shadow-lg`}>
                {stat.icon}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Date Range Card */}
      <div className="rounded-2xl border border-neutral-200/60 dark:border-slate-800/60 bg-white dark:bg-slate-900 p-8 shadow-lg shadow-neutral-200/50 dark:shadow-slate-900/50 transition-colors duration-300">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-6">Data Coverage</h2>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-2">From</p>
            <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{formatDate(stats.date_range_start)}</p>
          </div>
          <div className="flex-shrink-0 mx-6">
            <svg className="h-8 w-8 text-slate-400 dark:text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-2">To</p>
            <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{formatDate(stats.date_range_end)}</p>
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="rounded-2xl border border-blue-200/60 dark:border-blue-900/50 bg-blue-50 dark:bg-blue-950/30 p-8 transition-colors duration-300">
        <div className="flex gap-4">
          <svg className="h-6 w-6 text-blue-700 dark:text-blue-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h3 className="text-base font-semibold text-blue-900 dark:text-blue-300 mb-2">About This Data</h3>
            <p className="text-sm text-blue-900 dark:text-blue-200 leading-relaxed">
              This data is collected from official U.S. Senate eFD (Electronic Financial Disclosure)
              periodic transaction reports. Senators are required to report stock trades within 45 days
              under the STOCK Act. The estimated volume is calculated using the midpoint of reported
              ranges, as exact amounts are not disclosed.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
