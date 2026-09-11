# P1.03.c — yerel katalog listeleme ve seçme sonucu

## Kapsam

Bu dilim P1.03.b’de doğrulanan public cache’i yeniden indirmeden kataloglar. Katalog yalnız uygulama içinde explicit olarak tanımlanan dataset definition’ları görür; serbest cache JSON’u veya serbest URL taranmaz.

İlk tanım:

- Dataset ID: `binance_spot_klines_v1:BTCUSDT:1h:2025-01-01`
- Source: `binance_spot_klines_v1`
- Sembol/interval: `BTCUSDT` / `1h`
- Dönem: `[2025-01-01, 2025-01-02)`
- Artifact: `BTCUSDT-1h-2025-01-01.zip`
- Expected SHA-256 ve byte: immutable P1.03.b planından gelir

## Uygulama

- `PublicDatasetDefinition`: dataset kimliği ile immutable download planını ve explicit dönem/sembol/interval bilgisini bağlar.
- `PublicDatasetCatalog.list_entries()`: `MISSING`, `CORRUPT` veya `VERIFIED` cache bütünlük durumunu, hash ve byte bilgisini deterministik listeler.
- `PublicDatasetCatalog.select(dataset_id)`: bilinmeyen, eksik veya bozuk dataset’i reddeder; yalnız `inspect_cached_artifact` tarafından doğrulanmış ZIP path’ini ve iç CSV adını parser/application portuna aktarır.
- Cache dosyasının yalnız metadata’sına güvenilmez; expected hash, byte, ZIP path/symlink/CRC ve metadata birlikte doğrulanır.

## Kanıt

- `tools/run_checks.py`: PASS, 60 test.
- `tools/check_workspace.py`: PASS; `YEDEK_ESKI_PROJE` okunmadı/çalıştırılmadı.
- `compileall`: PASS.
- Yeni odak testleri: cache yokken `MISSING`, başarılı indirme sonrası `VERIFIED` ve selection path, cache tampering sonrası `CORRUPT`, bilinmeyen/bozuk seçim reddi.

## Açık sınırlar

Bu dilimde HTTP endpoint, frontend ekranı, progress/cancel/retry job orchestration, kalıcı import kaydı ve canonical Binance CSV normalizasyonu yoktur. Listeleme/seçme API’si P1.03.d’nin tek işidir. `VERIFIED`, CSV’nin ekonomik kalite raporunun tamamlandığı anlamına gelmez; bu aşamada yerel artifact bütünlüğünün doğrulandığı anlamına gelir.

Durum: `COMPLETE / LOCAL_PASS`; bağımsız inceleme: `NOT_RUN`.
