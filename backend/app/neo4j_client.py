import sys, os
import time
import logging
from contextlib import contextmanager
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, SessionExpired

logger = logging.getLogger(__name__)

try:
    from app.config import settings
except ImportError:
    # Handle the case where the script is run from the frontend Streamlit app
    # Or if root is not in sys.path
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from backend.app.config import settings

_driver = None

_RECONNECT_ATTEMPTS = 3
_RECONNECT_DELAY    = 2  # seconds


def get_driver():
    """Return (or lazily create) the Neo4j driver, verifying connectivity."""
    global _driver
    if _driver is None:
        _driver = _create_driver()
    return _driver


def _create_driver():
    """Create a new Neo4j driver and verify the connection."""
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    driver.verify_connectivity()
    logger.info("Neo4j driver connected to %s", settings.neo4j_uri)
    return driver


def _reconnect() -> bool:
    """
    Attempt to close the stale driver and establish a fresh connection.
    Returns True if successful, False after all retries are exhausted.
    """
    global _driver
    close_driver()
    for attempt in range(1, _RECONNECT_ATTEMPTS + 1):
        try:
            logger.warning("Neo4j reconnect attempt %d/%d …", attempt, _RECONNECT_ATTEMPTS)
            _driver = _create_driver()
            return True
        except Exception as exc:
            logger.error("Reconnect attempt %d failed: %s", attempt, exc)
            if attempt < _RECONNECT_ATTEMPTS:
                time.sleep(_RECONNECT_DELAY)
    return False


@contextmanager
def get_session():
    """
    Yield a Neo4j session.  On transient network errors (ServiceUnavailable /
    SessionExpired) the driver is automatically reconnected once before
    propagating the exception.
    """
    driver = get_driver()
    session = driver.session()
    try:
        yield session
    except (ServiceUnavailable, SessionExpired) as exc:
        logger.error("Neo4j session error: %s — attempting reconnect", exc)
        session.close()
        if _reconnect():
            # Surface a clear message so the caller can retry its request
            raise ServiceUnavailable(
                "Neo4j connection was lost and has been restored. Please retry."
            ) from exc
        raise
    finally:
        try:
            session.close()
        except Exception:
            pass


def close_driver():
    global _driver
    if _driver is not None:
        try:
            _driver.close()
        except Exception:
            pass
        _driver = None
