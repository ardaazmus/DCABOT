# DCABOT — Demo öncelikli güncellenmiş proje paketi

Plan: DEMO_FIRST_1. İçerilen Python çekirdek: 0.1.0, önceki teslimle aynı kod. **Bu teslim işlem sırasını ve geniş ürün/arayüz kapsamını düzeltir; bitmiş arayüz teslimi değildir.**

Yeni sıra: **tam arayüz + geçmiş veri demo → Binance testnet → gerçek Binance kurulum → diğer borsalar.**

Önce [ürün kapsamını](docs/URUN_KAPSAMI.md), ardından [değişiklik tablosunu](docs/GECIS.md) oku. [Özellik matrisi](docs/OZELLIK_MATRISI.md) 40 gereksinimi ve bugünkü gerçek durumunu taşır. [UI/UX](docs/UI_UX.md), [veri/simülasyon](docs/VERI_VE_SIMULASYON.md), [mimari](docs/MIMARI.md) ve [yol haritası](docs/YOL_HARITASI.md) ilgili iş sırasında okunur. Günlük başlangıç yalnız AGENTS/STATE/TASK.

Çekirdek ayrı yazılım katmanıdır; aşağıdaki CLI demo mevcut çalışan kısmıdır. P1.01 ile UI/API önizleme dilimi, P1.02 ile CSV/ZIP kalite akışı, P1.03 ile explicit public dataset/cache ve download job akışı, P1.04.a ile verified canonical historical input sınırı, P1.04.b ile salt-okunur preflight özeti, P1.04.c ile aktif config’e bağlı salt-okunur koşu planı, P1.04.d ile bounded tarihsel koşu validation sınırı, P1.04.e ile sınırlı offline OHLCV simülasyon başlatma akışı, P1.05.a ile minimal sonuç özeti, P1.05.b ile read-only action geçmişi, P1.05.c.1 ile bounded chart data sözleşmesi, P1.05.c.2 ile minimal static OHLC overview, P1.05.c.3 ile doğrulanmış action marker katmanı, P1.05.d ile minimal ekonomik sonuç özeti, P1.06.e ile Saved Runs salt-okunur list/detail UI’sı, P1.16.e ile ayrı stress lineage/result identity ve P1.16.h ile persisted trial/OOS/stress metadata binding sınırı eklendi. P1.16.i.a ile stress ekonomik modelinin mevcut yerel authority envanteri çıkarıldı; P1.16.i.b araştırma raporu denetlendi ve ekonomik implementation `DEFERRED/NO-GO` olarak kapatıldı. P1.16.i.c deterministic identity, P1.16.i.d persistence/replay sınırları bağımsız kontrol edildi; P1.16.i.e ekonomik stress runner için `NO-GO` olarak kapatıldı. P1.17.a historical public download/cache authority’si, P1.17.b public read-only feed contract araştırması, P1.17.c bounded local observation replay sınırı, P1.17.d Binance Spot transport/reconnect araştırma kapısı, P1.17.e network-free payload normalization, P1.17.f network-free replay binding, P1.17.g public profile acceptance matrix, P1.17.h network-free REST public payload normalization ve P1.17.i capability boundary tamamlandı. P1.17.j live transport activation gate `NO-GO/DEFERRED` olarak kapatıldı. P1.18.a offline rule-based read-only event explanation projection, P1.18.b mevcut historical response binding, P1.18.c read-only explanation UI, P1.18.d visual/accessibility QA, P1.19.a result-shell state acceptance, P1.19.b inventory, P1.19.c dark-token/focus implementation ve P1.19.d Chrome CDP accessibility QA `COMPLETE_WITH_LIMITATION` olarak tamamlandı. P1.19.e light theme/uzman görünüm raporu gerçek checkout ile denetlendi; P1.19.f exact token/detailed-view gate ölçüldü, 11 PASS/1 border FAIL sonucu ile yeni light theme ve expert mode `DEFERRED/NO-GO` kaldı. Aktif ürün kararı: exact light palette/default/persistence gereksinimi.

## P1.01 local arayüzü çalıştır

Python bağımlılıklarını kilitli kurulumla hazırla:

```powershell
$env:PYTHONPATH = "$PWD/src"
uv sync --frozen
uv run uvicorn dcabot.server.api:app --host 127.0.0.1 --port 8000
```

