"""
Main module of the server file
"""

# local modules
import config

# Get the application instance
connex_app = config.connex_app

# Read the swagger.yml file to configure the endpoints
connex_app.add_api("swagger.yml")

# create a URL route in our application for "/"
@connex_app.route("/")
def home():
    return "SPONGEdb API"

if __name__ == "__main__":
    print("serving on port: ", config.PORT)
    connex_app.run(port=config.PORT)

