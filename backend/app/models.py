from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


class Transaction(BaseModel):
    transaction_id: int
    filing_id: int
    doc_id: str
    tx_number: Optional[int]
    tx_date: Optional[date]
    owner: Optional[str]
    ticker: Optional[str]
    asset_name: str
    asset_type: Optional[str]
    rate_coupon: Optional[str]
    maturity_date: Optional[date]
    tx_type: str
    amount_range: Optional[str]
    amount_min: Optional[Decimal]
    amount_max: Optional[Decimal]
    comment: Optional[str]
    row_confidence: Optional[Decimal]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class Filing(BaseModel):
    filing_id: int
    doc_id: str
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    suffix: Optional[str]
    full_name: Optional[str]
    prefix: Optional[str]
    filing_type: str
    report_type: Optional[str]
    filing_date: Optional[date]
    filed_time: Optional[str]
    filing_year: int
    certified: Optional[bool]
    total_transactions: Optional[int]
    ingested_at: Optional[datetime]
    parsed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TransactionWithSenator(Transaction):
    """Transaction enriched with senator information."""
    senator_name: Optional[str]
    filing_date: Optional[date]


class SenatorStats(BaseModel):
    """Statistics for a senator's trading activity."""
    full_name: str
    total_transactions: int
    total_volume_estimate: Optional[Decimal]
    earliest_trade: Optional[date]
    latest_trade: Optional[date]
    total_purchases: Optional[int]
    total_sales: Optional[int]


class TradingStats(BaseModel):
    """Overall trading statistics."""
    total_transactions: int
    total_filings: int
    total_senators: int
    total_volume_estimate: Optional[Decimal]
    date_range_start: Optional[date]
    date_range_end: Optional[date]
