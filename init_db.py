#!/usr/bin/env python3
"""Database initialization script"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Land, UserRole

def init_database():
    """Initialize the database with tables and demo data"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            
            # Create demo admin user
            admin = User.query.filter_by(username='demo_admin').first()
            if not admin:
                print("Creating demo admin user...")
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
            
            # Create demo user
            user = User.query.filter_by(username='demo_user').first()
            if not user:
                print("Creating demo user...")
                user = User(
                    username='demo_user',
                    email='user@demo.com',
                    first_name='Demo',
                    last_name='User',
                    role=UserRole.USER,
                    wallet_address='0x8ba1f109551bD432803012645Hac136c73c0d1b1',
                    phone='+1234567891',
                    address='456 User Avenue, City, Country'
                )
                user.set_password('user123')
                db.session.add(user)
            
            db.session.commit()
            
            # Create demo land records
            if user and Land.query.count() == 0:
                print("Creating demo land records...")
                demo_lands = [
                    {
                        'property_id': 'PROP001',
                        'title': 'Residential Plot in Downtown',
                        'description': 'Prime residential land in the heart of the city',
                        'location': 'Downtown District, Main City',
                        'area': 1500.0,
                        'property_type': 'residential',
                        'latitude': 40.7128,
                        'longitude': -74.0060,
                        'price': 150000.0,
                        'status': 'verified',
                        'is_verified': True
                    },
                    {
                        'property_id': 'PROP002',
                        'title': 'Commercial Land near Business Center',
                        'description': 'Excellent location for commercial development',
                        'location': 'Business District, Main City',
                        'area': 2500.0,
                        'property_type': 'commercial',
                        'latitude': 40.7589,
                        'longitude': -73.9851,
                        'price': 300000.0,
                        'status': 'verified',
                        'is_verified': True
                    },
                    {
                        'property_id': 'PROP003',
                        'title': 'Agricultural Land',
                        'description': 'Fertile agricultural land suitable for farming',
                        'location': 'Rural Area, County',
                        'area': 10000.0,
                        'property_type': 'agricultural',
                        'latitude': 40.6892,
                        'longitude': -74.0445,
                        'price': 75000.0,
                        'status': 'pending',
                        'is_verified': False
                    }
                ]
                
                for land_data in demo_lands:
                    land = Land(
                        owner_id=user.id,
                        wallet_address=user.wallet_address,
                        **land_data
                    )
                    db.session.add(land)
                
                db.session.commit()
            
            print("✅ Database initialized successfully!")
            print("Demo admin: username=demo_admin, password=admin123")
            print("Demo user: username=demo_user, password=user123")
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    init_database()