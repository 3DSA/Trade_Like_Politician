-- Minimal schema for storing Senate financial disclosure filings.
-- Apply with: psql postgresql://tlp:tlp_password@localhost:5432/tlp_senate -f senateParser/db/schema.sql

CREATE TABLE IF NOT EXISTS senate_filings (
    doc_id          TEXT PRIMARY KEY,
    filing_year     INTEGER NOT NULL,
    first_name      TEXT,
    last_name       TEXT,
    filing_type     TEXT,
    state           TEXT,
    filing_date     DATE,
    report_type     TEXT,
    pdf_url         TEXT,
    pdf_sha256      TEXT,
    parse_version   TEXT,
    parse_quality   FLOAT,
    raw_payload     JSONB,
    ingested_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (doc_id, filing_year)
);

CREATE TABLE IF NOT EXISTS senate_transactions (
    tx_id           SERIAL PRIMARY KEY,
    doc_id          TEXT REFERENCES senate_filings(doc_id),
    tx_date         DATE,
    owner          TEXT,
    ticker         TEXT,
    asset_name     TEXT,
    tx_type        TEXT,
    amount_min     NUMERIC,
    amount_max     NUMERIC,
    comment        TEXT,
    row_conf       FLOAT,
    ingested_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (doc_id, tx_date, owner, ticker, tx_type)
);

CREATE INDEX IF NOT EXISTS idx_senate_filings_year ON senate_filings(filing_year);
CREATE INDEX IF NOT EXISTS idx_senate_transactions_date ON senate_transactions(tx_date);
CREATE INDEX IF NOT EXISTS idx_senate_transactions_ticker ON senate_transactions(ticker);