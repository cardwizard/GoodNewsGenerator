from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.auth import login_required
from app.services.cache_service import get_paginated_articles, get_total_cached_articles
from app.models import User
from app.config import Config

news_bp = Blueprint('news', __name__)


@news_bp.route('/')
def index():
    """Home page - redirect to feed if logged in, else login"""
    if 'user_id' in session:
        return redirect(url_for('news.feed'))
    return redirect(url_for('auth.login'))


@news_bp.route('/feed')
@login_required
def feed():
    """Main news feed page"""
    page = request.args.get('page', 1, type=int)
    articles = get_paginated_articles(page=page, per_page=Config.ARTICLES_PER_PAGE)
    total_articles = get_total_cached_articles()

    # Get user admin status
    user = User.query.get(session['user_id'])
    is_admin = user.is_admin if user else False

    return render_template(
        'news_feed.html',
        articles=articles,
        page=page,
        total_articles=total_articles,
        username=session.get('username'),
        is_admin=is_admin
    )


@news_bp.route('/api/feed')
@login_required
def api_feed():
    """API endpoint for AJAX pagination"""
    page = request.args.get('page', 1, type=int)
    articles = get_paginated_articles(page=page, per_page=Config.ARTICLES_PER_PAGE)

    # Convert articles to dictionaries for JSON
    articles_data = [article.to_dict() for article in articles]

    return jsonify(articles_data)
