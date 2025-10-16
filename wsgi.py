# Python 3.13 compatibility fixes for deployment

import sys
import os

# Ensure we're using the right Python version context
if sys.version_info >= (3, 13):
    print(f"Running on Python {sys.version}")
    print("Using psycopg3 for Python 3.13 compatibility")
    
# Set environment variables for production deployment
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('PYTHON_VERSION', '3.13')

# Import and run the Flask app
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)