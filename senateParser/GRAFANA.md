# Grafana Visualization Setup

This directory includes a pre-configured Grafana instance for visualizing Senate trading data.

## Quick Start

### 1. Start Grafana and PostgreSQL
```bash
cd /Users/dhruvsusheelkar/Documents/Trade_Like_Politician/senateParser
docker compose up -d
```

### 2. Access Grafana
- **URL:** http://localhost:3000
- **Username:** `admin`
- **Password:** `admin`

(You'll be prompted to change the password on first login)

### 3. View the Dashboard
The "Senate Trading Overview" dashboard will be automatically provisioned and available immediately.

Navigate to: **Dashboards → Senate Trading Overview**

**Note:** If the dashboard doesn't appear or shows datasource errors, the dashboard JSON may need to be updated with the correct datasource UID. Check Configuration → Data Sources to find the UID of "Senate Trading DB" (usually starts with `P` followed by random characters).

---

## Dashboard Panels

### **Summary Stats (Top Row)**
1. **Total Filings** - Count of all Senate PTR filings
2. **Total Transactions** - Count of all stock/bond transactions
3. **Total Est. Trading Volume** - Sum of midpoint estimates
4. **Unique Senators** - Number of senators who filed

### **Recent Transactions Table**
Shows the 50 most recent transactions with:
- Date, Senator, Ticker, Asset Name
- Transaction Type (Purchase/Sale)
- Disclosed Range
- **Estimated Volume (Midpoint)**
- Owner (Self/Spouse/Joint)

### **Daily Trading Volume Chart**
Time-series visualization of estimated daily trading volume using midpoint calculation:
```sql
Est. Volume = (amount_min + amount_max) / 2
```

### **Transaction Types (Pie Chart)**
Breakdown of Purchase vs Sale vs Exchange transactions

### **Top Traders by Volume**
Leaderboard showing senators ranked by estimated total trading volume (midpoint)

### **Most Traded Tickers**
Top 20 most frequently traded stock symbols with purchase/sale counts

---

## Understanding the Data

### **Midpoint Calculation**
All volume estimates use the midpoint of disclosed ranges:

| Disclosed Range | Midpoint Est. |
|-----------------|---------------|
| $1,001 - $15,000 | $8,000 |
| $15,001 - $50,000 | $32,500 |
| $50,001 - $100,000 | $75,000 |

**⚠️ Important:** These are estimates only. Actual transaction values may be anywhere within the disclosed range.

### **Data Quality**
- All data parsed with 100% confidence from Senate eFD portal
- Original range text preserved in database
- Parse quality scores tracked per filing

---

## Customizing Dashboards

### Create a New Panel
1. Click "Add" → "Visualization"
2. Select "Senate Trading DB" as datasource
3. Write your SQL query
4. Configure visualization type

### Example Custom Queries

#### **High-Value Trades (>$50k)**
```sql
SELECT
  tx_date AS time,
  f.full_name,
  t.ticker,
  t.asset_name,
  t.amount_range,
  (t.amount_min + t.amount_max) / 2 AS est_amount
FROM senate_transactions t
JOIN senate_filings f ON t.filing_id = f.filing_id
WHERE t.amount_min > 50000
ORDER BY tx_date DESC;
```

#### **Senator-Specific Timeline**
```sql
SELECT
  tx_date AS time,
  ticker,
  tx_type,
  (amount_min + amount_max) / 2 AS value
FROM senate_transactions t
JOIN senate_filings f ON t.filing_id = f.filing_id
WHERE f.full_name = 'Boozman, John'
ORDER BY tx_date;
```

#### **Purchase vs Sale Ratio by Senator**
```sql
SELECT
  f.full_name,
  COUNT(CASE WHEN tx_type LIKE '%Purchase%' THEN 1 END) AS purchases,
  COUNT(CASE WHEN tx_type LIKE '%Sale%' THEN 1 END) AS sales,
  ROUND(
    COUNT(CASE WHEN tx_type LIKE '%Purchase%' THEN 1 END)::DECIMAL /
    NULLIF(COUNT(CASE WHEN tx_type LIKE '%Sale%' THEN 1 END), 0),
    2
  ) AS buy_sell_ratio
FROM senate_transactions t
JOIN senate_filings f ON t.filing_id = f.filing_id
GROUP BY f.full_name
HAVING COUNT(*) > 5
ORDER BY buy_sell_ratio DESC;
```

#### **Bond vs Stock Trading**
```sql
SELECT
  CASE
    WHEN asset_type LIKE '%Bond%' THEN 'Bonds'
    WHEN asset_type = 'Stock' THEN 'Stocks'
    ELSE 'Other'
  END AS asset_category,
  COUNT(*) AS trade_count,
  SUM((amount_min + amount_max) / 2) AS est_volume
FROM senate_transactions
GROUP BY asset_category
ORDER BY est_volume DESC;
```

---

## Alerting (Future Enhancement)

Grafana supports alerts. Example use cases:

### High-Value Trade Alert
```sql
-- Alert when a senator trades >$500k
SELECT
  f.full_name,
  SUM((t.amount_min + t.amount_max) / 2) AS daily_volume
FROM senate_transactions t
JOIN senate_filings f ON t.filing_id = f.filing_id
WHERE tx_date = CURRENT_DATE
GROUP BY f.full_name
HAVING SUM((t.amount_min + t.amount_max) / 2) > 500000;
```

### Unusual Activity Alert
```sql
-- Alert when trade count spikes >2x daily average
SELECT COUNT(*) AS today_count
FROM senate_transactions
WHERE tx_date = CURRENT_DATE;
```

---

## Data Sources

### PostgreSQL Connection Details

**For Grafana (inside Docker network):**
- **Host:** `postgres` (Docker network)
- **Port:** `5432` (internal Docker port)
- **Database:** `tlp_senate`
- **User:** `tlp`
- **Password:** `tlp_password`
- **SSL Mode:** `disable`

**For Python Scraper (from host machine):**
- **Host:** `localhost`
- **Port:** `5433` (mapped from internal 5432)
- **Connection String:** `postgresql://tlp:tlp_password@localhost:5433/tlp_senate`

The datasource is automatically provisioned via `grafana/provisioning/datasources/postgres.yml`.

---

## Troubleshooting

### Dashboard Not Appearing
1. Check Grafana logs:
   ```bash
   docker compose logs grafana
   ```

2. Verify provisioning files exist:
   ```bash
   ls -la grafana/provisioning/dashboards/
   ls -la grafana/provisioning/datasources/
   ```

3. Restart Grafana:
   ```bash
   docker compose restart grafana
   ```

### Database Connection Error
1. Ensure PostgreSQL is running:
   ```bash
   docker compose ps
   ```

2. Test database connection:
   ```bash
   docker compose exec postgres psql -U tlp -d tlp_senate -c "SELECT COUNT(*) FROM senate_filings;"
   ```

3. Verify network connectivity:
   ```bash
   docker compose exec grafana ping postgres
   ```

### No Data Showing
1. Verify data exists in database:
   ```bash
   docker compose exec postgres psql -U tlp -d tlp_senate -c "SELECT COUNT(*) FROM senate_transactions;"
   ```

2. Run the scraper to populate data:
   ```bash
   python senate_ptr_scraper.py --start-date 10/10/25 --end-date 10/11/25 \
     --db-url postgresql://tlp:tlp_password@localhost:5433/tlp_senate
   ```

---

## Next Steps

1. **Explore the data** - Use the pre-built dashboard to understand trading patterns
2. **Create custom panels** - Build visualizations for specific analysis
3. **Set up alerts** - Get notified of high-value or unusual trades
4. **Share dashboards** - Export and share with collaborators
5. **Iterate on scraper** - Use Grafana to validate data quality and identify parsing issues

---

## Additional Resources

- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [PostgreSQL Query Guide](https://www.postgresql.org/docs/current/sql-select.html)
- [Senate eFD Portal](https://efdsearch.senate.gov/search/)
- [STOCK Act Information](https://en.wikipedia.org/wiki/STOCK_Act)
