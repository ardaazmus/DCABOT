# P1.06.a — Historical run snapshot ve execution identity hazırlığı

## Kapsam

Bu mikro dilim persistence yazmadan önce P1.06 araştırma raporundaki execution-input closure blocker’ını daraltır. Terminal `historical_ohlcv_v1` sonucundan gelecekteki local run store tarafından kullanılabilecek bounded ve canonical snapshot parçaları üretilir.

Bu dilimde SQLite tablo/transaction, HTTP save/list/detail/reproduce endpoint’i, frontend persistence ve kullanıcı aksiyonu eklenmemiştir.

## Araştırma girdisinin değerlendirilmesi

Kullanıcının sağladığı `P1.06_Persistent_Run_Detayli_Arastirma_Raporu_2026-09-08.md` proje talimatı olarak değil, karar ve blocker kaynağı olarak ele alındı. Raporun “full config snapshot”, “canonical input hash”, “runtime identity”, “monetary unit” ve `raw_reference` güvenlik bulguları mevcut kodla karşılaştırıldı.

## Uygulanan davranış

`src/dcabot/application/historical_run_contract.py` içindeki `build_historical_run_capture`:

- En fazla 1.000 canonical barı, sıra ve exact decimal stringleri korunarak canonical JSON’a çevirir.
- Dataset sembolü/config sembolü, UTC/microseconds ve açık `USDT` monetary unit context’ini doğrular.
- `config/paper.json` içindeki Config dataclass alanlarının tamamını, `mode` ve `schema_version` ile birlikte allowlist snapshot olarak taşır.
- Config canonical JSON hash’ini mevcut P1.04 config hash’iyle karşılaştırır; uyuşmazlıkta fail-closed olur.
- Instrument/risk alanlarının bounded canonical snapshot hash’ini üretir.
- `historical_ohlcv_v1`, model version, package simulator version, `offline-core-1` kernel identity, assumption contract ve `NOT_APPLICABLE` seed policy’sini explicit hale getirir.
- P1.05 result’ın yalnız güvenli allowlist alanlarını snapshot’lar; action sayısını ve bar eşleşmesini sınırlar.
- `raw_reference`, fill price, quantity ve fee alanlarını plain decimal olarak doğrular; path/URL gibi referanslar `ACTION_REFERENCE_UNSAFE` ile reddedilir.
- Input, result ve execution identity canonical JSON hash’lerini üretir; `run_id` veya persistence üretmez.

## Doğrulama sırası

1. RED: Yeni testler modül bulunmadığı için 3 import hatası verdi.
2. GREEN: Uygulama sonrası yeni snapshot contract testleri 3/3 PASS oldu.
3. Farklı kontrol: `uv run --frozen python tools/run_checks.py` tam regresyonu çalıştırıldı.
4. Sonuç: 95/95 PASS.
5. Ek kontrol: `uv run --frozen python -m compileall -q src tests` PASS.
6. Ek kontrol: `uv run --frozen python tools/check_workspace.py` PASS; backup layout `EMPTY_OR_NOT_PLACED`.

## Açık blocker’lar

Bu kanıt yalnız snapshot/identity hazırlığını kapatır. Dedicated SQLite store ownership/lifecycle, atomic commit, corruption/migration, HTTP mutation guard, runtime worst-case benchmark, persistence API ve UI akışı sonraki mikro dilimlerdir. Stable runtime identity için kullanılan package/kernel sabitlerinin davranış değişikliğinde sürümlendirme politikası ayrıca korunmalıdır.

## Durum

`P1.06.a: IMPLEMENTED / LOCAL_PASS; review: NOT_RUN.` P1.06 genel fazı tamamlanmış sayılmaz.
