# Senate Trading API

FastAPI backend for serving Senate financial disclosure data from Supabase.

## Setup

### 1. Create Python virtual environment

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and update with your Supabase credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres"
ALLOWED_ORIGINS="http://localhost:3000"
```

### 4. Run the API server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### GET /api/trades/recent
Get recent stock trades with optional filters.

**Query Parameters:**
- `limit` (int, default 100, max 500): Number of trades to return
- `offset` (int, default 0): Pagination offset
- `ticker` (string): Filter by ticker symbol
- `tx_type` (string): Filter by transaction type (purchase, sale, exchange)
- `min_amount` (int): Minimum transaction amount

**Example:**
```
GET /api/trades/recent?ticker=AAPL&limit=50
```

### GET /api/trades/senator/{senator_name}
Get all trades for a specific senator.

**Path Parameters:**
- `senator_name` (string): Senator's full name

**Query Parameters:**
- `limit` (int, default 100, max 500)
- `offset` (int, default 0)

**Example:**
```
GET /api/trades/senator/Warren%2C%20Elizabeth
```

### GET /api/senators
Get list of senators with trading statistics.

**Query Parameters:**
- `limit` (int, default 50, max 200)
- `order_by` (string): Sort by `total_transactions`, `total_volume_estimate`, or `latest_trade`

**Example:**
```
GET /api/senators?order_by=total_volume_estimate&limit=100
```

### GET /api/senators/{senator_name}/stats
Get detailed statistics for a specific senator.

**Example:**
```
GET /api/senators/Warren%2C%20Elizabeth/stats
```

### GET /api/stats
Get overall trading statistics across all senators.

### GET /health
Health check endpoint to verify database connection.

## CORS Configuration

Configure allowed origins in `.env`:
```env
ALLOWED_ORIGINS="http://localhost:3000,https://yourdomain.com"
```

## Production Deployment

For production deployment:

1. Set environment variables securely (don't use `.env` file)
2. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```
3. Configure proper CORS origins
4. Enable HTTPS
5. Set up rate limiting and authentication as needed