Ayrı bir PowerShell'de frontend'i başlat:

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

Tarayıcıda `http://127.0.0.1:5173` adresini aç. UI yalnız local API'ye bağlanır; credential, emir ve testnet yolu yoktur. API sözleşmesi `GET /api/health`, `GET /api/capabilities`, `POST /api/preview`, `POST /api/data-quality`, `GET /api/datasets`, `GET /api/datasets/{dataset_id}/preflight`, `GET /api/historical-profiles`, `GET /api/datasets/{dataset_id}/chart-data`, `GET /api/datasets/{dataset_id}/run-plan?profile_id=...`, `POST /api/historical-runs/validate`, `POST /api/historical-runs/simulate`, `POST /api/historical-runs`, `GET /api/historical-runs`, `GET /api/historical-runs/{run_id}`, `PUT /api/dataset-selection`, `POST/GET /api/dataset-downloads` ve `POST /api/dataset-downloads/{job_id}/cancel` endpoint'lerini içerir. Historical profile seçimi UI’da explicit yapılır; profile listesi label ve beklenen dataset eşleşmesini backend’den alır. Validation endpoint’i yalnız current VERIFIED artifact/config revision assertion’larını kontrol eder; run/job/simulation/write başlatmaz. Historical simulation endpoint’i yalnız doğrulanmış artifact + aktif offline config ile en fazla 1.000 kapalı barı, `historical_ohlcv_v1` ve `INDETERMINATE` belirsizlik sonucu ile çalıştırır; yanıt server-side ephemeral `execution_id` ile explicit save akışına bağlanır ve `persisted=false` kalır. Save endpoint’i yalnız aynı process’te üretilmiş capture’ı dedicated local SQLite store’a immutable/idempotent olarak yazar; istemci sonuç/config gönderemez. List/detail endpoint’leri yalnız bounded metadata ve doğrulanmış immutable snapshot döndürür; eksik store okuma sırasında dosya yaratılmaz, corrupt/unsafe detail fail-closed olur ve detail response byte bütçesi vardır. Chart-data endpoint’i aynı bounded VERIFIED canonical bar sınırıyla salt okunur OHLC sözleşmesi döndürür; persistence/network/credential/emir yoktur. Dataset işlemleri yalnız explicit registry, bounded download ve doğrulanmış atomik yerel cache ile çalışır; response’lar URL/path taşımaz.

## Hemen çalıştır — Windows PowerShell

ZIP'teki DCABOT kökünü aç. Python 3.13 kuruluysa:

```powershell
py -3.13 tools/run_checks.py
py -3.13 tools/bot.py demo
py -3.13 tools/bot.py preview --anchor 100
```

uv kullanıyorsan `uv sync --frozen`, ardından aynı komutlarda `py -3.13` yerine `uv run --frozen python` kullan. Harici Python bağımlılığı yok; ilk Python/uv kurulumu internet gerektirebilir. Çalışma akışı ağ kullanmaz.

Demo geçici SQLite dosyasında `100 → 90 → 80 → 100` sentetik fiyatlarını işler: 1@100, 1@90, 1@80 alım, 3@100 çıkış. Brüt kâr=30, toplam ücret=0.57, net=29.43, son equity=1029.43. **Bunlar gerçek BTC fiyatları veya strateji performansı değildir; elle hesaplanabilir yazılım örneğidir.**

## Kalıcı çalıştır

```powershell
py -3.13 tools/bot.py init --db data/paper.db
py -3.13 tools/bot.py replay --db data/paper.db --input tests/fixtures/demo_ticks.json
py -3.13 tools/bot.py status --db data/paper.db
py -3.13 tools/bot.py audit --db data/paper.db
```

`init` mevcut dosyayı üzerine yazmaz. Aynı replay aynı ID'lerle tekrar verilirse yeniden ekonomik kayıt oluşmaz. İşlem yarıda kesilirse aynı replay ile devam edilebilir; tamamlanmış tick'ler atlanır. Farklı config için yeni DB adı kullan; var olan DB config'i sabittir. CLI DB yolları yeni kökün data/ alanıyla sınırlıdır.

## Uygulanan parçalar

