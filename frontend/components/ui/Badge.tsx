import React from 'react';

/**
 * Badge Component - Status and Category Indicators
 *
 * DESIGN DECISIONS:
 * - Transaction type colors aligned with politically neutral palette
 * - Purchase uses teal (not partisan green)
 * - Sale uses amber (not partisan red)
 * - Exchange uses neutral slate
 * - Rounded-full for pill shape (common badge pattern)
 * - Uppercase text with letter-spacing for emphasis and scannability
 * - Font-semibold for clear hierarchy
 * - px-3 py-1 provides comfortable badge proportions
 */

type BadgeVariant = 'purchase' | 'sale' | 'exchange' | 'neutral' | 'info';
type BadgeSize = 'sm' | 'md' | 'lg';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: BadgeSize;
  className?: string;
}

export function Badge({
  children,
  variant = 'neutral',
  size = 'md',
  className = '',
}: BadgeProps) {
  // Base styles
  const baseStyles = 'inline-flex items-center justify-center font-semibold rounded-full uppercase tracking-wide';

  // Variant styles - using design system colors
  const variantStyles: Record<BadgeVariant, string> = {
    purchase: 'bg-purchase-100 text-purchase-800 border border-purchase-200',
    sale: 'bg-sale-100 text-sale-800 border border-sale-200',
    exchange: 'bg-slate-100 text-slate-800 border border-slate-200',
    neutral: 'bg-neutral-100 text-neutral-700 border border-neutral-200',
    info: 'bg-accent-100 text-accent-800 border border-accent-200',
  };

  // Size styles
  const sizeStyles: Record<BadgeSize, string> = {
    sm: 'px-2 py-0.5 text-2xs',
    md: 'px-3 py-1 text-xs',
    lg: 'px-4 py-1.5 text-sm',
  };

  return (
    <span className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}>
      {children}
    </span>
  );
}

/**
 * Specialized badge for transaction types
 * Automatically maps transaction type to correct variant
 */
interface TransactionBadgeProps {
  transactionType: string;
  size?: BadgeSize;
  className?: string;
}

export function TransactionBadge({
  transactionType,
  size = 'md',
  className = '',
}: TransactionBadgeProps) {
  const normalizedType = transactionType.toLowerCase();

  let variant: BadgeVariant = 'neutral';
  let displayText = transactionType;

  if (normalizedType.includes('purchase') || normalizedType.includes('buy')) {
    variant = 'purchase';
    displayText = 'Purchase';
  } else if (normalizedType.includes('sale') || normalizedType.includes('sell')) {
    variant = 'sale';
    displayText = 'Sale';
  } else if (normalizedType.includes('exchange')) {
    variant = 'exchange';
    displayText = 'Exchange';
  }

  return (
    <Badge variant={variant} size={size} className={className}>
      {displayText}
    </Badge>
  );
}
