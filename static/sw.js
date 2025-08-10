const CACHE_NAME = "dlmtc-cache-v1";
const urlsToCache = [
  "/",                         // Homepage
  "/static/css/style.css",     // Your CSS file
  "/static/icons/icon-192.png",  // App icon
  "/static/icons/icon-512.png",  // Bigger icon
  "/manifest.json",            // Manifest file
  // Add more static files if needed
];

// Install event: cache static assets
self.addEventListener("install", function(event) {
  console.log("Service Worker: Installed");
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log("Service Worker: Caching Files");
        return cache.addAll(urlsToCache);
      })
  );
});

// Activate event: clean old caches
self.addEventListener("activate", function(event) {
  console.log("Service Worker: Activated");
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cache) {
          if (cache !== CACHE_NAME) {
            console.log("Service Worker: Clearing Old Cache");
            return caches.delete(cache);
          }
        })
      );
    })
  );
});

// Fetch event: serve cached content when offline
self.addEventListener("fetch", function(event) {
  event.respondWith(
    caches.match(event.request).then(function(response) {
      return response || fetch(event.request);
    }).catch(() => {
      // Optional fallback for offline pages
      if (event.request.mode === 'navigate') {
        return caches.match('/');
      }
    })
  );
});
