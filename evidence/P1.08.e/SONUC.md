# P1.08.e — Lifecycle event-to-transition adapter

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Bağımsız review: `NOT_RUN`  
Production readiness: `NO`

## Karar

P1.08.d’de tanımlanan event kimliği/scope/sequence contract’ı ile P1.08.a’daki saf lifecycle transition projection’ı tek bir non-economic adapter’da bağlandı. Adapter persistence veya ekonomik reducer değildir.

## Uygulanan dar dilim

- Event önce mevcut lifecycle deal/config-revision scope’u ile eşleştirilir.
- History ile projection’ın sequence’i uyumsuzsa `LIFECYCLE_PROJECTION_OUT_OF_SYNC` döner.
- Event contract kabulü tamamlanmadan transition uygulanmaz.
- Geçerli yeni event hem projection’ı hem history’yi birlikte ilerletir.
- Exact duplicate aynı projection ve history ile `DUPLICATE` döner; ikinci transition uygulanmaz.
- Geçersiz lifecycle transition exception üretir; candidate history dışarı verilmez.
- Adapter ekonomik event, order, position, reserve veya posting üretmez.

## Kanıt zinciri

1. **İddia:** Kabul edilen event lifecycle projection’ını ve history’yi bir kez ilerletir.  
   **RED:** Adapter modülü bulunmadığı için kanonik suite import error verdi.  
   **GREEN:** START ile `DRAFT -> RUNNING`, PAUSE ile `RUNNING -> PAUSED`; history sequence 1, 2 oldu.

2. **İddia:** Exact duplicate ikinci transition üretmemelidir.  
   **Kontrol:** Kabul edilmiş START aynı immutable kayıtla tekrarlandı.  
   **Sonuç:** Projection ve history değişmeden `DUPLICATE` döndü.

3. **İddia:** Invalid transition event history’ye eklenmemelidir.  
   **Kontrol:** DRAFT durumuna `RESUME` event’i uygulandı.  
   **Sonuç:** `LIFECYCLE_TRANSITION_INVALID` üretildi; kaynak projection ve boş history korundu.

4. **Farklı kontrol:** Adapter source scope ve projection/history sequence uyumsuzluklarını transition öncesinde reddedecek şekilde sınırlandırıldı; ekonomik modüllere import bağımlılığı eklenmedi.

5. **Genel doğrulama:** Kanonik regresyon `161/161 PASS`; `compileall PASS`; `tools/check_workspace.py PASS` (`active_python_files: 65`).

## Bilinçli olarak yapılmayanlar

- Persistent lifecycle record/schema, restart/replay ve event dedupe’nin kalıcı uygulanması.
- Config revision snapshot/hash/store ve COPY persistence.
- Terminal event sonrası kalıcı lifecycle politikası, cooldown ve pause-order policy.
- API/UI, shared account/reserve, economic reducer veya posting.

Bu nedenle P1.08 hâlâ kalıcı multi-deal bot çalıştırma özelliği değildir.

## Değişen dosyalar

- `src/dcabot/application/lifecycle_event_transition.py`
- `tests/test_lifecycle_event_transition.py`

## Sonraki tek iş

`P1.08.f` persistent lifecycle record boundary: lifecycle kayıtlarının ekonomik journal’dan ayrı kalıcı sınırını ve restart doğrulamasını tanımlayacaktır.
