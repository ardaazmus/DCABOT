# Anonim Kanıtlı Dış Araştırma Promptu

## Rolün

Yerel çalışan Python 3.13 + FastAPI tabanlı, yalnız offline tarihsel OHLCV simülasyonu yapan bir finansal yazılımın bağımsız ürün/matematik/güvenlik araştırmacısısın. Aşağıdaki bilgiler anonimleştirilmiştir. Proje adı, yerel klasör yolu, kullanıcı adı, artifact hash'i, credential, özel hesap veya canlı emir bilgisi yoktur ve araştırma için gerekli değildir.

Bu araştırma bir kod değişikliği talebi değildir. Amacın, aşağıdaki dört açık kararı bir sonraki küçük geliştirme fazında güvenle uygulayabilmek için birincil/otoritatif kaynaklara dayalı karar raporu hazırlamaktır. Her iddiayı doğru kabul etme. “Kod değişsin” sonucuna ancak matematik, mevcut sözleşme ve risk etkisi birlikte kanıtlanıyorsa var.

## Değiştirilemez güvenlik ve kapsam sınırları

- Uygulama yereldir; bu araştırma canlı borsa hesabı, API key, emir, testnet veya gerçek para işlemi istemez.
- Araştırma çıktısında gizli bilgi, kimlik bilgisi, özel dosya yolu, yerel URL veya kullanıcıya ait veri bulunmamalıdır.
- Çekirdek ekonomik hesaplar exact `Fraction` kullanır; dış sınırdaki finansal değerler ondalık string olarak gelir. UI finansal hesap yapmaz.
- Tarihsel model yalnız kapalı bar kullanır, OHLC içi sıra bilinmiyorsa `INDETERMINATE` üretir, aynı barda en fazla bir action işler ve eksik veriyi sessizce interpolate etmez.
- Slippage fill fiyatına uygulanıyorsa PnL'den ikinci kez düşülmemelidir.
- Hiçbir öneri Binance venue risk motoru, likidasyon garantisi, liquidity/fill garantisi veya canlı işlem tavsiyesi gibi sunulamaz.
- Öneri “uygulanmalı” diyorsa bunun karşılığında gereken yeni test senaryolarını, response/config değişikliklerini ve geriye dönük uyumluluk etkisini açıkça belirt.

## Mevcut doğrulanmış bağlam

Bu bağlam araştırma istemcisinin yaptığı yerel ön incelemeden gelir; dış kaynak yerine geçmez:

1. Resmi public Spot günlük kline artifact'ının 1 Ocak 2025 tarihli ilk `open_time` değeri mikro-saniye ölçeğindedir. Bu konu için yeniden milisaniye/mikro-saniye araştırması yapma; yalnızca başka kaynak bununla çelişirse çelişkiyi kanıtlarıyla belirt.
2. Tarihsel modelin long pozisyonu için ortalama maliyet `cost / qty` ve satış brüt sonucu `qty * execution_price - removed_cost` biçimindedir.
3. Long satış fill'i, ham tetikleme/referans fiyatından adverse slippage sonrası tick'e aşağı hizalanır. Alış fill'i adverse slippage sonrası tick'e yukarı hizalanır.
4. `GROSS_PRICE_RETURN` modunda mevcut TP eşiği yaklaşık `average * (1 + take_profit)` ve `NET_QUOTE` modunda mevcut kök, kalan maliyetler/önceki realized değer/çıkış fee'si üzerinden hesaplanır. Her iki durumda da gerçek exit fill'i ayrıca adverse slippage ile değişir.
5. Mevcut `NET_QUOTE` örneğinde pozisyon `qty=1`, `cost=100`, hedef `5`, çıkış fee oranı `0.001`, tick `0.01`, slippage `0.01` olduğunda mevcut eşik `105.11`, adverse slippage sonrası fill `104.05`, çıkış fee sonrası net fiyat sonucu `3.94595` olur. Bu, “hesaplanan eşik net hedefi garanti eder” semantiği seçilirse bir uyumsuzluk kanıtıdır; fakat eşik yalnız tetikleme seviyesi sayılıyorsa beklenen model sonucu olabilir.
6. Gerçek yerel BTCUSDT 1h artifact'ının ilk bar açılışı yaklaşık `93576` quote birimidir. Aktif demo config'inde `base_qty=1`, `initial_equity=1000`, `max_entry_notional=1000`, `leverage=1` ve fee oranı `0.001` bulunmaktadır. Bu nedenle ilk base notionalı üst sınırı aşar ve koşu güvenli politika reddiyle sonuçlanır. Bu değerleri doğrudan değiştirme; güvenli demo sizing kararı araştırılmalıdır.
7. Canonical parser zaman sırasını, dönem sınırını ve bar çakışmasını kontrol eder. Kalite katmanı gözlenen zaman delta'sını medyanla tahmin edip büyük boşlukları warning olarak raporlar. Tarihsel simülasyon barlar arasında beklenen sabit interval/grid sürekliliğini ayrıca reddetmez.
8. FastAPI'de küçük tarihsel validate gövdesi için 4 KiB limit vardır. Ham data-quality endpoint'i 20 MiB dosya sınırını ve bildirilen `Content-Length` değerini kontrol eder; gövde boyutu bildirilmemiş/chunked ise parser çağrısından önce ortak uygulama seviyesi sınır bulunmayabilir. Diğer küçük JSON POST gövdelerinde ortak limit davranışı ayrıca değerlendirilmelidir. Kalite raporu issue listesi satır başına uyarı üretebildiğinden yanıt boyutu için bounded response önerisi de incelenmelidir.

