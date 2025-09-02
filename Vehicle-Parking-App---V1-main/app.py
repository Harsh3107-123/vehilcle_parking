# flask in package name and all above imports are required for the Flask application to run and they are basically classes and functions
# it is necessary to to import packages in correct order or else it will show error
from flask import Flask
# create an instance of the Flask class
app = Flask(__name__)
import config
import models
import routes
# Check if the script is being run directly
if __name__ == '__main__':
    # run the Flask application
    app.run()