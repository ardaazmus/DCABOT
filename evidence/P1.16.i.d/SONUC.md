# P1.16.i.d — Persistence/replay/recovery kanıt denetimi

## Karar

- Alt faz durumu: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Stress economic persistence/replay: `DEFERRED / NO-GO`
- Kod değişikliği: yok
- Production readiness: `NO`
- Sonraki tek iş: `P1.16.i.e` minimum dikey uygulama ve dış yüzey karar kapısı

Bu denetim, rapordaki persistence, replay, recovery, checksum, dedup ve atomicity iddialarını mevcut iki SQLite sahibine karşı sınadı. Mevcut base economic Store kendi kapsamı içinde güçlü bir transaction/replay kanıtı taşıyor; HistoricalRunStore ise immutable historical snapshot sahibi. Hiçbiri stress event, scenario branch veya ekonomik stress sonucu için ortak persistence authority değildir.

## Yerel authority karşılaştırması

| Alan | Mevcut yerel gerçek | Denetim sonucu |
|---|---|---|
| Base ekonomik event journal | `Store` içinde `batches`, `events`, `postings`, `incidents`; event payload SHA-256, ordered replay ve exact Fraction posting | `ACCEPT / scope-limited` |
| Base transaction | `Store.transact()` `BEGIN IMMEDIATE` ile batch, event ve posting yazımını tek local transaction’da yürütür; hata rollback yapar | `ACCEPT / yalnız aynı Store için` |
| Base crash recovery | Process-death ve injected posting/event failure testlerinde uncommitted batch/event ekonomik state’e geçmiyor; retry mümkün | `ACCEPT / base Store için` |
| Base dedup/conflict | Batch ID request conflict; `FILL.execution_id` unique ve aynı payload retry no-op; farklı payload conflict/quarantine | `ACCEPT / generic event-id sözleşmesi değil` |
| Base replay | `events ORDER BY seq`, payload hash doğrulaması ve core reducer replay’i | `ACCEPT / stress branch yok` |
| Historical run persistence | Ayrı `historical_runs` SQLite snapshot tablosu; canonical record ve `record_sha256`; source execution idempotency/conflict | `ACCEPT / snapshot scope` |
| Historical corruption | Record checksum, row metadata karşılaştırması ve nested field eksikliği `CORRUPT` olarak ayrıştırılıyor | `ACCEPT / snapshot scope` |
| Stress event/branch | Her iki store şemasında `stress_event`, `scenario`, `branch`, branch snapshot veya event-level stress state yok | `RED / NO-GO` |
| İki store atomikliği | Base Store ve HistoricalRunStore ayrı SQLite bağlantıları/dosyaları; ortak transaction veya two-phase commit yok | `RED / adapter yazılmadı` |
| Field-level base/stress comparison | Mevcut binding hash ve snapshot bütünlüğü var; ekonomik alanların base/stress karşılaştırma authority’si yok | `RED / NO-GO` |

## Claim → kontrol → sonuç

### C-D-01 — Event + posting atomikliği

**İddia:** Bir ekonomik event ile ona ait posting’ler birlikte commit edilmeli; hata halinde hiçbir ekonomik geçiş kalmamalı.

**Mevcut kontrol:** `Store.transact()` batch/event/posting yazımını aynı SQLite transaction’ında yürütüyor. Posting insert hatası ve sentetik cycle içindeki event hatası için rollback testleri var.

**Bağımsız kontrol:** Production reducer çağrısını genişletmeden geçici bir Store üzerinde `MARK → INTENT → FILL` akışı, aynı `FILL` için farklı transport batch ID retry ve close/reopen sonrası state/posting/event sayısı karşılaştırıldı.

```text
STORE_TABLES=('batches','events','incidents','metadata','postings')
STORE_REPLAY_BEFORE=('1','1/10',3)
STORE_REPLAY_AFTER=('1','1/10',3)
```

**Sonuç:** `PASS`, fakat yalnız mevcut base Store kapsamı için. Bu sonuç stress event veya scenario branch atomikliği kanıtı değildir.

### C-D-02 — Crash/recovery

**İddia:** Commit öncesi process ölümü veya posting/event hatası yarım ekonomik sonucu kalıcı bırakmamalı.

**Mevcut kontrol:** `test_real_process_death_rolls_back_uncommitted_batch`, `test_posting_failure_rolls_back_execution_and_can_retry` ve `test_tick_failure_rolls_back_whole_synthetic_cycle` geçiyor.

**Sonuç:** Base Store için `PASS`. HistoricalRunStore için kodda tek-row `BEGIN IMMEDIATE`/rollback mevcut olsa da process-death sonrası stress snapshot recovery state, staged event veya replay protokolü bulunmadığından stress recovery iddiası `NOT_PROVEN` kabul edildi.

### C-D-03 — Dedup/conflicting duplicate

**İddia:** Aynı execution yeniden uygulandığında ekonomik sonuç değişmemeli; aynı kimlikle farklı payload fail-closed olmalı.

**Mevcut kontrol:** Base Store’da `FILL.execution_id` unique dedup/conflict ve incident quarantine; HistoricalRunStore’da `source_execution_id` idempotency/conflict testleri geçiyor.

**Sınır:** Bu iki kimlik aynı contract değildir. Generic `event_id + checksum`, scenario id, branch id veya stress result event identity mevcut store’larda yoktur.

**Sonuç:** Mevcut base fill ve historical snapshot için `PASS`; raporun stress event dedup iddiası için `RED`.

### C-D-04 — Replay ve immutable kayıt

**İddia:** Reopen/replay aynı sonucu üretmeli ve immutable kayıt bozulduğunda yayınlanmamalı.

