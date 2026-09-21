# Özellik matrisi — ürün hedefi ve gerçek durum

Referans taraması: 6 Eylül 2026, resmî ürün belgeleri. Bu matris rakiplerin bütün ücretli/bölgesel ekranlarının tam envanteri değildir; doğrulanmış aileleri ve kullanıcının geniş ürün hedefini izlenebilir hale getirir. “PLAN” bitmiş özellik değildir. Kabul sütunu **bizim tasarım gereksinimimizdir**, rakipteki uygulamanın birebir tarifi değildir.

F01–F36 ve F39–F40 için P1'de uçtan uca demo hedeflenir; online kaynak/LLM dış erişimi açık istisnadır ve dosya/kural tabanlı yol çalışır. F37'nin simulated akışı P1, gerçek bağlantıları P2/P3/P4'tür. F38 için dış platform gereksinimi çözümlenmeden “tam rakip eşdeğerliği” ilan edilmez. KEŞİF satırları silinerek P1 kapısı geçilmiş sayılmaz; doğrulanan davranış ve açık kapsam kararı kayda girer.

Her gereksinim uygulamada aynı ID'li acceptance kaydı taşır: ui_status, kernel_status, data_model_status, test_status, evidence_path. Bu belge kapsamın tek kaynağıdır; durum ilerledikçe ilgili satır güncellenir.

## İlerleme ve kullanıcı blokajı politikası

`DEFERRED`, `NO-GO`, `CONTRACT_REQUIRED`, `IMPLEMENTATION_PENDING` veya
eksik oracle/source etiketi kullanıcıdan eylem isteme nedeni değildir. Teknik
araştırma, aktif kaynak/fixture kontrolü, karşı-örnek, bağımsız offline oracle,
fail-closed sınır ve güvenli local implementation asistan tarafından yürütülür.
Kanıt yetersizse riskli ekonomik/API/persistence davranışı açılmaz; bunun yerine
bir sonraki asistan-owned WIP=1 alt fazı ve kabul ölçütü TASK/STATE/evidence’a
yazılır. Kullanıcıdan yalnız credential/hesap/CAPTCHA, ücretli/özel erişim,
fiziksel/OS işlemi veya ekonomik sonucu değiştiren açık ürün kararı gerektiğinde
eylem istenir.

## Güncel P2 durumu — 2026-09-19 P2.04 post-gap mixed cursor repeated conflict stale old anchor final replay parity

Transaction-forward `(211,199)` ve event-forward `(209,211)` recovery
anchor’larından sonra tekrarlı fingerprint conflict `CONFLICT/GAP` açtı; tuple
sırasına göre eski mixed-component anchor’lar `(210,212)` ve `(208,212)`
`RESYNC_ANCHOR_STALE` kaldı. Aynı terminal boundary anchor yeniden kabul
edildi; `SNAPSHOT_STALE` → `SYNCED`, exact replay `DUPLICATE`, eski
recovery/conflict/anchor event’leri `QUARANTINED`, empty SQLite journal değişmedi.
Bu yalnız offline journal/reconciliation kanıtıdır; gerçek reconnect worker,
REST catch-up, core/economic binding, mutation ve mainnet yok. Odak `1/1`,
komşu `90/90`, tam checker `865/865 PASS`, compileall/workspace/diff PASS;
workspace `296` aktif Python dosyası. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`. Sıradaki tek güvenli iş stale
mixed-anchor reddinden sonra güncel cursor’ın snapshot retry ve final replay
boyunca korunması regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 post-gap mixed cursor forward terminal repeated fingerprint conflict re-entry freshness ve quarantine parity

Transaction-forward `(212,211)` ve event-forward `(211,212)` akışlarında aynı
forward boundary’de tekrarlı fingerprint conflict `CONFLICT/GAP`, aynı boundary
terminal recovery anchor, eşik altı snapshot `SNAPSHOT_STALE`, eşik snapshot
`SYNCED`, exact replay `DUPLICATE`, eski conflict/re-entry/terminal/replacement
event’leri `QUARANTINED` kaldı; empty SQLite journal değişmedi. Bu kabul
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `89/89`, tam
checker `864/864 PASS`, compileall, workspace (`296` aktif Python dosyası) ve
diff PASS. Gerçek reconnect worker, REST catch-up, core/economic binding,
mutation ve mainnet yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`. Sıradaki tek güvenli iş aynı
tekrarlı conflict sonrası eski mixed-component anchor monotonicity ve final
replay parity regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 post-gap repeated replacement anchor equal-boundary freshness ve duplicate quarantine parity

Tekrarlı replacement conflict sonrası eşit cursor’lı terminal recovery anchor
kabul ediliyor; `209` snapshot `SNAPSHOT_STALE`, eşik `210` snapshot `SYNCED`
oluyor. Terminal recovery replay `DUPLICATE`, önceki non-terminal recovery ve
forward event `QUARANTINED` kalıyor, empty SQLite journal değişmiyor. Bu kabul
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `82/82`, tam
checker `856/856 PASS`, compileall, workspace (`296` aktif Python dosyası) ve
diff PASS. Gerçek reconnect worker, REST catch-up, core/economic binding,
mutation ve mainnet yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`. Sıradaki tek güvenli iş
post-gap equal-boundary repeated recovery fingerprint conflict re-entry
parity regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 post-gap repeated replacement conflict anchor monotonicity ve terminal quarantine parity

İlk replacement conflict sonrası non-terminal recovery anchor ile yeniden
`SYNCED` açıldı; aynı recovery identity’nin tekrarlı fingerprint conflict’i
yeniden `CONFLICT/GAP` açıyor. Daha eski `209` recovery anchor
`RESYNC_ANCHOR_STALE`, monoton `211` terminal anchor kabul ediliyor; `210`
snapshot `SNAPSHOT_STALE`, `211` snapshot `SYNCED` oluyor. Terminal recovery
replay `DUPLICATE`, eski recovery ve forward event `QUARANTINED` kalıyor, empty
SQLite journal değişmiyor. Bu kabul `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`;
odak `1/1`, komşu `80/80`, tam checker `855/855 PASS`, compileall, workspace
(`296` aktif Python dosyası) ve diff PASS. Gerçek reconnect worker, REST
catch-up, core/economic binding, mutation ve mainnet yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`. Sıradaki tek güvenli iş
post-gap repeated replacement anchor equal-boundary freshness ve duplicate
quarantine parity regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 post-gap replacement fingerprint conflict ve re-entry quarantine parity

GAP sonrası aynı replacement identity’nin farklı fingerprint’i `CONFLICT/GAP`
açıyor; doğrudan authoritative snapshot `SYNC_STATE_INVALID` ile reddediliyor.
Transaction-ileri/event-geride ve event-ileri/transaction-geride recovery
anchor sonrası `209` snapshot `SNAPSHOT_STALE`, `210` snapshot `SYNCED` oluyor;
recovery exact replay `DUPLICATE`, eski replacement ve forward event
`QUARANTINED` kalıyor, empty SQLite journal değişmiyor. Bu kabul
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `79/79`, tam
checker `854/854 PASS`, compileall, workspace (`296` aktif Python dosyası) ve
diff PASS. Gerçek reconnect worker, REST catch-up, core/economic binding,
mutation ve mainnet yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`. Sıradaki tek güvenli iş
post-gap repeated replacement conflict anchor monotonicity ve terminal
quarantine parity regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 recovery anchor post-gap re-entry ve paired snapshot gate parity

GAP sonrası doğrudan snapshot `SYNC_STATE_INVALID`, iki paired recovery anchor
yönü yeniden `RECONCILIATION_REQUIRED`, `209` snapshot `SNAPSHOT_STALE`, `210`
snapshot `SYNCED` oluyor; recovery replay `DUPLICATE`, empty SQLite journal
değişmiyor. Bu kabul `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`,
komşu `78/78`, tam checker `853/853 PASS`, compileall, workspace (`296` aktif
Python dosyası) ve diff PASS. Gerçek reconnect worker, REST catch-up,
core/economic binding, mutation ve mainnet yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`. Sıradaki tek güvenli iş
post-gap replacement fingerprint conflict ve re-entry quarantine parity
regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 recovery anchor paired-component strict ordering ve quarantine parity

Transaction veya event cursor bileşeni gerilediğinde `OUT_OF_ORDER/GAP`, GAP
sonrası forward event `QUARANTINED` kalıyor; empty SQLite journal değişmiyor.
Dört paired ordering yönü doğrulandı. Bu kabul
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `77/77`, tam
checker `852/852 PASS`, compileall, workspace (`296` aktif Python dosyası) ve
diff PASS. Gerçek reconnect worker, REST catch-up, core/economic binding,
mutation ve mainnet yok. Kanıt: `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.
Sıradaki tek güvenli iş recovery anchor post-gap re-entry ve paired snapshot
gate parity regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 recovery anchor mixed component equal-boundary ve late-event quarantine parity

Transaction component ilerleyip event component geride kaldığında ve ters yönde
de equal max snapshot `SYNCED` oluyor. Terminal anchor sonrası
mixed-component late/forward event’ler `QUARANTINED`, exact replay `DUPLICATE`
kalıyor; empty SQLite journal değişmiyor. Bu kabul
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `76/76`, tam
checker `851/851 PASS`, compileall, workspace (`296` aktif Python dosyası) ve
diff PASS. Gerçek reconnect worker, REST catch-up, core/economic binding,
mutation ve mainnet yok. Kanıt: `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.
Sıradaki tek güvenli iş recovery anchor paired-component strict ordering ve
quarantine parity regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 recovery anchor transaction/event cursor component parity

Transaction component ilerleyip event component geride kaldığında ve event
component ilerleyip transaction component geride kaldığında `209` gözlem zamanlı
authoritative snapshot `SNAPSHOT_STALE`, max component `210` snapshot `SYNCED`
oluyor; empty SQLite journal değişmiyor. Bu kabul
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `75/75`, tam
checker `850/850 PASS`, compileall, workspace (`296` aktif Python dosyası) ve
diff PASS. Gerçek reconnect worker, REST catch-up, core/economic binding,
mutation ve mainnet yok. Kanıt: `evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.
Sıradaki tek güvenli iş recovery anchor mixed component equal-boundary ve
late-event quarantine parity regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 equal-cursor recovery anchor sonrası snapshot freshness boundary ve terminal quarantine parity

Recovery anchor sonrası `209` gözlem zamanlı authoritative snapshot
`SNAPSHOT_STALE`, eşik `210` snapshot `SYNCED` oluyor. Recovery terminal
identity exact replay `DUPLICATE`, eski ve ileri event’ler `QUARANTINED` kalıyor;
empty SQLite journal değişmiyor. Bu kabul `IMPLEMENTED_WITH_LIMITATION /
LOCAL_PASS`; odak `1/1`, komşu `74/74`, tam checker `849/849 PASS`, compileall,
workspace (`296` aktif Python dosyası) ve diff PASS. Gerçek reconnect worker,
REST catch-up, core/economic binding, mutation ve mainnet yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`. Sıradaki tek güvenli iş
recovery anchor transaction/event cursor component parity regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 equal-cursor replacement anchor sonrası same-cursor replacement fingerprint conflict ve snapshot gate parity

Aynı replacement identity’nin farklı fingerprint’i `CONFLICT/GAP` açıyor;
doğrudan authoritative snapshot reddediliyor. Yalnız yeni equal-cursor recovery
anchor ve taze snapshot ile `SYNCED` açılıyor; recovery exact replay
`DUPLICATE`, empty SQLite journal değişmiyor. Bu kabul
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `73/73`, tam
checker `848/848 PASS`, compileall, workspace (`296` aktif Python dosyası) ve
diff PASS. Gerçek reconnect worker, REST catch-up, core/economic binding,
mutation ve mainnet yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`. Sıradaki tek güvenli iş
equal-cursor recovery anchor sonrası snapshot freshness boundary ve terminal
quarantine parity regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 equal-cursor replacement anchor sonrası terminal identity ve late-event quarantine parity

Equal-cursor replacement anchor ile kurulan terminal identity’nin exact replay’i
`DUPLICATE`, terminal öncesi geç kalan event ve terminal sonrası ileri event
`QUARANTINED` kalıyor; coordinator `SYNCED` durumunu koruyor ve empty SQLite
journal değişmiyor. Bu kabul `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak
`1/1`, komşu `72/72`, tam checker `847/847 PASS`, compileall, workspace (`296`
aktif Python dosyası) ve diff PASS. Gerçek reconnect worker, REST catch-up,
core/economic binding, mutation ve mainnet yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`. Sıradaki tek güvenli iş
terminal replacement anchor sonrası same-cursor replacement fingerprint
conflict ve snapshot gate parity regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 terminal replacement anchor sonrası equal-cursor resync identity ve snapshot gate re-entry parity

Equal cursor’lı yeni replacement identity stale sayılmadan
`RECONCILIATION_REQUIRED` durumuna dönüyor; snapshot olmadan `mark_synced`
`AUTHORITATIVE_SNAPSHOT_REQUIRED` ile fail-closed kalıyor. Taze snapshot
sonrası aynı replacement `DUPLICATE` oluyor ve empty SQLite journal değişmiyor.
Bu kabul `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu
`71/71`, tam checker `846/846 PASS`, compileall, workspace (`296` aktif Python
dosyası) ve diff PASS. Gerçek reconnect worker, REST catch-up, core/economic
binding, mutation ve mainnet yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`. Sıradaki tek güvenli iş
equal-cursor replacement anchor sonrası terminal identity ve late-event
quarantine parity regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 terminal replacement anchor sonrası stale resync anchor ve snapshot gate re-entry parity

Stale resync anchor `RESYNC_ANCHOR_STALE` ile reddediliyor; `GAP` durumunda
doğrudan authoritative snapshot `SYNC_STATE_INVALID` ile engelleniyor. Yalnız
monotonic replacement anchor ve taze snapshot ile `SYNCED` açılıyor; empty
SQLite journal değişmiyor. Bu kabul `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`;
odak `1/1`, komşu `70/70`, tam checker `845/845 PASS`, compileall, workspace
(`296` aktif Python dosyası) ve diff PASS. Gerçek reconnect worker, REST
catch-up, core/economic binding, mutation ve mainnet yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`. Sıradaki tek güvenli iş
terminal replacement anchor sonrası equal-cursor resync identity ve snapshot
gate re-entry parity regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 terminal replacement anchor sonrası snapshot cursor freshness ve stale-boundary parity

Terminal anchor’ın transaction zamanı ve event zamanı ayrı ayrı sınandı;
cursor’ın en büyük bileşeninden eski `209` snapshot `SNAPSHOT_STALE`, eşit
`210` snapshot fresh kabul ediliyor. Bu kabul
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `69/69`, tam
checker `844/844 PASS`, compileall, workspace (`296` aktif Python dosyası) ve
diff PASS. Gerçek reconnect worker, REST catch-up, core/economic binding,
mutation ve mainnet yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`. Sıradaki tek güvenli iş
terminal replacement anchor sonrası stale resync anchor ve snapshot gate
re-entry parity regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 empty/reopen replacement anchor sonrası terminal cursor ve late-event quarantine parity

Terminal `REJECT` replacement anchor sonrası exact replay `DUPLICATE`,
terminal öncesi late event ve terminal sonrası yeni event `QUARANTINED` kalıyor;
coordinator yanlışlıkla `SYNCED` durumundan çıkmıyor ve boş SQLite journal
değişmiyor. Bu kabul `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`,
komşu `68/68`, tam checker `843/843 PASS`, compileall, workspace (`296` aktif
Python dosyası) ve diff PASS. Gerçek reconnect worker, REST catch-up,
core/economic binding, mutation ve mainnet yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`. Sıradaki tek güvenli iş
terminal replacement anchor sonrası snapshot cursor freshness ve
stale-boundary parity regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 empty/reopen aynı cursor identity conflict ve snapshot gate parity

