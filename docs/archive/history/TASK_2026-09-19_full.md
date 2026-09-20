# DCABOT Task History

# Current task status — 2026-09-19

- 2026-09-19 P2.04 post-gap mixed cursor repeated conflict stale old anchor
  final replay parity `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`: transaction-
  forward `(211,199)` ve event-forward `(209,211)` recovery anchor’larından
  sonra tekrarlı fingerprint conflict ile `GAP` açıldı; tuple sırasına göre
  eski mixed-component anchor’lar `(210,212)` ve `(208,212)`
  `RESYNC_ANCHOR_STALE` kaldı. Aynı terminal boundary anchor yeniden kabul
  edildi; `SNAPSHOT_STALE` → `SYNCED`, exact replay `DUPLICATE`, eski
  recovery/conflict/anchor event’leri `QUARANTINED`, boş SQLite journal
  değişmedi. Odak 1/1, komşu 90/90, tam checker 865/865 PASS; compileall,
  workspace (296 aktif Python dosyası) ve diff check PASS. Kanıt
  `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`; sıradaki tek güvenli iş
  stale mixed-anchor reddinden sonra güncel cursor’ın snapshot retry ve final
  replay boyunca korunması regresyonudur.

- 2026-09-19 P2.04 post-gap mixed cursor repeated conflict stale old anchor
  final replay parity `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`:
  transaction-forward `(211,199)` ve event-forward `(209,211)` recovery
  anchor’larından sonra tekrarlı fingerprint conflict ile `GAP` açıldı; tuple
  sırasına göre eski mixed-component anchor’lar `(210,212)` ve `(208,212)`
  `RESYNC_ANCHOR_STALE` kaldı. Aynı terminal boundary anchor’ı yeniden kabul
  edildi; eşik altı `SNAPSHOT_STALE`, eşik snapshot `SYNCED`, exact replay
  `DUPLICATE`, eski recovery/conflict/anchor event’leri `QUARANTINED`, boş
  SQLite journal değişmedi. Odak 1/1, komşu 90/90, tam checker 865/865 PASS.
  Compileall, workspace (296 aktif Python dosyası) ve diff check PASS. Kanıt
  `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`; sıradaki tek
  asistan-owned güvenli iş stale mixed-anchor reddinden sonra güncel cursor’ın
  yeni snapshot retry ve final replay boyunca korunması regresyonudur.

- 2026-09-19 P2.04 post-gap mixed cursor forward terminal repeated
  fingerprint conflict re-entry freshness ve quarantine parity
  `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`: transaction-forward `(212,211)`
  ve event-forward `(211,212)` akışlarında aynı forward boundary’de tekrarlı
  fingerprint conflict `CONFLICT/GAP`, aynı boundary terminal recovery anchor,
  eşik altı `SNAPSHOT_STALE`, eşik snapshot `SYNCED`, exact replay `DUPLICATE`,
  eski conflict/re-entry/terminal/replacement event’leri `QUARANTINED`, boş
  SQLite journal değişmiyor. Odak 1/1, komşu 89/89, tam checker 864/864 PASS.
  Compileall, workspace (296 aktif Python dosyası) ve diff check PASS. Kanıt
  `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`; sıradaki tek
  asistan-owned güvenli iş tekrarlı conflict sonrası eski mixed-component anchor
  monotonicity ve final replay parity regresyonudur.

- 2026-09-19 P2.04 post-gap mixed cursor forward terminal repeated
  fingerprint conflict re-entry freshness ve quarantine parity
  `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`: transaction-forward `(212,211)`
  ve event-forward `(211,212)` akışlarında aynı forward boundary’de tekrarlı
  fingerprint conflict `CONFLICT/GAP`, aynı boundary terminal recovery anchor,
  eşik altı `SNAPSHOT_STALE`, eşik snapshot `SYNCED`, exact replay `DUPLICATE`,
  eski conflict/re-entry/terminal/replacement event’leri `QUARANTINED`, boş
  SQLite journal değişmiyor. Odak 1/1, komşu 89/89, tam checker 864/864 PASS.
  Compileall, workspace (296 aktif Python dosyası) ve diff check PASS. Kanıt
  `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`; sıradaki tek
  asistan-owned güvenli iş tekrarlı conflict sonrası eski mixed-component anchor
  monotonicity ve final replay parity regresyonudur.

- 2026-09-19 P2.04 post-gap mixed cursor forward terminal equal-cursor
  re-entry freshness ve stale-event quarantine parity `IMPLEMENTED_WITH_LIMITATION /
  LOCAL_PASS`: transaction-forward `(212,211)` ve event-forward `(211,212)`
  terminal anchor’larından sonra aynı cursor’lı re-entry conflict, eşit terminal
  anchor re-entry, eşik altı `SNAPSHOT_STALE`, eşik snapshot `SYNCED`, terminal
  exact replay `DUPLICATE`, önceki re-entry/terminal/replacement event’leri
  `QUARANTINED`, boş SQLite journal değişmiyor. Odak 1/1, komşu 89/89, tam
  checker 864/864 PASS. Compileall, workspace (296 aktif Python dosyası) ve
  diff check PASS. Kanıt `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`;
  sıradaki tek asistan-owned güvenli iş aynı forward boundary’de tekrarlı
  fingerprint conflict sonrası re-entry freshness ve quarantine parity
  regresyonudur.

- 2026-09-19 P2.04 post-gap mixed cursor forward terminal duplicate
  quarantine parity `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`: transaction-forward
  `(212,211)` ve event-forward `(211,212)` terminal anchor’larında eşik altı
  snapshot `SNAPSHOT_STALE`, eşik snapshot `SYNCED`, terminal exact replay
  `DUPLICATE`, önceki recovery/re-entry/replacement event’leri `QUARANTINED`,
  boş SQLite journal değişmiyor. Odak 1/1, komşu 88/88, tam checker 863/863
  PASS. Compileall, workspace (296 aktif Python dosyası) ve diff check PASS.
  Kanıt `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`; sıradaki tek
  asistan-owned güvenli iş forward terminal anchor sonrası equal-cursor re-entry
  freshness ve stale-event quarantine parity regresyonudur.

- 2026-09-19 P2.04 post-gap mixed cursor equal re-entry terminal snapshot
  parity `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`: eşit terminal anchor
  re-entry sonrasında yeniden kabul ediliyor; `210` snapshot `SNAPSHOT_STALE`,
  `211` snapshot `SYNCED`. Aynı `max(cursor)=211` değerine sahip fakat tuple
  sırasına göre eski cross-component anchor `(209,211)`, mevcut `(211,199)`
  anchor’ı geriye alamıyor ve `RESYNC_ANCHOR_STALE` ile kapanıyor; gerçek ileri
  `(212,211)` anchor kabul ediliyor, `211` snapshot stale ve `212` snapshot fresh.
  Final recovery exact replay `DUPLICATE`, eski/re-entry event `QUARANTINED`,
  boş SQLite journal değişmiyor. Odak 1/1, komşu 87/87, tam checker 862/862
  PASS. Compileall, workspace (296 aktif Python dosyası) ve diff check PASS.
  Kanıt `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`; sıradaki tek
  asistan-owned güvenli iş post-gap mixed cursor forward anchor sonrası terminal
  duplicate ve stale-event quarantine parity regresyonudur.

- 2026-09-19 P2.04 post-gap repeated replacement anchor equal-boundary
  freshness ve duplicate quarantine parity `IMPLEMENTED_WITH_LIMITATION /
  LOCAL_PASS`: tekrarlı replacement conflict sonrası eşit cursor’lı terminal
  recovery anchor kabul ediliyor; `209` snapshot `SNAPSHOT_STALE`, eşik `210`
  snapshot `SYNCED`; terminal recovery exact replay `DUPLICATE`, önceki
  non-terminal recovery ve forward event `QUARANTINED`, boş SQLite journal
  değişmiyor. Odak 1/1, komşu 82/82, tam checker 856/856 PASS. Compileall,
  workspace (296 aktif Python dosyası) ve diff check PASS. Kanıt
  `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`; sıradaki tek asistan-owned
  güvenli iş post-gap equal-boundary repeated recovery fingerprint conflict
  re-entry parity regresyonudur.

- 2026-09-19 P2.04 post-gap repeated replacement conflict anchor monotonicity
  ve terminal quarantine parity `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`:
  ilk replacement conflict sonrası non-terminal recovery anchor ile yeniden
  `SYNCED` açıldı; aynı recovery identity’nin tekrarlı fingerprint conflict’i
  yeniden `CONFLICT/GAP` açıyor. Daha eski `209` recovery anchor
  `RESYNC_ANCHOR_STALE`, monoton `211` terminal anchor kabul ediliyor; `210`
  snapshot `SNAPSHOT_STALE`, `211` snapshot `SYNCED`; terminal recovery replay
  `DUPLICATE`, eski recovery ve forward event `QUARANTINED`, boş SQLite journal
  değişmiyor. Odak 1/1, komşu 80/80, tam checker 855/855 PASS. Compileall,
  workspace (296 aktif Python dosyası) ve diff check PASS. Kanıt
  `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`; sıradaki tek asistan-owned
  güvenli iş post-gap repeated replacement anchor equal-boundary freshness ve
  duplicate quarantine parity regresyonudur.

- 2026-09-19 P2.04 post-gap replacement fingerprint conflict ve re-entry
  quarantine parity `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`: GAP sonrası
  aynı replacement identity’nin farklı fingerprint’i `CONFLICT/GAP` açıyor;
  doğrudan snapshot `SYNC_STATE_INVALID`; transaction-ileri/event-geride ve
  event-ileri/transaction-geride recovery anchor sonrası `209` snapshot
  `SNAPSHOT_STALE`, `210` snapshot `SYNCED`; recovery exact replay
  `DUPLICATE`, eski replacement ve forward event `QUARANTINED`, boş SQLite
  journal değişmiyor. Odak 1/1, komşu 79/79, tam checker 854/854 PASS.
  Compileall, workspace (296 aktif Python dosyası) ve diff check PASS. Kanıt
  `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`; sıradaki tek asistan-owned
  güvenli iş post-gap repeated replacement conflict anchor monotonicity ve
  terminal quarantine parity regresyonudur.

- 2026-09-19 P2.04 recovery anchor post-gap re-entry ve paired snapshot gate
  parity `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`: GAP sonrası doğrudan
  snapshot `SYNC_STATE_INVALID`, iki paired recovery anchor yönü yeniden
  `RECONCILIATION_REQUIRED`, `209` snapshot `SNAPSHOT_STALE`, `210` snapshot
  `SYNCED`; recovery replay `DUPLICATE`, boş SQLite journal değişmiyor. Odak
  1/1, komşu 78/78, tam checker 853/853 PASS. Compileall, workspace (296
  aktif Python dosyası) ve diff check PASS. Kanıt
  `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`; sıradaki tek asistan-owned
  güvenli iş post-gap replacement fingerprint conflict ve re-entry quarantine
  parity regresyonudur.

- 2026-09-19 P2.04 equal-cursor replacement anchor sonrası same-cursor
  replacement fingerprint conflict ve snapshot gate parity
  `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`: aynı replacement identity’nin
  farklı fingerprint’i `CONFLICT/GAP` açıyor; doğrudan snapshot reddediliyor;
  yalnız yeni equal-cursor recovery anchor ve taze snapshot ile `SYNCED` açılıyor,
  exact recovery replay `DUPLICATE`, boş SQLite journal değişmiyor. Odak 1/1,
  komşu 73/73, tam checker 848/848 PASS. Compileall, workspace (296 aktif
  Python dosyası) ve diff check PASS. Kanıt
  `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`; sıradaki tek asistan-owned
  güvenli iş equal-cursor recovery anchor sonrası snapshot freshness boundary
  ve terminal quarantine parity regresyonudur.

- 2026-09-19 P2.04 equal-cursor replacement anchor sonrası terminal identity
  ve late-event quarantine parity `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`:
  exact replacement replay `DUPLICATE`, terminal öncesi geç kalan event ve
  terminal sonrası ileri event `QUARANTINED` kalıyor; coordinator `SYNCED`
  durumunu koruyor ve boş SQLite journal değişmiyor. Odak 1/1, komşu 72/72,
  tam checker 847/847 PASS. Compileall, workspace (296 aktif Python dosyası)
  ve diff check PASS. Kanıt `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`;
  sıradaki tek asistan-owned güvenli iş terminal replacement anchor sonrası
  same-cursor replacement fingerprint conflict ve snapshot gate parity
  regresyonudur.

- 2026-09-19 P2.04 terminal replacement anchor sonrası equal-cursor resync
  identity ve snapshot gate re-entry parity `IMPLEMENTED_WITH_LIMITATION /
  LOCAL_PASS`: equal cursor’lı yeni replacement identity stale sayılmadan
  `RECONCILIATION_REQUIRED` durumuna dönüyor; snapshot olmadan `mark_synced`
  `AUTHORITATIVE_SNAPSHOT_REQUIRED` ile fail-closed kalıyor; taze snapshot
  sonrası aynı replacement `DUPLICATE`, boş SQLite journal değişmiyor. Odak
  1/1, komşu 71/71, tam checker 846/846 PASS. Compileall, workspace (296
  aktif Python dosyası) ve diff check PASS. Kanıt
  `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`; sıradaki tek asistan-owned
  güvenli iş equal-cursor replacement anchor sonrası terminal identity ve
  late-event quarantine parity regresyonudur.

- 2026-09-19 P2.04 terminal replacement anchor sonrası stale resync anchor
  ve snapshot gate re-entry parity `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`:
  stale cursor anchor `RESYNC_ANCHOR_STALE` ile reddediliyor; bu hata sonrası
  `GAP` durumunda doğrudan snapshot uygulanamıyor; yalnız monotonic replacement
  anchor ve taze authoritative snapshot ile `SYNCED` açılıyor, boş SQLite journal
  değişmiyor. Odak 1/1, komşu 70/70, tam checker 845/845 PASS. Compileall,
  workspace (296 aktif Python dosyası) ve diff check PASS. Kanıt
  `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`; sıradaki tek asistan-owned
  güvenli iş terminal replacement anchor sonrası equal-cursor resync identity
  ve snapshot gate re-entry parity regresyonudur.

- 2026-09-19 P2.04 terminal replacement anchor sonrası snapshot cursor
  freshness ve stale-boundary parity `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`:
  terminal anchor’ın transaction zamanı veya event zamanı snapshot cursor’ının
  en büyük bileşeni olarak kullanılıyor; `209` snapshot `SNAPSHOT_STALE`, eşit
  `210` snapshot fresh kabul ediliyor. Odak 1/1, komşu 69/69, tam checker
  844/844 PASS. Compileall, workspace (296 aktif Python dosyası) ve diff check
  PASS. Kanıt evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md; sıradaki tek
  asistan-owned güvenli iş terminal replacement anchor sonrası stale resync
  anchor ve snapshot gate re-entry parity regresyonudur.

- 2026-09-19 P2.04 empty/reopen replacement anchor sonrası terminal cursor
  ve late-event quarantine parity `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`:
  terminal `REJECT` anchor sonrası exact replay `DUPLICATE`, terminalden önce
  kalan late event ve terminalden sonra gelen yeni event `QUARANTINED` kalıyor;
  coordinator yanlışlıkla `SYNCED` durumundan çıkmıyor ve boş SQLite journal
  değişmiyor. Odak 1/1, komşu 68/68, tam checker 843/843 PASS. Compileall,
  workspace (296 aktif Python dosyası) ve diff check PASS. Kanıt
  evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md; sıradaki tek asistan-owned
  güvenli iş terminal replacement anchor sonrası snapshot cursor freshness ve
  stale-boundary parity regresyonudur.

- 2026-09-19 P2.04 empty/reopen aynı cursor identity conflict ve snapshot
  gate parity `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`: boş SQLite journal
  yeniden açıldıktan sonra resync anchor ile kurulan event exact duplicate
  olarak kalıyor; aynı event kimliğinin farklı fingerprint’i `CONFLICT` açıp
  `GAP` durumuna geçiriyor. Snapshot bu durumda doğrudan uygulanamıyor;
  replacement anchor ve fresh snapshot olmadan `SYNCED` açılamıyor. Journal
  anchor işlemleriyle değişmiyor ve boş kalıyor. Odak 1/1, komşu 67/67, tam
  checker 842/842 PASS. Compileall, workspace (296 aktif Python dosyası) ve
  diff check PASS. Kanıt evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md;
  sıradaki tek asistan-owned güvenli iş empty/reopen replacement anchor
  sonrası terminal cursor ve late-event quarantine parity regresyonudur.

- 2026-09-19 P2.04 empty/reopen cursor freshness ve resync-anchor parity
  `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`: boş SQLite journal yeniden
  açıldığında cursor `()` kalıyor ve authoritative snapshot kapısı korunuyor;
  boş başlangıçtan uygulanan anchor için cursor çiftinden eski snapshot
  reddediliyor, taze snapshot ile `SYNCED` açılıyor. Odak 1/1, komşu 66/66,
  tam checker 841/841 PASS. Compileall, workspace (296 aktif Python dosyası)
  ve diff check PASS. Kanıt evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md;
  sıradaki tek asistan-owned güvenli iş empty/reopen sonrası aynı cursor
  identity conflict ve snapshot gate parity regresyonudur.

- 2026-09-19 P2.04 restart terminal cursor freshness ve authoritative
  snapshot sınır parity `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`:
  restart ile hydrate edilen terminal cursor için anchor gözlem zamanı hem
  transaction hem event zamanını kapsıyor; authoritative snapshot da cursor
  çiftinin en güncel bileşeninden eskiyse `SNAPSHOT_STALE` ile reddediliyor.
  Odak 1/1, komşu 65/65, tam checker 840/840 PASS. Compileall, workspace
  (296 aktif Python dosyası) ve diff check PASS. Kanıt
  evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md; sıradaki tek
  asistan-owned güvenli iş empty/reopen cursor freshness ile resync-anchor
  parity regresyonudur.

- 2026-09-19 P2.04 terminal replay conflict ve restart snapshot parity
  `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`: ikinci açılışta terminal
  snapshot değişmeden kalıyor; terminal event exact duplicate, aynı event
  kimliğinin farklı fingerprint’i `CONFLICT` ve coordinator’da GAP oluyor.
  Odak 1/1, komşu 64/64, tam checker 839/839 PASS. Compileall, workspace
  (296 aktif Python dosyası) ve diff check PASS. Kanıt
  evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md; sıradaki tek
  asistan-owned güvenli iş restart sonrası terminal cursor freshness ve
  authoritative snapshot sınır parity regresyonudur.

- 2026-09-18 P2.04 read-only listStatus sequence/gap quarantine ve
  reconnect sınırı IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS: yeni venue
  sequence icat edilmeden transaction_time_ms,event_time_ms cursor’ı
  non-decreasing doğrulanıyor; exact duplicate/no-op, aynı event ID için
  fingerprint conflict ve out-of-order GAP fail-closed uygulanıyor.
  RECONCILIATION_REQUIRED, STALE ve GAP durumlarında yeni listStatus
  olayı kabul edilmiyor; reconnect sonrası açık reconciliation olmadan
  acceptance yok. Bu yalnız in-memory offline kapıdır; REST catch-up, canlı
  reconnect, durable cursor hydration, core/economic binding, mutation ve
  mainnet authority açılmadı. Odak 37/37 PASS; tam checker 812/812 PASS.
  Compileall, workspace (296 aktif Python dosyası) ve diff check PASS. Kanıt
  evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md; sıradaki tek
  asistan-owned güvenli iş explicit offline reconciliation anchor/resync
  contract’ını aynı fail-closed sınırda doğrulamaktır.

- 2026-09-18 P2.04 listStatus → bounded SQLite journal sınırı (önceki dilim)

- 2026-09-18 P2.04 `listStatus` → bounded SQLite journal sınırı
  `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`: parser çıktısı ayrı
  `USER_STREAM_LIST_STATUS` observation olarak `OrderListEventStore` içine
  bağlandı. Canonical JSON + SHA-256 checksum, transaction-time monotonic
  sıra, restart replay, exact duplicate/no-op, identity conflict ve
  out-of-order/terminal fail-closed davranışı korunuyor. Parser’ın taşımadığı
  leg status/role/type, fiyat, miktar, fee veya fill çıkarılmıyor; observation
  `OrderListVenueEvent` veya ekonomik/core event’e yükseltilmiyor. P2.04
  parser+journal odak kümesi `25/25 PASS`; tam checker `810` testte `808 PASS`,
  iki Windows Credential Manager ortam hatası (`1312` ve cleanup
  `CREDENTIAL_NOT_FOUND`) kaldı. Compileall, workspace (`296` aktif Python
  dosyası) ve diff check PASS. Kanıt
  `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`; sıradaki tek
  asistan-owned güvenli iş read-only stream sequence/gap quarantine ve
  reconnect/catch-up sınırının offline doğrulanmasıdır.

- 2026-09-18 P2.03 durable venue-event journal ve cancel-replace observation
  sequencing karar kapısı
  `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`: exact OCO/leg eşleşmesiyle
  kabul edilen venue event’leri ve cancel-replace identity gözlemleri
  `OrderListEventStore` ile bounded SQLite journal’a bağlandı. Canonical JSON +
  SHA-256 checksum, monotonic sequence, restart replay, exact duplicate/no-op,
  conflict, out-of-order/terminal red ve `BEGIN IMMEDIATE` rollback birlikte
  korunuyor. Journal yalnız redacted venue-fact observation taşır; fill, core
  event, economic state, order mutation veya signed transport üretmez. Odak
  `18/18 PASS`; tam checker `806` testte `804 PASS`; iki Windows Credential
  Manager ortam hatası (`1312` ve cleanup `CREDENTIAL_NOT_FOUND`) kaldı.
  Compileall, workspace (`296` aktif Python dosyası) ve diff check PASS. Kanıt
  `evidence/P2.03/MARKET_CONDITIONAL_ORDER_LIST_CONTRACT_SONUC.md`; sıradaki
  tek asistan-owned güvenli iş read-only User Data Stream order-list event
  parser/adapter contract kapısıdır.

- 2026-09-18 P2.03 venue event reconciliation ve cancel-replace identity
  karar kapısı (önceki dilim)
  `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`: OCO venue event’leri exact
  `orderListId` + `listClientOrderId` ve exact leg `orderId` +
  `clientOrderId` ile redacted evidence’a bağlandı; liste veya bacak kimliği
  uyuşmazlığı `CONFLICT` olarak kalıyor. Binance’in cancel-replace
  `cancelResult`/`newOrderResult` ayrımı immutable prior/replacement identity
  ile sınıflandırılıyor; eksik veya tutarsız sonuç `UNKNOWN`,
  `CANCEL_REJECTED_NEW_CONFIRMED` ise yeniden reconciliation gerektiriyor.
  Hiçbir sonuç fill, core event, economic state, order mutation veya signed
  transport üretmiyor. Odak `5/5 PASS`; tam checker `801` testte `799 PASS`;
  iki Windows Credential Manager ortam hatası (`1312` ve cleanup
  `CREDENTIAL_NOT_FOUND`) kaldı. Kanıt
  `evidence/P2.03/MARKET_CONDITIONAL_ORDER_LIST_CONTRACT_SONUC.md`.

- 2026-09-18 P2.03 SQLite atomic durable replay owner (önceki dilim)
  `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`: Offline OCO identity ve bounded
  venue-fact observation projection’ı `OrderListStore` ile SQLite’a bağlandı.
  Identity ve her observation canonical JSON + SHA-256 checksum ile tutuluyor;
  `BEGIN IMMEDIATE` transaction içinde append, duplicate/conflict kontrolü,
  sıralı replay ve rollback birlikte korunuyor. Restart sonrası projection
  aynı snapshot olarak yeniden kuruluyor; checksum, sıra, identity, terminal
  koordinasyon ve bounded `128` observation sınırı fail-closed. Odak OCO
  contract + durable store `8/8 PASS`; tam checker `796` testte `794 PASS`,
  iki hata Windows Credential Manager ortamı (`1312` ve cleanup
  `CREDENTIAL_NOT_FOUND`) nedeniyle kaldı. Compileall, workspace (`292` aktif
  Python dosyası) ve diff check PASS. Fiyat, miktar, fill, fee, reserve, core
  event, cancel-replace, venue reconciliation, signed transport, User Data
  Stream orchestration, Testnet mutation ve mainnet açılmadı. Kanıt
  `evidence/P2.03/MARKET_CONDITIONAL_ORDER_LIST_CONTRACT_SONUC.md`; sıradaki
  tek iş venue event reconciliation ve cancel-replace identity karar kapısıdır.

- 2026-09-18 P1.16.g local feature/label horizon ve historical runner binding
  tamamlandı: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, production readiness
  `NO`. Bounded exact `CLOSE_SMA`, `CLOSE_RETURN` ve
  `FUTURE_CLOSE_RETURN` pipeline’ı closed-bar, chronology, lookback/horizon ve
  1.000 bar limitleriyle fail-closed uygulandı. Feature binding run planına,
  historical reducer’a ve capture identity’sine bağlandı; warmup barlarında
  action üretilmiyor, binding değişirse reducer başlamadan reddediliyor.
  `4/4` feature testi, `6/6` evaluation binding testi, `26/26` historical API
  regresyonu, compile, workspace ve diff kontrolleri geçti. Tam checker
  `786/788 PASS`; iki hata Windows Credential Manager ortamı (`1312` ve
  cleanup `CREDENTIAL_NOT_FOUND`) nedeniyle kaldı. Kanıt
  `evidence/P1.16.g/SONUC.md`. Sıradaki tek iş `P1.16.i` stress ekonomik
  modeli ve gerçek senaryo runner karar kapısıdır.

- 2026-09-18 P1.16.f araştırma-önce yeniden doğrulama tamamlandı:
  QuantConnect warm-up sırasında trade yerleştirilmediğini, Freqtrade ise
  stabil indicator history’sinin local strategy lookback’inden türetilmesi ve
  unstable başlangıç bölümünün backtestten çıkarılması gerektiğini doğruluyor.
  Local source audit `signal_readiness.py`nin yalnız caller warmup sayısını
  sınıflandırdığını, mevcut historical simulation/plan/contract zincirinin
  feature/indicator/label adapterı taşımadığını gösterdi. Bağımsız stdlib
  warmup/lookahead oracle `PASS`. Kod değişmedi; faz
  `DEFERRED / NO-GO / RESEARCH_AUDITED / LOCAL_PASS`, production readiness
  `NO`. Kanıt `evidence/P1.16.f/SONUC.md`; resmî kaynaklar kanıt dosyasında
  kayıtlı. Sıradaki tek iş `P1.16.g` local feature/label horizon ve gerçek run
  binding karar kapısıdır.

- 2026-09-18 P1.16.a chronological split sınırı tamamlandı:
  public `ChronologicalSplit` kurucusunun bölüm sırası, gap/test sınırı,
  duplicate sample identity ve yanlış point tipi bypass’ları fail-closed
  doğrulanıyor; `ChronologicalPoint` exact string ve non-negative integer
  event-time sınırını koruyor. Odak `7/7 PASS`, bağımsız chronological oracle
  `PASS`, Noether salt-okunur Codex review `PASS_WITH_LIMITATION` (P1/P2 bulgu
  yok), compile ve diff `PASS`. `tools/run_checks.py` ile
  `tools/check_workspace.py` Python `3.13` gereksinimi nedeniyle bu oturumda
  çalışmadı; bundled runtime `3.12.14`, `active_python_files: 286`; güncel
  tam-suite/workspace sonucu iddia edilmiyor. Faz
  `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, production readiness `NO`;
  gap yalnız yapısal ayrımdır, purge/embargo, OOS freeze, feature/label
  leakage, persistence, API/UI, ekonomik hesap ve venue authority açılmadı.
  Kanıt `evidence/P1.16.a/SONUC.md`. Sıradaki tek güvenli iş `P1.16.b`
  OOS freeze ve evaluation lineage karar kapısıdır.

- 2026-09-18 P1.16.b OOS freeze ve evaluation lineage sınırı tamamlandı:
  public `EvaluationLineage` ve `OosTuningDecision` modellerinde exact string
  doğrulaması eklendi; custom equality/string-subclass ile status, experiment ID
  veya outcome allowlist bypass’ı fail-closed. OOS görülmeden tuning
  `TUNING_ALLOWED`, inspection sonrası eski lineage `TOUCHED` ve
  `NEW_EXPERIMENT_REQUIRED`; touched lineage tekrar untouched/inspected
  gösterilemiyor. Odak `5/5 PASS`, bağımsız OOS freeze oracle `PASS`, Hilbert
  salt-okunur Codex re-review `PASS` (P1/P2 bulgu yok), compile ve
  diff `PASS`. Python `3.13` gereksinimi nedeniyle
  `tools/run_checks.py`/`tools/check_workspace.py` bundled `3.12.14` ile
  çalışmadı (`active_python_files: 286`); güncel tam-suite/workspace sonucu
  iddia edilmiyor. Faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, production
  readiness `NO`; dataset/run binding, purge/embargo, feature/label leakage,
  persistence, API/UI, ekonomik hesap ve venue authority açılmadı. Kanıt
  `evidence/P1.16.b/SONUC.md`. Sıradaki tek güvenli iş `P1.16.c`
  feature/label horizon ve purge/embargo karar kapısıdır.

- 2026-09-18 P1.16.c feature/label horizon overlap ve purge kararı tamamlandı:
  `TimeInterval` half-open `[start,end)` sınırı ve deterministic overlap
  assessment korunuyor; adjacent aralık `NO_OVERLAP`, gerçek kesişim
  `PURGE_REQUIRED`. Public assessment constructor’ında status/ID tutarlılığı,
  duplicate ID, exact tuple/interval tipi ve custom equality bypass’ları
  fail-closed. Odak `5/5 PASS`, bağımsız horizon oracle `PASS`, Pauli
  salt-okunur Codex re-review `PASS` (P1/P2 bulgu yok), compile ve diff
  `PASS`. Python `3.13` gereksinimi nedeniyle
  `tools/run_checks.py`/`tools/check_workspace.py` bundled `3.12.14` ile
  çalışmadı (`active_python_files: 286`); güncel tam-suite/workspace sonucu
  iddia edilmiyor. Faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, production
  readiness `NO`; numeric purge/embargo, feature/label dataset binding,
  OOS/trial/stress lineage, persistence, API/UI, ekonomik hesap ve venue
  authority açılmadı. Kanıt `evidence/P1.16.c/SONUC.md`. Sıradaki tek güvenli
  iş `P1.16.d` multiple-testing trial registry karar kapısıdır.

- 2026-09-18 P1.16.d multiple-testing trial registry sınırı tamamlandı:
  `TrialStudy` explicit parameter-space/objective/selection-rule kimliğini ve
  en fazla 1.000 trial sınırını taşıyor; `SUCCEEDED`, `FAILED`, `INVALID`
  denemelerin tamamı sayılıyor. Duplicate aynı payload için idempotent,
  conflict ve limit aşımı fail-closed. Public registry/model subclass,
  tuple-subclass ve custom-equality bypass’ları exact type kontrolleriyle
  kapatıldı. Odak `6/6 PASS`, evaluation-binding `6/6 PASS`, bağımsız trial
  control `PASS`, ikinci salt-okunur kaynak kontrolü `PASS_WITH_LIMITATION`
  (P1/P2 bulgu yok), compile ve diff `PASS`. Python `3.13` gereksinimi ve
  bundled `3.12.14` nedeniyle checker’lar `FAIL` (`active_python_files: 286`),
  API read testi `starlette` eksikliği nedeniyle çalışmadı; tam-suite/workspace
  sonucu iddia edilmiyor. Faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS`,
  production readiness `NO`; optimizer, score/KPI, winner selection,
  persistence, dataset binding, OOS/stress result, purge/embargo, API/UI ve
  ekonomik hesap açılmadı. Kanıt `evidence/P1.16.d/SONUC.md`. Sıradaki tek
  güvenli iş `P1.16.e` stress lineage ve ayrı sonuç kimliği karar kapısıdır.

- 2026-09-18 P1.16.e stress lineage ve ayrı sonuç kimliği tamamlandı:
  `StressLineage` base result, stress profile ve profile hash girdilerinden
  deterministic ayrı `stress_result_id` türetiyor; public kurucu canonical
  kimlik eşleşmesini, sabit `STRESS` etiketini ve exact string/hash tiplerini
  fail-closed doğruluyor. Odak `4/4 PASS`, evaluation-binding `6/6 PASS`,
  bağımsız canonical kimlik kontrolü `PASS`, ikinci salt-okunur kaynak
  kontrolü `PASS_WITH_LIMITATION` (P1/P2 bulgu yok), compile ve diff `PASS`.
  Python `3.13` gereksinimi nedeniyle checker’lar bundled `3.12.14` ile
  `FAIL` (`active_python_files: 286`); API read testi `starlette` eksikliği
  nedeniyle çalışmadı, tam-suite/workspace sonucu iddia edilmiyor. Faz
  `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, production readiness `NO`; spread,
  slippage, latency, volume, partial fill, OHLC ekonomik modeli, seed/RNG,
  persistence, dataset/config/model binding, optimizer, API/UI ve purge/
  embargo açılmadı. Kanıt `evidence/P1.16.e/SONUC.md`. Sıradaki tek güvenli
  iş `P1.16.f` warmup leakage ve readiness binding karar kapısıdır.

- 2026-09-18 P1.15.c two-leg persistence/replay/recovery karar kapısı
  yeniden doğrulandı: `LifecycleStore` metadata’sı
  `NON_ECONOMIC_LIFECYCLE_ONLY`; lifecycle şeması hedge leg/side, quantity,
  effective-time veya recovery alanlarını taşımıyor. Generic economic
  `Store` event/posting batch, hash ve `execution_id` dedup sağlıyor ancak
  two-leg identity/state, effective-time, model lineage veya iki store arasında
  atomic binding sağlamıyor. P1.15.b projection’ını bağlayan mevcut adapter
  bulunmadı; bu nedenle migration, yeni schema veya persistence implementation
  açılmadı. Persistence sınır regresyonu `30/30 PASS`, bağımsız storage schema
  control `PASS`, Beauvoir salt-okunur Codex review `DEFERRED / NO-GO` kararını
  doğruladı, compile/diff `PASS`. `tools/run_checks.py` ve
  `tools/check_workspace.py` Python `3.13` gereksinimi nedeniyle bu oturumda
  tam-suite/workspace sonucu veremedi; güncel tam-suite sonucu iddia edilmiyor.
  Faz `DEFERRED / NO-GO / LOCAL_PASS`, production readiness `NO`; recovery,
  cross ownership, margin/liquidation, API/UI ve venue mutation açılmadı.
  `docs/P1_KRITIK_ARASTIRMA_FINAL/test_matrices/P1.15_TESTS.md` mevcut fakat
  `SPECIFIED_NOT_EXECUTED_AGAINST_LOCAL_CODE`. Kanıt
  `evidence/P1.15.c/SONUC.md`. Sıradaki tek güvenli iş `P1.16.a`
  chronological split ve leakage-free evaluation karar kapısıdır.

- 2026-09-18 P1.15.b accepted two-leg fill projection tamamlandı:
  public projection constructor’ı state, identity pair, fill history, exact
  aggregate ve status tutarlılığını yeniden doğruluyor; aynı side/scope
  çakışmaları ve tamamlanmış leg sonrası history bozulması fail-closed.
  State/leg/status whitelist’lerinde exact string tipi zorunlu. Kırmızı
  regresyonla bulunan iki bulgu düzeltildi. Odak `7/7 PASS`, ilgili hedge
  projection kümesi `11/11 PASS`, bağımsız accepted-fill/malformed-constructor
  oracle `PASS`, Bohr salt-okunur Codex review düzeltme sonrası `PASS`; kritik
  P1/P2 bulgu yok. Compile/diff `PASS`. `tools/run_checks.py` ve
  `tools/check_workspace.py` proje Python `3.13` istediği ve kullanılabilir
  bundled runtime `3.12.14` olduğu için bu oturumda tam-suite/workspace sonucu
  veremedi; güncel tam-suite sonucu iddia edilmiyor. Faz
  `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, production readiness `NO`;
  persistence/replay/recovery, order/reserve/fill posting, cross/margin/
  liquidation, API/UI ve venue mutation açılmadı. Kanıt
  `evidence/P1.15.b/SONUC.md`. Sıradaki tek güvenli iş `P1.15.c`
  two-leg persistence/replay/recovery karar kapısıdır.

