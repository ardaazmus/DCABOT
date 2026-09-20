# Yol haritası — DEMO_FIRST_1

Öncelik: P1 tam demo → P2 Binance testnet → P3 Binance gerçek kurulum → P4 diğer borsalar. Eski N serisi tarihsel referanstır; aktif görev seçimi buradan yapılır. CORE01 kaynakları çalışır başlangıçtır, P1 bitmiş değildir.

## Güncel görev — 2026-09-19 P2.04 post-gap mixed cursor repeated conflict stale old anchor final replay parity

Transaction-forward `(211,199)` ve event-forward `(209,211)` recovery
anchor’larından sonra tekrarlı fingerprint conflict ile `GAP` açıldı; tuple
sırasına göre eski mixed-component anchor’lar `(210,212)` ve `(208,212)`
`RESYNC_ANCHOR_STALE` kaldı. Aynı terminal boundary anchor yeniden kabul
edildi; `SNAPSHOT_STALE` → `SYNCED`, exact replay `DUPLICATE`, eski
recovery/conflict/anchor event’leri `QUARANTINED`, boş SQLite journal değişmedi.
Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `90/90`,
tam checker `865/865 PASS`, compileall/workspace/diff PASS. Gerçek reconnect
worker, REST catch-up, core/economic binding, mutation ve mainnet authority yok.
Kanıt: `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş stale mixed-anchor reddinden sonra güncel
cursor’ın snapshot retry ve final replay boyunca korunması regresyonudur.

## Önceki görev — 2026-09-19 P2.04 post-gap mixed cursor forward terminal repeated fingerprint conflict re-entry freshness ve quarantine parity

Transaction-forward `(212,211)` ve event-forward `(211,212)` akışlarında aynı
forward boundary’de tekrarlı fingerprint conflict `CONFLICT/GAP`, aynı boundary
terminal recovery anchor, eşik altı snapshot `SNAPSHOT_STALE`, eşik snapshot
`SYNCED`, exact replay `DUPLICATE`, eski conflict/re-entry/terminal/replacement
event’leri `QUARANTINED` kaldı; boş SQLite journal değişmedi. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `89/89`, tam
checker `864/864 PASS`, compileall/workspace/diff PASS. Gerçek reconnect worker,
REST catch-up, core/economic binding, mutation ve mainnet authority yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş tekrarlı conflict sonrası eski
mixed-component anchor monotonicity ve final replay parity regresyonudur.

## Önceki görev — 2026-09-19 P2.04 post-gap repeated replacement anchor equal-boundary freshness ve duplicate quarantine parity

Tekrarlı replacement conflict sonrası eşit cursor’lı terminal recovery anchor
kabul ediliyor; `209` snapshot `SNAPSHOT_STALE`, eşik `210` snapshot `SYNCED`
oluyor. Terminal recovery replay `DUPLICATE`, önceki non-terminal recovery ve
forward event `QUARANTINED` kalıyor, boş SQLite journal değişmiyor. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `82/82`, tam
checker `856/856 PASS`, compileall/workspace/diff PASS. Gerçek reconnect worker,
REST catch-up, core/economic binding, mutation ve mainnet authority yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş post-gap equal-boundary repeated recovery
fingerprint conflict re-entry parity regresyonudur.

## Önceki görev — 2026-09-19 P2.04 post-gap repeated replacement conflict anchor monotonicity ve terminal quarantine parity

İlk replacement conflict sonrası non-terminal recovery anchor ile yeniden
`SYNCED` açıldı; aynı recovery identity’nin tekrarlı fingerprint conflict’i
yeniden `CONFLICT/GAP` açıyor. Daha eski `209` recovery anchor
`RESYNC_ANCHOR_STALE`, monoton `211` terminal anchor kabul ediliyor; `210`
snapshot `SNAPSHOT_STALE`, `211` snapshot `SYNCED` oluyor. Terminal recovery
replay `DUPLICATE`, eski recovery ve forward event `QUARANTINED` kalıyor, boş
SQLite journal değişmiyor. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`;
odak `1/1`, komşu `80/80`, tam checker `855/855 PASS`,
compileall/workspace/diff PASS. Gerçek reconnect worker, REST catch-up,
core/economic binding, mutation ve mainnet authority yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş post-gap repeated replacement anchor
equal-boundary freshness ve duplicate quarantine parity regresyonudur.

## Önceki görev — 2026-09-19 P2.04 post-gap replacement fingerprint conflict ve re-entry quarantine parity

GAP sonrası aynı replacement identity’nin farklı fingerprint’i `CONFLICT/GAP`
açıyor; doğrudan snapshot `SYNC_STATE_INVALID` ile reddediliyor.
Transaction-ileri/event-geride ve event-ileri/transaction-geride recovery
anchor sonrası `209` snapshot `SNAPSHOT_STALE`, `210` snapshot `SYNCED` oluyor;
recovery exact replay `DUPLICATE`, eski replacement ve forward event
`QUARANTINED` kalıyor, boş SQLite journal değişmiyor. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `79/79`, tam
checker `854/854 PASS`, compileall/workspace/diff PASS. Gerçek reconnect worker,
REST catch-up, core/economic binding, mutation ve mainnet authority yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş post-gap repeated replacement conflict
anchor monotonicity ve terminal quarantine parity regresyonudur.

## Önceki görev — 2026-09-19 P2.04 recovery anchor post-gap re-entry ve paired snapshot gate parity

GAP sonrası doğrudan snapshot `SYNC_STATE_INVALID`, iki paired recovery anchor
yönü yeniden `RECONCILIATION_REQUIRED`, `209` snapshot `SNAPSHOT_STALE`, `210`
snapshot `SYNCED` oluyor; recovery replay `DUPLICATE`, boş SQLite journal
değişmiyor. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`,
komşu `78/78`, tam checker `853/853 PASS`, compileall/workspace/diff PASS.
Gerçek reconnect worker, REST catch-up, core/economic binding, mutation ve
mainnet authority yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş post-gap replacement fingerprint conflict
ve re-entry quarantine parity regresyonudur.

## Önceki görev — 2026-09-19 P2.04 recovery anchor paired-component strict ordering ve quarantine parity

Transaction veya event cursor bileşeni gerilediğinde `OUT_OF_ORDER/GAP`, GAP
sonrası forward event `QUARANTINED` kalıyor; boş SQLite journal değişmiyor.
Dört paired ordering yönü doğrulandı. Durum `IMPLEMENTED_WITH_LIMITATION /
LOCAL_PASS`; odak `1/1`, komşu `77/77`, tam checker `852/852 PASS`,
compileall/workspace/diff PASS. Gerçek reconnect worker, REST catch-up,
core/economic binding, mutation ve mainnet authority yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş recovery anchor post-gap re-entry ve
paired snapshot gate parity regresyonudur.

## Önceki görev — 2026-09-19 P2.04 recovery anchor mixed component equal-boundary ve late-event quarantine parity

Transaction component ilerleyip event component geride kaldığında ve ters yönde
de equal max snapshot `SYNCED` oluyor. Terminal anchor sonrası
mixed-component late/forward event’ler `QUARANTINED`, exact replay `DUPLICATE`
kalıyor; boş SQLite journal değişmiyor. Durum `IMPLEMENTED_WITH_LIMITATION /
LOCAL_PASS`; odak `1/1`, komşu `76/76`, tam checker `851/851 PASS`,
compileall/workspace/diff PASS. Gerçek reconnect worker, REST catch-up,
core/economic binding, mutation ve mainnet authority yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş recovery anchor paired-component strict
ordering ve quarantine parity regresyonudur.

## Önceki görev — 2026-09-19 P2.04 recovery anchor transaction/event cursor component parity

Transaction component ilerleyip event component geride kaldığında ve event
component ilerleyip transaction component geride kaldığında `209` gözlem zamanlı
authoritative snapshot `SNAPSHOT_STALE`, max component `210` snapshot `SYNCED`
oluyor; boş SQLite journal değişmiyor. Durum `IMPLEMENTED_WITH_LIMITATION /
LOCAL_PASS`; odak `1/1`, komşu `75/75`, tam checker `850/850 PASS`,
compileall/workspace/diff PASS. Gerçek reconnect worker, REST catch-up,
core/economic binding, mutation ve mainnet authority yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş recovery anchor mixed component
equal-boundary ve late-event quarantine parity regresyonudur.

## Önceki görev — 2026-09-19 P2.04 equal-cursor recovery anchor sonrası snapshot freshness boundary ve terminal quarantine parity

Recovery anchor sonrası `209` gözlem zamanlı authoritative snapshot
`SNAPSHOT_STALE`, eşik `210` snapshot `SYNCED` oluyor. Recovery terminal
identity exact replay `DUPLICATE`, eski ve ileri event’ler `QUARANTINED` kalıyor;
boş SQLite journal değişmiyor. Durum `IMPLEMENTED_WITH_LIMITATION /
LOCAL_PASS`; odak `1/1`, komşu `74/74`, tam checker `849/849 PASS`,
compileall/workspace/diff PASS. Gerçek reconnect worker, REST catch-up,
core/economic binding, mutation ve mainnet authority yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş recovery anchor transaction/event cursor
component parity regresyonudur.

## Önceki görev — 2026-09-19 P2.04 equal-cursor replacement anchor sonrası same-cursor replacement fingerprint conflict ve snapshot gate parity

Aynı replacement identity’nin farklı fingerprint’i `CONFLICT/GAP` açıyor;
doğrudan authoritative snapshot reddediliyor. Yalnız yeni equal-cursor recovery
anchor ve taze snapshot ile `SYNCED` açılıyor; recovery exact replay
`DUPLICATE`, boş SQLite journal değişmiyor. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `73/73`, tam
checker `848/848 PASS`, compileall/workspace/diff PASS. Gerçek reconnect worker,
REST catch-up, core/economic binding, mutation ve mainnet authority yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş equal-cursor recovery anchor sonrası
snapshot freshness boundary ve terminal quarantine parity regresyonudur.

## Önceki görev — 2026-09-19 P2.04 equal-cursor replacement anchor sonrası terminal identity ve late-event quarantine parity

Equal-cursor replacement anchor ile kurulan terminal identity’nin exact replay’i
`DUPLICATE`, terminal öncesi geç kalan event ve terminal sonrası ileri event
`QUARANTINED` kalıyor; coordinator `SYNCED` durumunu koruyor ve boş SQLite
journal değişmiyor. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak
`1/1`, komşu `72/72`, tam checker `847/847 PASS`, compileall/workspace/diff
PASS. Gerçek reconnect worker, REST catch-up, core/economic binding, mutation
ve mainnet authority yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş terminal replacement anchor sonrası
same-cursor replacement fingerprint conflict ve snapshot gate parity
regresyonudur.

## Önceki görev — 2026-09-19 P2.04 terminal replacement anchor sonrası equal-cursor resync identity ve snapshot gate re-entry parity

Equal cursor’lı yeni replacement identity stale sayılmadan
`RECONCILIATION_REQUIRED` durumuna dönüyor; snapshot olmadan `mark_synced`
`AUTHORITATIVE_SNAPSHOT_REQUIRED` ile fail-closed kalıyor. Taze authoritative
snapshot sonrası aynı replacement `DUPLICATE` oluyor ve boş SQLite journal
değişmiyor. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`,
komşu `71/71`, tam checker `846/846 PASS`, compileall/workspace/diff PASS.
Gerçek reconnect worker, REST catch-up, core/economic binding, mutation ve
mainnet authority yok. Kanıt: `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş equal-cursor replacement anchor sonrası
terminal identity ve late-event quarantine parity regresyonudur.

## Önceki görev — 2026-09-19 P2.04 terminal replacement anchor sonrası stale resync anchor ve snapshot gate re-entry parity

Stale resync anchor `RESYNC_ANCHOR_STALE` ile reddediliyor; bu hata sonrası
`GAP` durumunda doğrudan snapshot uygulanamıyor (`SYNC_STATE_INVALID`). Yalnız
monotonic replacement anchor ve taze authoritative snapshot ile `SYNCED`
açılıyor; boş SQLite journal değişmiyor. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `70/70`, tam
checker `845/845 PASS`, compileall/workspace/diff PASS. Gerçek reconnect worker,
REST catch-up, core/economic binding, mutation ve mainnet authority yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş terminal replacement anchor sonrası
equal-cursor resync identity ve snapshot gate re-entry parity regresyonudur.

## Önceki görev — 2026-09-19 P2.04 terminal replacement anchor sonrası snapshot cursor freshness ve stale-boundary parity

Terminal anchor’ın transaction zamanı ve event zamanı ayrı ayrı sınandı;
cursor’ın en büyük bileşeninden eski `209` snapshot `SNAPSHOT_STALE`, eşit
`210` snapshot fresh kabul ediliyor. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `69/69`, tam
checker `844/844 PASS`, compileall/workspace/diff PASS. Gerçek reconnect worker,
REST catch-up, core/economic binding, mutation ve mainnet authority yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş terminal replacement anchor sonrası stale
resync anchor ve snapshot gate re-entry parity regresyonudur.

## Önceki görev — 2026-09-19 P2.04 empty/reopen replacement anchor sonrası terminal cursor ve late-event quarantine parity

Terminal `REJECT` replacement anchor sonrası exact replay `DUPLICATE`,
terminal öncesi late event ve terminal sonrası yeni event `QUARANTINED` kalıyor;
coordinator yanlışlıkla `SYNCED` durumundan çıkmıyor ve boş SQLite journal
değişmiyor. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`,
komşu `68/68`, tam checker `843/843 PASS`, compileall/workspace/diff PASS.
Gerçek reconnect worker, REST catch-up, core/economic binding, mutation ve
mainnet authority yok. Kanıt: `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş terminal replacement anchor sonrası
snapshot cursor freshness ve stale-boundary parity regresyonudur.

## Önceki görev — 2026-09-19 P2.04 empty/reopen aynı cursor identity conflict ve snapshot gate parity

Boş SQLite journal yeniden açıldıktan sonra resync anchor ile kurulan event
exact duplicate olarak kalıyor; aynı event kimliğinin farklı fingerprint’i
`CONFLICT` açıp `GAP` durumuna geçiriyor. Snapshot bu durumda doğrudan
uygulanamıyor; replacement anchor ve fresh snapshot olmadan `SYNCED` açılamıyor.
Journal anchor işlemleriyle değişmiyor ve boş kalıyor. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `67/67`, tam
checker `842/842 PASS`, compileall/workspace/diff PASS. Gerçek reconnect
worker, REST catch-up, core/economic binding, mutation ve mainnet authority
yok. Kanıt: `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş empty/reopen replacement anchor sonrası
terminal cursor ve late-event quarantine parity regresyonudur.

## Önceki görev — 2026-09-19 P2.04 empty/reopen cursor freshness ve resync-anchor parity

Boş SQLite journal yeniden açıldığında cursor `()` kalıyor ve authoritative
snapshot kapısı korunuyor; boş başlangıçtan uygulanan anchor için cursor
çiftinden eski snapshot reddediliyor, taze snapshot ile `SYNCED` açılıyor.
Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `66/66`,
tam checker `841/841 PASS`, compileall/workspace/diff PASS. Gerçek reconnect
worker, REST catch-up, core/economic binding, mutation ve mainnet authority
yok. Kanıt: `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş empty/reopen sonrası aynı cursor
identity conflict ve snapshot gate parity regresyonudur.

## Önceki görev — 2026-09-19 P2.04 restart terminal cursor freshness ve authoritative snapshot sınır parity

Restart ile hydrate edilen terminal cursor için anchor gözlem zamanı hem
transaction hem event zamanını kapsıyor; authoritative snapshot cursor
çiftinin en güncel bileşeninden eskiyse `SNAPSHOT_STALE` ile reddediliyor.
Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `65/65`,
tam checker `840/840 PASS`, compileall/workspace/diff PASS. Gerçek reconnect
worker, REST catch-up, core/economic binding, mutation ve mainnet authority
yok. Kanıt: `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş empty/reopen cursor freshness ile
resync-anchor parity regresyonudur.

## Önceki görev — 2026-09-19 P2.04 terminal replay conflict ve restart snapshot parity

İkinci açılışta terminal snapshot değişmeden kalıyor; terminal event exact
duplicate, aynı event kimliğinin farklı fingerprint’i `CONFLICT` ve
coordinator’da GAP oluyor. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`;
odak `1/1`, komşu `64/64`, tam checker `839/839 PASS`,
compileall/workspace/diff PASS. Gerçek reconnect worker, REST catch-up,
core/economic binding, mutation ve mainnet authority yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş restart sonrası terminal cursor
freshness ve authoritative snapshot sınır parity regresyonudur.

## Önceki görev — 2026-09-18 P2.04 listStatus read-only sequence/gap quarantine

P2.04’ün read-only `listStatus` OCO kimliği için yeni venue sequence
üretilmeden `(transaction_time_ms,event_time_ms)` cursor’ı non-decreasing
doğrulanıyor. Exact duplicate/no-op, event-ID fingerprint conflict ve
out-of-order `GAP` fail-closed; `RECONCILIATION_REQUIRED`, `STALE` ve `GAP`
durumlarında yeni listStatus olayı quarantine ediliyor. Reconnect sonrası
explicit reconciliation olmadan acceptance yok. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `37/37 PASS`, tam checker
`812/812 PASS`, compileall/workspace/diff PASS. Parser’ın taşımadığı leg
status/role/type, fiyat, miktar, fee veya fill çıkarılmıyor; ekonomik/core
event, REST catch-up, canlı reconnect, mutation veya mainnet authority yok.
Kanıt: `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Sıradaki tek asistan-owned güvenli iş explicit offline reconciliation
anchor/resync contract’ını aynı fail-closed sınırda doğrulamaktır.

## Önceki görev — 2026-09-18 P2.04 listStatus → bounded SQLite journal sınırı

P2.04’ün read-only `listStatus` OCO parser çıktısı ayrı
`USER_STREAM_LIST_STATUS` observation olarak bounded `OrderListEventStore` içine
bağlandı ve `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` ile kapandı. Canonical
JSON + SHA-256 checksum, transaction-time monotonic sıra, restart replay,
exact duplicate/no-op, identity conflict ve out-of-order/terminal fail-closed
davranışı doğrulandı. Parser’ın taşımadığı leg status/role/type, fiyat, miktar,
fee veya fill çıkarılmıyor; observation ekonomik/core event’e yükseltilmiyor.
Odak `25/25 PASS`; tam checker `810` testte `808 PASS`, iki Windows Credential
Manager ortam hatası (`1312`, `CREDENTIAL_NOT_FOUND`) kaldı. Compileall,
workspace (`296` aktif Python dosyası) ve diff check PASS. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Canlı event tüketimi, reconnect/catch-up, mutation veya mainnet authority
açılmadı. Sıradaki tek asistan-owned güvenli iş read-only stream
sequence/gap quarantine ve reconnect/catch-up sınırının offline
doğrulanmasıdır.

## Önceki görev — 2026-09-18 P2.03 durable venue-event journal ve observation sequencing

P2.03’ün exact venue reconciliation sonuçları ve cancel-replace identity
gözlemleri `OrderListEventStore` ile bounded SQLite journal’a bağlandı.
Canonical JSON + SHA-256 checksum, monotonic sequence, restart replay, exact
duplicate/no-op, conflict, out-of-order/terminal fail-closed ve
`BEGIN IMMEDIATE` rollback doğrulandı. Journal redacted venue-fact observation
taşır; fill, core event, economic state, mutation veya signed transport
authority açmaz. Odak `18/18 PASS`; tam checker `806` testte `804 PASS`, iki
Windows Credential Manager ortam hatası (`1312`, `CREDENTIAL_NOT_FOUND`) kaldı.
Compileall, workspace (`296` aktif Python dosyası) ve diff check PASS. Kanıt:
`evidence/P2.03/MARKET_CONDITIONAL_ORDER_LIST_CONTRACT_SONUC.md`.

Sıradaki tek güvenli iş read-only User Data Stream order-list event
parser/adapter contract kapısıdır.

## 2026-09-18 P2.03 venue event reconciliation ve cancel-replace identity (önceki dilim)

P2.03’ün SQLite durable replay owner’ı üzerine venue event reconciliation ve
cancel-replace identity dilimi `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` oldu.
OCO event’leri exact `orderListId` + `listClientOrderId` ve exact leg kimliğiyle
redacted evidence’a bağlanıyor; uyuşmazlık `CONFLICT`. Cancel-replace sonucu
`cancelResult`/`newOrderResult` ikilisi ve immutable prior/replacement
identity’leriyle sınıflandırılıyor; eksik veya tutarsız kombinasyon `UNKNOWN`,
cancel reddedilip yeni emir kabul edildiğinde yeniden reconciliation gerekiyor.
Bu dilim fill, core event, economic state, mutation veya signed transport
authority açmıyor. Odak `5/5 PASS`; tam checker `801` testte `799 PASS`, iki
Windows Credential Manager ortam hatası (`1312`, `CREDENTIAL_NOT_FOUND`) kaldı.
Compileall, workspace ve diff check PASS. Kanıt:
`evidence/P2.03/MARKET_CONDITIONAL_ORDER_LIST_CONTRACT_SONUC.md`.

Sıradaki tek güvenli iş durable venue-event journal ve cancel-replace
observation sequencing kapısıdır.

## 2026-09-18 P2.03 SQLite atomic durable replay owner (önceki dilim)

