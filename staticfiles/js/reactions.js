// ==================== REACTIONS HOVER MENU ====================
(function() {
    'use strict';
    
    const reactionData = {
        'love': { icon: 'fa-heart', text: 'Love', color: '#f56565' },
        'haha': { icon: 'fa-laugh', text: 'Haha', color: '#ecc94b' },
        'wow': { icon: 'fa-surprise', text: 'Wow', color: '#9f7aea' },
        'sad': { icon: 'fa-sad-tear', text: 'Sad', color: '#4299e1' },
        'angry': { icon: 'fa-angry', text: 'Angry', color: '#e53e3e' },
        'like': { icon: 'fa-thumbs-up', text: 'Like', color: '#3182ce' }
    };
    
    function initReactionMenus() {
        document.querySelectorAll('.reaction-container').forEach(container => {
            const likeBtn = container.querySelector('.main-like-btn');
            const hoverMenu = container.querySelector('.reaction-hover-menu');
            
            if (!likeBtn || !hoverMenu) return;
            
            likeBtn.removeEventListener('mouseenter', handleMouseEnter);
            likeBtn.removeEventListener('mouseleave', handleMouseLeave);
            hoverMenu.removeEventListener('mouseenter', handleMenuEnter);
            hoverMenu.removeEventListener('mouseleave', handleMenuLeave);
            
            likeBtn._hoverMenu = hoverMenu;
            hoverMenu._likeBtn = likeBtn;
            
            likeBtn.addEventListener('mouseenter', handleMouseEnter);
            likeBtn.addEventListener('mouseleave', handleMouseLeave);
            hoverMenu.addEventListener('mouseenter', handleMenuEnter);
            hoverMenu.addEventListener('mouseleave', handleMenuLeave);
            
            hoverMenu.querySelectorAll('.reaction-option').forEach(option => {
                option.removeEventListener('click', handleReactionClick);
                option.addEventListener('click', handleReactionClick);
            });
        });
    }
    
    let reactionTimer, menuTimeout;
    
    function handleMouseEnter(e) {
        const likeBtn = e.currentTarget;
        clearTimeout(menuTimeout);
        reactionTimer = setTimeout(() => {
            likeBtn._hoverMenu.style.display = 'block';
        }, 400);
    }
    
    function handleMouseLeave(e) {
        const likeBtn = e.currentTarget;
        clearTimeout(reactionTimer);
        menuTimeout = setTimeout(() => {
            if (!likeBtn._hoverMenu.matches(':hover')) {
                likeBtn._hoverMenu.style.display = 'none';
            }
        }, 200);
    }
    
    function handleMenuEnter(e) {
        clearTimeout(menuTimeout);
    }
    
    function handleMenuLeave(e) {
        const hoverMenu = e.currentTarget;
        menuTimeout = setTimeout(() => {
            hoverMenu.style.display = 'none';
        }, 200);
    }
    
    function handleReactionClick(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const option = e.currentTarget;
        const postId = option.dataset.postId;
        const reaction = option.dataset.reaction;
        const postCard = option.closest('.post-card');
        const likeBtn = postCard.querySelector('.main-like-btn');
        const hoverMenu = option.closest('.reaction-hover-menu');
        
        likeBtn.disabled = true;
        const originalContent = likeBtn.innerHTML;
        likeBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
        
        fetch(`/ajax/react/${postId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ reaction_type: reaction })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.user_reaction) {
                    const r = reactionData[data.user_reaction];
                    likeBtn.innerHTML = `<i class="fas ${r.icon} me-1" style="color: ${r.color};"></i> ${r.text} <span class="like-count" style="color: #718096;">${data.counts[data.user_reaction]}</span>`;
                    likeBtn.style.color = r.color;
                } else {
                    likeBtn.innerHTML = `<i class="fas fa-thumbs-up me-1" style="color: #718096;"></i> Like <span class="like-count" style="color: #718096;">${data.counts.like}</span>`;
                    likeBtn.style.color = '#718096';
                }
                updateReactionCounter(postId, data.counts);
            } else {
                likeBtn.innerHTML = originalContent;
            }
        })
        .catch(() => {
            likeBtn.innerHTML = originalContent;
        })
        .finally(() => {
            likeBtn.disabled = false;
            hoverMenu.style.display = 'none';
        });
    }
    
    function updateReactionCounter(postId, counts) {
        const counter = document.querySelector(`.reaction-counter[data-post-id="${postId}"]`);
        if (!counter) return;
        
        const total = Object.values(counts).reduce((a, b) => a + b, 0);
        
        if (total === 0) {
            counter.innerHTML = '<i class="fas fa-thumbs-up me-1" style="color: #718096;"></i> <span>0</span>';
            return;
        }
        
        let mostPopular = 'like';
        let highest = 0;
        for (const [type, count] of Object.entries(counts)) {
            if (count > highest) {
                highest = count;
                mostPopular = type;
            }
        }
        
        const icons = {
            'like': '<i class="fas fa-thumbs-up me-1" style="color: #3182ce;"></i>',
            'love': '<i class="fas fa-heart me-1" style="color: #f56565;"></i>',
            'haha': '<i class="fas fa-laugh me-1" style="color: #ecc94b;"></i>',
            'wow': '<i class="fas fa-surprise me-1" style="color: #9f7aea;"></i>',
            'sad': '<i class="fas fa-sad-tear me-1" style="color: #4299e1;"></i>',
            'angry': '<i class="fas fa-angry me-1" style="color: #e53e3e;"></i>'
        };
        
        counter.innerHTML = icons[mostPopular] + ' <span>' + total + '</span>';
    }
    
    function getCsrfToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') return value;
        }
        return '';
    }
    
    document.addEventListener('DOMContentLoaded', initReactionMenus);
    
    const observer = new MutationObserver(initReactionMenus);
    const container = document.getElementById('posts-container');
    if (container) observer.observe(container, { childList: true, subtree: true });
})();