**Kontrol:** Base Store ordered reducer replay, posting reconciliation ve SQLite integrity audit yapıyor. HistoricalRunStore save/reopen/list/detail, tamper ve checksum-valid-but-schema-invalid testleri geçiyor.

**Sonuç:** Her iki mevcut sahip kendi kapsamı içinde `PASS`. HistoricalRunStore ekonomik event replay yapmadığı için stress economic replay `NO-GO`.

### C-D-05 — Branch isolation

**İddia:** OHLC ambiguity branch’leri immutable başlangıç state’inden ayrılmalı; branch tüketimleri birbirine sızmamalı.

**RED kontrolü:** Bağımsız SQLite şema sorgusunda yalnız şu tablolar bulundu:

```text
STORE_TABLES=('batches','events','incidents','metadata','postings')
HISTORICAL_TABLES=('historical_runs','run_store_meta')
STRESS_TABLE_PRESENT=False
```

Hiçbir store’da branch registry, branch-local reserve/position snapshot veya scenario event owner yoktur. Mevcut historical simulation ambiguity’yi commit etmeden korur; bu, persisted branch isolation ile aynı şey değildir.

**Sonuç:** `RED / NO-GO`; branch adapter veya deepcopy/event-sourcing varsayımı eklenmedi.

### C-D-06 — İki store arasında atomicity

**İddia:** Ekonomik stress event’i ile historical run sonucu tek güvenilir commit sınırında bağlanmalı.

**Kontrol:** `Store` kendi dosyasını; `HistoricalRunStore` ayrı versioned dosyayı yönetiyor. API save yolu yalnız `HistoricalRunStore.save()` çağırıyor; base Store transaction’ı ile ortak transaction yok.

**Sonuç:** İki store’u adapter ile ardışık bağlamak atomicity kanıtlamaz. `RED / NO-GO`. Yeni schema, adapter veya cross-store transaction açılmadı.

### C-D-07 — Checksum ve field-level comparison

**İddia:** Kayıt checksum’ı, kimlik ve alan bazlı karşılaştırma ekonomik yanlış eşleşmeyi yakalamalı.

**Kontrol:** Base event payload hash’i ve posting reconciliation mevcut; historical record checksum’ı ve denormalize list metadata eşleşmesi mevcut. Testlerde tamper `CORRUPT`/`Conflict` olarak yakalanıyor.

**Sınır:** Bunlar kayıt bütünlüğü kontrolleridir. Base result ile stress result’ın dataset/config/model/kernel/stress/scenario/seed alanlarını alan bazında karşılaştıran bir oracle yoktur.

**Sonuç:** Mevcut bütünlük kontrolleri `PASS`; raporun stress field-level comparison iddiası `NOT_PROVEN`.

## Raporla ayrılan noktalar

1. Rapordaki `economic_event`, `result_summary` ve `scenario_branch` tabloları mevcut project schema’sı değildir; bu tabloları eklemek migration ve authority kararı gerektirir.
2. Rapordaki “result summary ancak bütün event’ler COMMITTED ise tamamdır” kuralı mevcut historical snapshot store’da uygulanmıyor; mevcut kayıt `execution_status` ve immutable snapshot taşır, event-state reducer değildir.
3. Rapordaki genel `event_id` dedup modeli mevcut base Store’da yalnızca `FILL.execution_id` ve batch ID kapsamındaki kısmi karşılığa sahiptir.
4. Rapordaki branch isolation için `deepcopy` önerisi kanıtlanmış persistence/recovery stratejisi değildir; branch state ownership ve commit authority seçilmeden kullanılmadı.
5. Historical run store’un FULL synchronous ve transaction kullanması tek snapshot insert güvenilirliği için yararlı bir yerel sınırdır; stress event ile economic posting’in aynı transaction’da olduğu anlamına gelmez.

## Uygulama kararı

| Davranış | Karar |
|---|---|
| Mevcut base Store transaction/replay/audit | `ACCEPT`, mevcut scope korunur |
| Mevcut HistoricalRunStore checksum/idempotency/corruption isolation | `ACCEPT`, snapshot scope korunur |
| Stress event persistence | `DEFERRED / NO-GO` |
| Scenario branch persistence/isolation | `DEFERRED / NO-GO` |
| Cross-store atomic adapter | `REJECT_FOR_CURRENT_CONTRACT` |
| Stress economic crash recovery | `NOT_PROVEN` |
| Stress field-level base/result comparison | `DEFERRED / NO-GO` |
| Reserve lifecycle persistence | Bu alt fazın dışı; önceki `NO-GO` korunur |

## Kapanış kontrolleri

- Kanonik regresyon: `uv run --frozen python tools/run_checks.py` → `325/325 PASS`.
- Bağımsız Store reopen/dedup/schema kontrolü: `PASS`; stress/scenario/branch tablosu bulunmadı.
- Base crash/rollback/replay testleri: kanonik regresyonda `PASS`.
- Historical snapshot save/reopen/conflict/corruption testleri: kanonik regresyonda `PASS`.
- Kod değişikliği: yok.
- Production readiness: `NO`.

## Sonraki geçiş

`P1.16.i.d` tamamlandı-with-limitation. Mevcut iki store’un kendi kapsamındaki güvenilirlik kanıtı korunuyor; stress economic event, scenario branch, cross-store atomicity, economic recovery ve field-level result comparison kanıtlanmadı. Bu nedenle `.e` fazı ekonomik runner yazmaya otomatik izin vermez; önceki no-go sınırlarını birleştirerek minimum dikey uygulama ve dış yüzey kararını verecektir. Kanıt yoksa yeni ekonomik kod yazmadan no-go sonucu kapatılmalıdır.
