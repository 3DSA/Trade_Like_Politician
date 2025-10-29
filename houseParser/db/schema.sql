-- Minimal schema for storing House financial disclosure filings.
-- Apply with: psql postgresql://tlp:tlp_password@localhost:5432/tlp_house -f houseParser/db/schema.sql

CREATE TABLE IF NOT EXISTS house_filings (
    doc_id         TEXT PRIMARY KEY,
    filing_year    INTEGER NOT NULL,
    prefix         TEXT,
    first_name     TEXT,
    last_name      TEXT,
    suffix         TEXT,
    filing_type    TEXT,
    state_dst      TEXT,
    filing_date    DATE,
    raw_payload    JSONB,
    ingested_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
