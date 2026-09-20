# Durum — 2026-09-20

Aktif faz: Faz 2.4 — etkileşimli marker, **Codex'e devredildi** (TASK.md brief'i, dosya sınırlı). Faz 2.1-2.3 kapandı. Dal: codex/latest-state-2026-09-20.
Doğrulanan: uv sync --frozen başarılı; tam checker 879/879 PASS (0 skip); frontend tsc -b temiz, vitest 13/13 PASS.
Eksenler: implementation=IN_PROGRESS · verification=PASS · evidence_scope=LOCAL_INTEGRATION · review=NOT_RUN · deployment=NOT_DEPLOYED

## Faz 2.3 — Reproduce + Compare (bu oturum, uygulandı ve canlı test edildi)
- **Reproduce** (`POST /api/historical-runs/{run_id}/reproduce`): kayıtlı run'ın `dataset_id` + stored config snapshot + stored `config_hash`'ı ile `simulate_historical_ohlcv`'i yeniden çalıştırır; yeni capture'ın `result_sha256`/`canonical_input_sha256`/`execution.identity_sha256`'ını kayıtlıyla karşılaştırır. Yerel artifact `dataset_preflight`'ta değişmişse `REPRODUCE_ARTIFACT_CHANGED` ile fail-closed reddeder, hiçbir şey yazmaz. Fixed-slice run'ları hiç kaydedilmediği için yalnız `historical_ohlcv_v1` modeli desteklenir (kontrol edilip reddediliyor).
- **Canlı kanıt:** Eski (bugünkü Faz 2.2 alanları eklenmeden önce kaydedilmiş) bir run'da `reproduced=false, result_sha256_match=false` (şema değişti, doğru tespit); az önce yeni kodla kaydedilen bir run'da `reproduced=true`, tüm hash'ler eşit — fonksiyon gerçek Binance dataset'i ve gerçek SQLite store ile canlı doğrulandı.
- **Compare** (frontend, yeni backend endpoint gerekmedi): `SavedRunsPanel`'e checkbox tabanlı 2-run seçimi + "Karşılaştır" ekranı eklendi (`App.tsx`, `SavedRunsPanel.tsx`, `styles.css`). İki `GET /api/historical-runs/{run_id}` çağrısını paralel yapıp özet alanlarını (PnL, fees, max drawdown, action/deal count, ortalama giriş, pozisyonda kalma süresi, result SHA-256) yan yana tablo halinde gösterir; farklı değerler amber vurgulanır.
- **Canlı kanıt:** Bugünkü yeni-şema run ile eski bir run karşılaştırıldı; ortak alanlar (equity, fees, net PnL) eşleşti, Faz 2.2'nin yeni alanları (tepe equity, max drawdown, action/deal count, ortalama giriş, pozisyonda kalma) eski kayıtta yok olduğu için "—" ile doğru şekilde farklı işaretlendi, result hash'i haklı olarak eşleşmedi.
- Kanıt: 4 yeni API testi (`tests/api/test_historical_run_reproduce.py`), tam checker 879/879 PASS, frontend tsc/vitest yeşil, iki özellik de gerçek tarayıcı oturumunda uçtan uca çalıştırıldı (sentetik fixture değil).

## Faz 2.2 — ekonomik metrik seti v1 (önceki dilim, uygulandı)
`action_count`, `average_entry_price`, `time_in_position_us` yeni hesaplandı; `max_drawdown`/`peak_equity`/`current_drawdown`/`fees`/net PnL zaten `report()`'taydı, artık persist/expose ediliyor (kayıtlı + canlı yanıt). Fixed-slice modeli için ayrı `HistoricalFixedSliceSummaryResponse` (deal kavramı yok).

## Sıralı deal: restart + kayıt kimliği (önceki dilim, uygulandı)
`historical_simulation.py` deal kapanınca yeni `State`/BASE başlatır (realized/fees/funding/peak/max_dd taşınır); `deal_id = "<source_execution_id>:deal:<n>"` `save()` sırasında composed edilir. `engine.py` değişmedi. 24 bar VERIFIED fixture'ında deal hiç kapanmadığı için restart yolu gerçek veride hâlâ gözlenemedi (sentetik testte kanıtlı).

## Proje temizliği (Faz 2.1 dışı, Arda talebiyle — önceki dilim)
29 eski araştırma dosyası arşivlendi; `.cluster/` (544MB) silindi; hata raporu madde #4/#8 KAPALI. Detay: `docs/KARARLAR.md`.

## Kodda mevcut
- Yerel arayüz (FastAPI 127.0.0.1:8000 + React/Vite 5173): veri seti kaydı, sınırlı public indirme, kalite raporu, OHLC grafik, doğrulama, kapalı-bar simülasyon (sıralı deal + Faz 2.2 metrikleri destekli), SQLite kayıt/listesi, **reproduce doğrulama** ve **iki-run karşılaştırma** — hepsi bu oturumda canlı denendi.
- CLI tools/bot.py: demo, init/replay/status/audit, preview.
- Çekirdek: exact Decimal/Fraction ladder, net TP, drawdown; idempotent SQLite kayıtları.
- P2 salt-okunur Binance testnet sınırı: public, account, user-stream adaptörleri.

## Bilinen sınırlar
- Signed REST/WS emir, mutation ve mainnet: NO-GO. Gerçek reconnect worker ve REST catch-up yok.
- Simülasyon: OHLC intrabar sırası INDETERMINATE; gerçek likidite modeli yok.
- Reproduce yalnız `historical_ohlcv_v1` modelini destekler (fixed-slice hiç kaydedilmiyor, kapsam dışı kalması tutarlı).
- API tek worker'a bağlı. Python 3.13 zorunlu; uv sync --frozen.

## Kararlar (2026-09-20, Claude tarafından alındı — bkz. `docs/KARARLAR.md`)
Arda çalışma kuralını netleştirdi: ürün/teknik kararları Claude alır, gerekçesiyle işaretler, açık soru olarak geri atmaz (credential/gerçek emir/mainnet hariç).
1. Sıralı deal persistence/API tasarımı **ONAYLANDI ve UYGULANDI**.
2. Faz 2 dondurma listesi **ONAYLANDI**, P1 kapanışına kadar; yeniden değerlendirme: `p1-demo-complete` tag'i.
3. Testnet mutation gate koşulları **ERTELENDİ** — Faz 3.4'e kadar olgun değil.

## Ajanlar arası işbölümü (2026-09-20, bkz. AGENTS.md + docs/KARARLAR.md)
Kritik/matematik dosyalar (`domain/`, `historical_simulation.py`, `historical_run_contract.py`, `persistence/`) yalnız Claude değiştirir. Backend'e dokunmayan UI dilimleri dosya allowlist'li bir brief ile Codex'e TASK.md üzerinden devredilebilir; Codex STATE/TASK/KARARLAR'ı değiştirmez, Claude her devirden sonra diff+checker+tsc/vitest ile kontrol edip belgeleri günceller.

## Sıradaki adım
Faz 2.3 tamamlandı. **Faz 2.4 — Etkileşimli marker şu an Codex'te** (TASK.md brief'i: `HistoricalChart.tsx`/`DatasetCatalogPanel.tsx`/testler/CSS dışında hiçbir dosyaya dokunmaması, Python'a hiç girmemesi istendi). Codex bitirince: diff review, tam checker, canlı tarayıcı denemesi, STATE.md/TASK.md güncellemesi — bunları Claude yapacak.
