# P1.17.c — Offline observation replay adapter

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Production readiness: `NO`  
Tarih: 2026-09-10

## 1. Kapsam

P1.17.b’de doğrulanan normalize edilmiş `PublicObservation` kayıtları, yalnız caller tarafından verilen deterministic zamanlar ve explicit resync index’leriyle bounded local replay akışına bağlandı.

Bu dilim:

- network veya WebSocket/REST client kullanmaz;
- private credential, account, gerçek emir veya testnet kullanmaz;
- observation’ı candidate, order, fill, balance, reserve, PnL veya historical run sonucuna dönüştürmez;
- persistence/API/UI eklemez;
- historical run/result identity üretmez veya overwrite etmez.

## 2. RED kontrolü

Replay testleri eklenmeden önce beklenen API yoktu:

```text
ImportError: cannot import name 'replay_observations'
```

Bu kontrol, replay davranışının mevcut kodda zaten varmış gibi kabul edilmediğini gösterdi.

## 3. Minimum uygulama

`src/dcabot/data_adapters/public_feed.py` içine `ReplayResult` ve `replay_observations(...)` eklendi:

- input yalnız immutable `PublicObservation` tuple’ıdır;
- replay en fazla `1,024` observation kabul eder;
- her observation için caller-supplied `now_time_us` zorunludur; wall clock okunmaz;
- sequence gap veya out-of-order sonrası yeni event, explicit resync index’i olmadan kabul edilmez;
- exact duplicate no-op, conflicting duplicate fail-closed kalır;
- sonuç yalnız `cursor`, `outcomes` ve `accepted_count` taşır;
- `run_id`, `result_id`, `pnl`, `order`, `fill` alanları yoktur.

## 4. Test ve bağımsız kontrol

- Odak testleri: `11/11 PASS` (`tests/test_public_feed_contract.py`).
- Bağımsız replay oracle: `INDEPENDENT_REPLAY_ORACLE=PASS`.
- Tam proje regresyonu: `336/336 PASS` (`tools/run_checks.py`).
- `compileall`: `PASS`.
- Workspace kontrolü: `PASS`, `140` aktif Python dosyası.

Kontrol edilen davranışlar:

1. accepted observation + duplicate replay;
2. sequence gap sonrası quarantine;
3. explicit resync index’iyle yeni segment;
4. replay sonucunun historical/economic identity taşımaması;
5. deterministic replay zamanı ve bounded input.

## 5. Sonuç ve sınır

P1.17.c `LOCAL_PASS` olarak kapanabilir. Salt-okunur observation replay sınırı kanıtlandı; bu, canlı feed’in veya simulated execution’ın çalıştığı anlamına gelmez.

Bir sonraki tek mikro faz: `P1.17.d — Venue-specific transport mapping and reconnect/catch-up research gate`. Coinbase/Bybit resmi belgelerinden seçilecek tek bir public profile için REST-vs-WebSocket payload mapping, sequence/reconnect/catch-up ve stale policy kanıtı tamamlanmadan canlı adapter veya paper-trading route açılmayacaktır.