- 2026-09-18 P1.15.a hedge identity/two-leg state sınırı tamamlandı:
  unhashable ve yanlış tipte state girdisinin ham `TypeError` üretmemesi için
  `advance_two_leg_state` string guard’ı eklendi; kırmızı regresyonla
  doğrulanıp fail-closed `TWO_LEG_STATE_INVALID` olarak düzeltildi. Odak
  `4/4 PASS`, ilgili two-leg projection kümesi `8/8 PASS`, bağımsız hedge/
  two-leg oracle `PASS`, Herschel salt-okunur Codex review düzeltme sonrası
  `PASS`; kritik P1 bulgu yok. Compile/diff `PASS`. `tools/run_checks.py` bu
  oturumda proje Python `3.13` istediği ve kullanılabilir bundled runtime
  `3.12.14` olduğu için güncel tam-suite çalıştırılamadı; tam-suite sonucu
  iddia edilmiyor. Faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, production
  readiness `NO`; identity/state boundary order/reserve/fill posting,
  persistence, recovery ledger, cross/margin/liquidation, API/UI ve venue
  mutation açmaz. Kanıt `evidence/P1.15.a/SONUC.md`. Sıradaki tek güvenli iş
  `P1.15.b` accepted two-leg fill projection karar kapısıdır.

- 2026-09-18 P1.14.f template activation/capability gate kapısı tamamlandı:
  mevcut gate bağımsız review ve activation oracle ile doğrulandı. Odak
  `4/4 PASS`, ilgili template/projection kümesi `10/10 PASS`, bağımsız oracle
  `PASS`, Singer salt-okunur Codex review `PASS`, kritik P1/P2 bulgu yok;
  compile/diff `PASS`. `PENDING`/`APPROVED`, unsupported capability precedence,
  duplicate/bool allowlist ve non-authority sınırları doğrulandı. `tools/run_checks.py`
  bu oturumda proje Python `3.13` istediği ve kullanılabilir bundled runtime
  `3.12.14` olduğu için güncel tam-suite çalıştırılamadı; tam-suite sonucu
  iddia edilmiyor. Faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, production
  readiness `NO`; gate activation, candidate/order/reserve/fill, persistence,
  API/UI veya venue mutation açmaz. Kanıt `evidence/P1.14.f/SONUC.md`.
  Sıradaki tek güvenli iş `P1.15.a` hedge/cross/two-leg kapsam karar kapısıdır.

- 2026-09-18 P1.14.e strategy template integrity ve non-authority kapısı
  tamamlandı: public `StrategyTemplate(...)` kurucusundaki duplicate capability
  bypass’ı bağımsız review’da bulundu, kırmızı regresyonla doğrulandı ve
  `__post_init__` fail-closed guard’ıyla düzeltildi. Odak `6/6 PASS`, ilgili
  projection kümesi `14/14 PASS`, bağımsız canonical/hash/non-authority oracle
  `PASS`, Turing salt-okunur Codex review düzeltme sonrası `PASS`, kritik P1/P2
  bulgu yok. Compile/diff `PASS`. `tools/run_checks.py` bu oturumda proje
  Python `3.13` istediği ve kullanılabilir bundled runtime `3.12.14` olduğu
  için güncel tam-suite çalıştırılamadı; tam-suite sonucu iddia edilmiyor.
  Faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, production readiness `NO`;
  template inert configuration artifact olarak kalır, activation/candidate/
  order/reserve/fill, persistence, API/UI ve venue mutation yok. Kanıt
  `evidence/P1.14.e/SONUC.md`. Sıradaki tek güvenli iş `P1.14.f` template
  activation/capability gate karar kapısıdır.

- 2026-09-18 P1.14.d threshold/time rebalancing trigger kapısı tamamlandı:
  mevcut projection bağımsız inceleme ve exact Decimal/time oracle ile
  doğrulandı. Odak `8/8 PASS`, ilgili projection kümesi `14/14 PASS`,
  bağımsız oracle `PASS`, Mendel salt-okunur Codex review `PASS`, kritik
  `BLOCKED` bulgu yok. NaN/Infinity/exponent/malformed decimal, threshold=0,
  signed zero, aynı timestamp ve tüm bool zaman girdileri regresyon kapsamına
  alındı. Compile/diff `PASS`. `tools/run_checks.py` bu oturumda proje
  Python `3.13` istediği ve kullanılabilir bundled runtime `3.12.14` olduğu
  için güncel tam-suite çalıştırılamadı; tam-suite sonucu iddia edilmiyor.
  Faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, production readiness `NO`;
  trigger yalnız salt-okunur aday kapısıdır, order/candidate/fill,
  persistence, API/UI ve venue mutation yok. Kanıt `evidence/P1.14.d/SONUC.md`.
  Sıradaki tek güvenli iş `P1.14.e` template integrity ve non-authority karar
  kapısıdır.

- 2026-09-18 P1.14.c signal warmup/closed-bar ve stale readiness kapısı
  tamamlandı: mevcut implementation bağımsız inceleme ve sınır oracle’ıyla
  doğrulandı. Odak `6/6 PASS`, readiness ile ilgili küme `12/12 PASS`,
  bağımsız readiness oracle `PASS`, Locke salt-okunur Codex review `PASS`,
  kritik `BLOCKED` bulgu yok. Stale eşik eşitliği ve tüm gate bool tipleri
  için regresyon kapsaması eklendi. Compile/diff `PASS`. `tools/run_checks.py`
  bu oturumda proje Python `3.13` istediği ve kullanılabilir bundled runtime
  `3.12.14` olduğu için güncel tam-suite çalıştırılamadı; tam-suite sonucu
  iddia edilmiyor. Faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, production
  readiness `NO`; candidate/order/fill, adapter, trigger, persistence, API/UI
  ve venue mutation yok. Kanıt `evidence/P1.14.c/SONUC.md`. Sıradaki tek
  güvenli iş `P1.14.d` threshold/time rebalancing trigger karar kapısıdır.

- 2026-09-18 P1.14.b signal identity/event-time/dedupe kapısı tamamlandı:
  bağımsız review’da bulunan duplicate-history açığı fail-closed guard ve
  regresyon testiyle düzeltildi. Odak `6/6 PASS`, readiness ile ilgili küme
  `11/11 PASS`, ayrı signal oracle `PASS`, Ptolemy salt-okunur Codex review
  düzeltme sonrası `PASS`, kritik `BLOCKED` bulgu yok. Compile/diff `PASS`.
  Kapsamlı
  `tools/run_checks.py` bu oturumda proje Python `3.13` istediği ve kullanılabilir
  bundled runtime `3.12.14` olduğu için başlatılamadı; güncel tam-suite sonucu
  iddia edilmiyor. Faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, production
  readiness `NO`; signal candidate/order/fill, auth/replay window, warmup,
  closed-bar, persistence, API/UI ve venue mutation yok. Kanıt
  `evidence/P1.14.b/SONUC.md`. Sıradaki tek güvenli iş `P1.14.c` signal
  warmup/closed-bar ve stale-policy karar kapısıdır.

- 2026-09-18 P1.14.a mevcut checkout doğrulaması ve bağımsız kapısı tamamlandı:
  exact target/delta projection kaynak ve testleri mevcut durumda çalışır;
  odak `6/6 PASS`, ayrı Decimal oracle `PASS`, Erdos salt-okunur Codex review
  `PASS`, kritik `BLOCKED` bulgu yok. Compile/diff `PASS`. Kapsamlı
  `tools/run_checks.py` bu oturumda proje Python `3.13` istediği ve kullanılabilir
  bundled runtime `3.12.14` olduğu için başlatılamadı; bu nedenle güncel tam-suite
  sonucu iddia edilmiyor. Faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, production
  readiness `NO`; order/reserve/fill, fee/rounding, conversion, balance,
  persistence, signal/template, API/UI ve venue mutation yok. Kanıt
  `evidence/P1.14.a/SONUC.md`. Sıradaki tek güvenli iş `P1.14.b` signal
  identity/dedupe ve event-time karar kapısıdır.

- 2026-09-17 P1.13.h.d Reverse/Infinity boundary bağımsız inceleme ve kritik
  regresyon kapısı tamamlandı: Erdos salt-okunur Codex incelemesi h.a–h.c
  sınırını PASS olarak doğruladı; kritik BLOCKED bulgu yok. Literal boundary
  oracle `3/3`, h.a+h.c gate kümesi `6/6`, hedefli sınır kümesi `9/9`, geniş
  Futures Grid doğrulama kümesi `53/53 PASS`; compile/diff PASS. Exact
  Reverse/Infinity source/oracle yokluğu sürdüğü için vendor-eşdeğer
  implementation `DEFERRED / NO-GO`, availability `NOT_SUPPORTED`, admission
  `BLOCKED`, authority alanları `NONE`. Kanıt `evidence/P1.13.h.d/SONUC.md`;
  order, economic, persistence, API/UI, Binance/Testnet mutation ve mainnet
  yok. Sıradaki tek güvenli iş `P1.14.c` signal warmup/closed-bar ve
  stale-policy karar kapısıdır.

- 2026-09-17 P1.13.h.c Reverse/Infinity `NOT_SUPPORTED` admission sınırı
  tamamlandı: h.a’nın typed fail-closed gate’i ürün katmanına bağlandı. Exact
  source/oracle olmadan her iki varyant `availability=NOT_SUPPORTED`,
  `admission=BLOCKED`, `order_authority=NONE` ve `economic_authority=NONE`
  döndürüyor; Reverse Futures short’a, Infinity generic Futures Grid’e sessiz
  map edilmiyor. Alt faz `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`,
  vendor-eşdeğer implementation `DEFERRED / NO-GO`. Kanıt
  `evidence/P1.13.h.c/SONUC.md`; yeni odak `3/3 PASS`, h.a+h.c `6/6 PASS`,
  Futures Grid ilgili doğrulama kümesi `50/50 PASS`, compile/diff PASS. Order,
  level, reserve, persistence, API/UI, Binance/Testnet mutation ve mainnet yok.
  Sıradaki tek güvenli iş `P1.13.h.d` h.a–h.c boundary’si için bağımsız
  inceleme ve kritik regresyon kapısıdır.

- 2026-09-17 P1.13.h.b Reverse/Infinity Futures Grid araştırma karşı-auditi
  tamamlandı: mevcut 3Commas/Pionex ürün raporları ve primary-source lifecycle
  audit’i karşılaştırıldı. Reverse Grid’in ayrı spot ürün oluşu ve Futures
  short olmadığı doğrulandı; Infinity’nin sabit üst limit olmamasının
  inventory/sermaye/lower-bound/fill garantisi olmadığı doğrulandı. Buna karşın
  exact range transition, reserve, replacement identity, late-fill ve replay
  sözleşmeleri kapanmadı. Alt faz `COMPLETE_WITH_LIMITATION /
  RESEARCH_AUDITED`, vendor-eşdeğer implementation `DEFERRED / NO-GO`.
  Kanıt `evidence/P1.13.h.b/SONUC.md`; rapor hash’leri ve kapsamı orada kayıtlı.
  h.a gate’i korunuyor: her iki varyant `BLOCKED_CONTRACT_REQUIRED`, authority
  alanları `NONE`; order, economic, persistence, API/UI, Binance/Testnet
  mutation ve mainnet yok. Odak h.a ilgili kümesi `24/24 PASS`, compile/diff
  PASS. Sıradaki tek güvenli iş `P1.13.h.c` local `NOT_SUPPORTED`/admission
  sınırıdır.

- 2026-09-17 P1.13.h.a Reverse/Infinity Futures Grid varyant güvenlik kapısı
  tamamlandı: `REVERSE_GRID` ve `INFINITY_GRID` ayrı typed varyantlar olarak
  sınıflandırıldı; exact contract/oracle olmadan ikisi de
  `BLOCKED_CONTRACT_REQUIRED`, `order_authority=NONE` ve
  `economic_authority=NONE`. Reverse Grid Futures short’a sessizce map edilmedi;
  Infinity “sınırsız” ifadesi inventory/sermaye/lower-bound/fill garantisi
  sayılmadı. Karar `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, vendor-eşdeğer
  implementation `DEFERRED / NO-GO`; odak `3/3 PASS`, ilgili g.a–g.c, g.f–g.h,
  h.a kümesi `24/24 PASS`, compile/diff PASS. Kanıt
  `evidence/P1.13.h.a/SONUC.md`; order, reserve, persistence, API/UI,
  Binance/Testnet mutation ve mainnet yok. Sıradaki tek güvenli iş
  `P1.13.h.b` mevcut araştırma kaynaklarının exact Reverse/Infinity
  sözleşmelerini kapatıp kapatmadığının karşı-auditidir.

- 2026-09-17 P1.13.g.h Futures Grid offline lifecycle bağımsız oracle ve
  conflict/replay regresyon kapısı tamamlandı: g.g reducer’ı bağımsız literal
  transition matrisiyle OPEN→CANCEL_PENDING→CANCELED, cancel sonrası
  FILL→FILLED, cancel ack sonrası replacement, erken replacement quarantine,
  duplicate/conflict kimlik, invalid sequence ve deterministic replay sınırları
  üzerinden doğrulandı. Alt faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, local
  oracle `ORACLE_PASS`, vendor-eşdeğer implementation `DEFERRED / NO-GO`.
  Odak `4/4 PASS`; g.a–g.c, g.f–g.h ilgili küme `21/21 PASS`; compile/diff
  PASS. Kanıt `evidence/P1.13.g.h/SONUC.md`; gerçek order/fill/replacement,
  reserve/economic/persistence/venue authority, Binance/Testnet mutation ve
  mainnet yok. Sıradaki tek güvenli iş `P1.13.h` Reverse/Infinity varyantları
  için ayrı karar/kaynak kapısıdır.

- 2026-09-17 P1.13.g.g Futures Grid offline lifecycle transition simülasyonu
  tamamlandı: g.f’de ilan edilen DCABOT yerel politikası immutable in-memory
  reducer ile uygulandı. Cancel request/confirmation sırası, cancel sonrası
  fill’in önceliği, cancel ack olmadan replacement’ın quarantine edilmesi,
  exact duplicate fill’in state değiştirmemesi, unknown/conflict quarantine ve
  deterministic replay kanıtlandı. Bu `FILL_ACCEPTED` yalnız local observation;
  gerçek fill/order/replacement/reserve/economic posting/persistence/venue
  authority değildir. Karar `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, local
  simulation `CONTRACT_READY`, vendor-eşdeğer implementation `DEFERRED /
  NO-GO`, kapsam `DCABOT_OFFLINE_SIMULATION_ONLY`. Odak `5/5 PASS`, g.a–g.c
  gate kümesi `10/10 PASS`, g.f `2/2 PASS`, compile ve diff PASS. Kanıt
  `evidence/P1.13.g.g/SONUC.md`; canlı/API key/secret, order/mutation yok.
  Sıradaki tek güvenli iş local event matrix için bağımsız oracle ve
  conflict/replay regresyon kapısıdır.

- 2026-09-17 P1.13.g.f DCABOT yerel Futures Grid lifecycle politika sözleşmesi
  tamamlandı: vendor-eşdeğerliği iddia etmeyen offline politika; fill-wins-over-
  cancel, cancel-ack-before-replacement, terminal-event reserve release,
  exact-duplicate trade ignore, unknown/conflict quarantine ve deterministic
  replay gereksinimi açık typed değer olarak kayda alındı. Tüm order/economic/
  persistence/venue authority alanları `NONE`; kapsam
  `DCABOT_OFFLINE_SIMULATION_ONLY`. Karar `COMPLETE_WITH_LIMITATION /
  LOCAL_PASS`, yerel kontrat `CONTRACT_DECLARED`, vendor lifecycle implementation
  `DEFERRED / NO-GO`. Odak `2/2 PASS`; mevcut g.a–g.c gate kümesi `10/10
  PASS`, g.d/g.e araştırma kontrolleri ayrı ayrı `3/3 PASS`,
  compile ve diff PASS. `tools/check_workspace.py` bundled Python 3.12 ile
  Python 3.13 önkoşulunda çalışmadı; ortam sınırlaması. Kanıt
  `evidence/P1.13.g.f/SONUC.md`; canlı/API key/secret, order/mutation yok.
  Sıradaki tek güvenli iş: explicit politika üzerine offline lifecycle
  transition simülasyonu; vendor parity ve gerçek venue davranışı açılmayacak.

- 2026-09-17 P1.13.g.e dış Futures Grid lifecycle araştırma raporu karşı-auditi
  tamamlandı: 3Commas’ın 2-step/1-step Trailing Up/Down ve Expansion
  kuralları high-level ürün davranışı olarak, Binance `ORDER_TRADE_UPDATE`,
  Modify/amendment ve sınırlı E/T ordering exchange primitive olarak yeniden
  doğrulandı; Pionex public Orders API’nin SPOT non-strategic ile sınırlı
  olduğu ve Futures Grid strategic lifecycle oracle’ı olmadığı doğrulandı.
  Exact range transition, replacement identity, pending/reserve lifecycle,
  late-fill authority ve deterministic replay oracle birlikte kapanmadı.
  Karar `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED`; ileri implementation
  `DEFERRED / NO-GO`. P1.13.g.c `BLOCKED_CONTRACT_REQUIRED` ve
  `order_authority=NONE` aynen korunuyor. Dış rapor ve hash:
  `C:\Users\nefer\Downloads\futures_grid_lifecycle_primary_sources_research.md`,
  `807333B14D07CCAFC7376480E9BF97D55B79ECD8E5001AB6FC02B85BCD97AEF0`.
  Kanıt `evidence/P1.13.g.e/SONUC.md`; odak `3/3 PASS`, canlı/API key/secret,
  order veya mutation yok. Production readiness `NO`; kalan advanced davranışlar
  `CONTRACT_REQUIRED`.

- 2026-09-17 P1.13.g.d Futures Grid primary-source lifecycle audit tamamlandı:
  3Commas/Pionex ürün belgeleri trailing/expansion davranışını yalnız yüksek
  seviyede destekliyor; Binance kaynakları exchange-level order/event
  gözlemlerini sağlıyor. Exact range transition, replacement identity,
  pending/reserve lifecycle, late-fill authority ve deterministic replay
  oracle birlikte doğrulanmadı. Karar `COMPLETE_WITH_LIMITATION /
  RESEARCH_AUDITED`; ileri implementation `DEFERRED / NO-GO`. P1.13.g.c’nin
  `BLOCKED_CONTRACT_REQUIRED` ve `order_authority=NONE` sınırı korunuyor.
  Rapor `docs/P1.13_FUTURES_GRID_LIFECYCLE_PRIMARY_SOURCE_AUDIT.md`, kanıt
  `evidence/P1.13.g.d/SONUC.md`. Checkout karşı kontrolü, odak `3/3 PASS`,
  compile/workspace/diff PASS; gerçek API key/secret, order veya mutation yok.
  Tam son doğrulama `749` testte `747 PASS`, faz dışı Windows Credential
  Manager `1312` nedeniyle `2` environment error. Production readiness `NO`;
  P1.13.g’nin kalan ileri davranışları `CONTRACT_REQUIRED`.

- 2026-09-17 P1.13.g.c Futures Grid replacement/replay ve late-fill identity
  karar kapısı tamamlandı: `RANGE_REVISION`, `CANCEL_REPLACE`, `LATE_FILL` ve
  `REPLAY` sınırları typed olarak ayrıldı; her sınır için exact range transition,
  replacement identity, pending/reserve lifecycle, late-fill authority ve
  deterministic replay oracle gereksinimleri açıkça listelendi. Exact kaynak ve
  oracle doğrulanana kadar karar `BLOCKED_CONTRACT_REQUIRED`,
  `order_authority=NONE`; order ID, replacement ID, candidate level, state
  mutation, persistence, API/UI ve Binance/Testnet mutation yok. Odak `3/3
  PASS`; P1.13.a–d, f.a–f.d, g.a–g.c ilişkili küme `55/55 PASS`; tam proje
  `749` testte `747 PASS`, Windows Credential Manager `Windows error 1312`
  nedeniyle `2` environment error. Compile/workspace/diff PASS. Durum
  `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, ana P1.13.g `IN_PROGRESS /
  IMPLEMENTATION_PENDING`, bağımsız review `NOT_RUN`, production readiness
  `NO`. Kanıt: `evidence/P1.13.g.c/SONUC.md`. P1.13.g’nin kalan advanced
  davranışları exact source/oracle kanıtı gelene kadar `CONTRACT_REQUIRED`.

- 2026-09-17 P1.13.g.b Futures Grid advanced variant safety gate tamamlandı:
  trailing-up/down, expansion, reversal, range revision, cancel/replace ve
  replay typed enum ile ayrı sözleşmeler olarak sınıflandırıldı. Exact
  transition, replacement identity, reserve, late-fill ve replay oracle’ı
  doğrulanana kadar her varyant `BLOCKED_CONTRACT_REQUIRED`; `order_authority`
  `NONE`. Level/order ID/candidate order/state mutation, persistence, API/UI ve
  Binance/Testnet mutation yok. Odak `3/3 PASS`; P1.13.a–d, f.a–f.d, g.a ve
  g.b ilişkili küme `52/52 PASS`; tam proje `746` testte `744 PASS`, Windows
  Credential Manager `Windows error 1312` nedeniyle `2` environment error.
  Compile/workspace/diff PASS. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`,
  ana P1.13.g `IN_PROGRESS / IMPLEMENTATION_PENDING`, bağımsız review
  `NOT_RUN`, production readiness `NO`. Kanıt: `evidence/P1.13.g.b/SONUC.md`.
  P1.13.g.c ile replacement/replay ve late-fill identity karar kapısı
  kapatıldı; güncel kayıt `evidence/P1.13.g.c/SONUC.md` içindedir.

- 2026-09-17 P1.13.g.a Futures Grid dynamic order placement boundary
  tamamlandı: `STATIC` + `FIXED` yalnız daha önce exact üretilmiş seviyeleri
  inert candidate listesi olarak döndürüyor. `DYNAMIC` placement ve
  `RANGE_REVISION`, exact current-price selection, range transition, reserve,
  cancel/replace identity ve replay sözleşmesi yokluğu nedeniyle
  `BLOCKED_CONTRACT_REQUIRED` kalıyor. `order_authority=NONE`; order ID,
  request, mutation, accepted fill, persistence, API/UI ve canlı emir yok.
  Odak `4/4 PASS`; P1.13.a–d, f.a–f.d ve g.a ilişkili küme `49/49 PASS`; tam
  proje `743` testte `741 PASS`, Windows Credential Manager `Windows error 1312`
  nedeniyle `2` environment error. Compile/workspace/diff PASS. Durum
  `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, ana P1.13.g
  `IN_PROGRESS / IMPLEMENTATION_PENDING`, bağımsız review `NOT_RUN`,
  production readiness `NO`. Kanıt: `evidence/P1.13.g.a/SONUC.md`.
  P1.13.g.b ile advanced variant safety gate kapatıldı; güncel kayıt
  `evidence/P1.13.g.b/SONUC.md` içindedir.

- 2026-09-17 P1.13.f.d Futures Grid funding/mark/P&L projection tamamlandı:
  accepted fill’lerden realized gross P&L, caller-supplied reference mark ile
  unrealized P&L ve signed funding cashflow ayrı projection olarak üretiliyor.
  `matched_cycle_profit` açık inventory’yi dışarıda bırakıyor; `total_pnl`
  mark hareketini ekliyor. Event identity/asset/time/snapshot sınırları
  fail-closed. `total_equity`, venue mark/funding authority, fee conversion,
  maintenance margin, liquidation, reserve mutation, persistence, API/UI ve
  Binance/Testnet mutation yok. Odak `5/5 PASS`; P1.13.a–d, f.a–f.d ilişkili
  küme `45/45 PASS`; tam proje `739` testte `737 PASS`, Windows Credential
  Manager `Windows error 1312` nedeniyle `2` environment error.
  Compile/workspace/diff PASS. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`,
  ana P1.13.f `IN_PROGRESS / IMPLEMENTATION_PENDING`, bağımsız review
  `NOT_RUN`, production readiness `NO`. Kanıt: `evidence/P1.13.f.d/SONUC.md`.
  P1.13.g.a ile dynamic order placement ve grid range/trailing ayrımı kapatıldı;
  güncel kayıt `evidence/P1.13.g.a/SONUC.md` içindedir.

- 2026-09-17 P1.13.f.c Futures Grid isolated margin/leverage ve reserve
  projection tamamlandı: P1.13.f.b ile açılmış LONG/SHORT state üzerinden
  caller-supplied exact contract-size ve reference price ile notional ve
  `notional / leverage` initial-margin projection uygulanıyor. Available margin
  yoksa kapasite `UNVERIFIED`; verilirse yalnız local `ELIGIBLE` veya
  `INSUFFICIENT_AVAILABLE_MARGIN` sonucu üretiliyor. Contract-size `1`
  varsayımı, venue balance/reservation authority, maintenance margin, fee,
  funding, mark/liquidation, P&L, persistence, API/UI ve Binance/Testnet
  mutation yok. Non-terminating initial margin rounding yapılmadan fail-closed.
  Odak `6/6 PASS`; P1.13.a–d, f.a, f.b ve f.c ilişkili küme `40/40 PASS`; tam
  proje `734` testte `732 PASS`, Windows Credential Manager `Windows error 1312`
  nedeniyle `2` environment error. Compile/workspace/diff PASS. Durum
  `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, ana P1.13.f
  `IN_PROGRESS / IMPLEMENTATION_PENDING`, bağımsız review `NOT_RUN`,
  production readiness `NO`. Kanıt: `evidence/P1.13.f.c/SONUC.md`.
  P1.13.f.d ile funding/mark/liquidation ve grid profit/total-P&L projection
  kapatıldı.

- 2026-09-17 P1.13.f.b Futures Grid one-way position ve accepted-fill state
  tamamlandı: selected isolated one-way profile içinde yalnız FLAT başlangıç,
  LONG/SHORT yön, exact quantity ve weighted average-entry projection
  uygulanıyor. Close overflow, ters flat açılış, position flip’i, duplicate
  conflict ve geriye giden effective time fail-closed. Odak `9/9 PASS`;
  P1.13.a–d, f.a ve f.b ilişkili küme `34/34 PASS`; tam proje `728` testte
  `726 PASS`, Windows Credential Manager `Windows error 1312` nedeniyle `2`
  environment error. Compile/workspace/diff PASS. Neutral netleme, non-flat
  initial, P&L, margin/leverage effect, funding/liquidation,
  order/replacement, persistence, API/UI ve Binance/Testnet mutation yok.
  Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, ana P1.13.f
  `IN_PROGRESS / IMPLEMENTATION_PENDING`, bağımsız review `NOT_RUN`,
  production readiness `NO`. Kanıt: `evidence/P1.13.f.b/SONUC.md`.
  P1.13.f.c ile isolated margin/leverage ve reserve projection kapatıldı;
  güncel kayıt `evidence/P1.13.f.c/SONUC.md` içindedir.

- 2026-09-17 P1.13.f.a Futures Grid v1 profile-bound exact level projection
  tamamlandı: Spot Grid’den ayrı `BINANCE/USD_M/USDT/PERPETUAL/ONE_WAY/
  ISOLATED` profile, explicit leverage alanı, `LONG`/`SHORT`/`NEUTRAL`
  direction ve yalnız `FLAT` initial-position policy tanımlandı. Arithmetic
  ve geometric seviyeler exact decimal/rational kök ile
  `price_tick`/`tick_origin` doğrulamasından geçiyor; off-grid, non-perfect
  root ve desteklenmeyen policy fail-closed. Odak `7/7 PASS`; P1.13.a–d ve
  f.a ilişkili küme `25/25 PASS`; tam proje `719` testte `717 PASS`, Windows
  Credential Manager `Windows error 1312` nedeniyle `2` environment error.
  Compile/workspace/diff PASS. Position/fill, margin/leverage effect,
  funding/liquidation, grid-profit/total-equity, order/replacement,
  persistence, API/UI ve Binance/Testnet mutation yok. Durum
  `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, ana P1.13.f
  `IN_PROGRESS / IMPLEMENTATION_PENDING`, bağımsız review `NOT_RUN`,
  production readiness `NO`. Kanıt: `evidence/P1.13.f.a/SONUC.md`.
  P1.13.f.b ile position/initial-position ve accepted-fill state projection
  kapatıldı; güncel kayıt `evidence/P1.13.f.b/SONUC.md` içindedir.

- 2026-09-17 P1.13.e Grid trailing-up/down ve reverse/infinity karar kapısı
  tamamlandı; yeni ürün kodu açılmadı. Araştırma exact range/version geçişi,
  pending order/reserve yaşam döngüsü, cancel-replace identity, late-fill,
  replay ve precision sahipliğini doğrulamadı; reverse/infinity exact
  semantics `NOT_VERIFIED / DEFER` durumda. Durum `DEFERRED / NO-GO /
  LOCAL_PASS`, bağımsız review `NOT_RUN`, production readiness `NO`. Son
  doğrulanmış checkout baseline'ı `712` testte `710 PASS` ve Windows
  Credential Manager `Windows error 1312` nedeniyle `2` environment error;
  compile/workspace/diff kontrolleri PASS. Kanıt: `evidence/P1.13.e/SONUC.md`.
  Sıradaki tek iş `P1.13.f` Futures Grid v1 için ayrı profile ve exact
  projection karar kapısıdır.

- 2026-09-17 P1.13.d Spot Grid geometric precision/quantization kapısı
  tamamlandı: exact rational `N`-inci kökü ve explicit `price_tick`/
  `tick_origin` ile yalnız tam temsil edilebilen geometric seviyeler üretiliyor;
  non-perfect root ve off-tick seviye sessiz yuvarlama olmadan `BLOCKED`.
  Odak `9/9 PASS`; P1.13.a–d ilişkili küme `18/18 PASS`; tam proje `712`
  testte `710 PASS`, faz dışı Windows Credential Manager `Windows error 1312`
  nedeniyle `2` environment error. Bağımsız literal oracle, compile,
  read-only source-surface, workspace ve `git diff --check` PASS. Fee,
  inventory/fill, replacement, trailing/reverse/infinity, API/UI, Store veya
  Binance/Testnet mutation açılmadı. Kanıt: `evidence/P1.13.d/SONUC.md`.
  Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; production readiness `NO`.
  P1.13.e kararı `DEFERRED / NO-GO` olarak kapatıldı; sıradaki tek iş
  `P1.13.f` Futures Grid v1 için ayrı profile ve exact projection karar
  kapısıdır.

- 2026-09-17 P1.13.c Spot Grid fee asset/rounding ve matched cycle profit-total
  equity ayrımı tamamlandı: ilk offline profil yalnız quote-asset fee ve
  explicit `EXACT_NO_ROUNDING` sözleşmesi kabul ediyor; base/third fee asset’i
  ve venue quantization fail-closed. Accepted BUY/SELL çifti exact inventory
  projection üzerinden doğrulanıyor; matched cycle profit ile explicit mark
  fiyatına bağlı total equity ayrı alanlarda hesaplanıyor. Odak `5/5 PASS`;
  P1.13.a–c ilişkili küme `13/13 PASS`; tam proje `707` testte `705 PASS`,
  faz dışı Windows Credential Manager `Windows error 1312` nedeniyle `2`
  environment error. Bağımsız Decimal oracle, compile, read-only source
  surface, workspace ve `git diff --check` PASS. Store/persistence,
  pending reserve/replacement, API/UI, üçüncü fee asset dönüşümü, Binance/
  Testnet mutation veya canlı order açılmadı. Kanıt: `evidence/P1.13.c/SONUC.md`.
  Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; production readiness `NO`.
  Sıradaki tek iş `P1.13.d` geometric seviye precision/quantization karar
  kapısıdır.

- 2026-09-17 P1.12.h.d Futures DCA recovery snapshot ile immutable
  profile-source provenance cross-check ve publish/migration NO-GO gate’i
  tamamlandı: recovery ve provenance profile revision eşleşmesi, tekil
  `ACCEPTED` source snapshot, manifest hash ve reopened target oracle’ı
  salt-okunur karşılaştırılıyor. Stale snapshot, profile mismatch, eksik/bozuk
  provenance veya önceki gate/oracle başarısızlığı `NO_GO`; temiz fixture
  sonucu yalnız `READY_FOR_REVIEW`, `publish_action=BLOCKED` ve
  `migration_action=BLOCKED`. Odak `4/4 PASS`; h.a–h.d ilişkili odak
  `51/51 PASS`; provenance/manifest/reopen oracle kümesi `18/18 PASS`; tam
  proje `702` testte `700 PASS`, faz dışı Windows Credential Manager
  `Windows error 1312` nedeniyle `2` environment error. Compile ve
  read-only source-surface PASS. Gerçek source export, migration/publish,
  CORE01 economic admission, order/fill mutation veya Binance/Testnet
  mutation açılmadı. Kanıt: `evidence/P1.12.h.d/SONUC.md`.
  Sıradaki tek iş `P1.13.c` Spot Grid fee asset/rounding ve matched cycle
  profit-total equity ayrımının karar ve salt-okunur projection kapısıdır.

- 2026-09-17 P1.12.h.c Futures DCA durable profile recovery snapshot ve stale
  quarantine boundary tamamlandı: seçilen profile ait event, posting, release
  ve replay receipt kimlikleri deterministik salt-okunur snapshot olarak
  projekte ediliyor; active profile revision farklıysa snapshot `QUARANTINED`,
  bilinmiyorsa veya journal bozuksa `BLOCKED` kalıyor. Odak `4/4 PASS`; h.a ve
  h.b ile ilişkili odak `47/47 PASS`; tam proje `698` testte `696 PASS`, faz dışı
  Windows Credential Manager `Windows error 1312` nedeniyle `2` environment
  error. Compile, read-only source-surface, byte-oracle ve `git diff --check`
  PASS. CORE01 economic admission, order/fill mutation, Binance/Testnet
  mutation veya mainnet açılmadı. Kanıt: `evidence/P1.12.h.c/SONUC.md`.
  P1.12.h.d ile immutable profile-source provenance cross-check ve
  publish/migration NO-GO gate kapatıldı; sıradaki tek iş `P1.13.c` Spot Grid
  fee asset/rounding ve matched cycle profit-total equity ayrımının karar ve
  salt-okunur projection kapısıdır.

- 2026-09-17 P1.12.h.b Futures DCA profile-bound recovery capability ve CORE01
  admission boundary gate’i tamamlandı: tek profile revision için durable
  profile/event/posting/release/receipt kapsamı birebir doğrulanıyor; eksik
  receipt/release, bozuk journal ve cross-profile transition fail-closed
  `BLOCKED` kalıyor. Odak `4/4 PASS`; h.a ile ilişkili odak `43/43 PASS`; tam
  proje `694` testte `692 PASS`, faz dışı Windows Credential Manager
  `Windows error 1312` nedeniyle `2` environment error. Compile, read-only
  byte-oracle ve `git diff --check` PASS. CORE01 economic admission, order/fill
  mutation, Binance/Testnet mutation veya mainnet açılmadı. Kanıt:
  `evidence/P1.12.h.b/SONUC.md`. P1.12.h.c ve P1.12.h.d ile recovery snapshot,
  immutable profile-source provenance cross-check ve publish/migration NO-GO
  gate kapatıldı; sıradaki tek iş `P1.13.c` Spot Grid fee asset/rounding ve
  matched cycle profit-total equity ayrımının karar kapısıdır.

