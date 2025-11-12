'use client';

import { useEffect, useState } from 'react';
import { Transaction, SenatorStats } from '@/types';
import { getSenatorTrades, getSenatorStats } from '@/lib/api';
import { TransactionTable } from '@/components/TransactionTable';
import { formatCurrency } from '@/lib/utils';

interface SenatorProfileClientProps {
  senatorName: string;
}

export function SenatorProfileClient({ senatorName }: SenatorProfileClientProps) {
  const [trades, setTrades] = useState<Transaction[]>([]);
  const [stats, setStats] = useState<SenatorStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const [tradesData, statsData] = await Promise.all([
          getSenatorTrades(senatorName, { limit: 200 }),
          getSenatorStats(senatorName),
        ]);
        setTrades(tradesData);
        setStats(statsData);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch senator data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [senatorName]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="h-12 w-12 animate-spin rounded-full border-3 border-slate-200 dark:border-slate-700 border-t-slate-900 dark:border-t-slate-100"></div>
        <p className="mt-6 text-sm font-medium text-slate-600 dark:text-slate-400">Loading senator data...</p>
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
        <p className="text-base font-semibold text-red-900 dark:text-red-400 mb-2">Error loading senator data</p>
        <p className="text-sm text-red-700 dark:text-red-500">{error}</p>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <>
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="rounded-2xl border border-neutral-200/60 dark:border-slate-800/60 bg-white dark:bg-slate-900 p-8 shadow-lg shadow-neutral-200/50 dark:shadow-slate-900/50 transition-colors duration-300">
          <p className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-2">Total Trades</p>
          <p className="text-4xl font-bold text-slate-900 dark:text-slate-100">{stats.total_transactions.toLocaleString()}</p>
        </div>

        <div className="rounded-2xl border border-neutral-200/60 dark:border-slate-800/60 bg-white dark:bg-slate-900 p-8 shadow-lg shadow-neutral-200/50 dark:shadow-slate-900/50 transition-colors duration-300">
          <p className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-2">Estimated Volume</p>
          <p className="text-4xl font-bold text-slate-900 dark:text-slate-100">{formatCurrency(stats.total_volume_estimate)}</p>
        </div>

        <div className="rounded-2xl border border-neutral-200/60 dark:border-slate-800/60 bg-white dark:bg-slate-900 p-8 shadow-lg shadow-neutral-200/50 dark:shadow-slate-900/50 transition-colors duration-300">
          <p className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-2">Purchases</p>
          <p className="text-4xl font-bold text-teal-600 dark:text-teal-400">{stats.total_purchases?.toLocaleString() || 0}</p>
        </div>

        <div className="rounded-2xl border border-neutral-200/60 dark:border-slate-800/60 bg-white dark:bg-slate-900 p-8 shadow-lg shadow-neutral-200/50 dark:shadow-slate-900/50 transition-colors duration-300">
          <p className="text-sm font-medium text-slate-600 dark:text-slate-400 mb-2">Sales</p>
          <p className="text-4xl font-bold text-amber-600 dark:text-amber-400">{stats.total_sales?.toLocaleString() || 0}</p>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="rounded-2xl border border-neutral-200/60 dark:border-slate-800/60 bg-white dark:bg-slate-900 shadow-lg shadow-neutral-200/50 dark:shadow-slate-900/50 overflow-hidden transition-colors duration-300">
        <div className="px-8 py-6 border-b border-neutral-200/80 dark:border-slate-800/80">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">All Transactions</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">Complete trading history for this senator</p>
        </div>
        <TransactionTable transactions={trades} />
      </div>
    </>
  );
}
