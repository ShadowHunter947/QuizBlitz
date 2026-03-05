diff --git a/sw.js b/sw.js
index 4cb440c25dcbba3f595805f47ee137754b506b57..8d06364fadd6a67ffd62e5892ea7aab272d5ccb1 100644
--- a/sw.js
+++ b/sw.js
@@ -1,33 +1,54 @@
-const CACHE_NAME = 'quiz-blitz-v2.1';
+const CACHE_NAME = 'quiz-blitz-v3';
 const ASSETS = [
   '/',
   '/index.html',
   '/manifest.json',
   '/icons/icon-192.png',
   '/icons/icon-512.png',
+  'https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Dela+Gothic+One&display=swap',
+  'https://unpkg.com/react@18/umd/react.production.min.js',
+  'https://unpkg.com/react-dom@18/umd/react-dom.production.min.js',
+  'https://unpkg.com/@babel/standalone/babel.min.js',
 ];
 
 self.addEventListener('install', e => {
   e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(ASSETS)));
   self.skipWaiting();
 });
 
 self.addEventListener('activate', e => {
   e.waitUntil(caches.keys().then(keys =>
     Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
   ));
   self.clients.claim();
 });
 
 self.addEventListener('fetch', e => {
   if (e.request.method !== 'GET') return;
+  const url = e.request.url;
+  const isCdn = url.includes('unpkg.com') || url.includes('fonts.googleapis.com');
+
+  if (isCdn) {
+    e.respondWith(
+      caches.match(e.request).then(cached => {
+        if (cached) return cached;
+        return fetch(e.request).then(res => {
+          const clone = res.clone();
+          caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
+          return res;
+        });
+      })
+    );
+    return;
+  }
+
   e.respondWith(
     fetch(e.request)
       .then(res => {
         const clone = res.clone();
         caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
         return res;
       })
       .catch(() => caches.match(e.request))
   );
 });
