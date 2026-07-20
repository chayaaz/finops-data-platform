from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import admin, analytics, anomalies, auth, budgets, dimensions, ingestion, issues, transactions, upload, vendors

settings = get_settings()

app = FastAPI(title="FinOps Data Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(transactions.router)
app.include_router(issues.router)
app.include_router(anomalies.router)
app.include_router(budgets.router)
app.include_router(vendors.router)
app.include_router(analytics.router)
app.include_router(admin.router)
app.include_router(ingestion.router)
app.include_router(dimensions.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
