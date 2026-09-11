# P1.11.d — Atomic reservation persistence and version boundary

## Durum

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; production readiness `NO`.

## Uygulanan en küçük davranış

`src/dcabot/application/account_reservation_ledger.py` içinde yalnız yerel ve açıkça ayrılmış bir SQLite reservation ledger eklendi:

- Account/asset kapasitesi ve account version kalıcı olarak tutulur.
- Reservation owner kapsamı `account_id/product_id/position_mode/deal_id/allocation_id` ile saklanır.
- `BEGIN IMMEDIATE` içinde kapasite, aktif toplam, reservation kaydı ve version artışı tek commit sınırındadır.
- `available_after = capacity - Σactive_reservations - requested` exact olarak hesaplanır; finansal değerler dışarıda decimal string, içeride `Fraction` olarak kalır.
- Exact duplicate aynı daha önce kaydedilmiş `ReservationCommit` sonucunu döndürür; farklı payload aynı kimlikle kullanılırsa fail-closed reddedilir.
- Stale account version, kapasite aşımı, eksik kapasite ve desteklenmeyen/başka SQLite dosyası güvenli biçimde reddedilir.
- Reopen sonrası kapasite version’ı, aktif reservation seti ve commit metadata’sı değişmeden okunur.

Bu mikro fazda fill/release, position commitment transferi, economic posting, API/UI veya mevcut ana `Store` ile binding eklenmedi.

## Doğrulama zinciri

- Önceki RED: ledger modülü yokken import failure; mevcut testler korunuyordu.
- GREEN: `tests/test_account_reservation_ledger.py` ve tam paket toplam `241/241 PASS`.
- Farklı bağımsız kontrol: production ledger import etmeden Fraction hesabı `PASS` (`100 - 20 - 10 - 30 = 40`, version `+1`).
- Python 3.13 compile/workspace: `uv run --frozen python tools/check_workspace.py` → `PASS`; `102` aktif Python dosyası.
- Dosya bütünlüğü kontrolü: mevcut unrelated SQLite dosyası ledger olarak sahiplenilmiyor ve içeriği değişmiyor.
- İkinci ledger instance kontrolü: stale version ikinci commit’i engelliyor; güncel version ile sonraki commit exact ilerliyor.

## Araştırma temeli

`docs/P1_KRITIK_ARASTIRMA_FINAL/08_P1.11_SHARED_ACCOUNT.md` account-level reservation, optimistic version conflict, transaction/locking ve restart/replay gereksinimlerini destekler. Yerel uygulama bu gereksinimin yalnız persistence + version-guard bölümünü kanıtlar.

## Açık sınır ve üretim kararı

Bu SQLite ledger mevcut ekonomik `Store`/core reducer’a bağlı değildir; bu nedenle production shared-account reservation hazır kabul edilmez. Gerçek üretim kabulü için aynı transaction içinde reservation + position commitment + fill/release + economic posting + dedup/replay owner’larının bağlanması, process/multi-writer testleri ve bağımsız review gerekir. UI bu ledger’dan bağımsız ekonomik hesap yapamaz.

## Sonraki tek iş

`P1.11.e` — reservation fill/release, position commitment transferi ve mevcut economic Store binding karar kapısı.
