# Aktif iş — Faz 3 kapandı; Faz 4 kapsam kararı bekleniyor

Faz 3 (P2 testnet) tamamen kapandı: tüm dilimler PASS, bağımsız review `APPROVED_WITH_FINDINGS`, 2 gerçek bulgu (cancel'in AttemptStore disiplininden geçmemesi; UNKNOWN attempt'in yeni mutation'ı bloklamaması) aynı gün düzeltildi, `git tag p2-testnet-complete` atıldı. Ayrıntı: STATE.md, docs/KARARLAR.md.

## Sıradaki: Faz 4 (P3 — gerçek Binance, sınırlı canary) kapsam kararı
docs/YOL_HARITASI.md'nin Faz 4 taslağı: küçük sabit tutar üst sınırı, kill-switch, günlük kayıp limiti, canary süresi ve başarı ölçütü (işlem sayısı, sıfır duplicate, çözülmemiş UNKNOWN yok) tanımı, paketleme/tek-worker sınırı. Bu bir güvenlik çizgisi kararı — Arda'nın açık onayı gerekir (AGENTS.md, değişmez).

## Arda'nın isteğe bağlı yapabileceği
Testnet hesabındaki 0.0004 BTC açık pozisyonu kapatmak istersen (zararsız, sahte para, zorunlu değil):
```powershell
$env:PYTHONPATH='src'; $env:DCABOT_TRADING_ENABLED='true'; uv run --frozen python tools/run_single_testnet_order.py testnet-readonly BTCUSDT SELL 0.0004 <guncel_fiyata_yakin_bir_deger>
```

## Değişmez sınırlar
- Credential, secret, gerçek emir, mutation ve mainnet: Arda onayı olmadan asla.
- STATE.md/TASK.md yalnız Claude günceller.

## Kabul
- Arda Faz 4 kapsamını (mainnet, tutar limiti, kill-switch, canary süresi) onayladığında Claude başlatır.
