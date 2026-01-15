from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, abort
from app.auth import login_required
from app.services.cache_service import get_paginated_articles, get_total_cached_articles
from app.models import User, Article, ReadArticle, db
from app.config import Config
from sqlalchemy import and_

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
    show_read = request.args.get('show_read', 'false')  # Default: show only unread
    user_id = session['user_id']

    # Get articles based on read status
    query = Article.query.filter_by(is_active=True, status='approved')

    if show_read == 'false':
        # Show only unread articles (exclude articles in read_articles table for this user)
        read_article_ids = db.session.query(ReadArticle.article_id).filter_by(user_id=user_id).all()
        read_ids = [r[0] for r in read_article_ids]
        if read_ids:
            query = query.filter(~Article.id.in_(read_ids))
    elif show_read == 'only':
        # Show only read articles
        read_article_ids = db.session.query(ReadArticle.article_id).filter_by(user_id=user_id).all()
        read_ids = [r[0] for r in read_article_ids]
        if read_ids:
            query = query.filter(Article.id.in_(read_ids))
        else:
            query = query.filter(Article.id == -1)  # No read articles, return empty
    # If show_read == 'true', show all articles (no filtering)

    # Paginate
    articles = query.order_by(Article.published_at.desc())\
        .limit(Config.ARTICLES_PER_PAGE)\
        .offset((page - 1) * Config.ARTICLES_PER_PAGE)\
        .all()

    # Get user admin status
    user = User.query.get(user_id)
    is_admin = user.is_admin if user else False

    return render_template(
        'news_feed.html',
        articles=articles,
        page=page,
        show_read=show_read,
        username=session.get('username'),
        is_admin=is_admin
    )


@news_bp.route('/article/<int:article_id>')
@login_required
def article_detail(article_id):
    """View a single article"""
    article = Article.query.get(article_id)

    if not article or not article.is_active or article.status != 'approved':
        abort(404)

    # Get user admin status
    user = User.query.get(session['user_id'])
    is_admin = user.is_admin if user else False

    return render_template(
        'article_detail.html',
        article=article,
        username=session.get('username'),
        is_admin=is_admin
    )


@news_bp.route('/api/feed')
@login_required
def api_feed():
    """API endpoint for AJAX pagination"""
    page = request.args.get('page', 1, type=int)
    articles = get_paginated_articles(page=page, per_page=Config.ARTICLES_PER_PAGE)

    # Get current user_id for social data
    user_id = session.get('user_id')

    # Convert articles to dictionaries for JSON with user context
    articles_data = [article.to_dict(user_id=user_id) for article in articles]

    return jsonify(articles_data)