## Araştırma görevi A — TP/slippage sözleşmesi

Long-only, linear, tek quote-asset bağlamında aşağıdaki iki modelin hangisinin açıkça tercih edilmesi gerektiğini araştır:

### A1 — Tetikleme eşiği modeli

TP fiyatı, OHLC barı içinde “ham piyasa fiyatı bu seviyeye değdi” koşuludur. Gerçek execution fill'i adverse slippage ve tick hizalaması sonrası oluşur; bu nedenle görünen gross/net sonuç hedefin altında kalabilir. Bu durumda UI ve API'de hedefin garanti değil tetikleyici olduğu nasıl adlandırılmalı?

### A2 — Execution hedefi modeli

TP fiyatı, adverse slippage, tick hizalaması ve çıkış fee'si uygulandıktan sonra hedef net/gross sonucun sağlanacağı şekilde geriye doğru çözülür. `GROSS_PRICE_RETURN` için gerekli eşik; `NET_QUOTE` için gerekli eşik; alış/çıkış slippage yönleri; tick'in hangi aşamada uygulanacağı ve fee quantum yuvarlamasıyla güvenli üst sınır formüllerini exact matematikle türet.

### A3 — Karar için zorunlu ayrıntılar

- `NET_QUOTE` hedefinde geçmişte gerçekleşmiş realized kâr/zarar ile mevcut kalan pozisyon maliyetinin formüle nasıl girdiğini tanımla.
- Çoklu alış sonrası VWAP/weighted-average maliyette formülü göster.
- Kısmi satış ve tam satış için farkı belirt.
- `fee_quantum` round-to-nearest/ties-to-even benzeri yuvarlama payının hedefte nasıl güvenli ele alınacağını belirt.
- Tick hizalama hedefi yukarı/aşağı olduğunda hedefin “en az hedef” garantisi korunuyor mu göster.
- Aynı OHLC barında hem safety hem TP erişilebilirse bu kararın sonucu nasıl etkilediğini belirt; intrabar sıra uydurma.
- Slippage’ın execution fill içine dahil olduğu durumda PnL'yi ikinci kez düşürmeme kuralını doğrula.
- Bu yazılımın mevcut ilk fazında yalnız “tetikleme modeli + görünür sınırlama metni” uygulanmasının, execution hedefi araştırması tamamlanana kadar en güvenli seçenek olup olmadığını karar tablosuyla değerlendir.

### A için kaynak şartı

Formüller için güvenilir finans/muhasebe veya borsa API dokümantasyonu; tick/fee/slippage için ilgili resmi piyasa dokümanı veya açık matematiksel türetim kullan. Bir kaynağın venue-spesifik olduğunu ve bu yerel öğretici modelin birebir venue motoru olmadığını ayır. Blog/SEO yazısını tek başına kanıt sayma.

