// ==================== REACTIONS MODAL ====================
// This file handles ONLY the reactions list popup

(function() {
    'use strict';
    
    function initReactionsModal() {
        // When modal opens
        document.querySelectorAll('[data-bs-target^="#reactionsModal-"]').forEach(trigger => {
            trigger.removeEventListener('click', handleModalOpen);
            trigger.addEventListener('click', handleModalOpen);
        });
        
        // Tab clicks
        document.querySelectorAll('.reaction-tab').forEach(tab => {
            tab.removeEventListener('click', handleTabClick);
            tab.addEventListener('click', handleTabClick);
        });
    }
    
    function handleModalOpen(e) {
        const trigger = e.currentTarget;
        const postCard = trigger.closest('.post-card');
        if (!postCard) return;
        
        const postId = postCard.dataset.postId;
        loadReactions(postId, 'all');
    }
    
    function handleTabClick(e) {
        e.preventDefault();
        
        const tab = e.currentTarget;
        const postId = tab.dataset.postId;
        const container = tab.closest('.reaction-tabs');
        
        // Update active tab
        container.querySelectorAll('.reaction-tab').forEach(t => {
            t.style.color = '#718096';
            t.style.fontWeight = '500';
            t.style.borderBottom = 'none';
        });
        tab.style.color = '#3182ce';
        tab.style.fontWeight = '600';
        tab.style.borderBottom = '2px solid #3182ce';
        
        loadReactions(postId, tab.dataset.tab);
    }
    
    function loadReactions(postId, type) {
        const listContainer = document.getElementById(`reactions-list-${postId}`);
        const loadingSpinner = document.getElementById(`reactions-loading-${postId}`);
        
        if (!listContainer || !loadingSpinner) return;
        
        loadingSpinner.style.display = 'block';
        listContainer.innerHTML = '';
        
        fetch(`/ajax/post/${postId}/reactions/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadingSpinner.style.display = 'none';
                    
                    let html = '';
                    let reactionsToShow = [];
                    
                    if (type === 'all') {
                        reactionsToShow = [
                            ...data.reactions.like.map(u => ({...u, type: 'like', emoji: '👍'})),
                            ...data.reactions.love.map(u => ({...u, type: 'love', emoji: '❤️'})),
                            ...data.reactions.haha.map(u => ({...u, type: 'haha', emoji: '😂'})),
                            ...data.reactions.wow.map(u => ({...u, type: 'wow', emoji: '😮'})),
                            ...data.reactions.sad.map(u => ({...u, type: 'sad', emoji: '😢'})),
                            ...data.reactions.angry.map(u => ({...u, type: 'angry', emoji: '😡'}))
                        ];
                    } else {
                        reactionsToShow = data.reactions[type].map(u => ({
                            ...u, 
                            type: type, 
                            emoji: type === 'like' ? '👍' : 
                                   type === 'love' ? '❤️' :
                                   type === 'haha' ? '😂' :
                                   type === 'wow' ? '😮' :
                                   type === 'sad' ? '😢' : '😡'
                        }));
                    }
                    
                    if (reactionsToShow.length === 0) {
                        html = '<p class="text-center text-muted py-4">No reactions yet</p>';
                    } else {
                        reactionsToShow.forEach(user => {
                            html += `
                                <div class="d-flex align-items-center justify-content-between py-2" style="border-bottom: 1px solid #f0f0f0;">
                                    <div class="d-flex align-items-center">
                                        <div class="profile-avatar me-3" style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #667eea, #764ba2); display: flex; align-items: center; justify-content: center; color: white; font-weight: 600;">
                                            ${user.profile_picture ? 
                                                `<img src="${user.profile_picture}" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">` : 
                                                user.username.charAt(0).toUpperCase()}
                                        </div>
                                        <div>
                                            <strong>${user.username}</strong>
                                            ${user.university ? 
                                                `<span style="font-size: 0.7rem; background: rgba(102, 126, 234, 0.1); color: #4a5568; padding: 2px 8px; border-radius: 12px; margin-left: 8px;">
                                                    ${user.university === 'ub' ? 'UB' : 
                                                      user.university === 'buan' ? 'BUAN' :
                                                      user.university === 'botho' ? 'BOTHO' :
                                                      user.university === 'limkokwing' ? 'LIMKO' :
                                                      user.university === 'baisago' ? 'ISAGO' :
                                                      user.university === 'biust' ? 'BIUST' : 'VISITOR'}
                                                </span>` : ''}
                                            ${user.is_verified ? '<i class="fas fa-check-circle ms-1" style="color: #1DA1F2; font-size: 0.8rem;"></i>' : ''}
                                        </div>
                                    </div>
                                    <span style="font-size: 1.2rem;">${user.emoji}</span>
                                </div>
                            `;
                        });
                    }
                    
                    listContainer.innerHTML = html;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                loadingSpinner.style.display = 'none';
                listContainer.innerHTML = '<p class="text-center text-danger py-4">Error loading reactions</p>';
            });
    }
    
    // Initialize
    document.addEventListener('DOMContentLoaded', initReactionsModal);
    
    // For infinite scroll
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                initReactionsModal();
            }
        });
    });
    
    observer.observe(document.getElementById('posts-container') || document.body, {
        childList: true,
        subtree: true
    });
})();