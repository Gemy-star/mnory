// static/js/main.js
// ========================================

// ========================================
// EARLY INITIALIZATION (Before DOM Ready)
// ========================================

// Replace 'no-js' class with 'js' immediately
document.documentElement.className = document.documentElement.className.replace('no-js', 'js');

// Early performance mark
if ('performance' in window && 'mark' in performance) {
    performance.mark('mnory-head-end');
    performance.mark('mnory-body-start');
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

// Simple notification function (uses cart-wishlist.js if available)
function showMainNotification(message, type = 'warning') {
    if (typeof window.showNotification === 'function') {
        window.showNotification(message, type);
    } else {
        alert(message);
    }
}

// Basic cookie helper (for CSRF token, etc.)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ========================================
// SWIPER INITIALIZATION FUNCTIONS
// ========================================

// Initialize Category Products Swiper
function initCategoryProductsSwiper() {
    const swiperContainer = document.querySelector('.category-products-swiper-container .swiper');
    if (!swiperContainer) return null;

    return new Swiper(swiperContainer, {
        slidesPerView: 2,
        spaceBetween: 15,
        loop: false,
        autoplay: false,
        centeredSlides: false,
        grabCursor: true,
        watchOverflow: true,

        // Navigation arrows
        navigation: {
            nextEl: '.category-swiper-next',
            prevEl: '.category-swiper-prev',
        },

        // Pagination dots
        pagination: {
            el: '.swiper-pagination',
            clickable: true,
            dynamicBullets: true,
        },

        // Responsive breakpoints: mobile -> 2 slides, desktop (>=768px) -> 4 slides
        breakpoints: {
            0:   { slidesPerView: 2, spaceBetween: 15 },
            768: { slidesPerView: 4, spaceBetween: 25 }
        },
        // Effects and animations
        on: {
            init: function() {
                // Add custom styling when swiper initializes
                this.el.classList.add('swiper-initialized');
            },
            slideChange: function() {
                // Optional: Add animations on slide change
                const activeSlide = this.slides[this.activeIndex];
                if (activeSlide) {
                    activeSlide.style.transform = 'scale(1)';
                }
            }
        }
    });
}

// Make function globally accessible
window.initCategoryProductsSwiper = initCategoryProductsSwiper;

// ========================================
// DOM READY - MAIN INITIALIZATION
// ========================================

document.addEventListener('DOMContentLoaded', function() {

    // Performance mark
    if ('performance' in window && 'mark' in performance) {
        performance.mark('mnory-dom-ready');
    }

    // Remove loading class
    document.body.classList.remove('loading');
    document.body.classList.add('loaded');

    // ========================================
    // MOBILE MENU DRAWER FUNCTIONALITY
    // ========================================

    const menuDrawer = document.getElementById('menuDrawer');
    const hamburgerBtn = document.getElementById('hamburgerMenuBtn');
    const drawerClose = document.getElementById('menuDrawerClose');
    const drawerOverlay = document.getElementById('menuDrawerOverlay');
    const drawerCategoriesToggle = document.getElementById('drawerCategoriesToggle');
    const drawerCategoriesSubmenu = document.getElementById('drawerCategoriesSubmenu');
    const drawerThemeToggle = document.getElementById('drawerThemeToggle');

    // Open drawer
    if (hamburgerBtn) {
        hamburgerBtn.addEventListener('click', function() {
            menuDrawer.classList.add('active');
            document.body.classList.add('drawer-open');

            // Add staggered animation to menu items
            const menuItems = menuDrawer.querySelectorAll('.drawer-menu-item, .drawer-user-info');
            menuItems.forEach((item, index) => {
                item.style.animation = 'none';
                setTimeout(() => {
                    item.style.animation = `slideInLeft 0.4s ease-out ${index * 0.05}s both`;
                }, 10);
            });

            // Counts are updated automatically by cart-wishlist.js
        });
    }

    // Close drawer function
    function closeDrawer() {
        menuDrawer.classList.remove('active');
        document.body.classList.remove('drawer-open');
    }

    // Close drawer button
    if (drawerClose) {
        drawerClose.addEventListener('click', closeDrawer);
    }

    // Close drawer on overlay click
    if (drawerOverlay) {
        drawerOverlay.addEventListener('click', closeDrawer);
    }

    // Close drawer on ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && menuDrawer.classList.contains('active')) {
            closeDrawer();
        }
    });

    // Categories submenu toggle
    if (drawerCategoriesToggle && drawerCategoriesSubmenu) {
        drawerCategoriesToggle.addEventListener('click', function() {
            drawerCategoriesToggle.classList.toggle('active');
            drawerCategoriesSubmenu.classList.toggle('active');
        });
    }

    // Theme toggle in drawer (desktop)
    if (drawerThemeToggle) {
        drawerThemeToggle.addEventListener('click', toggleTheme);
    }

    // Mobile drawer theme toggle
    const mobileDrawerThemeToggle = document.getElementById('mobileDrawerThemeToggle');
    if (mobileDrawerThemeToggle) {
        mobileDrawerThemeToggle.addEventListener('click', toggleTheme);
    }

    // Unified theme toggle function
    function toggleTheme() {
        const isDark = document.body.classList.contains('dark-mode');
        const htmlElement = document.documentElement;

        if (isDark) {
            // Switch to light mode
            document.body.classList.remove('dark-mode');
            htmlElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');

            // Update header theme toggle icons
            const headerLightIcon = document.querySelector('.theme-icon-light');
            const headerDarkIcon = document.querySelector('.theme-icon-dark');
            if (headerLightIcon) headerLightIcon.style.display = 'block';
            if (headerDarkIcon) headerDarkIcon.style.display = 'none';

            // Update mobile drawer theme toggle icons
            const mobileLightIcon = document.querySelector('.mobile-theme-icon-light');
            const mobileDarkIcon = document.querySelector('.mobile-theme-icon-dark');
            if (mobileLightIcon) mobileLightIcon.style.display = 'block';
            if (mobileDarkIcon) mobileDarkIcon.style.display = 'none';

            // Update drawer theme toggle icons (desktop)
            const drawerMoonIcon = document.querySelector('.drawer-theme-icon-moon');
            const drawerSunIcon = document.querySelector('.drawer-theme-icon-sun');
            if (drawerMoonIcon) drawerMoonIcon.style.display = 'block';
            if (drawerSunIcon) drawerSunIcon.style.display = 'none';

            // Update drawer theme text (desktop only)
            if (drawerThemeToggle) {
                const themeText = drawerThemeToggle.querySelector('.drawer-theme-text');
                if (themeText) themeText.textContent = document.documentElement.lang === 'ar' ? 'الوضع الداكن' : 'Dark Mode';
            }
        } else {
            // Switch to dark mode
            document.body.classList.add('dark-mode');
            htmlElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');

            // Update header theme toggle icons
            const headerLightIcon = document.querySelector('.theme-icon-light');
            const headerDarkIcon = document.querySelector('.theme-icon-dark');
            if (headerLightIcon) headerLightIcon.style.display = 'none';
            if (headerDarkIcon) headerDarkIcon.style.display = 'block';

            // Update mobile drawer theme toggle icons
            const mobileLightIcon = document.querySelector('.mobile-theme-icon-light');
            const mobileDarkIcon = document.querySelector('.mobile-theme-icon-dark');
            if (mobileLightIcon) mobileLightIcon.style.display = 'none';
            if (mobileDarkIcon) mobileDarkIcon.style.display = 'block';

            // Update drawer theme toggle icons (desktop)
            const drawerMoonIcon = document.querySelector('.drawer-theme-icon-moon');
            const drawerSunIcon = document.querySelector('.drawer-theme-icon-sun');
            if (drawerMoonIcon) drawerMoonIcon.style.display = 'none';
            if (drawerSunIcon) drawerSunIcon.style.display = 'block';

            // Update drawer theme text (desktop only)
            if (drawerThemeToggle) {
                const themeText = drawerThemeToggle.querySelector('.drawer-theme-text');
                if (themeText) themeText.textContent = document.documentElement.lang === 'ar' ? 'الوضع الفاتح' : 'Light Mode';
            }
        }
    }

    // Cart & Wishlist functionality is now handled by cart-wishlist.js module

    // Close drawer when clicking on navigation links
    const drawerLinks = menuDrawer ? menuDrawer.querySelectorAll('a:not(.drawer-categories-toggle)') : [];
    drawerLinks.forEach(link => {
        link.addEventListener('click', function() {
            // Add a small delay to allow navigation to start
            setTimeout(closeDrawer, 150);
        });
    });

    // ========================================
    // HEADER & NAVBAR FUNCTIONALITY
    // ========================================

    // Category Search Filter
    const categorySearchInput = document.getElementById('categorySearchInput');
    const categoryItems = document.querySelectorAll('#categoryGrid .category-item');

    if (categorySearchInput && categoryItems.length > 0) {
        categorySearchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            categoryItems.forEach(item => {
                const name = item.getAttribute('data-name');
                item.style.display = name && name.includes(query) ? '' : 'none';
            });
        });
    }

    // Cart/wishlist count updates are now handled by cart-wishlist.js module

    // Header Scroll Behavior
    function initHeaderScrollBehavior() {
        const navbar = document.getElementById('mainNavbar');
        const promoBanner = document.getElementById('promoBanner');
        const body = document.body;

        if (!navbar) return;

        const isHomeTransparentInitial = navbar.classList.contains('home-transparent');

        function adjustHeaderPositions() {
            const promoBannerHeight = promoBanner ? promoBanner.offsetHeight : 0;
            const scrollY = window.scrollY;

            if (scrollY > 10) {
                if (promoBanner) promoBanner.classList.add('hidden');
                if (isHomeTransparentInitial) {
                    navbar.classList.add('scrolled');
                    navbar.classList.remove('home-transparent');
                }
                navbar.style.top = `0px`;
            } else {
                if (promoBanner) promoBanner.classList.remove('hidden');
                if (isHomeTransparentInitial) {
                    navbar.classList.remove('scrolled');
                    navbar.classList.add('home-transparent');
                }
                navbar.style.top = `${promoBannerHeight}px`;
            }

            const totalFixedHeaderHeight = navbar.offsetHeight +
                (promoBanner && promoBanner.classList.contains('hidden') ? 0 : promoBannerHeight);
            body.style.paddingTop = `${totalFixedHeaderHeight}px`;
        }

        // Initial adjustment
        adjustHeaderPositions();

        // Listen to scroll and resize
        window.addEventListener('scroll', adjustHeaderPositions);
        window.addEventListener('resize', adjustHeaderPositions);
    }

    // Search Modal Functionality
    function initSearchModal() {
        const searchModalElement = document.getElementById('searchModal');
        if (!searchModalElement) return;

        const searchModal = new bootstrap.Modal(searchModalElement);
        const searchModalTrigger = document.getElementById('searchModalTrigger');
        const searchInputModal = document.getElementById('searchInputModal');
        const searchClearBtnModal = document.getElementById('searchClearBtnModal');

        if (searchModalTrigger) {
            searchModalTrigger.addEventListener('click', function() {
                searchModal.show();
                setTimeout(() => {
                    if (searchInputModal) searchInputModal.focus();
                }, 500);
            });
        }

        if (searchInputModal) {
            searchInputModal.addEventListener('input', function() {
                if (searchClearBtnModal) {
                    searchClearBtnModal.style.display = this.value.length > 0 ? 'block' : 'none';
                }
            });
        }

        if (searchClearBtnModal) {
            searchClearBtnModal.addEventListener('click', function() {
                if (searchInputModal) {
                    searchInputModal.value = '';
                    this.style.display = 'none';
                    searchInputModal.focus();
                }
            });
        }
    }

    // Mobile Search Toggle
    function initMobileSearch() {
        const mobileSearchToggle = document.getElementById('mobileSearchToggle');
        const searchContainerMobile = document.getElementById('searchContainerMobileToggled');

        if (mobileSearchToggle && searchContainerMobile) {
            mobileSearchToggle.addEventListener('click', function() {
                searchContainerMobile.classList.toggle('active');
                const mobileSearchInput = document.getElementById('mobileSearchInput');
                if (searchContainerMobile.classList.contains('active') && mobileSearchInput) {
                    setTimeout(() => mobileSearchInput.focus(), 300);
                }
            });
        }
    }

    // ========================================
    // THEME SYSTEM
    // ========================================

    // Update Theme Icon States (logo stays same in both themes)
    function updateThemeIcon(isDark) {
        const updateIcons = (toggle) => {
            if (!toggle) return;

            const lightIcon = toggle.querySelector('.theme-icon-light, .mobile-theme-icon-light, .drawer-theme-icon-moon');
            const darkIcon = toggle.querySelector('.theme-icon-dark, .mobile-theme-icon-dark, .drawer-theme-icon-sun');

            if (lightIcon && darkIcon) {
                if (isDark) {
                    // Dark mode - show sun/light_mode icon
                    lightIcon.style.display = 'none';
                    darkIcon.style.display = 'inline-block';
                } else {
                    // Light mode - show moon/dark_mode icon
                    lightIcon.style.display = 'inline-block';
                    darkIcon.style.display = 'none';
                }
            }
        };

        // Update all theme toggle buttons
        document.querySelectorAll('.theme-toggle-btn, #themeToggle, #themeToggleMobile, #mobileDrawerThemeToggle, #drawerThemeToggle').forEach(updateIcons);

        // Logo stays the same (logo.png) in both themes - no switching needed
    }

    // Dark Mode Initialization
    function initDarkMode() {
        // Check for saved theme preference or default to dark mode
        const savedTheme = localStorage.getItem('mnory-theme');
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        // Default to dark mode if no preference is saved
        const shouldUseDark = savedTheme === 'dark' || (!savedTheme);

        // Apply initial theme
        if (shouldUseDark) {
            document.body.classList.add('dark-mode');
            updateThemeIcon(true);
        } else {
            document.body.classList.remove('dark-mode');
            updateThemeIcon(false);
        }

        // Add event listeners to all theme toggle buttons
        const themeToggles = document.querySelectorAll('.theme-toggle-btn, #themeToggle, #themeToggleMobile');

        themeToggles.forEach(toggle => {
            if (toggle) {
                toggle.addEventListener('click', () => {
                    // Add smooth transition class
                    document.body.classList.add('theme-transition-active');

                    const isDark = document.body.classList.toggle('dark-mode');
                    localStorage.setItem('mnory-theme', isDark ? 'dark' : 'light');
                    updateThemeIcon(isDark);

                    // Remove transition class after animation completes
                    setTimeout(() => {
                        document.body.classList.remove('theme-transition-active');
                    }, 400);

                    // Dispatch custom event for other components to listen
                    window.dispatchEvent(new CustomEvent('themeChanged', {
                        detail: { isDark: isDark }
                    }));

                    // Add visual feedback to the button
                    toggle.style.transform = 'scale(0.95)';
                    setTimeout(() => {
                        toggle.style.transform = '';
                    }, 150);
                });
            }
        });

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('mnory-theme')) {
                const isDark = e.matches;
                document.body.classList.toggle('dark-mode', isDark);
                updateThemeIcon(isDark);
            }
        });
    }

    // ========================================
    // GLOBAL NOTIFICATION DROPDOWN
    // ========================================
    function initGlobalNotifications() {
        const notificationDropdown = document.getElementById('headerNotificationDropdown');
        const notificationBadge = document.getElementById('headerNotificationBadge');
        const markUrl = document.body && document.body.dataset
            ? document.body.dataset.markNotificationsUrl
            : null;

        if (!notificationDropdown || !markUrl) {
            return;
        }

        notificationDropdown.addEventListener('show.bs.dropdown', function () {
            // When dropdown is opened, mark notifications as read
            if (notificationBadge && notificationBadge.style.display !== 'none') {
                fetch(markUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken') || '',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({})
                })
                .then(response => response.json())
                .then(data => {
                    if (data && data.success) {
                        // Hide the badge visually
                        notificationBadge.style.display = 'none';
                    }
                }).catch(error => {
                    console.error("Error marking notifications as read:", error);
                });
            }
        });
    }

    // ========================================
    // IMAGE LAZY LOADING
    // ========================================

    function initLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('loading');
                        img.classList.add('loaded');
                        observer.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }

    // ========================================
    // BACK TO TOP BUTTON
    // ========================================

    function initBackToTop() {
        const backToTopBtn = document.getElementById('backToTop');
        if (!backToTopBtn) return;

        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                backToTopBtn.classList.add('visible');
            } else {
                backToTopBtn.classList.remove('visible');
            }
        });

        backToTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // ========================================
    // ANIMATION SYSTEM
    // ========================================

    function initAnimations() {
        if (!document.body.dataset.animations || document.body.dataset.animations === 'false') return;

        // Intersection Observer for animations
        if ('IntersectionObserver' in window) {
            const animationObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const element = entry.target;
                        const animationClass = element.dataset.animation || 'animate-fade-in-up';
                        element.classList.add(animationClass);
                        animationObserver.unobserve(element);
                    }
                });
            }, { threshold: 0.1 });

            document.querySelectorAll('[data-animation]').forEach(el => {
                animationObserver.observe(el);
            });
        }
    }

    // ========================================
    // FORM VALIDATION
    // ========================================

    function initFormValidation() {
        const forms = document.querySelectorAll('.needs-validation');
        forms.forEach(form => {
            form.addEventListener('submit', event => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();

                    // Focus first invalid field
                    const firstInvalid = form.querySelector(':invalid');
                    if (firstInvalid) {
                        firstInvalid.focus();
                        firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }
                form.classList.add('was-validated');
            }, false);
        });
    }

    // ========================================
    // LANGUAGE SWITCHER
    // ========================================

    function initLanguageSwitcher() {
        document.querySelectorAll('.language-dropdown select[name="language"]').forEach(selectElement => {
            selectElement.addEventListener('change', function() {
                const form = this.closest('form');
                if (form) form.submit();
            });
        });
    }

    // ========================================
    // PAGE LOADER
    // ========================================

    function initPageLoader() {
        const loader = document.getElementById('pageLoader');
        const body = document.body;

        if (!loader) return;

        const hideLoader = () => {
            if (!loader.classList.contains('hidden')) {
                loader.classList.add('hidden');
                body.classList.remove('loading');
                // Remove from DOM after animation to prevent interaction
                setTimeout(() => {
                    loader.style.display = 'none';
                }, 800); // Must match CSS transition duration
            }
        };

        // Promise that resolves on window load
        const windowLoad = new Promise(resolve => {
            window.addEventListener('load', resolve);
        });

        // Promise that resolves after a timeout
        const fallbackTimeout = new Promise(resolve => {
            setTimeout(resolve, 5000); // 5-second fallback
        });

        // Hide loader when the first of these events completes
        Promise.race([windowLoad, fallbackTimeout]).then(() => {
            hideLoader();
        });
    }

    // ========================================
    // PERFORMANCE MONITORING
    // ========================================

    function measurePerformance() {
        if ('performance' in window && 'measure' in performance) {
            try {
                performance.mark('mnory-scripts-start');
                performance.measure('mnory-initialization', 'mnory-body-start', 'mnory-dom-ready');
                const timing = performance.getEntriesByName('mnory-initialization')[0];
                console.log('Mnory initialization time:', timing.duration.toFixed(2) + 'ms');
            } catch (e) {
                // Ignore performance measurement errors
            }
        }
    }

    // ========================================
    // INITIALIZE ALL FEATURES
    // ========================================

    // Category Search Filter
    function initCategorySearch() {
        const searchInput = document.getElementById('categorySearchInput');
        if (searchInput) {
            searchInput.addEventListener('input', function(e) {
                const searchTerm = e.target.value.toLowerCase();
                const categoryItems = document.querySelectorAll('.category-item');

                categoryItems.forEach(item => {
                    const categoryName = item.getAttribute('data-name');
                    if (categoryName && categoryName.toLowerCase().includes(searchTerm)) {
                        item.style.display = 'block';
                    } else {
                        item.style.display = 'none';
                    }
                });
            });
        }
    }

    // Categories Drawer
    function initCategoriesDrawer() {
        const drawer = document.getElementById('categoriesDrawer');
        const drawerBtn = document.getElementById('categoriesDrawerBtn');
        const drawerClose = document.getElementById('categoriesDrawerClose');
        const drawerOverlay = document.getElementById('categoriesDrawerOverlay');

        if (!drawer || !drawerBtn) return;

        // Initialize tab functionality
        initCategoriesDrawerTabs(drawer);

        // Open drawer
        drawerBtn.addEventListener('click', function() {
            drawer.classList.add('active');
            document.body.style.overflow = 'hidden';
        });

        // Close drawer
        const closeDrawer = function() {
            drawer.classList.remove('active');
            document.body.style.overflow = '';
        };

        if (drawerClose) {
            drawerClose.addEventListener('click', closeDrawer);
        }

        if (drawerOverlay) {
            drawerOverlay.addEventListener('click', closeDrawer);
        }

        // Close on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && drawer.classList.contains('active')) {
                closeDrawer();
            }
        });

        // Close drawer when clicking on a category
        const categoryLinks = drawer.querySelectorAll('.category-card');
        categoryLinks.forEach(link => {
            link.addEventListener('click', function() {
                setTimeout(closeDrawer, 300);
            });
        });
    }

    // Categories Drawer Tab Functionality
    function initCategoriesDrawerTabs(drawer) {
        const tabs = drawer.querySelectorAll('.categories-tab');
        const tabPanes = drawer.querySelectorAll('.categories-tab-pane');
        const searchInput = drawer.querySelector('#categorySearchInput');
        const categoryItems = drawer.querySelectorAll('.category-item');

        // Tab switching
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const targetTab = this.getAttribute('data-tab');

                // Remove active class from all tabs and panes
                tabs.forEach(t => t.classList.remove('active'));
                tabPanes.forEach(pane => pane.classList.remove('active'));

                // Add active class to clicked tab
                this.classList.add('active');

                // Show corresponding tab pane
                const targetPane = drawer.querySelector(`#${targetTab}Tab`);
                if (targetPane) {
                    targetPane.classList.add('active');
                }

                // Clear search if switching away from search tab
                if (targetTab !== 'search' && searchInput) {
                    searchInput.value = '';
                    // Show all categories
                    categoryItems.forEach(item => {
                        item.style.display = '';
                    });
                }
            });
        });

        // Search functionality (only for search tab)
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                const searchTerm = this.value.toLowerCase().trim();

                categoryItems.forEach(item => {
                    const categoryName = item.getAttribute('data-name') || '';
                    if (categoryName.includes(searchTerm)) {
                        item.style.display = '';
                    } else {
                        item.style.display = 'none';
                    }
                });

                // Show/hide no results message
                const searchResults = drawer.querySelector('#searchResults');
                if (searchResults) {
                    const visibleItems = Array.from(categoryItems).filter(item =>
                        item.style.display !== 'none'
                    );

                    let noResultsMsg = searchResults.querySelector('.no-search-results');

                    if (visibleItems.length === 0 && searchTerm.length > 0) {
                        if (!noResultsMsg) {
                            noResultsMsg = document.createElement('div');
                            noResultsMsg.className = 'no-categories no-search-results';
                            noResultsMsg.innerHTML = `
                                <span class="material-icons">search_off</span>
                                <p>No categories found for "${searchTerm}"</p>
                            `;
                            searchResults.appendChild(noResultsMsg);
                        }
                        noResultsMsg.style.display = 'block';
                    } else if (noResultsMsg) {
                        noResultsMsg.style.display = 'none';
                    }
                }
            });
        }
    }

    // Pages Drawer (Desktop Menu)
    function initPagesDrawer() {
        const drawer = document.getElementById('pagesDrawer');
        const drawerBtn = document.getElementById('pagesDrawerBtn');
        const drawerClose = document.getElementById('pagesDrawerClose');
        const drawerOverlay = document.getElementById('pagesDrawerOverlay');

        if (!drawer || !drawerBtn) return;

        // Open drawer
        drawerBtn.addEventListener('click', function() {
            drawer.classList.add('active');
            document.body.style.overflow = 'hidden';
        });

        // Close drawer
        const closeDrawer = function() {
            drawer.classList.remove('active');
            document.body.style.overflow = '';
        };

        if (drawerClose) {
            drawerClose.addEventListener('click', closeDrawer);
        }

        if (drawerOverlay) {
            drawerOverlay.addEventListener('click', closeDrawer);
        }

        // Close on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && drawer.classList.contains('active')) {
                closeDrawer();
            }
        });

        // Close drawer when clicking on a menu item
        const menuLinks = drawer.querySelectorAll('.pages-menu-item');
        menuLinks.forEach(link => {
            link.addEventListener('click', function() {
                setTimeout(closeDrawer, 300);
            });
        });
    }

    // Mobile Drawer Theme Toggle
    function initMobileDrawerTheme() {
        const mobileThemeToggle = document.getElementById('mobileDrawerThemeToggle');

        if (mobileThemeToggle) {
            mobileThemeToggle.addEventListener('click', function() {
                const body = document.body;
                const isDarkMode = body.classList.contains('dark-mode');

                if (isDarkMode) {
                    body.classList.remove('dark-mode');
                    localStorage.setItem('theme', 'light');
                } else {
                    body.classList.add('dark-mode');
                    localStorage.setItem('theme', 'dark');
                }

                // Update all theme toggle icons
                updateAllThemeIcons();
            });
        }
    }

    // Update all theme icons across the page
    function updateAllThemeIcons() {
        const isDarkMode = document.body.classList.contains('dark-mode');

        // Update header theme icons
        document.querySelectorAll('.theme-icon-light, .theme-icon-dark').forEach(icon => {
            if (icon.classList.contains('theme-icon-light')) {
                icon.style.display = isDarkMode ? 'none' : 'block';
            } else {
                icon.style.display = isDarkMode ? 'block' : 'none';
            }
        });

        // Update mobile drawer theme icons
        document.querySelectorAll('.mobile-theme-icon-light, .mobile-theme-icon-dark').forEach(icon => {
            if (icon.classList.contains('mobile-theme-icon-light')) {
                icon.style.display = isDarkMode ? 'none' : 'block';
            } else {
                icon.style.display = isDarkMode ? 'block' : 'none';
            }
        });
    }

    // Product compare feature
    function initCompareFeature() {
        if (window.__mnoryCompareInitialized) {
            return;
        }
        window.__mnoryCompareInitialized = true;

        const compareItems = [];
        const maxItems = 3;

        const compareModalEl = document.getElementById('compareModal');
        let compareModal = null;
        if (compareModalEl && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            compareModal = new bootstrap.Modal(compareModalEl);
        }

        const compareTable = document.querySelector('.compare-table');
        const compareFab = document.getElementById('compareFab');
        const compareFabCount = document.getElementById('compareFabCount');
        const labels = compareTable ? {
            name: compareTable.dataset.labelName || 'Name',
            price: compareTable.dataset.labelPrice || 'Price',
            vendor: compareTable.dataset.labelVendor || 'Vendor',
            rating: compareTable.dataset.labelRating || 'Rating',
            colors: compareTable.dataset.labelColors || 'Colors',
            sizes: compareTable.dataset.labelSizes || 'Sizes',
            availability: compareTable.dataset.labelAvailability || 'Availability'
        } : {
            name: 'Name',
            price: 'Price',
            vendor: 'Vendor',
            rating: 'Rating',
            colors: 'Colors',
            sizes: 'Sizes',
            availability: 'Availability'
        };

        function collectProductData(card) {
            const id = card.dataset.productId || '';
            const nameEl = card.querySelector('.product-title-link, .product-name a, .product-name');
            const name = nameEl ? nameEl.textContent.trim() : '';

            const priceEl = card.querySelector('.product-price-wrapper .current-price') ||
                card.querySelector('.price-area .sale-price') ||
                card.querySelector('.price-area .regular-price');
            const price = priceEl ? priceEl.textContent.trim() : '';

            const vendorEl = card.querySelector('.vendor-name');
            const vendor = vendorEl ? vendorEl.textContent.trim() : '';

            const ratingTextEl = card.querySelector('.rating-text');
            const ratingCountEl = card.querySelector('.rating-count');
            const rating = ratingTextEl ? ratingTextEl.textContent.trim() : '';
            const ratingCount = ratingCountEl ? ratingCountEl.textContent.trim() : '';

            const colorDots = card.querySelectorAll('.color-swatches .color-dot');
            const colors = Array.from(colorDots)
                .map(el => el.getAttribute('title') || '')
                .filter(Boolean)
                .join(', ');

            const sizeTags = card.querySelectorAll('.size-tags .size-tag');
            const sizes = Array.from(sizeTags)
                .map(el => el.textContent.trim())
                .filter(Boolean)
                .join(', ');

            const statusEl = card.querySelector('.availability-status .status');
            const status = statusEl ? statusEl.textContent.trim() : '';

            const imgEl = card.querySelector('.product-img.main-img, .product-img');
            const image = imgEl ? imgEl.getAttribute('src') : '';

            const linkEl = card.querySelector('.product-link, .product-title-link');
            const url = linkEl ? linkEl.getAttribute('href') : '#';

            return {
                id,
                name,
                price,
                vendor,
                rating,
                ratingCount,
                colors,
                sizes,
                status,
                image,
                url
            };
        }

        function renderCompareModal() {
            const headerRow = document.getElementById('compareHeaderRow');
            const bodyRows = document.getElementById('compareBodyRows');
            const emptyState = document.getElementById('compareEmptyState');
            const tableWrapper = document.getElementById('compareTableWrapper');

            if (!headerRow || !bodyRows || !emptyState || !tableWrapper) {
                return;
            }

            if (compareItems.length === 0) {
                headerRow.innerHTML = '';
                bodyRows.innerHTML = '';
                tableWrapper.style.display = 'none';
                emptyState.style.display = 'block';
                if (compareFab) {
                    compareFab.style.display = 'none';
                }
                if (compareFabCount) {
                    compareFabCount.style.display = 'none';
                }
                return;
            }

            tableWrapper.style.display = 'block';
            emptyState.style.display = 'none';
            if (compareFab) {
                compareFab.style.display = 'flex';
            }
            if (compareFabCount) {
                compareFabCount.style.display = 'flex';
                compareFabCount.textContent = String(compareItems.length);
            }

            let headerHtml = '<th></th>';
            compareItems.forEach(item => {
                const imgHtml = item.image ? '<img src="' + item.image + '" alt="' + (item.name || '') + '" class="img-fluid" style="max-height: 80px;">' : '';
                headerHtml += '<th><div class="compare-product-heading">' +
                    imgHtml +
                    '<div class="mt-2">' + (item.name || '') + '</div>' +
                    '</div></th>';
            });
            headerRow.innerHTML = headerHtml;

            bodyRows.innerHTML = '';

            const rows = [
                { key: 'price', label: labels.price },
                { key: 'vendor', label: labels.vendor },
                { key: 'rating', label: labels.rating },
                { key: 'colors', label: labels.colors },
                { key: 'sizes', label: labels.sizes },
                { key: 'status', label: labels.availability }
            ];

            rows.forEach(row => {
                const tr = document.createElement('tr');
                const th = document.createElement('th');
                th.textContent = row.label;
                tr.appendChild(th);

                compareItems.forEach(item => {
                    const td = document.createElement('td');
                    let value = item[row.key] || '';
                    if (row.key === 'rating' && item.rating) {
                        const countText = item.ratingCount ? ' ' + item.ratingCount : '';
                        value = item.rating + countText;
                    }
                    td.textContent = value || '-';
                    tr.appendChild(td);
                });

                bodyRows.appendChild(tr);
            });
        }

        function openCompareModal() {
            if (compareModal && compareItems.length > 0) {
                compareModal.show();
            }
        }

        if (compareFab) {
            compareFab.addEventListener('click', function(e) {
                e.preventDefault();
                openCompareModal();
            });
        }

        function updateButtonState(card, active) {
            const btn = card.querySelector('.compare-btn, [data-action="compare-toggle"]');
            if (!btn) return;
            if (active) {
                btn.classList.add('in-compare');
                btn.setAttribute('aria-pressed', 'true');
            } else {
                btn.classList.remove('in-compare');
                btn.setAttribute('aria-pressed', 'false');
            }
        }

        function toggleCompare(card) {
            const data = collectProductData(card);
            if (!data.id) return;

            const existingIndex = compareItems.findIndex(item => item.id === data.id);
            if (existingIndex !== -1) {
                compareItems.splice(existingIndex, 1);
                updateButtonState(card, false);
                renderCompareModal();
                return;
            }

            if (compareItems.length >= maxItems) {
                if (typeof getMainMessage === 'function') {
                    showMainNotification(getMainMessage('compareLimit'), 'warning');
                } else {
                    showMainNotification('You can compare up to ' + maxItems + ' products.', 'warning');
                }
                return;
            }

            compareItems.push(data);
            updateButtonState(card, true);
            renderCompareModal();
        }

        document.addEventListener('click', function(e) {
            const btn = e.target.closest('.compare-btn, [data-action="compare-toggle"]');
            if (!btn) return;
            const card = btn.closest('.product-card');
            if (!card) return;
            e.preventDefault();
            e.stopPropagation();
            toggleCompare(card);
        });

        const clearBtn = document.getElementById('compareClearBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', function() {
                compareItems.splice(0, compareItems.length);
                document.querySelectorAll('.compare-btn.in-compare').forEach(btn => {
                    btn.classList.remove('in-compare');
                    btn.setAttribute('aria-pressed', 'false');
                });
                renderCompareModal();
            });
        }

        renderCompareModal();
    }

    // Sync cart and wishlist counts across all locations (FIXED)
    function syncCounts() {
        // Call the updateAllCounts function from cart-wishlist.js
        // This properly fetches counts from the API instead of just reading DOM values
        if (typeof window.updateAllCounts === 'function') {
            window.updateAllCounts();
            console.log('Syncing counts via cart-wishlist.js updateAllCounts');
        } else {
            console.warn('updateAllCounts not available yet, will retry...');
            // Retry after a short delay if cart-wishlist.js hasn't loaded yet
            setTimeout(() => {
                if (typeof window.updateAllCounts === 'function') {
                    window.updateAllCounts();
                }
            }, 500);
        }
    }

    // Make syncCounts globally accessible
    window.syncDrawerCounts = syncCounts;

    // ========================================
    // PRODUCT DETAIL PAGE FUNCTIONALITY
    // ========================================

    // Initialize product detail page if elements exist
    if (document.getElementById('add-to-cart-btn')) {
        initializeProductDetail();
    }

    function initializeProductDetail() {
        const increaseBtn = document.getElementById('increase-quantity');
        const decreaseBtn = document.getElementById('decrease-quantity');
        const quantityInput = document.getElementById('quantity-input');
        const quantityDisplay = document.getElementById('quantity-display');
        const wishlistBtn = document.getElementById('add-to-wishlist-btn');
        const addToCartBtn = document.getElementById('add-to-cart-btn');
        const buyNowForm = document.getElementById('buy-now-form');
        const buyNowColorInput = document.getElementById('buy-now-color-id');
        const buyNowSizeInput = document.getElementById('buy-now-size-id');
        const buyNowQuantityInput = document.getElementById('buy-now-quantity-input');
        const sizeButtonToggle = document.getElementById('size_btn');
        const sizeContainer = document.getElementById('size_container');
        let selectedColorId = null;
        let selectedSizeId = null;

        // Quantity controls with animation
        function updateDisplay(value) {
            if (quantityInput) quantityInput.value = value;
            if (quantityDisplay) {
                // Add animation
                quantityDisplay.style.animation = 'quantityChange 0.3s ease';
                quantityDisplay.textContent = value;

                // Remove animation after it completes
                setTimeout(() => {
                    quantityDisplay.style.animation = '';
                }, 300);
            }
            if (buyNowQuantityInput) buyNowQuantityInput.value = value;
        }

        increaseBtn?.addEventListener('click', () => {
            let current = parseInt(quantityInput.value) || 1;
            const max = parseInt(quantityInput.max) || 99;
            if (current < max) {
                updateDisplay(current + 1);
                // Add button feedback
                increaseBtn.style.transform = 'scale(0.9)';
                setTimeout(() => {
                    increaseBtn.style.transform = '';
                }, 150);
            } else {
                // Shake animation when max reached
                increaseBtn.style.animation = 'shake 0.5s ease';
                setTimeout(() => {
                    increaseBtn.style.animation = '';
                }, 500);
            }
        });

        decreaseBtn?.addEventListener('click', () => {
            let current = parseInt(quantityInput.value) || 1;
            const min = parseInt(quantityInput.min) || 1;
            if (current > min) {
                updateDisplay(current - 1);
                // Add button feedback
                decreaseBtn.style.transform = 'scale(0.9)';
                setTimeout(() => {
                    decreaseBtn.style.transform = '';
                }, 150);
            } else {
                // Shake animation when min reached
                decreaseBtn.style.animation = 'shake 0.5s ease';
                setTimeout(() => {
                    decreaseBtn.style.animation = '';
                }, 500);
            }
        });

        // Auto-select first color
        const firstColorBtn = document.querySelector('.color-select');
        if (firstColorBtn) {
            firstColorBtn.classList.add('active');
            selectedColorId = firstColorBtn.getAttribute('data-color-id');
            if (buyNowColorInput) buyNowColorInput.value = selectedColorId;
            updateSizes(selectedColorId);
        }

        // Color selection
        document.querySelectorAll('.color-select').forEach(button => {
            button.addEventListener('click', function () {
                document.querySelectorAll('.color-select').forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                selectedColorId = this.getAttribute('data-color-id');
                if (buyNowColorInput) buyNowColorInput.value = selectedColorId;
                updateSizes(selectedColorId);
            });
        });

        // Update sizes based on color
        function updateSizes(colorId) {
            const productId = document.querySelector('[data-product-id]')?.dataset?.productId;
            if (!productId) return;

            const baseUrl = window.location.origin;
            const langPrefix = document.documentElement.lang || 'en';
            fetch(`${baseUrl}/${langPrefix}/api/get-available-sizes/${productId}/?color_id=${colorId}`, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(res => res.json())
            .then(data => {
                const sizeButtonsContainer = document.querySelector('.size-buttons');
                if (!sizeButtonsContainer) return;

                sizeButtonsContainer.innerHTML = '';
                selectedSizeId = null;
                if (buyNowSizeInput) buyNowSizeInput.value = '';

                if (data.sizes && data.sizes.length > 0) {
                    data.sizes.forEach(size => {
                        const button = document.createElement('button');
                        button.type = 'button';
                        button.className = 'product-size-btn size-select';
                        button.dataset.sizeId = size.id;
                        button.dataset.sizeName = size.name;
                        button.innerHTML = `<span class="material-icons">straighten</span><span>${size.name}</span>`;
                        sizeButtonsContainer.appendChild(button);
                    });

                    // Attach event listeners to new size buttons
                    document.querySelectorAll('.size-select').forEach(button => {
                        button.addEventListener('click', function () {
                            document.querySelectorAll('.size-select').forEach(btn => btn.classList.remove('active'));
                            this.classList.add('active');
                            selectedSizeId = this.getAttribute('data-size-id');
                            if (buyNowSizeInput) buyNowSizeInput.value = selectedSizeId;
                        });
                    });

                    // Auto-select first size
                    const newFirstSizeBtn = document.querySelector('.size-select');
                    if (newFirstSizeBtn) {
                        newFirstSizeBtn.classList.add('active');
                        selectedSizeId = newFirstSizeBtn.getAttribute('data-size-id');
                        if (buyNowSizeInput) buyNowSizeInput.value = selectedSizeId;
                    }
                }
            })
            .catch(error => {
                console.error("Failed to fetch sizes:", error);
            });
        }

        // Wishlist button
        wishlistBtn?.addEventListener('click', function () {
            const productId = this.dataset.productId;
            if (typeof window.toggleWishlist === 'function') {
                window.toggleWishlist(productId, this);
            } else {
                console.error('toggleWishlist function not found. Make sure cart-wishlist.js is loaded.');
            }
        });

        // Add to cart button
        addToCartBtn?.addEventListener('click', () => {
            if (!selectedColorId || !selectedSizeId) {
                showMainNotification(getMainMessage('selectColorSize'), 'warning');
                return;
            }
            const productId = wishlistBtn?.dataset?.productId;
            const quantity = quantityInput?.value || 1;

            if (typeof window.addToCart === 'function') {
                window.addToCart(productId, {
                    button: addToCartBtn,
                    quantity: quantity,
                    colorId: selectedColorId,
                    sizeId: selectedSizeId
                });
            } else {
                console.error('addToCart function not found. Make sure cart-wishlist.js is loaded.');
            }
        });

        // Buy now form validation
        buyNowForm?.addEventListener('submit', function(e) {
            if (!selectedColorId || !selectedSizeId) {
                e.preventDefault();
                // Use the main notification function for consistency
                showMainNotification(getMainMessage('selectColorSize'), 'warning');
            } else {
                if (buyNowQuantityInput && quantityInput) {
                    buyNowQuantityInput.value = quantityInput.value;
                }
            }
        });

        // Size chart toggle
        if (sizeButtonToggle && sizeContainer) {
            sizeButtonToggle.addEventListener('click', function() {
                sizeContainer.classList.toggle('d-none');
            });
        }

        // Cart buttons (related products)
        document.querySelectorAll('.cart-btn').forEach(button => {
            button.addEventListener('click', function (e) {
                e.preventDefault();
                if (window.showToast) window.showToast('Please select a color and size from the product page.', 'primary');
            });
        });

        // Wishlist buttons (related products)
        document.querySelectorAll('.wishlist-btn').forEach(button => {
            button.addEventListener('click', function (e) {
                e.preventDefault();
                // Use the global toggleWishlist function from cart-wishlist.js
                const productId = this.dataset.productId;
                if (typeof window.toggleWishlist === 'function') {
                    window.toggleWishlist(productId, this);
                } else {
                    console.error('toggleWishlist function not found.');
                }
            });
        });
    }

    // Copy product link function
    window.copyProductLink = function() {
        const url = window.location.href;
        navigator.clipboard.writeText(url).then(() => {
            if (window.showToast) {
                window.showToast('Link copied to clipboard!', 'primary');
            }
        }).catch(err => {
            console.error('Failed to copy link:', err);
        });
    };

    // FIXED: Initialize product detail swiper with better loading check
    if (document.querySelector('.product-detail-swiper')) {
        // Wait for Swiper library to be loaded
        if (typeof Swiper !== 'undefined') {
            initializeProductSwiper();
        } else {
            // If Swiper not loaded yet, wait and retry
            let retryCount = 0;
            const checkSwiper = setInterval(() => {
                if (typeof Swiper !== 'undefined') {
                    clearInterval(checkSwiper);
                    initializeProductSwiper();
                } else if (retryCount++ > 10) {
                    clearInterval(checkSwiper);
                    console.error('Swiper library failed to load');
                }
            }, 200);
        }
    }

    function initializeProductSwiper() {
        // Wait for Swiper to be available
        if (typeof Swiper === 'undefined') {
            console.error('Swiper library not loaded');
            return;
        }

        // FIXED: Ensure all slides have proper zoom container structure
        document.querySelectorAll('.product-detail-swiper .swiper-slide').forEach(slide => {
            const img = slide.querySelector('img');
            const zoomContainer = slide.querySelector('.swiper-zoom-container');

            // If image exists but not inside zoom container, fix structure
            if (img && !zoomContainer) {
                const newZoomContainer = document.createElement('div');
                newZoomContainer.className = 'swiper-zoom-container';
                img.parentNode.insertBefore(newZoomContainer, img);
                newZoomContainer.appendChild(img);
                console.log('Fixed zoom container structure for slide');
            }
        });

        // Initialize thumbnails swiper first
        const thumbsElement = document.querySelector('.product-detail-thumbs');
        let productThumbsSwiper = null;

        if (thumbsElement) {
            productThumbsSwiper = new Swiper('.product-detail-thumbs', {
                spaceBetween: 10,
                slidesPerView: 4,
                freeMode: true,
                watchSlidesProgress: true,
                breakpoints: {
                    640: { slidesPerView: 5 },
                    768: { slidesPerView: 6 },
                    1024: { slidesPerView: 7 },
                }
            });
        }

        // Initialize main product swiper
        const mainSwiperConfig = {
            spaceBetween: 10,
            zoom: {
                maxRatio: 5,
                minRatio: 1,
                toggle: true,
            },
            navigation: {
                nextEl: '.product-detail-swiper .swiper-button-next',
                prevEl: '.product-detail-swiper .swiper-button-prev',
            },
            pagination: {
                el: '.product-detail-swiper .swiper-pagination',
                clickable: true,
                dynamicBullets: true,
            },
            keyboard: {
                enabled: true,
            },
            mousewheel: {
                invert: false,
            },
            on: {
                init: function() {
                    console.log('Product detail swiper initialized');
                },
            }
        };

        // Add thumbs only if thumbs swiper exists
        if (productThumbsSwiper) {
            mainSwiperConfig.thumbs = {
                swiper: productThumbsSwiper,
            };
        }

        const productMainSwiper = new Swiper('.product-detail-swiper', mainSwiperConfig);

        // Enhanced zoom functionality
        const zoomIndicator = document.querySelector('.zoom-indicator');

        productMainSwiper.on('zoomChange', (swiper, scale) => {
            if (zoomIndicator) {
                if (scale > 1) {
                    zoomIndicator.style.opacity = '0';
                    zoomIndicator.style.visibility = 'hidden';
                } else {
                    zoomIndicator.style.opacity = '1';
                    zoomIndicator.style.visibility = 'visible';
                }
            }
        });

        // Click to zoom
        setTimeout(() => {
            document.querySelectorAll('.product-detail-swiper .swiper-slide img').forEach((img) => {
                img.addEventListener('click', () => {
                    if (productMainSwiper.zoom) {
                        if (productMainSwiper.zoom.scale > 1) {
                            productMainSwiper.zoom.out();
                        } else {
                            productMainSwiper.zoom.in();
                        }
                    }
                });

                img.style.cursor = 'zoom-in';

                img.parentElement.addEventListener('mouseenter', () => {
                    if (productMainSwiper.zoom && productMainSwiper.zoom.scale > 1) {
                        img.style.cursor = 'zoom-out';
                    }
                });
            });

            // Double click to zoom
            document.querySelectorAll('.product-detail-swiper .swiper-slide').forEach((slide) => {
                slide.addEventListener('dblclick', () => {
                    if (productMainSwiper.zoom) {
                        if (productMainSwiper.zoom.scale > 1) {
                            productMainSwiper.zoom.out();
                        } else {
                            productMainSwiper.zoom.in();
                        }
                    }
                });
            });
        }, 100);
    }

    // Initialize related products swiper
    if (document.querySelector('.related_products-swiper')) {
        const relatedProductsSwiper = new Swiper('.related_products-swiper', {
            slidesPerView: 2,
            spaceBetween: 15,
            loop: true,
            navigation: {
                nextEl: '.related-next',
                prevEl: '.related-prev',
            },
               breakpoints: {
                    0:   { slidesPerView: 2, spaceBetween: 15 },
                    768: { slidesPerView: 4, spaceBetween: 25 }
                },
        });
    }

    // ========================================
    // CURRENCY SELECTOR
    // ========================================

    // Currency selection function
    window.setCurrency = function(currency) {
        // Set currency in session via GET request (redirect)
        window.location.href = `/set-currency/?currency=${currency}`;
    };

    // Call initialization functions
    initHeaderScrollBehavior();
    initSearchModal();
    initMobileSearch();
    initDarkMode();
    initLazyLoading();
    initBackToTop();
    initAnimations();
    initFormValidation();
    initLanguageSwitcher();
    initCategorySearch();
    initCategoriesDrawer();
    initPagesDrawer();
    initMobileDrawerTheme();
    updateAllThemeIcons();
    initCompareFeature();
    initGlobalNotifications();
    syncCounts();
    initPageLoader();
    measurePerformance();

});
// ========================================
// WISHLIST & CHECKOUT SWIPER INIT
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    // Wishlist Swiper
    if (document.querySelector('.wishlist-swiper')) {
        new Swiper('.wishlist-swiper', {
            slidesPerView: 2,
            spaceBetween: 15,
            breakpoints: {
                0: { slidesPerView: 2, spaceBetween: 15 },
                768: { slidesPerView: 4, spaceBetween: 25 }
            },
            navigation: {
                nextEl: '.swiper-button-next',
                prevEl: '.swiper-button-prev'
            },
            pagination: {
                el: '.swiper-pagination',
                clickable: true
            },
            loop: false,
            speed: 600,
            watchOverflow: true,
            autoplay: {
                delay: 5000,
                disableOnInteraction: false,
                pauseOnMouseEnter: true
            },
            effect: 'slide',
            touchRatio: 1,
            touchAngle: 45,
            simulateTouch: true,
            allowTouchMove: true,
            resistance: true,
            resistanceRatio: 0.85
        });
    }
    // Checkout Swiper
    if (document.querySelector('.checkout-swiper')) {
        new Swiper('.checkout-swiper', {
            slidesPerView: 2,
            spaceBetween: 15,
               breakpoints: {
                    // Mobile
                    0: { slidesPerView: 2, spaceBetween: 15 },
                    // Desktop
                    768: { slidesPerView: 4, spaceBetween: 25 }
                },
            navigation: {
                nextEl: '.swiper-button-next',
                prevEl: '.swiper-button-prev'
            },
            pagination: {
                el: '.swiper-pagination',
                clickable: true
            },
            loop: false,
            speed: 600,
            watchOverflow: true,
            autoplay: {
                delay: 5000,
                disableOnInteraction: false,
                pauseOnMouseEnter: true
            },
            effect: 'slide',
            touchRatio: 1,
            touchAngle: 45,
            simulateTouch: true,
            allowTouchMove: true,
            resistance: true,
            resistanceRatio: 0.85
        });
    }
});

// ========================================
// INTERNATIONALIZATION (i18n) MESSAGES
// ========================================
function getMainMessage(key) {
    const lang = document.documentElement.lang || 'en';
    const messages = {
        en: {
            selectColorSize: 'Please select a color and size',
            addedToCart: 'Added to cart successfully!',
            addedToWishlist: 'Added to wishlist!',
            removedFromWishlist: 'Removed from wishlist',
            loginRequired: 'Please login to continue',
            compareLimit: 'You can compare up to 3 products.',
            error: 'An error occurred. Please try again.'
        },
        ar: {
            selectColorSize: 'الرجاء اختيار اللون والمقاس',
            addedToCart: 'تمت الإضافة إلى السلة بنجاح!',
            addedToWishlist: 'تمت الإضافة إلى المفضلة!',
            removedFromWishlist: 'تمت الإزالة من المفضلة',
            loginRequired: 'الرجاء تسجيل الدخول للمتابعة',
            compareLimit: 'يمكنك مقارنة ما يصل إلى 3 منتجات.',
            error: 'حدث خطأ. يرجى المحاولة مرة أخرى.'
        }
    };
    return messages[lang]?.[key] || messages.en[key] || key;
}
