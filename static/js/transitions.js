// Page transition animations
document.addEventListener('DOMContentLoaded', function() {
    // Add fade-in animation to all pages
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.classList.add('fade-in');
    }
    
    // Animate elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);
    
    // Observe elements with animation classes
    document.querySelectorAll('.fade-in-up, .slide-in-left, .slide-in-right, .scale-in')
        .forEach(el => observer.observe(el));
    
    // Stagger animation for cards
    const cards = document.querySelectorAll('.property-card');
    cards.forEach((card, index) => {
        card.classList.add('stagger-item');
        setTimeout(() => {
            card.classList.add('animated');
        }, index * 100);
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Loading bar for page transitions
    const createLoadingBar = () => {
        const loadingBar = document.createElement('div');
        loadingBar.className = 'loading-bar';
        document.body.appendChild(loadingBar);
        
        setTimeout(() => {
            loadingBar.style.transition = 'transform 0.3s ease';
            loadingBar.style.transform = 'translateX(0)';
            
            setTimeout(() => {
                loadingBar.style.transform = 'translateX(100%)';
                setTimeout(() => loadingBar.remove(), 300);
            }, 300);
        }, 10);
    };
    
    // Handle link clicks for SPA-like transitions
    document.querySelectorAll('a:not([href^="#"]):not([target="_blank"])').forEach(link => {
        link.addEventListener('click', function(e) {
            if (this.href && this.href.includes(window.location.hostname)) {
                e.preventDefault();
                createLoadingBar();
                
                setTimeout(() => {
                    window.location.href = this.href;
                }, 300);
            }
        });
    });
    
    // Image gallery animation
    const galleryImages = document.querySelectorAll('.thumbnail');
    const mainImage = document.querySelector('.gallery-main');
    
    if (galleryImages.length && mainImage) {
        galleryImages.forEach(img => {
            img.addEventListener('click', function() {
                // Remove active class from all thumbnails
                galleryImages.forEach(i => i.classList.remove('active'));
                
                // Add active class to clicked thumbnail
                this.classList.add('active');
                
                // Fade out main image
                mainImage.style.opacity = '0';
                
                // Change main image after fade
                setTimeout(() => {
                    mainImage.src = this.dataset.large || this.src;
                    
                    // Fade in new image
                    setTimeout(() => {
                        mainImage.style.opacity = '1';
                    }, 50);
                }, 300);
            });
        });
    }
    
    // Form submission animations
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="loading"></span> Отправка...';
                submitBtn.disabled = true;
            }
        });
    });
    
    // Add ripple effect to buttons
    const buttons = document.querySelectorAll('.btn-primary, .btn-secondary');
    buttons.forEach(button => {
        button.classList.add('btn-ripple');
    });
    
    // Parallax effect for hero section
    const heroSection = document.querySelector('.hero');
    if (heroSection) {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.5;
            heroSection.style.transform = `translate3d(0, ${rate}px, 0)`;
        });
    }
});
