# P1.08.f — Persistent lifecycle record boundary

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Bağımsız review: `NOT_RUN`  
Production readiness: `NO`

## Karar

P1.08.c yerel envanteri mevcut ekonomik journal’ın lifecycle authority’si olmadığını gösterdi. Bu mikro fazda lifecycle kayıtlarının ekonomik `Store` tablolarına karıştırılmaması için ayrı, versioned ve yalnız lifecycle event kapsamlı SQLite store oluşturuldu.

## Uygulanan dar dilim

- `LifecycleStore.create(path)` mevcut dosyanın üzerine yazmaz; `open(path)` yalnız desteklenen metadata/schema ile açar.
- Store metadata’sı `offline-lifecycle-1` ve `NON_ECONOMIC_LIFECYCLE_ONLY` scope’unu taşır.
- Event append `BEGIN IMMEDIATE` transaction’ı içinde yapılır.
- Event ID, deal/config-revision scope ve sequence P1.08.d contract’ı ile kontrol edilir.
- Accepted event saf event-to-transition adapter ile doğrulanmadan kaydedilmez.
- Exact duplicate aynı immutable kayıtla tekrarlandığında `DUPLICATE` döner; yeni kayıt oluşmaz.
- Aynı ID farklı kayıt, invalid transition ve mevcut scope/sequence ihlali reddedilir.
- Reopen sonrası tüm event’ler adapter üzerinden replay edilerek aynı `DealLifecycle` projection/history yeniden kurulur.
- Row alanları ile serialized payload uyuşmazlığı `LIFECYCLE_RECORD_CORRUPT` ile fail-closed reddedilir.

## Kanıt zinciri

1. **İddia:** Lifecycle event’leri ekonomik journal’dan ayrı kalıcı sınırda tutulabilir.  
   **RED:** `lifecycle_store` modülü yokken store testleri import error verdi.  
   **GREEN:** Ayrı SQLite schema ve metadata ile store oluşturuldu; ekonomik `Store` modülüne tablo/alan eklenmedi.

2. **İddia:** Restart sonrası lifecycle projection aynı kalmalıdır.  
   **Kontrol:** START + PAUSE kaydedildi, store kapatıldı ve yeni instance ile açıldı.  
   **Sonuç:** Replay sonucu aynı `PAUSED` projection ve event history verdi.

3. **İddia:** Persistent duplicate ikinci lifecycle etkisi üretmemelidir.  
   **Kontrol:** Aynı event ID ve aynı immutable payload store’a tekrar gönderildi.  
   **Sonuç:** `DUPLICATE`, history tek kayıt.

4. **İddia:** Conflict, invalid transition ve bozuk record sessizce kabul edilmemelidir.  
   **Farklı kontrol:** Aynı ID farklı event, DRAFT + RESUME ve row/payload `event_type` uyumsuzluğu fixture’ları.  
   **Sonuç:** Conflict/transition hataları ve `LIFECYCLE_RECORD_CORRUPT` üretildi; geçerli kayıt zinciri bozulmadı.

5. **Genel doğrulama:** Kanonik regresyon `164/164 PASS`; `compileall PASS`; `tools/check_workspace.py PASS` (`active_python_files: 67`).

## Bilinçli olarak yapılmayanlar

- Config revision snapshot/hash ve lifecycle kaydına içerik bağlama.
- Lifecycle API/UI, saved-run entegrasyonu veya kullanıcıya açık multi-deal akışı.
- Cooldown, PAUSED order policy, stop-after-deal/cancel/flatten.
- Shared account/reserve, economic reducer, position veya posting.
- Schema migration, mevcut DB’ye lifecycle tablo ekleme veya ekonomik journal’ı yeniden kullanma.

Bu nedenle bu store bir production bot çalıştırma özelliği değil, sonraki config binding ve replay çalışmalarının kalıcı sınır prototipidir.

## Değişen dosyalar

- `src/dcabot/persistence/lifecycle_store.py`
- `tests/test_lifecycle_store.py`

## Sonraki tek iş

`P1.08.g` config revision snapshot binding: lifecycle event’in revision kimliğini immutable config snapshot/hash ile bağlayacaktır.
