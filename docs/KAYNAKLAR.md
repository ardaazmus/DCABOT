# Kaynak ve kanıt sınırları

Erişim: 6 Eylül 2026. Sadece aşağıdaki teknik birincil kaynakların bu çalışmada açılan ilgili bölümleri kullanıldı. Mimari tercih, görev boyutu ve context bütçesi bu projeye yönelik mühendislik önerisidir; standart kuruluşunun zorunlu kuralı diye sunulmaz.

| ID | Kaynak | Doğrudan desteklediği konu |
|---|---|---|
| S01 | [Kaynak depo, sabit commit](https://github.com/ardaazmus/DCABOT/tree/318e1c409ff67083168b31fdd5a27fb28ec7d5f7) | Gerçek kod/doküman davranışı; master'ın gelecekteki hali değil |
| S02 | [Binance Futures General Info](https://developers.binance.com/en/docs/products/derivatives-trading-usds-futures/general-info) | Testnet adresleri, 503 mesaj ayrımları, rate limit ve imza protokolü |
| S03 | [Binance Futures Market Data](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data) | Exchange information, instrument filters, mark/funding veri yolları |
| S04 | [Binance Futures Trade](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/trade) | Trade ID/commissionAsset/maker, pozisyon/teminat/likidasyon alanları, order/algo nesneleri |
| S05 | [Python 3.13 Decimal](https://docs.python.org/3.13/library/decimal.html) | Precision/context, round/trap, float conversion, quantize |
| S06 | [SQLite atomic commit](https://www.sqlite.org/atomiccommit.html) | DB atomikliği ve storage/flush varsayımları |
| S07 | [PostgreSQL 18 isolation](https://www.postgresql.org/docs/18/transaction-iso.html) | Concurrent transaction ve serialization retry sınırı |
| S08 | [Linux flock](https://man7.org/linux/man-pages/man2/flock.2.html) | Tek host dosya tanıtıcısına bağlı advisory locking |

## Güncellik bulgusu

Kaynak gateway testnet URL'sini `https://testnet.binancefuture.com` olarak sabitliyor. S02'nin açılan güncel sayfası REST için `https://demo-fapi.binance.com`, WebSocket için `wss://demo-fstream.binance.com` belirtiyor. Bu fark eski endpoint'in kesin kapalı olduğu kanıtı değildir. P2'da gerçek seçili ortam ve sürüm doğrulanmalı; string değiştirip entegrasyon PASS sayılmamalı. Eski URL canlı emirle denenmedi.

## Kaynakların söylemediği şeyler

- S02–S04 kullanıcının gerçek hesap erişimini veya API yetkisini kanıtlamaz; gerçek hesaba bağlanılmadı.
- Spot ve Futures hata davranışı tek tabloya karıştırılmadı. Genel Spot API sayfası başlangıç kontrolünde açıldı, futures contract'ı için esas alınmadı.
- Bazı eski Binance URL'leri yeni katalog sayfalarına yönlendi; maker/fee/position alanları bu yeni katalogda kontrol edildi. İçeriği görünmeyen eski user stream sayfası kanıt olarak kullanılmadı.
- Matematikte DCA seviye politikası, net TP kökü ve öğretici likidasyon kökü açık varsayımlardan türetimdir. Borsa formülü diye atfedilmez.
- Eski raporların onlarca kaynak atfının tamamı yeniden araştırılmadı; güncel ilk kapsam dışındaki Bybit/OKX/grid/hybrid doğrulaması bu teslimin parçası değil.

Her gerçek venue kabul kaydı URL'den fazlasını taşır: product/account/mode/environment, endpoint/schema, erişim tarihi, redakte fixture hash'i ve çalışma kanıtı. URL varlığı `VERIFIED` değildir.

## Yeni iskeletin araç kaynakları

- [uv proje yapılandırması](https://docs.astral.sh/uv/concepts/projects/config/): Python sürüm gereksinimi ve package=false davranışı.
- [Python 3.13 unittest](https://docs.python.org/3.13/library/unittest.html): standart kütüphane test runner ve discovery.

Bu kaynaklar yeni kökün gerçek test kanıtı yerine geçmez; kanıt evidence/N00 içindedir.

## CORE01 uygulamasında doğrulanan teknik kaynaklar

- [Python 3.13 Decimal](https://docs.python.org/3.13/library/decimal.html): ondalık sınır, context ve gösterim yuvarlaması.
- [Python 3.13 sqlite3](https://docs.python.org/3.13/library/sqlite3.html): bağlantı, açık transaction ve parametreli SQL.
- [SQLite transaction](https://www.sqlite.org/lang_transaction.html): BEGIN IMMEDIATE ve yerel commit/rollback semantiği.

Fraction iç hesabı, tek pending emir ve sentetik tick modeli proje tercihidir. SQLite dokümanı venue ile atomiklik iddiasını desteklemez.

## Demo öncelikli ürün planının kaynakları

Rakip özellik referansları ve kapsam sınırı [OZELLIK_MATRISI.md](OZELLIK_MATRISI.md) içindedir. Veri kaynağı [Binance Public Data](https://github.com/binance/binance-public-data). HTTP/UI tabanları için [FastAPI](https://fastapi.tiangolo.com/) ve [React](https://react.dev/learn) resmî belgeleri incelendi. Bu teknoloji seçimi proje önerisidir; paket içinde yeni bağımlılık kurulmadı.