P2.03’ün OCO identity/state projection dilimi ve SQLite durable replay owner’ı
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` oldu. `OrderListStore`, identity ve
bounded observation journal’ını canonical JSON + SHA-256 checksum ile saklıyor;
`BEGIN IMMEDIATE` transaction içinde append, exact duplicate/conflict,
ordered replay ve rollback birlikte korunuyor. Restart sonrası aynı snapshot
yeniden kuruluyor; ekonomik fill/core/order authority açılmıyor. OCO contract +
durable store odak `8/8 PASS`; tam checker `796` testte `794 PASS`, yalnız iki
Windows Credential Manager ortam hatası (`1312`, `CREDENTIAL_NOT_FOUND`) kaldı.
Compileall, workspace (`292` aktif Python dosyası) ve diff check PASS. Sıradaki
tek güvenli iş venue event reconciliation ve cancel-replace identity karar
kapısıdır. Kanıt:
`evidence/P2.03/MARKET_CONDITIONAL_ORDER_LIST_CONTRACT_SONUC.md`.

## 2026-09-18 P1.16.a Chronological split sınırı

P1.16.a `COMPLETE_WITH_LIMITATION / LOCAL_PASS` olarak kapandı. Public
`ChronologicalSplit` kurucusu bölüm sırası, gap/test sınırı, duplicate sample
identity ve yanlış point tipi bypass’larını fail-closed reddediyor;
`ChronologicalPoint` exact string ve non-negative integer event-time sınırını
koruyor. Odak `7/7 PASS`, bağımsız chronological oracle `PASS`, Noether
salt-okunur Codex review `PASS_WITH_LIMITATION` (P1/P2 bulgu yok),
compile/diff `PASS`. `tools/run_checks.py` ve `tools/check_workspace.py`
Python `3.13` gereksinimi nedeniyle bundled `3.12.14` ile çalışmadı;
`active_python_files: 286`, güncel tam-suite/workspace sonucu iddia edilmiyor.
Gap yalnız yapısal ayrımdır; purge/embargo, OOS freeze, feature/label
leakage, persistence, API/UI, ekonomik hesap ve venue authority açılmadı.
Kanıt: `evidence/P1.16.a/SONUC.md`.

Sıradaki tek güvenli iş `P1.16.b` OOS freeze ve evaluation lineage karar
kapısıdır.

## 2026-09-18 P1.16.b OOS freeze ve evaluation lineage sınırı

P1.16.b `COMPLETE_WITH_LIMITATION / LOCAL_PASS` olarak kapandı. Public
`EvaluationLineage` ve `OosTuningDecision` modellerinde exact string doğrulaması
ile custom equality/string-subclass allowlist bypass’ı fail-closed düzeltildi.
OOS öncesi tuning `TUNING_ALLOWED`; inspection sonrası eski lineage `TOUCHED`
olur ve `NEW_EXPERIMENT_REQUIRED` döner; touched lineage yeniden untouched ya
da inspected gösterilemez. Odak `5/5 PASS`, bağımsız OOS freeze oracle `PASS`,
Hilbert salt-okunur Codex re-review `PASS` (P1/P2 bulgu yok),
compile/diff `PASS`. Python `3.13` gereksinimi nedeniyle checker’lar bundled
`3.12.14` ile çalışmadı (`active_python_files: 286`); güncel tam-suite/workspace
sonucu iddia edilmiyor. Dataset/run binding, purge/embargo, feature/label
leakage, persistence, API/UI, ekonomik hesap ve venue authority açılmadı.
Kanıt: `evidence/P1.16.b/SONUC.md`.

Sıradaki tek güvenli iş `P1.16.c` feature/label horizon ve purge/embargo karar
kapısıdır.

## 2026-09-18 P1.16.c Feature/label horizon overlap ve purge kararı

P1.16.c `COMPLETE_WITH_LIMITATION / LOCAL_PASS` olarak kapandı. `TimeInterval`
half-open `[start,end)` sınırı korunuyor; adjacent aralık `NO_OVERLAP`, gerçek
kesişim `PURGE_REQUIRED`. Public assessment constructor’ı status/ID tutarlılığı,
duplicate ID, exact tuple/interval tipi ve custom equality bypass’larını
fail-closed reddediyor. Odak `5/5 PASS`, bağımsız horizon oracle `PASS`, Pauli
salt-okunur Codex re-review `PASS` (P1/P2 bulgu yok), compile/diff `PASS`.
Python `3.13` gereksinimi nedeniyle checker’lar bundled `3.12.14` ile çalışmadı
(`active_python_files: 286`); güncel tam-suite/workspace sonucu iddia edilmiyor.
Numeric purge/embargo, feature/label dataset binding, OOS/trial/stress lineage,
persistence, API/UI, ekonomik hesap ve venue authority açılmadı. Kanıt:
`evidence/P1.16.c/SONUC.md`.

Sıradaki tek güvenli iş `P1.16.d` multiple-testing trial registry karar
kapısıdır.

## 2026-09-18 P1.16.d Multiple-testing trial registry sınırı

P1.16.d `COMPLETE_WITH_LIMITATION / LOCAL_PASS` olarak kapandı. `TrialStudy`
explicit parameter-space/objective/selection-rule kimliği ve en fazla 1.000
trial sınırı taşıyor; `SUCCEEDED`, `FAILED`, `INVALID` denemelerin tamamı
sayılıyor. Duplicate aynı payload için idempotent, conflict ve limit aşımı
fail-closed. Public model/tuple/subclass ve custom-equality bypass’ları exact
type kontrolleriyle kapatıldı. Odak `6/6 PASS`, evaluation-binding `6/6 PASS`,
trial control `PASS`, ikinci salt-okunur kaynak kontrolü
`PASS_WITH_LIMITATION` (P1/P2 bulgu yok), compile/diff `PASS`. Python `3.13`
gereksinimi nedeniyle checker’lar bundled `3.12.14` ile çalışmadı
(`active_python_files: 286`); API read testi `starlette` eksikliği nedeniyle
çalışmadı ve güncel tam-suite/workspace sonucu iddia edilmiyor. Optimizer,
score/KPI, winner selection, persistence, dataset binding, OOS/stress result,
purge/embargo, API/UI ve ekonomik hesap açılmadı. Production readiness `NO`.
Kanıt: `evidence/P1.16.d/SONUC.md`.

Sıradaki tek güvenli iş `P1.16.e` stress lineage ve ayrı sonuç kimliği karar
kapısıdır.

## 2026-09-18 P1.16.e Stress lineage ve ayrı sonuç kimliği

P1.16.e `COMPLETE_WITH_LIMITATION / LOCAL_PASS` olarak kapandı.
`StressLineage` base result, stress profile ve profile hash girdilerinden
deterministic ayrı `stress_result_id` türetiyor; public kurucu canonical kimlik
eşleşmesini, sabit `STRESS` etiketini ve exact string/hash tiplerini fail-closed
doğruluyor. Odak `4/4 PASS`, evaluation-binding `6/6 PASS`, bağımsız canonical
kimlik kontrolü `PASS`, ikinci salt-okunur kaynak kontrolü
`PASS_WITH_LIMITATION` (P1/P2 bulgu yok), compile/diff `PASS`. Python `3.13`
gereksinimi nedeniyle checker’lar bundled `3.12.14` ile çalışmadı
(`active_python_files: 286`); API read testi `starlette` eksikliği nedeniyle
çalışmadı ve güncel tam-suite/workspace sonucu iddia edilmiyor. Ekonomik stress
modeli, seed/RNG, persistence, dataset/config/model binding, optimizer, API/UI
ve purge/embargo açılmadı. Production readiness `NO`. Kanıt:
`evidence/P1.16.e/SONUC.md`.

Sıradaki tek güvenli iş `P1.16.f` warmup leakage ve readiness binding karar
kapısıdır.

## 2026-09-18 P1.16.f Warmup leakage ve readiness binding

P1.16.f `DEFERRED / NO-GO / RESEARCH_AUDITED / LOCAL_PASS` olarak kapatıldı;
production readiness `NO`. QuantConnect warm-up sırasında trade
yerleştirilmediğini, Freqtrade ise stabil indicator history’sinin gerçek
strategy lookback’inden türetilmesini ve unstable başlangıç bölümünün
backtestten çıkarılmasını doğruluyor. Local source audit’te
`signal_readiness.py` yalnız caller warmup sayısını sınıflandırıyor; mevcut
historical simulation/plan/contract zincirinde feature/indicator/label adapterı
yok. Bağımsız stdlib warmup/lookahead oracle `PASS`. Yeni numeric warmup,
indicator authority veya warmup event’lerinden fill üreten ekonomik kod
açılmadı. Kanıt: `evidence/P1.16.f/SONUC.md`.

Sıradaki tek güvenli iş `P1.16.g` local feature/label horizon ve gerçek run
binding karar kapısıdır.

## 2026-09-18 P1.16.g Local feature/label horizon ve gerçek run binding

P1.16.g `COMPLETE_WITH_LIMITATION / LOCAL_PASS` olarak kapatıldı; production
readiness `NO`. Bounded exact `CLOSE_SMA`, `CLOSE_RETURN` ve
`FUTURE_CLOSE_RETURN` pipeline’ı closed-bar, chronology, lookback/horizon ve
1.000 bar limitiyle fail-closed uygulandı. Binding run planına, historical
reducer’a ve capture identity’sine bağlandı; warmup barlarında action üretilmiyor
ve tam binding reducer başlamadan yeniden doğrulanıyor. Capture kimliği dataset,
artifact, config, pipeline, feature/label, warmup, horizon ve eligible row
bağını checksum’lıyor. `4/4`, `6/6`, `26/26` odak regresyonları ile
compile/workspace/diff geçti; tam checker `786/788 PASS`, iki Windows Credential
Manager ortam hatası kaldı. Kanıt: `evidence/P1.16.g/SONUC.md`.

Numeric purge/embargo, ekonomik KPI/OOS, optimizer, stress model, persistence
schema, API/UI opt-in profili ve canlı venue davranışı bu fazda açılmadı.

Sıradaki tek güvenli iş `P1.16.i` stress ekonomik modeli ve gerçek senaryo
runner karar kapısıdır.

## 2026-09-18 P1.15.c Two-leg persistence/replay/recovery karar kapısı

P1.15.c mevcut checkout üzerinde yeniden doğrulandı ve güvenli karar değişmedi:
`LifecycleStore` `NON_ECONOMIC_LIFECYCLE_ONLY` kapsamındadır; lifecycle şeması
hedge leg/side, quantity, effective-time veya recovery alanlarını taşımıyor.
Generic economic `Store` batch event/posting, hash ve `execution_id` dedup
sağlıyor ancak two-leg identity/state, model lineage veya iki store arasında
atomic binding yok. P1.15.b projection’ını bağlayan adapter bulunmadı.

Persistence sınır regresyonu `30/30 PASS`, bağımsız storage schema control
`PASS`, Beauvoir salt-okunur Codex review `DEFERRED / NO-GO` kararını doğruladı;
compile/diff `PASS`. Python `3.13` gereksinimi nedeniyle tam-suite/workspace
checker bu oturumda çalışmadı; güncel tam-suite sonucu iddia edilmiyor. Faz
`DEFERRED / NO-GO / LOCAL_PASS`, production readiness `NO`; migration, yeni
schema, recovery implementation, cross ownership, margin/liquidation, API/UI
ve venue mutation açılmadı. Test matrisi mevcut ancak
`SPECIFIED_NOT_EXECUTED_AGAINST_LOCAL_CODE`. Kanıt:
`evidence/P1.15.c/SONUC.md`.

Sıradaki tek güvenli iş `P1.16.a` chronological split ve leakage-free
evaluation karar kapısıdır.

## 2026-09-18 P1.15.b Accepted two-leg fill projection

P1.15.b mevcut accepted-fill projection’ı bağımsız kapıyla tamamlandı:
public projection constructor’ı state, identity pair, fill history, exact
aggregate ve status tutarlılığını yeniden doğruluyor. Aynı side/scope
çakışmaları, tamamlanmış leg sonrası history bozulması ve custom equality
whitelist bypass’ı fail-closed düzeltildi. Odak test `7/7 PASS`, ilgili hedge
projection kümesi `11/11 PASS`, bağımsız accepted-fill/malformed-constructor
oracle `PASS`, Bohr salt-okunur Codex review düzeltme sonrası `PASS`; kritik
P1/P2 bulgu yok. Compile/diff `PASS`.

Faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS` olarak kapandı. `tools/run_checks.py`
ve `tools/check_workspace.py` proje Python `3.13` istediği, bu oturumdaki
kullanılabilir bundled runtime `3.12.14` olduğu için tam-suite/workspace
sonucu veremedi; güncel tam-suite sonucu iddia edilmiyor. Production readiness
`NO`; projection yalnız in-memory’dir. Persistence/replay/recovery,
order/reserve/fill posting, cross/margin/liquidation, API/UI ve venue authority
açılmadı. Kanıt: `evidence/P1.15.b/SONUC.md`.

Sıradaki tek güvenli iş `P1.15.c` two-leg persistence/replay/recovery karar
kapısıdır.

## 2026-09-18 P1.15.a Hedge identity ve two-leg state sınırı

P1.15.a mevcut checkout üzerinde doğrulandı ve bağımsız kapısı tamamlandı:
unhashable/wrong-type state girdisinin ham `TypeError` üretmemesi için
`advance_two_leg_state` string guard’ı eklendi; kırmızı regresyonla doğrulanıp
fail-closed `TWO_LEG_STATE_INVALID` olarak düzeltildi. Odak test `4/4 PASS`,
ilgili two-leg projection kümesi `8/8 PASS`, bağımsız hedge/two-leg oracle
`PASS`, Herschel salt-okunur Codex review düzeltme sonrası `PASS`; kritik P1
bulgu yok. Compile/diff `PASS`.

Faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS` olarak kapandı. Proje Python
`3.13` istediği, bu oturumdaki kullanılabilir bundled runtime `3.12.14` olduğu
için `tools/run_checks.py` güncel tam-suite çalıştırılamadı; güncel tam-suite
sonucu iddia edilmiyor. Production readiness `NO`; identity/state boundary
order/reserve/fill posting, persistence, recovery ledger, cross/margin/
liquidation, API/UI ve venue authority açmaz. Kanıt:
`evidence/P1.15.a/SONUC.md`.

Sıradaki tek güvenli iş `P1.15.b` accepted two-leg fill projection karar
kapısıdır.

## 2026-09-18 P1.14.f Template activation ve capability gate

P1.14.f mevcut checkout üzerinde doğrulandı ve bağımsız kapısı tamamlandı:
odak test `4/4 PASS`, ilgili template/projection kümesi `10/10 PASS`,
bağımsız activation oracle `PASS`, Singer salt-okunur Codex review `PASS`;
kritik P1/P2 bulgu yok. `PENDING`/`APPROVED`, unsupported capability
precedence, duplicate/bool allowlist ve non-authority sınırları doğrulandı.
Compile/diff `PASS`.

Faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS` olarak kapandı. Proje Python
`3.13` istediği, bu oturumdaki kullanılabilir bundled runtime `3.12.14` olduğu
için `tools/run_checks.py` güncel tam-suite çalıştırılamadı; güncel tam-suite
sonucu iddia edilmiyor. Production readiness `NO`; gate activation, candidate,
order/reserve/fill, persistence, API/UI veya venue authority açmaz. Kanıt:
`evidence/P1.14.f/SONUC.md`.

Sıradaki tek güvenli iş `P1.15.a` hedge/cross/two-leg kapsam karar kapısıdır.

## 2026-09-18 P1.14.e Strategy template integrity ve non-authority

P1.14.e mevcut checkout üzerinde doğrulandı ve bağımsız kapısı tamamlandı:
public `StrategyTemplate(...)` kurucusundaki duplicate capability bypass’ı
bağımsız review’da bulundu, kırmızı regresyonla doğrulandı ve `__post_init__`
fail-closed guard’ıyla düzeltildi. Odak test `6/6 PASS`, ilgili projection
kümesi `14/14 PASS`, bağımsız canonical/hash/non-authority oracle `PASS`,
Turing salt-okunur Codex review düzeltme sonrası `PASS`; kritik P1/P2 bulgu
yok. Compile/diff `PASS`.

Faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS` olarak kapandı. Proje Python
`3.13` istediği, bu oturumdaki kullanılabilir bundled runtime `3.12.14` olduğu
için `tools/run_checks.py` güncel tam-suite çalıştırılamadı; güncel tam-suite
sonucu iddia edilmiyor. Production readiness `NO`; template yalnız inert
configuration artifact’tır ve activation/candidate/order/reserve/fill,
persistence, API/UI veya venue authority açmaz. Kanıt:
`evidence/P1.14.e/SONUC.md`.

Sıradaki tek güvenli iş `P1.14.f` template activation/capability gate karar
kapısıdır.

## 2026-09-18 P1.14.d Rebalancing threshold/time trigger projection

P1.14.d mevcut checkout üzerinde doğrulandı ve bağımsız kapısı tamamlandı:
odak test `8/8 PASS`, ilgili projection kümesi `14/14 PASS`, bağımsız
Decimal/time oracle `PASS`, Mendel salt-okunur Codex review `PASS`; kritik
`BLOCKED` bulgu yok. NaN/Infinity/exponent/malformed decimal, threshold=0,
signed zero, aynı timestamp ve tüm bool zaman girdileri regresyon kapsamına
alındı. Compile/diff `PASS`.

Faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS` olarak kapandı. Proje Python
`3.13` istediği, bu oturumdaki kullanılabilir bundled runtime `3.12.14` olduğu
için `tools/run_checks.py` güncel tam-suite çalıştırılamadı; güncel tam-suite
sonucu iddia edilmiyor. Production readiness `NO`; trigger yalnız salt-okunur
projection’dır ve order/candidate/fill, persistence, API/UI veya venue
authority açmaz. Kanıt: `evidence/P1.14.d/SONUC.md`.

Sıradaki tek güvenli iş `P1.14.e` template integrity ve non-authority karar
kapısıdır.

## 2026-09-18 P1.14.c Signal warmup, closed-bar ve stale readiness kapısı

P1.14.c mevcut checkout üzerinde doğrulandı ve bağımsız kapısı tamamlandı:
odak test `6/6 PASS`, readiness ile ilgili küme `12/12 PASS`, bağımsız
readiness oracle `PASS`, Locke salt-okunur Codex review `PASS`; kritik
`BLOCKED` bulgu yok. Stale threshold eşitliği ve tüm gate bool tipleri için
regresyon kapsamı eklendi. Compile/diff `PASS`.

Faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS` olarak kapandı. Proje Python
`3.13` istediği, bu oturumdaki kullanılabilir bundled runtime `3.12.14` olduğu
için `tools/run_checks.py` güncel tam-suite çalıştırılamadı; güncel tam-suite
sonucu iddia edilmiyor. Production readiness `NO`; readiness yalnız gate
projection’ıdır ve candidate/order/fill, adapter, trigger, persistence, API/UI
ve venue authority açmaz. Kanıt: `evidence/P1.14.c/SONUC.md`.

Sıradaki tek güvenli iş `P1.14.d` threshold/time rebalancing trigger karar
kapısıdır.

## 2026-09-18 P1.14.b Signal identity, event-time ve dedupe doğrulaması

P1.14.b mevcut checkout üzerinde doğrulandı ve bağımsız kapısı tamamlandı:
bağımsız review’da bulunan duplicate-history açığı fail-closed guard ve
regresyon testiyle düzeltildi; odak test `6/6 PASS`, readiness ile ilgili signal
kümesi `11/11 PASS`, ayrı signal oracle `PASS`, Ptolemy salt-okunur Codex review
düzeltme sonrası `PASS`; kritik `BLOCKED` bulgu yok. Compile ve diff
kontrolleri `PASS`.

Faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS` olarak kapandı. Proje Python
`3.13` istediği, bu oturumdaki kullanılabilir bundled runtime `3.12.14` olduğu
için `tools/run_checks.py` güncel tam-suite çalıştırılamadı; güncel tam-suite
sonucu iddia edilmiyor. Production readiness `NO`; signal yalnız immutable
source/event-time projection ve dedupe sınırıdır; candidate/order/fill,
auth/replay window, warmup/closed-bar, persistence, API/UI veya venue authority
açılmaz. Kanıt: `evidence/P1.14.b/SONUC.md`.

## 2026-09-17 P1.13.h.d Reverse/Infinity boundary bağımsız inceleme ve kritik regresyon kapısı

Erdos’un salt-okunur Codex incelemesi h.a–h.c varyant sınırını `PASS` olarak
doğruladı; kritik BLOCKED bulgu bulunmadı. Literal boundary oracle `3/3`,
h.a+h.c gate kümesi `6/6`, hedefli sınır kümesi `9/9`, geniş Futures Grid
doğrulama kümesi `53/53 PASS`; compile/diff PASS.

Exact source/oracle yokluğu sürdüğü için Reverse/Infinity vendor parity
`DEFERRED / NO-GO`; ürün sonucu `NOT_SUPPORTED + BLOCKED`, authority alanları
`NONE` olarak kaldı. Kanıt: `evidence/P1.13.h.d/SONUC.md`.

Sıradaki tek güvenli iş `P1.14.c` signal warmup/closed-bar ve stale-policy
karar kapısıdır.
P1.13.h yalnız exact source/oracle gelirse yeniden açılacaktır.

## 2026-09-18 P1.14.a Rebalancing exact target/delta projection doğrulaması

P1.14.a mevcut checkout üzerinde yeniden doğrulandı ve bağımsız kapısı
tamamlandı: odak test `6/6 PASS`, ayrı Decimal oracle `PASS`, Erdos
salt-okunur Codex review `PASS`; kritik `BLOCKED` bulgu yok. Compile ve diff
kontrolleri `PASS`.

Faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS` olarak kapandı. Proje Python
`3.13` istediği, bu oturumdaki kullanılabilir bundled runtime `3.12.14` olduğu
için `tools/run_checks.py` güncel tam-suite çalıştırılamadı; güncel tam-suite
sonucu iddia edilmiyor. Production readiness `NO`; projection yalnız exact
target/delta adayıdır ve order/reserve/fill, fee/rounding, conversion,
balance, persistence, signal/template, API/UI veya venue authority açmaz.
Kanıt: `evidence/P1.14.a/SONUC.md`.

## 2026-09-17 P1.13.h.c Reverse/Infinity `NOT_SUPPORTED` admission sınırı

H.a typed fail-closed gate’i ürün admission katmanına bağlandı. Exact
source/oracle yokken Reverse ve Infinity için sonuç açıkça
`availability=NOT_SUPPORTED` ve `admission=BLOCKED`; order/economic authority
`NONE` kalır. Reverse Futures short’a, Infinity generic Futures Grid’e sessizce
map edilmez.

Alt faz `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, vendor-eşdeğer
implementation `DEFERRED / NO-GO`. Yeni odak `3/3 PASS`, h.a+h.c `6/6 PASS`,
ilgili Futures Grid doğrulama kümesi `50/50 PASS`, compile/diff PASS. Kanıt:
`evidence/P1.13.h.c/SONUC.md`.

Sıradaki tek güvenli iş `P1.13.h.d` h.a–h.c varyant boundary’si için bağımsız
inceleme ve kritik regresyon kapısıdır; exact source/oracle olmadan
implementation açılmayacaktır.

## 2026-09-17 P1.13.h.b Reverse/Infinity Futures Grid araştırma karşı-auditi

Mevcut 3Commas/Pionex ürün araştırmaları ile Futures Grid primary-source
lifecycle audit’i karşılaştırıldı. Reverse Grid’in ayrı bir spot ürün olduğu ve
Futures short olmadığı korunuyor. Infinity Grid’de sabit üst limit olmaması,
inventory/sermaye/lower-bound/fill garantisi anlamına gelmiyor. Exact range
transition, reserve, replacement identity, late-fill precedence ve deterministic
replay sözleşmeleri bulunmadı.

Alt faz `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED`, vendor-eşdeğer
implementation `DEFERRED / NO-GO`; h.a `BLOCKED_CONTRACT_REQUIRED` ve tüm
authority alanları `NONE` olarak kaldı. Odak h.a ilgili kümesi `24/24 PASS`,
compile/diff PASS. Kanıt: `evidence/P1.13.h.b/SONUC.md`.

Sıradaki tek güvenli iş `P1.13.h.c` local `NOT_SUPPORTED`/admission sınırıdır;
exact source/oracle olmadan order, economic, persistence veya venue davranışı
açılmayacaktır.

## 2026-09-17 P1.13.h.a Reverse/Infinity Futures Grid varyant güvenlik kapısı

`REVERSE_GRID` ve `INFINITY_GRID` ayrı typed varyantlar olarak sınıflandırıldı.
Exact contract/oracle doğrulanana kadar her ikisi
`BLOCKED_CONTRACT_REQUIRED`, `order_authority=NONE` ve
`economic_authority=NONE` döndürür. Reverse Grid Futures short’a sessizce map
edilmez; Infinity upper-limit yokluğu inventory, sermaye, lower-bound veya fill
garantisi değildir.

Alt faz `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, vendor-eşdeğer
implementation `DEFERRED / NO-GO`. Odak `3/3 PASS`; g.a–g.c, g.f–g.h ve h.a
ilgili küme `24/24 PASS`; compile/diff PASS. Level/order/replacement,
position/reserve, economic posting, persistence, API/UI ve Binance/Testnet
mutation yoktur. Kanıt: `evidence/P1.13.h.a/SONUC.md`.

Sıradaki tek güvenli iş `P1.13.h.b` mevcut araştırma kaynaklarının exact
Reverse/Infinity sözleşmelerini kapatıp kapatmadığının karşı-auditidir.

## 2026-09-17 P1.13.g.h Futures Grid offline lifecycle bağımsız oracle ve regresyon kapısı

g.g local reducer’ı bağımsız literal transition matrisiyle doğrulandı:
cancel request/confirmation sırası, cancel sonrası fill önceliği, cancel ack
sonrası replacement, erken replacement quarantine, duplicate/conflict kimlik,
invalid sequence ve deterministic replay sınırları test edildi.

Alt faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, local oracle `ORACLE_PASS`,
vendor-eşdeğer implementation `DEFERRED / NO-GO`. Odak `4/4 PASS`; g.a–g.c,
g.f–g.h ilgili küme `21/21 PASS`; compile/diff PASS. Test kapısı yalnız local
in-memory state kullanır; order/fill/replacement, reserve, economic posting,
persistence, API/UI veya Binance/Testnet mutation yoktur. Kanıt:
`evidence/P1.13.g.h/SONUC.md`.

Sıradaki tek güvenli iş `P1.13.h` Reverse/Infinity varyantları için ayrı
karar/kaynak kapısıdır; vendor parity ve gerçek venue davranışı açılmayacaktır.

## 2026-09-17 P1.13.g.g Futures Grid offline lifecycle transition simülasyonu

P1.13.g.f yerel politika kontratı immutable in-memory transition simülasyonuna
bağlandı. Cancel request/confirmation sırası, cancel sonrası fill’in önceliği,
cancel ack olmadan replacement’ın quarantine edilmesi, exact duplicate fill’in
state değiştirmemesi, unknown/conflict quarantine ve deterministic replay
doğrulandı.

Alt faz `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, local simulation
`CONTRACT_READY`, vendor-eşdeğer lifecycle implementation `DEFERRED / NO-GO`.
`FILL_ACCEPTED` yalnız local observation’dır; order/replacement, reserve,
economic posting, persistence, API/UI veya venue authority üretmez. Kapsam
`DCABOT_OFFLINE_SIMULATION_ONLY`; odak `5/5 PASS`, g.a–g.c `10/10 PASS`, g.f
`2/2 PASS`, compile/diff PASS. Kanıt: `evidence/P1.13.g.g/SONUC.md`.

