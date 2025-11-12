# Quick Start Guide - Senate Trading Dashboard

This guide will help you quickly get the backend API and frontend dashboard running.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase account with Senate data loaded (see [SUPABASE_SETUP.md](SUPABASE_SETUP.md))

## 1. Backend Setup (FastAPI)

### Install dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configure environment

Create `.env` file in the `backend` directory:

```env
DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres"
ALLOWED_ORIGINS="http://localhost:3000"
```

Use your Supabase credentials from the root `.env` file.

### Run the API server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive API docs**: http://localhost:8000/docs

## 2. Frontend Setup (Next.js)

### Install dependencies

```bash
cd frontend
npm install
```

### Configure environment

The `.env.local` file is already created with:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Run the development server

```bash
npm run dev
```

The dashboard will be available at: **http://localhost:3000**

## 3. Using the Dashboard

### Recent Trades Page (/)
- View the latest stock trades from senators
- Filter by ticker symbol, transaction type, or minimum amount
- Click on any senator's name to view their profile

### Senators Page (/senators)
- See all senators with trading activity
- View statistics: total trades, purchases, sales, estimated volume
- Sort by transactions, volume, or recent activity

### Senator Profile (/senator/[name])
- Individual senator's trading statistics
- Complete transaction history
- Total trades, volume, purchases, and sales

### Statistics Page (/stats)
- Overall trading statistics
- Total transactions, volume, senators, filings
- Date range of available data

## API Endpoints

### GET /api/trades/recent
Get recent trades with optional filters.

**Example:**
```bash
curl "http://localhost:8000/api/trades/recent?ticker=AAPL&limit=10"
```

### GET /api/senators
Get list of senators with statistics.

**Example:**
```bash
curl "http://localhost:8000/api/senators?order_by=total_volume_estimate&limit=20"
```

### GET /api/stats
Get overall statistics.

**Example:**
```bash
curl "http://localhost:8000/api/stats"
```

## Troubleshooting

### Backend won't start
- Check that Supabase credentials are correct in `.env`
- Verify database connection: `python -c "import psycopg; psycopg.connect('YOUR_DATABASE_URL')"`
- Check port 8000 is not already in use

### Frontend shows errors
- Ensure backend is running on port 8000
- Check browser console for detailed error messages
- Verify `NEXT_PUBLIC_API_URL` is set correctly

### No data showing
- Verify you've run the Senate scraper and loaded data into Supabase
- Check API health endpoint: http://localhost:8000/health
- Run a test query in Supabase SQL editor: `SELECT COUNT(*) FROM senate_transactions;`

## Next Steps

1. **Populate more data**: Run the Senate scraper for more date ranges
2. **Customize the UI**: Edit components in `frontend/components/` and `frontend/app/`
3. **Add features**: Extend API endpoints in `backend/app/main.py`
4. **Deploy**: See individual README files in `backend/` and `frontend/` for production deployment

## Project Structure

```
Trade_Like_Politician/
├── backend/              # FastAPI server
│   ├── app/
│   │   ├── main.py      # API routes
│   │   ├── models.py    # Pydantic models
│   │   ├── database.py  # Database connection
│   │   └── config.py    # Configuration
│   └── requirements.txt
├── frontend/             # Next.js dashboard
│   ├── app/             # Pages (App Router)
│   ├── components/      # React components
│   ├── lib/             # API client and utilities
│   ├── types/           # TypeScript types
│   └── package.json
└── senateParser/        # Data scraper
    └── senate_ptr_scraper.py
```

## Documentation

- [Backend README](backend/README.md) - Detailed API documentation
- [Frontend README](frontend/README.md) - Frontend development guide
- [Supabase Setup](SUPABASE_SETUP.md) - Database setup and scraper usage
- [Main README](README.md) - Full project vision and architecture

---

**Built with:** FastAPI • Next.js • TypeScript • Tailwind CSS • Supabase
