// Security script to prevent screenshots and printing

(function() {
    'use strict';

    // A. DYNAMIC CONTENT WATERMARK (Optional - adds timestamp overlay)
    function addWatermark() {
        const watermark = document.createElement('div');
        watermark.id = 'security-watermark';
        watermark.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-45deg);
            font-size: 72px;
            color: rgba(107, 45, 92, 0.05);
            pointer-events: none;
            z-index: 9999;
            user-select: none;
            font-weight: bold;
            white-space: nowrap;
        `;
        watermark.textContent = 'iGlobals © ' + new Date().toLocaleString();
        document.body.appendChild(watermark);
        
        // Update watermark every 2 seconds
        setInterval(() => {
            watermark.textContent = 'iGlobals © ' + new Date().toLocaleString();
        }, 2000);
    }

    // B. WINDOW FOCUS BLUR (Deters screen capture of background apps)
    window.addEventListener('blur', () => {
        document.body.style.filter = 'blur(10px)';
        document.body.style.pointerEvents = 'none';
    });
    
    window.addEventListener('focus', () => {
        document.body.style.filter = 'none';
        document.body.style.pointerEvents = 'auto';
    });

    // C. PRINT SCREEN / KEYBOARD LISTENER
    document.addEventListener('keydown', (e) => {
        // Detect PrintScreen
        if (e.key === "PrintScreen") {
            navigator.clipboard.writeText('');
            alert("Security Alert: Screen capture is not allowed on this page.");
        }
        
        // Detect Command+Shift+4 (Mac screenshot)
        if (e.metaKey && e.shiftKey && (e.key === '4' || e.key === '3')) {
            e.preventDefault();
            alert("Security Alert: Screen capture is not allowed on this page.");
            return false;
        }
        
        // Disable F12, Ctrl+Shift+I, Ctrl+Shift+J (DevTools)
        if (e.keyCode === 123 || 
            (e.ctrlKey && e.shiftKey && e.keyCode === 73) ||
            (e.ctrlKey && e.shiftKey && e.keyCode === 74)) {
            e.preventDefault();
            return false;
        }
        
        // Disable Ctrl+U (View Source)
        if (e.ctrlKey && e.keyCode === 85) {
            e.preventDefault();
            return false;
        }
        
        // Disable Ctrl+S (Save)
        if (e.ctrlKey && e.keyCode === 83) {
            e.preventDefault();
            alert("Saving content is not allowed.");
            return false;
        }
        
        // Disable Ctrl+P (Print)
        if (e.ctrlKey && e.keyCode === 80) {
            e.preventDefault();
            alert("Printing is not allowed on this page.");
            return false;
        }
    });

    // D. MOBILE SCREENSHOT DETECTION (Limited support)
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
            console.log('User navigated away or may have taken a screenshot.');
            // Log to server if needed
        }
    });

    // E. DISABLE RIGHT CLICK
    document.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        return false;
    });

    // F. DISABLE TEXT SELECTION
    document.body.style.userSelect = 'none';
    document.body.style.webkitUserSelect = 'none';
    document.body.style.mozUserSelect = 'none';
    document.body.style.msUserSelect = 'none';
    document.body.style.webkitTouchCallout = 'none';

    // G. DISABLE DRAG
    document.addEventListener('dragstart', (e) => {
        e.preventDefault();
        return false;
    });

    // H. DETECT DEVTOOLS OPENING
    let devtoolsOpen = false;
    const threshold = 160;
    
    setInterval(() => {
        if (window.outerWidth - window.innerWidth > threshold || 
            window.outerHeight - window.innerHeight > threshold) {
            if (!devtoolsOpen) {
                devtoolsOpen = true;
                document.body.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;"><h1>Developer tools detected. Please close to continue.</h1></div>';
            }
        }
    }, 1000);

    // I. PREVENT PRINT
    window.addEventListener('beforeprint', (e) => {
        e.preventDefault();
        alert("Printing is disabled for security reasons.");
        return false;
    });

    // J. CSS PRINT MEDIA OVERRIDE
    const style = document.createElement('style');
    style.textContent = `
        @media print {
            body { display: none !important; }
        }
    `;
    document.head.appendChild(style);

    // Initialize watermark
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', addWatermark);
    } else {
        addWatermark();
    }

})();
