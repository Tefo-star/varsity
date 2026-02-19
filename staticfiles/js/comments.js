// ==================== COMMENTS TOGGLE ====================
(function() {
    'use strict';
    
    function initCommentFeatures() {
        initCommentToggles();
        initCommentSubmits();
        initReplyFeatures();
        initPostReplyFeatures();
        initPostReplies();
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
    
    // ==================== WHATSAPP-STYLE POST REPLIES ====================
    function initPostReplies() {
        document.querySelectorAll('.toggle-replies-btn').forEach(btn => {
            btn.removeEventListener('click', toggleReplies);
            btn.addEventListener('click', toggleReplies);
        });
    }
    
    function toggleReplies(e) {
        e.preventDefault();
        const btn = e.currentTarget;
        const postId = btn.dataset.postId;
        const repliesContainer = document.querySelector(`.replies-container-${postId}`);
        const icon = btn.querySelector('i');
        
        if (repliesContainer.style.display === 'none' || repliesContainer.style.display === '') {
            repliesContainer.style.display = 'block';
            icon.className = 'fas fa-chevron-down me-1';
            btn.innerHTML = btn.innerHTML.replace('View', 'Hide');
        } else {
            repliesContainer.style.display = 'none';
            icon.className = 'fas fa-chevron-right me-1';
            btn.innerHTML = btn.innerHTML.replace('Hide', 'View');
        }
    }
    
    // ==================== REPLY TO POST ====================
    function initPostReplyFeatures() {
        document.querySelectorAll('.reply-to-post-btn').forEach(btn => {
            btn.removeEventListener('click', handlePostReplyToggle);
            btn.addEventListener('click', handlePostReplyToggle);
        });
        
        document.querySelectorAll('.submit-reply-to-post-btn').forEach(btn => {
            btn.removeEventListener('click', handlePostReplySubmit);
            btn.addEventListener('click', handlePostReplySubmit);
        });
        
        document.querySelectorAll('.reply-to-post-input').forEach(input => {
            input.removeEventListener('keypress', handlePostReplyKeyPress);
            input.addEventListener('keypress', handlePostReplyKeyPress);
        });
    }
    
    function handlePostReplyToggle(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const btn = e.currentTarget;
        const postId = btn.dataset.postId;
        const replyForm = document.querySelector(`.reply-to-post-form-${postId}`);
        
        if (replyForm) {
            if (replyForm.style.display === 'none' || replyForm.style.display === '') {
                replyForm.style.display = 'block';
                replyForm.querySelector('.reply-to-post-input').focus();
            } else {
                replyForm.style.display = 'none';
            }
        }
    }
    
    function handlePostReplySubmit(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const btn = e.currentTarget;
        const postId = btn.dataset.postId;
        const input = document.querySelector(`.reply-to-post-input[data-post-id="${postId}"]`);
        const content = input.value.trim();
        
        if (!content) {
            showNotification('Please enter a reply', 'error');
            return;
        }
        
        btn.disabled = true;
        const originalText = btn.innerHTML;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
        
        fetch(`/ajax/post/${postId}/reply/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ content: content })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const postsContainer = document.getElementById('posts-container');
                postsContainer.insertAdjacentHTML('afterbegin', data.reply_html);
                
                const originalPost = document.querySelector(`.post-card[data-post-id="${postId}"]`);
                if (originalPost) {
                    const repliesSection = originalPost.querySelector('.replies-section');
                    if (repliesSection) {
                        const toggleBtn = repliesSection.querySelector('.toggle-replies-btn');
                        const count = parseInt(toggleBtn.textContent.match(/\d+/)[0]) || 0;
                        toggleBtn.innerHTML = `<i class="fas fa-chevron-right me-1"></i> View ${count + 1} repl${count + 1 === 1 ? 'y' : 'ies'}`;
                    }
                }
                
                input.value = '';
                document.querySelector(`.reply-to-post-form-${postId}`).style.display = 'none';
                
                showNotification('Reply posted at the top!', 'success');
                
                const newReply = document.querySelector(`.post-card[data-post-id="${data.reply_id}"]`);
                if (newReply) {
                    newReply.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
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
    
    function handlePostReplyKeyPress(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const input = e.currentTarget;
            const postId = input.dataset.postId;
            const submitBtn = document.querySelector(`.submit-reply-to-post-btn[data-post-id="${postId}"]`);
            if (submitBtn) submitBtn.click();
        }
    }
    
    // ==================== GET CSRF TOKEN ====================
    function getCsrfToken() {
        // Try cookie first
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') return value;
        }
        // Try hidden input
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfInput ? csrfInput.value : '';
    }
    
    // ==================== SHOW NOTIFICATION ====================
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
    
    // Placeholder functions to prevent errors
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
        
        fetch(`/ajax/comment/${postId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ content: content })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                showNotification('Error: ' + (data.error || 'Failed'), 'error');
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Network error', 'error');
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
    
    function initReplyFeatures() {
        // Comment reply functionality - handled by inline script in _comment.html
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