import os
from connexion import FlaskApp
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
import logging
import sys
from flask import request
from flask_caching import Cache


basedir = os.path.abspath(os.path.dirname(__file__))

# Create the Connexion application instance
connex_app = FlaskApp(__name__, specification_dir=basedir)

# Get the underlying Flask app instance
app = connex_app.app

# Prevent trailing-slash redirects (301) which browsers follow as GET,
# turning POST requests into GET and causing 405 Method Not Allowed
app.url_map.strict_slashes = False

# CORS(connex_app)
connex_app.add_middleware(
    CORSMiddleware,
    position=MiddlewarePosition.BEFORE_EXCEPTION,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging to the console (stdout)
logging.basicConfig(
    stream=sys.stdout,  # Output to console
    level=logging.INFO,  # Logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# change port to whatever is needed
PORT = 5555
UPLOAD_DIR = os.getenv("SPONGE_DB_UPLOAD_DIR")
MODEL_PATH = os.getenv("SPONGEFFECTS_MODEL_PATH")
SPONGEFFECTS_PREDICT_SCRIPT = os.getenv("SPONGEFFECTS_PREDICT_SCRIPT")
# R worker processes per prediction request (each concurrent request starts its own). OE enrichment
# is memory-bound (~12 bytes x upload rows x 1000 per module task), so more workers stop helping early:
# on a 12-core M-series Mac 6 was fastest, 8 no faster, 12 three to four times slower than 6.
SPONGEFFECTS_CORES = int(os.getenv("SPONGEFFECTS_CORES", 6))
# prediction jobs running R at the same time, across all gunicorn workers; further jobs wait queued.
# Each uses SPONGEFFECTS_CORES workers and, for OE, ~12 bytes x upload rows x 1000 of memory per worker.
SPONGEFFECTS_MAX_JOBS = int(os.getenv("SPONGEFFECTS_MAX_JOBS", 2))
# seconds before a prediction's R process is killed
SPONGEFFECTS_TIMEOUT = int(os.getenv("SPONGEFFECTS_TIMEOUT", 3600))
# prediction job files (upload, result, log) older than this are deleted when a new job is submitted
SPONGEFFECTS_JOB_TTL_HOURS = int(os.getenv("SPONGEFFECTS_JOB_TTL_HOURS", 24))

# latest database version 
LATEST = 2

# Configure the SQLAlchemy part of the app instance
app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SPONGE_DB_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True
app.config['TESTING'] = True
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
# Configure Flask-Caching with redis
app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
app.config['CACHE_DEFAULT_TIMEOUT'] = 60 * 60 * 24 * 30  # 30 days default

cache = Cache(app)
cache.init_app(app)

from app.config import cache
from flask import jsonify

@connex_app.route("/test-cache")
def test_cache():
    cache.set("hello", "world", timeout=60)
    value = cache.get("hello")
    return jsonify({"cached_value": value})

@connex_app.app.before_request
def log_request():
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    body = ''
    if request.method == 'POST':
        if request.content_type and request.content_type.startswith('multipart/form-data'):
            body = str({'args': request.args.to_dict(),
                    'form': request.form.to_dict(),
                    'files': list(request.files.keys())})
        else:
            body = request.get_data(as_text=True)
    logger.info(f"Body: {body[:1000] if len(body) > 1000 else body}")

@app.after_request
def add_header(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'max-age=0'
    return response

# DuckDB: case-insensitive LIKE (nocase does not cover LIKE) and engine options
import duckdb_engine
from sqlalchemy.dialects.postgresql.base import PGCompiler

class _CaseInsensitiveLikeCompiler(duckdb_engine.Dialect.statement_compiler):
    visit_like_op_binary = PGCompiler.visit_ilike_op_binary
    visit_not_like_op_binary = PGCompiler.visit_not_ilike_op_binary

duckdb_engine.Dialect.statement_compiler = _CaseInsensitiveLikeCompiler

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "connect_args": {
        "read_only": True,
        "config": {"memory_limit": "64GB", "threads": 16, "default_collation": "nocase"},
    }
}

# Create the SQLAlchemy db instance
db = SQLAlchemy(app)

# Initialize Marshmallow
ma = Marshmallow(app)
