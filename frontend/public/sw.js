/* Service worker do Pauta: casco do app em cache, notícias sempre da rede. */
const VERSAO = 'pauta-v1'
const ESTATICOS = ['/', '/index.html', '/icone.svg', '/manifest.webmanifest']

self.addEventListener('install', (evento) => {
  evento.waitUntil(caches.open(VERSAO).then((cache) => cache.addAll(ESTATICOS)))
  self.skipWaiting()
})

self.addEventListener('activate', (evento) => {
  evento.waitUntil(
    caches.keys().then((chaves) =>
      Promise.all(chaves.filter((chave) => chave !== VERSAO).map((chave) => caches.delete(chave)))
    )
  )
  self.clients.claim()
})

self.addEventListener('fetch', (evento) => {
  const requisicao = evento.request
  if (requisicao.method !== 'GET') return
  const url = new URL(requisicao.url)
  if (url.origin !== self.location.origin) return

  // conteúdo da API: rede primeiro, cache como rede de segurança
  if (url.pathname.startsWith('/api/')) {
    evento.respondWith(
      fetch(requisicao)
        .then((resposta) => {
          const copia = resposta.clone()
          caches.open(VERSAO).then((cache) => cache.put(requisicao, copia))
          return resposta
        })
        .catch(() => caches.match(requisicao))
    )
    return
  }

  // casco do app: cache primeiro
  evento.respondWith(
    caches.match(requisicao).then((cacheado) => cacheado || fetch(requisicao).catch(() => caches.match('/index.html')))
  )
})