- 2026-09-17 P1.12.h.a Futures DCA durable recovery/replay readiness gate’i
  tamamlandı: mevcut greenfield journal v4 profile, event, reservation, release,
  economic posting ve CORE01 replay receipt sahiplerini ayrı ve izlenebilir
  tutuyor. Restart replay sequence/checksum/link doğrulaması yapıyor; receipt
  preflight eksik schema/constraint’i salt-okunur `BLOCKED` döndürüyor; atomic
  failure rollback, exact duplicate ve conflict sınırları kanıtlandı. Odak
  `39/39 PASS`; tam proje `690` testte `688 PASS`, faz dışı Windows Credential
  Manager `Windows error 1312` nedeniyle `2` environment error. Compile,
  independent restart oracle ve `git diff --check` PASS. CORE01 economic
  admission, order/fill mutation, Binance/Testnet mutation veya mainnet
  açılmadı. Kanıt: `evidence/P1.12.h.a/SONUC.md`. P1.12.h.b ile profile-bound
  recovery capability ve CORE01 admission boundary, P1.12.h.c ile durable
  profile recovery snapshot ve P1.12.h.d immutable profile-source provenance
  cross-check kapatıldı; sıradaki tek iş `P1.13.c` Spot Grid fee asset/rounding
  ve matched cycle profit-total equity ayrımının karar kapısıdır.

- 2026-09-17 P1.12.g.h Futures DCA fee-aware exit-candidate ve quantization
  boundary contract’ı tamamlandı: g.d’nin explicit fee/funding profilinden çıkan
  exact fee-aware breakeven yalnız `TAKE_PROFIT` adayına bağlandı. Fee profili
  eksikliği, settlement mismatch, off-grid hedef ve kapasite aşımı fail-closed;
  sessiz rounding, STOP/Trailing’a yanlış breakeven bağlama ve order authority
  yok. Odak `9/9 PASS`; tam proje `690` testte `688 PASS`, faz dışı Windows
  Credential Manager `Windows error 1312` nedeniyle `2` environment error.
  Bağımsız Fraction capacity oracle, compile, AST/write-surface ve
  `git diff --check` PASS. Gerçek order/fill, OCO/cancel-replace, reserve
  mutation, persistence veya Binance/Testnet mutation açılmadı
  (`order_authority=NONE`). Kanıt: `evidence/P1.12.g.h/SONUC.md`. P1.12.h.a
  ile durable recovery/replay readiness, P1.12.h.b ile profile-bound recovery
  capability, P1.12.h.c ile durable profile recovery snapshot ve P1.12.h.d ile
  immutable profile-source provenance cross-check kapatıldı; sıradaki tek iş
  `P1.13.c` Spot Grid fee asset/rounding ve matched cycle profit-total equity
  ayrımının karar kapısıdır.

- 2026-09-17 P1.12.g.g Futures DCA candidate identity ve late-fill
  ayrım contract’ı tamamlandı: g.f adayından deterministic SHA-256 snapshot
  identity üretildi; identity trigger, fiyat, requested miktar, kalan kapasite,
  açık miktar ve gözlem zamanına bağlı. Late fill yalnız aynı candidate
  identity’ye bağlı, sıralı ve requested miktarı aşmayan salt-okunur observation
  olarak kaydediliyor; execution order identity veya economic posting üretmiyor.
  Odak `7/7 PASS`; tam proje `681` testte `679 PASS`, faz dışı Windows
  Credential Manager `Windows error 1312` nedeniyle `2` environment error.
  Bağımsız identity/tamper oracle, compile, AST/write-surface ve
  `git diff --check` PASS. Conditional execution, order/fill mutation,
  persistence veya Binance/Testnet mutation açılmadı (`order_authority=NONE`).
  Kanıt: `evidence/P1.12.g.g/SONUC.md`. P1.12.g.h ile tamamlandı; P1.12.h.a ile
  durable recovery/replay readiness, P1.12.h.b ile profile-bound recovery
  capability, P1.12.h.c ile durable profile recovery snapshot ve P1.12.h.d ile
  immutable profile-source provenance cross-check kapatıldı; sıradaki tek iş
  `P1.13.c` Spot Grid fee asset/rounding ve matched cycle profit-total equity
  ayrımının karar kapısıdır.

- 2026-09-17 P1.12.g.f Futures DCA exit-candidate and capacity contract
  tamamlandı: g.e’nin seçtiği `CLOSE` trigger’ı exact tick-grid trigger fiyatı,
  requested quantity ve gözlenmiş açık pozisyon kapasitesine bağlandı. TP,
  stop-loss ve trailing-stop adayları üretilebiliyor; breakeven adjustment ve
  trigger yok durumu fail-closed. Accepted fill + committed exit + yeni aday
  toplamı açık pozisyonu aşamıyor; bağımsız Fraction oracle ile doğrulandı.
  Odak `9/9 PASS`; tam proje `674` testte `672 PASS`, faz dışı Windows
  Credential Manager `Windows error 1312` nedeniyle `2` environment error.
  Compile, AST/write-surface ve `git diff --check` PASS. Gerçek order/fill,
  OCO/cancel-replace, reserve mutation, persistence veya Binance/Testnet
  mutation açılmadı (`order_authority=NONE`). Kanıt:
  `evidence/P1.12.g.f/SONUC.md`. P1.12.g.g ile tamamlandı; sıradaki tek iş
  `P1.12.g.h` fee-aware exit-candidate ve quantization boundary contract’ıdır.

- 2026-09-17 P1.12.g.e Futures DCA exit priority contract
  tamamlandı: aynı gözlemde `STOP_LOSS > TRAILING_STOP > TAKE_PROFIT >
  BREAKEVEN_ADJUSTMENT` önceliği deterministik seçiliyor; breakeven tek başına
  `ADJUST_STOP`, diğerleri `CLOSE` kararı üretiyor. Input sırası sonucu
  değiştirmiyor, duplicate trigger fail-closed. Odak `9/9 PASS`; tam proje
  `665` testte `663 PASS`, faz dışı Windows Credential Manager `Windows error
  1312` nedeniyle `2` environment error. Bağımsız alt-küme oracle, compile ve
  AST/write-surface PASS. Order/fill/candidate/OCO/cancel-replace/reserve,
  persistence veya Binance/Testnet mutation açılmadı (`order_authority=NONE`).
  Kanıt: `evidence/P1.12.g.e/SONUC.md`. P1.12.g.f ile tamamlandı; sıradaki
  tek iş `P1.12.g.g` candidate identity ve late-fill/conditional execution
  ayrım contract’ıdır.

- 2026-09-17 P1.12.g.d Futures DCA fee-aware breakeven contract
  tamamlandı: fee/funding profili olmadan yalnız gross average-entry boundary
  gösteriliyor; settlement asset dışı fee asset’i, asset mismatch ve tick dışı
  fee-aware hedef fail-closed kalıyor. Explicit settlement-notional modelinde
  LONG/SHORT ve signed funding exact hesaplanıyor. Odak `9/9 PASS`; tam proje
  `656` testte `654 PASS`, faz dışı Windows Credential Manager `Windows error
  1312` nedeniyle `2` environment error. Bağımsız Fraction oracle, compile ve
  AST/write-surface PASS. Fee conversion/rounding, funding source/schedule,
  TP/SL/trailing execution, OCO/cancel-replace, persistence veya
  Binance/Testnet mutation açılmadı (`order_authority=NONE`). Kanıt:
  `evidence/P1.12.g.d/SONUC.md`. P1.12.g.e ile tamamlandı; sıradaki tek iş
  `P1.12.g.f` seçilmiş trigger’ı exact exit-candidate ve kapasite contract’ına
  bağlamaktır.

- 2026-09-17 P1.12.g.c Futures DCA average-entry TP/split-TP projection
  tamamlandı: gözlenmiş fill projection’dan LONG/SHORT yönüne göre exact
  average-entry hedefi hesaplanıyor; tick dışı hedef sessiz yuvarlanmadan
  reddediliyor; split TP toplamı açık pozisyonu aşamıyor ve kalan miktar exact
  gösteriliyor. Odak `18/18 PASS`; tam proje `647` testte `645 PASS`, faz dışı
  Windows Credential Manager `Windows error 1312` nedeniyle `2` environment
  error. Compile, AST/write-surface, bağımsız exact oracle ve
  `git diff --check` PASS. TP emri/OCO/cancel-replace, fill, reserve,
  persistence veya Binance/Testnet mutation açılmadı (`order_authority=NONE`).
  Kanıt: `evidence/P1.12.g.c/SONUC.md`. `P1.12.g.d` ile tamamlandı; sıradaki
  tek iş `P1.12.g.e` exit priority ve eşzamanlı trigger karar contract’ıdır.

- 2026-09-17 P1.12.g.b Futures DCA max-DCA/stop/`EXHAUSTED` contract
  tamamlandı: tüketilmemiş ladder için `CONTINUE`, ladder kalırken max-DCA
  sınırında `STOP`, dış stop nedenleri için ayrı `STOP` ve full ladder için
  `EXHAUSTED` kararı salt-okunur değerlendiriliyor. Odak `19/19 PASS`; tam
  proje `640` testte `638 PASS`, faz dışı Windows Credential Manager
  `Windows error 1312` nedeniyle `2` environment error. Compile,
  AST/write-surface, bağımsız contract oracle ve `git diff --check` PASS. Yeni order/recovery talebi,
  lifecycle mutation, fill, reserve, persistence veya Binance/Testnet
  mutation açılmadı (`order_authority=NONE`). Kanıt:
  `evidence/P1.12.g.b/SONUC.md`. Sıradaki tek iş `P1.12.g.c` average-entry
  TP ve split-TP miktar conservation projection’ıdır.

- 2026-09-17 P1.12.g.a Futures DCA start-condition gate tamamlandı:
  `IMMEDIATE`, `CLOSED_CANDLE` ve mevcut `SignalReadiness` sonucuna bağlı
  `SIGNAL` başlangıcı source-time sınırlarıyla salt-okunur değerlendiriliyor.
  Odak `20/20 PASS`; tam proje `634` testte `632 PASS`, faz dışı Windows
  Credential Manager `Windows error 1312` nedeniyle `2` environment error.
  Compile, AST/write-surface ve `git diff --check` PASS. Start gate
  lifecycle/order/fill/reserve/persistence veya Binance/Testnet mutation
  authority taşımıyor (`order_authority=NONE`). Kanıt:
  `evidence/P1.12.g.a/SONUC.md`. Sıradaki tek iş `P1.12.g.b` max-DCA/stop
  koşulları ve `EXHAUSTED` terminal sınırının explicit contract’ıdır.

- 2026-09-17 P1.12.f.i.d custom candidate offline sizing/pre-acceptance
  köprüsü tamamlandı: quote-notional custom candidate’ın ilk seviyesi mevcut
  `SizingCandidate`, kalan seviyeleri mevcut `LadderBinding` olarak salt-okunur
  pre-acceptance kapısına bağlandı. Acceptance identity yeniden doğrulanıyor;
  eligible quote budget aşımı ve acceptance conflict fail-closed. BASE_QTY için
  örtük quote bütçesi üretilmiyor. Odak `23/23`, ilişkili sizing dahil `27/27`
  PASS; tam proje `626/628` PASS, faz dışı Windows Credential Manager
  `Windows error 1312` nedeniyle iki environment error; compile, write-surface ve
  `git diff --check` PASS. `order_authority=NONE`, persistence, reserve, order
  attempt, Binance/Testnet mutation ve mainnet açılmadı. Kanıt:
  `evidence/P1.12.f.i.d/SONUC.md`. Sıradaki tek iş `P1.12.g` DCA
  start/stop/TP/trailing/breakeven lifecycle sözleşmesidir.

- 2026-09-17 P1.12.f.i.c immutable custom candidate acceptance-boundary
  sözleşmesi tamamlandı: candidate projection yeniden doğrulanıp Futures DCA
  profili, instrument filter metadata’sı, ladder seviyeleri ve post-quantization
  conservation alanlarını kapsayan deterministik SHA-256 identity ile snapshot’a
  bağlandı. Tamper/conflict fail-closed; `order_authority=NONE`. Odak 20/20,
  ilişkili 55/55, tam proje 625/625 PASS, compile/workspace PASS (240 aktif
  Python dosyası), `git diff --check` PASS. Persistence, order attempt,
  Binance/Testnet mutation ve mainnet açılmadı. Kanıt:
  evidence/P1.12.f.i.c/SONUC.md. Sıradaki tek iş P1.12.f.i.d custom candidate
  acceptance’ını offline sizing/pre-acceptance köprüsüne bağlamaktır.

- 2026-09-17 P1.12.f.i.b bağımsız candidate/oracle incelemesi ve kritik gate
  tamamlandı: BASE_QTY ve QUOTE_NOTIONAL post-quantization sonuçları bağımsız
  Decimal oracle ile eşleşti; candidate binding AST/write-surface kontrolünde
  persistence/SQLite/HTTP mutation çağrısı bulunmadı. Odak 17/17, ilişkili
  52/52, tam proje 622/622 PASS, compile/workspace PASS (239 aktif Python
  dosyası), `git diff --check` PASS. Gerçek venue metadata, emir, persistence,
  Binance/Testnet mutation ve mainnet açılmadı. Kanıt:
  evidence/P1.12.f.i.b/SONUC.md. Sıradaki tek iş P1.12.f.i.c immutable
  custom candidate acceptance-boundary sözleşmesiydi; i.c ile tamamlandı.

- 2026-09-17 P1.12.f.i.a quantity-step ve quote/base candidate sözleşmesi
  tamamlandı: mevcut instrument filter profiline bağlanan read-only candidate
  projection, BASE_QTY ve QUOTE_NOTIONAL için post-quantization gerçek allocation,
  quantity-step, min-quantity ve min-notional doğruluyor. Tick mismatch ve
  quantity collapse fail-closed; requested/actual allocation ayrımı korunuyor.
  Odak 14/14, ilişkili 49/49, tam proje 619/619 PASS, compile/workspace PASS
  (239 aktif Python dosyası). Emir, persistence, Binance/Testnet mutation ve
  mainnet açılmadı. Kanıt: evidence/P1.12.f.i.a/SONUC.md. Sıradaki tek iş
  P1.12.f.i.b bağımsız candidate/oracle incelemesi ve kritik gate’ti; i.b ile
  tamamlandı.

- 2026-09-17 P1.12.f.i Pionex DIY per-safety-order deviation/allocation
  profile sözleşmesi tamamlandı: custom ladder her safety order için anchor’a
  göre cumulative deviation, strict index/order ve explicit BASE_QTY veya
  QUOTE_NOTIONAL allocation taşıyor; tick hizası ve exact budget conservation
  doğrulanıyor. Bağımsız Decimal oracle dahil odak 5/5, ilişkili küme 43/43,
  tam proje 616/616 PASS, compile/workspace PASS (239 aktif Python dosyası).
  SHARE semantiği, quantity-step/venue quantization, min-notional, persistence
  ve canlı mutation açılmadı. Kanıt: evidence/P1.12.f.i/SONUC.md. Sıradaki
  tek iş i.a quantity-step ve quote/base candidate sözleşmesiydi; i.a ile
  tamamlandı.

- 2026-09-17 P1.12.f.h.av bağımsız replay integrity incelemesi ve kritik gate
  tamamlandı: h.au read-only restart oracle’ı bağımsız AST/write-surface
  kontrolünden geçti; SQLite yazma/append çağrısı yok, schema corruption
  exception’ı fail-closed BLOCKED’a çevriliyor. Odak 15/15, tam proje
  611/611 PASS, compile/workspace PASS (238 aktif Python dosyası),
  `git diff --check` hata vermedi. CORE01 durable owner, Binance/venue
  mutation, mainnet, secret, migration ve publish açılmadı. Kanıt:
  evidence/P1.12.f.h.av/SONUC.md. Sıradaki tek iş P1.12.f.i Pionex DIY
  per-safety-order deviation/allocation profilinin exact sözleşmesidir.

- 2026-09-17 P1.12.f.h.au durable replay integrity oracle
  tamamlandı: read-only restart oracle artık durable event, economic posting,
  release history ve reservation projection checksum/consistency kontrollerini
  kullanıyor; bozuk durable veri exception olarak dışarı taşınmadan BLOCKED
  kalıyor. Pure duplicate boundary, retry duplicate/conflict boundary ve aynı
  scope farklı receipt fingerprint conflict’i kanıtlandı. Odak 15/15,
  ilişkili küme 55/55 PASS, tam proje 611/611 PASS, compile/workspace PASS
  (238 aktif Python dosyası). Oracle durable yazmıyor; Binance/venue mutation,
  mainnet, secret, migration veya publish açılmadı. Kanıt:
  evidence/P1.12.f.h.au/SONUC.md. Sıradaki bağımsız inceleme ve kritik gate
  h.av ile tamamlandı; sonraki tek iş P1.12.f.i profil sözleşmesidir.

- 2026-09-17 P1.12.f.h.at read-only CORE01 replay projection oracle
  tamamlandı: restart oracle durable accepted event, economic posting, release
  transition ve receipt satırlarını read-only loader’larla doğruluyor; aynı
  immutable girdilerle pure CORE01 replay decision/projection yeniden
  hesaplanıyor. Receipt fingerprint/scope ve pure decision eşleşirse READY,
  receipt eksikliği veya stale CORE01 admission BLOCKED. Odak 12/12, ilişkili
  küme 52/52 PASS, tam proje 608/608 PASS, compile/workspace PASS (238 aktif
  Python dosyası). CORE01 durable owner, venue mutation, Binance ve canlı emir
  açılmadı. Kanıt: evidence/P1.12.f.h.at/SONUC.md. Sıradaki tek iş durable
  reservation/posting/release checksum ve duplicate/conflict sınırlarını
  genişleten read-only oracle kapısıydı; bu iş h.au ile tamamlandı.

- 2026-09-17 P1.12.f.h.as atomic CORE01 replay receipt binding tamamlandı:
  accepted Futures DCA fill event’i, release transition, economic posting ve
  replay receipt tek SQLite transaction’ında birlikte yazılıyor. Dört kayıt
  birlikte ACCEPTED veya DUPLICATE; receipt scope mismatch ve injected receipt
  failure event/release/reservation/posting kayıtlarının tümünü rollback
  ediyor. Restart load exact receipt bağlantılarını koruyor. Odak 25/25,
  ilişkili küme 49/49 PASS, tam proje 605/605 PASS, compile/workspace PASS
  (236 aktif Python dosyası). Binance/Testnet mutation, mainnet, secret,
  legacy migration/publish ve yeni economic authority açılmadı. Kanıt:
  evidence/P1.12.f.h.as/SONUC.md. Sıradaki tek iş atomik receipt binding’in
  read-only CORE01 replay projection oracle’ıyla restart sonrası eşitliğini
  kanıtlamaktır.

- 2026-09-17 P1.12.f.h.ar durable CORE01 replay receipt append/load
  tamamlandı: greenfield journal schema revision 4 içine receipt owner tablosu,
  fingerprint primary key ve mapping/event/posting/transition/release scope
  unique contract’ı eklendi. Accepted event, posting, release transition ve
  reservation projection bağlantıları append öncesi doğrulanıyor; exact
  duplicate DUPLICATE, scope/fingerprint çakışması CONFLICT; restart
  sonrasında load ve link doğrulaması çalışıyor. Odak 16/16, ilişkili küme
  46/46 PASS, tam proje 602/602 PASS, compile/workspace PASS (235 aktif
  Python dosyası). Bu faz eski schema migration’ı veya canlı venue/mutation
  açmıyor; receipt append mevcut durable kayıtların ardından ayrı transaction.
  Kanıt: evidence/P1.12.f.h.ar/SONUC.md. Sıradaki tek iş receipt +
  event/release/posting bağını tek transaction’da kuran atomik binding ve
  rollback kapısıdır.

- 2026-09-17 P1.12.f.h.aq durable CORE01 replay receipt Store preflight’i
  tamamlandı: mevcut greenfield journal read-only kontrol edildi; gerekli
  `core_replay_receipts` tablosu, fingerprint identity ve mapping/event/
  posting/release unique scope sözleşmesi tanımlandı. Mevcut schema’da tablo
  bulunmadığı kanıtlandı ve preflight `BLOCKED`; tablo/migration/receipt yazımı
  kendisi tarafından yapılmadı. Fixture READY ve malformed/eksik constraint
  RED kontrolleri var. Odak `3/3`, ilişkili küme `43/43 PASS`, tam proje
  `599/599 PASS`, compile/workspace PASS (`235` aktif Python dosyası). Kanıt:
  `evidence/P1.12.f.h.aq/SONUC.md`. Sıradaki tek iş greenfield schema
  revision/migration ve exact append/load contract’ıdır.

- 2026-09-17 P1.12.f.h.ap offline replay idempotency sözleşmesi tamamlandı:
  accepted CORE01 + Futures DCA replay kararından event/posting/release/
  mapping alanlarıyla bounded canonical fingerprint ve frozen receipt üretiliyor.
  Aynı scope + aynı fingerprint `DUPLICATE`; same-scope payload/fee/commitment/
  transition farkı `CONFLICT`; farklı scope `BLOCKED`. Receipt yalnız accepted
  kararından oluşuyor ve durable Store/journal/restart authority’si taşımıyor.
  Odak `17/17`, ilişkili küme `68/68 PASS`, tam proje `596/596 PASS`,
  compile/workspace PASS (`233` aktif Python dosyası). Kanıt:
  `evidence/P1.12.f.h.ap/SONUC.md`. Sıradaki tek iş receipt’in bounded
  durable Store/restart sözleşmesi için karar kapısıdır.

- 2026-09-17 P1.12.f.h.ao offline CORE01 + Futures DCA replay karar kapısı
  tamamlandı: h.an reducer projection’ı accepted event, projected posting ve
  partial/full release transition ile aynı salt-okunur kararda birleşiyor.
  Event/transition/posting identity, FILL türü, commitment, fee ve release
  consumed-delta exact doğrulanıyor; DUPLICATE yeniden CORE01 economics
  üretmiyor. Kabul sonucu CORE state projection, reservation projection ve
  posting kimliğini taşıyor; Store/journal/posting/venue mutation yok. Odak
  `14/14`, ilişkili küme `65/65 PASS`, tam proje `593/593 PASS`,
  compile/workspace PASS (`233` aktif Python dosyası). Kanıt:
  `evidence/P1.12.f.h.ao/SONUC.md`. Sıradaki tek iş bounded
  idempotency/replay sözleşmesini durable Store’a yazmadan doğrulamaktır.

- 2026-09-17 P1.12.f.h.an offline CORE01 FILL reducer projection tamamlandı:
  h.am admission’ından gelen immutable FILL tuple yalnız kopya CORE01 state
  üzerinde reducer’a uygulanıyor; position quantity, entry notional, fee ve
  order filled/notional exact projection olarak doğrulanıyor. Girdi state,
  durable Store, journal, posting ve venue transport değişmiyor. BLOCKED veya
  bozuk/tekrarlı tuple reducer’a girmeden fail-closed kalıyor; reducer hatası
  ham hata taşımadan `BLOCKED` oluyor. Odak `12/12`, ilişkili küme `50/50
  PASS`, tam proje `591/591 PASS`, compile/workspace PASS (`233` aktif Python
  dosyası). Kanıt: `evidence/P1.12.f.h.an/SONUC.md`. Sıradaki tek iş
  reducer projection’ını Futures DCA posting/release replay kararına salt-
  okunur bağlamaktır.

- 2026-09-17 P1.12.f.h.am Futures DCA → CORE01 economic FILL boundary
  admission kapısı tamamlandı: explicit admitted mapping, accepted fill
  envelope ve projected posting identity/commitment/fee/funding/profile
  eşleşmeleri birlikte doğrulanıyor. Gross commitment CORE01 `qty * price`
  olarak temsil edilemiyorsa, order terminal/UNKNOWN ise, overfill veya
  off-grid quantity/price varsa `BLOCKED`; contract-size ya da ekonomik
  varsayım üretilmiyor. Kabul halinde yalnız immutable CORE01 `FILL` tuple
  önerisi dönüyor; reducer, Store, persistence, posting ve venue mutation yok.
  Odak `10/10`, ilişkili küme `48/48 PASS`, tam proje `589/589 PASS`,
  compile/workspace PASS (`233` aktif Python dosyası). Kanıt:
  `evidence/P1.12.f.h.am/SONUC.md`. Sıradaki tek iş kabul edilmiş tuple’ın
  kopya CORE01 state üzerinde exact reducer projection kapısıdır.

- 2026-09-17 P1.12.f.h.al CORE01 intent identity authority sözleşmesi
  tamamlandı: `Order` modeli explicit `intent_id` taşıyabiliyor; eski INTENT
  payload’ları korunuyor, yeni kimlikler sentetik üretilmiyor ve Spot binding
  serializer’ında restart sonrası korunuyor. h.ak admission oracle’ı artık
  `core_order_id`, role, side, exact limit ve intent identity birlikte
  eşleşirse yalnız salt-okunur `ADMISSIBLE` kararı veriyor; eksik/conflict
  `BLOCKED`. Economic FILL/posting, Store binding ve venue mutation açılmadı.
  Odak `8/8`, tam proje `587/587 PASS`, compile/workspace PASS (`233` aktif
  Python dosyası). Kanıt: `evidence/P1.12.f.h.al/SONUC.md`. Sıradaki tek iş
  admitted mapping’i Futures DCA fill envelope ile CORE01 economic FILL
  boundary’sine bağlayan offline karar kapısıdır.

- 2026-09-17 P1.12.f.h.ak read-only CORE01 mapping admission oracle’ı
  tamamlandı: mevcut `State` içindeki order scope’u `core_order_id`, role, side
  ve exact limit ile karşılaştırılıyor. Order yoksa veya scope çatışıyorsa
  `BLOCKED`; scope tam eşleşse bile mevcut CORE01 `Order` modeli intent kimliği
  taşımadığı için `core_order_intent` authority’si eksik ve admission açılmıyor.
  State/Store/economic projection mutation’ı veya sentetik intent üretilmedi.
  Odak `7/7`, ilişkili guard kümesi `16/16 PASS`, tam proje `585/585 PASS`,
  compile/workspace PASS (`233` aktif Python dosyası). Kanıt:
  `evidence/P1.12.f.h.ak/SONUC.md`. Sıradaki tek iş CORE01 intent identity
  authority’sinin mutasyonsuz karar ve sözleşme kapısıdır.

- 2026-09-17 P1.12.f.h.aj immutable Futures DCA → CORE01 mapping contract’ı
  tamamlandı: accepted event/posting için profile revision, core order/intent,
  role, side ve exact limit alanları açıkça zorunlu. Source/commitment/fee,
  profile ve BUY/SELL limit eşleşmeleri fail-closed; candidate non-economic ve
  CORE01 Store mutation yapmıyor. Odak `5/5`, hedefli küme `28/28 PASS`, tam
  proje `583/583 PASS`, compile/workspace PASS (`233` aktif Python dosyası).
  Kanıt: `evidence/P1.12.f.h.aj/SONUC.md`. Sıradaki tek iş mapping candidate’ın
  mevcut CORE01 state ile mutasyonsuz admission oracle’ıdır.

- 2026-09-17 P1.12.f.h.ai CORE01 economic authority boundary preflight’i
  tamamlandı: durable Futures DCA event/posting replay read-only doğrulanıyor,
  fakat mevcut envelope’ta CORE01 `FILL` için gereken `side`, `core_order_intent`,
  `role` ve `limit_price` bulunmadığı için binding `BLOCKED` kalıyor. CORE01
  Store’a yazma, sentetik intent/side üretme veya cross-database atomicity iddiası
  yok. Odak `3/3`, release+posting kümesi `23/23 PASS`, tam proje
  `578/578 PASS`, compile/workspace PASS (`231` aktif Python dosyası). Kanıt:
  `evidence/P1.12.f.h.ai/SONUC.md`. Sıradaki tek iş Futures DCA → CORE01
  immutable mapping contract’ıdır.

- 2026-09-17 P1.12.f.h.ah durable Futures DCA release + economic-posting
  atomic binding tamamlandı: accepted partial/full fill event’i, release
  history, reservation projection ve economic posting aynı SQLite transaction’ında
  bağlandı. Event/transition/posting identity, source, commitment, fee ve
  consumed-delta eşleşmeleri fail-closed; injected posting failure tümünü
  rollback ediyor; tam retry `DUPLICATE`. Odak `20/20 PASS`; tam proje
  `575/575 PASS`, compile/workspace PASS (`229` aktif Python dosyası). Cancel,
  late/UNKNOWN ekonomik posting’e bağlanmadı; canlı Binance ve CORE01 canlı
  binding açılmadı. Kanıt: `evidence/P1.12.f.h.ah/SONUC.md`. Sıradaki tek iş
  durable economic posting replay’sinin CORE01 ekonomik authority sınırıdır.

- 2026-09-17 P1.12.f.h.ag durable Futures DCA release update tamamlandı:
  schema revision `3` içindeki `reservation_releases` history’si reservation
  projection ile aynı transaction’da yazılıyor. Optimistic version, monotonic
  release cursor, checksum/replay, duplicate/conflict ve injected failure
  rollback doğrulandı. Odak `17/17 PASS`; tam proje `572/572 PASS`,
  compile/workspace PASS (`228` aktif Python dosyası). Economic posting ile
  release’in birleşmesi, canlı Binance ve legacy migration/publish açılmadı.
  Kanıt: `evidence/P1.12.f.h.ag/SONUC.md`. Sıradaki tek iş release + economic
  posting cursor’ının aynı transaction’da bağlanmasıdır.

- 2026-09-17 P1.12.f.h.af Futures DCA release transition state machine
  tamamlandı: partial/full fill, cancel, late ve UNKNOWN için exact conservation,
  quarantine, monotonic release cursor, version gate ve duplicate/conflict
  davranışı eklendi. Saf projection testleri `4/4 PASS`; tam proje
  `569/569 PASS`, compile/workspace PASS (`226` aktif Python dosyası).
  Durable journal update ve transition history henüz açılmadı; legacy
  migration/publish `NOT_APPLICABLE`, canlı Binance açılmadı. Kanıt:
  `evidence/P1.12.f.h.af/SONUC.md`. Sıradaki tek iş release transition’ın
  bounded journal’da optimistic version + cursor ile durable atomic update’idir.

- 2026-09-17 P1.12.f.h.ae greenfield journal binding tamamlandı:
  schema revision 2’de ayrı release cursor, exact economic posting projection
  ve event + reservation + posting tek transaction akışı eklendi. ACCEPTED
  dışı event posting’e bağlanmıyor; source/commitment/fee mismatch ve cursor
  boşluğu fail-closed; duplicate replay idempotent. Odak `13/13 PASS`, tam
  proje `565/565 PASS`, compile/workspace PASS (`224` aktif Python dosyası).
  Legacy migration/publish `NOT_APPLICABLE`; canlı Binance açılmadı. Kanıt:
  `evidence/P1.12.f.h.ae/SONUC.md`. Sıradaki tek iş partial/cancel/late/UNKNOWN
  release transition ve release-cursor state machine kapısıdır.

- 2026-09-17 P1.12.f.h.ad greenfield ürün teslim sınırı kararı tamamlandı:
  ürün yeni kurulacağı için kullanıcıdan eski source DB/export, test çalışması
  veya gerçek işlem kaydı beklenmeyecek. Önceki provenance/migration/publish
  zinciri yalnız gelecekteki legacy import için opsiyonel güvenlik sınırı;
  aktif ürün bağımlılığı değil. Eski başarısız DCA projesi ve yedekler de
  yalnız seçici teknik/UI/UX referansıdır; doğrulama ve reuse kaydı olmadan
  runtime’a alınmaz. Durum `COMPLETE_WITH_LIMITATION / LOCAL_PASS`,
  legacy migration/publish `NOT_APPLICABLE`. Kanıt:
  `evidence/P1.12.f.h.ad/SONUC.md`. Sıradaki tek iş greenfield journal’da
  event + reservation + fill-release + economic-posting cursor binding’idir.

- 2026-09-17 P1.12.f.h.ac bağımsız inceleme + kapsamlı kabul kapısı tamamlandı:
  iki ayrı Standards/Spec incelemesinde bulunan iki P1 düzeltildi. Önceki
  `NO_GO` gate artık readiness’e taşınıyor; manifest mapping’leri evaluation
  sırasında canonical olarak yeniden doğrulanıyor. Güncel odak `14/14`, tam
  proje `562/562 PASS`; migration/publish `NO-GO`. Kanıt:
  `evidence/P1.12.f.h.ac/SONUC.md`. Legacy import yolu ürün teslimatının
  önkoşulu değildir; greenfield journal binding yoluna dönülmüştür.

- 2026-09-17 P1.12.f.h.ab insan kontrollü publish-readiness karar kapısı
  tamamlandı: target validation, manifest eşleşmesi ve bağımsız oracle tek
  kararda birleşiyor. Teknik kanıtlar geçerse `READY_FOR_REVIEW`, fakat
  `approval_state=REQUIRED` ve `publish_action=BLOCKED` korunuyor; oracle
  eksik/başarısızsa `NO_GO`. Migration/publish çalıştırılmadı. Kanıt:
  `evidence/P1.12.f.h.ab/SONUC.md`; odak `13/13`, tam proje `561/561 PASS`.
  Sıradaki tek iş bağımsız inceleme ve kapsamlı kabul kapısıdır.

- 2026-09-17 P1.12.f.h.aa manifest reopen + bağımsız hash/eşleme oracle kapısı
  tamamlandı: production hash yardımcısından bağımsız stdlib oracle reopen
  edilmiş target satırını ve canonical SHA-256 manifestini doğruluyor; target
  veya manifest tahrifi `NO_GO`, target satırı değişmeden kalıyor. Durum
  `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; migration/publish açılmadı. Kanıt:
  `evidence/P1.12.f.h.aa/SONUC.md`; odak `11/11`, tam proje `559/559 PASS`.
  Sıradaki tek iş insan kontrollü publish-readiness karar kapısıdır.

- 2026-09-17 P1.12.f.h.z source-to-target eşleme ve immutable migration
  manifest kapısı tamamlandı: source/target row identity, profile revision,
  payload hash, schema revision, observed time ve state canonical SHA-256
  manifest’e bağlandı. Manifest-target read-only birebir eşleşme `READY`,
  UNKNOWN/duplicate/conflict/empty/mismatch `NO_GO` veriyor. Migration/publish
  çalıştırılmadı. Kanıt: `evidence/P1.12.f.h.z/SONUC.md`; odak `8/8`, tam
  proje `556/556 PASS`. Sıradaki tek iş reopen + bağımsız hash/eşleme oracle
  kapısıdır.

- 2026-09-17 P1.12.f.h.y read-only provenance validation + publish karar kapısı
  tamamlandı: profile checksum/replay, source snapshot identity/hash/state,
  profile FK, tekil ACCEPTED kaynak ve UNKNOWN/QUARANTINED/missing/conflict
  durumları doğrulanıyor. Geçerli target `READY/READY`, sorunlu target
  `NO_GO/NO_GO` dönüyor; otomatik publish ve migration açılmadı. Kanıt:
  `evidence/P1.12.f.h.y/SONUC.md`; odak `5/5`, tam proje `553/553 PASS`.
  Sıradaki tek iş read-only source-to-target eşleme ve immutable migration
  manifest karar kapısıdır.

- 2026-09-17 P1.12.f.h.x bounded provenance target initializer + failure/restart
  kapısı tamamlandı: mevcut v1 dosyasını yerinde değiştirmeyen yeni target,
  `profile_source_snapshots` owner’ı, profile FK, ACCEPTED unique kuralı,
  duplicate/conflict/UNKNOWN ve rollback/reopen sınırları doğrulandı. Durum
  `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; migration ve publish `NO-GO`.
  Kanıt: `evidence/P1.12.f.h.x/SONUC.md`; odak `3/3`, tam proje
  `551/551 PASS`. Sıradaki tek iş read-only profile/provenance validation ve
  publish karar kapısıdır.

