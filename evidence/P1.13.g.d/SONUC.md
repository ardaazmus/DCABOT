# P1.13.g.d — Futures Grid primary-source lifecycle audit

## Sonuç

- Alt faz durumu: `COMPLETE_WITH_LIMITATION / RESEARCH_AUDITED`
- İleri Futures Grid implementation kararı: `DEFERRED / NO-GO`
- Ana faz: `P1.13.g IN_PROGRESS / IMPLEMENTATION_PENDING`
- Rapor: `docs/archive/arastirma-promptlari/P1.13_FUTURES_GRID_LIFECYCLE_PRIMARY_SOURCE_AUDIT.md` (2026-09-20'de arşivlendi; içerik/hash değişmedi)
- Rapor SHA-256: `1CDAA5BD6ADDF73C731E1DEBC1138AAE0F02550A616CC889BDED8A3011F01939`
- Production readiness: `NO`

## Araştırma kararı

Resmî 3Commas ve Pionex kaynakları trailing/expansion ve Futures Grid ürün
ailelerini yüksek seviyede destekliyor. Resmî Binance kaynakları order/event
kimliklerini ve bazı zaman alanlarını gözlemlemeye izin veriyor. Ancak
incelenen kaynaklar birlikte exact bir lifecycle oracle oluşturmuyor.

| Sınır | Audit sonucu | Uygulama kararı |
|---|---|---|
| `RANGE_REVISION` | Ürün davranışı kısmen belgeli; exact transition/version/line identity yok | `CONTRACT_REQUIRED` |
| `CANCEL_REPLACE` | Exchange order/amend alanları var; bot replacement lineage ve confirmation protokolü yok | `CONTRACT_REQUIRED` |
| `PENDING_RESERVE` | Dynamic margin/pending order kavramları var; lock/consume/release atomikliği yok | `NOT_DOCUMENTED` |
| `LATE_FILL` | Order/fill event alanları var; generation önceliği ve ekonomik yetki yok | `NOT_DOCUMENTED` |
| `REPLAY` | Bazı event/time alanları var; deterministic replay, gap recovery ve retry idempotency yok | `NOT_DOCUMENTED` |

Bu nedenle P1.13.g.c’nin `BLOCKED_CONTRACT_REQUIRED` ve
`order_authority=NONE` sınırı aynen korunmuştur. Order placement,
replacement, accepted fill, reserve mutation, P&L/margin mutation,
persistence, API/UI ve Binance/Testnet mutation açılmamıştır.

## Checkout karşı kontrolü

- `src/dcabot/application/futures_grid_replacement_replay_gate.py` dört sınırı
  typed olarak expose eder ve her biri için gerekli beş contract başlığını
  taşır.
- `tests/test_futures_grid_replacement_replay_gate.py`: `3/3 PASS`.
- Gate sonucu: her sınır `BLOCKED_CONTRACT_REQUIRED`, authority `NONE`.
- Gate çıktısında order/replacement ID, candidate level, position veya store
  alanı bulunmadığı testle doğrulandı.
- `python -m compileall -q src`: `PASS`.
- `tools/check_workspace.py`: `PASS`.
- `git diff --check`: `PASS`.
- Tam suite son doğrulaması: `749` testte `747 PASS`, Windows Credential
  Manager `Windows error 1312` nedeniyle `2` environment error.

## Yetki ve sonraki sınır

Bu rapor, yüksek seviyeli vendor özelliklerini exact DCABOT sözleşmesi olarak
onaylamaz. Kaynak/oracle açığı kapanmadan P1.13.g’nin kalan ileri yaşam döngüsü
davranışı `CONTRACT_REQUIRED` kalır. Sonraki güvenli iş, yeni ekonomik veya
emir davranışı yazmak değil; exact source/oracle sağlanıp sağlanmadığını
bağımsız olarak yeniden değerlendirmektir.

Gerçek API anahtarı/secret, canlı veya Testnet mutation ve manuel kullanıcı
işlemi kullanılmadı.
