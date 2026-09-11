# P1.08.c — Lifecycle persistence/replay authority inventory

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Bağımsız review: `NOT_RUN`  
Production readiness: `NO`

## Karar

Bu mikro faz yalnız mevcut yerel kayıt katmanlarının neyi garanti ettiğini ayırmak için yapıldı. Yeni persistent schema, lifecycle adapter, replay implementation, API/UI veya ekonomik davranış eklenmedi.

## Yerel bulgular

### Ekonomik offline journal

`src/dcabot/persistence/store.py` içindeki `Store` şu authority’lere sahiptir:

- `batches.id` ile aynı batch request’inin tekrarını idempotent biçimde tanır; farklı request conflict üretir.
- `events.execution_id` yalnız `FILL` için unique’tir; aynı ekonomik payload tekrarında ikinci ekonomik etki oluşmaz, farklı payload conflict üretir.
- Event, posting ve incident işlemleri SQLite transaction sınırında tutulur.
- Restart sonrası ekonomik event’ler sıralı yüklenir ve reducer’a tekrar uygulanır; posting audit’i ayrıca kontrol edilir.

Bu kapsam ekonomik event journal’ıdır. Deal lifecycle status, config-revision snapshot, lifecycle event cursor veya lifecycle event identity alanı taşımaz.

### Historical run store

`src/dcabot/persistence/historical_runs.py` içindeki `HistoricalRunStore` şu authority’lere sahiptir:

- `source_execution_id` unique olarak aynı historical capture retry’sini tanır.
- Aynı source execution farklı sonuç kimliği/payload ile gelirse conflict üretir.
- İlk kayıt immutable historical result olarak saklanır; list/detail yeniden okunabilir.

Bu kapsam persisted simulation result’ıdır. Lifecycle transition sırası, pause/resume event’i, COPY ilişkisi veya aktif config revision rehydration authority’si değildir.

### Synthetic replay yolu

`src/dcabot/application/service.py` synthetic tick replay’i tick ID’lerini batch identity olarak kullanır; input içindeki duplicate tick ID reddedilir ve aynı batch tekrarında journal idempotency devreye girer. Bu yol ekonomik MARK/INTENT/FILL/ORDER_FINAL akışını replay eder; lifecycle event replay etmez.

## Kanıt zinciri

1. **İddia:** Mevcut store ekonomik duplicate/conflict davranışına sahiptir.  
   **Kontrol:** Mevcut `test_engine_store.py` duplicate execution, conflicting execution, posting rollback, restart ve replay testleri.  
   **Sonuç:** Bu ekonomik kapsamın testleri kanonik suite içinde PASS.

2. **İddia:** Historical run kayıtları source execution retry/conflict davranışına sahiptir.  
   **Kontrol:** Mevcut historical simulation save retry/conflict testleri.  
   **Sonuç:** İlk save ve aynı execution retry davranışı testlerle PASS.

3. **İddia:** Bu authority’ler lifecycle persistence değildir.  
   **Farklı kontrol:** Store tabloları ve yazma/okuma çağrı zinciri incelendi; alanlar ekonomik event/posting veya historical result ile sınırlı, lifecycle event kimliği/status cursor/deal lifecycle tablosu yok.

4. **Çalışma doğrulaması:** Son kanonik kod doğrulaması `155/155 PASS`; `compileall PASS`; `tools/check_workspace.py PASS`. Bu mikro fazda kod değişmediği için bu sonuçlar yeniden etiketlenmedi.

## Bilinçli olarak yapılmayanlar

- Lifecycle event identity, canonical payload/hash ve duplicate/conflict sonucu.
- Lifecycle event sıralama/cursor, restart rehydration ve lifecycle replay.
- Deal/config-revision isolation’ın persistent kanıtı.
- Yeni SQLite schema veya mevcut ekonomik journal’a lifecycle event karıştırılması.
- API/UI, cooldown, pause-order policy, shared account/reserve ve ekonomik posting.

Bu nedenle P1.08’in kalıcı duraklatma, yeniden açma veya çoklu deal çalıştırma davranışları henüz production-ready değildir.

## Sonraki tek iş

`P1.08.d` lifecycle event identity contract: ekonomik journal’dan ayrı, önce saf contract/test seviyesinde event kimliği, duplicate/conflict ve sıralama sınırını tanımlayacaktır.
