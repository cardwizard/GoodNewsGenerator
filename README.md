# Good News Aggregator

A Flask-based web application that displays 5 good news articles at a time in an Instagram-like layout. Users can log in and refresh to see more articles from a cached pool of positive news from around the world.

## Features

- User authentication (registration and login)
- Instagram-style news feed layout
- 5 articles displayed at a time
- AJAX-powered "Load More" functionality
- Daily automatic news cache refresh
- NewsAPI.org integration for positive news
- SQLite database for users and article caching
- Responsive design for mobile and desktop

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- NewsAPI.org API key (free tier)

## Installation

### 1. Clone or navigate to the project directory

```bash
cd "C:\dev\practiceProjects\Good News Aggregator"
```

### 2. Create a virtual environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Unix/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get NewsAPI.org API Key

1. Go to [https://newsapi.org/](https://newsapi.org/)
2. Sign up for a free account
3. Copy your API key from the dashboard

### 5. Configure environment variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your NewsAPI key:

```bash
SECRET_KEY=your-random-secret-key-here
NEWS_API_KEY=your-newsapi-org-api-key-here
DATABASE_URL=sqlite:///good_news.db
FLASK_ENV=development
```

**Important:** Generate a secure random secret key for production use:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Running the Application

### 1. Start the Flask development server

```bash
python run.py
```

The application will be available at: [http://localhost:5000](http://localhost:5000)

### 2. First-time setup

1. Navigate to [http://localhost:5000](http://localhost:5000)
2. Click "Register here" to create an account
3. Fill in username (3-20 characters) and password (8+ characters)
4. After registration, you'll be automatically logged in

### 3. Initial cache population

The first time you access the feed, the cache will be empty. To populate it:

Open a Python shell in the project directory:

```bash
python
```

Then run:

```python
from app import create_app
from app.services.cache_service import update_cache

app = create_app()
with app.app_context():
    update_cache()
```

This will fetch 50 articles from NewsAPI and cache them.

## Usage

### Viewing News

- After logging in, you'll see 5 good news articles
- Each article displays: image, title, source, date, description, and link
- Click "Read Full Article" to open the full story in a new tab

### Loading More Articles

- Click the "Load More Good News" button at the bottom of the feed
- This fetches the next 5 articles from the cache (no API call)
- Continue clicking to see more cached articles

### Automatic Cache Refresh

- The application automatically refreshes the cache daily at 6 AM
- This runs in the background while the server is running
- Old articles (7+ days) are automatically archived

## Project Structure

```
Good News Aggregator/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration
│   ├── models.py                # Database models
│   ├── auth.py                  # Authentication routes
│   ├── news.py                  # News feed routes
│   ├── services/
│   │   ├── news_api_service.py  # NewsAPI integration
│   │   └── cache_service.py     # Article caching
│   ├── static/
│   │   ├── css/style.css        # Styling
│   │   └── js/main.js           # JavaScript
│   └── templates/
│       ├── base.html            # Base template
│       ├── login.html           # Login page
│       ├── register.html        # Registration page
│       └── news_feed.html       # News feed
├── .env                         # Environment variables (not committed)
├── .env.example                 # Example environment variables
├── .gitignore                   # Git ignore rules
├── requirements.txt             # Python dependencies
├── run.py                       # Application entry point
└── README.md                    # This file
```

## Database

The application uses SQLite with three tables:

- **users**: User accounts with hashed passwords
- **articles**: Cached news articles
- **api_requests**: API usage tracking for rate limiting

Database file location: `instance/good_news.db`

## Rate Limiting

- NewsAPI.org free tier: 100 requests/day
- The app limits itself to 90 requests/day (buffer)
- If the limit is reached, the app shows cached articles only
- Rate limit resets daily at midnight

## Troubleshooting

### No articles showing

**Solution 1:** Manually populate the cache (see "Initial cache population" above)

**Solution 2:** Check your API key in the `.env` file

**Solution 3:** Check the console for error messages

### "Invalid API key" error

- Verify your NewsAPI key in `.env` is correct
- Ensure there are no extra spaces in the `.env` file
- Try generating a new key from NewsAPI.org

### Application won't start

- Ensure virtual environment is activated
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version: `python --version` (should be 3.8+)

### Images not loading

- Some articles don't have images - this is normal
- The app shows a placeholder (📰 icon) for articles without images
- Check browser console for image loading errors

## Development

### Running in development mode

```bash
# With debug mode enabled
python run.py
```

### Manually triggering cache refresh

```python
from app import create_app
from app.services.cache_service import update_cache

app = create_app()
with app.app_context():
    result = update_cache()
    print(f"Cache update: {'Success' if result else 'Failed'}")
```

### Checking API usage

```python
from app import create_app
from app.services.cache_service import get_api_request_count

app = create_app()
with app.app_context():
    count = get_api_request_count()
    print(f"API requests today: {count}/90")
```

## Technologies Used

- **Backend:** Flask 3.0
- **Database:** SQLite with SQLAlchemy ORM
- **News Source:** NewsAPI.org
- **Authentication:** Session-based with password hashing
- **Scheduler:** APScheduler for background jobs
- **Frontend:** HTML, CSS, Vanilla JavaScript
- **Styling:** Custom CSS (Instagram-inspired)

## API Keywords

The app searches for articles with these positive keywords:
- innovation
- breakthrough
- success
- achievement
- inspiring

## Security Features

- Password hashing with werkzeug.security
- Session-based authentication
- CSRF protection via Flask sessions
- Input validation and sanitization
- Secure cookie configuration

## Future Enhancements

- User preferences for news topics
- Bookmark/favorite articles
- Share articles on social media
- Dark mode toggle
- Admin dashboard
- PostgreSQL for production
- Docker containerization

## License

This project is open source and available for personal and educational use.

## Credits

- News data powered by [NewsAPI.org](https://newsapi.org/)
- Built with [Flask](https://flask.palletsprojects.com/)

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review the console logs for error messages
3. Verify your NewsAPI key is valid
4. Ensure all dependencies are installed

---

**Enjoy your daily dose of good news!** 🌟
