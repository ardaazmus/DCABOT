# P1.12.d — Futures fee/funding persistence ve core Store binding karar kapısı

## Durum

`DEFERRED / NO-GO / LOCAL_PASS`; bu mikro fazda production kodu değişmedi.

## Mevcut local davranış

`src/dcabot/persistence/store.py` aynı SQLite transaction içinde generic `FILL` fee, `FUNDING` ve balanced postings tutabiliyor; batch id tekrarında aynı payload idempotent, farklı payload conflict oluyor. Bu, CORE01 offline journal kanıtıdır; linear futures event persistence’inin tamamı değildir.

P1.12.c’deki `LinearLedgerEvent` sözleşmesi ise `event_id`, `event_type`, `effective_time_us`, settlement asset ve signed amount taşıyor. Mevcut core `engine.apply` event şeması:

- `FUNDING` için yalnız `amount/asset` kabul ediyor; effective time, product, position ve profile owner yok.
- `FILL` için base/contract quantity, price, fee ve fee asset var; futures contract size, settlement profile, mark authority ve position identity yok.
- `Store` state’i CORE01’in mevcut long-only `Position` tipini yeniden oynatıyor; linear short/futures margin state’i taşımıyor.
- Yeni alanları strict `_fields` sözleşmesine doğrudan eklemek eski event replay’ini, schema/hash kimliğini ve mevcut audit davranışını etkiler.

## Uygulama kararı

Yeni futures event’lerini mevcut Store’a bağlayan adapter, migration veya gizli alan eşlemesi eklenmedi. İki ayrı ledger’ı sonradan birleştiren “transaction tamam” yaklaşımı da reddedildi; reserve/fill/posting exactly-once iddiası aynı owner ve transaction sınırında kanıtlanmalıdır.

## Kanıt zinciri

- Local inspection: `src/dcabot/domain/engine.py`, `src/dcabot/persistence/store.py`, `src/dcabot/application/linear_futures_math.py`.
- Mevcut son kod regresyonu: `uv run --frozen python tools/run_checks.py` → `251/251 PASS`.
- Mevcut generic Store kontrolleri: funding/fee posting, restart/replay, duplicate execution, conflict ve per-event audit testleri PASS.
- P1.12.c bağımsız Decimal oracle: `gross - fee + funding` hesabı PASS.
- Workspace: `uv run --frozen python tools/check_workspace.py` → `PASS`; son P1.12.c ölçümü `106` aktif Python dosyası.

## Blokaj ve yeniden açma koşulları

P1.12.d; versioned futures event schema, event identity/effective-time policy, linear position reducer, fee/funding posting owner, old CORE01 replay compatibility/migration strategy ve aynı transaction’da dedup + posting kararı olmadan açılamaz. Bu koşullar çözülmeden UI/API veya persistent futures sonucu yayınlanamaz.

## Sonraki tek iş

`P1.12.e` — isolated margin terminolojisi ve seçilmiş venue-profile kapsamı için karar kapısı; liquidation generic formül olarak açılmayacak.
