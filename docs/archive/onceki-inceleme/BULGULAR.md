# Kaynaklara bağlı bulgular

Commit: `318e1c409ff67083168b31fdd5a27fb28ec7d5f7` · 6 Eylül 2026. P0 = gerçek para/ilgili yetki öncesi kapanması gereken; P1 = ilgili özellik veya iddia düzeltilmeden ilerlenmemesi gereken konu. Dokuz hedefli kaynak probu çalıştırıldı; kalanlar statik inceleme/teknik kaynak doğrulamasıdır. Önceki girişimin neden başarısız olduğunu kesin belirleyen olay logları verilmedi; bunlar mevcut kaynakta bulunan sorunlardır.

**En güçlü öneri:** yeni özellik yerine D01 recovery ve D02 tek ekonomik kayıt yoluyla başlayın. Doğru araştırma metinleri var; asıl açık bunların runtime boyunca tek sözleşme olarak uygulanmaması.

## F01 — Likidasyon yaklaşık, “exact” değil

- Öncelik: P0/model. Kanıt: Çalıştırıldı.
- Kaynak: [src/dcabot/domain/liquidation.py · L8](https://github.com/ardaazmus/DCABOT/blob/318e1c409ff67083168b31fdd5a27fb28ec7d5f7/src/dcabot/domain/liquidation.py#L8).
- Bulgu: 100 giriş, 10x, MMR=.005 için 90.5 dönüyor. Aynı basit denklemin kökü 90/.995≈90.4522613. W, miktar, bracket/deduction ve mevcut collateral girdisi yok.
- Düzeltme: MATEMATIK M07: öğretici model etiketi; gerçek risk snapshot ayrı; D05b/A15.

## F02 — Önizleme ve replay farklı DCA

- Öncelik: P1/strateji. Kanıt: Çalıştırıldı + statik.
- Kaynak: [src/dcabot/replay/dca_strategy.py · L204](https://github.com/ardaazmus/DCABOT/blob/318e1c409ff67083168b31fdd5a27fb28ec7d5f7/src/dcabot/replay/dca_strategy.py#L204).
- Bulgu: Önizleme base anchor üzerinden kümülatif sapma; replay last_order_price üzerinden çarpım yapıyor ve SO niyetinde referansı bar.close ile değiştiriyor. Probda SO fill gelmeden sayaç 1 ve referans 90. placed sayacı kendi başına tamamlanma değildir; sorun bu değişkenlerin ekonomik seviye/referansı sürmesi ve ortak plan kullanılmaması.
- Düzeltme: MATEMATIK M02/M03, D03a/b: tek plan, plan/pending/filled ayrımı.

## F03 — Geçersiz fiyat uyduruluyor

- Öncelik: P1/matematik. Kanıt: Çalıştırıldı.
- Kaynak: [src/dcabot/domain/dca_math.py · L90](https://github.com/ardaazmus/DCABOT/blob/318e1c409ff67083168b31fdd5a27fb28ec7d5f7/src/dcabot/domain/dca_math.py#L90).
- Bulgu: 100 giriş, d=.6, n=2 planı ikinci fiyatta negatif yerine 1E-8 üretiyor. Ayrıca total_margin_required aslında toplam notional; kaldıraç/fee/bracket dönüşümü değil.
- Düzeltme: D03a/A10: config ret; MATEMATIK M03 alanlarını ayır.

## F04 — Kısmi çıkış doğru işlenmiyor

- Öncelik: P0/ekonomik çekirdek. Kanıt: Çalıştırıldı + statik.
- Kaynak: [src/dcabot/replay/dca_strategy.py · L107](https://github.com/ardaazmus/DCABOT/blob/318e1c409ff67083168b31fdd5a27fb28ec7d5f7/src/dcabot/replay/dca_strategy.py#L107).
- Bulgu: Pozisyon 1→.5 iken total_qty ve _last_position 1 kalıyor. Fill fiyatını bar.open üzerinden tahmin eden arayüz fiyat/fee/kimlik taşımaz. multi_tp_targets constructor tarafından saklanıyor, on_bar içinde kullanılmıyor. Mevcut full-fill market modelinin dar yolu bu eksikliği gizleyebilir.
- Düzeltme: D03c/D04: gerçek Execution girdisi ve ortak ledger; M04/A11.

## F05 — Çözülmemiş farkta yeni risk açılabiliyor

- Öncelik: P0/recovery. Kanıt: Çalıştırıldı.
- Kaynak: [src/dcabot/server/recovery.py · L109](https://github.com/ardaazmus/DCABOT/blob/318e1c409ff67083168b31fdd5a27fb28ec7d5f7/src/dcabot/server/recovery.py#L109).
- Bulgu: Yerel NEW emir, boş venue map: MARK_ORDER_CANCELLED_LOCALLY ve is_safe_to_resume=true. Boş local+venue map de CLEAN_COLD_START. Query coverage, pozisyon, bakiye veya unknown attempt kanıtı girdi değil.
- Düzeltme: D01/A06/A17: tipli scope, blockers ve allow_new_risk=false; düzeltme uygulanıp yeniden doğrulanmalı.

## F06 — Status farkı temiz sayılıyor

- Öncelik: P0/reconciliation. Kanıt: Çalıştırıldı.
- Kaynak: [src/dcabot/domain/reconciliation.py · L59](https://github.com/ardaazmus/DCABOT/blob/318e1c409ff67083168b31fdd5a27fb28ec7d5f7/src/dcabot/domain/reconciliation.py#L59).
- Bulgu: Yerel NEW ve venue CANCELED, filled qty ikisinde 0 olunca is_clean=true. Aynı order_id altında symbol/side/quantity/price farkları da mevcut dallarda tam karşılaştırılmıyor. Status değişimini execution sayan öneriler gerçek trade kimliği/fiyatını sağlamaz.
- Düzeltme: D01: farkları ayrı sınıfla; toplam filled qty üzerinden sahte fill üretme.

## F07 — Deal settlement idempotent değil

- Öncelik: P0/ledger. Kanıt: Çalıştırıldı.
- Kaynak: [src/dcabot/replay/multi_pair_orchestrator.py · L124](https://github.com/ardaazmus/DCABOT/blob/318e1c409ff67083168b31fdd5a27fb28ec7d5f7/src/dcabot/replay/multi_pair_orchestrator.py#L124).
- Bulgu: Başlangıç100; +20 settlement aynı parametrelerle iki kez çağrılınca equity140. API settlement kimliği kabul etmiyor; aşırı rezerv bırakma max(0,...) ile örtülüyor. Bu lokal sınıfın davranışıdır; tüm olası çağıranların duplicate korumasız olduğu iddia edilmez.
- Düzeltme: D02a/D05a: tek settlement/execution kimliği, unique posting, over-release ret.

## F08 — Başlangıca göre kayıp drawdown diye kullanılıyor

- Öncelik: P0/risk. Kanıt: Çalıştırıldı.
- Kaynak: [src/dcabot/replay/multi_pair_orchestrator.py · L145](https://github.com/ardaazmus/DCABOT/blob/318e1c409ff67083168b31fdd5a27fb28ec7d5f7/src/dcabot/replay/multi_pair_orchestrator.py#L145).
- Bulgu: 100→120→100 ve eşik .15: devre kesici false. Peak DD=1/6. Ayrıca sınıf equityyi yalnız settle_deal ile güncelliyor; kendi başına açık pozisyon/mark riskini izlemiyor. try_reserve_margin dictionary işlemi, dayanıklı DB atomikliği değil.
- Düzeltme: M06, D05a/A13: mark dahil equity, peak, ortak kalıcı rezerv.

## F09 — PID dosyası gerçek sahiplik kilidi değil

- Öncelik: P0/process. Kanıt: Çalıştırıldı + statik.
- Kaynak: [src/dcabot/server/daemon.py · L22](https://github.com/ardaazmus/DCABOT/blob/318e1c409ff67083168b31fdd5a27fb28ec7d5f7/src/dcabot/server/daemon.py#L22).
- Bulgu: Lock sahibi olmayan ikinci PidLock.release() ilk kilidi silebiliyor. acquire exists→write yarışı içeriyor; aynı PID tekrar kabulü var; ServerDaemon default pid=1001. Gerçek çok-process race bu teslimde çalıştırılmadı, statik risk olarak kaydedildi.
- Düzeltme: D06/A16: OS lock ve ownership; iki process kanıtı.

## F10 — LIMIT her zaman maker sayılıyor

- Öncelik: P1/maliyet. Kanıt: Statik.
- Kaynak: [src/dcabot/domain/fees.py · L41](https://github.com/ardaazmus/DCABOT/blob/318e1c409ff67083168b31fdd5a27fb28ec7d5f7/src/dcabot/domain/fees.py#L41).
- Bulgu: fee_for_fill tür=limit ise maker_bps seçiyor; FeeSchedule negatif oranı reddediyor. Pazarlanabilir limit taker olabilir; gerçek rol/ücret farklı alandır. Sadece varsayımsal simülasyon tarifesi ise bu kapsam açık etiketlenmeli.
- Düzeltme: M05/A12: role alanı, gerçek commission/asset; desteklenmeyen rebate açık scope. [Resmî trade alanları](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/trade).

## F11 — Basit fill modeli üretim doğruluğu değil

- Öncelik: P1/backtest. Kanıt: Statik.
- Kaynak: [src/dcabot/replay/runner.py · L106](https://github.com/ardaazmus/DCABOT/blob/318e1c409ff67083168b31fdd5a27fb28ec7d5f7/src/dcabot/replay/runner.py#L106).
- Bulgu: Limit touch bütün qtyyi limit fiyatında dolduruyor; queue/volume/partial fill yok. DCA TP high kontrolünden sonra market niyeti üretip sonraki open dolduruyor. Bu tek başına lookahead demek değildir; bar-close stratejisi olabilir. Ancak TP fiyatından satış veya intrabar TP/SL sırası doğrulanmış olmaz.
- Düzeltme: D04/D11/A22: model adı/varsayımı; aynı çekirdek, açık fiyat/zaman, belirsiz sıra politikası.

## F12 — Testnet harness ve Docker çalışma iddiası daraltılmalı

- Öncelik: P1/kanıt ve deployment. Kanıt: Statik.
- Kaynak: [tools/run_testnet_harness.py · L27](https://github.com/ardaazmus/DCABOT/blob/318e1c409ff67083168b31fdd5a27fb28ec7d5f7/tools/run_testnet_harness.py#L27).
- Bulgu: Yanıt ve WS fill sabit dictionary; signature_valid yalnız bool(signature); local/venue map aynı nesne; net_deal_pnl sabit24.96. order_placed=true gerçek ağ kanıtı değil. Docker CMD bu tek seferlik aracı çalıştırıyor; HEALTHCHECK sadece import. Sürekli gerçek bot döngüsü gösterilmiyor.
- Düzeltme: D06–D09: uzun yaşayan entrypoint, gerçek readiness; sentetik ve gerçek testnet ayrı kanıt.

## F13 — Güncel durum birçok yerde çelişiyor

- Öncelik: P1/doküman. Kanıt: Statik.
- Kaynak: [PLAN.md · L46](https://github.com/ardaazmus/DCABOT/blob/318e1c409ff67083168b31fdd5a27fb28ec7d5f7/PLAN.md#L46).
- Bulgu: PLAN genel bölüm414, U11 satırı447 test+17 E2E; PROJECT_CONTEXT390, aynı dosyada326. Review NOT_RUN iken “bağımsız doğrulandı” ve VERIFIED etiketleri de var. Bu sayılar geçmişte geçerli olabilir; ortak commit/scope olmadan güncel ürün durumu çıkarılamaz.
- Düzeltme: STATE tek güncel otorite; evidence scope/commit; geçmiş sayılar source archive.

## F14 — Decimal varlığı hassasiyet sözleşmesi değil

- Öncelik: P1/numerik. Kanıt: Statik.
- Kaynak: [src/dcabot/domain/numeric.py · L14](https://github.com/ardaazmus/DCABOT/blob/318e1c409ff67083168b31fdd5a27fb28ec7d5f7/src/dcabot/domain/numeric.py#L14).
- Bulgu: exact() MAX_PREC kullanıyor; bounded()28 ve rounding trap kapalı. Bazı finansal girişler finite/type/büyüklük kontrolünü tutarlı uygulamıyor. Sınırsız precision adı ve signed/string birlikteliği tek başına kaynak sınırı veya tam doğruluk sağlamaz.
- Düzeltme: M01: bounded input/scale, açık arithmetic context, residual; boundary/finiteness testleri. [Decimal](https://docs.python.org/3.13/library/decimal.html).

## F15 — Tek kullanımlık onay kalıcılık sınırında geri alınabilir

- Öncelik: P0/yetkili kullanım öncesi. Kanıt: Statik.
- Kaynak: [src/dcabot/persistence/store.py · L143](https://github.com/ardaazmus/DCABOT/blob/318e1c409ff67083168b31fdd5a27fb28ec7d5f7/src/dcabot/persistence/store.py#L143).
- Bulgu: save_approval mevcut satırı DELETE/INSERT ile gelen used alanından yeniden oluşturuyor. Eski Approval(used=false) save edilirse tüketim monotonluğu DB seviyesinde korunmuyor. Dış işlem yolunda sömürülebilirlik/caller akışı çalıştırılmadı.
- Düzeltme: D02/UoW ve yetkili işlem öncesi A19: atomik consume/CAS, stale save ret; onay+komut aynı transaction.

## F16 — Test ortamı adresi güncel belgeyle farklı

- Öncelik: P1/adapter güncellik. Kanıt: Statik + resmî belge.
- Kaynak: [src/dcabot/venue/binance_gateway.py · L84](https://github.com/ardaazmus/DCABOT/blob/318e1c409ff67083168b31fdd5a27fb28ec7d5f7/src/dcabot/venue/binance_gateway.py#L84).
- Bulgu: Gateway testnet.binancefuture.com sabitliyor. Güncel Binance General Info demo-fapi.binance.com gösteriyor. Eski adresin çalışmadığı denenmedi; URL farkı güncellik açığı. Constructor is_testnet parametresi base URL seçiminde fiilen kullanılmıyor.
- Düzeltme: D07: ürün/ortam manifesti; desteklenmeyen modu ret; S02 doğrulaması, gerçek ağ testi ayrı.

## F17 — Aktif paketler iç içe ve linkler yerleşime uymuyor

- Öncelik: P1/doküman akışı. Kanıt: Statik envanter.
- Kaynak: [docs/yeni/00_OKU_BENI.md · L15](https://github.com/ardaazmus/DCABOT/blob/318e1c409ff67083168b31fdd5a27fb28ec7d5f7/docs/yeni/00_OKU_BENI.md#L15).
- Bulgu: Bu index docs/research/01... yoluna yönlendiriyor fakat kendi konumuna göre hedef docs/yeni/docs/research/01... yok; dosya iç paket klasöründe. Aynı düzeltme/rehber/araştırma dosyalarının byte-identical kopyaları var. Ayrıntılı sayı ENVANTERde.
- Düzeltme: D00/GECIS: tek kanonik yerleşim, aktif link kontrolü, kopya yerine tarihçe.

## F18 — Import testi katman sınırını tam ölçmüyor

- Öncelik: P1/mimari kanıt. Kanıt: Statik.
- Kaynak: [tests/meta/test_ast_gates.py · L80](https://github.com/ardaazmus/DCABOT/blob/318e1c409ff67083168b31fdd5a27fb28ec7d5f7/tests/meta/test_ast_gates.py#L80).
- Bulgu: _imports_of yalnız üst modülü alıyor; dcabot görüldüğünde tüm iç importlar kabul ediliyor. Domain→persistence gibi ters yön kaçabilir. Buna karşılık tüm src içinde os/time yasağı gerçek runtime katmanını da saf olmaya zorluyor.
- Düzeltme: MIMARI: tam import yolu testi; domain saf, adapter I/O; AST whitelist fiziksel egress kanıtı değil.

## Korunması gerekenler

Exact Decimal/birim tipleri, offline varsayılanı, durum eksenlerini ayırma, execution kimliği, risk store revision kontrolleri, attempt-before-send, coverage ve immutable config yaklaşımı doğru başlangıç parçalarıdır. Bu inceleme tüm projeyi çöpe atmayı önermiyor. Uzun anonim finansal rapor M08/M09 ve V3 düzeltmelerinin önemli kısmı doğru kapsam sınırlamaları içeriyor.

## İnceleme sınırı

Tam pytest/lint/type/build/gerçek venue ve DB migration/restore süiti burada çalıştırılmadı. Python3.12 probu Python3.13 ürün sertifikasyonu değildir. Özel hesap/DB içerikleri incelenmedi; geçmiş başarı veya başarısızlık finansal sonuçları doğrulanmadı. Kaynak commit sabit; farklı HEADte önce tekrar kontrol gerekir.
