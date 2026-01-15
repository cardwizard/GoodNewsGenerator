// Global variables
let currentPage = 2; // Start from page 2 since page 1 is already loaded
let isLoading = false;
let currentReportCommentId = null; // Track which comment is being reported

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
    card.setAttribute('data-article-id', article.id);

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

    // Action Bar (Like, Comment, Share)
    const actionBar = document.createElement('div');
    actionBar.className = 'action-bar';
    actionBar.innerHTML = `
        <button class="action-btn like-btn"
                data-article-id="${article.id}"
                data-liked="${article.user_has_liked || false}"
                onclick="toggleLike(${article.id})"
                aria-label="Like">
            <svg class="icon" viewBox="0 0 24 24">
                <path class="like-outline" ${article.user_has_liked ? 'style="display: none;"' : ''} d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3zm-4.4 15.55l-.1.1-.1-.1C7.14 14.24 4 11.39 4 8.5 4 6.5 5.5 5 7.5 5c1.54 0 3.04.99 3.57 2.36h1.87C13.46 5.99 14.96 5 16.5 5c2 0 3.5 1.5 3.5 3.5 0 2.89-3.14 5.74-7.9 10.05z"/>
                <path class="like-filled" ${article.user_has_liked ? '' : 'style="display: none;"'} d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
        </button>
        <button class="action-btn comment-btn"
                onclick="toggleComments(${article.id})"
                aria-label="Comment">
            <svg class="icon" viewBox="0 0 24 24">
                <path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 9h12v2H6V9zm8 5H6v-2h8v2zm4-6H6V6h12v2z"/>
            </svg>
        </button>
        <button class="action-btn share-btn"
                onclick="shareArticle(${article.id})"
                aria-label="Share">
            <svg class="icon" viewBox="0 0 24 24">
                <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92 1.61 0 2.92-1.31 2.92-2.92s-1.31-2.92-2.92-2.92z"/>
            </svg>
        </button>
    `;

    // Likes Display (Instagram-style)
    const likesDisplay = document.createElement('div');
    likesDisplay.className = 'likes-display';
    likesDisplay.setAttribute('data-article-id', article.id);
    likesDisplay.innerHTML = formatLikesDisplay(article.like_count || 0, article.liked_by_users || []);

    // Article Title and Meta
    const title = document.createElement('h3');
    title.textContent = article.title;

    const meta = document.createElement('p');
    meta.className = 'meta';
    meta.innerHTML = `
        <span class="source">${escapeHtml(article.source_name)}</span>
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

    // Happiness Meter
    const happinessMeter = document.createElement('div');
    happinessMeter.className = 'happiness-meter';
    happinessMeter.setAttribute('data-article-id', article.id);

    const happinessAvg = article.happiness_average || 0;
    const happinessCount = article.happiness_count || 0;
    const userRating = article.user_happiness_rating;

    let countText = 'Be the first to rate this post!';
    if (happinessCount === 1) {
        countText = '1 person rated this';
    } else if (happinessCount > 1) {
        countText = `${happinessCount} people rated this`;
    }

    let emoji = '😊';
    if (happinessAvg >= 80) emoji = '🤩';
    else if (happinessAvg >= 60) emoji = '😃';
    else if (happinessAvg >= 40) emoji = '😊';
    else if (happinessAvg >= 20) emoji = '🙂';
    else if (happinessAvg > 0) emoji = '😐';

    happinessMeter.innerHTML = `
        <div class="happiness-header">
            <span class="happiness-label">Happiness Meter</span>
            <span class="happiness-percentage">${happinessAvg}%</span>
        </div>
        <div class="happiness-bar-container">
            <div class="happiness-bar" style="width: ${happinessAvg}%;">
                <div class="happiness-shine"></div>
            </div>
            <div class="happiness-emoji">${emoji}</div>
        </div>
        <div class="happiness-info">
            <span class="happiness-count">${countText}</span>
        </div>
        <div class="happiness-slider-container">
            <input type="range" class="happiness-slider"
                   min="0" max="100" value="${userRating || 0}" step="1"
                   data-article-id="${article.id}"
                   oninput="updateHappinessPreview(${article.id}, this.value)"
                   onchange="rateHappiness(${article.id}, this.value)">
            <div class="happiness-slider-labels">
                <span>😐 Meh</span>
                <span>🙂 Okay</span>
                <span>😊 Good</span>
                <span>😃 Great</span>
                <span>🤩 Amazing!</span>
            </div>
        </div>
    `;

    // Comments Section
    const commentsSection = document.createElement('div');
    commentsSection.className = 'comments-section';
    commentsSection.setAttribute('data-article-id', article.id);
    commentsSection.style.display = 'none';
    commentsSection.innerHTML = `
        <div class="comments-header">
            <h4>Comments <span class="comment-count">${article.comment_count || 0}</span></h4>
        </div>
        <div class="comment-input-container">
            <textarea class="comment-input" placeholder="Add a comment..." maxlength="1000" rows="2"></textarea>
            <div class="comment-input-footer">
                <span class="char-count">0/1000</span>
                <button class="btn-post-comment" onclick="postComment(${article.id})">Post</button>
            </div>
        </div>
        <div class="comments-list">
            <!-- Comments will be loaded dynamically -->
        </div>
    `;

    // Assemble card
    contentDiv.appendChild(actionBar);
    contentDiv.appendChild(likesDisplay);
    contentDiv.appendChild(title);
    contentDiv.appendChild(meta);
    if (article.description) {
        contentDiv.appendChild(description);
    }
    contentDiv.appendChild(readMore);
    contentDiv.appendChild(happinessMeter);
    contentDiv.appendChild(commentsSection);

    card.appendChild(imageDiv);
    card.appendChild(contentDiv);

    // Setup character counter for this card's comment input
    setTimeout(() => setupCommentInputs(), 0);

    return card;
}

// ==================== SOCIAL FEATURES ====================

/**
 * Escape HTML to prevent XSS attacks
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format likes display Instagram-style
 * @param {number} likeCount - Total number of likes
 * @param {Array} likedByUsers - Array of user objects who liked
 * @returns {string} Formatted HTML string
 */
function formatLikesDisplay(likeCount, likedByUsers) {
    if (likeCount === 0) {
        return '<span class="like-count">Be the first to like this</span>';
    }

    if (likeCount === 1) {
        return `<span class="like-count"><strong>${escapeHtml(likedByUsers[0].username)}</strong> likes this</span>`;
    }

    if (likeCount === 2) {
        return `<span class="like-count"><strong>${escapeHtml(likedByUsers[0].username)}</strong> and <strong>${escapeHtml(likedByUsers[1].username)}</strong> like this</span>`;
    }

    // 3 or more likes
    const othersCount = likeCount - 1;
    return `<span class="like-count"><strong>${escapeHtml(likedByUsers[0].username)}</strong> and <strong>${othersCount} ${othersCount === 1 ? 'other' : 'others'}</strong></span>`;
}

/**
 * Toggle like on an article
 * @param {number} articleId - Article ID
 */
function toggleLike(articleId) {
    const likeBtn = document.querySelector(`.like-btn[data-article-id="${articleId}"]`);
    if (!likeBtn) return;

    // Optimistic UI update
    const isLiked = likeBtn.getAttribute('data-liked') === 'true';
    const outlinePath = likeBtn.querySelector('.like-outline');
    const filledPath = likeBtn.querySelector('.like-filled');

    if (isLiked) {
        outlinePath.style.display = '';
        filledPath.style.display = 'none';
        likeBtn.setAttribute('data-liked', 'false');
    } else {
        outlinePath.style.display = 'none';
        filledPath.style.display = '';
        likeBtn.setAttribute('data-liked', 'true');
    }

    // Send request to backend
    fetch(`/api/articles/${articleId}/like`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateLikesDisplay(articleId, data);
        } else {
            // Revert optimistic update on failure
            if (isLiked) {
                outlinePath.style.display = 'none';
                filledPath.style.display = '';
                likeBtn.setAttribute('data-liked', 'true');
            } else {
                outlinePath.style.display = '';
                filledPath.style.display = 'none';
                likeBtn.setAttribute('data-liked', 'false');
            }
            alert('Failed to update like. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error toggling like:', error);
        // Revert optimistic update on error
        if (isLiked) {
            outlinePath.style.display = 'none';
            filledPath.style.display = '';
            likeBtn.setAttribute('data-liked', 'true');
        } else {
            outlinePath.style.display = '';
            filledPath.style.display = 'none';
            likeBtn.setAttribute('data-liked', 'false');
        }
        alert('Network error. Please try again.');
    });
}

/**
 * Update likes display with fresh data
 * @param {number} articleId - Article ID
 * @param {Object} data - Like data from backend
 */
function updateLikesDisplay(articleId, data) {
    const likesDisplay = document.querySelector(`.likes-display[data-article-id="${articleId}"]`);
    if (likesDisplay) {
        likesDisplay.innerHTML = formatLikesDisplay(data.like_count, data.liked_by_users || []);
    }
}

/**
 * Toggle comments section visibility
 * @param {number} articleId - Article ID
 */
function toggleComments(articleId) {
    const commentsSection = document.querySelector(`.comments-section[data-article-id="${articleId}"]`);
    if (!commentsSection) return;

    const isVisible = commentsSection.style.display !== 'none';

    if (isVisible) {
        commentsSection.style.display = 'none';
    } else {
        commentsSection.style.display = 'block';
        // Load comments if not already loaded
        const commentsList = commentsSection.querySelector('.comments-list');
        if (commentsList && commentsList.children.length === 0) {
            loadComments(articleId);
        }
    }
}

/**
 * Load comments for an article
 * @param {number} articleId - Article ID
 */
function loadComments(articleId) {
    const commentsList = document.querySelector(`.comments-section[data-article-id="${articleId}"] .comments-list`);
    if (!commentsList) return;

    commentsList.innerHTML = '<p class="loading-comments">Loading comments...</p>';

    fetch(`/api/articles/${articleId}/comments`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                commentsList.innerHTML = '';

                if (data.comments.length === 0) {
                    commentsList.innerHTML = '<p class="no-comments">No comments yet. Be the first to comment!</p>';
                } else {
                    data.comments.forEach(comment => {
                        const commentElement = renderComment(comment, articleId);
                        commentsList.appendChild(commentElement);
                    });
                }

                // Update comment count
                const commentCount = document.querySelector(`.comments-section[data-article-id="${articleId}"] .comment-count`);
                if (commentCount) {
                    commentCount.textContent = data.comments.length;
                }
            } else {
                commentsList.innerHTML = '<p class="error-message">Failed to load comments.</p>';
            }
        })
        .catch(error => {
            console.error('Error loading comments:', error);
            commentsList.innerHTML = '<p class="error-message">Network error. Please try again.</p>';
        });
}

/**
 * Post a new comment
 * @param {number} articleId - Article ID
 */
function postComment(articleId) {
    const commentsSection = document.querySelector(`.comments-section[data-article-id="${articleId}"]`);
    if (!commentsSection) return;

    const textarea = commentsSection.querySelector('.comment-input');
    const content = textarea.value.trim();

    if (!content) {
        alert('Please enter a comment.');
        return;
    }

    if (content.length > 1000) {
        alert('Comment is too long. Maximum 1000 characters.');
        return;
    }

    // Disable button during submission
    const postBtn = commentsSection.querySelector('.btn-post-comment');
    postBtn.disabled = true;
    postBtn.textContent = 'Posting...';

    fetch(`/api/articles/${articleId}/comments`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: content })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear textarea
            textarea.value = '';
            const charCount = commentsSection.querySelector('.char-count');
            if (charCount) {
                charCount.textContent = '0/1000';
            }

            // Add comment to list
            const commentsList = commentsSection.querySelector('.comments-list');
            const noCommentsMsg = commentsList.querySelector('.no-comments');
            if (noCommentsMsg) {
                noCommentsMsg.remove();
            }

            const commentElement = renderComment(data.comment, articleId);
            commentsList.insertBefore(commentElement, commentsList.firstChild);

            // Update comment count
            const commentCount = commentsSection.querySelector('.comment-count');
            if (commentCount) {
                const currentCount = parseInt(commentCount.textContent) || 0;
                commentCount.textContent = currentCount + 1;
            }
        } else {
            alert('Failed to post comment. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error posting comment:', error);
        alert('Network error. Please try again.');
    })
    .finally(() => {
        postBtn.disabled = false;
        postBtn.textContent = 'Post';
    });
}

/**
 * Render a comment element
 * @param {Object} comment - Comment object
 * @param {number} articleId - Article ID
 * @returns {HTMLElement} Comment element
 */
function renderComment(comment, articleId) {
    const commentDiv = document.createElement('div');
    commentDiv.className = 'comment-card';
    commentDiv.setAttribute('data-comment-id', comment.id);

    const isEditable = comment.is_owner;
    const editedBadge = comment.updated_at ? '<span class="edited-badge">(edited)</span>' : '';

    commentDiv.innerHTML = `
        <div class="comment-header">
            <strong class="comment-username">${escapeHtml(comment.username)}</strong>
            <span class="comment-date">${comment.created_at}</span>
        </div>
        <div class="comment-content">
            <p class="comment-text">${escapeHtml(comment.content)}</p>
            ${editedBadge}
        </div>
        <div class="comment-actions">
            ${isEditable ? `<button class="btn-edit-comment" onclick="editComment(${comment.id}, ${articleId})">Edit</button>` : ''}
            ${isEditable ? `<button class="btn-delete-comment" onclick="deleteComment(${comment.id}, ${articleId})">Delete</button>` : ''}
            <button class="btn-report-comment" onclick="openReportModal(${comment.id})">Report</button>
        </div>
    `;

    return commentDiv;
}

/**
 * Edit a comment
 * @param {number} commentId - Comment ID
 * @param {number} articleId - Article ID
 */
function editComment(commentId, articleId) {
    const commentCard = document.querySelector(`.comment-card[data-comment-id="${commentId}"]`);
    if (!commentCard) return;

    const commentText = commentCard.querySelector('.comment-text');
    const currentContent = commentText.textContent;

    // Replace content with textarea
    const editContainer = document.createElement('div');
    editContainer.className = 'edit-comment-container';
    editContainer.innerHTML = `
        <textarea class="edit-comment-input" maxlength="1000" rows="3">${escapeHtml(currentContent)}</textarea>
        <div class="edit-comment-footer">
            <span class="char-count">${currentContent.length}/1000</span>
            <button class="btn-save-comment" onclick="saveEditComment(${commentId}, ${articleId})">Save</button>
            <button class="btn-cancel-edit" onclick="cancelEditComment(${commentId})">Cancel</button>
        </div>
    `;

    const commentContent = commentCard.querySelector('.comment-content');
    const originalContent = commentContent.innerHTML;
    commentCard.setAttribute('data-original-content', originalContent);
    commentContent.innerHTML = '';
    commentContent.appendChild(editContainer);

    // Setup character counter
    const textarea = editContainer.querySelector('.edit-comment-input');
    const charCount = editContainer.querySelector('.char-count');
    textarea.addEventListener('input', function() {
        charCount.textContent = `${this.value.length}/1000`;
    });

    textarea.focus();
}

/**
 * Save edited comment
 * @param {number} commentId - Comment ID
 * @param {number} articleId - Article ID
 */
function saveEditComment(commentId, articleId) {
    const commentCard = document.querySelector(`.comment-card[data-comment-id="${commentId}"]`);
    if (!commentCard) return;

    const textarea = commentCard.querySelector('.edit-comment-input');
    const newContent = textarea.value.trim();

    if (!newContent) {
        alert('Comment cannot be empty.');
        return;
    }

    if (newContent.length > 1000) {
        alert('Comment is too long. Maximum 1000 characters.');
        return;
    }

    const saveBtn = commentCard.querySelector('.btn-save-comment');
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';

    fetch(`/api/comments/${commentId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: newContent })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload comments to show updated version
            loadComments(articleId);
        } else {
            alert('Failed to update comment. Please try again.');
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save';
        }
    })
    .catch(error => {
        console.error('Error updating comment:', error);
        alert('Network error. Please try again.');
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save';
    });
}

