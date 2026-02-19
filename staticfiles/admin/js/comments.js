// ==================== COMMENTS TOGGLE ====================
// This file handles ONLY the comment toggle functionality
// Independent from reactions and other features

(function() {
    'use strict';
    
    // Initialize comment toggles and submit buttons
    function initCommentFeatures() {
        initCommentToggles();
        initCommentSubmits();
    }
    
    // Initialize comment toggle buttons
    function initCommentToggles() {
        document.querySelectorAll('.comment-toggle-btn').forEach(btn => {
            // Remove old listeners to prevent duplicates
            btn.removeEventListener('click', handleCommentToggle);
            btn.addEventListener('click', handleCommentToggle);
        });
    }
    
    // Initialize comment submit buttons
    function initCommentSubmits() {
        document.querySelectorAll('.submit-comment-btn').forEach(btn => {
            btn.removeEventListener('click', handleCommentSubmit);
            btn.addEventListener('click', handleCommentSubmit);
        });
        
        // Also allow Enter key to submit
        document.querySelectorAll('.comment-input').forEach(input => {
            input.removeEventListener('keypress', handleCommentKeyPress);
            input.addEventListener('keypress', handleCommentKeyPress);
        });
    }
    
    // Handle comment toggle click
    function handleCommentToggle(e) {
        e.preventDefault();
        e.stopPropagation(); // Prevent interference with other features
        
        const btn = e.currentTarget;
        const postId = btn.dataset.postId;
        const commentsSection = document.querySelector(`.comments-section-${postId}`);
        
        if (!commentsSection) return;
        
        // Toggle visibility
        if (commentsSection.style.display === 'none' || commentsSection.style.display === '') {
            commentsSection.style.display = 'block';
            btn.innerHTML = '<i class="fas fa-comment me-1" style="color: #4299e1;"></i> Hide Comments';
        } else {
            commentsSection.style.display = 'none';
            btn.innerHTML = '<i class="fas fa-comment me-1" style="color: #4299e1;"></i> Comment';
        }
    }
    
    // Handle comment submission
    function handleCommentSubmit(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const btn = e.currentTarget;
        const postId = btn.dataset.postId;
        const input = document.querySelector(`.comment-input[data-post-id="${postId}"]`);
        const content = input.value.trim();
        
        if (!content) {
            showNotification('Please enter a comment', 'error');
            return;
        }
        
        // Disable button and show loading
        btn.disabled = true;
        const originalText = btn.innerHTML;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" style="width:1rem; height:1rem;"></span>';
        
        // Get CSRF token
        const csrfToken = getCsrfToken();
        
        fetch(`/ajax/comment/${postId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ content: content })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Add comment to container
                const commentsContainer = document.querySelector(`.comments-container-${postId}`);
                commentsContainer.insertAdjacentHTML('afterbegin', data.comment_html);
                input.value = '';
                
                // Update comment count
                const commentCountSpan = document.querySelector(`.comment-toggle-btn[data-post-id="${postId}"] .comments-count`);
                if (commentCountSpan) {
                    const currentCount = parseInt(commentCountSpan.textContent) || 0;
                    commentCountSpan.textContent = currentCount + 1;
                }
                
                // Update the comments count in stats
                const statsCommentSpan = document.querySelector(`.post-card[data-post-id="${postId}"] .comments-count`);
                if (statsCommentSpan) {
                    const currentCount = parseInt(statsCommentSpan.textContent) || 0;
                    statsCommentSpan.textContent = currentCount + 1;
                }
                
                showNotification('Comment added!', 'success');
            } else {
                showNotification('Error: ' + (data.error || 'Failed to add comment'), 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Network error. Please try again.', 'error');
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
        });
    }
    
    // Handle Enter key in comment input
    function handleCommentKeyPress(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const input = e.currentTarget;
            const postId = input.dataset.postId;
            const submitBtn = document.querySelector(`.submit-comment-btn[data-post-id="${postId}"]`);
            if (submitBtn) {
                submitBtn.click();
            }
        }
    }
    
    // Get CSRF token from cookie or form
    function getCsrfToken() {
        // Try to get from cookie first
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        
        // Fallback to form input
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfInput ? csrfInput.value : '';
    }
    
    // Show notification
    function showNotification(message, type = 'success') {
        const toast = document.createElement('div');
        toast.style.position = 'fixed';
        toast.style.bottom = '20px';
        toast.style.left = '50%';
        toast.style.transform = 'translateX(-50%)';
        toast.style.background = type === 'success' ? '#48bb78' : '#f56565';
        toast.style.color = 'white';
        toast.style.padding = '10px 20px';
        toast.style.borderRadius = '50px';
        toast.style.boxShadow = '0 5px 20px rgba(0,0,0,0.2)';
        toast.style.zIndex = '9999';
        toast.style.animation = 'slideUp 0.3s ease';
        toast.style.fontWeight = '500';
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideDown 0.3s ease';
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    // Initialize on load
    document.addEventListener('DOMContentLoaded', initCommentFeatures);
    
    // For infinite scroll - observe new posts being added
    const observer = new MutationObserver(function(mutations) {
        let shouldInit = false;
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                shouldInit = true;
            }
        });
        if (shouldInit) {
            initCommentFeatures();
        }
    });
    
    // Start observing
    const postsContainer = document.getElementById('posts-container');
    if (postsContainer) {
        observer.observe(postsContainer, {
            childList: true,
            subtree: true
        });
    } else {
        // Fallback to observe body
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    // Add required animations if not present
    if (!document.querySelector('#comment-animations')) {
        const style = document.createElement('style');
        style.id = 'comment-animations';
        style.textContent = `
            @keyframes slideUp {
                from {
                    opacity: 0;
                    transform: translate(-50%, 20px);
                }
                to {
                    opacity: 1;
                    transform: translate(-50%, 0);
                }
            }
            @keyframes slideDown {
                from {
                    opacity: 1;
                    transform: translate(-50%, 0);
                }
                to {
                    opacity: 0;
                    transform: translate(-50%, 20px);
                }
            }
        `;
        document.head.appendChild(style);
    }
    
})();