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


class SenateScraper:
    def __init__(self, samples_dir: Path):
        self.session = requests.Session()
        self.samples_dir = samples_dir
        self._setup_session()

    def _setup_session(self):
        """Configure session headers and get initial cookies/CSRF token if needed."""
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 Trade Transparency Platform",
            "Accept": "text/html,application/json",
            "Accept-Language": "en-US,en;q=0.9",
        })
        # public access typically works; authentication can be added here if needed

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
                        "pdf_url": None,
                        "raw": row.get("raw", {}),
                    })
                    continue

                # Case B: older shape where row contains 'href' and 'text'
                href = row.get("href", "")
                text = row.get("text", "")
                if href and ("/search/view/ptr/" in href or "/view/ptr/" in href):
                    m = re.search(r"(\d+)", href)
                    doc_id = m.group(1) if m else href
                    date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", text)
                    date_text = date_match.group(1) if date_match else None
                    results.append({
                        "doc_id": str(doc_id),
                        "filing_date": date_text,
                        "pdf_url": None,
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


    def download_filing(self, doc_id: str, year: int) -> tuple[bytes, str]:
        """Download a specific filing PDF and return its content and SHA256. Save debug file if not PDF."""
        url = f"{DOWNLOAD_URL}{doc_id}"
        try:
            resp = self.session.get(url, timeout=30, allow_redirects=True)
            resp.raise_for_status()
        except requests.RequestException:
            raise

        content: bytes
        ctype = resp.headers.get("Content-Type", "")
        year_dir = self.samples_dir / str(year)
        year_dir.mkdir(parents=True, exist_ok=True)
        out_path = year_dir / f"{doc_id}.pdf"

        if ctype.startswith("application/pdf"):
            content = resp.content
        else:
            # Not a PDF: log warning, save debug file, and try to extract PDF link
            logging.warning(f"Doc {doc_id}: Response is not PDF (Content-Type: {ctype})")
            preview = resp.content[:200]
            try:
                logging.warning(f"Doc {doc_id}: First 200 bytes: {preview!r}")
            except Exception:
                pass
            debug_path = year_dir / f"debug_{doc_id}.bin"
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
                pdf_url = pdf_href if pdf_href.startswith("http") else f"{SENATE_BASE_URL}{pdf_href}"
                pdf_resp = self.session.get(pdf_url, timeout=30)
                pdf_resp.raise_for_status()
                content = pdf_resp.content
                # If this is not a PDF, save debug file
                pdf_ctype = pdf_resp.headers.get("Content-Type", "")
                if not pdf_ctype.startswith("application/pdf"):
                    logging.warning(f"Doc {doc_id}: Fallback PDF link is not PDF (Content-Type: {pdf_ctype})")
                    debug_pdf_path = year_dir / f"debug_{doc_id}_fallback.bin"
                    with debug_pdf_path.open("wb") as fh:
                        fh.write(pdf_resp.content)
            else:
                # fallback: return HTML bytes
                content = resp.content

        sha256 = hashlib.sha256(content).hexdigest()

        write_file = True
        if out_path.exists():
            try:
                existing = out_path.read_bytes()
                if hashlib.sha256(existing).hexdigest() == sha256:
                    write_file = False
            except OSError:
                write_file = True

        if write_file:
            with out_path.open("wb") as fh:
                fh.write(content)

        return content, sha256

    def extract_transactions(self, pdf_content: bytes) -> list[TransactionRow]:
        """Extract transaction data from a filing PDF.

        Placeholder: implement pdfplumber table parsing and OCR fallback here.
        """
        # TODO: Use pdfplumber to extract tables and lines. If tables are empty,
        # run Tesseract OCR on pages and re-parse text blocks.
        return []


    def download_filing(self, doc_id: str, year: int) -> tuple[bytes, str]:
        """Download a specific filing PDF and return its content and SHA256."""
        # The view endpoint often either streams a PDF or contains a link to it.
        url = f"{DOWNLOAD_URL}{doc_id}"
        try:
            resp = self.session.get(url, timeout=30, allow_redirects=True)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise

        content = None

        ctype = resp.headers.get("Content-Type", "")
        if ctype.startswith("application/pdf"):
            content = resp.content
        else:
            # Parse HTML page to find PDF link or embedded PDF
            soup = BeautifulSoup(resp.text, "html.parser")
            # check for <iframe src="...pdf">
            iframe = soup.find("iframe")
            pdf_href = None
            if iframe and iframe.get("src") and ".pdf" in iframe.get("src"):
                pdf_href = iframe.get("src")
            else:
                # find first link with .pdf
                for a in soup.find_all("a", href=True):
                    if ".pdf" in a["href"].lower():
                        pdf_href = a["href"]
                        break

            if pdf_href:
                pdf_url = pdf_href if pdf_href.startswith("http") else f"{SENATE_BASE_URL}{pdf_href}"
                pdf_resp = self.session.get(pdf_url, timeout=30)
                pdf_resp.raise_for_status()
                content = pdf_resp.content
            else:
                # As a fallback, treat the HTML body as bytes (not ideal)
                content = resp.content

        sha256 = hashlib.sha256(content).hexdigest()

        # Save to samples dir
        year_dir = self.samples_dir / str(year)
        year_dir.mkdir(parents=True, exist_ok=True)
        out_path = year_dir / f"{doc_id}.pdf"
        # Only write if new or content differs
        write_file = True
        if out_path.exists():
            try:
                existing = out_path.read_bytes()
                if hashlib.sha256(existing).hexdigest() == sha256:
                    write_file = False
            except OSError:
                write_file = True

        if write_file:
            with out_path.open("wb") as fh:
                fh.write(content)

        return content, sha256

    def extract_transactions(self, pdf_content: bytes) -> list[TransactionRow]:
        """Extract transaction data from a filing PDF."""
        # TODO: Implement PDF parsing with pdfplumber + OCR fallback
        pass

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

    scraper = SenateScraper(args.samples_dir)
    filings = scraper.search_filings(args.start_date, args.end_date)
    
    if not filings:
        logging.info("No new filings found for date range.")
        return

    logging.info("Found %d filings to process.", len(filings))
    total = 0
    downloaded = 0
    skipped = 0
    failed = 0

    for item in filings:
        total += 1
        doc_id = str(item.get("doc_id") or item.get("DocID") or item.get("raw", {}).get("id") or "")
        if not doc_id:
            logging.warning("Skipping filing with missing doc_id: %r", item)
            skipped += 1
            continue

        # Determine year for saving; fall back to current year
        filing_date = item.get("filing_date") or item.get("date") or None
        year = None
        try:
            if filing_date:
                if isinstance(filing_date, str):
                    # try ISO or common formats
                    try:
                        year = datetime.strptime(filing_date, "%Y-%m-%d").year
                    except ValueError:
                        try:
                            year = datetime.strptime(filing_date, "%m/%d/%Y").year
                        except ValueError:
                            year = date.today().year
                elif isinstance(filing_date, (datetime, date)):
                    year = filing_date.year
        except Exception:
            year = date.today().year

        if year is None:
            year = date.today().year

        logging.info("Processing doc_id=%s (year=%s)", doc_id, year)

        if args.dry_run:
            logging.info("Dry run: would download %s", doc_id)
            continue

        try:
            content, sha = scraper.download_filing(doc_id, year)
            logging.info("Saved %s (sha256=%s)", doc_id, sha)
            downloaded += 1
        except Exception as exc:
            logging.warning("Failed to download %s: %s", doc_id, exc)
            failed += 1

    logging.info("Done. total=%d downloaded=%d skipped=%d failed=%d", total, downloaded, skipped, failed)

if __name__ == "__main__":
    main()