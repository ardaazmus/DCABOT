# P1.12.f.i.b — bağımsız candidate/oracle incelemesi ve kritik gate

## Sonuç

Durum: `IMPLEMENTED_WITH_LIMITATION / INDEPENDENT_REVIEW_PASS`

P1.12.f.i.a candidate binding bağımsız Decimal hesaplarıyla yeniden kontrol edildi.
BASE_QTY için quantity-step aşağı quantization; QUOTE_NOTIONAL için
`allocation / price` sonrası quantity-step quantization ve gerçekleşen quote
notional sonuçları production hesaplarından bağımsız oracle ile eşleşti.

AST write-surface incelemesi `bind_futures_dca_custom_candidates` fonksiyonunda
SQLite/persistence veya HTTP mutation çağrısı bulmadı. Fonksiyon yalnız yerel
immutable ladder/instrument girdilerinden candidate projection üretir. Kritik gate
tam regresyon, compile, workspace ve diff kontrolleriyle geçti.

## Kanıt

- Odak: `tests.test_futures_dca_custom_ladder tests.test_futures_dca_plan tests.test_instrument_filters` — `17/17 PASS`
- İlişkili: Futures DCA plan/oracle/fill projection/fill oracle/reservation/contract-size,
  ladder binding/conservation, sizing ve math kümeleri — `52/52 PASS`
- Tam proje: `uv --cache-dir D:\project\DCABOT\.uv-cache run --isolated --frozen python tools/run_checks.py` — `622/622 PASS`
- Bağımsız Decimal candidate oracle: `PASS`
- AST/write-surface: `PASS` (`write_calls=[]`, `sqlite3/httpx` import yok)
- Python `compileall`: `PASS`
- Workspace: `PASS`, `239` aktif Python dosyası, `EMPTY_OR_NOT_PLACED` yedek düzeni
- `git diff --check`: `PASS` (yalnız mevcut LF/CRLF uyarıları)

## Sınır ve sonraki iş

Bu inceleme gerçek exchange metadata, gerçek emir, persistence activation veya
Binance/Testnet mutation kanıtı değildir. `SHARE`, contract-size ve gerçek venue
metadata bağlama sonraki bağımlı kararlara bırakıldı. Sıradaki tek iş
`P1.12.f.i.c` immutable custom candidate acceptance-boundary sözleşmesidir.
