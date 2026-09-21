# Araştırma — TradingView Sinyal Entegrasyonu, İleri Backtest ve Bot Kalitesi

**Tarih:** 2026-09-21 · **Kapsam:** Arda'nın isteğiyle (Tailwind/Next.js/IA konsolidasyonu ayrı kapıda) yalnız üç eksen: (1) TradingView sinyal entegrasyonu, (2) backtest'i sektör rakiplerinin (3Commas/Pionex/Bitsgap) önüne geçirecek istatistiksel sağlamlık, (3) matematik kesinliği ve bot operasyonel kalitesi. Üç bağımsız araştırma oturumu (dış kaynak) + kod tabanının doğrudan denetimi (iç kaynak) birleştirildi. Kullanıcının önceki oturumdan aktardığı dış araştırma metni burada **doğrulandı, düzeltildi ve DCABOT'un gerçek koduna bağlandı** — düzeltilen en önemli nokta madde 1.1'de.

---

## 0. Yönetici özeti

DCABOT'un çekirdek disiplini (exact Fraction/Decimal, fail-closed, idempotent attempt ledger) **sektör rakiplerinden zaten daha sağlam**. Ama üç alanda kod hazır olduğu halde hiçbir HTTP/orkestrasyon ucuna bağlanmamış durumda — yani "yeniden yazmak" değil, "zaten var olanı bağlamak" gerekiyor:

