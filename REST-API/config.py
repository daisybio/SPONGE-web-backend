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

# Configure the SQLAlchemy part of the app instance
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:a6/4qpQYx]QA@10.162.163.20/sponge"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create the SQLAlchemy db instance
db = SQLAlchemy(app)

# Initialize Marshmallow
ma = Marshmallow(app)