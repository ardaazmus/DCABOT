# Yol haritası — DEMO_FIRST_1

Öncelik: P1 tam demo → P2 Binance testnet → P3 Binance gerçek kurulum → P4 diğer borsalar. Eski N serisi tarihsel referanstır; aktif görev seçimi buradan yapılır. CORE01 kaynakları çalışır başlangıçtır, P1 bitmiş değildir.

## P1 — Arayüzlü demo ürün

Her satır küçük dikey davranıştır: ekran → application/çekirdek → kayıt/sonuç → odak test. Büyük başlıklar gerektiğinde .a/.b alt işlere bölünür; her oturumda tek iş vardır. Arayüz en baştan gelişir.

| ID | Kullanıcıya görünen teslim | Kabul |
|---|---|---|
| P1.01 | Bot kurulum ekranından mevcut çekirdeğin önizlemesini gör | Python API + form; 100 anchor için 90/80; invalid string/birim ret; no credential |
| P1.02 | CSV/ZIP seç, alanları eşleştir ve veri kalite raporu al | OHLCV/trade schema, UTC birimi, checksum/duplikasyon/gap; bozuk dosya sessiz kabul olmaz |
| P1.03 | Public arşivden geçmiş veriyi indir ve yerel katalogdan seç | İlerleme/iptal/retry/cache; internet yoksa yerel veri akışı sürer |
| P1.04 | Tarihsel veride ilk DCA koşusunu UI'dan başlat | Look-ahead yok; model açık; mark/funding eksikliği görünür; job progress |
| P1.05 | Sonucu grafikte, işlem tablosunda ve ekonomik dökümde incele | Realized/unrealized/fee/funding/equity aynı backend sonucundan |
| P1.06 | Koşuyu kaydet, uygulamayı yeniden aç, tekrar üret/karşılaştır | Dataset/config/model/kernel hash + seed; eski sonucu üzerine yazma yok |
| P1.07 | Simülatörde kısmi fill, iptal, limit/stop ve gecikme uygula | P1.07.a.1 core partial state + P1.07.a.2 opt-in fixed-slice runner + P1.07.a.3 public contract + P1.07.b fixed-slice UI + P1.07.c.1 fixed INDETERMINATE fail-closed authority + P1.07.c.2 guarded capability-aware committed prefix + P1.07.c.3 boundary-only marker + P1.07.d.1 explicit fixed-limit application policy + P1.07.d.3.a internal BASE-only reducer probe + d.3.b `reserve_model=NONE` sınır kararı + d.3.c NONE acceptance testleri + d.2.b explicit-fixture BASE-bound public limit contract `COMPLETE_WITH_LIMITATION` olarak tamamlandı; bağımsız review, explicit reserve ledger, SAFETY/EXIT binding, incomplete persistence, volume/latency/queue/stop ve aynı-bar cancel-fill yarışı hâlâ PLAN/ayrı araştırma kapısı |
| P1.08 | Botu birkaç deal boyunca çalıştır, duraklat/bitir/kopyala | P1.08.a saf lifecycle authority, P1.08.b in-memory COPY sınırı, P1.08.c store inventory, P1.08.d event identity, P1.08.e transition adapter, P1.08.f ayrı persistent record boundary, P1.08.g config snapshot/hash binding, P1.08.h terminal/cooldown policy ve P1.08.i pause-order policy `COMPLETE_WITH_LIMITATION`; API/UI ve shared-account isolation PLAN |
| P1.09 | Gelişmiş DCA/sizing ve risk formunu tamamla | P1.09.a exact BASE/QUOTE candidate, P1.09.b exact ladder conservation, P1.09.c profile-bound instrument filter validation, P1.09.d tagged eligible-balance percent budget, P1.09.e exact ladder binding, P1.09.f realized-profit reinvestment projection, P1.09.g quote-unit pre-acceptance gate, P1.09.h bağımsız exact/metamorphic oracle ve P1.09.i BASE candidate quote commitment binding `COMPLETE_WITH_LIMITATION`; balance conversion, quantization, hacim/indikatör koşulları ve UI PLAN |
| P1.10 | Terminalde çoklu TP, SL, trailing ve breakeven simüle et | P1.10.a exit trigger/execution, P1.10.b multi-TP exact quantity conservation, P1.10.c stop trigger/execution, P1.10.d long trailing ratchet, P1.10.e trailing-exit capacity binding, P1.10.g short sabit-mesafeli, P1.10.h long/short percentage trailing ve P1.10.i ortak trailing exit-boundary `COMPLETE_WITH_LIMITATION`; P1.10.f fee-aware breakeven, P1.10.j OCO/cancel-replace/late-fill ve P1.10.k public/API/UI `DEFERRED/NO-GO` (fee-asset, cancellation confirmation, replacement identity, reserve, public state ve görsel sözleşmeler eksik) |
| P1.11 | Çoklu bot/pair'i ortak sanal hesapta yönet | P1.11.a ownership/isolation `DEFERRED/NO-GO`; P1.11.b immutable identity, P1.11.c pure capacity/version projection ve P1.11.d dedicated SQLite reservation persistence/version boundary `COMPLETE_WITH_LIMITATION`; P1.11.e fill/release + existing Store binding `DEFERRED/NO-GO` çünkü owner/event/unit/transaction sözleşmesi eksik; combined dedup/replay ve UI double-counting PLAN |
| P1.12 | Spot ile lineer futures long/short ürün modellerini tamamla | P1.12.a explicit contract-size/settlement linear UPL + timestamped funding projection, P1.12.b partial-close/gross PnL ve P1.12.c immutable fee/funding event projection `COMPLETE_WITH_LIMITATION`; P1.12.d persistent Store replay/idempotency binding `DEFERRED/NO-GO`; P1.12.e isolated margin/profile gate `DEFERRED/NO-GO`; margin/liquidation/cross/isolated numeric behavior profile bekliyor |
| P1.13 | Grid, trailing/reverse/infinity grid ve dönemsel alım ailelerini simüle et | P1.13.a exact aritmetik level generation + P1.13.b accepted-fill inventory projection `COMPLETE_WITH_LIMITATION`; P1.13.c fee/cycle-profit/equity `DEFERRED/NO-GO`; P1.13.d geometric precision/quantization `DEFERRED/NO-GO`; P1.13.e grid trailing-up/down ve reverse/infinity `DEFERRED/NO-GO`; replacement, leveraged ve dönemsel alım `PLAN`; her varyant ayrı davranış |
| P1.14 | Rebalancing, signal ve strategy template akışları | P1.14.a exact rebalancing target/delta projection + P1.14.b immutable signal identity/event-time/dedupe + P1.14.c warmup/closed-bar/stale readiness + P1.14.d threshold/time trigger + P1.14.e template integrity/non-authority + P1.14.f activation/capability gate `COMPLETE_WITH_LIMITATION`; actual activation transition, conversion/order sizing, profile binding, persistence, API ve UI `PLAN`; her sınır ayrı davranış |
| P1.15 | Genişletilmiş futures/hedge/cross ve çift bacaklı model gereksinimleri | P1.15.a hedge/net identity ve explicit two-leg intermediate state + P1.15.b aynı scope HEDGE LONG/SHORT accepted-fill projection `COMPLETE_WITH_LIMITATION`; P1.15.c persistence/replay/recovery `DEFERRED/NO-GO` çünkü mevcut lifecycle Store non-economic, generic Store two-leg/recovery lineage taşımıyor ve atomic binding kanıtlanmadı; cross ownership, reduce-only, liquidation, margin ve venue profile `PLAN/DEFERRED`; risk sözleşmeleri tamamlanmadan sahte arbitraj/liq sonucu yok |
| P1.16 | Parametre kıyası, OOS/walk-forward ve stres çalışma alanı | P1.16.a chronological boundary + P1.16.b OOS freeze/touched lineage + P1.16.c feature/label overlap gate + P1.16.d bounded trial registry + P1.16.e ayrı stress lineage/result identity + P1.16.h bounded persisted trial/stress/OOS metadata binding `COMPLETE_WITH_LIMITATION`; P1.16.f warmup/readiness binding ve P1.16.g local feature/label horizon/real-run pipeline `DEFERRED/NO-GO`; P1.16.i.a authority/evidence inventory `COMPLETE_WITH_LIMITATION`; P1.16.i.b research audit `COMPLETE_WITH_LIMITATION`, ekonomik implementation `DEFERRED/NO-GO`; P1.16.i.c deterministic identity `COMPLETE_WITH_LIMITATION`, ekonomik scenario identity `DEFERRED/NO-GO`; P1.16.i.d persistence/replay/recovery `COMPLETE_WITH_LIMITATION`, stress persistence/branch/atomicity `DEFERRED/NO-GO`; P1.16.i.e `COMPLETE_WITH_LIMITATION/NO-GO`; ekonomik stress runner açılmaz |

