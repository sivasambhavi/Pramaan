import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Resolve .env from project root regardless of working directory
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    neo4j_uri:      str = "bolt://localhost:7687"
    neo4j_user:     str = "neo4j"
    neo4j_password: str = "password"      # override in .env: NEO4J_PASSWORD=pramaa2026
    groq_api_key:   str = ""              # override in .env: GROQ_API_KEY=<key>
    pramaan_env:    str = "development"
    google_api_key: str = ""
    api_base_url:   str = "http://localhost:8000"

    class Config:
        env_file = str(_ENV_FILE)
        extra = "ignore"


settings = Settings()

# ── Source domain whitelist ────────────────────────────────────────────────────
# v1: Minimal high-signal official Indian government sources.
# Covers all 7 domains: Climate, Defense, Economics, Society, Governance, Geopolitics, Technology.
ALLOWED_SOURCE_DOMAINS_V1: set[str] = {
    "pib.gov.in",           # Press Information Bureau — all press releases (all domains)
    "ndma.gov.in",          # NDMA — disaster policies, advisories, situation reports (Climate)
    "mausam.imd.gov.in",    # IMD operational — cyclone/weather products (Climate)
    "imd.gov.in",           # IMD main — bulletins, city forecasts, press releases (Climate)
    "isro.gov.in",          # ISRO — missions, space tech, emergency mgmt (Technology)
    "nrsc.gov.in",          # NRSC/NDEM — satellite disaster imagery (Climate, Governance)
    "ndrf.gov.in",          # NDRF — deployment orders, situation notes (Society, Governance)
    "ndap.niti.gov.in",     # NDAP — cross-sector datasets for India (Economics, Society, Tech)
}

# v2: Extended whitelist — add via env var, no code change needed.
# Set: PRAMAAN_EXTRA_ALLOWED_DOMAINS="nidm.gov.in,iced.niti.gov.in,data.gov.in,niti.gov.in"
_extra = os.getenv("PRAMAAN_EXTRA_ALLOWED_DOMAINS", "")
_extra_domains: set[str] = {d.strip() for d in _extra.split(",") if d.strip()}

ALLOWED_SOURCE_DOMAINS: set[str] = ALLOWED_SOURCE_DOMAINS_V1 | _extra_domains


def is_allowed_source(url: str) -> bool:
    """Return True if the URL's domain is in the allowed whitelist."""
    try:
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ""
        # Match exact domain or any subdomain (e.g. "rsmcnewdelhi.imd.gov.in" → "imd.gov.in")
        return any(host == d or host.endswith("." + d) for d in ALLOWED_SOURCE_DOMAINS)
    except Exception:
        return False