- 2026-09-17 P1.12.f.h.w provenance target schema/migration taslağı hazırlandı:
  mevcut v1 dosyalarını yerinde değiştirmeyen ayrı target, immutable
  `profile_source_snapshots` owner’ı, FK/unique/hash/state/replay kısıtları ve
  read-only → validate → commit sırası tanımlandı. Migration çalıştırılmadı;
  durum `CONTRACT_READY / IMPLEMENTATION_PENDING`, migration `NO-GO`. Kanıt:
  `evidence/P1.12.f.h.w/SONUC.md`; son tam proje `548/548 PASS`. Sıradaki tek
  iş bounded target initializer + publish edilmeyen failure/restart testidir.

- 2026-09-17 P1.12.f.h.v provenance SQLite failure/replay oracle kapısı
  tamamlandı: ACCEPTED replay, exact duplicate/conflict, UNKNOWN authority
  dışı bırakma ve commit öncesi failure rollback `3/3` ile doğrulandı. Bu
  test-only oracle production schema/migration binding açmıyor. Kanıt:
  `evidence/P1.12.f.h.v/SONUC.md`; tam proje `548/548 PASS`. Sıradaki tek iş
  provenance owner’ını production schema’ya bağlayan minimum migration
  taslağıdır.

- 2026-09-17 P1.12.f.h.u immutable provenance schema taslağı hazırlandı:
  profile revision’dan ayrı source snapshot owner’ı, source kind/row ID,
  payload hash, source schema revision, observed time ve ACCEPTED/UNKNOWN/
  QUARANTINED state kuralları tanımlandı. V1’e uygulanmadı, schema version ve
  migration binding açılmadı. Kanıt: `evidence/P1.12.f.h.u/SONUC.md`; son tam
  proje kapısı `545/545 PASS`. Sıradaki tek iş provenance schema için bağımsız
  SQLite failure/replay ve duplicate/conflict oracle’ıdır.

- 2026-09-17 P1.12.f.h.t profile source provenance/snapshot identity karar
  kapısı tamamlandı: source kind, row/snapshot identity, payload hash,
  schema/policy revision, observed time ve profile bağı zorunlu contract olarak
  tanımlandı. Aynı identity farklı hash ile `CONFLICT`, eksik/UNKNOWN source
  `QUARANTINED/NO_GO` kalacak. V1 profile tablosu provenance taşımadığı için
  persistence/migration `NO-GO`; üretim kodu değişmedi. Kanıt:
  `evidence/P1.12.f.h.t/SONUC.md`; mevcut adapter `2/2`, son tam proje
  `545/545 PASS`. Sıradaki tek iş immutable provenance schema taslağıdır.

- 2026-09-17 P1.12.f.h.s profile revision + contract-size source adapter
  tamamlandı: caller-supplied revision identity, symbol, effective time,
  exact positive contract-size ve fee/slippage/rounding policy revision’ları
  immutable journal profile revision’ına dönüştürülüyor. Contract-size default
  edilmiyor; invalid source fail-closed. Venue fetch, provenance, migration ve
  ekonomik binding açılmadı. Kanıt: `evidence/P1.12.f.h.s/SONUC.md`; odak
  `2/2 PASS`, tam proje `545/545 PASS`. Sıradaki tek iş explicit source
  provenance/snapshot identity kararı `P1.12.f.h.t` altında tamamlandı; sıradaki
  iş immutable provenance schema oracle’ıdır.

- 2026-09-17 P1.12.f.h.r migration source contract karar kapısı tamamlandı:
  her hedef alan için source authority/row identity, exact normalization,
  revision-event bağı ve missing/UNKNOWN/conflict/late davranışı zorunlu
  kabul şartı yapıldı. Profile, event/execution, reservation ve posting
  sahiplikleri ayrıldı; mevcut split store’lar bunları tam taşımadığı için
  migration `NO-GO`, implementation `PENDING`. Kanıt:
  `evidence/P1.12.f.h.r/SONUC.md`; hedefli preflight `1/1 PASS`, son tam
  proje kapısı `543/543 PASS`. Sıradaki tek iş profile revision + contract-size
  source adapter karar kapısıdır.

- 2026-09-17 P1.12.f.h.q split-store migration kapsam envanteri tamamlandı:
  preflight v1 journal’ın profile, event/execution, reservation ve posting
  alanlarının tamamını karşılaştırıyor. Gerçek split kaynaklarda yalnız
  event identity/sequence/hash ve reservation identity/owner/amount gözlendi;
  eksik alanlar default’lanmadı, migration `NO-GO` kaldı. Kanıt:
  `evidence/P1.12.f.h.q/SONUC.md`; odak `11/11 PASS`, tam proje
  `543/543 PASS`. Sıradaki tek iş eksik ekonomik alanların üretileceği kaynak
  sözleşmesi için karar kapısıdır.

- 2026-09-17 P1.12.f.h.p event+reservation atomic coordinator kapısı
  tamamlandı: profile-bound event ve source-event bağlı reservation aynı bounded
  SQLite transaction’ında yazılıyor; exact duplicate idempotent, conflict ve
  source mismatch fail-closed. Reservation insert’ine SQLite failure injection
  event insert’inin de restart sonrası görünmemesini doğruladı. Durum
  `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, release/posting ve legacy split
  store migration `NO-GO`. Kanıt: `evidence/P1.12.f.h.p/SONUC.md`; odak
  `10/10 PASS`, tam proje `543/543 PASS`. Sıradaki tek iş mevcut split
  FuturesDcaEventStore + ReservationLedger verisinin bu journal’a güvenli,
  eksik ekonomik alanları uydurmayan migration kararıdır.

- 2026-09-17 P1.12.f.h.o minimum reservation projection kapısı tamamlandı:
  reservation identity, owner/asset, exact reserved-consumed-releasable alanları,
  optional release identity, terminal state, version ve source-event reference
  yazımı/replay’i eklendi. Exact duplicate `DUPLICATE`, farklı payload
  `CONFLICT`, negatif/bozuk alan ve eksik source event fail-closed. Event ve
  reservation aynı transaction’da bağlanmadı; release/posting ekonomik otoritesi
  açılmadı. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, release/atomic
  binding `NO-GO`. Kanıt: `evidence/P1.12.f.h.o/SONUC.md`; odak `8/8 PASS`,
  tam proje `541/541 PASS`. Bu kapıdan sonra event+reservation atomic
  coordinator `P1.12.f.h.p` altında tamamlandı; sıradaki iş split-store migration
  kapsamını kanıtlamaktır.

- 2026-09-17 P1.12.f.h.n profile-bound immutable event envelope kapısı
  tamamlandı: event/execution/order identity, sequence, exact execution
  alanları, canonical payload, checksum, duplicate/conflict ve profile scope
  doğrulandı. Reservation/posting binding’i açılmadı. Durum
  `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, reservation/posting `NO-GO`.
  Kanıt: `evidence/P1.12.f.h.n/SONUC.md`; tam proje `539/539 PASS`. Sıradaki
  tek iş minimum reservation projection kapısıdır.

- 2026-09-17 P1.12.f.h.m immutable profile revision insert/replay kapısı
  tamamlandı: v1 journal profile scope’u explicit contract-size ve policy
  revision kimlikleriyle canonical hash’li, duplicate idempotent ve conflict
  fail-closed biçimde yazıp replay ediyor. Event/reservation/posting binding’i
  açılmadı. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, event binding
  `NO-GO`. Kanıt: `evidence/P1.12.f.h.m/SONUC.md`; tam proje `537/537 PASS`.
  Sıradaki tek iş immutable event envelope validator’ıdır.

- 2026-09-17 P1.12.f.h.l minimum Futures DCA v1 schema kapısı tamamlandı:
  boş/inert bounded SQLite schema initializer profile revision, event,
  reservation ve economic posting sahipliklerini tanımlıyor; mevcut dosya
  üzerine yazmıyor. Binding ve ekonomik satır yazımı açılmadı. Durum
  `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, binding `NO-GO`. Kanıt:
  `evidence/P1.12.f.h.l/SONUC.md`; tam proje `535/535 PASS`. Sıradaki tek iş
  immutable profile revision insert/replay validator’ıdır.

- 2026-09-17 P1.12.f.h.k gerçek kaynaklara bağlı migration preflight kapısı
  tamamlandı: `FuturesDcaEventStore` ve `ReservationLedger` read-only
  incelendi; eksik profile/multiplier, fee/slippage/rounding,
  release-identity ve posting alanlarında açık `NO_GO` verildi. Migration
  hedefi oluşturulmadı. Durum `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, binding
  `NO-GO`. Kanıt: `evidence/P1.12.f.h.k/SONUC.md`; tam proje `533/533 PASS`.
  Sıradaki tek iş minimum production schema’yı oluşturmaktır.

- 2026-09-17 P1.12.f.h.j migration validator/conflict-replay oracle kapısı
  tamamlandı: profile revision, sequence, identity, reservation/posting link,
  checksum ve UNKNOWN/quarantine fail-closed kuralları `3/3 PASS` doğrulandı.
  Bu production migration değildir; durum `COMPLETE_WITH_LIMITATION /
  LOCAL_PASS`, production validator/binding `IMPLEMENTATION_PENDING`. Kanıt:
  `evidence/P1.12.f.h.j/SONUC.md`; sıradaki tek iş gerçek kaynak tiplerine
  bağlayıp tam suite ile doğrulamaktır. Tam proje `532/532 PASS`.

- 2026-09-17 P1.12.f.h.i minimum Futures DCA journal schema/migration
  sözleşmesi hazırlandı: Spot’tan bağımsız bounded SQLite hedefi, immutable
  profile/event/execution/reservation/posting sahiplikleri ve in-place olmayan
  migration sınırı yazıldı. Ekonomik authority alanları varsayılmadı; durum
  `CONTRACT_READY / IMPLEMENTATION_PENDING`, production binding `NO-GO`.
  Kanıt: `evidence/P1.12.f.h.i/SONUC.md`; sıradaki tek iş migration validator
  ile conflict/replay testidir.

- 2026-09-17 P1.12.f.h.h tek journal transaction oracle kapısı tamamlandı:
  bağımsız stdlib SQLite failure-injection testi, event/reservation/posting
  birlikte commit edilmeden hata oluştuğunda restart sonrası partial projection
  görünmediğini ve başarılı commit’in aynı kayıt kümesini replay ettiğini
  doğruladı. Durum `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, production
  binding `IMPLEMENTATION_PENDING`. Kanıt:
  `evidence/P1.12.f.h.h/SONUC.md`; sıradaki tek iş bu sözleşmeyi gerçek
  Futures DCA immutable alanlarına bağlayan minimum schema/migration taslağıdır.
  Tam proje `529/529 PASS`.

- 2026-09-17 P1.12.f.h.g tek journal sahiplik kapısı tamamlandı:
  `SpotBindingStore` atomic transaction için referans kalıbı olsa da Spot
  lifecycle/CORE01 sahibidir; Futures DCA event, multiplier, fee/slippage,
  reservation release ve position commitment schema’sını taşımaz. İki mevcut
  Futures store ayrı transaction sınırlarında kaldı; production coordinator
  eklenmedi. Durum `DEFERRED / NO-GO / LOCAL_PASS`. Kanıt:
  `evidence/P1.12.f.h.g/SONUC.md`; sıradaki tek iş ortak immutable sözleşmeyi
  bağımsız oracle ve failure-injection ile doğrulayan migration/transaction
  contract kararıdır.

- 2026-09-17 P1.12.f.h.f partial/cancel/late/UNKNOWN release kapısı
  tamamlandı: mevcut Futures DCA event/reservation sözleşmeleri release
  identity, consumed/releasable miktar, terminal/quarantine state ve cursor
  taşımıyor. Event sequence’i release authority’si değildir; production
  binding açılmadı. Durum `DEFERRED / NO-GO / LOCAL_PASS`. Kanıt:
  `evidence/P1.12.f.h.f/SONUC.md`; sıradaki tek iş bunu profile revision,
  multiplier ve fee/slippage/rounding ile tek bounded journal transaction’ında
  birleştirmektir.

- 2026-09-17 P1.12.f.h.e fee/slippage/rounding karar kapısı tamamlandı:
  `FuturesDcaFill` fee, fee asset, effective execution price, slippage
  reference, execution time ve rounding policy taşımıyor; pending reserve fee
  ve slippage hariç hesaplanıyor. Production binding açılmadı.
  Durum `DEFERRED / NO-GO / LOCAL_PASS`. Kanıt:
  `evidence/P1.12.f.h.e/SONUC.md`; sıradaki tek iş bu alanları profile
  revision ve release identity ile tek bounded journal transaction’ında exact
  contract olarak tanımlamaktır.

- 2026-09-17 P1.12.f.h.d profile-revision kapsam kapısı tamamlandı:
  `FuturesDcaProfile` symbol, effective-time ve immutable revision authority
  taşımıyor; odak `1/1 PASS`. Production profile/ledger binding açılmadı.
  Durum `DEFERRED / NO-GO / LOCAL_PASS`, tam proje `527/527 PASS`. Kanıt:
  `evidence/P1.12.f.h.d/SONUC.md`; sıradaki tek iş revision scope ile
  fee/slippage/rounding ve partial/cancel/late/UNKNOWN release kurallarını tek
  bounded journal transaction sözleşmesinde birleştirmektir.

- 2026-09-17 P1.12.f.h.c tamamlandı: bağımsız Decimal oracle, DCA fill
  quantity’sinin explicit `pnl_multiplier` ile effective quantity/notional’a
  dönüşümünü doğruladı; `0.001` örneğinde mevcut `quantity × price` sonucu ile
  fark görüldü. Üretim profile/ledger binding açılmadı.
  Durum `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; ekonomik binding
  `DEFERRED / NO-GO`, odak `1/1 PASS`, tam proje `526/526 PASS`. Kanıt:
  `evidence/P1.12.f.h.c/SONUC.md`; sıradaki tek iş profile-revision kapsamı
  ve fee/slippage/rounding dahil tek-journal transaction sözleşmesidir.

- 2026-09-17 P1.12.f.h.b contract-size commitment kapısı tamamlandı:
  `FuturesDcaProfile` multiplier taşımıyor; DCA fill projection notional’ı
  doğrudan `quantity × price` hesaplıyor, ayrı linear math ise explicit
  contract-size istiyor. Sessiz `1` varsayımı reddedildi.
  Durum `DEFERRED / NO-GO / LOCAL_PASS`; production kodu değişmedi, son tam
  suite `525/525 PASS`. Kanıt: `evidence/P1.12.f.h.b/SONUC.md`; sıradaki tek
  iş profile-revision bağlı contract-size/multiplier exact oracle kapısıdır.

- 2026-09-17 P1.12.f.h.a failure-injection kapısı tamamlandı:
  event journal commit’inden reservation commit’inden önceki injected failure
  restart sonrası event’i görünür, reservation’ı unchanged bıraktı. Bu,
  mevcut iki-store yaklaşımının atomic ekonomik binding olmadığını bağımsız
  `1/1 PASS` ile doğrular; production coordinator eklenmedi.
  Durum `LOCAL_PASS / NO-GO_CONFIRMED`; son tam suite `525/525 PASS`.
  Kanıt: `evidence/P1.12.f.h.a/SONUC.md`; sıradaki tek iş dört ekonomik
  sözleşme için exact oracle ve tek bounded SQLite journal failure/restart
  kabulüdür.

- 2026-09-17 gelen ayrıntılı Binance ürün raporu ve ikinci küçük 3Commas/
  Pionex metni yeniden doğrulandı. Güvenli Futures/Spot v1 profili değişmedi.
  Pionex DIY per-safety-order deviation/allocation `P1.12.f.i`; Futures Grid
  dynamic order placement ile dynamic range ayrımı, dynamic margin reserve ve
  P1.15 bağımlı Hedge Grid `P1.13.f–g` kapsamına eklendi. Pasted metindeki
  stale Binance karşılaştırması, kişisel değerler, iç citation’lar, untyped
  mimari ve ilk hatalı step formülü reddedildi. Kod/dependency değişmedi; son
  tam suite `524/524 PASS`. Kanıt/karar raporu:
  `docs/P1.12_P1.13_3COMMAS_PIONEX_KARSILASTIRMA_KARAR_RAPORU.md`.

- 2026-09-17 P1.12.f.h atomic binding yeniden açılma sözleşmesi hazırlandı:
  hedef, event + reservation + fill-release + posting cursor’ını tek bounded
  SQLite transaction’ında tutan tek journal’dır. Base→quote commitment,
  fee/slippage/rounding, partial/cancel/late/UNKNOWN release ve position
  identity exact olarak çözülmeden implementation açılmayacak.
  `CONTRACT_READY / IMPLEMENTATION_PENDING`; mevcut f.g `DEFERRED / NO-GO`
  kararı korunuyor. Son tam suite `524/524 PASS`. Kanıt:
  `evidence/P1.12.f.h/SONUC.md`; sıradaki tek iş bu dört ekonomik sözleşme
  için bağımsız oracle ve failure-injection kabul kapısıdır.

- 2026-09-17 P1.12.f.g reservation + fill-release atomicity karar kapısı
  tamamlandı: mevcut Futures DCA event store ve AccountReservationLedger ayrı
  SQLite transaction sınırlarında olduğu için atomic ekonomik binding güvenli
  biçimde kurulamadı. Kod/adapter değişmedi; `DEFERRED / NO-GO / LOCAL_PASS`.
  Reservation odak `5/5`, event store odak `4/4`, son tam suite `524/524 PASS`.
  Kanıt: `evidence/P1.12.f.g/SONUC.md`; tek veritabanı transaction veya
  crash-safe outbox/recovery sözleşmesi oluşmadan lifecycle/live authority
  açılmayacak.

- 2026-09-17 P1.12.f.f tamamlandı: P1.12.f.d Futures DCA event contract’ı
  ayrı bounded SQLite journal/replay store’a bağlandı. Canonical JSON,
  SHA-256 checksum, sabit deal/config scope, local sequence ve duplicate/
  conflict kuralları restart sonrasında doğrulanıyor. Odak `4/4 PASS`, tam
  proje `tools/run_checks.py` `524/524 PASS`, compile/workspace PASS. Bu local
  sequence Binance transport sequence’i değildir; reservation commit/fill-
  release/economic posting atomicity yoktur. Kanıt:
  `evidence/P1.12.f.f/SONUC.md`; sıradaki tek iş reservation + fill-release
  atomicity karar kapısıdır.

- 2026-09-17 P1.12.f.e tamamlandı: pending Futures DCA quote tutarı mevcut
  immutable AccountReservation projection’ına bağlandı. Yalnız seçilen USDT
  settlement asset ve ONE_WAY mode kabul ediliyor; yanlış asset/mode, kapasite
  aşımı ve stale version fail-closed. Odak `3/3 PASS`, tam proje
  `tools/run_checks.py` `520/520 PASS`, compile/workspace PASS. Bu candidate
  projection’dır; persistence/commit ve fill-release atomicity yoktur. Kanıt:
  `evidence/P1.12.f.e/SONUC.md`; sıradaki tek iş reservation persistence ve
  event journal/replay binding karar kapısıdır.

- 2026-09-16 P1.12.f.d tamamlandı: Futures DCA fill’leri için yerel event
  identity, deal/config revision scope ve ardışık sequence contract’ı eklendi.
  Exact event duplicate idempotent; event/execution identity conflict, scope
  ve sequence gap fail-closed. Odak `4/4 PASS`, tam proje
  `tools/run_checks.py` `517/517 PASS`, compile/workspace PASS. Bu sequence
  Binance transport sequence’i değildir; persistence ve shared-account
  reservation binding yoktur. Kanıt: `evidence/P1.12.f.d/SONUC.md`; sıradaki
  tek iş shared-account reservation binding karar kapısıdır.

- 2026-09-16 P1.12.f.c tamamlandı: ayrı Futures DCA fill projection’ı
  gözlemlenmiş base/safety fill’lerinden exact average-entry, pozisyon
  quantity/notional, tamamlanan safety sayısı ve sınırlı pending seviyeleri
  üretiyor. Base tamamlanmadan safety, seviye atlama, overfill ve farklı
  duplicate payload fail-closed; sonlu dış decimal’e sığmayan average
  yaklaşıklaştırılmıyor. Odak projection `4/4`, bağımsız Decimal oracle `2/2`,
  tam proje `tools/run_checks.py` `513/513 PASS`, compile/workspace PASS.
  Kanıt: `evidence/P1.12.f.c/SONUC.md`; sıradaki tek iş gerçek event
  identity/sequence ve shared-account reservation binding karar kapısıdır.

- 2026-09-16 P1.12.f.b tamamlandı: bağımsız Decimal oracle, Futures DCA plan
  projection’ının long/short cumulative deviation, volume multiplier,
  BASE/QUOTE sizing, quantity-step quantization ve gerçekleşebilir quote
  allocation sonuçlarını tekrar uygulamadan doğruladı. Odak `2/2 PASS`, tam
  proje `tools/run_checks.py` `507/507 PASS`, compile/workspace PASS. Kanıt:
  `evidence/P1.12.f.b/SONUC.md`; sıradaki tek iş average-entry/fill ve aktif
  safety-order/pending reservation sözleşmesidir.

- 2026-09-16 P1.12.f.a tamamlandı: `futures_dca_plan.py` seçilen
  USD_M/USDT/one-way/isolated offline profile içinde finite long/short safety
  ladder, cumulative deviation, volume scale, BASE_QTY/QUOTE_NOTIONAL sizing,
  quantity-step quantization ve required-capital/coverage projection’ı üretiyor.
  Odak `3/3 PASS`, tam proje `tools/run_checks.py` `505/505 PASS`,
  compile/workspace PASS. Order/fill/position/exit/live authority yok.
  Kanıt: `evidence/P1.12.f.a/SONUC.md`; bağımsız oracle P1.12.f.b’de
  tamamlandı.

- 2026-09-16 P1.12.e ilk dikey dilimi tamamlandı: fixed-tier isolated
  liquidation estimate long/short için exact analitik kök üretiyor; risk tier,
  isolated margin ve mark snapshot zorunlu. Tier mismatch, eski snapshot ve
  exact decimal’e sığmayan kök fail-closed. Odak `3/3 PASS`, tam proje
  `tools/run_checks.py` `502/502 PASS`, compile/workspace PASS. Venue
  liquidation, cross/hedge, partial liquidation, bankruptcy, ADL ve core
  binding kapalıdır. Kanıt: `evidence/P1.12.e/SONUC.md`.

- 2026-09-16 P1.12.d ilk dikey dilimi tamamlandı: ayrı
  `linear_ledger_store.py` fee/funding projection’ını checksum’li SQLite
  replay’e bağladı. Restart exactness, duplicate/conflict, geriye dönük zaman
  ve tamper fail-closed odak testleri `4/4 PASS`; tam proje kontrolü
  `tools/run_checks.py` `499/499 PASS`, compile/workspace PASS. Bu store
  position/order/core/venue authority taşımaz; P1.12.e ve P1.12.f sıradaki
  bağımlı işlerdir. Kanıt: `evidence/P1.12.d/SONUC.md`.

- 2026-09-16 3Commas/Pionex ikinci araştırması ve kullanıcı tarafından sağlanan
  Binance raporu birlikte denetlendi. Binance raporunun dar v1 çekirdeği
  korunurken, hedef ürünün gelişmiş DCA ve Futures Grid kapsamı yol haritasına
  somut alt fazlar olarak işlendi: P1.12.f–h Futures DCA plan/lifecycle/recovery;
  P1.13.f–h Futures Grid v1, advanced replacement/replay ve doğrulanmış
  Reverse/Infinity profilleri. 3Commas safety-order multiplier, averaging,
  signal, multiple-TP/trailing/breakeven; Pionex long/short/neutral Futures
  Grid, funding/liquidation ve grid-profit/equity ayrımı `ROADMAP` olarak
  kabul edildi. Pionex Futures DCA exact alanları, dynamic grid algoritması,
  bazı arithmetic/lifecycle ayrıntıları `NOT_VERIFIED/DEFERRED` kaldı.
  Pasted metindeki stale Binance karşılaştırması, kişisel/proje değerleri,
  sahte atıflar, untyped EventBus/GridNode/JSON-Zustand mimarisi ve hatalı ilk
  deviation formülü reddedildi. Kanıt ve karar:
  `docs/P1.12_P1.13_3COMMAS_PIONEX_ARASTIRMA_RAPORU.md` ve
  `docs/P1.12_P1.13_3COMMAS_PIONEX_KARSILASTIRMA_KARAR_RAPORU.md`.

- 2026-09-16 P1.12/P1.13 ürün kuralı araştırması tamamlandı: resmi Binance
  USDⓈ-M ve Spot Grid sözleşmeleri ile ilk ürün profili sabitlendi. Futures
  `USDⓈ-M perpetual + USDT single-asset + one-way + isolated`; UPL/liquidation
  mark price, realized close execution price, funding yalnız timestamped venue
  event ve offline demo default leverage `1x` olacaktır. Spot Grid
  `arithmetic + quote-asset-fee-only`; matched cycle profit ile total equity
  ayrı tutulacaktır. Cross/hedge/multi-asset/ADL/auto-margin, third-asset fee
  conversion, geometric rounding, trailing ekonomik replacement ve
  reverse/infinity açılmadı. Kanıt: `docs/P1.12_P1.13_URUN_KURALLARI_ARASTIRMA_RAPORU.md`.
  Bu karar P1.12.d/e ve P1.13.c için offline sözleşme sınırını netleştirir;
  canlı signed/mutation veya mevcut CORE01 ekonomik Store binding izni vermez.

- 2026-09-16 P2.04 live order-status read-only preflight yapıldı: sentetik
  `BTCUSDT/orderId=0` sorgusu `ORDER_STATUS_QUERY_REJECTED` olarak sanitize
  edildi. Sonuç başarılı lookup veya `NOT_FOUND` olarak yorumlanmadı; gerçek
  order ID/event, reconnect/catch-up orchestration, ekonomik binding ve
  mutation hâlâ kapalıdır.

- 2026-09-16 P2.04 signed read-only order catch-up tamamlandı: ayrı WebSocket
  bağlantısında `order.status` HMAC isteği, `symbol/orderId` identity kontrolü,
  redaction ve hata sonrası socket kapanışı eklendi. Odak `7/7 PASS`,
  standart/optimize suite `495/495 PASS`, release manifest/workspace PASS.
  Gerçek order ID/event, reconnect/catch-up orchestration, ekonomik binding ve
  mutation açılmadı; live reconciliation `DEFERRED / NO-GO`.
  Kanıt: `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

- 2026-09-16 P2.04 User Data Stream fail-closed hardening tamamlandı: geçersiz,
  desteklenmeyen veya timeout/transport hatası sonrasında socket kapatılıyor,
  abonelik temizleniyor ve sonraki okuma `USER_STREAM_NOT_CONNECTED` ile
  duruyor. Odak `6/6 PASS`, standart/optimize suite `493/493 PASS`,
  compileall/workspace PASS. Canlı event, reconnect/catch-up, REST order query,
  ekonomik binding ve mutation açılmadı; live reconciliation `DEFERRED / NO-GO`.
  Kanıt: `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

- 2026-09-16 P2.04 canlı User Data Stream read-only aboneliği tamamlandı: `websockets==17.1` eklendi; gerçek Testnet WS API’de imzalı `userDataStream.subscribe.signature` `status=200`, `subscription_id=0` verdi ve bağlantı kapatıldı. Adapter yalnız bounded `executionReport` identity çözümlemesi ve redacted `UserDataEvent` üretir; mutation, event üretimi, reconnect/catch-up, REST order query ve ekonomik binding yok. Odak `4/4 PASS`, standart/optimize `492/492 PASS`; canlı reconciliation `DEFERRED / NO-GO`. Kanıt: `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

- 2026-09-16 P2.04 canlı read-only kapısı tamamlandı: mevcut `testnet-readonly` credential ile yalnız signed `GET /api/v3/account` geçti; güvenli hesap/izin özeti `SPOT`, `SPOT`, `SIGNED_ACCOUNT_CONTEXT`, `balances_count=502`. Bu hesap erişimi reconciliation veya emir kanıtı değildir. Aktif kaynakta gerçek User Data Stream, reconnect worker ve live reconciliation adapterı bulunmadığı için `P2.04_USER_DATA_STREAM = DEFERRED / NO-GO`; yeni bağımlılık, adapter veya mutation eklenmedi. Standart/optimize `488/488 PASS`, workspace/manifest PASS. Kanıt: `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

- 2026-09-16 P2.03 conditional durable replay mikro-fazı tamamlandı: immutable conditional projection ayrı bounded SQLite store’da checksum’li persist/replay ediliyor; state sırası, duplicate/conflict, tamper ve restart exactness doğrulandı. Fill/core/order/live venue authority yok. Odak `3/3`, tam ve optimize suite `488/488 PASS`; venue-specific identity ve live integration `DEFERRED / NO-GO`.

- 2026-09-16 P2.03 conditional trigger → execution mikro-fazı tamamlandı: trigger gözlemi ile explicit execution order kimliği ayrıldı; duplicate/conflict, execution-before-trigger, out-of-order, GAP/STALE/CONFLICT quarantine ve cancel confirmation race sınırları fail-closed doğrulandı. Fill/core/persistence/live venue/mutation açılmadı. Odak `6/6`, tam ve optimize suite `485/485 PASS`; sonraki conditional durable replay ve gerçek venue identity `DEFERRED / NO-GO`.

- 2026-09-16 P2.03 MARKET durable economic replay mikro-fazı tamamlandı: exact execution state’i ve redacted identity binding ayrı bounded SQLite projection’da checksum’li ve atomik persist/replay ediliyor; duplicate/conflict, immutable successor, terminal state, tamper ve rollback sınırları doğrulandı. Replay core event/order/balance üretmez. Odak `5/5`, tam ve optimize suite `478/478 PASS`; compile/workspace PASS. MARKET core binding, conditional/order-list ve mutation kapalıdır.

