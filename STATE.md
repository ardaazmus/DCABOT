# Durum — 2026-09-21

Aktif faz: **Faz 3 (P2 testnet) kapalı — `p2-testnet-complete`.** Faz 5-8 (7 dondurulmuş özellik ailesi: Futures Grid/Reverse-Infinity, two-leg/hedge, rebalancing, signal bot, çoklu bot/pair, LLM dış-parça) bu oturumda dondurmadan çıkarılıp docs/YOL_HARITASI.md'ye bağlandı. Sırada: Faz 4 (P3 canary) VE Faz 5 (Futures Grid) kapsam kararları, ikisi de Arda'yı bekliyor, paralel ilerleyebilirler. Dal: codex/latest-state-2026-09-20.
Doğrulanan: tam checker 948/948 PASS. Faz 3: 3.1/3.5/3.6 tam REAL_TESTNET, 3.2/3.7 kısmi; bağımsız review APPROVED_WITH_FINDINGS (2 bulgu aynı gün düzeltildi). Faz 5-8: yalnız araştırma yapıldı, kod değişmedi.
Eksenler: implementation=DONE(Faz 3)·PLAN(Faz 5-8) · verification=PASS · evidence_scope=REAL_TESTNET(3.1,3.5,3.6)+kısmi(3.2,3.7) · review=APPROVED_WITH_FINDINGS(Faz3) · deployment=NOT_DEPLOYED

## Faz 5-8 açılışı (bu oturum) — araştırma tamam, implementasyon başlamadı
- Arda: "tüm kapalı olanları aç yol haritasına bağla ve derinlemesine incele". Bağımsız bir ajana (salt-okunur) tüm `src/dcabot` + `docs/OZELLIK_MATRISI.md` + `docs/URUN_KAPSAMI.md` taratıldı.
- Sonuç: 5 ailede zaten önemli miktarda offline-test-edilmiş kod var (Futures Grid en fazla: 1257+satır çekirdek + futures_dca 17+7 dosya, 57+ test); 2 ailede (çoklu bot/pair, LLM dış-parça) SIFIR kod var. Hiçbirinin API/UI bağlantısı yok.
- Olgunluk sırasıyla docs/YOL_HARITASI.md'ye Faz 5 (Futures Grid+Reverse/Infinity) → Faz 6 (two-leg/hedge) → Faz 7 (rebalancing+signal bot) → Faz 8 (çoklu bot/pair+LLM dış-parça) olarak eklendi; venue ekseninden (P1-P4) bağımsız paralel eksen. Tam envanter: docs/KARARLAR.md 2026-09-21 "Faz 5-8 açılış".
- Her fazın ilk adımı kendi sözleşme boşluğunu kapatan bir araştırma kutusu — kanıtsız implementasyona geçilmiyor (AGENTS.md evidence-first korunuyor).
- Ayrıca: Faz 2 dondurma kararının gerekçesi düzeltildi — asıl sebep sözleşme olgunluğu, rekabet emsali yalnız destekleyici gözlemdi (önceki kayıtta birinci sebep gibi yazılmıştı).

## Faz 3 kapanışı (önceki tur, özet)
Bağımsız review `APPROVED_WITH_FINDINGS`: F1 (cancel AttemptStore disiplininden geçmiyordu) ve F2 (UNKNOWN attempt yeni mutation'ı bloklamıyordu) aynı gün düzeltildi, 9 yeni test, `git tag p2-testnet-complete`. Ayrıntı: docs/KARARLAR.md.

## Faz 3.1-3.7 özeti (git geçmişinde ve docs/KARARLAR.md'de)
3.1 reconnect worker (REAL_TESTNET), 3.2 REST catch-up (kısmi), 3.3 salt-okunur hesap ekranı, 3.4 mutation gate 7 kuralı, 3.5 tek testnet emri (REAL_TESTNET), 3.6 restart kurtarma (REAL_TESTNET), 3.7 DCA botu uçtan uca (kısmi).

## Kodda mevcut
- P2 Binance testnet: public/account/open-orders/user-stream/my-trades adaptörleri + reconnect worker + REST catch-up + mutation gate (place VE cancel) + restart kurtarma + DCA orkestrasyonu — bağımsız review'dan geçti.
- Faz 5-8 aileleri: yalnız çekirdek/domain matematiği ve kimlik katmanları (bkz. yukarı) — hiçbiri API/UI'a bağlı değil.

## Bilinen sınırlar
- DCA session state durable değil (yalnız process belleği).
- Testnet hesabında 0.0004 BTC açık pozisyon (zararsız).
- Mainnet: kesin NO-GO, Arda'nın açık onayı olmadan asla.
- Faz 5-8: hiçbiri implementasyona hazır değil — her biri kendi araştırma kutusunu bekliyor.

## Kararlar (bkz. `docs/KARARLAR.md`)
Faz 3 kapandı (`p2-testnet-complete`). Faz 5-8 açıldı, araştırma tamam, implementasyon henüz başlamadı.

## Sıradaki adım
Arda'nın seçimi: Faz 4 (P3 canary) kapsam kararı, ve/veya Faz 5 (Futures Grid) için araştırma kutusu (venue liquidation/funding oracle sorunu). İkisi paralel ilerleyebilir.
