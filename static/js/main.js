// ========================================
// PRODUCTS HEADER CONTROLS (Grid/List View, Per Page, Mobile Filters)
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    // View toggle handlers
    const viewGridBtn = document.querySelector('.view-btn.view-grid');
    const viewListBtn = document.querySelector('.view-btn.view-list');
    const productsGrid = document.getElementById('product-list-container');
    if (viewGridBtn && viewListBtn && productsGrid) {
        viewGridBtn.addEventListener('click', function() {
            viewGridBtn.classList.add('active');
            viewGridBtn.setAttribute('aria-pressed', 'true');
            viewListBtn.classList.remove('active');
            viewListBtn.setAttribute('aria-pressed', 'false');
            productsGrid.classList.remove('list-view');
            productsGrid.classList.add('grid-view');
        });
        viewListBtn.addEventListener('click', function() {
            viewListBtn.classList.add('active');
            viewListBtn.setAttribute('aria-pressed', 'true');
            viewGridBtn.classList.remove('active');
            viewGridBtn.setAttribute('aria-pressed', 'false');
            productsGrid.classList.remove('grid-view');
            productsGrid.classList.add('list-view');
        });
    }

    // Per page select handler
    const perPageSelect = document.getElementById('perPageSelect');
    if (perPageSelect) {
        perPageSelect.addEventListener('change', function() {
            const params = new URLSearchParams(window.location.search);
            params.set('per_page', perPageSelect.value);
            window.location.search = params.toString();
        });
    }

    // Mobile filters quick-open
    const openFiltersMobile = document.getElementById('openFiltersMobile');
    const filtersPanel = document.getElementById('filtersPanel');
    if (openFiltersMobile && filtersPanel) {
        openFiltersMobile.addEventListener('click', function() {
            filtersPanel.classList.add('expanded');
            const toggle = document.getElementById('toggleFilters');
            if (toggle) toggle.classList.add('expanded');
            const arrow = toggle ? toggle.querySelector('.toggle-arrow') : null;
            if (arrow) arrow.style.transform = 'rotate(180deg)';
            // focus first input inside filters
            const firstInput = filtersPanel.querySelector('select, input');
            if (firstInput) firstInput.focus();
        });
    }
});
// ========================================
// PRODUCTS HEADER CONTROLS (Grid/List View, Per Page, Mobile Filters)
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    // View toggle handlers
    const viewGridBtn = document.querySelector('.view-btn.view-grid');
    const viewListBtn = document.querySelector('.view-btn.view-list');
    const productsGrid = document.getElementById('product-list-container');
    if (viewGridBtn && viewListBtn && productsGrid) {
        viewGridBtn.addEventListener('click', function() {
            viewGridBtn.classList.add('active');
            viewGridBtn.setAttribute('aria-pressed', 'true');
            viewListBtn.classList.remove('active');
            viewListBtn.setAttribute('aria-pressed', 'false');
            productsGrid.classList.remove('list-view');
            productsGrid.classList.add('grid-view');
        });
        viewListBtn.addEventListener('click', function() {
            viewListBtn.classList.add('active');
            viewListBtn.setAttribute('aria-pressed', 'true');
            viewGridBtn.classList.remove('active');
            viewGridBtn.setAttribute('aria-pressed', 'false');
            productsGrid.classList.remove('grid-view');
            productsGrid.classList.add('list-view');
        });
    }

    // Per page select handler
    const perPageSelect = document.getElementById('perPageSelect');
    if (perPageSelect) {
        perPageSelect.addEventListener('change', function() {
            const params = new URLSearchParams(window.location.search);
            params.set('per_page', perPageSelect.value);
            window.location.search = params.toString();
        });
    }

    // Mobile filters quick-open
    const openFiltersMobile = document.getElementById('openFiltersMobile');
    const filtersPanel = document.getElementById('filtersPanel');
    if (openFiltersMobile && filtersPanel) {
        openFiltersMobile.addEventListener('click', function() {
            filtersPanel.classList.add('expanded');
            const toggle = document.getElementById('toggleFilters');
            if (toggle) toggle.classList.add('expanded');
            const arrow = toggle ? toggle.querySelector('.toggle-arrow') : null;
            if (arrow) arrow.style.transform = 'rotate(180deg)';
            // focus first input inside filters
            const firstInput = filtersPanel.querySelector('select, input');
            if (firstInput) firstInput.focus();
        });
    }
});
// static/js/main.js
// ========================================
// MNORY - Unified JavaScript Functionality
// All inline scripts consolidated here
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

// Language Helper Functions
function getLangPrefix() {
    return window.location.pathname.split('/')[1] || 'en';
}

function isArabic() {
    return getLangPrefix() === 'ar';
}

// Bilingual messages for main.js
const mainMessages = {
    selectColorSize: { ar: 'الرجاء اختيار اللون والحجم أولاً', en: 'Please select color and size first.' }
};

function getMainMessage(key) {
    const lang = isArabic() ? 'ar' : 'en';
    return mainMessages[key] ? mainMessages[key][lang] : key;
}

// Simple notification function (uses cart-wishlist.js if available)
function showMainNotification(message, type = 'warning') {
    if (typeof window.showNotification === 'function') {
        window.showNotification(message, type);
    } else {
        alert(message);
    }
}

