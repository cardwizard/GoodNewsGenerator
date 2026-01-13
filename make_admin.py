"""Script to make a user admin"""
import sys
from app import create_app
from app.models import db, User

app = create_app()

with app.app_context():
    if len(sys.argv) < 2:
        # No username provided, make first user admin
        user = User.query.first()
        if user:
            user.is_admin = True
            db.session.commit()
            print(f'User "{user.username}" is now admin!')
        else:
            print('No users found. Please register first.')
    else:
        # Make specific user admin
        username = sys.argv[1]
        user = User.query.filter_by(username=username).first()

        if user:
            user.is_admin = True
            db.session.commit()
            print(f'User "{user.username}" is now admin!')
        else:
            print(f'User "{username}" not found.')
            print('\nExisting users:')
            users = User.query.all()
            for u in users:
                admin_status = ' (admin)' if u.is_admin else ''
                print(f'  - {u.username}{admin_status}')
