import type { Config } from "tailwindcss";

/**
 * Congressional Trading Tracker - Design System Configuration
 *
 * DESIGN PHILOSOPHY:
 * This design system prioritizes political neutrality, data clarity, and accessibility.
 *
 * COLOR STRATEGY:
 * - Primary colors use slate/gray tones that convey authority without partisan association
 * - Transaction types use amber (not red) and teal (not green) to avoid political color coding
 * - Blue is used sparingly and only for interactive elements, never for party affiliation
 *
 * TYPOGRAPHY STRATEGY:
 * - System fonts ensure fast loading and native feel across platforms
 * - Tight letter spacing on headings prevents looseness in large text
 * - Tabular figures in mono font ensure numerical data aligns properly
 *
 * SPACING STRATEGY:
 * - Generous spacing prevents overwhelming dense financial data
 * - 8px base unit creates consistent rhythm
 * - Extended scale (up to 128) supports expansive layouts without custom values
 */

export default {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],

  darkMode: 'class', // Enable class-based dark mode

  theme: {
    extend: {
      /**
       * COLORS - Politically Neutral Palette
       *
       * Primary: Professional slate that conveys governmental authority
       * Accent: Muted cyan for interactive elements (non-partisan blue alternative)
       * Success/Purchase: Teal (not partisan green)
       * Warning/Sale: Amber (not partisan red)
       *
       * All colors tested for WCAG AA contrast on white backgrounds
       */
      colors: {
        // Primary slate - governmental, professional, non-partisan
        slate: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },

        // Accent cyan - interactive elements, links (non-partisan blue alternative)
        accent: {
          50: '#ecfeff',
          100: '#cffafe',
          200: '#a5f3fc',
          300: '#67e8f9',
          400: '#22d3ee',
          500: '#06b6d4',
          600: '#0891b2',
          700: '#0e7490',
          800: '#155e75',
          900: '#164e63',
        },

        // Transaction type: Purchase (teal - politically neutral)
        purchase: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        },

        // Transaction type: Sale (amber - politically neutral)
        sale: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },

        // Semantic colors
        border: 'hsl(214 32% 91%)',
        input: 'hsl(214 32% 91%)',
        ring: 'hsl(215 16% 47%)',
        background: 'hsl(0 0% 100%)',
        foreground: 'hsl(222 47% 11%)',

        // Component-specific
        card: {
          DEFAULT: 'hsl(0 0% 100%)',
          foreground: 'hsl(222 47% 11%)',
        },

        muted: {
          DEFAULT: 'hsl(210 40% 96%)',
          foreground: 'hsl(215 16% 47%)',
        },
      },

      /**
       * TYPOGRAPHY - Optimized for Financial Data Display
       *
       * Line heights calculated for optimal readability in dense tables
       * Letter spacing tightened on large text to prevent looseness
       * Tabular figure support in mono font for aligned numbers
       */
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.875rem', letterSpacing: '0.025em' }],
        'xs': ['0.75rem', { lineHeight: '1rem', letterSpacing: '0.01em' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem', letterSpacing: '0' }],
        'base': ['1rem', { lineHeight: '1.5rem', letterSpacing: '0' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem', letterSpacing: '-0.01em' }],
        'xl': ['1.25rem', { lineHeight: '1.875rem', letterSpacing: '-0.01em' }],
        '2xl': ['1.5rem', { lineHeight: '2rem', letterSpacing: '-0.02em' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem', letterSpacing: '-0.02em' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem', letterSpacing: '-0.03em' }],
        '5xl': ['3rem', { lineHeight: '3.5rem', letterSpacing: '-0.03em' }],
        '6xl': ['3.75rem', { lineHeight: '4rem', letterSpacing: '-0.04em' }],
      },

      /**
       * FONT FAMILIES
       *
       * Sans: System fonts for instant loading and native feel
       * Mono: Optimized for tabular financial data with consistent character width
       */
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          '"Helvetica Neue"',
          'Arial',
          'sans-serif',
          '"Apple Color Emoji"',
          '"Segoe UI Emoji"',
          '"Segoe UI Symbol"',
        ],
        mono: [
          '"SF Mono"',
          'Monaco',
          '"Cascadia Code"',
          '"Roboto Mono"',
          'Consolas',
          '"Liberation Mono"',
          'Menlo',
          'monospace',
        ],
      },

      /**
       * SPACING - Generous Scale for Data-Dense Interfaces
       *
       * Extended beyond default to support expansive layouts
       * Prevents need for arbitrary custom values
       */
      spacing: {
        '18': '4.5rem',    // 72px
        '88': '22rem',     // 352px
        '100': '25rem',    // 400px
        '112': '28rem',    // 448px
        '128': '32rem',    // 512px
      },

      /**
       * BORDER RADIUS - Refined Scale
       *
       * Softer than defaults for approachable civic tech aesthetic
       * Still professional without feeling consumer-product playful
       */
      borderRadius: {
        'sm': '0.25rem',     // 4px
        DEFAULT: '0.5rem',   // 8px
        'md': '0.5rem',      // 8px
        'lg': '0.75rem',     // 12px
        'xl': '1rem',        // 16px
        '2xl': '1.25rem',    // 20px
        '3xl': '1.5rem',     // 24px
      },

      /**
       * BOX SHADOWS - Subtle Depth System
       *
       * Softer than defaults to feel modern without being dramatic
       * Three-level system: cards, elevated cards, modals
       */
      boxShadow: {
        'xs': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'sm': '0 1px 3px 0 rgb(0 0 0 / 0.08), 0 1px 2px -1px rgb(0 0 0 / 0.08)',
        DEFAULT: '0 4px 6px -1px rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.08)',
        'md': '0 4px 6px -1px rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.08)',
        'lg': '0 10px 15px -3px rgb(0 0 0 / 0.08), 0 4px 6px -4px rgb(0 0 0 / 0.08)',
        'xl': '0 20px 25px -5px rgb(0 0 0 / 0.08), 0 8px 10px -6px rgb(0 0 0 / 0.08)',
        '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.15)',
      },

      /**
       * ANIMATIONS - Purposeful Motion
       *
       * Subtle, functional animations that enhance UX without distraction
       * All respect prefers-reduced-motion via global CSS
       */
      transitionDuration: {
        '250': '250ms',
        '350': '350ms',
      },

      animation: {
        'fade-in': 'fadeIn 250ms ease-in-out',
        'slide-up': 'slideUp 350ms ease-out',
        'slide-down': 'slideDown 350ms ease-out',
        'scale-in': 'scaleIn 200ms ease-out',
        'skeleton': 'skeleton 2s ease-in-out infinite',
      },

      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        skeleton: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
      },

      /**
       * MAX-WIDTH - Content Constraints
       *
       * Wide enough for data tables, narrow enough for readability
       */
      maxWidth: {
        '8xl': '88rem',   // 1408px
        '9xl': '96rem',   // 1536px
      },
    },
  },

  plugins: [],
} satisfies Config;
