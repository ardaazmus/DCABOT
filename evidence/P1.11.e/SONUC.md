# P1.11.e — Reservation fill/release ve economic Store binding karar kapısı

## Durum

`DEFERRED / NO-GO / LOCAL_PASS`; bu mikro fazda production kodu değişmedi.

## Kontrol sonucu

P1.11.d’de eklenen `ReservationLedger` yalnız aktif quote-asset reservation’ı ve account version’ı kalıcı tutuyor. Mevcut core `Store` ise `FILL`/`ORDER_FINAL` event’lerini ayrı SQLite journal’da, account veya reservation owner alanları olmadan saklıyor. Bu iki sınır arasında güvenli fill/release adapter’ı oluşturmak için gereken ekonomik sahiplik ve transaction sözleşmesi mevcut değil.

- `FILL` miktarı base asset’tir; reservation miktarı quote asset’tir.
- Fill’in rezervden düşeceği quote notional; fee, slippage ve varsa kalan reserve hesabının hangi exact fiyat/yuvarlama sahibiyle yapılacağı tanımlı değildir.
- `ORDER_FINAL` içinde `reservation_id`, `account_id`, reserved amount ve released amount yoktur; cancellation yalnız gözlem olarak kalır.
- Partial fill, late fill, UNKNOWN ve conflicting duplicate durumlarında reserve transferi için core event kimliği ile reservation identity aynı transaction içinde değildir.
- `ReservationLedger` ile mevcut economic `Store` ayrı SQLite veritabanlarıdır. İki ayrı connection arasında atomic reservation + economic posting iddiası kurulamaz.

## Uygulama kararı

Fill/release metodu, cross-database transaction adapter’ı, core event şeması değişikliği, quote/base dönüşümü veya UI/account toplamı eklenmedi. Eksik sözleşmeyi varsayımla doldurmak; double reserve, yanlış release, yanlış fee/PnL ve late-fill sonrası yanlış kullanılabilir bakiye riski doğurur.

Bu nedenle P1.11.e `DEFERRED/NO-GO` olarak bırakıldı. P1.11.d’nin yerel persistence/version kanıtı geçerlidir; ancak shared-account production readiness hâlâ `NO`.

## Kanıt zinciri

- Kaynak araştırma: `docs/P1_KRITIK_ARASTIRMA_FINAL/08_P1.11_SHARED_ACCOUNT.md`; local code binding açıkça `LOCAL_CODE_REQUIRED`.
- Local inspection: `src/dcabot/domain/engine.py`, `src/dcabot/persistence/store.py`, `src/dcabot/application/account_reservation_ledger.py`.
- Mevcut son kod doğrulaması: `uv run --frozen python tools/run_checks.py` → `241/241 PASS`.
- Workspace doğrulaması: `uv run --frozen python tools/check_workspace.py` → `PASS`; `102` aktif Python dosyası.
- Bağımsız karar kontrolü: farklı asset/unit ve iki ayrı SQLite transaction sınırı nedeniyle fill/release ekonomik eşleme kurulamadı; bu yüzden kod değişikliği yapılmadı.

## Yeniden açma koşulları

P1.11.e ancak şu alanlar araştırma + local test ile dondurulduğunda yeniden açılabilir: reservation’ın hangi order/intent kimliğine bağlandığı; base→quote commitment formülü; fee/slippage/rounding owner; partial fill ve cancel release miktarları; late/unknown/conflict authority; tek veritabanı transaction veya kanıtlanmış outbox/recovery protokolü; aynı transaction’da dedup ve economic posting.

## Sonraki tek iş

`P1.12.a` — spot ve lineer futures için ürün/settlement/fee/funding/teminat modelinin karar kapısı. P1.11.e, gerekli ortak transaction ve identity sözleşmeleri oluştuğunda yeniden ele alınacaktır.