## Kanıt gerektiren fazların yürütme standardı

Bir iddia veya öneri mevcut kod/fixture ile doğrudan kanıtlanamıyorsa bu durum plansız bekleme olarak bırakılmaz; ilgili ana fazın altında numaralı bir kanıt alt fazı açılır. Alt faz sırası şöyledir:

1. **Kapsam ve sahiplik envanteri:** İddianın hangi davranışa, asset/unit’e, zaman türüne, state transition’a, API’ye veya persistence sahibine ait olduğu yazılır.
2. **Yerel kanıt kontrolü:** Aktif kaynak, test, fixture, schema ve mevcut evidence incelenir; yedek/archive delil sayılmaz.
3. **RED veya karşı örnek:** İddia mevcut değilse bunu gösteren sınırlı test/probe yazılır; mevcutsa sınır ve yanlış-pozitif davranış test edilir.
4. **Bağımsız kontrol:** Production kodunu tekrar kullanmayan hesap, transition tablosu, canonical hash, replay veya field-level oracle ile sonuç karşılaştırılır.
5. **Minimum uygulama kararı:** Yalnız iddia doğrulanmış ve sahiplik netse en küçük dikey değişiklik yapılır. Kanıt yetersizse `DEFERRED / NO-GO` yazılır; varsayımsal ekonomik/API/UI/persistence davranışı eklenmez.
6. **Kapanış:** Odak regresyon, tam regresyon, compile, workspace, güvenlik/veri sızıntısı kontrolü ve evidence kaydı tamamlanır; `STATE.md`, `TASK.md`, roadmap ve özellik matrisi aynı sonucu taşır.

