const CACHE_NAME = 'maxky-pos-v3'; // 🟢 เปลี่ยน Version เพื่อ Force Clear Cache
const ASSETS_TO_CACHE = [
  '/',
  '/sale',
  '/static/manifest.json'
];

// 1. ติดตั้ง และข้ามการรอ (Skip Waiting)
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
  );
  self.skipWaiting();
});

// 2. เคลียร์ Cache เวอร์ชันเก่าออกให้หมดทันที
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) return caches.delete(key);
        })
      );
    })
  );
  self.clients.claim();
});

// 3. ดักจับ Request แบบ Network-First (ถ้ามีเน็ตดึงจากเซิร์ฟเวอร์ ถ้าไม่มีเน็ตดึงจาก Cache)
self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(
          JSON.stringify({ success: false, offline: true, message: 'Offline Mode' }),
          { headers: { 'Content-Type': 'application/json' } }
        );
      })
    );
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
        }
        return networkResponse;
      })
      .catch(() => {
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) return cachedResponse;
          if (event.request.mode === 'navigate') {
            return caches.match('/sale') || caches.match('/');
          }
        });
      })
  );
});