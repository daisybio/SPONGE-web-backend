import os
import connexion
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))

# Create the Connexion application instance
connex_app = connexion.App(__name__, specification_dir=basedir)

# Get the underlying Flask app instance
app = connex_app.app
CORS(app)

PORT = 5555
UPLOAD_DIR = os.getenv("SPONGE_DB_UPLOAD_DIR")
MODEL_DIR = os.getenv("SPONGEFFECTS_MODEL_DIR")
SPONGEFFECTS_PREDICT_SCRIPT = os.getenv("SPONGEFFECTS_PREDICT_SCRIPT")
WORK_DIR = os.getenv("WORK_DIR")

# Configure the SQLAlchemy part of the app instance
app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SPONGE_DB_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG '] = True
app.config['TESTING '] = True
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR

@app.after_request
def add_header(response):
    #response.cache_control.no_store = True
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'max-age=0'
    #print(memory_usage(-1, interval=.2, timeout=1), "after request")
    return response

# Create the SQLAlchemy db instance
db = SQLAlchemy(app)

# Initialize Marshmallow
ma = Marshmallow(app)