Boş SQLite journal yeniden açıldıktan sonra resync anchor ile kurulan event
exact duplicate olarak kalıyor; aynı event kimliğinin farklı fingerprint’i
`CONFLICT` açıp `GAP` durumuna geçiriyor. Snapshot bu durumda doğrudan
uygulanamıyor; replacement anchor ve fresh snapshot olmadan `SYNCED` açılamıyor.
Journal anchor işlemleriyle değişmiyor ve boş kalıyor. Bu kabul
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `67/67`, tam
checker `842/842 PASS`, compileall, workspace (`296` aktif Python dosyası) ve
diff PASS. Gerçek reconnect worker, REST catch-up, core/economic binding,
mutation ve mainnet yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`. Sıradaki tek güvenli iş
empty/reopen replacement anchor sonrası terminal cursor ve late-event
quarantine parity regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 empty/reopen cursor freshness ve resync-anchor parity

Boş SQLite journal yeniden açıldığında cursor `()` kalıyor ve authoritative
snapshot kapısı korunuyor; boş başlangıçtan uygulanan anchor için cursor
çiftinden eski snapshot reddediliyor, taze snapshot ile `SYNCED` açılıyor.
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `66/66`, tam
checker `841/841 PASS`, compileall, workspace (`296` aktif Python dosyası) ve
diff PASS. Gerçek reconnect worker, REST catch-up, core/economic binding,
mutation ve mainnet yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`. Sıradaki tek güvenli iş
empty/reopen sonrası aynı cursor identity conflict ve snapshot gate parity
regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 restart terminal cursor freshness ve authoritative snapshot sınır parity

Restart ile hydrate edilen terminal cursor için anchor gözlem zamanı hem
transaction hem event zamanını kapsıyor; authoritative snapshot cursor
çiftinin en güncel bileşeninden eskiyse `SNAPSHOT_STALE` ile reddediliyor.
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak `1/1`, komşu `65/65`, tam
checker `840/840 PASS`, compileall, workspace (`296` aktif Python dosyası) ve
diff PASS. Gerçek reconnect worker, REST catch-up, core/economic binding,
mutation ve mainnet yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`. Sıradaki tek güvenli iş
empty/reopen cursor freshness ile resync-anchor parity regresyonudur.

## Önceki P2 durumu — 2026-09-19 P2.04 terminal replay conflict ve restart snapshot parity

İkinci açılışta terminal snapshot değişmeden kalıyor; terminal event exact
duplicate, aynı event kimliğinin farklı fingerprint’i `CONFLICT` ve
coordinator’da GAP oluyor. `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; odak
`1/1`, komşu `64/64`, tam checker `839/839 PASS`, compileall, workspace
(`296` aktif Python dosyası) ve diff PASS. Gerçek reconnect worker, REST
catch-up, core/economic binding, mutation ve mainnet yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`. Sıradaki tek güvenli iş
restart sonrası terminal cursor freshness ve authoritative snapshot sınır
parity regresyonudur.

## Önceki P2 durumu — 2026-09-18 P2.04 listStatus sequence/gap quarantine

P2.04 read-only User Data Stream `listStatus` için venue sequence
üretilmeden `(transaction_time_ms,event_time_ms)` cursor’ı non-decreasing
doğrulanıyor. Exact duplicate/no-op, event-ID fingerprint conflict ve
out-of-order `GAP` fail-closed; `RECONCILIATION_REQUIRED`, `STALE` ve `GAP`
durumlarında listStatus acceptance’ı quarantine ediliyor. Reconnect sonrası
explicit reconciliation olmadan acceptance yok. `IMPLEMENTED_WITH_LIMITATION /
LOCAL_PASS`; odak `37/37 PASS`, tam checker `812/812 PASS`, compileall,
workspace (`296` aktif Python dosyası) ve diff PASS. Bu dilim yalnız offline
in-memory sınırdır; REST catch-up, canlı reconnect, durable cursor hydration,
core/economic binding, mutation ve mainnet authority yok. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`. Sıradaki tek güvenli iş
explicit offline reconciliation anchor/resync contract’ıdır.

## Önceki P2 durumu — 2026-09-18 P2.04 listStatus journal

P2.04 read-only User Data Stream `listStatus` parser çıktısı ayrı
`USER_STREAM_LIST_STATUS` observation olarak bounded SQLite `OrderListEventStore`
sınırına bağlandı: `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Canonical JSON +
SHA-256 checksum, transaction-time monotonic sıra, restart replay, exact
duplicate/no-op, identity conflict ve out-of-order/terminal fail-closed
korunuyor. Parser’ın taşımadığı leg status/role/type, fiyat, miktar, fee veya
fill çıkarılmıyor ve observation ekonomik/core event’e yükseltilmiyor. Odak
`25/25 PASS`; tam checker `810` testte `808 PASS`, iki Windows Credential
Manager ortam hatası (`1312`, `CREDENTIAL_NOT_FOUND`) kaldı. Compileall,
workspace (`296` aktif Python dosyası) ve diff check PASS. Kanıt:
`evidence/P2.04/LIVE_READ_ONLY_GATE_SONUC.md`.

Bu dilim canlı event tüketimi, reconnect/catch-up, mutation veya mainnet
readiness kanıtı değildir. Sıradaki tek güvenli iş read-only stream
sequence/gap quarantine ve reconnect/catch-up sınırının offline
doğrulanmasıdır.

P2.03 durable venue-event journal ve cancel-replace observation sequencing
dilimi `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` olarak doğrulandı. Exact
OCO/leg reconciliation sonucu ve cancel-replace identity gözlemleri bounded
SQLite journal’a canonical JSON + SHA-256 checksum ile bağlanıyor; monotonic
sequence, restart replay, exact duplicate/no-op, conflict,
out-of-order/terminal fail-closed ve atomic rollback korunuyor. Bu dilim
fill/core posting, economic state, signed transport ve mutation authority
içermez. Odak `18/18 PASS`; tam checker `806` testte `804 PASS`, iki Windows
Credential Manager ortam hatası (`1312`, `CREDENTIAL_NOT_FOUND`) kaldı.
Compileall, workspace (`296` aktif Python dosyası) ve diff check PASS. Kanıt:
`evidence/P2.03/MARKET_CONDITIONAL_ORDER_LIST_CONTRACT_SONUC.md`.

Sıradaki tek güvenli iş read-only User Data Stream order-list event
parser/adapter contract kapısıdır.

P2.03 venue event reconciliation ve cancel-replace identity dilimi de
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` olarak doğrulandı. OCO venue event’i
exact liste + leg kimliğiyle redacted evidence’a bağlanıyor; liste veya bacak
kimliği uyuşmazlığı `CONFLICT`. Cancel-replace sonuçları immutable prior ve
replacement identity’leriyle sınıflandırılıyor; belirsiz/eksik sonuç `UNKNOWN`,
cancel reddedilip yeni emir kabul edildiğinde yeniden reconciliation gerekiyor.
Bu dilim fill/core posting, economic state, signed transport ve mutation
authority içermez. Odak `5/5 PASS`; tam checker `801` testte `799 PASS`, iki
Windows Credential Manager ortam hatası (`1312`, `CREDENTIAL_NOT_FOUND`) kaldı.
Compileall, workspace ve diff check PASS. Kanıt:
`evidence/P2.03/MARKET_CONDITIONAL_ORDER_LIST_CONTRACT_SONUC.md`.

P2.03 SQLite durable replay owner `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`
durumundadır. `OrderListStore`, identity ve bounded observation journal’ını
canonical JSON + SHA-256 checksum ile saklıyor; append transaction’ı,
exact duplicate/conflict, ordered replay, restart recovery ve rollback birlikte
korunuyor. Fill/core binding, signed transport ve mutation acceptance hâlâ
ayrı kapılardır; production readiness `NO`.

## 2026-09-18 P1.16.a Chronological split sınırı

P1.16.a `COMPLETE_WITH_LIMITATION / LOCAL_PASS` olarak kapandı. Public
`ChronologicalSplit` kurucusu bölüm sırası, gap/test sınırı, duplicate sample
identity ve yanlış point tipi bypass’larını fail-closed reddediyor;
`ChronologicalPoint` exact string ve non-negative integer event-time sınırını
koruyor. Odak `7/7 PASS`, bağımsız chronological oracle `PASS`, Noether
salt-okunur Codex review `PASS_WITH_LIMITATION` (P1/P2 bulgu yok),
compile/diff `PASS`. Python `3.13` gereksinimi nedeniyle bu oturumda
`tools/run_checks.py` ve `tools/check_workspace.py` çalışmadı; bundled
`3.12.14`, `active_python_files: 286`, güncel tam-suite/workspace sonucu
iddia edilmiyor. Gap yalnız yapısal ayrımdır; purge/embargo, OOS freeze,
feature/label leakage, persistence, API/UI ve ekonomik hesap açılmadı.
Production readiness `NO`. Kanıt: `evidence/P1.16.a/SONUC.md`.

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
leakage, persistence, API/UI ve ekonomik hesap açılmadı. Production readiness
`NO`. Kanıt: `evidence/P1.16.b/SONUC.md`.

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
persistence, API/UI ve ekonomik hesap açılmadı. Production readiness `NO`.
Kanıt: `evidence/P1.16.c/SONUC.md`.

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
production readiness `NO`. Resmî warm-up kaynakları state hazırlığı ile
trade authority’sini ayırıyor; local source audit’te gerçek
feature/indicator/label adapterı ve historical runner binding bulunmadı.
Bağımsız stdlib warmup/lookahead oracle `PASS`. Yeni numeric warmup,
indicator/signal authority veya ekonomik fill üretimi açılmadı. Kanıt:
`evidence/P1.16.f/SONUC.md`.

Sıradaki tek güvenli iş `P1.16.g` local feature/label horizon ve gerçek run
binding karar kapısıdır.

## 2026-09-18 P1.16.g Local feature/label horizon ve gerçek run binding

P1.16.g `COMPLETE_WITH_LIMITATION / LOCAL_PASS` olarak kapatıldı; production
readiness `NO`. Bounded exact `CLOSE_SMA`, `CLOSE_RETURN` ve
`FUTURE_CLOSE_RETURN` pipeline’ı closed-bar, chronology, lookback/horizon ve
1.000 bar limitiyle fail-closed uygulandı. Binding run planına, historical
reducer’a ve capture identity’sine bağlandı; warmup barlarında action üretilmiyor
ve tam binding reducer başlamadan yeniden doğrulanıyor. Kanıt:
`evidence/P1.16.g/SONUC.md`.

Numeric purge/embargo, ekonomik KPI/OOS, optimizer, stress model, persistence
schema, API/UI opt-in profili ve canlı venue davranışı ayrı P1.16.i kapısıdır.

Sıradaki tek güvenli iş `P1.16.i` stress ekonomik modeli ve gerçek senaryo
runner karar kapısıdır.

## 2026-09-18 P1.15.c Two-leg persistence/replay/recovery karar kapısı

P1.15.c `DEFERRED / NO-GO / LOCAL_PASS` olarak yeniden doğrulandı.
`LifecycleStore` `NON_ECONOMIC_LIFECYCLE_ONLY` kapsamını koruyor ve lifecycle
şeması hedge leg/side, quantity, effective-time veya recovery alanlarını
taşımıyor. Generic `Store` event/posting batch, hash ve `execution_id` dedup
sağlıyor; two-leg identity/state, model lineage ve iki store arasında atomic
binding yok. P1.15.b in-memory projection’ını bağlayan adapter bulunmadı.
Persistence sınır regresyonu `30/30 PASS`, bağımsız storage schema control ve
Beauvoir salt-okunur Codex review kararı doğruladı; compile/diff `PASS`.
Python `3.13` gereksinimi nedeniyle tam-suite/workspace checker çalışmadı.
Test matrisi mevcut ancak `SPECIFIED_NOT_EXECUTED_AGAINST_LOCAL_CODE`;
production readiness `NO`. Kanıt: `evidence/P1.15.c/SONUC.md`.

Sıradaki tek güvenli iş `P1.16.a` chronological split ve leakage-free
evaluation karar kapısıdır.

## 2026-09-18 P1.15.b Accepted two-leg fill projection

P1.15.b `COMPLETE_WITH_LIMITATION / LOCAL_PASS` olarak kapandı. Public
projection constructor’ı state, identity pair, fill history, exact aggregate
ve status tutarlılığını yeniden doğruluyor; aynı side/scope, tamamlanmış leg
history ve custom equality whitelist bypass’ları fail-closed. Odak `7/7 PASS`,
ilgili hedge projection kümesi `11/11 PASS`, bağımsız accepted-fill/
malformed-constructor oracle `PASS`, Bohr salt-okunur Codex review düzeltme
sonrası `PASS`, compile/diff `PASS`. `tools/run_checks.py` ve
`tools/check_workspace.py` Python `3.13` gereksinimi nedeniyle bu oturumda
tam-suite/workspace sonucu veremedi. Production readiness `NO`; persistence/
replay/recovery, order/reserve/fill posting, cross/margin/liquidation, API/UI
ve venue authority açılmadı. Kanıt: `evidence/P1.15.b/SONUC.md`.

Sıradaki tek güvenli iş `P1.15.c` two-leg persistence/replay/recovery karar
kapısıdır.

## 2026-09-18 P1.15.a Hedge identity ve two-leg state sınırı

P1.15.a mevcut checkout üzerinde doğrulandı: `COMPLETE_WITH_LIMITATION /
LOCAL_PASS`; unhashable/wrong-type state için explicit string guard eklendi,
ham `TypeError` fail-closed `TWO_LEG_STATE_INVALID` olarak düzeltildi. Odak
`4/4 PASS`, ilgili two-leg projection kümesi `8/8 PASS`, bağımsız hedge/
two-leg oracle `PASS`, Herschel salt-okunur Codex review düzeltme sonrası
`PASS`, kritik P1 bulgu yok; compile/diff `PASS`.

Bu oturumda proje Python `3.13` gerektirirken kullanılabilir bundled runtime
`3.12.14` olduğu için `tools/run_checks.py` tam-suite başlatılamadı; güncel
tam-suite sonucu iddia edilmiyor. Production readiness `NO`; identity/state
boundary order/reserve/fill posting, persistence, recovery, cross/margin/
liquidation, API/UI veya venue authority açmaz. Kanıt:
`evidence/P1.15.a/SONUC.md`.

Sıradaki tek güvenli iş `P1.15.b` accepted two-leg fill projection karar
kapısıdır.

## 2026-09-18 P1.14.f Template activation ve capability gate

P1.14.f mevcut checkout üzerinde doğrulandı: `COMPLETE_WITH_LIMITATION /
LOCAL_PASS`; odak `4/4 PASS`, ilgili template/projection kümesi `10/10 PASS`,
bağımsız activation oracle `PASS`, Singer salt-okunur Codex review `PASS`,
kritik P1/P2 bulgu yok. `PENDING`/`APPROVED`, unsupported capability
precedence, duplicate/bool allowlist ve non-authority sınırları doğrulandı;
compile/diff `PASS`.

Bu oturumda proje Python `3.13` gerektirirken kullanılabilir bundled runtime
`3.12.14` olduğu için `tools/run_checks.py` tam-suite başlatılamadı; güncel
tam-suite sonucu iddia edilmiyor. Production readiness `NO`; gate activation,
candidate/order/reserve/fill, persistence, API/UI veya venue authority açmaz.
Kanıt: `evidence/P1.14.f/SONUC.md`.

Sıradaki tek güvenli iş `P1.15.a` hedge/cross/two-leg kapsam karar kapısıdır.

## 2026-09-18 P1.14.e Strategy template integrity ve non-authority

P1.14.e mevcut checkout üzerinde doğrulandı: `COMPLETE_WITH_LIMITATION /
LOCAL_PASS`; public constructor duplicate capability bypass’ı kırmızı testle
doğrulanıp `__post_init__` fail-closed guard’ıyla düzeltildi. Odak `6/6 PASS`,
ilgili projection kümesi `14/14 PASS`, bağımsız canonical/hash/non-authority
oracle `PASS`, Turing salt-okunur Codex review düzeltme sonrası `PASS`, kritik
P1/P2 bulgu yok; compile/diff `PASS`.

Bu oturumda proje Python `3.13` gerektirirken kullanılabilir bundled runtime
`3.12.14` olduğu için `tools/run_checks.py` tam-suite başlatılamadı; güncel
tam-suite sonucu iddia edilmiyor. Production readiness `NO`; template inert
artifact olarak kalır ve activation/candidate/order/reserve/fill, persistence,
API/UI veya venue authority açmaz. Kanıt: `evidence/P1.14.e/SONUC.md`.

Sıradaki tek güvenli iş `P1.14.f` template activation/capability gate karar
kapısıdır.

## 2026-09-18 P1.14.d Rebalancing threshold/time trigger projection

P1.14.d mevcut checkout üzerinde doğrulandı: `COMPLETE_WITH_LIMITATION /
LOCAL_PASS`; odak `8/8 PASS`, ilgili projection kümesi `14/14 PASS`, bağımsız
Decimal/time oracle `PASS`, Mendel salt-okunur Codex review `PASS`, kritik
`BLOCKED` bulgu yok. NaN/Infinity/exponent/malformed decimal, threshold=0,
signed zero, aynı timestamp ve tüm bool zaman girdileri regresyon kapsamına
alındı; compile/diff `PASS`.

