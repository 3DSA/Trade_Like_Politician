#!/usr/bin/env python3
"""
Downloader and parser for U.S. Senate financial disclosure PDFs.

- Accepts the site access agreement if present
- Searches for PTR filings in a date range
- Downloads filing PDFs and saves them under `samples/<year>/<doc_id>.pdf`
- Computes SHA256 for each downloaded PDF

This file implements a robust, best-effort scraper for local dev and prototyping.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Iterable, Optional

import requests
from bs4 import BeautifulSoup
import pdfplumber
from tqdm import tqdm
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import psycopg

# Senate eFD portal base URL and endpoints
SENATE_BASE_URL = "https://efdsearch.senate.gov"
HOME_URL = f"{SENATE_BASE_URL}/search/home/"
SEARCH_URL = f"{SENATE_BASE_URL}/search/"
DOWNLOAD_URL = f"{SENATE_BASE_URL}/search/view/ptr/"

# Current parser version for tracking
PARSER_VERSION = "0.1.0"

@dataclass
class FilingRow:
    doc_id: str
    filing_year: int
    first_name: Optional[str]
    last_name: Optional[str]
    filing_type: Optional[str]
    state: Optional[str]
    filing_date: Optional[date]
    report_type: Optional[str]
    pdf_url: Optional[str]
    pdf_sha256: Optional[str]
    parse_version: str
    parse_quality: float
    raw_payload: dict[str, Any]

    def to_db_params(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "filing_year": self.filing_year,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "filing_type": self.filing_type,
            "state": self.state,
            "filing_date": self.filing_date,
            "report_type": self.report_type,
            "pdf_url": self.pdf_url,
            "pdf_sha256": self.pdf_sha256,
            "parse_version": self.parse_version,
            "parse_quality": self.parse_quality,
            "raw_payload": json.dumps(self.raw_payload),
        }


@dataclass
class TransactionRow:
    doc_id: str
    tx_date: Optional[date]
    owner: Optional[str]
    ticker: Optional[str]
    asset_name: Optional[str]
    tx_type: Optional[str]
    amount_min: Optional[float]
    amount_max: Optional[float]
    comment: Optional[str]
    row_conf: float

    def to_db_params(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "tx_date": self.tx_date,
            "owner": self.owner,
            "ticker": self.ticker,
            "asset_name": self.asset_name,
            "tx_type": self.tx_type,
            "amount_min": self.amount_min,
            "amount_max": self.amount_max,
            "comment": self.comment,
            "row_conf": self.row_conf,
        }


# HTML Parsing Functions
def parse_amount_range(amount_str: str) -> tuple[Optional[float], Optional[float]]:
    """Parse amount range string like '$1,001 - $15,000' into min/max floats."""
    if not amount_str or amount_str.strip() == '--':
        return None, None
    cleaned = amount_str.replace('$', '').replace(',', '').strip()
    parts = re.split(r'\s*-\s*', cleaned)
    if len(parts) == 2:
        try:
            return float(parts[0]), float(parts[1])
        except ValueError:
            return None, None
    return None, None


def parse_date_str(date_str: str) -> Optional[date]:
    """Parse date string in MM/DD/YYYY format."""
    if not date_str or date_str.strip() == '--':
        return None
    date_str = date_str.strip()
    for fmt in ('%m/%d/%Y', '%m/%d/%y'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def parse_filed_datetime(filed_str: str) -> tuple[Optional[date], Optional[str]]:
    """Parse 'Filed 10/10/2025 @ 11:38 AM' into date and time."""
    if not filed_str:
        return None, None
    match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})\s*@\s*(.+)', filed_str)
    if match:
        date_part = parse_date_str(match.group(1))
        time_part = match.group(2).strip()
        return date_part, time_part
    return None, None


def extract_name_parts(full_name_header: str) -> dict[str, Optional[str]]:
    """Extract name parts from header like 'The Honorable John Boozman (Boozman, John)'."""
    result = {
        'prefix': None,
        'first_name': None,
        'middle_name': None,
        'last_name': None,
        'suffix': None,
        'full_name': None
    }
    if not full_name_header:
        return result

    # Extract parenthetical part
    paren_match = re.search(r'\(([^)]+)\)', full_name_header)
    if paren_match:
        result['full_name'] = paren_match.group(1).strip()
        parts = paren_match.group(1).split(',')
        if len(parts) >= 2:
            last_part = parts[0].strip()
            first_middle_part = parts[1].strip()
            last_tokens = last_part.split()
            if len(last_tokens) > 1 and last_tokens[-1] in ['Jr', 'Jr.', 'Sr', 'Sr.', 'II', 'III', 'IV']:
                result['suffix'] = last_tokens[-1].rstrip('.,')
                result['last_name'] = ' '.join(last_tokens[:-1])
            else:
                result['last_name'] = last_part
            name_tokens = first_middle_part.split()
            if len(name_tokens) >= 1:
                result['first_name'] = name_tokens[0]
            if len(name_tokens) >= 2:
                result['middle_name'] = ' '.join(name_tokens[1:])

    prefix_match = re.match(r'(The Honorable|Hon\.|Mr\.|Mrs\.|Ms\.|Dr\.)', full_name_header, re.IGNORECASE)
    if prefix_match:
        result['prefix'] = prefix_match.group(1)

    return result


def parse_transaction_counts(summary_text: str) -> dict[str, int]:
    """Parse transaction summary like '(9 transactions total) 0 Self 9 Joint 0 Spouse 0 Dependent Child'."""
    result = {
        'total_transactions': 0,
        'self_transactions': 0,
        'joint_transactions': 0,
        'spouse_transactions': 0,
        'dependent_transactions': 0
    }
    if not summary_text:
        return result

    total_match = re.search(r'(\d+)\s+transactions?\s+total', summary_text, re.IGNORECASE)
    if total_match:
        result['total_transactions'] = int(total_match.group(1))

    self_match = re.search(r'(\d+)\s+Self', summary_text)
    if self_match:
        result['self_transactions'] = int(self_match.group(1))

    joint_match = re.search(r'(\d+)\s+Joint', summary_text)
    if joint_match:
        result['joint_transactions'] = int(joint_match.group(1))

    spouse_match = re.search(r'(\d+)\s+Spouse', summary_text)
    if spouse_match:
        result['spouse_transactions'] = int(spouse_match.group(1))

    dependent_match = re.search(r'(\d+)\s+Dependent\s+Child', summary_text)
    if dependent_match:
        result['dependent_transactions'] = int(dependent_match.group(1))

    return result


def parse_ptr_html(html_content: str, doc_id: str, source_url: str) -> dict[str, Any]:
    """Parse Senate PTR HTML and return structured data."""
    soup = BeautifulSoup(html_content, 'html.parser')

    filing = {
        'doc_id': doc_id,
        'filing_type': 'ptr',
        'parse_version': PARSER_VERSION,
        'source_url': source_url,
        'raw_payload': json.dumps({'html_length': len(html_content)})  # Store metadata instead of full HTML
    }

    transactions = []

    # Extract report type from h1
    h1 = soup.find('h1')
    if h1:
        h1_text = h1.get_text(strip=True)
        filing['report_type'] = h1_text
        year_match = re.search(r'for\s+(\d{1,2}/\d{1,2}/(\d{4}))', h1_text)
        if year_match:
            filing['filing_year'] = int(year_match.group(2))

    # Extract member name
    h2 = soup.find('h2', class_='filedReport')
    if h2:
        name_parts = extract_name_parts(h2.get_text(strip=True))
        filing.update(name_parts)

    # Extract filing date and time
    filed_p = soup.find('p', class_='muted')
    if filed_p:
        strong = filed_p.find('strong')
        if strong:
            filing_date, filing_time = parse_filed_datetime(strong.get_text(strip=True))
            filing['filing_date'] = filing_date
            filing['filed_time'] = filing_time
            if filing_date and not filing.get('filing_year'):
                filing['filing_year'] = filing_date.year

    # Check certification
    cert_checkbox = soup.find('input', {'name': 'filing_certified'})
    filing['certified'] = cert_checkbox and cert_checkbox.get('checked') == 'checked'

    cert_labels = soup.find_all('label', class_='form-check-label')
    if cert_labels:
        filing['certification_text'] = '\\n'.join([label.get_text(strip=True) for label in cert_labels])

    # Extract transaction counts
    summary_list = soup.find('ul', class_='unstyled')
    if summary_list:
        counts = parse_transaction_counts(summary_list.get_text())
        filing.update(counts)

    # Extract transactions
    table = soup.find('table', class_='table-striped')
    if table:
        tbody = table.find('tbody')
        if tbody:
            for row in tbody.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 9:
                    tx = {}
                    tx['tx_number'] = int(cells[0].get_text(strip=True))
                    tx['tx_date'] = parse_date_str(cells[1].get_text(strip=True))
                    tx['owner'] = cells[2].get_text(strip=True) or None

                    ticker_link = cells[3].find('a')
                    if ticker_link:
                        tx['ticker'] = ticker_link.get_text(strip=True)
                    else:
                        ticker_text = cells[3].get_text(strip=True)
                        tx['ticker'] = ticker_text if ticker_text != '--' else None

                    asset_text = cells[4].get_text(strip=True)
                    tx['asset_name'] = asset_text or None

                    # Check for bond details
                    bond_div = cells[4].find('div', class_='text-muted')
                    if bond_div:
                        bond_text = bond_div.get_text()
                        rate_match = re.search(r'Rate/Coupon:\s*([^\n]+)', bond_text)
                        if rate_match:
                            tx['rate_coupon'] = rate_match.group(1).strip()
                        maturity_match = re.search(r'Matures:\s*(\d{1,2}/\d{1,2}/\d{4})', bond_text)
                        if maturity_match:
                            tx['maturity_date'] = parse_date_str(maturity_match.group(1))

                    tx['asset_type'] = cells[5].get_text(strip=True) or None
                    tx['tx_type'] = cells[6].get_text(strip=True) or None

                    amount_str = cells[7].get_text(strip=True)
                    tx['amount_range'] = amount_str if amount_str != '--' else None
                    tx['amount_min'], tx['amount_max'] = parse_amount_range(amount_str)

                    comment_text = cells[8].get_text(strip=True)
                    tx['comment'] = comment_text if comment_text != '--' else None
                    tx['row_confidence'] = 1.0

                    transactions.append(tx)

    # Calculate parse quality
    parse_quality = 1.0
    if not filing.get('first_name') or not filing.get('last_name'):
        parse_quality -= 0.2
    if not filing.get('filing_date'):
        parse_quality -= 0.2
    if not transactions:
        parse_quality -= 0.3
    filing['parse_quality'] = max(0.0, parse_quality)

    return {
        'filing': filing,
        'transactions': transactions
    }


class SenateScraper:
    def __init__(self, samples_dir: Path, db_url: Optional[str] = None):
        self.session = requests.Session()
        self.samples_dir = samples_dir
        self.db_url = db_url
        self.db_conn = None
        self._setup_session()

    def _setup_session(self):
        """Configure session headers and get initial cookies/CSRF token if needed."""
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 Trade Transparency Platform",
            "Accept": "text/html,application/json",
            "Accept-Language": "en-US,en;q=0.9",
        })
        # public access typically works; authentication can be added here if needed

    def get_db_connection(self):
        """Get or create database connection."""
        if not self.db_url:
            return None
        if not self.db_conn or self.db_conn.closed:
            self.db_conn = psycopg.connect(self.db_url)
            logging.info("Connected to database")
        return self.db_conn

    def close_db_connection(self):
        """Close database connection if open."""
        if self.db_conn and not self.db_conn.closed:
            self.db_conn.close()
            logging.info("Database connection closed")

    def insert_filing(self, filing_data: dict) -> Optional[int]:
        """Insert filing into senate_filings table and return filing_id."""
        conn = self.get_db_connection()
        if not conn:
            logging.warning("No database connection, skipping insert")
            return None

        insert_sql = """
            INSERT INTO senate_filings (
                doc_id, first_name, middle_name, last_name, suffix, full_name, prefix,
                filing_type, report_type, filing_date, filed_time, filing_year,
                certified, certification_text,
                total_transactions, self_transactions, joint_transactions,
                spouse_transactions, dependent_transactions,
                parse_version, parse_quality, raw_payload, source_url,
                parsed_at
            ) VALUES (
                %(doc_id)s, %(first_name)s, %(middle_name)s, %(last_name)s, %(suffix)s,
                %(full_name)s, %(prefix)s, %(filing_type)s, %(report_type)s,
                %(filing_date)s, %(filed_time)s, %(filing_year)s,
                %(certified)s, %(certification_text)s,
                %(total_transactions)s, %(self_transactions)s, %(joint_transactions)s,
                %(spouse_transactions)s, %(dependent_transactions)s,
                %(parse_version)s, %(parse_quality)s, %(raw_payload)s::jsonb, %(source_url)s,
                NOW()
            )
            ON CONFLICT (doc_id) DO UPDATE SET
                first_name = EXCLUDED.first_name,
                middle_name = EXCLUDED.middle_name,
                last_name = EXCLUDED.last_name,
                suffix = EXCLUDED.suffix,
                full_name = EXCLUDED.full_name,
                prefix = EXCLUDED.prefix,
                report_type = EXCLUDED.report_type,
                filing_date = EXCLUDED.filing_date,
                filed_time = EXCLUDED.filed_time,
                filing_year = EXCLUDED.filing_year,
                certified = EXCLUDED.certified,
                certification_text = EXCLUDED.certification_text,
                total_transactions = EXCLUDED.total_transactions,
                self_transactions = EXCLUDED.self_transactions,
                joint_transactions = EXCLUDED.joint_transactions,
                spouse_transactions = EXCLUDED.spouse_transactions,
                dependent_transactions = EXCLUDED.dependent_transactions,
                parse_version = EXCLUDED.parse_version,
                parse_quality = EXCLUDED.parse_quality,
                raw_payload = EXCLUDED.raw_payload,
                source_url = EXCLUDED.source_url,
                parsed_at = NOW()
            RETURNING filing_id;
        """

        try:
            with conn.cursor() as cur:
                cur.execute(insert_sql, filing_data)
                result = cur.fetchone()
                filing_id = result[0] if result else None
                conn.commit()
                logging.info(f"Inserted/updated filing {filing_data['doc_id']} with filing_id={filing_id}")
                return filing_id
        except Exception as e:
            conn.rollback()
            logging.error(f"Failed to insert filing {filing_data.get('doc_id')}: {e}")
            return None

    def insert_transactions(self, filing_id: int, doc_id: str, transactions: list[dict]) -> int:
        """Insert transactions into senate_transactions table. Returns count of inserted rows."""
        conn = self.get_db_connection()
        if not conn:
            logging.warning("No database connection, skipping transaction insert")
            return 0

        insert_sql = """
            INSERT INTO senate_transactions (
                filing_id, doc_id, tx_number, tx_date, owner, ticker,
                asset_name, asset_type, rate_coupon, maturity_date,
                tx_type, amount_range, amount_min, amount_max,
                comment, row_confidence
            ) VALUES (
                %(filing_id)s, %(doc_id)s, %(tx_number)s, %(tx_date)s, %(owner)s, %(ticker)s,
                %(asset_name)s, %(asset_type)s, %(rate_coupon)s, %(maturity_date)s,
                %(tx_type)s, %(amount_range)s, %(amount_min)s, %(amount_max)s,
                %(comment)s, %(row_confidence)s
            );
        """

        inserted_count = 0
        try:
            with conn.cursor() as cur:
                for tx in transactions:
                    tx['filing_id'] = filing_id
                    tx['doc_id'] = doc_id
                    # Ensure all required fields have defaults
                    tx.setdefault('rate_coupon', None)
                    tx.setdefault('maturity_date', None)
                    tx.setdefault('row_confidence', 1.0)
                    cur.execute(insert_sql, tx)
                    inserted_count += 1
                conn.commit()
                logging.info(f"Inserted/updated {inserted_count} transactions for filing {doc_id}")
        except Exception as e:
            conn.rollback()
            logging.error(f"Failed to insert transactions for filing {doc_id}: {e}")
            return 0

        return inserted_count

    def search_filings(self, start_date: date, end_date: date) -> list[dict]:
        """Search for PTR filings within the given date range.

        Returns a list of dicts with keys: doc_id, filing_date, pdf_url, raw
        """
        from playwright_search import run_search  # Local import to avoid circular dependencies
        
        results: list[dict] = []
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        try:
            # Use Playwright to handle authentication and search
            rows, pw_cookies = run_search(start_str, end_str)

            # If Playwright provided browser cookies, copy them into our
            # requests.Session so subsequent downloads use the same session.
            try:
                if pw_cookies:
                    for c in pw_cookies:
                        cookie = requests.cookies.create_cookie(
                            name=c.get("name"), value=c.get("value"), domain=c.get("domain")
                        )
                        self.session.cookies.set_cookie(cookie)
                    logging.info("Applied %d Playwright cookies to requests session", len(pw_cookies))
            except Exception:
                logging.exception("Failed to apply Playwright cookies to session")

            # Convert playwright results to our canonical format.
            # The Playwright helper may return different shapes depending on
            # whether we intercepted the XHR or parsed the fallback JSON. Be
            # defensive and support both formats.
            for row in rows:
                # Case A: run_search returned a canonical dict with 'doc_id'
                if row.get("doc_id"):
                    doc_id = str(row.get("doc_id"))
                    # filing_date may be provided directly or inside raw text
                    date_text = row.get("filing_date")
                    if not date_text:
                        raw = row.get("raw", {}) or {}
                        text = raw.get("text") or raw.get("row_text") or ""
                        m = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", text)
                        date_text = m.group(1) if m else None

                    results.append({
                        "doc_id": doc_id,
                        "filing_date": date_text,
                        "html_content": row.get("html_content"),  # Pass through HTML content from Playwright
                        "source_url": row.get("source_url"),  # Pass through source URL from Playwright
                        "raw": row.get("raw", {}),
                    })
                    continue

                # Case B: older shape where row contains 'href' and 'text'
                href = row.get("href", "")
                text = row.get("text", "")
                if href and ("/search/view/ptr/" in href or "/view/ptr/" in href):
                    # Extract doc_id from href - support both numeric and UUID formats
                    # Examples: /view/ptr/123 or /view/ptr/f87f8a40-efa5-43df-ad71-56327f5a18ce
                    m = re.search(r"/ptr/([^/]+)", href)
                    doc_id = m.group(1) if m else href
                    date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", text)
                    date_text = date_match.group(1) if date_match else None
                    results.append({
                        "doc_id": str(doc_id),
                        "filing_date": date_text,
                        "html_content": row.get("html_content"),  # Pass through HTML content from Playwright
                        "source_url": row.get("source_url"),  # Pass through source URL from Playwright
                        "raw": {"href": href, "row_text": text},
                    })
                    
        except Exception as e:
            logging.exception("Playwright search failed")

            return results
            
        # If no results were found, log the error
        if not results:
            logging.warning("No results found for date range %s to %s", start_str, end_str)
            
        return results

        return results


    def download_filing(self, doc_id: str, year: int, pdf_url: Optional[str] = None, pdf_path: Optional[str] = None) -> tuple[bytes, str]:
        """Download a specific filing PDF and return its content and SHA256.

        Args:
            doc_id: The filing document ID
            year: Year for organizing downloaded files
            pdf_url: Optional direct PDF URL from Playwright enrichment. If provided,
                    this URL will be used instead of attempting to extract from view page.
            pdf_path: Optional path to already-generated PDF from Playwright. If provided,
                     the file will be read from this path instead of downloading.
        """
        year_dir = self.samples_dir / str(year)
        year_dir.mkdir(parents=True, exist_ok=True)
        out_path = year_dir / f"{doc_id}.pdf"

        content: bytes

        # If we already have a generated PDF from Playwright, use it
        if pdf_path and Path(pdf_path).exists():
            logging.info(f"Doc {doc_id}: Using pre-generated PDF from Playwright: {pdf_path}")
            try:
                content = Path(pdf_path).read_bytes()
                logging.info(f"Doc {doc_id}: Read PDF ({len(content)} bytes)")

                # Verify it's a valid PDF
                if not content.startswith(b'%PDF'):
                    raise ValueError(f"File at {pdf_path} is not a valid PDF")

            except Exception as exc:
                logging.error(f"Doc {doc_id}: Failed to read pre-generated PDF: {exc}")
                raise
        # If we have a direct PDF URL from Playwright, use it
        elif pdf_url:
            logging.info(f"Doc {doc_id}: Using direct PDF URL from Playwright: {pdf_url}")
            try:
                resp = self.session.get(pdf_url, timeout=30, allow_redirects=True)
                resp.raise_for_status()

                ctype = resp.headers.get("Content-Type", "")
                if ctype.startswith("application/pdf"):
                    content = resp.content
                    logging.info(f"Doc {doc_id}: Successfully downloaded PDF ({len(content)} bytes)")
                else:
                    logging.warning(f"Doc {doc_id}: Direct URL did not return PDF (Content-Type: {ctype})")
                    # Save debug file
                    debug_path = year_dir / f"debug_{doc_id}_direct.html"
                    with debug_path.open("wb") as fh:
                        fh.write(resp.content)
                    raise ValueError(f"Direct PDF URL returned {ctype} instead of PDF")
            except requests.RequestException as exc:
                logging.error(f"Doc {doc_id}: Failed to download from direct PDF URL: {exc}")
                raise
        else:
            # Fallback: try the view page endpoint (less reliable)
            logging.warning(f"Doc {doc_id}: No direct PDF URL provided, trying view page endpoint")
            url = f"{DOWNLOAD_URL}{doc_id}"
            try:
                resp = self.session.get(url, timeout=30, allow_redirects=True)
                resp.raise_for_status()
            except requests.RequestException:
                raise

            ctype = resp.headers.get("Content-Type", "")
            if ctype.startswith("application/pdf"):
                content = resp.content
            else:
                # Not a PDF: log warning, save debug file, and try to extract PDF link
                logging.warning(f"Doc {doc_id}: Response is not PDF (Content-Type: {ctype})")
                debug_path = year_dir / f"debug_{doc_id}.html"
                with debug_path.open("wb") as fh:
                    fh.write(resp.content)

                soup = BeautifulSoup(resp.text, "html.parser")
                iframe = soup.find("iframe")
                pdf_href = None
                if iframe and iframe.get("src") and ".pdf" in iframe.get("src"):
                    pdf_href = iframe.get("src")
                else:
                    for a in soup.find_all("a", href=True):
                        if ".pdf" in a["href"].lower():
                            pdf_href = a["href"]
                            break

                if pdf_href:
                    pdf_url_fallback = pdf_href if pdf_href.startswith("http") else f"{SENATE_BASE_URL}{pdf_href}"
                    logging.info(f"Doc {doc_id}: Found PDF link in HTML: {pdf_url_fallback}")
                    pdf_resp = self.session.get(pdf_url_fallback, timeout=30)
                    pdf_resp.raise_for_status()
                    content = pdf_resp.content

                    # Verify it's actually a PDF
                    pdf_ctype = pdf_resp.headers.get("Content-Type", "")
                    if not pdf_ctype.startswith("application/pdf"):
                        logging.warning(f"Doc {doc_id}: Fallback PDF link is not PDF (Content-Type: {pdf_ctype})")
                        raise ValueError(f"Could not obtain valid PDF for doc_id {doc_id}")
                else:
                    # No PDF link found
                    raise ValueError(f"Could not find PDF link for doc_id {doc_id}")

        sha256 = hashlib.sha256(content).hexdigest()

        # Only write if new or content differs
        write_file = True
        if out_path.exists():
            try:
                existing = out_path.read_bytes()
                if hashlib.sha256(existing).hexdigest() == sha256:
                    write_file = False
                    logging.info(f"Doc {doc_id}: File already exists with same SHA256, skipping write")
            except OSError:
                write_file = True

        if write_file:
            with out_path.open("wb") as fh:
                fh.write(content)
            logging.info(f"Doc {doc_id}: Saved to {out_path}")

        return content, sha256

    def extract_transactions(self, pdf_content: bytes) -> list[TransactionRow]:
        """Extract transaction data from a filing PDF.

        Placeholder: implement pdfplumber table parsing and OCR fallback here.
        """
        # TODO: Use pdfplumber to extract tables and lines. If tables are empty,
        # run Tesseract OCR on pages and re-parse text blocks.
        return []

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and parse Senate PTR filings."
    )
    def _parse_date(s: str) -> date:
        """Parse a date string from several common formats into a date object.

        Accepted formats: YYYY-MM-DD, MM/DD/YY, MM/DD/YYYY, YY-MM-DD
        """
        patterns = ("%Y-%m-%d", "%m/%d/%y", "%m/%d/%Y", "%y-%m-%d")
        for p in patterns:
            try:
                return datetime.strptime(s, p).date()
            except Exception:
                continue
        raise argparse.ArgumentTypeError(
            "Invalid date format. Use YYYY-MM-DD or MM/DD/YY or MM/DD/YYYY"
        )

    parser.add_argument(
        "--start-date",
        type=_parse_date,
        help="Start date for filing search (accepts YYYY-MM-DD or MM/DD/YY or MM/DD/YYYY).",
        default=(date.today() - timedelta(days=1)),
    )
    parser.add_argument(
        "--end-date",
        type=_parse_date,
        help="End date for filing search (accepts YYYY-MM-DD or MM/DD/YY or MM/DD/YYYY).",
        default=date.today(),
    )
    parser.add_argument(
        "--samples-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "samples",
        help="Directory to store downloaded PDFs.",
    )
    parser.add_argument(
        "--db-url",
        default=os.getenv("DATABASE_URL"),
        help="Postgres connection string; defaults to DATABASE_URL env var.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download PDFs even if they exist locally.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run: list filings but do not download PDFs.",
    )
    return parser.parse_args()

def main() -> None:
    load_dotenv()
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    scraper = SenateScraper(args.samples_dir, db_url=args.db_url)
    filings = scraper.search_filings(args.start_date, args.end_date)

    if not filings:
        logging.info("No new filings found for date range.")
        return

    logging.info("Found %d filings to process.", len(filings))
    total = 0
    parsed = 0
    skipped = 0
    failed = 0

    try:
        for item in filings:
            total += 1
            doc_id = str(item.get("doc_id") or item.get("DocID") or item.get("raw", {}).get("id") or "")
            if not doc_id:
                logging.warning("Skipping filing with missing doc_id: %r", item)
                skipped += 1
                continue

            # Extract HTML content and source URL from Playwright enrichment
            html_content = item.get("html_content")
            source_url = item.get("source_url")

            # If no HTML content but source_url is available, fetch it
            if not html_content and source_url:
                try:
                    logging.info("Fetching HTML from source_url: %s", source_url)
                    resp = scraper.session.get(source_url, timeout=30)
                    resp.raise_for_status()
                    html_content = resp.text
                    logging.info("Fetched HTML content (%d bytes)", len(html_content))
                except Exception as e:
                    logging.error("Failed to fetch HTML from %s: %s", source_url, e)
                    skipped += 1
                    continue

            if not html_content:
                logging.warning("Skipping filing %s: no HTML content available", doc_id)
                skipped += 1
                continue

            logging.info("Processing doc_id=%s (source_url=%s)", doc_id, source_url or "not provided")

            if args.dry_run:
                logging.info("Dry run: would parse and insert %s", doc_id)
                continue

            try:
                # Parse HTML into structured data
                parsed_data = parse_ptr_html(html_content, doc_id, source_url or "")
                filing_data = parsed_data['filing']
                transactions = parsed_data['transactions']

                logging.info("Parsed filing %s: %d transactions, parse_quality=%.2f",
                            doc_id, len(transactions), filing_data.get('parse_quality', 0.0))

                # Insert into database if db_url is provided
                if args.db_url:
                    # Ensure all required fields have defaults
                    filing_data.setdefault('first_name', None)
                    filing_data.setdefault('middle_name', None)
                    filing_data.setdefault('last_name', None)
                    filing_data.setdefault('suffix', None)
                    filing_data.setdefault('full_name', None)
                    filing_data.setdefault('prefix', None)
                    filing_data.setdefault('report_type', None)
                    filing_data.setdefault('filing_date', None)
                    filing_data.setdefault('filed_time', None)
                    filing_data.setdefault('filing_year', date.today().year)
                    filing_data.setdefault('certified', False)
                    filing_data.setdefault('certification_text', None)
                    filing_data.setdefault('total_transactions', 0)
                    filing_data.setdefault('self_transactions', 0)
                    filing_data.setdefault('joint_transactions', 0)
                    filing_data.setdefault('spouse_transactions', 0)
                    filing_data.setdefault('dependent_transactions', 0)
                    filing_data.setdefault('parse_version', PARSER_VERSION)
                    filing_data.setdefault('parse_quality', 0.0)

                    filing_id = scraper.insert_filing(filing_data)
                    if filing_id and transactions:
                        tx_count = scraper.insert_transactions(filing_id, doc_id, transactions)
                        logging.info("Inserted filing %s (filing_id=%d) with %d transactions", doc_id, filing_id, tx_count)
                    elif filing_id:
                        logging.info("Inserted filing %s (filing_id=%d) with no transactions", doc_id, filing_id)
                    else:
                        logging.warning("Failed to insert filing %s", doc_id)
                        failed += 1
                        continue

                parsed += 1

            except Exception as exc:
                logging.exception("Failed to parse/insert %s: %s", doc_id, exc)
                failed += 1

    finally:
        scraper.close_db_connection()

    logging.info("Done. total=%d parsed=%d skipped=%d failed=%d", total, parsed, skipped, failed)

if __name__ == "__main__":
    main()