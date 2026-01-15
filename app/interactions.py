from flask import Blueprint, request, jsonify, session
from app.auth import login_required
from app.models import db, Article, Like, Comment, ReportedComment, User, HappinessRating, ReadArticle
from datetime import datetime

interactions_bp = Blueprint('interactions', __name__, url_prefix='/api')

# ==================== LIKE ENDPOINTS ====================

@interactions_bp.route('/articles/<int:article_id>/like', methods=['POST'])
@login_required
def toggle_like(article_id):
    """Toggle like on an article"""
    user_id = session['user_id']
    article = Article.query.get_or_404(article_id)

    # Check if user already liked
    existing_like = Like.query.filter_by(
        user_id=user_id,
        article_id=article_id
    ).first()

    try:
        if existing_like:
            # Unlike
            db.session.delete(existing_like)
            db.session.commit()
            action = 'unliked'
        else:
            # Like
            new_like = Like(user_id=user_id, article_id=article_id)
            db.session.add(new_like)
            db.session.commit()
            action = 'liked'

        # Get updated like data
        like_count = Like.query.filter_by(article_id=article_id).count()
        user_has_liked = (action == 'liked')

        # Get liked_by_users for Instagram-style display
        likes = Like.query.filter_by(article_id=article_id)\
            .order_by(Like.created_at)\
            .limit(5)\
            .all()
        liked_by_users = [
            {'id': like.user_id, 'username': like.user.username}
            for like in likes
        ]

        return jsonify({
            'success': True,
            'action': action,
            'like_count': like_count,
            'user_has_liked': user_has_liked,
            'liked_by_users': liked_by_users
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@interactions_bp.route('/articles/<int:article_id>/likes', methods=['GET'])
@login_required
def get_likes(article_id):
    """Get all likes for an article"""
    article = Article.query.get_or_404(article_id)
    user_id = session['user_id']

    likes = Like.query.filter_by(article_id=article_id)\
        .order_by(Like.created_at)\
        .all()

    liked_by_users = [
        {'id': like.user_id, 'username': like.user.username}
        for like in likes
    ]

    return jsonify({
        'success': True,
        'like_count': len(likes),
        'user_has_liked': any(like.user_id == user_id for like in likes),
        'liked_by_users': liked_by_users
    })


# ==================== COMMENT ENDPOINTS ====================

@interactions_bp.route('/articles/<int:article_id>/comments', methods=['GET'])
@login_required
def get_comments(article_id):
    """Get all comments for an article"""
    article = Article.query.get_or_404(article_id)
    user_id = session['user_id']
    user = User.query.get(user_id)

    comments = Comment.query.filter_by(
        article_id=article_id,
        is_active=True
    ).order_by(Comment.created_at.desc()).all()

    comments_data = [
        comment.to_dict(current_user_id=user_id)
        for comment in comments
    ]

    return jsonify({
        'success': True,
        'comments': comments_data,
        'is_admin': user.is_admin if user else False
    })


@interactions_bp.route('/articles/<int:article_id>/comments', methods=['POST'])
@login_required
def add_comment(article_id):
    """Add a comment to an article"""
    article = Article.query.get_or_404(article_id)
    user_id = session['user_id']

    data = request.get_json()
    content = data.get('content', '').strip()

    # Validation
    if not content:
        return jsonify({'success': False, 'error': 'Comment cannot be empty'}), 400

    if len(content) > 1000:
        return jsonify({'success': False, 'error': 'Comment too long (max 1000 characters)'}), 400

    try:
        comment = Comment(
            user_id=user_id,
            article_id=article_id,
            content=content
        )
        db.session.add(comment)
        db.session.commit()

        return jsonify({
            'success': True,
            'comment': comment.to_dict(current_user_id=user_id)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@interactions_bp.route('/comments/<int:comment_id>', methods=['PUT'])
@login_required
def edit_comment(comment_id):
    """Edit a comment (owner only)"""
    comment = Comment.query.get_or_404(comment_id)
    user_id = session['user_id']

    # Authorization: Only comment owner can edit
    if comment.user_id != user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data = request.get_json()
    content = data.get('content', '').strip()

    # Validation
    if not content:
        return jsonify({'success': False, 'error': 'Comment cannot be empty'}), 400

    if len(content) > 1000:
        return jsonify({'success': False, 'error': 'Comment too long (max 1000 characters)'}), 400

    try:
        comment.content = content
        comment.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'comment': comment.to_dict(current_user_id=user_id)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@interactions_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    """Delete a comment (owner or admin)"""
    comment = Comment.query.get_or_404(comment_id)
    user_id = session['user_id']
    user = User.query.get(user_id)

    # Authorization: Comment owner or admin
    if comment.user_id != user_id and not user.is_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    try:
        # Soft delete
        comment.is_active = False
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Comment deleted successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@interactions_bp.route('/comments/<int:comment_id>/report', methods=['POST'])
@login_required
def report_comment(comment_id):
    """Report a comment for moderation"""
    comment = Comment.query.get_or_404(comment_id)
    user_id = session['user_id']

    data = request.get_json()
    reason = data.get('reason', '').strip()

    # Validation
    if not reason:
        return jsonify({'success': False, 'error': 'Please provide a reason'}), 400

    if len(reason) > 500:
        return jsonify({'success': False, 'error': 'Reason too long (max 500 characters)'}), 400

    # Check if already reported by this user
    existing_report = ReportedComment.query.filter_by(
        comment_id=comment_id,
        reported_by_id=user_id
    ).first()

    if existing_report:
        return jsonify({'success': False, 'error': 'You have already reported this comment'}), 400

    try:
        report = ReportedComment(
            comment_id=comment_id,
            reported_by_id=user_id,
            reason=reason
        )
        db.session.add(report)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Comment reported successfully. Admins will review it.'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== HAPPINESS RATING ENDPOINTS ====================

@interactions_bp.route('/articles/<int:article_id>/happiness', methods=['POST'])
@login_required
def rate_happiness(article_id):
    """Submit or update happiness rating for an article"""
    user_id = session['user_id']
    article = Article.query.get_or_404(article_id)

    try:
        data = request.get_json()
        rating = data.get('rating')

        # Validate rating (1-100)
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 100:
            return jsonify({'success': False, 'error': 'Rating must be between 1 and 100'}), 400

        # Check if user already rated this article
        existing_rating = HappinessRating.query.filter_by(
            user_id=user_id,
            article_id=article_id
        ).first()

        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating
            existing_rating.updated_at = datetime.utcnow()
        else:
            # Create new rating
            new_rating = HappinessRating(
                user_id=user_id,
                article_id=article_id,
                rating=rating
            )
            db.session.add(new_rating)

        db.session.commit()

        # Calculate new average
        all_ratings = HappinessRating.query.filter_by(article_id=article_id).all()
        rating_count = len(all_ratings)
        average_happiness = round(sum(r.rating for r in all_ratings) / rating_count) if rating_count > 0 else 0

        return jsonify({
            'success': True,
            'happiness_average': average_happiness,
            'happiness_count': rating_count,
            'user_happiness_rating': rating
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@interactions_bp.route('/articles/<int:article_id>/happiness', methods=['GET'])
@login_required
def get_happiness(article_id):
    """Get happiness rating data for an article"""
    article = Article.query.get_or_404(article_id)
    user_id = session['user_id']

    ratings = HappinessRating.query.filter_by(article_id=article_id).all()
    rating_count = len(ratings)
    average_happiness = round(sum(r.rating for r in ratings) / rating_count) if rating_count > 0 else 0

    user_rating = None
    user_rating_obj = HappinessRating.query.filter_by(
        user_id=user_id,
        article_id=article_id
    ).first()
    if user_rating_obj:
        user_rating = user_rating_obj.rating

    return jsonify({
        'success': True,
        'happiness_average': average_happiness,
        'happiness_count': rating_count,
        'user_happiness_rating': user_rating
    })


# ==================== READ ARTICLE ENDPOINTS ====================

@interactions_bp.route('/articles/<int:article_id>/mark-read', methods=['POST'])
@login_required
def mark_article_read(article_id):
    """Mark an article as read by the current user"""
    user_id = session['user_id']
    article = Article.query.get_or_404(article_id)

    try:
        # Check if already marked as read
        existing_read = ReadArticle.query.filter_by(
            user_id=user_id,
            article_id=article_id
        ).first()

        if not existing_read:
            # Mark as read
            read_record = ReadArticle(
                user_id=user_id,
                article_id=article_id
            )
            db.session.add(read_record)
            db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Article marked as read'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