| Parça | Kod |
|---|---|
| Sonlu Decimal giriş, tam kesir hesabı, tick/step ve çıktı | src/dcabot/domain/numbers.py |
| Ladder, kısmi pozisyon, net TP, DD, öğretici likidasyon kökü | src/dcabot/domain/math.py |
| Açık ürün/birim/config doğrulaması | src/dcabot/domain/config.py |
| Intent/fill/final/UNKNOWN, risk ve sonraki tek DCA kararı | src/dcabot/domain/engine.py |
| Transaction, execution dedup, kalıcı olay ve dengeli nakit kayıtları | src/dcabot/persistence/store.py |
| Preview, notional ve ortak çekirdekte replay | src/dcabot/application/service.py |
| Public kaynak planı, bounded download, ZIP doğrulama ve atomik cache | src/dcabot/data_adapters/public_sources.py, src/dcabot/data_adapters/public_download.py |
| Local download job progress/retry/cancel sözleşmesi | src/dcabot/data_adapters/download_jobs.py, src/dcabot/server/api.py |
| Verified artifact → exact canonical historical input, preflight, bounded chart data, run-plan, bounded validation ve offline OHLCV simulation | src/dcabot/data_adapters/historical.py, src/dcabot/application/historical.py, src/dcabot/application/chart_data.py, src/dcabot/application/historical_simulation.py, src/dcabot/server/api.py |
| Walk-forward/OOS çalışma sınırları, stress ve persisted run binding | src/dcabot/application/chronological_split.py, src/dcabot/application/oos_lineage.py, src/dcabot/application/horizon_overlap.py, src/dcabot/application/trial_registry.py, src/dcabot/application/stress_lineage.py, src/dcabot/application/evaluation_run_binding.py |
| Public read-only observation cursor’ı ve fail-closed stale/gap/reconnect sınırı | src/dcabot/data_adapters/public_feed.py |
| Terminal komutları | tools/bot.py |

Ayrıntılı olay örnekleri ve sınırlar: [docs/CEKIRDEK_KULLANIM.md](docs/CEKIRDEK_KULLANIM.md). Güncel kanıt: [evidence/P1.19.f/SONUC.md](evidence/P1.19.f/SONUC.md). Light theme ve yeni expert mode ürün kararı/ exact palette olmadan açılmadı. Sonraki tek iş: [TASK.md](TASK.md).

## Eski yedeğini koru

Bu ZIP YEDEK_ESKI_PROJE klasörünü boş içerir; bilgisayarındaki eski projeyi içermez. Daha önce yedek yerleştirdiysen o klasörü silme veya değiştirerek birleştirme. Yeni ZIP'i ayrı yere açıp eski tam yedek klasörünü bu yeni kökün altına aynı adla yerleştir. Yeni kaynaklar yedek olmadan da çalışır. `.venv`, `.git`, DB ve eski IDE kuralları aktif köke geri alınmaz.

Aktarım politikası [docs/YEDEKTEN_AKTARIM.md](docs/YEDEKTEN_AKTARIM.md) içinde. Bu çekirdek eski Python modülleri kopyalanmadan, düzeltilmiş sözleşmeden yazıldı.

## Kapsam

Çekirdek CLI sentetik tick replay’i, bir tick'te en çok bir emir ve anında tam dolum varsayar. Manuel olay yolu kısmi fill/çıkış ve UNKNOWN senaryolarını destekler. Gerçek liquidity, OHLC intrabar sırası (belirsiz yol `INDETERMINATE`), live cancel/recovery, borsa margin/bracket, credential, outbox sender ve daemon uygulanmamıştır. P1.04.e sınırlı kapalı-bar tarihsel simülasyon başlatma, P1.05.a minimal read-only sonuç özeti, P1.05.b read-only action geçmişi, P1.05.c.1 bounded read-only chart data contract, P1.05.c.2 minimal static OHLC overview, P1.05.c.3 fail-closed action marker, P1.05.d minimal ekonomik sonuç özeti, P1.06.e Saved Runs list/detail UI’sı, P1.16.e ayrı stress lineage/result identity ve P1.16.h bounded persisted trial/OOS/stress metadata binding sınırı eklenmiştir; gerçek stress ekonomik modeli, etkileşimli marker, kapsamlı ekonomik metrikler, reproduction/compare ve canlı çalışma hâlâ sonraki alt fazlardadır. Büyük fazın bağımsız ikinci Codex incelemesi henüz yapılmadı. Güncel P1 tamamlanma ölçütleri URUN_KAPSAMI ve özellik matrisindedir.
