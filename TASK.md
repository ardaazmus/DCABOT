# Aktif iş — Faz 5-8 yol haritasına bağlandı; sıradaki adım Arda'nın seçimi

Faz 3 (P2 testnet) kapalı (`p2-testnet-complete`). Bu oturumda Arda'nın "tüm kapalı olanları aç" talimatıyla 7 dondurulmuş özellik ailesi (Futures Grid/Reverse-Infinity, two-leg/hedge, rebalancing, signal bot, çoklu bot/pair, LLM dış-parça) derinlemesine incelendi ve docs/YOL_HARITASI.md'ye Faz 5-8 olarak bağlandı (olgunluk sırasıyla). Bu yalnız araştırma+belgeleme — hiçbir kod değişmedi, hiçbir yeni sözleşme yazılmadı. Ayrıntı: STATE.md, docs/KARARLAR.md 2026-09-21 "Faz 5-8 açılış".

## Sıradaki: iki paralel seçenek, ikisi de Arda'nın kapsam onayını bekliyor
1. **Faz 4 (P3 — gerçek Binance, sınırlı canary):** mainnet emri, tutar limiti, kill-switch, canary süresi/başarı ölçütü. Güvenlik çizgisi — AGENTS.md, Arda onayı zorunlu.
2. **Faz 5 (Futures Grid + Reverse/Infinity varyantı):** en olgun dondurulmuş aile (1257+ satır kod, 57+ test zaten var). İlk adım kod değil — venue liquidation/funding için resmi exact oracle bulunamaması sorununu kapatacak bir araştırma kutusu (AGENTS.md, ≤1 oturum). Ayrıca Binance Futures ayrı bir venue/mutation katmanı gerektirir (P2'nin Spot gate'i doğrudan taşınmaz).

İkisi birbirini bloklamaz, paralel ilerleyebilir.

## Arda'nın isteğe bağlı yapabileceği
Testnet hesabındaki 0.0004 BTC açık pozisyonu kapatmak istersen (zararsız, sahte para, zorunlu değil):
```powershell
$env:PYTHONPATH='src'; $env:DCABOT_TRADING_ENABLED='true'; uv run --frozen python tools/run_single_testnet_order.py testnet-readonly BTCUSDT SELL 0.0004 <guncel_fiyata_yakin_bir_deger>
```

## Değişmez sınırlar
- Credential, secret, gerçek emir, mutation ve mainnet: Arda onayı olmadan asla.
- STATE.md/TASK.md yalnız Claude günceller.

## Kabul
- Arda Faz 4 (mainnet kapsamı) VEYA Faz 5 (Futures Grid araştırma kutusu) için onay/tercih verdiğinde Claude o dilimi başlatır.
