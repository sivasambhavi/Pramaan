from fastapi import FastAPI
from app.routers import wards, assets, ingest, scrape, questions, govdata

app = FastAPI(title="Pramaan API", version="0.1.0")

app.include_router(wards.router, prefix="/wards", tags=["wards"])
app.include_router(assets.router, prefix="/assets", tags=["assets"])
app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
app.include_router(scrape.router)
app.include_router(questions.router)
app.include_router(govdata.router)


@app.get("/health")
def health():
    return {"status": "ok"}
