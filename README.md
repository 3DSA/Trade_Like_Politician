# Congressional Trade Transparency Platform — Full Implementation Plan

This repository contains the design and implementation plan for a Congressional Trade Transparency Platform: a data-driven, explainable system that scrapes official U.S. House and Senate financial disclosures, normalizes them, computes conflict-of-interest (COI) scores with provenance, and visualizes findings through an interactive dashboard.

## 1. Project Overview

Objective:
Develop a web-based, data-driven transparency platform that scrapes official Congressional stock trading disclosures from U.S. House and Senate portals, parses and normalizes the data, detects potential conflicts of interest (COIs) using rule-based and contextual logic, and visualizes findings interactively through graphs, timelines, and explainable scores.

Key Design Principles:
- Primary data only (no aggregators)
- Transparency-first architecture (auditability and provenance)
- Explainable conflict detection
- Modular, fault-tolerant AWS-based pipeline

## 2. Core Objectives
1. Daily ingestion of filings from official House and Senate portals.
2. Parsing and normalization of PDF disclosures into structured form.
3. Data lineage and confidence tracking for transparency and reproducibility.
4. Conflict-of-Interest scoring using committee mappings and enrichment data.
5. Visualization dashboard (Next.js frontend) showing daily summaries, stock charts, and conflicts.
6. Contextual enrichment — bills, contracts, and sector overlap.
7. Resilient architecture with parser drift monitoring, reprocessing, and alerts.

## 3. System Architecture

Layer / Components
- Ingestion: AWS Lambda, Step Functions, EventBridge
- Parsing/OCR: pdfplumber + AWS Textract (fallback)
- Storage: AWS Aurora PostgreSQL + S3
- Enrichment: Fargate Batch for bill/contract analysis
- Backend: FastAPI (Python 3.11)
- Frontend: Next.js + TypeScript
- Caching: Redis (ElastiCache)
- Monitoring: CloudWatch + Schema Drift Detection
- Infrastructure: Terraform (IaC)

## 4. Data Ingestion Pipeline

Sources
- House Clerk PTR filings: https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure
- Senate eFD filings: https://efdsearch.senate.gov/search/

Pipeline Steps
1. Scheduler: EventBridge triggers daily Step Function.
2. Indexer Lambdas: Scrape new filings since last run.
3. HTML Schema Detector: Validates DOM structure; raises alerts on layout drift.
4. Downloader Lambdas: Fetch PDFs, compute SHA256, store in S3.
5. Parser Workers:
   - Primary: pdfplumber for table extraction
   - Fallback: Textract for scanned documents
6. Validator & Loader: Normalize data → Aurora PostgreSQL.
7. Deduplication: Detect amended or duplicate filings via SHA256 and text comparison.
8. Audit Logging: Record every ingestion event and parser version.

Improvements Implemented

| Gap | Solution |
|---|---|
| HTML schema changes | Schema drift detector job before scraping |
| Duplicate filings | Deduplication logic using SHA256 + amendment text detection |
| OCR errors | AWS Textract for structured text parsing |
| Name disambiguation | Bioguide ID + multi-attribute matching |
| Parser version drift | parse_version field and nightly reprocessing queue |
| Parse failure alerting | CloudWatch alarm <95% parse success |

## 5. Data Model (Aurora PostgreSQL)

Core Tables (high level)
- `persons(person_id, full_name, chamber, state, district, bioguide_id)`
- `committees(committee_id, chamber, name, jurisdiction)`
- `committee_assignments(person_id, committee_id, start_date, end_date, valid_from, valid_to)`
- `issuers(issuer_id, name, cik, sector, industry, naics)`
- `symbols_ref(ticker, issuer_id, exchange, name_observed, as_of_date)`
- `filings(filing_id, source_system, filing_type, person_id, report_date, filing_url, s3_uri, sha256, parse_version, parse_quality)`
- `transactions(tx_id, filing_id, tx_date, tx_type, amount_min, amount_max, asset_text, ticker_observed, issuer_id, ticker_conf, row_conf)`
- `conflict_scores(tx_id, committee_hit, jurisdiction_overlap, position_size_norm, bill_overlap_score, contract_exposure_score, delay_days, score, explain_json)`
- `daily_summaries(summary_date, total_trades, total_estimated_volume, high_conflict_count, top_sectors_json)`

