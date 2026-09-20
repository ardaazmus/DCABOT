# P1 kapanış bağımsız incelemesi — SONUC.md

Tarih: 2026-09-20. Kapsam: `git diff main...HEAD` (`main`=0024181, dal=`codex/latest-state-2026-09-20`, HEAD=`bb0aed9`). İnceleme sırasında `git status --porcelain` boştu (ağaç temiz). Bu rapor dışında hiçbir dosya oluşturulmadı/değiştirilmedi.

## 1. Özet karar: APPROVED_WITH_FINDINGS

Kritik/ekonomik katmanda (Katman 1) ve API sözleşmesinde (Katman 2) davranışsal kusur bulunamadı; 3 doğrulama komutunun üçü de PASS. Bulgular yalnız 1 LOW (UI kozmetik, ekonomik etkisi yok) + 4 INFO'dur. P1 kapanışını engelleyecek CRITICAL/HIGH/MEDIUM bulgu yoktur.

## 2. Çalıştırılan komutlar ve gerçek çıktıları

Komut 1 — `$env:PYTHONPATH='src'; uv run --frozen python tools/run_checks.py` (ayrıntılı test satırları elendi; FAIL/ERROR eşleşmesi + özet kuyruğu aşağıdadır):

```text
EXIT:0
=== FAIL-ERROR-LINES ===
(yok — eşleşme bulunamadı)
=== SUMMARY-TAIL ===
Ran 880 tests in 24.510s
OK
```

Komut 2 — `cd frontend; npx tsc -b; npx vitest run`:

```text
EXIT_TSC:0
RUN v3.2.4 D:/project/DCABOT/frontend
✓ src/datasetCatalog.test.ts (3 tests)
✓ src/ExplanationSection.test.tsx (2 tests)
✓ src/AppState.test.ts (1 test)
✓ src/DatasetCatalogPanel.test.tsx (3 tests)
✓ src/HistoricalChart.test.tsx (13 tests)
Test Files 5 passed (5)
Tests 22 passed (22)
EXIT_VITEST:0
```

Komut 3 — `uv run --frozen python tools/release_manifest.py check`:

```text
{"status": "PASS", "errors": [], "tracked_files": 714, "manifest_entries": 713, "manifest": "SHA256SUMS.txt"}
EXIT:0
```

Not: 714'e karşı 713 farkı beklenen durumdur; `tools/release_manifest.py:74` manifestin kendisini kapsam dışı bırakır (`set(tracked) - {MANIFEST_NAME}`). Kod okunarak doğrulandı.

## 3. Bulgular tablosu

