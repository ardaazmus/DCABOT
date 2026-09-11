# P2.03 — Spot lifecycle → core event binding

Tarih: 2026-09-11

Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`

Kapsam: Offline/fake venue lifecycle facts ile mevcut `domain.engine` ekonomik event sınırı

## Karar

```text
P2.03_CORE_BINDING = IMPLEMENTED_WITH_LIMITATION
LOCAL_VERIFICATION = PASS
VENUE = FAKE_OFFLINE_ONLY
REAL_TESTNET_MUTATION = NO-GO
MAINNET = NO-GO
TRADING_ACTIVATION = NO-GO
```

## Uygulanan minimum davranış

Yeni dosya: `src/dcabot/application/spot_lifecycle_core_binding.py`

Test: `tests/test_spot_lifecycle_core_binding.py`

- Yalnız `LIMIT` Spot lifecycle olayları mevcut core `INTENT/FILL/ORDER_FINAL` olaylarına geçirilebilir.
- `core_role` strateji/domain tarafından açıkça sağlanır; venue event’inden türetilmez.
- Ücret ve ücret varlığı fill için açık girdidir; frontend veya adapter fee hesaplamaz.
- `PARTIALLY_FILLED` bir `FILL`, `FILLED` ise `FILL + ORDER_FINAL`, `CANCELED` ise varsa son fill ile `ORDER_FINAL(CANCELED)` olarak bağlanır.
- Core’a aktarım önce yerel aday state üzerinde uygulanır; herhangi bir olay reddedilirse hem Spot lifecycle hem core state önceki haliyle kalır.
- Aynı execution/event duplicate’i core’a ikinci ekonomik etki üretmez.
- Conflict, out-of-order veya quarantine sonucu ekonomik posting yapılmaz ve reconciliation gerekir.
- `MARKET`, `REJECTED`, `EXPIRED` ve `EXPIRED_IN_MATCH` mevcut core sözleşmesine zorla çevrilmez; açıkça unsupported/blocked kalır.

## Authority sınırı

Bu modül venue olayını ekonomik gerçek olarak tek başına kabul etmez. Spot lifecycle admission, açık strateji rolü, exact fee ve mevcut core state birlikte uygun olmadan core event üretilmez. `MARKET` için core’da limit-price tabanlı order modeli bulunduğundan bu dilimde ekonomik binding yapılmadı.

Bu dilim gerçek Binance REST/WS, signed account, order placement/cancel, reconciliation transport, fee/balance/reserve/PnL hesaplaması veya UI binding eklemez.

## RED → GREEN kanıtı

Yeni testler:

1. LIMIT partial fill → `INTENT + FILL`, exact `Fraction` position.
2. Aynı event tekrarında core state ve rapor değişmez.
3. Farklı payload’lı aynı execution conflict açar; ekonomik posting yapılmaz.
4. MARKET event’i limit tabanlı core’a bağlanmaz.
5. FILLED event’i `ORDER_FINAL` coverage ile tamamlanır.
6. CANCELED içindeki son fill yalnız bir kez ekonomik akışa alınır.
7. Ücret eksikliği iki projection’ı da ilerletmez.

Çalıştırılan doğrulamalar:

```text
uv run --frozen python tools/run_checks.py: 411/411 PASS
uv run --frozen python -m compileall -q src tests: PASS
uv run --frozen python tools/check_workspace.py: PASS
frontend npm run build: PASS
git diff --check: PASS
```

## Açık sınırlamalar

- Binding henüz durable venue-event/core-event transaction store’a bağlanmadı.
- Gerçek Binance executionReport mapping ve REST/WS reconciliation yok.
- MARKET core ekonomik modeli ve conditional/order-list lifecycle yok.
- Bağımsız faz review: `NOT_RUN`.
- Gerçek Testnet mutasyonu ve mainnet: `NO-GO`.

## Kanıt sınıfları

- `[LOCAL_EVIDENCE]` — kaynak ve test sonuçları.
- `[OFFLINE_ORACLE]` — fake lifecycle/core reducer testleri.
- `[APPLICATION_POLICY]` — unsupported ve reconciliation fail-closed sınırları.
- `[NOT_VERIFIED]` — gerçek venue execution/reconciliation davranışı.
