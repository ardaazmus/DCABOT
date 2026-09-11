# Ürün sözleşmesi — önce tam demo

Plan sürümü: DEMO_FIRST_1. Kullanıcının son kararı önceki N serisi sıralamanın yerine geçer. Python çekirdek sürümü hâlâ 0.1.0; bu teslim ürün planını düzeltir, arayüz veya veri ithalatı uygulanmış sayılmaz.

## Bağlayıcı teslim sırası

1. **P1: Arayüz + hesaplar + gerçek geçmiş veriyle tamamlanmış demo ürün.** Dosya içe aktarımı zorunlu; internet erişimi varsa public tarihsel veri indirme ve isteğe bağlı canlı fiyatla paper trading. Gerçek hesap/emir anahtarı gerekmez.
2. **P2: Binance testnet bağlantısı ve testleri.** P1'deki ekranlar/stratejiler aynı çekirdekle testnet adaptörüne bağlanır; destek matrisiyle gerçek kabul, fill, iptal, koruma ve restart kanıtlanır.
3. **P3: Gerçek kurulum ve Binance bağlantısı.** Paketleme, işletim, hesap doğrulama ve sınırlı canary; başarılı operasyon kanıtıyla kapsam artırma.
4. **P4: Diğer istenen borsalar.** Her borsaya ayrı capability/contract testleri; aynı UI ve çekirdek. Test ortamı varsa önce orası, yoksa read-only ve kontrollü kabul yolu.

Public veri indirmek P1'e aittir. Private testnet/account/trading API'si P2'ye aittir. İnternet bağlantısı ile gerçek emir yetkisi aynı şey değildir.

## Çekirdek ayrı mı?

Evet: çekirdek ekonomik kuralların ayrı **yazılım katmanıdır**, ayrı bir son kullanıcı ürünü veya zorunlu ayrı servis değildir. Arayüz veri gönderir; application kullanım senaryosunu işletir; çekirdek hesap/karar üretir; adaptör geçmiş veri, simülatör veya borsayla konuşur. Aynı hesap UI, demo ve canlı için üç kez yazılmaz.

CORE01 korunur ve genişletilir. Mevcut tek long/tek deal/sentetik tick kapsamı nihai ürün sınırı değildir. Modern arayüz eklemek tek başına spot, short, grid, çoklu bot, trailing veya çoklu TP desteği yaratmaz; bu özelliklerin ekonomi, persistence ve simülasyon davranışı P1'de geliştirilir.

## P1 bitmiş ürün tanımı

Kullanıcı Windows'ta projeyi açıp arayüzden veri seçer/içe aktarır, kalite raporunu görür, bot kurar, tüm giriş/çıkış/risk ayarlarının parasal etkisini önizler, geçmiş dönemi çalıştırır, grafikten olayları inceler, sonucu kaydeder, uygulamayı kapatıp geri açar ve aynı sonucu yeniden üretir. Terminal bilmek, API anahtarı girmek veya dosyadan manuel emir JSON'u yazmak temel akışın şartı değildir.

[Özellik matrisindeki](OZELLIK_MATRISI.md) P1 gereksinimlerinin kullanıcı akışları, hesapları ve kabul testleri tamamlanmadan P2 açılmaz. Yalnız güzel bir ekran, disabled düğmeler veya sabit örnek sayılar P1 tamamlanması değildir. Canlı borsa seçimi gibi doğası gereği sonraki aşamaya ait kontroller neden kapalı olduğunu gösterir.

“3Commas/Pionex'in tüm özellikleri” hedefi, doğrulanmış ürün aileleri ve izlenebilir gereksinim kimlikleriyle yönetilir. Açık kaynak ürün belgelerinin incelenmesi ücretli/bölgesel tüm ekranların eksiksiz görüldüğü anlamına gelmez. Kapsam açığı P1 kabul kaydında açık olur; karşılanmayan kritik özellik sessizce ertelenmez veya “tam eşdeğer” denmez. Yeni keşfedilen özellik aynı matrise eklenir; yeni master plan üretilmez.

## Sektör kapsamı ve ürün genişlemesi

Hedef aileler: DCA/averaging-down ve dönemsel alım, gelişmiş manuel işlem, grid çeşitleri, signal bot, portföy/rebalancing, backtest/optimizasyon, strateji şablonları, çoklu bot/pair, bağlantı/risk/operasyon ve açıklayıcı asistan. DCA, spot grid ve perpetual long/short farklı ekonomik sözleşmelere sahiptir. Spot envanteri, ücret varlığı ve cross/hedge teminat modeli birbirinin adı değiştirilmiş kopyası olmaz.

Borsa içi custody, fiat geçidi, kredi/earn ürünü, sosyal kullanıcı ağı gibi dış platform işletimi gerektiren yetenekler yerel UI ile sağlanmış sayılamaz. Bunların demo modeli ile gerçek platform bağımlılığı matriste ayrı kaydedilir. Kullanıcının istediği kapsam korunur; uygulanamayan borsa ürünü UNSUPPORTED veya EXTERNAL_DEPENDENCY olarak görünür.

## Daha iyi ürün için ölçülebilir hedefler

Kâr üstünlüğü iddiası yerine: tek tıkla grafikten hesap kaydına geçiş; anlaşılır “neden işlem açılmadı” açıklaması; config değişikliğinin önce/sonra sermaye etkisi; açık veri kalitesi ve dolum varsayımları; yeniden üretilebilir sonuç; basit/uzman görünümü; aynı UI'da demo/testnet/live ayrımı. Bunlar kendi ürün tasarım hedeflerimizdir, rakiplerde kesinlikle bulunmadığı iddiası değildir.
