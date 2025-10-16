#!/bin/bash

# Build script for Render deployment
echo "Starting deployment..."

# Install dependencies
pip install -r requirements.txt

# Set environment variables for production
export FLASK_ENV=production

# Initialize database
echo "Initializing database..."
python -c "
from app import create_app, db
from app.models import User, Land, LandTransfer, LandDocument, UserRole

app = create_app()
with app.app_context():
    try:
        db.create_all()
        print('Database tables created successfully')
        
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
            print('Demo admin created')
        else:
            print('Demo admin already exists')
            
    except Exception as e:
        print(f'Database initialization error: {e}')
        import traceback
        traceback.print_exc()
"

echo "Deployment completed!"