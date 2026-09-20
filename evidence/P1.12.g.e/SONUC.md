# P1.12.g.e — Futures DCA exit priority contract

## Kapsam

Bu mikro-faz, aynı gözlemde birden fazla Futures DCA exit trigger’ı oluştuğunda
kararı deterministik ve execution’dan ayrı tutar:

- öncelik `STOP_LOSS > TRAILING_STOP > TAKE_PROFIT > BREAKEVEN_ADJUSTMENT`;
- stop-loss, trailing stop ve take-profit kapanış kararı üretir;
- breakeven tek başına yalnız stop adjustment kararıdır, kapanış değildir;
- kapanış trigger’ı varsa breakeven adjustment bastırılır;
- giriş sırası sonucu değiştirmez, aynı trigger türü ikinci kez taşınamaz.

Bu, 3Commas/Pionex venue davranışı iddiası değildir; ürünün açık güvenlik
politikasına ait salt-okunur karar contract’ıdır. Order, fill, OCO,
cancel-replace, reserve, persistence veya Binance mutation açılmaz.

## Kanıt

- Odak: `uv run --frozen python -m unittest tests.test_futures_dca_exit_priority -v` — `9/9 PASS`.
- Tam proje: `uv run --frozen python tools/run_checks.py` — `665` test; `663 PASS`, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle `2` environment error.
- Bağımsız tüm trigger alt-kümeleri oracle’ı priority, suppression ve karar sınıfını `PASS` doğruladı.
- `uv run --frozen python -m compileall -q src tests` PASS.
- AST/write-surface testi persistence/transport write çağrısı bulunmadığını doğruladı; `order_authority=NONE`.

## Karar

`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.

Bu kanıt yalnız trigger precedence ve breakeven’in adjustment olarak ayrımını
kapatır. Seçilen trigger’ı gerçek exit candidate’a bağlama, exact quantity
capacity, OCO/cancel-replace, late fill, reserve, persistence ve Binance
account/order akışı sonraki kapılardır.

## Durum ve sonraki tek mikro-faz

`P1.12.g.f` ile seçilmiş exit trigger’ı exact exit-candidate ve açık pozisyon
kapasitesi contract’ına bağlandı. Sıradaki tek mikro-faz `P1.12.g.g` candidate
identity ve late-fill/conditional execution ayrım contract’ıdır.