Bu oturumda proje Python `3.13` gerektirirken kullanılabilir bundled runtime
`3.12.14` olduğu için `tools/run_checks.py` tam-suite başlatılamadı; güncel
tam-suite sonucu iddia edilmiyor. Production readiness `NO`; trigger
projection order/candidate/fill, persistence, API/UI veya venue authority
açmaz. Kanıt: `evidence/P1.14.d/SONUC.md`.

Sıradaki tek güvenli iş `P1.14.e` template integrity ve non-authority karar
kapısıdır.

## 2026-09-18 P1.14.c Signal warmup, closed-bar ve stale readiness kapısı

P1.14.c mevcut checkout üzerinde doğrulandı: `COMPLETE_WITH_LIMITATION /
LOCAL_PASS`; odak `6/6 PASS`, ilgili readiness kümesi `12/12 PASS`, bağımsız
readiness oracle `PASS`, Locke salt-okunur Codex review `PASS`, kritik
`BLOCKED` bulgu yok. Stale boundary ve tüm bool gate tipleri için regresyon
kapsamı eklendi; compile/diff `PASS`.

Bu oturumda proje Python `3.13` gerektirirken kullanılabilir bundled runtime
`3.12.14` olduğu için `tools/run_checks.py` tam-suite başlatılamadı; güncel
tam-suite sonucu iddia edilmiyor. Production readiness `NO`; readiness
projection candidate/order/fill, adapter, trigger, persistence, API/UI ve
venue authority açmaz. Kanıt: `evidence/P1.14.c/SONUC.md`.

Sıradaki tek güvenli iş `P1.14.d` threshold/time rebalancing trigger karar
kapısıdır.

## 2026-09-18 P1.14.b Signal identity, event-time ve dedupe doğrulaması

P1.14.b mevcut checkout üzerinde doğrulandı: bağımsız review’da bulunan
duplicate-history açığı fail-closed guard ve regresyon testiyle düzeltildi;
odak `6/6 PASS`, readiness ile ilgili küme `11/11 PASS`, ayrı signal oracle
`PASS`, Ptolemy salt-okunur Codex review düzeltme sonrası `PASS`, kritik
`BLOCKED` bulgu yok; compile/diff `PASS`. Faz
`COMPLETE_WITH_LIMITATION / LOCAL_PASS` durumundadır.

Bu oturumda proje Python `3.13` gerektirirken kullanılabilir bundled runtime
`3.12.14` olduğu için `tools/run_checks.py` tam-suite başlatılamadı; güncel
tam-suite sonucu iddia edilmiyor. Production readiness `NO`; candidate/order/
fill, auth/replay window, warmup/closed-bar, persistence, API/UI ve venue
authority kapsam dışıdır. Kanıt: `evidence/P1.14.b/SONUC.md`.

## 2026-09-17 P1.13.h.d Reverse/Infinity boundary bağımsız inceleme ve kritik regresyon kapısı

Erdos’un salt-okunur Codex incelemesi h.a–h.c varyant sınırını `PASS` olarak
doğruladı; kritik BLOCKED bulgu bulunmadı. Literal boundary oracle `3/3`,
h.a+h.c gate kümesi `6/6`, hedefli sınır kümesi `9/9`, geniş doğrulama kümesi
`53/53 PASS`; compile/diff PASS.

Exact source/oracle yokluğu sürdüğü için vendor implementation
`DEFERRED / NO-GO`; ürün availability `NOT_SUPPORTED`, admission `BLOCKED`,
order/economic authority `NONE`. Kanıt:
`evidence/P1.13.h.d/SONUC.md`.

Sıradaki tek güvenli iş `P1.14.c` signal warmup/closed-bar ve stale-policy
karar kapısıdır;
P1.13.h exact source/oracle gelirse yeniden açılacaktır.

## 2026-09-18 P1.14.a Rebalancing exact target/delta projection doğrulaması

P1.14.a mevcut checkout üzerinde yeniden doğrulandı: odak `6/6 PASS`, ayrı
Decimal oracle `PASS`, Erdos salt-okunur Codex review `PASS`, kritik `BLOCKED`
bulgu yok; compile/diff `PASS`. Faz
`COMPLETE_WITH_LIMITATION / LOCAL_PASS` durumundadır.

Bu oturumda proje Python `3.13` gerektirirken kullanılabilir bundled runtime
`3.12.14` olduğu için `tools/run_checks.py` tam-suite başlatılamadı; güncel
tam-suite sonucu iddia edilmiyor. Production readiness `NO`; order/reserve/fill,
fee/rounding, conversion, balance, persistence, signal/template, API/UI ve
venue authority kapsam dışıdır. Kanıt:
`evidence/P1.14.a/SONUC.md`.

## 2026-09-17 P1.13.h.c Reverse/Infinity `NOT_SUPPORTED` admission sınırı

H.a typed fail-closed gate’i ürün admission katmanına bağlandı. Exact
source/oracle yokken iki varyant da `availability=NOT_SUPPORTED` ve
`admission=BLOCKED`; order/economic authority `NONE` olarak kalır. Reverse
Futures short değildir; Infinity generic Futures Grid fallback’i değildir.

Alt faz `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, vendor implementation
`DEFERRED / NO-GO`. Yeni odak `3/3 PASS`, h.a+h.c `6/6 PASS`, ilgili doğrulama
kümesi `50/50 PASS`, compile/diff PASS. Kanıt:
`evidence/P1.13.h.c/SONUC.md`.

Sıradaki tek güvenli iş `P1.13.h.d` h.a–h.c boundary’si için bağımsız inceleme
ve kritik regresyon kapısıdır; exact source/oracle olmadan order veya ekonomik
uygulama açılmaz.

## 2026-09-17 P1.13.h.b Reverse/Infinity Futures Grid araştırma karşı-auditi

Ürün araştırması ile primary-source lifecycle audit’i karşılaştırıldı. Reverse
Grid’in ayrı spot ürün olduğu ve Futures short olmadığı doğrulandı. Infinity
Grid’in sabit üst limit olmaması inventory, sermaye, lower-bound veya fill
garantisi değildir. Exact range transition, reserve, replacement/late-fill
identity ve deterministic replay sözleşmeleri doğrulanmadı.

Alt faz `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED`, vendor implementation
`DEFERRED / NO-GO`; h.a `BLOCKED_CONTRACT_REQUIRED` ve order/economic authority
`NONE` olarak korunuyor. Odak h.a ilgili kümesi `24/24 PASS`, compile/diff
PASS. Kanıt: `evidence/P1.13.h.b/SONUC.md`.

Sıradaki tek güvenli iş `P1.13.h.c` local `NOT_SUPPORTED`/admission sınırıdır;
exact source/oracle olmadan order veya ekonomik davranış açılmaz.

## 2026-09-17 P1.13.h.a Reverse/Infinity Futures Grid varyant güvenlik kapısı

Reverse ve Infinity ayrı typed varyantlar olarak sınıflandırıldı. Exact
contract/oracle olmadan ikisi `BLOCKED_CONTRACT_REQUIRED`, order/economic
authority `NONE` ve vendor implementation `DEFERRED / NO-GO` kalır. Reverse
Futures short değildir; Infinity upper-limit yokluğu inventory/sermaye veya
fill garantisi değildir. Odak `3/3 PASS`; g.a–g.c, g.f–g.h ve h.a ilgili küme
`24/24 PASS`, compile/diff PASS. Order, replacement, reserve, persistence,
API/UI veya Binance/Testnet mutation yoktur. Kanıt:
`evidence/P1.13.h.a/SONUC.md`.

Sıradaki tek güvenli iş `P1.13.h.b` exact Reverse/Infinity sözleşmeleri için
araştırma karşı-auditidir.

## 2026-09-17 P1.13.g.h Futures Grid offline lifecycle bağımsız oracle ve regresyon kapısı

g.g local reducer’ı literal transition matrisi, conflict identity, invalid
sequence ve deterministic replay regresyonlarıyla doğrulandı. Alt faz
`COMPLETE_WITH_LIMITATION / LOCAL_PASS`, local oracle `ORACLE_PASS`,
vendor lifecycle implementation `DEFERRED / NO-GO`. Odak `4/4 PASS`; g.a–g.c,
g.f–g.h ilgili küme `21/21 PASS`; compile/diff PASS. Yalnız local in-memory
state kullanılır; order/fill/replacement, reserve, economic posting,
persistence, API/UI veya Binance/Testnet mutation yoktur. Kanıt:
`evidence/P1.13.g.h/SONUC.md`.

Sıradaki tek güvenli iş `P1.13.h` Reverse/Infinity varyantları için ayrı
karar/kaynak kapısıdır.

## 2026-09-17 P1.13.g.g Futures Grid offline lifecycle transition simülasyonu

g.f yerel politika kontratı immutable in-memory transition simülasyonuna
bağlandı: cancel request/ack sırası, fill’in cancel yarışındaki önceliği,
replacement ack sınırı, exact duplicate fill idempotency, unknown/conflict
quarantine ve deterministic replay doğrulandı.

Alt faz `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, local simulation
`CONTRACT_READY`, vendor lifecycle implementation `DEFERRED / NO-GO`.
`FILL_ACCEPTED` local observation’dır; order/replacement, reserve, economic
posting, persistence, API/UI veya venue authority yoktur. Kapsam
`DCABOT_OFFLINE_SIMULATION_ONLY`; odak `5/5 PASS`, g.a–g.c `10/10 PASS`, g.f
`2/2 PASS`, compile/diff PASS. Kanıt: `evidence/P1.13.g.g/SONUC.md`.

Sıradaki tek güvenli iş local event matrix için bağımsız oracle ve
conflict/replay regresyon kapısıdır; vendor parity ve gerçek venue davranışı
açılmayacaktır.

## 2026-09-17 P1.13.g.f DCABOT yerel Futures Grid lifecycle politika sözleşmesi

Vendor-eşdeğerliği iddia etmeyen DCABOT offline politika kontratı typed
immutable değer olarak kayda alındı: fill cancel yarışında öncelikli,
replacement cancel ack sonrasına bağlı, reserve terminal exchange event
gözlemine bağlı, exact duplicate trade yok sayılır, unknown/conflict
quarantine/fail-closed ve replay deterministic olmalıdır.