Sıradaki tek güvenli iş local event matrix için bağımsız oracle ve
conflict/replay regresyon kapısıdır; vendor parity ve gerçek venue davranışı
açılmayacaktır.

## 2026-09-17 P1.13.g.f DCABOT yerel Futures Grid lifecycle politika sözleşmesi

Vendor davranışı iddia etmeyen açık bir DCABOT offline politika sözleşmesi
tanımlandı: kabul edilmiş fill cancel yarışında öncelikli, replacement için
cancel terminal onayı gerekli, reserve yalnız terminal exchange event gözlemiyle
serbest bırakılabilir, exact duplicate trade yok sayılır, bilinmeyen/çelişkili
event quarantine/fail-closed kalır ve replay deterministic olmalıdır.

Alt faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, yerel kontrat
`CONTRACT_DECLARED`, vendor-eşdeğer ileri lifecycle implementation
`DEFERRED / NO-GO`. Kod `futures_grid_local_policy.py` yalnız immutable policy
değeri döndürür; kapsam `DCABOT_OFFLINE_SIMULATION_ONLY`, order/economic/
persistence/venue authority `NONE`. Odak `2/2 PASS`, g.a–g.f güvenlik kümesi
`10/10 PASS`, compile/diff PASS. Workspace checker Python 3.13 istediği halde
mevcut bundled Python 3.12 ile çalışmadı; bu ortam sınırlamasıdır. Kanıt:
`evidence/P1.13.g.f/SONUC.md`.

Sıradaki tek güvenli iş explicit politika üzerine offline lifecycle transition
simülasyonudur; gerçek venue, vendor parity, order, reserve mutation,
persistence, API/UI ve Binance/Testnet mutation açılmayacaktır.

## 2026-09-17 P1.13.g.e Futures Grid second primary-source report cross-audit

Yeni raporun seçili kritik iddiaları güncel resmî sayfalarla karşılaştırıldı:
3Commas 2-step/1-step Trailing Up/Down ve Expansion high-level kurallarını,
Binance `ORDER_TRADE_UPDATE`, Modify/amendment ve sınırlı E/T ordering
primitive’lerini doğruluyor. Pionex public Orders API’nin SPOT non-strategic
ile sınırlı olduğu doğrulandı; Futures Grid strategic lifecycle oracle’ı
değil. Exact range transition, replacement identity, pending/reserve,
late-fill authority ve deterministic replay oracle birlikte kapanmadı.

Alt faz `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED`, ileri implementation
`DEFERRED / NO-GO`; dış raporun kanıt kaydı
`evidence/P1.13.g.e/SONUC.md`. P1.13.g.c’nin
`BLOCKED_CONTRACT_REQUIRED` ve `order_authority=NONE` sınırı korunuyor;
order/replacement, reserve, state/economic mutation, persistence, API/UI ve
Binance/Testnet mutation açılmadı. Odak `3/3 PASS`, production readiness
`NO`.

## 2026-09-17 P1.13.g.d Futures Grid primary-source lifecycle audit

Resmî 3Commas/Pionex kaynakları trailing/expansion davranışını yüksek
seviyede, Binance kaynakları exchange-level order/event alanlarını
destekliyor. Exact range transition, replacement identity, pending/reserve
lifecycle, late-fill authority ve deterministic replay oracle birlikte
doğrulanmadı. Alt faz `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED`, ileri
implementation `DEFERRED / NO-GO`; rapor
`docs/P1.13_FUTURES_GRID_LIFECYCLE_PRIMARY_SOURCE_AUDIT.md`, kanıt
`evidence/P1.13.g.d/SONUC.md`.

P1.13.g.c’nin `BLOCKED_CONTRACT_REQUIRED` ve `order_authority=NONE` sınırı
korunuyor. Order/replacement, reserve, state/economic mutation,
persistence, API/UI ve Binance/Testnet mutation açılmadı. Checkout karşı
kontrolü ve odak `3/3 PASS`, compile/workspace/diff PASS; tam son doğrulama
`749` testte `747 PASS`, Windows Credential Manager `1312` nedeniyle `2`
environment error. Production readiness `NO`.

## 2026-09-17 P1.13.g.c Futures Grid replacement/replay ve late-fill identity karar kapısı

`RANGE_REVISION`, `CANCEL_REPLACE`, `LATE_FILL` ve `REPLAY` typed yaşam
döngüsü sınırları olarak ayrıldı. Her sınır exact range transition, replacement
identity, pending/reserve lifecycle, late-fill authority ve deterministic replay
oracle gereksinimlerini açıkça taşır. Exact kaynak/oracle doğrulanana kadar her
karar `BLOCKED_CONTRACT_REQUIRED`; `order_authority=NONE`. Order ID,
replacement ID, candidate level, state mutation, persistence, API/UI ve
Binance/Testnet mutation üretilmedi.

Odak `3/3 PASS`; P1.13.a–d, f.a–f.d, g.a–g.c ilişkili grid kümesi `55/55
PASS`; tam proje `749` testte `747 PASS`, faz dışı Windows Credential Manager
`Windows error 1312` nedeniyle `2` environment error. Compile, workspace ve
`git diff --check` PASS. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, ana
P1.13.g `IN_PROGRESS / IMPLEMENTATION_PENDING`, bağımsız review `NOT_RUN`,
production readiness `NO`. Kanıt: `evidence/P1.13.g.c/SONUC.md`.

P1.13.g’nin kalan advanced davranışları exact source/oracle kanıtı gelene kadar
`CONTRACT_REQUIRED` durumundadır; bu kapıdan ekonomik veya emir yetkisi
çıkarılamaz.

## 2026-09-17 P1.13.g.b Futures Grid advanced variant safety gate

Trailing-up/down, expansion, reversal, range revision, cancel/replace ve replay
varyantları typed enum ile ayrı sözleşmeler olarak sınıflandırıldı. Exact
transition, replacement identity, reserve, late-fill ve replay oracle’ı
doğrulanana kadar her varyant `BLOCKED_CONTRACT_REQUIRED` kalıyor.
`order_authority=NONE`; level, order ID, candidate order, state mutation ve
persistence açılmadı.

Odak `3/3 PASS`; P1.13.a–d, f.a–f.d, g.a ve g.b ilişkili grid kümesi `52/52
PASS`; tam proje `746` testte `744 PASS`, faz dışı Windows Credential Manager
`Windows error 1312` nedeniyle `2` environment error. Compile, workspace ve
`git diff --check` PASS. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, ana
P1.13.g `IN_PROGRESS / IMPLEMENTATION_PENDING`, bağımsız review `NOT_RUN`,
production readiness `NO`. Kanıt: `evidence/P1.13.g.b/SONUC.md`.

P1.13.g.c ile replacement/replay ve late-fill identity karar kapısı kapatıldı;
güncel kayıt `evidence/P1.13.g.c/SONUC.md` içindedir.

## 2026-09-17 P1.13.g.a Futures Grid dynamic order placement boundary

`STATIC` + `FIXED` placement yalnız daha önce exact üretilmiş seviyeleri inert
candidate listesi olarak döndürüyor. `DYNAMIC` placement ve `RANGE_REVISION`,
exact current-price selection, range transition, reserve, cancel/replace
identity ve replay sözleşmesi doğrulanana kadar
`BLOCKED_CONTRACT_REQUIRED` kalıyor. `order_authority=NONE`; order ID,
request, mutation, accepted fill ve persistence açılmadı.

Odak `4/4 PASS`; P1.13.a–d, f.a–f.d ve g.a ilişkili grid kümesi `49/49 PASS`;
tam proje `743` testte `741 PASS`, faz dışı Windows Credential Manager
`Windows error 1312` nedeniyle `2` environment error. Compile, workspace ve
`git diff --check` PASS. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, ana
P1.13.g `IN_PROGRESS / IMPLEMENTATION_PENDING`, bağımsız review `NOT_RUN`,
production readiness `NO`. Kanıt: `evidence/P1.13.g.a/SONUC.md`.

P1.13.g.b ile advanced variant safety gate kapatıldı; güncel kayıt
`evidence/P1.13.g.b/SONUC.md` içindedir.

## 2026-09-17 P1.13.f.d Futures Grid funding/mark/P&L projection

Accepted Futures Grid fill’lerinden realized gross P&L, caller-supplied
reference mark ile unrealized P&L ve signed funding cashflow ayrı projection
olarak üretiliyor. `matched_cycle_profit` açık inventory’yi dışarıda bırakıyor;
`total_pnl` mark hareketini ekliyor. Event identity/asset/time/snapshot
sınırları fail-closed. `total_equity`, venue mark/funding authority, fee
conversion, maintenance margin, liquidation, reserve mutation, persistence,
API/UI ve Binance/Testnet mutation açılmadı.

Odak `5/5 PASS`; P1.13.a–d, f.a–f.d ilişkili grid kümesi `45/45 PASS`; tam
proje `739` testte `737 PASS`, faz dışı Windows Credential Manager
`Windows error 1312` nedeniyle `2` environment error. Compile, workspace ve
`git diff --check` PASS. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, ana
P1.13.f `IN_PROGRESS / IMPLEMENTATION_PENDING`, bağımsız review `NOT_RUN`,
production readiness `NO`. Kanıt: `evidence/P1.13.f.d/SONUC.md`.

P1.13.g.a ile dynamic order placement ve grid range/trailing ayrımı kapatıldı;
güncel kayıt `evidence/P1.13.g.a/SONUC.md` içindedir.

## 2026-09-17 P1.13.f.c Futures Grid isolated margin/leverage and reserve projection

P1.13.f.b ile açılmış LONG/SHORT position state üzerinden caller-supplied
exact `contract_size` ve `reference_price` ile notional ve isolated
initial-margin projection uygulanıyor. Leverage yalnızca
`required_initial_margin = notional / leverage` için kullanılıyor; available
margin yoksa kapasite `UNVERIFIED`, verilirse yalnız local
`ELIGIBLE`/`INSUFFICIENT_AVAILABLE_MARGIN` sonucu üretiliyor. Contract-size `1`
varsayımı, venue balance/reservation authority, maintenance margin, fee,
funding, mark/liquidation, P&L, persistence, API/UI ve Binance/Testnet
mutation açılmadı. Non-terminating sonuç rounding olmadan fail-closed.

Odak `6/6 PASS`; P1.13.a–d, f.a, f.b ve f.c ilişkili grid kümesi `40/40 PASS`;
tam proje `734` testte `732 PASS`, faz dışı Windows Credential Manager
`Windows error 1312` nedeniyle `2` environment error. Compile, workspace ve
`git diff --check` PASS. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, ana
P1.13.f `IN_PROGRESS / IMPLEMENTATION_PENDING`, bağımsız review `NOT_RUN`,
production readiness `NO`. Kanıt: `evidence/P1.13.f.c/SONUC.md`.

P1.13.f.d ile funding/mark/liquidation ve grid profit/total-P&L projection
kapatıldı; güncel kayıt `evidence/P1.13.f.d/SONUC.md` içindedir.

## 2026-09-17 P1.13.f.b Futures Grid one-way position and accepted-fill state

Selected Futures Grid profile içinde yalnız `ONE_WAY` + `FLAT` başlangıçtan
gelen `LONG` veya `SHORT` position projection uygulanıyor. Accepted BUY/SELL
fill’leri exact quantity ve weighted average-entry ile immutable in-memory
state’e ekleniyor; close overflow, ters yönde flat açılış, position flip’i,
conflict duplicate ve geriye giden effective time fail-closed.

Odak `9/9 PASS`; P1.13.a–d, f.a ve f.b ilişkili grid kümesi `34/34 PASS`; tam
proje `728` testte `726 PASS`, faz dışı Windows Credential Manager
`Windows error 1312` nedeniyle `2` environment error. Compile, workspace ve
`git diff --check` PASS. Neutral netleme, non-flat initial position, realized/
unrealized P&L, margin/leverage effect, funding, mark/liquidation,
order/replacement, persistence, API/UI ve Binance/Testnet mutation açılmadı.
Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, ana P1.13.f
`IN_PROGRESS / IMPLEMENTATION_PENDING`, bağımsız review `NOT_RUN`, production
readiness `NO`. Kanıt: `evidence/P1.13.f.b/SONUC.md`.

P1.13.f.c ile isolated margin/leverage ve reserve projection kapatıldı; güncel
kayıt `evidence/P1.13.f.c/SONUC.md` içindedir.

## 2026-09-17 P1.13.f.a Futures Grid v1 profile-bound exact level projection

Futures Grid için Spot Grid’den ayrı `BINANCE/USD_M/USDT/PERPETUAL/ONE_WAY/
ISOLATED` profile ve explicit leverage alanı tanımlandı. `LONG`, `SHORT` ve
`NEUTRAL` direction değerleri taşınıyor; initial-position policy yalnız
`FLAT` kabul ediliyor. Arithmetic/geometric seviyeler exact decimal/rational
kök ve `price_tick`/`tick_origin` ile üretiliyor; off-grid, non-perfect root ve
desteklenmeyen profile/policy fail-closed.

Odak `7/7 PASS`; P1.13.a–d ve f.a ilişkili grid kümesi `25/25 PASS`; tam
proje `719` testte `717 PASS`, faz dışı Windows Credential Manager
`Windows error 1312` nedeniyle `2` environment error. Compile, workspace ve
`git diff --check` PASS. Position/fill, margin/leverage effect, funding,
liquidation, grid-profit/total-equity, order/replacement, persistence, API/UI
ve Binance/Testnet mutation açılmadı. Durum `IMPLEMENTED_WITH_LIMITATION /
LOCAL_PASS`, ana P1.13.f `IN_PROGRESS / IMPLEMENTATION_PENDING`, bağımsız
review `NOT_RUN`, production readiness `NO`. Kanıt:
`evidence/P1.13.f.a/SONUC.md`.

Sıradaki tek iş: `P1.13.f.b` position/initial-position ve accepted-fill state
karar kapısıdır.

## 2026-09-17 P1.13.e Grid trailing-up/down ve reverse/infinity karar kapısı

Araştırma, trailing-up için yalnız gözlenen davranışı destekliyor; exact range
revision, grid-version/pending-order/reserve yaşam döngüsü, cancel-replace
identity, late-fill, replay ve precision sahipliği doğrulanmadı. Reverse/infinity
exact semantics `NOT_VERIFIED / DEFER` durumda. Mevcut exit ratchet ve grid
level üreticisi bu authority'yi taşımıyor; leveraged grid de P1.12/P1.11
bağımlılıkları nedeniyle kapsam dışı.

Kod değişikliği yok. Son doğrulanmış checkout baseline'ında tam proje `712`
testte `710 PASS`, Windows Credential Manager `Windows error 1312` nedeniyle
`2` environment error; workspace, compile ve diff kontrolleri PASS. Bağımsız
review `NOT_RUN`, production readiness `NO`. Durum `DEFERRED / NO-GO /
LOCAL_PASS`; kanıt: `evidence/P1.13.e/SONUC.md`.

Sıradaki tek iş: `P1.13.f` Futures Grid v1 için ayrı profile ve exact
projection karar kapısıdır.

## 2026-09-17 P1.13.d Spot Grid geometric precision/quantization

Geometric grid exact rational `N`-inci root ve explicit `price_tick`/
`tick_origin` ile sınırlandı. Perfect-root olmayan oran veya off-tick seviye
reddediliyor; otomatik rounding, float yaklaşımı ve endpoint düzeltmesi yok.

Odak `9/9 PASS`; P1.13.a–d ilişkili küme `18/18 PASS`; tam proje `712` testte
`710 PASS`, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle
`2` environment error. Bağımsız literal oracle, compile, read-only
AST/write-surface, workspace ve `git diff --check` PASS. Fee,
inventory/fill, replacement, API/UI, Store/persistence ve Binance/Testnet
mutation açılmadı; `order_authority=NONE`. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, production readiness `NO`. Kanıt:
`evidence/P1.13.d/SONUC.md`.

P1.13.e kararı `DEFERRED / NO-GO` olarak kapatıldı; sıradaki tek iş:
`P1.13.f` Futures Grid v1 için ayrı profile ve exact projection karar
kapısıdır.

## 2026-09-17 P1.13.c Spot Grid fee ve cycle/equity projection

İlk offline arithmetic Spot Grid profili quote-asset fee ve explicit
`EXACT_NO_ROUNDING` sözleşmesiyle sınırlandı. Accepted BUY/SELL çifti mevcut
immutable inventory projection üzerinden doğrulanıyor; matched cycle profit
ile explicit mark price’a bağlı total equity ayrı exact alanlarda tutuluyor.
Base/third fee asset’i ve venue quantization profili fail-closed kalıyor.

