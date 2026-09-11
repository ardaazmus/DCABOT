# P1.18.a — Offline rule-based read-only event explanation projection

Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`  
Production readiness: `NO`  
Tarih: 2026-09-10

## 1. Kapsam

Mevcut tarihsel sonuç ve public observation replay outcome sınırlarından,
ekonomik hesabı yeniden yapmadan deterministik açıklama kayıtları üretildi.
Bu mikro faz canlı transport, persistence, API/UI, candidate/order/fill,
reserve, balance veya PnL authority açmaz.

## 2. Claim → kontrol → uygulama

### Claim A — Açıklama mevcut backend authority’sini yeniden hesaplamadan üretebilir

Local kontrol: `HistoricalSimulationResult` / fixed-slice result alanları
(`execution_status`, `application_code`, `position_status`,
`funding_status`, `mark_status`, `actions`) ve public `ReplayResult.outcomes`
mevcut durumda yeterliydi. Yeni numeric alan okumadan yalnız status, outcome,
action index/bar index/role bağlamı kullanıldı.

RED kontrol: Yeni test ilk çalıştırmada `read_only_explanations` modülü yokluğu
nedeniyle import aşamasında başarısız oldu; davranış henüz mevcut değildi.

Minimum uygulama: `src/dcabot/application/read_only_explanations.py` içinde
bounded `ReadOnlyExplanation`, `explain_historical_result` ve
`explain_public_replay` eklendi.

### Claim B — Bilinmeyen veya tutarsız durum sessizce açıklanmamalıdır

Projection bilinmeyen historical status/application code, tamamlanmış sonuçta
ambiguity code’u, desteklenmeyen position/funding/mark durumu, bozuk action
kapsamı ve bilinmeyen public outcome için `ValueError` ile fail-closed olur.
Explanation context’i `MappingProxyType` ile dışarıya salt-okunur sunulur.

### Claim C — Projection ekonomik authority’ye dönüşmemelidir

Bağımsız kontrol gerçek üretim `HistoricalSimulationResult` ve
`ObservationOutcome` sınıflarıyla çalıştırıldı. Çıktılarda `pnl`, `fee`,
`reserve`, `order_id` veya `fill_id` alanı üretilmedi; public replay sonucu
yalnız observation outcome açıklaması olarak kaldı.

## 3. Test sonuçları

Odak testleri:

```text
tests/test_read_only_explanations.py: 4/4 PASS
INDEPENDENT_ORACLE=PASS
```

Tam regresyon ve kalite:

```text
tools/run_checks.py: 359/359 PASS
compileall: PASS
tools/check_workspace.py: PASS
active_python_files: 147
```

## 4. Bilinçli sınırlar

- API response alanı ve frontend görünümü bu mikro fazda değiştirilmedi.
- Açıklama metinleri ekonomik sonuç, kârlılık, risk seviyesi veya işlem önerisi
  iddiası taşımaz.
- Tarihsel result summary içindeki finansal değerler projection tarafından
  yeniden hesaplanmaz veya dönüştürülmez.
- Public replay açıklaması canlı akış, reconnect, catch-up veya simulated fill
  anlamına gelmez.
- Dış LLM, network, credential, persistence ve bildirim kanalı eklenmedi.

## 5. Karar

```text
IMPLEMENTATION_STATUS=COMPLETE_WITH_LIMITATION
PRODUCTION_READINESS=NO
NEXT_SINGLE_WORK=P1.18.b
```

P1.18.a local projection katmanı için kanıt yeterlidir. Kullanıcıya/API’ye
bağlamak, yeni response sözleşmesi ve UI davranışı gerektirdiği için ayrı bir
sonraki mikro faz olarak ele alınacaktır.
