# P1.08.b — Lifecycle config-revision binding contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Bağımsız review: `NOT_RUN`  
Production readiness: `NO`

## Karar

P1.08 araştırması, COPY’nin yeni immutable config revision’dan yeni deal oluşturması gerektiğini; aktif deal’in mutate edilmemesini söylüyor. Ancak gerçek config-revision persistence/store bu mikro fazın local code scope’unda yoktur. Bu nedenle yalnız saf in-memory kimlik sınırı uygulandı; config içeriği, hash veya snapshot üretilmedi.

## Uygulanan dar dilim

- `copy_deal_lifecycle(source, new_deal_id, new_config_revision_id)` yalnız yeni kimliklerle `DRAFT` projection döndürür.
- Kaynak lifecycle’ın durum, deal kimliği, config-revision kimliği veya event sayacı değişmez.
- Kaynak deal kimliği ya da kaynak config-revision kimliği yeniden kullanılırsa ayrı fail-closed hata kodları döner.
- Yeni projection `event_sequence=0` ile başlar; COPY ekonomi event’i, position, reserve veya order üretmez.

## Kanıt zinciri

1. **İddia:** COPY aktif deal’i mutate etmeden yeni deal/revision kimliğiyle başlayabilir.  
   **RED:** `copy_deal_lifecycle` importu bulunmadığı için kanonik suite `ImportError` ile başarısız oldu.  
   **GREEN:** Kaynak `RUNNING` kaldı; kopya `deal-2/config-revision-2/DRAFT/0` döndü.

2. **İddia:** COPY kaynak kimliği yeniden kullanarak yeni deal görünümü üretemez.  
   **Kontrol:** Aynı deal kimliği ve aynı config-revision kimliği için iki ayrı negatif test.  
   **Sonuç:** Sırasıyla `COPY_DEAL_ID_REUSED` ve `COPY_CONFIG_REVISION_ID_REUSED` ile reddedildi.

3. **Farklı kontroller:** Kanonik regresyon `155/155 PASS`; `compileall PASS`; `tools/check_workspace.py PASS` (`active_python_files: 61`).

## Bilinçli olarak yapılmayanlar

- Config revision içeriğinin immutable snapshot/hash/store’u.
- Persistent COPY event’i, restart/reopen/replay, event identity/dedupe ve conflict handling.
- Cooldown, PAUSED order policy, stop-after-deal/cancel/flatten.
- API/UI, shared-account isolation/reserve ve ekonomik reducer mutation.

Bu nedenle COPY kullanıcıya açık, kalıcı veya ekonomik olarak etkili bir özellik değildir.

## Değişen dosyalar

- `src/dcabot/application/deal_lifecycle.py`
- `tests/test_deal_lifecycle.py`

## Sonraki tek iş

`P1.08.c` mevcut offline store’un lifecycle event identity, duplicate/conflict ve restart/replay authority’si için dar local inventory’dir; bu adım yeni persistent schema veya API yazmayacaktır.
