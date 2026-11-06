self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('titantap-store').then((cache) => cache.addAll([
      '/',
      'https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap'
    ]))
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => response || fetch(e.request))
  );
});
