import logging
from datetime import date, datetime, timedelta
from flask import current_app
from app.models import db, Article, APIRequest
from app.services.news_api_service import fetch_good_news
from app.config import Config

logger = logging.getLogger(__name__)


def update_cache(app=None):
    """
    Update article cache by fetching new articles from NewsAPI

    Args:
        app: Flask application instance (for app context)

    Returns:
        bool: True if successful, False otherwise
    """
    if app:
        with app.app_context():
            return _update_cache_impl()
    else:
        return _update_cache_impl()


def _update_cache_impl():
    """Internal implementation of cache update"""
    try:
        today = date.today()

        # Check rate limiting
        api_request = APIRequest.query.filter_by(request_date=today).first()
        if api_request and api_request.request_count >= Config.MAX_DAILY_API_REQUESTS:
            logger.warning(f"Daily API limit reached: {api_request.request_count}")
            return False

        # Fetch new articles
        articles = fetch_good_news()
        if not articles:
            logger.error("Failed to fetch articles from NewsAPI")
            return False

        # Store articles in database
        for article_data in articles:
            article = Article(**article_data)
            db.session.add(article)

        # Increment API request counter
        if api_request:
            api_request.request_count += 1
        else:
            api_request = APIRequest(request_date=today, request_count=1)
            db.session.add(api_request)

        # Mark old articles as inactive
        cutoff_date = datetime.utcnow() - timedelta(days=Config.ARTICLE_RETENTION_DAYS)
        Article.query.filter(Article.cached_at < cutoff_date).update({'is_active': False})

        db.session.commit()
        logger.info(f"Successfully cached {len(articles)} articles")
        return True

    except Exception as e:
        logger.error(f"Error updating cache: {str(e)}")
        db.session.rollback()
        return False


def get_paginated_articles(page=1, per_page=5):
    """
    Retrieve paginated articles from cache

    Args:
        page: Page number (1-indexed)
        per_page: Number of articles per page

    Returns:
        list: List of Article objects
    """
    offset = (page - 1) * per_page

    articles = Article.query\
        .filter_by(is_active=True)\
        .order_by(Article.published_at.desc())\
        .offset(offset)\
        .limit(per_page)\
        .all()

    return articles


def get_api_request_count(request_date=None):
    """
    Get API request count for a specific date

    Args:
        request_date: Date to check (defaults to today)

    Returns:
        int: Number of requests made on that date
    """
    if request_date is None:
        request_date = date.today()

    api_request = APIRequest.query.filter_by(request_date=request_date).first()
    return api_request.request_count if api_request else 0


def get_total_cached_articles():
    """
    Get total number of active cached articles

    Returns:
        int: Count of active articles
    """
    return Article.query.filter_by(is_active=True).count()
