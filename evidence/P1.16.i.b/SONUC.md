# P1.16.i.b — Exact stress economic contract rapor doğrulama

## Karar

- Alt faz durumu: `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED`
- Ekonomik stress uygulama kararı: `DEFERRED / NO-GO`
- Rapor kullanımı: Araştırma girdisi ve test hipotezi; proje talimatı veya ekonomik authority değildir.
- Sonraki tek iş: `P1.16.i.c` deterministic scenario/result identity karar kapısı.
- Production readiness: `NO`

Raporun kapsamı değerlidir; fakat “ACCEPT / uygulanabilir” satırlarının tamamı local contract ve bağımsız kontrol ile doğrulanmadığı için ekonomik runner, spread/slippage, volume participation, reserve adapter, yeni public API veya finansal UI açılmadı.

## Yerel kontrol

Mevcut proje authority’si rapordaki öneriden farklıdır:

| Alan | Yerel gerçek | Karar |
|---|---|---|
| Ekonomik sayı | `src/dcabot/domain/numbers.py` ve core `engine.py` içinde exact `Fraction` (`Q`) | `Decimal + ROUND_UP` otomatik geçirilmez |
| Dış sayı sınırı | Finansa giriş plain decimal string; output `exact_text` ile dış sözleşmeye çevrilir | `float` ve sessiz precision kaybı yok |
| Fee | Mevcut core quote asset (`USDT`) ve `round_quantum` ile exact Fraction hesabı | Fee rounding policy rapor ile değiştirilmeyecek |
| Historical slippage | Mevcut runner’da normal modelin config slippage’ı | Stress spread/latency/volume modeli değildir |
| Volume | Dataset kalite doğrulaması | Participation cap authority’si yok |
| OHLC ambiguity | Aynı bar safety/TP çakışmasında `INDETERMINATE / AMBIGUOUS_OHLC_PATH` | Tek keyfi path seçimi açılmadı |
| Reserve | Historical fixed-slice sonucu `reserve_model=NONE`; ayrı reservation sınırları mevcut | Atomic stress reserve lifecycle kanıtlanmadı |
| Stress identity | P1.16.e ayrı stress lineage, P1.16.h persisted binding metadata’sı | Ekonomik scenario sonucu üretmez; i.c’de ayrıca denetlenecek |
| Persistence | Mevcut Store economic journal ve historical run store ayrı sahiplik taşır | Rapor şeması mevcut store’a bağlanmadı |

## Bağımsız matematik kontrolü

Production reducer kullanılmadan Python `decimal` ile rapordaki fixture’lar yeniden hesaplandı.

| Fixture | Kontrol sonucu | Karar |
|---|---|---|
| T-01 BUY | `fill=100.10`, `fee=0.11` | Raporla uyumlu; yalnız örnek formülün doğrulanmasıdır |
| T-02 SELL | `fill=99.90`, `fee=0.10` | Raporla uyumlu; yalnız örnek formülün doğrulanmasıdır |
| T-07 HIGH_FIRST | Rapor formülüyle `fill=103.84`, `net=103.73`; rapor `103.89`, `+3.78` yazıyor | **RED / sayısal çelişki** |
| T-07 LOW_FIRST | `fill=95.90`, `net=95.80` | Bu branch örneğiyle uyumlu; diğer branch çelişkisi kapanmadan kabul edilemez |
| T-08 fee rounding | Per-fill `0.33`, aggregate `0.31` | Raporla uyumlu; seçim policy’sini çözmez |
| T-12 identity | Seed hash’e dahil ediliyor denirken deterministic modelde seed `null` ve hash dışı deniyor | **RED / identity çelişkisi** |

Bağımsız kontrol çıktısı:

```text
T01_buy=100.10
T02_sell=99.90
T07_tp_fill_from_report_formula=103.84
T07_tp_net_from_report_formula=103.73
T07_sl_fill_from_report_formula=95.90
T07_sl_net_from_report_formula=95.80
T08_per_fill_total=0.33
T08_aggregate=0.31
T12_identity_seed_policy=contradictory_if_seed_is_in_hash_but_deterministic_seed_must_be_null
```

## Karşı örnekler ve kritik düzeltmeler

### 1. Reserve oracle güvenli değil

Rapordaki `ReserveState` örneğinde `create(50) → consume(30) → release(30)` sonrası:

```text
reserved = 20
consumed = 30
available = reserved - consumed = -10
```

Yani örnek kendi `available >= 0` invariant’ını ihlal ediyor. `release` miktarı için active reservation owner, consumed/releasable ayrımı ve hangi alanın azaltıldığı tanımlanmadan reserve lifecycle uygulanamaz. Bu nedenle reserve bölümü `NO-GO` olarak kaldı.

### 2. JCS iddiası mevcut ekonomik identity ile aynı şey değil