## Araştırma görevi B — Gap ve tarihsel veri sürekliliği politikası

1h OHLCV dizisinde beklenen open-time grid'i ile bir veya daha fazla bar eksik olduğunda aşağıdaki seçenekleri karşılaştır:

1. Koşuyu fail-closed reddetmek (`GAP_OBSERVED` / `DATASET_NOT_CONTIGUOUS`).
2. Koşuyu çalıştırmak fakat sonucu `INCOMPLETE` veya eşdeğer bir açık durumla işaretlemek; gap'i response ve UI'da görünür kılmak.
3. Kalite warning ile koşuyu `COMPLETED` saymak.
4. Yalnız seçilmiş veri aralıklarında “gap öncesine kadar” çalıştırmak.

Her seçenek için:

- OHLC'nin yalnız bar içi bilgi taşıdığı ve gap sırasında bilinmeyen fiyat yolu olduğu için DCA safety/TP tetikleme, realized PnL, drawdown ve açık pozisyon yorumuna etkisini analiz et.
- Eksik barı sıfır/hayali bar/interpolate ile doldurmanın neden güvenli veya güvensiz olduğunu kanıtla.
- Exchange public historical data'da gap/duplicate/out-of-order kayıtların görülebileceğini resmi kaynak veya doğrulanabilir örnekle göster; bir kaynağın borsa türünü (Spot/Futures) karıştırmadığından emin ol.
- Medyan delta ile gap tespitinin güçlü/zayıf yanlarını; interval metadata biliniyorsa bunun daha iyi olup olmadığını incele.
- `processed_bar_count`, action table, chart ve `INDETERMINATE` sözleşmesine etkisini belirt.
- İlk P1 fazında en küçük ve en dürüst davranışı seç; yeni endpoint veya kalıcı run kaydı önermeden önce gereksinimi gerekçelendir.

## Araştırma görevi C — Offline demo config sizing kararı

Amaç canlı işlem değil, gerçek public BTCUSDT 1h artifact üzerinde sahte başarı üretmeden yerel demo akışının en az bir güvenli `COMPLETED` veya açıkça beklenen `OPEN_AT_END` örnek üretebilmesidir.

Mevcut örnek bağlam: başlangıç quote equity `1000`, max entry notional `1000`, leverage `1`, fee `0.001`, slippage `0`, base/safety quantity `1`, BTC fiyatı yaklaşık `93576`.

Araştır:

- `base_qty=0.01` ve `base_qty=0.005` gibi adayların ilk notional, fee ve kalan equity sonuçlarını exact formülle karşılaştır.
- Safety quantity, safety count, deviation, max entry notional ve minimum equity birlikte nasıl seçilmeli? Bir adayın tüm teorik ladder notionalını da kontrol et.
- Bir günlük tek artifact'ın tarihsel fiyat aralığına bakarak config'i overfit etmenin sakıncalarını belirt.
- Demo config ile üretim/live/testnet config'inin aynı dosya/aynı anlamda tutulmasının riskini değerlendir; küçük fazda yalnız offline demo için hangi alanların değiştirilebileceğini ayır.
- `slippage=0` değerinin “gerçekçilik” değil deterministik demonstrasyon varsayımı olarak korunmasının veya küçük pozitif slippage kullanılmasının etkisini yaz.
- Bir config değişikliğinin hangi mevcut API hash/snapshot/plan ve test beklentilerini değiştireceğini listele.

Sonuçta tek bir zorunlu sayı uydurma. En az iki aday, her adayın formüllü artı/eksi tablosu ve “şimdilik değiştirme / araştırma sonrası değiştir” kararı ver. Tarihsel piyasa fiyatını gelecekte sabitmiş gibi sunma.

## Araştırma görevi D — FastAPI/Starlette gövde ve hata yanıtı sınırları

Yerel uygulamada küçük JSON endpoint'leri ile ham CSV/ZIP upload endpoint'ini birbirinden ayıran, bellek tüketimini sınırlayan bir güvenlik sözleşmesi araştır:

