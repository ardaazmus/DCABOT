# Aktif iş — Faz 3.2 kodu tamam; sıradaki adım Arda'nın tercihi

`src/dcabot/application/rest_catch_up.py` yazıldı, offline test edildi (10 yeni test, tam checker 899/899 PASS). Ayrıntı: STATE.md, docs/KARARLAR.md.

## Arda'nın yapabileceği (opsiyonel, kod zaten offline kanıtlı)
Sorgu mekaniğini gerçek testnet'e karşı doğrulamak istersen:
```powershell
$env:PYTHONPATH='src'; uv run --frozen python tools/run_order_status_lookup_diagnostic.py testnet-readonly BTCUSDT --client-order-id hicvarolmayan-bir-id
```
`kind=NOT_FOUND` beklenir — bu, `-2013` ayrımının ve `clientOrderId` alan adı varsayımının gerçek venue ile uyumlu olduğunu kanıtlar. Gerçek bir emrin `venue_order_id`'sini biliyorsan (elle testnet.binance.vision'da bir emir verdiysen) `--order-id <id>` ile `kind=FOUND` da doğrulanabilir.

## Sıradaki adım (ikisinden biri, Arda seçer)
1. Yukarıdaki teşhisi çalıştırıp 3.2'yi tam REAL_TESTNET kanıtına yaklaştırmak (tam kanıt yine de 3.5'i — gerçek emir gönderme — bekler).
2. Doğrudan **Faz 3.3 — salt-okunur hesap ekranı**'na geçmek (bakiye + açık emirler, "TESTNET" rozetiyle). Roadmap sırası zaten bu.

## Değişmez sınırlar
- Credential, secret, signed mutating request, gerçek emir, mutation ve mainnet: Arda onayı olmadan asla.
- STATE.md/TASK.md yalnız Claude günceller.

## Kabul
- Arda 1 veya 2'yi seçtiğinde Claude devam eder; 3.3 için henüz brief yazılmadı.
