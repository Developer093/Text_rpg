// 오프라인 실행을 위한 서비스 워커
// 게임 파일을 고치면 아래 버전 숫자를 올려 주세요. (그래야 설치한 사람에게도 새 버전이 반영돼요)
const CACHE = "kingdom-rpg-v1";

const FILES = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icon-192.png",
  "./icon-512.png",
  "./apple-touch-icon.png",
];

// 설치: 게임 파일을 미리 저장
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES)));
  self.skipWaiting();
});

// 활성화: 예전 버전 캐시 삭제
self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// 요청 처리: 인터넷이 되면 최신 파일, 안 되면 저장해 둔 파일
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET" || !e.request.url.startsWith("http")) return;
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy)); // 글꼴 등도 함께 저장
        return res;
      })
      .catch(() =>
        caches.match(e.request, { ignoreSearch: true }).then(
          (hit) => hit || (e.request.mode === "navigate" ? caches.match("./index.html") : undefined)
        )
      )
  );
});
