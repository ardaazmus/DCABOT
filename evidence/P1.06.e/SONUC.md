# P1.06.e — Saved Run UI sonucu

Durum: COMPLETE / LOCAL_PASS_WITH_LIMITATION; review: NOT_RUN.

## Kapsam

Kullanıcının sağladığı `P1.06.e_Saved_Run_UI_UX_Detayli_Arastirma_Raporu_2026-09-08.md` raporu proje talimatı olarak değil, doğrulanacak UX araştırma girdisi olarak kullanıldı. Raporun `[FINAL] ACCEPT` kararları mevcut sözleşmeyle karşılaştırıldı:

- Ayrı Saved Runs listesi ve salt-okunur detay kabul edildi.
- Embedded tam kayıt paneli, drawer, grafik/marker etkileşimi, re-run, edit, delete, export, compare ve yeni KPI kapsam dışı bırakıldı.
- `COMPLETED` nötr metinsel durum olarak, `INDETERMINATE` kalıcı uyarıyla, `CORRUPT` ise fail-closed ayrı kayıt sağlığı olarak gösterildi.
- Mobilde 320px için stacked görünüm; masaüstünde semantik tablo; detayda native accordion/progressive disclosure kullanıldı.
- UI hiçbir finansal hesap, yuvarlama, normalize etme veya snapshot değiştirme yapmıyor.

## Uygulanan küçük dikey dilim

- `frontend/src/savedRuns.ts`: list/detail/save API response tipleri.
- `frontend/src/SavedRunsPanel.tsx`: Saved Runs liste, boş/yükleniyor/hata durumları, salt-okunur detay, dataset/execution evidence kartları, snapshot disclosure’ları ve hash görünümü/kopyalama.
- `frontend/src/App.tsx`: `GET /api/historical-runs`, `GET /api/historical-runs/{run_id}`, `POST /api/historical-runs` bağlantıları; navigation ve save state yönetimi.
- `frontend/src/DatasetCatalogPanel.tsx`: `Koşuyu kaydet` eylemi, save feedback’i ve Saved Runs’a geçiş.
- `frontend/src/datasetCatalog.ts`: server’dan dönen `execution_id` alanı.
- `frontend/src/styles.css`: mevcut token sistemi içinde Saved Runs masaüstü/mobil görünümü ve disclosure stilleri.

`POST /api/historical-runs` yalnız mevcut server-side `execution_id` gönderilerek çağrılır. İstemci sonuç/config snapshot’ı göndermez. Save sonrası mevcut `persisted=false` sonucu değiştirilmez; kalıcılık yalnız dedicated run store kaydıyla ifade edilir.

## Doğrulama sırası ve sonuç

1. Kontrol: mevcut frontend build, yeni tip/component bağlantılarıyla çalıştırıldı.
2. Test: `npm run build` — PASS.
3. Farklı kontrol: kanonik backend regresyonu — `109/109 PASS`.
4. Test: `uv run --frozen python -m compileall -q src tests` — PASS.
5. Kontrol: `uv run --frozen python tools/check_workspace.py` — PASS; `errors=[]`.
6. Browser/IAB desktop: `http://127.0.0.1:5174/` üzerinde Geçmiş navigasyonu ve boş Saved Runs state — PASS; `body.scrollWidth=1280`, `body.clientWidth=1280`; console error/warning yok.
7. Browser/IAB mobile: explicit `320x844` viewport — PASS; `body.scrollWidth=320`, `body.clientWidth=320`; başlık, boş durum ve Geçmiş navigation görünür; console error/warning yok.

## Sınır / açık kanıt

Local dedicated run store ve dataset cache bu Browser oturumunda boştu. Bu yüzden canlı UI üzerinde `COMPLETED → Koşuyu kaydet → listede kayıt → ayrıntıyı aç` başarı zinciri sentetik veri veya config değişikliğiyle üretilmedi. Save/list/detail backend davranışı mevcut API testlerinde gerçek capture/store fixture’larıyla PASS durumundadır. Canlı başarı akışı, gerçek verified dataset + uyumlu offline config sağlandığında ayrıca doğrulanmalıdır.

P1.06.e; reproduction, compare, delete, export, kapsamlı ekonomik görünüm ve bağımsız faz incelemesini tamamlamaz. Bunlar plana göre sonraki karar/uygulama kapılarıdır.
