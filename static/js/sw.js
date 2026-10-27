// Prisma Territorial · service worker: permite abrir el formulario comunitario sin señal.
const CACHE = 'prisma-reportar-v3';
const ARCHIVOS = ['/reportar', '/static/css/styles.css', '/static/css/public.css', '/static/vendor/bootstrap/bootstrap.min.css',
  '/static/vendor/fontawesome/css/all.min.css', '/static/vendor/fontawesome/webfonts/fa-solid-900.woff2',
  '/static/fonts/ibm-plex-sans-latin-400-normal.woff2', '/static/fonts/ibm-plex-sans-latin-500-normal.woff2',
  '/static/fonts/ibm-plex-sans-latin-600-normal.woff2', '/static/fonts/ibm-plex-sans-latin-300-normal.woff2'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ARCHIVOS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return;
  if (url.pathname === '/reportar') {
    // Red primero; si no hay señal, la copia guardada.
    e.respondWith(fetch(e.request).then(r => { const c = r.clone(); caches.open(CACHE).then(k => k.put('/reportar', c)); return r; })
      .catch(() => caches.match('/reportar')));
  } else if (url.pathname.startsWith('/static/')) {
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
  }
});
