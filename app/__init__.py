from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from apscheduler.schedulers.background import BackgroundScheduler
from app.models import db
from app.config import Config

# Initialize extensions
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


def create_app():
    """Flask application factory"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    # Initialize security extensions
    csrf.init_app(app)
    limiter.init_app(app)

    # Register blueprints
    from app.auth import auth_bp
    from app.news import news_bp
    from app.admin import admin_bp
    from app.interactions import interactions_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(news_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(interactions_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Start background scheduler for daily cache refresh
    scheduler = BackgroundScheduler()
    with app.app_context():
        from app.services.cache_service import update_cache
        scheduler.add_job(
            func=lambda: update_cache(app),
            trigger='cron',
            hour=6,  # Run at 6 AM daily
            id='refresh_news_cache'
        )
    scheduler.start()

    return app
