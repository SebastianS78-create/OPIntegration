import os
from fastapi import FastAPI

from src.scraping.router import router as scraping_router

app = FastAPI(title="OPIntegration Monitoring")
app.include_router(scraping_router)


@app.get("/")
def root():
    return {"status": "ok", "service": "pepper-monitoring"}


@app.get("/health")
def health():
    return {"status": "healthy"}