| # | severity | dosya:satır | bulgu | kanıt | önerilen aksiyon (uygulanmadı) |
|---|----------|-------------|-------|-------|-------------------------------|
| F1 | LOW | frontend/src/DatasetCatalogPanel.tsx:151 | Satır `onClick`'i iç öğe tıklamalarını da seçime dönüştürür. Klavye yolu `:136`'daki `event.target !== event.currentTarget` korumasıyla kapatılmış, ancak click yolunda aynı koruma yok: fixed-slice satırındaki Kopyala butonuna veya `details/summary`'e tıklamak hem iç öğeyi çalıştırır hem satırı seçer. Ekonomik etkisi yok, kozmetik yan etki. | `:136`: `if (event.target !== event.currentTarget) return; ...` — `:151`: `onClick: interactive ? () => onSelectBarIndex?.(barIndex) : undefined,` (koşulsuz). | Click yoluna aynı hedef kontrolü veya iç kontrollere `stopPropagation`; iç-öğe tıklama izolasyonu için test ekle. |
| F2 | INFO | src/dcabot/server/api.py:1479-1480 + src/dcabot/application/historical_run_contract.py:314-315 | `deal_count` / `completed_deal_count` formülü iki katmanda tekrarlanıyor. Bugün iki formül birebir aynı (okunarak doğrulandı); tek risk gelecekte birinin değişip diğerinin unutulması. | api.py: `deal_count = max((action.deal_sequence for action in result.actions), default=0)`; contract: `deal_count = max((action["deal_sequence"] for action in actions), default=0)` (+ aynı completed formülü). | Tek yardımcıya taşı veya iki noktaya karşılıklı referans yorumu ekle. |
| F3 | INFO | pyproject.toml (diff: +1 satır) | Yeni `websockets>=17.1` bağımlılığının üst sınırı yok; oysa `fastapi`/`uvicorn` `<1` ile sabitlenmiş. `uv.lock --frozen` ile bugün tekrarlanabilir; tutarlılık notudur. Bağımlılık gerçekten kullanılıyor (`src/dcabot/data_adapters/binance_testnet_user_stream.py:11`: `from websockets.asyncio.client import connect`). | `git diff main...HEAD -- pyproject.toml` çıktısı + yukarıdaki import satırı. | Üst sınır ekle (örn. `<18`) veya pinsiz bırakmanın gerekçesini kaydet. |
| F4 | INFO | frontend/src/DatasetCatalogPanel.test.tsx (dosya geneli) | `:136`'daki hedef-koruması testsiz: 3 test Enter/Space/ilgisiz-tuş/handler-yok durumlarını kapsıyor, iç-öğe tuş izolasyonunu kapsamıyor. | Test dosyası 57 satırın tamamı okundu; iç öğe (`button`/`summary` odağında keyDown) senaryosu yok. | İç öğe odağındayken Enter/Space'in satırı seçmediğini doğrulayan 1 test ekle. |
| F5 | INFO | src/dcabot/persistence/futures_* + order_list_* + market/linear/conditional store'lar | Yeni store modülleri `server/` ve `tools/`'tan hiç import edilmiyor (sıfır eşleşme doğrulandı); yalnız `application/` modülleri + testler kullanıyor. Canlı API yüzeyi yok, risk test/kütüphane yüzeyiyle sınırlı. Kusur değil, kapsam notudur. | `server|tools` yollarında `futures_dca\|order_list_store\|market_execution_store\|linear_ledger_store\|conditional_execution` araması: 0 sonuç. | P1 kapanış notuna "henüz API'ye bağlı değil" olarak işle veya bağlama planını netleştir. |

Ayrıca doğrulanan (bulgu DEĞİL, kanıtlı) kritik noktalar:

