# Durum — 2026-09-21

Aktif faz: **Faz 3 (P2 testnet) resmen kapandı — `p2-testnet-complete` etiketlendi.** P1 `p1-demo-complete` ile kapalı. Sırada: Faz 4 (P3, gerçek Binance sınırlı canary) kapsam kararı, Arda'yı bekliyor. Dal: codex/latest-state-2026-09-20.
Doğrulanan: tam checker 948/948 PASS; 3.1/3.5/3.6 tam REAL_TESTNET, 3.2/3.7 kısmi REAL_TESTNET; bağımsız review APPROVED_WITH_FINDINGS (2 gerçek bulgu, aynı gün düzeltildi).
Eksenler: implementation=DONE(Faz 3) · verification=PASS · evidence_scope=REAL_TESTNET(3.1,3.5,3.6)+kısmi(3.2,3.7) · review=APPROVED_WITH_FINDINGS(Faz 3 kapanışı) · deployment=NOT_DEPLOYED

## Faz 3 kapanışı — bağımsız review + düzeltme (bu oturum)
- **Review:** bu oturumdan farklı, salt-okunur ayrı bir ajana Faz 3'ün tüm diff'i (`d2dd43f^..60ca267`, 33 dosya) incelettirildi — P1 kapanışındaki Codex/muse deseninin karşılığı. Sonuç `APPROVED_WITH_FINDINGS`: 7 mutation-gate kuralından 5'i, `can_transition` düzeltmesi, `_fee_in_quote_asset`, `engine.py`'ye dokunulmadığı, credential sızıntısı olmadığı — hepsi teyit edildi.
- **F1 (HIGH, düzeltildi):** `cancel_gated_testnet_order` `AttemptStore` disiplininden hiç geçmiyordu (yalnız kill-switch+onay). Artık placement ile birebir aynı `prepare()→persist()→mark_sending()` + rejected/unknown ayrımını kullanıyor.
- **F2 (MEDIUM/HIGH, düzeltildi):** transport hatasıyla UNKNOWN'a düşen bir attempt "in-flight" sayılmıyordu — hemen ardından ikinci bir emir gönderilebilirdi; `recover_stuck_attempts` de yalnız restart-kaynaklı UNKNOWN'ları görüyordu. Artık `_require_no_blocking_attempts()` her UNKNOWN/RECONCILING'de reddediyor, `recover_stuck_attempts` tüm çözülebilir attempt'leri çözüyor. UNRESOLVED bilinçli olarak bloklamıyor (Faz 3.6'nın kanıtlanmış davranışını korumak için).
- Doğrulama: 9 yeni offline test, tam checker 948/948 PASS. Ayrıntı: `docs/KARARLAR.md`.
- **`git tag p2-testnet-complete` atıldı.**

## Faz 3.1-3.7 özeti (önceki turlar — ayrıntı git geçmişinde ve docs/KARARLAR.md'de)
3.1 reconnect worker (REAL_TESTNET), 3.2 REST catch-up (kısmi REAL_TESTNET), 3.3 salt-okunur hesap ekranı (tamam), 3.4 mutation gate 7 kuralı (karar), 3.5 tek testnet emri (REAL_TESTNET), 3.6 restart kurtarma (REAL_TESTNET), 3.7 DCA botu uçtan uca (kısmi REAL_TESTNET — BASE bacağı canlı, SAFETY/EXIT offline).

## Kodda mevcut
- P2 Binance testnet: public/account/open-orders/user-stream/my-trades adaptörleri + reconnect worker + REST catch-up + mutation gate (place VE cancel aynı disiplinde) + tek dosyada mutation + restart kurtarma + DCA orkestrasyonu — tamamı canlı veya offline exact kanıtlı, bağımsız review'dan geçti.

## Bilinen sınırlar
- DCA session state durable değil (yalnız process belleği) — gelecekteki iş.
- `PERCENT_PRICE_BY_SIDE` offline pre-check yok (DEFERRED).
- Testnet hesabında 0.0004 BTC açık pozisyon (zararsız, sahte para; Arda isterse elle SELL edebilir).
- Simülasyon: OHLC intrabar sırası INDETERMINATE; tam stress ekonomik modeli NO-GO.
- Mainnet: kesin NO-GO, Arda'nın açık onayı olmadan asla (Faz 4).

## Kararlar (bkz. `docs/KARARLAR.md`)
Faz 3 bağımsız review + 2 gerçek bulgunun düzeltilmesiyle kapandı, `p2-testnet-complete` etiketlendi.

## Sıradaki adım
Faz 4 (P3 — gerçek Binance, sınırlı canary) kapsam kararı: küçük sabit tutar üst sınırı, kill-switch, günlük kayıp limiti, canary süresi/başarı ölçütü tanımı. Arda'nın açık onayı olmadan mainnet emri yok (AGENTS.md, değişmez). Henüz başlatılmadı.
