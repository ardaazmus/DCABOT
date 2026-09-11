# CORE01 mevcut kodunun kullanım sözleşmesi

Bu dosya 0.1.0 kodunun gerçek sınırlarını anlatır. Nihai ürün kapsamı ve güncel iş sırası URUN_KAPSAMI/YOL_HARITASI belgelerindedir. Aşağıdaki eski N kodları tarihsel karşılaştırmadır; UI/demo önceliğini değiştirmez.

## Sayı ve birim

Finansal JSON alanları düz ondalık string olmalı: `"0.04"`. JSON float, bool, NaN/Infinity, bilimsel üs, boşluk, alt çizgi reddedilir. Giriş en çok 50 karakter, 24 kesir basamağı ve mutlak 10^12; executable tick/step/base/safety/fee quantum en çok 12 kesir basamağıdır. Grid dışı emir büyütülmez; ret verilir. Sayaçlar gerçek int'tir, bool değildir.

Sınırda Decimal doğrulaması; içeride Fraction ile tam rasyonel maliyet/PnL/risk hesabı kullanılır. DB'nin nakit kayıtları numerator/denominator string çifti taşır. Kısmi kapanışta bölünmeyen maliyet son kapanışa kadar tam kalır; gizli residual veya global Decimal context bağımlılığı yoktur. İç numerator/denominator 4096 bit ile sınırlıdır; aşılırsa transaction reddedilir.

Raporun ondalık alanları 12 basamağa HALF_EVEN yuvarlanır, karar hesabına geri verilmez. `exact_ratios` temel ekonomik alanları kayıpsız verir. Çok küçük pozisyon raporda 0'a yuvarlanabilir; gerçek qty için exact_ratios kullanılır. Simülasyon ücreti her fill'de config.fee_quantum'a HALF_EVEN ile yuvarlanır. Net TP fiyatında bu ücret yuvarlaması için yarım quantum konservatif pay vardır.

Config yalnız BASE_QTY, sabit final base VWAP anchor ve cumulative deviation uygular. QUOTE_NOTIONAL, short/spot/cross/hedge ve dış nakit akışları bu sürümde yoktur. `initial_equity` sentetik başlangıç teminatıdır; `max_entry_notional` tüm deal boyunca brüt alım notional tavanıdır. Bunlar aynı büyüklük değildir. Local IM tahmini pozisyon mark notional/leverage + aday notional/leverage + fee'dir; venue collateral veya likidasyon garantisi değildir.

## Olay API'si

Her olay JSON dosyasıdır. Tek komut:

```powershell
py -3.13 tools/bot.py event --db data/paper.db --id olay-001 --input olay.json
```

Olay ID'si yeniden kullanılmamalı; aynı ID/aynı payload idempotent, aynı ID/farklı payload kalıcı incident olur. FILL ayrıca execution_id ile tekilleştirilir; farklı taşıma ID'si aynı execution'ı ikinci kez uygulamaz. Finansal stringlerin farklı yazımı farklı payload sayılır (`"1"`/`"1.0"`); değişik gözlem sessizce eşdeğer ilan edilmez. Funding ekonomik kimliği `--id` olarak sabit tutulmalıdır; farklı ID ile tekrar verilirse farklı olaydır.

Yalnız sentetik/normalize edilmiş offline olay kabul edilir. Source venue/account/symbol namespace'i bu tek DB'nin config'i ile sınırlıdır; gerçek REST/WS normalizasyonu henüz yoktur.

| Olay | Gerekli alanlar (type dışında) |
|---|---|
| MARK | price |
| INTENT | order_id, role, qty, limit_price |
| FILL | execution_id, order_id, side, qty, price, fee, fee_asset |
| ORDER_FINAL | order_id, status, filled_qty, coverage_complete |
| UNKNOWN | order_id |
| FUNDING | amount, asset |
| POLICY_REJECTION | reason; otomatik replay'in görünür yerel ret kaydı |

Örnek sıra (her nesne ayrı dosya/ID):

```json
{"type":"MARK","price":"100"}
{"type":"INTENT","order_id":"base","role":"BASE","qty":"1","limit_price":"100"}
{"type":"FILL","execution_id":"trade1","order_id":"base","side":"BUY","qty":"0.5","price":"100","fee":"0.05","fee_asset":"USDT"}
{"type":"ORDER_FINAL","order_id":"base","status":"CANCELED","filled_qty":"0.5","coverage_complete":true}
```

Bu dört JSON satırı tek geçerli JSON belgesi değildir; komuta ayrı nesneler verilir. Kısmi base bu kapsamlı finalden sonra actual VWAP ile safety planını etkinleştirir. Sonraki role `SAFETY:1`, sonra `SAFETY:2`; exit role `EXIT` veya DD sonrası `STOP`, side=SELL. Intent ve status pozisyon yaratmaz. FILL toplamı emri bitirse bile final coverage gelmeden sıradaki niyet üretilmez.

