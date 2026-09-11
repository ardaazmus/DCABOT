# P1.14.c — Signal warmup, closed-bar ve stale readiness gate

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/signal_readiness.py`
- Test: `tests/test_signal_readiness.py`
- Bağımsız review: `NOT_RUN`
- Production readiness: `NO`
- Sonraki tek iş: `P1.14.d` threshold/time rebalancing trigger karar kapısı

Bu mikro-fazda signal’in ekonomik işleme hazır olup olmadığını belirleyen salt-okunur readiness gate eklendi. Gate sonucu order, candidate veya fill oluşturmaz.

## Uygulanan sözleşme

`assess_signal_readiness` açık biçimde şu dört sonucu üretir:

- `WAITING_FOR_CLOSED_BAR`: signal `event_time_us`, son kapalı bar zamanından ilerideyse,
- `STALE`: signal, seçilmiş `max_staleness_us` penceresinin dışındaysa,
- `WARMING_UP`: gözlenen kapalı bar sayısı gereken warmup sayısına ulaşmadıysa,
- `READY`: yukarıdaki engeller yoksa.

Zaman yalnız source `event_time_us` ve `closed_bar_time_us` ile integer microseconds olarak değerlendirilir. Wall-clock veya processing time ekonomik zaman yerine kullanılmaz. Warmup ve stale penceresi caller tarafından açıkça verilir; gizli varsayılan eklenmez. Bozuk tip, negatif zaman/sayaç ve sıfır warmup requirement fail-closed olur.

## Bilinçli kapsam dışı

İndikatör formülü, veri sağlayıcı adapter’ı, gerçek incomplete-bar feed, signal-to-candidate mapping, threshold/time trigger, price conversion, order sizing, core acceptance, persistence, API ve UI eklenmedi. `READY` ekonomik onay anlamına gelmez.

## Kontroller

- Önce test RED: yeni test dosyası eksik `signal_readiness` modülü nedeniyle import error verdi.
- En küçük uygulama sonrası kanonik `uv run --frozen python tools/run_checks.py`: `275/275 PASS`.
- Bağımsız readiness control: warmup, future/incomplete bar, stale ve ready durumları `PASS`.
- Bağımsız kontrolde ilk fixture event zamanı yanlış seçildi; bu kontrol verisi düzeltilip aynı iddia tekrar çalıştırıldığında `PASS` alındı.
- `uv run --frozen python -m compileall -q src tests`: `PASS`.
- `uv run --frozen python tools/check_workspace.py`: `PASS`; `116` aktif Python dosyası; backup discovery kapsam dışı.

## Kanıt sınırı

Araştırma kanıtı `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md` warmup, closed-bar ve stale signal ayrımını destekliyor; yerel implementation’ın geçtiğini iddia etmiyor. Bu teslim yalnız readiness projection kabulüdür; strateji sinyalinin ekonomik emir olduğu iddia edilmez.
