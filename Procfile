web: gunicorn app:app --bind 0.0.0.0:$PORT
release: python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"