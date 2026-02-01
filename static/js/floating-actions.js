// ========================================
// FLOATING ACTION BUTTONS (FAB)
// Modern vertical stack design
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    const backToTopBtn = document.getElementById('backToTop');
    const chatbotToggle = document.getElementById('mnoryChatbotToggle');
    const compareFab = document.getElementById('compareFab');
    const whatsappBtn = document.getElementById('whatsappBtn');

    // ========================================
    // BACK TO TOP FUNCTIONALITY
    // ========================================

    if (backToTopBtn) {
        // Show/hide button based on scroll position
        function toggleBackToTop() {
            if (window.pageYOffset > 300) {
                backToTopBtn.style.display = 'flex';
                // Animate in
                setTimeout(() => {
                    backToTopBtn.style.opacity = '1';
                    backToTopBtn.style.transform = 'translateX(0)';
                }, 10);
            } else {
                backToTopBtn.style.opacity = '0';
                backToTopBtn.style.transform = 'translateX(100px)';
                setTimeout(() => {
                    backToTopBtn.style.display = 'none';
                }, 300);
            }
        }

        // Set initial hidden state
        backToTopBtn.style.opacity = '0';
        backToTopBtn.style.transform = 'translateX(100px)';
        backToTopBtn.style.transition = 'opacity 0.3s ease, transform 0.3s ease';

        window.addEventListener('scroll', toggleBackToTop);
        toggleBackToTop(); // Initial check

        // Scroll to top on click
        backToTopBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });

            // Add click animation
            this.style.transform = 'translateX(-8px) scale(1.05)';
            setTimeout(() => {
                if (window.pageYOffset > 300) {
                    this.style.transform = 'translateX(-8px) scale(1.1)';
                }
            }, 150);
        });
    }

    // ========================================
    // CHATBOT TOGGLE FUNCTIONALITY
    // ========================================

    const chatbotWidget = document.querySelector('.chatbot-widget');
    const chatbotClose = document.querySelector('.chatbot-close');
    const chatbotInput = document.getElementById('chatbotInput');
    const chatbotSend = document.getElementById('chatbotSend');
    const chatbotMessages = document.getElementById('chatbotMessages');
    const chatbotTyping = document.getElementById('chatbotTyping');

    if (chatbotToggle && chatbotWidget) {
        chatbotToggle.addEventListener('click', function() {
            chatbotWidget.classList.add('active');
            // Hide the chatbot toggle button
            this.style.opacity = '0';
            this.style.pointerEvents = 'none';
            this.style.transform = 'translateX(-8px) scale(0.8)';

            setTimeout(() => {
                if (chatbotInput) {
                    chatbotInput.focus();
                }
            }, 300);
        });
    }

    if (chatbotClose && chatbotWidget) {
        chatbotClose.addEventListener('click', function() {
            chatbotWidget.classList.remove('active');
            // Show the chatbot toggle button again
            if (chatbotToggle) {
                chatbotToggle.style.opacity = '1';
                chatbotToggle.style.pointerEvents = 'all';
                chatbotToggle.style.transform = '';
            }
        });
    }

    // Send message function
    function sendChatbotMessage() {
        if (!chatbotInput || !chatbotMessages) return;

        const question = chatbotInput.value.trim();
        if (!question) return;

        // Add user message
        const userMessage = document.createElement('div');
        userMessage.className = 'chatbot-message user-message';
        userMessage.innerHTML = `
            <div class="message-content">
                <p>${escapeHtml(question)}</p>
                <div class="message-time">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
            </div>
        `;
        chatbotMessages.appendChild(userMessage);
        chatbotInput.value = '';

        // Scroll to bottom
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;

        // Show typing indicator
        if (chatbotTyping) {
            chatbotTyping.style.display = 'flex';
        }

        // Get language code from body data attribute
        const langCode = document.body.dataset.languageCode || 'en';

        // Send to API
        fetch(`/${langCode}/api/chatbot/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ question: question })
        })
        .then(response => response.json())
        .then(data => {
            // Hide typing indicator
            if (chatbotTyping) {
                chatbotTyping.style.display = 'none';
            }

            // Add bot response
            const botMessage = document.createElement('div');
            botMessage.className = 'chatbot-message bot-message';
            botMessage.innerHTML = `
                <div class="message-avatar">
                    <span class="material-icons">smart_toy</span>
                </div>
                <div class="message-content">
                    <p>${escapeHtml(data.answer || data.error || 'Sorry, I could not understand.')}</p>
                    <div class="message-time">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
                </div>
            `;
            chatbotMessages.appendChild(botMessage);

            // Scroll to bottom
            chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
        })
        .catch(error => {
            // Hide typing indicator
            if (chatbotTyping) {
                chatbotTyping.style.display = 'none';
            }

            console.error('Chatbot error:', error);
            const errorMessage = document.createElement('div');
            errorMessage.className = 'chatbot-message bot-message';
            errorMessage.innerHTML = `
                <div class="message-avatar">
                    <span class="material-icons">smart_toy</span>
                </div>
                <div class="message-content">
                    <p>Sorry, something went wrong. Please try again.</p>
                    <div class="message-time">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
                </div>
            `;
            chatbotMessages.appendChild(errorMessage);
            chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
        });
    }

    // Helper function to escape HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Helper function to get cookie
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

    // Send button click
    if (chatbotSend) {
        chatbotSend.addEventListener('click', sendChatbotMessage);
    }

    // Enter key to send
    if (chatbotInput) {
        chatbotInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChatbotMessage();
            }
        });
    }

    // ========================================
    // COMPARE BUTTON FUNCTIONALITY
    // ========================================

    if (compareFab) {
        // Visibility is controlled by compare feature in main.js
        compareFab.addEventListener('click', function() {
            // Open compare modal if function exists
            if (typeof window.openCompareModal === 'function') {
                window.openCompareModal();
            } else {
                // Fallback to compare page
                const langPrefix = document.documentElement.lang || 'en';
                window.location.href = `/${langPrefix}/compare/`;
            }

            // Add click feedback
            this.style.transform = 'translateX(-8px) scale(1.05)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    }

    // ========================================
    // WHATSAPP BUTTON ENHANCEMENT
    // ========================================

    if (whatsappBtn) {
        // Add click tracking or analytics if needed
        whatsappBtn.addEventListener('click', function() {
            // Add click feedback
            this.style.transform = 'translateX(-8px) scale(1.05)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);

            // Optional: Track WhatsApp click
            if (typeof gtag !== 'undefined') {
                gtag('event', 'click', {
                    'event_category': 'engagement',
                    'event_label': 'whatsapp_button'
                });
            }
        });
    }

    // ========================================
    // ACCESSIBILITY ENHANCEMENTS
    // ========================================

    // Add keyboard support for all FAB buttons
    const fabButtons = document.querySelectorAll('.fab-option');
    fabButtons.forEach(button => {
        button.addEventListener('keydown', function(e) {
            // Enter or Space to activate
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    });

    // ========================================
    // SCROLL PERFORMANCE OPTIMIZATION
    // ========================================

    // Throttle scroll events for better performance
    let scrollTimeout;
    let lastScrollY = window.pageYOffset;

    window.addEventListener('scroll', function() {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            const currentScrollY = window.pageYOffset;

            // Add/remove shadow based on scroll direction
            const fabMenu = document.querySelector('.fab-menu');
            if (fabMenu) {
                if (currentScrollY > lastScrollY && currentScrollY > 100) {
                    // Scrolling down
                    fabMenu.style.opacity = '0.8';
                } else {
                    // Scrolling up or at top
                    fabMenu.style.opacity = '1';
                }
            }

            lastScrollY = currentScrollY;
        }, 100);
    });

    // ========================================
    // INITIALIZE
    // ========================================

    console.log('Floating Action Buttons initialized');
});