Schema Enhancements

| Gap | Solution |
|---|---|
| Missing time-valid committee mappings | Added `valid_from`, `valid_to` columns |
| Parser lineage missing | Added `parse_version` column |
| Confidence aggregation missing | Introduced stored procedure: tx_conf = min(parse_quality, ticker_conf, row_conf) |
| Amendment tracking | Added `filing_supersedes` field |
| Audit missing | Added `audit_log` table for ingestion & enrichment |
| Low performance joins | Added materialized views (`mv_recent_trades`, `mv_conflict_leaderboard`) |

## 6. Parsing Framework

Implementation Details
- Modular parsers per chamber (e.g. `house_parser.py`, `senate_parser.py`).
- Confidence-based fallback to OCR pipeline.
- Regex extraction for transaction rows (amount, ticker, date, type).
- Fuzzy company name → ticker mapping (via `symbols_ref`).
- `parse_errors` table storing failed or low-confidence runs.

Solutions to Known Parsing Problems

| Problem | Fix |
|---|---|
| Inconsistent tables | Parser templates per source |
| Scanned PDFs | Textract-based OCR fallback |
| Ambiguous tickers | Fuzzy match + manual review table |
| Data gaps | Parser confidence scoring |
| Filing amendments | Hash comparison + supersedes link |
| Parser bugs | Nightly reprocessing job for old versions |
| Parser drift | Daily schema validation and alert if DOM or text structure changes |

## 7. Conflict-of-Interest Engine

Purpose

Compute a transparent and reproducible score indicating potential conflicts between an official’s roles and their stock trades.

Inputs
- Committee memberships
- Committee → Sector mapping
- Issuer industries
- Disclosure delay
- Trade amount

Static Mapping Example (conceptual)

```
{
  "House Energy & Commerce": ["Healthcare", "Pharma", "Insurance"],
  "Senate Armed Services": ["Defense", "Aerospace", "Cybersecurity"],
  "House Agriculture": ["Commodities", "Farming", "Food"]
}
```

Conflict Score (example formula)

committee_hit        = 1 if overlap exists
jurisdiction_overlap = degree of overlap (0–1)
position_size_norm   = log10(midpoint(amount_range)) / 6
delay_days           = report_date - tx_date
bill_overlap_score   = overlap with active legislation
contract_exposure_score = issuer involved in government contracts

score = 0.35*committee_hit
      + 0.20*jurisdiction_overlap
      + 0.15*position_size_norm
      + 0.15*bill_overlap_score
      + 0.10*contract_exposure_score
      + 0.05*(1 - delay_days/60)

Explain JSON Example

```
{
  "committee_match": ["House Energy & Commerce"],
  "bill_context": "HR-105 healthcare pricing reform under same committee",
  "contract_overlap": "Issuer received $5M DoD contract (USAspending.gov)",
  "trade_size_usd": 15000,
  "delay_days": 18,
  "confidence": 0.92
}
```

Enhancements & Gap Fixes

| Gap | Solution |
|---|---|
| Static sector mapping | Auto-update via scraped committee jurisdiction text (keyword-based) |
| No policy context | Bill scraper (Congress.gov API) adds `bill_overlap_score` |
| Missing contract data | USAspending.gov integration adds `contract_exposure_score` |
| Heuristic weights only | Weight calibration via regression on backtested data |
| False positives | Baseline control group for comparison |
| No confidence weighting | Weight COI scores by aggregated transaction confidence |

