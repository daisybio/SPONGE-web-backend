"""
Main module of the server file
"""

# local modules
import app.config as config
import os
from connexion.resolver import RelativeResolver
import logging
import sys
from flask import request


# Get the application instance
connex_app = config.connex_app

# Configure logging to the console (stdout)
logging.basicConfig(
    stream=sys.stdout,  # Output to console
    level=logging.INFO,  # Logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@connex_app.app.before_request
def log_request():
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Body: {request.get_data(as_text=True)}")

# Read the swagger.yml file to configure the endpoints
swagger_file = os.path.join(os.path.dirname(__file__), "swagger.yml")
connex_app.add_api(swagger_file, resolver=RelativeResolver('app.controllers'))

# create a URL route in our application for "/"
@connex_app.route("/sponge-api/")
def home():
    return "SPONGEdb API"

if __name__ == "__main__":
    print("serving on port: ", config.PORT)
    connex_app.run(port=config.PORT)

