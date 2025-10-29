# House Parser Setup

## 1. Create a Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

## 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```
If network access is restricted, install manually:
```bash
pip install psycopg[binary]==3.1.18 python-dotenv==1.0.0
```
or via conda:
```bash
conda install -c conda-forge psycopg python-dotenv
```

## 3. Start Local Postgres (Docker)
```bash
docker compose up -d    # Start
docker compose down     # Stop
docker compose logs -f  # Tail logs
```

Apply the schema once Postgres is running:
```bash
docker compose exec postgres psql -U tlp -d tlp_house -f db/schema.sql
```

## 4. Run the Scraper
Basic run (parse + DB insert):
```bash
python house_ptr_scraper.py 2025 --db-url postgresql://tlp:tlp_password@localhost:5432/tlp_house
```

### Output Options
- JSON export:
  ```bash
  python house_ptr_scraper.py 2025 \
    --db-url postgresql://tlp:tlp_password@localhost:5432/tlp_house \
    --output json
  ```
- CSV export:
  ```bash
  python house_ptr_scraper.py 2025 \
    --db-url postgresql://tlp:tlp_password@localhost:5432/tlp_house \
    --output csv
  ```
- Multiple years:
  ```bash
  python house_ptr_scraper.py 2023 2024 2025 \
    --db-url postgresql://tlp:tlp_password@localhost:5432/tlp_house
  ```

Outputs are saved to `samples/<year>/<year>FD.zip` and optional JSON/CSV files beside the ZIP. Parsed rows are upserted into the `house_filings` table.

Verify data:
```bash
docker compose exec postgres psql -U tlp -d tlp_house \
  -c "SELECT doc_id, filing_year, last_name FROM house_filings LIMIT 5;"
```