Odak `5/5 PASS`; P1.13.a–c ilişkili küme `13/13 PASS`; tam proje `707` testte
`705 PASS`, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle
`2` environment error. Bağımsız Decimal oracle, compile, read-only
AST/write-surface, workspace ve `git diff --check` PASS. Store/persistence,
reserve/replacement, API/UI, Binance/Testnet mutation ve canlı order yok;
`order_authority=NONE`. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`,
production readiness `NO`. Kanıt: `evidence/P1.13.c/SONUC.md`.

Sıradaki tek iş: `P1.13.d` geometric seviye precision/quantization karar kapısı.

## 2026-09-17 P1.12.g.a Futures DCA start-condition gate

Futures DCA için `IMMEDIATE`, `CLOSED_CANDLE` ve mevcut `SignalReadiness` ile
`SIGNAL` start koşulları source-time üzerinden salt-okunur değerlendiriliyor.
Closed-bar sınırı inclusive; closed-bar/warmup/staleness kararı signal gate’te
kalıyor. Odak `20/20 PASS`; tam proje `634` testte `632 PASS`, faz dışı Windows
Credential Manager `Windows error 1312` nedeniyle `2` environment error.
Compile, AST/write-surface ve `git diff --check` PASS. `order_authority=NONE`;
lifecycle, order, fill, reserve, persistence ve Binance/Testnet mutation yok.
Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
evidence/P1.12.g.a/SONUC.md.

P1.12.g.b ile tamamlandı. Sıradaki tek iş: `P1.12.g.c` average-entry TP ve
split-TP miktar conservation projection contract’ı.

P1.12.g.c ile tamamlandı. P1.12.g.d ile fee-aware profile ve breakeven boundary
kararı kapatıldı. P1.12.g.e ile exit priority ve eşzamanlı trigger kararı
kapatıldı. P1.12.g.f ile selected exit-candidate ve kapasite contract’ı,
P1.12.g.g ile candidate identity ve late-fill ayrım contract’ı kapatıldı.
P1.12.g.h ile fee-aware `TAKE_PROFIT` exit-candidate ve exact quantization
boundary kapatıldı. P1.12.h.a ile durable recovery/replay readiness kapatıldı.
P1.12.h.b ile profile-bound recovery capability ve CORE01 admission boundary
kapatıldı. P1.12.h.c ile durable profile recovery snapshot ve stale-profile
quarantine, P1.12.h.d ile immutable profile-source provenance cross-check ve
publish/migration NO-GO gate kapatıldı. Sıradaki tek iş: `P1.13.c` Spot Grid
fee asset/rounding ve matched cycle profit-total equity ayrımının karar ve
salt-okunur projection kapısıdır.

## 2026-09-17 P1.12.g.h Futures DCA fee-aware exit-candidate ve quantization boundary

P1.12.g.d’nin explicit fee/funding profilinden çıkan fee-aware breakeven exact
`TAKE_PROFIT` adayına bağlanıyor. Profil eksikliği, settlement asset mismatch,
off-grid hedef ve açık pozisyon kapasitesi aşımı fail-closed kalıyor. Sessiz
rounding yapılmıyor; STOP/Trailing trigger’larına breakeven fiyatı bağlanmıyor.
Sonuç salt-okunur ve `order_authority=NONE`.

Odak `9/9 PASS`; tam proje `690` testte `688 PASS`, faz dışı Windows
Credential Manager `Windows error 1312` nedeniyle `2` environment error.
Bağımsız Fraction capacity oracle, compile, AST/write-surface ve
`git diff --check` PASS. Gerçek order/fill, OCO/cancel-replace, reserve
mutation, persistence ve Binance/Testnet mutation yok. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
`evidence/P1.12.g.h/SONUC.md`.

P1.12.h.a ile mevcut greenfield journal’ın durable recovery/replay readiness
sınırı kapatıldı. P1.12.h.b ile profile-bound recovery capability ve CORE01
admission boundary, P1.12.h.c ile durable profile recovery snapshot ve
stale-profile quarantine, P1.12.h.d ile immutable profile-source provenance
cross-check kapatıldı. Sıradaki tek iş: `P1.13.c` Spot Grid fee
asset/rounding ve matched cycle profit-total equity ayrımının karar kapısıdır.

## 2026-09-17 P1.12.h.a Futures DCA durable recovery/replay readiness gate

Mevcut greenfield journal v4; profile revision, journal event, reservation,
release transition, economic posting ve CORE01 replay receipt sahiplerini ayrı
tutuyor. Restart replay sequence, canonical payload/checksum ve link ilişkilerini
doğruluyor. Receipt preflight eksik schema/unique constraint’i yazmadan
`BLOCKED` döndürüyor; event + release + posting + receipt failure injection
sonrasında kısmi state bırakmıyor. Exact duplicate idempotent, farklı payload ve
scope conflict olarak fail-closed kalıyor.

Odak readiness alt kümesi `39/39 PASS`; tam proje `690` testte `688 PASS`, faz
dışı Windows Credential Manager `Windows error 1312` nedeniyle `2` environment
error. Compile, independent restart oracle ve `git diff --check` PASS. CORE01
economic admission, order/fill mutation, Binance/Testnet mutation ve mainnet
yok. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
`evidence/P1.12.h.a/SONUC.md`.

P1.12.h.b ile tamamlandı. P1.12.h.c ile durable profile recovery snapshot ve
stale-profile quarantine, P1.12.h.d ile immutable profile-source provenance
cross-check ve publish/migration NO-GO gate kapatıldı. Sıradaki tek iş:
`P1.13.c` Spot Grid fee asset/rounding ve matched cycle profit-total equity
ayrımının karar kapısıdır.

## 2026-09-17 P1.12.h.b Futures DCA profile-bound recovery capability ve CORE01 boundary

Tek bir profile revision için durable profile, accepted event, economic posting,
release transition ve CORE01 replay receipt kapsamı birebir doğrulanıyor. Eksik
receipt/release, bozuk journal ve cross-profile transition fail-closed `BLOCKED`
kalıyor. Capability salt-okunur loader/preflight kullanıyor; migration, repair,
CORE01 economic admission veya venue mutation yapmıyor.

Odak `4/4 PASS`; h.a ile ilişkili odak `43/43 PASS`; tam proje `694` testte
`692 PASS`, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle
`2` environment error. Compile, read-only byte-oracle ve `git diff --check`
PASS. CORE01 economic admission hâlâ `BLOCKED`, `order_authority=NONE`.
Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
`evidence/P1.12.h.b/SONUC.md`.

P1.12.h.c ile durable profile recovery snapshot ve stale-profile quarantine,
P1.12.h.d ile immutable profile-source provenance cross-check ve
publish/migration NO-GO gate kapatıldı. Sıradaki tek iş: `P1.13.c` Spot Grid
fee asset/rounding ve matched cycle profit-total equity ayrımının karar kapısıdır.

## 2026-09-17 P1.12.h.c Futures DCA durable profile recovery snapshot ve stale quarantine

Seçilen profile ait accepted event, posting, release ve replay receipt
kimlikleri deterministic salt-okunur snapshot olarak projekte edilir. Active
profile revision farklıysa eski seçim `QUARANTINED` olur ve lineage projekte
edilmez; active profile bilinmiyorsa veya journal bozuksa `BLOCKED` kalır.
Snapshot CORE01 state, order/fill authority veya ekonomik uygulama taşımaz.

Odak `4/4 PASS`; h.a ve h.b ile ilişkili odak `47/47 PASS`; tam proje `698`
testte `696 PASS`, faz dışı Windows Credential Manager `Windows error 1312`
nedeniyle `2` environment error. Compile, read-only source-surface,
byte-oracle ve `git diff --check` PASS. CORE01 economic admission hâlâ
`BLOCKED`, `order_authority=NONE`. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
`evidence/P1.12.h.c/SONUC.md`.

P1.12.h.d ile recovery snapshot ile immutable profile-source provenance
cross-check ve publish/migration NO-GO gate kapatıldı. Sıradaki tek iş:
`P1.13.c` Spot Grid fee asset/rounding ve matched cycle profit-total equity
ayrımının karar kapısıdır.

## 2026-09-17 P1.12.h.d Futures DCA recovery snapshot provenance ve publish/migration gate

Recovery snapshot ile immutable profile-source provenance target’ı ve canonical
migration manifest salt-okunur karşılaştırılıyor. Recovery/provenance profile
revision eşleşmesi, tekil `ACCEPTED` source snapshot, manifest hash ve reopened
target oracle’ı birlikte doğrulanıyor. Stale snapshot, profile mismatch,
eksik/bozuk provenance veya önceki gate/oracle başarısızlığı `NO_GO`; temiz
fixture sonucu yalnız `READY_FOR_REVIEW`, `publish_action=BLOCKED` ve
`migration_action=BLOCKED` üretiyor.

Odak `4/4 PASS`; h.a–h.d ilişkili odak `51/51 PASS`; provenance/manifest/
reopen oracle kümesi `18/18 PASS`; tam proje `702` testte `700 PASS`, faz dışı
Windows Credential Manager `Windows error 1312` nedeniyle `2` environment
error. Compile, read-only source-surface ve `git diff --check` PASS. Gerçek
source export, migration/publish, CORE01 economic admission, order/fill
mutation ve Binance/Testnet mutation yok. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
`evidence/P1.12.h.d/SONUC.md`.

Sıradaki tek iş: `P1.13.c` Spot Grid fee asset/rounding ve matched cycle
profit-total equity ayrımının karar ve salt-okunur projection kapısıdır.

## 2026-09-17 P1.12.g.d Futures DCA fee-aware breakeven contract

Fee/funding profili olmadan yalnız gross average-entry boundary gösteriliyor;
üçüncü fee asset’i, settlement mismatch ve tick dışı fee-aware hedef fail-closed
kalıyor. Explicit settlement-notional modelinde LONG/SHORT ve signed funding
exact hesaplanıyor. Odak `9/9 PASS`; tam proje `656` testte `654 PASS`, faz dışı
Windows Credential Manager `Windows error 1312` nedeniyle `2` environment error.
Bağımsız Fraction oracle, compile, AST/write-surface ve `git diff --check` PASS.
`order_authority=NONE`; fee conversion/rounding, funding source/schedule,
TP/SL/trailing execution, OCO/cancel-replace, persistence ve Binance/Testnet
mutation yok. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
evidence/P1.12.g.d/SONUC.md.

P1.12.g.f ile tamamlandı. Sıradaki tek iş: `P1.12.g.g` candidate identity ve
late-fill/conditional execution ayrım contract’ıdır.

## 2026-09-17 P1.12.g.e Futures DCA exit priority contract

Aynı gözlemdeki trigger’lar `STOP_LOSS > TRAILING_STOP > TAKE_PROFIT >
BREAKEVEN_ADJUSTMENT` sırasıyla deterministik seçiliyor. Breakeven tek başına
stop adjustment, diğerleri close kararıdır; kapanış trigger’ı varsa breakeven
bastırılır. Input sırası sonucu değiştirmiyor, duplicate trigger fail-closed.
Odak `9/9 PASS`; tam proje `665` testte `663 PASS`, faz dışı Windows Credential
Manager `Windows error 1312` nedeniyle `2` environment error. Bağımsız alt-küme
oracle, compile, AST/write-surface ve `git diff --check` PASS.
`order_authority=NONE`; exit candidate/order/fill/OCO/cancel-replace/reserve,
persistence ve Binance/Testnet mutation yok. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
evidence/P1.12.g.e/SONUC.md.

P1.12.g.f ile seçilmiş trigger exact exit-candidate ve açık pozisyon kapasitesi
contract’ına bağlandı. Sıradaki tek iş: `P1.12.g.g` candidate identity ve
late-fill/conditional execution ayrım contract’ıdır.

## 2026-09-17 P1.12.g.f Futures DCA exit-candidate ve kapasite contract’ı

P1.12.g.e’nin seçtiği `CLOSE` trigger’ı, ilgili trigger projection’ından
sağlanan exact tick-grid fiyatı ve requested quantity ile gözlenmiş açık
pozisyon kapasitesine bağlanıyor. `TAKE_PROFIT`, `STOP_LOSS` ve
`TRAILING_STOP` adayları kabul ediliyor; `BREAKEVEN_ADJUSTMENT` veya trigger
yokluğu close adayı üretmiyor. Accepted exit fill’leri, mevcut committed exit
miktarları ve yeni aday birlikte exact conservation ile doğrulanıyor; over-close
ve off-grid değerler fail-closed kalıyor.

Odak `9/9 PASS`; tam proje `674` testte `672 PASS`, faz dışı Windows Credential
Manager `Windows error 1312` nedeniyle `2` environment error. Bağımsız Fraction
capacity oracle, compile, AST/write-surface ve `git diff --check` PASS.
`order_authority=NONE`; gerçek order/fill, OCO/cancel-replace, reserve mutation,
persistence ve Binance/Testnet mutation yok. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
`evidence/P1.12.g.f/SONUC.md`.

Sıradaki tek iş: `P1.12.g.g` candidate identity ve late-fill/conditional
execution ayrım contract’ıdır.

## 2026-09-17 P1.12.g.g Futures DCA candidate identity ve late-fill ayrım contract’ı

P1.12.g.f exit candidate’ından deterministic SHA-256 snapshot identity
üretiliyor. Identity; seçilmiş trigger, trigger fiyatı, requested quantity,
kalan kapasite, açık pozisyon miktarı ve candidate gözlem zamanını kapsıyor.
Late fill yalnız aynı candidate identity’ye bağlı, candidate snapshot’tan önce
olmayan ve requested miktarı aşmayan salt-okunur observation olarak tutuluyor.
Bu observation execution order identity veya economic posting üretmiyor ve
mevcut genel conditional execution sözleşmesi kopyalanmıyor.

Odak `7/7 PASS`; tam proje `681` testte `679 PASS`, faz dışı Windows Credential
Manager `Windows error 1312` nedeniyle `2` environment error. Bağımsız
identity/tamper oracle, compile, AST/write-surface ve `git diff --check` PASS.
`order_authority=NONE`; conditional execution, order/fill mutation,
persistence ve Binance/Testnet mutation yok. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
`evidence/P1.12.g.g/SONUC.md`.

P1.12.g.h ile tamamlandı. P1.12.h.a ile durable recovery/replay readiness,
P1.12.h.b ile profile-bound recovery capability, P1.12.h.c ile durable
profile recovery snapshot/stale-profile quarantine ve P1.12.h.d ile immutable
profile-source provenance cross-check kapatıldı. Sıradaki tek iş: `P1.13.c`
Spot Grid fee asset/rounding ve matched cycle profit-total equity ayrımının
karar kapısıdır.

## 2026-09-17 P1.12.g.b Futures DCA max-DCA/stop/EXHAUSTED contract

Tüketilmemiş ladder için `CONTINUE`, ladder seviyeleri kalırken max-DCA
sınırında `STOP`, dış stop nedenleri için ayrı `STOP` ve full ladder için
`EXHAUSTED` kararı salt-okunur değerlendiriliyor. `EXHAUSTED` yeni order veya
recovery talebi üretmiyor. Odak `19/19 PASS`; tam proje `640` testte `638 PASS`,
faz dışı Windows Credential Manager `Windows error 1312` nedeniyle `2`
environment error. Compile, AST/write-surface, bağımsız contract oracle ve
`git diff --check` PASS.
`order_authority=NONE`; lifecycle/order/fill/reserve/persistence ve
Binance/Testnet mutation yok. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.
Kanıt: evidence/P1.12.g.b/SONUC.md.

Sıradaki tek iş: `P1.12.g.c` average-entry TP ve split-TP miktar conservation
projection contract’ı.

## 2026-09-17 P1.12.g.c Futures DCA average-entry TP/split-TP projection

Observed fill projection average-entry’sinden LONG/SHORT yönüne göre exact TP
target hesaplanıyor; hedef tick grid dışında kalırsa sessiz quantization yapılmadan
fail-closed reddediliyor. Split TP miktarları açık pozisyonu aşamıyor, kalan miktar
exact dönüyor. Odak `18/18 PASS`; tam proje `647` testte `645 PASS`, faz dışı
Windows Credential Manager `Windows error 1312` nedeniyle `2` environment error.
Compile, AST/write-surface, bağımsız exact oracle ve `git diff --check` PASS.
`order_authority=NONE`; TP order/OCO/cancel-replace, fill, reserve, persistence ve
Binance/Testnet mutation yok. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.
Kanıt: evidence/P1.12.g.c/SONUC.md.

P1.12.g.d ile tamamlandı. P1.12.g.e ile exit priority kararı kapatıldı;
sıradaki tek iş `P1.12.g.f` seçilmiş trigger’ı exact exit-candidate ve kapasite
contract’ına bağlamaktır.

## 2026-09-17 P1.12.f.i.d custom candidate offline sizing/pre-acceptance köprüsü

Quote-notional custom candidate acceptance mevcut offline sizing/pre-acceptance
kapısına salt-okunur bağlandı. İlk quantized seviye `SizingCandidate`, kalan
seviyeler `LadderBinding` olarak değerlendirilir; acceptance identity ve eligible
quote budget yeniden doğrulanır. BASE_QTY için örtük quote bütçesi üretilmez ve
fail-closed reddedilir. Odak 23/23, ilişkili sizing dahil 27/27 PASS; tam proje
626/628 PASS, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle
iki environment error. Compile, write-surface ve `git diff --check` PASS.
Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
evidence/P1.12.f.i.d/SONUC.md.

Sıradaki tek iş: P1.12.g DCA start/stop/TP/trailing/breakeven lifecycle
sözleşmesidir.

## 2026-09-17 P1.12.f.i.c immutable custom candidate acceptance-boundary

Custom candidate projection yeniden doğrulanıp Futures DCA profili, instrument filter
metadata’sı, ladder seviyeleri ve post-quantization conservation alanlarını kapsayan
deterministik SHA-256 identity ile immutable acceptance snapshot’a bağlandı. Tamper ve
conflict fail-closed; `order_authority=NONE`. Odak 20/20, ilişkili 55/55, tam proje
625/625 PASS, compile/workspace ve `git diff --check` PASS (240 aktif Python dosyası).
Durum `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`. Kanıt:
evidence/P1.12.f.i.c/SONUC.md.

P1.12.f.i.d ile tamamlandı. Sıradaki tek iş: P1.12.g DCA
start/stop/TP/trailing/breakeven lifecycle sözleşmesidir.

## 2026-09-17 P1.12.f.i.b bağımsız candidate/oracle incelemesi ve kritik gate

P1.12.f.i.a BASE_QTY ve QUOTE_NOTIONAL candidate quantization sonuçları bağımsız
Decimal oracle ile doğrulandı. AST/write-surface kontrolünde persistence/SQLite/
HTTP mutation çağrısı bulunmadı. Odak 17/17, ilişkili 52/52, tam proje 622/622
PASS, compile/workspace ve `git diff --check` PASS (239 aktif Python dosyası).
Durum `IMPLEMENTED_WITH_LIMITATION / INDEPENDENT_REVIEW_PASS`. Kanıt:
evidence/P1.12.f.i.b/SONUC.md.

P1.12.f.i.c immutable custom candidate acceptance-boundary sözleşmesi ve
P1.12.f.i.d offline sizing/pre-acceptance köprüsü ile tamamlandı. Sıradaki tek
iş: P1.12.g DCA start/stop/TP/trailing/breakeven lifecycle sözleşmesidir.

## 2026-09-17 P1.12.f.i Pionex DIY per-safety-order deviation/allocation profile

Custom Futures DCA ladder her safety order için anchor’a göre cumulative
deviation, strict index/order ve explicit `BASE_QTY` veya `QUOTE_NOTIONAL`
allocation taşıyor; tick hizası ve exact budget conservation doğrulanıyor.
Bağımsız Decimal oracle dahil odak 5/5, ilişkili 43/43, tam proje 616/616
PASS, compile/workspace PASS (239 aktif Python dosyası). `SHARE` semantiği,
quantity-step/venue quantization, min-notional, persistence ve canlı mutation
açılmadı. Durum `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`. Kanıt:
evidence/P1.12.f.i/SONUC.md.

P1.12.f.i.a ile tamamlanan quantity-step ve quote/base candidate sözleşmesi,
allocation’ı mevcut instrument filter profiline bağlar; post-quantization actual
allocation, quantity-step, min-quantity ve min-notional doğrulanır. Odak 14/14,
ilişkili 49/49, tam proje 619/619 PASS, compile/workspace PASS (239 aktif Python
dosyası). Durum `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`. Kanıt:
evidence/P1.12.f.i.a/SONUC.md.

P1.12.f.i.b bağımsız candidate/oracle incelemesi ve kritik gate ile tamamlandı.
Sıradaki tek iş: P1.12.f.i.c immutable custom candidate acceptance-boundary
sözleşmesi.

## 2026-09-17 P1.12.f.h.av bağımsız replay integrity incelemesi ve kritik gate

P1.12.f.h.au read-only restart oracle bağımsız AST/write-surface kontrolünden
geçti; SQLite write/append çağrısı yok ve schema corruption fail-closed
`BLOCKED` oluyor. Odak 15/15, tam proje 611/611 PASS, compile/workspace PASS
(238 aktif Python dosyası), `git diff --check` hata vermedi. CORE01 durable
owner, Binance/venue mutation, mainnet, secret, migration ve publish yok.
Durum `IMPLEMENTED_WITH_LIMITATION / INDEPENDENT_REVIEW_PASS`. Kanıt:
evidence/P1.12.f.h.av/SONUC.md.

Sıradaki tek iş: P1.12.f.i Pionex DIY per-safety-order deviation/allocation
profilinin exact sözleşmesi ve bağımsız oracle kapısıydı; h.i ile tamamlandı.

## 2026-09-17 P1.12.f.h.au durable replay integrity oracle

Read-only restart oracle durable event, economic posting, release history ve
reservation projection checksum/consistency kontrollerini kullanıyor; bozuk
durable veri fail-closed `BLOCKED` kalıyor. Pure duplicate boundary, retry
duplicate/conflict boundary ve aynı scope farklı receipt fingerprint conflict’i
kanıtlandı. Durable write, Binance/venue mutation, mainnet, secret, migration
ve publish açılmadı. Odak 15/15, ilişkili 55/55, tam proje 611/611 PASS,
compile/workspace PASS (238 aktif Python dosyası). Durum
IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY. Kanıt:
evidence/P1.12.f.h.au/SONUC.md.

Sıradaki tek iş: P1.12.f.h.av read-only replay integrity oracle için bağımsız
inceleme ve kritik gate değerlendirmesiydi; h.av ile tamamlandı.

## 2026-09-17 P1.12.f.h.at read-only CORE01 replay projection oracle

Restart oracle durable accepted event, economic posting, release transition ve
receipt satırlarını read-only loader’larla doğruluyor; aynı immutable girdilerle
pure CORE01 replay decision/projection yeniden hesaplanıyor. Receipt
fingerprint/scope ile pure decision eşleşirse READY, receipt eksikliği veya
stale CORE01 admission BLOCKED. CORE01 durable owner, venue mutation, Binance ve
canlı emir yok. Odak 12/12, ilişkili küme 52/52 PASS, tam proje 608/608 PASS,
compile/workspace PASS (238 aktif Python dosyası). Durum
IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY. Kanıt:
evidence/P1.12.f.h.at/SONUC.md.

Sıradaki tek iş: P1.12.f.h.au durable reservation/posting/release checksum ve
duplicate/conflict sınırlarını genişleten read-only oracle kapısıydı; h.au ile
tamamlandı.

## 2026-09-17 P1.12.f.h.as atomic CORE01 replay receipt binding

Accepted Futures DCA fill event’i, release transition, economic posting ve
CORE01 replay receipt tek SQLite transaction’ında bağlandı. Dört kayıt birlikte
ACCEPTED veya DUPLICATE; receipt scope mismatch ve injected receipt failure
event/release/reservation/posting kayıtlarının tümünü rollback ediyor. Restart
load exact receipt bağlantılarını koruyor. Binance/Testnet mutation, mainnet,
secret, legacy migration/publish ve yeni economic authority yok. Odak 25/25,
ilişkili küme 49/49 PASS, tam proje 605/605 PASS, compile/workspace PASS
(236 aktif Python dosyası). Durum IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY.
Kanıt: evidence/P1.12.f.h.as/SONUC.md.

Sıradaki tek iş: P1.12.f.h.at atomik receipt binding’in read-only CORE01
replay projection oracle’ıyla restart sonrası eşitliğini kanıtlamak.

## 2026-09-17 P1.12.f.h.ar durable CORE01 replay receipt append/load

Greenfield journal schema revision 4 içine core_replay_receipts owner tablosu,
fingerprint primary key ve tam mapping/event/posting/transition/release scope
unique contract’ı eklendi. Accepted event, posting, release transition ve
reservation son projection linkleri append/load sırasında doğrulanıyor; exact
duplicate DUPLICATE, scope/fingerprint çakışması CONFLICT; restart replay
exact receipt döndürüyor. Eski schema migration’ı, venue ve canlı mutation yok.
Receipt append bu fazda mevcut ekonomik kayıtların ardından ayrı transaction’dır.
Odak 16/16, ilişkili küme 46/46 PASS, tam proje 602/602 PASS,
compile/workspace PASS (235 aktif Python dosyası). Durum
IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY. Kanıt:
evidence/P1.12.f.h.ar/SONUC.md.

Sıradaki tek iş: P1.12.f.h.as receipt + event/release/posting bağını tek
transaction’da kuran atomik append/restart ve rollback kapısı.

## 2026-09-17 P1.12.f.h.aq durable CORE01 replay receipt Store preflight

Mevcut greenfield Futures DCA journal read-only incelendi. `core_replay_receipts`
owner tablosu, fingerprint identity ve mapping/event/posting/release unique
scope contract’ı zorunlu; mevcut schema’da tablo olmadığı için preflight
`BLOCKED`. Fixture READY, malformed/eksik constraint RED; migration, receipt
yazımı, restart Store activation ve economic binding yok. Odak `3/3`, ilişkili
küme `43/43 PASS`, tam proje `599/599 PASS`, compile/workspace PASS (`235`
aktif Python dosyası). Durum `IMPLEMENTED_WITH_LIMITATION / NO_GO_CONFIRMED`.
Kanıt: `evidence/P1.12.f.h.aq/SONUC.md`.

Sıradaki tek iş: `P1.12.f.h.ar` greenfield schema revision/migration ve exact
append/load contract’ı.

## 2026-09-17 P1.12.f.h.ap offline replay idempotency contract

Accepted CORE01 + Futures DCA replay kararından event/posting/release/mapping
alanlarıyla bounded canonical fingerprint ve frozen in-memory receipt üretildi.
Aynı scope/fingerprint `DUPLICATE`, same-scope payload/fee/commitment/transition
farkı `CONFLICT`, farklı scope `BLOCKED`; economics yeniden uygulanmıyor.
Durable Store, journal, restart authority ve venue mutation yok. Odak `17/17`,
ilişkili küme `68/68 PASS`, tam proje `596/596 PASS`, compile/workspace PASS
(`233` aktif Python dosyası). Durum `IMPLEMENTED_WITH_LIMITATION /
CONTRACT_READY`. Kanıt: `evidence/P1.12.f.h.ap/SONUC.md`.

Sıradaki tek iş: `P1.12.f.h.aq` receipt’in bounded durable Store/restart
sözleşmesi için karar kapısı.

## 2026-09-17 P1.12.f.h.ao offline CORE01 + Futures DCA replay decision

h.an CORE01 reducer projection’ı accepted Futures DCA event, projected posting
ve partial/full release transition ile tek salt-okunur replay kararında
birleşiyor. Event/transition/posting identity, FILL türü, commitment, fee ve
release consumed-delta exact doğrulanıyor; DUPLICATE yeniden CORE01 economics
üretmiyor. Kabul sonucu CORE state/reservation projection ve posting kimliğini
taşıyor; Store/journal/posting/venue mutation yok. Odak `14/14`, ilişkili küme
`65/65 PASS`, tam proje `593/593 PASS`, compile/workspace PASS (`233` aktif
Python dosyası). Durum `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`. Kanıt:
`evidence/P1.12.f.h.ao/SONUC.md`.

Sıradaki tek iş: `P1.12.f.h.ap` bounded idempotency/replay sözleşmesini durable
Store’a yazmadan doğrulamak.

## 2026-09-17 P1.12.f.h.an offline CORE01 FILL reducer projection

h.am admission’ından gelen immutable CORE01 `FILL` tuple’ı yalnız kopya state
üzerinde reducer’a uygulanıyor. Position quantity, entry notional, fee ve order
filled/notional exact projection olarak doğrulanıyor; BLOCKED veya bozuk tuple
reducer’a girmiyor. Girdi state, durable Store, journal, posting ve venue
transport mutation yok. Odak `12/12`, ilişkili küme `50/50 PASS`, tam proje
`591/591 PASS`, compile/workspace PASS (`233` aktif Python dosyası). Durum
`IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`. Kanıt:
`evidence/P1.12.f.h.an/SONUC.md`.

Sıradaki tek iş: `P1.12.f.h.ao` reducer projection’ını Futures DCA
posting/release replay kararına salt-okunur bağlamak.

## 2026-09-17 P1.12.f.h.am offline CORE01 economic FILL boundary admission

Explicit admitted mapping, accepted Futures DCA fill envelope ve projected
economic posting salt-okunur bir kararda birlikte doğrulanıyor. Identity,
commitment, fee/funding/profile, fee asset, exact `qty * price`, terminal/UNKNOWN
order, overfill ve off-grid kontrolleri fail-closed. Kabul halinde yalnız
immutable CORE01 `FILL` tuple öneriliyor; reducer, Store, persistence, posting
ve venue mutation yok. Odak `10/10`, ilişkili küme `48/48 PASS`, tam proje
`589/589 PASS`, compile/workspace PASS (`233` aktif Python dosyası). Durum
`IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`. Kanıt:
`evidence/P1.12.f.h.am/SONUC.md`.

Sıradaki tek iş: `P1.12.f.h.an` kabul edilmiş CORE01 `FILL` tuple’ını kopya
state üzerinde exact reducer projection olarak doğrulamak.

## 2026-09-17 P1.12.f.h.al CORE01 intent identity authority contract

CORE01 `Order` içine explicit `intent_id` authority’si eklendi. Eski INTENT
payload’ları korunuyor; yeni identity sentetik üretilmiyor ve Spot binding
restart serializer’ında korunuyor. h.ak admission oracle’ı order ID/role/side/
exact limit/intent ID tam eşleşmesinde yalnız salt-okunur `ADMISSIBLE`, eksik
veya conflict durumda `BLOCKED` dönüyor. Economic FILL/posting, Store binding,
venue ve canlı mutation açılmadı. Odak `8/8`, tam proje `587/587 PASS`,
compile/workspace PASS (`233` aktif Python dosyası). Durum
`IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`. Kanıt:
`evidence/P1.12.f.h.al/SONUC.md`.

Sıradaki tek iş: `P1.12.f.h.am` admitted mapping’i Futures DCA fill envelope
ile CORE01 economic FILL boundary’sine offline bağlayan karar kapısı.

## 2026-09-17 P1.12.f.h.ak read-only CORE01 mapping admission oracle

Immutable Futures DCA mapping candidate mevcut CORE01 `State` order scope’u ile
salt-okunur karşılaştırıldı. `core_order_id`, role, side ve exact limit
eşleşmeleri korunuyor; order yokluğu veya scope conflict `BLOCKED`. Scope tam
eşleşse bile mevcut CORE01 `Order` modeli `core_order_intent_id` taşımadığı için
admission güvenli biçimde açılmadı. Odak `7/7`, ilişkili guard kümesi `16/16
PASS`, tam proje `585/585 PASS`, compile/workspace PASS (`233` aktif Python
dosyası). Durum `IMPLEMENTED_WITH_LIMITATION / NO_GO_CONFIRMED`. Kanıt:
`evidence/P1.12.f.h.ak/SONUC.md`.

Sıradaki tek iş: `P1.12.f.h.al` CORE01 intent identity authority’sinin
mutasyonsuz karar ve sözleşme kapısı.

## 2026-09-17 P1.12.f.h.aj immutable Futures DCA → CORE01 mapping contract

Accepted Futures DCA event/posting için profile revision, core order/intent,
role, side ve exact limit alanlarını zorunlu kılan non-economic candidate
contract’ı eklendi. Source/commitment/fee/profile ve BUY/SELL limit eşleşmeleri
fail-closed; CORE01 Store/state mutation yapılmadı. Odak `5/5`, hedefli küme
`28/28 PASS`, tam proje `583/583 PASS`, compile/workspace PASS (`233` aktif
Python dosyası). Durum `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`. Kanıt:
`evidence/P1.12.f.h.aj/SONUC.md`.

Sıradaki tek iş: `P1.12.f.h.ak` mutasyonsuz CORE01 admission oracle’ı.

## 2026-09-17 P1.12.f.h.ai CORE01 economic authority boundary preflight

Durable Futures DCA event/posting replay’si read-only preflight ile doğrulandı.
Mevcut envelope CORE01 `FILL` için gereken `side`, `core_order_intent`, `role`
ve `limit_price` alanlarını taşımadığı için karar `BLOCKED`; CORE01 Store’a
yazma veya sentetik mapping yapılmadı. Odak `3/3`, release+posting kümesi
`23/23 PASS`, tam proje `578/578 PASS`, compile/workspace PASS (`231` aktif
Python dosyası). Durum `IMPLEMENTED_WITH_LIMITATION / NO_GO_CONFIRMED`. Kanıt:
`evidence/P1.12.f.h.ai/SONUC.md`.

Sıradaki tek iş: `P1.12.f.h.aj` immutable Futures DCA → CORE01 mapping contract’ı.

## 2026-09-17 P1.12.f.h.ah durable release + economic-posting atomic binding

Accepted `PARTIAL_FILL`/`FULL_FILL` event’i, release history, reservation
projection ve economic posting aynı bounded SQLite transaction’ında bağlandı.
Event/transition/posting identity, source, commitment, fee ve consumed-delta
uyuşmazlıkları fail-closed; mixed duplicate reddediliyor ve injected posting
failure tüm state’i rollback ediyor. Odak `20/20`, tam proje `575/575 PASS`,
compile/workspace PASS (`229` aktif Python dosyası). Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; cancel, late/UNKNOWN posting’e
çevrilmedi, canlı Binance ve CORE01 canlı binding açılmadı. Kanıt:
`evidence/P1.12.f.h.ah/SONUC.md`.

Sıradaki tek iş: `P1.12.f.h.ai` durable economic posting replay’sinin CORE01
ekonomik authority sınırına güvenli offline binding’i.

## 2026-09-17 P1.12.f.h.ag durable Futures DCA release update

Schema revision `3` içindeki `reservation_releases` history’si ile güncel
reservation projection’ı aynı bounded SQLite transaction’ında durable olarak
bağlandı. Optimistic version, monotonic release cursor, checksum/replay,
duplicate/conflict ve injected failure rollback doğrulandı. Odak `17/17`, tam
proje `572/572 PASS`, compile/workspace PASS (`228` aktif Python dosyası).
Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; release ile economic posting
henüz aynı transaction’a alınmadı. Kanıt: `evidence/P1.12.f.h.ag/SONUC.md`.

Sıradaki tek iş: `P1.12.f.h.ah` release + economic-posting cursor atomic binding.

## 2026-09-17 P1.12.f.h.af Futures DCA release transition state machine

Partial/full fill, cancel, late ve UNKNOWN transition’ları exact conservation,
quarantine, monotonic release cursor, optimistic version ve duplicate/conflict
kurallarıyla saf projection olarak bağlandı. Odak `4/4`, tam proje
`569/569 PASS`, compile/workspace PASS (`226` aktif Python dosyası). Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; durable journal update ayrı bir
sonraki mikro-fazdır. Legacy migration/publish `NOT_APPLICABLE`; canlı Binance
açılmadı. Kanıt: `evidence/P1.12.f.h.af/SONUC.md`.

Sıradaki tek iş: `P1.12.f.h.ag` release transition’ın bounded journal’da
optimistic version + release cursor ile durable atomic update’i.

## 2026-09-17 P1.12.f.h.ae greenfield journal binding

Greenfield Futures DCA journal schema revision 2’ye ayrı `release_cursor`,
canonical economic posting ve event + reservation + posting atomic binding
eklendi. ACCEPTED dışı event, source/commitment/fee mismatch ve cursor gap
fail-closed; duplicate/replay korunuyor. Odak `13/13`, tam proje
`565/565 PASS`, compile/workspace PASS (`224` aktif Python dosyası). Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; legacy migration/publish
`NOT_APPLICABLE`. Kanıt: `evidence/P1.12.f.h.ae/SONUC.md`.

Sıradaki tek iş: partial/cancel/late/UNKNOWN release transition ve
release-cursor state machine kapısı.

## 2026-09-17 P1.12.f.h.ad greenfield ürün teslim sınırı

DCABOT yeni kurulacak ürün olarak ilerler. Kullanıcıdan eski source DB/export,
manuel test çalıştırması veya gerçek işlem kaydı beklenmez. Provenance,
source-to-target ve publish-readiness zinciri yalnız ileride legacy import
gerekirse kullanılacak opsiyonel güvenlik sınırıdır; aktif ürün teslimatını
bloklamaz. Durum `COMPLETE_WITH_LIMITATION / LOCAL_PASS`, legacy
migration/publish `NOT_APPLICABLE`. Kanıt:
`evidence/P1.12.f.h.ad/SONUC.md`.

Eski başarısız DCA projesi ve `YEDEK_ESKI_PROJE` aktif ürünün veri kaynağı veya
zorunlu migration girdisi değildir. Başarılı teknik parçalar ile UI/UX fikirleri
yalnız aktif kodla karşılaştırılıp kalite kapısından geçerse kontrollü yeniden
kullanılır; yedek kendi başına kanıt ya da runtime değildir.

Sıradaki tek iş: greenfield Futures DCA journal’ında event + reservation +
fill-release + economic-posting cursor binding’i.

## 2026-09-17 P1.12.f.h.ac bağımsız inceleme + kapsamlı kabul kapısı

Bağımsız Standards/Spec incelemesinde bulunan iki P1 düzeltildi: önceki
`NO_GO` gate sonucu artık readiness’e taşınıyor; manifest mapping’leri
evaluation sırasında canonical olarak yeniden doğrulanıyor. Odak `14/14 PASS`,
tam proje `562/562 PASS`; legacy migration/publish ürün teslimatı için
`NOT_APPLICABLE`. Kanıt: `evidence/P1.12.f.h.ac/SONUC.md` ve
greenfield karar kaydı `evidence/P1.12.f.h.ad/SONUC.md`.

## 2026-09-17 P1.12.f.h.ab insan kontrollü publish-readiness karar kapısı

Target validation, manifest eşleşmesi ve bağımsız oracle tek kararda birleşiyor.
Teknik kanıtlar geçerse `READY_FOR_REVIEW`; `approval_state=REQUIRED` ve
`publish_action=BLOCKED` her durumda korunuyor. Oracle eksik/başarısız veya
önceki bir kapı NO_GO ise readiness `NO_GO`. Durum
`COMPLETE_WITH_LIMITATION / LOCAL_PASS`, odak `13/13 PASS`, tam proje
`561/561 PASS`; migration/publish açılmadı. Kanıt:
`evidence/P1.12.f.h.ab/SONUC.md`.

## 2026-09-17 P1.12.f.h.aa manifest reopen + bağımsız hash/eşleme oracle kapısı

Bağımsız stdlib oracle production hash yardımcısını kullanmadan reopen edilmiş
target satırını ve canonical manifest SHA-256 değerini doğruladı. Target veya
manifest tahrifi `NO_GO`, target satırı değişmeden kalıyor. Durum
`COMPLETE_WITH_LIMITATION / LOCAL_PASS`, odak `11/11 PASS`, tam proje
`559/559 PASS`; migration/publish açılmadı. Kanıt:
`evidence/P1.12.f.h.aa/SONUC.md`.

## 2026-09-17 P1.12.f.h.z source-to-target eşleme ve immutable migration manifest kapısı

Source/target row identity, profile revision, payload hash, schema revision,
observed time ve state canonical SHA-256 manifest’e bağlandı. Manifest ile
target ACCEPTED provenance satırları read-only birebir karşılaştırılıyor;
deterministic eşleşme `READY`, UNKNOWN/duplicate/conflict/empty/mismatch
`NO_GO`. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, odak `8/8 PASS`,
tam proje `556/556 PASS`; migration ve publish açılmadı. Kanıt:
`evidence/P1.12.f.h.z/SONUC.md`.

## 2026-09-17 P1.12.f.h.y read-only provenance validation + publish karar kapısı

Target üzerinde profile checksum/replay, source snapshot identity/hash/state,
profile FK ve her profile için tekil ACCEPTED provenance doğrulanıyor. Geçerli
target `READY/READY`, UNKNOWN/missing/conflict veya bozuk veri `NO_GO/NO_GO`
döndürüyor. Bu yalnız karar kapısıdır; migration ve otomatik publish açılmadı.
Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, odak `5/5 PASS`, tam proje
`553/553 PASS`. Kanıt: `evidence/P1.12.f.h.y/SONUC.md`.

## 2026-09-17 P1.12.f.h.x bounded provenance target initializer + failure/restart kapısı

Mevcut v1 journal dosyasını yerinde değiştirmeyen yeni bounded target,
`profile_source_snapshots` owner’ı, profile FK, ACCEPTED unique kuralı ve
unpublished owner metadata ile kuruldu. Duplicate/conflict, UNKNOWN replay
dışı bırakma ve injected SQLite failure sonrası rollback/reopen davranışı
`3/3` doğrulandı; tam proje `551/551 PASS`. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, migration ve publish `NO-GO`.
Kanıt: `evidence/P1.12.f.h.x/SONUC.md`.

## 2026-09-17 P1.12.f.h.w provenance target schema/migration taslağı

Mevcut v1 dosyasını yerinde değiştirmeyen ayrı target, immutable
`profile_source_snapshots` owner’ı, FK/unique/hash/state/replay kısıtları ve
read-only → validate → commit sırası taslaklandı. Migration çalıştırılmadı;
durum `CONTRACT_READY / IMPLEMENTATION_PENDING`, migration `NO-GO`. Kanıt:
`evidence/P1.12.f.h.w/SONUC.md`.

## 2026-09-17 P1.12.f.h.v provenance SQLite failure/replay oracle kapısı

Bağımsız stdlib SQLite oracle ACCEPTED replay, duplicate/conflict, UNKNOWN
authority dışı bırakma ve commit öncesi failure rollback invariant’larını `3/3`
doğruladı. Production schema version/migration binding açılmadı; tam proje
`548/548 PASS`. Kanıt: `evidence/P1.12.f.h.v/SONUC.md`.

## 2026-09-17 P1.12.f.h.u immutable provenance schema taslağı

Profile revision’dan ayrı immutable `profile_source_snapshots` owner’ı,
source kind/row identity, payload hash, source schema revision, observed time ve
ACCEPTED/UNKNOWN/QUARANTINED state kısıtları taslaklandı. V1’e uygulanmadı;
schema version/migration binding `NO-GO`. Kanıt:
`evidence/P1.12.f.h.u/SONUC.md`.

## 2026-09-17 P1.12.f.h.t profile source provenance/snapshot identity kararı

Profile provenance için source kind, row/snapshot identity, payload hash,
schema/policy revision, observed time ve profile bağı zorunlu tutuldu. Aynı
identity farklı hash ile conflict; eksik/UNKNOWN source quarantine/NO-GO olur.
V1 profile tablosu provenance taşımadığı için persistence/migration açılmadı;
durum `CONTRACT_READY / IMPLEMENTATION_PENDING`. Kanıt:
`evidence/P1.12.f.h.t/SONUC.md`.

## 2026-09-17 P1.12.f.h.s profile revision + contract-size source adapter

Caller-supplied revision identity, symbol, effective time, exact positive
contract-size ve policy revision’ları immutable journal profile revision’ına
dönüştürülüyor; contract-size default edilmiyor. Venue fetch, provenance,
migration ve ekonomik binding açılmadı. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, odak `2/2 PASS`, tam proje
`545/545 PASS`. Kanıt: `evidence/P1.12.f.h.s/SONUC.md`.

## 2026-09-17 P1.12.f.h.r migration source contract karar kapısı

Migration için her hedef alanda source authority/row identity, exact
normalization, revision/event binding ve missing/UNKNOWN/conflict/late
quarantine şartları zorunlu kabul edildi. Profile, event/execution,
reservation ve posting sahiplikleri ayrıldı; mevcut split store’lar tam kaynak
olmadığı için migration `NO-GO`, implementation `PENDING`. Kanıt:
`evidence/P1.12.f.h.r/SONUC.md`.

## 2026-09-17 P1.12.f.h.q split-store migration kapsam envanteri

Read-only preflight v1 journal’ın profile, event/execution, reservation ve
posting alanlarının tamamını karşılaştıracak şekilde genişletildi. Gerçek split
kaynaklarda yalnız event identity/sequence/hash ve reservation
identity/owner/amount gözleniyor; eksik alanlar default’lanmadı ve migration
`NO-GO` kaldı. Odak `11/11 PASS`, tam proje `543/543 PASS`. Kanıt:
`evidence/P1.12.f.h.q/SONUC.md`.

## 2026-09-17 P1.12.f.h.p event+reservation atomic coordinator kapısı

Profile-bound event ve source-event bağlı reservation aynı bounded SQLite
transaction’ında yazılıp replay ediliyor. Exact duplicate idempotent; conflict,
source mismatch ve injected reservation failure fail-closed. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; release/posting ve mevcut split
`FuturesDcaEventStore` + `ReservationLedger` migration `NO-GO`; odak `10/10
PASS`, tam proje `543/543 PASS`. Kanıt:
`evidence/P1.12.f.h.p/SONUC.md`.

## 2026-09-17 P1.12.f.h.o minimum reservation projection kapısı

Reservation identity, owner/asset, exact reserved-consumed-releasable alanları,
optional release identity, terminal state, version ve source-event reference
alanları bounded journal’a yazılıp replay ediliyor. Duplicate/conflict ve
eksik source event fail-closed; event+reservation atomic coordinator, release
transition, posting ve core binding açılmadı. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, release/atomic binding `NO-GO`;
odak `8/8 PASS`, tam proje `541/541 PASS`. Kanıt:
`evidence/P1.12.f.h.o/SONUC.md`.

## 2026-09-17 P1.12.f.h.n profile-bound event envelope kapısı

V1 journal event envelope’ı immutable profile revision’a bağlandı; identity,
sequence, exact execution alanları, canonical payload/checksum ve
duplicate/conflict replay kuralları doğrulandı. Reservation/posting binding’i
açılmadı. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, reservation/posting
`NO-GO`; tam proje `539/539 PASS`. Kanıt:
`evidence/P1.12.f.h.n/SONUC.md`.

## 2026-09-17 P1.12.f.h.m immutable profile revision kapısı

V1 journal profile revision’ı explicit contract-size ve policy revision
kimlikleriyle canonical hash’li, duplicate idempotent ve conflict fail-closed
biçimde yazıp replay ediyor. Event/reservation/posting binding’i açılmadı.
Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, event binding `NO-GO`; tam
proje `537/537 PASS`. Kanıt: `evidence/P1.12.f.h.m/SONUC.md`.

## 2026-09-17 P1.12.f.h.l minimum v1 schema kapısı

Boş/inert bounded SQLite schema initializer profile revision, event,
reservation ve economic posting tablolarını tanımladı; mevcut dosyayı
değiştirmiyor ve ekonomik satır/binding yazmıyor. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, binding `NO-GO`; tam proje
`535/535 PASS`. Kanıt: `evidence/P1.12.f.h.l/SONUC.md`.

## 2026-09-17 P1.12.f.h.k gerçek kaynak migration preflight kapısı

Read-only preflight mevcut `FuturesDcaEventStore` ve `ReservationLedger`
kaynaklarını inceledi; eksik immutable profile/economic/release/posting alanları
nedeniyle `NO_GO` verdi ve migration hedefi oluşturmadı. Durum
`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; tam proje `533/533 PASS`; kanıt:
`evidence/P1.12.f.h.k/SONUC.md`.

