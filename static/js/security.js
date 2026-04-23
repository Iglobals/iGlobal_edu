(function () {
    'use strict';

    // ── Styles ────────────────────────────────────────────────────────────────
    var s = document.createElement('style');
    s.textContent =
        '.ig-blurred { filter:blur(14px) !important; pointer-events:none !important; transition:filter 0s !important; }' +
        '* { user-select:none; -webkit-user-select:none; -webkit-touch-callout:none; }' +
        '@media print { body { display:none !important; } }';
    document.head.appendChild(s);

    // ── Overlay ───────────────────────────────────────────────────────────────
    var overlay = document.createElement('div');
    overlay.style.cssText =
        'position:fixed;inset:0;background:rgba(20,8,30,0.92);z-index:2147483647;' +
        'display:none;align-items:center;justify-content:center;' +
        'flex-direction:column;gap:1rem;font-family:Inter,sans-serif;';
    overlay.innerHTML =
        '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.5">' +
        '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>' +
        '<p style="color:white;font-size:1.05rem;font-weight:700;margin:0;letter-spacing:.02em;">Content Protected</p>' +
        '<p style="color:rgba(255,255,255,.5);font-size:.78rem;margin:0;">Screenshots and recording are not permitted.</p>';

    function target() {
        return document.querySelector('.reader-shell') || document.body;
    }

    var _blurTimer = null;

    function blurNow() {
        clearTimeout(_blurTimer);
        target().classList.add('ig-blurred');
        overlay.style.display = 'flex';
    }

    function unblurAfter(ms) {
        clearTimeout(_blurTimer);
        _blurTimer = setTimeout(function () {
            target().classList.remove('ig-blurred');
            overlay.style.display = 'none';
        }, ms || 700);
    }

    // ── 1. KEYBOARD ───────────────────────────────────────────────────────────
    // Blur IMMEDIATELY on keydown for any screenshot-capable key combo.
    // The blur happens before the OS captures the frame.
    var SCREENSHOT_KEYS = new Set(['PrintScreen', 'F12']);

    document.addEventListener('keydown', function (e) {
        var k = e.key;

        // --- Screenshot keys ---
        if (k === 'PrintScreen') {
            blurNow();
            navigator.clipboard && navigator.clipboard.writeText('').catch(function(){});
            unblurAfter(2500);
            return;
        }

        // Win+PrtSc, Win+Shift+S (Snipping Tool), Win+G (Game Bar)
        if (e.metaKey && (k === 'PrintScreen' || (e.shiftKey && k === 'S') || k === 'g' || k === 'G')) {
            e.preventDefault(); blurNow(); unblurAfter(2500); return;
        }

        // Mac: Cmd+Shift+3/4/5/6
        if (e.metaKey && e.shiftKey && ['3','4','5','6'].includes(k)) {
            e.preventDefault(); blurNow(); unblurAfter(2500); return;
        }

        // --- DevTools ---
        if (k === 'F12') { e.preventDefault(); return; }
        if (e.ctrlKey && e.shiftKey && ['i','I','j','J','c','C','k','K'].includes(k)) {
            e.preventDefault(); return;
        }
        if (e.ctrlKey && (k === 'u' || k === 'U')) { e.preventDefault(); return; }

        // --- Print / Save ---
        if (e.ctrlKey && (k === 'p' || k === 'P')) { e.preventDefault(); blurNow(); unblurAfter(1500); return; }
        if (e.ctrlKey && (k === 's' || k === 'S')) { e.preventDefault(); return; }

        // --- Ctrl+A (select all) ---
        if (e.ctrlKey && (k === 'a' || k === 'A')) { e.preventDefault(); return; }

        // --- Ctrl+C (copy) — block silently ---
        if (e.ctrlKey && (k === 'c' || k === 'C')) { e.preventDefault(); return; }
    }, true); // capture phase — fires before any other handler

    // ── 2. PRINT ──────────────────────────────────────────────────────────────
    window.addEventListener('beforeprint', function () { blurNow(); });
    window.addEventListener('afterprint',  function () { unblurAfter(300); });

    // ── 3. WINDOW FOCUS / BLUR ────────────────────────────────────────────────
    // Fires when Snipping Tool, Alt+Tab, or any external tool steals focus.
    // Blur is synchronous — no setTimeout — so the blurred frame is what
    // the OS captures if a screenshot is taken while focus is away.
    window.addEventListener('blur', function () { blurNow(); });
    window.addEventListener('focus', function () { unblurAfter(600); });

    // ── 4. VISIBILITY CHANGE (mobile + desktop screen record) ─────────────────
    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'hidden') { blurNow(); }
        else { unblurAfter(800); }
    });

    // ── 5. CONTEXT MENU + DRAG ────────────────────────────────────────────────
    document.addEventListener('contextmenu', function (e) { e.preventDefault(); }, true);
    document.addEventListener('dragstart',   function (e) { e.preventDefault(); }, true);

    // ── 6. DEVTOOLS SIZE HEURISTIC (desktop) ──────────────────────────────────
    // Detects docked devtools by measuring the gap between outer and inner window.
    // Also catches undocked devtools on a second monitor (outerWidth won't change
    // but the window will blur — caught above).
    var _devOpen = false;
    setInterval(function () {
        var wGap = window.outerWidth  - window.innerWidth;
        var hGap = window.outerHeight - window.innerHeight;
        // Allow ~100px for browser chrome (scrollbars, address bar)
        var open = wGap > 200 || hGap > 200;
        if (open && !_devOpen)  { _devOpen = true;  blurNow(); }
        if (!open && _devOpen)  { _devOpen = false; unblurAfter(300); }
    }, 800);

    // ── 7. POINTER EVENTS ON OVERLAY (prevent interaction while blurred) ──────
    overlay.addEventListener('click',      function (e) { e.stopPropagation(); });
    overlay.addEventListener('touchstart', function (e) { e.stopPropagation(); });

    // ── INIT ──────────────────────────────────────────────────────────────────
    function init() { document.body.appendChild(overlay); }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