Kısmi safety + CANCELED planın kalan safety adımlarını durdurur; otomatik kalanı yeniden gönderme veya seviye atlama yoktur. Terminal sonrası geç, sınırlar içinde fill kayda alınır, coverage UNKNOWN ve blocker olur. Geç fill nedeniyle sabit anchor sessiz değişmez. Blocker temizliği manuel DB edit ile yapılmaz; ayrı recovery görevi gerektirir.

Geçersiz sentetik overfill, bilinmeyen order/fee asset veya çelişkili execution ham istek olarak incidents tablosunda saklanır; sahte finansal başarı üretilmez ve yeni risk bloklanır. **Gerçek borsa overfill/reversal muhasebesi uygulanmadı.** Bu offline karantina gerçek gerçekleşmenin tam muhasebeleştirilmesinin yerine geçmez. Incident olan DB'de audit muhasebe tutarlılığı PASS verebilir; bu trading izni değildir, incidents sayısı ayrı gösterilir.

## Replay ve yeniden başlama

Input: benzersiz id + price taşıyan sıralı JSON liste. Liste sırası olay sırasıdır; gerçek zaman/latency veya OHLC mum semantiği iddia edilmez. Her tick tek SQLite transaction içinde MARK → karar → INTENT → sentetik FILL → kapsamlı FINAL uygular. Policy reddi görünür POLICY_REJECTION kaydı bırakır. Gap bir tick'te bütün ladder'ı doldurmaz; yalnız sıradaki bir seviye değerlendirilir.

Alış gerçekleşme fiyatı mark*(1+slippage), yukarı tick; satış mark*(1-slippage), aşağı tick. Böylece gerçek simülasyon fiyatı PnL'ye girer; slippage ikinci gider olarak düşülmez. Oran LIMIT emrinden maker sonucu çıkarmaz; yalnız bu sentetik modelin açık ücret girdisidir. Kısmi dolum/sıra/likidite simülatörü değildir.

Bir tick'in tüm etkileri atomik olduğundan süreç ölümü o tick'i tamamen geri alır veya tamamını korur. Aynı listeyle yeniden çalışma idempotent devam eder. Manuel olayda UNKNOWN varsa otomatik yeni emir yoktur. Bu davranış offline journal restart'ıdır; dış borsayla reconciliation veya ağda exactly-once kanıtı değildir.

## Kalıcılık ve muhasebe

Yeni SQLite DB: uygulama kimliği/schema/engine sürümü ve config hash'i kontrol edilir. Mevcut yabancı/legacy DB üzerine yazılmaz, otomatik migration yapılmaz. Bir ekonomik olay ve WALLET/REALIZED_PNL/FEE_EXPENSE/FUNDING_EXPENSE kayıtları aynı transaction'dadır; her olayın nakit kayıtları sıfıra dengelenir. Futures giriş notional'ı cüzdandan spot alım gibi düşülmez. Pozisyon maliyet tabanı olaylardan yeniden hesaplanır.

`BEGIN IMMEDIATE` tek DB içindeki kabulü serileştirir. Bu sürüm yalnız bir unresolved emir kabul eder; onun qty/limit'i pending yükü temsil eder ve ikinci niyet reddedilir. Ayrı hesap-geneli çok emir rezerv tablosu/outbox/kalıcı sender attempt yoktur; N03/N04 tamamlandı sayılmaz.

Replay küçük örnekler için en çok 2500 tick, journal en çok 10000 olay kabul eder. State olaylardan yeniden hesaplanır; uzun tarihçede maliyet artar. Büyük veri backtest performansı ve projection/checkpoint optimizasyonu sonraki iştir. Veri dosyası secretsiz olsa da WAL/shm ile çalışan DB'nin düz kopyası tutarlı backup sayılmaz; aktif DB backup yöntemi ayrıca uygulanmalıdır.

## Operasyon sınırı

Bir deal bittiğinde kendiliğinden yeni base başlamaz. DD/minimum equity kapısı kilitlenir; piyasa toparlanınca otomatik açılmaz. Bekleyen/UNKNOWN order varken bu küçük motor koruyucu başka emir de göndermez; live koruma/cancel orchestration yoktur. Exit minNotional/qty altında kalırsa görünür ret oluşur; dust'ı otomatik büyütmez. Bu yüzden canlı daemon olarak kullanılmaz.

`tools/run_offline.py` eski başlangıç komutuyla uyumlu sağlık çıktısıdır; işlem simülasyonu için `tools/bot.py demo` veya replay kullanılır.
