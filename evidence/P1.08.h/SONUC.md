# P1.08.h — Lifecycle terminal/cooldown policy sonucu

## Karar

`COMPLETE_WITH_LIMITATION / LOCAL_PASS`.

Bu mikro dilim yalnız iki saf, ekonomik olmayan davranışı kapatır:

1. `COMPLETED`, `ABORTED` veya `FAILED` lifecycle projection’ından sonra yeni event kabul edilmez.
2. Yeni deal cooldown kararı yalnız historical integer `effective_time_us` farkına göre verilir.

Persistent API/UI, wall-clock, processing-time, order cancellation, shared account/reserve ve ekonomik state mutation bu dilime alınmadı. Production readiness `NO`; bağımsız review `NOT_RUN`.

## Uygulanan sınır

Terminal reddi yeni bir terminal state üretmedi. Mevcut declarative transition tablosunda terminal durumlar için geçiş çifti bulunmadığı için `LIFECYCLE_TRANSITION_INVALID` döner. Adapter geçişi çağırmadan önce history’yi aday event ile değiştirmediğinden reddedilen event projection veya history’de görünmez.

`cooldown_allows_new_deal(terminal_effective_time_us, candidate_effective_time_us, cooldown_us)`:

- yalnız `int` historical zamanları kabul eder;
- `candidate - terminal >= cooldown` kuralını kullanır;
- eşit sınırı kabul eder;
- aday zaman terminal zamandan gerideyse `COOLDOWN_TIME_ORDER_INVALID` döner;
- negatif veya integer olmayan cooldown’ı `COOLDOWN_INVALID` ile reddeder;
- wall-clock veya ekonomik alan okumaz.

## Kanıt zinciri

### RED

Yeni `tests/test_lifecycle_policy.py`, henüz mevcut olmayan `dcabot.application.lifecycle_policy` modülünü import ettiği için odak test discovery aşamasında başarısız oldu: `ModuleNotFoundError`.

### GREEN

`src/dcabot/application/lifecycle_policy.py` eklendikten sonra aynı proje kontrolü:

```text
Ran 170 tests ... OK
```

Testler terminal durumlarının üçünü, history/projection mutasyonsuz reddi, cooldown eşik dahil/haricini, negatif süreyi ve geriye giden historical zamanı kapsar.

### Farklı kontrol

Policy test dosyası bağımsız unittest hedefi olarak ayrıca çalıştırıldı; üç test metodu ve terminal subtest’leri geçti. Ardından compile ve workspace kontrolleri de çalıştırıldı.

## Açık sınırlar

- Cooldown henüz lifecycle event kaydına veya persistent store’a bağlanmadı.
- `effective_time_us` kaynağının event contract’a eklenmesi bu fazın kararı değildir.
- Pause sırasında pending order’ın korunması/iptali/reject edilmesi `P1.08.i` kapsamındadır.
- Gerçek saat, çoklu bot, ortak hesap, reserve ve venue davranışı yoktur.