Alt faz `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; yerel kontrat
`CONTRACT_DECLARED`; vendor lifecycle implementation `DEFERRED / NO-GO`.
Authority alanları `NONE`, kapsam `DCABOT_OFFLINE_SIMULATION_ONLY`; order,
economic state, persistence, API/UI veya Binance/Testnet mutation yok. Odak
`2/2 PASS`; g.a–g.c gate kümesi `10/10 PASS`, g.d/g.e araştırma kontrolleri
ayrı ayrı `3/3 PASS`, compile/diff PASS. Kanıt:
`evidence/P1.13.g.f/SONUC.md`.

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
`docs/archive/arastirma-promptlari/P1.13_FUTURES_GRID_LIFECYCLE_PRIMARY_SOURCE_AUDIT.md`, kanıt
`evidence/P1.13.g.d/SONUC.md`.

P1.13.g.c’nin `BLOCKED_CONTRACT_REQUIRED` ve `order_authority=NONE` sınırı
korunuyor; order/replacement, reserve, state/economic mutation,
persistence, API/UI ve Binance/Testnet mutation açılmadı. Checkout karşı
kontrolü ve odak `3/3 PASS`, compile/workspace/diff PASS; tam son doğrulama
`749` testte `747 PASS`, Windows Credential Manager `1312` nedeniyle `2`
environment error. Production readiness `NO`.

## 2026-09-17 P1.13.g.c Futures Grid replacement/replay ve late-fill identity karar kapısı

`RANGE_REVISION`, `CANCEL_REPLACE`, `LATE_FILL` ve `REPLAY` typed yaşam
döngüsü sınırları olarak ayrıldı. Exact range transition, replacement identity,
pending/reserve lifecycle, late-fill authority ve deterministic replay oracle
gereksinimleri doğrulanana kadar her sınır `BLOCKED_CONTRACT_REQUIRED` ve
`order_authority=NONE` kalıyor. Order/replacement ID, candidate level, state
mutation, persistence, API/UI ve Binance/Testnet mutation açılmadı. Odak `3/3
PASS`; ilişkili grid kümesi `55/55 PASS`; tam suite `749` testte `747 PASS`,
Windows Credential Manager `Windows error 1312` nedeniyle `2` environment error.
Bağımsız review `NOT_RUN`, production readiness `NO`; durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
`evidence/P1.13.g.c/SONUC.md`.

Ana P1.13.g `IN_PROGRESS / IMPLEMENTATION_PENDING`; kalan advanced davranışlar
exact source/oracle kanıtı olmadan `CONTRACT_REQUIRED`.

## 2026-09-17 P1.13.g.a Futures Grid dynamic order placement boundary

`STATIC` + `FIXED` placement yalnız daha önce exact üretilmiş seviyeleri inert
candidate listesi olarak döndürüyor. `DYNAMIC` placement ve `RANGE_REVISION`,
exact current-price selection, range transition, reserve, cancel/replace
identity ve replay sözleşmesi doğrulanana kadar `BLOCKED_CONTRACT_REQUIRED`.
`order_authority=NONE`; order ID, request, mutation, accepted fill ve
persistence açılmadı. Odak `4/4 PASS`; P1.13.a–d, f.a–f.d ve g.a ilişkili
küme `49/49 PASS`; tam suite `743` testte `741 PASS`, Windows Credential
Manager `Windows error 1312` nedeniyle `2` environment error. Bağımsız review
`NOT_RUN`, production readiness `NO`; durum `IMPLEMENTED_WITH_LIMITATION /
LOCAL_PASS`. Kanıt: `evidence/P1.13.g.a/SONUC.md`.

Ana P1.13.g `IN_PROGRESS / IMPLEMENTATION_PENDING`; `P1.13.g.b` advanced
variant ve `P1.13.g.c` replacement/replay-late-fill identity karar kapıları
kapatıldı. Kalan advanced davranışlar exact source/oracle kanıtı olmadan
`CONTRACT_REQUIRED`.

## 2026-09-17 P1.13.f.d Futures Grid funding/mark/P&L projection

Accepted Futures Grid fill’lerinden realized gross P&L, caller-supplied
reference mark ile unrealized P&L ve signed funding cashflow ayrı projection
olarak üretiliyor. `matched_cycle_profit` açık inventory’yi dışarıda bırakıyor;
`total_pnl` mark hareketini ekliyor. Event identity/asset/time/snapshot
sınırları fail-closed. `total_equity`, venue mark/funding authority, fee
conversion, maintenance margin, liquidation, reserve mutation, persistence,
API/UI ve Binance/Testnet mutation yok. Odak `5/5 PASS`; P1.13.a–d, f.a–f.d
ilişkili küme `45/45 PASS`; tam suite `739` testte `737 PASS`, Windows
Credential Manager `Windows error 1312` nedeniyle `2` environment error.
Bağımsız review `NOT_RUN`, production readiness `NO`; durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
`evidence/P1.13.f.d/SONUC.md`.

Ana P1.13.f `IN_PROGRESS / IMPLEMENTATION_PENDING`; P1.13.g.a ile dynamic
order placement ve grid range/trailing ayrımı kapatıldı.

## 2026-09-17 P1.13.f.c Futures Grid isolated margin/leverage and reserve projection

P1.13.f.b position state üzerinden caller-supplied exact `contract_size` ve
`reference_price` ile notional ve isolated initial-margin projection
uygulanıyor. Leverage yalnızca `notional / leverage` için kullanılıyor;
available margin yoksa kapasite `UNVERIFIED`, verilirse yalnız local
`ELIGIBLE`/`INSUFFICIENT_AVAILABLE_MARGIN` sonucu üretiliyor. Contract-size `1`
varsayımı, venue balance/reservation authority, maintenance margin, fee,
funding, mark/liquidation, P&L, persistence, API/UI ve Binance/Testnet
mutation yok. Non-terminating sonuç rounding olmadan fail-closed. Odak `6/6
PASS`; P1.13.a–d, f.a, f.b ve f.c ilişkili küme `40/40 PASS`; tam suite `734`
testte `732 PASS`, Windows Credential Manager `Windows error 1312` nedeniyle
`2` environment error. Bağımsız review `NOT_RUN`, production readiness `NO`;
durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
`evidence/P1.13.f.c/SONUC.md`.

Ana P1.13.f `IN_PROGRESS / IMPLEMENTATION_PENDING`; P1.13.f.d ile
funding/mark/liquidation ve grid profit/total-P&L projection kapatıldı.

## 2026-09-17 P1.13.f.b Futures Grid one-way position and accepted-fill state

Selected one-way/isolated Futures profile içinde yalnız FLAT başlangıçtan
gelen LONG/SHORT position projection uygulanıyor. Accepted fill quantity ve
weighted average-entry exact immutable in-memory state’e yazılıyor; overflow,
ters flat açılış, flip, duplicate conflict ve geç event zamanı fail-closed.
Odak `9/9 PASS`; P1.13.a–d, f.a ve f.b ilişkili küme `34/34 PASS`; tam suite
`728` testte `726 PASS`, Windows Credential Manager `Windows error 1312`
nedeniyle `2` environment error. Bağımsız review `NOT_RUN`, production
readiness `NO`; durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Neutral,
non-flat initial, P&L, margin/leverage effect, funding/liquidation,
order/replacement, persistence, API/UI ve Binance/Testnet mutation yok. Kanıt:
`evidence/P1.13.f.b/SONUC.md`.

Ana P1.13.f `IN_PROGRESS / IMPLEMENTATION_PENDING`; P1.13.f.c ile isolated
margin/leverage ve reserve projection kapatıldı.

## 2026-09-17 P1.13.f.a Futures Grid v1 profile-bound exact level projection

Spot Grid’den ayrı seçilmiş Futures profile (`BINANCE/USD_M/USDT/PERPETUAL`,
`ONE_WAY`, `ISOLATED`) ve explicit leverage alanı tanımlandı. LONG/SHORT/
NEUTRAL direction taşınıyor; initial-position policy yalnız FLAT. Arithmetic ve
geometric level projection exact ve tick/origin fail-closed. Odak `7/7 PASS`,
P1.13.a–d ve f.a ilişkili küme `25/25 PASS`; tam suite `719` testte `717 PASS`,
Windows Credential Manager `Windows error 1312` nedeniyle `2` environment
error. Bağımsız review `NOT_RUN`, production readiness `NO`; durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Position/fill, margin/leverage
effect, funding/liquidation, P&L, order/replacement, persistence, API/UI ve
Binance/Testnet mutation yok. Kanıt: `evidence/P1.13.f.a/SONUC.md`.

Ana P1.13.f `IN_PROGRESS / IMPLEMENTATION_PENDING`; P1.13.f.b ile one-way
position/accepted-fill state projection kapatıldı.

## 2026-09-17 P1.13.e Grid trailing-up/down ve reverse/infinity karar kapısı

Trailing-up için yalnız gözlenen ürün davranışı doğrulandı; exact
range/version transition, pending/reserve yaşam döngüsü, cancel-replace
identity, late-fill, replay ve precision sahipliği doğrulanmadı. Reverse/infinity
exact semantics `NOT_VERIFIED / DEFER` durumunda. Kod değişikliği yok; son
doğrulanmış checkout baseline'ında `712` testte `710 PASS` ve Windows
Credential Manager `Windows error 1312` nedeniyle `2` environment error var.
Bağımsız review `NOT_RUN`, production readiness `NO`; durum
`DEFERRED / NO-GO / LOCAL_PASS`. Kanıt: `evidence/P1.13.e/SONUC.md`.

Sıradaki aktif kabul `P1.13.f` Futures Grid v1 için ayrı profile ve exact
projection karar kapısıdır.

## 2026-09-17 P1.13.d Spot Grid geometric precision/quantization

Geometric grid exact rational `N`-inci root ve explicit `price_tick`/
`tick_origin` ile sınırlandı. Perfect-root olmayan oran veya off-tick seviye
reddediliyor; otomatik rounding ve yaklaşık float/Decimal seviye yok.

Odak `9/9 PASS`; P1.13.a–d ilişkili küme `18/18 PASS`; tam proje `712` testte
`710 PASS`, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle
`2` environment error. Bağımsız literal oracle, compile, read-only source
surface, workspace ve `git diff --check` PASS. Fee, inventory/fill,
replacement, API/UI, persistence ve Binance/Testnet mutation yok. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; production readiness `NO`.
Kanıt: `evidence/P1.13.d/SONUC.md`.

P1.13.e trailing/replacement ve reverse/infinity semantics güvenli karar
kapısında `DEFERRED / NO-GO` bırakıldı. Sıradaki aktif kabul `P1.13.f`
Futures Grid v1 için ayrı profile ve exact projection karar kapısıdır.

## 2026-09-17 P1.13.c Spot Grid fee ve cycle/equity projection

İlk offline arithmetic Spot Grid profili yalnız quote-asset fee ve explicit
`EXACT_NO_ROUNDING` kabul ediyor. Accepted matched BUY/SELL cycle için net
cycle profit ile explicit mark-price total equity ayrı exact alanlardır;
base/third fee asset’i ve venue quantization fail-closed kalır.

Odak `5/5 PASS`; P1.13.a–c ilişkili küme `13/13 PASS`; tam proje `707` testte
`705 PASS`, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle
`2` environment error. Bağımsız Decimal oracle, compile, read-only source
surface, workspace ve `git diff --check` PASS. Persistence/Store,
reserve/replacement, API/UI ve Binance/Testnet mutation yok. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; production readiness `NO`.
Kanıt: `evidence/P1.13.c/SONUC.md`.

P1.13.d geometric precision/quantization tamamlandı; P1.13.e
trailing/replacement ve reverse/infinity semantics `DEFERRED / NO-GO` ayrı
kapı olarak kapatıldı. Sıradaki aktif kabul `P1.13.f` Futures Grid v1 için
ayrı profile ve exact projection karar kapısıdır.

## 2026-09-17 P1.12.g.a Futures DCA start-condition gate

`IMMEDIATE`, `CLOSED_CANDLE` ve mevcut `SignalReadiness` sonucuna bağlı
`SIGNAL` başlangıç koşulları source-time ile salt-okunur değerlendiriliyor.
Closed-bar/warmup/staleness sahipliği `SignalReadiness` içinde kaldı; hazır
olmayan signal fail-closed `BLOCKED`. Odak `20/20 PASS`; tam proje `634` testte
`632 PASS`, faz dışı Windows Credential Manager `Windows error 1312` nedeniyle
`2` environment error. Compile, AST/write-surface ve `git diff --check` PASS.
`order_authority=NONE`; lifecycle/order/fill/reserve/persistence veya
Binance/Testnet mutation yok. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.
Kanıt: evidence/P1.12.g.a/SONUC.md.

P1.12.g.b ile tamamlandı. Sıradaki aktif kabul: `P1.12.g.c` average-entry TP
ve split-TP miktar conservation projection contract’ı.

P1.12.g.c ile tamamlandı. P1.12.g.d ile fee-aware profile ve breakeven boundary
kararı kapatıldı. P1.12.g.e ile exit priority ve eşzamanlı trigger kararı
kapatıldı. P1.12.g.f ile selected exit-candidate ve kapasite contract’ı,
P1.12.g.g ile candidate identity ve late-fill ayrım contract’ı kapatıldı.
P1.12.g.h ile fee-aware `TAKE_PROFIT` exit-candidate ve exact quantization
boundary kapatıldı. P1.12.h.a ile durable recovery/replay readiness kapatıldı.
P1.12.h.b ile profile-bound recovery capability ve CORE01 admission boundary
kapatıldı. P1.12.h.c ile durable profile recovery snapshot ve stale-profile
quarantine, P1.12.h.d ile immutable profile-source provenance cross-check ve
publish/migration NO-GO gate kapatıldı. Sıradaki aktif kabul: `P1.13.c` Spot
Grid fee asset/rounding ve matched cycle profit-total equity ayrımının karar
kapısıdır.

## 2026-09-17 P1.12.g.h Futures DCA fee-aware exit-candidate ve quantization boundary

Explicit fee/funding profilinden çıkan exact fee-aware breakeven yalnız
`TAKE_PROFIT` exit adayına bağlanıyor. Profil eksikliği, settlement mismatch,
off-grid hedef ve over-close fail-closed; sessiz rounding yapılmıyor ve
STOP/Trailing trigger’ları breakeven adayı olarak kullanılmıyor. Sonuç
`order_authority=NONE` ile salt-okunur.

Odak `9/9 PASS`; tam proje `690` testte `688 PASS`, faz dışı Windows
Credential Manager `Windows error 1312` nedeniyle `2` environment error.
Bağımsız Fraction capacity oracle, compile, AST/write-surface ve diff PASS.
Gerçek order/fill, OCO/cancel-replace, reserve mutation, persistence ve
Binance/Testnet mutation yok. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.
Kanıt: `evidence/P1.12.g.h/SONUC.md`.

P1.12.h.a ile durable recovery/replay readiness sınırı kapatıldı. P1.12.h.b
ile profile-bound recovery capability ve CORE01 admission boundary, P1.12.h.c
ile durable profile recovery snapshot ve stale-profile quarantine, P1.12.h.d
ile immutable profile-source provenance cross-check kapatıldı. Sıradaki aktif
kabul: `P1.13.c` Spot Grid fee asset/rounding ve matched cycle profit-total
equity ayrımının karar kapısıdır.

## 2026-09-17 P1.12.h.a Futures DCA durable recovery/replay readiness gate

Mevcut greenfield journal v4; profile revision, journal event, reservation,
release transition, economic posting ve CORE01 replay receipt sahiplerini ayrı
tutuyor. Restart replay sequence, checksum ve link doğrulaması yapıyor; receipt
preflight eksik schema/unique constraint’i yazmadan `BLOCKED` döndürüyor.
Event + release + posting + receipt failure injection sonrasında kısmi state
bırakmıyor; exact duplicate idempotent, farklı payload/scope conflict olarak
fail-closed kalıyor. CORE01 economic admission hâlâ `BLOCKED`.

Odak readiness alt kümesi `39/39 PASS`; tam proje `690` testte `688 PASS`, faz
dışı Windows Credential Manager `Windows error 1312` nedeniyle `2` environment
error. Compile, independent restart oracle ve diff PASS. Binance/account/order
mutation ve mainnet yok. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.
Kanıt: `evidence/P1.12.h.a/SONUC.md`.

P1.12.h.b ile tamamlandı. P1.12.h.c ile durable profile recovery snapshot ve
stale-profile quarantine, P1.12.h.d ile immutable profile-source provenance
cross-check ve publish/migration NO-GO gate kapatıldı. Sıradaki aktif kabul:
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
`2` environment error. Compile, read-only byte-oracle ve diff PASS. CORE01
economic admission hâlâ `BLOCKED`, `order_authority=NONE`. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
`evidence/P1.12.h.b/SONUC.md`.

P1.12.h.c ile durable profile recovery snapshot ve stale-profile quarantine,
P1.12.h.d ile immutable profile-source provenance cross-check ve
publish/migration NO-GO gate kapatıldı. Sıradaki aktif kabul: `P1.13.c` Spot
Grid fee asset/rounding ve matched cycle profit-total equity ayrımının karar
kapısıdır.

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
cross-check ve publish/migration NO-GO gate kapatıldı. Sıradaki aktif kabul:
`P1.13.c` Spot Grid fee asset/rounding ve matched cycle profit-total equity
ayrımının karar ve salt-okunur projection kapısıdır.

## 2026-09-17 P1.12.h.d Futures DCA recovery snapshot provenance ve publish/migration gate

Recovery snapshot ile immutable profile-source provenance target’ı ve canonical
migration manifest salt-okunur karşılaştırılır. Recovery/provenance profile
revision eşleşmesi, tekil `ACCEPTED` source snapshot, manifest hash ve reopened
target oracle’ı birlikte doğrulanır. Stale snapshot, profile mismatch,
eksik/bozuk provenance veya önceki gate/oracle başarısızlığı `NO_GO`; temiz
fixture sonucu yalnız `READY_FOR_REVIEW`, publish ve migration eylemleri
`BLOCKED` kalır.

Odak `4/4 PASS`; h.a–h.d ilişkili odak `51/51 PASS`; provenance/manifest/
reopen oracle kümesi `18/18 PASS`; tam proje `702` testte `700 PASS`, faz dışı
Windows Credential Manager `Windows error 1312` nedeniyle `2` environment
error. Compile, read-only source-surface ve `git diff --check` PASS. Gerçek
source export, migration/publish, CORE01 economic admission, order/fill
mutation ve Binance/Testnet mutation yok. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
`evidence/P1.12.h.d/SONUC.md`.

Sıradaki aktif kabul: `P1.13.c` Spot Grid fee asset/rounding ve matched cycle
profit-total equity ayrımının karar ve salt-okunur projection kapısıdır.

## 2026-09-17 P1.12.g.d Futures DCA fee-aware breakeven contract

Fee/funding profili olmadan yalnız gross average-entry boundary gösteriliyor;
üçüncü fee asset’i, settlement mismatch ve tick dışı fee-aware hedef fail-closed
kalıyor. Explicit settlement-notional modelinde LONG/SHORT ve signed funding
exact hesaplanıyor. Odak `9/9 PASS`; tam proje `656` testte `654 PASS`, faz dışı
Windows Credential Manager `Windows error 1312` nedeniyle `2` environment error.
Bağımsız Fraction oracle, compile ve AST/write-surface PASS. `order_authority=NONE`;
fee conversion/rounding, funding source/schedule, TP/SL/trailing execution,
OCO/cancel-replace, persistence ve Binance/Testnet mutation yok. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt: evidence/P1.12.g.d/SONUC.md.

P1.12.g.f ile tamamlandı. Sıradaki aktif kabul: `P1.12.g.g` candidate identity
ve late-fill/conditional execution ayrım contract’ıdır.

## 2026-09-17 P1.12.g.e Futures DCA exit priority contract

Aynı gözlemdeki trigger’lar `STOP_LOSS > TRAILING_STOP > TAKE_PROFIT >
BREAKEVEN_ADJUSTMENT` sırasıyla deterministik seçiliyor. Breakeven tek başına
stop adjustment, diğerleri close kararıdır; kapanış trigger’ı varsa breakeven
bastırılır. Input sırası sonucu değiştirmiyor, duplicate trigger fail-closed.
Odak `9/9 PASS`; tam proje `665` testte `663 PASS`, faz dışı Windows Credential
Manager `Windows error 1312` nedeniyle `2` environment error. Bağımsız alt-küme
oracle, compile ve AST/write-surface PASS. `order_authority=NONE`; exit
candidate/order/fill/OCO/cancel-replace/reserve, persistence ve Binance/Testnet
mutation yok. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
evidence/P1.12.g.e/SONUC.md.

P1.12.g.f ile seçilmiş trigger exact exit-candidate ve açık pozisyon kapasitesi
contract’ına bağlandı. Sıradaki aktif kabul: `P1.12.g.g` candidate identity ve
late-fill/conditional execution ayrım contract’ıdır.

## 2026-09-17 P1.12.g.f Futures DCA exit-candidate ve kapasite contract’ı

P1.12.g.e’nin seçtiği `CLOSE` trigger’ı exact tick-grid trigger fiyatı,
requested quantity ve gözlenmiş açık pozisyon kapasitesine salt-okunur aday
olarak bağlanıyor. `TAKE_PROFIT`, `STOP_LOSS` ve `TRAILING_STOP` adayları
kabul ediliyor; `BREAKEVEN_ADJUSTMENT` ve trigger yokluğu fail-closed. Accepted
fill, committed exit ve yeni aday toplamı exact kapasiteyi aşamıyor.

Odak `9/9 PASS`; tam proje `674` testte `672 PASS`, faz dışı Windows Credential
Manager `Windows error 1312` nedeniyle `2` environment error. Bağımsız Fraction
oracle, compile, AST/write-surface ve `git diff --check` PASS.
`order_authority=NONE`; gerçek order/fill, OCO/cancel-replace, reserve mutation,
persistence ve Binance/Testnet mutation yok. Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
`evidence/P1.12.g.f/SONUC.md`.

Sıradaki aktif kabul: `P1.12.g.g` candidate identity ve late-fill/conditional
execution ayrım contract’ıdır.

## 2026-09-17 P1.12.g.g Futures DCA candidate identity ve late-fill ayrım contract’ı

P1.12.g.f adayından deterministic SHA-256 snapshot identity üretiliyor;
identity trigger, fiyat, requested miktar, kalan kapasite, açık miktar ve
candidate gözlem zamanına bağlı. Late fill yalnız aynı identity’ye bağlı,
sıralı ve requested miktar sınırında salt-okunur observation olarak tutuluyor;
execution order identity veya economic posting üretmiyor.

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
profile-source provenance cross-check kapatıldı. Sıradaki aktif kabul:
`P1.13.c` Spot Grid fee asset/rounding ve matched cycle profit-total equity
ayrımının karar kapısıdır.

## 2026-09-17 P1.12.g.b Futures DCA max-DCA/stop/EXHAUSTED contract

Tüketilmemiş ladder için `CONTINUE`, ladder seviyeleri kalırken max-DCA
sınırında `STOP`, explicit dış stop nedenlerinde ayrı `STOP` ve full ladder’da
`EXHAUSTED` kararı salt-okunur değerlendiriliyor. `EXHAUSTED` yeni order veya
recovery talebi üretmiyor. Odak `19/19 PASS`; tam proje `640` testte `638 PASS`,
faz dışı Windows Credential Manager `Windows error 1312` nedeniyle `2`
environment error. Compile, AST/write-surface, bağımsız contract oracle ve
`git diff --check` PASS.
`order_authority=NONE`; lifecycle/order/fill/reserve/persistence veya
Binance/Testnet mutation yok. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.
Kanıt: evidence/P1.12.g.b/SONUC.md.

Sıradaki aktif kabul: `P1.12.g.c` average-entry TP ve split-TP miktar
conservation projection contract’ı.

## 2026-09-17 P1.12.g.c Futures DCA average-entry TP/split-TP projection

Observed fill projection average-entry’sinden LONG/SHORT yönüne göre exact TP
target hesaplanıyor; hedef tick grid dışında kalırsa sessiz quantization yapılmadan
fail-closed reddediliyor. Split TP miktarları açık pozisyonu aşamıyor, kalan miktar
exact dönüyor. Odak `18/18 PASS`; tam proje `647` testte `645 PASS`, faz dışı
Windows Credential Manager `Windows error 1312` nedeniyle `2` environment error.
Compile, AST/write-surface, bağımsız exact oracle ve `git diff --check` PASS.
`order_authority=NONE`; TP order/OCO/cancel-replace, fill, reserve, persistence veya
Binance/Testnet mutation yok. Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`.
Kanıt: evidence/P1.12.g.c/SONUC.md.