/**
 * Cancel comment edit
 * @param {number} commentId - Comment ID
 */
function cancelEditComment(commentId) {
    const commentCard = document.querySelector(`.comment-card[data-comment-id="${commentId}"]`);
    if (!commentCard) return;

    const originalContent = commentCard.getAttribute('data-original-content');
    const commentContent = commentCard.querySelector('.comment-content');
    commentContent.innerHTML = originalContent;
}

/**
 * Delete a comment
 * @param {number} commentId - Comment ID
 * @param {number} articleId - Article ID
 */
function deleteComment(commentId, articleId) {
    if (!confirm('Are you sure you want to delete this comment?')) {
        return;
    }

    fetch(`/api/comments/${commentId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove comment from DOM
            const commentCard = document.querySelector(`.comment-card[data-comment-id="${commentId}"]`);
            if (commentCard) {
                commentCard.remove();
            }

            // Update comment count
            const commentsSection = document.querySelector(`.comments-section[data-article-id="${articleId}"]`);
            if (commentsSection) {
                const commentCount = commentsSection.querySelector('.comment-count');
                if (commentCount) {
                    const currentCount = parseInt(commentCount.textContent) || 0;
                    commentCount.textContent = Math.max(0, currentCount - 1);
                }

                // Show "no comments" message if all comments removed
                const commentsList = commentsSection.querySelector('.comments-list');
                if (commentsList && commentsList.children.length === 0) {
                    commentsList.innerHTML = '<p class="no-comments">No comments yet. Be the first to comment!</p>';
                }
            }
        } else {
            alert('Failed to delete comment. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error deleting comment:', error);
        alert('Network error. Please try again.');
    });
}

/**
 * Open report modal
 * @param {number} commentId - Comment ID
 */
function openReportModal(commentId) {
    currentReportCommentId = commentId;
    const modal = document.getElementById('report-modal');
    const textarea = document.getElementById('report-reason');
    const charCount = document.getElementById('report-char-count');

    if (modal) {
        modal.style.display = 'flex';
        textarea.value = '';
        charCount.textContent = '0';

        // Setup character counter
        textarea.oninput = function() {
            charCount.textContent = this.value.length;
        };
    }
}

/**
 * Close report modal
 */
function closeReportModal() {
    const modal = document.getElementById('report-modal');
    if (modal) {
        modal.style.display = 'none';
    }
    currentReportCommentId = null;
}

/**
 * Submit comment report
 */
function submitReport() {
    if (!currentReportCommentId) return;

    const textarea = document.getElementById('report-reason');
    const reason = textarea.value.trim();

    if (reason.length > 500) {
        alert('Report reason is too long. Maximum 500 characters.');
        return;
    }

    const submitBtn = document.querySelector('.modal-footer .btn-submit');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';

    fetch(`/api/comments/${currentReportCommentId}/report`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ reason: reason })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Comment reported successfully. Thank you for helping keep our community safe.');
            closeReportModal();
        } else {
            alert('Failed to report comment. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error reporting comment:', error);
        alert('Network error. Please try again.');
    })
    .finally(() => {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Report';
    });
}

/**
 * Share an article using Web Share API or clipboard fallback
 * @param {number} articleId - Article ID
 */
function shareArticle(articleId) {
    const card = document.querySelector(`.news-card[data-article-id="${articleId}"]`);
    if (!card) return;

    const title = card.querySelector('h3').textContent;

    // Generate URL to the article on our website
    const baseUrl = window.location.origin;
    const articleUrl = `${baseUrl}/article/${articleId}`;

    // Try Web Share API first (works on mobile)
    if (navigator.share) {
        navigator.share({
            title: title,
            text: 'Check out this good news!',
            url: articleUrl
        })
        .then(() => console.log('Shared successfully'))
        .catch(error => console.log('Error sharing:', error));
    } else {
        // Fallback: Copy to clipboard
        navigator.clipboard.writeText(articleUrl)
            .then(() => {
                alert('Link copied to clipboard! Share it with your friends.');
            })
            .catch(error => {
                console.error('Error copying to clipboard:', error);
                // Final fallback: Show URL in prompt
                prompt('Copy this link to share:', articleUrl);
            });
    }
}

/**
 * Setup character counters for comment inputs
 */
function setupCommentInputs() {
    const commentInputs = document.querySelectorAll('.comment-input');
    commentInputs.forEach(textarea => {
        // Remove existing listeners by cloning
        const newTextarea = textarea.cloneNode(true);
        textarea.parentNode.replaceChild(newTextarea, textarea);

        const container = newTextarea.closest('.comment-input-container');
        if (!container) return;

        const charCount = container.querySelector('.char-count');
        if (!charCount) return;

        newTextarea.addEventListener('input', function() {
            charCount.textContent = `${this.value.length}/1000`;
        });
    });
}

// ==================== HAPPINESS METER ====================

/**
 * Submit or update happiness rating for an article
 * @param {number} articleId - Article ID
 * @param {number} rating - Rating value (1-100)
 */
function rateHappiness(articleId, rating) {
    // Only submit if rating > 0
    if (rating == 0) return;

    fetch(`/api/articles/${articleId}/happiness`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ rating: parseInt(rating) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateHappinessMeter(articleId, data);
        } else {
            alert('Failed to submit rating. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error rating happiness:', error);
        alert('Network error. Please try again.');
    });
}

/**
 * Update happiness meter display as user drags slider (preview)
 * @param {number} articleId - Article ID
 * @param {number} value - Slider value (0-100)
 */
function updateHappinessPreview(articleId, value) {
    const meter = document.querySelector(`.happiness-meter[data-article-id="${articleId}"]`);
    if (!meter) return;

    const percentage = parseInt(value);

    // Update percentage display
    const percentageEl = meter.querySelector('.happiness-percentage');
    percentageEl.textContent = `${percentage}%`;

    // Update progress bar
    const bar = meter.querySelector('.happiness-bar');
    bar.style.width = `${percentage}%`;

    // Update emoji based on percentage
    const emojiEl = meter.querySelector('.happiness-emoji');
    if (percentage >= 80) {
        emojiEl.textContent = '🤩';
    } else if (percentage >= 60) {
        emojiEl.textContent = '😃';
    } else if (percentage >= 40) {
        emojiEl.textContent = '😊';
    } else if (percentage >= 20) {
        emojiEl.textContent = '🙂';
    } else {
        emojiEl.textContent = '😐';
    }
}

/**
 * Update happiness meter display with fresh data
 * @param {number} articleId - Article ID
 * @param {Object} data - Happiness data from backend
 */
function updateHappinessMeter(articleId, data) {
    const meter = document.querySelector(`.happiness-meter[data-article-id="${articleId}"]`);
    if (!meter) return;

    const percentage = data.happiness_average;
    const count = data.happiness_count;
    const userRating = data.user_happiness_rating;

    // Update percentage display
    const percentageEl = meter.querySelector('.happiness-percentage');
    percentageEl.textContent = `${percentage}%`;

    // Update progress bar
    const bar = meter.querySelector('.happiness-bar');
    bar.style.width = `${percentage}%`;

    // Update emoji based on percentage
    const emojiEl = meter.querySelector('.happiness-emoji');
    if (percentage >= 80) {
        emojiEl.textContent = '🤩';
    } else if (percentage >= 60) {
        emojiEl.textContent = '😃';
    } else if (percentage >= 40) {
        emojiEl.textContent = '😊';
    } else if (percentage >= 20) {
        emojiEl.textContent = '🙂';
    } else {
        emojiEl.textContent = '😐';
    }

    // Update count message
    const countEl = meter.querySelector('.happiness-count');
    if (count === 0) {
        countEl.textContent = 'Be the first to rate this post!';
    } else if (count === 1) {
        countEl.textContent = '1 person rated this';
    } else {
        countEl.textContent = `${count} people rated this`;
    }

    // Update slider value if user has rated
    const slider = meter.querySelector('.happiness-slider');
    if (slider && userRating) {
        slider.value = userRating;
    }
}

/**
 * Load happiness data for an article
 * @param {number} articleId - Article ID
 */
function loadHappinessMeter(articleId) {
    fetch(`/api/articles/${articleId}/happiness`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateHappinessMeter(articleId, data);
            }
        })
        .catch(error => console.error('Error loading happiness data:', error));
}

// ==================== DARK MODE ====================

/**
 * Toggle dark mode
 */
function toggleDarkMode() {
    const body = document.body;
    const sunIcon = document.querySelector('.sun-icon');
    const moonIcon = document.querySelector('.moon-icon');

    body.classList.toggle('dark-mode');

    // Toggle icons
    if (body.classList.contains('dark-mode')) {
        sunIcon.style.display = 'none';
        moonIcon.style.display = '';
        localStorage.setItem('theme', 'dark');
    } else {
        sunIcon.style.display = '';
        moonIcon.style.display = 'none';
        localStorage.setItem('theme', 'light');
    }
}

/**
 * Initialize dark mode from localStorage
 */
function initDarkMode() {
    const savedTheme = localStorage.getItem('theme');
    const body = document.body;
    const sunIcon = document.querySelector('.sun-icon');
    const moonIcon = document.querySelector('.moon-icon');

    if (savedTheme === 'dark') {
        body.classList.add('dark-mode');
        if (sunIcon) sunIcon.style.display = 'none';
        if (moonIcon) moonIcon.style.display = '';
    }
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

    // Setup comment inputs on page load
    setupCommentInputs();

    // Initialize dark mode
    initDarkMode();

    // Load happiness data for all visible articles
    document.querySelectorAll('.happiness-meter').forEach(meter => {
        const articleId = parseInt(meter.getAttribute('data-article-id'));
        loadHappinessMeter(articleId);
    });

    // Mark articles as read after a few seconds of viewing
    setTimeout(() => {
        markVisibleArticlesAsRead();
    }, 3000);  // Mark as read after 3 seconds
});

// ==================== READ/UNREAD ARTICLES ====================

/**
 * Toggle between showing read and unread articles
 */
function toggleReadArticles() {
    const btn = document.getElementById('toggle-read-btn');
    const urlParams = new URLSearchParams(window.location.search);
    const currentShowRead = urlParams.get('show_read') || 'false';

    let newShowRead = 'only';  // Show only read articles
    let btnText = 'Show Unread Articles';

    if (currentShowRead === 'only') {
        newShowRead = 'false';  // Show unread articles
        btnText = 'Show Previously Read Articles';
    }

    // Update URL and reload
    urlParams.set('show_read', newShowRead);
    window.location.search = urlParams.toString();
}

/**
 * Mark an article as read
 * @param {number} articleId - Article ID
 */
function markArticleAsRead(articleId) {
    fetch(`/api/articles/${articleId}/mark-read`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log(`Article ${articleId} marked as read`);
        }
    })
    .catch(error => {
        console.error('Error marking article as read:', error);
    });
}

/**
 * Mark all visible articles as read
 */
function markVisibleArticlesAsRead() {
    const articles = document.querySelectorAll('.news-card');
    articles.forEach(article => {
        const articleId = parseInt(article.getAttribute('data-article-id'));
        if (articleId) {
            markArticleAsRead(articleId);
        }
    });
}

/**
 * Update toggle button text based on current filter
 */
function updateToggleButtonText() {
    const btn = document.getElementById('toggle-read-btn');
    if (!btn) return;

    const urlParams = new URLSearchParams(window.location.search);
    const showRead = urlParams.get('show_read') || 'false';

    if (showRead === 'only') {
        btn.textContent = 'Show Unread Articles';
    } else {
        btn.textContent = 'Show Previously Read Articles';
    }
}

// Update button text on page load
document.addEventListener('DOMContentLoaded', function() {
    updateToggleButtonText();
});
