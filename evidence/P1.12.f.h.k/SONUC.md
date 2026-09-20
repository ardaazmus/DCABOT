# P1.12.f.h.k — Gerçek kaynaklara bağlı migration preflight kapısı

**Tarih:** 2026-09-17  
**Durum:** `COMPLETE_WITH_LIMITATION / LOCAL_PASS`; migration binding `NO-GO`

## Kanıt

Read-only preflight gerçek `FuturesDcaEventStore` ve `ReservationLedger`
örneklerini inceledi. Mevcut split kaynaklar profile contract-size,
execution fee/slippage/rounding, reservation release identity/terminal state
ve economic posting cursor/checksum alanlarını birlikte taşımadığı için açık
`NO_GO` verdi.

Odak test: `tests/test_futures_dca_migration_preflight.py` — `1/1 PASS`.
Preflight `futures_dca_journal_v1.sqlite` hedefi oluşturmadı ve kaynakları
değiştirmedi.

## Karar

Validator gerçek kaynak tiplerine bağlandı, ancak sonuç migration’a izin
vermiyor. Mevcut iki store’u birleştiren adapter, eksik alanları default’layan
conversion veya Spot journal’a taşıma yapılmayacak. Gerçek schema/coordinator,
immutable alanların tek kaynakta üretilmesi ve exact ekonomik kararların
kanıtlanmasından sonra açılabilir.

Tam proje kontrolü `tools/run_checks.py` — `533/533 PASS` (yükseltilmiş yerel
Windows Credential Manager erişimiyle).

## Sonraki tek iş

Önce production Futures DCA v1 schema’sını minimum immutable alanlarla
oluşturmak; ardından aynı preflight’ı gerçek target schema’ya karşı `READY`
üretecek şekilde bağlamak.
