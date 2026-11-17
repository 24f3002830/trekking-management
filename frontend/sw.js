/**
 * Minimal Service Worker for Trekking Management Application (TMA).
 * Enables "Add to Desktop / Install App" PWA functionality.
 */

const CACHE_NAME = 'tma-cache-v2';
const STATIC_ASSETS = [
  '/',
  '/frontend/src/app.js',
  '/frontend/manifest.json'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  // Let network handle API requests directly; fallback to cache if available
  if (event.request.url.includes('/api/')) {
    return;
  }
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
