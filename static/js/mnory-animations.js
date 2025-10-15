/**
 * mnory-animations.js
 * GSAP-powered animations and enhanced Swiper functionality
 * 
 * Customization Guide:
 * - Adjust animation durations in GSAP timeline settings
 * - Modify easing functions for different animation feels
 * - Toggle animations via data-animations="false" on body element
 * - Customize Swiper settings in initHeroGallery function
 */

// Check if animations should be enabled
function animationsEnabled() {
    const body = document.body;
    const dataAttr = body.getAttribute('data-animations');
    const urlParams = new URLSearchParams(window.location.search);
    const queryParam = urlParams.get('animations');
    
    // Check prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    if (prefersReducedMotion) return false;
    if (queryParam === 'false') return false;
    if (dataAttr === 'false') return false;
    
    return true;
}

/**
 * Initialize GSAP page entrance animations
 */
function initPageEntranceAnimations() {
    if (!animationsEnabled()) return;
    
    // Check if GSAP is loaded
    if (typeof gsap === 'undefined') {
        console.warn('GSAP not loaded. Skipping animations.');
        return;
    }
    
    // Create master timeline for page entrance
    const tl = gsap.timeline({
        defaults: {
            ease: 'power2.out',
            duration: 0.8
        }
    });
    
    // Animate header/navbar
    const header = document.querySelector('header, nav.navbar');
    if (header) {
        gsap.set(header, { y: -100, opacity: 0 });
        tl.to(header, {
            y: 0,
            opacity: 1,
            duration: 0.6
        }, 0.1);
    }
    
    // Animate hero section
    const heroSection = document.querySelector('.hero-swiper, .intro');
    if (heroSection) {
        gsap.set(heroSection, { opacity: 0, scale: 0.95 });
        tl.to(heroSection, {
            opacity: 1,
            scale: 1,
            duration: 1
        }, 0.3);
    }
    
    // Animate section headers with stagger
    const sectionHeaders = document.querySelectorAll('.section-header h2');
    if (sectionHeaders.length > 0) {
        gsap.set(sectionHeaders, { x: -50, opacity: 0 });
        tl.to(sectionHeaders, {
            x: 0,
            opacity: 1,
            stagger: 0.2,
            duration: 0.6
        }, 0.5);
    }
    
    // Animate product/memory cards with stagger
    const productCards = document.querySelectorAll('.product-card, .swiper-slide');
    if (productCards.length > 0) {
        gsap.set(productCards, { y: 30, opacity: 0 });
        tl.to(productCards, {
            y: 0,
            opacity: 1,
            stagger: 0.1,
            duration: 0.6
        }, 0.7);
    }
}

/**
 * Initialize hover micro-interactions for cards
 */
function initCardHoverAnimations() {
    if (!animationsEnabled()) return;
    if (typeof gsap === 'undefined') return;
    
    const cards = document.querySelectorAll('.product-card');
    
    cards.forEach(card => {
        // Mouse enter animation
        card.addEventListener('mouseenter', function() {
            gsap.to(this, {
                scale: 1.03,
                y: -8,
                boxShadow: '0 12px 36px rgba(0, 0, 0, 0.25)',
                duration: 0.3,
                ease: 'power2.out'
            });
            
            // Animate image inside card
            const img = this.querySelector('img');
            if (img) {
                gsap.to(img, {
                    scale: 1.1,
                    duration: 0.5,
                    ease: 'power2.out'
                });
            }
        });
        
        // Mouse leave animation
        card.addEventListener('mouseleave', function() {
            gsap.to(this, {
                scale: 1,
                y: 0,
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                duration: 0.3,
                ease: 'power2.out'
            });
            
            const img = this.querySelector('img');
            if (img) {
                gsap.to(img, {
                    scale: 1,
                    duration: 0.5,
                    ease: 'power2.out'
                });
            }
        });
        
        // Click/press animation
        card.addEventListener('mousedown', function() {
            gsap.to(this, {
                scale: 0.98,
                duration: 0.1,
                ease: 'power2.out'
            });
        });
        
        card.addEventListener('mouseup', function() {
            gsap.to(this, {
                scale: 1.03,
                duration: 0.1,
                ease: 'power2.out'
            });
        });
    });
}

/**
 * Initialize GSAP ScrollTrigger for staggered reveals
 */
