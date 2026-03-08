"""API endpoints for scraping status dashboard."""

from datetime import date

from fastapi import APIRouter, HTTPException

from .models import Product, ScrapeResult, ScrapeError, DailyStatusRow
from .scraper import scrape_product, retry_failed_pages
from .store import store

router = APIRouter(prefix="/scraping", tags=["scraping"])


# --- Products ---

@router.post("/products", response_model=Product)
def add_product(product: Product):
    """Register a product for scraping."""
    return store.add_product(product)


@router.get("/products", response_model=list[Product])
def list_products():
    """List all registered products."""
    return store.get_products()


# --- Daily Status Table ---

@router.get("/status/daily", response_model=list[DailyStatusRow])
def daily_status(target_date: date | None = None):
    """Get daily scraping status table for all products.

    Shows status, pages scraped/cleaned, errors for each product on a given date.
    Defaults to today if no date provided.
    """
    if target_date is None:
        target_date = date.today()
    return store.get_daily_status(target_date)


# --- Scraping ---

@router.post("/scrape/{product_id}", response_model=ScrapeResult)
def scrape(product_id: str):
    """Trigger scraping for a specific product."""
    product = store.products.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return scrape_product(product)


@router.post("/scrape-all", response_model=list[ScrapeResult])
def scrape_all():
    """Trigger scraping for all active products."""
    results = []
    for product in store.get_products():
        if product.active:
            results.append(scrape_product(product))
    return results


# --- Error Tracking ---

@router.get("/errors", response_model=list[ScrapeError])
def list_errors(product_id: str | None = None, unresolved_only: bool = True):
    """Get error tracking table.

    Shows pages that failed scraping — to revisit once fixed.
    """
    if product_id:
        errors = store.get_errors_by_product(product_id)
    elif unresolved_only:
        errors = store.get_unresolved_errors()
    else:
        errors = store.errors
    return errors


@router.post("/errors/{error_id}/resolve", response_model=ScrapeError)
def resolve_error(error_id: str):
    """Mark an error as resolved."""
    error = store.resolve_error(error_id)
    if not error:
        raise HTTPException(status_code=404, detail=f"Error {error_id} not found")
    return error


@router.post("/retry", response_model=list[ScrapeResult])
def retry_failed():
    """Retry scraping for all products with unresolved errors."""
    return retry_failed_pages()
