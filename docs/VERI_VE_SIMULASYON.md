# Veri ve demo hesap sözleşmesi

Bu dosya P1 hedefidir; mevcut CLI dört sentetik tick örneğini çalıştırır. CSV/ZIP kalite akışı, explicit public archive downloader/cache altyapısı, verified artifact’tan canonical bar input use case’i, salt-okunur tarihsel koşu preflight’i, aktif config’e bağlı run-plan özeti, current revision’ları doğrulayan salt-okunur validation endpoint’i, en fazla 1.000 kapalı bar için `historical_ohlcv_v1` offline simülasyon endpoint’i, P1.05.a minimal read-only sonuç özeti, P1.05.b read-only action geçmişi, P1.05.c.1 bounded read-only chart data contract endpoint’i, P1.05.c.2 static inline SVG OHLC overview, P1.05.c.3 chart composition içinde fail-closed static action marker, P1.05.d minimal ekonomik sonuç özeti, P1.06.a canonical run capture hazırlığı, P1.06.b dedicated run store, P1.06.c explicit save API’si, P1.06.d bounded list/detail read API’si, P1.06.e ayrı Saved Runs list/detail UI’sı, P1.06.f explicit historical profile backend binding’i ve P1.06.f.2 preflight içi explicit profile selector UI’sı vardır. `paper` ve `historical_demo_btcusdt_1h_v1` ayrı immutable config profile’larıdır; profile provenance `project_fixture` ve `historical_filter_claim=false` açıkça taşınır. Marker etkileşimi, volume, reproduction, compare ve kapsamlı ekonomik görünüm sonraki alt fazlardadır.

## Historical profile sözleşmesi

`paper` config’i değiştirilmez. Verified BTCUSDT/1h public artifact için yalnız açıkça seçilen `historical_demo_btcusdt_1h_v1` profile kullanılabilir. Bu profile rapordaki demo uyumluluk miktarlarını taşır; gerçek venue veya tarihsel Binance filter uyumluluğu iddiası taşımaz.

API historical run request’i `profile_id` alanını zorunlu taşır. Backend yalnız kayıtlı profile kimliğini, profile’ın beklenen dataset eşleşmesini ve profile config hash’ini kabul eder. Profile response/snapshot kimliği `profile_id`, `profile_version`, `label`, `expected_dataset_id`, `venue_filter_provenance`, `historical_filter_claim` ve `anchor_source` alanlarını içerir. Profile runtime’da mutate edilmez; quantity veya anchor sessizce normalize edilmez.

## P1.06.a run capture sınırı

`build_historical_run_capture` terminal historical result’ın güvenli snapshot parçalarını canonical JSON/hash olarak hazırlar. Canonical input en fazla 1.000 bar içerir; full Config dataclass allowlist’i exact değerleriyle, `USDT` monetary unit ile, instrument/risk snapshot ve `historical_ohlcv_v1` runtime identity ile birlikte hazırlanır. Action `raw_reference` yalnız plain decimal olarak kabul edilir. `HistoricalRunStore` bu capture’ı mevcut CORE journal’dan ayrı versioned SQLite DB’de tek transaction ile immutable saklar; record checksum ve `CORRUPT` list health uygulanır. `POST /api/historical-runs/simulate` capture’ı yalnız bounded in-memory registry’ye koyup `execution_id` döndürür; `POST /api/historical-runs` yalnız bu kimlikle store’a yazar, aynı execution retry’ında aynı `run_id` döner. Save sonucunun response’unda `persisted` değiştirilmez; kayıt içindeki result snapshot da `persisted=false` olarak kalır. Bu alt fazda HTTP list/detail, reproduction, compare ve frontend persistence yoktur.

## P1.05.d ekonomik alan sözleşmesi açıklaması

Mevcut P1 v1 sözleşmesinde `Config.parse` yalnız `quote_asset=USDT` olan explicit offline config’i kabul eder. `run-plan` aynı config snapshot’ının `quote_asset` değerini taşır; UI ekonomik stringleri bu değeri etiket olarak kullanır ve sayısal hesap yapmaz. Domain kodunda `position.cost`, `realized`, `fees`, `funding`, `entry_notional`, `initial_equity` ve `equity` quote-asset bağlamındadır; `qty` base-asset miktarıdır. Historical fill fee’si `config.quote_asset` olarak kaydedilir.

