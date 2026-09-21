# Aktif iş — Faz 5-10 yol haritasına bağlandı; sıradaki adım Arda'nın seçimi

Faz 3 (P2 testnet) kapalı (`p2-testnet-complete`). Bu oturumda tam bir gap-analizi yapıldı: 20 F-kodu (7 dondurulmuş aile + 13 kalan madde) derinlemesine incelendi, docs/YOL_HARITASI.md'ye Faz 5-10 olarak bağlandı (olgunluk sırasıyla). Ayrıca F22'nin stale `PLAN` kaydı düzeltildi. Bu yalnız araştırma+belgeleme — hiçbir kod değişmedi. Ayrıntı: STATE.md, docs/KARARLAR.md 2026-09-21 ("Faz 5-8 açılış", "Faz 9-10 açılış").

## Sıradaki: dört paralel seçenek, hepsi Arda'nın kapsam onayını bekliyor
1. **Faz 4 (P3 — gerçek Binance, sınırlı canary):** mainnet emri, tutar limiti, kill-switch, canary ölçütü. Güvenlik çizgisi — Arda onayı zorunlu.
2. **Faz 5 (Futures Grid + Reverse/Infinity):** en olgun dondurulmuş aile. İlk adım: venue liquidation/funding oracle sorunu için araştırma kutusu.
3. **Faz 9 (P1 kapanış borcu):** F27 (paper trading, en olgun — yalnız transport gate kapalı) ile başlamak en mantıklı.
4. **Faz 10 (yeni aileler):** F20 (strateji şablonu, en olgun — snapshot/onay kapısı zaten var) ile başlamak en mantıklı.

Hepsi birbirini bloklamaz, paralel ilerleyebilir.

## Arda'nın isteğe bağlı yapabileceği
Testnet hesabındaki 0.0004 BTC açık pozisyonu kapatmak istersen (zararsız, sahte para, zorunlu değil):
```powershell
$env:PYTHONPATH='src'; $env:DCABOT_TRADING_ENABLED='true'; uv run --frozen python tools/run_single_testnet_order.py testnet-readonly BTCUSDT SELL 0.0004 <guncel_fiyata_yakin_bir_deger>
```

## Değişmez sınırlar
- Credential, secret, gerçek emir, mutation ve mainnet: Arda onayı olmadan asla.
- STATE.md/TASK.md yalnız Claude günceller.

## Kabul
- Arda Faz 4/5/9/10'dan hangisiyle (veya hangileriyle paralel) başlanacağını seçtiğinde Claude o dilimi başlatır.