## 2026-09-17 P1.12.f.h.i minimum journal schema/migration sözleşmesi

Spot’tan bağımsız bounded Futures DCA journal hedefi, immutable
profile/event/execution/reservation/posting sahiplikleri ve in-place olmayan
migration sınırı yazıldı. Eksik fee/slippage/rounding veya UNKNOWN-release
otoritesi varsayılmadı. Durum `CONTRACT_READY / IMPLEMENTATION_PENDING`,
production binding `NO-GO`; kanıt: `evidence/P1.12.f.h.i/SONUC.md`.

## 2026-09-17 P1.12.f.h.j migration validator oracle kapısı

Bağımsız draft oracle profile revision, sequence, identity, checksum ve
UNKNOWN/quarantine fail-closed kurallarını `3/3 PASS` ile doğruladı. Bu
production migration değildir; gerçek kaynak tiplerine bağlama ve tam suite
kapısı `532/532 PASS` ile geçildi. Kanıt:
`evidence/P1.12.f.h.j/SONUC.md`.

## 2026-09-17 P1.12.f.h.g tek journal sahiplik kapısı

SpotBindingStore’un tek SQLite transaction kalıbı incelendi; Spot lifecycle ve
CORE01 sahibi olduğu için Futures DCA ekonomik schema’sına doğrudan taşınamaz.
Futures event/reservation store’ları ayrı transaction sınırlarında kaldı.
Durum `DEFERRED / NO-GO / LOCAL_PASS`; production coordinator eklenmedi.
Kanıt: `evidence/P1.12.f.h.g/SONUC.md`.

## 2026-09-17 P1.12.f.h.h tek journal transaction oracle kapısı

Bağımsız stdlib SQLite oracle, event/reservation/posting kayıtlarının tek
transaction içinde ya hep birlikte görünmesi ya da injected failure sonrası
hiç görünmemesi gerektiğini `2/2 PASS` ile doğruladı. Production binding
`IMPLEMENTATION_PENDING`; tam proje `529/529 PASS`; kanıt:
`evidence/P1.12.f.h.h/SONUC.md`.

## 2026-09-17 P1.12.f.h.f release identity kapısı

Partial/cancel/late/UNKNOWN için mevcut Futures DCA event ve reservation
tiplerinde reservation identity, consumed/releasable miktar,
terminal/quarantine state ve release cursor’ı bulunmadığı doğrulandı. Durum
`DEFERRED / NO-GO / LOCAL_PASS`; production binding açılmadı. Kanıt:
`evidence/P1.12.f.h.f/SONUC.md`.

## 2026-09-17 P1.12.f.h.e fee/slippage/rounding karar kapısı

Futures DCA fill’de fee, fee asset, effective execution price, slippage
reference, execution time ve rounding policy bulunmadığı; pending reserve’in
fee/slippage hariç hesaplandığı doğrulandı. Durum `DEFERRED / NO-GO / LOCAL_PASS`;
production binding açılmadı. Kanıt:
`evidence/P1.12.f.h.e/SONUC.md`.

## 2026-09-17 P1.12.f.h.d profile-revision kapsam kapısı

`FuturesDcaProfile` symbol, effective-time ve immutable profile-revision
authority taşımıyor; odak `1/1 PASS`. Durum `DEFERRED / NO-GO / LOCAL_PASS`;
tam proje `527/527 PASS`; production binding açılmadı. Kanıt:
`evidence/P1.12.f.h.d/SONUC.md`.

## 2026-09-17 P1.12.f.h.c multiplier exact oracle kapısı

Bağımsız Decimal oracle, DCA quantity’sinin explicit `pnl_multiplier` ile
effective quantity/notional’a dönüşümünü doğruladı; `0.001` örneği mevcut
`quantity × price` projection’ından ayrıştı. Durum `COMPLETE_WITH_LIMITATION /
LOCAL_PASS`; ekonomik binding `DEFERRED / NO-GO`. Üretim profile/ledger
değişmedi; tam proje `526/526 PASS`. Kanıt:
`evidence/P1.12.f.h.c/SONUC.md`.

## 2026-09-17 P1.12.f.h.b contract-size commitment kapısı

DCA profile/fill katmanında explicit contract-size/multiplier bulunmadığı,
fill notional’ının `quantity × price` varsayımına dayandığı ve ayrı lineer
futures matematiğinin contract-size’ı zorunlu tuttuğu doğrulandı. Sessiz `1`
varsayımı reddedildi; durum `DEFERRED / NO-GO / LOCAL_PASS`. Production kodu
değişmedi, son tam suite `525/525 PASS`. Kanıt:
`evidence/P1.12.f.h.b/SONUC.md`.

## 2026-09-17 P1.12.f.h.a atomicity failure-injection kanıtı

İki ayrı SQLite ledger arasındaki injected failure, event journal’ın commit
olup reservation’ın commit olmadan kalabildiğini `1/1 PASS` ile gösterdi.
Durum `LOCAL_PASS / NO-GO_CONFIRMED`; production coordinator açılmadı. Sonraki
tek iş dört ekonomik sözleşme için bağımsız exact oracle ve tek bounded SQLite
journal failure/restart kabulüdür. Kanıt: `evidence/P1.12.f.h.a/SONUC.md`.

## 2026-09-17 3Commas/Pionex ikinci küçük araştırma yeniden doğrulaması

Yeni ayrıntılı Binance raporu ve pasted karşılaştırma mevcut karar raporuyla
yeniden denetlendi. İlk güvenli profil değişmedi. Nihai kapsamda Pionex DIY
per-safety-order deviation/allocation için `P1.12.f.i`, Binance/Pionex
dynamic order placement ile margin-reserve ayrımı için `P1.13.f–g`, 3Commas
Hedge Grid için P1.15 bağımlılığı görünürleştirildi. Dynamic placement,
dynamic range/trailing/infinity ile aynı davranış sayılmayacak. Pasted
metindeki stale Binance karşılaştırması, kişisel değerler, iç citation’lar,
untyped mimari ve ilk hatalı step formülü reddedildi. Kod ve dependency
değişmedi; son tam suite `524/524 PASS`. Karar raporu:
`docs/P1.12_P1.13_3COMMAS_PIONEX_KARSILASTIRMA_KARAR_RAPORU.md`.

## 2026-09-16 P1.12/P1.13 ürün kuralı araştırması

Kullanıcının ekonomik kural seçimini varsayıma bırakmamak için resmi Binance
USDⓈ-M ve Spot Grid sözleşmeleri yeniden incelendi. İlk uygulanabilir ürün
profili `USDⓈ-M perpetual + USDT single-asset + one-way + isolated` Futures
ve `arithmetic + quote-asset-fee-only` Spot Grid olarak sabitlendi. Futures
UPL/liquidation authority mark price, realized close authority execution
price, funding ise yalnız timestamped venue event olacaktır; ilk offline
demo leverage değeri güvenli varsayılan olarak `1x`'tir ve PnL'yi çarpmaz.

Bu bir ürün profili kararıdır, canlı işlem izni değildir. Cross margin, hedge
mode, multi-assets, ADL, auto-margin, third-asset fee conversion, geometric
rounding, trailing ekonomik cancel/replace ve reverse/infinity grid bu
araştırmayla açılmadı. Liquidation ancak versioned risk-tier/bracket + mark +
margin snapshot birlikte varsa hesaplanacak; eksik veri `NOT_VERIFIED` olur.
Grid `matched cycle profit` ile `total equity`yi ayrı raporlayacak; açık
inventory ve reserved fee cycle kârına yazılmayacaktır. Ayrıntılı kanıt:
`docs/P1.12_P1.13_URUN_KURALLARI_ARASTIRMA_RAPORU.md`.

