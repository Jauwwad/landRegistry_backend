#!/usr/bin/env python3

import os
import sys
from app import create_app, db

def main():
    """
    Production startup script for Render deployment
    """
    try:
        print("Starting Land Registry API...")
        
        # Create Flask app
        app = create_app()
        
        # Test database connection
        with app.app_context():
            try:
                db.engine.execute('SELECT 1')
                print("✅ Database connection successful")
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                sys.exit(1)
        
        print("✅ Application initialized successfully")
        return app
        
    except Exception as e:
        print(f"❌ Application startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    app = main()
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)