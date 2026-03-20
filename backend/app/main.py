from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import wards, assets, ingest, scrape, questions, govdata, beneficiaries, notifications, regions
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Pramaan API",
    version="3.0.0",
    description="Global Ontology Engine - Micro-Accountability & Booth-Level Logic",
    lifespan=lifespan,
)

app.include_router(wards.router, prefix="/wards", tags=["wards"])
app.include_router(assets.router, prefix="/assets", tags=["assets"])
app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
app.include_router(scrape.router)
app.include_router(questions.router)
app.include_router(govdata.router)
app.include_router(beneficiaries.router, prefix="/beneficiaries", tags=["beneficiaries"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
app.include_router(regions.router, prefix="/regions", tags=["regions"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/scheduler/status", tags=["scheduler"])
def scheduler_status():
    """List scheduled jobs and their next run times."""
    from app.services.scheduler import _scheduler
    jobs = [
        {
            "id":       job.id,
            "name":     job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        }
        for job in _scheduler.get_jobs()
    ]
    return {"running": _scheduler.running, "jobs": jobs}
