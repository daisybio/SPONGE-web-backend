"""
Main module of the server file
"""
import os
from swagger_modifier import replaceAll

# local modules
import config

if __name__ == "__main__":
    replaceAll("swagger.yml", "- url", "- url: " + os.getenv("SPONGE_API_URL"))

    # Get the application instance
    connex_app = config.connex_app

    # Read the swagger.yml file to configure the endpoints
    connex_app.add_api("swagger.yml")
    connex_app.run()