P1.12.g.d ile tamamlandı. P1.12.g.e ile exit priority kararı kapatıldı;
sıradaki aktif kabul `P1.12.g.f` seçilmiş trigger’ı exact exit-candidate ve
kapasite contract’ına bağlamaktır.

## 2026-09-17 P1.12.f.i.c immutable custom candidate acceptance-boundary

Custom candidate projection deterministik SHA-256 identity ile Futures DCA profili,
instrument filter metadata’sı, ladder seviyeleri ve post-quantization conservation’ı
kapsayan immutable acceptance snapshot’a bağlandı. Tamper/conflict fail-closed;
`order_authority=NONE`. Odak 20/20, ilişkili 55/55, tam proje 625/625 PASS,
compile/workspace ve `git diff --check` PASS (240 aktif Python dosyası). Durum
`IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`. Kanıt:
evidence/P1.12.f.i.c/SONUC.md.

P1.12.f.i.d ile tamamlandı. Sıradaki aktif kabul: P1.12.g DCA
start/stop/TP/trailing/breakeven lifecycle sözleşmesi.

## 2026-09-17 P1.12.f.i.d custom candidate offline sizing/pre-acceptance köprüsü

Quote-notional custom candidate acceptance mevcut offline sizing/pre-acceptance
kapısına salt-okunur bağlandı. İlk quantized seviye `SizingCandidate`, kalan
seviyeler `LadderBinding` olarak eligible quote budget’a karşı doğrulanıyor;
BASE_QTY için örtük quote bütçesi üretilmiyor ve fail-closed reddediliyor.
Odak 23/23, ilişkili sizing dahil 27/27 PASS; tam proje 626/628 PASS, faz dışı
Windows Credential Manager `Windows error 1312` nedeniyle iki environment error.
Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`. Kanıt:
evidence/P1.12.f.i.d/SONUC.md.

Sıradaki aktif kabul: P1.12.g DCA start/stop/TP/trailing/breakeven lifecycle
sözleşmesi.

## 2026-09-17 P1.12.f.i.b bağımsız candidate/oracle incelemesi ve kritik gate

P1.12.f.i.a candidate quantization sonuçları bağımsız Decimal oracle ile eşleşti;
AST/write-surface kontrolünde persistence/SQLite/HTTP mutation bulunmadı. Odak
17/17, ilişkili 52/52, tam proje 622/622 PASS, compile/workspace ve
`git diff --check` PASS (239 aktif Python dosyası). Durum
`IMPLEMENTED_WITH_LIMITATION / INDEPENDENT_REVIEW_PASS`. Kanıt:
evidence/P1.12.f.i.b/SONUC.md.

Sıradaki aktif kabul: P1.12.f.i.c immutable custom candidate
acceptance-boundary sözleşmesi.

## 2026-09-17 P1.12.f.i Pionex DIY per-safety-order deviation/allocation profile

Custom Futures DCA ladder her safety order için anchor’a göre cumulative
deviation, strict index/order ve explicit `BASE_QTY` veya `QUOTE_NOTIONAL`
allocation taşıyor; tick hizası ve exact budget conservation doğrulanıyor.
Bağımsız Decimal oracle dahil odak 5/5, ilişkili 43/43, tam proje 616/616
PASS, compile/workspace PASS (239 aktif Python dosyası). `SHARE` semantiği,
quantity-step/venue quantization, min-notional, persistence ve canlı mutation
açılmadı. Durum `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`. Kanıt:
evidence/P1.12.f.i/SONUC.md.

P1.12.f.i.a ile custom ladder allocation mevcut instrument filter profiline
bağlandı. BASE_QTY/QUOTE_NOTIONAL post-quantization actual allocation, quantity-step,
min-quantity ve min-notional ile doğrulanıyor; requested ve actual allocation ayrı
görünüyor. Odak 14/14, ilişkili 49/49, tam proje 619/619 PASS,
compile/workspace PASS (239 aktif Python dosyası). Durum
`IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`. Kanıt:
evidence/P1.12.f.i.a/SONUC.md.

P1.12.f.i.b bağımsız candidate/oracle incelemesi ve kritik gate ile tamamlandı.
P1.12.f.i.c immutable acceptance-boundary sözleşmesi ve P1.12.f.i.d offline
sizing/pre-acceptance köprüsü ile de tamamlandı. Sıradaki aktif kabul: P1.12.g
DCA start/stop/TP/trailing/breakeven lifecycle sözleşmesi.

## 2026-09-17 P1.12.f.h.av bağımsız replay integrity incelemesi ve kritik gate

P1.12.f.h.au read-only restart oracle bağımsız AST/write-surface kontrolünden
geçti; SQLite write/append çağrısı yok ve schema corruption fail-closed
`BLOCKED` oluyor. Odak 15/15, tam proje 611/611 PASS, compile/workspace PASS
(238 aktif Python dosyası), `git diff --check` hata vermedi. Durum
`IMPLEMENTED_WITH_LIMITATION / INDEPENDENT_REVIEW_PASS`; CORE01 durable owner,
venue/Binance mutation, mainnet, secret, migration ve publish yok. Kanıt:
evidence/P1.12.f.h.av/SONUC.md.

Sıradaki aktif kabul: P1.12.f.i Pionex DIY per-safety-order
deviation/allocation profilinin exact sözleşmesi ve bağımsız oracle kapısıydı;
h.i ile tamamlandı.

## 2026-09-17 P1.12.f.h.au durable replay integrity oracle

Read-only restart oracle durable event, economic posting, release history ve
reservation projection checksum/consistency kontrollerini kullanıyor; bozuk
durable veri fail-closed `BLOCKED` kalıyor. Pure duplicate ve retry
duplicate/conflict sınırları ile aynı scope farklı receipt fingerprint
conflict’i doğrulandı. Durable write, Binance/venue mutation, mainnet, secret,
migration ve publish yok. Odak 15/15, ilişkili 55/55, tam proje 611/611 PASS,
compile/workspace PASS (238 aktif Python dosyası). Durum
IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY. Kanıt:
evidence/P1.12.f.h.au/SONUC.md.

Sıradaki aktif kabul: P1.12.f.h.av read-only replay integrity oracle için
bağımsız inceleme ve kritik gate değerlendirmesiydi; h.av ile tamamlandı.

## 2026-09-17 P1.12.f.h.at read-only CORE01 replay projection oracle

Restart oracle durable accepted event, economic posting, release transition ve
receipt satırlarını read-only loader’larla doğruluyor; aynı immutable girdilerle
pure CORE01 replay decision/projection yeniden hesaplanıyor. Receipt
fingerprint/scope ile pure decision eşleşirse READY, receipt eksikliği veya
stale CORE01 admission BLOCKED. CORE01 durable owner, venue mutation, Binance ve
canlı emir yok. Odak 12/12, ilişkili 52/52 PASS, tam proje 608/608 PASS,
compile/workspace PASS (238 aktif Python dosyası). Durum
IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY. Kanıt:
evidence/P1.12.f.h.at/SONUC.md.

Sıradaki aktif kabul: P1.12.f.h.au durable reservation/posting/release
checksum ve duplicate/conflict sınırlarını genişleten read-only oracle kapısıydı;
h.au ile tamamlandı.

## 2026-09-17 P1.12.f.h.as atomic CORE01 replay receipt binding

Accepted Futures DCA fill event’i, release transition, economic posting ve
CORE01 replay receipt tek SQLite transaction’ında bağlandı. Dört kayıt birlikte
ACCEPTED veya DUPLICATE; receipt scope mismatch ve injected receipt failure
event/release/reservation/posting kayıtlarının tümünü rollback ediyor. Restart
load exact receipt bağlantılarını koruyor. Binance/Testnet mutation, mainnet,
secret, legacy migration/publish ve yeni economic authority yok. Odak 25/25,
ilişkili 49/49 PASS, tam proje 605/605 PASS, compile/workspace PASS (236
aktif Python dosyası). Durum IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY.
Kanıt: evidence/P1.12.f.h.as/SONUC.md.

Sıradaki aktif kabul: P1.12.f.h.at atomik receipt binding’in read-only CORE01
replay projection oracle’ıyla restart sonrası eşitliğini kanıtlamak.

## 2026-09-17 P1.12.f.h.ar durable CORE01 replay receipt append/load

Greenfield journal schema revision 4 içine core_replay_receipts owner tablosu,
fingerprint primary key ve mapping/event/posting/transition/release scope unique
contract’ı eklendi. Accepted event, posting, release transition ve reservation
projection linkleri append/load sırasında doğrulanıyor; exact duplicate
DUPLICATE, scope/fingerprint çakışması CONFLICT, restart replay exact receipt
döndürüyor. Eski schema migration’ı, venue ve canlı mutation yok. Receipt append
mevcut ekonomik kayıtların ardından ayrı transaction’dır. Odak 16/16,
ilişkili 46/46 PASS, tam proje 602/602 PASS, compile/workspace PASS (235
aktif Python dosyası). Durum IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY.
Kanıt: evidence/P1.12.f.h.ar/SONUC.md.

Sıradaki aktif kabul: P1.12.f.h.as receipt + event/release/posting bağını tek
transaction’da kuran atomik append/restart ve rollback kapısı.

## 2026-09-17 P1.12.f.h.aq durable CORE01 replay receipt Store preflight

Mevcut greenfield journal read-only incelendi; `core_replay_receipts` owner
tablosu ve fingerprint/scope unique contract’ı eksik olduğu için durable Store
`BLOCKED`. Fixture READY, malformed/eksik constraint RED; migration ve receipt
yazımı yok. Odak `3/3`, ilişkili `43/43 PASS`, tam proje `599/599 PASS`,
compile/workspace PASS (`235` aktif Python dosyası). Durum
`IMPLEMENTED_WITH_LIMITATION / NO_GO_CONFIRMED`. Kanıt:
`evidence/P1.12.f.h.aq/SONUC.md`.

Sıradaki aktif kabul: `P1.12.f.h.ar` greenfield schema revision/migration ve
exact append/load contract’ı.

## 2026-09-17 P1.12.f.h.ap offline replay idempotency contract

Accepted CORE01 + Futures DCA replay kararından bounded canonical fingerprint
ve frozen in-memory receipt üretildi. Aynı scope/fingerprint `DUPLICATE`,
same-scope değişiklik `CONFLICT`, farklı scope `BLOCKED`; economics yeniden
uygulanmıyor. Durable Store/journal/restart authority yok. Odak `17/17`,
ilişkili `68/68 PASS`, tam proje `596/596 PASS`, compile/workspace PASS
(`233` aktif Python dosyası). Durum `IMPLEMENTED_WITH_LIMITATION /
CONTRACT_READY`. Kanıt: `evidence/P1.12.f.h.ap/SONUC.md`.

Sıradaki aktif kabul: `P1.12.f.h.aq` receipt’in bounded durable Store/restart
sözleşmesi için karar kapısı.

## 2026-09-17 P1.12.f.h.ao offline CORE01 + Futures DCA replay decision

h.an CORE01 reducer projection’ı accepted Futures DCA event, projected posting
ve partial/full release transition ile salt-okunur replay kararında birleşiyor.
Identity, FILL türü, commitment/fee ve release consumed-delta exact; DUPLICATE
yeniden CORE01 economics üretmiyor. Kabul sonucu CORE state/reservation
projection ve posting kimliğini taşıyor; Store/journal/posting/venue mutation
yok. Odak `14/14`, ilişkili `65/65 PASS`, tam proje `593/593 PASS`,
compile/workspace PASS (`233` aktif Python dosyası). Durum
`IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`. Kanıt:
`evidence/P1.12.f.h.ao/SONUC.md`.

Sıradaki aktif kabul: `P1.12.f.h.ap` bounded idempotency/replay sözleşmesinin
durable Store’a yazmadan doğrulanması.

## 2026-09-17 P1.12.f.h.an offline CORE01 FILL reducer projection

h.am admission’ından gelen immutable CORE01 `FILL` tuple’ı kopya state üzerinde
reducer projection’a veriliyor. Position quantity, entry notional, fee ve order
filled/notional exact olarak doğrulanıyor; BLOCKED/bozuk tuple reducer’a
girmiyor. Store, journal, posting ve venue mutation yok. Odak `12/12`, ilişkili
`50/50 PASS`, tam proje `591/591 PASS`, compile/workspace PASS (`233` aktif
Python dosyası). Durum `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`. Kanıt:
`evidence/P1.12.f.h.an/SONUC.md`.

Sıradaki aktif kabul: `P1.12.f.h.ao` reducer projection’ının Futures DCA
posting/release replay kararına salt-okunur bağlanması.

## 2026-09-17 P1.12.f.h.am offline CORE01 economic FILL boundary admission

Explicit admitted mapping, accepted Futures DCA fill envelope ve projected
posting salt-okunur CORE01 FILL boundary’sinde doğrulanıyor. Exact identity,
commitment/fee/funding/profile, fee asset, `qty * price`, terminal/UNKNOWN,
overfill ve off-grid kontrolleri fail-closed; kabul yalnız immutable CORE01
FILL tuple önerisi üretir. Reducer, Store, persistence, posting veya venue
mutation yok. Odak `10/10`, ilişkili küme `48/48 PASS`, tam proje `589/589 PASS`,
compile/workspace PASS (`233` aktif Python dosyası). Durum
`IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`. Kanıt:
`evidence/P1.12.f.h.am/SONUC.md`.

Sıradaki aktif kabul: `P1.12.f.h.an` immutable CORE01 FILL tuple’ının kopya
state üzerinde exact reducer projection’ı.

## 2026-09-17 P1.12.f.h.al CORE01 intent identity authority contract

CORE01 `Order` artık explicit `intent_id` authority’sini taşıyabiliyor; eski
INTENT payload’ları korunuyor, kimlik sentetik üretilmiyor ve Spot binding
restart sonrası korunuyor. h.ak oracle’ı order ID/role/side/exact limit/intent
ID tam eşleşirse salt-okunur `ADMISSIBLE`, eksik/conflict durumda `BLOCKED`
dönüyor. Economic FILL/posting ve Store mutation yok. Odak `8/8`, tam proje
`587/587 PASS`, compile/workspace PASS (`233` aktif Python dosyası). Durum
`IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`. Kanıt:
`evidence/P1.12.f.h.al/SONUC.md`.

Sıradaki aktif kabul: `P1.12.f.h.am` admitted mapping’in Futures DCA fill
envelope ile CORE01 economic FILL boundary’sine offline bağlanması.

## 2026-09-17 P1.12.f.h.ak read-only CORE01 mapping admission oracle

F03 ve F15 için immutable Futures DCA mapping candidate mevcut CORE01 `State`
order scope’u ile mutation olmadan kontrol edildi. `core_order_id`, role, side
ve exact limit eşleşmiyorsa `BLOCKED`; eşleşse bile mevcut CORE01 `Order`
modelinde `core_order_intent_id` authority’si bulunmadığı için güvenli admission
açılmadı. Odak `7/7`, ilişkili guard kümesi `16/16 PASS`, tam proje
`585/585 PASS`, compile/workspace PASS (`233` aktif Python dosyası). Durum
`IMPLEMENTED_WITH_LIMITATION / NO_GO_CONFIRMED`. Kanıt:
`evidence/P1.12.f.h.ak/SONUC.md`.

Sıradaki aktif kabul: `P1.12.f.h.al` CORE01 intent identity authority’sinin
mutasyonsuz karar ve sözleşme kapısı.

## 2026-09-17 P1.12.f.h.aj immutable CORE01 mapping contract

F03 ve F15 için accepted Futures DCA event/posting ile CORE01 arasında
profile revision, core order/intent, role, side ve exact limit alanlarını
taşıyan non-economic mapping candidate contract’ı hazırlandı. Source ve
economic identity eşleşmeleri fail-closed; CORE01 Store/state mutation yok.
Odak `5/5`, hedefli küme `28/28 PASS`, tam proje `583/583 PASS`,
compile/workspace PASS (`233` aktif Python dosyası). Durum
`IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`. Kanıt:
`evidence/P1.12.f.h.aj/SONUC.md`.

Sıradaki aktif kabul: `P1.12.f.h.ak` mutasyonsuz CORE01 admission oracle’ı.

## 2026-09-17 P1.12.f.h.ai CORE01 economic authority boundary preflight

F03 ve F15 Futures DCA posting replay’si read-only CORE01 preflight ile
doğrulandı; mevcut envelope `side`, `core_order_intent`, `role` ve `limit_price`
authority alanlarını taşımadığı için binding `BLOCKED` kaldı. CORE01 Store’a
veya sentetik ekonomik state’e yazılmadı. Odak `3/3`, release+posting kümesi
`23/23 PASS`, tam proje `578/578 PASS`, compile/workspace PASS (`231` aktif
Python dosyası). Durum `IMPLEMENTED_WITH_LIMITATION / NO_GO_CONFIRMED`. Kanıt:
`evidence/P1.12.f.h.ai/SONUC.md`.

Sıradaki aktif kabul: `P1.12.f.h.aj` immutable Futures DCA → CORE01 mapping
contract’ı.

## 2026-09-17 P1.12.f.h.ah durable release + economic-posting atomic binding

F03 ve F15 Futures DCA zincirinde accepted partial/full fill event’i, release
history, reservation projection ve economic posting aynı bounded SQLite
transaction’ında bağlandı. Identity/source/commitment/fee/consumed-delta
eşleşmeleri, mixed duplicate ve failure rollback fail-closed; odak `20/20`,
tam proje `575/575 PASS`, compile/workspace PASS (`229` aktif Python dosyası).
Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; cancel, late/UNKNOWN
posting’e bağlanmadı. Kanıt: `evidence/P1.12.f.h.ah/SONUC.md`.

Sıradaki aktif kabul: `P1.12.f.h.ai` durable economic posting replay’sinin
CORE01 ekonomik authority sınırına offline binding’i.

## 2026-09-17 P1.12.f.h.ag durable Futures DCA release update

Schema revision `3` içindeki `reservation_releases` history’si reservation
projection ile aynı bounded transaction’da durable olarak bağlandı.
Optimistic version, release cursor, checksum/replay ve failure rollback
doğrulandı. Odak `17/17`, tam proje `572/572 PASS`, compile/workspace PASS
(`228` aktif Python dosyası). Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`;
release + economic-posting atomic binding sonraki mikro-fazdır. Kanıt:
`evidence/P1.12.f.h.ag/SONUC.md`.

