# P1.08.a — Lifecycle authority local inventory

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Bağımsız review: `NOT_RUN`  
Production readiness: `NO`

## Karar

P1.08 dış araştırması yerel kod incelemesi yapmadığını ve LCR-02 ile local authority doğrulaması istediğini açıkça belirtiyordu. Bu nedenle rapordaki lifecycle sözleri doğrudan ürün davranışı olarak alınmadı. Mevcut ekonomik reducer ile karışmayan, yalnız in-memory ve non-economic bir projection en küçük güvenli dilim olarak uygulandı.

Araştırmadaki `STARTED/RUNNING` ile `STARTING/ACTIVE` adlandırmaları çeliştiğinden yeni ara durumlar türetilmedi. Bu dilimde kalıcı durum tablosu `DRAFT -> RUNNING <-> PAUSED -> COMPLETED | ABORTED | FAILED` olarak daraltıldı; `START` durum değil olaydır.

## Uygulanan dar dilim

- `DealLifecycle` immutable projection’ı deal kimliği, config-revision kimliği, durum ve monoton event sequence taşır.
- Sadece açık transition tablosundaki `START`, `PAUSE`, `RESUME`, `COMPLETE`, `ABORT` ve `FAIL` olayları kabul edilir.
- Deal/config-revision kimliği transition ile değişmez.
- Geçersiz bir event `LIFECYCLE_TRANSITION_INVALID` ile reddedilir ve kaynak projection değişmeden kalır.
- Modül economic reducer, persistence ve HTTP katmanını import etmez; ekonomik event veya posting üretmez.

## Kanıt zinciri

1. **İddia:** Lifecycle transition economic reducer’dan ayrı tutulabilir.  
   **Kontrol:** İlk RED çalıştırmada lifecycle modülü yoktu; test import aşamasında `ModuleNotFoundError` ile başarısız oldu.  
   **GREEN:** Saf modül eklendikten sonra declarative transition tablosu ve negatif transition testi geçti.

2. **İddia:** Aktif deal config revision’ını mutasyonsuz taşır.  
   **Kontrol:** DRAFT, RUNNING ve PAUSED başlangıçlarından her geçişte deal/config-revision kimliği ve sayaç kontrolü yapıldı.  
   **Sonuç:** Kimlikler sabit, sayaç tam bir arttı; geçersiz `DRAFT + RESUME` kaynak state’i değiştirmedi.

3. **Farklı kontroller:** Kanonik regresyon `153/153 PASS`; `compileall PASS`; `tools/check_workspace.py PASS` (`active_python_files: 61`). Kaynak modülünde economic reducer/persistence/server importu aranarak bağımlılık olmadığı doğrulandı.

## Bilinçli olarak yapılmayanlar

- Persistent lifecycle event günlüğü, restart/reopen/replay ve event identity/dedupe.
- Gerçek immutable config-revision store, COPY event’i veya yeni deal/revision üretimi.
- Cooldown ve historical `effective_time` politikası.
- PAUSED altında açık emir için KEEP_OPEN/CANCEL_REQUESTED/BLOCKED politikası.
- API/UI, toplu işlemler, shared-account isolation/reserve veya ekonomik mutation.

Bu sınırlar kapanmadan P1.08’in kullanıcıya birkaç deal çalıştırma, kopyalama veya kalıcı duraklatma sunduğu iddia edilmez.

## Değişen dosyalar

- `src/dcabot/application/deal_lifecycle.py`
- `tests/test_deal_lifecycle.py`

## Sonraki tek iş

`P1.08.b` lifecycle config-revision binding contract: COPY’nin aktif deal’i mutate etmeden yeni deal/revision üretme sınırını, persistence yazmadan, local contract ve RED -> GREEN testleriyle kapatacaktır.