Her alt faz için yalnız bir durum `ACTIVE` olabilir. Dış araştırma, yalnız yerel kontrolde cevaplanamayan ve uygulama kararını gerçekten değiştirecek açık iddia kaldığında istenir; prompt ilgili alt fazın kapsamını, anonimleştirme sınırını, beklenen kanıt formatını ve kabul/red ölçütünü içermelidir.

### P1.16.i kanıt alt fazları

| Alt faz | Durum | Çıkış kapısı |
|---|---|---|
| P1.16.i.a — Core/store authority ve mevcut scenario inventory | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | `evidence/P1.16.i/SONUC.md` ile mevcut sahiplik ve eksik davranışlar kayda alındı |
| P1.16.i.b — Exact stress economic contract | `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED` | Rapor denetlendi; T-07/T-12 ve reserve oracle karşı örnekleri nedeniyle ekonomik implementation `DEFERRED/NO-GO` |
| P1.16.i.c — Deterministic scenario/result identity | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | Mevcut lineage/hash/base-stress bağının bağımsız kontrolü geçti; ekonomik scenario/seed genişletmesi `DEFERRED/NO-GO` |
| P1.16.i.d — Persistence/replay/recovery | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | Base Store transaction/replay/rollback ve HistoricalRunStore snapshot checksum/idempotency sınırları doğrulandı; stress event/branch/cross-store atomicity/economic recovery kanıtı yok. Kanıt: `evidence/P1.16.i.d/SONUC.md` |
| P1.16.i.e — Minimum dikey uygulama ve dış yüzey | `COMPLETE_WITH_LIMITATION / NO-GO` | P1.16.i kanıt zinciri birleştirildi; ekonomik stress runner, yeni schema/adapter, API ve UI açılmadı. Kanıt: `evidence/P1.16.i.e/SONUC.md` |

