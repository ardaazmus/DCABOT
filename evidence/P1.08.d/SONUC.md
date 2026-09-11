# P1.08.d — Lifecycle event identity contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Bağımsız review: `NOT_RUN`  
Production readiness: `NO`

## Karar

P1.08 araştırması lifecycle event identity, ordering, duplicate/conflict ve replay sınırlarının açık olmasını istiyor. Bu mikro fazda persistent schema veya reducer bağlantısı kurulmadı. Kimlik ve sıralama yalnız saf, in-memory contract olarak tanımlandı.

## Uygulanan dar dilim

- `LifecycleEvent` immutable `event_id`, `deal_id`, `config_revision_id`, event type ve pozitif sequence taşır.
- Event type kümesi yalnız `START`, `PAUSE`, `RESUME`, `COMPLETE`, `ABORT`, `FAIL` ile sınırlıdır; `COPY` bu event journal’ına eklenmemiştir.
- Bir event history tek deal ve tek config revision scope’unda kalır.
- İlk event sequence `1`, sonraki yeni event sequence’i tam ardışık olmalıdır.
- Aynı `event_id` ve tüm immutable alanlar eşitse sonuç `DUPLICATE` olur ve history değişmez.
- Aynı `event_id` farklı kayıtla gelirse `LIFECYCLE_EVENT_CONFLICT` oluşur.
- Yeni event farklı deal/revision scope’u veya sequence gap taşıyorsa fail-closed reddedilir.

Bu modül lifecycle durumunu değiştirmez; yalnız event’in kimlik/scope/order açısından kabul edilebilir olup olmadığını kontrol eder.

## Kanıt zinciri

1. **İddia:** Yeni lifecycle event’leri tek deal/config revision scope’unda ve ardışık sırada tutulabilir.  
   **RED:** Test modülü ilk çalıştırmada yeni `lifecycle_event_contract` bulunamadığı için import error verdi.  
   **GREEN:** START sequence 1 ve PAUSE sequence 2 aynı scope’ta kabul edildi.

2. **İddia:** Exact duplicate ikinci ekonomik veya lifecycle etkisi üretmemelidir.  
   **Kontrol:** Aynı immutable event tekrar kabul edildi.  
   **Sonuç:** History aynı kaldı ve `DUPLICATE` sonucu döndü.

3. **İddia:** Aynı event ID farklı içerikle tekrar kullanılamaz.  
   **Kontrol:** Aynı ID ile `START` yerine `FAIL` gönderildi.  
   **Sonuç:** `LIFECYCLE_EVENT_CONFLICT` ile reddedildi; history değişmedi.

4. **İddia:** Scope ve sıra ihlalleri sessizce kabul edilmemelidir.  
   **Farklı kontrol:** Farklı deal ve sequence gap fixture’ları çalıştırıldı.  
   **Sonuç:** `LIFECYCLE_EVENT_SCOPE_CONFLICT` ve `LIFECYCLE_EVENT_SEQUENCE_INVALID` üretildi.

5. **Genel doğrulama:** Kanonik regresyon `158/158 PASS`; `compileall PASS`; `tools/check_workspace.py PASS` (`active_python_files: 63`).

## Bilinçli olarak yapılmayanlar

- Hash/canonical serialization veya persisted event record.
- Lifecycle event’in `DealLifecycle` status projection’ına uygulanması.
- Terminal state sonrası event reddi; bunu sonraki transition adapter/reducer sahibi belirleyecek.
- Restart/replay, API/UI, config snapshot, cooldown ve pause-order policy.
- Shared account/reserve, economic reducer ve posting.

Bu nedenle event contract production lifecycle veya persistent replay kanıtı değildir.

## Değişen dosyalar

- `src/dcabot/application/lifecycle_event_contract.py`
- `tests/test_lifecycle_event_contract.py`

## Sonraki tek iş

`P1.08.e` lifecycle event-to-transition adapter: accepted event’in saf `DealLifecycle` projection’ına tek kez uygulanmasını ve duplicate/invalid transition sınırını bağlayacaktır.
