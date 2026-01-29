// ========================================
// FLOATING ACTION BUTTONS (FAB) MENU
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    const fabMenu = document.querySelector('.fab-menu');
    const fabMain = document.querySelector('.fab-main');
    const fabOptions = document.querySelector('.fab-options');
    const backToTopBtn = document.getElementById('backToTop');
    const chatbotToggle = document.getElementById('mnoryChatbotToggle');
    const compareFab = document.getElementById('compareFab');

    // Toggle FAB menu
    if (fabMain && fabMenu) {
        fabMain.addEventListener('click', function() {
            const isActive = fabMenu.classList.toggle('active');
            fabMain.setAttribute('aria-expanded', isActive ? 'true' : 'false');

            // Add rotation animation to icon
            if (isActive) {
                fabMain.classList.add('active');
            } else {
                fabMain.classList.remove('active');
            }
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!fabMenu.contains(event.target)) {
                fabMenu.classList.remove('active');
                fabMain.classList.remove('active');
                fabMain.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // Back to Top functionality
    if (backToTopBtn) {
        // Show/hide button based on scroll position
        function toggleBackToTop() {
            if (window.pageYOffset > 300) {
                backToTopBtn.style.display = 'flex';
            } else {
                backToTopBtn.style.display = 'none';
            }
        }

        window.addEventListener('scroll', toggleBackToTop);
        toggleBackToTop(); // Initial check

        backToTopBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // Chatbot Toggle functionality
    if (chatbotToggle) {
        chatbotToggle.addEventListener('click', function() {
            // Close FAB menu
            fabMenu.classList.remove('active');
            fabMain.classList.remove('active');
            fabMain.setAttribute('aria-expanded', 'false');

            // Show notification or open chatbot
            if (typeof showMainNotification === 'function') {
                showMainNotification('Chatbot feature coming soon!', 'info');
            } else if (typeof alertify !== 'undefined') {
                alertify.message('Chatbot feature coming soon!');
            } else {
                alert('Chatbot feature coming soon!');
            }

            // TODO: Implement actual chatbot widget
            // Example: document.getElementById('chatbotWidget').classList.add('active');
        });
    }


    // Compare button visibility (controlled by compare feature)
    if (compareFab) {
        // This button's visibility is controlled by the compare feature in main.js
        // Just ensure it works when visible
        compareFab.addEventListener('click', function() {
            // Close FAB menu
            fabMenu.classList.remove('active');
            fabMain.classList.remove('active');
            fabMain.setAttribute('aria-expanded', 'false');

            // Navigate to compare page or show compare modal
            // This functionality should be in your compare feature
            if (typeof window.showCompareModal === 'function') {
                window.showCompareModal();
            } else {
                window.location.href = '/compare/';
            }
        });
    }

    // Add smooth animations for all FAB items
    if (fabOptions) {
        const fabItems = fabOptions.querySelectorAll('.fab-option');
        fabItems.forEach((item, index) => {
            item.style.transitionDelay = `${(index + 1) * 0.05}s`;
        });
    }
});
