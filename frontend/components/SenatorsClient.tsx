'use client';

import { useEffect, useState } from 'react';
import { SenatorStats } from '@/types';
import { getSenators } from '@/lib/api';
import { formatCurrency, formatDate } from '@/lib/utils';
import Link from 'next/link';

export function SenatorsClient() {
  const [senators, setSenators] = useState<SenatorStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [orderBy, setOrderBy] = useState<'total_transactions' | 'total_volume_estimate' | 'latest_trade'>('total_transactions');

  const fetchSenators = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSenators({ limit: 100, order_by: orderBy });
      setSenators(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch senators');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSenators();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orderBy]);

  return (
    <>
      {/* Sort Control */}
      <div className="rounded-2xl border border-neutral-200/60 dark:border-slate-800/60 bg-white dark:bg-slate-900 p-6 shadow-lg shadow-neutral-200/50 dark:shadow-slate-900/50 transition-colors duration-300">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-neutral-900 dark:text-slate-100">Sort By</h2>
          <select
            value={orderBy}
            onChange={(e) => setOrderBy(e.target.value as any)}
            className="rounded-lg border-2 border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 px-4 py-2.5 text-sm font-medium focus:border-slate-500 dark:focus:border-slate-500 focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 dark:focus:ring-offset-slate-900 transition-colors"
          >
            <option value="total_transactions">Most Transactions</option>
            <option value="total_volume_estimate">Highest Volume</option>
            <option value="latest_trade">Most Recent Activity</option>
          </select>
        </div>
      </div>

      {/* Senators Table */}
      <div className="rounded-2xl border border-neutral-200/60 dark:border-slate-800/60 bg-white dark:bg-slate-900 shadow-lg shadow-neutral-200/50 dark:shadow-slate-900/50 overflow-hidden transition-colors duration-300">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="h-12 w-12 animate-spin rounded-full border-3 border-slate-200 dark:border-slate-700 border-t-slate-900 dark:border-t-slate-100"></div>
            <p className="mt-6 text-sm font-medium text-slate-600 dark:text-slate-400">Loading senators...</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-center px-4">
            <svg
              className="h-16 w-16 text-red-400 dark:text-red-500 mb-6"
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
            <p className="text-base font-semibold text-red-900 dark:text-red-400 mb-2">Error loading senators</p>
            <p className="text-sm text-red-700 dark:text-red-500">{error}</p>
          </div>
        ) : senators.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <svg
              className="h-16 w-16 text-neutral-300 dark:text-slate-700 mb-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
            <p className="text-base text-neutral-700 dark:text-slate-300 font-semibold">No senators found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-neutral-200/80 dark:divide-slate-800/80">
              <thead>
                <tr className="bg-slate-50/50 dark:bg-slate-800/50">
                  <th className="py-4 pl-6 pr-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                    Senator
                  </th>
                  <th className="px-4 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                    Total Trades
                  </th>
                  <th className="px-4 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                    Purchases
                  </th>
                  <th className="px-4 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                    Sales
                  </th>
                  <th className="px-4 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                    Est. Volume
                  </th>
                  <th className="px-4 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                    Latest Trade
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100 dark:divide-slate-800 bg-white dark:bg-slate-900">
                {senators.map((senator) => (
                  <tr key={senator.full_name} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/50 transition-colors duration-150">
                    <td className="py-5 pl-6 pr-4">
                      <Link
                        href={`/senator/${encodeURIComponent(senator.full_name)}`}
                        className="text-sm font-semibold text-slate-900 dark:text-slate-100 hover:text-slate-600 dark:hover:text-slate-400 transition-colors underline decoration-slate-300 dark:decoration-slate-600 hover:decoration-slate-600 dark:hover:decoration-slate-400 decoration-2 underline-offset-2"
                      >
                        {senator.full_name}
                      </Link>
                    </td>
                    <td className="whitespace-nowrap px-4 py-5 text-sm font-medium text-slate-900 dark:text-slate-100">
                      {senator.total_transactions.toLocaleString()}
                    </td>
                    <td className="whitespace-nowrap px-4 py-5 text-sm font-semibold text-teal-600 dark:text-teal-400">
                      {senator.total_purchases?.toLocaleString() || 0}
                    </td>
                    <td className="whitespace-nowrap px-4 py-5 text-sm font-semibold text-amber-600 dark:text-amber-400">
                      {senator.total_sales?.toLocaleString() || 0}
                    </td>
                    <td className="whitespace-nowrap px-4 py-5 text-sm font-semibold text-slate-900 dark:text-slate-100">
                      {formatCurrency(senator.total_volume_estimate)}
                    </td>
                    <td className="whitespace-nowrap px-4 py-5 text-sm text-slate-600 dark:text-slate-400">
                      {formatDate(senator.latest_trade)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