function initScrollTriggerAnimations() {
    if (!animationsEnabled()) return;
    if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') {
        console.warn('GSAP ScrollTrigger not loaded. Skipping scroll animations.');
        return;
    }
    
    gsap.registerPlugin(ScrollTrigger);
    
    // Animate sections on scroll
    const sections = document.querySelectorAll('.section');
    sections.forEach((section, index) => {
        // Skip first section (usually hero)
        if (index === 0) return;
        
        const elements = section.querySelectorAll('.product-card, .swiper-slide, .feature-card');
        
        if (elements.length > 0) {
            gsap.from(elements, {
                scrollTrigger: {
                    trigger: section,
                    start: 'top 80%',
                    end: 'bottom 20%',
                    toggleActions: 'play none none reverse'
                },
                y: 50,
                opacity: 0,
                stagger: 0.1,
                duration: 0.8,
                ease: 'power2.out'
            });
        }
    });
    
    // Parallax effect for hero images (subtle)
    const heroImages = document.querySelectorAll('.hero-swiper img, .intro');
    heroImages.forEach(img => {
        gsap.to(img, {
            scrollTrigger: {
                trigger: img,
                start: 'top top',
                end: 'bottom top',
                scrub: 1
            },
            y: '20%',
            ease: 'none'
        });
    });
}

/**
 * Initialize hero gallery Swiper with enhanced features
 */
function initHeroGallery() {
    // Check if Swiper is loaded
    if (typeof Swiper === 'undefined') {
        console.warn('Swiper not loaded. Skipping hero gallery initialization.');
        return;
    }
    
    const heroGalleryElement = document.querySelector('.hero-gallery-swiper');
    if (!heroGalleryElement) return;
    
    const heroGallerySwiper = new Swiper('.hero-gallery-swiper', {
        slidesPerView: 1,
        spaceBetween: 0,
        loop: true,
        autoplay: {
            delay: 4000,
            disableOnInteraction: false,
            pauseOnMouseEnter: true
        },
        effect: 'fade',
        fadeEffect: {
            crossFade: true
        },
        pagination: {
            el: '.hero-gallery-swiper .swiper-pagination',
            clickable: true,
            dynamicBullets: true
        },
        navigation: {
            nextEl: '.hero-gallery-swiper .swiper-button-next',
            prevEl: '.hero-gallery-swiper .swiper-button-prev'
        },
        keyboard: {
            enabled: true,
            onlyInViewport: true
        },
        a11y: {
            enabled: true,
            prevSlideMessage: 'Previous slide',
            nextSlideMessage: 'Next slide'
        },
        on: {
            init: function() {
                console.log('Hero gallery Swiper initialized');
            },
            slideChange: function() {
                // Add GSAP animation when slide changes
                if (animationsEnabled() && typeof gsap !== 'undefined') {
                    const activeSlide = this.slides[this.activeIndex];
                    const img = activeSlide.querySelector('img');
                    if (img) {
                        gsap.fromTo(img,
                            { scale: 1.2, opacity: 0 },
                            { scale: 1, opacity: 1, duration: 0.8, ease: 'power2.out' }
                        );
                    }
                }
            }
        }
    });
    
    return heroGallerySwiper;
}

/**
 * Enhanced Swiper for product carousels
 */
function enhanceProductSwipers() {
    if (typeof Swiper === 'undefined') return;
    
    // Find all product swipers and add enhanced features
    const productSwipers = document.querySelectorAll('.newarrivals-swiper, .featured-swiper, .bestseller-swiper, .onsale-swiper, .all-products-swiper');
    
    productSwipers.forEach(swiperElement => {
        // Add enhanced class for styling
        swiperElement.classList.add('mnory-swiper-enhanced');
    });
}

/**
 * Initialize button ripple effect
 */
function initButtonRipples() {
    if (!animationsEnabled()) return;
    
    const buttons = document.querySelectorAll('.btn');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });
}

/**
 * Lazy load images with fade-in effect
 */
function initLazyImageLoading() {
    const lazyImages = document.querySelectorAll('img[loading="lazy"]');
    
    lazyImages.forEach(img => {
        img.addEventListener('load', function() {
            this.classList.add('loaded');
        });
        
        // If already loaded
        if (img.complete) {
            img.classList.add('loaded');
        }
    });
}

/**
 * Add smooth scroll to anchor links
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#') return;
            
            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Initialize all animations and enhancements
 */
function initMnoryEnhancements() {
    console.log('Initializing Mnory Enhancements...');
    
    // Wait for DOM to be fully loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    function init() {
        // Core animations
        initPageEntranceAnimations();
        initCardHoverAnimations();
        initScrollTriggerAnimations();
        
        // Swiper enhancements
        initHeroGallery();
        enhanceProductSwipers();
        
        // Utility enhancements
        initButtonRipples();
        initLazyImageLoading();
        initSmoothScroll();
        
        console.log('Mnory Enhancements Initialized!');
        
        // Log animation status
        if (!animationsEnabled()) {
            console.log('Animations are disabled (prefers-reduced-motion or data-animations=false)');
        }
    }
}

// Auto-initialize
initMnoryEnhancements();

// Export functions for manual control if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initPageEntranceAnimations,
        initCardHoverAnimations,
        initScrollTriggerAnimations,
        initHeroGallery,
        enhanceProductSwipers,
        animationsEnabled
    };
}