## 8. Backend (FastAPI)

Endpoints (high-level)
- `/members/search?q=` — Autocomplete search
- `/members/{id}` — Member overview
- `/members/{id}/trades?...` — Fetch trades with filters
- `/prices/{ticker}?start&end` — Get OHLC candles
- `/members/{id}/trades/{tx_id}/performance` — Post-trade returns (7/30/90 days)
- `/summary/daily?date=` — Daily summary
- `/conflicts?date=` — Top conflict scores daily
- `/admin/reprocess` — Trigger reparsing for low-confidence filings

Improvements

| Gap | Solution |
|---|---|
| Query lag | Pre-aggregated views + indexes |
| Rate limits | IP throttling & CloudFront caching |
| Security | JWT + rate limit middleware |
| Version tracking | Include `X-Data-Version` header |
| Cache redundancy | Redis TTL (24h) for price and performance endpoints |

## 9. Market Data Integration

MarketData Abstraction (concept)

class MarketData:
    def candles(self, ticker, start, end, interval="1d"): ...
    def benchmark(self, start, end, symbol="SPY"): ...

Features
- Adjusted close prices only.
- Benchmark overlay (SPY, sector ETF).
- Prefetched daily cache for top-traded tickers.
- Redis layer for 24h caching.

Gap Fixes

| Gap | Solution |
|---|---|
| Rate limit from data source | Fallback providers + cache layer |
| Inconsistent timestamps | Round to nearest market day |
| Missing holiday handling | Adjust window automatically via trading calendar |

## 10. Frontend (Next.js + TypeScript)

Pages
- Home Dashboard — Daily summary, top conflicts, volume stats
- Member Explorer — Bio, committees, trades, COI timeline
- Trade Details — Filing info, explainable COI score, stock graph
- Conflict Feed — Filtered list by score, sector, chamber
- Timeline View — Chronological view of trades vs. policy events
- Admin QA Panel — Confidence audit and reparse trigger

UI Enhancements

| Gap | Solution |
|---|---|
| Limited filters | Add sector, committee, conflict score, delay range filters |
| Missing timeline | Interactive axis with events + filings |
| Low data transparency | Confidence color badges + source link |
| Context missing | Hover tooltips showing COI rationale |
| No narrative insight | LangChain agent-generated daily summary (“Story Mode”) |

## 11. Data Enrichment & Intelligence Modules

Module / Function
- Committee Updater — Monthly refresh of Congress.gov rosters
- Bill Tracker — Maps active bills to sectors via NLP keywords
- Contract Linker — Joins issuers with USAspending.gov contracts
- Donor Overlay (Optional) — Pulls OpenSecrets donor data
- Anomaly Detector (Phase 3) — Detects unusual trade timing patterns
- LangChain Narrative Agent — Auto-generates summaries and contextual insights

## 12. Observability & Quality Control

Monitoring Metrics
- Parse success %
- Parser drift detection (schema change)
- Avg. parse time
- Ingestion latency
- COI scoring success rate
- Confidence distribution

Data Audits
- Weekly checksum validation (S3 vs DB SHA256)
- Reconciliation of scraped vs. official filing counts
- Daily parser pattern drift test (deviation > 2σ → alert)
- Billing alarms for AWS cost control

Regression Testing
- “Golden dataset” of verified PTRs for CI/CD parser testing.
- Automated diff reports for parser output drift.

## 13. Scalability and Cost Optimization

| Issue | Fix |
|---|---|
| OCR Lambda timeouts | Offload to Fargate or AWS Batch |
| High PDF volume | Split queues by chamber/date |
| Storage costs | Lifecycle rule: archive parsed JSON to Glacier |
| API load | Read replicas + Redis caching |
| GPU OCR cost | Spot instance orchestration for heavy OCR workloads |

## 14. Legal, Ethical, and Transparency Measures

