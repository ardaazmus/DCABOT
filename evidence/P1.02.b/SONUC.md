# P1.02.b — Canonical alan eşleme ve ilk kalite ekranı

Durum: IMPLEMENTED / LOCAL_PASS  
Bağımsız inceleme: NOT_RUN  
Referans: P1.01’deki mevcut React/Vite koyu arayüz sistemi; bu küçük UI dilimi için dış görsel araştırma veya yeni görsel konsept kullanılmadı.

## Teslim

- `frontend/src/App.tsx`: local CSV/ZIP seçimi, `/api/data-quality` upload akışı, kalite özeti ve canonical bar/trade alan eşleme kontrolleri.
- Exact canonical header’lar otomatik seçilir.
- Canonical olmayan/rejected raporda kullanıcı veri tipini seçip ham header’ları mapping ekranında hazırlayabilir; kalite reddi gizlenmez ve mapping import edilmiş veri gibi gösterilmez.
- Eksik veya aynı kaynak kolona çakışan eşleme yerel olarak reddedilir.
- `frontend/src/styles.css`: mevcut tasarım token’larına bağlı responsive veri paneli, mapping grid’i ve kalite bulguları.
- `src/dcabot/server/api.py`: doğrudan istemci kullanımı için `X-Filename` CORS izni.

## Kanıt

- `npm run build`: **PASS**.
- `uv run --frozen python tools/run_checks.py`: **50 test PASS**.
- Browser/IAB: `http://127.0.0.1:5175/`, başlık ve içerik **PASS**, framework overlay yok, console error/warning **0**.
- Browser akışı: local canonical CSV seçildi → `Temiz`, `bar`, `microseconds`, `UTC`, 2 satır raporu → exact mapping otomatik seçildi → `Eşleme tamamlandı`.
- Browser akışı: ham CSV seçildi → backend `422 / REJECTED` raporu görünür kaldı → `Bar / OHLCV` seçildi → mapping alanları açıldı → eksik mapping `Eksik eşleme` olarak reddedildi.
- Responsive: masaüstü 1280×800 ve mobil 360×800 kontrol edildi; mobil sayfada yatay taşma gözlenmedi.
- `tools/check_workspace.py`: **PASS**; yedek alanı çalıştırılmadı/taranmadı.

## Sınır ve sonraki faz

Bu teslim kalıcı dataset kaydı, mapping persistence, public downloader, tarihsel simülasyon veya testnet değildir. Sıradaki tek görev `P1.03.a`: izinli public kaynak sözleşmesi ve güvenli indirme/cache akışının en küçük hazırlık dilimi. Dış kaynak veya finansal araştırma gereksinimi ortaya çıkarsa kullanıcıdan anonim ve uygulanabilir araştırma prompt’u istenecektir.