| Alan | Mevcut durum | Eksik |
|---|---|---|
| TradingView sinyali | `signal_intake.py`'de HMAC-SHA256 doğrulama (`verify_signal_signature`) ve replay-window kontrolü (`check_replay_window`) **yazılmış ve test edilmiş** ama hiçbir API endpoint'i çağırmıyor — ölü kod | Gerçek webhook endpoint'i, durable dedup store, TradingView'ın gerçek kısıtlarına uygun kimlik doğrulama |
| Overfitting direnci | `chronological_split.py` (train/gap/test sınırı) + `horizon_overlap.py` (purge kararı, NO_OVERLAP/PURGE_REQUIRED) + `trial_registry.py` (kaybedenleri de saklayan sınırlı kayıt) + `oos_lineage.py` (OOS veri tekrar kullanımını engelleme) — bunların **hepsi** CPCV/PBO/DSR'nin akademik literatürdeki temel yapı taşları | Embargo primitifi, kombinatoryal N-grup/C(N,k) path üretici, PBO/DSR skorlayıcı — bunlar hiç yok |
| Backtest ölçeği | Tek-thread, 1000 bar/5 saniye tavanlı tek çalıştırma | Paralel parametre taraması, optimizer, bellek-içi bar önbelleği yok |
| Matematik kesinliği | `numbers.py`: Fraction iç hesap, `Decimal` sınırında `ROUND_HALF_EVEN` (banker's rounding), 1400 haneli precision context, `align`/`round_quantum` ile tick/step hizalama — **zaten doğru ve sağlam** | Yeni istatistik katmanının (Sharpe/PBO/DSR) float kullanıp kullanamayacağı — açık karar sorusu (bkz. §4) |
| Bot operasyonel kalitesi | `order_attempt.py`: PREPARED→PERSISTED→SENDING→ACKNOWLEDGED/UNKNOWN/RECONCILING/REJECTED durum makinesi, crash-safe attempt ledger, mutation gate — **zaten Hummingbot/Freqtrade seviyesinde** | Aşağıda §5'te küçük sertleştirme önerileri |

Sonuç: bu üç eksende DCABOT'un "temeli" rakiplerden ileride; eksik olan üst katman **orkestrasyon ve istatistik**, çekirdek mimari değil.

---

## 1. TradingView Sinyal Entegrasyonu

### 1.1 Kritik düzeltme: TradingView'da native HMAC yok

Önceki araştırma metninin varsaydığı "gelen Webhook payload'ları için HMAC/Secret imza doğrulama katmanı" ifadesi **yanıltıcı**: TradingView'ın resmi webhook belgeleri doğrulandı — TradingView, giden webhook isteğine **özel header ekleyemez ve hiçbir imzalama fonksiyonu çalıştıramaz**. Yalnızca bir URL + serbest metin/JSON mesaj gövdesi tanımlarsınız; tek güvenlik notu "kimlik bilgilerini mesaja koyma"dır ve webhook alert kullanmak için hesapta 2FA şart koşulur. Yani TradingView **kendi başına** hiçbir isteği kriptografik olarak imzalayamaz.

**Gerçekçi model:** mesaj gövdesine gömülü, uzun/rastgele **paylaşılan gizli anahtar (static shared secret)** — sunucu bunu sabit-zamanlı (`hmac.compare_digest`) karşılaştırır. Gerçek HMAC yalnız her iki ucu da siz kontrol ederseniz mümkündür (örn. TradingView → sizin yazdığınız bir **relay/middleware** → DCABOT; relay isteği alır, gizli anahtarla DCABOT'un beklediği HMAC'i hesaplar ve DCABOT'un zaten var olan `verify_signal_signature`'ına gönderir).

**DCABOT'a somut öneri:** `signal_intake.py`'deki `verify_signal_signature` (HMAC-SHA256, `keys: Mapping[str, str]`, sabit-zamanlı karşılaştırma) **aynen korunsun** — bu, TradingView'ın kendisi tarafından değil, DCABOT'un kendi süreç içi "webhook alım katmanı" tarafından üretilecek bir imza için kullanılacak. Gerçek TradingView ucu için ayrı, daha basit bir kontrol yeterli: mesaj gövdesindeki sabit `secret_token` alanının beklenen değerle sabit-zamanlı eşleşmesi. İki katman birbirini dışlamaz: TradingView→DCABOT hattı static-token ile, DCABOT'un iç `/api/signals/*` ailesi (script/relay/manuel test) HMAC ile korunur.

### 1.2 Idempotency / dedup — DCABOT'un content-hash yaklaşımıyla birebir örtüşüyor

TradingView'ın **doğal bir eşsiz alert ID'si yok**. Kullanılabilir alanlar: `{{time}}` (bar/alert zaman damgası, yalnız bar-kapanış çözünürlüğünde), ve yalnız *strateji* scriptlerinde `{{strategy.order.id}}` (Pine'ın kendi emir kimliği — indikatör-tipi alertlerde yok). Sektör pratiği: `(strateji/sembol + aksiyon + {{time}} + fiyat)` bileşik anahtarının hash'i, kısa bir pencerede (endüstride 5-10 saniye örnekleri var) dedup. Bu **DCABOT'un zaten `hash_signal_payload` ile yaptığı canonical-JSON hash + `check_replay_window`'daki `seen_ids` mantığıyla neredeyse birebir aynı** — yalnız `seen_ids`'in şu an çağıran tarafından (in-memory) sağlanması gerekiyor; durable bir SQLite-backed store'a taşınması gerekiyor (mevcut `AttemptStore`/`two_leg_journal.py` desenlerinin aynısı tekrar kullanılabilir).

Ayrıca **hızlı-ACK disiplini** şart: TradingView, hızlı `200 OK` almazsa yeniden dener; bu yüzden endpoint önce dedup+kabul kaydını yazıp 200 dönmeli, ağır işleme (candidate binding vb.) sonrasında/eşzamansız yapılmalı.

### 1.3 Pine Script paritesi — offline backtest için

- **`PyneSys/pynecore`** (doğrulandı: gerçek, aktif, Apache-2.0, AST-tabanlı Python transpiler, `Series`/`Persistent` semantiği, CLI backtest desteği var). **Önemli sınırlama:** `.pine` kaynağını PyneCore-Python'a **tam otomatik çevirme adımı PyneSys'in ücretli hosted API'sine/Discord botuna dayanıyor** — yani "tamamen ücretsiz, tamamen offline Pine paritesi" iddiası tam doğru değil; script'i elle taşımadan tam otomasyon için dış servise dokunuluyor.
- **"PineTS"** kullanıcı referansı isim karışıklığıydı: gerçek proje **`LuxAlgo/PineTS`** — ama bu **TypeScript/Node.js** hedefli, Python değil. `be-thomas/OpenPineScript` de gerçek ama yine TS, ve yalnız Pine v1/v2'yi destekliyor (v5/v6 değil). İkisi de Python/FastAPI yığınına köprü olmadan doğrudan kullanılamaz.
- **Daha basit alternatif:** indikatörleri doğrudan Python'da (`pandas-ta-classic` — orijinal `twopirllc/pandas-ta` GitHub'dan kaldırıldı, topluluk devamı bu isimde; opsiyonel TA-Lib hızlandırma) yeniden implemente etmek. Trade-off: taşınabilirlik/parite kaybı — Pine'ın `nz()`, series-vs-scalar semantiği gibi ince farkları elle doğrulanmadan **sessiz mantık sapması** riski taşır; DCABOT'un "sinyal → aday bağlama" zincirinin idempotency/no-mutation disiplinine göre bu risk hafife alınmamalı.

**Öneri sıralaması:** (a) ilk dilim — gerçek TradingView alert'i kabul eden dar bir webhook + static-token + dedup + mevcut `signal_intake`/`signal_candidate_binding`'e bağlama (dış repo bağımlılığı yok); (b) ikinci dilim — `pynecore`'u yalnız *offline backtest* tarafında (script elle taşınarak) deneme; TradingView bağımlılığı gerektirmeyen bir yol olarak.

---

## 2. Backtest'i Rakiplerin Önüne Geçirme — Overfitting Direnci

3Commas/Pionex/Bitsgap'in backtest'lerinde **sıfır istatistiksel geçerlilik kontrolü var** — tek bir P&L sayısı gösterirler, kaç parametre denendiği/aşırı-uyum riski hiç raporlanmaz. DCABOT bunun *kimlik/bookkeeping altyapısını zaten kurmuş* — akademik literatürdeki (Marcos López de Prado, *Advances in Financial Machine Learning*) üç temel yapı taşı koda birebir karşılık geliyor:

### 2.1 Combinatorial Purged Cross-Validation (CPCV)

- **Purging** (bir etiketin olay-ufku test kümesiyle çakışıyorsa o örneği eğitimden çıkar): `horizon_overlap.py`'nin `NO_OVERLAP`/`PURGE_REQUIRED` kararı ve `chronological_split.py`'nin `ChronologicalPoint(sample_id, event_time_us)` zaman kimliği bunu **doğrudan karşılıyor**.
- **Embargo** (test bloğundan hemen sonraki artık-otokorelasyonu emen tampon bölge): **DCABOT'ta hiç yok** — yeni bir `embargo_window.py` primitifi gerekir (toplam bar sayısının küçük bir yüzdesi veya açık mikrosaniye genişliği parametreli).
- **Kombinatoryal kısım**: veri N eşit gruba bölünür, k tanesi test olarak seçilir → `C(N,k)` farklı train/test bölünmesi; her grup tam olarak `φ = k·C(N,k)/N` kombinasyonda test'te yer alır, bu φ sonuç iç içe geçmeyen tam-uzunluklu **yol (path)**'lara dikilir — her path bir Sharpe oranı üretir, tek sayı değil **dağılım**. Bu tamamen yeni: N-grup bölücü + `C(N,k)` üretici + path-birleştirici + her path için Sharpe hesaplayıcı. En sağlam referans implementasyon: `skfolio.model_selection.CombinatorialPurgedCV` (aktif bakımlı, 2025 arXiv makalesi var); yapısal referans olarak `sam31415/timeseriescv` (MIT, `PurgedWalkForwardCV`/`CombPurgedKFoldCV`) de uygun ama küçük/tek-bakımcı, kullanmadan önce son commit tarihine bakılmalı.

### 2.2 Probability of Backtest Overfitting (PBO)

Bailey, Borwein, López de Prado & Zhu'nun **CSCV** prosedürü: N konfigürasyonun (=`trial_registry`'deki `SUCCEEDED` trial'lar) T dönemlik getiri matrisini S eşit bloğa böl → `C(S, S/2)` kombinasyonun her birinde S/2 blok in-sample (IS), kalan S/2 out-of-sample (OOS) → IS'de en iyi konfigürasyonu seç → onun OOS göreli sırasını (`ω̄`) bul → `λ = ln(ω̄/(1-ω̄))` logit'ini hesapla → **PBO = λ<0 olan kombinasyon oranı**. `trial_registry.py`'nin FAILED/INVALID trial'ları da bilinçli sakladığı için, PBO hesabı önce yalnız `SUCCEEDED` + karşılaştırılabilir zaman aralığına filtrelemeli — bu filtreleme mantığı bugün yok, yeni bir `overfitting_probability.py` modülü gerekiyor (registry'yi salt-okunur tüketen).

