// ==================== REACTIONS MODAL ====================
(function() {
    'use strict';
    
    function initReactionsModal() {
        document.querySelectorAll('[data-bs-target="#reactionsModal"], .reaction-counter').forEach(trigger => {
            trigger.removeEventListener('click', handleModalOpen);
            trigger.addEventListener('click', handleModalOpen);
        });
    }
    
    function handleModalOpen(e) {
        e.preventDefault();
        const postId = e.currentTarget.dataset.postId;
        if (!postId) {
            const postCard = e.currentTarget.closest('.post-card');
            if (postCard) {
                showReactions(postCard.dataset.postId);
            }
        } else {
            showReactions(postId);
        }
    }
    
    window.showReactions = function(postId) {
        const modal = document.getElementById('reactionsModal');
        if (!modal) return;
        
        const listContainer = document.getElementById('reactionsList');
        const loadingSpinner = document.getElementById('reactionsLoading');
        
        if (!listContainer || !loadingSpinner) return;
        
        listContainer.innerHTML = '';
        loadingSpinner.style.display = 'block';
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        fetch(`/ajax/post/${postId}/reactions/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadingSpinner.style.display = 'none';
                    
                    let html = '<div style="padding: 10px;">';
                    const allReactions = [
                        ...data.reactions.like.map(u => ({...u, reaction: '👍'})),
                        ...data.reactions.love.map(u => ({...u, reaction: '❤️'})),
                        ...data.reactions.haha.map(u => ({...u, reaction: '😂'})),
                        ...data.reactions.wow.map(u => ({...u, reaction: '😮'})),
                        ...data.reactions.sad.map(u => ({...u, reaction: '😢'})),
                        ...data.reactions.angry.map(u => ({...u, reaction: '😡'}))
                    ];
                    
                    if (allReactions.length === 0) {
                        html += '<p class="text-center text-muted py-3">No reactions yet</p>';
                    } else {
                        allReactions.forEach(user => {
                            html += `
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #f0f0f0;">
                                    <span><strong>${user.username}</strong></span>
                                    <span style="font-size: 1.2rem;">${user.reaction}</span>
                                </div>
                            `;
                        });
                    }
                    html += '</div>';
                    listContainer.innerHTML = html;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                loadingSpinner.style.display = 'none';
                listContainer.innerHTML = '<p class="text-center text-danger py-3">Error loading reactions</p>';
            });
    };
    
    document.addEventListener('DOMContentLoaded', initReactionsModal);
    
    const observer = new MutationObserver(initReactionsModal);
    const container = document.getElementById('posts-container');
    if (container) observer.observe(container, { childList: true, subtree: true });
})();