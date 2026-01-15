#!/bin/bash

# Initialize database
python -c "from app import create_app; from app.models import db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized')"

# Start Gunicorn with 4 worker processes
gunicorn --bind=0.0.0.0:8000 --workers=4 --timeout=120 --access-logfile '-' --error-logfile '-' run:app
