# Aktif iş — Faz 5-11 planlandı; Faz 11 tasarım kararı hazır, implementasyon bekliyor

Faz 3 (P2 testnet) kapalı (`p2-testnet-complete`). Bu oturumda: (1) 20 F-kodu (7 dondurulmuş aile + 13 kalan madde) incelendi, Faz 5-10'a bağlandı, dış araştırma paketiyle (`docs/P1_KRITIK_ARASTIRMA_FINAL/`) eşlendi. (2) F22'nin stale kaydı düzeltildi. (3) **Faz 11 (Birleşik UI/UX): Arda iki bağımsız anonim araştırma raporu getirdi (`docs/UIUX_ARASTIRMA_FINAL/`), analiz edilip 9 maddelik somut tasarım kararı docs/YOL_HARITASI.md'ye yazıldı.** Bu yalnız araştırma+tasarım+belgeleme — hiçbir kod değişmedi. Ayrıntı: STATE.md, docs/KARARLAR.md 2026-09-21.

## Faz 11 — tasarım hazır, ilk kod dilimi Arda'nın onayını bekliyor
Sıradaki somut adım: 5-bölümlü sidebar iskeleti (`frontend/src/App.tsx`) + 3-katmanlı semantic design token tema mimarisi (`frontend/src/styles.css`, şu an yalnız 6 düz token var). Bu, Faz 5-10'un 20 F-kodunun bağlanacağı zemin. Tasarım kararının 9 maddesi docs/YOL_HARITASI.md Faz 11'de.

## Sıradaki: en az sürtünmeli seçenekler (dış araştırma/tasarım kutusu zaten kapalı)
1. **Faz 11 ilk dilimi:** sidebar iskeleti + token mimarisi — tasarım kararı hazır, doğrudan implementasyona geçilebilir.
2. **Faz 7 (rebalancing + signal bot):** sıfır blocker.
3. **Faz 9/F27 (paper trading):** sıfır blocker, kalan iş yalnız gerçek REST/WS transport.
4. **Faz 10/F20 (strateji şablonu):** sıfır blocker, snapshot/onay kapısı zaten var.

## Daha zor seçenekler (yerel araştırma kutusu hâlâ açık, veya güvenlik çizgisi)
5. **Faz 4 (P3 canary):** mainnet emri — Arda onayı zorunlu, güvenlik çizgisi.
6. **Faz 5 (Futures Grid):** venue liquidation profili seçimi gerekiyor (LCR-12).
7. **Faz 6 (two-leg/hedge):** persistence/recovery ownership kanıtı gerekiyor (LCR-09).
8. **Faz 9/F31 (shared-account bulk actions):** concurrency/transaction boundary kanıtı gerekiyor.

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
- Arda yukarıdaki 8 seçenekten hangisiyle (veya hangileriyle paralel) başlanacağını seçtiğinde Claude o dilimi başlatır.
