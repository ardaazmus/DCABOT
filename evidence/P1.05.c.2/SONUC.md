# P1.05.c.2 — Minimal grafik render kanıtı

## Kapsam

Bu alt faz, P1.05.c.1’de kabul edilen chart data contract’ı değiştirmeden `COMPLETED` simülasyon sonucunda read-only, statik ve minimal bir OHLC overview render eder. Grafik yalnız açıklayıcı tarihsel görünüm olarak kullanılır; finansal doğruluk kaynağı, işlem karar motoru veya action table alternatifi değildir.

Kullanıcının sağladığı anonim araştırma raporu araştırma/karar girdisi olarak değerlendirildi; proje talimatı sayılmadı.

## Araştırma kararı

- **ACCEPT:** Native React + inline SVG, nötr OHLC bar glyph, backend sırası, en fazla 1.000 bar, exact decimal string etiket kaynağı, fixed-point display coordinate mapping, equal-slot x mapping, responsive `viewBox`, erişilebilir figure/image semantiği, güvenli boş/hata durumları.
- **SIMPLIFY:** Candlestick yerine tek renkli nötr OHLC glyph; tooltip, zaman-orantılı x ekseni ve per-bar erişilebilir tablo ilk render’dan çıkarıldı.
- **DEFER:** Action marker, tooltip, hover/crosshair, zoom/pan/brush, per-bar keyboard exploration, time-proportional x scale, gelişmiş tick/locale biçimleme, export ve chart library değerlendirmesi.
- **REJECT:** Canvas default, yeni chart dependency, backend contract genişletmesi, frontend finansal hesap, decimal stringlerin kör `Number()` ile authoritative fiyat olarak kullanılması, downsampling/aggregation, partial ambiguity render, 409 sonrası client slicing, fake exit ve external resource.

## Uygulanan davranış

- Grafik yalnız simulation `COMPLETED` olduğunda `/api/datasets/{dataset_id}/chart-data` endpoint’inden yüklenir.
- Chart request simulation’ın `dataset_id`, `artifact_sha256` ve `processed_bar_count` değerleriyle eşleşme kontrolü yapar; mismatch fail-closed hata durumudur.
- Endpoint yanıtı `HistoricalChartData` olarak alınır; model id, bar sayısı, 1-based `bar_index`, artan zaman, geçerli OHLC aralığı ve timestamp güvenlik guard’ları kontrol edilir.
- OHLC kaynak stringleri değiştirilmez. Decimal değerler geçici fixed-point `BigInt` katsayılarla karşılaştırılır; yalnız SVG pixel koordinatı için bounded oran üretilir.
- Grafik tek/az sayıda declarative SVG path ile çizilir; bar başına focus veya pointer event yoktur.
- Renk yön semantiği kullanılmaz. Grafik low-high dikey çizgisi, open sol tick’i ve close sağ tick’i ile nötr OHLC overview gösterir.
- `INDETERMINATE`, `AMBIGUOUS_OHLC_PATH`, geçersiz payload, boş veri, API hatası ve scope error durumlarında grafik çizilmez; bounded metin durumu gösterilir.
- `OPEN_AT_END` için fake exit, forced close veya final PnL üretilmez.
- Action table mevcut haliyle korunur; marker eklenmez.
- Renderer `fetch`, persistence, credential, exchange, websocket, external CDN veya analytics başlatmaz. Veri yükleme yalnız üst uygulama akışındaki mevcut local API çağrısıdır.

## Değişen dosyalar

- `frontend/src/HistoricalChart.tsx`: fixed-point display guard’ları ve native SVG renderer.
- `frontend/src/App.tsx`: `COMPLETED` sonrası bounded chart data fetch, revision/eşleşme guard’ı ve abort lifecycle.
- `frontend/src/DatasetCatalogPanel.tsx`: sonuç özetine chart görünümünün bağlanması.
- `frontend/src/styles.css`: responsive chart frame, statik SVG ve safe state stilleri.
- `TASK.md`, `STATE.md`, `README.md`, `docs/MIMARI.md`, `docs/VERI_VE_SIMULASYON.md`, `docs/OZELLIK_MATRISI.md`: faz durumu ve sınır kayıtları.

## Doğrulama

- Frontend TypeScript/Vite build: **PASS** (`npm run build`).
- Browser sayfa kimliği: **PASS** — `http://127.0.0.1:5173/`, başlık `DCABOT — Bot stüdyosu`.
- Browser DOM/blank page: **PASS** — anlamlı uygulama içeriği render edildi, framework error overlay görülmedi.
- Desktop layout: **PASS** — `body.scrollWidth=1430`, `body.clientWidth=1430`, page overflow yok.
- Simulation interaction: **PASS** — onay dialog’u açıldı; `Başlat` sonrası mevcut config uyumsuzluğu güvenli `Historical reducer mevcut politika sınırları içinde çalışamadı.` hatası olarak gösterildi.
- 320px responsive: **PASS** — `innerWidth=320`, `body.scrollWidth=305`, `body.clientWidth=305`, page overflow yok.
- Console: **PASS** — browser error/warning kaydı yok.
- Chart success state: **NOT_RUN** — aktif `config/paper.json` mevcut gerçek artifact fiyat ölçeğiyle uyumsuz olduğu için `COMPLETED` sonucu üretilemedi; sentetik başarı sonucu üretilmedi.

## Kalan sınır

Başarı sonucu üretilemediği için canlı artifact üzerinde SVG path’in görsel doğrulaması ve chart endpoint’inden UI’a kadar başarı akışı doğrulanamadı. Config değiştirilmedi; finansal config kararı bu alt fazın yetkisi dışında bırakıldı. P1.05.c.2 implementasyonu build ve güvenli hata/responsive akışında doğrulanmıştır, ancak başarı ekranı için açık QA sınırı vardır.

## Sonraki tek iş

`P1.05.c.3 — Action marker araştırma kapısı`. Marker eşleştirmesi, `bar_index`/zaman ilişkisi, belirsizlik görünümü, erişilebilirlik ve 320px davranışı için yeni anonim araştırma alınmadan marker render kodu yazılmayacaktır.
