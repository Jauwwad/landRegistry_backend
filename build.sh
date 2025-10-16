#!/bin/bash

# Build script for Render deployment
echo "Starting deployment with Python 3.13 and psycopg3..."

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
import psycopg
from urllib.parse import urlparse

database_url = os.getenv('DATABASE_URL')
if database_url:
    try:
        # Parse the URL for psycopg3
        parsed = urlparse(database_url)
        conn_params = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'dbname': parsed.path[1:],  # Remove leading /
            'user': parsed.username,
            'password': parsed.password,
            'sslmode': 'require'
        }
        
        with psycopg.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT version()')
                version = cur.fetchone()
                print(f'✅ Database connection successful: {version[0][:50]}...')
    except Exception as e:
        print(f'❌ Database connection test failed: {e}')
        exit(1)
else:
    print('❌ No DATABASE_URL provided')
    exit(1)
"

# Initialize database
echo "Initializing database with Flask-SQLAlchemy..."
python -c "
from app import create_app, db
from app.models import User, Land, LandTransfer, LandDocument, UserRole

app = create_app()
with app.app_context():
    try:
        # Create all tables
        db.create_all()
        print('✅ Database tables created successfully')
        
        # Create demo admin if not exists
        admin = User.query.filter_by(username='demo_admin').first()
        if not admin:
            admin = User(
                username='demo_admin',
                email='admin@demo.com',
                first_name='Demo',
                last_name='Admin',
                role=UserRole.ADMIN,
                wallet_address='0x742d35Cc6634C0532925a3b8D8976b4D23d4e57C',
                phone='+1234567890',
                address='123 Admin Street, City, Country'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('✅ Demo admin created')
        else:
            print('✅ Demo admin already exists')
            
    except Exception as e:
        print(f'❌ Database initialization error: {e}')
        import traceback
        traceback.print_exc()
        exit(1)
"

echo "✅ Deployment completed successfully!"