"""Scraping and cleaning logic for product pages."""

import re
import time
from datetime import date

from .models import Product, ScrapeResult, ScrapeError, ScrapeStatus
from .store import store


def clean_text(raw_html: str) -> str:
    """Remove HTML tags and normalize whitespace."""
    text = re.sub(r"<[^>]+>", "", raw_html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def scrape_product(product: Product) -> ScrapeResult:
    """Scrape all pages for a product, clean data, track errors."""
    start = time.time()
    pages_scraped = 0
    pages_cleaned = 0
    error_count = 0
    errors: list[ScrapeError] = []

    try:
        # Simulate scraping pages (replace with real HTTP requests in production)
        raw_pages = _fetch_pages(product.url)
        pages_scraped = len(raw_pages)

        # Clean each page
        for page_url, raw_content in raw_pages:
            try:
                cleaned = clean_text(raw_content)
                if cleaned:
                    pages_cleaned += 1
            except Exception as e:
                error_count += 1
                errors.append(ScrapeError(
                    product_id=product.id,
                    url=page_url,
                    error_type="cleaning_error",
                    error_message=str(e),
                    date=date.today(),
                ))

        status = ScrapeStatus.SUCCESS if error_count == 0 else ScrapeStatus.FAILED

    except Exception as e:
        status = ScrapeStatus.FAILED
        error_count += 1
        errors.append(ScrapeError(
            product_id=product.id,
            url=product.url,
            error_type="scrape_error",
            error_message=str(e),
            date=date.today(),
        ))

    duration = time.time() - start

    # Store errors
    for err in errors:
        store.add_error(err)

    # Store result
    result = ScrapeResult(
        product_id=product.id,
        date=date.today(),
        status=status,
        pages_scraped=pages_scraped,
        pages_cleaned=pages_cleaned,
        errors=error_count,
        duration_seconds=round(duration, 2),
    )
    store.add_result(result)
    return result


def _fetch_pages(base_url: str) -> list[tuple[str, str]]:
    """Fetch pages from URL. Returns list of (page_url, raw_html).

    In production, replace with real HTTP requests (httpx/aiohttp).
    Currently returns sample data for testing.
    """
    return [
        (f"{base_url}/page/1", "<h1>Product A</h1><p>Description of product</p>"),
        (f"{base_url}/page/2", "<h1>Product B</h1><p>Another product details</p>"),
        (f"{base_url}/page/3", "<div class='price'>99.99 PLN</div>"),
    ]


def retry_failed_pages() -> list[ScrapeResult]:
    """Retry scraping for all products with unresolved errors."""
    results = []
    retry_queue = store.get_retry_queue()

    # Group errors by product
    products_to_retry: set[str] = set()
    for error in retry_queue:
        products_to_retry.add(error.product_id)

    for product_id in products_to_retry:
        product = store.products.get(product_id)
        if product:
            result = scrape_product(product)
            results.append(result)
    return results
