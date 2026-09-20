# P1.16.c — Feature/label horizon overlap ve purge kararı

## Sonuç

- Durum: `COMPLETE_WITH_LIMITATION / LOCAL_PASS`
- Kod: `src/dcabot/application/horizon_overlap.py`
- Test: `tests/test_horizon_overlap.py`
- Bağımsız review: `Pauli PASS` (salt-okunur re-review, P1/P2 bulgu yok)
- Production readiness: `NO`
- Sonraki tek iş: `P1.16.d` multiple-testing trial registry karar kapısı

P1.16 araştırmasındaki feature/label horizon overlap kontrolünün güvenli, generic alt parçası uygulandı. Half-open integer zaman aralıkları `[start_time_us, end_time_us)` karşılaştırılıyor; sınırda birleşen aralık overlap sayılmıyor. Overlap varsa `PURGE_REQUIRED`, yoksa `NO_OVERLAP` sonucu dönüyor.

## Uygulanan sözleşme

- `TimeInterval` pozitif ve non-negative integer zamanlarla immutable’dır.
- Train-label ve test-feature aralıkları otomatik sıralanmaz; input listeleri zaman sırasını korumalıdır.
- Duplicate interval identity, geriye giden interval listesi, geçersiz/boş aralık ve yanlış tip fail-closed reddedilir.
- Overlap kimlikleri deterministic sıralı tuple olarak raporlanır.
- `PURGE_REQUIRED` yalnız bir karar/gate durumudur; kaç bar veya kaç mikro saniye purge/embargo uygulanacağını hesaplamaz.

## Bilinçli kapsam dışı

Local feature lookback, label future horizon, event settlement horizon, exact purge/embargo duration, expanding/rolling orchestration, dataset binding, OOS/trial/stress lineage, persistence, API/UI ve ekonomik sonuç bu mikro-fazda açılmadı. Exact numeric horizon local veri üretim sözleşmesi görülmeden seçilmeyecek.

## Kontroller

- `tests.test_horizon_overlap`: `5/5 PASS`. Public assessment invariant’ları,
  exact tuple/interval tipleri, custom equality ve malformed subclass
  bypass’ları regresyon kapsamına alındı.
- Bağımsız horizon oracle: adjacent sınır, gerçek half-open overlap,
  deterministic ID listesi, tutarsız status/ID sonuçları ve tuple subclass
  reddi: `PASS`.
- Bundled Python `3.12.14` ile `python -m compileall -q src tests`: `PASS`.
- `tools/run_checks.py` ve `tools/check_workspace.py`: `FAIL`, ikisi de proje
  gereksinimi olan Python `3.13` yokluğunda durdu (`active_python_files: 286`).
  Bu nedenle bu oturumda tam-suite/workspace sonucu iddia edilmiyor.
- `git diff --check`: `PASS` (yalnız mevcut LF/CRLF uyarıları).
- Live/testnet, credential ve dış ağ yolu açılmadı.

## Araştırma dayanağı

`docs/P1_KRITIK_ARASTIRMA_FINAL/13_P1.16_WALK_FORWARD_STRESS.md` purge/embargo gereğinin feature/label yapısına bağlı olduğunu ve sabit horizon uydurulmaması gerektiğini belirtir. Bu teslim yalnız overlap’i görünür kılan generic kontrolü kapatır; purge/embargo uygulamasının tamamlandığını iddia etmez. Pauli bağımsız re-review’ı P1/P2 bulgu bildirmedi; numeric purge/embargo policy, dataset binding ve ekonomik runner sonraki mikro-fazlara bırakıldı.
