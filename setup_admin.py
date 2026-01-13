"""Setup script to recreate database and make first user admin"""
from app import create_app
from app.models import db, User
from app.services.cache_service import update_cache

app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()
    print('Database recreated with new schema')

    # Fetch articles
    update_cache()
    print('Articles fetched and cached')

    # Make first user admin if exists
    user = User.query.first()
    if user:
        user.is_admin = True
        db.session.commit()
        print(f'User "{user.username}" is now admin')
    else:
        print('No users found. Register a new account and run this script again.')
