# Land Registry Backend - Render Deployment Guide

## Quick Deployment Steps

### 1. Prerequisites
- GitHub repository with your backend code
- Render account (free tier works)
- PostgreSQL database (can be created on Render)

### 2. Database Setup
1. Go to Render Dashboard
2. Create a new PostgreSQL database
3. Note the connection string (DATABASE_URL)

### 3. Web Service Deployment
1. Create new Web Service on Render
2. Connect your GitHub repository
3. Configure:
   - **Runtime**: Python 3.11.9
   - **Build Command**: `chmod +x build.sh && ./build.sh`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`

### 4. Environment Variables
Add these in Render Dashboard:
```
DATABASE_URL=<your-postgres-connection-string>
SECRET_KEY=<generate-random-secret>
JWT_SECRET_KEY=<generate-random-jwt-secret>
FLASK_ENV=production
FRONTEND_URL=https://your-frontend-domain.com
```

### 5. Custom Domain (Optional)
- Add your custom domain in Render settings
- Configure DNS to point to Render

## Troubleshooting

### Common Issues:

1. **Python 3.13 Compatibility Error**
   - Solution: Use `runtime.txt` with `python-3.11.9`

2. **psycopg2 Import Error**
   - Solution: Use `psycopg2-binary==2.9.9` in requirements.txt

3. **Database Connection Issues**
   - Check DATABASE_URL format
   - Ensure SSL mode is enabled for Neon/external DBs

4. **Build Failures**
   - Check build logs in Render dashboard
   - Verify all dependencies in requirements.txt

### Demo Credentials:
- Admin: username=`demo_admin`, password=`admin123`
- User: username=`demo_user`, password=`user123`

### API Endpoints:
- Health: `GET /health`
- Auth: `POST /api/auth/login`
- Profile: `GET /api/auth/profile`
- Lands: `GET /api/lands/`

## Files Created for Deployment:
- `runtime.txt` - Python version specification
- `Procfile` - Process definitions
- `build.sh` - Build script with DB initialization
- `render.yaml` - Render configuration
- `start.py` - Production startup script