Risk / Mitigation
- Implication of misconduct — Add clear disclaimer: “COI score ≠ evidence of wrongdoing.”
- Misinterpretation of timeliness — Display “Reported X days after transaction” in all UI views
- PII exposure — Use only publicly available STOCK Act data
- Data misrepresentation — Show provenance: link, SHA256, parser version
- Transparency — Public API documentation and open dataset exports
- Right to respond — Optional feedback contact for congressional offices

## 15. Roadmap & Phase Summary

Phase / Focus / Key Deliverables
- Phase 1 (MVP) — Core ingestion, parser, DB, COI v1, UI summary — Parsing + FastAPI + Next.js dashboard
- Phase 2 (Contextual Intelligence) — Enrichment (bills, contracts), caching, trends — Ontology updates, bill tracking, caching
- Phase 3 (Insights & AI) — LangChain narrative, anomaly detection, Congress Alpha Index — Story Mode, Influence Timeline
- Phase 4 (Production & Governance) — Parser monitoring, alerts, public dataset export — Schema drift detection, audit dashboards
- Phase 5 (Open Research Platform) — Public API + academic access — API documentation portal + open data release

## 16. Example Daily Output

Date: October 25, 2025
- New Filings: 14
- Total Trades: 102
- Volume: $5.1M
- Top Sector: Healthcare (29%)
- Average Delay: 18 days
- Top Conflict: Rep. Mike Moore → CNC (COI: 0.73)
- Context: Energy & Commerce Committee oversight on healthcare pricing reform (HR-105).

## 17. Long-Term Evolution

Phase 3–5 Additions
- Influence Timeline: Overlay trades with legislative votes.
- Congress Alpha Index: Backtest “follow-the-Congress” performance.
- Cross-Member Network Graph: Graph visualization (Neo4j) of trading overlaps.
- Transparency Index: Score combining disclosure delay, conflict frequency, parse confidence.
- Public Data Portal: Daily Parquet exports for journalists and researchers.

---

## Final Deliverable Vision

You’ll have a transparent, self-healing, explainable, and ethically grounded system that:
1. Scrapes primary Congressional trade data daily.
2. Parses and normalizes it with confidence metrics and versioning.
3. Detects conflicts of interest using dynamic ontology and enrichment data.
4. Presents information through interactive, narrative dashboards.
5. Self-monitors for parser drift, schema changes, and data errors.
6. Publishes results transparently, with open data access and ethical context.

## Summary Table — Remaining Gaps (Now Addressed)

| Category | Gap | Solution Integrated |
|---|---|---|
| Scraping | HTML layout drift | Schema change detector + alert |
| Parsing | OCR accuracy | AWS Textract + validation dataset |
| Normalization | Ambiguous names | Bioguide + fuzzy multi-key match |
| Data lineage | No versioning | Added `parse_version` + audit logs |
| COI Model | Static mapping | Dynamic jurisdiction ontology scraper |
| Enrichment | Missing bills/contracts | Congress.gov + USAspending integration |
| Frontend | Limited filters | Multi-filter search + timeline view |
| Trust | Confidence missing | Confidence badges + provenance display |
| Observability | No drift monitoring | Daily parser pattern test |
| Governance | Legal risk | Disclaimers + right-to-respond channel |

---

## Notes & Next Steps

- This README expresses the final integrated implementation plan. The next engineering steps are:
  1. Create the ingestion and parser skeletons (`house_parser.py`, `senate_parser.py`) and CI tests against a golden dataset.
  2. Implement the `filings` and `transactions` schemas in Aurora and add materialized views.
  3. Wire up a minimal FastAPI backend and a Next.js frontend shell to present the daily summary.
  4. Add monitoring dashboards and CloudWatch alarms for parser drift and parse success %.

- If you'd like, I can scaffold the repository with starter templates (Python FastAPI service, parser modules, Terraform skeleton, and a Next.js app) and add minimal unit tests and CI config.

---