`P1.16.i.b` araştırma teslimi: `docs/P1.16.i.b_Stress_Ekonomik_Sozlesme_Arastirma_Promptu.md`.

### P1.17.a kanıt alt fazı

| Alt faz | Durum | Çıkış kapısı |
|---|---|---|
| P1.17.a — Public read-only data authority inventory | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | Historical public download/cache authority’si doğrulandı; canlı feed bulunmadı. Kanıt: `evidence/P1.17.a/SONUC.md` |
| P1.17.b — Public read-only feed contract research gate | `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED` | Resmi public feed, event/time ve gap/stale/reconnect sınırı araştırıldı; local RED→GREEN doğrulandı. REST/catch-up/venue-specific reconnect ve canlı adapter production için açık. Kanıt: `evidence/P1.17.b/SONUC.md` |
| P1.17.c — Offline observation replay adapter | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | Normalize edilmiş observation yalnız local bounded replay ile feed cursor’a verildi; network, API/UI, persistence ve economic fill yok. Kanıt: `evidence/P1.17.c/SONUC.md` |
| P1.17.d — Venue-specific transport mapping and reconnect/catch-up research gate | `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED` | Binance Spot public profile resmi güncel REST/WS kaynaklarıyla denetlendi; heartbeat/limit/timestamp düzeltmeleri, `t/a` identity-vs-sequence ayrımı ve reconnect/catch-up sınırı kayda alındı. Kanıt: `evidence/P1.17.d/SONUC.md` |
| P1.17.e — Binance public payload normalization (network-free) | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | Trade/aggTrade fixture normalize edildi; explicit unit/scope/identity ve `source_sequence=None` fail-closed doğrulandı. Kanıt: `evidence/P1.17.e/SONUC.md` |
| P1.17.f — Binance normalized observation → local replay binding (network-free) | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | Normalize edilmiş observation mevcut bounded replay cursor’ına bağlandı; stream scope, duplicate/conflict, event-time ve `source_sequence=None` doğrulandı. Kanıt: `evidence/P1.17.f/SONUC.md` |
| P1.17.g — Binance public profile acceptance matrix (network-free) | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | 8 parser + 4 replay hücresinde mapping, unit mismatch, malformed/scope, duplicate/conflict, event-time ve economic-boundary no-op doğrulandı; timestamp guard RED→GREEN düzeltildi. Kanıt: `evidence/P1.17.g/SONUC.md` |
| P1.17.h — Binance REST public payload normalization (network-free) | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | `/api/v3/trades` ve `/api/v3/aggTrades` decoded fixture mapping’i, `REST` transport, REST zaman/identity alanları ve WS/stream ayrımı doğrulandı. Kanıt: `evidence/P1.17.h/SONUC.md` |
| P1.17.i — Binance public observation capability boundary (network-free) | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | REST/WS observation yalnız read-only/replay tiplerinde kaldı; untrusted economic alan izolasyonu ve AST import graph kontrolü geçti. Kanıt: `evidence/P1.17.i/SONUC.md` |
| P1.17.j — Binance public transport activation readiness gate (network-free) | `DEFERRED / NO-GO / LOCAL_PASS` | Venue kanıtı ve local önkoşul kontrolü canlı activation için yeterli olmadı; entrypoint, reconnect worker, tam catch-up ve live persistence yok. Kanıt: `evidence/P1.17.j/SONUC.md` |
| P1.17 | Public canlı fiyatla sanal işlem çalıştır | P1.17.a–i public authority/feed/replay/venue research, ağsız WS/REST normalization ve capability sınırları tamamlandı; j activation gate `NO-GO/DEFERRED`; private credential/gerçek emir yok; canlı REST/WS adapter ve simulated execution hâlâ PLAN |
| P1.18.a — Offline rule-based read-only event explanation projection | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | Mevcut tarihsel/public observation ve sonuçlardan bounded read-only açıklama projection’ı; `4/4` odak, `359/359` regresyon, compile/workspace PASS. Kanıt: `evidence/P1.18.a/SONUC.md` |
| P1.18.b — Read-only explanation response binding karar kapısı | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | İki historical API response’una bounded strict explanation alanı bağlandı; fixed-slice status uyarlaması, persistence ayrımı ve frontend type-only sınırı doğrulandı. `359/359` regresyon, compile/workspace/frontend build PASS. Kanıt: `evidence/P1.18.b/SONUC.md` |
| P1.18.c — Read-only explanation UI/UX research gate | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | Teslim edilen UI/UX araştırması gerçek result ekranıyla karşılaştırıldı; `ExplanationSection` completed/indeterminate akışlarına bağlandı, severity ve native technical disclosure eklendi. `359/359` regresyon, compile/workspace/frontend build PASS; Browser visual QA çalışmadı. Kanıt: `evidence/P1.18.c/SONUC.md` |
| P1.18.d — Read-only explanation visual/accessibility QA | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | Chrome CDP fallback’i ile 1280/390/320px render, 8 açıklama/8 kart, mobil yatay taşmama ve native disclosure Space etkileşimi doğrulandı; NVDA/JAWS çalıştırılmadı. Kanıt: `evidence/P1.18.d/SONUC.md` |
| P1.19.a — Result shell responsive state acceptance | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | Idle/empty, loading, error ve completed local UI durumları doğrulandı; legacy `summary` response shape için minimum read-only fallback eklendi, fixed-slice akışı korundu. İndeterminate UI screenshot’ı bu dilimde alınmadı. Kanıt: `evidence/P1.19.a/SONUC.md` |
| P1.19.b — Existing result-shell responsive/theme inventory | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | Mevcut 1080/720/380px breakpoint’ler, 320/390px taşmama kanıtı, koyu tema, token yokluğu, kısmi focus ve empty/loading/error durumları envanterlendi; kod değişmedi. NVDA/JAWS etkileşimli QA ortam sınırı nedeniyle çalıştırılmadı. Kanıt: `evidence/P1.19.b/SONUC.md` |
| P1.19.c — Theme/focus implementation decision gate | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | Araştırma kararı bağımsız local kontrolle denetlendi; mevcut dark palette’den sınırlı tokenlar, ortak `:focus-visible` ve 768px taşma düzeltmesi uygulandı. Light theme, backend/economic/network/persistence/LLM yok. `359/359` regresyon, compile/workspace/frontend build ve responsive/focus smoke PASS; NVDA/JAWS NOT_RUN. Kanıt: `evidence/P1.19.c/SONUC.md` |
| P1.19.d — Screen-reader/high-contrast accessibility QA gate | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | Chrome CDP ile gerçek local DOM/AX tree, 320/390/768/1024/1280px taşmama, 18 focus durağı, native disclosure, forced-colors emülasyonu ve temiz uygulama konsolu doğrulandı. NVDA/JAWS ve gerçek Windows HCM `NOT_RUN`; favicon 404 düzeltildi. Kanıt: `evidence/P1.19.d/SONUC.md` |
| P1.19.e — Light theme / uzman görünüm karar kapısı | `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED` | Sağlanan rapor gerçek checkout ile denetlendi; okunmamış dosya/palette iddiaları reddedildi. Gerçek response contract, token/focus/responsive durumu doğrulandı; seçilmiş contrast oracle 11 PASS/1 border FAIL verdi. Light theme ve uzman görünüm DEFER; NVDA/JAWS ve gerçek HCM NOT_RUN. Kanıt: `evidence/P1.19.e/SONUC.md` |
| P1.19.f — Exact token/palette ve safe detailed-view implementation gate | `DEFERRED / NO-GO / LOCAL_PASS` | Gerçek token/renk kapsamı ve seçilmiş contrast oracle ölçüldü: 11 PASS/1 border FAIL. Yeni light theme/toggle/persistence veya expert mode açılmadı; mevcut native disclosure minimum detailed-view olarak kabul edildi. Exact light palette ve ürün/default kararı bekleniyor. Kanıt: `evidence/P1.19.f/SONUC.md` |
| P1.20 — Tam demo kabulü ve bağımsız inceleme | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | Verified sabit artifact ile dataset → profile/run plan → onay → simülasyon → grafik/ekonomi/açıklama → save → Saved Runs list/detail uçtan uca geçti. 1280/390px görsel kanıt, 320/390/768/1024/1280px responsive kontrol, `359/359` regresyon, Python 3.13 compile/workspace ve frontend build PASS. NVDA/JAWS ve gerçek Windows HCM NOT_RUN; production readiness `NO`. Kanıt: `evidence/P1.20/SONUC.md` |
| P1.18 | Açıklayıcı asistan, olay/bildirim merkezi, şablon paylaşımı | Kural tabanlı açıklama offline; isteğe bağlı LLM; onaysız parametre/emir değişimi yok |
| P1.19 | Kullanıcı deneyimi, kurulum ve erişilebilirlik tamamla | Responsive/açık-koyu/basit-uzman; empty/loading/error; offline bundle; Windows başlangıcı |
| P1.20 | Tam demo kabulü ve bağımsız inceleme | Özellik matrisi P1 kapıları, aşağıdaki kontrol; kritik açık yok |

