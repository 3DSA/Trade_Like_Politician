# Senate Trading Frontend

Next.js frontend for visualizing Senate financial disclosure data, similar to Capitol Trades.

## Features

- **Recent Trades Dashboard**: View and filter recent stock trades from senators
- **Senator Profiles**: Individual senator pages with trading statistics and history
- **Statistics Overview**: Aggregate statistics across all senators
- **Filtering & Sorting**: Filter by ticker, transaction type, amount, and sort by various metrics
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS

## Setup

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. Configure environment variables

The `.env.local` file is already created with default settings:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production, update this to your backend API URL.

### 3. Run the development server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Pages

### Home (/)
Recent trades dashboard with filtering options:
- Filter by ticker symbol
- Filter by transaction type (purchase/sale/exchange)
- Filter by minimum amount
- View senator name, ticker, asset, type, amount, and owner

### Senators (/senators)
List of all senators with trading activity:
- Total transactions count
- Number of purchases and sales
- Estimated trading volume
- Latest trade date
- Sort by transactions, volume, or recent activity

### Senator Profile (/senator/[name])
Individual senator page showing:
- Trading statistics cards (total trades, volume, purchases, sales)
- Complete transaction history
- Click senator name from any trade to view their profile

### Statistics (/stats)
Overall statistics dashboard:
- Total transactions across all senators
- Total estimated trading volume
- Number of senators with trades
- Total filings processed
- Date range of available data

## Components

### TransactionTable
Reusable table component for displaying transactions with:
- Formatted dates and currency
- Color-coded transaction types
- Clickable senator names
- Responsive design

## Utilities

### lib/api.ts
API client functions for all backend endpoints.

### lib/utils.ts
Helper functions for:
- Currency formatting
- Date formatting
- Transaction type color coding
- Transaction type text formatting

## Building for Production

```bash
npm run build
npm start
```

The optimized production build will be created in the `.next` folder.

## Technology Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **State Management**: React hooks (useState, useEffect)

## Customization

### Styling
Modify `tailwind.config.ts` to customize colors and themes.

### API Configuration
Update `lib/api.ts` to add new endpoints or modify request logic.

### Layout
Edit `app/layout.tsx` to customize the navigation and overall layout.
