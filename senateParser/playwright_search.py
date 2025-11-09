# senateParser/playwright_search.py
from playwright.sync_api import sync_playwright
from datetime import datetime
import logging
import requests
import re
import json

HOME_URL = "https://efdsearch.senate.gov/search/home/"
SEARCH_URL = "https://efdsearch.senate.gov/search/"

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
                logging.info("Clicking search submit and waiting for XHR response")
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
                    try:
                        data = resp.json().get("data")
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

                    # Enrich rows by visiting each view page in the browser and extracting
                    # a direct PDF link (iframe src or .pdf anchor). This ensures we have
                    # an absolute pdf_url that can be fetched with requests.
                    enriched = []
                    for r in rows:
                        href = r.get("href")
                        pdf_url = None
                        view_url = None
                        try:
                            if href:
                                view_url = href if href.startswith("http") else (SEARCH_URL.rstrip("/") + href)
                                logging.info("Visiting view page: %s", view_url)
                                page.goto(view_url)
                                page.wait_for_load_state("networkidle")

                                # Try to find an iframe with a PDF
                                try:
                                    iframe = page.query_selector("iframe")
                                    if iframe:
                                        src = iframe.get_attribute("src")
                                        if src and ".pdf" in src:
                                            pdf_url = src if src.startswith("http") else (SEARCH_URL.rstrip("/") + src)
                                except Exception:
                                    pass

                                # If no iframe PDF, look for a link to a PDF
                                if not pdf_url:
                                    try:
                                        a = page.query_selector("a[href*='.pdf']")
                                        if a:
                                            ah = a.get_attribute("href")
                                            if ah:
                                                pdf_url = ah if ah.startswith("http") else (SEARCH_URL.rstrip("/") + ah)
                                    except Exception:
                                        pass

                        except Exception:
                            logging.exception("Failed to fetch view page for href=%s", href)

                        r["view_url"] = view_url
                        r["pdf_url"] = pdf_url
                        enriched.append(r)

                    cookies = page.context.cookies()
                    browser.close()
                    return enriched, cookies
                except Exception:
                    logging.exception("Failed to intercept XHR; falling back to server-side POST")
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
            payload = {
                "draw": 1,
                "start": 0,
                "length": 1000,
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

            logging.info("AJAX payload (fallback): %s", payload)

            logging.info("Performing server-side AJAX request for reports (fallback)")
            try:
                resp = sess.post(ajax_url, data=payload, headers=headers, timeout=30)
                resp.raise_for_status()
            except Exception:
                logging.exception("AJAX request to report data endpoint failed (fallback)")
                cookies = page.context.cookies()
                browser.close()
                return [], cookies

            # Save raw JSON for debugging
            try:
                with open("debug_results_json.json", "w", encoding="utf-8") as fh:
                    fh.write(resp.text)
            except Exception:
                pass

            rows: list[dict] = []
            try:
                data = resp.json().get("data")
            except Exception:
                logging.error("Response not JSON or missing 'data' key (fallback)")
                browser.close()
                return rows

            # DataTables may return rows as arrays or HTML strings. Parse conservatively.
            for item in data:
                text_frag = ""
                if isinstance(item, str):
                    text_frag = item
                elif isinstance(item, list):
                    text_frag = " ".join([str(x) for x in item])
                elif isinstance(item, dict):
                    text_frag = " ".join([str(v) for v in item.values()])

                # Look for link to the PTR view
                m = re.search(r"/search/view/ptr/(\d+)", text_frag)
                if not m:
                    m = re.search(r"/view/ptr/(\d+)", text_frag)
                if m:
                    doc_id = m.group(1)
                    date_match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", text_frag)
                    date_text = date_match.group(1) if date_match else None
                    rows.append({"doc_id": str(doc_id), "filing_date": date_text, "raw": {"text": text_frag}})

            logging.info("Found %d filings via fallback AJAX", len(rows))
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