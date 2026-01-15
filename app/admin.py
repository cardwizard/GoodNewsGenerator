from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from datetime import datetime
import csv
import io
from app.models import db, User, Article, ReportedComment
from app.auth import login_required
from app.services.cache_service import (
    fetch_articles_for_review,
    get_pending_articles,
    approve_article,
    reject_article
)

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
    total_articles = Article.query.filter_by(is_active=True, status='approved').count()
    manual_articles = Article.query.filter_by(source_type='manual', is_active=True, status='approved').count()
    auto_articles = Article.query.filter_by(source_type='auto', is_active=True, status='approved').count()
    pending_count = Article.query.filter_by(status='pending').count()
    reports_count = ReportedComment.query.filter_by(is_resolved=False).count()

    recent_manual = Article.query.filter_by(source_type='manual', is_active=True)\
        .order_by(Article.cached_at.desc()).limit(10).all()

    return render_template(
        'admin/dashboard.html',
        total_articles=total_articles,
        manual_articles=manual_articles,
        auto_articles=auto_articles,
        recent_manual=recent_manual,
        pending_count=pending_count,
        reports_count=reports_count
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
        if not title or not url or not source_name:
            flash('Title, URL, and Source Name are required', 'error')
            return render_template('admin/add_news.html')

        # Create new article (pending approval)
        try:
            article = Article(
                title=title,
                description=description,
                content=description,  # Use description as content for manual entries
                image_url=image_url if image_url else None,
                source_url=url,
                source_name=source_name,
                published_at=datetime.utcnow(),
                source_type='manual',
                added_by_id=session['user_id'],
                status='pending',
                is_active=True
            )

            db.session.add(article)
            db.session.commit()

            flash('News article submitted for review!', 'success')
            return redirect(url_for('admin.review_articles'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding article: {str(e)}', 'error')
            return render_template('admin/add_news.html')

    return render_template('admin/add_news.html')


@admin_bp.route('/upload-csv', methods=['GET', 'POST'])
@admin_required
def upload_csv():
    """Upload articles from CSV file"""
    if request.method == 'POST':
        # Check if file was uploaded
        if 'csv_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('admin.upload_csv'))

        file = request.files['csv_file']

        # Check if file has a name
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('admin.upload_csv'))

        # Check file extension
        if not file.filename.endswith('.csv'):
            flash('File must be a CSV file', 'error')
            return redirect(url_for('admin.upload_csv'))

        try:
            # Read CSV file
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_reader = csv.DictReader(stream)

            # Validate CSV headers
            required_columns = ['title', 'url', 'source_name']
            optional_columns = ['description', 'image_url']

            if not csv_reader.fieldnames:
                flash('CSV file is empty', 'error')
                return redirect(url_for('admin.upload_csv'))

            # Normalize column names (case-insensitive, strip spaces)
            normalized_fieldnames = {name.lower().strip().replace(' ', '_'): name for name in csv_reader.fieldnames}

            # Check required columns
            missing_columns = []
            for col in required_columns:
                if col not in normalized_fieldnames and col.replace('_', ' ') not in normalized_fieldnames:
                    missing_columns.append(col)

            if missing_columns:
                flash(f'CSV is missing required columns: {", ".join(missing_columns)}', 'error')
                return redirect(url_for('admin.upload_csv'))

            # Process CSV rows
            articles_added = 0
            articles_skipped = 0
            errors = []

            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
                try:
                    # Get values using normalized column names
                    title = None
                    url = None
                    source_name = None
                    description = None
                    image_url = None

                    for key, value in row.items():
                        normalized_key = key.lower().strip().replace(' ', '_')
                        if normalized_key == 'title' or normalized_key == 'article_title':
                            title = value.strip()
                        elif normalized_key == 'url' or normalized_key == 'article_url':
                            url = value.strip()
                        elif normalized_key == 'source_name':
                            source_name = value.strip()
                        elif normalized_key == 'description':
                            description = value.strip()
                        elif normalized_key == 'image_url':
                            image_url = value.strip()

                    # Validate required fields
                    if not title or not url or not source_name:
                        articles_skipped += 1
                        errors.append(f'Row {row_num}: Missing required fields (title, url, or source_name)')
                        continue

                    # Create article (pending approval)
                    article = Article(
                        title=title,
                        description=description if description else None,
                        content=description if description else None,
                        image_url=image_url if image_url else None,
                        source_url=url,
                        source_name=source_name,
                        published_at=datetime.utcnow(),
                        source_type='manual',
                        added_by_id=session['user_id'],
                        status='pending',
                        is_active=True
                    )

                    db.session.add(article)
                    articles_added += 1

                except Exception as e:
                    articles_skipped += 1
                    errors.append(f'Row {row_num}: {str(e)}')
                    continue

            # Commit all articles
            db.session.commit()

            # Show results
            if articles_added > 0:
                flash(f'Successfully imported {articles_added} article(s) for review!', 'success')

            if articles_skipped > 0:
                flash(f'Skipped {articles_skipped} row(s) due to errors', 'error')

            if errors and len(errors) <= 10:  # Only show first 10 errors
                for error in errors[:10]:
                    flash(error, 'error')

            return redirect(url_for('admin.review_articles'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error processing CSV file: {str(e)}', 'error')
            return redirect(url_for('admin.upload_csv'))

    return render_template('admin/upload_csv.html')


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


# ==================== COMMENT MODERATION ROUTES ====================

@admin_bp.route('/moderation')
@admin_required
def moderation():
    """View reported comments for moderation"""
    # Get unresolved reports
    reports = ReportedComment.query.filter_by(is_resolved=False)\
        .order_by(ReportedComment.created_at.desc())\
        .all()

    # Get report data with comment and user info
    reports_data = []
    for report in reports:
        if report.comment.is_active:  # Only show active comments
            reports_data.append({
                'report': report,
                'comment': report.comment,
                'reporter': report.reported_by,
                'commenter': report.comment.user,
                'article': report.comment.article
            })

    return render_template(
        'admin/moderation.html',
        reports=reports_data
    )


@admin_bp.route('/moderation/resolve/<int:report_id>/<action>', methods=['POST'])
@admin_required
def resolve_report(report_id, action):
    """Resolve a reported comment (delete or dismiss)"""
    report = ReportedComment.query.get_or_404(report_id)

    try:
        if action == 'delete':
            # Delete the comment
            report.comment.is_active = False
            flash('Comment deleted successfully', 'success')
        elif action == 'dismiss':
            # Just dismiss the report
            flash('Report dismissed', 'info')
        else:
            flash('Invalid action', 'error')
            return redirect(url_for('admin.moderation'))

        # Mark report as resolved
        report.is_resolved = True
        report.resolved_at = datetime.utcnow()
        report.resolved_by_id = session['user_id']

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        flash(f'Error resolving report: {str(e)}', 'error')

    return redirect(url_for('admin.moderation'))


# ==================== ARTICLE REVIEW ROUTES ====================

@admin_bp.route('/review-articles')
@admin_required
def review_articles():
    """Show pending articles for review"""
    pending = get_pending_articles()
    return render_template('admin/review_articles.html', articles=pending)


@admin_bp.route('/fetch-articles', methods=['POST'])
@admin_required
def fetch_articles():
    """Trigger manual article fetch"""
    count = request.form.get('count', 25, type=int)

    # Limit to reasonable range
    count = max(10, min(count, 50))

    success, articles_count, error = fetch_articles_for_review(count)

    if success:
        flash(f'Successfully fetched {articles_count} articles for review', 'success')
    else:
        flash(f'Failed to fetch articles: {error}', 'error')

    return redirect(url_for('admin.review_articles'))


@admin_bp.route('/approve-article/<int:article_id>', methods=['POST'])
@admin_required
def approve_article_route(article_id):
    """Approve a pending article"""
    if approve_article(article_id, session['user_id']):
        flash('Article approved and published to feed', 'success')
    else:
        flash('Failed to approve article', 'error')

    return redirect(url_for('admin.review_articles'))


@admin_bp.route('/reject-article/<int:article_id>', methods=['POST'])
@admin_required
def reject_article_route(article_id):
    """Reject a pending article"""
    if reject_article(article_id, session['user_id']):
        flash('Article rejected', 'info')
    else:
        flash('Failed to reject article', 'error')

    return redirect(url_for('admin.review_articles'))


@admin_bp.route('/bulk-approve', methods=['POST'])
@admin_required
def bulk_approve():
    """Approve multiple articles at once"""
    article_ids = request.form.getlist('article_ids[]')
    approved_count = 0

    for article_id in article_ids:
        if approve_article(int(article_id), session['user_id']):
            approved_count += 1

    flash(f'Approved {approved_count} article(s)', 'success')
    return redirect(url_for('admin.review_articles'))


@admin_bp.route('/bulk-reject', methods=['POST'])
@admin_required
def bulk_reject():
    """Reject multiple articles at once"""
    article_ids = request.form.getlist('article_ids[]')
    rejected_count = 0

    for article_id in article_ids:
        if reject_article(int(article_id), session['user_id']):
            rejected_count += 1

    flash(f'Rejected {rejected_count} article(s)', 'info')
    return redirect(url_for('admin.review_articles'))
