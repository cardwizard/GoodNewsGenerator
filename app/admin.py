from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from datetime import datetime
from app.models import db, User, Article
from app.auth import login_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin access for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access admin panel', 'error')
            return redirect(url_for('auth.login'))

        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('Admin access required', 'error')
            return redirect(url_for('news.feed'))

        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard"""
    total_articles = Article.query.filter_by(is_active=True).count()
    manual_articles = Article.query.filter_by(source_type='manual', is_active=True).count()
    auto_articles = Article.query.filter_by(source_type='auto', is_active=True).count()

    recent_manual = Article.query.filter_by(source_type='manual', is_active=True)\
        .order_by(Article.cached_at.desc()).limit(10).all()

    return render_template(
        'admin/dashboard.html',
        total_articles=total_articles,
        manual_articles=manual_articles,
        auto_articles=auto_articles,
        recent_manual=recent_manual
    )


@admin_bp.route('/add-news', methods=['GET', 'POST'])
@admin_required
def add_news():
    """Add news article manually"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        url = request.form.get('url', '').strip()
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip()
        source_name = request.form.get('source_name', '').strip()

        # Validation
        if not title or not url:
            flash('Title and URL are required', 'error')
            return render_template('admin/add_news.html')

        # Create new article
        try:
            article = Article(
                title=title,
                description=description,
                content=description,  # Use description as content for manual entries
                image_url=image_url if image_url else None,
                source_url=url,
                source_name=source_name if source_name else 'Manual Entry',
                published_at=datetime.utcnow(),
                source_type='manual',
                added_by_id=session['user_id'],
                is_active=True
            )

            db.session.add(article)
            db.session.commit()

            flash('News article added successfully!', 'success')
            return redirect(url_for('admin.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding article: {str(e)}', 'error')
            return render_template('admin/add_news.html')

    return render_template('admin/add_news.html')


@admin_bp.route('/manage-news')
@admin_required
def manage_news():
    """Manage existing news articles"""
    # Get filter parameter
    filter_type = request.args.get('filter', 'all')

    query = Article.query.filter_by(is_active=True)

    if filter_type == 'manual':
        query = query.filter_by(source_type='manual')
    elif filter_type == 'auto':
        query = query.filter_by(source_type='auto')

    articles = query.order_by(Article.cached_at.desc()).all()

    return render_template(
        'admin/manage_news.html',
        articles=articles,
        filter_type=filter_type
    )


@admin_bp.route('/delete-news/<int:article_id>', methods=['POST'])
@admin_required
def delete_news(article_id):
    """Delete a news article"""
    article = Article.query.get_or_404(article_id)

    try:
        article.is_active = False
        db.session.commit()
        flash('Article deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting article: {str(e)}', 'error')

    return redirect(url_for('admin.manage_news'))


@admin_bp.route('/bulk-delete', methods=['POST'])
@admin_required
def bulk_delete():
    """Delete multiple articles"""
    article_ids = request.form.getlist('article_ids[]')

    if not article_ids:
        flash('No articles selected', 'error')
        return redirect(url_for('admin.manage_news'))

    try:
        count = Article.query.filter(Article.id.in_(article_ids)).update(
            {'is_active': False},
            synchronize_session=False
        )
        db.session.commit()
        flash(f'{count} article(s) deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting articles: {str(e)}', 'error')

    return redirect(url_for('admin.manage_news'))


@admin_bp.route('/delete-all-auto', methods=['POST'])
@admin_required
def delete_all_auto():
    """Delete all auto-fetched articles"""
    try:
        count = Article.query.filter_by(source_type='auto', is_active=True).update(
            {'is_active': False},
            synchronize_session=False
        )
        db.session.commit()
        flash(f'{count} auto-fetched article(s) deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting auto articles: {str(e)}', 'error')

    return redirect(url_for('admin.manage_news'))


@admin_bp.route('/delete-all-manual', methods=['POST'])
@admin_required
def delete_all_manual():
    """Delete all manually added articles"""
    try:
        count = Article.query.filter_by(source_type='manual', is_active=True).update(
            {'is_active': False},
            synchronize_session=False
        )
        db.session.commit()
        flash(f'{count} manual article(s) deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting manual articles: {str(e)}', 'error')

    return redirect(url_for('admin.manage_news'))


@admin_bp.route('/delete-all', methods=['POST'])
@admin_required
def delete_all():
    """Delete all articles"""
    try:
        count = Article.query.filter_by(is_active=True).update(
            {'is_active': False},
            synchronize_session=False
        )
        db.session.commit()
        flash(f'All {count} article(s) deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting all articles: {str(e)}', 'error')

    return redirect(url_for('admin.manage_news'))


@admin_bp.route('/edit-news/<int:article_id>', methods=['GET', 'POST'])
@admin_required
def edit_news(article_id):
    """Edit a news article"""
    article = Article.query.get_or_404(article_id)

    if request.method == 'POST':
        article.title = request.form.get('title', '').strip()
        article.source_url = request.form.get('url', '').strip()
        article.description = request.form.get('description', '').strip()
        article.content = article.description
        article.image_url = request.form.get('image_url', '').strip() or None
        article.source_name = request.form.get('source_name', '').strip()

        try:
            db.session.commit()
            flash('Article updated successfully!', 'success')
            return redirect(url_for('admin.manage_news'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating article: {str(e)}', 'error')

    return render_template('admin/edit_news.html', article=article)
