(function () {
    'use strict';

    // ── BLUR APPROACH ─────────────────────────────────────────────────────────
    // CSS filter:blur is applied synchronously before the next paint, so it
    // actually shows up in screenshots on both desktop and mobile.
    // An overlay on top handles the visual "content protected" message.

    var blurStyle = document.createElement('style');
    blurStyle.id = 'ig-blur-style';
    blurStyle.textContent = [
        '.ig-blurred { filter: blur(12px) !important; pointer-events: none !important; }',
        '@media print { body { display:none !important; } }'
    ].join('\n');
    document.head.appendChild(blurStyle);

    // Overlay — shown on top of blurred content
    var overlay = document.createElement('div');
    overlay.id = 'ig-overlay';
    overlay.style.cssText = [
        'position:fixed', 'inset:0',
        'background:rgba(26,10,36,0.82)',
        'z-index:2147483647',   // max z-index
        'display:none',
        'align-items:center', 'justify-content:center',
        'flex-direction:column', 'gap:1rem',
        'font-family:Inter,sans-serif'
    ].join(';');
    overlay.innerHTML =
        '<svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.5">' +
        '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>' +
        '<p style="color:white;font-size:1rem;font-weight:600;margin:0;">Content protected</p>';

    function getContentEl() {
        // Blur the reader shell if present, otherwise the whole body
        return document.querySelector('.reader-shell') || document.body;
    }

    function blurContent() {
        getContentEl().classList.add('ig-blurred');
        overlay.style.display = 'flex';
    }

    function unblurContent() {
        getContentEl().classList.remove('ig-blurred');
        overlay.style.display = 'none';
    }

    // ── VISIBILITY CHANGE (mobile screenshot / app switcher / screen record) ──
    // On iOS: taking a screenshot briefly triggers visibilitychange → hidden.
    // On Android: same for recent-apps gesture and screen recording start.
    // Applying blur BEFORE the hidden state means the blurred frame is what
    // gets captured.
    var blurTimeout;
    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'hidden') {
            blurContent();
        } else {
            // Small delay so the blur is visible for a moment on return
            clearTimeout(blurTimeout);
            blurTimeout = setTimeout(unblurContent, 800);
        }
    });

    // ── WINDOW BLUR (desktop: alt-tab, print dialog, screenshot tool focus) ──
    window.addEventListener('blur', function () {
        blurContent();
    });
    window.addEventListener('focus', function () {
        clearTimeout(blurTimeout);
        blurTimeout = setTimeout(unblurContent, 600);
    });

    // ── KEYBOARD SHORTCUTS (desktop) ─────────────────────────────────────────
    document.addEventListener('keydown', function (e) {
        // PrintScreen
        if (e.key === 'PrintScreen') {
            blurContent();
            navigator.clipboard && navigator.clipboard.writeText('').catch(function(){});
            clearTimeout(blurTimeout);
            blurTimeout = setTimeout(unblurContent, 2000);
        }
        // Mac screenshot: Cmd+Shift+3/4/5/6
        if (e.metaKey && e.shiftKey && ['3','4','5','6'].includes(e.key)) {
            e.preventDefault();
            blurContent();
            clearTimeout(blurTimeout);
            blurTimeout = setTimeout(unblurContent, 2000);
        }
        // Ctrl+P (print)
        if (e.ctrlKey && (e.key === 'p' || e.key === 'P')) { e.preventDefault(); }
        // Ctrl+S (save page)
        if (e.ctrlKey && (e.key === 's' || e.key === 'S')) { e.preventDefault(); }
        // F12 / DevTools shortcuts
        if (e.key === 'F12') { e.preventDefault(); }
        if (e.ctrlKey && e.shiftKey && ['i','I','j','J','c','C'].includes(e.key)) { e.preventDefault(); }
        if (e.ctrlKey && (e.key === 'u' || e.key === 'U')) { e.preventDefault(); }
    });

    // ── PRINT BLOCK ───────────────────────────────────────────────────────────
    window.addEventListener('beforeprint', function (e) {
        e.preventDefault();
        blurContent();
    });
    window.addEventListener('afterprint', function () {
        unblurContent();
    });

    // ── CONTEXT MENU + SELECTION + DRAG ──────────────────────────────────────
    document.addEventListener('contextmenu', function (e) { e.preventDefault(); });
    document.addEventListener('dragstart',   function (e) { e.preventDefault(); });

    // Disable text selection via CSS (doesn't block reading, just copy)
    var selStyle = document.createElement('style');
    selStyle.textContent = '* { user-select:none; -webkit-user-select:none; -webkit-touch-callout:none; }';
    document.head.appendChild(selStyle);

    // ── DEVTOOLS DETECTION (desktop) ─────────────────────────────────────────
    // Uses size diff heuristic — doesn't wipe the DOM, just blurs
    var devOpen = false;
    setInterval(function () {
        var wDiff = window.outerWidth  - window.innerWidth  > 160;
        var hDiff = window.outerHeight - window.innerHeight > 160;
        if ((wDiff || hDiff) && !devOpen) {
            devOpen = true;
            blurContent();
        }
        if (!wDiff && !hDiff && devOpen) {
            devOpen = false;
            unblurContent();
        }
    }, 1000);

    // ── INIT ──────────────────────────────────────────────────────────────────
    function init() {
        document.body.appendChild(overlay);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
