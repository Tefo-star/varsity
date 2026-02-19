// ==================== COMMENTS TOGGLE ====================
(function() {
    'use strict';
    
    function initCommentFeatures() {
        initCommentToggles();
        initCommentSubmits();
        initReplyFeatures(); // Added reply features
    }
    
    function initCommentToggles() {
        document.querySelectorAll('.comment-toggle-btn').forEach(btn => {
            btn.removeEventListener('click', handleCommentToggle);
            btn.addEventListener('click', handleCommentToggle);
        });
    }
    
    function initCommentSubmits() {
        document.querySelectorAll('.submit-comment-btn').forEach(btn => {
            btn.removeEventListener('click', handleCommentSubmit);
            btn.addEventListener('click', handleCommentSubmit);
        });
        
        document.querySelectorAll('.comment-input').forEach(input => {
            input.removeEventListener('keypress', handleCommentKeyPress);
            input.addEventListener('keypress', handleCommentKeyPress);
        });
    }
    
    // ==================== REPLY TO COMMENT (WHATSAPP STYLE) ====================
    function initReplyFeatures() {
        // Reply toggle buttons
        document.querySelectorAll('.reply-btn').forEach(btn => {
            btn.removeEventListener('click', handleReplyToggle);
            btn.addEventListener('click', handleReplyToggle);
        });
        
        // Reply submit buttons
        document.querySelectorAll('.submit-reply-btn').forEach(btn => {
            btn.removeEventListener('click', handleReplySubmit);
            btn.addEventListener('click', handleReplySubmit);
        });
        
        // View replies toggle
        document.querySelectorAll('.view-replies-btn').forEach(btn => {
            btn.removeEventListener('click', handleViewReplies);
            btn.addEventListener('click', handleViewReplies);
        });
        
        // Reply input enter key
        document.querySelectorAll('.reply-input').forEach(input => {
            input.removeEventListener('keypress', handleReplyKeyPress);
            input.addEventListener('keypress', handleReplyKeyPress);
        });
    }
    
    function handleReplyToggle(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const btn = e.currentTarget;
        const commentId = btn.dataset.commentId;
        const replyForm = document.querySelector(`.reply-form-${commentId}`);
        
        if (replyForm) {
            if (replyForm.style.display === 'none' || replyForm.style.display === '') {
                replyForm.style.display = 'block';
                replyForm.querySelector('.reply-input').focus();
            } else {
                replyForm.style.display = 'none';
            }
        }
    }
    
    function handleReplySubmit(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const btn = e.currentTarget;
        const parentId = btn.dataset.parentId;
        const input = document.querySelector(`.reply-input[data-parent-id="${parentId}"]`);
        const content = input.value.trim();
        const postId = input.dataset.postId;
        
        if (!content) {
            showNotification('Please enter a reply', 'error');
            return;
        }
        
        // Disable button
        btn.disabled = true;
        const originalText = btn.innerHTML;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
        
        fetch(`/ajax/comment/${postId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ 
                content: content,
                parent_id: parentId 
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Add reply to the replies container
                const repliesContainer = document.querySelector(`.replies-${parentId}`);
                repliesContainer.insertAdjacentHTML('beforeend', data.comment_html);
                
                // Show replies container if hidden
                if (repliesContainer.style.display === 'none' || repliesContainer.style.display === '') {
                    repliesContainer.style.display = 'block';
                }
                
                // Clear input and hide form
                input.value = '';
                document.querySelector(`.reply-form-${parentId}`).style.display = 'none';
                
                // Update reply count button
                const viewBtn = document.querySelector(`.view-replies-btn[data-comment-id="${parentId}"]`);
                if (viewBtn) {
                    const currentCount = parseInt(viewBtn.textContent.match(/\d+/)[0]) || 0;
                    const newCount = currentCount + 1;
                    viewBtn.textContent = `View ${newCount} repl${newCount === 1 ? 'y' : 'ies'}`;
                    viewBtn.style.display = 'inline-block';
                }
                
                showNotification('Reply sent!', 'success');
            } else {
                showNotification('Error: ' + (data.error || 'Failed'), 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Network error', 'error');
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
        });
    }
    
    function handleViewReplies(e) {
        e.preventDefault();
        
        const btn = e.currentTarget;
        const commentId = btn.dataset.commentId;
        const repliesDiv = document.querySelector(`.replies-${commentId}`);
        
        if (repliesDiv.style.display === 'none' || repliesDiv.style.display === '') {
            repliesDiv.style.display = 'block';
            btn.textContent = 'Hide replies';
        } else {
            repliesDiv.style.display = 'none';
            const count = repliesDiv.children.length;
            btn.textContent = `View ${count} repl${count === 1 ? 'y' : 'ies'}`;
        }
    }
    
    function handleReplyKeyPress(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const input = e.currentTarget;
            const parentId = input.dataset.parentId;
            const submitBtn = document.querySelector(`.submit-reply-btn[data-parent-id="${parentId}"]`);
            if (submitBtn) submitBtn.click();
        }
    }
    
    function handleCommentToggle(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const btn = e.currentTarget;
        const postId = btn.dataset.postId;
        const commentsSection = document.querySelector(`.comments-section-${postId}`);
        
        if (!commentsSection) return;
        
        if (commentsSection.style.display === 'none' || commentsSection.style.display === '') {
            commentsSection.style.display = 'block';
            btn.innerHTML = '<i class="fas fa-comment me-1" style="color: #4299e1;"></i> Hide Comments';
        } else {
            commentsSection.style.display = 'none';
            btn.innerHTML = '<i class="fas fa-comment me-1" style="color: #4299e1;"></i> Comment';
        }
    }
    
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
        
        btn.disabled = true;
        const originalText = btn.innerHTML;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
        
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
                const commentsContainer = document.querySelector(`.comments-container-${postId}`);
                commentsContainer.insertAdjacentHTML('afterbegin', data.comment_html);
                input.value = '';
                
                const commentCountSpan = document.querySelector(`.comment-toggle-btn[data-post-id="${postId}"] .comments-count`);
                if (commentCountSpan) {
                    commentCountSpan.textContent = parseInt(commentCountSpan.textContent) + 1;
                }
                
                const statsCommentSpan = document.querySelector(`.post-card[data-post-id="${postId}"] .comments-count`);
                if (statsCommentSpan) {
                    statsCommentSpan.textContent = parseInt(statsCommentSpan.textContent) + 1;
                }
                
                showNotification('Comment added!', 'success');
            } else {
                showNotification('Error: ' + (data.error || 'Failed'), 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Network error', 'error');
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
        });
    }
    
    function handleCommentKeyPress(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const input = e.currentTarget;
            const postId = input.dataset.postId;
            const submitBtn = document.querySelector(`.submit-comment-btn[data-post-id="${postId}"]`);
            if (submitBtn) submitBtn.click();
        }
    }
    
    function getCsrfToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') return value;
        }
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfInput ? csrfInput.value : '';
    }
    
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
        toast.style.zIndex = '9999';
        toast.style.animation = 'slideUp 0.3s ease';
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.animation = 'slideDown 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    document.addEventListener('DOMContentLoaded', initCommentFeatures);
    
    const observer = new MutationObserver(initCommentFeatures);
    const container = document.getElementById('posts-container');
    if (container) observer.observe(container, { childList: true, subtree: true });
    
    if (!document.getElementById('comment-animations')) {
        const style = document.createElement('style');
        style.id = 'comment-animations';
        style.textContent = `
            @keyframes slideUp {
                from { opacity: 0; transform: translate(-50%, 20px); }
                to { opacity: 1; transform: translate(-50%, 0); }
            }
            @keyframes slideDown {
                from { opacity: 1; transform: translate(-50%, 0); }
                to { opacity: 0; transform: translate(-50%, 20px); }
            }
        `;
        document.head.appendChild(style);
    }
})();