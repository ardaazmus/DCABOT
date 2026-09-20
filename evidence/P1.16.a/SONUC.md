# P1.16.a — Chronological split sınırı

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/chronological_split.py`
- Test: `tests/test_chronological_split.py`
- Bağımsız review: `Noether PASS_WITH_LIMITATION` (salt-okunur)
- Production readiness: `NO`
- Sonraki tek iş: `P1.16.b` OOS freeze ve evaluation lineage karar kapısı

P1.16 araştırmasındaki `CLM-116-01` kabulü olan zaman sırasına dayalı train/gap/test sınırı, ekonomik authority oluşturmadan uygulandı. Girdi noktaları strict artan integer `event_time_us` ve benzersiz `sample_id` olmadan kabul edilmiyor; otomatik sıralama yapılmıyor.

## Uygulanan sözleşme

- `split_chronological` explicit `train_count` ile geçmiş train bölümünü, isteğe bağlı explicit `gap_count` ile dışlanan yapısal bölümü ve sonraki test bölümünü üretir.
- Train’in son zamanı test’in ilk zamanından kesin olarak küçüktür; future row train’e sızamaz.
- `gap_count` yalnız gözlemleri ayıran yapısal bir sınırdır; finansal purge/embargo süresini çözmüş veya garanti etmiş sayılmaz.
- Boş/taşan sınır, negatif veya yanlış tip count, duplicate sample identity, geriye giden/eşit zaman ve geçersiz sample kimliği fail-closed reddedilir.
- Çıktı immutable tuple’lardır; sıralama, ekonomik hesap, fill/order, persistence veya UI authority yoktur.

## Bilinçli kapsam dışı

Expanding/rolling walk-forward orkestrasyonu, gerçek dataset binding, feature/label horizon analizi, exact purge/embargo değeri, warmup, OOS freeze/touched lineage, multiple-testing registry, stress lineage, run persistence, API/UI ve ekonomik sonuç hesapları bu mikro-fazda açılmadı. Purge/embargo değeri local feature/label/event settlement horizon görülmeden seçilmeyecek.

## Kontroller

- `tests.test_chronological_split`: `7/7 PASS`. Public constructor için ters sıra,
  bölüm sınırında duplicate, geç gap ve yanlış point tipi regresyonları da aynı
  test içinde kapsandı.
- Bağımsız chronological oracle: explicit gap, strict
  `max(train_time) < min(test_time)`, future row eklenince önceki prefix’in
  değişmemesi ve malformed public constructor reddi: `PASS`.
- Bundled Python `3.12.14` ile `python -m compileall -q src tests`: `PASS`.
- `tools/run_checks.py` ve `tools/check_workspace.py`: `FAIL`, ikisi de proje
  gereksinimi olan Python `3.13` yokluğunda durdu (`active_python_files: 286`).
  Bu nedenle bu oturumda tam-suite/workspace sonucu iddia edilmiyor.
- `git diff --check`: `PASS` (yalnız mevcut LF/CRLF uyarıları).
- Live/testnet, credential ve dış ağ yolu açılmadı.

## Araştırma dayanağı

`docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md` chronological split’i `ACCEPT` eder; purge/embargo horizon’unun feature/label yapısına bağlı olduğunu ve local data gerektirdiğini belirtir. Bu teslim yalnız kabul edilen temel zaman sınırını yerel testlerle kapatır; P1.16’nın tamamlandığını iddia etmez. Noether incelemesi P1/P2 bulgu bulmadı; leakage-free evaluation, purge/embargo, OOS freeze ve ekonomik runner sonraki mikro-fazlara bırakıldı.
