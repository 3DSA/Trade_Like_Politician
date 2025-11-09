## Senate PTR Scraper: Quickstart

### Prerequisites
- Python 3.9+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (for OCR fallback)
  - macOS: `brew install tesseract`
  - Ubuntu: `sudo apt-get install -y tesseract-ocr`
- [Docker](https://www.docker.com/) (for local Postgres, optional)

### Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### (Optional) Start Local Postgres
```bash
docker compose up -d
docker compose exec postgres psql -U tlp -d tlp_senate -f db/schema.sql
```

### Run the Senate Scraper
Fetch filings for a date range (MM/DD/YY, MM/DD/YYYY, or YYYY-MM-DD):
```bash
python senate_ptr_scraper.py --start-date 10/10/25 --end-date 10/11/25
```

### Options
- `--samples-dir DIR`   : Where to save PDFs (default: `samples/`)
- `--force`             : Re-download PDFs even if they exist
- `--dry-run`           : List filings, do not download PDFs
- `--db-url URL`        : Postgres connection string (optional)

### Output
- PDFs are saved in `samples/<year>/<doc_id>.pdf`
- Debug files (HTML, JSON, non-PDF responses) are saved in `samples/<year>/`

### Troubleshooting
- If PDFs are invalid, check `debug_*.bin` files in the samples directory for HTML error pages.
- If the site is under maintenance, try again later.
- For Playwright errors, ensure you have run `playwright install` after installing requirements.

### Development Notes
- The code is modular: browser automation is in `playwright_search.py`, scraping logic in `senate_ptr_scraper.py`.
- All configuration is via CLI flags or environment variables (see `.env.example`).
- For OCR fallback, ensure Tesseract is installed and in your PATH.

---
For more details, see code comments in `senate_ptr_scraper.py` and `playwright_search.py`.