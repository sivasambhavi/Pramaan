import logging
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from app.routers import wards, assets, ingest, scrape, questions, govdata, beneficiaries, notifications, regions, agents
from app.services.scheduler import start_scheduler, stop_scheduler

log = logging.getLogger("pramaan.startup")

_SEED_SCRIPT = Path(__file__).resolve().parents[2] / "backend" / "scripts" / "load_seed_data.py"


def _is_graph_empty() -> bool:
    """Return True if Neo4j has fewer than 5 nodes (effectively unseeded)."""
    try:
        from app.neo4j_client import get_session
        with get_session() as session:
            rec = session.run("MATCH (n) RETURN count(n) AS c").single()
            count = rec["c"] if rec else 0
            log.info("[startup] Neo4j node count: %d", count)
            return count < 5
    except Exception as e:
        log.warning("[startup] Could not check Neo4j node count: %s", e)
        return False   # do NOT auto-seed if Neo4j is unreachable — avoid masking connection errors


def _run_seed():
    """Run load_seed_data.py as a subprocess so it gets its own sys.path."""
    log.info("[startup] Graph is empty — running auto-seed from final_formalized CSVs …")
    result = subprocess.run(
        [sys.executable, str(_SEED_SCRIPT)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode == 0:
        log.info("[startup] ✅ Auto-seed complete.\n%s", result.stdout[-1500:])
    else:
        log.error("[startup] ❌ Auto-seed FAILED (exit %d):\n%s", result.returncode, result.stderr[-1500:])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Step 1: auto-seed if graph is empty ───────────────────────────────────
    if _is_graph_empty():
        _run_seed()
    else:
        log.info("[startup] Graph already seeded — skipping auto-seed.")

    # ── Step 2: start background scheduler ────────────────────────────────────
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
app.include_router(agents.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats", tags=["meta"])
def stats():
    """Live graph statistics for the landing page."""
    try:
        from app.neo4j_client import get_session
        with get_session() as session:
            rec = session.run("""
                CALL { MATCH (n)          RETURN count(n)  AS total_nodes }
                CALL { MATCH (a:Asset)    RETURN count(a)  AS assets      }
                CALL { MATCH (s:Scheme)   RETURN count(s)  AS schemes     }
                CALL { MATCH (e:Evidence) RETURN count(e)  AS evidence    }
                RETURN total_nodes, assets, schemes, evidence
            """).single()
            if rec:
                return {
                    "assets":      rec["assets"],
                    "schemes":     rec["schemes"],
                    "evidence":    rec["evidence"],
                    "total_nodes": rec["total_nodes"],
                }
    except Exception as e:
        log.warning("[stats] Neo4j query failed: %s", e)
    return {"assets": 0, "schemes": 0, "evidence": 0, "total_nodes": 0}


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