### 2.3 Deflated Sharpe Ratio (DSR)

Probabilistic Sharpe Ratio (PSR) formülü çarpıklık (`γ₃`) ve basıklığı (`γ₄`) hesaba katarak standart hatayı büyütür; DSR, PSR'nin karşılaştırma eşiğini **"N bağımsız denemeyle şans eseri ulaşılabilecek beklenen maksimum Sharpe"** (`E[max SR_N]`, Euler-Mascheroni sabiti içeren kapalı-form yaklaşık formülü mevcut) ile değiştirir. N = `trial_registry`'deki `SUCCEEDED` trial sayısı; López de Prado'nun sonraki çalışması, neredeyse-birbirinin-aynısı parametre setlerinin her birini "tam bağımsız deneme" saymamak için trial korelasyon matrisi üzerinden hiyerarşik kümeleme ile **"efektif" N** kullanılmasını öneriyor — ilk kesimde ham N ile başlanıp bu iyileştirme ikinci dilime bırakılabilir.

### 2.4 Tamamlayıcı testler

White's Reality Check / Hansen's SPA: bootstrap-tabanlı, "en iyi strateji şans mı gerçek mi" testi — CPCV/PBO/DSR'nin zaman-sıralı purge/embargo mantığından farklı, tamamlayıcı bir doğrulama katmanı olarak (CPCV path getirilerinin bootstrap'ıyla) ikinci aşamada eklenebilir; ilk kesimde gerekli değil.

