# P1.12.g.f — Futures DCA exit-candidate ve kapasite contract’ı

## Kapsam

Bu mikro-faz, `P1.12.g.e` tarafından seçilen kapanış trigger’ını gerçek emir
oluşturmadan gözlenmiş pozisyona bağlar:

- yalnız `CLOSE` kararı ve `STOP_LOSS`, `TRAILING_STOP`, `TAKE_PROFIT`
  trigger’ları aday üretir;
- trigger fiyatı pozisyon planının `price_tick` grid’inde exact temsil edilmelidir;
- requested quantity exact positive decimal olmalıdır;
- accepted exit fill’leri, mevcut committed exit miktarları ve yeni adayın
  toplamı açık pozisyon kapasitesini aşamaz;
- `BREAKEVEN_ADJUSTMENT`, trigger yokluğu, boş pozisyon, over-close ve off-grid
  fiyat fail-closed kalır.

Bu salt-okunur bir ürün contract’ıdır; `order_authority=NONE` korunur. Gerçek
order/fill, OCO, cancel-replace, reserve mutation, persistence veya
Binance/Testnet mutation açılmaz.

## Kanıt

- Odak: `uv run --frozen python -m unittest tests.test_futures_dca_exit_candidate -v`
  — `9/9 PASS`.
- Tam proje: `uv run --frozen python tools/run_checks.py` — `674` test;
  `672 PASS`, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle
  `2` environment error.
- Bağımsız Fraction oracle, `0.12 - 0.02 - 0.03 - 0.06 = 0.01` kapasite
  hesabını projection sonucuyla eşleştirdi.
- `uv run --frozen python -m compileall -q src tests` PASS.
- AST/write-surface testi persistence/transport write çağrısı bulunmadığını
  doğruladı; `order_authority=NONE`.
- `git diff --check` PASS.

## Karar

`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.

Bu kanıt seçilmiş trigger’ın exact aday ve kapasite sınırını kapatır. Candidate
identity, late-fill/conditional execution, OCO/cancel-replace, fee conversion,
reserve mutation, persistence/recovery ve Binance account/order akışı sonraki
kapılardır.

## Durum ve sonraki tek mikro-faz

`P1.12.g.g` ile candidate identity ve late-fill/conditional execution ayrım
contract’ı tamamlandı. Sıradaki tek mikro-faz `P1.12.g.h` fee-aware
exit-candidate ve quantization boundary contract’ıdır.
