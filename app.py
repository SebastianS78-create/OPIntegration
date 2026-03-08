import os
from fastapi import FastAPI

app = FastAPI(title="OPIntegration Monitoring")


@app.get("/")
def root():
    return {"status": "ok", "service": "pepper-monitoring"}


@app.get("/health")
def health():
    return {"status": "healthy"}
