// static/js/cart-wishlist.js - Cart & Wishlist Module (FIXED)
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

    function getLangPrefix() {
        return window.location.pathname.split('/')[1] || 'en';
    }

    function isArabic() {
        return getLangPrefix() === 'ar';
    }

    // Bilingual messages
    const messages = {
        addedToCart: { ar: 'تمت إضافة المنتج إلى السلة', en: 'Added to cart successfully!' },
        failedToAddCart: { ar: 'فشل إضافة المنتج إلى السلة', en: 'Failed to add to cart' },
        wishlistUpdated: { ar: 'تم تحديث قائمة الأمنيات', en: 'Wishlist updated successfully!' },
        wishlistFailed: { ar: 'فشل تحديث قائمة الأمنيات', en: 'Failed to update wishlist' },
        connectionError: { ar: 'حدث خطأ في الاتصال. حاول مرة أخرى.', en: 'Connection error. Please try again.' },
        removedFromCart: { ar: 'تمت إزالة المنتج من السلة', en: 'Removed from cart successfully' },
        removeCartFailed: { ar: 'فشل إزالة المنتج', en: 'Failed to remove from cart' },
        confirmRemove: { ar: 'هل أنت متأكد من حذف هذا المنتج من السلة؟', en: 'Are you sure you want to remove this item from cart?' },
        selectColorSize: { ar: 'الرجاء اختيار اللون والحجم أولاً', en: 'Please select color and size first' },
        errorOccurred: { ar: 'حدث خطأ. حاول مرة أخرى.', en: 'An error occurred. Please try again.' }
    };

    function getMessage(key) {
        const lang = isArabic() ? 'ar' : 'en';
        return messages[key] ? messages[key][lang] : key;
    }

    // Expose getMessage globally for use in other scripts
    window.getCartMessage = getMessage;

    function showNotification(message, type = 'info') { // MODIFIED
        document.querySelectorAll('.cart-notification').forEach(n => n.remove());
        const notification = document.createElement('div');
        notification.className = `cart-notification notification-${type} animate__animated animate__fadeInRight`; // Use Animate.css
        const icons = { success: 'check_circle', error: 'error', info: 'info', warning: 'warning' }; // Use Material Icons
        notification.innerHTML = `<div class="notification-content"><span class="material-icons">${icons[type]}</span><span>${message}</span></div>`;
        document.body.appendChild(notification);
        requestAnimationFrame(() => notification.classList.add('show'));
        setTimeout(() => { notification.classList.remove('show'); setTimeout(() => notification.remove(), 300); }, 3000);
    }

    // Expose showNotification globally for use in other scripts
    window.showNotification = showNotification;

    // ========================================
    // CART FUNCTIONS (FIXED)
    // ========================================
    window.addToCart = function(productId, options = {}) {
        if (!productId) return console.error('Product ID is required');

        // FIXED: Handle both button object and options object properly
        let button = null;
        let quantity = 1;
        let colorId = null;
        let sizeId = null;

        // Check if options is actually the button element (for backward compatibility)
        if (options instanceof HTMLElement) {
            button = options;
        } else {
            button = options.button || null;
            quantity = options.quantity || 1;
            colorId = options.colorId || options.color_id || null;
            sizeId = options.sizeId || options.size_id || null;
        }

        if (button) {
            button.disabled = true;
            button.classList.add('loading');
            const icon = button.querySelector('i') || button.querySelector('.material-icons');
            if (icon) {
                icon.className = 'material-icons';
                icon.textContent = 'hourglass_empty';
            }
        }

        const formData = new FormData();
        formData.append('product_id', productId);
        formData.append('quantity', quantity);
        if (colorId) formData.append('color_id', colorId);
        if (sizeId) formData.append('size_id', sizeId);
        formData.append('csrfmiddlewaretoken', getCSRFToken());

        // FIXED: Get the current language prefix from the URL, default to 'en' not 'ar'
        const langPrefix = getLangPrefix();
        fetch(`/${langPrefix}/api/add-to-cart/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
        .then(data => {
            if (data.success) {
                showNotification(data.message || getMessage('addedToCart'), 'success');
                updateAllCounts();

                // --- NEW: Update button state ---
                if (button) {
                    button.dataset.action = 'cart-remove';
                    button.dataset.itemId = data.cart_item_id; // Store the new cart item ID
                    button.title = getMessage('removedFromCart'); // Assuming this is a translatable string
                    button.setAttribute('aria-label', getMessage('removedFromCart'));
                    button.classList.add('active');

                    const addIcon = button.querySelector('.cart-add-icon');
                    const removeIcon = button.querySelector('.cart-remove-icon');
                    if (addIcon) addIcon.style.display = 'none';
                    if (removeIcon) removeIcon.style.display = 'inline-block';

                    button.style.animation = 'cartBounce 0.6s ease-in-out';
                    setTimeout(() => {
                        button.style.animation = '';
                        button.classList.remove('loading');
                        button.disabled = false;
                    }, 1500);
                }
            } else {
                showNotification(data.message || getMessage('failedToAddCart'), 'error');
                if (button) {
                    button.disabled = false;
                    button.classList.remove('loading');
                    const addIcon = button.querySelector('.cart-add-icon');
                    const removeIcon = button.querySelector('.cart-remove-icon');
                    if(addIcon && removeIcon) {
                        addIcon.style.display = 'inline-block';
                        removeIcon.style.display = 'none';
                    }
                }
            }
        })
        .catch(error => {
            console.error('Cart Error:', error);
            showNotification(getMessage('connectionError'), 'error');
            if (button) {
                button.disabled = false;
                button.classList.remove('loading');
                const addIcon = button.querySelector('.cart-add-icon');
                const removeIcon = button.querySelector('.cart-remove-icon');
                if(addIcon && removeIcon) {
                    addIcon.style.display = 'inline-block';
                    removeIcon.style.display = 'none';
                }
            }
        });
    };

    window.removeFromCart = function(itemId, button = null) {
        if (!itemId) {
            console.error('Item ID is required for removeFromCart');
            return;
        }

        // Confirmation is better handled on pages like cart_view, not on product cards.
        // We will skip confirm() for direct card actions.

        if (button) {
            button.disabled = true;
            button.classList.add('loading');
        }

        // FIXED: Get the current language prefix from the URL, default to 'en' not 'ar'
        const langPrefix = getLangPrefix();
        fetch(`/${langPrefix}/cart/remove/`, { // Ensure this URL is correct
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
                showNotification(data.message || getMessage('removedFromCart'), 'success');
                updateAllCounts();

                // --- NEW: Update button state ---
                if (button) {
                    button.dataset.action = 'cart-add';
                    button.title = getMessage('addedToCart');
                    button.setAttribute('aria-label', getMessage('addedToCart'));
                    button.classList.remove('active');

                    const addIcon = button.querySelector('.cart-add-icon');
                    const removeIcon = button.querySelector('.cart-remove-icon');
                    if (addIcon) addIcon.style.display = 'inline-block';
                    if (removeIcon) removeIcon.style.display = 'none';

                    button.disabled = false;
                    button.classList.remove('loading');
                }
            } else {
                showNotification(data.message || getMessage('removeCartFailed'), 'error');
                if (button) {
                    button.disabled = false;
                    button.classList.remove('loading');
                }
            }
        })
        .catch(e => {
            console.error('Remove cart error:', e);
            showNotification(getMessage('connectionError'), 'error');
        });
    };

    // ========================================
    // WISHLIST FUNCTIONS (FIXED)
    // ========================================
    window.toggleWishlist = function(productId, button = null) {
        if (!productId) return console.error('Product ID is required');
        if (button) button.disabled = true;
        const formData = new FormData();
        formData.append('product_id', productId);
        formData.append('csrfmiddlewaretoken', getCSRFToken());

        // FIXED: Get the current language prefix from the URL, default to 'en' not 'ar'
        const langPrefix = getLangPrefix();
        fetch(`/${langPrefix}/api/add-to-wishlist/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
        .then(data => {
            if (data.success) {
                showNotification(data.message || getMessage('wishlistUpdated'), 'success');
                updateAllCounts();
                if (button) {
                    const icon = button.querySelector('.material-icons') || button.querySelector('i');
                    const card = button.closest('.product-card');
                    const isWishlistPage = card && card.dataset.context === 'wishlist';
                    const btnText = button.querySelector('.btn-text');

                    // Get translated labels
                    const addToWishlistLabel = isArabic() ? 'إضافة إلى المفضلة' : 'Add to Wishlist';
                    const removeFromWishlistLabel = isArabic() ? 'إزالة من المفضلة' : 'Remove from Wishlist';

                    if (data.in_wishlist || data.added) {
                        // Now in wishlist (added)
                        button.classList.add('active');
                        button.classList.add('in-wishlist');
                        button.setAttribute('aria-pressed', 'true');
                        button.title = removeFromWishlistLabel;
                        button.setAttribute('aria-label', removeFromWishlistLabel);
                        if (icon) {
                            icon.textContent = 'favorite';
                            icon.style.animation = 'heartBeat 0.5s ease';
                            setTimeout(() => { icon.style.animation = ''; }, 500);
                        }
                        // Keep textual label as "Wishlist" for consistency
                        if (btnText) {
                            btnText.textContent = btnText.textContent; // no-op, but keeps structure explicit
                        }
                    } else {
                        // Removed from wishlist
                        if (isWishlistPage) {
                            card.classList.add('removing');
                            setTimeout(() => {
                                card.remove();
                                if (!document.querySelectorAll('.product-card[data-context="wishlist"]').length)
                                    setTimeout(() => location.reload(), 500);
                            }, 300);
                        } else {
                            button.classList.remove('in-wishlist');
                            button.classList.remove('active');
                            button.setAttribute('aria-pressed', 'false');
                            button.title = addToWishlistLabel;
                            button.setAttribute('aria-label', addToWishlistLabel);
                            if (icon) {
                                icon.textContent = 'favorite_border';
                            }
                            if (btnText) {
                                btnText.textContent = btnText.textContent;
                            }
                        }
                    }
                }
            } else {
                showNotification(data.message || getMessage('wishlistFailed'), 'error');
            }
            if (button && !button.closest('.product-card.removing')) button.disabled = false;
        })
        .catch(e => {
            console.error('Wishlist Error:', e);
            showNotification(getMessage('connectionError'), 'error');
            if(button) button.disabled=false;
        });
    };

    // ========================================
    // UPDATE COUNTS (FIXED)
    // ========================================
    function updateAllCounts() {
        // FIXED: Get the current language prefix from the URL, default to 'en' not 'ar'
        const langPrefix = getLangPrefix();
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

    // Expose updateAllCounts globally
    window.updateAllCounts = updateAllCounts;

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
            showNotification(getMessage('errorOccurred'),'info');

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
                    if(productId) window.addToCart(productId, {button: btn});
                    break;
                case 'wishlist-toggle':
                    if(productId) window.toggleWishlist(productId, btn);
                    break;
                case 'cart-remove':
                    const itemId = btn.getAttribute('data-item-id');
                    if(itemId) window.removeFromCart(itemId, btn);
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
        style.textContent = `
        @keyframes heartBeat {0%,100%{transform:scale(1);}25%{transform:scale(1.3);}50%{transform:scale(1.1);}75%{transform:scale(1.25);}}
        @keyframes badgePulse {0%,100%{transform:scale(1);}50%{transform:scale(1.2);}}
        @keyframes cartBounce {0%,100%{transform:scale(1);}25%{transform:scale(1.3);}50%{transform:scale(1.1);}75%{transform:scale(1.25);}}
        .action-btn.loading{opacity:0.7;cursor:not-allowed;}
        .cart-notification{position:fixed;top:80px;right:20px;background:linear-gradient(135deg,var(--theme-bg,#fff) 0%,rgba(255,255,255,0.95) 100%);color:var(--theme-text,#000);padding:20px 28px;border-radius:16px;box-shadow:0 12px 40px rgba(0,0,0,0.15),0 6px 20px rgba(0,0,0,0.08);z-index:10000;transition:all 0.4s cubic-bezier(0.175,0.885,0.32,1.275);border:1px solid var(--theme-border,rgba(0,0,0,0.08));min-width:320px;max-width:420px;font-family:'IBM Plex Sans Arabic',sans-serif;backdrop-filter:blur(12px);}
        body.dark-mode .cart-notification{background:linear-gradient(135deg,rgba(40,40,40,0.95) 0%,rgba(60,60,60,0.9) 100%);border-color:rgba(255,255,255,0.1);box-shadow:0 12px 40px rgba(0,122,255,0.2),0 6px 20px rgba(0,0,0,0.3);}
        .notification-content{display:flex;align-items:center;gap:14px;font-weight:600;font-size:16px;line-height:1.4;}
        .notification-success{border-inline-start:4px solid #4CAF50;} .notification-success .material-icons{color:#4CAF50;font-size:22px;filter:drop-shadow(0 2px 4px rgba(76,175,80,0.3));}
        .notification-error{border-inline-start:4px solid #F44336;} .notification-error .material-icons{color:#F44336;font-size:22px;filter:drop-shadow(0 2px 4px rgba(244,67,54,0.3));}
        .notification-info{border-inline-start:4px solid var(--secondary-color,#A48111);} .notification-info .material-icons{color:var(--secondary-color,#A48111);font-size:22px;filter:drop-shadow(0 2px 4px rgba(164,129,17,0.3));}
        @media(max-width:480px){.cart-notification{right:-100%;left:10px;min-width:auto;max-width:calc(100%-20px);padding:16px 20px;}.cart-notification.show{right:auto;left:10px;}.notification-content{font-size:14px;}}
        `;
        document.head.appendChild(style);
    }
}