### 2.5 Kütüphane/lisans durumu

`mlfinlab` (hudson-and-thames) artık **kapalı/ticari lisanslı** — doğrudan bağımlılık olarak kullanılamaz, yalnız algoritma referansı olarak okunabilir. `skfolio` (BSD/MIT-benzeri) ve `sam31415/timeseriescv` (MIT) en uygun yapısal referanslar; `rubenbriones/Probabilistic-Sharpe-Ratio` PSR/DSR formüllerinin kısa, doğrudan-taşınabilir Python karşılığı. **Hiçbiri Fraction kullanmıyor — hepsi numpy float.**

---

## 3. Backtest Ölçekleme Mimarisi

### 3.1 Paralelleştirme: multiprocessing vs Python 3.13/3.14 free-threading

- Python 3.13'ün "no-GIL" build'i **deneysel**; 3.14 (2025-10) ile artık deneysel değil ama hâlâ **opt-in varyant** (`python3.14t`), varsayılan değil (PEP 779 destek çerçevesi tanımlı). Saf-Python CPU-bound döngülerde gerçek ~2.3-2.8x hızlanma ölçülmüş — Fraction hiçbir C-extension'la hızlanmadığı için **teorik olarak DCABOT'un reducer döngüsü için ideal aday**.
- **Kritik risk:** uyumsuz bir C-extension yüklenirse CPython **sessizce** GIL'e geri dönebilir — fark edilmeden. FastAPI 0.136.0 free-threading'i resmî destekliyor; ama Pydantic'in Rust-tabanlı çekirdeği (pydantic-core) **hâlâ tam garanti vermiyor**.
- **Sonuç/öneri:** free-threaded yorumlayıcıyı **üretim FastAPI/uvicorn servisiyle aynı process'te asla çalıştırma**. Backtest/sweep işini `ProcessPoolExecutor` ile tamamen ayrı worker process'lere ver — bu klasik GIL'li CPython 3.13 ile Fraction/Pydantic/FastAPI'yle sıfır risk çalışır. Free-threaded 3.13t/3.14t, yalnız saf-Python reducer'ı koşan izole bir opsiyonel ikinci havuz olarak **ileri faz**da, feature-flag'li denenebilir — ilk teslimatta değil.

