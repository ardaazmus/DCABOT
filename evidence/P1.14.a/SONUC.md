# P1.14.a — Rebalancing exact target/delta projection

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/rebalance_projection.py`
- Test: `tests/test_rebalance_projection.py`
- Bağımsız review: `PASS` (Erdos salt-okunur Codex incelemesi)
- Production readiness: `NO`
- Sonraki tek iş: `P1.14.b` signal identity/dedupe ve event-time karar kapısı

Bu mikro-fazda yalnızca aynı valuation asset içindeki mevcut değerlerden hedef değer ve signed delta projection’ı eklendi. Bu çıktı candidate/projection’dır; accepted order, reserve, fill, fee, price conversion, balance lookup veya persistence authority değildir.

## Uygulanan sözleşme

`target_value_i = total_equity * target_weight_i` ve `trade_delta_i = target_value_i - current_value_i` exact `Fraction` iç hesapla uygulanır. Girdiler plain decimal string sınırındadır. Allocation’lar:

- tek ve açık `valuation_asset` ile sınırlandırılır,
- `target_weight` değerleri 0–1 aralığında ve toplamları exact 1 olmak zorundadır,
- aynı asset’in tekrarı conflict olarak reddedilir,
- `current_value` negatif olamaz,
- sonuçlar asset adına göre canonical sıraya alınır,
- exact decimal dışına taşan sonuç sessiz yuvarlama olmadan fail-closed olur.

## Bilinçli kapsam dışı

Fiyatla asset-to-valuation dönüşümü, residual cash, eşik/zaman tetikleyicisi, instrument tick/quantity quantization, fee etkisi, available balance, order/reserve lifecycle, accepted fill, Store/replay, signal import, template import ve UI eklenmedi. Araştırmadaki `CONFIG/CONDITIONAL` asset universe ve order sizing kararları bu mikro-fazda numeric olarak varsayılmadı. Template doğrudan emir authority’si olamaz.

## Kontroller

- Önce test RED: yeni test dosyası eksik `rebalance_projection` modülü nedeniyle import error verdi; bu beklenen ön koşul kontrolüydü.
- En küçük uygulama sonrası kanonik `uv run --frozen python tools/run_checks.py`: `265/265 PASS`.
- Bağımsız Decimal oracle: exact BTC/ETH target ve delta değerleri ile allocation input sırası değişmezliği `PASS`.
- `uv run --frozen python tools/check_workspace.py`: `PASS`; `110` aktif Python dosyası; backup discovery kapsam dışı.

## 2026-09-18 mevcut checkout doğrulaması

- P1.14.a odak testi mevcut checkout üzerinde `6/6 PASS` verdi.
- Ayrı Decimal oracle, BTC/ETH hedef ve delta değerleri ile allocation sırası
  değişmezliğini yeniden `PASS` verdi.
- Erdos salt-okunur Codex incelemesi exact formül, fail-closed sınırlar ve
  order/economic/persistence/venue authority yokluğunu `PASS` olarak doğruladı;
  kritik `BLOCKED` bulgu yok.
- `python -m compileall -q src` ve `git diff --check` `PASS`.
- Kapsamlı `tools/run_checks.py` bu oturumda başlatılamadı: proje Python
  `3.13` isterken kullanılabilir bundled runtime `3.12.14`. Bu, odak testini
  geçersiz kılmaz; güncel tam-suite sonucu iddia edilmiyor. Önceki `265/265`
  sonucu tarihsel kanıt olarak korunmuştur.

## Kanıt sınırı

Araştırma kanıtı `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md` rebalancing formüllerini kabul ediyor, fakat yerel implementation’ın geçtiğini iddia etmiyor. Bu nedenle bu teslim yalnız local exact projection kabulüdür; kullanıcıya emir veya portföyün fiilen yeniden dengelendiği söylenemez.
