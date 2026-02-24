// Initialize Lucide icons
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    initScrollAnimations();
});

// Mobile Menu Toggle
function toggleMobileMenu() {
    const menu = document.getElementById('mobileMenu');
    menu.classList.toggle('hidden');
}

// Scroll Animations
function initScrollAnimations() {
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                observer.unobserve(entry.target); // Only animate once
            }
        });
    }, observerOptions);

    const revealElements = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');
    revealElements.forEach(el => observer.observe(el));
}

// Auth State Check (Simulation)
function checkAuthState() {
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    const authBtn = document.getElementById('authBtn');
    const libraryLink = document.getElementById('libraryLink');

    if (isLoggedIn) {
        if (authBtn) {
            authBtn.textContent = 'Logout';
            authBtn.onclick = logout;
            authBtn.classList.remove('btn-primary');
            authBtn.classList.add('btn-ash');
        }
        if (libraryLink) libraryLink.classList.remove('hidden');
    }
}

function logout() {
    localStorage.removeItem('isLoggedIn');
    window.location.href = 'index.html';
}

// Run auth check if needed (can be called in specific pages)
// checkAuthState();