## 2026-09-16 3Commas/Pionex hedef kapsamı ve P1.12.d ilerlemesi

Kullanıcının sağladığı Binance odaklı rapor, bağımsız 3Commas/Pionex araştırması
ve pasted metin mevcut checkout’a karşı karşılaştırıldı. 3Commas DCA safety
order/volume-deviation multiplier, averaging, signal, multiple TP/trailing/
breakeven; Pionex Futures Grid long/short/neutral, margin/funding/liquidation
ve grid-profit/total-P&L ayrımı nihai hedef kapsamına alındı. Pionex Futures DCA
exact alanları, dynamic grid algoritması, replacement/replay ve Reverse/Infinity
semantics kaynak sınırı nedeniyle `NOT_VERIFIED/DEFERRED` kaldı. Pasted metindeki
stale Binance karşılaştırması, kişisel/proje değerleri, sahte citation, untyped
EventBus/GridNode/JSON mimarisi ve ilk hatalı step formülü kabul edilmedi.
Karar raporu: `docs/P1.12_P1.13_3COMMAS_PIONEX_KARSILASTIRMA_KARAR_RAPORU.md`;
bağımsız araştırma: `docs/P1.12_P1.13_3COMMAS_PIONEX_ARASTIRMA_RAPORU.md`.

P1.12.d’nin ilk dikey dilimi tamamlandı: ayrı linear ledger SQLite projection’ı
yalnız fee/funding event’lerini checksum’li ve idempotent biçimde replay eder;
CORE01, order, position, venue veya live mutation authority taşımaz. Odak
`4/4`, tam proje suite `499/499 PASS`, compile/workspace kontrolleri PASS.
Kanıt: `evidence/P1.12.d/SONUC.md`.

P1.12.e’nin ilk dikey dilimi tamamlandı: fixed-tier isolated liquidation
estimate yalnız geçerli risk tier, isolated margin ve timestamped mark snapshot
ile long/short analitik kök üretir. Tier dışı kök, eski snapshot ve exact
decimal’e sığmayan sonuç fail-closed kalır. Odak `3/3`, tam proje suite
`502/502 PASS`, compile/workspace kontrolleri PASS. Sonuç gerçek venue
liquidation değildir; cross/hedge, partial liquidation, bankruptcy, ADL ve
CORE01 binding açılmadı. Kanıt: `evidence/P1.12.e/SONUC.md`.

P1.12.f.a tamamlandı: offline Futures DCA planı long/short yönü, finite safety
ladder, kümülatif deviation multiplier, volume multiplier, BASE/QUOTE sizing,
quantity-step quantization, required capital ve covered deviation projection’ı
üretir. Plan yalnız candidate/projection’dır; order, fill, position, exit veya
live venue authority taşımaz. Odak `3/3`, tam proje suite `505/505 PASS`.
P1.12.f.b bağımsız Decimal oracle kapısı da tamamlandı: odak `2/2`, tam proje
suite `507/507 PASS`, compile/workspace PASS. Oracle projection’ı tekrar
uygulamadan long/short deviation, volume, sizing ve quantization sonuçlarını
doğrular. Lifecycle, exit ve durable DCA state daha sonra gelir. P1.12.f.c de
tamamlandı: gözlemlenmiş base/safety fill’lerinden exact
average-entry ve `max_active_safety_orders` ile sınırlı pending projection
üretir; base-before-safety, sıra atlama, duplicate/conflict ve non-terminating
average fail-closed’tur. Odak `4/4`, bağımsız oracle `2/2`, tam suite
`513/513 PASS`, compile/workspace PASS. P1.12.f.d event identity/sequence alt
fazı da tamamlandı: local event scope,
ardışık sequence, exact duplicate ve execution identity conflict kontrolleri
`4/4` odak ve `517/517 PASS` tam suite ile doğrulandı. Bu local sequence
Binance transport sequence’i değildir. Sıradaki tek alt faz shared-account
reservation binding karar kapısıdır. P1.12.f.e de tamamlandı: pending quote
`AccountReservation` projection’ına exact bağlandı; USDT settlement, ONE_WAY
mode, capacity ve optimistic version sınırları `3/3` odak ve `520/520 PASS`
tam suite ile doğrulandı. Bu candidate projection’dır; persistence/commit ve
fill-release atomicity’si yoktur. Sıradaki tek alt faz reservation persistence
ve event journal/replay binding karar kapısıdır. P1.12.f.f de tamamlandı:
Futures DCA event contract ayrı bounded SQLite journal/replay store’a bağlandı;
checksum, scope, local sequence ve duplicate/conflict restart sonrası `4/4`
odak ve `524/524 PASS` tam suite ile doğrulandı. Bu local sequence Binance
transport sequence’i değildir ve reservation/fill-release/economic posting
atomicity’si yoktur. Sıradaki tek alt faz reservation + fill-release atomicity
karar kapısıdır. P1.12.f.g kararı tamamlandı: iki ayrı SQLite transaction
sınırı nedeniyle atomic binding güvenli biçimde kurulamadı ve
`DEFERRED / NO-GO / LOCAL_PASS` olarak bırakıldı. Reservation `5/5`, event
store `4/4`, son tam suite `524/524 PASS`; kod/adapter değişmedi. Yeniden
açılma için tek transaction veya crash-safe outbox/recovery, commitment
dönüşümü, release identity ve partial/late/UNKNOWN/conflict sözleşmeleri
gerekiyor.
P1.12.f.h atomic binding yeniden açılma sözleşmesi hazırlandı: hedef tek
bounded SQLite journal ve aynı transaction invariant’larıdır; commitment,
fee/slippage/rounding ve release authority çözülmeden implementation açılmaz.
Durum `CONTRACT_READY / IMPLEMENTATION_PENDING`; son tam suite `524/524 PASS`.
Kanıtlar: `evidence/P1.12.f.a/SONUC.md`, `evidence/P1.12.f.b/SONUC.md`,
`evidence/P1.12.f.c/SONUC.md`, `evidence/P1.12.f.d/SONUC.md` ve
`evidence/P1.12.f.e/SONUC.md`, `evidence/P1.12.f.f/SONUC.md`,
`evidence/P1.12.f.g/SONUC.md` ve `evidence/P1.12.f.h/SONUC.md`.

## 2026-09-16 P2.04 canlı read-only kapısı

Mevcut `testnet-readonly` credential ile yalnız signed `GET /api/v3/account`
çağrısı tekrar geçti: `SPOT`, `permissions=('SPOT',)`,
`capability_source=SIGNED_ACCOUNT_CONTEXT` ve `balances_count=502`. Secret ve
bakiye tutarları hiçbir çıktıya veya kalıcı kanıta alınmadı. Bu sonuç yalnız
hesap endpoint erişimini doğrular; User Data Stream, reconciliation, emir veya
trading activation kanıtı değildir.

Read-only User Data Stream aboneliği gerçek Testnet üzerinde doğrulandı; ancak
reconnect worker, signed order-query ve canlı reconciliation adapterı kapsamı
henüz tamamlanmadı. Karar:
`P2.04_READ_ONLY_ACCOUNT = LIVE_READ_ONLY_PASS`,
`P2.04_USER_DATA_STREAM = LIVE_READ_ONLY_PASS_WITH_LIMITATION`,
`P2.04_LIVE_RECONCILIATION = DEFERRED / NO-GO`. Yeni WebSocket bağımlılığı,
adapter ve bounded `executionReport` identity çözümlemesi eklendi; ekonomik
state veya mutation eklenmedi. Yeniden açılma için gerçek event tüketimi,
reconnect/catch-up, resmi payload/sequence oracle’ı ve kapsamlı test kapısı
gerekir. Kanıt: `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

### 2026-09-16 P2.04 fail-closed hardening

Geçersiz, desteklenmeyen veya timeout/transport hatası veren User Data Stream
frame’inden sonra socket kapatılıp abonelik durumu temizleniyor; sonraki okuma
`USER_STREAM_NOT_CONNECTED` ile reddediliyor. Odak `6/6 PASS`, standart ve
optimize suite `493/493 PASS`, compileall/workspace `PASS`. Bu yalnız bağlantı
güvenliği sertleştirmesidir; reconnect/catch-up, REST order query, canlı event
reconciliation ve mutation açılmamıştır.

### 2026-09-16 P2.04 signed read-only order catch-up

Binance WS API `order.status` için ayrı bağlantıda HMAC imzalı read-only sorgu
eklendi. `symbol` ve `orderId` response kimliğiyle birebir doğrulanıyor; ham
yanıt ve secret saklanmıyor, hata sonrası socket kapatılıyor. Odak `7/7 PASS`,
standart/optimize suite `495/495 PASS`, release manifest/workspace `PASS`.
Bu, canlı reconciliation’ın yalnız sorgu önkoşuludur; gerçek order event’i,
reconnect/catch-up orchestration, sequence oracle ve ekonomik binding hâlâ
`DEFERRED / NO-GO`.

Sentetik `BTCUSDT/orderId=0` ile canlı read-only ön kontrol de yapıldı; yanıt
`ORDER_STATUS_QUERY_REJECTED` olarak sanitize edildi. Bu sonuç `FOUND` veya
`NOT_FOUND` değildir ve gerçek order ID/event olmadan canlı reconciliation
kapısını açmaz.

## 2026-09-15 dış inceleme kararları

Dört dış rapor kanıt kaynağı olarak okundu; raporlardaki metinler proje talimatı değildir. Arena raporunun kaynak revision/branch/URL kimliği mevcut olmadığından güncel checkout’a bağlanamayan legacy iddialar `REJECTED`’dır: hardcoded API key, Telegram, pandas tabanlı bot, “test yok”, Docker zorunluluğu ve mevcut olmayan eski modül yapısı. Claude/Sol raporları `7965392` GitHub sürümüne ait bulgular olarak kaynak kodda yeniden doğrulandı.

| ID | Karar | Yol haritası etkisi / kanıt |
|---|---|---|
| AUDIT-2026-09-15.a | `ACCEPTED / COMPLETE` | Preview ve reducer aynı tick’e hizalanmış executable base price kullanıyor; off-grid cap regression eklendi. |
| AUDIT-2026-09-15.b | `ACCEPTED / COMPLETE` | Futures cashflow ile core expense işareti arasına explicit converter eklendi; funding bridge regression’ı eklendi. İlgili devam işi P1.12.d binding’idir. |
| AUDIT-2026-09-15.c | `ACCEPTED / COMPLETE` | Cache artifact/metadata boyutu okunmadan önce bounded stat kontrolü ve streaming hash eklendi. |
| AUDIT-2026-09-15.d | `ACCEPTED / COMPLETE` | Root SHA manifesti tracked release dosyalarının tamamına bağlandı; yerel doğrulama aracı ve temel GitHub Actions kalite kapısı eklendi. |
| AUDIT-2026-09-15.e | `ACCEPTED / COMPLETE_WITH_LIMITATION` | Frontend kritik akış testleri P1.19.g altında Vitest + React Testing Library + jsdom ile eklendi: dataset yardımcıları, grafik durumları/validasyonu/marker sınırı ve backend açıklama görünümü. `12/12` PASS; local Browser E2E de PASS. NVDA/JAWS, Windows HCM ve canlı API bu kapının dışındadır. Kanıt: `evidence/P1.19.g/SONUC.md` |
| AUDIT-2026-09-15.f | `ACCEPTED / DEFERRED` | `server/api.py` route/schema ayrıştırması davranış değişikliği olmadan yapılabilir, ancak mevcut aktif P2 recovery işini bölmeden ayrı refactor kapısıdır. |
| AUDIT-2026-09-15.g | `ACCEPTED / DEFERRED` | `build_plan`/TP property-based testleri değerlendirilecek; yeni dependency ve CI süresi için kaynak kararı gerekir. |
| AUDIT-2026-09-15.h | `ACCEPTED / P3.01` | Air-gapped wheelhouse, lock hash, SBOM ve image digest release provenance/operasyon işine taşındı; şu an runtime’a eklenmedi. |
| AUDIT-2026-09-15.i | `ACCEPTED / EXISTING LIMITATION` | Historical sonuçların execution backtest olmadığı disclosure’ı korunacak; lower-timeframe/liquidity/latency modeli gerçek venue kanıtı olmadan açılmayacak. |
| AUDIT-2026-09-15.j | `REJECTED / NO-GO` | Live trading’i bu rapor önerileriyle açma, otomatik retry, Telegram/Docker/ML/multi-exchange gibi eski veya doğrulanmamış önerileri P1’e taşıma. |
| AUDIT-2026-09-15.k | `ACCEPTED / EXISTING LIMITATION` | `UNKNOWN` için offline reconciliation/recovery yolu mevcut; canlı venue adapter ve mutation recovery tamamlanmadan runtime’dan çıkış açılmayacak. |
| AUDIT-2026-09-15.l | `ACCEPTED / DEFERRED` | Fee rebate ve maksimum gerçek fee oranı venue policy’sine bağlıdır; policy sahibi kanıtlanmadan core’a keyfi üst sınır eklenmeyecek. |
| AUDIT-2026-09-15.m | `ACCEPTED / DEFERRED` | Ladder quantity rounding sonrası effective multiplier raporlama/invariant’ı ürün kararı gerektirir; mevcut fail-closed quantization korunacak. |
| AUDIT-2026-09-15.n | `ACCEPTED / DEFERRED` | Fraction iç model/string boundary ayrımı mevcut exact sözleşmeyi koruyor; geniş refactor ayrı performans/regression kapısıdır. |
| AUDIT-2026-09-15.o | `ACCEPTED / DEFERRED` | Test edilmiş fakat API’ye bağlı olmayan application contract’ları P2 binding dilimleriyle tek tek bağlanacak; toplu silme veya sahte ürün erişimi yapılmayacak. |
| AUDIT-2026-09-15.p | `ACCEPTED / DEFERRED` | Coverage baseline/threshold ve Ruff + mypy veya pyright kalite kapısı ayrı CI işi olarak eklenecek; mevcut temel CI bunları henüz kanıtlamıyor. |
| AUDIT-2026-09-15.q | `ACCEPTED / DEFERRED` | `FundingExpense`, `FundingCashflow`, `FeeExpense` ve `RebateCashflow` gibi semantic economic event boundary’leri venue binding öncesi tanımlanacak; mevcut explicit funding converter korunacak. |
| AUDIT-2026-09-15.r | `ACCEPTED / COMPLETE_WITH_LIMITATION` | Offline repository security scanında pre-fix validation body buffering (CWE-400, LOW) bulundu; ortak streaming body limiter ve chunked early-cut regression ile düzeltildi. Delegated baseline, NVDA/JAWS ve Windows HCM doğrulaması kapsam dışı; local Browser E2E PASS. |
| AUDIT-2026-09-15.s | `ACCEPTED / COMPLETE_WITH_LIMITATION` | Lisans gerektirmeyen erişilebilirlik doğrulama yolu seçildi: ücretsiz NVDA + Windows yerleşik Narrator + Windows High Contrast Mode. NVDA ve Narrator kullanıcı onayıyla `PASS`; gerçek HCM `Gece gökyüzü` altında `forced-colors: active`, 1390px taşmasız UI ve temiz konsol ile `PASS`, test sonunda `Yok` geri yüklendi. JAWS zorunlu kapıdan çıkarıldı ve yalnız opsiyonel doğrulama. |

## 2026-09-16 güncel checkout karşılaştırması

Claude, Sol ve Buffy raporları mevcut checkout ve testlerle yeniden kontrol edildi. Arena raporunun revision/branch kimliği doğrulanamadığı için yalnız güncel kodla eşleşen iddialar dikkate alındı. Bu karşılaştırma yeni bir ürün fazı açmaz; yalnız kararların bugünkü kanıtını günceller.

| Rapor konusu | Güncel karar | Yeniden doğrulama / yol haritası etkisi |
|---|---|---|
| Arena: eski `main.py`/`dca_bot.py`, Telegram, pandas, “test yok”, Docker zorunluluğu | `REJECTED / STALE` | Güncel checkout bu yapıyı taşımıyor; legacy snapshot’a göre uygulama yapılmadı. |
| Claude/Sol F-01: preview–execution fiyat/cap farkı | `ACCEPTED / COMPLETE` | Aynı executable price authority ve off-grid regression mevcut. |
| Claude/Sol F-02: funding işaret uyumsuzluğu | `ACCEPTED / COMPLETE_WITH_LIMITATION` | Explicit cashflow → expense converter ve regression mevcut; futures binding P1.12.d’de sınırlı. |
| Sol F-03/F-04: release manifesti ve cache body sınırı | `ACCEPTED / COMPLETE` | Root manifest/CI ve bounded stat/streaming hash mevcut; manifest tekrar doğrulandı. |
| Claude A-4: frontend testsiz; reconciliation journal erişilemez/testsiz | `REJECTED / STALE` | P1.19.g `12/12`, Browser E2E ve `tests/test_reconciliation_journal.py` mevcut. |
| Claude L-1 / Buffy HATA-f: `UNKNOWN`/`FAILED` recovery güvensiz | `ACCEPTED / EXISTING LIMITATION` | Offline reconciliation, recovery handoff ve `FAILED` önceliği regression ile korunuyor; canlı venue recovery hâlâ kapalı. |
| Claude L-2: her negatif fee reddedilmeli | `REJECTED / EXISTING CONTRACT` | Güncel core testi negatif fee’yi rebate olarak bilinçli kullanıyor; bu yüzden global red ekonomik sözleşmeyi bozar. Maksimum gerçek fee oranı ise venue policy kanıtı gelene kadar `DEFERRED`. |
| Claude A-1: application contract’ları API’ye bağlı değil | `ACCEPTED / DEFERRED` | Contract’lar tek tek P2 binding dilimleriyle bağlanacak; toplu adapter/API açılımı yapılmayacak. |
| Claude A-3/Sol F-07: `server/api.py` hotspot | `ACCEPTED / DEFERRED` | 2.253 satırlık dosya doğrulandı; davranış değişikliğine yol açmayacak route/schema ayrımı ayrı refactor kapısıdır. |
| Sol F-05: historical sim gerçek backtest değil | `ACCEPTED / EXISTING LIMITATION` | `INDETERMINATE` ve execution-limitation açıklaması korunuyor; likidite/latency modeli eklenmedi. |
| Sol F-06: live trading hazır değil | `ACCEPTED / NO-GO` | Signed account, mutation, live recovery ve mainnet açılmadı. |
| Sol F-08: CI/static kalite yok | `ACCEPTED / PARTIAL` | Temel GitHub Actions mevcut; coverage threshold ve Ruff/mypy/pyright ayrı kalite işi olarak `DEFERRED`. |
| Sol F-09: wheelhouse/SBOM/image provenance | `ACCEPTED / P3.01` | Operasyon/release provenance kapsamına taşındı; şimdi ek kaynak gerektirdiği için runtime’a eklenmedi. |
| Sol F-10: semantic fee/funding event tipleri | `ACCEPTED / DEFERRED` | Venue binding öncesi ürün/ledger sınırı olarak korunuyor; mevcut converter değiştirilmedi. |
| Buffy HATA-b: kalite response biçimi | `ACCEPTED / COMPLETE` | PASS/REJECTED tek `JSONResponse` sözleşmesine alındı ve `no-store` doğrulandı. |
| Buffy HATA-c/e/j: quality alanları, Content-Length ve 30+ state iddiası | `REJECTED / STALE veya SAFE BY DESIGN` | Güncel parser bu alanları taşımıyor, body sınırı fiilî byte okumasıyla korunuyor, `App.tsx` state sayısı 15. |
| Buffy HATA-d/g/h/i: config cache, SQLite/process ownership, CORS | `ACCEPTED / P3.01` | Güvenli offline demo için davranış korunuyor; deployment, multi-worker ve production origin sözleşmesi sonraki operasyon kapısıdır. |
| Tüm raporların OCO/MARKET/conditional, otomatik retry, multi-exchange önerileri | `DEFERRED / NO-GO` | Güncel Binance contract araştırması sonrası sıra `MARKET/BASE_QUANTITY → conditional → order-list/OCO`; sözleşme ve oracle olmadan ekonomik kod açılmayacak. |

Güncel yerel sonuç: standart ve optimize Python regression `459/459 PASS`; compileall, workspace, frontend build ve release manifest kontrolleri PASS. Rapor karşılaştırması sonucunda bu turda yeni ekonomik davranış eklenmedi ve ek dış kaynak kullanılmadı.

## 2026-09-15 offline reconciliation-result evidence binding

P2.03/P2.04 için sıradaki güvenli mikro-faz tamamlandı. `DurableReconciliationObservation` REST lookup sonucunu yalnız redacted kanıt olarak taşıyabiliyor; journal canonical hash/idempotency/conflict sınırını koruyor, lookup sonucu ekonomik fill/core event üretmiyor. Exact `UserDataEvent ↔ OrderLookup` identity classifier yalnız birebir `FOUND` eşleşmesini `MATCHED`, kimlik uyuşmazlığını `CONFLICT`, diğer lookup sınıflarını `UNRESOLVED` yapıyor. Bu eşleşmeden `SpotOrderEvent`/execution kimliklerini taşıyan, ekonomik alan içermeyen mapping candidate üretilebiliyor; `MATCHED` olmayan evidence candidate oluşturamıyor. Lookup alanı olmayan eski journal payload’ları okunabilir bırakıldı. Candidate aynı offline SQLite journal’ında bounded, checksum’li, idempotent/conflict kontrollü biçimde persist/replay ediliyor; matched evidence ile candidate aynı transaction’da cross-check edilerek yazılıyor, hata halinde ikisi de rollback oluyor. Yalnız ayrıca durable candidate+matched evidence, birebir Spot event kimlikleri ve kabul edilmiş (`ACCEPTED`/`DUPLICATE`) stream kararı doğrulanırsa mevcut guarded LIMIT→core binder’a explicit admission yapılabiliyor; candidate replay tek başına core projection’a terfi etmiyor. Bağımsız admission-boundary review yerel olarak kapandı. MARKET/conditional genişletmesi, canlı signed REST/WS ve Testnet mutation açılmadı. Durum: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; kanıt: `evidence/P2.03/DURABLE_BINDING_SONUC.md`.

## 2026-09-15 MARKET / conditional / order-list scope gate

Yerel kaynak incelemesi şu kararı verdi:

| Alan | Karar | Gerekçe |
|---|---|---|
| MARKET → core ekonomik binding | `DEFERRED / NO-GO` | Spot lifecycle MARKET’i tanıyor; ancak core `Order` limit fiyatını zorunlu tutuyor ve `FILL` fiyatını bu limite göre denetliyor. MARKET etkin fiyatı, `quoteOrderQty` → gerçekleşen base miktarı, partial-fill ve slippage sözleşmesi kanıtlanmadan ekonomik binding eklenmeyecek. Mevcut MARKET → limit core reddi korunacak. |
| Conditional order lifecycle | `DEFERRED / NO-GO` | Aktif trigger/activation, gap, cancel ve execution state modeli bulunmuyor. Venue sözleşmesi ve ekonomik sahiplik kanıtlanmadan yeni tip eklenmeyecek. |
| Order-list / OCO lifecycle | `DEFERRED / NO-GO` | Parent/list kimliği, leg koordinasyonu, cancel-replace ve restart persistence sözleşmesi bulunmuyor. Varsayımla çoklu emir semantiği açılmayacak. |

Bu karar yeni ekonomik kod eklemez; mevcut fail-closed sınırı korur. Sonraki açılabilir iş ancak bağımsız ekonomik model, venue lifecycle sözleşmesi ve kapsamlı test oracle’ı hazır olduğunda seçilecektir.

## 2026-09-16 MARKET / conditional / order-list contract research gate

Resmi Binance Spot dokümantasyonu ile mevcut checkout karşılaştırıldı. MARKET’in
`quantity` (base) veya `quoteOrderQty` (quote) ile çalıştığı ve gerçekleşen base
miktarının likiditeye bağlı olduğu; conditional türlerde `stopPrice` tetikleme ile
oluşan MARKET/LIMIT execution’ın ayrıldığı; OCO/order-list tarafında liste ve bacak
kimlikleri ile working/pending durumlarının ayrı taşındığı doğrulandı. Bu alanlar
mevcut `domain.engine` limit fiyatı, tek order kimliği ve tekil `INTENT/FILL` sınırına
varsayımla bağlanamaz.

Kapsam daraltılmış ilk offline ekonomik sözleşme `MARKET/BASE_QUANTITY` için
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` olarak tamamlandı; core binding hâlâ
`MARKET_CORE_BINDING = DEFERRED / NO-GO`,
`CONDITIONAL_LIFECYCLE = DEFERRED / NO-GO`,
`ORDER_LIST_OCO_LIFECYCLE = DEFERRED / NO-GO`. Yalnız izole MARKET ekonomik
contract’ı eklendi; core ekonomik binding açılmadı.
MARKET için effective price/quote-to-base/cumulative quote/slippage/partial-fill;
conditional için trigger-to-execution state ve gap/cancel; order-list için
list/leg identity, coordination ve restart atomicity sözleşmeleri ayrı kabul
kapısı olmadan açılamaz. Kanıt: `evidence/P2.03/MARKET_CONDITIONAL_ORDER_LIST_CONTRACT_SONUC.md`.

