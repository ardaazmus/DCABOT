# Kanonik matematik sözleşmesi

CORE01 lineer long temeli aşağıdadır. P1 ürün genişlemesinde spot/short/grid/çoklu TP/trailing/portföy hesapları bu kanonik sözleşmeye testli maddeler olarak eklenecek; mevcut fonksiyonların bunları zaten desteklediği varsayılmaz.

Sürüm: M1 · Durum: kanonik sözleşme; CORE01 uygulanmış alt küme ve sınırları CEKIRDEK_KULLANIM.md içinde. Formüller belirtilen varsayımlardan türetilmiştir; borsanın kapalı risk motoru olduğu iddia edilmez. Temel kapsam lineer, USDT uzlaşılı, tek bacaklı türevdir. Inverse, USDC settlement, cross ve portfolio margin bu formüllere otomatik taşınmaz.

## M01 — Temsil ve birimler

| Değer | Birim / temsil |
|---|---|
| Fiyat p, ortalama A, mark m | quote/base |
| Pozitif miktar q | base; kontrat adedi geliyorsa çarpanla dönüştür |
| Yön s | Long +1, short −1; ilk uygulama yalnız long |
| Notional N=q×p | quote; collateral ile aynı anlamda değil |
| Fee/funding/realized G | settlement varlığı |
| Oran | 2%=0.02; 20 bps=0.002 |
| Sayı | Sonlu Decimal; sayaçlar tamsayı, bool geçerli sayı değil |

Girişte string → Decimal; float, NaN, Infinity, aşırı uzun katsayı/üs reddedilir. JSON/DB finansal alanları string veya ölçeği açık tamsayı taşır. Sayıyı UI'da formatlamak karar verisini değiştirmez.

