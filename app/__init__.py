from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Database configuration with fallback
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Handle both psycopg2 and psycopg3 URL formats
        if database_url.startswith('postgres://'):
            # Convert postgres:// to postgresql:// for compatibility
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        elif database_url.startswith('postgresql://') and 'psycopg' not in database_url:
            # For psycopg3, we might need to specify the driver
            # but SQLAlchemy 2.0+ should auto-detect psycopg3
            pass
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Engine options for better connection handling
    engine_options = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Add SSL configuration for external databases like Neon
    if database_url and ('neon.tech' in database_url or 'amazonaws.com' in database_url):
        engine_options['connect_args'] = {'sslmode': 'require'}
    
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options
    
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-string')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    
    # Mail configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
    
    # File upload configuration
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    
    # Configure CORS
    CORS(app, origins=[os.getenv('FRONTEND_URL', 'http://localhost:3000')])
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        return {
            'message': 'Welcome to Land Registry API',
            'status': 'healthy',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'auth': '/api/auth/*',
                'lands': '/api/lands/*',
                'admin': '/api/admin/*'
            }
        }, 200
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return {
            'status': 'healthy',
            'message': 'Land Registry API is running',
            'version': '1.0.0'
        }, 200
    
    # Register blueprints
    from app.auth import auth_bp
    from app.lands import lands_bp
    from app.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(lands_bp, url_prefix='/api/lands')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    return app