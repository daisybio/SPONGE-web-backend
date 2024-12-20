"""
Main module of the server file
"""

# local modules
import app.config as config
import os
from connexion.resolver import RelativeResolver


# Get the application instance
connex_app = config.connex_app

# Read the swagger.yml file to configure the endpoints
swagger_file = os.path.join(os.path.dirname(__file__), "swagger.yml")
connex_app.add_api(swagger_file, resolver=RelativeResolver('app.controllers'), options={"swagger_ui": True})

# create a URL route in our application for "/"
@connex_app.route("/")
def home():
    return "SPONGEdb API"

if __name__ == "__main__":
    print("serving on port: ", config.PORT)
    connex_app.run(port=config.PORT)

