// ==================== GLOBAL FUNCTIONS FOR COMMENT REPLIES ====================
window.showReplyForm = function(commentId) {
    const form = document.getElementById(`reply-form-${commentId}`);
    if (form) {
        form.style.display = 'block';
    }
};

window.submitReply = function(commentId, postId) {
    const input = document.getElementById(`reply-input-${commentId}`);
    const content = input.value.trim();
    const btn = event.target;
    
    if (!content) {
        alert('Please enter a reply');
        return;
    }
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    fetch(`/ajax/comment/${postId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ 
            content: content, 
            parent_id: commentId 
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert(data.error || 'Error posting reply');
            btn.disabled = false;
            btn.innerHTML = 'Reply';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Network error');
        btn.disabled = false;
        btn.innerHTML = 'Reply';
    });
};

// Initialize any existing reply buttons with event listeners
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.reply-to-comment-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const commentId = this.dataset.commentId;
            window.showReplyForm(commentId);
        });
    });
    
    document.querySelectorAll('.submit-reply-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const parentId = this.dataset.parentId;
            const postId = document.querySelector(`.reply-input[data-parent-id="${parentId}"]`)?.dataset.postId;
            if (postId) {
                window.submitReply(parentId, postId);
            }
        });
    });
});