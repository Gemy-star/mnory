// static/js/cart-wishlist.js - Cart & Wishlist Module
// ========================================
// Prevents double initialization
// ========================================

if (typeof window.cartWishlistInitialized !== 'undefined') {
    console.log('Cart & Wishlist already initialized');
} else {
    window.cartWishlistInitialized = true;

    // ========================================
    // UTILITY FUNCTIONS
    // ========================================
    function getCSRFToken() {
        const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenElement) return tokenElement.value;
        const cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
        return cookieMatch ? cookieMatch[1] : '';
    }

    function showNotification(message, type = 'info') {
        document.querySelectorAll('.cart-notification').forEach(n => n.remove());
        const notification = document.createElement('div');
        notification.className = `cart-notification notification-${type}`;
        const icons = { success: 'fa-check-circle', error: 'fa-exclamation-circle', info: 'fa-info-circle' };
        notification.innerHTML = `<div class="notification-content"><i class="fas ${icons[type]}"></i><span>${message}</span></div>`;
        document.body.appendChild(notification);
        requestAnimationFrame(() => notification.classList.add('show'));
        setTimeout(() => { notification.classList.remove('show'); setTimeout(() => notification.remove(), 300); }, 3000);
    }

    // ========================================
    // CART FUNCTIONS
    // ========================================
    window.addToCart = function(productId, button = null) {
        if (!productId) return console.error('Product ID is required');
        if (button) {
            button.disabled = true;
            button.classList.add('loading');
            const icon = button.querySelector('i');
            if (icon) icon.className = 'fas fa-spinner fa-spin';
        }
        const formData = new FormData();
        formData.append('quantity', 1);
        formData.append('csrfmiddlewaretoken', getCSRFToken());

        fetch(`/ajax/cart/add/${productId}/`, {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            credentials: 'same-origin'
        })
        .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
        .then(data => {
            if (data.success) {
                showNotification(data.message || 'تمت إضافة المنتج إلى السلة', 'success');
                updateAllCounts();
                if (button) {
                    button.classList.add('active');
                    const icon = button.querySelector('i');
                    if (icon) icon.className = 'fas fa-check';
                    button.style.animation = 'cartBounce 0.6s ease-in-out';
                    setTimeout(() => {
                        if (icon) icon.className = 'fas fa-shopping-cart';
                        button.style.animation = '';
                        button.classList.remove('loading');
                        button.disabled = false;
                    }, 1500);
                }
            } else {
                showNotification(data.message || 'حدث خطأ أثناء الإضافة', 'error');
                if (button) {
                    button.disabled = false;
                    button.classList.remove('loading');
                    const icon = button.querySelector('i');
                    if (icon) icon.className = 'fas fa-shopping-cart';
                }
            }
        })
        .catch(error => {
            console.error('Cart Error:', error);
            showNotification('حدث خطأ في الاتصال', 'error');
            if (button) {
                button.disabled = false;
                button.classList.remove('loading');
                const icon = button.querySelector('i');
                if (icon) icon.className = 'fas fa-shopping-cart';
            }
        });
    };

    window.removeFromCart = function(itemId) {
        if (!confirm('هل أنت متأكد من حذف هذا المنتج من السلة؟')) return;
        fetch(`/ajax/cart/remove/${itemId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
        .then(data => {
            if (data.success) {
                const card = document.querySelector(`.product-card[data-product-id="${data.product_id}"]`);
                if (card) {
                    card.classList.add('removing');
                    setTimeout(() => {
                        card.remove();
                        if (!document.querySelectorAll('.product-card[data-context="cart"]').length)
                            setTimeout(() => location.reload(), 500);
                    }, 300);
                }
                updateAllCounts();
                showNotification(data.message || 'تمت الإزالة من السلة', 'success');
            } else {
                showNotification(data.message || 'حدث خطأ', 'error');
            }
        })
        .catch(e => {
            console.error('Remove cart error:', e);
            showNotification('حدث خطأ في الاتصال', 'error');
        });
    };

    // ========================================
    // WISHLIST FUNCTIONS
    // ========================================
    window.toggleWishlist = function(productId, button = null) {
        if (!productId) return console.error('Product ID is required');
        if (button) button.disabled = true;
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', getCSRFToken());

        fetch(`/ajax/wishlist/toggle/${productId}/`, {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            credentials: 'same-origin'
        })
        .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
        .then(data => {
            if (data.success) {
                showNotification(data.message || 'تم التحديث بنجاح', 'success');
                updateAllCounts();
                if (button) {
                    const icon = button.querySelector('i');
                    const card = button.closest('.product-card');
                    const isWishlistPage = card && card.dataset.context === 'wishlist';

                    if (data.in_wishlist || data.added) {
                        button.classList.add('active');
                        if (icon) {
                            icon.classList.remove('far');
                            icon.classList.add('fas');
                            icon.style.animation='heartBeat 0.5s ease';
                            setTimeout(()=>{icon.style.animation='';},500);
                        }
                    } else {
                        if (isWishlistPage) {
                            card.classList.add('removing');
                            setTimeout(()=>{
                                card.remove();
                                if(!document.querySelectorAll('.product-card[data-context="wishlist"]').length)
                                    setTimeout(()=>location.reload(),500);
                            },300);
                        } else {
                            button.classList.remove('active');
                            if(icon){
                                icon.classList.remove('fas');
                                icon.classList.add('far');
                            }
                        }
                    }
                }
            } else {
                showNotification(data.message || 'حدث خطأ', 'error');
            }
            if (button && !button.closest('.product-card.removing')) button.disabled = false;
        })
        .catch(e => {
            console.error('Wishlist Error:', e);
            showNotification('حدث خطأ في الاتصال', 'error');
            if(button) button.disabled=false;
        });
    };

    // ========================================
    // UPDATE COUNTS
    // ========================================
    function updateAllCounts() {
        fetch('/ajax/cart-count/', {
            credentials:'same-origin',
            headers:{'X-Requested-With':'XMLHttpRequest'}
        })
        .then(r => { if(!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
        .then(data => {
            if(data.success){
                updateCartBadge(data.cart_count);
                updateWishlistBadge(data.wishlist_count);
            }
        })
        .catch(e=>console.error('Count update error:',e));
    }

    function updateCartBadge(count){
        document.querySelectorAll('#cartBadge, #cart-count, #drawer-cart-count, .cart-badge, [data-cart-count]').forEach(badge=>{
            if(count>0){
                badge.textContent=count;
                badge.style.display='flex';
                badge.style.animation='badgePulse 0.6s ease';
                setTimeout(()=>badge.style.animation='',600);
            } else {
                badge.textContent='0';
                badge.style.display='flex';
            }
        });
    }

    function updateWishlistBadge(count){
        document.querySelectorAll('#wishlistBadge, #wishlist-count, #drawer-wishlist-count, .wishlist-badge, [data-wishlist-count]').forEach(badge=>{
            if(count>0){
                badge.textContent=count;
                badge.style.display='flex';
                badge.style.animation='badgePulse 0.6s ease';
                setTimeout(()=>badge.style.animation='',600);
            } else {
                badge.textContent='0';
                badge.style.display='flex';
            }
        });
    }

    // ========================================
    // INITIALIZE
    // ========================================
    document.addEventListener('DOMContentLoaded', ()=>{
        console.log('Cart & Wishlist system initialized');
        updateAllCounts();
        setInterval(updateAllCounts, 30000);
        if(new URLSearchParams(window.location.search).get('login_required'))
            showNotification('يرجى تسجيل الدخول للمتابعة','info');

        // Global event delegation for action buttons (no inline onclicks needed)
        document.addEventListener('click', function(e){
            const btn = e.target.closest('button[data-action]');
            if(!btn) return;
            const action = btn.getAttribute('data-action');
            if(!action) return;
            // Prevent navigating when buttons are inside links or near clickable cards
            e.preventDefault();
            e.stopPropagation();

            const productId = btn.getAttribute('data-product-id');
            switch(action){
                case 'cart-add':
                    if(productId) window.addToCart(productId, btn);
                    break;
                case 'wishlist-toggle':
                    if(productId) window.toggleWishlist(productId, btn);
                    break;
                case 'cart-remove':
                    const itemId = btn.getAttribute('data-item-id');
                    if(itemId) window.removeFromCart(itemId);
                    break;
                default:
                    break;
            }
        });
    });

    // ========================================
    // CSS ANIMATIONS
    // ========================================
    if(!document.getElementById('cart-wishlist-styles')){
        const style=document.createElement('style');
        style.id='cart-wishlist-styles';
        style.textContent=`
        @keyframes heartBeat {0%,100%{transform:scale(1);}25%{transform:scale(1.3);}50%{transform:scale(1.1);}75%{transform:scale(1.25);}}
        @keyframes badgePulse {0%,100%{transform:scale(1);}50%{transform:scale(1.2);}}
        @keyframes cartBounce {0%,100%{transform:scale(1);}25%{transform:scale(1.3);}50%{transform:scale(1.1);}75%{transform:scale(1.25);}}
        .action-btn.loading{opacity:0.7;cursor:not-allowed;}
        .cart-notification{position:fixed;top:20px;right:-400px;background:var(--theme-bg,#fff);color:var(--theme-text,#000);padding:16px 24px;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,0.15);z-index:10000;transition:right 0.3s cubic-bezier(0.175,0.885,0.32,1.275);border:1px solid var(--theme-border,#eee);min-width:300px;max-width:400px;font-family:'IBM Plex Sans Arabic',sans-serif;}
        .cart-notification.show{right:20px;}
        .notification-content{display:flex;align-items:center;gap:12px;font-weight:600;font-size:15px;}
        .notification-success{border-right:4px solid #4CAF50;} .notification-success i{color:#4CAF50;font-size:20px;}
        .notification-error{border-right:4px solid #F44336;} .notification-error i{color:#F44336;font-size:20px;}
        .notification-info{border-right:4px solid var(--secondary-color,#A48111);} .notification-info i{color:var(--secondary-color,#A48111);font-size:20px;}
        @media(max-width:480px){.cart-notification{right:-100%;left:10px;min-width:auto;max-width:calc(100%-20px);}.cart-notification.show{right:auto;left:10px;}}
        `;
        document.head.appendChild(style);
    }
}