Decimal sınırda ondalık doğrulama için kullanılır. CORE01'de kabul edilen sayılar tam Fraction'a çevrilir; bölme dahil ekonomik hesaplar kayıpsızdır. DB posting'leri numerator/denominator string taşır. 4096-bit iç sayı sınırı hesap kaynaklarını sınırlar. Raporlarda yerel Decimal context ile 12 basamak HALF_EVEN gösterim yapılır; bu çıktı karar hesabına girmez. Tick/step ve limit karşılaştırmaları tam kesirle yapılır. Simülasyon ücreti açık quantum'a HALF_EVEN yuvarlanır; kalan ücret tahmini ile gerçek gider çift sayılmaz. Net TP çalışma fiyatında yarım fee quantum konservatif payı bulunur. Bu sayısal tasarım önceki belgenin genel precision önerisinin uygulanmış, daha kesin alt seçeneğidir. [Python Decimal](https://docs.python.org/3.13/library/decimal.html)

## M02 — DCA taksonomisi ve sabit seviye planı

İncelenen eski strateji davranışı periyodik yatırım değil, fiyat aleyhe gidince ekleyen `AVERAGING_DOWN` yaklaşımıdır. v>1 ise büyüyen safety miktarı/geometrik sermaye riski açık gösterilir. DCA kelimesi tek başına config değildir.

İlk sözleşme tercihleri:

- `sizing_mode=BASE_QTY` eski kodun miktar anlamıyla uyumludur; QUOTE_NOTIONAL ayrı açık seçenek olur.
- `anchor_mode=BASE_ORDER_FINAL_VWAP`: ilk emrin terminal ve fill kapsamı tamamlandıktan sonraki ortalama gerçekleşme fiyatı P0 sabitlenir. Kısmi ilk dolum sırasında pozisyon korunur, safety planı etkinleşmez.
- `deviation_mode=CUMULATIVE_FROM_ANCHOR`; d>0, step çarpanı a>0, n≥0.
- Yalnız bir risk artırıcı safety niyeti pending/unknown olabilir. Sonraki seviye önceki plan miktarı tamamlanınca açılır. Kısmi+iptal durumunda kalan planı yeniden yetkilendirme veya sonlandırma açık olaydır; sessiz seviye atlama yok.

Seviye i=1..n için:

$$D_i=d\sum_{k=0}^{i-1}a^k,\qquad P_i=P_0(1-D_i).$$

a=1 ise D_i=i×d. Tüm P_i>0 ve tüm D_i<1 zorunlu. Negatif fiyatı 1e−8'e sabitlemek yasaktır. Tick sonrası seviyeler çakışıyorsa config reddedilir veya açık yeni plan sürümü gerekir.

Örnek P0=100, d=0.10, a=1: 90,80,70. Ardışık referanslı bileşik model 90,81,72.9 verir; başka geçerli bir stratejidir fakat aynı mod adıyla uygulanamaz. Piyasa gap ile birkaç seviye geçerse bu sürüm tek sonraki niyeti üretir; ilerleme gerçekleşme sonrası yeniden değerlendirilir.

Önizleme teorik tam dolumları gösterir. Runtime state yalnız gerçek gerçekleşmelerle değişir. Preview, replay ve runtime aynı `build_plan(config, anchor, instrument_rules)` fonksiyonunu kullanır. Runtime farklı `bar.close` referansı yaratmaz.

## M03 — Plan notional'ı, bütçe ve collateral

BASE_QTY için `q_i=S_q v^(i−1)`, `N_plan=B_q P0 + Σ q_i P_i`.

QUOTE_NOTIONAL için `N_i=S_N v^(i−1)`, `q_i=down_qty(N_i/P_i)`; teorik notional üst toplamı:

$$N_{plan}=B_N+\begin{cases}nS_N&v=1\\S_N(v^n-1)/(v-1)&v\ne1.\end{cases}$$

Bu iki sizing modelini aynı `amount` alanına koyma. B=100, S=50, n=4, v=1 →300; n=8,v=2 →12.850 quote. Geometrik toplam doğrudur; fiyatın toparlanacağını kanıtlamaz. Market tetiklenip sonraki fiyattan dolarsa ladder fiyatı harcama üst sınırı değildir; kayma/fiyat bandı ve gönderim öncesi yeniden risk hesabı gerekir.

`total_margin_required` yerine üç ayrı alan: `planned_gross_notional`, `estimated_initial_margin`, `policy_required_collateral`. Lineer ideal IM=N/L yalnız kaba bileşendir. `N/L + N*MMR` borsa için kesin collateral formülü değildir. Bakım marjı ve başlangıç marjı farklı eşiklerdir; ücret/funding/gap tamponu üçüncü şeydir.

Stres yolları Ω, ara durum z, başlangıç equity C0, başlangıca göre net ekonomik değişim Π(z) için yerel politika:

$$R_{open}(z)=IM_{position}(z)+IM_{pending}(z)+R_{extra}(z)$$
$$R_{survive}(z)=MM(z)+R_{close}(z)+R_{funding}(z)+R_{gap}(z)$$
$$C_{required}=\max\left(0,\sup_{z\in\Omega}\{\max(R_{open},R_{survive})-\Pi(z)\}\right).$$

Bu, eski finansal araştırmadaki M08'in korunmuş mantığıdır. Tamponlar birbirini veya gerçekleşmiş gideri tekrar saymaz. Her durumda venue available balance, collateral varlığı, bracket ve emir kuralları ayrıca geçer. Sadece seçilmiş stres yollarını kapsar; sonsuz kötü fiyat/funding için garanti değildir. Maksimum safety sayısı stop-loss değildir.

Spot seçilirse kaldıraç/funding/MM yerine net teslim alınan varlık, quote harcaması, fee varlığı ve emir rezerviyle ayrı model gerekir. Eski R0 §3.2'deki spot toplamına vadeli MM/funding kalemlerini varsayılan ekleme; aynı emri plan harcaması ve open-order rezervi olarak iki kez sayma.

## M04 — Fill, ortalama ve kısmi kapanış

Aynı yönde benzersiz a miktarı p'den eklenirse:

`q'=q+a`, `C'=C+a*p`, `A'=C'/q'`, `ΔG=0`.

Emir kabulü, planlanan qty, gönderim sayısı ve status bu hesabın girdisi değildir. C pozitif referans maliyetidir; türev cüzdanından N kadar nakit çıkışı değildir.

0<r≤q miktarı p'den azaltma:

`ΔG=s*r*(p-A)`, `q'=q-r`, `C'=C-r*A`.

Kısmi kapanışta A değişmez (weighted-average cost yöntemi). Tam kapanışta q=C=0, A=null. Reversal kapanan ve yeni açılan parçaya bölünür; ilk ürün reduce-only çıkışta reversal yasaktır. Gerçek overfill gelirse olay silinmez: muhasebeleştir, ihlali bildir, yeni riski kapat.

| Olay | q | C | A | Birikimli brüt G |
|---|---:|---:|---:|---:|
| 1 @100 al | 1 | 100 | 100 | 0 |
| 2 @90 planla, yalnız 1 dolsun | 2 | 190 | 95 | 0 |
| Aynı fill tekrar gelsin | 2 | 190 | 95 | 0 |
| 0.5 @110 sat | 1.5 | 142.5 | 95 | 7.5 |
| Mark=100 | 1.5 | 142.5 | 95 | 7.5; U=7.5 |

Weighted average ve FIFO yanlış/doğru alternatifleri değildir; farklı muhasebe yöntemleridir. Tek raporda yöntem karıştırılmaz. FIFO raporuna net realized veren fonksiyon, brüt G bekleyen PnL alanına bağlanmaz.

## M05 — Fee, funding ve net hedef

Bu sözleşmede gider pozitif, gelir/rebate negatif: `K_fee>0` ödenen ücret. Raw venue işareti adaptörde dönüştürülür; yalnız isimden çıkarılmaz. Gerçek fill'in maker/taker rolü ve ücret varlığı esas alınır; `LIMIT => maker` çıkarımı yok. Gerçek trade kaydı rol ve commission alanlarını ayrı taşır. [Binance Trade](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/trade)

`fee_est=abs(q*p)*rate`; bps ise rate=bps/10.000. Bilinmeyen rol için görünür konservatif tahmin; gerçek ücret gelince tahminin farkı düzeltilir, ikisi birlikte gider olmaz. Funding saat/oranları sabit 8 saat kabul edilmez; gerçek olay, pozisyon ve snapshot'tan gelir. Alınan funding negatif giderdir.

İlk brüt long TP: `A*(1+t)`; adı `GROSS_PRICE_RETURN`. “Net %2” diye sunulmaz. Net hedef için referans sermaye C_ref ve istenen quote kâr T=t*C_ref açık seçilir. Henüz kısmen kapanmamış q miktarı, tüm giriş/bugüne kadarki funding gideri F ve çıkış notional oranı f_out için:

`net_long(p)=q*(p-A)-F-f_out*q*p`.

`P_TP_long=(q*A+F+T)/(q*(1-f_out))`, f_out<1.

Short için `P_TP_short=(q*A-F-T)/(q*(1+f_out))`; geçerli pozitif kök gerekir. Bu sabit ücret varsayımıdır; gerçekleşme garantisi değildir. Kısmi kapanmış deal'de geçmiş gerçekleşen net kâr, kalan hedef hesabından düşülür ve gider kapsamı ayrıca tahsis edilir.

Örnek q=2,A=95,F=0.19,f_out=0.001,T=1.9 →192.09/1.998≈96.14114114. Tick=0.01 ve long satış tabanı hedefinde 96.15'e yukarı hizalanır; net=1.9177. Brüt %1 hedef 95.95'te net yalnız 1.5181 olur.

Slippage gerçekleşen fill fiyatına girdiyse PnL'den ikinci kez çıkarılmaz. Üçüncü varlıkla ücret için zamanlı kur ve kaynak gerekir; dönüşüm eksikse net PnL INCOMPLETE olur. Spot base-fee envanteri de azaltır; türev gross miktar modeline aynen taşınmaz.

## M06 — Equity ve drawdown

Tek settlement varlığında `U=s*q*(m-A)`; aynı q,A,m için kaldıraç gross PnL'yi değiştirmez.

`E_t-E_0-X_period = ΔG + (U_t-U_0) - fee_period - funding_period - borrow_period - other_period`.

X net dış nakit akışıdır. Başlangıç U0 sıfır değilse çıkarılır. Kısmi kapanışta aynı mark'ta `ΔG+U_after=U_before` fiyat PnL'sini korur. Açık pozisyon kaybı toplam performanstan çıkarılamaz. Spot ve çok varlıklı portföyde varlık bakiyeleri/değerleme ayrı köprü gerektirir.

Dış akışlar yoksa `peak_t=max(E_u,u≤t)`, `DD_t=(peak_t-E_t)/peak_t`, `MDD=max DD_t`. Akış varsa işlem anında aralık bölünür; TWR endeksi üzerinden peak kullanılır. `initial_equity`'ye göre kayıp farklı metriktir, drawdown diye adlandırılmaz. 100→120→100: DD=1/6≈%16.6667. Risk her mark/fill/fee/funding olayında değerlendirilir; yalnız deal kapanışında değil. E≤0'da yüzdeler undefined, yeni risk kapalı.

## M07 — Likidasyonun doğru sınırı

İncelenen eski kod `A*(1-1/L+r)` long hesabını exact diye tanımlıyor. Aynı basit modelde bile tam kök farklıdır. Tek isolated lineer bacak; sabit q,A; nakit teminat W; MM(m)=r*q*m−d; fee/funding/diğer pozisyon yok varsayımı:

`W+s*q*(m-A)=r*q*m-d`.

Long: `m*=(q*A-W-d)/(q*(1-r))`.

Short: `m*=(q*A+W+d)/(q*(1+r))`.

W=q*A/L ve d=0 ise long `A*(1-1/L)/(1-r)`. A=100,L=10,r=.005 →90.4522613065…; eski kod 90.5. Cebirsel doğruluk, borsa likidasyonunu birebir modellediğimiz anlamına gelmez. Kök pozitif ve ait olduğu notional bracket aralığında olmalı; aksi kök geçersiz. Güncel collateral, bracket deduction, funding, fee, mark, mode gerekir.

Canlı riskte venue pozisyon/teminat snapshot'ı ve doğrulanmış koruma politikası esas alınır. `liquidationPrice=0` otomatik risksiz anlamına gelmez. Model/snapshot uyumsuzluğunda yeni risk açılmaz. Binance pozisyon verisi liquidationPrice, isolatedWallet ve margin alanlarını ayrı taşır. [Binance Trade](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/trade)

## M08 — Tick, step ve zaman

İzinli kafes başlangıcı o ve adımı h>0: `down(x)=o+h*floor((x-o)/h)`, `up(x)=o+h*ceil((x-o)/h)`. o ürün sözleşmesinden gelir. `quantize(.25)` .25 katlarına hizalama değildir. 100.13 için alt 100.00, üst 100.25.

Miktar aşağı hizalanır; minQty/minNotional başarısızsa otomatik büyütülmez. Long TP tabanı yukarı, alış limit tavanı aşağı; market/stop emrinde farklı niyet kuralları açık yazılır. Fiyat/miktar filtreleri sürümlü instrument snapshot'ından gelir; decimal basamak sayısı tek başına yeterli değildir. [Binance Market Data](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data)

Karar zamanı, trigger zamanı, gerçekleşme zamanı ayrılır. Kapanmış mum high/low'u görüp ertesi open'da market satmak geçerli bir simülasyon tercihi olabilir; fakat “TP fiyatından doldu” değildir. Aynı mum TP/SL sırası bilinmiyorsa önce TP kontrolü intrabar gerçeklik iddiası yapamaz. Önceden çalışan emirler için açık kötü durum sıralaması veya daha ince veri gerekir.
