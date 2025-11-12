import React from 'react';

/**
 * Input Component - Form Input with Validation States
 *
 * DESIGN DECISIONS:
 * - Generous padding for readability and touch targets
 * - Slate border colors maintain political neutrality
 * - Error state uses red, success uses teal (from design system)
 * - Floating label pattern considered but rejected for simplicity/accessibility
 * - Helper text positioned below for screen reader flow
 * - Focus ring matches button focus pattern
 * - Disabled state reduces opacity while maintaining readable contrast
 */

type InputVariant = 'default' | 'error' | 'success';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  error?: string;
  variant?: InputVariant;
  fullWidth?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      helperText,
      error,
      variant = 'default',
      fullWidth = false,
      className = '',
      id,
      ...props
    },
    ref
  ) => {
    // Generate unique ID if not provided
    const inputId = id || `input-${React.useId()}`;
    const helperTextId = `${inputId}-helper`;
    const errorId = `${inputId}-error`;

    // Determine actual variant based on error prop
    const actualVariant = error ? 'error' : variant;

    // Base styles
    const baseStyles = 'block px-4 py-3 text-base rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-slate-900 disabled:opacity-60 disabled:cursor-not-allowed disabled:bg-slate-50 dark:disabled:bg-slate-800';

    // Variant styles
    const variantStyles: Record<InputVariant, string> = {
      default: 'border-2 border-slate-300 dark:border-slate-700 focus:border-slate-500 dark:focus:border-slate-500 focus:ring-slate-500 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500',
      error: 'border-2 border-red-400 dark:border-red-600 focus:border-red-600 dark:focus:border-red-500 focus:ring-red-600 dark:focus:ring-red-500 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500',
      success: 'border-2 border-purchase-500 dark:border-purchase-600 focus:border-purchase-600 dark:focus:border-purchase-500 focus:ring-purchase-600 dark:focus:ring-purchase-500 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500',
    };

    // Width styles
    const widthStyles = fullWidth ? 'w-full' : '';

    return (
      <div className={fullWidth ? 'w-full' : ''}>
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2"
          >
            {label}
          </label>
        )}

        <input
          ref={ref}
          id={inputId}
          className={`${baseStyles} ${variantStyles[actualVariant]} ${widthStyles} ${className}`}
          aria-invalid={!!error}
          aria-describedby={
            error
              ? errorId
              : helperText
              ? helperTextId
              : undefined
          }
          {...props}
        />

        {error && (
          <p
            id={errorId}
            className="mt-2 text-sm text-red-700 flex items-start gap-1.5"
            role="alert"
          >
            <svg
              className="h-5 w-5 flex-shrink-0 mt-0.5"
              fill="currentColor"
              viewBox="0 0 20 20"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
                clipRule="evenodd"
              />
            </svg>
            <span>{error}</span>
          </p>
        )}

        {!error && helperText && (
          <p
            id={helperTextId}
            className="mt-2 text-sm text-slate-600"
          >
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
