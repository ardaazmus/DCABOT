# Aktif iş — Q1 kapalı; sırada Q2 (tek yapay zeka: Muse)

**Tam yetki (Arda, bağlayıcı, 2026-09-26):** Tüm kararlar Muse'da;
soru yok. Hedef: 3Commas/Bitsgap paritesi. Kaynak: `docs/KARARLAR.md`.
P4 + Qwen taraması + N2 canlı kanıt en sonda (Arda 2026-09-27).

## Kapalı (bu oturum)
- **Q1:** backtest fiyat+işlem-işareti grafiği + PF backend (3 test) + UI + e2e.
  Sayaç: backtest alt sistemi 1/3.
- **F09a:** DCA trailing TP backend (10 test) + API + UI + e2e.
  Sayaç: motor/sim alt sistemi 1/3.
- **F20a:** bot-copy backend (6 test) + UI + e2e.
  Sayaç: bots alt sistemi 1/3.
- **F10a:** DCA deal brüt/net/ücret backend (5 test) + UI + e2e.
  Sayaç: deals alt sistemi 1/3.
- **B:** bot-replay backend (16 test) + API + UI + e2e (2 test).
  Sayaç: runner alt sistemi 1/3.
- **A:** DCA kurulumu tek-sayfa form + hata-odak kaydırma.
  Sayaç: DCA-UI alt sistemi 1/3.
- **G4:** COMBO-lite backend (25 test) + UI + e2e.
  Sayaç: DCA alt sistemi 3/3 doldu.
- **G3-d:** multi-pair DCA backend (21 test) + UI + e2e.
- **N2-impl:** Telegram fan-out + API + worker + UI (20 test).
- G3-c + G3-b + G3-a + Faz G2 + N1 + W-B8 + W-B6 + W-F7 + Faz G1.

## Sırada
1. **Q2:** korelasyon-matrisi UI; sonra **Q3:** RSI/hacim göstergeleri.
2. **F31-bulk (aday):** bot lifecycle + toplu işlemler (DEFERRED olabilir).
3. **EN SON:** P4 marketler + N2 canlı (Qwen taraması kapalı, KARARLAR'da).
4. G3 canlı likidasyon NO-GO (credential+venue kararı bekler).

## Durum
checker **2516/2516** (1 skip) · vitest 265/265 · e2e 79/79 ·
review=NOT_RUN.

## Değişmez sınırlar (sürüyor)
- Credential/secret dosyaya girmez. Gerçek emir için ayrıca açık
  emir gerekir; anahtar yokken mutation kapıları kapalı.
- Venue likidasyon (canlı) NO-GO — credential+venue kararı bekler.
