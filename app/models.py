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

    def to_dict(self):
        """Convert article to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'content': self.content,
            'image_url': self.image_url,
            'published_at': self.published_at.strftime('%B %d, %Y') if self.published_at else '',
            'source_name': self.source_name,
            'source_url': self.source_url
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
