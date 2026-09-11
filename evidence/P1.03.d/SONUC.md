# P1.03.d — local katalog API sonucu

## Kapsam

P1.03.c’deki explicit yerel katalog sözleşmesi, iki küçük local HTTP endpoint’iyle erişilebilir hale getirildi:

- `GET /api/datasets`
- `PUT /api/dataset-selection`

Bu endpoint’ler yalnız loopback ile çalıştırılan local uygulamanın mevcut API’sine eklenmiştir. Listeleme ve selection ağ erişimi, download, cache yazımı veya testnet işlemi başlatmaz.

## API davranışı

- Dataset ID request’te strict Pydantic v2 modeliyle alınır: yalnız lowercase alfanümerik, `_` ve `-`, 1–64 karakter; extra alan yoktur.
- Liste response’u explicit registry tanımlarını `dataset_id` lexical sırasıyla döndürür.
- Wire durumları yalnız `MISSING`, `CORRUPT`, `VERIFIED` değerleridir.
- `VERIFIED` dışında `artifact: null` döner; verified artifact özetinde yalnız SHA-256 ve byte size vardır.
- HTTP response’larında `path`, `cache_path`, `metadata_path`, `url` veya benzeri yerel/uzak adres alanları yoktur.
- Bilinmeyen ID `404 DATASET_NOT_FOUND`.
- Bilinen MISSING cache `409 DATASET_CACHE_MISSING`.
- Bilinen CORRUPT cache `409 DATASET_CACHE_CORRUPT`.
- Listeleme ve başarılı/başarısız selection response’ları `Cache-Control: no-store` taşır.
- Selection önce catalog state’i kontrol eder, sonra fresh verified selection yapar; yarışta parser’a doğrulanmamış path aktarılmaz.
- Eski preview/data-quality endpoint hata gövdeleri korunmuştur.

## Uygulanan dosyalar

- `src/dcabot/server/api.py`: strict DTO’lar, problem response’ları, iki endpoint ve CORS PUT izni.
- `tests/api/test_dataset_catalog.py`: listeleme, path sızıntısı, no-store, missing/verified/corrupt/unknown selection.
- `README.md`: güncel API endpoint listesi ve dataset endpoint sınırı.

## Kanıt

- `tools/run_checks.py`: PASS, 64 test.
- `tools/check_workspace.py`: PASS; `YEDEK_ESKI_PROJE` okunmadı/çalıştırılmadı.
- `compileall`: PASS.
- `uv.lock`: FastAPI 0.141.1 ve Starlette 1.6.0 mevcut; yeni runtime dependency eklenmedi.
- README ve mevcut çalıştırma akışı local loopback `127.0.0.1` olarak kaldı.
- Gerçek loopback HTTP smoke: `health=200`, `GET /api/datasets=200`, `Cache-Control: no-store`, katalog response’unda path anahtarı yok; `PUT /api/dataset-selection` mevcut cache olmadığı için `409 DATASET_CACHE_MISSING` döndürdü.

## Açık sınırlar

Bu fazda frontend katalog ekranı, download/progress/cancel/retry job’ı, kalıcı dataset/import kaydı, checksum refresh, authentication ve testnet yoktur. UI’ye geçmeden önce görsel araştırma gerekirse kullanıcıya anonim prompt verilecektir. `VERIFIED`, CSV’nin canonical ekonomik kalite raporunun tamamlandığı değil, cache artifact bütünlüğünün doğrulandığı anlamına gelir.

Durum: `COMPLETE / LOCAL_PASS`; bağımsız inceleme: `NOT_RUN`.
