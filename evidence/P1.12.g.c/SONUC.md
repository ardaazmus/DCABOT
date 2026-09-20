# P1.12.g.c — Futures DCA average-entry TP ve split-TP projection

## Kapsam

Bu mikro-faz, gözlenmiş Futures DCA fill projection’ından average-entry TP
hedefini ve split-TP miktarlarını yalnız offline/salt-okunur projection olarak
üretir:

- LONG için average-entry × (1 + exact profit rate);
- SHORT için average-entry × (1 − exact profit rate);
- hedef fiyat tick grid’inde değilse sessiz quantization yapılmadan fail-closed
  ret;
- split-TP toplamı açık pozisyon miktarını aşamaz, kalan miktar exact olarak
  görünür.

Mevcut `FuturesDcaFillProjection` average-entry ve position quantity kaynağı
olarak yeniden kullanıldı; mevcut `multi_tp_conservation` kapasite doğrulaması
split miktarlarını sınamak için yeniden kullanıldı. Bu faz TP emri, OCO,
cancel-replace, reserve, persistence, fill veya venue/Binance mutation açmaz.

## Kanıt

- Odak: `uv --cache-dir D:\project\DCABOT\.uv-cache run --isolated --frozen python -m unittest tests.test_futures_dca_take_profit tests.test_futures_dca_fill_projection tests.test_multi_tp_conservation tests.test_futures_dca_plan` — `18/18 PASS`.
- Tam proje: `uv --cache-dir D:\project\DCABOT\.uv-cache run --isolated --frozen python tools/run_checks.py` — `647` test; `645 PASS`, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle `2` environment error.
- `order_authority=NONE`; TP projection içinde persistence, SQLite/HTTP transport, order attempt, fill veya reserve yazımı bulunmuyor. AST/write-surface testi PASS.
- Bağımsız exact davranış kontrolü LONG/SHORT yönünü, tick dışı hedefin reddini ve split miktar conservation’ını PASS doğruladı.
- Compile ve workspace kontrolleri ayrıca çalıştırıldı; `git diff --check` PASS.

## Karar

`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.

Bu kanıt yalnız average-entry hedef projection’ı ve split miktar conservation’ını
kapatır. Fee-aware TP, çoklu TP/OCO emirleri, trailing/breakeven, cancel-replace,
gerçek execution ve durable lifecycle recovery sonraki mikro-fazlardır.

## Sonraki tek mikro-faz

`P1.12.g.d`: fee/funding etkisini varsaymadan, TP target’ın fee-aware profile
gereksinimini ve breakeven boundary’sini karar/contract kapısı olarak doğrulamak.
