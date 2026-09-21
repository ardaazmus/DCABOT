# Aktif iş — Faz 5-11 planlandı; Faz 11 Arda'nın dış araştırmasını bekliyor

Faz 3 (P2 testnet) kapalı (`p2-testnet-complete`). Bu oturumda: (1) 20 F-kodu (7 dondurulmuş aile + 13 kalan madde) derinlemesine incelendi, docs/YOL_HARITASI.md'ye Faz 5-10 olarak bağlandı. (2) F22'nin stale `PLAN` kaydı düzeltildi. (3) `docs/P1_KRITIK_ARASTIRMA_FINAL/` dış araştırma paketi (2026-09-09, 48 kaynak) her Faz'a eşlenip kaynak olarak gösterildi. (4) **Faz 11 (Birleşik UI/UX, kapanış fazı) eklendi — Arda'ya anonim araştırma promptu verildi, dış rapor bekleniyor.** Bu yalnız araştırma+belgeleme — hiçbir kod değişmedi. Ayrıntı: STATE.md, docs/KARARLAR.md 2026-09-21 (dört girdi).

## Faz 11 — beklemede, Arda'nın aksiyonu gerekiyor
Anonim UI/UX araştırma promptu Arda'ya sohbette verildi (proje adı/dosya yolu içermez). Arda bunu bir dış araştırma aracına verip raporu getirdiğinde: Claude raporu `docs/UIUX_ARASTIRMA_FINAL/` (veya Arda'nın getirdiği konuma) okuyup mevcut `frontend/src/` yapısını bu kaynağa göre analiz edecek, Faz 5-10'un tüm yüzeylerini kaldıracak bir bilgi mimarisi önerecek ve docs/YOL_HARITASI.md Faz 11'i ayrıntılandıracak. Bu turda erişilebilirlik (yüksek kontrast/ekran okuyucu) kapsam dışı — ayrı iz Faz 9/F30.

## Sıradaki: en az sürtünmeli üç seçenek (dış araştırma kutusu zaten kapalı)
1. **Faz 7 (rebalancing + signal bot):** sıfır blocker, doğrudan yerel implementasyon+test ile başlanabilir.
2. **Faz 9/F27 (paper trading):** sıfır blocker, kalan iş yalnız gerçek REST/WS transport + activation gate.
3. **Faz 10/F20 (strateji şablonu):** sıfır blocker, snapshot/onay kapısı zaten var.

## Daha zor seçenekler (yerel araştırma kutusu hâlâ açık, veya güvenlik çizgisi)
4. **Faz 4 (P3 canary):** mainnet emri — Arda onayı zorunlu, güvenlik çizgisi.
5. **Faz 5 (Futures Grid):** venue liquidation profili seçimi + local Position/Margin owner kanıtı gerekiyor (LCR-12).
6. **Faz 6 (two-leg/hedge):** persistence/recovery ownership kanıtı gerekiyor (LCR-09).
7. **Faz 9/F31 (shared-account bulk actions):** concurrency/transaction boundary kanıtı gerekiyor.

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
- Arda yukarıdaki 7 seçenekten hangisiyle (veya hangileriyle paralel) başlanacağını seçtiğinde Claude o dilimi başlatır.
