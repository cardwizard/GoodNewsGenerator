from app import create_app
from app.models import db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()
        print("Database initialized successfully!")

    print("Starting Good News Aggregator...")
    print("Access the application at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
