const CACHE='apiculture-v1-27';
const CORE=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png'];

self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)));
  self.skipWaiting();
});

self.addEventListener('activate',event=>{
  event.waitUntil(
    caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener('fetch',event=>{
  const req=event.request;
  if(req.method!=='GET')return;
  const url=new URL(req.url);
  if(url.pathname.startsWith('/api/'))return;

  if(req.mode==='navigate'){
    const network=fetch(req).then(resp=>{
      if(resp&&resp.ok){
        const copy=resp.clone();
        caches.open(CACHE).then(c=>c.put('./index.html',copy)).catch(()=>{});
      }
      return resp;
    });
    event.respondWith(
      caches.match('./index.html').then(cached=>cached || network.catch(()=>caches.match('./index.html')))
    );
    if(event.waitUntil)event.waitUntil(network.catch(()=>{}));
    return;
  }

  event.respondWith(
    caches.match(req).then(hit=>hit || fetch(req).then(resp=>{
      if(resp&&resp.ok){
        const copy=resp.clone();
        caches.open(CACHE).then(c=>c.put(req,copy)).catch(()=>{});
      }
      return resp;
    }))
  );
});
