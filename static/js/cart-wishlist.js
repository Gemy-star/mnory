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
        formData.append('product_id', productId);
        formData.append('quantity', 1);
        formData.append('csrfmiddlewaretoken', getCSRFToken());

        // Get the current language prefix from the URL
        const langPrefix = window.location.pathname.split('/')[1] || 'ar';
        fetch(`/${langPrefix}/api/add-to-cart/`, {
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
        // Get the current language prefix from the URL
        const langPrefix = window.location.pathname.split('/')[1] || 'ar';
        fetch(`/${langPrefix}/cart/remove/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `item_id=${itemId}`,
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
        formData.append('product_id', productId);
        formData.append('csrfmiddlewaretoken', getCSRFToken());

        // Get the current language prefix from the URL
        const langPrefix = window.location.pathname.split('/')[1] || 'ar';
        fetch(`/${langPrefix}/api/add-to-wishlist/`, {
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
        // Get the current language prefix from the URL
        const langPrefix = window.location.pathname.split('/')[1] || 'ar';
        const url = `/${langPrefix}/api/get-counts/`;

        console.log('Updating counts from:', url);

        fetch(url, {
            credentials:'same-origin',
            headers:{'X-Requested-With':'XMLHttpRequest'}
        })
        .then(r => {
            if(!r.ok) {
                console.error(`Count update failed: HTTP ${r.status} for ${url}`);
                throw new Error(`HTTP ${r.status}`);
            }
            return r.json();
        })
        .then(data => {
            if(data.success){
                updateCartBadge(data.cart_count);
                updateWishlistBadge(data.wishlist_count);
            } else {
                console.error('Count update response indicates failure:', data);
            }
        })
        .catch(e => {
            console.error('Count update error for', url, ':', e);
            // Don't show notification for count updates as they're automatic
        });
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
        @keyframes slideInRight {0%{transform:translateX(100%);opacity:0;}100%{transform:translateX(0);opacity:1;}}
        @keyframes notificationPulse {0%,100%{box-shadow:0 8px 30px rgba(0,0,0,0.15);}50%{box-shadow:0 12px 40px rgba(0,0,0,0.25);}}
        .action-btn.loading{opacity:0.7;cursor:not-allowed;}
        .cart-notification{position:fixed;top:20px;right:-400px;background:linear-gradient(135deg,var(--theme-bg,#fff) 0%,rgba(255,255,255,0.95) 100%);color:var(--theme-text,#000);padding:20px 28px;border-radius:16px;box-shadow:0 12px 40px rgba(0,0,0,0.15),0 6px 20px rgba(0,0,0,0.08);z-index:10000;transition:all 0.4s cubic-bezier(0.175,0.885,0.32,1.275);border:1px solid var(--theme-border,rgba(0,0,0,0.08));min-width:320px;max-width:420px;font-family:'IBM Plex Sans Arabic',sans-serif;backdrop-filter:blur(12px);animation:notificationPulse 2s ease-in-out infinite alternate;}
        body.dark-mode .cart-notification{background:linear-gradient(135deg,rgba(40,40,40,0.95) 0%,rgba(60,60,60,0.9) 100%);border-color:rgba(255,255,255,0.1);box-shadow:0 12px 40px rgba(0,122,255,0.2),0 6px 20px rgba(0,0,0,0.3);}
        .cart-notification.show{right:20px;animation:slideInRight 0.4s ease-out;}
        .notification-content{display:flex;align-items:center;gap:14px;font-weight:600;font-size:16px;line-height:1.4;}
        .notification-success{border-right:4px solid #4CAF50;} .notification-success i{color:#4CAF50;font-size:22px;filter:drop-shadow(0 2px 4px rgba(76,175,80,0.3));}
        .notification-error{border-right:4px solid #F44336;} .notification-error i{color:#F44336;font-size:22px;filter:drop-shadow(0 2px 4px rgba(244,67,54,0.3));}
        .notification-info{border-right:4px solid var(--secondary-color,#A48111);} .notification-info i{color:var(--secondary-color,#A48111);font-size:22px;filter:drop-shadow(0 2px 4px rgba(164,129,17,0.3));}
        @media(max-width:480px){.cart-notification{right:-100%;left:10px;min-width:auto;max-width:calc(100%-20px);padding:16px 20px;}.cart-notification.show{right:auto;left:10px;}.notification-content{font-size:14px;}}
        `;
        document.head.appendChild(style);
    }
}
