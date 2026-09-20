# P1.12.f.h.al — CORE01 intent identity authority contract

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`  
**Legacy migration/publish:** `NOT_APPLICABLE`

## Uygulanan minimum dikey dilim

- CORE01 `Order` artık opsiyonel fakat açık bir `intent_id` taşıyabiliyor;
  kimlik yalnız explicit `INTENT` event’inden geliyor, sentetik kimlik
  üretilmiyor.
- Existing INTENT event payload’ları geriye dönük korunuyor; yeni explicit
  identity verilirse order scope ile birlikte CORE01 state’e taşınıyor.
- Spot binding state serializer’ı intent identity’yi yeni kayıtlarda koruyor;
  intent alanı bulunmayan eski state payload’ları okunabilir kalıyor.
- P1.12.f.h.ak admission oracle’ı artık yalnız `core_order_id`, role, side,
  exact limit ve `core_order_intent_id` birlikte eşleşirse `ADMISSIBLE` dönüyor;
  eksik veya farklı identity `BLOCKED` kalıyor.
- Bu faz yalnız identity/authority sözleşmesidir. Futures DCA event’inin CORE01
  `FILL` event’ine çevrilmesi, economic posting, Store binding, venue veya canlı
  mutation açılmadı.

## Kanıt

- Futures DCA mapping/admission odak testleri: `8/8 PASS`.
- Tam proje: `tools/run_checks.py` — `587/587 PASS`.
- `compileall`: `PASS`.
- Workspace: `PASS`, `233` aktif Python dosyası; backup layout
  `EMPTY_OR_NOT_PLACED`.
- `git diff --check`: whitespace hatası yok; yalnız mevcut LF/CRLF dönüşüm
  uyarıları görüldü.
- Canlı Binance emri, mutation, mainnet, secret, economic posting veya
  CORE01 Store binding çalıştırılmadı.

## Karar

CORE01 intent identity authority’si artık state/order sözleşmesinde açıkça
temsil edilebilir ve restart sonrası korunabilir. Exact identity olmadan
admission hâlâ fail-closed’tur; bu faz ekonomik kabul iddiası taşımaz.

## Sıradaki tek iş

`P1.12.f.h.am` — explicit admitted mapping’i Futures DCA fill envelope ve
CORE01 economic `FILL` boundary’sine bağlayan salt-offline karar kapısı.