Sıradaki aktif kabul: `P1.12.f.h.ah` release + economic-posting cursor binding.

## 2026-09-17 P1.12.f.h.af Futures DCA release transition state machine

Partial/full fill, cancel, late ve UNKNOWN release transition’ları exact
conservation, quarantine, release cursor, optimistic version ve
duplicate/conflict kurallarıyla saf projection olarak doğrulandı. Odak `4/4`,
tam proje `569/569 PASS`, compile/workspace PASS (`226` aktif Python dosyası).
Durum `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; durable journal update
sonraki mikro-fazdır. Kanıt: `evidence/P1.12.f.h.af/SONUC.md`.

Sıradaki aktif kabul: `P1.12.f.h.ag` durable atomic release transition update.

## 2026-09-17 P1.12.f.h.ae greenfield journal binding

F03 ve F15 Futures DCA greenfield journal’ında schema revision 2, ayrı
`release_cursor`, canonical economic posting ve event + reservation + posting
atomic binding tamamlandı. Odak `13/13`, tam proje `565/565 PASS`,
compile/workspace PASS (`224` aktif Python dosyası). Durum
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; legacy migration/publish
`NOT_APPLICABLE`. Kanıt: `evidence/P1.12.f.h.ae/SONUC.md`.

Sıradaki aktif kabul: partial/cancel/late/UNKNOWN release transition ve
release-cursor state machine.

## 2026-09-17 P1.12.f.h.ad greenfield ürün teslim sınırı

F03 ve F15 Futures DCA zinciri yeni ürün olarak kurulacaktır. Kullanıcıdan
eski source DB/export, manuel test veya gerçek işlem kaydı beklenmez. Legacy
migration/publish zinciri yalnız gelecekteki import için opsiyonel güvenlik
sınırıdır ve aktif ürün teslimatını bloklamaz. Durum
`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; migration/publish
`NOT_APPLICABLE`. Kanıt: `evidence/P1.12.f.h.ad/SONUC.md`.

Eski DCA projesi ve yedekler yalnız seçici teknik ve UI/UX referansıdır.
Başarılı parça ancak aktif sözleşme, test ve `reuse/REGISTER.md` kanıtıyla
yeniden kullanılabilir; eski runtime, talimat veya veri otomatik taşınmaz.

Sıradaki aktif kabul: greenfield journal event + reservation + fill-release +
economic-posting cursor binding’i.

## 2026-09-17 P1.12.f.h.d güncel kapsam kapısı

F03 ve F15 Futures DCA binding zincirinde profile-revision kapsamı ayrı bir
kapı olarak `DEFERRED / NO-GO / LOCAL_PASS` durumundadır: mevcut profile
symbol, effective-time ve immutable revision authority taşımaz. Kanıt:
`evidence/P1.12.f.h.d/SONUC.md`.

F03 ve F15 Futures DCA zincirinde fee/slippage/rounding authority’si ayrıca
`DEFERRED / NO-GO / LOCAL_PASS` durumundadır: mevcut fill ve pending reserve
bu ekonomik alanları taşımıyor. Kanıt:
`evidence/P1.12.f.h.e/SONUC.md`.

F03 ve F15 zincirinde partial/cancel/late/UNKNOWN release identity’si de
`DEFERRED / NO-GO / LOCAL_PASS` durumundadır; event sequence’i reservation
release authority’si değildir. Kanıt:
`evidence/P1.12.f.h.f/SONUC.md`.

F03 ve F15 Futures DCA persistence sahipliği için SpotBindingStore doğrudan
yeniden kullanılmayacak; tek journal/migration kararı
`DEFERRED / NO-GO / LOCAL_PASS` durumundadır. Kanıt:
`evidence/P1.12.f.h.g/SONUC.md`.

F03 ve F15 tek journal transaction oracle’ı `COMPLETE_WITH_LIMITATION /
LOCAL_PASS` durumundadır; production schema/migration binding’i
`IMPLEMENTATION_PENDING` kalır. Kanıt: `evidence/P1.12.f.h.h/SONUC.md`.

F03 ve F15 minimum Futures DCA journal schema/migration sözleşmesi
`CONTRACT_READY / IMPLEMENTATION_PENDING`, production binding `NO-GO`
durumundadır; validator ve conflict/replay testi beklenir. Kanıt:
`evidence/P1.12.f.h.i/SONUC.md`.

F03 ve F15 migration validator/conflict-replay oracle’ı
`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; production validator/binding
`IMPLEMENTATION_PENDING` durumundadır. Kanıt:
`evidence/P1.12.f.h.j/SONUC.md`.

F03 ve F15 gerçek split store migration preflight’i
`COMPLETE_WITH_LIMITATION / LOCAL_PASS`, migration binding `NO-GO`;
eksik immutable alanlar ve target oluşturulmaması doğrulandı. Kanıt:
`evidence/P1.12.f.h.k/SONUC.md`.

F03 ve F15 minimum v1 schema initializer’ı
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, binding `NO-GO`; şema inert,
satır ve ekonomik binding yoktur. Kanıt:
`evidence/P1.12.f.h.l/SONUC.md`.

F03 ve F15 immutable profile revision insert/replay’i
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, event binding `NO-GO`;
canonical hash, duplicate/conflict ve contract-size sınırları doğrulandı.
Kanıt: `evidence/P1.12.f.h.m/SONUC.md`.

F03 ve F15 profile-bound immutable event envelope’ı
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; reservation/posting binding
`NO-GO`. Sequence, canonical payload/checksum ve duplicate/conflict sınırları
doğrulandı. Kanıt: `evidence/P1.12.f.h.n/SONUC.md`.

F03 ve F15 minimum reservation projection kapısı
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; exact reservation alanları,
duplicate/conflict replay ve source-event reference doğrulandı. Event+reservation
atomic coordinator, release transition ve economic posting `NO-GO` durumundadır.
Kanıt: `evidence/P1.12.f.h.o/SONUC.md`.

F03 ve F15 event+reservation atomic coordinator kapısı
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; aynı bounded journal transaction’ı,
failure-injection rollback ve restart replay doğrulandı. Release/posting ve
mevcut split store migration `NO-GO` durumundadır. Kanıt:
`evidence/P1.12.f.h.p/SONUC.md`.

F03 ve F15 split-store migration kapsam envanteri
`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; v1 journal’ın tam immutable alanları
karşılaştırıldı, gerçek kaynaklarda eksik profile/economic/release/posting
alanları nedeniyle migration `NO-GO` kaldı. Kanıt:
`evidence/P1.12.f.h.q/SONUC.md`.

F03 ve F15 migration source contract kararı
`CONTRACT_READY / IMPLEMENTATION_PENDING`; source authority, row identity,
exact normalization, revision/event binding ve unknown/conflict/late davranışı
zorunlu kabul şartlarıdır. Mevcut split store’lar tam kaynak olmadığı için
migration `NO-GO` durumundadır. Kanıt:
`evidence/P1.12.f.h.r/SONUC.md`.

F03 ve F15 profile revision + contract-size source adapter
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; explicit source alanları immutable
profile revision’a bağlanıyor, contract-size default edilmiyor. Venue fetch,
provenance, migration ve ekonomik binding `NO-GO` durumundadır. Kanıt:
`evidence/P1.12.f.h.s/SONUC.md`.

F03 ve F15 profile source provenance/snapshot identity
`CONTRACT_READY / IMPLEMENTATION_PENDING`; source kind, row/snapshot identity,
payload hash, schema/policy revision, observed time ve profile bağı zorunludur.
V1 profile tablosu bunları taşımadığı için persistence/migration `NO-GO`.
Kanıt: `evidence/P1.12.f.h.t/SONUC.md`.

F03 ve F15 immutable provenance schema taslağı
`CONTRACT_READY / IMPLEMENTATION_PENDING`; ayrı source snapshot owner’ı,
identity/hash/state/replay ve profile foreign-key kısıtları tanımlandı. V1’e
uygulanmadı; schema migration `NO-GO`. Kanıt:
`evidence/P1.12.f.h.u/SONUC.md`.

F03 ve F15 provenance SQLite failure/replay oracle
`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; ACCEPTED replay, duplicate/conflict,
UNKNOWN authority dışı bırakma ve failure rollback `3/3` doğrulandı. Production
schema/migration binding `NO-GO` durumundadır. Kanıt:
`evidence/P1.12.f.h.v/SONUC.md`.

F03 ve F15 bağımsız inceleme + kapsamlı kabul kapısı
Bağımsız Standards/Spec incelemesi sonrası önceki `NO_GO` aktarımı ve manifest
canonical doğrulaması düzeltildi; odak `14/14`, tam proje `562/562 PASS`.
Migration/publish hâlâ `NO-GO`. Kanıt: `evidence/P1.12.f.h.ac/SONUC.md`.

F03 ve F15 insan kontrollü publish-readiness karar kapısı
`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; target validation, manifest eşleşmesi
ve bağımsız oracle birleşiyor. Teknik geçiş `READY_FOR_REVIEW`, fakat insan
onayı `REQUIRED` ve publish `BLOCKED`; migration/publish açılmadı. Kanıt:
`evidence/P1.12.f.h.ab/SONUC.md`.

F03 ve F15 manifest reopen + bağımsız hash/eşleme oracle kapısı
`COMPLETE_WITH_LIMITATION / LOCAL_PASS`; production hash yardımcısından
bağımsız stdlib oracle reopen edilmiş target satırını ve canonical SHA-256
manifestini doğruluyor. Target/manifest tahrifi `NO_GO`; migration ve publish
açılmadı. Kanıt: `evidence/P1.12.f.h.aa/SONUC.md`.

F03 ve F15 source-to-target eşleme ve immutable migration manifest kapısı
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; source/target identity, profile
revision, payload hash, schema revision, observed time ve state canonical
SHA-256 manifest’e bağlanıyor. Target ile read-only birebir eşleşme `READY`,
UNKNOWN/duplicate/conflict/empty/mismatch `NO_GO`; migration ve publish
açılmadı. Kanıt: `evidence/P1.12.f.h.z/SONUC.md`.

F03 ve F15 read-only provenance validation + publish karar kapısı
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; profile checksum/replay, snapshot
identity/hash/state, profile FK ve tekil ACCEPTED bağ doğrulanıyor. Geçerli
target `READY/READY`, UNKNOWN/missing/conflict `NO_GO/NO_GO`; migration ve
otomatik publish açılmadı. Kanıt: `evidence/P1.12.f.h.y/SONUC.md`.

F03 ve F15 bounded provenance target initializer + failure/restart kapısı
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; yeni target mevcut v1 dosyasını
değiştirmeden profile-source snapshot tablosunu ve kısıtlarını kuruyor.
Duplicate/conflict, UNKNOWN replay dışı bırakma ve rollback/reopen `3/3`
doğrulandı. Migration ve publish `NO-GO`. Kanıt:
`evidence/P1.12.f.h.x/SONUC.md`.

F03 ve F15 provenance target schema/migration taslağı
`CONTRACT_READY / IMPLEMENTATION_PENDING`; v1 in-place değişmeden ayrı target,
profile foreign key, unique/hash/state/replay ve read-only migration sırası
tanımlandı. Migration `NO-GO` durumundadır. Kanıt:
`evidence/P1.12.f.h.w/SONUC.md`.

Güncel F03/F15 override: P1.12.f.h.ai read-only CORE01 preflight’i
`IMPLEMENTED_WITH_LIMITATION / NO_GO_CONFIRMED`; gerçek CORE01 economic
binding, `side`/intent/role/limit authority’si tanımlanana kadar açılmaz.