- 2026-09-16 P2.03 MARKET execution identity/reconciliation mikro-fazı tamamlandı: exact `MarketFill`, `MATCHED` lookup, `ACCEPTED`/`DUPLICATE` stream kararı ve birebir venue/Spot/order/execution kimlikleri in-memory binding’e bağlandı. Quarantine, conflict, not-found ve farklı payload fail-closed. Odak `3/3 PASS`; MARKET core binding `DEFERRED / NO-GO`, durable replay `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.

- 2026-09-16 P2.03 MARKET/BASE_QUANTITY mikro-fazı tamamlandı: explicit base miktarlı MARKET için immutable exact ekonomik sözleşme eklendi. Her fill base/quote/effective price/fee/asset taşır; BUY/SELL slippage, partial fill, residual, terminal coverage ve duplicate/conflict fail-closed doğrulandı. `quoteOrderQty`, core binding, gerçek MARKET emri, mutation ve mainnet açılmadı. Odak `6/6`, tam ve optimize suite `470/470 PASS`; compile/workspace/manifest/diff PASS. Kanıt: `evidence/P2.03/MARKET_CONDITIONAL_ORDER_LIST_CONTRACT_SONUC.md`.

- 2026-09-15 security scan: one LOW CWE-400 historical validation body-buffering finding was remediated with the shared streaming limiter and chunked early-cut regression. Local gates: Python 459/459, optimized 459/459, compileall/workspace/frontend build/release manifest PASS. Local Browser E2E PASS; live venue mutation remains closed. Lisanssız erişilebilirlik yolunda NVDA `PASS / USER_CONFIRMED`, Narrator `PASS / USER_CONFIRMED`, Windows HCM `PASS / LOCAL_UI`; JAWS yalnız opsiyonel ek doğrulamadır.

Audit baseline: `7965392`; target branch is public `origin/main`. P2.05 read-only acceptance passed `29/29`; the current audit-remediation regression target is `459/459`, with compileall, workspace, release-manifest and frontend production build gates PASS.

NVDA ücretsiz doğrulaması kapandı: NVDA açıkken 28/28 keyboard focus durağı ve DOM/landmark/form/status/table/disclosure sözleşmesi PASS; kullanıcı sesli çıktıyı onayladı. Narrator aynı akışta 27/28 görünür focus ölçümüyle kullanıcı sesli çıktısı onaylandı ve `PASS / USER_CONFIRMED` kaydedildi; teknik body-döngüsü sınırı kanıtta korundu. JAWS `NOT_RUN` ve opsiyonel.

Windows High Contrast testi kullanıcı onayıyla gerçek Windows Ayarları ekranında tamamlandı: `Gece gökyüzü` altında DCABOT `forced-colors: active`, 9 heading, 4 landmark, 21 control, yatay taşmasız (`1390=1390`) ve temiz konsol ile doğrulandı; tema test sonunda `Yok` olarak geri yüklendi. HCM `PASS / LOCAL_UI`; Narrator kullanıcı onayıyla `PASS / USER_CONFIRMED`; JAWS `NOT_RUN` ve opsiyonel.

The P2.03 lifecycle-to-core binding exists in `a60ef1f`; the current working slice adds its offline durable replay journal, redacted reconciliation association, fail-closed coordinator restart hydration, explicit authoritative snapshot gate, AttemptStore recovery orchestration, bounded post-recovery lookup handoff, and verified external-review fixes. P1.19.g adds a minimal frontend component-test runtime and `12/12` critical-flow tests plus a passing local Browser E2E flow. Neither activates live Binance REST/WS, signed account, mutation, live recovery, or mainnet.

Current gate: External-review remediation plus the Buffy HATA report review, offline reconciliation-result evidence binding, exact venue-event identity contract, non-economic venue-to-Spot mapping candidate persistence/replay and independently reviewed explicit verified-mapping admission are locally closed; full P2.03/P2.04 remain `IN_PROGRESS`; trading activation `NO-GO`.

The Buffy HATA report was checked against current source and tests. `_quality_response()` was normalized to one JSON response type with `Cache-Control: no-store`; hydration `FAILED` precedence received a focused regression test. The report’s stale quality-parser and frontend state-count claims were not implemented; config caching remains deferred; CORS, SQLite path ownership and multi-worker state remain P3.01 deployment gates. The offline reconciliation slice added redacted lookup-result evidence with idempotent conflict handling and legacy-payload readability, then added exact `UserDataEvent ↔ OrderLookup` classification and a non-economic mapping candidate; neither promotes lookup outcomes to fills or core postings.

Next safe action: MARKET core binding’i açmamak; limitten bağımsız ekonomik event şeması, core authority ve bağımsız oracle kabul edilmeden `DEFERRED / NO-GO` korumak. Yeni order-list/OCO implementation’ı da açılmayacak; list/leg identity, working/pending coordination, cancellation confirmation, replacement identity ve atomic restart/replay owner sözleşmesi ürün/venue kanıtıyla ayrıca kabul edilmeden `DEFERRED / NO-GO` kalacak. Live signed integration ve Testnet mutation kapalı; mutation ayrı açık kullanıcı yetkisi ister. Frontend component tests, local Browser E2E, NVDA, Narrator ve Windows HCM ücretsiz kabul yolu PASS; JAWS opsiyonel ve NOT_RUN.

2026-09-16 güncel karar: P2.03/P2.04 offline lifecycle, durable replay, reconciliation evidence binding ve explicit LIMIT admission yerel olarak kapalıdır (`LOCAL_PASS`). MARKET → core ekonomik binding ve gerçek venue conditional/order-list/OCO lifecycle `DEFERRED / NO-GO` kalır; conditional stop/exit trigger → fill ayrımı için yalnız sınırlı offline regresyon kanıtı eklendi, yeni ekonomik kod eklenmedi. Binance resmi sözleşme araştırması, MARKET için effective-price/quote-to-base/cumulative-quote/slippage; conditional için trigger-to-execution/gap/cancel; order-list için list/leg identity/coordination/restart atomicity gereksinimlerini doğruladı. Yeniden açılma sırası: `MARKET/BASE_QUANTITY` → conditional trigger/execution → order-list/OCO; `quoteOrderQty` ilk dilimde yoktur. Kanıt: `docs/YOL_HARITASI.md`, `evidence/P2.03/MARKET_CONDITIONAL_ORDER_LIST_CONTRACT_SONUC.md`, `evidence/P2.03/DURABLE_BINDING_SONUC.md`.

2026-09-16 dış araştırma raporlarının güncel checkout karşılaştırması tamamlandı. Arena legacy revision nedeniyle `REJECTED / STALE`; Claude/Sol’un preview fiyatı, funding işareti, manifest/cache sınırı, frontend testleri ve journal erişimi maddeleri mevcut kod/testlerle kapalıdır. Negatif fee red önerisi, güncel rebate kullanımını gösteren core regression nedeniyle `REJECTED / EXISTING CONTRACT`; gerçek venue maksimum fee policy’si `DEFERRED`. API ayrıştırması, coverage/static kalite, wheelhouse/SBOM, semantic event tipleri ve deployment ownership `DEFERRED/P3.01`; live trading, MARKET/conditional/order-list binding ve otomatik retry/multi-exchange `NO-GO`. Bu yeniden değerlendirmede yeni ekonomik kod veya dış kaynak eklenmedi; tam ve optimize suite `459/459 PASS`. Kanıt: `docs/YOL_HARITASI.md`.

2026-09-16 P2.02.c tamamlandı: Windows Credential Manager üzerinde yalnız HMAC generic credential saklama/okuma sınırı ve secret echo etmeyen `tools/configure_testnet_credential.py` yardımcı programı eklendi. Gerçek Binance anahtarı okunmadı; dummy round-trip/redaction ve desteklenmeyen key family fail-closed odak testleri PASS. Kullanıcı kendi makinesinde `uv run --frozen python tools/configure_testnet_credential.py testnet-readonly` komutuyla API key ve secret’ı girmelidir; değerler sohbete, Git’e veya loga aktarılmayacaktır. Signed account HTTP, gerçek REST/WS ve mutation hâlâ `NO-GO`.

2026-09-16 P2.02.d tamamlandı: Kullanıcının yerel Credential Manager kaydı yalnız imzalı, sabit `GET /api/v3/account` read-only adapter’ında kullanıldı. Gerçek Testnet çağrısı `SPOT` account, `SPOT` permission ve `SIGNED_ACCOUNT_CONTEXT` capability ile geçti; bakiye değerleri hiçbir çıktı/repr/persistence’e alınmadı. Sahte taşıma odak testi `3/3 PASS`; gerçek çağrı `LIVE_READ_ONLY_PASS`. Emir, mutation, WebSocket, reconciliation ve mainnet kapalı; tam P2.02 kabulü verilmedi.

---

## P1.02.a — Yerel CSV/ZIP kalite raporunun ilk dikey dilimi

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. P1.02.a tamamlandı; bağımsız faz incelemesi açık bırakıldı. Sıradaki en küçük davranış P1.02.b'dir.

## Tek davranış

Kullanıcı local CSV veya ZIP dosyasını veri merkezine verir; backend dosyayı güvenli biçimde okur ve sessiz kabul yerine sembol, kolon, timestamp, duplicate, gap ve satır kalite raporu üretir. Bu alt dilim alan eşleme ekranından önce yalnız güvenli okuma + deterministik kalite sonucunu kapsar; credential, public downloader ve gerçek emir yolu yoktur.

## Sınırlı okuma ve değişim

AGENTS/STATE; docs/VERI_VE_SIMULASYON veri sözleşmesi; docs/MIMARI data_adapters sınırı; docs/OZELLIK_MATRISI F25. Kod: `tools/check_workspace.py`, mevcut `src/dcabot` sınırları ve test fixture yaklaşımı. Önce yedek kapsam dışı; `YEDEK_ESKI_PROJE` okunmaz.

Gerçekleşen yollar: `src/dcabot/data_adapters/quality.py`, `src/dcabot/server/api.py` altında `POST /api/data-quality`, `tests/data/test_quality.py` ve `tests/api/test_data_quality.py`. Dosya yalnız proje dışına taşmadan okunur; ZIP içindeki yol traversal, boyut, uzantı, encoding ve malformed CSV reddedilir. Kalıcı dataset kaydı bu alt dilimin dışındadır.

## Kabul

1. Güvenli local CSV okunur; dosya adı/satır sayısı/byte sınırı raporlanır.
2. CSV/ZIP içeriğinde izinli tek veri dosyası seçilir; path traversal, çoklu belirsiz aday ve bozuk dosya reddedilir.
3. Header, required alanlar, timestamp birimi/UTC, duplicate ve sıralı gap bulguları deterministik raporlanır.
4. Malformed veya unsupported input sessizce başarıya çevrilmez; alan/kategori bazlı hata döner.
5. Python odak test + API contract testi gerçek parser sonucunu doğrular; fixture dışı yedek taranmaz.

Kapanış: P1.02.a parser/API kanıtı `evidence/P1.02.a/SONUC.md` altında tutulur. P1.02.b alan eşleme + kalite ekranı başlamadan P2 testnet’e atlanmaz. UI/UX yönünde kapsam genişletme veya dış görsel araştırma ihtiyacı doğarsa önce kullanıcıya danışılır.

## P1.02.b — Sıradaki tek iş

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.02.b/SONUC.md`.

Gerçekleşen küçük davranış: local CSV/ZIP seçimi, kalite raporunun ekranda gösterimi, exact canonical mapping, ham şema için Bar/Trade seçimi, manuel mapping ve eksik/çakışan mapping reddi. P1.02.a parser sonucu yeniden hesaplanmadı; kalıcı import yapılmadı.

## P1.03.a — Public kaynak sözleşmesi ve indirme doğrulama hazırlığı

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.03.a/SONUC.md`.

Gerçekleşen küçük davranış: registry’ye açıkça kayıtlı public source için HTTPS/host/path/filename allowlist kontrolü, immutable download planı, SHA-256/byte metadata’sı ve diske yazmadan payload doğrulaması. Güncel Binance URL/checksum kayıtları doğrulanmadan aktif kaynak eklenmedi.

## P1.03.b — Sıradaki tek iş

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.03.b/SONUC.md`.

Gerçekleşen küçük davranış: Kullanıcı tarafından doğrulanan Binance Spot `BTCUSDT/1h` 2025-01-01 ZIP’i registry’ye sabit hash/byte/iç CSV metadata’sıyla eklendi. HTTPS indirme response’u bounded streaming ile alınır; Content-Length/Content-Encoding, byte sayısı, SHA-256, ZIP CRC, üye yolu, symlink, üye/açılım sınırı ve beklenen CSV adı doğrulanmadan final cache yayınlanmaz. Başarılı payload content-addressed ZIP + metadata olarak atomik biçimde cache’e alınır; aynı doğrulanmış plan ağ çağrısı olmadan cache hit döner. Checksum/redirect/network retry orkestrasyonu ve katalog/UI bu dilimin dışındadır.

## P1.03.c — Sıradaki tek iş

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.03.c/SONUC.md`.

Gerçekleşen küçük davranış: Explicit dataset definition’lar yerel cache durumuyla birleştirilerek dataset ID, source, sembol, interval, `[başlangıç,bitiş)` dönemi, beklenen SHA-256, byte, artifact adı ve `MISSING/CORRUPT/VERIFIED` bütünlük durumu listelenir. `select(dataset_id)` yalnız expected hash ve güvenli ZIP doğrulaması geçmiş artifact’ın path’ini parser/application portuna aktarır; bilinmeyen, eksik veya bozuk dataset seçilemez. UI, HTTP endpoint, download job orchestration ve credential kapsam dışıdır.

## P1.03.d — Sıradaki tek iş

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.03.d/SONUC.md`.

Gerçekleşen küçük davranış: `GET /api/datasets` explicit katalog tanımlarını deterministic sırayla ve `MISSING/CORRUPT/VERIFIED` durumlarıyla döndürür. `PUT /api/dataset-selection` strict dataset ID alır; bilinmeyen ID’yi 404, bilinen fakat seçilemeyen cache’i 409 döndürür ve yalnız fresh VERIFIED artifact için path içermeyen selection DTO üretir. Yeni endpoint’ler `Cache-Control: no-store` kullanır, download/network başlatmaz ve mevcut endpoint’lerin hata sözleşmesini değiştirmez. Loopback çalıştırma README’deki `127.0.0.1` komutuyla korunur; yeni runtime dependency eklenmedi.

## P1.03.e — Sıradaki tek iş

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.03.e/SONUC.md`.

Gerçekleşen küçük davranış: Katalog API’si mevcut P1.02 ekranına bağlandı. UI explicit dataset listesini okur; `ALL/VERIFIED/MISSING/CORRUPT` filtreleri, semantik tablo ve sağ detay paneliyle dataset type, enstrüman, interval, dönem, artifact boyutu ve kısaltılmış hash’i gösterir. `MISSING` ve `CORRUPT` seçim eylemleri kapalıdır; yalnız `VERIFIED` için `PUT /api/dataset-selection` çağrısı yapılır. Parser/application durumu, mevcut API’nin aktarımı başlatmadığı açıkça belirtilerek gösterilir. İndirme, URL/path, credential, progress/cancel/retry job ve testnet eklenmedi. Görsel karar, kullanıcı tarafından sağlanan anonim rapordaki tablo + sağ detay paneli önerisiyle sınırlı tutuldu.

## P1.03.f — Sıradaki tek iş

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.03.f/SONUC.md`.

Gerçekleşen küçük davranış: Mevcut bounded downloader’a iptal/progress hook’ları eklendi; in-memory job yöneticisi `QUEUED/RUNNING/RETRYING/SUCCEEDED/FAILED/CANCELLED` durumlarını, sınırlı retry’ı ve dataset başına tek aktif job sahipliğini yönetiyor. `POST /api/dataset-downloads`, `GET /api/dataset-downloads/{job_id}` ve `POST /api/dataset-downloads/{job_id}/cancel` yalnız explicit katalog `dataset_id` ile çalışıyor. Job response’ları progress ve güvenli hata kodu taşır; URL/path/credential içermez. Verified cache yayımlama mevcut atomik/hash/ZIP doğrulama akışından geçer.

## P1.03.g — Katalog download job UI

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.03.g/SONUC.md`.

Gerçekleşen küçük davranış: Sağ detay panelindeki tek `LOCAL COPY` kartı, yalnız explicit registry dataset’i için indirme başlatır; `MISSING` ve `CORRUPT` durumlarında başlatma, `QUEUED/RUNNING/RETRYING` durumlarında bounded progress + deneme bilgisi + iptal, `FAILED/CANCELLED` durumlarında güvenli hata ve tekrar deneme eylemi gösterilir. Başarılı job sonrası katalog yeniden okunur ve `VERIFIED` selection akışı korunur. Polling hatası terminal başarısızlık sayılmaz; backend faz/ETA üretmediği için UI bunları uydurmaz. Serbest URL, credential, testnet/live emir eklenmedi.

## P1.04.a — Sıradaki tek iş

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.04.a/SONUC.md`.

Gerçekleşen küçük davranış: Verified katalog selection capability’si salt-okunur application use case üzerinden header’sız Binance kline satırlarını immutable canonical bar tuple’ına dönüştürüyor. OHLCV değerleri exact decimal string, zamanlar integer microseconds/UTC, source kimliği ve artifact hash/byte metadata’sı input’a bağlı; path, URL, credential ve ekonomik hesap yok. Bar sırası, dönem sınırı, kapanış aralığı, OHLC sınırı, ham kolon sayısı ve bounded row sayısı doğrulanıyor.

## P1.04.b — Verified dataset preflight özeti

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.04.b/SONUC.md`.

Gerçekleşen küçük davranış: Verified canonical input için mevcut katalog detayında salt-okunur koşu öncesi özet gösteriliyor. Backend parser/application sınırından enstrüman, interval, `[başlangıç,bitiş)` dönemi, UTC microseconds standardı, gerçek bar sayısı ve artifact bütünlüğü alınarak path/URL/credential dışı bir preflight DTO’suna bağlanıyor. UI `READY`, yükleniyor ve güvenli hata durumlarını; `UNKNOWN` veri kalitesi durumunu; klavye ile açılabilen bütünlük ayrıntılarını ve 390px taşmasız görünümü gösteriyor. Koşu başlatma, ekonomik hesap tekrarı, import ve emir yolu eklenmedi.

## P1.04.c — Sıradaki tek iş

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.04.c/SONUC.md`.

Gerçekleşen küçük davranış: Verified dataset preflight’i aktif `config/paper.json` ile salt-okunur tarihsel koşu planına bağlandı. Application katmanı offline config’i tekrar doğruluyor, dataset sembol uyumunu kontrol ediyor ve exact finansal string alanlarıyla deterministik config hash’i üretiyor. API `SIMULATED`, `NOT_STARTED`, `read_only` ve dataset preflight’ini aynı response’ta döndürüyor. UI mevcut preflight kartında aktif config snapshot’ını ve koşunun henüz başlatılmadığını gösteriyor. Simülasyon çalıştırma, sonuç kaydı ve yeni UI aksiyonu eklenmedi.

## P1.04.d — Bounded tarihsel koşu doğrulaması

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.04.d/SONUC.md`.

Gerçekleşen küçük davranış: `POST /api/historical-runs/validate` yalnız explicit dataset ID, current artifact SHA-256, current config hash ve `SIMULATED` kabul eder. Server kendi güncel VERIFIED preflight ve offline config bağlamını karşılaştırır; stale artifact/config, dataset-config çatışması, offline gate ve bar sınırı fail-closed reddedilir. Strict request/response DTO, 4 KiB body sınırı, güvenli Problem Details, `no-store` ve path/URL/credential/arbitrary config dışlama korunur. Endpoint run oluşturmaz, job başlatmaz, simülasyon çalıştırmaz, persistence/cache write yapmaz ve UI aksiyonu eklemez.

## P1.04.e — Offline tarihsel simülasyon başlatma

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.04.e/SONUC.md`.

Gerçekleşen küçük davranış: Güncel VERIFIED dataset preflight ve aktif offline config hazır olduğunda UI, `OFFLINE / TARİHSEL / SIMULATED` kapsamını görünür kılar; erişilebilir onay adımından sonra strict `POST /api/historical-runs/simulate` çağrılır. Application katmanı en fazla 1.000 kapalı barı `historical_ohlcv_v1` modeliyle, mevcut core reducer’a delegasyon ve deterministik fee/slippage sınırıyla işler. Safety/TP aynı OHLC barında birlikte erişilebiliyorsa o bar commit edilmeden `INDETERMINATE / AMBIGUOUS_OHLC_PATH` döner. UI yalnız completed/indeterminate/error durumunu bildirir; sonuç grafiği, işlem tablosu, persistence, network emir veya credential eklenmedi. Gerçek artifact + mevcut `config/paper.json` smoke’unda reducer’ın `max_entry_notional` politikası nedeniyle 422 güvenli hata görüldü; config sessizce değiştirilmedi.

## P1.05.a — Minimal güvenli tarihsel sonuç özeti

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.05.a/SONUC.md`.

Gerçekleşen küçük davranış: Mevcut `historical_ohlcv_v1` response’u UI’da yeni finansal hesap yapılmadan gösteriliyor. `COMPLETED` sonuçta backend’den gelen realized net after all costs, fee, position status, işlenen bar, dataset dönemi, model ve kısaltılmış config/artifact hash görünür. `OPEN_AT_END`, funding `NOT_MODELED`, mark `NOT_AVAILABLE`, forced close yokluğu ve `persisted=false` açıkça belirtiliyor. `INDETERMINATE` durumda ekonomik özet başarı gibi gösterilmiyor; ambiguity açıklaması korunuyor. Grafik, action/trade table, equity curve, ROI/risk metrikleri, persistence, credential ve network emir eklenmedi.

## P1.05.b — Read-only action/trade table

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.05.b/SONUC.md`.

Gerçekleşen küçük davranış: Mevcut `actions` alanından read-only aksiyon geçmişi eklendi. Masaüstünde semantik tablo; dar ekranda yatay taşma üretmeyen kart/liste düzeni kullanılıyor. `bar_index`, backend’in ham `role` değeri, `open_time_us`, `fill_price`, `quantity` ve `fee` aynen gösteriliyor; frontend finansal hesap yapmıyor. `INDETERMINATE` durumda tablo gösterilmiyor; `OPEN_AT_END` için sahte kapanış aksiyonu eklenmiyor. Grafik, marker, OHLCV response genişletmesi, yeni endpoint, chart dependency, ekonomik detay genişletmesi ve persistence eklenmedi.

## P1.05.c — Grafik veri sözleşmesi araştırma kapısı

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.05.c.1/SONUC.md`.

Gerçekleşen küçük davranış: Ayrı ve salt-okunur `GET /api/datasets/{dataset_id}/chart-data` endpoint’i ile bounded canonical chart data sözleşmesi eklendi. DTO yalnız verified dataset metadata’sını, `bar_index`, `open_time_us`, `close_time_us` ve exact OHLC stringlerini taşır. `volume`, `is_closed`, marker, grafik UI’si, persistence/run_id ve yeni chart dependency eklenmedi. Endpoint `no-store`, strict/frozen Pydantic model, dataset preflight ve 1.000 bar sınırını korur. P1.05.b action table mevcut sözleşmesiyle korunuyor.

## P1.05.c.2 — Minimal grafik render araştırma kapısı

Durum: COMPLETE / LOCAL_PASS_WITH_LIMITATION; review: NOT_RUN. Kanıt: `evidence/P1.05.c.2/SONUC.md`.

Gerçekleşen küçük davranış: P1.05.c.1 chart contract değişmeden, yalnız `COMPLETED` simülasyon sonrası mevcut `/api/datasets/{dataset_id}/chart-data` endpoint’inden veri alan native inline SVG nötr OHLC overview eklendi. Renderer backend sırasını koruyor; bounded 1.000 bar guard’ı, exact decimal string kaynağı, fixed-point display coordinate mapping, flat-domain/invalid payload fail-closed davranışı, accessible figure/image açıklaması ve 320px taşmasız görünüm var. Marker, tooltip, crosshair, zoom/pan, aggregation/downsampling, yeni endpoint/dependency, frontend finansal hesap ve persistence eklenmedi. `INDETERMINATE`/`AMBIGUOUS_OHLC_PATH` grafik göstermiyor; action table korunuyor.

## P1.05.c.3 — Action marker araştırma kapısı

Durum: COMPLETE / LOCAL_PASS_WITH_LIMITATION; review: NOT_RUN. Kanıt: `evidence/P1.05.c.3/SONUC.md`.

Gerçekleşen küçük davranış: Kullanıcı tarafından sağlanan anonim action marker araştırmasına göre mevcut `simulation.actions` ile `HistoricalChartData.bars` aynı dataset/artifact/bar kapsamı kimliği altında doğrulanıyor. `bar_index` aynı canonical equal-slot x yardımcısıyla marker merkezine bağlanıyor; `open_time_us` yalnız exact consistency check olarak kullanılıyor. Marker statik ve nötr bir circle glyph; sabit annotation lane’de çiziliyor, `pointer-events:none`, focus/tabindex/tooltip/hover/crosshair/zoom/pan yok. Duplicate, out-of-range, timestamp mismatch veya kimlik uyuşmazlığında yalnız marker katmanı fail-closed kapanıyor ve action table ayrıntı/fallback olarak kalıyor. `INDETERMINATE` sonuçta mevcut davranış korunuyor; `OPEN_AT_END` için sahte exit eklenmiyor. Backend, yeni endpoint, persistence, dependency ve frontend finansal hesap eklenmedi.

P1.05.c.2 chart contract ve static OHLC renderer korunur. Aktif gerçek config ile başarı sonucu üretilemediği için marker’ın canlı `COMPLETED` örneği browser’da sentetik veri olmadan doğrulanmadı; build ve güvenli hata/responsive QA PASS olarak kaydedildi. Sıradaki alt faz için marker etkileşimi veya kapsamlı finansal görünüm otomatik başlatılmayacak; ayrıca karar/araştırma kapısı gerekir.

## P1.05.d — Minimal ekonomik sonuç özeti araştırma kapısı

Durum: COMPLETE / LOCAL_PASS_WITH_LIMITATION; review: NOT_RUN. Araştırma girdisi: `P1.05.d_Minimal_Ekonomik_Sonuc_Detayli_Arastirma_Raporu.md`. Kanıt: `evidence/P1.05.d/SONUC.md`.

P1.05.a mevcut sonuç özeti, P1.05.b action table ve P1.05.c chart/marker katmanı korunuyor. Mevcut kod/contract clarification ile yalnız backend’den gelen `realized_gross`, `fees`, `realized_net_after_all_costs` ve `position_status` değerleri, explicit `quote_asset` etiketiyle gösteriliyor. `unrealized`, `equity`, numeric funding, ROI, drawdown, Sharpe/Sortino/CAGR, equity curve, benchmark, export ve frontend finansal hesaplama bu faza alınmadı. `OPEN_AT_END`, mark/funding ve `persisted=false` sınırlamaları metinsel olarak görünür; `INDETERMINATE` özeti gizli kalır.

## P1.06 — Kalıcı tarihsel koşu ve tekrar üretme araştırma kapısı

Durum: IN_PROGRESS; araştırma raporu değerlendirildi. Kanıt: `evidence/P1.06.a/SONUC.md`. Anonim araştırma girdisi: `P1.06_Persistent_Run_Detayli_Arastirma_Raporu_2026-09-08.md`.

Raporun kararları proje talimatı değil, doğrulanacak kanıt/öneri kaynağı olarak işlendi. P1.06.a’da persistence yazmadan önce bounded canonical input/config/result snapshot, explicit `USDT` monetary unit, action `raw_reference` güvenlik doğrulaması ve execution identity hash’leri hazırlandı. Yeni modül `src/dcabot/application/historical_run_contract.py` yalnız canonical capture üretir; SQLite, HTTP save/list/detail/reproduce, frontend persistence ve `run_id` henüz yoktur. P1.06 genel kabulü için dedicated store ownership, atomicity/corruption/migration, runtime benchmark ve API/UI mikro dilimleri sırayla kanıtlanacaktır.

### P1.06.b — Dedicated SQLite run-store ve backend save/reopen

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.06.b/SONUC.md`.

P1.06.a capture bileşenleri ayrı versioned SQLite run store’a bağlandı. Store path ownership, foreign DB reddi, rollback journal/FULL synchronous ayarı, immutable transaction insert, UUIDv4 run ID, source execution idempotency/conflict, record checksum, corruption isolation ve bounded deterministic list sınıf seviyesinde doğrulandı. HTTP endpoint, frontend, reproduction, compare, delete ve backup eklenmedi.

### P1.06.c — Explicit application/API save

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.06.c/SONUC.md`.

`POST /api/historical-runs/simulate` artık server-side bounded ephemeral execution registry’ye bir capture bağlayıp güvenli `execution_id` döndürüyor. `POST /api/historical-runs` istemciden result/config kabul etmeden yalnız bu mevcut execution capture’ını dedicated store’a kaydediyor. İlk save `201`, aynı execution retry’ı `200` ve aynı `run_id` döndürüyor; bilinmeyen execution store oluşturmadan `404 EXECUTION_NOT_FOUND` veriyor. `COMPLETED`/`INDETERMINATE`, `persisted=false`, secret/path/url dışı payload ve 4 KiB request sınırı RED→GREEN test edildi. UI, list/detail, reproduction, compare, delete ve backup eklenmedi.

### P1.06.d — Bounded list/detail read API

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.06.d/SONUC.md`.

Dedicated store’daki immutable kayıtlar için bounded deterministic `GET /api/historical-runs` list ve `GET /api/historical-runs/{run_id}` read-only detail/reopen API’si eklendi. Eksik store listede boş sonuç döndürürken dosya oluşturmaz; list limit’i 1..100 bounded; corrupt kayıt health’i korunur; invalid/not found/corrupt durumları Problem Details sözleşmesindedir; detail allowlist dışı path/url/secret anahtarlarında fail-closed olur ve 256 KiB response bütçesini aşamaz. Store tarafında valid checksum’e rağmen eksik nested alanlar da exception yerine `CORRUPT` olarak ayrıştırılır. UI, reproduction, compare, delete ve backup eklenmedi.

### P1.06.e — Saved Run UI

Durum: COMPLETE / LOCAL_PASS_WITH_LIMITATION; review: NOT_RUN. Kanıt: `evidence/P1.06.e/SONUC.md`. Araştırma girdisi: `P1.06.e_Saved_Run_UI_UX_Detayli_Arastirma_Raporu_2026-09-08.md`.

Mevcut React uygulamasına en küçük dikey dilimde `POST /api/historical-runs` save, `GET /api/historical-runs` bounded liste ve `GET /api/historical-runs/{run_id}` salt-okunur detay bağlandı. Ayrı Saved Runs navigasyonu, boş/yükleniyor/hata durumları, masaüstü semantik tablo, 320px stacked görünüm, `INDETERMINATE` uyarısı ve `CORRUPT` fail-closed ayrımı uygulandı. Detay snapshot’ları native disclosure içinde gösterilir; client-side finansal hesap, round/normalize, edit, delete, re-run, export, compare ve grafik eklenmedi. `COMPLETED` nötr durum olarak gösterilir; save feedback’i `201`/`200` idempotent ayrımını korur. Frontend build, 109/109 backend regresyonu, compile, workspace ve Browser/IAB desktop+320px QA PASS. Gerçek local cache/store boş olduğu için canlı save-success zinciri sentetik veriyle doğrulanmadı; bu sınırlama kanıtta açık bırakıldı.

### P1.06.f — Uyumlu historical profile ve gerçek backend save kanıtı

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.06.f/SONUC.md`. Araştırma girdisi: `P1.06.f_Uyumlu_Historical_Config_Detayli_Arastirma_Raporu_2026-09-08.md`.

Raporun `paper` config’i koruma ve ayrı explicit profile önerisi kabul edildi; rapordaki demo miktarları gerçek artifact üzerinde bağımsız test edildi. `config/historical_demo_btcusdt_1h_v1.json` ve kayıtlı profile registry eklendi. API run-plan, validation ve simulation request’leri explicit `profile_id` taşır; response ve immutable execution identity profile/provenance alanlarını echo eder. Gerçek artifact ile `historical_demo_btcusdt_1h_v1` backend zinciri `COMPLETED → temporary save → detail` olarak geçti. `paper.json` değişmedi; cap formülü ve anchor davranışı değiştirilmedi. Tam Python regresyonu `113/113 PASS`, frontend build, compile ve workspace PASS. Profile selector UI’sı anonim araştırma raporu sonrasında uygulandı; kanıt: `evidence/P1.06.f.2/SONUC.md`. Re-run, compare, delete, export ve kapsamlı ekonomik görünüm hâlâ kapsam dışıdır.

### P1.06.f.2 — Explicit profile selector UI

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.06.f.2/SONUC.md`. Araştırma girdisi: `P1.06.f.2_Historical_Profile_Secimi_UI_UX_Detayli_Arastirma_Raporu_2026-09-08.md`.

Preflight kartına native `Historical profile` select eklendi. İlk durum boş ve fail-closed; seçim backend `profile_id` ile run-plan’a bağlanıyor. Backend’den gelen insan-okunur label ve `expected_dataset_id` frontend’de yeniden türetilmiyor. Profil değişiminde eski plan/simülasyon/chart/save state’i temizleniyor; `project_fixture` uyarısı kalıcı inline note olarak gösteriliyor. 320px taşma ve browser console kontrolü PASS. Sonraki tek iş plan sırasındaki P1.06.f.2 bağımsız review kapısıdır; review `NOT_RUN` olarak açık bırakıldı.

### P1.07 — Sıradaki tek iş / kısmi fill ve order-event araştırma kapısı

Durum: IN_PROGRESS; P1.07.a, P1.07.b, P1.07.c.1, guarded P1.07.c.2/c.3 ve P1.07.d.1 complete-with-limitation; d.2 ve d.3 DEFERRED. Kanıt: `evidence/P1.07/SONUC.md`.

Kısmi fill, cancel/fill yarışı, limit/stop tetikleme, gecikme, OHLC belirsizliği ve exact ekonomik invariant’lar aynı state-machine’i etkiliyor. P1.07.a.1–a.4 ve P1.07.b fixed-slice dikey dilimleri tamamlandı. P1.07.c.1 ile fixed public response’ta `INDETERMINATE` fail-closed authority, c.2 ile capability-aware prefix action kanıtı, c.3 ile yalnız boundary-only annotation, d.1 ile bağımsız strict fixed-limit application policy uygulandı; incomplete persistence, volume/latency/queue/stop ve aynı-bar cancel-fill yarışı değiştirilmedi. Public limit contract d.2, mevcut DCA strategy binding kanıtlanmadığı için ertelendi. Sıradaki tek kapı `P1.07.d.3` DCA strategy binding araştırmasıdır.

### P1.07.a — Mevcut Core partial-fill uyumluluk audit kapısı

Durum: COMPLETE / LOCAL_PASS; araştırma kararı `SIMPLIFIED`. Kanıt: `evidence/P1.07/SONUC.md`. Prompt: `docs/P1.07.a_Mevcut_Core_Partial_Fill_Uyumluluk_Arastirma_Promptu.md`.

P1.07 raporu mevcut reducer ile karşılaştırıldı. Reducer manuel partial `FILL` ve `ORDER_FINAL(CANCELED)` gözlemini taşıyor; historical simulator aynı bar içinde full fill yapıyor, config schema’da explicit slice modeli yok ve persisted action contract’ı lifecycle için yetersiz. Bu audit sonrasında yalnız `Order` üzerinde `PARTIALLY_FILLED`, exact `leaves` ve explicit cancel `canceled` görünümü eklendi; late-fill `UNKNOWN` korundu. Historical model/API/config değişikliği sonraki mikro faza bırakıldı.

### P1.07.a.1 — Core order partial-state görünümü

Durum: COMPLETE / LOCAL_PASS. Kanıt: `evidence/P1.07/SONUC.md`.

`FILL` ile order quantity conservation görünümü açıklaştırıldı: partial fill `PARTIALLY_FILLED`, açık remainder `leaves`, explicit cancel remainder `canceled`. Legacy historical path, reserve, latency, stop ve same-bar race değiştirilmedi. TDD RED→GREEN, late-fill kontrolü, tam `114/114` regresyonu, compile ve workspace PASS. Sonraki tek iş P1.07.a.2’dir.

### P1.07.a.2 — Opt-in historical fixed-slice runner

Durum: COMPLETE / LOCAL_PASS. Kanıt: `evidence/P1.07/SONUC.md`.

Raporun önerdiği `historical_ohlcv_partial_fixed_v1` application runner olarak eklendi. Yalnız explicit `slice_qty`, aynı order’ın çok barlı lifecycle’ı, bar başına tek fill, exact remainder ve EOF’de sentetik cancel yerine `OPEN_AT_END` davranışı var. RED→GREEN, farklı ambiguity/determinism kontrolü, tam `119/119` regresyon, compile ve workspace PASS. Public API/action v2 ve UI henüz bağlanmadı.

### P1.07.a.3 — Fixed-slice public profile/config/response contract

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.07/SONUC.md`.

Yeni application runner strict opt-in `historical_demo_btcusdt_1h_partial_fixed_v1` profile/config ve versioned public response/action contract’ına bağlandı. Fixed model config hash’i execution policy’yi kapsıyor; run-plan/validation için ayrı strict DTO’lar ve lifecycle action alanları var. Legacy `historical_ohlcv_v1`, `paper` profile, legacy run-plan/validation/simulation response’ları ve frontend davranışı korunuyor. Fixed response `execution_id=null`, `persisted=false` ile P1.06 persistence’ından ayrılıyor. TDD RED→GREEN, `121/121` tam regresyon, OpenAPI, compile ve workspace PASS. UI görsel değişikliği yapılmadı.

### P1.07.a.4 — Fixed-slice gerçek ASGI HTTP smoke

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.07/SONUC.md`.

Opt-in fixed profile için gerçek ASGI request/response serileştirmesi ve strict response union smoke kontrol edildi. `1/1 PASS`; `execution_id=null`, `persisted=false` ve lifecycle action alanları doğrulandı. Fixed profile mevcut UI selector’a veya P1.06 save akışına açılmadı.