*Last updated: October 26, 2025*

# Congressional Trade Transparency Platform — Full Implementation Plan

This repository contains the design and implementation plan for a Congressional Trade Transparency Platform: a data-driven, explainable system that scrapes official U.S. House and Senate financial disclosures, normalizes them, computes conflict-of-interest (COI) scores with provenance, and visualizes findings through an interactive dashboard.

## 1. Project Overview

Objective:
Develop a web-based, data-driven transparency platform that scrapes official Congressional stock trading disclosures from U.S. House and Senate portals, parses and normalizes the data, detects potential conflicts of interest (COIs) using rule-based and contextual logic, and visualizes findings interactively through graphs, timelines, and explainable scores.

Key Design Principles:
- Primary data only (no aggregators)
- Transparency-first architecture (auditability and provenance)
- Explainable conflict detection
- Modular, fault-tolerant AWS-based pipeline

## 2. Core Objectives
1. Daily ingestion of filings from official House and Senate portals.
2. Parsing and normalization of PDF disclosures into structured form.
3. Data lineage and confidence tracking for transparency and reproducibility.
4. Conflict-of-Interest scoring using committee mappings and enrichment data.
5. Visualization dashboard (Next.js frontend) showing daily summaries, stock charts, and conflicts.
6. Contextual enrichment — bills, contracts, and sector overlap.
7. Resilient architecture with parser drift monitoring, reprocessing, and alerts.

## 3. System Architecture

Layer / Components
- Ingestion: AWS Lambda, Step Functions, EventBridge
- Parsing/OCR: pdfplumber + AWS Textract (fallback)
- Storage: AWS Aurora PostgreSQL + S3
- Enrichment: Fargate Batch for bill/contract analysis
- Backend: FastAPI (Python 3.11)
- Frontend: Next.js + TypeScript
- Caching: Redis (ElastiCache)
- Monitoring: CloudWatch + Schema Drift Detection
- Infrastructure: Terraform (IaC)

## 4. Data Ingestion Pipeline

Sources
- House Clerk PTR filings: https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure
- Senate eFD filings: https://efdsearch.senate.gov/search/

Pipeline Steps
1. Scheduler: EventBridge triggers daily Step Function.
2. Indexer Lambdas: Scrape new filings since last run.
3. HTML Schema Detector: Validates DOM structure; raises alerts on layout drift.
4. Downloader Lambdas: Fetch PDFs, compute SHA256, store in S3.
5. Parser Workers:
	 - Primary: pdfplumber for table extraction
	 - Fallback: Textract for scanned documents
6. Validator & Loader: Normalize data → Aurora PostgreSQL.
7. Deduplication: Detect amended or duplicate filings via SHA256 and text comparison.
8. Audit Logging: Record every ingestion event and parser version.

Improvements Implemented

| Gap | Solution |
|---|---|
| HTML schema changes | Schema drift detector job before scraping |
| Duplicate filings | Deduplication logic using SHA256 + amendment text detection |
| OCR errors | AWS Textract for structured text parsing |
| Name disambiguation | Bioguide ID + multi-attribute matching |
| Parser version drift | parse_version field and nightly reprocessing queue |
| Parse failure alerting | CloudWatch alarm <95% parse success |

## 5. Data Model (Aurora PostgreSQL)

Core Tables (high level)
- `persons(person_id, full_name, chamber, state, district, bioguide_id)`
- `committees(committee_id, chamber, name, jurisdiction)`
- `committee_assignments(person_id, committee_id, start_date, end_date, valid_from, valid_to)`
- `issuers(issuer_id, name, cik, sector, industry, naics)`
- `symbols_ref(ticker, issuer_id, exchange, name_observed, as_of_date)`
- `filings(filing_id, source_system, filing_type, person_id, report_date, filing_url, s3_uri, sha256, parse_version, parse_quality)`
- `transactions(tx_id, filing_id, tx_date, tx_type, amount_min, amount_max, asset_text, ticker_observed, issuer_id, ticker_conf, row_conf)`
- `conflict_scores(tx_id, committee_hit, jurisdiction_overlap, position_size_norm, bill_overlap_score, contract_exposure_score, delay_days, score, explain_json)`
- `daily_summaries(summary_date, total_trades, total_estimated_volume, high_conflict_count, top_sectors_json)`

