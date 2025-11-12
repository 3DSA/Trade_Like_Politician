'use client';

import { useEffect, useState } from 'react';
import { Transaction } from '@/types';
import { getRecentTrades } from '@/lib/api';
import { TransactionTable } from '@/components/TransactionTable';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';

export function TradesClient() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    ticker: '',
    tx_type: '',
    min_amount: '',
  });

  const fetchTrades = async () => {
    try {
      setLoading(true);
      setError(null);
      const params: any = { limit: 100 };

      if (filters.ticker) params.ticker = filters.ticker;
      if (filters.tx_type) params.tx_type = filters.tx_type;
      if (filters.min_amount) params.min_amount = parseInt(filters.min_amount);

      const data = await getRecentTrades(params);
      setTransactions(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch trades');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrades();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFilters({
      ...filters,
      [e.target.name]: e.target.value,
    });
  };

  const handleApplyFilters = (e: React.FormEvent) => {
    e.preventDefault();
    fetchTrades();
  };

  const handleClearFilters = () => {
    setFilters({
      ticker: '',
      tx_type: '',
      min_amount: '',
    });
    setTimeout(() => fetchTrades(), 0);
  };

  return (
    <>
      {/* Filters Card */}
      <Card>
        <Card.Header
          title="Filter Trades"
          description="Refine results by ticker, transaction type, or minimum amount"
        />
        <Card.Body>
          <form onSubmit={handleApplyFilters} className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Input
              id="ticker"
              name="ticker"
              label="Ticker Symbol"
              value={filters.ticker}
              onChange={handleFilterChange}
              placeholder="e.g., AAPL"
              fullWidth
            />

            <div>
              <label htmlFor="tx_type" className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
                Transaction Type
              </label>
              <select
                id="tx_type"
                name="tx_type"
                value={filters.tx_type}
                onChange={handleFilterChange}
                className="block w-full px-4 py-3 text-base rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-slate-900 border-2 border-slate-300 dark:border-slate-700 focus:border-slate-500 dark:focus:border-slate-500 focus:ring-slate-500 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
              >
                <option value="">All Types</option>
                <option value="purchase">Purchase</option>
                <option value="sale">Sale</option>
                <option value="exchange">Exchange</option>
              </select>
            </div>

            <Input
              type="number"
              id="min_amount"
              name="min_amount"
              label="Min Amount ($)"
              value={filters.min_amount}
              onChange={handleFilterChange}
              placeholder="e.g., 50000"
              fullWidth
            />

            <div className="flex items-end gap-3">
              <Button type="submit" variant="primary" size="md" fullWidth>
                Apply
              </Button>
              <Button type="button" onClick={handleClearFilters} variant="secondary" size="md" fullWidth>
                Clear
              </Button>
            </div>
          </form>
        </Card.Body>
      </Card>

      {/* Results Card */}
      <Card>
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="h-12 w-12 animate-spin rounded-full border-3 border-slate-200 dark:border-slate-700 border-t-slate-900 dark:border-t-slate-100"></div>
            <p className="mt-6 text-sm font-medium text-slate-600 dark:text-slate-400">Loading trades...</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-center px-4">
            <svg
              className="h-16 w-16 text-red-400 dark:text-red-500 mb-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <p className="text-base font-semibold text-red-900 dark:text-red-400 mb-2">Error loading trades</p>
            <p className="text-sm text-red-700 dark:text-red-500">{error}</p>
          </div>
        ) : (
          <TransactionTable transactions={transactions} />
        )}
      </Card>
    </>
  );
}
