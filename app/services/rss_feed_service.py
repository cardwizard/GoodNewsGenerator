import feedparser
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# RSS Feeds to subscribe to
RSS_FEEDS = [
    {
        'url': 'https://www.positive.news/feed/',
        'source_name': 'Positive News'
    },
    {
        'url': 'https://reasonstobecheerful.world/feed/',
        'source_name': 'Reasons to be Cheerful'
    },
    {
        'url': 'https://news.janegoodall.org/feed/',
        'source_name': 'Jane Goodall News'
    }
]


def fetch_articles_from_rss(max_articles=50) -> Optional[List[Dict]]:
    """
    Fetch articles from configured RSS feeds

    Args:
        max_articles: Maximum number of articles to return across all feeds

    Returns:
        list: List of article dictionaries or None on error
    """
    all_articles = []

    for feed_config in RSS_FEEDS:
        feed_url = feed_config['url']
        source_name = feed_config['source_name']

        try:
            logger.info(f"Fetching RSS feed from {source_name}: {feed_url}")
            feed = feedparser.parse(feed_url)

            if feed.bozo and feed.bozo_exception:
                logger.warning(f"Feed parsing warning for {source_name}: {feed.bozo_exception}")

            # Process each entry in the feed
            for entry in feed.entries:
                article = parse_rss_entry(entry, source_name)
                if article:
                    all_articles.append(article)

            logger.info(f"Fetched {len(feed.entries)} articles from {source_name}")

        except Exception as e:
            logger.error(f"Error fetching RSS feed {source_name}: {str(e)}")
            continue

    # Sort by published date (most recent first)
    all_articles.sort(key=lambda x: x.get('published_date') or datetime.min, reverse=True)

    # Return requested number of articles
    result = all_articles[:max_articles]
    logger.info(f"Successfully fetched {len(result)} total articles from RSS feeds")

    return result if result else None


def parse_rss_entry(entry, source_name: str) -> Optional[Dict]:
    """
    Parse an RSS feed entry into article dictionary

    Args:
        entry: feedparser entry object
        source_name: Name of the source feed

    Returns:
        dict: Parsed article data or None if invalid
    """
    try:
        # Extract title
        title = entry.get('title', '').strip()
        if not title:
            return None

        # Extract description/summary
        description = entry.get('summary', '') or entry.get('description', '')
        # Strip HTML tags from description
        if description:
            import re
            description = re.sub('<[^<]+?>', '', description).strip()

        # Extract content
        content = ''
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].value if isinstance(entry.content, list) else entry.content
        elif description:
            content = description

        # Strip HTML from content
        if content:
            import re
            content = re.sub('<[^<]+?>', '', content).strip()

        # Extract image URL
        image_url = None

        # Try media:content (common in RSS feeds)
        if hasattr(entry, 'media_content') and entry.media_content:
            image_url = entry.media_content[0].get('url')

        # Try media:thumbnail
        if not image_url and hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            image_url = entry.media_thumbnail[0].get('url')

        # Try enclosure
        if not image_url and hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if enclosure.get('type', '').startswith('image/'):
                    image_url = enclosure.get('href')
                    break

        # Try links with rel="enclosure"
        if not image_url and hasattr(entry, 'links'):
            for link in entry.links:
                if link.get('rel') == 'enclosure' and link.get('type', '').startswith('image/'):
                    image_url = link.get('href')
                    break

        # Extract published date
        published_date = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                published_date = datetime(*entry.published_parsed[:6])
            except:
                pass

        if not published_date and hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            try:
                published_date = datetime(*entry.updated_parsed[:6])
            except:
                pass

        # If no date found, use current time
        if not published_date:
            published_date = datetime.utcnow()

        # Extract article URL
        url = entry.get('link', '')
        if not url:
            return None

        # Build article dictionary in NewsAPI format for compatibility
        article = {
            'title': title,
            'description': description[:500] if description else None,  # Limit description length
            'content': content[:1000] if content else description,  # Limit content length
            'urlToImage': image_url,
            'publishedAt': published_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'published_date': published_date,  # For sorting
            'source': {
                'name': source_name
            },
            'url': url
        }

        return article

    except Exception as e:
        logger.error(f"Error parsing RSS entry: {str(e)}")
        return None


def test_rss_feeds():
    """
    Test function to verify RSS feeds are accessible

    Returns:
        dict: Status of each feed
    """
    results = {}

    for feed_config in RSS_FEEDS:
        feed_url = feed_config['url']
        source_name = feed_config['source_name']

        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo and feed.bozo_exception:
                results[source_name] = {
                    'status': 'warning',
                    'message': str(feed.bozo_exception),
                    'entries': len(feed.entries)
                }
            else:
                results[source_name] = {
                    'status': 'success',
                    'entries': len(feed.entries),
                    'title': feed.feed.get('title', 'Unknown')
                }

        except Exception as e:
            results[source_name] = {
                'status': 'error',
                'message': str(e)
            }

    return results