| ID | Hedef yetenek | Referans | Bizim demo kabulümüz | Bugünkü durum |
|---|---|---|---|---|
| F01 | DCA standard/custom ladder | C2 | Form → plan/sermaye önizleme; base/quote sizing, gerçek fill ile ilerleme | CORE01 temel alt küme; P1.09.a exact BASE/QUOTE candidate, P1.09.b exact ladder conservation, P1.09.e exact ladder binding, P1.09.g quote-unit pre-acceptance gate, P1.09.h bağımsız exact/metamorphic oracle ve P1.09.i BASE candidate quote commitment binding `COMPLETE_WITH_LIMITATION`, public ladder UI PLAN |
| F02 | Base/quote/bakiye yüzdesi sizing | C2 | Referans bakiye türü ve notional/margin ayrımı; yuvarlama retleri | P1.09.a BASE_QTY/QUOTE_NOTIONAL candidate, P1.09.c profile-bound grid/minimum, P1.09.d tagged eligible-balance percent budget, P1.09.h bağımsız exact/metamorphic oracle ve P1.09.i BASE candidate binding `COMPLETE_WITH_LIMITATION`; public balance authority ve rounding PLAN |
| F03 | Safety hacim/adım çarpanı ve aktif emir sayısı | C2 | Ladder toplam bütçesi, birden çok pending rezerv yarışı | CORE01 tek pending alt küme; 3Commas/Pionex uyumlu cumulative deviation + volume multiplier, fixed amount/value ve finite safety planı P1.12.f.a `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.12.f.b bağımsız exact oracle `COMPLETE_WITH_LIMITATION / LOCAL_PASS` (`2/2`, tam suite `507/507 PASS`); P1.12.f.c fill sonrası exact average-entry ve bounded pending projection `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (odak `4/4`, bağımsız oracle `2/2`, tam suite `513/513 PASS`); P1.12.f.d local event identity/sequence `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (`4/4`, tam suite `517/517 PASS`); P1.12.f.e shared-account reservation candidate binding `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (`3/3`, tam suite `520/520 PASS`); P1.12.f.f durable event journal/replay `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (`4/4`, tam suite `524/524 PASS`); P1.12.f.g reservation + fill-release atomicity `DEFERRED / NO-GO / LOCAL_PASS`; P1.12.f.h atomic binding contract `CONTRACT_READY / IMPLEMENTATION_PENDING`; P1.12.f.h.a ayrı-ledger failure-injection `LOCAL_PASS / NO-GO_CONFIRMED`; P1.12.f.h.b contract-size gate `DEFERRED / NO-GO / LOCAL_PASS`; P1.12.f.h.c explicit multiplier exact oracle `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; P1.12.f.h.af release transition state machine `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (`4/4`, tam suite `569/569 PASS`); P1.12.f.h.ag durable release update `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (`17/17`, tam suite `572/572 PASS`); P1.12.f.h.ah release + economic-posting atomic binding `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (`20/20`, tam suite `575/575 PASS`; cancel/late/UNKNOWN posting dışı) |
| F04 | Custom giriş/averaging/çıkış koşulları | C2/C3 | Koşul ağacı, indikatör warmup, closed-bar zamanı, tetik açıklaması | P1.14.b/c signal/readiness sınırı `COMPLETE_WITH_LIMITATION`; P1.12.g.a immediate/closed-candle/signal start gate `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.12.g.b max-DCA/stop/EXHAUSTED `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.12.g.c average-entry/split-TP projection `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.12.g.d explicit fee-aware breakeven boundary ve P1.12.g.e exit priority `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; selected exit-candidate/trailing/advanced execution P1.12.g.f+ `PLAN / CONTRACT_REQUIRED` |
| F05 | Çok pair/bot, blacklist/favoriler | C2 | Ortak sanal bütçe, pozisyon sahipliği, arama ve filtre | F8 bot registry + ownership + 6 endpoint + BotPanel `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (RAM registry, session tek-sahipli, blacklist∩pairs yasak); durable registry + arama/filtre PLAN |
| F06 | Cooldown, zaman sınırı, reinvest ve risk azaltma | C3 | Çok deal döngüsü; realized kâr sonrası yeni sizing; cashflow ayrımı | P1.09.f realized-profit eligible reinvestment projection `COMPLETE_WITH_LIMITATION`; multi-deal cashflow, risk azaltma ve runtime bağlama PLAN |
| F07 | Manuel gelişmiş işlem terminali | C1 | Limit/market/stop, giriş/çıkış grafiği ve kalıcı command | CLI olay alt küme |
| F08 | Split take profit | C4 | Hedef miktar toplamı kalan pozisyonu aşmaz; partial sonrası revizyon | P1.10.a trigger/execution boundary ve P1.10.b exact quantity conservation `COMPLETE_WITH_LIMITATION`; multi-TP registry/OCO ve UI PLAN; P1.12.g.b stop boundary `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.12.g.c average-entry/split-TP projection `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.12.g.d fee-aware breakeven boundary ve P1.12.g.e exit priority `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; selected exit candidate/OCO/cancel-replace/real execution P1.12.g.f+ `PLAN / CONTRACT_REQUIRED` |
| F09 | Trailing TP/SL ve breakeven | C1/C4 | Activation/mesafe/fee-aware eşik; gap ve cancel-replace senaryosu | P1.10.a TP, P1.10.c STOP trigger/execution, P1.10.d long, P1.10.g short sabit-mesafe, P1.10.h long/short percentage ratchet ve P1.10.i ortak trailing exit-boundary, P1.10.e trailing-exit capacity binding `COMPLETE_WITH_LIMITATION`; P1.10.f breakeven, P1.10.j OCO/cancel-replace/late-fill ve P1.10.k public/API/UI `DEFERRED/NO-GO` (fee-asset, cancellation confirmation, replacement identity, reserve, public state ve görsel sözleşmeler eksik); Futures DCA/Grid profilleri P1.12.g.c average-entry/split-TP projection, P1.12.g.d explicit fee-aware breakeven ve P1.12.g.e exit priority `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; fee conversion/rounding, selected exit candidate, OCO/cancel-replace ve gerçek execution P1.12.g.f+ `PLAN / CONTRACT_REQUIRED`; F9 trailing-bind + yüzde-ratchet + breakeven API + ExitPanel `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (authority NONE, canlı kanıtlı) |
| F10 | Gross/net hedef, fee ve funding dökümü | C3 + ürün önerisi | Tahmin/gerçek gider ayrımı; third-asset conversion; exact hesap | CORE01 kısmi; P1.12.a linear futures signed UPL/timestamped funding, P1.12.b partial-close gross PnL ve P1.12.c immutable fee/funding event projection `COMPLETE_WITH_LIMITATION`; P1.12.d yalnız fee/funding ledger replay `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`, CORE01 ekonomik Store binding `DEFERRED/NO-GO`; funding dataset/schedule, settlement conversion ve public result PLAN |
| F11 | Spot grid | P1 | Alt/üst range, aritmetik/geometrik seviye, net envanter ve fee | P1.13.a exact aritmetik level generation + P1.13.b accepted-fill inventory projection + P1.13.c quote-asset fee, matched cycle profit/total equity projection + P1.13.d exact geometric root/tick validation `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; base/third fee conversion, venue rounding, replacement ve public UI ayrı kapı/PLAN |
| F12 | Grid trailing up/down | C1 | Range kayması yeni version; pending emir/rezerv etkisi | P1.13.e Spot trailing `DEFERRED / NO-GO / LOCAL_PASS`; P1.13.g.a–g.c Futures trailing/expansion/replacement/replay/late-fill sınırları `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` olarak yalnız güvenlik kapısında; P1.13.g.d primary-source lifecycle audit ve P1.13.g.e second report cross-audit `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED`, ileri implementation `DEFERRED / NO-GO`; exact range/version, cancel-replace, late-fill ve replay kanıtı olmadan ekonomik veya emir davranışı açılmaz; F5 trailing arm/observe API+UI `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (tetikleyici projeksiyonu, emir değil) |
| F13 | Reverse/infinity/leveraged grid aileleri | P4 keşif | Her varyant ayrı matematik ve kaynak doğrulaması; görünüşte isim değişimi yok | P1.13.h `DEFERRED / NO-GO until verified`; 3Commas Reversal yüksek seviye davranışı `RESEARCH_ACCEPTED_WITH_LIMITATION`, exact reversal/Infinity semantics ve oracle bekliyor; leverage P1.13.f + P1.12/P1.11 bağımlı; Faz 5 kutusu DEFERRED onayı (standart model yok) |
| F14 | Futures grid long/short | P3 | Ayrı yön/teminat/funding, pozisyon sahipliği ve liquidation kapsamı | P1.12.e fixed-tier isolated liquidation estimate `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (risk snapshot zorunlu, venue liquidation değildir); P1.13.f.a Futures Grid v1 ayrı profile + exact arithmetic/geometric level projection `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.13.f.b one-way position/initial-position/accepted-fill state `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.13.f.c isolated margin/leverage/reserve `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.13.f.d funding/mark/liquidation ve grid-profit/total-P&L `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.13.g.a dynamic order placement ile grid range/trailing ayrımı `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.13.g.b advanced variant safety gate `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.13.g.c replacement/replay ve late-fill identity safety gate `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.13.g.d primary-source lifecycle audit ve P1.13.g.e second report cross-audit `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED`, ileri implementation `DEFERRED / NO-GO`; P1.13.g dynamic order placement, exact lifecycle implementation ve P1.15 bağımlı Hedge Grid `PLAN / CONTRACT_REQUIRED`; F5 grid/PnL/trailing/funding projection API+UI `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (canlı kanıtlı, likidasyon yetkisi yok — LCR-12 NO-GO); canlı emir P2/P3 kapısına bağlı |
| F15 | DCA averaging-down / martingale | P2 | Geometrik sermaye artışı açık; maximum safety stop-loss sayılmaz | CORE01 temel alt küme; 3Commas/Pionex safety-order count, cumulative deviation, volume scale, average-entry/capital preview P1.12.f.a `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.12.f.b bağımsız exact oracle `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; P1.12.f.c observed fill average-entry ve bounded pending reservation `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.12.f.d local event identity/sequence `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.12.f.e shared-account reservation candidate binding `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.12.f.f durable event journal/replay `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.12.f.g reservation + fill-release atomicity `DEFERRED / NO-GO / LOCAL_PASS`; P1.12.f.h atomic binding contract `CONTRACT_READY / IMPLEMENTATION_PENDING`; P1.12.f.h.a ayrı-ledger failure-injection `LOCAL_PASS / NO-GO_CONFIRMED`; P1.12.f.h.b contract-size gate `DEFERRED / NO-GO / LOCAL_PASS`; P1.12.f.h.c explicit multiplier exact oracle `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; P1.12.f.h.af release transition state machine `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.12.f.h.ag durable release update `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.12.f.h.ah release + economic-posting atomic binding `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.12.f.i Pionex DIY per-safety-order deviation/allocation `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`; P1.12.f.i.a quantity-step + quote/base candidate `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`; P1.12.f.i.b bağımsız Decimal oracle/write-surface gate `IMPLEMENTED_WITH_LIMITATION / INDEPENDENT_REVIEW_PASS`; P1.12.f.i.c immutable acceptance-boundary `IMPLEMENTED_WITH_LIMITATION / CONTRACT_READY`; P1.12.f.i.d offline sizing/pre-acceptance bridge `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (quote-only, BASE→QUOTE örtük dönüşüm yok); P1.12.g.a immediate/closed-candle/signal start gate `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.12.g.b max-DCA/stop/EXHAUSTED `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.12.g.c average-entry/split-TP projection `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.12.g.d explicit fee-aware breakeven `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; P1.12.g.e exit priority `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; selected exit-candidate, fee conversion/rounding, trailing, OCO and durable recovery P1.12.g.f+ `RESEARCH_READY / IMPLEMENTATION_PENDING` |
| F16 | Dönemsel alım / recurring buy | Ürün kapsamı | Zaman takvimi; fiyat aleyhe safety stratejisinden ayrı model | F10 `POST /api/recurring/schedule` projection + RecurringPanel `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; zamanlanmış yürütme/safety entegrasyonu `PLAN` |
| F17 | Portföy ve rebalancing | P5/C1 | Hedef ağırlık; zaman/eşik; işlem ücreti ve dış akış etkisi | P1.14.a exact valuation target/delta projection + P1.14.d threshold/time trigger `COMPLETE_WITH_LIMITATION`; F7.1 explicit-price valuation + canonical plan identity + F7.3 valuation API/UI + F7.4 fee/rounding disclosure + reserve check + order-candidate binding + plan/disclosure API/UI `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; venue order gönderimi kapsam-dışı (candidates emir değil) |
| F18 | Spot–futures arbitraj / çift bacak | P4 keşif | Spread/funding/borrow/transfer varsayımı; senkron olmayan iki bacak riski | P1.15.a explicit two-leg intermediate state/identity + P1.15.b same-scope HEDGE accepted-fill projection `COMPLETE_WITH_LIMITATION`; P1.15.c persistence/replay/recovery `DEFERRED/NO-GO`; F6 durable journal + 5 endpoint + TwoLegPanel `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (same-scope HEDGE, restart-kanıtlı, sentetik bacak yok); cross-venue atomicity ve economic binding `PLAN` |
| F19 | Signal bot / webhook / TradingView akışı | C1 | Offline kaydedilmiş sinyal; event-time, auth/replay protection ve dedup | P1.14.b immutable signal identity/event-time/dedupe + P1.14.c warmup/closed-bar/stale readiness `COMPLETE_WITH_LIMITATION`; F7.2 canonical payload hash + HMAC auth + replay window + F7.4 signal→candidate binding + hash/assess/candidate API/UI `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; venue order gönderimi kapsam-dışı |
| F20 | Strateji şablonu/kopyalama/paylaşma | C2 | Versiyon, parametre diff, yerel import/export; takip edilen şablon yetkisiz emir açmaz | P1.14.e canonical snapshot/hash + P1.14.f explicit approval/capability gate, bounded inert payload ve non-authority `COMPLETE_WITH_LIMITATION`; F20.1 onaylı profile binding + F20.2 materialization/import-export/diff + F20.3 API/UI `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (canlı import→bind kanıtlı); paylaşım, order binding `PLAN` |
| F21 | Geçmiş veri backtest | C1/C3 | Gerçek dataset; değişmez run kimliği; model varsayımı ve açık pozisyon değeri | P1.04.a canonical input + P1.04.b preflight + P1.04.c config bağlı run-plan + P1.04.d bounded validation + P1.04.e bounded `historical_ohlcv_v1` reducer koşusu/status + P1.05.a minimal read-only sonuç özeti + P1.05.b read-only action geçmişi + P1.05.c.1 bounded chart data contract + P1.05.c.2 static inline SVG OHLC overview + P1.05.c.3 fail-closed static action marker + P1.05.d minimal economic outcome + P1.06.a canonical run capture + P1.06.b dedicated immutable run store + P1.06.c explicit save API + P1.06.d bounded list/detail read API + P1.06.e Saved Runs list/detail UI + P1.20 gerçek local tam demo kabulü `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; reproduce/compare ve kapsamlı ekonomik görünüm PLAN |
| F22 | Kaydedilmiş koşu, kıyas ve log–chart bağlantısı | C3 | Aynı dataset/model; olaydan chart noktasına ulaşım; export | P1.06.d/e list/detail + Faz 2.3 `POST /api/historical-runs/{run_id}/reproduce` (hash karşılaştırmalı, fail-closed) + `SavedRunsPanel.tsx` yan yana kıyas + Faz 2.4 grafik↔tablo çift yönlü marker `COMPLETE_WITH_LIMITATION`; CSV/JSON export F10 `GET /api/historical-runs/{run_id}/export` `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (canlı kanıtlı, 2026-09-21) |
| F23 | Parametre tarama, OOS/walk-forward | Ürün önerisi | Train/test sızıntısı yok; başarısız koşular ve çoklu deneme riski görünür | P1.16.a chronological train/gap/test boundary `COMPLETE_WITH_LIMITATION / LOCAL_PASS` + P1.16.b OOS freeze/touched lineage `COMPLETE_WITH_LIMITATION / LOCAL_PASS` + P1.16.c feature/label overlap gate `COMPLETE_WITH_LIMITATION / LOCAL_PASS` + P1.16.d bounded trial registry + P1.16.e ayrı stress lineage/result identity + P1.16.g bounded local feature/label horizon ve historical runner binding + P1.16.h bounded persisted trial/stress/OOS metadata binding `COMPLETE_WITH_LIMITATION`; P1.16.f warmup/readiness research audit `DEFERRED / NO-GO / RESEARCH_AUDITED / LOCAL_PASS`; exact purge/embargo ve ekonomik evaluation `PLAN` |
| F24 | Stres, spread/slippage/latency/partial fill | Ürün önerisi | Reproducible seed; iyimser/kötümser OHLC model farkı | P1.16.e immutable separate stress lineage/result identity + P1.16.h persisted metadata binding `COMPLETE_WITH_LIMITATION`; P1.16.i.a authority/evidence inventory `COMPLETE_WITH_LIMITATION`; P1.16.i.b research audit `COMPLETE_WITH_LIMITATION`, ekonomik implementation `DEFERRED/NO-GO`; P1.16.i.c deterministic identity `COMPLETE_WITH_LIMITATION`, ekonomik scenario identity `DEFERRED/NO-GO`; P1.16.i.d persistence/replay/recovery `COMPLETE_WITH_LIMITATION`, stress persistence/branch/atomicity `DEFERRED/NO-GO`; P1.16.i.e `COMPLETE_WITH_LIMITATION/NO-GO`; P1.07.a.1 core partial state + P1.07.a.2 opt-in fixed-slice application + P1.07.a.3 public contract alt kümesi + P1.07.d.3.a internal BASE-only reducer probe + P1.07.d.3.b `reserve_model=NONE` sınır kararı + d.3.c NONE acceptance testleri + d.2.b explicit-fixture BASE-bound public limit contract `COMPLETE_WITH_LIMITATION`; ekonomik spread/slippage/latency/queue/volume/OHLC senaryoları, explicit reserve lifecycle, stop ve aynı-bar cancel-fill yarışı kanıt gelmeden açılmaz |
| F25 | CSV/ZIP import ve kalite merkezi | Ürün gereksinimi | Schema, checksum, timestamp, gap/duplicate raporu; iptal ve atomik kayıt | P1.02 kalite/mapping var; kalıcı import ve kayıt PLAN |
| F26 | Public tarihsel indirme/cache | D1 | İnternet elverişliyse source/retry/cancel; yerel dosya fallback | P1.03 explicit registry/cache/catalog/download UI var; tam import fallback PLAN |
| F27 | Canlı fiyatla paper trading | Ürün gereksinimi | Public feed stale/reconnect; simulated emirler; credential yok | P1.17.a public read-only data authority inventory `COMPLETE_WITH_LIMITATION`; P1.17.b public feed contract `COMPLETE_WITH_LIMITATION/RESEARCH_AUDITED`; P1.17.c offline observation replay `COMPLETE_WITH_LIMITATION`; P1.17.d Binance Spot public transport/reconnect research `COMPLETE_WITH_LIMITATION/RESEARCH_AUDITED`; P1.17.e network-free payload normalization `COMPLETE_WITH_LIMITATION/LOCAL_PASS`; P1.17.f network-free replay binding `COMPLETE_WITH_LIMITATION/LOCAL_PASS`; P1.17.g acceptance matrix `COMPLETE_WITH_LIMITATION/LOCAL_PASS`; P1.17.h REST normalization `COMPLETE_WITH_LIMITATION/LOCAL_PASS`; P1.17.i capability boundary `COMPLETE_WITH_LIMITATION/LOCAL_PASS`; P1.17.j transport activation gate `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (F27.1 credential-free activation + F27.2 gerçek REST/WS transport, canlı venue kanıtlı + F27.3 binding/API/UI); simulated emir/fill `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (explicit fill politikası, marketsiz otomatik-fill yok); credential ve gerçek emir kapsam-dışı (paper tanımsal olarak credentialsız) |
| F28 | Dashboard/portföy/risk bütçesi | C1 + ürün önerisi | Equity/rezerv/exposure, realized/unrealized ayrımı; account toplamı | CLI rapor alt küme + F10 `GET /api/dashboard` (paper+bot aggregation, read-only) + DashboardPanel `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; account toplamı venue bağına bağlı `PLAN` |
| F29 | Grafik üstünde plan düzenleme | C2 | Sürükleme → backend doğrulama → revision-bound preview | F10 `POST /api/datasets/{id}/draft-level` (ACCEPTED/REJECTED, sha-bound, fail-closed) + chart sürükleme/klavye/metin UI `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (canlı kanıtlı); revision-bound preview `PLAN` |
| F30 | Basit/uzman, açık/koyu ve responsive UI | C2 + ürün önerisi | Aynı config, klavye/focus, ekran genişlikleri ve empty/error state | P1.01–P1.03 responsive UI dilimleri, P1.18.d visual/accessibility smoke QA, P1.19.a result-shell state acceptance, P1.19.b inventory, P1.19.c dark-token/focus implementation, P1.19.d CDP accessibility QA, P1.19.e gerçek kod/contract/contrast denetimi ve P1.19.f exact token/detailed-view gate `DEFERRED / NO-GO`; mevcut native disclosure minimum detailed-view olarak kabul edildi; F9 açık palet exact donduruldu + 32/32 AA + statik a11y kapıları `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; NVDA/JAWS/HCM NOT_RUN (insan kapısı) |
| F31 | Bot lifecycle ve toplu işlemler | Ürün gereksinimi | Pause/stop-after-deal/cancel/flatten ayrımı; her botun sonucu ayrı | P1.08.a saf lifecycle authority, P1.08.b COPY sınırı, P1.08.c store inventory, P1.08.d event identity, P1.08.e event adapter, P1.08.f persistent record boundary, P1.08.g config snapshot/hash binding, P1.08.h terminal/cooldown policy ve P1.08.i pause-order policy `COMPLETE_WITH_LIMITATION`; P1.11.a shared account ownership/isolation `DEFERRED/NO-GO`, P1.11.b immutable identity, P1.11.c pure capacity/version projection ve P1.11.d dedicated reservation persistence/version boundary `COMPLETE_WITH_LIMITATION`; P1.11.e fill/release + existing Store binding `DEFERRED/NO-GO`; F9 deal API (create/event/replay) + sıralı bulk + DealPanel `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (atomik değil, her deal sonucu ayrı); cross-deal isolation PLAN |
| F32 | Açıklayıcı asistan | C1 + ürün önerisi | Offline yardım/neden; isteğe bağlı LLM önerisi önce doğrulama/backtest | P1.18.a bounded rule-based read-only explanation projection, P1.18.b strict API response binding, P1.18.c read-only explanation UI ve P1.18.d visual/accessibility QA `COMPLETE_WITH_LIMITATION`; F8 zincir 15/15 + canlı UI bağlı doğrulandı; dış LLM/öneri/bildirim `DEFERRED` (credential + ürün kararı Arda'da) |
| F33 | Uyarı, bildirim ve olay merkezi | Ürün önerisi | Stale veri/UNKNOWN/gap/limit; yerel kanal zorunlu, dış kanallar adapter | F10 `GET /api/events` yerel olay listesi + EventPanel `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; dış kanallar adapter `DEFERRED` |
| F34 | Cross/isolated/hedge ürün kapsamı | C2 + ürün kapsamı | Mode-specific muhasebe ve stres; veri yetersizse açık model sınırı | P1.15.a one-way/hedge identity ve two-leg state + P1.15.b same-scope HEDGE leg-fill projection `COMPLETE_WITH_LIMITATION`; P1.15.c persistence/replay/recovery `DEFERRED/NO-GO`; F6 journal/replay/recovery same-scope HEDGE `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; cross/isolated muhasebesi, margin/liquidation ve venue profile `PLAN/DEFERRED` |
| F35 | Çoklu settlement/fee varlığı | Ürün kapsamı | Zamanlı kur, envanter etkisi, eksik kurda net sonuç INCOMPLETE | Yalnız USDT alt küme: `GET /api/settlement` + settlement_profile gate `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; çoklu settlement `DEFERRED` (zamanlı kur/envanter yok) |
| F36 | Audit/export/backup/restore | Ürün gereksinimi | Run kaynak izi; aktif DB tutarlı backup; restore sonrası yeniden üretim | Journal audit alt küme + F10 `POST /api/admin/backup` + verify + liste + BackupPanel `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (traversal-safe); restore otomasyonu `PLAN` |
| F37 | Exchange capability/connection wizard | C1 + ürün gereksinimi | P1 simulated connection; P2 Binance testnet; P3 live; P4 venue farkı | P2.01 araştırması `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED`; P2.01.a gerçek kimliksiz public `exchangeInfo` connectivity + bounded read-only UTF-8 symbol/filter/rate-limit snapshot `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; P2.01.b public snapshot salt-okunur UI `IMPLEMENTED_WITH_LIMITATION / READY_WITH_LIMITATION`; P2.02 durable attempt/outbox, P2.02.a signer/time, P2.02.b ephemeral credential/capability ve P2.04.a/b offline reconciliation/restart sınırı `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; gerçek Windows provider, signed account/key capability, canlı WS/REST recovery, order/account mutation ve canlı kabul hâlâ `IN_PROGRESS/PLAN/DEFERRED/NO-GO`. Kanıt: `evidence/P2.01/SONUC.md`, `evidence/P2.01.a/SONUC.md`, `evidence/P2.01.b/SONUC.md`, `evidence/P2.02/SONUC.md` |
| F38 | Online marketplace/copy ağı ve platforma özgü earn/fiat/custody | EXTERNAL_DEPENDENCY | P1 katalog/sözleşme ve mock akış; gerçek hizmet için ayrı dış platform entegrasyonu kararı | KEŞİF; eşdeğer sunulmaz |
| F39 | Hesaplanabilir risk açıklaması ve değişiklik etkisi | Ürün önerisi | Önce/sonra equity/bütçe; işlem açmama nedenini kullanıcı anlar | F10 `POST /api/risk/explain` (read-only, hesaplanabilir alanlar) + RiskPanel `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS`; değişiklik-etkisi simülasyonu `PLAN` |
| F40 | Zaman çizgisinde replay step/seek/speed | Ürün önerisi | Event snapshot; geri sarma yeni dal/run yaratır, geçmiş ledger değişmez | F10 `GET /api/deals/{id}/timeline` step/seek + TimelinePanel oynatma/hız `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` (deal-scoped, salt okunur); yeni dal/run yaratma yok |

Güncel P1.13 override: ayrıntılı kabul satırları ve üstteki güncel mikro-faz
kayıtları bağlayıcıdır. `P1.13.g.f` DCABOT’a özgü offline lifecycle politika
kontratı `COMPLETE_WITH_LIMITATION / LOCAL_PASS` ve
`CONTRACT_DECLARED` olarak tamamlandı; vendor-eşdeğer lifecycle
implementation `DEFERRED / NO-GO`, tüm authority alanları `NONE`.
`P1.13.g.g` explicit politikayı `CONTRACT_READY` immutable in-memory offline
transition simülasyonuna bağladı. `P1.13.g.h` local event matrix bağımsız
oracle ve conflict/replay regresyon kapısını `ORACLE_PASS` olarak tamamladı;
`P1.13.h.a` Reverse/Infinity varyantlarını typed ve
`BLOCKED_CONTRACT_REQUIRED` güvenlik kapısında tamamladı. `P1.13.h.b` exact
Reverse/Infinity sözleşmelerinin mevcut kaynaklarda bulunmadığını karşı-audit
ile doğruladı; vendor parity `DEFERRED / NO-GO` kaldı. Sonraki tek güvenli iş
`P1.13.h.c` bu eksikliği ürün admission sınırında `NOT_SUPPORTED + BLOCKED`
olarak görünür kıldı. `P1.13.h.d` bağımsız inceleme ve kritik regresyon
kapısını tamamladı; sonraki tek güvenli iş `P1.14.c` signal warmup/closed-bar
ve stale-policy karar kapısıdır.
`P1.13.c` ve `P1.13.d` tamamlandı; `P1.13.e`
trailing-up/down ve reverse/infinity karar kapısı `DEFERRED / NO-GO` olarak
kapatıldı. `P1.13.f.a` ayrı profile ve exact level projection, `P1.13.f.b`
one-way position/accepted-fill state, `P1.13.f.c` isolated
margin/leverage-reserve ve `P1.13.f.d` funding/mark/P&L projection olarak
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` durumundadır. `P1.13.g.a`
dynamic order placement, `P1.13.g.b` advanced variant ve `P1.13.g.c`
replacement/replay-late-fill identity güvenlik kapıları olarak kapatıldı.
`P1.13.g.d` primary-source lifecycle audit ve `P1.13.g.e` ikinci raporun
karşı-auditi tamamlandı; resmî kaynaklar exact oracle sağlamadığı için ileri
implementation `DEFERRED / NO-GO` ve ana P1.13.g’nin kalan advanced
davranışları exact source/oracle kanıtı olmadan `CONTRACT_REQUIRED`.

