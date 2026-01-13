// Global variables
let currentPage = 2; // Start from page 2 since page 1 is already loaded
let isLoading = false;

/**
 * Load more articles via AJAX
 */
function loadMore() {
    if (isLoading) return;

    isLoading = true;
    const button = document.getElementById('load-more-btn');
    if (button) {
        button.disabled = true;
        button.textContent = 'Loading...';
    }

    fetch(`/api/feed?page=${currentPage}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(articles => {
            if (articles.length > 0) {
                appendArticles(articles);
                currentPage++;
                if (button) {
                    button.disabled = false;
                    button.textContent = 'Load More Good News';
                }
            } else {
                if (button) {
                    button.disabled = true;
                    button.textContent = 'No More Articles';
                }
            }
            isLoading = false;
        })
        .catch(error => {
            console.error('Error loading articles:', error);
            if (button) {
                button.disabled = false;
                button.textContent = 'Try Again';
            }
            isLoading = false;
            alert('Failed to load articles. Please try again.');
        });
}

/**
 * Append articles to the feed
 * @param {Array} articles - Array of article objects
 */
function appendArticles(articles) {
    const container = document.getElementById('articles-container');
    if (!container) return;

    articles.forEach(article => {
        const articleCard = createArticleCard(article);
        container.appendChild(articleCard);
    });

    // Smooth scroll to first new article
    const cards = container.querySelectorAll('.news-card');
    if (cards.length > 0) {
        const lastCard = cards[cards.length - articles.length];
        if (lastCard) {
            lastCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
}

/**
 * Create an article card element
 * @param {Object} article - Article object
 * @returns {HTMLElement} Article card element
 */
function createArticleCard(article) {
    const card = document.createElement('article');
    card.className = 'news-card';

    // Create image section
    const imageDiv = document.createElement('div');
    imageDiv.className = 'card-image';

    if (article.image_url) {
        const img = document.createElement('img');
        img.src = article.image_url;
        img.alt = article.title;
        img.onerror = function() {
            this.parentElement.innerHTML = '<div class="placeholder-image"><span>📰</span></div>';
        };
        imageDiv.appendChild(img);
    } else {
        imageDiv.innerHTML = '<div class="placeholder-image"><span>📰</span></div>';
    }

    // Create content section
    const contentDiv = document.createElement('div');
    contentDiv.className = 'card-content';

    const title = document.createElement('h3');
    title.textContent = article.title;

    const meta = document.createElement('p');
    meta.className = 'meta';
    meta.innerHTML = `
        <span class="source">${article.source_name}</span>
        ${article.published_at ? `<span class="separator">•</span><span class="date">${article.published_at}</span>` : ''}
    `;

    const description = document.createElement('p');
    description.className = 'description';
    description.textContent = article.description || '';

    const readMore = document.createElement('a');
    readMore.href = article.source_url;
    readMore.target = '_blank';
    readMore.className = 'read-more';
    readMore.textContent = 'Read Full Article →';

    contentDiv.appendChild(title);
    contentDiv.appendChild(meta);
    if (article.description) {
        contentDiv.appendChild(description);
    }
    contentDiv.appendChild(readMore);

    card.appendChild(imageDiv);
    card.appendChild(contentDiv);

    return card;
}

/**
 * Auto-dismiss flash messages after 5 seconds
 */
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transition = 'opacity 0.5s';
            setTimeout(() => message.remove(), 500);
        }, 5000);
    });
});