- FastAPI/Starlette request body'nin uygulama katmanına ulaşmadan veya kontrollü okunarak sınırlanması için resmi dokümantasyon ve güvenilir upstream kaynakları incele.
- `Content-Length` yoksa/chunked request varsa güvenli davranışı belirle. Yalnız header'a güvenmenin ve yalnız `await request.body()` sonrası kontrol etmenin risklerini karşılaştır.
- Küçük strict JSON gövdeleri için endpoint başına veya route sınıfına göre uygun üst limit yaklaşımını öner; ham data-quality dosyası için mevcut 20 MiB sınırını yanlışlıkla düşürme.
- Malformed JSON, validation error, oversized body ve quality rejection için tek/uyumlu Problem Details sözleşmesi öner; mevcut response biçimiyle geriye dönük etkisini belirt.
- Satır başına issue üreten kalite raporunun maksimum response boyutunu ve kullanıcıya sunulacak “ilk N + toplam” modelini öner. Orijinal payload'ın gizli/özel içerik taşıyabileceğini varsayarak hata mesajı sanitizasyonunu da değerlendir.
- Bu güvenlik değişikliklerinin P1 planında küçük bir dikey dilim olarak uygulanıp uygulanamayacağını, yoksa ayrı araştırma/faz gerektirip gerektirmediğini söyle.

### D için kaynak şartı

Öncelik resmi FastAPI/Starlette/Uvicorn dokümantasyonu, upstream kaynak kodu ve güvenilir güvenlik rehberleridir. Genel “OWASP önerir” ifadesi tek başına yeterli değildir; mümkünse ilgili mekanizma ve sınırın nasıl çalıştığını doğrudan göster.

## Zorunlu çıktı biçimi

Tek bir Markdown raporu üret ve şu sırayı koru:

1. **Kısa karar özeti:** A/B/C/D için `APPLY_AFTER_RESEARCH`, `KEEP_AS_IS`, `DOCUMENT_ONLY`, `DEFER`, `BLOCKED` etiketlerinden biri.
2. **Kaynak matrisi:** her kaynak için başlık, yayıncı/kurum, doğrudan URL, erişim tarihi, hangi iddiayı desteklediği ve güven seviyesi.
3. **A — TP/slippage:** varsayımlar, exact türetimler, sayısal örnekler, tick/fee quantum etkisi, tavsiye edilen v1 semantiği.
4. **B — Gap:** seçenek karşılaştırması, risk analizi, önerilen response/status/UI etkisi.
5. **C — Demo sizing:** aday config tablosu, formüller, overfit ve yanlış güven riskleri, öneri.
6. **D — Request limits:** resmi mekanizma, chunked/header/body davranışı, bounded error response önerisi.
7. **Uygulama öncesi kabul testleri:** her APPLY kararından önce yazılması gereken bağımsız test senaryoları ve beklenen sonuçlar.
8. **Uygulanmaması gereken öneriler:** araştırmanın desteklemediği veya canlı venue davranışı gibi yanlış yorumlanabilecek fikirler.
9. **Belirsizlikler:** kesin kanıtlanamayan her maddeyi açıkça `UNKNOWN`/`NOT_PROVEN` olarak işaretle.

## Kesin yasaklar

- Proje adı, yerel path, kullanıcı adı, özel veri, secret, credential veya gerçek hesap ayrıntısı isteme.
- Kaynak görmeden Binance/başka venue davranışı icat etme.
- Bir blog veya model tahminini “resmi kanıt” gibi sunma.
- Tetikleme fiyatını execution fiyatı, brüt sonucu net sonuç veya gap'li koşuyu tam veri gibi etiketleme.
- Araştırma sonunda doğrudan büyük kod bloğu yazma. Önce karar, formül, risk, test ve küçük faz sınırı ver.
- Bir iddia yalnızca test yok diye doğru kabul edilmemeli; test eksikliği ile davranış hatasını ayır.

Bu rapor yalnızca anonim yerel offline tarihsel simülasyon sözleşmesini netleştirmek için kullanılacaktır.
