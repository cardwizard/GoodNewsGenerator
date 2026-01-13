import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///good_news.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # NewsAPI Configuration
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')
    NEWS_API_BASE_URL = 'https://newsapi.org/v2'

    # Application Settings
    ARTICLES_PER_PAGE = 5
    MAX_DAILY_API_REQUESTS = 90  # Buffer for 100/day limit
    ARTICLE_RETENTION_DAYS = 7
