# Durum — 2026-09-21

Aktif faz: **Faz 3.7 (DCA botu uçtan uca) kodu tamam, offline doğrulandı; REAL_TESTNET kanıtı Arda'yı bekliyor.** Faz 3.1-3.6 kapalı (3.1, 3.5, 3.6 canlı kanıtlı). P1 `p1-demo-complete` etiketiyle kapalı. Dal: codex/latest-state-2026-09-20.
Doğrulanan: tam checker 942/942 PASS.
Eksenler: implementation=DONE(3.7 kod) · verification=PASS(offline) · evidence_scope=LOCAL_INTEGRATION(3.7; REAL_TESTNET Arda'yı bekliyor) · review=NOT_RUN(3.7) · deployment=NOT_DEPLOYED

## Faz 3.7 — DCA botu testnet'te uçtan uca (bu oturum, Claude yaptı)
- **Yeni icat değil:** çekirdek `engine.py`'nin `State/apply/decision`'ı (Faz 2'nin de kullandığı) gerçek testnet mutation'larına bağlandı.
- **Yeni:** `fetch_binance_testnet_my_trades` (exact fill fiyat/miktar/fee — order-status yalnız kümülatif verir). `application/testnet_dca_session.py`: `build_live_config`, `place_next_action`, `sync_order_fills` (execution_id dedup, tam dolunca `ORDER_FINAL`).
- **Bulunan gerçek uyumsuzluk (offline testte, canlıya çıkmadan):** `engine.py` ücretin her zaman quote-asset olmasını istiyor; gerçek BUY dolumları genelde base-asset ücret kesiyor. `_fee_in_quote_asset()` aynı fill'in kendi fiyatıyla exact dönüştürüyor, desteklenmeyen asset'te fail-closed.
- **Test:** 5 yeni offline test, biri tam BASE→SAFETY:1→EXIT döngüsünü (anchor=100, safety=95, ortalama=97.5, TP=99.45) elle doğrulanmış değerlerle kanıtlıyor. Tam checker 942/942 PASS.
- **Bilinen sınır:** DCA session state yalnız process belleğinde, durable değil — crash deal'i kaybeder (attempt-seviyesi kurtarma yine çalışır). Durable live-deal store gelecekteki iş.
- **REAL_TESTNET durumu:** `tools/run_testnet_dca_deal.py` — Arda'nın çalıştırması bekleniyor.

## Faz 3.1-3.6 özeti (önceki turlar — ayrıntı git geçmişinde)
3.1 reconnect worker (REAL_TESTNET), 3.2 REST catch-up (kod tamam), 3.3 salt-okunur hesap ekranı (tamam), 3.4 mutation gate 7 kuralı (karar), 3.5 tek testnet emri (REAL_TESTNET), 3.6 restart kurtarma (REAL_TESTNET).

## Kodda mevcut
- P2 Binance testnet: tüm katmanlar + DCA orkestrasyonu (`testnet_dca_session.py`) + CLI kanıt araçları (biri tam DCA deal'i, biri deterministik crash-simülasyonu).

## Bilinen sınırlar
- Faz 3.7'nin REAL_TESTNET kanıtı yok.
- DCA session state durable değil (yalnız process belleği).
- `PERCENT_PRICE_BY_SIDE` offline pre-check yok (DEFERRED).
- Simülasyon: OHLC intrabar sırası INDETERMINATE; tam stress ekonomik modeli NO-GO.
- Mainnet: kesin NO-GO, Arda'nın açık onayı olmadan asla (Faz 4).

## Kararlar (bkz. `docs/KARARLAR.md`)
Faz 3.7 kapsamı onaylandı (elle adımlanan CLI, tam otonom worker değil), implementasyon sırasında fee-asset uyumsuzluğu bulunup düzeltildi.

## Sıradaki adım
Arda'nın `tools/run_testnet_dca_deal.py`'yi çalıştırıp gerçek bir DCA deal'i (base + varsa safety + TP) tamamlaması bekleniyor. Bu, Faz 3'ün SON kod dilimi — kanıt geldiğinde Faz 3'ün kendi kapanış ölçütü (bağımsız review + `git tag p2-testnet-complete`) sırada.
