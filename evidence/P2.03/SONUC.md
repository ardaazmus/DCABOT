# P2.03 — Fake venue Spot order lifecycle ilk dilimi

Tarih: 2026-09-11  
Proje: DCABOT  
Kapsam: Offline/fake Spot LIMIT ve MARKET lifecycle sözleşmesi

## Karar

```text
P2.03_FIRST_SLICE = IMPLEMENTED_WITH_LIMITATION
LOCAL_VERIFICATION = PASS
VENUE = FAKE_OFFLINE_ONLY
REAL_TESTNET_MUTATION = NO-GO
MAINNET = NO-GO
TRADING_ACTIVATION = NO-GO
FULL_P2.03 = IN_PROGRESS
```

P2.03’ün ilk güvenli dilimi tamamlandı. Amaç, gerçek Binance taşıma katmanı
kurmadan dış order lifecycle event’lerinin kimlik, sıra ve exact quantity
korumasını sabitlemekti. Bu modül ekonomik posting yapmaz; bakiye, reserve,
fee, PnL, exposure veya fill değeri hesaplamaz.

## Uygulanan sözleşme

Yeni dosya: `src/dcabot/application/spot_order_lifecycle.py`

- `LIMIT` ve `MARKET` order type’ları.
- `BUY` ve `SELL` side’ları.
- `NEW`, `PARTIALLY_FILLED`, `FILLED`, `CANCELED`, `REJECTED`, `EXPIRED` ve
  `EXPIRED_IN_MATCH` status’ları.
- LIMIT order için mevcut `InstrumentFilterProfile` ile exact tick/step,
  minimum quantity ve minimum notional doğrulaması.
- MARKET order için base `quantity` veya quote `quoteOrderQty` modelinden
  yalnız birinin seçilmesi.
- `quoteOrderQty` kullanıldığında frontend/application katmanı base quantity
  veya leaves quantity türetmez; venue execution sonucu beklenir.
- `cumulative_filled_qty = önceki filled + last_filled_qty` conservation
  kuralı.
- Order kimliği event içinde taşınır; event başka bir order lifecycle’ına
  uygulanamaz.
- Aynı event/execution fingerprint’i tekrar gelirse `DUPLICATE` ve no-op.
- Aynı kimlik farklı içerikle gelirse `CONFLICT` ve reconciliation gerekir.
- Eski event zamanı `OUT_OF_ORDER` sonucuyla quarantine/reconciliation açar.
- Terminal order sonrasında gelen yeni fill sessizce kabul edilmez.
- Cancel event’i son fill’i de taşıyabilir; final status `CANCELED`, kalan
  quantity ise yalnız quantity-mode order için korunur.
- Sonuç `report()` ile yalnız lifecycle/display alanlarına projekte edilir.

## Ekonomik authority sınırı

Bu dilim `domain.engine` ekonomik reducer’ını değiştirmedi. Kabul edilen event
henüz ekonomik `FILL` değildir. Venue lifecycle projection’ının core ekonomik
event’lerine nasıl ve hangi reconciliation kanıtıyla bağlanacağı P2.03’ün
sonraki dilimidir. Bu nedenle aşağıdakiler bilinçli olarak kapsam dışıdır:

- Gerçek Binance REST/WS transportu.
- Signed account veya order query.
- API key/secret storage ve header binding.
- Gerçek order placement/cancel.
- Fee, balance, reserve, PnL veya exposure.
- Conditional/protective orders, order lists, amend ve cancel-replace.
- Frontend/API/UI entegrasyonu.

## RED → GREEN kanıtı

Yeni test dosyası: `tests/test_spot_order_lifecycle.py`

7 offline test ile şu durumlar doğrulandı:

1. LIMIT partial fill ve exact leaves.
2. Aynı execution’ın idempotent duplicate davranışı.
3. Farklı içerikli duplicate’in conflict/reconciliation davranışı.
4. Cancel event’i içinde son fill ve kalan quantity.
5. Terminal state sonrasında late fill quarantine.
6. Out-of-order event’in state’i değiştirmemesi.
7. MARKET `quoteOrderQty` için base leaves türetilmemesi.
8. Event’in başka order lifecycle’ına uygulanamaması.

Çalıştırılan doğrulamalar:

```text
P2.03 hedef testleri: 7/7 PASS
tools/run_checks.py: 404/404 PASS
Python compileall: PASS
tools/check_workspace.py: PASS
```

## Sıradaki güvenli dilim

P2.03 hâlâ `IN_PROGRESS` durumundadır. Sıradaki tek iş, kabul edilen venue
lifecycle facts’larının mevcut `domain.engine` `INTENT/FILL/ORDER_FINAL`
event’lerine bağlanma sözleşmesini incelemektir. Bu bağlama başlamadan önce
duplicate execution’ın ekonomik olarak tek kez yazılması, partial fill,
cancel/fill race ve restart/reconciliation kanıtları ayrıca korunmalıdır.

Gerçek Testnet mutation bu evidence paketinde çalıştırılmadı ve açık kullanıcı
yetkilendirmesi olmadan çalıştırılmayacaktır.

## Kanıt sınıfları

- `[LOCAL_EVIDENCE]` — Kaynak dosyaları ve test çıktıları.
- `[APPLICATION_POLICY]` — Conflict, quarantine ve economic binding sınırları.
- `[OFFLINE_ORACLE]` — Fake lifecycle testleri.
- `[NOT_VERIFIED]` — Gerçek Binance order lifecycle çalışma zamanı ve REST/WS
  reconciliation entegrasyonu.