Schema Enhancements

| Gap | Solution |
|---|---|
| Missing time-valid committee mappings | Added `valid_from`, `valid_to` columns |
| Parser lineage missing | Added `parse_version` column |
| Confidence aggregation missing | Introduced stored procedure: tx_conf = min(parse_quality, ticker_conf, row_conf) |
| Amendment tracking | Added `filing_supersedes` field |
| Audit missing | Added `audit_log` table for ingestion & enrichment |
| Low performance joins | Added materialized views (`mv_recent_trades`, `mv_conflict_leaderboard`) |

## 6. Parsing Framework

Implementation Details
- Modular parsers per chamber (e.g. `house_parser.py`, `senate_parser.py`).
- Confidence-based fallback to OCR pipeline.
- Regex extraction for transaction rows (amount, ticker, date, type).
- Fuzzy company name → ticker mapping (via `symbols_ref`).
- `parse_errors` table storing failed or low-confidence runs.

Solutions to Known Parsing Problems

| Problem | Fix |
|---|---|
| Inconsistent tables | Parser templates per source |
| Scanned PDFs | Textract-based OCR fallback |
| Ambiguous tickers | Fuzzy match + manual review table |
| Data gaps | Parser confidence scoring |
| Filing amendments | Hash comparison + supersedes link |
| Parser bugs | Nightly reprocessing job for old versions |
| Parser drift | Daily schema validation and alert if DOM or text structure changes |

## 7. Conflict-of-Interest Engine

Purpose

Compute a transparent and reproducible score indicating potential conflicts between an official’s roles and their stock trades.

Inputs
- Committee memberships
- Committee → Sector mapping
- Issuer industries
- Disclosure delay
- Trade amount

Static Mapping Example (conceptual)

```
{
	"House Energy & Commerce": ["Healthcare", "Pharma", "Insurance"],
	"Senate Armed Services": ["Defense", "Aerospace", "Cybersecurity"],
	"House Agriculture": ["Commodities", "Farming", "Food"]
}
```

Conflict Score (example formula)

committee_hit        = 1 if overlap exists
jurisdiction_overlap = degree of overlap (0–1)
position_size_norm   = log10(midpoint(amount_range)) / 6
delay_days           = report_date - tx_date
bill_overlap_score   = overlap with active legislation
contract_exposure_score = issuer involved in government contracts

score = 0.35*committee_hit
			+ 0.20*jurisdiction_overlap
			+ 0.15*position_size_norm
			+ 0.15*bill_overlap_score
			+ 0.10*contract_exposure_score
			+ 0.05*(1 - delay_days/60)

Explain JSON Example

```
{
	"committee_match": ["House Energy & Commerce"],
	"bill_context": "HR-105 healthcare pricing reform under same committee",
	"contract_overlap": "Issuer received $5M DoD contract (USAspending.gov)",
	"trade_size_usd": 15000,
	"delay_days": 18,
	"confidence": 0.92
}
```

Enhancements & Gap Fixes

| Gap | Solution |
|---|---|
| Static sector mapping | Auto-update via scraped committee jurisdiction text (keyword-based) |
| No policy context | Bill scraper (Congress.gov API) adds `bill_overlap_score` |
| Missing contract data | USAspending.gov integration adds `contract_exposure_score` |
| Heuristic weights only | Weight calibration via regression on backtested data |
| False positives | Baseline control group for comparison |
| No confidence weighting | Weight COI scores by aggregated transaction confidence |

## 8. Backend (FastAPI)

