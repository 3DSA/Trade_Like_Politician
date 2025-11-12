# senateParser/playwright_search.py
from playwright.sync_api import sync_playwright
from datetime import datetime
import logging
import requests
import re
import json

HOME_URL = "https://efdsearch.senate.gov/search/home/"
SEARCH_URL = "https://efdsearch.senate.gov/search/"
BASE_URL = "https://efdsearch.senate.gov"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

def run_search(start_date: str, end_date: str):
    logging.info(f"Starting search for date range: {start_date} to {end_date}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to False temporarily for debugging
        page = browser.new_page()
        logging.info("Navigating to home page...")
        page.goto(HOME_URL)
        
        # Handle the access agreement on the home page (checkbox + submit)
        try:
            logging.info("Looking for access agreement on home page...")
            page.wait_for_load_state("networkidle")

            # Prefer the specific checkbox by id/name
            checkbox = None
            if page.locator("input#agree_statement").count():
                checkbox = page.locator("input#agree_statement").first
            elif page.locator("input[name='agree_statement']").count():
                checkbox = page.locator("input[name='agree_statement']").first

            # If we found a checkbox (by id or name), act on it
            if checkbox:
                try:
                    logging.info("Found agreement checkbox, checking it")
                    # Wait for checkbox to be ready
                    page.wait_for_timeout(1000)  # Wait 1 second before clicking
                    checkbox.wait_for(timeout=10000)  # Wait up to 10 seconds for checkbox
                    logging.info("Checkbox is visible and ready")

                    # Try clicking the checkbox directly first
                    try:
                        checkbox.click(timeout=10000)
                        logging.info("Clicked checkbox successfully")
                    except Exception:
                        logging.warning("Click failed, trying check() instead")
                        checkbox.check(timeout=10000)

                    # Wait after checking to ensure it registers
                    page.wait_for_timeout(2000)
                    logging.info("Verified checkbox state after action")
                except Exception:
                    logging.exception("Failed to check agreement checkbox")

                # Try to find a submit button within the same form or a visible 'Get Access' button
                submit_btn = None
                if page.locator("button[type='submit']").count():
                    submit_btn = page.locator("button[type='submit']").first
                elif page.locator("text=Get Access").count():
                    submit_btn = page.locator("text=Get Access").first
                elif page.locator("text=I Agree").count():
                    submit_btn = page.locator("text=I Agree").first

                if submit_btn:
                    try:
                        logging.info("Clicking agreement submit button")
                        submit_btn.click()
                        page.wait_for_load_state("networkidle")
                    except Exception:
                        logging.exception("Failed to click agreement submit button")
                else:
                    logging.info("No submit button found after checking agreement checkbox")
            else:
                # If no checkbox, maybe there's a direct link/button to proceed
                if page.locator("text=Get Access").count():
                    logging.info("Clicking 'Get Access' link/button")
                    try:
                        page.click("text=Get Access")
                        page.wait_for_load_state("networkidle")
                    except Exception:
                        logging.exception("Failed to click 'Get Access'")
                elif page.locator("text=I Agree").count():
                    logging.info("Clicking 'I Agree' link/button")
                    try:
                        page.click("text=I Agree")
                        page.wait_for_load_state("networkidle")
                    except Exception:
                        logging.exception("Failed to click 'I Agree'")
                else:
                    logging.info("No access agreement controls found on home page; continuing")

            # If clicking the agreement navigated away, the current URL may already be the search page.
            if not page.url.startswith(SEARCH_URL):
                logging.info("Navigating to search page...")
                page.goto(SEARCH_URL)
                page.wait_for_load_state("networkidle")

            # At this point the page is a client-side DataTable that fetches results via
            # POST to /search/report/data/ using a CSRF token. Rather than attempting to
            # drive the table UI, extract cookies and the CSRF token from the browser
            # context and call the same AJAX endpoint directly via requests. This is
            # more reliable and avoids extra client-side navigation that previously
            # Save search page HTML for debugging
            try:
                page_content = page.content()
                with open("debug_search_page.html", "w", encoding="utf-8") as f:
                    f.write(page_content)
                logging.info("Saved search page HTML for debugging")
            except Exception:
                logging.exception("Failed to save search page HTML")

            # Try to capture the site's XHR for /report/data/ by listening to network
            try:
                # Fill date inputs on the form (ensure the UI will send the correct XHR)
                try:
                    # Format dates for UI input
                    def format_ui_date(dt_str: str) -> str:
                        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
                            try:
                                d = datetime.strptime(dt_str, fmt)
                                return d.strftime("%m/%d/%Y")  # Changed to YYYY format
                            except Exception:
                                continue
                        return dt_str

                    start_el = page.locator("input[name='submitted_start_date']")
                    end_el = page.locator("input[name='submitted_end_date']")
                    if start_el.count():
                        ui_start_date = format_ui_date(start_date)
                        start_el.fill(ui_start_date)
                        logging.info("Filled start date in UI: %s", ui_start_date)
                    if end_el.count():
                        ui_end_date = format_ui_date(end_date)
                        end_el.fill(ui_end_date)
                        logging.info("Filled end date in UI: %s", ui_end_date)
                except Exception:
                    logging.exception("Failed to fill date inputs in UI")

                # Click the search button and wait for the XHR/response
                # NOTE: XHR interception disabled to force fallback path with full pagination
                # The XHR path only captures the first page and is too slow (visits each filing page)
                # To re-enable XHR interception, change ENABLE_XHR_INTERCEPTION to True
                ENABLE_XHR_INTERCEPTION = False

                if ENABLE_XHR_INTERCEPTION:
                    logging.info("Clicking search submit and waiting for XHR response (first page only)")
                    try:
                        with page.expect_response(lambda r: "/report/data/" in r.url and r.request.method == "POST") as resp_info:
                            # Click the primary search button
                            if page.locator("button.btn-primary[type='submit']").count():
                                    page.locator("button.btn-primary[type='submit']").first.click()
                            else:
                                page.click("button[type='submit']")
                        resp = resp_info.value
                        text = resp.text()
                        # Save the raw JSON
                        try:
                            with open("debug_results_json.json", "w", encoding="utf-8") as fh:
                                fh.write(text)
                        except Exception:
                            pass

                        data = None
                        total_records = None
                        try:
                            json_response = resp.json()
                            data = json_response.get("data")
                            total_records = json_response.get("recordsTotal", 0)
                            if total_records:
                                logging.warning("XHR captured first page only: showing %d of %d total filings (pagination not implemented in XHR path)",
                                              len(data) if data else 0, total_records)
                        except Exception:
                            logging.error("Response not JSON or missing 'data' key from XHR")

                        rows = []
                        if data:
                            for item in data:
                                text_frag = ""
                                if isinstance(item, str):
                                    text_frag = item
                                elif isinstance(item, list):
                                    text_frag = " ".join([str(x) for x in item])
                                elif isinstance(item, dict):
                                    text_frag = " ".join([str(v) for v in item.values()])

                                # Prefer extracting an href attribute if present in the row HTML
                                href_m = re.search(r'href="([^"]+)"', text_frag)
                                href = href_m.group(1) if href_m else None

                                # Extract a date if present
                                date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", text_frag)
                                date_text = date_match.group(1) if date_match else None

                                rows.append({"href": href, "filing_date": date_text, "raw": {"text": text_frag}})

                        logging.info("Found %d filings via intercepted XHR", len(rows))

                        # Parse the XHR data and extract filing info
                        # Data is array of arrays: [firstName, lastName, fullName, linkHTML, date]
                        enriched = []
                        for item in data:
                            text_frag = ""
                            if isinstance(item, str):
                                text_frag = item
                            elif isinstance(item, list):
                                text_frag = " ".join([str(x) for x in item])
                            elif isinstance(item, dict):
                                text_frag = " ".join([str(v) for v in item.values()])

                            # Extract href and doc_id
                            href_m = re.search(r'href="([^"]+)"', text_frag)
                            href = href_m.group(1) if href_m else None

                            doc_id = None
                            html_content = None
                            if href and "/ptr/" in href:
                                doc_id_m = re.search(r"/ptr/([^/\"]+)", href)
                                doc_id = doc_id_m.group(1) if doc_id_m else None

                                # Fetch HTML from the view page
                                if doc_id:
                                    try:
                                        view_url = href if href.startswith("http") else (BASE_URL + href)
                                        logging.info("Visiting view page: %s", view_url)
                                        page.goto(view_url, timeout=30000)
                                        page.wait_for_load_state("networkidle", timeout=30000)

                                        # Get HTML content
                                        html_content = page.content()
                                        logging.info("Fetched HTML for doc_id: %s (%d bytes)", doc_id, len(html_content))
                                    except Exception:
                                        logging.exception("Failed to fetch HTML for %s", doc_id)

                            # Extract date
                            date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", text_frag)
                            date_text = date_match.group(1) if date_match else None

                            if doc_id:
                                view_url_full = href if href.startswith("http") else (BASE_URL + href)
                                enriched.append({
                                    "doc_id": doc_id,
                                    "href": href,
                                    "filing_date": date_text,
                                    "html_content": html_content,
                                    "source_url": view_url_full,
                                    "raw": {"text": text_frag}
                                })

                        cookies = page.context.cookies()
                        browser.close()
                        return enriched, cookies
                    except Exception:
                        logging.exception("Failed to intercept XHR; falling back to server-side POST")
                else:
                    logging.info("XHR interception disabled, using UI pagination by clicking through pages")

                    # Click search to trigger the initial results
                    if page.locator("button.btn-primary[type='submit']").count():
                        page.locator("button.btn-primary[type='submit']").first.click()
                    else:
                        page.click("button[type='submit']")

                    page.wait_for_load_state("networkidle")
                    logging.info("Initial search results loaded")

                    # Now scrape all pages by clicking Next
                    all_rows = []
                    page_num = 1

                    while True:
                        logging.info("Scraping page %d...", page_num)

                        # Wait for DataTable to load
                        page.wait_for_timeout(2000)

                        # Extract all rows from current page
                        try:
                            # DataTable rows are in <tbody> with <tr> elements
                            table_rows = page.locator("#filedReports tbody tr")
                            row_count = table_rows.count()
                            logging.info("Found %d rows on page %d", row_count, page_num)

                            for i in range(row_count):
                                row = table_rows.nth(i)
                                # Get all text content from the row
                                row_text = row.inner_text()

                                # Look for PTR links in the row
                                links = row.locator("a[href*='/ptr/']")
                                if links.count() > 0:
                                    href = links.first.get_attribute("href")
                                    doc_id_m = re.search(r"/ptr/([^/]+)", href)
                                    if doc_id_m:
                                        doc_id = doc_id_m.group(1)
                                        date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", row_text)
                                        date_text = date_match.group(1) if date_match else None

                                        # Construct full source URL
                                        source_url = href if href.startswith("http") else (BASE_URL + href)

                                        all_rows.append({
                                            "doc_id": doc_id,
                                            "filing_date": date_text,
                                            "source_url": source_url,
                                            "raw": {"text": row_text}
                                        })
                                        logging.debug("Found PTR filing: %s", doc_id)
                        except Exception:
                            logging.exception("Error scraping page %d", page_num)

                        # Check if there's a "Next" button and if it's enabled
                        next_button = page.locator(".dataTables_paginate .paginate_button.next:not(.disabled)")

                        if next_button.count() == 0:
                            logging.info("No more pages (Next button not found or disabled)")
                            break

                        # Click Next
                        try:
                            next_button.click()
                            page.wait_for_load_state("networkidle")
                            page_num += 1
                        except Exception:
                            logging.exception("Failed to click Next button")
                            break

                    logging.info("Found %d total PTR filings across %d pages", len(all_rows), page_num)
                    cookies = page.context.cookies()
                    browser.close()
                    return all_rows, cookies
            except Exception:
                logging.exception("Error during XHR interception attempt")

            # Fallback: extract cookies from Playwright and populate a requests.Session
            cookies = page.context.cookies()
            sess = requests.Session()
            for c in cookies:
                cookie = requests.cookies.create_cookie(name=c.get("name"), value=c.get("value"), domain=c.get("domain"))
                sess.cookies.set_cookie(cookie)

            # Try to find CSRF token in page (hidden input) or cookie
            csrf = None
            try:
                token_el = page.query_selector("input[name='csrfmiddlewaretoken']")
                if token_el:
                    csrf = token_el.get_attribute("value")
                    logging.info("Found CSRF token in form")
            except Exception:
                logging.debug("No csrf hidden input found via Playwright")

            if not csrf:
                csrf = sess.cookies.get("csrftoken")
                if csrf:
                    logging.info("Found CSRF token in cookies")

            headers = {
                "User-Agent": "Mozilla/5.0 Trade Transparency Platform",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
            }
            if csrf:
                headers["X-CSRFToken"] = csrf

            # Format dates to the site's expected MM/DD/YYYY and build the data payload
            def _fmt_date(dt_str: str) -> str:
                # Accept YYYY-MM-DD and convert to MM/DD/YYYY
                if not dt_str:
                    return ""
                for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%d/%m", "%m/%d/%y"):
                    try:
                        d = datetime.strptime(dt_str, fmt)
                        return d.strftime("%m/%d/%Y")  # Changed to YYYY format
                    except Exception:
                        continue
                # fallback: return original
                return dt_str

            ajax_url = SEARCH_URL.rstrip("/") + "/report/data/"
            base_payload = {
                # Filters (DataTables expects JSON-encoded lists for these fields on the site)
                "report_types": json.dumps([11]),  # Periodic Transactions
                # Ensure at least one filer type is selected: 1=Senator,4=Candidate,5=Former Senator
                "filer_types": json.dumps([1, 4, 5]),
                "submitted_start_date": _fmt_date(start_date),
                "submitted_end_date": _fmt_date(end_date),
                "candidate_state": "",
                "senator_state": "",
                "office_id": "",
                "first_name": "",
                "last_name": "",
            }

            # Pagination loop: fetch all pages
            rows: list[dict] = []
            page_size = 100  # Max results per request (Senate portal supports 25, 50, 75, 100)
            current_offset = 0
            draw_counter = 1
            total_records = None

            logging.info("Starting paginated AJAX requests (fallback)")

            while True:
                payload = {
                    **base_payload,
                    "draw": draw_counter,
                    "start": current_offset,
                    "length": page_size,
                }

                logging.info("Fetching page: offset=%d, length=%d (draw=%d)", current_offset, page_size, draw_counter)

                try:
                    resp = sess.post(ajax_url, data=payload, headers=headers, timeout=30)
                    resp.raise_for_status()
                except Exception:
                    logging.exception("AJAX request to report data endpoint failed (fallback)")
                    break

                # Save raw JSON for debugging (first page only)
                if draw_counter == 1:
                    try:
                        with open("debug_results_json.json", "w", encoding="utf-8") as fh:
                            fh.write(resp.text)
                    except Exception:
                        pass

                try:
                    json_response = resp.json()
                    data = json_response.get("data")

                    # Get total count from first response
                    if total_records is None:
                        total_records = json_response.get("recordsTotal", 0)
                        logging.info("Total records available: %d", total_records)
                except Exception:
                    logging.error("Response not JSON or missing 'data' key (fallback)")
                    break

                if not data:
                    logging.info("No more data in response, stopping pagination")
                    break

                # DataTables may return rows as arrays or HTML strings. Parse conservatively.
                page_rows = 0
                for item in data:
                    text_frag = ""
                    if isinstance(item, str):
                        text_frag = item
                    elif isinstance(item, list):
                        text_frag = " ".join([str(x) for x in item])
                    elif isinstance(item, dict):
                        text_frag = " ".join([str(v) for v in item.values()])

                    # Look for link to the PTR view (support both numeric and UUID formats)
                    m = re.search(r"/search/view/ptr/([^/\"'<>\s]+)", text_frag)
                    if not m:
                        m = re.search(r"/view/ptr/([^/\"'<>\s]+)", text_frag)
                    if m:
                        doc_id = m.group(1)
                        date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", text_frag)
                        date_text = date_match.group(1) if date_match else None
                        rows.append({"doc_id": str(doc_id), "filing_date": date_text, "raw": {"text": text_frag}})
                        page_rows += 1

                logging.info("Parsed %d filings from this page (total so far: %d)", page_rows, len(rows))

                # Check if we've reached the end
                if total_records and len(rows) >= total_records:
                    logging.info("Fetched all available records")
                    break

                if page_rows < page_size:
                    logging.info("Received fewer results than page size, assuming last page")
                    break

                # Move to next page
                current_offset += page_size
                draw_counter += 1

            logging.info("Found %d total filings via fallback AJAX across %d pages", len(rows), draw_counter)
            cookies = page.context.cookies()
            browser.close()
            return rows, cookies
        except Exception:
            logging.exception("Playwright run failed")
            try:
                cookies = page.context.cookies()
            except Exception:
                cookies = []
            try:
                browser.close()
            except Exception:
                pass
            return [], cookies