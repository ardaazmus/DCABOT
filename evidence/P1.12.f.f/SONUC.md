# P1.12.f.f — Futures DCA durable event journal/replay sonucu

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`

## Kapsam

`src/dcabot/persistence/futures_dca_event_store.py`, P1.12.f.d’deki Futures
DCA fill event contract’ını ayrı, bounded SQLite journal’a bağlar. Store
canonical JSON + SHA-256 checksum, sabit deal/config scope, ardışık local
sequence ve exact duplicate/conflict kurallarını restart sonrasında yeniden
oynatır.

Bu local event sequence’i Binance transport sequence’i değildir. Store
reservation ledger, position/economic Store, fill-release veya venue adapter
ile aynı transaction sınırında değildir; canlı emir ve hesap mutation authority
taşımaz.

## Kabul kanıtı

- Odak test: `4/4 PASS`.
- Restart sonrası event history exact replay edildi.
- Exact duplicate idempotent; event conflict, store scope/sequence ihlali,
  checksum ve metadata bozulması fail-closed doğrulandı.
- Tam proje kontrolü `tools/run_checks.py`: `524/524 PASS`.
- Compile/workspace kontrolleri tam proje kontrolünde PASS.

## Açık sınır

Reservation commit’i ile event append, fill sonrası reserve release, position
commitment transferi ve economic posting atomik biçimde bağlanmadı. Gerçek
venue event sequence/catch-up, fee/funding binding ve DCA lifecycle/exit
sonraki mikro-fazlardır. Bu kanıt production shared-account concurrency veya
Binance hesap yetkisi kanıtı değildir.