### P1.07.b — Fixed-slice UI/UX araştırma kapısı

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.07/SONUC.md`. Araştırma girdisi: `P1.07.b_Fixed_Slice_UI_UX_Detayli_Arastirma_Raporu_2026-09-08.md`.

Fixed profile mevcut selector’a explicit opt-in olarak açıldı; model farkı yardımcı metinle anlatılıyor. Onay checkbox’ı işaretlenmeden başlatma engelleniyor ve hata checkbox’a odaklanıyor. Determinate fixed sonuçta backend action lifecycle alanları Original → Cumulative filled → Leaves ana sırasıyla gösteriliyor; teknik kimlik/provenance alanları native disclosure içinde ve kopyalama düğmeleriyle sunuluyor. `INDETERMINATE` durumda ekonomik özet, grafik ve action history gizli kalıyor; frontend belirsizlik üretmiyor. Fixed sonuçta `persisted=false` nedeniyle save CTA kaldırıldı ve kaydedilemez notu gösteriliyor. 320px/390px responsive ölçümleri, keyboard/focus akışı, copy disclosure, frontend build, tam backend `122/122` regresyon, compile, workspace ve Browser/IAB console QA PASS.

### P1.07.c — INDETERMINATE action authority araştırma kapısı

Durum: RESEARCH_RECEIVED; P1.07.c.1 COMPLETE / LOCAL_PASS; P1.07.c.2 COMPLETE_WITH_LIMITATION / LOCAL_PASS. Prompt: `docs/P1.07.c_Indeterminate_Action_Authority_Arastirma_Promptu.md`; c.2 raporu: `P1.07.c.2_Committed_Prefix_Marker_Ayrintili_Arastirma_Raporu.md`.

Kullanıcı araştırması talimat değil, doğrulanacak kanıt olarak değerlendirildi. Raporun `INDETERMINATE` için authority, cutoff, no-final-summary ve marker fail-closed kararları mevcut fixed runner/API ile kontrol edildi. P1.07.c.1’de legacy client’ın yanlış yorumlayabileceği çıplak prefix public response’tan çıkarıldı; c.2’de explicit fixed capability ile prefix kanıtı kontrollü biçimde açıldı. Marker için doğrudan trading-domain kanıtı ve incomplete persistence semantiği bulunmadığından marker/persistence uygulanmadı; `marker_authority=NONE` korunuyor.

### P1.07.c.1 — Fixed indeterminate fail-closed public contract

Durum: COMPLETE / LOCAL_PASS; review: NOT_RUN. Kanıt: `evidence/P1.07/SONUC.md`.

Fixed response’a `complete_execution`, machine-readable `action_authority`, `marker_authority` ve nullable `final_economic_summary` alanları eklendi. `INDETERMINATE / AMBIGUOUS_OHLC_PATH` durumunda application’ın iç prefix’i public DTO’ya sızmaz; ambiguity barı ve sonrası için action/marker/final ekonomik özet yayınlanmaz. Completed fixed result’ta action lifecycle ve ekonomik özet `FULL_RUN` authority ile aynı içerikte kalır. Legacy `historical_ohlcv_v1` response/persistence sözleşmesine bu dilimde alan sızdırılmadı.

RED→GREEN: yeni ambiguity fixture’ı önce dört prefix action’ının çıplak biçimde döndüğünü göstererek başarısız oldu; minimum public DTO filtresi ve authority alanları sonrası odak API `10/10 PASS` verdi. Bağımsız gerçek ASGI response kontrolü aynı fixture’da `actions=[]`, `NONE`, nullable final summary ve eski `summary` alanının yokluğunu doğruladı. Tam regresyon `123/123 PASS`, compile, workspace ve frontend build PASS.

### P1.07.c.2 — Capability-aware committed prefix ve marker

Durum: COMPLETE_WITH_LIMITATION / LOCAL_PASS; bağımsız review: NOT_RUN. Araştırma girdisi: `P1.07.c.2_Committed_Prefix_Marker_Ayrintili_Arastirma_Raporu.md`. Kanıt: `evidence/P1.07/SONUC.md`.

Raporun yalnız doğrulanabilir ve güvenli kısmı uygulandı. Fixed `historical_ohlcv_partial_fixed_v1` için request’e açık `action_authority` capability’si eklendi; varsayılan `NONE` kaldı ve `COMMITTED_PREFIX` legacy `historical_ohlcv_v1` yolunda sessizce yok sayılmak yerine `422 UNSUPPORTED_ACTION_AUTHORITY` ile reddedildi. Explicit prefix isteğinde yalnız ambiguity öncesi backend action snapshot’ları döner; `event_sequence`, cutoff bar/zaman/event ve `PREFIX_ONLY` kapsamı görünürdür. `complete_execution=false`, `complete_history=false`, `final_economic_summary=null`, `marker_authority=NONE` ve ambiguity/post-ambiguity action guard’ları korunur. UI’da prefix eylemleri ayrı, salt-okunur “PREFIX KANITI” tablosunda gösterilir; normal action marker çizilmez.

Raporun doğrudan finansal marker kanıtı olmadığından prefix marker, persistence ve incomplete run save/reopen bu mikro dilime alınmadı. Legacy default response, fixed completed `FULL_RUN` sonucu ve P1.06 persistence akışı korunuyor.

Doğrulama: odak API `11/11 PASS`; tam Python regresyonu `124/124 PASS`; frontend `npm run build PASS`. c.2’nin sonraki marker authority kapısı c.3’te boundary-only kararıyla kapanmıştır; limit/stop/gecikme gibi ekonomik davranışlar için ayrı araştırma gereklidir.

### P1.07.c.3 — Marker authority araştırması ve boundary-only uygulaması

Durum: COMPLETE_WITH_LIMITATION / LOCAL_PASS; bağımsız review: NOT_RUN. Araştırma girdisi: `P1.07.c.3_Marker_Authority_Ayrintili_Arastirma_Raporu.md`. Kanıt: `evidence/P1.07/SONUC.md`.

Raporun `SIMPLIFY` kararı uygulandı: `INDETERMINATE + COMMITTED_PREFIX` için normal trade/action marker eklenmedi. Bunun yerine API’de `marker_authority=PREFIX_BOUNDARY_ONLY` ve `marker_kind=INCOMPLETE_BOUNDARY` ayrımıyla yalnız ambiguity barı başlangıcında nötr, çizgili ve metin etiketli boundary annotation gösteriliyor. Boundary; dataset/artifact, ambiguity bar/zamanı, committed cutoff, action count, event sequence, bar index ve action timestamp invariant’larını geçmeden çizilmiyor. Geçemezse yalnız annotation layer kapanıyor; OHLC chart, warning ve geçerli prefix tablosu korunuyor.

UI’da boundary interaktif değil, tooltip/crosshair/hover/focus/animasyon yok; görünür `INCOMPLETE · BAR n` etiketi, caption ve screen-reader açıklamasıyla destekleniyor. Grafik yalnız explicit prefix authority’de indeterminate sonuca açılıyor; `OPEN_AT_END`, legacy response, persistence ve ekonomik hesap değişmedi. Prefix action’ları price chart üzerinde marker olarak çizilmedi.

Doğrulama: ilk TypeScript build kontrolü event sequence type guard hatasını yakaladı; düzeltme sonrası frontend `npm run build PASS`. Odak API `11/11 PASS`; tam Python regresyonu `124/124 PASS`; `compileall PASS`; `tools/check_workspace.py PASS`. Sonraki tek iş P1.07 içindeki limit/stop/gecikme gibi yeni ekonomik davranışlar için ayrı kanıt kapısıdır.

### P1.07.d — Tarihsel limit trigger/fill araştırma kapısı

Durum: RESEARCH_RECEIVED; d.1 application mikro dilimi COMPLETE / LOCAL_PASS. Anonim araştırma promptu: `docs/P1.07.d_Limit_Order_Trigger_Fill_Arastirma_Promptu.md`; rapor: `P1.07.d_Limit_Order_Trigger_Fill_Ayrintili_Arastirma_Raporu.md`.

Bu kapı yalnız OHLCV üzerinde limit order placement zamanı, touch/equality trigger kuralı, gap/open dolum fiyatı, exact fixed-slice/remainder uyumu ve EOF davranışını inceler. Stop, cancellation yarışı, latency, queue, volume participation, persistence, UI ve kapsamlı ekonomik metrikler bu kapının dışındadır. Raporun `SIMPLIFY` kararıyla yalnız explicit, bağımsız application policy dilimi açıldı; legacy veya mevcut public fixed profile’a bağlanmadı.

### P1.07.d.1 — Explicit fixed-limit application policy

Durum: COMPLETE / LOCAL_PASS; bağımsız review: NOT_RUN. Kanıt: `evidence/P1.07/SONUC.md`.

Yeni `src/dcabot/application/historical_fixed_limit.py` modülü yalnız explicit `FIXED_LIMIT_STRICT_V1` policy’sini uygular: placement barı eligible değildir; sonraki canonical barlar değerlendirilir; BUY için `low < limit`, SELL için `high > limit` strict penetration sentetik fill gözlemi verir; equality yalnız `EQUALITY_TOUCH` observation olarak kalır; fill exact `limit_price` ile bir fixed slice’tır; bar başına tek fill, exact remainder ve EOF’de `OPEN_AT_END` korunur. Same-bar ekonomik sıra belirsizliği application seam üzerinden `INDETERMINATE / AMBIGUOUS_OHLC_PATH` olarak fail-closed’dur. Fee, slippage, tick uydurma, open price improvement ve gerçek exchange execution iddiası eklenmedi.

RED → GREEN odak testleri ve production kodundan bağımsız Decimal tablo oracle kontrolü `9/9 PASS`; tam regresyon `131/131 PASS`; `compileall PASS`. Public profile/API, legacy historical model, persistence, UI ve marker authority değiştirilmedi. P1.07.d.2 public contract değerlendirmesi `DEFER` edildi; sonraki tek iş, public entegrasyondan önce DCA strategy binding araştırma kapısı olan P1.07.d.3’tür.

### P1.07.d.2 — Public contract araştırma kapısı

Durum: DEFERRED; karar `DEFER`; implementation başlamadı. Rapor: `P1.07.d.2_Limit_Order_Public_Contract_Ayrintili_Arastirma_Raporu.md`. Prompt: `docs/P1.07.d.2_Limit_Order_Public_Contract_Arastirma_Promptu.md`.

D.1 application policy’sini public profile/run-plan/HTTP response’a bağlama adımı bilinçli olarak durduruldu. Yerel kontrol mevcut public contract’ı gösterse de d.1 generic single-limit policy’sinin DCA strategy state, role, anchor, reserve ve economic posting’e bağlandığı kanıtlanmadı. Public endpoint/profile açmak yerine bu eksik binding için d.3 araştırması gerekiyor. Persistence, UI, marker ve canlı exchange kapsam dışıdır.

### P1.07.d.3 — DCA strategy binding araştırma kapısı

Durum: RESEARCH_RECEIVED / DEFERRED; implementation başlamadı. Araştırma raporu: `P1.07.d.3_DCA_Limit_Strategy_Binding_Ayrintili_Arastirma_Raporu(1).md`. Prompt: `docs/P1.07.d.3_DCA_Limit_Strategy_Binding_Arastirma_Promptu.md`.

Raporun BASE-only aday önerisi production’a alınmadı. Yerel kontrolde çekirdeğin INTENT/FILL/ORDER_FINAL, partial leaves, BASE anchor, safety blocker ve late-fill invalidation davranışları mevcut testlerle kanıtlandı; ancak d.1 fixed-limit observation’ının DCA order state’e güvenli adapter olarak bağlandığı, reserve lifecycle’ının ve BASE-only end-to-end ekonomik posting zincirinin kanıtı yok. SAFETY ve EXIT DEFER olarak kaldı. Public API, persistence, UI ve marker kapsam dışıdır.

P1.07.d.3.a tamamlandı: internal BASE-only probe, d.1 observation’dan existing core INTENT/FILL/ORDER_FINAL zincirine geçişi kanıtlıyor; `reserve_model=NONE` ve `production_ready=false` sınırı korunuyor. Odak testleri `6/6 PASS`; kanıt: `evidence/P1.07.d.3.a/SONUC.md`. Bu probe production DCA reserve kanıtı değildir.

P1.07.d.3.b araştırması alındı ve yerel kontrollerle değerlendirildi. Mevcut BASE-only v1 için karar `SIMPLIFY_WITH_LIMITATION`: `reserve_model=NONE`, numeric reserve iddiası yok, pending blocker lifecycle gate, accepted core FILL tek ekonomik authority, equality/candidate no-op ve EOF `OPEN_AT_END`. Yeni explicit reserve ledger için karar `DEFER`; raporun asset/unit/owner/fee/partial/EOF/ambiguity/duplicate/atomicity kapıları local code/test ile kapanmadı. Kanıt: `evidence/P1.07.d.3.b/SONUC.md`.

P1.07.d.3.c tamamlandı: `reserve_model=NONE` için `NOT_MODELED`/`NOT_APPLICABLE` metadata sınırı eklendi; pending BASE → SAFETY blokajı ve full-fill/final-coverage ayrımı acceptance testleriyle kapatıldı. Odak `9/9 PASS`, tam regresyon `140/140 PASS`, compile ve workspace PASS; internal probe `production_ready=false` olarak kaldı. Kanıt: `evidence/P1.07.d.3.c/SONUC.md`.

### P1.07.d.2.b — BASE-bound public limit contract readiness

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.07.d.2.b/SONUC.md`.

Yalnız explicit `historical_demo_btcusdt_1h_v1` fixture’a bağlı `POST /api/historical-runs/simulate-base-limit` public contract’ı eklendi. Strict exact-decimal request, dataset/artifact/config doğrulaması, sunucu kontrollü BASE quantity, observation/fill ayrımı, deterministic `binding_identity_sha256`, fail-closed `INDETERMINATE`, `reserve_model=NONE` metadata’sı, `no-store` ve bounded response sınırı uygulandı. Legacy route/fixed-slice route, persistence, UI ve profile katalog akışı değiştirilmedi. Review’de validation-error path’inin generic JSON/no-cache davranışı RED ile doğrulandı ve Problem Details + `no-store` olarak düzeltildi. Tam regresyon `151/151 PASS`; compile, workspace ve OpenAPI route kontrolleri PASS.

Bu bir genel DCA/production execution adapter’ı değildir. Explicit numeric reserve ledger, SAFETY/EXIT, cancellation race, latency/queue/volume/stop, persistence, marker/UI ve canlı venue kapsam dışıdır.

Bağımsız review `NOT_RUN` kalır: scoped security scan reportable bulgu üretmedi, ancak delegated bağımsız worker yoktu ve scan snapshot’ı son düzeltmeden önceydi. Bu nedenle bağımsız acceptance yerine geçmez.

### P1.08.a — Lifecycle authority local inventory

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.08.a/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/05_P1.08_DEAL_LIFECYCLE.md`, LCR-02.

Mevcut reducer’ın economic `INTENT/FILL/ORDER_FINAL/UNKNOWN/MARK` authority’siyle saf deal lifecycle authority’si ayrıldı. Araştırmadaki çelişkili `STARTED/RUNNING` ve `STARTING/ACTIVE` adları yeni ekonomik durumlar olarak kabul edilmedi: kalıcı projection `DRAFT -> RUNNING <-> PAUSED -> COMPLETED | ABORTED | FAILED`; `START` bir olaydır. Deal ve config-revision kimliği immutable kalır; geçiş sayacı yalnız geçerli transition ile artar. Declarative transition table ve negatif geçiş testi RED -> GREEN çalıştırıldı; tam regresyon `153/153 PASS`, compile ve workspace PASS.

Bu, production lifecycle değildir: persistence/reopen/replay, event identity/dedupe, gerçek immutable config revision kaydı ve COPY, cooldown, pause altındaki order policy, UI, shared account/reserve ve tüm ekonomik mutation kapsam dışıdır.

### P1.08.b — Lifecycle config-revision binding contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.08.b/SONUC.md`.

`COPY`, aktif lifecycle projection’ı değiştirmeden caller’ın sağladığı yeni deal kimliği ve yeni config-revision kimliğiyle `DRAFT` projection üretir. Kaynak deal veya config revision kimliğinin tekrar kullanımı reddedilir. RED import failure -> GREEN copy/negative testleri, tam regresyon `155/155 PASS`, compile ve workspace PASS.

Bu, config revision snapshot/store veya persisted COPY değildir: yeni revision’ın içerik hash’i, persistence/replay, event identity/dedupe, cooldown, pause-order policy, UI, shared-account/reserve ve ekonomik mutation kapsam dışıdır.

### P1.08.c — Lifecycle persistence/replay authority inventory

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.08.c/SONUC.md`.

Mevcut `Store` ekonomik event journal’ında batch-idempotency ve FILL execution-id dedupe/conflict; `HistoricalRunStore` ise source-execution idempotency/conflict ve immutable sonuç kaydı taşıyor. Bunlar lifecycle event’inin deal/config-revision/status/cursor authority’si değildir. Lifecycle persistence/replay için ayrı schema veya adapter mevcut olmadığı yerel kodla doğrulandı; yeni production davranışı eklenmedi.

### P1.08.d — Lifecycle event identity contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.08.d/SONUC.md`.

Lifecycle event contract’ı caller-supplied immutable event ID, deal/config-revision scope ve ardışık event sequence taşır. Aynı tam kayıt ikinci kez gelirse `DUPLICATE`, aynı ID farklı immutable alanla gelirse `LIFECYCLE_EVENT_CONFLICT`, farklı scope veya sequence gap ise fail-closed rejection döner. RED import failure -> GREEN odak testleri; tam regresyon `158/158 PASS`, compile ve workspace PASS.

Bu contract ekonomik journal’a veya persistence’a bağlı değildir; hash/canonical serialization, terminal transition enforcement, API/UI, cooldown, pause-order policy ve ekonomik posting kapsam dışıdır.

### P1.08.e — Lifecycle event-to-transition adapter

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.08.e/SONUC.md`.

Accepted lifecycle event önce event identity/scope/sequence contract’ından, sonra saf `DealLifecycle` transition tablosundan geçirilir. Geçerli event projection ve history’yi birlikte ilerletir; exact duplicate ikisini de değiştirmez; invalid transition history’ye eklenmez. RED import failure -> GREEN adapter testleri; tam regresyon `161/161 PASS`, compile ve workspace PASS.

Persistence/replay, API/UI, config snapshot/hash, cooldown, pause-order policy, shared account/reserve veya ekonomik mutation bu dilimde açılmadı.

### P1.08.f — Persistent lifecycle record boundary

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.08.f/SONUC.md`.

Ekonomik `Store`’dan ayrı versioned lifecycle SQLite store eklendi. Store yalnız lifecycle event kayıtlarını transaction içinde yazar; event kimliği, deal/config-revision scope ve sequence replay ile doğrulanır. Yeniden açma aynı projection/history üretir; exact duplicate idempotent kalır; conflict, invalid transition ve satır/payload uyumsuzluğu fail-closed reddedilir. RED import failure -> GREEN store testleri; tam regresyon `164/164 PASS`, compile ve workspace PASS.

Store API/UI’ya açılmadı; config snapshot/hash, cooldown, pause-order policy, shared account/reserve ve ekonomik posting kapsam dışıdır.

### P1.08.g — Config revision snapshot binding

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.08.g/SONUC.md`.

Lifecycle store artık event’in `config_revision_id` değerini ayrı immutable canonical config snapshot + SHA-256 kaydıyla zorunlu olarak bağlıyor. Aynı revision ID farklı snapshot ile kullanılamaz; row/payload ve revision snapshot/hash uyumsuzlukları fail-closed reddedilir. Eşdeğer JSON field order tek revision kimliği üretir, config değişince hash değişir. RED import failure -> GREEN binding/conflict testleri; tam regresyon `167/167 PASS`, compile ve workspace PASS.

Bu yalnız local snapshot binding’dir; API/UI, config editing, COPY persistence, cooldown, pause-order policy, shared account/reserve ve ekonomik posting kapsam dışıdır.

### P1.08.h — Lifecycle terminal/cooldown policy contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.08.h/SONUC.md`.

Terminal `COMPLETED`, `ABORTED` ve `FAILED` projection’ları için sonraki lifecycle event reddi mevcut transition adapter üzerinden korundu; reddedilen event history/projection’ı değiştirmiyor. Yeni saf `cooldown_allows_new_deal` politikası yalnız integer historical `effective_time_us` farkını kullanıyor, eşit sınırı kabul ediyor ve geriye giden zaman/negatif süreyi fail-closed reddediyor. Wall-clock, processing-time, persistence, API/UI ve ekonomik state mutation eklenmedi. RED import failure -> GREEN odak policy testleri; tam regresyon `170/170 PASS`, compile ve workspace PASS.

Sonraki tek iş: `P1.08.i` pause altındaki order policy contract’ını araştırma kanıtı ve saf test sınırıyla değerlendirmek.

### P1.08.i — Pause altında order policy contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.08.i/SONUC.md`.

PAUSED lifecycle için saf `evaluate_paused_orders` contract’ı eklendi. Üç explicit policy (`KEEP_OPEN`, `CANCEL_REQUESTED`, `BLOCKED`) mevcut pending order davranışını tanımlar; üçünde de yeni economic intent `BLOCKED` kalır. `CANCEL_REQUESTED` yalnız `REQUESTED_NOT_CONFIRMED` bildirir; otomatik cancellation, fill, reserve release, persistence, API/UI veya ekonomik mutation iddiası taşımaz. Bilinmeyen policy fail-closed reddedilir. RED import failure -> GREEN odak policy testleri; tam regresyon `173/173 PASS`, compile ve workspace PASS.

Sonraki tek iş: P1 plan sırasındaki sonraki READY mikro-fazı, mevcut kanıt ve bağımlılıklar yeniden kontrol edilerek seçilecektir.

### P1.09.a — Exact BASE/QUOTE sizing candidate contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.09.a/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/06_P1.09_ADVANCED_DCA_SIZING.md`.

`build_sizing_candidate` ile explicit `BASE_QTY` ve `QUOTE_NOTIONAL` farklı birimlerde parse ediliyor; QUOTE notional yalnız explicit positive reference price ile aday BASE quantity’ye çevriliyor. Aday quantity/notional exact decimal string olarak üretiliyor ve eşdeğer BASE/QUOTE girdileri bağımsız testle aynı sonucu veriyor. `BALANCE_PERCENT`, venue quantity/tick quantization, min-notional/risk kabulü, ladder, reinvestment, API/UI, persistence ve economic posting bu mikro dilime alınmadı. Unknown/malformed/zero input fail-closed. RED import failure -> GREEN odak testleri; tam regresyon `176/176 PASS`, bağımsız odak unittest, compile ve workspace PASS.

Sonraki tek iş: P1.09.b exact ladder allocation/conservation contract’ı; venue rounding owner netleşmeden public/API/UI bağlantısı yapılmayacak.

### P1.09.b — Exact ladder allocation/conservation contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.09.b/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/06_P1.09_ADVANCED_DCA_SIZING.md`.

`validate_ladder_allocations` explicit `BASE_QTY` veya `QUOTE_NOTIONAL` birimindeki allocation tuple’ını exact toplar, explicit budget ile karşılaştırır ve kalan bütçeyi aynı birimde döndürür. Bütçe aşımı, bilinmeyen birim ve geçersiz/zero allocation fail-closed reddedilir. Venue quantization, instrument metadata, risk kabulü, reserve/economic posting, ladder price generation, balance-percent, reinvestment, API/UI ve persistence bu mikro dilime alınmadı. RED import failure -> GREEN odak testleri; tam regresyon `179/179 PASS`, bağımsız odak unittest, compile ve workspace PASS.

Sonraki tek iş: `P1.09.c` venue quantization/filter owner contract’ı; profile kanıtı olmadan rounding veya public order davranışı eklenmeyecek.

### P1.09.c — Profile-bound instrument filter contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.09.c/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/06_P1.09_ADVANCED_DCA_SIZING.md`.

`InstrumentFilterProfile` explicit `profile_id`, quantity step, price tick, minimum quantity ve minimum notional metadata’sını sahipleniyor. `validate_order_candidate` yalnız profile grid’inde olan, minimumları ve exact notional filtresini geçen adayları doğruluyor; off-grid veya minimum altı aday fail-closed reddediliyor. Rounding yönü seçilmedi ve aday otomatik quantize edilmedi. Venue, live/testnet, risk acceptance, reserve, API/UI, persistence ve economic posting bu mikro dilime alınmadı. RED import failure -> GREEN odak testleri; tam regresyon `182/182 PASS`, bağımsız odak unittest, compile ve workspace PASS.

Sonraki tek iş: `P1.09.d` balance-percent sizing için eligible balance kaynağı ve exact budget contract’ı; kaynak belirsizse numeric sıfır varsayılmayacak.

### P1.09.d — Tagged eligible-balance percent budget contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.09.d/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/06_P1.09_ADVANCED_DCA_SIZING.md`.

`build_balance_percent_budget`, caller’ın sağladığı açık `balance_source`, asset, positive `eligible_balance` ve `0 < percent <= 1` değerleriyle exact `budget = eligible_balance * percent` projection’ı üretir. Total wallet, available/reserved ayrımı, balance discovery, reserve creation, risk acceptance veya order posting yapılmaz; kaynak/asset/percent/zero input fail-closed reddedilir. RED import failure -> GREEN odak testleri; tam regresyon `185/185 PASS`, bağımsız odak unittest, compile ve workspace PASS.

Sonraki tek iş: `P1.09.e` exact ladder generation’ın sizing candidate ve conservation contract’larına bağlanması; venue quantization tamamlanmadan public/API/UI yolu açılmayacak.

### P1.09.e — Exact ladder generation binding

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.09.e/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/06_P1.09_ADVANCED_DCA_SIZING.md`.

Mevcut domain `build_plan` çıktısı exact application binding’e alındı: generated price/quantity seviyeleri açık allocation unit’e (`BASE_QTY` veya `QUOTE_NOTIONAL`) dönüştürülüyor ve P1.09.b conservation contract’ı ile budget’a karşı doğrulanıyor. BASE ve QUOTE allocation’ları bağımsız exact fixture ile kontrol edildi; budget aşımı ve collapsed/invalid ladder fail-closed. Venue rounding/filter, balance authority, risk acceptance, reserve, economic posting, API/UI ve persistence bağlanmadı. RED import failure -> GREEN odak testleri; tam regresyon `188/188 PASS`, bağımsız odak unittest, compile ve workspace PASS.

Sonraki tek iş: P1.09.f reinvestment eligibility contract’ı; yalnız realized eligible pool için araştırma ve local ledger kanıtı varsa ilerlenir.

### P1.09.f — Realized-profit eligible reinvestment contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.09.f/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/06_P1.09_ADVANCED_DCA_SIZING.md`.

`build_reinvestment_budget`, yalnız asset etiketli `realized_profit_eligible` pool ve `0..1` percent ile exact budget projection’ı üretir. Negative pool, invalid asset/percent fail-closed; zero pool/zero percent `0` budget verir. Unrealized PnL, fee/funding, account ledger, reserve, API/UI, persistence ve economic posting bu dilimde kullanılmadı. RED import failure -> GREEN odak testleri; tam regresyon `191/191 PASS`, bağımsız odak unittest, compile ve workspace PASS.

Sonraki tek iş: `P1.09.g` sizing candidate + ladder + instrument filter + eligible budget birleşimi için saf pre-acceptance gate; mevcut kanıt yetersizse public/UI bağlantısı açılmayacak.

### P1.09.g — Sizing pre-acceptance gate

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.09.g/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/06_P1.09_ADVANCED_DCA_SIZING.md`.

P1.09.a–f sözleşmeleri saf bir pre-acceptance gate’te birleştirildi. İlk güvenli kapsam yalnız ortak `QUOTE_NOTIONAL` unit, aynı quote asset, profile-bound instrument filters ve eligible balance budget’tır. Candidate notional + ladder notional toplamı eligible budget’ı aşamaz; candidate/ladder snapshot uyuşmazlığı ve cross-unit/cross-asset durumları fail-closed reddedilir. Sonuç `order_authority=NONE` taşır; accepted intent, reserve, risk, API/UI, persistence veya economic posting açılmadı. RED import failure -> GREEN odak testleri; tam regresyon `194/194 PASS`, bağımsız odak unittest, compile ve workspace PASS.

Sonraki tek iş: `P1.09.h` pre-acceptance gate için bağımsız metamorphic/exact oracle kontrolleri; kanıt geçmeden public/API/UI sizing akışı açılmayacak.

### P1.09.h — Independent exact/metamorphic sizing oracle

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.09.h/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/06_P1.09_ADVANCED_DCA_SIZING.md`.

Production kodu değiştirilmeden bağımsız Decimal oracle ve metamorphic testler eklendi. QUOTE candidate division, eşdeğer decimal yazımları, allocation sırası değişmezliği ve ladder price/notional formülü production output’tan bağımsız kontrol edildi. Test-only olduğu için import-failure RED uygulanmadı; tam regresyon `197/197 PASS`, bağımsız odak unittest `3/3 PASS`, Python 3.13 compile ve workspace `PASS`.

P1.09.a–h sizing zinciri public/API/UI akışına açılmadı; BASE/balance conversion, quantization owner, hacim/indikatör koşulları, risk, reserve, persistence ve economic posting hâlâ kapsam dışıdır.

Sonraki tek iş: `P1.09.i` için plan bağımlılıklarını kontrol edip yalnız güvenli ve kanıtlanabilir bir sonraki sizing mikro-fazını seçmek.

### P1.09.i — BASE candidate quote commitment binding

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.09.i/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/06_P1.09_ADVANCED_DCA_SIZING.md`.

P1.09.a exact `BASE_QTY` candidate, explicit referans fiyatla hesaplanmış quote notional’ı üzerinden P1.09.g pre-acceptance gate’e bağlandı. Candidate quantity/notional tutarlılığı, profile filter, quote asset, quote-unit ladder ve eligible budget kontrolleri korundu; cross-unit ladder reddediliyor. RED testi mevcut `PRE_ACCEPTANCE_UNIT_CONFLICT` davranışını gösterdi; GREEN sonrası gate `4/4`, tam regresyon `198/198`, bağımsız ilgili suite `9/9`, Python 3.13 compile/workspace `PASS`. `order_authority=NONE` korunuyor; reserve, risk, API/UI, persistence ve economic posting açılmadı.

Sonraki tek iş: P1.09 kapsamındaki kalan koşulları ve P1.10’a geçiş bağımlılığını yeniden kontrol ederek bir sonraki en küçük READY mikro-fazı seçmek.

### P1.10.a — Exit trigger/execution boundary

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.10.a/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

Mevcut core reducer bağımsız testlerle doğrulandı: TP eşiği yalnız `EXIT` kararı üretir, `EXIT` intent pozisyon/PnL değiştirmez, yalnız ayrı `SELL` fill ekonomik geçiş yapar. Test-only olduğu için import-failure RED uygulanmadı; boundary suite `3/3 PASS`, farklı engine kontrolü `1/1 PASS`, tam regresyon `201/201 PASS`, Python 3.13 compile/workspace `PASS`. Multi-TP, trailing, breakeven, cancel-replace ve late-fill recovery bu dilime alınmadı.

Sonraki tek iş: `P1.10.b` multi-TP quantity conservation için mevcut core local contract ve bağımsız oracle kontrolü.

### P1.10.b — Multi-TP exact quantity conservation

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.10.b/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

Saf application validation contract’ı eklendi: `free_exit_capacity = open_qty - accepted_exit_fills - committed_exit_qty`. Over-close fail-closed reddediliyor; split-fill ve exact remainder korunuyor; contract order/position mutation yapmıyor. RED import failure -> GREEN `4/4`, bağımsız Python 3.13 suite `7/7`, tam regresyon `205/205`, compile/workspace `PASS`. Multi-TP registry/OCO, cancel-replace, late fill, stop, trailing, breakeven, API/UI, persistence, reserve ve economic posting açılmadı.

Sonraki tek iş: `P1.10.c` stop trigger/execution ayrımının local contract kontrolü.

### P1.10.c — Stop trigger/execution boundary

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.10.c/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

Mevcut core reducer bağımsız testlerle doğrulandı: halted state `STOP` kararı üretir, stop intent position/PnL değiştirmez, yalnız ayrı `SELL` fill ekonomik geçiş yapar. Test-only olduğu için import-failure RED uygulanmadı; stop boundary `3/3`, bağımsız TP+stop suite `6/6`, tam regresyon `208/208`, Python 3.13 compile/workspace `PASS`. Stop-market/stop-limit, gap/slippage, competing exit, cancel-replace, late fill, trailing ve breakeven açılmadı.

Sonraki tek iş: `P1.10.d` trailing ratchet contract kontrolü.

### P1.10.d — Long trailing ratchet

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.10.d/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

Sabit mesafeli long trailing trigger projection’ı eklendi: `INACTIVE → ACTIVE(high_water, stop_price) → TRIGGERED`. Aktivasyon altı pasiflik, exact `high_water - distance`, favorable ratchet, retracement monotonicity ve trigger sınırı fail-closed testlerle doğrulandı. RED import failure -> GREEN trailing `5/5`, bağımsız Python 3.13 TP/STOP/trailing/multi-TP suite `15/15`, tam regresyon `213/213`, compile/workspace `PASS`. Yalnız trigger state’i vardır; execution, fill, position/PnL, API/UI, persistence, reserve, OCO/cancel-replace, late fill ve breakeven açılmadı.

Sonraki tek iş: `P1.10.e` trailing state’in exit capacity/trigger boundary ile birlikte kontrolü.

### P1.10.e — Trailing exit capacity binding

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.10.e/SONUC.md`. Araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

`TRIGGERED` long trailing state, multi-TP exit capacity contract’ına bağlandı. Accepted fill + mevcut commitment + yeni aday exact açık pozisyon kapasitesini aşarsa fail-closed; geçerli adayda trigger fiyatı ve kalan kapasite dönüyor, `order_authority=NONE` korunuyor. RED import failure -> GREEN binding `3/3`, bağımsız Python 3.13 ilgili suite `12/12`, tam regresyon `216/216`, compile/workspace `PASS`. Order/position mutation, reserve, OCO/cancel-replace, late fill, gap/slippage ve breakeven açılmadı.

Sonraki tek iş: `P1.10.f` breakeven için fee/asset conversion koşul ve karar kapısı.

### P1.10.f — Breakeven fee/asset conversion karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; kanıt: `evidence/P1.10.f/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

Fee-aware breakeven için gerekli fee asset dönüşümü, beklenen çıkış maliyeti ve funding tahsisi yerel sözleşmede tanımlı olmadığı için kod değişikliği yapılmadı. Mevcut `NET_QUOTE` hesabı breakeven olarak yeniden adlandırılmadı; mevcut math testi yalnız generic NET_QUOTE davranışını doğruluyor. Bu mikro fazda production readiness `NO` olarak korunuyor.

Sonraki tek iş: `P1.10.g` short sabit-mesafeli trailing ratchet için bağımsız local contract kontrolü.

### P1.10.g — Short sabit-mesafeli trailing ratchet

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.10.g/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

Short trigger-only projection eklendi: aktivasyon `price <= activation_price`, exact `stop = low_water + distance`, favorable düşüşte low-water ratchet ve `price >= stop` ile `TRIGGERED`. RED import failure -> GREEN long+short suite `10/10`, bağımsız Python 3.13 Decimal oracle `PASS`, tam regresyon `221/221 PASS`. Execution/fill, position/PnL, reserve, OCO/cancel-replace, gap/slippage, API/UI, persistence ve breakeven açılmadı; production readiness `NO`.

Sonraki tek iş: `P1.10.h` yüzde-mesafeli trailing ratchet için karar/uygulama kapısı.

### P1.10.h — Percentage trailing ratchet

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.10.h/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

Long ve short percentage trigger-only projection eklendi: long `high_water × (1-rate)`, short `low_water × (1+rate)`; `0 < rate < 1`, exact Fraction hesabı, yönsel monotonic ratchet ve sınır trigger’ı doğrulandı. RED import failure -> GREEN suite `15/15`, bağımsız Python 3.13 Decimal oracle `PASS`, tam regresyon `226/226`, workspace/compile `PASS`. Execution/fill, position/PnL, reserve, OCO/cancel-replace, gap/slippage, API/UI, persistence ve breakeven açılmadı; production readiness `NO`.

Sonraki tek iş: `P1.10.i` trailing trigger’ın stop/exit execution boundary’sine bağlanması için karar kapısı.

### P1.10.i — Trailing trigger–exit boundary

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.10.i/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

Trailing exit adapter’ı long/short fixed-distance ve percentage state’lerini ortak exact exit-capacity kontrolüne bağlıyor. Yalnız `TRIGGERED` state aday üretebiliyor; accepted fill, `ORDER_FINAL`, reserve, position/PnL mutasyonu yok; `order_authority=NONE` korunuyor. RED type-boundary failure -> GREEN binding `5/5`, dört variant bağımsız immutability control `PASS`, tam regresyon `228/228`, workspace/compile `PASS`. OCO/cancel-replace, late fill, gap/slippage, execution, API/UI, persistence, reserve ve breakeven açılmadı; production readiness `NO`.

Sonraki tek iş: `P1.10.j` OCO/cancel-replace ve late-fill kapasite karar kapısı.

### P1.10.j — OCO/cancel-replace ve late-fill kapasite karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; kanıt: `evidence/P1.10.j/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md` ve `docs/External_Claim_Verification/01_rapor/Ayrintili_Arastirma_Raporu.md`.

Mevcut reducer late fill’i `UNKNOWN` + `LATE_FILL_AFTER_FINAL` blocker’ına alıyor; partial/cancel, duplicate/conflict ve pending-order kontrolleri çalışıyor. Buna rağmen trailing’e özgü OCO üyeliği, cancellation confirmation, replacement identity, late-fill authority ve reserve/commitment owner sözleşmesi yok. Kod veya numeric reserve davranışı eklenmedi. Odak suite `27/27 PASS`, tam regresyon `228/228 PASS`, workspace/compile `PASS`; production readiness `NO`.

Sonraki tek iş: `P1.10.k` trailing public/API/UI readiness karar kapısı.

