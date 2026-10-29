/* Service worker. Bump CACHE when the precache list changes; every path below must exist or install fails. */
const CACHE = 'llm-wiki-v10';
const PRECACHE = [
  './',
  './index.html',
  './offline.html',
  './manifest.webmanifest',
  './assets/site.css',
  './assets/brain.css',
  './assets/i18n.js',
  './assets/brain.js',
  './assets/app.js',
  './assets/favicon.svg',
  './assets/icon-192.png',
  './assets/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // Pages: network first, fall back to cache, then the offline page.
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {}); }
          return res;
        })
        .catch(() => caches.match(req).then((r) => r || caches.match('./index.html')).then((r) => r || caches.match('./offline.html')))
    );
    return;
  }

  // Assets: serve from cache immediately, refresh in the background (stale-while-revalidate).
  event.respondWith(
    caches.open(CACHE).then((cache) =>
      cache.match(req).then((cached) => {
        const network = fetch(req)
          .then((res) => { if (res && res.ok && res.type === 'basic') cache.put(req, res.clone()).catch(() => {}); return res; })
          .catch(() => cached || caches.match('./offline.html'));
        return cached || network;
      })
    )
  );
});
