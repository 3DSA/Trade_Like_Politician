'use client';

import { useState } from 'react';
import { Transaction } from '@/types';
import { formatCurrency, formatDate } from '@/lib/utils';
import Link from 'next/link';
import { TransactionBadge } from '@/components/ui/Badge';

/**
 * TransactionTable Component - Financial Data Display
 *
 * DESIGN DECISIONS:
 * - Desktop: Full table with all columns for comprehensive view
 * - Mobile: Card layout for better readability on small screens (progressive disclosure)
 * - Sortable columns with visual indicators for user control
 * - Hover states on rows for interactivity feedback
 * - Monospace font for tickers (tabular figures alignment)
 * - Amount shows midpoint with range details below for context
 * - Empty state with helpful guidance
 * - Sticky header on scroll for context preservation (future enhancement)
 */

interface TransactionTableProps {
  transactions: Transaction[];
}

type SortField = 'tx_date' | 'amount' | 'senator_name' | 'ticker';
type SortDirection = 'asc' | 'desc';

export function TransactionTable({ transactions }: TransactionTableProps) {
  const [sortField, setSortField] = useState<SortField>('tx_date');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  // Empty state
  if (transactions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 px-4 text-center">
        <svg
          className="h-16 w-16 text-neutral-300 dark:text-slate-700 mb-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <p className="text-base text-neutral-700 dark:text-slate-300 font-semibold mb-2">No transactions found</p>
        <p className="text-sm text-neutral-500 dark:text-slate-500">Try adjusting your filters or search criteria</p>
      </div>
    );
  }

  // Sorting logic
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedTransactions = [...transactions].sort((a, b) => {
    let aValue: any;
    let bValue: any;

    // Special handling for amount (use midpoint)
    if (sortField === 'amount') {
      aValue = a.amount_min && a.amount_max ? (a.amount_min + a.amount_max) / 2 : 0;
      bValue = b.amount_min && b.amount_max ? (b.amount_min + b.amount_max) / 2 : 0;
    } else {
      // For other fields, access them from the transaction object
      aValue = a[sortField as keyof Transaction];
      bValue = b[sortField as keyof Transaction];
    }

    // Handle null/undefined
    if (aValue == null) return 1;
    if (bValue == null) return -1;

    // Compare
    if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  return (
    <>
      {/* Desktop table - hidden on mobile */}
      <div className="hidden md:block overflow-x-auto">
        <div className="inline-block min-w-full align-middle">
          <table className="min-w-full divide-y divide-neutral-200/80 dark:divide-slate-800/80">
            <thead>
              <tr className="bg-slate-50/50 dark:bg-slate-800/50">
                <SortableHeader
                  label="Date"
                  field="tx_date"
                  currentField={sortField}
                  direction={sortDirection}
                  onSort={handleSort}
                  className="pl-6 pr-4"
                />
                <SortableHeader
                  label="Senator"
                  field="senator_name"
                  currentField={sortField}
                  direction={sortDirection}
                  onSort={handleSort}
                  className="px-4"
                />
                <SortableHeader
                  label="Ticker"
                  field="ticker"
                  currentField={sortField}
                  direction={sortDirection}
                  onSort={handleSort}
                  className="px-4"
                />
                <th
                  scope="col"
                  className="px-4 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400"
                >
                  Asset
                </th>
                <th
                  scope="col"
                  className="px-4 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400"
                >
                  Type
                </th>
                <SortableHeader
                  label="Amount"
                  field="amount"
                  currentField={sortField}
                  direction={sortDirection}
                  onSort={handleSort}
                  className="px-4"
                />
                <th
                  scope="col"
                  className="px-4 py-4 text-left text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400"
                >
                  Owner
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100 dark:divide-slate-800 bg-white dark:bg-slate-900">
              {sortedTransactions.map((transaction) => (
                <tr
                  key={transaction.transaction_id}
                  className="hover:bg-slate-50/50 dark:hover:bg-slate-800/50 transition-colors duration-150"
                >
                  <td className="whitespace-nowrap py-5 pl-6 pr-4 text-sm text-slate-900 dark:text-slate-100 font-medium">
                    {formatDate(transaction.tx_date)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-5 text-sm">
                    {transaction.senator_name ? (
                      <Link
                        href={`/senator/${encodeURIComponent(transaction.senator_name)}`}
                        className="font-semibold text-slate-900 dark:text-slate-100 hover:text-slate-600 dark:hover:text-slate-400 transition-colors duration-150 underline decoration-slate-300 dark:decoration-slate-600 hover:decoration-slate-600 dark:hover:decoration-slate-400 decoration-2 underline-offset-2"
                      >
                        {transaction.senator_name}
                      </Link>
                    ) : (
                      <span className="text-neutral-400 dark:text-slate-600">—</span>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-4 py-5 text-sm font-mono font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                    {transaction.ticker || <span className="text-neutral-400 dark:text-slate-600">—</span>}
                  </td>
                  <td className="px-4 py-5 text-sm text-slate-600 dark:text-slate-400 max-w-xs truncate" title={transaction.asset_name}>
                    {transaction.asset_name}
                  </td>
                  <td className="whitespace-nowrap px-4 py-5 text-sm">
                    <TransactionBadge transactionType={transaction.tx_type} size="md" />
                  </td>
                  <td className="whitespace-nowrap px-4 py-5 text-sm">
                    {transaction.amount_min && transaction.amount_max ? (
                      <div>
                        <div className="font-semibold text-slate-900 dark:text-slate-100">
                          {formatCurrency((transaction.amount_min + transaction.amount_max) / 2)}
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-500 mt-1">{transaction.amount_range}</div>
                      </div>
                    ) : (
                      <span className="text-neutral-400 dark:text-slate-600">{transaction.amount_range || '—'}</span>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-4 py-5 text-sm text-slate-600 dark:text-slate-400 capitalize">
                    {transaction.owner?.replace('_', ' ') || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mobile card layout - shown only on mobile */}
      <div className="md:hidden space-y-4">
        {sortedTransactions.map((transaction) => (
          <div
            key={transaction.transaction_id}
            className="bg-white dark:bg-slate-900 border border-neutral-200/60 dark:border-slate-800/60 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow duration-200"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                {transaction.senator_name ? (
                  <Link
                    href={`/senator/${encodeURIComponent(transaction.senator_name)}`}
                    className="font-semibold text-base text-slate-900 dark:text-slate-100 hover:text-slate-600 dark:hover:text-slate-400 transition-colors underline decoration-slate-300 dark:decoration-slate-600 hover:decoration-slate-600 dark:hover:decoration-slate-400 decoration-2 underline-offset-2"
                  >
                    {transaction.senator_name}
                  </Link>
                ) : (
                  <span className="text-neutral-400 dark:text-slate-600">Unknown</span>
                )}
                <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">{formatDate(transaction.tx_date)}</p>
              </div>
              <TransactionBadge transactionType={transaction.tx_type} size="sm" />
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-xs text-slate-500 dark:text-slate-500 uppercase tracking-wide font-semibold mb-1">Ticker & Asset</p>
                <p className="text-sm font-mono font-bold text-slate-900 dark:text-slate-100">
                  {transaction.ticker || <span className="text-neutral-400 dark:text-slate-600">—</span>}
                </p>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 line-clamp-2">{transaction.asset_name}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-500 uppercase tracking-wide font-semibold mb-1">Amount</p>
                  {transaction.amount_min && transaction.amount_max ? (
                    <>
                      <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                        {formatCurrency((transaction.amount_min + transaction.amount_max) / 2)}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-500 mt-0.5">{transaction.amount_range}</p>
                    </>
                  ) : (
                    <p className="text-sm text-neutral-400 dark:text-slate-600">{transaction.amount_range || '—'}</p>
                  )}
                </div>

                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-500 uppercase tracking-wide font-semibold mb-1">Owner</p>
                  <p className="text-sm text-slate-600 dark:text-slate-400 capitalize">
                    {transaction.owner?.replace('_', ' ') || '—'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

// Sortable table header component
interface SortableHeaderProps {
  label: string;
  field: SortField;
  currentField: SortField;
  direction: SortDirection;
  onSort: (field: SortField) => void;
  className?: string;
}

function SortableHeader({
  label,
  field,
  currentField,
  direction,
  onSort,
  className = '',
}: SortableHeaderProps) {
  const isActive = currentField === field;

  return (
    <th scope="col" className={`py-4 text-left ${className}`}>
      <button
        onClick={() => onSort(field)}
        className="group inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors duration-150"
        aria-label={`Sort by ${label}`}
        aria-sort={isActive ? (direction === 'asc' ? 'ascending' : 'descending') : 'none'}
      >
        {label}
        <span className={`transition-all duration-200 ${isActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-50'}`}>
          {isActive && direction === 'asc' ? (
            <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          )}
        </span>
      </button>
    </th>
  );
}
