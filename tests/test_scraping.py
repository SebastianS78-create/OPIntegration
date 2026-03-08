"""Tests for scraping status dashboard (OP-40).

Acceptance criteria:
1. Daily table to check scraping status for each product
2. Scrape new pages and make cleaning
3. Table to track errors to get back to pages once fixed
"""

from datetime import date

from fastapi.testclient import TestClient

from app import app
from src.scraping.models import ScrapeStatus
from src.scraping.store import store
from src.scraping.scraper import clean_text

client = TestClient(app)


def setup_function():
    """Reset store before each test."""
    store.products.clear()
    store.results.clear()
    store.errors.clear()


# --- Criterion 1: Daily status table ---

def test_daily_status_empty():
    resp = client.get("/scraping/status/daily")
    assert resp.status_code == 200
    assert resp.json() == []


def test_daily_status_after_scrape():
    # Register a product
    product = {"id": "p1", "name": "Test Product", "url": "https://example.com"}
    client.post("/scraping/products", json=product)

    # Scrape it
    client.post("/scraping/scrape/p1")

    # Check daily status
    resp = client.get("/scraping/status/daily")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["product_id"] == "p1"
    assert rows[0]["product_name"] == "Test Product"
    assert rows[0]["date"] == str(date.today())
    assert rows[0]["status"] == ScrapeStatus.SUCCESS


def test_daily_status_with_date_filter():
    product = {"id": "p2", "name": "Product 2", "url": "https://example.com/2"}
    client.post("/scraping/products", json=product)
    client.post("/scraping/scrape/p2")

    # Query for today — should have results
    resp = client.get(f"/scraping/status/daily?target_date={date.today()}")
    assert resp.status_code == 200
    rows = resp.json()
    today_products = [r for r in rows if r["product_id"] == "p2"]
    assert len(today_products) == 1

    # Query for a different date — product shows as PENDING (no scrape that day)
    resp = client.get("/scraping/status/daily?target_date=2020-01-01")
    assert resp.status_code == 200
    old_rows = [r for r in resp.json() if r["product_id"] == "p2"]
    assert len(old_rows) == 1
    assert old_rows[0]["status"] == ScrapeStatus.PENDING
    assert old_rows[0]["pages_scraped"] == 0


# --- Criterion 2: Scrape and clean pages ---

def test_clean_text_removes_html():
    raw = "<h1>Title</h1><p>Some <b>bold</b> text</p>"
    assert clean_text(raw) == "TitleSome bold text"


def test_clean_text_normalizes_whitespace():
    raw = "  lots   of    spaces  "
    assert clean_text(raw) == "lots of spaces"


def test_scrape_single_product():
    product = {"id": "s1", "name": "Scrape Test", "url": "https://example.com"}
    client.post("/scraping/products", json=product)

    resp = client.post("/scraping/scrape/s1")
    assert resp.status_code == 200
    result = resp.json()
    assert result["product_id"] == "s1"
    assert result["status"] == ScrapeStatus.SUCCESS
    assert result["pages_scraped"] == 3
    assert result["pages_cleaned"] == 3
    assert result["errors"] == 0


def test_scrape_all_products():
    client.post("/scraping/products", json={"id": "a1", "name": "A", "url": "https://a.com"})
    client.post("/scraping/products", json={"id": "a2", "name": "B", "url": "https://b.com"})

    resp = client.post("/scraping/scrape-all")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 2
    assert all(r["status"] == ScrapeStatus.SUCCESS for r in results)


def test_scrape_nonexistent_product():
    resp = client.post("/scraping/scrape/nonexistent")
    assert resp.status_code == 404


# --- Criterion 3: Error tracking table ---

def test_errors_empty():
    resp = client.get("/scraping/errors")
    assert resp.status_code == 200
    assert resp.json() == []


def test_add_and_list_products():
    product = {"id": "e1", "name": "Error Test", "url": "https://example.com"}
    resp = client.post("/scraping/products", json=product)
    assert resp.status_code == 200

    resp = client.get("/scraping/products")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["id"] == "e1"


def test_resolve_error():
    from src.scraping.models import ScrapeError

    error = ScrapeError(
        product_id="r1",
        url="https://example.com/page/1",
        error_type="test_error",
        error_message="test failure",
        date=date.today(),
    )
    store.add_error(error)
    error_id = store.errors[0].id

    # Error shows up in unresolved list
    resp = client.get("/scraping/errors?unresolved_only=true")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # Resolve it
    resp = client.post(f"/scraping/errors/{error_id}/resolve")
    assert resp.status_code == 200
    assert resp.json()["resolved"] is True

    # No longer in unresolved list
    resp = client.get("/scraping/errors?unresolved_only=true")
    assert resp.status_code == 200
    assert resp.json() == []


def test_retry_failed():
    resp = client.post("/scraping/retry")
    assert resp.status_code == 200
    assert resp.json() == []


def test_errors_filter_by_product():
    from src.scraping.models import ScrapeError

    for pid in ["fp1", "fp2"]:
        store.add_error(ScrapeError(
            product_id=pid,
            url=f"https://example.com/{pid}",
            error_type="test_error",
            error_message="fail",
            date=date.today(),
        ))

    resp = client.get("/scraping/errors?product_id=fp1&unresolved_only=false")
    assert resp.status_code == 200
    errors = resp.json()
    assert len(errors) == 1
    assert errors[0]["product_id"] == "fp1"
