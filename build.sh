#!/bin/bash

# Build script for Render deployment
echo "Starting deployment with Python 3.11 and psycopg2-binary..."

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set environment variables for production
export FLASK_ENV=production

# Test database connection first
echo "Testing database connection..."
python -c "
import os
import psycopg2
from urllib.parse import urlparse

database_url = os.getenv('DATABASE_URL')
if database_url:
    try:
        # Test connection with psycopg2
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        cur.execute('SELECT version()')
        version = cur.fetchone()
        print(f'✅ Database connection successful: {version[0][:50]}...')
        cur.close()
        conn.close()
    except Exception as e:
        print(f'❌ Database connection test failed: {e}')
        exit(1)
else:
    print('❌ No DATABASE_URL provided')
    exit(1)
"

#!/bin/bash

# Build script for Render deployment
echo "Starting deployment build process..."

# Set environment for production
export FLASK_ENV=production

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Verify critical packages
echo "Verifying psycopg2-binary installation..."
python -c "import psycopg2; print('✅ psycopg2-binary installed successfully')" || echo "❌ psycopg2-binary installation failed"

echo "✅ Build completed successfully!"

echo "✅ Deployment completed successfully!"