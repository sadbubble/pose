var CACHE_NAME='pose-v1';
var STATIC_ASSETS=[
  '/','/index.html','/manifest.json','/icon-192.png','/icon-512.png'
];
var FONT_CACHE='pose-fonts-v1';

self.addEventListener('install',function(e){
  e.waitUntil(
    caches.open(CACHE_NAME).then(function(cache){
      return cache.addAll(STATIC_ASSETS);
    }).then(function(){self.skipWaiting();})
  );
});

self.addEventListener('activate',function(e){
  e.waitUntil(
    caches.keys().then(function(keys){
      return Promise.all(keys.filter(function(k){
        return k!==CACHE_NAME&&k!==FONT_CACHE;
      }).map(function(k){return caches.delete(k);}));
    }).then(function(){return self.clients.claim();})
  );
});

self.addEventListener('fetch',function(e){
  var url=new URL(e.request.url);

  // Skip non-GET requests
  if(e.request.method!=='GET')return;

  // Bypass cache for API / Supabase (dynamic guest data)
  if(url.pathname.startsWith('/api')||url.pathname.includes('/api/')||url.hostname.includes('supabase.co')){
    return;
  }

  // Cache-first for fonts
  if(url.hostname==='fonts.googleapis.com'||url.hostname==='fonts.gstatic.com'){
    e.respondWith(
      caches.open(FONT_CACHE).then(function(cache){
        return cache.match(e.request).then(function(resp){
          if(resp)return resp;
          return fetch(e.request).then(function(r){
            if(r.ok)cache.put(e.request,r.clone());
            return r;
          });
        });
      })
    );
    return;
  }

  // Network-first for HTML (to get latest version)
  if(e.request.headers.get('accept')&&e.request.headers.get('accept').includes('text/html')){
    e.respondWith(
      fetch(e.request).then(function(r){
        if(r.ok){
          var c=r.clone();
          caches.open(CACHE_NAME).then(function(cache){cache.put(e.request,c);});
        }
        return r;
      }).catch(function(){
        return caches.match(e.request)||caches.match('/');
      })
    );
    return;
  }

  // Cache-first for static assets (CDN scripts, icons)
  e.respondWith(
    caches.match(e.request).then(function(resp){
      if(resp)return resp;
      return fetch(e.request).then(function(r){
        if(r.ok&&url.protocol==='https:'){
          var c=r.clone();
          caches.open(CACHE_NAME).then(function(cache){cache.put(e.request,c);});
        }
        return r;
      });
    }).catch(function(){
      return new Response('Offline',{status:503,statusText:'Offline'});
    })
  );
});
