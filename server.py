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
base_path = os.getenv("SPONGE_API_BASE_PATH", "/sponge-api")

connex_app.add_api(
    swagger_file,
    resolver=RelativeResolver('app.controllers'),
    base_path=base_path,
    name="sponge_api_blueprint"
)

# create a URL route in our application for "/"
@connex_app.route(f"{base_path.rstrip('/')}/")
@connex_app.route("/")
def home():
    return "SPONGEdb API"

if __name__ == "__main__":
    print("serving on port: ", config.PORT)
    connex_app.run(port=config.PORT)
# Reload swagger spec update

