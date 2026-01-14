# Entry point for the Flask application
# Import the Flask app instance from the app package
from app import app

# Run the Flask application in debug mode
if __name__ == "__main__":
    app.run(debug=True)