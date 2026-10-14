# Durum — 2026-09-27 (tek yapay zeka: Muse)

**Yetki (Arda, bağlayıcı):** Proje bitene kadar tüm kararlar Muse'da;
soru sorulmaz. Hedef: minimum 3Commas/Bitsgap spot/futures DCA+grid
paritesi. Sınır: gerçek emir için ayrıca açık emir gerekir; anahtar
yokken mutation kapıları kapalı.

Aktif iş: **Q2 kapalı; sırada Q3.** Kaynak makine: notebook (2026-10-14).
- **KAPALI (bu oturum): Q1** backtest fiyat+işlem grafiği + PF.
- **KAPALI (bu oturum): F09a** DCA trailing TP (motor+API+UI+e2e).
- **KAPALI (bu oturum): F20a** bot-copy; **F10a** deal brüt/net.
- **KAPALI (bu oturum): B** replay; **A** tek-sayfa form; **G4**
  COMBO-lite; **G3-d** multi-pair; **N2-impl**.
- HAZIR: N2 Telegram (canlı kanıt en sonda, Arda kararı).
- Kalan: G3 canlı likidasyon (NO-GO, credential+venue kararı).
Doğrulanan: checker **2528/2528 OK** (1 skip), vitest 267/267,
tsc temiz, e2e 80/80 (yerel; CI 64, görsel/venue/kasa ayrı).
Eksenler: implementation=COMPLETE (Q1) · verification=PASS ·
evidence_scope=LOCAL_INTEGRATION · review=NOT_RUN ·
deployment=NOT_DEPLOYED

## Bilinen sınırlar
- Bot + paper runtime/deals/events/snapshot + sistem olay kaydı
  SQLite'da (WAL); v1 deal'ler ve webhook dosyada.
- Mainnet kesin NO-GO; testnet mutation kapalı (anahtar yok).
  Venue likidasyon (canlı) NO-GO — credential+venue kararı bekler.
  Fiyat tick SSE'de yok (DEFERRED). Reverse/Infinity DEFERRED.
  Backtest tek-sembol; combo-kapanışı modellemez.
  Replay max 7 gün, tek koşu; kurallar güncel venue kuralları.
  İptal deal'de brüt tanımsız; DCA paper'da funding yok.
  Trailing: bar-kapanışı modeli; testnet `decision()` sabit TP.
- Portföy grid botunu bütçeden sayar; canlı grid P&L portföyde yok.
- review=NOT_RUN. `web/` + Faz W/G çalışması commitli değil.

## Arda kararları (hepsi Muse'a devredildi, kapalı)
Grid (yapılacak), bildirim (Telegram+uygulama-içi), testnet bot başına
onay (evet), masaüstü öncelikli, canary DRAFT değerleri, P4 (OKX+Bybit),
Pine DEFERRED, HCM W-F9'da, ADX/marjin defaultları. Bkz. KARARLAR.md.
P4 + Qwen taraması + N2 canlı kanıt en sonda (2026-09-27).
Sıra: Q3 → F31-bulk (aday) → en son P4+N2-canlı.