Endpoints (high-level)
- `/members/search?q=` — Autocomplete search
- `/members/{id}` — Member overview
- `/members/{id}/trades?...` — Fetch trades with filters
- `/prices/{ticker}?start&end` — Get OHLC candles
- `/members/{id}/trades/{tx_id}/performance` — Post-trade returns (7/30/90 days)
- `/summary/daily?date=` — Daily summary
- `/conflicts?date=` — Top conflict scores daily
- `/admin/reprocess` — Trigger reparsing for low-confidence filings

Improvements

| Gap | Solution |
|---|---|
| Query lag | Pre-aggregated views + indexes |
| Rate limits | IP throttling & CloudFront caching |
| Security | JWT + rate limit middleware |
| Version tracking | Include `X-Data-Version` header |
| Cache redundancy | Redis TTL (24h) for price and performance endpoints |

## 9. Market Data Integration

MarketData Abstraction (concept)

class MarketData:
		def candles(self, ticker, start, end, interval="1d"): ...
		def benchmark(self, start, end, symbol="SPY"): ...

Features
- Adjusted close prices only.
- Benchmark overlay (SPY, sector ETF).
- Prefetched daily cache for top-traded tickers.
- Redis layer for 24h caching.

Gap Fixes

| Gap | Solution |
|---|---|
| Rate limit from data source | Fallback providers + cache layer |
| Inconsistent timestamps | Round to nearest market day |
| Missing holiday handling | Adjust window automatically via trading calendar |

## 10. Frontend (Next.js + TypeScript)

Pages
- Home Dashboard — Daily summary, top conflicts, volume stats
- Member Explorer — Bio, committees, trades, COI timeline
- Trade Details — Filing info, explainable COI score, stock graph
- Conflict Feed — Filtered list by score, sector, chamber
- Timeline View — Chronological view of trades vs. policy events
- Admin QA Panel — Confidence audit and reparse trigger

UI Enhancements

| Gap | Solution |
|---|---|
| Limited filters | Add sector, committee, conflict score, delay range filters |
| Missing timeline | Interactive axis with events + filings |
| Low data transparency | Confidence color badges + source link |
| Context missing | Hover tooltips showing COI rationale |
| No narrative insight | LangChain agent-generated daily summary (“Story Mode”) |

## 11. Data Enrichment & Intelligence Modules

Module / Function
- Committee Updater — Monthly refresh of Congress.gov rosters
- Bill Tracker — Maps active bills to sectors via NLP keywords
- Contract Linker — Joins issuers with USAspending.gov contracts
- Donor Overlay (Optional) — Pulls OpenSecrets donor data
- Anomaly Detector (Phase 3) — Detects unusual trade timing patterns
- LangChain Narrative Agent — Auto-generates summaries and contextual insights

## 12. Observability & Quality Control

Monitoring Metrics
- Parse success %
- Parser drift detection (schema change)
- Avg. parse time
- Ingestion latency
- COI scoring success rate
- Confidence distribution

Data Audits
- Weekly checksum validation (S3 vs DB SHA256)
- Reconciliation of scraped vs. official filing counts
- Daily parser pattern drift test (deviation > 2σ → alert)
- Billing alarms for AWS cost control

Regression Testing
- “Golden dataset” of verified PTRs for CI/CD parser testing.
- Automated diff reports for parser output drift.

## 13. Scalability and Cost Optimization

| Issue | Fix |
|---|---|
| OCR Lambda timeouts | Offload to Fargate or AWS Batch |
| High PDF volume | Split queues by chamber/date |
| Storage costs | Lifecycle rule: archive parsed JSON to Glacier |
| API load | Read replicas + Redis caching |
| GPU OCR cost | Spot instance orchestration for heavy OCR workloads |

## 14. Legal, Ethical, and Transparency Measures

