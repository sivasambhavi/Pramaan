"""
api.py — PRAMAAN frontend shared HTTP client

All Streamlit pages import safe_get() / safe_post() from here instead of
calling requests directly. Benefits:

  • Automatic retry with exponential back-off (default 3 attempts)
  • Consistent timeout (default 10s)
  • Friendly st.error() shown on persistent failure instead of crashing
  • Single place to change BASE_URL, timeouts, or auth headers

Usage
-----
from utils.api import safe_get, safe_post

data = safe_get("/wards/REG_W45/assets")          # returns dict or None
data = safe_get("/wards/REG_W45/assets",
                params={"limit": 50}, timeout=15)

result = safe_post("/ingest/entities",
                   json={"entities": [], "relations": []})

If the call fails after all retries, both functions return None and
display a st.warning() so the page continues rendering (no crash).
"""

import time
import logging
import requests
import streamlit as st
from utils.constants import (
    API_BASE_URL as BASE_URL,
    API_RETRIES  as _RETRIES,
    API_DELAY    as _DELAY,
    API_BACKOFF  as _BACKOFF,
    API_TIMEOUT  as _TIMEOUT,
)

logger = logging.getLogger(__name__)

# Exceptions we consider transient (worth retrying)
_TRANSIENT = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    requests.exceptions.ChunkedEncodingError,
)


def _retry_request(method: str, path: str, **kwargs) -> requests.Response | None:
    """
    Internal: send an HTTP request with retry + exponential back-off.
    Returns a Response on success, None if all attempts fail.
    """
    url     = path if path.startswith("http") else f"{BASE_URL}{path}"
    timeout = kwargs.pop("timeout", _TIMEOUT)
    wait    = _DELAY

    for attempt in range(1, _RETRIES + 1):
        try:
            resp = requests.request(method, url, timeout=timeout, **kwargs)
            resp.raise_for_status()
            return resp
        except _TRANSIENT as exc:
            if attempt < _RETRIES:
                logger.warning(
                    "[api] %s %s — attempt %d/%d failed (%s). Retrying in %.1fs …",
                    method, path, attempt, _RETRIES, type(exc).__name__, wait,
                )
                time.sleep(wait)
                wait *= _BACKOFF
            else:
                logger.error(
                    "[api] %s %s — all %d attempts failed. Last: %s",
                    method, path, _RETRIES, exc,
                )
                return None
        except requests.exceptions.HTTPError as exc:
            # 4xx/5xx from server — don't retry, it won't help
            logger.error("[api] %s %s — HTTP %s", method, path, exc.response.status_code)
            return exc.response
        except Exception as exc:
            logger.error("[api] %s %s — unexpected error: %s", method, path, exc)
            return None

    return None


def safe_get(
    path: str,
    params: dict | None = None,
    timeout: int = _TIMEOUT,
    silent: bool = False,
) -> dict | None:
    """
    GET {BASE_URL}{path} with retry.

    Returns parsed JSON dict on success.
    Returns None on failure and shows st.warning() (unless silent=True).
    """
    resp = _retry_request("GET", path, params=params, timeout=timeout)
    if resp is None:
        if not silent:
            st.warning(
                f"Could not reach backend at `{path}`. "
                "Is the server running? Check `uvicorn backend.app.main:app`"
            )
        return None
    if not resp.ok:
        if not silent:
            st.warning(f"Backend returned {resp.status_code} for `{path}`")
        return None
    try:
        return resp.json()
    except Exception:
        logger.error("[api] GET %s — response is not JSON", path)
        return None


def safe_post(
    path: str,
    json: dict | None = None,
    data: dict | None = None,
    files: dict | None = None,
    timeout: int = _TIMEOUT,
    silent: bool = False,
) -> dict | None:
    """
    POST {BASE_URL}{path} with retry.

    Returns parsed JSON dict on success.
    Returns None on failure and shows st.warning() (unless silent=True).
    """
    resp = _retry_request("POST", path, json=json, data=data, files=files, timeout=timeout)
    if resp is None:
        if not silent:
            st.warning(
                f"POST to `{path}` failed after {_RETRIES} attempts. "
                "Backend may be down."
            )
        return None
    if not resp.ok:
        if not silent:
            st.warning(f"Backend returned {resp.status_code} for POST `{path}`")
        return None
    try:
        return resp.json()
    except Exception:
        logger.error("[api] POST %s — response is not JSON", path)
        return None


def safe_delete(path: str, timeout: int = _TIMEOUT, silent: bool = False) -> dict | None:
    """DELETE {BASE_URL}{path} with retry."""
    resp = _retry_request("DELETE", path, timeout=timeout)
    if resp is None or not resp.ok:
        if not silent:
            st.warning(f"DELETE `{path}` failed.")
        return None
    try:
        return resp.json()
    except Exception:
        return {}
