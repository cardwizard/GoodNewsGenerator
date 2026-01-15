import logging
from datetime import date, datetime, timedelta
from flask import current_app, session
from app.models import db, Article, APIRequest, FetchHistory
from app.services.rss_feed_service import fetch_articles_from_rss
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
        # Fetch new articles from RSS feeds
        articles = fetch_articles_from_rss()
        if not articles:
            logger.error("Failed to fetch articles from RSS feeds")
            return False

        # Store articles in database (automatically approved for scheduled fetches)
        for item in articles:
            try:
                article = Article(
                    title=item.get('title', 'No title'),
                    description=item.get('description'),
                    content=item.get('content'),
                    image_url=item.get('urlToImage'),
                    published_at=datetime.strptime(item['publishedAt'], '%Y-%m-%dT%H:%M:%SZ') if item.get('publishedAt') else None,
                    source_name=item['source']['name'] if isinstance(item.get('source'), dict) else 'Unknown',
                    source_url=item.get('url', ''),
                    source_type='auto',
                    status='approved'  # Scheduled fetches are auto-approved
                )
                db.session.add(article)
            except Exception as e:
                logger.error(f"Error processing article: {str(e)}")
                continue

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
        .filter_by(is_active=True, status='approved')\
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
    return Article.query.filter_by(is_active=True, status='approved').count()


# ==================== ARTICLE REVIEW FUNCTIONS ====================

def can_make_api_request():
    """Check if we can make an API request (rate limiting)"""
    today = date.today()
    api_request = APIRequest.query.filter_by(request_date=today).first()
    if api_request and api_request.request_count >= Config.MAX_DAILY_API_REQUESTS:
        return False
    return True


def increment_api_request_count():
    """Increment the API request counter for today"""
    today = date.today()
    api_request = APIRequest.query.filter_by(request_date=today).first()
    if api_request:
        api_request.request_count += 1
    else:
        api_request = APIRequest(request_date=today, request_count=1)
        db.session.add(api_request)


def fetch_articles_for_review(count=25):
    """
    Fetch articles from RSS feeds and save with 'pending' status
    Returns: (success: bool, article_count: int, error: str)
    """
    try:
        # Fetch from RSS feeds
        news_data = fetch_articles_from_rss(max_articles=count)

        if not news_data:
            return False, 0, "No articles returned from RSS feeds"

        # Save as pending
        articles_added = 0
        for item in news_data:
            try:
                article = Article(
                    title=item.get('title', 'No title'),
                    description=item.get('description'),
                    content=item.get('content'),
                    image_url=item.get('urlToImage'),
                    published_at=datetime.strptime(item['publishedAt'], '%Y-%m-%dT%H:%M:%SZ') if item.get('publishedAt') else None,
                    source_name=item['source']['name'] if isinstance(item.get('source'), dict) else 'Unknown',
                    source_url=item.get('url', ''),
                    source_type='auto',
                    status='pending'  # Key difference - articles start as pending
                )
                db.session.add(article)
                articles_added += 1
            except Exception as e:
                logger.error(f"Error processing article: {str(e)}")
                continue

        # Create fetch history record
        fetch_record = FetchHistory(
            fetched_by_id=session.get('user_id'),
            articles_fetched=articles_added
        )
        db.session.add(fetch_record)

        db.session.commit()
        logger.info(f"Fetched {articles_added} articles for review from RSS feeds")
        return True, articles_added, None

    except Exception as e:
        logger.error(f"Error fetching articles for review: {str(e)}")
        db.session.rollback()
        return False, 0, str(e)


def get_pending_articles():
    """Get all pending articles for review"""
    return Article.query\
        .filter_by(status='pending')\
        .order_by(Article.cached_at.desc())\
        .all()


def approve_article(article_id, admin_id):
    """Approve pending article"""
    try:
        article = Article.query.get(article_id)
        if article and article.status == 'pending':
            article.status = 'approved'
            article.reviewed_by_id = admin_id
            article.reviewed_at = datetime.utcnow()
            article.is_active = True
            db.session.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Error approving article {article_id}: {str(e)}")
        db.session.rollback()
        return False


def reject_article(article_id, admin_id):
    """Reject pending article"""
    try:
        article = Article.query.get(article_id)
        if article and article.status == 'pending':
            article.status = 'rejected'
            article.reviewed_by_id = admin_id
            article.reviewed_at = datetime.utcnow()
            article.is_active = False
            db.session.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Error rejecting article {article_id}: {str(e)}")
        db.session.rollback()
        return False