// CSRF Token Helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');

// Debounce function for performance
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
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

        // Responsive breakpoints
        breakpoints: {
            480: {
                slidesPerView: 2,
                spaceBetween: 15,
            },
            768: {
                slidesPerView: 3,
                spaceBetween: 20,
            },
            1024: {
                slidesPerView: 3,
                spaceBetween: 25,
            },
            1200: {
                slidesPerView: 3,
                spaceBetween: 30,
            }
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
        // Check for saved theme preference or default to light mode
        const savedTheme = localStorage.getItem('mnory-theme');
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const shouldUseDark = savedTheme === 'dark' || (!savedTheme && systemPrefersDark);

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

    function hidePageLoader() {
        setTimeout(() => {
            const loader = document.getElementById('pageLoader');
            if (loader) {
                loader.style.opacity = '0';
                setTimeout(() => {
                    loader.style.display = 'none';
                }, 300);
            }
        }, 500);
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

    function initializeAllFeatures() {
        // Header & Navigation (counts now handled by cart-wishlist.js)
        initHeaderScrollBehavior();
        initSearchModal();
        initMobileSearch();

        // Theme System
        initDarkMode();

        // UI Enhancements
        initLazyLoading();
        initBackToTop();
        initAnimations();
        initFormValidation();
        initLanguageSwitcher();
        initCategorySearch();
        initCategoriesDrawer();
        initPagesDrawer();
        initMobileDrawerTheme();

        // Update theme icons on load
        updateAllThemeIcons();

        // Sync counts on load
        syncCounts();

        // Page State
        hidePageLoader();
        measurePerformance();
    }

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

    // Sync cart and wishlist counts across all locations
    function syncCounts() {
        // This function will be called by cart-wishlist.js
        const cartCount = document.getElementById('cart-count')?.textContent || '0';
        const wishlistCount = document.getElementById('wishlist-count')?.textContent || '0';

        // Update drawer counts
        const drawerCartCount = document.getElementById('drawer-cart-count');
        const drawerWishlistCount = document.getElementById('drawer-wishlist-count');
        const mobileCartCount = document.getElementById('mobile-cart-count');
        const mobileWishlistCount = document.getElementById('mobile-wishlist-count');

        if (drawerCartCount) drawerCartCount.textContent = cartCount;
        if (drawerWishlistCount) drawerWishlistCount.textContent = wishlistCount;
        if (mobileCartCount) mobileCartCount.textContent = cartCount;
        if (mobileWishlistCount) mobileWishlistCount.textContent = wishlistCount;
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
                if (window.showToast) window.showToast('Please select color and size first for Buy Now.', 'error');
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

        // Update global counts
        function updateGlobalCounts(nav_id = "nav1") {
            const baseUrl = window.location.origin;
            fetch(`${baseUrl}/get-cart-wishlist-counts/`, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(res => res.json())
            .then(data => {
                const cartCountEl = document.getElementById(`cart-count-${nav_id}`);
                const wishCountEl = document.getElementById(`wishlist-count-${nav_id}`);
                if (cartCountEl && data.cart_count !== undefined) {
                    cartCountEl.textContent = data.cart_count;
                }
                if (wishCountEl && data.wishlist_count !== undefined) {
                    wishCountEl.textContent = data.wishlist_count;
                }
            })
            .catch(error => {
                console.error("Failed to fetch cart/wishlist counts:", error);
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
                const productId = this.dataset.productId;
                const baseUrl = window.location.origin;
                fetch(`${baseUrl}/add-to-wishlist/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({ product_id: productId })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        updateGlobalCounts();
                        if (window.showToast) window.showToast('Added to Wishlist', 'success');
                    } else {
                        if (window.showToast) window.showToast(data.message || 'Action failed.', 'error');
                    }
                })
                .catch(() => {
                    if (window.showToast) window.showToast('An unexpected error occurred. Please try again.', 'error');
                });
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

    // Initialize Swiper for product detail
    if (document.querySelector('.product-detail-swiper')) {
        initializeProductSwiper();
    }

    function initializeProductSwiper() {
        const productThumbsSwiper = new Swiper('.product-detail-thumbs', {
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

        const productMainSwiper = new Swiper('.product-detail-swiper', {
            spaceBetween: 10,
            zoom: {
                maxRatio: 5,
                minRatio: 1,
                toggle: true,
            },
            navigation: {
                nextEl: '.swiper-button-next',
                prevEl: '.swiper-button-prev',
            },
            pagination: {
                el: '.swiper-pagination',
                clickable: true,
                dynamicBullets: true,
            },
            thumbs: {
                swiper: productThumbsSwiper,
            },
            keyboard: {
                enabled: true,
            },
            mousewheel: {
                invert: false,
            },
        });

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
                576: { slidesPerView: 2 },
                768: { slidesPerView: 3 },
                992: { slidesPerView: 4 },
            }
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

    // Check if Bootstrap is loaded before initializing
    if (typeof bootstrap !== 'undefined') {
        initializeAllFeatures();
    } else {
        setTimeout(() => {
            initializeAllFeatures();
        }, 100);
    }

});