2026-09-16 MARKET execution/reconciliation sonrası durable replay mikro-fazı
tamamlandı. Exact `MarketBaseExecution` state’i ve redacted
`MarketExecutionReconciliationBinding` ayrı bounded SQLite store’da canonical
payload/checksum ile transaction-safe persist/replay ediliyor. Aynı binding
duplicate olarak idempotent kalır; farklı payload conflict verir; immutable
execution kimliği, fill geçmişi ve terminal state değiştirilemez. Restart
replay yalnız MARKET projection üretir; core event, balance, order authority,
secret veya live transport üretmez. Durum:
`MARKET_DURABLE_ECONOMIC_REPLAY = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.
Store tek execution projection’ı ve bounded binding kapasitesiyle sınırlıdır;
MARKET → core ekonomik binding, `quoteOrderQty`, conditional/order-list ve
Testnet mutation hâlâ `DEFERRED / NO-GO`/kapalıdır. Odak `5/5`, tam ve optimize
suite `478/478 PASS`; kanıt aynı dosyadadır.

### Yeniden açılma sırası — 10 dakikalık mikro-görevler

1. **MARKET / BASE_QUANTITY ekonomik sözleşmesi:** yalnız explicit base miktarlı
   MARKET adayı; her execution için exact base/quote/etkin fiyat/fee ve toplam
   invariant’ı. `quoteOrderQty`, ilk dilimden bilinçli olarak dışarıda kalır.
   `MarketBaseExecution` offline sözleşmesi, exact execution/reconciliation
   identity binding ve sınırlı durable replay `LOCAL_PASS`; core binding ve
   gerçek MARKET emri hâlâ kapalıdır.
2. **Conditional trigger → execution sözleşmesi:** mevcut trigger gözlemi ile
   yeni executable order identity’sini ayıran, gap/stale/cancel yarışlarını
   kapsayan offline/fake state tablosu. Trigger/execution identity ve yarış
   sınırı `LOCAL_PASS`; durable replay ve gerçek venue identity kapalıdır.
3. **Order-list/OCO sözleşmesi:** list/leg identity, working/pending, liste
   durumları, leg koordinasyonu ve restart/replay atomicity.

Her mikro-görev önce kanıt ve bağımsız oracle üretir; ekonomik core binding ancak
ilgili sözleşme gerçekten kabul edilirse açılır. Bu sıra ürün yol haritasını
değiştirmez ve canlı signed/mutation kapısını açmaz.

2026-09-16 MARKET core binding karar kapısı: mevcut guarded binder hem
`quoteOrderQty` hem explicit base-quantity MARKET lifecycle event’ini
`CORE_ORDER_TYPE_UNSUPPORTED` ile reddediyor; core state, lifecycle ve core event
çıktısı değişmeden kalıyor. Bu sonuç, mevcut core `Order.limit` zorunluluğunun ve
`FILL` limit-fiyat kontrolünün MARKET effective price’ı varsayımla taşıyamadığını
doğruluyor. Karar:
`MARKET_CORE_BINDING = DEFERRED / NO-GO / LOCAL_PASS`. Yeni core event şeması,
fee-asset/quantity authority ve bağımsız ekonomik oracle tanımlanmadan binder
genişletilmeyecek. Odak core-binding sınıfı `8/8 PASS`; tam/optimize suite
`479/479 PASS`.

2026-09-16 conditional trigger → execution mikro-fazı tamamlandı. Yeni
venue-neutral projection, trigger gözlemini explicit executable order
kimliğinden ayırıyor; trigger `ACCEPTED` olmadan execution bağlanamıyor. Aynı
trigger duplicate olarak idempotent, farklı payload conflict; execution
gözlemi trigger’dan önceyse reddediliyor. `GAP`, `STALE` veya `CONFLICT`
quarantine’ı trigger kimliğini silmeden yeni execution’ı kapatıyor. Explicit
cancel confirmation, execution kimliği bağlandıktan sonra gelen cancel yarışını
sessiz başarıya çevirmiyor. Bu katman fill, core event, persistence, gerçek
venue veya mutation yetkisi taşımaz. Durum:
`CONDITIONAL_TRIGGER_EXECUTION = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.
Odak `6/6`, tam ve optimize suite `485/485 PASS`; conditional durable replay
ve venue-specific identity hâlâ `DEFERRED / NO-GO`.

2026-09-16 conditional durable replay mikro-fazı tamamlandı. Projection ayrı
bounded SQLite store’da canonical payload ve SHA-256 checksum ile persist/replay
ediliyor; `ARMED → TRIGGERED → EXECUTION_IDENTIFIED` geçiş sırası zorunlu,
duplicate idempotent, immutable state conflict ve tamper fail-closed. Replay
fill, core event, order authority, secret veya canlı venue üretmez. Durum:
`CONDITIONAL_DURABLE_REPLAY = IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.
Odak `3/3`, tam ve optimize suite `488/488 PASS`; venue-specific identity ve
live integration hâlâ `DEFERRED / NO-GO`.

2026-09-16 conditional mikro-görevi tamamlandı: mevcut stop/exit akışında trigger
gözlemi, executable intent, ekonomik fill ve terminal cancellation ayrımını
koruyan; kısmi fill sonrası kalan STOP kararını doğrulayan offline regresyon
eklendi. Bu yalnız `LOCAL_PASS_WITH_LIMITATION` kanıtıdır; gerçek venue
conditional identity, gap/stale ve cancel yarışları hâlâ `DEFERRED / NO-GO`.
Sıradaki tek iş order-list/OCO lifecycle sözleşme boşluğunun offline/fake
denetimidir.

2026-09-16 order-list/OCO mikro-görevi tamamlandı: aktif kaynakta liste/bacak
kimliği, working/pending, list-level state veya atomic replay sahibi bulunmadı;
mevcut HEDGE two-leg projection OCO authority’si değildir. Yeni model, adapter
veya ekonomik state eklenmedi. Karar `DEFERRED / NO-GO / LOCAL_PASS`; yeniden
açılma için önce immutable offline/fake list/leg state tablosu ve atomic replay
owner sözleşmesi kabul edilmelidir. Sıralı 10 dakikalık sözleşme denetimi burada
sona erdi.

## 2026-09-15 Buffy hata raporu kararları

`DCABOT_HATA_RAPORU.md` mevcut checkout’a karşı yeniden denetlendi. Raporun 437 testlik sayımı rapor tarihindeki kanıttır; düzeltme ve ek regresyon sonrasında güncel suite `454/454 PASS`’tir.

| ID | Karar | Yol haritası etkisi / kanıt |
|---|---|---|
| HATA-2026-09-15.a | `REJECTED / EXISTING LIMITATION` | İlk mark sonrasında `State.orders` boşken BASE kararı erişilebilirdir. Tamamlanan deal’in order geçmişi kasıtlı korunur ve yeni BASE otomatik açılmaz; bu CORE01/P1.08 sınırı dokümante edilmiştir. |
| HATA-2026-09-15.b | `ACCEPTED / COMPLETE` | `_quality_response()` artık PASS ve REJECTED sonuçlarını aynı `JSONResponse` biçiminde, `Cache-Control: no-store` ile döndürüyor; API testi eklendi. |
| HATA-2026-09-15.c | `REJECTED / STALE` | Raporun işaret ettiği `quote_volume`/`trade_count` parse satırları güncel `quality.py` içinde yok; aktif canonical bar sözleşmesi bu alanları taşımıyor. Eski kod varsayımıyla yeni alan/hesap eklenmedi. |
| HATA-2026-09-15.d | `ACCEPTED / DEFERRED` | `_load_config()` istekte diskten okuyor; bu performans önerisi config invalidation/refresh sözleşmesi ve ölçüm olmadan cache’lenmedi. Mevcut davranış güncel config hash’ini sessizce bayatlatmıyor. |
| HATA-2026-09-15.e | `REJECTED / NO-GO` | `Content-Length == 0` gerçek gövdenin okunmasını ortadan kaldırmaz; chunked/başlıksız body için de fiilî byte sınırı gerekir. Mevcut negatif/geçersiz/büyük değer kontrolleri korunmuştur. |
| HATA-2026-09-15.f | `REJECTED / SAFE BY DESIGN` | Hydration state sırası `FAILED`’i daha düşük riskli durumlardan üstün tutarak fail-closed davranır; `SYNCED` hydration sonrası doğrudan geri yüklenmez. Bu sonuç için odak regresyon testi eklendi. |
| HATA-2026-09-15.g | `ACCEPTED / P3.01` | `xb` ile normal çift init yarışı reddediliyor, ardından SQLite yalnız `mode=rw` açılıyor. Kalan path ownership/TOCTOU ve çok-process hardening deployment/worker kapısına taşındı. |
| HATA-2026-09-15.h | `ACCEPTED / P3.01` | CORS şu an loopback Vite geliştirme origin’leriyle sınırlı; production origin allowlist’i deploy konfigürasyonunda tanımlanacak. Wildcard açılmayacak. |
| HATA-2026-09-15.i | `ACCEPTED / P3.01` | Modül global’leri process’ler arasında paylaşılmıyor; multi-worker sahipliği, durable state ve tek-yazıcı/fence modeli operasyon fazında kanıtlanmadan varsayılmayacak. |
| HATA-2026-09-15.j | `REJECTED / STALE` | Güncel `App.tsx` içinde 15 `useState` kullanımı var; “30+” iddiası eski checkout’a ait. State refactor’ı ancak frontend davranış testleri sonrasında bakım işi olarak değerlendirilebilir. |

## P1 — Arayüzlü demo ürün

Her satır küçük dikey davranıştır: ekran → application/çekirdek → kayıt/sonuç → odak test. Büyük başlıklar gerektiğinde .a/.b alt işlere bölünür; her oturumda tek iş vardır. Arayüz en baştan gelişir.

| ID | Kullanıcıya görünen teslim | Kabul |
|---|---|---|
| P1.12.f.i | Pionex DIY per-safety-order deviation/allocation profilini exact sözleşmeye bağla | `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`; per-level cumulative deviation, strict index/order, tick-aligned LONG/SHORT prices, explicit `BASE_QTY`/`QUOTE_NOTIONAL` allocation ve exact budget conservation; odak `5/5`, ilişkili `43/43`, tam suite `616/616 PASS`; i.a ile quantity-step/venue filter candidate bağlandı; `SHARE`, persistence ve live mutation yok |
| P1.12.f.i.a | Custom ladder allocation’ını quantity-step ve quote/base candidate sözleşmesine bağla | `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`; existing instrument filter profile kullanıldı, BASE_QTY/QUOTE_NOTIONAL post-quantization actual allocation, quantity-step, min-quantity ve min-notional fail-closed doğrulandı; odak `14/14`, ilişkili `49/49`, tam suite `619/619 PASS`, compile/workspace PASS; order/mutation yok |
| P1.12.f.i.b | Custom candidate projection için bağımsız oracle ve kritik gate | `IMPLEMENTED_WITH_LIMITATION / INDEPENDENT_REVIEW_PASS`; bağımsız Decimal oracle ve AST/write-surface kontrolü PASS; odak `17/17`, ilişkili `52/52`, tam suite `622/622 PASS`, compile/workspace/diff PASS; persistence, HTTP, Binance/venue mutation yok |
| P1.12.f.i.c | Immutable custom candidate acceptance-boundary sözleşmesi | `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`; deterministic SHA-256 identity, tamper/conflict fail-closed revalidation ve `order_authority=NONE`; odak `20/20`, ilişkili `55/55`, tam suite `625/625 PASS`, compile/workspace/diff PASS; persistence, order attempt ve venue mutation yok |
| P1.12.f.i.d | Custom candidate acceptance’ını offline sizing/pre-acceptance köprüsüne bağla | `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; quote-notional candidate ilk seviyesi mevcut `SizingCandidate`, kalan seviyeler `LadderBinding` ile eligible quote budget’a karşı doğrulanıyor; BASE_QTY örtük quote dönüşümü yok; odak `23/23`, ilişkili `27/27 PASS`, tam proje `626/628` (faz dışı Credential Manager 1312 environment error); order authority/persistence/venue mutation yok |
| P1.12.g.a | Futures DCA immediate/closed-candle/signal start-condition gate | `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; mevcut `SignalReadiness` closed-bar/warmup/staleness kararını koruyor, source-time boundary ile eligibility/blocking üretiliyor; odak `20/20 PASS`, tam proje `634` testte `632 PASS` ve faz dışı Credential Manager 1312 nedeniyle `2` environment error; compile/AST/write-surface/diff PASS; lifecycle/order/fill/reserve/persistence/Binance mutation yok |
| P1.12.g.b | Futures DCA max-DCA/stop/EXHAUSTED terminal contract | `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; unconsumed ladder `CONTINUE`, remaining ladder with max-DCA cap `STOP`, explicit external stop reasons separate, full ladder `EXHAUSTED`; odak `19/19 PASS`, tam proje `640` testte `638 PASS` ve faz dışı Credential Manager 1312 nedeniyle `2` environment error; compile/AST/write-surface/diff PASS; new order/recovery/lifecycle mutation yok |
| P1.12.g.c | Futures DCA average-entry TP ve split-TP miktar conservation projection | `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; observed fill average-entry’den LONG/SHORT exact target, off-grid target fail-closed, split toplamı açık pozisyonu aşamaz ve kalan miktar exact; odak `18/18 PASS`, tam proje `647` testte `645 PASS` ve faz dışı Credential Manager 1312 nedeniyle `2` environment error; compile/AST/write-surface/independent oracle/diff PASS; TP order/OCO/cancel-replace/fill/reserve/persistence/Binance mutation yok |
| P1.12.g.d | Futures DCA fee-aware breakeven boundary contract | `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; explicit fee/funding profile olmadan gross-only, third fee asset ve settlement mismatch fail-closed; settlement-notional modelinde LONG/SHORT signed-funding exact boundary, off-grid/unrepresentable fail-closed; odak `9/9 PASS`, tam proje `656` testte `654 PASS` ve faz dışı Credential Manager 1312 nedeniyle `2` environment error; bağımsız Fraction oracle/compile/AST/write-surface/diff PASS; fee conversion/rounding, exit execution, persistence/Binance mutation yok |
| P1.12.g.e | Futures DCA exit priority ve eşzamanlı trigger karar contract’ı | `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; STOP_LOSS > TRAILING_STOP > TAKE_PROFIT > BREAKEVEN_ADJUSTMENT, breakeven yalnız ADJUST_STOP, close trigger varsa suppression, input-order invariant ve duplicate fail-closed; odak `9/9 PASS`, tam proje `665` testte `663 PASS` ve faz dışı Credential Manager 1312 nedeniyle `2` environment error; bağımsız alt-küme oracle/compile/AST/write-surface/diff PASS; exit candidate/order/fill/OCO/cancel-replace/reserve/persistence/Binance mutation yok |
| P1.12.g.f | Futures DCA selected exit-candidate ve açık pozisyon kapasitesi contract’ı | `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; g.e’nin seçtiği CLOSE trigger’ı exact tick-grid trigger fiyatı ve requested quantity ile bağlar; TP/SL/trailing kabul, breakeven/no-trigger fail-closed, accepted fill + committed exit + aday exact conservation; odak `9/9 PASS`, tam proje `674` testte `672 PASS` ve faz dışı Credential Manager 1312 nedeniyle `2` environment error; bağımsız Fraction oracle/compile/AST/write-surface/diff PASS; `order_authority=NONE`, gerçek order/fill/OCO/cancel-replace/reserve/persistence/Binance mutation yok |
| P1.12.g.g | Futures DCA candidate identity ve late-fill/conditional execution ayrım contract’ı | `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; g.f adayından trigger/fiyat/requested/kalan kapasite/açık miktar/zaman bağlı canonical SHA-256 identity, tamper fail-closed; late fill aynı identity’ye bağlı, sıralı ve requested miktar sınırında salt-okunur observation; odak `7/7 PASS`, tam proje `681` testte `679 PASS` ve faz dışı Credential Manager 1312 nedeniyle `2` environment error; bağımsız identity/tamper oracle/compile/AST/write-surface/diff PASS; conditional execution/order/fill mutation, persistence/Binance mutation yok |
| P1.12.g.h | Futures DCA fee-aware exit-candidate ve quantization boundary contract’ı | `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; explicit fee/funding profilinden exact fee-aware breakeven yalnız TAKE_PROFIT adayına bağlanıyor; profile-required, settlement mismatch, off-grid ve over-close fail-closed; sessiz rounding yok, STOP/Trailing breakeven adayı değil; odak `9/9 PASS`, tam proje `690` testte `688 PASS` ve faz dışı Credential Manager 1312 nedeniyle `2` environment error; bağımsız Fraction capacity oracle/compile/AST/write-surface/diff PASS; order/fill/OCO/cancel-replace/reserve/persistence/Binance mutation yok |
| P1.12.h.a | Futures DCA durable recovery/replay readiness gate | `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; schema v4 profile/event/reservation/release/posting/replay-receipt sahipliği, restart sequence/checksum/link replay, read-only receipt preflight, atomic failure rollback, exact duplicate/conflict ve CORE01 admission BLOCKED; odak `39/39 PASS`, tam proje `690` testte `688 PASS` ve faz dışı Credential Manager 1312 nedeniyle `2` environment error; compile/independent restart oracle/diff PASS; Binance/account/order mutation ve mainnet yok |
| P1.12.h.b | Futures DCA profile-bound recovery capability ve CORE01 admission boundary | `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; tek profile revision için accepted event, economic posting, release transition ve CORE01 replay receipt kapsamı birebir doğrulanır; eksik receipt/release, bozuk journal ve cross-profile transition fail-closed `BLOCKED`; odak `4/4 PASS`, h.a ile ilişkili `43/43 PASS`, tam proje `694` testte `692 PASS` ve faz dışı Credential Manager 1312 nedeniyle `2` environment error; compile/read-only byte-oracle/diff PASS; CORE01 economic admission, order/fill ve Binance mutation yok |
| P1.12.h.c | Futures DCA durable profile recovery snapshot ve stale quarantine | `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; accepted event/posting/release/replay receipt kimlikleri deterministik salt-okunur snapshot olarak projekte edilir; active profile mismatch QUARANTINED, bilinmeyen active profile veya bozuk journal BLOCKED, lineage projekte edilmez; odak `4/4 PASS`, h.a+h.b ilişkili `47/47 PASS`, tam proje `698` testte `696 PASS` ve faz dışı Credential Manager 1312 nedeniyle `2` environment error; compile/read-only source-surface/byte-oracle/diff PASS; CORE01 economic admission, order/fill ve Binance mutation yok |
| P1.12.h.d | Futures DCA recovery snapshot immutable provenance cross-check ve publish/migration gate | `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; recovery/provenance profile revision eşleşmesi, tekil ACCEPTED source snapshot, canonical manifest hash ve reopened target oracle’ı salt-okunur doğrulanır; stale/mismatch/eksik provenance veya prior/oracle failure NO_GO; temiz sonuç READY_FOR_REVIEW olsa da publish_action ve migration_action BLOCKED; odak `4/4 PASS`, h.a–h.d ilişkili `51/51 PASS`, provenance/manifest/reopen oracle `18/18 PASS`, tam proje `702` testte `700 PASS` ve faz dışı Credential Manager 1312 nedeniyle `2` environment error; compile/source-surface/diff PASS; gerçek source export, migration/publish, CORE01 ve Binance mutation yok |
| P1.12.f.h.av | Durable replay integrity oracle için bağımsız inceleme ve kritik gate | `IMPLEMENTED_WITH_LIMITATION / INDEPENDENT_REVIEW_PASS`; bağımsız AST/write-surface kontrolü PASS, odak `15/15`, tam suite `611/611 PASS`, compile/workspace PASS; CORE01 durable owner ve venue/Binance mutation yok |
| P1.12.f.h.au | Durable replay integrity sınırlarını read-only CORE01 restart oracle ile doğrula | `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`; event/posting/release/reservation checksum/consistency bozulması fail-closed `BLOCKED`, pure duplicate ve retry duplicate/conflict sınırları, aynı scope farklı receipt fingerprint conflict’i doğrulandı; odak `15/15`, ilişkili `55/55`, tam suite `611/611 PASS`; durable write, Binance/venue mutation, mainnet, secret, migration ve publish yok |
| P1.12.f.h.at | Atomik receipt binding’i restart sonrası read-only CORE01 replay projection oracle’ıyla karşılaştır | IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY; durable event/posting/release/receipt doğrulaması, pure decision/projection eşitliği, eksik receipt/stale admission BLOCKED; odak 12/12, ilişkili 52/52, tam suite 608/608 PASS; CORE01 durable owner ve venue mutation yok |
| P1.12.f.h.as | Futures DCA fill/release/posting ile CORE01 replay receipt’i tek transaction’da bağla | IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY; dört kayıt birlikte ACCEPTED veya DUPLICATE, receipt failure ve scope mismatch tam rollback; odak 25/25, ilişkili 49/49, tam suite 605/605 PASS; Binance/Testnet/mainnet mutation yok |
| P1.12.f.h.ar | Durable CORE01 replay receipt append/load sözleşmesini greenfield journal’a bağla | IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY; schema revision 4, accepted event/posting/release/reservation link doğrulaması, exact DUPLICATE/CONFLICT ve restart load; odak 16/16, ilişkili 46/46, tam suite 602/602 PASS; receipt append henüz ekonomik binding ile aynı transaction değil |
| P1.12.f.h.aq | Durable CORE01 replay receipt Store için schema/idempotency/restart preflight’i çalıştır | `IMPLEMENTED_WITH_LIMITATION / NO_GO_CONFIRMED`; mevcut journal’da receipt owner tablosu eksikliği ve gerekli fingerprint/scope unique contract kanıtlandı; odak `3/3`, ilişkili `43/43`, tam suite `599/599 PASS`; migration/receipt write yok |
| P1.12.f.h.ap | CORE01 + Futures DCA replay receipt için exact idempotency/conflict contract’ını doğrula | `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`; canonical fingerprint, same-scope `DUPLICATE`, same-scope `CONFLICT`, farklı scope `BLOCKED`; odak `17/17`, ilişkili `68/68`, tam suite `596/596 PASS`; durable Store/journal/restart mutation yok |
| P1.12.f.h.ao | CORE01 FILL projection’ını Futures DCA release/posting replay kararıyla salt-okunur birleştir | `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`; identity, FILL, commitment/fee ve release consumed-delta exact; DUPLICATE yeniden economics üretmiyor; odak `14/14`, ilişkili `65/65`, tam suite `593/593 PASS`; Store/journal/posting/venue mutation yok |
| P1.12.f.h.an | Admitted CORE01 FILL tuple’ını kopya state üzerinde exact reducer projection olarak doğrula | `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`; position quantity, entry notional, fee ve order filled/notional exact projection; odak `12/12`, ilişkili `50/50`, tam suite `591/591 PASS`; Store/journal/posting/venue mutation yok |
| P1.12.f.h.al | CORE01 intent identity authority’sini State/Order sözleşmesinde temsil et | `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`; explicit intent kimliği order state ve restart serializer’ında korunuyor; admission oracle exact identity ile `ADMISSIBLE`, eksik/conflict `BLOCKED`; odak `8/8`, tam suite `587/587 PASS`; economic FILL/posting mutation yok |
| P1.12.f.h.ak | Immutable Futures DCA mapping candidate için mevcut CORE01 order scope’unu salt-okunur admission oracle’ı ile kontrol et | `IMPLEMENTED_WITH_LIMITATION / NO_GO_CONFIRMED`; odak `7/7`, ilişkili guard `16/16`, tam suite `585/585 PASS`; intent identity CORE01 state’te temsil edilmediği için admission mutation yok; sıradaki intent authority kararı |
| P1.12.f.h.am | Explicit admitted mapping’i Futures DCA fill envelope ile CORE01 economic FILL boundary’sine bağla | `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`; identity/commitment/fee/funding/profile, fee asset, exact `qty * price`, terminal/UNKNOWN, overfill ve off-grid kontrolleri fail-closed; immutable FILL tuple proposal only; odak `10/10`, ilişkili `48/48`, tam suite `589/589 PASS`; reducer/Store/posting/venue mutation yok |
| P1.12.f.h.aj | Accepted Futures DCA event/posting için immutable CORE01 mapping candidate’ı üret | `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`; explicit profile/order/intent/role/side/limit contract, odak `5/5`, tam suite `583/583 PASS`; CORE01 mutation yok; sıradaki admission oracle |
| P1.12.f.h.ai | Durable Futures DCA posting replay’sini CORE01 ekonomik authority sınırında doğrula | `IMPLEMENTED_WITH_LIMITATION / NO_GO_CONFIRMED`; read-only preflight `3/3`, tam suite `578/578 PASS`; side/intent/role/limit mapping eksik olduğu için CORE01 mutation yok; sıradaki immutable mapping contract’ı |
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
| P1.12 | Spot ile lineer futures long/short ve gelişmiş Futures DCA ürün modellerini tamamla | P1.12.a explicit contract-size/settlement linear UPL + timestamped funding projection, P1.12.b partial-close/gross PnL ve P1.12.c immutable fee/funding event projection `COMPLETE_WITH_LIMITATION`; araştırma profili `USDⓈ-M/USDT/single-asset/one-way/isolated` olarak seçildi; P1.12.d fee/funding projection replay/idempotency `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (ayrı `linear_ledger_store.py`, CORE01 ekonomik binding yok); P1.12.e fixed-tier isolated liquidation estimate `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (risk-tier + isolated margin + mark snapshot zorunlu, venue liquidation değildir); P1.12.f.a Futures DCA exact plan projection `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, P1.12.f.b bağımsız exact Decimal oracle `COMPLETE_WITH_LIMITATION / LOCAL_PASS` (odak `2/2`, tam suite `507/507 PASS`), P1.12.f.c fill/average-entry + bounded pending projection `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (odak `4/4`, bağımsız oracle `2/2`, tam suite `513/513 PASS`), P1.12.f.d local event identity/sequence contract `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (odak `4/4`, tam suite `517/517 PASS`; Binance transport sequence’i değildir), P1.12.f.e shared-account reservation candidate binding `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (odak `3/3`, tam suite `520/520 PASS`; persistence/commit yok) ve P1.12.f.f durable event journal/replay `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (odak `4/4`, tam suite `524/524 PASS`; reservation/fill-release/economic posting atomicity yok); P1.12.f.g reservation + fill-release atomicity `DEFERRED / NO-GO / LOCAL_PASS` (kod değişmedi; ayrı SQLite transaction sınırları), P1.12.f.h atomic binding contract `CONTRACT_READY / IMPLEMENTATION_PENDING`, P1.12.f.h.a ayrı-ledger failure-injection `LOCAL_PASS / NO-GO_CONFIRMED` (event commit/reservation gap kanıtlandı), P1.12.f.h.b contract-size/multiplier commitment gate `DEFERRED / NO-GO / LOCAL_PASS`, P1.12.f.h.c multiplier exact oracle `COMPLETE_WITH_LIMITATION / LOCAL_PASS` (ekonomik binding `DEFERRED / NO-GO`), P1.12.f.h.af release transition state machine `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (odak `4/4`, tam suite `569/569 PASS`), P1.12.f.h.ag durable release update `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (odak `17/17`, tam suite `572/572 PASS`), P1.12.f.h.ah release + economic-posting atomic binding `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (odak `20/20`, tam suite `575/575 PASS`; cancel/late/UNKNOWN posting dışı), P1.12.f.i Pionex DIY per-safety-order deviation/allocation profile `RESEARCH_ACCEPTED_WITH_LIMITATION / IMPLEMENTATION_PENDING`; P1.12.f genel Futures DCA kapsamı `RESEARCH_READY / IMPLEMENTATION_PENDING`; P1.12.g.a immediate/closed-candle/signal start gate `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (odak `20/20`, tam proje `634` testte `632 PASS`, faz dışı Credential Manager 1312 nedeniyle `2` environment error); P1.12.g.b max-DCA/stop/EXHAUSTED `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (odak `19/19`, tam proje `640` testte `638 PASS`, faz dışı Credential Manager 1312 nedeniyle `2` environment error); P1.12.g.c average-entry/split-TP projection `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (odak `18/18`, tam proje `647` testte `645 PASS`, faz dışı Credential Manager 1312 nedeniyle `2` environment error); P1.12.g.d fee-aware breakeven contract `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (odak `9/9`, tam proje `656` testte `654 PASS`, faz dışı Credential Manager 1312 nedeniyle `2` environment error; explicit profile, signed funding, off-grid fail-closed; fee conversion/rounding ve exit execution yok); P1.12.g.e+ exit priority/trailing/OCO/real execution `PLAN / CONTRACT_REQUIRED`; P1.12.h durable recovery `PLAN / DEPENDENCY_REQUIRED`; cross/hedge/multi-asset `PLAN/DEFERRED` |
 | P1.13 | Spot Grid ve ayrı Futures Grid, trailing/reverse/infinity grid ve dönemsel alım ailelerini simüle et | P1.13.a exact aritmetik level generation + P1.13.b accepted-fill inventory projection + P1.13.c quote-asset fee, matched cycle profit/total equity projection + P1.13.d exact geometric root/tick validation `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.13.e Spot trailing range-revision/replacement `DEFERRED / NO-GO / LOCAL_PASS` çünkü exact range/version, pending/reserve, cancel-replace identity, late-fill, replay ve precision sözleşmesi yok; third-asset fee conversion ve venue rounding ayrı kapı; P1.13.f.a Futures Grid v1 ayrı profile + exact arithmetic/geometric levels `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.13.f.b one-way position/accepted-fill state `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.13.f.c isolated margin/leverage/reserve `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.13.f.d funding/mark/liquidation ve grid-profit/total-P&L `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.13.g.a dynamic order placement ile grid range/trailing ayrımı `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.13.g.b trailing/expansion/reversal/range revision/replacement `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.13.g.c advanced replacement/replay ve late-fill identity `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.13.g.d primary-source lifecycle audit `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED`; P1.13.g.e second primary-source report cross-audit `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED`, ileri implementation `DEFERRED / NO-GO`; P1.13.g Futures dynamic order placement (static/dynamic ayrı), trailing/expansion/reversal/replay, exact lifecycle implementation ve 3Commas Hedge Grid `PLAN / CONTRACT_REQUIRED` (hedge identity/P1.15 bağımlı); P1.13.h Reverse/Infinity profile variations `DEFERRED / NO-GO until verified`; dönemsel alım `PLAN`; her varyant ayrı davranış |