### P1.10.k — Trailing public/API/UI readiness karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; kanıt: `evidence/P1.10.k/SONUC.md`; ilgili araştırma: `docs/P1_KRITIK_ARASTIRMA_FINAL/07_P1.10_TP_SL_TRAILING.md`.

Mevcut public historical response chart/action/authority sözleşmesini taşıyor ancak trailing state, trigger-candidate identity ve execution lifecycle alanlarını taşımıyor. UI’da yeni trailing görünümü veya marker semantiği eklenmedi; görsel araştırma ve OCO/cancel-replace/reserve önkoşulları kapanmadı. Güncel tam regresyon `228/228 PASS`, workspace/compile `PASS`; kod değişikliği yok, production readiness `NO`.

Sonraki tek iş: `P1.11.a` ortak sanal hesap için account/position ownership ve isolation karar kapısı.

### P1.11.a — Ortak sanal hesap ownership/isolation karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; kanıt: `evidence/P1.11.a/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/08_P1.11_SHARED_ACCOUNT.md`.

P1.11 araştırması concurrent reservation ve replay’i `LOCAL_CODE_REQUIRED` olarak işaretliyor. Yerel model deal lifecycle/config-revision scope’u taşıyor ancak shared account balance/reservation ledger, pair/deal position owner ve account version conflict boundary taşımıyor. Multi-bot/account mutation eklenmedi. Güncel tam regresyon `228/228 PASS`, workspace/compile `PASS`; production readiness `NO`.

Sonraki tek iş: `P1.11.b` shared-account immutable identity ve account/deal/position ownership contract karar kapısı.

### P1.11.b — Shared-account immutable identity contract

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.11.b/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/08_P1.11_SHARED_ACCOUNT.md`.

Ekonomik davranışa dokunmadan immutable `SharedAccountIdentity(account_id, product_id, position_mode, deal_id, allocation_id)` contract’ı eklendi. Her kimlik bileşeni scope-significant; `position_mode` bu mikro fazda opaque bırakıldı ve account balance/reservation/position allocation anlamı uydurulmadı. RED import failure -> GREEN identity suite `3/3`, bağımsız frozen/hash control `PASS`, tam regresyon `231/231`, workspace/compile `PASS`; production readiness `NO`.

 Sonraki tek iş: `P1.11.c` account reservation ledger ve account-version concurrency karar kapısı.

 ### P1.11.c — Account reservation capacity/version projection

 Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.11.c/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/08_P1.11_SHARED_ACCOUNT.md`.

 Pure `AccountCapacity` + `AccountReservation` projection’ı eklendi: `available = capacity - Σactive_reservations`, same-account/same-asset scope, duplicate ID ve stale account version fail-closed; `ReservationProjection` version+1 döndürüyor. RED import failure → GREEN `5/5`, bağımsız Fraction oracle `PASS`, tam regresyon `236/236`, workspace/compile `PASS` (`100` aktif Python dosyası). Persistence, atomic multi-writer locking, fill/release, replay, API/UI ve production reservation ledger açılmadı; production readiness `NO`.

 Sonraki tek iş: `P1.11.d` atomic reservation persistence/replay ve fill/release karar kapısı.

### P1.11.d — Atomic reservation persistence ve account-version boundary

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.11.d/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/08_P1.11_SHARED_ACCOUNT.md`.

Dedicated `ReservationLedger` SQLite modülü eklendi. `BEGIN IMMEDIATE` transaction içinde capacity, active reservation toplamı, reservation commit metadata’sı ve account version artışı tek atomik yerel geçişte tutuluyor. Reopen, exact duplicate idempotency, conflicting duplicate, stale-version, capacity-overrun, unrelated SQLite file protection ve ikinci ledger instance kontrolleri var. RED import failure → GREEN ledger testleri ile tam regresyon `241/241 PASS`; bağımsız Fraction oracle `PASS`; workspace/compile `PASS` (`102` aktif Python dosyası). Mevcut economic `Store`/core reducer binding’i, fill/release, position commitment transferi, dedup/replay birleşimi, API/UI ve production readiness açılmadı.

 Sonraki tek iş: `P1.11.e` reservation fill/release, position commitment transferi ve mevcut economic Store binding karar kapısı.

### P1.11.e — Reservation fill/release ve economic Store binding karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; kanıt: `evidence/P1.11.e/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/08_P1.11_SHARED_ACCOUNT.md`.

Mevcut core `FILL` event’i account/reservation owner taşımıyor; fill quantity base asset, reservation quote asset. `ORDER_FINAL` release miktarı ve reservation kimliği taşımıyor. Reservation ledger ile economic `Store` ayrı SQLite dosyalarında olduğundan atomic reserve + fill/release + posting transaction’ı kanıtlanamadı. Fee/slippage/rounding, partial/late/unknown/conflict authority ve commitment transferi eksik olduğu için kod veya adapter eklenmedi. Son doğrulanmış baseline `241/241 PASS`, workspace/compile `PASS` (`102` aktif Python dosyası), production readiness `NO`.

Sonraki tek iş: `P1.12.a` spot ve lineer futures ürün/settlement/fee/funding/teminat modelinin karar kapısı. P1.11.e yeniden açma koşulları kanıt dosyasında listelidir.

### P1.12.a — Linear futures PnL ve funding temel sınırı

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.12.a/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/09_P1.12_FUTURES_MODEL.md`.

Spot state’inden ayrı saf `LinearFuturesPosition`/`FundingProjection` eklendi. Explicit contract size ile effective quantity, settlement-asset position value, long/short signed unrealized PnL ve timestamped funding projection exact hesaplanıyor. RED import failure → GREEN suite ile tam regresyon `245/245 PASS`; bağımsız Decimal oracle `PASS`; workspace/compile `PASS` (`104` aktif Python dosyası). Leverage, margin, liquidation, mark/index adapter, venue profile, persistence, event replay, API/UI, fee ledger ve account binding açılmadı; production readiness `NO`.

Sonraki tek iş: `P1.12.b` linear futures partial-close, trading fee/funding ledger ve event/replay contract karar kapısı.

### P1.12.b — Linear futures partial-close quantity ve gross PnL

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.12.b/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/09_P1.12_FUTURES_MODEL.md`.

`project_partial_close` ile explicit contract-size partial/full close, kalan quantity conservation, long/short gross realized PnL ve over-close fail-closed sınırı eklendi. RED import failure → GREEN ile tam regresyon `248/248 PASS`; bağımsız Decimal oracle `PASS`; workspace/compile `PASS` (`105` aktif Python dosyası). Fee/funding net binding, event identity/replay, persistence, margin, liquidation, API/UI ve account binding açılmadı; production readiness `NO`.

Sonraki tek iş: `P1.12.c` timestamped funding/trading-fee ledger event identity, duplicate/replay ve net-result binding karar kapısı.

### P1.12.c — Linear futures fee/funding event projection

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.12.c/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/09_P1.12_FUTURES_MODEL.md`.

Immutable `LinearLedgerEvent`/`LinearLedgerState` eklendi. Trading fee pozitif expense, funding işaretli cashflow olarak ayrı tutuluyor; event identity, effective time ordering, exact duplicate idempotency/conflict, asset scope ve `gross - fee + funding` net binding projection’ı doğrulandı. RED import failure → GREEN ile tam regresyon `251/251 PASS`; bağımsız Decimal oracle `PASS`; workspace/compile `PASS` (`106` aktif Python dosyası). Persistence, existing economic Store binding, restart replay, fee tier/maker-taker, funding dataset, per-fill rounding, API/UI ve venue profile açılmadı; production readiness `NO`.

Sonraki tek iş: `P1.12.d` timestamped fee/funding event’lerinin mevcut economic Store içinde kalıcı replay/idempotency binding karar kapısı.

### P1.12.d — Futures fee/funding persistence ve core Store binding karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; kanıt: `evidence/P1.12.d/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/09_P1.12_FUTURES_MODEL.md`.

Mevcut Store generic `FILL` fee ve `FUNDING` posting’ini aynı SQLite transaction’ında, batch dedup/replay ile taşıyor; fakat `effective_time_us`, futures product/profile/position owner ve linear short/margin state’i taşımıyor. Strict event schema’yı migration/replay planı olmadan genişletmek güvenli değil; iki ayrı ledger’ı sonradan birleştiren adapter da atomicity kanıtı üretmez. Kod değişikliği yapılmadı. Son kod baseline `251/251 PASS`, bağımsız Decimal oracle `PASS`, workspace/compile `PASS` (`106` aktif Python dosyası), production readiness `NO`.

Sonraki tek iş: `P1.12.e` isolated margin terminolojisi ve seçilmiş venue-profile kapsamı için karar kapısı.

### P1.12.e — Isolated margin ve venue profile karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; kanıt: `evidence/P1.12.e/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/09_P1.12_FUTURES_MODEL.md`.

Mevcut `leverage`/`initial_equity` yalnız CORE01 local teaching IM estimate ve sentetik başlangıç varsayımıdır; venue margin balance, available margin, collateral, MMR veya liquidation authority değildir. Araştırma isolated/cross kapsamını venue/profile/risk-tier bağımlı, liquidation’ı generic formüle kapalı sınıflandırıyor. Numeric margin/liquidation, collateral conversion, margin API/UI ve profile adapter eklenmedi. Son kod baseline `251/251 PASS`, workspace/compile `PASS` (`106` aktif Python dosyası), production readiness `NO`.

Sonraki tek iş: `P1.13.a` spot grid ailesi için ayrı state-machine, inventory/fee ve level-generation karar kapısı.

### P1.13.a — Spot grid aritmetik seviye üretimi

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.13.a/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/10_P1.13_GRID_FAMILIES.md`.

`build_arithmetic_grid_levels` ile exact `(upper-lower)/N` step ve `N+1` decimal-string seviye üretimi eklendi. Pozitif/bounds/interval doğrulaması, 1–1000 sınırı ve exact decimal sözleşmesine sığmayan sonucu sessiz yuvarlamadan reddetme davranışı var. Geometric precision/quantization sahibi, inventory/fee, accepted FILL, order/replacement, trailing/reverse/infinity/leveraged grid ve UI bu mikro-faza alınmadı. Odak `4/4 PASS`, bağımsız Decimal oracle `PASS`, tam regresyon `255/255 PASS`, compile ve workspace `PASS` (`108` aktif Python dosyası).

Sonraki tek iş: `P1.13.b` spot grid inventory/fee ve accepted-fill cycle/replacement karar kapısı.

### P1.13.b — Spot grid accepted-fill inventory projection

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.13.b/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/10_P1.13_GRID_FAMILIES.md`.

`SpotInventoryState` ve `apply_accepted_spot_fill` ile accepted BUY/SELL fill’in exact base inventory ve signed quote cashflow etkisi eklendi. Sell yalnız sahip olunan base kapasitesi kadar geçerli; aynı canonical `fill_id` duplicate’i idempotent, farklı payload conflict olarak reddediliyor. Fee asset/rounding/posting, order/reserve/replacement, matched grid profit-total equity, geometric/trailing/reverse/infinity/leveraged grid ve UI açılmadı. Odak `4/4 PASS`, bağımsız Decimal inventory oracle `PASS`, tam regresyon `259/259 PASS`, compile ve workspace `PASS` (`110` aktif Python dosyası).

Sonraki tek iş: `P1.13.c` spot grid fee asset/rounding ve matched cycle profit ile total equity ayrımının karar kapısı.

### P1.13.c — Spot grid fee ve cycle/equity karar kapısı

Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.13.c/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/10_P1.13_GRID_FAMILIES.md`.

İlk offline arithmetic profilinde yalnız quote-asset fee, explicit
`EXACT_NO_ROUNDING` ve exact mark-price equity kabul ediliyor. Accepted BUY/SELL
çifti mevcut inventory projection üzerinden doğrulanıyor; matched cycle profit
ile total equity ayrı alanlarda hesaplanıyor. Base/third-asset fee conversion,
venue quantization, fee Store binding, replacement, reserve, API/UI ve public
grid sonucu açılmadı. Odak `5/5 PASS`; P1.13.a–c ilişkili küme `13/13 PASS`;
tam proje `707` testte `705 PASS`, faz dışı Windows Credential Manager
`Windows error 1312` nedeniyle `2` environment error. Bağımsız Decimal oracle,
compile, read-only source-surface, workspace ve `git diff --check` PASS.

Sıradaki tek iş: `P1.13.d` geometric seviye precision/quantization karar kapısı;
kanıt yetersizse güvenli DEFER.

### P1.13.d — Geometric grid precision ve quantization karar kapısı

Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.13.d/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/10_P1.13_GRID_FAMILIES.md`.

Geometric `r=(upper/lower)^(1/N)` exact rational kök ve explicit tick grid’i
ile sınırlandı. Perfect-root olmayan oran ve off-tick seviye fail-closed
reddediliyor; otomatik rounding yapılmıyor. Odak `9/9 PASS`, P1.13.a–d
ilişkili küme `18/18 PASS`, tam proje `712` testte `710 PASS`, faz dışı Windows
Credential Manager `Windows error 1312` nedeniyle `2` environment error.
Compile, independent literal oracle, read-only source-surface, workspace ve
`git diff --check` PASS. Order/fill, inventory/fee, replacement,
trailing/reverse/infinity/leveraged grid, API/UI, persistence ve Binance/
Testnet mutation açılmadı.

P1.13.e kararı `DEFERRED / NO-GO` olarak kapatıldı; sonraki tek iş
`P1.13.f` Futures Grid v1 için ayrı profile ve exact projection karar
kapısıdır.

### P1.13.e — Grid trailing-up/down ve reverse/infinity karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.13.e/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/10_P1.13_GRID_FAMILIES.md`.

Trailing-up/down için araştırma yalnız ürün davranışını destekliyor; exact range/version transition, pending order/reserve lifecycle, cancel-replace identity, late fill, precision/rounding ve persistence/replay sözleşmesi yok. Reverse/infinity exact semantics `NOT_VERIFIED`. Mevcut `trailing_ratchet.py` exit-trigger projection’ıdır ve grid range authority değildir; aritmetik seviye üreticisine de range kaydırma eklenmedi. Leveraged grid P1.12/P1.11 bağımlılıkları nedeniyle kapsam dışı kaldı. Kod/API/UI/order/reserve değişikliği yapılmadı.

Son doğrulanmış checkout baseline'ı: `712` testte `710 PASS`, Windows
Credential Manager `Windows error 1312` nedeniyle `2` environment error;
workspace, compile ve diff kontrolleri `PASS`. P1.13.f.a ile ayrı profile ve
exact level projection tamamlandı. Sonraki tek iş: `P1.13.f.b`
position/initial-position ve accepted-fill state karar kapısı.

### P1.14.a — Rebalancing exact target/delta projection

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `PASS` (Erdos salt-okunur Codex incelemesi); production readiness: `NO`. Kanıt: `evidence/P1.14.a/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md`.

`target_value_i = total_equity * target_weight_i` ve `trade_delta_i = target_value_i - current_value_i` aynı açık valuation asset içinde exact projection olarak eklendi. Weight toplamı exact 1, duplicate asset, negatif current, geçersiz giriş ve exact decimal dışı sonuç fail-closed; çıktı asset adına göre canonical. Order/reserve/fill, fee/rounding, price conversion, balance, trigger, persistence, signal/template ve UI authority’si yoktur. RED import → GREEN kanonik regresyon `265/265 PASS`; bağımsız Decimal oracle `PASS`; workspace `PASS` (`110` aktif Python dosyası).

Sonraki tek iş: `P1.14.b` signal identity/dedupe ve event-time karar kapısı.

### P1.14.b — Signal identity, event-time ve dedupe

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `PASS` (Ptolemy salt-okunur Codex incelemesi, düzeltme sonrası); production readiness: `NO`. Kanıt: `evidence/P1.14.b/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md`.

Immutable `signal_id`, source, integer `event_time_us`, `schema_version=signal-v1` ve lowercase SHA-256 payload hash sözleşmesi eklendi. Exact duplicate no-op, aynı ID ile farklı metadata/payload conflict, history içinde duplicate identity, eski yeni signal stale ve geçmiş zaman sırası ihlali fail-closed. Signal candidate/order/fill, payload hash üretimi, auth/replay window, warmup/closed-bar, persistence, API ve UI açılmadı. RED import → GREEN kanonik regresyon `270/270 PASS`; bağımsız signal control `PASS`; compile/workspace `PASS` (`114` aktif Python dosyası).

Sonraki tek iş: `P1.14.c` signal warmup/closed-bar ve stale-policy karar kapısı.

### P1.14.c — Signal warmup, closed-bar ve stale readiness gate

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `PASS` (Locke salt-okunur Codex incelemesi); production readiness: `NO`. Kanıt: `evidence/P1.14.c/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md`.

Explicit `WAITING_FOR_CLOSED_BAR`, `STALE`, `WARMING_UP` ve `READY` readiness projection’ı eklendi. Signal event time ile son kapalı bar zamanı integer microseconds; warmup/stale pencereleri açık caller input’u; stale boundary equality ve tüm bool gate tipleri fail-closed regresyonlarla kapsandı; wall-clock/processing time kullanılmıyor. Signal candidate/order/fill, indikatör, adapter, trigger, persistence, API ve UI açılmadı. Odak regresyon `6/6 PASS`, ilgili readiness kümesi `12/12 PASS`, bağımsız readiness oracle `PASS`; compile/diff `PASS`. `tools/run_checks.py` proje Python `3.13` isterken bundled runtime `3.12.14` olduğu için bu oturumda çalıştırılamadı.

Sonraki tek iş: `P1.14.d` threshold/time rebalancing trigger karar kapısı.

### P1.14.d — Rebalancing threshold/time trigger projection

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `PASS` (Mendel salt-okunur Codex incelemesi); production readiness: `NO`. Kanıt: `evidence/P1.14.d/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md`.

Threshold `abs(current-target)>=threshold` ve time interval `observation-last>=interval` ayrı exact projection’lar olarak eklendi. Inclusive boundary, decimal weight/threshold, integer microsecond time ve geriye giden observation zamanı fail-closed. NaN/Infinity/exponent/malformed decimal, threshold=0, signed zero, aynı timestamp ve tüm bool zaman girdileri doğrudan regresyonlarla kapsandı. Trigger yalnız readiness/candidate kapısıdır; order/reserve/fill, conversion, fee/rounding, balance, sizing, persistence, API ve UI authority’si yoktur. Odak regresyon `8/8 PASS`, ilgili projection kümesi `14/14 PASS`, bağımsız Decimal/time oracle `PASS`; compile/diff `PASS`. `tools/run_checks.py` proje Python `3.13` isterken bundled runtime `3.12.14` olduğu için bu oturumda çalıştırılamadı.

Sonraki tek iş: `P1.14.e` template integrity ve non-authority karar kapısı.

### P1.14.e — Strategy template integrity ve non-authority

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `PASS` (Turing salt-okunur Codex incelemesi, düzeltme sonrası); production readiness: `NO`. Kanıt: `evidence/P1.14.e/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md`.

`strategy-template-v1` canonical JSON snapshot, SHA-256 identity, 64 KiB/bounded payload, forbidden executable/secret/credential field, declared capability integrity ve inert/non-authority sınırı ile eklendi. Public `StrategyTemplate(...)` kurucusundaki duplicate capability bypass’ı kırmızı regresyonla doğrulanıp `__post_init__` fail-closed guard’ıyla düzeltildi. Activation approval, profile capability binding, webhook auth, order/reserve/fill, persistence, API ve UI açılmadı. Odak regresyon `6/6 PASS`, ilgili projection kümesi `14/14 PASS`, bağımsız canonical/hash/non-authority oracle `PASS`; compile/diff `PASS`. `tools/run_checks.py` proje Python `3.13` isterken bundled runtime `3.12.14` olduğu için bu oturumda çalıştırılamadı.

P1.14.f tamamlandı; ayrıntılı kapanış ve sonraki görev aşağıdaki bölümde kayıtlıdır.

### P1.14.f — Template activation ve capability gate

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.14.f/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/11_P1.14_REBALANCING_SIGNAL_TEMPLATES.md`.

Template declared capability’leri explicit allowlist ve `PENDING`/`APPROVED` approval durumu ile değerlendiren gate eklendi. Supported pending `AWAITING_APPROVAL`, supported approved `READY_FOR_ACTIVATION`, eksik capability `CAPABILITY_UNSUPPORTED` döner. Gate activation, candidate, order, reserve veya fill üretmez; gerçek activation transition, profile binding, parameter validation, persistence, API ve UI dışarıdadır. RED import → GREEN kanonik regresyon `290/290 PASS`; bağımsız activation/capability control, compile ve workspace `PASS` (`122` aktif Python dosyası).

Sonraki tek iş: `P1.15.a` hedge/cross/two-leg kapsam karar kapısı.

### P1.15.a — Hedge identity ve two-leg state sınırı

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `PASS` (Herschel salt-okunur Codex incelemesi, düzeltme sonrası); production readiness: `NO`. Kanıt: `evidence/P1.15.a/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/12_P1.15_HEDGE_CROSS_TWO_LEG.md`.

`ONE_WAY` ve `HEDGE` position identity’leri explicit venue profile, product, symbol ve gerekiyorsa LONG/SHORT hedge side ile ayrıldı. Two-leg state machine yalnız güvenli ilk sınırı uygular: `NONE → LEG_A_PENDING → ONE_LEG_FILLED/PARTIAL_HEDGE → BOTH_ESTABLISHED`; recovery ve timeout geçişleri explicit’tir. First-leg ara state’i geri alınmaz; fake atomicity yoktur. Unhashable/wrong-type state girdileri explicit string guard ile fail-closed `TWO_LEG_STATE_INVALID` döndürür. Accepted-fill quantity posting, duplicate/replay persistence, recovery ledger, cross ownership, reduce-only, liquidation, API ve UI bu dilimin dışındadır. Odak `4/4 PASS`, ilgili two-leg projection kümesi `8/8 PASS`, bağımsız hedge/two-leg oracle `PASS`; compile/diff `PASS`. `tools/run_checks.py` proje Python `3.13` isterken bundled runtime `3.12.14` olduğu için bu oturumda çalıştırılamadı.

P1.15.a tamamlandı; ayrıntılı kapanış `evidence/P1.15.a/SONUC.md` altında kayıtlıdır.

### P1.15.b — Accepted two-leg fill projection

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `PASS` (Bohr salt-okunur Codex incelemesi, düzeltme sonrası); production readiness: `NO`. Kanıt: `evidence/P1.15.b/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/12_P1.15_HEDGE_CROSS_TWO_LEG.md`.

`LegFill` ve immutable `TwoLegFillProjection` ile aynı account/venue-profile/product/symbol kapsamındaki HEDGE LONG/SHORT iki ayağın accepted fill’leri exact decimal miktarlarla ayrı izleniyor. İlk leg partial/full sonrası `PARTIAL_HEDGE`/`ONE_LEG_FILLED` ara state’i korunuyor; iki leg FULL olduğunda `BOTH_ESTABLISHED` oluşuyor. Duplicate aynı payload’da idempotent, conflicting ID, aynı side, scope değişimi, geriye giden event time ve tamamlanmış leg’e yeni fill fail-closed reddediliyor. İstenen toplam quantity bu mikro-fazda bulunmadığından quantity conservation iddia edilmiyor.

Public projection constructor’ı state, identity pair, fill history, aggregate quantity ve status tutarlılığını yeniden doğruluyor; state/leg/status whitelist’leri exact string tipini zorunlu kılıyor. Bu sayede malformed projection ve custom equality allowlist bypass’ı fail-closed kalıyor. Projection yalnız in-memory read modelidir; persistence/reopen/replay/recovery, late-fill policy, cross ownership, reduce-only, margin/liquidation, order/reserve binding, API/UI ve ekonomik posting açılmadı. `docs/P1_KRITIK_ARASTIRMA_FINAL/test_matrices/P1.15_TESTS.md` mevcut ancak `SPECIFIED_NOT_EXECUTED_AGAINST_LOCAL_CODE` olduğu için implementation kabul kanıtı sayılmadı. Kırmızı regresyonla bulunan iki bulgu düzeltildi; odak `7/7 PASS`, ilgili hedge projection kümesi `11/11 PASS`, bağımsız accepted-fill/malformed-constructor oracle ve compile `PASS`, `git diff --check` `PASS`. `tools/run_checks.py` ve `tools/check_workspace.py` Python `3.13` gereksinimi nedeniyle bu oturumda tam-suite/workspace sonucu veremedi; güncel tam-suite sonucu iddia edilmiyor.

P1.15.b tamamlandı; ayrıntılı kapanış `evidence/P1.15.b/SONUC.md` altında kayıtlıdır.

### P1.15.c — Two-leg persistence/replay/recovery karar kapısı

Durum: `DEFERRED / NO-GO / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.15.c/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/12_P1.15_HEDGE_CROSS_TWO_LEG.md`.

Mevcut `LifecycleStore` açıkça `NON_ECONOMIC_LIFECYCLE_ONLY` kapsamındadır ve two-leg economic identity/leg/effective-time alanlarını taşımaz. Generic economic `Store` execution dedup ve posting içerir, ancak hedge side/leg scope, effective ordering, recovery state ve P1.15 model lineage sözleşmesini taşımaz. P1.15.b in-memory projection’ını iki ayrı store arasında bağlayan adapter atomic accepted-fill + state transition kanıtı üretmez. Bu nedenle migration, yeni economic schema, recovery numeric modeli veya adapter yazılmadı.

P1.15.c’nin yeniden açılması için canonical event schema, tek persistence sahibi/transaction planı, event/effective/persistence time ayrımı, two-leg duplicate/conflict/late-fill recovery politikası, deterministic reopen/replay ve independent field-level oracle/test matrisi gerekir. `docs/P1_KRITIK_ARASTIRMA_FINAL/test_matrices/P1.15_TESTS.md` mevcut ancak local code’a karşı çalıştırılmış kabul matrisi değildir. Kanonik regresyon `30/30 PASS` (lifecycle + generic store), bağımsız storage schema control, compile ve diff `PASS`; tam suite/workspace checker Python `3.13` gereksinimi nedeniyle çalışmadı.

Sonraki güvenli tek iş: `P1.16.a` chronological split ve leakage-free evaluation karar kapısı.

### P1.16.a — Chronological train/gap/test split sınırı

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review:
`PASS` (Noether salt-okunur Codex incelemesi, P1/P2 bulgu yok);
production readiness: `NO`. Kanıt: `evidence/P1.16.a/SONUC.md`; araştırma
kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md`.

`ChronologicalPoint`, `ChronologicalSplit` ve `split_chronological` ile strict
artan integer `event_time_us` kullanan immutable train/gap/test sınırı eklendi.
Public constructor artık üç bölümün tamamında sıra, gap/test sınırı ve duplicate
identity’yi yeniden doğruluyor; yanlış point tipi ve custom equality’li sample ID
fail-closed reddediliyor. `max(train_time) < min(test_time)` korunuyor;
sıralama otomatik yapılmıyor. Explicit `gap_count` yalnız yapısal dışlama
alanıdır, purge/embargo horizon’u değildir. OOS freeze/touched lineage,
feature/label horizon, exact purge/embargo, multiple-testing/stress registry,
persistence, API/UI ve economic result bu mikro-fazda yok. Odak `7/7 PASS`;
bağımsız chronology oracle ve compile `PASS`.

`tools/run_checks.py` ve `tools/check_workspace.py` Python `3.13` gereksinimi
nedeniyle bundled `3.12.14` ile çalışmadı (`active_python_files: 286`); güncel
tam-suite/workspace sonucu iddia edilmiyor. `git diff --check` `PASS` (mevcut
LF/CRLF uyarıları).

Sonraki tek iş: `P1.16.b` OOS freeze ve evaluation lineage karar kapısı.

### P1.16.b — OOS freeze ve evaluation lineage

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review:
`PASS` (Hilbert salt-okunur Codex re-review, P1/P2 bulgu yok); production
readiness: `NO`. Kanıt: `evidence/P1.16.b/SONUC.md`; araştırma kanıtı:
`docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md`.

`EvaluationLineage` OOS sonucu görülmeden `OOS_UNTOUCHED`, inspection sonrası
`OOS_INSPECTED` durumunu taşır. Inspection sonrası tuning talebi eski lineage’ı
`TOUCHED` yaparak `NEW_EXPERIMENT_REQUIRED` döndürür; eski OOS tekrar untouched
gösterilemez. Public lineage ve tuning decision modelleri exact string ve exact
lineage tipiyle custom equality/string-subclass bypass’ını fail-closed reddeder.
OOS görülmeden tuning değişmeden izinlidir. New experiment/trial üretimi,
dataset/config/model/kernel/seed binding, persistence, OOS KPI, purge/embargo,
stress, API/UI ve economic result bu mikro-fazda yok. Odak `5/5 PASS`, bağımsız
OOS freeze oracle, Hilbert re-review, compile ve diff `PASS`; Python `3.13`
gereksinimi nedeniyle checker’lar bu oturumda çalışmadı
(`active_python_files: 286`).

Sonraki tek iş: `P1.16.c` feature/label horizon ve purge/embargo karar kapısı.

### P1.16.c — Feature/label horizon overlap ve purge kararı

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `Pauli PASS` (salt-okunur Codex re-review, P1/P2 bulgu yok); production readiness: `NO`. Kanıt: `evidence/P1.16.c/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md`.

`TimeInterval` ve `assess_purge_requirement` ile half-open `[start_time_us,end_time_us)` train-label/test-feature aralıkları karşılaştırılıyor. Adjacent sınır `NO_OVERLAP`, kesişen aralık `PURGE_REQUIRED`; public assessment status/ID tutarlılığı, duplicate ID, exact tuple/interval tipi ve custom equality/subclass bypass’ları fail-closed. Bu yalnız overlap/gate sonucudur; exact purge/embargo süresi feature lookback, label future horizon ve settlement bilgisi olmadan seçilmedi. Dataset binding, OOS/trial/stress lineage, persistence, API/UI ve economic result yok. Odak `5/5 PASS`; bağımsız horizon oracle, compile ve diff `PASS`. Checker’lar Python `3.13` gereksinimi nedeniyle bundled `3.12.14` ile çalışmadı (`active_python_files: 286`); güncel tam-suite/workspace sonucu iddia edilmiyor.

Sonraki tek iş: `P1.16.d` multiple-testing trial registry karar kapısı.

### P1.16.d — Multiple-testing trial registry

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.16.d/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md`.

`TrialStudy` explicit parameter-space/objective/selection-rule identity ve en fazla 1.000 trial sınırı taşır. `TrialRecord` status’ları `SUCCEEDED`, `FAILED`, `INVALID` olarak ayrıdır ve tümü trial_count’a dahil edilir. Exact duplicate no-op, conflicting ID fail-closed; winner selection yoktur. Parameter snapshot/score, optimizer, persistence, dataset lineage, OOS/stress result, purge/embargo, API/UI ve economic result bu mikro-fazda açılmadı. RED import → GREEN `315/315 PASS`; bağımsız trial registry control, compile ve workspace `PASS` (`134` aktif Python dosyası).

Sonraki tek iş: `P1.16.e` stress lineage ve ayrı sonuç kimliği karar kapısı.

### P1.16.e — Stress lineage ve ayrı sonuç kimliği

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.16.e/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md`.

`StressLineage` base result identity, stress profile identity ve profile hash’ini immutable biçimde taşır. Aynı girdiler deterministik ayrı `stress_result_id` üretir; sabit `STRESS` etiketi ve base result overwrite koruması vardır. Spread/slippage/latency/volume/partial-fill/OHLC ekonomik modeli, seed/RNG, persistence, dataset/config/model/kernel binding, API/UI ve exact purge/embargo bu mikro-fazda yok. RED import → GREEN `318/318 PASS`; bağımsız stress lineage control, compile ve workspace `PASS` (`136` aktif Python dosyası).

Sonraki tek iş: `P1.16.f` warmup leakage ve readiness binding karar kapısı.

### P1.16.f — Warmup leakage ve readiness binding

Durum: `DEFERRED / NO-GO / RESEARCH_AUDITED / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.16.f/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md` ve evidence içindeki QuantConnect/Freqtrade primer kaynakları.

Resmî kaynak denetimi warmup’ın indicator state hazırlığı olduğunu ve warmup sırasında trade açılmaması gerektiğini doğruladı; Freqtrade ayrıca stabil history’nin strategy’nin gerçek lookback’inden türetilmesini ve unstable başlangıç bölümünün çıkarılmasını ister. Local source audit’te `signal_readiness.py` yalnız caller tarafından verilen sayıyı sınıflandırıyor; mevcut historical simulation/plan/contract zincirinde feature/indicator/label adapterı yok. Bağımsız stdlib warmup/lookahead oracle `PASS`. Bu nedenle yeni numeric warmup, indicator/signal authority veya warmup event’lerinden fill oluşmadığına dair end-to-end ekonomik kod açılmadı.

Sonraki tek iş: `P1.16.g` local feature/label horizon ve gerçek run binding karar kapısı.

### P1.16.g — Local feature/label horizon ve gerçek run binding

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; odak red/green kontrat kontrolü:
`PASS_WITH_LIMITATION`; ayrı bağımsız review: `NOT_RUN`; production readiness: `NO`.
Kanıt:
`evidence/P1.16.g/SONUC.md`; araştırma dayanağı:
`docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md`.

`historical_features.py` bounded exact `CLOSE_SMA`, `CLOSE_RETURN` ve
`FUTURE_CLOSE_RETURN` pipeline’ını closed-bar, chronology, lookback/horizon ve
1.000 bar sınırlarıyla uygular. Feature binding run planına, historical
reducer’a ve capture identity’sine bağlanır; warmup barlarında action üretilmez,
tam binding yeniden doğrulanır ve değişiklik reducer başlamadan reddedilir.
Feature değerleri exact `Fraction` tabanlı canonical ratio olarak taşınır.
Numeric purge/embargo, ekonomik KPI/OOS, optimizer, stress model, persistence
schema, API/UI opt-in profili ve canlı venue davranışı bu faza dahil değildir.
`4/4`, `6/6`, `26/26` odak regresyonları geçti; tam checker `786/788 PASS`, iki
Windows Credential Manager ortam hatası kaldı; compile/workspace/diff geçti.

Sonraki tek iş: `P1.16.i` stress ekonomik modeli ve gerçek senaryo runner karar kapısı.

### P1.16.h — Bounded real-run lineage binding

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; bağımsız review: `NOT_RUN`; production readiness: `NO`. Kanıt: `evidence/P1.16.h/SONUC.md`; araştırma kanıtı: `docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md`.

P1.06 capture/store dataset/config/model/kernel/seed/result identity’sini kendi kapsamı içinde taşıyor. P1.16.h ile optional `EvaluationRunBinding` bu mevcut kimlikleri kayıtlı trial, OOS ve isteğe bağlı stress lineage’ına canonical biçimde bağlıyor. Store binding’i checksum’lı immutable kayda alıyor; close/reopen sonrası geri veriyor; aynı source execution’da aynı binding idempotent, farklı binding conflict; sözleşme dışı binding alanları fail-closed reddediliyor. Mevcut `325/325 PASS`, bağımsız canonical kontrol, compile ve workspace `PASS` (`138` aktif Python dosyası).

Economic stress modeli, exact purge/embargo, feature/label/warmup pipeline, score/KPI ve production readiness bu dilimde açılmadı. Sonraki tek iş: `P1.16.i` stress ekonomik modeli ve gerçek senaryo runner karar kapısı.

### P1.16.i — Stress ekonomik modeli ve gerçek senaryo runner karar kapısı

Durum: `IN_PROGRESS / EVIDENCE_AUDIT`; production readiness: `NO`. Ana kanıt dayanağı: `docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md`. Alt faz kanıtı: `evidence/P1.16.i/SONUC.md`.