- `engine.py` tek-base-order kilidi (`if s.orders or qty != c.base_qty: raise ... "One base order per deal"`, engine.py:120-124) değişmemiş; diff yalnız opsiyonel `intent_id` ekliyor (`identifier()` ile doğrulanıyor). `_start_new_deal` (historical_simulation.py:384+) `State`'in TÜM alanlarını muhasebeleştiriyor (`unsettled` türetilmiş property, taşınması gerekmez); `entry_notional=0`/`anchor=None`/`orders={}`/`blockers=[]` sıfırlamaları deal-kapsamlı, `realized/fees/funding/peak/max_dd` kümülatif taşınıyor. Restart koşulu (`not position.qty and orders and not unsettled and not halted and not blockers`) motorun INTENT önkoşullarıyla tutarlı.
- Eklenen diff satırlarında `float(`/`REAL`/`Decimal(`/`round(` yok (taramayla); `persistence/` genelinde `REAL`/`float` yok; yeni journal şemasında para kolonları TEXT (`fill_quantity/effective_price/gross_commitment/fee_amount ... TEXT NOT NULL`), zamanlar INTEGER.
- F-string SQL yalnız `PRAGMA application_id/user_version=<INT SABİT>` ve çift-tırnağı kaçırılmış (`replace('"','""')`) `PRAGMA index_info` (futures_dca_core_replay_store.py:272-274). Enjeksiyon yok.
- `gross - fee = net`: `report()` (engine.py:318) `realized - fees - funding`; fee per-fill `round_quantum(qty*price*rate, fee_quantum)` (simulation:338), model dizesi `CONFIGURED_RATE_ON_EACH_FILL` ile tutarlı.
- Hash kimliği: `_canonical_json` float reddeder + `sort_keys` + sabit ayraç + `allow_nan=False` (contract:385-390) → aynı girdi aynı hash. Identity; config_hash, input sha, model/profil/sürümler, risk-sha, feature-binding-sha içerir; sonuç ve zaman damgası dışarıda (tasarım gereği — kimlik yeniden-üretimi kilitler, sonuç çıktıdır).
- Stress profili: `config/historical_demo_btcusdt_1h_stress_slippage_v1.json` demo config ile anahtar-birebir aynı; TEK fark `slippage: '0' → '0.002'` (gerçek JSON diff komutuyla doğrulandı). Profil kaydı `HISTORICAL_OPT_IN_PROFILES` içinde, `simulation_model` varsayılan ohlcv.
- Reproduce (`POST /api/historical-runs/{run_id}/reproduce`, api.py:2222+): UUID kanonik doğrulama → model kilidi (yalnız `historical_ohlcv_v1`, yoksa 422) → busy kilidi (409) → artifact karşılaştırması (uyuşmazsa 409 `REPRODUCE_ARTIFACT_CHANGED`) → 3 hash karşılaştırması. Fonksiyonda `store.save` YOK (yazmıyor). `store.get` kayıt sha + satır eşleşmesi doğruluyor (RUN_CORRUPTelenco kapalı). `feature_binding` api.py'de hiç geçmiyor (0 eşleşme) → API üretimli tüm koşular bindingsiz; reproduce'un binding geçmemesi tutarlı, işlevsel boşluk yok.
- Fixed-slice/save/reproduce zinciri tutarlı: fixed-slice dalı capture kurulmadan erken dönüyor (api.py:~1979-1985) → asla kaydedilemez; `_result_payload`'un zorunlu kıldığı `action_count/time_in_position_us` anahtarlarının fixed-slice özetinde olmayışı bu yüzden zararsız (fail-closed). İki model artık ayrı Pydantic özet modelleri kullanıyor (`HistoricalSimulationSummaryResponse` + `HistoricalFixedSliceSummaryResponse`, ikisi de `extra="forbid", strict=True`); alan listeleri çağrı noktalarıyla birebir eşleşiyor.
- `dataset_id` kayıtlı katalog dict'inde çözülüyor (api.py:1180-1182), kullanıcı girdisinden dosya yolu kurulmuyor; `profile_id` `resolve()+parent` kontrolünden geçiyor (historical_profiles.py:111-114); `run_id` UUID-kanonik. Body-limit middleware'i genel mekanizmaya taşınmış (`SMALL_JSON_BODY_LIMITS`, api.py:162-164) — `/validate` limiti korunuyor. CORS env değeri `*`/boş ise güvenli varsayılana düşüyor. Paper config mtime-cache `deepcopy` ile dönüyor. `_quality_response` değişikliği güvenli (uçta `response_model` yok).
- Secret/mainnet taraması: eklenen satırlarda gömülü secret yok (`api_key` eşleşmeleri parametre/alan adları); `mainnet`/`place_order`/`create_order`/`newOrder` yok; adapter'larda yalnız `method="GET"`; credential aracı `getpass` + Windows vault + redacted çıktı kullanıyor.
- Frontend: marker/satır klavye deseni tutarlı (`Enter`/`Space` + `preventDefault`, diğer tuşlar yok sayılır); AbortController ailesi (detail/compare aynı ref'i paylaşıyor, her yeni istek öncekini iptal ediyor) ve `signal.aborted` kontrolleri düzgün; compare görünümü snapshot string'lerini gösteriyor, `Number` ile finansal hesap yok (taramayla); `role="button"` satırlar `interactive` kapalıyken niteliksiz.

## 4. Katman bazında kapsam notu (dürüst derinlik beyanı)

- **Katman 1 — kritik/ekonomik: DEĞİŞEN DOSYALAR SATIR SATIR, YENİ DOSYALAR HEDEFLİ.** `engine.py` (9/2), `historical_simulation.py` (105/5), `historical_run_contract.py` (51/2), `historical_profiles.py` (10), `historical_runs.py` (21/2), `reconciliation_journal.py` (212/3), `spot_binding_store.py` (120/4) diff'leri satır satır okundu ve komşu kod/çağrı noktalarıyla (`State` alanları, `report()`, `decision()`, `_decode_*`, `store.get/save`) doğrulandı. Katman-1'e bitişik YENİ `historical_features.py` (250 satır) tamamı okundu. YENİ persistence dosyaları (~4,5k satır: futures_dca_*/order_list_*/market/linear/conditional) satır satır OKUNMADI; hedefli tarama yapıldı (float/REAL/SQL-parametreleme/UNIQUE-PK/TEXT-para + `futures_dca_core_binding.py` tam okuma + server/tools erişilebilirlik kontrolü).
- **Katman 2 — API: DİFF TAMAMI + İLGİLİ FONKSİYONLAR (orta-derin).** `api.py` diff'i (184/42) tamamı okundu; save/reproduce/preflight/catalog/quality/body-limit/CORS yolları dosyada doğrulandı. Dosyanın tamamı satır satır okunmadı.
- **Katman 3 — frontend + geri kalan: BİLEŞEN BAZINDA OKUMA + YÜZEYSEL TARAMA.** `DatasetCatalogPanel.tsx`, `HistoricalChart.tsx`, `SavedRunsPanel.tsx`, `App.tsx` (async/compare/state hunks), `styles.css` (ilgili kurallar), `package.json`/`vitest.config`/`testSetup.ts` diff'leri okundu/tarandı. `App.tsx`'in tamamı satır satır okunmadı. Geri kalan ~372 dosya (evidence 125, tests 99, src 76, docs 72 dahil) YÜZEYSEL tarandı: dizin sayımı + hedefli taramalar (secret/mainnet/float/POST) + test-dosya adları; içerik doğruluğu incelenmedi.
- **Bağımsızlık notu:** `6fed8f7` içindeki klavye-erişimi UI diliminin ilk hali bu oturumda yazıldı; commit sırasında Claude değiştirdi (hedef-koruma satırı eklendi). O küçük UI dilimi için tam bağımsızlık yoktur; Katman 1-2 kodları bu oturumda yazılmadı.

## 5. Açık sorular / NOT_VERIFIED listesi

- NV1 — Gerçek tarayıcıda klavye/focus-halkası/`scrollIntoView` davranışı: NOT_VERIFIED (bu oturumda tarayıcı çalıştırılmadı; yalnız jsdom testleri PASS).
- NV2 — Canlı testnet/mainnet davranışı: NOT_VERIFIED (credential yok, offline; adapter kodları yalnız diff-seviyesinde tarandı, çalıştırılmadı).
- NV3 — Yeni persistence (~4,5k satır) ve futures/grid/order_list application modüllerinin tam satır-satır doğruluğu: NOT_VERIFIED (hedefli tarama yapıldı, eksiksiz okuma yapılmadı).
- NV4 — `evidence/` (125 dosya) ve `docs/` (72 dosya) içeriklerinin doğruluğu: NOT_VERIFIED (içerik incelemesi yapılmadı).
- NV5 — `tools/archive_cleanup.py` (334 satır, yeni), `.claude/launch.json`, `SHA256SUMS.txt` satır içeriği, `frontend/package-lock.json`: NOT_VERIFIED (okunmadı; release_manifest PASS yalnızca hash tutarlılığını kanıtlar).
- NV6 — F1'in kullanıcı-etkisi eşiği (LOW olarak sınıflandırıldı): ürün kararı gerektirirse Arda'ya sorulmalıdır; bu rapor düzeltme önermez, yalnız kaydeder.
