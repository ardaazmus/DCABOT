# Aktif iş — Faz 3'ün tüm kod dilimleri bitti; sıradaki adım Faz 3 kapanışı

Faz 3.1-3.7 tamamlandı (bkz. STATE.md, docs/KARARLAR.md). Şu anda Claude'un elinde açık kod görevi yok.

## Sıradaki: Faz 3 kapanışı (docs/YOL_HARITASI.md: "3.7 PASS + bağımsız review → git tag p2-testnet-complete")
P1 kapanışında yapılan işin aynısı: Codex/muse'e dosya-sınırlı, salt-okunur bir bağımsız inceleme brief'i (bu turdaki tüm Faz 3 diff'i — mutation gate, tek dosyada mutation, restart kurtarma, DCA orkestrasyonu — özellikle güvenlik/fail-closed açısından) yazılabilir, sonra `git tag p2-testnet-complete`.

## Arda'nın isteğe bağlı yapabileceği
Testnet hesabındaki 0.0004 BTC açık pozisyonu kapatmak istersen (zararsız, sahte para, zorunlu değil):
```powershell
$env:PYTHONPATH='src'; $env:DCABOT_TRADING_ENABLED='true'; uv run --frozen python tools/run_single_testnet_order.py testnet-readonly BTCUSDT SELL 0.0004 <guncel_fiyata_yakin_bir_deger>
```

## Değişmez sınırlar
- Credential, secret, gerçek emir, mutation ve mainnet: Arda onayı olmadan asla.
- STATE.md/TASK.md yalnız Claude günceller.

## Kabul
- Arda Faz 3 kapanışını (bağımsız review + tag) onayladığında Claude başlatır.