Stress profile metadata’sı P1.16.h ile persisted run’a bağlandı; ancak spread/slippage/latency/volume/partial-fill/OHLC stress modelinin ekonomik authority’si yok. Bu ana faz kanıt sırasına göre mikro fazlara ayrılmıştır; aynı anda yalnız bir alt faz aktiftir:

- `P1.16.i.a` — Core/store authority ve mevcut scenario evidence inventory: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**. Mevcut fill, fee, precision, late-fill, OHLC ambiguity, result identity ve persistence sahipleri kod/fixture üzerinden çıkarıldı; eksik ekonomik davranışlar varsayımla açılmadı. Kanıt: `evidence/P1.16.i/SONUC.md`.
- `P1.16.i.b` — Exact stress economic contract: **COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED**; ekonomik implementation **DEFERRED / NO-GO**. Rapor `evidence/P1.16.i.b/SONUC.md` altında yerel ve bağımsız kontrollerle denetlendi. T-07’de sayısal çelişki, T-12’de seed/identity çelişkisi ve reserve oracle’ında negatif available karşı örneği bulundu. Spread/slippage/latency/volume/partial-fill/OHLC ekonomik kodu, reserve adapter ve yeni public yüzey açılmadı.
- `P1.16.i.c` — Deterministic scenario/result identity: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; ekonomik scenario identity **DEFERRED / NO-GO**. Mevcut stress profile hash, base-result ilişkisi, canonical serialization ve overwrite/dedup/conflict sınırı bağımsız oracle ile doğrulandı; seed/scenario/kapsam genişletmesi yapılmadı. Kanıt: `evidence/P1.16.i.c/SONUC.md`.
- `P1.16.i.d` — Persistence/replay/recovery: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**. Base Store’un kendi transaction/replay/rollback ve HistoricalRunStore’un snapshot checksum/idempotency sınırı doğrulandı; stress event, branch isolation, cross-store atomicity, economic recovery ve field-level result comparison **DEFERRED / NO-GO** kaldı. Kanıt: `evidence/P1.16.i.d/SONUC.md`. Economic runner, reserve adapter veya yeni public yüzey yazılmadı.
- `P1.16.i.e` — Minimum dikey uygulama ve dış yüzey kararı: **COMPLETE_WITH_LIMITATION / NO-GO**. P1.16.i.a–d kanıt zinciri birleştirildi; economic runner, yeni persistence schema/adapter, API ve UI açılmadı. Ekonomik stress persistence, branch isolation, cross-store atomicity, reserve lifecycle ve scenario identity `DEFERRED / NO-GO`. Kanıt: `evidence/P1.16.i.e/SONUC.md`.

Her alt fazda değişiklik sırası zorunludur: iddia → mevcut kontrol → RED/karşı örnek → farklı bağımsız kontrol → sonuç → yalnız doğrulanmış iddia için değişiklik. Ekonomik model, optimizer, numeric purge/embargo, yeni UI veya public endpoint kanıt yokken açılamaz.

### P1.17.a — Public read-only data authority inventory

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`.

P1.16.i ekonomik stress kapısı kanıt yetersizliği nedeniyle no-go olarak kapatıldı. Sıradaki bağlayıcı P1 işi, public canlı fiyat/veri için mevcut kod, veri adapter’ı, stale/gap/reconnect, offline fallback ve `SIMULATED` emir sınırlarının yerel envanteridir. Bu mikro fazda private credential, gerçek emir, yeni ekonomik hesap, stress runner veya UI eklenmeyecek. Public kaynağın güncel davranışı yerel kodla cevaplanamıyorsa ancak uygulama kararını değiştirecek iddia için anonim/kanıtlı araştırma istenecektir.

Çıkış kanıtı: `evidence/P1.17.a/SONUC.md` içinde mevcut authority, RED/karşı örnek, bağımsız kontrol ve public-read-only sınırı kaydedildi. Canlı feed bulunmadığı için kod açılmadı.

### P1.17.b — Public read-only feed contract research gate

Durum: **COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED**; production readiness: `NO`. Kanıt: `evidence/P1.17.b/SONUC.md`. Araştırma: `docs/P1_KRITIK_ARASTIRMA_FINAL/14_P1.17_SIMULATED_RUNTIME.md`.

Güncel resmi kaynak araştırması public read-only market-data WebSocket, source/system zaman ayrımı ve sequence gap/out-of-order riskini destekledi. Rapor yerel kodu ve testleri incelemediği için RED→GREEN yerel kontrolü ayrıca yapıldı. REST payload/rate-limit/catch-up ayrıntıları ve belirli venue reconnect algoritması tamamlanmış sayılmadı. Canlı REST/WS adapter, live route, credential, gerçek emir veya ekonomik live fill kodu hâlâ açılmadı.

### P1.17.c — Offline observation replay adapter

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.17.c/SONUC.md`.

P1.17.b ile doğrulanan salt-okunur `PublicObservation` ve fail-closed feed cursor’ı yalnız local fixture/replay girdileriyle ilerletildi. `replay_observations` bounded ve deterministic zamanlıdır; gap sonrası explicit resync olmadan devam etmez. Ağ bağlantısı, venue SDK’sı, yeni API/UI, persistence, candidate/order/fill, fee/spread/slippage ve gerçek paper-trading davranışı yoktur.

### P1.17.d — Venue-specific transport mapping and reconnect/catch-up research gate

Durum: **COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED**; production readiness: `NO`. Kanıt: `evidence/P1.17.d/SONUC.md`.

Binance Spot `binance-spot-public-v3` tek public profile olarak seçilebilir sınırlı araştırma yönü verdi. Güncel resmi belgelerle heartbeat/limit/timestamp iddiaları düzeltildi: ping 20 saniye, pong penceresi 60 saniye, 1024 stream/connection ve 300 connection attempt/5 dakika/IP ayrıdır; millisecond varsayılan olsa da explicit microsecond seçenekleri vardır. `t/a` yalnız trade/aggregate-trade identity’sidir; source sequence olarak bağlanmaz. Resubscribe kabul edildi, automatic snapshot ve tam REST gap repair garanti edilmedi. Canlı adapter, live route, credential, simulated economic fill veya persistence açılmadı.

### P1.17.e — Binance public payload normalization (network-free)

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.17.e/SONUC.md`.

Binance Spot `@trade` ve `@aggTrade` fixture payload’ları ağsız biçimde generic `PublicObservation` sınırına aktarıldı. Numeric/timestamp unit guard’ları, transport/profile scope, stream ayrımı, `t/a` event identity ve `source_sequence=None` doğrulandı. WebSocket client, reconnect worker, REST catch-up, persistence, API/UI, candidate/order/fill ve ekonomik hesap açılmadı.

### P1.17.f — Binance normalized observation → local replay binding (network-free)

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.17.f/SONUC.md`.

Normalize edilmiş Binance trade/aggTrade observation kayıtları mevcut bounded replay cursor’ına doğru stream scope, duplicate/conflict ve event-time davranışıyla bağlandı. `t/a` source sequence olarak bağlanmadı; forged sequence fail-closed reddedildi. Ağ, reconnect, REST catch-up, persistence, API/UI, candidate/order/fill ve ekonomik hesap açılmadı.

### P1.17.g — Binance public profile acceptance matrix (network-free)

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.17.g/SONUC.md`.

Trade/aggTrade mapping, unit mismatch, malformed payload, wrong scope, duplicate/conflict, event-time order, replay ve economic-boundary no-op davranışları tek bounded acceptance matrix içinde birlikte kanıtlandı. İlk RED’de görülen timestamp unit mismatch kabulü explicit plausibility/unit guard ile düzeltildi; bağımsız oracle ve `346/346` regresyon geçti. Canlı transport, reconnect worker, REST catch-up, persistence, API/UI ve economic fill açılmadı.

### P1.17.h — Binance REST public payload normalization (network-free)

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.17.h/SONUC.md`.

Yalnız fixture/decoded payload ile `/api/v3/trades` ve `/api/v3/aggTrades` REST mapping’i uygulandı. `transport=REST`, REST’e özgü zaman alanları, event identity, exact numeric parse, symbol/product scope ve WS observation’dan ayrık identity davranışı RED→GREEN ve bağımsız kontrolle kanıtlandı. `7/7` odak testi ve `353/353` regresyon geçti. Ağ, REST catch-up, reconnect worker, persistence, API/UI, candidate/order/fill ve ekonomik hesap açılmadı.

### P1.17.i — Binance public observation capability boundary (network-free)

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.17.i/SONUC.md`.

REST ve WS normalize edilmiş observation’ların hiçbir candidate/order/fill/economic authority portuna ulaşmadığı mevcut local import/call graph ve bounded negatif testlerle kanıtlandı. Observation yalnız read-only public data ve replay sınırında kaldı; untrusted economic alanlar taşınmadı. `2/2` odak testi ve `355/355` regresyon geçti. Canlı network, reconnect/catch-up, persistence ve API/UI açılmadı.

### P1.17.j — Binance public transport activation readiness gate (network-free)

Durum: **DEFERRED / NO-GO / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.17.j/SONUC.md`.

Mevcut resmi venue kanıtı ile local persistence/catch-up ve reconnect önkoşulları karşılaştırıldı. Bağımsız gate `NO-GO` verdi: canlı entrypoint, reconnect worker, tam REST catch-up ve live observation persistence yok; venue automatic snapshot/full gap repair/contiguous sequence garantisi vermiyor. `355/355` regresyon geçti. Network client, reconnect worker, REST catch-up, credential, candidate/order/fill ve economic/paper execution açılmadı.

### P1.18.a — Offline rule-based read-only event explanation projection

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.18.a/SONUC.md`.

Mevcut tarihsel/public observation ve sonuç sınırlarından yalnız açıklama/projection üretildi. `ReadOnlyExplanation` bounded ve salt-okunur; bilinmeyen durumlar fail-closed. `4/4` odak test, bağımsız oracle, `359/359` tam regresyon, compile ve workspace geçti. Parametre, emir, fill, reserve, PnL veya canlı transport authority’si eklenmedi.

### P1.18.b — Read-only explanation response binding karar kapısı

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.18.b/SONUC.md`.

P1.18.a projection’ı mevcut iki historical API response’una bounded `explanations` alanı olarak bağlandı. Strict/forbid/frozen response modeli, fixed-slice summary status fallback’i ve frontend type-only tüketim sınırı doğrulandı. İlk RED’deki üç response/projection hatası minimum düzeltmeyle kapatıldı; `359/359` regresyon, compile/workspace ve frontend build geçti. Persistence response DTO’sunu değil mevcut capture/result snapshot’ını kullandığı için persisted schema değişmedi. UI görünümü, LLM, network, candidate/order/fill, reserve veya PnL authority açılmadı.

### P1.18.c — Read-only explanation UI/UX research gate

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.18.c/SONUC.md`.

Kullanıcı tarafından teslim edilen UI/UX araştırma raporu gerçek sonuç ekranı ve response contract ile karşılaştırıldı. `ExplanationSection` completed ve indeterminate result akışlarına bağlandı; severity sunumu, backend grup-içi sıra korunumu, native teknik ayrıntı disclosure’ı ve 320px taşma önlemleri eklendi. Frontend hesaplama, LLM, network, persistence ve backend contract değişmedi. `frontend npm run build`, `359/359` regresyon, compile ve workspace geçti. Browser kernel-assets hatası nedeniyle görsel screenshot/viewport QA çalıştırılamadı; bu açık P1.18.d görsel erişilebilirlik QA kapısına bırakıldı.

### P1.18.d — Read-only explanation visual/accessibility QA

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.18.d/SONUC.md`.

Browser eklentisinin kernel-assets hatası sürmesine rağmen doğrudan kurulu Chrome CDP fallback’i ile gerçek yerel frontend/backend sonucu doğrulandı. 1280, 390 ve 320px görünümleri; 8 açıklama/8 kart, mobil yatay taşmama ve native disclosure’ın Space klavye etkileşimi geçti. Frontend build, `359/359` regresyon, compile, workspace ve statik UI contract kontrolleri geçti. NVDA/JAWS çalıştırılmadı; bu nedenle kabul local visual/accessibility smoke QA ile sınırlıdır. Yeni ekonomik alan, backend contract, LLM, network, persistence veya sticky notification eklenmedi.

### P1.19.a — Result shell responsive state acceptance

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.19.a/SONUC.md`.

Gerçek local UI akışında idle/empty, loading, error ve completed durumları doğrulandı. İlk RED, legacy response’un `summary` alanının UI tarafından okunmamasıydı; `final_economic_summary ?? summary` ile minimum frontend düzeltmesi yapıldı. Fixed-slice akışı korundu; indeterminate branch mevcut backend/API testleri ve kod sınırıyla doğrulandı ancak bu dilimde ayrı UI screenshot’ı alınmadı. Frontend build ve `359/359` regresyon geçti. Backend economic authority, response contract, network, persistence veya LLM değişmedi.

### P1.19.b — Existing result-shell responsive/theme inventory

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.19.b/SONUC.md`.

Mevcut result shell’in responsive breakpoint, renk tokenı, açık/koyu tema, focus ve empty/error görsel durumu envanterlendi. 1080/720/380px responsive kırılımları ve önceki 320/390px taşmama kanıtı doğrulandı; açık tema/token yok, focus desteği kısmi. Yeni tema sistemi veya focus davranışı eklenmedi. NVDA/JAWS etkileşimli QA ortam sınırı nedeniyle NOT_RUN kaldı.

### P1.19.c — Theme/focus implementation decision gate

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.19.c/SONUC.md`.

Teslim edilen raporun `SIMPLIFY` kararı bağımsız local kontrolle denetlendi. Raporun yanlış palette/satır referansları kullanılmadı; mevcut dark palette’den sınırlı CSS tokenları ve button/input/select/summary/a için ortak `:focus-visible` standardı eklendi. 768px gerçek yatay taşma RED’i 900px altında tek workspace kolonu ile kapatıldı. Light theme, ARIA redesign, backend/economic/network/persistence/LLM açılmadı. Frontend build, `359/359` regresyon, compile, workspace ve Chrome CDP responsive/focus smoke PASS; NVDA/JAWS etkileşimli QA ortam sınırı nedeniyle NOT_RUN.

### P1.19.d — Screen-reader/high-contrast accessibility QA gate

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.19.d/SONUC.md`.

Chrome CDP fallback’i ile gerçek local DOM/AX tree, 320/390/768/1024/1280px taşmama, 18 focus durağı, native disclosure, forced-colors emülasyonu ve temiz uygulama konsolu doğrulandı. Eksik favicon isteği kapatıldı; frontend build, `359/359` regresyon, compile ve workspace PASS. NVDA/JAWS ve gerçek Windows High Contrast Mode çalıştırılmadı; bu nedenle production readiness `NO` ve tam erişilebilirlik iddiası kapalıdır. Light theme veya yeni persistence mekanizması bu mikro fazda açılmadı.

### P1.19.e — Light theme / uzman görünüm karar kapısı

Durum: **COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED**; production readiness: `NO`. Kanıt: `evidence/P1.19.e/SONUC.md`.

Kullanıcı tarafından sağlanan rapor gerçek checkout ile denetlendi; okunmamış dosya/palette iddiaları local evidence olarak reddedildi. Gerçek React/Vite sürümleri, `ReadOnlyExplanation` type’ı, backend strict response modelleri, mevcut CSS token/focus kuralları ve P1.19.d responsive/focus kanıtı doğrulandı. Bağımsız contrast oracle seçilmiş gerçek çiftlerde 11 PASS, border/body için 1.44:1 FAIL verdi; alpha/gradient dahil tam matrix tamamlanmadı. Light theme ve uzman görünüm DEFER; app kodu bu mikro fazda değiştirilmedi. NVDA/JAWS ve gerçek Windows High Contrast Mode NOT_RUN olduğundan production readiness `NO` kaldı.

Araştırma promptu: `docs/P1.19.e_Light_Theme_Uzman_Gorunum_Arastirma_Promptu.md`. Ayrıntılı sonuç: `evidence/P1.19.e/SONUC.md`.

### P1.19.f — Exact token/palette ve safe detailed-view implementation gate

Durum: **DEFERRED / NO-GO / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.19.f/SONUC.md`.

Mevcut gerçek token kapsamı ve seçilmiş kontrast oracle ölçüldü; 11 kritik çift PASS, border/body `1.44:1` FAIL. Tam semantic token/alpha/gradient matrisi ve exact light palette yok. Yeni light theme/toggle/persistence veya expert mode eklenmedi. Mevcut native `details/summary` teknik disclosure’ı güvenli minimum detailed-view olarak kabul edildi; raw context’ten ekonomik türetme ve frontend ekonomik hesaplaması kalıcı `NO-GO`.

F30’un light theme kısmı için exact palette/default/persistence kararı gerekir; bu karar gelmeden yeni UI kodu açılmayacak. Kanıt: `evidence/P1.19.f/SONUC.md`.

### P1.19.g — Frontend kritik akış component-test kapısı

Durum: **COMPLETE_WITH_LIMITATION / LOCAL_PASS**; production readiness: `NO`. Kanıt: `evidence/P1.19.g/SONUC.md`.

Onaylanan ek test runtime’ı olarak Vitest, React Testing Library ve jsdom eklendi. `datasetCatalog` yardımcıları, `HistoricalChart` idle/loading/error/ready durumları, exact decimal OHLC doğrulaması, dataset/artifact uyuşmayan tamamlanmış aksiyon marker’larının fail-closed reddi, `PREFIX_BOUNDARY_ONLY` indeterminate boundary ve backend `ExplanationSection` görünümü test edildi. Üç test dosyasında `12/12 PASS`; TypeScript ve production frontend build PASS.

Bu kanıt gerçek browser/E2E, canlı API, NVDA/JAWS veya gerçek Windows High Contrast Mode değildir. Yeni ekonomik hesap, API contract, persistence veya canlı entegrasyon açılmadı. Test runtime kurulumu npm çıktısında `2` güvenlik uyarısı bildirdi; `audit fix` çalıştırılmadı, bağımlılık yükseltmesi ayrı bakım kapısıdır.

### P1.16.g — Local feature/label horizon ve gerçek run binding

Bounded exact feature/label pipeline ve historical runner binding uygulandı;
closed-bar, lookback/future horizon, warmup action suppression ve capture
identity checksum’ı kanıtlandı. Numeric purge/embargo, ekonomik KPI/OOS ve
stress runner ayrı P1.16.i karar kapısıdır.

### P1.16.f — Warmup leakage ve readiness binding

Warmup döneminin gerçek trade window’dan ayrılması ve warmup event’lerinin emir üretmemesi için local feature/indicator binding kanıtı gereklidir. Kanıt olmadan indicator, signal veya ekonomik sonuç kodu açılmayacak.

### P1.06.e — Kapanan UI araştırma kapısı

Kaydetme ve saved-run list/detail deneyimini mevcut React ekranına bağlamadan önce anonim görsel/UX araştırma raporu alınacak. Prompt: `docs/P1.06.e_Saved_Run_UI_UX_Arastirma_Promptu.md`. Rapor gelmeden UI özelliği, yeni görsel sistem, grafik genişletmesi veya mobil davranış kararı uygulanmayacak.

## 2026-09-07 — Kapsamlı/matematiksel analiz audit kapısı

Durum: AUDIT_COMPLETE_WITH_ONE_SMALL_FIX; kanıt: `evidence/AUDIT_2026-09-07/SONUC.md`.

Kullanıcı raporlarındaki iddialar kaynak kod, mevcut sözleşme, gerçek local artifact, kontrollü matematik ve bağımsız kontrollerle denetlendi. Timestamp mikro-saniye sözleşmesi ve config TOCTOU iddiası doğrulanmadı; TP/slippage, gap politikası, demo sizing ve ortak request-body/quality response sınırları karar araştırması bekliyor. Kanıtlanan tek küçük hata, simulate validation hatasının Problem Details yerine genel JSON dönmesiydi; `/api/historical-runs/simulate` mevcut Problem Details path kümesine alındı ve 83/83 regresyon geçti.

Yeni araştırma kapısı: `docs/2026-09-07_Kanitli_Audit_Dis_Arastirma_Promptu.md`. Bu kapı kapanmadan finansal formül, `paper.json`, gap status veya ortak body-limit sözleşmesi değiştirilmeyecek.

## 2026-09-07 — Yeni offline simülasyon audit raporu değerlendirmesi

Durum: B UYGULANDI / A BELGELENDİ / C DEFERRED / D1 UYGULANDI / D2 UYGULANDI / D3A UYGULANDI / D3B UYGULANDI. Son doğrulama: `92/92 PASS`; kanıt: `evidence/AUDIT_2026-09-07/SONUC.md`.

Kullanıcının sağladığı kapsamlı rapor talimat değil, kanıtlanması gereken araştırma çıktısı olarak ele alındı. Raporun TP/slippage kararı mevcut sözleşmeyle uyumlu bulundu: formül değiştirilmedi, trigger referansı ile fill fiyatı ayrımı `docs/VERI_VE_SIMULASYON.md` içinde belgelendi. Gap kararı için önce RED→GREEN test uygulandı; yalnız desteklenen `1h` interval’inde exact open-time grid preflight’i ekonomik state kurulmadan çalışıyor ve gap/bilinmeyen interval fail-closed reddediliyor. Demo sizing değiştirilmedi.

Gövde sınırının D1 parçası uygulandı: küçük JSON route’ları native Starlette katmanında 4 KiB ile sınırlı, `data-quality` 20 MiB upload bütçesini koruyor. D2 olarak quality issue örnekleri üretim anında en fazla 200 kayıtla bounded hale getirildi; tam issue/error/warning sayaçları ve `issues_truncated` korunuyor. Native 413 yanıtları küçük JSON route’larında ortak Problem Details sözleşmesine alındı (D3A). Quality report response toplam byte bütçesi D3B olarak 256 KiB fallback ile sınırlandı. Bu audit güvenlik dilimleri tamamlandı; P1.06 kalıcı koşu fazı sırası atlanmadı.

## 2026-09-11 — P2.01 Binance Spot Testnet bağlantı/capability araştırması

Durum: `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED`; implementasyon kapısı `DEFERRED`; trading activation `NO-GO`. Kanıt: `evidence/P2.01/SONUC.md`.

P1.20 sonrası P2.01 için resmi Binance Spot Testnet endpoint ve izin/filter snapshot yüzeyi mevcut local kodla karşılaştırıldı. Testnet REST’in `https://testnet.binance.vision/api` tabanı, market WebSocket’in `wss://stream.testnet.binance.vision/ws` tabanı, WebSocket API’nin ayrı tabanı ve yalnız `/api/*` desteği doğrulandı. Mevcut projede venue adapter, signed client ve güvenli credential injection bulunmadığı için credential, order, account mutation veya yeni testnet kodu açılmadı. Sıradaki tek küçük iş `P2.01.a`: credential/emir içermeyen public connectivity + exchangeInfo snapshot sözleşmesi.

## 2026-09-11 — P2.01.a public connectivity + exchangeInfo snapshot

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; trading activation `NO-GO`. Kanıt: `evidence/P2.01.a/SONUC.md`.

Kimliksiz gerçek Binance Spot Testnet `GET /api/v3/exchangeInfo?symbol=BTCUSDT` çağrısı bounded adaptöre bağlandı ve yeni read-only local endpoint’ten sunuldu: `GET /api/venue-snapshots/binance-spot-testnet?symbol=BTCUSDT`. Sözleşme sabit testnet tabanı, boşluksuz/kontrol-karaktersiz 1–32 karakter UTF-8 symbol girdisi, UTF-8 percent-encoding, 5 saniye default/30 saniye max timeout, 256 KiB response sınırı, identity encoding, response hash, symbol/filter/rate-limit metadata’sı ve fail-closed upstream hatalarını içeriyor. Gerçek public yanıt `TRADING`, 11 filter, 4 rate-limit kaydı, boş `permissions` ve `permissionSets=[['SPOT']]` verdi; `SPOT` account/key capability’si uydurulmadı.

Odak `9/9 PASS`, tam Python regresyon `366/366 PASS`, Python 3.13 compile/workspace, ASGI smoke, frontend build ve gerçek public GET PASS. API key/secret, signed account capability, `/sapi`, WebSocket, order/order-test/cancel, persistence, UI wizard ve ekonomik hesaplama açılmadı. Sıradaki tek iş: P2.01.b public snapshot’ın UI’da salt-okunur gösterimi için karar/uygulama kapısı.

## 2026-09-11 — P2.01.b public snapshot salt-okunur UI

Durum: `IMPLEMENTED_WITH_LIMITATION / READY_WITH_LIMITATION`; kanıt: `evidence/P2.01.b/SONUC.md`.

Public Testnet snapshot kartı mevcut React stüdyo ekranına bağlandı. Kart yalnız
`CONNECTED_READ_ONLY`/yükleniyor/`FAILED` durumlarını, venue status’ünü,
`permissionSets`, `order_types`, rate limits, filters ve hash ayrıntılarını
gösterir. Hesap/API-key trade yetkisi, bakiye, order, fill veya frontend
ekonomik hesaplama yoktur. Frontend build ve backend test/compile/workspace
kontrolleri PASS; güncel kaynakla yeniden başlatılan local API route smoke HTTP
200 verdi. Doğrudan Chrome CDP ile 320/768/1280px taşmama, snapshot/boundary
DOM, screenshot ve 23 klavye odağında görünür focus ring doğrulandı. Yerleşik
browser runtime yolu, NVDA/JAWS ve gerçek Windows HCM NOT_RUN. Sıradaki tek iş:
P2.02/P2.04 offline güvenlik kapıları.

## 2026-09-11 — P1.20 tam demo kabulü

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P1.20/SONUC.md`.

Gerçek local frontend/backend ile verified sabit BTCUSDT 1h artifact kullanılarak dataset seçimi, historical profile/run plan, kullanıcı onayı, simülasyon, grafik/ekonomi/açıklama incelemesi, kaydetme, Saved Runs listesi ve salt-okunur ayrıntıyı yeniden açma akışı tamamlandı. `359/359` Python regresyonu, Python 3.13 compile, workspace kontrolü, frontend build ve Chrome CDP görsel/etkileşim smoke PASS. İlk 768px Saved Runs yatay taşması `900px` responsive eşik düzeltmesiyle kapatıldı. NVDA/JAWS ve gerçek Windows High Contrast Mode çalıştırılmadı; production readiness `NO`. P1.20 demo kapısı kapanmıştır; özellik matrisindeki PLAN maddeleri P1 tamamlanmış anlamına gelmez.

## 2026-09-11 — P2.02.a offline signer ve request-time sınırı

Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; full P2.02: `IN_PROGRESS`; trading activation: `NO-GO`. Kanıt: `evidence/P2.02/SONUC.md`.

P2.02.a’da gerçek ağ çağrısı olmadan `HmacSha256Signer`, `RequestSigner`/`Clock` sınırları, exact UTF-8 percent-encoded imza payload’ı, unsafe/duplicate/credential parametre reddi, unknown key type fail-closed ve integer millisecond `timestamp/recvWindow` predicate’i eklendi. RED import failure → GREEN `6/6` odak testi geçti. Gerçek secret/API key, Ed25519/RSA signer, Windows provider, signed account, HTTP, clock sync, reconciliation, Testnet mutation ve mainnet açılmadı.

Sıradaki tek iş: P2.02’nin Windows secret provider ve signed-account sınırını offline/fake oracle ile değerlendirmek. Bu iş tamamlanmadan P2.03 order lifecycle veya gerçek Testnet mutation başlatılmaz.

## 2026-09-11 — P2.02.b Windows secret-provider ve signed-account sınırı

Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; sahiplik: backend application security boundary; kanıt: `evidence/P2.02/SONUC.md`.

Kapsam: Windows Credential Locker/DPAPI’ye gerçek yazma yapmadan, secret’ın frontend/URL/log/persistence dışı kaldığını garanti eden provider portu ve public venue metadata’nın signed account/key capability sayılamadığı fail-closed sözleşme. Ön kontrol: mevcut source’ta credential provider veya signed-account implementation bulunmadı; bu yüzden yalnız yeni offline/fake oracle açılacak. RED→GREEN, dummy material, import-graph ve serialization boundary testleriyle kanıtlanacak. Gerçek secret, API key, OS vault, HTTP, signed account çağrısı, order veya mainnet yok.

RED→GREEN odak testi `6/6 PASS`; tam regresyon `387/387 PASS`, Python 3.13 compile/workspace ve frontend build PASS. Gerçek Windows provider runtime ve signed account `DEFERRED/NO-GO` kalır; ekonomik/API/persistence davranışı varsayımla açılmaz.

Sıradaki tek iş: `P2.04.a` — Fake WebSocket/Fake REST ile reconnect, stale/gap, restart ve UNKNOWN attempt reconciliation state machine.

## 2026-09-11 — P2.04.a offline reconciliation state machine

Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; full P2.04: `IN_PROGRESS`;
trading activation: `NO-GO`; kanıt: `evidence/P2.02/SONUC.md`.

Yalnız [OFFLINE_ORACLE] fake WebSocket/Fake REST sınırı eklendi. Restart sonrası
`SENDING` attempt `UNKNOWN` olarak karantinaya alınıyor; reconnect doğrudan
`SYNCED` olmuyor; authoritative REST sonucu olmadan ekonomik senkronizasyon
verilmiyor. Duplicate event idempotent, aynı ID ile farklı fingerprint conflict,
out-of-order event `GAP`; ham event payload’ı saklanmıyor. Fake REST `FOUND`
yalnız `ACKNOWLEDGED`, diğer sonuçlar `UNRESOLVED` üretiyor; fill veya emir
yaşam döngüsü hesabı yok.

RED→GREEN odak `6/6 PASS`; tam regresyon `393/393 PASS`; Python 3.13
compileall, workspace (`160` aktif Python dosyası) ve frontend build PASS.
Gerçek WebSocket API, signed REST, Testnet mutation, P2.03 order lifecycle,
NVDA/JAWS ve Windows HCM açılmadı.

Sıradaki tek iş: P2.04.b — Fake REST/stream disagreement, stale/reset ve
non-terminal attempt recovery matrisini genişletmek.

## 2026-09-11 — P2.04.b disagreement/freshness/reset quarantine

Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; full P2.04: `IN_PROGRESS`;
trading activation: `NO-GO`; kanıt: `evidence/P2.02/SONUC.md`.

P2.04.a state machine’i Fake REST/stream disagreement, freshness ve Testnet
reset karşı-örnekleriyle genişletildi. REST ve stream order identity farkı
`GAP` açıyor; freshness sınırı `STALE`; reset sonrası yeni authoritative snapshot
olmadan `SYNCED` yasak; GAP sonrası event’ler karantinada tutuluyor. Ham event,
ekonomik değer veya order lifecycle hesabı eklenmedi.

RED→GREEN odak `10/10 PASS`; tam regresyon `397/397 PASS`; Python 3.13
compileall, workspace (`160` aktif Python dosyası) ve frontend build PASS.
Gerçek WebSocket API, signed REST, canlı reset recovery, P2.03 lifecycle,
NVDA/JAWS ve Windows HCM açılmadı.

Sıradaki tek iş: `P2.04.c` — mevcut signed transport/WS adapter contract
denetimi; local kod yeterli değilse gerçek entegrasyon açılmayacak.

## 2026-09-11 — P2.02 offline attempt/outbox ilk dikey dilimi

Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; full P2.02: `IN_PROGRESS`; trading activation: `NO-GO`. Kanıt: `evidence/P2.02/SONUC.md`.

P2.02’nin ilk güvenli diliminde ayrı SQLite attempt store, `PREPARED -> PERSISTED -> SENDING` kalıcılık sırası, canonical request fingerprint, credential-bearing payload reddi, ambiguous transport -> `UNKNOWN`, restart sırasında `SENDING -> UNKNOWN`, kör retry engeli ve `UNKNOWN -> RECONCILING` geçişi uygulandı. Odak `9/9 PASS`, tam regresyon `375/375 PASS`, Python 3.13 compile/workspace PASS (`154` aktif Python dosyası). Gerçek transport, API key/secret, signer, clock/recvWindow, signed account, reconciliation, API/UI, Testnet mutation ve mainnet açılmadı.

Bu ilk dilimin sonraki alt fazı P2.02.a olarak tamamlandı; signer/time kanıtı ve kalan sınırlar `evidence/P2.02/SONUC.md` içinde tutulur.
# P2.04.c — Signed transport ve WebSocket adapter contract denetimi

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; full P2.04: `IN_PROGRESS`;
trading activation: `NO-GO`; kanıt: `evidence/P2.04.c/SONUC.md`.

Mevcut public Testnet snapshot, offline signed-request/credential sınırı,
fake order transport ve reconciliation coordinator denetlendi. Gerçek signed
REST, API-key header binding, Binance User Data Stream subscription, reconnect
worker ve order query adapter'ı bulunmadı. Bu nedenle canlı entegrasyon,
secret, order ve mainnet açılmadı.

Standart suite `397/397 PASS`, Python 3.13 compileall/workspace ve frontend
production build PASS. Bir sonraki tek iş: P2.03 fake venue ile Spot
`LIMIT`/`MARKET` order lifecycle, partial fill ve cancel/fill race sözleşmesi.
# P2.03 — Fake venue Spot LIMIT/MARKET order lifecycle ilk dilimi

Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; full P2.03: `IN_PROGRESS`;
trading activation: `NO-GO`; kanıt: `evidence/P2.03/SONUC.md`.

Offline/fake lifecycle modülüyle LIMIT/MARKET, exact filter validation,
partial fill/leaves, quoteOrderQty sınırı, duplicate/conflict, out-of-order,
terminal late fill, cancel/fill race ve order-scoped event sözleşmesi eklendi.
Gerçek Binance REST/WS, signed account/order, mutation, frontend binding ve
ekonomik posting açılmadı. Tam regresyon `404/404 PASS`, compileall/workspace
PASS.

Sıradaki tek iş: venue lifecycle facts’larının mevcut `domain.engine`
`INTENT/FILL/ORDER_FINAL` ekonomik event’lerine bağlanma sözleşmesini ve
offline dedup/reconciliation kanıtını incelemek.
## 2026-09-18 — P2.03 offline OCO order-list identity/state projection

Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; full P2.03: `IN_PROGRESS`;
trading activation: `NO-GO`. Kanıt:
`evidence/P2.03/MARKET_CONDITIONAL_ORDER_LIST_CONTRACT_SONUC.md`.

P2.03’ün sıradaki güvenli dilimi olarak resmi Spot OCO sözleşmesi ile mevcut
checkout karşılaştırıldı ve yeni `order_list_contract.py` eklendi. Immutable
`orderListId`/`listClientOrderId`/`OCO` identity, tam iki leg, WORKING/PENDING
rolü, venue order-type sınırı, bounded list/leg status gözlemi, duplicate,
conflict, out-of-order ve terminal OCO koordinasyonu fail-closed doğrulandı.
`tests/test_order_list_contract.py` `4/4 PASS`; P2.03’e ilişkin geniş koruma
kümesi `77/77 PASS`. `tools/run_checks.py` `792` testte `790 PASS` verdi; kalan
iki hata Windows Credential Manager ortamı (`1312` ve cleanup
`CREDENTIAL_NOT_FOUND`) ile sınırlı kaldı. Compileall, workspace (`290` aktif
Python dosyası) ve diff check PASS.

Bu dilimde fiyat, miktar, fill, fee, reserve, core event, cancel-replace,
SQLite persistence, signed transport, User Data Stream orchestration, gerçek
Testnet mutation veya mainnet açılmadı. In-memory observation geçmişi 128 kayıt
ile bounded’dır. Sıradaki tek iş bu state projection’ı SQLite transaction içinde
atomic durable replay owner’a bağlamaktır; MARKET core binding ve canlı order
listesi hâlâ `DEFERRED / NO-GO`.
