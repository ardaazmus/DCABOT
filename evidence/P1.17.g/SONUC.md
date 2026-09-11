# P1.17.g — Binance public profile acceptance matrix

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Production readiness: `NO`  
Tarih: 2026-09-10

## 1. Kapsam

P1.17.e ve P1.17.f çıktıları, tek bir network-free kabul matrisi içinde birlikte kontrol edildi. Bu dilim Binance Spot public `@trade` ve `@aggTrade` payload mapping’i ile mevcut bounded local replay sınırını doğrular.

Kapsam dışı ve açılmayan yollar:

- canlı WebSocket/REST istemcisi, reconnect worker ve REST catch-up;
- persistence, API/UI, credential, candidate/order/fill ve ekonomik hesap;
- public observation’ın simulated fill veya herhangi bir ekonomik transition’a dönüşmesi.

## 2. Claim → RED → minimum uygulama → GREEN

### Claim A — Yanlış timestamp birimi fail-closed reddedilmelidir

**RED:** İlk acceptance matrix, milisaniye bekleyen parser’a microsecond büyüklüğünde timestamp verildiğinde payload’ı kabul etti.

```text
FAIL ... name='timestamp_unit_mismatch'
AssertionError: ValueError not raised
```

**Minimum uygulama:** `binance_public.py` içine explicit time-unit modu ve bounded venue timestamp plausibility guard eklendi. Millisecond modunda değer ms aralığında doğrulanıp `* 1000` edilir; microsecond modunda değer us aralığında doğrulanıp aynen taşınır. Uyuşmazlık `BINANCE_TIMESTAMP_UNIT_MISMATCH` ile fail-closed reddedilir.

**GREEN:** Timestamp mismatch case’i ve explicit microsecond case’i geçti.

### Claim B — Mapping, scope ve malformed payload kararları tek kabul tablosunda sabitlenebilir

Sekiz parser hücresi doğrulandı:

1. geçerli `@trade` → kabul;
2. geçerli `@aggTrade` → kabul;
3. explicit microsecond payload → kabul, çift çarpım yok;
4. yanlış event type → reject;
5. allowlist dışı symbol → reject;
6. float ekonomik alan → reject;
7. event identity alanı eksik → reject;
8. timestamp unit mismatch → reject.

Her kabul edilen kayıt `Decimal` ekonomik alanları taşır; `source_sequence` zorunlu olarak `None` kalır. `t/a` yalnız event identity’dir.

### Claim C — Replay boundary duplicate/conflict/order/scope davranışını korur

Dört replay hücresi doğrulandı:

1. duplicate + sonraki non-contiguous ID → `ACCEPTED / DUPLICATE / ACCEPTED`, cursor `SYNCED`;
2. aynı identity ile farklı payload → `CONFLICT`, cursor `FAILED`;
3. event-time sırası geriye giden kayıt → `OUT_OF_ORDER`, cursor `GAP`;
4. aynı cursor’da karışık `TRADE` ve `AGG_TRADE` → `WRONG_SCOPE`, cursor `FAILED`.

Bu hücreler Binance trade/aggregate ID’sini source sequence gibi kullanmaz. Forged `source_sequence` ayrıca fail-closed reddedilir.

### Claim D — Economic-boundary no-op korunur

Matrix, normalize/replay çıktısında `candidate_id`, `order_id`, `fill_id`, `reserve`, `balance`, `pnl` veya benzeri ekonomik transition alanlarının oluşmadığını doğrular. Observation yalnız `READ_ONLY`, `PUBLIC_MARKET_DATA`, `NO_CREDENTIAL`, `NO_REAL_ORDER` sınırında kalır.

## 3. Bağımsız kontrol

Üretim parser/replay kararlarını kopyalamayan ayrı expected-outcome kontrolü çalıştırıldı:

```text
INDEPENDENT_BINANCE_ACCEPTANCE_MATRIX_ORACLE=PASS
```

Kontrol, parser için 8 ve replay için 4 olmak üzere toplam 12 bounded matrix hücresinin beklenen kararlarını, cursor state’ini ve ekonomik alan yokluğunu doğruladı.

## 4. Regresyon ve sınır kontrolü

```text
tests.test_binance_public_acceptance_matrix: PASS
tools/run_checks.py: 346/346 PASS
compileall: PASS
tools/check_workspace.py: PASS
active_python_files: 143
```

Bu sonuç venue’ye canlı bağlantı kurulduğunu, reconnect/catch-up’ın çalıştığını veya herhangi bir ekonomik simülasyonun açıldığını kanıtlamaz. Zaman plausibility aralıkları ve fail-closed kararları uygulama politikasıdır; Binance’ın tam timestamp/sequence sürekliliği garantisi olarak yorumlanamaz.

## 5. Sonuç ve sonraki tek iş

P1.17.g `LOCAL_PASS` olarak kapanır; production readiness `NO` kalır. Acceptance matrix, mevcut ağsız parser ve replay sınırının birlikte çalıştığını kanıtladı.

Sonraki tek mikro faz:

**P1.17.h — Binance REST public payload normalization (network-free)**

Yalnız fixture/decoded payload ile `/api/v3/trades` ve `/api/v3/aggTrades` REST mapping’i, `transport=REST`, REST’e özgü zaman alanları, identity ayrımı ve WS observation ile güvenli duplicate/scope ilişkisi kontrol edilecek. Ağ, catch-up, persistence, API/UI ve ekonomik fill açılmayacak.
