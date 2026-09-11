# P1.08.g — Config revision snapshot binding

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Bağımsız review: `NOT_RUN`  
Production readiness: `NO`

## Karar

Lifecycle event’in yalnız revision ID taşıması yeterli bir immutable config authority değildi. Bu mikro fazda config editing veya API açılmadan, doğrulanmış config’in canonical JSON snapshot’ı ve SHA-256 kimliği oluşturuldu; ayrı lifecycle store bu revision kaydını event append/replay için zorunlu tuttu.

## Uygulanan dar dilim

- `ConfigRevision`, geçerli offline `Config` snapshot’ını canonical JSON olarak doğrular.
- Canonical serialization `ensure_ascii=True`, `sort_keys=True`, sıkıştırılmış ayraçlar ve `allow_nan=False` kurallarını kullanır.
- Snapshot SHA-256 değeri yeniden hesaplanarak verilen hash ile eşleştirilir.
- Eşdeğer field order aynı snapshot/hash üretir; config değeri değişince revision hash’i değişir.
- Lifecycle event append sırasında event revision ID’si, caller’ın verdiği `ConfigRevision.revision_id` ile eşleşmek zorundadır.
- Aynı revision ID store’da farklı snapshot/hash ile tekrar kullanılamaz.
- Restart replay, event’in bağlı revision snapshot’ının varlığını ve geçerliliğini kontrol eder.
- Economic `Store` şeması değiştirilmedi; config revision tablosu yalnız ayrı lifecycle store’a aittir.

## Kanıt zinciri

1. **İddia:** Eşdeğer config mapping sırası aynı revision identity üretmelidir.  
   **RED:** Yeni `config_revision` modülü yokken test import error verdi.  
   **GREEN:** Aynı config farklı field order ile aynı immutable `ConfigRevision` üretildi.

2. **İddia:** Config değişikliği aynı revision snapshot’ı olarak kabul edilmemelidir.  
   **Kontrol:** `target_quote` değiştirilen geçerli config snapshot’ı.  
   **Sonuç:** Snapshot JSON ve SHA-256 farklı oldu.

3. **İddia:** Lifecycle store bir revision ID’yi farklı snapshot ile yeniden bağlamamalıdır.  
   **Kontrol:** Aynı revision ID’ye farklı config snapshot ile ikinci event append edildi.  
   **Sonuç:** `CONFIG_REVISION_CONFLICT` döndü; mevcut history değişmedi.

4. **İddia:** Event ile config revision ID uyuşmazlığı sessizce kabul edilmemelidir.  
   **Farklı kontrol:** Event `config-revision-2`, caller snapshot `config-revision-1` ile gönderildi.  
   **Sonuç:** `LIFECYCLE_EVENT_REVISION_CONFLICT` döndü.

5. **Genel doğrulama:** Kanonik regresyon `167/167 PASS`; `compileall PASS`; `tools/check_workspace.py PASS` (`active_python_files: 69`).

## Bilinçli olarak yapılmayanlar

- Config editor, revision oluşturma API’si veya UI.
- COPY’nin persistent config clone davranışı.
- Event/config hash’in historical run veya economic journal ile birleştirilmesi.
- Terminal event sonrası event policy, cooldown ve effective-time kararları.
- Pause-order policy, shared account/reserve, economic reducer veya posting.

Bu nedenle lifecycle snapshot binding local ve non-economic bir authority’dir; P1.08’in kullanıcıya açık multi-deal ürünü tamamlanmış sayılmaz.

## Değişen dosyalar

- `src/dcabot/application/config_revision.py`
- `src/dcabot/persistence/lifecycle_store.py`
- `tests/test_config_revision.py`
- `tests/test_lifecycle_store.py`

## Sonraki tek iş

`P1.08.h` lifecycle terminal/cooldown policy contract: terminal event sonrası yeni event reddi ve historical effective-time cooldown sınırını saf contract/test olarak tanımlayacaktır.
