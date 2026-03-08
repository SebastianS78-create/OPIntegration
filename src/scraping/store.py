"""In-memory store for scraping data. Replace with database in production."""

from datetime import date
from uuid import uuid4

from .models import Product, ScrapeResult, ScrapeError, ScrapeStatus, DailyStatusRow


class ScrapingStore:
    def __init__(self):
        self.products: dict[str, Product] = {}
        self.results: list[ScrapeResult] = []
        self.errors: list[ScrapeError] = []

    def add_product(self, product: Product) -> Product:
        self.products[product.id] = product
        return product

    def get_products(self) -> list[Product]:
        return list(self.products.values())

    def add_result(self, result: ScrapeResult) -> ScrapeResult:
        self.results.append(result)
        return result

    def get_daily_status(self, target_date: date) -> list[DailyStatusRow]:
        rows = []
        for product in self.products.values():
            if not product.active:
                continue
            matching = [r for r in self.results
                        if r.product_id == product.id and r.date == target_date]
            if matching:
                result = matching[-1]
                rows.append(DailyStatusRow(
                    product_id=product.id,
                    product_name=product.name,
                    url=product.url,
                    date=target_date,
                    status=result.status,
                    pages_scraped=result.pages_scraped,
                    pages_cleaned=result.pages_cleaned,
                    errors=result.errors,
                    duration_seconds=result.duration_seconds,
                ))
            else:
                rows.append(DailyStatusRow(
                    product_id=product.id,
                    product_name=product.name,
                    url=product.url,
                    date=target_date,
                    status=ScrapeStatus.PENDING,
                    pages_scraped=0,
                    pages_cleaned=0,
                    errors=0,
                    duration_seconds=0.0,
                ))
        return rows

    def add_error(self, error: ScrapeError) -> ScrapeError:
        error.id = str(uuid4())
        self.errors.append(error)
        return error

    def get_unresolved_errors(self) -> list[ScrapeError]:
        return [e for e in self.errors if not e.resolved]

    def get_errors_by_product(self, product_id: str) -> list[ScrapeError]:
        return [e for e in self.errors if e.product_id == product_id]

    def resolve_error(self, error_id: str) -> ScrapeError | None:
        for error in self.errors:
            if error.id == error_id:
                error.resolved = True
                error.resolved_date = date.today()
                return error
        return None

    def get_retry_queue(self) -> list[ScrapeError]:
        """Get unresolved errors for retry — pages to revisit once fixed."""
        return [e for e in self.errors if not e.resolved]


# Shared instance
store = ScrapingStore()
