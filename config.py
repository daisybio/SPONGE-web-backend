import os
from connexion import FlaskApp
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

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


# change port to whatever is needed
PORT = 5555
UPLOAD_DIR = os.getenv("SPONGE_DB_UPLOAD_DIR")
MODEL_PATH = os.getenv("SPONGEFFECTS_MODEL_PATH")
SPONGEFFECTS_PREDICT_SCRIPT = os.getenv("SPONGEFFECTS_PREDICT_SCRIPT")

# Configure the SQLAlchemy part of the app instance
app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:spongebob@10.162.163.20:9669/SPONGEdb_v2"  # os.getenv("SPONGE_DB_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True
app.config['TESTING'] = True
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR

@app.after_request
def add_header(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'max-age=0'
    return response

# Create the SQLAlchemy db instance
db = SQLAlchemy(app)

# Initialize Marshmallow
ma = Marshmallow(app)