Risk / Mitigation
- Implication of misconduct — Add clear disclaimer: “COI score ≠ evidence of wrongdoing.”
- Misinterpretation of timeliness — Display “Reported X days after transaction” in all UI views
- PII exposure — Use only publicly available STOCK Act data
- Data misrepresentation — Show provenance: link, SHA256, parser version
- Transparency — Public API documentation and open dataset exports
- Right to respond — Optional feedback contact for congressional offices

## 15. Roadmap & Phase Summary

Phase / Focus / Key Deliverables
- Phase 1 (MVP) — Core ingestion, parser, DB, COI v1, UI summary — Parsing + FastAPI + Next.js dashboard
- Phase 2 (Contextual Intelligence) — Enrichment (bills, contracts), caching, trends — Ontology updates, bill tracking, caching
- Phase 3 (Insights & AI) — LangChain narrative, anomaly detection, Congress Alpha Index — Story Mode, Influence Timeline
- Phase 4 (Production & Governance) — Parser monitoring, alerts, public dataset export — Schema drift detection, audit dashboards
- Phase 5 (Open Research Platform) — Public API + academic access — API documentation portal + open data release

## 16. Example Daily Output

Date: October 25, 2025
- New Filings: 14
- Total Trades: 102
- Volume: $5.1M
- Top Sector: Healthcare (29%)
- Average Delay: 18 days
- Top Conflict: Rep. Mike Moore → CNC (COI: 0.73)
- Context: Energy & Commerce Committee oversight on healthcare pricing reform (HR-105).

## 17. Long-Term Evolution

Phase 3–5 Additions
- Influence Timeline: Overlay trades with legislative votes.
- Congress Alpha Index: Backtest “follow-the-Congress” performance.
- Cross-Member Network Graph: Graph visualization (Neo4j) of trading overlaps.
- Transparency Index: Score combining disclosure delay, conflict frequency, parse confidence.
- Public Data Portal: Daily Parquet exports for journalists and researchers.

---

## Final Deliverable Vision

You’ll have a transparent, self-healing, explainable, and ethically grounded system that:
1. Scrapes primary Congressional trade data daily.
2. Parses and normalizes it with confidence metrics and versioning.
3. Detects conflicts of interest using dynamic ontology and enrichment data.
4. Presents information through interactive, narrative dashboards.
5. Self-monitors for parser drift, schema changes, and data errors.
6. Publishes results transparently, with open data access and ethical context.

## Summary Table — Remaining Gaps (Now Addressed)

| Category | Gap | Solution Integrated |
|---|---|---|
| Scraping | HTML layout drift | Schema change detector + alert |
| Parsing | OCR accuracy | AWS Textract + validation dataset |
| Normalization | Ambiguous names | Bioguide + fuzzy multi-key match |
| Data lineage | No versioning | Added `parse_version` + audit logs |
| COI Model | Static mapping | Dynamic jurisdiction ontology scraper |
| Enrichment | Missing bills/contracts | Congress.gov + USAspending integration |
| Frontend | Limited filters | Multi-filter search + timeline view |
| Trust | Confidence missing | Confidence badges + provenance display |
| Observability | No drift monitoring | Daily parser pattern test |
| Governance | Legal risk | Disclaimers + right-to-respond channel |

---

## Notes & Next Steps

- This README expresses the final integrated implementation plan. The next engineering steps are:
	1. Create the ingestion and parser skeletons (`house_parser.py`, `senate_parser.py`) and CI tests against a golden dataset.
	2. Implement the `filings` and `transactions` schemas in Aurora and add materialized views.
	3. Wire up a minimal FastAPI backend and a Next.js frontend shell to present the daily summary.
	4. Add monitoring dashboards and CloudWatch alarms for parser drift and parse success %.

- If you'd like, I can scaffold the repository with starter templates (Python FastAPI service, parser modules, Terraform skeleton, and a Next.js app) and add minimal unit tests and CI config.

---

*Last updated: October 26, 2025*

