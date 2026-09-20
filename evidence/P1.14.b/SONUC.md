# P1.14.b — Signal identity, event-time ve dedupe

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/signal_event_contract.py`
- Test: `tests/test_signal_event_contract.py`
- Bağımsız review: `PASS` (Ptolemy salt-okunur Codex incelemesi, düzeltme sonrası)
- Production readiness: `NO`
- Sonraki tek iş: `P1.14.c` signal warmup/closed-bar ve stale-policy karar kapısı

Bu mikro-fazda source signal için immutable identity ve event-time sıralı, salt projection düzeyinde kabul sözleşmesi eklendi. Signal kabulü ekonomik order, candidate veya fill üretmez.

## Uygulanan sözleşme

Signal kaydı `signal_id`, `source`, integer `event_time_us`, `schema_version=signal-v1` ve küçük harfli 64 karakter SHA-256 `payload_hash` taşır. `accept_signal`:

- exact aynı identity ve payload için `DUPLICATE` ile no-op döner,
- aynı `signal_id` farklı immutable payload/metadata ile gelirse `SIGNAL_EVENT_CONFLICT` verir,
- geçmişte aynı `signal_id` iki kez bulunursa `SIGNAL_HISTORY_IDENTITY_INVALID` ile fail-closed olur,
- yeni signal’in event zamanı son kabul edilen zamandan eskiyse açık stale policy ile `SIGNAL_EVENT_STALE` verir,
- geçmişi immutable tuple olarak döndürür ve mevcut event zaman sırasını bozan geçmişi reddeder,
- processing/wall-clock zamanını ekonomik event zamanı yerine kullanmaz.

## Bilinçli kapsam dışı

Payload canonicalization/hash üretimi, webhook authentication, replay window/retention, warmup/indicator, closed-bar adapter, threshold/time rebalance trigger, signal-to-candidate mapping, core acceptance, order/reserve/fill, persistence, API ve UI eklenmedi. Bu alanlar sonraki ayrı mikro-fazlardır.

## Kontroller

- Önce test RED: yeni test dosyası eksik `signal_event_contract` modülü nedeniyle import error verdi.
- En küçük uygulama sonrası kanonik `uv run --frozen python tools/run_checks.py`: `270/270 PASS`.
- Bağımsız signal contract control: accepted event, exact duplicate no-op, conflicting duplicate ve stale rejection `PASS`.
- `uv run --frozen python -m compileall -q src tests`: `PASS`.
- `uv run --frozen python tools/check_workspace.py`: `PASS`; `114` aktif Python dosyası; backup discovery kapsam dışı.

## 2026-09-18 mevcut checkout doğrulaması

- Bağımsız review’da bulunan duplicate-history açığı düzeltildi: history içinde
  aynı `signal_id` artık aynı veya çelişkili event olsa da fail-closed reddediliyor.
- P1.14.b odak testi mevcut checkout üzerinde `6/6 PASS` verdi; readiness ile
  birlikte ilgili signal kümesi `11/11 PASS` oldu.
- Ayrı signal oracle; accepted, exact duplicate no-op, conflict ve stale
  sonuçları ve duplicate-history reddini yeniden `PASS` verdi.
- Ptolemy salt-okunur Codex incelemesi immutable identity, event-time sırası,
  fail-closed duplicate/conflict/stale sınırları ve authority yokluğunu `PASS`
  olarak doğruladı; kritik `BLOCKED` bulgu yok.
- `python -m compileall -q src` ve `git diff --check` `PASS`.
- Kapsamlı `tools/run_checks.py` bu oturumda başlatılamadı: proje Python
  `3.13` isterken kullanılabilir bundled runtime `3.12.14`. Bu, odak testini
  geçersiz kılmaz; güncel tam-suite sonucu iddia edilmiyor. Önceki `270/270`
  sonucu tarihsel kanıt olarak korunmuştur.

## Kanıt sınırı

Araştırma kanıtı `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md` signal identity, event-time ve duplicate/conflict ayrımını destekliyor; yerel kodun geçerli olduğunu iddia etmiyor. Bu teslim yalnızca immutable source-signal contract’ıdır; signal’in işlem emrine dönüştüğü iddia edilmez.
