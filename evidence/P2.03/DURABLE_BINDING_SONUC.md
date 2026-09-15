# P2.03 — Durable offline lifecycle/core binding

Tarih: 2026-09-15
Proje: DCABOT
Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`

## Karar

```text
P2.03_DURABLE_BINDING = IMPLEMENTED_WITH_LIMITATION
LOCAL_VERIFICATION = PASS
VENUE = FAKE_OFFLINE_ONLY
REAL_TESTNET_MUTATION = NO-GO
MAINNET = NO-GO
TRADING_ACTIVATION = NO-GO
```

## Uygulanan minimum davranış

- `SpotBindingStore` ayrı, versioned SQLite journal olarak yalnız offline/fake
  Spot lifecycle → core binding kayıtlarını sahiplenir.
- Başlangıç `SpotOrderLifecycle` ve exact `Fraction` kullanan core `State`
  checksum’li projection olarak saklanır.
- Kabul edilen Spot event zarfı ve üretilen core `INTENT/FILL/ORDER_FINAL`
  event listesi aynı SQLite transaction’ında yazılır.
- Açılış/replay, stored event’leri mevcut guarded binder üzerinden yeniden
  oynatır; core event checksum’i ve replay sonucu eşleşmezse fail-closed olur.
- Aynı event’in aynı payload’ı idempotent `DUPLICATE`; farklı payload conflict;
  reddedilen binding hiçbir projection’ı journal’a yazmaz.
- Coordinator’dan açıkça verilen redakte reconciliation observation; event
  fingerprint, karar, connection state ve isteğe bağlı `binding_event_id` ile
  aynı SQLite journal’ında checksum’li ve bounded biçimde saklanır.
- `append(..., reconciliation=...)` kabul edilmiş Spot/core binding ile
  reconciliation kaydını tek transaction’da yazar; reconciliation conflict’i
  ekonomik binding’i de rollback eder.
- Restart hydration, durable observation’lardan kabul edilmiş event fingerprint/
  zaman cursor’ını geri kurar; önceki `SYNCED` durumu yeniden trust edilmez ve
  state en az `RECONCILIATION_REQUIRED` seviyesinde kalır.
- Hydration sonrası `mark_synced(True)` bypass’ı kapalıdır. Redakte
  `AuthoritativeReconciliationSnapshot`; bounded kimlik, zaman, fingerprint ve
  hydrated son event cursor eşleşmesiyle doğrulanmadan `SYNCED` üretilmez.
- `startup_with_durable_recovery`, durable event continuity doğrulamasını
  `AttemptStore.recover_after_restart` çağrısından önce çalıştırır. Böylece
  geçerli cursor ile in-flight attempt’ler `UNKNOWN` olarak karantinaya alınır;
  geçersiz/conflict cursor durumunda attempt store mutasyona uğramaz ve
  authoritative snapshot gereksinimi korunur.
- `reconcile_recovered_attempts`, recovery’den dönen bounded `UNKNOWN` listesini
  önce tamamen doğrular; duplicate veya farklı state varsa lookup başlamadan
  reddeder. Doğrulanan her kayıt mevcut explicit lookup portuna devredilir;
  sonuçlar durable `ACKNOWLEDGED`/`UNRESOLVED` state’lerine yazılır ve
  authoritative snapshot kapısı ayrıca korunur.

## Sınır

Bu dilim gerçek Binance REST/WS, signed account, order mutation, fee/balance/
reserve/PnL genişletmesi veya frontend binding açmaz. Coordinator’ın in-memory
`_seen_events`/zaman cursor’ı yalnız explicit `hydrate_event_continuity` çağrısı
ile geri kurulur; stored observation tek başına verilen karar/state’i yeniden
sunar, `SYNCED` üretmez. `startup_with_durable_recovery` aynı doğrulamayı
AttemptStore recovery’sinden önce orkestre eder. Snapshot sonrası gerçek
reconciliation ve canlı venue association ayrıca kanıtlanmalıdır.

## RED → GREEN kanıtı

`tests/test_spot_binding_store.py` lifecycle/core replay, duplicate/conflict ve
rejected no-write davranışını; `tests/test_spot_binding_reconciliation.py`
reconciliation restart replay, redacted schema, duplicate/conflict, GAP’ın
promotion olmadan korunması ve transaction rollback davranışını kapsar.

`tests/test_reconciliation.py` cursor hydration, SYNCED promotion engeli, GAP
quarantine, authoritative snapshot cursor/freshness doğrulaması, tutarsız
geçmişte atomic no-partial-restore davranışı ve recovery öncesi cursor doğrulama
sırasını; recovered attempt listesinin explicit lookup handoff’unu ve mutation
öncesi duplicate doğrulamasını kapsar.

Yerel doğrulama:

```text
uv run --frozen python tools/run_checks.py: 432/432 PASS
uv run --frozen python -O tools/run_checks.py: 432/432 PASS
uv run --frozen python -m compileall -q src tests: PASS
uv run --frozen python tools/check_workspace.py: PASS, 168 aktif Python dosyası
frontend npm run build: PASS
git diff --check: PASS
```

## Kanıt sınıfları

- `[LOCAL_EVIDENCE]` — kaynak ve test sonuçları.
- `[OFFLINE_ORACLE]` — fake Spot lifecycle ve mevcut core reducer replay’i.
- `[APPLICATION_POLICY]` — duplicate/conflict/fail-closed sınırları.
- `[NOT_VERIFIED]` — canlı venue transport/reconciliation ve Testnet mutation.
