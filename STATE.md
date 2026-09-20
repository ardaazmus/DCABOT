# Durum — 2026-09-20

Aktif faz: Faz 2 tamamen kapandı (2.1-2.5). Dal: codex/latest-state-2026-09-20.
Doğrulanan: tam checker 880/880 PASS (0 skip); frontend tsc -b temiz, vitest 22/22 PASS.
Eksenler: implementation=IN_PROGRESS · verification=PASS · evidence_scope=LOCAL_INTEGRATION · review=NOT_RUN · deployment=NOT_DEPLOYED

## Faz 2.5 — Stress modeli (bu oturum, Claude yaptı, delege edilmedi)
- **Önce araştırıldı:** `docs/archive/arastirma-promptlari/P1.16.i.b_...md` ve `evidence/P1.16.i.b/SONUC.md` yeniden okundu. Rapor bağımsız kontrolde iki yerde çelişkili çıktı verdi (T-07 sayısal, T-12 seed/identity) ve `ReserveState` örneği kendi `available>=0` invariant'ını ihlal etti. Sonuç: tam stress ekonomik modeli (spread/latency/queue/reserve) **`DEFERRED/NO-GO` olarak kaldı** — bkz. docs/KARARLAR.md.
- **Uygulanan dar dilim:** yeni bir isimli profil — `historical_demo_btcusdt_1h_stress_slippage_v1` (`src/dcabot/application/historical_profiles.py`, `config/historical_demo_btcusdt_1h_stress_slippage_v1.json`) — mevcut demo config'in birebir kopyası, yalnız `slippage="0.002"`. Yeni ekonomik kod yok; mevcut exact `config.slippage` mekanizması (Fraction) kullanıldı.
- **Neden Codex'e gitmedi:** mevcut UI zaten profil seçiciyle yeni profili otomatik listeliyor, mevcut Faz 2.3 compare ekranı iki slippage koşusunu yan yana göstermeye zaten yeterli — frontend'e hiç dokunulmadı. Kalan iş (`application/historical_profiles.py`, config JSON) işbölümü kuralının Claude-only tarafına giriyor.
- **Doğrulama:** yeni bağımsız oracle testi (`test_stress_slippage_profile_shifts_the_base_fill_price_deterministically`: bar open=100 → base fill=100, stress fill=100.2, elle hesaplandı); profil registry + API profil listesi testleri güncellendi; tam checker 880/880 PASS; canlı tarayıcıda `/api/historical-profiles` ve `/api/datasets/{id}/run-plan?profile_id=...` her iki profil için ayrı `config_hash` ile doğrulandı, UI dropdown'ında yeni profil göründü.

## Faz 2.4 tamamlama — aksiyon tablosuna klavye erişimi (önceki oturum, Codex uyguladı, Claude doğruladı+düzeltti)
- **Uygulayan:** Codex/Muse, TASK.md brief'i ile, yalnız izinli 3 dosyaya dokunarak (`DatasetCatalogPanel.tsx`, `styles.css`, yeni `DatasetCatalogPanel.test.tsx`). Diff ~76 satır.
- **Claude'un düzeltmesi:** event bubbling (Copy butonu → satır seçimi) `onRowKeyDown`'a `event.target !== event.currentTarget` koruması eklenerek kapatıldı.
- **Claude'un doğrulaması:** diff satır satır incelendi; tsc temiz, vitest 22/22 PASS; tam checker PASS; canlı tarayıcıda gerçek `KeyboardEvent('Enter')` dispatch edilip satır+marker eşzamanlı `aria-pressed=true` oldu.

## Ajanlar arası işbölümü — durum
İki Codex devri (Faz 2.4) temiz ve dosya allowlist'ine sadık kaldı. Faz 2.5'te delegasyon gerekmedi çünkü kalan iş tamamen kritik/config katmanındaydı ve UI tarafı zaten mevcut bileşenlerin yeniden kullanımıydı — bu da doğru "verimlilik" kararıydı (yeni UI kodu icat etmek yerine sıfır yeni kod).

## Faz 2.1-2.3 özeti (önceki dilimler — ayrıntı git geçmişinde)
Sıralı deal restart + deal kimliği, Faz 2.2 ekonomik metrik seti, Faz 2.3 reproduce+compare. Proje temizliği: 29 araştırma dosyası arşivlendi, `.cluster/` silindi.

## Kodda mevcut
- Yerel arayüz (FastAPI 127.0.0.1:8000 + React/Vite 5173): veri seti kaydı, public indirme, kalite raporu, OHLC grafik (etkileşimli marker, klavye dahil), doğrulama, sıralı deal + Faz 2.2 metrikleri destekli simülasyon, SQLite kayıt/listesi, reproduce doğrulama, iki-run karşılaştırma, 4 historical profil (paper, demo v1, demo stress-slippage v1, demo fixed-slice v1).
- CLI tools/bot.py: demo, init/replay/status/audit, preview.
- Çekirdek: exact Decimal/Fraction ladder, net TP, drawdown; idempotent SQLite kayıtları.
- P2 salt-okunur Binance testnet sınırı: public, account, user-stream adaptörleri.

## Bilinen sınırlar
- Signed REST/WS emir, mutation ve mainnet: NO-GO. Gerçek reconnect worker ve REST catch-up yok.
- Simülasyon: OHLC intrabar sırası INDETERMINATE; gerçek likidite modeli yok. Tam stress ekonomik modeli (spread/latency/queue/reserve) NO-GO — bkz. docs/KARARLAR.md 2026-09-20.
- API tek worker'a bağlı. Python 3.13 zorunlu; uv sync --frozen.

## Kararlar (2026-09-20, Claude tarafından alındı — bkz. `docs/KARARLAR.md`)
Arda çalışma kuralını netleştirdi: ürün/teknik kararları Claude alır, gerekçesiyle işaretler (credential/gerçek emir/mainnet hariç). Sıralı deal persistence, Faz 2 dondurma listesi onaylandı; testnet mutation gate ertelendi; Claude/Codex işbölümü kuralı doğrulandı; Faz 2.5 stress modeli NO-GO + dar slippage-profili ACCEPT.

## Sıradaki adım
Faz 2 (P1 kapanışı) tamamen kapandı: 2.1, 2.1b, 2.2, 2.3, 2.4, 2.5 hepsi tamam. Kapanış ölçütü docs/YOL_HARITASI.md'de: "temiz klonda README komutlarıyla 9 adımlık akış hatasız çalışır → bağımsız review APPROVED → `git tag p1-demo-complete`." Sırada: bu kapanış ölçütünü (uçtan uca temiz-klon doğrulama + review) çalıştırmak, ya da Arda onaylarsa doğrudan Faz 3'e (P2 gerçek Binance testnet) geçmek — bu ikisi arasında seçim Arda'nın product-scope kararı, TASK.md'de açık soru olarak bırakıldı.