Güncel P1.12 override: ayrıntılı kabul satırları ve üstteki güncel mikro-faz
kayıtları bağlayıcıdır. `P1.12.h.d` tamamlandı; sıradaki aktif kabul
`P1.13.c` Spot Grid fee asset/rounding ve matched cycle profit-total equity
ayrımının karar ve salt-okunur projection kapısıdır.
g.g sonrası conditional execution, OCO/cancel-replace ve durable recovery ayrı
kapılar olarak kalır.

Güncel P1.12.g.f override: yukarıdaki g.f mikro-faz kaydı bağlayıcıdır ve eski
F04/F08/F09/F15 özetlerindeki `g.f+ PLAN` ifadesini supersede eder. g.f
`IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` olarak tamamlandı; g.g ile candidate
identity/late-fill ayrımı da kapatıldı. OCO/cancel-replace, fee
conversion/rounding, reserve mutation, persistence/recovery ve
Binance/Testnet mutation hâlâ açılmadı.

Güncel P1.12.h.d override: `P1.12.h.d` tamamlandı; recovery snapshot ile
immutable profile-source provenance cross-check kanıtlandı, temiz sonuç yalnız
`READY_FOR_REVIEW`, CORE01 economic admission, publish ve migration `BLOCKED`.
Sıradaki aktif kabul `P1.13.c` Spot Grid fee asset/rounding ve matched cycle
profit-total equity ayrımının karar kapısıdır. Binance/Testnet mutation hâlâ
açılmadı.

P1.12.g.h override: `P1.12.g.h` tamamlandı; fee-aware breakeven yalnız exact
`TAKE_PROFIT` adayına bağlanıyor, off-grid hedef sessiz rounding olmadan
BLOCKED. P1.12.h.a ile durable recovery/replay readiness, P1.12.h.b ile
profile-bound recovery capability, P1.12.h.c ile snapshot/quarantine ve
P1.12.h.d ile provenance/publish gate’i kapatıldı. Sıradaki P1.13.c Spot Grid
fee/cycle-profit karar kapısıdır. Conditional
execution, order/fill mutation,
persistence/recovery ve Binance/Testnet mutation hâlâ açılmadı.

## Referanslar

- C1: [3Commas özellik aileleri](https://help.3commas.io/en/articles/4430555-all-about-3commas-features-tools-history-and-benefits): SmartTrade, DCA/Grid/Signal, portföy ve asistan.
- C2: [DCA arayüzü ve ayarlar](https://help.3commas.io/en/articles/3108940-dca-bot-interface-and-main-settings): builder, ladder, sizing, pair ve hesap modu.
- C3: [Backtest özellikleri](https://3commas.io/blog/3commas-backtesting-update-8-new-features-for-smarter-trading): MTP, TSL, breakeven, timeout, reinvest, koşullar, fee/uPnL ve kayıt.
- C4: [Take profit ve trailing](https://help.3commas.io/en/articles/3108981-how-take-profit-works-smarttrade-and-dca-bots-trailing-feature-explained).
- P1: [Pionex grid](https://www.pionex.com/blog/grid-bot/).
- P2: [Pionex DCA ve grid ayrımı](https://www.pionex.com/blog/martingale-vs-grid-bot/).
- P3: [Pionex futures grid](https://support.pionex.com/hc/en-us/articles/45343668185113-Futures-Grid-Bot).
- P4: [Pionex bot kaynak indeksi](https://www.pionex.com/blog/): varyant/çift bacak aileleri keşif girdisidir; bugünkü her hesapta kullanılabilirlik kanıtı değildir.
- P5: [Pionex rebalancing](https://www.pionex.com/blog/dual-coin-rebalancing-bot-app-version/).
- D1: [Binance public veri](https://github.com/binance/binance-public-data).

Karşılaştırma fiyat/subscription planı veya performans tavsiyesi değildir. Rakip ürün açıklamasında bulunan bir matematik ya da fill varsayımı doğrulanmadan bizim çekirdeğe taşınmaz. Kapsam eşdeğerliği özellik ailesi + davranış + kabul kanıtıyla değerlendirilir, yalnız menü adlarıyla değil.
## 2026-09-18 P2.03 order-list/OCO state boundary

P2.03 order-list/OCO için immutable liste-bacak kimliği, WORKING/PENDING rolü,
bounded venue status gözlemi ve duplicate/conflict/out-of-order/terminal OCO
koordinasyonu `IMPLEMENTED_WITH_LIMITATION / LOCAL_PASS` durumundadır. Bu satır
yalnız read-only/fake venue projection kabulüdür; fiyat, miktar, fill, reserve,
core event, cancel-replace, SQLite replay, signed transport veya canlı mutation
özelliği değildir. Kanıt: `evidence/P2.03/MARKET_CONDITIONAL_ORDER_LIST_CONTRACT_SONUC.md`.
Durable replay owner ve venue reconciliation ayrı mikro-fazlardır; production
readiness `NO`.