`realized_net_after_all_costs`, mevcut v1 domain kodundaki `realized - fees - funding` ifadesinin string sonucudur. Bu ifade gerçek dünyadaki tüm maliyetlerin modellenmiş olduğu anlamına gelmez; funding tarihsel modelde `NOT_MODELED` olduğu için P1.05.d etiketi `Model net gerçekleşen sonuç` olarak kullanılır. `unrealized` mark yokken domain tarafından sıfır metni üretebilse de `mark_status=NOT_AVAILABLE` nedeniyle UI’da sayısal gösterilmez. `equity` valuation/başlangıç sermayesi sözleşmesi bu faz için kullanıcı sonucu olarak yeterince tanımlı olmadığından UI’da gösterilmez.

Tarihsel v1 TP değeri mevcut modelde bir fiyat-tetikleyici/eşik referansıdır; gerçekleşecek fill fiyatı veya net kâr garantisi değildir. Action kaydındaki `raw_reference` tetikleyici referansını, `fill_price` ise slippage ve tick hizalaması sonrası modellenen gerçekleşme fiyatını taşır. Slippage fill fiyatına dahil edildiğinden sonuç hesabında ikinci kez düşülmez. Bu fazda TP semantiği execution-target olarak yeniden yorumlanmaz; böyle bir değişiklik ayrı bir sözleşme ve doğrulama kapısı gerektirir.

## Veri girişleri

A: Kullanıcı CSV/ZIP dosyası seçer; alan eşleme, ürün/sembol, zaman birimi ve aralık onayıyla içe alınır. Bu yol internet yokken de çalışır.

