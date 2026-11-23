const CACHE_NAME = 'iglobals-cache-v1';

const PRECACHE_URLS = [
    '/static/logo.png',
    '/static/manifest.json'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_URLS))
    );
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(name => {
                    if (name !== CACHE_NAME) {
                        return caches.delete(name);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // Skip non-HTTP(S) schemes (e.g. chrome-extension://)
    if (url.protocol !== 'http:' && url.protocol !== 'https:') return;

    // Skip non-GET requests (e.g. POST to login)
    if (event.request.method !== 'GET') return;

    // Never intercept full-page navigations. fetch() transparently follows
    // server-side redirects (login, logout, "add to library first", etc.),
    // and handing a redirected response back to a navigation request is
    // rejected by the browser outright - the navigation just silently fails,
    // which looks exactly like clicking Logout and having the page "refresh"
    // without actually logging out. Let the browser handle these directly.
    if (event.request.mode === 'navigate') return;

    // Use Network First, falling back to Cache for most HTML / API requests
    // This ensures they always get the latest content if online.
    event.respondWith(
        fetch(event.request).then(networkResponse => {
            // Check if we received a valid response
            if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
                return networkResponse;
            }

            // Don't cache opaque responses or non-GET
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then(cache => {
                // We cache pages, api requests, and static assets
                cache.put(event.request, responseToCache);
            });

            return networkResponse;
        }).catch(async () => {
            // Network failed (offline), try cache
            const cachedResponse = await caches.match(event.request);
            if (cachedResponse) {
                return cachedResponse;
            }
            return Response.error();
        })
    );
});
