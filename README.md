# MNORY - Modern E-Commerce Platform

A Django-based e-commerce platform with modern frontend enhancements.

## Frontend Enhancements

### GSAP + Swiper Integration

This application features modern UI enhancements powered by GSAP (GreenSock Animation Platform) and Swiper.js for a polished, interactive user experience.

#### Features

- **Smooth Page Entrance Animations**: Elements fade and slide into view when the page loads
- **Hover Micro-interactions**: Product cards respond with subtle animations on hover and click
- **Scroll-triggered Animations**: Content reveals progressively as users scroll
- **Enhanced Swiper Carousels**: Auto-playing galleries with custom navigation and pagination
- **Glassmorphism Effects**: Modern, translucent card designs
- **Responsive Design**: Optimized for all screen sizes
- **Accessibility**: Respects `prefers-reduced-motion` settings

#### New Files Added

- `static/css/mnory-enhanced.css` - Enhanced styling with CSS variables and modern effects
- `static/js/mnory-animations.js` - GSAP animations and Swiper initialization

#### Customization

##### Disabling Animations

Animations can be disabled in multiple ways:

1. **URL Parameter**: Add `?animations=false` to any URL
   ```
   https://yoursite.com/?animations=false
   ```

2. **Body Attribute**: Set `data-animations="false"` on the body tag in `templates/base.html`
   ```html
   <body data-animations="false">
   ```

3. **System Preference**: Animations automatically disable if the user has enabled "prefers-reduced-motion" in their system settings

##### Customizing Colors

Edit the CSS variables in `static/css/mnory-enhanced.css`:

```css
:root {
    --primary-color: #000000;        /* Main brand color */
    --secondary-color: #e0e0e0;      /* Background/secondary color */
    --accent-color: #007aff;         /* Accent/highlight color */
    /* ... more variables */
}
```

##### Customizing Animation Durations

Adjust timing in `static/css/mnory-enhanced.css`:

```css
:root {
    --transition-fast: 0.2s;    /* Quick interactions */
    --transition-normal: 0.3s;  /* Default transitions */
    --transition-slow: 0.5s;    /* Slower, more dramatic effects */
}
```

Or modify GSAP animation durations in `static/js/mnory-animations.js`:

```javascript
// Example: Change page entrance duration
const tl = gsap.timeline({
    defaults: {
        ease: 'power2.out',
        duration: 0.8  // Change this value
    }
});
```

##### Customizing Swiper Settings

Edit the Swiper configuration in `static/js/mnory-animations.js`:

```javascript
function initHeroGallery() {
    const heroGallerySwiper = new Swiper('.hero-gallery-swiper', {
        autoplay: {
            delay: 4000,  // Change autoplay delay (in milliseconds)
            // ... more settings
        },
        effect: 'fade',  // Try 'slide', 'cube', 'coverflow', 'flip'
        // ... more settings
    });
}
```

#### CDN Dependencies

The following libraries are loaded via CDN:

- **GSAP 3.12.5**: https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js
- **GSAP ScrollTrigger**: https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js
- **Swiper 11**: https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js

#### Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Progressive enhancement ensures basic functionality without JavaScript
- Graceful degradation for older browsers

#### Performance Considerations

- Images use lazy loading for better initial page load
- Animations respect system performance settings
- CSS transitions are hardware-accelerated where possible
- Swiper instances are efficiently initialized only once

#### Troubleshooting

**Animations not working?**
1. Check browser console for JavaScript errors
2. Verify GSAP and Swiper CDN links are loading
3. Ensure `data-animations="true"` on body tag
4. Check that you don't have `?animations=false` in the URL

**Performance issues?**
1. Disable animations temporarily with `?animations=false`
2. Reduce the number of animated elements on a single page
3. Increase animation durations for smoother effects on slower devices

## Development

### Requirements

See `Pipfile` for Python dependencies.

### Setup

1. Install dependencies:
   ```bash
   pipenv install
   ```

2. Run migrations:
   ```bash
   python manage.py migrate
   ```

3. Run development server:
   ```bash
   python manage.py runserver
   ```

4. Visit http://localhost:8000 to see the enhanced UI in action

## License

[Your License Here]

## Credits

- Animations powered by [GSAP](https://greensock.com/gsap/)
- Carousels powered by [Swiper.js](https://swiperjs.com/)
