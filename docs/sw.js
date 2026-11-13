/* Service Worker: macht die Seite als App installierbar und offline nutzbar.
   Seite und Daten: zuerst aus dem Netz (immer aktuell), ohne Netz aus dem Zwischenspeicher.
   Schriften, Icons, Flaggen: aus dem Zwischenspeicher (ändern sich selten).
   Fremde Server (Störungen live, Stadtplan, Google Maps) werden nicht angefasst. */
const CACHE = "wien-live-1.3.0";
self.addEventListener("install", e => { self.skipWaiting(); e.waitUntil(caches.open(CACHE).then(c => c.addAll(["./", "manifest.webmanifest", "icons/icon-192.png"]))); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(k => Promise.all(k.filter(n => n !== CACHE).map(n => caches.delete(n)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== location.origin) return;
  const stat = /\/(fonts|icons|flags)\//.test(u.pathname);
  if (stat) {
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).then(res => { const c = res.clone(); caches.open(CACHE).then(x => x.put(e.request, c)); return res; })));
  } else {
    /* Seite und Manifest immer frisch vom Server, nicht aus dem Browser-Zwischenspeicher (sonst übernimmt Chrome beim Installieren ein altes Icon) */
    const fresh = /manifest\.webmanifest$|\/$|index\.html$/.test(u.pathname) ? new Request(e.request, { cache: "no-cache" }) : e.request;
    e.respondWith(fetch(fresh).then(res => { if (res.ok) { const c = res.clone(); caches.open(CACHE).then(x => x.put(e.request, c)); } return res; })
      .catch(() => caches.match(e.request, { ignoreSearch: true }).then(r => r || caches.match("./"))));
  }
});
