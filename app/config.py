import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///good_news.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security Settings
    SESSION_COOKIE_SECURE = os.getenv('FLASK_ENV') == 'production'  # HTTPS only in production
    SESSION_COOKIE_HTTPONLY = True  # Not accessible via JavaScript
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour session timeout

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # CSRF tokens don't expire

    # Rate Limiting
    RATELIMIT_STORAGE_URL = "memory://"  # Use memory storage for rate limits
    RATELIMIT_STRATEGY = "fixed-window"

    # NewsAPI Configuration
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')
    NEWS_API_BASE_URL = 'https://newsapi.org/v2'

    # Application Settings
    ARTICLES_PER_PAGE = 5
    MAX_DAILY_API_REQUESTS = 90  # Buffer for 100/day limit
    ARTICLE_RETENTION_DAYS = 7

    # Security: Password & Account Settings
    MIN_PASSWORD_LENGTH = 8
    MAX_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_DURATION = 900  # 15 minutes in seconds
