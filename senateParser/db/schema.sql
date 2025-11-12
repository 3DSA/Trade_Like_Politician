-- Schema for storing Senate financial disclosure filings (eFD system)
-- Apply with: psql postgresql://tlp:tlp_password@localhost:5432/tlp_senate -f senateParser/db/schema.sql

-- Drop existing tables if recreating
-- DROP TABLE IF EXISTS senate_transactions CASCADE;
-- DROP TABLE IF EXISTS senate_filings CASCADE;

-- ============================================================================
-- FILINGS TABLE
-- ============================================================================
-- Stores metadata for each Senate financial disclosure filing
CREATE TABLE IF NOT EXISTS senate_filings (
    filing_id       SERIAL PRIMARY KEY,
    doc_id          TEXT UNIQUE NOT NULL,           -- UUID from Senate eFD (e.g., f87f8a40-efa5-43df-ad71-56327f5a18ce)

    -- Member information
    first_name      TEXT,
    middle_name     TEXT,
    last_name       TEXT,
    suffix          TEXT,
    full_name       TEXT,                           -- As displayed in portal (e.g., "McCormick, David H.")
    prefix          TEXT,                           -- "Mr.", "Mrs.", "Hon.", etc.

    -- Filing metadata
    filing_type     TEXT NOT NULL,                  -- 'ptr', 'annual', 'candidate', etc.
    report_type     TEXT,                           -- e.g., "Periodic Transaction Report for 10/10/2025"
    filing_date     DATE,                           -- Date filed
    filed_time      TEXT,                           -- Time filed (e.g., "7:40 PM")
    filing_year     INTEGER NOT NULL,

    -- Certification statement
    certified       BOOLEAN DEFAULT FALSE,          -- Whether filer checked certification box
    certification_text TEXT,                        -- Full certification statement

    -- Transaction summary
    total_transactions INTEGER,                     -- Total number of transactions in filing
    self_transactions  INTEGER,                     -- Count of "Self" owner transactions
    joint_transactions INTEGER,                     -- Count of "Joint" owner transactions
    spouse_transactions INTEGER,                    -- Count of "Spouse" owner transactions
    dependent_transactions INTEGER,                 -- Count of "Dependent Child" owner transactions

    -- Processing metadata
    pdf_path        TEXT,                           -- Local path to generated PDF
    pdf_sha256      TEXT,                           -- SHA256 hash of PDF
    parse_version   TEXT,                           -- Parser version used
    parse_quality   DECIMAL(3,2),                   -- 0.00 to 1.00 confidence score

    -- Raw data for auditability
    raw_payload     JSONB,                          -- Full HTML/JSON payload
    source_url      TEXT,                           -- View page URL

    -- Timestamps
    ingested_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    parsed_at       TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- TRANSACTIONS TABLE
-- ============================================================================
-- Individual stock/asset transactions from PTR filings
CREATE TABLE IF NOT EXISTS senate_transactions (
    transaction_id  SERIAL PRIMARY KEY,
    filing_id       INTEGER NOT NULL REFERENCES senate_filings(filing_id) ON DELETE CASCADE,
    doc_id          TEXT NOT NULL REFERENCES senate_filings(doc_id) ON DELETE CASCADE,

    -- Transaction details
    tx_number       INTEGER,                        -- Transaction # within filing (1, 2, 3, etc.)
    tx_date         DATE,                           -- Transaction date (e.g., 09/10/2025)
    owner           TEXT,                           -- 'Self', 'Spouse', 'Joint', 'Dependent Child'

    -- Asset information
    ticker          TEXT,                           -- Stock ticker (if applicable, often '--' for bonds/munis)
    asset_name      TEXT NOT NULL,                  -- Full asset name (e.g., "HILTON WORLDWIDE FINANCE")
    asset_type      TEXT,                           -- 'Corporate Bond', 'Municipal Security', 'Stock', 'Fund', etc.

    -- Bond-specific fields (NULL for stocks)
    rate_coupon     TEXT,                           -- Interest rate/coupon (e.g., "4.875%")
    maturity_date   DATE,                           -- Bond maturity date

    -- Transaction type and amount
    tx_type         TEXT NOT NULL,                  -- 'Purchase', 'Sale (Full)', 'Sale (Partial)', 'Exchange'
    amount_range    TEXT,                           -- Original range text (e.g., "$250,001 - $500,000")
    amount_min      DECIMAL(15,2),                  -- Parsed min value
    amount_max      DECIMAL(15,2),                  -- Parsed max value

    -- Additional fields
    comment         TEXT,                           -- Any comments/notes ('--' if none)

    -- Data quality tracking
    row_confidence  DECIMAL(3,2),                   -- 0.00 to 1.00 confidence in extraction

    -- Timestamps
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Filings indexes
CREATE INDEX IF NOT EXISTS idx_senate_filings_doc_id ON senate_filings(doc_id);
CREATE INDEX IF NOT EXISTS idx_senate_filings_year ON senate_filings(filing_year);
CREATE INDEX IF NOT EXISTS idx_senate_filings_name ON senate_filings(last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_senate_filings_type ON senate_filings(filing_type);
CREATE INDEX IF NOT EXISTS idx_senate_filings_date ON senate_filings(filing_date DESC);

-- Transactions indexes
CREATE INDEX IF NOT EXISTS idx_senate_tx_filing ON senate_transactions(filing_id);
CREATE INDEX IF NOT EXISTS idx_senate_tx_doc_id ON senate_transactions(doc_id);
CREATE INDEX IF NOT EXISTS idx_senate_tx_date ON senate_transactions(tx_date DESC);
CREATE INDEX IF NOT EXISTS idx_senate_tx_ticker ON senate_transactions(ticker) WHERE ticker IS NOT NULL AND ticker != '--';
CREATE INDEX IF NOT EXISTS idx_senate_tx_asset_type ON senate_transactions(asset_type);
CREATE INDEX IF NOT EXISTS idx_senate_tx_owner ON senate_transactions(owner);
CREATE INDEX IF NOT EXISTS idx_senate_tx_type ON senate_transactions(tx_type);

-- Composite index for timeline queries
CREATE INDEX IF NOT EXISTS idx_senate_tx_timeline ON senate_transactions(tx_date DESC, owner, tx_type);

-- ============================================================================
-- CONSTRAINTS
-- ============================================================================

-- Ensure we don't have duplicate transactions within a filing
CREATE UNIQUE INDEX IF NOT EXISTS idx_senate_tx_unique
    ON senate_transactions(doc_id, tx_number)
    WHERE tx_number IS NOT NULL;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE senate_filings IS 'Senate financial disclosure filings from eFD portal';
COMMENT ON COLUMN senate_filings.doc_id IS 'UUID identifier from Senate eFD system';
COMMENT ON COLUMN senate_filings.filing_type IS 'ptr=Periodic Transaction Report, annual=Annual Report, candidate=Candidate Report';
COMMENT ON COLUMN senate_filings.raw_payload IS 'Original HTML/JSON for audit trail and reprocessing';

COMMENT ON TABLE senate_transactions IS 'Individual transactions extracted from Senate PTR filings';
COMMENT ON COLUMN senate_transactions.ticker IS 'Stock ticker; often -- for bonds/municipal securities';
COMMENT ON COLUMN senate_transactions.asset_type IS 'Corporate Bond, Municipal Security, Stock, Mutual Fund, etc.';
COMMENT ON COLUMN senate_transactions.owner IS 'Self, Spouse, Joint, or Dependent Child';
COMMENT ON COLUMN senate_transactions.tx_type IS 'Purchase, Sale (Full), Sale (Partial), Exchange';
COMMENT ON COLUMN senate_transactions.rate_coupon IS 'Interest rate for bonds (NULL for stocks)';
COMMENT ON COLUMN senate_transactions.maturity_date IS 'Maturity date for bonds (NULL for stocks)';
