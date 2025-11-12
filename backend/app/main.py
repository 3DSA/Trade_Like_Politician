from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import date
from app.config import settings
from app.database import get_db
from app.models import TransactionWithSenator, SenatorStats, TradingStats
import psycopg.rows

app = FastAPI(
    title="Senate Trading API",
    description="API for viewing Senate financial disclosure data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "message": "Senate Trading API",
        "docs": "/docs",
        "endpoints": {
            "recent_trades": "/api/trades/recent",
            "senator_trades": "/api/trades/senator/{name}",
            "senators": "/api/senators",
            "senator_stats": "/api/senators/{name}/stats",
            "stats": "/api/stats"
        }
    }


@app.get("/api/trades/recent", response_model=List[TransactionWithSenator])
def get_recent_trades(
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    ticker: Optional[str] = None,
    tx_type: Optional[str] = None,
    min_amount: Optional[int] = None,
):
    """Get recent stock trades with senator information."""
    with get_db() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            query = """
                SELECT
                    t.transaction_id,
                    t.filing_id,
                    t.doc_id,
                    t.tx_number,
                    t.tx_date,
                    t.owner,
                    t.ticker,
                    t.asset_name,
                    t.asset_type,
                    t.rate_coupon,
                    t.maturity_date,
                    t.tx_type,
                    t.amount_range,
                    t.amount_min,
                    t.amount_max,
                    t.comment,
                    t.row_confidence,
                    t.created_at,
                    f.full_name as senator_name,
                    f.filing_date
                FROM senate_transactions t
                JOIN senate_filings f ON t.filing_id = f.filing_id
                WHERE t.ticker IS NOT NULL AND t.ticker != '--'
            """

            params = []

            if ticker:
                query += " AND UPPER(t.ticker) = UPPER(%s)"
                params.append(ticker)

            if tx_type:
                query += " AND t.tx_type ILIKE %s"
                params.append(f"%{tx_type}%")

            if min_amount:
                query += " AND t.amount_min >= %s"
                params.append(min_amount)

            query += " ORDER BY t.tx_date DESC NULLS LAST, t.created_at DESC"
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cur.execute(query, params)
            results = cur.fetchall()
            return results


@app.get("/api/trades/senator/{senator_name}", response_model=List[TransactionWithSenator])
def get_senator_trades(
    senator_name: str,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
):
    """Get trades for a specific senator."""
    with get_db() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            query = """
                SELECT
                    t.transaction_id,
                    t.filing_id,
                    t.doc_id,
                    t.tx_number,
                    t.tx_date,
                    t.owner,
                    t.ticker,
                    t.asset_name,
                    t.asset_type,
                    t.rate_coupon,
                    t.maturity_date,
                    t.tx_type,
                    t.amount_range,
                    t.amount_min,
                    t.amount_max,
                    t.comment,
                    t.row_confidence,
                    t.created_at,
                    f.full_name as senator_name,
                    f.filing_date
                FROM senate_transactions t
                JOIN senate_filings f ON t.filing_id = f.filing_id
                WHERE f.full_name ILIKE %s
                ORDER BY t.tx_date DESC NULLS LAST, t.created_at DESC
                LIMIT %s OFFSET %s
            """

            cur.execute(query, [f"%{senator_name}%", limit, offset])
            results = cur.fetchall()

            if not results:
                raise HTTPException(status_code=404, detail="Senator not found")

            return results


@app.get("/api/senators", response_model=List[SenatorStats])
def get_senators(
    limit: int = Query(default=50, le=200),
    order_by: str = Query(default="total_transactions", regex="^(total_transactions|total_volume_estimate|latest_trade)$")
):
    """Get list of senators with trading statistics."""
    # Whitelist valid order_by columns to prevent SQL injection
    valid_order_columns = {
        "total_transactions": "total_transactions",
        "total_volume_estimate": "total_volume_estimate",
        "latest_trade": "latest_trade"
    }

    order_column = valid_order_columns.get(order_by, "total_transactions")

    with get_db() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            # Build query with safe column name interpolation
            query = """
                SELECT
                    f.full_name,
                    COUNT(DISTINCT t.transaction_id) as total_transactions,
                    SUM((t.amount_min + t.amount_max) / 2) as total_volume_estimate,
                    MIN(t.tx_date) as earliest_trade,
                    MAX(t.tx_date) as latest_trade,
                    COUNT(DISTINCT CASE WHEN t.tx_type ILIKE '%%purchase%%' THEN t.transaction_id END) as total_purchases,
                    COUNT(DISTINCT CASE WHEN t.tx_type ILIKE '%%sale%%' THEN t.transaction_id END) as total_sales
                FROM senate_filings f
                LEFT JOIN senate_transactions t ON f.filing_id = t.filing_id
                WHERE t.ticker IS NOT NULL AND t.ticker != '--'
                GROUP BY f.full_name
                HAVING COUNT(DISTINCT t.transaction_id) > 0
                ORDER BY {} DESC NULLS LAST
                LIMIT %s
            """.format(order_column)

            cur.execute(query, [limit])
            results = cur.fetchall()
            return results


@app.get("/api/senators/{senator_name}/stats", response_model=SenatorStats)
def get_senator_stats(senator_name: str):
    """Get detailed statistics for a specific senator."""
    with get_db() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            query = """
                SELECT
                    f.full_name,
                    COUNT(DISTINCT t.transaction_id) as total_transactions,
                    SUM((t.amount_min + t.amount_max) / 2) as total_volume_estimate,
                    MIN(t.tx_date) as earliest_trade,
                    MAX(t.tx_date) as latest_trade,
                    COUNT(DISTINCT CASE WHEN t.tx_type ILIKE '%%purchase%%' THEN t.transaction_id END) as total_purchases,
                    COUNT(DISTINCT CASE WHEN t.tx_type ILIKE '%%sale%%' THEN t.transaction_id END) as total_sales
                FROM senate_filings f
                LEFT JOIN senate_transactions t ON f.filing_id = t.filing_id
                WHERE f.full_name ILIKE %s
                GROUP BY f.full_name
                HAVING COUNT(DISTINCT t.transaction_id) > 0
            """

            cur.execute(query, [f"%{senator_name}%"])
            result = cur.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Senator not found or has no trades")

            return result


@app.get("/api/stats", response_model=TradingStats)
def get_overall_stats():
    """Get overall trading statistics."""
    with get_db() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            query = """
                SELECT
                    COUNT(DISTINCT t.transaction_id) as total_transactions,
                    COUNT(DISTINCT f.filing_id) as total_filings,
                    COUNT(DISTINCT f.full_name) as total_senators,
                    SUM((t.amount_min + t.amount_max) / 2) as total_volume_estimate,
                    MIN(t.tx_date) as date_range_start,
                    MAX(t.tx_date) as date_range_end
                FROM senate_transactions t
                JOIN senate_filings f ON t.filing_id = f.filing_id
                WHERE t.ticker IS NOT NULL AND t.ticker != '--'
            """

            cur.execute(query)
            result = cur.fetchone()
            return result


@app.get("/health")
def health_check():
    """Health check endpoint."""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