P1.12, spot/grid gibi ona bağımlı davranışlardan önce tamamlanır. P1.15'te gereken kapsam, özellik matrisindeki özel ürün keşfiyle ayrıntılanır; çözümlenmemiş kritik özellik varken tam eşdeğerlik iddia edilmez. Bu geniş hedef tek kısa oturum değildir; teslimler küçük kalır, nihai P1 kapsamı küçültülmez.

### P1 kabul kapısı

- Veri yükle/indir → strateji kur → çalıştır → grafik/ekonomi incele → kaydet → yeniden aç akışı uçtan uca geçer.
- [Özellik matrisi](OZELLIK_MATRISI.md) her gereksinim için UI, çekirdek, veri/model ve test kanıtı taşır. P1 zorunlularında placeholder veya tanımsız hesap yoktur.
- Min. bir gerçek tarihsel dataset, sabit hash ile çevrimdışı tekrar üretilebilir. İndirici ağ hatası mevcut koşuyu bozmaz.
- Güncel fiyat/filtreyi geçmişe uygulama, future candle bilgisi veya varsayılan sıfır funding gibi gizli varsayımlar yoktur.
- Testnet/live entegrasyonu P1 başarısı için gerekmez. Public online erişim elverişsizse sağlanan dosyayla demo çalışır; indirici otomatik test/failure kanıtı ayrı tutulur.
- Bağımsız Codex incelemesi; UX ve Windows E2E; hesap ve veri kabulü. Eski 38 çekirdek testi bu kapının tamamı değildir.

