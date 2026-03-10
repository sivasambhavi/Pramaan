import sys, os
from contextlib import contextmanager
from neo4j import GraphDatabase

try:
    from app.config import settings
except ImportError:
    # Handle the case where the script is run from the frontend Streamlit app
    # Or if root is not in sys.path
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from backend.app.config import settings

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    return _driver


@contextmanager
def get_session():
    driver = get_driver()
    session = driver.session()
    try:
        yield session
    finally:
        session.close()


def close_driver():
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
