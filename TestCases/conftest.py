"""Pytest harness for SPONGEdb TestCases against DuckDB."""
import os
import sys
from pathlib import Path

from sqlalchemy.engine import make_url

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_CONTROLLERS_DIR = _BACKEND_DIR / "app" / "controllers"

# Controllers are imported as top-level modules (import dataset, ...).
sys.path.insert(0, str(_BACKEND_DIR))
sys.path.insert(0, str(_CONTROLLERS_DIR))

collect_ignore_glob = []

_uri = os.getenv("SPONGE_DB_URI")
_db_path = None
if _uri:
    try:
        _db_path = make_url(_uri).database
    except Exception:
        _db_path = None

if not _uri or not _db_path or not Path(_db_path).is_file():
    collect_ignore_glob.append("test_*.py")
else:
    # Import after SPONGE_DB_URI is known so the engine can open the file.
    from app.config import app, cache

    app.config["CACHE_TYPE"] = "NullCache"
    cache.init_app(app)
    # @cache.cached needs a request context; keep one for the whole session.
    _request_ctx = app.test_request_context()
    _request_ctx.push()