B: Public arşiv indiricisi tarihsel dataset alır, checksum doğrular ve cache'e kaydeder. Binance public arşivi günlük/aylık dosya ve checksum yayınlar; dosyalar sonradan güncellenebilir. Eski koşu kayıtlı hash'ine bağlı kalır. [Binance Public Data](https://github.com/binance/binance-public-data)

C: Public REST/WS ile eksik günleri tamamlama veya canlı fiyatla sanal işlem. Hesap/secret gerekmeden sunulan endpoint'ler seçilir; erişim/rate limit/coğrafi kısıt olursa açık hata ve A yolu kalır. Private order API'sine fallback yapılmaz.

## Normalize schema

Dataset kimliği: source, product, symbol, base/quote/settlement, kind, source_time_unit, timezone, start/end, interval, source/schema_version, original_sha256, normalized_sha256, ingestion_version. Sayısal finansal kolonlar decimal string veya ölçekli tam sayı; timezone UTC. Kaynak metadata olmadan zaman birimi sadece büyüklükten tahmin edilmez.

Bar: open_time_us, close_time_us, open/high/low/close, base_volume, quote_volume (varsa), trade_count (varsa), is_closed. Trade: exchange_time_us, source_trade_id, price, base_qty, role/side semantiği kaynak tanımıyla. Decision_time ve fill_time ayrıca tutulur.

Binance public SPOT verisinde 1 Ocak 2025 sonrası timestamp mikro-saniye olarak belgelenir; bu kural bütün futures veya tüm endpoint'lere uygulanmaz. Kaynak türü ve schema ile dönüşüm test edilir. [Resmî veri formatı](https://github.com/binance/binance-public-data#data-information)

Futures için mark/index, funding takvimi/oranı, ürünün tarihsel filtre ve bracket/risk parametreleri ayrı dataset/snapshot'tır. Trade OHLC fiyatı mark-price yerine sessizce kullanılmaz. Tarihsel fee tier/balance verilmediyse model varsayımı ve etkisi açık gösterilir. Fonksiyonel demo tahminle çalışabilir, sonuç evidence_scope=ASSUMPTION_BASED/INCOMPLETE olur; tam veri kanıtı etiketi alamaz.

## Kalite kabulü

Fiyatlar pozitif, hacim negatif değil; low≤open/close≤high; open_time<close_time; kapalı bar ve interval doğru. Yinelenen key aynı veri ise dedup sayacı; farklı veri ise conflict. Gap, sırasız veri, eksik funding/mark, ürün delist/list zamanları raporlanır. Sessiz interpolate, gelecek barla doldurma veya varsayılan sıfır funding yok. UI ham/normalize örnek satırını ve kalite etkisini gösterir.

ZIP girişinde path traversal, genişleme limiti, dosya türü ve boyut kontrolü; indirici belirlenmiş public kaynaklara gider. Hiçbir veri import yolu kod çalıştırmaz. Dataset kalıcı metadata'ya ancak başarılı doğrulama sonrası bağlanır. İptal edilen download yarım dosyayı kullanılabilir dataset yapmaz.

Yerel API taşıma sınırları ekonomik/veri sınırlarından ayrıdır: küçük JSON route’ları (`preview`, dataset selection/download ve historical simulation) native Starlette route katmanında 4 KiB ile sınırlıdır; sınır aşımı body parser’a ulaşmadan `413` ve güvenli `application/problem+json` (`REQUEST_TOO_LARGE`) döner. Historical validation’ın mevcut 4 KiB Problem Details kontrolü korunur. `data-quality` upload akışı ise ayrı 20 MiB ham giriş bütçesini, ZIP açılım/üye/satır sınırlarını korur. Quality report issue listesi üretim anında en fazla 200 örnek taşır; `issue_count`, `error_count`, `warning_count` ve `issues_truncated` toplam kapsamı açıklar. Serileştirilmiş kalite response’u 256 KiB’yi aşarsa `QUALITY_RESPONSE_TOO_LARGE` ile bounded Problem Details fallback’i döner.

## Geçmiş veriyle emir modeli

P1.04.e `historical_ohlcv_v1` modeli yalnız kapalı barları işler. İlk bar base için bar açılışını kullanır; sonraki barlarda yalnız önceden aktif safety/TP adayları değerlendirilir. Yeni safety ile oluşan TP aynı barda değerlendirilmez. TP ve safety aynı bar içinde erişilebiliyorsa OHLC içi sıra bilinmez ve koşu ilgili barı commit etmeden `INDETERMINATE / AMBIGUOUS_OHLC_PATH` döner. En fazla bir action/bar vardır. Bu ilk alt dilimde gerçek liquidity, volume participation, funding ve exchange mark modellenmez; forced close yapılmaz.

Limit değdi diye her miktar dolmuş sayılmaz. Volume participation, sıra varsayımı, spread, latency ve slippage ayrı parametrelerdir; veri yoksa model varsayımıdır. Kısmi fill, cancel latency, geç execution, fee düzeltmesi simüle edilir. Slippage fiyatın içindeyse PnL'den ikinci kez düşülmez. Seed ve model sürümü kaydedilir; rastgelelik tekrar üretilebilir.

Futures IM/MM, bracket deduction, closing fee, funding, cross/isolated, mark likidasyon hesabının ürün modeli ayrıca kanıtlanır. CORE01'in öğretici liquidation_long fonksiyonu gerçek Binance risk motoru değildir. Spot'ta notional varlık alışıdır; türevde aynı tutar wallet gideri değildir. Base-varlık fee envanteri azaltır. Hedge/multi-leg sahiplik ve muhasebe kapsamı ayrı tutulur.

## Hesap/rapor kabul tablosu

| Hesap | Gerekli açıklık ve kontrol |
|---|---|
| Ortalama/kısmi satış | Gerçek fill, weighted-cost/FIFO seçimi; kalan maliyet ve tam kapanış residual |
| Brüt/net PnL | Realized/unrealized, fee/funding/borrow ve üçüncü varlık dönüşüm kaynağı |
| Sermaye | Notional, başlangıç teminatı, pending rezerv, kullanılabilir equity ayrı |
| Hedef/stop | Gross price %, NET_QUOTE ve referans sermaye; trailing/partial payları |
| Drawdown | Equity peak, mark anında ölçüm; dış akış varsa TWR ayrımı |
| Performans | Win rate/payda, profit factor sıfır kayıp durumu, exposure, turnover, time underwater |
| Yıllık metrik | CAGR/Sharpe/Sortino için süre, örnekleme, risk-free ve yetersiz örnek undefined |
| Portföy/grid | Açık envanter kaybı gizlenmez; grid kârı toplam kâr diye yazılmaz |
| Kıyas/optimizasyon | Buy-and-hold aynı fee/cashflow varsayımı; OOS ve walk-forward; leakage kontrolü |

Run kimliği: run_id + dataset_hash + config_hash + kernel_version/hash + simulator_version + instrument/risk snapshot hash + seed. Export bu kanıtı taşır. Dataset güncellenince geçmiş sonucu sessizce yeniden adlandırma; yeni run aç. Tam veri üzerinde ticari performans kanıtı ile küçük fixture üzerinde yazılım testi ayrı durumdur.
