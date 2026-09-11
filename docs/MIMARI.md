# Mimari — ortak çekirdek, demo öncelikli ürün

## Katmanlar

| Katman | Sorumluluk | Bugünkü durum |
|---|---|---|
| Çekirdek: src/dcabot/domain | Ekonomik tip/hesap, strateji ve risk kuralları | CORE01 dar alt kümesi var |
| Application: src/dcabot/application | Preview, run, command, query; transaction/iş akışı | CLI demo/replay, verified input, explicit historical profile registry, salt-okunur historical run-plan/validation, bounded `historical_ohlcv_v1` simulation, P1.06.a canonical run capture ve explicit save için capture üretimi var; UI hesap yapmıyor |
| Portlar: src/dcabot/ports | Journal, market data, simulator/execution, clock vb. sözleşmeler | Journal var, diğerleri plan |
| Persistence: src/dcabot/persistence | Ledger, config, job, run ve dataset metadata | CORE01 SQLite journal korunuyor; P1.06.b ayrı versioned historical run snapshot SQLite store’u, P1.06.c explicit local save API’si ve P1.06.d bounded list/detail read API’si var; P1.06.e UI salt-okunur tüketim katmanı olarak eklendi; reproduction sonraki alt faz |
| HTTP: src/dcabot/server | UI için tipli API, download job progress; business rule içermez | Preview, katalog, bounded historical profile listesi, verified preflight, profile’lı read-only run-plan/validation ve bounded simulation API’si var |
| UI: frontend/ | React + TypeScript; responsive bileşenler/ekranlar | P1.01–P1.05.b katalog/download/preflight, offline simulation action/status, minimal result summary ve read-only action history UI var; P1.05.c.1 chart data contract, P1.05.c.2 static inline SVG OHLC overview, P1.05.c.3 fail-closed static action marker, P1.05.d minimal economic outcome ve P1.06.e Saved Runs list/detail UI var; marker etkileşimi/kapsamlı ekonomik inceleme/reproduction sonraki alt faz |
| Veri: src/dcabot/data_adapters | CSV/ZIP, public archive/REST/WS normalizasyonu | CSV/ZIP kalite, public cache/job ve verified canonical bar parser var |
| Simülasyon: src/dcabot/replay | Zaman, fill, latency, orderbook/volume varsayımları | Basit replay application içinde; ayrıntılı adapter plan |
| Borsa: src/dcabot/venue | Private Binance ve sonraki venue adapter'ları | P2/P4 |
| Yedek: YEDEK_ESKI_PROJE | Salt okunur eski kaynak | ZIP'te boş; kullanıcı kendi yedeğini korur |

Plan klasörleri ilk ilgili dilimde açılır; yüzlerce boş interface önceden üretilmez. Mevcut src yolları sırf görünüş için taşınmaz.

UI → HTTP/application → domain/port sözleşmeleri. Adapter'lar portları uygular; domain UI, HTTP, DB ve venue import etmez. Composition root bağımlılıkları bağlar. Çekirdek başlangıçta aynı Python process'inde kullanılan modüldür; zorunlu microservice değildir.

## Çalışma modu iki ayrı eksendir

| Veri modu | Emir modu | Ürün aşaması |
|---|---|---|
| HISTORY_LOCAL | SIMULATED | P1 |
| HISTORY_PUBLIC_DOWNLOAD | SIMULATED | P1 |
| LIVE_PUBLIC | SIMULATED | P1 opsiyonel canlı paper |
| TESTNET_MARKET | BINANCE_TESTNET | P2 |
| LIVE_MARKET | BINANCE_LIVE | P3 |
| VENUE_PUBLIC/LIVE | ilgili adapter | P4 |

Dataset kaynağının Binance olması Binance'e gerçek emir gönderileceği anlamına gelmez. Veri ve execution adapter seçimleri ayrı ve izinli kombinasyon tablosundan yapılır. UI'daki mod adı yalnız renk değildir; backend kalıcı run/account namespace'ini ve yetkiyi denetler.

## Önerilen uygulama tabanı

Mevcut Python 3.13 çekirdeği + FastAPI HTTP katmanı; React/TypeScript arayüzü. İlk geliştirilebilir dilimde frontend build/lock ve backend bağımlılıkları gerçek sürümleriyle kilitlenir; bu belge kurulu olduklarını iddia etmez. Başlangıç tek makine, local-only bind; P3'te uzak servis kurulumu ayrıca tasarlanır.

UI para alanlarını string taşır. JavaScript Number sadece grafik koordinatı/arayüz amaçlıdır; miktar, bütçe, TP ve PnL doğrusu backend'den gelir. Grafik sürüklemesi yeni fiyat niyeti üretir; backend grid/risk doğrulayıp döndürür. Hesaplanan preview config revizyonuna bağlıdır; eski HTTP yanıtı yeni formu ezemez.

API önce minimal: health/capabilities, preview. Sonra datasets/imports, runs/jobs, bots/deals/orders, ledger/risk, settings/connections. Verified dataset preflight’i source/time/bar kapsamını; run-plan ise bunu aktif offline config ve hash’iyle salt-okunur bağlamı döndürür, validation endpoint’i client revision assertion’larını current VERIFIED/config state’e karşı fail-closed kontrol eder. Validation ekonomik hesap veya koşu başlatmaz. Uzun backtest request içinde bloklamaz; job_id/progress/cancel/resume uygulanır. Eksik, başarısız ve iptal sonuçları birbirinden ayrıdır. Tarihsel job'un SIMULATED yerel atomikliği canlı network transaction'a aynen taşınmaz.

## Ürüne genişlerken korunacaklar

- CORE01'in exact ratio, Decimal sınır, ekonomik dedup ve cash posting ilkeleri.
- Tek pending kısıtı bugünkü basitleştirmedir; P1 çoklu bot/emir için account bütçe rezervi ve sahiplik modeli gerektirir.
- Spot, linear long/short, cross/hedge veya çift bacak ayrı ürün modelleri. Desteklenmeyen hesap yolu yanlış enum ile açılmaz.
- 10000 olay sınırı ve her olayda full replay büyük backtest'e yetmez; P1.16'da ölçüm ve sürümlü projection/checkpoint tasarlanır.
- Çekirdek API sürümü, dataset/config/model/hash ve schema migration izlenir; eski DB üzerinde örtük migration yok.