| P1.14 | Rebalancing, signal ve strategy template akışları | P1.14.a exact rebalancing target/delta projection + P1.14.b immutable signal identity/event-time/dedupe + P1.14.c warmup/closed-bar/stale readiness + P1.14.d threshold/time trigger + P1.14.e template integrity/non-authority + P1.14.f activation/capability gate `COMPLETE_WITH_LIMITATION`; actual activation transition, conversion/order sizing, profile binding, persistence, API ve UI `PLAN`; her sınır ayrı davranış |
| P1.15 | Genişletilmiş futures/hedge/cross ve çift bacaklı model gereksinimleri | P1.15.a hedge/net identity ve explicit two-leg intermediate state + P1.15.b aynı scope HEDGE LONG/SHORT accepted-fill projection `COMPLETE_WITH_LIMITATION`; P1.15.c persistence/replay/recovery `DEFERRED/NO-GO` çünkü mevcut lifecycle Store non-economic, generic Store two-leg/recovery lineage taşımıyor ve atomic binding kanıtlanmadı; P1.15 Futures DCA/Grid ile ortak kullanılacak hedge/cross/reduce-only/margin/venue profile sözleşmelerini taşır; cross ownership, liquidation, margin ve venue profile `PLAN/DEFERRED`; risk sözleşmeleri tamamlanmadan sahte arbitraj/liq sonucu yok |
 | P1.16 | Parametre kıyası, OOS/walk-forward ve stres çalışma alanı | P1.16.a chronological boundary `COMPLETE_WITH_LIMITATION / LOCAL_PASS` + P1.16.b OOS freeze/touched lineage `COMPLETE_WITH_LIMITATION / LOCAL_PASS` + P1.16.c feature/label overlap gate `COMPLETE_WITH_LIMITATION / LOCAL_PASS` + P1.16.d bounded trial registry `COMPLETE_WITH_LIMITATION / LOCAL_PASS` + P1.16.e ayrı stress lineage/result identity `COMPLETE_WITH_LIMITATION / LOCAL_PASS` + P1.16.f warmup/readiness research audit `DEFERRED / NO-GO / RESEARCH_AUDITED / LOCAL_PASS` + P1.16.g bounded local feature/label horizon ve historical runner binding `COMPLETE_WITH_LIMITATION / LOCAL_PASS` + P1.16.h bounded persisted trial/stress/OOS metadata binding `COMPLETE_WITH_LIMITATION`; P1.16.i.a authority/evidence inventory `COMPLETE_WITH_LIMITATION`; P1.16.i.b research audit `COMPLETE_WITH_LIMITATION`, ekonomik implementation `DEFERRED/NO-GO`; P1.16.i.c deterministic identity `COMPLETE_WITH_LIMITATION`, ekonomik scenario identity `DEFERRED/NO-GO`; P1.16.i.d persistence/replay/recovery `COMPLETE_WITH_LIMITATION`, stress persistence/branch/atomicity `DEFERRED/NO-GO`; P1.16.i.e `COMPLETE_WITH_LIMITATION/NO-GO`; ekonomik stress runner açılmaz |

Güncel P1.13 override: üstteki güncel mikro-faz kaydı bağlayıcıdır.
`P1.13.e` güvenli karar kapısı olarak `DEFERRED / NO-GO` bırakıldı; exact
trailing/reverse/infinity sözleşmesi doğrulanmadan numeric grid sonucu açılmaz.
`P1.13.f.a` ayrı profile ve exact level projection, `P1.13.f.b` one-way
position/accepted-fill state, `P1.13.f.c` isolated margin/leverage-reserve ve
`P1.13.f.d` funding/mark/P&L projection olarak tamamlandı. `P1.13.g.a`
dynamic order placement ile grid range/trailing ayrımı, `P1.13.g.b` ise
advanced variant safety gate olarak kapatıldı. Sıradaki aktif kabul
`P1.13.g.c` advanced grid replacement/replay ve late-fill identity karar
kapısı olarak kapatıldı. `P1.13.g.d` primary-source lifecycle audit tamamlandı;
`P1.13.g.e` ikinci raporun karşı-auditi tamamlandı; resmî kaynaklar exact
oracle sağlamadığı için ileri implementation `DEFERRED / NO-GO` ve ana
P1.13.g’nin kalan vendor-eşdeğer davranışları `CONTRACT_REQUIRED` kalır.
`P1.13.g.f` DCABOT’a özgü offline lifecycle politika kontratını
`CONTRACT_DECLARED` olarak tamamladı; tüm authority alanları `NONE`.
`P1.13.g.g` bu kontratı immutable in-memory offline transition simülasyonuna
bağlayarak `CONTRACT_READY` yaptı; vendor-eşdeğer implementation hâlâ
`DEFERRED / NO-GO`. `P1.13.g.h` local event matrix için bağımsız oracle ve
conflict/replay regresyon kapısını `ORACLE_PASS` olarak tamamladı. Sonraki tek
güvenli iş `P1.13.h.a` Reverse/Infinity varyantları için güvenlik kapısıdır.
`P1.13.h.a` her iki varyantı typed ve `BLOCKED_CONTRACT_REQUIRED` olarak
kapattı. `P1.13.h.b` mevcut araştırma kaynaklarının exact Reverse/Infinity
sözleşmelerini kapatmadığını karşı-audit ile doğruladı; vendor parity
`DEFERRED / NO-GO` kaldı. `P1.13.h.c` bu eksikliği ürün admission sınırında
`NOT_SUPPORTED + BLOCKED` olarak görünür kıldı. Sonraki tek iş
`P1.13.h.d` bağımsız inceleme ve kritik regresyon kapısını tamamladı. Sonraki
tek iş `P1.14.c` signal warmup/closed-bar ve stale-policy karar kapısıdır.

Güncel P1.12 override: ayrıntılı kabul satırları ve üstteki güncel mikro-faz
kayıtları bağlayıcıdır. `P1.12.h.d` tamamlandı. `P1.12.g.e+` ifadesi artık
yalnız g.f sonrası kalan execution, OCO/cancel-replace ve recovery kapsamını
ifade eder.

## Kanıt gerektiren fazların yürütme standardı

Bir iddia veya öneri mevcut kod/fixture ile doğrudan kanıtlanamıyorsa bu durum plansız bekleme olarak bırakılmaz; ilgili ana fazın altında numaralı bir kanıt alt fazı açılır. Alt faz sırası şöyledir:

1. **Kapsam ve sahiplik envanteri:** İddianın hangi davranışa, asset/unit’e, zaman türüne, state transition’a, API’ye veya persistence sahibine ait olduğu yazılır.
2. **Yerel kanıt kontrolü:** Aktif kaynak, test, fixture, schema ve mevcut evidence incelenir; yedek/archive delil sayılmaz.
3. **RED veya karşı örnek:** İddia mevcut değilse bunu gösteren sınırlı test/probe yazılır; mevcutsa sınır ve yanlış-pozitif davranış test edilir.
4. **Bağımsız kontrol:** Production kodunu tekrar kullanmayan hesap, transition tablosu, canonical hash, replay veya field-level oracle ile sonuç karşılaştırılır.
5. **Minimum uygulama kararı:** Yalnız iddia doğrulanmış ve sahiplik netse en küçük dikey değişiklik yapılır. Kanıt yetersizse `DEFERRED / NO-GO` yazılır; varsayımsal ekonomik/API/UI/persistence davranışı eklenmez.
6. **Kapanış:** Odak regresyon, tam regresyon, compile, workspace, güvenlik/veri sızıntısı kontrolü ve evidence kaydı tamamlanır; `STATE.md`, `TASK.md`, roadmap ve özellik matrisi aynı sonucu taşır.

Her alt faz için yalnız bir durum `ACTIVE` olabilir. Dış araştırma, yalnız yerel kontrolde cevaplanamayan ve uygulama kararını gerçekten değiştirecek açık iddia kaldığında istenir; prompt ilgili alt fazın kapsamını, anonimleştirme sınırını, beklenen kanıt formatını ve kabul/red ölçütünü içermelidir.

### Sessiz durak yasağı

`DEFERRED`, `NO-GO`, `CONTRACT_REQUIRED`, `IMPLEMENTATION_PENDING` veya
`oracle/source eksik` durumu kullanıcı blokajı değildir. Bu etiketler riskli
implementation’ın açılmadığını gösterir; yol haritası durmaz. Sıradaki her
çalışmada asistan bir WIP=1 araştırma, karşı-örnek, bağımsız offline oracle,
fail-closed admission/`NOT_SUPPORTED` guard veya minimum güvenli local dilimi
uygular ve TASK/STATE/evidence’ı günceller. Kullanıcı eylemi yalnız API
credential/hesap/CAPTCHA, ücretli/özel erişim, fiziksel/OS işlemi veya ekonomik
sonucu değiştiren açık ürün kararı gerektiğinde istenir. Teknik source
araştırması, implementation, test, compile, evidence ve doküman senkronu
asistanın sorumluluğudur.

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
| P1.19.g — Frontend kritik akış component-test kapısı | `COMPLETE_WITH_LIMITATION / LOCAL_PASS` | Vitest + React Testing Library + jsdom test runtime’ı eklendi. Dataset yardımcıları, idle/loading/error/ready grafik durumları, OHLC fail-closed validasyonu, dataset/artifact eşleşmeyen marker reddi, belirsiz prefix boundary ve backend açıklama görünümü doğrulandı. `3` dosya / `12/12` PASS; local Browser E2E preview → profile → 24 bar offline simülasyon akışı, desktop/390px screenshot ve console/overflow kontrolleri PASS. NVDA ve Narrator kullanıcı onayıyla `PASS`; gerçek Windows HCM `PASS / LOCAL_UI` ve test sonrası `Yok` geri yüklendi. Kanıt: `evidence/P1.19.g/SONUC.md` |
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
| P2.01.b | Public snapshot’ın UI’da salt-okunur gösterimi | `IMPLEMENTED_WITH_LIMITATION / READY_WITH_LIMITATION`: React kartı `CONNECTED_READ_ONLY`/loading/`FAILED`, status, permissionSets, order types, rate-limit/filter/hash disclosure ve kalıcı public/account sınırıyla gösteriyor; frontend hesaplama, secret ve order yolu yok. Güncel local Browser QA’da `CONNECTED_READ_ONLY`, `TRADING`, order types, 4 rate limit ve 11 symbol filter görünümü doğrulandı. Kanıt: `evidence/P2.01.b/SONUC.md` |
| P2.02 | Kalıcı attempt/outbox sender ve account rezervini gerçek sınırda doğrula | İlk offline attempt/outbox, P2.02.a signer/time, P2.02.b ephemeral credential/capability, P2.02.c Windows Credential Manager HMAC provider ve P2.02.d gerçek signed read-only account GET `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; gerçek REST/WS reconciliation, order/mutation ve mainnet `IN_PROGRESS/DEFERRED/NO-GO`. Kanıt: `evidence/P2.02/SONUC.md` |
| P2.02.d | İmzalı Testnet hesap okuması | `IMPLEMENTED_WITH_LIMITATION / LIVE_READ_ONLY_PASS`: Windows Credential Manager’dan HMAC credential yüklenerek yalnız sabit `GET /api/v3/account` çağrısı yapıldı; güvenli hesap/izin özeti ve `SIGNED_ACCOUNT_CONTEXT` capability üretildi. Sahte taşıma `3/3`, gerçek Testnet read-only GET `PASS`; bakiye değerleri repr/log/persistence’e alınmadı. Emir, mutation, WebSocket, reconciliation ve mainnet kapalı. Kanıt: `evidence/P2.02/SONUC.md` |
| P2.03 | Plain/conditional/koruyucu emir yaşamını test et | Fake/offline Spot LIMIT/MARKET lifecycle, isolated exact `MARKET/BASE_QUANTITY` economics ve execution/reconciliation identity binding, sınırlı MARKET offline durable replay, guarded LIMIT → core `INTENT/FILL/ORDER_FINAL` binding, redakte reconciliation association, redacted lookup-result evidence binding, exact `UserDataEvent ↔ OrderLookup` identity classifier, non-economic `SpotOrderEvent`/execution mapping candidate, candidate persistence/replay, matched evidence ↔ candidate atomic linkage ve explicit durable verified-mapping → guarded LIMIT admission `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; offline OCO order-list identity/bounded state projection da `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, ancak SQLite durable replay, venue reconciliation, real signed REST/WS ve mutation `IN_PROGRESS/DEFERRED/NO-GO`. Candidate ve MARKET/OCO replay tek başına core fill veya posting değildir. Kanıt: `evidence/P2.03/SONUC.md`, `evidence/P2.03/CORE_BINDING_SONUC.md`, `evidence/P2.03/DURABLE_BINDING_SONUC.md`, `evidence/P2.03/MARKET_CONDITIONAL_ORDER_LIST_CONTRACT_SONUC.md` |
| P2.04 | Restart, WS/REST reconciliation ve operasyon kontrolleri | Offline Fake WebSocket/Fake REST restart, duplicate/conflict, out-of-order, UNKNOWN, GAP, STALE, reset, disagreement, redakte durable observation + lookup-result evidence, exact venue-event identity classifier, non-economic `SpotOrderEvent`/execution mapping candidate, candidate persistence/replay, matched evidence ↔ candidate atomic linkage, explicit durable admission ve signed read-only WS `order.status` sorgu sınırı `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; gerçek event orchestration, reconnect/catch-up, live recovery ve mutation `IN_PROGRESS/DEFERRED/NO-GO`. Kanıt: `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`, `evidence/P2.04.c/SONUC.md`, `evidence/P2.03/P2.04_OFFLINE_ACCEPTANCE_SONUC.md`, `evidence/P2.03/DURABLE_BINDING_SONUC.md` |
| P2.05 | UI'dan Binance testnet kabul kampanyası | Public read-only snapshot ve offline/fake boundary kabulü `ACCEPT_WITH_LIMITATION`; odak `29/29 PASS`, gerçek signed account/order/mutation `DEFER`. Kanıt: `evidence/P2.05/SONUC.md` |

Testnet erişimi olmayan venue yeteneği gerçek testten geçmiş sayılmaz. Desteklenmeyen ürün/mode canlıya taşınmaz; bağlayıcı user kararı ve capability kaydı gerekir.

## P3 — Gerçek Binance kurulum

P3.01 dağıtım/başlangıç/upgrade/backup/restore, worker sahipliği ve gözlemleme; P3.02 read-only gerçek hesap karşılaştırması; P3.03 açık yetkili düşük limitli canary; P3.04 sürdürülebilir işletim ve doğrulanmış özellikleri kademeli açma. Withdraw/transfer yetkisi başlangıç gereksinimi değildir. P2 kanıtı P3'teki kullanıcı para yetkisinin yerine geçmez.

## P4 — Diğer borsalar

İstenen her borsa için: resmi API/capability → ayrı adapter → simulator contract test → sandbox varsa entegrasyon → read-only doğrulama → açık yetkili canary. Binance enum/ID/fee/filter/precision/account modeli evrensel kabul edilmez. Venue seçimi UI'ı veya çekirdeği kopyalamaz; destek farklarını gösterir.

## Opsiyonel — JAWS ekran okuyucu doğrulaması

Durum: `OPTIONAL / DEFERRED`; ücretsiz erişilebilirlik kabul kapısının parçası değildir.

JAWS lisans veya uygun deneme erişimi mevcut olduğunda, kullanıcı ayrıca isterse NVDA/Narrator klavye akışının bağımsız ekran okuyucu doğrulaması olarak çalıştırılabilir. Kurulum, lisans ve sesli sonuç için gereken kaynak kullanıcı tarafından sağlanmadıkça yeni kaynak eklenmeyecek; çalıştırılmadan `PASS` yazılmayacak. Kanıt geldiğinde yalnızca bu bölüm güncellenecek, canlı emir/mutation veya production readiness açılmayacak.
## 2026-09-18 P2.03 offline OCO order-list identity/state projection

P2.03’ün ilk order-list dili `COMPLETE_WITH_LIMITATION / LOCAL_PASS` olarak
ilerletildi. Resmî Binance Spot OCO tanımı ve güncel WebSocket trading cevabı
ile karşılaştırılan immutable `orderListId`/`listClientOrderId`/OCO identity,
iki leg, WORKING/PENDING rolleri ve bounded list/leg status projection’ı
uygulandı. Duplicate/conflict, out-of-order, terminal liste ve bir OCO bacağı
filled olduğunda diğer bacağın cancel/expire olması fail-closed doğrulandı.

Bu projection salt venue-fact state’tir; fiyat, miktar, fill, fee, reserve,
core event, cancel-replace, persistence, signed transport veya mutation
authority taşımaz. Odak `4/4 PASS`, P2.03 koruma kümesi `77/77 PASS`; tam
checker `792` testte `790 PASS` ve iki Windows Credential Manager ortam hatası
kaldı. Compileall/workspace (`290` aktif Python dosyası) ve diff check PASS;
kanıt:
`evidence/P2.03/MARKET_CONDITIONAL_ORDER_LIST_CONTRACT_SONUC.md`.

P2.03/P2.04 full gate `IN_PROGRESS`, trading activation `NO-GO` kalır. Sıradaki
tek güvenli iş bu state projection’ın SQLite transaction içinde atomic durable
replay owner’a bağlanmasıdır. [Resmî Spot API Glossary](https://developers.binance.com/en/docs/products/spot/faqs/spot_glossary)
ve [Spot WebSocket trading requests](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/ws-api/trade)
referans alınmıştır.
