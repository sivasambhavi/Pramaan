import logging
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from app.routers import ontology, scrape, ingest, citizen_report, agentic, crisis
from app.services.scheduler import start_scheduler, stop_scheduler, set_news_refresh_interval, get_scheduler_status

log = logging.getLogger("pramaan.startup")

_SEED_SCRIPT = Path(__file__).resolve().parents[2] / "backend" / "scripts" / "load_ontology.py"


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
        return False


def _run_seed():
    """Run load_ontology.py as a subprocess to seed the graph."""
    log.info("[startup] Graph is empty — running auto-seed from seed_graph.json …")
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
    if _is_graph_empty():
        _run_seed()
    else:
        log.info("[startup] Graph already seeded — skipping auto-seed.")
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="PRAMAAN API",
    version="4.0.0",
    description="Global Ontology Engine — India Intelligence Graph",
    lifespan=lifespan,
)

app.include_router(ontology.router)
app.include_router(scrape.router)
app.include_router(ingest.router)
app.include_router(citizen_report.router)
app.include_router(agentic.router)
app.include_router(crisis.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/scheduler/status", tags=["scheduler"])
def scheduler_status():
    """Current scheduler state — job names, intervals, next run times."""
    return get_scheduler_status()


@app.post("/scheduler/set-interval", tags=["scheduler"])
def scheduler_set_interval(minutes: int):
    """Reschedule news_refresh to run every N minutes (min 5, max 1440)."""
    minutes = max(5, min(1440, minutes))
    set_news_refresh_interval(minutes)
    return {"ok": True, "news_refresh_every_minutes": minutes}


@app.get("/stats", tags=["meta"])
def stats():
    """Live graph statistics — v5 governance metrics."""
    try:
        from app.neo4j_client import get_session
        with get_session() as session:
            rec = session.run("""
                CALL { MATCH (n)                          RETURN count(n)    AS total_nodes  }
                CALL { MATCH (e:Event)                    RETURN count(e)    AS events       }
                CALL { MATCH (d:Domain)                   RETURN count(d)    AS domains      }
                CALL { MATCH (a:Actor)                    RETURN count(a)    AS actors       }
                CALL { MATCH (ev:Evidence)                RETURN count(ev)   AS evidence     }
                CALL { MATCH ()-[r]->()                   RETURN count(r)    AS total_edges  }
                CALL { MATCH (s:Scheme)                   RETURN count(s)    AS schemes      }
                CALL { MATCH (ast:Asset)                  RETURN count(ast)  AS assets       }
                CALL { MATCH (ast:Asset {status:'completed'}) RETURN count(ast) AS verified_assets }
                CALL { MATCH (s:Scheme)
                       WHERE s.budget_crore IS NOT NULL
                       RETURN sum(toFloat(s.budget_crore)) AS funds_tracked }
                RETURN total_nodes, events, domains, actors, evidence, total_edges,
                       schemes, assets, verified_assets, funds_tracked
            """).single()
            if rec:
                return {
                    "events":          rec["events"],
                    "domains":         rec["domains"],
                    "actors":          rec["actors"],
                    "evidence":        rec["evidence"],
                    "total_nodes":     rec["total_nodes"],
                    "total_edges":     rec["total_edges"],
                    "schemes":         rec["schemes"],
                    "assets":          rec["assets"],
                    "verified_assets": rec["verified_assets"],
                    "funds_tracked":   rec["funds_tracked"] or 0,
                }
    except Exception as e:
        log.warning("[stats] Neo4j query failed: %s", e)
    return {
        "total_nodes": 0, "events": 0, "domains": 0, "actors": 0,
        "evidence": 0, "total_edges": 0, "schemes": 0, "assets": 0,
        "verified_assets": 0, "funds_tracked": 0,
    }
