"""
Main module of the server file
"""
import sys
import os

# local modules
import config

# Get the application instance
connex_app = config.connex_app

# Read the swagger.yml file to configure the endpoints
connex_app.add_api("swagger.yml")

@connex_app.route("/")
def home():
    return None

cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None


if __name__ == "__main__":
    connex_app.run()
