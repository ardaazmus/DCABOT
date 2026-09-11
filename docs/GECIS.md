# Bu plan değişikliğinde ne düzeldi?

| Önceki kurgu | Kullanıcının istediği düzeltme | Yeni yer |
|---|---|---|
| Arayüz N12, testnetten sonra ve read-only | Arayüz ilk günden; bot kurma/çalıştırma/analiz/kontrol | P1.01–P1.20 |
| Tam tarihsel backtest N13 | Veri import/download + gerçek geçmiş veri demo önce | P1.02–P1.06 |
| İnternet bağlantısı venue entegrasyonuyla birlikte düşünülüyordu | Public veri erişimi ile private emir API'si ayrıldı | Veri modu × emir modu |
| Sonraki iş review ardından backend N03 | İlk gerçek UI/API dilimi; ihtiyaç kadar odak review | TASK P1.01 |
| Tek long/tek deal/tek pending nihai ürünü daraltıyordu | Bunlar bugünkü çekirdek sınırları; geniş matris P1 hedefi | URUN_KAPSAMI/OZELLIK_MATRISI |
| Basit dashboard yeterli olabilirdi | Modern builder/terminal/lab/data/portfolio/risk/assistant akışları | UI_UX |
| Diğer borsalar genel gelecek işi | Binance testnet→gerçek sonrası her venue için ayrı adapter/kabul | P4 |

Bu ZIP önceki 0.1.0 Python çekirdeğini ve testlerini aynen içerir. Yeni frontend, historical importer veya yeni borsa kodu eklenmedi. Değişenler: bağlayıcı ürün kapsamı, görev sırası, mimari/UX/veri gereksinimleri ve çalışma belgeleri.

Yerleştirme: yeni ZIP'i ayrı klasöre çıkar. Mevcut YEDEK_ESKI_PROJE ve geliştirme değişikliklerini koru. Kullanıcıda ek kod varsa kör üzerine yazmak yerine bu plan belgelerini yeni karara göre birleştir. Temiz başlangıç yapılıyorsa bu paketin DCABOT kökü kullanılabilir; tam eski yedek kökün altına aynı adla taşınır. ZIP'teki yedek alanı boştur.
