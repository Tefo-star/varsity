function handleCommentReplySubmit(e) {
    e.preventDefault();
    
    const btn = e.currentTarget;
    const parentId = btn.dataset.parentId;
    const input = document.querySelector(`.reply-input[data-parent-id="${parentId}"]`);
    const content = input.value.trim();
    const postId = input.dataset.postId;
    
    if (!content) return;
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    
    fetch(`/ajax/comment/${postId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ content: content, parent_id: parentId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload the page to show the new reply
            location.reload();
        } else {
            alert(data.error || 'Cannot reply here');
        }
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = 'Reply';
    });
}