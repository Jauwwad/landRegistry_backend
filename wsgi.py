#!/usr/bin/env python3
"""
WSGI entry point for production deployment on Render
"""
import os
import sys

# Set production environment
os.environ.setdefault('FLASK_ENV', 'production')

# Import Flask app
from app import create_app

# Create the application instance
app = create_app()

# Add some debugging info
print(f"Python version: {sys.version}")
print(f"Flask app created successfully")
print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")

if __name__ == "__main__":
    # For local development only
    port = int(os.environ.get("PORT", 5001))
    print(f"Starting development server on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)