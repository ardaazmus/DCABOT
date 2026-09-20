# P1.12.f.e — Futures DCA shared-account reservation binding sonucu

**Tarih:** 2026-09-17  
**Durum:** `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`

## Kapsam

`src/dcabot/application/futures_dca_reservation.py`, Futures DCA fill
projection’ındaki exact pending quote tutarını mevcut immutable
`AccountReservation` ve `project_reservation` projection’ına bağlar. Settlement
asset olarak yalnız seçilmiş `USDT` profile kapsamı kabul edilir; position mode
Futures profile ile eşleşmelidir.

Bu bir candidate projection’dır. SQLite reservation commit’i, fill/release
atomicity’si, gerçek hesap bakiyesi, economic Store binding, venue adapter ve
canlı emir authority taşımaz.

## Kabul kanıtı

- Odak test: `3/3 PASS`.
- Pending quote `0.0198 USDT` matching kapasiteye exact bağlandı.
- Yanlış asset, yanlış position mode, kapasite aşımı ve stale account version
  fail-closed doğrulandı.
- Tam proje kontrolü `tools/run_checks.py`: `520/520 PASS`.
- Compile/workspace kontrolleri tam proje kontrolünde PASS.

## Açık sınır

Reservation persistence/commit, fill ile reserve release atomicity’si, event
journal/replay, gerçek account snapshot, fee/funding binding ve lifecycle
sonraki mikro-fazlardır. Bu kanıt shared-account concurrency veya Binance
hesap yetkisi kanıtı değildir.
