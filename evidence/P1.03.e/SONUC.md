# P1.03.e — katalog UI dikey dilimi sonucu

## Kapsam

P1.03.d’deki local katalog API’si mevcut P1.02 React/Vite ekranına bağlandı. Bu faz yalnız katalog okuma, durumların anlaşılır gösterimi ve doğrulanmış dataset seçimi sınırındadır.

## Uygulanan davranış

- `GET /api/datasets` ekran açılışında okunur; loading, error ve empty durumları gösterilir.
- `ALL`, `VERIFIED`, `MISSING` ve `CORRUPT` filtreleri vardır.
- Dataset tablosu dataset ID/type, enstrüman, interval, dönem ve durum alanlarını gösterir.
- Sağ detay panelinde artifact byte size ve kısa SHA-256 gösterilir; path ve URL gösterilmez.
- Durumlar yalnız renkle anlatılmaz: `✓ VERIFIED — Doğrulandı`, `– MISSING — Yerel kopya yok`, `! CORRUPT — Bütünlük hatası` ikon + metinle gösterilir.
- `MISSING` ve `CORRUPT` için seçim düğmesi disabled’dır.
- `VERIFIED` için `PUT /api/dataset-selection` çağrısı yapılır; seçim tamamlandıktan sonra UI, parser/application aktarımının bu fazda başlatılmadığını açıkça korur.
- Download button/job, URL/path, credential, import persistence, chart, finansal hesap ve testnet eklenmedi.

## Uygulanan dosyalar

- `frontend/src/App.tsx`: katalog okuma ve verified selection state/fetch akışı.
- `frontend/src/DatasetCatalogPanel.tsx`: filtre, semantik tablo, durum rozeti ve sağ detay paneli.
- `frontend/src/datasetCatalog.ts`: wire tipleri, durum metadata’sı ve artifact format yardımcıları.
- `frontend/src/styles.css`: masaüstü tablo + detay düzeni, mobil stack, focus ve durum stilleri.
- `TASK.md`, `STATE.md`: faz ve sıradaki iş kaydı.

## Kanıt

- `npm run build` (`frontend/`): PASS; TypeScript ve Vite production build tamamlandı.
- Gerçek local API + Vite üzerinden Browser/IAB masaüstü: PASS; katalog 1 tanım döndürdü, varsayılan cache olmadığı için `MISSING` gösterildi, sağ detay paneli açıldı.
- Browser/IAB etkileşim: `MISSING` filtresi bir satır gösterdi; `Doğrulanmış cache gerekli` düğmesi disabled; UI console error/warning yok.
- Browser/IAB mobil 390×844: PASS; katalog DOM’da görünür, `scrollWidth=375` ve `clientWidth=375`, yatay sayfa taşması yok; console error/warning yok.
- Backend regression: P1.03.d’den kalan `tools/run_checks.py` sonucu 64 test PASS olarak korunuyor; bu faz backend kodunu değiştirmedi.

## Açık sınırlar

Varsayılan `data/public_cache` boş olduğundan gerçek local ekranda `VERIFIED` seçim başarı ekranı üretilemez; bu, katalog API’nin beklenen `MISSING` sözleşmesidir. Verified seçim endpoint’ine bağlanan UI yolu kodlanmıştır, fakat gerçek verified artifact üretimi P1.03.f download/cache fazının konusudur.

Durum: `COMPLETE / LOCAL_PASS`; bağımsız inceleme: `NOT_RUN`.
