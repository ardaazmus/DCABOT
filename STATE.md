# Durum — 2026-09-21

Aktif faz: **Faz 3.4 (Mutation gate kararı) ONAYLANDI — 7 kural belirlendi, kod yok (roadmap tanımı gereği).** Faz 3.1 (`evidence_scope=REAL_TESTNET`), 3.2 (kod tamam, kısmi REAL_TESTNET) kapalı. P1 `p1-demo-complete` etiketiyle kapalı. Dal: codex/latest-state-2026-09-20.
Doğrulanan: tam checker 910/910 PASS; frontend tsc -b temiz, vitest 31/31 PASS; canlı sunucuda `not_configured` durumu ekran görüntüsüyle doğrulandı.
Eksenler: implementation=DONE(3.3) · verification=PASS · evidence_scope=LOCAL_INTEGRATION+kısmi_REAL_TESTNET · review=NOT_RUN(3.3) · deployment=NOT_DEPLOYED

## Faz 3.3 — Salt-okunur hesap ekranı: tamamlandı (bu oturum)
- **Backend (Claude):** `binance_testnet_account.py` genişletildi (gerçek testnet bakiyeleri + `fetch_binance_testnet_open_orders`), iki yeni API uç noktası (`/api/testnet/account`, `/api/testnet/open-orders`), 14 offline test. Bulgu: bu adapter hiç P2.05 kabul kapısından geçmemişti (bkz. docs/KARARLAR.md).
- **Frontend (Codex/muse, dosya-sınırlı brief, Claude doğruladı):** `BinanceAccountPanel.tsx` + test (yeni), `App.tsx`'e yalnız ekleme, `styles.css`'e 3 satır. Yalnız izinli 4 dosyaya dokunuldu. `not_configured` durumu bilinçli olarak sakin tasarlandı (alarm değil, role="status").
- **Claude'un doğrulaması:** diff satır satır incelendi; tsc temiz; vitest 31/31 PASS (8 yeni); tam checker 910/910 PASS; canlı sunucuda credential ayarlanmadan `not_configured` kartı ekran görüntüsüyle doğrulandı. `ready` durumu gerçek credential'la canlı test edilmedi (Claude'un sınırı) — sahte veriyle yazılmış 8 component testi yeterli kanıt kabul edildi.

## Faz 3.2 — REST catch-up (kod tamam) / Faz 3.1 — Reconnect worker (kapalı, REAL_TESTNET)
Ayrıntı git geçmişinde.

## Kodda mevcut
- P2 salt-okunur Binance testnet: public/account/open-orders/user-stream adaptörleri + reconnect worker (REAL_TESTNET) + REST catch-up (offline+kısmi REAL_TESTNET) + hesap/açık-emir API + frontend paneli (tamam).

## Bilinen sınırlar
- Signed mutating request (gerçek emir), mutation ve mainnet: NO-GO.
- Faz 3.3'ün `ready` durumu yalnız sahte veriyle test edildi; gerçek credential'la canlı görünüm henüz teyit edilmedi (istersen Arda credential'ı ayarlayıp `DCABOT_TESTNET_CREDENTIAL_ID` env değişkenini set edip kendisi bakabilir).
- 3.2'nin tam REAL_TESTNET kanıtı 3.5'i bekliyor.
- Simülasyon: OHLC intrabar sırası INDETERMINATE; tam stress ekonomik modeli NO-GO.
- API tek worker'a bağlı. Python 3.13 zorunlu; uv sync --frozen.

## Kararlar (bkz. `docs/KARARLAR.md`)
Faz 3.1-3.3 kapandı. Üçüncü ardışık temiz Codex devri — dosya allowlist disiplini tutarlı çalışıyor.

## Faz 3.4 — Mutation gate kararı (bu oturum, Arda'nın "en güvenli en iyi yolu seç" yetkilendirmesiyle)
7 kural onaylandı (bkz. docs/KARARLAR.md, docs/YOL_HARITASI.md): kill-switch, mevcut `max_entry_notional`'ın mutation'da da uygulanması, execution-anında açık onay, idempotent clientOrderId + durable-before-send (mevcut `AttemptStore` sırası), tek eşzamanlı mutation, cancel aynı disiplin, testnet hard-code. Her madde ya mevcut test edilmiş bir mekanizmayı genişletiyor ya da yalnız bir kısıt ekliyor — sıfırdan icat edilen güvenlik mantığı yok. Kod yazılmadı (roadmap Faz 3.4'ü kasıtlı olarak "belge, kod değil" tanımlıyor).

## Sıradaki adım
**Faz 3.5 — Tek testnet emri:** limit emir gönder → gör → iptal et; journal kaydı. Faz 3.4'ün 7 kuralını uygulayan implementasyon. Kod yazılmadan önce dar bir teknik tasarım (hangi dosyalar, hangi sıra) Arda'ya sunulacak.
