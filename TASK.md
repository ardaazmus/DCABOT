# Aktif iş — Faz 3.5 kodu tamam; REAL_TESTNET kanıtı Arda'yı bekliyor

`data_adapters/binance_testnet_order_execution.py` (projede mutation yapabilen TEK dosya), `application/testnet_order_execution.py` (Faz 3.4'ün 7 kuralını uygulayan kapı), `tools/run_single_testnet_order.py` (CLI kanıt aracı) yazıldı, 19 yeni offline test, tam checker 929/929 PASS. Ayrıntı: STATE.md, docs/KARARLAR.md.

## Arda'nın yapması gereken (Claude yapamaz — credential + gerçek mutation gerekir)
1. Testnet credential zaten kayıtlıysa (`testnet-readonly`) tekrar gerekmez.
2. Kill-switch'i aç ve çalıştır:
```powershell
$env:PYTHONPATH='src'
$env:DCABOT_TRADING_ENABLED='true'
uv run --frozen python tools/run_single_testnet_order.py testnet-readonly BTCUSDT BUY 0.001 20000
```
(Fiyatı güncel testnet BTCUSDT fiyatından uzak, dolmayacak şekilde seç — örn. güncel fiyatın çok altında bir BUY limit, hemen dolup "gör" adımını anlamsızlaştırmasın.)
3. İki onay isteyecek (gönder, iptal) — her birinde tam `EVET` yaz.
4. Çıktıyı (venue_order_id, durum, sorgu sonucu, iptal sonucu — credential/secret içermez) buraya yapıştır.

## Bu geldiğinde Claude'un yapacağı
- STATE.md'yi `evidence_scope=REAL_TESTNET` olarak günceller.
- Sıradaki: **Faz 3.6 — Dolum + restart kurtarma** (süreç ortada öldürülür, yeniden başlayınca tek ekonomik kayıt) için kapsam araştırması.

## Değişmez sınırlar
- Credential, secret, gerçek emir, mutation ve mainnet: Arda onayı olmadan asla. Claude `tools/run_single_testnet_order.py`'yi kendisi hiç çalıştırmaz.
- STATE.md/TASK.md yalnız Claude günceller.

## Kabul
- REAL_TESTNET kanıtı geldiğinde STATE.md güncellenir ve 3.6 brief'i yazılır.
