# P1.12.f.d — Futures DCA event identity/sequence sonucu

**Tarih:** 2026-09-16  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`

## Kapsam

`src/dcabot/application/futures_dca_event_contract.py` gözlemlenmiş Futures
DCA fill’lerini yerel `event_id`, deal/config revision scope’u ve ardışık
`event_sequence` ile sınıflandırır. Aynı event kimliğinin exact duplicate’i
idempotent’tir; farklı payload conflict’tir. Aynı execution kimliği farklı bir
event’te tekrar kullanılamaz.

Bu `event_sequence` yerel kabul geçmişinin sırasıdır; Binance WebSocket veya
REST transport sequence’i olduğu varsayılmaz. Contract yalnız in-memory
kimlik/sıra kontrolüdür; ekonomik fill projection, persistence, venue adapter
ve shared-account reservation authority eklemez.

## Kabul kanıtı

- Odak test: `4/4 PASS`.
- Aynı scope ardışık event, exact duplicate, event conflict, execution reuse,
  scope conflict ve sequence gap fail-closed davranışları doğrulandı.
- Tam proje kontrolü `tools/run_checks.py`: `517/517 PASS`.
- Compile/workspace kontrolleri tam proje kontrolünde PASS.

## Açık sınır

Shared-account reservation binding, persistent event journal/replay, gerçek
venue sequence/catch-up, fee/funding binding ve lifecycle/exit sonraki
mikro-fazlardır. Bu kanıt canlı Binance event tüketimi veya emir yetkisi
anlamına gelmez.
