import React from 'react';

/**
 * Card Component - Consistent Container for Grouped Information
 *
 * DESIGN DECISIONS:
 * - Three-section structure (header, body, footer) with optional sections
 * - Soft shadows from design system for subtle depth
 * - Generous padding (p-8) prevents cramped feeling with dense data
 * - Border uses neutral-200 for soft separation without harshness
 * - Header includes optional description for progressive disclosure
 * - Hover variant adds subtle shadow lift for interactive cards
 * - Footer uses border-top separator, optional for flexibility
 */

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}

interface CardHeaderProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

interface CardBodyProps {
  children: React.ReactNode;
  className?: string;
}

interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className = '', hover = false }: CardProps) {
  const hoverStyles = hover
    ? 'hover:shadow-xl dark:hover:shadow-slate-900/50 transition-shadow duration-300 cursor-pointer'
    : '';

  return (
    <div
      className={`rounded-2xl border border-neutral-200/60 dark:border-slate-800/60 bg-white dark:bg-slate-900 shadow-lg shadow-neutral-200/50 dark:shadow-slate-900/50 overflow-hidden transition-colors duration-300 ${hoverStyles} ${className}`}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  title,
  description,
  action,
  className = '',
}: CardHeaderProps) {
  return (
    <div className={`px-8 py-6 border-b border-neutral-200/80 dark:border-slate-800/80 ${className}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-slate-100">{title}</h2>
          {description && (
            <p className="text-sm text-neutral-600 dark:text-slate-400 mt-1">{description}</p>
          )}
        </div>
        {action && <div className="ml-4 flex-shrink-0">{action}</div>}
      </div>
    </div>
  );
}

export function CardBody({ children, className = '' }: CardBodyProps) {
  return <div className={`px-8 py-6 ${className}`}>{children}</div>;
}

export function CardFooter({ children, className = '' }: CardFooterProps) {
  return (
    <div
      className={`px-8 py-6 border-t border-neutral-200/80 dark:border-slate-800/80 bg-neutral-50/50 dark:bg-slate-800/50 ${className}`}
    >
      {children}
    </div>
  );
}

/**
 * Compound Component Pattern
 * Allows flexible composition:
 *
 * <Card>
 *   <CardHeader title="Title" description="Description" />
 *   <CardBody>Content</CardBody>
 *   <CardFooter>Actions</CardFooter>
 * </Card>
 *
 * Or simple usage:
 *
 * <Card>
 *   <div className="p-8">Simple content</div>
 * </Card>
 */
Card.Header = CardHeader;
Card.Body = CardBody;
Card.Footer = CardFooter;