RFC 8785 property sorting ve JSON primitive serialization tanımlar; yüksek hassasiyetli sayıları JSON string olarak taşıma ihtiyacını ayrıca açıklar. Rapordaki `json.dumps(default=str, sort_keys=True)` örneği tam bir JCS uyumluluk kanıtı değildir. Özellikle Decimal string politikası, null/default alanları, Unicode normalization ve numeric serialization aynı anda ayrıca test edilmelidir. Mevcut proje identity’leri bu rapor nedeniyle değiştirilmedi.

### 3. `Decimal` önerisi proje authority’siyle çakışıyor

Python 3.13 `decimal` modülü doğru yuvarlanan, context precision’ı değişebilen decimal arithmetic sağlar; bu, her işlem zincirinin sınırsız exact olduğu anlamına gelmez. Mevcut proje exact ekonomik çekirdek olarak `Fraction` kullanır. `Decimal`’a geçiş bir refactor değil; tüm invariant, serialization, store posting ve bağımsız oracle sözleşmesinin yeniden kanıtlanması olur. Bu fazda yapılmadı.

### 4. Volume participation ve latency uygulanabilir kanıt değildir

Rapor, OHLCV’nin queue position ve gerçek latency’yi taşımadığını doğru biçimde söylüyor; fakat sonra synthetic participation cap için `ACCEPT` satırı veriyor. Bu ancak açıkça `APPROXIMATE` etiketli bir model ve ayrı kullanıcı/ürün kabulüyle mümkün olabilir. Exchange calibration ve order-book/tick verisi olmadan gerçek fill sonucu gibi yayınlanmayacak.

### 5. Stop/limit/gap politikası henüz ortak authority değil

Rapor aynı bölümde market, limit, stop ve stop-limit için farklı referans ve gap kuralları öneriyor; ancak bunların mevcut reducer transition’larına ve mevcut fixed-limit politikalarına bağlandığını kanıtlamıyor. Özellikle stop-limit gap’te `NO_FILL` ile `GAP_FILL` arasında seçim yapılmadan yeni execution path açılmadı.

## Karar matrisi

| Rapor konusu | Audit kararı | Uygulama durumu |
|---|---|---|
| Quote/base/third-asset ayrımı | Quote-only sınır ve third-asset belirsizliği makul | Mevcut USDT sınırı korunur; third-asset `NO-GO` |
| Spread + slippage formülü | Bir synthetic candidate; genel doğru veya kalibre edilmiş exchange modeli değil | `DEFERRED` |
| Fee `ROUND_UP` | Mevcut Fraction half-even policy ile çelişiyor | `REJECT_FOR_CURRENT_CONTRACT` |
| Volume participation | OHLCV’den gerçek execution çıkarılamaz | `DEFERRED / APPROXIMATE_ONLY` |
| OHLC scenario set | Belirsizlik için doğru yön; branch state authority eksik | i.c/i.d öncesi economic implementation yok |
| Reserve lifecycle | Verilen oracle karşı örnekle başarısız | `NO-GO` |
| Duplicate/conflict | Mevcut Store’da kısmen kanıtlı, stress event schema’sına bağlanmadı | i.d’ye bırakıldı |
| Persistence/recovery | Öneri mevcut iki store’a bağlanmış değil | i.d’ye bırakıldı |
| Result identity | Mevcut separate stress identity var; rapor T-12 çelişkili | i.c aktif |
| Metamorphic tests | Test adayları yararlı; model policy’den bağımsız zorunluluk değil | i.c/i.e’de seçilerek uygulanacak |

## Resmî kaynak karşı kontrol notu

- Python 3.13 dokümanı `Decimal`’ın context precision ve rounding ayarlarına bağlı olduğunu, `quantize()` işleminin yuvarlama yaptığını ve exact decimal girişin arithmetic boyunca otomatik sınırsız exact anlamına gelmediğini gösterir: <https://docs.python.org/3.13/library/decimal.html>.
- RFC 8785 JCS, JSON primitive serialization’ını ECMAScript/I-JSON kurallarına bağlar; property sorting’i recursively tanımlar ve IEEE-754 kapsamını aşan sayılar için string kullanımını önerir: <https://www.rfc-editor.org/rfc/rfc8785.html>.
- Bu kaynaklar raporun “Decimal kullanılabilir” ve “canonical hash gerekir” yönünü destekler; ancak rapordaki özel fee, reserve, latency, volume, stop/gap ve scenario ekonomik policy’lerini kanıtlamaz.

## Kapanış kontrolleri

- Mevcut regresyon: `325/325 PASS`.
- Bağımsız Decimal fixture kontrolü: T-01/T-02/T-08 uyumlu; T-07 ve T-12 RED.
- Kod değişikliği: ekonomik kod yok; mevcut authority korunmuştur.
- Production readiness: `NO`.

## Sonraki geçiş

`P1.16.i.b` rapor denetimi tamamlandı; ancak ekonomik stress implementation gate açılmadı. Sıradaki güvenli iş `P1.16.i.c` içinde mevcut stress lineage/result identity’nin rapordaki seed, scenario, base-result, canonical serialization ve idempotency iddialarıyla bağımsız kontrol edilmesidir. Bu kontrol tamamlanmadan `.d` persistence/recovery veya `.e` ekonomik runner/public surface açılmayacaktır.
