from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field


class ScrapeStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    SKIPPED = "skipped"


class Product(BaseModel):
    id: str
    name: str
    url: str
    active: bool = True


class ScrapeResult(BaseModel):
    product_id: str
    date: date
    status: ScrapeStatus
    pages_scraped: int = 0
    pages_cleaned: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ScrapeError(BaseModel):
    id: str = Field(default_factory=lambda: "")
    product_id: str
    url: str
    error_type: str
    error_message: str
    date: date
    resolved: bool = False
    resolved_date: date | None = None
    retry_count: int = 0


class DailyStatusRow(BaseModel):
    product_id: str
    product_name: str
    url: str
    date: date
    status: ScrapeStatus
    pages_scraped: int
    pages_cleaned: int
    errors: int
    duration_seconds: float