### 3.2 Bellek-içi bar önbellekleme

Fraction nesneleri sabit-genişlikte olmadığı için `multiprocessing.shared_memory`'ye doğrudan konamaz. Gerçekçi yol: `ProcessPoolExecutor(initializer=...)` ile her worker, havuz başında **önceden parse edilmiş bir cache dosyasından** (pickle/msgpack) barları bir kez yükler ve süreç-global tutar — 500 parametre kombinasyonu aynı worker'da art arda koşacağı için disk/SQLite okuma maliyeti N kez değil, worker-sayısı kadar ödenir. Asıl darboğaz genelde bar-başına Fraction aritmetiği (döngü sayısı), veri yükleme değil — mühendislik karmaşıklığı `shared_memory`'ye değil, buraya yatırılmalı.

### 3.3 Orkestrasyon deseni — `backtrader`'dan ilham, reducer değişmeden

`backtesting.py` (vektörize, numpy/pandas — DCABOT'un reducer mimarisiyle uyumsuz) yerine `backtrader`'ın (event-driven, bar-bar, `Cerebro`/`optstrategy`/`OptReturn` — hafif, yalnız gerekli metrikleri taşıyan sonuç nesnesi) **orkestrasyon deseni** taklit edilmeye değer: parametre kombinasyonu üret → worker havuzuna dağıt → hafif Decimal-string özet sonuç döndür (tam bar-bar geçmiş değil, pickle maliyeti yüzünden). **DCABOT'un reducer'ının kendisi asla değişmemeli** — yalnız dış döngü.

### 3.4 Optimizer seçimi

4-6 parametreli (safety_qty, safety_count, deviation, step_multiplier, volume_multiplier), karma integer/sürekli uzayda **Optuna (TPE sampler)** en iyi uyum — grid search'ün %10-20'si denemeyle benzer sonuca ulaşabiliyor. Kritik mimari nokta: Optuna'nın **ask-and-tell arayüzü** (`study.ask()` → parametre al → DCABOT'un kendi reducer'ıyla çalıştır → `study.tell()`) kullanılırsa, Optuna yalnız "hangi kombinasyon denenecek" sampler'ı olur; **gerçek çalıştırma ve sonuç kaydı `trial_registry.py`'de kalır** (registry zaten yalnız `trial_id`+`status` tutuyor, ekonomik veri tutmuyor — bu ayrım kodda hazır). Optuna'nın kendi storage'ı (SQLite/RDB) **kullanılmaz** — source of truth her zaman DCABOT'un kendi registry'si. Mevcut `_MAX_TRIALS = 1_000` tavanı `study.ask()` çağrı sayısını sınırlamakla doğal olarak korunur.

---

## 4. Karar — istatistik katmanında float kullanılacak (kapalı, araştırıldı)

**Karar: (b) — `numpy`/`scipy` float64 kullanılacak, sıfırdan Fraction/Decimal yeniden yazımı YAPILMAYACAK.** Ayrı bir dış araştırmayla kapatıldı, aşağıda gerekçe ve zorunlu güvenlik sınırı var.

**Gerekçe:**
- Literatürde veya hiçbir referans implementasyonda (skfolio, mlfinlab, quantstats, PSR/DSR notebook'ları) float64'ün Sharpe/skewness/kurtosis/normal-CDF hesabında yetersiz kaldığına dair **tek bir belgelenmiş vaka yok**. Bunlar yüzlerce-binlerce trade üzerinde **tek seferlik** özet istatistikler — Fraction'ın koruduğu risk (milyonlarca sıralı defter işleminde birikimli yuvarlama sapması, borsa-eşleşmesi-kritik değerlerde donanımlar-arası tutarsızlık) burada oluşmuyor.
- **Somut emsal:** QuantConnect/LEAN (gerçek para ile emir yürüten üretim motoru) `Statistics.cs`'de tam bu ayrımı yapıyor — holdings/fill/cash/order miktarı `decimal`, ama `SharpeRatio`/`AnnualStandardDeviation`/skewness/kurtosis hesapları **tamamen `double`**; `decimal` girdi alan public metod bile içeride `double`'a çevirip hesaplayıp geri `decimal`'e cast ediyor. Bankacılık mimarisinde de aynı desen: "golden source" (defter) ayrı, risk/analiz motoru (VaR, Sharpe, stress) ayrı katman, float-tabanlı.
- `mpmath` (arbitrary-precision normal-CDF/erf) özel fonksiyon tarafındaki acıyı azaltır ama CPCV'nin kombinatoryal path enumerasyonu (ör. C(16,8)=12.870 path) numpy'sız 10-100x+ yavaş olur — kazanç, hiçbir yerde ihtiyaç duyulmamış bir kesinlik garantisi için gereksiz mühendislik maliyeti.

**Zorunlu güvenlik sınırı (bu kararın GÜVENLİ olmasını sağlayan tek şart):** float64, yalnız ayrı, açıkça adlandırılmış bir `dcabot/analytics/` (veya `overfitting_scoring.py` gibi) modülünde yaşayacak; bu modül **yalnızca** zaten Fraction/Decimal ile kesinleşmiş trade sonuçlarını kendi girdi sınırında float'a çevirip okuyacak, çıktısı yalnız danışma amaçlı skor/olasılık olacak — **hiçbir ledger, order, veya position-sizing kod yoluna asla geri yazılmayacak**. Bu sınır yorum değil, `ruff`/özel bir AST kontrolü veya bağımlılık-yönü testiyle (ör. "hiçbir order/ledger/sizing modülü `analytics`'ten import edemez") **zorunlu kılınmalı**.

Kaynak: ek araştırma oturumu (QuantConnect/LEAN kod incelemesi, Databricks finans-mimarisi referansı, mpmath teknik dokümantasyonu) — tam kaynak listesi bu belgenin sonunda "float-kararı ek kaynaklar" altında.

---

## 5. Matematik Kesinliği ve Bot Kalitesi — mevcut durum sağlam, küçük sertleştirmeler

Doğrulanan mevcut durum (`src/dcabot/domain/numbers.py`, `application/order_attempt.py`): iç hesap `Fraction`, `Decimal` sınırında `ROUND_HALF_EVEN` (banker's rounding — IEEE 754 ve çoğu borsa eşleştirme motoruyla tutarlı) + 1400 haneli precision context; `align`/`round_quantum` tick/step hizalaması; `OrderAttempt` durum makinesi (PREPARED→PERSISTED→SENDING→ACKNOWLEDGED/UNKNOWN/RECONCILING/REJECTED) crash-safe attempt ledger olarak zaten Hummingbot/Freqtrade seviyesinde bir tasarım. Bu alanda büyük bir boşluk yok; öneriler küçük ve isteğe bağlı:

- `evaluation_run_binding.py`'nin sağladığı canonical-hash zinciri, yeni CPCV/PBO sonuçlarını da aynı immutable-run-capture disiplinine bağlamalı (yeni bir "hesap türü" için ayrı bir kural seti icat etmeye gerek yok — mevcut desen genişletilsin).
- `trial_registry.py`'ye (yalnız `trial_id`+`status` tutuyor) parametre-hash'i eklenmesi — CSCV/DSR'nin "hangi konfigürasyon" sorusuna cevap vermesi için gerekli, ama ekonomik veri değil, yalnız kimlik alanı.

---

## 6. Önerilen yol haritası fazları (taslak — onay bekliyor)

**Faz 13 — TradingView sinyal entegrasyonu (webhook uçtan uca)**
1. Static-token doğrulamalı `POST /api/signals/webhook/tradingview` endpoint'i (mevcut `hash_signal_payload`'a bağlanır).
2. Durable dedup store (`AttemptStore`/`two_leg_journal.py` deseninde) — composite key `(kaynak+sembol+aksiyon+{{time}} veya strategy.order.id+fiyat)`.
3. Hızlı-ACK + async işleme (kabul kaydı → 200 → arka planda candidate-binding).
4. `verify_signal_signature`'ın (mevcut, test edilmiş) DCABOT'un kendi iç/relay istemcileri için korunması — TradingView ucundan ayrı.
5. Araştırma kutusu (opsiyonel, ayrı dilim): `pynecore` ile offline Pine-parity backtest denemesi.

**Faz 14 — İleri backtest: overfitting direnci ve ölçekleme**
1. ~~§4'teki float/Fraction kararı~~ — KAPALI: float64, izole `analytics/` modülünde (bkz. §4).
2. `embargo_window.py` (yeni primitif).
3. CPCV path üretici (N-grup/`C(N,k)`/path-reconstruction), `chronological_split.py`+`horizon_overlap.py`+yeni embargo'yu tüketir.
4. `overfitting_probability.py` (PBO/CSCV) ve DSR skorlayıcı, `trial_registry.py`'yi salt-okunur tüketir.
5. `ProcessPoolExecutor` + worker-initializer bar-cache orkestratörü (backtrader-esinli, reducer değişmeden).
6. Optuna ask-tell entegrasyonu (yalnız sampler; source of truth `trial_registry` kalır).

---

## Kaynaklar

**Float-kararı ek kaynaklar (§4):**
- [QuantConnect/Lean — Common/Statistics/Statistics.cs](https://github.com/QuantConnect/Lean/blob/master/Common/Statistics/Statistics.cs)
- [QuantConnect/Lean — Common/Statistics/PortfolioStatistics.cs](https://github.com/QuantConnect/Lean/blob/master/Common/Statistics/PortfolioStatistics.cs)
- [skfolio PR #255 — deflated_sharpe_ratio / expected_max_sharpe_ratio](https://github.com/skfolio/skfolio/pull/255)
- [mrbcuda/pbo — Probability of Backtest Overfitting (CSCV)](https://github.com/mrbcuda/pbo)
- [jarvisss007/backtest-overfitting — Deflated Sharpe, PBO, min backtest length](https://github.com/jarvisss007/backtest-overfitting)
- [mpmath — arbitrary-precision floating point](https://mpmath.org/)
- [mpmath — precision/representation issues](https://mpmath.org/doc/current/technical.html)
- [Databricks — Financial Services Investment Management Reference Architecture](https://www.databricks.com/resources/architectures/financial-services-investment-management-reference-architecture)
- [Architecting High Performance Financial Ledgers — Sagard](https://www.sagard.com/wp-content/uploads/2024/11/Sagard-Financial-Ledgers-v1c.pdf)

**CPCV/PBO/DSR:**
- [Purged cross-validation — Wikipedia](https://en.wikipedia.org/wiki/Purged_cross-validation)
- [Cross Validation in Finance: Purging, Embargoing, Combinatorial — QuantInsti](https://blog.quantinsti.com/cross-validation-embargo-purging-combinatorial/)
- [skfolio.model_selection.CombinatorialPurgedCV](https://skfolio.org/generated/skfolio.model_selection.CombinatorialPurgedCV.html)
- [skfolio: Portfolio Optimization in Python (arXiv)](https://arxiv.org/pdf/2507.04176)
- [GitHub — eslazarev/purged-cross-validation](https://github.com/eslazarev/purged-cross-validation)
- [GitHub — sam31415/timeseriescv](https://github.com/sam31415/timeseriescv)
- [The Probability of Backtest Overfitting — Bailey, Borwein, López de Prado, Zhu (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253)
- [PBO paper PDF](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)
- [pbo (CRAN) README](https://cran.r-project.org/web/packages/pbo/readme/README.html)
- [The Deflated Sharpe Ratio — Bailey & López de Prado (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551)
- [DSR paper PDF](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf)
- [Deflated Sharpe Ratio — Wikipedia](https://en.wikipedia.org/wiki/Deflated_Sharpe_ratio)
- [GitHub — rubenbriones/Probabilistic-Sharpe-Ratio](https://github.com/rubenbriones/Probabilistic-Sharpe-Ratio)
- [GitHub — hudson-and-thames/mlfinlab](https://github.com/hudson-and-thames/mlfinlab) (lisans: kapalı/ticari)
- [Re-Examining Technical Analysis with White's Reality Check](https://homepage.ntu.edu.tw/~ckuan/pdf/snoop01.pdf)
- [A Test for Superior Predictive Ability — Hansen](https://www.researchgate.net/publication/4724332_A_Test_for_Superior_Predictive_Ability)
- [quantstats/stats.py](https://github.com/ranaroussi/quantstats/blob/main/quantstats/stats.py)

**Ölçekleme / free-threading / optimizer:**
- [py-free-threading.github.io](https://py-free-threading.github.io/)
- [Python 3.13 What's New](https://docs.python.org/3/whatsnew/3.13.html)
- [FastAPI free-threading duyurusu (X/Twitter)](https://x.com/FastAPI/status/2044747877797319069)
- [GitHub — kernc/backtesting.py CHANGELOG](https://github.com/kernc/backtesting.py/blob/master/CHANGELOG.md)
- [backtesting.py optimization guide (SAMBO)](https://kernc-backtesting-py.mintlify.app/guides/optimization)
- [backtrader architecture overview](https://backtrader.readthedocs.io/en/latest/advanced/architecture/overview.html)
- [backtrader optimization improvements](https://www.backtrader.com/docu/optimization-improvements/)
- [Optuna efficient optimization algorithms](https://optuna.readthedocs.io/en/stable/tutorial/10_key_features/003_efficient_optimization_algorithms.html)
- [Optuna ask-and-tell interface](https://optuna.readthedocs.io/en/stable/tutorial/20_recipes/009_ask_and_tell.html)
- [On sharing large arrays with multiprocessing](https://research.wmz.ninja/articles/2018/03/on-sharing-large-arrays-when-using-pythons-multiprocessing.html)

**TradingView / Pine parity:**
- [TradingView — webhook alert kurulumu (resmi)](https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/)
- [TradingView — webhooks kullanım klasörü (resmi)](https://www.tradingview.com/support/folders/43000560150-webhooks-usage/)
- [GitHub — robswc/tradingview-webhooks-bot](https://github.com/robswc/tradingview-webhooks-bot) (durgun, ~1.5 yıl güncellenmemiş)
- [GitHub — vlameiras/tradingview-webhook-integration](https://github.com/vlameiras/tradingview-webhook-integration) (durgun, küçük)
- [GitHub — PyneSys/pynecore](https://github.com/PyneSys/pynecore) (aktif, Apache-2.0)
- [GitHub — LuxAlgo/PineTS](https://github.com/LuxAlgo/PineTS) (TS/JS, AGPL+ticari)
- [GitHub — be-thomas/OpenPineScript](https://github.com/be-thomas/OpenPineScript) (TS, yalnız Pine v1/v2)
- [pandas-ta-classic (PyPI)](https://pypi.org/project/pandas-ta-classic/)
- [Webhook idempotency — Activepieces](https://www.activepieces.com/blog/webhook-idempotency-how-to-handle-duplicate-events-2026)
- [Webhook idempotency & dedup — Hooklistener](https://www.hooklistener.com/learn/webhook-idempotency-and-deduplication)