## P2 — Binance testnet

| ID | Teslim | Kabul |
|---|---|---|
| P2.01 | Connection wizard, ürün/izin/filter snapshot | P2.01 araştırma kapısı `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED`; testnet endpoint, `/api`-only sınırı ve snapshot ayrımı kanıtlandı. Güvenli credential injection, signed account runtime ve UI implementasyonu `DEFERRED`; trading activation `NO-GO`. Kanıt: `evidence/P2.01/SONUC.md` |
| P2.01.a | Public testnet connectivity + exchangeInfo snapshot | `COMPLETE_WITH_LIMITATION / LOCAL_PASS`: Gerçek kimliksiz `GET /api/v3/exchangeInfo?symbol=BTCUSDT` ve local read-only `/api/venue-snapshots/binance-spot-testnet` endpoint’i; fixed testnet base, bounded UTF-8 symbol/query, 256 KiB response sınırı, hash, symbol/filter/rate-limit snapshot, `7/7` odak ve `366/366` regresyon PASS. Account/order/WebSocket/persistence/UI wizard açılmadı. Kanıt: `evidence/P2.01.a/SONUC.md` |
| P2.01.b | Public snapshot’ın UI’da salt-okunur gösterimi | `IMPLEMENTED_WITH_LIMITATION / READY_WITH_LIMITATION`: React kartı `CONNECTED_READ_ONLY`/loading/`FAILED`, status, permissionSets, order types, rate-limit/filter/hash disclosure ve kalıcı public/account sınırıyla gösteriyor; frontend hesaplama, secret ve order yolu yok. Rendered browser QA, güncel local runtime yeniden başlatılana kadar `NOT_RUN`. Kanıt: `evidence/P2.01.b/SONUC.md` |
| P2.02 | Kalıcı attempt/outbox sender ve account rezervini gerçek sınırda doğrula | İlk offline attempt/outbox, P2.02.a signer/time ve P2.02.b ephemeral credential/capability sınırı `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; gerçek Windows provider, signed account, reconciliation ve mutation `IN_PROGRESS/DEFERRED/NO-GO`. Kanıt: `evidence/P2.02/SONUC.md` |
| P2.03 | Plain/conditional/koruyucu emir yaşamını test et | Accept/fill/cancel/late/partial/reduce-only; gerçek scope |
| P2.04 | Restart, WS/REST reconciliation ve operasyon kontrolleri | P2.04.a ve P2.04.b offline Fake WebSocket/Fake REST state machine `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; reconnect `SYNCED` değildir, UNKNOWN/GAP/STALE/reset fail-closed ve REST/stream disagreement kanıtlandı. Gerçek Binance User Data Stream, signed REST, reset sonrası canlı recovery ve tam lifecycle hâlâ `RESEARCH_REQUIRED/DEFERRED`; P2.04.c contract denetimi sıradaki adımdır. Kanıt: `evidence/P2.02/SONUC.md` |
| P2.05 | UI'dan Binance testnet kabul kampanyası | P1'deki desteklenen özellikler trace edilir; gerçek örnek ve otomatik kanıt |

Testnet erişimi olmayan venue yeteneği gerçek testten geçmiş sayılmaz. Desteklenmeyen ürün/mode canlıya taşınmaz; bağlayıcı user kararı ve capability kaydı gerekir.

## P3 — Gerçek Binance kurulum

P3.01 dağıtım/başlangıç/upgrade/backup/restore, worker sahipliği ve gözlemleme; P3.02 read-only gerçek hesap karşılaştırması; P3.03 açık yetkili düşük limitli canary; P3.04 sürdürülebilir işletim ve doğrulanmış özellikleri kademeli açma. Withdraw/transfer yetkisi başlangıç gereksinimi değildir. P2 kanıtı P3'teki kullanıcı para yetkisinin yerine geçmez.

## P4 — Diğer borsalar

İstenen her borsa için: resmi API/capability → ayrı adapter → simulator contract test → sandbox varsa entegrasyon → read-only doğrulama → açık yetkili canary. Binance enum/ID/fee/filter/precision/account modeli evrensel kabul edilmez. Venue seçimi UI'ı veya çekirdeği kopyalamaz; destek farklarını gösterir.
