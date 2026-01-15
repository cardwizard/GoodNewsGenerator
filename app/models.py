from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """Hash and store password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Article(db.Model):
    """Article model for caching news articles"""
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    published_at = db.Column(db.DateTime)
    source_name = db.Column(db.String(100))
    source_url = db.Column(db.String(500))
    cached_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    source_type = db.Column(db.String(20), default='auto')  # 'auto' or 'manual'
    added_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    # Article review fields
    status = db.Column(db.String(20), default='approved')  # 'pending', 'approved', 'rejected'
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self, user_id=None):
        """Convert article to dictionary for JSON serialization with social engagement data"""
        like_count = len(self.likes)
        user_has_liked = False
        liked_by_users = []

        if user_id:
            user_has_liked = any(like.user_id == user_id for like in self.likes)
            # Get list of users who liked (for Instagram-style display)
            liked_by_users = [
                {'id': like.user_id, 'username': like.user.username}
                for like in sorted(self.likes, key=lambda x: x.created_at)[:5]  # First 5 users
            ]

        # Get comment count (only active comments)
        comment_count = len([c for c in self.comments if c.is_active])

        # Calculate happiness rating data
        ratings = self.happiness_ratings
        rating_count = len(ratings)
        average_happiness = 0
        user_rating = None

        if rating_count > 0:
            average_happiness = round(sum(r.rating for r in ratings) / rating_count)

        if user_id:
            user_rating_obj = next((r for r in ratings if r.user_id == user_id), None)
            user_rating = user_rating_obj.rating if user_rating_obj else None

        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'content': self.content,
            'image_url': self.image_url,
            'published_at': self.published_at.strftime('%B %d, %Y') if self.published_at else '',
            'source_name': self.source_name,
            'source_url': self.source_url,
            # Social engagement data
            'like_count': like_count,
            'user_has_liked': user_has_liked,
            'liked_by_users': liked_by_users,
            'comment_count': comment_count,
            # Happiness rating data
            'happiness_average': average_happiness,
            'happiness_count': rating_count,
            'user_happiness_rating': user_rating,
        }

    def __repr__(self):
        return f'<Article {self.title[:50]}>'


class APIRequest(db.Model):
    """Track daily API requests for rate limiting"""
    __tablename__ = 'api_requests'

    id = db.Column(db.Integer, primary_key=True)
    request_date = db.Column(db.Date, nullable=False, unique=True)
    request_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<APIRequest {self.request_date}: {self.request_count}>'


class Like(db.Model):
    """User likes on articles"""
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='likes')
    article = db.relationship('Article', backref='likes')

    # Unique constraint: one like per user per article
    __table_args__ = (
        db.UniqueConstraint('user_id', 'article_id', name='unique_user_article_like'),
        db.Index('idx_article_likes', 'article_id'),  # Performance index
    )

    def __repr__(self):
        return f'<Like user={self.user_id} article={self.article_id}>'


class Comment(db.Model):
    """User comments on articles"""
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)  # For soft delete

    # Relationships
    user = db.relationship('User', backref='comments')
    article = db.relationship('Article', backref='comments')

    # Indexes for performance
    __table_args__ = (
        db.Index('idx_article_comments', 'article_id', 'is_active'),
        db.Index('idx_user_comments', 'user_id'),
    )

    def to_dict(self, current_user_id=None):
        """Convert comment to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username,
            'content': self.content,
            'created_at': self.created_at.strftime('%B %d, %Y at %I:%M %p'),
            'updated_at': self.updated_at.strftime('%B %d, %Y at %I:%M %p') if self.updated_at != self.created_at else None,
            'is_owner': current_user_id == self.user_id if current_user_id else False
        }

    def __repr__(self):
        return f'<Comment {self.id} by {self.user_id}>'


class ReportedComment(db.Model):
    """Track reported comments for moderation"""
    __tablename__ = 'reported_comments'

    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False)
    reported_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    comment = db.relationship('Comment', backref='reports')
    reported_by = db.relationship('User', foreign_keys=[reported_by_id], backref='reported_comments')
    resolved_by = db.relationship('User', foreign_keys=[resolved_by_id])

    # Prevent duplicate reports
    __table_args__ = (
        db.UniqueConstraint('comment_id', 'reported_by_id', name='unique_comment_report'),
        db.Index('idx_unresolved_reports', 'is_resolved'),
    )

    def __repr__(self):
        return f'<ReportedComment {self.comment_id}>'


class FetchHistory(db.Model):
    """Track manual article fetch requests"""
    __tablename__ = 'fetch_history'

    id = db.Column(db.Integer, primary_key=True)
    fetched_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow)
    articles_fetched = db.Column(db.Integer, default=0)
    articles_approved = db.Column(db.Integer, default=0)
    articles_rejected = db.Column(db.Integer, default=0)

    # Relationship
    fetched_by = db.relationship('User', backref='fetch_history')

    def __repr__(self):
        return f'<FetchHistory {self.id} by {self.fetched_by_id}>'


class HappinessRating(db.Model):
    """Model for storing happiness ratings on articles"""
    __tablename__ = 'happiness_ratings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-100 percentage
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='happiness_ratings')
    article = db.relationship('Article', backref='happiness_ratings')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'article_id', name='unique_user_article_rating'),
        db.Index('idx_article_ratings', 'article_id'),
    )

    def __repr__(self):
        return f'<HappinessRating {self.user_id} rated {self.article_id} as {self.rating}%>'


class ReadArticle(db.Model):
    """Track which articles a user has read"""
    __tablename__ = 'read_articles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    read_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='read_articles')
    article = db.relationship('Article', backref='read_by')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'article_id', name='unique_user_article_read'),
        db.Index('idx_user_reads', 'user_id'),
        db.Index('idx_article_reads', 'article_id'),
    )

    def __repr__(self):
        return f'<ReadArticle user={self.user_id} article={self.article_id}>'


class LoginAttempt(db.Model):
    """Track failed login attempts for account security"""
    __tablename__ = 'login_attempts'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 support
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)
    successful = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.Index('idx_username_attempts', 'username', 'attempted_at'),
    )

    def __repr__(self):
        return f'<LoginAttempt {self.username} at {self.attempted_at}>'

