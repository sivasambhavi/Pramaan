from fastapi import FastAPI
from app.routers import wards, assets, ingest, scrape, questions, govdata, beneficiaries, notifications

app = FastAPI(title="Pramaan API", version="3.0.0", description="Global Ontology Engine - Micro-Accountability & Booth-Level Logic")

app.include_router(wards.router, prefix="/wards", tags=["wards"])
app.include_router(assets.router, prefix="/assets", tags=["assets"])
app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
app.include_router(scrape.router)
app.include_router(questions.router)
app.include_router(govdata.router)
app.include_router(beneficiaries.router, prefix="/beneficiaries", tags=["beneficiaries"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])


@app.get("/health")
def health():
    return {"status": "ok"}
