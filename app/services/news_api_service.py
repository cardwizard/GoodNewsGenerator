import requests
import logging
from datetime import datetime
from app.config import Config

logger = logging.getLogger(__name__)


def fetch_good_news():
    """
    Fetch positive news articles from NewsAPI.org

    Returns:
        list: List of article dictionaries or None on error
    """
    if not Config.NEWS_API_KEY:
        logger.error("NEWS_API_KEY not configured")
        return None

    url = f"{Config.NEWS_API_BASE_URL}/everything"

    # Simpler positive keywords for API query (NewsAPI has query complexity limits)
    positive_query = (
        'rescued OR hero OR miracle OR heartwarming OR donate OR charity OR '
        'volunteer OR cure OR breakthrough OR discovery OR celebration OR '
        'award OR inspiring OR kindness OR reunited OR adopted OR hope'
    )

    params = {
        'q': positive_query,
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': 100,  # Fetch more to filter better
        'apiKey': Config.NEWS_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get('status') != 'ok':
            logger.error(f"API returned error: {data.get('message')}")
            return None

        articles = data.get('articles', [])

        # Parse and filter articles
        parsed_articles = []
        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')

            # Skip articles with negative keywords in title or description
            if not is_positive_article(title, description):
                continue

            parsed_article = {
                'title': title,
                'description': description,
                'content': article.get('content', ''),
                'image_url': article.get('urlToImage'),
                'published_at': parse_date(article.get('publishedAt')),
                'source_name': article.get('source', {}).get('name', ''),
                'source_url': article.get('url', '')
            }

            # Only include articles with at least a title
            if parsed_article['title']:
                parsed_articles.append(parsed_article)

        # Return top 50 most recent positive articles
        logger.info(f"Successfully fetched and filtered {len(parsed_articles)} positive articles")
        return parsed_articles[:50]

    except requests.exceptions.Timeout:
        logger.error("NewsAPI request timed out")
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            logger.error("Rate limit exceeded")
        elif e.response.status_code == 401:
            logger.error("Invalid API key")
        else:
            logger.error(f"HTTP error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching news: {str(e)}")
        return None


def is_positive_article(title, description):
    """
    Check if article title and description are positive/uplifting

    Args:
        title: Article title
        description: Article description

    Returns:
        bool: True if article seems positive, False otherwise
    """
    # Negative keywords that should exclude an article
    negative_keywords = [
        '死', 'death', 'die', 'died', 'kill', 'murder', 'shoot', 'attack',
        'war', 'conflict', 'terror', 'bomb', 'explode', 'crash', 'accident',
        'fire', 'disaster', 'threat', 'warning', 'crisis', 'scandal', 'abuse',
        'violence', 'injure', 'wound', 'arrest', 'guilty', 'sentence', 'jail',
        'prison', 'convicted', 'fraud', 'scam', 'stolen', 'theft', 'robbery',
        'missing', 'lost', 'disappear', 'tragic', 'devastat', 'destroy',
        'lawsuit', 'sue', 'bankrupt', 'collapse', 'fail', 'defeat', 'loss',
        'cancer', 'disease outbreak', 'pandemic', 'epidemic', 'victim'
    ]

    # Positive keywords that increase confidence
    positive_keywords = [
        'rescue', 'save', 'hero', 'miracle', 'heartwarming', 'inspire',
        'help', 'donate', 'charity', 'volunteer', 'recover', 'cure',
        'breakthrough', 'discover', 'success', 'achieve', 'win', 'celebrate',
        'award', 'honor', 'graduate', 'adopted', 'reunite', 'wedding',
        'birth', 'newborn', 'joy', 'happy', 'smile', 'kind', 'generous',
        'hope', 'peace', 'unity', 'together', 'community', 'friend',
        'love', 'compassion', 'beauty', 'amazing', 'wonderful', 'fantastic'
    ]

    text = f"{title} {description}".lower()

    # Check for negative keywords
    for keyword in negative_keywords:
        if keyword.lower() in text:
            return False

    # Check for positive keywords (at least one should be present)
    has_positive = any(keyword.lower() in text for keyword in positive_keywords)

    return has_positive


def parse_date(date_string):
    """
    Parse ISO 8601 date string to datetime object

    Args:
        date_string: ISO 8601 formatted date string

    Returns:
        datetime: Parsed datetime object or None
    """
    if not date_string:
        return None

    try:
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except Exception as e:
        logger.warning(f"Failed to parse date {date_string}: {e}")
        return None
