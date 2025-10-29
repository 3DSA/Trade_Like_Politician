#!/usr/bin/env python3
"""
Downloader and parser for U.S. House financial disclosure ZIP archives.

- Downloads yearly ZIPs (e.g. 2025FD.zip) into houseParser/samples/<year>/
- Parses the XML payload (ignoring the TXT companion file)
- Optionally persists filings into the local Postgres database
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Any, Iterable, Optional
from zipfile import ZipFile

import psycopg
import requests
from dotenv import load_dotenv

DEFAULT_BASE_URL = "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.zip"


@dataclass
class FilingRow:
    doc_id: str
    filing_year: int
    prefix: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    suffix: Optional[str]
    filing_type: Optional[str]
    state_dst: Optional[str]
    filing_date: Optional[date]
    raw_payload: dict[str, Any]

    def to_db_params(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "filing_year": self.filing_year,
            "prefix": self.prefix,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "suffix": self.suffix,
            "filing_type": self.filing_type,
            "state_dst": self.state_dst,
            "filing_date": self.filing_date,
            "raw_payload": json.dumps(self.raw_payload),
        }

    def to_export_dict(self) -> dict[str, Any]:
        payload = {
            "doc_id": self.doc_id,
            "filing_year": self.filing_year,
            "prefix": self.prefix,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "suffix": self.suffix,
            "filing_type": self.filing_type,
            "state_dst": self.state_dst,
            "filing_date": self.filing_date.isoformat() if self.filing_date else None,
            "raw_payload": self.raw_payload,
        }
        return payload


@dataclass
class ParseResult:
    year: int
    zip_path: Path
    filings: list[FilingRow]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and parse House financial disclosure ZIP archives."
    )
    parser.add_argument(
        "years",
        nargs="+",
        type=int,
        help="Year(s) to download/parse (e.g. 2024 2025).",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Year template or prefix for ZIP downloads (default: %(default)s).",
    )
    parser.add_argument(
        "--samples-dir",
        default=Path(__file__).resolve().parent / "samples",
        type=Path,
        help="Directory to store downloaded ZIPs and parsed outputs.",
    )
    parser.add_argument(
        "--output",
        choices=("print", "json", "csv"),
        default="print",
        help="How to expose parsed data. JSON/CSV write alongside the ZIP.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if the ZIP already exists locally.",
    )
    parser.add_argument(
        "--skip-parse",
        action="store_true",
        help="Download ZIPs only (parsing disabled).",
    )
    parser.add_argument(
        "--db-url",
        default=os.getenv("DATABASE_URL"),
        help="Postgres connection string; defaults to DATABASE_URL env variable.",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    session = requests.Session()
    for year in args.years:
        result = process_year(
            year=year,
            base_url=args.base_url,
            samples_dir=args.samples_dir,
            force_download=args.force,
            skip_parse=args.skip_parse,
            session=session,
        )

        if not result or args.skip_parse:
            continue

        emit_output(result, args.output)

        if args.db_url:
            persist_filings(result.filings, args.db_url)
        else:
            logging.info("Skipping database persistence; no DB URL provided.")


def process_year(
    year: int,
    base_url: str,
    samples_dir: Path,
    force_download: bool,
    skip_parse: bool,
    session: requests.Session,
) -> Optional[ParseResult]:
    target_dir = samples_dir / str(year)
    target_dir.mkdir(parents=True, exist_ok=True)
    zip_path = target_dir / f"{year}FD.zip"

    if not zip_path.exists() or force_download:
        url = build_year_url(base_url, year)
        logging.info("Downloading %s -> %s", url, zip_path)
        download_zip(url, zip_path, session)
    else:
        logging.info("ZIP already present, skipping download: %s", zip_path)

    if skip_parse:
        return None

    filings = parse_zip(year, zip_path)
    logging.info("Parsed %s filings for %s", len(filings), year)
    return ParseResult(year=year, zip_path=zip_path, filings=filings)


def build_year_url(template_or_prefix: str, year: int) -> str:
    if "{year}" in template_or_prefix:
        return template_or_prefix.format(year=year)
    prefix = template_or_prefix.rstrip("/")
    return f"{prefix}/{year}FD.zip"


def download_zip(url: str, destination: Path, session: requests.Session) -> None:
    response = session.get(url, stream=True, timeout=30)
    response.raise_for_status()
    with destination.open("wb") as fh:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                fh.write(chunk)


def parse_zip(year: int, zip_path: Path) -> list[FilingRow]:
    with ZipFile(zip_path) as zf:
        xml_name = find_xml_file(zf)
        if not xml_name:
            logging.warning("No XML file found in %s; skipping.", zip_path)
            return []
        xml_records = parse_xml_records(zf, xml_name)

    filings: list[FilingRow] = []
    for record in xml_records:
        normalized = normalize_record(year, record)
        if normalized:
            filings.append(normalized)
    return filings


def find_xml_file(zf: ZipFile) -> Optional[str]:
    for name in zf.namelist():
        if name.lower().endswith("fd.xml"):
            return name
    return None


def parse_xml_records(zf: ZipFile, filename: str) -> list[dict[str, Any]]:
    from xml.etree import ElementTree as ET

    with zf.open(filename) as fh:
        root = ET.parse(fh).getroot()

    records: list[dict[str, Any]] = []
    for member in root.findall("Member"):
        record: dict[str, Any] = {}
        for child in list(member):
            record[child.tag] = extract_element_value(child)
        if record.get("DocID"):
            records.append(record)
    return records


def extract_element_value(element) -> Any:
    children = list(element)
    if not children:
        text = element.text.strip() if element.text else None
        return text or None

    grouped: dict[str, Any] = {}
    for child in children:
        value = extract_element_value(child)
        existing = grouped.get(child.tag)
        if existing is None:
            grouped[child.tag] = value
        else:
            if not isinstance(existing, list):
                grouped[child.tag] = [existing]
            grouped[child.tag].append(value)
    return grouped


def normalize_record(year: int, record: dict[str, Any]) -> Optional[FilingRow]:
    doc_id = record.get("DocID")
    if not doc_id:
        return None

    filing_date_raw = record.get("FilingDate")
    filing_date = parse_date(filing_date_raw)

    return FilingRow(
        doc_id=str(doc_id),
        filing_year=year,
        prefix=record.get("Prefix"),
        first_name=record.get("First"),
        last_name=record.get("Last"),
        suffix=record.get("Suffix"),
        filing_type=record.get("FilingType"),
        state_dst=record.get("StateDst"),
        filing_date=filing_date,
        raw_payload=record,
    )


def parse_date(raw: Any) -> Optional[date]:
    if not raw:
        return None
    for fmt in ("%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    logging.debug("Unable to parse date %r", raw)
    return None


def emit_output(result: ParseResult, mode: str) -> None:
    export_records = [filing.to_export_dict() for filing in result.filings]
    if mode == "print":
        print(f"Year {result.year} — {len(result.filings)} filings parsed from {result.zip_path}")
        for preview in export_records[:5]:
            print(json.dumps(preview, ensure_ascii=False, indent=2))
        if len(export_records) > 5:
            print(f"... {len(export_records) - 5} additional filings omitted from preview ...")
    elif mode == "json":
        output_path = result.zip_path.with_suffix(".json")
        with output_path.open("w", encoding="utf-8") as fh:
            json.dump(export_records, fh, ensure_ascii=False, indent=2)
        print(f"Wrote JSON to {output_path}")
    elif mode == "csv":
        from csv import DictWriter

        output_path = result.zip_path.with_suffix(".csv")
        if not export_records:
            logging.warning("No records to write for %s", output_path)
            return
        fieldnames = sorted(export_records[0].keys())
        with output_path.open("w", newline="", encoding="utf-8") as fh:
            writer = DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for rec in export_records:
                row = rec.copy()
                row["raw_payload"] = json.dumps(row["raw_payload"], ensure_ascii=False)
                writer.writerow(row)
        print(f"Wrote CSV to {output_path}")


def persist_filings(filings: Iterable[FilingRow], db_url: str) -> None:
    filings = list(filings)
    if not filings:
        logging.info("No filings to persist.")
        return

    logging.info("Persisting %s filings into Postgres.", len(filings))
    with psycopg.connect(db_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO house_filings (
                    doc_id,
                    filing_year,
                    prefix,
                    first_name,
                    last_name,
                    suffix,
                    filing_type,
                    state_dst,
                    filing_date,
                    raw_payload
                )
                VALUES (
                    %(doc_id)s,
                    %(filing_year)s,
                    %(prefix)s,
                    %(first_name)s,
                    %(last_name)s,
                    %(suffix)s,
                    %(filing_type)s,
                    %(state_dst)s,
                    %(filing_date)s,
                    %(raw_payload)s::jsonb
                )
                ON CONFLICT (doc_id) DO UPDATE SET
                    filing_year = EXCLUDED.filing_year,
                    prefix = EXCLUDED.prefix,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    suffix = EXCLUDED.suffix,
                    filing_type = EXCLUDED.filing_type,
                    state_dst = EXCLUDED.state_dst,
                    filing_date = EXCLUDED.filing_date,
                    raw_payload = EXCLUDED.raw_payload,
                    ingested_at = NOW();
                """,
                [filing.to_db_params() for filing in filings],
            )


if __name__ == "__main__":
    main()
