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
    if (request.method == 'POST'):
        if (request.content_type.startswith('multipart/form-data')):
            body = {'args': request.args.to_dict(), 
                    'form': request.form.to_dict(), 
                    'files': {k: f'{v.read(1000)}...{v.seek(0)}' for k, v in request.files.items()}
                    }
    else:        
        body = request.get_data(as_text=True)
    logger.info(f"Body: {body[:1000] if len(body) > 1000 else body}")

@app.after_request
def add_header(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'max-age=0'
    return response

# Create the SQLAlchemy db instance
db = SQLAlchemy(app)

# Initialize Marshmallow
ma = Marshmallow(app)
