# P2.04 — Güvenlik taraması sonucu

**Tarih:** 2026-09-15
**Durum:** LOCAL_PASS / COMPLETE_WITH_LIMITATION
**Scan:** `7b1e7a45-5d44-48f8-bf81-4de8eba3b076`

## Kapsam

525 dosyalık yerel checkout; API kaynak bütçeleri, durable reconciliation ve authority admission, credential/live-mutation sınırı, public artifact doğrulaması, frontend veri akışı ve test/runtime tedarik zinciri incelendi.

Canlı venue çağrısı, credential kullanımı, imzalı istek, emir mutasyonu, commit veya public push yapılmadı. Bağımsız delegated baseline worker bu oturumda kullanılamadı; sonuç parent source audit ve yerel odaklı doğrulama kapsamındadır.

## Bulgular ve düzeltme

### LOW — historical validation gövdesi erken sınırlandırılmıyordu

Tarama snapshot’ında `/api/historical-runs/validate` için özel middleware, `request.body()` ile tüm gövdeyi aldıktan sonra 4 KiB kontrolü yapıyordu. `Content-Length` bulunmayan chunked isteklerde bu, yerel worker’ın gereksiz/büyük bellek tüketmesine neden olabilirdi (CWE-400). Endpoint loopback kapsamındadır; bu nedenle önem seviyesi **LOW** olarak belirlendi.

Kök neden düzeltildi:

- endpoint ortak `RequestBodyLimitMiddleware` streaming yoluna alındı;
- özel tam-gövde `request.body()` middleware’i kaldırıldı;
- `tests/api/test_request_limits.py::test_validation_rejects_oversized_chunked_body_without_content_length` eklendi;
- odaklı istek-limit paketi **9/9 PASS**.

Tarama, düzeltmeden önce alınan snapshot üzerinde tamamlandı; bu nedenle rapordaki bulgu geçmiş durumun kanıtıdır. Mevcut çalışma ağacındaki düzeltme ayrıca odaklı testle doğrulanmıştır.

## Açık sınırlamalar

- Tam Python regresyonu **457/457 PASS**, optimize regresyon **457/457 PASS**, compileall **PASS**, workspace **PASS** ve release-manifest check **PASS** olarak tamamlandı.
- Tarama, loopback dışı reverse-proxy/deployment maruziyetini doğrulamadı.
- Frontend browser/E2E, ekran okuyucu, high-contrast ve canlı API doğrulaması hâlâ yapılmadı.

## Kabul kararı

**Kabul:** Düşük önem seviyeli bulgu giderildi ve odaklı regresyonla kapatıldı.
**P2.04 tam kapanış:** `COMPLETE_WITH_LIMITATION` — yerel kabul kapıları geçti; bağımsız delegated baseline ve browser/E2E erişilebilirlik doğrulaması bu çalışma kapsamında yok.
