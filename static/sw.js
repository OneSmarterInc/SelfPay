// Cache only a generic offline page. Never cache API responses, searches or chat.
const CACHE = 'myselfpay-offline-v1';
const OFFLINE = '/offline.html';
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache =>
    cache.add(new Request(OFFLINE, {cache: 'reload', credentials: 'omit'}))));
  // Let an existing open session finish before activating an update.
});
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) {
      if (key.startsWith('myselfpay-offline-') && key !== CACHE) await caches.delete(key);
    }
    await self.clients.claim();
  })());
});
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || request.mode !== 'navigate' ||
      url.origin !== self.location.origin || url.pathname !== '/') return;
  event.respondWith(fetch(request).catch(async () =>
    (await caches.match(OFFLINE)) || new Response('MySelfPay needs an internet connection. Please reconnect and reload.',
      {status: 503, headers: {'Content-Type': 'text/plain; charset=utf-8'}})));
});
