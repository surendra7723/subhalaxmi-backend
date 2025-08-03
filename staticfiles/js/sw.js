// Service Worker for Progressive Web App and Caching
// This improves performance by caching resources and enabling offline functionality

const CACHE_NAME = 'subhalaxmi-v1.0.0';
const STATIC_CACHE = 'subhalaxmi-static-v1.0.0';
const DYNAMIC_CACHE = 'subhalaxmi-dynamic-v1.0.0';

// Resources to cache immediately
const STATIC_ASSETS = [
    '/',
    '/static/css/styles.css',
    '/static/css/performance.css',
    '/static/js/main.js',
    // Add your most critical assets here
];

// Resources to cache on demand
const CACHE_STRATEGIES = {
    images: 'cache-first',
    api: 'network-first',
    pages: 'stale-while-revalidate'
};

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('Service Worker: Installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('Service Worker: Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('Service Worker: Failed to cache static assets', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker: Activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                            console.log('Service Worker: Deleting old cache', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                return self.clients.claim();
            })
    );
});

// Fetch event - handle network requests with caching strategies
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip cross-origin requests (unless specifically handled)
    if (url.origin !== location.origin) {
        return;
    }
    
    event.respondWith(handleRequest(request));
});

async function handleRequest(request) {
    const url = new URL(request.url);
    const path = url.pathname;
    
    try {
        // Static assets - Cache First strategy
        if (isStaticAsset(path)) {
            return await cacheFirst(request, STATIC_CACHE);
        }
        
        // Images - Cache First strategy
        if (isImage(path)) {
            return await cacheFirst(request, DYNAMIC_CACHE);
        }
        
        // API endpoints - Network First strategy
        if (isAPIRequest(path)) {
            return await networkFirst(request, DYNAMIC_CACHE);
        }
        
        // Pages - Stale While Revalidate strategy
        if (isPageRequest(path)) {
            return await staleWhileRevalidate(request, DYNAMIC_CACHE);
        }
        
        // Default to network
        return await fetch(request);
        
    } catch (error) {
        console.error('Service Worker: Request failed', error);
        
        // Fallback to cache if available
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline page for page requests
        if (isPageRequest(path)) {
            return await caches.match('/offline.html') || 
                   new Response('Offline', { status: 503 });
        }
        
        throw error;
    }
}

// Cache First Strategy - Good for static assets
async function cacheFirst(request, cacheName) {
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    
    if (networkResponse && networkResponse.status === 200) {
        const cache = await caches.open(cacheName);
        await cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
}

// Network First Strategy - Good for API requests
async function networkFirst(request, cacheName) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse && networkResponse.status === 200) {
            const cache = await caches.open(cacheName);
            await cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        throw error;
    }
}

// Stale While Revalidate Strategy - Good for pages
async function staleWhileRevalidate(request, cacheName) {
    const cachedResponse = await caches.match(request);
    
    const fetchPromise = fetch(request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
            const cache = caches.open(cacheName);
            cache.then(c => c.put(request, networkResponse.clone()));
        }
        return networkResponse;
    });
    
    return cachedResponse || fetchPromise;
}

// Helper functions to determine request types
function isStaticAsset(path) {
    return /\.(css|js|woff|woff2|ttf|eot|ico)$/i.test(path) ||
           path.startsWith('/static/');
}

function isImage(path) {
    return /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(path) ||
           path.startsWith('/media/');
}

function isAPIRequest(path) {
    return path.startsWith('/api/') ||
           path.startsWith('/admin/');
}

function isPageRequest(path) {
    return !isStaticAsset(path) && !isImage(path) && !isAPIRequest(path);
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    // Handle any offline actions when connection is restored
    console.log('Service Worker: Background sync triggered');
}

// Push notifications (if needed)
self.addEventListener('push', (event) => {
    if (event.data) {
        const data = event.data.json();
        
        const options = {
            body: data.body,
            icon: '/static/images/icon-192x192.png',
            badge: '/static/images/badge-72x72.png',
            actions: [
                {
                    action: 'view',
                    title: 'View',
                    icon: '/static/images/view-icon.png'
                },
                {
                    action: 'close',
                    title: 'Close',
                    icon: '/static/images/close-icon.png'
                }
            ]
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Performance monitoring
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'PERFORMANCE_MEASURE') {
        // Log performance metrics
        console.log('Performance measure:', event.data.measure);
    }
});

// Cache size management
async function manageCacheSize(cacheName, maxItems = 100) {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();
    
    if (keys.length > maxItems) {
        const deletePromises = keys.slice(0, keys.length - maxItems)
            .map(key => cache.delete(key));
        
        await Promise.all(deletePromises);
        console.log(`Cache ${cacheName} cleaned up`);
    }
}

// Periodic cache cleanup
setInterval(() => {
    manageCacheSize(DYNAMIC_CACHE, 100);
}, 300000); // Every 5 minutes
