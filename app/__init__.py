# Initialize the Flask application
from flask import Flask

# Create an instance of the Flask application
app = Flask(__name__)

# Import the routes module to register the application routes
from app import routes