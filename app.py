from app import create_app, db
from app.models import User, Land, LandTransfer, LandDocument, UserRole
from flask_migrate import upgrade
import os

app = create_app()

@app.cli.command("init_db")
def init_db():
    """Initialize the database with tables and demo data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create demo admin user
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
        
        # Create demo user
        user = User.query.filter_by(username='demo_user').first()
        if not user:
            user = User(
                username='demo_user',
                email='user@demo.com',
                first_name='Demo',
                last_name='User',
                role=UserRole.USER,
                wallet_address='0x8ba1f109551bD432803012645aac136c73c0d1b1',
                phone='+1234567891',
                address='456 User Avenue, City, Country'
            )
            user.set_password('user123')
            db.session.add(user)
        
        db.session.commit()
        
        # Create demo land records
        if user and Land.query.count() == 0:
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
        
        print("Database initialized successfully!")
        print("Demo admin: username=demo_admin, password=admin123")
        print("Demo user: username=demo_user, password=user123")

@app.route('/api', methods=['GET'])
def api_info():
    """API information endpoint"""
    return {
        'name': 'Land Registry API',
        'version': '1.0.0',
        'description': 'Blockchain-based land registry system',
        'endpoints': {
            'auth': '/api/auth',
            'lands': '/api/lands',
            'admin': '/api/admin'
        }
    }, 200

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') != 'production')