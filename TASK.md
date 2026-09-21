# Aktif iş — Faz 3.7 kodu tamam; REAL_TESTNET kanıtı Arda'yı bekliyor

`fetch_binance_testnet_my_trades`, `application/testnet_dca_session.py`, `tools/run_testnet_dca_deal.py` yazıldı. 5 yeni offline test (biri tam BASE→SAFETY→EXIT döngüsü), tam checker 942/942 PASS. Ayrıntı: STATE.md, docs/KARARLAR.md.

## Arda'nın yapması gereken (Claude yapamaz — gerçek mutation gerekir)
Güncel BTCUSDT fiyatını önce kontrol et (`check_price_and_band.py` benzeri, ya da testnet.binance.vision arayüzünden), sonra:
```powershell
$env:PYTHONPATH='src'
$env:DCABOT_TRADING_ENABLED='true'
uv run --frozen python tools/run_testnet_dca_deal.py testnet-readonly BTCUSDT BTC --base-qty 0.001 --safety-qty 0.001 --safety-count 1 --deviation 0.03 --take-profit 0.01
```
- `--deviation 0.03`: safety, mark anchor'ın %3 altına düşerse tetiklenir.
- `--take-profit 0.01`: TP, ortalama girişin %1 üstünde.
- BASE emri için onay isteyecek (EVET yaz). Sonra döngü: "Fiyati/dolumlari kontrol et [k], cik [q]" — `k` yazıp Enter'a bas, tekrar tekrar (fiyat hareket edip safety/TP tetiklenene kadar). Her yeni emir (safety, TP) için ayrıca EVET istenecek.
- İstersen istediğin an `q` ile çıkabilirsin (yarım kalan emirler testnet'te açık kalır, elle takip edilmeli — sonraki bir `run_single_testnet_order.py`/`recover_stuck_attempts` çalıştırması attempt-seviyesinde kurtarır ama açık venue emrini iptal etmez).
- Çıktının tamamını (credential/secret içermez) buraya yapıştır.

## Bu geldiğinde Claude'un yapacağı
- STATE.md'yi `evidence_scope=REAL_TESTNET` olarak günceller.
- Faz 3'ün kendi kapanış ölçütünü (bağımsız review + `git tag p2-testnet-complete`) çalıştırır.

## Değişmez sınırlar
- Credential, secret, gerçek emir, mutation ve mainnet: Arda onayı olmadan asla.
- STATE.md/TASK.md yalnız Claude günceller.

## Kabul
- REAL_TESTNET kanıtı geldiğinde STATE.md güncellenir ve Faz 3 kapanışı başlar.
